import streamlit as st

from prisme import content, ui
from prisme.util import titrer


def render() -> None:
    ui.header(
        "Module 06",
        "Rédaction institutionnelle",
        "Documents-type de cabinet, avec révision itérative et export vers les outils du cabinet.",
    )
    with st.container(border=True):
        typo = st.selectbox("Typologie", content.TYPOLOGIES)
        contenu = st.text_area(
            "Éléments de contenu", placeholder="Contexte, points à traiter, décisions attendues…", height=140
        )
    col1, col2, _ = st.columns([1, 1, 3])
    if col1.button("Générer", type="primary", disabled=not contenu.strip()):
        res = ui.ask(
            f"Rédige un document de type « {typo} » à partir des éléments suivants : {contenu}\n"
            "Respecte la structure canonique du genre (contexte, éléments de décision, options, recommandation, "
            "calendrier pour une note d'arbitrage ; objet, état des lieux, analyse, propositions, échéancier "
            "pour une note de synthèse). Concision, hiérarchisation, actionnabilité.",
            module="Rédaction",
        )
        if res:
            st.session_state["red_out"] = res.text
    out = st.session_state.get("red_out", "")
    if out and col2.button("Réviser le texte"):
        res = ui.ask(
            "Révise et améliore le texte suivant (clarté, registre institutionnel, orthographe, ponctuation "
            "française classique) sans en changer le fond :\n\n" + out,
            module="Rédaction",
        )
        if res:
            st.session_state["red_out"] = out = res.text
    ui.output_box(out, "Le document rédigé s'affichera ici.")
    ui.export_bar("red", titrer(typo, contenu), out, "Rédaction")
