"""
Decision Journal API router.

Mounted at /api/decisions/ in main.py.

Endpoints:
  GET  /api/decisions                  All decisions (optional ?status=active filter)
  GET  /api/decisions/stale            Expired active decisions
  GET  /api/decisions/budget           Budget status (count, max, warning threshold)
  GET  /api/decisions/{dec_id}         Single decision by ID
  GET  /api/decisions/scope/{scope}    Filter by scope
"""

from __future__ import annotations

import time
from datetime import date
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException, Query

from .config import PROJECT_ROOT

router = APIRouter(tags=["decisions"])

# ── Config ────────────────────────────────────────────────────────

DECISIONS_FILE = PROJECT_ROOT / "docs" / "decisions" / "decisions.yaml"
BUDGET_MAX = 50
BUDGET_WARN = 40
_VALID_SCOPES = {"pipeline", "content", "architecture", "tooling", "pedagogy"}

# ── TTL Cache ─────────────────────────────────────────────────────

_cache: dict = {"data": None, "ts": 0.0}
_CACHE_TTL = 60  # seconds


def _load_decisions() -> list[dict]:
    """Load decisions from YAML with 60s TTL cache."""
    now = time.monotonic()
    if _cache["data"] is not None and (now - _cache["ts"]) < _CACHE_TTL:
        return _cache["data"]

    if not DECISIONS_FILE.exists():
        _cache["data"] = []
        _cache["ts"] = now
        return []

    raw = yaml.safe_load(DECISIONS_FILE.read_text("utf-8"))
    decisions = raw.get("decisions", []) if raw else []
    _cache["data"] = decisions
    _cache["ts"] = now
    return decisions


def _is_stale(dec: dict) -> bool:
    """Check if an active decision is past its expiry date."""
    if dec.get("status") != "active":
        return False
    expires = dec.get("expires")
    if not expires:
        return False
    try:
        return date.fromisoformat(str(expires)) <= date.today()
    except (ValueError, TypeError):
        return False


# ── Endpoints ─────────────────────────────────────────────────────


@router.get("")
async def list_decisions(status: str | None = Query(None, description="Filter by status (active, superseded, expired, archived)")):
    """All decisions, optionally filtered by status."""
    decisions = _load_decisions()
    if status:
        decisions = [d for d in decisions if d.get("status") == status]
    return {
        "count": len(decisions),
        "decisions": decisions,
    }


@router.get("/stale")
async def stale_decisions():
    """Active decisions past their expiry date — need re-evaluation."""
    decisions = _load_decisions()
    stale = [d for d in decisions if _is_stale(d)]
    return {
        "count": len(stale),
        "decisions": stale,
    }


@router.get("/budget")
async def decision_budget():
    """Budget status: how many active decisions vs max allowed."""
    decisions = _load_decisions()
    active = [d for d in decisions if d.get("status") == "active"]
    count = len(active)
    return {
        "active_count": count,
        "total_count": len(decisions),
        "budget_max": BUDGET_MAX,
        "budget_warn": BUDGET_WARN,
        "status": (
            "exceeded" if count >= BUDGET_MAX
            else "warning" if count >= BUDGET_WARN
            else "ok"
        ),
    }


@router.get("/scope/{scope}")
async def decisions_by_scope(scope: str):
    """Filter decisions by scope (pipeline, content, architecture, tooling, pedagogy)."""
    if scope not in _VALID_SCOPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope '{scope}'. Valid: {sorted(_VALID_SCOPES)}",
        )
    decisions = _load_decisions()
    filtered = [d for d in decisions if d.get("scope") == scope]
    return {
        "scope": scope,
        "count": len(filtered),
        "decisions": filtered,
    }


@router.get("/{dec_id}")
async def get_decision(dec_id: str):
    """Single decision by ID (e.g., dec-001)."""
    decisions = _load_decisions()
    for dec in decisions:
        if dec.get("id") == dec_id:
            return {
                "decision": dec,
                "is_stale": _is_stale(dec),
            }
    raise HTTPException(status_code=404, detail=f"Decision '{dec_id}' not found")
