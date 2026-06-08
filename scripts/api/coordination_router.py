"""Read-only Monitor API surface for the parallel-agent ledger."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException

from scripts.orchestration import agent_ledger

from .config import PROJECT_ROOT

router = APIRouter(tags=["coordination"])


@router.get("/summary")
async def coordination_summary():
    return await asyncio.to_thread(agent_ledger.summary, PROJECT_ROOT)


@router.get("/active")
async def coordination_active():
    tasks = await asyncio.to_thread(agent_ledger.active_tasks, PROJECT_ROOT)
    return {"total": len(tasks), "tasks": tasks}


@router.get("/tasks/{task_id}")
async def coordination_task(task_id: str):
    try:
        task = await asyncio.to_thread(agent_ledger.get_task, PROJECT_ROOT, task_id)
    except agent_ledger.LedgerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return task


def ledger_state_dir() -> Path:
    return agent_ledger.ledger_dir(PROJECT_ROOT)
