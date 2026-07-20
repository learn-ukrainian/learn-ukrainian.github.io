"""Content-addressed artifact / file-drop service (Fleet Comms PR-C / #5512).

Store immutable payloads at::

    batch_state/fleet-comms/v1/blobs/sha256/<aa>/<digest>

Creation is temp → fsync → hash → atomic rename → SQLite commit so a crash
never leaves a DB row pointing at a missing blob.
"""

from __future__ import annotations

import contextlib
import hashlib
import mimetypes
import os
import re
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.fleet_comms.contracts import new_id
from scripts.fleet_comms.migrations import apply_migrations

DEFAULT_ROOT = Path("batch_state/fleet-comms/v1")
_SAFE_NAME = re.compile(r"^[A-Za-z0-9._@+=,-][A-Za-z0-9._@+=, -]{0,200}$")


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
    blob_path: Path

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
            "blob_path": str(self.blob_path),
        }


class ArtifactStoreError(RuntimeError):
    """Artifact store refused an operation."""


class ArtifactStore:
    """SQLite metadata + content-addressed blob store."""

    def __init__(self, root: Path | None = None, *, repo_root: Path | None = None) -> None:
        base = repo_root or Path.cwd()
        self.root = (root if root is not None else base / DEFAULT_ROOT).resolve()
        self.blob_root = self.root / "blobs" / "sha256"
        self.db_path = self.root / "comms.sqlite3"
        self.root.mkdir(parents=True, exist_ok=True)
        self.blob_root.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        apply_migrations(self._conn)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> ArtifactStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @property
    def connection(self) -> sqlite3.Connection:
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
    ) -> ArtifactRecord:
        if not producer or not producer.strip():
            raise ArtifactStoreError("producer is required")
        if logical_filename is not None:
            logical_filename = self._validate_filename(logical_filename)
        digest = hashlib.sha256(data).hexdigest()
        dest = self.blob_path_for(digest)
        dest.parent.mkdir(parents=True, exist_ok=True)

        existing = self._conn.execute(
            "SELECT * FROM artifacts WHERE sha256 = ?", (digest,)
        ).fetchone()
        if existing is not None:
            if not dest.exists():
                self._write_blob_atomic(dest, data)
            return self._row_to_record(existing)

        if not dest.exists():
            self._write_blob_atomic(dest, data)

        aid = artifact_id or new_id("artifact")
        created = _utc_now()
        mime = mime_type
        if mime is None and logical_filename:
            mime, _ = mimetypes.guess_type(logical_filename)
        try:
            self._conn.execute(
                """INSERT INTO artifacts(
                    artifact_id, sha256, bytes, mime_type, logical_filename,
                    producer, retention_class, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (aid, digest, len(data), mime, logical_filename, producer, retention_class, created),
            )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE artifact_id = ?", (aid,)
        ).fetchone()
        if row is None:
            raise ArtifactStoreError(f"failed to persist artifact metadata for {aid}")
        return self._row_to_record(row)

    def store_text(
        self,
        text: str,
        *,
        producer: str,
        retention_class: str = "default",
        logical_filename: str | None = None,
        mime_type: str = "text/plain; charset=utf-8",
    ) -> ArtifactRecord:
        return self.store_bytes(
            text.encode("utf-8"),
            producer=producer,
            retention_class=retention_class,
            logical_filename=logical_filename,
            mime_type=mime_type,
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
        shutil.copyfile(rec.blob_path, dest)
        if readonly:
            dest.chmod(0o444)
        return dest

    def get(self, artifact_id: str) -> ArtifactRecord:
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()
        if row is None:
            raise ArtifactStoreError(f"artifact not found: {artifact_id}")
        return self._row_to_record(row)

    def get_by_sha256(self, digest: str) -> ArtifactRecord | None:
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE sha256 = ?", (digest.lower(),)
        ).fetchone()
        return self._row_to_record(row) if row else None

    def read_bytes(self, artifact_id: str) -> bytes:
        rec = self.get(artifact_id)
        if not rec.blob_path.is_file():
            raise ArtifactStoreError(
                f"missing blob for {artifact_id} (sha256={rec.sha256}) — integrity failure"
            )
        data = rec.blob_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != rec.sha256:
            raise ArtifactStoreError(f"blob digest mismatch for {artifact_id}")
        return data

    def reference(self, message_id: str, artifact_id: str, relation: str = "body") -> None:
        """Link artifact to a message so GC will not delete it."""
        if not message_id or not artifact_id:
            raise ArtifactStoreError("message_id and artifact_id required")
        self.get(artifact_id)  # ensure exists
        self._ensure_message_stub(message_id)
        self._conn.execute(
            """INSERT OR IGNORE INTO message_artifacts(message_id, artifact_id, relation)
               VALUES (?, ?, ?)""",
            (message_id, artifact_id, relation),
        )
        self._conn.commit()

    def is_referenced(self, artifact_id: str) -> bool:
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
        return row is not None

    def garbage_collect_unreferenced(self, *, grace_seconds: int = 3600) -> list[str]:
        """Delete unreferenced artifacts older than grace. Returns deleted artifact_ids."""
        cutoff = (datetime.now(UTC) - timedelta(seconds=grace_seconds)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        rows = self._conn.execute(
            "SELECT artifact_id, sha256, created_at FROM artifacts"
        ).fetchall()
        deleted: list[str] = []
        for row in rows:
            aid = str(row["artifact_id"])
            if self.is_referenced(aid):
                continue
            if str(row["created_at"]) > cutoff:
                continue
            digest = str(row["sha256"])
            path = self.blob_path_for(digest)
            self._conn.execute("DELETE FROM artifacts WHERE artifact_id = ?", (aid,))
            if path.is_file():
                # Only remove blob if no other artifact row shares the digest.
                still = self._conn.execute(
                    "SELECT 1 FROM artifacts WHERE sha256 = ? LIMIT 1", (digest,)
                ).fetchone()
                if still is None:
                    path.unlink()
            deleted.append(aid)
        self._conn.commit()
        return deleted

    def _write_blob_atomic(self, dest: Path, data: bytes) -> None:
        fd, tmp_name = tempfile.mkstemp(prefix=".art-", dir=str(dest.parent))
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, dest)
        except Exception:
            with contextlib.suppress(OSError):
                tmp_path.unlink(missing_ok=True)
            raise

    def _row_to_record(self, row: sqlite3.Row) -> ArtifactRecord:
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
            blob_path=self.blob_path_for(digest),
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
        self._conn.commit()
