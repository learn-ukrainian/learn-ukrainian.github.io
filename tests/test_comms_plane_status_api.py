"""Monitor API plane-status surface (read-only; Sol PR-K-ish / #5512)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.fleet_comms.message_plane import read_plane_status
from scripts.fleet_comms.migrations import MIGRATIONS, apply_migrations


def _client() -> TestClient:
    from scripts.api.comms_router import router

    app = FastAPI()
    app.include_router(router, prefix="/api/comms")
    return TestClient(app)


def test_read_plane_status_defaults_to_configured_mode(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("FLEET_COMMS_MESSAGE_PLANE", raising=False)
    # Every production caller (Monitor API routers, CLI) passes an in-repo
    # PROJECT_ROOT; this fixture is a non-git tmp dir, and since #6863 the
    # default plane root hard-fails there, so anchor via the explicit
    # operator override. The default under test is the plane MODE.
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "plane"))
    monkeypatch.delenv("FLEET_COMMS_PLANE_TELEMETRY", raising=False)
    status = read_plane_status(repo_root=tmp_path)
    # The final migration gate promotes durable authority as the default.
    assert status["mode"] == "authority"
    assert status["enabled"] is True
    assert status["read_only"] is True
    assert status["schema"]["known_version"] == MIGRATIONS[-1].version
    assert status["schema"]["applied_version"] is None
    assert status["schema"]["db_exists"] is False
    assert status["parity_telemetry"]["exists"] is False
    assert status["parity_telemetry"]["event_count"] == 0
    assert "plane_root" not in status
    assert "db_path" not in status["schema"]
    assert "path" not in status["parity_telemetry"]
    assert status["store"]["kind"] == "comms-plane"
    assert status["store"]["reachable"] is False


def test_read_plane_status_with_schema_and_telemetry(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "fleet-comms" / "v1"
    root.mkdir(parents=True)
    db_path = root / "comms.sqlite3"
    conn = sqlite3.connect(str(db_path))
    try:
        applied = apply_migrations(conn)
        assert applied == MIGRATIONS[-1].version
    finally:
        conn.close()

    tele = root / "telemetry" / "plane-parity.jsonl"
    tele.parent.mkdir(parents=True)
    events = [
        {"event": "plane_complete", "parity_ok": True, "request_id": "a"},
        {"event": "plane_complete", "parity_ok": False, "request_id": "b"},
        {"event": "plane_refuse_legacy_replied", "request_id": "c"},
    ]
    tele.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "shadow")
    status = read_plane_status(root=root, telemetry_path=tele)
    assert status["mode"] == "shadow"
    assert status["enabled"] is True
    assert status["schema"]["db_exists"] is True
    assert status["schema"]["applied_version"] == MIGRATIONS[-1].version
    assert status["schema"]["applied_name"] == MIGRATIONS[-1].name
    assert status["parity_telemetry"]["exists"] is True
    assert status["parity_telemetry"]["event_count"] == 3
    assert status["parity_telemetry"]["parity_ok_count"] == 1
    assert status["parity_telemetry"]["parity_fail_count"] == 1
    assert len(status["parity_telemetry"]["recent"]) == 3
    assert "plane_root" not in status
    assert "db_path" not in status["schema"]
    assert "path" not in status["parity_telemetry"]
    assert status["response_schema_version"] == "comms.v2"


def test_api_plane_status_endpoint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "dual_write")
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "plane"))
    tele = tmp_path / "tele.jsonl"
    tele.write_text(
        json.dumps({"event": "plane_complete", "parity_ok": True}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("FLEET_COMMS_PLANE_TELEMETRY", str(tele))

    # Endpoint uses PROJECT_ROOT for repo_root; plane root/telemetry come from env.
    client = _client()
    response = client.get("/api/comms/v1/plane-status")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "dual_write"
    assert data["enabled"] is True
    assert data["read_only"] is True
    assert data["response_schema_version"] == "comms.v2"
    assert data["store"]["kind"] == "comms-plane"
    assert data["store"]["reachable"] is False
    assert "plane_root" not in data
    assert "db_path" not in data["schema"]
    assert "path" not in data["parity_telemetry"]
    assert data["parity_telemetry"]["exists"] is True
    assert data["parity_telemetry"]["event_count"] == 1
    assert data["schema"]["known_version"] == MIGRATIONS[-1].version


def test_api_plane_status_invalid_mode(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "production")
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "plane"))
    client = _client()
    response = client.get("/api/comms/v1/plane-status")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "invalid"
    assert data["enabled"] is False
    assert data["mode_error"] == "invalid_mode"


def test_comms_v1_collectors_emit_store_not_db_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("scripts.api.comms_router.MESSAGE_DB", tmp_path / "missing.db")
    client = _client()
    for path in ("/api/comms/v1/backlog", "/api/comms/v1/dead-letters", "/api/comms/v1/metrics"):
        response = client.get(path)
        assert response.status_code == 200
        payload = response.json()
        assert payload["response_schema_version"] == "comms.v2"
        assert "store" in payload
        assert payload["store"]["kind"] == "legacy-broker"
        assert "db_path" not in payload


def test_comms_v1_collectors_with_seeded_broker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broker = tmp_path / "messages.db"
    conn = sqlite3.connect(broker)
    conn.executescript(
        """
        CREATE TABLE channel_messages (
          message_id TEXT PRIMARY KEY,
          channel TEXT,
          from_agent TEXT,
          kind TEXT,
          body TEXT,
          created_at TEXT
        );
        CREATE TABLE deliveries (
          delivery_id TEXT PRIMARY KEY,
          message_id TEXT,
          to_agent TEXT,
          to_model TEXT,
          status TEXT,
          dispatched_at TEXT,
          delivered_at TEXT,
          attempt_count INTEGER DEFAULT 0
        );
        """
    )
    conn.close()
    monkeypatch.setattr("scripts.api.comms_router.MESSAGE_DB", broker)
    client = _client()
    backlog = client.get("/api/comms/v1/backlog").json()
    dead = client.get("/api/comms/v1/dead-letters").json()
    metrics = client.get("/api/comms/v1/metrics").json()
    for payload in (backlog, dead, metrics):
        assert payload["response_schema_version"] == "comms.v2"
        assert payload["store"]["kind"] == "legacy-broker"
        assert payload["store"]["reachable"] is True
        assert "db_path" not in payload
