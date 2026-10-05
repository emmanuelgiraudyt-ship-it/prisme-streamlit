"""Utilitaires : dates françaises, découpage de lignes, titres de documents."""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]


def now_paris() -> datetime:
    return datetime.now(PARIS)


def fr_date(dt: datetime | None = None, weekday: bool = True) -> str:
    dt = dt or now_paris()
    jour = f"{dt.day}er" if dt.day == 1 else str(dt.day)
    base = f"{jour} {MOIS[dt.month - 1]} {dt.year}"
    return f"{JOURS[dt.weekday()]} {base}" if weekday else base


def fr_datetime(iso: str) -> str:
    """Convertit un horodatage ISO (UTC) en 'JJ/MM/AAAA HH:MM' heure de Paris."""
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(PARIS).strftime("%d/%m/%Y %H:%M")


def lignes(text: str | None) -> list[str]:
    return [s.strip() for s in str(text or "").splitlines() if s.strip()]


def titrer(module: str, sujet: str = "") -> str:
    base = re.sub(r"\s+", " ", str(sujet or "")).strip()
    if len(base) > 64:
        base = base[:64].rstrip() + "…"
    return f"{module} : {base}" if base else f"{module} du {now_paris().strftime('%d/%m/%Y')}"


def slug(text: str, maxlen: int = 60) -> str:
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    norm = re.sub(r"[^A-Za-z0-9]+", "-", norm).strip("-").lower()
    return (norm or "document")[:maxlen]
