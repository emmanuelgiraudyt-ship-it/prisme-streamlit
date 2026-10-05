import streamlit as st

from prisme import content, ui
from prisme.util import lignes, titrer

SECTIONS = [
    ("Adjoints et délégations", "adjoints", "liste"),
    ("Commissions sensibles", "commissions", "puces"),
    ("Projets de mandat", "projets", "liste"),
    ("Tensions identifiées", "tensions", "puces"),
    ("Alertes institutionnelles", "alertes", "puces"),
    ("Agenda du conseil municipal probable", "agendaCM", "liste"),
]


def render() -> None:
    c = ui.ctx()
    ui.header(
        "Module 02",
        "Cartographie politique",
        "Équilibres d'exécutif, délégations, dossiers sensibles et points de tension, avec fiches personnalisées mémorisées.",
    )
    custom = c.storage.list_communes(c.tenant)
    toutes = {**content.COMMUNES_DEMO, **custom}

    if "_carto_next" in st.session_state:
        st.session_state["carto_commune"] = st.session_state.pop("_carto_next")
    names = list(toutes)
    if st.session_state.get("carto_commune") not in names:
        st.session_state["carto_commune"] = names[0]
    commune = st.selectbox("Collectivité", names, key="carto_commune")
    data = toutes[commune]

    left, mid, right = st.columns([1, 1, 2])
    enrichir = right.toggle("Enrichir par recherche web", key="carto_web")
    if commune in custom and mid.button("Supprimer cette fiche"):
        c.storage.delete_commune(c.tenant, commune)
        st.rerun()
    with left.popover("Ajouter une collectivité"):
        st.caption(
            "Une étiquette politique rattachée à une personne identifiable relève des catégories particulières "
            "de données (article 9 du RGPD). Limitez-vous à des informations publiques et à un hébergement adapté."
        )
        with st.form("carto_form", clear_on_submit=True):
            nom = st.text_input("Nom de la collectivité")
            maire = st.text_input("Exécutif (étiquette, mandat)")
            adjoints = st.text_area("Adjoints et délégations (un par ligne)", height=90)
            commissions = st.text_area("Commissions sensibles (une par ligne)", height=70)
            projets = st.text_area("Projets de mandat (un par ligne)", height=70)
            tensions = st.text_area("Tensions identifiées (une par ligne)", height=70)
            alertes = st.text_area("Alertes institutionnelles (une par ligne)", height=70)
            agenda = st.text_area("Agenda du conseil (un point par ligne)", height=70)
            if st.form_submit_button("Enregistrer la fiche"):
                if not nom.strip() or not maire.strip():
                    st.error("Le nom et l'exécutif sont requis.")
                else:
                    c.storage.save_commune(
                        c.tenant,
                        nom.strip(),
                        {
                            "maire": maire.strip(),
                            "adjoints": lignes(adjoints),
                            "commissions": lignes(commissions),
                            "projets": lignes(projets),
                            "tensions": lignes(tensions),
                            "alertes": lignes(alertes),
                            "agendaCM": lignes(agenda),
                        },
                    )
                    st.session_state["_carto_next"] = nom.strip()
                    st.rerun()

    if data.get("demo"):
        st.info("Fiche d'exemple fictive : ajoutez vos collectivités réelles avec le bouton prévu à cet effet.")
    with st.container(border=True):
        st.markdown(f"**Exécutif** : {data['maire']}")
        for titre, key, mode in SECTIONS:
            items = data.get(key) or []
            st.markdown(f"**{titre}**")
            if not items:
                st.caption("Aucun élément renseigné.")
            elif mode == "liste":
                st.markdown("\n".join(f"- {i}" for i in items))
            else:
                st.markdown(" ".join(f"`{i}`" for i in items))

    if st.button("Générer la synthèse de cabinet", type="primary"):
        prompt = (
            f"Rédige une synthèse de cartographie politique pour la collectivité « {commune} », à destination du "
            "directeur de cabinet, à partir des éléments déclaratifs suivants"
            + (
                ", que tu peux compléter par une recherche web sur l'actualité institutionnelle récente de cette "
                "collectivité, en distinguant clairement ce qui provient de la recherche"
                if enrichir
                else ", sans les enrichir d'informations non fournies"
            )
            + f" :\nExécutif : {data['maire']}\n"
            + "\n".join(f"{t} : {'; '.join(data.get(k) or [])}" for t, k, _ in SECTIONS)
            + "\nFormat : quatre paragraphes courts : équilibre politique, dossiers à enjeu, points de vigilance, "
            "recommandation d'action pour la semaine."
        )
        res = ui.ask(prompt, module="Cartographie", web=enrichir, demo="cartographie")
        if res:
            st.session_state["carto_out"] = res.with_sources()
    out = st.session_state.get("carto_out", "")
    ui.output_box(out, "La synthèse de cartographie politique s'affichera ici.")
    ui.export_bar("carto", titrer("Cartographie", commune), out, "Cartographie")
