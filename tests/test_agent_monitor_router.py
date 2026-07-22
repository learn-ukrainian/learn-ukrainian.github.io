import os

import psutil
from fastapi.testclient import TestClient

TEST_TOKEN = "test-agent-monitor-token-5652"
os.environ["AGENT_MONITOR_TOKEN"] = TEST_TOKEN

from scripts.api.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-Agent-Monitor-Token": TEST_TOKEN}


def test_agent_monitor_status():
    res = client.get("/api/agent-monitor/status")
    assert res.status_code == 200
    data = res.json()
    assert data["host"] == "local_fleet"
    assert "ram" in data
    assert "capacity_reservations" in data
    assert data["capacity_reservations"]["active_leases_count"] >= 0


def test_agent_monitor_preflight():
    res = client.post(
        "/api/agent-monitor/preflight",
        json={"agent_id": "gemini/test", "task_name": "test_preflight", "required_ram_mb": 256},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] in ["APPROVED", "REJECTED"]


def test_agent_monitor_unauthorized():
    res = client.post(
        "/api/agent-monitor/register",
        json={
            "agent_id": "gemini/unauth",
            "task_name": "test",
            "pid": os.getpid(),
            "process_create_time": psutil.Process(os.getpid()).create_time(),
            "reserved_ram_mb": 256,
        },
        headers={"X-Agent-Monitor-Token": "invalid-token"},
    )
    assert res.status_code == 401


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
        headers=AUTH_HEADERS,
    )
    assert reg.status_code == 200
    data = reg.json()
    assert data["verdict"] == "APPROVED"
    token = data["lease_token"]

    # Heartbeat
    hb = client.post(
        "/api/agent-monitor/heartbeat",
        json={"lease_token": token, "pid": current_pid},
        headers=AUTH_HEADERS,
    )
    assert hb.status_code == 200

    # Release
    rel = client.post(
        f"/api/agent-monitor/release?lease_token={token}",
        headers=AUTH_HEADERS,
    )
    assert rel.status_code == 200


def test_agent_monitor_register_idempotent():
    current_pid = os.getpid()
    proc = psutil.Process(current_pid)
    create_time = proc.create_time()

    payload = {
        "agent_id": "gemini/test-idem",
        "task_name": "unit_test",
        "pid": current_pid,
        "process_create_time": create_time,
        "reserved_ram_mb": 256,
    }

    reg1 = client.post("/api/agent-monitor/register", json=payload, headers=AUTH_HEADERS)
    assert reg1.status_code == 200
    token1 = reg1.json()["lease_token"]

    reg2 = client.post("/api/agent-monitor/register", json=payload, headers=AUTH_HEADERS)
    assert reg2.status_code == 200
    token2 = reg2.json()["lease_token"]

    assert token1 == token2
    assert reg2.json().get("idempotent_reattach") is True
