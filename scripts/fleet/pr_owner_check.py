#!/usr/bin/env python3
"""List open PRs that have no live dispatch-task owner, in every fleet repository.

Use each CTO cycle to find open PRs nobody is accountable for, then dispatch an owner for
each. Ownership is the dispatch task record (repository + worktree_branch + a live
process), never the PR author or a branch prefix. Read-only: it never dispatches,
comments, or edits records.

A PR is reported when its branch has no live owner. The reason names the branch's latest
task: none, or its final status (failed/timeout/cancelled/no_deliverable/crashed/... or
done with the PR still open). Live means status spawning/running and the supervisor
process is still the one the record names.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass

from scripts.common import github_client
from scripts.orchestration.fleet_repos import FleetRepo, FleetRepoError, load_fleet_repos

# Repositories whose open PRs the CTO cycle must account for ("both repositories").
DEFAULT_REPO_KEYS = ("public", "infra-private")
_ACTIVE = {"spawning", "running"}
_GH_TIMEOUT_SECONDS = 60
_PR_LIMIT = 200
_PR_FIELDS = "number,title,headRefName,isCrossRepository,isDraft,url"


@dataclass(frozen=True)
class Unowned:
    repo: str
    number: int
    branch: str
    reason: str
    last_task: str | None = None


def _supervisor_alive(record: dict) -> bool:
    pid = record.get("pid")
    if pid is None:
        return True  # spawning, supervisor not yet started
    from scripts.dispatcher.worker import _identity

    return _identity(pid) == record.get("process_start")


def _record_repository(record: dict, repos: Mapping[str, FleetRepo]) -> str:
    slug = record.get("repository") or record.get("repository_id")
    if not slug:
        key = record.get("repo")
        slug = repos[key].github if key in repos else next(r.github for r in repos.values() if r.default)
    return str(slug).casefold()


def evaluate(
    open_prs: Mapping[str, list[dict]],
    records: list[dict],
    repos: Mapping[str, FleetRepo],
    alive: Callable[[dict], bool] = _supervisor_alive,
) -> list[Unowned]:
    """Return every open PR (keyed by repo slug) lacking a live owner task."""
    by_branch: dict[tuple[str, str], list[dict]] = {}
    for record in records:
        branch = record.get("worktree_branch")
        if branch:
            by_branch.setdefault((_record_repository(record, repos), branch), []).append(record)
    unowned = []
    for slug, prs in open_prs.items():
        for pr in prs:
            branch = pr.get("headRefName") or ""
            fork = bool(pr.get("isCrossRepository"))
            tasks = [] if fork else by_branch.get((slug.casefold(), branch), [])
            if any(t.get("status") in _ACTIVE and alive(t) for t in tasks):
                continue
            last = max(tasks, key=lambda t: t.get("started_at") or "", default=None)
            if last is None:
                reason = "fork PR: no branch owner possible" if fork else "no task record owns this branch"
            elif last.get("status") in _ACTIVE:
                reason = f"last owner {last['status']} but its supervisor is gone"
            elif last.get("status") == "done":
                reason = "last owner finished done, PR still open (not MERGED)"
            else:
                reason = f"last owner ended {last.get('status')}, PR not MERGED"
            unowned.append(Unowned(slug, int(pr["number"]), branch, reason, last["task_id"] if last else None))
    return unowned


def fetch_open_prs(slug: str) -> list[dict]:
    """Open PRs of one repository; raises RuntimeError when GitHub cannot be read."""
    proc = github_client.run(
        ["gh", "pr", "list", "--repo", slug, "--state", "open", "--limit", str(_PR_LIMIT), "--json", _PR_FIELDS],
        capture_output=True, text=True, check=False, timeout=_GH_TIMEOUT_SECONDS,
    )
    try:
        prs = json.loads(proc.stdout) if proc.returncode == 0 else None
    except ValueError:
        prs = None
    if not isinstance(prs, list):
        raise RuntimeError(f"cannot list open PRs of {slug}: {(proc.stderr or '').strip()[:200]}")
    if len(prs) >= _PR_LIMIT:
        raise RuntimeError(f"{slug} has at least {_PR_LIMIT} open PRs; the list may be truncated")
    return prs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "List open PRs, in both fleet repositories, that have no live dispatch-task owner.\n"
            "Use it every CTO cycle (cto/references/cycle.md); then dispatch an owner for each PR "
            "it prints. Not for judging review or CI state."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/fleet/pr_owner_check.py\n"
            "  .venv/bin/python scripts/fleet/pr_owner_check.py --repo infra-private --json\n\n"
            "Outputs: one line per unowned PR on stdout (or a JSON list with --json); no side effects.\n"
            "Exit codes: 0 every open PR has a live owner task; 1 at least one PR is unowned;\n"
            "  2 GitHub, the repository catalog or the task records could not be read (unknown, never clean).\n"
            "Related: dispatch task records (scripts/dispatch.py list), scripts/config/fleet_repos.yaml, "
            "epic #10453."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo", action="append", metavar="KEY",
        help=f"fleet_repos.yaml key to check, repeatable (default: {' and '.join(DEFAULT_REPO_KEYS)})",
    )
    parser.add_argument("--json", action="store_true", help="print the unowned PRs as a JSON list (default: text lines)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repos = load_fleet_repos()
        keys = args.repo or list(DEFAULT_REPO_KEYS)
        unknown = [k for k in keys if k not in repos]
        if unknown:
            raise FleetRepoError(f"unknown fleet repo key(s): {', '.join(unknown)}")
        from scripts.dispatcher import store

        records = store.list_tasks(strict=True)
        open_prs = {repos[k].github: fetch_open_prs(repos[k].github) for k in keys}
    except (FleetRepoError, RuntimeError, ValueError, OSError) as exc:
        print(f"UNKNOWN: {exc}", file=sys.stderr)
        return 2
    unowned = evaluate(open_prs, records, repos)
    if args.json:
        print(json.dumps([asdict(u) for u in unowned], indent=2))
    else:
        for u in unowned:
            print(f"{u.repo}#{u.number} {u.branch}: {u.reason}" + (f" [{u.last_task}]" if u.last_task else ""))
        total = sum(len(p) for p in open_prs.values())
        print(f"{total - len(unowned)}/{total} open PRs have a live owner task", file=sys.stderr)
    return 1 if unowned else 0


if __name__ == "__main__":
    sys.exit(main())
