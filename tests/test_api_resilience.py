"""Tests for process-wide playground API resilience controls."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest

from scripts.api.resilience import (
    connect_sqlite,
    get_resilience_snapshot,
    reset_resilience_stats_for_tests,
)
from scripts.lib.readonly_sqlite import CorpusDatabaseWriteRefused

ROOT = Path(__file__).resolve().parents[1]


def test_slow_sql_caller_never_exposes_absolute_filesystem_root(monkeypatch, tmp_path):
    """``recent_slow_sql[*].caller`` is published on /api/health, so it must
    be repo-relative (or a bare basename) — never an absolute host path."""
    reset_resilience_stats_for_tests()
    monkeypatch.setenv("API_SLOW_SQL_MS", "0")

    db_path = tmp_path / "timed.db"
    conn = connect_sqlite(str(db_path))
    conn.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
    conn.close()

    snapshot = get_resilience_snapshot()
    callers = [event["caller"] for event in snapshot["recent_slow_sql"]]
    assert callers
    for caller in callers:
        assert not caller.startswith("/"), caller
        assert "/home/" not in caller
        assert "/Users/" not in caller
    assert any(caller.startswith("tests/test_api_resilience.py:") for caller in callers)


def test_connect_sqlite_refuses_writable_corpus_databases(tmp_path):
    sources = tmp_path / "sources.db"
    vesum = tmp_path / "vesum.db"
    other = tmp_path / "notes.db"
    for path in (sources, vesum):
        with pytest.raises(CorpusDatabaseWriteRefused, match=path.name):
            connect_sqlite(str(path))
        uri = path.resolve().as_uri() + "?mode=ro"
        with pytest.raises(sqlite3.OperationalError):
            connect_sqlite(uri, uri=True)
    conn = connect_sqlite(str(other))
    conn.execute("CREATE TABLE sample (id INTEGER)")
    conn.close()


def test_declared_writer_may_open_sources_db_through_connect_sqlite(tmp_path, monkeypatch):
    from scripts.lib import readonly_sqlite

    monkeypatch.setattr(
        readonly_sqlite,
        "_declared_writer_paths",
        lambda: frozenset({readonly_sqlite._script_path(__file__)}),
    )
    database = tmp_path / "sources.db"
    connection = connect_sqlite(str(database))
    connection.execute("CREATE TABLE sample (id INTEGER)")
    connection.close()
    assert database.is_file()


def test_services_sh_loopback_bind_and_match_contract():
    """services.sh api/sources must bind loopback and keep SVC_MATCH aligned with argv."""
    content = (ROOT / "services.sh").read_text(encoding="utf-8")

    def _field(name: str) -> str:
        escaped = re.escape(name)
        match = re.search(rf'{escaped}="([^"]+)"', content)
        assert match is not None, f"missing {name} in services.sh"
        return match.group(1)

    api_cmd = _field("SVC_CMD[api]")
    api_match = _field("SVC_MATCH[api]")
    sources_cmd = _field("SVC_CMD[sources]")
    sources_match = _field("SVC_MATCH[sources]")

    assert "SVC_HOST[api]=127.0.0.1" in content
    assert "SVC_HOST[sources]=127.0.0.1" in content
    assert "--host 127.0.0.1" in api_cmd
    assert "--host 127.0.0.1 --port 8766" in sources_cmd
    assert "0.0.0.0" not in api_cmd
    assert "0.0.0.0" not in sources_cmd
    assert api_match in api_cmd
    assert sources_match in sources_cmd
