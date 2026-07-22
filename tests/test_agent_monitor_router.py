import os

import psutil
from fastapi.testclient import TestClient

from scripts.api.main import app

client = TestClient(app)


def test_agent_monitor_status():
    res = client.get("/api/agent-monitor/status")
    assert res.status_code == 200
    data = res.json()
    assert data["host"] == "local_fleet"
    assert "ram" in data
    assert "active_leases" in data


def test_agent_monitor_preflight():
    res = client.post(
        "/api/agent-monitor/preflight",
        json={"agent_id": "gemini/test", "task_name": "test_preflight", "required_ram_mb": 256},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] in ["APPROVED", "REJECTED"]


def test_agent_monitor_register_heartbeat_release():
    current_pid = os.getpid()
    proc = psutil.Process(current_pid)
    create_time = proc.create_time()

    reg = client.post(
        "/api/agent-monitor/register",
        json={
            "agent_id": "gemini/test-register",
            "task_name": "unit_test",
            "pid": current_pid,
            "process_create_time": create_time,
            "reserved_ram_mb": 256,
        },
    )
    assert reg.status_code == 200
    data = reg.json()
    assert data["verdict"] == "APPROVED"
    token = data["lease_token"]

    # Heartbeat
    hb = client.post("/api/agent-monitor/heartbeat", json={"lease_token": token, "pid": current_pid})
    assert hb.status_code == 200

    # Release
    rel = client.post(f"/api/agent-monitor/release?lease_token={token}")
    assert rel.status_code == 200
