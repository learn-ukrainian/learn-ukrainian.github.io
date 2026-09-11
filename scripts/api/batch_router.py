"""FastAPI router for batch dispatcher, active orchestration, and batch websocket."""

from __future__ import annotations

import asyncio
import json
import subprocess
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from .monitor_context import MonitorContext, get_ctx

router = APIRouter()


@router.get("/api/batch/dispatcher")
async def get_dispatcher_state(ctx: MonitorContext = Depends(get_ctx)):
    state_file = ctx.roots.batch_state_dir / "dispatcher_state.json"
    if not state_file.exists():
        return {"tracks": {}}
    with open(state_file) as f:
        return json.load(f)


@router.get("/api/batch/active")
async def get_active_orchestration(ctx: MonitorContext = Depends(get_ctx)):
    active = []
    if not ctx.roots.curriculum_root.exists():
        return active
    for track_dir in ctx.roots.curriculum_root.iterdir():
        if not track_dir.is_dir():
            continue
        orch_dir = track_dir / "orchestration"
        if not orch_dir.exists():
            continue
        for module_dir in orch_dir.iterdir():
            if not module_dir.is_dir():
                continue
            latest_mtime = 0.0
            for f in module_dir.iterdir():
                if f.is_file():
                    latest_mtime = max(latest_mtime, f.stat().st_mtime)
            if (datetime.now().timestamp() - latest_mtime) < 900:
                active.append(
                    {
                        "slug": module_dir.name,
                        "track": track_dir.name,
                        "seconds_ago": int(datetime.now().timestamp() - latest_mtime),
                    }
                )
    return active


@router.get("/api/batch/failures")
async def get_failure_queue(ctx: MonitorContext = Depends(get_ctx)):
    f_file = ctx.roots.batch_state_dir / "failure_queue.json"
    if not f_file.exists():
        return []
    with open(f_file) as f:
        return json.load(f)


@router.get("/api/batch/usage")
async def get_batch_usage(ctx: MonitorContext = Depends(get_ctx)):
    usage_dir = ctx.roots.batch_state_dir / "api_usage"
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


@router.get("/api/batch/checkpoints")
async def get_all_checkpoints(ctx: MonitorContext = Depends(get_ctx)):
    results = {}
    if not ctx.roots.batch_state_dir.exists():
        return results
    for f in ctx.roots.batch_state_dir.glob("checkpoint_*.json"):
        track = f.stem.replace("checkpoint_", "")
        try:
            with open(f) as fh:
                results[track] = json.load(fh)
        except Exception:
            pass
    return results


@router.get("/api/batch/dispatcher/running")
async def dispatcher_running():
    return {"running": False}


@router.post("/api/batch/dispatcher/scan")
async def run_dispatcher_scan(ctx: MonitorContext = Depends(get_ctx)):
    cmd = [
        str(ctx.roots.live_repo_root / ".venv" / "bin" / "python"),
        str(ctx.roots.live_repo_root / "scripts" / "batch_dispatcher.py"),
        "scan",
    ]
    # Use asyncio.to_thread to avoid blocking the event loop
    result = await asyncio.to_thread(subprocess.run, cmd, cwd=ctx.roots.live_repo_root)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Dispatcher scan failed")
    return {"status": "ok"}


@router.get("/api/batch/dispatcher/logs")
async def get_dispatcher_logs(lines: int = 50, ctx: MonitorContext = Depends(get_ctx)):
    log_file = ctx.roots.project_root / "logs" / "dispatcher.log"
    if not log_file.exists():
        return {"lines": []}
    return {"lines": log_file.read_text().splitlines()[-lines:]}


# ==================== WEBSOCKET ====================


@router.websocket("/ws/batch")
async def batch_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"type": "heartbeat"})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
