from __future__ import annotations

import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.result import Result
from ai_agent_bridge import _channels, _channels_cli, _cli, _db


def test_post_preflight_warns_for_large_body():
    warning = _channels_cli._post_preflight_warning(body="x" * 8001, mode="workspace-write")

    assert warning == (
        "[PREFLIGHT] brief looks large (8001 chars, 0 files mentioned). "
        "Consider --deadline 1800 or splitting."
    )


def test_post_preflight_warns_for_many_file_mentions():
    body = "\n".join(
        [
            "scripts/a.py",
            "tests/test_a.py",
            "pkg/worker.py",
            "app/api/router.py",
            "foo/bar.py",
        ]
    )

    warning = _channels_cli._post_preflight_warning(body=body, mode="workspace-write")

    assert warning == (
        f"[PREFLIGHT] brief looks large ({len(body)} chars, 5 files mentioned). "
        "Consider --deadline 1800 or splitting."
    )


def test_post_preflight_warns_for_multi_step_markers():
    body = "Fix this and then update that."
    warning = _channels_cli._post_preflight_warning(body=body, mode="workspace-write")

    assert warning == (
        f"[PREFLIGHT] brief looks large ({len(body)} chars, 0 files mentioned). "
        "Consider --deadline 1800 or splitting."
    )


def test_post_preflight_skips_non_workspace_write_mode():
    warning = _channels_cli._post_preflight_warning(
        body="scripts/a.py\ntests/test_a.py\npkg/worker.py\napp/api/router.py\nfoo/bar.py",
        mode="read-only",
    )

    assert warning is None


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


def _oldest_pending_delivery_id(agent: str) -> str | None:
    conn = _db.get_db()
    try:
        row = conn.execute(
            """
            SELECT d.delivery_id
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE d.to_agent = ? AND d.status = 'pending'
            ORDER BY cm.created_at ASC, d.delivery_id ASC
            LIMIT 1
            """,
            (agent,),
        ).fetchone()
    finally:
        conn.close()
    return str(row["delivery_id"]) if row is not None else None


def _install_fake_inbox_module(monkeypatch, run_inbox) -> None:
    fake_inbox_module = ModuleType("ai_agent_bridge._inbox")
    fake_inbox_module.run_inbox = run_inbox
    monkeypatch.setitem(sys.modules, "ai_agent_bridge._inbox", fake_inbox_module)


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


def test_inbox_run_once_processes_one_thread(monkeypatch, capsys):
    first = _make_thread("claude", count=1)
    second = _make_thread("claude", count=1)

    calls: list[tuple[str, dict[str, object]]] = []

    def _fake_run_inbox(agent: str, **kwargs):
        calls.append((agent, kwargs))
        delivery_id = _oldest_pending_delivery_id(agent)
        assert delivery_id is not None
        _channels.mark_delivery(delivery_id, "delivered")
        return SimpleNamespace(
            deliveries_claimed=1,
            threads_processed=1,
            deliveries_failed=0,
            aborted=False,
        )

    _install_fake_inbox_module(monkeypatch, _fake_run_inbox)

    exit_code = _run_cli(["inbox", "run", "claude", "--once"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "processed: 1 deliveries | 1 threads | 0 failed | duration:" in captured.out
    statuses = _delivery_statuses()
    assert statuses[0]["status"] == "delivered"
    assert statuses[1]["status"] == "pending"
    assert calls == [
        (
            "claude",
            {
                "max_messages": None,
                "until_idle": False,
                "stop_after_seconds": None,
                "hard_timeout": 900,
            },
        )
    ]
    assert first[0]["thread_id"] != second[0]["thread_id"]


def test_sync_all_iterates_known_agents(monkeypatch, capsys):
    for agent in _channels.VALID_AGENTS:
        _make_thread(agent, channel=f"{agent}-topic", count=1)

    calls: list[tuple[str, dict[str, object]]] = []

    def _fake_run_inbox(agent: str, **kwargs):
        calls.append((agent, kwargs))
        delivery_id = _oldest_pending_delivery_id(agent)
        assert delivery_id is not None
        _channels.mark_delivery(delivery_id, "delivered")
        return SimpleNamespace(
            deliveries_claimed=1,
            threads_processed=1,
            deliveries_failed=0,
            aborted=False,
        )

    _install_fake_inbox_module(monkeypatch, _fake_run_inbox)

    exit_code = _run_cli(["sync", "--all"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert [call[0] for call in calls] == list(_channels.VALID_AGENTS)
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


def test_post_model_flag_stores_delivery_target_model(capsys):
    _channels.create_channel("topic")

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

    assert post_exit == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert delivery["to_model"] == "gemini-3-flash-preview"


def test_post_model_flag_applies_to_default_channel_subscribers(capsys):
    _channels.create_channel("topic", subscribers=["gemini"])

    post_exit = _run_cli(
        [
            "post",
            "topic",
            "hello subscriber",
            "--model",
            "gemini-3-pro-preview",
            "--no-snapshot",
        ]
    )
    message = _channels.read("topic")[0]
    delivery = _channels.deliveries_for_message(str(message["message_id"]))[0]

    assert post_exit == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert delivery["to_model"] == "gemini-3-pro-preview"


def test_post_workspace_write_large_body_preflight_warns_to_stderr_and_still_posts(capsys):
    _channels.create_channel("topic")
    body = "x" * 8001

    exit_code = _run_cli(["post", "topic", body, "--mode", "workspace-write", "--no-snapshot"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "✅ posted to #topic" in captured.out
    assert (
        "[PREFLIGHT] brief looks large (8001 chars, 0 files mentioned). "
        "Consider --deadline 1800 or splitting."
    ) in captured.err
    assert _channels.read("topic")[0]["body"] == body


def test_inbox_run_deadline_flag_overrides_worker_timeout(monkeypatch, capsys):
    captured_run: dict[str, object] = {}

    def _fake_run_inbox(agent: str, **kwargs):
        captured_run["agent"] = agent
        captured_run.update(kwargs)
        return SimpleNamespace(
            deliveries_claimed=1,
            threads_processed=1,
            deliveries_failed=0,
            aborted=False,
        )

    _install_fake_inbox_module(monkeypatch, _fake_run_inbox)

    exit_code = _run_cli(["inbox", "run", "claude", "--once", "--deadline", "1800"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured_run == {
        "agent": "claude",
        "max_messages": None,
        "until_idle": False,
        "stop_after_seconds": None,
        "hard_timeout": 1800,
    }


def test_post_deadline_flag_stores_delivery_override_and_worker_uses_it(monkeypatch, capsys):
    _channels.create_channel("topic")

    captured_run: dict[str, object] = {}

    def _fake_run_inbox(agent: str, **kwargs):
        delivery_id = _oldest_pending_delivery_id(agent)
        assert delivery_id is not None
        message = _channels.read("topic")[0]
        delivery = _channels.deliveries_for_message(str(message["message_id"]))[0]
        captured_run["hard_timeout"] = max(
            int(kwargs["hard_timeout"]),
            int(delivery["deadline_seconds"] or 0),
        )
        _channels.mark_delivery(delivery_id, "delivered")
        return SimpleNamespace(
            deliveries_claimed=1,
            threads_processed=1,
            deliveries_failed=0,
            aborted=False,
        )

    _install_fake_inbox_module(monkeypatch, _fake_run_inbox)

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
    assert captured_run["hard_timeout"] == 1200


def test_deadline_whitelist_accepts_1800(capsys):
    _channels.create_channel("topic")

    exit_code = _run_cli(
        ["post", "topic", "hello", "--to", "claude", "--deadline", "1800", "--no-snapshot"]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    message = _channels.read("topic")[0]
    delivery = _channels.deliveries_for_message(str(message["message_id"]))[0]
    assert delivery["deadline_seconds"] == 1800


def test_invalid_deadline_value_is_rejected_with_helpful_error(capsys):
    exit_code = _run_cli(["post", "topic", "hello", "--deadline", "999"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "usage:" in captured.err
    assert "deadline must be one of: 300, 600, 900, 1200, 1800, 2400, 3000" in captured.err


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
