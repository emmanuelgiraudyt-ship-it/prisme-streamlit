"""Configuration : variables d'environnement d'abord, puis st.secrets."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

APP_VERSION = "5.1.0"
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 4096


def secret(name: str, default: str | None = None) -> str | None:
    """Lit une valeur de configuration (environnement, puis st.secrets)."""
    value = os.environ.get(name)
    if value not in (None, ""):
        return value
    try:
        import streamlit as st

        if name in st.secrets:
            found = st.secrets[name]
            if not isinstance(found, Mapping):
                return str(found)
    except Exception:
        pass
    return default


def secret_table(name: str) -> dict:
    """Lit une table de configuration (section TOML de st.secrets ou JSON en variable d'environnement)."""
    raw = os.environ.get(f"PRISME_{name.upper()}")
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except ValueError:
            return {}
    try:
        import streamlit as st

        if name in st.secrets:
            found = st.secrets[name]
            if isinstance(found, Mapping):
                return {str(k): v for k, v in found.items()}
    except Exception:
        pass
    return {}


def flag(name: str) -> bool:
    return str(secret(name, "")).strip().lower() in {"1", "true", "yes", "oui"}


def provider() -> str:
    return str(secret("PRISME_PROVIDER", "anthropic")).strip().lower()


def model() -> str:
    if provider() == "anthropic":
        return str(secret("PRISME_MODEL", DEFAULT_MODEL))
    return str(secret("PRISME_OPENAI_MODEL", "mistral-large-latest"))


def daily_limit() -> int:
    try:
        return int(str(secret("PRISME_DAILY_LIMIT", "200")))
    except ValueError:
        return 200


def db_path() -> Path:
    return Path(str(secret("PRISME_DB_PATH", "data/prisme.db")))
