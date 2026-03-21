"""State API router -- v3/v4/v5 pipeline state, research/review coverage, weak points, issues.

Mounted at /api/state/ in main.py.

Endpoints:
  GET /api/state/summary              Full project snapshot
  GET /api/state/pipeline/{track}     Per-module v3/v4/v5 phase state for one track
  GET /api/state/ready-to-build       Phase A done, Phase B not started
  GET /api/state/weak-points          Modules with quality issues
  GET /api/state/build-status/{track}  Compact live build progress (one call)
  GET /api/state/build-status          All-tracks build progress summary
  GET /api/state/module/{track}/{num}  Single module deep-dive with comms
  GET /api/state/final-reviews/{track} Phase F results aggregated per track
  GET /api/state/failing              Modules with audit/phase failures
  GET /api/state/research-coverage    Per-track research completeness
  GET /api/state/research/{track}    Per-module research quality + dimensions + upgrade queue
  GET /api/state/review-coverage      Per-track review completeness + quality
  GET /api/state/issues               Aggregated outstanding issues

Performance notes:
  - Heavy endpoints run their sync I/O in asyncio.to_thread().
  - Results are cached in-memory with a TTL (60s for summary/pipeline, 300s for coverage).
"""

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from .config import CURRICULUM_ROOT, LEVELS
from .state_build import (
    compute_build_stats,
    compute_build_status_all,
    compute_build_status_track,
    compute_enrichment_status,
    compute_track_health,
)
from .state_compute import (
    compute_module_detail,
    compute_research_detail,
    severity_key,
)
from .state_coverage import (
    compute_pipeline_track,
    compute_research_coverage,
    compute_review_coverage,
    compute_summary,
)
from .state_helpers import (
    cache_get,
    cache_set,
    detect_pipeline_version,
    get_audit_status,
    get_plan_slugs,
    get_research_score,
    get_word_target_from_plan,
    is_content_done,
    is_research_done,
    load_module_state,
    parse_v4_phase_status,
    read_v2_state,
    read_v3_state,
    read_v4_state,
)
from .state_issues import (
    compute_final_reviews,
    compute_issues,
)

# Re-export symbols used by dashboard_router and tests (backward compat)
_detect_pipeline_version = detect_pipeline_version
_parse_v4_phase_status = parse_v4_phase_status
_read_v4_state = read_v4_state
_is_research_done = is_research_done
_is_content_done = is_content_done

router = APIRouter(tags=["state"])


# ==================== ENDPOINTS ====================


@router.get("/summary")
async def state_summary():
    """Full project snapshot. One call replaces 5 bash scripts at session start."""
    cached = cache_get("summary", ttl=60.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(compute_summary)
    cache_set("summary", result)
    return result


@router.get("/pipeline/{track_id}")
async def pipeline_track(track_id: str):
    """Per-module v5/v4/v3 phase state for one track."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = f"pipeline_{track_id}"
    cached = cache_get(cache_key, ttl=60.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(compute_pipeline_track, track_id, level_cfg)
    cache_set(cache_key, result)
    return result


@router.get("/pipeline-versions")
async def pipeline_versions(track: str | None = Query(None)):
    """All modules grouped by pipeline version."""
    def _compute():
        counts = {"v6": 0, "v5": 0, "v4": 0, "v3": 0, "unbuilt": 0}
        by_version: dict[str, list] = {"v6": [], "v5": [], "v4": [], "v3": [], "unbuilt": []}
        per_track: dict[str, dict] = {}

        level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

        for level_cfg in level_cfgs:
            track_id = level_cfg["id"]
            plan_slugs = get_plan_slugs(track_id)
            if not plan_slugs:
                continue

            track_dir = CURRICULUM_ROOT / level_cfg["path"]
            track_counts = {"v6": 0, "v5": 0, "v4": 0, "v3": 0, "unbuilt": 0}

            for num, slug in plan_slugs:
                orch_dir = track_dir / "orchestration" / slug
                version = detect_pipeline_version(orch_dir)
                counts[version] += 1
                track_counts[version] += 1
                by_version[version].append({"track": track_id, "num": num, "slug": slug})

            per_track[track_id] = track_counts

        total = sum(counts.values())
        built = counts["v6"] + counts["v5"] + counts["v4"]
        return {
            "total": total, "counts": counts,
            "pct_v6": round(counts["v6"] / total * 100) if total else 0,
            "pct_v5": round(counts["v5"] / total * 100) if total else 0,
            "pct_built": round(built / total * 100) if total else 0,
            "needs_rebuild": counts["v3"] + counts["unbuilt"],
            "per_track": per_track,
            "v6_modules": by_version["v6"],
            "v5_modules": by_version["v5"],
            "v4_modules": by_version["v4"],
            "generated_at": datetime.now(UTC).isoformat(),
        }

    cache_key = f"pipeline_versions_{track or 'all'}"
    cached = cache_get(cache_key, ttl=60.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute)
    cache_set(cache_key, result)
    return result


@router.get("/ready-to-build")
async def ready_to_build(track: str | None = Query(None)):
    """Modules where Phase A is complete but Phase B hasn't started."""
    def _compute():
        ready = []
        level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

        for level_cfg in level_cfgs:
            track_id = level_cfg["id"]
            plan_slugs = get_plan_slugs(track_id)
            track_dir = CURRICULUM_ROOT / level_cfg["path"]

            for num, slug in plan_slugs:
                orch_dir = track_dir / "orchestration" / slug
                state = load_module_state(track_id, slug, orch_dir)

                if is_research_done(state, track_dir, slug) and not is_content_done(state):
                    version = detect_pipeline_version(orch_dir)
                    research_phase = state.get("phases", {}).get("research", {})
                    ready.append({
                        "track": track_id, "num": num, "slug": slug,
                        "pipeline_version": version,
                        "phase_a_ts": research_phase.get("ts"),
                        "phase_a_mode": research_phase.get("mode"),
                    })
        return {"count": len(ready), "modules": ready}

    return await asyncio.to_thread(_compute)


@router.get("/weak-points")
async def weak_points(
    track: str | None = Query(None),
    min_score: int = Query(7, ge=0, le=10),
    limit: int = Query(20, ge=1, le=500),
):
    """Modules with quality issues: failing audit, thin research, or low word count."""
    def _compute():
        weak = []
        level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

        for level_cfg in level_cfgs:
            track_id = level_cfg["id"]
            plan_slugs = get_plan_slugs(track_id)
            track_dir = CURRICULUM_ROOT / level_cfg["path"]

            for num, slug in plan_slugs:
                issues = []
                audit = get_audit_status(track_dir, slug)

                if audit["status"] == "fail":
                    issues.append("audit_fail")

                research_score = get_research_score(track_dir, slug, track_id) if track else None
                if research_score is not None and research_score < min_score:
                    issues.append(f"research_score_{research_score}")

                word_count = audit.get("word_count", 0)
                word_target = audit.get("word_target", 0)
                if word_target == 0:
                    word_target = get_word_target_from_plan(track_id, slug)
                if word_target > 0 and word_count > 0 and word_count < word_target * 0.8:
                    issues.append(f"low_words_{word_count}/{word_target}")

                if issues:
                    orch_dir = track_dir / "orchestration" / slug
                    version = detect_pipeline_version(orch_dir)
                    weak.append({
                        "track": track_id, "num": num, "slug": slug,
                        "audit_status": audit["status"],
                        "word_count": word_count, "word_target": word_target,
                        "research_score": research_score,
                        "pipeline_version": version, "issues": issues,
                    })

        weak.sort(key=severity_key)
        return {"count": len(weak), "modules": weak[:limit]}

    return await asyncio.to_thread(_compute)


@router.get("/failing")
async def failing_modules(track: str | None = Query(None)):
    """All modules with audit failures or phase failures."""
    def _compute():
        failing = []
        level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

        for level_cfg in level_cfgs:
            track_id = level_cfg["id"]
            plan_slugs = get_plan_slugs(track_id)
            track_dir = CURRICULUM_ROOT / level_cfg["path"]

            for num, slug in plan_slugs:
                orch_dir = track_dir / "orchestration" / slug
                version = detect_pipeline_version(orch_dir)
                audit = get_audit_status(track_dir, slug)

                if version in ("v6", "v5"):
                    phases = read_v2_state(orch_dir).get("phases", {})
                    failed_phases = [
                        k for k, v in phases.items()
                        if isinstance(v, dict) and v.get("status") == "failed"
                    ]
                elif version == "v4":
                    v4 = read_v4_state(orch_dir)
                    phases = v4.get("phases", {})
                    failed_phases = [
                        k.replace("v4-", "") for k, v in phases.items()
                        if isinstance(v, dict) and v.get("status") == "failed"
                    ]
                else:
                    v3 = read_v3_state(orch_dir)
                    phases = v3.get("phases", {})
                    failed_phases = [
                        k.replace("v3-", "") for k, v in phases.items()
                        if isinstance(v, dict) and v.get("status") == "failed"
                    ]

                if audit["status"] == "fail" or failed_phases:
                    failing.append({
                        "track": track_id, "num": num, "slug": slug,
                        "pipeline_version": version, "audit_status": audit["status"],
                        "failed_phases": failed_phases,
                        "blocking_issues": audit.get("blocking_issues", []),
                    })

        return {"count": len(failing), "modules": failing}

    return await asyncio.to_thread(_compute)


@router.get("/research-coverage")
async def research_coverage():
    """Per-track research completeness and quality."""
    cached = cache_get("research_coverage", ttl=300.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(compute_research_coverage)
    cache_set("research_coverage", result)
    return result


@router.get("/research/{track_id}")
async def research_detail(track_id: str, min_score: int = 9):
    """Per-module research quality with dimension scores, gaps, and upgrade queue."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = f"research_detail_{track_id}_{min_score}"
    cached = cache_get(cache_key, ttl=120.0)
    if cached is not None:
        return cached

    result = await asyncio.to_thread(compute_research_detail, track_id, level_cfg, min_score)
    cache_set(cache_key, result)
    return result


@router.get("/review-coverage")
async def review_coverage():
    """Per-track review and final-review coverage + quality signal."""
    cached = cache_get("review_coverage", ttl=300.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(compute_review_coverage)
    cache_set("review_coverage", result)
    return result


@router.get("/build-status/{track_id}")
async def build_status(track_id: str):
    """Compact build progress for a track."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = f"build_status_{track_id}"
    cached = cache_get(cache_key, ttl=15.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(compute_build_status_track, track_id, level_cfg)
    cache_set(cache_key, result)
    return result


@router.get("/build-status")
async def build_status_all():
    """All-tracks build progress in one call."""
    cached = cache_get("build_status_all", ttl=30.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(compute_build_status_all)
    cache_set("build_status_all", result)
    return result


@router.get("/build-stats")
async def build_stats_all():
    """V6 build stats aggregated across all tracks."""
    from .state_build import compute_build_stats_all
    return await asyncio.to_thread(compute_build_stats_all)


@router.get("/build-stats/{track_id}")
async def build_stats(track_id: str):
    """V6 build-stats.jsonl parsed: attempts, success rate, recent entries."""
    return await asyncio.to_thread(compute_build_stats, track_id)


@router.get("/module/{track_id}/{num}")
async def module_detail(track_id: str, num: int):
    """Single module deep-dive: pipeline state, audit, research, review, comms."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    result = await asyncio.to_thread(compute_module_detail, track_id, num, level_cfg)
    if "error" in result:
        return JSONResponse(status_code=404, content=result)
    return result


@router.get("/final-reviews/{track_id}")
async def final_reviews_track(track_id: str):
    """Phase F results aggregated per track: verdicts, issue counts, common patterns."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = f"final_reviews_{track_id}"
    cached = cache_get(cache_key, ttl=60.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(compute_final_reviews, track_id, level_cfg)
    cache_set(cache_key, result)
    return result


@router.get("/enrichment-status")
async def enrichment_status(track: str | None = Query(None)):
    """Which plans are enriched per track."""
    cached = cache_get("enrichment_status", ttl=120.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(compute_enrichment_status, track)
    cache_set("enrichment_status", result)
    return result


@router.get("/track-health/{track_id}")
async def track_health(track_id: str):
    """Single-call track health summary."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = f"track_health_{track_id}"
    cached = cache_get(cache_key, ttl=30.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(compute_track_health, track_id, level_cfg)
    cache_set(cache_key, result)
    return result


@router.get("/issues")
async def outstanding_issues(
    track: str | None = Query(None),
    severity: str | None = Query(None),
):
    """Aggregated outstanding issues from review files + audit failures."""
    return await asyncio.to_thread(compute_issues, track, severity)
