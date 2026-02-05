#!/usr/bin/env python3
"""
AI Agent Bridge - Multi-agent communication bridge via MCP Message Broker

This script allows AI agents (Gemini, Claude, etc.) to participate in a 
bidirectional communication system by reading from and writing to the 
same SQLite database that the MCP Message Broker uses.

Usage:
    # Check for messages
    python scripts/ai_agent_bridge.py inbox

    # Get a specific message
    python scripts/ai_agent_bridge.py read <message_id>

    # Send a message to Claude
    python scripts/ai_agent_bridge.py send "Your message content" --to claude

    # Send with structured data
    python scripts/ai_agent_bridge.py send "Message" --data data.yaml --task-id my-task

    # Get full conversation
    python scripts/ai_agent_bridge.py conversation <task_id>

    # Process and respond (read message, pipe to LLM CLI, send response)
    python scripts/ai_agent_bridge.py process <message_id>
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
    # Ensure messages table exists with all columns
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
            acknowledged INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending'
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
    
    # Check for missing columns (migration for existing DBs)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(messages)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "status" not in columns:
        print("🔧 Migrating database: adding 'status' column to 'messages' table")
        conn.execute("ALTER TABLE messages ADD COLUMN status TEXT DEFAULT 'pending'")
        conn.commit()
        
    # Ensure sessions table exists
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

def check_inbox(for_llm: str = "gemini"):
    """Check inbox for messages addressed to an agent."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, from_llm, message_type, substr(content, 1, 100), timestamp
        FROM messages
        WHERE to_llm = ? AND acknowledged = 0
        ORDER BY id ASC
    """, (for_llm,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"📭 No unread messages for {for_llm}")
        return

    print(f"📬 {len(rows)} unread message(s) for {for_llm}:\n")
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

def send_message(content: str, task_id: str = None, msg_type: str = "response", data: str = None, from_llm: str = "gemini", to_llm: str = "claude", from_model: str = None, to_model: str = None):
    """Send a message between agents.

    Args:
        from_llm: Agent family (gemini, claude) - for routing
        to_llm: Target agent family - for routing
        from_model: Exact model ID (e.g., 'claude-opus-4-5-20251101', 'gemini-3-flash-preview')
        to_model: Target model ID
    """
    conn = get_db()
    cursor = conn.cursor()

    timestamp = datetime.now(timezone.utc).isoformat()

    # Store model info in data as JSON if provided
    metadata = {}
    if data:
        try:
            metadata = json.loads(data) if isinstance(data, str) and data.startswith('{') else {"raw": data}
        except:
            metadata = {"raw": data}
    if from_model:
        metadata["from_model"] = from_model
    if to_model:
        metadata["to_model"] = to_model

    data_json = json.dumps(metadata) if metadata else None

    cursor.execute("""
        INSERT INTO messages (task_id, from_llm, to_llm, message_type, content, data, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (task_id, from_llm, to_llm, msg_type, content, data_json, timestamp))

    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"✅ Message sent to {to_llm.title()} (ID: {msg_id})")

    # Trigger macOS notification to alert human
    try:
        preview = content[:80].replace('"', '\\"').replace('\n', ' ')
        notification = f'display notification "{preview}..." with title "{from_llm.title()} → {to_llm.title()}" subtitle "Check inbox"'
        subprocess.run(["osascript", "-e", notification], check=False, capture_output=True)
    except Exception:
        pass  # Notification is nice-to-have, don't fail if it doesn't work

    return msg_id


def ask_claude(content: str, task_id: str = None, msg_type: str = "query", data: str = None, new_session: bool = False, from_llm: str = "gemini", from_model: str = None, to_model: str = None):
    """Send message to Claude AND invoke Claude to process it. One-step communication.

    Args:
        from_llm: Sender agent family (gemini, claude) - for routing
        from_model: Exact model ID of sender (e.g., 'claude-opus-4-5-20251101')
        to_model: Target model ID (e.g., 'claude-sonnet-4')
    """
    # Step 1: Send the message
    msg_id = send_message(content, task_id, msg_type, data, from_llm=from_llm, to_llm="claude", from_model=from_model, to_model=to_model)

    # Step 2: Invoke Claude to process it
    print(f"\n🚀 Invoking Claude to process message #{msg_id}...")
    process_for_claude(msg_id, new_session)

    return msg_id


def send_to_gemini(content: str, task_id: str = None, msg_type: str = "query", data: str = None, from_model: str = None, to_model: str = None):
    """Send a message from Claude to Gemini."""
    return send_message(content, task_id, msg_type, data, from_llm="claude", to_llm="gemini", from_model=from_model, to_model=to_model)


def ask_gemini(content: str, task_id: str = None, msg_type: str = "query", data: str = None, model: str = "gemini-3-flash-preview", from_model: str = None, async_mode: bool = False):
    """Send message to Gemini AND optionally invoke Gemini to process it.

    Args:
        model: Gemini model to use (default: gemini-3-flash-preview)
        from_model: Exact model ID of sender (e.g., 'claude-opus-4-5-20251101')
        async_mode: If True, just queue message without invoking Gemini CLI.
                   Auto-enabled for 'handoff' type messages (complex tasks).
    """
    # Auto-enable async for handoff type (complex tasks shouldn't expect immediate response)
    if msg_type == "handoff":
        async_mode = True
        print("ℹ️  Async mode auto-enabled for handoff (complex task)")

    # Validation: Warn if handoff message is too long (handoff anti-pattern)
    # Only warn for handoff type - help/query messages can be long
    HANDOFF_WARNING_THRESHOLD = 500  # chars
    if msg_type == "handoff" and len(content) > HANDOFF_WARNING_THRESHOLD and task_id and task_id.startswith("gh-"):
        print(f"⚠️  WARNING: Handoff message is {len(content)} chars (>{HANDOFF_WARNING_THRESHOLD})")
        print(f"   For task handoffs, the GitHub issue should contain details.")
        print(f"   Consider sending a SHORT message with issue reference only:")
        print(f"   'Issue #{task_id.replace('gh-', '')} is assigned to you. Read it for details.'")
        print()

    # Step 1: Send the message (model param becomes to_model)
    msg_id = send_to_gemini(content, task_id, msg_type, data, from_model=from_model, to_model=model)

    # Step 2: Invoke Gemini to process it (unless async mode)
    if async_mode:
        print(f"\n📥 Message #{msg_id} queued for Gemini (async mode - no immediate invocation)")
        print(f"   Gemini will see this in his inbox when he starts a session.")
        print(f"   To trigger manually: .venv/bin/python scripts/ai_agent_bridge.py process {msg_id}")
    else:
        print(f"\n🚀 Invoking Gemini to process message #{msg_id}...")
        process_and_respond(msg_id, model)

    return msg_id


def acknowledge(message_ids: list[int]):
    """Mark message(s) as acknowledged.

    Args:
        message_ids: Single ID or list of message IDs to acknowledge
    """
    if isinstance(message_ids, int):
        message_ids = [message_ids]

    conn = get_db()
    cursor = conn.cursor()

    for msg_id in message_ids:
        cursor.execute("UPDATE messages SET acknowledged = 1 WHERE id = ?", (msg_id,))

    conn.commit()
    conn.close()

    if len(message_ids) == 1:
        print(f"✓ Message {message_ids[0]} acknowledged")
    else:
        print(f"✓ {len(message_ids)} messages acknowledged: {', '.join(map(str, message_ids))}")


def acknowledge_all(for_llm: str):
    """Acknowledge ALL unread messages for a given agent.

    Args:
        for_llm: 'claude' or 'gemini'
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get unread message IDs first
    cursor.execute("""
        SELECT id FROM messages
        WHERE to_llm = ? AND acknowledged = 0
        ORDER BY id ASC
    """, (for_llm,))

    rows = cursor.fetchall()

    if not rows:
        print(f"📭 No unread messages to acknowledge for {for_llm}")
        conn.close()
        return

    msg_ids = [row[0] for row in rows]

    # Acknowledge all
    cursor.execute("""
        UPDATE messages SET acknowledged = 1
        WHERE to_llm = ? AND acknowledged = 0
    """, (for_llm,))

    conn.commit()
    conn.close()

    print(f"✓ Acknowledged {len(msg_ids)} messages for {for_llm}: {', '.join(map(str, msg_ids))}")

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
            timeout=600  # 10 min timeout for long-form content
        )

        if result.returncode != 0:
            print(f"❌ Gemini CLI error: {result.stderr}")
            return

        response = result.stdout.strip()

        print(f"\n📝 Gemini's response ({len(response)} chars):\n")
        print(response[:500])
        if len(response) > 500:
            print(f"\n... [{len(response) - 500} more characters]")

        # Send response with model info
        send_message(
            content=response,
            task_id=msg['task_id'],
            msg_type="response",
            from_llm="gemini",
            to_llm="claude",
            from_model=model,  # Track which Gemini model responded
            to_model=None  # Response doesn't target specific model
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
1. Use mcp__message-broker__send_message to send your response with these params:
   - to: "gemini" (or sender from above)
   - from_llm: "claude"
   - from_model: YOUR_MODEL_ID (e.g., "claude-sonnet-4-20250514" - use your actual model ID)
   - content: your response
   - task_id: same as above
   - message_type: "response"
2. Use mcp__message-broker__acknowledge_message to acknowledge this message

IMPORTANT: Always include from_model with your exact model ID for audit tracking.
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
            timeout=600,  # 10 min timeout
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
            
        # IMPORTANT: Acknowledge the message so it's not processed again
        acknowledge(message_id)

    except subprocess.TimeoutExpired:
        print("❌ Claude CLI timed out")
    except FileNotFoundError:
        print("❌ claude CLI not found. Is it installed?")


def interactive_mode():
    """Interactive mode for testing."""
    print("🔄 AI Agent Bridge Interactive Mode")
    print("Commands: inbox [agent], read <id>, send <text> --to <agent>, ack <id>, conv <task_id>, process <id>, quit")
    print()

    while True:
        try:
            cmd = input("bridge> ").strip()
            if not cmd:
                continue

            if cmd.lower() in ["quit", "q", "exit"]:
                break
                
            # Simple parser for interactive mode
            parts = cmd.split()
            action = parts[0].lower()
            
            if action == "inbox":
                agent = parts[1] if len(parts) > 1 else "gemini"
                check_inbox(agent)
            elif action == "read" and len(parts) > 1:
                read_message(int(parts[1]))
            elif action == "send" and len(parts) > 1:
                # Very basic send for interactive mode
                content = " ".join(parts[1:])
                send_message(content)
            elif action == "ack" and len(parts) > 1:
                ids = [int(x) for x in parts[1:]]
                acknowledge(ids)
            elif action == "conv" and len(parts) > 1:
                get_conversation(parts[1])
            elif action == "process" and len(parts) > 1:
                process_and_respond(int(parts[1]))
            else:
                print("Unknown command or missing arguments.")

        except KeyboardInterrupt:
            print("\nBye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def process_all_gemini(model: str = "gemini-3-flash-preview"):
    """Process ALL unread messages for Gemini in batch."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task_id, from_llm, message_type, substr(content, 1, 50)
        FROM messages
        WHERE to_llm = 'gemini' AND acknowledged = 0
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("📭 No unread messages for Gemini to process")
        return

    print(f"📬 Processing {len(rows)} unread message(s) for Gemini...\n")

    success = 0
    failed = 0

    for row in rows:
        msg_id, task_id, from_llm, msg_type, preview = row
        preview = preview.replace('\n', ' ')[:40]
        print(f"━━━ Processing [{msg_id}] from {from_llm}: {preview}...")

        try:
            process_and_respond(msg_id, model)
            success += 1
            print(f"    ✅ Done\n")
        except Exception as e:
            failed += 1
            print(f"    ❌ Failed: {e}\n")

    print(f"\n{'═' * 50}")
    print(f"📊 Results: {success} succeeded, {failed} failed out of {len(rows)} total")


def process_all_claude(new_session: bool = False):
    """Process ALL unread messages for Claude in batch (headless)."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task_id, from_llm, message_type, substr(content, 1, 50)
        FROM messages
        WHERE to_llm = 'claude' AND acknowledged = 0
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("📭 No unread messages for Claude to process")
        return

    print(f"📬 Processing {len(rows)} unread message(s) for Claude (headless)...\n")

    success = 0
    failed = 0

    for row in rows:
        msg_id, task_id, from_llm, msg_type, preview = row
        preview = preview.replace('\n', ' ')[:40]
        print(f"━━━ Processing [{msg_id}] from {from_llm}: {preview}...")

        try:
            process_for_claude(msg_id, new_session)
            success += 1
            print(f"    ✅ Done\n")
        except Exception as e:
            failed += 1
            print(f"    ❌ Failed: {e}\n")

    print(f"\n{'═' * 50}")
    print(f"📊 Results: {success} succeeded, {failed} failed out of {len(rows)} total")


def main():
    parser = argparse.ArgumentParser(description="AI Agent Bridge - Claude/Gemini/LLM Communication")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # inbox
    inbox_parser = subparsers.add_parser("inbox", help="Check inbox for messages")
    inbox_parser.add_argument("--for", dest="for_llm", default="gemini", choices=['gemini', 'claude'], 
                             help="Check inbox for which agent (default: gemini)")

    # read
    read_parser = subparsers.add_parser("read", help="Read a specific message")
    read_parser.add_argument("message_id", type=int, help="Message ID to read")

    # send
    send_parser = subparsers.add_parser("send", help="Send message to another agent")
    send_parser.add_argument("content", help="Message content")
    send_parser.add_argument("--to", dest="to_llm", default="claude", choices=['claude', 'gemini'],
                            help="Target agent (default: claude)")
    send_parser.add_argument("--from", dest="from_llm", default="gemini",
                            help="Sender agent name (default: gemini)")
    send_parser.add_argument("--task-id", help="Task ID for grouping")
    send_parser.add_argument("--type", default="response", help="Message type")
    send_parser.add_argument("--data", help="Path to data file to attach")
    send_parser.add_argument("--from-model", dest="from_model", help="Specific model ID of sender")
    send_parser.add_argument("--to-model", dest="to_model", help="Specific model ID of receiver")

    # ack (supports multiple IDs)
    ack_parser = subparsers.add_parser("ack", help="Acknowledge message(s)")
    ack_parser.add_argument("message_ids", type=int, nargs='+', help="Message ID(s) to acknowledge")

    # ack-all (acknowledge all unread for an agent)
    ack_all_parser = subparsers.add_parser("ack-all", help="Acknowledge ALL unread messages for an agent")
    ack_all_parser.add_argument("agent", choices=['claude', 'gemini'], help="Agent whose inbox to clear")

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
    ask_claude_parser.add_argument("--from", dest="from_llm", default="gemini",
                                   help="Sender agent family (gemini, claude). Default: gemini")
    ask_claude_parser.add_argument("--from-model", dest="from_model",
                                   help="Exact sender model ID (e.g., claude-opus-4-5-20251101)")
    ask_claude_parser.add_argument("--to-model", dest="to_model",
                                   help="Target model ID (e.g., claude-sonnet-4)")

    # ask-gemini (PREFERRED: send + invoke in one step) - for Claude's use
    ask_gemini_parser = subparsers.add_parser("ask-gemini", help="Send message AND invoke Gemini (one-step communication)")
    ask_gemini_parser.add_argument("content", help="Message content")
    ask_gemini_parser.add_argument("--task-id", required=True, help="Task ID (required for session tracking)")
    ask_gemini_parser.add_argument("--type", default="query", help="Message type (default: query)")
    ask_gemini_parser.add_argument("--data", help="Path to data file to attach")
    ask_gemini_parser.add_argument("--model", default="gemini-3-flash-preview", help="Gemini model to use (also used as to_model)")
    ask_gemini_parser.add_argument("--from-model", dest="from_model",
                                   help="Exact sender model ID (e.g., claude-opus-4-5-20251101)")
    ask_gemini_parser.add_argument("--async", dest="async_mode", action="store_true",
                                   help="Queue only, don't invoke Gemini CLI (for complex tasks). Auto-enabled for --type handoff")

    # process-all (batch process all unread for Gemini)
    proc_all_parser = subparsers.add_parser("process-all", help="Process ALL unread messages with Gemini")
    proc_all_parser.add_argument("--model", default="gemini-3-flash-preview", help="Gemini model")

    # process-claude-all (batch process all unread for Claude)
    proc_claude_all_parser = subparsers.add_parser("process-claude-all", help="Process ALL unread messages with Claude")
    proc_claude_all_parser.add_argument("--new-session", dest="new_session", action="store_true",
                                        help="Force new sessions for each message")

    # interactive
    subparsers.add_parser("interactive", help="Interactive mode")

    args = parser.parse_args()

    if args.command == "inbox":
        check_inbox(args.for_llm)
    elif args.command == "read":
        read_message(args.message_id)
    elif args.command == "send":
        data = None
        if args.data:
            data = Path(args.data).read_text()
        send_message(args.content, args.task_id, args.type, data, args.from_llm, args.to_llm, args.from_model, args.to_model)
    elif args.command == "ack":
        acknowledge(args.message_ids)
    elif args.command == "ack-all":
        acknowledge_all(args.agent)
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
        ask_claude(args.content, args.task_id, args.type, data, args.new_session, args.from_llm, args.from_model, args.to_model)
    elif args.command == "ask-gemini":
        data = None
        if args.data:
            data = Path(args.data).read_text()
        ask_gemini(args.content, args.task_id, args.type, data, args.model, getattr(args, 'from_model', None), getattr(args, 'async_mode', False))
    elif args.command == "process-all":
        process_all_gemini(args.model)
    elif args.command == "process-claude-all":
        process_all_claude(args.new_session)
    elif args.command == "interactive":
        interactive_mode()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()