"""Tests for POST /api/observer/presence (#7063)."""

from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.api.observer_presence import (
    PRESENCE_TTL_SECONDS,
    PresenceRequest,
    list_live,
    reset_observer_presence,
    upsert_presence,
)

loop_client = TestClient(
    app,
    base_url="http://127.0.0.1",
    client=("127.0.0.1", 50000),
    raise_server_exceptions=False,
)
remote_client = TestClient(
    app,
    base_url="http://testserver",
    client=("testclient", 50000),
    raise_server_exceptions=False,
)

_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_ALIAS_LEAKS = ("atlas-runner", "hramatka", "vps")
_HEARTBEAT = {
    "agent": "grok-bot",
    "kind": "observer",
    "task_id": "7061",
    "epic": "6943",
    "status": "working",
    "summary": "tunneled Monitor observer sweep",
}


@pytest.fixture(autouse=True)
def _clear_observer_presence() -> None:
    reset_observer_presence()
    yield
    reset_observer_presence()


def test_presence_loopback_heartbeat_appears_under_cloud_observer() -> None:
    posted = loop_client.post("/api/observer/presence", json=_HEARTBEAT)
    assert posted.status_code == 200
    body = posted.json()
    assert body["agent"] == "grok-bot"
    assert body["kind"] == "observer"
    assert body["task_id"] == "7061"
    assert body["host_id"] == "cloud-observer"
    assert body["ttl_seconds"] == PRESENCE_TTL_SECONDS
    assert body["summary"] == "tunneled Monitor observer sweep"
    assert "pid" not in body
    assert "reserved_ram_mb" not in body
    assert posted.headers.get("cache-control") == "no-store"

    occupancy = remote_client.get("/api/occupancy")
    assert occupancy.status_code == 200
    data = occupancy.json()
    host = data["hosts"]["cloud-observer"]
    assert host["host_id"] == "cloud-observer"
    assert host["status"] == "fresh"
    assert host["burn_state"] == "active"
    assert set(host["burn_sources"]) == {"atlas_job", "driver", "foundry"}
    assert all(source["state"] == "clear" for source in host["burn_sources"].values())
    assert all(source["observation_age_s"] >= 0 for source in host["burn_sources"].values())
    assert host["idle_or_empty"] is False
    assert host["ai_seats"] == ["grok-bot"]
    assert "cpu_count" not in host
    assert "mem" not in host
    assert "error" not in host
    assert host["occupants"] == [
        {
            "kind": "observer",
            "agent": "grok-bot",
            "task_id": "7061",
            "epic": "6943",
            "status": "working",
        }
    ]
    assert "summary" not in host["occupants"][0]
    text = json.dumps(data)
    assert "summary" not in text
    assert _IP.findall(text) == []
    for alias in _ALIAS_LEAKS:
        assert alias not in text


def test_presence_rejects_non_loopback_peer() -> None:
    posted = remote_client.post("/api/observer/presence", json=_HEARTBEAT)
    assert posted.status_code == 403
    occupancy = remote_client.get("/api/occupancy")
    hosts = occupancy.json()["hosts"]
    assert "cloud-observer" not in hosts
    assert "mac-operator" in hosts
    assert hosts["mac-operator"]["occupants"] == []
    assert hosts["mac-operator"]["status"] == "unavailable"


def test_default_occupancy_keeps_quiet_mac_alongside_cloud_observer() -> None:
    posted = loop_client.post("/api/observer/presence", json=_HEARTBEAT)
    assert posted.status_code == 200
    occupancy = remote_client.get("/api/occupancy")
    assert occupancy.status_code == 200
    hosts = occupancy.json()["hosts"]
    assert "cloud-observer" in hosts
    assert "mac-operator" in hosts
    assert hosts["mac-operator"]["occupants"] == []
    assert hosts["mac-operator"]["status"] == "unavailable"
    assert hosts["mac-operator"]["idle_or_empty"] is False
    assert hosts["cloud-observer"]["occupants"][0]["agent"] == "grok-bot"
    assert hosts["cloud-observer"]["burn_state"] == "active"
    assert hosts["cloud-observer"]["idle_or_empty"] is False
    assert set(hosts["cloud-observer"]["burn_sources"]) == {"atlas_job", "driver", "foundry"}


def test_presence_rejects_ram_lease_fields() -> None:
    posted = loop_client.post(
        "/api/observer/presence",
        json={**_HEARTBEAT, "pid": 12, "reserved_ram_mb": 256},
    )
    assert posted.status_code == 422


def test_presence_rejects_unknown_agent_and_leaky_summary() -> None:
    unknown = loop_client.post("/api/observer/presence", json={**_HEARTBEAT, "agent": "claude"})
    assert unknown.status_code == 400
    for summary in (
        "talk to atlas-runner",
        "notes/etc/passwd",
        "token=abc123",
        "see box.example.com",
        "box.example.com!",
        "pid=12 reserved_ram_mb=256",
        "bearer secret value",
    ):
        leaky = loop_client.post(
            "/api/observer/presence",
            json={**_HEARTBEAT, "summary": summary},
        )
        assert leaky.status_code == 400, summary
    alias_epic = loop_client.post(
        "/api/observer/presence",
        json={**_HEARTBEAT, "epic": "hramatka"},
    )
    assert alias_epic.status_code == 400
    dotted_task = loop_client.post(
        "/api/observer/presence",
        json={**_HEARTBEAT, "task_id": "box.example.com."},
    )
    assert dotted_task.status_code == 400


def test_presence_upserts_per_agent_and_drops_after_ttl() -> None:
    first = upsert_presence(PresenceRequest.model_validate(_HEARTBEAT), now_mono=100.0, ttl_seconds=15)
    assert first.task_id == "7061"
    second = upsert_presence(
        PresenceRequest.model_validate({**_HEARTBEAT, "task_id": "7063", "status": "blocked"}),
        now_mono=110.0,
        ttl_seconds=15,
    )
    live = list_live(now_mono=120.0)
    assert len(live) == 1
    assert live[0].task_id == "7063"
    assert live[0].status == "blocked"
    assert second.agent == "grok-bot"
    assert list_live(now_mono=126.0) == []


def test_idle_observer_occupancy_reports_idle_burn() -> None:
    posted = loop_client.post(
        "/api/observer/presence",
        json={
            "agent": "qa-engineer",
            "kind": "observer",
            "task_id": "7063",
            "status": "idle",
            "summary": "waiting on review",
        },
    )
    assert posted.status_code == 200
    occupancy = remote_client.get("/api/occupancy?host_id=cloud-observer")
    assert occupancy.status_code == 200
    host = occupancy.json()["hosts"]["cloud-observer"]
    assert host["burn_state"] == "idle"
    assert host["idle_or_empty"] is True
    assert host["occupants"] == [
        {
            "kind": "observer",
            "agent": "qa-engineer",
            "task_id": "7063",
            "epic": None,
            "status": "idle",
        }
    ]
    assert "summary" not in host["occupants"][0]
    assert "pid" not in occupancy.text
    assert "reserved_ram_mb" not in occupancy.text


def test_qa_engineer_and_grok_bot_can_coexist() -> None:
    loop_client.post("/api/observer/presence", json=_HEARTBEAT)
    qa = loop_client.post(
        "/api/observer/presence",
        json={
            "agent": "qa-engineer",
            "kind": "observer",
            "task_id": "6742",
            "status": "idle",
        },
    )
    assert qa.status_code == 200
    occupancy = remote_client.get("/api/occupancy?host_id=cloud-observer")
    agents = {row["agent"] for row in occupancy.json()["hosts"]["cloud-observer"]["occupants"]}
    assert agents == {"grok-bot", "qa-engineer"}


def test_cursor_driver_heartbeat_appears_under_cloud_observer() -> None:
    posted = loop_client.post(
        "/api/observer/presence",
        json={
            "agent": "cursor",
            "kind": "observer",
            "task_id": "7075",
            "epic": "7073",
            "status": "working",
            "summary": "cursor driver occupancy heartbeat",
        },
    )
    assert posted.status_code == 200
    assert posted.json()["agent"] == "cursor"
    occupancy = remote_client.get("/api/occupancy")
    occupants = occupancy.json()["hosts"]["cloud-observer"]["occupants"]
    assert occupants == [
        {
            "kind": "observer",
            "agent": "cursor",
            "task_id": "7075",
            "epic": "7073",
            "status": "working",
        }
    ]
    assert "summary" not in occupants[0]


def test_codex_ui_heartbeat_appears_under_cloud_observer() -> None:
    posted = loop_client.post(
        "/api/observer/presence",
        json={
            "agent": "codex",
            "kind": "observer",
            "task_id": "7104",
            "epic": "7073",
            "status": "working",
            "summary": "codex ui occupancy heartbeat",
        },
    )
    assert posted.status_code == 200
    assert posted.json()["agent"] == "codex"
    occupancy = remote_client.get("/api/occupancy")
    occupants = occupancy.json()["hosts"]["cloud-observer"]["occupants"]
    assert occupants == [
        {
            "kind": "observer",
            "agent": "codex",
            "task_id": "7104",
            "epic": "7073",
            "status": "working",
        }
    ]
    assert "summary" not in occupants[0]
