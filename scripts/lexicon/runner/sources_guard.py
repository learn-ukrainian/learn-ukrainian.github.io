"""Hard guard: network workers cannot open ``sources.db`` (#5230 PR3).

Spec §Phase 5: the VPS runner cannot construct or open sources.db. This module
provides a process-local flag plus path refusal used by network-side entry points.
"""

from __future__ import annotations

import contextlib
import os
import threading
from collections.abc import Iterator
from pathlib import Path

_ENV_FLAG = "LEXICON_RUNNER_NETWORK_WORKER"
_tls = threading.local()


class SourcesDbForbiddenError(RuntimeError):
    """Raised when a network worker attempts to open or construct sources.db."""


def _flag_active() -> bool:
    if getattr(_tls, "active", False):
        return True
    return os.environ.get(_ENV_FLAG, "").strip() in {"1", "true", "TRUE", "yes", "YES"}


def is_network_worker() -> bool:
    return _flag_active()


def assert_not_sources_db(path: Path | str) -> None:
    """Refuse any path that is or ends with sources.db when the guard is active.

    Always refuses an explicit ``sources.db`` basename under the network-worker
    role. When the guard is inactive this is a no-op so offline workers may open
    sources for Map/Reduce enrichment.
    """
    if not _flag_active():
        return
    resolved = Path(path)
    name = resolved.name
    # Also catch URI forms like file:/.../sources.db?mode=ro
    s = str(path)
    if name == "sources.db" or s.rstrip("/").endswith("sources.db") or "/sources.db?" in s:
        raise SourcesDbForbiddenError(
            f"network workers cannot open sources.db (refused path={path})"
        )


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

    Always raises when path names sources.db, regardless of ambient flag — the
    network worker must call this before any SQLite open of corpus sources.
    """
    resolved = Path(path)
    s = str(path)
    if (
        resolved.name == "sources.db"
        or s.rstrip("/").endswith("sources.db")
        or "/sources.db?" in s
    ):
        raise SourcesDbForbiddenError(
            f"network workers cannot open sources.db (refused path={path})"
        )
    # Non-sources paths are still blocked when the ambient network role is set
    # and something tries the open_sources_ro helper — that helper consults the flag.
    if _flag_active():
        # Allow non-sources opens only through explicit network-cache APIs.
        return
