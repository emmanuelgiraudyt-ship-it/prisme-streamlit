"""PRISME v5.0 : point d'entrée Streamlit."""

import streamlit as st

from prisme import APP_VERSION, auth, ui

st.set_page_config(page_title="PRISME", layout="wide", initial_sidebar_state="expanded")
ui.inject_css()

if not auth.require_login():
    st.stop()

from views import (  # noqa: E402
    agenda,
    bibliotheque,
    cartographie,
    communication,
    crise,
    dashboard,
    invisible,
    parametres,
    redaction,
    veille,
)

DEFINITIONS = [
    ("dashboard", "Tableau de bord", dashboard),
    ("cartographie", "Cartographie politique", cartographie),
    ("veille", "Veille institutionnelle", veille),
    ("communication", "Communication Manager", communication),
    ("agenda", "Agenda 60·20·20", agenda),
    ("redaction", "Rédaction institutionnelle", redaction),
    ("crise", "Protocole de crise", crise),
    ("invisible", "L'Invisible du Cabinet", invisible),
    ("bibliotheque", "Bibliothèque", bibliotheque),
    ("parametres", "Paramètres et connexions", parametres),
]
pages = {
    key: st.Page(module.render, title=title, url_path=key, default=(key == "dashboard"))
    for key, title, module in DEFINITIONS
}
ui.PAGES.clear()
ui.PAGES.update(pages)

navigation = st.navigation(list(pages.values()))
with st.sidebar:
    st.divider()
    st.markdown("**PRISME**")
    st.caption(f"v{APP_VERSION} · édité par EG Conseil & Lobbying")
    tenant = st.session_state.get("tenant", "local")
    st.caption(f"Espace : {tenant}")
    if tenant != "local" and st.button("Se déconnecter"):
        auth.logout()
        st.rerun()

navigation.run()
st.divider()
st.markdown(
    "<div class='prisme-foot'>Contenus générés par intelligence artificielle : relecture et validation du "
    "cabinet requises avant toute diffusion.</div>",
    unsafe_allow_html=True,
)
