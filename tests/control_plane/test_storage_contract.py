"""Phase 0b dual-engine control-plane storage contract (sqlite + Postgres)."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.control_plane.storage import (
    StoreId,
    connect,
)

_PG_DSN_ENV = "LEARN_UKRAINIAN_CP_PG_DSN"
_PROBE_TABLE = "cp_contract_probe"

pytestmark = pytest.mark.repo_invariant


def _pg_dsn_or_skip() -> str:
    dsn = (os.environ.get(_PG_DSN_ENV) or "").strip()
    if not dsn:
        pytest.skip(f"{_PG_DSN_ENV} unset/empty — Postgres contract skipped")
    return dsn


@pytest.fixture
def engine_connection(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[str, object, Path]]:
    """Yield (engine, connection, sqlite_path_that_must_stay_absent_for_pg)."""
    engine: str = request.param
    sqlite_target = tmp_path / "write-ownership.sqlite3"
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_AUTHORITY", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_CP_AUTHORITY_WRITE_OWNERSHIP", raising=False)

    if engine == "sqlite":
        monkeypatch.setenv("LEARN_UKRAINIAN_OWNERSHIP_LEDGER", str(sqlite_target))
        conn = connect(StoreId.WRITE_OWNERSHIP, path=sqlite_target)
        try:
            yield engine, conn, sqlite_target
        finally:
            conn.close()
        return

    if engine == "pg":
        _pg_dsn_or_skip()
        monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_WRITE_OWNERSHIP", "pg")
        # Point the sqlite override at a path that must remain absent.
        monkeypatch.setenv("LEARN_UKRAINIAN_OWNERSHIP_LEDGER", str(sqlite_target))
        conn = connect(StoreId.WRITE_OWNERSHIP)
        try:
            yield engine, conn, sqlite_target
        finally:
            conn.close()
        return

    raise AssertionError(f"unknown engine: {engine!r}")


@pytest.mark.parametrize(
    "engine_connection",
    [
        pytest.param("sqlite", id="sqlite"),
        pytest.param("pg", marks=pytest.mark.postgres, id="pg"),
    ],
    indirect=True,
)
def test_write_ownership_select_one(
    engine_connection: tuple[str, object, Path],
) -> None:
    engine, conn, sqlite_target = engine_connection
    row = conn.execute("SELECT 1").fetchone()
    assert row is not None
    assert int(row[0]) == 1
    if engine == "pg":
        assert not sqlite_target.exists()


@pytest.mark.parametrize(
    "engine_connection",
    [
        pytest.param("sqlite", id="sqlite"),
        pytest.param("pg", marks=pytest.mark.postgres, id="pg"),
    ],
    indirect=True,
)
def test_write_ownership_probe_round_trip(
    engine_connection: tuple[str, object, Path],
) -> None:
    engine, conn, sqlite_target = engine_connection
    try:
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {_PROBE_TABLE} ("
            "id INTEGER PRIMARY KEY, note TEXT NOT NULL)"
        )
        conn.execute(f"DELETE FROM {_PROBE_TABLE}")
        conn.execute(
            f"INSERT INTO {_PROBE_TABLE} (id, note) VALUES (1, 'contract-ok')"
        )
        if engine == "pg":
            conn.commit()
        row = conn.execute(
            f"SELECT note FROM {_PROBE_TABLE} WHERE id = 1"
        ).fetchone()
        assert row is not None
        assert row[0] == "contract-ok"
    finally:
        conn.execute(f"DROP TABLE IF EXISTS {_PROBE_TABLE}")
        if engine == "pg" or isinstance(conn, sqlite3.Connection):
            conn.commit()
    if engine == "pg":
        assert not sqlite_target.exists()


@pytest.mark.postgres
def test_pg_engine_does_not_create_sqlite_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pg_dsn_or_skip()
    sqlite_target = tmp_path / "must-not-appear.sqlite3"
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_WRITE_OWNERSHIP", "pg")
    monkeypatch.setenv("LEARN_UKRAINIAN_OWNERSHIP_LEDGER", str(sqlite_target))
    conn = connect(StoreId.WRITE_OWNERSHIP, path=sqlite_target)
    try:
        assert conn.execute("SELECT 1").fetchone() is not None
    finally:
        conn.close()
    assert not sqlite_target.exists()
