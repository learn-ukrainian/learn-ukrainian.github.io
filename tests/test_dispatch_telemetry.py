"""Focused tests for dispatch telemetry resolution and persistence."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.base import InvocationPlan
from agent_runtime.runner import invoke
from agent_runtime.telemetry import (
    _reset_version_cache_for_tests,
    resolve_dispatch_start_telemetry,
    resolve_invocation_telemetry,
)
from agent_runtime.usage import _reset_rate_limit_cache_for_tests


def test_resolve_dispatch_start_telemetry_uses_codex_config(tmp_path, monkeypatch):
    home = tmp_path / "home"
    codex_dir = home / ".codex"
    codex_dir.mkdir(parents=True)
    (codex_dir / "config.toml").write_text(
        'model = "gpt-5.5"\nmodel_reasoning_effort = "high"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("agent_runtime.telemetry.Path.home", lambda: home)

    with patch("agent_runtime.telemetry.codex_cli_version", return_value="0.123.0"):
        telemetry = resolve_dispatch_start_telemetry(
            agent_name="codex",
            requested_model=None,
            requested_effort=None,
        )

    assert telemetry.model == "gpt-5.5"
    assert telemetry.effort == "high"
    assert telemetry.cli_version == "0.123.0"


def test_resolve_invocation_telemetry_reads_claude_plan_flags():
    plan = InvocationPlan(
        cmd=[
            "claude",
            "-p",
            "hi",
            "--model",
            "claude-opus-4-6",
            "--effort",
            "xhigh",
        ],
        cwd=Path("."),
    )

    with patch("agent_runtime.telemetry._probe_version", return_value="2.1.89"):
        telemetry = resolve_invocation_telemetry(
            agent_name="claude",
            plan=plan,
            requested_model=None,
            requested_effort=None,
        )

    assert telemetry.model == "claude-opus-4-6"
    assert telemetry.effort == "xhigh"
    assert telemetry.cli_version == "2.1.89"


def test_runner_invoke_returns_resolved_telemetry(tmp_path):
    from agent_runtime import runner as runner_mod

    spy_adapter = MagicMock()
    spy_adapter.supported_modes = frozenset({"read-only", "workspace-write", "danger"})
    spy_adapter.default_model = "gpt-5.4"
    fake_plan = InvocationPlan(
        cmd=["codex", "exec", "-m", "gpt-5.5", "-"],
        cwd=tmp_path,
    )
    spy_adapter.build_invocation.return_value = fake_plan
    spy_adapter.liveness_signal_paths.return_value = ()
    spy_adapter.parse_response.return_value = MagicMock(
        ok=True,
        response="ok",
        stderr_excerpt=None,
        rate_limited=False,
        session_id=None,
        tokens=None,
    )

    fake_proc = MagicMock()
    fake_proc.poll.return_value = 0
    fake_proc.returncode = 0
    fake_proc.stdin = None

    with patch("agent_runtime.runner._load_adapter", return_value=spy_adapter), patch(
        "agent_runtime.runner.has_headroom",
        return_value=(True, ""),
    ), patch("agent_runtime.runner.write_record"), patch(
        "agent_runtime.runner.subprocess.Popen",
        return_value=fake_proc,
    ), patch(
        "agent_runtime.runner.start_watchdog",
        return_value=(MagicMock(stdout_lines=[], stderr_lines=[]), []),
    ), patch("agent_runtime.runner.stop_watchdog"), patch(
        "agent_runtime.runner.resolve_invocation_telemetry",
        return_value=runner_mod.InvocationTelemetry(
            model="gpt-5.5",
            effort="high",
            cli_version="0.123.0",
        ),
    ):
        result = invoke(
            "codex",
            "hi",
            mode="read-only",
            cwd=tmp_path,
            model="gpt-5.4",
            entrypoint="delegate",
        )

    assert result.model == "gpt-5.5"
    assert result.effort == "high"
    assert result.cli_version == "0.123.0"


def setup_function() -> None:
    _reset_rate_limit_cache_for_tests()
    _reset_version_cache_for_tests()


def teardown_function() -> None:
    _reset_rate_limit_cache_for_tests()
    _reset_version_cache_for_tests()
