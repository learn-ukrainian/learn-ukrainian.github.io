"""Tests for the native Kimi K3 runtime lane."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.agent_runtime.adapters.kimi import (
    _MODE_FLAGS,
    _READ_ONLY_REFUSAL,
    KIMI_DEFAULT_EFFORT,
    KIMI_DEFAULT_MODEL,
    KIMI_MODEL_ALIASES,
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
    mode: str = "workspace-write",
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


@pytest.mark.parametrize("mode", ["workspace-write", "danger"])
def test_build_invocation_uses_flagless_write_modes(tmp_path, monkeypatch, mode):
    plan = _build(tmp_path, monkeypatch, mode=mode)

    assert plan.cmd[0] == str(tmp_path / "kimi")
    assert plan.cmd[plan.cmd.index("-m") + 1] == KIMI_MODEL_ALIASES[KIMI_DEFAULT_MODEL]
    assert plan.cmd[plan.cmd.index("--output-format") + 1] == "stream-json"
    assert not ({"--auto", "--yolo", "--plan"} & set(plan.cmd))


def test_mode_flag_mapping_is_empty_for_all_headless_modes():
    assert _MODE_FLAGS == {
        "read-only": (),
        "workspace-write": (),
        "danger": (),
    }


def test_read_only_refuses_before_kimi_binary_resolution(tmp_path, monkeypatch):
    with patch("scripts.agent_runtime.adapters.kimi._resolve_kimi_binary") as resolve_binary:
        with pytest.raises(ValueError, match=re.escape(_READ_ONLY_REFUSAL)):
            _build(tmp_path, monkeypatch, mode="read-only")
    resolve_binary.assert_not_called()


def test_short_names_and_full_aliases_resolve_and_unknown_models_reject(tmp_path, monkeypatch):
    for requested, resolved in (
        ("k3", "kimi-code/k3"),
        ("k2.7-coding", "kimi-code/kimi-for-coding"),
        ("k2.7-coding-highspeed", "kimi-code/kimi-for-coding-highspeed"),
        ("kimi-code/k3", "kimi-code/k3"),
    ):
        plan = _build(tmp_path, monkeypatch, model=requested)
        assert plan.cmd[plan.cmd.index("-m") + 1] == resolved

    with pytest.raises(ValueError, match="unsupported Kimi model"):
        _build(tmp_path, monkeypatch, model="k1-classic")


def test_effort_warning_fires_only_for_k3(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    plan = _build(tmp_path, monkeypatch, model="k3", effort="high")
    assert KIMI_DEFAULT_EFFORT == "max"
    assert "max effort only" in caplog.text
    assert "--effort" not in plan.cmd

    caplog.clear()
    plan = _build(tmp_path, monkeypatch, model="k2.7-coding", effort="high")
    assert "max effort only" not in caplog.text
    assert "--effort" not in plan.cmd


def test_empty_stdout_with_rc_zero_fails():
    parsed = KimiAdapter().parse_response(stdout="", stderr="", returncode=0, output_file=None)

    assert parsed.ok is False
    assert parsed.response == ""


def test_nonzero_returncode_fails_even_with_assistant_text():
    stdout = json.dumps({"role": "assistant", "content": "looks fine"})
    parsed = KimiAdapter().parse_response(stdout=stdout, stderr="boom", returncode=1, output_file=None)

    assert parsed.ok is False
    assert parsed.response == ""
    assert "boom" in (parsed.stderr_excerpt or "")


def test_non_assistant_event_stream_is_never_promoted_to_success():
    """Silent-error-as-content guard: tool/status-only streams must fail."""
    stdout = "\n".join(
        [
            json.dumps({"role": "tool", "name": "Read", "content": "raw dump"}),
            json.dumps({"role": "meta", "type": "status", "state": "working"}),
        ]
    )
    parsed = KimiAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None)

    assert parsed.ok is False
    assert parsed.response == ""


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


def test_invocation_telemetry_is_model_aware_and_reports_native_cli_version(tmp_path, monkeypatch):
    k3_plan = _build(tmp_path, monkeypatch, model="k3", effort="medium")
    with patch("scripts.agent_runtime.telemetry.kimi_cli_version", return_value="0.26.0"):
        k3_telemetry = resolve_invocation_telemetry(
            agent_name="kimi",
            plan=k3_plan,
            requested_model=None,
            requested_effort="medium",
        )

    assert k3_telemetry.model == "kimi-code/k3"
    assert k3_telemetry.effort == "max"  # K3 is always-max; caller request never mislabeled
    assert k3_telemetry.cli_version == "0.26.0"

    coding_plan = _build(tmp_path, monkeypatch, effort="medium")  # default: k2.7-coding
    with patch("scripts.agent_runtime.telemetry.kimi_cli_version", return_value="0.26.0"):
        coding_telemetry = resolve_invocation_telemetry(
            agent_name="kimi",
            plan=coding_plan,
            requested_model=None,
            requested_effort="medium",
        )

    assert coding_telemetry.model == KIMI_MODEL_ALIASES[KIMI_DEFAULT_MODEL]
    assert coding_telemetry.effort == "not-exposed"  # k2.7 models have no effort knob
