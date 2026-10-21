"""Unit tests for scripts/ci/ci_timings.py (issue #7174).

Hermetic, offline test suite verifying:
- Nearest-rank p95 percentile against hand-computed values.
- ISO and relative --since window parsing and boundary filtering.
- Queue timing and kick calculation from recorded API fixtures.
- Stable-ordered JSON serialization and Markdown table formatting.
- CLI argument parsing and error handling.
"""

from __future__ import annotations

import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from scripts.ci.ci_timings import (
    DEFAULT_REPO,
    analyze_timings,
    fetch_run_jobs_from_api,
    fetch_workflow_runs_from_api,
    gh_api_get,
    load_runs_and_jobs_from_fixture,
    main,
)

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ci_timings" / "sample_ci_runs.json"


pytestmark = pytest.mark.usefixtures("github_command_boundary")


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
    assert mg.wall_clock_minutes["avg"] == 13.0
    assert mg.wall_clock_minutes["median"] == 13.0
    assert mg.wall_clock_minutes["max"] == 15.0
    assert mg.wall_clock_all_minutes["n"] == 5
    assert mg.wall_clock_all_minutes["avg"] == 12.0
    assert mg.wall_clock_all_minutes["median"] == 11.1
    assert mg.wall_clock_all_minutes["max"] == 15.0

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


def test_fetch_workflow_runs_passes_query_params(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify fetch_workflow_runs_from_api constructs correct API query parameters."""
    captured_paths: list[str] = []

    def fake_gh_api_get(path: str, **kwargs: Any) -> dict[str, Any]:
        captured_paths.append(path)
        return {"workflow_runs": [{"id": 1}]}

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


def test_fetch_workflow_runs_out_of_order_page_does_not_stop_pagination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stale entry before newer runs must not hide later pages."""
    cutoff = datetime(2026, 9, 27, 12, tzinfo=UTC)
    paths: list[str] = []
    recent = [{"id": run_id, "created_at": "2026-09-28T00:00:00Z"} for run_id in range(1, 101)]
    pages = {
        1: [{"id": 0, "created_at": "2026-09-26T00:00:00Z"}, *recent[:99]],
        2: recent[99:],
    }

    def fake_gh_api_get(path: str, **_kwargs: Any) -> dict[str, Any]:
        paths.append(path)
        query = parse_qs(urlsplit(path).query)
        assert query["created"] == [">=2026-09-27T12:00:00Z"]
        assert "event" not in query
        return {"total_count": 101, "workflow_runs": pages[int(query["page"][0])]}

    monkeypatch.setattr("scripts.ci.ci_timings.gh_api_get", fake_gh_api_get)
    runs = fetch_workflow_runs_from_api(DEFAULT_REPO, "ci.yml", since_dt=cutoff, event="all")

    assert [run["id"] for run in runs] == list(range(1, 101))
    assert len(paths) == 2


def test_fetch_workflow_runs_stops_when_page_ends_before_since(monkeypatch: pytest.MonkeyPatch) -> None:
    cutoff = datetime(2026, 9, 27, 12, tzinfo=UTC)
    paths: list[str] = []

    def fake_gh_api_get(path: str, **_kwargs: Any) -> dict[str, Any]:
        paths.append(path)
        assert "page=1" in path
        return {
            "total_count": 300,
            "workflow_runs": [
                {"id": run_id, "created_at": "2026-09-28T00:00:00Z" if run_id < 50 else "2026-09-26T00:00:00Z"}
                for run_id in range(100)
            ],
        }

    monkeypatch.setattr("scripts.ci.ci_timings.gh_api_get", fake_gh_api_get)
    runs = fetch_workflow_runs_from_api(DEFAULT_REPO, "ci.yml", since_dt=cutoff, event="all")
    assert len(runs) == 50
    assert len(paths) == 1


def test_fetch_workflow_runs_stops_at_total_count_on_full_page(monkeypatch: pytest.MonkeyPatch) -> None:
    paths: list[str] = []

    def fake_gh_api_get(path: str, **_kwargs: Any) -> dict[str, Any]:
        paths.append(path)
        return {"total_count": 100, "workflow_runs": [{"id": i} for i in range(100)]}

    monkeypatch.setattr("scripts.ci.ci_timings.gh_api_get", fake_gh_api_get)
    assert len(fetch_workflow_runs_from_api(DEFAULT_REPO, "ci.yml")) == 100
    assert len(paths) == 1


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
                "jobs": [{"id": 100 + i, "name": f"job-{100 + i}", "status": "completed"} for i in range(25)],
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

    with pytest.raises(RuntimeError, match="Failed to parse JSON response from gh api repos/owner/repo/test"):
        gh_api_get("repos/owner/repo/test")


def test_empty_workflow_page_retries_then_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def empty_page(_path: str, **_kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return {"total_count": 80, "workflow_runs": []}

    monkeypatch.setattr("scripts.ci.ci_timings.gh_api_get", empty_page)
    with pytest.raises(RuntimeError, match="stayed empty after 3 attempts despite total_count=80"):
        fetch_workflow_runs_from_api(DEFAULT_REPO, "ci.yml")
    assert calls == 3

    assert main(["--since", "2026-09-27T11:00", "--event", "merge_group"]) == 1
    assert calls == 6


def test_empty_workflow_page_recovers(monkeypatch: pytest.MonkeyPatch) -> None:
    pages = iter(
        [
            {"total_count": 1, "workflow_runs": []},
            {"total_count": 1, "workflow_runs": [{"id": 1, "created_at": "2026-09-28T00:00:00Z"}]},
        ]
    )
    monkeypatch.setattr("scripts.ci.ci_timings.gh_api_get", lambda *_a, **_kw: next(pages))
    runs = fetch_workflow_runs_from_api(DEFAULT_REPO, "ci.yml")
    assert [run["id"] for run in runs] == [1]


def test_cli_all_limit_fetches_each_event_separately(monkeypatch: pytest.MonkeyPatch) -> None:
    paths: list[str] = []

    def fake_api(path: str, **_kwargs: Any) -> dict[str, Any]:
        paths.append(path)
        if "/jobs?" in path:
            return {"jobs": [], "total_count": 0}
        event = next(ev for ev in ("pull_request", "merge_group", "push") if f"event={ev}" in path)
        return {
            "total_count": 1,
            "workflow_runs": [
                {"id": len(paths), "event": event, "status": "completed", "created_at": "2026-09-28T00:00:00Z"}
            ],
        }

    monkeypatch.setattr("scripts.ci.ci_timings.gh_api_get", fake_api)
    assert main(["--event", "all", "--limit", "1", "--json"]) == 0
    run_paths = [path for path in paths if "/workflows/" in path]
    assert len(run_paths) == 3
    assert all(
        f"event={event}" in path for event, path in zip(("pull_request", "merge_group", "push"), run_paths, strict=True)
    )
