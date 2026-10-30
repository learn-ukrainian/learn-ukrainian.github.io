"""Journal and recovery refs left from the retired merged-worktree reaper.

State intentionally lives in ignored ``batch_state/`` rather than a database.
The reaper's reservation and daily-cap files went with it (FR-01b): the
dispatcher settles each task's own worktree.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.orchestration.execution_safe_git import primary_repository
from scripts.orchestration.execution_safe_git import run_git as safe_git

_STATE_RELATIVE = Path("batch_state") / "worktree-reaper"
_JOURNAL_NAME = "journal.jsonl"
DEFAULT_GIT_TIMEOUT_SECONDS = 30.0


def utc_now() -> datetime:
    return datetime.now(UTC)


def _state_dir(repo_root: Path) -> Path:
    return repo_root / _STATE_RELATIVE


def journal_path(repo_root: Path) -> Path:
    return _state_dir(repo_root) / _JOURNAL_NAME


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def append_journal(repo_root: Path, event: str, **evidence: Any) -> None:
    """Append one fsync'd event; journal failures must stop enforcement."""
    path = journal_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    row = {
        "schema_version": "worktree-reaper-journal.v1",
        "at": utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "event": event,
        **evidence,
    }
    with path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def create_recovery_ref(
    repo_root: Path,
    *,
    branch: str | None,
    head: str,
    timeout: float | None = None,
) -> tuple[str | None, str | None]:
    """Pin the exact pre-reap commit under a private local rescue ref.

    ``timeout`` overrides :data:`DEFAULT_GIT_TIMEOUT_SECONDS`. The reaper
    passes the time left on its locked-region deadline.
    """
    label = re.sub(r"[^A-Za-z0-9._/-]+", "-", branch or "detached").strip("./-")
    label = label or "detached"
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    ref = f"refs/reaper-rescue/{stamp}/{label}-{head[:12]}"
    bound = DEFAULT_GIT_TIMEOUT_SECONDS if timeout is None else timeout
    try:
        proc = safe_git(
            ["update-ref", ref, head],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=bound,
        )
    except subprocess.TimeoutExpired as exc:
        return None, f"git update-ref timed out after {bound:g}s: {exc}"
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout or "git update-ref failed").strip()
    return ref, None


def restore_worktree(
    repo_root: Path,
    *,
    recovery_ref: str,
    branch: str,
    worktree_path: Path,
) -> tuple[bool, str | None]:
    """Reconstruct a reaped dispatch worktree from its rescue ref.

    This deliberately never moves old directories: Git recreates the checkout
    from the recovery ref after the target and branch identity are verified.
    The shared checkout profile refuses transforming attributes before creation.
    """
    try:
        if primary_repository(repo_root) != repo_root.resolve():
            return False, "restore requires the primary repository"
    except (OSError, ValueError):
        return False, "restore requires the primary repository"
    target = worktree_path.resolve()
    try:
        target.relative_to((repo_root / ".worktrees").resolve())
    except ValueError:
        return False, "restore target is outside repo .worktrees/"
    if target.exists():
        return False, "restore target already exists"
    try:
        resolved = safe_git(
            ["rev-parse", "--verify", recovery_ref],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False, "recovery ref is unavailable (git rev-parse timed out)"
    if resolved.returncode != 0:
        return False, "recovery ref is unavailable"
    sha = (resolved.stdout or "").strip()
    try:
        branch_ref = safe_git(
            ["rev-parse", "--verify", f"refs/heads/{branch}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False, f"git rev-parse branch timed out after {DEFAULT_GIT_TIMEOUT_SECONDS:g}s"
    if branch_ref.returncode == 0 and (branch_ref.stdout or "").strip() != sha:
        return False, "branch no longer matches recovery ref"
    command = ["worktree", "add"]
    if branch_ref.returncode == 0:
        command.extend([str(target), branch])
    else:
        command.extend(["-b", branch, str(target), sha])
    try:
        proc = safe_git(
            command,
            cwd=repo_root,
            profile="checkout",
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return False, f"git worktree add timed out after {DEFAULT_GIT_TIMEOUT_SECONDS:g}s: {exc}"
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "git worktree add failed").strip()
    return True, None
