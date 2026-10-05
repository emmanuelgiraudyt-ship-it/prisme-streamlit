from prisme import auth


def test_hash_roundtrip():
    h = auth.hash_password("un-mot-de-passe-solide")
    assert h.startswith("pbkdf2_sha256$")
    assert auth.verify_password(h, "un-mot-de-passe-solide")
    assert not auth.verify_password(h, "autre")


def test_plain_and_malformed():
    assert auth.verify_password("secret", "secret")
    assert not auth.verify_password("secret", "Secret")
    assert not auth.verify_password("pbkdf2_sha256$abc", "x")


def test_authenticate():
    users = {"cabinet": auth.hash_password("pw-long-1234"), "demo": "demo-pw"}
    assert auth.authenticate("Cabinet ", "pw-long-1234", users) == "cabinet"
    assert auth.authenticate("demo", "demo-pw", users) == "demo"
    assert auth.authenticate("cabinet", "faux", users) is None
    assert auth.authenticate("inconnu", "x", users) is None


def test_load_users_from_env(monkeypatch):
    monkeypatch.setenv("PRISME_USERS", '{"Alice": "pw"}')
    assert auth.load_users() == {"alice": "pw"}
