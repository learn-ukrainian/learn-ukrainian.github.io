#!/usr/bin/env python3
"""Produce the nightly flake ledger from slow and merge-queue JUnit artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.ci.junit_results import parse_junit
from scripts.common import github_client
from scripts.common.flake_quarantine import REGISTRY, load_registry


def _gh(*args: str) -> str:
    result = github_client.run(["gh", *args], fresh=True, capture_output=True, text=True, check=True, timeout=120)
    return result.stdout


def fetch_queue_junit(destination: Path, *, since: date) -> tuple[dict[int, list[Path]], list[int]]:
    """Download last week's CI merge-group JUnit; keep missing run IDs visible."""
    raw = _gh(
        "run", "list", "--workflow", "ci.yml", "--event", "merge_group", "--status", "completed",
        "--created", f">={since.isoformat()}",
        "--limit", "1000", "--json", "databaseId,createdAt",
    )
    runs = json.loads(raw)
    if len(runs) == 1000:
        raise ValueError("queue run list reached the 1000-run limit; weekly denominator is incomplete")
    selected = {
        int(run["databaseId"])
        for run in runs
        if datetime.fromisoformat(run["createdAt"].replace("Z", "+00:00")).date() >= since
    }
    artifacts: dict[int, list[Path]] = {}
    missing: list[int] = []
    for run_id in sorted(selected):
        run_dir = destination / str(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        try:
            _gh("run", "download", str(run_id), "--pattern", "pytest-junit-shard-*", "--dir", str(run_dir))
        except subprocess.CalledProcessError:
            if not _reused_pytest(run_id):
                missing.append(run_id)
            continue
        paths = sorted(run_dir.rglob("*.xml"))
        if paths:
            artifacts[run_id] = paths
        else:
            missing.append(run_id)
    return artifacts, missing


def _reused_pytest(run_id: int) -> bool:
    """A queue run that reused a green pull_request run of the same tree executed no tests.

    ci.yml's Reuse check then succeeds and every pytest shard is skipped; such a
    run is outside the denominator, not a run with missing evidence.
    """
    jobs = json.loads(_gh("run", "view", str(run_id), "--json", "jobs"))["jobs"]
    shards = [job for job in jobs if job["name"].startswith("pytest (")]
    reuse = [job for job in jobs if job["name"] == "Reuse check"]
    return bool(shards) and all(job["conclusion"] == "skipped" for job in shards) and [
        job["conclusion"] for job in reuse
    ] == ["success"]


def make_ledger(
    entries: list[dict], queue_junit: dict[int, list[Path]], nightly_junit: list[Path], *,
    today: date, missing_runs: list[int] | None = None,
) -> dict:
    """Count distinct queue runs, recovered reruns, and nightly failures."""
    nightly = parse_junit(nightly_junit)
    queue_results = {run: parse_junit(paths) for run, paths in queue_junit.items()}
    queue_count = len(queue_junit) + len(missing_runs or [])
    rows = []
    for entry in entries:
        node_id = entry["node_id"]
        recovered = sorted(
            run for run, results in queue_results.items()
            if any(result.node_id == node_id and result.outcome == "passed" and result.reruns for result in results)
        )
        nightly_failures = [result.message for result in nightly if result.node_id == node_id and result.outcome in ("failed", "error")]
        percent = round(100 * len(recovered) / queue_count, 2) if queue_count else 0.0
        rows.append({
            "node_id": node_id,
            "fix_issue": entry["fix_issue"],
            "owner": entry["owner"],
            "expires_on": entry["expires_on"].isoformat(),
            "expired": today >= entry["expires_on"],
            "recovered_queue_run_ids": recovered,
            "queue_rerun_percent": percent,
            "escalate": percent > 5,
            "nightly_failures": nightly_failures,
        })
    return {
        "generated_on": today.isoformat(),
        "queue_run_count": queue_count,
        "queue_missing_junit_run_ids": sorted(missing_runs or []),
        "nightly_result_count": len(nightly),
        "entries": rows,
    }


def update_issues(ledger: dict, *, dry_run: bool) -> list[str]:
    """Announce expiry once, including a missed night, and escalate >5% use."""
    actions: list[str] = []
    for row in ledger["entries"]:
        if not row["expired"] and not row["escalate"]:
            continue
        number = str(row["fix_issue"])
        issue = json.loads(_gh("issue", "view", number, "--json", "state,labels,comments"))
        marker = f"<!-- flake-expiry:{row['node_id']}:{row['expires_on']} -->"
        needs_expiry = row["expired"] and not any(marker in comment["body"] for comment in issue["comments"])
        needs_escalation = row["escalate"] and "priority:high" not in {label["name"] for label in issue["labels"]}
        if not needs_expiry and not needs_escalation:
            continue
        if issue["state"] != "OPEN":
            actions.append(f"reopen #{number}")
            if not dry_run:
                _gh("issue", "reopen", number)
        if needs_expiry:
            message = (
                f"{marker}\nQuarantine expired on {row['expires_on']} for `{row['node_id']}`. "
                f"Reruns stop after seven grace days; owner: {row['owner']}."
            )
            actions.append(f"comment #{number}: expiry")
            if not dry_run:
                _gh("issue", "comment", number, "--body", message)
        if needs_escalation:
            actions.append(f"escalate #{number}: {row['queue_rerun_percent']}%")
            if not dry_run:
                _gh("issue", "edit", number, "--add-label", "priority:high")
                _gh("issue", "comment", number, "--body", (
                    f"Weekly queue rerun use exceeded D2's 5% threshold: {row['queue_rerun_percent']}% "
                    f"of {ledger['queue_run_count']} runs. Driver queue: priority:high; owner: {row['owner']}."
                ))
    return actions


@github_client.timer
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the D2 nightly flake ledger from pytest JUnit and queue artifacts.\n"
        "Use on schedule or for a dry-run replay, not as a replacement for CI Gate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/ci/flake_ledger.py --nightly-junit ci-artifacts/slow-junit.xml "
            "--fetch-queue --output ci-artifacts/flake-ledger.json\n"
            "  .venv/bin/python scripts/ci/flake_ledger.py --nightly-junit sample.xml "
            "--queue-dir queue-artifacts --dry-run --output ledger.json\n"
            "Outputs: JSON ledger; may reopen/comment/label fix issues unless --dry-run.\n"
            "Exit codes: 0 success; nonzero invalid input, missing evidence, or GitHub failure.\n"
            "Related: docs/epics/ci-speed-program.md D2; issue #9067."
        ),
    )
    parser.add_argument("--nightly-junit", type=Path, action="append", required=True,
                        help="Nightly pytest JUnit XML path; repeat for multiple files, e.g. slow-junit.xml")
    parser.add_argument("--queue-dir", type=Path,
                        help="Directory of <run-id>/*.xml queue artifacts for offline replay")
    parser.add_argument("--fetch-queue", action="store_true",
                        help="Download the last seven days of merge_group JUnit from GitHub Actions")
    parser.add_argument("--registry", type=Path, default=REGISTRY,
                        help="Quarantine YAML path; default tests/flake_quarantine.yaml")
    parser.add_argument("--output", type=Path, required=True,
                        help="Write JSON ledger to this path, e.g. ci-artifacts/flake-ledger.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show issue actions without changing GitHub issues")
    args = parser.parse_args(argv)
    if bool(args.queue_dir) == bool(args.fetch_queue):
        parser.error("choose exactly one of --queue-dir or --fetch-queue")
    today = datetime.now(UTC).date()
    entries = load_registry(args.registry)
    with tempfile.TemporaryDirectory(prefix="flake-ledger-") as temp:
        queue_dir = Path(temp) if args.fetch_queue else args.queue_dir
        if args.fetch_queue:
            queue, missing = fetch_queue_junit(queue_dir, since=today - timedelta(days=7))
        else:
            queue = {int(directory.name): sorted(directory.rglob("*.xml")) for directory in queue_dir.iterdir() if directory.is_dir()}
            missing = [run for run, paths in queue.items() if not paths]
            queue = {run: paths for run, paths in queue.items() if paths}
        ledger = make_ledger(entries, queue, args.nightly_junit, today=today, missing_runs=missing)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"output": str(args.output), "queue_runs": ledger["queue_run_count"],
                          "missing_junit": len(missing), "entries": len(entries),
                          "issue_actions": update_issues(ledger, dry_run=args.dry_run)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
