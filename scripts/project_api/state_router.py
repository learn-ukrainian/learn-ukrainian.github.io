"""Product half of the State API: curriculum pipeline state, coverage, scores and issues.

Mounted at /api/state/ by the product entry, next to the machinery
``scripts.api.state_router`` (routing and GitHub budgets, manifest).

Endpoints:
  GET /api/state/summary              Full project snapshot
  GET /api/state/pipeline/{track}     Per-module pipeline state for one track
  GET /api/state/preparation          Active manifest bundle/publication roster
  GET /api/state/preparation/{track}/{slug} Canonical one-module preparation
  GET /api/state/weak-points          Modules with quality issues
  GET /api/state/build-status/{track}  Compact live build progress (one call)
  GET /api/state/build-status          All-tracks build progress summary
  GET /api/state/module-range/{track}  Deterministic committed-file status for a module range
  GET /api/state/module/{track}/{num}  Single module deep-dive with comms
  GET /api/state/final-reviews/{track} Phase F results aggregated per track
  GET /api/state/failing              Modules with audit/phase failures
  GET /api/state/scores/{track}       Per-module status + LLM-QG aggregate + per-dim scores
  GET /api/state/scores/{track}/{slug} One module's status + per-dimension scores
  GET /api/state/research-coverage    Per-track research completeness
  GET /api/state/research/{track}    Per-module research quality + dimensions + upgrade queue
  GET /api/state/review-coverage      Per-track review completeness + quality
  GET /api/state/issues               Aggregated outstanding issues

Performance notes:
  - Heavy endpoints run their sync I/O in asyncio.to_thread().
  - Results are cached in-memory with a TTL (60s for summary/pipeline, 300s for coverage).
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

try:
    from lu_machinery.path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from lu_machinery.path_safety import safe_join  # scripts.api package import (production)

from lu_machinery.api.monitor_context import MonitorContext, get_ctx
from lu_machinery.api.repository_authority import (
    RepositoryAuthorityError,
    build_repository_authority,
    preparation_data_root,
)
from lu_machinery.api.rules_router import _matches_etag
from lu_machinery.api.state_helpers import (
    cache_get,
    cache_get_or_compute,
    cache_get_or_compute_async,
    cache_get_with_age,
    cache_invalidate,
    cache_set,
    ctx_scoped_ttl_key,
)

from . import preparation_state
from .config import LEVELS
from .curriculum_state import (
    detect_pipeline_version,
    get_audit_status,
    get_plan_slugs,
    get_research_score,
    get_word_target_from_plan,
    monitor_surface,
    read_v2_state,
    read_v3_state,
)
from .state_build import (
    compute_build_stats,
    compute_build_stats_all,
    compute_build_status_all,
    compute_build_status_track,
    compute_enrichment_status,
    compute_module_range_status,
    compute_track_health,
)
from .state_compute import (
    compute_llm_qg_track,
    compute_module_detail,
    compute_research_detail,
    read_llm_qg,
    severity_key,
    summarize_llm_qg,
)
from .state_coverage import (
    compute_pipeline_track,
    compute_research_coverage,
    compute_review_coverage,
    compute_summary,
)
from .state_issues import (
    compute_final_reviews,
    compute_issues,
)

router = APIRouter(tags=["state"])

STATE_SUMMARY_TTL_S = 60.0
STATE_PIPELINE_TTL_S = 60.0
STATE_RESEARCH_COVERAGE_TTL_S = 300.0
STATE_RESEARCH_DETAIL_TTL_S = 120.0
STATE_REVIEW_COVERAGE_TTL_S = 300.0
STATE_PIPELINE_VERSIONS_TTL_S = 60.0
STATE_WEAK_POINTS_TTL_S = 60.0
_PREPARATION_SELECTOR_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def _ctx_cache_key(ctx: MonitorContext, *parts: object) -> str:
    """Cache key scoped to one MonitorContext root (process-global TTL cache)."""
    return ctx_scoped_ttl_key(ctx, *parts)


def _isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _compute_pipeline_versions_payload(ctx: MonitorContext, track: str | None) -> dict[str, Any]:
    """Walk orchestration dirs and group modules by pipeline version."""
    counts = {"v6": 0, "v5": 0, "v3": 0, "unbuilt": 0}
    by_version: dict[str, list] = {"v6": [], "v5": [], "v3": [], "unbuilt": []}
    per_track: dict[str, dict] = {}

    level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

    for level_cfg in level_cfgs:
        track_id = level_cfg["id"]
        plan_slugs = get_plan_slugs(
            track_id, curriculum_root=ctx.roots.curriculum_root, plans_root=ctx.roots.plans_root
        )
        if not plan_slugs:
            continue

        track_dir = ctx.roots.curriculum_root / level_cfg["path"]
        track_counts = {"v6": 0, "v5": 0, "v3": 0, "unbuilt": 0}

        for num, slug in plan_slugs:
            orch_dir = safe_join(track_dir / "orchestration", slug)
            version = detect_pipeline_version(orch_dir)
            if version not in counts:
                version = "unbuilt"
            counts[version] += 1
            track_counts[version] += 1
            by_version[version].append({"track": track_id, "num": num, "slug": slug})

        per_track[track_id] = track_counts

    total = sum(counts.values())
    current_builds = counts["v6"]
    legacy_builds = counts["v5"] + counts["v3"]
    unbuilt_modules = counts["unbuilt"]
    rebuild_backlog = legacy_builds + unbuilt_modules
    built = current_builds + counts["v5"]
    return {
        "total": total,
        "counts": counts,
        "pct_v6": round(counts["v6"] / total * 100) if total else 0,
        "pct_v5": round(counts["v5"] / total * 100) if total else 0,
        "pct_current": round(current_builds / total * 100) if total else 0,
        "pct_built": round(built / total * 100) if total else 0,
        "current_builds": current_builds,
        "legacy_builds": legacy_builds,
        "unbuilt_modules": unbuilt_modules,
        "rebuild_backlog": rebuild_backlog,
        "build_state": {
            "current": current_builds,
            "legacy": legacy_builds,
            "unbuilt": unbuilt_modules,
            "backlog": rebuild_backlog,
        },
        "needs_rebuild": rebuild_backlog,
        "per_track": per_track,
        "v6_modules": by_version["v6"],
        "v5_modules": by_version["v5"],
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _compute_weak_points_payload(
    ctx: MonitorContext,
    track: str | None,
    min_score: int,
    limit: int,
) -> dict[str, Any]:
    """Scan modules for audit/research/word-count weakness."""
    weak = []
    level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

    for level_cfg in level_cfgs:
        track_id = level_cfg["id"]
        plan_slugs = get_plan_slugs(
            track_id, curriculum_root=ctx.roots.curriculum_root, plans_root=ctx.roots.plans_root
        )
        track_dir = ctx.roots.curriculum_root / level_cfg["path"]

        for num, slug in plan_slugs:
            issues = []
            audit = get_audit_status(track_dir, slug)

            if audit["status"] == "fail":
                issues.append("audit_fail")

            research_score = get_research_score(track_dir, slug, track_id)
            if research_score is not None and research_score < min_score:
                issues.append(f"research_score_{research_score}")

            word_count = audit.get("word_count", 0)
            word_target = audit.get("word_target", 0)
            if word_target == 0 and word_count > 0:
                word_target = get_word_target_from_plan(
                    track_id, slug, plans_root=ctx.roots.plans_root, curriculum_root=ctx.roots.curriculum_root
                )
            if word_target > 0 and word_count > 0 and word_count < word_target * 0.8:
                issues.append(f"low_words_{word_count}/{word_target}")

            if issues:
                orch_dir = safe_join(track_dir / "orchestration", slug)
                version = detect_pipeline_version(orch_dir)
                weak.append(
                    {
                        "track": track_id,
                        "num": num,
                        "slug": slug,
                        "audit_status": audit["status"],
                        "word_count": word_count,
                        "word_target": word_target,
                        "research_score": research_score,
                        "pipeline_version": version,
                        "issues": issues,
                    }
                )

    weak.sort(key=severity_key)
    return {"count": len(weak), "modules": weak[:limit]}


def warm_state_scans(ctx: MonitorContext) -> None:
    """Populate the default expensive curriculum state-scan caches after process start.

    Runs in the machinery state-scan warmup thread, after the routing-budget
    warm (``scripts.api.state_router.schedule_state_scan_warmup``).
    """
    try:
        cache_get_or_compute(
            _ctx_cache_key(ctx, "pipeline_versions", "all"),
            STATE_PIPELINE_VERSIONS_TTL_S,
            lambda: _compute_pipeline_versions_payload(ctx, None),
        )
        cache_get_or_compute(
            _ctx_cache_key(ctx, "weak_points", "all", 7, 20),
            STATE_WEAK_POINTS_TTL_S,
            lambda: _compute_weak_points_payload(ctx, None, 7, 20),
        )
        cache_get_or_compute(
            _ctx_cache_key(ctx, "summary"),
            STATE_SUMMARY_TTL_S,
            lambda: compute_summary(
                curriculum_root=ctx.roots.curriculum_root,
                project_root=ctx.roots.project_root,
                plans_root=ctx.roots.plans_root,
            ),
        )
        cache_get_or_compute(
            _ctx_cache_key(ctx, "research_coverage"),
            STATE_RESEARCH_COVERAGE_TTL_S,
            lambda: compute_research_coverage(
                curriculum_root=ctx.roots.curriculum_root,
                plans_root=ctx.roots.plans_root,
            ),
        )
    except Exception as exc:
        logging.getLogger("state_router").warning("State scan warmup failed: %s", exc)


def _validate_preparation_query(request: Request, allowed: set[str]) -> None:
    unknown = sorted(set(request.query_params) - allowed)
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={"code": "UNKNOWN_QUERY_PARAMETER", "parameters": unknown},
        )
    duplicates = sorted(key for key in allowed if len(request.query_params.getlist(key)) > 1)
    if duplicates:
        raise HTTPException(
            status_code=422,
            detail={"code": "DUPLICATE_QUERY_PARAMETER", "parameters": duplicates},
        )


def _validate_preparation_selector(value: str, label: str) -> None:
    if not _PREPARATION_SELECTOR_RE.fullmatch(value):
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_SELECTOR", "selector": label},
        )


def _preparation_response(request: Request, payload: dict[str, Any], *, status_code: int = 200) -> Response:
    body, etag_hex = preparation_state.response_document(payload)
    headers = {
        "ETag": f'"{etag_hex}"',
        "Cache-Control": "no-cache",
        "X-Source-Identity": payload["freshness"]["source_identity"],
    }
    if status_code == 200 and _matches_etag(request.headers.get("If-None-Match"), etag_hex):
        return Response(status_code=304, headers=headers)
    return Response(content=body, media_type="application/json", status_code=status_code, headers=headers)


def _with_state_meta(
    result: dict[str, Any],
    *,
    source: str,
    stale_after_s: float,
    cache: str,
    age_s: float | None = None,
) -> dict[str, Any]:
    """Attach freshness metadata without mutating the cached payload."""
    payload = dict(result)
    generated_at = str(payload.get("generated_at") or _isoformat_z(datetime.now(UTC)))
    meta: dict[str, Any] = {
        "generated_at": generated_at,
        "source": source,
        "cache": cache,
        "stale_after_s": stale_after_s,
        "stale": False,
    }
    if age_s is not None:
        meta["age_s"] = round(age_s, 3)
    payload["meta"] = meta
    return payload



@router.get("/summary")
async def state_summary(fresh: bool = Query(False), ctx: MonitorContext = Depends(get_ctx)):
    """Full project snapshot. One call replaces 5 bash scripts at session start."""
    cache_key = _ctx_cache_key(ctx, "summary")
    if fresh:
        cache_invalidate(cache_key)
    was_warm = (not fresh) and cache_get(cache_key, STATE_SUMMARY_TTL_S) is not None
    result = await cache_get_or_compute_async(
        cache_key,
        STATE_SUMMARY_TTL_S,
        lambda: compute_summary(
            curriculum_root=ctx.roots.curriculum_root,
            project_root=ctx.roots.project_root,
            plans_root=ctx.roots.plans_root,
        ),
        force=fresh,
    )
    aged = cache_get_with_age(cache_key, STATE_SUMMARY_TTL_S)
    return _with_state_meta(
        result,
        source="fs:plans+orchestration+artifacts+research",
        stale_after_s=STATE_SUMMARY_TTL_S,
        cache="hit" if was_warm else "miss",
        age_s=0.0 if aged is None else aged[1],
    )


@router.get("/pipeline/{track_id}")
async def pipeline_track(track_id: str, fresh: bool = Query(False), ctx: MonitorContext = Depends(get_ctx)):
    """Per-module pipeline state for one track."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = _ctx_cache_key(ctx, "pipeline", track_id)
    if fresh:
        cache_invalidate(cache_key)
    cached = cache_get_with_age(cache_key, ttl=STATE_PIPELINE_TTL_S)
    if cached is not None:
        value, age_s = cached
        return _with_state_meta(
            cast(dict[str, Any], value),
            source="fs:orchestration+audit+research",
            stale_after_s=STATE_PIPELINE_TTL_S,
            cache="hit",
            age_s=age_s,
        )
    result = await asyncio.to_thread(
        compute_pipeline_track,
        track_id,
        level_cfg,
        curriculum_root=ctx.roots.curriculum_root,
        project_root=ctx.roots.project_root,
        plans_root=ctx.roots.plans_root,
    )
    cache_set(cache_key, result)
    return _with_state_meta(
        result,
        source="fs:orchestration+audit+research",
        stale_after_s=STATE_PIPELINE_TTL_S,
        cache="miss",
        age_s=0.0,
    )


@router.get("/pipeline-versions")
async def pipeline_versions(
    track: str | None = Query(None), fresh: bool = Query(False), ctx: MonitorContext = Depends(get_ctx)
):
    """All modules grouped by pipeline version."""
    cache_key = _ctx_cache_key(ctx, "pipeline_versions", track or "all")
    was_warm = (not fresh) and cache_get(cache_key, STATE_PIPELINE_VERSIONS_TTL_S) is not None
    result = await cache_get_or_compute_async(
        cache_key,
        STATE_PIPELINE_VERSIONS_TTL_S,
        lambda: _compute_pipeline_versions_payload(ctx, track),
        force=fresh,
    )
    age_s = 0.0
    aged = cache_get_with_age(cache_key, STATE_PIPELINE_VERSIONS_TTL_S)
    if aged is not None:
        age_s = aged[1]
    return _with_state_meta(
        result,
        source="fs:orchestration",
        stale_after_s=STATE_PIPELINE_VERSIONS_TTL_S,
        cache="hit" if was_warm else "miss",
        age_s=age_s,
    )


@router.get("/preparation")
async def preparation_roster(
    request: Request,
    track: str | None = Query(None, min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$"),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Active-manifest learner bundle and publication state, without readiness sweeps."""
    _validate_preparation_query(request, {"track"})

    def _compute() -> dict[str, Any]:
        data_root = preparation_data_root(
            project_root=ctx.roots.project_root,
            live_repo_root=ctx.roots.live_repo_root,
        )
        authority = build_repository_authority(
            project_root=ctx.roots.project_root,
            live_repo_root=data_root,
        )
        return preparation_state.build_roster(
            repo_root=data_root,
            authority=authority,
            track=track,
        )

    try:
        payload = await asyncio.to_thread(_compute)
    except preparation_state.InactiveTrackError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INACTIVE_TRACK", "manifest_authority": "fallback-diagnostic-only"},
        ) from exc
    except preparation_state.UnknownTrackError as exc:
        raise HTTPException(status_code=404, detail={"code": "UNKNOWN_TRACK"}) from exc
    except (preparation_state.PreparationStateError, RepositoryAuthorityError) as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "PREPARATION_AUTHORITY_UNAVAILABLE"},
        ) from exc
    return _preparation_response(request, payload)


@router.get("/preparation/{track}/{slug}")
async def preparation_module(
    request: Request,
    track: str,
    slug: str,
    evidence: Literal["summary", "expanded"] = Query("summary"),
    ctx: MonitorContext = Depends(get_ctx),
):
    """One fail-closed canonical preparation decision plus orthogonal publication state."""
    _validate_preparation_query(request, {"evidence"})
    _validate_preparation_selector(track, "track")
    _validate_preparation_selector(slug, "slug")

    def _compute() -> dict[str, Any]:
        data_root = preparation_data_root(
            project_root=ctx.roots.project_root,
            live_repo_root=ctx.roots.live_repo_root,
        )
        authority = build_repository_authority(
            project_root=ctx.roots.project_root,
            live_repo_root=data_root,
        )
        return preparation_state.build_module_state(
            repo_root=data_root,
            authority=authority,
            track=track,
            slug=slug,
            expanded=evidence == "expanded",
        )

    try:
        payload = await asyncio.to_thread(_compute)
    except preparation_state.InactiveTrackError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INACTIVE_TRACK", "manifest_authority": "fallback-diagnostic-only"},
        ) from exc
    except preparation_state.UnknownTrackError as exc:
        raise HTTPException(status_code=404, detail={"code": "UNKNOWN_TRACK"}) from exc
    except (preparation_state.PreparationStateError, RepositoryAuthorityError) as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "PREPARATION_AUTHORITY_UNAVAILABLE"},
        ) from exc

    status_code = 404 if payload["manifest_authority"] == "off-manifest" else 200
    return _preparation_response(request, payload, status_code=status_code)


@router.get("/weak-points")
async def weak_points(
    track: str | None = Query(None),
    min_score: int = Query(7, ge=0, le=10),
    limit: int = Query(20, ge=1, le=500),
    fresh: bool = Query(False),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Modules with quality issues: failing audit, thin research, or low word count."""
    cache_key = _ctx_cache_key(ctx, "weak_points", track or "all", min_score, limit)
    return await cache_get_or_compute_async(
        cache_key,
        STATE_WEAK_POINTS_TTL_S,
        lambda: _compute_weak_points_payload(ctx, track, min_score, limit),
        force=fresh,
    )


@router.get("/failing")
async def failing_modules(track: str | None = Query(None), ctx: MonitorContext = Depends(get_ctx)):
    """All modules with audit failures or phase failures."""

    def _compute():
        failing = []
        level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

        for level_cfg in level_cfgs:
            track_id = level_cfg["id"]
            plan_slugs = get_plan_slugs(
                track_id, curriculum_root=ctx.roots.curriculum_root, plans_root=ctx.roots.plans_root
            )
            track_dir = ctx.roots.curriculum_root / level_cfg["path"]

            for num, slug in plan_slugs:
                orch_dir = safe_join(track_dir / "orchestration", slug)
                version = detect_pipeline_version(orch_dir)
                audit = get_audit_status(track_dir, slug)

                if version in ("v6", "v5"):
                    phases = read_v2_state(orch_dir).get("phases", {})
                    failed_phases = [
                        k for k, v in phases.items() if isinstance(v, dict) and v.get("status") == "failed"
                    ]
                elif version == "v3":
                    v3 = read_v3_state(orch_dir)
                    phases = v3.get("phases", {})
                    failed_phases = [
                        k.replace("v3-", "")
                        for k, v in phases.items()
                        if isinstance(v, dict) and v.get("status") == "failed"
                    ]
                else:
                    failed_phases = []

                if audit["status"] == "fail" or failed_phases:
                    failing.append(
                        {
                            "track": track_id,
                            "num": num,
                            "slug": slug,
                            "pipeline_version": version,
                            "audit_status": audit["status"],
                            "failed_phases": failed_phases,
                            "blocking_issues": audit.get("blocking_issues", []),
                        }
                    )

        return {"count": len(failing), "modules": failing}

    return await asyncio.to_thread(_compute)


def _read_llm_qg_scores(module_dir: Path) -> dict[str, Any]:
    """Read per-module LLM-QG aggregate + per-dimension scores from llm_qg.json.

    Returns ``{"aggregate": {...}|None, "dimensions": {dim: score}}``. Missing,
    unreadable, or malformed files degrade to ``aggregate=None`` / empty dims
    (a module may not have been QG-scored yet). The dimension map is read
    generically, so a newly-added dim (e.g. ``beauty`` once Phase A lands) is
    surfaced automatically with no change here.
    """
    level = module_dir.parent.name
    slug = module_dir.name
    data = monitor_surface.current_payload_for_module(level, slug, module_dir)
    path = module_dir / "llm_qg.json"
    if data is None:
        if not monitor_surface.llm_qg_file_is_current_for_module(module_dir, path):
            return {"aggregate": None, "dimensions": {}}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, ValueError):
            return {"aggregate": None, "dimensions": {}}
    if not isinstance(data, dict):
        return {"aggregate": None, "dimensions": {}}

    raw_agg = data.get("aggregate") if isinstance(data, dict) else None
    aggregate: dict[str, Any] | None = None
    if isinstance(raw_agg, dict):
        aggregate = {
            "verdict": raw_agg.get("verdict"),
            "terminal_verdict": raw_agg.get("terminal_verdict"),
            "min_score": raw_agg.get("min_score"),
            "min_dim": raw_agg.get("min_dim"),
            "failing_dims": raw_agg.get("failing_dims", []),
            "warning_dims": raw_agg.get("warning_dims", []),
        }

    raw_dims = data.get("dimensions") if isinstance(data, dict) else None
    dimensions: dict[str, Any] = {}
    if isinstance(raw_dims, dict):
        for dim, entry in raw_dims.items():
            if isinstance(entry, dict) and "score" in entry:
                dimensions[dim] = entry.get("score")
    return {"aggregate": aggregate, "dimensions": dimensions}


def _module_score_record(track_id: str, track_dir: Path, num: int, slug: str) -> dict[str, Any]:
    """Assemble one module's status + LLM-QG score record."""
    audit = get_audit_status(track_dir, slug)
    scores = _read_llm_qg_scores(safe_join(track_dir, slug))
    return {
        "track": track_id,
        "num": num,
        "slug": slug,
        "status": audit.get("status"),
        "word_count": audit.get("word_count"),
        "word_target": audit.get("word_target"),
        "scored": scores["aggregate"] is not None,
        "aggregate": scores["aggregate"],
        "dimensions": scores["dimensions"],
    }


@router.get("/scores/{track}")
async def module_scores(track: str, ctx: MonitorContext = Depends(get_ctx)):
    """Per-module status + LLM-QG aggregate + per-dimension scores for a track.

    The view the user watches the seminar quality-gate prototype converge with
    (docs/folk-epic/seminar-quality-gate-design.md). Source of truth:
    ``curriculum/l2-uk-en/<track>/<slug>/llm_qg.json`` (``.aggregate`` +
    ``.dimensions``) plus the audit status cache. Always fresh (small reads, no
    cache) so polling during a build reflects the latest round.
    """

    def _compute() -> dict[str, Any] | None:
        level_cfg = next((l for l in LEVELS if l["id"] == track), None)
        if not level_cfg:
            return None
        track_dir = ctx.roots.curriculum_root / level_cfg["path"]
        plan_slugs = get_plan_slugs(track, curriculum_root=ctx.roots.curriculum_root, plans_root=ctx.roots.plans_root)
        modules = [_module_score_record(track, track_dir, num, slug) for num, slug in plan_slugs]
        scored = sum(1 for m in modules if m["scored"])
        return {"track": track, "count": len(modules), "scored": scored, "modules": modules}

    result = await asyncio.to_thread(_compute)
    if result is None:
        return JSONResponse(status_code=404, content={"error": f"Track '{track}' not found"})
    return _with_state_meta(result, source="fs:llm_qg+status", stale_after_s=0.0, cache="miss", age_s=0.0)


@router.get("/scores/{track}/{slug}")
async def module_scores_one(track: str, slug: str, ctx: MonitorContext = Depends(get_ctx)):
    """One module's status + LLM-QG aggregate + per-dimension scores."""

    def _compute() -> dict[str, Any] | None:
        level_cfg = next((l for l in LEVELS if l["id"] == track), None)
        if not level_cfg:
            return None
        track_dir = ctx.roots.curriculum_root / level_cfg["path"]
        plan_slugs = get_plan_slugs(track, curriculum_root=ctx.roots.curriculum_root, plans_root=ctx.roots.plans_root)
        match = next((ns for ns in plan_slugs if ns[1] == slug), None)
        if match is None:
            return {"__not_found__": "slug"}
        num, resolved_slug = match
        return _module_score_record(track, track_dir, num, resolved_slug)

    result = await asyncio.to_thread(_compute)
    if result is None:
        return JSONResponse(status_code=404, content={"error": f"Track '{track}' not found"})
    if result.get("__not_found__"):
        return JSONResponse(status_code=404, content={"error": f"Module '{slug}' not found in track '{track}'"})
    return _with_state_meta(result, source="fs:llm_qg+status", stale_after_s=0.0, cache="miss", age_s=0.0)


@router.get("/research-coverage")
async def research_coverage(fresh: bool = Query(False), ctx: MonitorContext = Depends(get_ctx)):
    """Per-track research completeness and quality."""
    cache_key = _ctx_cache_key(ctx, "research_coverage")
    if fresh:
        cache_invalidate(cache_key)
    was_warm = (not fresh) and cache_get(cache_key, STATE_RESEARCH_COVERAGE_TTL_S) is not None
    result = await cache_get_or_compute_async(
        cache_key,
        STATE_RESEARCH_COVERAGE_TTL_S,
        lambda: compute_research_coverage(
            curriculum_root=ctx.roots.curriculum_root,
            plans_root=ctx.roots.plans_root,
        ),
        force=fresh,
    )
    aged = cache_get_with_age(cache_key, STATE_RESEARCH_COVERAGE_TTL_S)
    return _with_state_meta(
        result,
        source="fs:research+dossiers",
        stale_after_s=STATE_RESEARCH_COVERAGE_TTL_S,
        cache="hit" if was_warm else "miss",
        age_s=0.0 if aged is None else aged[1],
    )


@router.get("/research/{track_id}")
async def research_detail(
    track_id: str, min_score: int = 9, fresh: bool = Query(False), ctx: MonitorContext = Depends(get_ctx)
):
    """Per-module research quality with dimension scores, gaps, and upgrade queue."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = _ctx_cache_key(ctx, "research_detail", track_id, min_score)
    if fresh:
        cache_invalidate(cache_key)
    cached = cache_get_with_age(cache_key, ttl=STATE_RESEARCH_DETAIL_TTL_S)
    if cached is not None:
        value, age_s = cached
        return _with_state_meta(
            cast(dict[str, Any], value),
            source="fs:research+dossiers",
            stale_after_s=STATE_RESEARCH_DETAIL_TTL_S,
            cache="hit",
            age_s=age_s,
        )

    result = await asyncio.to_thread(
        compute_research_detail,
        track_id,
        level_cfg,
        min_score,
        curriculum_root=ctx.roots.curriculum_root,
        plans_root=ctx.roots.plans_root,
    )
    cache_set(cache_key, result)
    return _with_state_meta(
        result,
        source="fs:research+dossiers",
        stale_after_s=STATE_RESEARCH_DETAIL_TTL_S,
        cache="miss",
        age_s=0.0,
    )


@router.get("/review-coverage")
async def review_coverage(fresh: bool = Query(False), ctx: MonitorContext = Depends(get_ctx)):
    """Per-track review and final-review coverage + quality signal."""
    cache_key = _ctx_cache_key(ctx, "review_coverage")
    if fresh:
        cache_invalidate(cache_key)
    cached = cache_get_with_age(cache_key, ttl=STATE_REVIEW_COVERAGE_TTL_S)
    if cached is not None:
        value, age_s = cached
        return _with_state_meta(
            cast(dict[str, Any], value),
            source="fs:review+audit",
            stale_after_s=STATE_REVIEW_COVERAGE_TTL_S,
            cache="hit",
            age_s=age_s,
        )
    result = await asyncio.to_thread(
        compute_review_coverage,
        curriculum_root=ctx.roots.curriculum_root,
        plans_root=ctx.roots.plans_root,
    )
    cache_set(cache_key, result)
    return _with_state_meta(
        result,
        source="fs:review+audit",
        stale_after_s=STATE_REVIEW_COVERAGE_TTL_S,
        cache="miss",
        age_s=0.0,
    )


@router.get("/build-status/{track_id}")
async def build_status(track_id: str, ctx: MonitorContext = Depends(get_ctx)):
    """Compact build progress for a track."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = _ctx_cache_key(ctx, "build_status", track_id)
    cached = cache_get(cache_key, ttl=15.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(
        compute_build_status_track,
        track_id,
        level_cfg,
        curriculum_root=ctx.roots.curriculum_root,
        plans_root=ctx.roots.plans_root,
    )
    cache_set(cache_key, result)
    return result


@router.get("/build-status")
async def build_status_all(ctx: MonitorContext = Depends(get_ctx)):
    """All-tracks build progress in one call."""
    cache_key = _ctx_cache_key(ctx, "build_status_all")
    cached = cache_get(cache_key, ttl=30.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(
        compute_build_status_all,
        curriculum_root=ctx.roots.curriculum_root,
        plans_root=ctx.roots.plans_root,
    )
    cache_set(cache_key, result)
    return result


@router.get("/module-range/{track_id}")
async def module_range_status(
    track_id: str,
    start: int = Query(..., ge=1),
    end: int = Query(..., ge=1),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Deterministic committed-file status for a module number range."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})
    if end < start:
        return JSONResponse(
            status_code=422,
            content={"error": "end must be greater than or equal to start"},
        )
    cache_key = _ctx_cache_key(ctx, "module_range", track_id, start, end)
    cached = cache_get(cache_key, ttl=30.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(
        compute_module_range_status,
        track_id,
        level_cfg,
        start=start,
        end=end,
        curriculum_root=ctx.roots.curriculum_root,
        project_root=ctx.roots.project_root,
        plans_root=ctx.roots.plans_root,
    )
    cache_set(cache_key, result)
    return result


@router.get("/llm-qg/{track_id}")
async def llm_qg_track(
    track_id: str,
    verbose: bool = Query(
        False,
        description="True = include full dimension evidence. Default returns score-only dimensions.",
    ),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Per-module LLM quality-gate scores from build artifacts on disk."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    return await asyncio.to_thread(
        compute_llm_qg_track,
        track_id,
        level_cfg,
        verbose=verbose,
        curriculum_root=ctx.roots.curriculum_root,
        plans_root=ctx.roots.plans_root,
    )


@router.get("/build-stats")
async def build_stats_all(ctx: MonitorContext = Depends(get_ctx)):
    """V6 build stats aggregated across all tracks."""
    return await asyncio.to_thread(compute_build_stats_all, curriculum_root=ctx.roots.curriculum_root)


@router.get("/build-stats/{track_id}")
async def build_stats(track_id: str, ctx: MonitorContext = Depends(get_ctx)):
    """V6 build-stats.jsonl parsed: attempts, success rate, recent entries."""
    return await asyncio.to_thread(compute_build_stats, track_id, curriculum_root=ctx.roots.curriculum_root)


@router.get("/module/{track_id}/{num}")
async def module_detail(track_id: str, num: int, ctx: MonitorContext = Depends(get_ctx)):
    """Single module deep-dive: pipeline state, audit, research, review, comms."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    result = await asyncio.to_thread(
        compute_module_detail,
        track_id,
        num,
        level_cfg,
        curriculum_root=ctx.roots.curriculum_root,
        plans_root=ctx.roots.plans_root,
        message_db=ctx.stores.message_db,
    )
    if "error" in result:
        return JSONResponse(status_code=404, content=result)
    return result


@router.get("/module/{track_id}/slug/{slug}")
async def module_detail_by_slug(
    track_id: str,
    slug: str,
    verbose: bool = Query(
        False,
        description="True = full compute_module_detail payload. Default returns a compact view.",
    ),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Slug-keyed module state (#1313 / Codex-1).

    Same data as ``/api/state/module/{track_id}/{num}`` but keyed by
    slug (the stable identifier agents actually use) and returning a
    compact default shape so cold-start / "what's the state of this
    module right now" calls don't pay for the full dump.

    Pass ``?verbose=true`` to get the original rich payload.

    Compact shape::
        {
          "track": "a1", "slug": "...", "num": 3,
          "phase":            "review",   # current or last-complete phase name
          "last_successful":  "review",   # last phase whose status was complete
          "pipeline_version": "v6",
          "needs_rebuild":    false,
          "audit":  {"status": "pass", "word_count": ..., "word_target": ...},
          "review": {"score": 9.4, "verdict": "PASS"},
          "final_review": {"exists": true, "verdict": "PASS"} | null,
          "blocking_issues":  [...],
          "retry_count":      0,
          "worker":           "gemini"
        }
    """
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(
            status_code=404,
            content={"error": f"Track '{track_id}' not found"},
        )

    plan_slugs = get_plan_slugs(track_id, curriculum_root=ctx.roots.curriculum_root, plans_root=ctx.roots.plans_root)
    match = next(((n, s) for n, s in plan_slugs if s == slug), None)
    if not match:
        return JSONResponse(
            status_code=404,
            content={"error": f"Module '{slug}' not found in track '{track_id}'"},
        )
    num, _ = match

    full = await asyncio.to_thread(
        compute_module_detail,
        track_id,
        num,
        level_cfg,
        curriculum_root=ctx.roots.curriculum_root,
        plans_root=ctx.roots.plans_root,
        message_db=ctx.stores.message_db,
    )
    if "error" in full:
        return JSONResponse(status_code=404, content=full)

    if verbose:
        return full

    # --- compact projection -------------------------------------------
    phases = full.get("phases") or {}
    current_phase = None
    last_successful = None
    retry_count = 0
    current_worker = None
    for name, data in phases.items():
        if not isinstance(data, dict):
            continue
        status = data.get("status")
        if status == "in_progress":
            current_phase = name
        if status == "complete":
            last_successful = name
        # attempts / retry_count key varies by pipeline version; surface
        # whatever the phase payload carries so consumers don't have to.
        for key in ("retries", "retry_count", "attempts"):
            val = data.get(key)
            if isinstance(val, int):
                retry_count = max(retry_count, val)
        if status == "in_progress":
            exec_ = cast(dict[str, Any], data.get("executor")) if isinstance(data.get("executor"), dict) else {}
            current_worker = exec_.get("agent")

    audit = full.get("audit") or {}
    review = full.get("review") or {}
    final_review = full.get("final_review")
    track_dir = ctx.roots.curriculum_root / level_cfg["path"]
    llm_qg = await asyncio.to_thread(read_llm_qg, track_dir, slug)

    return {
        "track": track_id,
        "slug": slug,
        "num": num,
        "phase": current_phase or last_successful or "pending",
        "last_successful": last_successful,
        "pipeline_version": full.get("pipeline_version"),
        "needs_rebuild": full.get("needs_rebuild"),
        "audit": {
            "status": audit.get("status"),
            "word_count": audit.get("word_count"),
            "word_target": audit.get("word_target"),
        },
        "review": {
            "score": review.get("score") if isinstance(review, dict) else None,
            "verdict": review.get("verdict") if isinstance(review, dict) else None,
        },
        "final_review": (
            {"exists": final_review.get("exists"), "verdict": final_review.get("verdict")}
            if isinstance(final_review, dict) and final_review.get("exists")
            else None
        ),
        "blocking_issues": audit.get("blocking_issues") or [],
        "retry_count": retry_count,
        "worker": current_worker,
        "llm_qg": summarize_llm_qg(llm_qg),
    }


@router.get("/final-reviews/{track_id}")
async def final_reviews_track(track_id: str, ctx: MonitorContext = Depends(get_ctx)):
    """Phase F results aggregated per track: verdicts, issue counts, common patterns."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = _ctx_cache_key(ctx, "final_reviews", track_id)
    cached = cache_get(cache_key, ttl=60.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(
        compute_final_reviews,
        track_id,
        level_cfg,
        curriculum_root=ctx.roots.curriculum_root,
        plans_root=ctx.roots.plans_root,
    )
    cache_set(cache_key, result)
    return result


@router.get("/enrichment-status")
async def enrichment_status(track: str | None = Query(None), ctx: MonitorContext = Depends(get_ctx)):
    """Which plans are enriched per track."""
    cache_key = _ctx_cache_key(ctx, "enrichment_status", track or "all")
    cached = cache_get(cache_key, ttl=120.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(
        compute_enrichment_status,
        track,
        curriculum_root=ctx.roots.curriculum_root,
        plans_root=ctx.roots.plans_root,
    )
    cache_set(cache_key, result)
    return result


@router.get("/track-health/{track_id}")
async def track_health(track_id: str, ctx: MonitorContext = Depends(get_ctx)):
    """Single-call track health summary."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = _ctx_cache_key(ctx, "track_health", track_id)
    cached = cache_get(cache_key, ttl=30.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(
        compute_track_health,
        track_id,
        level_cfg,
        curriculum_root=ctx.roots.curriculum_root,
        plans_root=ctx.roots.plans_root,
        project_root=ctx.roots.project_root,
        git_root=ctx.roots.live_repo_root,
    )
    cache_set(cache_key, result)
    return result


@router.get("/issues")
async def outstanding_issues(
    track: str | None = Query(None),
    severity: str | None = Query(None),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Aggregated outstanding issues from review files + audit failures."""
    return await asyncio.to_thread(
        compute_issues,
        track,
        severity,
        curriculum_root=ctx.roots.curriculum_root,
        plans_root=ctx.roots.plans_root,
    )


# ==================== RANGE STATUS (#1313 / Codex-4) ====================


@router.get("/range/{track_id}")
async def range_status(
    track_id: str,
    start: int = Query(1, ge=1, description="First module number (inclusive)."),
    end: int | None = Query(
        None,
        description="Last module number (inclusive). Omit to go to the end of the track.",
    ),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Compact per-module table for one [start, end] slice of a track.

    Designed for overnight batch runs: one call tells you exactly
    which module is in which phase, whether it's blocked, current
    review score, and which worker is assigned. Builds on
    ``compute_pipeline_track`` so the data source is shared with the
    existing ``/api/state/pipeline/{track}`` endpoint — just slice
    + flatten (reviewer Codex-4 / #1313).
    """
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(
            status_code=404,
            content={"error": f"Track '{track_id}' not found"},
        )

    def _compute() -> dict:
        full = compute_pipeline_track(
            track_id,
            level_cfg,
            curriculum_root=ctx.roots.curriculum_root,
            project_root=ctx.roots.project_root,
            plans_root=ctx.roots.plans_root,
        )
        modules = full.get("modules", []) if isinstance(full, dict) else full
        if not isinstance(modules, list):
            return {"error": "pipeline_track returned non-list"}

        sliced = [
            m
            for m in modules
            if isinstance(m, dict)
            and isinstance(m.get("num"), int)
            and m["num"] >= start
            and (end is None or m["num"] <= end)
        ]

        compact = []
        for m in sliced:
            phases = m.get("phases") or {}
            # "current phase" = last phase whose status is in_progress or
            # the last completed phase (whichever is latest). Keeps the
            # compact view actionable without a separate call.
            current = None
            last_complete = None
            failed_phase = None
            for name, data in phases.items():
                if not isinstance(data, dict):
                    continue
                status = data.get("status")
                if status == "in_progress":
                    current = name
                if status == "complete":
                    last_complete = name
                if status == "failed":
                    failed_phase = name
            phase_now = current or failed_phase or last_complete or "pending"

            review = m.get("review") or {}
            audit = m.get("audit")

            # ``compute_pipeline_track`` does NOT emit a ``blocker``
            # field (reviewer Codex BLOCKER on #1312 pre-merge:
            # previously this was always null and documented as
            # "whether a module is blocked"). Derive it here so the
            # compact dashboard actually answers the stated question:
            #   - a failed phase name — the pipeline gave up at that step
            #   - "audit_fail" — audit ran but produced a fail verdict
            #   - first blocking_issues[*].gate name — specific gate
            #   - null — nothing known to be blocking
            blocker: str | None = None
            if failed_phase:
                blocker = f"failed:{failed_phase}"
            elif isinstance(audit, str) and audit.lower() == "fail":
                blocker = "audit_fail"
            blocking_issues = m.get("blocking_issues") or []
            if blocker is None and blocking_issues:
                first = blocking_issues[0]
                if isinstance(first, dict):
                    gate = first.get("gate") or first.get("type")
                    blocker = f"gate:{gate}" if gate else "audit_issue"

            compact.append(
                {
                    "num": m["num"],
                    "slug": m.get("slug"),
                    "phase": phase_now,
                    "phase_status": (
                        phases.get(phase_now, {}).get("status") if isinstance(phases.get(phase_now), dict) else None
                    ),
                    "worker": (
                        phases.get(phase_now, {}).get("executor", {}).get("agent")
                        if isinstance(phases.get(phase_now), dict)
                        and isinstance(phases.get(phase_now, {}).get("executor"), dict)
                        else None
                    ),
                    "audit": audit,
                    "review_score": (review.get("score") if isinstance(review, dict) else None),
                    "words": m.get("words"),
                    "word_target": m.get("word_target"),
                    "blocker": blocker,
                    "pipeline_version": m.get("pipeline_version"),
                    "needs_rebuild": m.get("needs_rebuild"),
                }
            )

        return {
            "track": track_id,
            "start": start,
            "end": end,
            "count": len(compact),
            "modules": compact,
        }

    return await asyncio.to_thread(_compute)
