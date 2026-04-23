"""Delegate observability API router."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query

from .config import BATCH_STATE_DIR

router = APIRouter(tags=["delegate"])

TASKS_DIR = BATCH_STATE_DIR / "tasks"
RESULT_BYTES_LIMIT = 64 * 1024


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _task_state_path(task_id: str) -> Path:
    safe = task_id.replace("/", "_").replace("\\", "_")
    return TASKS_DIR / f"{safe}.json"


def _read_task_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _task_age_seconds(started_at: str | None) -> float | None:
    started = _parse_iso_datetime(started_at)
    if started is None:
        return None
    return round((datetime.now(UTC) - started).total_seconds(), 1)


def _derived_task_status(task: dict[str, Any]) -> tuple[str, bool]:
    status = str(task.get("status") or "")
    pid = task.get("pid")
    alive = _pid_alive(pid) if pid else False
    if status == "running" and pid and not alive:
        return "zombie", False
    return status, alive


def list_delegate_tasks(
    *, status: Literal["running", "done", "failed", "spawning", "all"] = "all", limit: int = 50
) -> dict[str, Any]:
    task_limit = min(max(1, int(limit)), 500)
    rows: list[dict[str, Any]] = []
    if TASKS_DIR.exists():
        for path in sorted(TASKS_DIR.glob("*.json")):
            task = _read_task_state(path)
            if task is None:
                continue
            derived_status, alive = _derived_task_status(task)
            if status != "all" and derived_status != status:
                continue
            rows.append({
                "task_id": task.get("task_id") or path.stem,
                "agent": task.get("agent"),
                "model": task.get("model"),
                "effort": task.get("effort"),
                "cli_version": task.get("cli_version"),
                "status": derived_status,
                "started_at": task.get("started_at"),
                "duration_s": task.get("duration_s"),
                "age_s": _task_age_seconds(task.get("started_at")),
                "alive": alive,
            })
    rows.sort(
        key=lambda item: _parse_iso_datetime(item.get("started_at")) or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return {"total": len(rows), "tasks": rows[:task_limit]}


def get_delegate_task_detail(task_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    path = _task_state_path(task_id)
    task = _read_task_state(path)
    if task is None:
        return None, None

    _, alive = _derived_task_status(task)
    result_text = None
    truncated = False
    if task.get("status") != "running":
        result_file = task.get("result_file")
        if result_file:
            try:
                with open(result_file, encoding="utf-8") as handle:
                    result_text = handle.read(RESULT_BYTES_LIMIT + 1)
                if result_text is not None and len(result_text.encode("utf-8")) > RESULT_BYTES_LIMIT:
                    while len(result_text.encode("utf-8")) > RESULT_BYTES_LIMIT:
                        result_text = result_text[:-1]
                    truncated = True
            except OSError:
                result_text = None

    return task, {
        "task": task,
        "result": result_text,
        "result_truncated": truncated,
        "alive": alive,
    }


def active_delegate_count() -> int:
    tasks = list_delegate_tasks(status="all", limit=500)["tasks"]
    return sum(1 for task in tasks if task["status"] in {"running", "spawning"})


@router.get("/tasks")
async def delegate_tasks(
    status: Literal["running", "done", "failed", "spawning", "all"] = Query("all"),
    limit: int = Query(50, ge=1, le=500),
):
    return await asyncio.to_thread(list_delegate_tasks, status=status, limit=limit)


@router.get("/tasks/{task_id}")
async def delegate_task_detail(task_id: str):
    task, response = await asyncio.to_thread(get_delegate_task_detail, task_id)
    if task is None or response is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return response
