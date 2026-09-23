"""FastAPI router for batch dispatcher, active orchestration, and batch websocket."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from .monitor_context import MonitorContext, get_ctx

logger = logging.getLogger(__name__)

router = APIRouter()

# Wall-clock bound so a hung dispatcher scan cannot pin a FastAPI worker.
DISPATCHER_SCAN_TIMEOUT_S = 120.0

_JSON_LOAD_ERRORS = (OSError, json.JSONDecodeError, UnicodeDecodeError, RecursionError)


def _load_track_json(path: Path, track: str) -> tuple[Any, str | None]:
    """Return ``(payload, None)`` or ``(None, error)`` for one track file.

    Malformed or unreadable files are logged and named in the error string.
    Callers put that string on the response ``errors`` list instead of
    omitting the track.
    """
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle), None
    except _JSON_LOAD_ERRORS as exc:
        logger.warning("failed to load %s: %s", path.name, exc)
        return None, f"{track}: {path.name}: {type(exc).__name__}"


def _with_load_errors(payload: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    if errors:
        payload["errors"] = errors
    return payload


def _run_dispatcher_scan(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        timeout=DISPATCHER_SCAN_TIMEOUT_S,
        check=False,
    )


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
    summaries: dict[str, Any] = {}
    errors: list[str] = []
    for f in sorted(usage_dir.glob("summary_*.json")):
        track = f.stem.replace("summary_", "")
        payload, error = _load_track_json(f, track)
        if error:
            errors.append(error)
            continue
        summaries[track] = payload
    return _with_load_errors(summaries, errors)


@router.get("/api/batch/checkpoints")
async def get_all_checkpoints(ctx: MonitorContext = Depends(get_ctx)):
    results: dict[str, Any] = {}
    if not ctx.roots.batch_state_dir.exists():
        return results
    errors: list[str] = []
    for f in ctx.roots.batch_state_dir.glob("checkpoint_*.json"):
        track = f.stem.replace("checkpoint_", "")
        payload, error = _load_track_json(f, track)
        if error:
            errors.append(error)
            continue
        results[track] = payload
    return _with_load_errors(results, errors)


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
    # Use asyncio.to_thread to avoid blocking the event loop. The timeout lives
    # on subprocess.run (see _run_dispatcher_scan), not on the thread call.
    try:
        result = await asyncio.to_thread(_run_dispatcher_scan, cmd, ctx.roots.live_repo_root)
    except subprocess.TimeoutExpired:
        logger.warning("dispatcher scan timed out after %ss", DISPATCHER_SCAN_TIMEOUT_S)
        return {"status": "degraded", "errors": ["dispatcher scan timed out"]}
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
