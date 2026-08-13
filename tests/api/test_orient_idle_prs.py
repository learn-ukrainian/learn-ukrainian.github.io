"""Tests for the cache-first idle pull-request orient section (#4728)."""

from __future__ import annotations

import json
import subprocess
import threading
import time
from datetime import UTC, datetime, timedelta

import pytest

import scripts.api.main as api_main
import scripts.api.state_helpers as state_helpers

NOW = datetime(2026, 8, 13, 12, tzinfo=UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _pr(number: int, *, updated_at: datetime, **changes: object) -> dict:
    result: dict[str, object] = {
        "number": number,
        "state": "OPEN",
        "isDraft": False,
        "headRefName": f"codex/pr-{number}",
        "headRefOid": f"{number:040x}",
        "updatedAt": _iso(updated_at),
        "reviewDecision": "APPROVED",
        "reviews": [],
        "comments": [],
        "mergeStateStatus": "CLEAN",
        "statusCheckRollup": [
            {
                "name": "CI Gate",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "startedAt": _iso(updated_at),
                "completedAt": _iso(updated_at + timedelta(minutes=10)),
            }
        ],
    }
    result.update(changes)
    return result


@pytest.fixture(autouse=True)
def _reset_idle_pr_state():
    state_helpers.cache_invalidate(api_main.IDLE_PR_CACHE_KEY)
    api_main._idle_pr_last_good = None
    api_main._idle_pr_last_error = None
    api_main._idle_pr_next_retry_at = 0.0
    thread = api_main._idle_pr_refresh_thread
    if thread is not None and thread.is_alive():
        thread.join(timeout=2.0)
    api_main._idle_pr_refresh_thread = None
    yield
    thread = api_main._idle_pr_refresh_thread
    if thread is not None and thread.is_alive():
        thread.join(timeout=2.0)
    state_helpers.cache_invalidate(api_main.IDLE_PR_CACHE_KEY)
    api_main._idle_pr_last_good = None
    api_main._idle_pr_last_error = None
    api_main._idle_pr_next_retry_at = 0.0
    api_main._idle_pr_refresh_thread = None


def test_idle_pr_collector_excludes_fresh_red_and_unreviewed_prs(monkeypatch):
    now = datetime.now(UTC)
    approved_by_comment = _pr(
        102,
        updated_at=now - timedelta(hours=2),
        reviewDecision="",
        comments=[
            {
                "body": (
                    "## Cross-family CF (Grok / xAI)\n"
                    f"**VERDICT: APPROVE** at head `{102:040x}`."
                )
            }
        ],
    )
    payload = [
        _pr(101, updated_at=now - timedelta(hours=2)),
        approved_by_comment,
        _pr(103, updated_at=now - timedelta(minutes=45)),
        _pr(
            104,
            updated_at=now - timedelta(hours=2),
            statusCheckRollup=[
                {
                    "name": "CI Gate",
                    "status": "COMPLETED",
                    "conclusion": "FAILURE",
                    "startedAt": _iso(now - timedelta(hours=2)),
                    "completedAt": _iso(now - timedelta(hours=1, minutes=50)),
                }
            ],
        ),
        _pr(105, updated_at=now - timedelta(hours=2), reviewDecision="", comments=[]),
    ]

    monkeypatch.setattr(
        api_main,
        "_run_command",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=json.dumps(payload), stderr=""
        ),
    )
    result = api_main._collect_idle_prs_orient_data()

    assert [row["number"] for row in result["idle_prs"]] == [101, 102]
    assert all(set(row) == {"number", "branch", "minutes_idle"} for row in result["idle_prs"])
    assert all(row["minutes_idle"] > 60 for row in result["idle_prs"])


def test_latest_red_check_blocks_an_old_green_run():
    pr = _pr(
        106,
        updated_at=NOW - timedelta(hours=2),
        statusCheckRollup=[
            {
                "name": "CI Gate",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "startedAt": _iso(NOW - timedelta(hours=2)),
                "completedAt": _iso(NOW - timedelta(hours=1, minutes=50)),
            },
            {
                "name": "CI Gate",
                "status": "COMPLETED",
                "conclusion": "FAILURE",
                "startedAt": _iso(NOW - timedelta(hours=1)),
                "completedAt": _iso(NOW - timedelta(minutes=50)),
            },
        ],
    )

    assert api_main._eligible_idle_pr(pr, now=NOW) is None


def test_timeout_refresh_degrades_to_absent_cache():
    def timed_out():
        raise subprocess.TimeoutExpired(cmd=["gh", "pr", "list"], timeout=api_main.IDLE_PR_FETCH_TIMEOUT_S)

    api_main._run_idle_pr_refresh(timed_out)

    assert state_helpers.cache_get(api_main.IDLE_PR_CACHE_KEY, ttl=api_main.ORIENT_SECTION_TTLS["idle_prs"]) is None
    assert api_main._idle_pr_last_error == "gh_timeout"

    result, meta = api_main._cached_idle_pr_section(timed_out, {"idle_prs": []})

    assert result == {"idle_prs": []}
    assert meta["error"] == "gh_timeout"


def test_idle_pr_request_path_only_schedules_slow_gh_refresh(monkeypatch):
    started = threading.Event()
    release = threading.Event()

    def slow_collector():
        started.set()
        release.wait(timeout=2.0)
        return {"idle_prs": []}

    start = time.perf_counter()
    result, meta = api_main._cached_idle_pr_section(slow_collector, {"idle_prs": []})
    elapsed = time.perf_counter() - start

    assert elapsed < 0.2
    assert result == {"idle_prs": []}
    assert meta["refreshing"] is True
    assert started.wait(timeout=1.0)

    release.set()
    assert api_main._idle_pr_refresh_thread is not None
    api_main._idle_pr_refresh_thread.join(timeout=2.0)
