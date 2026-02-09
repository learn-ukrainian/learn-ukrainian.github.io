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
import atexit
import json
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add repo root to sys.path so we can import from scripts.*
REPO_ROOT = Path(__file__).parent.parent
sys.path.append(str(REPO_ROOT))

from scripts.utils.logging_utils import setup_logging

# Setup logging
logger = logging.getLogger("ai_agent_bridge")

# Token cost estimation (USD per 1M tokens)
# Values for Gemini 1.5 (approximate)
MODEL_COSTS = {
    "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "default": {"input": 0.50, "output": 1.50}
}


# Database path (same as MCP server uses)
DB_PATH = Path(__file__).parent.parent / ".mcp/servers/message-broker/messages.db"
PID_DIR = Path(__file__).parent.parent / ".mcp/servers/message-broker/pids"

# Resolve CLI paths at import time (before detached children lose PATH)
CLAUDE_CLI = shutil.which("claude") or "claude"
GEMINI_CLI = shutil.which("gemini") or "gemini"

# Snapshot environment for passing to detached children
_PARENT_ENV = os.environ.copy()


def _git_status_snapshot() -> set[str]:
    """Capture current set of modified/untracked files for post-validation."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
            cwd=str(Path(__file__).parent.parent)
        )
        return set(result.stdout.strip().splitlines()) if result.stdout.strip() else set()
    except Exception:
        return set()


def _validate_file_writes(pre_snapshot: set[str], allowed_path: str) -> list[str]:
    """Compare git status before/after to detect unauthorized file writes.

    Returns list of violation descriptions (empty = clean).
    """
    post_snapshot = _git_status_snapshot()
    new_changes = post_snapshot - pre_snapshot
    if not new_changes:
        return []

    # Normalize allowed path to be relative to repo root
    repo_root = Path(__file__).parent.parent
    try:
        allowed_rel = str(Path(allowed_path).resolve().relative_to(repo_root.resolve()))
    except ValueError:
        allowed_rel = allowed_path

    violations = []
    for change in new_changes:
        # git status --porcelain format: "XY filename" or "XY filename -> newname"
        file_part = change[3:].strip().split(" -> ")[0].strip('"')
        if file_part != allowed_rel:
            violations.append(f"{change.strip()} (unauthorized)")
    return violations


def _write_pid_file(agent: str, task_id: str, info: dict, pid: int = None):
    """Write a PID file for a running agent process."""
    try:
        PID_DIR.mkdir(parents=True, exist_ok=True)
        pid_file = PID_DIR / f"{agent}-{task_id}.json"
        pid_data = {
            "pid": pid or os.getpid(),
            "agent": agent,
            "started": datetime.now(timezone.utc).isoformat(),
            **info,
        }
        pid_file.write_text(json.dumps(pid_data, indent=2))
    except (IOError, OSError) as e:
        logger.error(f"Failed to write PID file: {e}")


def _is_task_locked(agent: str, task_id: str) -> bool:
    """Check if another process is already working on this task.

    Returns True if locked (another process is alive), False if free.
    Cleans up stale PID files automatically.
    Excludes the current process's own PID (prevents self-lock).
    Also detects stale locks: if PID file is older than 30 minutes and the
    process doesn't look like a python/gemini/claude process, treat as stale.
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

        # Process exists, but check if PID file is stale (>30 min old)
        started = data.get("started")
        if started:
            try:
                start_time = datetime.fromisoformat(started)
                age_minutes = (datetime.now(timezone.utc) - start_time).total_seconds() / 60
                if age_minutes > 30:
                    # PID exists but lock is old — verify process is actually ours
                    try:
                        result = subprocess.run(
                            ["ps", "-p", str(pid), "-o", "comm="],
                            capture_output=True, text=True, timeout=5
                        )
                        proc_name = result.stdout.strip().lower()
                        if not any(name in proc_name for name in ("python", "gemini", "claude", "node")):
                            logger.info(f"🧹 Stale PID lock: {pid_file.name} (PID {pid} is '{proc_name}', {age_minutes:.0f}m old)")
                            pid_file.unlink(missing_ok=True)
                            return False
                    except Exception:
                        # Can't verify process name — treat old lock as stale
                        logger.info(f"🧹 Stale PID lock: {pid_file.name} ({age_minutes:.0f}m old, can't verify process)")
                        pid_file.unlink(missing_ok=True)
                        return False
            except (ValueError, TypeError):
                pass  # Can't parse timestamp — fall through to "locked"

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
    try:
        pid_file = PID_DIR / f"{agent}-{task_id}.json"
        pid_file.unlink(missing_ok=True)
    except (IOError, OSError) as e:
        logger.error(f"Failed to remove PID file: {e}")


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
            print("")
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
        logger.info("🔧 Migrating database: adding 'status' column to 'messages' table")
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
    logger.info(f"📌 Stored {agent} session: {session_id[:8]}... for task {task_id}")

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
        from_model: Exact model ID (e.g., 'claude-opus-4-5-20251101', 'gemini-1.5-flash')
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

    logger.info(f"✅ Message sent to {to_llm.title()} (ID: {msg_id})")

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

    Runs in sync mode by default (15 min timeout). Use --async flag for fire-and-forget.

    Args:
        from_llm: Sender agent family (gemini, claude) - for routing
        from_model: Exact model ID of sender (e.g., 'claude-opus-4-5-20251101')
        to_model: Target model ID (e.g., 'claude-sonnet-4')
    """
    # Step 1: Send the message
    msg_id = send_message(content, task_id, msg_type, data, from_llm=from_llm, to_llm="claude", from_model=from_model, to_model=to_model)

    # Step 2: Invoke Claude to process it (mode auto-detected from message type)
    logger.info(f"\n🚀 Invoking Claude to process message #{msg_id}...")
    process_for_claude(msg_id, new_session)

    return msg_id


def send_to_gemini(content: str, task_id: str = None, msg_type: str = "query", data: str = None, from_model: str = None, to_model: str = None):
    """Send a message from Claude to Gemini."""
    return send_message(content, task_id, msg_type, data, from_llm="claude", to_llm="gemini", from_model=from_model, to_model=to_model)


def ask_gemini(content: str, task_id: str = None, msg_type: str = "query", data: str = None, model: str = "gemini-1.5-flash", from_model: str = None, async_mode: bool = False, stdout_only: bool = False, output_path: str = None):
    """Send message to Gemini AND optionally invoke Gemini to process it.

    Args:
        model: Gemini model to use (default: gemini-1.5-flash)
        from_model: Exact model ID of sender (e.g., 'claude-opus-4-5-20251101')
        async_mode: If True, just queue message without invoking Gemini CLI.
                   Auto-enabled for 'handoff' type messages (complex tasks).
        stdout_only: If True, don't route full response through broker. Output goes
                    to stdout only. Broker gets a short summary instead. Use for
                    orchestrated rebuilds where Claude captures stdout directly.
        output_path: If set, Gemini writes output to this file instead of stdout.
                    Enables -y mode with post-validation (only this file may be written).
    """
    # Auto-enable async for handoff type (complex tasks shouldn't expect immediate response)
    if msg_type == "handoff":
        async_mode = True
        logger.info("ℹ️  Async mode auto-enabled for handoff (complex task)")

    # Validation: Warn if handoff message is too long (handoff anti-pattern)
    # Only warn for handoff type - help/query messages can be long
    HANDOFF_WARNING_THRESHOLD = 500  # chars
    if msg_type == "handoff" and len(content) > HANDOFF_WARNING_THRESHOLD and task_id and task_id.startswith("gh-"):
        logger.warning(f"⚠️  WARNING: Handoff message is {len(content)} chars (>{HANDOFF_WARNING_THRESHOLD})")
        logger.warning(f"   For task handoffs, the GitHub issue should contain details.")
        logger.warning(f"   Consider sending a SHORT message with issue reference only:")
        logger.warning(f"   'Issue #{task_id.replace('gh-', '')} is assigned to you. Read it for details.'")
        logger.warning("")

    # Step 1: Send the message (model param becomes to_model)
    # In output_path mode, skip broker entirely — batch script handles everything
    if output_path:
        msg_id = send_to_gemini(content, task_id, msg_type, data, from_model=from_model, to_model=model)
        acknowledge(msg_id)
        logger.info(f"   Pre-acknowledged (file output mode — no broker traffic)")
    else:
        msg_id = send_to_gemini(content, task_id, msg_type, data, from_model=from_model, to_model=model)

        # Step 1.5: Pre-acknowledge for orchestration mode.
        # Prevents race condition: without this, the message sits unread in broker
        # while Gemini processes it. If a standalone Gemini session checks inbox
        # during that window, it picks up the message with no restrictions.
        if stdout_only:
            acknowledge(msg_id)
            logger.info(f"   Pre-acknowledged (orchestration mode — won't appear in Gemini inbox)")

    # Step 2: Invoke Gemini to process it (unless async mode)
    if async_mode:
        logger.info(f"\n📥 Message #{msg_id} queued for Gemini (async mode - no immediate invocation)")
        logger.info(f"   Gemini will see this in his inbox when he starts a session.")
        logger.info(f"   To trigger manually: .venv/bin/python scripts/ai_agent_bridge.py process {msg_id}")
    else:
        logger.info(f"\n🚀 Invoking Gemini to process message #{msg_id}...")
        process_and_respond(msg_id, model, stdout_only=stdout_only, output_path=output_path)

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
        logger.info(f"✓ Message {message_ids[0]} acknowledged")
    else:
        logger.info(f"✓ {len(message_ids)} messages acknowledged: {', '.join(map(str, message_ids))}")


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
        logger.info(f"📭 No unread messages to acknowledge for {for_llm}")
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

    logger.info(f"✓ Acknowledged {len(msg_ids)} messages for {for_llm}: {', '.join(map(str, msg_ids))}")

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
        print("")

def _estimate_tokens(text: str) -> int:
    """Rough estimation of tokens based on character count."""
    if not text:
        return 0
    # Average ~3.5 chars per token for mixed English/Ukrainian
    return max(1, len(text) // 3)

def _log_usage(model: str, input_text: str, output_text: str, task_id: str = None):
    """Log estimated token usage and cost."""
    in_tokens = _estimate_tokens(input_text)
    out_tokens = _estimate_tokens(output_text)

    costs = MODEL_COSTS.get(model, MODEL_COSTS["default"])
    cost = (in_tokens * costs["input"] + out_tokens * costs["output"]) / 1_000_000

    logger.info(f"📊 Usage [{model}] {'(Task: ' + task_id + ')' if task_id else ''}:")
    logger.info(f"   Tokens: {in_tokens} in, {out_tokens} out (total: {in_tokens + out_tokens})")
    logger.info(f"   Est. Cost: ${cost:.4f}")

def process_and_respond(message_id: int, model: str = "gemini-1.5-flash", fire_and_forget: bool = False, no_timeout: bool = False, stdout_only: bool = False, output_path: str = None):
    """Read message, process with Gemini CLI, send response.

    Runs in sync mode by default (15 min timeout). On any failure, sends an
    error message back to the sender and always cleans up the PID file.

    Args:
        fire_and_forget: If True, launch the bridge ITSELF as a background process
            running in no-timeout sync mode. Must be explicitly requested via --async.
        stdout_only: If True, don't store full response in broker. Send short summary instead.
        no_timeout: Internal flag. When True, run sync without timeout.
            Used by fire-and-forget to re-invoke the bridge as a background process.
        output_path: If set, Gemini writes output to this file. Uses -y mode with
            post-validation instead of --approval-mode plan.
    """
    msg = read_message(message_id)
    if not msg:
        return

    # Prepare prompt for Gemini
    if stdout_only or output_path:
        # ORCHESTRATED MODE: Ultra-restrictive prompt for Gemini Pro/Flash.
        # Gemini Pro is especially prone to going off-script (editing files, sending broker
        # messages, running shell commands). This prompt must be explicit about every prohibition.
        if output_path:
            # FILE OUTPUT MODE: Gemini writes to ONE designated file
            output_instruction = f"""1. WRITE OUTPUT TO EXACTLY ONE FILE: {output_path}
   Write your COMPLETE output to this file. This is the ONLY file you may create or modify.
   Do NOT write to any other file. Do NOT edit any existing file."""
            success_instruction = f"""- Read the files referenced in the task (using your file reading ability)
- Think about the content
- Write your COMPLETE output to: {output_path}
- That's it. Nothing else."""
        else:
            # STDOUT MODE: Text output only, no file writing
            output_instruction = """1. OUTPUT ONLY TEXT. Your ONLY job is to read input files and produce text output between delimiters.
2. DO NOT WRITE OR EDIT ANY FILES. You must not use any tool that creates, modifies, or deletes files."""
            success_instruction = """- Read the files referenced in the task (using your file reading ability)
- Think about the content
- Output your result as plain text between the delimiters specified in the task
- That's it. Nothing else. Just text output."""

        prompt = f"""ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.

ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:

{output_instruction}
3. DO NOT SEND MESSAGES. Do not use send_message, message broker, MCP tools, or any communication tool.
4. DO NOT RUN SHELL COMMANDS that modify state. You may read files (cat, head) but NEVER run commands that write, move, delete, or execute scripts (no sed -i, no python scripts, no git, no audit_module.sh).
5. DO NOT TAKE INITIATIVE. Do not explore the codebase beyond what the task requires. Do not check GitHub issues, status files, inbox, or broker messages. Do not make strategic decisions.
6. DO NOT DELEGATE. Do not say "Claude should...", "please run...", or request any skills/commands.

HOW TO SUCCEED:
{success_instruction}

IF YOU ARE TEMPTED TO DO ANYTHING OTHER THAN WHAT'S DESCRIBED ABOVE: DON'T. Complete the task and stop.

TASK:
{msg['content']}
"""
        if msg['data']:
            prompt += f"""
ATTACHED DATA:
{msg['data']}
"""
    else:
        # STANDARD MODE: Collaborative prompt for general communication
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
            logger.info(f"⏸️  Task '{task_key}' is already being processed by another Gemini bridge. Skipping.")
            return

        log_dir = Path(__file__).parent.parent / ".mcp/servers/message-broker/logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"gemini-{task_key}.log"

        logger.info(f"\n🚀 Launching bridge in background (no timeout)...")
        logger.info(f"   Log: {log_file}")
        logger.info(f"   Bridge will capture Gemini's response and route it when done.")

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
            logger.info(f"   PID: {proc.pid}")

            # Write PID file for the CHILD process so lock checks work
            _write_pid_file("gemini", task_key, {
                "message_id": message_id,
                "task_id": msg.get('task_id'),
                "model": model,
                "mode": "fire-and-forget",
            }, pid=proc.pid)

        except FileNotFoundError:
            logger.error("❌ Python or bridge script not found")
    else:
        # SYNC: Run Gemini with STREAMING output (visible in log in real-time)
        task_key = msg.get('task_id') or str(message_id)
        timeout_val = None if no_timeout else 900
        mode_label = "no-timeout" if no_timeout else "sync, 15 min timeout"

        # LOCK CHECK: Don't process if another bridge is already working on this task
        if _is_task_locked("gemini", task_key):
            logger.info(f"⏸️  Task '{task_key}' is already being processed by another Gemini bridge. Skipping.")
            return

        logger.info(f"\n🤖 Processing with Gemini ({model}) [{mode_label}]...")
        sys.stdout.flush()

        # Write PID file for status tracking and locking
        _write_pid_file("gemini", task_key, {
            "message_id": message_id,
            "task_id": msg.get('task_id'),
            "model": model,
            "mode": mode_label,
        })
        atexit.register(_remove_pid_file, "gemini", task_key)

        max_retries = 3
        base_delay = 60  # seconds
        max_delay = 120  # seconds
        _response_sent = False

        try:
            for attempt in range(max_retries):
                try:
                    # Stream stdout line-by-line so the log file updates in real-time
                    gemini_cmd = [GEMINI_CLI, "-m", model]
                    if stdout_only and not output_path:
                        gemini_cmd += ["--approval-mode", "plan"]
                    else:
                        gemini_cmd += ["-y"]
                    gemini_cmd += ["-p", prompt]

                    # Snapshot for post-validation when output_path is set
                    pre_snapshot = None
                    if output_path:
                        pre_snapshot = _git_status_snapshot()

                    proc = subprocess.Popen(
                        gemini_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=str(Path(__file__).parent.parent),
                        env=_PARENT_ENV
                    )

                    # Read stdout in real-time, collect for response routing
                    output_lines = []
                    start_time = time.time()
                    while True:
                        line = proc.stdout.readline()
                        if not line:
                            if proc.poll() is not None:
                                break
                            time.sleep(0.1)
                            # Check for timeout if not no_timeout
                            if not no_timeout and (time.time() - start_time) > (timeout_val or 900):
                                proc.terminate()
                                raise subprocess.TimeoutExpired(gemini_cmd, timeout_val or 900)
                            continue

                        print(line, end='')  # Real-time to log file
                        sys.stdout.flush()
                        output_lines.append(line)
                        # Reset timeout clock on activity
                        start_time = time.time()

                    # Wait for process to finish, get stderr
                    stdout_remaining, stderr = proc.communicate(timeout=30)
                    if stdout_remaining:
                        output_lines.append(stdout_remaining)

                    if proc.returncode != 0:
                        # Detect quota/rate limit errors
                        is_rate_limited = any(x in stderr.lower() for x in ["exhausted your capacity", "429", "quota", "too many requests"])
                        is_cooldown = "cooldown" in stderr.lower() or "temporarily overloaded" in stderr.lower()

                        if is_rate_limited or is_cooldown:
                            delay = min(base_delay * (2 ** attempt), max_delay)
                            if attempt < max_retries - 1:
                                reason = "Rate limited" if is_rate_limited else "Cooldown"
                                logger.warning(f"\n⏳ {reason} (attempt {attempt + 1}/{max_retries}). Waiting {delay}s...")
                                sys.stdout.flush()
                                time.sleep(delay)
                                continue
                            else:
                                logger.error(f"\n❌ {reason} after {max_retries} attempts. Giving up.")
                                return
                        logger.error(f"\n❌ Gemini CLI error (exit {proc.returncode}): {stderr[:1000]}")
                        sys.stdout.flush()
                        # Non-zero exit but has output? Gemini tool calls may cause exit 1.
                        # If we got substantial output, treat as success.
                        if not output_lines or len(''.join(output_lines).strip()) < 50:
                            return

                    response = ''.join(output_lines).strip()

                    # Log usage
                    _log_usage(model, prompt, response, msg.get('task_id'))

                    # Post-validation: check Gemini only wrote to the allowed file
                    if output_path and pre_snapshot is not None:
                        violations = _validate_file_writes(pre_snapshot, output_path)
                        if violations:
                            logger.warning(f"\n⚠️  VIOLATION: Gemini wrote to unauthorized files:")
                            for v in violations:
                                logger.warning(f"   - {v}")
                            sys.stdout.flush()

                    logger.info(f"\n\n{'─' * 40}")
                    if output_path:
                        output_exists = Path(output_path).exists()
                        output_size = Path(output_path).stat().st_size if output_exists else 0
                        logger.info(f"✅ Gemini finished → {output_path} ({output_size} bytes)")
                    else:
                        logger.info(f"✅ Gemini finished ({len(response)} chars)")
                    sys.stdout.flush()

                    if output_path:
                        # File output mode: NO broker message. Batch script reads the file directly.
                        logger.info(f"   (no broker message — file output mode)")
                    elif stdout_only:
                        # Stdout-only mode: broker gets SHORT summary only
                        summary = f"[stdout-only] Gemini finished. {len(response)} chars output to stdout."
                        send_message(
                            content=summary,
                            task_id=msg['task_id'],
                            msg_type="response",
                            from_llm="gemini",
                            to_llm="claude",
                            from_model=model,
                            to_model=None
                        )
                    else:
                        # Standard mode: full response through broker
                        send_message(
                            content=response,
                            task_id=msg['task_id'],
                            msg_type="response",
                            from_llm="gemini",
                            to_llm="claude",
                            from_model=model,
                            to_model=None
                        )
                    _response_sent = True

                    # Acknowledge original message
                    acknowledge(message_id)
                    break  # Success — exit retry loop

                except subprocess.TimeoutExpired:
                    proc.kill()
                    logger.error(f"\n❌ Gemini CLI timed out ({timeout_val}s sync limit)")
                    return
                except FileNotFoundError:
                    logger.error("❌ gemini CLI not found. Is it installed?")
                    return
        finally:
            # Always clean up PID file, and send error if no response was routed
            if not _response_sent:
                try:
                    send_message(
                        content=f"[Bridge Error] Gemini process failed for message #{message_id}. Check logs.",
                        task_id=msg['task_id'],
                        msg_type="error",
                        from_llm="gemini",
                        to_llm="claude",
                        from_model="gemini-bridge-error"
                    )
                    acknowledge(message_id)
                except Exception:
                    pass  # Best-effort error reporting
            _remove_pid_file("gemini", task_key)


def process_for_claude(message_id: int, new_session: bool = False, fire_and_forget: bool = False, no_timeout: bool = False):
    """Read message addressed to Claude, invoke Claude CLI headlessly, send response back to sender.

    Runs in sync mode by default (15 min timeout). On any failure, sends an
    error message back to the sender and always cleans up the PID file.

    Args:
        message_id: The message ID to process
        new_session: If True, force a new session even if one exists
        fire_and_forget: If True, re-launch bridge in background with --no-timeout.
            Must be explicitly requested via --async flag.
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
        logger.error(f"❌ Message {message_id} not found or not addressed to Claude")
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

    logger.info(f"📨 Message #{msg['id']}")
    logger.info(f"   From: {msg['from']} → To: {msg['to']}")
    logger.info(f"   Type: {msg['type']}")
    logger.info(f"   Task: {msg['task_id'] or 'N/A'}")
    logger.info(f"   Mode: {'🚀 async (bridge bg)' if fire_and_forget else '⏳ sync' + (' (no timeout)' if no_timeout else '')}")
    logger.info(f"   Session: {claude_session_id[:8] + '...' if claude_session_id else 'NEW'}")

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
        logger.info(f"   Resuming session: {claude_session_id[:8]}...")
    elif msg['task_id']:
        new_id = str(uuid.uuid4())
        cmd.extend(["--session-id", new_id])
        set_session(msg['task_id'], "claude", new_id)
        logger.info(f"   New session: {new_id[:8]}...")

    if fire_and_forget:
        # ASYNC: Launch the BRIDGE ITSELF as a background process in no-timeout mode.
        task_key = msg['task_id'] or str(message_id)

        # LOCK CHECK: Don't launch if another process is already working on this task
        if _is_task_locked("claude", task_key):
            logger.info(f"⏸️  Task '{task_key}' is already being processed by another Claude bridge. Skipping.")
            return

        log_dir = Path(__file__).parent.parent / ".mcp/servers/message-broker/logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"claude-{task_key}.log"

        logger.info(f"\n🚀 Launching bridge in background (no timeout)...")
        logger.info(f"   Log: {log_file}")
        logger.info(f"   Bridge will capture Claude's response and route it when done.")

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
            logger.info(f"   PID: {proc.pid}")

            # Write PID file for the CHILD process so lock checks work
            _write_pid_file("claude", task_key, {
                "message_id": message_id,
                "task_id": msg.get('task_id'),
                "mode": "fire-and-forget",
            }, pid=proc.pid)

        except FileNotFoundError:
            logger.error("❌ Python or bridge script not found")
    else:
        # SYNC: Run Claude with STREAMING output (visible in log in real-time)
        task_key = msg.get('task_id') or str(message_id)
        timeout_val = None if no_timeout else 900
        mode_label = "no-timeout" if no_timeout else "sync, 15 min timeout"

        # LOCK CHECK: Don't process if another bridge is already working on this task
        if _is_task_locked("claude", task_key):
            logger.info(f"⏸️  Task '{task_key}' is already being processed by another Claude bridge. Skipping.")
            return

        logger.info(f"\n🤖 Processing with Claude CLI (headless) [{mode_label}]...")
        sys.stdout.flush()

        # Write PID file for status tracking and locking
        _write_pid_file("claude", task_key, {
            "message_id": message_id,
            "task_id": msg.get('task_id'),
            "mode": mode_label,
        })
        atexit.register(_remove_pid_file, "claude", task_key)

        _response_sent = False
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
            start_time = time.time()
            while True:
                line = proc.stdout.readline()
                if not line:
                    if proc.poll() is not None:
                        break
                    time.sleep(0.1)
                    if not no_timeout and (time.time() - start_time) > (timeout_val or 900):
                        proc.terminate()
                        raise subprocess.TimeoutExpired(cmd, timeout_val or 900)
                    continue

                print(line, end='')
                sys.stdout.flush()
                output_lines.append(line)
                start_time = time.time()

            stdout_remaining, stderr = proc.communicate(timeout=30)
            if stdout_remaining:
                output_lines.append(stdout_remaining)

            if proc.returncode != 0:
                error_msg = stderr.strip() or "Unknown error"
                logger.error(f"\n❌ Claude CLI error: {error_msg[:500]}")
                sys.stdout.flush()

                send_message(
                    content=f"[Bridge Error] Claude CLI failed:\n{error_msg[:500]}",
                    task_id=msg['task_id'],
                    msg_type="error",
                    from_llm="claude",
                    to_llm=msg['from'],
                    from_model="claude-bridge-error"
                )
                _response_sent = True
                acknowledge(message_id)
                return

            response = ''.join(output_lines).strip()

            logger.info(f"\n\n{'─' * 40}")
            logger.info(f"✅ Claude finished ({len(response)} chars)")
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
            _response_sent = True

            acknowledge(message_id)

        except subprocess.TimeoutExpired:
            proc.kill()
            timeout_mins = timeout_val // 60 if timeout_val else "?"
            logger.error(f"\n❌ Claude CLI timed out ({timeout_mins} min sync limit)")
            send_message(
                content=f"[Bridge Error] Claude CLI timed out after {timeout_mins} minutes. Consider using --async flag for long tasks.",
                task_id=msg['task_id'],
                msg_type="error",
                from_llm="claude",
                to_llm=msg['from'],
                from_model="claude-bridge-timeout"
            )
            _response_sent = True
            acknowledge(message_id)
        except FileNotFoundError:
            logger.error("❌ claude CLI not found. Is it installed?")
            send_message(
                content="[Bridge Error] Claude CLI not found on system",
                task_id=msg['task_id'],
                msg_type="error",
                from_llm="claude",
                to_llm=msg['from'],
                from_model="claude-bridge-not-found"
            )
            _response_sent = True
        finally:
            # Always clean up PID file, and send error if no response was routed
            if not _response_sent:
                try:
                    send_message(
                        content=f"[Bridge Error] Claude process failed unexpectedly for message #{message_id}. Check logs.",
                        task_id=msg['task_id'],
                        msg_type="error",
                        from_llm="claude",
                        to_llm=msg['from'],
                        from_model="claude-bridge-error"
                    )
                    acknowledge(message_id)
                except Exception:
                    pass  # Best-effort error reporting
            _remove_pid_file("claude", task_key)


def interactive_mode():
    """Interactive mode for testing."""
    print("🔄 AI Agent Bridge Interactive Mode")
    print("Commands: inbox [agent], read <id>, send <text> --to <agent>, ack <id>, conv <task_id>, process <id>, quit")
    print("")

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


def process_all_gemini(model: str = "gemini-1.5-flash"):
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
        logger.info("📭 No unread messages for Gemini to process")
        return

    logger.info(f"📬 Processing {len(rows)} unread message(s) for Gemini...\n")

    success = 0
    failed = 0

    for row in rows:
        msg_id, task_id, from_llm, msg_type, preview = row
        preview = preview.replace('\n', ' ')[:40]
        logger.info(f"━━━ Processing [{msg_id}] from {from_llm}: {preview}...")

        try:
            process_and_respond(msg_id, model)
            success += 1
            logger.info(f"    ✅ Done\n")
        except Exception as e:
            failed += 1
            logger.info(f"    ❌ Failed: {e}\n")

    logger.info(f"\n{'═' * 50}")
    logger.info(f"📊 Results: {success} succeeded, {failed} failed out of {len(rows)} total")


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
        logger.info("📭 No unread messages for Claude to process")
        return

    logger.info(f"📬 Processing {len(rows)} unread message(s) for Claude (headless)...\n")

    success = 0
    failed = 0

    for row in rows:
        msg_id, task_id, from_llm, msg_type, preview = row
        preview = preview.replace('\n', ' ')[:40]
        logger.info(f"━━━ Processing [{msg_id}] from {from_llm}: {preview}...")

        try:
            process_for_claude(msg_id, new_session)
            success += 1
            logger.info(f"    ✅ Done\n")
        except Exception as e:
            failed += 1
            logger.info(f"    ❌ Failed: {e}\n")

    logger.info(f"\n{'═' * 50}")
    logger.info(f"📊 Results: {success} succeeded, {failed} failed out of {len(rows)} total")


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
    proc_parser.add_argument("--model", default="gemini-1.5-flash", help="Gemini model")
    proc_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true",
                             help="Run sync without timeout (used internally by fire-and-forget)")

    # process-claude (invoke Claude headlessly)
    proc_claude_parser = subparsers.add_parser("process-claude", help="Process message with Claude CLI (headless)")
    proc_claude_parser.add_argument("message_id", type=int, help="Message ID for Claude to process")
    proc_claude_parser.add_argument("--new-session", dest="new_session", action="store_true",
                                    help="Force new session even if one exists for this task")
    proc_claude_parser.add_argument("--async", dest="fire_and_forget", action="store_true",
                                    help="Launch Claude in background (no timeout). Must be explicitly requested.")
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
    ask_gemini_parser.add_argument("--model", default="gemini-1.5-flash", help="Gemini model to use (also used as to_model)")
    ask_gemini_parser.add_argument("--from-model", dest="from_model",
                                   help="Exact sender model ID (e.g., claude-opus-4-5-20251101)")
    ask_gemini_parser.add_argument("--async", dest="async_mode", action="store_true",
                                   help="Queue only, don't invoke Gemini CLI (for complex tasks). Auto-enabled for --type handoff")
    ask_gemini_parser.add_argument("--stdout-only", dest="stdout_only", action="store_true",
                                   help="Don't route full response through broker. Output goes to stdout only. Broker gets short summary.")
    ask_gemini_parser.add_argument("--output-path", dest="output_path",
                                   help="Gemini writes output to this file (uses -y mode with post-validation).")

    # process-all (batch process all unread for Gemini)
    proc_all_parser = subparsers.add_parser("process-all", help="Process ALL unread messages with Gemini")
    proc_all_parser.add_argument("--model", default="gemini-1.5-flash", help="Gemini model")

    # process-claude-all (batch process all unread for Claude)
    proc_claude_all_parser = subparsers.add_parser("process-claude-all", help="Process ALL unread messages with Claude")
    proc_claude_all_parser.add_argument("--new-session", dest="new_session", action="store_true",
                                        help="Force new sessions for each message")

    # Logging options
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set log level")
    parser.add_argument("--json-log", action="store_true", help="Use JSON structured logging")

    # status
    subparsers.add_parser("status", help="Show running bridge processes")

    # interactive
    subparsers.add_parser("interactive", help="Interactive mode")

    args = parser.parse_args()

    # Initialize logging
    setup_logging(level=getattr(logging, args.log_level), json_format=args.json_log)

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
        ask_gemini(args.content, args.task_id, args.type, data, args.model, getattr(args, 'from_model', None), getattr(args, 'async_mode', False), getattr(args, 'stdout_only', False), getattr(args, 'output_path', None))
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