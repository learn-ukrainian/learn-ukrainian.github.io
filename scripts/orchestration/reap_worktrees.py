#!/usr/bin/env python3
"""Safely reap finished repository worktrees.

The CLI is intentionally safe by default: ``--dry-run`` is the default mode,
only paths under the repository's ``.worktrees/`` directory are eligible, and
dirty worktrees are preserved unless ``--preserve-then-reap`` is explicit.

Suggested backstop:

    .venv/bin/python scripts/orchestration/reap_worktrees.py --apply
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.orchestration import reaper_lifecycle
from scripts.path_safety import assert_delete_target

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUILD_AGE_HOURS = 6

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


@dataclass(frozen=True)
class WorktreeInfo:
    path: Path
    branch: str | None
    head: str | None
    detached: bool = False


@dataclass(frozen=True)
class PullRequestState:
    number: int | None
    state: str
    head_sha: str | None = None


@dataclass(frozen=True)
class ReapResult:
    path: str
    branch: str | None
    action: str
    reason: str
    dirty: bool | None
    pr: dict[str, Any] | None = None
    error: str | None = None
    branch_pruned: bool = False
    recovery_ref: str | None = None


def sanitized_git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_ENV_DENYLIST and not key.startswith("PRE_COMMIT")
    }


def _run(
    args: list[str],
    *,
    cwd: Path,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=sanitized_git_env(),
    )


def resolve_repo_root(cwd: Path | None = None) -> Path:
    """Resolve the current git worktree root."""
    start = cwd or Path.cwd()
    proc = _run(["git", "rev-parse", "--show-toplevel"], cwd=start)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "not inside a git repository").strip()
        raise RuntimeError(detail)
    return Path((proc.stdout or "").strip()).resolve()


def primary_checkout_root(repo_root: Path) -> Path:
    """Return the primary checkout root that owns the shared .git dir."""
    git_path = repo_root / ".git"
    if git_path.is_dir():
        return repo_root
    if not git_path.is_file():
        return repo_root

    try:
        first_line = git_path.read_text(encoding="utf-8").splitlines()[0]
    except (IndexError, OSError):
        return repo_root
    prefix = "gitdir:"
    if not first_line.startswith(prefix):
        return repo_root

    git_dir = Path(first_line[len(prefix):].strip())
    if not git_dir.is_absolute():
        git_dir = repo_root / git_dir
    git_dir = git_dir.resolve()
    if git_dir.parent.name != "worktrees":
        return repo_root
    common_git_dir = git_dir.parent.parent
    if common_git_dir.name != ".git":
        return repo_root
    return common_git_dir.parent


def _format_failure(proc: subprocess.CompletedProcess[str]) -> str:
    detail = (proc.stderr or proc.stdout or "").strip()
    if detail:
        return detail.splitlines()[-1]
    return f"exit {proc.returncode}"


def _branch_name(raw: str) -> str:
    for prefix in ("refs/heads/", "refs/remotes/origin/"):
        if raw.startswith(prefix):
            return raw[len(prefix):]
    return raw


def parse_worktree_porcelain(output: str) -> list[WorktreeInfo]:
    entries: list[WorktreeInfo] = []
    current: dict[str, Any] | None = None

    def finish() -> None:
        nonlocal current
        if current and current.get("path"):
            entries.append(
                WorktreeInfo(
                    path=Path(current["path"]).resolve(),
                    branch=current.get("branch"),
                    head=current.get("head"),
                    detached=bool(current.get("detached")),
                )
            )
        current = None

    for line in output.splitlines():
        if not line:
            finish()
            continue
        if line.startswith("worktree "):
            finish()
            current = {"path": line.removeprefix("worktree ").strip()}
            continue
        if current is None:
            continue
        if line.startswith("HEAD "):
            current["head"] = line.removeprefix("HEAD ").strip()
        elif line.startswith("branch "):
            current["branch"] = _branch_name(line.removeprefix("branch ").strip())
        elif line == "detached":
            current["detached"] = True
    finish()
    return entries


def list_git_worktrees(repo_root: Path) -> list[WorktreeInfo]:
    proc = _run(["git", "worktree", "list", "--porcelain"], cwd=repo_root)
    if proc.returncode != 0:
        raise RuntimeError(f"git worktree list failed: {_format_failure(proc)}")
    return parse_worktree_porcelain(proc.stdout or "")


def _worktrees_root(repo_root: Path) -> Path:
    return (repo_root / ".worktrees").resolve()


def is_under_worktrees(repo_root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(_worktrees_root(repo_root))
    except ValueError:
        return False
    return True


def _worktree_clean(path: Path) -> bool | None:
    """Return True when the worktree has no meaningful dirty files.

    Dispatch workers often leave an untracked ``.venv`` (or nested site
    venv) which must not block reaping multi-hundred-MB trees.
    """
    proc = _run(["git", "status", "--porcelain", "-uall"], cwd=path)
    if proc.returncode != 0:
        return None
    ignored_prefixes = (".venv/", ".venv", "node_modules/", "node_modules")
    for raw in (proc.stdout or "").splitlines():
        if len(raw) < 4:
            continue
        rel = raw[3:].strip().strip('"')
        if rel in ignored_prefixes or rel.startswith((".venv/", "node_modules/")):
            continue
        return False
    return True


def _query_pr_states(repo_root: Path, branch: str | None) -> tuple[list[PullRequestState], str | None]:
    if not branch:
        return [], None
    try:
        proc = _run(
            [
                "gh",
                "pr",
                "list",
                "--head",
                branch,
                "--state",
                "all",
                "--json",
                "number,state,headRefOid",
            ],
            cwd=repo_root,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return [], f"gh pr list failed: {exc}"
    if proc.returncode != 0:
        return [], f"gh pr list failed: {_format_failure(proc)}"
    try:
        raw_items = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        return [], f"gh pr list returned invalid JSON: {exc}"

    states: list[PullRequestState] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        state = str(item.get("state") or "").upper()
        if not state:
            continue
        number = item.get("number")
        states.append(
            PullRequestState(
                number=number if isinstance(number, int) else None,
                state=state,
                head_sha=(
                    str(item.get("headRefOid"))
                    if item.get("headRefOid")
                    else None
                ),
            )
        )
    return states, None


def _best_pr(prs: list[PullRequestState]) -> PullRequestState | None:
    # A branch name can be reused. Any open PR is therefore authoritative over
    # historical merged/closed PRs for the same head name.
    for desired in ("OPEN", "MERGED", "CLOSED"):
        for pr_state in prs:
            if pr_state.state == desired:
                return pr_state
    return prs[0] if prs else None


def _pr_dict(pr_state: PullRequestState | None) -> dict[str, Any] | None:
    if pr_state is None:
        return None
    return {
        "number": pr_state.number,
        "state": pr_state.state,
        "head_sha": pr_state.head_sha,
    }


def _candidate_branches_for_worktree(repo_root: Path, info: WorktreeInfo) -> list[str]:
    if info.branch is not None:
        return [info.branch]

    candidates: list[str] = []
    dispatch_root = (repo_root / ".worktrees" / "dispatch").resolve()
    try:
        rel = info.path.resolve().relative_to(dispatch_root)
        if len(rel.parts) == 2:
            candidates.append(f"{rel.parts[0]}/{rel.parts[1]}")
    except ValueError:
        pass

    wt_root = _worktrees_root(repo_root)
    try:
        rel_wt = info.path.resolve().relative_to(wt_root)
        rel_str = str(rel_wt)
        if rel_str and rel_str not in candidates:
            candidates.append(rel_str)
        if "-" in rel_str and "/" not in rel_str:
            slash_conv = rel_str.replace("-", "/", 1)
            if slash_conv not in candidates:
                candidates.append(slash_conv)
    except ValueError:
        pass

    return candidates


def _pr_matches_worktree_head(
    info: WorktreeInfo,
    pr_state: PullRequestState | None,
) -> bool:
    if pr_state is None or not pr_state.head_sha or not info.head:
        return False
    if pr_state.head_sha == info.head:
        return True
    proc = _run(
        ["git", "merge-base", "--is-ancestor", info.head, pr_state.head_sha],
        cwd=info.path,
    )
    return proc.returncode == 0


def _live_cwd_paths(repo_root: Path) -> set[Path] | None:
    """Return process working directories, or ``None`` when lsof is unavailable."""
    try:
        proc = _run(["lsof", "-d", "cwd", "-F", "n"], cwd=repo_root, timeout=15)
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    paths: set[Path] = set()
    for line in (proc.stdout or "").splitlines():
        if not line.startswith("n/"):
            continue
        try:
            paths.add(Path(line[1:]).resolve())
        except OSError:
            continue
    return paths


def _path_contains(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _dispatch_task_id(repo_root: Path, info: WorktreeInfo) -> str | None:
    dispatch_root = (repo_root / ".worktrees" / "dispatch").resolve()
    try:
        relative = info.path.resolve().relative_to(dispatch_root)
    except ValueError:
        return None
    return relative.parts[1] if len(relative.parts) == 2 else None


def _task_record(repo_root: Path, task_id: str | None) -> dict[str, Any] | None:
    if not task_id:
        return None
    task_file = repo_root / "batch_state" / "tasks" / f"{task_id}.json"
    try:
        payload = json.loads(task_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _task_record_status(repo_root: Path, task_id: str | None) -> str | None:
    payload = _task_record(repo_root, task_id)
    if payload is None:
        return None
    status = payload.get("status")
    return str(status) if status else None


def _task_pid_alive(payload: dict[str, Any] | None) -> bool:
    """Return True only when task JSON names a live process."""
    if not payload:
        return False
    raw_pid = payload.get("pid")
    if raw_pid is None:
        return False
    try:
        pid = int(raw_pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Exists but not signalable by this user — treat as live.
        return True
    return True


def _activity_reason(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    active_ids: set[str] | None,
    live_cwds: set[Path] | None,
) -> str | None:
    task_id = _dispatch_task_id(repo_root, info)
    if task_id and active_ids is not None and task_id in active_ids:
        return f"active dispatch task-id={task_id}"
    task_payload = _task_record(repo_root, task_id)
    task_status = None
    if task_payload is not None:
        raw_status = task_payload.get("status")
        task_status = str(raw_status) if raw_status else None
    # Stale "running" rows with a dead worker PID must not block reaping forever
    # (observed: multi-hour dispatch workers left status=running after exit).
    if (
        task_status in {"queued", "starting", "running", "needs_finalize"}
        and _task_pid_alive(task_payload)
    ):
        return f"non-terminal dispatch task-id={task_id} status={task_status}"
    if live_cwds is not None:
        worktree = info.path.resolve()
        for cwd in live_cwds:
            if _path_contains(worktree, cwd):
                return f"live process cwd={cwd}"
    return None


def _common_git_dir(repo_root: Path) -> Path:
    proc = _run(["git", "rev-parse", "--git-common-dir"], cwd=repo_root)
    if proc.returncode != 0:
        raise RuntimeError(f"cannot resolve git common dir: {_format_failure(proc)}")
    path = Path((proc.stdout or "").strip())
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


class _ReapLock:
    def __init__(self, repo_root: Path) -> None:
        self.path = _common_git_dir(repo_root) / "worktree-reaper.lock"
        self.handle: Any = None

    def __enter__(self) -> None:
        self.handle = self.path.open("a+", encoding="utf-8")
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.handle.close()
            raise RuntimeError(f"another worktree cleanup holds {self.path}") from exc

    def __exit__(self, _exc_type: Any, _exc: Any, _tb: Any) -> None:
        if self.handle is not None:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()


def _origin_matches_head(path: Path, branch: str | None) -> bool:
    if not branch:
        return False
    remote_ref = f"origin/{branch}"
    verify = _run(["git", "rev-parse", "--verify", remote_ref], cwd=path)
    if verify.returncode != 0:
        return False
    count = _run(
        ["git", "rev-list", "--left-right", "--count", f"{remote_ref}...HEAD"],
        cwd=path,
    )
    if count.returncode != 0:
        return False
    parts = (count.stdout or "").strip().split()
    return parts == ["0", "0"]


def _worktree_age_hours(path: Path, now: float | None = None) -> float | None:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    return ((now or time.time()) - mtime) / 3600


def _active_task_ids() -> set[str] | None:
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8765/api/delegate/active", timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tasks = data.get("tasks", [])
            return {str(t.get("task_id")) for t in tasks if t.get("task_id")}
    except Exception:
        return None


def _is_ancestor_of_origin_main(path: Path) -> bool:
    proc = _run(["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"], cwd=path)
    return proc.returncode == 0


_TERMINAL_DISPATCH_STATUSES = frozenset({"done", "failed", "no_deliverable"})


def _terminal_dispatch_reason(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    active_ids: set[str] | None,
) -> str | None:
    """Prove that a dispatch worktree is terminal and no longer owned.

    This deliberately does not infer terminality from a dead PID.  A stale
    ``running`` record may be recoverable; scheduled cleanup may only reap an
    explicit terminal record and a known-empty active-task probe.
    """
    task_id = _dispatch_task_id(repo_root, info)
    if task_id is None or active_ids is None or task_id in active_ids:
        return None
    task_data = _task_record(repo_root, task_id)
    if task_data is None:
        return None
    task_status = task_data.get("status")
    if task_status not in _TERMINAL_DISPATCH_STATUSES or _task_pid_alive(task_data):
        return None
    return f"settled dispatch task-id={task_id} status={task_status}"


def _qualifying_reason(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    pr_state: PullRequestState | None,
    build_age_hours: float,
    now: float | None,
    active_ids: set[str] | None = None,
    safe_only: bool = False,
    merged_pr_only: bool = False,
    include_terminal_dispatches: bool = False,
) -> str | None:
    if pr_state is not None:
        pr_label = f"PR #{pr_state.number}" if pr_state.number is not None else "PR"
        if pr_state.state == "MERGED" and _pr_matches_worktree_head(info, pr_state):
            return f"{pr_label} MERGED"
        if (
            not merged_pr_only
            and pr_state.state == "CLOSED"
            and info.branch is not None
            and _pr_matches_worktree_head(info, pr_state)
        ):
            return f"{pr_label} CLOSED"

    if info.branch is not None:

        if not safe_only:
            if info.branch.startswith("build/"):
                age_hours = _worktree_age_hours(info.path, now=now)
                if age_hours is not None and age_hours > build_age_hours:
                    return f"build branch age {age_hours:.1f}h > {build_age_hours:g}h"

            # Never treat "matches remote tip" as reaped-while-OPEN: open PR
            # worktrees commonly match origin/<branch> and must stay mounted.
            if (pr_state is None or pr_state.state != "OPEN") and _origin_matches_head(
                info.path, info.branch
            ):
                return f"HEAD matches origin/{info.branch}"

    if merged_pr_only and not include_terminal_dispatches:
        return None

    # Class B: detached-HEAD worktrees under .worktrees/
    is_under_wt = is_under_worktrees(repo_root, info.path)
    clean = _worktree_clean(info.path)
    task_id = _dispatch_task_id(repo_root, info)
    is_dispatch_candidate = task_id is not None

    if (
        not merged_pr_only
        and not include_terminal_dispatches
        and is_under_wt
        and info.detached
        and clean is True
    ):
        has_matching_task = False
        task_settled = False
        if is_dispatch_candidate:
            task_file = repo_root / "batch_state" / "tasks" / f"{task_id}.json"
            if task_file.exists():
                has_matching_task = True
                try:
                    task_data = json.loads(task_file.read_text(encoding="utf-8"))
                    task_status = task_data.get("status")
                    if task_status in ("done", "failed", "no_deliverable") and (
                        active_ids is None or task_id not in active_ids
                    ):
                        task_settled = True
                except Exception:
                    pass

        ancestor = _is_ancestor_of_origin_main(info.path)
        if has_matching_task and task_settled:
            if ancestor:
                return f"detached HEAD ancestor of origin/main; settled dispatch task-id={task_id}"
            return f"detached HEAD settled dispatch task-id={task_id}"

        if ancestor:
            age_hours = _worktree_age_hours(info.path, now=now)
            if age_hours is not None and age_hours > 24.0:
                return f"detached HEAD ancestor of origin/main; age {age_hours:.1f}h > 24h"

    # Optional Class A: settled dispatch worktree.  This class is intentionally
    # narrower than the legacy classes: an explicit terminal task record, no
    # live PID, a known-empty active-task probe, and no open PR are all required.
    if (
        is_dispatch_candidate
        and clean is True
        and (include_terminal_dispatches or not merged_pr_only)
    ):
        terminal_reason = _terminal_dispatch_reason(
            repo_root=repo_root,
            info=info,
            active_ids=active_ids,
        )
        if terminal_reason is not None and (pr_state is None or pr_state.state != "OPEN"):
            return terminal_reason

    return None


def find_needs_finalize_worktrees(repo_root: Path) -> list[dict[str, Any]]:
    """Return all worktrees that have a task record with status 'needs_finalize'."""
    results: list[dict[str, Any]] = []
    try:
        worktrees = list_git_worktrees(repo_root)
    except Exception:
        return []
    for info in worktrees:
        task_id = _dispatch_task_id(repo_root, info)
        if task_id:
            status = _task_record_status(repo_root, task_id)
            if status == "needs_finalize":
                results.append(
                    {
                        "path": str(info.path),
                        "task_id": task_id,
                        "branch": info.branch,
                    }
                )
    return results


def adopt_dispatch_worktrees(repo_root: Path) -> list[dict[str, Any]]:
    """Journal already-mounted dispatch worktrees without inferring ownership.

    Adoption is observation only.  A later enforce pass must still independently
    prove an exact merged PR head and every P0 guard before it removes anything.
    """
    adopted: list[dict[str, Any]] = []
    for info in list_git_worktrees(repo_root):
        task_id = _dispatch_task_id(repo_root, info)
        if task_id is None or not is_under_worktrees(repo_root, info.path):
            continue
        row = {
            "path": str(info.path),
            "branch": info.branch,
            "head": info.head,
            "task_id": task_id,
        }
        reaper_lifecycle.append_journal(repo_root, "adopt", **row)
        adopted.append(row)
    return adopted


def _preserve_dirty_worktree(info: WorktreeInfo) -> str | None:
    branch = info.branch or "detached"
    add_proc = _run(["git", "add", "-A"], cwd=info.path)
    if add_proc.returncode != 0:
        return f"git add failed: {_format_failure(add_proc)}"
    commit_proc = _run(
        [
            "git",
            "commit",
            "--no-verify",
            "-m",
            f"wip: preserve {branch} before reap [skip ci]",
        ],
        cwd=info.path,
    )
    if commit_proc.returncode != 0:
        return f"git commit failed: {_format_failure(commit_proc)}"
    return None


def _remove_worktree(repo_root: Path, info: WorktreeInfo) -> str | None:
    """Remove a worktree only after the caller has completed every P0 guard.

    ``_worktree_clean`` deliberately accepts disposable ignored residue such as
    a worker's ``.venv``. Git still considers that residue when removing a
    worktree, so force is required at this final, guarded deletion boundary.
    """
    try:
        target = assert_delete_target(info.path, repo_root=repo_root)
    except ValueError as exc:
        return f"delete guard refused worktree target: {exc}"
    proc = _run(
        ["git", "worktree", "remove", "--force", str(target)],
        cwd=repo_root,
    )
    if proc.returncode != 0:
        return _format_failure(proc)
    return None


def _prune_branch(
    repo_root: Path,
    branch: str | None,
    force: bool = False,
    expected_head: str | None = None,
) -> str | None:
    if not branch:
        return None
    if expected_head is None:
        flag = "-D" if force else "-d"
        proc = _run(["git", "branch", flag, "--", branch], cwd=repo_root)
        return None if proc.returncode == 0 else _format_failure(proc)

    current = _run(
        ["git", "rev-parse", "--verify", f"refs/heads/{branch}"],
        cwd=repo_root,
    )
    if (
        current.returncode != 0
        or (current.stdout or "").strip() != expected_head
    ):
        return "branch HEAD changed during cleanup"

    flag = "-D" if force else "-d"
    deleted = _run(["git", "branch", flag, "--", branch], cwd=repo_root)
    return None if deleted.returncode == 0 else _format_failure(deleted)


def _reap_qualified_worktree(
    *,
    repo_root: Path,
    info: WorktreeInfo,
    reason: str,
    dirty: bool | None,
    pr_state: PullRequestState | None,
    apply: bool,
    preserve_then_reap: bool,
    prune_merged_branches: bool,
    require_terminal_dispatch_guards: bool,
) -> ReapResult:
    expected_head = info.head
    if dirty is None:
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason="unable to determine worktree status",
            dirty=None,
            pr=_pr_dict(pr_state),
        )
    if dirty and not preserve_then_reap:
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason=f"dirty; qualifies for reap because {reason}",
            dirty=True,
            pr=_pr_dict(pr_state),
        )
    if not apply:
        action = "would_preserve_then_remove" if dirty else "would_remove"
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action=action,
            reason=reason,
            dirty=dirty,
            pr=_pr_dict(pr_state),
        )

    if os.environ.get("LU_REAPER_DISABLED") == "1":
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason="reaper disabled by LU_REAPER_DISABLED=1",
            dirty=dirty,
            pr=_pr_dict(pr_state),
        )

    cap_allowed, cap_reason = reaper_lifecycle.cap_allows_reap(repo_root)
    if not cap_allowed:
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason=cap_reason or "first-class daily reap cap reached",
            dirty=dirty,
            pr=_pr_dict(pr_state),
        )

    pending_marked = False
    recovery_ref: str | None = None
    try:
        # This reservation is intentionally before the final TOCTOU checks.
        # Scheduler/delegate consumers can reject a new bind while it exists.
        reaper_lifecycle.mark_reap_pending(
            repo_root,
            worktree_path=info.path,
            branch=info.branch,
            head=expected_head,
            task_id=_dispatch_task_id(repo_root, info),
        )
        pending_marked = True

        if dirty:
            preserve_error = _preserve_dirty_worktree(info)
            if preserve_error is not None:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="error",
                    reason=f"preserve before reap failed: {reason}",
                    dirty=True,
                    pr=_pr_dict(pr_state),
                    error=preserve_error,
                )
            refreshed_head = _run(["git", "rev-parse", "HEAD"], cwd=info.path)
            if refreshed_head.returncode != 0:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="error",
                    reason=f"cannot verify preserved worktree HEAD: {reason}",
                    dirty=True,
                    pr=_pr_dict(pr_state),
                    error=_format_failure(refreshed_head),
                )
            expected_head = (refreshed_head.stdout or "").strip()

        current_head_proc = _run(["git", "rev-parse", "HEAD"], cwd=info.path)
        current_head = (current_head_proc.stdout or "").strip()
        if current_head_proc.returncode != 0 or not expected_head or current_head != expected_head:
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="skipped",
                reason=f"HEAD changed during cleanup; originally qualified because {reason}",
                dirty=dirty,
                pr=_pr_dict(pr_state),
            )

        current_clean = _worktree_clean(info.path)
        if current_clean is not True:
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="skipped",
                reason=f"worktree changed during cleanup; originally qualified because {reason}",
                dirty=None if current_clean is None else True,
                pr=_pr_dict(pr_state),
            )

        if require_terminal_dispatch_guards:
            current_active_ids = _active_task_ids()
            current_live_cwds = _live_cwd_paths(repo_root)
            if current_active_ids is None or current_live_cwds is None:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason="terminal dispatch guards unavailable during cleanup",
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            terminal_reason = _terminal_dispatch_reason(
                repo_root=repo_root,
                info=info,
                active_ids=current_active_ids,
            )
            activity = _activity_reason(
                repo_root=repo_root,
                info=info,
                active_ids=current_active_ids,
                live_cwds=current_live_cwds,
            )
            if terminal_reason is None or activity is not None:
                return ReapResult(
                    path=str(info.path),
                    branch=info.branch,
                    action="skipped",
                    reason=activity or "terminal dispatch state changed during cleanup",
                    dirty=dirty,
                    pr=_pr_dict(pr_state),
                )
            if info.branch is not None:
                current_prs, current_pr_error = _query_pr_states(repo_root, info.branch)
                if current_pr_error is not None:
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=f"PR guard unavailable during cleanup; {current_pr_error}",
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                    )
                if any(pr.state == "OPEN" for pr in current_prs):
                    return ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason="open PR appeared during cleanup",
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                    )

        recovery_ref, recovery_error = reaper_lifecycle.create_recovery_ref(
            repo_root,
            branch=info.branch,
            head=current_head,
        )
        if recovery_error is not None:
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="error",
                reason=f"could not create recovery material; {reason}",
                dirty=dirty,
                pr=_pr_dict(pr_state),
                error=recovery_error,
            )

        remove_error = _remove_worktree(repo_root, info)
        if remove_error is not None:
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="error",
                reason=reason,
                dirty=dirty,
                pr=_pr_dict(pr_state),
                error=remove_error,
                recovery_ref=recovery_ref,
            )

        branch_prune_error = None
        branch_pruned = False
        if (
            prune_merged_branches
            and info.branch is not None
            and pr_state is not None
            and pr_state.state == "MERGED"
            and _pr_matches_worktree_head(info, pr_state)
        ):
            branch_prune_error = _prune_branch(
                repo_root,
                info.branch,
                force=True,
                expected_head=current_head,
            )
            branch_pruned = branch_prune_error is None

        if branch_prune_error is not None:
            return ReapResult(
                path=str(info.path),
                branch=info.branch,
                action="removed",
                reason=f"{reason}; branch prune failed",
                dirty=dirty,
                pr=_pr_dict(pr_state),
                error=branch_prune_error,
                recovery_ref=recovery_ref,
            )

        reaper_lifecycle.record_reap_for_cap(repo_root)
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="preserved_then_removed" if dirty else "removed",
            reason=reason,
            dirty=dirty,
            pr=_pr_dict(pr_state),
            branch_pruned=branch_pruned,
            recovery_ref=recovery_ref,
        )
    finally:
        if pending_marked:
            reaper_lifecycle.clear_reap_pending(repo_root, info.path)

def _target_filter(target_paths: list[Path] | None) -> set[Path] | None:
    if target_paths is None:
        return None
    return {path.resolve() for path in target_paths}


def reap_worktrees(
    *,
    repo_root: Path,
    apply: bool = False,
    build_age_hours: float = DEFAULT_BUILD_AGE_HOURS,
    preserve_then_reap: bool = False,
    prune_merged_branches: bool = False,
    target_paths: list[Path] | None = None,
    now: float | None = None,
    safe_only: bool = False,
    live_cwds: set[Path] | None = None,
    merged_pr_only: bool = True,
    require_activity_probe: bool | None = None,
    include_terminal_dispatches: bool = False,
) -> list[ReapResult]:
    """Evaluate and optionally reap eligible worktrees.

    Apply mode requires a process-CWD activity probe unless a caller
    deliberately overrides that policy.
    """
    repo_root = repo_root.resolve()
    targets = _target_filter(target_paths)
    results: list[ReapResult] = []
    active_ids = _active_task_ids()
    if require_activity_probe is None:
        require_activity_probe = bool(apply)
    if live_cwds is None:
        live_cwds = _live_cwd_paths(repo_root)
    if require_activity_probe and live_cwds is None:
        raise RuntimeError("process-CWD activity probe unavailable; cleanup skipped")

    with _ReapLock(repo_root):
        for info in list_git_worktrees(repo_root):
            if targets is not None and info.path.resolve() not in targets:
                continue
            if not is_under_worktrees(repo_root, info.path):
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason="outside repo .worktrees/",
                        dirty=None,
                    )
                )
                continue

            if not info.path.is_dir():
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=(
                            "registered worktree path is missing; "
                            "run git worktree prune"
                        ),
                        dirty=None,
                    )
                )
                continue

            activity = _activity_reason(
                repo_root=repo_root,
                info=info,
                active_ids=active_ids,
                live_cwds=live_cwds,
            )
            if activity is not None:
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=activity,
                        dirty=None,
                    )
                )
                continue

            dirty_state = _worktree_clean(info.path)
            dirty = None if dirty_state is None else not dirty_state

            candidates = _candidate_branches_for_worktree(repo_root, info)
            pr_state = None
            pr_error = None
            if candidates:
                all_pr_states: list[PullRequestState] = []
                errors: list[str] = []
                for cand_branch in candidates:
                    st, err = _query_pr_states(repo_root, cand_branch)
                    if err:
                        errors.append(err)
                    all_pr_states.extend(st)
                if errors and not all_pr_states:
                    pr_error = "; ".join(errors)
                else:
                    pr_state = _best_pr(all_pr_states)

            if (merged_pr_only or include_terminal_dispatches) and pr_error is not None:
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=f"PR guard unavailable; {pr_error}",
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                    )
                )
                continue

            reason = _qualifying_reason(
                repo_root=repo_root,
                info=info,
                pr_state=pr_state,
                build_age_hours=build_age_hours,
                now=now,
                active_ids=active_ids,
                safe_only=safe_only,
                merged_pr_only=merged_pr_only,
                include_terminal_dispatches=include_terminal_dispatches,
            )
            if reason is None:
                if info.branch is None:
                    reason = "detached or missing branch"
                else:
                    reason = (
                        f"no reap condition matched; {pr_error}"
                        if pr_error
                        else "no reap condition matched"
                    )
                results.append(
                    ReapResult(
                        path=str(info.path),
                        branch=info.branch,
                        action="skipped",
                        reason=reason,
                        dirty=dirty,
                        pr=_pr_dict(pr_state),
                    )
                )
                continue

            reaper_lifecycle.append_journal(
                repo_root,
                "plan" if apply else "observe",
                path=str(info.path),
                branch=info.branch,
                head=info.head,
                reason=reason,
                pr=_pr_dict(pr_state),
            )
            results.append(
                _reap_qualified_worktree(
                    repo_root=repo_root,
                    info=info,
                    reason=reason,
                    dirty=dirty,
                    pr_state=pr_state,
                    apply=apply,
                    preserve_then_reap=preserve_then_reap,
                    prune_merged_branches=prune_merged_branches,
                    require_terminal_dispatch_guards=(
                        include_terminal_dispatches
                        and reason.startswith("settled dispatch task-id=")
                    ),
                )
            )

    if targets is not None:
        seen = {Path(result.path).resolve() for result in results}
        for target in sorted(targets - seen):
            results.append(
                ReapResult(
                    path=str(target),
                    branch=None,
                    action="skipped",
                    reason="target path is not a registered git worktree",
                    dirty=None,
                )
            )

    for result in results:
        event = "reap" if result.action in {"removed", "preserved_then_removed"} else "skip"
        reaper_lifecycle.append_journal(
            repo_root,
            event,
            path=result.path,
            branch=result.branch,
            action=result.action,
            reason=result.reason,
            dirty=result.dirty,
            pr=result.pr,
            error=result.error,
            recovery_ref=result.recovery_ref,
        )
    return results


def reap_success_worktree(
    *,
    repo_root: Path,
    worktree_path: Path,
    reason: str,
    apply: bool = True,
    preserve_then_reap: bool = False,
) -> ReapResult:
    """Remove one clean success worktree while keeping its branch."""
    repo_root = repo_root.resolve()
    target = worktree_path.resolve()
    matching = [
        info
        for info in list_git_worktrees(repo_root)
        if info.path.resolve() == target
    ]
    if not matching:
        return ReapResult(
            path=str(target),
            branch=None,
            action="skipped",
            reason="target path is not a registered git worktree",
            dirty=None,
        )

    info = matching[0]
    if not is_under_worktrees(repo_root, info.path):
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="skipped",
            reason="outside repo .worktrees/",
            dirty=None,
        )
    clean = _worktree_clean(info.path)
    dirty = None if clean is None else not clean
    return _reap_qualified_worktree(
        repo_root=repo_root,
        info=info,
        reason=reason,
        dirty=dirty,
        pr_state=None,
        apply=apply,
        preserve_then_reap=preserve_then_reap,
        prune_merged_branches=False,
        require_terminal_dispatch_guards=False,
    )


def _result_payload(result: ReapResult) -> dict[str, Any]:
    return asdict(result)


def _format_result_line(result: ReapResult) -> str:
    branch = result.branch or "-"
    base = f"{result.action.upper()} {result.path} branch={branch} reason={result.reason}"
    if result.error:
        base = f"{base} error={result.error}"
    return base


def format_text_results(results: list[ReapResult], *, apply: bool) -> str:
    remove_actions = {
        "would_remove",
        "would_preserve_then_remove",
        "removed",
        "preserved_then_removed",
    }
    candidates = sum(1 for result in results if result.action in remove_actions)
    skipped = sum(1 for result in results if result.action == "skipped")
    errors = sum(1 for result in results if result.action == "error")
    mode = "APPLY" if apply else "DRY RUN"
    lines = [f"{mode}: {candidates} candidate(s), {skipped} skipped, {errors} error(s)"]
    lines.extend(_format_result_line(result) for result in results)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely reap completed git worktrees under .worktrees/.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root to inspect (default: current git worktree root).",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("report", "plan", "apply", "journal", "restore"),
        help="Optional verb: report/plan are dry-run, apply enforces, journal prints evidence.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Print candidates without changing the filesystem (default).",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Remove eligible worktrees.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )
    parser.add_argument(
        "--build-age-hours",
        type=float,
        default=DEFAULT_BUILD_AGE_HOURS,
        help=f"Reap clean build/* worktrees older than this many hours (default: {DEFAULT_BUILD_AGE_HOURS:g}).",
    )
    parser.add_argument(
        "--preserve-then-reap",
        action="store_true",
        help="Commit dirty eligible worktrees locally with --no-verify before removing them.",
    )
    parser.add_argument(
        "--prune-merged-branches",
        action="store_true",
        help=(
            "Delete a local branch only after its MERGED PR head SHA exactly "
            "matches the removed worktree HEAD."
        ),
    )
    parser.add_argument(
        "--safe-only",
        action="store_true",
        help="Restrict reaping to provably-safe classes (merged PRs + settled dispatches + detached-HEAD ancestors).",
    )
    parser.add_argument(
        "--merged",
        action="store_true",
        help=(
            "Restrict cleanup to exact MERGED PR heads and enable branch "
            "pruning. Dirty trees remain untouched unless "
            "--preserve-then-reap is explicit."
        ),
    )
    parser.add_argument(
        "--legacy-classes",
        action="store_true",
        help="Enable pre-P0 non-merged cleanup classes for an explicit manual run.",
    )
    parser.add_argument(
        "--terminal-dispatches",
        action="store_true",
        help=(
            "Also reap clean terminal dispatch worktrees only when their task is "
            "inactive, its PID is dead, and GitHub confirms no open PR."
        ),
    )
    parser.add_argument(
        "--worktree",
        action="append",
        type=Path,
        default=None,
        help="Limit evaluation to a registered worktree path. Repeatable.",
    )
    parser.add_argument("--restore-ref", help="Recovery ref to restore from.")
    parser.add_argument("--restore-branch", help="Branch identity expected for --restore-ref.")
    parser.add_argument("--restore-worktree", type=Path, help="New .worktrees/ target for restore.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = (
        args.repo_root.resolve()
        if args.repo_root
        else primary_checkout_root(resolve_repo_root())
    )
    apply = bool(args.apply) or args.command == "apply"
    merged_mode = bool(args.merged) or (
        not bool(args.legacy_classes) and not bool(args.terminal_dispatches)
    )
    preserve = bool(args.preserve_then_reap)
    prune = bool(args.prune_merged_branches) or bool(args.merged)
    safe_only = bool(args.safe_only) or merged_mode
    if args.command == "journal":
        journal = reaper_lifecycle.journal_path(repo_root)
        print(journal.read_text(encoding="utf-8") if journal.exists() else "")
        return 0
    if args.command == "restore":
        if not (args.restore_ref and args.restore_branch and args.restore_worktree):
            parser.error("restore requires --restore-ref, --restore-branch, and --restore-worktree")
        restored, error = reaper_lifecycle.restore_worktree(
            repo_root,
            recovery_ref=args.restore_ref,
            branch=args.restore_branch,
            worktree_path=args.restore_worktree,
        )
        print(json.dumps({"restored": restored, "error": error}, indent=2))
        return 0 if restored else 2

    results = reap_worktrees(
        repo_root=repo_root,
        apply=apply,
        build_age_hours=args.build_age_hours,
        preserve_then_reap=preserve,
        prune_merged_branches=prune,
        target_paths=args.worktree,
        safe_only=safe_only,
        merged_pr_only=merged_mode,
        require_activity_probe=apply,
        include_terminal_dispatches=bool(args.terminal_dispatches),
    )
    if args.json:
        print(json.dumps([_result_payload(result) for result in results], indent=2))
    else:
        print(format_text_results(results, apply=apply))
    # Always sweep formal CF temp roots (including $TMPDIR/shielded-reviews)
    # when applying — worktree reaps alone left multi-GB lu-review snaps.
    if apply:
        try:
            if str(PROJECT_ROOT) not in sys.path:
                sys.path.insert(0, str(PROJECT_ROOT))
            from scripts.review.isolation import sweep_review_temp_orphans

            sweep = sweep_review_temp_orphans()
            print(
                "review_temp_sweep: "
                f"roots_reaped={sweep.get('roots_reaped', 0)} "
                f"bytes_freed={sweep.get('bytes_freed', 0)} "
                f"errors={sweep.get('errors', 0)}",
                file=sys.stderr,
            )
        except Exception as exc:
            print(f"review_temp_sweep: skipped ({exc})", file=sys.stderr)
    return 1 if any(result.action == "error" for result in results) else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"reap_worktrees.py: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
