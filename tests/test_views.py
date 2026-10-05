from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from prisme.storage import get_storage

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = "from views import {m}\n{m}.render()"
VIEWS = [
    "dashboard",
    "cartographie",
    "veille",
    "communication",
    "agenda",
    "redaction",
    "crise",
    "invisible",
    "bibliotheque",
    "parametres",
]


def run(view, tenant="t1"):
    at = AppTest.from_string(SCRIPT.format(m=view), default_timeout=30)
    at.session_state["tenant"] = tenant
    return at.run()


def button(at, label):
    return next(b for b in at.button if b.label == label)


@pytest.mark.parametrize("view", VIEWS)
def test_every_view_renders(view):
    at = run(view)
    assert not at.exception, at.exception


def test_veille_generates_with_domains(fake_client):
    at = run("veille")
    at.text_area[1].set_value("réforme de la DGF").run()
    button(at, "Générer").click().run()
    assert not at.exception
    call = fake_client.calls[0]
    assert call["tools"][0]["allowed_domains"][0] == "lagazettedescommunes.com"
    assert "7 derniers jours" in call["messages"][-1]["content"]
    assert any("Réponse de test." in m.value for m in at.markdown)


def test_redaction_generate_then_archive(fake_client):
    at = run("redaction")
    at.text_area[0].set_value("Arbitrage sur le budget").run()
    button(at, "Générer").click().run()
    button(at, "Archiver").click().run()
    assert not at.exception
    assert get_storage().count_documents("t1") == 1
    assert get_storage().count_documents("autre") == 0


def test_cartographie_demo_is_fictional():
    at = run("cartographie")
    assert any("fictive" in i.value for i in at.info)


def test_crise_journal_roundtrip():
    at = run("crise")
    at.text_input[0].set_value("Appel de la préfecture")  # valeur de formulaire : validée par le clic
    next(b for b in at.button if b.label == "Horodater").click().run()
    assert [e["text"] for e in get_storage().journal_list("t1")] == ["Appel de la préfecture"]


def test_invisible_dialogue_keeps_history(fake_client):
    at = run("invisible")
    at.chat_input[0].set_value("Comment gérer un désaccord avec le DGS ?").run()
    assert not at.exception
    at.chat_input[0].set_value("Et si l'élu tranche contre mon avis ?").run()
    history = fake_client.calls[1]["messages"]
    assert len(history) == 3 and history[0]["role"] == "user" and history[1]["role"] == "assistant"


def test_agenda_classification_updates_gauges(fake_client, monkeypatch):
    from prisme import google_ws
    from tests.conftest import make_response

    fake_client.responses = [
        make_response('{"strategique": 55, "operationnel": 25, "imprevus": 20, "commentaire": "Bon équilibre."}')
    ]
    monkeypatch.setattr(google_ws, "configured", lambda: True)
    monkeypatch.setattr(
        google_ws, "week_events", lambda days=7: [{"title": "Arbitrage budget", "start": "01/10 09:00", "minutes": 90}]
    )
    at = run("agenda")
    button(at, "Analyser mon Google Agenda (7 jours)").click().run()
    assert not at.exception
    assert at.session_state["ag_strategique"] == 55 and at.session_state["ag_comment"] == "Bon équilibre."


def test_parametres_save_settings():
    at = run("parametres")
    at.text_input[0].set_value("Ville de Test")
    next(b for b in at.button if b.label == "Enregistrer").click().run()
    assert get_storage().get_settings("t1")["collectivite"] == "Ville de Test"


def test_login_gate_blocks_without_users(monkeypatch):
    monkeypatch.delenv("PRISME_AUTH_DISABLED")
    at = AppTest.from_string(
        "from prisme import auth\nimport streamlit as st\nif auth.require_login():\n    st.write('PRIVE')",
        default_timeout=30,
    ).run()
    assert any("Aucun compte" in e.value for e in at.error)
    assert not any("PRIVE" in m.value for m in at.markdown)


def test_login_success_and_failure(monkeypatch):
    from prisme import auth

    monkeypatch.delenv("PRISME_AUTH_DISABLED")
    monkeypatch.setenv("PRISME_USERS", '{"cabinet": "' + auth.hash_password("mot-de-passe-long") + '"}')
    monkeypatch.setattr("time.sleep", lambda s: None)
    script = "from prisme import auth\nimport streamlit as st\nif auth.require_login():\n    st.write('PRIVE ' + st.session_state['tenant'])"
    at = AppTest.from_string(script, default_timeout=30).run()
    at.text_input[0].set_value("cabinet")
    at.text_input[1].set_value("faux")
    at.button[0].click().run()
    assert any("incorrect" in e.value for e in at.error)
    at.text_input[0].set_value("cabinet")
    at.text_input[1].set_value("mot-de-passe-long")
    at.button[0].click().run()
    assert any("PRIVE cabinet" in m.value for m in at.markdown)


def test_app_entrypoint_boots_with_navigation():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=40).run()
    assert not at.exception, at.exception
    assert [t.value for t in at.title] == ["Tableau de bord"]
