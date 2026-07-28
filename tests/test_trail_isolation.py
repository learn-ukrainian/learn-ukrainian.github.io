"""Conformance tests for the P5 weak-driver TrailSpec tool boundary."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime import trail_isolation
from agent_runtime.adapters import grok_build
from agent_runtime.adapters.glm import GlmAdapter
from agent_runtime.adapters.grok_build import GrokBuildAdapter
from agent_runtime.adapters.kimi import KimiAdapter
from agent_runtime.adapters.kimicc import KimiccHarness
from agent_runtime.runner import invoke
from agent_runtime.trail_isolation import TrailIsolationError, prepare_trail_isolation

from scripts.orchestration.trails import trail_mcp

FAKE_GROK = "/usr/local/bin/grok"
FAKE_CLAUDE = "/usr/local/bin/claude"


def _values_after(cmd: list[str], flag: str) -> list[str]:
    return [cmd[index + 1] for index, value in enumerate(cmd[:-1]) if value == flag]


def _prepared_profile(agent_name: str, **tool_config: object):
    return prepare_trail_isolation(
        agent_name=agent_name,
        mode="read-only",
        tool_config={"trail_isolation": True, **tool_config},
    )


def test_mcp_server_exposes_only_three_fixed_tools() -> None:
    tools = asyncio.run(trail_mcp.mcp.list_tools())

    assert [tool.name for tool in tools] == ["trail_status", "trail_step", "trail_summon"]


def test_mcp_tools_only_call_fixed_p3_runner_verbs() -> None:
    payload = {
        "schema_version": "trail-run-result.v1",
        "command": "status",
        "exit_class": 0,
        "outcome": "status",
        "run_id": "run-123",
        "state": "active",
        "cursor_step": "check",
        "data": {"summons": []},
        "error": None,
    }
    completed = subprocess.CompletedProcess([], 0, stdout=json.dumps(payload), stderr="")
    with patch("scripts.orchestration.trails.trail_mcp.subprocess.run", return_value=completed) as run:
        assert trail_mcp.trail_status("run-123") == payload
        assert trail_mcp.trail_step("run-123", "check") == payload
        assert trail_mcp.trail_summon("run-123") == payload

    calls = [call.args[0] for call in run.call_args_list]
    assert calls[0][-3:] == ["status", "--run-id", "run-123"]
    assert calls[1][-5:] == ["step", "--run-id", "run-123", "--expected-step", "check"]
    # Summons are P3-owned records exposed by status, never a local mutation.
    assert calls[2][-3:] == ["status", "--run-id", "run-123"]
    assert all(call[:2] == [str(trail_mcp.PYTHON_BIN), str(trail_mcp.TRAIL_RUNNER)] for call in calls)


def test_grok_profile_has_one_private_server_and_exact_allowlist() -> None:
    launch = _prepared_profile("grok")
    assert launch is not None
    try:
        config_path = launch.root / ".mcp.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        assert set(config["mcpServers"]) == {"trail"}
        assert config["mcpServers"]["trail"]["command"] == str(
            trail_isolation.PROJECT_ROOT / ".venv" / "bin" / "python"
        )
        assert launch.tool_config["allowed_tools"].split(",") == list(trail_isolation.GROK_TRAIL_TOOLS)

        with patch("agent_runtime.adapters.grok_build.shutil.which", return_value=FAKE_GROK):
            plan = GrokBuildAdapter().build_invocation(
                prompt="Run the trail.",
                mode="read-only",
                cwd=Path.cwd(),
                model=None,
                task_id="p5-test",
                session_id=None,
                tool_config=launch.tool_config,
            )

        assert plan.cwd == launch.root
        assert _values_after(plan.cmd, "--tools") == [launch.tool_config["allowed_tools"]]
        assert _values_after(plan.cmd, "--allow") == list(trail_isolation.GROK_TRAIL_TOOLS)
        denied = _values_after(plan.cmd, "--deny")
        assert "Bash" in denied
        assert {"Write", "Edit", "MultiEdit", "NotebookEdit"} <= set(denied)
        assert "mcp__unknown__mutation" not in launch.tool_config["allowed_tools"]
        assert plan.cmd[plan.cmd.index("--permission-mode") + 1] == "default"
    finally:
        launch.cleanup()
    assert not launch.root.exists()


def test_grok_deny_check_is_mutation_honest() -> None:
    launch = _prepared_profile("grok")
    assert launch is not None
    try:
        with patch("agent_runtime.adapters.grok_build.shutil.which", return_value=FAKE_GROK):
            with patch.object(
                grok_build,
                "GROK_TRAIL_DENY_TOOLS",
                tuple(rule for rule in trail_isolation.GROK_TRAIL_DENY_TOOLS if rule != "Bash"),
            ):
                mutated = GrokBuildAdapter().build_invocation(
                    prompt="Run the trail.",
                    mode="read-only",
                    cwd=Path.cwd(),
                    model=None,
                    task_id="p5-mutant",
                    session_id=None,
                    tool_config=launch.tool_config,
                )
        # This proves the preceding conformance assertion would reject a
        # regression that dropped the Bash deny rule.
        assert "Bash" not in _values_after(mutated.cmd, "--deny")
    finally:
        launch.cleanup()


def test_grok_profile_refuses_conflicting_or_unknown_tool_config() -> None:
    launch = _prepared_profile("grok")
    assert launch is not None
    try:
        for extra in ({"review_isolation": True}, {"disallowed_tools": "Bash"}):
            with pytest.raises(TrailIsolationError, match="incompatible tool_config"):
                GrokBuildAdapter().build_invocation(
                    prompt="Run the trail.",
                    mode="read-only",
                    cwd=Path.cwd(),
                    model=None,
                    task_id="p5-conflict",
                    session_id=None,
                    tool_config={**launch.tool_config, **extra},
                )
    finally:
        launch.cleanup()


def test_kimicc_profile_forwards_strict_three_tool_admission() -> None:
    launch = _prepared_profile("kimi", harness="kimicc")
    assert launch is not None
    try:
        with (
            patch("agent_runtime.adapters.kimicc._default_claude_bin", return_value=FAKE_CLAUDE),
            patch("agent_runtime.adapters.kimicc._ensure_supported_claude_cli_version"),
        ):
            plan = KimiccHarness().build_invocation(
                prompt="Run the trail.",
                mode="read-only",
                cwd=Path.cwd(),
                model=None,
                task_id="p5-test",
                session_id=None,
                tool_config=launch.tool_config,
            )

        assert _values_after(plan.cmd, "--tools") == [launch.tool_config["tools"]]
        assert _values_after(plan.cmd, "--allowedTools") == [launch.tool_config["allowed_tools"]]
        assert "--strict-mcp-config" in plan.cmd
        assert _values_after(plan.cmd, "--setting-sources") == [""]
        assert _values_after(plan.cmd, "--mcp-config") == [launch.tool_config["mcp_config_path"]]
        assert "Bash" not in launch.tool_config["tools"]
        assert "Write" not in launch.tool_config["tools"]
    finally:
        launch.cleanup()


def test_kimicc_profile_refuses_conflicting_or_unknown_tool_config() -> None:
    launch = _prepared_profile("kimi", harness="kimicc")
    assert launch is not None
    try:
        for extra in ({"agent": "untrusted"}, {"max_budget_usd": 1}):
            with pytest.raises(TrailIsolationError, match="incompatible tool_config"):
                KimiccHarness().build_invocation(
                    prompt="Run the trail.",
                    mode="read-only",
                    cwd=Path.cwd(),
                    model=None,
                    task_id="p5-conflict",
                    session_id=None,
                    tool_config={**launch.tool_config, **extra},
                )
    finally:
        launch.cleanup()


def test_kimicc_wrapper_accepts_the_strict_trail_flags(tmp_path: Path) -> None:
    launch = _prepared_profile("kimi", harness="kimicc")
    assert launch is not None
    try:
        fake_claude = tmp_path / "claude"
        fake_claude.write_text(
            "#!/usr/bin/env bash\nprintf 'arg=%s\\n' \"$@\"\n",
            encoding="utf-8",
        )
        fake_claude.chmod(0o755)
        home = tmp_path / "home"
        home.mkdir()
        env = os.environ.copy()
        env.update({"HOME": str(home), "KIMICC_CLAUDE_BIN": str(fake_claude), "KIMICC_AUTH_TOKEN": "test"})
        result = subprocess.run(
            [
                str(trail_isolation.PROJECT_ROOT / "scripts/agent_runtime/kimicc_headless.sh"),
                "--model",
                "k3",
                "--mode",
                "read-only",
                "--prompt",
                "Run the trail.",
                "--mcp-config",
                str(launch.tool_config["mcp_config_path"]),
                "--allowedTools",
                str(launch.tool_config["allowed_tools"]),
                "--tools",
                str(launch.tool_config["tools"]),
                "--strict-mcp-config",
                "--setting-sources",
                "",
            ],
            cwd=trail_isolation.PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )

        assert result.returncode == 0, result.stderr
        assert f"arg={launch.tool_config['tools']}" in result.stdout
        assert "arg=--strict-mcp-config" in result.stdout
        assert "arg=--setting-sources" in result.stdout
    finally:
        launch.cleanup()


@pytest.mark.parametrize("adapter", ["glm", "grok-hermes", "claude"])
def test_unproven_adapters_refuse_before_runner_loads_them(adapter: str) -> None:
    with patch("agent_runtime.runner._load_adapter", side_effect=AssertionError("spawn attempted")):
        with pytest.raises(TrailIsolationError, match="trail isolation refused"):
            invoke(adapter, "Run the trail.", tool_config={"trail_isolation": True})


def test_glm_and_native_kimi_refuse_the_profile_at_adapter_boundary(tmp_path: Path) -> None:
    with pytest.raises(TrailIsolationError, match="GLM"):
        GlmAdapter().build_invocation(
            prompt="Run the trail.",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config={"trail_isolation": True},
        )
    with pytest.raises(TrailIsolationError, match="native Kimi"):
        KimiAdapter().build_invocation(
            prompt="Run the trail.",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config={"trail_isolation": True},
        )


def test_trail_isolation_rejects_write_modes_and_caller_tool_injection() -> None:
    launch = prepare_trail_isolation(
        agent_name="grok",
        mode="read-only",
        tool_config={"trail_isolation": {}},
    )
    assert launch is not None
    launch.cleanup()
    with pytest.raises(TrailIsolationError, match="mode='read-only'"):
        prepare_trail_isolation(
            agent_name="grok",
            mode="workspace-write",
            tool_config={"trail_isolation": True},
        )
    with pytest.raises(TrailIsolationError, match="caller-supplied tool configuration"):
        prepare_trail_isolation(
            agent_name="grok",
            mode="read-only",
            tool_config={"trail_isolation": True, "allowed_tools": "Bash"},
        )
