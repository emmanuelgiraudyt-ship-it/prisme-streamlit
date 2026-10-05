import json

import streamlit as st

from prisme import APP_VERSION, config, exports, google_ws, ui


def render() -> None:
    c = ui.ctx()
    ui.header(
        "Module 10",
        "Paramètres et connexions",
        "Identité du cabinet, état des connecteurs, consommation, droits sur les données et cadre de conformité.",
    )
    st.subheader("Identité du cabinet")
    with st.form("params"):
        collectivite = st.text_input("Collectivité ou institution", c.settings.get("collectivite", ""))
        elu = st.text_input("Exécutif servi", c.settings.get("elu", ""))
        cabinet = st.text_input("Structure émettrice", c.settings.get("cabinet", ""))
        web = st.toggle("Recherche web active par défaut", value=bool(c.settings.get("web_default", True)))
        if st.form_submit_button("Enregistrer"):
            c.storage.save_settings(
                c.tenant,
                {
                    "collectivite": collectivite.strip(),
                    "elu": elu.strip(),
                    "cabinet": cabinet.strip(),
                    "web_default": web,
                },
            )
            st.success("Paramètres enregistrés : ils personnalisent désormais toutes les productions.")

    st.subheader("Connexions")
    for row in ui.integration_rows():
        etat = ":green[actif]" if row["actif"] else ":gray[non configuré]"
        st.markdown(f"**{row['nom']}** : {etat} ({row['detail']})")
    col1, col2, col3 = st.columns(3)
    if col1.button("Tester le modèle"):
        res = ui.ask("Réponds uniquement : OK.", module="Test", max_tokens=16)
        if res:
            st.success(f"Modèle opérationnel : {res.text[:60]}")
    if col2.button("Tester Notion", disabled=not exports.notion_configured()):
        try:
            st.success(f"Notion opérationnel : {exports.notion_test()}")
        except exports.ExportError as exc:
            st.error(str(exc))
    if col3.button("Tester Google", disabled=not google_ws.configured()):
        try:
            st.success(f"Google opérationnel : {google_ws.test_connection()}")
        except exports.ExportError as exc:
            st.error(str(exc))
    st.caption(
        "Les identifiants se saisissent dans les secrets de l'application (jamais dans cette interface). "
        "Gmail est limité à la création de brouillons : aucun courriel n'est envoyé."
    )

    st.subheader("Consommation")
    s = c.storage.usage_stats(c.tenant)
    m = st.columns(4)
    m[0].metric("Générations aujourd'hui", f"{s['today']} / {config.daily_limit()}")
    m[1].metric("Générations ce mois", s["month_calls"])
    m[2].metric("Jetons ce mois", f"{s['month_input'] + s['month_output']:,}".replace(",", " "))
    m[3].metric("Recherches web ce mois", s["month_searches"])

    st.subheader("Vos données")
    st.download_button(
        "Exporter toutes mes données (JSON)",
        data=json.dumps(c.storage.export_all(c.tenant), ensure_ascii=False, indent=2).encode(),
        file_name="prisme-donnees.json",
        mime="application/json",
    )
    with st.expander("Supprimer définitivement toutes mes données"):
        st.warning("Cette action efface paramètres, fiches, archives, main courante et historique de consommation.")
        if st.checkbox("Je confirme la suppression définitive") and st.button("Supprimer mes données"):
            c.storage.erase_all(c.tenant)
            st.success("Données supprimées.")

    st.subheader("Conformité et bon usage")
    st.markdown(
        "Les contenus produits par PRISME sont générés par intelligence artificielle : ils constituent des projets "
        "de documents, soumis à la relecture et à la validation du cabinet avant toute diffusion. Ne saisissez pas "
        "de données à caractère personnel sensibles dans les champs de l'application. L'usage professionnel en "
        "collectivité s'inscrit dans le cadre du RGPD et du règlement européen sur l'intelligence artificielle : "
        "PRISME est un outil d'aide à la rédaction et à l'analyse, la décision demeure humaine."
    )
    st.caption(f"PRISME v{APP_VERSION} · fournisseur de modèle : {config.provider()} · {config.model()}")
