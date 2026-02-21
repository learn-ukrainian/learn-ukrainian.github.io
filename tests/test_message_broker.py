"""Tests for the MCP message broker — concurrent write safety (#613).

Uses asyncio.run() wrappers to avoid needing pytest-asyncio.
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import aiosqlite


# Path to the broker module
SERVER_DIR = Path(__file__).resolve().parent.parent / ".mcp" / "servers" / "message-broker"


def _get_broker(tmp_path):
    """Import broker with patched DB_PATH pointing to a temp file."""
    db_path = tmp_path / "test_messages.db"
    sys.path.insert(0, str(SERVER_DIR))

    # Force reimport
    if "server" in sys.modules:
        del sys.modules["server"]
    import server as broker
    broker.DB_PATH = db_path
    # Reset write lock for each test (new event loop)
    broker._write_lock = asyncio.Lock()
    return broker, db_path


def test_init_db_creates_tables(tmp_path):
    """init_db creates all required tables."""
    broker, db_path = _get_broker(tmp_path)

    async def _test():
        await broker.init_db()
        assert db_path.exists()

        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = {row[0] for row in await cursor.fetchall()}

        assert "messages" in tables
        assert "message_history" in tables
        assert "sessions" in tables

    asyncio.run(_test())


def test_wal_mode_enabled(tmp_path):
    """Database uses WAL journal mode after init."""
    broker, db_path = _get_broker(tmp_path)

    async def _test():
        await broker.init_db()

        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("PRAGMA journal_mode")
            row = await cursor.fetchone()
            assert row[0] == "wal"

    asyncio.run(_test())


def test_send_message_validation(tmp_path):
    """Invalid inputs are rejected without DB writes."""
    broker, db_path = _get_broker(tmp_path)

    async def _test():
        await broker.init_db()

        # Invalid from_llm
        result = await broker.handle_send_message({
            "from_llm": "gpt", "to": "claude", "content": "hello"
        })
        assert "error" in json.loads(result[0].text)

        # Empty content
        result = await broker.handle_send_message({
            "from_llm": "claude", "to": "gemini", "content": ""
        })
        assert "error" in json.loads(result[0].text)

        # Content too long
        result = await broker.handle_send_message({
            "from_llm": "claude", "to": "gemini",
            "content": "x" * (broker.MAX_CONTENT_LENGTH + 1)
        })
        assert "error" in json.loads(result[0].text)

    asyncio.run(_test())


def test_send_and_receive(tmp_path):
    """Basic send/receive round-trip."""
    broker, db_path = _get_broker(tmp_path)

    async def _test():
        await broker.init_db()

        # Send
        result = await broker.handle_send_message({
            "from_llm": "claude", "to": "gemini",
            "content": "Hello Gemini", "task_id": "test-1"
        })
        data = json.loads(result[0].text)
        assert data["status"] == "sent"

        # Receive
        result = await broker.handle_receive_messages({
            "for_llm": "gemini", "unread_only": True
        })
        data = json.loads(result[0].text)
        assert data["count"] == 1
        assert data["messages"][0]["content"] == "Hello Gemini"

        # Second receive should return nothing (already acknowledged)
        result = await broker.handle_receive_messages({
            "for_llm": "gemini", "unread_only": True
        })
        data = json.loads(result[0].text)
        assert data["count"] == 0

    asyncio.run(_test())


def test_history_trail(tmp_path):
    """Messages are logged to history table on send."""
    broker, db_path = _get_broker(tmp_path)

    async def _test():
        await broker.init_db()

        await broker.handle_send_message({
            "from_llm": "gemini", "to": "claude",
            "content": "Review this", "task_id": "test-2"
        })

        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM message_history WHERE action = 'sent'"
            )
            row = await cursor.fetchone()
            assert row[0] == 1

    asyncio.run(_test())


def test_concurrent_writes(tmp_path):
    """Multiple concurrent writes don't cause DB corruption (#613)."""
    broker, db_path = _get_broker(tmp_path)

    async def _test():
        await broker.init_db()

        async def send_message(i: int):
            return await broker.handle_send_message({
                "from_llm": "claude", "to": "gemini",
                "content": f"Message {i}", "task_id": "concurrent-test"
            })

        # Fire 20 concurrent writes
        results = await asyncio.gather(*[send_message(i) for i in range(20)])

        # All should succeed
        for r in results:
            data = json.loads(r[0].text)
            assert data["status"] == "sent", f"Write failed: {data}"

        # Verify all 20 messages exist
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM messages WHERE task_id = 'concurrent-test'"
            )
            row = await cursor.fetchone()
            assert row[0] == 20

        # Verify all 20 history entries
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM message_history WHERE task_id = 'concurrent-test'"
            )
            row = await cursor.fetchone()
            assert row[0] == 20

    asyncio.run(_test())


def test_check_inbox(tmp_path):
    """check_inbox returns correct unread count."""
    broker, db_path = _get_broker(tmp_path)

    async def _test():
        await broker.init_db()

        # Send 3 messages
        for i in range(3):
            await broker.handle_send_message({
                "from_llm": "claude", "to": "gemini",
                "content": f"msg {i}", "task_id": "inbox-test"
            })

        result = await broker.handle_check_inbox({"for_llm": "gemini"})
        data = json.loads(result[0].text)
        assert data["unread_count"] == 3
        assert data["by_sender"]["claude"] == 3

    asyncio.run(_test())
