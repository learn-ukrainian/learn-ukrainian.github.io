"""Communications and broker helpers for the dashboard API router.

Handles broker DB access, watcher health, stuck task collection,
pipeline queue scanning, and dispatcher state. Roots and store handles
come from MonitorContext — no module-level Path globals.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from .monitor_context import MonitorContext, resolve_context

# Schema column check cache for backward compat
_BROKER_COLS: set | None = None

_BROKER_DIR = Path(".mcp") / "servers" / "message-broker"




def _broker_dir(ctx: MonitorContext | None = None) -> Path:
    return resolve_context(ctx).roots.project_root / _BROKER_DIR


def _watcher_pid_file(ctx: MonitorContext | None = None) -> Path:
    return _broker_dir(ctx) / "watcher.pid"


def _watcher_log_file(ctx: MonitorContext | None = None) -> Path:
    return _broker_dir(ctx) / "watcher.log"


def ensure_broker_cols(conn: sqlite3.Connection) -> set:
    """Cache the column names of the messages table."""
    global _BROKER_COLS
    if _BROKER_COLS is None:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(messages)")
        _BROKER_COLS = {row[1] for row in cur.fetchall()}
    return _BROKER_COLS


def get_broker_db(ctx: MonitorContext | None = None):
    """Get a connection to the broker SQLite database via MonitorContext."""
    resolved = resolve_context(ctx)
    handle = resolved.stores.message_db
    if handle is None or not handle.path.exists():
        return None
    conn = handle.connect()
    conn.row_factory = sqlite3.Row
    return conn


def is_watcher_running(ctx: MonitorContext | None = None) -> dict:
    """Check watcher daemon health."""
    pid_file = _watcher_pid_file(ctx)
    pid = None
    running = False
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            running = True
        except (ValueError, OSError):
            pass
    return {"running": running, "pid": pid}


def collect_stuck_tasks(ctx: MonitorContext | None = None) -> list[dict]:
    """Collect stuck tasks from filesystem directories."""
    resolved = resolve_context(ctx)
    curriculum_root = resolved.roots.curriculum_root
    stuck_dir = curriculum_root / "stuck"
    stuck_tasks = []

    if stuck_dir.exists():
        for f in sorted(stuck_dir.glob("*.md")):
            try:
                text = f.read_text()
                stuck_tasks.append({
                    "file": f.name,
                    "task_id": f.stem,
                    "preview": text[:300],
                })
            except Exception:
                pass

    if curriculum_root.exists():
        for track_dir in curriculum_root.iterdir():
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


def get_watcher_log_tail(num_lines: int = 20, ctx: MonitorContext | None = None) -> list[str]:
    """Read the last N lines of the watcher log file."""
    log_file = _watcher_log_file(ctx)
    if not log_file.exists():
        return []
    try:
        return log_file.read_text().splitlines()[-num_lines:]
    except Exception:
        return []


def fetch_broker_messages(ctx: MonitorContext | None = None) -> list[dict]:
    """Fetch the last 20 broker messages from the SQLite database."""
    conn = get_broker_db(ctx)
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, task_id, from_llm, to_llm, message_type, content, timestamp, status
            FROM messages ORDER BY id DESC LIMIT 20
        """)
        return [dict(row) for row in cur.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


def read_dispatcher_state(ctx: MonitorContext | None = None) -> dict:
    """Read the batch dispatcher state from disk."""
    ds_file = resolve_context(ctx).roots.batch_state_dir / "dispatcher_state.json"
    if not ds_file.exists():
        return {}
    try:
        with open(ds_file) as f:
            return json.load(f)
    except Exception:
        return {}
