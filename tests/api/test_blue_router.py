"""Tests for Blue API router timeout handling and endpoints."""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from scripts.api import blue_router
from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def _ctx_with_curriculum_root(curriculum_root: Path):
    """Redirect ``ctx.roots.curriculum_root`` for HTTP calls through ``client``.

    ``blue_router`` resolves module paths from MonitorContext (#7330 step 12a),
    so tests swap ``app.state.ctx`` instead of monkeypatching a module Path.
    """
    base = app.state.ctx
    return replace(base, roots=replace(base.roots, curriculum_root=Path(curriculum_root)))


def test_get_audit_status_passes_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    track_dir = tmp_path / "a1"
    track_dir.mkdir(parents=True)
    md_file = track_dir / "01-test.md"
    md_file.write_text("# Test Module\n", encoding="utf-8")
    status_dir = track_dir / "status"
    status_dir.mkdir()
    status_file = status_dir / "01-test.json"
    status_file.write_text(json.dumps({"overall": {"status": "pass"}, "gates": {}}), encoding="utf-8")

    monkeypatch.setattr(app.state, "ctx", _ctx_with_curriculum_root(tmp_path))

    fake = subprocess.CompletedProcess(["audit_module.sh"], 0, "", "")
    with patch("subprocess.run", return_value=fake) as run_mock:
        resp = client.get("/api/blue/audit/a1/01-test?fresh=true")

    assert resp.status_code == 200
    assert run_mock.call_args.kwargs.get("timeout") == blue_router.AUDIT_MODULE_TIMEOUT_SECONDS


def test_get_audit_status_timeout_returns_504(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    track_dir = tmp_path / "a1"
    track_dir.mkdir(parents=True)
    md_file = track_dir / "01-test.md"
    md_file.write_text("# Test Module\n", encoding="utf-8")

    monkeypatch.setattr(app.state, "ctx", _ctx_with_curriculum_root(tmp_path))

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["audit_module.sh"], blue_router.AUDIT_MODULE_TIMEOUT_SECONDS),
    ):
        resp = client.get("/api/blue/audit/a1/01-test?fresh=true")

    assert resp.status_code == 504
    assert "Audit execution timed out after 60.0s" in resp.json()["detail"]
