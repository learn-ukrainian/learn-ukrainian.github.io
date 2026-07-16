"""Unit tests for the native managed-seat Kimi runtime adapter."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from agent_runtime.adapters.base import AgentAdapter
from agent_runtime.adapters.kimi import (
    KIMI_DEFAULT_MODEL,
    KIMI_MODEL_ALIASES,
    KimiAdapter,
    resolve_kimi_code_bin,
)


def _plan(tmp_path: Path, *, mode: str = "read-only", model: str | None = None):
    return KimiAdapter().build_invocation(
        prompt="Review this change.", mode=mode, cwd=tmp_path, model=model,
        task_id="kimi-test", session_id="must-not-resume", tool_config={"ignored": True},
    )


def _value(cmd: list[str], flag: str) -> str:
    return cmd[cmd.index(flag) + 1]


def test_read_only_plan_uses_native_headless_stream_json_without_auto_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("KIMI_CODE_BIN", "/opt/kimi")
    plan = _plan(tmp_path)

    assert plan.cmd[0] == "/opt/kimi"
    assert _value(plan.cmd, "-p") == "Review this change."
    assert _value(plan.cmd, "-m") == KIMI_MODEL_ALIASES[KIMI_DEFAULT_MODEL]
    assert _value(plan.cmd, "--output-format") == "stream-json"
    assert "-y" not in plan.cmd
    assert "--auto" not in plan.cmd


def test_workspace_write_also_never_auto_approves_actions(tmp_path):
    plan = _plan(tmp_path, mode="workspace-write")

    assert "-y" not in plan.cmd
    assert "--auto" not in plan.cmd


def test_danger_plan_adds_yolo_and_no_auto_alias(tmp_path):
    plan = _plan(tmp_path, mode="danger")

    assert "-y" in plan.cmd
    assert "--auto" not in plan.cmd


@pytest.mark.parametrize("short_name, cli_alias", KIMI_MODEL_ALIASES.items())
def test_model_short_names_map_to_known_cli_aliases(tmp_path, short_name, cli_alias):
    assert _value(_plan(tmp_path, model=short_name).cmd, "-m") == cli_alias


def test_unknown_model_is_rejected_loudly(tmp_path):
    with pytest.raises(ValueError, match="unsupported Kimi model"):
        _plan(tmp_path, model="unregistered-kimi-model")


def test_binary_override_and_default_resolution(monkeypatch):
    monkeypatch.setenv("KIMI_CODE_BIN", "/tmp/kimi-test-bin")
    assert resolve_kimi_code_bin() == "/tmp/kimi-test-bin"
    monkeypatch.delenv("KIMI_CODE_BIN")
    assert resolve_kimi_code_bin().endswith("/.kimi-code/bin/kimi")


def test_stream_json_response_prefers_terminal_result_and_extracts_tool_calls():
    stdout = "\n".join(
        [
            json.dumps({"type": "delta", "delta": {"text": "partial "}}),
            json.dumps({"type": "result", "result": "final response"}),
            json.dumps({"type": "tool_call", "name": "Read", "arguments": {"path": "x"}}),
        ]
    )

    result = KimiAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None)

    assert result.ok is True
    assert result.response == "final response"
    assert result.tool_calls[0]["name"] == "Read"


def test_unknown_mode_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="unsupported mode"):
        _plan(tmp_path, mode="invalid")


def test_conforms_to_adapter_protocol():
    assert isinstance(KimiAdapter(), AgentAdapter)
