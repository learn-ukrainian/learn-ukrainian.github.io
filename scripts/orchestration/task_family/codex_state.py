"""Fragile Codex DB reconciliation bridge for cleanup state repair."""

from __future__ import annotations

import contextlib
import json
import re
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

THREADS_TABLE = "threads"
THREADS_REQUIRED_COLUMNS = frozenset({"id", "title", "cwd", "archived", "archived_at"})
STATE_PATTERN = re.compile(r"^state_.*\.sqlite$")


class CodexStateError(RuntimeError):
    """Base error for fail-closed bridge failures."""


class CodexStateDiscoveryError(CodexStateError):
    """No usable DB was found or discovery was ambiguous."""


class CodexStateSchemaError(CodexStateError):
    """The DB exists but missing required thread columns."""


class CodexStateMissingTaskError(CodexStateError):
    """Requested thread ID was not found in the chosen DB."""


class CodexStateContextError(CodexStateError):
    """Context mismatch for strict row targeting."""


class CodexStateConflictError(CodexStateError):
    """Requested reconcile transition conflicts with current row state."""


@dataclass(frozen=True)
class ThreadRecord:
    thread_id: int
    title: str
    cwd: str
    archived: bool
    archived_at: str | None
    host: str | None


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        lowered = value.lower().strip()
        if lowered in {"1", "true", "t", "yes", "y"}:
            return True
        if lowered in {"0", "false", "f", "no", "n", ""}:
            return False
    raise CodexStateContextError(f"cannot coerce archived flag: {value!r}")


def _to_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _row_to_record(row: sqlite3.Row, *, has_host: bool) -> ThreadRecord:
    archived = _coerce_bool(row["archived"])
    archived_at = _to_text(row["archived_at"])
    host = row["host"] if has_host else None
    return ThreadRecord(
        thread_id=int(row["id"]),
        title=_to_text(row["title"]) or "",
        cwd=_to_text(row["cwd"]) or "",
        archived=archived,
        archived_at=archived_at,
        host=_to_text(host),
    )


def _thread_columns(connection: sqlite3.Connection) -> frozenset[str]:
    rows = connection.execute(f"PRAGMA table_info({THREADS_TABLE})").fetchall()
    return frozenset(str(row[1]) for row in rows)


def _sqlite_tables(connection: sqlite3.Connection) -> frozenset[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'",
    ).fetchall()
    return frozenset(str(row[0]) for row in rows)


def _require_threads_schema(columns: frozenset[str]) -> None:
    if not THREADS_REQUIRED_COLUMNS.issubset(columns):
        missing = sorted(THREADS_REQUIRED_COLUMNS - columns)
        raise CodexStateSchemaError(f"missing threads columns: {', '.join(missing)}")


def _codex_home_path(codex_home: Path | None) -> Path:
    return codex_home or (Path.home() / ".codex")


def _make_uri(path: Path, mode: str) -> str:
    return f"file:{path.as_posix()}?mode={mode}"


def _raise_db_failure(exc: Exception, *, context: str) -> None:
    message = str(exc) if str(exc) else exc.__class__.__name__
    if isinstance(exc, sqlite3.OperationalError) and ("locked" in message.lower() or "timeout" in message.lower()):
        raise CodexStateConflictError(f"database contention while {context}: {message}") from exc
    raise CodexStateError(f"database error while {context}: {message}") from exc


@contextmanager
def open_state_db(
    path: Path,
    *,
    timeout_seconds: float = 5.0,
    mode: str = "ro",
):
    """Open the bridge DB in strict read-only mode unless writable is requested."""
    if mode not in {"ro", "rw"}:
        raise ValueError("mode must be 'ro' or 'rw'")

    uri = _make_uri(path, mode)
    try:
        connection = sqlite3.connect(
            uri,
            uri=True,
            timeout=timeout_seconds,
            check_same_thread=False,
        )
    except sqlite3.Error as exc:
        _raise_db_failure(exc, context="opening DB")

    try:
        connection.row_factory = sqlite3.Row
        if mode == "ro":
            connection.execute("PRAGMA query_only = ON")
        yield connection
    finally:
        with contextlib.suppress(Exception):
            connection.close()


def discover_state_database(
    explicit_db_path: Path | str | None = None,
    *,
    codex_home: Path | None = None,
    timeout_seconds: float = 5.0,
) -> Path:
    """Return explicit DB or the newest unique compatible ``~/.codex/state_*.sqlite``."""
    if explicit_db_path is not None:
        db_path = Path(explicit_db_path).expanduser()
        if not db_path.exists():
            raise CodexStateDiscoveryError(f"explicit codex DB not found: {db_path}")
        with open_state_db(db_path, timeout_seconds=timeout_seconds, mode="ro") as connection:
            tables = _sqlite_tables(connection)
            if not tables:
                raise CodexStateSchemaError(f"empty schema for explicit DB: {db_path}")
            if THREADS_TABLE not in tables:
                raise CodexStateSchemaError(f"missing threads table in {db_path}")
            columns = _thread_columns(connection)
            _require_threads_schema(columns)
        return db_path

    home = _codex_home_path(codex_home)
    if not home.exists():
        raise CodexStateDiscoveryError(f"codex home not found: {home}")

    candidates: list[tuple[Path, int]] = []
    for path in sorted(home.glob("state_*.sqlite")):
        if not path.is_file() or not STATE_PATTERN.match(path.name):
            continue
        try:
            with open_state_db(path, timeout_seconds=timeout_seconds, mode="ro") as connection:
                tables = _sqlite_tables(connection)
                if not tables:
                    continue
                if THREADS_TABLE not in tables:
                    raise CodexStateSchemaError(f"missing threads table in {path}")
                _require_threads_schema(_thread_columns(connection))
            candidates.append((path, path.stat().st_mtime_ns))
        except CodexStateSchemaError:
            raise
        except (sqlite3.Error, OSError):
            continue

    if not candidates:
        raise CodexStateDiscoveryError(f"missing compatible codex DB in {home}")

    candidates.sort(key=lambda item: item[1], reverse=True)
    newest_mtime = candidates[0][1]
    ambiguous = [path for path, mtime in candidates if mtime == newest_mtime]
    if len(ambiguous) > 1:
        joined = ", ".join(sorted(str(path) for path in ambiguous))
        raise CodexStateDiscoveryError(f"ambiguous newest compatible state DBs: {joined}")

    return candidates[0][0]


def _select_sql(connection: sqlite3.Connection) -> str:
    columns = ["id", "title", "cwd", "archived", "archived_at"]
    if "host" in _thread_columns(connection):
        columns.append("host")
    return ", ".join(columns)


def _read_thread_once(
    db_path: Path,
    thread_id: int,
    *,
    timeout_seconds: float = 5.0,
) -> ThreadRecord:
    with open_state_db(db_path, timeout_seconds=timeout_seconds, mode="ro") as connection:
        columns = _select_sql(connection)
        has_host = "host" in columns
        rows = connection.execute(
            f"select {columns} from {THREADS_TABLE} where id = ? limit 1",
            (thread_id,),
        ).fetchall()

    if not rows:
        raise CodexStateMissingTaskError(f"missing task {thread_id} in {db_path}")

    return _row_to_record(rows[0], has_host=has_host)


def read_thread_record(
    thread_id: int,
    db_path: Path | str,
    *,
    timeout_seconds: float = 5.0,
    read_window_seconds: float = 0.75,
) -> ThreadRecord:
    """Read one exact thread row with a bounded monotonic read guard."""
    path = Path(db_path)
    if not path.exists():
        raise CodexStateMissingTaskError(f"missing task {thread_id} in {path}")

    deadline = time.monotonic() + max(0.0, read_window_seconds)
    stable_sample: ThreadRecord | None = None
    stable_count = 0

    while True:
        try:
            current = _read_thread_once(path, thread_id, timeout_seconds=timeout_seconds)
        except sqlite3.Error as exc:
            _raise_db_failure(exc, context="reading thread row")

        if stable_sample is None:
            stable_sample = current
            stable_count = 1
            time.sleep(0.05)
            continue
        if current == stable_sample:
            stable_count += 1
            if stable_count >= 3:
                return current
        else:
            stable_sample = current
            stable_count = 1
        if time.monotonic() >= deadline:
            raise CodexStateConflictError(
                f"thread {thread_id} state raced during bounded read window: {db_path}"
            )
        time.sleep(0.05)


def reconcile_thread_archive(
    *,
    thread_id: int,
    expected_title: str,
    expected_cwd: str,
    archived: bool,
    db_path: Path | str,
    expected_host: str | None = None,
    archive_now: str | None = None,
    timeout_seconds: float = 5.0,
) -> tuple[ThreadRecord, ThreadRecord, bool]:
    """Reconcile a thread to the target archive state and report mutation status."""
    path = Path(db_path)
    before = read_thread_record(thread_id, path, timeout_seconds=timeout_seconds)

    if before.title != expected_title:
        raise CodexStateContextError(
            f"title mismatch for task {thread_id}: db={before.title!r}, expected={expected_title!r}"
        )
    if before.cwd != expected_cwd:
        raise CodexStateContextError(
            f"cwd mismatch for task {thread_id}: db={before.cwd!r}, expected={expected_cwd!r}"
        )
    if expected_host is not None and before.host != expected_host:
        raise CodexStateContextError(
            f"host mismatch for task {thread_id}: db={before.host!r}, expected={expected_host!r}"
        )

    if before.archived and before.archived_at in (None, ""):
        raise CodexStateConflictError(
            f"conflicting archive shape for task {thread_id}: archived=1 and archived_at is NULL"
        )
    if (not before.archived) and before.archived_at not in (None, ""):
        raise CodexStateConflictError(
            f"conflicting archive shape for task {thread_id}: archived=0 and archived_at={before.archived_at!r}"
        )

    target_archived_at = None if not archived else (archive_now or _utc_now())
    already_target = before.archived == archived and (
        (archived is False and before.archived_at in (None, ""))
        or (archived is True and before.archived_at not in (None, ""))
    )
    if already_target:
        return before, before, False

    where = "id = ? AND title = ? AND cwd = ?"
    params = [int(bool(archived)), target_archived_at, thread_id, expected_title, expected_cwd]
    if expected_host is not None:
        where += " AND host = ?"
        params.append(expected_host)

    target = None
    try:
        with open_state_db(path, timeout_seconds=timeout_seconds, mode="rw") as connection:
            cursor = connection.execute(
                f"UPDATE {THREADS_TABLE} SET archived = ?, archived_at = ? WHERE {where}",
                params,
            )
            if cursor.rowcount != 1:
                raise CodexStateConflictError(f"conflicting update for task {thread_id}")
            connection.commit()
            target = read_thread_record(
                thread_id,
                path,
                timeout_seconds=timeout_seconds,
            )
    except sqlite3.Error as exc:
        _raise_db_failure(exc, context=f"reconciling task {thread_id}")

    if target is None:
        raise CodexStateConflictError(f"could not read task {thread_id} after reconcile")

    if target.archived != archived:
        raise CodexStateConflictError(f"archive target mismatch for task {thread_id}")
    if archived and not target.archived_at:
        raise CodexStateConflictError(f"archive target requires archived_at for task {thread_id}")
    if (not archived) and target.archived_at not in (None, ""):
        raise CodexStateConflictError(f"restore target requires archived_at NULL for task {thread_id}")
    if target.title != expected_title:
        raise CodexStateConflictError(f"title mismatch after reconcile for task {thread_id}: {target.title!r}")

    return before, target, True


def reconcile_thread_restore(
    *,
    thread_id: int,
    expected_title: str,
    expected_cwd: str,
    db_path: Path | str,
    expected_host: str | None = None,
    timeout_seconds: float = 5.0,
) -> tuple[ThreadRecord, ThreadRecord, bool]:
    """Explicit restore path (inverse of archive)."""
    return reconcile_thread_archive(
        thread_id=thread_id,
        expected_title=expected_title,
        expected_cwd=expected_cwd,
        archived=False,
        db_path=db_path,
        expected_host=expected_host,
        timeout_seconds=timeout_seconds,
    )


def reconcile_task_thread(
    *,
    task_id: int,
    action: str,
    expected_title: str,
    expected_cwd: str,
    db_path: Path | str,
    expected_host: str | None = None,
    timeout_seconds: float = 5.0,
    archive_now: str | None = None,
) -> tuple[ThreadRecord, ThreadRecord, bool]:
    """Reconcile a task thread by action string: ``archive`` or ``restore``."""
    verb = action.lower()
    if verb == "archive":
        return reconcile_thread_archive(
            thread_id=task_id,
            expected_title=expected_title,
            expected_cwd=expected_cwd,
            archived=True,
            db_path=db_path,
            expected_host=expected_host,
            archive_now=archive_now,
            timeout_seconds=timeout_seconds,
        )
    if verb == "restore":
        return reconcile_thread_restore(
            thread_id=task_id,
            expected_title=expected_title,
            expected_cwd=expected_cwd,
            db_path=db_path,
            expected_host=expected_host,
            timeout_seconds=timeout_seconds,
        )
    raise CodexStateContextError(f"unsupported action: {action!r}")


def build_reconciliation_payload(
    before: ThreadRecord,
    after: ThreadRecord,
    changed: bool,
    *,
    action: str,
    archived_at: str | None = None,
) -> dict[str, Any]:
    return {
        "action": action,
        "thread_id": before.thread_id,
        "changed": bool(changed),
        "expected": {
            "title": before.title,
            "archived": after.archived,
            "archived_at": after.archived_at,
        },
        "before": {
            "title": before.title,
            "archived": before.archived,
            "archived_at": before.archived_at,
        },
        "after": {
            "title": after.title,
            "archived": after.archived,
            "archived_at": after.archived_at,
        },
        "evidence": {
            "archived_at": archived_at,
        },
    }


def dump_thread_state(record: ThreadRecord) -> dict[str, Any]:
    return json.loads(json.dumps(record.__dict__))
