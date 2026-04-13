"""Focused tests for Codex bridge behavior."""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.errors import AgentStalledError, RateLimitedError
from agent_runtime.result import Result
from agent_runtime.usage import _reset_rate_limit_cache_for_tests
from ai_agent_bridge._cli import _dispatch_command, _handle_ask_codex
from ai_agent_bridge._codex import (
    _codex_bridge_runtime_mode,
    _resolve_codex_bridge_timeout,
    ask_codex_chain,
    process_for_codex,
)
from ai_agent_bridge._db import get_db, init_db
from ai_agent_bridge._messaging import detect_sender, send_message


@pytest.fixture(autouse=True)
def _isolate_usage_log(tmp_path):
    """Ensure no test writes to the real batch_state/api_usage/ log."""
    _reset_rate_limit_cache_for_tests()
    with patch("agent_runtime.usage._usage_dir", return_value=tmp_path / "api_usage"):
        yield
    _reset_rate_limit_cache_for_tests()


@pytest.fixture
def bridge_db(tmp_path):
    """Use a temporary broker DB for bridge tests."""
    db_path = tmp_path / "messages.db"
    with patch("ai_agent_bridge._db.DB_PATH", db_path):
        conn = init_db()
        conn.close()
        yield db_path


def _message_acknowledged(message_id: int) -> int:
    """Return the acknowledged flag for a message."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT acknowledged FROM messages WHERE id = ?", (message_id,))
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    return int(row[0])


def _task_messages(task_id: str) -> list[sqlite3.Row]:
    """Fetch messages for a task ordered by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, from_llm, to_llm, from_model, message_type, content, acknowledged
        FROM (
            SELECT
                id,
                from_llm,
                to_llm,
                json_extract(data, '$.from_model') AS from_model,
                message_type,
                content,
                acknowledged
            FROM messages
            WHERE task_id = ?
        )
        ORDER BY id ASC
        """,
        (task_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


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
        no_timeout=False,
        chain=None,
    )
    with patch("ai_agent_bridge._cli.ask_codex") as ask_codex_mock, \
         patch("sys.stdin", io.StringIO("stdin prompt")):
        _handle_ask_codex(args)
    ask_codex_mock.assert_called_once()
    assert ask_codex_mock.call_args[0][0] == "stdin prompt"
    assert ask_codex_mock.call_args.args[-1] is False


def test_handle_ask_codex_chain_rejects_explicit_task_id():
    args = argparse.Namespace(
        content="Fix {issue_ref}",
        task_id="issue-1177",
        type="query",
        data=None,
        new_session=False,
        from_llm="gemini",
        from_model=None,
        to_model=None,
        no_timeout=False,
        chain=["1177"],
    )

    with pytest.raises(SystemExit, match="omit --task-id"):
        _handle_ask_codex(args)


def test_handle_ask_codex_requires_task_id_without_chain():
    args = argparse.Namespace(
        content="Fix #1177",
        task_id=None,
        type="query",
        data=None,
        new_session=False,
        from_llm="gemini",
        from_model=None,
        to_model=None,
        no_timeout=False,
        chain=None,
    )

    with pytest.raises(SystemExit, match="requires --task-id"):
        _handle_ask_codex(args)


def test_handle_ask_codex_chain_dispatches_through_helper():
    args = argparse.Namespace(
        content="Fix {issue_ref}",
        task_id=None,
        type="query",
        data=None,
        new_session=False,
        from_llm="gemini",
        from_model=None,
        to_model=None,
        no_timeout=True,
        chain=["1177", "#1178"],
    )

    with patch("ai_agent_bridge._cli.ask_codex_chain") as ask_codex_chain_mock:
        _handle_ask_codex(args)

    ask_codex_chain_mock.assert_called_once_with(
        "Fix {issue_ref}",
        ["1177", "#1178"],
        "query",
        None,
        False,
        "gemini",
        None,
        None,
        True,
    )


def test_ask_codex_chain_dispatches_issues_sequentially():
    with patch("ai_agent_bridge._codex.ask_codex", side_effect=[11, 12]) as ask_codex_mock:
        message_ids = ask_codex_chain(
            "Fix {issue_ref} via {task_id}",
            ["1177", "#1178", "issue-1177"],
            no_timeout=True,
        )

    assert message_ids == [11, 12]
    assert ask_codex_mock.call_count == 2
    assert ask_codex_mock.call_args_list[0].args == (
        "Fix #1177 via issue-1177",
        "issue-1177",
        "query",
        None,
        False,
        "gemini",
        None,
        None,
        True,
    )
    assert ask_codex_mock.call_args_list[1].args == (
        "Fix #1178 via issue-1178",
        "issue-1178",
        "query",
        None,
        False,
        "gemini",
        None,
        None,
        True,
    )


def test_ask_codex_chain_prefixes_issue_context_without_placeholders():
    with patch("ai_agent_bridge._codex.ask_codex", return_value=11) as ask_codex_mock:
        ask_codex_chain("Review and fix the issue.", ["1177"])

    assert ask_codex_mock.call_args.args[0] == (
        "GitHub issue #1177 (issue-1177).\n\nReview and fix the issue."
    )


def test_resolve_codex_bridge_timeout_defaults_to_normal_timeout():
    with patch.dict(os.environ, {}, clear=True):
        assert _resolve_codex_bridge_timeout() == 900


def test_resolve_codex_bridge_timeout_honors_env_override():
    with patch.dict(os.environ, {"CODEX_BRIDGE_TIMEOUT": "120"}, clear=True):
        assert _resolve_codex_bridge_timeout() == 120


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
    assert kwargs["hard_timeout"] == 900
    assert kwargs["stall_timeout"] == 600
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
    assert kwargs["hard_timeout"] == 900
    assert kwargs["stall_timeout"] == 600
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


def test_process_for_codex_short_circuits_when_no_headroom(bridge_db):
    task_id = "issue-1183-short-circuit"
    message_id = send_message(
        "Please review the bridge",
        task_id=task_id,
        msg_type="query",
        from_llm="gemini",
        to_llm="codex",
        quiet=True,
    )

    with patch(
        "ai_agent_bridge._codex.has_codex_headroom",
        return_value=(False, "rate_limited 30s ago"),
    ), patch(
        "ai_agent_bridge._codex.build_codex_prompt",
    ) as mock_prompt, patch(
        "agent_runtime.runner.invoke",
    ) as mock_invoke:
        process_for_codex(message_id)

    mock_prompt.assert_not_called()
    mock_invoke.assert_not_called()
    assert _message_acknowledged(message_id) == 0

    rows = _task_messages(task_id)
    assert len(rows) == 2
    reply = rows[1]
    assert reply[1] == "codex"
    assert reply[2] == "gemini"
    assert reply[3] == "codex-bridge-rate-limited"
    assert reply[4] == "error"
    assert "remains in Codex's inbox" in reply[5]
    assert int(reply[6]) == 1


def test_rate_limit_error_defers_message(bridge_db):
    task_id = "issue-1183-rate-limit"
    message_id = send_message(
        "Please retry later",
        task_id=task_id,
        msg_type="query",
        from_llm="gemini",
        to_llm="codex",
        quiet=True,
    )

    with patch(
        "ai_agent_bridge._codex.has_codex_headroom",
        return_value=(True, ""),
    ), patch(
        "ai_agent_bridge._codex.build_codex_prompt",
        return_value="bridge prompt",
    ), patch(
        "agent_runtime.runner.invoke",
        side_effect=RateLimitedError("codex", "gpt-5.4", "quota exceeded"),
    ):
        process_for_codex(message_id)

    assert _message_acknowledged(message_id) == 0

    rows = _task_messages(task_id)
    assert len(rows) == 2
    reply = rows[1]
    assert reply[3] == "codex-bridge-rate-limited"
    assert "Sender should NOT retry manually." in reply[5]
    assert int(reply[6]) == 1


def test_other_errors_still_ack_inbound(bridge_db):
    task_id = "issue-1183-stalled"
    message_id = send_message(
        "Please handle stall",
        task_id=task_id,
        msg_type="query",
        from_llm="gemini",
        to_llm="codex",
        quiet=True,
    )

    with patch(
        "ai_agent_bridge._codex.has_codex_headroom",
        return_value=(True, ""),
    ), patch(
        "ai_agent_bridge._codex.build_codex_prompt",
        return_value="bridge prompt",
    ), patch(
        "agent_runtime.runner.invoke",
        side_effect=AgentStalledError("codex", 600, 601.0),
    ):
        process_for_codex(message_id)

    assert _message_acknowledged(message_id) == 1

    rows = _task_messages(task_id)
    assert len(rows) == 2
    reply = rows[1]
    assert reply[3] == "codex-bridge-error"
    assert "[Bridge Error] Codex CLI failed:" in reply[5]
    assert int(reply[6]) == 1


def test_codex_usage_cli_reports_counts(capsys, tmp_path):
    usage_dir = tmp_path / "api_usage"
    usage_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    usage_file = usage_dir / f"usage_codex-bridge_{today}.jsonl"
    now = datetime.now(UTC)
    records = [
        {
            "ts": (now - timedelta(minutes=3)).isoformat(),
            "agent": "codex",
            "entrypoint": "bridge",
            "model": "gpt-5.4",
            "mode": "read-only",
            "duration_s": 12.3,
            "outcome": "ok",
            "rate_limited": False,
            "stalled": False,
        },
        {
            "ts": (now - timedelta(minutes=2)).isoformat(),
            "agent": "codex",
            "entrypoint": "bridge",
            "model": "gpt-5.4",
            "mode": "read-only",
            "duration_s": 8.0,
            "outcome": "ok",
            "rate_limited": False,
            "stalled": False,
        },
        {
            "ts": (now - timedelta(minutes=1)).isoformat(),
            "agent": "codex",
            "entrypoint": "bridge",
            "model": "gpt-5.4",
            "mode": "read-only",
            "duration_s": 0.0,
            "outcome": "rate_limited",
            "rate_limited": True,
            "stalled": False,
            "stderr_excerpt": "pre-call headroom check",
        },
    ]
    usage_file.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )

    args = argparse.Namespace(
        command="codex-usage",
        window="5h",
        entrypoint="all",
        json=False,
    )
    _dispatch_command(args)

    out = capsys.readouterr().out
    assert "Total calls: 3" in out
    assert re.search(r"ok\s+2", out)
    assert re.search(r"rate_limited\s+1", out)
