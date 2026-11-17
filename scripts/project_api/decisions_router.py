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
from typing import Any, cast

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from lu_machinery.api.monitor_context import MonitorContext, get_ctx, resolve_context

from .curriculum_state import monitor_surface
from .snapshots import prime_snapshot, read_snapshot, stamp_age

router = APIRouter(tags=["decisions"])

# ── Config ────────────────────────────────────────────────────────

BUDGET_MAX = 50
BUDGET_WARN = 40
_VALID_SCOPES = {"pipeline", "content", "architecture", "tooling", "pedagogy"}

# ── TTL Cache ─────────────────────────────────────────────────────

_cache: dict = {"data": None, "ts": 0.0, "path": None}
_CACHE_TTL = 60  # seconds
# Lineage searches the whole git history (tens of seconds); new citations arrive
# with merges, so a few minutes of age is acceptable and is reported.
LINEAGE_TTL_S = 300.0




def _decisions_file(ctx: MonitorContext | None = None) -> Path:
    return resolve_context(ctx).roots.project_root / "docs" / "decisions" / "decisions.yaml"


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
        return cast("list[dict[Any, Any]]", _cache["data"])

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
    """Scan decision lineage from the live checkout's git history."""
    resolved = resolve_context(ctx)
    data: dict = monitor_surface.build_lineage_response(resolved.roots.live_repo_root, decision_id=decision_id)
    return data


def _lineage_params(ctx: MonitorContext, decision_id: str | None) -> tuple[object, ...]:
    return (str(ctx.roots.live_repo_root), decision_id)


def warm_lineage_snapshot(ctx: MonitorContext) -> None:
    """Fill the unfiltered lineage snapshot after process start."""
    prime_snapshot(ctx, "decision_lineage", _lineage_params(ctx, None), LINEAGE_TTL_S, lambda: _load_lineage(ctx=ctx))


# ── Endpoints ─────────────────────────────────────────────────────


@router.get("")
def list_decisions(
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
def stale_decisions(ctx: MonitorContext = Depends(get_ctx)):
    """Active decisions past their expiry date — need re-evaluation."""
    decisions = _load_decisions(ctx)
    stale = [d for d in decisions if _is_stale(d)]
    return {
        "count": len(stale),
        "decisions": stale,
    }


@router.get("/budget")
def decision_budget(ctx: MonitorContext = Depends(get_ctx)):
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
    response: Response,
    decision_id: str | None = Query(None, description="Optional decision ID or alias filter, e.g. ADR-008 or dec-007"),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Decision files with git commit and PR backlink lineage."""
    snapshot, _state = await read_snapshot(
        ctx,
        "decision_lineage",
        _lineage_params(ctx, decision_id),
        LINEAGE_TTL_S,
        lambda: _load_lineage(decision_id=decision_id, ctx=ctx),
    )
    stamp_age(response, snapshot)
    return snapshot.value


@router.get("/scope/{scope}")
def decisions_by_scope(scope: str, ctx: MonitorContext = Depends(get_ctx)):
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
def get_decision(dec_id: str, ctx: MonitorContext = Depends(get_ctx)):
    """Single decision by ID (e.g., dec-001)."""
    decisions = _load_decisions(ctx)
    for dec in decisions:
        if dec.get("id") == dec_id:
            return {
                "decision": dec,
                "is_stale": _is_stale(dec),
            }
    raise HTTPException(status_code=404, detail=f"Decision '{dec_id}' not found")
