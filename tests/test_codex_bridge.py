"""Focused tests for Codex bridge behavior."""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.result import Result
from ai_agent_bridge._cli import _handle_ask_codex
from ai_agent_bridge._codex import _codex_bridge_runtime_mode, process_for_codex
from ai_agent_bridge._messaging import detect_sender


@pytest.fixture(autouse=True)
def _isolate_usage_log(tmp_path):
    """Ensure no test writes to the real batch_state/api_usage/ log."""
    with patch("agent_runtime.usage._usage_dir", return_value=tmp_path / "api_usage"):
        yield


def test_detect_sender_codex():
    env = {k: v for k, v in os.environ.items() if k not in ("GEMINI_SESSION", "GOOGLE_API_KEY", "CLAUDE_PROJECT_DIR", "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS")}
    with patch.dict(os.environ, {**env, "CODEX_SESSION": "1"}, clear=True), \
         patch("ai_agent_bridge._messaging.Path.exists", return_value=False):
        assert detect_sender() == "codex"


def test_detect_sender_claude_beats_codex_session():
    with patch.dict(os.environ, {"CODEX_SESSION": "1", "CLAUDE_PROJECT_DIR": "/tmp/project"}, clear=True):
        assert detect_sender() == "claude"


def test_detect_sender_gemini_beats_codex_session():
    with patch.dict(os.environ, {"CODEX_SESSION": "1", "GEMINI_SESSION": "1"}, clear=True):
        assert detect_sender() == "gemini"


def test_handle_ask_codex_reads_stdin():
    args = argparse.Namespace(
        content="-",
        task_id="issue-1177",
        type="query",
        data=None,
        new_session=False,
        from_llm="gemini",
        from_model=None,
        to_model=None,
    )
    with patch("ai_agent_bridge._cli.ask_codex") as ask_codex_mock, \
         patch("sys.stdin", io.StringIO("stdin prompt")):
        _handle_ask_codex(args)
    ask_codex_mock.assert_called_once()
    assert ask_codex_mock.call_args[0][0] == "stdin prompt"


def test_codex_bridge_runtime_mode_invalid_mode_falls_back_read_only():
    with patch.dict(os.environ, {"CODEX_BRIDGE_MODE": "weird"}, clear=True):
        assert _codex_bridge_runtime_mode() == "read-only"


@patch("ai_agent_bridge._codex.acknowledge")
@patch("ai_agent_bridge._codex.send_message", return_value=99)
@patch("ai_agent_bridge._codex.set_session")
@patch("ai_agent_bridge._codex.build_codex_prompt", return_value="bridge prompt")
@patch(
    "ai_agent_bridge._codex._fetch_codex_message",
    return_value={
        "id": 7,
        "task_id": "issue-1177",
        "from": "gemini",
        "to": "codex",
        "type": "query",
        "content": "bridge content",
        "data": json.dumps({"to_model": "gpt-5.4"}),
        "timestamp": "2026-04-10T12:00:00Z",
    },
)
@patch("agent_runtime.runner.invoke")
def test_process_for_codex_invokes_runtime_with_bridge_shape(
    mock_invoke,
    mock_fetch_message,
    mock_build_prompt,
    mock_set_session,
    mock_send_message,
    mock_acknowledge,
):
    mock_invoke.return_value = Result(
        ok=True,
        agent="codex",
        model="gpt-5.4",
        mode="read-only",
        response="Codex response",
        stderr_excerpt=None,
        duration_s=1.0,
        session_id="session-123",
        rate_limited=False,
        stalled=False,
        returncode=0,
        usage_record={},
    )

    with patch.dict(os.environ, {}, clear=True):
        process_for_codex(7)

    mock_fetch_message.assert_called_once_with(7)
    mock_build_prompt.assert_called_once()
    kwargs = mock_invoke.call_args.kwargs
    assert kwargs["mode"] == "read-only"
    assert kwargs["model"] == "gpt-5.4"
    assert kwargs["entrypoint"] == "bridge"
    assert kwargs["tool_config"] is None
    assert kwargs["session_id"] is None
    mock_set_session.assert_called_once_with("issue-1177", "codex", "session-123")
    mock_send_message.assert_called_once_with(
        content="Codex response",
        task_id="issue-1177",
        msg_type="response",
        from_llm="codex",
        to_llm="gemini",
    )
    assert mock_acknowledge.call_args_list[0].args == (7,)
    assert mock_acknowledge.call_args_list[1].args == (99,)


@patch("ai_agent_bridge._codex.acknowledge")
@patch("ai_agent_bridge._codex.send_message", return_value=100)
@patch("ai_agent_bridge._codex.set_session")
@patch("ai_agent_bridge._codex.build_codex_prompt", return_value="bridge prompt")
@patch(
    "ai_agent_bridge._codex._fetch_codex_message",
    return_value={
        "id": 8,
        "task_id": "issue-1178",
        "from": "gemini",
        "to": "codex",
        "type": "query",
        "content": "bridge content",
        "data": None,
        "timestamp": "2026-04-10T12:00:00Z",
    },
)
@patch("agent_runtime.runner.invoke")
def test_process_for_codex_uses_workspace_write_mode_and_never_resumes(
    mock_invoke,
    mock_fetch_message,
    mock_build_prompt,
    mock_set_session,
    mock_send_message,
    mock_acknowledge,
):
    mock_invoke.return_value = Result(
        ok=True,
        agent="codex",
        model="gpt-5.4",
        mode="workspace-write",
        response="Codex response",
        stderr_excerpt=None,
        duration_s=1.0,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        usage_record={},
    )

    with patch.dict(os.environ, {"CODEX_BRIDGE_MODE": "workspace-write"}, clear=True):
        process_for_codex(8, new_session=False)

    mock_fetch_message.assert_called_once_with(8)
    mock_build_prompt.assert_called_once()
    kwargs = mock_invoke.call_args.kwargs
    assert kwargs["mode"] == "workspace-write"
    assert kwargs["model"] is None
    assert kwargs["entrypoint"] == "bridge"
    assert kwargs["session_id"] is None
    assert kwargs["tool_config"] is None
    mock_set_session.assert_not_called()
    mock_send_message.assert_called_once_with(
        content="Codex response",
        task_id="issue-1178",
        msg_type="response",
        from_llm="codex",
        to_llm="gemini",
    )
    assert mock_acknowledge.call_args_list[0].args == (8,)
    assert mock_acknowledge.call_args_list[1].args == (100,)
