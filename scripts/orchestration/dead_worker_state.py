"""Serialize dispatch task writes and terminalize dead workers without stale writes."""

from __future__ import annotations

import fcntl
import json
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.orchestration.worktree_prep import ORPHANED_PREP_REASON


@contextmanager
def task_state_lock(path: Path) -> Iterator[None]:
    """Use a stable adjacent lock file; locking the replaced JSON inode is unsafe."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path.with_suffix(path.suffix + ".lock"), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def write_state_unlocked(path: Path, state: dict[str, Any]) -> None:
    """Replace state while the caller holds its per-task lock."""
    tmp = path.with_suffix(f".json.tmp.{os.getpid()}")
    tmp.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def mark_dead_worker_terminal(
    path: Path,
    observed: dict[str, Any],
    *,
    source: str,
    terminal_status: str,
    allowed_statuses: tuple[str, ...],
    pid_alive: Callable[[int], bool],
    resolve_head: Callable[[Path], str | None],
) -> tuple[dict[str, Any], bool]:
    """Recheck a dead worker under the writer lock, then persist its final HEAD."""
    with task_state_lock(path):
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return observed, False
        if not isinstance(current, dict):
            return observed, False
        raw_pid = current.get("pid")
        pid = int(raw_pid) if isinstance(raw_pid, int) or (isinstance(raw_pid, str) and raw_pid.isdigit()) else None
        if (
            current.get("status") not in allowed_statuses
            or current.get("run_nonce") != observed.get("run_nonce")
            or current.get("pid") != observed.get("pid")
            or current.get("started_at") != observed.get("started_at")
            or (pid is not None and pid_alive(pid))
        ):
            return current, False
        prior_status = current["status"]
        current["status"] = terminal_status
        current["finished_at"] = datetime.now(UTC).isoformat()
        raw_path = current.get("worktree_path")
        if isinstance(raw_path, str) and Path(raw_path).is_dir():
            current["final_branch_head_commit"] = resolve_head(Path(raw_path))
        if terminal_status == "failed":
            current["exit_code"] = current.get("exit_code") if current.get("exit_code") is not None else -9
            current["returncode"] = current.get("returncode") if current.get("returncode") is not None else -9
            current["last_error"] = current.get("last_error") or (
                "dispatch_settle: recorded PID is dead while status=running"
            )
        else:
            current["stderr_excerpt"] = (
                f"worker pid {pid} is not alive but state said {prior_status!r}; marked crashed by {source} probe"
            )
        write_state_unlocked(path, current)
        return current, True


def mark_orphaned_worktree_prep_crashed(
    path: Path,
    observed: dict[str, Any],
    *,
    source: str,
    is_orphaned: Callable[[dict[str, Any]], bool],
) -> tuple[dict[str, Any], bool]:
    """Mark a provisional ``worktree_prep`` record ``crashed`` once its dispatcher is gone (#8663).

    ``is_orphaned`` (normally ``worktree_prep.is_orphaned_prep_record``) is
    re-proved under the writer lock against the record as it is now, and the
    record must still be the observed run. ``worktree_prep`` is kept: it is
    the reaper's proof for the half-built worktree the dispatcher left.
    """
    with task_state_lock(path):
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return observed, False
        if (
            not isinstance(current, dict)
            or current.get("run_nonce") != observed.get("run_nonce")
            or current.get("started_at") != observed.get("started_at")
            or not is_orphaned(current)
        ):
            return current if isinstance(current, dict) else observed, False
        prior_status = current["status"]
        owner = current["worktree_prep"].get("owner_pid")
        current["status"] = "crashed"
        current["finished_at"] = datetime.now(UTC).isoformat()
        current["returncode_reason"] = ORPHANED_PREP_REASON
        current["stderr_excerpt"] = (
            f"dispatcher pid {owner} died while preparing the worktree (state said {prior_status!r}, "
            f"no worker spawned); marked crashed by {source} probe"
        )
        write_state_unlocked(path, current)
        return current, True
