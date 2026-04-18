from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.errors import RateLimitedError
from agent_runtime.result import Result
from ai_agent_bridge._cli import _handle_ask_gemini
from ai_agent_bridge._db import get_db, init_db
from ai_agent_bridge._gemini import _run_gemini_sync
from ai_agent_bridge._messaging import send_message
from batch_gemini_config import FALLBACK_MODEL, PRO_MODEL


@pytest.fixture
def bridge_db(tmp_path):
    db_path = tmp_path / "messages.db"
    with patch("ai_agent_bridge._config.DB_PATH", db_path), \
         patch("ai_agent_bridge._db.DB_PATH", db_path):
        conn = init_db()
        conn.close()
        yield db_path


def _message_to_model(message_id: int) -> str | None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT json_extract(data, '$.to_model') FROM messages WHERE id = ?",
            (message_id,),
        ).fetchone()
        assert row is not None
        return row[0]
    finally:
        conn.close()


@patch("ai_agent_bridge._gemini._route_gemini_response")
@patch("ai_agent_bridge._gemini.acknowledge")
@patch("ai_agent_bridge._gemini.runtime_invoke")
def test_run_gemini_sync_429_retries_same_model_then_falls_back_to_auto(
    mock_invoke,
    mock_acknowledge,
    mock_route_response,
    bridge_db,
):
    message_id = send_message(
        "Please review this",
        task_id="issue-1234",
        msg_type="query",
        from_llm="claude",
        to_llm="gemini",
        to_model=PRO_MODEL,
        quiet=True,
    )
    msg = {
        "id": message_id,
        "task_id": "issue-1234",
        "from": "claude",
        "to": "gemini",
        "type": "query",
        "content": "Please review this",
        "data": None,
    }

    mock_invoke.side_effect = [
        RateLimitedError("gemini", PRO_MODEL, "HTTP 429 No capacity available"),
        RateLimitedError("gemini", PRO_MODEL, "HTTP 429 No capacity available"),
        Result(
            ok=True,
            agent="gemini",
            model=FALLBACK_MODEL,
            mode="workspace-write",
            response="bridge reply",
            stderr_excerpt=None,
            duration_s=0.1,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={},
        ),
    ]

    with patch("ai_agent_bridge._gemini._is_task_locked", return_value=False), \
         patch("ai_agent_bridge._gemini._write_pid_file"), \
         patch("ai_agent_bridge._gemini._remove_pid_file"), \
         patch("ai_agent_bridge._gemini.atexit.register"):
        response = _run_gemini_sync(
            msg,
            message_id,
            PRO_MODEL,
            "bridge prompt",
            no_timeout=False,
            stdout_only=True,
            output_path=None,
            allow_write=False,
            skip_github=True,
            auth_mode=None,
        )

    invoked_models = [call.kwargs["model"] for call in mock_invoke.call_args_list]
    assert invoked_models == [PRO_MODEL, PRO_MODEL, FALLBACK_MODEL]
    assert _message_to_model(message_id) == FALLBACK_MODEL
    assert response == "[model=auto, pro-capacity-unavailable]\n\nbridge reply"
    mock_route_response.assert_called_once()
    assert mock_route_response.call_args.args[2] == FALLBACK_MODEL
    mock_acknowledge.assert_called_once_with(message_id, quiet=True)


@patch("ai_agent_bridge._gemini._route_gemini_response")
@patch("ai_agent_bridge._gemini.acknowledge")
@patch("ai_agent_bridge._gemini.runtime_invoke")
def test_run_gemini_sync_passes_auth_mode_to_runtime(
    mock_invoke,
    _mock_acknowledge,
    _mock_route_response,
    bridge_db,
):
    message_id = send_message(
        "Please review this",
        task_id="issue-1235",
        msg_type="query",
        from_llm="claude",
        to_llm="gemini",
        quiet=True,
    )
    msg = {
        "id": message_id,
        "task_id": "issue-1235",
        "from": "claude",
        "to": "gemini",
        "type": "query",
        "content": "Please review this",
        "data": None,
    }

    mock_invoke.return_value = Result(
        ok=True,
        agent="gemini",
        model=PRO_MODEL,
        mode="workspace-write",
        response="bridge reply",
        stderr_excerpt=None,
        duration_s=0.1,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        usage_record={},
    )

    with patch("ai_agent_bridge._gemini._is_task_locked", return_value=False), \
         patch("ai_agent_bridge._gemini._write_pid_file"), \
         patch("ai_agent_bridge._gemini._remove_pid_file"), \
         patch("ai_agent_bridge._gemini.atexit.register"):
        _run_gemini_sync(
            msg,
            message_id,
            PRO_MODEL,
            "bridge prompt",
            no_timeout=False,
            stdout_only=True,
            output_path=None,
            allow_write=False,
            skip_github=True,
            auth_mode="subscription",
        )

    assert mock_invoke.call_args.kwargs["tool_config"] == {"auth_mode": "subscription"}


def test_handle_ask_gemini_passes_auth_mode(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_ask_gemini(*args):
        captured["args"] = args
        return 123

    monkeypatch.setattr("ai_agent_bridge._cli.ask_gemini", _fake_ask_gemini)

    class _Args:
        content = "hello"
        task_id = "task-1"
        type = "query"
        data = None
        model = PRO_MODEL
        from_model = None
        async_mode = False
        stdout_only = False
        output_path = None
        extract = None
        skip_model_check = False
        allow_write = False
        delimiters = None
        no_github = True
        auth = "api-key"

    _handle_ask_gemini(_Args())
    assert captured["args"][-1] == "api-key"
