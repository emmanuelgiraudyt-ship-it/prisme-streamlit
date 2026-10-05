import streamlit as st

from prisme import ui
from prisme.util import fr_datetime


def render() -> None:
    c = ui.ctx()
    ui.header(
        "Module 09",
        "Bibliothèque du cabinet",
        "Documents produits et archivés, conservés d'une session à l'autre, exportables vers Word, Notion et Google.",
    )
    query = st.text_input("Recherche dans les archives", placeholder="Titre, module, contenu…")
    docs = c.storage.list_documents(c.tenant, query)
    if not docs:
        st.info("Aucun document archivé. Le bouton « Archiver » de chaque module dépose la production ici.")
    for d in docs:
        with st.expander(f"{fr_datetime(d['created_at'])} · {d['module']} · {d['title']}"):
            st.markdown(d["content"])
            ui.export_bar(f"lib_{d['id']}", d["title"], d["content"], d["module"], archive=False)
            if st.button("Supprimer des archives", key=f"del_{d['id']}"):
                c.storage.delete_document(c.tenant, d["id"])
                st.rerun()
