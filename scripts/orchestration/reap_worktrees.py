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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUILD_AGE_HOURS = 6.0

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
    proc = _run(["git", "status", "--porcelain"], cwd=path)
    if proc.returncode != 0:
        return None
    return not bool((proc.stdout or "").strip())


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


def _pr_matches_worktree_head(
    info: WorktreeInfo,
    pr_state: PullRequestState | None,
) -> bool:
    return bool(
        pr_state is not None
        and pr_state.head_sha
        and info.head
        and pr_state.head_sha == info.head
    )


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


def _task_record_status(repo_root: Path, task_id: str | None) -> str | None:
    if not task_id:
        return None
    task_file = repo_root / "batch_state" / "tasks" / f"{task_id}.json"
    try:
        payload = json.loads(task_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    status = payload.get("status") if isinstance(payload, dict) else None
    return str(status) if status else None


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
    task_status = _task_record_status(repo_root, task_id)
    if task_status in {"queued", "starting", "running", "needs_finalize"}:
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
) -> str | None:
    if info.branch is not None:
        if pr_state is not None:
            pr_label = f"PR #{pr_state.number}" if pr_state.number is not None else "PR"
            if pr_state.state == "MERGED" and _pr_matches_worktree_head(info, pr_state):
                return f"{pr_label} MERGED"
            if (
                not merged_pr_only
                and pr_state.state == "CLOSED"
                and _pr_matches_worktree_head(info, pr_state)
            ):
                return f"{pr_label} CLOSED"

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

    if merged_pr_only:
        return None

    # Class B: detached-HEAD worktrees under .worktrees/
    is_under_wt = is_under_worktrees(repo_root, info.path)
    clean = _worktree_clean(info.path)
    task_id = _dispatch_task_id(repo_root, info)
    is_dispatch_candidate = task_id is not None

    if is_under_wt and info.detached and clean is True and _is_ancestor_of_origin_main(info.path):
        has_matching_task = False
        task_settled = False
        if is_dispatch_candidate:
            task_file = repo_root / "batch_state" / "tasks" / f"{task_id}.json"
            if task_file.exists():
                has_matching_task = True
                try:
                    task_data = json.loads(task_file.read_text(encoding="utf-8"))
                    task_status = task_data.get("status")
                    if task_status in ("done", "failed", "no_deliverable") and active_ids is not None and task_id not in active_ids:
                        task_settled = True
                except Exception:
                    pass

        if has_matching_task:
            if task_settled:
                return f"detached HEAD ancestor of origin/main; settled dispatch task-id={task_id}"
        else:
            age_hours = _worktree_age_hours(info.path, now=now)
            if age_hours is not None and age_hours > 24.0:
                return f"detached HEAD ancestor of origin/main; age {age_hours:.1f}h > 24h"

    # Class A: settled-dispatch, no PR
    if is_dispatch_candidate and clean is True:
        task_file = repo_root / "batch_state" / "tasks" / f"{task_id}.json"
        if task_file.exists():
            try:
                task_data = json.loads(task_file.read_text(encoding="utf-8"))
                task_status = task_data.get("status")
                if task_status in ("done", "failed", "no_deliverable") and active_ids is not None and task_id not in active_ids:
                    if info.branch:
                        prs, pr_error = _query_pr_states(repo_root, info.branch)
                        if pr_error is None and not any(pr.state == "OPEN" for pr in prs):
                            return f"settled dispatch task-id={task_id} status={task_status}"
                    else:
                        return f"settled dispatch task-id={task_id} status={task_status}"
            except Exception:
                pass

    return None


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
    proc = _run(
        ["git", "worktree", "remove", str(info.path)],
        cwd=repo_root,
    )
    if proc.returncode != 0:
        return _format_failure(proc)
    return None


def _prune_branch(repo_root: Path, branch: str | None, force: bool = False) -> str | None:
    if not branch:
        return None
    flag = "-D" if force else "-d"
    proc = _run(["git", "branch", flag, branch], cwd=repo_root)
    if proc.returncode != 0:
        return _format_failure(proc)
    return None


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
        )

    branch_prune_error = None
    if (
        prune_merged_branches
        and pr_state is not None
        and pr_state.state == "MERGED"
        and pr_state.head_sha == current_head
    ):
        branch_prune_error = _prune_branch(repo_root, info.branch, force=True)

    if branch_prune_error is not None:
        return ReapResult(
            path=str(info.path),
            branch=info.branch,
            action="removed",
            reason=f"{reason}; branch prune failed",
            dirty=dirty,
            pr=_pr_dict(pr_state),
            error=branch_prune_error,
        )

    return ReapResult(
        path=str(info.path),
        branch=info.branch,
        action="preserved_then_removed" if dirty else "removed",
        reason=reason,
        dirty=dirty,
        pr=_pr_dict(pr_state),
    )


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
    merged_pr_only: bool = False,
    require_activity_probe: bool = False,
) -> list[ReapResult]:
    """Evaluate and optionally reap eligible worktrees."""
    repo_root = repo_root.resolve()
    targets = _target_filter(target_paths)
    results: list[ReapResult] = []
    active_ids = _active_task_ids()
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

            pr_state = None
            pr_error = None
            if info.branch is not None:
                pr_states, pr_error = _query_pr_states(repo_root, info.branch)
                pr_state = _best_pr(pr_states)

            reason = _qualifying_reason(
                repo_root=repo_root,
                info=info,
                pr_state=pr_state,
                build_age_hours=build_age_hours,
                now=now,
                active_ids=active_ids,
                safe_only=safe_only,
                merged_pr_only=merged_pr_only,
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
        "--worktree",
        action="append",
        type=Path,
        default=None,
        help="Limit evaluation to a registered worktree path. Repeatable.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = (
        args.repo_root.resolve()
        if args.repo_root
        else primary_checkout_root(resolve_repo_root())
    )
    apply = bool(args.apply)
    merged_mode = bool(getattr(args, "merged", False))
    preserve = bool(args.preserve_then_reap)
    prune = bool(args.prune_merged_branches) or merged_mode
    safe_only = bool(args.safe_only) or merged_mode
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
    )
    if args.json:
        print(json.dumps([_result_payload(result) for result in results], indent=2))
    else:
        print(format_text_results(results, apply=apply))
    return 1 if any(result.action == "error" for result in results) else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"reap_worktrees.py: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
