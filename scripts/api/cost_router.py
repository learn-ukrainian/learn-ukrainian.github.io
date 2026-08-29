"""Estimated token/cost analytics API router."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, Query

from scripts.analytics.cost_report import build_cost_windows

from .monitor_context import MonitorContext, get_ctx

router = APIRouter(tags=["cost"])


def _cost_kwargs(ctx: MonitorContext) -> dict:
    return {
        "root": ctx.roots.curriculum_root,
        "usage_dir": ctx.roots.batch_state_dir / "api_usage",
    }


@router.get("")
async def cost_summary(
    track: str | None = Query(None),
    ctx: MonitorContext = Depends(get_ctx),
):
    return await asyncio.to_thread(build_cost_windows, track=track, **_cost_kwargs(ctx))


@router.get("/module/{level}/{slug}")
async def cost_module(level: str, slug: str, ctx: MonitorContext = Depends(get_ctx)):
    return await asyncio.to_thread(
        build_cost_windows, level=level, slug=slug, **_cost_kwargs(ctx)
    )


@router.get("/phase/{name}")
async def cost_phase(
    name: str,
    track: str | None = Query(None),
    ctx: MonitorContext = Depends(get_ctx),
):
    return await asyncio.to_thread(
        build_cost_windows, phase=name, track=track, **_cost_kwargs(ctx)
    )
