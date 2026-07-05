from __future__ import annotations

import json

from fastapi.testclient import TestClient

from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_hermes_cron_router_returns_404_when_missing(tmp_path, monkeypatch):
    from scripts.api import hermes_cron_router
    monkeypatch.setattr(hermes_cron_router, "PROJECT_ROOT", tmp_path)

    # Request JSON
    resp_json = client.get("/api/hermes-cron/latest")
    assert resp_json.status_code == 404
    assert resp_json.json()["detail"] == "Latest nightly audit json report not found"

    # Request markdown
    resp_md = client.get("/api/hermes-cron/latest?format=markdown")
    assert resp_md.status_code == 404
    assert resp_md.json()["detail"] == "Latest nightly audit markdown report not found"


def test_hermes_cron_router_returns_correct_content(tmp_path, monkeypatch):
    from scripts.api import hermes_cron_router
    monkeypatch.setattr(hermes_cron_router, "PROJECT_ROOT", tmp_path)

    # Write fake reports to tmp_path/batch_state/hermes_cron/
    cron_dir = tmp_path / "batch_state" / "hermes_cron"
    cron_dir.mkdir(parents=True)

    fake_json = {
        "timestamp": "2026-07-05T19:33:21Z",
        "summary": {"findings_total": 0},
        "tracks": {},
        "insights": "mocked",
    }
    (cron_dir / "latest.json").write_text(json.dumps(fake_json), encoding="utf-8")

    fake_md = "# Hermes Nightly Audit Report\nNo findings."
    (cron_dir / "latest.md").write_text(fake_md, encoding="utf-8")

    # Request JSON (default)
    resp_json = client.get("/api/hermes-cron/latest")
    assert resp_json.status_code == 200
    assert resp_json.json() == fake_json

    # Request markdown
    resp_md = client.get("/api/hermes-cron/latest?format=markdown")
    assert resp_md.status_code == 200
    assert resp_md.headers["content-type"] == "text/markdown; charset=utf-8"
    assert resp_md.text == fake_md
