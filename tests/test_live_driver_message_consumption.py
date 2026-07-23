"""Regression coverage for live epic-driver legacy-message consumption (#5687)."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge import _ask_lifecycle, _cli, _db, _messaging

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRIVE_EPIC_SKILL = PROJECT_ROOT / "agents_extensions/shared/skills/drive-epic/SKILL.md"


@pytest.fixture(autouse=True)
def isolate_db(tmp_path: Path):
    """Keep legacy-message rows isolated for each consumption-state test."""
    db_file = tmp_path / "messages.db"
    with patch("ai_agent_bridge._config.DB_PATH", db_file), patch("ai_agent_bridge._db.DB_PATH", db_file):
        _db.init_db().close()
        yield db_file


def _run_cli(argv: list[str]) -> int:
    with patch.object(sys, "argv", ["ab", *argv]):
        try:
            _cli.main()
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 0
    return 0


def _message_consumption(message_id: int) -> tuple[int, int, str | None]:
    conn = _db.get_db()
    try:
        row = conn.execute(
            "SELECT acknowledged, consumed_by_live_driver, consumed_at FROM messages WHERE id = ?",
            (message_id,),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    return int(row[0]), int(row[1]), row[2]


def test_legacy_messages_migrate_live_driver_consumption_columns(tmp_path: Path):
    """Existing bridge DBs receive both consumption fields through the race-safe migration."""
    legacy_db = tmp_path / "legacy-messages.db"
    conn = sqlite3.connect(legacy_db)
    try:
        conn.executescript(
            """
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                from_llm TEXT NOT NULL,
                to_llm TEXT NOT NULL,
                message_type TEXT DEFAULT 'message',
                content TEXT NOT NULL,
                data TEXT,
                timestamp TEXT NOT NULL,
                acknowledged INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending'
            );
            """
        )
        conn.commit()
    finally:
        conn.close()

    with patch("ai_agent_bridge._config.DB_PATH", legacy_db), patch("ai_agent_bridge._db.DB_PATH", legacy_db):
        migrated = _db.get_db()
        try:
            columns = {row[1] for row in migrated.execute("PRAGMA table_info(messages)").fetchall()}
        finally:
            migrated.close()

    assert {"consumed_by_live_driver", "consumed_at"}.issubset(columns)


def test_live_driver_ack_is_distinct_from_plain_one_shot_ack(capsys):
    """A live-loop acknowledgement is distinguishable from headless processing."""
    one_shot_id = _messaging.send_message(
        "headless worker handled this", task_id="review-pr-5687", from_llm="claude", to_llm="codex", quiet=True
    )
    live_driver_id = _messaging.send_message(
        "live driver must apply this", task_id="review-pr-5687", from_llm="claude", to_llm="codex", quiet=True
    )

    _messaging.acknowledge(one_shot_id, quiet=True)
    assert _message_consumption(one_shot_id) == (1, 0, None)

    assert _run_cli(["inbox", "--for", "codex"]) == 0
    inbox = capsys.readouterr().out
    assert "read-but-not-live-consumed" in inbox
    assert "unread" in inbox

    assert _run_cli(["ack", "--consumed-by-live-driver", str(live_driver_id)]) == 0
    acknowledged, consumed, consumed_at = _message_consumption(live_driver_id)
    assert (acknowledged, consumed) == (1, 1)
    assert consumed_at is not None
    assert _message_consumption(one_shot_id) == (1, 0, None)


def test_ack_all_flag_is_opt_in_and_asks_surfaces_consumption(capsys):
    """Existing ack-all callers stay plain while the explicit flag marks live consumption."""
    plain_id = _messaging.send_message(
        "plain acknowledgement", task_id="review-pr-5687-plain", from_llm="claude", to_llm="codex", quiet=True
    )
    _messaging.acknowledge_all("codex")
    assert _message_consumption(plain_id) == (1, 0, None)

    live_id = _messaging.send_message(
        "tracked review request", task_id="review-pr-5687-live", from_llm="claude", to_llm="codex", quiet=True
    )
    _ask_lifecycle.register_ask(live_id)
    assert _run_cli(["ack-all", "codex", "--consumed-by-live-driver"]) == 0
    acknowledged, consumed, consumed_at = _message_consumption(live_id)
    assert (acknowledged, consumed) == (1, 1)
    assert consumed_at is not None

    assert _run_cli(["asks", "--task-id", "review-pr-5687-live"]) == 0
    asks = capsys.readouterr().out
    assert "CONSUMPTION" in asks
    assert "live-consumed" in asks


def test_drive_epic_skill_keeps_all_required_live_inbox_boundaries():
    """The portable driver contract must not silently lose its inbox drain steps."""
    text = DRIVE_EPIC_SKILL.read_text(encoding="utf-8")
    required_headings = (
        "### 0a. Required live-driver inbox drain — cycle start",
        "### 4a. Required live-driver inbox drain — immediately before dispatch",
        "### 5a. Required live-driver inbox drain — after settle",
        "### 8a. Required live-driver inbox drain — before handoff",
    )
    for heading in required_headings:
        assert heading in text

    inbox_command = '.venv/bin/python -m scripts.ai_agent_bridge inbox --for "$SESSION_HANDOFF_AGENT"'
    acknowledgement = ".venv/bin/python -m scripts.ai_agent_bridge ack --consumed-by-live-driver"
    assert text.count(inbox_command) == 4
    assert text.count(acknowledgement) == 4
    assert ".venv/bin/python -m scripts.ai_agent_bridge asks --task-id review-pr-<PR_NUMBER>" in text
