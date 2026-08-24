"""Unmocked TestClient probe for /api/fleet/workers/v1 (#7187)."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.api.observer_presence import PresenceRequest, reset_observer_presence, upsert_presence
from scripts.api.occupancy_local import write_marker
from scripts.api.project_state_store import reset_project_state_store

client = TestClient(app, raise_server_exceptions=False)


def _host_by_id(payload: dict, host_id: str) -> dict:
    hosts = payload["hosts"]
    assert isinstance(hosts, list)
    for host in hosts:
        if host.get("host_id") == host_id:
            return host
    raise AssertionError(f"host {host_id!r} not in {hosts!r}")


def test_unmocked_workers_route_with_fixture_stores(tmp_path: Path, monkeypatch) -> None:
    """Exercise real adapters on fixture stores without monkeypatching the collector."""
    reset_project_state_store()
    reset_observer_presence()

    tasks = tmp_path / "tasks"
    tasks.mkdir()
    started = datetime.now(UTC).isoformat()
    (tasks / "live-task.json").write_text(
        json.dumps(
            {
                "task_id": "live-task",
                "agent": "cursor",
                "status": "running",
                "pid": os.getpid(),
                "started_at": started,
                "run_nonce": "probe-nonce-1234",
            }
        ),
        encoding="utf-8",
    )

    markers = tmp_path / "markers"
    write_marker(kind="service", task_id="svc-1", host_id="host-job", agent="codex", path=markers)

    upsert_presence(PresenceRequest(agent="cursor", task_id="observe-1", status="working"))

    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", "teach-box=host-teacher,job-box=host-job")
    monkeypatch.setenv("LU_MONITOR_HOST_ID", "host-job")
    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(markers))
    monkeypatch.setattr("scripts.api.delegate_router.TASKS_DIR", tasks)

    response = client.get("/api/fleet/workers/v1?host_id=host-job")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "monitor-fleet-workers.v1"
    assert isinstance(payload["hosts"], list)
    host = _host_by_id(payload, "host-job")
    assert host["workers_status"] == "reported"
    kinds = {row["kind"] for row in host["workers"]}
    assert "delegate" in kinds

    observer = _host_by_id(client.get("/api/fleet/workers/v1?host_id=cloud-observer").json(), "cloud-observer")
    assert any(row["kind"] == "observer" for row in observer["workers"])

    print("UNMOCKED_WORKERS_PROBE_OK", json.dumps({"delegate_kinds": sorted(kinds), "observer_count": len(observer["workers"])}))
