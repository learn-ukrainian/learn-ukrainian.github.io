"""Delegate observability API router."""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query

from .config import BATCH_STATE_DIR

router = APIRouter(tags=["delegate"])

TASKS_DIR = BATCH_STATE_DIR / "tasks"
RESULT_BYTES_LIMIT = 64 * 1024
TASK_READ_RETRIES = 2
TASK_READ_RETRY_SECONDS = 0.01
ACTIVE_TASK_STATUSES = {"running", "spawning"}


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
    for attempt in range(TASK_READ_RETRIES):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            if attempt + 1 == TASK_READ_RETRIES:
                return None
            time.sleep(TASK_READ_RETRY_SECONDS)
            continue
        return data if isinstance(data, dict) else None
    return None


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


def _delegate_task_rows(statuses: set[str] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if TASKS_DIR.exists():
        for path in sorted(TASKS_DIR.glob("*.json")):
            task = _read_task_state(path)
            if task is None:
                continue
            derived_status, alive = _derived_task_status(task)
            if statuses is not None and derived_status not in statuses:
                continue
            rows.append({
                "task_id": task.get("task_id") or path.stem,
                "agent": task.get("agent"),
                "model": task.get("model"),
                "effort": task.get("effort"),
                "cli_version": task.get("cli_version"),
                "substitution": task.get("substitution"),
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
    return rows


def list_delegate_tasks(
    *,
    status: Literal["running", "done", "failed", "timeout", "spawning", "all"] = "all",
    limit: int = 50,
) -> dict[str, Any]:
    task_limit = min(max(1, int(limit)), 500)
    statuses = None if status == "all" else {status}
    rows = _delegate_task_rows(statuses)
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
    return len(_delegate_task_rows(ACTIVE_TASK_STATUSES))


def active_delegate_tasks() -> dict[str, Any]:
    active = _delegate_task_rows(ACTIVE_TASK_STATUSES)
    return {"total": len(active), "tasks": active}


@router.get("/tasks")
async def delegate_tasks(
    status: Literal["running", "done", "failed", "timeout", "spawning", "all"] = Query("all"),
    limit: int = Query(50, ge=1, le=500),
):
    return await asyncio.to_thread(list_delegate_tasks, status=status, limit=limit)


@router.get("/active")
async def delegate_active():
    return await asyncio.to_thread(active_delegate_tasks)


@router.get("/tasks/{task_id}")
async def delegate_task_detail(task_id: str):
    task, response = await asyncio.to_thread(get_delegate_task_detail, task_id)
    if task is None or response is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return response
