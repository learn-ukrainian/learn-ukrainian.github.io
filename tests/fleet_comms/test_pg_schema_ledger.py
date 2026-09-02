"""#7483 (1.14): numbered/checksummed pg schema ledger + drift verification."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.fleet_comms.artifacts import ArtifactStore, ArtifactStoreError
from scripts.fleet_comms.pg_schema import (
    MIGRATIONS,
    PG_BLOB_TABLE,
    PG_MIGRATION_TABLE,
    PgSchemaError,
    apply_pg_schema,
    verify_pg_schema,
)

pytestmark = [pytest.mark.repo_invariant, pytest.mark.postgres]

_PG_DSN_ENV = "LEARN_UKRAINIAN_CP_PG_DSN"


@pytest.fixture
def pg_conn(monkeypatch: pytest.MonkeyPatch):
    if not (os.environ.get(_PG_DSN_ENV) or "").strip():
        pytest.skip(f"{_PG_DSN_ENV} unset/empty — Postgres tests skipped")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    from scripts.control_plane.storage import StoreId
    from scripts.control_plane.storage import connect as cp_connect

    conn = cp_connect(StoreId.FLEET_COMMS)
    conn.autocommit = True
    yield conn
    conn.close()


def test_apply_pg_schema_records_checksummed_receipts(pg_conn) -> None:
    highest = apply_pg_schema(pg_conn)
    assert highest == MIGRATIONS[-1].version
    rows = {
        int(row[0]): (str(row[1]), str(row[2]))
        for row in pg_conn.execute(
            f"SELECT version, name, checksum FROM {PG_MIGRATION_TABLE}"
        )
    }
    for migration in MIGRATIONS:
        assert rows[migration.version] == (migration.name, migration.checksum)
    # Blob table is owned by v1 of the ledger, not inline ArtifactStore DDL.
    assert pg_conn.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = %s",
        (PG_BLOB_TABLE,),
    ).fetchone()
    assert verify_pg_schema(pg_conn) == highest
    # Idempotent re-apply leaves receipts intact.
    assert apply_pg_schema(pg_conn) == highest


def test_verify_pg_schema_detects_checksum_drift(pg_conn) -> None:
    apply_pg_schema(pg_conn)
    pg_conn.execute(
        f"UPDATE {PG_MIGRATION_TABLE} SET checksum = %s WHERE version = 1",
        ("0" * 64,),
    )
    try:
        with pytest.raises(PgSchemaError, match="unexpected checksum"):
            verify_pg_schema(pg_conn)
    finally:
        pg_conn.execute(
            f"UPDATE {PG_MIGRATION_TABLE} SET checksum = %s WHERE version = 1",
            (MIGRATIONS[0].checksum,),
        )


def test_verify_pg_schema_detects_incomplete_ledger(pg_conn) -> None:
    # Fresh schema namespace: drop only the ledger receipts so tables may remain
    # but verify must still refuse an incomplete receipt set.
    apply_pg_schema(pg_conn)
    pg_conn.execute(f"DELETE FROM {PG_MIGRATION_TABLE} WHERE version = 2")
    with pytest.raises(PgSchemaError, match="incomplete"):
        verify_pg_schema(pg_conn)
    # Restore so later tests (and this file's readonly open) see a complete ledger.
    apply_pg_schema(pg_conn)


def test_open_readonly_pg_verifies_without_applying_and_refuses_drift(
    pg_conn, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Readonly pg open is the drift gate; it must never apply/mutate DDL."""
    apply_pg_schema(pg_conn)
    import scripts.fleet_comms.artifacts as artifacts_mod

    apply_calls: list[object] = []
    verify_calls: list[object] = []
    real_apply = artifacts_mod.apply_pg_schema
    real_verify = artifacts_mod.verify_pg_schema

    def tracked_apply(conn):
        apply_calls.append(conn)
        return real_apply(conn)

    def tracked_verify(conn):
        verify_calls.append(conn)
        return real_verify(conn)

    monkeypatch.setattr(artifacts_mod, "apply_pg_schema", tracked_apply)
    monkeypatch.setattr(artifacts_mod, "verify_pg_schema", tracked_verify)

    with ArtifactStore.open_readonly(root=tmp_path):
        pass
    assert apply_calls == []
    assert verify_calls

    pg_conn.execute(
        f"UPDATE {PG_MIGRATION_TABLE} SET checksum = %s WHERE version = 1",
        ("0" * 64,),
    )
    try:
        with pytest.raises(ArtifactStoreError, match="pg schema missing or drifted"):
            ArtifactStore.open_readonly(root=tmp_path)
        assert apply_calls == []
        assert len(verify_calls) >= 2
    finally:
        pg_conn.execute(
            f"UPDATE {PG_MIGRATION_TABLE} SET checksum = %s WHERE version = 1",
            (MIGRATIONS[0].checksum,),
        )


def test_open_readonly_pg_maps_missing_schema_not_undefined_table(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A missing migration table must become ArtifactStoreError, not UndefinedTable."""
    if not (os.environ.get(_PG_DSN_ENV) or "").strip():
        pytest.skip(f"{_PG_DSN_ENV} unset/empty — Postgres tests skipped")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")

    import psycopg.errors

    import scripts.fleet_comms.artifacts as artifacts_mod
    import scripts.fleet_comms.pg_schema as pg_schema_mod

    def forbid_apply(_conn):
        raise AssertionError("readonly pg open must not apply_pg_schema")

    def missing_receipts(_conn):
        raise psycopg.errors.UndefinedTable(
            "relation fleet_comms_pg_schema_migrations does not exist"
        )

    monkeypatch.setattr(artifacts_mod, "apply_pg_schema", forbid_apply)
    monkeypatch.setattr(pg_schema_mod, "_applied_migrations", missing_receipts)

    with pytest.raises(ArtifactStoreError, match="pg schema missing or drifted") as excinfo:
        ArtifactStore.open_readonly(root=tmp_path)
    assert not isinstance(excinfo.value, psycopg.errors.UndefinedTable)
