"""
Decision Journal API router.

Mounted at /api/decisions/ in main.py.

Endpoints:
  GET  /api/decisions                  All decisions (optional ?status=active filter)
  GET  /api/decisions/lineage          Decision files with git backlink lineage
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
from fastapi import APIRouter, Depends, HTTPException, Query

from scripts.audit.decision_lineage import build_lineage_response

from .monitor_context import MonitorContext, get_ctx, production_context

router = APIRouter(tags=["decisions"])

# ── Config ────────────────────────────────────────────────────────

BUDGET_MAX = 50
BUDGET_WARN = 40
_VALID_SCOPES = {"pipeline", "content", "architecture", "tooling", "pedagogy"}

# ── TTL Cache ─────────────────────────────────────────────────────

_cache: dict = {"data": None, "ts": 0.0, "path": None}
_lineage_cache: dict = {"data": None, "ts": 0.0, "root": None}
_CACHE_TTL = 60  # seconds


def _resolve_context(ctx: MonitorContext | None = None) -> MonitorContext:
    """Fall back to the live production context for plain-Python callers."""
    if isinstance(ctx, MonitorContext):
        return ctx
    return production_context()


def _decisions_file(ctx: MonitorContext | None = None) -> Path:
    return _resolve_context(ctx).roots.project_root / "docs" / "decisions" / "decisions.yaml"


def _load_decisions(ctx: MonitorContext | None = None) -> list[dict]:
    """Load decisions from YAML with 60s TTL cache."""
    now = time.monotonic()
    decisions_file = _decisions_file(ctx)
    path_key = str(decisions_file)
    if (
        _cache["data"] is not None
        and _cache.get("path") == path_key
        and (now - _cache["ts"]) < _CACHE_TTL
    ):
        return _cache["data"]

    if not decisions_file.exists():
        _cache["data"] = []
        _cache["ts"] = now
        _cache["path"] = path_key
        return []

    raw = yaml.safe_load(decisions_file.read_text("utf-8"))
    decisions = raw.get("decisions", []) if raw else []
    _cache["data"] = decisions
    _cache["ts"] = now
    _cache["path"] = path_key
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


def _load_lineage(decision_id: str | None = None, ctx: MonitorContext | None = None) -> dict:
    """Load decision lineage with a short TTL because git history scans are heavier."""
    now = time.monotonic()
    resolved = _resolve_context(ctx)
    root_key = str(resolved.roots.live_repo_root)
    if (
        decision_id is None
        and _lineage_cache["data"] is not None
        and _lineage_cache.get("root") == root_key
        and (now - _lineage_cache["ts"]) < _CACHE_TTL
    ):
        return _lineage_cache["data"]

    data = build_lineage_response(resolved.roots.live_repo_root, decision_id=decision_id)
    if decision_id is None:
        _lineage_cache["data"] = data
        _lineage_cache["ts"] = now
        _lineage_cache["root"] = root_key
    return data


# ── Endpoints ─────────────────────────────────────────────────────


@router.get("")
async def list_decisions(
    status: str | None = Query(None, description="Filter by status (active, superseded, expired, archived)"),
    ctx: MonitorContext = Depends(get_ctx),
):
    """All decisions, optionally filtered by status."""
    decisions = _load_decisions(ctx)
    if status:
        decisions = [d for d in decisions if d.get("status") == status]
    return {
        "count": len(decisions),
        "decisions": decisions,
    }


@router.get("/stale")
async def stale_decisions(ctx: MonitorContext = Depends(get_ctx)):
    """Active decisions past their expiry date — need re-evaluation."""
    decisions = _load_decisions(ctx)
    stale = [d for d in decisions if _is_stale(d)]
    return {
        "count": len(stale),
        "decisions": stale,
    }


@router.get("/budget")
async def decision_budget(ctx: MonitorContext = Depends(get_ctx)):
    """Budget status: how many active decisions vs max allowed."""
    decisions = _load_decisions(ctx)
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


# Keep this route above /{dec_id}; otherwise "lineage" is parsed as a decision ID.
@router.get("/lineage")
async def decision_lineage(
    decision_id: str | None = Query(None, description="Optional decision ID or alias filter, e.g. ADR-008 or dec-007"),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Decision files with git commit and PR backlink lineage."""
    return _load_lineage(decision_id=decision_id, ctx=ctx)


@router.get("/scope/{scope}")
async def decisions_by_scope(scope: str, ctx: MonitorContext = Depends(get_ctx)):
    """Filter decisions by scope (pipeline, content, architecture, tooling, pedagogy)."""
    if scope not in _VALID_SCOPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope '{scope}'. Valid: {sorted(_VALID_SCOPES)}",
        )
    decisions = _load_decisions(ctx)
    filtered = [d for d in decisions if d.get("scope") == scope]
    return {
        "scope": scope,
        "count": len(filtered),
        "decisions": filtered,
    }


@router.get("/{dec_id}")
async def get_decision(dec_id: str, ctx: MonitorContext = Depends(get_ctx)):
    """Single decision by ID (e.g., dec-001)."""
    decisions = _load_decisions(ctx)
    for dec in decisions:
        if dec.get("id") == dec_id:
            return {
                "decision": dec,
                "is_stale": _is_stale(dec),
            }
    raise HTTPException(status_code=404, detail=f"Decision '{dec_id}' not found")
