"""Read-only Monitor API surface for the parallel-agent ledger."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from scripts.orchestration import agent_ledger

from .monitor_context import MonitorContext, get_ctx, resolve_context

router = APIRouter(tags=["coordination"])




def _project_root(ctx: MonitorContext | None = None) -> Path:
    return resolve_context(ctx).roots.project_root


@router.get("/summary")
async def coordination_summary(ctx: MonitorContext = Depends(get_ctx)):
    return await asyncio.to_thread(agent_ledger.summary, _project_root(ctx))


@router.get("/active")
async def coordination_active(ctx: MonitorContext = Depends(get_ctx)):
    tasks = await asyncio.to_thread(agent_ledger.active_tasks, _project_root(ctx))
    return {"total": len(tasks), "tasks": tasks}


@router.get("/tasks/{task_id}")
async def coordination_task(task_id: str, ctx: MonitorContext = Depends(get_ctx)):
    try:
        task = await asyncio.to_thread(agent_ledger.get_task, _project_root(ctx), task_id)
    except agent_ledger.LedgerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return task


def ledger_state_dir(ctx: MonitorContext | None = None) -> Path:
    return agent_ledger.ledger_dir(_project_root(ctx))
