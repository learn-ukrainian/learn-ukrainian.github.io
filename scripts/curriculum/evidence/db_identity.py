"""Metadata identity of ``data/sources.db``: the one implementation, stdlib-only.

``data/sources.db`` is a multi-gigabyte WAL database written continuously by
the ULIF walk. Hashing its body is a multi-second full read and yields a digest
that races the writer (#8527, #8683). This module is the honest alternative:
file *metadata* (size, mtime, journal mode, WAL size and mtime) under the
scheme ``file-meta-v1``. It is an identity of the file's state, never a
content hash. It stays import-light so the sources MCP server and the local
MCP client can both use it without pulling in the evidence stack.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from pathlib import Path
from typing import Any

from . import codes

SOURCES_DB_META_SCHEME = "file-meta-v1"


def canonical_bytes(value: Any) -> bytes:
    # ensure_ascii=False keeps Ukrainian bytes readable; bytes values raise (no cited table has a BLOB).
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def journal_mode_from_header(path: Path) -> str | None:
    """SQLite header bytes 18-19: 2,2 means WAL; 1,1 legacy (rollback) journal. None when unreadable."""
    try:
        with Path(path).open("rb") as stream:
            header = stream.read(20)
    except OSError:
        return None
    if len(header) < 20 or header[:16] != b"SQLite format 3\x00":
        return None
    if header[18] == 2 and header[19] == 2:
        return "wal"
    if header[18] == 1 and header[19] == 1:
        return "delete"
    return "unknown"


def sources_db_meta_identity(path: Path, *, fallback_journal_mode: str | None = None) -> tuple[str, dict]:
    """Cheap, honestly labelled identity of the sources.db file: metadata only, never its body.

    The review receipt ledger and the sources MCP ``mcp_server_identity`` tool
    both record this. It is not a content hash: hashing the multi-gigabyte
    file per process is what raced the ULIF walk (#8527). The content evidence
    of a sources.db read is the receipt's full stored result (rows-v2). The
    digest is the sha256 of the canonical metadata JSON so readers expecting a
    64-hex string stay valid. ``fallback_journal_mode`` is the pinned
    session's PRAGMA answer, used when the 20-byte header is unreadable.
    """
    path = Path(path)
    try:
        stat = path.stat()
    except OSError as exc:
        raise FileNotFoundError(f"{codes.SOURCE_UNAVAILABLE}: {str(path)!r}") from exc
    wal_bytes, wal_mtime_ns = 0, None
    with suppress(OSError):
        wal_stat = Path(f"{path}-wal").stat()
        wal_bytes, wal_mtime_ns = wal_stat.st_size, wal_stat.st_mtime_ns
    metadata = {
        "scheme": SOURCES_DB_META_SCHEME,
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "journal_mode": journal_mode_from_header(path) or fallback_journal_mode,
        "wal_bytes": wal_bytes,
        "wal_mtime_ns": wal_mtime_ns,
    }
    return hashlib.sha256(canonical_bytes(metadata)).hexdigest(), metadata
