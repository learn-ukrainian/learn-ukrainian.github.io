"""#7483 pg transaction discipline (autocommit reads, savepoints, determinism).

pg-marked tests run in CI's postgres service job; they skip without a DSN.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

from scripts.fleet_comms.artifacts import ArtifactStore, ArtifactStoreError

_PG_DSN_ENV = "LEARN_UKRAINIAN_CP_PG_DSN"

pytestmark = [pytest.mark.repo_invariant, pytest.mark.postgres]


@pytest.fixture
def pg_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ArtifactStore:
    if not (os.environ.get(_PG_DSN_ENV) or "").strip():
        pytest.skip(f"{_PG_DSN_ENV} unset/empty — Postgres tests skipped")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    store = ArtifactStore(root=tmp_path)
    yield store
    store.close()


def _payload() -> bytes:
    return f"payload-{uuid.uuid4()}".encode()


def test_reads_do_not_hold_a_transaction_open(pg_store: ArtifactStore) -> None:
    """#7483 (1.1): a bare read must leave the connection IDLE, not INTRANS."""
    import psycopg

    rec = pg_store.store_bytes(_payload(), producer="t")
    pg_store.get(rec.artifact_id)
    pg_store.get_by_sha256(rec.sha256)
    pg_store.read_bytes(rec.artifact_id)
    assert (
        pg_store.connection.info.transaction_status
        == psycopg.pq.TransactionStatus.IDLE
    )


def test_prior_read_does_not_defeat_deferred_commit_guard(
    pg_store: ArtifactStore,
) -> None:
    """#7483 (1.2): after a read, commit=False without a caller tx must raise."""
    rec = pg_store.store_bytes(_payload(), producer="t")
    pg_store.get(rec.artifact_id)  # would previously flip INTRANS
    with pytest.raises(ArtifactStoreError, match="caller-owned active transaction"):
        pg_store.store_bytes(_payload(), producer="t", commit=False)


def test_helper_error_does_not_poison_caller_transaction(
    pg_store: ArtifactStore,
) -> None:
    """#7483 (1.3): a failing deferred write rolls back its SAVEPOINT only."""
    conn = pg_store.connection
    keep = _payload()
    with conn.transaction():
        kept = pg_store.store_bytes(keep, producer="t", commit=False)
        with pytest.raises(ArtifactStoreError):
            # Same explicit id, different content → deterministic error.
            pg_store.store_bytes(
                _payload(), producer="t", commit=False, artifact_id=kept.artifact_id
            )
        # The caller's transaction must still be usable after the error.
        assert pg_store.get(kept.artifact_id).sha256 == kept.sha256
    assert pg_store.get(kept.artifact_id).sha256 == kept.sha256


def test_explicit_artifact_id_conflicts_are_deterministic(
    pg_store: ArtifactStore,
) -> None:
    """#7483 (1.7): id/content mismatches raise ArtifactStoreError, never a
    raw UniqueViolation."""
    first = pg_store.store_bytes(_payload(), producer="t")
    # Same id, different content.
    with pytest.raises(ArtifactStoreError, match="already exists with different"):
        pg_store.store_bytes(_payload(), producer="t", artifact_id=first.artifact_id)
    # Same content, different explicit id.
    with pytest.raises(ArtifactStoreError, match="refusing duplicate id"):
        pg_store.store_bytes(
            pg_store.read_bytes(first.artifact_id),
            producer="t",
            artifact_id=f"artifact-{uuid.uuid4()}",
        )


def test_constructor_closes_connection_on_partial_init(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """#7483 (1.10): a failure after connect must not leak the connection."""
    if not (os.environ.get(_PG_DSN_ENV) or "").strip():
        pytest.skip(f"{_PG_DSN_ENV} unset/empty — Postgres tests skipped")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    closed: list[object] = []

    real_ensure = ArtifactStore._ensure_pg_blob_table

    def boom(self):
        closed.append(self._conn)
        raise RuntimeError("induced init failure")

    monkeypatch.setattr(ArtifactStore, "_ensure_pg_blob_table", boom)
    with pytest.raises(RuntimeError, match="induced init failure"):
        ArtifactStore(root=tmp_path)
    assert closed and closed[0].closed
    monkeypatch.setattr(ArtifactStore, "_ensure_pg_blob_table", real_ensure)
