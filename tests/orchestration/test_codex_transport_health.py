"""Tests for the bounded fresh Codex transport probe."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.orchestration.codex_transport_health import (
    DEGRADED,
    HEALTHY,
    RESERVED_SCHEMA_FAILURE,
    UNKNOWN,
    current_transport_health,
    probe_codex_transport,
)


def _write_config(path: Path, namespace: str = "agents") -> None:
    path.write_text(
        f'[features.multi_agent_v2]\ntool_namespace = "{namespace}"\n',
        encoding="utf-8",
    )


def test_probe_requires_fresh_bridge_response_sentinel(tmp_path):
    config_path = tmp_path / "config.toml"
    receipt_path = tmp_path / "health.json"
    runtime_root = tmp_path / "repo"
    _write_config(config_path)
    observed: dict[str, str | list[str]] = {}

    def runner(command, **kwargs):
        observed["command"] = command
        observed["prompt"] = kwargs["input"]
        return subprocess.CompletedProcess(command, 0, stdout="finished", stderr="")

    def replies(_task_id):
        sentinel = str(observed["prompt"]).rsplit(" ", 1)[-1]
        return [
            {
                "message_type": "response",
                "from_llm": "codex",
                "to_llm": "health-probe",
                "content": sentinel,
            }
        ]

    result = probe_codex_transport(
        receipt_path=receipt_path,
        config_path=config_path,
        runtime_repo_root=runtime_root,
        force_fresh=True,
        command_runner=runner,
        reply_loader=replies,
    )

    assert result["status"] == HEALTHY
    assert result["fresh"] is True
    assert result["failure_class"] is None
    assert "ask-codex" in observed["command"]
    assert "--new-session" in observed["command"]
    stored = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert "prompt" not in stored
    assert "response" not in stored


def test_probe_classifies_reserved_collaboration_schema(tmp_path):
    config_path = tmp_path / "config.toml"
    receipt_path = tmp_path / "health.json"
    _write_config(config_path)
    error = (
        "Invalid Value: 'tools'. Function 'collaboration.spawn_agent' is "
        "reserved for use by this model and must match the configured schema."
    )

    def runner(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, stdout=error, stderr="")

    result = probe_codex_transport(
        receipt_path=receipt_path,
        config_path=config_path,
        runtime_repo_root=tmp_path,
        force_fresh=True,
        command_runner=runner,
        reply_loader=lambda _task_id: [
            {
                "message_type": "error",
                "from_llm": "codex",
                "to_llm": "health-probe",
                "content": error,
            }
        ],
    )

    assert result["status"] == DEGRADED
    assert result["failure_class"] == RESERVED_SCHEMA_FAILURE
    assert error not in receipt_path.read_text(encoding="utf-8")


def test_probe_reuses_fresh_cached_receipt_without_model_call(tmp_path):
    config_path = tmp_path / "config.toml"
    receipt_path = tmp_path / "health.json"
    _write_config(config_path)
    now = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": "codex-transport-health.v1",
                "status": HEALTHY,
                "checked_at": (now - timedelta(seconds=30)).isoformat(),
                "expires_at": (now + timedelta(minutes=10)).isoformat(),
                "model": "gpt-5.6-terra",
                "effort": "low",
                "task_id": "cached",
                "failure_class": None,
                "source": "fresh_bridge_probe",
            }
        ),
        encoding="utf-8",
    )

    def unexpected_runner(*_args, **_kwargs):
        raise AssertionError("fresh process should not launch while receipt is valid")

    result = probe_codex_transport(
        receipt_path=receipt_path,
        config_path=config_path,
        runtime_repo_root=tmp_path,
        now=now,
        command_runner=unexpected_runner,
    )

    assert result["status"] == HEALTHY
    assert result["fresh"] is True
    assert result["age_seconds"] == 30


def test_probe_does_not_reuse_receipt_for_another_model(tmp_path):
    config_path = tmp_path / "config.toml"
    receipt_path = tmp_path / "health.json"
    _write_config(config_path)
    now = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": "codex-transport-health.v1",
                "status": HEALTHY,
                "checked_at": (now - timedelta(seconds=30)).isoformat(),
                "expires_at": (now + timedelta(minutes=10)).isoformat(),
                "model": "gpt-5.6-terra",
                "effort": "low",
                "task_id": "cached-terra",
                "failure_class": None,
                "source": "fresh_bridge_probe",
            }
        ),
        encoding="utf-8",
    )
    observed: dict[str, str] = {}

    def runner(command, **kwargs):
        observed["prompt"] = kwargs["input"]
        return subprocess.CompletedProcess(command, 0, stdout="finished", stderr="")

    def replies(_task_id):
        sentinel = observed["prompt"].rsplit(" ", 1)[-1]
        return [
            {
                "message_type": "response",
                "from_llm": "codex",
                "to_llm": "health-probe",
                "content": sentinel,
            }
        ]

    result = probe_codex_transport(
        receipt_path=receipt_path,
        config_path=config_path,
        runtime_repo_root=tmp_path,
        model="gpt-5.6-sol",
        now=now,
        command_runner=runner,
        reply_loader=replies,
    )

    assert result["status"] == HEALTHY
    assert result["model"] == "gpt-5.6-sol"
    assert "prompt" in observed


def test_stale_receipt_is_unknown(tmp_path):
    config_path = tmp_path / "config.toml"
    receipt_path = tmp_path / "health.json"
    _write_config(config_path)
    now = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": "codex-transport-health.v1",
                "status": HEALTHY,
                "checked_at": (now - timedelta(hours=1)).isoformat(),
                "expires_at": (now - timedelta(minutes=1)).isoformat(),
                "model": "gpt-5.6-terra",
                "effort": "low",
                "task_id": "stale",
                "failure_class": None,
                "source": "fresh_bridge_probe",
            }
        ),
        encoding="utf-8",
    )

    result = current_transport_health(
        receipt_path=receipt_path,
        config_path=config_path,
        now=now,
    )

    assert result["status"] == UNKNOWN
    assert result["fresh"] is False
    assert result["failure_class"] == "stale_probe_receipt"


def test_invalid_namespace_fails_before_launch(tmp_path):
    config_path = tmp_path / "config.toml"
    receipt_path = tmp_path / "health.json"
    _write_config(config_path, namespace="collaboration")

    def unexpected_runner(*_args, **_kwargs):
        raise AssertionError("invalid config must fail before launching Codex")

    result = probe_codex_transport(
        receipt_path=receipt_path,
        config_path=config_path,
        runtime_repo_root=tmp_path,
        force_fresh=True,
        command_runner=unexpected_runner,
    )

    assert result["status"] == DEGRADED
    assert result["failure_class"] == "invalid_tool_namespace"
    assert result["namespace_valid"] is False
