"""Authentification par identifiant et mot de passe, un espace de données par identifiant."""

from __future__ import annotations

import hashlib
import hmac
import secrets as pysecrets
import time

import streamlit as st

from . import config

ITERATIONS = 240_000
MAX_FAILS = 5


def hash_password(password: str, salt: str | None = None, iterations: int = ITERATIONS) -> str:
    salt = salt or pysecrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def verify_password(stored: str, supplied: str) -> bool:
    stored = str(stored)
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, expected = stored.split("$")
            digest = hashlib.pbkdf2_hmac("sha256", supplied.encode(), salt.encode(), int(iterations))
        except ValueError:
            return False
        return hmac.compare_digest(digest.hex(), expected)
    return hmac.compare_digest(stored.encode(), supplied.encode())


def load_users() -> dict[str, str]:
    return {str(k).strip().lower(): str(v) for k, v in config.secret_table("users").items()}


def authenticate(username: str, password: str, users: dict[str, str] | None = None) -> str | None:
    users = load_users() if users is None else users
    key = username.strip().lower()
    stored = users.get(key)
    if stored is None:
        verify_password("pbkdf2_sha256$1$00$00", password)  # temps constant approximatif
        return None
    return key if verify_password(stored, password) else None


def logout() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def require_login() -> bool:
    """Affiche le formulaire de connexion si nécessaire. Retourne True si l'accès est autorisé."""
    if config.flag("PRISME_AUTH_DISABLED"):
        st.session_state.setdefault("tenant", "local")
        return True
    if st.session_state.get("tenant"):
        return True

    users = load_users()
    st.markdown("## PRISME")
    if not users:
        st.error(
            "Aucun compte n'est configuré. Renseignez la section [users] des secrets "
            "(voir README) ou, pour un essai local uniquement, PRISME_AUTH_DISABLED=true."
        )
        return False

    fails = int(st.session_state.get("_fails", 0))
    if fails >= MAX_FAILS:
        st.error("Trop de tentatives. Rechargez la page pour réessayer.")
        return False
    with st.form("login"):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")
    if submitted:
        tenant = authenticate(username, password, users)
        if tenant:
            st.session_state["tenant"] = tenant
            st.session_state.pop("_fails", None)
            st.rerun()
        st.session_state["_fails"] = fails + 1
        time.sleep(min(2, fails + 1))
        st.error("Identifiant ou mot de passe incorrect.")
    return False
