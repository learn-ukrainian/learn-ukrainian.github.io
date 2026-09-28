"""List stale agent branches and delete only those with verifiable safe heads."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from scripts.common.git_context import UnsafeBranchNameError, sanitized_git_env, validate_plain_branch_name
from scripts.orchestration import reap_worktrees as reaper
from scripts.orchestration.task_family.git_safety import remote_protected_branches

AGENTS = frozenset({"codex", "claude", "grok", "agy", "kimi", "cursor", "deepseek", "gemini", "glm"})
PROTECTED = frozenset({"main", "master", "gh-pages", "production"})
SHA_RE = re.compile(r"[0-9a-f]{40,64}\Z")
PrLookup = Callable[[Path, str], tuple[list[reaper.PullRequestState], str | None]]


@dataclass(frozen=True)
class Branch:
    name: str
    remote_sha: str | None = None
    local_sha: str | None = None
    remote_date: int | None = None
    local_date: int | None = None


@dataclass(frozen=True)
class Decision:
    branch: str
    classification: str
    reason: str
    remote_sha: str | None
    local_sha: str | None
    age_days: int | None
    remote_deleted: bool = False
    local_deleted: bool = False


def _git(repo: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, env=sanitized_git_env(),
        capture_output=True, text=True, check=False, timeout=timeout,
    )


def _checked(repo: Path, *args: str) -> str:
    result = _git(repo, *args)
    if result.returncode:
        raise RuntimeError(f"git {args[0]} failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout


def _refs(repo: Path) -> list[Branch]:
    # NUL separates fields; Git ref names cannot contain NUL or a line feed.
    output = _checked(
        repo, "for-each-ref", "--format=%(refname)%00%(objectname)%00%(committerdate:unix)",
        "refs/remotes/origin", "refs/heads",
    )
    by_name: dict[str, dict[str, object]] = {}
    for line in output.splitlines():
        fields = line.split("\0")
        if len(fields) != 3:
            raise RuntimeError("git for-each-ref returned a malformed row")
        ref, sha, raw_date = fields
        if ref.startswith("refs/remotes/origin/"):
            kind, name = "remote", ref.removeprefix("refs/remotes/origin/")
        elif ref.startswith("refs/heads/"):
            kind, name = "local", ref.removeprefix("refs/heads/")
        else:
            continue
        if not SHA_RE.fullmatch(sha):
            raise RuntimeError("git for-each-ref returned an invalid SHA")
        row = by_name.setdefault(name, {"name": name})
        row[f"{kind}_sha"] = sha
        row[f"{kind}_date"] = int(raw_date) if raw_date.isdecimal() else None
    return [Branch(**by_name[name]) for name in sorted(by_name)]


def _candidate(name: str) -> bool:
    parts = name.split("/")
    return (
        name.startswith("pr-") or (
            len(parts) > 1
            and (parts[0] in AGENTS or parts[0] == "rescue"
                 or parts[-1].startswith("review-") or parts[-1].startswith("pr-"))
        )
    )


def _valid(name: str, repo: Path) -> bool:
    try:
        return validate_plain_branch_name(name, repo_root=repo) == name
    except UnsafeBranchNameError:
        return False


def _active_tasks(repo: Path) -> set[str]:
    task_dir = reaper.control_plane_root(repo) / "batch_state" / "tasks"
    active: set[str] = set()
    for path in task_dir.glob("*.json"):
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"cannot inspect task state {path.name}: {exc}") from exc
        if not isinstance(state, dict):
            raise RuntimeError(f"cannot inspect task state {path.name}: not an object")
        if state.get("status") not in {"running", "spawning"}:
            continue
        for key in ("worktree_branch", "branch"):
            value = state.get(key)
            if isinstance(value, str):
                active.add(value)
        prep = state.get("worktree_prep")
        if isinstance(prep, dict) and isinstance(prep.get("branch"), str):
            active.add(prep["branch"])
        agent, task_id = state.get("agent"), state.get("task_id")
        if isinstance(agent, str) and isinstance(task_id, str):
            active.add(f"{agent}/{task_id}")
    return active


def _origin_head(repo: Path, branch: str) -> str | None:
    output = _checked(repo, "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    rows = output.splitlines()
    if not rows:
        return None
    if len(rows) != 1:
        raise RuntimeError("git ls-remote returned multiple heads")
    fields = rows[0].split("\t")
    if len(fields) != 2 or fields[1] != f"refs/heads/{branch}" or not SHA_RE.fullmatch(fields[0]):
        raise RuntimeError("git ls-remote returned an unexpected head")
    return fields[0]


def _age(branch: Branch) -> int | None:
    dates = [date for date in (branch.remote_date, branch.local_date) if date is not None]
    return max(0, int(datetime.now(UTC).timestamp() - max(dates)) // 86400) if dates else None


def _classify(
    repo: Path, branch: Branch, *, worktree_branches: set[str], detached_heads: set[str],
    active_tasks: set[str], protected_branches: set[str], pr_lookup: PrLookup,
) -> Decision:
    name = branch.name

    def decision(kind: str, reason: str) -> Decision:
        return Decision(name, kind, reason, branch.remote_sha, branch.local_sha, _age(branch))

    if name in protected_branches or not _candidate(name):
        return decision("protected", "outside agent/scratch candidate namespace or protected name")
    if not _valid(name, repo):
        return decision("report-only", "invalid or unsafe branch name")
    if name in worktree_branches:
        return decision("skipped-worktree", "registered worktree uses this branch")
    if (branch.remote_sha or branch.local_sha) in detached_heads:
        return decision("skipped-worktree", "detached worktree uses this branch tip")
    if name in active_tasks:
        return decision("skipped-live-task", "running or spawning dispatch names this branch")
    if branch.remote_sha and branch.local_sha and branch.remote_sha != branch.local_sha:
        return decision("report-only", "local and remote tips differ")

    prs, error = pr_lookup(repo, name)
    if error is not None:
        return decision("report-only", f"PR lookup unavailable: {error}")
    if any(pr.state == "OPEN" for pr in prs):
        return decision("skipped-open-PR", "branch has an open PR")
    if any(pr.state not in {"MERGED", "CLOSED"} for pr in prs):
        return decision("report-only", "PR state is unknown")
    tip = branch.remote_sha or branch.local_sha
    if tip is None:
        return decision("report-only", "branch has no readable tip")
    if any(pr.head_sha == tip for pr in prs):
        return decision("delete-merged", "closed/merged PR head matches branch tip")
    main = _git(repo, "rev-parse", "--verify", "refs/remotes/origin/main")
    if main.returncode:
        return decision("report-only", "origin/main is unavailable")
    ancestor = _git(repo, "merge-base", "--is-ancestor", tip, main.stdout.strip())
    if ancestor.returncode == 0:
        return decision("delete-ancestor", "branch tip is an ancestor of origin/main")
    if ancestor.returncode != 1:
        return decision("report-only", "ancestry check failed")
    if prs:
        return decision("report-only", "closed/merged PR head does not match branch tip; unique commits")
    return decision("report-only", "no PR and unique commits")


def sweep(
    repo: Path, *, apply: bool = False, pr_lookup: PrLookup = reaper._query_pr_states,
    protected_lookup: Callable[[Path], set[str]] = remote_protected_branches,
) -> list[Decision]:
    branches = _refs(repo)
    try:
        protected = PROTECTED | protected_lookup(repo)
        protection_error = None
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        protected = PROTECTED
        protection_error = str(exc)
    worktrees = reaper.list_git_worktrees(repo)
    worktree_branches = {item.branch for item in worktrees if item.branch}
    detached_heads = {item.head for item in worktrees if item.detached and item.head}
    active = _active_tasks(repo)
    decisions: list[Decision] = []
    for branch in branches:
        if protection_error and _candidate(branch.name) and branch.name not in PROTECTED:
            decisions.append(Decision(
                branch.name, "report-only", f"branch protection query unavailable: {protection_error}",
                branch.remote_sha, branch.local_sha, _age(branch),
            ))
            continue
        verdict = _classify(
            repo, branch, worktree_branches=worktree_branches, detached_heads=detached_heads,
            active_tasks=active,
            protected_branches=protected, pr_lookup=pr_lookup,
        )
        if apply and verdict.classification.startswith("delete-"):
            # Recheck all volatile guards before each destructive call. In particular,
            # stale origin tracking refs cannot authorize deletion of a moved head.
            current_worktrees = reaper.list_git_worktrees(repo)
            verdict = _classify(
                repo, branch,
                worktree_branches={w.branch for w in current_worktrees if w.branch},
                detached_heads={w.head for w in current_worktrees if w.detached and w.head},
                active_tasks=_active_tasks(repo), protected_branches=protected,
                pr_lookup=pr_lookup,
            )
            if verdict.classification.startswith("delete-"):
                verdict = _apply(repo, branch, verdict)
        decisions.append(verdict)
    if apply:
        _checked(repo, "fetch", "--prune", "origin")
    return decisions


def _apply(repo: Path, branch: Branch, verdict: Decision) -> Decision:
    from dataclasses import replace

    name = branch.name
    if verdict.classification == "delete-ancestor":
        try:
            main = _origin_head(repo, "main")
            tracking_main = _checked(repo, "rev-parse", "refs/remotes/origin/main").strip()
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            return replace(verdict, classification="report-only", reason=f"origin/main verification failed: {exc}")
        if main != tracking_main:
            return replace(verdict, classification="report-only", reason="origin/main tracking ref is stale")
    if branch.remote_sha:
        try:
            live = _origin_head(repo, name)
            if live is not None:
                if live != branch.remote_sha:
                    return replace(verdict, classification="skipped-moved", reason="origin head changed")
                result = _git(
                    repo, "push", "--porcelain",
                    f"--force-with-lease=refs/heads/{name}:{branch.remote_sha}",
                    "origin", f":refs/heads/{name}", timeout=60,
                )
                if result.returncode:
                    output = (result.stdout + "\n" + result.stderr).strip()
                    if "[rejected]" in output and "(stale info)" in output:
                        return replace(verdict, classification="skipped-moved", reason="origin head changed during deletion")
                    return replace(verdict, classification="report-only", reason=f"remote deletion failed: {output}")
                verdict = replace(verdict, remote_deleted=True)
                if _origin_head(repo, name) is not None:
                    return replace(verdict, classification="report-only", reason="origin head remains after deletion")
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            return replace(verdict, classification="report-only", reason=f"remote verification failed: {exc}")
    if branch.local_sha:
        # The reaper checks the exact local head again before deleting it.
        error = reaper._prune_branch(repo, name, force=True, expected_head=branch.local_sha)
        if error:
            return replace(verdict, classification="report-only", reason=f"local deletion failed: {error}")
        verdict = replace(verdict, local_deleted=True)
    return verdict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "List stale agent and scratch branches with evidence for every decision.\n"
            "Use after dispatch cleanup; use --apply only to delete proven safe branches."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.hygiene.branch_sweep --json\n"
            "  .venv/bin/python -m scripts.hygiene.branch_sweep --apply --json\n"
            "Outputs: stdout receipts; --apply deletes qualifying remote and local refs and prunes tracking refs.\n"
            "Exit codes: 0 = sweep succeeded; 1 = repository or probe failure.\n"
            "Related: issue #9129; drive-epic §7a."
        ),
    )
    parser.add_argument("--apply", action="store_true", help="Delete proven safe branches; default is dry run.")
    parser.add_argument("--json", action="store_true", help="Print JSON receipts; default is readable text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo = reaper.resolve_repo_root()
        decisions = sweep(repo, apply=args.apply)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"branch_sweep: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"ok": True, "apply": args.apply, "decisions": [asdict(d) for d in decisions]}, indent=2))
    else:
        for item in decisions:
            print(f"{item.classification}: {item.branch} ({item.reason}; age_days={item.age_days})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
