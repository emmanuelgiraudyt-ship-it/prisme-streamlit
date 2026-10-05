import time

import streamlit as st

from prisme import content, exports, ui
from prisme.util import fr_datetime, titrer


def _elapsed() -> float:
    start = st.session_state.get("crise_start")
    return st.session_state.get("crise_acc", 0.0) + (time.time() - start if start else 0.0)


def _chrono(color: str) -> None:
    s = int(_elapsed())
    st.markdown(
        f"<div class='prisme-chrono' style='color:{color}'>{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}</div>",
        unsafe_allow_html=True,
    )


def render() -> None:
    c = ui.ctx()
    ui.header(
        "Module 07",
        "Protocole de crise",
        "Niveaux d'alerte, chronomètre, protocole H+1 à H+72, déclaration d'attente et main courante horodatée.",
    )
    labels = [n["label"] for n in content.NIVEAUX_CRISE]
    niveau = st.radio("Niveau d'alerte", labels, horizontal=True, key="crise_niveau")
    color = content.NIVEAUX_CRISE[labels.index(niveau)]["color"]
    running = st.session_state.get("crise_start") is not None

    with st.container(border=True):
        left, right = st.columns([2, 3])
        with left:
            st.fragment(_chrono, run_every=1 if running else None)(color)
        if right.button("Pause" if running else "Démarrer", key="crise_toggle"):
            if running:
                st.session_state["crise_acc"] = _elapsed()
                st.session_state["crise_start"] = None
            else:
                st.session_state["crise_start"] = time.time()
            st.rerun()
        if right.button("Réinitialiser", key="crise_reset"):
            st.session_state["crise_start"] = None
            st.session_state["crise_acc"] = 0.0
            st.rerun()

    st.subheader("Protocole d'intervention")
    for h, action in content.PROTOCOLE_H:
        st.markdown(f"**{h}** : {action}")

    st.subheader("Élément de langage immédiat")
    situation = st.text_area(
        "Description factuelle de la situation",
        placeholder="Faits établis, lieu, personnes ou services concernés, ce qui est déjà engagé…",
        height=100,
    )
    if st.button("Générer la déclaration d'attente", type="primary", disabled=not situation.strip()):
        res = ui.ask(
            f"Situation de crise (niveau {niveau}) : {situation}\nRédige un élément de langage initial "
            "(déclaration d'attente) de 120 mots au maximum, prêt à être prononcé par l'élu ou son porte-parole : "
            "faits établis uniquement, empathie mesurée envers les personnes concernées, action engagée, annonce "
            "d'un prochain point d'information. Aucune spéculation, aucune reconnaissance de responsabilité "
            "prématurée.",
            module="Crise",
            max_tokens=700,
        )
        if res:
            st.session_state["crise_out"] = res.text
    out = st.session_state.get("crise_out", "")
    ui.output_box(out, "La déclaration d'attente s'affichera ici.")
    ui.export_bar("crise", titrer("Déclaration de crise", situation), out, "Crise")

    st.subheader("Main courante horodatée")
    with st.form("journal_form", clear_on_submit=True):
        entree = st.text_input("Nouvelle entrée : fait, décision, appel reçu…")
        if st.form_submit_button("Horodater") and entree.strip():
            c.storage.journal_add(c.tenant, entree.strip())
            st.rerun()
    entries = c.storage.journal_list(c.tenant)
    if not entries:
        st.caption("Aucune entrée pour le moment.")
    for e in entries:
        st.markdown(f"`{fr_datetime(e['ts'])}` {e['text']}")
    if entries:
        col1, col2, _ = st.columns([1, 1, 2])
        if col1.button("Consigner dans Notion", disabled=not exports.notion_configured()):
            corps = "\n".join(f"{fr_datetime(e['ts'])} : {e['text']}" for e in reversed(entries))
            try:
                url = exports.notion_create_page(titrer("Main courante de crise"), corps)
                st.success(f"Main courante consignée dans Notion. {url}")
            except exports.ExportError as exc:
                st.error(str(exc))
        if col2.button("Réinitialiser la main courante"):
            c.storage.journal_clear(c.tenant)
            st.rerun()
