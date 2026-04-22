"""Unit tests for #1396 — ``--effort`` wiring through delegate → runner → adapters.

Covers:
- ``delegate.py dispatch --effort xhigh`` argparse parses correctly.
- ``_run_worker`` forwards ``effort`` to ``runtime.invoke``.
- ``runner.invoke(effort=...)`` forwards to ``adapter.build_invocation(effort=...)``.
- ClaudeAdapter emits ``--effort <level>`` when the CLI supports it, and
  logs a warning + skips the flag when it does not.
- CodexAdapter emits ``-c model_reasoning_effort=<level>``.
- GeminiAdapter accepts ``effort`` without crashing, logs at DEBUG, and
  does not mutate the command.

Issue: #1396
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate as delegate_mod
from agent_runtime.adapters.claude import ClaudeAdapter
from agent_runtime.adapters.codex import CodexAdapter
from agent_runtime.adapters.gemini import GeminiAdapter
from agent_runtime.usage import _reset_rate_limit_cache_for_tests


@pytest.fixture(autouse=True)
def _isolate_usage_log(tmp_path):
    """Never write to the real batch_state/api_usage/ log during tests."""
    with patch("agent_runtime.usage._usage_dir", return_value=tmp_path / "api_usage"):
        yield


@pytest.fixture(autouse=True)
def _clear_state():
    """Reset runtime in-process caches before every test."""
    _reset_rate_limit_cache_for_tests()
    from agent_runtime import runner

    runner._ADAPTER_CACHE.clear()
    yield
    runner._ADAPTER_CACHE.clear()
    _reset_rate_limit_cache_for_tests()


# ---------------------------------------------------------------------------
# AC5.1 — delegate.py dispatch --effort parses
# ---------------------------------------------------------------------------

def test_delegate_dispatch_parses_effort_flag():
    """``dispatch --effort xhigh ...`` parses to ``args.effort == "xhigh"``."""
    parser = delegate_mod.build_parser()
    args = parser.parse_args([
        "dispatch",
        "--agent", "claude",
        "--task-id", "t1",
        "--prompt", "hi",
        "--effort", "xhigh",
    ])
    assert args.effort == "xhigh"
    assert args.agent == "claude"
    assert args.task_id == "t1"


def test_delegate_dispatch_effort_default_is_none():
    """Omitting --effort leaves args.effort == None (falls through to CLI default)."""
    parser = delegate_mod.build_parser()
    args = parser.parse_args([
        "dispatch",
        "--agent", "claude",
        "--task-id", "t1",
        "--prompt", "hi",
    ])
    assert args.effort is None


def test_delegate_dispatch_rejects_invalid_effort_level():
    """Only the documented choices are accepted."""
    parser = delegate_mod.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([
            "dispatch",
            "--agent", "claude",
            "--task-id", "t1",
            "--prompt", "hi",
            "--effort", "ultra",
        ])


@pytest.mark.parametrize("level", ["low", "medium", "high", "xhigh", "max"])
def test_delegate_dispatch_accepts_all_documented_effort_levels(level):
    parser = delegate_mod.build_parser()
    args = parser.parse_args([
        "dispatch",
        "--agent", "claude",
        "--task-id", f"t-{level}",
        "--prompt", "hi",
        "--effort", level,
    ])
    assert args.effort == level


def test_delegate_worker_parser_accepts_effort():
    """The internal `_worker` subcommand also accepts --effort so the parent
    can propagate the value into the detached child's argv."""
    parser = delegate_mod.build_parser()
    args = parser.parse_args([
        "_worker",
        "--task-id", "t1",
        "--agent", "claude",
        "--mode", "read-only",
        "--cwd", "/tmp",
        "--effort", "xhigh",
    ])
    assert args.effort == "xhigh"


# ---------------------------------------------------------------------------
# AC5.2 — _run_worker forwards effort to runtime.invoke
# ---------------------------------------------------------------------------

def test_run_worker_forwards_effort_to_runtime_invoke(tmp_path):
    """_run_worker must pass effort= straight through to runner.invoke."""
    mock_result = MagicMock(
        ok=True,
        response="ok",
        stderr_excerpt=None,
        returncode=0,
        rate_limited=False,
    )
    # The state file must exist so _run_worker's read returns a dict.
    state_path = delegate_mod._state_path("t-effort")
    delegate_mod._write_state_atomic(state_path, {"task_id": "t-effort"})

    with patch("agent_runtime.runner.invoke", return_value=mock_result) as mock_invoke:
        rc = delegate_mod._run_worker(
            task_id="t-effort",
            agent="claude",
            prompt="hi",
            mode="read-only",
            cwd_str=str(tmp_path),
            model="claude-opus-4-7",
            hard_timeout=60,
            effort="xhigh",
        )

    assert rc == 0
    assert mock_invoke.called, "runner.invoke should have been called"
    kwargs = mock_invoke.call_args.kwargs
    assert kwargs["effort"] == "xhigh", (
        f"_run_worker must forward effort='xhigh'; kwargs={kwargs}"
    )
    assert kwargs["model"] == "claude-opus-4-7"
    assert kwargs["entrypoint"] == "delegate"


def test_run_worker_effort_none_forwards_none(tmp_path):
    """Omitting effort (default None) propagates None — not a string."""
    mock_result = MagicMock(
        ok=True,
        response="ok",
        stderr_excerpt=None,
        returncode=0,
        rate_limited=False,
    )
    state_path = delegate_mod._state_path("t-none")
    delegate_mod._write_state_atomic(state_path, {"task_id": "t-none"})

    with patch("agent_runtime.runner.invoke", return_value=mock_result) as mock_invoke:
        delegate_mod._run_worker(
            task_id="t-none",
            agent="claude",
            prompt="hi",
            mode="read-only",
            cwd_str=str(tmp_path),
            model=None,
            hard_timeout=60,
        )

    assert mock_invoke.call_args.kwargs["effort"] is None


# ---------------------------------------------------------------------------
# AC5.3 — runner.invoke forwards effort to adapter.build_invocation
# ---------------------------------------------------------------------------

def test_runner_invoke_forwards_effort_to_adapter_build_invocation(tmp_path):
    """runner.invoke(..., effort="xhigh") must pass effort="xhigh" into the
    adapter's build_invocation call. Stub has_headroom + Popen so no real
    process runs; assert the adapter spy captured effort."""
    from agent_runtime import runner as runner_mod

    spy_adapter = MagicMock()
    spy_adapter.supported_modes = frozenset({"read-only", "workspace-write", "danger"})
    spy_adapter.default_model = "claude-opus-4-7"
    # Make build_invocation return an InvocationPlan-ish mock.
    fake_plan = MagicMock()
    fake_plan.cmd = ["/bin/true"]
    fake_plan.cwd = tmp_path
    fake_plan.stdin_payload = ""
    fake_plan.env_overrides = {}
    fake_plan.env_unsets = ()
    fake_plan.output_file = None
    fake_plan.liveness_paths = ()
    spy_adapter.build_invocation.return_value = fake_plan
    spy_adapter.liveness_signal_paths.return_value = ()
    # parse_response returns an ok ParseResult-like object.
    spy_parse = MagicMock(
        ok=True,
        response="ok",
        stderr_excerpt=None,
        rate_limited=False,
        session_id=None,
        tokens=None,
    )
    spy_adapter.parse_response.return_value = spy_parse

    fake_proc = MagicMock()
    fake_proc.poll.return_value = 0
    fake_proc.returncode = 0
    fake_proc.stdin = None

    with patch(
        "agent_runtime.runner._load_adapter", return_value=spy_adapter,
    ), patch(
        "agent_runtime.runner.has_headroom", return_value=(True, ""),
    ), patch(
        "agent_runtime.runner.write_record",
    ), patch(
        "agent_runtime.runner.subprocess.Popen", return_value=fake_proc,
    ), patch(
        "agent_runtime.runner.start_watchdog",
        return_value=(MagicMock(stdout_lines=[], stderr_lines=[]), []),
    ), patch(
        "agent_runtime.runner.stop_watchdog",
    ):
        runner_mod.invoke(
            "claude",
            "hi",
            mode="read-only",
            cwd=tmp_path,
            model="claude-opus-4-7",
            effort="xhigh",
            entrypoint="delegate",
        )

    assert spy_adapter.build_invocation.called
    build_kwargs = spy_adapter.build_invocation.call_args.kwargs
    assert build_kwargs["effort"] == "xhigh", (
        f"runner.invoke must forward effort='xhigh' to adapter; "
        f"kwargs={build_kwargs}"
    )


# ---------------------------------------------------------------------------
# AC5.4 — ClaudeAdapter emits --effort when supported
# ---------------------------------------------------------------------------

def test_claude_adapter_emits_effort_when_supported(tmp_path):
    adapter = ClaudeAdapter()
    with patch(
        "utils.claude_version.supports_effort", return_value=True,
    ), patch(
        "utils.claude_version.supports_exclude_dynamic_system_prompt_sections",
        return_value=False,  # keep the OTHER gated flag off so we isolate --effort
    ):
        plan = adapter.build_invocation(
            prompt="hi",
            mode="read-only",
            cwd=tmp_path,
            model="claude-opus-4-7",
            task_id="t",
            session_id=None,
            tool_config=None,
            effort="xhigh",
        )
    assert "--effort" in plan.cmd, f"plan.cmd={plan.cmd}"
    i = plan.cmd.index("--effort")
    assert plan.cmd[i + 1] == "xhigh", (
        f"--effort must be followed by 'xhigh'; got {plan.cmd[i + 1]!r}"
    )


# ---------------------------------------------------------------------------
# AC5.5 — ClaudeAdapter skips + warns when unsupported
# ---------------------------------------------------------------------------

def test_claude_adapter_skips_effort_when_unsupported(tmp_path, caplog):
    adapter = ClaudeAdapter()
    with patch(
        "utils.claude_version.supports_effort", return_value=False,
    ), patch(
        "utils.claude_version.supports_exclude_dynamic_system_prompt_sections",
        return_value=False,
    ), caplog.at_level(logging.WARNING, logger="agent_runtime.adapters.claude"):
        plan = adapter.build_invocation(
            prompt="hi",
            mode="read-only",
            cwd=tmp_path,
            model="claude-opus-4-7",
            task_id="t",
            session_id=None,
            tool_config=None,
            effort="xhigh",
        )
    assert "--effort" not in plan.cmd, (
        f"--effort must be omitted when the CLI does not support it; "
        f"plan.cmd={plan.cmd}"
    )
    assert any(
        "does not support --effort" in rec.message for rec in caplog.records
    ), (
        f"expected a WARNING log about effort being unsupported; "
        f"records={[r.message for r in caplog.records]}"
    )


def test_claude_adapter_no_effort_arg_means_no_flag(tmp_path):
    """Default (effort=None) must NOT emit --effort regardless of version."""
    adapter = ClaudeAdapter()
    with patch(
        "utils.claude_version.supports_effort", return_value=True,
    ):
        plan = adapter.build_invocation(
            prompt="hi",
            mode="read-only",
            cwd=tmp_path,
            model="claude-opus-4-7",
            task_id=None,
            session_id=None,
            tool_config=None,
        )
    assert "--effort" not in plan.cmd


# ---------------------------------------------------------------------------
# AC5.6 — CodexAdapter emits -c model_reasoning_effort=<level>
# ---------------------------------------------------------------------------

def test_codex_adapter_emits_effort_as_config_override(tmp_path):
    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt="hi",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="t",
        session_id=None,
        tool_config=None,
        effort="xhigh",
    )
    # The argv must contain `-c model_reasoning_effort=xhigh` as adjacent tokens.
    assert "-c" in plan.cmd
    flag_pairs = [
        (plan.cmd[i], plan.cmd[i + 1])
        for i in range(len(plan.cmd) - 1)
        if plan.cmd[i] == "-c"
    ]
    assert ("-c", "model_reasoning_effort=xhigh") in flag_pairs, (
        f"expected ('-c', 'model_reasoning_effort=xhigh') in flag pairs; "
        f"plan.cmd={plan.cmd}"
    )


def test_codex_adapter_no_effort_means_no_config_override(tmp_path):
    """effort=None (default) must fall through to ~/.codex/config.toml —
    no -c model_reasoning_effort=... override in the argv."""
    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt="hi",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    joined = " ".join(plan.cmd)
    assert "model_reasoning_effort" not in joined, (
        f"plan.cmd must not contain a model_reasoning_effort override when "
        f"effort is unset; plan.cmd={plan.cmd}"
    )


# ---------------------------------------------------------------------------
# AC5.7 — GeminiAdapter accepts effort, logs debug, no cmd mutation
# ---------------------------------------------------------------------------

def test_gemini_adapter_accepts_effort_without_crashing(tmp_path, caplog):
    adapter = GeminiAdapter()
    with caplog.at_level(logging.DEBUG, logger="agent_runtime.adapters.gemini"):
        plan = adapter.build_invocation(
            prompt="hi",
            mode="read-only",
            cwd=tmp_path,
            model="gemini-3.1-pro-preview",
            task_id=None,
            session_id=None,
            tool_config=None,
            effort="xhigh",
        )
    # No --effort in cmd (gemini-cli doesn't expose one).
    assert "--effort" not in plan.cmd
    assert "xhigh" not in plan.cmd
    # And a DEBUG note referencing the follow-up issue was logged.
    assert any(
        "xhigh" in rec.message and "#1396" in rec.message
        for rec in caplog.records
    ), (
        f"expected a DEBUG log mentioning 'xhigh' and '#1396'; "
        f"records={[r.message for r in caplog.records]}"
    )
