"""Read-only SQLite openers for immutable side databases and sources."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path


def file_sha256(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def open_immutable_ro(
    path: Path,
    *,
    cache_kib: int = 2000,
    mmap_size: int = 0,
) -> sqlite3.Connection:
    """Open a completed side DB for workers: mode=ro, immutable, query_only.

    Bounded page cache; large mmap disabled so workers do not pin giant mappings.
    """
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    uri = f"file:{resolved.as_posix()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.execute("PRAGMA query_only = ON")
    conn.execute(f"PRAGMA cache_size = -{int(cache_kib)}")
    conn.execute(f"PRAGMA mmap_size = {int(mmap_size)}")
    conn.row_factory = sqlite3.Row
    return conn


def open_sources_ro(path: Path) -> sqlite3.Connection:
    """Open sources.db read-only (mutable file; no immutable=1).

    Network workers are hard-refused (PR3 / spec §Phase 5).
    """
    from scripts.lexicon.runner.sources_guard import assert_not_sources_db

    assert_not_sources_db(path)
    resolved = path.resolve()
    uri = f"file:{resolved.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.execute("PRAGMA query_only = ON")
    conn.row_factory = sqlite3.Row
    return conn


def checkpoint_and_hash(conn: sqlite3.Connection, path: Path) -> str:
    """Flush the DB and return a content hash of the file.

    WAL checkpoint is best-effort (side builders often use ``journal_mode=OFF``).
    """
    import contextlib

    try:
        mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).casefold()
    except sqlite3.Error:
        mode = ""
    if mode == "wal":
        with contextlib.suppress(sqlite3.OperationalError):
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.commit()
    return file_sha256(path)
