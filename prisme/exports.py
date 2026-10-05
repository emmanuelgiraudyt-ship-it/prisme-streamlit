"""Exports : Word, courriel (.eml), Notion."""

from __future__ import annotations

import io
import re
from email.message import EmailMessage

from . import config

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MENTION_IA = "Projet généré par intelligence artificielle, soumis à relecture et validation avant toute diffusion."


class ExportError(Exception):
    """Erreur d'export, message directement affichable."""


# ---------- Word ----------
def _runs(paragraph, text: str) -> None:
    for chunk in re.split(r"(\*\*[^*]+\*\*)", text):
        if chunk.startswith("**") and chunk.endswith("**") and len(chunk) > 4:
            paragraph.add_run(chunk[2:-2]).bold = True
        elif chunk:
            paragraph.add_run(chunk)


def to_docx_bytes(title: str, content: str, author: str = "") -> bytes:
    from docx import Document
    from docx.shared import Pt

    doc = Document()
    doc.styles["Normal"].font.name = "Garamond"
    doc.styles["Normal"].font.size = Pt(11.5)
    doc.core_properties.title = title
    if author:
        doc.core_properties.author = author
    doc.add_heading(title, level=0)
    for raw in content.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)", line)
        bullet = re.match(r"^\s*[-*•]\s+(.*)", line)
        number = re.match(r"^\s*\d+[.)]\s+(.*)", line)
        if heading:
            doc.add_heading(heading.group(2).replace("**", ""), level=len(heading.group(1)))
        elif bullet:
            _runs(doc.add_paragraph(style="List Bullet"), bullet.group(1))
        elif number:
            _runs(doc.add_paragraph(style="List Number"), number.group(1))
        else:
            _runs(doc.add_paragraph(), line.strip())
    note = doc.add_paragraph()
    run = note.add_run(MENTION_IA)
    run.italic = True
    run.font.size = Pt(9)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# ---------- Courriel ----------
def to_eml_bytes(subject: str, body: str, to: str = "", sender: str = "") -> bytes:
    """Brouillon .eml : s'ouvre comme message non envoyé dans Outlook, Apple Mail, Thunderbird."""
    msg = EmailMessage()
    msg["Subject"] = subject
    if to:
        msg["To"] = to
    if sender:
        msg["From"] = sender
    msg["X-Unsent"] = "1"
    msg.set_content(body)
    return msg.as_bytes()


# ---------- Notion ----------
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_HEX32 = re.compile(r"[0-9a-fA-F]{32}")


def notion_configured() -> bool:
    return bool(config.secret("NOTION_TOKEN") and notion_parent()[0])


def notion_parent() -> tuple[str | None, str]:
    """Retourne (identifiant, type) du parent de dépôt : base de données ou page."""
    for name, kind in (("NOTION_DATABASE_ID", "database"), ("NOTION_PARENT_PAGE_ID", "page")):
        found = extract_notion_id(config.secret(name) or "")
        if found:
            return found, kind
    return None, "page"


def extract_notion_id(value: str) -> str | None:
    uuid_match = _UUID.findall(value)
    if uuid_match:
        return uuid_match[-1].replace("-", "")
    hex_match = _HEX32.findall(value)
    return hex_match[-1] if hex_match else None


def _chunks(text: str, size: int = 1900) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


def to_notion_blocks(content: str) -> list[dict]:
    blocks: list[dict] = []

    def add(kind: str, text: str) -> None:
        for piece in _chunks(text.replace("**", "")):
            blocks.append(
                {"object": "block", "type": kind, kind: {"rich_text": [{"type": "text", "text": {"content": piece}}]}}
            )

    for raw in content.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)", line)
        bullet = re.match(r"^\s*[-*•]\s+(.*)", line)
        number = re.match(r"^\s*\d+[.)]\s+(.*)", line)
        if heading:
            add(f"heading_{len(heading.group(1))}", heading.group(2))
        elif bullet:
            add("bulleted_list_item", bullet.group(1))
        elif number:
            add("numbered_list_item", number.group(1))
        else:
            add("paragraph", line.strip())
    return blocks


def _notion_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _notion_check(resp) -> dict:
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("message", resp.text)
        except ValueError:
            detail = resp.text
        raise ExportError(f"Notion a refusé la requête ({resp.status_code}) : {detail}")
    return resp.json()


def notion_create_page(title: str, content: str) -> str:
    """Crée une page Notion et retourne son URL."""
    import requests

    token = config.secret("NOTION_TOKEN")
    parent_id, kind = notion_parent()
    if not token or not parent_id:
        raise ExportError("Notion n'est pas configuré (NOTION_TOKEN et NOTION_PARENT_PAGE_ID ou NOTION_DATABASE_ID).")
    headers = _notion_headers(token)
    blocks = to_notion_blocks(content)
    try:
        if kind == "database":
            db = _notion_check(requests.get(f"{NOTION_API}/databases/{parent_id}", headers=headers, timeout=30))
            title_prop = next((k for k, v in db.get("properties", {}).items() if v.get("type") == "title"), "Name")
            parent = {"database_id": parent_id}
            props = {title_prop: {"title": [{"text": {"content": title[:200]}}]}}
        else:
            parent = {"page_id": parent_id}
            props = {"title": {"title": [{"text": {"content": title[:200]}}]}}
        page = _notion_check(
            requests.post(
                f"{NOTION_API}/pages",
                headers=headers,
                json={"parent": parent, "properties": props, "children": blocks[:100]},
                timeout=60,
            )
        )
        rest = blocks[100:]
        for i in range(0, len(rest), 100):
            _notion_check(
                requests.patch(
                    f"{NOTION_API}/blocks/{page['id']}/children",
                    headers=headers,
                    json={"children": rest[i : i + 100]},
                    timeout=60,
                )
            )
    except requests.RequestException as exc:
        raise ExportError("Connexion à Notion impossible.") from exc
    return page.get("url", "")


def notion_test() -> str:
    import requests

    token = config.secret("NOTION_TOKEN")
    if not token:
        raise ExportError("NOTION_TOKEN absent.")
    try:
        data = _notion_check(requests.get(f"{NOTION_API}/users/me", headers=_notion_headers(token), timeout=30))
    except requests.RequestException as exc:
        raise ExportError("Connexion à Notion impossible.") from exc
    return data.get("name") or "intégration reconnue"
