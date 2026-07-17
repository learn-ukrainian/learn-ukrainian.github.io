"""Hard guard: network workers cannot open ``sources.db`` (#5230 PR3).

Spec §Phase 5: the VPS runner cannot construct or open sources.db. This module
provides a process-local flag plus path refusal used by network-side entry points.

Hardening (PR #5365 review delta):
- SQLite URI / query-string forms are parsed with URI semantics before checks
- Case-insensitive substring match on the resolved path target
- Inode comparison against the configured ``sources.db`` path (hardlink defense)
- SQLite authorizer denying ``ATTACH`` of any sources.db on network connections
"""

from __future__ import annotations

import contextlib
import os
import sqlite3
import threading
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote

_ENV_FLAG = "LEXICON_RUNNER_NETWORK_WORKER"
_SOURCES_DB_ENV = "LEXICON_SOURCES_DB"
_SOURCES_DB_NAME = "sources.db"
_tls = threading.local()


class SourcesDbForbiddenError(RuntimeError):
    """Raised when a network worker attempts to open or construct sources.db."""


def _flag_active() -> bool:
    if getattr(_tls, "active", False):
        return True
    return os.environ.get(_ENV_FLAG, "").strip() in {"1", "true", "TRUE", "yes", "YES"}


def is_network_worker() -> bool:
    return _flag_active()


def configured_sources_db_path() -> Path:
    """Return the configured corpus ``sources.db`` path.

    Honours ``LEXICON_SOURCES_DB`` when set; otherwise the repo-default
    ``data/sources.db`` (resolved against the process cwd).
    """
    override = os.environ.get(_SOURCES_DB_ENV, "").strip()
    if override:
        return Path(override)
    return Path("data") / _SOURCES_DB_NAME


def _sqlite_uri_path_target(path: Path | str) -> str:
    """Extract the filesystem path SQLite would open from a URI or plain path.

    Implements the subset of SQLite URI filename semantics needed for the guard
    (https://www.sqlite.org/uri.html): ``file:`` scheme, authority forms, and
    stripping of query string / fragment. Non-``file:`` strings are treated as
    ordinary filenames; a bare ``?…`` suffix (common accidental URI form) is
    still stripped so ``sources.db?mode=ro`` resolves to ``sources.db``.
    """
    raw = str(path)
    lower = raw.lower()
    if lower.startswith("file:"):
        rest = raw[5:]
        if rest.startswith("//"):
            # file:///abs, file://localhost/abs, file://host/path
            without = rest[2:]
            if without.startswith("/"):
                path_part = without
            else:
                slash = without.find("/")
                path_part = without[slash:] if slash >= 0 else without
        else:
            # file:/abs or file:relative
            path_part = rest
        for sep in ("?", "#"):
            if sep in path_part:
                path_part = path_part.split(sep, 1)[0]
        return unquote(path_part)

    # Ordinary filename. Strip accidental query/fragment suffixes so
    # ``sources.db?mode=ro`` is recognized even without a file: scheme.
    plain = raw
    for sep in ("?", "#"):
        if sep in plain:
            plain = plain.split(sep, 1)[0]
    return plain


def _looks_like_sources_db(path: Path | str) -> bool:
    """True when *path* names sources.db (URI-aware, case-insensitive)."""
    target = _sqlite_uri_path_target(path)
    target_lower = target.lower().replace("\\", "/")
    if _SOURCES_DB_NAME in target_lower:
        return True
    # Basename of the stripped target (handles empty/edge URI forms).
    name = Path(target).name.lower()
    if name == _SOURCES_DB_NAME:
        return True
    # Resolved absolute path (follows symlinks when the path exists).
    try:
        candidate = Path(target)
        # Only resolve when it doesn't invent a non-existent absolute path for
        # pure URI strings that are already absolute after unquote.
        resolved = candidate.resolve()
        resolved_s = str(resolved).lower().replace("\\", "/")
        if _SOURCES_DB_NAME in resolved_s or resolved.name.lower() == _SOURCES_DB_NAME:
            return True
    except OSError:
        pass
    return False


def _same_inode(a: Path, b: Path) -> bool:
    try:
        if not a.is_file() or not b.is_file():
            return False
        sa = a.stat()
        sb = b.stat()
        return sa.st_ino == sb.st_ino and sa.st_dev == sb.st_dev
    except OSError:
        return False


def _inode_matches_configured_sources(path: Path | str) -> bool:
    """True when *path* is a hardlink (same inode) to the configured sources.db."""
    target = _sqlite_uri_path_target(path)
    try:
        candidate = Path(target).resolve()
    except OSError:
        return False
    configured = configured_sources_db_path()
    try:
        configured_resolved = configured.resolve()
    except OSError:
        return False
    return _same_inode(candidate, configured_resolved)


def assert_not_sources_db(path: Path | str) -> None:
    """Refuse any path that is or ends with sources.db when the guard is active.

    Always refuses an explicit ``sources.db`` basename (including URI/query forms
    and hardlinks to the configured sources.db) under the network-worker role.
    When the guard is inactive this is a no-op so offline workers may open
    sources for Map/Reduce enrichment.
    """
    if not _flag_active():
        return
    if _looks_like_sources_db(path) or _inode_matches_configured_sources(path):
        raise SourcesDbForbiddenError(
            f"network workers cannot open sources.db (refused path={path})"
        )


def install_network_authorizer(
    conn: sqlite3.Connection,
    *,
    force: bool = False,
) -> None:
    """Deny ATTACH of sources.db on a network-side SQLite connection.

    Applied by every network-side connection factory after ``sqlite3.connect``.
    When *force* is False (default), installs only while the network-worker
    guard is active so offline openers are unaffected. Network-only factories
    (e.g. ``NetworkCache``) pass ``force=True``.
    """
    if not force and not _flag_active():
        return

    def _authorizer(
        action: int,
        arg1: str | None,
        _arg2: str | None,
        _dbname: str | None,
        _source: str | None,
    ) -> int:
        if action == sqlite3.SQLITE_ATTACH:
            target = arg1 if arg1 is not None else ""
            if _looks_like_sources_db(target) or _inode_matches_configured_sources(target):
                return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    conn.set_authorizer(_authorizer)


def apply_network_connection_guards(
    conn: sqlite3.Connection,
    path: Path | str | None = None,
    *,
    force_authorizer: bool = False,
) -> sqlite3.Connection:
    """Path assert (optional) + ATTACH authorizer for a network-side connection."""
    if path is not None:
        assert_not_sources_db(path)
    install_network_authorizer(conn, force=force_authorizer)
    return conn


@contextlib.contextmanager
def guard_network_worker() -> Iterator[None]:
    """Activate the process/thread-local network-worker sources.db ban."""
    prev_tls = getattr(_tls, "active", False)
    prev_env = os.environ.get(_ENV_FLAG)
    _tls.active = True
    os.environ[_ENV_FLAG] = "1"
    try:
        yield
    finally:
        _tls.active = prev_tls
        if prev_env is None:
            os.environ.pop(_ENV_FLAG, None)
        else:
            os.environ[_ENV_FLAG] = prev_env


def open_sources_db_refused(path: Path | str) -> None:
    """Explicit entry used by network workers / tests to prove the hard guard.

    Always raises when path names sources.db (URI/inode-aware), regardless of
    ambient flag — the network worker must call this before any SQLite open of
    corpus sources.
    """
    if _looks_like_sources_db(path) or _inode_matches_configured_sources(path):
        raise SourcesDbForbiddenError(
            f"network workers cannot open sources.db (refused path={path})"
        )
    # Non-sources paths are still blocked when the ambient network role is set
    # and something tries the open_sources_ro helper — that helper consults the flag.
    if _flag_active():
        # Allow non-sources opens only through explicit network-cache APIs.
        return
