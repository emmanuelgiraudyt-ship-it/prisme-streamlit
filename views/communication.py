import streamlit as st

from prisme import content, ui
from prisme.util import titrer


def render() -> None:
    ui.header(
        "Module 04",
        "Communication Manager",
        "Documents de communication institutionnelle calibrés par format, ton et audience, avec brief visuel Canva.",
    )
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        fmt = c1.selectbox("Format", content.FORMATS_COMM)
        ton = c2.selectbox("Ton", content.TONS)
        audience = c3.selectbox("Audience", content.AUDIENCES)
        sujet = st.text_area("Sujet", placeholder="Objet du document…", height=90)

    if st.button("Générer le document", type="primary", disabled=not sujet.strip()):
        res = ui.ask(
            f"Rédige un document de type « {fmt} », ton {ton.lower()}, destiné à l'audience « {audience} », "
            f"sur le sujet suivant : {sujet}. Respecte les codes du genre et les usages institutionnels français.",
            module="Communication",
            demo=f"communication:{fmt}",
        )
        if res:
            st.session_state["comm_out"] = res.text
    out = st.session_state.get("comm_out", "")
    ui.output_box(out, "Le document généré s'affichera ici.")
    ui.export_bar("comm", titrer(fmt, sujet), out, "Communication", canva=True)
