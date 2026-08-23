"""Unit tests for scripts/ci/ci_timings.py (issue #7174).

Hermetic, offline test suite verifying:
- Nearest-rank p95 percentile against hand-computed values.
- ISO and relative --since window parsing and boundary filtering.
- Queue timing and kick calculation from recorded API fixtures.
- Stable-ordered JSON serialization and Markdown table formatting.
- CLI argument parsing and error handling.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from scripts.ci.ci_timings import (
    DEFAULT_REPO,
    DEFAULT_WORKFLOW,
    EventReport,
    JobStats,
    TimingReport,
    analyze_timings,
    compute_metric_stats,
    extract_pr_number,
    fetch_run_jobs_from_api,
    fetch_workflow_runs_from_api,
    gh_api_get,
    load_runs_and_jobs_from_fixture,
    main,
    nearest_rank_percentile,
    parse_since,
    render_json,
    render_markdown,
)

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ci_timings" / "sample_ci_runs.json"


def test_nearest_rank_percentile_hand_computed() -> None:
    """Validate nearest-rank percentile against hand-computed reference values.

    Formula:
      k = ceil((P / 100) * N), clamped to [1, N]
      value = sorted_values[k - 1]
    """
    # Empty list
    assert nearest_rank_percentile([], 95.0) == 0.0

    # N = 1 -> always the single element
    assert nearest_rank_percentile([42.0], 95.0) == 42.0
    assert nearest_rank_percentile([42.0], 50.0) == 42.0

    # N = 5, values = [10, 20, 30, 40, 50]
    # P = 95 -> k = ceil(0.95 * 5) = ceil(4.75) = 5 -> index 4 (50)
    # P = 50 -> k = ceil(0.50 * 5) = ceil(2.5) = 3 -> index 2 (30)
    # P = 20 -> k = ceil(0.20 * 5) = ceil(1.0) = 1 -> index 0 (10)
    v5 = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert nearest_rank_percentile(v5, 95.0) == 50.0
    assert nearest_rank_percentile(v5, 50.0) == 30.0
    assert nearest_rank_percentile(v5, 20.0) == 10.0

    # N = 10, values = [1..10]
    # P = 95 -> k = ceil(0.95 * 10) = ceil(9.5) = 10 -> index 9 (10)
    # P = 90 -> k = ceil(0.90 * 10) = ceil(9.0) = 9 -> index 8 (9)
    # P = 50 -> k = ceil(0.50 * 10) = ceil(5.0) = 5 -> index 4 (5)
    v10 = [float(i) for i in range(1, 11)]
    assert nearest_rank_percentile(v10, 95.0) == 10.0
    assert nearest_rank_percentile(v10, 90.0) == 9.0
    assert nearest_rank_percentile(v10, 50.0) == 5.0

    # N = 20, values = [1..20]
    # P = 95 -> k = ceil(0.95 * 20) = ceil(19.0) = 19 -> index 18 (19)
    # P = 99 -> k = ceil(0.99 * 20) = ceil(19.8) = 20 -> index 19 (20)
    v20 = [float(i) for i in range(1, 21)]
    assert nearest_rank_percentile(v20, 95.0) == 19.0
    assert nearest_rank_percentile(v20, 99.0) == 20.0

    # Unsorted input should produce identical result to sorted
    v_unsorted = [50.0, 10.0, 40.0, 20.0, 30.0]
    assert nearest_rank_percentile(v_unsorted, 95.0) == 50.0

    # Invalid percentile raises ValueError
    with pytest.raises(ValueError, match="percentile must be between 0 and 100"):
        nearest_rank_percentile(v5, -1.0)
    with pytest.raises(ValueError, match="percentile must be between 0 and 100"):
        nearest_rank_percentile(v5, 101.0)


def test_compute_metric_stats() -> None:
    """Test summary stats calculation (n, avg, median, p95, max)."""
    assert compute_metric_stats([]) == {
        "avg": 0.0,
        "max": 0.0,
        "median": 0.0,
        "n": 0,
        "p95": 0.0,
    }

    vals = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    stats = compute_metric_stats(vals)
    assert stats["n"] == 8
    assert stats["avg"] == 5.0
    assert stats["median"] == 4.5
    assert stats["max"] == 9.0
    # N=8, P=95: k = ceil(0.95 * 8) = ceil(7.6) = 8 -> 9.0
    assert stats["p95"] == 9.0


def test_parse_since_iso_and_relative() -> None:
    """Test parsing ISO timestamps and relative lookback strings."""
    fixed_now = datetime(2026, 8, 23, 18, 0, 0, tzinfo=UTC)

    # ISO date-only
    d1 = parse_since("2026-08-22")
    assert d1 == datetime(2026, 8, 22, 0, 0, 0, tzinfo=UTC)

    # ISO date-time with Z
    d2 = parse_since("2026-08-22T14:30:00Z")
    assert d2 == datetime(2026, 8, 22, 14, 30, 0, tzinfo=UTC)

    # ISO date-time with offset
    d3 = parse_since("2026-08-22T16:30:00+02:00")
    assert d3 == datetime(2026, 8, 22, 14, 30, 0, tzinfo=UTC)

    # Relative: 24h
    r_24h = parse_since("24h", now=fixed_now)
    assert r_24h == datetime(2026, 8, 22, 18, 0, 0, tzinfo=UTC)

    # Relative: 10d
    r_10d = parse_since("10d", now=fixed_now)
    assert r_10d == datetime(2026, 8, 13, 18, 0, 0, tzinfo=UTC)

    # Relative: plain integer
    r_plain = parse_since("3", now=fixed_now)
    assert r_plain == datetime(2026, 8, 20, 18, 0, 0, tzinfo=UTC)

    # Relative: minutes and weeks
    r_min = parse_since("30m", now=fixed_now)
    assert r_min == datetime(2026, 8, 23, 17, 30, 0, tzinfo=UTC)

    r_w = parse_since("2w", now=fixed_now)
    assert r_w == datetime(2026, 8, 9, 18, 0, 0, tzinfo=UTC)

    # Invalid string
    with pytest.raises(ValueError, match="Invalid --since format"):
        parse_since("invalid-date-string")
    with pytest.raises(ValueError, match="Empty since string"):
        parse_since("   ")


def test_since_window_boundary_filtering() -> None:
    """Prove --since cutoff strictly discards runs created before the boundary."""
    runs: list[dict[str, Any]] = [
        {
            "id": 101,
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "created_at": "2026-08-22T05:00:00Z",
            "updated_at": "2026-08-22T05:15:00Z",
            "run_started_at": "2026-08-22T05:00:00Z",
        },
        {
            "id": 102,
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "created_at": "2026-08-22T10:00:00Z",
            "updated_at": "2026-08-22T10:15:00Z",
            "run_started_at": "2026-08-22T10:00:00Z",
        },
        {
            "id": 103,
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "created_at": "2026-08-23T01:00:00Z",
            "updated_at": "2026-08-23T01:15:00Z",
            "run_started_at": "2026-08-23T01:00:00Z",
        },
    ]
    cutoff = datetime(2026, 8, 22, 8, 0, 0, tzinfo=UTC)
    report = analyze_timings(
        runs=runs,
        jobs_fetcher={},
        since_dt=cutoff,
        event_filter="push",
    )
    push_report = report.events["push"]
    # Run 101 (created at 05:00) is before 08:00 cutoff; runs 102 and 103 must be retained
    assert push_report.runs_count == 2
    assert push_report.wall_clock_minutes["n"] == 2
    assert push_report.wall_clock_all_minutes["n"] == 2


def test_extract_pr_number() -> None:
    """Test extracting PR numbers from branch names."""
    assert (
        extract_pr_number("gh-readonly-queue/main/pr-7170-0224500326cbe490cd890784f67741ca1d8ef65b")
        == 7170
    )
    assert extract_pr_number("issue/7139-monitor-dual-host-slice") == 7139
    assert extract_pr_number("pull/6863") == 6863
    assert extract_pr_number("pr-4811") == 4811
    assert extract_pr_number("main") is None
    assert extract_pr_number("") is None
    assert extract_pr_number(None) is None


def test_analyze_timings_on_recorded_fixture() -> None:
    """Verify complete timing analysis against the offline recorded fixture."""
    runs, jobs_by_run = load_runs_and_jobs_from_fixture(_FIXTURE_PATH)
    assert len(runs) == 15
    assert len(jobs_by_run) == 15

    report = analyze_timings(
        runs=runs,
        jobs_fetcher=jobs_by_run,
        workflow_name="CI",
        repo_name=DEFAULT_REPO,
        event_filter="all",
    )

    assert set(report.events.keys()) == {"pull_request", "merge_group", "push"}

    # Validate merge_group analysis: 5 total completed runs, 3 successful
    mg = report.events["merge_group"]
    assert mg.runs_count == 5
    assert mg.wall_clock_minutes["n"] == 3
    assert mg.wall_clock_minutes["avg"] == 15.4
    assert mg.wall_clock_minutes["median"] == 15.7
    assert mg.wall_clock_minutes["max"] == 18.9
    assert mg.wall_clock_all_minutes["n"] == 5
    assert mg.wall_clock_all_minutes["avg"] == 13.4
    assert mg.wall_clock_all_minutes["median"] == 11.7
    assert mg.wall_clock_all_minutes["max"] == 18.9

    job_names = {j.name for j in mg.jobs}
    assert "Contracts (schema, MDX, atlas, BIO)" in job_names
    assert "Python (pytest) [1/4]" in job_names
    assert "Python (pytest) [2/4]" in job_names
    assert "Python (pytest) [3/4]" in job_names
    assert "Python (pytest) [4/4]" in job_names
    assert "Frontend (build + vitest)" in job_names

    # Check queue timing details for merge_group
    assert mg.queue_timing is not None
    q = mg.queue_timing
    assert q["summary"]["prs_count"] == 4
    assert q["summary"]["kicks_total"] == 2

    pr_map = {p["pr_number"]: p for p in q["prs"]}
    assert set(pr_map.keys()) == {7165, 7167, 7169, 7170}

    # PR 7170: landed cleanly with 0 kicks
    assert pr_map[7170]["status"] == "landed"
    assert pr_map[7170]["kicks"] == 0
    assert pr_map[7170]["time_in_queue_minutes"] == 11.7

    # PR 7165: 1 kick and landed
    assert pr_map[7165]["status"] == "landed"
    assert pr_map[7165]["kicks"] == 1

    # PR 7169: failed / kicked
    assert pr_map[7169]["status"] == "failed"
    assert pr_map[7169]["kicks"] == 1


def test_render_json_stable_ordering() -> None:
    """Verify JSON output keys are deterministically sorted."""
    report = TimingReport(
        workflow=DEFAULT_WORKFLOW,
        repo=DEFAULT_REPO,
        since="2026-08-22",
        generated_at="2026-08-23T18:00:00Z",
        events={
            "merge_group": EventReport(
                event="merge_group",
                runs_count=1,
                wall_clock_minutes=compute_metric_stats([12.5]),
                wall_clock_all_minutes=compute_metric_stats([12.5]),
                jobs=[
                    JobStats(
                        name="Contracts",
                        n=1,
                        avg_minutes=5.2,
                        median_minutes=5.2,
                        p95_minutes=5.2,
                        max_minutes=5.2,
                    )
                ],
            )
        },
    )

    json_str_1 = render_json(report)
    json_str_2 = render_json(report)
    assert json_str_1 == json_str_2

    parsed = json.loads(json_str_1)
    assert list(parsed.keys()) == ["events", "generated_at", "repo", "since", "workflow"]
    assert list(parsed["events"]["merge_group"].keys()) == [
        "jobs",
        "runs_count",
        "wall_clock_all_minutes",
        "wall_clock_minutes",
    ]


def test_render_markdown_table_formatting() -> None:
    """Verify Markdown report renders table headers, jobs, population note, and queue stats."""
    runs, jobs_by_run = load_runs_and_jobs_from_fixture(_FIXTURE_PATH)
    report = analyze_timings(
        runs=runs,
        jobs_fetcher=jobs_by_run,
        workflow_name="CI",
        repo_name=DEFAULT_REPO,
        event_filter="merge_group",
    )
    md = render_markdown(report)
    assert "# CI Timing & Queue Report — CI" in md
    assert "- **Population:**" in md
    assert "## merge_group (5 completed runs)" in md
    assert "| job | n | avg | med | p95 | max |" in md
    assert "Python (pytest) [1/4]" in md
    assert "**Run Wall-clock (success)**" in md
    assert "**Run Wall-clock (all)**" in md
    assert "### merge_group Time-in-Queue & Kicks" in md
    assert "#7170" in md


def test_cli_main_with_fixture(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI main() execution in fixture mode."""
    exit_code = main(["--fixture", str(_FIXTURE_PATH), "--event", "merge_group"])
    assert exit_code == 0
    out, err = capsys.readouterr()
    assert "## merge_group" in out
    assert not err


def test_cli_main_with_fixture_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI main() execution with --json and --fixture."""
    exit_code = main(["--fixture", str(_FIXTURE_PATH), "--json"])
    assert exit_code == 0
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert "events" in data
    assert "merge_group" in data["events"]
    assert "pull_request" in data["events"]
    assert not err


def test_cli_main_invalid_since(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI main() returns exit code 2 on invalid --since."""
    exit_code = main(["--since", "not-a-valid-date"])
    assert exit_code == 2
    _out, err = capsys.readouterr()
    assert "Error: Invalid --since format" in err


def test_analyze_timings_limit_with_newer_non_matching_runs() -> None:
    """Verify --limit on fixture data selects the N most recent matching runs.

    In the fixture, there are 15 total runs (pull_request, merge_group, push).
    There are only 3 push runs, and several newer pull_request and merge_group
    runs occurred after them. Specifying event_filter='push' with limit=2 must
    return the 2 most recent push runs, ignoring newer non-matching runs.
    """
    runs, jobs_by_run = load_runs_and_jobs_from_fixture(_FIXTURE_PATH)
    report = analyze_timings(
        runs=runs,
        jobs_fetcher=jobs_by_run,
        event_filter="push",
        limit=2,
    )
    push = report.events["push"]
    assert push.runs_count == 2
    assert push.wall_clock_minutes["n"] == 2


def test_fetch_workflow_runs_passes_query_params(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify fetch_workflow_runs_from_api constructs correct API query parameters."""
    captured_paths: list[str] = []

    def fake_gh_api_get(path: str, **kwargs: Any) -> dict[str, Any]:
        captured_paths.append(path)
        return {"workflow_runs": []}

    monkeypatch.setattr("scripts.ci.ci_timings.gh_api_get", fake_gh_api_get)

    # 1. Event + branch + default status
    fetch_workflow_runs_from_api(
        repo="learn-ukrainian/learn-ukrainian.github.io",
        workflow_file="ci.yml",
        event="push",
        branch="main",
        limit=5,
    )
    assert len(captured_paths) == 1
    assert "event=push" in captured_paths[0]
    assert "branch=main" in captured_paths[0]
    assert "status=completed" in captured_paths[0]
    assert "per_page=100" in captured_paths[0]

    captured_paths.clear()

    # 2. Event == 'all' should NOT pass event=all
    fetch_workflow_runs_from_api(
        repo="learn-ukrainian/learn-ukrainian.github.io",
        workflow_file="ci.yml",
        event="all",
    )
    assert len(captured_paths) == 1
    assert "event=" not in captured_paths[0]


def test_fetch_workflow_runs_api_event_limit_with_newer_non_matching_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify limit operates on matching runs when API filters by event.

    Simulates the GitHub Actions API returning runs based on query params:
    - Without event= in query: returns all runs (where top runs are non-push).
    - With event=push in query: returns push runs only.
    Demonstrates that fetching with event='push' and limit=2 fetches the 2 push runs.
    """
    runs, _ = load_runs_and_jobs_from_fixture(_FIXTURE_PATH)

    def fake_gh_api_get(path: str, **kwargs: Any) -> dict[str, Any]:
        if "event=push" in path:
            matching = [r for r in runs if r.get("event") == "push" and r.get("status") == "completed"]
            return {"workflow_runs": matching}
        # If API was called without event filter, it returns unfiltered runs (starting with non-push)
        return {"workflow_runs": runs}

    monkeypatch.setattr("scripts.ci.ci_timings.gh_api_get", fake_gh_api_get)

    fetched = fetch_workflow_runs_from_api(
        repo="learn-ukrainian/learn-ukrainian.github.io",
        workflow_file="ci.yml",
        event="push",
        limit=2,
    )
    assert len(fetched) == 2
    assert all(r.get("event") == "push" for r in fetched)


def test_cli_main_api_event_limit_matching_runs(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """End-to-end test of main() with API fetch, verifying --limit N returns N matching runs.

    If the fix were missing (i.e. event filter omitted during fetch), fetch would return
    the newest runs which are non-push, resulting in 'push (0 completed runs)'.
    With the fix, main() produces 'push (2 completed runs)'.
    """
    runs, jobs_by_run = load_runs_and_jobs_from_fixture(_FIXTURE_PATH)

    def fake_gh_api_get(path: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        if "actions/runs/" in path and "/jobs" in path:
            run_id = path.split("actions/runs/")[1].split("/jobs")[0]
            return jobs_by_run.get(run_id, [])
        if "event=push" in path:
            matching = [r for r in runs if r.get("event") == "push" and r.get("status") == "completed"]
            return {"workflow_runs": matching}
        # Unfiltered returns all runs (the top ones are non-push)
        return {"workflow_runs": runs}

    monkeypatch.setattr("scripts.ci.ci_timings.gh_api_get", fake_gh_api_get)

    exit_code = main(["--event", "push", "--limit", "2"])
    assert exit_code == 0
    out, err = capsys.readouterr()
    assert not err
    assert "## push (2 completed runs)" in out
    assert "## push (0 completed runs)" not in out


def test_fetch_run_jobs_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify fetch_run_jobs_from_api paginates across multiple pages."""
    calls: list[str] = []

    def fake_gh_api_get(path: str, **kwargs: Any) -> dict[str, Any]:
        calls.append(path)
        m = re.search(r"[?&]page=(\d+)", path)
        page_num = int(m.group(1)) if m else 1
        if page_num == 1:
            return {
                "total_count": 125,
                "jobs": [{"id": i, "name": f"job-{i}", "status": "completed"} for i in range(100)],
            }
        if page_num == 2:
            return {
                "total_count": 125,
                "jobs": [{"id": 100 + i, "name": f"job-{100+i}", "status": "completed"} for i in range(25)],
            }
        return {"total_count": 125, "jobs": []}

    monkeypatch.setattr("scripts.ci.ci_timings.gh_api_get", fake_gh_api_get)

    jobs = fetch_run_jobs_from_api(
        repo="learn-ukrainian/learn-ukrainian.github.io",
        run_id=12345,
    )
    assert len(jobs) == 125
    assert len(calls) == 2
    assert "page=1" in calls[0]
    assert "page=2" in calls[1]


def test_fetch_run_jobs_pagination_max_pages_warning(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify fetch_run_jobs_from_api emits a warning when max_pages limit is reached."""

    def fake_gh_api_get(path: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "total_count": 500,
            "jobs": [{"id": i, "name": f"job-{i}", "status": "completed"} for i in range(100)],
        }

    monkeypatch.setattr("scripts.ci.ci_timings.gh_api_get", fake_gh_api_get)

    jobs = fetch_run_jobs_from_api(
        repo="learn-ukrainian/learn-ukrainian.github.io",
        run_id=99999,
        max_pages=2,
    )
    assert len(jobs) == 200
    _, err = capsys.readouterr()
    assert "Warning: Reached maximum pagination limit (2 pages) for run 99999 jobs; retrieved 200 jobs." in err


def test_load_runs_and_jobs_from_fixture_non_list_non_dict(tmp_path: Path) -> None:
    """Verify load_runs_and_jobs_from_fixture raises ValueError on non-list/non-dict JSON payloads."""
    str_file = tmp_path / "string_fixture.json"
    str_file.write_text(json.dumps("plain string value"), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid fixture format: expected JSON object or array"):
        load_runs_and_jobs_from_fixture(str_file)

    int_file = tmp_path / "int_fixture.json"
    int_file.write_text(json.dumps(12345), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid fixture format: expected JSON object or array"):
        load_runs_and_jobs_from_fixture(int_file)


def test_load_runs_and_jobs_from_fixture_json_decode_error(tmp_path: Path) -> None:
    """Verify load_runs_and_jobs_from_fixture propagates json.JSONDecodeError on malformed JSON."""
    bad_file = tmp_path / "malformed.json"
    bad_file.write_text("{not valid json: 123", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_runs_and_jobs_from_fixture(bad_file)


def test_load_runs_and_jobs_from_fixture_file_not_found() -> None:
    """Verify load_runs_and_jobs_from_fixture raises FileNotFoundError for non-existent path."""
    with pytest.raises(FileNotFoundError, match="Fixture file not found"):
        load_runs_and_jobs_from_fixture("does_not_exist_fixture.json")


def test_gh_api_get_json_decode_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify gh_api_get raises RuntimeError with documented message on malformed JSON from API."""

    def fake_subprocess_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["gh", "api", "repos/owner/repo/test"],
            returncode=0,
            stdout="<html>502 Bad Gateway</html>",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    with pytest.raises(
        RuntimeError, match="Failed to parse JSON response from gh api repos/owner/repo/test"
    ):
        gh_api_get("repos/owner/repo/test")
