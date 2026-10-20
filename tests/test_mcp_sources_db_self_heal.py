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
import inspect
import json
import sqlite3
import sys
import threading
from pathlib import Path
from typing import ClassVar

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

    def restore_then_discard(database, seen=None):
        _restore_in_place(db, original)
        return real_discard(database, seen)

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

    def restore_then_discard(database, seen=None):
        _restore_in_place(db, original)
        return real_discard(database, seen)

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
    old_short, old_full = short._conn, full._conn
    monkeypatch.setitem(server.sys.modules, "wiki.sources_db", short)
    monkeypatch.setitem(server.sys.modules, "scripts.wiki.sources_db", full)
    monkeypatch.setitem(server.sys.modules, "scripts.verification.vesum", vesum)
    monkeypatch.delitem(server.sys.modules, "verification.vesum", raising=False)
    monkeypatch.setattr(server, "_open_observed_sources_conn", lambda module: object())

    assert server._discard_cached_connections("sources.db") is True
    assert short._conn is not None and short._conn is not old_short
    assert full._conn is not None and full._conn is not old_full
    assert short._conn is not full._conn
    assert vesum._vesum_conn is not None and vesum.closed == 0

    assert server._discard_cached_connections("vesum.db") is True
    assert vesum._vesum_conn is None and vesum.closed == 1

    assert server._discard_cached_connections("vesum.db") is False  # nothing cached any more


# --- #11115 round 2: false recovery, connection race, WikiCache close ---------


def _add_dictionary_tables(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE style_guide (id INTEGER PRIMARY KEY, word TEXT, text TEXT)")
    conn.execute("INSERT INTO style_guide (word, text) VALUES ('Приймати участь', 'брати участь')")
    conn.execute("CREATE TABLE grinchenko (id INTEGER PRIMARY KEY, word TEXT, text TEXT)")
    conn.execute("INSERT INTO grinchenko (word, text) VALUES ('Вода', 'рідина')")
    conn.commit()
    conn.close()


def _failing_connection_opener(server, path: Path, message: str):
    """An opener whose connection raises ``OperationalError(message)`` on every query, as the reopen would."""

    def raise_error(self, *args, **kwargs):
        raise sqlite3.OperationalError(message)

    class FailingCursor(server._ObservedCursor):
        execute = server._observe(raise_error)

    class FailingConnection(server._ObservedConnection):
        def cursor(self, factory=FailingCursor):
            return super().cursor(factory)

    def opener(_module):
        conn = sqlite3.connect(str(path), factory=FailingConnection, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    return opener


def _observed_connection_at(server, path: Path):
    conn = sqlite3.connect(
        f"{path.as_uri()}?mode=ro", uri=True, factory=server._ObservedConnection, check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def _dispatch(server, name: str, arguments: dict):
    return asyncio.run(server._dispatch_tool_call(name, dict(arguments)))


@pytest.mark.parametrize(
    ("tool", "arguments"),
    [
        # ``_dict_lookup_contains`` swallows OperationalError and returns [].
        ("search_style_guide", {"query": "участь"}),
        # ``_dict_lookup`` (exact and prefix path) swallows it the same way.
        ("search_grinchenko_1907", {"query": "Вода"}),
    ],
)
def test_retry_that_swallows_a_disk_error_is_a_typed_error_not_an_empty_result(
    server, sdb, db, tmp_path, monkeypatch, tool, arguments
):
    _add_dictionary_tables(db)
    healthy, is_error, _ = _dispatch(server, tool, arguments)  # opens and caches the process-wide connection
    assert is_error is False and "No results" not in healthy[0].text
    _truncate_in_place(db)  # first attempt: malformed, propagates out of the helper
    monkeypatch.setattr(server, "_open_observed_sources_conn", _failing_connection_opener(server, db, "disk I/O error"))

    content, is_error, typed = _dispatch(server, tool, arguments)

    assert is_error is True
    payload = json.loads(content[0].text)
    assert payload == typed
    assert payload["status"] == "error" and payload["error_code"] == "database_unavailable"
    assert payload["database"] == "sources.db" and payload["error_class"] == "OperationalError"
    assert "No results" not in content[0].text
    heal = _log_entries(tmp_path)[-1]["self_heal"]
    assert heal["recovered"] is False and heal["error_class"] == "DatabaseError"


def test_swallowed_damage_on_a_first_attempt_over_the_healed_connection_is_healed(server, sdb, db, tmp_path):
    _add_dictionary_tables(db)
    _dispatch(server, "search_style_guide", {"query": "участь"})
    # A heal already happened, so the cached connection is an observed one; it fails once and the helper swallows it.
    failing = _failing_connection_opener(server, db, "disk I/O error")(sdb)
    sdb._conn = failing

    content, is_error, _ = _dispatch(server, "search_style_guide", {"query": "участь"})

    assert is_error is False and "Приймати участь" in content[0].text
    assert sdb._conn is not failing
    assert _log_entries(tmp_path)[-1]["self_heal"] == {
        "database": "sources.db",
        "error_class": "OperationalError",
        "reopened": True,
        "recovered": True,
    }


def test_swallowed_absent_table_is_not_a_database_failure(server, sdb, db, tmp_path):
    _dispatch(server, "collection_stats", {})  # no style_guide table in this database
    sdb._conn = server._open_observed_sources_conn(sdb)

    content, is_error, typed = _dispatch(server, "search_style_guide", {"query": "участь"})

    assert is_error is False and typed["status"] == "empty"
    assert "No results" in content[0].text
    assert "self_heal" not in _log_entries(tmp_path)[-1]


def test_swallowed_absent_table_on_a_first_attempt_does_not_start_a_heal(server, sdb, db, tmp_path, monkeypatch):
    _dispatch(server, "collection_stats", {})  # no style_guide table in this database
    sdb._conn = server._open_observed_sources_conn(sdb)  # as after any earlier heal: swallowed errors are reported
    reopened: list[object] = []
    monkeypatch.setattr(server, "_open_observed_sources_conn", lambda module: reopened.append(module))

    content, is_error, typed = _dispatch(server, "search_style_guide", {"query": "участь"})

    assert is_error is False and typed["status"] == "empty"
    assert "No results" in content[0].text
    assert reopened == []
    assert "self_heal" not in _log_entries(tmp_path)[-1]


def test_retry_over_a_rebuilt_database_missing_a_table_is_a_typed_error_not_an_empty_result(
    server, sdb, db, tmp_path, monkeypatch
):
    _add_dictionary_tables(db)
    healthy, is_error, _ = _dispatch(server, "search_style_guide", {"query": "участь"})
    assert is_error is False and "Приймати участь" in healthy[0].text
    _truncate_in_place(db)  # first attempt: malformed
    rebuilt = db.with_name("rebuilt.db")  # a valid database from a schema change: no style_guide table
    conn = sqlite3.connect(rebuilt)
    conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY, body TEXT)")
    conn.commit()
    conn.close()
    monkeypatch.setattr(
        server,
        "_open_observed_sources_conn",
        lambda module: _observed_connection_at(server, rebuilt),
    )

    content, is_error, typed = _dispatch(server, "search_style_guide", {"query": "участь"})

    assert is_error is True
    payload = json.loads(content[0].text)
    assert payload == typed
    assert payload["status"] == "error" and payload["error_code"] == "database_unavailable"
    assert payload["database"] == "sources.db" and payload["error_class"] == "OperationalError"
    assert "No results" not in content[0].text
    heal = _log_entries(tmp_path)[-1]["self_heal"]
    assert heal["recovered"] is False and heal["error_class"] == "DatabaseError"


def test_failed_reopen_keeps_the_held_connection_instead_of_clearing_it(server, sdb, db, monkeypatch):
    _stats(server)
    held = sdb._conn

    def cannot_reopen(_module):
        raise FileNotFoundError("sources database is being rebuilt")

    monkeypatch.setattr(server, "_open_observed_sources_conn", cannot_reopen)

    assert server._discard_cached_connections("sources.db") is False
    assert sdb._conn is held


def test_reader_paused_before_returning_the_connection_never_gets_none_when_a_heal_runs(server, sdb, db):
    _stats(server)
    held = sdb._conn
    source, first_line = inspect.getsourcelines(sdb._get_conn)
    return_line = first_line + next(i for i, text in enumerate(source) if text.strip() == "return _conn")
    code = sdb._get_conn.__code__
    paused, resume = threading.Event(), threading.Event()
    outcome: dict[str, object] = {}

    def trace_calls(frame, event, arg):
        if frame.f_code is not code:
            return None

        def trace_lines(frame, event, arg):
            if event == "line" and frame.f_lineno == return_line:
                paused.set()
                assert resume.wait(timeout=30)
            return trace_lines

        return trace_lines

    def reader():
        sys.settrace(trace_calls)
        try:
            outcome["conn"] = sdb._get_conn()
        finally:
            sys.settrace(None)

    thread = threading.Thread(target=reader)
    thread.start()
    assert paused.wait(timeout=30)  # the reader has seen a cached connection and is about to return it
    assert server._discard_cached_connections("sources.db") is True  # the heal runs now
    resume.set()
    thread.join(timeout=30)

    returned = outcome["conn"]
    assert returned is not None
    assert returned.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0] == ROW_COUNT  # open and usable
    assert returned is sdb._conn and returned is not held


def test_simultaneous_heals_of_one_stale_connection_reopen_once(server, sdb, db, tmp_path, monkeypatch):
    _stats(server)
    original = _truncate_in_place(db)
    opens: list[int] = []
    real_open = server._open_observed_sources_conn

    def counting_open(module):
        opens.append(1)
        return real_open(module)

    monkeypatch.setattr(server, "_open_observed_sources_conn", counting_open)

    async def scenario():
        failed = 0
        both_failed = asyncio.Event()
        attempts = {"a": 0, "b": 0}

        def handler_for(name):
            async def handler():
                attempts[name] += 1
                if attempts[name] > 1:
                    return await server.handle_collection_stats({})
                try:
                    return await server.handle_collection_stats({})
                except sqlite3.DatabaseError:
                    nonlocal failed
                    failed += 1
                    if failed == 2:  # both callers hold the stale connection's failure before either heals
                        _restore_in_place(db, original)
                        both_failed.set()
                    await both_failed.wait()
                    raise

            return handler

        heals = {"a": {}, "b": {}}
        results = await asyncio.gather(
            server._call_with_database_self_heal(handler_for("a"), heals["a"]),
            server._call_with_database_self_heal(handler_for("b"), heals["b"]),
        )
        return results, heals, attempts

    results, heals, attempts = asyncio.run(scenario())

    assert attempts == {"a": 2, "b": 2}
    assert [json.loads(r[0].text) for r in results] == [{"textbooks": ROW_COUNT}] * 2
    assert len(opens) == 1
    assert all(h["reopened"] is True and h["recovered"] is True for h in heals.values())


@pytest.fixture()
def fake_wiki_cache(monkeypatch):
    wiki_cache = importlib.import_module("rag.wiki_cache")

    class FakeCache:
        instances: ClassVar[list[FakeCache]] = []
        fail = False

        def __init__(self) -> None:
            self.closed = False
            FakeCache.instances.append(self)

        def get(self, *_args):
            if FakeCache.fail:
                raise RuntimeError("cache read failed")
            return "cached text"

        def is_negative(self, _value) -> bool:
            return False

        def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(wiki_cache, "WikiCache", FakeCache)
    return FakeCache


def test_wikipedia_cache_is_closed_after_a_call(server, fake_wiki_cache):
    result = asyncio.run(server._query_wikipedia({"query": "Київ", "mode": "search"}))

    assert result[0].text == "cached text"
    assert [cache.closed for cache in fake_wiki_cache.instances] == [True]


def test_wikipedia_cache_is_closed_when_the_call_raises(server, fake_wiki_cache):
    fake_wiki_cache.fail = True
    with pytest.raises(RuntimeError, match="cache read failed"):
        asyncio.run(server._query_wikipedia({"query": "Київ", "mode": "search"}))

    assert [cache.closed for cache in fake_wiki_cache.instances] == [True]
