from __future__ import annotations

import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.result import Result
from ai_agent_bridge import _channels, _cli, _db


@pytest.fixture(autouse=True)
def isolate_db(tmp_path):
    db_file = tmp_path / "messages.db"
    with patch("ai_agent_bridge._config.DB_PATH", db_file), \
         patch("ai_agent_bridge._db.DB_PATH", db_file):
        _db.init_db()
        yield db_file


def _run_cli(argv: list[str]) -> int:
    with patch.object(sys, "argv", ["ab", *argv]):
        try:
            _cli.main()
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 0
    return 0


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


def _set_message_created_at(message_id: str, created_at: str) -> None:
    conn = _db.get_db()
    try:
        conn.execute(
            "UPDATE channel_messages SET created_at = ? WHERE message_id = ?",
            (created_at, message_id),
        )
        conn.commit()
    finally:
        conn.close()


def _delivery_statuses() -> list[sqlite3.Row]:
    conn = _db.get_db()
    try:
        return conn.execute(
            """
            SELECT d.status, d.to_agent, cm.body
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            ORDER BY cm.created_at ASC, d.delivery_id ASC
            """
        ).fetchall()
    finally:
        conn.close()


def _reply_deliveries() -> list[sqlite3.Row]:
    conn = _db.get_db()
    try:
        return conn.execute(
            """
            SELECT cm.from_agent, cm.parent_id, d.to_agent, d.status, d.delivered_at
            FROM channel_messages cm
            JOIN deliveries d ON d.message_id = cm.message_id
            WHERE cm.kind = 'reply'
            ORDER BY cm.from_agent ASC, d.to_agent ASC
            """
        ).fetchall()
    finally:
        conn.close()


def _ok_result(agent: str) -> Result:
    return Result(
        ok=True,
        agent=agent,
        model="test-model",
        mode="read-only",
        response=f"{agent} reply",
        stderr_excerpt=None,
        duration_s=0.1,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        usage_record={},
    )


def test_inbox_show_empty(capsys):
    exit_code = _run_cli(["inbox", "show", "claude"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "claude inbox:" in captured.out
    assert "pending:    0" in captured.out
    assert "processing: 0" in captured.out
    assert "failed (last 24h): 0" in captured.out
    assert "    (none)" in captured.out


@patch("agent_runtime.runner.invoke")
def test_discuss_replies_create_delivered_reply_deliveries(mock_invoke, monkeypatch, capsys):
    _channels.create_channel("shared")
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)

    def _discuss_result(agent: str, *_args, **_kwargs) -> Result:
        return Result(
            ok=True,
            agent=agent,
            model="test-model",
            mode="read-only",
            response=f"{agent} discuss reply [AGREE]",
            stderr_excerpt=None,
            duration_s=0.1,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={},
        )

    mock_invoke.side_effect = _discuss_result

    exit_code = _run_cli(
        ["discuss", "shared", "topic", "--with", "claude,codex", "--max-rounds", "1"]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "✅ converged at round 1" in captured.out

    reply_deliveries = _reply_deliveries()
    assert len(reply_deliveries) == 2
    assert {
        (row["from_agent"], row["to_agent"], row["status"])
        for row in reply_deliveries
    } == {
        ("claude", "codex", "delivered"),
        ("codex", "claude", "delivered"),
    }
    assert all(row["delivered_at"] is not None for row in reply_deliveries)
    assert all(row["parent_id"] is not None for row in reply_deliveries)


def test_inbox_show_with_pending_and_failed(capsys):
    _channels.create_channel("topic")
    first = _channels.post("topic", "user", "first pending", to_agents=["claude"], auto_snapshot=False)
    second = _channels.post("topic", "user", "second pending", to_agents=["claude"], auto_snapshot=False)
    third = _channels.post("topic", "user", "third pending", to_agents=["claude"], auto_snapshot=False)
    failed = _channels.post("topic", "user", "failed message", to_agents=["claude"], auto_snapshot=False)
    _channels.mark_delivery(failed["delivery_ids"][0], "failed", error="boom")
    old_ts = (datetime.now(UTC) - timedelta(minutes=12)).isoformat()
    _set_message_created_at(str(first["message_id"]), old_ts)

    exit_code = _run_cli(["inbox", "show", "claude"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "pending:    3 (oldest 12m ago)" in captured.out
    assert "failed (last 24h): 1" in captured.out
    assert "[topic/" in captured.out
    assert 'user → "first pending"' in captured.out
    assert second["message_id"] != third["message_id"]


@patch("ai_agent_bridge._inbox.runtime_invoke")
def test_inbox_run_once_processes_one_thread(mock_invoke, capsys):
    first = _make_thread("claude", count=1)
    second = _make_thread("claude", count=1)
    mock_invoke.return_value = _ok_result("claude")

    exit_code = _run_cli(["inbox", "run", "claude", "--once"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "processed: 1 deliveries | 1 threads | 0 failed | duration:" in captured.out
    statuses = _delivery_statuses()
    assert statuses[0]["status"] == "delivered"
    assert statuses[1]["status"] == "pending"
    assert mock_invoke.call_count == 1
    assert first[0]["thread_id"] != second[0]["thread_id"]


@patch("ai_agent_bridge._inbox.runtime_invoke")
def test_sync_all_iterates_known_agents(mock_invoke, capsys):
    for agent in _channels.VALID_AGENTS:
        _make_thread(agent, channel=f"{agent}-topic", count=1)
    mock_invoke.side_effect = [_ok_result(agent) for agent in _channels.VALID_AGENTS]

    exit_code = _run_cli(["sync", "--all"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert mock_invoke.call_count == len(_channels.VALID_AGENTS)
    assert [call.args[0] for call in mock_invoke.call_args_list] == list(_channels.VALID_AGENTS)
    assert captured.out.count("processed: 1 deliveries | 1 threads | 0 failed | duration:") == len(
        _channels.VALID_AGENTS
    )


def test_backlog_banner_triggers_for_old_pending_delivery(monkeypatch, capsys):
    thread = _make_thread("codex", count=1)
    monkeypatch.setenv("AB_BACKLOG_WARN_HOURS", "2")
    old_ts = (datetime.now(UTC) - timedelta(hours=6, minutes=12)).isoformat()
    _set_message_created_at(str(thread[0]["message_id"]), old_ts)

    exit_code = _run_cli(["inbox", "show", "claude"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "⚠️  codex has 1 pending deliveries (oldest 6h12m)." in captured.err
    assert "Run 'ab inbox run codex' to drain." in captured.err


def test_backlog_banner_does_not_trigger_for_fresh_pending_delivery(monkeypatch, capsys):
    _make_thread("codex", count=1)
    monkeypatch.setenv("AB_BACKLOG_WARN_HOURS", "2")

    exit_code = _run_cli(["inbox", "show", "claude"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""


@patch("ai_agent_bridge._inbox.runtime_invoke")
def test_post_model_flag_round_trips_to_gemini_invocation(mock_invoke, capsys):
    _channels.create_channel("topic")
    mock_invoke.return_value = _ok_result("gemini")

    post_exit = _run_cli(
        [
            "post",
            "topic",
            "hello gemini",
            "--to",
            "gemini",
            "--model",
            "gemini-3-flash-preview",
            "--no-snapshot",
        ]
    )
    message = _channels.read("topic")[0]
    delivery = _channels.deliveries_for_message(str(message["message_id"]))[0]
    run_exit = _run_cli(["inbox", "run", "gemini", "--once"])

    assert post_exit == 0
    assert run_exit == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert delivery["to_model"] == "gemini-3-flash-preview"
    assert mock_invoke.call_args.kwargs["model"] == "gemini-3-flash-preview"


@patch("ai_agent_bridge._inbox.runtime_invoke")
def test_inbox_run_deadline_flag_overrides_worker_timeout(mock_invoke, capsys):
    _make_thread("claude", count=1)
    mock_invoke.return_value = _ok_result("claude")

    exit_code = _run_cli(["inbox", "run", "claude", "--once", "--deadline", "1800"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert mock_invoke.call_args.kwargs["hard_timeout"] == 1800


@patch("ai_agent_bridge._inbox.runtime_invoke")
def test_post_deadline_flag_stores_delivery_override_and_worker_uses_it(mock_invoke, capsys):
    _channels.create_channel("topic")
    mock_invoke.return_value = _ok_result("codex")

    post_exit = _run_cli(
        [
            "post",
            "topic",
            "hello codex",
            "--to",
            "codex",
            "--deadline",
            "1200",
            "--no-snapshot",
        ]
    )
    run_exit = _run_cli(["inbox", "run", "codex", "--once"])

    assert post_exit == 0
    assert run_exit == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    message = _channels.read("topic")[0]
    delivery = _channels.deliveries_for_message(str(message["message_id"]))[0]
    assert delivery["deadline_seconds"] == 1200
    assert mock_invoke.call_args.kwargs["hard_timeout"] == 1200


def test_help_includes_model_and_deadline_flags(capsys):
    parser = _cli._build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["post", "--help"])
    post_help = capsys.readouterr()
    assert "--model" in post_help.out
    assert "--deadline" in post_help.out

    with pytest.raises(SystemExit):
        parser.parse_args(["inbox", "run", "--help"])
    inbox_help = capsys.readouterr()
    assert "--deadline" in inbox_help.out
