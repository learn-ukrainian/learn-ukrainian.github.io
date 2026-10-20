"""Read-only SUM-20 store selection using the shared storage boundaries (#10655)."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from scripts.lexdata.generation import Unavailable, open_generation
from scripts.lib.readonly_sqlite import SQLiteConnection, open_readonly
from scripts.storage.topology import StoreBinding, StoreRefusal, resolve_store


class Sum20StoreError(ValueError):
    """A path-free refusal; an invalid store is never a dictionary miss."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def open_sources(db_path: Path | str | None = None, *, repository_root: Path | None = None) -> SQLiteConnection:
    """Open an injected or canonical sources store through the read boundary."""
    binding = None if db_path is None else StoreBinding("sources", Path(db_path))
    resolved = resolve_store("sources", repository_root, binding=binding)
    if isinstance(resolved, StoreRefusal):
        raise Sum20StoreError(resolved.reason)
    try:
        conn = open_readonly(resolved.path)
    except (OSError, sqlite3.Error):
        raise Sum20StoreError("sources_unavailable") from None
    conn.row_factory = sqlite3.Row
    return conn


def open_sum20(db_path: Path | str | None = None, *, repository_root: Path | None = None) -> SQLiteConnection:
    """Open canonical articles, validating every selected lexdata generation.

    Injected sources paths take precedence. Explicit lexdata overrides are
    exclusive, including the legacy LEXDATA_DB_PATH spelling. Only an absent
    default lexdata file or a valid generation without SUM-20 uses sources.
    The caller closes the connection. No input grants write access.
    """
    if db_path is not None:
        return open_sources(db_path, repository_root=repository_root)
    env = dict(os.environ)
    if "LEXDATA_DB_PATH" in env:
        if "LU_LEXDATA_DB" in env and env["LU_LEXDATA_DB"] != env["LEXDATA_DB_PATH"]:
            raise Sum20StoreError("conflicting_lexdata_overrides")
        env["LU_LEXDATA_DB"] = env["LEXDATA_DB_PATH"]
    exclusive = "LU_LEXDATA_DB" in env
    resolved = resolve_store("lexdata", repository_root, env=env)
    if isinstance(resolved, StoreRefusal):
        if resolved.reason == "store_missing" and not exclusive:
            return open_sources(repository_root=repository_root)
        raise Sum20StoreError(resolved.reason)
    opened = open_generation(resolved.path, repository_root=repository_root, env=env)
    if isinstance(opened, Unavailable):
        raise Sum20StoreError(opened.reason)
    conn = opened.conn
    conn.row_factory = sqlite3.Row
    present = None
    try:
        present = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sum20_articles'").fetchone()
        if present:
            return conn
    except sqlite3.Error:
        raise Sum20StoreError("lexdata_unavailable") from None
    finally:
        if not present:
            conn.close()
    if exclusive:
        raise Sum20StoreError("sum20_table_missing")
    return open_sources(repository_root=repository_root)
