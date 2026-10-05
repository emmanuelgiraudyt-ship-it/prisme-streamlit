import streamlit as st

from prisme import content, ui
from prisme.util import lignes, titrer


def render() -> None:
    c = ui.ctx()
    ui.header(
        "Module 03",
        "Veille institutionnelle",
        "Suivi réglementaire, législatif et médiatique appuyé sur la recherche web, mis en forme pour l'action de cabinet.",
    )
    with st.container(border=True):
        col1, col2 = st.columns(2)
        mode = col1.selectbox("Format de sortie", list(content.MODES_VEILLE))
        periode = col2.selectbox("Période", list(content.PERIODES_VEILLE), index=1)
        web = st.toggle("Recherche web en direct", value=bool(c.settings.get("web_default", True)), key="veille_web")
        restreint = st.toggle(
            "Restreindre aux sources institutionnelles et à la presse spécialisée",
            value=True,
            key="veille_restreint",
            disabled=not web,
        )
        domaines = lignes(
            st.text_area(
                "Domaines autorisés (un par ligne)",
                value="\n".join(content.DOMAINES_INSTITUTIONNELS),
                height=120,
                disabled=not (web and restreint),
            )
        )
        sujet = st.text_area(
            "Sujet de veille",
            placeholder="Ex. réforme de la DGF, décret d'application du CGCT, jurisprudence du Conseil d'État sur les DSP…",
            height=90,
        )

    if st.button("Générer", type="primary", disabled=not sujet.strip()):
        fenetre = content.PERIODES_VEILLE[periode]
        prompt = f"{content.MODES_VEILLE[mode]} : {sujet}\n"
        if web:
            prompt += (
                "Appuie-toi sur la recherche web ; cite chaque source (média ou institution, date). "
                + (f"Ne retiens que les informations publiées pendant {fenetre}. " if fenetre else "")
                + "Si aucune information récente et vérifiable n'est trouvée, dis-le explicitement plutôt "
                "que de combler par supposition."
            )
        else:
            prompt += (
                "Travaille sans recherche web, à partir du droit et des mécanismes institutionnels stables, "
                "et signale toute donnée susceptible d'avoir évolué."
            )
        res = ui.ask(
            prompt,
            module="Veille",
            demo="veille",
            web=web,
            domains=domaines if (web and restreint and domaines) else None,
        )
        if res:
            st.session_state["veille_out"] = res.with_sources()
    out = st.session_state.get("veille_out", "")
    ui.output_box(out, "Le résultat de la veille s'affichera ici.")
    ui.export_bar("veille", titrer("Veille", sujet), out, "Veille")
