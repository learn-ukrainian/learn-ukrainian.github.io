"""Reviewer-ghost-findings API router — aggregates reviewer-hallucination telemetry.

Mounted at /api/state/reviewer-ghosts in main.py.

Endpoint:
    GET /api/state/reviewer-ghosts/{track}[?slug=<slug>&since=<iso>]

Why this exists (GH #1529 P3): when a reviewer emits a <fixes> entry whose
anchor text does not exist in current module content, the convergence loop
(via build/v6_build.py:_write_reviewer_ghost_bundle) persists the finding to
``curriculum/l2-uk-en/{level}/review/{slug}-ghost-review-r{round}.yaml`` BEFORE
deciding a terminal state. This router reads those bundles and returns
per-track aggregates so operators (and future dashboards) can watch
reviewer-hallucination rate per dimension and per reviewer agent without
scraping individual YAML files.

Filesystem is the source of truth — bundles are small per-module YAML files
and there is no database table. Each GET does a directory scan; acceptable
at the current track size (~200 modules max).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from .config import CURRICULUM_ROOT, LEVELS

router = APIRouter(tags=["reviewer-ghosts"])


def _iter_ghost_bundles(track: str) -> list[Path]:
    """Return every ghost-bundle path under the given track's review dir."""
    level_cfg = next((lvl for lvl in LEVELS if lvl["id"] == track), None)
    if not level_cfg:
        return []
    review_dir = CURRICULUM_ROOT / level_cfg["path"] / "review"
    if not review_dir.is_dir():
        return []
    return sorted(review_dir.glob("*-ghost-review-r*.yaml"))


def _parse_since(since: str | None) -> datetime | None:
    """Parse ISO-8601 ``since`` filter. ``None``/empty → no filter.

    Returns the cutoff or raises ``HTTPException(400)`` when the string is
    not ISO-8601 — a silently-ignored filter would give wrong aggregates.
    """
    if not since:
        return None
    try:
        return datetime.fromisoformat(since)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"?since must be ISO-8601 (got {since!r})",
        ) from exc


def _load_bundle(path: Path) -> dict[str, Any] | None:
    """Load and shallow-validate a ghost-bundle YAML.

    Returns ``None`` for malformed bundles so a single broken file does not
    500 the whole aggregation. Downstream operators will notice missing
    counts from a track health dashboard before they notice an endpoint
    outage.
    """
    try:
        raw = yaml.safe_load(path.read_text("utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(raw, dict):
        return None
    if not isinstance(raw.get("ghost_findings"), list):
        return None
    return raw


def _bundle_generated_at(bundle: dict[str, Any]) -> datetime | None:
    raw = bundle.get("generated_at")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


@router.get("/{track}")
def reviewer_ghosts(
    track: str,
    slug: str | None = Query(
        default=None,
        description="Restrict to a single module slug (e.g. 'colors').",
    ),
    since: str | None = Query(
        default=None,
        description="Only include bundles generated at-or-after this ISO-8601 instant.",
    ),
):
    """Aggregate ghost-finding counts across a track, with optional filters.

    Response shape:

    .. code-block:: json

        {
          "track": "a1",
          "total_ghost_findings": 7,
          "by_dimension": {"factual": 4, "honesty": 3},
          "by_reviewer_agent": {"codex-tools": 5, "claude-tools": 2},
          "recent": [ {"slug":"colors", "round":1, "dimension":"factual",
                       "anchor":"...", "generated_at":"2026-04-24T12:00:00+00:00"},
                       ... ]
        }

    ``recent`` is sorted newest-generated-first and capped at 20 entries —
    callers needing full history can iterate bundles off-API.
    """
    bundles = _iter_ghost_bundles(track)
    if not bundles and not any(lvl["id"] == track for lvl in LEVELS):
        return JSONResponse(
            status_code=404,
            content={"error": f"Track '{track}' not found"},
        )

    since_cutoff = _parse_since(since)
    total = 0
    by_dimension: dict[str, int] = {}
    by_reviewer_agent: dict[str, int] = {}
    recent_rows: list[dict[str, Any]] = []

    for path in bundles:
        bundle = _load_bundle(path)
        if bundle is None:
            continue
        if slug is not None and str(bundle.get("slug") or "") != slug:
            continue
        generated_at = _bundle_generated_at(bundle)
        if since_cutoff is not None and (
            generated_at is None or generated_at < since_cutoff
        ):
            continue

        reviewer_agent = str(bundle.get("reviewer_agent") or "") or "unknown"
        findings = bundle.get("ghost_findings") or []
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            total += 1
            dim = str(finding.get("dimension") or "unknown")
            by_dimension[dim] = by_dimension.get(dim, 0) + 1
            by_reviewer_agent[reviewer_agent] = by_reviewer_agent.get(
                reviewer_agent, 0
            ) + 1
            recent_rows.append(
                {
                    "slug": str(bundle.get("slug") or ""),
                    "round": int(bundle.get("round") or 0),
                    "dimension": dim,
                    "anchor": str(finding.get("reviewer_find_anchor") or ""),
                    "reviewer_agent": reviewer_agent,
                    "generated_at": (
                        generated_at.isoformat() if generated_at else ""
                    ),
                }
            )

    # Newest first; missing timestamps sort to the end with empty string.
    recent_rows.sort(key=lambda row: row["generated_at"], reverse=True)

    return {
        "track": track,
        "total_ghost_findings": total,
        "by_dimension": by_dimension,
        "by_reviewer_agent": by_reviewer_agent,
        "recent": recent_rows[:20],
    }
