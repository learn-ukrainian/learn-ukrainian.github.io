from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.ai_agent_bridge import _channels, _cli, _db
from scripts.ai_agent_bridge._channels_watch import (
    emit_reply_complete,
    emit_reply_started,
    read_channel_events,
)


@pytest.fixture(autouse=True)
def isolate_db(tmp_path):
    db_file = tmp_path / "messages.db"
    with patch("scripts.ai_agent_bridge._config.DB_PATH", db_file), \
         patch("scripts.ai_agent_bridge._db.DB_PATH", db_file):
        _db.init_db()
        yield db_file


def _run_cli(argv: list[str]) -> int:
    with patch.object(sys, "argv", ["ab", *argv]):
        try:
            _cli.main()
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 0
    return 0


def _make_thread(agent: str, *, channel: str = "topic") -> dict[str, object]:
    if _channels.get_channel(channel) is None:
        _channels.create_channel(channel)
    return _channels.post(
        channel,
        "user",
        "watch me",
        to_agents=[agent],
        auto_snapshot=False,
    )


def test_channel_watch_event_stream_replays_history_and_exits(capsys):
    thread = _make_thread("claude")
    thread_id = str(thread["thread_id"])
    emit_reply_started(thread_id, agent="codex", model="gpt-5.4")
    emit_reply_complete(thread_id, agent="codex", chars=42)

    exit_code = _run_cli(["channel", "watch", thread_id, "--event-stream"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    events = [json.loads(line) for line in captured.out.strip().splitlines()]
    assert [event["event"] for event in events] == ["reply_started", "reply_complete"]
    assert all(event["thread_id"] == thread_id for event in events)
    assert events[0]["agent"] == "codex"
    assert events[1]["chars"] == 42


def test_channel_watch_auto_migrates_missing_table():
    conn = _db.get_db()
    try:
        conn.execute("DROP TABLE channel_events")
        conn.commit()
    finally:
        conn.close()

    thread = _make_thread("claude")
    thread_id = str(thread["thread_id"])
    emit_reply_started(thread_id, agent="claude", model="test-model")

    events = read_channel_events(thread_id)
    assert len(events) == 1
    assert events[0]["event"] == "reply_started"
