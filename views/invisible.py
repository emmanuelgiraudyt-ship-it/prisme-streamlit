import streamlit as st

from prisme import content, ui


def render() -> None:
    ui.header(
        "Module 08",
        "L'Invisible du Cabinet",
        "Les dimensions non écrites de la fonction : ce que les textes ne codifient pas. Dialogue suivi.",
    )
    for titre, texte in content.INVISIBLE_ENTRIES:
        with st.expander(titre):
            st.markdown(f"*{texte}*")

    st.subheader("Dialogue de cabinet")
    thread = st.session_state.setdefault("inv_thread", [])
    for m in thread:
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            st.markdown(m["content"])
    question = st.chat_input("Posez une question sur une situation de cabinet non codifiée…")
    if question:
        enveloppe = (
            "Un directeur de cabinet pose la question suivante sur les dimensions non écrites de sa fonction : "
            f"« {question} ». Réponds avec la nuance d'un praticien expérimenté, sans généralité creuse, en "
            "tenant compte de l'échange précédent le cas échéant."
        )
        history = [{"role": m["role"], "content": m.get("api", m["content"])} for m in thread]
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            res = ui.ask(enveloppe, module="Invisible", history=history)
            if res:
                st.markdown(res.text)
        if res:
            thread.append({"role": "user", "content": question, "api": enveloppe})
            thread.append({"role": "assistant", "content": res.text})
    if thread and st.button("Nouveau dialogue"):
        st.session_state["inv_thread"] = []
        st.rerun()
