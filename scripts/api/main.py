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
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

import yaml
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
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
    TASKS_DIR,
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
    operation: str  # fix-review, research, orchestrate
    track: str
    start_num: int
    end_num: int
    model: Optional[str] = "gemini-3-pro-preview"


# ==================== HELPERS ====================


class ConnectionManager:
    """Manage WebSocket connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


def parse_word_count(message: str) -> tuple[int, int]:
    """Extract word count and target from message."""
    try:
        parts = message.split("/")
        count = int(parts[0])
        target = int(parts[1].split()[0])
        return count, target
    except Exception:
        return 0, 0


def parse_activity_count(message: str) -> int:
    """Extract activity count."""
    try:
        return int(message.split("/")[0])
    except Exception:
        return 0


def parse_naturalness(message: str) -> int:
    """Extract naturalness score."""
    try:
        return int(message.split("/")[0])
    except Exception:
        return 0


def is_process_running(pid: int) -> bool:
    """Check if a process is running."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def extract_module_number(module_id: str) -> int:
    """Extract module number."""
    try:
        parts = module_id.split("-")
        if len(parts) >= 2:
            return int(parts[-1])
    except (ValueError, IndexError):
        pass
    return 0


def load_module_status(status_file: Path, level_path: Optional[Path] = None) -> dict:
    """Load a single module's status."""
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

        if level_path:
            meta_file = level_path / "meta" / f"{filename}.yaml"
            if meta_file.exists():
                try:
                    with open(meta_file) as f:
                        meta_data = yaml.safe_load(f)
                    module_id = meta_data.get("id") or meta_data.get("module", "")
                    num = extract_module_number(module_id)
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
    """Get SQLite database connection."""
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


# ==================== SYSTEM ENDPOINTS ====================


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tasks_dir_exists": TASKS_DIR.exists()
    }


# ==================== CONFIG ENDPOINTS ====================


@app.get("/api/config")
async def get_config():
    """Get configuration data."""
    return {
        "levels": LEVELS,
        "api_version": "1.0.0",
    }


@app.get("/api/curriculum/tree")
async def get_curriculum_tree():
    """Get curriculum tree."""
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
    """Get all levels status."""
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
    """Get specific level status."""
    level_info = next((l for l in LEVELS if l["id"] == level), None)
    if not level_info:
        raise HTTPException(status_code=404, detail=f"Level '{level}' not found")
    status_dir = CURRICULUM_ROOT / level_info["path"] / "status"
    if not status_dir.exists():
        return {"id": level, "name": level_info["name"], "modules": [], "total": 0, "pass_count": 0, "fail_count": 0, "pending_count": 0}
    level_dir = CURRICULUM_ROOT / level_info["path"]
    modules = []
    for status_file in sorted(status_dir.glob("*.json")):
        module_data = load_module_status(status_file, level_path=level_dir)
        if "error" not in module_data:
            modules.append(module_data)
    modules.sort(key=lambda m: (m["num"], m["id"]))
    return {
        "id": level,
        "name": level_info["name"],
        "modules": modules,
        "total": len(modules),
        "pass_count": sum(1 for m in modules if m["status"] == "pass"),
        "fail_count": sum(1 for m in modules if m["status"] == "fail"),
        "pending_count": sum(1 for m in modules if m["status"] == "pending"),
    }


@app.get("/api/status/modules/{level}/{slug}")
async def get_module_status(level: str, slug: str):
    """Get module status."""
    if not validate_slug(slug): raise HTTPException(status_code=400, detail="Invalid slug")
    level_info = next((l for l in LEVELS if l["id"] == level), None)
    if not level_info: raise HTTPException(status_code=404, detail=f"Level '{level}' not found")
    status_file = CURRICULUM_ROOT / level_info["path"] / "status" / f"{slug}.json"
    if not status_file.exists(): raise HTTPException(status_code=404, detail="Not found")
    return load_module_status(status_file, level_path=CURRICULUM_ROOT / level_info["path"])


# ==================== BATCH ENDPOINTS ====================


@app.post("/api/batch/launch")
async def launch_batch(request: BatchLaunchRequest, background_tasks: BackgroundTasks):
    """Launch batch."""
    if request.operation not in ["fix-review", "research", "orchestrate"]:
        raise HTTPException(status_code=400, detail="Invalid operation")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    task_id = f"{request.operation}-{request.track}-{request.start_num}-{request.end_num}-{timestamp}"
    cmd = [sys.executable, "scripts/batch_manager.py", request.operation, request.track, str(request.start_num), str(request.end_num), "--background"]
    if request.operation == "fix-review" and request.model:
        cmd.extend(["--model", request.model])
    try:
        process = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        if process.returncode != 0: raise HTTPException(status_code=500, detail=process.stderr)
        background_tasks.add_task(monitor_task_logs, task_id)
        return {"message": "Batch launched", "task_id": task_id}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/batch/tasks")
async def list_tasks():
    """List tasks."""
    if not TASKS_DIR.exists(): return {"tasks": []}
    tasks = []
    for task_file in sorted(TASKS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with open(task_file) as f: metadata = json.load(f)
            if metadata.get("status") == "running" and metadata.get("pid"):
                if not is_process_running(metadata["pid"]):
                    metadata["status"] = "completed"
                    with open(task_file, "w") as f: json.dump(metadata, f, indent=2)
            tasks.append(metadata)
        except Exception: continue
    return {"tasks": tasks}


@app.get("/api/batch/recent")
async def get_recent_results():
    """Get recent."""
    t = await list_tasks()
    return {"results": t["tasks"][:10]}


@app.post("/api/batch/stop/{task_id}")
async def stop_task(task_id: str):
    subprocess.run([sys.executable, "scripts/batch_manager.py", "stop", task_id], cwd=PROJECT_ROOT)
    return {"message": "Stopped"}


@app.post("/api/batch/pause/{task_id}")
async def pause_task(task_id: str):
    subprocess.run([sys.executable, "scripts/batch_manager.py", "pause", task_id], cwd=PROJECT_ROOT)
    return {"message": "Paused"}


@app.post("/api/batch/resume/{task_id}")
async def resume_task(task_id: str):
    subprocess.run([sys.executable, "scripts/batch_manager.py", "resume", task_id], cwd=PROJECT_ROOT)
    return {"message": "Resumed"}


async def monitor_task_logs(task_id: str):
    """Monitor logs."""
    output_file = TASKS_DIR / f"{task_id}.output"
    metadata_file = TASKS_DIR / f"{task_id}.json"
    for _ in range(10):
        if output_file.exists(): break
        await asyncio.sleep(0.5)
    if not output_file.exists(): return
    with open(output_file, 'r') as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if line:
                level = "info"
                if "error" in line.lower() or "failed" in line.lower(): level = "error"
                elif "success" in line.lower() or "done" in line.lower(): level = "success"
                await manager.broadcast({"type": "log", "task_id": task_id, "message": line.strip(), "level": level})
            else:
                try:
                    with open(metadata_file) as mf: metadata = json.load(mf)
                    if metadata.get("status") not in ["running", "pending"]: break
                    if metadata.get("pid") and not is_process_running(metadata["pid"]): break
                except Exception: pass
                await asyncio.sleep(0.5)


# ==================== WEBSOCKET ====================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: manager.disconnect(websocket)


# ==================== STATIC FILES ====================


@app.get("/")
async def serve_index(): return FileResponse(PLAYGROUNDS_DIR / "index.html")


@app.get("/{filename:path}")
async def serve_static(filename: str):
    file_path = PLAYGROUNDS_DIR / filename
    if file_path.exists() and file_path.is_file(): return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Not found")
