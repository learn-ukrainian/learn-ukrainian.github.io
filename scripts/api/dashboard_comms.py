"""Communications and broker helpers for the dashboard API router.

Handles broker DB access, watcher health, stuck task collection,
pipeline queue scanning, and dispatcher state.
"""

import json
import sqlite3
from pathlib import Path

from .config import BATCH_STATE_DIR, CURRICULUM_ROOT, LEVELS, MESSAGE_DB, PROJECT_ROOT

WATCHER_PID_FILE = PROJECT_ROOT / ".mcp" / "servers" / "message-broker" / "watcher.pid"
WATCHER_LOG_FILE = PROJECT_ROOT / ".mcp" / "servers" / "message-broker" / "watcher.log"
STUCK_DIR = CURRICULUM_ROOT / "stuck"

# Schema column check cache for backward compat
_BROKER_COLS: set | None = None


def ensure_broker_cols(conn: sqlite3.Connection) -> set:
    """Cache the column names of the messages table."""
    global _BROKER_COLS
    if _BROKER_COLS is None:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(messages)")
        _BROKER_COLS = {row[1] for row in cur.fetchall()}
    return _BROKER_COLS


def get_broker_db():
    """Get a read-only connection to the broker SQLite database."""
    if not MESSAGE_DB.exists():
        return None
    conn = sqlite3.connect(str(MESSAGE_DB))
    conn.row_factory = sqlite3.Row
    return conn


def is_watcher_running() -> dict:
    """Check watcher daemon health."""
    import os
    pid = None
    running = False
    if WATCHER_PID_FILE.exists():
        try:
            pid = int(WATCHER_PID_FILE.read_text().strip())
            os.kill(pid, 0)
            running = True
        except (ValueError, OSError):
            pass
    return {"running": running, "pid": pid}


def collect_stuck_tasks() -> list[dict]:
    """Collect stuck tasks from filesystem directories."""
    stuck_tasks = []

    if STUCK_DIR.exists():
        for f in sorted(STUCK_DIR.glob("*.md")):
            try:
                text = f.read_text()
                stuck_tasks.append({
                    "file": f.name,
                    "task_id": f.stem,
                    "preview": text[:300],
                })
            except Exception:
                pass

    for track_dir in CURRICULUM_ROOT.iterdir():
        stuck_sub = track_dir / "stuck"
        if stuck_sub.exists() and stuck_sub.is_dir():
            for f in sorted(stuck_sub.glob("*.md")):
                try:
                    text = f.read_text()
                    stuck_tasks.append({
                        "file": f"{track_dir.name}/{f.name}",
                        "task_id": f.stem,
                        "preview": text[:300],
                    })
                except Exception:
                    pass

    return stuck_tasks


def get_watcher_log_tail(num_lines: int = 20) -> list[str]:
    """Read the last N lines of the watcher log file."""
    if not WATCHER_LOG_FILE.exists():
        return []
    try:
        return WATCHER_LOG_FILE.read_text().splitlines()[-num_lines:]
    except Exception:
        return []


def fetch_broker_messages() -> list[dict]:
    """Fetch the last 20 broker messages from the SQLite database."""
    db_path = PROJECT_ROOT / ".mcp" / "servers" / "message-broker" / "messages.db"
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT id, task_id, from_llm, to_llm, message_type, content, timestamp, status
            FROM messages ORDER BY id DESC LIMIT 20
        """)
        messages = [dict(row) for row in cur.fetchall()]
        conn.close()
        return messages
    except Exception:
        return []


def read_dispatcher_state() -> dict:
    """Read the batch dispatcher state from disk."""
    ds_file = BATCH_STATE_DIR / "dispatcher_state.json"
    if not ds_file.exists():
        return {}
    try:
        with open(ds_file) as f:
            return json.load(f)
    except Exception:
        return {}
