"""#7483 (1.14): numbered/checksummed pg schema ledger + drift verification."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

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
    with pytest.raises(PgSchemaError, match="unexpected checksum"):
        verify_pg_schema(pg_conn)


def test_verify_pg_schema_detects_incomplete_ledger(pg_conn, tmp_path: Path) -> None:
    # Fresh schema namespace: drop only the ledger receipts so tables may remain
    # but verify must still refuse an incomplete receipt set.
    apply_pg_schema(pg_conn)
    pg_conn.execute(f"DELETE FROM {PG_MIGRATION_TABLE} WHERE version = 2")
    with pytest.raises(PgSchemaError, match="incomplete"):
        verify_pg_schema(pg_conn)
