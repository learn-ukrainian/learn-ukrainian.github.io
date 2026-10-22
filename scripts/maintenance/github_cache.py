"""Physical maintenance of the owning GitHub client's existing SQLite cache.

No client is constructed: its normal open path initializes and prunes rows.
This boundary uses its selector and schema but never its fallback or retention.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import sqlite3
import stat
import time
from collections.abc import Callable
from contextlib import ExitStack, closing
from pathlib import Path

from scripts.common import github_client as owner


class _Refused(Exception):
    """A fixed, privacy-safe refusal code, never a filesystem or SQL message."""


def _target(stack: ExitStack) -> tuple[Path, os.stat_result]:
    """Pin trusted, non-symlink components; never create the selected target."""
    directory = owner._cache_directory()
    if directory is None:
        raise _Refused("target_unresolved")
    path = Path(directory).absolute() / "cache.sqlite3"
    if ".." in path.parts:
        raise _Refused("unsafe_path")
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    stack.callback(os.close, fd)
    for part in path.parts[1:-1]:
        fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        stack.callback(os.close, fd)
        info = os.fstat(fd)
        # Root-owned sticky ancestors permit private synthetic caches under a
        # temporary directory. The cache directory itself must be private.
        sticky_root = info.st_uid == 0 and info.st_mode & stat.S_ISVTX
        if info.st_uid not in (0, os.geteuid()) or (info.st_mode & 0o022 and not sticky_root):
            raise _Refused("unsafe_path")
    if os.fstat(fd).st_uid != os.geteuid() or os.fstat(fd).st_mode & 0o022:
        raise _Refused("unsafe_path")
    for suffix in ("", "-journal", "-wal", "-shm"):
        try:
            info = os.stat(path.name + suffix, dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            if not suffix:
                raise
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.geteuid() or info.st_mode & 0o022:
            raise _Refused("unsafe_path")
        # Read-only reporting must not recover a hot journal or create WAL
        # sidecars. Neither is part of the client's default rollback mode.
        if suffix and info.st_size:
            raise _Refused("pending_journal")
    file_fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    stack.callback(os.close, file_fd)
    info = os.fstat(file_fd)
    header = os.pread(file_fd, 100, 0)
    if not header.startswith(b"SQLite format 3\0"):
        raise _Refused("wrong_schema")
    if header[18:20] != b"\x01\x01":
        raise _Refused("unsupported_journal")
    return path, info


def _same_target(path: Path, original: os.stat_result) -> os.stat_result:
    """Refuse identity changes before any SQL and before physical maintenance."""
    current = path.lstat()
    if (current.st_dev, current.st_ino) != (original.st_dev, original.st_ino):
        raise _Refused("target_changed")
    # Recheck components too, so a replaced parent cannot redirect sidecars.
    if any(component.is_symlink() for component in (path, *path.parents)):
        raise _Refused("target_changed")
    return current


def _schema(db: sqlite3.Connection) -> None:
    """Require the owner's exact tables and optional retention index, not lookalikes."""

    def normalize(sql):
        return " ".join(sql.split())

    actual = {normalize(sql) for (sql,) in db.execute("SELECT sql FROM sqlite_schema WHERE sql IS NOT NULL")}
    required = {normalize(sql) for sql in owner.CACHE_SCHEMA[:2]}
    allowed = {normalize(sql) for sql in owner.CACHE_SCHEMA}
    if not required <= actual <= allowed:
        raise _Refused("wrong_schema")


def _snapshot(db: sqlite3.Connection, path: Path, original: os.stat_result) -> dict:
    """Report aggregate storage only; never return row keys, bodies or paths."""
    info = _same_target(path, original)
    page_size = db.execute("PRAGMA page_size").fetchone()[0]
    pages = db.execute("PRAGMA page_count").fetchone()[0]
    free = db.execute("PRAGMA freelist_count").fetchone()[0]
    rows, logical = db.execute(
        f"SELECT count(*),coalesce(sum({owner._CACHE_BYTES}),0) FROM cache WHERE {owner._CACHE_RESPONSE}"
    ).fetchone()
    return {
        "file_bytes": info.st_size,
        "allocated_bytes": info.st_blocks * 512,
        "page_size": page_size,
        "page_count": pages,
        "freelist_count": free,
        "free_page_bytes": free * page_size,
        "response_rows": rows,
        "logical_response_bytes": logical,
        "unclassified_rows": db.execute("SELECT count(*) FROM cache").fetchone()[0] - rows,
        "budget_rows": db.execute("SELECT count(*) FROM budget").fetchone()[0],
    }


def maintain(
    *,
    apply: bool = False,
    timeout_seconds: float = 30,
    cancelled: Callable[[], bool] | None = None,
) -> dict:
    """Inspect, or explicitly VACUUM, the existing owner-selected cache.

    Exclusive rollback-mode locking persists across COMMIT and VACUUM. A busy
    reader/writer refuses admission; newly arriving connections wait or fail
    under their own SQLite policy. VM progress/deadline checks bound SQL work;
    OS I/O and journal rollback may take longer. No retries or alternate DB.
    """
    receipt = {"outcome": "refused", "eligible": False, "applied": False}
    if (
        type(timeout_seconds) not in (int, float)
        or not math.isfinite(timeout_seconds)
        or not 0 < timeout_seconds <= 300
    ):
        return {**receipt, "reason": "invalid_timeout"}
    deadline = time.monotonic() + timeout_seconds
    cancelled = cancelled or (lambda: False)
    try:
        with ExitStack() as stack:
            path, original = _target(stack)
            uri = path.as_uri() + ("?mode=rw" if apply else "?mode=ro")
            db = stack.enter_context(
                closing(
                    sqlite3.connect(
                        uri,
                        uri=True,
                        timeout=min(timeout_seconds, 1),
                        isolation_level=None,
                    )
                )
            )
            _same_target(path, original)
            db.execute("PRAGMA trusted_schema=OFF")
            db.set_progress_handler(lambda: int(cancelled() or time.monotonic() >= deadline), 1000)
            if apply:
                db.execute("PRAGMA locking_mode=EXCLUSIVE")
                db.execute("BEGIN EXCLUSIVE")
            else:
                db.execute("BEGIN")
            if db.execute("PRAGMA journal_mode").fetchone()[0] not in {"delete", "truncate", "persist"}:
                raise _Refused("unsupported_journal")
            _schema(db)
            before = _snapshot(db, path, original)
            receipt["before"] = before
            receipt["eligible"] = bool(before["freelist_count"])
            if not apply:
                return {**receipt, "outcome": "report", "reason": "free_pages" if receipt["eligible"] else "compact"}
            if not receipt["eligible"]:
                return {**receipt, "outcome": "no_op", "reason": "compact", "after": before, "reclaimed_file_bytes": 0}
            # EXCLUSIVE locking mode holds the lock after the transaction ends.
            # VACUUM cannot execute inside a transaction.
            db.execute("COMMIT")
            _same_target(path, original)
            if cancelled():
                raise _Refused("interrupted")
            if time.monotonic() >= deadline:
                raise _Refused("deadline")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("VACUUM")
            receipt["applied"] = True
            # Keep deadline/cancellation checks during receipt collection.
            # A post-commit failure is applied_unverified, never an unapplied refusal.
            after = _snapshot(db, path, original)
            reclaimed = before["file_bytes"] - after["file_bytes"]
            return {
                **receipt,
                "outcome": "reclaimed" if reclaimed > 0 else "no_op",
                "reason": "vacuum_complete",
                "after": after,
                "reclaimed_file_bytes": reclaimed,
            }
    except _Refused as exc:
        reason = str(exc)
    except FileNotFoundError:
        reason = "missing_database"
    except (OSError, ValueError):
        reason = "unsafe_or_unavailable_target"
    except sqlite3.Error as exc:
        code = getattr(exc, "sqlite_errorcode", 0) & 0xFF
        reason = {
            sqlite3.SQLITE_BUSY: "busy",
            sqlite3.SQLITE_LOCKED: "busy",
            sqlite3.SQLITE_INTERRUPT: "interrupted",
        }.get(code, "sqlite_failure")
        if code == sqlite3.SQLITE_INTERRUPT and not cancelled() and time.monotonic() >= deadline:
            reason = "deadline"
    except KeyboardInterrupt:
        reason = "interrupted"
    if receipt["applied"]:
        receipt["outcome"] = "applied_unverified"
    return {**receipt, "eligible": False, "reason": reason}


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        """Do not echo caller-supplied private paths or values on syntax errors."""
        self.exit(2, "github_cache: invalid_arguments; use --help\n")


def main(argv: list[str] | None = None) -> int:
    """Print a privacy-safe JSON receipt; signal interruption closes SQLite normally."""
    parser = _Parser(
        description="Report physical GitHub cache storage, or explicitly reclaim free pages.\n"
        "Use for owner-cache maintenance, never for arbitrary databases or row eviction.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.maintenance.github_cache
  .venv/bin/python -m scripts.maintenance.github_cache --apply --timeout-seconds 60
Outputs: one aggregate JSON receipt; --apply runs journaled VACUUM in place.
Exit codes: 0 report/reclaimed/no_op; 2 refused; 130 interrupted.
Related: docs/runbooks/github-cache-maintenance.md; issue #11362.
""",
    )
    parser.add_argument("--apply", action="store_true", help="Reclaim free pages explicitly; default: report only.")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30,
        help="SQL deadline in seconds, >0 and <=300; default: 30; example: 60. Lock wait <=1 second.",
    )
    args = parser.parse_args(argv)

    cancellation = [False]

    def interrupted(signum, frame):
        cancellation[0] = True

    with ExitStack() as stack:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous = signal.signal(signum, interrupted)
            stack.callback(signal.signal, signum, previous)
        receipt = maintain(apply=args.apply, timeout_seconds=args.timeout_seconds, cancelled=lambda: cancellation[0])
    print(json.dumps(receipt, sort_keys=True))
    return (
        130
        if receipt.get("reason") == "interrupted"
        else 2
        if receipt["outcome"] in {"refused", "applied_unverified"}
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
