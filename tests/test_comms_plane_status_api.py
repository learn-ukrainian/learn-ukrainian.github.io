"""Monitor API plane-status surface (read-only; Sol PR-K-ish / #5512)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.fleet_comms.message_plane import read_plane_status
from scripts.fleet_comms.migrations import apply_migrations


def _client() -> TestClient:
    from scripts.api.comms_router import router

    app = FastAPI()
    app.include_router(router, prefix="/api/comms")
    return TestClient(app)


def test_read_plane_status_defaults_to_configured_mode(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("FLEET_COMMS_MESSAGE_PLANE", raising=False)
    monkeypatch.delenv("FLEET_COMMS_ROOT", raising=False)
    monkeypatch.delenv("FLEET_COMMS_PLANE_TELEMETRY", raising=False)
    status = read_plane_status(repo_root=tmp_path)
    # Config default is shadow (Gate A finish); env still wins when set.
    assert status["mode"] == "shadow"
    assert status["enabled"] is True
    assert status["read_only"] is True
    assert status["schema"]["known_version"] == 2
    assert status["schema"]["applied_version"] is None
    assert status["schema"]["db_exists"] is False
    assert status["parity_telemetry"]["exists"] is False
    assert status["parity_telemetry"]["event_count"] == 0


def test_read_plane_status_with_schema_and_telemetry(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "fleet-comms" / "v1"
    root.mkdir(parents=True)
    db_path = root / "comms.sqlite3"
    conn = sqlite3.connect(str(db_path))
    try:
        applied = apply_migrations(conn)
        assert applied == 2
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
    assert status["schema"]["applied_version"] == 2
    assert status["schema"]["applied_name"] == "fleet-comms-v2-sealed-verdict-artifact"
    assert status["parity_telemetry"]["exists"] is True
    assert status["parity_telemetry"]["event_count"] == 3
    assert status["parity_telemetry"]["parity_ok_count"] == 1
    assert status["parity_telemetry"]["parity_fail_count"] == 1
    assert len(status["parity_telemetry"]["recent"]) == 3


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
    assert data["plane_root"] == str(tmp_path / "plane")
    assert data["parity_telemetry"]["exists"] is True
    assert data["parity_telemetry"]["event_count"] == 1
    assert data["schema"]["known_version"] == 2


def test_api_plane_status_invalid_mode(monkeypatch) -> None:
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "production")
    client = _client()
    response = client.get("/api/comms/v1/plane-status")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "invalid"
    assert data["enabled"] is False
    assert data["mode_error"] == "invalid_mode"
