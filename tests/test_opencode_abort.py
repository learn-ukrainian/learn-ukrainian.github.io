"""Hermetic regression tests for opencode turn classification, failure handling, and standing notice (#5932)."""

from unittest.mock import MagicMock, patch

import pytest

from scripts.agent_runtime.adapters.glm import GlmAdapter
from scripts.ai_agent_bridge._db import get_db
from scripts.ai_agent_bridge._opencode import (
    STANDING_TOOLLESS_NOTICE,
    _run_opencode,
    ask_opencode,
    read_opencode_turn_status,
)


def test_read_opencode_turn_status_completed():
    ndjson = (
        '{"type":"text","part":{"type":"text","text":"Hello world"}}\n'
        '{"type":"step_finish","part":{"type":"step-finish","reason":"stop"}}\n'
    )
    status = read_opencode_turn_status(ndjson)
    assert status.outcome == "completed"
    assert status.reason == "stop"


def test_read_opencode_turn_status_permission_rejected():
    ndjson = (
        '{"type":"text","part":{"type":"text","text":"I will execute bash command"}}\n'
        '{"type":"tool","part":{"tool":"bash","state":{"status":"rejected"}}}\n'
    )
    status = read_opencode_turn_status(ndjson)
    assert status.outcome == "permission_rejected"
    assert status.cancellation_category == "permission_rejected"
    assert "tool call bash permission cancelled" in status.reason


def test_read_opencode_turn_status_aborted():
    ndjson = (
        '{"type":"text","part":{"type":"text","text":"Starting work..."}}\n'
        '{"type":"error","error":{"name":"MessageAbortedError","data":{"message":"User aborted session"}}}\n'
    )
    status = read_opencode_turn_status(ndjson)
    assert status.outcome == "aborted"
    assert status.cancellation_category == "aborted"
    assert "User aborted session" in status.reason


def test_read_opencode_turn_status_errored():
    ndjson = (
        '{"type":"text","part":{"type":"text","text":"Processing..."}}\n'
        '{"type":"step_finish","part":{"reason":"length"}}\n'
    )
    status = read_opencode_turn_status(ndjson)
    assert status.outcome == "errored"
    assert status.cancellation_category == "length"


def test_read_opencode_turn_status_trace_unavailable():
    status = read_opencode_turn_status("")
    assert status.outcome == "trace_unavailable"
    assert status.cancellation_category == "trace_unavailable"


def test_read_opencode_turn_status_pure_json_reply_completes():
    """A model reply that is itself a bare JSON object (no opencode event
    signature keys) is CONTENT, not a missing trace — the ask must succeed."""
    status = read_opencode_turn_status('{"verdict": "MERGE", "findings": []}')
    assert status.outcome == "completed"


def test_read_opencode_turn_status_null_error_key_is_benign():
    """`error: null` on a normal event must not mark the turn errored."""
    ndjson = '{"type":"text","part":{"type":"text","text":"hi"},"error":null}\n'
    status = read_opencode_turn_status(ndjson)
    assert status.outcome == "completed"


def test_run_opencode_attaches_standing_notice_when_agent_chat():
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value="/fake/opencode"):
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout='{"type":"text","part":{"text":"hi"}}', stderr="")
            _run_opencode("hello", "deepseek/deepseek-v4.1-flash", agent="chat")
            argv = run_mock.call_args[0][0]
            assert "--agent" in argv
            assert "chat" in argv
            assert STANDING_TOOLLESS_NOTICE in argv[-1]


def test_opencode_permission_abort_fails_ask_loud_and_writes_sidecar(
    tmp_path, monkeypatch, isolated_bridge_db
):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("OPENCODE_HOME", str(tmp_path / ".local" / "share"))

    permission_rejected_ndjson = (
        '{"type":"text","part":{"type":"text","text":"I will run rm -rf /"}}\n'
        '{"type":"tool","part":{"tool":"bash","state":{"status":"rejected"}}}\n'
    )

    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value="/fake/opencode"):
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout=permission_rejected_ndjson, stderr="")
            with pytest.raises(SystemExit, match=r"\[Bridge Error\] opencode turn aborted"):
                ask_opencode("Run a script", "t-5932", from_llm="claude", model="deepseek/deepseek-v4.1-flash")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, status FROM messages WHERE task_id = 't-5932' AND to_llm = 'opencode' ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    assert row is not None
    ask_id, status = row
    assert status.startswith("failed:")
    assert "opencode turn aborted" in status

    cursor.execute("SELECT message_type, content FROM messages WHERE task_id = 't-5932'")
    rows = cursor.fetchall()
    conn.close()

    error_msgs = [r for r in rows if r[0] == "error"]
    response_msgs = [r for r in rows if r[0] == "response"]

    assert len(error_msgs) >= 1
    assert len(response_msgs) == 0
    assert "[Bridge Error]" in error_msgs[0][1]

    from scripts.ai_agent_bridge._ask_lifecycle import _is_clean_terminal_record
    assert _is_clean_terminal_record(ask_id) is False


def test_glm_adapter_parse_response_incomplete_turn():
    adapter = GlmAdapter()
    ndjson = (
        '{"type":"text","part":{"type":"text","text":"Analyzing..."}}\n'
        '{"type":"tool","part":{"tool":"bash","state":{"status":"rejected"}}}\n'
    )
    res = adapter.parse_response(stdout=ndjson, stderr="", returncode=0)
    assert res.ok is False
    assert res.response == ""
    assert "opencode turn aborted (permission_rejected" in res.stderr_excerpt
