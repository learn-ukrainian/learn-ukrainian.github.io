"""#7486: /api/comms/v1 metric-family routes follow the plane/storage switch."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.api import main as api_main
from scripts.api.monitor_context import fixture_context

pytestmark = pytest.mark.repo_invariant

_ROUTES = ("/api/comms/v1/metrics", "/api/comms/v1/backlog", "/api/comms/v1/dead-letters")


def _client(tmp_path: Path) -> TestClient:
    return TestClient(api_main.create_app(fixture_context(tmp_path)))


def test_authority_mode_reads_plane_not_legacy_broker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")
    client = _client(tmp_path)
    for route in _ROUTES:
        payload = client.get(route).json()
        assert payload["source"] == "authority", route
        # Fixture has no plane db — fail-open db_missing, never legacy data.
        assert payload.get("db_missing") is True, route
        assert payload["store"]["kind"] == "comms-plane", route
    # #7505 CF r1: legacy zero-value shape fields survive in authority mode.
    backlog = client.get("/api/comms/v1/backlog").json()
    assert backlog["total"] == 0 and backlog["rows"] == []
    assert backlog["by_agent"] == {} and backlog["by_status"] == {}
    dead = client.get("/api/comms/v1/dead-letters").json()
    assert dead["total"] == 0 and dead["by_reason"] == {} and dead["rows"] == []


def test_authority_mode_with_plane_db_runs_authority_collectors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")
    plane = tmp_path / "batch_state" / "fleet-comms" / "v1"
    plane.mkdir(parents=True)
    sqlite3.connect(plane / "comms.sqlite3").close()  # empty schema
    client = _client(tmp_path)
    for route in _ROUTES:
        payload = client.get(route).json()
        assert payload["source"] == "authority", route
        # Empty schema → collectors answer (empty projections) or a typed
        # db_error code; never a 500 and never exception text.
        assert "db_error" not in payload or payload["db_error"].isidentifier()


def test_forced_off_mode_stays_on_legacy_broker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Explicit off mode pins the legacy broker path (the repo's CONFIGURED
    default is authority, so the off/legacy path needs an explicit pin)."""
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "off")
    client = _client(tmp_path)
    for route in _ROUTES:
        payload = client.get(route).json()
        assert payload.get("source") != "authority", route
        assert payload.get("db_missing") is True, route  # fixture: no broker db
