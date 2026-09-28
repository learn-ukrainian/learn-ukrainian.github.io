"""Honest, metadata-only identity for the mutable sources database."""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from pathlib import Path
from typing import Any

SOURCES_DB_META_SCHEME = "file-meta-v1"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def journal_mode_from_header(path: Path) -> str | None:
    """SQLite header bytes 18-19: 2,2 means WAL; 1,1 legacy journal."""
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


def sources_db_meta_identity(path: Path, journal_mode_fallback: str | None = None) -> tuple[str, dict[str, Any]]:
    """Return the file-meta-v1 digest and metadata without reading the DB body."""
    path = Path(path)
    stat = path.stat()
    wal_bytes, wal_mtime_ns = 0, None
    with suppress(OSError):
        wal_stat = Path(f"{path}-wal").stat()
        wal_bytes, wal_mtime_ns = wal_stat.st_size, wal_stat.st_mtime_ns
    metadata = {
        "scheme": SOURCES_DB_META_SCHEME,
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "journal_mode": journal_mode_from_header(path) or journal_mode_fallback,
        "wal_bytes": wal_bytes,
        "wal_mtime_ns": wal_mtime_ns,
    }
    return hashlib.sha256(_canonical(metadata)).hexdigest(), metadata
