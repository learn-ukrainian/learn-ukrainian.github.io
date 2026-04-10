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

from agent_runtime.adapters.claude import ClaudeAdapter
from agent_runtime.adapters.codex import CodexAdapter
from agent_runtime.adapters.gemini import GeminiAdapter
from agent_runtime.errors import (
    AgentUnavailableError,
    RateLimitedError,
)
from agent_runtime.registry import AGENTS, get_agent_entry
from agent_runtime.runner import _enforce_resume_policy, _load_adapter, invoke
from agent_runtime.usage import _reset_rate_limit_cache_for_tests
from agent_runtime.watchdog import WatchdogState, should_kill


@pytest.fixture(autouse=True)
def _isolate_usage_log(tmp_path):
    """Ensure no test writes to the real batch_state/api_usage/ log."""
    with patch("agent_runtime.usage._usage_dir", return_value=tmp_path / "api_usage"):
        yield

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


# ---------------------------------------------------------------------------
# GeminiAdapter
# ---------------------------------------------------------------------------

def test_gemini_adapter_attributes():
    adapter = GeminiAdapter()
    assert adapter.name == "gemini"
    assert "read-only" in adapter.supported_modes
    assert "workspace-write" in adapter.supported_modes
    assert "danger" in adapter.supported_modes


def test_gemini_adapter_read_only_no_yolo(tmp_path):
    adapter = GeminiAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert "--approval-mode=yolo" not in plan.cmd
    assert "-m" in plan.cmd
    assert plan.stdin_payload == "hello"
    assert plan.output_file is None  # Gemini uses stdout, no -o file
    assert plan.liveness_paths == ()


def test_gemini_adapter_workspace_write_yolo(tmp_path):
    adapter = GeminiAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="workspace-write",
        cwd=tmp_path,
        model="gemini-3.1-pro-preview",
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert "--approval-mode=yolo" in plan.cmd


def test_gemini_adapter_mcp_tool_config(tmp_path):
    """The #1 consultation finding: tool_config for MCP restrictions must
    survive through the protocol."""
    adapter = GeminiAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"mcp_server_names": ["rag"]},
    )
    assert "--allowed-mcp-server-names" in plan.cmd
    idx = plan.cmd.index("--allowed-mcp-server-names")
    assert plan.cmd[idx + 1] == "rag"


def test_gemini_adapter_mcp_tool_config_multiple(tmp_path):
    adapter = GeminiAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"mcp_server_names": ["rag", "other", "third"]},
    )
    assert "rag,other,third" in plan.cmd


def test_gemini_adapter_ignores_unknown_tool_config_keys(tmp_path):
    """Forward compatibility: adapters silently ignore tool_config keys
    they don't understand."""
    adapter = GeminiAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={
            "mcp_server_names": ["rag"],
            "some_future_field": "value",
            "another_future_field": {"nested": True},
        },
    )
    assert "--allowed-mcp-server-names" in plan.cmd
    # Unknown keys do not appear anywhere in the command
    cmd_str = " ".join(plan.cmd)
    assert "some_future_field" not in cmd_str
    assert "another_future_field" not in cmd_str


def test_gemini_adapter_ignores_session_id(tmp_path):
    """Gemini CLI has no --resume equivalent; session_id must be silently dropped."""
    adapter = GeminiAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id="some-uuid",
        tool_config=None,
    )
    assert "--resume" not in plan.cmd
    assert "some-uuid" not in " ".join(plan.cmd)


def test_gemini_parse_response_success():
    adapter = GeminiAdapter()
    result = adapter.parse_response(
        stdout="Hello from Gemini\n",
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is True
    assert result.response == "Hello from Gemini"
    assert result.rate_limited is False
    assert result.session_id is None
    assert result.tokens is None


def test_gemini_parse_response_rate_limit_resource_exhausted():
    adapter = GeminiAdapter()
    result = adapter.parse_response(
        stdout="",
        stderr="Error: RESOURCE_EXHAUSTED",
        returncode=1,
        output_file=None,
    )
    assert result.ok is False
    assert result.rate_limited is True


def test_gemini_parse_response_rate_limit_quota_exceeded():
    adapter = GeminiAdapter()
    result = adapter.parse_response(
        stdout="",
        stderr="quota exceeded for project xyz",
        returncode=1,
        output_file=None,
    )
    assert result.rate_limited is True


def test_gemini_parse_response_rate_limit_in_stdout():
    """Some Gemini rate-limit messages land in stdout, not stderr."""
    adapter = GeminiAdapter()
    result = adapter.parse_response(
        stdout="Error: quota exceeded",
        stderr="",
        returncode=1,
        output_file=None,
    )
    assert result.rate_limited is True


def test_gemini_parse_response_url_no_false_positive():
    """\\b429\\b must not match URL path components."""
    adapter = GeminiAdapter()
    result = adapter.parse_response(
        stdout="See https://example.com/issues/4290 for details",
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is True
    assert result.rate_limited is False


def test_gemini_parse_response_error_with_empty_stderr():
    """Falls back to stdout for excerpt when stderr is empty."""
    adapter = GeminiAdapter()
    result = adapter.parse_response(
        stdout="unexpected error: model timed out",
        stderr="",
        returncode=2,
        output_file=None,
    )
    assert result.ok is False
    assert "timed out" in (result.stderr_excerpt or "")


def test_gemini_liveness_paths_from_project_tmp(tmp_path, monkeypatch):
    """Gemini adapter returns ~/.gemini/tmp/<cwd-basename>/ paths when they exist.

    Updated 2026-04-10: the adapter USED to return () and rely entirely
    on the stdout streamer. That turned out to be a false assumption —
    the gemini CLI block-buffers stdout when not a TTY and can stay
    silent for 5+ minutes during reasoning bursts, causing spurious
    stalls. It DOES write to ~/.gemini/tmp/<project>/logs.json and
    chats/ during exec, so we now watch those files via mtime polling.

    Further updated: the adapter now reads cwd from plan.cwd rather than
    os.getcwd(), so the test no longer needs monkeypatch.chdir().
    """
    adapter = GeminiAdapter()

    # Fake $HOME so Path.home() resolves inside the test sandbox.
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    # cwd basename drives the lookup; create a matching gemini state dir.
    project_cwd = tmp_path / "learn-ukrainian"
    project_cwd.mkdir()

    gemini_dir = fake_home / ".gemini" / "tmp" / "learn-ukrainian"
    (gemini_dir / "chats").mkdir(parents=True)
    (gemini_dir / "logs.json").write_text("{}")
    (gemini_dir / "chats" / "session-2026-04-10T17-35-abc.json").write_text("{}")

    plan = adapter.build_invocation(
        prompt="x",
        mode="read-only",
        cwd=project_cwd,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    paths = adapter.liveness_signal_paths(plan)
    names = {p.name for p in paths}
    assert "logs.json" in names
    assert "chats" in names
    assert any(n.startswith("session-") for n in names)


def test_gemini_liveness_paths_missing_dir_returns_empty(tmp_path, monkeypatch):
    """If ~/.gemini/tmp/<basename>/ doesn't exist, return () gracefully."""
    adapter = GeminiAdapter()
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    # cwd basename with no corresponding gemini project dir
    empty_cwd = tmp_path / "no-such-project-xyz"
    empty_cwd.mkdir()

    plan = adapter.build_invocation(
        prompt="x",
        mode="read-only",
        cwd=empty_cwd,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert adapter.liveness_signal_paths(plan) == ()


# ---------------------------------------------------------------------------
# ClaudeAdapter
# ---------------------------------------------------------------------------

def test_claude_adapter_attributes():
    adapter = ClaudeAdapter()
    assert adapter.name == "claude"
    assert adapter.supported_modes == frozenset({"read-only", "workspace-write", "danger"})


def test_claude_adapter_basic_stateless(tmp_path):
    adapter = ClaudeAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert "-p" in plan.cmd
    assert "hello" in plan.cmd
    assert "--resume" not in plan.cmd
    assert "--session-id" not in plan.cmd
    assert "--output-format" in plan.cmd
    assert plan.stdin_payload == ""  # Claude -p takes prompt as positional


def test_claude_adapter_resume_existing_session(tmp_path):
    adapter = ClaudeAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="test",
        session_id="abc-123",
        tool_config=None,  # default is_new_session=False → resume
    )
    assert "--resume" in plan.cmd
    assert "abc-123" in plan.cmd
    assert "--session-id" not in plan.cmd
    assert "--bare" not in plan.cmd  # --bare is incompatible with resume


def test_claude_adapter_new_named_session(tmp_path):
    adapter = ClaudeAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="test",
        session_id="new-uuid-123",
        tool_config={"is_new_session": True},
    )
    assert "--session-id" in plan.cmd
    assert "new-uuid-123" in plan.cmd
    assert "--resume" not in plan.cmd


def test_claude_adapter_mcp_tool_config(tmp_path):
    """The #1 consultation finding for Claude too: tool_config for MCP
    restrictions must flow through the protocol."""
    adapter = ClaudeAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={
            "mcp_config_path": "/path/.mcp.json",
            "allowed_tools": "Read,Grep,mcp__rag__verify_word",
        },
    )
    assert "--mcp-config" in plan.cmd
    assert "/path/.mcp.json" in plan.cmd
    assert "--allowedTools" in plan.cmd
    assert "Read,Grep,mcp__rag__verify_word" in plan.cmd


def test_claude_adapter_danger_mode(tmp_path):
    adapter = ClaudeAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="danger",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert "--dangerously-skip-permissions" in plan.cmd


def test_claude_adapter_model_override(tmp_path):
    adapter = ClaudeAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model="claude-sonnet-4-5",
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert "--model" in plan.cmd
    assert "claude-sonnet-4-5" in plan.cmd


def test_claude_adapter_bare_when_api_key_set(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake")
    adapter = ClaudeAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert "--bare" in plan.cmd


def test_claude_adapter_no_bare_when_session_id_passed(tmp_path, monkeypatch):
    """--bare is incompatible with resumed or named sessions."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake")
    adapter = ClaudeAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="test",
        session_id="abc-123",
        tool_config=None,
    )
    assert "--bare" not in plan.cmd
    assert "--resume" in plan.cmd


def test_claude_parse_response_success():
    adapter = ClaudeAdapter()
    result = adapter.parse_response(
        stdout="Claude's response text.",
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is True
    assert result.response == "Claude's response text."
    assert result.rate_limited is False


def test_claude_parse_response_rate_limit():
    adapter = ClaudeAdapter()
    result = adapter.parse_response(
        stdout="",
        stderr="Error: rate limit reached, try again later",
        returncode=1,
        output_file=None,
    )
    assert result.rate_limited is True


def test_claude_parse_response_url_no_false_positive():
    adapter = ClaudeAdapter()
    result = adapter.parse_response(
        stdout="See docs/issues/4290 for details",
        stderr="",
        returncode=0,
        output_file=None,
    )
    assert result.ok is True
    assert result.rate_limited is False
