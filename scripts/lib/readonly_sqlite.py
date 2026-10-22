"""Shared filesystem SQLite reader boundary (#9609, #9662).

Kept in scripts/lib so tooling and corpus readers share one small dependency,
without importing a curriculum, crawler, or application package.
"""

from __future__ import annotations

import functools
import importlib
import sqlite3
import threading
from collections.abc import Callable, Iterable
from contextlib import suppress
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


def _serialized(method: Any) -> Any:
    """Keep SQLite execution and its Python result/error handling under one lock."""

    @functools.wraps(method)
    def call(self: Any, *args: Any, **kwargs: Any) -> Any:
        connection = self.connection if isinstance(self, sqlite3.Cursor) else self
        with connection._operation_lock:
            try:
                return method(self, *args, **kwargs)
            finally:
                while connection._pending_cursor_closes:
                    cursor = connection._pending_cursor_closes.pop()
                    # Connection.close() may already have closed the reader.
                    with suppress(sqlite3.ProgrammingError):
                        sqlite3.Cursor.close(cursor)

    return call


class SerializedCursor(sqlite3.Cursor):
    """Cursors on one shared reader use their connection's operation lock."""

    execute = _serialized(sqlite3.Cursor.execute)
    executemany = _serialized(sqlite3.Cursor.executemany)
    executescript = _serialized(sqlite3.Cursor.executescript)
    fetchone = _serialized(sqlite3.Cursor.fetchone)
    fetchmany = _serialized(sqlite3.Cursor.fetchmany)
    fetchall = _serialized(sqlite3.Cursor.fetchall)
    __next__ = _serialized(sqlite3.Cursor.__next__)
    close = _serialized(sqlite3.Cursor.close)

    def __del__(self) -> None:
        try:
            connection = self.connection
            lock = connection._operation_lock
            # RLock permits same-thread GC. Never wait across connections:
            # two threads may each hold one lock while finalizing the other's
            # cursor. Retain a contended cursor until a locked call drains it;
            # letting native deallocation run here would reset SQLite unlocked.
            if not lock.acquire(blocking=False):
                connection._pending_cursor_closes.append(self)
                return
            try:
                self.close()
            finally:
                lock.release()
        except Exception:
            # Failed construction, an already closed connection, or teardown
            # may leave no usable connection or module globals for close().
            pass


class SerializedConnection(sqlite3.Connection):
    """Serialize shared read operations without holding the cache/reopen lock.

    SQLite's mutex alone does not protect CPython's subsequent error handling.
    One RLock also covers fetches, iteration and close, including held readers
    after a cache replacement. No Python SQL callbacks are installed.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._operation_lock = threading.RLock()
        self._pending_cursor_closes: list[SerializedCursor] = []
        super().__init__(*args, **kwargs)

    @_serialized
    def cursor(self, factory: Any = SerializedCursor) -> Any:
        return super().cursor(factory)

    # SQLite's convenience methods create plain cursors internally.
    def execute(self, sql: str, parameters: Any = (), /) -> Any:
        return self.cursor().execute(sql, parameters)

    def executemany(self, sql: str, parameters: Any, /) -> Any:
        return self.cursor().executemany(sql, parameters)

    def executescript(self, script: str, /) -> Any:
        return self.cursor().executescript(script)

    close = _serialized(sqlite3.Connection.close)
    commit = _serialized(sqlite3.Connection.commit)
    rollback = _serialized(sqlite3.Connection.rollback)
    __enter__ = _serialized(sqlite3.Connection.__enter__)
    __exit__ = _serialized(sqlite3.Connection.__exit__)


def open_readonly(
    path: str | Path,
    *,
    timeout: float = 5.0,
    check_same_thread: bool = True,
    isolation_level: str | None = "",
    immutable: bool = False,
    factory: type[sqlite3.Connection] | None = None,
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
    Shared connections disable the statement cache; CPython 3.12+ corrupts it
    when threads share one connection. ``factory`` is a ``sqlite3.Connection``
    subclass for readers that observe errors (the Sources MCP server, #11115).
    Shared readers default to ``SerializedConnection``; custom shared-reader
    factories inherit it and use ``SerializedCursor`` to retain serialization.
    """
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    if immutable:
        uri += "&immutable=1"
    settings: dict[str, Any] = {}
    if timeout != 5.0:
        settings["timeout"] = timeout
    if not check_same_thread:
        settings["check_same_thread"] = False
        # CPython 3.12+ keeps one statement cache per connection, and that cache
        # is not safe when threads share the connection: fetches come back wrong
        # and sqlite3 raises InterfaceError or IndexError (CPython #118172,
        # #11208). The operation lock also protects Python error handling
        # after SQLite releases its mutex.
        # Disabling the statement cache is the documented upstream mitigation.
        # Retain this defense even though the default shared reader now also
        # serializes native calls and their Python error handling (#11330).
        settings["cached_statements"] = 0
    if isolation_level != "":
        settings["isolation_level"] = isolation_level
    if factory is None and not check_same_thread:
        factory = SerializedConnection
    if factory is not None:
        settings["factory"] = factory
    conn = sqlite3.connect(uri, uri=True, **settings)
    try:
        if hasattr(conn, "enable_load_extension"):
            conn.enable_load_extension(False)
        conn.execute("PRAGMA query_only=ON")
        # Refuse ATTACH with SQLite's own limit, never a Python callback: a
        # callback runs while SQLite holds the connection mutex with the GIL
        # released, so a connection shared across threads deadlocks against a
        # thread that holds the GIL and waits for that mutex (#10674). With no
        # attached database, DETACH has nothing to remove.
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
