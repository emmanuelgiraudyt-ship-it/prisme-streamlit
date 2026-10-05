from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from prisme import demo, llm
from prisme.storage import Storage, get_storage

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = "from views import {m}\n{m}.render()"


@pytest.fixture(autouse=True)
def demo_mode(monkeypatch):
    monkeypatch.setenv("PRISME_DEMO_MODE", "true")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def run(view):
    at = AppTest.from_string(SCRIPT.format(m=view), default_timeout=30)
    at.session_state["tenant"] = "demo-tenant"
    return at.run()


def button(at, label):
    return next(b for b in at.button if b.label == label)


def test_generate_without_key_returns_marked_example(tmp_path):
    s = Storage(tmp_path / "d.db")
    res = llm.generate("q", "s", module="Veille", tenant="t", storage=s, demo_key="veille")
    assert demo.MARK in res.text and res.notice == demo.NOTICE and res.sources == []
    assert s.usage_stats("t")["month_calls"] == 1


def test_key_lookup_and_fallback():
    assert demo.respond("communication:Discours") != demo.respond("communication:Communiqué de presse")
    assert demo.respond("redaction:Note d'arbitrage") != demo.respond("redaction:Note de synthèse")
    assert demo.MARK in demo.respond("inconnu")
    assert demo.respond(echo="Texte").endswith(demo.REVISION_NOTE)
    assert demo.respond(echo=demo.respond(echo="Texte")).count(demo.REVISION_NOTE) == 1


def test_veille_flow_with_exports_and_archive():
    at = run("veille")
    at.text_area[1].set_value("dotations aux collectivités").run()
    button(at, "Générer").click().run()
    assert not at.exception, at.exception
    assert any(demo.MARK in m.value for m in at.markdown)
    assert any("Mode démonstration" in w.value for w in at.warning)
    button(at, "Archiver").click().run()
    docs = get_storage().list_documents("demo-tenant")
    assert len(docs) == 1 and demo.MARK in docs[0]["content"]


def test_redaction_generate_then_revise_keeps_text():
    at = run("redaction")
    at.text_area[0].set_value("Arbitrage sur un équipement scolaire").run()
    button(at, "Générer").click().run()
    first = at.session_state["red_out"]
    button(at, "Réviser le texte").click().run()
    assert at.session_state["red_out"].startswith(first) and demo.REVISION_NOTE in at.session_state["red_out"]


def test_communication_follows_selected_format():
    at = run("communication")
    at.selectbox[0].select("Discours")
    at.text_area[0].set_value("Ouverture de la concertation").run()
    button(at, "Générer le document").click().run()
    assert "Discours (exemple)" in at.session_state["comm_out"]


def test_invisible_dialogue_rotates_answers():
    at = run("invisible")
    at.chat_input[0].set_value("Première question").run()
    at.chat_input[0].set_value("Seconde question").run()
    answers = [m["content"] for m in at.session_state["inv_thread"] if "api" not in m]
    assert len(answers) == 2 and answers[0] != answers[1]


def test_agenda_classification_in_demo(monkeypatch):
    from prisme import google_ws

    monkeypatch.setattr(google_ws, "configured", lambda: True)
    monkeypatch.setattr(
        google_ws, "week_events", lambda days=7: [{"title": "x", "start": "01/10 09:00", "minutes": 60}]
    )
    at = run("agenda")
    button(at, "Analyser mon Google Agenda (7 jours)").click().run()
    assert not at.exception, at.exception
    assert at.session_state["ag_strategique"] == 52


def test_cartographie_crise_and_settings_in_demo():
    at = run("cartographie")
    button(at, "Générer la synthèse de cabinet").click().run()
    assert demo.MARK in at.session_state["carto_out"]
    at = run("crise")
    at.text_area[0].set_value("Incident sur la voie publique").run()
    button(at, "Générer la déclaration d'attente").click().run()
    assert "Déclaration d'attente (exemple)" in at.session_state["crise_out"]
    at = run("parametres")
    button(at, "Tester le modèle").click().run()
    assert any("OK (mode démonstration)" in s.value for s in at.success)


def test_app_shows_demo_banner_and_row(monkeypatch):
    monkeypatch.setenv("PRISME_AUTH_DISABLED", "true")
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=40).run()
    assert not at.exception, at.exception
    assert any("Mode démonstration" in i.value for i in at.info)


def test_without_demo_error_mentions_the_flag(monkeypatch):
    monkeypatch.delenv("PRISME_DEMO_MODE")
    with pytest.raises(llm.LLMError, match="PRISME_DEMO_MODE"):
        llm.generate("q", "s")
