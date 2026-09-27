"""Content-addressed, local cache for raw ULIF DictUA responses."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

RAW_TABLE = "ulif_dictua_raw_responses"
RAW_SCHEMA = """
CREATE TABLE IF NOT EXISTS ulif_dictua_raw_responses (
    response_sha256 TEXT PRIMARY KEY,
    body BLOB NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'text/html; charset=utf-8',
    stored_at TEXT NOT NULL DEFAULT ''
)
"""


def _primary_checkout() -> Path:
    root = Path(__file__).resolve().parents[2]
    git_marker = root / ".git"
    if git_marker.is_file():
        git_dir = Path(git_marker.read_text(encoding="utf-8").strip().removeprefix("gitdir: "))
        common = git_dir / "commondir"
        if common.exists():
            return (git_dir / common.read_text(encoding="utf-8").strip()).resolve().parent
    return root


def cache_path(source_db: str | Path | None = None) -> Path:
    """Return the shared primary data cache, or a fixture DB's sibling cache.

    ``LU_ULIF_RAW_CACHE`` always wins. Explicit source DB paths permit isolated
    fixture runs without touching the primary checkout's live cache.
    """
    if override := os.environ.get("LU_ULIF_RAW_CACHE"):
        return Path(override).expanduser().resolve()
    if source_db is not None:
        return Path(source_db).resolve().parent / "lexicon/cache/ulif_raw.sqlite"
    return _primary_checkout() / "data/lexicon/cache/ulif_raw.sqlite"


def open_cache(path: str | Path | None = None, *, create: bool = True) -> sqlite3.Connection:
    """Open the cache; read paths fail if migration has not created it."""
    target = Path(path) if path is not None else cache_path()
    if create:
        target.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(target, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(RAW_SCHEMA)
        conn.commit()
    else:
        conn = sqlite3.connect(f"file:{target.resolve()}?mode=ro", uri=True)
    return conn


def put(
    sha: str,
    body: bytes,
    content_type: str = "text/html; charset=utf-8",
    stored_at: str = "",
    *,
    path: str | Path | None = None,
    conn: sqlite3.Connection | None = None,
) -> None:
    """Store one verified blob; an existing digest is immutable.

    An owned connection commits before returning. A borrowed connection is
    committed by its caller, allowing the offline migration to batch writes.
    """
    if len(sha) != 64 or hashlib.sha256(body).hexdigest() != sha:
        raise ValueError(f"ULIF raw response hash mismatch: {sha}")
    owned = conn is None
    if owned:
        conn = open_cache(path)
    assert conn is not None
    try:
        conn.execute(
            f"INSERT OR IGNORE INTO {RAW_TABLE} (response_sha256, body, content_type, stored_at) VALUES (?, ?, ?, ?)",
            (sha, body, content_type, stored_at),
        )
        row = conn.execute(f"SELECT body FROM {RAW_TABLE} WHERE response_sha256 = ?", (sha,)).fetchone()
        if row is None or bytes(row[0]) != body:
            raise ValueError(f"ULIF raw response hash mismatch: {sha}")
        if owned:
            conn.commit()
    finally:
        if owned:
            conn.close()


def get(sha: str, *, path: str | Path | None = None, conn: sqlite3.Connection | None = None) -> bytes | None:
    """Read a body and reject corruption instead of returning untrusted bytes."""
    if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        raise ValueError(f"Invalid ULIF raw response SHA-256: {sha}")
    owned = conn is None
    if owned:
        conn = open_cache(path, create=False)
    assert conn is not None
    try:
        row = conn.execute(f"SELECT body FROM {RAW_TABLE} WHERE response_sha256 = ?", (sha,)).fetchone()
        if row is None:
            return None
        body = bytes(row[0])
        if hashlib.sha256(body).hexdigest() != sha:
            raise ValueError(f"ULIF raw response hash mismatch: {sha}")
        return body
    finally:
        if owned:
            conn.close()


def resolve_ref(ref: str, *, path: str | Path | None = None) -> bytes | None:
    """Verify a reference and every nested reference in a JSON manifest."""
    if not ref.startswith("sha256:"):
        return None
    visiting: set[str] = set()

    def resolve(sha: str) -> bytes | None:
        if sha in visiting:
            raise ValueError(f"ULIF raw response manifest cycle: {sha}")
        visiting.add(sha)
        try:
            body = get(sha, path=path)
            if body is None:
                return None
            try:
                manifest = json.loads(body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                return body
            if isinstance(manifest, dict) and (
                not manifest
                or any(isinstance(value, str) and value.startswith("sha256:") for value in manifest.values())
            ):
                for nested in manifest.values():
                    if not isinstance(nested, str) or not nested.startswith("sha256:"):
                        raise ValueError(f"Invalid ULIF raw response manifest: {sha}")
                for nested in manifest.values():
                    if resolve(nested.removeprefix("sha256:")) is None:
                        return None
            return body
        finally:
            visiting.remove(sha)

    return resolve(ref.removeprefix("sha256:"))
