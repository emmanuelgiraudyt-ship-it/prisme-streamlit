"""Persistance SQLite, cloisonnée par espace client (tenant)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from .util import now_paris

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings(
    tenant TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(tenant, key));
CREATE TABLE IF NOT EXISTS documents(
    id TEXT PRIMARY KEY, tenant TEXT NOT NULL, created_at TEXT NOT NULL,
    module TEXT NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_documents_tenant ON documents(tenant, created_at DESC);
CREATE TABLE IF NOT EXISTS communes(
    tenant TEXT NOT NULL, name TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(tenant, name));
CREATE TABLE IF NOT EXISTS journal(
    id INTEGER PRIMARY KEY AUTOINCREMENT, tenant TEXT NOT NULL, ts TEXT NOT NULL, text TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS usage(
    id INTEGER PRIMARY KEY AUTOINCREMENT, tenant TEXT NOT NULL, ts TEXT NOT NULL, day TEXT NOT NULL,
    module TEXT, model TEXT, input_tokens INTEGER DEFAULT 0, output_tokens INTEGER DEFAULT 0,
    searches INTEGER DEFAULT 0);
CREATE INDEX IF NOT EXISTS idx_usage_tenant_day ON usage(tenant, day);
"""

DEFAULT_SETTINGS = {"collectivite": "", "elu": "", "cabinet": "", "web_default": True}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Storage:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as con:
            con.executescript(SCHEMA)

    @contextmanager
    def _conn(self):
        con = sqlite3.connect(self.path, timeout=15)
        con.row_factory = sqlite3.Row
        try:
            try:
                con.execute("PRAGMA journal_mode=WAL")
            except sqlite3.DatabaseError:
                pass
            yield con
            con.commit()
        finally:
            con.close()

    # Paramètres
    def get_settings(self, tenant: str) -> dict:
        with self._conn() as con:
            row = con.execute("SELECT value FROM settings WHERE tenant=? AND key='settings'", (tenant,)).fetchone()
        stored = json.loads(row["value"]) if row else {}
        return {**DEFAULT_SETTINGS, **stored}

    def save_settings(self, tenant: str, settings: dict) -> None:
        with self._conn() as con:
            con.execute(
                "INSERT INTO settings(tenant,key,value) VALUES(?,?,?) "
                "ON CONFLICT(tenant,key) DO UPDATE SET value=excluded.value",
                (tenant, "settings", json.dumps(settings, ensure_ascii=False)),
            )

    # Bibliothèque
    def add_document(self, tenant: str, module: str, title: str, content: str) -> str:
        doc_id = uuid.uuid4().hex
        with self._conn() as con:
            con.execute(
                "INSERT INTO documents(id,tenant,created_at,module,title,content) VALUES(?,?,?,?,?,?)",
                (doc_id, tenant, _utc_now(), module, title, content),
            )
        return doc_id

    def list_documents(self, tenant: str, query: str = "", limit: int = 500) -> list[dict]:
        sql = "SELECT * FROM documents WHERE tenant=?"
        params: list = [tenant]
        if query.strip():
            sql += " AND (title LIKE ? OR module LIKE ? OR content LIKE ?)"
            params += [f"%{query.strip()}%"] * 3
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._conn() as con:
            return [dict(r) for r in con.execute(sql, params).fetchall()]

    def count_documents(self, tenant: str) -> int:
        with self._conn() as con:
            return con.execute("SELECT COUNT(*) FROM documents WHERE tenant=?", (tenant,)).fetchone()[0]

    def delete_document(self, tenant: str, doc_id: str) -> None:
        with self._conn() as con:
            con.execute("DELETE FROM documents WHERE tenant=? AND id=?", (tenant, doc_id))

    # Collectivités
    def list_communes(self, tenant: str) -> dict[str, dict]:
        with self._conn() as con:
            rows = con.execute("SELECT name,data FROM communes WHERE tenant=? ORDER BY name", (tenant,))
            return {r["name"]: json.loads(r["data"]) for r in rows.fetchall()}

    def save_commune(self, tenant: str, name: str, data: dict) -> None:
        with self._conn() as con:
            con.execute(
                "INSERT INTO communes(tenant,name,data) VALUES(?,?,?) "
                "ON CONFLICT(tenant,name) DO UPDATE SET data=excluded.data",
                (tenant, name, json.dumps(data, ensure_ascii=False)),
            )

    def delete_commune(self, tenant: str, name: str) -> None:
        with self._conn() as con:
            con.execute("DELETE FROM communes WHERE tenant=? AND name=?", (tenant, name))

    # Main courante
    def journal_add(self, tenant: str, text: str) -> None:
        with self._conn() as con:
            con.execute("INSERT INTO journal(tenant,ts,text) VALUES(?,?,?)", (tenant, _utc_now(), text))

    def journal_list(self, tenant: str, limit: int = 300) -> list[dict]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT id,ts,text FROM journal WHERE tenant=? ORDER BY id DESC LIMIT ?", (tenant, limit)
            )
            return [dict(r) for r in rows.fetchall()]

    def journal_clear(self, tenant: str) -> None:
        with self._conn() as con:
            con.execute("DELETE FROM journal WHERE tenant=?", (tenant,))

    # Consommation
    def log_usage(
        self, tenant: str, module: str, model: str, input_tokens: int, output_tokens: int, searches: int
    ) -> None:
        with self._conn() as con:
            con.execute(
                "INSERT INTO usage(tenant,ts,day,module,model,input_tokens,output_tokens,searches) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (
                    tenant,
                    _utc_now(),
                    now_paris().strftime("%Y-%m-%d"),
                    module,
                    model,
                    int(input_tokens),
                    int(output_tokens),
                    int(searches),
                ),
            )

    def calls_today(self, tenant: str) -> int:
        day = now_paris().strftime("%Y-%m-%d")
        with self._conn() as con:
            return con.execute("SELECT COUNT(*) FROM usage WHERE tenant=? AND day=?", (tenant, day)).fetchone()[0]

    def usage_stats(self, tenant: str) -> dict:
        month = now_paris().strftime("%Y-%m") + "-%"
        with self._conn() as con:
            row = con.execute(
                "SELECT COUNT(*) c, COALESCE(SUM(input_tokens),0) i, COALESCE(SUM(output_tokens),0) o, "
                "COALESCE(SUM(searches),0) s FROM usage WHERE tenant=? AND day LIKE ?",
                (tenant, month),
            ).fetchone()
        return {
            "today": self.calls_today(tenant),
            "month_calls": row["c"],
            "month_input": row["i"],
            "month_output": row["o"],
            "month_searches": row["s"],
        }

    # Droits des personnes (portabilité et effacement)
    def export_all(self, tenant: str) -> dict:
        return {
            "tenant": tenant,
            "exported_at": _utc_now(),
            "settings": self.get_settings(tenant),
            "documents": self.list_documents(tenant, limit=100000),
            "communes": self.list_communes(tenant),
            "journal": self.journal_list(tenant, limit=100000),
        }

    def erase_all(self, tenant: str) -> None:
        with self._conn() as con:
            for table in ("settings", "documents", "communes", "journal", "usage"):
                con.execute(f"DELETE FROM {table} WHERE tenant=?", (tenant,))


_STORAGE: dict[str, Storage] = {}


def get_storage() -> Storage:
    from . import config

    path = str(config.db_path())
    if path not in _STORAGE:
        _STORAGE[path] = Storage(path)
    return _STORAGE[path]
