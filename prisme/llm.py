"""Couche d'appel aux modèles : Anthropic (par défaut) ou point d'accès compatible OpenAI (Mistral, hébergeur souverain)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from . import config


class LLMError(Exception):
    """Erreur d'appel au modèle, message directement affichable à l'utilisateur."""


@dataclass
class LLMResult:
    text: str
    sources: list[dict] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    searches: int = 0
    notice: str = ""

    def with_sources(self) -> str:
        if not self.sources:
            return self.text
        lines = [f"- {s['title']} ({s['url']})" if s.get("title") else f"- {s['url']}" for s in self.sources]
        return self.text.rstrip() + "\n\nSources consultées :\n" + "\n".join(lines)


_client_factory = None  # point d'injection pour les tests


def _anthropic_client():
    if _client_factory is not None:
        return _client_factory()
    key = config.secret("ANTHROPIC_API_KEY")
    if not key:
        raise LLMError("Clé API absente : renseignez ANTHROPIC_API_KEY dans les secrets de l'application.")
    import anthropic

    return anthropic.Anthropic(api_key=key, max_retries=2, timeout=180.0)


def _web_tool(allowed_domains: list[str] | None) -> dict:
    tool = {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 5,
        "user_location": {"type": "approximate", "country": "FR", "timezone": "Europe/Paris"},
    }
    if allowed_domains:
        tool["allowed_domains"] = allowed_domains
    return tool


def _collect(blocks) -> tuple[str, list[dict]]:
    parts: list[str] = []
    sources: list[dict] = []
    seen: set[str] = set()
    for block in blocks or []:
        if getattr(block, "type", "") != "text":
            continue
        parts.append(getattr(block, "text", "") or "")
        for cit in getattr(block, "citations", None) or []:
            url = getattr(cit, "url", None)
            if url and url not in seen:
                seen.add(url)
                sources.append({"url": url, "title": getattr(cit, "title", "") or ""})
    return "".join(parts).strip(), sources


def _anthropic_generate(messages, system, max_tokens, web, domains) -> LLMResult:
    import anthropic

    client = _anthropic_client()
    kwargs = {"model": config.model(), "max_tokens": max_tokens, "system": system}
    notice = ""
    tools = [_web_tool(domains)] if web else None
    msgs = list(messages)
    texts: list[str] = []
    sources: list[dict] = []
    usage = {"in": 0, "out": 0, "search": 0}

    for _ in range(6):  # la recherche web peut suspendre le tour (pause_turn)
        call = dict(kwargs, messages=msgs)
        if tools:
            call["tools"] = tools
        try:
            resp = client.messages.create(**call)
        except anthropic.BadRequestError as exc:
            if tools and "search" in str(exc).lower():
                tools = None
                notice = (
                    "La recherche web n'est pas activée sur l'organisation Anthropic liée à cette clé : "
                    "réponse produite sans recherche."
                )
                continue
            raise LLMError(f"Requête refusée par le modèle : {exc}") from exc
        except anthropic.AuthenticationError as exc:
            raise LLMError("Clé API Anthropic invalide ou révoquée.") from exc
        except anthropic.RateLimitError as exc:
            raise LLMError("Limite de débit atteinte côté Anthropic : réessayez dans un instant.") from exc
        except anthropic.APIConnectionError as exc:
            raise LLMError("Connexion à l'API Anthropic impossible. Vérifiez le réseau.") from exc
        except anthropic.APIError as exc:
            raise LLMError(f"Erreur de l'API Anthropic : {exc}") from exc

        text, found = _collect(resp.content)
        texts.append(text)
        sources.extend(s for s in found if s["url"] not in {x["url"] for x in sources})
        u = getattr(resp, "usage", None)
        usage["in"] += getattr(u, "input_tokens", 0) or 0
        usage["out"] += getattr(u, "output_tokens", 0) or 0
        stu = getattr(u, "server_tool_use", None)
        usage["search"] += getattr(stu, "web_search_requests", 0) or 0
        if getattr(resp, "stop_reason", "") == "pause_turn":
            msgs = msgs + [{"role": "assistant", "content": resp.content}]
            continue
        break

    final = "\n".join(t for t in texts if t).strip()
    return LLMResult(final or "Aucune réponse générée.", sources, usage["in"], usage["out"], usage["search"], notice)


def _openai_compat_generate(messages, system, max_tokens, web) -> LLMResult:
    import requests

    base = str(config.secret("PRISME_OPENAI_BASE_URL", "https://api.mistral.ai/v1")).rstrip("/")
    key = config.secret("PRISME_OPENAI_API_KEY") or config.secret("MISTRAL_API_KEY")
    if not key:
        raise LLMError("Clé API absente : renseignez PRISME_OPENAI_API_KEY (ou MISTRAL_API_KEY).")
    payload = {
        "model": config.model(),
        "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": system}, *messages],
    }
    try:
        resp = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
            timeout=180,
        )
    except requests.RequestException as exc:
        raise LLMError("Connexion au fournisseur de modèle impossible.") from exc
    if resp.status_code >= 400:
        raise LLMError(f"Erreur du fournisseur de modèle ({resp.status_code}) : {resp.text[:300]}")
    data = resp.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("Réponse du fournisseur de modèle inexploitable.") from exc
    usage = data.get("usage") or {}
    notice = "La recherche web n'est pas disponible avec ce fournisseur." if web else ""
    return LLMResult(
        (text or "").strip() or "Aucune réponse générée.",
        [],
        usage.get("prompt_tokens", 0),
        usage.get("completion_tokens", 0),
        0,
        notice,
    )


def generate(
    prompt: str,
    system: str,
    *,
    history: list[dict] | None = None,
    web_search: bool = False,
    allowed_domains: list[str] | None = None,
    max_tokens: int | None = None,
    module: str = "general",
    tenant: str | None = None,
    storage=None,
) -> LLMResult:
    if tenant and storage is not None and storage.calls_today(tenant) >= config.daily_limit():
        raise LLMError(
            f"Plafond quotidien de {config.daily_limit()} générations atteint pour cet espace. Il se renouvelle demain."
        )
    messages = [*(history or []), {"role": "user", "content": prompt}]
    max_tokens = max_tokens or config.DEFAULT_MAX_TOKENS
    if config.provider() == "anthropic":
        result = _anthropic_generate(messages, system, max_tokens, web_search, allowed_domains)
    else:
        result = _openai_compat_generate(messages, system, max_tokens, web_search)
    if tenant and storage is not None:
        storage.log_usage(tenant, module, config.model(), result.input_tokens, result.output_tokens, result.searches)
    return result


def extract_json(text: str) -> dict:
    """Extrait un objet JSON d'une réponse de modèle (balises de code tolérées)."""
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    try:
        value = json.loads(match.group(0) if match else cleaned)
    except ValueError as exc:
        raise LLMError("Le modèle n'a pas renvoyé de données structurées exploitables.") from exc
    if not isinstance(value, dict):
        raise LLMError("Le modèle n'a pas renvoyé de données structurées exploitables.")
    return value
