#!/usr/bin/env python3
"""
MCP Message Broker Server - Bidirectional LLM Communication

Enables Claude and Gemini (and other LLMs) to communicate asynchronously
through a shared message queue.

Usage:
    As MCP server: Configure in .mcp.json

Tools provided:
    - send_message: Send a message to another LLM
    - receive_messages: Get messages addressed to you
    - check_inbox: Quick check for unread messages
    - get_conversation: Get full conversation for a task
    - acknowledge_message: Mark message as read
"""

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite

# MCP protocol imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError:
    print("MCP package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Database path
DB_PATH = Path(__file__).parent / "messages.db"

# Limits
MAX_CONTENT_LENGTH = 10000
VALID_AGENTS = ("claude", "gemini")

# Write lock — serializes all DB writes within this process.
# Cross-process writes are serialized by SQLite WAL mode + busy_timeout.
_write_lock = asyncio.Lock()


async def init_db():
    """Initialize SQLite database for message storage with WAL mode."""
    async with aiosqlite.connect(DB_PATH) as db:
        # WAL mode: allows concurrent reads while serializing writes.
        # busy_timeout: wait up to 5s for locks instead of failing immediately.
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA busy_timeout=5000")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                from_llm TEXT NOT NULL,
                to_llm TEXT NOT NULL,
                message_type TEXT DEFAULT 'message',
                content TEXT NOT NULL,
                data TEXT,
                payload TEXT,
                timestamp TEXT NOT NULL,
                acknowledged INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                claimed_by TEXT,
                claimed_at TEXT
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_to_llm ON messages(to_llm, acknowledged)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_task ON messages(task_id)
        """)
        # Migration: add claimed_by/claimed_at to existing tables
        try:
            await db.execute("ALTER TABLE messages ADD COLUMN claimed_by TEXT")
        except Exception:
            pass  # Column already exists
        try:
            await db.execute("ALTER TABLE messages ADD COLUMN claimed_at TEXT")
        except Exception:
            pass  # Column already exists
        # Sessions table - track CLI session IDs for each agent per task
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                task_id TEXT PRIMARY KEY,
                claude_session_id TEXT,
                gemini_session_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        # Message history table - soft-delete audit trail
        await db.execute("""
            CREATE TABLE IF NOT EXISTS message_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_id INTEGER NOT NULL,
                task_id TEXT,
                from_llm TEXT NOT NULL,
                to_llm TEXT NOT NULL,
                message_type TEXT,
                content TEXT NOT NULL,
                data TEXT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                action_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_original ON message_history(original_id)
        """)
        await db.commit()


async def get_db() -> aiosqlite.Connection:
    """Get an async database connection with WAL mode and busy timeout."""
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA busy_timeout=5000")
    return db


# Initialize server
server = Server("message-broker")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="send_message",
            description="Send a message to another LLM (e.g., Claude to Gemini or vice versa)",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient LLM (e.g., 'gemini', 'claude')",
                        "enum": ["claude", "gemini"]
                    },
                    "content": {
                        "type": "string",
                        "description": "Message content (natural language)"
                    },
                    "message_type": {
                        "type": "string",
                        "description": "Type of message",
                        "enum": ["request", "response", "discussion", "handoff", "feedback", "query", "context"],
                        "default": "message"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "Optional task ID to group related messages"
                    },
                    "data": {
                        "type": "string",
                        "description": "Optional structured data (YAML/JSON) to include"
                    },
                    "from_llm": {
                        "type": "string",
                        "description": "Sender identity (e.g., 'claude', 'gemini')",
                        "enum": ["claude", "gemini"]
                    },
                    "from_model": {
                        "type": "string",
                        "description": "Exact sender model ID (e.g., 'claude-opus-4-5-20251101', 'gemini-3-flash-preview')"
                    },
                    "to_model": {
                        "type": "string",
                        "description": "Target model ID if specific model required"
                    }
                },
                "required": ["to", "content", "from_llm"]
            }
        ),
        Tool(
            name="receive_messages",
            description="Receive messages addressed to you, optionally filtered",
            inputSchema={
                "type": "object",
                "properties": {
                    "for_llm": {
                        "type": "string",
                        "description": "Your identity (who you are)",
                        "enum": ["claude", "gemini"]
                    },
                    "since_id": {
                        "type": "integer",
                        "description": "Only get messages after this ID"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "Filter by task ID"
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "Only return unacknowledged messages",
                        "default": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum messages to return",
                        "default": 10
                    }
                },
                "required": ["for_llm"]
            }
        ),
        Tool(
            name="check_inbox",
            description="Quick check for unread message count",
            inputSchema={
                "type": "object",
                "properties": {
                    "for_llm": {
                        "type": "string",
                        "description": "Your identity",
                        "enum": ["claude", "gemini"]
                    }
                },
                "required": ["for_llm"]
            }
        ),
        Tool(
            name="get_conversation",
            description="Get full conversation history for a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to retrieve conversation for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum messages",
                        "default": 50
                    }
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="acknowledge_message",
            description="Mark a message as read/acknowledged",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "integer",
                        "description": "ID of message to acknowledge"
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="list_tasks",
            description="List all active task IDs with message counts",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""

    await init_db()  # Ensure DB exists

    if name == "send_message":
        return await handle_send_message(arguments)
    elif name == "receive_messages":
        return await handle_receive_messages(arguments)
    elif name == "check_inbox":
        return await handle_check_inbox(arguments)
    elif name == "get_conversation":
        return await handle_get_conversation(arguments)
    elif name == "acknowledge_message":
        return await handle_acknowledge_message(arguments)
    elif name == "list_tasks":
        return await handle_list_tasks(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def handle_send_message(args: dict) -> list[TextContent]:
    """Send a message to another LLM."""
    # Input validation
    from_llm = args.get("from_llm", "")
    to_llm = args.get("to", "")
    content = args.get("content", "")

    if from_llm not in VALID_AGENTS:
        return [TextContent(type="text", text=json.dumps({
            "error": f"Invalid from_llm: '{from_llm}'. Must be one of: {', '.join(VALID_AGENTS)}"
        }))]
    if to_llm not in VALID_AGENTS:
        return [TextContent(type="text", text=json.dumps({
            "error": f"Invalid to: '{to_llm}'. Must be one of: {', '.join(VALID_AGENTS)}"
        }))]
    if not isinstance(content, str) or not content.strip():
        return [TextContent(type="text", text=json.dumps({
            "error": "Content must be a non-empty string."
        }))]
    if len(content) > MAX_CONTENT_LENGTH:
        return [TextContent(type="text", text=json.dumps({
            "error": f"Content too long ({len(content)} chars). Maximum is {MAX_CONTENT_LENGTH}."
        }))]

    async with _write_lock:
        db = await get_db()
        try:
            timestamp = datetime.now(UTC).isoformat()

            # Merge model info into data field as JSON
            data = args.get("data")
            metadata = {}
            if data:
                try:
                    metadata = json.loads(data) if isinstance(data, str) and data.startswith('{') else {"raw": data}
                except json.JSONDecodeError:
                    metadata = {"raw": data}

            if args.get("from_model"):
                metadata["from_model"] = args["from_model"]
            if args.get("to_model"):
                metadata["to_model"] = args["to_model"]

            data_json = json.dumps(metadata) if metadata else None
            task_id = args.get("task_id")
            message_type = args.get("message_type", "message")

            cursor = await db.execute("""
                INSERT INTO messages (task_id, from_llm, to_llm, message_type, content, data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (task_id, from_llm, to_llm, message_type, content, data_json, timestamp))

            msg_id = cursor.lastrowid

            # Log to history
            await db.execute("""
                INSERT INTO message_history (original_id, task_id, from_llm, to_llm, message_type, content, data, timestamp, action, action_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'sent', ?)
            """, (msg_id, task_id, from_llm, to_llm, message_type, content, data_json, timestamp, timestamp))

            await db.commit()

            result = {
                "status": "sent",
                "message_id": msg_id,
                "from": from_llm,
                "to": to_llm,
                "from_model": args.get("from_model"),
                "to_model": args.get("to_model"),
                "timestamp": timestamp
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        finally:
            await db.close()

async def handle_receive_messages(args: dict) -> list[TextContent]:
    """Receive messages for an LLM.

    Uses atomic claim-then-read to prevent multiple sessions from
    picking up the same message. A session_id identifies the caller;
    if not provided, one is generated from PID + timestamp.

    Stale claims (>10 min old) are automatically released so crashed
    sessions don't permanently lock messages.
    """
    async with _write_lock:
        db = await get_db()
        try:
            session_id = args.get("session_id") or f"pid-{os.getpid()}-{datetime.now(UTC).strftime('%H%M%S')}"
            now = datetime.now(UTC).isoformat()

            # Release stale claims (session crashed or timed out — 10 min TTL)
            await db.execute("""
                UPDATE messages SET claimed_by = NULL, claimed_at = NULL
                WHERE claimed_by IS NOT NULL
                  AND claimed_at < datetime('now', '-10 minutes')
                  AND acknowledged = 0
            """)

            # Build WHERE clause
            where = ["to_llm = ?"]
            params: list[Any] = [args["for_llm"]]

            if args.get("since_id"):
                where.append("id > ?")
                params.append(args["since_id"])

            if args.get("task_id"):
                where.append("task_id = ?")
                params.append(args["task_id"])

            if args.get("unread_only", True):
                where.append("acknowledged = 0")
                where.append("claimed_by IS NULL")  # Only unclaimed messages

            where_clause = " AND ".join(where)
            limit = args.get("limit", 10)

            # Atomic claim: UPDATE first, then SELECT claimed rows
            await db.execute(f"""
                UPDATE messages SET claimed_by = ?, claimed_at = ?
                WHERE id IN (
                    SELECT id FROM messages
                    WHERE {where_clause}
                    ORDER BY id ASC
                    LIMIT ?
                )
            """, [session_id, now] + params + [limit])

            # Fetch the messages we just claimed
            cursor = await db.execute("""
                SELECT id, task_id, from_llm, message_type, content, data, timestamp, acknowledged
                FROM messages
                WHERE claimed_by = ? AND acknowledged = 0
                ORDER BY id ASC
            """, [session_id])
            rows = await cursor.fetchall()

            # Auto-acknowledge claimed messages
            if rows:
                ids = [row[0] for row in rows]
                placeholders = ",".join("?" * len(ids))
                await db.execute(f"UPDATE messages SET acknowledged = 1 WHERE id IN ({placeholders})", ids)

            await db.commit()

            messages = []
            for row in rows:
                msg = {
                    "id": row[0],
                    "task_id": row[1],
                    "from": row[2],
                    "type": row[3],
                    "content": row[4],
                    "timestamp": row[6],
                    "acknowledged": bool(row[7])
                }
                if row[5]:  # data field
                    msg["data"] = row[5]
                messages.append(msg)

            result = {
                "count": len(messages),
                "messages": messages
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        finally:
            await db.close()

async def handle_check_inbox(args: dict) -> list[TextContent]:
    """Quick inbox check. Also sweeps stale messages (TTL: 6h)."""
    db = await get_db()
    try:
        # TTL sweep is a write — serialize it
        async with _write_lock:
            cursor = await db.execute("""
                UPDATE messages SET acknowledged = 1
                WHERE acknowledged = 0
                  AND timestamp < datetime('now', '-6 hours')
            """)
            if cursor.rowcount > 0:
                await db.commit()

        # Reads don't need the write lock
        cursor = await db.execute("""
            SELECT COUNT(*) FROM messages
            WHERE to_llm = ? AND acknowledged = 0
        """, (args["for_llm"],))

        row = await cursor.fetchone()
        unread = row[0] if row else 0

        cursor = await db.execute("""
            SELECT from_llm, COUNT(*) FROM messages
            WHERE to_llm = ? AND acknowledged = 0
            GROUP BY from_llm
        """, (args["for_llm"],))

        by_sender = {row[0]: row[1] for row in await cursor.fetchall()}

        result = {
            "unread_count": unread,
            "by_sender": by_sender
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    finally:
        await db.close()

async def handle_get_conversation(args: dict) -> list[TextContent]:
    """Get full conversation for a task."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT id, from_llm, to_llm, message_type, content, data, timestamp
            FROM messages
            WHERE task_id = ?
            ORDER BY id ASC
            LIMIT ?
        """, (args["task_id"], args.get("limit", 50)))

        rows = await cursor.fetchall()

        messages = []
        for row in rows:
            msg = {
                "id": row[0],
                "from": row[1],
                "to": row[2],
                "type": row[3],
                "content": row[4],
                "timestamp": row[6]
            }
            if row[5]:
                msg["data"] = row[5]
            messages.append(msg)

        result = {
            "task_id": args["task_id"],
            "message_count": len(messages),
            "messages": messages
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    finally:
        await db.close()

async def handle_acknowledge_message(args: dict) -> list[TextContent]:
    """Acknowledge a message."""
    async with _write_lock:
        db = await get_db()
        try:
            now = datetime.now(UTC).isoformat()

            # Fetch the original message for history logging
            cursor = await db.execute("""
                SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp
                FROM messages WHERE id = ?
            """, (args["message_id"],))
            row = await cursor.fetchone()

            cursor = await db.execute("""
                UPDATE messages SET acknowledged = 1 WHERE id = ?
            """, (args["message_id"],))

            updated = cursor.rowcount

            # Log to history if the message existed
            if row:
                await db.execute("""
                    INSERT INTO message_history (original_id, task_id, from_llm, to_llm, message_type, content, data, timestamp, action, action_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'acknowledged', ?)
                """, (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], now))

            await db.commit()

            result = {
                "status": "acknowledged" if updated else "not_found",
                "message_id": args["message_id"]
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        finally:
            await db.close()

async def handle_list_tasks(args: dict) -> list[TextContent]:
    """List active tasks."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT task_id, COUNT(*), MAX(timestamp)
            FROM messages
            WHERE task_id IS NOT NULL
            GROUP BY task_id
            ORDER BY MAX(timestamp) DESC
        """)

        rows = await cursor.fetchall()

        tasks = [
            {
                "task_id": row[0],
                "message_count": row[1],
                "last_activity": row[2]
            }
            for row in rows
        ]

        return [TextContent(type="text", text=json.dumps({"tasks": tasks}, indent=2))]
    finally:
        await db.close()

async def main():
    """Run the MCP server."""
    await init_db()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
