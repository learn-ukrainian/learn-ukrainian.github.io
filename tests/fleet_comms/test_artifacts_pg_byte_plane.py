"""Phase 0b artifact byte-plane tests (private #603).

``fleet_comms`` authority ``pg``: payload bytes must live in Postgres, in the
same durability domain as the metadata row — never in a host-local
``blobs/sha256/...`` file. A second process with the DSN and no local blob
tree must still ``read_bytes`` successfully. Skips (does not fail) when
``LEARN_UKRAINIAN_CP_PG_DSN`` is unset, matching the existing dual-engine
contract tests in ``tests/control_plane``.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

import pytest

from scripts.fleet_comms.artifacts import ArtifactStore, ArtifactStoreError

pytestmark = pytest.mark.repo_invariant

_PG_DSN_ENV = "LEARN_UKRAINIAN_CP_PG_DSN"


def _pg_dsn_or_skip() -> str:
    dsn = (os.environ.get(_PG_DSN_ENV) or "").strip()
    if not dsn:
        pytest.skip(f"{_PG_DSN_ENV} unset/empty — Postgres byte-plane test skipped")
    return dsn


def _unique_payload(tag: str) -> bytes:
    # Random per-test-run content avoids sha256 collisions with rows other
    # shards/tests may have left in the shared CI Postgres instance.
    return f"phase0b-byte-plane:{tag}:{uuid.uuid4().hex}".encode()


@pytest.fixture
def pg_authority(monkeypatch: pytest.MonkeyPatch) -> str:
    dsn = _pg_dsn_or_skip()
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    return dsn


@pytest.mark.postgres
def test_store_bytes_then_read_bytes_round_trips_no_local_blob_file(
    pg_authority: str,
    tmp_path: Path,
) -> None:
    root = tmp_path / "plane"
    data = _unique_payload("round-trip")
    with ArtifactStore(root=root) as store:
        rec = store.store_bytes(data, producer="phase0b-test")
        assert rec.sha256 == hashlib.sha256(data).hexdigest()
        # No host-local blob tree was ever created for the pg byte-plane.
        assert not (root / "blobs").exists()
        assert not (root / "comms.sqlite3").exists()

        assert store.read_bytes(rec.artifact_id) == data
        fetched = store.get(rec.artifact_id)
        assert fetched.sha256 == rec.sha256
        assert fetched.producer == "phase0b-test"
        by_digest = store.get_by_sha256(rec.sha256)
        assert by_digest is not None
        assert by_digest.artifact_id == rec.artifact_id


@pytest.mark.postgres
def test_read_bytes_succeeds_from_second_process_with_no_local_blob_dir(
    pg_authority: str,
    tmp_path: Path,
) -> None:
    """A second store instance, pointed at a different (never-created) root,
    must still read the bytes back — proving the payload lives in Postgres,
    not on the writer's local disk."""
    data = _unique_payload("second-process")
    with ArtifactStore(root=tmp_path / "writer-plane") as writer:
        rec = writer.store_bytes(data, producer="phase0b-test")

    reader_root = tmp_path / "reader-plane-never-shares-disk-with-writer"
    assert not reader_root.exists()
    with ArtifactStore(root=reader_root) as reader:
        assert reader.read_bytes(rec.artifact_id) == data
        assert not (reader_root / "blobs" / "sha256").exists()


@pytest.mark.postgres
def test_store_bytes_dedups_by_sha256(pg_authority: str, tmp_path: Path) -> None:
    data = _unique_payload("dedup")
    with ArtifactStore(root=tmp_path / "plane") as store:
        first = store.store_bytes(data, producer="phase0b-test")
        second = store.store_bytes(data, producer="phase0b-test-other")
        assert second.artifact_id == first.artifact_id
        assert second.producer == first.producer


@pytest.mark.postgres
def test_materialize_writes_scratch_file_from_postgres_bytes(
    pg_authority: str,
    tmp_path: Path,
) -> None:
    data = _unique_payload("materialize")
    with ArtifactStore(root=tmp_path / "plane") as store:
        rec = store.store_bytes(data, producer="phase0b-test", logical_filename="payload.bin")
        scratch = tmp_path / "scratch"
        out = store.materialize(rec.artifact_id, scratch, filename="payload.bin")
        assert out.read_bytes() == data


@pytest.mark.postgres
def test_get_missing_artifact_raises(pg_authority: str, tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path / "plane") as store:
        with pytest.raises(ArtifactStoreError, match="not found"):
            store.get("no-such-artifact")


@pytest.mark.postgres
def test_deferred_commit_without_active_transaction_raises(
    pg_authority: str,
    tmp_path: Path,
) -> None:
    with ArtifactStore(root=tmp_path / "plane") as store:
        with pytest.raises(ArtifactStoreError, match="caller-owned active transaction"):
            store.store_bytes(_unique_payload("deferred"), producer="t", commit=False)
