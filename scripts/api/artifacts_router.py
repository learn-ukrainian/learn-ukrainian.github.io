"""Artifacts API router — content-delivery-to-production gate check.

Mounted at /api/artifacts in main.py.

Endpoints:
    GET /api/artifacts/{track}/{slug}   Single-module gate snapshot
    GET /api/artifacts/ship-ready       Aggregate ship-ready list

Why this exists (GH #1309): before this router, the only way to ask
"which modules are ready to ship" was to scrape seven different endpoints
and cross-reference them. The artifact layer answers that question in
one call, with the EXACT set of gates defined as a tuple of booleans so
clients never guess at which combination means "ship-ready".

Boundary: this router is about the INTERNAL artifact state. The public
site (is it up, was the latest build deployed, does the canonical URL
404) lives in ``site_router.py`` — see that file for the public-facing
checks. Codex flagged that mixing these would muddy the contract.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from .config import CURRICULUM_ROOT, LEVELS, PROJECT_ROOT
from .state_compute import _compute_shippable, _get_review_score
from .state_helpers import (
    find_content_file,
    get_audit_status,
    get_final_review_info,
    get_plan_slugs,
    get_word_target_from_plan,
)

router = APIRouter(tags=["artifacts"])

PLANS_ROOT = PROJECT_ROOT / "plans"


# ---------------------------------------------------------------------
# Gate checks — each returns a bool so ``ship_ready`` is (all gates true).
# ---------------------------------------------------------------------


def _has_frontmatter(content_path: Path) -> bool:
    """True if the MDX/MD file starts with a YAML frontmatter block.

    We only check the shape, not the schema — schema checks live in the
    audit layer and will have already run by the time anything reaches
    ship-ready. This gate catches the worst failure mode: the content
    file exists but is empty / half-written.
    """
    if not content_path.is_file():
        return False
    try:
        head = content_path.read_text(encoding="utf-8", errors="replace")[:512]
    except OSError:
        return False
    return bool(re.match(r"^---\s*\n.*?\n---\s*\n", head, re.DOTALL))


def _plan_not_changed_after_build(
    plan_path: Path, content_path: Path
) -> bool:
    """True if the plan is not newer than the content file.

    If the plan has been edited since the last build, the module needs
    a rebuild before shipping. Missing either side → False (something
    is incomplete).
    """
    if not plan_path.is_file() or not content_path.is_file():
        return False
    try:
        return plan_path.stat().st_mtime <= content_path.stat().st_mtime
    except OSError:
        return False


def _final_review_approved(final_review: dict | None) -> bool:
    if not final_review or not final_review.get("exists"):
        return False
    verdict = str(final_review.get("verdict") or "").upper()
    return verdict == "PASS"


def _word_target_met(audit: dict, word_target: int) -> bool:
    wc = int(audit.get("word_count") or 0)
    return bool(word_target) and wc >= word_target


# ---------------------------------------------------------------------
# Per-module snapshot
# ---------------------------------------------------------------------


def _level_cfg(track: str) -> dict | None:
    return next((cfg for cfg in LEVELS if cfg["id"] == track), None)


def _compute_artifact_snapshot(track: str, slug: str) -> dict[str, Any]:
    """Return the full gate-by-gate snapshot for one module.

    Shape::
        {
          "track": "a1", "slug": "...",
          "gates": {
              "content_exists":    bool,
              "frontmatter_valid": bool,
              "word_target_met":   bool,
              "audit_pass":        bool,
              "final_review_pass": bool,
              "plan_fresh":        bool,
          },
          "ship_ready": bool,   # every gate green
          "audit":       {...},
          "review":      {...},
          "final_review": {...} | null,
          "word_count": int, "word_target": int,
          "content_path": "curriculum/l2-uk-en/a1/...md" | null,
          "plan_path":    "plans/a1/...yaml" | null,
        }
    """
    cfg = _level_cfg(track)
    if not cfg:
        return {"error": f"unknown track: {track}"}

    track_dir: Path = CURRICULUM_ROOT / cfg["path"]
    content_path = find_content_file(track_dir, slug)
    plan_path = PLANS_ROOT / track / f"{slug}.yaml"

    audit = get_audit_status(track_dir, slug)
    review = _get_review_score(track_dir, slug)
    final_review = get_final_review_info(track_dir, slug)

    word_target = int(audit.get("word_target") or 0)
    if word_target == 0:
        word_target = int(get_word_target_from_plan(track, slug) or 0)

    gates = {
        "content_exists": bool(content_path and content_path.is_file()),
        "frontmatter_valid": bool(content_path) and _has_frontmatter(content_path),
        "word_target_met": _word_target_met(audit, word_target),
        "audit_pass": str(audit.get("status") or "").lower() == "pass",
        "final_review_pass": _final_review_approved(final_review),
        "plan_fresh": bool(content_path) and _plan_not_changed_after_build(plan_path, content_path),
    }

    # ``_compute_shippable`` is the legacy audit+review definition and
    # does NOT include plan_fresh / frontmatter / final_review. We keep
    # it in the response for back-compat with existing dashboards, but
    # ``ship_ready`` is the strict new definition.
    legacy_shippable = _compute_shippable(audit.get("status", ""), review.get("score"))

    return {
        "track": track,
        "slug": slug,
        "gates": gates,
        "ship_ready": all(gates.values()),
        "legacy_shippable": legacy_shippable,
        "audit": {
            "status": audit.get("status"),
            "word_count": int(audit.get("word_count") or 0),
            "word_target": word_target,
            "blocking_issues": audit.get("blocking_issues", []),
        },
        "review": review,
        "final_review": final_review,
        "content_path": (
            str(content_path.relative_to(PROJECT_ROOT)) if content_path else None
        ),
        "plan_path": (
            str(plan_path.relative_to(PROJECT_ROOT)) if plan_path.exists() else None
        ),
    }


@router.get("/{track}/{slug}")
async def module_artifact(track: str, slug: str):
    """Single-module artifact snapshot."""
    result = await asyncio.to_thread(_compute_artifact_snapshot, track, slug)
    if "error" in result:
        return JSONResponse(status_code=404, content=result)
    return result


# ---------------------------------------------------------------------
# Aggregate ship-ready list
# ---------------------------------------------------------------------


def _list_ship_ready(track_filter: str | None) -> dict[str, Any]:
    """Walk every plan and return the modules whose every gate is green.

    ``track_filter`` narrows the scan to one level. Empty tracks or
    missing plan dirs are silently skipped — the response reports what
    was inspected.
    """
    ship_ready: list[dict[str, Any]] = []
    inspected = 0
    tracks_scanned: list[str] = []

    for cfg in LEVELS:
        if track_filter and cfg["id"] != track_filter:
            continue
        tracks_scanned.append(cfg["id"])
        for _num, slug in get_plan_slugs(cfg["id"]):
            inspected += 1
            snap = _compute_artifact_snapshot(cfg["id"], slug)
            if snap.get("ship_ready"):
                ship_ready.append({
                    "track": cfg["id"],
                    "slug": slug,
                    "review_score": snap.get("review", {}).get("score"),
                    "word_count": snap.get("audit", {}).get("word_count"),
                    "word_target": snap.get("audit", {}).get("word_target"),
                })

    return {
        "tracks_scanned": tracks_scanned,
        "modules_inspected": inspected,
        "ship_ready_count": len(ship_ready),
        "ship_ready": ship_ready,
    }


@router.get("/ship-ready")
async def ship_ready(
    track: str | None = Query(
        None,
        description="Narrow the scan to one track id (e.g. 'a1'). Omit to scan all.",
    ),
):
    """Modules that pass EVERY artifact gate — safe to deploy."""
    return await asyncio.to_thread(_list_ship_ready, track)
