from types import SimpleNamespace

import pytest

from prisme import llm


def make_response(text="Réponse de test.", citations=None, stop_reason="end_turn", searches=0):
    block = SimpleNamespace(type="text", text=text, citations=citations or [])
    usage = SimpleNamespace(
        input_tokens=11, output_tokens=22, server_tool_use=SimpleNamespace(web_search_requests=searches)
    )
    return SimpleNamespace(content=[block], stop_reason=stop_reason, usage=usage)


class FakeClient:
    def __init__(self, responses=None):
        self.responses = list(responses or [make_response()])
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PRISME_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("PRISME_AUTH_DISABLED", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    for name in (
        "NOTION_TOKEN",
        "NOTION_PARENT_PAGE_ID",
        "NOTION_DATABASE_ID",
        "GOOGLE_REFRESH_TOKEN",
        "PRISME_PROVIDER",
        "PRISME_DAILY_LIMIT",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(llm, "_client_factory", None)


@pytest.fixture
def fake_client(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(llm, "_client_factory", lambda: client)
    return client
