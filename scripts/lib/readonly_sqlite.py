"""Shared filesystem SQLite reader boundary (#9609, #9662).

Kept in scripts/lib so tooling and corpus readers share one small dependency,
without importing a curriculum, crawler, or application package.
"""

from __future__ import annotations

import importlib
import sqlite3
from collections.abc import Callable, Iterable
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol, Self


class SQLiteConnection(Protocol):
    """Connection type for annotations, without exporting a constructor."""

    row_factory: Any
    isolation_level: str | None
    in_transaction: bool

    def execute(self, sql: str, parameters: Any = (), /) -> sqlite3.Cursor: ...
    def executemany(self, sql: str, parameters: Iterable[Any], /) -> sqlite3.Cursor: ...
    def executescript(self, sql: str, /) -> sqlite3.Cursor: ...
    def cursor(self) -> sqlite3.Cursor: ...
    def close(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def set_authorizer(self, callback: Callable[..., int] | None) -> None: ...
    def set_progress_handler(self, callback: Callable[[], int] | None, n: int) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, *args: Any) -> None: ...


def is_sqlite_connection(value: object) -> bool:
    """Keep SQLite-vs-Postgres runtime checks without exporting a constructor."""
    return isinstance(value, sqlite3.Connection)


def open_readonly(
    path: str | Path,
    *,
    timeout: float = 5.0,
    check_same_thread: bool = True,
    isolation_level: str | None = "",
    immutable: bool = False,
) -> sqlite3.Connection:
    """Open exactly path, read-only; refuse extensions and other databases.

    Optional settings preserve reader concurrency, transaction, and immutable
    side-artifact contracts. The caller owns closing the returned connection.
    URI strings are not filesystem paths and must be decoded by their owner.

    SQLite's native attachment limit avoids Python callbacks on connections
    shared across threads. ATTACH raises OperationalError ("too many attached
    databases"); DETACH uses SQLite's own errors for main, temp, or absent names.
    No additional database can be attached, so none can be detached. VACUUM INTO
    is also refused by the attachment limit. Callers must preserve the limit
    and avoid installing Python SQL callbacks on shared connections.
    """
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    if immutable:
        uri += "&immutable=1"
    settings: dict[str, Any] = {}
    if timeout != 5.0:
        settings["timeout"] = timeout
    if not check_same_thread:
        settings["check_same_thread"] = False
    if isolation_level != "":
        settings["isolation_level"] = isolation_level
    conn = sqlite3.connect(uri, uri=True, **settings)
    try:
        if hasattr(conn, "enable_load_extension"):
            conn.enable_load_extension(False)
        conn.execute("PRAGMA query_only=ON")
        conn.setlimit(sqlite3.SQLITE_LIMIT_ATTACHED, 0)
    except BaseException:
        conn.close()
        raise
    return conn


_SQLITE_MODULE_ROOTS = frozenset({"sqlite3", "_sqlite3"})


def import_named_module(name: str) -> ModuleType:
    """Import ``name`` unless it is a SQLite implementation module.

    A non-constant ``importlib.import_module`` is a structural finding: the
    scanner cannot prove the target is not sqlite3. Adapter and startup
    loaders call this boundary, which refuses those module names first.
    """
    root = name.split(".", 1)[0].split(":", 1)[0]
    if root in _SQLITE_MODULE_ROOTS or name in _SQLITE_MODULE_ROOTS:
        raise ImportError(f"SQLite modules are not loaded through this boundary: {name}")
    return importlib.import_module(name)
