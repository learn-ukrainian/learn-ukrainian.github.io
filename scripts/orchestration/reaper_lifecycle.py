"""Durable, fail-closed state for the merged-worktree reaper.

State intentionally lives in ignored ``batch_state/`` rather than a database:
the JSONL journal is append-only, while the small pending/cap files provide the
atomic coordination needed around a destructive ``git worktree remove``.
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

_STATE_RELATIVE = Path("batch_state") / "worktree-reaper"
_PENDING_NAME = "reap-pending.json"
_CAP_NAME = "first-class-cap.json"
_JOURNAL_NAME = "journal.jsonl"
_FIRST_CLASS_DAYS = 7
_DEFAULT_MAX_REAPS_PER_DAY = 10


def utc_now() -> datetime:
    return datetime.now(UTC)


def _state_dir(repo_root: Path) -> Path:
    return repo_root / _STATE_RELATIVE


def journal_path(repo_root: Path) -> Path:
    return _state_dir(repo_root) / _JOURNAL_NAME


def pending_path(repo_root: Path) -> Path:
    return _state_dir(repo_root) / _PENDING_NAME


def _cap_path(repo_root: Path) -> Path:
    return _state_dir(repo_root) / _CAP_NAME


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _read_mapping(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


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


def mark_reap_pending(
    repo_root: Path,
    *,
    worktree_path: Path,
    branch: str | None,
    head: str | None,
    task_id: str | None,
) -> None:
    """Atomically reserve a path before its final deletion checks.

    Consumers that bind dispatch paths can call :func:`is_reap_pending` and
    refuse reuse while this reservation exists.  The reaper clears it after a
    terminal remove or any abort path.
    """
    path = pending_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        try:
            current = json.load(handle)
        except json.JSONDecodeError:
            current = {}
        if not isinstance(current, dict):
            current = {}
        entries = current.get("paths")
        if not isinstance(entries, dict):
            entries = {}
        entries[str(worktree_path.resolve())] = {
            "branch": branch,
            "head": head,
            "task_id": task_id,
            "marked_at": utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
        _atomic_write(path, {"schema_version": "worktree-reaper-pending.v1", "paths": entries})
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def clear_reap_pending(repo_root: Path, worktree_path: Path) -> None:
    path = pending_path(repo_root)
    if not path.exists():
        return
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        try:
            current = json.load(handle)
        except json.JSONDecodeError:
            current = {}
        entries = current.get("paths") if isinstance(current, dict) else None
        if isinstance(entries, dict):
            entries.pop(str(worktree_path.resolve()), None)
            _atomic_write(path, {"schema_version": "worktree-reaper-pending.v1", "paths": entries})
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def is_reap_pending(repo_root: Path, worktree_path: Path) -> bool:
    entries = _read_mapping(pending_path(repo_root)).get("paths")
    return isinstance(entries, dict) and str(worktree_path.resolve()) in entries


def _max_reaps_per_day() -> int:
    raw = os.environ.get("LU_REAPER_MAX_REAPS_PER_DAY")
    if raw is None:
        return _DEFAULT_MAX_REAPS_PER_DAY
    try:
        parsed = int(raw)
    except ValueError:
        return _DEFAULT_MAX_REAPS_PER_DAY
    return max(0, parsed)


def cap_allows_reap(repo_root: Path, *, now: datetime | None = None) -> tuple[bool, str | None]:
    """Apply the first-seven-days daily cap unless the policy flag lifts it."""
    if os.environ.get("LU_REAPER_LIFT_FIRST_CLASS_CAP") == "1":
        return True, None
    current = now or utc_now()
    state = _read_mapping(_cap_path(repo_root))
    enabled_raw = state.get("enabled_at")
    try:
        enabled_at = datetime.fromisoformat(str(enabled_raw).replace("Z", "+00:00"))
    except ValueError:
        enabled_at = current
    if (current - enabled_at).days >= _FIRST_CLASS_DAYS:
        return True, None
    counts = state.get("counts")
    count = counts.get(current.date().isoformat(), 0) if isinstance(counts, dict) else 0
    if isinstance(count, int) and count >= _max_reaps_per_day():
        return False, f"first-class daily reap cap reached ({_max_reaps_per_day()})"
    return True, None


def record_reap_for_cap(repo_root: Path, *, now: datetime | None = None) -> None:
    current = now or utc_now()
    path = _cap_path(repo_root)
    state = _read_mapping(path)
    counts = state.get("counts") if isinstance(state.get("counts"), dict) else {}
    day = current.date().isoformat()
    previous = counts.get(day, 0)
    counts[day] = previous + 1 if isinstance(previous, int) else 1
    state = {
        "schema_version": "worktree-reaper-first-class-cap.v1",
        "enabled_at": state.get("enabled_at")
        or current.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "counts": counts,
    }
    _atomic_write(path, state)


def create_recovery_ref(
    repo_root: Path,
    *,
    branch: str | None,
    head: str,
) -> tuple[str | None, str | None]:
    """Pin the exact pre-reap commit under a private local rescue ref."""
    label = re.sub(r"[^A-Za-z0-9._/-]+", "-", branch or "detached").strip("./-")
    label = label or "detached"
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    ref = f"refs/reaper-rescue/{stamp}/{label}-{head[:12]}"
    proc = subprocess.run(
        ["git", "update-ref", ref, head],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
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
    """
    target = worktree_path.resolve()
    try:
        target.relative_to((repo_root / ".worktrees").resolve())
    except ValueError:
        return False, "restore target is outside repo .worktrees/"
    if target.exists():
        return False, "restore target already exists"
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", recovery_ref],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if resolved.returncode != 0:
        return False, "recovery ref is unavailable"
    sha = (resolved.stdout or "").strip()
    branch_ref = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/heads/{branch}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if branch_ref.returncode == 0 and (branch_ref.stdout or "").strip() != sha:
        return False, "branch no longer matches recovery ref"
    command = ["git", "worktree", "add"]
    if branch_ref.returncode == 0:
        command.extend([str(target), branch])
    else:
        command.extend(["-b", branch, str(target), sha])
    proc = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "git worktree add failed").strip()
    return True, None
