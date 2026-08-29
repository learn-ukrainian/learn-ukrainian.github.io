"""Fleet header jobs chip must name its ledger and see runtime/delegate work (#7079).

The fleet.html header chip derives its "jobs in the last 24h" count from the
fleet-comms ``authority_jobs`` table only. Runtime and delegate work is
recorded in a separate usage ledger, so a zero authority window is idle-now,
not zero-today. The health payload exposes both ledgers and the chip names
them.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import scripts.api.fleet_router as fleet_router
from scripts.api.monitor_context import production_context
from scripts.fleet_comms.migrations import apply_migrations

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.state.ctx = production_context()
    app.include_router(fleet_router.router, prefix="/api/fleet")
    return TestClient(app)


@pytest.fixture()
def fleet_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "fleet-comms" / "v1"
    root.mkdir(parents=True)
    connection = sqlite3.connect(root / "comms.sqlite3")
    try:
        apply_migrations(connection)
    finally:
        connection.close()
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")
    return root


def _runtime_records(*timestamps: str) -> dict[str, list[dict[str, str]]]:
    return {
        "records": [
            {
                "ts": ts,
                "source": "operator",
                "agent": "kimi",
                "via": "dispatch",
                "entrypoint": "dispatch",
                "model": "kimi",
                "outcome": "ok",
                "source_provenance": "explicit",
                "source_task_id": "task-7079",
            }
            for ts in timestamps
        ]
    }


def test_health_names_both_ledgers_when_authority_window_is_empty(
    client: TestClient, fleet_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Idle authority window + runtime/delegate work must not read as zero-today."""
    now = fleet_router.datetime.now(fleet_router.UTC)
    inside = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    outside = (now - fleet_router.timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
    monkeypatch.setattr(
        fleet_router,
        "recent_runtime_records",
        lambda *, limit, ctx=None: _runtime_records(inside, inside, outside),
    )

    health = client.get("/api/fleet/health").json()

    authority = health["authority_health"]
    assert authority["state"] == "idle"
    assert authority["jobs"] == {"total": 0, "by_state": {}}
    runtime = health["runtime_activity"]
    assert runtime["ledger"] == "runtime_delegate_usage"
    assert runtime["availability"] == "available"
    assert runtime["records_in_window"] == 2


def test_health_runtime_activity_survives_ledger_read_failure(
    client: TestClient, fleet_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A broken runtime ledger degrades the chip hint, never the health verdict."""

    def _boom(*, limit: int, ctx=None) -> dict[str, list[dict[str, str]]]:
        raise OSError("usage files unreadable")

    monkeypatch.setattr(fleet_router, "recent_runtime_records", _boom)

    response = client.get("/api/fleet/health")

    assert response.status_code == 200
    runtime = response.json()["runtime_activity"]
    assert runtime["records_in_window"] is None
    assert runtime["availability"] == "unavailable"
    assert response.json()["authority_health"]["state"] == "idle"


def test_fleet_page_chip_names_fleet_comms_ledger_and_runtime_delegate() -> None:
    html = (ROOT / "dashboards" / "fleet.html").read_text(encoding="utf-8")

    assert "fleet-comms authority jobs in the last" in html
    assert "runtime/delegate records in window" in html
    assert "health.runtime_activity?.records_in_window" in html
