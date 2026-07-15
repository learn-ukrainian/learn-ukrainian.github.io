from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from agent_runtime.adapters.base import InvocationPlan
from agent_runtime.adapters.hermes_grok import HermesGrokAdapter
from agent_runtime.errors import AgentTimeoutError, AgentUnavailableError
from agent_runtime.runner import invoke
from agent_runtime.usage import _reset_rate_limit_cache_for_tests


@pytest.fixture(autouse=True)
def _isolate_runtime(tmp_path):
    _reset_rate_limit_cache_for_tests()
    with patch("agent_runtime.usage._usage_dir", return_value=tmp_path / "api_usage"):
        yield
    _reset_rate_limit_cache_for_tests()


def _build(prompt: str, tmp_path: Path):
    return HermesGrokAdapter().build_invocation(
        prompt=prompt,
        mode="workspace-write",
        cwd=tmp_path,
        model="grok-4.5",
        task_id=None,
        session_id=None,
        tool_config={"hermes_mcp_servers": ["sources"]},
        effort="medium",
    )


def test_grok_adapter_invokes_hermes_z_with_correct_argv(tmp_path, monkeypatch):
    monkeypatch.setattr("agent_runtime.adapters.hermes_grok.shutil.which", lambda _: "hermes")

    plan = _build("Write the module.", tmp_path)

    assert plan.cmd == ["hermes", "-z", "Write the module.", "-m", "grok-4.5"]
    assert plan.cwd == tmp_path
    assert plan.stdin_payload == ""


def test_grok_adapter_returns_stdout_as_response():
    result = HermesGrokAdapter().parse_response(
        stdout="hello from grok",
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is True
    assert result.response == "hello from grok"


def test_grok_adapter_tool_calls_total_is_none_not_zero():
    result = HermesGrokAdapter().parse_response(
        stdout="hello",
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.tool_calls == []
    assert result.tool_calls_total is None


def test_grok_adapter_handles_missing_hermes_binary(tmp_path):
    with (
        patch("agent_runtime.runner.has_headroom", return_value=(True, "")),
        patch("agent_runtime.runner.write_record"),
        patch(
            "agent_runtime.runner.subprocess.Popen",
            side_effect=FileNotFoundError("hermes"),
        ),
        pytest.raises(AgentUnavailableError, match="Popen failed: FileNotFoundError"),
    ):
        invoke(
            "grok",
            "hello",
            mode="workspace-write",
            cwd=tmp_path,
            model="grok-4.5",
            entrypoint="dispatch",
            effort="medium",
        )


def test_grok_adapter_honors_timeout(tmp_path, monkeypatch):
    adapter = HermesGrokAdapter()

    def fake_build_invocation(**kwargs):
        return InvocationPlan(cmd=["/bin/sh", "-c", "sleep 5"], cwd=Path(kwargs["cwd"]))

    monkeypatch.setattr(adapter, "build_invocation", fake_build_invocation)
    monkeypatch.setattr("agent_runtime.runner._load_adapter", lambda _name: adapter)

    with (
        patch("agent_runtime.runner.has_headroom", return_value=(True, "")),
        patch("agent_runtime.runner.write_record"),
        pytest.raises(AgentTimeoutError),
    ):
        invoke(
            "grok",
            "hello",
            mode="workspace-write",
            cwd=tmp_path,
            model="grok-4.5",
            entrypoint="dispatch",
            hard_timeout=1,
        )


def test_grok_adapter_strips_ansi_codes_from_stdout():
    result = HermesGrokAdapter().parse_response(
        stdout="\x1b[32mhello\x1b[0m",
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.response == "hello"


def test_runner_preserves_unknown_grok_tool_call_total(tmp_path, monkeypatch):
    adapter = HermesGrokAdapter()

    def fake_build_invocation(**kwargs):
        return InvocationPlan(cmd=["/bin/sh", "-c", "printf hello"], cwd=Path(kwargs["cwd"]))

    monkeypatch.setattr(adapter, "build_invocation", fake_build_invocation)
    monkeypatch.setattr("agent_runtime.runner._load_adapter", lambda _name: adapter)

    with (
        patch("agent_runtime.runner.has_headroom", return_value=(True, "")),
        patch("agent_runtime.runner.write_record"),
    ):
        result = invoke(
            "grok",
            "hello",
            mode="workspace-write",
            cwd=tmp_path,
            model="grok-4.5",
            entrypoint="dispatch",
            effort="medium",
        )

    assert result.response == "hello"
    assert result.tool_calls == []
    assert result.tool_calls_total is None
