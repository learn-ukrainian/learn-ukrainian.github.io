"""Loopback router contract for remote epic lifecycle v1."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api import epics_router


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "api.sqlite3"))
    monkeypatch.setattr(epics_router, "_store", lambda: store)
    app = FastAPI()
    app.include_router(epics_router.router, prefix="/api/epics")
    return TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 8765))


def _claim(client: TestClient, *, session_id: str = "api-session", lease_id: str = "api-lease") -> dict:
    response = client.post(
        "/api/epics/v1/epic:7178/claim",
        json={
            "session_id": session_id,
            "lease_id": lease_id,
            "lineage_id": "api-lineage",
            "agent": "codex",
            "harness": "codex-cli",
            "instance_id": "api-instance",
            "process_id": 1234,
            "host_id": "api-host",
            "ttl_seconds": 900,
            "digest_limit": 5,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_router_claim_heartbeat_handoff_release_round_trip(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    claimed = _claim(client)
    lease = claimed["lease"]
    assert claimed["outcome"] == "claimed"
    assert _claim(client)["outcome"] == "replayed"

    heartbeat = client.post("/api/epics/v1/epic:7178/heartbeat", json=lease)
    assert heartbeat.status_code == 200
    exact = heartbeat.json()["lease"]
    handoff = client.post(
        "/api/epics/v1/epic:7178/handoff",
        json={**exact, "type": "state", "body": "working", "idempotency_key": "api-state-1"},
    )
    assert handoff.status_code == 200
    assert handoff.json()["entry"]["type"] == "state"

    released = client.post("/api/epics/v1/epic:7178/release", json=exact)
    assert released.status_code == 200
    assert released.json()["outcome"] == "released"
    assert client.post("/api/epics/v1/epic:7178/release", json=exact).status_code == 200


def test_router_rejects_live_holder_force_without_actor_and_opsec_body(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    _claim(client)
    competing = client.post(
        "/api/epics/v1/epic:7178/claim",
        json={
            "session_id": "other-session",
            "lease_id": "other-lease",
            "lineage_id": "other-lineage",
            "agent": "gemini",
            "harness": "agy",
            "instance_id": "other-instance",
            "process_id": 5678,
            "host_id": "other-host",
        },
    )
    assert competing.status_code == 409
    assert client.post("/api/epics/v1/epic:7178/release", json={"force": True}).status_code == 400

    bad = client.post(
        "/api/epics/v1/epic:7178/handoff",
        json={**_claim(client)["lease"], "type": "note", "body": "10.0.0.1", "idempotency_key": "bad"},
    )
    # The claim above replays the first lease, so the body is rejected by the API hygiene gate.
    assert bad.status_code == 400


def test_router_responses_have_no_paths_or_host_network_tokens(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    response = _claim(client)
    response_text = json.dumps(response, sort_keys=True)
    assert "/Users/" not in response_text
    assert "/home/" not in response_text
    assert "127.0.0.1" not in response_text
    assert "atlas-runner" not in response_text
    status = client.get("/api/epics/v1/epic:7178")
    assert status.status_code == 200
    assert "/Users/" not in status.text
    assert "/home/" not in status.text


def test_router_force_release_requires_and_records_actor(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    _claim(client)
    response = client.post(
        "/api/epics/v1/epic:7178/release",
        json={
            "force": True,
            "actor_agent": "operator",
            "actor_host_id": "operator-host",
            "reason": "operator recovery",
        },
    )
    assert response.status_code == 200
    assert response.json()["outcome"] == "force_released"


def test_router_rejects_shared_stream_aliases(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    response = client.post(
        "/api/epics/v1/shared:legacy/claim",
        json={"session_id": "session", "lease_id": "lease", "lineage_id": "lineage"},
    )
    assert response.status_code == 400


def test_router_redacts_legacy_uri_references(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    payload = {
        "entry_id": 1,
        "stream": "epic:7178",
        "session_id": "session",
        "agent": "codex",
        "harness": "codex-cli",
        "idempotency_key": "key",
        "body": "safe",
        "refs": [{"kind": "source", "uri": "/Users/alice/private.txt", "target_entry_id": None}],
    }
    sanitized = epics_router._safe_entry(payload)
    assert "/Users/" not in json.dumps(sanitized)
    assert sanitized["refs"] == []
