"""API tests for occupancy seats beyond the atlas-job registry (#7139)."""

from __future__ import annotations

import json
import re
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
from scripts.api.occupancy_local import write_marker
from scripts.lexicon.runner import atlas_job

_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_ALIAS_LEAKS = ("atlas-runner", "hramatka", "vps")
_PLACEHOLDER_MAP = "job-box=host-job,teach-box=host-teacher"


def _client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path / "occupancy-ctx")
    app.include_router(occupancy_router, prefix="/api/occupancy")
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _isolate_local_occupants(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_RUN_ROOT", "/tmp/atlas-run-root")
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


def test_occupancy_session_stream_driver_keeps_low_load_host_busy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    monkeypatch.setenv("ATLAS_JOB_SELF_HOST", "teach-box")
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
        load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
        resp = _client(tmp_path).get("/api/occupancy?host_id=host-teacher")
        assert resp.status_code == 200
        host = resp.json()["hosts"]["host-teacher"]
        assert host["idle_or_empty"] is False
        assert host["occupants"] == [
            {
                "kind": "driver",
                "agent": "claude",
                "task_id": "infra-drive",
                "epic": "7139",
            }
        ]
        assert host["ai_seats"] == ["claude"]
        text = resp.text
        for alias in _ALIAS_LEAKS:
            assert alias not in text
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


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
        load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
        resp = _client(tmp_path).get("/api/occupancy?host_id=host-teacher")
        assert resp.status_code == 200
        host = resp.json()["hosts"]["host-teacher"]
        assert host["occupants"] == []
        assert host["idle_or_empty"] is True
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_foundry_marker_keeps_low_load_host_busy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", _PLACEHOLDER_MAP)
    markers = tmp_path / "markers"
    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(markers))
    written = write_marker(
        kind="service",
        agent="foundry",
        task_id="evidence-compiler",
        epic="7102",
        host_id="host-teacher",
        path=markers,
    )
    assert written is not None
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        load_mod.clear_host_load_cache()
        idle_load = fake.host_load("teach-box")
        idle_load["loadavg"] = [0.20, 0.20, 0.20]
        idle_load["job_unit"] = {"active_count": 0, "job_id": None, "state": None}
        load_mod.set_host_load_cache("teach-box", idle_load)
        load_mod.set_host_load_cache("job-box", fake.host_load("job-box"))
        resp = _client(tmp_path).get("/api/occupancy?host_id=host-teacher")
        assert resp.status_code == 200
        host = resp.json()["hosts"]["host-teacher"]
        assert host["idle_or_empty"] is False
        assert host["occupants"] == [
            {
                "kind": "service",
                "agent": "foundry",
                "task_id": "evidence-compiler",
                "epic": "7102",
            }
        ]
        assert host["ai_seats"] == ["foundry"]
        text = json.dumps(host)
        assert _IP.findall(text) == []
        for alias in _ALIAS_LEAKS:
            assert alias not in text
        assert "/home/" not in text
        assert "ssh" not in text.lower()
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_marker_on_empty_map_linux_host_teacher_is_not_idle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Empty-map Linux fills host-teacher in-process (fresh); a live marker still blocks idle."""
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.setenv("ATLAS_RUN_ROOT", str(tmp_path / "run-root"))
    (tmp_path / "run-root").mkdir()
    monkeypatch.delenv("MONITOR_OCCUPANCY_HOST_IDS", raising=False)
    monkeypatch.setattr("scripts.api.occupancy.sys.platform", "linux")
    markers = tmp_path / "markers"
    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(markers))
    write_marker(
        kind="service",
        agent="foundry",
        task_id="evidence-compiler",
        epic="7102",
        host_id="host-teacher",
        path=markers,
    )
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        resp = _client(tmp_path).get("/api/occupancy?host_id=host-teacher")
        assert resp.status_code == 200
        host = resp.json()["hosts"]["host-teacher"]
        # One-VPS empty-map fill may report fresh/stale; the marker invariant is non-idle.
        assert host["status"] in {"fresh", "stale"}
        assert host["idle_or_empty"] is False
        assert host["occupant_count"] == 1
        assert host["occupants"][0]["kind"] == "service"
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()


def test_occupancy_marker_on_unavailable_mac_operator_is_not_idle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """mac-operator stays unavailable without observers; a live marker still blocks idle."""
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path))
    monkeypatch.delenv("MONITOR_OCCUPANCY_HOST_IDS", raising=False)
    monkeypatch.setattr("scripts.api.occupancy.sys.platform", "linux")
    markers = tmp_path / "markers"
    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(markers))
    write_marker(
        kind="service",
        agent="foundry",
        task_id="evidence-compiler",
        epic="7102",
        host_id="mac-operator",
        path=markers,
    )
    fake = atlas_job.FakeHostAdapter()
    atlas_job.set_host_adapter(fake)
    try:
        resp = _client(tmp_path).get("/api/occupancy?host_id=mac-operator")
        assert resp.status_code == 200
        host = resp.json()["hosts"]["mac-operator"]
        assert host["status"] == "unavailable"
        assert host["error"] == "unreachable"
        assert host["idle_or_empty"] is False
        assert host["occupant_count"] == 1
        assert host["occupants"][0]["kind"] == "service"
        assert host["occupants"][0]["agent"] == "foundry"
    finally:
        atlas_job.set_host_adapter(None)
        load_mod.clear_host_load_cache()
