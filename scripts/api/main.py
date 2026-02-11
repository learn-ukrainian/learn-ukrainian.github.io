"""
FastAPI server for playground dashboards.

Provides REST API endpoints for:
- Module status data
- Message broker communication
- Audit triggering
- Activity management
"""

import asyncio
import json
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import (
    BATCH_STATE_DIR,
    CURRICULUM_ROOT,
    MESSAGE_DB,
    PLAYGROUNDS_DIR,
    LEVELS,
    PROJECT_ROOT,
)

app = FastAPI(
    title="Playground API",
    description="API for Learn Ukrainian playground dashboards",
    version="1.0.0",
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== MODELS ====================


class MessageSend(BaseModel):
    """Message to send between agents."""
    to: str  # "claude" or "gemini"
    from_llm: str  # "claude" or "gemini"
    content: str
    message_type: str = "message"
    task_id: Optional[str] = None
    data: Optional[str] = None


class AuditRequest(BaseModel):
    """Request to audit a module."""
    level: str
    slug: str


def validate_slug(slug: str) -> bool:
    """Validate slug doesn't contain path traversal characters."""
    if ".." in slug or "/" in slug or "\\" in slug:
        return False
    return True


class ActivitySave(BaseModel):
    """Request to save activities to a module."""
    activities: list


class DispatcherStartRequest(BaseModel):
    """Request to start the batch dispatcher."""
    one_shot: bool = False
    dry_run: bool = False
    track: Optional[str] = None
    include_tracks: Optional[str] = None
    exclude_tracks: Optional[str] = None


# ==================== HELPERS ====================


def parse_word_count(message: str) -> tuple[int, int]:
    """Extract word count and target from message like '3375/3000 (raw: 3539)'."""
    try:
        parts = message.split("/")
        count = int(parts[0])
        target = int(parts[1].split()[0])
        return count, target
    except Exception:
        return 0, 0


def parse_activity_count(message: str) -> int:
    """Extract activity count from message like '13/8'."""
    try:
        return int(message.split("/")[0])
    except Exception:
        return 0


def parse_naturalness(message: str) -> int:
    """Extract naturalness score from message like '9/10 (High)'."""
    try:
        return int(message.split("/")[0])
    except Exception:
        return 0


def extract_module_number(module_id: str) -> int:
    """Extract module number from ID like 'b2-hist-116' or 'c1-bio-053'."""
    try:
        # Split by '-' and get the last part which should be the number
        parts = module_id.split("-")
        if len(parts) >= 2:
            return int(parts[-1])
    except (ValueError, IndexError):
        pass
    return 0


def load_module_status(status_file: Path, level_path: Optional[Path] = None) -> dict:
    """Load a single module's status from JSON file.

    Args:
        status_file: Path to the status JSON file
        level_path: Optional path to the level directory (for loading meta files)
    """
    try:
        with open(status_file) as f:
            data = json.load(f)

        gates = data.get("gates", {})
        overall = data.get("overall", {})

        lesson_msg = gates.get("lesson", {}).get("message", "0/0")
        word_count, word_target = parse_word_count(lesson_msg)

        activity_msg = gates.get("activities", {}).get("message", "0/0")
        activity_count = parse_activity_count(activity_msg)

        nat_msg = gates.get("naturalness", {}).get("message", "0/0")
        naturalness = parse_naturalness(nat_msg)

        status = overall.get("status", "pending")

        filename = status_file.stem
        num = 0
        title = filename.replace("-", " ").title()

        # Try to extract number from filename like "04-this-is-i-am"
        try:
            num = int(filename.split("-")[0])
        except (ValueError, IndexError):
            # Filename doesn't start with a number (e.g., track modules like "ivan-franko")
            # Try to get number from meta file
            if level_path:
                meta_file = level_path / "meta" / f"{filename}.yaml"
                if meta_file.exists():
                    try:
                        with open(meta_file) as f:
                            meta_data = yaml.safe_load(f)
                        # Extract number from module ID like "c1-bio-053" or "b2-hist-116"
                        # Prefer 'id' over 'module' since 'module' is sometimes just the slug
                        module_id = meta_data.get("id") or meta_data.get("module", "")
                        num = extract_module_number(module_id)
                        # Use title from meta if available
                        if meta_data.get("title"):
                            title = meta_data["title"]
                    except Exception:
                        pass

        return {
            "id": filename,
            "num": num,
            "title": title,
            "status": status,
            "wordCount": word_count,
            "wordTarget": word_target or 3000,
            "activityCount": activity_count,
            "naturalness": naturalness,
            "gates": {
                gate: info.get("status", "pending")
                for gate, info in gates.items()
            },
            "violations": overall.get("blocking_issues", []),
        }
    except Exception as e:
        return {"error": str(e), "file": str(status_file)}


def get_db_connection():
    """Get SQLite database connection for message broker."""
    if not MESSAGE_DB.exists():
        MESSAGE_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(MESSAGE_DB)
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
        conn.commit()
        return conn
    return sqlite3.connect(MESSAGE_DB)


# ==================== CONFIG ENDPOINTS ====================


@app.get("/api/config")
async def get_config():
    """Get configuration data for frontend use."""
    return {
        "levels": LEVELS,
        "api_version": "1.0.0",
    }


@app.get("/api/curriculum/tree")
async def get_curriculum_tree():
    """Get full curriculum tree hierarchy."""
    tree = []
    for level_info in LEVELS:
        level_dir = CURRICULUM_ROOT / level_info["path"]
        status_dir = level_dir / "status"

        modules = []
        if status_dir.exists():
            for status_file in sorted(status_dir.glob("*.json")):
                slug = status_file.stem
                modules.append({"slug": slug, "has_status": True})
        else:
            # List markdown files if no status
            for md_file in sorted(level_dir.glob("*.md")):
                slug = md_file.stem
                modules.append({"slug": slug, "has_status": False})

        tree.append({
            "id": level_info["id"],
            "name": level_info["name"],
            "path": level_info["path"],
            "module_count": len(modules),
            "modules": modules,
        })

    return {"levels": tree}


# ==================== STATUS ENDPOINTS ====================


@app.get("/api/status/levels")
async def get_all_levels():
    """Get summary of all levels with pass/fail counts."""
    result = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "levels": {},
        "summary": {"total_modules": 0, "total_pass": 0, "total_fail": 0, "total_pending": 0},
    }

    for level_info in LEVELS:
        level_data = await get_level_status(level_info["id"])
        result["levels"][level_info["id"]] = level_data
        result["summary"]["total_modules"] += level_data["total"]
        result["summary"]["total_pass"] += level_data["pass_count"]
        result["summary"]["total_fail"] += level_data["fail_count"]
        result["summary"]["total_pending"] += level_data["pending_count"]

    return result


@app.get("/api/status/levels/{level}")
async def get_level_status(level: str):
    """Get all modules for a specific level."""
    level_info = next((l for l in LEVELS if l["id"] == level), None)
    if not level_info:
        raise HTTPException(status_code=404, detail=f"Level '{level}' not found")

    status_dir = CURRICULUM_ROOT / level_info["path"] / "status"

    if not status_dir.exists():
        return {
            "id": level_info["id"],
            "name": level_info["name"],
            "modules": [],
            "total": 0,
            "pass_count": 0,
            "fail_count": 0,
            "pending_count": 0,
        }

    level_dir = CURRICULUM_ROOT / level_info["path"]
    modules = []
    for status_file in sorted(status_dir.glob("*.json")):
        module_data = load_module_status(status_file, level_path=level_dir)
        if "error" not in module_data:
            modules.append(module_data)

    # Sort by number, then by id for stable ordering when numbers are equal
    modules.sort(key=lambda m: (m["num"], m["id"]))

    pass_count = sum(1 for m in modules if m["status"] == "pass")
    fail_count = sum(1 for m in modules if m["status"] == "fail")
    pending_count = sum(1 for m in modules if m["status"] == "pending")

    return {
        "id": level_info["id"],
        "name": level_info["name"],
        "modules": modules,
        "total": len(modules),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pending_count": pending_count,
    }


@app.get("/api/status/modules/{level}/{slug}")
async def get_module_status(level: str, slug: str):
    """Get detailed status for a single module."""
    if not validate_slug(slug):
        raise HTTPException(status_code=400, detail="Invalid slug (path traversal detected)")

    level_info = next((l for l in LEVELS if l["id"] == level), None)
    if not level_info:
        raise HTTPException(status_code=404, detail=f"Level '{level}' not found")

    level_dir = CURRICULUM_ROOT / level_info["path"]
    status_file = level_dir / "status" / f"{slug}.json"

    if not status_file.exists():
        raise HTTPException(status_code=404, detail=f"Module '{slug}' not found in level '{level}'")

    return load_module_status(status_file, level_path=level_dir)


# ==================== AUDIT ENDPOINTS ====================


audit_status = {}  # Track running audits


@app.post("/api/audit/module")
async def trigger_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    """Trigger an audit on a module."""
    level_info = next((l for l in LEVELS if l["id"] == request.level), None)
    if not level_info:
        raise HTTPException(status_code=404, detail=f"Level '{request.level}' not found")

    # Find the module file
    level_dir = CURRICULUM_ROOT / level_info["path"]
    module_files = list(level_dir.glob(f"*{request.slug}*.md"))

    if not module_files:
        # Try exact match
        module_files = list(level_dir.glob(f"{request.slug}.md"))

    if not module_files:
        raise HTTPException(status_code=404, detail=f"Module file for '{request.slug}' not found")

    module_path = module_files[0]
    audit_key = f"{request.level}/{request.slug}"

    # Mark as running
    audit_status[audit_key] = {"status": "running", "started": datetime.now(timezone.utc).isoformat()}

    # Run audit in background
    async def run_audit():
        try:
            result = subprocess.run(
                [".venv/bin/python", "scripts/audit_module.py", str(module_path)],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=120,
            )
            audit_status[audit_key] = {
                "status": "completed",
                "exit_code": result.returncode,
                "stdout": result.stdout[-5000:] if len(result.stdout) > 5000 else result.stdout,
                "stderr": result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr,
                "completed": datetime.now(timezone.utc).isoformat(),
            }
        except subprocess.TimeoutExpired:
            audit_status[audit_key] = {"status": "timeout"}
        except Exception as e:
            audit_status[audit_key] = {"status": "error", "error": str(e)}

    background_tasks.add_task(run_audit)

    return {"message": f"Audit started for {module_path.name}", "audit_key": audit_key}


@app.get("/api/audit/status/{level}/{slug}")
async def get_audit_status(level: str, slug: str):
    """Get the status of a running or completed audit."""
    audit_key = f"{level}/{slug}"
    return audit_status.get(audit_key, {"status": "not_found"})


# ==================== MESSAGE ENDPOINTS ====================


@app.get("/api/messages/inbox/{agent}")
async def get_inbox(agent: str, unread_only: bool = True, limit: int = 50, task_id: Optional[str] = None):
    """Get messages for an agent."""
    if agent not in ("claude", "gemini"):
        raise HTTPException(status_code=400, detail="Agent must be 'claude' or 'gemini'")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp, acknowledged FROM messages WHERE to_llm = ?"
    params = [agent]

    if unread_only:
        query += " AND acknowledged = 0"

    if task_id:
        query += " AND task_id = ?"
        params.append(task_id)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "task_id": row[1],
            "from_llm": row[2],
            "to_llm": row[3],
            "message_type": row[4],
            "content": row[5],
            "data": row[6],
            "timestamp": row[7],
            "acknowledged": bool(row[8]),
        }
        for row in rows
    ]


@app.post("/api/messages/send")
async def send_message(msg: MessageSend):
    """Send a message between agents."""
    if msg.to not in ("claude", "gemini"):
        raise HTTPException(status_code=400, detail="'to' must be 'claude' or 'gemini'")
    if msg.from_llm not in ("claude", "gemini"):
        raise HTTPException(status_code=400, detail="'from_llm' must be 'claude' or 'gemini'")

    conn = get_db_connection()
    cursor = conn.cursor()

    timestamp = datetime.now(timezone.utc).isoformat()

    cursor.execute(
        """
        INSERT INTO messages (task_id, from_llm, to_llm, message_type, content, data, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (msg.task_id, msg.from_llm, msg.to, msg.message_type, msg.content, msg.data, timestamp),
    )

    message_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"message_id": message_id, "timestamp": timestamp}


@app.post("/api/messages/acknowledge/{message_id}")
async def acknowledge_message(message_id: int):
    """Mark a message as acknowledged/read."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE messages SET acknowledged = 1 WHERE id = ?", (message_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected == 0:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")

    return {"acknowledged": message_id}


@app.get("/api/messages/tasks")
async def get_tasks():
    """List all task IDs with message counts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT task_id, COUNT(*) as count, MAX(timestamp) as last_message
        FROM messages
        WHERE task_id IS NOT NULL AND task_id != ''
        GROUP BY task_id
        ORDER BY last_message DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {"task_id": row[0], "message_count": row[1], "last_message": row[2]}
        for row in rows
    ]


@app.get("/api/messages/conversation/{task_id}")
async def get_conversation(task_id: str, limit: int = 100):
    """Get full conversation for a task."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp, acknowledged
        FROM messages
        WHERE task_id = ?
        ORDER BY id ASC
        LIMIT ?
        """,
        (task_id, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "task_id": row[1],
            "from_llm": row[2],
            "to_llm": row[3],
            "message_type": row[4],
            "content": row[5],
            "data": row[6],
            "timestamp": row[7],
            "acknowledged": bool(row[8]),
        }
        for row in rows
    ]


# ==================== ACTIVITY ENDPOINTS ====================


@app.get("/api/activities/{level}/{slug}")
async def get_activities(level: str, slug: str):
    """Get activities for a module."""
    if not validate_slug(slug):
        raise HTTPException(status_code=400, detail="Invalid slug (path traversal detected)")

    level_info = next((l for l in LEVELS if l["id"] == level), None)
    if not level_info:
        raise HTTPException(status_code=404, detail=f"Level '{level}' not found")

    activity_file = CURRICULUM_ROOT / level_info["path"] / "activities" / f"{slug}.yaml"

    if not activity_file.exists():
        return {"activities": [], "exists": False}

    try:
        with open(activity_file) as f:
            activities = yaml.safe_load(f)
        return {"activities": activities or [], "exists": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading activities: {e}")


@app.post("/api/activities/{level}/{slug}")
async def save_activities(level: str, slug: str, request: ActivitySave):
    """Save activities to a module."""
    if not validate_slug(slug):
        raise HTTPException(status_code=400, detail="Invalid slug (path traversal detected)")

    level_info = next((l for l in LEVELS if l["id"] == level), None)
    if not level_info:
        raise HTTPException(status_code=404, detail=f"Level '{level}' not found")

    activities_dir = CURRICULUM_ROOT / level_info["path"] / "activities"
    activities_dir.mkdir(parents=True, exist_ok=True)

    activity_file = activities_dir / f"{slug}.yaml"

    try:
        with open(activity_file, "w") as f:
            yaml.dump(request.activities, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return {"saved": str(activity_file), "count": len(request.activities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving activities: {e}")


# ==================== BATCH ENDPOINTS ====================


VALID_TRACKS = {
    "a1", "a2", "b1", "b2", "c1", "c2",
    "b2-hist", "c1-bio", "c1-hist", "lit",
    "lit-essay", "lit-hist-fic", "lit-fantastika", "lit-war", "lit-humor", "lit-juvenile",
    "oes", "ruth", "b2-pro", "c1-pro",
}


def validate_track(track: str) -> bool:
    """Validate track name."""
    return track in VALID_TRACKS


@app.get("/api/batch/dispatcher")
async def get_dispatcher_state():
    """Get full dispatcher state (tracks, stats, history)."""
    state_file = BATCH_STATE_DIR / "dispatcher_state.json"
    if not state_file.exists():
        raise HTTPException(status_code=404, detail="Dispatcher state not found")
    try:
        with open(state_file) as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading dispatcher state: {e}")


@app.get("/api/batch/state/{track}")
async def get_batch_track_state(track: str):
    """Get batch state for a specific track."""
    if not validate_track(track):
        raise HTTPException(status_code=400, detail=f"Invalid track: {track}")
    state_file = BATCH_STATE_DIR / f"state_{track}.json"
    if not state_file.exists():
        raise HTTPException(status_code=404, detail=f"No batch state for track '{track}'")
    try:
        with open(state_file) as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading track state: {e}")


@app.get("/api/batch/failures")
async def get_failure_queue():
    """Get the global failure queue."""
    queue_file = BATCH_STATE_DIR / "failure_queue.json"
    if not queue_file.exists():
        return []
    try:
        with open(queue_file) as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading failure queue: {e}")


@app.get("/api/batch/failures/{track}")
async def get_track_failures(track: str):
    """Get detailed failure records for a specific track."""
    if not validate_track(track):
        raise HTTPException(status_code=400, detail=f"Invalid track: {track}")
    failures_dir = BATCH_STATE_DIR / "failures" / track
    if not failures_dir.exists():
        return []
    results = []
    for f in sorted(failures_dir.glob("*.json")):
        try:
            with open(f) as fh:
                results.append(json.load(fh))
        except Exception:
            pass
    return results


@app.get("/api/batch/escalations")
async def get_escalations():
    """Get all modules escalated to Claude across all tracks."""
    failures_dir = BATCH_STATE_DIR / "failures"
    if not failures_dir.exists():
        return []
    results = []
    for track_dir in sorted(failures_dir.iterdir()):
        if not track_dir.is_dir():
            continue
        for f in sorted(track_dir.glob("*.json")):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                    if data.get("escalated"):
                        results.append(data)
            except Exception:
                pass
    return results


@app.get("/api/batch/usage")
async def get_batch_usage():
    """Get API usage summaries for all tracks."""
    usage_dir = BATCH_STATE_DIR / "api_usage"
    if not usage_dir.exists():
        return {}
    summaries = {}
    for f in sorted(usage_dir.glob("summary_*.json")):
        track = f.stem.replace("summary_", "")
        try:
            with open(f) as fh:
                summaries[track] = json.load(fh)
        except Exception:
            pass
    return summaries


@app.get("/api/batch/health")
async def get_batch_health():
    """Get batch system health: lock status, running tracks, last activity."""
    locks_dir = BATCH_STATE_DIR / "locks"
    running_tracks = []
    if locks_dir.exists():
        for lock_file in locks_dir.glob("*.lock"):
            track = lock_file.stem
            try:
                pid = lock_file.read_text().strip()
                running_tracks.append({"track": track, "pid": pid})
            except Exception:
                pass

    # Find last activity across all state files
    last_activity = None
    for state_file in BATCH_STATE_DIR.glob("state_*.json"):
        try:
            mtime = state_file.stat().st_mtime
            ts = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
            if last_activity is None or ts > last_activity:
                last_activity = ts
        except Exception:
            pass

    # Check dispatcher state exists
    dispatcher_exists = (BATCH_STATE_DIR / "dispatcher_state.json").exists()

    return {
        "status": "ok",
        "dispatcher_state_exists": dispatcher_exists,
        "running_tracks": running_tracks,
        "last_activity": last_activity,
        "batch_state_dir_exists": BATCH_STATE_DIR.exists(),
    }


# ==================== DISPATCHER CONTROL ====================


# Track running dispatcher process
_dispatcher_process = None


@app.post("/api/batch/dispatcher/start")
async def start_dispatcher(request: DispatcherStartRequest):
    """Start the batch dispatcher as a background process."""
    global _dispatcher_process
    if _dispatcher_process and _dispatcher_process.poll() is None:
        return {"status": "already_running", "pid": _dispatcher_process.pid}

    cmd = [".venv/bin/python", "scripts/batch_dispatcher.py", "run"]
    if request.one_shot:
        cmd.append("--one-shot")
    if request.dry_run:
        cmd.append("--dry-run")
    if request.track:
        cmd.extend(["--track", request.track])
    if request.include_tracks:
        cmd.extend(["--include-tracks", request.include_tracks])
    if request.exclude_tracks:
        cmd.extend(["--exclude-tracks", request.exclude_tracks])

    # Log dispatcher output to file so it's observable
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "dispatcher.log"
    fh = open(log_file, "a")
    fh.write(f"\n{'='*60}\n")
    fh.write(f"Started: {datetime.now(timezone.utc).isoformat()}\n")
    fh.write(f"Command: {' '.join(cmd)}\n")
    fh.write(f"{'='*60}\n")
    fh.flush()

    _dispatcher_process = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        stdout=fh,
        stderr=subprocess.STDOUT,
    )

    return {
        "status": "started",
        "pid": _dispatcher_process.pid,
        "cmd": " ".join(cmd),
        "log_file": str(log_file),
    }


@app.post("/api/batch/dispatcher/stop")
async def stop_dispatcher():
    """Stop the running batch dispatcher."""
    global _dispatcher_process
    if not _dispatcher_process or _dispatcher_process.poll() is not None:
        return {"status": "not_running"}

    pid = _dispatcher_process.pid
    _dispatcher_process.terminate()
    try:
        _dispatcher_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        _dispatcher_process.kill()

    _dispatcher_process = None
    return {"status": "stopped", "pid": pid}


@app.get("/api/batch/dispatcher/running")
async def dispatcher_running():
    """Check if the dispatcher is currently running."""
    if _dispatcher_process and _dispatcher_process.poll() is None:
        return {"running": True, "pid": _dispatcher_process.pid}
    return {"running": False}


@app.post("/api/batch/cleanup")
async def cleanup_stale_state():
    """Clean up stale running modules, dead locks, and orphaned processes."""
    cleaned = {"stale_modules": [], "stale_locks": [], "orphaned_pids": []}

    # 1. Fix stale "running" modules (>2 hours old)
    if BATCH_STATE_DIR.exists():
        for sf in BATCH_STATE_DIR.glob("state_*.json"):
            try:
                data = json.loads(sf.read_text(encoding="utf-8"))
                changed = False
                for slug, mod in data.get("modules", {}).items():
                    if mod.get("status") == "running" and mod.get("start_time"):
                        start = datetime.fromisoformat(mod["start_time"].replace("Z", "+00:00"))
                        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
                        if elapsed > 7200:  # 2 hours
                            track = sf.stem.replace("state_", "")
                            mod["status"] = "fail"
                            mod["end_time"] = mod["start_time"]
                            changed = True
                            cleaned["stale_modules"].append(f"{track}/{slug}")
                if changed:
                    sf.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            except Exception:
                pass

    # 2. Remove stale lock files (PID not running)
    lock_dir = BATCH_STATE_DIR / "locks"
    if lock_dir.exists():
        for lf in lock_dir.glob("*.lock"):
            try:
                lock_data = json.loads(lf.read_text())
                pid = lock_data.get("pid")
                if pid:
                    try:
                        import os
                        os.kill(pid, 0)  # Check if process exists
                    except OSError:
                        cleaned["stale_locks"].append(lf.name)
                        lf.unlink()
            except Exception:
                pass

    return {"cleaned": cleaned, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/batch/dispatcher/scan")
async def run_dispatcher_scan():
    """Trigger a dispatcher scan (updates dispatcher_state.json with fresh data)."""
    try:
        cmd = [str(PROJECT_ROOT / ".venv" / "bin" / "python"),
               str(PROJECT_ROOT / "scripts" / "batch_dispatcher.py"), "scan"]
        result = subprocess.run(
            cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120
        )
        # Read back the updated state
        state_file = BATCH_STATE_DIR / "dispatcher_state.json"
        state = {}
        if state_file.exists():
            state = json.loads(state_file.read_text(encoding="utf-8"))
        return {
            "success": result.returncode == 0,
            "output": result.stdout[-2000:] if result.stdout else "",
            "state": state,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Scan timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {e}")


@app.get("/api/batch/dispatcher/logs")
async def get_dispatcher_logs(lines: int = 50):
    """Get the last N lines from the dispatcher log file."""
    log_file = PROJECT_ROOT / "logs" / "dispatcher.log"
    if not log_file.exists():
        return {"lines": [], "exists": False}
    try:
        text = log_file.read_text()
        all_lines = text.splitlines()
        tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
        return {"lines": tail, "exists": True, "total_lines": len(all_lines)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log: {e}")


# ==================== WEBSOCKET ====================


_ws_clients: list[WebSocket] = []


@app.websocket("/ws/batch")
async def batch_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time batch state updates.

    Pushes change notifications when state files are modified.
    Clients should fetch full data via REST for changed tracks.
    """
    await websocket.accept()
    _ws_clients.append(websocket)
    last_mtimes: dict[str, float] = {}

    try:
        while True:
            changes = []

            # Check dispatcher state
            ds_file = BATCH_STATE_DIR / "dispatcher_state.json"
            if ds_file.exists():
                try:
                    mtime = ds_file.stat().st_mtime
                    if last_mtimes.get("dispatcher") != mtime:
                        last_mtimes["dispatcher"] = mtime
                        changes.append("dispatcher")
                except OSError:
                    pass

            # Check track states
            if BATCH_STATE_DIR.exists():
                for sf in BATCH_STATE_DIR.glob("state_*.json"):
                    try:
                        track = sf.stem.replace("state_", "")
                        mtime = sf.stat().st_mtime
                        if last_mtimes.get(track) != mtime:
                            last_mtimes[track] = mtime
                            changes.append(track)
                    except OSError:
                        pass

            # Check failure queue
            fq_file = BATCH_STATE_DIR / "failure_queue.json"
            if fq_file.exists():
                try:
                    mtime = fq_file.stat().st_mtime
                    if last_mtimes.get("failures") != mtime:
                        last_mtimes["failures"] = mtime
                        changes.append("failures")
                except OSError:
                    pass

            if changes:
                await websocket.send_json({
                    "type": "changes",
                    "changed": changes,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            else:
                await websocket.send_json({"type": "heartbeat"})

            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)


# ==================== STATIC FILES ====================


# Serve playground HTML files
@app.get("/")
async def serve_index():
    """Serve the playground index."""
    return FileResponse(PLAYGROUNDS_DIR / "index.html")


@app.get("/{filename:path}")
async def serve_static(filename: str):
    """Serve static files from playgrounds directory."""
    # Skip WebSocket paths (handled by websocket route)
    if filename.startswith("ws/"):
        raise HTTPException(status_code=404, detail="Not a static file")
    file_path = PLAYGROUNDS_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
