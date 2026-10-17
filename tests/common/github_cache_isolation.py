"""Keep GitHub client tests off the shared production cache.

The client stores its disk cache under the git common directory, which for a
linked worktree is the primary checkout. ``LU_GITHUB_CACHE_DIR`` and
``GitHubClient(cache_dir=...)`` already select another directory. Test modules
that construct the client yield :func:`isolate_github_client_cache` from an
autouse fixture so a missing override cannot open ``batch_state/github-client``.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

from scripts.common import github_client as gh


def production_github_cache_directory():
    """The cache directory the client would use with no override, or ``None``."""
    saved = os.environ.pop("LU_GITHUB_CACHE_DIR", None)
    try:
        return gh._cache_directory()
    finally:
        if saved is not None:
            os.environ["LU_GITHUB_CACHE_DIR"] = saved


def _database_path(database):
    """Filesystem path a ``sqlite3.connect`` argument opens, or ``None`` for memory."""
    if isinstance(database, (bytes, bytearray)):
        database = os.fsdecode(database)
    if not isinstance(database, (str, os.PathLike)):
        return None
    raw = os.fsdecode(os.fspath(database))
    if raw == ":memory:" or raw.startswith("file::memory:"):
        return None
    if raw.startswith("file:"):
        raw = unquote(urlsplit(raw).path)
        if not raw:
            return None
    path = Path(raw)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def opens_production_github_cache(database, production):
    """True when ``database`` is the production cache directory or a file inside it."""
    if production is None:
        return False
    path = _database_path(database)
    if path is None:
        return False
    root = Path(production).resolve()
    if path == root:
        return True
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def isolate_github_client_cache(tmp_path, monkeypatch):
    """Point the client at ``tmp_path`` and refuse a connect to the production cache."""
    cache = tmp_path / "github-client-cache"
    monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(cache))
    production = production_github_cache_directory()
    original = gh.sqlite3.connect

    def connect(database, *args, **kwargs):
        if opens_production_github_cache(database, production):
            raise AssertionError("test opened the production GitHub cache under batch_state/github-client")
        return original(database, *args, **kwargs)

    connect.guards_production_github_cache = True
    # github_client.sqlite3 is the sqlite3 module, so this wraps every connect
    # for the test and still passes through paths that are not the shared cache.
    monkeypatch.setattr(gh.sqlite3, "connect", connect)
    yield cache
