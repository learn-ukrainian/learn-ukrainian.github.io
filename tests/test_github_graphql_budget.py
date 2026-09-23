"""Tests for the authoritative GitHub GraphQL budget probe."""

from __future__ import annotations

import json
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from scripts import github_graphql_budget as probe


def _runner(stdout: str, *, stderr: str = "", returncode: int = 0, record: list | None = None):
    def run(args, **kwargs):
        if record is not None:
            record.append((args, kwargs))
        return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)

    return run


def test_healthy_probe_uses_one_graphql_rate_limit_query() -> None:
    calls = []
    result = probe.probe_graphql_budget(
        _runner(json.dumps({"data": {"rateLimit": {
            "limit": 5000, "remaining": 321, "used": 4679, "resetAt": "2026-09-24T00:00:00Z"
        }}}), record=calls)
    )

    assert result == {
        "source": "graphql.rateLimit",
        "limit": 5000,
        "remaining": 321,
        "used": 4679,
        "reset_at": "2026-09-24T00:00:00Z",
        "exhausted": False,
        "error": None,
        "checked_at": result["checked_at"],
    }
    assert len(calls) == 1
    assert calls[0][0][:3] == ["gh", "api", "graphql"]
    assert "rateLimit { limit remaining used resetAt }" in calls[0][0][4]
    assert calls[0][1]["timeout"] == probe.TIMEOUT_SECONDS


@pytest.mark.parametrize(
    "detail",
    [
        {"type": "RATE_LIMIT", "message": "exhausted"},
        {"code": "graphql_rate_limit", "message": "exhausted"},
    ],
)
def test_exhausted_graphql_error_is_signal(detail: dict) -> None:
    result = probe.probe_graphql_budget(
        _runner(json.dumps(detail), returncode=1)
    )

    assert result["exhausted"] is True
    assert result["remaining"] == 0
    assert result["error"]


@pytest.mark.parametrize(
    "stdout",
    [
        "not json",
        json.dumps({"data": {"rateLimit": {"limit": 5, "remaining": 3}}}),
        json.dumps({"data": {"rateLimit": {"limit": 5, "remaining": "3", "used": 2, "resetAt": "soon"}}}),
        json.dumps({"data": {"rateLimit": None}}),
    ],
)
def test_malformed_or_partial_response_is_unknown(stdout: str) -> None:
    result = probe.probe_graphql_budget(_runner(stdout))
    assert result["exhausted"] is None
    assert result["remaining"] is None
    assert result["error"]


def test_missing_gh_is_unknown() -> None:
    def missing(*_args, **_kwargs):
        raise FileNotFoundError

    result = probe.probe_graphql_budget(missing)
    assert result["exhausted"] is None
    assert result["error"] == "gh CLI not found"


def test_timeout_is_unknown_and_bounded() -> None:
    def timeout(args, **kwargs):
        assert kwargs["timeout"] == probe.TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(args, kwargs["timeout"])

    result = probe.probe_graphql_budget(timeout)
    assert result["exhausted"] is None
    assert "timed out" in result["error"]


def test_ttl_cache_and_single_flight(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.api import state_helpers

    now = [100.0]
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: now[0])
    state_helpers.cache_invalidate("github-budget-test")
    calls = []
    started = threading.Event()
    release = threading.Event()

    def compute():
        calls.append(1)
        started.set()
        assert release.wait(timeout=2)
        return {"remaining": 10}

    key = "github-budget-test"
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(state_helpers.cache_get_or_compute, key, 60.0, compute) for _ in range(4)]
        assert started.wait(timeout=2)
        time.sleep(0.02)
        release.set()
        assert [future.result(timeout=2) for future in futures] == [{"remaining": 10}] * 4

    assert len(calls) == 1
    assert state_helpers.cache_get_or_compute(key, 60.0, lambda: pytest.fail("warm cache missed")) == {"remaining": 10}
    now[0] += 60.0
    assert state_helpers.cache_get_or_compute(key, 60.0, lambda: {"remaining": 9}) == {"remaining": 9}
    state_helpers.cache_invalidate(key)
