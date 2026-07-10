"""CLI-level tests for #4837 wave 2: broadcast post, delivery TTL/auto-expire
+ cleanup automation, and unified thread retrieval.

Follows the `_run_cli` + `isolate_db` pattern established in
tests/test_ab_reconcile.py and tests/test_bridge_inbox_cli.py.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge import _channels, _cli, _db, _messaging


@pytest.fixture(autouse=True)
def isolate_db(tmp_path):
    db_file = tmp_path / "messages.db"
    with patch("ai_agent_bridge._config.DB_PATH", db_file), patch("ai_agent_bridge._db.DB_PATH", db_file):
        _db.init_db()
        yield db_file


def _run_cli(argv: list[str]) -> int:
    with patch.object(sys, "argv", ["ab", *argv]):
        try:
            _cli.main()
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 0
    return 0


def _hours_ago(hours: float) -> str:
    return (datetime.now(UTC) - timedelta(hours=hours)).isoformat()


def _set_message_created_at(message_id: str, created_at: str) -> None:
    conn = _db.get_db()
    try:
        conn.execute("UPDATE channel_messages SET created_at = ? WHERE message_id = ?", (created_at, message_id))
        conn.commit()
    finally:
        conn.close()


def _delivery_status(delivery_id: str) -> str:
    conn = _db.get_db()
    try:
        row = conn.execute("SELECT status FROM deliveries WHERE delivery_id = ?", (delivery_id,)).fetchone()
        return str(row["status"])
    finally:
        conn.close()


def _pending_agents_for_message(message_id: str) -> set[str]:
    conn = _db.get_db()
    try:
        rows = conn.execute(
            "SELECT to_agent FROM deliveries WHERE message_id = ? AND status = 'pending'", (message_id,)
        ).fetchall()
        return {row["to_agent"] for row in rows}
    finally:
        conn.close()


def _message_priority(message_id: str) -> str:
    conn = _db.get_db()
    try:
        row = conn.execute(
            "SELECT priority FROM channel_messages WHERE message_id = ?", (message_id,)
        ).fetchone()
        return str(row["priority"])
    finally:
        conn.close()


# ── Item 3: broadcast post ──────────────────────────────────────────────


def test_p_single_recipient_still_works(capsys):
    _channels.create_channel("shared")
    rc = _run_cli(["p", "shared", "claude", "hello"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "→ claude" in out
    assert "1 deliveries" in out


def test_p_multi_recipient_comma_list(capsys):
    _channels.create_channel("shared")
    rc = _run_cli(["p", "shared", "claude,codex", "hello team"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "claude" in out and "codex" in out
    assert "2 deliveries" in out


def test_p_broadcast_excludes_dead_lane(capsys, monkeypatch):
    monkeypatch.setenv("AB_DEAD_LANES", "gemini")
    _channels.create_channel("ops", subscribers=["claude", "codex", "gemini"])
    rc = _run_cli(["p", "ops", "--broadcast", "fleet announcement"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "claude" in out
    assert "codex" in out
    assert "excluded dead lanes: gemini" in out
    # Broadcast defaults to fyi priority (#4837 item 3).
    msgs = _channels.read("ops", tail=1)
    assert msgs[0]["priority"] == "fyi"
    delivered_agents = {d["to_agent"] for d in _channels.deliveries_for_message(msgs[0]["message_id"])}
    assert delivered_agents == {"claude", "codex"}


def test_p_broadcast_and_agent_conflict_errors(capsys):
    _channels.create_channel("shared")
    rc = _run_cli(["p", "shared", "claude", "hello", "--broadcast"])
    assert rc == 2
    assert "not both" in capsys.readouterr().err


def test_p_missing_recipient_errors(capsys):
    _channels.create_channel("shared")
    rc = _run_cli(["p", "shared", "hello with no recipient"])
    assert rc == 2
    assert "missing recipient" in capsys.readouterr().err


def test_post_broadcast_and_to_conflict_errors(capsys):
    _channels.create_channel("shared")
    rc = _run_cli(["post", "shared", "hello", "--broadcast", "--to", "claude"])
    assert rc == 1
    assert "cannot be combined" in capsys.readouterr().err


def test_post_review_flag_implies_action_required_priority():
    _channels.create_channel("shared")
    rc = _run_cli(["post", "shared", "please review this", "--to", "claude", "--review", "--no-snapshot"])
    assert rc == 0
    msgs = _channels.read("shared", tail=1)
    assert msgs[0]["priority"] == "action_required"


def test_post_explicit_priority_overrides_review_flag():
    _channels.create_channel("shared")
    rc = _run_cli(
        ["post", "shared", "fyi + review text", "--to", "claude", "--review", "--priority", "fyi", "--no-snapshot"]
    )
    assert rc == 0
    msgs = _channels.read("shared", tail=1)
    assert msgs[0]["priority"] == "fyi"


def test_post_explicit_action_required_priority_without_review():
    _channels.create_channel("shared")
    rc = _run_cli(
        ["post", "shared", "urgent", "--to", "claude", "--priority", "action-required", "--no-snapshot"]
    )
    assert rc == 0
    msgs = _channels.read("shared", tail=1)
    assert msgs[0]["priority"] == "action_required"


# ── Item 4: delivery TTL/auto-expire + cleanup automation ──────────────


def test_cleanup_expire_dry_run_previews_without_mutating(capsys):
    _channels.create_channel("shared")
    res = _channels.post("shared", "user", "stale", to_agents=["claude"], auto_snapshot=False)
    _set_message_created_at(res["message_id"], _hours_ago(30))

    rc = _run_cli(["cleanup", "--expire", "--dry-run"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "would expire" in out
    assert "1 deliveries would expire" in out
    assert _delivery_status(res["delivery_ids"][0]) == "pending"


def test_cleanup_expire_applies_and_logs(capsys):
    _channels.create_channel("shared")
    res = _channels.post("shared", "user", "stale", to_agents=["claude"], auto_snapshot=False)
    _set_message_created_at(res["message_id"], _hours_ago(30))

    rc = _run_cli(["cleanup", "--expire"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "1 deliveries auto-expired" in out
    assert _delivery_status(res["delivery_ids"][0]) == "expired"


def test_cleanup_expire_bulk_expires_dead_lane_regardless_of_age(capsys, monkeypatch):
    monkeypatch.setenv("AB_DEAD_LANES", "gemini")
    _channels.create_channel("shared")
    res = _channels.post("shared", "user", "fresh", to_agents=["gemini"], auto_snapshot=False)
    # No backdating — this delivery is brand new, well within any TTL.

    rc = _run_cli(["cleanup", "--expire"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "dead-lane expire: 1 pending deliveries for 'gemini'" in out
    assert _delivery_status(res["delivery_ids"][0]) == "expired"


def test_cleanup_without_expire_flag_leaves_channel_deliveries_untouched():
    _channels.create_channel("shared")
    res = _channels.post("shared", "user", "stale", to_agents=["claude"], auto_snapshot=False)
    _set_message_created_at(res["message_id"], _hours_ago(30))

    rc = _run_cli(["cleanup"])

    assert rc == 0
    assert _delivery_status(res["delivery_ids"][0]) == "pending"


def test_action_required_delivery_survives_plain_cleanup_expire_before_escalation_ttl():
    """A review request 3 days old must not be swept by the fast fyi path."""
    _channels.create_channel("shared")
    res = _channels.post(
        "shared", "user", "please review", to_agents=["claude"],
        priority=_channels.PRIORITY_ACTION_REQUIRED, auto_snapshot=False,
    )
    _set_message_created_at(res["message_id"], _hours_ago(72))

    rc = _run_cli(["cleanup", "--expire"])

    assert rc == 0
    assert _delivery_status(res["delivery_ids"][0]) == "pending"


# ── Item 5: unified thread retrieval ────────────────────────────────────


def test_thread_cli_by_task_id(capsys):
    _messaging.send_message("hello", task_id="t-4837", quiet=True)
    rc = _run_cli(["thread", "t-4837"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Conversation: t-4837" in out
    assert "hello" in out


def test_thread_cli_by_numeric_message_id_resolves_task(capsys):
    msg_id = _messaging.send_message("ask", task_id="t-4837b", from_llm="claude", to_llm="codex", quiet=True)
    _messaging.send_message("reply", task_id="t-4837b", from_llm="codex", to_llm="claude", quiet=True)
    rc = _run_cli(["thread", str(msg_id)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Conversation: t-4837b (2 messages)" in out
    assert "ask" in out
    assert "reply" in out
