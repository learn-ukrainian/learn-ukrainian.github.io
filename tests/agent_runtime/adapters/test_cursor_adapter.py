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
    assert "-" in plan.cmd
    assert "--model" in plan.cmd
    assert "composer-2.5" in plan.cmd
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
        tool_config={"cursor_mode": "ask"},
    )

    assert "--mode" in plan.cmd
    assert "ask" in plan.cmd
    assert "--approve-mcps" in plan.cmd
    assert "--yolo" not in plan.cmd


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
