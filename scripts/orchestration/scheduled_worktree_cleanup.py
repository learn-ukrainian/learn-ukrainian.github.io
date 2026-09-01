#!/usr/bin/env python3
"""Run fail-closed Git hygiene for an explicit repository set.

The scheduled runner prunes remote refs and stale worktree registrations,
requires the macOS process-CWD probe in apply mode, delegates safe worktree
removal to the canonical reaper, deletes origin and local branches only with
exact merged/closed-PR or origin/main-ancestry proof, runs automatic Git
maintenance, and writes an immutable JSON receipt. Orphaned ``.worktrees/**``
directories are reported but never deleted.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.hygiene import fetch_refspecs, home_session_retention_check
from scripts.orchestration import reap_worktrees
from scripts.orchestration.tmp_leak_sweep import sweep_tmp_leaks
from scripts.review.isolation import sweep_review_temp_orphans

SCHEMA_VERSION = "scheduled-git-hygiene.v2"
DEFAULT_INTERVAL_MINUTES = 240


def terminal_dispatch_reaping_enabled() -> bool:
    """Return whether the scheduled terminal-dispatch class is enabled.

    The class is on by default for disk-pressure recovery.  Setting
    ``LU_REAPER_TERMINAL_DISPATCHES=0`` disables only this optional class while
    preserving exact merged-PR cleanup.
    """
    return os.environ.get("LU_REAPER_TERMINAL_DISPATCHES", "1") != "0"


def default_public_repo() -> Path:
    return PROJECT_ROOT


def default_private_repo(public_repo: Path) -> Path:
    return public_repo.parent / "learn-ukrainian-infra-private"


def default_state_dir() -> Path:
    return Path.home() / ".codex" / "worktree-cleanup"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=reap_worktrees.sanitized_git_env(),
    )


def _failure(proc: subprocess.CompletedProcess[str]) -> str:
    detail = (proc.stderr or proc.stdout or "").strip()
    return detail.splitlines()[-1] if detail else f"exit {proc.returncode}"


class _GitHygieneLock:
    def __init__(self, repo_root: Path) -> None:
        common_git_dir = reap_worktrees._common_git_dir(repo_root)
        self.path = common_git_dir / "scheduled-git-hygiene.lock"
        self.handle: Any = None

    def __enter__(self) -> None:
        self.handle = self.path.open("a+", encoding="utf-8")
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.handle.close()
            raise RuntimeError(f"another scheduled Git hygiene run holds {self.path}") from exc

    def __exit__(self, _exc_type: Any, _exc: Any, _tb: Any) -> None:
        if self.handle is not None:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()


def _worktree_prune(repo_root: Path, *, apply: bool) -> dict[str, Any]:
    args = ["worktree", "prune", "--expire", "now", "--verbose"]
    if not apply:
        args.insert(2, "--dry-run")
    proc = _run_git(repo_root, *args)
    detail = (proc.stdout or proc.stderr or "").strip()
    return {
        "action": "pruned" if apply else "would_prune",
        "detail": detail or None,
        "ok": proc.returncode == 0,
    }


_PROTECTED_BRANCHES = frozenset({"main", "master"})
_PROTECTED_LOCAL_PREFIXES = ("entire/",)
_REVIEW_CHECKOUT_RE = re.compile(r"^(?:pr|review)-(\d+)(?:-review|-tmp)?$")


def _checked_out_branches(repo_root: Path) -> set[str]:
    return {item.branch for item in reap_worktrees.list_git_worktrees(repo_root) if item.branch is not None}


def _is_protected_local_branch(branch: str) -> bool:
    if branch in _PROTECTED_BRANCHES:
        return True
    return branch.startswith(_PROTECTED_LOCAL_PREFIXES)


def _review_checkout_pr_number(branch: str) -> int | None:
    match = _REVIEW_CHECKOUT_RE.fullmatch(branch)
    if match is None:
        return None
    return int(match.group(1))


def _gone_local_branches(repo_root: Path) -> list[tuple[str, str]]:
    proc = _run_git(
        repo_root,
        "for-each-ref",
        "refs/heads",
        "--format=%(refname:short)%09%(objectname)%09%(upstream)",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cannot list local branches: {_failure(proc)}")
    gone: list[tuple[str, str]] = []
    for line in (proc.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        branch, head_sha, upstream = parts
        if branch in {"main", "master"} or not upstream.startswith("refs/remotes/origin/"):
            continue
        exists = _run_git(repo_root, "show-ref", "--verify", "--quiet", upstream)
        if exists.returncode == 1:
            gone.append((branch, head_sha))
        elif exists.returncode != 0:
            raise RuntimeError(f"cannot verify upstream for {branch}: {_failure(exists)}")
    return gone


def _branch_is_origin_main_ancestor(repo_root: Path, head_sha: str) -> bool:
    proc = _run_git(
        repo_root,
        "merge-base",
        "--is-ancestor",
        head_sha,
        "origin/main",
    )
    return proc.returncode == 0


def _stale_ref_delete_reason(
    repo_root: Path,
    *,
    prs: list[reap_worktrees.PullRequestState],
    head_sha: str,
    kind: str,
) -> tuple[str | None, str | None]:
    """Return ``(delete_reason, skip_reason)`` for a candidate stale ref."""
    open_pr = next((pr for pr in prs if pr.state == "OPEN"), None)
    if open_pr is not None:
        return None, f"{kind} but PR #{open_pr.number} is OPEN"
    exact_merged = next(
        (pr for pr in prs if pr.state == "MERGED" and pr.head_sha == head_sha),
        None,
    )
    if exact_merged is not None:
        return f"{kind}; exact head of MERGED PR #{exact_merged.number}", None
    exact_closed = next(
        (pr for pr in prs if pr.state == "CLOSED" and pr.head_sha == head_sha),
        None,
    )
    if exact_closed is not None:
        return f"{kind}; exact head of CLOSED PR #{exact_closed.number}", None
    if _branch_is_origin_main_ancestor(repo_root, head_sha):
        return f"{kind}; branch HEAD is an ancestor of origin/main", None
    return None, (f"{kind} but no exact merged/closed PR or origin/main ancestry evidence")


def _origin_heads(repo_root: Path) -> list[tuple[str, str]]:
    proc = _run_git(
        repo_root,
        "for-each-ref",
        "refs/remotes/origin",
        "--format=%(refname)%09%(objectname)",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cannot list origin branches: {_failure(proc)}")
    heads: list[tuple[str, str]] = []
    prefix = "refs/remotes/origin/"
    for line in (proc.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) != 2 or not parts[0].startswith(prefix):
            continue
        branch = parts[0][len(prefix) :]
        if branch in _PROTECTED_BRANCHES or branch == "HEAD" or _is_protected_local_branch(branch):
            continue
        heads.append((branch, parts[1]))
    return heads


def _live_origin_head(repo_root: Path, branch: str) -> str | None:
    proc = _run_git(repo_root, "ls-remote", "--heads", "origin", branch)
    if proc.returncode != 0:
        return None
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, ref = parts
        if ref == f"refs/heads/{branch}":
            return sha
    return None


def _delete_origin_branch(
    repo_root: Path,
    *,
    branch: str,
    expected_head: str,
) -> str | None:
    live_head = _live_origin_head(repo_root, branch)
    if live_head is None:
        return "origin HEAD disappeared during cleanup"
    if live_head != expected_head:
        return "origin HEAD changed during cleanup"
    if branch in _checked_out_branches(repo_root):
        return "branch became checked out during cleanup"
    proc = _run_git(
        repo_root,
        "push",
        f"--force-with-lease=refs/heads/{branch}:{expected_head}",
        "origin",
        f":refs/heads/{branch}",
    )
    if proc.returncode != 0:
        return _failure(proc)
    return None


def cleanup_stale_origin_branches(
    repo_root: Path,
    *,
    apply: bool,
) -> list[dict[str, Any]]:
    """Delete origin heads only with exact merged/closed PR or ancestry proof."""
    checked_out = _checked_out_branches(repo_root)
    results: list[dict[str, Any]] = []
    for branch, head_sha in _origin_heads(repo_root):
        if branch in checked_out:
            results.append(
                {
                    "action": "skipped",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": "origin branch is checked out",
                }
            )
            continue
        prs, pr_error = reap_worktrees._query_pr_states(repo_root, branch)
        if pr_error is not None:
            results.append(
                {
                    "action": "error",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": "origin branch PR state could not be verified",
                    "error": pr_error,
                }
            )
            continue
        reason, skip_reason = _stale_ref_delete_reason(
            repo_root,
            prs=prs,
            head_sha=head_sha,
            kind="origin head",
        )
        if skip_reason is not None:
            results.append(
                {
                    "action": "skipped",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": skip_reason,
                }
            )
            continue
        assert reason is not None
        if not apply:
            results.append(
                {
                    "action": "would_delete",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": reason,
                }
            )
            continue
        prs_now, pr_error_now = reap_worktrees._query_pr_states(repo_root, branch)
        if pr_error_now is not None:
            results.append(
                {
                    "action": "error",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": "origin branch PR state could not be re-verified",
                    "error": pr_error_now,
                }
            )
            continue
        open_now = next((pr for pr in prs_now if pr.state == "OPEN"), None)
        if open_now is not None:
            results.append(
                {
                    "action": "skipped",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": f"origin head but PR #{open_now.number} is OPEN",
                }
            )
            continue
        error = _delete_origin_branch(
            repo_root,
            branch=branch,
            expected_head=head_sha,
        )
        # Deleting the origin head without dropping the matching fetch
        # refspec is the #7121 landmine: the next bare fetch hard-fails.
        refspec_dropped = False
        if error is None or error == "origin HEAD disappeared during cleanup":
            try:
                refspec_dropped = fetch_refspecs.drop_fetch_refspec_for_branch(
                    repo_root,
                    branch,
                )
            except Exception as exc:
                if error is None:
                    error = f"origin head deleted but fetch refspec drop failed: {exc}"
        results.append(
            {
                "action": "error" if error else "deleted",
                "branch": branch,
                "head_sha": head_sha,
                "reason": reason,
                "error": error,
                "refspec_dropped": refspec_dropped,
            }
        )
    return results


def _delete_local_branch(
    repo_root: Path,
    *,
    branch: str,
    expected_head: str,
) -> str | None:
    current = _run_git(
        repo_root,
        "rev-parse",
        "--verify",
        f"refs/heads/{branch}",
    )
    if current.returncode != 0 or (current.stdout or "").strip() != expected_head:
        return "branch HEAD changed during cleanup"
    if branch in _checked_out_branches(repo_root):
        return "branch became checked out during cleanup"
    return reap_worktrees._prune_branch(
        repo_root,
        branch,
        force=True,
        expected_head=expected_head,
    )


def cleanup_gone_local_branches(
    repo_root: Path,
    *,
    apply: bool,
) -> list[dict[str, Any]]:
    """Delete gone-upstream branches only with exact merged or ancestry proof."""
    checked_out = _checked_out_branches(repo_root)
    results: list[dict[str, Any]] = []
    for branch, head_sha in _gone_local_branches(repo_root):
        if branch in checked_out:
            results.append(
                {
                    "action": "skipped",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": "upstream gone but branch is checked out",
                }
            )
            continue

        prs, pr_error = reap_worktrees._query_pr_states(repo_root, branch)
        if pr_error is not None:
            results.append(
                {
                    "action": "error",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": "upstream gone but PR state could not be verified",
                    "error": pr_error,
                }
            )
            continue
        reason, skip_reason = _stale_ref_delete_reason(
            repo_root,
            prs=prs,
            head_sha=head_sha,
            kind="upstream gone",
        )
        if skip_reason is not None:
            results.append(
                {
                    "action": "skipped",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": skip_reason,
                }
            )
            continue
        assert reason is not None
        if not apply:
            results.append(
                {
                    "action": "would_delete",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": reason,
                }
            )
            continue

        error = _delete_local_branch(
            repo_root,
            branch=branch,
            expected_head=head_sha,
        )
        results.append(
            {
                "action": "error" if error else "deleted",
                "branch": branch,
                "head_sha": head_sha,
                "reason": reason,
                "error": error,
            }
        )
    return results


def _untracked_local_branches(repo_root: Path) -> list[tuple[str, str]]:
    proc = _run_git(
        repo_root,
        "for-each-ref",
        "refs/heads",
        "--format=%(refname:short)%09%(objectname)%09%(upstream)",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cannot list local branches: {_failure(proc)}")
    untracked: list[tuple[str, str]] = []
    for line in (proc.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        branch, head_sha, upstream = parts
        if _is_protected_local_branch(branch):
            continue
        if upstream:
            continue
        untracked.append((branch, head_sha))
    return untracked


def _query_pr_by_number(
    repo_root: Path,
    number: int,
) -> tuple[list[reap_worktrees.PullRequestState], str | None]:
    try:
        proc = reap_worktrees._run(
            [
                "gh",
                "pr",
                "view",
                str(number),
                "--json",
                "number,state,headRefOid",
            ],
            cwd=repo_root,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return [], f"gh pr view failed: {exc}"
    if proc.returncode != 0:
        return [], f"gh pr view failed: {reap_worktrees._format_failure(proc)}"
    try:
        item = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return [], f"gh pr view returned invalid JSON: {exc}"
    if not isinstance(item, dict):
        return [], "gh pr view returned invalid JSON"
    state = str(item.get("state") or "").upper()
    if not state:
        return [], None
    number_value = item.get("number")
    return [
        reap_worktrees.PullRequestState(
            number=number_value if isinstance(number_value, int) else number,
            state=state,
            head_sha=(str(item.get("headRefOid")) if item.get("headRefOid") else None),
        )
    ], None


def cleanup_untracked_local_branches(
    repo_root: Path,
    *,
    apply: bool,
) -> list[dict[str, Any]]:
    """Delete never-tracked local branches with merged/closed or ancestry proof."""
    checked_out = _checked_out_branches(repo_root)
    results: list[dict[str, Any]] = []
    for branch, head_sha in _untracked_local_branches(repo_root):
        if branch in checked_out:
            results.append(
                {
                    "action": "skipped",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": "untracked local branch is checked out",
                }
            )
            continue
        prs, pr_error = reap_worktrees._query_pr_states(repo_root, branch)
        if pr_error is not None:
            results.append(
                {
                    "action": "error",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": "untracked local PR state could not be verified",
                    "error": pr_error,
                }
            )
            continue
        review_number = _review_checkout_pr_number(branch)
        if review_number is not None:
            extra, extra_error = _query_pr_by_number(repo_root, review_number)
            if extra_error is not None:
                results.append(
                    {
                        "action": "error",
                        "branch": branch,
                        "head_sha": head_sha,
                        "reason": "untracked local PR state could not be verified",
                        "error": extra_error,
                    }
                )
                continue
            prs = [*prs, *extra]
        reason, skip_reason = _stale_ref_delete_reason(
            repo_root,
            prs=prs,
            head_sha=head_sha,
            kind="untracked local",
        )
        if skip_reason is not None:
            results.append(
                {
                    "action": "skipped",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": skip_reason,
                }
            )
            continue
        assert reason is not None
        if not apply:
            results.append(
                {
                    "action": "would_delete",
                    "branch": branch,
                    "head_sha": head_sha,
                    "reason": reason,
                }
            )
            continue
        error = _delete_local_branch(
            repo_root,
            branch=branch,
            expected_head=head_sha,
        )
        results.append(
            {
                "action": "error" if error else "deleted",
                "branch": branch,
                "head_sha": head_sha,
                "reason": reason,
                "error": error,
            }
        )
    return results


def _git_maintenance(repo_root: Path, *, apply: bool) -> dict[str, Any]:
    if not apply:
        return {"action": "would_run", "ok": True, "detail": "git gc --auto"}
    proc = _run_git(repo_root, "gc", "--auto")
    return {
        "action": "ran",
        "ok": proc.returncode == 0,
        "detail": None if proc.returncode == 0 else _failure(proc),
    }


def _registered_paths(repo_root: Path) -> set[Path]:
    return {item.path.resolve() for item in reap_worktrees.list_git_worktrees(repo_root)}


def find_orphaned_worktree_directories(repo_root: Path) -> list[dict[str, Any]]:
    """Report unregistered checkout-shaped directories without deleting them."""
    worktrees_root = repo_root / ".worktrees"
    if not worktrees_root.is_dir():
        return []
    registered = _registered_paths(repo_root)
    orphans: list[dict[str, Any]] = []
    for directory, child_dirs, files in os.walk(worktrees_root, followlinks=False):
        path = Path(directory)
        if ".git" not in files:
            if len(path.relative_to(worktrees_root).parts) >= 4:
                child_dirs.clear()
            continue
        child_dirs.clear()
        resolved = path.resolve()
        if resolved in registered:
            continue
        git_file = path / ".git"
        try:
            first_line = git_file.read_text(encoding="utf-8").splitlines()[0]
        except (IndexError, OSError) as exc:
            orphans.append(
                {
                    "path": str(resolved),
                    "reason": f"unreadable .git file: {exc}",
                    "gitdir": None,
                }
            )
            continue
        prefix = "gitdir:"
        if not first_line.startswith(prefix):
            reason = "unrecognized .git file"
            gitdir = None
        else:
            target = Path(first_line.removeprefix(prefix).strip())
            if not target.is_absolute():
                target = path / target
            target = target.resolve()
            gitdir = str(target)
            reason = (
                "unregistered worktree with missing gitdir"
                if not target.exists()
                else "unregistered worktree with existing gitdir"
            )
        orphans.append({"path": str(resolved), "reason": reason, "gitdir": gitdir})
    return sorted(orphans, key=lambda item: item["path"])


def _empty_repo_result(repo_root: Path) -> dict[str, Any]:
    return {
        "repo_root": str(repo_root),
        "fetch": None,
        "fetch_refspecs": None,
        "worktree_prune": None,
        "activity_probe": None,
        "results": [],
        "adopted": [],
        "origin_branches": [],
        "branches": [],
        "maintenance": None,
        "orphans": [],
        "errors": [],
        "reaper_disabled": False,
        "needs_finalize_worktrees": [],
    }


def _repo_result_unlocked(repo_root: Path, *, apply: bool) -> dict[str, Any]:
    result = _empty_repo_result(repo_root)
    if not (repo_root / ".git").exists():
        result["errors"].append("repository .git metadata is missing")
        return result

    # Self-heal stale per-branch fetch refspecs before fetch (#7121).
    # A configured refspec whose remote head is gone is a hard error, so
    # this must run before the first `git fetch --prune`.
    try:
        refspec_report = fetch_refspecs.reconcile_fetch_refspecs(repo_root, apply=apply)
        result["fetch_refspecs"] = refspec_report
        if not refspec_report.get("ok"):
            result["errors"].append(f"fetch refspec reconcile failed ({refspec_report.get('error')})")
    except Exception as exc:
        result["fetch_refspecs"] = {"ok": False, "error": str(exc)}
        result["errors"].append(f"fetch refspec reconcile failed: {exc}")

    if apply:
        fetch = _run_git(repo_root, "fetch", "--prune", "origin")
        result["fetch"] = {
            "ok": fetch.returncode == 0,
            "detail": None if fetch.returncode == 0 else _failure(fetch),
        }
        if fetch.returncode != 0:
            result["errors"].append(f"fetch failed ({_failure(fetch)}); degraded to local cleanup")

    worktree_prune = _worktree_prune(repo_root, apply=apply)
    result["worktree_prune"] = worktree_prune
    if not worktree_prune["ok"]:
        result["errors"].append("worktree prune failed; cleanup skipped")
        return result

    live_cwds = reap_worktrees._live_cwd_paths(repo_root)
    result["activity_probe"] = {
        "available": live_cwds is not None,
        "cwd_count": len(live_cwds or ()),
    }
    if apply and live_cwds is None:
        result["errors"].append("process-CWD activity probe unavailable; apply skipped")
        return result

    try:
        rows = reap_worktrees.reap_worktrees(
            repo_root=repo_root,
            apply=apply,
            preserve_then_reap=False,
            prune_merged_branches=True,
            safe_only=True,
            live_cwds=live_cwds,
            # Exact merged PR heads remain the primary class.  The terminal
            # dispatch class is independently fail-closed and can be disabled
            # with LU_REAPER_TERMINAL_DISPATCHES=0 for incident containment.
            merged_pr_only=True,
            include_terminal_dispatches=terminal_dispatch_reaping_enabled(),
        )
        result["results"] = [asdict(row) for row in rows]
        try:
            result["adopted"] = reap_worktrees.adopt_dispatch_worktrees(repo_root)
        except Exception as exc:
            # Adoption only journals currently mounted dispatch worktrees.  A
            # broken or incomplete repository must not prevent the remaining
            # local hygiene steps from running.
            result["adopted"] = []
            result["errors"].append(f"adoption skipped: {exc}")
        result["errors"].extend(f"{row.path}: {row.error or row.reason}" for row in rows if row.action == "error")
        if apply and os.environ.get("LU_REAPER_DISABLED") == "1":
            origin_branches: list[dict[str, Any]] = []
            branches: list[dict[str, Any]] = []
            result["reaper_disabled"] = True
        else:
            origin_branches = cleanup_stale_origin_branches(repo_root, apply=apply)
            if apply:
                if any(row.get("action") == "deleted" for row in origin_branches):
                    try:
                        fetch_refspecs.reconcile_fetch_refspecs(repo_root, apply=True)
                    except Exception as exc:
                        result["errors"].append(f"post-origin fetch refspec reconcile failed: {exc}")
                prune_after = _run_git(repo_root, "fetch", "--prune", "origin")
                if prune_after.returncode != 0:
                    result["errors"].append(f"post-origin prune failed ({_failure(prune_after)})")
            branches = cleanup_gone_local_branches(repo_root, apply=apply) + cleanup_untracked_local_branches(
                repo_root, apply=apply
            )
        result["origin_branches"] = origin_branches
        result["branches"] = branches
        result["errors"].extend(
            f"origin/{row['branch']}: {row.get('error') or row['reason']}"
            for row in origin_branches
            if row["action"] == "error"
        )
        result["errors"].extend(
            f"{row['branch']}: {row.get('error') or row['reason']}" for row in branches if row["action"] == "error"
        )
        result["orphans"] = find_orphaned_worktree_directories(repo_root)
        maintenance = _git_maintenance(repo_root, apply=apply)
        result["maintenance"] = maintenance
        if not maintenance["ok"]:
            result["errors"].append(f"git maintenance failed: {maintenance['detail']}")
        if apply:
            try:
                sweep_res = sweep_review_temp_orphans()
                result["review_temp_sweep"] = sweep_res
                if sweep_res.get("errors"):
                    result["errors"].append(f"review temp sweep encountered {sweep_res['errors']} error(s)")
            except Exception as exc:
                result["errors"].append(f"review temp sweep failed: {exc}")
        try:
            leak_res = sweep_tmp_leaks(apply=apply)
            result["tmp_leak_sweep"] = {
                "roots_reaped": leak_res.get("roots_reaped", 0),
                "bytes_freed": leak_res.get("bytes_freed", 0),
                "candidates": leak_res.get("candidates", 0),
                "skipped_live": leak_res.get("skipped_live", 0),
                "errors": leak_res.get("errors", 0),
                "disk_pressure": leak_res.get("disk_pressure"),
            }
            if leak_res.get("errors"):
                result["errors"].append(f"tmp leak sweep encountered {leak_res['errors']} error(s)")
        except Exception as exc:
            result["errors"].append(f"tmp leak sweep failed: {exc}")

        result["needs_finalize_worktrees"] = reap_worktrees.find_needs_finalize_worktrees(repo_root)
    except RuntimeError as exc:
        result["errors"].append(str(exc))
    return result


def _repo_result(repo_root: Path, *, apply: bool) -> dict[str, Any]:
    if not (repo_root / ".git").exists():
        return _repo_result_unlocked(repo_root, apply=apply)
    try:
        with _GitHygieneLock(repo_root):
            return _repo_result_unlocked(repo_root, apply=apply)
    except RuntimeError as exc:
        result = _empty_repo_result(repo_root)
        result["errors"].append(str(exc))
        return result


def build_receipt(
    repo_roots: list[Path],
    *,
    apply: bool,
    observed_at: str | None = None,
) -> dict[str, Any]:
    timestamp = observed_at or utc_now()
    repositories = [_repo_result(path.resolve(), apply=apply) for path in repo_roots]
    removed = sum(
        1
        for repository in repositories
        for row in repository["results"]
        if row["action"] in {"removed", "preserved_then_removed"}
    )
    errors = sum(len(repository["errors"]) for repository in repositories)
    orphans = sum(len(repository["orphans"]) for repository in repositories)
    origin_branches_deleted = sum(
        1 for repository in repositories for row in repository.get("origin_branches", []) if row["action"] == "deleted"
    )
    branches_deleted = (
        sum(1 for repository in repositories for row in repository["branches"] if row["action"] == "deleted")
        + sum(1 for repository in repositories for row in repository["results"] if row.get("branch_pruned") is True)
        + origin_branches_deleted
    )
    review_temp_reaped = sum(
        repository.get("review_temp_sweep", {}).get("roots_reaped", 0)
        for repository in repositories
        if repository.get("review_temp_sweep")
    )
    review_temp_bytes_freed = sum(
        repository.get("review_temp_sweep", {}).get("bytes_freed", 0)
        for repository in repositories
        if repository.get("review_temp_sweep")
    )
    needs_finalize_worktrees = [
        item for repository in repositories for item in repository.get("needs_finalize_worktrees", [])
    ]
    if needs_finalize_worktrees:
        for item in needs_finalize_worktrees:
            sys.stderr.write(f"WARNING: Worktree '{item.get('path')}' skipped with status 'needs_finalize'\n")
    return {
        "schema_version": SCHEMA_VERSION,
        "observed_at": timestamp,
        "mode": "apply" if apply else "dry_run",
        "summary": {
            "repositories": len(repositories),
            "removed": removed,
            "branches_deleted": branches_deleted,
            "origin_branches_deleted": origin_branches_deleted,
            "orphans_reported": orphans,
            "errors": errors,
            "review_temp_reaped": review_temp_reaped,
            "review_temp_bytes_freed": review_temp_bytes_freed,
            "needs_finalize_worktrees": needs_finalize_worktrees,
        },
        "repositories": repositories,
    }


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def ensure_private_directory(path: Path) -> None:
    """Create every missing directory component with owner-only permissions."""
    missing: list[Path] = []
    current = path
    while not current.exists():
        missing.append(current)
        if current.parent == current:
            break
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        os.chmod(directory, 0o700)
    os.chmod(path, 0o700)


def write_receipt(receipt: dict[str, Any], receipt_dir: Path) -> Path:
    content = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()[:12]
    timestamp = str(receipt["observed_at"]).replace(":", "").replace("-", "")
    destination = receipt_dir / f"{timestamp}-{digest}.json"
    ensure_private_directory(receipt_dir)
    atomic_write(destination, content)
    return destination


def build_parser() -> argparse.ArgumentParser:
    public_repo = default_public_repo()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        action="append",
        type=Path,
        default=None,
        help="Repository root to sweep. Repeatable.",
    )
    parser.add_argument("--apply", action="store_true", help="Apply safe cleanup candidates.")
    parser.add_argument(
        "--receipt-dir",
        type=Path,
        default=default_state_dir() / "receipts" / "v2",
    )
    parser.set_defaults(default_repo_roots=[public_repo, default_private_repo(public_repo)])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_roots = args.repo_root or args.default_repo_roots
    receipt = build_receipt(repo_roots, apply=bool(args.apply))
    home_session_retention = home_session_retention_check.build_report()
    receipt["home_session_retention"] = home_session_retention
    for line in home_session_retention_check.warning_lines(home_session_retention):
        sys.stderr.write(f"{line}\n")
    receipt_path = write_receipt(receipt, args.receipt_dir.expanduser().resolve())
    payload = {**receipt, "receipt_path": str(receipt_path)}
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 1 if receipt["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
