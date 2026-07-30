"""Tests for runtime monitor API endpoints."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

import scripts.api.runtime_router as runtime_router
from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _write_usage_file(path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def test_agents_endpoint_returns_known_adapters():
    response = client.get("/api/runtime/agents")

    assert response.status_code == 200
    agents = response.json()["agents"]
    names = {agent["name"] for agent in agents}
    assert {"claude", "gemini", "codex"} <= names
    assert not any(name.startswith("acpx-") for name in names)
    codex = next(agent for agent in agents if agent["name"] == "codex")
    assert codex["binary"] == "codex"
    assert codex["default_model"] == "gpt-5.6-terra"


def test_usage_aggregates_by_agent(tmp_path, monkeypatch):
    usage_dir = tmp_path / "api_usage"
    today = datetime.now(UTC)
    monkeypatch.setattr(runtime_router, "USAGE_DIR", usage_dir)

    _write_usage_file(
        usage_dir / f"usage_codex-dispatch_{today:%Y-%m-%d}.jsonl",
        [
            {
                "ts": _iso(today - timedelta(minutes=4)),
                "agent": "codex",
                "entrypoint": "dispatch",
                "model": "gpt-5.5",
                "duration_s": 10.5,
                "outcome": "ok",
            },
            {
                "ts": _iso(today - timedelta(minutes=3)),
                "agent": "codex",
                "entrypoint": "dispatch",
                "model": "gpt-5.5",
                "duration_s": 4.0,
                "outcome": "error",
            },
        ],
    )
    _write_usage_file(
        usage_dir / f"usage_gemini-bridge_{today:%Y-%m-%d}.jsonl",
        [
            {
                "ts": _iso(today - timedelta(minutes=2)),
                "agent": "gemini",
                "entrypoint": "bridge",
                "model": "gemini-3.1-pro-preview",
                "duration_s": 8.0,
                "outcome": "rate_limited",
            }
        ],
    )

    response = client.get("/api/runtime/usage?days=7")

    assert response.status_code == 200
    data = response.json()
    assert data["records_total"] == 3
    assert data["by_agent"]["codex"]["total"] == 2
    assert data["by_agent"]["codex"]["ok"] == 1
    assert data["by_agent"]["codex"]["error"] == 1
    assert data["by_agent"]["codex"]["total_duration_s"] == 14.5
    assert data["by_entrypoint"]["bridge"]["rate_limited"] == 1


def test_acpx_overview_is_read_only_and_aggregates_hyphenated_seats(
    tmp_path,
    monkeypatch,
):
    usage_dir = tmp_path / "api_usage"
    today = datetime.now(UTC)
    monkeypatch.setattr(runtime_router, "USAGE_DIR", usage_dir)
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "shadow")

    _write_usage_file(
        usage_dir / f"usage_acpx-grok-shadow-runner_{today:%Y-%m-%d}.jsonl",
        [
            {
                "ts": _iso(today - timedelta(minutes=2)),
                "agent": "acpx-grok-shadow",
                "entrypoint": "runner",
                "model": "grok-4.5",
                "duration_s": 6.25,
                "outcome": "ok",
                "task_id": "must-not-leak",
                "cwd": "/private/must-not-leak",
                "stderr_excerpt": "must-not-leak",
                "provider_session_id": "must-not-leak",
            }
        ],
    )

    response = client.get("/api/runtime/acpx?days=7")

    assert response.status_code == 200
    data = response.json()
    assert data["transport"] == {
        "mode": "shadow",
        "scope": "monitor_process",
        "default_mode": "off",
        "authority": "native_runtime",
        "posture": "evidence_only",
        "writable": False,
    }
    assert data["pins"] == {
        "acpx": "0.13.0",
        "grok_cli": "0.2.114",
        "validation": "before_spawn",
    }
    assert data["safety"]["max_in_flight"] == 1
    assert data["safety"]["chat"] is False
    assert data["safety"]["mutations"] is False

    seats = {seat["name"]: seat for seat in data["seats"]}
    assert seats["acpx-codex-shadow"]["evidence_state"] == "no_evidence"
    assert seats["acpx-codex-shadow"]["evidence"]["total"] == 0
    assert seats["acpx-grok-shadow"]["evidence_state"] == "observed"
    assert seats["acpx-grok-shadow"]["evidence"]["ok"] == 1
    assert seats["acpx-grok-shadow"]["evidence"]["total_duration_s"] == 6.25

    serialized = response.text
    for private_field in (
        "task_id",
        "cwd",
        "stderr_excerpt",
        "provider_session_id",
        "must-not-leak",
    ):
        assert private_field not in serialized


def test_acpx_overview_sanitizes_unrecognized_transport_mode(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(runtime_router, "USAGE_DIR", tmp_path / "missing")
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "secret-looking-invalid-value")

    response = client.get("/api/runtime/acpx")

    assert response.status_code == 200
    data = response.json()
    assert data["transport"]["mode"] == "invalid"
    assert "secret-looking-invalid-value" not in response.text


def test_headroom_rejects_missing_params():
    response = client.get("/api/runtime/headroom")

    assert response.status_code == 400
    assert "required" in response.json()["detail"]


def test_recent_limits_results(tmp_path, monkeypatch):
    usage_dir = tmp_path / "api_usage"
    now = datetime.now(UTC)
    monkeypatch.setattr(runtime_router, "USAGE_DIR", usage_dir)
    _write_usage_file(
        usage_dir / f"usage_codex-dispatch_{now:%Y-%m-%d}.jsonl",
        [
            {
                "ts": _iso(now - timedelta(minutes=3)),
                "agent": "codex",
                "entrypoint": "dispatch",
                "model": "gpt-5.5",
                "outcome": "ok",
                "duration_s": 9.0,
            },
            {
                "ts": _iso(now - timedelta(minutes=1)),
                "agent": "codex",
                "entrypoint": "dispatch",
                "model": "gpt-5.5",
                "outcome": "timeout",
                "duration_s": 12.0,
            },
            {
                "ts": _iso(now - timedelta(minutes=2)),
                "agent": "gemini",
                "entrypoint": "bridge",
                "model": "gemini-3.1-pro-preview",
                "outcome": "ok",
                "duration_s": 5.0,
            },
        ],
    )

    response = client.get("/api/runtime/recent?limit=2")

    assert response.status_code == 200
    records = response.json()["records"]
    assert len(records) == 2
    assert records[0]["outcome"] == "timeout"
    assert records[1]["agent"] == "gemini"


def test_transport_health_returns_sanitized_cached_probe(tmp_path, monkeypatch):
    receipt_path = tmp_path / "codex-transport-health.json"
    config_path = tmp_path / "config.toml"
    now = datetime.now(UTC)
    config_path.write_text(
        "[features.multi_agent_v2]\ntool_namespace = \"agents\"\n",
        encoding="utf-8",
    )
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": "codex-transport-health.v1",
                "status": "healthy",
                "checked_at": _iso(now - timedelta(seconds=5)),
                "expires_at": _iso(now + timedelta(minutes=10)),
                "model": "gpt-5.6-terra",
                "effort": "low",
                "task_id": "codex-transport-probe-test",
                "failure_class": None,
                "source": "fresh_bridge_probe",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(runtime_router, "CODEX_TRANSPORT_RECEIPT_PATH", receipt_path)
    monkeypatch.setattr(runtime_router, "CODEX_TRANSPORT_CONFIG_PATH", config_path)

    response = client.get("/api/runtime/transport-health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["fresh"] is True
    assert data["namespace_valid"] is True
    assert data["tool_namespace"] == "agents"
    assert "task_id" not in data
    assert "content" not in data


def test_transport_health_is_unknown_without_probe_receipt(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[features.multi_agent_v2]\ntool_namespace = \"agents\"\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runtime_router,
        "CODEX_TRANSPORT_RECEIPT_PATH",
        tmp_path / "missing.json",
    )
    monkeypatch.setattr(runtime_router, "CODEX_TRANSPORT_CONFIG_PATH", config_path)

    response = client.get("/api/runtime/transport-health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unknown"
    assert data["fresh"] is False
    assert data["failure_class"] == "no_probe_receipt"
