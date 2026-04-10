"""Tests for cost analytics API endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

import scripts.analytics.cost_report as cost_report
from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def _write_meta(root: Path, level: str, slug: str, filename: str, phase: str, prompt_chars: int, response_chars: int) -> None:
    dispatch_dir = root / level / "orchestration" / slug / "dispatch"
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    (dispatch_dir / filename).write_text(
        json.dumps(
            {
                "timestamp": "2026-04-10T12:00:00Z",
                "phase": phase,
                "agent": "codex (gpt-5.4)",
                "model": "gpt-5.4",
                "ok": True,
                "returncode": 0,
                "prompt_chars": prompt_chars,
                "response_chars": response_chars,
                "prompt_tokens_est": cost_report.estimate_tokens(prompt_chars),
                "response_tokens_est": cost_report.estimate_tokens(response_chars),
                "duration_s": 9.0,
            }
        ),
        encoding="utf-8",
    )


def test_cost_summary_empty_payload(tmp_path, monkeypatch):
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", tmp_path)

    response = client.get("/api/analytics/cost")

    assert response.status_code == 200
    payload = response.json()
    assert payload["windows"]["all_time"]["totals"]["cost_usd_est"] == 0.0
    assert payload["windows"]["all_time"]["records_total"] == 0


def test_cost_module_route_returns_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", tmp_path)
    _write_meta(tmp_path, "a1", "my-family", "01-write-meta.json", "write", 3800, 380)

    response = client.get("/api/analytics/cost/module/a1/my-family")

    assert response.status_code == 200
    payload = response.json()
    assert payload["windows"]["all_time"]["records_total"] == 1
    assert payload["windows"]["all_time"]["top_modules"][0]["name"] == "a1/my-family"


def test_cost_phase_route_filters_phase(tmp_path, monkeypatch):
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", tmp_path)
    _write_meta(tmp_path, "a1", "alpha", "01-write-meta.json", "write", 3800, 380)
    _write_meta(tmp_path, "a1", "alpha", "02-review-meta.json", "review", 1900, 190)

    response = client.get("/api/analytics/cost/phase/write")

    assert response.status_code == 200
    payload = response.json()
    assert payload["windows"]["all_time"]["records_total"] == 1
    assert payload["windows"]["all_time"]["per_phase"][0]["name"] == "write"
