#!/usr/bin/env python3
"""Safe post-task reaper for dispatch worktrees.

Reaps the dispatch worktree bound to one task_id only after the task is terminal,
the worktree is clean, and (when a PID is recorded) the process is dead.  ACP
runtime paths are reaped only when they are explicitly listed in the task state
(``acp_runtime_paths``), the task is terminal, the path is clean, and no live
process holds it.

A terminal dispatch worktree is reaped even when its task never opened a GitHub
PR (measure-only, timeout, cancelled, …) as long as ownership, cleanliness, and
dead-PID guards all hold and no open PR is present.  The deletion itself always
goes through the canonical P0 reaper boundary.

Default mode is dry-run; pass --apply to delete anything.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from scripts.common.repo_root import main_checkout_root
from scripts.common.task_store_paths import tasks_dir as default_tasks_dir
from scripts.fleet import ignored_task_output, pr_identity
from scripts.orchestration import reap_worktrees, reaper_lifecycle, worktree_claims
from scripts.orchestration.execution_safe_git import run_git as safe_git

ROOT = main_checkout_root(Path(__file__).resolve().parents[2])
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
    return safe_git(
        args,
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


def _worktree_path_from_state(state: dict[str, Any], *, repo_root: Path) -> Path | None:
    """Return the bound worktree path recorded in task state, if any."""
    for key in ("worktree_path", "cwd"):
        value = state.get(key)
        if value:
            try:
                return worktree_claims.resolve_claim_path(str(value), repo_root=repo_root)
            except (OSError, ValueError, RuntimeError):
                continue
    return None


def _acp_runtime_paths_from_state(state: dict[str, Any]) -> list[Path]:
    """Return ACP runtime paths explicitly bound to this task in state.

    Paths are taken from ``acp_runtime_paths`` (a list of strings).  Name or
    substring matching is never used; an unbound path is not ours to reap.
    """
    raw = state.get("acp_runtime_paths")
    if not isinstance(raw, list):
        return []
    candidates: list[Path] = []
    for item in raw:
        if not item:
            continue
        try:
            candidates.append(Path(str(item)).resolve())
        except OSError:
            continue
    return candidates


def _is_under_dispatch_worktrees(path: Path) -> bool:
    """True for paths inside .worktrees/dispatch/ but outside the ACP runtime subtree."""
    try:
        rel = path.resolve().relative_to(_DISPATCH_WORKTREES_ROOT)
    except ValueError:
        return False
    return rel.parts[:1] != ("acp",)


def _acp_runtime_root(repo_root: Path) -> Path:
    """Return the dedicated ACP-runtime subtree for one repository root."""
    return repo_root.resolve() / ".worktrees" / "dispatch" / "acp"


def _is_under_acp_runtime_root(path: Path, repo_root: Path = ROOT) -> bool:
    """True for paths inside .worktrees/dispatch/acp/."""
    runtime_root = _acp_runtime_root(repo_root).resolve()
    try:
        resolved_path = path.resolve()
        resolved_path.relative_to(runtime_root)
    except ValueError:
        return False
    return resolved_path != runtime_root


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


def _worktree_is_dirty(path: Path, *, ignore_deleted_tracked: bool = False) -> bool | None:
    proc = _run_git(["status", "--porcelain"], cwd=path)
    if proc.returncode != 0:
        return None
    lines = [line for line in (proc.stdout or "").splitlines() if line.strip()]
    if ignore_deleted_tracked:
        # No-checkout ACP runtime worktrees report every tracked file as deleted.
        # Ignore those baseline deletions; flag only untracked/modified additions.
        lines = [line for line in lines if not (line[0] == "D" or line[1] == "D")]
    return bool(lines)


def _git_worktree_lock_reason(path: Path, repo_root: Path) -> str | None:
    """Return git's lock reason for the worktree, or None when it is unlocked.

    A lock without a reason is ``""``. Fail closed: when git cannot list the
    worktree, it is reported as locked with reason ``""``.
    """
    proc = _run_git(["worktree", "list", "--porcelain"], cwd=repo_root)
    if proc.returncode != 0:
        return ""
    resolved = path.resolve()
    entry_path: Path | None = None
    lock_reason: str | None = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith("worktree "):
            if entry_path == resolved:
                return lock_reason
            entry_path = Path(line[len("worktree ") :].strip()).resolve()
            lock_reason = None
        elif line == "locked" or line.startswith("locked "):
            lock_reason = line.removeprefix("locked").strip()
    if entry_path == resolved:
        return lock_reason
    return ""


def _pid_alive(pid: int) -> bool | None:
    """Return True if ``pid`` is alive, False if dead, None if probe failed.

    Fail-closed callers must treat ``None`` as 'retain'.
    """
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return None
    return True


def _probe_path_liveness(path: Path) -> bool | None:
    """Return True if a live process holds ``path``, False if not, None on error.

    Uses ``lsof +D`` when available.  Any probe failure (missing binary, timeout,
    nonzero exit, or subprocess error) returns ``None`` so the caller can fail
    closed and retain the path.
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
        return None
    if proc.returncode != 0:
        return None
    return any(line and not line.startswith("COMMAND") for line in (proc.stdout or "").splitlines())


def _remove_acp_runtime_worktree(
    path: Path,
    *,
    task_id: str,
    tasks_dir: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Force-remove one state-bound ACP runtime through the guarded chokepoint (#8610).

    This is deliberately not the regular dispatch deletion path: callers must
    first establish terminal task ownership, cleanliness, and no live process.
    Regular dispatch worktrees always go through ``reap_worktrees`` instead.
    Under the per-worktree lock dispatch attaches under, the chokepoint
    re-proves the runtime lies beneath ``.worktrees/dispatch/acp/`` and is
    clean, refuses while another task's unfinished record names it, and only
    then lifts the runtime's git lock and removes it.
    """
    reason = "task terminal, path clean, and process gone"

    def releasable() -> tuple[bool, str]:
        if not _is_under_acp_runtime_root(path, repo_root):
            return False, "ACP runtime path is outside .worktrees/dispatch/acp/"
        return True, ""

    removal = worktree_claims.remove_unclaimed_worktree(
        path,
        repo_root=repo_root,
        reason=reason,
        owner_task_id=task_id,
        releasable=releasable,
        force=True,
        dirty_probe=lambda runtime: _worktree_is_dirty(runtime, ignore_deleted_tracked=True),
        unlock=True,
        tasks_dir=tasks_dir,
    )
    if removal.action == "skipped":
        return {
            "path": str(path),
            "action": "retained",
            "reason": removal.reason,
            "error": None,
            **({"preserved_artifacts": removal.preserved_artifacts} if removal.preserved_artifacts is not None else {}),
        }
    if removal.action == "removed" and path.exists():
        return {
            "path": str(path),
            "action": "error",
            "reason": reason,
            "error": f"worktree path still exists after remove: {path}",
        }
    return {
        "path": str(path),
        "action": removal.action,
        "reason": reason,
        "error": removal.error,
        "preserved_artifacts": removal.preserved_artifacts,
    }


def _parse_state_pid(state: dict[str, Any]) -> int | None:
    """Return a positive integer PID from task state, or None."""
    raw = state.get("pid")
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw if raw > 0 else None
    if isinstance(raw, str) and raw.isdigit():
        return int(raw) if int(raw) > 0 else None
    return None


def _reap_main_worktree(
    *,
    task_id: str,
    state: dict[str, Any],
    repo_root: Path,
    apply: bool,
    tasks_dir: Path | None = None,
) -> dict[str, Any]:
    """Evaluate and optionally reap the dispatch worktree bound to task_id."""
    tasks_dir = default_tasks_dir() if tasks_dir is None else tasks_dir
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

    bound_path = _worktree_path_from_state(state, repo_root=repo_root)
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

    state_task_id = state.get("task_id")
    if state_task_id not in (None, task_id):
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "unknown ownership: task-state task_id does not match requested task",
            "error": None,
        }
    try:
        relative = bound_path.relative_to(_DISPATCH_WORKTREES_ROOT)
    except ValueError:  # guarded above; retain if the filesystem changed.
        relative = ()
    expected_agent = str(state.get("agent") or "")
    reuse_matches = []
    if len(relative.parts) == 2 and relative.parts[1] != task_id:
        try:
            reuse_matches = ignored_task_output.matching_worktree_records(
                bound_path, tasks_dir, repo_root=repo_root, publish_cache=False
            )
            _, creator = ignored_task_output.reused_worktree_creator(
                reuse_matches, bound_path, repo_root=repo_root, tasks_dir=tasks_dir
            )
            if creator != state or creator.get("task_id") != task_id or len(reuse_matches) < 2:
                reuse_matches = []
        except (OSError, ValueError, RuntimeError):
            reuse_matches = []
    if (
        len(relative.parts) != 2
        or (relative.parts[1] != task_id and not reuse_matches)
        or not expected_agent
        or relative.parts[0] != expected_agent
    ):
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "unknown ownership: task binding does not match dispatch path",
            "error": None,
        }

    if not _is_registered_worktree(bound_path, repo_root):
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "unknown ownership: path is not a registered git worktree",
            "error": None,
        }

    lock_reason = _git_worktree_lock_reason(bound_path, repo_root)
    if (
        lock_reason == "initializing"
        and state.get("pid", False) is None
        and isinstance(state.get("worktree_prep"), dict)
    ):
        # #8663: this task's ``git worktree add`` was stopped and left the
        # worktree under git's ``initializing`` lock. It is never removed
        # automatically; the canonical P0 reaper's report-only class returns
        # the ``needs_attention`` evidence and journals it.
        row = _reap_via_canonical(
            repo_root=repo_root,
            bound_path=bound_path,
            apply=apply,
            include_terminal_dispatches=True,
        )
        if row is None:
            return {
                "path": str(bound_path),
                "action": "retained",
                "reason": "canonical P0 reaper did not evaluate bound path",
                "error": None,
            }
        return row
    if lock_reason is not None:
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "registered worktree is locked",
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

    pid = _parse_state_pid(state)
    if pid is not None:
        alive = _pid_alive(pid)
        if alive is True:
            return {
                "path": str(bound_path),
                "action": "retained",
                "reason": f"live process holds worktree (pid={pid})",
                "error": None,
            }
        if alive is None:
            return {
                "path": str(bound_path),
                "action": "retained",
                "reason": f"liveness probe failed for recorded pid={pid}",
                "error": None,
            }

    retrieval = _retrieve_retained_reuse(
        task_id, state, bound_path, tasks_dir=tasks_dir, repo_root=repo_root, apply=apply
    )
    if retrieval is not None:
        return retrieval

    row = _reap_via_canonical(
        repo_root=repo_root,
        bound_path=bound_path,
        apply=apply,
        include_terminal_dispatches=True,
    )
    if row is None:
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "canonical P0 reaper did not evaluate bound path",
            "error": None,
        }

    # The canonical reaper only reaps a settled dispatch without a PR when its
    # active-task API probe succeeds and the status is in its narrow terminal
    # set (done/failed/no_deliverable).  post_task_reap has already proven the
    # broader terminal contract itself: status is terminal, the bound tree is
    # clean, and the recorded PID is dead.  When the canonical reaper declines
    # solely because no GitHub PR qualifies, drive the same guarded deletion
    # through its public success-worktree boundary, after re-proving that no
    # open PR appeared and (on apply) that no live process holds the tree.
    if row["action"] == "skipped" and row["reason"] == "no reap condition matched":
        return _reap_terminal_without_pr(
            task_id=task_id,
            status_str=status_str,
            bound_path=bound_path,
            row=row,
            repo_root=repo_root,
            apply=apply,
            branch=row.get("branch") or f"{expected_agent}/{task_id}",
        )
    return row


def _retrieve_retained_reuse(
    task_id: str, state: dict[str, Any], worktree: Path, *, tasks_dir: Path, repo_root: Path, apply: bool
) -> dict[str, Any] | None:
    """Retrieve a retained creator's bytes without relaxing any removal claim."""
    try:
        matches = ignored_task_output.matching_worktree_records(
            worktree, tasks_dir, repo_root=repo_root, publish_cache=False
        )
        if len(matches) < 2 or not any(record.get("keep_worktree") for _, record in matches):
            return None
        _, creator = ignored_task_output.reused_worktree_creator(
            matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir
        )
        if creator != state or creator.get("task_id") != task_id:
            raise ValueError("retained reuse output belongs to its creator")
        if not all(
            reap_worktrees._pid_proven_absent(record)
            for _, record in ignored_task_output._current_reuse_records(matches, tasks_dir)
        ):
            raise ValueError("retained reuse retrieval requires all recorded processes gone")
        receipt = creator.get("preserved_artifacts") or {
            "owner": task_id,
            "location": f"batch_state/preserved/{task_id}/<retrieval-attempt>",
        }
        reason = "would retrieve retained reuse output; creator must release retention before reap"
        if apply:
            with worktree_claims.worktree_lock(worktree, lock_dir=worktree_claims.repository_lock_dir(repo_root)):
                current = ignored_task_output.matching_worktree_records(
                    worktree, tasks_dir, repo_root=repo_root, publish_cache=False
                )
                if current != matches or not all(
                    reap_worktrees._pid_proven_absent(record)
                    for _, record in ignored_task_output._current_reuse_records(current, tasks_dir)
                ):
                    raise ValueError("retained reuse records or processes changed")
                _, reason, receipt = ignored_task_output.preserve_worktree_artifacts(
                    worktree,
                    primary=worktree_claims.control_plane_root(repo_root),
                    task_id=task_id,
                    tasks_dir=tasks_dir,
                    repo_root=repo_root,
                )
        return {
            "path": str(worktree),
            "action": "retained",
            "reason": reason,
            "error": None,
            "preserved_artifacts": receipt,
        }
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        return {
            "path": str(worktree),
            "action": "retained",
            "reason": "retained reuse retrieval refused: ownership, record or process proof unavailable",
            "error": None,
        }


def _reap_via_canonical(
    *,
    repo_root: Path,
    bound_path: Path,
    apply: bool,
    include_terminal_dispatches: bool,
) -> dict[str, Any] | None:
    """Delegate to the canonical P0 reaper for one bound dispatch worktree."""
    try:
        rows = reap_worktrees.reap_worktrees(
            repo_root=repo_root,
            apply=apply,
            preserve_then_reap=False,
            prune_merged_branches=True,
            target_paths=[bound_path],
            merged_pr_only=True,
            include_terminal_dispatches=include_terminal_dispatches,
            require_activity_probe=apply,
        )
    except RuntimeError as exc:
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "canonical P0 reaper guard failed",
            "error": str(exc),
        }
    if not rows:
        return None
    row = rows[0]
    return {
        "path": row.path,
        "action": row.action,
        "reason": row.reason,
        "error": row.error,
        "pr": row.pr,
        "recovery_ref": row.recovery_ref,
        "branch": row.branch,
        "needs_attention": row.needs_attention,
        "preserved_artifacts": row.preserved_artifacts,
    }


def _no_open_pr_for_branch(
    *,
    repo_root: Path,
    branch: str | None,
) -> tuple[bool, str | None]:
    """Return (no_open_pr, failure) for the branch that owns the bound tree.

    PR identity binding lives in one shared probe (scripts.fleet.pr_identity,
    #7127) — the same binding hramatka_hygiene_check uses — so the reaper and
    the closeout gate cannot drift apart again.  This caller keeps only its
    fail-closed direction: an unknown answer retains the worktree instead of
    deleting it.
    """
    if not branch:
        return False, "no branch identity to probe for an open PR"
    repo = pr_identity.resolve_repo_slug(repo_root)
    has_open_pr, error = pr_identity.probe_open_pr_for_branch(
        repo_root=repo_root,
        repo=repo,
        branch=branch,
    )
    if has_open_pr is None:
        return False, f"PR guard unavailable; {error}"
    return not has_open_pr, None


def _reap_terminal_without_pr(
    *,
    task_id: str,
    status_str: str,
    bound_path: Path,
    row: dict[str, Any],
    repo_root: Path,
    apply: bool,
    branch: str | None,
) -> dict[str, Any]:
    """Reap a clean, dead-PID, dispatch-layout worktree that never had a PR."""
    reason = f"settled dispatch task-id={task_id} status={status_str}"

    no_open_pr, guard_error = _no_open_pr_for_branch(repo_root=repo_root, branch=branch)
    if guard_error is not None:
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": guard_error,
            "error": None,
        }
    if not no_open_pr:
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "open PR present for bound worktree branch",
            "error": None,
        }

    if not reap_worktrees._is_head_reachable_from_remote(bound_path):
        return {
            "path": str(bound_path),
            "action": "skipped",
            "reason": "unpushed_head",
            "error": None,
        }

    if apply:
        live_cwds = reap_worktrees.live_cwds_for_reap(repo_root, bound_path, reap_worktrees._live_cwd_paths(repo_root))
        if live_cwds is None:
            return {
                "path": str(bound_path),
                "action": "retained",
                "reason": "process-CWD activity probe unavailable",
                "error": None,
            }
        resolved = bound_path.resolve()
        if any(_cwd_within(Path(cwd), resolved) for cwd in live_cwds):
            return {
                "path": str(bound_path),
                "action": "retained",
                "reason": "live process holds worktree",
                "error": None,
            }

    try:
        result = reap_worktrees.reap_success_worktree(
            repo_root=repo_root,
            worktree_path=bound_path,
            reason=reason,
            apply=apply,
        )
    except RuntimeError as exc:
        return {
            "path": str(bound_path),
            "action": "retained",
            "reason": "canonical P0 reaper guard failed",
            "error": str(exc),
        }
    return {
        "path": result.path,
        "action": result.action,
        "reason": result.reason,
        "error": result.error,
        "pr": result.pr,
        "recovery_ref": result.recovery_ref,
        "preserved_artifacts": result.preserved_artifacts,
    }


def _cwd_within(cwd: Path, worktree: Path) -> bool:
    try:
        cwd.resolve().relative_to(worktree)
    except ValueError:
        return False
    return True


def _reap_acp_runtime_worktrees(
    *,
    task_id: str,
    state: dict[str, Any],
    tasks_dir: Path,
    repo_root: Path,
    apply: bool,
) -> list[dict[str, Any]]:
    """Evaluate and optionally reap ACP runtime worktrees bound in task state."""
    status = state.get("status")
    status_str = str(status) if status is not None else None

    if status_str in _ACTIVE_STATUSES or status_str in (None, ""):
        return []
    if status_str not in _TERMINAL_STATUSES:
        return []

    results: list[dict[str, Any]] = []
    for path in _acp_runtime_paths_from_state(state):
        if not path.exists():
            results.append(
                {
                    "path": str(path),
                    "action": "retained",
                    "reason": "bound ACP runtime path does not exist",
                    "error": None,
                }
            )
            continue

        if not _is_under_acp_runtime_root(path, repo_root):
            results.append(
                {
                    "path": str(path),
                    "action": "retained",
                    "reason": "unknown ownership: outside .worktrees/dispatch/acp/",
                    "error": None,
                }
            )
            continue

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

        dirty = _worktree_is_dirty(path, ignore_deleted_tracked=True)
        if dirty is None:
            results.append(
                {
                    "path": str(path),
                    "action": "retained",
                    "reason": "unable to determine worktree cleanliness",
                    "error": None,
                }
            )
            continue
        if dirty:
            results.append(
                {
                    "path": str(path),
                    "action": "retained",
                    "reason": "worktree has uncommitted changes",
                    "error": None,
                }
            )
            continue

        liveness = _probe_path_liveness(path)
        if liveness is True:
            results.append(
                {
                    "path": str(path),
                    "action": "retained",
                    "reason": "live process holds path",
                    "error": None,
                }
            )
            continue
        if liveness is None:
            results.append(
                {
                    "path": str(path),
                    "action": "retained",
                    "reason": "liveness probe failed",
                    "error": None,
                }
            )
            continue

        if not apply:
            results.append(
                {
                    "path": str(path),
                    "action": "would_remove",
                    "reason": "task terminal, path clean, and process gone",
                    "error": None,
                }
            )
            continue

        results.append(_remove_acp_runtime_worktree(path, task_id=task_id, tasks_dir=tasks_dir, repo_root=repo_root))
    return results


def post_task_reap(
    task_id: str,
    *,
    tasks_dir: Path | None = None,
    repo_root: Path = ROOT,
    apply: bool = False,
    include_acp_runtime: bool = True,
    release_retention: bool = False,
) -> dict[str, Any]:
    """Return a reap report for ``task_id``; delete only when ``apply`` is True."""
    tasks_dir = tasks_dir or default_tasks_dir()
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
                "preserved_artifacts": {
                    "retention_disposition": "retained",
                    "owner": "infra lane",
                    "next_condition": "establish canonical task attribution before removal",
                },
            },
            "acp_runtimes": [],
            "errors": ["retention release requires an existing task state"] if release_retention else [],
            "needs_attention": [],
        }

    if release_retention:
        refusal = _release_retention(task_id, tasks_dir=tasks_dir, repo_root=repo_root, apply=apply)
        if refusal:
            return {
                "task_id": task_id,
                "task_status": state.get("status"),
                "apply": apply,
                "main_worktree": {"action": "retained", "reason": refusal, "error": refusal},
                "acp_runtimes": [],
                "errors": [refusal],
                "needs_attention": [],
            }
        state = _load_task_state(tasks_dir, task_id)

    main_result = _reap_main_worktree(
        task_id=task_id,
        state=state,
        repo_root=repo_root,
        apply=apply,
        tasks_dir=tasks_dir,
    )
    acp_results: list[dict[str, Any]] = []
    if include_acp_runtime:
        acp_results = _reap_acp_runtime_worktrees(
            task_id=task_id,
            state=state,
            tasks_dir=tasks_dir,
            repo_root=repo_root,
            apply=apply,
        )

    errors: list[str] = []
    if main_result.get("error"):
        errors.append(f"main worktree: {main_result['error']}")
    for item in acp_results:
        if item.get("error"):
            errors.append(f"acp runtime {item['path']}: {item['error']}")

    # Report-only findings (#8663): nothing acted on them; a human must.
    needs_attention = [
        {"path": item.get("path"), **item["needs_attention"]}
        for item in (main_result, *acp_results)
        if item.get("needs_attention")
    ]

    return {
        "task_id": task_id,
        "task_status": state.get("status"),
        "apply": apply,
        "main_worktree": main_result,
        "acp_runtimes": acp_results,
        "errors": errors,
        "needs_attention": needs_attention,
    }


def _finalized_reuse_proof(
    worktree: Path, matches: list[tuple[Path, dict[str, Any]]], *, repo_root: Path
) -> dict[str, Any] | None:
    """A done successor must have shipped the checkout's exact head; status alone is insufficient."""
    head = _run_git(["rev-parse", "HEAD"], cwd=worktree)
    if head.returncode != 0:
        return None
    for _, record in matches:
        if (
            record.get("worktree_reused") is True
            and record.get("status") == "done"
            and record.get("final_branch_head_commit") == head.stdout.strip()
            and reap_worktrees._needs_finalize_claim_proven_settled(repo_root, record) is not None
        ):
            return record
    return None


def _release_retention(task_id: str, *, tasks_dir: Path, repo_root: Path, apply: bool) -> str | None:
    """Release a creator's retrieved output and every settled reused successor.

    Worktree lock precedes all task-state locks. Validate the entire cohort
    before any writes; publish successors first and owner last so an interrupted
    release retains the owner's keep flag. Each record uses atomic replacement.
    """
    if not apply:
        return "retention release requires --apply"
    try:
        state = _load_task_state(tasks_dir, task_id)
        worktree = _worktree_path_from_state(state or {}, repo_root=repo_root)
        if worktree is None or not worktree.exists():
            return "retention release requires an existing bound worktree"
        # Network merge proof belongs outside the worktree lock. Recheck the
        # complete records, checkout head and worker absence under the locks.
        before = ignored_task_output.matching_worktree_records(
            worktree, tasks_dir, repo_root=repo_root, publish_cache=False
        )
        finalized = None
        if state.get("status") == "needs_finalize":
            ignored_task_output.reused_worktree_creator(before, worktree, repo_root=repo_root, tasks_dir=tasks_dir)
            finalized = _finalized_reuse_proof(worktree, before, repo_root=repo_root)
        with worktree_claims.worktree_lock(worktree, lock_dir=worktree_claims.repository_lock_dir(repo_root)):
            matches = ignored_task_output.matching_worktree_records(
                worktree,
                tasks_dir,
                repo_root=repo_root,
                publish_cache=worktree_claims.identity_cache_publication_allowed(worktree, tasks_dir),
            )
            if matches != before:
                return "retention release refused: task records changed"
            if len(matches) > 1:
                path, record = ignored_task_output.reused_worktree_creator(
                    matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir
                )
            else:
                path, record = matches[0] if matches else (None, {})
            if path is None or record.get("task_id") != task_id:
                return "retention release requires unambiguous owner attribution"
            receipt = record.get("preserved_artifacts", {})
            if (
                not isinstance(receipt, dict)
                or not receipt.get("retrieval_proof_sha256")
                or receipt.get("task_id") != task_id
                or receipt.get("run_nonce") != record.get("run_nonce")
            ):
                return "retention release requires an existing passing retrieval receipt"
            with contextlib.ExitStack() as stack:
                for member_path, member in sorted(matches):
                    stack.enter_context(ignored_task_output.artifacts.task_state_lock(member_path))
                    if json.loads(member_path.read_text(encoding="utf-8")) != member:
                        return "retention release refused: task records changed"
                    if (
                        not isinstance(member.get("task_id"), str)
                        or not member["task_id"].strip()
                        or not isinstance(member.get("run_nonce"), str)
                        or not member["run_nonce"].strip()
                    ):
                        return "retention release refused: task run identity unavailable"
                if (
                    ignored_task_output.matching_worktree_records(
                        worktree, tasks_dir, repo_root=repo_root, publish_cache=False
                    )
                    != matches
                ):
                    return "retention release refused: task records changed"

                def settled_creator(current: dict[str, Any]) -> bool:
                    # AC-03: a merged exact-head done successor completes this
                    # reuse case only. Never rewrite the creator's status.
                    head = _run_git(["rev-parse", "HEAD"], cwd=worktree)
                    return bool(
                        current == record
                        and finalized is not None
                        and head.returncode == 0
                        and head.stdout.strip() == finalized.get("final_branch_head_commit")
                        and reap_worktrees._pid_proven_absent(current)
                        and reap_worktrees._pid_proven_absent(finalized)
                    )

                refusal = worktree_claims.owner_release_refusal(
                    worktree,
                    owner_task_id=task_id,
                    tasks_dir=tasks_dir,
                    repo_root=repo_root,
                    settled_claim=settled_creator,
                )
                if refusal:
                    return refusal
                primary = worktree_claims.control_plane_root(repo_root)
                digest = ignored_task_output.verify_retrieval(primary, receipt)
                files = ignored_task_output._ignored_output_files(worktree, primary, record)
                if digest != receipt["retrieval_proof_sha256"] or digest != ignored_task_output._content_digest(
                    worktree, files
                ):
                    return "retention release requires retrieval of the current output bytes"
                release = {"owner": task_id, "run_nonce": record["run_nonce"], "retrieval_proof_sha256": digest}
                if finalized is not None:
                    release["finalized_by"] = {
                        "task_id": finalized["task_id"],
                        "run_nonce": finalized["run_nonce"],
                        "head_sha": finalized["final_branch_head_commit"],
                    }
                # A successor-only keep claim needs the same interruption guard:
                # reserve the creator before clearing successors, then release it last.
                if not record.get("keep_worktree") and any(member.get("keep_worktree") for _, member in matches):
                    reaper_lifecycle._atomic_write(path, dict(record, keep_worktree=True))
                # The owner is the final commit marker for a multi-record release.
                ordered = [match for match in matches if match[0] != path] + [(path, record)]
                for member_path, member in ordered:
                    if member_path != path and not member.get("keep_worktree"):
                        continue
                    member_receipt = dict(receipt)
                    member_receipt.update(
                        {
                            "owner": task_id,
                            "retrieval_owner": {"task_id": task_id, "run_nonce": record["run_nonce"]},
                            "task_id": member["task_id"],
                            "run_nonce": member["run_nonce"],
                            "retention_disposition": "released",
                            "next_condition": "none",
                            "retention_release": release,
                        }
                    )
                    updated = dict(member, keep_worktree=False, preserved_artifacts=member_receipt)
                    reaper_lifecycle._atomic_write(member_path, updated)
        return None
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError):
        return "retention release refused: owner or retrieval proof unavailable"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.fleet.post_task_reap --task-id example
  .venv/bin/python -m scripts.fleet.post_task_reap --task-id example --release-retention --apply
Outputs: JSON disposition; --apply updates retention receipts and invokes the common reaper.
Exit codes: 0 = report without errors (may retain); 1 = release or reap error.
Related: #9934; scripts/orchestration/reap_worktrees.py; docs/runbooks/worktree-cleanup.md
""",
    )
    parser.add_argument("--task-id", required=True, help="Task id whose worktree should be reaped")
    parser.add_argument(
        "--release-retention",
        action="store_true",
        help="Release creator and settled reused successors after current-byte retrieval (requires --apply; default: off)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually remove worktrees (default: dry-run)",
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=default_tasks_dir(),
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
        help="Also evaluate ACP runtime paths listed in task state (default: on)",
    )
    args = parser.parse_args(argv)

    report = post_task_reap(
        args.task_id,
        tasks_dir=args.tasks_dir,
        repo_root=args.repo_root,
        apply=args.apply,
        include_acp_runtime=args.include_acp_runtime,
        release_retention=args.release_retention,
    )

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
