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
from agent_runtime.watchdog import (
    WatchdogState,
    should_kill,
    start_watchdog,
    stop_watchdog,
    tail_liveness_file_for_debug,
)


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


def test_codex_liveness_paths_pick_newest_rollout(tmp_path, monkeypatch):
    """Regression: Codex 0.118 stores the live rollout in
    sessions/YYYY/MM/DD/rollout-*.jsonl inside the directory. The
    directory mtime only bumps on child creation, so directory-only
    polling misses content writes. The adapter must return the NEWEST
    rollout file directly (same pattern as Gemini's newest session-*.json).

    Tonight (2026-04-10) we watched our own watchdog about to kill a
    successfully-running Codex process because the dir-only signal had
    gone silent while the rollout file was still growing at 409KB.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    # Build today's sessions dir structure
    from datetime import UTC, datetime
    today = datetime.now(UTC)
    sessions_today = (
        fake_home / ".codex" / "sessions"
        / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
    )
    sessions_today.mkdir(parents=True)

    # Two rollout files, different ages. The newer one must be chosen.
    old_rollout = sessions_today / "rollout-2026-04-10T18-00-00-aaa.jsonl"
    old_rollout.write_text('{"old": true}\n')
    import os as _os
    _os.utime(old_rollout, (old_rollout.stat().st_mtime - 300,
                             old_rollout.stat().st_mtime - 300))
    new_rollout = sessions_today / "rollout-2026-04-10T20-53-00-bbb.jsonl"
    new_rollout.write_text('{"new": true}\n')

    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt="x",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="test",
        session_id=None,
        tool_config=None,
    )
    paths = adapter.liveness_signal_paths(plan)
    names = {p.name for p in paths}
    assert new_rollout.name in names, (
        f"newest rollout-*.jsonl missing from liveness paths: {names}"
    )
    assert old_rollout.name not in names, (
        f"older rollout file should not be in liveness paths: {names}"
    )


def test_codex_parse_response_failed_call_with_prompt_echo_not_rate_limit(tmp_path):
    """Regression: a KILLED or FAILED Codex call whose prompt contained
    rate-limit phrases must not be misclassified as rate-limited. Only
    genuine error output (outside the echoed prompt block) should count.

    The specific incident: we sent Codex a consultation prompt literally
    asking about rate-limit handling. I killed the process mid-run. The
    adapter saw returncode != 0 + empty output file + pattern hit in
    echoed prompt and reported rate_limited=True, poisoning has_headroom.
    """
    adapter = CodexAdapter()
    output_file = tmp_path / "output.txt"
    output_file.write_text("")  # empty — call failed

    # Realistic stderr: banner, echoed prompt containing rate-limit
    # phrases (because the user's prompt was ABOUT rate limits), then
    # a real error that is NOT a rate limit (e.g. killed by signal).
    stderr = (
        "OpenAI Codex v0.118.0 (research preview)\n"
        "--------\n"
        "workdir: /Users/foo/project\n"
        "model: gpt-5.4\n"
        "--------\n"
        "user\n"
        "Please review our rate-limit handling. We had a usage limit reached\n"
        "incident where transient 429 errors locked the quota for 5 hours.\n"
        "What would you do about rate limit detection?\n"
        "--------\n"
        "error: terminated by signal\n"
    )

    result = adapter.parse_response(
        stdout="",
        stderr=stderr,
        returncode=-15,  # SIGTERM
        output_file=output_file,
    )
    # Call failed (no output file content), but the rate-limit phrases
    # were ONLY in the echoed user prompt. Must not classify as rate-limited.
    assert result.rate_limited is False, (
        f"Killed Codex call with rate-limit phrases in echoed prompt was "
        f"misclassified as rate-limited. stderr_excerpt={result.stderr_excerpt!r}"
    )
    assert result.ok is False


def test_codex_parse_response_prompt_echo_is_not_rate_limit(tmp_path):
    """Regression: Codex CLI echoes the user prompt to stderr. The bridge
    prompts include standing rules mentioning 'usage limit reached' and
    'rate-limit error' as instructions to Codex. A successful call must
    NOT be classified as rate-limited just because its own prompt contains
    those phrases. This bug broke bridge comms entirely on 2026-04-10.
    """
    adapter = CodexAdapter()
    output_file = tmp_path / "output.txt"
    output_file.write_text("PONG")

    # Simulate the real Codex CLI stderr: banner + echoed prompt that
    # happens to contain rate-limit phrases from the standing rules.
    stderr = (
        "OpenAI Codex v0.118.0 (research preview)\n"
        "--------\n"
        "workdir: /Users/foo/project\n"
        "model: gpt-5.4\n"
        "provider: openai\n"
        "approval: never\n"
        "sandbox: read-only\n"
        "reasoning effort: high\n"
        "session id: abc12345\n"
        "--------\n"
        "user\n"
        "Reply with exactly: PONG\n"
        "## Reporting\n"
        "- If you hit a 'usage limit reached' or rate-limit error, STOP.\n"
        "\n"
        "codex\n"
        "PONG\n"
        "tokens used\n"
        "4089\n"
    )

    result = adapter.parse_response(
        stdout="session id: abc12345",
        stderr=stderr,
        returncode=0,
        output_file=output_file,
    )
    # Call succeeded (rc=0, output file has content), therefore CANNOT
    # be rate-limited regardless of what pattern text appears in stderr.
    assert result.rate_limited is False, (
        f"False rate-limit classification on successful call. "
        f"stderr_excerpt={result.stderr_excerpt!r}"
    )
    assert result.ok is True
    assert result.response == "PONG"


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


def test_should_kill_ignores_stall_silence():
    """Stall detection was removed from the kill path on 2026-04-10 after
    repeated production incidents where successful long-running calls
    were killed as false-positive stalls. A silent-but-alive process
    must NOT be killed — only hard_timeout can kill. See
    watchdog.py::should_kill() docstring for the full incident chain.
    """
    now = time.monotonic()
    state = WatchdogState(start_time=now - 60, last_activity=now - 2000)
    # Silent for 2000s, well past stall_timeout=180. Still must not kill.
    assert should_kill(state, stall_timeout=180, hard_timeout=3600) is None


def test_should_kill_detects_hard_timeout():
    now = time.monotonic()
    state = WatchdogState(start_time=now - 4000, last_activity=now)
    # Started 4000s ago, hard_timeout 3600s → hard_timeout
    assert should_kill(state, stall_timeout=180, hard_timeout=3600) == "hard_timeout"


def test_tail_liveness_skips_binary_sqlite(tmp_path):
    """Regression: state_5.sqlite is in Codex's liveness paths and can
    be the newest at failure time. We must not decode it as UTF-8 and
    write replacement-char garbage into stderr_excerpt. (Gemini review
    finding, #1184.)
    """
    # Binary SQLite-ish file (just needs the extension)
    binary = tmp_path / "state_5.sqlite"
    binary.write_bytes(b"\x00\x01\x02\xff\xfe" * 800)  # 4KB of binary
    # Older text file that IS tailable
    text = tmp_path / "history.log"
    text.write_text("real error line 1\nreal error line 2\n")
    # Force the text file to be older than the binary (the binary is
    # newest, which is what would trigger the bug).
    import os as _os
    _os.utime(text, (text.stat().st_mtime - 60, text.stat().st_mtime - 60))

    result = tail_liveness_file_for_debug([binary, text])
    # The binary must be filtered out; the text file should be chosen.
    assert "real error" in result
    assert "\ufffd" not in result, (
        f"UTF-8 replacement char leaked from binary file tail: {result!r}"
    )


def test_tail_liveness_skips_directories(tmp_path):
    """Codex passes sessions/YYYY/MM/DD/ as a liveness path. Tailing a
    directory as if it were a file should fail gracefully and fall
    through to the next candidate, not raise or return garbage.
    """
    sessions_dir = tmp_path / "sessions-today"
    sessions_dir.mkdir()
    # Make it the newest path
    text = tmp_path / "history.log"
    text.write_text("fallback content\n")
    import os as _os
    _os.utime(text, (text.stat().st_mtime - 60, text.stat().st_mtime - 60))

    result = tail_liveness_file_for_debug([sessions_dir, text])
    assert "fallback content" in result


def test_tail_liveness_empty_on_all_binary_or_dirs(tmp_path):
    """If every candidate is binary or a directory, return empty."""
    binary = tmp_path / "logs_1.sqlite"
    binary.write_bytes(b"\x00" * 100)
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    assert tail_liveness_file_for_debug([binary, empty_dir]) == ""


def test_stop_watchdog_unblocks_stdout_streamer():
    """Regression: the stdout streamer thread used to block on
    proc.stdout.readline() forever because state.stop=True does not
    interrupt a blocked read. daemon=True prevented process hang but
    we accumulated orphaned threads during long bridge sessions.

    Fix: stop_watchdog(proc=proc) closes proc.stdout, which makes the
    blocked readline raise ValueError — the streamer's try/except
    catches it and the thread exits cleanly. Test: start a subprocess
    that sleeps with no output, stop the watchdog, assert the streamer
    thread has joined within a short timeout.

    This is the bug Gemini flagged in his 2026-04-10 review. If we
    ever regress, this test will catch it.
    """
    import subprocess as _sp
    import sys as _sys

    # A quiet subprocess that will sit silent forever (well, 30s)
    proc = _sp.Popen(
        [_sys.executable, "-c", "import time; time.sleep(30)"],
        stdout=_sp.PIPE,
        stderr=_sp.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        state, threads = start_watchdog(proc, liveness_paths=[])
        # Find the streamer thread
        streamer = next((t for t in threads if "stdout" in t.name), None)
        assert streamer is not None, "streamer thread was not started"
        assert streamer.is_alive(), "streamer should be running"

        # Kill the subprocess first (required ordering: we only close
        # stdout after kill to avoid SIGPIPE) and stop the watchdog.
        proc.kill()
        proc.wait(timeout=5.0)
        stop_watchdog(state, threads, timeout=2.0, proc=proc)

        # The streamer MUST have joined by now — without the fix, the
        # thread would still be blocked on readline() and is_alive()
        # would return True.
        assert not streamer.is_alive(), (
            "streamer thread leaked — still running after stop_watchdog. "
            "This is the bug the 2026-04-10 fix was supposed to prevent."
        )
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5.0)


def test_should_kill_hard_timeout_is_the_only_killer():
    """Regression pin: even when the process has been silent for a long
    time AND past hard_timeout, hard_timeout is what fires — there is
    no 'stalled' return value anymore.
    """
    now = time.monotonic()
    state = WatchdogState(start_time=now - 4000, last_activity=now - 2000)
    # Both past "stall threshold" AND past hard_timeout — only kill reason
    # is hard_timeout (stall detection is no longer a kill condition).
    assert should_kill(state, stall_timeout=180, hard_timeout=3600) == "hard_timeout"


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
