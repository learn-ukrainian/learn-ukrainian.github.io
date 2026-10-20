"""#11115: the Sources MCP server heals a stale long-lived database connection.

A server that has been up for days keeps process-wide SQLite connections. When
the database file is rewritten under one, the held connection raises
``DatabaseError: database disk image is malformed`` although a fresh connection
reads the file fine. These tests drive the real ``collection_stats`` tool (real
``_get_conn``/``_open_conn`` cache in ``wiki.sources_db``) against a temporary
database, break the held connection by truncating the file in place, and check
the discard-reopen-retry path, the typed failure and the request-log record.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import sqlite3
from pathlib import Path

import mcp
import pytest
import requests

SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"
ROW_COUNT = 400


def _load_sources_server():
    assert requests.__name__ == "requests"
    assert mcp.__name__ == "mcp"
    spec = importlib.util.spec_from_file_location("mcp_sources_db_self_heal_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def server():
    return _load_sources_server()


@pytest.fixture()
def sdb(server):
    """The ``wiki.sources_db`` module the server's tools use (importable once the server loaded)."""
    return importlib.import_module("wiki.sources_db")


@pytest.fixture()
def db(server, sdb, tmp_path, monkeypatch):
    path = tmp_path / "sources.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY, body TEXT)")
    conn.executemany("INSERT INTO textbooks (body) VALUES (?)", [("т" * 200,)] * ROW_COUNT)
    conn.commit()
    conn.close()
    monkeypatch.setattr(sdb, "SOURCES_DB_PATH", path)
    monkeypatch.setattr(sdb, "_conn", None)
    monkeypatch.setenv("LU_MCP_SOURCES_LOG_DIR", str(tmp_path / "logs"))
    yield path
    held = sdb._conn
    monkeypatch.setattr(sdb, "_conn", None)
    if held is not None:
        held.close()


def _stats(server, name: str = "collection_stats"):
    return asyncio.run(server._dispatch_tool_call(name, {}))


def _log_entries(tmp_path: Path) -> list[dict]:
    log = tmp_path / "logs" / "mcp-sources-requests.jsonl"
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def _truncate_in_place(path: Path) -> bytes:
    original = path.read_bytes()
    with open(path, "r+b") as handle:
        handle.truncate(5000)
    return original


def _restore_in_place(path: Path, original: bytes) -> None:
    with open(path, "r+b") as handle:
        handle.write(original)
        handle.truncate(len(original))


def test_held_connection_that_raises_database_error_is_replaced_and_call_succeeds(server, sdb, db, monkeypatch):
    content, is_error, _ = _stats(server)  # opens and caches the process-wide connection
    assert is_error is False and json.loads(content[0].text) == {"textbooks": ROW_COUNT}
    held = sdb._conn
    assert held is not None

    original = _truncate_in_place(db)
    with pytest.raises(sqlite3.DatabaseError, match="malformed"):
        held.execute("SELECT COUNT(*) FROM textbooks").fetchone()  # the held connection is bad

    # The file is healthy again by the time the server reopens (the incident's state:
    # a fresh connection reads the file fine).
    real_discard = server._discard_cached_connections

    def restore_then_discard(database):
        _restore_in_place(db, original)
        return real_discard(database)

    monkeypatch.setattr(server, "_discard_cached_connections", restore_then_discard)

    content, is_error, _ = _stats(server)
    assert is_error is False
    assert json.loads(content[0].text) == {"textbooks": ROW_COUNT}
    assert sdb._conn is not held and sdb._conn is not None


def test_persistent_failure_returns_typed_error_naming_the_database(server, sdb, db, tmp_path):
    _stats(server)
    _truncate_in_place(db)  # stays damaged: the reopen fails too

    content, is_error, typed = _stats(server)

    assert is_error is True
    payload = json.loads(content[0].text)
    assert payload == typed
    assert payload["status"] == "error"
    assert payload["error_code"] == "database_unavailable"
    assert payload["database"] == "sources.db"
    assert payload["error_class"] == "DatabaseError"
    assert payload["retried"] is True and payload["reopened"] is True
    assert str(tmp_path) not in content[0].text and "malformed" not in content[0].text


def test_wire_path_carries_the_typed_error_not_a_bare_tool_call_failed(server, sdb, db):
    _stats(server)
    _truncate_in_place(db)

    params = server.CallToolRequestParams(name="collection_stats", arguments={})
    result = asyncio.run(server._on_call_tool(None, params))

    assert result.is_error is True
    assert result.content[0].text != "Tool call failed: collection_stats."
    assert json.loads(result.content[0].text)["error_code"] == "database_unavailable"
    assert result.structured_content["database"] == "sources.db"


def test_recovered_self_heal_is_recorded_in_the_request_log(server, sdb, db, tmp_path, monkeypatch):
    _stats(server)
    original = _truncate_in_place(db)
    real_discard = server._discard_cached_connections

    def restore_then_discard(database):
        _restore_in_place(db, original)
        return real_discard(database)

    monkeypatch.setattr(server, "_discard_cached_connections", restore_then_discard)
    _stats(server)

    healed = _log_entries(tmp_path)[-1]
    assert healed["tool"] == "collection_stats"
    assert healed["self_heal"] == {
        "database": "sources.db",
        "error_class": "DatabaseError",
        "reopened": True,
        "recovered": True,
    }
    assert "error" not in healed
    assert str(tmp_path) not in json.dumps(healed)


def test_failed_self_heal_is_recorded_in_the_request_log(server, sdb, db, tmp_path):
    _stats(server)
    _truncate_in_place(db)
    _stats(server)

    failed = _log_entries(tmp_path)[-1]
    assert failed["self_heal"] == {
        "database": "sources.db",
        "error_class": "DatabaseError",
        "reopened": True,
        "recovered": False,
    }
    assert failed["error"].startswith("SourcesDatabaseUnavailable")
    assert str(tmp_path) not in json.dumps(failed)


def test_privacy_mode_log_keeps_self_heal_and_no_error_text(server, sdb, db, tmp_path):
    _stats(server)
    _truncate_in_place(db)
    asyncio.run(server._dispatch_tool_call("collection_stats", {"_privacy_mode": True}))

    entry = _log_entries(tmp_path)[-1]
    assert entry["privacy_mode"] is True
    assert entry["self_heal"]["recovered"] is False
    assert entry["error_class"] == "SourcesDatabaseUnavailable"
    assert "unavailable after reopen" not in json.dumps(entry)


def test_healthy_call_has_no_self_heal_field(server, sdb, db, tmp_path):
    _stats(server)
    assert "self_heal" not in _log_entries(tmp_path)[-1]


def test_database_error_that_is_not_a_stale_connection_is_not_retried(server, monkeypatch):
    calls: list[int] = []

    async def bad_query(_arguments):
        calls.append(1)
        raise sqlite3.OperationalError('fts5: syntax error near "("')

    monkeypatch.setattr(server, "handle_collection_stats", bad_query)
    content, is_error, typed = _stats(server)

    assert is_error is True and typed is None
    assert calls == [1]
    assert "fts5: syntax error" in content[0].text


def test_discard_covers_both_import_names_and_leaves_other_databases_alone(server, monkeypatch):
    class Store:
        def __init__(self) -> None:
            self._conn = object()

    class Vesum:
        _vesum_conn = object()
        closed = 0

        def close_vesum_conn(self) -> None:
            self.closed += 1
            self._vesum_conn = None

    short, full, vesum = Store(), Store(), Vesum()
    monkeypatch.setitem(server.sys.modules, "wiki.sources_db", short)
    monkeypatch.setitem(server.sys.modules, "scripts.wiki.sources_db", full)
    monkeypatch.setitem(server.sys.modules, "scripts.verification.vesum", vesum)
    monkeypatch.delitem(server.sys.modules, "verification.vesum", raising=False)

    assert server._discard_cached_connections("sources.db") is True
    assert short._conn is None and full._conn is None
    assert vesum._vesum_conn is not None and vesum.closed == 0

    assert server._discard_cached_connections("vesum.db") is True
    assert vesum._vesum_conn is None and vesum.closed == 1

    assert server._discard_cached_connections(None) is False  # nothing cached any more
