#!/usr/bin/env python3
"""Prove a PR is MERGED, then close it out: reap its dispatch worktrees
through the P0 reaper and prove the remote and local branch are gone.

``gh pr merge`` (or the merge queue) reporting MERGED is not closeout --
worktree reaping and branch deletion are frequently skipped afterward. This
CLI makes the full closeout a single command instead of a checklist an
orchestrator can forget.

    .venv/bin/python -m scripts.orchestration.merge_closeout <pr-number> --apply

Default is dry-run. See docs/runbooks/worktree-cleanup.md
§ Immediate cleanup after merge.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.orchestration import reap_worktrees as rw
from scripts.orchestration import scheduled_worktree_cleanup as swc

DEFAULT_TIMEOUT = 30


class MergeCloseoutError(RuntimeError):
    """Raised when the PR's MERGED state cannot be proven via GitHub."""


@dataclass(frozen=True)
class PullRequestInfo:
    number: int
    state: str
    head_ref_name: str | None
    head_sha: str | None


@dataclass(frozen=True)
class BranchStatus:
    branch: str
    remote_gone: bool
    local_gone: bool
    remote_error: str | None = None
    local_error: str | None = None


@dataclass(frozen=True)
class CloseoutResult:
    pr: PullRequestInfo
    apply: bool
    matched_worktrees: list[str]
    reap_results: list[dict[str, Any]]
    branch_status: BranchStatus | None
    ok: bool
    errors: list[str] = field(default_factory=list)


def _run_gh(
    args: list[str],
    *,
    cwd: Path,
    timeout: int = DEFAULT_TIMEOUT,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=rw.sanitized_git_env(),
    )


def fetch_pr_info(repo_root: Path, pr_number: int, *, repo: str | None = None) -> PullRequestInfo:
    """Read PR state from GitHub. Raises when the state cannot be proven."""
    args = [
        "gh",
        "pr",
        "view",
        str(pr_number),
        "--json",
        "number,state,headRefName,headRefOid",
    ]
    if repo:
        args += ["--repo", repo]
    try:
        proc = _run_gh(args, cwd=repo_root)
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        raise MergeCloseoutError(f"gh pr view {pr_number} failed: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise MergeCloseoutError(
            f"gh pr view {pr_number} failed: {detail or f'exit {proc.returncode}'}"
        )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise MergeCloseoutError(f"gh pr view {pr_number} returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise MergeCloseoutError(f"gh pr view {pr_number} returned a non-object payload")

    state = str(payload.get("state") or "").upper()
    head_ref = payload.get("headRefName")
    head_sha = payload.get("headRefOid")
    return PullRequestInfo(
        number=pr_number,
        state=state,
        head_ref_name=str(head_ref) if head_ref else None,
        head_sha=str(head_sha) if head_sha else None,
    )


def find_matching_worktrees(repo_root: Path, pr: PullRequestInfo) -> list[rw.WorktreeInfo]:
    """Worktrees under ``.worktrees/`` whose branch or exact HEAD matches the PR.

    Matching by exact HEAD sha (not only branch name) is required to also
    catch detached review-checkout siblings of the same merged commit.
    """
    primary = rw.primary_checkout_root(repo_root)
    matches: list[rw.WorktreeInfo] = []
    for info in rw.list_git_worktrees(repo_root):
        resolved = info.path.resolve()
        if resolved in (repo_root.resolve(), primary.resolve()):
            continue
        if not rw.is_under_worktrees(repo_root, resolved):
            continue
        branch_match = pr.head_ref_name is not None and info.branch == pr.head_ref_name
        sha_match = pr.head_sha is not None and info.head == pr.head_sha
        if branch_match or sha_match:
            matches.append(info)
    return matches


def reap_matched_worktrees(
    repo_root: Path,
    matches: list[rw.WorktreeInfo],
    *,
    apply: bool,
    live_cwds: set[Path] | None = None,
) -> list[rw.ReapResult]:
    """Delegate removal to the P0 reaper. This is not a second deletion hand."""
    if not matches:
        return []
    return rw.reap_worktrees(
        repo_root=repo_root,
        apply=apply,
        target_paths=[info.path for info in matches],
        merged_pr_only=True,
        prune_merged_branches=True,
        safe_only=True,
        live_cwds=live_cwds,
        require_activity_probe=apply,
    )


def _guard_branch_not_open(repo_root: Path, branch: str) -> str | None:
    """Return an error message when it is unsafe to delete ``branch``.

    Reuses the P0 reaper's ``gh pr list`` guard (``rw._query_pr_states``).
    When no worktree remains, the reaper's own guard never runs, so this
    fallback path must re-run it: a branch with a currently OPEN PR -- even
    one opened after the merged PR this closeout targets -- must never be
    deleted, and a failed guard query must fail closed rather than be read
    as "no open PR".
    """
    prs, pr_error = rw._query_pr_states(repo_root, branch)
    if pr_error is not None:
        return f"PR guard unavailable; refusing to delete: {pr_error}"
    for pr_state in prs:
        if pr_state.state == "OPEN":
            return f"branch has an open PR (#{pr_state.number}); refusing to delete"
    return None


def _local_branch_head(repo_root: Path, branch: str) -> tuple[str | None, str | None]:
    """Return ``(sha, error)`` for a local branch ref.

    ``--quiet`` suppresses git's error message only when the ref genuinely
    does not exist, so a nonzero exit with no stderr means "absent" and a
    nonzero exit with stderr means the lookup itself failed -- the latter
    must never be read as "branch is gone".
    """
    proc = rw._run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=repo_root,
    )
    if proc.returncode == 0:
        return (proc.stdout or "").strip(), None
    stderr = (proc.stderr or "").strip()
    return (None, stderr) if stderr else (None, None)


def verify_branch_gone(
    repo_root: Path,
    pr: PullRequestInfo,
    *,
    apply: bool,
) -> BranchStatus | None:
    """Prove the merged PR's remote and local branch are gone.

    Only ever deletes a branch whose live head exactly matches the merged PR
    head -- the same exact-head proof the P0 reaper requires -- and only
    when the reaper's open-PR guard clears it. This is a fallback for
    whatever the reap step above did not already clean up. A failed lookup
    (unreachable origin, failed gh call) is never read as "branch is gone";
    it leaves the branch alone and is reported as an error.
    """
    branch = pr.head_ref_name
    if not branch:
        return None
    expected_head = pr.head_sha

    guard_error: str | None = None
    if apply and expected_head is not None:
        guard_error = _guard_branch_not_open(repo_root, branch)

    remote_error: str | None = None
    live_remote, live_remote_error = swc._live_origin_head(repo_root, branch)
    if live_remote_error is not None:
        remote_error = f"cannot verify origin HEAD: {live_remote_error}"
    elif apply and live_remote is not None:
        if expected_head is not None and live_remote == expected_head:
            remote_error = guard_error or swc._delete_origin_branch(
                repo_root, branch=branch, expected_head=expected_head
            )
        else:
            remote_error = "origin head does not match merged PR head; refusing to delete"
    remote_after, remote_after_error = swc._live_origin_head(repo_root, branch)
    if remote_after_error is not None:
        remote_gone = False
        remote_error = remote_error or f"cannot verify origin HEAD: {remote_after_error}"
    else:
        remote_gone = remote_after is None

    local_error: str | None = None
    local_head, local_lookup_error = _local_branch_head(repo_root, branch)
    if local_lookup_error is not None:
        local_error = f"cannot verify local branch: {local_lookup_error}"
    elif apply and local_head is not None:
        if expected_head is not None and local_head == expected_head:
            local_error = guard_error or rw._prune_branch(
                repo_root, branch, force=True, expected_head=expected_head
            )
        else:
            local_error = "local head does not match merged PR head; refusing to delete"
    local_after, local_after_error = _local_branch_head(repo_root, branch)
    if local_after_error is not None:
        local_gone = False
        local_error = local_error or f"cannot verify local branch: {local_after_error}"
    else:
        local_gone = local_after is None

    return BranchStatus(
        branch=branch,
        remote_gone=remote_gone,
        local_gone=local_gone,
        remote_error=remote_error,
        local_error=local_error,
    )


def run_merge_closeout(
    repo_root: Path,
    pr_number: int,
    *,
    repo: str | None = None,
    apply: bool = False,
    live_cwds: set[Path] | None = None,
) -> CloseoutResult:
    pr = fetch_pr_info(repo_root, pr_number, repo=repo)
    if pr.state != "MERGED":
        raise MergeCloseoutError(f"PR #{pr_number} is not MERGED (state={pr.state or 'UNKNOWN'})")

    matches = find_matching_worktrees(repo_root, pr)
    reap_results = reap_matched_worktrees(repo_root, matches, apply=apply, live_cwds=live_cwds)

    errored_paths = {result.path for result in reap_results if result.action == "error"}
    errors: list[str] = [
        f"{result.path}: {result.error or result.reason}"
        for result in reap_results
        if result.action == "error"
    ]

    # A worktree the reaper left retained/skipped (dirty, active dispatch, PR
    # guard, etc.) is not an ``error`` action -- it must still block success,
    # or a retained dirty worktree reports a clean closeout. Re-enumerate the
    # live worktrees rather than trusting the reap actions alone.
    worktree_residuals: list[str] = []
    if apply and matches:
        still_present = {str(info.path) for info in rw.list_git_worktrees(repo_root)}
        for info in matches:
            path_str = str(info.path)
            if path_str in still_present:
                worktree_residuals.append(path_str)
                if path_str not in errored_paths:
                    errors.append(f"{path_str}: worktree still registered after reap (not removed)")

    branch_status = verify_branch_gone(repo_root, pr, apply=apply)
    if branch_status is not None:
        if branch_status.remote_error:
            errors.append(f"remote branch {branch_status.branch}: {branch_status.remote_error}")
        if branch_status.local_error:
            errors.append(f"local branch {branch_status.branch}: {branch_status.local_error}")

    residual = apply and (
        bool(worktree_residuals)
        or (branch_status is not None and not (branch_status.remote_gone and branch_status.local_gone))
    )

    return CloseoutResult(
        pr=pr,
        apply=apply,
        matched_worktrees=[str(info.path) for info in matches],
        reap_results=[rw._result_payload(result) for result in reap_results],
        branch_status=branch_status,
        ok=not errors and not residual,
        errors=errors,
    )


def _result_to_dict(result: CloseoutResult) -> dict[str, Any]:
    return {
        "pr": asdict(result.pr),
        "apply": result.apply,
        "matched_worktrees": result.matched_worktrees,
        "reap_results": result.reap_results,
        "branch_status": asdict(result.branch_status) if result.branch_status else None,
        "ok": result.ok,
        "errors": result.errors,
    }


def _format_text(result: CloseoutResult) -> str:
    lines = [
        f"PR #{result.pr.number}: {result.pr.state}",
        f"mode: {'apply' if result.apply else 'dry-run'}",
    ]
    if result.matched_worktrees:
        lines.append("matched worktrees:")
        lines.extend(f"  {path}" for path in result.matched_worktrees)
    else:
        lines.append("matched worktrees: none")
    for entry in result.reap_results:
        lines.append(f"  reap {entry['action']}: {entry['path']} ({entry['reason']})")
    if result.branch_status is not None:
        status = result.branch_status
        lines.append(
            f"branch {status.branch}: remote_gone={status.remote_gone} local_gone={status.local_gone}"
        )
        if status.remote_error:
            lines.append(f"  remote_error: {status.remote_error}")
        if status.local_error:
            lines.append(f"  local_error: {status.local_error}")
    if result.errors:
        lines.append("errors:")
        lines.extend(f"  {error}" for error in result.errors)
    lines.append("OK" if result.ok else "RESIDUAL / ERROR")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="merge_closeout",
        description=(
            "Prove a PR is MERGED, reap its dispatch worktrees through the P0 "
            "reaper, and prove its remote and local branch are gone. "
            "Dry-run by default."
        ),
        epilog="Related: docs/runbooks/worktree-cleanup.md § Immediate cleanup after merge.",
    )
    parser.add_argument("pr_number", type=int, help="Pull request number.")
    parser.add_argument("--repo", help="owner/name; defaults to the repo in the current directory.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root to operate in (default: the primary checkout).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Reap matched worktrees and delete residual branches. Default is dry-run.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = (
        args.repo_root.resolve()
        if args.repo_root
        else rw.primary_checkout_root(rw.resolve_repo_root())
    )

    try:
        result = run_merge_closeout(repo_root, args.pr_number, repo=args.repo, apply=args.apply)
    except MergeCloseoutError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"merge_closeout: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(_result_to_dict(result), indent=2))
    else:
        print(_format_text(result))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
