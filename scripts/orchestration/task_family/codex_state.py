"""Fragile Codex DB reconciliation bridge for cleanup state repair.

The module is intentionally read-only: it validates that selected Codex task
threads are already at the required archive state. It never writes to the Codex
state DB.
"""

from __future__ import annotations

import contextlib
import dataclasses
import json
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

THREADS_TABLE = "threads"
THREADS_REQUIRED_COLUMNS = frozenset({"id", "title", "cwd", "archived", "archived_at"})
# Codex uses versioned filenames such as ``state_5.sqlite`` and longer opaque
# versions.  Discovery deliberately accepts the documented family, not a
# guessed length or hexadecimal-only subset.
STATE_PATTERN = re.compile(r"^state_[A-Za-z0-9][A-Za-z0-9._-]*\.sqlite$")


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
    thread_id: str
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


def _coerce_task_id(raw: Any) -> str:
    candidate = _to_text(raw)
    if candidate is None:
        raise CodexStateContextError("task id is required")
    try:
        return str(uuid.UUID(candidate.strip()))
    except ValueError as exc:
        raise CodexStateContextError(f"task id must be a UUID: {candidate!r}") from exc


def _row_to_record(row: sqlite3.Row, *, has_host: bool) -> ThreadRecord:
    archived = _coerce_bool(row["archived"])
    archived_at = _to_text(row["archived_at"])
    host = row["host"] if has_host else None
    return ThreadRecord(
        thread_id=_coerce_task_id(row["id"]),
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


def _make_uri(path: Path, mode: str) -> str:
    if mode != "ro":
        raise ValueError("mode must be 'ro'")
    return f"file:{path.resolve().as_posix()}?mode=ro"


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
    """Open the bridge DB read-only. Mutations are forbidden."""
    if mode != "ro":
        raise ValueError("mode must be 'ro'")

    uri = _make_uri(path, mode)
    connection = sqlite3.connect(
        uri,
        uri=True,
        timeout=timeout_seconds,
        check_same_thread=False,
    )
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.execute(f"PRAGMA busy_timeout = {int(max(0.0, timeout_seconds) * 1000)}")
        yield connection
    except sqlite3.Error as exc:
        _raise_db_failure(exc, context="opening DB")
    finally:
        with contextlib.suppress(Exception):
            connection.close()


def discover_state_database(
    explicit_db_path: Path | str | None = None,
    *,
    codex_home: Path | None = None,
    timeout_seconds: float = 5.0,
) -> Path:
    """Return explicit DB or the newest compatible ``~/.codex/state_*.sqlite``."""
    if explicit_db_path is not None:
        db_path = Path(explicit_db_path).expanduser()
        if not db_path.exists():
            raise CodexStateDiscoveryError(f"explicit codex DB not found: {db_path}")
        if not STATE_PATTERN.fullmatch(db_path.name):
            raise CodexStateContextError(f"invalid Codex DB filename: {db_path.name}")
        with open_state_db(db_path, timeout_seconds=timeout_seconds, mode="ro") as connection:
            tables = _sqlite_tables(connection)
            if not tables:
                raise CodexStateSchemaError(f"empty schema for explicit DB: {db_path}")
            if THREADS_TABLE not in tables:
                raise CodexStateSchemaError(f"missing threads table in {db_path}")
            columns = _thread_columns(connection)
            _require_threads_schema(columns)
        return db_path

    home = codex_home or Path.home() / ".codex"
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
    thread_id: str,
    *,
    timeout_seconds: float = 5.0,
) -> ThreadRecord:
    normalized = _coerce_task_id(thread_id)
    with open_state_db(db_path, timeout_seconds=timeout_seconds, mode="ro") as connection:
        columns = _select_sql(connection)
        has_host = "host" in columns.split(", ")
        rows = connection.execute(
            f"select {columns} from {THREADS_TABLE} where id = ? limit 1",
            (normalized,),
        ).fetchall()

    if not rows:
        raise CodexStateMissingTaskError(f"missing task {thread_id} in {db_path}")

    return _row_to_record(rows[0], has_host=has_host)


def read_thread_record(
    db_path: Path | str,
    *,
    thread_id: str | None = None,
    task_id: str | None = None,
    timeout_seconds: float = 5.0,
    read_window_seconds: float = 0.75,
) -> ThreadRecord:
    """Read one exact thread row with a bounded stable sample guard."""
    if thread_id is None and task_id is None:
        raise CodexStateContextError("thread_id/task_id is required")
    task = task_id or thread_id
    assert task is not None

    path = Path(db_path)
    if not path.exists():
        raise CodexStateMissingTaskError(f"missing task {task} in {path}")

    deadline = time.monotonic() + max(0.0, read_window_seconds)
    stable_sample: ThreadRecord | None = None
    stable_count = 0

    while True:
        try:
            current = _read_thread_once(path, task, timeout_seconds=timeout_seconds)
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
                f"thread {task} state raced during bounded read window: {db_path}"
            )
        time.sleep(0.05)


def _ensure_archive_shape(record: ThreadRecord, *, archived: bool) -> bool:
    if archived:
        return record.archived and bool(record.archived_at and str(record.archived_at).strip())
    return not record.archived and record.archived_at in (None, "")


def _validate_context(
    record: ThreadRecord,
    *,
    expected_title: str,
    expected_cwd: str,
    expected_host: str | None,
) -> None:
    if record.title != expected_title:
        raise CodexStateContextError(
            f"title mismatch for task {record.thread_id}: db={record.title!r}, expected={expected_title!r}"
        )
    if record.cwd != expected_cwd:
        raise CodexStateContextError(
            f"cwd mismatch for task {record.thread_id}: db={record.cwd!r}, expected={expected_cwd!r}"
        )
    if expected_host is not None and record.host != expected_host:
        raise CodexStateContextError(
            f"host mismatch for task {record.thread_id}: db={record.host!r}, expected={expected_host!r}"
        )


def await_task_target(
    *,
    task_id: str,
    expected_title: str,
    expected_cwd: str,
    expected_archived: bool,
    db_path: Path | str,
    expected_host: str | None = None,
    timeout_seconds: float = 5.0,
    read_window_seconds: float = 0.75,
) -> ThreadRecord:
    """Poll until a task reaches exact archive target or fail closed."""
    deadline = time.monotonic() + max(0.0, read_window_seconds)

    while True:
        record = read_thread_record(
            task_id=task_id,
            db_path=db_path,
            timeout_seconds=timeout_seconds,
            read_window_seconds=min(0.75, read_window_seconds),
        )
        _validate_context(record, expected_title=expected_title, expected_cwd=expected_cwd, expected_host=expected_host)

        if record.archived and not record.archived_at:
            raise CodexStateConflictError(
                f"conflicting archive shape for task {task_id}: archived=1 and archived_at is NULL"
            )
        if (not record.archived) and record.archived_at not in (None, ""):
            raise CodexStateConflictError(
                f"conflicting archive shape for task {task_id}: archived=0 and archived_at={record.archived_at!r}"
            )

        if _ensure_archive_shape(record, archived=expected_archived):
            return record

        if time.monotonic() >= deadline:
            raise CodexStateConflictError(
                f"thread {task_id} state did not reach target within bounded read window: {db_path}"
            )
        time.sleep(0.05)


def reconcile_thread_archive(
    *,
    thread_id: str,
    expected_title: str,
    expected_cwd: str,
    archived: bool,
    db_path: Path | str,
    expected_host: str | None = None,
    archive_now: str | None = None,
    timeout_seconds: float = 5.0,
) -> tuple[ThreadRecord, ThreadRecord, bool]:
    """Reconcile expectation: return only when the DB matches the target shape."""
    del archive_now
    before = await_task_target(
        task_id=_coerce_task_id(thread_id),
        expected_title=expected_title,
        expected_cwd=expected_cwd,
        expected_archived=archived,
        db_path=db_path,
        expected_host=expected_host,
        timeout_seconds=timeout_seconds,
    )
    return before, before, False


def reconcile_thread_restore(
    *,
    thread_id: str,
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
    task_id: str,
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
            thread_id=_coerce_task_id(task_id),
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
            thread_id=_coerce_task_id(task_id),
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
    return json.loads(json.dumps(dataclasses.asdict(record)))
