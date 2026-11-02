"""Content-addressed artifact / file-drop service (Fleet Comms PR-C / #5512).

Store immutable payloads at::

    batch_state/fleet-comms/v1/blobs/sha256/<aa>/<digest>

Creation is temp → fsync → hash → atomic rename → SQLite commit so a crash
never leaves a DB row pointing at a missing blob.

Byte-plane slice (private #603, Phase 0b): when ``fleet_comms`` authority is
``pg`` (``LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS=pg``), payload bytes live
in Postgres (``BYTEA``, content-addressed by sha256) in a small dedicated
table — never in a host-local ``blobs/sha256/...`` file that a second host
with the DSN could not read back. Default authority stays ``sqlite`` (today's
file-backed store, unchanged). ``is_referenced``/
``garbage_collect_unreferenced`` remain sqlite-only in this slice;
``reference`` is dialect-aware (request-execute slice, #605 follow-on).

Retention (#12530): ``expire_message_blobs`` removes the blob files of
finished messages past an age floor while keeping every row and digest
(``python -m scripts.fleet_comms retention``; dry run unless ``--apply``).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import mimetypes
import os
import re
import shutil
import sqlite3
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.control_plane.storage import (
    Authority,
    StoreId,
    assert_component_supported,
)
from scripts.control_plane.storage import connect as cp_connect
from scripts.fleet_comms.contracts import new_id
from scripts.fleet_comms.migrations import apply_migrations
from scripts.fleet_comms.paths import DEFAULT_ROOT_REL, default_plane_root
from scripts.fleet_comms.paths import validate_plane_root as validate_plane_root
from scripts.fleet_comms.pg_schema import (
    PG_BLOB_TABLE,
    PgSchemaError,
    apply_pg_schema,
    verify_pg_schema,
)

DEFAULT_ROOT = DEFAULT_ROOT_REL
_SAFE_NAME = re.compile(r"^[A-Za-z0-9._@+=,-][A-Za-z0-9._@+=, -]{0,200}$")
_PRIVATE_DIR_MODE = 0o700
_PRIVATE_FILE_MODE = 0o600
_BUSY_TIMEOUT_MS = 5_000
# Small, dedicated Postgres table for the pg byte-plane path (#603 / #7483 1.14).
# DDL lives in the numbered pg migration ledger (``pg_schema``); this alias
# keeps SQL in this module pointing at the same table name.
_PG_BLOB_TABLE = PG_BLOB_TABLE
# #7484 (Sol 1.9): ONE documented byte-plane limit, enforced before hashing,
# filesystem writes, or a BYTEA insert. Raw adapter captures are the largest
# legitimate payload class; 64 MiB bounds them while staying far under the
# 1 GB bytea wall and psycopg parameter limits. The rollover-bundle path keeps
# its own tighter 4 MiB cap.
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024

# #12530 (OO-RETENTION-1102): message-blob retention. Only blobs whose producer
# asked for no special retention are collectable; any other class (evidence,
# review, audit, snapshot, verdict, checkpoint, handoff, channel context, ...)
# is a producer-declared hold and is never collected by this rule.
RETENTION_COLLECTABLE_CLASSES = frozenset(
    {"message-body", "historical-message", "acpx-discussion", "default"}
)
# Marker prefixed to ``artifacts.retention_class`` when retention removed the
# blob. The row, its sha256 and its byte count stay, so history keeps proof
# that the body existed and what it hashed to.
RETENTION_EXPIRED_PREFIX = "expired:"
RETENTION_DEFAULT_DAYS = 30
RETENTION_GRACE_SECONDS = 3600
_OPEN_DELIVERY_STATES = ("queued", "running")
_OPEN_REQUEST_STATES = ("queued", "running")
# Every artifact column outside message links. An artifact named here is kept
# whole: job payloads and results (idempotent replay, Kimi admission reads),
# delivery receipts, channel context and formal-review snapshots/verdicts.
_NON_MESSAGE_REFERENCES = (
    ("authority_context_revisions", "artifact_id"),
    ("authority_jobs", "payload_artifact_id"),
    ("authority_jobs", "result_artifact_id"),
    ("authority_deliveries", "acknowledgment_artifact_id"),
    ("authority_delivery_attempts", "artifact_id"),
    ("delivery_attempts", "raw_capture_artifact_id"),
    ("formal_review_jobs", "snapshot_artifact_id"),
    ("formal_review_jobs", "sealed_verdict_artifact_id"),
    ("formal_review_attempts", "raw_capture_artifact_id"),
    ("formal_review_snapshot_seals", "snapshot_artifact_id"),
)


def _retention_candidate_sql(*, single: bool) -> str:
    """Artifacts whose blob the retention rule may remove (sqlite).

    Named parameters: ``:cutoff`` and ``:now`` (ISO-Z), plus ``:artifact_id``
    when ``single`` (the per-artifact re-check under the writer lock, which
    narrows every set to that artifact). An artifact qualifies only when it
    is linked to at least one message, its class is collectable or already
    expired, nothing outside message links names it, and EVERY message that
    links it is older than the cutoff with no open delivery, no pending
    request and no open ACP discussion. Set-based on purpose: the reference
    columns carry no artifact index, so per-row correlated scans cost
    minutes on the live store.
    """
    only = " AND {column} = :artifact_id" if single else ""
    classes = ", ".join(f"'{name}'" for name in sorted(RETENTION_COLLECTABLE_CLASSES))
    deliveries = ", ".join(f"'{state}'" for state in _OPEN_DELIVERY_STATES)
    requests = ", ".join(f"'{state}'" for state in _OPEN_REQUEST_STATES)
    held = "\n      UNION ALL ".join(
        f"SELECT {column} FROM {table} WHERE {column} IS NOT NULL"
        + only.format(column=column)
        for table, column in _NON_MESSAGE_REFERENCES
    )
    return f"""
WITH links(message_id, artifact_id) AS (
  SELECT message_id, artifact_id FROM message_artifacts
   WHERE 1 = 1{only.format(column="artifact_id")}
  UNION ALL
  SELECT message_id, body_artifact_id FROM comms_messages
   WHERE body_artifact_id IS NOT NULL{only.format(column="body_artifact_id")}
),
open_messages(message_id) AS (
  SELECT m.message_id FROM comms_messages m
   WHERE m.message_id IN (SELECT message_id FROM links) AND m.created_at >= :cutoff
  UNION SELECT d.message_id FROM authority_deliveries d
   WHERE d.message_id IN (SELECT message_id FROM links) AND d.state IN ({deliveries})
  UNION SELECT r.request_message_id FROM requests r
   WHERE r.request_message_id IN (SELECT message_id FROM links) AND r.state IN ({requests})
  UNION SELECT m.message_id FROM comms_messages m
   JOIN acp_conversations c ON c.conversation_id = m.conversation_id
   WHERE m.message_id IN (SELECT message_id FROM links) AND c.deadline_at > :now
)
SELECT a.artifact_id, a.sha256, a.bytes, a.retention_class
FROM artifacts a
WHERE (a.retention_class IN ({classes})
       OR a.retention_class LIKE '{RETENTION_EXPIRED_PREFIX}%')
  AND a.created_at < :cutoff{only.format(column="a.artifact_id")}
  AND a.artifact_id IN (SELECT artifact_id FROM links)
  AND a.artifact_id NOT IN (
      {held})
  AND a.artifact_id NOT IN (
      SELECT l.artifact_id FROM links l JOIN open_messages o ON o.message_id = l.message_id)
ORDER BY a.created_at, a.artifact_id
"""


@dataclass(frozen=True, slots=True)
class RetentionReport:
    """Outcome of one ``expire_message_blobs`` run (metadata only)."""

    applied: bool
    older_than_days: int
    cutoff: str
    candidates: int
    candidate_bytes: int
    already_expired: int
    present_blobs: int
    present_bytes: int
    removed: int
    removed_bytes: int
    skipped_recent_use: int
    skipped_changed: int
    by_class: dict[str, dict[str, int]]
    backup_dir: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    artifact_id: str
    sha256: str
    bytes: int
    mime_type: str | None
    logical_filename: str | None
    producer: str
    retention_class: str
    created_at: str
    # None under pg authority (#7484): bytes live in Postgres, a host-local
    # path would be a fabricated contract. Sqlite records always carry one.
    blob_path: Path | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "mime_type": self.mime_type,
            "logical_filename": self.logical_filename,
            "producer": self.producer,
            "retention_class": self.retention_class,
            "created_at": self.created_at,
            "blob_path": str(self.blob_path) if self.blob_path is not None else None,
        }


class ArtifactStoreError(RuntimeError):
    """Artifact store refused an operation."""


class ArtifactExpiredError(ArtifactStoreError):
    """The blob was removed by the retention rule; row and digest remain."""


class ArtifactStore:
    """SQLite metadata + content-addressed blob store."""

    def __init__(
        self,
        root: Path | None = None,
        *,
        repo_root: Path | None = None,
        readonly: bool = False,
    ) -> None:
        self.root = validate_plane_root(
            root
            if root is not None
            else default_plane_root(repo_root=repo_root)
        )
        self.blob_root = self.root / "blobs" / "sha256"
        self.db_path = self.root / "comms.sqlite3"
        self._readonly = bool(readonly)
        self._authority = assert_component_supported(StoreId.FLEET_COMMS, "artifact_store")
        if self._authority is Authority.PG:
            # Byte-plane slice (#603): connect first, touch no local disk.
            # A DSN-unreachable failure must not leave a stray root/blob dir
            # behind, and payload bytes never land in a host-local file.
            self._conn = cp_connect(StoreId.FLEET_COMMS, read_only=self._readonly)
            try:
                self._configure_pg_connection()
                if not self._readonly:
                    # #7483 (1.14): blob + request-plane DDL via checksummed ledger.
                    apply_pg_schema(self._conn)
                # Readonly must still fail closed on missing/drifted schema
                # rather than hitting UndefinedTable on the first blob SELECT.
                verify_pg_schema(self._conn)
            except Exception as exc:
                # #7483: never leak the pg connection on partial init —
                # repeated failures against a flaky DSN exhaust max_connections.
                with contextlib.suppress(Exception):
                    self._conn.close()
                if isinstance(exc, PgSchemaError):
                    raise ArtifactStoreError(
                        "fleet_comms pg schema missing or drifted"
                    ) from exc
                raise
            return
        if self._readonly:
            self._conn = cp_connect(
                StoreId.FLEET_COMMS,
                path=self.db_path,
                read_only=True,
            )
            self._conn.row_factory = sqlite3.Row
            return
        self._prepare_private_dir(self.root)
        self._prepare_private_dir(self.root / "blobs")
        self._prepare_private_dir(self.blob_root)
        self._conn = cp_connect(
            StoreId.FLEET_COMMS,
            path=self.db_path,
            # WAL initialization owns its bounded retry loop below. Install
            # the normal statement busy timeout only after WAL is established.
            timeout=0,
        )
        self._conn.row_factory = sqlite3.Row
        self._enable_wal()
        self._conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        self._conn.execute("PRAGMA synchronous = FULL")
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._tighten_owned_mode(self.db_path, _PRIVATE_FILE_MODE, require_dir=False)
        apply_migrations(self._conn)
        for suffix in ("-wal", "-shm"):
            self._tighten_owned_mode(
                Path(f"{self.db_path}{suffix}"),
                _PRIVATE_FILE_MODE,
                require_dir=False,
            )

    @classmethod
    def open_readonly(
        cls,
        root: Path | None = None,
        *,
        repo_root: Path | None = None,
    ) -> ArtifactStore:
        """Open an existing plane for reads only (#7483 1.12).

        Skips apply/DDL and opens the backend read-only so sealed-verdict
        resolvers (and other body-free readers) never mutate the store and
        never bypass it via a host-local CAS path. On pg this still runs
        ``verify_pg_schema`` (read-only drift gate).
        """
        return cls(root=root, repo_root=repo_root, readonly=True)

    def _configure_pg_connection(self) -> None:
        from psycopg.rows import dict_row

        self._conn.row_factory = dict_row
        # #7483 (1.1/1.2): autocommit reads. Without it psycopg BEGINs on the
        # first SELECT and the store pins an idle-in-transaction snapshot
        # forever (blocks VACUUM, trips idle_in_transaction_session_timeout),
        # and any prior read defeated the deferred-commit ownership guard.
        # Writes use the single ``_transaction`` context manager below;
        # nested blocks become SAVEPOINTs, so a helper error can never poison
        # a caller-owned transaction (Sol 1.3).
        self._conn.autocommit = True

    @contextlib.contextmanager
    def _transaction(self):
        """Single write-transaction owner for sqlite and pg (#7483 acceptance).

        Under pg, delegates to ``conn.transaction()`` (nested = SAVEPOINT).
        Under sqlite, opens ``BEGIN IMMEDIATE`` when the caller does not
        already own a transaction; nested use reuses the outer tx.
        """
        self._refuse_readonly_write("_transaction")
        if self._authority is Authority.PG:
            with self._conn.transaction():
                yield self._conn
            return
        nested = self._conn.in_transaction
        if nested:
            yield self._conn
            return
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield self._conn
        except Exception:
            self._conn.rollback()
            raise
        else:
            self._conn.commit()

    def _refuse_readonly_write(self, op: str) -> None:
        if self._readonly:
            raise ArtifactStoreError(f"read-only ArtifactStore refuses {op}")

    @property
    def authority(self) -> Authority:
        """Resolved control-plane authority this store opened with (#7482)."""
        return self._authority

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> ArtifactStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @property
    def connection(self) -> Any:
        return self._conn

    def blob_path_for(self, digest: str) -> Path:
        digest = digest.lower()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ArtifactStoreError("sha256 digest must be 64 lowercase hex chars")
        return self.blob_root / digest[:2] / digest

    def store_bytes(
        self,
        data: bytes,
        *,
        producer: str,
        retention_class: str = "default",
        mime_type: str | None = None,
        logical_filename: str | None = None,
        artifact_id: str | None = None,
        commit: bool = True,
    ) -> ArtifactRecord:
        """Store bytes; ``commit=False`` requires a caller-owned active transaction."""
        self._refuse_readonly_write("store_bytes")
        if not commit:
            self._require_active_transaction_for_deferred_commit()
        if not producer or not producer.strip():
            raise ArtifactStoreError("producer is required")
        if len(data) > MAX_ARTIFACT_BYTES:
            raise ArtifactStoreError(
                f"artifact payload of {len(data)} bytes exceeds the byte-plane "
                f"limit of {MAX_ARTIFACT_BYTES} bytes (#7484)"
            )
        if logical_filename is not None:
            logical_filename = self._validate_filename(logical_filename)
        digest = hashlib.sha256(data).hexdigest()

        if self._authority is Authority.PG:
            return self._store_bytes_pg(
                data,
                digest=digest,
                producer=producer,
                retention_class=retention_class,
                mime_type=mime_type,
                logical_filename=logical_filename,
                artifact_id=artifact_id,
                commit=commit,
            )

        dest = self.blob_path_for(digest)
        self._prepare_private_dir(dest.parent)

        existing = self._conn.execute(
            "SELECT * FROM artifacts WHERE sha256 = ?", (digest,)
        ).fetchone()
        if existing is not None:
            return self._reuse_existing_blob(existing, dest, data, commit=commit)

        aid = artifact_id or new_id("artifact")
        created = _utc_now()
        mime = mime_type
        if mime is None and logical_filename:
            mime, _ = mimetypes.guess_type(logical_filename)
        try:
            if commit:
                # #7484 CF r2: the blob-existence decision, the blob write,
                # and the row INSERT must share ONE write lock. A writer that
                # saw the blob pre-unlink and then inserted its row after
                # GC's locked unlink committed {row: True, blob: False}.
                # BEGIN IMMEDIATE serializes against _unlink_if_unreferenced:
                # whichever side wins, the losing side re-observes reality
                # (GC sees our row and keeps the blob; we see the unlinked
                # blob and rewrite it).
                self._conn.execute("BEGIN IMMEDIATE")
            if not dest.exists():
                self._write_blob_atomic(dest, data)
            self._conn.execute(
                """INSERT INTO artifacts(
                    artifact_id, sha256, bytes, mime_type, logical_filename,
                    producer, retention_class, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (aid, digest, len(data), mime, logical_filename, producer, retention_class, created),
            )
            if commit:
                self._conn.commit()
        except Exception:
            if commit:
                self._conn.rollback()
            raise
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE artifact_id = ?", (aid,)
        ).fetchone()
        if row is None:
            raise ArtifactStoreError(f"failed to persist artifact metadata for {aid}")
        return self._row_to_record(row)

    def _reuse_existing_blob(
        self,
        existing: sqlite3.Row,
        dest: Path,
        data: bytes,
        *,
        commit: bool,
    ) -> ArtifactRecord:
        """Return a deduplicated row with its blob present and marked in use.

        #12530: touching the blob's mtime opens the retention grace window,
        so a caller that links this artifact to a new message soon after
        cannot lose the bytes to a concurrent retention run (the run re-checks
        mtime under the write lock). A blob already removed by retention is
        rewritten from ``data`` and its class marker restored under the write
        lock, so the row never claims "expired" while the bytes are back.
        """
        retention_class = str(existing["retention_class"])
        if not retention_class.startswith(RETENTION_EXPIRED_PREFIX):
            try:
                os.utime(dest)
            except FileNotFoundError:
                self._write_blob_atomic(dest, data)
            except PermissionError:
                # Not our file to touch; the bytes are present, which is all
                # the pre-#12530 contract promised.
                pass
            return self._row_to_record(existing)
        own_transaction = commit and not self._conn.in_transaction
        if own_transaction:
            self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._write_blob_atomic(dest, data)
            self._conn.execute(
                """UPDATE artifacts SET retention_class = ?
                   WHERE artifact_id = ? AND retention_class = ?""",
                (
                    retention_class[len(RETENTION_EXPIRED_PREFIX):],
                    str(existing["artifact_id"]),
                    retention_class,
                ),
            )
            if own_transaction:
                self._conn.commit()
        except Exception:
            if own_transaction:
                self._conn.rollback()
            raise
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE artifact_id = ?", (str(existing["artifact_id"]),)
        ).fetchone()
        return self._row_to_record(row)

    def _store_bytes_pg(
        self,
        data: bytes,
        *,
        digest: str,
        producer: str,
        retention_class: str,
        mime_type: str | None,
        logical_filename: str | None,
        artifact_id: str | None,
        commit: bool,
    ) -> ArtifactRecord:
        existing = self._pg_row_by_sha256(digest)
        if existing is not None:
            if artifact_id is not None and str(existing["artifact_id"]) != artifact_id:
                # #7483 (1.7): deterministic rejection — same content already
                # stored under a different id; honoring the caller's id would
                # break content addressing, silently renaming would lie.
                raise ArtifactStoreError(
                    f"artifact content already stored as "
                    f"{existing['artifact_id']!r}; refusing duplicate id "
                    f"{artifact_id!r}"
                )
            return self._row_to_record(existing)

        aid = artifact_id or new_id("artifact")
        created = _utc_now()
        mime = mime_type
        if mime is None and logical_filename:
            mime, _ = mimetypes.guess_type(logical_filename)
        if artifact_id is not None:
            id_row = self._pg_row_by_artifact_id(artifact_id)
            if id_row is not None:
                # #7483 (1.7): explicit id already bound to DIFFERENT content —
                # fail deterministically instead of an opaque UniqueViolation
                # that would also abort a caller-owned transaction.
                raise ArtifactStoreError(
                    f"artifact_id {artifact_id!r} already exists with "
                    f"different content (sha256 {id_row['sha256']!r})"
                )
        # ``_transaction`` commits on exit / rolls back on error; nested in a
        # caller-owned transaction it becomes a SAVEPOINT, so an error here
        # rolls back only this write and never poisons the caller (#7483 1.3).
        # A concurrent explicit-id writer can still slip between the
        # pre-checks and the INSERT: convert the narrow UniqueViolation race
        # to the same deterministic error the pre-checks raise (CF r1).
        import psycopg.errors

        try:
            with self._transaction():
                self._conn.execute(
                    f"""INSERT INTO {_PG_BLOB_TABLE}(
                        artifact_id, sha256, bytes, mime_type, logical_filename,
                        producer, retention_class, created_at, payload
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (sha256) DO NOTHING""",
                    (aid, digest, len(data), mime, logical_filename, producer, retention_class, created, data),
                )
        except psycopg.errors.UniqueViolation as exc:
            raise ArtifactStoreError(
                f"artifact_id {aid!r} already exists with different content "
                "(lost a concurrent-writer race)"
            ) from exc
        row = self._pg_row_by_sha256(digest)
        if row is None:
            raise ArtifactStoreError(f"failed to persist artifact metadata for {aid}")
        return self._row_to_record(row)

    # #7484 (Sol 1.15): metadata lookups must not drag the BYTEA payload over
    # the wire — a dedup probe against a 100 MB duplicate used to download all
    # of it. Payload transfer happens only in _pg_payload_by_artifact_id.
    _PG_META_COLUMNS = (
        "artifact_id, sha256, bytes, mime_type, logical_filename, "
        "producer, retention_class, created_at"
    )

    def _pg_row_by_sha256(self, digest: str) -> Any:
        return self._conn.execute(
            f"SELECT {self._PG_META_COLUMNS} FROM {_PG_BLOB_TABLE} WHERE sha256 = %s",
            (digest,),
        ).fetchone()

    def _pg_row_by_artifact_id(self, artifact_id: str) -> Any:
        return self._conn.execute(
            f"SELECT {self._PG_META_COLUMNS} FROM {_PG_BLOB_TABLE} WHERE artifact_id = %s",
            (artifact_id,)
        ).fetchone()

    def store_text(
        self,
        text: str,
        *,
        producer: str,
        retention_class: str = "default",
        logical_filename: str | None = None,
        mime_type: str = "text/plain; charset=utf-8",
        commit: bool = True,
    ) -> ArtifactRecord:
        """Store text; ``commit=False`` requires a caller-owned active transaction."""
        if not commit:
            self._require_active_transaction_for_deferred_commit()
        return self.store_bytes(
            text.encode("utf-8"),
            producer=producer,
            retention_class=retention_class,
            logical_filename=logical_filename,
            mime_type=mime_type,
            commit=commit,
        )

    def import_path(
        self,
        path: Path,
        *,
        producer: str,
        retention_class: str = "default",
        mime_type: str | None = None,
        logical_filename: str | None = None,
    ) -> ArtifactRecord:
        """Import a local file into the store (never hand caller paths to providers)."""
        candidate = path.expanduser()
        # Check symlink on the caller path before resolve() follows it.
        if candidate.is_symlink() or path.is_symlink():
            raise ArtifactStoreError("import refuses symlink paths")
        resolved = candidate.resolve()
        if not resolved.is_file():
            raise ArtifactStoreError(f"import path is not a file: {path}")
        if resolved.is_symlink():
            raise ArtifactStoreError("import refuses symlink paths")
        name = logical_filename or resolved.name
        data = resolved.read_bytes()
        return self.store_bytes(
            data,
            producer=producer,
            retention_class=retention_class,
            mime_type=mime_type,
            logical_filename=name,
        )

    def materialize(
        self,
        artifact_id: str,
        dest_dir: Path,
        *,
        filename: str | None = None,
        readonly: bool = True,
    ) -> Path:
        """Copy blob into an invocation scratch directory as a real file."""
        rec = self.get(artifact_id)
        dest_dir = dest_dir.resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)
        name = filename or rec.logical_filename or f"{rec.sha256[:16]}.bin"
        name = self._validate_filename(name)
        dest = dest_dir / name
        if dest.exists():
            raise ArtifactStoreError(f"materialize target already exists: {dest}")
        if self._authority is Authority.PG:
            # Write the Postgres bytes into scratch directly — there is no
            # host-local blob file to copy from under the pg byte-plane.
            dest.write_bytes(self.read_bytes(artifact_id))
        else:
            shutil.copyfile(rec.blob_path, dest)
        if readonly:
            dest.chmod(0o444)
        return dest

    def get(self, artifact_id: str) -> ArtifactRecord:
        if self._authority is Authority.PG:
            row = self._pg_row_by_artifact_id(artifact_id)
            if row is None:
                raise ArtifactStoreError(f"artifact not found: {artifact_id}")
            return self._row_to_record(row)
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()
        if row is None:
            raise ArtifactStoreError(f"artifact not found: {artifact_id}")
        return self._row_to_record(row)

    def get_by_sha256(self, digest: str) -> ArtifactRecord | None:
        digest = digest.lower()
        if self._authority is Authority.PG:
            row = self._pg_row_by_sha256(digest)
            return self._row_to_record(row) if row else None
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE sha256 = ?", (digest,)
        ).fetchone()
        return self._row_to_record(row) if row else None

    def _pg_payload_by_artifact_id(self, artifact_id: str) -> Any:
        return self._conn.execute(
            f"SELECT sha256, payload FROM {_PG_BLOB_TABLE} WHERE artifact_id = %s",
            (artifact_id,),
        ).fetchone()

    def read_bytes(self, artifact_id: str) -> bytes:
        if self._authority is Authority.PG:
            row = self._pg_payload_by_artifact_id(artifact_id)
            if row is None:
                raise ArtifactStoreError(f"artifact not found: {artifact_id}")
            data = bytes(row["payload"])
            if hashlib.sha256(data).hexdigest() != str(row["sha256"]):
                raise ArtifactStoreError(f"blob digest mismatch for {artifact_id}")
            return data
        rec = self.get(artifact_id)
        if not rec.blob_path.is_file():
            if rec.retention_class.startswith(RETENTION_EXPIRED_PREFIX):
                raise ArtifactExpiredError(
                    f"blob for {artifact_id} (sha256={rec.sha256}) was removed by "
                    "the message retention rule (#12530); the row and digest remain"
                )
            raise ArtifactStoreError(
                f"missing blob for {artifact_id} (sha256={rec.sha256}) — integrity failure"
            )
        data = rec.blob_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != rec.sha256:
            raise ArtifactStoreError(f"blob digest mismatch for {artifact_id}")
        return data

    def reference(
        self,
        message_id: str,
        artifact_id: str,
        relation: str = "body",
        *,
        commit: bool = True,
    ) -> None:
        """Link artifact to a message so GC will not delete it.

        ``commit=False`` is only safe when the caller owns an active transaction
        and will commit or roll it back.
        """
        self._refuse_readonly_write("reference")
        if not commit:
            self._require_active_transaction_for_deferred_commit()
        if not message_id or not artifact_id:
            raise ArtifactStoreError("message_id and artifact_id required")
        self.get(artifact_id)  # ensure exists
        if self._authority is Authority.PG:
            # Autocommit connection: the stub + link share ONE explicit
            # transaction; nested in a caller-owned transaction (commit=False,
            # e.g. the request executor's finalize) it becomes a SAVEPOINT,
            # matching the _store_bytes_pg pattern (#7483 Sol 1.3).
            with self._transaction():
                self._ensure_message_stub(message_id)
                self._conn.execute(
                    """INSERT INTO message_artifacts(message_id, artifact_id, relation)
                       VALUES (%s, %s, %s)
                       ON CONFLICT (message_id, artifact_id, relation) DO NOTHING""",
                    (message_id, artifact_id, relation),
                )
            return
        try:
            self._ensure_message_stub(message_id)
            self._conn.execute(
                """INSERT OR IGNORE INTO message_artifacts(message_id, artifact_id, relation)
                   VALUES (?, ?, ?)""",
                (message_id, artifact_id, relation),
            )
            if commit:
                self._conn.commit()
        except Exception:
            if commit:
                self._conn.rollback()
            raise

    def is_referenced(self, artifact_id: str) -> bool:
        if self._authority is Authority.PG:
            raise ArtifactStoreError(
                "is_referenced() is not implemented for fleet_comms authority=pg in this slice"
            )
        row = self._conn.execute(
            "SELECT 1 FROM message_artifacts WHERE artifact_id = ? LIMIT 1",
            (artifact_id,),
        ).fetchone()
        if row:
            return True
        row = self._conn.execute(
            "SELECT 1 FROM delivery_attempts WHERE raw_capture_artifact_id = ? LIMIT 1",
            (artifact_id,),
        ).fetchone()
        if row:
            return True
        # Authority-mode metadata shares this artifact store.  These checks
        # keep queued payloads, immutable context revisions, delivery receipts,
        # and sealed formal-review snapshots alive through garbage collection.
        for query in (
            "SELECT 1 FROM authority_context_revisions WHERE artifact_id = ? LIMIT 1",
            "SELECT 1 FROM authority_jobs WHERE payload_artifact_id = ? LIMIT 1",
            "SELECT 1 FROM authority_jobs WHERE result_artifact_id = ? LIMIT 1",
            "SELECT 1 FROM authority_deliveries WHERE acknowledgment_artifact_id = ? LIMIT 1",
            "SELECT 1 FROM authority_delivery_attempts WHERE artifact_id = ? LIMIT 1",
            "SELECT 1 FROM formal_review_snapshot_seals WHERE snapshot_artifact_id = ? LIMIT 1",
        ):
            row = self._conn.execute(query, (artifact_id,)).fetchone()
            if row:
                return True
        return False

    def garbage_collect_unreferenced(self, *, grace_seconds: int = 3600) -> list[str]:
        """Delete unreferenced artifacts older than grace. Returns deleted artifact_ids."""
        self._refuse_readonly_write("garbage_collect_unreferenced")
        if self._authority is Authority.PG:
            raise ArtifactStoreError(
                "garbage_collect_unreferenced() is not implemented for "
                "fleet_comms authority=pg in this slice"
            )
        cutoff = (datetime.now(UTC) - timedelta(seconds=grace_seconds)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        rows = self._conn.execute(
            "SELECT artifact_id, sha256, created_at FROM artifacts"
        ).fetchall()
        deleted: list[str] = []
        unlink_candidates: list[str] = []
        for row in rows:
            aid = str(row["artifact_id"])
            if self.is_referenced(aid):
                continue
            if str(row["created_at"]) > cutoff:
                continue
            digest = str(row["sha256"])
            self._conn.execute("DELETE FROM artifacts WHERE artifact_id = ?", (aid,))
            unlink_candidates.append(digest)
            deleted.append(aid)
        # #7484 (Sol 1.6): COMMIT the row deletions BEFORE touching any file.
        # The old unlink-then-commit order could crash into rows that pointed
        # at deleted bytes — the exact failure the module docstring rules out.
        # The inverse window (committed rows gone, files still present) is
        # recoverable garbage: reclaim_orphan_blobs() sweeps it.
        self._conn.commit()
        for digest in unlink_candidates:
            self._unlink_if_unreferenced(digest)
        return deleted

    def _unlink_if_unreferenced(self, digest: str) -> bool:
        """Atomically re-check and unlink one blob (#7484 CF r1).

        The row re-check and the unlink run inside one BEGIN IMMEDIATE
        transaction: a concurrent writer's row INSERT either lands before the
        lock (the check sees it and the blob survives) or blocks until the
        commit — after which the writer's dedup path finds ``dest.exists()``
        False and rewrites the blob atomically. Either way no committed row
        can end up pointing at deleted bytes. A crash between unlink and
        commit leaves no row for the digest (checked under the lock), so
        nothing dangles.
        """
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            still = self._conn.execute(
                "SELECT 1 FROM artifacts WHERE sha256 = ? LIMIT 1", (digest,)
            ).fetchone()
            if still is None:
                path = self.blob_path_for(digest)
                if path.is_file():
                    path.unlink()
                removed = True
            else:
                removed = False
        except Exception:
            self._conn.rollback()
            raise
        self._conn.commit()
        return removed

    def reclaim_orphan_blobs(self, *, grace_seconds: int = 3600) -> list[str]:
        """Delete blob files no artifact row references (crash leftovers).

        #7484 / Sol M6: a crash between blob write and row commit — or between
        GC's row commit and its unlinks — leaves bytes that row-driven GC can
        never discover. Grace-period protected: young files are in-flight
        writes, never touched. Returns the reclaimed digests. Sqlite only.
        """
        self._refuse_readonly_write("reclaim_orphan_blobs")
        if self._authority is Authority.PG:
            raise ArtifactStoreError(
                "reclaim_orphan_blobs() is not implemented for "
                "fleet_comms authority=pg in this slice"
            )
        import time as _time

        reclaimed: list[str] = []
        if not self.blob_root.is_dir():
            return reclaimed
        cutoff_ts = _time.time() - max(0, grace_seconds)
        for shard in sorted(self.blob_root.iterdir()):
            if not shard.is_dir():
                continue
            for blob in sorted(shard.iterdir()):
                digest = blob.name
                if len(digest) != 64:
                    continue
                try:
                    if blob.stat().st_mtime > cutoff_ts:
                        continue
                except OSError:
                    continue
                if self._unlink_if_unreferenced(digest):
                    reclaimed.append(digest)
        return reclaimed

    def expire_message_blobs(
        self,
        *,
        older_than_days: int = RETENTION_DEFAULT_DAYS,
        grace_seconds: int = RETENTION_GRACE_SECONDS,
        apply: bool = False,
        now: datetime | None = None,
        backup_dir: Path | None = None,
    ) -> RetentionReport:
        """Remove blobs of finished messages older than the cutoff (#12530).

        Dry run unless ``apply``. Only the blob file goes; the ``artifacts``
        row keeps its sha256 and byte count, its class gains
        ``RETENTION_EXPIRED_PREFIX``, and every message row stays. Each removal
        re-evaluates the full rule and the blob's mtime inside one
        ``BEGIN IMMEDIATE`` transaction (the store's writer lock, which
        authority writes and new artifact rows also take), then marks the
        row, unlinks and commits. A
        crash before the commit leaves an unmarked row without its blob;
        the next run marks it again. Sqlite only.

        ``backup_dir`` (apply only) copies each blob there, sha256-verified,
        inside the same locked transaction just before its unlink, and
        appends one ``manifest.jsonl`` line per blob, so every removed blob has
        a verified copy (a rolled-back removal can leave an extra one). Restoring a copy through ``store_bytes``
        rewrites the blob and clears the expired marker.
        """
        if older_than_days < 1:
            raise ArtifactStoreError("older_than_days must be at least 1")
        if backup_dir is not None:
            if not apply:
                raise ArtifactStoreError("backup_dir is only meaningful with apply")
            backup_dir = backup_dir.expanduser().resolve()
            if backup_dir.is_relative_to(self.root.resolve()):
                raise ArtifactStoreError("backup_dir must be outside the plane root")
            self._prepare_private_dir(backup_dir)
        if apply:
            self._refuse_readonly_write("expire_message_blobs")
        if self._authority is Authority.PG:
            raise ArtifactStoreError(
                "expire_message_blobs() is not implemented for "
                "fleet_comms authority=pg in this slice"
            )
        moment = now or datetime.now(UTC)
        stamp = moment.strftime("%Y-%m-%dT%H:%M:%SZ")
        cutoff = (moment - timedelta(days=older_than_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {"cutoff": cutoff, "now": stamp}
        rows = self._conn.execute(_retention_candidate_sql(single=False), params).fetchall()
        if not apply and self._conn.in_transaction:
            self._conn.commit()
        by_class: dict[str, dict[str, int]] = {}
        candidate_bytes = present_blobs = present_bytes = 0
        removed = removed_bytes = skipped_recent = skipped_changed = 0
        mtime_floor = moment.timestamp() - max(0, grace_seconds)
        candidates = already_expired = 0
        for row in rows:
            size = int(row["bytes"])
            klass = str(row["retention_class"])
            present = self.blob_path_for(str(row["sha256"])).is_file()
            if not present and klass.startswith(RETENTION_EXPIRED_PREFIX):
                already_expired += 1
                continue
            base_class = klass.removeprefix(RETENTION_EXPIRED_PREFIX)
            bucket = by_class.setdefault(
                base_class, {"candidates": 0, "bytes": 0, "present_blobs": 0, "present_bytes": 0}
            )
            candidates += 1
            candidate_bytes += size
            bucket["candidates"] += 1
            bucket["bytes"] += size
            if present:
                present_blobs += 1
                present_bytes += size
                bucket["present_blobs"] += 1
                bucket["present_bytes"] += size
            if not apply:
                continue
            outcome = self._expire_one_blob(
                str(row["artifact_id"]), params, mtime_floor, backup_dir=backup_dir
            )
            if outcome == "removed":
                removed += 1
                removed_bytes += size
            elif outcome == "recent":
                skipped_recent += 1
            elif outcome == "changed":
                skipped_changed += 1
        return RetentionReport(
            applied=apply,
            older_than_days=older_than_days,
            cutoff=cutoff,
            candidates=candidates,
            candidate_bytes=candidate_bytes,
            already_expired=already_expired,
            present_blobs=present_blobs,
            present_bytes=present_bytes,
            removed=removed,
            removed_bytes=removed_bytes,
            skipped_recent_use=skipped_recent,
            skipped_changed=skipped_changed,
            by_class=dict(sorted(by_class.items())),
            backup_dir=str(backup_dir) if backup_dir is not None else None,
        )

    def _expire_one_blob(
        self,
        artifact_id: str,
        params: dict[str, str],
        mtime_floor: float,
        *,
        backup_dir: Path | None = None,
    ) -> str:
        """Re-check one candidate under the writer lock, then mark and unlink.

        Returns ``removed`` (blob unlinked, or already gone and now marked),
        ``recent`` (blob touched inside the grace window) or ``changed`` (no
        longer a candidate: a new link, an open delivery or a revived row).
        """
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            row = self._conn.execute(
                _retention_candidate_sql(single=True),
                {**params, "artifact_id": artifact_id},
            ).fetchone()
            if row is None:
                self._conn.rollback()
                return "changed"
            path = self.blob_path_for(str(row["sha256"]))
            try:
                if path.stat().st_mtime > mtime_floor:
                    self._conn.rollback()
                    return "recent"
            except FileNotFoundError:
                pass
            klass = str(row["retention_class"])
            if backup_dir is not None:
                self._back_up_blob(path, row, backup_dir)
            if not klass.startswith(RETENTION_EXPIRED_PREFIX):
                self._conn.execute(
                    "UPDATE artifacts SET retention_class = ? WHERE artifact_id = ?",
                    (RETENTION_EXPIRED_PREFIX + klass, artifact_id),
                )
            path.unlink(missing_ok=True)
        except Exception:
            self._conn.rollback()
            raise
        self._conn.commit()
        return "removed"

    def _back_up_blob(self, path: Path, row: sqlite3.Row, backup_dir: Path) -> None:
        """Copy one blob into ``backup_dir`` and record it, or raise.

        The source must hash to its digest (a corrupt blob is refused, never
        removed), the copy is written temp, fsync, rename and re-hashed, and
        the manifest line is fsynced before the caller unlinks the source.
        A blob that is already gone has nothing to copy and gets no line.
        """
        digest = str(row["sha256"])
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            return
        if hashlib.sha256(data).hexdigest() != digest:
            raise ArtifactStoreError(f"refusing to expire corrupt blob {digest}")
        dest = backup_dir / digest[:2] / digest
        self._prepare_private_dir(dest.parent)
        self._write_blob_atomic(dest, data)
        if hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
            raise ArtifactStoreError(f"backup copy of {digest} does not verify")
        entry = json.dumps(
            {
                "artifact_id": str(row["artifact_id"]),
                "sha256": digest,
                "bytes": int(row["bytes"]),
                "retention_class": str(row["retention_class"]).removeprefix(
                    RETENTION_EXPIRED_PREFIX
                ),
                "backed_up_at": _utc_now(),
            },
            sort_keys=True,
        )
        with open(backup_dir / "manifest.jsonl", "a", encoding="utf-8") as handle:
            handle.write(entry + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    # --- V4 canonical authority store (PR #7662 repair 6/7) ----------------
    #
    # Read-only projections of this same plane, plus the exclusive Sources
    # writer. There is deliberately NO method here that accepts a
    # caller-built execution observation (PR #7662 repair 8): the only
    # writer of ``v4_execution_observations`` is the native runner via
    # ``RequestExecutor.finalize_v4_runner_execution``. These methods only
    # ever supply this store's own already-resolved connection and dialect.

    def resolve_v4_execution_observation(self, *, task_id: str, run_id: str, role: str) -> dict[str, Any] | None:
        from scripts.fleet_comms import v4_canonical_authority_store as v4_store

        return v4_store.resolve_execution_observation(task_id=task_id, run_id=run_id, role=role, conn=self._conn, is_pg=self._authority is Authority.PG)

    def record_v4_sources_invocation_from_typed_outcome(
        self,
        *,
        attempt_id: str,
        tool_name: str,
        tool_version: str,
        typed_outcome: dict[str, Any],
    ) -> dict[str, Any] | None:
        """The exclusive Sources-invocation writer: builds the record from
        a typed handler outcome and an authenticated attempt."""
        self._refuse_readonly_write("record_v4_sources_invocation_from_typed_outcome")
        from scripts.fleet_comms import v4_canonical_authority_store as v4_store

        with self._transaction() as conn:
            return v4_store.record_sources_invocation_from_typed_outcome(
                conn=conn,
                is_pg=self._authority is Authority.PG,
                attempt_id=attempt_id,
                tool_name=tool_name,
                tool_version=tool_version,
                typed_outcome=typed_outcome,
                commit=False,
            )

    def resolve_v4_sources_invocation(self, *, invocation_id: str) -> dict[str, Any] | None:
        from scripts.fleet_comms import v4_canonical_authority_store as v4_store

        return v4_store.resolve_sources_invocation(invocation_id=invocation_id, conn=self._conn, is_pg=self._authority is Authority.PG)

    def _write_blob_atomic(self, dest: Path, data: bytes) -> None:
        fd, tmp_name = tempfile.mkstemp(prefix=".art-", dir=str(dest.parent))
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, dest)
            self._tighten_owned_mode(dest, _PRIVATE_FILE_MODE, require_dir=False)
        except Exception:
            with contextlib.suppress(OSError):
                tmp_path.unlink(missing_ok=True)
            raise

    @classmethod
    def _prepare_private_dir(cls, path: Path) -> None:
        missing: list[Path] = []
        candidate = path
        while not candidate.exists():
            missing.append(candidate)
            parent = candidate.parent
            if parent == candidate:
                break
            candidate = parent

        for directory in reversed(missing):
            directory.mkdir(mode=_PRIVATE_DIR_MODE, exist_ok=True)
            cls._tighten_owned_mode(
                directory,
                _PRIVATE_DIR_MODE,
                require_dir=True,
            )
        if not missing:
            cls._tighten_owned_mode(path, _PRIVATE_DIR_MODE, require_dir=True)

    @staticmethod
    def _tighten_owned_mode(path: Path, mode: int, *, require_dir: bool) -> None:
        """Tighten only owned, non-symlink store paths."""
        try:
            stat_result = path.lstat()
        except OSError:
            return
        if path.is_symlink() or stat_result.st_uid != os.getuid():
            return
        if require_dir != path.is_dir():
            return
        path.chmod(mode)

    def _enable_wal(self) -> None:
        """Establish WAL even when multiple first-openers race."""
        deadline = time.monotonic() + (_BUSY_TIMEOUT_MS / 1_000)
        while True:
            try:
                row = self._conn.execute("PRAGMA journal_mode = WAL").fetchone()
                if row is None or str(row[0]).lower() != "wal":
                    raise ArtifactStoreError("fleet communications database refused WAL mode")
                return
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc).lower() or time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)

    def _row_to_record(self, row: sqlite3.Row | dict[str, Any]) -> ArtifactRecord:
        digest = str(row["sha256"])
        return ArtifactRecord(
            artifact_id=str(row["artifact_id"]),
            sha256=digest,
            bytes=int(row["bytes"]),
            mime_type=row["mime_type"],
            logical_filename=row["logical_filename"],
            producer=str(row["producer"]),
            retention_class=str(row["retention_class"]),
            created_at=str(row["created_at"]),
            blob_path=(
                None if self._authority is Authority.PG else self.blob_path_for(digest)
            ),
        )

    def _validate_filename(self, name: str) -> str:
        name = name.strip().replace("\\", "/")
        if ".." in name or name.startswith("/") or "\x00" in name:
            raise ArtifactStoreError("logical_filename rejects traversal/absolute/NUL")
        base = name.rsplit("/", 1)[-1]
        if not base or not _SAFE_NAME.match(base):
            raise ArtifactStoreError(f"unsafe logical_filename: {name!r}")
        if base in {".", ".."}:
            raise ArtifactStoreError("invalid logical_filename")
        return base

    def _ensure_message_stub(self, message_id: str) -> None:
        if self._authority is Authority.PG:
            row = self._conn.execute(
                "SELECT 1 FROM comms_messages WHERE message_id = %s", (message_id,)
            ).fetchone()
            if row:
                return
            conv = new_id("conversation")
            now = _utc_now()
            self._conn.execute(
                "INSERT INTO conversations(conversation_id, created_at, source)"
                " VALUES (%s, %s, %s) ON CONFLICT (conversation_id) DO NOTHING",
                (conv, now, "artifact-store"),
            )
            self._conn.execute(
                """INSERT INTO comms_messages(
                    message_id, conversation_id, kind, sender, body_inline, created_at
                ) VALUES (%s, %s, 'note', 'artifact-store', '', %s)
                ON CONFLICT (message_id) DO NOTHING""",
                (message_id, conv, now),
            )
            return
        row = self._conn.execute(
            "SELECT 1 FROM comms_messages WHERE message_id = ?", (message_id,)
        ).fetchone()
        if row:
            return
        conv = new_id("conversation")
        now = _utc_now()
        self._conn.execute(
            "INSERT OR IGNORE INTO conversations(conversation_id, created_at, source) VALUES (?, ?, ?)",
            (conv, now, "artifact-store"),
        )
        self._conn.execute(
            """INSERT OR IGNORE INTO comms_messages(
                message_id, conversation_id, kind, sender, body_inline, created_at
            ) VALUES (?, ?, 'note', 'artifact-store', '', ?)""",
            (message_id, conv, now),
        )

    def _require_active_transaction_for_deferred_commit(self) -> None:
        if self._authority is Authority.PG:
            import psycopg

            if self._conn.info.transaction_status == psycopg.pq.TransactionStatus.IDLE:
                raise ArtifactStoreError(
                    "commit=False requires a caller-owned active transaction"
                )
            return
        if not self._conn.in_transaction:
            raise ArtifactStoreError(
                "commit=False requires a caller-owned active transaction"
            )
