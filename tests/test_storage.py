from prisme.storage import Storage


def test_isolation_between_tenants(tmp_path):
    s = Storage(tmp_path / "a.db")
    s.add_document("alpha", "Veille", "Titre A", "contenu alpha")
    s.add_document("beta", "Veille", "Titre B", "contenu beta")
    assert [d["title"] for d in s.list_documents("alpha")] == ["Titre A"]
    assert s.count_documents("beta") == 1


def test_search_and_delete(tmp_path):
    s = Storage(tmp_path / "a.db")
    doc_id = s.add_document("t", "Rédaction", "Note DGF", "réforme de la dotation")
    assert s.list_documents("t", "dotation")
    assert not s.list_documents("t", "introuvable")
    s.delete_document("autre", doc_id)
    assert s.count_documents("t") == 1
    s.delete_document("t", doc_id)
    assert s.count_documents("t") == 0


def test_settings_defaults_and_update(tmp_path):
    s = Storage(tmp_path / "a.db")
    assert s.get_settings("t")["web_default"] is True
    s.save_settings("t", {"collectivite": "Ville X", "web_default": False})
    got = s.get_settings("t")
    assert got["collectivite"] == "Ville X" and got["web_default"] is False and got["elu"] == ""


def test_communes_and_journal(tmp_path):
    s = Storage(tmp_path / "a.db")
    s.save_commune("t", "Gentilly", {"maire": "Maire", "adjoints": ["a"]})
    assert s.list_communes("t")["Gentilly"]["adjoints"] == ["a"]
    s.delete_commune("t", "Gentilly")
    assert s.list_communes("t") == {}
    s.journal_add("t", "premier")
    s.journal_add("t", "second")
    assert [e["text"] for e in s.journal_list("t")] == ["second", "premier"]
    s.journal_clear("t")
    assert s.journal_list("t") == []


def test_usage_and_erasure(tmp_path):
    s = Storage(tmp_path / "a.db")
    s.log_usage("t", "Veille", "m", 100, 50, 2)
    s.log_usage("t", "Veille", "m", 10, 5, 0)
    stats = s.usage_stats("t")
    assert stats["today"] == 2 and stats["month_input"] == 110 and stats["month_searches"] == 2
    s.add_document("t", "x", "y", "z")
    assert s.export_all("t")["documents"]
    s.erase_all("t")
    assert s.count_documents("t") == 0 and s.calls_today("t") == 0
