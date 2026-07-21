"""Ops surfaces — Sol PR-L retention latest plan (read-only)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from .config import PROJECT_ROOT

router = APIRouter(tags=["ops"])

DEFAULT_PLAN_DIR = PROJECT_ROOT / "batch_state" / "fleet-comms" / "retention"


@router.get("/v1/retention/latest")
async def retention_latest() -> dict:
    """Return the latest retention plan JSON if present (no mutations)."""
    latest = DEFAULT_PLAN_DIR / "latest.json"
    if not latest.is_file():
        return {
            "schema": "fleet-comms.retention.plan.v1",
            "missing": True,
            "plan_dir": str(DEFAULT_PLAN_DIR),
            "hint": (
                ".venv/bin/python scripts/hygiene/retention_engine.py plan"
            ),
        }
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": "fleet-comms.retention.plan.v1",
            "error": "unreadable_plan",
            "detail": str(exc),
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
async def retention_plan_dir() -> dict:
    """Expose the on-disk plan directory path (for operators)."""
    return {
        "plan_dir": str(DEFAULT_PLAN_DIR),
        "exists": DEFAULT_PLAN_DIR.is_dir(),
        "archive_root_default": str(
            Path.home()
            / "Library"
            / "Application Support"
            / "learn-ukrainian"
            / "retention-archives"
        ),
        "scheduled_apply_default": False,
    }
