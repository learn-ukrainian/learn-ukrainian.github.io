"""Tests for the native Kimi K3 runtime lane."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.agent_runtime.adapters.kimi import (
    KIMI_DEFAULT_EFFORT,
    KIMI_DEFAULT_MODEL,
    KimiAdapter,
)
from scripts.agent_runtime.telemetry import resolve_invocation_telemetry
from scripts.agent_runtime.tool_config import build_mcp_tool_config
from scripts.audit.lint_agent_trailer import _TRAILER_RE
from scripts.delegate import build_parser


def _build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    mode: str = "read-only",
    model: str | None = None,
    effort: str | None = None,
):
    binary = tmp_path / "kimi"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    monkeypatch.setenv("LEARN_UK_KIMI_BIN", str(binary))
    return KimiAdapter().build_invocation(
        prompt="Inspect the target.",
        mode=mode,
        cwd=tmp_path,
        model=model,
        task_id="kimi-test",
        session_id=None,
        tool_config=None,
        effort=effort,
    )


@pytest.mark.parametrize(
    ("mode", "expected_flag"),
    [
        ("read-only", None),
        ("workspace-write", "--auto"),
        ("danger", "--yolo"),
    ],
)
def test_build_invocation_maps_permission_modes(tmp_path, monkeypatch, mode, expected_flag):
    plan = _build(tmp_path, monkeypatch, mode=mode)

    assert plan.cmd[0] == str(tmp_path / "kimi")
    assert plan.cmd[plan.cmd.index("-m") + 1] == KIMI_DEFAULT_MODEL
    assert plan.cmd[plan.cmd.index("--output-format") + 1] == "stream-json"
    assert "--plan" not in plan.cmd  # Kimi rejects --prompt + --plan.
    assert (expected_flag in plan.cmd) if expected_flag else not ({"--auto", "--yolo"} & set(plan.cmd))


def test_k3_is_the_only_allowed_model_and_effort_is_max(tmp_path, monkeypatch, caplog):
    with pytest.raises(ValueError, match="unsupported Kimi model"):
        _build(tmp_path, monkeypatch, model="kimi-code/kimi-for-coding")

    caplog.set_level(logging.WARNING)
    plan = _build(tmp_path, monkeypatch, effort="high")
    assert KIMI_DEFAULT_EFFORT == "max"
    assert "max effort only" in caplog.text
    assert "--effort" not in plan.cmd


def test_parse_stream_json_response_session_and_tool_calls(tmp_path):
    events = [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "type": "function",
                    "id": "tool-1",
                    "function": {"name": "Read", "arguments": json.dumps({"path": "AGENTS.md"})},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "tool-1", "content": "# AGENTS.md"},
        {"role": "assistant", "content": "done"},
        {
            "role": "meta",
            "type": "session.resume_hint",
            "session_id": "session-123",
        },
    ]
    parsed = KimiAdapter().parse_response(
        stdout="\n".join(json.dumps(event) for event in events),
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert parsed.ok is True
    assert parsed.response == "done"
    assert parsed.session_id == "session-123"
    assert parsed.tool_calls[0]["name"] == "Read"
    assert parsed.tool_calls[0]["arguments"] == {"path": "AGENTS.md"}
    assert parsed.tool_calls[0]["output_summary"] == "# AGENTS.md"


def test_parse_rate_limit_failure():
    parsed = KimiAdapter().parse_response(
        stdout="",
        stderr="HTTP 429: rate limit exceeded",
        returncode=1,
        output_file=None,
    )
    assert parsed.ok is False
    assert parsed.rate_limited is True
    assert parsed.response == ""


def test_dispatch_parser_and_commit_trailer_accept_kimi():
    args = build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "kimi",
            "--task-id",
            "kimi-smoke",
            "--prompt",
            "probe",
            "--dry-run",
        ]
    )
    assert args.agent == "kimi"
    assert _TRAILER_RE.search("X-Agent: kimi/kimi-smoke")


def test_kimi_mcp_request_fails_closed_without_per_call_selector():
    tool_config, diagnostics = build_mcp_tool_config("kimi", mcp_servers=["sources"])

    assert tool_config is None
    assert diagnostics["resolution_status"] == "servers_not_found"
    assert diagnostics["missing_server_names"] == ["sources"]


def test_invocation_telemetry_reports_k3_max_and_native_cli_version(tmp_path, monkeypatch):
    plan = _build(tmp_path, monkeypatch, effort="medium")
    with patch("scripts.agent_runtime.telemetry.kimi_cli_version", return_value="0.26.0"):
        telemetry = resolve_invocation_telemetry(
            agent_name="kimi",
            plan=plan,
            requested_model=None,
            requested_effort="medium",
        )

    assert telemetry.model == KIMI_DEFAULT_MODEL
    assert telemetry.effort == "max"
    assert telemetry.cli_version == "0.26.0"
