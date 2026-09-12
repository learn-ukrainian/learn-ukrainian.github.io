"""Tests for batch_router endpoints and websocket."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.batch_router import router as batch_router
from scripts.api.monitor_context import fixture_context


@pytest.fixture()
def batch_client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(batch_router)
    return TestClient(app)


def test_dispatcher_state_empty_and_populated(tmp_path: Path, batch_client: TestClient) -> None:
    resp = batch_client.get("/api/batch/dispatcher")
    assert resp.status_code == 200
    assert resp.json() == {"tracks": {}}

    state_file = tmp_path / "batch_state" / "dispatcher_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps({"tracks": {"hist": {"status": "ok"}}}), encoding="utf-8")

    resp = batch_client.get("/api/batch/dispatcher")
    assert resp.status_code == 200
    assert resp.json() == {"tracks": {"hist": {"status": "ok"}}}


def test_active_orchestration_empty(batch_client: TestClient) -> None:
    resp = batch_client.get("/api/batch/active")
    assert resp.status_code == 200
    assert resp.json() == []


def test_failure_queue_empty_and_populated(tmp_path: Path, batch_client: TestClient) -> None:
    resp = batch_client.get("/api/batch/failures")
    assert resp.status_code == 200
    assert resp.json() == []

    f_file = tmp_path / "batch_state" / "failure_queue.json"
    f_file.parent.mkdir(parents=True, exist_ok=True)
    f_file.write_text(json.dumps([{"module": "a1/test"}]), encoding="utf-8")

    resp = batch_client.get("/api/batch/failures")
    assert resp.status_code == 200
    assert resp.json() == [{"module": "a1/test"}]


def test_batch_usage_empty_and_populated(tmp_path: Path, batch_client: TestClient) -> None:
    resp = batch_client.get("/api/batch/usage")
    assert resp.status_code == 200
    assert resp.json() == {}

    usage_dir = tmp_path / "batch_state" / "api_usage"
    usage_dir.mkdir(parents=True, exist_ok=True)
    (usage_dir / "summary_a1.json").write_text(json.dumps({"tokens": 100}), encoding="utf-8")

    resp = batch_client.get("/api/batch/usage")
    assert resp.status_code == 200
    assert resp.json() == {"a1": {"tokens": 100}}


def test_batch_checkpoints_empty_and_populated(tmp_path: Path, batch_client: TestClient) -> None:
    resp = batch_client.get("/api/batch/checkpoints")
    assert resp.status_code == 200
    assert resp.json() == {}

    state_dir = tmp_path / "batch_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "checkpoint_a1.json").write_text(json.dumps({"cp": 1}), encoding="utf-8")

    resp = batch_client.get("/api/batch/checkpoints")
    assert resp.status_code == 200
    assert resp.json() == {"a1": {"cp": 1}}


def test_dispatcher_running(batch_client: TestClient) -> None:
    resp = batch_client.get("/api/batch/dispatcher/running")
    assert resp.status_code == 200
    assert resp.json() == {"running": False}


def test_dispatcher_logs_empty_and_populated(tmp_path: Path, batch_client: TestClient) -> None:
    resp = batch_client.get("/api/batch/dispatcher/logs")
    assert resp.status_code == 200
    assert resp.json() == {"lines": []}

    log_file = tmp_path / "logs" / "dispatcher.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("line1\nline2\nline3\n", encoding="utf-8")

    resp = batch_client.get("/api/batch/dispatcher/logs?lines=2")
    assert resp.status_code == 200
    assert resp.json() == {"lines": ["line2", "line3"]}


def test_batch_websocket_heartbeat(batch_client: TestClient) -> None:
    with batch_client.websocket_connect("/ws/batch") as ws:
        data = ws.receive_json()
        assert data == {"type": "heartbeat"}
