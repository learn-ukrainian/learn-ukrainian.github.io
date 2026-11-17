"""Stale-while-revalidate snapshots behind the slow product routes (API-UI-SLOW-1117).

Each case drives ``/api/state/failing`` (a snapshot route) with a scan that the
test gates by events, and sets the snapshot and TTL clocks explicitly, so no
case depends on wall-clock timing. Waiting for a background refresh joins the
refresh thread with a bound instead of sleeping.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from lu_machinery.api import state_helpers
from lu_machinery.api.monitor_context import fixture_context

from scripts.project_api import snapshots
from scripts.project_api import state_router as product_state_router

_JOIN_S = 30.0
_FAILING = "/api/state/failing"


@pytest.fixture(autouse=True)
def _clean_cache():
    state_helpers.cache_invalidate()
    snapshots._failed_keys.clear()
    yield
    state_helpers.cache_invalidate()
    snapshots._failed_keys.clear()


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    now = [1000.0]
    monkeypatch.setattr(snapshots, "_clock", lambda: now[0])
    monkeypatch.setattr(state_helpers, "_ttl_clock", lambda: now[0])
    return now


class _Scan:
    """A stand-in for the failing-modules scan whose later runs wait for the test."""

    def __init__(self) -> None:
        self.calls = 0
        self.gate = threading.Event()
        self.gate.set()
        self.entered = threading.Event()
        self.error: Exception | None = None

    def __call__(self, _ctx: Any, _track: str | None) -> dict[str, Any]:
        self.calls += 1
        generation = self.calls
        self.entered.set()
        if not self.gate.wait(_JOIN_S):
            raise AssertionError("scan gate was never released")
        if self.error is not None:
            raise self.error
        return {"count": 0, "modules": [], "generation": generation}


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scan: _Scan) -> TestClient:
    """A client used as a context manager, so every request shares one event loop
    (an in-flight scan belongs to the loop that started it, as in the server)."""
    monkeypatch.setattr(product_state_router, "_compute_failing_payload", scan)
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(product_state_router.router, prefix="/api/state")
    return TestClient(app, raise_server_exceptions=False)


def _join_refreshes() -> None:
    for thread in threading.enumerate():
        if thread.name == "status-cache-refresh":
            thread.join(_JOIN_S)
            assert not thread.is_alive(), "background refresh did not finish"


def test_stale_snapshot_is_served_at_once_with_true_age_and_one_refresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clock: list[float]
) -> None:
    """Defect class: a stale read waits for the rescan, reports the store time
    instead of the scan start as its age, or starts one rescan per reader."""
    scan = _Scan()
    with _client(tmp_path, monkeypatch, scan) as client:
        first = client.get(_FAILING)
        assert first.status_code == 200
        assert first.json()["generation"] == 1

        clock[0] += product_state_router.STATE_FAILING_TTL_S + 5
        scan.gate.clear()
        scan.entered.clear()
        stale = [client.get(_FAILING) for _ in range(5)]
        assert [response.status_code for response in stale] == [200] * 5
        assert [response.json()["generation"] for response in stale] == [1] * 5
        assert {response.headers[snapshots.AGE_HEADER] for response in stale} == {"65.000"}
        assert scan.entered.wait(_JOIN_S), "no background refresh started"
        assert scan.calls == 2

        # The refresh started reading at 1065 and is stored at 1070: its age counts from 1065.
        clock[0] += 5
        scan.gate.set()
        _join_refreshes()
        fresh = client.get(_FAILING)
        assert fresh.json()["generation"] == 2
        assert fresh.headers[snapshots.AGE_HEADER] == "5.000"
        assert scan.calls == 2


def test_cold_snapshot_past_wait_answers_typed_503_and_keeps_scanning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clock: list[float]
) -> None:
    """Defect class: a cold scan holds the request past the Monitor timeout (a
    504 with no reason), or the abandoned scan is cancelled or restarted."""
    scan = _Scan()
    scan.gate.clear()
    with _client(tmp_path, monkeypatch, scan) as client:
        # The scan cannot finish before the gate opens, so any wait bound gives the 503.
        monkeypatch.setattr(snapshots, "cold_wait_s", lambda: 0.05)

        for _ in range(2):
            warming = client.get(_FAILING)
            assert warming.status_code == 503
            assert warming.json()["detail"]["code"] == "SNAPSHOT_WARMING"
            assert warming.headers["Retry-After"] == str(snapshots.RETRY_AFTER_S)
            assert warming.headers["Cache-Control"] == "no-store"
        assert scan.entered.is_set()
        assert scan.calls == 1

        monkeypatch.setattr(snapshots, "cold_wait_s", lambda: _JOIN_S)
        scan.gate.set()
        ready = client.get(_FAILING)
        assert ready.status_code == 200
        assert ready.json()["generation"] == 1
        assert scan.calls == 1


def test_snapshot_older_than_stale_limit_is_not_served(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clock: list[float]
) -> None:
    """Defect class: old data hides a refresh that keeps failing: once a scan has
    failed, its stale value is not served again and the next reader gets the error."""
    scan = _Scan()
    with _client(tmp_path, monkeypatch, scan) as client:
        assert client.get(_FAILING).json()["generation"] == 1

        # The refresh fails: that stale read is served, the next one gets the error.
        clock[0] += product_state_router.STATE_FAILING_TTL_S + 1
        scan.error = RuntimeError("scan failed")
        assert client.get(_FAILING).json()["generation"] == 1
        _join_refreshes()
        assert scan.calls == 2
        assert client.get(_FAILING).status_code == 500
        assert scan.calls == 3
        scan.error = None
        recovered = client.get(_FAILING)
        assert recovered.status_code == 200
        assert recovered.json()["generation"] == 4
