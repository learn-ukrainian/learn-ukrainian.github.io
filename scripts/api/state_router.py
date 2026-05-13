"""State API router -- v6 pipeline state, research/review coverage, weak points, issues.

Mounted at /api/state/ in main.py.

Endpoints:
  GET /api/state/summary              Full project snapshot
  GET /api/state/pipeline/{track}     Per-module pipeline state for one track
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
  GET /api/state/routing-budget       Per-agent capacity burn + routing recommendation

Performance notes:
  - Heavy endpoints run their sync I/O in asyncio.to_thread().
  - Results are cached in-memory with a TTL (60s for summary/pipeline, 300s for coverage).
"""

import asyncio
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from scripts.analytics.cost_report import CostRecord, load_cost_records

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)

from . import delegate_router as delegate_api
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
    read_v2_state,
    read_v3_state,
)
from .state_issues import (
    compute_final_reviews,
    compute_issues,
)

# Re-export symbols used by dashboard_router and tests (backward compat)
_detect_pipeline_version = detect_pipeline_version
_is_research_done = is_research_done
_is_content_done = is_content_done

router = APIRouter(tags=["state"])

BUDGET_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "agent_budgets.yaml"
AGENT_NAMES = ("claude", "codex", "gemini")


def _isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_iso_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _load_agent_budgets() -> tuple[dict[str, Any], list[str]]:
    try:
        loaded = yaml.safe_load(BUDGET_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        return {}, [f"budget config unavailable: {type(exc).__name__}"]
    if not isinstance(loaded, dict):
        return {}, ["budget config unavailable: root is not a mapping"]
    return loaded, []


def _agent_key(raw_agent: str | None) -> str | None:
    agent = (raw_agent or "").lower().strip()
    for name in AGENT_NAMES:
        if agent == name or agent.startswith(f"{name} ") or agent.startswith(f"{name}("):
            return name
    return None


def _record_has_cost(record: CostRecord) -> bool:
    return (
        float(getattr(record, "cost_usd_est", 0.0) or 0.0) > 0
        or int(getattr(record, "prompt_tokens_est", 0) or 0) > 0
        or int(getattr(record, "response_tokens_est", 0) or 0) > 0
    )


def _sum_agent_spend(
    records: list[CostRecord],
    *,
    agent: str,
    since: datetime,
) -> tuple[float, int]:
    spent = 0.0
    missing = 0
    for record in records:
        if _agent_key(getattr(record, "agent", None)) != agent:
            continue
        if getattr(record, "mtime", datetime.min.replace(tzinfo=UTC)) < since:
            continue
        if not _record_has_cost(record):
            missing += 1
            continue
        spent += float(getattr(record, "cost_usd_est", 0.0) or 0.0)
    return spent, missing


def _status_from_burn(burn_pct: float | None) -> str:
    if burn_pct is None:
        return "pre_launch"
    if burn_pct < 50:
        return "cool"
    if burn_pct < 75:
        return "warm"
    if burn_pct <= 90:
        return "hot"
    return "near_cap"


def _burn_pct(spent_usd: float | None, cap_usd: float | None) -> float | None:
    if spent_usd is None or not cap_usd:
        return None
    return round((spent_usd / cap_usd) * 100, 1)


def _round_money(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def _format_pct(value: float | None) -> str:
    if value is None:
        return "unknown"
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _days_until(today: date, target: date | None) -> int | None:
    if target is None:
        return None
    return (target - today).days


def _in_flight_by_agent() -> dict[str, int]:
    in_flight = {agent: 0 for agent in AGENT_NAMES}
    try:
        tasks = delegate_api.list_delegate_tasks(status="all", limit=500)["tasks"]
    except Exception:
        return in_flight
    for task in tasks:
        if task.get("status") not in {"running", "spawning"}:
            continue
        agent = _agent_key(task.get("agent"))
        if agent:
            in_flight[agent] += 1
    return in_flight


def _recommend_agent(agents: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    status_by_agent = {
        "claude": agents["claude"]["interactive"]["status"],
        "codex": agents["codex"]["status"],
        "gemini": agents["gemini"]["status"],
    }
    burn_by_agent = {
        "claude": agents["claude"]["interactive"]["burn_pct_7d"],
        "codex": agents["codex"]["burn_pct_7d"],
        "gemini": agents["gemini"]["burn_pct_7d"],
    }

    if all(status in {"hot", "near_cap"} for status in status_by_agent.values()):
        warnings.append("all agents near cap — orchestrator inline-mode contingency may be needed soon")
        return {
            "primary_agent_for_code": "inline_orchestrator",
            "rationale": "All agents are hot or near cap; preserve remaining provider quota for high-judgment work.",
            "warnings": warnings,
        }

    if "near_cap" in status_by_agent.values():
        candidates = [
            agent for agent, status in status_by_agent.items()
            if status in {"cool", "warm"}
        ]
        if candidates:
            recommended = min(candidates, key=lambda agent: burn_by_agent[agent] or 0.0)
            return {
                "primary_agent_for_code": recommended,
                "rationale": (
                    f"At least one agent is near cap; {recommended} has the lowest "
                    f"available 7d burn ({_format_pct(burn_by_agent[recommended])}%)."
                ),
                "warnings": warnings,
            }

    agentic_pool = agents["claude"]["agentic_pool"]
    if agentic_pool.get("active") and agentic_pool.get("status") == "cool":
        return {
            "primary_agent_for_code": "claude",
            "rationale": "Claude agentic pool is active and cool; drain the separate monthly pool first.",
            "warnings": warnings,
        }

    if all(status in {"cool", "warm"} for status in status_by_agent.values()):
        codex_burn = burn_by_agent["codex"]
        return {
            "primary_agent_for_code": "codex",
            "rationale": (
                "All agents cool or warm; default 3:3:3 split applies. "
                f"Codex 7d burn is {_format_pct(codex_burn)}%. "
                "Claude agentic pool "
                + (
                    "active."
                    if agentic_pool.get("active")
                    else "pre-launch — interactive pool used for claude headless."
                )
            ),
            "warnings": warnings,
        }

    recommended = min(status_by_agent, key=lambda agent: burn_by_agent[agent] or 0.0)
    return {
        "primary_agent_for_code": recommended,
        "rationale": (
            f"Mixed routing state; {recommended} currently has the lowest 7d burn "
            f"({_format_pct(burn_by_agent[recommended])}%)."
        ),
        "warnings": warnings,
    }


def compute_routing_budget(now: datetime | None = None) -> dict[str, Any]:
    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    today = current_time.date()
    window_start = current_time - timedelta(days=7)
    budgets, warnings = _load_agent_budgets()
    if not budgets:
        agents = {
            "claude": {
                "interactive": {
                    "spent_7d_usd": None,
                    "weekly_cap_usd": None,
                    "burn_pct_7d": None,
                    "promo_active": False,
                    "status": "pre_launch",
                },
                "agentic_pool": {
                    "spent_cycle_usd": None,
                    "monthly_cap_usd": None,
                    "burn_pct_cycle": None,
                    "active": False,
                    "starts_on": None,
                    "status": "pre_launch",
                },
            },
            "codex": {"spent_7d_usd": None, "weekly_cap_usd": None, "burn_pct_7d": None, "status": "pre_launch"},
            "gemini": {"spent_7d_usd": None, "weekly_cap_usd": None, "burn_pct_7d": None, "status": "pre_launch"},
        }
        return {
            "generated_at": _isoformat_z(current_time),
            "agents": agents,
            "in_flight": _in_flight_by_agent(),
            "recommendation": {
                "primary_agent_for_code": "inline_orchestrator",
                "rationale": "Budget config could not be loaded; routing recommendation is unavailable.",
                "warnings": warnings,
            },
            "diagnostics": {
                "records_loaded": 0,
                "missing_cost_records": 0,
                "window_start": _isoformat_z(window_start),
            },
        }

    records = load_cost_records()
    agents: dict[str, Any] = {}
    missing_cost_records = 0

    claude_config = budgets.get("claude") if isinstance(budgets.get("claude"), dict) else {}
    interactive_config = claude_config.get("interactive") if isinstance(claude_config.get("interactive"), dict) else {}
    agentic_config = claude_config.get("agentic_pool") if isinstance(claude_config.get("agentic_pool"), dict) else {}
    promo_through = _parse_iso_date(interactive_config.get("promo_through"))
    promo_active = bool(promo_through and today <= promo_through)
    claude_cap = float(
        interactive_config.get("promo_weekly_cap_usd" if promo_active else "weekly_cap_usd") or 0.0
    )
    claude_spent, missing = _sum_agent_spend(records, agent="claude", since=window_start)
    missing_cost_records += missing
    claude_burn = _burn_pct(claude_spent, claude_cap)

    starts_on = _parse_iso_date(agentic_config.get("starts_on"))
    agentic_active = bool(starts_on and today >= starts_on)
    agentic_cap = float(agentic_config.get("monthly_cap_usd") or 0.0)
    if agentic_active and starts_on:
        cycle_start = datetime.combine(starts_on, datetime.min.time(), tzinfo=UTC)
        agentic_spent, missing = _sum_agent_spend(records, agent="claude", since=cycle_start)
        missing_cost_records += missing
        agentic_burn = _burn_pct(agentic_spent, agentic_cap)
        agentic_status = _status_from_burn(agentic_burn)
    else:
        agentic_spent = None
        agentic_burn = None
        agentic_status = "pre_launch"

    agents["claude"] = {
        "interactive": {
            "spent_7d_usd": _round_money(claude_spent),
            "weekly_cap_usd": _round_money(claude_cap),
            "burn_pct_7d": claude_burn,
            "promo_active": promo_active,
            "status": _status_from_burn(claude_burn),
        },
        "agentic_pool": {
            "spent_cycle_usd": _round_money(agentic_spent),
            "monthly_cap_usd": _round_money(agentic_cap),
            "burn_pct_cycle": agentic_burn,
            "active": agentic_active,
            "starts_on": starts_on.isoformat() if starts_on else None,
            "status": agentic_status,
        },
        "spent_7d_usd": _round_money(claude_spent),
        "weekly_cap_usd": _round_money(claude_cap),
        "burn_pct_7d": claude_burn,
        "status": _status_from_burn(claude_burn),
    }

    for agent in ("codex", "gemini"):
        agent_config = budgets.get(agent) if isinstance(budgets.get(agent), dict) else {}
        cap = float(agent_config.get("weekly_cap_usd") or 0.0)
        spent, missing = _sum_agent_spend(records, agent=agent, since=window_start)
        missing_cost_records += missing
        burn = _burn_pct(spent, cap)
        agents[agent] = {
            "spent_7d_usd": _round_money(spent),
            "weekly_cap_usd": _round_money(cap),
            "burn_pct_7d": burn,
            "status": _status_from_burn(burn),
        }

    claude_burn_pct = agents["claude"]["interactive"]["burn_pct_7d"]
    if agents["claude"]["interactive"]["status"] in {"hot", "near_cap"}:
        warnings.append(
            f"claude.interactive at {_format_pct(claude_burn_pct)}% — consider --agent codex for next mechanical fix"
        )
    starts_in_days = _days_until(today, starts_on)
    if starts_in_days is not None and 0 <= starts_in_days <= 14:
        warnings.append(f"agentic_pool launches in {starts_in_days} days")
    promo_days = _days_until(today, promo_through)
    if promo_days is not None and 0 <= promo_days <= 14:
        warnings.append(
            f"promo expires in {promo_days} days; +50% bonus capacity ends {promo_through.isoformat()}"
        )

    return {
        "generated_at": _isoformat_z(current_time),
        "agents": agents,
        "in_flight": _in_flight_by_agent(),
        "recommendation": _recommend_agent(agents, warnings),
        "diagnostics": {
            "records_loaded": len(records),
            "missing_cost_records": missing_cost_records,
            "window_start": _isoformat_z(window_start),
        },
    }


# ==================== ENDPOINTS ====================


@router.get("/routing-budget")
async def routing_budget():
    """Per-agent soft-cap burn and routing recommendation for dispatch planning."""
    return await asyncio.to_thread(compute_routing_budget)


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
    """Per-module pipeline state for one track."""
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
        counts = {"v6": 0, "v5": 0, "v3": 0, "unbuilt": 0}
        by_version: dict[str, list] = {"v6": [], "v5": [], "v3": [], "unbuilt": []}
        per_track: dict[str, dict] = {}

        level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

        for level_cfg in level_cfgs:
            track_id = level_cfg["id"]
            plan_slugs = get_plan_slugs(track_id)
            if not plan_slugs:
                continue

            track_dir = CURRICULUM_ROOT / level_cfg["path"]
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
        built = counts["v6"] + counts["v5"]
        return {
            "total": total, "counts": counts,
            "pct_v6": round(counts["v6"] / total * 100) if total else 0,
            "pct_v5": round(counts["v5"] / total * 100) if total else 0,
            "pct_built": round(built / total * 100) if total else 0,
            "needs_rebuild": counts["v5"] + counts["v3"] + counts["unbuilt"],
            "per_track": per_track,
            "v6_modules": by_version["v6"],
            "v5_modules": by_version["v5"],
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
                orch_dir = safe_join(track_dir / "orchestration", slug)
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
    cache_key = f"weak_points_{track or 'all'}_{min_score}_{limit}"
    cached = cache_get(cache_key, ttl=60.0)
    if cached is not None:
        return cached

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

                research_score = get_research_score(track_dir, slug, track_id)
                if research_score is not None and research_score < min_score:
                    issues.append(f"research_score_{research_score}")

                word_count = audit.get("word_count", 0)
                word_target = audit.get("word_target", 0)
                if word_target == 0 and word_count > 0:
                    word_target = get_word_target_from_plan(track_id, slug)
                if word_target > 0 and word_count > 0 and word_count < word_target * 0.8:
                    issues.append(f"low_words_{word_count}/{word_target}")

                if issues:
                    orch_dir = safe_join(track_dir / "orchestration", slug)
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

    result = await asyncio.to_thread(_compute)
    cache_set(cache_key, result)
    return result


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
                orch_dir = safe_join(track_dir / "orchestration", slug)
                version = detect_pipeline_version(orch_dir)
                audit = get_audit_status(track_dir, slug)

                if version in ("v6", "v5"):
                    phases = read_v2_state(orch_dir).get("phases", {})
                    failed_phases = [
                        k for k, v in phases.items()
                        if isinstance(v, dict) and v.get("status") == "failed"
                    ]
                elif version == "v3":
                    v3 = read_v3_state(orch_dir)
                    phases = v3.get("phases", {})
                    failed_phases = [
                        k.replace("v3-", "") for k, v in phases.items()
                        if isinstance(v, dict) and v.get("status") == "failed"
                    ]
                else:
                    failed_phases = []

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


@router.get("/module/{track_id}/slug/{slug}")
async def module_detail_by_slug(
    track_id: str,
    slug: str,
    verbose: bool = Query(
        False,
        description="True = full compute_module_detail payload. Default returns a compact view.",
    ),
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
          "shippable":        true,
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

    plan_slugs = get_plan_slugs(track_id)
    match = next(((n, s) for n, s in plan_slugs if s == slug), None)
    if not match:
        return JSONResponse(
            status_code=404,
            content={"error": f"Module '{slug}' not found in track '{track_id}'"},
        )
    num, _ = match

    full = await asyncio.to_thread(compute_module_detail, track_id, num, level_cfg)
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
            exec_ = data.get("executor") if isinstance(data.get("executor"), dict) else {}
            current_worker = exec_.get("agent")

    audit = full.get("audit") or {}
    review = full.get("review") or {}
    final_review = full.get("final_review")

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
        "shippable": bool(full.get("shippable")),
        "blocking_issues": audit.get("blocking_issues") or [],
        "retry_count": retry_count,
        "worker": current_worker,
    }


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


# ==================== RANGE STATUS (#1313 / Codex-4) ====================


@router.get("/range/{track_id}")
async def range_status(
    track_id: str,
    start: int = Query(1, ge=1, description="First module number (inclusive)."),
    end: int | None = Query(
        None,
        description="Last module number (inclusive). Omit to go to the end of the track.",
    ),
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
        full = compute_pipeline_track(track_id, level_cfg)
        modules = full.get("modules", []) if isinstance(full, dict) else full
        if not isinstance(modules, list):
            return {"error": "pipeline_track returned non-list"}

        sliced = [
            m for m in modules
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

            compact.append({
                "num": m["num"],
                "slug": m.get("slug"),
                "phase": phase_now,
                "phase_status": (
                    phases.get(phase_now, {}).get("status")
                    if isinstance(phases.get(phase_now), dict) else None
                ),
                "worker": (
                    phases.get(phase_now, {}).get("executor", {}).get("agent")
                    if isinstance(phases.get(phase_now), dict)
                    and isinstance(phases.get(phase_now, {}).get("executor"), dict)
                    else None
                ),
                "audit": audit,
                "review_score": (
                    review.get("score") if isinstance(review, dict) else None
                ),
                "words": m.get("words"),
                "word_target": m.get("word_target"),
                "blocker": blocker,
                "pipeline_version": m.get("pipeline_version"),
                "needs_rebuild": m.get("needs_rebuild"),
            })

        return {
            "track": track_id,
            "start": start,
            "end": end,
            "count": len(compact),
            "modules": compact,
        }

    return await asyncio.to_thread(_compute)


# ==================== MANIFEST (#1309) ====================


@router.get("/manifest")
async def manifest():
    """Tiny JSON index for agent cold-start coordination.

    Target size < 2 KB. Returns a hash + URL for every consolidated
    component an agent might need at boot. Agents keep a per-hash
    cache (see ``scripts/ai_agent_bridge/_monitor_cache.py`` / the
    client SDK) and only refetch components whose hash changed since
    the last manifest they consumed.

    Shape::
        {
          "generated_at": "2026-04-17T10:15:00Z",
          "rules":   {"hash": "...", "url": "/api/rules?format=markdown"},
          "session": {"hash": "...", "url": "/api/session/current?format=markdown"},
          "orient":  {"url": "/api/orient"},
          "inbox":   {"url_template": "/api/comms/inbox?agent={name}"}
        }

    ``rules`` and ``session`` expose a content hash so an agent can
    skip the payload entirely when unchanged. ``orient`` and ``inbox``
    have their own freshness machinery (TTLs, ``?fresh=true``, and
    per-section ``meta``) so they don't need a manifest hash.

    Reviewer BLOCKER #1309: without this endpoint an agent booting
    fresh had to read 5-8 files (CLAUDE.md + three rule files +
    current.md + recent handoffs + MONITOR-API.md) to orient — every
    session, every compaction. The manifest collapses the steady
    state to one tiny call.
    """
    from datetime import UTC
    from datetime import datetime as _dt

    from .rules_router import rules_hash
    from .session_router import session_hash
    from .telemetry.response import add_json_telemetry

    return add_json_telemetry({
        "generated_at": _dt.now(UTC).isoformat().replace("+00:00", "Z"),
        "rules": {
            "hash": rules_hash(),
            "url": "/api/rules?format=markdown",
            "format": "markdown",
            "note": "Condensed critical + non-negotiable + workflow rules. Drop straight into a system prompt.",
        },
        "session": {
            "hash": session_hash(),
            "url": "/api/session/current?format=markdown",
            "format": "markdown",
            "note": "Current.md + recent session-state handoff filenames.",
        },
        "orient": {
            "url": "/api/orient",
            "fresh_param": "?fresh=true",
            "note": "Per-section TTL cache + meta. Most agents only need the sections whose TTL has elapsed.",
        },
        "inbox": {
            "url_template": "/api/comms/inbox?agent={name}",
            "note": "Read-only view of unread channel deliveries for one agent.",
        },
    })
