"""Estimated token/cost analytics API router."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query

from scripts.analytics.cost_report import build_cost_windows

router = APIRouter(tags=["cost"])


@router.get("")
async def cost_summary(track: str | None = Query(None)):
    return await asyncio.to_thread(build_cost_windows, track=track)


@router.get("/module/{level}/{slug}")
async def cost_module(level: str, slug: str):
    return await asyncio.to_thread(build_cost_windows, level=level, slug=slug)


@router.get("/phase/{name}")
async def cost_phase(name: str, track: str | None = Query(None)):
    return await asyncio.to_thread(build_cost_windows, phase=name, track=track)
