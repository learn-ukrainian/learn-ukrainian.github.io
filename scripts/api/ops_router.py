"""Read-only ops surfaces: retention plans, test slots and high-load samples."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Query

from scripts.common import test_slots

from . import load_samples
from .entire_context_router import router as entire_context_router
from .monitor_context import MonitorContext, get_ctx

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ops"])
router.include_router(entire_context_router, prefix="/entire-context")


def _plan_dir(ctx: MonitorContext) -> Path:
    return ctx.roots.batch_state_dir / "fleet-comms" / "retention"


@router.get("/v1/retention/latest")
async def retention_latest(ctx: MonitorContext = Depends(get_ctx)) -> dict:
    """Return the latest retention plan JSON if present (no mutations)."""
    plan_dir = _plan_dir(ctx)
    latest = plan_dir / "latest.json"
    if not latest.is_file():
        return {
            "schema": "fleet-comms.retention.plan.v1",
            "missing": True,
            "plan_dir": str(plan_dir),
            "hint": (
                ".venv/bin/python scripts/hygiene/retention_engine.py plan"
            ),
        }
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        # Do not return exception text to HTTP clients (CodeQL py/stack-trace-exposure).
        logger.exception("retention plan unreadable: %s", latest)
        return {
            "schema": "fleet-comms.retention.plan.v1",
            "error": "unreadable_plan",
            "plan_path": str(latest),
        }
    if isinstance(payload, dict):
        payload.setdefault("plan_path", str(latest))
        payload["missing"] = False
        return payload
    return {
        "schema": "fleet-comms.retention.plan.v1",
        "error": "invalid_plan",
        "plan_path": str(latest),
    }


@router.get("/v1/retention/plan-dir")
async def retention_plan_dir(ctx: MonitorContext = Depends(get_ctx)) -> dict:
    """Expose the on-disk plan directory path (for operators)."""
    plan_dir = _plan_dir(ctx)
    return {
        "plan_dir": str(plan_dir),
        "exists": plan_dir.is_dir(),
        "archive_root_default": str(
            Path.home()
            / "Library"
            / "Application Support"
            / "learn-ukrainian"
            / "retention-archives"
        ),
        "scheduled_apply_default": False,
    }


@router.get("/v1/test-slots")
def test_slots_status(_ctx: MonitorContext = Depends(get_ctx)) -> dict:
    """Host test-slot pool (#10662): holders by task, the FIFO queue and wait times; never a path.

    A plain ``def``: the status read touches files, so FastAPI runs it off the event loop.
    """
    return test_slots.status()


@router.get("/v1/load-samples")
def load_samples_tail(
    limit: int = Query(50, ge=1, le=load_samples.MAX_SAMPLES), ctx: MonitorContext = Depends(get_ctx)
) -> dict:
    """Read the bounded attribution ring without triggering process collection."""
    return load_samples.tail(ctx.roots.batch_state_dir, limit)
