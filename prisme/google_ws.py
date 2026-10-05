"""Google Workspace (Gmail brouillons, Drive, Agenda) via un jeton d'actualisation OAuth."""

from __future__ import annotations

import base64
import io
from datetime import datetime, timedelta

from . import config
from .exports import DOCX_MIME, ExportError, to_eml_bytes

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def configured() -> bool:
    return all(config.secret(k) for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"))


def _credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    if not configured():
        raise ExportError("Google n'est pas configuré (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN).")
    creds = Credentials(
        token=None,
        refresh_token=config.secret("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.secret("GOOGLE_CLIENT_ID"),
        client_secret=config.secret("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES,
    )
    try:
        creds.refresh(Request())
    except Exception as exc:
        raise ExportError(f"Authentification Google refusée (jeton expiré ou révoqué ?) : {exc}") from exc
    return creds


def _service(name: str, version: str):
    from googleapiclient.discovery import build

    return build(name, version, credentials=_credentials(), cache_discovery=False)


def create_gmail_draft(subject: str, body: str, to: str = "") -> str:
    raw = base64.urlsafe_b64encode(to_eml_bytes(subject, body, to=to)).decode()
    try:
        draft = _service("gmail", "v1").users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    except ExportError:
        raise
    except Exception as exc:
        raise ExportError(f"Création du brouillon Gmail impossible : {exc}") from exc
    return draft.get("id", "")


def upload_docx_as_google_doc(title: str, docx_bytes: bytes) -> str:
    from googleapiclient.http import MediaIoBaseUpload

    body = {"name": title, "mimeType": "application/vnd.google-apps.document"}
    folder = config.secret("GOOGLE_DRIVE_FOLDER_ID")
    if folder:
        body["parents"] = [folder]
    media = MediaIoBaseUpload(io.BytesIO(docx_bytes), mimetype=DOCX_MIME, resumable=False)
    try:
        created = _service("drive", "v3").files().create(body=body, media_body=media, fields="id,webViewLink").execute()
    except ExportError:
        raise
    except Exception as exc:
        raise ExportError(f"Dépôt dans Google Drive impossible : {exc}") from exc
    return created.get("webViewLink", "")


def week_events(days: int = 7) -> list[dict]:
    """Événements des `days` derniers jours de l'agenda principal."""
    now = datetime.utcnow()
    try:
        items = (
            _service("calendar", "v3")
            .events()
            .list(
                calendarId="primary",
                timeMin=(now - timedelta(days=days)).isoformat() + "Z",
                timeMax=now.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
                maxResults=250,
            )
            .execute()
            .get("items", [])
        )
    except ExportError:
        raise
    except Exception as exc:
        raise ExportError(f"Lecture de Google Agenda impossible : {exc}") from exc
    events = []
    for it in items:
        start, end = it.get("start", {}), it.get("end", {})
        if "dateTime" in start and "dateTime" in end:
            s = datetime.fromisoformat(start["dateTime"])
            e = datetime.fromisoformat(end["dateTime"])
            events.append(
                {
                    "title": it.get("summary", "(sans titre)"),
                    "start": s.strftime("%d/%m %H:%M"),
                    "minutes": int((e - s).total_seconds() // 60),
                }
            )
        else:
            events.append({"title": it.get("summary", "(sans titre)"), "start": start.get("date", ""), "minutes": 0})
    return events


def test_connection() -> str:
    try:
        items = _service("calendar", "v3").calendarList().list(maxResults=1).execute().get("items", [])
    except ExportError:
        raise
    except Exception as exc:
        raise ExportError(f"Test Google impossible : {exc}") from exc
    return items[0].get("summary", "agenda principal") if items else "connexion établie"
