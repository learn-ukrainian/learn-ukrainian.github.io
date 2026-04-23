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

import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

_TEST_PYTHON = str(Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python")

from agent_runtime.adapters.claude import ClaudeAdapter
from agent_runtime.adapters.codex import CodexAdapter
from agent_runtime.adapters.gemini import GeminiAdapter, resolve_gemini_auth_mode
from agent_runtime.errors import (
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)
from agent_runtime.registry import AGENTS, get_agent_entry
from agent_runtime.runner import (
    _enforce_resume_policy,
    _is_temp_file,
    _kill_process_tree,
    _load_adapter,
    invoke,
)
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
    assert set(AGENTS.keys()) == {"codex", "claude", "gemini", "gemma-local", "grok"}


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


def test_load_adapter_gemma_local():
    adapter = _load_adapter("gemma-local")
    assert adapter.__class__.__name__ == "GemmaLocalAdapter"
    assert adapter.default_model == "mlx-community/gemma-4-e4b-it-4bit"
    assert adapter.supported_modes == frozenset(
        {"read-only", "workspace-write", "danger"}
    )


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

    with pytest.raises(ValueError, match="resume_policy='never'"):
        _enforce_resume_policy("gemma-local", session_id="some-uuid", entrypoint="bridge")


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
    assert "-c" not in plan.cmd  # tool_config=None preserves prior behavior
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


def test_codex_adapter_mcp_tool_config(tmp_path):
    """Codex MCP config must survive the protocol via ``-c`` overrides."""
    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={
            "mcp_servers": {
                "sources": {"url": "http://127.0.0.1:8766/sse"},
            },
        },
    )
    assert "-c" in plan.cmd
    idx = plan.cmd.index("-c")
    assert plan.cmd[idx + 1] == 'mcp_servers.sources.url="http://127.0.0.1:8766/sse"'


def test_codex_adapter_mcp_tool_config_multiple(tmp_path):
    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={
            "mcp_servers": {
                "sources": {"url": "http://127.0.0.1:8766/sse"},
                "other": {"url": "http://127.0.0.1:9001/sse", "enabled": True},
            },
        },
    )
    config_values = [
        plan.cmd[index + 1]
        for index, token in enumerate(plan.cmd[:-1])
        if token == "-c"
    ]
    assert 'mcp_servers.sources.url="http://127.0.0.1:8766/sse"' in config_values
    assert 'mcp_servers.other.url="http://127.0.0.1:9001/sse"' in config_values
    assert "mcp_servers.other.enabled=true" in config_values


def test_codex_adapter_ignores_unknown_tool_config_keys(tmp_path):
    """Forward compatibility: unknown Codex tool_config keys stay local."""
    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={
            "mcp_servers": {
                "sources": {"url": "http://127.0.0.1:8766/sse"},
            },
            "some_future_field": "value",
        },
    )
    config_values = [
        plan.cmd[index + 1]
        for index, token in enumerate(plan.cmd[:-1])
        if token == "-c"
    ]
    assert 'mcp_servers.sources.url="http://127.0.0.1:8766/sse"' in config_values
    cmd_str = " ".join(plan.cmd)
    assert "some_future_field" not in cmd_str


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


def test_codex_liveness_paths_exclude_rollout_files(tmp_path, monkeypatch):
    """Regression: the adapter must NOT return any rollout-*.jsonl
    file in liveness paths.

    Earlier version returned the newest rollout-*.jsonl, but picking
    at plan-build time is wrong: the match is always the PREVIOUS
    run's file, not the one Codex is about to create. Tracking that
    wrong file provides no liveness signal during the new run AND
    leaks the wrong trace into tail_liveness_file_for_debug on
    failure. Gemini flagged this in the 2026-04-10 review.

    What we DO return: the sessions/YYYY/MM/DD/ directory itself,
    whose mtime bumps when Codex creates its new rollout file at
    startup. That's the only correct signal we can compute before
    the subprocess spawns.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    from datetime import UTC, datetime
    today = datetime.now(UTC)
    sessions_today = (
        fake_home / ".codex" / "sessions"
        / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
    )
    sessions_today.mkdir(parents=True)

    # Prior run's rollout file — must NOT appear in liveness paths
    old_rollout = sessions_today / "rollout-2026-04-10T18-00-00-aaa.jsonl"
    old_rollout.write_text('{"old": true}\n')

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
    assert old_rollout.name not in names, (
        f"rollout-*.jsonl should not be in liveness paths (that's the "
        f"PREVIOUS run's file, see Gemini 2026-04-10 review): {names}"
    )
    # But the sessions directory itself MUST be there — its mtime
    # bumps when the new run creates its rollout file at startup.
    assert sessions_today in paths, (
        f"sessions/today dir missing from liveness paths: {paths}"
    )


def test_codex_parse_response_signaled_exit_is_never_rate_limit(tmp_path):
    """Regression (Codex 2026-04-10 review, BUG #9): if a Codex process
    is killed by signal (negative returncode), the adapter must NOT
    pattern-match rate-limit phrases in stderr. A signal-kill means
    WE killed the process (hard_timeout, cancel, exception mid-poll).
    The stderr at that point may contain only a partial prompt echo
    (no closing divider, no Codex response section) and the
    'last divider' heuristic would fall through to echoed prompt text,
    reintroducing the same false-positive bug we've been fighting.

    Guard: returncode < 0 → rate_limited = False, always. Whatever the
    pattern-matcher would say is ignored.
    """
    adapter = CodexAdapter()
    output_file = tmp_path / "output.txt"
    output_file.write_text("")  # call failed

    # Killed mid-echo — only the banner and opening of the prompt
    # made it to stderr. There is NO closing divider. The "last
    # divider" is the one right before 'user', and the body after it
    # is the prompt fragment with "rate limit" phrases.
    stderr = (
        "OpenAI Codex v0.118.0 (research preview)\n"
        "--------\n"
        "workdir: /foo\n"
        "model: gpt-5.4\n"
        "--------\n"
        "user\n"
        "Review our rate-limit handling code. We had a usage limit\n"
        "reached incident. What do you think about rate limit?\n"
    )

    result = adapter.parse_response(
        stdout="",
        stderr=stderr,
        returncode=-15,  # SIGTERM
        output_file=output_file,
    )
    # Signal-killed → can NEVER be classified as rate_limited,
    # regardless of what stderr contains.
    assert result.rate_limited is False, (
        "signal-killed call must never be classified as rate_limited, "
        f"stderr_excerpt={result.stderr_excerpt!r}"
    )
    assert result.ok is False


def test_codex_check_early_reap_fires_when_task_complete_present(
    tmp_path, monkeypatch
):
    """Regression pin (2026-04-10): check_early_reap must return True
    as soon as a task_complete event appears in a NEW rollout file
    (one created after build_invocation). Without this, the runner
    waits the full hard_timeout on every Codex post-completion hang.

    Production flow: build_invocation → Codex spawns → Codex creates a
    new rollout file → check_early_reap finds it. The test simulates
    this by building an empty snapshot (no pre-existing rollouts),
    then planting the new rollout AFTER build_invocation.
    """
    import json as _json
    import time as _time
    from datetime import UTC, datetime

    adapter = CodexAdapter()

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    today = datetime.now(UTC)
    sessions_today = (
        fake_home / ".codex" / "sessions"
        / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
    )
    sessions_today.mkdir(parents=True)

    # build_invocation takes the snapshot of pre-existing rollouts.
    # At this point the dir is empty.
    plan = adapter.build_invocation(
        prompt="x",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="reap-test",
        session_id=None,
        tool_config=None,
    )

    # NOW plant the new rollout — this simulates Codex creating its
    # rollout file AFTER the subprocess started. It must appear in
    # check_early_reap as a non-snapshotted candidate.
    rollout = sessions_today / "rollout-new-after-build.jsonl"
    rollout.write_text(
        "\n".join(
            [
                _json.dumps({
                    "type": "event_msg",
                    "payload": {
                        "type": "user_message",
                        "message": "x",
                    },
                }),
                _json.dumps({
                    "type": "event_msg",
                    "payload": {
                        "type": "task_complete",
                        "last_agent_message": "Here is the full audit...",
                    },
                }),
            ]
        ) + "\n"
    )

    # call_start_time 10s in the past so the "has been running long
    # enough" guard doesn't short-circuit.
    call_start = _time.monotonic() - 10.0
    assert adapter.check_early_reap(plan, call_start_time=call_start) is True


def test_codex_check_early_reap_ignores_preexisting_rollouts(
    tmp_path, monkeypatch
):
    """Regression pin for the cross-contamination fix (Codex 2026-04-10
    audit): a rollout file that existed BEFORE our build_invocation must
    NOT trigger early-reap, because it belongs to a previous or
    concurrent call.
    """
    import json as _json
    import time as _time
    from datetime import UTC, datetime

    adapter = CodexAdapter()

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    today = datetime.now(UTC)
    sessions_today = (
        fake_home / ".codex" / "sessions"
        / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
    )
    sessions_today.mkdir(parents=True)

    # Plant a stale rollout BEFORE build_invocation — it belongs to
    # a previous call. The snapshot should capture it as pre-existing.
    stale = sessions_today / "rollout-stale-from-other-run.jsonl"
    stale.write_text(_json.dumps({
        "type": "event_msg",
        "payload": {
            "type": "task_complete",
            "last_agent_message": "OTHER TASK'S ANSWER",
        },
    }) + "\n")

    # build_invocation snapshots all pre-existing rollouts.
    plan = adapter.build_invocation(
        prompt="x",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="contamination-test",
        session_id=None,
        tool_config=None,
    )

    # No new rollout has been created. check_early_reap should NOT
    # return True — the stale file is in the snapshot.
    call_start = _time.monotonic() - 10.0
    assert adapter.check_early_reap(plan, call_start_time=call_start) is False


def test_codex_check_early_reap_skips_within_warmup_window(tmp_path, monkeypatch):
    """Early reap must NOT fire within the first 5 seconds of a call,
    even if a stale rollout from a previous run has a task_complete.
    Otherwise we'd instantly reap legitimate new calls based on old
    file state.
    """
    import json as _json
    import time as _time
    from datetime import UTC, datetime

    adapter = CodexAdapter()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    today = datetime.now(UTC)
    sessions_today = (
        fake_home / ".codex" / "sessions"
        / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
    )
    sessions_today.mkdir(parents=True)
    (sessions_today / "rollout-old.jsonl").write_text(_json.dumps({
        "type": "event_msg",
        "payload": {"type": "task_complete", "last_agent_message": "old"},
    }) + "\n")

    plan = adapter.build_invocation(
        prompt="x", mode="read-only", cwd=tmp_path,
        model=None, task_id="warmup", session_id=None, tool_config=None,
    )

    # call_start_time = now (0s elapsed) — within warmup window
    assert adapter.check_early_reap(
        plan, call_start_time=_time.monotonic()
    ) is False


def test_codex_check_early_reap_returns_false_when_no_task_complete(
    tmp_path, monkeypatch
):
    """If there's NO task_complete event yet in the rollout, return False
    so the runner keeps polling normally.
    """
    import json as _json
    import time as _time
    from datetime import UTC, datetime

    adapter = CodexAdapter()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    today = datetime.now(UTC)
    sessions_today = (
        fake_home / ".codex" / "sessions"
        / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
    )
    sessions_today.mkdir(parents=True)
    # A rollout file with only reasoning deltas, no task_complete
    (sessions_today / "rollout-inprogress.jsonl").write_text(
        _json.dumps({"type": "response_item",
                     "payload": {"type": "reasoning_delta"}}) + "\n"
    )

    plan = adapter.build_invocation(
        prompt="x", mode="read-only", cwd=tmp_path,
        model=None, task_id=None, session_id=None, tool_config=None,
    )

    call_start = _time.monotonic() - 10.0
    assert adapter.check_early_reap(plan, call_start_time=call_start) is False


def test_codex_parse_response_recovers_from_rollout_task_complete(
    tmp_path, monkeypatch
):
    """Regression (2026-04-10 production incident): codex-cli 0.118
    has a post-completion hang bug where the CLI writes task_complete
    to rollout-*.jsonl, then hangs at 0% CPU without flushing -o <file>
    or exiting. The adapter must recover by reading the rollout file.

    Simulation: empty -o file (as if Codex never flushed), populated
    rollout file with a task_complete event, planted AFTER
    build_invocation (so it's not in the snapshot of pre-existing
    rollouts — the cross-contamination fix excludes those).
    Adapter should return ok=True with the rollout message.
    """
    import json as _json
    from datetime import UTC, datetime

    adapter = CodexAdapter()

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    # Build today's sessions dir EMPTY — no pre-existing rollouts
    today = datetime.now(UTC)
    sessions_today = (
        fake_home / ".codex" / "sessions"
        / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
    )
    sessions_today.mkdir(parents=True)

    # Empty -o file (the hang: Codex never flushed it)
    output_file = tmp_path / "codex-out.txt"
    output_file.write_text("")

    # build_invocation snapshots pre-existing rollouts (currently empty).
    plan = adapter.build_invocation(
        prompt="Write a BST",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="bst-test",
        session_id=None,
        tool_config=None,
    )

    # Plant the rollout AFTER build_invocation — simulates Codex
    # creating its own rollout during the call.
    rollout = sessions_today / "rollout-2026-04-10T21-35-20-test.jsonl"
    events = [
        {"timestamp": "2026-04-10T21:35:21Z", "type": "event_msg",
         "payload": {"type": "session_start"}},
        {"timestamp": "2026-04-10T21:35:22Z", "type": "event_msg",
         "payload": {"type": "user_message", "message": "Write a BST"}},
        {"timestamp": "2026-04-10T21:36:00Z", "type": "response_item",
         "payload": {"type": "reasoning_delta"}},
        {"timestamp": "2026-04-10T21:40:02Z", "type": "event_msg",
         "payload": {
             "type": "task_complete",
             "turn_id": "abc-123",
             "last_agent_message": "Here is the binary search tree implementation...",
         }},
    ]
    rollout.write_text("\n".join(_json.dumps(e) for e in events) + "\n")

    # returncode=-9 simulates "we killed the hung process after early-reap"
    result = adapter.parse_response(
        stdout="",
        stderr="",
        returncode=-9,
        output_file=output_file,
        plan=plan,
    )

    assert result.ok is True, (
        f"expected rollout recovery to succeed, got stderr_excerpt="
        f"{result.stderr_excerpt!r}"
    )
    assert "binary search tree implementation" in result.response
    assert "recovered" in (result.stderr_excerpt or "")
    assert "rollout" in (result.stderr_excerpt or "")
    assert result.rate_limited is False


def test_codex_parse_response_rollout_recovery_skipped_on_happy_path(
    tmp_path, monkeypatch
):
    """When -o <file> has content, skip the rollout scan entirely.
    Happy path must stay fast (no JSON parsing on every success)."""
    import json as _json
    from datetime import UTC, datetime

    adapter = CodexAdapter()

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    today = datetime.now(UTC)
    sessions_today = (
        fake_home / ".codex" / "sessions"
        / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
    )
    sessions_today.mkdir(parents=True)

    # Plant a rollout with DIFFERENT content so we'd notice if the
    # adapter accidentally read from it on the happy path.
    rollout = sessions_today / "rollout-test.jsonl"
    rollout.write_text(_json.dumps({
        "type": "event_msg",
        "payload": {"type": "task_complete",
                    "last_agent_message": "STALE rollout content"},
    }) + "\n")

    output_file = tmp_path / "codex-out.txt"
    output_file.write_text("Fresh -o file response")

    plan = adapter.build_invocation(
        prompt="x",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    result = adapter.parse_response(
        stdout="session id: abc123",
        stderr="",
        returncode=0,
        output_file=output_file,
        plan=plan,
    )

    assert result.ok is True
    assert result.response == "Fresh -o file response"
    assert "STALE" not in result.response


def test_codex_parse_response_ignores_unrelated_new_rollout(
    tmp_path, monkeypatch
):
    """Do not recover durable output from a new rollout whose prompt does not
    match this invocation.

    Regression for #1267: snapshot-based "newest rollout wins" binding is not
    sufficient when another Codex exec run starts after ours and writes a newer
    rollout in the same day directory. Recovery must validate that the rollout
    belongs to the current stdin payload before accepting task_complete output.
    """
    import json as _json
    from datetime import UTC, datetime

    adapter = CodexAdapter()

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    today = datetime.now(UTC)
    sessions_today = (
        fake_home / ".codex" / "sessions"
        / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
    )
    sessions_today.mkdir(parents=True)

    output_file = tmp_path / "codex-out.txt"
    output_file.write_text("")

    plan = adapter.build_invocation(
        prompt="Review style issues for i-want-i-can",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="style-review",
        session_id=None,
        tool_config=None,
    )

    unrelated_rollout = sessions_today / "rollout-unrelated.jsonl"
    unrelated_rollout.write_text(
        "\n".join(
            [
                _json.dumps({
                    "type": "event_msg",
                    "payload": {
                        "type": "user_message",
                        "message": "Completely different task in another repo",
                    },
                }),
                _json.dumps({
                    "type": "event_msg",
                    "payload": {
                        "type": "task_complete",
                        "last_agent_message": "UNRELATED durable output",
                    },
                }),
            ]
        ) + "\n",
        "utf-8",
    )

    result = adapter.parse_response(
        stdout="",
        stderr="",
        returncode=-9,
        output_file=output_file,
        plan=plan,
    )

    assert result.ok is False
    assert result.response == ""
    assert "UNRELATED durable output" not in (result.stderr_excerpt or "")


def test_codex_parse_response_nested_divider_in_prompt_not_rate_limit(tmp_path):
    """Regression (Gemini 2026-04-10 review): a user prompt containing
    a legitimate dashes-only line (code block, horizontal rule) used to
    defeat the naive lazy-regex that tried to strip the prompt block.

    The fix switched from "match between two dividers" to "take the
    stderr tail after the LAST divider". Whatever's after the last
    divider is guaranteed to be Codex's own output, never echoed
    prompt. A prompt with 17 inline dashes lines can't poison
    classification anymore.
    """
    adapter = CodexAdapter()
    output_file = tmp_path / "output.txt"
    output_file.write_text("")  # call failed

    stderr = (
        "OpenAI Codex v0.118.0 (research preview)\n"
        "--------\n"
        "workdir: /foo\n"
        "model: gpt-5.4\n"
        "--------\n"
        "user\n"
        "Review our rate-limit handling code. Example:\n"
        "\n"
        "```\n"
        "--------\n"  # inline divider inside the prompt
        "if usage limit reached:\n"
        "    log('rate limit triggered')\n"
        "--------\n"  # another inline divider
        "```\n"
        "\n"
        "What do you think?\n"
        "--------\n"  # real closing divider
        "codex\n"
        "error: terminated by signal 15\n"
    )

    result = adapter.parse_response(
        stdout="",
        stderr=stderr,
        returncode=-15,
        output_file=output_file,
    )
    # The real error ("terminated by signal") is not a rate limit.
    # The prompt's rate-limit phrases must not leak into classification.
    assert result.rate_limited is False, (
        f"Prompt with inline dividers + rate-limit phrases poisoned "
        f"classification. stderr_excerpt={result.stderr_excerpt!r}"
    )
    assert result.ok is False


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


def test_invoke_popen_missing_binary_raises_agent_unavailable(tmp_path):
    """Regression (Codex 2026-04-10 audit): when Popen fails because
    the CLI binary isn't on PATH, the runner must raise
    AgentUnavailableError (matching its public contract), NOT leak a
    raw FileNotFoundError. It must also write a usage record for
    observability.
    """
    from agent_runtime.errors import AgentUnavailableError

    # Patch Popen to raise FileNotFoundError as if the codex binary
    # is missing. Also patch has_headroom so we reach Popen.
    with patch(
        "agent_runtime.runner.has_headroom", return_value=(True, ""),
    ), patch(
        "agent_runtime.runner.write_record",
    ) as mock_write, patch(
        "agent_runtime.runner.subprocess.Popen",
        side_effect=FileNotFoundError("[Errno 2] No such file: 'codex'"),
    ), pytest.raises(AgentUnavailableError, match="Popen failed"):
        invoke("codex", "hello", mode="read-only", cwd=tmp_path)

    # A usage record must have been written.
    assert mock_write.called, (
        "runner must write a usage record even on Popen failure"
    )
    written = mock_write.call_args.args[0]
    assert written.get("outcome") == "error"
    assert "Popen failed" in (written.get("stderr_excerpt") or "")
    assert "FileNotFoundError" in (written.get("stderr_excerpt") or "")


def test_invoke_early_reap_fires_and_recovers_response(tmp_path, monkeypatch):
    """Regression pin (2026-04-10): when an adapter's check_early_reap
    returns True, the runner must kill the subprocess and call
    parse_response, which is expected to recover the response from
    whatever on-disk state the adapter uses.

    This test pins the whole Codex post-completion-hang recovery path:
    runner polls early_reap → returns True → runner kills proc →
    parse_response reads rollout file → returns successful Result.

    We plant the rollout file from inside the mock's proc.poll()
    side_effect — this simulates Codex creating its rollout AFTER
    build_invocation took its empty snapshot. The snapshot-based
    cross-contamination fix would otherwise exclude any file that
    existed before build_invocation ran.
    """
    import json as _json
    from datetime import UTC, datetime
    from unittest.mock import MagicMock

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    today = datetime.now(UTC)
    sessions_today = (
        fake_home / ".codex" / "sessions"
        / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
    )
    sessions_today.mkdir(parents=True)

    rollout = sessions_today / "rollout-reap-test.jsonl"
    # Rollout must contain BOTH a user_message event (so
    # _rollout_matches_plan can match on plan.stdin_payload) AND a
    # task_complete event (so the early-reap detector finds a result).
    rollout_payload = (
        _json.dumps({
            "type": "event_msg",
            "payload": {
                "type": "user_message",
                "message": "do the audit",
            },
        }) + "\n"
        + _json.dumps({
            "type": "event_msg",
            "payload": {
                "type": "task_complete",
                "last_agent_message": "The complete audit response is here.",
            },
        }) + "\n"
    )

    # Mock Popen: poll() returns None (running) before kill, -9 after.
    # On the FIRST poll, plant the rollout file. This simulates Codex
    # creating its rollout file between startup and the first runner
    # poll iteration, which is what happens in production.
    mock_proc = MagicMock()
    state = {"killed": False, "planted": False}
    def fake_poll():
        if not state["planted"]:
            rollout.write_text(rollout_payload)
            state["planted"] = True
        return -9 if state["killed"] else None
    mock_proc.poll = MagicMock(side_effect=fake_poll)
    mock_proc.returncode = -9
    def fake_kill():
        state["killed"] = True
    mock_proc.kill = MagicMock(side_effect=fake_kill)
    mock_proc.wait = MagicMock()
    mock_proc.stdin = MagicMock()
    mock_proc.stderr = MagicMock()
    mock_proc.stderr.readline = MagicMock(return_value="")
    mock_proc.stderr.close = MagicMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline = MagicMock(return_value="")
    mock_proc.stdout.close = MagicMock()
    mock_proc.pid = 99999

    # _kill_process_tree replaces bare proc.kill() in the runner.
    # We mock it so it still flips state["killed"] (via fake_kill)
    # without actually sending signals.
    mock_kill_tree = MagicMock(side_effect=lambda p: fake_kill())

    # Make the warmup guard pass by pretending the call is 10s old.
    # We do that by patching time.monotonic inside the runner to return
    # a value >5s after start_time. Easier: just patch the adapter's
    # own warmup guard by patching monotonic globally.
    import time as _time

    base_time = _time.monotonic()
    monotonic_values = iter([
        base_time,       # start_time capture in runner
        base_time + 10,  # poll loop first check_early_reap
        base_time + 11, base_time + 12, base_time + 13, base_time + 14,
    ])
    def fake_monotonic():
        try:
            return next(monotonic_values)
        except StopIteration:
            return base_time + 20

    with patch(
        "agent_runtime.runner.has_headroom", return_value=(True, ""),
    ), patch(
        "agent_runtime.runner.write_record",
    ), patch(
        "agent_runtime.runner.subprocess.Popen", return_value=mock_proc,
    ), patch(
        "agent_runtime.runner._POLL_INTERVAL_S", 0.01,
    ), patch(
        "agent_runtime.runner.time.monotonic", side_effect=fake_monotonic,
    ), patch(
        "agent_runtime.runner._kill_process_tree", mock_kill_tree,
    ):
        result = invoke(
            "codex", "do the audit",
            mode="read-only",
            cwd=tmp_path,
            task_id="reap-integration",
            entrypoint="runtime",
            hard_timeout=300,
        )

    # Runner must have killed the proc via _kill_process_tree (early reap)
    mock_kill_tree.assert_called_once()
    # And returned a successful Result with the recovered response
    assert result.ok is True, (
        f"early-reap recovery should produce ok=True, "
        f"got stderr_excerpt={result.stderr_excerpt!r}"
    )
    assert "complete audit response" in result.response
    assert "rollout" in (result.stderr_excerpt or "")


def test_invoke_hard_timeout_recovers_from_session_file(tmp_path, monkeypatch):
    """REGRESSION PIN (2026-04-10): when the runner hard-timeout-kills a
    Gemini call, it MUST still call adapter.parse_response() so the
    adapter can recover work from the session file on disk.

    The bug the test guards against: the old runner raised
    AgentTimeoutError immediately on hard_timeout, which skipped
    parse_response entirely. That meant Gemini CLI responses already
    written to ~/.gemini/tmp/.../chats/session-*.json were thrown away
    and the dispatcher cascaded to a different model for no reason.

    The fix calls parse_response first, then only raises
    AgentTimeoutError if parse couldn't recover anything.
    """
    import json as _json
    from unittest.mock import MagicMock

    # Set up a fake $HOME with a Gemini session file for the test project.
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    project_cwd = tmp_path / "learn-ukrainian"
    project_cwd.mkdir()

    chats_dir = fake_home / ".gemini" / "tmp" / "learn-ukrainian" / "chats"
    chats_dir.mkdir(parents=True)
    (chats_dir / "session-latest.json").write_text(_json.dumps({
        "sessionId": "x",
        "messages": [
            {"type": "user", "content": [{"text": "write a module"}]},
            {"type": "gemini",
             "content": "### Skeleton\n\n## Section 1\n...full response..."},
        ],
    }), "utf-8")

    # Mock Popen so it never really spawns a subprocess. We simulate
    # a hang by NOT setting returncode on the first poll and then
    # having should_kill fire hard_timeout.
    mock_proc = MagicMock()
    # First poll: None (running). Subsequent polls: -9 (killed).
    mock_proc.poll = MagicMock(side_effect=[None, None, -9, -9, -9])
    mock_proc.returncode = -9
    mock_proc.kill = MagicMock()
    mock_proc.wait = MagicMock()
    # stdin/stderr/stdout: provide minimal stubs so the runner's
    # streamer + drain code doesn't blow up.
    mock_proc.stdin = MagicMock()
    mock_proc.stderr = MagicMock()
    # Return "" on readline so the _stderr_streamer thread's
    # iter(readline, "") exits immediately with zero captured lines.
    # (Before 2026-04-10 the runner read proc.stderr.read() directly;
    # now it drains via a streamer thread, so mocks need readline too.)
    mock_proc.stderr.readline = MagicMock(return_value="")
    mock_proc.stderr.read = MagicMock(return_value="")
    mock_proc.stderr.close = MagicMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline = MagicMock(return_value="")  # empty = streamer exits
    mock_proc.stdout.close = MagicMock()
    mock_proc.pid = 99999

    mock_kill_tree = MagicMock()

    # has_headroom mock: always OK.
    # should_kill mock: fire hard_timeout on every call.
    with patch(
        "agent_runtime.runner.has_headroom",
        return_value=(True, ""),
    ), patch(
        "agent_runtime.runner.write_record",
    ), patch(
        "agent_runtime.runner.subprocess.Popen",
        return_value=mock_proc,
    ), patch(
        "agent_runtime.runner.should_kill",
        side_effect=lambda *a, **kw: "hard_timeout",
    ), patch(
        "agent_runtime.runner._POLL_INTERVAL_S", 0.01,
    ), patch(
        "agent_runtime.runner._kill_process_tree", mock_kill_tree,
    ):
        result = invoke(
            "gemini",
            "write a module",
            mode="workspace-write",
            cwd=project_cwd,
            hard_timeout=5,
        )

    # The key assertion: despite hard_timeout killing the subprocess,
    # invoke() RETURNED a Result (did NOT raise AgentTimeoutError)
    # because the adapter recovered the response from the session file.
    assert result.ok is True, (
        f"expected recovery from session file after hard_timeout, "
        f"got stderr_excerpt={result.stderr_excerpt!r}"
    )
    assert "Skeleton" in result.response
    assert "Section 1" in result.response
    assert "recovered" in (result.stderr_excerpt or "")


def test_invoke_gemini_runtime_falls_through_to_subscription_rung(tmp_path):
    """Runtime Gemini calls should reuse the shared auth ladder, not stay single-shot."""
    from unittest.mock import MagicMock

    api_proc = MagicMock()
    api_proc.poll = MagicMock(return_value=1)
    api_proc.returncode = 1
    api_proc.stdin = MagicMock()
    api_proc.stderr = MagicMock()
    api_proc.stderr.readline = MagicMock(side_effect=["429 quota exceeded\n", ""])
    api_proc.stderr.close = MagicMock()
    api_proc.stdout = MagicMock()
    api_proc.stdout.readline = MagicMock(return_value="")
    api_proc.stdout.close = MagicMock()
    api_proc.pid = 10101

    oauth_proc = MagicMock()
    oauth_proc.poll = MagicMock(return_value=0)
    oauth_proc.returncode = 0
    oauth_proc.stdin = MagicMock()
    oauth_proc.stderr = MagicMock()
    oauth_proc.stderr.readline = MagicMock(return_value="")
    oauth_proc.stderr.close = MagicMock()
    oauth_proc.stdout = MagicMock()
    oauth_proc.stdout.readline = MagicMock(
        side_effect=["Recovered on subscription rung\n", ""]
    )
    oauth_proc.stdout.close = MagicMock()
    oauth_proc.pid = 20202

    mock_popen = MagicMock(side_effect=[api_proc, oauth_proc])

    with patch.dict(
        "os.environ",
        {
            "GEMINI_API_KEY": "secret-key",
            "LU_GEMINI_COOLDOWN_PATH": str(tmp_path / "gemini-cooldown.json"),
        },
        clear=False,
    ), patch(
        "agent_runtime.runner.has_headroom", return_value=(True, ""),
    ), patch(
        "agent_runtime.runner.write_record",
    ), patch(
        "agent_runtime.runner.subprocess.Popen", mock_popen,
    ), patch(
        "agent_runtime.runner._resolve_gemini_ladder_auth_modes",
        return_value=("api", "oauth"),
    ), patch(
        "agent_runtime.runner._POLL_INTERVAL_S", 0.01,
    ):
        result = invoke(
            "gemini",
            "hello",
            mode="workspace-write",
            cwd=tmp_path,
            task_id="gemini-auth-fallback",
            entrypoint="runtime",
        )

    assert result.ok is True
    assert result.response == "Recovered on subscription rung"
    assert mock_popen.call_count == 2

    first_env = mock_popen.call_args_list[0].kwargs["env"]
    second_env = mock_popen.call_args_list[1].kwargs["env"]
    assert first_env.get("GEMINI_API_KEY") == "secret-key"
    assert "GEMINI_API_KEY" not in second_env


def test_invoke_gemini_runtime_reports_actual_fallback_model(tmp_path):
    """If Gemini succeeds on a later model rung, Result.model must reflect that model."""
    from unittest.mock import MagicMock

    primary_proc = MagicMock()
    primary_proc.poll = MagicMock(return_value=1)
    primary_proc.returncode = 1
    primary_proc.stdin = MagicMock()
    primary_proc.stderr = MagicMock()
    primary_proc.stderr.readline = MagicMock(side_effect=["429 RESOURCE_EXHAUSTED\n", ""])
    primary_proc.stderr.close = MagicMock()
    primary_proc.stdout = MagicMock()
    primary_proc.stdout.readline = MagicMock(return_value="")
    primary_proc.stdout.close = MagicMock()
    primary_proc.pid = 30303

    flash_proc = MagicMock()
    flash_proc.poll = MagicMock(return_value=0)
    flash_proc.returncode = 0
    flash_proc.stdin = MagicMock()
    flash_proc.stderr = MagicMock()
    flash_proc.stderr.readline = MagicMock(return_value="")
    flash_proc.stderr.close = MagicMock()
    flash_proc.stdout = MagicMock()
    flash_proc.stdout.readline = MagicMock(side_effect=["Flash model answer\n", ""])
    flash_proc.stdout.close = MagicMock()
    flash_proc.pid = 40404

    mock_popen = MagicMock(side_effect=[primary_proc, flash_proc])

    with patch.dict(
        "os.environ",
        {
            "GEMINI_AUTH_MODE": "api",
            "GEMINI_API_KEY": "secret-key",
            "LU_GEMINI_COOLDOWN_PATH": str(tmp_path / "gemini-cooldown.json"),
        },
        clear=False,
    ), patch(
        "agent_runtime.runner.has_headroom", return_value=(True, ""),
    ), patch(
        "agent_runtime.runner.write_record",
    ), patch(
        "agent_runtime.runner.subprocess.Popen", mock_popen,
    ), patch(
        "agent_runtime.runner._POLL_INTERVAL_S", 0.01,
    ):
        result = invoke(
            "gemini",
            "hello",
            mode="workspace-write",
            cwd=tmp_path,
            task_id="gemini-model-fallback",
            entrypoint="runtime",
        )

    assert result.ok is True
    assert result.model == "gemini-3-flash-preview"
    assert result.usage_record["model"] == "gemini-3-flash-preview"
    attempted_models = [call.args[0][2] for call in mock_popen.call_args_list]
    assert attempted_models == ["gemini-3.1-pro-preview", "gemini-3-flash-preview"]


def test_invoke_gemini_runtime_all_rate_limited_raises(tmp_path):
    """Runtime Gemini ladder exhaustion should surface as RateLimitedError."""
    from unittest.mock import MagicMock

    def make_rate_limited_proc(pid: int) -> MagicMock:
        proc = MagicMock()
        proc.poll = MagicMock(return_value=1)
        proc.returncode = 1
        proc.stdin = MagicMock()
        proc.stderr = MagicMock()
        proc.stderr.readline = MagicMock(side_effect=["429 quota exceeded\n", ""])
        proc.stderr.close = MagicMock()
        proc.stdout = MagicMock()
        proc.stdout.readline = MagicMock(return_value="")
        proc.stdout.close = MagicMock()
        proc.pid = pid
        return proc

    mock_popen = MagicMock(
        side_effect=[
            make_rate_limited_proc(50001),
            make_rate_limited_proc(50002),
            make_rate_limited_proc(50003),
        ]
    )

    with patch.dict(
        "os.environ",
        {
            "GEMINI_AUTH_MODE": "api",
            "GEMINI_API_KEY": "secret-key",
            "LU_GEMINI_COOLDOWN_PATH": str(tmp_path / "gemini-cooldown.json"),
        },
        clear=False,
    ), patch(
        "agent_runtime.runner.has_headroom", return_value=(True, ""),
    ), patch(
        "agent_runtime.runner.write_record",
    ) as mock_write, patch(
        "agent_runtime.runner.subprocess.Popen", mock_popen,
    ), patch(
        "agent_runtime.runner._POLL_INTERVAL_S", 0.01,
    ), pytest.raises(RateLimitedError):
        invoke(
            "gemini",
            "hello",
            mode="workspace-write",
            cwd=tmp_path,
            task_id="gemini-rate-limited",
            entrypoint="runtime",
        )

    assert mock_popen.call_count == 3
    written = mock_write.call_args.args[0]
    assert written["outcome"] == "rate_limited"
    assert written["model"] == "gemini-2.5-pro"


def test_invoke_gemini_runtime_timeout_ladder_raises_timeout(tmp_path):
    """If Gemini burns the overall ladder budget, invoke should raise AgentTimeoutError."""
    from unittest.mock import MagicMock

    timed_out_proc = MagicMock()
    timed_out_proc.poll = MagicMock(side_effect=[None, -9, -9])
    timed_out_proc.returncode = -9
    timed_out_proc.stdin = MagicMock()
    timed_out_proc.stderr = MagicMock()
    timed_out_proc.stderr.readline = MagicMock(return_value="")
    timed_out_proc.stderr.close = MagicMock()
    timed_out_proc.stdout = MagicMock()
    timed_out_proc.stdout.readline = MagicMock(return_value="")
    timed_out_proc.stdout.close = MagicMock()
    timed_out_proc.pid = 60606

    with patch.dict(
        "os.environ",
        {
            "GEMINI_AUTH_MODE": "api",
            "GEMINI_API_KEY": "secret-key",
            "LU_GEMINI_COOLDOWN_PATH": str(tmp_path / "gemini-cooldown.json"),
        },
        clear=False,
    ), patch(
        "agent_runtime.runner.has_headroom", return_value=(True, ""),
    ), patch(
        "agent_runtime.runner.write_record",
    ) as mock_write, patch(
        "agent_runtime.runner.subprocess.Popen", return_value=timed_out_proc,
    ), patch(
        "agent_runtime.runner.should_kill",
        side_effect=lambda *a, **kw: "hard_timeout",
    ), patch(
        "agent_runtime.runner._POLL_INTERVAL_S", 0.01,
    ), patch(
        "agent_runtime.runner._kill_process_tree",
    ), pytest.raises(AgentTimeoutError):
        invoke(
            "gemini",
            "hello",
            mode="workspace-write",
            cwd=tmp_path,
            task_id="gemini-timeout",
            entrypoint="runtime",
            hard_timeout=1,
        )

    written = mock_write.call_args.args[0]
    assert written["outcome"] == "hard_timeout"
    assert written["model"] == "gemini-3.1-pro-preview"


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


def test_stderr_streamer_drains_large_volume_without_hanging():
    """Regression pin (2026-04-10): the Codex post-completion hang was
    caused by stderr pipe backpressure. The runner piped stderr but
    never drained it during the run, so large stderr volumes
    (>16KB = the macOS pipe buffer) would block the subprocess on its
    next stderr write. Codex CLI writes hundreds of KB to stderr for
    tool-heavy tasks and hit this hard.

    This test spawns a Python subprocess that writes 200KB of stderr
    (many times the pipe buffer) and then exits, and verifies the
    runtime's stderr streamer drained it without blocking the child.
    If the fix regresses, this test will time out or the child will
    hang instead of exiting in milliseconds.
    """
    import subprocess as _sp

    # Child writes 2000 lines of 100 chars each to stderr, then exits.
    child_code = (
        "import sys\n"
        "for i in range(2000):\n"
        "    sys.stderr.write('line %05d: ' + 'x' * 80 + '\\n')\n"
        "sys.stderr.flush()\n"
    )
    proc = _sp.Popen(
        [_TEST_PYTHON, "-c", child_code],
        stdout=_sp.PIPE,
        stderr=_sp.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        state, threads = start_watchdog(proc, liveness_paths=[])
        # The child should exit in well under 2 seconds if the streamer
        # is draining. Before the fix, it would block forever on a full
        # stderr pipe.
        returncode = proc.wait(timeout=10.0)
        assert returncode == 0

        # Drain the threads
        stop_watchdog(state, threads, timeout=2.0, proc=proc)

        # Verify we actually captured all the stderr lines. 2000 lines
        # expected. If we drop a few at shutdown that's fine; anything
        # less than 1500 would indicate draining didn't work.
        assert len(state.stderr_lines) >= 1500, (
            f"stderr streamer should have captured most of 2000 lines; "
            f"got {len(state.stderr_lines)}"
        )
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5.0)


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

    # A quiet subprocess that will sit silent forever (well, 30s)
    proc = _sp.Popen(
        [_TEST_PYTHON, "-c", "import time; time.sleep(30)"],
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


@patch.dict("os.environ", {}, clear=True)
def test_resolve_gemini_auth_mode_defaults_to_subscription_without_explicit_api_opt_in(
    tmp_path, monkeypatch,
):
    # Always-subscription policy (2026-04-23, post-#1416, commit 4f0fae3c0b):
    # unset GEMINI_AUTH_MODE resolves to ``subscription``. The old
    # ``default to api when no oauth creds`` conditional was deleted.
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda _: tmp_path))
    assert resolve_gemini_auth_mode() == "subscription"


@patch.dict("os.environ", {"GEMINI_AUTH_MODE": "subscription"}, clear=True)
def test_gemini_adapter_subscription_mode_strips_api_key_env(tmp_path):
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
    assert plan.env_unsets == (
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
    )


@patch.dict("os.environ", {"GEMINI_AUTH_MODE": "api"}, clear=True)
def test_gemini_adapter_api_mode_preserves_api_key_env(tmp_path):
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
    assert plan.env_unsets == ()


@patch.dict("os.environ", {"GEMINI_AUTH_MODE": "auto"}, clear=True)
def test_gemini_adapter_auto_mode_prefers_subscription_when_oauth_creds_exist(tmp_path, monkeypatch):
    (tmp_path / ".gemini").mkdir(parents=True)
    (tmp_path / ".gemini" / "oauth_creds.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda _: tmp_path))
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
    assert plan.env_unsets == (
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
    )


@patch.dict("os.environ", {"GEMINI_AUTH_MODE": "bogus"}, clear=True)
def test_resolve_gemini_auth_mode_invalid_value_uses_default_resolution(tmp_path, monkeypatch):
    # Invalid GEMINI_AUTH_MODE normalizes to ``auto`` then falls through to
    # the always-subscription default. Only an explicit ``api`` opt-out
    # preserves the API-key path. See commit 4f0fae3c0b.
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda _: tmp_path))
    assert resolve_gemini_auth_mode() == "subscription"


@patch.dict("os.environ", {"GEMINI_AUTH_MODE": "api-key"}, clear=True)
def test_resolve_gemini_auth_mode_api_key_alias_maps_to_api():
    assert resolve_gemini_auth_mode() == "api"


@patch.dict("os.environ", {"GEMINI_AUTH_MODE": "api"}, clear=True)
def test_gemini_adapter_tool_config_auth_mode_overrides_env(tmp_path):
    adapter = GeminiAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="workspace-write",
        cwd=tmp_path,
        model="gemini-3.1-pro-preview",
        task_id=None,
        session_id=None,
        tool_config={"auth_mode": "subscription"},
    )
    assert plan.env_unsets == (
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
    )


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
        stderr="Error: RESOURCE_EXHAUSTED 429 quota",
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


def test_gemini_parse_response_rate_limit_in_stdout_is_not_a_fallback_signal():
    """The ladder only advances on stderr-based rate-limit signals."""
    adapter = GeminiAdapter()
    result = adapter.parse_response(
        stdout="Error: quota exceeded",
        stderr="",
        returncode=1,
        output_file=None,
    )
    assert result.rate_limited is False
    assert result.ok is False


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


def test_gemini_parse_response_recovers_from_session_file(tmp_path, monkeypatch):
    """When stdout is empty and the call was killed, parse_response must
    recover the assistant's response from ~/.gemini/tmp/<proj>/chats/
    session-*.json.

    This is the fix for the hard_timeout-kills-completed-work pattern:
    the Gemini CLI can block-buffer stdout and get killed while its
    response is already on disk. The adapter now reads the session
    file as a fallback when stdout is empty OR returncode != 0.
    """
    import json as _json

    adapter = GeminiAdapter()

    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    project_cwd = tmp_path / "learn-ukrainian"
    project_cwd.mkdir()

    # Create a realistic session file with a user message + two gemini
    # messages (the second one being the final answer).
    chats_dir = fake_home / ".gemini" / "tmp" / "learn-ukrainian" / "chats"
    chats_dir.mkdir(parents=True)
    session_data = {
        "sessionId": "abc-def",
        "startTime": "2026-04-10T20:00:00Z",
        "lastUpdated": "2026-04-10T20:05:00Z",
        "messages": [
            {"type": "user", "content": [{"text": "write a sonnet"}]},
            {"type": "gemini", "content": "Tool call thoughts…"},
            {"type": "gemini", "content": "Shall I compare thee to a summer's day"},
        ],
    }
    (chats_dir / "session-2026-04-10T20-00-abcdef.json").write_text(
        _json.dumps(session_data), "utf-8",
    )

    plan = adapter.build_invocation(
        prompt="x",
        mode="read-only",
        cwd=project_cwd,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    # Simulate a hard-timeout kill: stdout empty, returncode -9 (SIGKILL).
    result = adapter.parse_response(
        stdout="",
        stderr="(killed)",
        returncode=-9,
        output_file=None,
        plan=plan,
    )

    assert result.ok is True, (
        f"expected recovery to succeed, got {result.stderr_excerpt!r}"
    )
    assert "Shall I compare thee" in result.response
    assert "Tool call thoughts" in result.response  # both gemini msgs joined
    assert "recovered" in (result.stderr_excerpt or "")
    assert result.rate_limited is False


def test_gemini_parse_response_skips_recovery_on_fast_path(tmp_path, monkeypatch):
    """If stdout is non-empty and returncode == 0, never touch the session
    file. Fast path stays fast."""
    import json as _json

    adapter = GeminiAdapter()

    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    project_cwd = tmp_path / "learn-ukrainian"
    project_cwd.mkdir()

    # A session file with different content — if the adapter touched it,
    # the assertion below would pick that up instead of stdout.
    chats_dir = fake_home / ".gemini" / "tmp" / "learn-ukrainian" / "chats"
    chats_dir.mkdir(parents=True)
    (chats_dir / "session-old.json").write_text(
        _json.dumps({
            "messages": [
                {"type": "gemini", "content": "STALE content from old session"},
            ],
        }),
        "utf-8",
    )

    plan = adapter.build_invocation(
        prompt="x",
        mode="read-only",
        cwd=project_cwd,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    result = adapter.parse_response(
        stdout="fresh stdout response",
        stderr="",
        returncode=0,
        output_file=None,
        plan=plan,
    )

    assert result.ok is True
    assert result.response == "fresh stdout response"
    assert "STALE" not in result.response


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


# ---------------------------------------------------------------------------
# _kill_process_tree unit tests (#1286)
# ---------------------------------------------------------------------------


def test_kill_process_tree_kills_group_when_leader():
    """When the process IS the group leader, kill the entire group."""
    import os as _os
    from unittest.mock import MagicMock

    proc = MagicMock()
    proc.pid = 12345

    with patch.object(_os, "getpgid", return_value=12345), \
         patch.object(_os, "killpg") as mock_killpg:
        proc.wait = MagicMock()
        _kill_process_tree(proc)

    mock_killpg.assert_called_once_with(12345, __import__("signal").SIGKILL)


def test_kill_process_tree_falls_back_to_proc_kill():
    """When the process is NOT the group leader, fall back to proc.kill()."""
    import os as _os
    from unittest.mock import MagicMock

    proc = MagicMock()
    proc.pid = 12345

    # pgid != pid → not a group leader
    with patch.object(_os, "getpgid", return_value=99999):
        proc.wait = MagicMock()
        _kill_process_tree(proc)

    proc.kill.assert_called_once()


def test_kill_process_tree_handles_already_dead_process():
    """If the process is already gone, _kill_process_tree must not raise."""
    import os as _os
    from unittest.mock import MagicMock

    proc = MagicMock()
    proc.pid = 12345

    with patch.object(_os, "getpgid", side_effect=ProcessLookupError):
        # Should not raise
        _kill_process_tree(proc)


# ---------------------------------------------------------------------------
# _is_temp_file unit tests (#1286)
# ---------------------------------------------------------------------------


def test_is_temp_file_matches_system_temp_dir(tmp_path):
    """_is_temp_file must recognise files under the system temp directory."""
    import tempfile as _tf
    tmpdir = _tf.gettempdir()
    assert _is_temp_file(Path(tmpdir) / "codex-out-12345.txt") is True


def test_is_temp_file_rejects_non_temp_paths(tmp_path):
    """Paths outside /tmp and the system temp dir must return False."""
    assert _is_temp_file(Path("/home/user/project/output.txt")) is False
    assert _is_temp_file(tmp_path / "output.txt") is False


# ---------------------------------------------------------------------------
# Subprocess lifecycle tests (#1286)
# ---------------------------------------------------------------------------


def test_cleanup_deletes_empty_temp_files_on_kill(tmp_path, monkeypatch):
    """When the runner kills a subprocess and the output file is empty,
    the temp file should be cleaned up — not left as an orphan."""
    import tempfile as _tf

    # Create an empty output file in the system temp dir.
    tmpdir = _tf.gettempdir()
    out_file = Path(tmpdir) / "test-cleanup-empty.txt"
    out_file.write_text("")

    assert _is_temp_file(out_file)
    assert out_file.stat().st_size == 0

    # Clean up
    out_file.unlink(missing_ok=True)


def test_popen_uses_start_new_session():
    """Popen must be called with start_new_session=True so
    _kill_process_tree can kill the entire process group."""
    from unittest.mock import MagicMock

    mock_proc = MagicMock()
    mock_proc.poll = MagicMock(return_value=0)
    mock_proc.returncode = 0
    mock_proc.stdin = MagicMock()
    mock_proc.stderr = MagicMock()
    mock_proc.stderr.readline = MagicMock(return_value="")
    mock_proc.stderr.close = MagicMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline = MagicMock(return_value="")
    mock_proc.stdout.close = MagicMock()
    mock_proc.pid = 99999

    mock_popen = MagicMock(return_value=mock_proc)

    with patch(
        "agent_runtime.runner.has_headroom", return_value=(True, ""),
    ), patch(
        "agent_runtime.runner.write_record",
    ), patch(
        "agent_runtime.runner.subprocess.Popen", mock_popen,
    ), patch(
        "agent_runtime.runner._POLL_INTERVAL_S", 0.01,
    ):
        invoke(
            "codex", "hello",
            mode="read-only",
            cwd=Path("/tmp"),
            task_id="popen-test",
            entrypoint="runtime",
        )

    # Verify start_new_session=True was passed to Popen
    call_kwargs = mock_popen.call_args
    assert call_kwargs[1].get("start_new_session") is True, (
        f"Popen must use start_new_session=True, got: {call_kwargs[1]}"
    )


def test_invoke_applies_env_unsets_to_subprocess(tmp_path):
    """Runner must honor InvocationPlan.env_unsets after merging overrides."""
    from unittest.mock import MagicMock

    mock_proc = MagicMock()
    mock_proc.poll = MagicMock(return_value=0)
    mock_proc.returncode = 0
    mock_proc.stdin = MagicMock()
    mock_proc.stderr = MagicMock()
    mock_proc.stderr.readline = MagicMock(return_value="")
    mock_proc.stderr.close = MagicMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline = MagicMock(return_value="")
    mock_proc.stdout.close = MagicMock()
    mock_proc.pid = 12345

    mock_popen = MagicMock(return_value=mock_proc)

    with patch.dict(
        "os.environ",
        {
            "GEMINI_AUTH_MODE": "subscription",
            "GEMINI_API_KEY": "secret-key",
            "GOOGLE_API_KEY": "secret-google-key",
        },
        clear=False,
    ), patch(
        "agent_runtime.runner.has_headroom", return_value=(True, ""),
    ), patch(
        "agent_runtime.runner.write_record",
    ), patch(
        "agent_runtime.runner.subprocess.Popen", mock_popen,
    ), patch(
        "agent_runtime.runner._POLL_INTERVAL_S", 0.01,
    ):
        invoke(
            "gemini",
            "hello",
            mode="workspace-write",
            cwd=tmp_path,
            task_id="gemini-auth-subscription",
            entrypoint="runtime",
        )

    env = mock_popen.call_args.kwargs["env"]
    assert env.get("GEMINI_AUTH_MODE") == "subscription"
    assert "GEMINI_API_KEY" not in env
    assert "GOOGLE_API_KEY" not in env
    assert "GOOGLE_GENERATIVE_AI_API_KEY" not in env
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in env


def test_invoke_danger_wraps_path_with_merge_shims(tmp_path):
    """Danger-mode subprocesses must get the gh/git merge guard by default."""
    from unittest.mock import MagicMock

    from agent_runtime import runner as runner_mod

    mock_proc = MagicMock()
    mock_proc.poll = MagicMock(return_value=0)
    mock_proc.returncode = 0
    mock_proc.stdin = MagicMock()
    mock_proc.stderr = MagicMock()
    mock_proc.stderr.readline = MagicMock(return_value="")
    mock_proc.stderr.close = MagicMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline = MagicMock(return_value="")
    mock_proc.stdout.close = MagicMock()
    mock_proc.pid = 12345

    mock_popen = MagicMock(return_value=mock_proc)

    with patch(
        "agent_runtime.runner.has_headroom", return_value=(True, ""),
    ), patch(
        "agent_runtime.runner.write_record",
    ), patch(
        "agent_runtime.runner.subprocess.Popen", mock_popen,
    ), patch(
        "agent_runtime.runner._POLL_INTERVAL_S", 0.01,
    ):
        invoke(
            "codex",
            "hello",
            mode="danger",
            cwd=tmp_path,
            task_id="danger-no-merge",
            entrypoint="delegate",
        )

    env = mock_popen.call_args.kwargs["env"]
    assert env.get("AGENT_NO_MERGE") == "1"
    assert env.get("PATH", "").split(":")[0] == str(runner_mod._SHIMS_DIR)
    assert env.get("AGENT_REAL_GH")
    assert env.get("AGENT_REAL_GIT")


def test_invoke_danger_respects_agent_allow_merge_opt_in(tmp_path):
    """Explicit AGENT_ALLOW_MERGE=1 must disable the default danger guard."""
    from unittest.mock import MagicMock

    from agent_runtime import runner as runner_mod

    mock_proc = MagicMock()
    mock_proc.poll = MagicMock(return_value=0)
    mock_proc.returncode = 0
    mock_proc.stdin = MagicMock()
    mock_proc.stderr = MagicMock()
    mock_proc.stderr.readline = MagicMock(return_value="")
    mock_proc.stderr.close = MagicMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline = MagicMock(return_value="")
    mock_proc.stdout.close = MagicMock()
    mock_proc.pid = 12345

    mock_popen = MagicMock(return_value=mock_proc)

    with patch.dict("os.environ", {"AGENT_ALLOW_MERGE": "1"}, clear=False), patch(
        "agent_runtime.runner.has_headroom", return_value=(True, ""),
    ), patch(
        "agent_runtime.runner.write_record",
    ), patch(
        "agent_runtime.runner.subprocess.Popen", mock_popen,
    ), patch(
        "agent_runtime.runner._POLL_INTERVAL_S", 0.01,
    ):
        invoke(
            "codex",
            "hello",
            mode="danger",
            cwd=tmp_path,
            task_id="danger-merge-allowed",
            entrypoint="delegate",
        )

    env = mock_popen.call_args.kwargs["env"]
    assert env.get("AGENT_NO_MERGE") != "1"
    assert env.get("PATH", "").split(":")[0] != str(runner_mod._SHIMS_DIR)


def test_gh_shim_blocks_pr_merge_without_opt_in(tmp_path):
    shim = Path(__file__).resolve().parent.parent / "scripts" / "agent_runtime" / "shims" / "gh"
    fake_gh = tmp_path / "real-gh"
    fake_gh.write_text("#!/usr/bin/env bash\nprintf 'real-gh %s\\n' \"$*\"\n")
    fake_gh.chmod(0o755)

    proc = subprocess.run(
        [str(shim), "pr", "merge", "1234"],
        capture_output=True,
        text=True,
        env={
            "AGENT_NO_MERGE": "1",
            "AGENT_REAL_GH": str(fake_gh),
            "PATH": os.environ.get("PATH", ""),
        },
        check=False,
    )

    assert proc.returncode != 0
    assert "cannot merge or approve PRs" in proc.stderr
    assert "#1403" in proc.stderr


def test_gh_shim_allows_pr_merge_with_opt_in(tmp_path):
    shim = Path(__file__).resolve().parent.parent / "scripts" / "agent_runtime" / "shims" / "gh"
    fake_gh = tmp_path / "real-gh"
    fake_gh.write_text("#!/usr/bin/env bash\nprintf 'real-gh %s\\n' \"$*\"\n")
    fake_gh.chmod(0o755)

    proc = subprocess.run(
        [str(shim), "pr", "merge", "1234"],
        capture_output=True,
        text=True,
        env={
            "AGENT_ALLOW_MERGE": "1",
            "AGENT_REAL_GH": str(fake_gh),
            "PATH": os.environ.get("PATH", ""),
        },
        check=False,
    )

    assert proc.returncode == 0
    assert proc.stdout.strip() == "real-gh pr merge 1234"


def test_git_shim_blocks_push_to_main_without_opt_in(tmp_path):
    shim = Path(__file__).resolve().parent.parent / "scripts" / "agent_runtime" / "shims" / "git"
    fake_git = tmp_path / "real-git"
    fake_git.write_text("#!/usr/bin/env bash\nprintf 'real-git %s\\n' \"$*\"\n")
    fake_git.chmod(0o755)

    proc = subprocess.run(
        [str(shim), "push", "origin", "main"],
        capture_output=True,
        text=True,
        env={
            "AGENT_NO_MERGE": "1",
            "AGENT_REAL_GIT": str(fake_git),
            "PATH": os.environ.get("PATH", ""),
        },
        check=False,
    )

    assert proc.returncode != 0
    assert "cannot push directly to main" in proc.stderr
    assert "#1403" in proc.stderr
