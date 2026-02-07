#!/usr/bin/env python3
"""
Agent Watcher Daemon - Monitors message broker and triggers agents automatically.

This daemon watches the messages.db file for new unread messages and triggers
the appropriate agent (Claude or Gemini) to process them.

Features:
- Watches SQLite database for new messages via polling
- Triggers appropriate agent based on message recipient
- Loop prevention: max turns per task, cooldown periods
- User session awareness: backs off when user is active
- Logging: writes to watcher.log for visibility

Usage:
    # Start daemon (foreground)
    python scripts/agent_watcher.py

    # Start daemon (background)
    python scripts/agent_watcher.py --daemon

    # Check status
    python scripts/agent_watcher.py --status

    # Stop daemon
    python scripts/agent_watcher.py --stop
"""

import argparse
import json
import logging
import os
import signal
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

# Configuration
DB_PATH = Path(__file__).parent.parent / ".mcp/servers/message-broker/messages.db"
PID_FILE = Path(__file__).parent.parent / ".mcp/servers/message-broker/watcher.pid"
LOG_FILE = Path(__file__).parent.parent / ".mcp/servers/message-broker/watcher.log"
BRIDGE_SCRIPT = Path(__file__).parent / "ai_agent_bridge.py"

# Timing configuration
POLL_INTERVAL_SECONDS = 5  # How often to check for new messages
IDLE_POLL_INTERVAL_SECONDS = 30  # Slower polling when no activity
COOLDOWN_AFTER_TRIGGER_SECONDS = 10  # Wait after triggering an agent
USER_ACTIVITY_WINDOW_SECONDS = 60  # Consider user active if recent messages from user

# Loop prevention
MAX_TURNS_PER_TASK = 8  # Max agent responses per task before requiring human intervention
MAX_CONSECUTIVE_ERRORS = 3  # Stop processing after consecutive errors

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Agent config (lazy-loaded singleton)
_AGENTS_CONFIG = None


def load_agent_config() -> dict:
    """Load agent registry from scripts/config/agents.yaml (cached)."""
    global _AGENTS_CONFIG
    if _AGENTS_CONFIG is None:
        config_path = Path(__file__).parent / "config" / "agents.yaml"
        if config_path.exists():
            with open(config_path) as f:
                _AGENTS_CONFIG = yaml.safe_load(f).get("agents", {})
        else:
            # Fallback hardcoded defaults
            _AGENTS_CONFIG = {
                "claude": {"bridge_command": "process-claude", "process_pattern": "claude"},
                "gemini": {"bridge_command": "process", "process_pattern": "gemini-cli"},
            }
        logger.info(f"Loaded agent config: {list(_AGENTS_CONFIG.keys())}")
    return _AGENTS_CONFIG


def notify_human(from_agent: str, to_agent: str, message_id: int, task_id: str):
    """Send macOS notification to alert human about inter-agent message."""
    try:
        title = f"{from_agent.title()} → {to_agent.title()}"
        subtitle = f"Task: {task_id}" if task_id else "New message"
        body = f"Message #{message_id} — processing headlessly"
        notification = (
            f'display notification "{body}" '
            f'with title "{title}" '
            f'subtitle "{subtitle}" '
            f'sound name "Submarine"'
        )
        subprocess.run(["osascript", "-e", notification], check=False, capture_output=True)
    except Exception:
        pass  # Notification is best-effort


def _save_stuck_report(task_id: str, turn_count: int, last_msg: dict):
    """Save a stuck report when a task hits the turn limit."""
    try:
        # Try to extract track and slug from task_id (e.g., "c1-bio-knyahynia-olha-rebuild")
        report_dir = None
        for track in ("c1-bio", "b2-hist", "c1-hist", "lit", "oes", "ruth"):
            if track in task_id:
                report_dir = Path(__file__).parent.parent / f"curriculum/l2-uk-en/{track}/stuck"
                report_dir.mkdir(parents=True, exist_ok=True)
                break

        if not report_dir:
            report_dir = Path(__file__).parent.parent / "curriculum/l2-uk-en/stuck"
            report_dir.mkdir(parents=True, exist_ok=True)

        slug = task_id.replace("rebuild-", "").replace("review-", "").replace("-v4", "")
        report_path = report_dir / f"{slug}.md"

        # Get last message content for context
        last_content = ""
        conn = get_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT content FROM messages WHERE task_id = ? ORDER BY id DESC LIMIT 1",
                (task_id,),
            )
            row = cursor.fetchone()
            if row:
                last_content = row[0][:500]  # Truncate to 500 chars
            conn.close()

        now = datetime.now(timezone.utc).isoformat()
        report = f"""# Stuck: {task_id}

**Date:** {now}
**Turns used:** {turn_count}/{MAX_TURNS_PER_TASK}
**Last message from:** {last_msg.get('from', 'unknown')} → {last_msg.get('to', 'unknown')}
**Message type:** {last_msg.get('type', 'unknown')}

## Last message (truncated)

{last_content}

## Resolution

- [ ] Human reviewed
- [ ] Fixed and re-queued / Skipped / Restarted with fresh session
"""
        report_path.write_text(report)
        logger.info(f"Saved stuck report: {report_path}")

        # Send desktop notification for stuck task
        _send_notification(
            "unknown", "human", last_msg.get("id", 0), task_id,
        )
    except Exception as e:
        logger.error(f"Failed to save stuck report for {task_id}: {e}")


def get_db():
    """Get database connection."""
    if not DB_PATH.exists():
        return None
    return sqlite3.connect(DB_PATH)


def get_unread_messages(for_agent: str = None):
    """Get unread messages, optionally filtered by recipient."""
    conn = get_db()
    if not conn:
        return []

    cursor = conn.cursor()

    if for_agent:
        cursor.execute("""
            SELECT id, task_id, from_llm, to_llm, message_type, timestamp
            FROM messages
            WHERE to_llm = ? AND acknowledged = 0
            ORDER BY id ASC
        """, (for_agent,))
    else:
        cursor.execute("""
            SELECT id, task_id, from_llm, to_llm, message_type, timestamp
            FROM messages
            WHERE acknowledged = 0
            ORDER BY id ASC
        """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "task_id": row[1],
            "from": row[2],
            "to": row[3],
            "type": row[4],
            "timestamp": row[5]
        }
        for row in rows
    ]


def acknowledge_message(message_id: int):
    """Mark a message as acknowledged in the database."""
    conn = get_db()
    if not conn:
        return
    try:
        conn.execute("UPDATE messages SET acknowledged = 1 WHERE id = ?", (message_id,))
        conn.commit()
        logger.debug(f"Acknowledged message #{message_id}")
    except Exception as e:
        logger.error(f"Failed to acknowledge message #{message_id}: {e}")
    finally:
        conn.close()


def count_task_turns(task_id: str) -> int:
    """Count how many messages have been exchanged in a task."""
    if not task_id:
        return 0

    conn = get_db()
    if not conn:
        return 0

    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM messages WHERE task_id = ?
    """, (task_id,))
    count = cursor.fetchone()[0]
    conn.close()

    return count


def is_any_agent_active() -> bool:
    """Check if any agent has an active interactive session."""
    agents = load_agent_config()
    for name, config in agents.items():
        pattern = config.get("process_pattern")
        if pattern:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", pattern],
                    capture_output=True, text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    return True
            except Exception:
                pass
    return False


def trigger_agent(agent: str, message_id: int, task_id: str = None, from_agent: str = None) -> bool:
    """Trigger an agent to process a message.

    Returns True if successful, False otherwise.
    """
    agents = load_agent_config()
    if agent not in agents:
        logger.error(f"Unknown agent: {agent}. Registered: {list(agents.keys())}")
        return False

    logger.info(f"Triggering {agent} to process message #{message_id} (task: {task_id or 'N/A'})")

    # Notify human before processing (so they know even if it takes minutes)
    notify_human(from_agent or "unknown", agent, message_id, task_id)

    try:
        bridge_cmd = agents[agent]["bridge_command"]
        cmd = [
            sys.executable,
            str(BRIDGE_SCRIPT),
            bridge_cmd,
            str(message_id)
        ]

        # Run in project directory with timeout
        # Bridge auto-detects sync/async from message type:
        #   request/handoff → async (Popen, returns immediately)
        #   query/response → sync (5 min bridge timeout)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=360,  # 6 min (safety net for bridge's 5 min sync timeout)
            cwd=str(Path(__file__).parent.parent)
        )

        if result.returncode == 0:
            logger.info(f"Successfully processed message #{message_id}")
            if result.stdout:
                # Log first 500 chars of output
                logger.debug(result.stdout[:500])
            # Mark message as acknowledged so we don't re-process it
            acknowledge_message(message_id)
            return True
        else:
            logger.error(f"Agent {agent} failed: {result.stderr[:500] if result.stderr else 'No error output'}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"Agent {agent} timed out processing message #{message_id}")
        return False
    except Exception as e:
        logger.error(f"Error triggering {agent}: {e}")
        return False


def run_watcher():
    """Main watcher loop."""
    logger.info("=" * 60)
    logger.info("Agent Watcher starting...")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Poll interval: {POLL_INTERVAL_SECONDS}s (idle: {IDLE_POLL_INTERVAL_SECONDS}s)")
    logger.info(f"Max turns per task: {MAX_TURNS_PER_TASK}")
    logger.info("=" * 60)

    consecutive_errors = 0
    last_activity = datetime.now(timezone.utc)

    # Track blocked tasks (hit turn limit)
    blocked_tasks = set()

    while True:
        try:
            # Check for unread messages
            messages = get_unread_messages()

            if not messages:
                # No messages - use idle polling
                time.sleep(IDLE_POLL_INTERVAL_SECONDS)
                continue

            # Check if user is active
            if is_any_agent_active():
                logger.debug("User session detected - backing off")
                time.sleep(POLL_INTERVAL_SECONDS * 2)
                continue

            # Process first eligible message
            processed = False
            for msg in messages:
                # Skip if task is blocked
                if msg['task_id'] and msg['task_id'] in blocked_tasks:
                    logger.debug(f"Skipping blocked task: {msg['task_id']}")
                    continue

                # Loop prevention: check turn count
                if msg['task_id']:
                    turn_count = count_task_turns(msg['task_id'])
                    if turn_count >= MAX_TURNS_PER_TASK:
                        logger.warning(f"Task {msg['task_id']} hit {MAX_TURNS_PER_TASK} turns - blocking until human intervention")
                        blocked_tasks.add(msg['task_id'])
                        _save_stuck_report(msg['task_id'], turn_count, msg)
                        continue

                # Skip error messages (don't auto-process)
                if msg['type'] == 'error':
                    logger.debug(f"Skipping error message #{msg['id']}")
                    continue

                # Trigger appropriate agent
                success = trigger_agent(msg['to'], msg['id'], msg['task_id'], from_agent=msg['from'])

                if success:
                    consecutive_errors = 0
                    last_activity = datetime.now(timezone.utc)
                    processed = True
                    # Cooldown after successful trigger
                    time.sleep(COOLDOWN_AFTER_TRIGGER_SECONDS)
                else:
                    consecutive_errors += 1
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        logger.error(f"Too many consecutive errors ({consecutive_errors}) - pausing for 60s")
                        time.sleep(60)
                        consecutive_errors = 0

                break  # Only process one message per loop iteration

            if not processed:
                # All messages were skipped (blocked or errors)
                time.sleep(POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logger.info("Shutdown requested")
            break
        except Exception as e:
            logger.error(f"Watcher error: {e}")
            consecutive_errors += 1
            time.sleep(POLL_INTERVAL_SECONDS)


def write_pid():
    """Write PID file for daemon mode."""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def read_pid() -> int:
    """Read PID from file."""
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except:
            pass
    return None


def is_running() -> bool:
    """Check if watcher is running."""
    pid = read_pid()
    if pid:
        try:
            os.kill(pid, 0)  # Just check if process exists
            return True
        except OSError:
            pass
    return False


def stop_daemon():
    """Stop running daemon."""
    pid = read_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Sent SIGTERM to watcher (PID {pid})")
            # Wait for cleanup
            time.sleep(1)
            if PID_FILE.exists():
                PID_FILE.unlink()
            return True
        except OSError as e:
            print(f"Error stopping daemon: {e}")
    else:
        print("No watcher running (no PID file found)")
    return False


def show_status():
    """Show watcher status."""
    print(f"Database: {DB_PATH}")
    print(f"PID file: {PID_FILE}")
    print(f"Log file: {LOG_FILE}")

    agents = load_agent_config()
    print(f"Registered agents: {', '.join(agents.keys())}")
    print()

    if is_running():
        pid = read_pid()
        print(f"Status: RUNNING (PID {pid})")
    else:
        print("Status: STOPPED")

    # Show pending messages
    messages = get_unread_messages()
    if messages:
        print(f"\nPending messages: {len(messages)}")
        for msg in messages[:5]:
            print(f"  [{msg['id']}] {msg['from']} → {msg['to']} ({msg['type']})")
        if len(messages) > 5:
            print(f"  ... and {len(messages) - 5} more")
    else:
        print("\nNo pending messages")

    # Show recent log entries
    if LOG_FILE.exists():
        print(f"\nRecent log entries:")
        try:
            with open(LOG_FILE) as f:
                lines = f.readlines()[-10:]
                for line in lines:
                    print(f"  {line.rstrip()}")
        except:
            pass


def main():
    parser = argparse.ArgumentParser(description="Agent Watcher Daemon")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run in daemon mode (background)")
    parser.add_argument("--foreground", "-f", action="store_true", help="Run in foreground (for launchd)")
    parser.add_argument("--status", "-s", action="store_true", help="Show status")
    parser.add_argument("--stop", action="store_true", help="Stop running daemon")
    parser.add_argument("--once", action="store_true", help="Process one message and exit")

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.stop:
        stop_daemon()
        return

    if not args.foreground and is_running():
        print("Watcher is already running. Use --stop to stop it first.")
        return

    if args.daemon:
        # Fork to background
        pid = os.fork()
        if pid > 0:
            print(f"Watcher started in background (PID {pid})")
            return
        # Child process continues
        os.setsid()

    # Write PID file
    write_pid()

    # Handle cleanup on exit
    def cleanup(signum, frame):
        if PID_FILE.exists():
            PID_FILE.unlink()
        logger.info("Watcher stopped")
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    if args.once:
        # Process one message and exit
        messages = get_unread_messages()
        if messages:
            msg = messages[0]
            trigger_agent(msg['to'], msg['id'], msg['task_id'], from_agent=msg['from'])
        else:
            print("No pending messages")
        cleanup(None, None)
    else:
        run_watcher()


if __name__ == "__main__":
    main()
