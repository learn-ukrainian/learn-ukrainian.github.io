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
from scripts.ai_agent_bridge import _acp_compat, _channels, _cli, _db


@pytest.fixture(autouse=True)
def isolate_db(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_AGENT_COMM_TRANSPORT", "bridge")
    # These tests cover the bounded read-only compatibility soak and its
    # historical writer behavior. Production authority mode refuses writers.
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "shadow")
    db_file = tmp_path / "messages.db"
    with patch("scripts.ai_agent_bridge._config.DB_PATH", db_file), patch("scripts.ai_agent_bridge._db.DB_PATH", db_file):
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


def _delivery_detail(delivery_id: str) -> sqlite3.Row:
    conn = _db.get_db()
    try:
        return conn.execute(
            """
            SELECT delivery_id, status, error, delivered_at
            FROM deliveries
            WHERE delivery_id = ?
            """,
            (delivery_id,),
        ).fetchone()
    finally:
        conn.close()


def _install_fake_inbox_module(monkeypatch, run_inbox) -> None:
    fake_inbox_module = ModuleType("scripts.ai_agent_bridge._inbox")
    fake_inbox_module.run_inbox = run_inbox
    monkeypatch.setitem(sys.modules, "scripts.ai_agent_bridge._inbox", fake_inbox_module)


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


def test_inbox_ack_marks_delivery_delivered(capsys):
    thread = _make_thread("claude", count=1)
    delivery_id = _channels.deliveries_for_message(str(thread[0]["message_id"]))[0]["delivery_id"]

    exit_code = _run_cli(
        [
            "inbox",
            "ack",
            delivery_id,
            "--error",
            "processed by codex-desktop automation",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert f"✅ delivery {delivery_id} → delivered" in captured.out
    detail = _delivery_detail(delivery_id)
    assert detail["status"] == "delivered"
    assert detail["error"] == "processed by codex-desktop automation"
    assert detail["delivered_at"] is not None


def test_inbox_ack_already_delivered_is_noop(capsys):
    thread = _make_thread("claude", count=1)
    delivery_id = _channels.deliveries_for_message(str(thread[0]["message_id"]))[0]["delivery_id"]
    assert _run_cli(["inbox", "ack", delivery_id]) == 0
    capsys.readouterr()

    exit_code = _run_cli(["inbox", "ack", delivery_id])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert f"delivery {delivery_id} is already 'delivered' (no-op)" in captured.out


def test_post_to_codex_desktop_routes_delivery(capsys):
    _channels.create_channel("topic")

    exit_code = _run_cli(
        [
            "post",
            "topic",
            "desktop brief",
            "--to",
            "codex-desktop",
            "--from-agent",
            "claude",
            "--no-snapshot",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "→ codex-desktop  (1 deliveries)" in captured.out
    delivery = _channels.deliveries_for_message(_channels.read("topic")[0]["message_id"])[0]
    assert delivery["to_agent"] == "codex-desktop"


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


def test_backlog_banner_count_matches_inbox_show_excluding_ttl_elapsed(
    monkeypatch, capsys
):
    """#6864: banner live-pending count equals inbox show (not raw pending).

    Seed one within-TTL pending + one past channel TTL. Banner must report
    only the live row (1), matching inbox show after expire, not the raw
    pending total (2).
    """
    monkeypatch.setenv("AB_BACKLOG_WARN_HOURS", "2")
    _channels.create_channel("topic", description="ttl fixture")
    _channels.set_channel_ttl("topic", 24)

    live = _channels.post(
        "topic", "user", "still live", to_agents=["codex"], auto_snapshot=False
    )
    stale = _channels.post(
        "topic", "user", "past ttl", to_agents=["codex"], auto_snapshot=False
    )
    live_ts = (datetime.now(UTC) - timedelta(hours=6, minutes=12)).isoformat()
    stale_ts = (datetime.now(UTC) - timedelta(hours=30)).isoformat()
    _set_message_created_at(str(live["message_id"]), live_ts)
    _set_message_created_at(str(stale["message_id"]), stale_ts)

    # Authority query (shared) already excludes TTL-elapsed before show mutates.
    live_rows = {
        row["agent"]: row for row in _channels.live_pending_by_agent()
    }
    assert live_rows["codex"]["count"] == 1

    exit_code = _run_cli(["inbox", "show", "codex"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "⚠️  codex has 1 pending deliveries (oldest 6h12m)." in captured.err
    assert "pending:    1 (oldest 6h12m ago)" in captured.out
    assert "inbox run" not in captured.err
    assert "ab inbox" not in captured.err
    # Stale row expired by show janitor; live row remains pending.
    statuses = {
        row["body"]: row["status"] for row in _delivery_statuses() if row["to_agent"] == "codex"
    }
    assert statuses["still live"] == "pending"
    assert statuses["past ttl"] == "expired"


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
    assert "--auth" in inbox_help.out

    with pytest.raises(SystemExit):
        parser.parse_args(["ask-gemini", "--help"])
    ask_gemini_help = capsys.readouterr()
    assert "--auth" in ask_gemini_help.out


def test_detect_caller_identity_honors_session_handoff_agent(monkeypatch):
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "claude-infra")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/tmp/claude-project")

    assert _cli._detect_caller_identity_from_env() == "claude-infra"


def test_detect_caller_identity_phantom_handoff_agent_aliased_to_provider(monkeypatch):
    # #7597: a pre-fix launcher exported SESSION_HANDOFF_AGENT=codex-monitor
    # (grok-monitor is a registered slot since #10835).
    # The explicit marker must still win (aliased to the provider), not fall
    # through to the soft CLAUDE_PROJECT_DIR heuristic.
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "codex-monitor")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/tmp/claude-project")

    assert _cli._detect_caller_identity_from_env() == "codex"


def test_explicit_from_mismatch_with_handoff_agent_is_warning_tagged(monkeypatch, capsys):
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "claude-folk")

    sender = _cli._resolve_from_llm(SimpleNamespace(from_llm="claude-infra"))

    assert sender == "claude-infra"
    assert "[SENDER_IDENTITY_MISMATCH]" in capsys.readouterr().err


def _clear_identity_env(monkeypatch) -> None:
    for var in (
        "SESSION_HANDOFF_AGENT",
        "CLAUDE_AGENT_NAME",
        "CODEX_SESSION",
        "GROK_AGENT",
        "CLAUDE_PROJECT_DIR",
        "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS",
        "GEMINI_SESSION",
    ):
        monkeypatch.delenv(var, raising=False)


def test_ask_claude_reads_body_from_stdin_on_dash(monkeypatch):
    # Regression for the grok "empty result" bug: ask-claude used args.content
    # directly, so `ask-claude - < prompt.md` sent the literal "-" as the body.
    # Every other ask-* handler resolves "-" to stdin; ask-claude must too.
    captured: dict[str, object] = {}

    def _fake_acp(target, content, **_kwargs):
        captured.update(target=target, content=content)
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(_acp_compat, "run_compat_ask", _fake_acp)
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(read=lambda: "the real question body"))

    exit_code = _run_cli(["ask-claude", "-", "--task-id", "t-stdin", "--from", "grok-build"])

    assert exit_code == 0
    assert captured["target"] == "claude"
    assert captured["content"] == "the real question body"


def test_ask_claude_literal_content_is_not_treated_as_stdin(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_acp(target, content, **_kwargs):
        captured.update(target=target, content=content)
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(_acp_compat, "run_compat_ask", _fake_acp)
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(read=lambda: "SHOULD-NOT-BE-USED"))

    exit_code = _run_cli(["ask-claude", "a literal question", "--task-id", "t-lit", "--from", "grok-build"])

    assert exit_code == 0
    assert captured["target"] == "claude"
    assert captured["content"] == "a literal question"


def test_recipient_choices_cover_every_valid_agent():
    # Regression: inbox --for / send --to / ack-all hardcoded {claude,gemini,codex},
    # silently second-classing grok-build, grok, kimi, agy, and cursor.
    parser = _cli._build_parser()
    for agent in ("grok-build", "grok", "kimi", "agy", "cursor"):
        assert parser.parse_args(["inbox", "--for", agent]).for_llm == agent
        assert parser.parse_args(["ack-all", agent]).agent == agent
        assert parser.parse_args(["send", "hi", "--to", agent]).to_llm == agent


def test_recipient_choices_cover_registered_cursor_seats():
    # Launcher mints cursor-<lane> via handoff_identity_for_cursor_epic; those
    # seats must be argparse-valid so live cursor drivers can drain supervisor
    # mail (cursor-infra was rejected on main before the roster backfill).
    parser = _cli._build_parser()
    for agent in (
        "cursor-infra",
        "cursor-devops",
        "cursor-corpus",
        "cursor-atlas",
    ):
        assert agent in _channels.get_valid_recipient_agents()
        assert parser.parse_args(["inbox", "--for", agent]).for_llm == agent
        assert parser.parse_args(["ack-all", agent]).agent == agent
        assert parser.parse_args(["send", "hi", "--to", agent]).to_llm == agent
        assert parser.parse_args(["inbox", "show", agent]).agent == agent


@pytest.mark.parametrize("provider", ("claude", "codex"))
def test_open_model_data_slot_bridge_round_trip(provider, isolate_db, capsys):
    """Exercise the real CLI and isolated SQLite store, including inbox separation."""
    slot = f"{provider}-open-model-data"
    other_slot = "codex-open-model-data" if provider == "claude" else "claude-open-model-data"
    assert _channels.resolve_recipient_alias(slot) == slot
    assert _run_cli(["send", "bare inbox control", "--to", provider, "--from", "claude-atlas"]) == 0
    assert _run_cli(["send", "lane inbox proof", "--to", slot, "--from", "claude-atlas"]) == 0
    capsys.readouterr()

    with sqlite3.connect(isolate_db) as conn:
        rows = conn.execute("SELECT to_llm, content FROM messages ORDER BY id").fetchall()
    assert rows == [(provider, "bare inbox control"), (slot, "lane inbox proof")]

    assert _run_cli(["inbox", "--for", slot]) == 0
    lane_inbox = capsys.readouterr().out
    assert f"Inbox for {slot}: 1 unread" in lane_inbox
    assert "lane inbox proof" in lane_inbox
    assert "bare inbox control" not in lane_inbox

    assert _run_cli(["inbox", "--for", provider]) == 0
    bare_inbox = capsys.readouterr().out
    assert "bare inbox control" in bare_inbox
    assert "lane inbox proof" not in bare_inbox

    assert _run_cli(["inbox", "--for", other_slot]) == 0
    assert f"No messages for {other_slot}" in capsys.readouterr().out


# ── #7597: phantom {provider}-{empty-slots-area} aliases ──────────────
