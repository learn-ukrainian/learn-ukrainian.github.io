"""CLI-level tests for #4837 wave 2: broadcast post, delivery TTL/auto-expire
+ cleanup automation, and unified thread retrieval.

Follows the `_run_cli` + `isolate_db` pattern established in
tests/test_ab_reconcile.py and tests/test_bridge_inbox_cli.py.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.ai_agent_bridge import _acp_compat, _channels, _cli, _db, _dispatch_wrappers


@pytest.fixture(autouse=True)
def isolate_db(tmp_path, monkeypatch):
    # This module exercises the retired bridge CLI's compatibility behavior.
    # Authority-mode retirement is covered in test_bridge_inbox_cli.py.
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


def test_post_review_flag_implies_action_required_priority(monkeypatch):
    """Review intent retains its priority and explicit native subject bindings."""
    _channels.create_channel("shared")
    rc = _run_cli(["post", "shared", "please review this", "--to", "claude", "--review", "--no-snapshot"])
    assert rc == 0
    msgs = _channels.read("shared", tail=1)
    assert msgs[0]["priority"] == "action_required"

    native_review = Mock(return_value={"ok": True, "status": "done", "response": "VERDICT: APPROVE"})
    acp_ask = Mock(side_effect=AssertionError("review intent reached ACP"))
    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", native_review)
    monkeypatch.setattr(_acp_compat, "run_compat_ask", acp_ask)
    parser = _cli._build_parser()
    for command in (
        "ask-claude", "ask-codex", "ask-gemini", "ask-agy", "ask-hermes", "ask-opencode",
        "ask-deepseek", "ask-pool", "ask-glm", "ask-gemma", "ask-cursor", "ask-grok",
        "ask-grok-build", "ask-kimi",
    ):
        args = parser.parse_args([
            command, "review this", "--task-id", "review-subjects", "--type", "review",
            "--subject-seat", "codex", "--subject-seat", "cursor",
            "--subject-family", "openai", "--subject-family", "xai", "--subject-family", "openai",
        ])
        assert args.subject_seat == ["codex", "cursor"]
        assert args.subject_family == ["openai", "xai", "openai"]
        # Refused/retired seats remain parser-compatible; their admission gates stay in force.
        if command in {"ask-gemini", "ask-agy"}:
            args.review_profile = "ukrainian"
        if command in {"ask-claude", "ask-codex", "ask-gemini", "ask-agy", "ask-cursor", "ask-grok", "ask-grok-build"}:
            _cli._handle_acp_compat(args, command.removeprefix("ask-"))
            assert native_review.call_args.kwargs["subject_seats"] == ["codex", "cursor"]
            assert native_review.call_args.kwargs["subject_families"] == ["openai", "xai", "openai"]

    args = parser.parse_args(["ask-claude", "review this", "--task-id", "review-no-subjects", "--review"])
    _cli._handle_ask_claude(args)
    assert native_review.call_args.kwargs["subject_seats"] is None
    assert native_review.call_args.kwargs["subject_families"] is None
    acp_ask.assert_not_called()


def test_post_explicit_priority_overrides_review_flag(monkeypatch):
    """Explicit post priority wins; ordinary asks reject review-only subject fields."""
    _channels.create_channel("shared")
    rc = _run_cli(
        ["post", "shared", "fyi + review text", "--to", "claude", "--review", "--priority", "fyi", "--no-snapshot"]
    )
    assert rc == 0
    msgs = _channels.read("shared", tail=1)
    assert msgs[0]["priority"] == "fyi"

    native_review = Mock(side_effect=AssertionError("ordinary ask reached native dispatch"))
    acp_ask = Mock(return_value=SimpleNamespace(ok=True))
    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", native_review)
    monkeypatch.setattr(_acp_compat, "run_compat_ask", acp_ask)
    parser = _cli._build_parser()
    args = parser.parse_args(["ask-claude", "ordinary question", "--task-id", "ordinary", "--from", "codex"])
    _cli._handle_ask_claude(args)
    acp_ask.assert_called_once()
    assert acp_ask.call_args.kwargs["review"] is False
    acp_ask.reset_mock()

    args = parser.parse_args([
        "ask-claude", "ordinary question", "--task-id", "ordinary", "--subject-seat", "codex",
    ])
    with pytest.raises(SystemExit, match="--subject-seat/--subject-family require review intent"):
        _cli._handle_ask_claude(args)
    args = parser.parse_args([
        "ask-claude", "ordinary question", "--task-id", "ordinary", "--subject-family", "openai",
    ])
    with pytest.raises(SystemExit, match="--subject-seat/--subject-family require review intent"):
        _cli._handle_ask_claude(args)
    acp_ask.assert_not_called()
    native_review.assert_not_called()


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
