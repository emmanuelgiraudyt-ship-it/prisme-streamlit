import anthropic
import pytest
from conftest import FakeClient, make_response

from prisme import llm
from prisme.storage import Storage

try:  # le SDK récent s'appuie sur httpx2, les anciennes versions sur httpx
    import httpx2 as httpx
except ImportError:
    import httpx


def test_simple_generation_and_usage(fake_client, tmp_path):
    s = Storage(tmp_path / "u.db")
    res = llm.generate("Bonjour", "système", module="Test", tenant="t", storage=s)
    assert res.text == "Réponse de test."
    assert fake_client.calls[0]["messages"][-1]["content"] == "Bonjour"
    assert "tools" not in fake_client.calls[0]
    assert s.usage_stats("t")["month_calls"] == 1


def test_web_search_tool_and_sources(monkeypatch):
    from types import SimpleNamespace as NS

    resp = make_response(
        "Une information.",
        citations=[NS(url="https://senat.fr/a", title="Sénat"), NS(url="https://senat.fr/a", title="doublon")],
        searches=2,
    )
    client = FakeClient([resp])
    monkeypatch.setattr(llm, "_client_factory", lambda: client)
    res = llm.generate("q", "s", web_search=True, allowed_domains=["senat.fr"])
    tool = client.calls[0]["tools"][0]
    assert tool["type"] == "web_search_20250305" and tool["allowed_domains"] == ["senat.fr"]
    assert "blocked_domains" not in tool
    assert [s["url"] for s in res.sources] == ["https://senat.fr/a"]
    assert res.searches == 2
    assert "Sources consultées" in res.with_sources() and "senat.fr/a" in res.with_sources()


def test_pause_turn_continues(monkeypatch):
    client = FakeClient([make_response("Début.", stop_reason="pause_turn"), make_response("Suite.")])
    monkeypatch.setattr(llm, "_client_factory", lambda: client)
    res = llm.generate("q", "s", web_search=True)
    assert len(client.calls) == 2 and "Début." in res.text and "Suite." in res.text
    assert client.calls[1]["messages"][-1]["role"] == "assistant"


def test_web_search_disabled_falls_back(monkeypatch):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    err = anthropic.BadRequestError(
        "web search is not enabled", response=httpx.Response(400, request=request), body=None
    )
    client = FakeClient([err, make_response("Sans recherche.")])
    monkeypatch.setattr(llm, "_client_factory", lambda: client)
    res = llm.generate("q", "s", web_search=True)
    assert res.text == "Sans recherche." and "pas activée" in res.notice
    assert "tools" not in client.calls[1]


def test_auth_error_is_friendly(monkeypatch):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    err = anthropic.AuthenticationError("bad key", response=httpx.Response(401, request=request), body=None)
    monkeypatch.setattr(llm, "_client_factory", lambda: FakeClient([err]))
    with pytest.raises(llm.LLMError, match="invalide"):
        llm.generate("q", "s")


def test_missing_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    with pytest.raises(llm.LLMError, match="ANTHROPIC_API_KEY"):
        llm.generate("q", "s")


def test_daily_limit(fake_client, tmp_path, monkeypatch):
    monkeypatch.setenv("PRISME_DAILY_LIMIT", "1")
    s = Storage(tmp_path / "l.db")
    llm.generate("q", "s", tenant="t", storage=s)
    with pytest.raises(llm.LLMError, match="Plafond"):
        llm.generate("q", "s", tenant="t", storage=s)
    llm.generate("q", "s", tenant="autre", storage=s)  # un autre espace n'est pas bloqué


def test_extract_json():
    assert llm.extract_json('```json\n{"a": 1}\n```')["a"] == 1
    assert llm.extract_json('Voici : {"a": 2} fin')["a"] == 2
    with pytest.raises(llm.LLMError):
        llm.extract_json("pas de json")


def test_openai_compatible_provider(monkeypatch):
    import requests

    monkeypatch.setenv("PRISME_PROVIDER", "openai")
    monkeypatch.setenv("PRISME_OPENAI_API_KEY", "k")
    seen = {}

    class R:
        status_code = 200
        text = ""

        def json(self):
            return {
                "choices": [{"message": {"content": "Bonjour"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 4},
            }

    def fake_post(url, headers, json, timeout):
        seen.update(url=url, auth=headers["Authorization"], payload=json)
        return R()

    monkeypatch.setattr(requests, "post", fake_post)
    res = llm.generate("q", "sys", web_search=True)
    assert res.text == "Bonjour" and res.input_tokens == 3 and "pas disponible" in res.notice
    assert seen["url"].endswith("/chat/completions") and seen["auth"] == "Bearer k"
    assert seen["payload"]["messages"][0] == {"role": "system", "content": "sys"}
