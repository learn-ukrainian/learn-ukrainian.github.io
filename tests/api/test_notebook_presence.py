"""Notebook presence schema, partitioning, telemetry, and occupancy flow."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.api.observer_presence import (
    PRESENCE_FRESHNESS_SECONDS,
    PresenceRequest,
    list_live,
    reset_observer_presence,
    upsert_presence,
)
from scripts.api.telemetry import response as telemetry_response

loop_client = TestClient(
    app,
    base_url="http://127.0.0.1",
    client=("127.0.0.1", 51000),
    raise_server_exceptions=False,
)


@pytest.fixture(autouse=True)
def _clear_presence() -> None:
    reset_observer_presence()
    yield
    reset_observer_presence()


def _notebook_body(session_id: str = "123e4567-e89b-12d3-a456-426614174000") -> dict[str, object]:
    return {
        "agent": "claude",
        "kind": "observer",
        "task_id": "7189",
        "status": "working",
        "host_id": "mac-operator",
        "instance_id": session_id,
        "ctx_tokens": 12345,
        "window_tokens": 272000,
        "summary": "Notebook session",
    }


def test_notebook_presence_accepts_telemetry_and_rejects_invalid_fields() -> None:
    posted = loop_client.post("/api/observer/presence", json=_notebook_body())
    assert posted.status_code == 200
    body = posted.json()
    assert body["host_id"] == "mac-operator"
    assert body["instance_id"] == _notebook_body()["instance_id"]
    assert body["ctx_tokens"] == 12345
    assert body["window_tokens"] == 272000
    assert "pid" not in body

    assert loop_client.post("/api/observer/presence", json={**_notebook_body(), "extra": 1}).status_code == 422
    assert loop_client.post("/api/observer/presence", json={**_notebook_body(), "host_id": "box.example.com"}).status_code == 400
    assert loop_client.post("/api/observer/presence", json={**_notebook_body(), "instance_id": "../session"}).status_code == 400
    assert loop_client.post("/api/observer/presence", json={**_notebook_body(), "ctx_tokens": -1}).status_code == 422
    assert loop_client.post("/api/observer/presence", json={**_notebook_body(), "window_tokens": 10_000_001}).status_code == 422
    assert loop_client.post("/api/observer/presence", json={**_notebook_body(), "task_id": None}).status_code == 200


def test_store_key_isolated_by_host_and_instance() -> None:
    base = _notebook_body()
    cloud = {**base, "agent": "cursor", "host_id": None, "instance_id": None}
    mac = {**base, "agent": "cursor", "instance_id": "same-session"}
    mac_other = {**mac, "instance_id": "other-session"}
    upsert_presence(PresenceRequest.model_validate(cloud))
    upsert_presence(PresenceRequest.model_validate(mac))
    upsert_presence(PresenceRequest.model_validate(mac_other))
    rows = list_live()
    assert {(row.host_id, row.agent, row.instance_id) for row in rows} == {
        ("cloud-observer", "cursor", None),
        ("mac-operator", "cursor", "same-session"),
        ("mac-operator", "cursor", "other-session"),
    }


def test_default_occupancy_keeps_quiet_mac_without_presence() -> None:
    assert list_live() == []
    occupancy = loop_client.get("/api/occupancy")
    assert occupancy.status_code == 200
    hosts = occupancy.json()["hosts"]
    assert "mac-operator" in hosts
    host = hosts["mac-operator"]
    assert host["host_id"] == "mac-operator"
    assert host["status"] == "unavailable"
    assert host["error"] == "unreachable"
    assert host["occupants"] == []
    assert host["occupant_count"] == 0
    assert host["ai_seats"] == []
    assert host["idle_or_empty"] is False
    assert "cpu_count" not in host
    assert "mem" not in host


def test_unmocked_testclient_flow_reaches_mac_occupancy_and_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    session_id = "123e4567-e89b-12d3-a456-426614174000"
    posted = loop_client.post("/api/observer/presence", json=_notebook_body(session_id))
    assert posted.status_code == 200

    occupancy = loop_client.get("/api/occupancy")
    assert occupancy.status_code == 200
    hosts = occupancy.json()["hosts"]
    assert "mac-operator" in hosts
    host = hosts["mac-operator"]
    queried = loop_client.get("/api/occupancy?host_id=mac-operator")
    assert queried.status_code == 200
    assert queried.json()["hosts"]["mac-operator"]["occupants"] == host["occupants"]
    assert host["status"] == "unavailable"
    assert host["idle_or_empty"] is False
    assert host["occupants"] == [
        {
            "kind": "observer",
            "agent": "claude",
            "task_id": "7189",
            "epic": None,
            "status": "working",
            "instance_id": session_id,
        }
    ]

    monkeypatch.setattr(telemetry_response, "session_context_telemetry", lambda *args, **kwargs: None)
    manifest = loop_client.get(f"/api/state/manifest?session={session_id}")
    assert manifest.status_code == 200
    assert manifest.json()["_telemetry"] == {
        "ctx": 12345,
        "prev_ctx": None,
        "turn": None,
        "caller_match": True,
        "source": "notebook-presence",
        "age_s": pytest.approx(0, abs=1),
        "window": 272000,
    }


def test_telemetry_fallback_requires_fresh_matching_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(telemetry_response, "session_context_telemetry", lambda *args, **kwargs: None)
    now = time.monotonic()
    upsert_presence(
        PresenceRequest.model_validate(_notebook_body("fresh-session")),
        now_mono=now,
    )
    fresh = telemetry_response.build_telemetry_payload("fresh-session", force=True)
    assert fresh is not None
    assert fresh["source"] == "notebook-presence"
    assert fresh["ctx"] == 12345

    stale_stamp = time.monotonic() - PRESENCE_FRESHNESS_SECONDS - 1
    upsert_presence(
        PresenceRequest.model_validate(_notebook_body("stale-session")),
        now_mono=stale_stamp,
    )
    stale = telemetry_response.build_telemetry_payload("stale-session", force=True)
    other = telemetry_response.build_telemetry_payload("missing-session", force=True)
    assert stale == {
        "ctx": None,
        "prev_ctx": None,
        "turn": None,
        "caller_match": False,
        "reason": "session-transcript-not-found",
    }
    assert other == stale


def test_telemetry_fallback_rejects_cloud_and_gui_instance_collisions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(telemetry_response, "session_context_telemetry", lambda *args, **kwargs: None)
    session_id = "collision-session"
    upsert_presence(
        PresenceRequest.model_validate(
            {**_notebook_body(session_id), "agent": "cursor", "host_id": None}
        )
    )
    cloud_result = telemetry_response.build_telemetry_payload(session_id, force=True)
    assert cloud_result == {
        "ctx": None,
        "prev_ctx": None,
        "turn": None,
        "caller_match": False,
        "reason": "session-transcript-not-found",
    }

    reset_observer_presence()
    upsert_presence(
        PresenceRequest.model_validate(
            {**_notebook_body(session_id), "agent": "cursor", "instance_id": "gui"}
        )
    )
    gui_result = telemetry_response.build_telemetry_payload(session_id, force=True)
    assert gui_result == cloud_result

    reset_observer_presence()
    upsert_presence(
        PresenceRequest.model_validate(
            {**_notebook_body(session_id), "agent": "cursor", "host_id": None}
        )
    )
    upsert_presence(PresenceRequest.model_validate(_notebook_body(session_id)))
    selected = telemetry_response.build_telemetry_payload(session_id, force=True)
    assert selected is not None
    assert selected["source"] == "notebook-presence"
    assert selected["ctx"] == 12345
