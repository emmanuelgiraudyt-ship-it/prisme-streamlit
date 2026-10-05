import streamlit as st

from prisme import config, content, ui
from prisme.util import fr_date, fr_datetime


def render() -> None:
    c = ui.ctx()
    sub = "Poste de commandement du cabinet"
    if c.settings.get("collectivite"):
        sub += f" : {c.settings['collectivite']}"
    ui.header("Module 01", "Tableau de bord", f"{sub}. {fr_date().capitalize()}.")

    stats = c.storage.usage_stats(c.tenant)
    communes = len(content.COMMUNES_DEMO) + len(c.storage.list_communes(c.tenant))
    cols = st.columns(4)
    cols[0].metric("Documents archivés", c.storage.count_documents(c.tenant))
    cols[1].metric("Collectivités suivies", communes)
    cols[2].metric("Entrées de main courante", len(c.storage.journal_list(c.tenant)))
    cols[3].metric("Générations aujourd'hui", f"{stats['today']} / {config.daily_limit()}")

    st.subheader("Actions rapides")
    quick = st.columns(4)
    for col, (label, key) in zip(
        quick,
        [
            ("Lancer une veille", "veille"),
            ("Rédiger une note", "redaction"),
            ("Analyser l'agenda", "agenda"),
            ("Protocole de crise", "crise"),
        ],
        strict=True,
    ):
        if col.button(label, key=f"quick_{key}", use_container_width=True):
            ui.goto(key)

    st.subheader("Derniers documents")
    docs = c.storage.list_documents(c.tenant, limit=3)
    if not docs:
        st.caption("Aucun document archivé. Les productions des modules s'archivent d'un clic dans la bibliothèque.")
    for d in docs:
        st.markdown(f"`{fr_datetime(d['created_at'])}` {d['title']}")

    st.subheader("Connexions")
    for row in ui.integration_rows():
        etat = f":green[actif] ({row['detail']})" if row["actif"] else ":gray[non configuré]"
        st.markdown(f"**{row['nom']}** : {etat}")
    st.caption("Détail et configuration dans Paramètres et connexions.")
