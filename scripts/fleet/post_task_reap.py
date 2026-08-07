#!/usr/bin/env python3
"""Safe post-task reaper for dispatch worktrees.

Reaps the dispatch worktree bound to one task_id only after the task is terminal
and the worktree is clean.  Optional ACP runtime-review paths are reaped only
when the owning task is terminal, the path can be bound to that task, and no
live process holds the path.

Default mode is dry-run; pass --apply to delete anything.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from scripts.common.repo_root import main_checkout_root

ROOT = main_checkout_root(Path(__file__).resolve().parents[2])
_TASKS_DIR = ROOT / "batch_state" / "tasks"
_DISPATCH_WORKTREES_ROOT = ROOT / ".worktrees" / "dispatch"
_ACP_RUNTIME_ROOT = _DISPATCH_WORKTREES_ROOT / "acp"

_ACTIVE_STATUSES = frozenset({"spawning", "running"})
_TERMINAL_STATUSES = frozenset(
    {
        "done",
        "failed",
        "timeout",
        "rate_limited",
        "cancelled",
        "crashed",
        "dry_run",
        "needs_finalize",
        "no_deliverable",
    }
)

_GIT_ENV_DENYLIST = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_COMMON_DIR",
}


def _sanitized_git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_ENV_DENYLIST and not key.startswith("PRE_COMMIT")
    }


def _run_git(
    args: list[str],
    *,
    cwd: Path,
    timeout: int | None = 30,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
        env=_sanitized_git_env(),
    )


def _load_task_state(tasks_dir: Path, task_id: str) -> dict[str, Any] | None:
    safe = task_id.replace("/", "_").replace("\\", "_")
    path = tasks_dir / f"{safe}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _worktree_path_from_state(state: dict[str, Any]) -> Path | None:
    """Return the bound worktree path recorded in task state, if any."""
    for key in ("worktree_path", "cwd"):
        value = state.get(key)
        if value:
            try:
                return Path(str(value)).resolve()
            except OSError:
                continue
    return None


def _is_under_dispatch_worktrees(path: Path) -> bool:
    """True for paths inside .worktrees/dispatch/ but outside the ACP runtime subtree."""
    try:
        rel = path.resolve().relative_to(_DISPATCH_WORKTREES_ROOT)
    except ValueError:
        return False
    return rel.parts[:1] != ("acp",)


def _is_registered_worktree(path: Path, repo_root: Path) -> bool:
    """True when path is a registered git worktree."""
    proc = _run_git(["worktree", "list", "--porcelain"], cwd=repo_root)
    if proc.returncode != 0:
        return False
    resolved = path.resolve()
    for line in (proc.stdout or "").splitlines():
        if line.startswith("worktree "):
            candidate = Path(line[len("worktree ") :].strip()).resolve()
            if candidate == resolved:
                return True
    return False


def _worktree_is_dirty(path: Path) -> bool | None:
    proc = _run_git(["status", "--porcelain"], cwd=path)
    if proc.returncode != 0:
        return None
    return bool((proc.stdout or "").strip())


def _git_worktree_is_locked(path: Path, repo_root: Path) -> bool:
    """Return True if git reports the worktree as locked.  Fail closed."""
    proc = _run_git(["worktree", "list", "--porcelain"], cwd=repo_root)
    if proc.returncode != 0:
        return True
    resolved = path.resolve()
    entry_path: Path | None = None
    locked = False
    for line in (proc.stdout or "").splitlines():
        if line.startswith("worktree "):
            if entry_path == resolved:
                return locked
            entry_path = Path(line[len("worktree ") :].strip()).resolve()
            locked = False
        elif line.startswith("locked"):
            locked = True
    if entry_path == resolved:
        return locked
    return True


def _is_path_held_by_process(path: Path) -> bool:
    """Return True if a live process appears to hold ``path``.

    Prefers ``lsof`` on the directory.  When lsof is unavailable or fails,
    falls back to the git worktree lock bit as a conservative proxy.
    """
    try:
        proc = subprocess.run(
            ["lsof", "+D", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        return _git_worktree_is_locked(path, ROOT)
    if proc.returncode != 0:
        return _git_worktree_is_locked(path, ROOT)
    return any(line and not line.startswith("COMMAND") for line in (proc.stdout or "").splitlines())


def _remove_worktree(path: Path, repo_root: Path, *, force: bool = True) -> tuple[bool, str | None]:
    cmd = ["worktree", "remove"]
    if force:
        cmd.append("--force")
    cmd.append(str(path))
    proc = _run_git(cmd, cwd=repo_root)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "git worktree remove failed").strip()
        return False, detail
    if path.exists():
        return False, f"worktree path still exists after remove: {path}"
    return True, None


def _safe_label(task_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", task_id).strip("-._")[:32]


def _find_acp_runtime_worktrees(task_id: str) -> list[Path]:
    """Find ACP runtime worktrees whose name binds them to task_id.

    Actual ACP execution worktrees are named ``runtime-{label}-{uuid}``.  The
    skill text also references ``runtime-review-*`` prefixes; we include both
    shapes but never return paths by prefix alone -- the caller must still
    require task terminal status and a dead process before reaping.
    """
    root = _ACP_RUNTIME_ROOT
    if not root.is_dir():
        return []
    label = _safe_label(task_id)
    candidates: list[Path] = []
    for path in root.iterdir():
        if not path.is_dir():
            continue
        name = path.name
        if name.startswith(f"runtime-{label}-") or (name.startswith("runtime-review-") and label in name):
            candidates.append(path)
    return candidates


def _reap_main_worktree(
    *,
    task_id: str,
    state: dict[str, Any],
    repo_root: Path,
    apply: bool,
) -> dict[str, Any]:
    """Evaluate and optionally reap the dispatch worktree bound to task_id."""
    status = state.get("status")
    status_str = str(status) if status is not None else None

    if status_str in _ACTIVE_STATUSES or status_str in (None, ""):
        return {
            "path": None,
            "action": "retained",
            "reason": f"task still active (status={status_str})",
            "error": None,
        }
    if status_str not in _TERMINAL_STATUSES:
        return {
            "path": None,
            "action": "retained",
            "reason": f"task status not terminal (status={status_str})",
            "error": None,
        }

    bound_path = _worktree_path_from_state(state)
    if bound_path is None:
        return {
            "path": None,
            "action": "retained",
            "reason": "unknown ownership: no worktree_path/cwd in task state",
            "error": None,
        }

    if not bound_path.exists():
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "bound worktree path does not exist",
            "error": None,
        }

    if not _is_under_dispatch_worktrees(bound_path):
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "unknown ownership: path is outside .worktrees/dispatch/",
            "error": None,
        }

    if not _is_registered_worktree(bound_path, repo_root):
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "unknown ownership: path is not a registered git worktree",
            "error": None,
        }

    dirty = _worktree_is_dirty(bound_path)
    if dirty is None:
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "unable to determine worktree cleanliness",
            "error": None,
        }
    if dirty:
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "worktree has uncommitted changes",
            "error": None,
        }

    if not apply:
        return {
            "path": str(bound_path),
            "action": "would_remove",
            "reason": f"task terminal (status={status_str}) and worktree clean",
            "error": None,
        }

    ok, error = _remove_worktree(bound_path, repo_root)
    return {
        "path": str(bound_path),
        "action": "removed" if ok else "error",
        "reason": f"task terminal (status={status_str}) and worktree clean",
        "error": error,
    }


def _reap_acp_runtime_worktrees(
    *,
    task_id: str,
    state: dict[str, Any],
    repo_root: Path,
    apply: bool,
) -> list[dict[str, Any]]:
    """Evaluate and optionally reap finished ACP runtime-review worktrees."""
    status = state.get("status")
    status_str = str(status) if status is not None else None

    if status_str in _ACTIVE_STATUSES or status_str in (None, ""):
        return []
    if status_str not in _TERMINAL_STATUSES:
        return []

    results: list[dict[str, Any]] = []
    for path in _find_acp_runtime_worktrees(task_id):
        if not _is_registered_worktree(path, repo_root):
            results.append(
                {
                    "path": str(path),
                    "action": "retained",
                    "reason": "unknown ownership: not a registered git worktree",
                    "error": None,
                }
            )
            continue

        if _is_path_held_by_process(path):
            results.append(
                {
                    "path": str(path),
                    "action": "retained",
                    "reason": "live process holds path",
                    "error": None,
                }
            )
            continue

        if not apply:
            results.append(
                {
                    "path": str(path),
                    "action": "would_remove",
                    "reason": "task terminal and process gone",
                    "error": None,
                }
            )
            continue

        ok, error = _remove_worktree(path, repo_root)
        results.append(
            {
                "path": str(path),
                "action": "removed" if ok else "error",
                "reason": "task terminal and process gone",
                "error": error,
            }
        )
    return results


def post_task_reap(
    task_id: str,
    *,
    tasks_dir: Path = _TASKS_DIR,
    repo_root: Path = ROOT,
    apply: bool = False,
    include_acp_runtime: bool = True,
) -> dict[str, Any]:
    """Return a reap report for ``task_id``; delete only when ``apply`` is True."""
    state = _load_task_state(tasks_dir, task_id)
    if state is None:
        return {
            "task_id": task_id,
            "task_status": None,
            "apply": apply,
            "main_worktree": {
                "path": None,
                "action": "retained",
                "reason": "no task state file found",
                "error": None,
            },
            "acp_runtimes": [],
            "errors": [],
        }

    main_result = _reap_main_worktree(
        task_id=task_id,
        state=state,
        repo_root=repo_root,
        apply=apply,
    )
    acp_results: list[dict[str, Any]] = []
    if include_acp_runtime:
        acp_results = _reap_acp_runtime_worktrees(
            task_id=task_id,
            state=state,
            repo_root=repo_root,
            apply=apply,
        )

    errors: list[str] = []
    if main_result.get("error"):
        errors.append(f"main worktree: {main_result['error']}")
    for item in acp_results:
        if item.get("error"):
            errors.append(f"acp runtime {item['path']}: {item['error']}")

    return {
        "task_id": task_id,
        "task_status": state.get("status"),
        "apply": apply,
        "main_worktree": main_result,
        "acp_runtimes": acp_results,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True, help="Task id whose worktree should be reaped")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually remove worktrees (default: dry-run)",
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=_TASKS_DIR,
        help="batch_state/tasks directory",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="Repository root (primary checkout)",
    )
    parser.add_argument(
        "--include-acp-runtime",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Also evaluate ACP runtime-review worktrees bound to the task (default: on)",
    )
    args = parser.parse_args(argv)

    report = post_task_reap(
        args.task_id,
        tasks_dir=args.tasks_dir,
        repo_root=args.repo_root,
        apply=args.apply,
        include_acp_runtime=args.include_acp_runtime,
    )

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
