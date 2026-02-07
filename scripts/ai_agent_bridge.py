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
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Database path (same as MCP server uses)
DB_PATH = Path(__file__).parent.parent / ".mcp/servers/message-broker/messages.db"
PID_DIR = Path(__file__).parent.parent / ".mcp/servers/message-broker/pids"

# Resolve CLI paths at import time (before detached children lose PATH)
CLAUDE_CLI = shutil.which("claude") or "claude"
GEMINI_CLI = shutil.which("gemini") or "gemini"

# Snapshot environment for passing to detached children
_PARENT_ENV = os.environ.copy()


def _write_pid_file(agent: str, task_id: str, info: dict, pid: int = None):
    """Write a PID file for a running agent process."""
    PID_DIR.mkdir(parents=True, exist_ok=True)
    pid_file = PID_DIR / f"{agent}-{task_id}.json"
    pid_data = {
        "pid": pid or os.getpid(),
        "agent": agent,
        "started": datetime.now(timezone.utc).isoformat(),
        **info,
    }
    pid_file.write_text(json.dumps(pid_data, indent=2))


def _is_task_locked(agent: str, task_id: str) -> bool:
    """Check if another process is already working on this task.

    Returns True if locked (another process is alive), False if free.
    Cleans up stale PID files automatically.
    Excludes the current process's own PID (prevents self-lock).
    """
    if not task_id:
        return False

    pid_file = PID_DIR / f"{agent}-{task_id}.json"
    if not pid_file.exists():
        return False

    try:
        data = json.loads(pid_file.read_text())
        pid = data.get("pid", 0)
        if pid == os.getpid():
            return False  # It's us — not locked
        os.kill(pid, 0)  # Signal 0 = check if process exists
        return True  # Another process is alive — task is locked
    except (ProcessLookupError, PermissionError):
        # Process is dead — clean up stale PID file
        pid_file.unlink(missing_ok=True)
        return False
    except Exception:
        pid_file.unlink(missing_ok=True)
        return False


def _remove_pid_file(agent: str, task_id: str):
    """Remove PID file when process finishes."""
    pid_file = PID_DIR / f"{agent}-{task_id}.json"
    pid_file.unlink(missing_ok=True)


def bridge_status():
    """Show status of all running bridge processes."""
    if not PID_DIR.exists():
        print("No PID directory found. No processes tracked yet.")
        return

    pid_files = list(PID_DIR.glob("*.json"))
    if not pid_files:
        print("No bridge processes tracked.")
        return

    alive = []
    stale = []
    for pf in sorted(pid_files):
        try:
            data = json.loads(pf.read_text())
            pid = data.get("pid", 0)
            # Check if process is still running
            try:
                os.kill(pid, 0)  # Signal 0 = check existence
                alive.append((pf.name, data))
            except (ProcessLookupError, PermissionError):
                stale.append((pf.name, data))
                pf.unlink()  # Clean up stale PID files
        except Exception:
            stale.append((pf.name, {}))
            pf.unlink()

    if alive:
        print(f"🟢 {len(alive)} running bridge process(es):\n")
        for name, data in alive:
            print(f"  {name}")
            print(f"    PID: {data.get('pid')}")
            print(f"    Agent: {data.get('agent')}")
            print(f"    Task: {data.get('task_id')}")
            print(f"    Model: {data.get('model', 'N/A')}")
            print(f"    Started: {data.get('started')}")
            # Show log file tail
            log_dir = Path(__file__).parent.parent / ".mcp/servers/message-broker/logs"
            log_file = log_dir / f"{data.get('agent')}-{data.get('task_id')}.log"
            if log_file.exists():
                lines = log_file.read_text().strip().split('\n')
                last_line = lines[-1] if lines else "(empty)"
                print(f"    Log: {log_file}")
                print(f"    Last output: {last_line[:100]}")
            print()
    else:
        print("No running bridge processes.")

    if stale:
        print(f"🔴 Cleaned up {len(stale)} stale PID file(s): {', '.join(n for n, _ in stale)}")

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

    Mode auto-detection: request/handoff → async (fire-and-forget), query/response → sync.

    Args:
        from_llm: Sender agent family (gemini, claude) - for routing
        from_model: Exact model ID of sender (e.g., 'claude-opus-4-5-20251101')
        to_model: Target model ID (e.g., 'claude-sonnet-4')
    """
    # Step 1: Send the message
    msg_id = send_message(content, task_id, msg_type, data, from_llm=from_llm, to_llm="claude", from_model=from_model, to_model=to_model)

    # Step 2: Invoke Claude to process it (mode auto-detected from message type)
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

def process_and_respond(message_id: int, model: str = "gemini-3-flash-preview", fire_and_forget: bool = False, no_timeout: bool = False):
    """Read message, process with Gemini CLI, send response.

    Args:
        fire_and_forget: If True, launch the bridge ITSELF as a background process
            running in no-timeout sync mode. The bridge captures stdout and routes
            the response — Gemini doesn't need to self-report.
        no_timeout: Internal flag. When True, run sync without timeout.
            Used by fire-and-forget to re-invoke the bridge as a background process.
    """
    msg = read_message(message_id)
    if not msg:
        return

    # Auto-detect mode from message type if not explicitly set
    if not no_timeout and not fire_and_forget and msg['type'] in ('request', 'handoff'):
        fire_and_forget = True
        print("ℹ️  Auto-enabled fire-and-forget for request/handoff (long-running task)")

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

    if fire_and_forget:
        # ASYNC: Launch the BRIDGE ITSELF as a background process in no-timeout mode.
        # The bridge still captures stdout and routes the response — Gemini doesn't
        # need to self-report. This is just sync mode without a timeout, running in bg.
        task_key = msg['task_id'] or str(message_id)

        # LOCK CHECK: Don't launch if another process is already working on this task
        if _is_task_locked("gemini", task_key):
            print(f"⏸️  Task '{task_key}' is already being processed by another Gemini bridge. Skipping.")
            return

        log_dir = Path(__file__).parent.parent / ".mcp/servers/message-broker/logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"gemini-{task_key}.log"

        print(f"\n🚀 Launching bridge in background (no timeout)...")
        print(f"   Log: {log_file}")
        print(f"   Bridge will capture Gemini's response and route it when done.")

        try:
            bridge_cmd = [
                sys.executable, str(Path(__file__)),
                "process", str(message_id),
                "--model", model,
                "--no-timeout"
            ]
            lf = open(log_file, "w")
            proc = subprocess.Popen(
                bridge_cmd,
                stdout=lf,
                stderr=subprocess.STDOUT,
                cwd=str(Path(__file__).parent.parent),
                env=_PARENT_ENV,  # Inherit PATH so CLI tools are found
                start_new_session=True  # Survive parent exit
            )
            print(f"   PID: {proc.pid}")

            # Write PID file for the CHILD process so lock checks work
            _write_pid_file("gemini", task_key, {
                "message_id": message_id,
                "task_id": msg.get('task_id'),
                "model": model,
                "mode": "fire-and-forget",
            }, pid=proc.pid)

        except FileNotFoundError:
            print("❌ Python or bridge script not found")
    else:
        # SYNC: Run Gemini with STREAMING output (visible in log in real-time)
        import time
        task_key = msg.get('task_id') or str(message_id)
        timeout_val = None if no_timeout else 300
        mode_label = "no-timeout" if no_timeout else "sync, 5 min timeout"

        # LOCK CHECK: Don't process if another bridge is already working on this task
        if _is_task_locked("gemini", task_key):
            print(f"⏸️  Task '{task_key}' is already being processed by another Gemini bridge. Skipping.")
            return

        print(f"\n🤖 Processing with Gemini ({model}) [{mode_label}]...")
        sys.stdout.flush()

        # Write PID file for status tracking and locking
        _write_pid_file("gemini", task_key, {
            "message_id": message_id,
            "task_id": msg.get('task_id'),
            "model": model,
            "mode": mode_label,
        })

        max_retries = 5
        base_delay = 30  # seconds — respect the quota, don't hammer

        for attempt in range(max_retries):
            try:
                # Stream stdout line-by-line so the log file updates in real-time
                proc = subprocess.Popen(
                    [GEMINI_CLI, "-m", model, "-y", "-p", prompt],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=str(Path(__file__).parent.parent),
                    env=_PARENT_ENV
                )

                # Read stdout in real-time, collect for response routing
                output_lines = []
                for line in proc.stdout:
                    print(line, end='')  # Real-time to log file
                    sys.stdout.flush()
                    output_lines.append(line)

                # Wait for process to finish, get stderr
                proc.wait()
                stderr = proc.stderr.read() if proc.stderr else ""

                if proc.returncode != 0:
                    # Detect quota/rate limit errors
                    if "exhausted your capacity" in stderr or "429" in stderr or "quota" in stderr.lower():
                        delay = base_delay * (2 ** attempt)  # 30s, 60s, 120s, 240s, 480s
                        if attempt < max_retries - 1:
                            print(f"\n⏳ Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {delay}s...")
                            sys.stdout.flush()
                            time.sleep(delay)
                            continue
                        else:
                            print(f"\n❌ Rate limited after {max_retries} attempts. Giving up.")
                            _remove_pid_file("gemini", msg.get('task_id') or str(message_id))
                            return
                    print(f"\n❌ Gemini CLI error (exit {proc.returncode}): {stderr[:500]}")
                    sys.stdout.flush()
                    # Non-zero exit but has output? Gemini tool calls may cause exit 1.
                    # If we got substantial output, treat as success.
                    if not output_lines or len(''.join(output_lines).strip()) < 50:
                        _remove_pid_file("gemini", msg.get('task_id') or str(message_id))
                        return

                response = ''.join(output_lines).strip()

                print(f"\n\n{'─' * 40}")
                print(f"✅ Gemini finished ({len(response)} chars)")
                sys.stdout.flush()

                # Send response with model info
                send_message(
                    content=response,
                    task_id=msg['task_id'],
                    msg_type="response",
                    from_llm="gemini",
                    to_llm="claude",
                    from_model=model,
                    to_model=None
                )

                # Acknowledge original message
                acknowledge(message_id)
                _remove_pid_file("gemini", msg.get('task_id') or str(message_id))
                break  # Success — exit retry loop

            except subprocess.TimeoutExpired:
                proc.kill()
                print("\n❌ Gemini CLI timed out (5 min sync limit)")
                _remove_pid_file("gemini", msg.get('task_id') or str(message_id))
                return
            except FileNotFoundError:
                print("❌ gemini CLI not found. Is it installed?")
                _remove_pid_file("gemini", msg.get('task_id') or str(message_id))
                return


def process_for_claude(message_id: int, new_session: bool = False, fire_and_forget: bool = False, no_timeout: bool = False):
    """Read message addressed to Claude, invoke Claude CLI headlessly, send response back to sender.

    Works symmetrically with process_and_respond (Gemini):
    - Sync: Captures Claude's stdout, routes response via send_message()
    - Async (fire-and-forget): Launches the bridge itself as a bg process in no-timeout mode

    Args:
        message_id: The message ID to process
        new_session: If True, force a new session even if one exists
        fire_and_forget: If True, re-launch bridge in background with --no-timeout.
        no_timeout: Internal flag. When True, run sync without timeout.
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

    # Auto-detect mode from message type if not explicitly set
    if not no_timeout and not fire_and_forget and msg['type'] in ('request', 'handoff'):
        fire_and_forget = True
        print("ℹ️  Auto-enabled fire-and-forget for request/handoff (long-running task)")

    # Check for existing session
    session = get_session(msg['task_id']) if msg['task_id'] else {"claude": None, "gemini": None}
    claude_session_id = session["claude"] if not new_session else None

    print(f"📨 Message #{msg['id']}")
    print(f"   From: {msg['from']} → To: {msg['to']}")
    print(f"   Type: {msg['type']}")
    print(f"   Task: {msg['task_id'] or 'N/A'}")
    print(f"   Mode: {'🚀 async (bridge bg)' if fire_and_forget else '⏳ sync' + (' (no timeout)' if no_timeout else '')}")
    print(f"   Session: {claude_session_id[:8] + '...' if claude_session_id else 'NEW'}")

    # Prepare prompt for Claude
    prompt = f"""You are Claude, receiving a message from {msg['from'].title()} via the message broker.

---
Task ID: {msg['task_id'] or 'none'}
Type: {msg['type']}
From: {msg['from']}

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

Respond directly to this message. Be concise and helpful.
Your response will be automatically sent back to the sender via the message broker.
Do NOT use MCP tools to send your response - just output your response directly.
"""

    # Build command with session handling (use resolved path for detached children)
    cmd = [CLAUDE_CLI, "-p", prompt]

    if claude_session_id:
        cmd.extend(["--resume", claude_session_id])
        print(f"   Resuming session: {claude_session_id[:8]}...")
    elif msg['task_id']:
        new_id = str(uuid.uuid4())
        cmd.extend(["--session-id", new_id])
        set_session(msg['task_id'], "claude", new_id)
        print(f"   New session: {new_id[:8]}...")

    if fire_and_forget:
        # ASYNC: Launch the BRIDGE ITSELF as a background process in no-timeout mode.
        task_key = msg['task_id'] or str(message_id)

        # LOCK CHECK: Don't launch if another process is already working on this task
        if _is_task_locked("claude", task_key):
            print(f"⏸️  Task '{task_key}' is already being processed by another Claude bridge. Skipping.")
            return

        log_dir = Path(__file__).parent.parent / ".mcp/servers/message-broker/logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"claude-{task_key}.log"

        print(f"\n🚀 Launching bridge in background (no timeout)...")
        print(f"   Log: {log_file}")
        print(f"   Bridge will capture Claude's response and route it when done.")

        try:
            bridge_cmd = [
                sys.executable, str(Path(__file__)),
                "process-claude", str(message_id),
                "--no-timeout"
            ]
            if new_session:
                bridge_cmd.append("--new-session")
            lf = open(log_file, "w")
            proc = subprocess.Popen(
                bridge_cmd,
                stdout=lf,
                stderr=subprocess.STDOUT,
                cwd=str(Path(__file__).parent.parent),
                env=_PARENT_ENV,  # Inherit PATH so CLI tools are found
                start_new_session=True  # Survive parent exit
            )
            print(f"   PID: {proc.pid}")

            # Write PID file for the CHILD process so lock checks work
            _write_pid_file("claude", task_key, {
                "message_id": message_id,
                "task_id": msg.get('task_id'),
                "mode": "fire-and-forget",
            }, pid=proc.pid)

        except FileNotFoundError:
            print("❌ Python or bridge script not found")
    else:
        # SYNC: Run Claude with STREAMING output (visible in log in real-time)
        task_key = msg.get('task_id') or str(message_id)
        timeout_val = None if no_timeout else 300
        mode_label = "no-timeout" if no_timeout else "sync, 5 min timeout"

        # LOCK CHECK: Don't process if another bridge is already working on this task
        if _is_task_locked("claude", task_key):
            print(f"⏸️  Task '{task_key}' is already being processed by another Claude bridge. Skipping.")
            return

        print(f"\n🤖 Processing with Claude CLI (headless) [{mode_label}]...")
        sys.stdout.flush()

        # Write PID file for status tracking and locking
        _write_pid_file("claude", task_key, {
            "message_id": message_id,
            "task_id": msg.get('task_id'),
            "mode": mode_label,
        })

        try:
            # Stream stdout line-by-line so the log file updates in real-time
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                env=_PARENT_ENV
            )

            output_lines = []
            for line in proc.stdout:
                print(line, end='')
                sys.stdout.flush()
                output_lines.append(line)

            proc.wait()
            stderr = proc.stderr.read() if proc.stderr else ""

            if proc.returncode != 0:
                error_msg = stderr.strip() or "Unknown error"
                print(f"\n❌ Claude CLI error: {error_msg[:500]}")
                sys.stdout.flush()

                send_message(
                    content=f"[Bridge Error] Claude CLI failed:\n{error_msg[:500]}",
                    task_id=msg['task_id'],
                    msg_type="error",
                    from_llm="claude",
                    to_llm=msg['from'],
                    from_model="claude-bridge-error"
                )
                acknowledge(message_id)
                _remove_pid_file("claude", msg.get('task_id') or str(message_id))
                return

            response = ''.join(output_lines).strip()

            print(f"\n\n{'─' * 40}")
            print(f"✅ Claude finished ({len(response)} chars)")
            sys.stdout.flush()

            send_message(
                content=response,
                task_id=msg['task_id'],
                msg_type="response",
                from_llm="claude",
                to_llm=msg['from'],
                from_model=None,
                to_model=None
            )

            acknowledge(message_id)
            _remove_pid_file("claude", msg.get('task_id') or str(message_id))

        except subprocess.TimeoutExpired:
            proc.kill()
            print("\n❌ Claude CLI timed out (5 min sync limit)")
            send_message(
                content="[Bridge Error] Claude CLI timed out after 5 minutes. Consider using async mode for long tasks.",
                task_id=msg['task_id'],
                msg_type="error",
                from_llm="claude",
                to_llm=msg['from'],
                from_model="claude-bridge-timeout"
            )
            acknowledge(message_id)
            _remove_pid_file("claude", msg.get('task_id') or str(message_id))
        except FileNotFoundError:
            print("❌ claude CLI not found. Is it installed?")
            send_message(
                content="[Bridge Error] Claude CLI not found on system",
                task_id=msg['task_id'],
                msg_type="error",
                from_llm="claude",
                to_llm=msg['from'],
                from_model="claude-bridge-not-found"
            )
            _remove_pid_file("claude", msg.get('task_id') or str(message_id))


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
    proc_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true",
                             help="Run sync without timeout (used internally by fire-and-forget)")

    # process-claude (invoke Claude headlessly)
    proc_claude_parser = subparsers.add_parser("process-claude", help="Process message with Claude CLI (headless)")
    proc_claude_parser.add_argument("message_id", type=int, help="Message ID for Claude to process")
    proc_claude_parser.add_argument("--new-session", dest="new_session", action="store_true",
                                    help="Force new session even if one exists for this task")
    proc_claude_parser.add_argument("--async", dest="fire_and_forget", action="store_true",
                                    help="Launch Claude in background (no timeout). Auto-enabled for request/handoff types.")
    proc_claude_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true",
                                    help="Run sync without timeout (used internally by fire-and-forget)")

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

    # status
    subparsers.add_parser("status", help="Show running bridge processes")

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
        process_and_respond(args.message_id, args.model, no_timeout=args.no_timeout)
    elif args.command == "process-claude":
        process_for_claude(args.message_id, args.new_session, args.fire_and_forget, args.no_timeout)
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
    elif args.command == "status":
        bridge_status()
    elif args.command == "interactive":
        interactive_mode()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()