"""Repository source stores stay read-only; runtime and fixture DBs may write."""

from __future__ import annotations

import sqlite3

import pytest

from tests.helpers import source_db_write_guard as guard


@pytest.mark.parametrize("name", ["sources.db", "vesum.db", "vesum_shadow_v680.db"])
@pytest.mark.parametrize("opener", [sqlite3.connect, sqlite3.dbapi2.connect, sqlite3.Connection])
@pytest.mark.parametrize("form", ["path", "str", "bytes", "uri", "rw", "rwc", "memory", "duplicate"])
def test_writable_repository_db_refused_before_open(tmp_path, monkeypatch, name, opener, form):
    data = tmp_path / "checkout" / "data"
    data.mkdir(parents=True)
    path = data / name
    # A real pre-existing database, created before making it a protected root.
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE witness(value)")
    before = path.read_bytes()
    monkeypatch.setattr(guard, "DATA_ROOTS", frozenset({data.resolve()}))
    values = {
        "path": path,
        "str": str(path),
        "bytes": bytes(path),
        "uri": path.as_uri(),
        "rw": path.as_uri() + "?mode=rw",
        "rwc": path.as_uri() + "?mode=rwc",
        "memory": path.as_uri() + "?mode=memory",
        "duplicate": path.as_uri() + "?mode=ro&mode=rw",
    }
    with pytest.raises(pytest.fail.Exception, match="Writable SQLite open"):
        opener(values[form], uri=form not in {"path", "str", "bytes"})
    assert path.read_bytes() == before


def test_real_repository_source_targets_are_protected():
    # Invoke the same pre-open audit hook directly: never open a real DB even
    # if a future regression weakens the hook.
    for root in guard.DATA_ROOTS:
        for name in ("sources.db", "vesum.db", "vesum_shadow_v680.db"):
            with pytest.raises(pytest.fail.Exception, match="Writable SQLite open"):
                guard.refuse_writable_source_db("sqlite3.connect", (root / name,))


@pytest.mark.parametrize("name", ["other.db", "fleet_comms.db", "telemetry/legacy_comms_routes.db"])
@pytest.mark.parametrize("opener", [sqlite3.connect, sqlite3.dbapi2.connect, sqlite3.Connection])
@pytest.mark.parametrize("form", ["path", "str", "bytes", "uri", "rw", "rwc"])
def test_runtime_db_under_data_writable_while_sources_refused(tmp_path, monkeypatch, name, opener, form):
    data = tmp_path / "checkout" / "data"
    path = data / name
    path.parent.mkdir(parents=True)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE witness(value)")
    monkeypatch.setattr(guard, "DATA_ROOTS", frozenset({data.resolve()}))
    values = {
        "path": path,
        "str": str(path),
        "bytes": bytes(path),
        "uri": path.as_uri(),
        "rw": path.as_uri() + "?mode=rw",
        "rwc": path.as_uri() + "?mode=rwc",
    }
    with opener(values[form], uri=form not in {"path", "str", "bytes"}) as conn:
        conn.execute("INSERT INTO witness VALUES (1)")
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT value FROM witness").fetchall() == [(1,)]
    with pytest.raises(pytest.fail.Exception, match="Writable SQLite open"):
        opener(data / "sources.db")
    assert not (data / "sources.db").exists()


def test_readonly_and_external_fixtures_are_allowed(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    path = data / "sources.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE witness(value)")
    monkeypatch.setattr(guard, "DATA_ROOTS", frozenset({data.resolve()}))
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as conn:
        assert conn.execute("SELECT count(*) FROM witness").fetchone() == (0,)
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("INSERT INTO witness VALUES (1)")
    with sqlite3.connect(tmp_path / "fixture.db") as conn:
        conn.execute("CREATE TABLE writable(value)")
    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE writable(value)")


@pytest.mark.parametrize("name", ["sources.db", "vesum.db", "vesum_shadow_v680.db"])
def test_symlink_to_repository_db_is_refused(tmp_path, monkeypatch, name):
    data = tmp_path / "data"
    data.mkdir()
    path = data / name
    path.touch()
    alias = tmp_path / "alias.db"
    alias.symlink_to(path)
    monkeypatch.setattr(guard, "DATA_ROOTS", frozenset({data.resolve()}))
    with pytest.raises(pytest.fail.Exception, match="Writable SQLite open"):
        sqlite3.connect(alias)


@pytest.mark.parametrize(
    "event,args", [("open", ("data/sources.db",)), ("sqlite3.connect", ()), ("sqlite3.connect", (None,))]
)
def test_unrelated_audit_events_pass(event, args):
    guard.refuse_writable_source_db(event, args)
