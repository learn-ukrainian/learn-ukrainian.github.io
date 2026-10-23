"""#7484 byte-plane integrity: GC ordering, orphan sweep, size cap, contracts."""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

import pytest

from scripts.fleet_comms.artifacts import (
    MAX_ARTIFACT_BYTES,
    ArtifactStore,
    ArtifactStoreError,
)

pytestmark = pytest.mark.repo_invariant

_PG_DSN_ENV = "LEARN_UKRAINIAN_CP_PG_DSN"


@pytest.fixture
def store(tmp_path: Path) -> ArtifactStore:
    with ArtifactStore(root=tmp_path / "plane") as st:
        yield st


def _payload() -> bytes:
    return f"payload-{uuid.uuid4()}".encode()


def test_size_cap_rejects_before_storing(store: ArtifactStore) -> None:
    oversized = b"x" * (MAX_ARTIFACT_BYTES + 1)
    with pytest.raises(ArtifactStoreError, match="byte-plane limit"):
        store.store_bytes(oversized, producer="t")
    # Nothing landed on disk or in the DB.
    assert store._conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 0


def test_gc_commits_rows_before_unlinking(
    store: ArtifactStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#7484 (1.6): a crash during unlink must never leave rows pointing at
    deleted bytes — rows are already committed gone; files become orphans."""
    rec = store.store_bytes(_payload(), producer="t")
    old = time.time() - 7200
    os.utime(rec.blob_path, (old, old))
    store._conn.execute(
        "UPDATE artifacts SET created_at = '2000-01-01T00:00:00Z' WHERE artifact_id = ?",
        (rec.artifact_id,),
    )
    store._conn.commit()

    def crash_unlink(self, missing_ok=False):
        raise OSError("induced crash during unlink")

    monkeypatch.setattr(Path, "unlink", crash_unlink)
    with pytest.raises(OSError, match="induced crash"):
        store.garbage_collect_unreferenced(grace_seconds=60)
    monkeypatch.undo()
    # Rows are gone (committed before the unlink attempt)...
    assert store._conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 0
    # ...the surviving file is an orphan the sweep reclaims.
    assert rec.blob_path.is_file()
    assert store.reclaim_orphan_blobs(grace_seconds=60) == [rec.sha256]
    assert not rec.blob_path.is_file()


def test_orphan_sweep_respects_grace(store: ArtifactStore) -> None:
    rec = store.store_bytes(_payload(), producer="t")
    store._conn.execute("DELETE FROM artifacts")
    store._conn.commit()
    # Fresh file (mtime now) — protected by grace.
    assert store.reclaim_orphan_blobs(grace_seconds=3600) == []
    old = time.time() - 7200
    os.utime(rec.blob_path, (old, old))
    assert store.reclaim_orphan_blobs(grace_seconds=3600) == [rec.sha256]


def test_orphan_sweep_never_touches_referenced_blobs(store: ArtifactStore) -> None:
    rec = store.store_bytes(_payload(), producer="t")
    old = time.time() - 7200
    os.utime(rec.blob_path, (old, old))
    assert store.reclaim_orphan_blobs(grace_seconds=60) == []
    assert rec.blob_path.is_file()


def test_sqlite_records_keep_blob_path_contract(store: ArtifactStore) -> None:
    rec = store.store_bytes(_payload(), producer="t")
    assert rec.blob_path is not None and rec.blob_path.is_file()
    assert rec.to_dict()["blob_path"] == str(rec.blob_path)


@pytest.mark.postgres
def test_pg_records_carry_no_fabricated_blob_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    if not (os.environ.get(_PG_DSN_ENV) or "").strip():
        pytest.skip(f"{_PG_DSN_ENV} unset/empty — Postgres tests skipped")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    with ArtifactStore(root=tmp_path) as store:
        rec = store.store_bytes(_payload(), producer="t")
        assert rec.blob_path is None
        assert rec.to_dict()["blob_path"] is None
        # Round trip still works through the dedicated payload fetch.
        assert store.read_bytes(rec.artifact_id)
        # Metadata lookups return no payload column.
        row = store._pg_row_by_artifact_id(rec.artifact_id)
        assert "payload" not in dict(row)


def test_unlink_skips_when_a_writer_reinserted_the_digest(
    store: ArtifactStore, tmp_path: Path
) -> None:
    """#7484 CF r1: a row committed by a concurrent writer between GC's row
    commit and the unlink phase must keep its blob."""
    rec = store.store_bytes(_payload(), producer="t")
    # Simulate the concurrent writer: the row exists when the unlink phase
    # re-checks under its write lock.
    assert store._unlink_if_unreferenced(rec.sha256) is False
    assert rec.blob_path.is_file()
    assert store.read_bytes(rec.artifact_id)


def test_writer_dedup_self_heals_a_missing_blob(store: ArtifactStore) -> None:
    """#7484 CF r1 companion: a writer that lost the unlink race rewrites the
    blob on its next same-content store (dest.exists() is re-checked)."""
    data = _payload()
    rec = store.store_bytes(data, producer="t")
    rec.blob_path.unlink()
    again = store.store_bytes(data, producer="t")
    assert again.artifact_id == rec.artifact_id
    assert rec.blob_path.is_file()
    assert store.read_bytes(rec.artifact_id) == data
