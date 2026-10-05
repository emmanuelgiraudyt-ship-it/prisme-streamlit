import streamlit as st

from prisme import google_ws, llm, ui
from prisme.exports import ExportError

CIBLES = {"strategique": 60, "operationnel": 20, "imprevus": 20}
LIBELLES = {"strategique": "Stratégique", "operationnel": "Opérationnel", "imprevus": "Imprévus"}
CLASSIFICATION = (
    "Voici les événements d'agenda d'un directeur de cabinet sur la période écoulée (date, titre, durée en "
    "minutes).\n{events}\n\nClasse le temps en trois catégories de doctrine de cabinet : stratégique "
    "(préparation des décisions, arbitrages, vision, dossiers de fond), opérationnel (gestion courante, réunions "
    "de suivi, logistique), imprévus (urgences, sollicitations non planifiées). Réponds UNIQUEMENT par un objet "
    'JSON, sans texte autour, au format exact : {{"strategique": entier, "operationnel": entier, "imprevus": '
    'entier, "commentaire": "deux phrases d\'analyse"}} où les trois entiers sont des pourcentages dont la '
    "somme fait 100."
)


def _ics_events(data: bytes) -> list[dict]:
    from icalendar import Calendar

    events = []
    for comp in Calendar.from_ical(data).walk("VEVENT"):
        start, end = comp.get("DTSTART"), comp.get("DTEND")
        if not start:
            continue
        s = start.dt
        minutes = 0
        if end is not None and hasattr(s, "hour") and hasattr(end.dt, "hour"):
            minutes = int((end.dt - s).total_seconds() // 60)
        events.append(
            {
                "title": str(comp.get("SUMMARY", "(sans titre)")),
                "start": s.strftime("%d/%m %H:%M") if hasattr(s, "hour") else s.strftime("%d/%m"),
                "minutes": minutes,
            }
        )
    return events


def _classify(events: list[dict]) -> None:
    if not events:
        st.warning("Aucun événement exploitable sur la période.")
        return
    listing = "\n".join(f"{e['start']} | {e['title']} | {e['minutes']} min" for e in events[:150])
    res = ui.ask(CLASSIFICATION.format(events=listing), module="Agenda", max_tokens=600)
    if not res:
        return
    try:
        parsed = llm.extract_json(res.text)
        values = {k: int(float(parsed.get(k, 0))) for k in CIBLES}
    except (llm.LLMError, ValueError, TypeError) as exc:
        st.error(f"Analyse inexploitable : {exc}")
        return
    if sum(values.values()) > 0:
        st.session_state.update({f"ag_{k}": v for k, v in values.items()})
    st.session_state["ag_comment"] = str(parsed.get("commentaire", ""))


def render() -> None:
    ui.header(
        "Module 05",
        "Agenda 60·20·20",
        "Répartition du temps de cabinet : 60 % stratégique, 20 % opérationnel, 20 % imprévus.",
    )
    for k in CIBLES:
        st.session_state.setdefault(f"ag_{k}", {"strategique": 45, "operationnel": 35, "imprevus": 20}[k])

    with st.container(border=True):
        total = 0
        for k, cible in CIBLES.items():
            v = int(st.session_state[f"ag_{k}"])
            total += v
            st.metric(LIBELLES[k], f"{v} %", delta=f"{v - cible:+d} pts (cible {cible} %)")
            st.progress(min(max(v, 0), 100) / 100)
        st.caption(f"Total : {total} %" + ("" if total == 100 else " : doit être égal à 100 %"))
        if st.session_state.get("ag_comment"):
            st.markdown(f"> {st.session_state['ag_comment']}")

    st.subheader("Mesurer depuis une source")
    col1, col2 = st.columns(2)
    if col1.button(
        "Analyser mon Google Agenda (7 jours)",
        disabled=not google_ws.configured(),
        help=None if google_ws.configured() else "Renseigner les identifiants Google (voir README).",
    ):
        try:
            _classify(google_ws.week_events(7))
        except ExportError as exc:
            st.error(str(exc))
    fichier = col2.file_uploader("Ou importer un export d'agenda (.ics)", type=["ics"])
    if fichier is not None and st.button("Analyser le fichier .ics"):
        try:
            _classify(_ics_events(fichier.getvalue()))
        except Exception as exc:
            st.error(f"Fichier .ics illisible : {exc}")

    with st.expander("Ajuster manuellement"):
        cols = st.columns(3)
        for col, k in zip(cols, CIBLES, strict=True):
            col.number_input(f"{LIBELLES[k]} (%)", 0, 100, key=f"ag_{k}")
