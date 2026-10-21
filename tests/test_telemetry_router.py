"""Tests for per-tool timing telemetry endpoints."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api.telemetry_router as telemetry_router
from scripts.api.main import app
from scripts.api.monitor_context import fixture_context

client = TestClient(app, raise_server_exceptions=False)


def _bind_fixture_ctx(tmp_path: Path, monkeypatch):
    ctx = fixture_context(tmp_path)
    monkeypatch.setattr(app.state, "ctx", ctx)
    return ctx


def _use_temp_db(tmp_path: Path, monkeypatch) -> Path:
    ctx = _bind_fixture_ctx(tmp_path, monkeypatch)
    return telemetry_router._tool_timings_path(ctx)


def _use_temp_module_db(tmp_path: Path, monkeypatch) -> Path:
    ctx = _bind_fixture_ctx(tmp_path, monkeypatch)
    return telemetry_router._module_build_db_path(ctx)


def test_ingest_valid_payload(tmp_path, monkeypatch):
    db_path = _use_temp_db(tmp_path, monkeypatch)

    response = client.post(
        "/api/telemetry/tool-timings",
        json={
            "ts": "2026-04-25T00:12:34.567Z",
            "tool_name": "Bash",
            "duration_ms": 142,
            "tool_use_id": "toolu_test",
            "session_id": "sess-1",
            "failed": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    with closing(sqlite3.connect(str(db_path))) as conn:
        row = conn.execute("SELECT tool_name, duration_ms, failed FROM tool_timings").fetchone()
    assert row == ("Bash", 142, 0)


def test_module_build_telemetry_ingest_and_readback(tmp_path, monkeypatch):
    db_path = _use_temp_module_db(tmp_path, monkeypatch)

    response = client.post(
        "/api/telemetry/module-builds",
        json={
            "run_id": "b1-m13-pr3148",
            "recorded_at": "2026-06-14T12:00:00Z",
            "level": "B1",
            "slug": "alternation-consonants-verbs",
            "module_title": "Alternation consonants in verbs",
            "branch": "codex/b1-m13-alternation-verbs",
            "commit_sha": "7066d5f506",
            "pr_number": 3148,
            "pr_url": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/3148",
            "status": "merged",
            "swarm_used": True,
            "swarm_label": "thin",
            "swarm_note": "Used bounded reviewers and validation runner.",
            "wall_clock_minutes": 30.5,
            "source": "codex-final",
            "participants": [
                {
                    "role": "main",
                    "agent": "codex",
                    "model": "gpt-5.5",
                    "effort": "xhigh",
                    "label": "integration",
                    "calls": 1,
                    "prompt_tokens": 120000,
                    "response_tokens": 18000,
                    "token_source": "estimated",
                },
                {
                    "role": "helper",
                    "agent": "gemini",
                    "model": "gemini-3.1-pro-preview",
                    "label": "independent review",
                    "total_tokens": 42000,
                    "token_source": "estimated",
                    "cost_usd_est": 0.12,
                },
            ],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True, "run_id": "b1-m13-pr3148"}
    assert db_path.exists()

    response = client.get("/api/telemetry/module-builds?level=b1&slug=alternation-consonants-verbs")

    assert response.status_code == 200
    payload = response.json()
    assert payload["records_total"] == 1
    assert payload["totals"]["swarm_runs"] == 1
    assert payload["totals"]["solo_runs"] == 0
    assert payload["totals"]["participants"] == 2
    assert payload["totals"]["prompt_tokens"] == 120000
    assert payload["totals"]["response_tokens"] == 18000
    assert payload["totals"]["total_tokens"] == 180000
    assert payload["totals"]["cost_usd_est"] == 0.12
    run = payload["runs"][0]
    assert run["level"] == "b1"
    assert run["swarm_used"] is True
    assert run["swarm_note"] == "Used bounded reviewers and validation runner."
    assert run["participants"][0]["total_tokens"] == 138000
    assert run["participants"][1]["total_tokens"] == 42000


def test_module_build_telemetry_upsert_replaces_participants(tmp_path, monkeypatch):
    _use_temp_module_db(tmp_path, monkeypatch)
    base_payload = {
        "run_id": "replace-me",
        "level": "b1",
        "slug": "upsert-demo",
        "swarm_used": False,
        "swarm_label": "none",
        "swarm_note": "solo run; no swarm used",
        "source": "manual",
    }

    response = client.post(
        "/api/telemetry/module-builds",
        json={
            **base_payload,
            "participants": [
                {"role": "main", "agent": "codex", "total_tokens": 100, "token_source": "estimated"}
            ],
        },
    )
    assert response.status_code == 200

    response = client.post(
        "/api/telemetry/module-builds",
        json={
            **base_payload,
            "participants": [
                {"role": "main", "agent": "codex", "total_tokens": 250, "token_source": "actual"}
            ],
        },
    )
    assert response.status_code == 200

    response = client.get("/api/telemetry/module-builds/b1/upsert-demo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["records_total"] == 1
    assert payload["latest"]["participants"] == [
        {
            "role": "main",
            "agent": "codex",
            "model": None,
            "effort": None,
            "label": None,
            "calls": None,
            "prompt_tokens": None,
            "response_tokens": None,
            "total_tokens": 250,
            "token_source": "actual",
            "cost_usd_est": None,
            "notes": None,
        }
    ]
