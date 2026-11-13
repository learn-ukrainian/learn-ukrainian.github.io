from __future__ import annotations

import sqlite3
from unittest.mock import patch

import pytest
from lu_machinery.agent_runtime.errors import RateLimitedError
from lu_machinery.agent_runtime.result import Result
from lu_machinery.ai_agent_bridge import _channels, _db, _inbox


@pytest.fixture(autouse=True)
def isolate_db(tmp_path):
    db_file = tmp_path / "messages.db"
    with patch("lu_machinery.ai_agent_bridge._config.DB_PATH", db_file):
        _db.init_db()
        yield db_file


def _delivery_rows(message_id: str) -> list[sqlite3.Row]:
    conn = _db.get_db()
    try:
        return conn.execute(
            """
            SELECT delivery_id, status, attempt_count, retry_after, last_error_kind
            FROM deliveries
            WHERE message_id = ?
            ORDER BY delivery_id
            """,
            (message_id,),
        ).fetchall()
    finally:
        conn.close()


def _make_thread(
    agent: str,
    *,
    channel: str = "topic",
    count: int = 1,
) -> list[dict[str, object]]:
    if _channels.get_channel(channel) is None:
        _channels.create_channel(channel)

    messages: list[dict[str, object]] = []
    parent_id: str | None = None
    for index in range(count):
        post = _channels.post(
            channel,
            "user",
            f"message-{index + 1}",
            to_agents=[agent],
            parent_id=parent_id,
            auto_snapshot=False,
        )
        messages.append(post)
        parent_id = str(post["message_id"])
    return messages


def _ok_result(
    agent: str,
    *,
    model: str = "test-model",
    ok: bool = True,
    response: str = "bridge reply",
    stderr_excerpt: str | None = None,
    rate_limited: bool = False,
    returncode: int | None = 0,
    session_id: str | None = None,
) -> Result:
    return Result(
        ok=ok,
        agent=agent,
        model=model,
        mode="read-only",
        response=response,
        stderr_excerpt=stderr_excerpt,
        duration_s=0.1,
        session_id=session_id,
        rate_limited=rate_limited,
        stalled=False,
        returncode=returncode,
        usage_record={},
    )


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_single_thread_single_delivery(mock_invoke):
    thread = _make_thread("claude", count=1)
    mock_invoke.return_value = _ok_result("claude")

    summary = _inbox.run_inbox("claude")

    assert summary.deliveries_delivered == 1
    assert summary.replies_posted == 1
    assert mock_invoke.call_count == 1
    assert mock_invoke.call_args.kwargs["mode"] == "read-only"
    assert mock_invoke.call_args.kwargs["initiator"] == "user"
    assert mock_invoke.call_args.kwargs["tool_config"]["discussion_readonly"] is True
    delivered = _delivery_rows(str(thread[0]["message_id"]))[0]
    assert delivered["status"] == "delivered"
    messages = _channels.read("topic", thread_id=str(thread[0]["thread_id"]))
    assert len(messages) == 2
    assert messages[-1]["from_agent"] == "claude"
    assert messages[-1]["parent_id"] == thread[0]["message_id"]


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_codex_cold_call_persists_runtime_session(mock_invoke):
    thread = _make_thread("codex", count=1)
    mock_invoke.return_value = _ok_result(
        "codex",
        session_id="codex-session-one",
    )

    summary = _inbox.run_inbox("codex")

    assert summary.deliveries_delivered == 1
    assert mock_invoke.call_args.kwargs["session_id"] is None
    task_id = _inbox._thread_session_key("topic", str(thread[0]["thread_id"]))
    assert _inbox._get_session_id(task_id, "codex") == "codex-session-one"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_codex_same_thread_resumes_with_unseen_only_prompt(mock_invoke):
    thread = _make_thread("codex", count=1)
    mock_invoke.return_value = _ok_result(
        "codex",
        session_id="codex-session-one",
    )
    _inbox.run_inbox("codex")

    follow_up = _channels.post(
        "topic",
        "user",
        "message-2",
        to_agents=["codex"],
        parent_id=str(thread[0]["message_id"]),
        auto_snapshot=False,
    )
    mock_invoke.reset_mock()
    mock_invoke.return_value = _ok_result("codex", session_id="codex-session-one")

    summary = _inbox.run_inbox("codex")

    assert summary.deliveries_delivered == 1
    assert mock_invoke.call_args.kwargs["session_id"] == "codex-session-one"
    prompt = mock_invoke.call_args.args[1]
    assert "Continue the existing bridge session" in prompt
    assert "message-2" in prompt
    assert "message-1" not in prompt
    assert str(follow_up["message_id"]) not in prompt


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_codex_sessions_are_isolated_by_thread(mock_invoke):
    first = _make_thread("codex", channel="first", count=1)
    second = _make_thread("codex", channel="second", count=1)
    first_task_id = _inbox._thread_session_key("first", str(first[0]["thread_id"]))
    _inbox._set_session_id(first_task_id, "codex", "first-session")
    mock_invoke.return_value = _ok_result("codex", session_id="second-session")

    summary = _inbox.run_inbox("codex")

    assert summary.threads_processed == 2
    calls_by_channel = {
        "first" if "#first" in call.args[1] else "second": call
        for call in mock_invoke.call_args_list
    }
    assert calls_by_channel["first"].kwargs["session_id"] == "first-session"
    assert calls_by_channel["second"].kwargs["session_id"] is None
    second_task_id = _inbox._thread_session_key("second", str(second[0]["thread_id"]))
    assert _inbox._get_session_id(second_task_id, "codex") == "second-session"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_failed_codex_result_does_not_overwrite_session(mock_invoke):
    thread = _make_thread("codex", count=1)
    task_id = _inbox._thread_session_key("topic", str(thread[0]["thread_id"]))
    _inbox._set_session_id(task_id, "codex", "existing-session")
    mock_invoke.return_value = _ok_result(
        "codex",
        ok=False,
        response="",
        stderr_excerpt="backend failed",
        session_id="unexpected-session",
        returncode=1,
    )

    _inbox.run_inbox("codex")

    assert mock_invoke.call_args.kwargs["session_id"] == "existing-session"
    assert _inbox._get_session_id(task_id, "codex") == "existing-session"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_single_thread_three_deliveries_coalesces(mock_invoke):
    thread = _make_thread("claude", count=3)
    mock_invoke.return_value = _ok_result("claude")

    summary = _inbox.run_inbox("claude")

    assert summary.deliveries_delivered == 3
    assert summary.replies_posted == 1
    assert mock_invoke.call_count == 1
    rows = []
    for message in thread:
        rows.extend(_delivery_rows(str(message["message_id"])))
    assert all(row["status"] == "delivered" for row in rows)
    messages = _channels.read("topic", thread_id=str(thread[0]["thread_id"]))
    assert len(messages) == 4
    assert messages[-1]["parent_id"] == thread[-1]["message_id"]


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_thread_tool_error_fails_only_that_thread(mock_invoke):
    first = _make_thread("claude", count=1)
    second = _make_thread("claude", count=1)
    mock_invoke.side_effect = [RuntimeError("tool exploded"), _ok_result("claude")]

    summary = _inbox.run_inbox("claude")

    assert summary.deliveries_failed == 1
    assert summary.deliveries_delivered == 1
    assert summary.aborted is False
    assert mock_invoke.call_count == 2
    first_row = _delivery_rows(str(first[0]["message_id"]))[0]
    second_row = _delivery_rows(str(second[0]["message_id"]))[0]
    assert first_row["status"] == "failed"
    assert first_row["last_error_kind"] == "tool_error"
    assert second_row["status"] == "delivered"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_rate_limit_releases_and_aborts(mock_invoke):
    first = _make_thread("claude", count=1)
    second = _make_thread("claude", count=1)
    mock_invoke.side_effect = RateLimitedError("claude", "test-model", "quota hit")

    summary = _inbox.run_inbox("claude")

    assert summary.aborted is True
    assert summary.deliveries_released == 1
    assert mock_invoke.call_count == 1
    first_row = _delivery_rows(str(first[0]["message_id"]))[0]
    second_row = _delivery_rows(str(second[0]["message_id"]))[0]
    assert first_row["status"] == "pending"
    assert first_row["retry_after"] is not None
    assert first_row["last_error_kind"] == "rate_limited"
    # attempt_count stays at 1 (not decremented) — Gemini c2-review r1 BLOCKER:
    # net-zero attempts (claim +1, release -1) creates an infinite retry loop
    # if the provider stays down. The agent WAS attempted (it just hit a
    # provider-side fault), so the attempt is real. Eventually a genuinely-
    # broken provider exhausts DEFAULT_MAX_DELIVERY_ATTEMPTS and the delivery
    # reaches terminal `failed`, which is correct.
    assert first_row["attempt_count"] == 1
    assert second_row["status"] == "pending"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_until_idle_false_stops_after_one_thread(mock_invoke):
    first = _make_thread("claude", count=1)
    second = _make_thread("claude", count=1)
    mock_invoke.return_value = _ok_result("claude")

    summary = _inbox.run_inbox("claude", until_idle=False)

    assert summary.threads_processed == 1
    assert summary.deliveries_delivered == 1
    assert mock_invoke.call_count == 1
    assert _delivery_rows(str(first[0]["message_id"]))[0]["status"] == "delivered"
    assert _delivery_rows(str(second[0]["message_id"]))[0]["status"] == "pending"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_max_messages_caps_deliveries(mock_invoke):
    first = _make_thread("claude", count=1)
    second = _make_thread("claude", count=2)
    mock_invoke.return_value = _ok_result("claude")

    summary = _inbox.run_inbox("claude", max_messages=1)

    assert summary.deliveries_claimed == 1
    assert summary.deliveries_delivered == 1
    assert mock_invoke.call_count == 1
    assert _delivery_rows(str(first[0]["message_id"]))[0]["status"] == "delivered"
    second_rows = []
    for message in second:
        second_rows.extend(_delivery_rows(str(message["message_id"])))
    assert all(row["status"] == "pending" for row in second_rows)


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_max_messages_soft_cap_first_thread(mock_invoke):
    """Regression: Gemini c2-review r1 BLOCKER — queue deadlock.

    If the oldest pending thread has MORE deliveries than max_messages, the
    original code returned (None, True) and broke the loop without processing
    anything. Same thread blocked every subsequent run forever.

    Fix: max_messages is a SOFT cap that never applies to the FIRST claim
    of a run. Subsequent claims still respect the budget so a single run
    can't blow past max_messages by an unbounded amount.
    """
    thread = _make_thread("claude", count=3)
    mock_invoke.return_value = _ok_result("claude")

    summary = _inbox.run_inbox("claude", max_messages=1)

    # All 3 deliveries from the oldest thread processed despite max_messages=1.
    assert summary.threads_processed == 1
    assert summary.deliveries_claimed == 3
    assert summary.deliveries_delivered == 3
    assert mock_invoke.call_count == 1
    for message in thread:
        assert _delivery_rows(str(message["message_id"]))[0]["status"] == "delivered"
