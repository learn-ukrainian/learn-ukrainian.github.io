"""Load failures on the cited comms_router sites stay on the response (#8521)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.comms_router import router as comms_router
from scripts.api.monitor_context import fixture_context


@pytest.fixture()
def comms_client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(comms_router, prefix="/api/comms")
    return TestClient(app)


def test_corrupt_pid_file_is_surfaced_and_dead_pid_is_not(
    tmp_path: Path, comms_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    pid_dir = tmp_path / ".mcp" / "servers" / "message-broker" / "pids"
    pid_dir.mkdir(parents=True, exist_ok=True)
    (pid_dir / "broken.json").write_text("{not-json", encoding="utf-8")
    (pid_dir / "dead.json").write_text(json.dumps({"pid": 2**31 - 1}), encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="scripts.api.comms_router"):
        resp = comms_client.get("/api/comms/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["alive_processes"] == 0
    assert any("broken.json" in item for item in body["errors"])
    assert all("dead.json" not in item for item in body["errors"])
    assert any("broken.json" in record.message for record in caplog.records)


def test_corrupt_curriculum_yaml_surfaces_track_error(
    tmp_path: Path, comms_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    curriculum.mkdir(parents=True, exist_ok=True)
    (curriculum / "curriculum.yaml").write_text("levels: [", encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="scripts.api.comms_router"):
        resp = comms_client.get("/api/comms/batch-progress/a1")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_expected"] == 0
    assert any("a1" in item and "curriculum.yaml" in item for item in body["errors"])
    assert any("curriculum.yaml" in record.message for record in caplog.records)
