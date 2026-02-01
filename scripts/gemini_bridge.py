#!/usr/bin/env python3
"""
Gemini Bridge - Bridge between Gemini CLI and MCP Message Broker

This script allows Gemini to participate in the bidirectional
communication system by reading from and writing to the same
SQLite database that the MCP Message Broker uses.

Usage:
    # Check for messages from Claude
    python scripts/gemini_bridge.py inbox

    # Get a specific message
    python scripts/gemini_bridge.py read <message_id>

    # Send a message to Claude
    python scripts/gemini_bridge.py send "Your message content"

    # Send with structured data
    python scripts/gemini_bridge.py send "Message" --data data.yaml --task-id my-task

    # Get full conversation
    python scripts/gemini_bridge.py conversation <task_id>

    # Interactive mode (for gemini-cli piping)
    python scripts/gemini_bridge.py interactive

    # Process and respond (read message, pipe to gemini, send response)
    python scripts/gemini_bridge.py process <message_id>
"""

import argparse
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Database path (same as MCP server uses)
DB_PATH = Path(__file__).parent.parent / ".mcp/servers/message-broker/messages.db"

def init_db():
    """Initialize database if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
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
            timestamp TEXT NOT NULL,
            acknowledged INTEGER DEFAULT 0
        )
    """)
    # Sessions table - track CLI session IDs for resuming conversations
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
    return conn

def get_db():
    """Get database connection."""
    if not DB_PATH.exists():
        return init_db()
    conn = sqlite3.connect(DB_PATH)
    # Ensure sessions table exists (for existing DBs)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            task_id TEXT PRIMARY KEY,
            claude_session_id TEXT,
            gemini_session_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    return conn


def get_session(task_id: str) -> dict:
    """Get session IDs for a task."""
    if not task_id:
        return {"claude": None, "gemini": None}

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT claude_session_id, gemini_session_id FROM sessions WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"claude": row[0], "gemini": row[1]}
    return {"claude": None, "gemini": None}


def set_session(task_id: str, agent: str, session_id: str):
    """Set session ID for an agent on a task."""
    if not task_id:
        return

    conn = get_db()
    cursor = conn.cursor()
    timestamp = datetime.now(timezone.utc).isoformat()

    # Upsert session
    cursor.execute("SELECT task_id FROM sessions WHERE task_id = ?", (task_id,))
    if cursor.fetchone():
        if agent == "claude":
            cursor.execute("UPDATE sessions SET claude_session_id = ?, updated_at = ? WHERE task_id = ?",
                          (session_id, timestamp, task_id))
        else:
            cursor.execute("UPDATE sessions SET gemini_session_id = ?, updated_at = ? WHERE task_id = ?",
                          (session_id, timestamp, task_id))
    else:
        if agent == "claude":
            cursor.execute("INSERT INTO sessions (task_id, claude_session_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
                          (task_id, session_id, timestamp, timestamp))
        else:
            cursor.execute("INSERT INTO sessions (task_id, gemini_session_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
                          (task_id, session_id, timestamp, timestamp))

    conn.commit()
    conn.close()
    print(f"📌 Stored {agent} session: {session_id[:8]}... for task {task_id}")

def check_inbox():
    """Check inbox for messages addressed to Gemini."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, from_llm, message_type, substr(content, 1, 100), timestamp
        FROM messages
        WHERE to_llm = 'gemini' AND acknowledged = 0
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("📭 No unread messages for Gemini")
        return

    print(f"📬 {len(rows)} unread message(s) for Gemini:\n")
    for row in rows:
        msg_id, from_llm, msg_type, preview, timestamp = row
        preview = preview.replace('\n', ' ')
        if len(preview) >= 100:
            preview += "..."
        print(f"  [{msg_id}] From: {from_llm} | Type: {msg_type} | {timestamp}")
        print(f"      {preview}\n")

def read_message(message_id: int):
    """Read a specific message."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp
        FROM messages
        WHERE id = ?
    """, (message_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"❌ Message {message_id} not found")
        return None

    msg = {
        "id": row[0],
        "task_id": row[1],
        "from": row[2],
        "to": row[3],
        "type": row[4],
        "content": row[5],
        "data": row[6],
        "timestamp": row[7]
    }

    print(f"📨 Message #{msg['id']}")
    print(f"   From: {msg['from']} → To: {msg['to']}")
    print(f"   Type: {msg['type']}")
    print(f"   Task: {msg['task_id'] or 'N/A'}")
    print(f"   Time: {msg['timestamp']}")
    print(f"\n{'='*60}\n")
    print(msg['content'])

    if msg['data']:
        print(f"\n{'='*60}")
        print("📎 Attached Data:")
        print(msg['data'])

    return msg

def send_message(content: str, task_id: str = None, msg_type: str = "response", data: str = None):
    """Send a message from Gemini to Claude."""
    conn = get_db()
    cursor = conn.cursor()

    timestamp = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
        INSERT INTO messages (task_id, from_llm, to_llm, message_type, content, data, timestamp, status)
        VALUES (?, 'gemini', 'claude', ?, ?, ?, ?, 'pending')
    """, (task_id, msg_type, content, data, timestamp))

    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"✅ Message sent to Claude (ID: {msg_id})")

    # Trigger macOS notification to alert human
    try:
        preview = content[:80].replace('"', '\\"').replace('\n', ' ')
        notification = f'display notification "{preview}..." with title "Gemini → Claude" subtitle "Tell Claude to check inbox"'
        subprocess.run(["osascript", "-e", notification], check=False, capture_output=True)
        print("🔔 Notification sent (tell Claude to check inbox)")
    except Exception:
        pass  # Notification is nice-to-have, don't fail if it doesn't work

    return msg_id


def ask_claude(content: str, task_id: str = None, msg_type: str = "query", data: str = None, new_session: bool = False):
    """Send message to Claude AND invoke Claude to process it. One-step communication.

    This is the PREFERRED method for Gemini to communicate with Claude.
    Combines send + process-claude into a single call.
    """
    # Step 1: Send the message
    msg_id = send_message(content, task_id, msg_type, data)

    # Step 2: Invoke Claude to process it
    print(f"\n🚀 Invoking Claude to process message #{msg_id}...")
    process_for_claude(msg_id, new_session)

    return msg_id


def send_to_gemini(content: str, task_id: str = None, msg_type: str = "query", data: str = None):
    """Send a message from Claude to Gemini (inverse of send_message)."""
    conn = get_db()
    cursor = conn.cursor()

    timestamp = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
        INSERT INTO messages (task_id, from_llm, to_llm, message_type, content, data, timestamp, status)
        VALUES (?, 'claude', 'gemini', ?, ?, ?, ?, 'pending')
    """, (task_id, msg_type, content, data, timestamp))

    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"✅ Message sent to Gemini (ID: {msg_id})")
    return msg_id


def ask_gemini(content: str, task_id: str = None, msg_type: str = "query", data: str = None, model: str = "gemini-3-flash-preview"):
    """Send message to Gemini AND invoke Gemini to process it. One-step communication.

    This is the PREFERRED method for Claude to communicate with Gemini.
    Combines send + process into a single call.
    """
    # Step 1: Send the message
    msg_id = send_to_gemini(content, task_id, msg_type, data)

    # Step 2: Invoke Gemini to process it
    print(f"\n🚀 Invoking Gemini to process message #{msg_id}...")
    process_and_respond(msg_id, model)

    return msg_id


def acknowledge(message_id: int):
    """Mark message as acknowledged."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE messages SET acknowledged = 1 WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()

    print(f"✓ Message {message_id} acknowledged")

def get_conversation(task_id: str):
    """Get full conversation for a task."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, from_llm, to_llm, message_type, content, timestamp
        FROM messages
        WHERE task_id = ?
        ORDER BY id ASC
    """, (task_id,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"❌ No messages found for task: {task_id}")
        return

    print(f"📜 Conversation: {task_id} ({len(rows)} messages)\n")
    print("="*70)

    for row in rows:
        msg_id, from_llm, to_llm, msg_type, content, timestamp = row
        print(f"\n[{msg_id}] {from_llm.upper()} → {to_llm.upper()} | {msg_type} | {timestamp}")
        print("-"*70)
        print(content[:500])
        if len(content) > 500:
            print(f"\n... [{len(content) - 500} more characters]")
        print()

def process_and_respond(message_id: int, model: str = "gemini-3-flash-preview"):
    """Read message, process with Gemini CLI, send response."""
    msg = read_message(message_id)
    if not msg:
        return

    # Prepare prompt for Gemini
    prompt = f"""You are Gemini, participating in a collaboration with Claude.
This is a message from Claude to you:

---
{msg['content']}
"""
    if msg['data']:
        prompt += f"""
---
Attached data:
{msg['data']}
"""
    prompt += """
---

Please respond appropriately. If this is a request, fulfill it.
If Claude asked for feedback, provide your honest assessment.
Format your response clearly.
"""

    print(f"\n🤖 Processing with Gemini ({model})...")

    try:
        # Call gemini-cli: -y (yolo/auto-accept), -p (non-interactive prompt)
        result = subprocess.run(
            ["gemini", "-m", model, "-y", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=300  # 5 min timeout
        )

        if result.returncode != 0:
            print(f"❌ Gemini CLI error: {result.stderr}")
            return

        response = result.stdout.strip()

        print(f"\n📝 Gemini's response ({len(response)} chars):\n")
        print(response[:500])
        if len(response) > 500:
            print(f"\n... [{len(response) - 500} more characters]")

        # Send response
        send_message(
            content=response,
            task_id=msg['task_id'],
            msg_type="response"
        )

        # Acknowledge original message
        acknowledge(message_id)

    except subprocess.TimeoutExpired:
        print("❌ Gemini CLI timed out")
    except FileNotFoundError:
        print("❌ gemini CLI not found. Is it installed?")


def process_for_claude(message_id: int, new_session: bool = False):
    """Read message addressed to Claude, invoke Claude CLI headlessly, send response back to Gemini.

    Session handling:
    - If task has existing Claude session ID: uses --resume to continue
    - If no session or new_session=True: creates new session with --session-id

    Args:
        message_id: The message ID to process
        new_session: If True, force a new session even if one exists
    """
    import uuid

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp
        FROM messages
        WHERE id = ? AND to_llm = 'claude'
    """, (message_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"❌ Message {message_id} not found or not addressed to Claude")
        return

    msg = {
        "id": row[0],
        "task_id": row[1],
        "from": row[2],
        "to": row[3],
        "type": row[4],
        "content": row[5],
        "data": row[6],
        "timestamp": row[7]
    }

    # Check for existing session
    session = get_session(msg['task_id']) if msg['task_id'] else {"claude": None, "gemini": None}
    claude_session_id = session["claude"] if not new_session else None

    print(f"📨 Message #{msg['id']}")
    print(f"   From: {msg['from']} → To: {msg['to']}")
    print(f"   Type: {msg['type']}")
    print(f"   Task: {msg['task_id'] or 'N/A'}")
    print(f"   Session: {claude_session_id[:8] + '...' if claude_session_id else 'NEW'}")

    # Prepare prompt for Claude
    prompt = f"""You are Claude, receiving a message from Gemini via the message broker.

Check and respond to this message from Gemini:

---
Task ID: {msg['task_id'] or 'none'}
Type: {msg['type']}
Content: {msg['content']}
"""
    if msg['data']:
        prompt += f"""
Attached data:
{msg['data']}
"""
    prompt += """
---

Respond appropriately using the MCP message broker tools:
1. Use mcp__message-broker__send_message to send your response to Gemini
2. Use mcp__message-broker__acknowledge_message to acknowledge this message

Be concise and direct in your response.
"""

    print(f"\n🤖 Processing with Claude CLI (headless)...")

    try:
        # Build command with session handling
        cmd = ["claude", "-p", prompt]

        if claude_session_id:
            # Resume existing session
            cmd.extend(["--resume", claude_session_id])
            print(f"   Resuming session: {claude_session_id[:8]}...")
        elif msg['task_id']:
            # Create new session with specific ID for task tracking
            new_id = str(uuid.uuid4())
            cmd.extend(["--session-id", new_id])
            set_session(msg['task_id'], "claude", new_id)
            print(f"   New session: {new_id[:8]}...")

        # Call claude CLI in print mode (headless)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout
            cwd=str(Path(__file__).parent.parent)  # Run from project root
        )

        if result.returncode != 0:
            print(f"❌ Claude CLI error: {result.stderr}")
            return

        response = result.stdout.strip()

        print(f"\n📝 Claude's response ({len(response)} chars):\n")
        print(response[:500])
        if len(response) > 500:
            print(f"\n... [{len(response) - 500} more characters]")

    except subprocess.TimeoutExpired:
        print("❌ Claude CLI timed out")
    except FileNotFoundError:
        print("❌ claude CLI not found. Is it installed?")


def interactive_mode():
    """Interactive mode for testing."""
    print("🔄 Gemini Bridge Interactive Mode")
    print("Commands: inbox, read <id>, send <text>, ack <id>, conv <task_id>, process <id>, quit")
    print()

    while True:
        try:
            cmd = input("gemini> ").strip()
            if not cmd:
                continue

            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None

            if action == "quit" or action == "q":
                break
            elif action == "inbox":
                check_inbox()
            elif action == "read" and arg:
                read_message(int(arg))
            elif action == "send" and arg:
                send_message(arg)
            elif action == "ack" and arg:
                acknowledge(int(arg))
            elif action == "conv" and arg:
                get_conversation(arg)
            elif action == "process" and arg:
                process_and_respond(int(arg))
            else:
                print("Unknown command. Try: inbox, read <id>, send <text>, ack <id>, conv <task>, process <id>")

        except KeyboardInterrupt:
            print("\nBye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Gemini Bridge - Claude/Gemini Communication")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # inbox
    subparsers.add_parser("inbox", help="Check inbox for messages from Claude")

    # read
    read_parser = subparsers.add_parser("read", help="Read a specific message")
    read_parser.add_argument("message_id", type=int, help="Message ID to read")

    # send
    send_parser = subparsers.add_parser("send", help="Send message to Claude")
    send_parser.add_argument("content", help="Message content")
    send_parser.add_argument("--task-id", help="Task ID for grouping")
    send_parser.add_argument("--type", default="response", help="Message type")
    send_parser.add_argument("--data", help="Path to data file to attach")

    # ack
    ack_parser = subparsers.add_parser("ack", help="Acknowledge a message")
    ack_parser.add_argument("message_id", type=int, help="Message ID")

    # conversation
    conv_parser = subparsers.add_parser("conversation", help="Get conversation history")
    conv_parser.add_argument("task_id", help="Task ID")

    # process (for Gemini)
    proc_parser = subparsers.add_parser("process", help="Process message with Gemini and respond")
    proc_parser.add_argument("message_id", type=int, help="Message ID to process")
    proc_parser.add_argument("--model", default="gemini-3-flash-preview", help="Gemini model")

    # process-claude (invoke Claude headlessly)
    proc_claude_parser = subparsers.add_parser("process-claude", help="Process message with Claude CLI (headless)")
    proc_claude_parser.add_argument("message_id", type=int, help="Message ID for Claude to process")
    proc_claude_parser.add_argument("--new-session", dest="new_session", action="store_true",
                                    help="Force new session even if one exists for this task")

    # ask-claude (PREFERRED: send + invoke in one step)
    ask_claude_parser = subparsers.add_parser("ask-claude", help="Send message AND invoke Claude (one-step communication)")
    ask_claude_parser.add_argument("content", help="Message content")
    ask_claude_parser.add_argument("--task-id", required=True, help="Task ID (required for session tracking)")
    ask_claude_parser.add_argument("--type", default="query", help="Message type (default: query)")
    ask_claude_parser.add_argument("--data", help="Path to data file to attach")
    ask_claude_parser.add_argument("--new-session", dest="new_session", action="store_true",
                                   help="Force new session even if one exists")

    # ask-gemini (PREFERRED: send + invoke in one step) - for Claude's use
    ask_gemini_parser = subparsers.add_parser("ask-gemini", help="Send message AND invoke Gemini (one-step communication)")
    ask_gemini_parser.add_argument("content", help="Message content")
    ask_gemini_parser.add_argument("--task-id", required=True, help="Task ID (required for session tracking)")
    ask_gemini_parser.add_argument("--type", default="query", help="Message type (default: query)")
    ask_gemini_parser.add_argument("--data", help="Path to data file to attach")
    ask_gemini_parser.add_argument("--model", default="gemini-3-flash-preview", help="Gemini model to use")

    # interactive
    subparsers.add_parser("interactive", help="Interactive mode")

    args = parser.parse_args()

    if args.command == "inbox":
        check_inbox()
    elif args.command == "read":
        read_message(args.message_id)
    elif args.command == "send":
        data = None
        if args.data:
            data = Path(args.data).read_text()
        send_message(args.content, args.task_id, args.type, data)
    elif args.command == "ack":
        acknowledge(args.message_id)
    elif args.command == "conversation":
        get_conversation(args.task_id)
    elif args.command == "process":
        process_and_respond(args.message_id, args.model)
    elif args.command == "process-claude":
        process_for_claude(args.message_id, args.new_session)
    elif args.command == "ask-claude":
        data = None
        if args.data:
            data = Path(args.data).read_text()
        ask_claude(args.content, args.task_id, args.type, data, args.new_session)
    elif args.command == "ask-gemini":
        data = None
        if args.data:
            data = Path(args.data).read_text()
        ask_gemini(args.content, args.task_id, args.type, data, args.model)
    elif args.command == "interactive":
        interactive_mode()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
