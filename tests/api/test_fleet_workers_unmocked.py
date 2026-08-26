"""Unmocked TestClient probe for /api/fleet/workers/v1 (#7187, #7265)."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.api.fleet_workers_collect import UNATTRIBUTED_HOST_ID, reset_workers_payload_cache
from scripts.api.main import app
from scripts.api.observer_presence import PresenceRequest, reset_observer_presence, upsert_presence
from scripts.api.occupancy_local import write_marker
from scripts.api.project_state_router import reset_local_document_cache
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
    reset_local_document_cache()
    reset_workers_payload_cache()

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

    print(
        "UNMOCKED_WORKERS_PROBE_OK",
        json.dumps({"delegate_kinds": sorted(kinds), "observer_count": len(observer["workers"])}),
    )


def _seed_local_driver_lease(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            stream_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            state TEXT NOT NULL,
            PRIMARY KEY (stream_id, session_id)
        );
        CREATE TABLE IF NOT EXISTS stream_leases (
            stream_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            state TEXT NOT NULL,
            holder_agent TEXT,
            holder_harness TEXT,
            holder_instance_id TEXT,
            holder_task_id TEXT,
            holder_host_id TEXT,
            heartbeat_at TEXT,
            expires_at TEXT
        );
        """
    )
    expires = (datetime.now(UTC) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    heartbeat = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    conn.execute("INSERT OR REPLACE INTO sessions VALUES ('epic:7265', 'sess-local', 'open')")
    conn.execute(
        """
        INSERT INTO stream_leases VALUES (
            'epic:7265', 'sess-local', 'active', 'grok', 'grok-tools',
            'inst-local-7265', 'task-local', 'local', ?, ?
        )
        """,
        (heartbeat, expires),
    )
    conn.commit()
    conn.close()


def test_unmocked_local_host_driver_lease_in_unattributed_bucket(tmp_path: Path, monkeypatch) -> None:
    """Driver lease with holder_host_id local must surface under unattributed, not vanish."""
    reset_project_state_store()
    reset_observer_presence()
    reset_local_document_cache()
    reset_workers_payload_cache()

    db = tmp_path / "session_streams.db"
    _seed_local_driver_lease(db)
    monkeypatch.setattr("scripts.api.fleet_workers_collect.session_streams_db_path", lambda: db)
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", "teach-box=host-teacher,job-box=host-job")
    monkeypatch.setenv("LU_MONITOR_HOST_ID", "host-teacher")

    response = client.get("/api/fleet/workers/v1")
    assert response.status_code == 200
    payload = response.json()
    unattributed = _host_by_id(payload, UNATTRIBUTED_HOST_ID)
    assert unattributed["reason"] == "lease has no host claim"
    worker_ids = {row["id"] for row in unattributed["workers"]}
    assert worker_ids == {"inst-local-7265"}
    assert payload["counts"]["live"] >= 1
    teacher = _host_by_id(payload, "host-teacher")
    assert not any(row.get("id") == "inst-local-7265" for row in teacher["workers"])

    print(
        "UNMOCKED_LOCAL_LEASE_PROBE_OK",
        json.dumps({"live": payload["counts"]["live"], "worker_ids": sorted(worker_ids)}),
    )
