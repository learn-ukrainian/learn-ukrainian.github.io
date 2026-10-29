#!/usr/bin/env python3
"""Run fail-closed Git hygiene for an explicit repository set.

The scheduled runner prunes remote refs and stale worktree registrations,
deletes origin and local branches only with
exact merged-PR, a closed PR whose head GitHub still publishes at
``refs/pull/<N>/head``, origin/main-ancestry, or (scratch names only)
another-origin-ref proof re-verified against the live remote with
``git ls-remote``, and writes an immutable
JSON receipt. When this run's ``fetch --prune`` fails, every deletion that
relies on remote containment is skipped as ``fetch_failed_no_remote_proof``.
Orphaned ``.worktrees/**`` directories are reported but never deleted. Finished
tasks' worktrees go only through the dispatcher's settlement retry, which this
run invokes with salvage for the control plane whose records the dispatcher
reads; every tree it keeps is listed with its reason (``retained``). Once the
shared GitHub client's admission refuses a read, the run is degraded: no later
GitHub read is sent and pull-request-dependent deletions are deferred.
The separate ``--git-maintenance`` mode runs only bounded foreground GC.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.common import github_client
from scripts.common.task_scratch import recover_orphans as recover_task_scratch
from scripts.hygiene import fetch_refspecs, home_session_retention_check
from scripts.maintenance.claude_session_scratch import sweep_sessions
from scripts.orchestration import backup_failure_alert, disk_watermark_alert, worktree_git
from scripts.orchestration.execution_safe_git import GIT
from scripts.orchestration.execution_safe_git import run_git as safe_git
from scripts.orchestration.pool_headroom import _read_limit
from scripts.orchestration.task_record_store import iter_task_records
from scripts.orchestration.tmp_leak_sweep import sweep_tmp_leaks
from scripts.review.isolation import sweep_review_temp_orphans

SCHEMA_VERSION = "scheduled-git-hygiene.v3"
DEFAULT_INTERVAL_MINUTES = 240
GC_MEMORY_MAX = 2 * 1024**3
GC_DEADLINE_SECONDS = 600
CGROUP_ROOT = Path("/sys/fs/cgroup")
SELF_CGROUP = Path("/proc/self/cgroup")


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
        env=worktree_git.sanitized_git_env(),
    )


def _fetch_origin(repo_root: Path) -> subprocess.CompletedProcess[str]:
    """``git fetch --prune origin`` with automatic maintenance disabled.

    A fetch whose loose-object count trips ``maintenance.auto`` runs
    ``maintenance run --auto``, which expires every reflog and can run
    ``gc --auto`` before the branch cleanup below has run (#10856). The
    separate bounded GC service stays the only maintenance path.
    """
    args = (*worktree_git.GIT_NO_AUTO_MAINTENANCE, "fetch", "--prune", "origin")
    fetched = _run_git(repo_root, *args)
    old_value = r"error: fetching ref refs/remotes/origin/main failed: incorrect old value provided"
    lock_race = r"error: cannot lock ref 'refs/remotes/origin/main': is at [0-9a-f]+ but expected [0-9a-f]+"
    diagnostics = [
        line.strip()
        for line in (fetched.stderr or "").splitlines()
        if re.search(r"\b(?:error|fatal):", line) or line.lstrip().startswith("!")
    ]
    update_failed = r"!\s+(?:[0-9a-f]+\.{2,3}[0-9a-f]+|\[new branch\])\s+main\s+-> origin/main\s+\(unable to update local ref\)"
    if (
        fetched.returncode
        and any(re.fullmatch(f"(?:{old_value}|{lock_race})", line) for line in diagnostics)
        and all(re.fullmatch(f"(?:{old_value}|{lock_race}|{update_failed})", line) for line in diagnostics)
    ):
        # Fetch again against current refs; never reset a ref or accept the
        # failed attempt as remote-containment proof. The retry may fail too.
        print("Origin/main fetch compare-and-swap race; retrying fetch once", file=sys.stderr)
        return _run_git(repo_root, *args)
    return fetched


def _failure(proc: subprocess.CompletedProcess[str]) -> str:
    detail = (proc.stderr or proc.stdout or "").strip()
    return detail.splitlines()[-1] if detail else f"exit {proc.returncode}"


class _GitHygieneBusy(RuntimeError):
    pass


class _GitHygieneLock:
    def __init__(self, repo_root: Path) -> None:
        common_git_dir = worktree_git._common_git_dir(repo_root)
        self.path = common_git_dir / "scheduled-git-hygiene.lock"
        self.handle: Any = None

    def __enter__(self) -> None:
        self.handle = self.path.open("a+", encoding="utf-8")
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.handle.close()
            raise _GitHygieneBusy(f"another scheduled Git hygiene run holds {self.path}") from exc

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
# salvage/* holds work settlement pushed instead of discarding it; only the operator deletes it.
_PROTECTED_LOCAL_PREFIXES = ("entire/", "salvage/")
_REVIEW_CHECKOUT_RE = re.compile(r"^(?:pr|review)-(\d+)(?:-review|-tmp)?$")


def _checked_out_branches(repo_root: Path) -> set[str]:
    return {item.branch for item in worktree_git.list_git_worktrees(repo_root) if item.branch is not None}


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
        if _is_protected_local_branch(branch) or not upstream.startswith("refs/remotes/origin/"):
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


def _is_agent_scratch_branch(branch: str) -> bool:
    """Names that are a review round, a rescue, or a ``pr-N`` checkout.

    These refs are not the pull request's head branch. ``gh pr list --head``
    never sees them, so without this set the exact-SHA rule kept every one of
    them. The set is the one named in the drive-epic closeout: ``*/review-*``,
    ``rescue/*``, and ``pr-*``. The name only widens which refs are examined.
    It is never proof the tip is safe to delete; a wider prefix list would
    still have to pass the same containment proof.
    """
    if branch.startswith(("rescue/", "pr-")):
        return True
    return branch.split("/")[-1].startswith("review-")


def _live_origin_branch_shas(repo_root: Path, branches: list[str]) -> dict[str, str] | None:
    """Return live ``refs/heads/<name>`` SHAs from one batched ``ls-remote``.

    ``None`` means the lookup itself failed (git error, unreachable origin,
    timeout) and proves nothing. A branch absent from a successful mapping is
    genuinely gone from the remote; its local tracking ref is a stale cache.
    """
    if not branches:
        return {}
    patterns = sorted({f"refs/heads/{branch}" for branch in branches})
    proc = _run_git(repo_root, "ls-remote", "origin", *patterns)
    if proc.returncode != 0:
        return None
    live: dict[str, str] = {}
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, ref = parts
        if ref.startswith("refs/heads/"):
            live[ref.removeprefix("refs/heads/")] = sha
    return live


def _tip_on_other_origin_ref(repo_root: Path, head_sha: str, branch: str) -> bool:
    """True when a live origin branch other than ``branch`` contains ``head_sha``.

    A local ``refs/remotes/origin/*`` ref is a cache, not proof: after a
    failed ``fetch --prune`` the remote branch may already be deleted while
    the tracking ref still contains the tip. Every candidate is re-verified
    against the live remote; containment counts only when the live SHA equals
    the cached tracking SHA or has ``head_sha`` as an ancestor. A git error,
    a missing remote ref, or an unreadable live SHA is not containment. The
    candidate's own ``refs/remotes/origin/<branch>`` does not count: a ref is
    always reachable from itself.
    """
    proc = _run_git(
        repo_root,
        "for-each-ref",
        "--contains",
        head_sha,
        "--format=%(refname)%09%(objectname)",
        "refs/remotes/origin",
    )
    if proc.returncode != 0:
        return False
    excluded = f"refs/remotes/origin/{branch}"
    prefix = "refs/remotes/origin/"
    candidates: list[tuple[str, str]] = []
    for line in (proc.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        ref, tracking_sha = parts
        if ref.startswith(prefix) and ref != excluded:
            candidates.append((ref[len(prefix) :], tracking_sha))
    if not candidates:
        return False
    live = _live_origin_branch_shas(repo_root, [name for name, _ in candidates])
    if live is None:
        return False
    for name, tracking_sha in candidates:
        live_sha = live.get(name)
        if live_sha is None:
            continue
        if live_sha == tracking_sha:
            return True
        contains = _run_git(repo_root, "merge-base", "--is-ancestor", head_sha, live_sha)
        if contains.returncode == 0:
            return True
    return False


def _merged_pr_contains_head(
    repo_root: Path,
    head_sha: str,
    prs: list[worktree_git.PullRequestState],
) -> worktree_git.PullRequestState | None:
    """A squash merge is not an ancestor of main. The old tip is still on the PR."""
    for pr in prs:
        if pr.state != "MERGED" or not pr.head_sha:
            continue
        if head_sha == pr.head_sha:
            return pr
        proc = _run_git(repo_root, "merge-base", "--is-ancestor", head_sha, pr.head_sha)
        if proc.returncode != 0:
            continue
        # A commit already on main is an ancestor of every PR that branched
        # after it. Return code 1 is "not an ancestor"; anything else is
        # unreadable and must not delete the ref.
        on_main = _run_git(repo_root, "merge-base", "--is-ancestor", head_sha, "origin/main")
        if on_main.returncode == 1:
            return pr
    return None


def _closed_pr_head_is_durable(repo_root: Path, number: int, head_sha: str) -> bool:
    """True only when GitHub still publishes ``head_sha`` at ``refs/pull/<N>/head``.

    A closed, unmerged pull request's recorded head is not containment by
    itself. ``git ls-remote`` must return exactly that SHA. A git or network
    error, an empty answer, or any other SHA is not proof, and the ref stays.
    """
    ref = f"refs/pull/{number}/head"
    proc = _run_git(repo_root, "ls-remote", "origin", ref)
    if proc.returncode != 0:
        return False
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == ref and parts[0] == head_sha:
            return True
    return False


def _stale_ref_delete_reason(
    repo_root: Path,
    *,
    branch: str,
    prs: list[worktree_git.PullRequestState],
    head_sha: str,
    kind: str,
    fetch_ok: bool = True,
) -> tuple[str | None, str | None]:
    """Return ``(delete_reason, skip_reason)`` for a candidate stale ref.

    Scratch names never skip containment. A scratch ref is deleted only when
    its tip is an exact merged-PR head, an ancestor of ``origin/main``,
    contained in a merged PR head, or reachable from some other origin ref.
    A closed PR head is proof only while ``refs/pull/<N>/head`` is still that
    commit.

    ``fetch_ok=False`` means this run's ``fetch --prune`` failed, so every
    local ``refs/remotes/origin/*`` ref is a suspect cache: origin/main
    ancestry and remote-ref containment stop being proof and the ref is kept
    with ``fetch_failed_no_remote_proof``. Exact merged-PR heads and live
    ``refs/pull/<N>/head`` checks do not depend on the fetch and still count.
    """
    open_pr = next((pr for pr in prs if pr.state == "OPEN"), None)
    if open_pr is not None:
        return None, f"{kind} but PR #{open_pr.number} is OPEN"
    exact_merged = next(
        (pr for pr in prs if pr.state == "MERGED" and pr.head_sha == head_sha),
        None,
    )
    if exact_merged is not None:
        return f"{kind}; exact head of MERGED PR #{exact_merged.number}", None
    if fetch_ok and _branch_is_origin_main_ancestor(repo_root, head_sha):
        return f"{kind}; branch HEAD is an ancestor of origin/main", None
    contained = _merged_pr_contains_head(repo_root, head_sha, prs) if fetch_ok else None
    if contained is not None:
        return f"{kind}; tip is contained in MERGED PR #{contained.number}", None
    exact_closed = next(
        (pr for pr in prs if pr.state == "CLOSED" and pr.head_sha == head_sha),
        None,
    )
    closed_not_durable = False
    if exact_closed is not None and exact_closed.number is not None:
        if _closed_pr_head_is_durable(repo_root, exact_closed.number, head_sha):
            return f"{kind}; exact head of CLOSED PR #{exact_closed.number}", None
        closed_not_durable = True
    if _is_agent_scratch_branch(branch):
        if fetch_ok and _tip_on_other_origin_ref(repo_root, head_sha, branch):
            return f"{kind}; agent scratch ref; tip is contained in a remote ref", None
        if not fetch_ok:
            return None, (
                f"{kind} but fetch_failed_no_remote_proof; agent scratch ref; "
                "origin/main ancestry and remote-ref containment are unverified"
            )
        return None, (
            f"{kind} but no exact merged/closed PR or origin/main ancestry evidence; "
            "agent scratch ref; tip not contained in main, a merged PR, or a remote ref"
        )
    if closed_not_durable and exact_closed is not None and exact_closed.number is not None:
        return None, (
            f"{kind} but CLOSED PR #{exact_closed.number} head is not durably on refs/pull/{exact_closed.number}/head"
        )
    if not fetch_ok:
        return None, (
            f"{kind} but fetch_failed_no_remote_proof; origin/main ancestry and remote-ref containment are unverified"
        )
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


def _live_origin_head(repo_root: Path, branch: str) -> tuple[str | None, str | None]:
    """Return ``(sha, error)``.

    ``(None, None)`` means ``git ls-remote`` succeeded and origin genuinely
    has no such branch. ``(None, error)`` means the lookup itself failed
    (unreachable origin, auth failure, timeout) -- callers must never read
    that as "branch is gone", since it is not proof of absence.
    """
    proc = _run_git(repo_root, "ls-remote", "--heads", "origin", branch)
    if proc.returncode != 0:
        return None, _failure(proc)
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, ref = parts
        if ref == f"refs/heads/{branch}":
            return sha, None
    return None, None


# Another actor (merge queue cleanup, a merged PR's branch auto-delete, a
# driver) removed the branch between listing and deletion. The goal is
# reached, so it is recorded as already absent, never as an error that fails
# the unit.
ORIGIN_HEAD_GONE = "origin HEAD disappeared during cleanup"


def _delete_origin_branch(
    repo_root: Path,
    *,
    branch: str,
    expected_head: str,
) -> str | None:
    live_head, live_error = _live_origin_head(repo_root, branch)
    if live_error is not None:
        return f"cannot verify origin HEAD: {live_error}"
    if live_head is None:
        return ORIGIN_HEAD_GONE
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


def _inspect_terminal_git(worktree: Path, *args: str) -> str:
    return safe_git(
        list(args),
        cwd=worktree,
        integrity=True,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.strip()


def report_terminal_worktrees(repo_root: Path) -> dict[str, Any]:
    """Inventory old terminal work without preserving or changing the worktrees."""
    rows: list[dict[str, Any]] = []
    root = repo_root.resolve()
    tasks_dir = worktree_git.control_plane_root(root) / "batch_state" / "tasks"
    now = datetime.now(UTC)
    for path in iter_task_records(tasks_dir, include_archive=True):
        row = {"task_id": path.stem, "action": "error"}
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(record, dict):
                raise ValueError("invalid task record")
            if record.get("status") not in worktree_git._TERMINAL_DISPATCH_STATUSES:
                continue
            raw_path = record.get("worktree_path")
            if raw_path is None:
                continue
            if not isinstance(raw_path, str):
                raise ValueError("invalid worktree path")
            worktree = (root / raw_path).resolve()
            if not worktree.is_relative_to(root):
                continue
            try:
                worktree.stat()
            except FileNotFoundError:
                continue
            finished = datetime.fromisoformat(str(record.get("finished_at")).replace("Z", "+00:00"))
            age_seconds = (now - finished).total_seconds()
            if age_seconds < 6 * 3600:
                continue
            row["task_id"] = record.get("task_id") or path.stem
            row["worktree_path"] = worktree.relative_to(root).as_posix()

            dirty = len(
                _inspect_terminal_git(worktree, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
            )
            # F3 follow-up: a squash-merged branch can count as unpushed until its remote ref is gone.
            unpushed = int(_inspect_terminal_git(worktree, "rev-list", "--count", "HEAD", "--not", "--remotes=origin"))
            if dirty or unpushed:
                row.update(
                    action="report",
                    branch=_inspect_terminal_git(worktree, "rev-parse", "--abbrev-ref", "HEAD"),
                    dirty=dirty,
                    unpushed=unpushed,
                    age_seconds=int(age_seconds),
                )
                rows.append(row)
        except (OSError, ValueError, TypeError, RecursionError, subprocess.SubprocessError) as exc:
            row["error"] = f"terminal worktree inspection failed ({type(exc).__name__})"
            rows.append(row)
    return {"summary": {"candidate": sum(row["action"] == "report" for row in rows)}, "tasks": rows}


GITHUB_DEFERRED = "github admission refused; pull-request-dependent deletion deferred"


class GitHubReads:
    """The run's pull-request reads and its one degraded mode.

    The first read the shared GitHub client refuses (its reserve or hold admission, which
    serializes the refusal as ``github_rate_limited``) degrades the run: no later read is sent,
    and each deletion that needs a pull-request answer is deferred instead of reported as an
    error. Git-proven local work continues.
    """

    def __init__(self) -> None:
        self.refusal: str | None = None

    def _degrade(self, error: str | None) -> bool:
        if error is not None and github_client.GitHubRateLimited.code in error:
            self.refusal = error
        return self.refusal is not None

    def pr_states(self, repo_root: Path, branch: str) -> tuple[list[worktree_git.PullRequestState] | None, str | None]:
        """``worktree_git._query_pr_states``; ``(None, GITHUB_DEFERRED)`` once the run is degraded."""
        if self.refusal is None:
            states, error = worktree_git._query_pr_states(repo_root, branch)
            if not self._degrade(error):
                return states, error
        return None, GITHUB_DEFERRED

    def pr_by_number(self, repo_root: Path, number: int) -> tuple[list[worktree_git.PullRequestState] | None, str | None]:
        """``_query_pr_by_number``; ``(None, GITHUB_DEFERRED)`` once the run is degraded."""
        if self.refusal is None:
            try:
                states, error = _query_pr_by_number(repo_root, number)
            except github_client.GitHubRateLimited as exc:  # its message starts with the code
                states, error = [], str(exc)
            if not self._degrade(error):
                return states, error
        return None, GITHUB_DEFERRED


def _deferred(branch: str, head_sha: str) -> dict[str, Any]:
    return {"action": "deferred", "branch": branch, "head_sha": head_sha, "reason": GITHUB_DEFERRED}


# Retained reasons the alert hook reports at once: salvage or a removal guard stopped on content
# that could be lost, rather than waiting for a cause to clear.
SAFETY_STOP_REASONS = frozenset({"salvage_failed", "salvage_unverified", "large_ignored_output", "removal_refused",
                                 "worktree_remove_failed", "settlement_failed"})


def settle_terminal_worktrees(repo_root: Path) -> dict[str, Any] | None:
    """Run the dispatcher's settlement retry with salvage, then list every finished task's tree still on disk.

    Only the control plane whose task records the dispatcher itself reads runs it (``None``
    otherwise), so a sibling repository or another checkout never settles that tree set.
    Settlement keeps every tree whose work it cannot prove is on the canonical remote. A
    borrowed tree is its creator's and is not listed twice. ``complete`` is false when the
    retry failed, so a consumer must not read the list as exhaustive.
    """
    from scripts.common.task_store_paths import tasks_dir
    from scripts.dispatcher import store, worker

    try:
        if (repo_root / "batch_state" / "tasks").resolve() != tasks_dir().resolve():
            return None
    except (OSError, RuntimeError):
        return None
    complete, error = True, None
    try:
        worker.settle_left_worktrees(salvage=True)
    except Exception as exc:  # one failed record must not hide the others' state
        complete, error = False, f"settlement retry failed ({type(exc).__name__})"
    trees: list[dict[str, Any]] = []
    # The same record set settlement reads: files that are not task records name no tree.
    for record in store.list_tasks():
        path = record.get("worktree_path")
        if (record.get("status") in store.ACTIVE or (record.get("options") or {}).get("cwd")
                or not isinstance(path, str) or not Path(path).is_dir()):
            continue
        reason = record.get("worktree_disposition_reason") or "unsettled"
        trees.append({
            "identity": record.get("task_id"),
            "task_id": record.get("task_id"),
            "worktree_path": path,
            "disposition": record.get("worktree_disposition"),
            "reason": reason,
            "detail": record.get("worktree_disposition_detail"),
            "safety_stop": record.get("worktree_disposition") == "error" or reason in SAFETY_STOP_REASONS,
        })
    return {"complete": complete, "error": error, "trees": trees}


def cleanup_stale_origin_branches(
    repo_root: Path,
    *,
    apply: bool,
    fetch_ok: bool = True,
    github: GitHubReads | None = None,
) -> list[dict[str, Any]]:
    """Delete origin heads only with merged/closed, ancestry, or remote-ref proof."""
    github = github or GitHubReads()
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
        prs, pr_error = github.pr_states(repo_root, branch)
        if prs is None:
            results.append(_deferred(branch, head_sha))
            continue
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
            branch=branch,
            prs=prs,
            head_sha=head_sha,
            kind="origin head",
            fetch_ok=fetch_ok,
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
        prs_now, pr_error_now = github.pr_states(repo_root, branch)
        if prs_now is None:
            results.append(_deferred(branch, head_sha))
            continue
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
        if error is None or error == ORIGIN_HEAD_GONE:
            try:
                refspec_dropped = fetch_refspecs.drop_fetch_refspec_for_branch(
                    repo_root,
                    branch,
                )
            except Exception as exc:
                if error is None:
                    error = f"origin head deleted but fetch refspec drop failed: {exc}"
        already_absent = error == ORIGIN_HEAD_GONE
        results.append(
            {
                "action": "already_absent" if already_absent else ("error" if error else "deleted"),
                "branch": branch,
                "head_sha": head_sha,
                "reason": reason,
                "error": None if already_absent else error,
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
    return worktree_git._prune_branch(
        repo_root,
        branch,
        force=True,
        expected_head=expected_head,
    )


def cleanup_gone_local_branches(
    repo_root: Path,
    *,
    apply: bool,
    fetch_ok: bool = True,
    github: GitHubReads | None = None,
) -> list[dict[str, Any]]:
    """Delete gone-upstream branches only with containment proof, never by name."""
    github = github or GitHubReads()
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

        prs, pr_error = github.pr_states(repo_root, branch)
        if prs is None:
            results.append(_deferred(branch, head_sha))
            continue
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
            branch=branch,
            prs=prs,
            head_sha=head_sha,
            kind="upstream gone",
            fetch_ok=fetch_ok,
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
) -> tuple[list[worktree_git.PullRequestState], str | None]:
    states, rest_error = worktree_git._query_pr_by_number_rest(repo_root, number)
    if rest_error is None:
        return states, None
    try:
        proc = github_client.run(
            [
                "gh",
                "pr",
                "view",
                str(number),
                "--json",
                "number,state,headRefOid,url",
                *(["--repo", repository] if (repository := worktree_git._pr_repository(repo_root)) else []),
            ],
            capture_output=True,
            text=True,
            cwd=repo_root,
            timeout=30,
            fresh=True,
        )
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return [], f"{rest_error}; gh pr view failed: {exc}"
    observation = getattr(proc, "github_result", None)
    if observation is not None and observation.error == "github_rate_limited":
        raise github_client.GitHubRateLimited(observation.reset_at)
    if proc.returncode != 0:
        return [], f"{rest_error}; gh pr view failed: {worktree_git._format_failure(proc)}"
    try:
        item = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return [], f"gh pr view returned invalid JSON: {exc}"
    if not isinstance(item, dict):
        return [], "gh pr view returned invalid JSON"
    rows, error = worktree_git._scope_pr_rows([item], worktree_git._pr_repository(repo_root), number=number)
    if error or not rows:
        return [], error
    parsed, error = worktree_git._parse_pr_item(rows[0])
    return ([parsed] if parsed is not None else []), error


def cleanup_untracked_local_branches(
    repo_root: Path,
    *,
    apply: bool,
    fetch_ok: bool = True,
    github: GitHubReads | None = None,
) -> list[dict[str, Any]]:
    """Delete never-tracked local branches only with containment proof."""
    github = github or GitHubReads()
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
        prs, pr_error = github.pr_states(repo_root, branch)
        if prs is None:
            results.append(_deferred(branch, head_sha))
            continue
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
            extra, extra_error = github.pr_by_number(repo_root, review_number)
            if extra is None:
                results.append(_deferred(branch, head_sha))
                continue
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
            branch=branch,
            prs=prs,
            head_sha=head_sha,
            kind="untracked local",
            fetch_ok=fetch_ok,
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


def _maintenance_limits() -> dict[str, int | float] | None:
    """Read effective cgroup v2 limits, including stricter ancestors."""
    try:
        relative = next(line[3:] for line in SELF_CGROUP.read_text().splitlines() if line.startswith("0::"))
        group = (CGROUP_ROOT / relative.lstrip("/")).resolve()
        root = CGROUP_ROOT.resolve()
        group.relative_to(root)
        values: dict[str, list[int | float]] = {name: [] for name in ("memory", "swap", "tasks", "cpu")}
        while group != root:
            for name, filename in (("memory", "memory.max"), ("swap", "memory.swap.max"), ("tasks", "pids.max")):
                limit = _read_limit(group / filename, "maintenance")
                if isinstance(limit, str):
                    return None
                if limit is not None:
                    values[name].append(limit)
            quota, period = (group / "cpu.max").read_text().split()
            if quota != "max":
                values["cpu"].append(int(quota) / int(period))
            group = group.parent
        if not all(values.values()):
            return None
        limits = {name: min(items) for name, items in values.items()}
        if 0 < limits["memory"] <= GC_MEMORY_MAX and limits["swap"] == 0 and 0 < limits["tasks"] <= 32 and 0 < limits["cpu"] <= 1:
            return limits
    except (OSError, ValueError, StopIteration, ZeroDivisionError):
        pass
    return None


class _GCDeadlineExceeded(TimeoutError):
    pass


def _run_gc(repo_root: Path, lock_fd: int) -> subprocess.CompletedProcess[str]:
    command = [
        GIT, "-c", "gc.autoDetach=false", "-c", "gc.auto=6700", "-c", "gc.autoPackLimit=50",
        "-c", "pack.threads=1", "-c", "pack.windowMemory=64m", "-c", "pack.deltaCacheSize=64m", "gc", "--auto",
    ]
    proc = subprocess.Popen(
        command, cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, env=worktree_git.sanitized_git_env(), start_new_session=True, pass_fds=(lock_fd,),
    )
    try:
        stdout, stderr = proc.communicate(timeout=GC_DEADLINE_SECONDS)
    except subprocess.TimeoutExpired:
        # Allow Git's signal handlers to remove its locks. Keep Git unreaped
        # during this grace period so its process-group id cannot be reused.
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGTERM)
        time.sleep(5)
        # Closed pipes or an exited Git parent do not prove children exited.
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            raise _GCDeadlineExceeded("GC deadline exceeded; SIGTERM and SIGKILL requested; output pipes remain open") from None
        raise _GCDeadlineExceeded("GC deadline exceeded; SIGTERM grace and process-group SIGKILL requested") from None
    return subprocess.CompletedProcess(command, proc.returncode, stdout, stderr)


def _git_maintenance(repo_root: Path, *, apply: bool) -> dict[str, Any]:
    if not apply:
        return {"action": "would_run", "ok": True, "detail": "bounded foreground git gc --auto"}
    try:
        with _GitHygieneLock(repo_root):
            state = worktree_git._common_git_dir(repo_root) / "lu-pre-push-gate"
            state.mkdir(mode=0o700, exist_ok=True)
            fd = os.open(state / "admission.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            try:
                # This excludes both serial EX and parallel SH validation, and
                # keeps new validation out through GC and timeout recovery.
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                limits = _maintenance_limits()
                if limits is None:
                    return {"action": "refused_unbounded", "ok": False, "detail": "effective cgroup limits unavailable or too loose"}
                automatic_disabled = (
                    _run_git(repo_root, "config", "--get", "gc.auto").stdout.strip() == "0"
                    and _run_git(repo_root, "config", "--bool", "--get", "maintenance.auto").stdout.strip() == "false"
                )
                if not automatic_disabled:
                    return {"action": "refused_automatic", "ok": False, "detail": "ordinary Git requires gc.auto=0 and maintenance.auto=false"}
                before = _run_git(repo_root, "count-objects", "-v")
                proc = _run_gc(repo_root, fd)
                after = _run_git(repo_root, "count-objects", "-v")
                ok = proc.returncode == before.returncode == after.returncode == 0
                return {
                    "action": "ran", "ok": ok, "limits": limits,
                    "changed": before.stdout != after.stdout if ok else None,
                    "detail": None if ok else _failure(next(p for p in (proc, before, after) if p.returncode)),
                }
            finally:
                os.close(fd)
    except (_GitHygieneBusy, BlockingIOError):
        return {"action": "deferred", "ok": True, "detail": "Git hygiene or validation holds admission"}
    except _GCDeadlineExceeded as exc:
        return {"action": "timeout", "ok": False, "detail": str(exc)}
    except subprocess.TimeoutExpired:
        return {"action": "timeout", "ok": False, "detail": "Git metadata query exceeded its timeout"}
    except (OSError, RuntimeError) as exc:
        return {"action": "error", "ok": False, "detail": f"bounded GC unavailable: {type(exc).__name__}"}


def _maintenance_repo_result(repo_root: Path, *, apply: bool) -> dict[str, Any]:
    result = _empty_repo_result(repo_root)
    result["maintenance"] = _git_maintenance(repo_root, apply=apply)
    if not result["maintenance"]["ok"]:
        result["errors"].append(f"git maintenance failed: {result['maintenance']['detail']}")
    return result


def _registered_paths(repo_root: Path) -> set[Path]:
    return {item.path.resolve() for item in worktree_git.list_git_worktrees(repo_root)}


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
        "origin_branches": [],
        "branches": [],
        "maintenance": None,
        "orphans": [],
        "errors": [],
        "reaper_disabled": False,
        "rescue": None,
        "retained": None,
        "github_degraded": None,
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

    fetch_ok = True
    if apply:
        fetch = _fetch_origin(repo_root)
        fetch_ok = fetch.returncode == 0
        result["fetch"] = {
            "ok": fetch_ok,
            "detail": None if fetch_ok else _failure(fetch),
        }
        if not fetch_ok:
            result["errors"].append(f"fetch failed ({_failure(fetch)}); degraded to local cleanup")

    worktree_prune = _worktree_prune(repo_root, apply=apply)
    result["worktree_prune"] = worktree_prune
    if not worktree_prune["ok"]:
        result["errors"].append("worktree prune failed; cleanup skipped")
        return result

    if apply and os.environ.get("LU_REAPER_DISABLED") != "1":
        result["rescue"] = report_terminal_worktrees(repo_root)
        result["errors"].extend(row["error"] for row in result["rescue"]["tasks"] if row["action"] == "error")

    try:
        if apply and os.environ.get("LU_REAPER_DISABLED") == "1":
            origin_branches: list[dict[str, Any]] = []
            branches: list[dict[str, Any]] = []
            result["reaper_disabled"] = True
        else:
            origin_branches = cleanup_stale_origin_branches(repo_root, apply=apply, fetch_ok=fetch_ok)
            if apply:
                if any(row.get("action") == "deleted" for row in origin_branches):
                    try:
                        fetch_refspecs.reconcile_fetch_refspecs(repo_root, apply=True)
                    except Exception as exc:
                        result["errors"].append(f"post-origin fetch refspec reconcile failed: {exc}")
                prune_after = _fetch_origin(repo_root)
                if prune_after.returncode != 0:
                    result["errors"].append(f"post-origin prune failed ({_failure(prune_after)})")
            branches = cleanup_gone_local_branches(repo_root, apply=apply, fetch_ok=fetch_ok) + (
                cleanup_untracked_local_branches(repo_root, apply=apply, fetch_ok=fetch_ok)
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
        result["maintenance"] = {"action": "scheduled_separately", "ok": True, "detail": None}
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
                "inventory_only": leak_res.get("inventory_only", 0),
                "inventory_bytes": leak_res.get("inventory_bytes", 0),
                "errors": leak_res.get("errors", 0),
                "disk_pressure": leak_res.get("disk_pressure"),
            }
            if leak_res.get("errors"):
                result["errors"].append(f"tmp leak sweep encountered {leak_res['errors']} error(s)")
        except Exception as exc:
            result["errors"].append(f"tmp leak sweep failed: {exc}")
        # #8738: task-owned scratch leases whose owner and child group are
        # provably dead. Counts only — never paths — reach the receipt.
        try:
            scratch_res = recover_task_scratch(apply=apply)
            result["task_scratch_recovery"] = {
                "candidates": scratch_res.get("candidates", 0),
                "reaped": scratch_res.get("reaped", 0),
                "bytes_freed": scratch_res.get("bytes_freed", 0),
                "preserved": scratch_res.get("preserved", 0),
                "preserved_by_reason": dict(scratch_res.get("preserved_by_reason") or {}),
                "errors": scratch_res.get("errors", 0),
                "disk_pressure": scratch_res.get("disk_pressure"),
            }
            if scratch_res.get("errors"):
                result["errors"].append(f"task scratch recovery encountered {scratch_res['errors']} error(s)")
        except Exception as exc:
            result["errors"].append(f"task scratch recovery failed: {exc}")
    except github_client.GitHubRateLimited:
        raise
    except RuntimeError as exc:
        result["errors"].append(str(exc))
    return result


def _repo_result(repo_root: Path, *, apply: bool) -> dict[str, Any]:
    if not (repo_root / ".git").exists():
        return _repo_result_unlocked(repo_root, apply=apply)
    try:
        with _GitHygieneLock(repo_root):
            return _repo_result_unlocked(repo_root, apply=apply)
    except github_client.GitHubRateLimited:
        raise
    except RuntimeError as exc:
        result = _empty_repo_result(repo_root)
        result["errors"].append(str(exc))
        return result


def build_receipt(
    repo_roots: list[Path],
    *,
    apply: bool,
    observed_at: str | None = None,
    git_maintenance: bool = False,
) -> dict[str, Any]:
    timestamp = observed_at or utc_now()
    runner = _maintenance_repo_result if git_maintenance else _repo_result
    repositories = [runner(path.resolve(), apply=apply) for path in repo_roots]
    errors = sum(len(repository["errors"]) for repository in repositories)
    orphans = sum(len(repository["orphans"]) for repository in repositories)
    origin_branches_deleted = sum(
        1 for repository in repositories for row in repository.get("origin_branches", []) if row["action"] == "deleted"
    )
    branches_deleted = (
        sum(1 for repository in repositories for row in repository["branches"] if row["action"] == "deleted")
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
    task_scratch_reaped = sum(
        (repository.get("task_scratch_recovery") or {}).get("reaped", 0) for repository in repositories
    )
    task_scratch_bytes_freed = sum(
        (repository.get("task_scratch_recovery") or {}).get("bytes_freed", 0) for repository in repositories
    )
    task_scratch_preserved = sum(
        (repository.get("task_scratch_recovery") or {}).get("preserved", 0) for repository in repositories
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "observed_at": timestamp,
        "mode": "apply" if apply else "dry_run",
        "summary": {
            "repositories": len(repositories),
            "branches_deleted": branches_deleted,
            "origin_branches_deleted": origin_branches_deleted,
            "orphans_reported": orphans,
            "errors": errors,
            "review_temp_reaped": review_temp_reaped,
            "review_temp_bytes_freed": review_temp_bytes_freed,
            "task_scratch_reaped": task_scratch_reaped,
            "task_scratch_bytes_freed": task_scratch_bytes_freed,
            "task_scratch_preserved": task_scratch_preserved,
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
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/orchestration/scheduled_worktree_cleanup.py
  .venv/bin/python scripts/orchestration/scheduled_worktree_cleanup.py --repo-root . --apply
  .venv/bin/python scripts/orchestration/scheduled_worktree_cleanup.py --git-maintenance --apply
Outputs:
  Private JSON receipt and aggregate JSON on stdout. Dry-run is the default.
  --apply deletes proven-merged branches and refs, snapshots and proven-ended Claude scratch.
  Large batch_state files are reported for their owners; they are never auto-deleted.
  --git-maintenance runs only GC under verified cgroup limits and validation admission.
Exit codes:
  0 report written without errors; 1 cleanup errors; 2 invalid arguments.
Related:
  docs/runbooks/worktree-cleanup.md; #8783; thread_handoff.py
""",
    )
    parser.add_argument(
        "--repo-root",
        action="append",
        type=Path,
        default=None,
        help="Repository root to sweep. Repeatable; default: configured public and private repositories. Example: .",
    )
    parser.add_argument(
        "--git-maintenance", action="store_true",
        help="Run only bounded foreground GC, without other hygiene. Default: hourly hygiene without GC.",
    )
    parser.add_argument("--apply", action="store_true", help="Apply safe cleanup candidates. Default: dry-run.")
    parser.add_argument(
        "--receipt-dir",
        type=Path,
        default=default_state_dir() / "receipts" / "v2",
        help="Private receipt directory. Default: configured hygiene state receipts/v2. Example: <receipts-dir>",
    )
    parser.add_argument(
        "--alert-state-dir",
        type=Path,
        default=default_state_dir() / "disk-watermark",
        help="Change-only disk watermark alert state. Default: configured hygiene state disk-watermark. "
        "Example: <alert-state-dir>",
    )
    parser.set_defaults(default_repo_roots=[public_repo, default_private_repo(public_repo)])
    return parser


def _apply_error_counts(row: dict[str, Any]) -> dict[str, int]:
    """Count apply-time ``error`` rows by errno name. Dry-run rows are not errors."""
    apply = row.get("apply")
    if not isinstance(apply, dict):
        return {}
    counts: dict[str, int] = {}
    for selected in apply.get("selected") or []:
        if not isinstance(selected, dict) or selected.get("action") != "error":
            continue
        key = selected.get("error")
        if not isinstance(key, str) or not key:
            key = "OSError"
        counts[key] = counts.get(key, 0) + 1
    return counts


def build_public_summary(
    receipt: dict[str, Any],
    receipt_path: Path | str | None = None,
) -> dict[str, Any]:
    summary = receipt.get("summary", {})
    repos_summary: dict[str, Any] = {}
    for repo_dict in receipt.get("repositories", []):
        raw_root = repo_dict.get("repo_root", "")
        repo_name = Path(raw_root).name if raw_root else "unknown"
        repos_summary[repo_name] = {
            "orphans_reported": len(repo_dict.get("orphans", [])),
            "maintenance": {
                key: value for key, value in (repo_dict.get("maintenance") or {}).items()
                if key in {"action", "ok", "changed", "limits"}
            },
            "errors": len(repo_dict.get("errors", [])),
            "rescue_candidates": ((repo_dict.get("rescue") or {}).get("summary") or {}).get("candidate", 0),
            "branches_deleted": (
                sum(1 for row in repo_dict.get("branches", []) if row.get("action") == "deleted")
                + sum(1 for row in repo_dict.get("origin_branches", []) if row.get("action") == "deleted")
            ),
        }

    public_payload: dict[str, Any] = {
        "schema_version": receipt.get("schema_version", SCHEMA_VERSION),
        "observed_at": receipt.get("observed_at"),
        "mode": receipt.get("mode"),
        "summary": {
            "repositories": summary.get("repositories", len(repos_summary)),
            "branches_deleted": summary.get("branches_deleted", 0),
            "origin_branches_deleted": summary.get("origin_branches_deleted", 0),
            "orphans_reported": summary.get("orphans_reported", 0),
            "errors": summary.get("errors", 0),
            "review_temp_reaped": summary.get("review_temp_reaped", 0),
            "review_temp_bytes_freed": summary.get("review_temp_bytes_freed", 0),
            "task_scratch_reaped": summary.get("task_scratch_reaped", 0),
            "task_scratch_bytes_freed": summary.get("task_scratch_bytes_freed", 0),
            "task_scratch_preserved": summary.get("task_scratch_preserved", 0),
        },
        "repositories": repos_summary,
    }
    if "home_session_retention" in receipt:
        public_payload["home_session_retention"] = receipt["home_session_retention"]
    if "claude_session_scratch" in receipt:
        public_payload["claude_session_scratch"] = receipt["claude_session_scratch"]["summary"]
    if "batch_state_retention" in receipt:
        public_payload["batch_state_retention"] = [
            {
                "mode": (row.get("apply") or row.get("dry_run") or {}).get("mode"),
                "reclaimable_bytes": (row.get("dry_run") or {}).get("totals", {}).get("reclaimable_bytes", 0),
                "selected": len((row.get("dry_run") or {}).get("selected", [])),
                "allowlist": (row.get("dry_run") or {}).get("allowlist"),
                "errors": _apply_error_counts(row),
                **(
                    {
                        "one_off_artifacts": len(row["dry_run"]["one_off_artifacts"]),
                        "one_off_bytes": sum(item["bytes"] for item in row["dry_run"]["one_off_artifacts"]),
                    }
                    if "one_off_artifacts" in (row.get("dry_run") or {})
                    else {}
                ),
            }
            for row in receipt["batch_state_retention"]
        ]
    if receipt_path is not None:
        public_payload["receipt_id"] = Path(receipt_path).name
    return public_payload


def batch_state_retention_reports(repo_roots: list[Path], *, apply: bool) -> list[dict[str, Any]]:
    """Dry-run the snapshot allowlist, then apply it when this hygiene run applies.

    The sweep rewrites only ``tasks/*.snapshots`` and ``tasks/archive/*.snapshots``.
    Large files are reported for owner disposition. The run also performs a
    separate once-per-host ended-session sweep in main().
    """
    from scripts.maintenance.batch_state_retention import plan_retention

    reports: list[dict[str, Any]] = []
    for repo_root in repo_roots:
        batch_state = Path(repo_root) / "batch_state"
        try:
            info = batch_state.lstat()
        except OSError:
            continue
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            continue
        dry = plan_retention(batch_state, apply=False)
        entry: dict[str, Any] = {"dry_run": dry}
        if apply:
            entry["apply"] = plan_retention(batch_state, apply=True)
        reports.append(entry)
    return reports


def disk_watermark_alert_report(state_dir: Path) -> dict[str, Any]:
    """Run the once-per-crossing cto alert; a failure is reported as an error, never raised (#10871)."""
    try:
        return {"detail": disk_watermark_alert.check_and_alert(state_dir, PROJECT_ROOT), "errors": 0}
    except (ValueError, backup_failure_alert.AlertError, OSError) as exc:
        detail = "state I/O failed; retry retains the publication identity" if isinstance(exc, OSError) else str(exc)
        return {"detail": f"disk watermark alert failed: {detail}", "errors": 1}


@github_client.timer
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_roots = args.repo_root or args.default_repo_roots
    receipt = build_receipt(repo_roots, apply=bool(args.apply), **({"git_maintenance": True} if args.git_maintenance else {}))
    if args.git_maintenance:
        receipt_path = write_receipt(receipt, args.receipt_dir.expanduser().resolve())
        print(json.dumps(build_public_summary(receipt, receipt_path), ensure_ascii=False, sort_keys=True))
        return 1 if receipt["summary"]["errors"] else 0
    home_session_retention = home_session_retention_check.build_report()
    receipt["home_session_retention"] = home_session_retention
    receipt["batch_state_retention"] = batch_state_retention_reports(repo_roots, apply=bool(args.apply))
    receipt["claude_session_scratch"] = sweep_sessions(
        rollover_roots=[Path(root) / ".agent/thread-rollovers/claude" for root in repo_roots],
        apply=bool(args.apply),
    )
    receipt["summary"]["errors"] += receipt["claude_session_scratch"]["summary"]["errors"]
    if args.apply:
        receipt["disk_watermark_alert"] = disk_watermark_alert_report(args.alert_state_dir.expanduser())
        receipt["summary"]["errors"] += receipt["disk_watermark_alert"]["errors"]
        if receipt["disk_watermark_alert"]["errors"]:
            sys.stderr.write(f"{receipt['disk_watermark_alert']['detail']}\n")
    for line in home_session_retention_check.warning_lines(home_session_retention):
        sys.stderr.write(f"{line}\n")
    receipt_path = write_receipt(receipt, args.receipt_dir.expanduser().resolve())
    public_summary = build_public_summary(receipt, receipt_path)
    print(json.dumps(public_summary, ensure_ascii=False, sort_keys=True))
    return 1 if receipt["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
