"""Load failures on the cited batch-progress sites stay on the response (#8521).

The comms_router health route (GET /api/comms/health) left with lu-machinery
0.1.31 (machinery #756), and with it the PID-file and broker-DB cases.
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from lu_machinery.api.comms_router import router as comms_router
from lu_machinery.api.monitor_context import fixture_context

from scripts.project_api.batch_progress import router as batch_progress_router

pytestmark = pytest.mark.reads_content


@pytest.fixture()
def comms_client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(batch_progress_router, prefix="/api/comms")
    app.include_router(comms_router, prefix="/api/comms")
    return TestClient(app)


def test_corrupt_curriculum_yaml_surfaces_track_error(
    tmp_path: Path, comms_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    curriculum.mkdir(parents=True, exist_ok=True)
    (curriculum / "curriculum.yaml").write_text("levels: [", encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="scripts.project_api.batch_progress"):
        resp = comms_client.get("/api/comms/batch-progress/a1")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_expected"] == 0
    assert any("a1" in item and "curriculum.yaml" in item for item in body["errors"])
    assert any("curriculum.yaml" in record.message for record in caplog.records)


def test_ps_timeout_is_not_reported_as_zero_processes(
    comms_client: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def _timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["ps", "aux"], timeout=5)

    monkeypatch.setattr("scripts.project_api.batch_progress.subprocess.run", _timeout)

    with caplog.at_level(logging.WARNING, logger="scripts.project_api.batch_progress"):
        resp = comms_client.get("/api/comms/batch-progress")

    assert resp.status_code == 200
    body = resp.json()
    assert body["running_processes"] is None
    assert body["tracks"] == {}
    assert any("ps:" in item and "TimeoutExpired" in item for item in body["errors"])
    assert any("ps" in record.message.lower() for record in caplog.records)


def _old_incomplete_log(tmp_path: Path, name: str = "hist-20260301-0100.log") -> None:
    log_dir = tmp_path / "logs" / "research-preseed"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / name
    log_file.write_text("Processing...\nVERDICT: PASS\n", encoding="utf-8")
    old = time.time() - 1200
    os.utime(log_file, (old, old))


def test_ps_timeout_does_not_mark_old_incomplete_log_dead(
    tmp_path: Path, comms_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _old_incomplete_log(tmp_path)

    def _timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["ps", "aux"], timeout=5)

    monkeypatch.setattr("scripts.project_api.batch_progress.subprocess.run", _timeout)

    resp = comms_client.get("/api/comms/batch-progress")

    assert resp.status_code == 200
    body = resp.json()
    track = body["tracks"]["hist"]
    assert body["running_processes"] is None
    assert track["health"] == "unknown"
    assert track["reason"] == "ps: TimeoutExpired"
    assert "dead" not in {item["health"] for item in body["tracks"].values()}


def test_old_incomplete_log_stays_dead_when_process_probe_succeeds(
    tmp_path: Path, comms_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _old_incomplete_log(tmp_path)

    def _empty_ps(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=["ps", "aux"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr("scripts.project_api.batch_progress.subprocess.run", _empty_ps)

    resp = comms_client.get("/api/comms/batch-progress")

    assert resp.status_code == 200
    body = resp.json()
    assert body["running_processes"] == 0
    assert body["tracks"]["hist"]["health"] == "dead"
    assert "reason" not in body["tracks"]["hist"]
