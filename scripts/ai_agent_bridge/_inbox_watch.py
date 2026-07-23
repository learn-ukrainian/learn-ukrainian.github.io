"""Read-only legacy-inbox wakeup watcher for live fleet drivers.

This module deliberately only reports unconsumed messages.  The live driver
remains responsible for reading the full inbox and recording consumption with
``ai_agent_bridge ack --consumed-by-live-driver``.
"""

from __future__ import annotations

import argparse
import fcntl
import os
import signal
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from agent_runtime.agent_identity import seat_read_aliases
from secret_redactor import redact_text

from ._config import DB_PATH, PRIMARY_REPO_ROOT

DEFAULT_POLL_INTERVAL_SECONDS = 15.0
MAX_PREVIEW_CHARS = 240
DEFAULT_LOCK_DIR = PRIMARY_REPO_ROOT / ".agent"


class WatcherAlreadyRunningError(RuntimeError):
    """Raised when another watcher owns an agent slot's lock."""


@dataclass(frozen=True)
class InboxEvent:
    """Stable metadata needed for a driver to decide whether to drain its inbox."""

    message_id: int
    sender: str
    request_id: str
    content: str

    def notification_line(self) -> str:
        """Return a one-line, bounded notification safe for Monitor stdout."""
        return (
            "INBOX-WATCH "
            f"id={self.message_id} "
            f"sender={_escape_one_line(self.sender)} "
            f"request_id={_escape_one_line(self.request_id)} "
            f"preview={_bounded_preview(self.content)}"
        )


@dataclass(frozen=True)
class WatcherLock:
    """An exclusive, per-seat process lock stored outside the broker database."""

    fd: int

    def release(self) -> None:
        """Release the advisory lock; the next watcher safely replaces its stale pid."""
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        finally:
            os.close(self.fd)


def recipients_for_agent(agent: str) -> tuple[str, ...]:
    """Resolve the bridge's permanent dual-read aliases for an agent seat."""
    recipients = seat_read_aliases(agent)
    if not recipients:
        raise ValueError("agent slot must not be empty")
    return recipients


def canonical_slot(agent: str) -> str:
    """Return the canonical slot used for duplicate-watcher locking."""
    return recipients_for_agent(agent)[0]


def build_poll_query(recipients: tuple[str, ...]) -> str:
    """Build the parameterized, read-only query for newly visible messages."""
    if not recipients:
        raise ValueError("at least one recipient is required")
    placeholders = ", ".join("?" for _ in recipients)
    return f"""
        SELECT id, from_llm, task_id, content
        FROM messages
        WHERE to_llm IN ({placeholders})
          AND consumed_by_live_driver = 0
          AND id > ?
        ORDER BY id ASC
    """


def poll_once(
    conn: sqlite3.Connection,
    agent: str,
    last_seen: int = 0,
) -> list[InboxEvent]:
    """Return currently unconsumed messages after the in-memory cursor.

    A fresh watcher starts with ``last_seen=0``, deliberately surfacing every
    current unconsumed row, including rows that predate the watcher process.
    """
    recipients = recipients_for_agent(agent)
    rows = conn.execute(build_poll_query(recipients), (*recipients, last_seen)).fetchall()
    return [
        InboxEvent(
            message_id=int(row["id"]),
            sender=str(row["from_llm"]),
            request_id=str(row["task_id"] or "-"),
            content=str(row["content"]),
        )
        for row in rows
    ]


def emit_notifications(events: list[InboxEvent], last_seen: int, output: TextIO) -> int:
    """Write events and advance the cursor only after each successful flush."""
    for event in events:
        output.write(f"{event.notification_line()}\n")
        output.flush()
        last_seen = event.message_id
    return last_seen


def open_readonly_db(db_path: Path) -> sqlite3.Connection:
    """Open the broker database without running migrations or taking a write lock."""
    database_uri = f"{db_path.resolve().as_uri()}?mode=ro"
    conn = sqlite3.connect(database_uri, uri=True, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def watcher_lock_path(agent: str, lock_dir: Path = DEFAULT_LOCK_DIR) -> Path:
    """Return the ignored per-seat pidfile path, rejecting unsafe slot strings."""
    slot = canonical_slot(agent)
    if not slot.replace("-", "").replace("_", "").replace(".", "").isalnum():
        raise ValueError(f"agent slot contains unsupported lock-path characters: {slot!r}")
    return lock_dir / f"inbox-watch-{slot}.pid"


def acquire_watcher_lock(agent: str, lock_dir: Path = DEFAULT_LOCK_DIR) -> WatcherLock:
    """Acquire an exclusive watcher lock and record the owning process id."""
    path = watcher_lock_path(agent, lock_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = f"{os.getpid()}\n"

    fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        os.close(fd)
        existing_pid = _read_lock_pid(path)
        slot = canonical_slot(agent)
        pid_detail = f" (pid {existing_pid})" if existing_pid is not None else ""
        raise WatcherAlreadyRunningError(
            f"inbox watcher already running for {slot!r}{pid_detail}; "
            f"stop it with scripts/ai_agent_bridge/inbox_watch.sh --stop {slot}"
        ) from exc

    try:
        os.ftruncate(fd, 0)
        os.write(fd, payload.encode("utf-8"))
    except Exception:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        raise
    return WatcherLock(fd=fd)


def stop_watcher(agent: str, lock_dir: Path = DEFAULT_LOCK_DIR) -> str:
    """Request a clean SIGTERM stop for the watcher that owns an agent slot."""
    path = watcher_lock_path(agent, lock_dir)
    if not path.exists():
        return f"No inbox watcher lock exists for {canonical_slot(agent)!r}."

    fd = os.open(path, os.O_WRONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        return f"No inbox watcher is running for {canonical_slot(agent)!r}."

    pid = _read_lock_pid(path)
    if pid is None or not _pid_is_running(pid):
        return f"Inbox watcher lock for {canonical_slot(agent)!r} is no longer active."

    os.kill(pid, signal.SIGTERM)
    return f"Requested clean stop for inbox watcher {canonical_slot(agent)!r} (pid {pid})."


def run_watcher(
    agent: str,
    *,
    interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    db_path: Path = DB_PATH,
    lock_dir: Path = DEFAULT_LOCK_DIR,
    output: TextIO = sys.stdout,
    once: bool = False,
) -> int:
    """Run the persistent watcher and return the final in-memory cursor.

    No messages-table mutation occurs here.  On a write/flush failure the
    exception exits the process before the failed event advances ``last_seen``;
    restarting then deliberately re-emits all still-unconsumed rows.
    """
    if interval_seconds <= 0:
        raise ValueError("poll interval must be greater than zero")

    lock = acquire_watcher_lock(agent, lock_dir)
    conn: sqlite3.Connection | None = None
    last_seen = 0
    try:
        conn = open_readonly_db(db_path)
        while True:
            events = poll_once(conn, agent, last_seen)
            last_seen = emit_notifications(events, last_seen, output)
            if once:
                return last_seen
            time.sleep(interval_seconds)
    finally:
        if conn is not None:
            conn.close()
        lock.release()


def _escape_one_line(value: str) -> str:
    """Escape line breaks so one message always yields exactly one event line."""
    return value.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n")


def _bounded_preview(content: str) -> str:
    """Redact, escape, and truncate message content for a compact notification."""
    preview = _escape_one_line(redact_text(content) or "")
    if len(preview) > MAX_PREVIEW_CHARS:
        return f"{preview[:MAX_PREVIEW_CHARS]}..."
    return preview


def _read_lock_pid(path: Path) -> int | None:
    """Read a positive pid from a lockfile, tolerating a partial stale write."""
    try:
        first_field = path.read_text(encoding="utf-8").split(maxsplit=1)[0]
        pid = int(first_field)
    except (FileNotFoundError, IndexError, OSError, ValueError):
        return None
    return pid if pid > 0 else None


def _pid_is_running(pid: int) -> bool:
    """Return whether a process exists without changing its state."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def build_parser() -> argparse.ArgumentParser:
    """Build the one-command watcher interface used by harness Monitor tools."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agent", help="driver handoff agent slot to watch")
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help=f"seconds between polls (default: {DEFAULT_POLL_INTERVAL_SECONDS:g})",
    )
    parser.add_argument("--once", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--stop", action="store_true", help="request a clean stop for this slot's watcher")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the watcher CLI while keeping normal polling stdout event-only."""
    args = build_parser().parse_args(argv)
    try:
        if args.stop:
            print(stop_watcher(args.agent), file=sys.stderr)
            return 0
        run_watcher(args.agent, interval_seconds=args.interval, once=args.once)
    except (OSError, RuntimeError, ValueError, sqlite3.Error) as exc:
        print(f"inbox watcher: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
