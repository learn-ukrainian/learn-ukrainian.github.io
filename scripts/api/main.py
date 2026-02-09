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
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import (
    CURRICULUM_ROOT,
    MESSAGE_DB,
    PLAYGROUNDS_DIR,
    LEVELS,
    PROJECT_ROOT,
)
from scripts.utils.monitoring import MetricsManager

metrics = MetricsManager()

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


# ==================== MONITORING ENDPOINTS ====================


@app.get("/api/health")
async def health_check():
    """Basic health check endpoint with alerts."""
    alerts = metrics.check_alerts()
    return {
        "status": "healthy" if not alerts else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "alerts": alerts
    }


@app.get("/api/metrics/llm")
async def get_llm_metrics():
    """Get LLM usage summary metrics."""
    return metrics.get_llm_metrics_summary()


@app.get("/api/metrics/batch")
async def get_batch_metrics(limit: int = 50):
    """Get recent batch operation metrics."""
    return metrics.get_recent_batch_operations(limit=limit)


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


# ==================== STATIC FILES ====================


# Serve playground HTML files
@app.get("/")
async def serve_index():
    """Serve the playground index."""
    return FileResponse(PLAYGROUNDS_DIR / "index.html")


@app.get("/{filename:path}")
async def serve_static(filename: str):
    """Serve static files from playgrounds directory."""
    file_path = PLAYGROUNDS_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
