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
file-backed store, unchanged). ``is_referenced`` remains sqlite-only in
this slice; ``reference`` is dialect-aware (request-execute slice, #605
follow-on).

Retention (#12530): ``expire_message_blobs`` removes the blob files of
finished messages past an age floor while keeping every row and digest
(``python -m scripts.fleet_comms retention``; dry run unless ``--apply``).

Unreferenced artifacts (#12574): ``expire_unreferenced_blobs`` owns artifacts
that no row names. It expires only an allow-listed class past a long window
and never an artifact a declared citation source names (``scan_citations``).
"""

from __future__ import annotations

import bz2
import contextlib
import hashlib
import io
import json
import lzma
import mimetypes
import os
import re
import sqlite3
import stat
import tempfile
import time
import zipfile
import zlib
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
# An expired delivery was never acknowledged. It still pins the message body,
# so expiry cannot make an unread body eligible for retention deletion.
_UNREAD_BODY_PIN_STATES = (*_OPEN_DELIVERY_STATES, "expired")
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
# Every column that names an artifact: message links plus the non-message
# columns above. An artifact named by none of them is "unreferenced" (#12574).
_MESSAGE_REFERENCES = (
    ("message_artifacts", "artifact_id"),
    ("comms_messages", "body_artifact_id"),
)
_ALL_REFERENCES = _MESSAGE_REFERENCES + _NON_MESSAGE_REFERENCES
# #12574: unreferenced artifacts expire only after a long window, only in these
# base classes, and never when a declared source cites them. Every other class
# (retained-evidence, handoff, checkpoint, sealed-verdict, formal-review-snapshot,
# channel-context, raw-capture, any unknown class) is pinned and fails closed.
UNREFERENCED_EXPIRING_CLASSES = frozenset(
    {
        "default",
        "review",
        "evidence",
        "task-evidence",
        "task_evidence",
        "review-evidence",
        "review_evidence",
        "audit",
        "authority-result",
        "authority-job-payload",
        "rejected-review-response",
        "message-body",
        "historical-message",
        "acpx-discussion",
    }
)
# The approved window is a floor: the flag may lengthen it, never shorten it.
UNREFERENCED_DEFAULT_DAYS = 90
UNREFERENCED_MIN_DAYS = 90


def _retention_rank(base_class: str) -> int:
    """How long the existing rules keep this base class. Higher outranks.

    Membership only, in the order the rules delete. ``RETENTION_COLLECTABLE_CLASSES``
    are the message-blob rule's targets (the shorter window), so they rank
    below the rest of ``UNREFERENCED_EXPIRING_CLASSES``. A class in neither
    set is pinned. This is not a new class list.
    """
    if base_class in RETENTION_COLLECTABLE_CLASSES:
        return 0
    if base_class in UNREFERENCED_EXPIRING_CLASSES:
        return 1
    return 2


def _kept_retention_class(current: str, requested: str) -> str:
    """Class to persist when the same bytes are stored again (#12590).

    A requested class that outranks the current base class replaces it.
    A weaker or equal request, including the default, keeps the current
    base class, so a hold is never downgraded. The ``expired:`` marker is
    not a class: a revived row stores the base class, upgraded when the
    request outranks it.
    """
    current_base = current.removeprefix(RETENTION_EXPIRED_PREFIX)
    requested_base = requested.removeprefix(RETENTION_EXPIRED_PREFIX)
    if _retention_rank(requested_base) > _retention_rank(current_base):
        return requested_base
    return current_base


GITHUB_DUMP_MAX_AGE_SECONDS = 24 * 3600
GITHUB_DUMP_KINDS = frozenset({"issue", "pull_request", "issue_comment", "pr_review_comment"})
_CITE_ID = re.compile(rb"artifact_[0-9a-f]{32}")
# A sha256 is a citation only as a token of its own: not part of a longer hex run.
_CITE_SHA = re.compile(rb"(?<![0-9a-f])([0-9a-f]{64})(?![0-9a-f])")
_SCAN_CHUNK = 8 * 1024 * 1024
# Compressed content is scanned decompressed, by magic bytes and never by suffix:
# a citation inside a gzip, bzip2, xz or zip file is still a citation. Nesting and
# the decompressed size of one top-level file are bounded; anything beyond them,
# any decode error, data after a stream that starts no supported stream, a
# stream cut short, an encrypted zip member and a format this scanner cannot
# open (zstd, 7z, rar, lz4) refuses the run instead of being skipped. The one
# waiver is an acknowledged message-linked blob cut at its end
# (``ArtifactStore._acknowledge_cut``).
_ARCHIVE_MAX_DEPTH = 3
_ARCHIVE_MAX_BYTES = 2 * 1024 * 1024 * 1024
_UNSUPPORTED_MAGIC = {
    b"\x28\xb5\x2f\xfd": "zstd",
    b"7z\xbc\xaf\x27\x1c": "7z",
    b"Rar!\x1a\x07": "rar",
    b"\x04\x22\x4d\x18": "lz4",
}
_SCAN_OVERLAP = 96
# The dispatcher writes a full inventory of the checkout (path -> git status) before
# and after a read-only task, so it lists every ignored blob path. Only an entry of
# that exact shape, ``"<...>/blobs/sha256/<aa>/<aa...digest>":"!!"`` (git's "ignored" status) inside one of
# these two files (live or archived snapshot directories), is a listing and not a citation;
# the rest of the file is scanned like any other.
_INVENTORY_SNAPSHOT_FILES = frozenset({"read_only_checkout_pre.json", "read_only_checkout_post.json"})
_INVENTORY_ENTRY = re.compile(rb'"(?:[^"\\]*/)?blobs/sha256/([0-9a-f]{2})/\1[0-9a-f]{62}":"!!",?')
_INVENTORY_MAX_BYTES = 256 * 1024 * 1024


def _retention_candidate_sql(*, single: bool) -> str:
    """Artifacts whose blob the retention rule may remove (sqlite).

    Named parameters: ``:cutoff`` and ``:now`` (ISO-Z), plus ``:artifact_id``
    when ``single`` (the per-artifact re-check under the writer lock, which
    narrows every set to that artifact). An artifact qualifies only when it
    is linked to at least one message, its class is collectable or already
    expired, nothing outside message links names it, and EVERY message that
    links it is older than the cutoff with no queued, running, or expired
    delivery, no pending request and no open ACP discussion. An expired
    delivery was never acknowledged, so it keeps an unread body ineligible.
    Set-based on purpose: the reference
    columns carry no artifact index, so per-row correlated scans cost
    minutes on the live store.
    """
    only = " AND {column} = :artifact_id" if single else ""
    classes = ", ".join(f"'{name}'" for name in sorted(RETENTION_COLLECTABLE_CLASSES))
    deliveries = ", ".join(f"'{state}'" for state in _UNREAD_BODY_PIN_STATES)
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


def _unreferenced_candidate_sql(*, single: bool) -> str:
    """Artifacts nothing names whose blob the unreferenced rule may remove.

    Named parameters: ``:cutoff`` (ISO-Z) and, when ``single``, ``:artifact_id``
    (the per-artifact re-check under the writer lock). An artifact qualifies
    only when no column in ``_ALL_REFERENCES`` names it, its base class (the
    ``expired:`` prefix stripped, so the allow-list is never bypassed) is in
    ``UNREFERENCED_EXPIRING_CLASSES`` and it is older than the cutoff. Citation
    is judged by the caller from its scanned sources, not here.
    """
    only = " AND {column} = :artifact_id" if single else ""
    classes = ", ".join(f"'{name}'" for name in sorted(UNREFERENCED_EXPIRING_CLASSES))
    held = "\n      UNION ALL ".join(
        f"SELECT {column} FROM {table} WHERE {column} IS NOT NULL" + only.format(column=column)
        for table, column in _ALL_REFERENCES
    )
    offset = len(RETENTION_EXPIRED_PREFIX) + 1
    return f"""
SELECT a.artifact_id, a.sha256, a.bytes, a.retention_class
FROM artifacts a
WHERE CASE WHEN a.retention_class LIKE '{RETENTION_EXPIRED_PREFIX}%'
           THEN substr(a.retention_class, {offset}) ELSE a.retention_class END IN ({classes})
  AND a.created_at < :cutoff{only.format(column="a.artifact_id")}
  AND a.artifact_id NOT IN (
      {held})
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
    held_acknowledged: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class UnreferencedReport:
    """Outcome of one ``expire_unreferenced_blobs`` run (metadata only)."""

    applied: bool
    older_than_days: int
    cutoff: str
    candidates: int
    candidate_bytes: int
    held_cited: int
    held_cited_bytes: int
    held_acknowledged: int
    already_expired: int
    present_blobs: int
    present_bytes: int
    removed: int
    removed_bytes: int
    skipped_recent_use: int
    skipped_changed: int
    by_class: dict[str, dict[str, int]]
    sources: list[dict[str, Any]]
    acknowledged_truncated: list[dict[str, Any]]
    backup_dir: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CitationSources:
    """The declared outside-the-store places that may cite an artifact (#12574).

    All five are required: the unreferenced rule never runs on a partial set.
    """

    tasks_dir: Path
    docs_dir: Path
    github_dump: Path
    citation_export: Path
    batch_state_dir: Path


@dataclass(frozen=True, slots=True)
class CitationScan:
    """Artifacts a verified scan found cited, plus per-source coverage."""

    cited: frozenset[str]
    coverage: tuple[dict[str, Any], ...]
    # Message-linked blobs cut short whose acknowledgement this scan honoured
    # (``scan_citations``): sha256, format, blob_bytes, decoded_bytes,
    # stream_offset, truncation_offset. Retention never removes these blobs.
    acknowledged_truncated: tuple[dict[str, Any], ...] = ()


_STREAM_MAGIC = ((b"\x1f\x8b", "gzip"), (b"BZh", "bzip2"), (b"\xfd7zXZ\x00", "xz"))
_STREAM_MAGIC_MAX = 6
_STREAM_READ = 1024 * 1024
_ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06")
# Everything a decoder or zipfile raises for content it cannot decode.
_DECODE_ERRORS = (
    OSError, EOFError, ValueError, NotImplementedError, zlib.error, lzma.LZMAError, zipfile.BadZipFile,
)


def _stream_format(head: bytes) -> str | None:
    """The compressed stream format whose magic bytes start ``head``, if any."""
    for magic, name in _STREAM_MAGIC:
        if head.startswith(magic):
            return name
    return None


class _StreamReader(io.RawIOBase):
    """Decode a gzip, bzip2 or xz file, every stream in it, completely or not at all.

    Built on the decompressor objects rather than ``GzipFile``, ``BZ2File`` or
    ``LZMAFile``: those drop the decoded tail of a stream that is cut short,
    and the bzip2 and xz readers stop silently at data after their first
    stream. Here the end of one stream starts the next, of whichever supported
    format its magic bytes name; zero padding is skipped only after a gzip
    member, across read boundaries. Any other data after a stream, corrupt
    data, and input that ends inside a stream raise, so the caller never
    treats an incomplete decode as a complete scan (#12574). Each call
    returns at most the caller's buffer, and every decoded byte is charged to
    ``charge`` before it is handed out, so highly compressible input never
    builds a large buffer ahead of the size cap.
    """

    def __init__(self, source: Any, fmt: str, charge: Any) -> None:
        super().__init__()
        self._source = source
        self._charge = charge
        self._fmt = fmt
        self._decoder = self._new_decoder(fmt)
        self._input = b""
        self._source_done = False
        self._between = False
        # Input offsets: bytes read from ``source``, and where the current stream began.
        self.consumed = 0
        self.stream_offset = 0
        # Set when ``source`` ends inside a stream. The reader then reports the
        # end of its data, so the caller scans every decoded byte before it
        # refuses (``_ScanState.feed_stream`` raises ``_CutShort``).
        self.cut_short = False

    @staticmethod
    def _new_decoder(fmt: str) -> Any:
        if fmt == "gzip":
            return zlib.decompressobj(31)
        if fmt == "bzip2":
            return bz2.BZ2Decompressor()
        return lzma.LZMADecompressor(format=lzma.FORMAT_XZ)

    def readable(self) -> bool:
        return True

    def _read_more(self) -> bool:
        if self._source_done:
            return False
        raw = self._source.read(_STREAM_READ)
        if not raw:
            self._source_done = True
            return False
        self.consumed += len(raw)
        self._input += raw
        return True

    def _start_next_stream(self) -> bool:
        """After a stream's end: start the next stream, or return False at a clean end."""
        while True:
            if self._fmt == "gzip":
                self._input = self._input.lstrip(b"\x00")
            if len(self._input) >= _STREAM_MAGIC_MAX or not self._read_more():
                break
        if not self._input:
            return False
        fmt = _stream_format(self._input)
        if fmt is None:
            raise ArtifactStoreError(
                f"citation scan: data that starts no supported stream follows a {self._fmt} stream; refusing"
            )
        self._fmt = fmt
        self._decoder = self._new_decoder(fmt)
        self._between = False
        self.stream_offset = self.consumed - len(self._input)
        return True

    @property
    def fmt(self) -> str:
        return self._fmt

    def readinto(self, buffer: Any) -> int:
        size = len(buffer)
        if not size or self.cut_short:
            return 0
        while True:
            if self._between and not self._start_next_stream():
                return 0
            decoder = self._decoder
            out = decoder.decompress(self._input, size)
            if decoder.eof:
                self._input = decoder.unused_data
                self._between = True
            else:
                # zlib returns the input it did not take; bz2 and lzma buffer it.
                self._input = decoder.unconsumed_tail if self._fmt == "gzip" else b""
            if out:
                self._charge(len(out))
                buffer[: len(out)] = out
                return len(out)
            if self._between:
                continue
            if self._input:
                raise ArtifactStoreError(f"citation scan: the {self._fmt} decoder made no progress; refusing")
            if not self._read_more():
                self.cut_short = True
                return 0


class _HashingReader(io.RawIOBase):
    """Read a file, hashing and counting exactly the bytes handed to the scan.

    Seeking is delegated, so a zip blob (which ``zipfile`` must seek) stays
    readable. The digest covers the file only while the reads run unbroken
    from the start: any seek away from the current end of the hashed bytes
    clears ``sequential``, and an acknowledgement needs it set.
    """

    def __init__(self, source: Any) -> None:
        super().__init__()
        self._source = source
        self.digest = hashlib.sha256()
        self.size = 0
        self.sequential = True

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return self._source.seekable()

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        position = self._source.seek(offset, whence)
        if position != self.size:
            self.sequential = False
        return position

    def tell(self) -> int:
        return self._source.tell()

    def readinto(self, buffer: Any) -> int:
        count = self._source.readinto(buffer)
        if count:
            self.digest.update(memoryview(buffer)[:count])
            self.size += count
        return count or 0


class _ChargedReader(io.RawIOBase):
    """Pass a zip member through, charging every decoded byte to the size cap.

    A member that is itself a zip must be seekable for ``zipfile``. A seek
    never lets the member decompress on its own (``ZipExtFile.seek`` would,
    uncharged): moving back rewinds the member to its start, which decodes
    nothing, and moving forward reads and discards through the charged path
    in bounded chunks. ``size`` (the member's declared size) resolves a seek
    from the end. Bytes decoded again after a seek are charged again.
    """

    def __init__(self, source: Any, charge: Any, size: int) -> None:
        super().__init__()
        self._source = source
        self._charge = charge
        self._size = size
        self._position = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return self._source.seekable()

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self._position, io.SEEK_END: self._size}[whence]
        target = base + offset
        if target < 0:
            raise ValueError("negative seek position")
        if target < self._position:
            self._source.seek(0)
            self._position = 0
        while self._position < target:
            data = self._source.read(min(_STREAM_READ, target - self._position))
            if not data:
                break
            self._charge(len(data))
            self._position += len(data)
        return self._position

    def tell(self) -> int:
        return self._position

    def readinto(self, buffer: Any) -> int:
        data = self._source.read(len(buffer))
        self._charge(len(data))
        self._position += len(data)
        buffer[: len(data)] = data
        return len(data)


class _PrefixedReader(io.RawIOBase):
    """Hand out ``prefix`` (bytes already read from ``source``), then the rest of ``source``."""

    def __init__(self, prefix: bytes, source: Any) -> None:
        super().__init__()
        self._prefix = prefix
        self._source = source

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        if self._prefix:
            count = min(len(buffer), len(self._prefix))
            buffer[:count] = self._prefix[:count]
            self._prefix = self._prefix[count:]
            return count
        data = self._source.read(len(buffer))
        buffer[: len(data)] = data
        return len(data)


_PREFIX_BYTES = 8


def _with_full_prefix(handle: Any) -> tuple[bytes, Any]:
    """Return the first bytes of ``handle`` for format detection, and a handle still holding them.

    ``peek`` returns at most one read of the source, which for decoded output
    can be shorter than a magic number (a stream whose first member decodes
    to one byte). The prefix is therefore complete: ``_PREFIX_BYTES`` bytes,
    or fewer only at the end of the data.
    """
    if not hasattr(handle, "peek"):
        handle = io.BufferedReader(handle)
    head = handle.peek(_PREFIX_BYTES)[:_PREFIX_BYTES]
    if len(head) >= _PREFIX_BYTES:
        return head, handle
    head = handle.read(_PREFIX_BYTES)
    return head, io.BufferedReader(_PrefixedReader(head, handle))


class _ScanState:
    """Accumulates cited artifact ids while a scan streams bytes."""

    def __init__(self, known_ids: frozenset[bytes], sha_to_id: dict[bytes, str]) -> None:
        self.known_ids = known_ids
        self.sha_to_id = sha_to_id
        self.cited: set[str] = set()
        self._decompressed = 0
        # Fully decoded bytes scanned for citations in the current top-level file.
        self.plain_bytes = 0

    def feed(self, data: bytes) -> None:
        for token in _CITE_ID.findall(data):
            if token in self.known_ids:
                self.cited.add(token.decode("ascii"))
        for token in _CITE_SHA.findall(data):
            artifact_id = self.sha_to_id.get(token)
            if artifact_id is not None:
                self.cited.add(artifact_id)

    def charge(self, count: int) -> None:
        """Count decoded bytes of one top-level file, at every nesting level, against the cap."""
        self._decompressed += count
        if self._decompressed > _ARCHIVE_MAX_BYTES:
            raise ArtifactStoreError(
                f"citation scan: decompressed content exceeds {_ARCHIVE_MAX_BYTES} bytes; refusing"
            )

    def feed_stream(self, handle: Any, depth: int = 0) -> int:
        """Scan a binary handle end to end, looking inside compressed content.

        Returns the bytes scanned (decompressed bytes for a compressed file).
        Raises ``ArtifactStoreError`` for content it cannot scan completely.
        """
        if depth == 0:
            self._decompressed = 0
            self.plain_bytes = 0
        head, handle = _with_full_prefix(handle)
        for magic, name in _UNSUPPORTED_MAGIC.items():
            if head.startswith(magic):
                raise ArtifactStoreError(f"citation scan cannot open {name} content; refusing")
        fmt = _stream_format(head)
        if fmt is None and not head.startswith(_ZIP_MAGIC):
            return self._feed_plain(handle)
        if depth >= _ARCHIVE_MAX_DEPTH:
            raise ArtifactStoreError(
                f"citation scan: compressed content nested deeper than {_ARCHIVE_MAX_DEPTH}; refusing"
            )
        total = 0
        try:
            if fmt is not None:
                reader = _StreamReader(handle, fmt, self.charge)
                with io.BufferedReader(reader) as inner:
                    total += self._feed_decoded(reader, depth + 1, lambda: self.feed_stream(inner, depth + 1))
            else:
                with zipfile.ZipFile(handle) as archive:
                    for info in archive.infolist():
                        if info.is_dir():
                            continue
                        if info.flag_bits & 0x1:
                            raise ArtifactStoreError(
                                f"citation scan: encrypted zip member {info.filename!r}; refusing"
                            )
                        with archive.open(info) as member:
                            try:
                                total += self.feed_stream(
                                    _ChargedReader(member, self.charge, info.file_size), depth + 1
                                )
                            except _CutShort as exc:
                                # The members after this one are unscanned: never waivable.
                                raise ArtifactStoreError(
                                    f"citation scan: zip member {info.filename!r}: {exc}"
                                ) from exc
        except ArtifactStoreError:
            raise
        except (*_DECODE_ERRORS, RuntimeError) as exc:
            raise ArtifactStoreError(f"citation scan cannot decode compressed content: {exc}") from exc
        return total

    @staticmethod
    def _feed_decoded(reader: _StreamReader, depth: int, scan: Any) -> Any:
        """Run ``scan`` over the output of ``reader`` (a stream at ``depth``), then raise
        ``_CutShort`` if the reader's input ended inside a stream.

        A cut in a nested stream is reported as the cut of this stream when
        this stream's own input ended too (the nested cut is its consequence).
        """
        try:
            result = scan()
        except _CutShort:
            if not reader.cut_short:
                raise
        else:
            if not reader.cut_short:
                return result
        raise _CutShort(reader.fmt, depth, reader.stream_offset, reader.consumed)

    def _feed_plain(self, handle: Any) -> int:
        tail = b""
        total = 0
        while chunk := handle.read(_SCAN_CHUNK):
            total += len(chunk)
            self.plain_bytes += len(chunk)
            self.feed(tail + chunk)
            tail = chunk[-_SCAN_OVERLAP:]
        return total

    def feed_inventory(self, handle: Any, depth: int = 0) -> tuple[int, int]:
        """Scan a generated checkout inventory; returns (bytes read, listings ignored).

        Only entries of the exact blob-listing shape are ignored; everything
        else is scanned in full. A gzip, bzip2 or xz inventory is decoded
        first, under the same rules as any compressed content; a zip or other
        archive under an inventory name is scanned like any other file, so its
        listings hold their artifacts. A file too large to hold in memory
        refuses the run (none exists: the largest live inventory is about 42 MB).
        """
        if depth == 0:
            self._decompressed = 0
        head, handle = _with_full_prefix(handle)
        fmt = _stream_format(head)
        if fmt is not None:
            if depth >= _ARCHIVE_MAX_DEPTH:
                raise ArtifactStoreError(
                    f"citation scan: compressed content nested deeper than {_ARCHIVE_MAX_DEPTH}; refusing"
                )
            try:
                reader = _StreamReader(handle, fmt, self.charge)
                with io.BufferedReader(reader) as inner:
                    return self._feed_decoded(reader, depth + 1, lambda: self.feed_inventory(inner, depth + 1))
            except ArtifactStoreError:
                raise
            except (*_DECODE_ERRORS, RuntimeError) as exc:
                raise ArtifactStoreError(f"citation scan cannot decode compressed content: {exc}") from exc
        if head.startswith(_ZIP_MAGIC) or any(head.startswith(m) for m in _UNSUPPORTED_MAGIC):
            return self.feed_stream(handle, depth), 0
        data = handle.read(_INVENTORY_MAX_BYTES + 1)
        if len(data) > _INVENTORY_MAX_BYTES:
            raise ArtifactStoreError(
                f"citation source: a checkout inventory exceeds {_INVENTORY_MAX_BYTES} bytes"
            )
        rest, listed = _INVENTORY_ENTRY.subn(b"", data)
        self.feed(rest)
        return len(data), listed


def _fsync_directory(path: Path) -> None:
    """Persist a directory's entries (a rename or a new child) to disk."""
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


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


class _CutShort(ArtifactStoreError):
    """Input ended inside a compressed stream, after every decoded byte was scanned.

    ``depth`` is the nesting level of the stream (1: the scanned file's own
    bytes). ``truncation_offset`` is the offset, in that stream's input (the
    file itself at depth 1), at which the input ends: the input's length.
    ``stream_offset`` is where in that input the unfinished stream began.
    """

    def __init__(self, fmt: str, depth: int, stream_offset: int, truncation_offset: int) -> None:
        super().__init__(
            f"citation scan: a {fmt} stream ends before its end marker (cut short at input offset "
            f"{truncation_offset}, depth {depth}; the stream began at offset {stream_offset}); refusing"
        )
        self.fmt = fmt
        self.depth = depth
        self.stream_offset = stream_offset
        self.truncation_offset = truncation_offset


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
            reused = self._reuse_existing_blob(
                digest, dest, data, commit=commit, retention_class=retention_class
            )
            if reused is not None:
                return reused

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
        digest: str,
        dest: Path,
        data: bytes,
        *,
        commit: bool,
        retention_class: str,
    ) -> ArtifactRecord | None:
        """Return a deduplicated row with its blob present and marked in use.

        #12530: runs under the store's writer lock, the lock retention holds
        while it re-checks and unlinks, and re-reads the row under it. A live
        row's blob gets its mtime touched (rewritten if missing), which opens
        retention's grace window, so a caller that links this artifact to a
        new message soon after cannot lose the bytes. An expired row's blob is
        rewritten from ``data`` and its class restored. Inside a caller-owned
        transaction a no-op UPDATE takes the same lock. Returns None when the
        row vanished, so the caller inserts it afresh.

        #12590: the class written under that same lock is
        ``_kept_retention_class`` of the row and the caller's
        ``retention_class``. A stronger request upgrades the row before the
        lock is released; a weaker or default request does not downgrade it.
        """
        own_transaction = commit and not self._conn.in_transaction
        if own_transaction:
            self._conn.execute("BEGIN IMMEDIATE")
        try:
            if not own_transaction:
                self._conn.execute(
                    "UPDATE artifacts SET retention_class = retention_class WHERE sha256 = ?",
                    (digest,),
                )
            row = self._conn.execute(
                "SELECT * FROM artifacts WHERE sha256 = ?", (digest,)
            ).fetchone()
            if row is not None:
                stored = str(row["retention_class"])
                chosen = _kept_retention_class(stored, retention_class)
                if stored.startswith(RETENTION_EXPIRED_PREFIX):
                    self._write_blob_atomic(dest, data)
                else:
                    try:
                        os.utime(dest)
                    except FileNotFoundError:
                        self._write_blob_atomic(dest, data)
                    except PermissionError:
                        # Not our file to touch; the bytes are present, which
                        # is all the pre-#12530 contract promised.
                        pass
                if chosen != stored:
                    self._conn.execute(
                        "UPDATE artifacts SET retention_class = ? WHERE artifact_id = ?",
                        (chosen, str(row["artifact_id"])),
                    )
            if own_transaction:
                self._conn.commit()
        except Exception:
            if own_transaction:
                self._conn.rollback()
            raise
        if row is None:
            return None
        return self.get(str(row["artifact_id"]))

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
            reused = self._reuse_existing_pg_blob(digest, retention_class, data)
            if reused is not None:
                return reused

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
                inserted = self._conn.execute(
                    f"""INSERT INTO {_PG_BLOB_TABLE}(
                        artifact_id, sha256, bytes, mime_type, logical_filename,
                        producer, retention_class, created_at, payload
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (sha256) DO NOTHING""",
                    (aid, digest, len(data), mime, logical_filename, producer, retention_class, created, data),
                )
                # A concurrent insert of the same digest wins the conflict
                # (rowcount 0). Upgrade that row under this same transaction.
                # A row this statement inserted keeps the class it wrote.
                if inserted.rowcount != 1:
                    self._upgrade_pg_retention_locked(digest, retention_class, data)
        except psycopg.errors.UniqueViolation as exc:
            raise ArtifactStoreError(
                f"artifact_id {aid!r} already exists with different content "
                "(lost a concurrent-writer race)"
            ) from exc
        row = self._pg_row_by_sha256(digest)
        if row is None:
            raise ArtifactStoreError(f"failed to persist artifact metadata for {aid}")
        return self._row_to_record(row)

    def _reuse_existing_pg_blob(
        self, digest: str, retention_class: str, data: bytes
    ) -> ArtifactRecord | None:
        """Upgrade an existing Postgres row under the store writer transaction.

        ``_transaction`` is the pg writer lock (a nested call is a savepoint),
        the same role as the ``BEGIN IMMEDIATE`` in ``_reuse_existing_blob``.
        The class decision is ``_kept_retention_class``. An expired row's
        payload is rewritten from ``data`` before that marker is cleared, in
        the same transaction, so a committed row is never live without its
        bytes. Returns None when the row vanished, so the caller inserts it.
        """
        with self._transaction():
            self._upgrade_pg_retention_locked(digest, retention_class, data)
        row = self._pg_row_by_sha256(digest)
        if row is None:
            return None
        return self._row_to_record(row)

    def _upgrade_pg_retention_locked(self, digest: str, requested: str, data: bytes) -> None:
        """Write a stronger class for ``digest``. Caller holds ``_transaction``.

        When ``retention_class`` carries the expired marker, the payload is
        rewritten from ``data`` before the marker is cleared. Both writes
        share the caller's transaction, so neither commits alone.
        """
        row = self._conn.execute(
            f"SELECT {self._PG_META_COLUMNS} FROM {_PG_BLOB_TABLE} "
            "WHERE sha256 = %s FOR UPDATE",
            (digest,),
        ).fetchone()
        if row is None:
            return
        stored = str(row["retention_class"])
        chosen = _kept_retention_class(stored, requested)
        expired = stored.startswith(RETENTION_EXPIRED_PREFIX)
        if not expired and chosen == stored:
            return
        if expired:
            if hashlib.sha256(data).hexdigest() != digest:
                raise ArtifactStoreError(
                    f"refusing to revive {digest}: bytes do not match the stored digest"
                )
            self._conn.execute(
                f"UPDATE {_PG_BLOB_TABLE} SET payload = %s, bytes = %s WHERE artifact_id = %s",
                (data, len(data), row["artifact_id"]),
            )
        if chosen != stored:
            self._conn.execute(
                f"UPDATE {_PG_BLOB_TABLE} SET retention_class = %s WHERE artifact_id = %s",
                (chosen, row["artifact_id"]),
            )

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
        # Both backends go through read_bytes: it verifies the digest and
        # reports a retention-removed blob as ArtifactExpiredError (#12530).
        dest.write_bytes(self.read_bytes(artifact_id))
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
        try:
            data = rec.blob_path.read_bytes()
        except FileNotFoundError:
            # Judge from metadata read after the miss: retention commits the
            # expired marker before it unlinks (#12530), so a blob removed
            # while this read ran is reported as expired, not as corruption.
            current = self.get(artifact_id)
            if current.retention_class.startswith(RETENTION_EXPIRED_PREFIX):
                raise ArtifactExpiredError(
                    f"blob for {artifact_id} (sha256={rec.sha256}) was removed by "
                    "the message retention rule (#12530); the row and digest remain"
                ) from None
            raise ArtifactStoreError(
                f"missing blob for {artifact_id} (sha256={rec.sha256}) — integrity failure"
            ) from None
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
            # The INSERT holds the writer lock that retention also takes
            # (#12530): never link a blob retention removed, and clear a
            # marker whose blob is still here, since this link keeps it.
            self._restore_if_present(artifact_id)
            if self.get(artifact_id).retention_class.startswith(RETENTION_EXPIRED_PREFIX):
                raise ArtifactExpiredError(
                    f"refusing to reference {artifact_id}: its blob was removed by "
                    "the message retention rule (#12530)"
                )
            if commit:
                self._conn.commit()
        except Exception:
            if commit:
                self._conn.rollback()
            raise

    def is_referenced(self, artifact_id: str) -> bool:
        """True when any column in ``_ALL_REFERENCES`` names the artifact."""
        if self._authority is Authority.PG:
            raise ArtifactStoreError(
                "is_referenced() is not implemented for fleet_comms authority=pg in this slice"
            )
        for table, column in _ALL_REFERENCES:
            row = self._conn.execute(
                f"SELECT 1 FROM {table} WHERE {column} = ? LIMIT 1", (artifact_id,)
            ).fetchone()
            if row:
                return True
        return False

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

    def _prepare_backup_dir(self, backup_dir: Path | None, apply: bool) -> Path | None:
        """Validate and persist the backup directory before any removal."""
        if backup_dir is None:
            return None
        if not apply:
            raise ArtifactStoreError("backup_dir is only meaningful with apply")
        backup_dir = backup_dir.expanduser().resolve()
        if backup_dir.is_relative_to(self.root.resolve()):
            raise ArtifactStoreError("backup_dir must be outside the plane root")
        self._prepare_private_dir(backup_dir)
        # Persist backup_dir's entry in every ancestor up to the root on
        # every apply, before any source can go (#12530 F4). Existence
        # does not prove durability: an earlier failed or interrupted
        # setup can leave directories whose entries were never synced.
        # Any failure raises here, before the first removal.
        child = backup_dir
        while child.parent != child:
            _fsync_directory(child.parent)
            child = child.parent
        return backup_dir

    def _expire_rows(
        self,
        rows: list[sqlite3.Row],
        *,
        single_sql: str,
        params: dict[str, str],
        mtime_floor: float,
        apply: bool,
        backup_dir: Path | None,
        cited: frozenset[str] = frozenset(),
        held_sha: frozenset[str] = frozenset(),
    ) -> dict[str, Any]:
        """Tally candidate rows and, when ``apply``, expire each one.

        ``cited`` (artifact ids) and ``held_sha`` (digests of acknowledged
        cut-short blobs) are never candidates, here or in the locked re-checks.
        """
        by_class: dict[str, dict[str, int]] = {}
        n = dict.fromkeys(
            (
                "candidates", "candidate_bytes", "already_expired", "present_blobs",
                "present_bytes", "removed", "removed_bytes", "recent", "changed",
                "held_cited", "held_cited_bytes", "held_acknowledged",
            ),
            0,
        )
        for row in rows:
            size = int(row["bytes"])
            klass = str(row["retention_class"])
            if str(row["sha256"]) in held_sha:
                n["held_acknowledged"] += 1
                continue
            if str(row["artifact_id"]) in cited:
                n["held_cited"] += 1
                n["held_cited_bytes"] += size
                continue
            present = self.blob_path_for(str(row["sha256"])).is_file()
            if not present and klass.startswith(RETENTION_EXPIRED_PREFIX):
                n["already_expired"] += 1
                continue
            base_class = klass.removeprefix(RETENTION_EXPIRED_PREFIX)
            bucket = by_class.setdefault(
                base_class, {"candidates": 0, "bytes": 0, "present_blobs": 0, "present_bytes": 0}
            )
            n["candidates"] += 1
            n["candidate_bytes"] += size
            bucket["candidates"] += 1
            bucket["bytes"] += size
            if present:
                n["present_blobs"] += 1
                n["present_bytes"] += size
                bucket["present_blobs"] += 1
                bucket["present_bytes"] += size
            if not apply:
                continue
            outcome = self._expire_one_blob(
                str(row["artifact_id"]),
                params,
                mtime_floor,
                backup_dir=backup_dir,
                single_sql=single_sql,
                cited=cited,
                held_sha=held_sha,
            )
            if outcome == "removed":
                n["removed"] += 1
                n["removed_bytes"] += size
            elif outcome == "recent":
                n["recent"] += 1
            elif outcome == "changed":
                n["changed"] += 1
        n["by_class"] = dict(sorted(by_class.items()))
        return n

    def expire_message_blobs(
        self,
        *,
        older_than_days: int = RETENTION_DEFAULT_DAYS,
        grace_seconds: int = RETENTION_GRACE_SECONDS,
        apply: bool = False,
        now: datetime | None = None,
        backup_dir: Path | None = None,
        held_sha: frozenset[str] = frozenset(),
    ) -> RetentionReport:
        """Remove blobs of finished messages older than the cutoff (#12530).

        Dry run unless ``apply``. Only the blob file goes; the ``artifacts``
        row keeps its sha256 and byte count, its class gains
        ``RETENTION_EXPIRED_PREFIX``, and every message row stays. Each removal
        re-evaluates the full rule and the blob's mtime under ``BEGIN
        IMMEDIATE`` (the store's writer lock, which authority writes,
        artifact inserts, dedup reuse and ``reference`` also take) in two
        phases: mark and commit, then re-check and unlink
        (``_expire_one_blob``). Sqlite only.

        ``backup_dir`` (apply only) copies each blob there, sha256-verified,
        inside the locked phase that unlinks it, persists the copy and its
        directory entries, and appends one fsynced ``manifest.jsonl`` line,
        so every removed blob has a durable verified copy (a rolled-back
        removal can leave an extra one). Restoring a copy through
        ``store_bytes`` rewrites the blob and clears the expired marker.

        ``held_sha`` names blobs this run must keep whatever the rule says:
        the cut-short blobs a citation scan acknowledged (#12574). They are
        never candidates, in the tally or in the locked re-checks.
        """
        if older_than_days < 1:
            raise ArtifactStoreError("older_than_days must be at least 1")
        backup_dir = self._prepare_backup_dir(backup_dir, apply)
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
        n = self._expire_rows(
            rows,
            single_sql=_retention_candidate_sql(single=True),
            params=params,
            mtime_floor=moment.timestamp() - max(0, grace_seconds),
            apply=apply,
            backup_dir=backup_dir,
            held_sha=held_sha,
        )
        return RetentionReport(
            applied=apply,
            older_than_days=older_than_days,
            cutoff=cutoff,
            candidates=n["candidates"],
            candidate_bytes=n["candidate_bytes"],
            already_expired=n["already_expired"],
            present_blobs=n["present_blobs"],
            present_bytes=n["present_bytes"],
            removed=n["removed"],
            removed_bytes=n["removed_bytes"],
            skipped_recent_use=n["recent"],
            skipped_changed=n["changed"],
            by_class=n["by_class"],
            backup_dir=str(backup_dir) if backup_dir is not None else None,
            held_acknowledged=n["held_acknowledged"],
        )

    def expire_unreferenced_blobs(
        self,
        *,
        citations: CitationScan,
        older_than_days: int = UNREFERENCED_DEFAULT_DAYS,
        grace_seconds: int = RETENTION_GRACE_SECONDS,
        apply: bool = False,
        now: datetime | None = None,
        backup_dir: Path | None = None,
    ) -> UnreferencedReport:
        """Remove blobs of unreferenced, uncited artifacts past the window (#12574).

        Same two-phase, locked, row-keeping expiry as ``expire_message_blobs``.
        A candidate is named by no column in ``_ALL_REFERENCES``, has an
        allow-listed base class (``UNREFERENCED_EXPIRING_CLASSES``; every other
        class is pinned), is older than ``older_than_days`` and is absent from
        ``citations``, the verified scan of the declared sources
        (``scan_citations``). A citation appearing after that scan is the one
        residual; ``backup_dir`` (required with ``apply``) is the recovery.
        """
        if older_than_days < UNREFERENCED_MIN_DAYS:
            raise ArtifactStoreError(
                f"older_than_days must be at least {UNREFERENCED_MIN_DAYS} for unreferenced artifacts"
            )
        if apply and backup_dir is None:
            raise ArtifactStoreError("unreferenced retention requires backup_dir with apply")
        backup_dir = self._prepare_backup_dir(backup_dir, apply)
        if apply:
            self._refuse_readonly_write("expire_unreferenced_blobs")
        if self._authority is Authority.PG:
            raise ArtifactStoreError(
                "expire_unreferenced_blobs() is not implemented for "
                "fleet_comms authority=pg in this slice"
            )
        moment = now or datetime.now(UTC)
        cutoff = (moment - timedelta(days=older_than_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {"cutoff": cutoff}
        rows = self._conn.execute(_unreferenced_candidate_sql(single=False), params).fetchall()
        if not apply and self._conn.in_transaction:
            self._conn.commit()
        n = self._expire_rows(
            rows,
            single_sql=_unreferenced_candidate_sql(single=True),
            params=params,
            mtime_floor=moment.timestamp() - max(0, grace_seconds),
            apply=apply,
            backup_dir=backup_dir,
            cited=citations.cited,
            held_sha=frozenset(str(entry["sha256"]) for entry in citations.acknowledged_truncated),
        )
        return UnreferencedReport(
            applied=apply,
            older_than_days=older_than_days,
            cutoff=cutoff,
            candidates=n["candidates"],
            candidate_bytes=n["candidate_bytes"],
            held_cited=n["held_cited"],
            held_cited_bytes=n["held_cited_bytes"],
            held_acknowledged=n["held_acknowledged"],
            already_expired=n["already_expired"],
            present_blobs=n["present_blobs"],
            present_bytes=n["present_bytes"],
            removed=n["removed"],
            removed_bytes=n["removed_bytes"],
            skipped_recent_use=n["recent"],
            skipped_changed=n["changed"],
            by_class=n["by_class"],
            sources=[dict(entry) for entry in citations.coverage],
            acknowledged_truncated=[dict(entry) for entry in citations.acknowledged_truncated],
            backup_dir=str(backup_dir) if backup_dir is not None else None,
        )

    def _expire_one_blob(
        self,
        artifact_id: str,
        params: dict[str, str],
        mtime_floor: float,
        *,
        single_sql: str,
        cited: frozenset[str] = frozenset(),
        held_sha: frozenset[str] = frozenset(),
        backup_dir: Path | None = None,
    ) -> str:
        """Expire one candidate in two locked phases (#12530).

        Phase 1 re-checks the rule and the grace window, marks the row
        expired and commits while the blob is still readable. Phase 2
        re-checks under the lock again, backs the blob up and unlinks it; it
        writes no row, so a crash at any point leaves either readable bytes or
        a durable expired marker, never an unmarked row without bytes. A row
        that stops qualifying between the phases (a reviver, a new reference,
        a touched blob) gets its class restored if its blob is still there.

        #12573 AC-02: finish_delivery refuses an expired-marked acknowledgment
        artifact, even between these phases while its blob is present. Its
        marker check and delivery update share one BEGIN IMMEDIATE transaction,
        so an acknowledgment cannot revive a marked blob. An acknowledgment
        committed before phase 1 instead makes this artifact ineligible.

        Returns ``removed``, ``recent`` (blob touched inside the grace
        window) or ``changed`` (no longer a candidate).
        """
        locked = {**params, "artifact_id": artifact_id}
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            row = self._candidate_row(single_sql, locked, cited, held_sha)
            outcome = self._grace_outcome(row, mtime_floor)
            if outcome is None:
                klass = str(row["retention_class"])
                if not klass.startswith(RETENTION_EXPIRED_PREFIX):
                    self._conn.execute(
                        "UPDATE artifacts SET retention_class = ? WHERE artifact_id = ?",
                        (RETENTION_EXPIRED_PREFIX + klass, artifact_id),
                    )
        except Exception:
            self._conn.rollback()
            raise
        self._conn.commit()
        if outcome is not None:
            return outcome
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            row = self._candidate_row(single_sql, locked, cited, held_sha)
            outcome = self._grace_outcome(row, mtime_floor)
            if outcome is None and not str(row["retention_class"]).startswith(
                RETENTION_EXPIRED_PREFIX
            ):
                outcome = "changed"
            if outcome is not None:
                self._restore_if_present(artifact_id)
            else:
                path = self.blob_path_for(str(row["sha256"]))
                if backup_dir is not None:
                    self._back_up_blob(path, row, backup_dir)
                path.unlink(missing_ok=True)
        except Exception:
            self._conn.rollback()
            raise
        self._conn.commit()
        return outcome or "removed"

    def _candidate_row(
        self,
        single_sql: str,
        locked: dict[str, str],
        cited: frozenset[str],
        held_sha: frozenset[str] = frozenset(),
    ) -> sqlite3.Row | None:
        """Re-run the rule for one artifact; a cited or acknowledged artifact is never one."""
        row = self._conn.execute(single_sql, locked).fetchone()
        if row is not None and (str(row["artifact_id"]) in cited or str(row["sha256"]) in held_sha):
            return None
        return row

    def _grace_outcome(self, row: sqlite3.Row | None, mtime_floor: float) -> str | None:
        """``changed`` for a non-candidate, ``recent`` inside grace, else None."""
        if row is None:
            return "changed"
        try:
            if self.blob_path_for(str(row["sha256"])).stat().st_mtime > mtime_floor:
                return "recent"
        except FileNotFoundError:
            pass
        return None

    def _restore_if_present(self, artifact_id: str) -> None:
        """Clear the expired marker of a row whose blob is still on disk."""
        row = self._conn.execute(
            "SELECT sha256, retention_class FROM artifacts WHERE artifact_id = ?",
            (artifact_id,),
        ).fetchone()
        if row is None:
            return
        klass = str(row["retention_class"])
        if klass.startswith(RETENTION_EXPIRED_PREFIX) and self.blob_path_for(
            str(row["sha256"])
        ).is_file():
            self._conn.execute(
                "UPDATE artifacts SET retention_class = ? WHERE artifact_id = ?",
                (klass.removeprefix(RETENTION_EXPIRED_PREFIX), artifact_id),
            )

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
        # The rename and any new shard directory are directory entries:
        # persist both before the source can go (#12530 F4).
        _fsync_directory(dest.parent)
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
        _fsync_directory(backup_dir)

    def scan_citations(
        self,
        sources: CitationSources,
        *,
        now: datetime | None = None,
        accept_truncated: frozenset[str] = frozenset(),
    ) -> CitationScan:
        """Verify and scan every declared citation source (#12574).

        Returns the artifacts any source names (by ``artifact_<id>`` or by
        sha256) plus per-source coverage. It raises ``ArtifactStoreError``
        unless EVERY source is present, non-empty for its kind, fresh and
        readable end to end, so the unreferenced rule cannot start on a
        partial or blind scan. Coverage is evidence; the refusal is the
        protection. Sources: the store itself (message text, message-linked
        blobs), the tasks directory, the repository docs tree, a GitHub dump
        (``_scan_github``), a citation export file and the batch-state tree.
        The batch-state scan excludes this store's own root: its artifact
        index and unlinked blobs are not outside citations. Store citations
        are scanned by ``_scan_store`` instead; coverage names the exclusion.

        Compressed content cut short refuses, with one exception:
        ``accept_truncated`` names message-linked blobs (by full sha256) whose
        acknowledged cut is honoured (``_acknowledge_cut``); every name must
        be used, or the scan refuses.
        """
        if self._authority is Authority.PG:
            raise ArtifactStoreError(
                "scan_citations() is not implemented for fleet_comms authority=pg in this slice"
            )
        known = self._conn.execute("SELECT artifact_id, sha256 FROM artifacts").fetchall()
        state = _ScanState(
            frozenset(str(r["artifact_id"]).encode("ascii") for r in known),
            {str(r["sha256"]).encode("ascii"): str(r["artifact_id"]) for r in known},
        )
        acknowledged: dict[str, dict[str, Any]] = {}
        coverage = [
            self._scan_store(state, accept_truncated, acknowledged),
            self._scan_tree("tasks", sources.tasks_dir, state, required_suffix=".json", inventories=True),
            self._scan_tree("docs", sources.docs_dir, state, required_suffix=".md"),
            self._scan_github(sources.github_dump, state, now or datetime.now(UTC)),
            self._scan_export(sources.citation_export, state),
            self._scan_tree(
                "batch_state", sources.batch_state_dir, state,
                inventories=True, excluded_store_root=self.root,
            ),
        ]
        if self._conn.in_transaction:
            self._conn.commit()
        return CitationScan(
            frozenset(state.cited), tuple(coverage), tuple(acknowledged[sha] for sha in sorted(acknowledged))
        )

    def _scan_store(
        self,
        state: _ScanState,
        accept_truncated: frozenset[str],
        acknowledged: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Scan message text and the blobs of message-linked artifacts.

        A blob that retention already removed (its row carries the expired
        marker) has nothing left to cite from; any other missing or unreadable
        linked blob is an incomplete scan and refuses the run. So does a
        linked blob cut short, unless ``accept_truncated`` acknowledges it
        (``_acknowledge_cut`` fills ``acknowledged``). An acknowledgement that
        matched no linked blob refuses the run.
        """
        records = 0
        for row in self._conn.execute("SELECT body_inline, metadata_json FROM comms_messages"):
            records += 1
            for text in (row["body_inline"], row["metadata_json"]):
                if text:
                    state.feed(str(text).encode("utf-8"))
        linked = self._conn.execute(
            """SELECT sha256, retention_class FROM artifacts WHERE artifact_id IN (
                   SELECT artifact_id FROM message_artifacts
                   UNION SELECT body_artifact_id FROM comms_messages
                         WHERE body_artifact_id IS NOT NULL)"""
        ).fetchall()
        files = scanned = expired = 0
        for row in linked:
            sha = str(row["sha256"])
            path = self.blob_path_for(sha)
            try:
                with open(path, "rb") as handle:
                    hashed = _HashingReader(handle)
                    try:
                        scanned += state.feed_stream(hashed)
                    except _CutShort as cut:
                        scanned += self._acknowledge_cut(cut, sha, hashed, state, accept_truncated, acknowledged)
            except FileNotFoundError as exc:
                if str(row["retention_class"]).startswith(RETENTION_EXPIRED_PREFIX):
                    expired += 1
                    continue
                raise ArtifactStoreError(
                    f"citation source store: linked blob {path} is missing, so it cannot be scanned"
                ) from exc
            except OSError as exc:
                raise ArtifactStoreError(f"citation scan cannot read blob {path}: {exc}") from exc
            files += 1
        unused = sorted(accept_truncated - acknowledged.keys())
        if unused:
            raise ArtifactStoreError(
                "citation source store: --accept-truncated-sha256 names no message-linked blob "
                f"that this scan found cut short: {', '.join(unused)}; refusing"
            )
        return {
            "source": "store",
            "messages": records,
            "blobs": files,
            "blobs_expired": expired,
            "bytes": scanned,
            "acknowledged_truncated": len(acknowledged),
        }

    @staticmethod
    def _acknowledge_cut(
        cut: _CutShort,
        sha: str,
        hashed: _HashingReader,
        state: _ScanState,
        accept_truncated: frozenset[str],
        acknowledged: dict[str, dict[str, Any]],
    ) -> int:
        """Honour an acknowledged cut of one linked blob, or refuse (#12574).

        Only a premature end of the blob's own bytes (depth 1) is waived, and
        only after every byte the decoders could produce was scanned; corrupt
        data, unsupported content, trailing data and the size cap raise
        elsewhere and are never waived. The sha256 of the bytes actually
        scanned (read to the end) must equal both the acknowledged digest and
        the blob's address. Returns the decoded bytes scanned.
        """
        if sha not in accept_truncated:
            raise ArtifactStoreError(f"citation source store: linked blob {sha}: {cut}") from cut
        if cut.depth != 1:
            raise ArtifactStoreError(
                f"citation source store: linked blob {sha} is complete but holds content cut short "
                f"inside it ({cut}); an acknowledgement covers only the end of the blob itself"
            ) from cut
        while hashed.read(_STREAM_READ):
            pass
        if not hashed.sequential:
            raise ArtifactStoreError(
                f"citation source store: linked blob {sha} was not read in one pass; "
                "the acknowledgement cannot be checked against the bytes scanned; refusing"
            ) from cut
        if hashed.digest.hexdigest() != sha:
            raise ArtifactStoreError(
                f"citation source store: the bytes scanned for linked blob {sha} hash to "
                f"{hashed.digest.hexdigest()}; the acknowledgement does not match; refusing"
            )
        acknowledged[sha] = {
            "sha256": sha,
            "format": cut.fmt,
            "blob_bytes": hashed.size,
            "decoded_bytes": state.plain_bytes,
            "stream_offset": cut.stream_offset,
            "truncation_offset": cut.truncation_offset,
        }
        return state.plain_bytes

    @staticmethod
    def _scan_export(path: Path, state: _ScanState) -> dict[str, Any]:
        """Scan the caller's citation export as content, without a format schema."""
        try:
            if not stat.S_ISREG(os.lstat(path).st_mode):
                raise ArtifactStoreError(f"citation source export: {path} is not a regular file")
            with open(path, "rb") as handle:
                size = state.feed_stream(handle)
        except OSError as exc:
            raise ArtifactStoreError(f"citation source export: cannot read {path}: {exc}") from exc
        if size == 0:
            raise ArtifactStoreError(f"citation source export: {path} is empty")
        return {"source": "export", "path": str(path), "files": 1, "bytes": size}

    @staticmethod
    def _scan_tree(
        name: str,
        root: Path,
        state: _ScanState,
        *,
        required_suffix: str | None = None,
        inventories: bool = False,
        excluded_store_root: Path | None = None,
    ) -> dict[str, Any]:
        """Scan every file under ``root`` end to end, or raise.

        Complete or refused: a symlink, a non-regular entry, an unreadable
        or vanished file or directory, or an empty tree raises. If given,
        ``required_suffix`` must occur. Only ``excluded_store_root`` may be
        skipped; its path and reason are reported. With ``inventories``, the blob-path
        listings inside the dispatcher's generated checkout inventories are
        not citations (``_INVENTORY_ENTRY``); they are counted in the coverage.
        """

        def fail_walk(exc: OSError) -> None:
            raise ArtifactStoreError(f"citation source {name}: cannot list {exc.filename}: {exc}")

        root = Path(root)
        if root.is_symlink():
            raise ArtifactStoreError(f"citation source {name}: {root} is a symlink")
        if not root.is_dir():
            raise ArtifactStoreError(f"citation source {name}: {root} is not a directory")
        excluded_store_root = excluded_store_root.resolve() if excluded_store_root is not None else None
        if excluded_store_root is not None and root.resolve().is_relative_to(excluded_store_root):
            raise ArtifactStoreError(
                f"citation source {name}: {root} is inside the artifact store; "
                "refusing an incompletely scanned tree"
            )
        excluded_subtrees = []
        files = required = total = listings = 0
        digest = hashlib.sha256()
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False, onerror=fail_walk):
            dirnames.sort()
            for dirname in dirnames[:]:
                child = Path(dirpath) / dirname
                if child.is_symlink():
                    raise ArtifactStoreError(
                        f"citation source {name}: {dirpath}/{dirname} is a symlink; "
                        "refusing an incompletely scanned tree"
                    )
                if excluded_store_root is not None and child.resolve() == excluded_store_root:
                    dirnames.remove(dirname)
                    excluded_subtrees.append({"path": str(excluded_store_root), "reason": "artifact_store"})
            for filename in sorted(filenames):
                path = Path(dirpath) / filename
                inventory = inventories and filename in _INVENTORY_SNAPSHOT_FILES
                try:
                    if not stat.S_ISREG(os.lstat(path).st_mode):
                        raise ArtifactStoreError(
                            f"citation source {name}: {path} is not a regular file; "
                            "refusing an incompletely scanned tree"
                        )
                    with open(path, "rb") as handle:
                        if inventory:
                            size, ignored = state.feed_inventory(handle)
                            listings += ignored
                        else:
                            size = state.feed_stream(handle)
                except FileNotFoundError as exc:
                    raise ArtifactStoreError(
                        f"citation source {name}: {path} vanished during the scan; run again"
                    ) from exc
                except OSError as exc:
                    raise ArtifactStoreError(
                        f"citation source {name}: cannot read {path}: {exc}"
                    ) from exc
                files += 1
                total += size
                required += required_suffix is None or path.suffix == required_suffix
                digest.update(f"{path.relative_to(root)}\0{size}\n".encode())
        if required < 1:
            expected = f"no {required_suffix} file" if required_suffix is not None else "no file"
            raise ArtifactStoreError(
                f"citation source {name}: {root} holds {expected}; "
                "refusing an empty or wrong tree"
            )
        return {
            "source": name,
            "path": str(root),
            "files": files,
            "bytes": total,
            "inventory_listings_ignored": listings,
            "excluded_subtrees": excluded_subtrees,
            "digest": digest.hexdigest(),
        }

    @staticmethod
    def _scan_github(path: Path, state: _ScanState, now: datetime) -> dict[str, Any]:
        """Scan a GitHub dump: a ``.jsonl`` of one JSON object per line.

        Line 1 is ``{"kind": "header", "fetched_at": "<ISO-Z>"}``, no older
        than 24 hours. Then one record per line whose ``kind`` is ``issue``,
        ``pull_request``, ``issue_comment`` or ``pr_review_comment``; each
        kind must occur at least once. The last line is
        ``{"kind": "footer", "records": N}`` with N the record count, which
        exposes a truncated write. Any other line is a failure.
        """
        name = "github"
        counts: dict[str, int] = {}
        header: dict[str, Any] | None = None
        footer: dict[str, Any] | None = None
        total = 0
        try:
            handle = open(path, "rb")  # noqa: SIM115 - closed in the finally below
        except OSError as exc:
            raise ArtifactStoreError(f"citation source {name}: cannot open {path}: {exc}") from exc
        try:
            for number, line in enumerate(handle, 1):
                total += len(line)
                if not line.strip():
                    continue
                if footer is not None:
                    raise ArtifactStoreError(f"citation source {name}: line {number} follows the footer")
                try:
                    record = json.loads(line)
                except ValueError as exc:
                    raise ArtifactStoreError(
                        f"citation source {name}: line {number} is not JSON: {exc}"
                    ) from exc
                kind = record.get("kind") if isinstance(record, dict) else None
                if header is None:
                    if kind != "header":
                        raise ArtifactStoreError(f"citation source {name}: first line is not the header")
                    header = record
                elif kind == "footer":
                    footer = record
                elif kind in GITHUB_DUMP_KINDS:
                    counts[kind] = counts.get(kind, 0) + 1
                    state.feed(line)
                else:
                    raise ArtifactStoreError(
                        f"citation source {name}: line {number} has unknown kind {kind!r}"
                    )
        except OSError as exc:
            raise ArtifactStoreError(f"citation source {name}: cannot read {path}: {exc}") from exc
        finally:
            handle.close()
        if header is None or footer is None:
            raise ArtifactStoreError(f"citation source {name}: header or footer missing (truncated?)")
        try:
            fetched = datetime.strptime(str(header.get("fetched_at")), "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=UTC
            )
        except ValueError as exc:
            raise ArtifactStoreError(f"citation source {name}: header has no valid fetched_at") from exc
        age = (now - fetched).total_seconds()
        if age > GITHUB_DUMP_MAX_AGE_SECONDS or age < -300:
            raise ArtifactStoreError(
                f"citation source {name}: dump fetched_at {header['fetched_at']} is not within "
                f"{GITHUB_DUMP_MAX_AGE_SECONDS // 3600} h of now"
            )
        missing = sorted(GITHUB_DUMP_KINDS - set(counts))
        if missing:
            raise ArtifactStoreError(f"citation source {name}: no records of kind {missing}")
        if footer.get("records") != sum(counts.values()):
            raise ArtifactStoreError(
                f"citation source {name}: footer says {footer.get('records')} records, "
                f"read {sum(counts.values())}"
            )
        return {
            "source": name,
            "path": str(path),
            "records": dict(sorted(counts.items())),
            "bytes": total,
            "fetched_at": header["fetched_at"],
        }

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
