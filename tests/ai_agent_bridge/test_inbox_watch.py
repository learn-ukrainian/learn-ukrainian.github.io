"""Unit coverage for the live-driver legacy-inbox wakeup watcher."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from ai_agent_bridge import _db, _inbox_watch, _messaging


@pytest.fixture(autouse=True)
def isolate_db(tmp_path: Path):
    """Create an isolated broker database with the current messages schema."""
    db_path = tmp_path / "messages.db"
    with patch("ai_agent_bridge._config.DB_PATH", db_path), patch("ai_agent_bridge._db.DB_PATH", db_path):
        _db.init_db().close()
        yield db_path


def _send(
    content: str,
    *,
    task_id: str = "review-pr-5687",
    to_llm: str = "grok",
    consumed: bool = False,
) -> int:
    message_id = _messaging.send_message(
        content,
        task_id=task_id,
        from_llm="claude",
        to_llm=to_llm,
        quiet=True,
    )
    if consumed:
        _messaging.acknowledge(message_id, quiet=True, consumed_by_live_driver=True)
    return message_id


def test_cold_start_surfaces_existing_unconsumed_alias_rows(isolate_db: Path):
    """A watcher begins at zero and includes permanent read aliases."""
    canonical_id = _send("canonical pending", to_llm="grok")
    alias_id = _send("historical pending", to_llm="grok-build")
    _send("already consumed", to_llm="grok", consumed=True)

    conn = _inbox_watch.open_readonly_db(isolate_db)
    try:
        events = _inbox_watch.poll_once(conn, "grok", last_seen=0)
    finally:
        conn.close()

    assert [event.message_id for event in events] == [canonical_id, alias_id]
    query = _inbox_watch.build_poll_query(("grok", "grok-build"))
    assert "to_llm IN (?, ?)" in query
    assert "consumed_by_live_driver = 0" in query
    assert "ORDER BY id ASC" in query


def test_cursor_advances_after_emission_and_does_not_reemit(isolate_db: Path):
    """The in-memory cursor suppresses events only after their flush succeeds."""
    message_id = _send("please drain")
    output = io.StringIO()
    conn = _inbox_watch.open_readonly_db(isolate_db)
    try:
        events = _inbox_watch.poll_once(conn, "grok", last_seen=0)
        cursor = _inbox_watch.emit_notifications(events, last_seen=0, output=output)
        repeated = _inbox_watch.poll_once(conn, "grok", last_seen=cursor)
    finally:
        conn.close()

    assert cursor == message_id
    assert repeated == []
    assert f"id={message_id}" in output.getvalue()


def test_empty_poll_is_silent(isolate_db: Path, tmp_path: Path):
    """An empty monitor tick writes no stdout notification."""
    output = io.StringIO()
    cursor = _inbox_watch.run_watcher(
        "grok",
        db_path=isolate_db,
        lock_dir=tmp_path / "locks",
        output=output,
        once=True,
    )

    assert cursor == 0
    assert output.getvalue() == ""


def test_notification_escapes_newlines_and_bounds_preview(isolate_db: Path):
    """One message always creates one bounded Monitor event line."""
    message_id = _send("first line\nsecond line\r\n" + ("x" * 400))
    conn = _inbox_watch.open_readonly_db(isolate_db)
    try:
        event = _inbox_watch.poll_once(conn, "grok", last_seen=0)[0]
    finally:
        conn.close()

    line = event.notification_line()
    preview = line.split("preview=", maxsplit=1)[1]
    assert f"id={message_id}" in line
    assert "sender=claude" in line
    assert "request_id=review-pr-5687" in line
    assert "first line\\nsecond line\\r\\n" in line
    assert "\n" not in line
    assert len(preview) == _inbox_watch.MAX_PREVIEW_CHARS + len("...")


def test_duplicate_watcher_lock_blocks_second_start(isolate_db: Path, tmp_path: Path):
    """A second process cannot own the same canonical agent-slot watcher lock."""
    lock_dir = tmp_path / "locks"
    first = _inbox_watch.acquire_watcher_lock("grok", lock_dir)
    try:
        with pytest.raises(_inbox_watch.WatcherAlreadyRunningError, match="already running"):
            _inbox_watch.run_watcher(
                "grok-build",
                db_path=isolate_db,
                lock_dir=lock_dir,
                once=True,
            )
    finally:
        first.release()

    assert _inbox_watch.run_watcher(
        "grok-build",
        db_path=isolate_db,
        lock_dir=lock_dir,
        once=True,
    ) == 0


def test_cursor_does_not_advance_when_stdout_flush_fails(isolate_db: Path):
    """A failed event flush leaves the caller's cursor unchanged for replay."""
    _send("retry this")
    conn = _inbox_watch.open_readonly_db(isolate_db)
    try:
        events = _inbox_watch.poll_once(conn, "grok", last_seen=0)
    finally:
        conn.close()

    class BrokenOutput:
        def write(self, _line: str) -> int:
            return 1

        def flush(self) -> None:
            raise OSError("stdout closed")

    last_seen = 0
    with pytest.raises(OSError, match="stdout closed"):
        last_seen = _inbox_watch.emit_notifications(events, last_seen=last_seen, output=BrokenOutput())
    assert last_seen == 0
