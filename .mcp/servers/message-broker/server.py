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

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# MCP protocol imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Database path
DB_PATH = Path(__file__).parent / "messages.db"

def init_db():
    """Initialize SQLite database for message storage."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
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
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_to_llm ON messages(to_llm, acknowledged)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_task ON messages(task_id)
    """)
    # Sessions table - track CLI session IDs for each agent per task
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            task_id TEXT PRIMARY KEY,
            claude_session_id TEXT,
            gemini_session_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_db():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)

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

    init_db()  # Ensure DB exists

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
    conn = get_db()
    cursor = conn.cursor()

    timestamp = datetime.now(timezone.utc).isoformat()

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

    cursor.execute("""
        INSERT INTO messages (task_id, from_llm, to_llm, message_type, content, data, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        args.get("task_id"),
        args["from_llm"],
        args["to"],
        args.get("message_type", "message"),
        args["content"],
        data_json,
        timestamp
    ))

    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()

    result = {
        "status": "sent",
        "message_id": msg_id,
        "from": args["from_llm"],
        "to": args["to"],
        "from_model": args.get("from_model"),
        "to_model": args.get("to_model"),
        "timestamp": timestamp
    }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

async def handle_receive_messages(args: dict) -> list[TextContent]:
    """Receive messages for an LLM."""
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT id, task_id, from_llm, message_type, content, data, timestamp, acknowledged FROM messages WHERE to_llm = ?"
    params = [args["for_llm"]]

    if args.get("since_id"):
        query += " AND id > ?"
        params.append(args["since_id"])

    if args.get("task_id"):
        query += " AND task_id = ?"
        params.append(args["task_id"])

    if args.get("unread_only", True):
        query += " AND acknowledged = 0"

    query += " ORDER BY id ASC LIMIT ?"
    params.append(args.get("limit", 10))

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

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

async def handle_check_inbox(args: dict) -> list[TextContent]:
    """Quick inbox check."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM messages
        WHERE to_llm = ? AND acknowledged = 0
    """, (args["for_llm"],))

    unread = cursor.fetchone()[0]

    cursor.execute("""
        SELECT from_llm, COUNT(*) FROM messages
        WHERE to_llm = ? AND acknowledged = 0
        GROUP BY from_llm
    """, (args["for_llm"],))

    by_sender = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    result = {
        "unread_count": unread,
        "by_sender": by_sender
    }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

async def handle_get_conversation(args: dict) -> list[TextContent]:
    """Get full conversation for a task."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, from_llm, to_llm, message_type, content, data, timestamp
        FROM messages
        WHERE task_id = ?
        ORDER BY id ASC
        LIMIT ?
    """, (args["task_id"], args.get("limit", 50)))

    rows = cursor.fetchall()
    conn.close()

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

async def handle_acknowledge_message(args: dict) -> list[TextContent]:
    """Acknowledge a message."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE messages SET acknowledged = 1 WHERE id = ?
    """, (args["message_id"],))

    updated = cursor.rowcount
    conn.commit()
    conn.close()

    result = {
        "status": "acknowledged" if updated else "not_found",
        "message_id": args["message_id"]
    }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

async def handle_list_tasks(args: dict) -> list[TextContent]:
    """List active tasks."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT task_id, COUNT(*), MAX(timestamp)
        FROM messages
        WHERE task_id IS NOT NULL
        GROUP BY task_id
        ORDER BY MAX(timestamp) DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    tasks = [
        {
            "task_id": row[0],
            "message_count": row[1],
            "last_activity": row[2]
        }
        for row in rows
    ]

    return [TextContent(type="text", text=json.dumps({"tasks": tasks}, indent=2))]

async def main():
    """Run the MCP server."""
    init_db()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
