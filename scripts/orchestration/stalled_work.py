"""Report committed dispatch work awaiting delivery or review fixes (#11212).

Only scan refs, cadence state and explicitly requested Fleet messages are written.
Task records and dispatch branches are never changed.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.common.task_store_paths import tasks_dir as default_tasks_dir
from scripts.fleet_comms.authority import AuthorityService
from scripts.orchestration import stale_task_records as stale
from scripts.orchestration.integration_sweep import GitHubAdapter, SweepError, lookup_verdict
from scripts.orchestration.worktree_claims import RELEASED_TASK_STATUSES

LANES = frozenset({"codex-devops", "claude-infra", "codex-atlas", "grok-monitor", "gemini-open-model-data"})
UNPUSHED_STATUSES = frozenset({"needs_finalize", "failed", "timeout", "timed_out", "timed-out"})
TERMINAL = RELEASED_TASK_STATUSES | UNPUSHED_STATUSES
MAX_AGE_DAYS = 14
GRACE_SECONDS = 2 * 3600


def owner(record: dict[str, Any]) -> str:
    """Dispatch initiator is the owner, independently of the worker's provider."""
    initiator = record.get("initiator")
    return initiator if isinstance(initiator, str) and initiator in LANES else "claude-cto"


def abandoned(record: dict[str, Any]) -> bool:
    receipt = record.get("worktree_abandon")
    return record.get("status") == "terminal_abandon" or (
        isinstance(receipt, dict)
        and receipt.get("schema") == "terminal-abandon.v1"
        and receipt.get("disposition") == "ABANDON"
    )


def load_records(tasks: Path, now: datetime) -> tuple[list[stale.Candidate], list[str]]:
    records, errors = [], []
    for path in stale._iter_record_files(tasks):
        try:
            record = json.loads(path.read_text())
            if not isinstance(record, dict):
                raise ValueError("not an object")
            stat = path.stat()
        except (OSError, ValueError) as exc:
            errors.append(f"task record {path.name}: {type(exc).__name__}")
            continue
        age = stale._record_age_days(record, stat.st_mtime_ns, now)
        # Keep live claims of any age; they still suppress duplicate repair work.
        if not abandoned(record) and (record.get("status") not in TERMINAL or 0 <= age < MAX_AGE_DAYS):
            records.append(stale.Candidate(path, stat.st_mtime_ns, record, age))
    return records, errors


def git_value(checkout: Path, args: list[str]) -> str:
    result = stale._git(args, cwd=checkout, timeout=30)
    if result is None or result.returncode:
        raise RuntimeError("git evidence unavailable: " + args[0])
    return result.stdout.strip()


def related(candidate: stale.Candidate, pr: dict[str, Any]) -> bool:
    record = candidate.record
    return (
        record.get("worktree_branch") == pr["headRefName"]
        or record.get("review_branch") == pr["headRefName"]
        or record.get("pr") == pr["number"]
    )


def finished(candidate: stale.Candidate) -> datetime:
    return stale._parse_ts(candidate.record.get("finished_at")) or datetime.fromtimestamp(candidate.mtime_ns / 1e9, UTC)


def scan(tasks: Path, checkouts: dict[str, Path], *, now: datetime, adapter_factory=GitHubAdapter) -> dict[str, Any]:
    """Use batched fresh remote refs, complete open PRs, and trusted exact-head verdicts."""
    candidates, errors = load_records(tasks, now)
    rows: list[dict[str, Any]] = []
    terminal_count = sum(
        c.record.get("status") in TERMINAL and c.record.get("repository") in checkouts for c in candidates
    )
    open_count = 0

    def add(candidate, kind, commit, since, pr=None):
        rows.append(
            {
                "task_id": candidate.task_id if candidate else "unknown",
                "lane": owner(candidate.record) if candidate else "claude-cto",
                "repository": slug,
                "kind": kind,
                "commit": commit,
                "pr": pr,
                "since": since.isoformat(),
                "age_hours": round((now - since).total_seconds() / 3600, 2),
            }
        )

    for slug, checkout in checkouts.items():
        group = [c for c in candidates if c.record.get("repository") == slug]
        terminal = [c for c in group if c.record.get("status") in TERMINAL]
        live = [c for c in group if c.record.get("status") not in TERMINAL]
        facts = stale.collect_repo_facts(slug, checkout, stale.fleet_fetch_target(slug))
        if facts.error or facts.fetch_error:
            errors.append(f"{slug}: git repository evidence unavailable")
            continue
        adapter = adapter_factory(checkout)
        try:
            prs = adapter.list_open_prs(slug)
            login = adapter.identity()
        except (SweepError, RuntimeError, OSError, ValueError) as exc:
            errors.append(f"{slug}: GitHub evidence unavailable ({type(exc).__name__})")
            continue
        open_count += len(prs)
        by_branch = {pr["headRefName"]: pr for pr in prs}
        pending_prs = []
        # Cache reachability across reused worktrees and repeated task records.
        reachability: dict[tuple[str, str], str] = {}

        def ahead(tip, exclusion, reachability=reachability, checkout=checkout):
            key = (tip, exclusion)
            if key not in reachability:
                reachability[key] = git_value(checkout, ["rev-list", "--max-count=1", tip, "--not", exclusion, "--"])
            return reachability[key]

        for c in terminal:
            branch = stale._normalize_branch(c.record.get("worktree_branch"))
            if not branch or c.record.get("review"):
                continue
            since = finished(c)
            try:
                # Reuse the existing branch/worktree classifier without settlement.
                stale._classify_one(c, facts)
                local = c.evidence.get("local_branch_sha") or (facts.local_branches or {}).get(branch)
                tree = c.record.get("worktree_path")
                tips = [local] if local else []
                if isinstance(tree, str) and (Path(tree) / ".git").exists():
                    tips.append(git_value(Path(tree), ["rev-parse", "--verify", "HEAD"]))
                unpushed = None
                if c.record.get("status") in UNPUSHED_STATUSES:
                    # A renamed branch can retain the recorded work after its
                    # original checkout and branch name disappear.
                    tips.extend(
                        sha
                        for sha in stale.recorded_work_commits(c.record)
                        if sha in (facts.local_branches or {}).values()
                    )
                    for tip in dict.fromkeys(tips):
                        unpushed = ahead(tip, f"--glob={facts.target.ref_prefix}/*")
                        if unpushed:
                            add(c, "unpushed", unpushed, since)
                            break
                if unpushed:
                    continue
                remote = (facts.remote_heads or {}).get(branch)
                # Already landed branches are cleanup debt, not stalled work.
                if (
                    remote
                    and branch not in by_branch
                    and c.age_days * 86400 > GRACE_SECONDS
                    and ahead(remote, f"{facts.target.ref_prefix}/main")
                ):
                    pending_prs.append((c, remote, since))
            except RuntimeError as exc:
                errors.append(f"{c.task_id}: {exc}")

        if pending_prs:
            # Squash merges do not make the old branch head an ancestor of main.
            # Existing merged-PR indexing supplies the exact head identity instead.
            merged = stale.build_pull_index(
                slug,
                oldest_start=min(c.task_start or since for c, _, since in pending_prs),
                pager=stale.gh_pull_page,
                max_pages=stale.DEFAULT_MAX_PR_PAGES,
            )
            if merged.error or merged.covered_since is not None:
                errors.append(f"{slug}: merged PR evidence incomplete")
            else:
                for candidate, remote, since in pending_prs:
                    if remote not in merged.merged_by_sha:
                        add(candidate, "no_open_pr", remote, since)

        for pr in prs:
            if any(related(c, pr) for c in live):
                continue
            try:
                comments = adapter.comments(slug, pr["number"])
                verdict = lookup_verdict(comments, pr["headRefOid"], login)
                if verdict.state == "unknown":
                    errors.append(f"{slug} PR #{pr['number']}: verdict unknown ({verdict.reason})")
                if verdict.state != "CHANGES_REQUESTED" or verdict.review_mode != "cross_family":
                    continue
                # lookup_verdict selects the standing trusted marker. Use its posting
                # time too, so a late publication gets the full repair grace period.
                posted = [
                    stale._parse_ts(cm.get("created_at") or cm.get("createdAt"))
                    for cm in comments
                    if (selected := lookup_verdict([cm], pr["headRefOid"], login)).state == "CHANGES_REQUESTED"
                    and selected.task == verdict.task
                    and selected.started == verdict.started
                ]
                matches = sorted((c for c in terminal if related(c, pr)), key=lambda c: c.age_days)
                times = [t for t in [verdict.started, *posted] if t is not None]
                if matches:
                    times.append(finished(matches[0]))
                since = max(times)
                if (now - since).total_seconds() > GRACE_SECONDS:
                    add(matches[0] if matches else None, "changes_requested", pr["headRefOid"], since, pr["number"])
            except (SweepError, RuntimeError, OSError, ValueError) as exc:
                errors.append(f"{slug} PR #{pr['number']}: comments unavailable ({type(exc).__name__})")
    rows.sort(key=lambda row: (row["lane"], row["task_id"], row["kind"]))
    return {"rows": rows, "errors": errors, "terminal_records": terminal_count, "open_prs": open_count}


def route(report: dict[str, Any], *, cycle: int, service: AuthorityService) -> list[str]:
    """Retry stable messages in a cycle; unresolved rows return in the next cycle."""
    if report["errors"]:
        raise ValueError("routing refused: incomplete report")
    groups = defaultdict(list)
    for row in report["rows"]:
        groups[row["lane"]].append({k: v for k, v in row.items() if k != "age_hours"})
    messages = []
    # A separate summary is still sent when unknown owners route to the CTO.
    packets = [(lane, "lane", rows) for lane, rows in sorted(groups.items())]
    packets.append(("claude-cto", "summary", [r for _, rs in sorted(groups.items()) for r in rs]))
    for lane, kind, rows in packets:
        rows = sorted(rows, key=lambda row: json.dumps(row, sort_keys=True))
        payload = json.dumps(rows, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode()).hexdigest()
        key = f"stalled:{cycle}:{kind}:{lane}:{digest}"
        message = service.enqueue_supervisory_request(
            sender="claude-cto",
            recipient=lane,
            body=f"Stalled work {kind}. Return each row to its owning lane until landed or explicitly abandoned.\n{payload}",
            correlation_id=f"stalled:{cycle}",
            idempotency_key=key,
        )
        messages.append(message.message_id)
    return messages


def run(args, *, now: datetime) -> dict[str, Any]:
    repository = next(repo.github for repo in stale.fleet_repos.load_fleet_repos().values() if repo.default)
    report = scan(args.tasks_dir, {repository: stale.PROJECT_ROOT}, now=now)
    if args.route and not report["errors"]:
        with AuthorityService(root=None) as service:
            report["messages"] = route(report, cycle=int(now.timestamp()) // args.cadence_seconds, service=service)
    return report


def tick(args, *, now: datetime) -> dict[str, Any]:
    """Serialize keeper invocations and checkpoint only a complete successful cycle."""
    args.state_file.parent.mkdir(parents=True, exist_ok=True)
    with args.state_file.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        last = json.loads(args.state_file.read_text()) if args.state_file.exists() else {}
        if not isinstance(last, dict) or any(
            key not in {"report", "route"} or type(value) is not int or value < 0 for key, value in last.items()
        ):
            raise ValueError("cadence checkpoint malformed")
        cycle = int(now.timestamp()) // args.cadence_seconds
        mode = "route" if args.route else "report"
        if last.get(mode) == cycle:
            return {"skipped": "cadence", "cycle": cycle}
        report = run(args, now=now)
        if not report["errors"]:
            last[mode] = cycle
            temporary = args.state_file.with_suffix(".tmp")
            with temporary.open("w") as state:
                json.dump(last, state)
                state.flush()
                os.fsync(state.fileno())
            temporary.replace(args.state_file)
        return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report committed dispatch work stalled before landing.\nUse for supervision, never for branch or task-record repair.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.orchestration.stalled_work stalled
  .venv/bin/python -m scripts.orchestration.stalled_work stalled --route
  .venv/bin/python -m scripts.orchestration.stalled_work stalled --tick
Outputs: JSON on stdout; --route enqueues Fleet requests; --tick writes cadence state.
Fresh Git scan refs are fetched; no task records or dispatch branches are written.
Exit codes: 0 complete or cadence skip; 1 incomplete evidence; 2 invalid usage/config.
Related: #11212; docs/runbooks/stalled-work.md; stale_task_records.py
""",
    )
    parser.add_argument(
        "command", choices=["stalled"], help="Report stalled terminal dispatch work from the last 14 days"
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=default_tasks_dir(),
        help="Task store, default shared batch_state/tasks; example: ./fixture-tasks",
    )
    parser.add_argument(
        "--route", action="store_true", help="Enqueue lane requests and a CTO summary, default report-only"
    )
    parser.add_argument(
        "--tick",
        action="store_true",
        help="Keeper entry point; obey cadence and LU_STALLED_WORK_ROUTE_ENABLED, default off",
    )
    parser.add_argument(
        "--cadence-minutes",
        type=int,
        default=os.environ.get("LU_STALLED_WORK_CADENCE_MINUTES", "30"),
        help="Tick cadence in minutes, default 30 or LU_STALLED_WORK_CADENCE_MINUTES; example: 60",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=default_tasks_dir().parent / "stalled-work" / "cadence.json",
        help="Tick checkpoint, default shared batch_state/stalled-work/cadence.json; example: ./cadence.json",
    )
    args = parser.parse_args(argv)
    if args.cadence_minutes <= 0:
        parser.error("cadence must be positive")
    enabled = os.environ.get("LU_STALLED_WORK_ROUTE_ENABLED", "0")
    if enabled not in {"0", "1"}:
        parser.error("LU_STALLED_WORK_ROUTE_ENABLED must be 0 or 1")
    args.route = args.route or (args.tick and enabled == "1")
    args.cadence_seconds = args.cadence_minutes * 60
    try:
        report = tick(args, now=datetime.now(UTC)) if args.tick else run(args, now=datetime.now(UTC))
    except (OSError, RuntimeError, ValueError) as exc:
        report = {"errors": [f"stalled scan failed ({type(exc).__name__})"]}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
