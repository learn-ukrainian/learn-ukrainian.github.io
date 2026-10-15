"""Ops API: per-caller GitHub request counts for the current and previous hour (#10730). Counts only."""

from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient

from scripts.api import main as api_main
from scripts.api.monitor_context import fixture_context
from scripts.common import github_budget_counters as counters
from scripts.common import github_client as gh


@pytest.fixture
def cache_dir(tmp_path, monkeypatch):
    path = tmp_path / "github-cache"
    monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(path))
    return path


@pytest.fixture
def api(tmp_path, cache_dir):
    # No lifespan: startup warmups issue their own GitHub reads, which would be counted too.
    return TestClient(api_main.create_app(fixture_context(tmp_path)))


def record(cache_dir, caller, endpoint, times, *, now, method="GET", payload=None, token="fixture-token"):
    client = gh.GitHubClient(
        cache_dir=cache_dir,
        transport=lambda *a: gh.Response(200, {"X-RateLimit-Remaining": "4321", "X-RateLimit-Reset": str(int(now) + 900)}, b"{}"),
        clock=lambda: now,
        env={"GH_TOKEN": token},
        caller=caller,
    )
    for _ in range(times):
        client.request(method, endpoint, payload=payload, fresh=True)


def test_top_callers_for_current_and_previous_hour_per_resource(api, cache_dir):
    now = time.time()
    this_hour, last_hour = counters.hour_start(now), counters.hour_start(now) - 3600
    record(cache_dir, "orphan-triage", "repos/o/r/issues/1", 4, now=now)
    record(cache_dir, "keeper", "repos/o/r/issues/1", 2, now=now)
    record(cache_dir, "keeper", "graphql", 3, now=now, method="POST", payload={"query": "query { viewer { login } }"})
    record(cache_dir, "issue-audit", "repos/o/r/issues/1", 5, now=last_hour + 10)
    body = api.get("/api/github-budget/callers").json()
    assert body["schema"] == "github-budget-callers.v1"
    assert body["windows"]["current"]["hour_start"] == this_hour
    assert body["windows"]["previous"]["hour_start"] == last_hour
    current = body["windows"]["current"]["resources"]
    assert current["core"] == [{"caller": "orphan-triage", "count": 4}, {"caller": "keeper", "count": 2}]
    assert current["graphql"] == [{"caller": "keeper", "count": 3}]
    assert current["search"] == []
    assert body["windows"]["previous"]["resources"]["core"] == [{"caller": "issue-audit", "count": 5}]
    assert body["budget"]["core"]["remaining"] == 4321


def test_limit_bounds_the_callers_per_pool(api, cache_dir):
    now = time.time()
    for index in range(4):
        record(cache_dir, f"caller-{index}", "repos/o/r/issues/1", index + 1, now=now)
    rows = api.get("/api/github-budget/callers", params={"limit": 2}).json()["windows"]["current"]["resources"]["core"]
    assert rows == [{"caller": "caller-3", "count": 4}, {"caller": "caller-2", "count": 3}]
    assert api.get("/api/github-budget/callers", params={"limit": 0}).status_code == 422
    assert api.get("/api/github-budget/callers", params={"limit": 51}).status_code == 422


def test_response_holds_counts_only(api, cache_dir):
    now = time.time()
    secret = "ghp_SECRETTOKENVALUE1234567890"
    record(
        cache_dir,
        "drv",
        "repos/secret-owner/secret-repo/issues/77/comments",
        1,
        now=now,
        method="POST",
        payload={"body": "private-body-text"},
        token=secret,
    )
    response = api.get("/api/github-budget/callers")
    text = response.text
    for marker in (secret, "secret-owner", "secret-repo", "private-body-text", "comments", "http", "/"):
        assert marker not in text
    allowed = {"caller", "count"}
    for window in response.json()["windows"].values():
        assert set(window) == {"hour_start", "resources"}
        for rows in window["resources"].values():
            assert all(set(row) == allowed and isinstance(row["count"], int) for row in rows)
    assert set(json.loads(text)) == {"schema", "generated_at", "windows", "budget"}


def test_no_database_yet_is_an_empty_report(api):
    body = api.get("/api/github-budget/callers").json()
    assert body["windows"]["current"]["resources"] == {"core": [], "graphql": [], "search": []}
    assert body["budget"] == {}


def test_router_is_registered_once_and_read_only(api):
    assert set(api.app.openapi()["paths"]["/api/github-budget/callers"]) == {"get"}
    assert api.post("/api/github-budget/callers").status_code in {404, 405}
