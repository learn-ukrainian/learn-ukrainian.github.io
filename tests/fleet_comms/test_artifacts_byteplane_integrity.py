"""#7484 byte-plane integrity: GC ordering, orphan sweep, size cap, contracts."""

from __future__ import annotations

import bz2
import gzip
import io
import json
import lzma
import os
import time
import uuid
import zipfile
import zlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.fleet_comms.artifacts import (
    MAX_ARTIFACT_BYTES,
    ArtifactExpiredError,
    ArtifactStore,
    ArtifactStoreError,
    CitationScan,
    CitationSources,
    _unreferenced_candidate_sql,
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


def _age(store: ArtifactStore, artifact_id: str, created_at: str = "2000-01-01T00:00:00Z") -> None:
    store._conn.execute(
        "UPDATE artifacts SET created_at = ? WHERE artifact_id = ?", (created_at, artifact_id)
    )
    store._conn.commit()


_LATER = datetime.now(UTC) + timedelta(days=1)
_NO_CITATIONS = CitationScan(frozenset(), ())


def test_unreferenced_expiry_crash_keeps_rows_and_marker(
    store: ArtifactStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#7484 (1.6), migrated to retention (#12574): a crash during the unlink
    must never leave a row without bytes or without its marker. The row, its
    digest and byte count are kept; a re-run finishes the removal."""
    data = _payload()
    rec = store.store_bytes(data, producer="t")
    _age(store, rec.artifact_id)

    def crash_unlink(self, missing_ok=False):
        raise OSError("induced crash during unlink")

    monkeypatch.setattr(Path, "unlink", crash_unlink)
    with pytest.raises(OSError, match="induced crash"):
        store.expire_unreferenced_blobs(
            citations=_NO_CITATIONS, apply=True, now=_LATER, backup_dir=tmp_path / "backup"
        )
    monkeypatch.undo()
    row = store._conn.execute(
        "SELECT sha256, bytes, retention_class FROM artifacts WHERE artifact_id = ?",
        (rec.artifact_id,),
    ).fetchone()
    assert (row["sha256"], row["bytes"], row["retention_class"]) == (
        rec.sha256,
        rec.bytes,
        "expired:default",
    )
    assert rec.blob_path.is_file()
    report = store.expire_unreferenced_blobs(
        citations=_NO_CITATIONS, apply=True, now=_LATER, backup_dir=tmp_path / "backup"
    )
    assert (report.removed, report.removed_bytes) == (1, rec.bytes)
    assert not rec.blob_path.is_file()
    assert store.get(rec.artifact_id).sha256 == rec.sha256
    assert (tmp_path / "backup" / rec.sha256[:2] / rec.sha256).read_bytes() == data
    with pytest.raises(ArtifactExpiredError):
        store.read_bytes(rec.artifact_id)


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


def test_referenced_blob_of_open_delivery_is_never_removed(tmp_path: Path) -> None:
    """#12530 (pre-approved). Defect class: retention removing bytes a live
    reader still needs (the body of a queued delivery). The acknowledged
    control loses only its blob, never its message row or digest."""
    from datetime import UTC, datetime, timedelta

    from scripts.fleet_comms.artifacts import ArtifactExpiredError
    from scripts.fleet_comms.authority import AuthorityService, AuthorityServiceError

    with ArtifactStore(root=tmp_path / "plane") as store:
        service = AuthorityService(store=store)
        done = service.publish_message(sender="codex", body="acknowledged body", recipients=("claude-cto",))
        lease = service.claim_next_delivery("claude-cto", "worker")
        assert lease is not None and lease.delivery.message_id == done.message_id
        service.acknowledge_delivery(
            lease.delivery.delivery_id, worker_id="worker", fence_token=lease.fence_token
        )
        pending = service.publish_message(sender="codex", body="open body", recipients=("claude-cto",))

        report = store.expire_message_blobs(apply=True, now=datetime.now(UTC) + timedelta(days=60))

        assert (report.candidates, report.removed) == (1, 1)
        assert store.get(pending.body_artifact_id).blob_path.is_file()
        assert service.read_message_body(pending.message_id) == "open body"
        done_record = store.get(done.body_artifact_id)
        assert not done_record.blob_path.is_file()
        assert service.get_message(done.message_id).content_sha256 == done.content_sha256
        with pytest.raises(ArtifactExpiredError):
            service.read_message_body(done.message_id)
        lease = service.claim_next_delivery("claude-cto", "worker")
        assert lease is not None and lease.delivery.message_id == pending.message_id
        with pytest.raises(AuthorityServiceError, match=r"^artifact_expired$"):
            service.acknowledge_delivery(
                lease.delivery.delivery_id, worker_id="worker", fence_token=lease.fence_token,
                acknowledgment_artifact_id=done.body_artifact_id,
            )
        assert service.get_delivery(lease.delivery.delivery_id) == lease.delivery


def test_acknowledgment_racing_retention_refuses_expired_marker(tmp_path: Path, monkeypatch) -> None:
    """#12573, CTO-approved: acknowledgment between retention phases must
    not revive an expired artifact or terminalize its delivery."""
    from datetime import UTC, datetime, timedelta

    from scripts.fleet_comms.authority import AuthorityService, AuthorityServiceError

    root = tmp_path / "plane"
    with ArtifactStore(root=root) as store, AuthorityService(root=root) as service:
        done = service.publish_message(sender="codex", body="old body", recipients=("claude-cto",))
        lease = service.claim_next_delivery("claude-cto", "worker")
        service.acknowledge_delivery(
            lease.delivery.delivery_id, worker_id="worker", fence_token=lease.fence_token
        )
        service.publish_message(sender="codex", body="new body", recipients=("claude-cto",))
        lease = service.claim_next_delivery("claude-cto", "worker")
        attempt_before = dict(service._conn.execute(
            "SELECT * FROM authority_delivery_attempts WHERE delivery_id = ?",
            (lease.delivery.delivery_id,),
        ).fetchone())
        connection = store._conn

        class BetweenPhases:
            begins = 0

            def __getattr__(self, name):
                return getattr(connection, name)

            def execute(self, sql, *args):
                if sql == "BEGIN IMMEDIATE":
                    self.begins += 1
                    if self.begins == 2:
                        # Phase 1 has committed; phase 2 has not taken its lock.
                        record = store.get(done.body_artifact_id)
                        assert record.retention_class == "expired:message-body"
                        assert record.blob_path.is_file()
                        with pytest.raises(AuthorityServiceError, match=r"^artifact_expired$"):
                            service.acknowledge_delivery(
                                lease.delivery.delivery_id, worker_id="worker",
                                fence_token=lease.fence_token,
                                acknowledgment_artifact_id=done.body_artifact_id,
                            )
                        assert service.get_delivery(lease.delivery.delivery_id) == lease.delivery
                        assert dict(service._conn.execute(
                            "SELECT * FROM authority_delivery_attempts WHERE delivery_id = ?",
                            (lease.delivery.delivery_id,),
                        ).fetchone()) == attempt_before
                        assert store.get(done.body_artifact_id).retention_class == "expired:message-body"
                return connection.execute(sql, *args)

        boundary = BetweenPhases()
        monkeypatch.setattr(store, "_conn", boundary)
        report = store.expire_message_blobs(apply=True, now=datetime.now(UTC) + timedelta(days=60))
        assert boundary.begins == 2
        assert report.removed == 1
        assert not store.get(done.body_artifact_id).blob_path.is_file()


def test_unreferenced_blob_in_window_referenced_or_pinned_is_never_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#12574 T1 (CTO-approved). Defect class: retention removes an
    unreferenced blob that is inside the window, newly referenced between the
    two expiry phases, or in a pinned or unknown class. The old, unreferenced,
    allow-listed control loses only its blob; its row, digest and size stay."""
    window_edge = (_LATER - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with ArtifactStore(root=tmp_path / "plane") as store:
        old = store.store_bytes(_payload(), producer="t")
        fresh = store.store_bytes(_payload(), producer="t")
        pinned = store.store_bytes(_payload(), producer="t", retention_class="retained-evidence")
        unknown = store.store_bytes(_payload(), producer="t", retention_class="mystery-class")
        for rec in (old, pinned, unknown):
            _age(store, rec.artifact_id)
        _age(store, fresh.artifact_id, window_edge)

        report = store.expire_unreferenced_blobs(
            citations=_NO_CITATIONS, apply=True, now=_LATER, backup_dir=tmp_path / "backup"
        )

        assert (report.candidates, report.removed, report.held_cited) == (1, 1, 0)
        with pytest.raises(ArtifactStoreError, match="at least 90"):
            store.expire_unreferenced_blobs(citations=_NO_CITATIONS, older_than_days=1)
        assert not old.blob_path.is_file()
        assert store.get(old.artifact_id).retention_class == "expired:default"
        assert (store.get(old.artifact_id).sha256, store.get(old.artifact_id).bytes) == (old.sha256, old.bytes)
        for kept in (fresh, pinned, unknown):
            assert kept.blob_path.is_file()
            assert not store.get(kept.artifact_id).retention_class.startswith("expired:")
        with pytest.raises(ArtifactExpiredError):
            store.read_bytes(old.artifact_id)

    with ArtifactStore(root=tmp_path / "plane2") as store:
        racer = store.store_bytes(_payload(), producer="t")
        _age(store, racer.artifact_id)
        connection = store._conn

        class BetweenPhases:
            begins = 0

            def __getattr__(self, name):
                return getattr(connection, name)

            def execute(self, sql, *args):
                if sql == "BEGIN IMMEDIATE":
                    self.begins += 1
                    if self.begins == 2:
                        # Phase 1 has marked and committed; phase 2 has not locked.
                        assert store.get(racer.artifact_id).retention_class == "expired:default"
                        store.reference("message_racer", racer.artifact_id)
                return connection.execute(sql, *args)

        boundary = BetweenPhases()
        monkeypatch.setattr(store, "_conn", boundary)
        report = store.expire_unreferenced_blobs(
            citations=_NO_CITATIONS, apply=True, now=_LATER, backup_dir=tmp_path / "backup2"
        )
        assert boundary.begins == 2
        assert (report.removed, report.skipped_changed) == (0, 1)
        assert racer.blob_path.is_file()
        assert store.get(racer.artifact_id).retention_class == "default"


@pytest.mark.parametrize(
    ("table", "column"),
    [
        ("comms_messages", "body_artifact_id"),
        ("formal_review_jobs", "snapshot_artifact_id"),
        ("formal_review_jobs", "sealed_verdict_artifact_id"),
        ("formal_review_attempts", "raw_capture_artifact_id"),
    ],
)
def test_artifact_named_only_by_one_reference_column_is_referenced_and_kept(
    tmp_path: Path, table: str, column: str
) -> None:
    """#12574 T2 (CTO-approved). Defect class: deleting an artifact named only
    by one formal-review column (or the message body column), which the old
    ``is_referenced`` missed. Each column alone must keep the artifact."""
    with ArtifactStore(root=tmp_path / "plane") as store:
        rec = store.store_bytes(_payload(), producer="t")
        _age(store, rec.artifact_id)
        control = store.store_bytes(_payload(), producer="t")
        _age(store, control.artifact_id)
        connection = store._conn
        connection.execute("PRAGMA foreign_keys = OFF")
        columns, values = [], []
        for _cid, name, kind, notnull, default, pk in connection.execute(f"PRAGMA table_info('{table}')"):
            if name == column:
                columns.append(name)
                values.append(rec.artifact_id)
            elif (notnull and default is None) or pk:
                columns.append(name)
                values.append(0 if "INT" in kind.upper() else f"{table}-{name}")
        connection.execute(
            f"INSERT INTO {table}({', '.join(columns)}) VALUES({', '.join('?' * len(values))})", values
        )
        connection.commit()

        assert store.is_referenced(rec.artifact_id)
        assert not store.is_referenced(control.artifact_id)
        report = store.expire_unreferenced_blobs(
            citations=_NO_CITATIONS, apply=True, now=_LATER, backup_dir=tmp_path / "backup"
        )

        assert (report.candidates, report.removed) == (1, 1)
        assert rec.blob_path.is_file()
        assert not control.blob_path.is_file()


def _sources(
    tmp_path: Path,
    *,
    cite_in_github: str = "",
    cite_in_tasks: str = "",
    fetched_at: datetime | None = None,
    kinds: tuple[str, ...] = ("issue", "pull_request", "issue_comment", "pr_review_comment"),
    footer: int | None = None,
) -> CitationSources:
    tasks, docs = tmp_path / "tasks", tmp_path / "docs"
    tasks.mkdir(parents=True)
    docs.mkdir()
    (tasks / "task.json").write_text(json.dumps({"note": cite_in_tasks}))
    (docs / "readme.md").write_text("no citation here\n")
    stamp = (fetched_at or datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [{"kind": "header", "fetched_at": stamp}]
    lines += [{"kind": kind, "body": cite_in_github if kind == "issue" else ""} for kind in kinds]
    lines.append({"kind": "footer", "records": len(kinds) if footer is None else footer})
    dump = tmp_path / "github.jsonl"
    dump.write_text("".join(json.dumps(line) + "\n" for line in lines))
    return CitationSources(tasks_dir=tasks, docs_dir=docs, github_dump=dump)


def test_unreferenced_retention_refuses_unverified_sources_and_keeps_cited(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#12574 T3 (CTO-approved). Defect class: the unreferenced rule starts or
    removes with a missing, empty, stale, incomplete or unreadable citation
    source, or removes a cited artifact."""
    with ArtifactStore(root=tmp_path / "plane") as store:
        names = (
            "by_id", "by_sha", "by_path", "by_doc", "by_note", "by_gz", "by_zip", "by_blob", "by_blobzip", "by_concat", "by_cut",
            "uncited", "padded", "inventory",
        )
        recs = {name: store.store_bytes(_payload(), producer="t") for name in names}
        for rec in recs.values():
            _age(store, rec.artifact_id)
        now = datetime.now(UTC)
        blob_path = lambda rec: f"blobs/sha256/{rec.sha256[:2]}/{rec.sha256}"  # noqa: E731

        def refuses(sources: CitationSources, match: str) -> None:
            with pytest.raises(ArtifactStoreError, match=match):
                store.scan_citations(sources, now=now)
            assert all(r.blob_path.is_file() for r in recs.values())

        empty = _sources(tmp_path / "empty")
        for jsonfile in empty.tasks_dir.glob("*.json"):
            jsonfile.unlink()
        refuses(empty, "no .json file")
        nodocs = _sources(tmp_path / "nodocs")
        (nodocs.docs_dir / "readme.md").unlink()
        refuses(nodocs, "no .md file")
        refuses(
            _sources(tmp_path / "missingkind", kinds=("issue", "pull_request", "issue_comment")),
            "no records of kind",
        )
        refuses(_sources(tmp_path / "stale", fetched_at=now - timedelta(hours=25)), "not within 24 h")
        refuses(_sources(tmp_path / "badfooter", footer=2), "footer says")
        truncated = _sources(tmp_path / "truncated")
        text = truncated.github_dump.read_text().splitlines(keepends=True)
        truncated.github_dump.write_text("".join(text[:-1]))
        refuses(truncated, "header or footer missing")
        missing = _sources(tmp_path / "gone")
        missing.github_dump.unlink()
        refuses(missing, "cannot open")
        linked_file = _sources(tmp_path / "linkfile")
        (linked_file.tasks_dir / "link.json").symlink_to(linked_file.tasks_dir / "task.json")
        refuses(linked_file, "not a regular file")
        linked_dir = _sources(tmp_path / "linkdir")
        (linked_dir.docs_dir / "alias").symlink_to(linked_dir.tasks_dir, target_is_directory=True)
        refuses(linked_dir, "is a symlink")
        vanishing = _sources(tmp_path / "vanishing")
        (vanishing.tasks_dir / "gone.json").write_text("{}")
        real_lstat = os.lstat

        def lstat_then_vanish(path, *args, **kwargs):
            if str(path).endswith("gone.json"):
                raise FileNotFoundError(path)
            return real_lstat(path, *args, **kwargs)

        monkeypatch.setattr(os, "lstat", lstat_then_vanish)
        refuses(vanishing, "vanished during the scan")
        monkeypatch.undo()
        corrupt = _sources(tmp_path / "corrupt")
        (corrupt.docs_dir / "bad.gz").write_bytes(b"\x1f\x8b\x08\x00" + b"not a gzip stream")
        refuses(corrupt, "cannot decode compressed content")
        # A stream cut short refuses in every format: its decoded tail is not
        # proof that nothing after it cited an artifact. So does data after a
        # stream that starts no supported stream.
        for suffix, compress in (("gz", gzip.compress), ("bz2", bz2.compress), ("xz", lzma.compress)):
            cut = _sources(tmp_path / f"cut-{suffix}")
            (cut.docs_dir / f"cut.{suffix}").write_bytes(compress(b"artifact_" + b"a" * 32)[:-8])
            refuses(cut, "ends before its end marker")
        trailing = _sources(tmp_path / "trailing")
        (trailing.docs_dir / "x.bz2").write_bytes(bz2.compress(b"text") + b"garbage")
        refuses(trailing, "starts no supported stream")
        zstd = _sources(tmp_path / "zstd")
        (zstd.docs_dir / "x.zst").write_bytes(b"\x28\xb5\x2f\xfd" + b"\x00" * 16)
        refuses(zstd, "cannot open zstd")
        deep = _sources(tmp_path / "deep")
        layered = b"artifact_" + b"a" * 32
        for _ in range(4):
            layered = gzip.compress(layered)
        (deep.docs_dir / "deep.gz").write_bytes(layered)
        refuses(deep, "nested deeper")
        if os.geteuid() != 0:
            locked = _sources(tmp_path / "locked")
            (locked.tasks_dir / "secret.json").write_text("{}")
            (locked.tasks_dir / "secret.json").chmod(0)
            refuses(locked, "cannot read")

        good = _sources(
            tmp_path / "good",
            cite_in_github=f"see {recs['by_id'].artifact_id}",
            # A bare digest cites; so does a digest in a path in a task note;
            # a 65-character hex run is no token of its own.
            cite_in_tasks=f"{recs['by_sha'].sha256} {blob_path(recs['by_path'])} {recs['padded'].sha256}0",
        )
        # Every docs subtree is scanned, whatever its name or suffix, and
        # compressed content is scanned decompressed (found by magic bytes).
        (good.docs_dir / "data").mkdir()
        (good.docs_dir / "data" / "evidence.mdx").write_text(recs["by_doc"].artifact_id)
        (good.docs_dir / "data" / "evidence.bin").write_bytes(
            gzip.compress(recs["by_gz"].artifact_id.encode())
        )
        # Every stream of a concatenated file is scanned, whatever its format.
        (good.docs_dir / "data" / "joined.bz2").write_bytes(
            bz2.compress(b"prefix") + gzip.compress(recs["by_concat"].artifact_id.encode())
        )
        # A zip inside a zip is read too (zipfile must seek the inner one).
        inner_zip = io.BytesIO()
        with zipfile.ZipFile(inner_zip, "w", zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("inner.txt", gzip.compress(recs["by_zip"].artifact_id.encode()))
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("inner.zip", inner_zip.getvalue())
        (good.tasks_dir / "bundle.dat").write_bytes(archive.getvalue())
        attached = store.store_bytes(gzip.compress(recs["by_blob"].artifact_id.encode()), producer="t")
        store.reference("message_attachment", attached.artifact_id)
        # A zip attachment is read too (zipfile must seek the blob).
        blob_zip = io.BytesIO()
        with zipfile.ZipFile(blob_zip, "w", zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("note.txt", recs["by_blobzip"].artifact_id)
        store.reference("message_attachment", store.store_bytes(blob_zip.getvalue(), producer="t").artifact_id)
        # The dispatcher's generated checkout inventory lists every blob path:
        # exactly those entries are not citations (and are counted). A citation
        # elsewhere in an inventory-named file still holds its artifact.
        snapshots = good.tasks_dir / "job.snapshots.20260101T000000Z.archived"
        snapshots.mkdir()
        inventory_key = f"x/{blob_path(recs['inventory'])}"
        listing = f'"{inventory_key}":"!!"'
        (snapshots / "read_only_checkout_pre.json").write_text("{" + listing + "}")
        # A compressed inventory is decoded before its listings are stripped.
        (snapshots / "read_only_checkout_post.json").write_bytes(
            gzip.compress(
                json.dumps({"note": recs["by_note"].artifact_id, inventory_key: "!!"}, separators=(",", ":")).encode()
            )
        )
        # A linked blob cut short refuses unless its digest is acknowledged; an
        # acknowledgement that matches no cut-short linked blob refuses too.
        cut_bytes = gzip.compress(f"{recs['by_cut'].artifact_id}\n".encode() + os.urandom(4096))[:-100]
        cut_blob = store.store_bytes(cut_bytes, producer="t")
        store.reference("message_attachment", cut_blob.artifact_id)
        refuses(good, "ends before its end marker")
        with pytest.raises(ArtifactStoreError, match="names no message-linked blob"):
            store.scan_citations(good, now=now, accept_truncated=frozenset({cut_blob.sha256, recs["uncited"].sha256}))
        scan = store.scan_citations(good, now=now, accept_truncated=frozenset({cut_blob.sha256}))
        assert scan.cited == frozenset(
            recs[name].artifact_id
            for name in ("by_id", "by_sha", "by_path", "by_doc", "by_note", "by_gz", "by_zip", "by_blob", "by_blobzip", "by_concat", "by_cut")
        )
        # Every byte the decoder can produce before the cut was scanned.
        receipt = {
            "sha256": cut_blob.sha256,
            "format": "gzip",
            "blob_bytes": len(cut_bytes),
            "decoded_bytes": len(zlib.decompressobj(31).decompress(cut_bytes)),
            "stream_offset": 0,
            "truncation_offset": len(cut_bytes),
        }
        assert scan.acknowledged_truncated == (receipt,)
        assert [e["inventory_listings_ignored"] for e in scan.coverage if e["source"] == "tasks"] == [2]
        dry = store.expire_unreferenced_blobs(citations=scan, apply=False, now=_LATER)
        report = store.expire_unreferenced_blobs(
            citations=scan, apply=True, now=_LATER, backup_dir=tmp_path / "backup"
        )
        assert dry.acknowledged_truncated == report.acknowledged_truncated == [receipt]
        assert (report.candidates, report.removed, report.held_cited) == (3, 3, 11)
        assert cut_blob.blob_path.is_file()
        assert {entry["source"] for entry in report.sources} == {"store", "tasks", "docs", "github"}
        for name in ("by_id", "by_sha", "by_path", "by_doc", "by_note", "by_gz", "by_zip", "by_blob", "by_blobzip", "by_concat", "by_cut"):
            assert recs[name].blob_path.is_file()
        for name in ("uncited", "padded", "inventory"):
            assert not recs[name].blob_path.is_file()
        assert store.read_bytes(recs["by_id"].artifact_id)

        # A linked blob that is gone without the expired marker cannot be scanned.
        linked = store.store_bytes(_payload(), producer="t")
        store.reference("message_linked", linked.artifact_id)
        linked.blob_path.unlink()
        refuses_after = pytest.raises(ArtifactStoreError, match="is missing")
        with refuses_after:
            store.scan_citations(good, now=now, accept_truncated=frozenset({cut_blob.sha256}))

    # An acknowledgement covers only the end of the blob's own bytes, and only
    # bytes that hash to the acknowledged digest.
    nested = gzip.compress(gzip.compress(b"x" * 64)[:-8])
    mismatched = gzip.compress(b"y" * 64)[:-8]
    for plane, content, match in (
        ("nested", nested, "complete but holds content cut short"),
        ("mismatched", mismatched, "does not match"),
    ):
        with ArtifactStore(root=tmp_path / f"ack-{plane}") as other:
            rec = other.store_bytes(content, producer="t")
            other.reference("message_attachment", rec.artifact_id)
            if plane == "mismatched":
                rec.blob_path.chmod(0o600)
                rec.blob_path.write_bytes(gzip.compress(b"z" * 64)[:-8])
            with pytest.raises(ArtifactStoreError, match=match):
                other.scan_citations(
                    _sources(tmp_path / f"ack-{plane}-src"), now=now, accept_truncated=frozenset({rec.sha256})
                )

    # An acknowledged digest is never a candidate, in the tally or in the
    # locked re-check, even for an otherwise expirable artifact.
    with ArtifactStore(root=tmp_path / "ack-held") as other:
        held = other.store_bytes(_payload(), producer="t")
        _age(other, held.artifact_id)
        acknowledged = CitationScan(frozenset(), (), ({"sha256": held.sha256},))
        report = other.expire_unreferenced_blobs(
            citations=acknowledged, apply=True, now=_LATER, backup_dir=tmp_path / "ack-held-backup"
        )
        assert (report.candidates, report.removed, report.held_acknowledged) == (0, 0, 1)
        assert held.blob_path.is_file()
        locked = {
            "cutoff": (_LATER - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "artifact_id": held.artifact_id,
        }
        single = _unreferenced_candidate_sql(single=True)
        assert other._candidate_row(single, locked, frozenset()) is not None
        assert other._candidate_row(single, locked, frozenset(), frozenset({held.sha256})) is None
