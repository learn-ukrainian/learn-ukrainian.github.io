"""
FastAPI server for playground dashboards.

Architecture:
  - main.py: shared endpoints (config, batch state, dispatcher, websocket, static files)
  - blue_router.py: Blue team endpoints at /api/blue/...
  - gold_router.py: Gold team endpoints at /api/gold/...

Each team owns their router file. No conflicts.
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .config import (
    BATCH_STATE_DIR,
    CURRICULUM_ROOT,
    PLAYGROUNDS_DIR,
    LEVELS,
    PROJECT_ROOT,
)

# Team routers
from .blue_router import router as blue_router
from .gold_router import router as gold_router
from .dashboard_router import router as dashboard_router
from .state_router import router as state_router
from .comms_router import router as comms_router
from .rag_router import router as rag_router

app = FastAPI(
    title="Playground API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Consistent JSON error format for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": str(exc)},
    )


# Mount team routers — each team owns their own file
app.include_router(blue_router, prefix="/api/blue")
app.include_router(gold_router, prefix="/api/gold")
app.include_router(dashboard_router, prefix="/api/dashboard")
app.include_router(state_router, prefix="/api/state")
app.include_router(comms_router, prefix="/api/comms")
app.include_router(rag_router, prefix="/api/rag")


# Server start time for uptime calculation
_SERVER_START = datetime.now(timezone.utc)


# ==================== SHARED ENDPOINTS ====================

@app.get("/api/health")
async def health_check():
    """Root health check — returns server status, version, uptime."""
    now = datetime.now(timezone.utc)
    uptime = now - _SERVER_START
    return {
        "status": "ok",
        "version": app.version,
        "uptime_seconds": int(uptime.total_seconds()),
        "started_at": _SERVER_START.isoformat(),
        "checked_at": now.isoformat(),
    }


@app.get("/api/config")
async def get_config():
    return {"levels": LEVELS, "api_version": app.version}


@app.get("/api/batch/dispatcher")
async def get_dispatcher_state():
    state_file = BATCH_STATE_DIR / "dispatcher_state.json"
    if not state_file.exists():
        return {"tracks": {}}
    with open(state_file) as f:
        return json.load(f)


@app.get("/api/batch/active")
async def get_active_orchestration():
    active = []
    for track_dir in CURRICULUM_ROOT.iterdir():
        if not track_dir.is_dir():
            continue
        orch_dir = track_dir / "orchestration"
        if not orch_dir.exists():
            continue
        for module_dir in orch_dir.iterdir():
            if not module_dir.is_dir():
                continue
            latest_mtime = 0
            for f in module_dir.iterdir():
                if f.is_file():
                    latest_mtime = max(latest_mtime, f.stat().st_mtime)
            if (datetime.now().timestamp() - latest_mtime) < 900:
                active.append({
                    "slug": module_dir.name,
                    "track": track_dir.name,
                    "seconds_ago": int(datetime.now().timestamp() - latest_mtime),
                })
    return active


@app.get("/api/batch/failures")
async def get_failure_queue():
    f_file = BATCH_STATE_DIR / "failure_queue.json"
    if not f_file.exists():
        return []
    with open(f_file) as f:
        return json.load(f)


@app.get("/api/batch/usage")
async def get_batch_usage():
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


@app.get("/api/batch/checkpoints")
async def get_all_checkpoints():
    results = {}
    for f in BATCH_STATE_DIR.glob("checkpoint_*.json"):
        track = f.stem.replace("checkpoint_", "")
        try:
            with open(f) as fh:
                results[track] = json.load(fh)
        except Exception:
            pass
    return results


@app.get("/api/batch/dispatcher/running")
async def dispatcher_running():
    return {"running": False}


@app.post("/api/batch/dispatcher/scan")
async def run_dispatcher_scan():
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "batch_dispatcher.py"), "scan"]
    subprocess.run(cmd, cwd=PROJECT_ROOT)
    return {"status": "ok"}


@app.get("/api/batch/dispatcher/logs")
async def get_dispatcher_logs(lines: int = 50):
    log_file = PROJECT_ROOT / "logs" / "dispatcher.log"
    if not log_file.exists():
        return {"lines": []}
    return {"lines": log_file.read_text().splitlines()[-lines:]}


# ==================== WEBSOCKET ====================

@app.websocket("/ws/batch")
async def batch_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"type": "heartbeat"})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass


# ==================== IMAGE SERVING ====================

_IMAGE_DIR = PROJECT_ROOT / "data" / "textbook_images"
_ALLOWED_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
_MIME_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


@app.get("/images/{path:path}")
async def serve_image(path: str):
    """Serve textbook images with caching. Path relative to data/textbook_images/."""
    file_path = _IMAGE_DIR / path
    if not file_path.suffix.lower() in _ALLOWED_IMG_EXT:
        raise HTTPException(status_code=403, detail="Forbidden file type")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404)
    # Prevent path traversal
    try:
        file_path.resolve().relative_to(_IMAGE_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Path traversal not allowed")
    return FileResponse(
        file_path,
        media_type=_MIME_TYPES.get(file_path.suffix.lower(), "application/octet-stream"),
        headers={"Cache-Control": "max-age=3600"},
    )


# ==================== STATIC FILES (MUST BE LAST) ====================

@app.get("/{path:path}")
async def serve_static(path: str):
    if not path or path == "/":
        return FileResponse(PLAYGROUNDS_DIR / "index.html")
    file_path = PLAYGROUNDS_DIR / path
    if file_path.exists():
        return FileResponse(file_path)
    if (file_path / "index.html").exists():
        return FileResponse(file_path / "index.html")
    raise HTTPException(status_code=404)
