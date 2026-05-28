"""Tests for CursorAdapter."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.agent_runtime.adapters.cursor import CursorAdapter


@pytest.fixture
def adapter():
    return CursorAdapter()


def test_cursor_adapter_build_invocation_read_only(adapter, tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: "/usr/local/bin/agent" if x == "agent" else None)

    plan = adapter.build_invocation(
        prompt="Hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="task-123",
        session_id=None,
        tool_config={"cursor_mode": "ask"},
    )

    assert "/usr/local/bin/agent" in plan.cmd
    assert "-p" in plan.cmd
    # Regression: cursor-agent's -p takes NO argument; a literal "-" after
    # it is parsed as the positional prompt = the string "-", which causes
    # the real prompt on stdin to be ignored. Prompt delivery is stdin-only.
    assert "-" not in plan.cmd
    assert "--model" in plan.cmd
    # Default flipped from "composer-2.5" to "auto" (2026-05-28). cursor-agent
    # picks the best available model from the user's plan rather than burning
    # the per-model composer-2.5 quota every call. Pass an explicit
    # `model="composer-2.5"` only when that specific model is required.
    assert "auto" in plan.cmd
    assert "--mode" in plan.cmd
    assert "ask" in plan.cmd
    assert "--trust" in plan.cmd
    assert "--workspace" in plan.cmd
    assert str(tmp_path) in plan.cmd
    assert plan.stdin_payload == "Hello"
    assert "--yolo" not in plan.cmd
    assert "--force" not in plan.cmd


def test_cursor_adapter_build_invocation_workspace_write(adapter, tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: "/usr/local/bin/agent" if x == "agent" else None)

    plan = adapter.build_invocation(
        prompt="Fix bug",
        mode="workspace-write",
        cwd=tmp_path,
        model="composer-2.5-heavy",
        task_id="task-123",
        session_id=None,
        tool_config={
            "cursor_workspace": "/tmp/scoped",
            "approve_mcps": True,
            "sandbox": "enabled",
        },
    )

    assert "--mode" in plan.cmd
    assert "plan" in plan.cmd  # default for workspace-write
    assert "--workspace" in plan.cmd
    assert "/tmp/scoped" in plan.cmd
    assert "--approve-mcps" in plan.cmd
    assert "--sandbox" in plan.cmd
    assert "enabled" in plan.cmd
    assert "--model" in plan.cmd
    assert "composer-2.5-heavy" in plan.cmd
    assert "--yolo" not in plan.cmd


def test_cursor_adapter_build_invocation_danger(adapter, tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: "/usr/local/bin/agent" if x == "agent" else None)

    plan = adapter.build_invocation(
        prompt="Delete all",
        mode="danger",
        cwd=tmp_path,
        model=None,
        task_id="task-123",
        session_id=None,
        tool_config={},
    )

    # Danger mode: no --mode flag (cursor-agent default allows edits;
    # --mode plan blocks edits, --mode ask is read-only Q&A).
    assert "--mode" not in plan.cmd
    # MCP discipline + sandbox kept on; --yolo deliberately omitted per Phase 2 spec.
    assert "--approve-mcps" in plan.cmd
    assert "--sandbox" in plan.cmd
    assert "enabled" in plan.cmd
    assert "--yolo" not in plan.cmd
    assert "--force" not in plan.cmd


def test_cursor_adapter_no_literal_dash_argument_anywhere(adapter, tmp_path, monkeypatch):
    """Regression for the 2026-05-24 'cursor reads literal "-" as prompt' bug.

    cursor-agent's `-p`/`--print` is a boolean toggle, NOT a flag that takes
    "-" to mean "stdin". A bare "-" anywhere in argv after `-p` is parsed as
    the POSITIONAL prompt = the literal string "-". The adapter therefore
    must NEVER pass "-" as an argv element. Prompt delivery is stdin-only.

    This regression bit the option-c-plan-reference-match-gate-2026-05-24
    dispatch on the day PR #2254 merged: 14KB brief sat unread on stdin
    while cursor processed "-" as a single-char prompt and exited with
    output_chars=0, classified as rate_limited via a false-positive regex
    match in `_RATE_LIMIT_RE` against cursor's empty-prompt thinking trace.
    """
    monkeypatch.setattr("shutil.which", lambda x: "/usr/local/bin/agent" if x == "agent" else None)

    for mode in ("read-only", "workspace-write", "danger"):
        plan = adapter.build_invocation(
            prompt="real prompt content",
            mode=mode,
            cwd=tmp_path,
            model=None,
            task_id="t",
            session_id=None,
            tool_config={},
        )
        assert "-" not in plan.cmd, (
            f"mode={mode}: literal '-' found in argv {plan.cmd}; "
            "cursor-agent parses this as positional prompt = '-' string, "
            "ignoring the real prompt on stdin"
        )
        assert plan.stdin_payload == "real prompt content", (
            f"mode={mode}: stdin_payload not set to the real prompt"
        )


def test_cursor_adapter_parse_response_success(adapter):
    stdout = """
{"type": "text", "content": "I have fixed the bug."}
{"type": "tool_use", "name": "mcp__sources__search_text", "arguments": {"query": "test"}}
{"type": "text", "content": " Done."}
"""
    result = adapter.parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is True
    assert result.response == "I have fixed the bug. Done."
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0]["name"] == "mcp__sources__search_text"


def test_cursor_adapter_parse_response_rate_limited(adapter):
    stdout = ""
    stderr = "Error: 429 Too Many Requests"
    result = adapter.parse_response(
        stdout=stdout,
        stderr=stderr,
        returncode=1,
        output_file=None,
    )

    assert result.ok is False
    assert result.rate_limited is True
    assert "429" in result.stderr_excerpt


def test_cursor_adapter_parse_response_message_format(adapter):
    stdout = """
{"type": "message", "role": "assistant", "content": [{"type": "text", "text": "Hello world"}]}
"""
    result = adapter.parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is True
    assert result.response == "Hello world"
