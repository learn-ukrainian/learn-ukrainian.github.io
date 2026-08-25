"""Loopback router contract for remote epic lifecycle v1."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.store import LifecycleError, SessionStreamStore
from scripts.api import epics_router


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "api.sqlite3"))
    epics_router.seed_manifest_inventory(epics_router.LIVE_REPO_ROOT, store=store)
    monkeypatch.setattr(epics_router, "_store", lambda: store)
    app = FastAPI()
    app.include_router(epics_router.router, prefix="/api/epics")
    return TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 8765))


def _claim(
    client: TestClient,
    stream_id: str = "epic:7178",
    *,
    session_id: str = "api-session",
    lease_id: str = "api-lease",
) -> dict:
    response = client.post(
        f"/api/epics/v1/{stream_id}/claim",
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
    assert (
        client.post("/api/epics/v1/epic:7178/release", json=exact).status_code == 200
    )  # allow-hardcoded-epic: remote lifecycle route fixture


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
    assert (
        client.post("/api/epics/v1/epic:7178/release", json={"force": True}).status_code == 400
    )  # allow-hardcoded-epic: remote lifecycle route fixture

    bad = client.post(
        "/api/epics/v1/epic:7178/handoff",
        json={**_claim(client)["lease"], "type": "note", "body": "10.0.0.1", "idempotency_key": "bad"},
    )
    # The claim above replays the first lease, so the body is rejected by the API hygiene gate.
    assert bad.status_code == 400


def test_router_live_claim_conflict_names_holder_and_expiry(tmp_path: Path, monkeypatch) -> None:
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
    assert "current holder=codex/codex-cli" in competing.text
    assert "instance_id=api-instance" in competing.text
    assert "expires_at=" in competing.text


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


@pytest.mark.parametrize("failure", [sqlite3.IntegrityError("foreign key"), LifecycleError("unsafe lifecycle")])
def test_router_claim_invariant_failures_are_logged_and_not_store_unavailable(
    tmp_path: Path, monkeypatch, caplog, failure: Exception
) -> None:
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "api.sqlite3"))

    def fail_claim(**_kwargs):
        raise failure

    monkeypatch.setattr(store, "claim_remote_session", fail_claim)
    monkeypatch.setattr(epics_router, "_store", lambda: store)
    app = FastAPI()
    app.include_router(epics_router.router, prefix="/api/epics")

    with caplog.at_level(logging.ERROR, logger=epics_router.__name__):
        response = TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 8765)).post(
            "/api/epics/v1/epic:7178/claim",
            json={
                "session_id": "failed-session",
                "lease_id": "failed-lease",
                "lineage_id": "failed-lineage",
                "agent": "codex",
                "harness": "codex-cli",
                "instance_id": "failed-instance",
                "process_id": 1234,
                "host_id": "failed-host",
            },
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "epic claim rejected by a session-stream invariant"
    assert "store unavailable" not in response.text
    assert any(record.exc_info for record in caplog.records)


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
    assert sanitized["stream"] == "epic:7178"  # allow-hardcoded-epic: remote lifecycle response fixture
    assert sanitized["refs"] == []


def test_epics_graph_endpoint_contract_and_structure(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    mock_audit = {
        "generated_at": 1700000000,
        "effective_membership": {
            "7269": {"epics": [7177], "streams": ["monitor"], "via": "native", "unique_stream": True},  # allow-hardcoded-epic: mock audit data
            "7270": {"epics": [7177], "streams": ["monitor"], "via": "native", "unique_stream": True},  # allow-hardcoded-epic: mock audit data
            "7271": {"epics": [7177], "streams": ["monitor"], "via": "native", "unique_stream": True},  # allow-hardcoded-epic: mock audit data
            "7100": {"epics": [7177], "streams": ["monitor"], "via": "native", "unique_stream": True},  # allow-hardcoded-epic: mock audit data
        },
        "open_issue_numbers": [7269, 7270, 7271],
        "open_issue_titles": {
            "7269": "Epics graph endpoint",
            "7270": "Dashboard map view",
            "7271": "Verification gates",
        },
    }

    monkeypatch.setattr(epics_router.audit, "read_cache", lambda max_age_s: mock_audit if max_age_s == 3600 else None)
    monkeypatch.setattr(
        epics_router.audit,
        "read_refresh_state",
        lambda: {"phase": "idle", "last_outcome": "succeeded", "last_outcome_at": 1700000000},
    )

    response = client.get("/api/epics/graph/v1")
    assert response.status_code == 200
    data = response.json()

    assert data["schema"] == "epics-graph.v1"
    assert "generated_at" in data
    assert data["refreshing"] is False
    assert data["refresh"]["phase"] == "idle"

    # Verify nodes.areas
    areas = {a["id"]: a for a in data["nodes"]["areas"]}
    assert "area:monitor" in areas
    assert areas["area:monitor"]["stream_id"] == "monitor"
    assert areas["area:monitor"]["epic_count"] == 1
    assert "Monitor API + UI" in areas["area:monitor"]["title"]

    # Verify nodes.epics
    epics = {e["id"]: e for e in data["nodes"]["epics"]}
    assert "epic:7177" in epics  # allow-hardcoded-epic: graph contract check
    monitor_epic = epics["epic:7177"]  # allow-hardcoded-epic: graph contract check
    assert monitor_epic["number"] == 7177  # allow-hardcoded-epic: graph contract check
    assert monitor_epic["area_id"] == "monitor"
    assert monitor_epic["open_issue_count"] == 3
    assert monitor_epic["closed_issue_count"] == 1
    assert "last_state" in monitor_epic
    assert "last_decision" in monitor_epic
    assert "last_next_action" in monitor_epic

    # Verify edges
    edge_pairs = {(e["from"], e["to"]) for e in data["edges"]}
    assert ("area:monitor", "epic:7177") in edge_pairs  # allow-hardcoded-epic: graph edge check

    # Verify issues_by_epic
    assert "7177" in data["issues_by_epic"]  # allow-hardcoded-epic: issues_by_epic check
    epic_issues = data["issues_by_epic"]["7177"]  # allow-hardcoded-epic: issues_by_epic check
    assert epic_issues["total_open"] == 3
    assert epic_issues["truncated"] is False
    assert len(epic_issues["items"]) == 3

    first_item = epic_issues["items"][0]
    assert first_item["number"] == 7269
    assert first_item["title"] == "Epics graph endpoint"
    assert first_item["state"] == "open"
    assert first_item["url"] == "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7269"


def test_epics_graph_stale_and_no_cache_fallbacks(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    stale_audit = {
        "generated_at": 1600000000,
        "effective_membership": {},
        "open_issue_numbers": [],
        "open_issue_titles": {},
    }

    # Case 1: Fresh cache miss, stale cache hit
    monkeypatch.setattr(
        epics_router.audit,
        "read_cache",
        lambda max_age_s: stale_audit if max_age_s > 3600 else None,
    )
    scheduled = []
    monkeypatch.setattr(
        epics_router.audit,
        "schedule_refresh",
        lambda force=False: scheduled.append(force) or {"phase": "scheduled", "requested_at": 1700000000},
    )

    resp_stale = client.get("/api/epics/graph/v1")
    assert resp_stale.status_code == 200
    stale_data = resp_stale.json()
    assert stale_data["stale"] is True
    assert stale_data["refreshing"] is True
    assert scheduled == [False]

    # Case 2: Complete cache miss (no fresh, no stale)
    monkeypatch.setattr(epics_router.audit, "read_cache", lambda max_age_s: None)
    scheduled.clear()
    resp_no_cache = client.get("/api/epics/graph/v1")
    assert resp_no_cache.status_code == 200
    no_cache_data = resp_no_cache.json()
    assert no_cache_data["status"] == "no-cache"
    assert no_cache_data["ok"] is None
    assert scheduled == [False]

    # Case 3: Explicit fresh=true param
    scheduled.clear()
    resp_fresh = client.get("/api/epics/graph/v1?fresh=true")
    assert resp_fresh.status_code == 200
    assert scheduled == [True]


def test_epics_graph_truncation_cap_at_50(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    # 60 open issues for epic 7177
    effective_membership = {
        str(1000 + i): {"epics": [7177], "streams": ["monitor"], "via": "native", "unique_stream": True}  # allow-hardcoded-epic: mock audit data
        for i in range(60)
    }
    open_issue_numbers = [1000 + i for i in range(60)]
    open_issue_titles = {str(1000 + i): f"Open issue {1000 + i}" for i in range(60)}

    mock_audit = {
        "generated_at": 1700000000,
        "effective_membership": effective_membership,
        "open_issue_numbers": open_issue_numbers,
        "open_issue_titles": open_issue_titles,
    }

    monkeypatch.setattr(epics_router.audit, "read_cache", lambda max_age_s: mock_audit)
    monkeypatch.setattr(
        epics_router.audit,
        "read_refresh_state",
        lambda: {"phase": "idle"},
    )

    response = client.get("/api/epics/graph/v1")
    assert response.status_code == 200
    data = response.json()

    monitor_issues = data["issues_by_epic"]["7177"]  # allow-hardcoded-epic: truncation check
    assert monitor_issues["total_open"] == 60
    assert monitor_issues["truncated"] is True
    assert len(monitor_issues["items"]) == 50


def test_epics_graph_store_lease_and_decision_passthrough(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    claimed = _claim(client, "epic:7177")  # allow-hardcoded-epic: remote lifecycle route fixture
    lease = claimed["lease"]

    # Append a state entry and a decision entry
    client.post(
        "/api/epics/v1/epic:7177/handoff",  # allow-hardcoded-epic: remote lifecycle route fixture
        json={**lease, "type": "state", "body": "working on graph", "idempotency_key": "graph-state-1"},
    )
    client.post(
        "/api/epics/v1/epic:7177/handoff",  # allow-hardcoded-epic: remote lifecycle route fixture
        json={**lease, "type": "decision", "body": "design approved", "idempotency_key": "graph-dec-1"},
    )

    monkeypatch.setattr(epics_router.audit, "read_cache", lambda max_age_s: {"generated_at": 1700000000})
    monkeypatch.setattr(epics_router.audit, "read_refresh_state", lambda: {"phase": "idle"})

    response = client.get("/api/epics/graph/v1")
    assert response.status_code == 200
    data = response.json()

    epics_by_id = {e["id"]: e for e in data["nodes"]["epics"]}
    assert "epic:7177" in epics_by_id  # allow-hardcoded-epic: store passthrough check
    epic_7177 = epics_by_id["epic:7177"]  # allow-hardcoded-epic: store passthrough check
    assert epic_7177["lease"] is not None
    assert epic_7177["last_state"]["body"] == "working on graph"
    assert epic_7177["last_decision"]["body"] == "design approved"

