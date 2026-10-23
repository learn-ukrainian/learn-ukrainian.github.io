"""Tests for batch_router endpoints and websocket."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api import batch_router as batch_router_mod
from scripts.api.batch_router import DISPATCHER_SCAN_TIMEOUT_S
from scripts.api.batch_router import router as batch_router
from scripts.api.monitor_context import fixture_context


@pytest.fixture()
def batch_client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(batch_router)
    return TestClient(app)


def test_corrupt_checkpoint_json_surfaces_track_error(
    tmp_path: Path, batch_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    state_dir = tmp_path / "batch_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "checkpoint_a1.json").write_text("{not-json", encoding="utf-8")
    (state_dir / "checkpoint_b1.json").write_text(json.dumps({"cp": 2}), encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="scripts.api.batch_router"):
        resp = batch_client.get("/api/batch/checkpoints")

    assert resp.status_code == 200
    body = resp.json()
    assert body["b1"] == {"cp": 2}
    assert any("a1" in item and "checkpoint_a1.json" in item for item in body["errors"])
    assert any("checkpoint_a1.json" in record.message for record in caplog.records)


def test_dispatcher_scan_timeout_returns_degraded_response(
    tmp_path: Path, batch_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The fixture checkout is not this process's repo. The scan must resolve
    # that checkout's interpreter, not inherit sys.executable.
    interpreter = tmp_path / ".venv" / "bin" / "python"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text("", encoding="utf-8")

    def _timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["scan"], timeout=DISPATCHER_SCAN_TIMEOUT_S)

    monkeypatch.setattr(batch_router_mod.subprocess, "run", _timeout)
    resp = batch_client.post("/api/batch/dispatcher/scan")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["errors"]


def test_batch_websocket_heartbeat(batch_client: TestClient) -> None:
    with batch_client.websocket_connect("/ws/batch") as ws:
        data = ws.receive_json()
        assert data == {"type": "heartbeat"}
