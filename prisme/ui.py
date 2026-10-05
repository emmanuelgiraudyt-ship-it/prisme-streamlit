"""Composants d'interface partagés : en-têtes, appels IA, barre d'export, navigation."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from . import config, content, exports, google_ws, llm
from .storage import Storage, get_storage
from .util import slug

PAGES: dict = {}  # alimenté par app.py à chaque exécution


@dataclass
class Ctx:
    tenant: str
    settings: dict
    storage: Storage


def ctx() -> Ctx:
    tenant = st.session_state.get("tenant", "local")
    storage = get_storage()
    return Ctx(tenant, storage.get_settings(tenant), storage)


def goto(key: str) -> None:
    page = PAGES.get(key)
    if page is not None:
        st.switch_page(page)


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;1,400&display=swap');
h1, h2, h3 { font-family: 'EB Garamond', Georgia, serif !important; letter-spacing: 0.01em; }
h1 { color: #D4A828 !important; font-weight: 600 !important; }
.prisme-eyebrow { font-family: monospace; font-size: 0.72rem; letter-spacing: 0.15em;
  text-transform: uppercase; color: #6B5426; margin-bottom: 0.2rem; }
.prisme-sub { font-style: italic; color: #9C9587; font-size: 1.05rem; max-width: 46rem; margin-top: -0.4rem; }
.prisme-chrono { font-family: monospace; font-size: 2.4rem; }
.prisme-foot { font-family: monospace; font-size: 0.68rem; color: #9C9587; line-height: 1.7; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def header(eyebrow: str, title: str, subtitle: str = "") -> None:
    st.markdown(f"<div class='prisme-eyebrow'>{eyebrow}</div>", unsafe_allow_html=True)
    st.title(title)
    if subtitle:
        st.markdown(f"<div class='prisme-sub'>{subtitle}</div>", unsafe_allow_html=True)
    st.write("")


def ask(
    prompt: str,
    *,
    module: str,
    web: bool = False,
    domains: list[str] | None = None,
    history: list[dict] | None = None,
    system: str | None = None,
    max_tokens: int | None = None,
) -> llm.LLMResult | None:
    c = ctx()
    with st.spinner("Génération en cours…"):
        try:
            result = llm.generate(
                prompt,
                system or content.build_system(c.settings),
                history=history,
                web_search=web,
                allowed_domains=domains,
                max_tokens=max_tokens,
                module=module,
                tenant=c.tenant,
                storage=c.storage,
            )
        except llm.LLMError as exc:
            st.error(str(exc))
            return None
    if result.notice:
        st.warning(result.notice)
    return result


def output_box(text: str, placeholder: str) -> None:
    with st.container(border=True):
        if text:
            st.markdown(text)
        else:
            st.caption(placeholder)


def export_bar(key: str, title: str, text: str, module: str, *, archive: bool = True, canva: bool = False) -> None:
    """Barre d'actions sur un texte produit : téléchargements, archivage, Notion, Google."""
    if not text:
        return
    c = ctx()
    author = c.settings.get("cabinet", "")
    row1 = st.columns(4)
    row1[0].download_button(
        "Word (.docx)",
        data=exports.to_docx_bytes(title, text, author),
        file_name=f"{slug(title)}.docx",
        mime=exports.DOCX_MIME,
        key=f"{key}_docx",
        use_container_width=True,
    )
    row1[1].download_button(
        "Markdown (.md)",
        data=f"# {title}\n\n{text}\n".encode(),
        file_name=f"{slug(title)}.md",
        mime="text/markdown",
        key=f"{key}_md",
        use_container_width=True,
    )
    row1[2].download_button(
        "Brouillon (.eml)",
        data=exports.to_eml_bytes(title, text),
        file_name=f"{slug(title)}.eml",
        mime="message/rfc822",
        key=f"{key}_eml",
        use_container_width=True,
    )
    with row1[3].popover("Copier le texte", use_container_width=True):
        st.code(text, language=None, wrap_lines=True)

    row2 = st.columns(4)
    notion_ok, google_ok = exports.notion_configured(), google_ws.configured()
    feedback = st.container()
    if archive and row2[0].button("Archiver", key=f"{key}_arch", use_container_width=True):
        c.storage.add_document(c.tenant, module, title, text)
        feedback.success("Document archivé dans la bibliothèque.")
    if row2[1].button(
        "Notion",
        key=f"{key}_notion",
        disabled=not notion_ok,
        use_container_width=True,
        help=None if notion_ok else "Renseigner NOTION_TOKEN et NOTION_PARENT_PAGE_ID.",
    ):
        _run(feedback, "Page Notion créée", lambda: exports.notion_create_page(title, text))
    if row2[2].button(
        "Google Drive",
        key=f"{key}_drive",
        disabled=not google_ok,
        use_container_width=True,
        help=None if google_ok else "Renseigner les identifiants Google (voir README).",
    ):
        _run(
            feedback,
            "Document créé dans Google Drive",
            lambda: google_ws.upload_docx_as_google_doc(title, exports.to_docx_bytes(title, text, author)),
        )
    if row2[3].button(
        "Brouillon Gmail",
        key=f"{key}_gmail",
        disabled=not google_ok,
        use_container_width=True,
        help=None if google_ok else "Renseigner les identifiants Google (voir README).",
    ):
        _run(feedback, "Brouillon Gmail créé (rien n'a été envoyé)", lambda: google_ws.create_gmail_draft(title, text))

    if canva:
        if st.button("Brief visuel pour Canva", key=f"{key}_canva"):
            res = ask(
                "À partir du texte institutionnel suivant, rédige un brief créatif prêt à coller dans Canva : "
                "titre, accroche, hiérarchie des textes, palette (fond sombre, accent doré), format recommandé.\n\n"
                + text,
                module="Canva",
            )
            if res:
                st.session_state[f"{key}_canva_out"] = res.text
        if st.session_state.get(f"{key}_canva_out"):
            with st.expander("Brief visuel", expanded=True):
                st.markdown(st.session_state[f"{key}_canva_out"])


def _run(feedback, success: str, action) -> None:
    try:
        result = action()
    except exports.ExportError as exc:
        feedback.error(str(exc))
        return
    feedback.success(f"{success}." + (f" {result}" if isinstance(result, str) and result.startswith("http") else ""))


def integration_rows() -> list[dict]:
    provider = config.provider()
    key_ok = bool(
        config.secret("ANTHROPIC_API_KEY")
        if provider == "anthropic"
        else (config.secret("PRISME_OPENAI_API_KEY") or config.secret("MISTRAL_API_KEY"))
    )
    return [
        {"nom": f"Modèle ({provider})", "actif": key_ok, "detail": config.model()},
        {"nom": "Recherche web", "actif": key_ok and provider == "anthropic", "detail": "Outil natif Anthropic"},
        {"nom": "Notion", "actif": exports.notion_configured(), "detail": "Dépôt de pages"},
        {
            "nom": "Google (Gmail, Drive, Agenda)",
            "actif": google_ws.configured(),
            "detail": "Brouillons, documents, agenda",
        },
    ]
