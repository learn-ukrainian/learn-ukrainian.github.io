"""API tests for occupancy seats beyond the atlas-job registry (#7139)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import LeaseHolder
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api import atlas_jobs_router as load_mod
from scripts.api.monitor_context import fixture_context
from scripts.api.occupancy import router as occupancy_router
from scripts.lexicon.runner import atlas_job

_PLACEHOLDER_MAP = "worker-box=host-worker,teach-box=host-teacher"


def _client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path / "occupancy-ctx")
    app.include_router(occupancy_router, prefix="/api/occupancy")
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _isolate_local_occupants(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_RUN_ROOT", "/nonexistent/atlas-run-root")
    marker_root = tmp_path / "no-markers"
    marker_root.mkdir()
    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(marker_root))
    monkeypatch.delenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", raising=False)
    monkeypatch.delenv("MONITOR_OCCUPANCY_FOUNDRY_HOST_ID", raising=False)
    monkeypatch.delenv("ATLAS_JOB_SELF_HOST", raising=False)
    monkeypatch.setattr(
        "scripts.api.occupancy_local.session_streams_db_path",
        lambda: tmp_path / "missing-session-streams.sqlite3",
    )


def _open_driver_lease(db_path: Path, *, agent: str = "claude", task_id: str = "infra-drive") -> None:
    store = SessionStreamStore(SessionStreamDatabase(db_path))
    store.open_session(
        stream_id="epic:7139",
        holder=LeaseHolder(
            agent=agent,
            harness="claude-code",
            instance_id="runtime-1",
            process_id=41001,
            task_id=task_id,
        ),
        lineage_id="lineage-occupancy",
        ttl_seconds=600,
        session_id="session-occupancy",
        lease_id="lease-occupancy",
    )


def test_occupancy_driver_lease_without_host_claim_stays_idle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    db_path = tmp_path / "session-streams.sqlite3"
    monkeypatch.setattr("scripts.api.occupancy_local.session_streams_db_path", lambda: db_path)
    _open_driver_lease(db_path)
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        idle_load = fake.host_load("teach-box")
        idle_load["loadavg"] = [0.10, 0.10, 0.10]
        idle_load["job_unit"] = {"active_count": 0, "job_id": None, "state": None}
        load_mod.set_host_load_cache("teach-box", idle_load)
        load_mod.set_host_load_cache("worker-box", fake.host_load("worker-box"))
        resp = _client(tmp_path).get("/api/occupancy?host_id=host-teacher")
        assert resp.status_code == 200
        host = resp.json()["hosts"]["host-teacher"]
        assert host["occupants"] == []
        assert host["idle_or_empty"] is True
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()
