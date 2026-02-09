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
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from .config import (
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


class BatchLaunchRequest(BaseModel):
    """Request to launch a batch operation."""
    operation: str
    track: str
    start_num: int
    end_num: int
    model: Optional[str] = "gemini-3-flash-preview"
    resume: bool = False


# ==================== HELPERS ====================


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        message = json.dumps(data)
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Connection might be closed
                pass


manager = ConnectionManager()


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


# ==================== REPO ENDPOINTS ====================


ALLOWED_REPO_DIRS = [
    PROJECT_ROOT / "curriculum",
    PROJECT_ROOT / "plans",
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "schemas",
    PROJECT_ROOT / "scripts",
    PROJECT_ROOT / "playgrounds",
    PROJECT_ROOT / "tests",
]


def validate_repo_path(path_str: str) -> Path:
    """Validate and return a Path object, ensuring it's within allowed directories."""
    path = (PROJECT_ROOT / path_str).resolve()
    if not any(path == allowed or allowed in path.parents for allowed in ALLOWED_REPO_DIRS):
        raise HTTPException(status_code=403, detail="Access denied: Path outside allowed directories")
    return path


@app.get("/api/repo/list")
async def list_repo_files(path: str = "."):
    """List files in a repository directory."""
    target_path = validate_repo_path(path)
    if not target_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    items = []
    for item in sorted(target_path.iterdir()):
        items.append({
            "name": item.name,
            "path": str(item.relative_to(PROJECT_ROOT)),
            "is_dir": item.is_dir(),
            "size": item.stat().st_size if item.is_file() else 0,
            "modified": datetime.fromtimestamp(item.stat().st_mtime, timezone.utc).isoformat()
        })
    return {"path": path, "items": items}


@app.get("/api/repo/read")
async def read_repo_file(path: str):
    """Read content of a repository file."""
    target_path = validate_repo_path(path)
    if not target_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "path": path,
            "content": content,
            "size": len(content),
            "modified": datetime.fromtimestamp(target_path.stat().st_mtime, timezone.utc).isoformat()
        }
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not a text file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@app.get("/api/status/export")
async def export_status(level: str = "all", format: str = "json"):
    """Export module status data as CSV or JSON."""
    if level == "all":
        data = await get_all_levels()
        modules = []
        for l_id, l_data in data["levels"].items():
            for m in l_data["modules"]:
                m["level"] = l_id
                modules.append(m)
    else:
        level_data = await get_level_status(level)
        modules = level_data["modules"]
        for m in modules:
            m["level"] = level

    if format == "csv":
        import io
        import csv
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["level", "id", "num", "title", "status", "wordCount", "wordTarget", "activityCount", "naturalness"])
        writer.writeheader()
        for m in modules:
            writer.writerow({
                "level": m.get("level"),
                "id": m.get("id"),
                "num": m.get("num"),
                "title": m.get("title"),
                "status": m.get("status"),
                "wordCount": m.get("wordCount"),
                "wordTarget": m.get("wordTarget"),
                "activityCount": m.get("activityCount"),
                "naturalness": m.get("naturalness")
            })
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=curriculum-status-{level}.csv"}
        )

    return {"modules": modules}


# ==================== BATCH & AUDIT ENDPOINTS ====================


audit_status = {}  # Track running audits
batch_tasks = {}   # Track running batch operations (task_id -> info)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


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


@app.post("/api/batch/launch")
async def launch_batch(request: BatchLaunchRequest, background_tasks: BackgroundTasks):
    """Launch a batch operation."""
    task_id = f"{request.operation}-{request.track}-{request.start_num}-{request.end_num}-{int(datetime.now().timestamp())}"

    # Determine command based on operation
    cmd = []
    if request.operation == "fix-review":
        cmd = [
            ".venv/bin/python", "scripts/batch_fix_review.py",
            request.track, str(request.start_num), str(request.end_num),
            "--model", request.model or "gemini-3-flash-preview"
        ]
        if request.resume:
            cmd.append("--resume")
    elif request.operation == "research":
        cmd = [
            ".venv/bin/python", "scripts/batch_research.py",
            request.track, str(request.start_num), str(request.end_num)
        ]
    elif request.operation == "orchestrate":
        # This would need a loop or a specific script that handles orchestration range
        # For now, we'll use a placeholder or assume a script exists
        cmd = [".venv/bin/python", "scripts/audit_level.py", request.track]
    else:
        raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")

    batch_tasks[task_id] = {
        "id": task_id,
        "operation": request.operation,
        "track": request.track,
        "status": "running",
        "progress": 0,
        "total": request.end_num - request.start_num + 1,
        "start_num": request.start_num,
        "end_num": request.end_num,
        "started": datetime.now(timezone.utc).isoformat(),
        "command": " ".join(cmd)
    }

    async def run_batch_process():
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=PROJECT_ROOT
            )

            # Store PID if we need to kill it later
            batch_tasks[task_id]["pid"] = process.pid

            await manager.broadcast({
                "type": "log",
                "task_id": task_id,
                "level": "info",
                "message": f"Started process {process.pid}: {' '.join(cmd)}"
            })

            async def stream_output(stream, level):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded_line = line.decode().strip()
                    if decoded_line:
                        await manager.broadcast({
                            "type": "log",
                            "task_id": task_id,
                            "level": level,
                            "message": decoded_line
                        })

            # Stream stdout and stderr in parallel
            await asyncio.gather(
                stream_output(process.stdout, "info"),
                stream_output(process.stderr, "error")
            )

            await process.wait()

            batch_tasks[task_id]["status"] = "completed" if process.returncode == 0 else "failed"
            batch_tasks[task_id]["exit_code"] = process.returncode
            batch_tasks[task_id]["completed"] = datetime.now(timezone.utc).isoformat()

            await manager.broadcast({
                "type": "task_update",
                "task_id": task_id,
                "status": batch_tasks[task_id]["status"],
                "exit_code": process.returncode
            })

        except Exception as e:
            batch_tasks[task_id]["status"] = "error"
            batch_tasks[task_id]["error"] = str(e)
            await manager.broadcast({
                "type": "log",
                "task_id": task_id,
                "level": "error",
                "message": f"Process error: {e}"
            })

    background_tasks.add_task(run_batch_process)

    return {"task_id": task_id, "message": "Batch operation launched"}


@app.get("/api/batch/status")
async def get_all_batch_status():
    """Get status of all batch operations."""
    return list(batch_tasks.values())


@app.get("/api/batch/status/{task_id}")
async def get_batch_status(task_id: str):
    """Get status of a specific batch operation."""
    if task_id not in batch_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return batch_tasks[task_id]


@app.post("/api/batch/stop/{task_id}")
async def stop_batch(task_id: str):
    """Stop a running batch operation."""
    if task_id not in batch_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = batch_tasks[task_id]
    if task["status"] != "running":
        return {"message": "Task is not running", "status": task["status"]}

    if "pid" in task:
        try:
            import os
            import signal
            os.kill(task["pid"], signal.SIGTERM)
            task["status"] = "stopped"
            task["completed"] = datetime.now(timezone.utc).isoformat()
            return {"message": "Task stopped"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to stop task: {e}")

    return {"message": "Task has no PID, cannot stop"}


@app.get("/api/batch/recent")
async def get_recent_results():
    """Get recent batch results from checkpoints or logs."""
    # This is a bit complex as it depends on where scripts save results.
    # For now, return the in-memory tasks.
    return {"results": list(batch_tasks.values())}


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


# ==================== WEBSOCKET ====================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, we mostly broadcast
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


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
