#!/usr/bin/env python3
"""Per-event and per-job CI duration and queue-wait measurement tool.

Answers 'how long does CI take, per event and per job, and how long do PRs
wait in the merge queue' using GitHub Actions API data.

Features:
- Event filtering: pull_request, merge_group, push, or all.
- Time-window filtering: ISO timestamp (e.g. 2026-08-22) or relative (e.g. 10d, 24h).
- Metrics: n, average, median, p95 (nearest-rank), and max duration in minutes.
- Run-level wall-clock duration analysis.
- Merge-queue time-in-queue and kick count per PR.
- Formats: Markdown / text tables and stable-ordered JSON.
- Offline fixture support for deterministic testing.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

DEFAULT_WORKFLOW = "CI"
DEFAULT_WORKFLOW_FILE = "ci.yml"
DEFAULT_REPO = "learn-ukrainian/learn-ukrainian.github.io"
DEFAULT_SUBPROCESS_TIMEOUT = 60
MAX_PAGINATION_PAGES = 10

QUEUE_BRANCH_RE = re.compile(r"gh-readonly-queue/[^/]+/pr-(\d+)-([0-9a-fA-F]+)")
PR_NUM_RE = re.compile(r"(?:pr[-/]|issue/|pull/|#|^)(\d+)")


def nearest_rank_percentile(values: Sequence[float], percentile: float = 95.0) -> float:
    """Compute percentile using the nearest-rank method (NIST / ISO standard).

    For an ordered list of N items and percentile P in [0, 100]:
        k = ceil(P / 100 * N)
    clamped to 1 <= k <= N, returning the item at index (k - 1).
    """
    if not values:
        return 0.0
    if not (0.0 <= percentile <= 100.0):
        raise ValueError(f"percentile must be between 0 and 100, got {percentile}")
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    k = math.ceil((percentile / 100.0) * n)
    k = max(1, min(n, k))
    return sorted_vals[k - 1]


def compute_metric_stats(values: Sequence[float]) -> dict[str, Any]:
    """Compute summary statistics (n, avg, median, p95, max) for a list of values (minutes)."""
    if not values:
        return {
            "avg": 0.0,
            "max": 0.0,
            "median": 0.0,
            "n": 0,
            "p95": 0.0,
        }
    return {
        "avg": round(statistics.mean(values), 1),
        "max": round(max(values), 1),
        "median": round(statistics.median(values), 1),
        "n": len(values),
        "p95": round(nearest_rank_percentile(values, 95.0), 1),
    }


def parse_since(since_str: str, now: datetime | None = None) -> datetime:
    """Parse a since string into a timezone-aware UTC datetime.

    Accepts:
    - ISO timestamps: '2026-08-22', '2026-08-22T00:00:00Z', '2026-08-22T00:00:00+00:00'
    - Relative durations: '10d', '24h', '30m', '2w', or plain integer (treated as days).
    """
    text = since_str.strip()
    if not text:
        raise ValueError("Empty since string")

    # Check relative duration pattern
    rel_match = re.fullmatch(r"(\d+)\s*([dhwmsDHWMS])?", text)
    if rel_match:
        val = int(rel_match.group(1))
        unit = (rel_match.group(2) or "d").lower()
        clock = now if now is not None else datetime.now(UTC)
        clock = clock.replace(tzinfo=UTC) if clock.tzinfo is None else clock.astimezone(UTC)

        if unit == "d":
            return clock - timedelta(days=val)
        if unit == "h":
            return clock - timedelta(hours=val)
        if unit == "w":
            return clock - timedelta(weeks=val)
        if unit == "m":
            return clock - timedelta(minutes=val)
        if unit == "s":
            return clock - timedelta(seconds=val)

    # ISO format parsing
    iso_text = text
    if iso_text.endswith("Z"):
        iso_text = iso_text[:-1] + "+00:00"
    elif "T" not in iso_text and len(iso_text) == 10 and iso_text.count("-") == 2:
        iso_text = f"{iso_text}T00:00:00+00:00"

    try:
        parsed = datetime.fromisoformat(iso_text)
    except ValueError as exc:
        raise ValueError(
            f"Invalid --since format {since_str!r}. Expected ISO timestamp (e.g. 2026-08-22) "
            f"or relative duration (e.g. 10d, 24h)."
        ) from exc

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_github_timestamp(raw: str | None) -> datetime | None:
    """Safely parse a GitHub API timestamp string into a UTC datetime."""
    if not raw or not isinstance(raw, str):
        return None
    text = raw.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def extract_pr_number(head_branch: str | None) -> int | None:
    """Extract PR number from a queue or feature branch name."""
    if not head_branch:
        return None
    queue_m = QUEUE_BRANCH_RE.search(head_branch)
    if queue_m:
        return int(queue_m.group(1))
    pr_m = PR_NUM_RE.search(head_branch)
    if pr_m:
        return int(pr_m.group(1))
    return None


@dataclass(frozen=True)
class JobStats:
    name: str
    n: int
    avg_minutes: float
    median_minutes: float
    p95_minutes: float
    max_minutes: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "avg_minutes": self.avg_minutes,
            "max_minutes": self.max_minutes,
            "median_minutes": self.median_minutes,
            "n": self.n,
            "name": self.name,
            "p95_minutes": self.p95_minutes,
        }


@dataclass(frozen=True)
class PRQueueStats:
    pr_number: int
    head_branch: str
    status: str
    kicks: int
    queue_entry_at: str
    queue_completed_at: str | None
    time_in_queue_minutes: float | None
    runner_wait_minutes: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "head_branch": self.head_branch,
            "kicks": self.kicks,
            "pr_number": self.pr_number,
            "queue_completed_at": self.queue_completed_at,
            "queue_entry_at": self.queue_entry_at,
            "runner_wait_minutes": self.runner_wait_minutes,
            "status": self.status,
            "time_in_queue_minutes": self.time_in_queue_minutes,
        }


@dataclass(frozen=True)
class EventReport:
    event: str
    runs_count: int
    wall_clock_minutes: dict[str, Any]
    jobs: list[JobStats]
    queue_timing: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "jobs": [j.to_dict() for j in self.jobs],
            "runs_count": self.runs_count,
            "wall_clock_minutes": self.wall_clock_minutes,
        }
        if self.queue_timing is not None:
            data["queue_timing"] = self.queue_timing
        return data


@dataclass(frozen=True)
class TimingReport:
    workflow: str
    repo: str
    since: str
    generated_at: str
    events: dict[str, EventReport]

    def to_dict(self) -> dict[str, Any]:
        return {
            "events": {k: v.to_dict() for k, v in sorted(self.events.items())},
            "generated_at": self.generated_at,
            "repo": self.repo,
            "since": self.since,
            "workflow": self.workflow,
        }


def _gh_env(token: str | None = None) -> dict[str, str]:
    """Prepare environment for gh subprocess calls."""
    env = dict(os.environ)
    if token:
        env["GH_TOKEN"] = token
        env["GITHUB_TOKEN"] = token
    elif "GH_TOKEN" not in env and "GITHUB_TOKEN" not in env:
        # Check standard user config directory
        config_dir = os.path.expanduser("~/.config/gh")
        if os.path.isdir(config_dir):
            env["GH_CONFIG_DIR"] = config_dir
    return env


def gh_api_get(
    path: str,
    *,
    token: str | None = None,
    timeout: int = DEFAULT_SUBPROCESS_TIMEOUT,
) -> dict[str, Any] | list[Any]:
    """Execute a read-only GitHub API GET request via `gh api`."""
    env = _gh_env(token)
    cmd = ["gh", "api", path]
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("`gh` CLI tool is required but not installed or not on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"GitHub API request timed out after {timeout}s: {path}") from exc

    if completed.returncode != 0:
        err_msg = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"gh api {path} failed (exit {completed.returncode}): {err_msg}")

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse JSON response from gh api {path}: {exc}") from exc


def resolve_repository(repo_arg: str | None = None) -> str:
    """Resolve owner/repo string from CLI arg, environment, or git remote."""
    if repo_arg and repo_arg.strip():
        return repo_arg.strip()

    env_repo = os.environ.get("GITHUB_REPOSITORY")
    if env_repo and "/" in env_repo:
        return env_repo.strip()

    try:
        completed = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            url = completed.stdout.strip()
            # Parse git remote url: git@github.com:owner/repo.git or https://github.com/owner/repo.git
            m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
            if m:
                return m.group(1)
    except Exception:
        pass

    return DEFAULT_REPO


def load_runs_and_jobs_from_fixture(
    fixture_path: str | Path,
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Load workflow runs and job mapping from a local JSON fixture file."""
    path = Path(fixture_path)
    if not path.is_file():
        raise FileNotFoundError(f"Fixture file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, list):
        # Format: list of runs with nested jobs
        runs: list[dict[str, Any]] = []
        jobs_by_run: dict[str, list[dict[str, Any]]] = {}
        for item in data:
            if isinstance(item, dict):
                runs.append(item)
                run_id = str(item.get("id"))
                if "jobs" in item and isinstance(item["jobs"], list):
                    jobs_by_run[run_id] = item["jobs"]
        return runs, jobs_by_run

    if isinstance(data, dict):
        runs = data.get("workflow_runs") or data.get("runs") or []
        jobs_by_run = data.get("jobs_by_run_id") or {}
        # Convert keys to string
        str_jobs_by_run = {str(k): v for k, v in jobs_by_run.items()}
        return runs, str_jobs_by_run

    raise ValueError("Invalid fixture format: expected JSON object or array")


def fetch_workflow_runs_from_api(
    repo: str,
    workflow_file: str,
    *,
    since_dt: datetime | None = None,
    limit: int | None = None,
    event: str | None = None,
    branch: str | None = None,
    status: str | None = "completed",
    token: str | None = None,
    max_pages: int = MAX_PAGINATION_PAGES,
) -> list[dict[str, Any]]:
    """Fetch completed workflow runs from the GitHub Actions API with bounded pagination."""
    all_runs: list[dict[str, Any]] = []
    page = 1
    per_page = 100

    query_parts = [f"per_page={per_page}"]
    if status:
        query_parts.append(f"status={status}")
    if event and event != "all":
        query_parts.append(f"event={event}")
    if branch:
        query_parts.append(f"branch={branch}")

    while page <= max_pages:
        path = f"repos/{repo}/actions/workflows/{workflow_file}/runs?{'&'.join(query_parts)}&page={page}"
        data = gh_api_get(path, token=token)
        if not isinstance(data, dict):
            break

        runs_page = data.get("workflow_runs", [])
        if not runs_page:
            break

        reached_since_cutoff = False
        for run in runs_page:
            if not isinstance(run, dict):
                continue
            created_at = parse_github_timestamp(run.get("created_at"))
            if since_dt is not None and created_at is not None and created_at < since_dt:
                reached_since_cutoff = True
                continue

            all_runs.append(run)
            if limit is not None and len(all_runs) >= limit:
                return all_runs

        if reached_since_cutoff or len(runs_page) < per_page:
            break

        page += 1

    return all_runs


def fetch_run_jobs_from_api(
    repo: str,
    run_id: int,
    *,
    token: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch completed jobs for a given workflow run."""
    path = f"repos/{repo}/actions/runs/{run_id}/jobs?per_page=100"
    data = gh_api_get(path, token=token)
    if isinstance(data, dict):
        return data.get("jobs", [])
    if isinstance(data, list):
        return data
    return []


def analyze_timings(
    runs: Sequence[Mapping[str, Any]],
    jobs_fetcher: Any,
    *,
    workflow_name: str = DEFAULT_WORKFLOW,
    repo_name: str = DEFAULT_REPO,
    since_str: str = "",
    event_filter: str = "all",
    branch_filter: str | None = None,
    since_dt: datetime | None = None,
    limit: int | None = None,
) -> TimingReport:
    """Analyze CI durations and queue timings from workflow runs and job data."""
    # Filter runs
    filtered_runs: list[dict[str, Any]] = []
    for r in runs:
        if not isinstance(r, Mapping):
            continue
        # Status must be completed
        if str(r.get("status") or "").lower() != "completed":
            continue

        # Event filter
        event = str(r.get("event") or "").strip()
        if event_filter != "all" and event != event_filter:
            continue

        # Branch filter
        if branch_filter:
            head_branch = str(r.get("head_branch") or "")
            if head_branch != branch_filter and not head_branch.endswith(f"/{branch_filter}"):
                continue

        # Since filter
        if since_dt is not None:
            created_at = parse_github_timestamp(r.get("created_at"))
            if created_at is not None and created_at < since_dt:
                continue

        filtered_runs.append(dict(r))

    # Sort runs chronologically by created_at
    filtered_runs.sort(key=lambda r: str(r.get("created_at") or ""))

    # If limit is set, take the most recent N runs
    if limit is not None and len(filtered_runs) > limit:
        filtered_runs = filtered_runs[-limit:]

    # Group runs by event
    runs_by_event: dict[str, list[dict[str, Any]]] = {}
    for r in filtered_runs:
        ev = str(r.get("event") or "unknown")
        runs_by_event.setdefault(ev, []).append(r)

    target_events = (
        ["pull_request", "merge_group", "push"]
        if event_filter == "all"
        else [event_filter]
    )

    event_reports: dict[str, EventReport] = {}

    for ev in target_events:
        ev_runs = runs_by_event.get(ev, [])
        wall_clock_durs: list[float] = []
        job_durs_by_name: dict[str, list[float]] = {}

        for r in ev_runs:
            run_id = int(r["id"])
            st = parse_github_timestamp(r.get("run_started_at") or r.get("created_at"))
            ut = parse_github_timestamp(r.get("updated_at"))
            if st is not None and ut is not None and ut >= st:
                wall_clock_durs.append((ut - st).total_seconds() / 60.0)

            # Fetch jobs
            if callable(jobs_fetcher):
                jobs = jobs_fetcher(run_id)
            elif isinstance(jobs_fetcher, Mapping):
                jobs = jobs_fetcher.get(str(run_id)) or jobs_fetcher.get(run_id) or []
            else:
                jobs = []

            for j in jobs:
                if not isinstance(j, Mapping):
                    continue
                # Skip unstarted or skipped jobs
                if str(j.get("status") or "").lower() != "completed":
                    continue
                if str(j.get("conclusion") or "").lower() == "skipped":
                    continue

                jst = parse_github_timestamp(j.get("started_at"))
                jct = parse_github_timestamp(j.get("completed_at"))
                if jst is not None and jct is not None and jct >= jst:
                    dur_min = (jct - jst).total_seconds() / 60.0
                    j_name = str(j.get("name") or "Unnamed Job").strip()
                    job_durs_by_name.setdefault(j_name, []).append(dur_min)

        # Build JobStats list
        job_stats_list: list[JobStats] = []
        for name in sorted(job_durs_by_name.keys()):
            stats = compute_metric_stats(job_durs_by_name[name])
            job_stats_list.append(
                JobStats(
                    name=name,
                    n=stats["n"],
                    avg_minutes=stats["avg"],
                    median_minutes=stats["median"],
                    p95_minutes=stats["p95"],
                    max_minutes=stats["max"],
                )
            )

        wall_clock_stats = compute_metric_stats(wall_clock_durs)

        # Queue timing for merge_group
        queue_timing_report: dict[str, Any] | None = None
        if ev == "merge_group":
            queue_timing_report = _compute_merge_group_queue_timings(ev_runs)

        event_reports[ev] = EventReport(
            event=ev,
            runs_count=len(ev_runs),
            wall_clock_minutes=wall_clock_stats,
            jobs=job_stats_list,
            queue_timing=queue_timing_report,
        )

    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return TimingReport(
        workflow=workflow_name,
        repo=repo_name,
        since=since_str or (since_dt.strftime("%Y-%m-%dT%H:%M:%SZ") if since_dt else ""),
        generated_at=now_iso,
        events=event_reports,
    )


def _compute_merge_group_queue_timings(
    merge_group_runs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compute time-in-queue and kicks per PR for merge_group runs.

    Definition:
      PR time-in-queue is measured from the earliest `merge_group` workflow run
      `created_at` timestamp for that PR's queue branch until the completion (`updated_at`)
      of the final successful run that landed it.
      Kicks count prior failed or cancelled merge_group attempts for the PR.

    Limits:
      Does not include internal GitHub queue scheduling latency prior to workflow run creation.
    """
    prs_by_num: dict[int, list[Mapping[str, Any]]] = {}
    for r in merge_group_runs:
        head_branch = str(r.get("head_branch") or "")
        pr_num = extract_pr_number(head_branch)
        if pr_num is not None:
            prs_by_num.setdefault(pr_num, []).append(r)

    pr_stats_list: list[PRQueueStats] = []
    landed_queue_times: list[float] = []
    total_kicks = 0

    for pr_num in sorted(prs_by_num.keys()):
        runs = prs_by_num[pr_num]
        runs.sort(key=lambda r: str(r.get("created_at") or ""))

        earliest_created = parse_github_timestamp(runs[0].get("created_at"))
        earliest_started = parse_github_timestamp(
            runs[0].get("run_started_at") or runs[0].get("created_at")
        )

        runner_wait_min: float | None = None
        if earliest_created is not None and earliest_started is not None:
            runner_wait_min = round(
                max(0.0, (earliest_started - earliest_created).total_seconds() / 60.0),
                1,
            )

        # Check outcomes and kicks
        kicks = 0
        success_run: Mapping[str, Any] | None = None
        for r in runs:
            conc = str(r.get("conclusion") or "").lower()
            if conc == "success":
                success_run = r
            elif conc in ("failure", "cancelled", "timed_out"):
                kicks += 1

        total_kicks += kicks
        head_branch = str(runs[-1].get("head_branch") or "")

        if success_run is not None:
            status = "landed"
            completed_at = parse_github_timestamp(success_run.get("updated_at"))
            entry_iso = (
                earliest_created.strftime("%Y-%m-%dT%H:%M:%SZ")
                if earliest_created
                else runs[0].get("created_at", "")
            )
            completed_iso = (
                completed_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                if completed_at
                else str(success_run.get("updated_at", ""))
            )

            time_in_queue: float | None = None
            if earliest_created is not None and completed_at is not None:
                time_in_queue = round(
                    max(0.0, (completed_at - earliest_created).total_seconds() / 60.0),
                    1,
                )
                landed_queue_times.append(time_in_queue)

            pr_stats_list.append(
                PRQueueStats(
                    pr_number=pr_num,
                    head_branch=head_branch,
                    status=status,
                    kicks=kicks,
                    queue_entry_at=entry_iso,
                    queue_completed_at=completed_iso,
                    time_in_queue_minutes=time_in_queue,
                    runner_wait_minutes=runner_wait_min,
                )
            )
        else:
            status = "failed" if kicks > 0 else "in_progress"
            entry_iso = (
                earliest_created.strftime("%Y-%m-%dT%H:%M:%SZ")
                if earliest_created
                else runs[0].get("created_at", "")
            )
            pr_stats_list.append(
                PRQueueStats(
                    pr_number=pr_num,
                    head_branch=head_branch,
                    status=status,
                    kicks=kicks,
                    queue_entry_at=entry_iso,
                    queue_completed_at=None,
                    time_in_queue_minutes=None,
                    runner_wait_minutes=runner_wait_min,
                )
            )

    queue_time_summary = compute_metric_stats(landed_queue_times)

    return {
        "definition": (
            "Time from first merge_group run creation for the PR until successful landing run completion."
        ),
        "limits": "Does not include internal GitHub merge-queue scheduling latency prior to run creation.",
        "prs": [p.to_dict() for p in pr_stats_list],
        "summary": {
            "kicks_total": total_kicks,
            "prs_count": len(pr_stats_list),
            "time_in_queue_minutes": queue_time_summary,
        },
    }


def render_markdown(report: TimingReport) -> str:
    """Render a human-readable Markdown report matching baseline format."""
    lines: list[str] = [
        f"# CI Timing & Queue Report — {report.workflow}",
        "",
        f"- **Repository:** `{report.repo}`",
        f"- **Window Since:** `{report.since or 'all available'}`",
        f"- **Generated At:** `{report.generated_at}`",
        "",
    ]

    for ev_name, ev_report in sorted(report.events.items()):
        lines.append(f"## {ev_name} ({ev_report.runs_count} completed runs)")
        lines.append("")

        if not ev_report.jobs:
            lines.append("_No completed job records found._")
            lines.append("")
        else:
            lines.append("| job | n | avg | med | p95 | max |")
            lines.append("|---|---|---|---|---|---|")
            for j in ev_report.jobs:
                lines.append(
                    f"| {j.name} | {j.n} | {j.avg_minutes:.1f} | {j.median_minutes:.1f} | "
                    f"{j.p95_minutes:.1f} | {j.max_minutes:.1f} |"
                )

            # Add run wall-clock row
            wc = ev_report.wall_clock_minutes
            lines.append(
                f"| **Run Wall-clock** | {wc['n']} | **{wc['avg']:.1f}** | **{wc['median']:.1f}** | "
                f"**{wc['p95']:.1f}** | **{wc['max']:.1f}** |"
            )
            lines.append("")

        # Merge group queue metrics
        if ev_report.queue_timing:
            q = ev_report.queue_timing
            summary = q.get("summary", {})
            q_stats = summary.get("time_in_queue_minutes", {})
            lines.append("### merge_group Time-in-Queue & Kicks")
            lines.append(f"> **Definition:** {q.get('definition', '')}")
            lines.append(f"> **Limits:** {q.get('limits', '')}")
            lines.append("")
            lines.append(
                f"- **PRs Evaluated:** {summary.get('prs_count', 0)} | "
                f"**Total Kicks (Gate Failures):** {summary.get('kicks_total', 0)}"
            )
            if q_stats.get("n", 0) > 0:
                lines.append(
                    f"- **Landed PR Time-in-Queue (min):** "
                    f"avg {q_stats.get('avg', 0.0):.1f} | "
                    f"median {q_stats.get('median', 0.0):.1f} | "
                    f"p95 {q_stats.get('p95', 0.0):.1f} | "
                    f"max {q_stats.get('max', 0.0):.1f}"
                )
            lines.append("")

            prs = q.get("prs", [])
            if prs:
                lines.append("| PR | Status | Kicks | Queue Entry (UTC) | Queue Exit (UTC) | In-Queue (min) | Runner Wait (min) |")
                lines.append("|---|---|---|---|---|---|---|")
                for p in prs:
                    q_exit = p.get("queue_completed_at") or "-"
                    in_q = f"{p.get('time_in_queue_minutes'):.1f}" if p.get("time_in_queue_minutes") is not None else "-"
                    r_wait = f"{p.get('runner_wait_minutes'):.1f}" if p.get("runner_wait_minutes") is not None else "-"
                    lines.append(
                        f"| #{p.get('pr_number')} | {p.get('status')} | {p.get('kicks')} | "
                        f"{p.get('queue_entry_at')} | {q_exit} | {in_q} | {r_wait} |"
                    )
                lines.append("")

    return "\n".join(lines)


def render_json(report: TimingReport) -> str:
    """Render a stable-ordered JSON string."""
    return json.dumps(report.to_dict(), indent=2, sort_keys=True)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Compute per-event and per-job CI durations and queue timings from GitHub Actions.",
    )
    parser.add_argument(
        "--workflow",
        default=DEFAULT_WORKFLOW,
        help="Workflow name or file (default: %(default)s).",
    )
    parser.add_argument(
        "--event",
        choices=["pull_request", "merge_group", "push", "all"],
        default="all",
        help="CI event filter (default: %(default)s).",
    )
    parser.add_argument(
        "--since",
        default="",
        help="Window cutoff: ISO timestamp (e.g. 2026-08-22) or relative duration (e.g. 10d, 24h).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of most recent matching runs to evaluate (default: all matching runs in window).",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Filter runs by head_branch (e.g. main).",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="GitHub owner/repo (default: detected from git origin or env).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output structured JSON instead of Markdown tables.",
    )
    parser.add_argument(
        "--fixture",
        "--file",
        dest="fixture_file",
        default=None,
        help="Path to a recorded JSON fixture of runs and jobs (offline mode).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    since_dt: datetime | None = None
    if args.since:
        try:
            since_dt = parse_since(args.since)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

    repo = resolve_repository(args.repo)
    workflow = args.workflow
    workflow_file = DEFAULT_WORKFLOW_FILE if workflow in ("CI", "ci.yml") else workflow

    if args.fixture_file:
        try:
            runs, jobs_by_run = load_runs_and_jobs_from_fixture(args.fixture_file)
        except Exception as exc:
            print(f"Error loading fixture {args.fixture_file}: {exc}", file=sys.stderr)
            return 1
        jobs_fetcher: Any = jobs_by_run
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        try:
            runs = fetch_workflow_runs_from_api(
                repo=repo,
                workflow_file=workflow_file,
                since_dt=since_dt,
                limit=args.limit,
                event=args.event,
                branch=args.branch,
                token=token,
            )
        except RuntimeError as exc:
            print(f"Error querying GitHub Actions API: {exc}", file=sys.stderr)
            return 1

        jobs_cache: dict[int, list[dict[str, Any]]] = {}

        def fetch_jobs_cached(run_id: int) -> list[dict[str, Any]]:
            if run_id not in jobs_cache:
                jobs_cache[run_id] = fetch_run_jobs_from_api(repo, run_id, token=token)
            return jobs_cache[run_id]

        jobs_fetcher = fetch_jobs_cached

    report = analyze_timings(
        runs=runs,
        jobs_fetcher=jobs_fetcher,
        workflow_name=workflow,
        repo_name=repo,
        since_str=args.since,
        event_filter=args.event,
        branch_filter=args.branch,
        since_dt=since_dt,
        limit=args.limit,
    )

    if args.json_output:
        print(render_json(report))
    else:
        print(render_markdown(report))

    return 0


if __name__ == "__main__":
    sys.exit(main())
