"""Read-only per-caller GitHub request counts (#10730, #10660).

Serves the hourly counters the shared client records (counts only: no URLs,
bodies, tokens or credential scopes). Mounted at ``/api/github-budget``.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from scripts.common import github_budget_counters, github_client

router = APIRouter(tags=["github-budget"])


@router.get("/callers")
def top_callers(limit: int = Query(10, ge=1, le=50, description="Callers per pool and hour")) -> dict:
    """Top callers per pool (core, graphql, search) for the current and previous hour."""
    return github_budget_counters.report_for(github_client._cache_directory(), limit=limit)
