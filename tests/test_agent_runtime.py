"""Unit tests for scripts/agent_runtime/ — runner + CodexAdapter + support layers.

Covers:
- Adapter loading from registry
- Mode validation and cwd requirement for write modes
- Resume policy enforcement (Codex "never", Claude/Gemini "bridge_only")
- CodexAdapter flag building for each mode
- CodexAdapter parse_response for ok/error/rate-limited cases
- Usage record building and writing
- Watchdog state + should_kill logic

Does NOT cover:
- Real subprocess invocation (that's an integration test, separate file)
- ClaudeAdapter / GeminiAdapter (not implemented yet)

Issue: #1184
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.codex import CodexAdapter
from agent_runtime.errors import (
    AgentUnavailableError,
    RateLimitedError,
)
from agent_runtime.registry import AGENTS, get_agent_entry
from agent_runtime.runner import _enforce_resume_policy, _load_adapter, invoke
from agent_runtime.usage import _reset_rate_limit_cache_for_tests
from agent_runtime.watchdog import WatchdogState, should_kill


@pytest.fixture(autouse=True)
def _clear_state():
    """Reset runtime in-process caches before every test."""
    _reset_rate_limit_cache_for_tests()
    # Clear adapter cache by reaching into runner module
    from agent_runtime import runner
    runner._ADAPTER_CACHE.clear()
    yield
    runner._ADAPTER_CACHE.clear()
    _reset_rate_limit_cache_for_tests()


# ---------------------------------------------------------------------------
# Registry + adapter loading
# ---------------------------------------------------------------------------

def test_registry_has_four_agents():
    assert set(AGENTS.keys()) == {"codex", "claude", "gemini", "grok"}


def test_codex_entry_has_never_resume_policy():
    assert get_agent_entry("codex")["resume_policy"] == "never"


def test_claude_entry_has_bridge_only_resume_policy():
    assert get_agent_entry("claude")["resume_policy"] == "bridge_only"


def test_load_adapter_codex():
    adapter = _load_adapter("codex")
    assert adapter.name == "codex"
    assert adapter.default_model == "gpt-5.4"
    assert adapter.supported_modes == frozenset({"read-only", "workspace-write", "danger"})


def test_load_adapter_unknown_raises():
    with pytest.raises(AgentUnavailableError, match="not in the registry"):
        _load_adapter("nonexistent")


def test_load_adapter_grok_stub_unavailable():
    with pytest.raises(AgentUnavailableError, match="cli_available=False"):
        _load_adapter("grok")


def test_load_adapter_cached():
    first = _load_adapter("codex")
    second = _load_adapter("codex")
    assert first is second


# ---------------------------------------------------------------------------
# Resume policy enforcement
# ---------------------------------------------------------------------------

def test_resume_policy_never_rejects_session_id():
    with pytest.raises(ValueError, match="resume_policy='never'"):
        _enforce_resume_policy("codex", session_id="some-uuid", entrypoint="bridge")


def test_resume_policy_never_allows_none():
    # No error when session_id is None
    _enforce_resume_policy("codex", session_id=None, entrypoint="bridge")


def test_resume_policy_bridge_only_allows_bridge():
    _enforce_resume_policy("claude", session_id="uuid", entrypoint="bridge")


def test_resume_policy_bridge_only_rejects_dispatch():
    with pytest.raises(ValueError, match="bridge_only"):
        _enforce_resume_policy("claude", session_id="uuid", entrypoint="dispatch")


def test_resume_policy_bridge_only_rejects_delegate():
    with pytest.raises(ValueError, match="bridge_only"):
        _enforce_resume_policy("gemini", session_id="uuid", entrypoint="delegate")


# ---------------------------------------------------------------------------
# CodexAdapter — flag building per mode
# ---------------------------------------------------------------------------

def test_codex_adapter_mode_flags_read_only():
    assert CodexAdapter._mode_flags("read-only") == ["-s", "read-only"]


def test_codex_adapter_mode_flags_workspace_write():
    assert CodexAdapter._mode_flags("workspace-write") == ["--full-auto"]


def test_codex_adapter_mode_flags_danger():
    assert CodexAdapter._mode_flags("danger") == [
        "--dangerously-bypass-approvals-and-sandbox"
    ]


def test_codex_adapter_build_invocation_read_only(tmp_path):
    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="test-task",
        session_id=None,
        tool_config=None,
    )
    assert plan.cmd[1] == "exec"
    assert "-s" in plan.cmd
    assert "read-only" in plan.cmd
    assert "-C" in plan.cmd
    assert str(tmp_path) in plan.cmd
    assert plan.cmd[-1] == "-"  # stdin marker
    assert plan.stdin_payload == "hello"
    assert plan.output_file is not None
    assert "test-task" in plan.output_file.name
    # Liveness paths should include the output file
    assert plan.output_file in plan.liveness_paths


def test_codex_adapter_build_invocation_ignores_session_id(tmp_path):
    """Defensive: Codex adapter MUST ignore session_id even when passed."""
    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id="should-be-ignored-uuid",
        tool_config=None,
    )
    # No --resume flag anywhere in the command
    assert "--resume" not in plan.cmd
    # No "resume" subcommand
    assert "resume" not in plan.cmd


def test_codex_adapter_build_invocation_workspace_write(tmp_path):
    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="workspace-write",
        cwd=tmp_path,
        model="gpt-5.4-mini",
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert "--full-auto" in plan.cmd
    assert "gpt-5.4-mini" in plan.cmd  # model override honored


# ---------------------------------------------------------------------------
# CodexAdapter — parse_response
# ---------------------------------------------------------------------------

def test_codex_parse_response_success(tmp_path):
    adapter = CodexAdapter()
    output_file = tmp_path / "output.txt"
    output_file.write_text("Hello from Codex")

    result = adapter.parse_response(
        stdout="session id: abc12345\nsome progress output",
        stderr="",
        returncode=0,
        output_file=output_file,
    )
    assert result.ok is True
    assert result.response == "Hello from Codex"
    assert result.rate_limited is False
    assert result.session_id == "abc12345"
    assert result.stderr_excerpt is None


def test_codex_parse_response_rate_limited(tmp_path):
    adapter = CodexAdapter()
    output_file = tmp_path / "output.txt"
    output_file.write_text("partial output")

    result = adapter.parse_response(
        stdout="",
        stderr="Error: usage limit reached. Try again later.",
        returncode=1,
        output_file=output_file,
    )
    assert result.ok is False
    assert result.rate_limited is True
    assert "usage limit" in (result.stderr_excerpt or "").lower()


def test_codex_parse_response_error(tmp_path):
    adapter = CodexAdapter()
    output_file = tmp_path / "output.txt"
    # Output file exists but empty
    output_file.write_text("")

    result = adapter.parse_response(
        stdout="",
        stderr="Error: something broke",
        returncode=2,
        output_file=output_file,
    )
    assert result.ok is False
    assert result.rate_limited is False
    assert result.response == ""
    assert "something broke" in (result.stderr_excerpt or "")


def test_codex_parse_response_missing_output_file():
    adapter = CodexAdapter()
    result = adapter.parse_response(
        stdout="",
        stderr="fatal error",
        returncode=1,
        output_file=Path("/nonexistent/path.txt"),
    )
    assert result.ok is False
    assert result.response == ""


def test_codex_parse_response_rate_limit_in_file(tmp_path):
    """Rate-limit pattern in the output file should be detected, not just stderr."""
    adapter = CodexAdapter()
    output_file = tmp_path / "output.txt"
    output_file.write_text("Error: quota exceeded")

    result = adapter.parse_response(
        stdout="",
        stderr="",
        returncode=1,
        output_file=output_file,
    )
    assert result.rate_limited is True


def test_codex_parse_response_rate_limit_url_no_false_positive(tmp_path):
    """The pattern '\\b429\\b' should not match '/issues/4290'."""
    adapter = CodexAdapter()
    output_file = tmp_path / "output.txt"
    output_file.write_text("see github.com/issues/4290 for details")

    result = adapter.parse_response(
        stdout="",
        stderr="",
        returncode=0,
        output_file=output_file,
    )
    assert result.rate_limited is False
    assert result.ok is True


# ---------------------------------------------------------------------------
# invoke() — high-level runner
# ---------------------------------------------------------------------------

def test_invoke_rejects_unsupported_mode(tmp_path):
    with pytest.raises(ValueError, match="does not support mode"):
        invoke("codex", "hello", mode="invalid-mode", cwd=tmp_path)


def test_invoke_requires_cwd_for_write_mode():
    with pytest.raises(ValueError, match="cwd is mandatory"):
        invoke("codex", "hello", mode="workspace-write", cwd=None)


def test_invoke_requires_cwd_for_danger_mode():
    with pytest.raises(ValueError, match="cwd is mandatory"):
        invoke("codex", "hello", mode="danger", cwd=None)


def test_invoke_codex_rejects_session_id(tmp_path):
    with pytest.raises(ValueError, match="resume_policy='never'"):
        invoke(
            "codex",
            "hello",
            mode="read-only",
            cwd=tmp_path,
            session_id="some-uuid",
        )


def test_invoke_rate_limit_short_circuit(tmp_path):
    """If has_headroom returns False, invoke raises RateLimitedError
    without spawning a subprocess."""
    # Patch write_record to prevent the short-circuit path from writing
    # rate_limited records to the REAL batch_state/api_usage/ directory
    # during test runs (would poison has_headroom for subsequent real calls).
    with patch(
        "agent_runtime.runner.has_headroom",
        return_value=(False, "cached rate limit"),
    ), patch(
        "agent_runtime.runner.write_record",
    ), patch(
        "agent_runtime.runner.subprocess.Popen",
    ) as mock_popen, pytest.raises(RateLimitedError, match="cached rate limit"):
        invoke("codex", "hello", mode="read-only", cwd=tmp_path)
    mock_popen.assert_not_called()


# ---------------------------------------------------------------------------
# Watchdog
# ---------------------------------------------------------------------------

def test_should_kill_returns_none_when_healthy():
    now = time.monotonic()
    state = WatchdogState(start_time=now, last_activity=now)
    # Fresh start, fresh activity → no kill
    assert should_kill(state, stall_timeout=180, hard_timeout=1800) is None


def test_should_kill_detects_stall():
    now = time.monotonic()
    state = WatchdogState(start_time=now - 60, last_activity=now - 200)
    # Active 200s ago, threshold 180s → stalled
    assert should_kill(state, stall_timeout=180, hard_timeout=1800) == "stalled"


def test_should_kill_detects_hard_timeout():
    now = time.monotonic()
    state = WatchdogState(start_time=now - 2000, last_activity=now)
    # Started 2000s ago, hard_timeout 1800s → hard_timeout
    assert should_kill(state, stall_timeout=180, hard_timeout=1800) == "hard_timeout"


def test_should_kill_hard_timeout_takes_precedence():
    """If both conditions fire, hard_timeout wins (checked first)."""
    now = time.monotonic()
    state = WatchdogState(start_time=now - 2000, last_activity=now - 500)
    # Both conditions true — but hard_timeout is reported first
    assert should_kill(state, stall_timeout=180, hard_timeout=1800) == "hard_timeout"
