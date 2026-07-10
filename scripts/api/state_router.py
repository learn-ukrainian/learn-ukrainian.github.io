"""State API router -- v6 pipeline state, research/review coverage, weak points, issues.

Mounted at /api/state/ in main.py.

Endpoints:
  GET /api/state/summary              Full project snapshot
  GET /api/state/pipeline/{track}     Per-module pipeline state for one track
  GET /api/state/ready-to-build       Phase A done, Phase B not started
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
  GET /api/state/routing-budget       Per-agent capacity burn + routing recommendation

Performance notes:
  - Heavy endpoints run their sync I/O in asyncio.to_thread().
  - Results are cached in-memory with a TTL (60s for summary/pipeline, 300s for coverage).
"""

import asyncio
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from scripts.analytics.cost_report import CostRecord, load_cost_records
from scripts.audit.llm_qg_store import (
    current_payload_for_module,
    llm_qg_file_is_current_for_module,
)

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)

from . import delegate_router as delegate_api
from .codexbar_usage import get_provider_usage_data, refresh_provider_usage_data
from .config import CURRICULUM_ROOT, LEVELS
from .state_build import (
    compute_build_stats,
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
from .state_helpers import (
    cache_get,
    cache_get_with_age,
    cache_invalidate,
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
TASKS_DIR = Path(__file__).resolve().parents[2] / "batch_state" / "tasks"
SUBSCRIPTION_LANES = ("claude", "codex", "gemini", "grok", "cursor")
API_LANES = ("deepseek",)  # representative; others via openrouter absent BY DESIGN
AGENT_NAMES = SUBSCRIPTION_LANES  # only subscription lanes participate in CodexBar window checks
STATE_SUMMARY_TTL_S = 60.0
STATE_PIPELINE_TTL_S = 60.0
STATE_RESEARCH_COVERAGE_TTL_S = 300.0
STATE_RESEARCH_DETAIL_TTL_S = 120.0
STATE_REVIEW_COVERAGE_TTL_S = 300.0
STATE_PIPELINE_VERSIONS_TTL_S = 60.0


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


def _load_budget_extras(budgets: dict[str, Any]) -> dict[str, Any]:
    """Load optional extras like reset threshold (default 6h per sensible default for 'imminent')."""
    if not isinstance(budgets, dict):
        return {"reset_imminent_hours": 6}
    val = budgets.get("reset_imminent_threshold_hours", 6)
    try:
        hours = int(val)
    except (TypeError, ValueError):
        hours = 6
    return {"reset_imminent_hours": max(1, min(48, hours))}


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


def _status_from_burn(burn_pct: float | None, *, has_cap: bool = True) -> str:
    if not has_cap:
        return "unknown"
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


def _next_weekly_reset(current_time: datetime) -> str:
    """Compute next ISO weekly reset boundary (treated as Monday 00:00Z for rolling weekly caps)."""
    today = current_time.date()
    # weekday: Mon=0 ... Sun=6; next Monday is (7 - wd) %7 , 0 means today if Mon
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7  # if exactly Monday, next is +7
    reset_dt = datetime.combine(today + timedelta(days=days_ahead), datetime.min.time(), tzinfo=UTC)
    return _isoformat_z(reset_dt)


def _snapshot_is_stale(
    current_time: datetime, records: list[CostRecord], threshold_s: float = 900.0
) -> tuple[bool, float | None]:
    """Return (is_stale, age_s) based on most recent record mtime vs now.
    15min=900s default per AC. If no records, not 'stale' but 'empty' handled separately.
    """
    if not records:
        return False, None
    latest = max(
        (getattr(r, "mtime", datetime.min.replace(tzinfo=UTC)) or datetime.min.replace(tzinfo=UTC) for r in records),
        default=None,
    )
    if latest is None:
        return False, None
    age = (current_time - latest).total_seconds()
    return age > threshold_s, round(age, 1)


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


def _recommend_agent(
    agents: dict[str, Any],
    warnings: list[str],
    *,
    current_time: datetime | None = None,
    reset_imminent_hours: int = 6,
    is_stale: bool = False,
    records_loaded: int = 0,
    authoritative_data_available: bool = False,
) -> dict[str, Any]:
    """Generalized recommendation over subscription lanes + reset-aware + empty/stale guards.

    When both the ledger and CodexBar are empty, suppress the primary rec. A
    fresh CodexBar overlay is authoritative even when the local USD ledger is
    empty.
    Reset-aware: if top pick resets within N hours, note deferral warning (N configurable).
    """
    if is_stale:
        warnings.append("snapshot stale (>15min old data) — advisory only, verify manually before trusting numbers")

    if records_loaded == 0 and not authoritative_data_available:
        return {
            "primary_agent_for_code": None,
            "rationale": "Budget snapshot empty/absent (records_loaded=0); confident primary-lane recommendation suppressed per pinned design constraint. Use model-assignment.md + /api/orient runtime.headroom instead.",
            "warnings": [*warnings, "empty snapshot — no recommendation emitted"],
        }

    # Build status/burn for core code lanes (claude special interactive, others flat); include grok/cursor if present
    core = ["claude", "codex", "gemini"]
    status_by_agent: dict[str, str] = {}
    burn_by_agent: dict[str, float | None] = {}
    resets_by: dict[str, str | None] = {}
    for a in core:
        if a not in agents:
            continue
        if a == "claude":
            st = agents[a].get("interactive", {}).get("status") or agents[a].get("status", "unknown")
            br = agents[a].get("interactive", {}).get("burn_pct_7d") or agents[a].get("burn_pct_7d")
        else:
            st = agents[a].get("status", "unknown")
            br = agents[a].get("burn_pct_7d")
        status_by_agent[a] = st
        burn_by_agent[a] = br
        resets_by[a] = agents[a].get("resets_at")

    # include extra subs if they have data
    for a in SUBSCRIPTION_LANES:
        if a in core or a not in agents:
            continue
        status_by_agent[a] = agents[a].get("status", "unknown")
        burn_by_agent[a] = agents[a].get("burn_pct_7d")
        resets_by[a] = agents[a].get("resets_at")

    # If no usable data at all for rec, suppress
    usable = [a for a, s in status_by_agent.items() if s not in {"unknown", "pre_launch", None}]
    if not usable or all(s in {"hot", "near_cap", "unknown"} for s in status_by_agent.values()):
        if all(s in {"hot", "near_cap"} for s in status_by_agent.values() if s not in {"unknown"}):
            warnings.append("all agents near cap — orchestrator inline-mode contingency may be needed soon")
            return {
                "primary_agent_for_code": "inline_orchestrator",
                "rationale": "All agents are hot or near cap; preserve remaining provider quota for high-judgment work.",
                "warnings": warnings,
            }
        return {
            "primary_agent_for_code": None,
            "rationale": "No usable subscription lane headroom data for confident recommendation (stale/empty/unknowns).",
            "warnings": warnings,
        }

    # Reset-aware filter: identify imminent resets
    imminent: list[str] = []
    if current_time is not None:
        for a, ra in resets_by.items():
            if not ra:
                continue
            try:
                rt = datetime.fromisoformat(ra.replace("Z", "+00:00"))
                hours_left = (rt - current_time).total_seconds() / 3600.0
                if 0 < hours_left <= reset_imminent_hours:
                    imminent.append(a)
            except Exception:
                pass
    if imminent:
        warnings.append(
            f"lanes resetting soon (within {reset_imminent_hours}h): {', '.join(imminent)} — defer large batches on these if possible"
        )
    if "near_cap" in status_by_agent.values():
        candidates = [agent for agent, st in status_by_agent.items() if st == "cool"]
        if not candidates:
            candidates = [agent for agent, st in status_by_agent.items() if st == "warm"]
        if candidates:
            # prefer non-imminent if possible
            non_imm = [c for c in candidates if c not in imminent] or candidates
            recommended = min(non_imm, key=lambda agent: burn_by_agent.get(agent) or 0.0)
            return {
                "primary_agent_for_code": recommended,
                "rationale": (
                    f"At least one agent is near cap; {recommended} has the lowest "
                    f"available 7d burn ({_format_pct(burn_by_agent.get(recommended))}%)."
                ),
                "warnings": warnings,
            }

    # claude pool still special
    if "claude" in agents:
        agentic_pool = agents["claude"].get("agentic_pool", {})
        if agentic_pool.get("active") and agentic_pool.get("status") == "cool":
            return {
                "primary_agent_for_code": "claude",
                "rationale": "Claude agentic pool is active and cool; drain the separate monthly pool first.",
                "warnings": warnings,
            }

    cool_lanes = [a for a, s in status_by_agent.items() if s == "cool"]
    if cool_lanes:
        pool = [c for c in cool_lanes if c not in imminent] or cool_lanes
        recommended = min(pool, key=lambda agent: burn_by_agent.get(agent) or 0.0)
        rationale = (
            "All agents cool or warm; default split applies. "
            f"{recommended} 7d burn is {_format_pct(burn_by_agent.get(recommended))}%. "
        )
        return {
            "primary_agent_for_code": recommended,
            "rationale": rationale,
            "warnings": warnings,
        }

    warm_lanes = [a for a, s in status_by_agent.items() if s == "warm"]
    if warm_lanes:
        pool = [c for c in warm_lanes if c not in imminent] or warm_lanes
        recommended = min(pool, key=lambda agent: burn_by_agent.get(agent) or 0.0)
        rationale = f"Mixed; {recommended} has lowest 7d burn ({_format_pct(burn_by_agent.get(recommended))}%)."
        return {
            "primary_agent_for_code": recommended,
            "rationale": rationale,
            "warnings": warnings,
        }

    # fallback to lowest burn among known
    known = list(status_by_agent.keys())
    if known:
        recommended = min(known, key=lambda agent: burn_by_agent.get(agent) or 0.0)
        return {
            "primary_agent_for_code": recommended,
            "rationale": f"Mixed routing state; {recommended} currently has the lowest 7d burn ({_format_pct(burn_by_agent.get(recommended))}%).",
            "warnings": warnings,
        }

    return {"primary_agent_for_code": None, "rationale": "insufficient data", "warnings": warnings}


def compute_routing_budget(now: datetime | None = None, *, fresh_codexbar: bool = False) -> dict[str, Any]:
    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    today = current_time.date()
    window_start = current_time - timedelta(days=7)
    budgets, warnings = _load_agent_budgets()
    extras = _load_budget_extras(budgets)
    reset_hours = extras["reset_imminent_hours"]
    resets_at = _next_weekly_reset(current_time)

    from .lane_health import compute_lane_health
    health_records = {}
    try:
        health_records = compute_lane_health(
            TASKS_DIR,
            now=current_time
        )
    except Exception as exc:
        import logging
        logging.getLogger("state_router").debug("Failed to compute lane health: %s", exc)

    # Empty config case: unknown statuses, suppressed rec (no confident pick from absent data)
    if not budgets:
        agents = {}
        for lane in SUBSCRIPTION_LANES:
            lane_health = health_records.get(lane, {"healthy": True, "consecutive_failures": 0, "span_minutes": 0})
            if lane == "claude":
                agents[lane] = {
                    "interactive": {
                        "spent_7d_usd": None,
                        "weekly_cap_usd": None,
                        "burn_pct_7d": None,
                        "promo_active": False,
                        "status": "unknown",
                    },
                    "agentic_pool": {
                        "spent_cycle_usd": None,
                        "monthly_cap_usd": None,
                        "burn_pct_cycle": None,
                        "active": False,
                        "starts_on": None,
                        "status": "unknown",
                    },
                    "spent_7d_usd": None,
                    "weekly_cap_usd": None,
                    "burn_pct_7d": None,
                    "status": "unknown",
                    "resets_at": resets_at,
                    "health": lane_health,
                }
            else:
                agents[lane] = {
                    "spent_7d_usd": None,
                    "weekly_cap_usd": None,
                    "burn_pct_7d": None,
                    "status": "unknown",
                    "resets_at": resets_at,
                    "health": lane_health,
                }
        rec = {
            "primary_agent_for_code": None,
            "rationale": "Budget config absent; recommendation suppressed (empty snapshot).",
            "warnings": [*warnings, "empty snapshot — use model-assignment + /api/orient"],
        }

        ranked_subs = [
            {
                "lane": lane,
                "type": "subscription",
                "status": "unknown",
                "burn_pct_7d": None,
                "remaining_pct": None,
                "resets_at": resets_at,
                "health": agents[lane]["health"],
            }
            for lane in SUBSCRIPTION_LANES
        ]
        ranked_apis = [
            {
                "lane": lane,
                "type": "api",
                "status": "unknown",
                "burn_pct_7d": None,
                "remaining_pct": None,
                "resets_at": None,
                "health": health_records.get(lane, {"healthy": True, "consecutive_failures": 0, "span_minutes": 0}),
            }
            for lane in API_LANES
        ]
        ranked = ranked_subs + ranked_apis

        healthy_lanes = [x for x in ranked if x.get("health", {}).get("healthy", True)]
        unhealthy_lanes = [x for x in ranked if not x.get("health", {}).get("healthy", True)]
        ranked = healthy_lanes + unhealthy_lanes

        return {
            "generated_at": _isoformat_z(current_time),
            "agents": agents,
            "in_flight": _in_flight_by_agent(),
            "recommendation": rec,
            "diagnostics": {
                "records_loaded": 0,
                "missing_cost_records": 0,
                "window_start": _isoformat_z(window_start),
                "stale": False,
                "data_age_s": None,
                "stale_threshold_s": 900,
            },
            "ranked_by_headroom": ranked,
        }

    records = load_cost_records()
    ledger_stale, ledger_age_s = _snapshot_is_stale(current_time, records)
    is_stale = ledger_stale
    data_age_s = ledger_age_s

    agents: dict[str, Any] = {}
    missing_cost_records = 0

    claude_config = budgets.get("claude") if isinstance(budgets.get("claude"), dict) else {}
    interactive_config = claude_config.get("interactive") if isinstance(claude_config.get("interactive"), dict) else {}
    agentic_config = claude_config.get("agentic_pool") if isinstance(claude_config.get("agentic_pool"), dict) else {}
    promo_through = _parse_iso_date(interactive_config.get("promo_through"))
    promo_active = bool(promo_through and today <= promo_through)
    claude_cap = float(interactive_config.get("promo_weekly_cap_usd" if promo_active else "weekly_cap_usd") or 0.0)
    claude_spent, missing = _sum_agent_spend(records, agent="claude", since=window_start)
    missing_cost_records += missing
    claude_burn = _burn_pct(claude_spent, claude_cap)
    claude_has_cap = claude_cap > 0

    starts_on = _parse_iso_date(agentic_config.get("starts_on"))
    agentic_active = bool(starts_on and today >= starts_on)
    agentic_cap = float(agentic_config.get("monthly_cap_usd") or 0.0)
    if agentic_active and starts_on:
        cycle_start = datetime.combine(starts_on, datetime.min.time(), tzinfo=UTC)
        agentic_spent, missing = _sum_agent_spend(records, agent="claude", since=cycle_start)
        missing_cost_records += missing
        agentic_burn = _burn_pct(agentic_spent, agentic_cap)
        agentic_status = _status_from_burn(agentic_burn, has_cap=(agentic_cap > 0))
    else:
        agentic_spent = None
        agentic_burn = None
        agentic_status = "pre_launch" if agentic_cap > 0 else "unknown"

    claude_status = _status_from_burn(claude_burn, has_cap=claude_has_cap)
    # empty snapshot special: force unknown (per AC, not cool when records_loaded==0)
    force_unknown = len(records) == 0
    if force_unknown:
        claude_status = "unknown"
        claude_burn = None

    agents["claude"] = {
        "interactive": {
            "spent_7d_usd": _round_money(claude_spent),
            "weekly_cap_usd": _round_money(claude_cap),
            "burn_pct_7d": claude_burn,
            "promo_active": promo_active,
            "status": claude_status,
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
        "status": claude_status,
        "resets_at": resets_at,
        "remaining_pct": (100.0 - claude_burn) if claude_burn is not None else None,
    }

    for agent in ("codex", "gemini", "grok", "cursor"):
        agent_config = budgets.get(agent) if isinstance(budgets.get(agent), dict) else {}
        cap = float(agent_config.get("weekly_cap_usd") or 0.0) if agent_config else 0.0
        has_cap = cap > 0
        spent, missing = _sum_agent_spend(records, agent=agent, since=window_start)
        missing_cost_records += missing
        burn = _burn_pct(spent, cap) if has_cap else None
        st = _status_from_burn(burn, has_cap=has_cap)
        if force_unknown or not has_cap:
            st = "unknown"
            burn = None
        agents[agent] = {
            "spent_7d_usd": _round_money(spent),
            "weekly_cap_usd": _round_money(cap) if has_cap else None,
            "burn_pct_7d": burn,
            "status": st,
            "resets_at": resets_at,
            "remaining_pct": (100.0 - burn) if burn is not None else None,
        }

    # Overlay codexbar data as authoritative
    cb_sourced_any = False
    cb_stale = False
    cb_max_age_s = None
    refreshed_codexbar = refresh_provider_usage_data(SUBSCRIPTION_LANES) if fresh_codexbar else {}

    for lane in SUBSCRIPTION_LANES:
        cb_data = refreshed_codexbar.get(lane) or get_provider_usage_data(lane)
        if cb_data and cb_data.get("weekly_used_pct") is not None:
            cb_sourced_any = True
            weekly_used = cb_data["weekly_used_pct"]

            # Determine status using deficit signal
            is_in_deficit = (
                (cb_data.get("will_last_to_reset") is False)
                or (cb_data.get("weekly_pace_delta_pct") is not None and cb_data["weekly_pace_delta_pct"] > 0)
                or (weekly_used >= 90.0)
            )

            if weekly_used >= 90.0:
                cb_status = "near_cap"
            elif is_in_deficit:
                cb_status = "hot"
            elif weekly_used < 50.0:
                cb_status = "cool"
            else:
                cb_status = "warm"

            # Check if stale
            if cb_data.get("stale"):
                cb_stale = True
            age = cb_data.get("age_s")
            if age is not None and (cb_max_age_s is None or age > cb_max_age_s):
                cb_max_age_s = age

            # Build codexbar metadata dict
            agents[lane]["codexbar"] = {
                "primary_used_pct": cb_data.get("primary_used_pct"),
                "weekly_used_pct": cb_data.get("weekly_used_pct"),
                "monthly_cap_usd": cb_data.get("monthly_cap_usd"),
                "monthly_used_usd": cb_data.get("monthly_used_usd"),
                "weekly_resets_at": cb_data.get("weekly_resets_at"),
                "weekly_pace_delta_pct": cb_data.get("weekly_pace_delta_pct"),
                "will_last_to_reset": cb_data.get("will_last_to_reset"),
                "pace_summary": cb_data.get("pace_summary"),
                "stale": cb_data.get("stale", False),
                "fetched_at": cb_data.get("fetched_at"),
            }

            # Update authoritative keys in agents
            if lane == "claude":
                agents[lane]["interactive"]["burn_pct_7d"] = weekly_used
                agents[lane]["interactive"]["status"] = cb_status
                agents[lane]["interactive"]["spent_7d_usd"] = (
                    _round_money((weekly_used / 100.0) * claude_cap) if claude_cap else None
                )
                agents[lane]["burn_pct_7d"] = weekly_used
                agents[lane]["status"] = cb_status
                agents[lane]["spent_7d_usd"] = agents[lane]["interactive"]["spent_7d_usd"]
                agents[lane]["remaining_pct"] = 100.0 - weekly_used
                if cb_data.get("weekly_resets_at"):
                    agents[lane]["resets_at"] = cb_data["weekly_resets_at"]

                # Check agentic pool overlay
                m_cap = cb_data.get("monthly_cap_usd")
                m_used = cb_data.get("monthly_used_usd")
                if m_cap is not None and m_used is not None:
                    agents[lane]["agentic_pool"]["monthly_cap_usd"] = m_cap
                    agents[lane]["agentic_pool"]["spent_cycle_usd"] = m_used
                    pool_burn = _burn_pct(m_used, m_cap)
                    agents[lane]["agentic_pool"]["burn_pct_cycle"] = pool_burn
                    agents[lane]["agentic_pool"]["status"] = _status_from_burn(pool_burn, has_cap=(m_cap > 0))
            else:
                agent_config = budgets.get(lane) if isinstance(budgets.get(lane), dict) else {}
                cap = float(agent_config.get("weekly_cap_usd") or 0.0) if agent_config else 0.0
                agents[lane]["burn_pct_7d"] = weekly_used
                agents[lane]["status"] = cb_status
                agents[lane]["spent_7d_usd"] = _round_money((weekly_used / 100.0) * cap) if cap else None
                agents[lane]["remaining_pct"] = 100.0 - weekly_used
                if cb_data.get("weekly_resets_at"):
                    agents[lane]["resets_at"] = cb_data["weekly_resets_at"]

    if cb_sourced_any:
        is_stale = cb_stale
        data_age_s = cb_max_age_s

    if is_stale:
        warnings.append(
            "generatedAt/data age >15min — advisory downgraded to stale, verify manually (never hard block)"
        )

    # Build warnings for any lane in deficit (authoritative or fallback)
    for lane in SUBSCRIPTION_LANES:
        if lane in agents:
            cb = agents[lane].get("codexbar")
            if cb:
                is_in_deficit = (
                    (cb.get("will_last_to_reset") is False)
                    or (cb.get("weekly_pace_delta_pct") is not None and cb.get("weekly_pace_delta_pct") > 0)
                    or (cb.get("weekly_used_pct") is not None and cb.get("weekly_used_pct") >= 90.0)
                )
                pace_sum = cb.get("pace_summary") or f"{cb.get('weekly_used_pct')}% used"
            else:
                # Fallback to local ledger logic
                status = agents[lane].get("status") or agents[lane].get("interactive", {}).get("status")
                is_in_deficit = status in {"hot", "near_cap"}
                burn_pct = agents[lane].get("burn_pct_7d") or agents[lane].get("interactive", {}).get("burn_pct_7d")
                pace_sum = f"burn pct {burn_pct}%" if burn_pct is not None else "unknown"

            if is_in_deficit:
                # Deficit is a WEEKLY-pace signal. Quote the 5h window too:
                # a lane can be week-deficit yet have full 5h reserve for
                # normal work now — weekly-only wording misled toward
                # over-restriction (user correction 2026-07-09).
                five_h_pct = cb.get("primary_used_pct") if cb else None
                if five_h_pct is not None:
                    warnings.append(
                        f"lane {lane} is in deficit ({pace_sum}; weekly-pace signal — "
                        f"5h window {five_h_pct:.0f}% used, {100 - five_h_pct:.0f}% reserve)"
                    )
                else:
                    warnings.append(f"lane {lane} is in deficit ({pace_sum})")

    # Legacy Claude Interactive warning
    if "claude" in agents:
        claude_burn_pct = agents["claude"]["interactive"]["burn_pct_7d"]
        if not force_unknown and agents["claude"]["interactive"]["status"] in {"hot", "near_cap"}:
            warnings.append(
                f"claude.interactive at {_format_pct(claude_burn_pct)}% — consider --agent codex for next mechanical fix"
            )

    starts_in_days = _days_until(today, starts_on)
    if starts_in_days is not None and 0 <= starts_in_days <= 14:
        warnings.append(f"agentic_pool launches in {starts_in_days} days")
    promo_days = _days_until(today, promo_through)
    if promo_days is not None and 0 <= promo_days <= 14:
        warnings.append(
            f"promo expires in {promo_days} days; +50% bonus capacity ends {promo_through.isoformat() if promo_through else ''}"
        )

    rec = _recommend_agent(
        agents,
        warnings,
        current_time=current_time,
        reset_imminent_hours=reset_hours,
        is_stale=is_stale,
        records_loaded=len(records),
        authoritative_data_available=cb_sourced_any,
    )

    # Map health information to all subscription lanes in the agents dict
    for lane in SUBSCRIPTION_LANES:
        lane_health = health_records.get(lane, {"healthy": True, "consecutive_failures": 0, "span_minutes": 0})
        agents[lane]["health"] = lane_health

    # Build ranked view: subscription by remaining headroom (low burn = high remaining first), API always unknown
    def _rank_key(lane: str) -> float:
        a = agents.get(lane, {})
        b = a.get("burn_pct_7d")
        if b is None:
            return 999.0
        return b

    ranked_subs = []
    for lane in SUBSCRIPTION_LANES:
        a = agents.get(lane, {})
        ranked_subs.append(
            {
                "lane": lane,
                "type": "subscription",
                "status": a.get("status", "unknown"),
                "burn_pct_7d": a.get("burn_pct_7d"),
                "remaining_pct": a.get("remaining_pct"),
                "resets_at": a.get("resets_at"),
                "in_flight": _in_flight_by_agent().get(lane, 0),
                "health": a.get("health", {"healthy": True, "consecutive_failures": 0, "span_minutes": 0}),
            }
        )
    ranked_subs.sort(key=lambda x: (x["status"] == "unknown", x.get("burn_pct_7d") or 999.0))

    ranked_apis = [
        {
            "lane": lane,
            "type": "api",
            "status": "unknown",
            "burn_pct_7d": None,
            "remaining_pct": None,
            "resets_at": None,
            "in_flight": 0,
            "health": health_records.get(lane, {"healthy": True, "consecutive_failures": 0, "span_minutes": 0}),
        }
        for lane in API_LANES
    ]
    # per one design note treat absent as full, but AC requires status unknown NOT cool for ranked view
    ranked = ranked_subs + ranked_apis

    # Apply health demotion: unhealthy lanes are moved to the bottom of the list
    healthy_lanes = [x for x in ranked if x.get("health", {}).get("healthy", True)]
    unhealthy_lanes = [x for x in ranked if not x.get("health", {}).get("healthy", True)]
    ranked = healthy_lanes + unhealthy_lanes

    return {
        "generated_at": _isoformat_z(current_time),
        "agents": agents,
        "in_flight": _in_flight_by_agent(),
        "recommendation": rec,
        "diagnostics": {
            "records_loaded": len(records),
            "missing_cost_records": missing_cost_records,
            "window_start": _isoformat_z(window_start),
            "stale": is_stale,
            "data_age_s": data_age_s,
            "stale_threshold_s": 900,
            "reset_imminent_hours": reset_hours,
            "codexbar_data_available": cb_sourced_any,
            "fresh_codexbar_requested": fresh_codexbar,
        },
        "ranked_by_headroom": ranked,
    }


# ==================== ENDPOINTS ====================


@router.get("/routing-budget")
async def routing_budget(fresh_codexbar: bool = Query(False)):
    """Per-agent soft-cap burn and routing recommendation for dispatch planning."""
    return await asyncio.to_thread(compute_routing_budget, fresh_codexbar=fresh_codexbar)


@router.get("/summary")
async def state_summary(fresh: bool = Query(False)):
    """Full project snapshot. One call replaces 5 bash scripts at session start."""
    if fresh:
        cache_invalidate("summary")
    cached = cache_get_with_age("summary", ttl=STATE_SUMMARY_TTL_S)
    if cached is not None:
        value, age_s = cached
        return _with_state_meta(
            value,
            source="fs:plans+orchestration+artifacts+research",
            stale_after_s=STATE_SUMMARY_TTL_S,
            cache="hit",
            age_s=age_s,
        )
    result = await asyncio.to_thread(compute_summary)
    cache_set("summary", result)
    return _with_state_meta(
        result,
        source="fs:plans+orchestration+artifacts+research",
        stale_after_s=STATE_SUMMARY_TTL_S,
        cache="miss",
        age_s=0.0,
    )


@router.get("/pipeline/{track_id}")
async def pipeline_track(track_id: str, fresh: bool = Query(False)):
    """Per-module pipeline state for one track."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = f"pipeline_{track_id}"
    if fresh:
        cache_invalidate(cache_key)
    cached = cache_get_with_age(cache_key, ttl=STATE_PIPELINE_TTL_S)
    if cached is not None:
        value, age_s = cached
        return _with_state_meta(
            value,
            source="fs:orchestration+audit+research",
            stale_after_s=STATE_PIPELINE_TTL_S,
            cache="hit",
            age_s=age_s,
        )
    result = await asyncio.to_thread(compute_pipeline_track, track_id, level_cfg)
    cache_set(cache_key, result)
    return _with_state_meta(
        result,
        source="fs:orchestration+audit+research",
        stale_after_s=STATE_PIPELINE_TTL_S,
        cache="miss",
        age_s=0.0,
    )


@router.get("/pipeline-versions")
async def pipeline_versions(track: str | None = Query(None), fresh: bool = Query(False)):
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

    cache_key = f"pipeline_versions_{track or 'all'}"
    if fresh:
        cache_invalidate(cache_key)
    cached = cache_get_with_age(cache_key, ttl=STATE_PIPELINE_VERSIONS_TTL_S)
    if cached is not None:
        value, age_s = cached
        return _with_state_meta(
            value,
            source="fs:orchestration",
            stale_after_s=STATE_PIPELINE_VERSIONS_TTL_S,
            cache="hit",
            age_s=age_s,
        )
    result = await asyncio.to_thread(_compute)
    cache_set(cache_key, result)
    return _with_state_meta(
        result,
        source="fs:orchestration",
        stale_after_s=STATE_PIPELINE_VERSIONS_TTL_S,
        cache="miss",
        age_s=0.0,
    )


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
                    ready.append(
                        {
                            "track": track_id,
                            "num": num,
                            "slug": slug,
                            "pipeline_version": version,
                            "phase_a_ts": research_phase.get("ts"),
                            "phase_a_mode": research_phase.get("mode"),
                        }
                    )
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
    data = current_payload_for_module(level, slug, module_dir)
    path = module_dir / "llm_qg.json"
    if data is None:
        if not llm_qg_file_is_current_for_module(module_dir, path):
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
async def module_scores(track: str):
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
        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        modules = [_module_score_record(track, track_dir, num, slug) for num, slug in get_plan_slugs(track)]
        scored = sum(1 for m in modules if m["scored"])
        return {"track": track, "count": len(modules), "scored": scored, "modules": modules}

    result = await asyncio.to_thread(_compute)
    if result is None:
        return JSONResponse(status_code=404, content={"error": f"Track '{track}' not found"})
    return _with_state_meta(result, source="fs:llm_qg+status", stale_after_s=0.0, cache="miss", age_s=0.0)


@router.get("/scores/{track}/{slug}")
async def module_scores_one(track: str, slug: str):
    """One module's status + LLM-QG aggregate + per-dimension scores."""

    def _compute() -> dict[str, Any] | None:
        level_cfg = next((l for l in LEVELS if l["id"] == track), None)
        if not level_cfg:
            return None
        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        match = next((ns for ns in get_plan_slugs(track) if ns[1] == slug), None)
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
async def research_coverage(fresh: bool = Query(False)):
    """Per-track research completeness and quality."""
    if fresh:
        cache_invalidate("research_coverage")
    cached = cache_get_with_age("research_coverage", ttl=STATE_RESEARCH_COVERAGE_TTL_S)
    if cached is not None:
        value, age_s = cached
        return _with_state_meta(
            value,
            source="fs:research+dossiers",
            stale_after_s=STATE_RESEARCH_COVERAGE_TTL_S,
            cache="hit",
            age_s=age_s,
        )
    result = await asyncio.to_thread(compute_research_coverage)
    cache_set("research_coverage", result)
    return _with_state_meta(
        result,
        source="fs:research+dossiers",
        stale_after_s=STATE_RESEARCH_COVERAGE_TTL_S,
        cache="miss",
        age_s=0.0,
    )


@router.get("/research/{track_id}")
async def research_detail(track_id: str, min_score: int = 9, fresh: bool = Query(False)):
    """Per-module research quality with dimension scores, gaps, and upgrade queue."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = f"research_detail_{track_id}_{min_score}"
    if fresh:
        cache_invalidate(cache_key)
    cached = cache_get_with_age(cache_key, ttl=STATE_RESEARCH_DETAIL_TTL_S)
    if cached is not None:
        value, age_s = cached
        return _with_state_meta(
            value,
            source="fs:research+dossiers",
            stale_after_s=STATE_RESEARCH_DETAIL_TTL_S,
            cache="hit",
            age_s=age_s,
        )

    result = await asyncio.to_thread(compute_research_detail, track_id, level_cfg, min_score)
    cache_set(cache_key, result)
    return _with_state_meta(
        result,
        source="fs:research+dossiers",
        stale_after_s=STATE_RESEARCH_DETAIL_TTL_S,
        cache="miss",
        age_s=0.0,
    )


@router.get("/review-coverage")
async def review_coverage(fresh: bool = Query(False)):
    """Per-track review and final-review coverage + quality signal."""
    if fresh:
        cache_invalidate("review_coverage")
    cached = cache_get_with_age("review_coverage", ttl=STATE_REVIEW_COVERAGE_TTL_S)
    if cached is not None:
        value, age_s = cached
        return _with_state_meta(
            value,
            source="fs:review+audit",
            stale_after_s=STATE_REVIEW_COVERAGE_TTL_S,
            cache="hit",
            age_s=age_s,
        )
    result = await asyncio.to_thread(compute_review_coverage)
    cache_set("review_coverage", result)
    return _with_state_meta(
        result,
        source="fs:review+audit",
        stale_after_s=STATE_REVIEW_COVERAGE_TTL_S,
        cache="miss",
        age_s=0.0,
    )


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


@router.get("/module-range/{track_id}")
async def module_range_status(
    track_id: str,
    start: int = Query(..., ge=1),
    end: int = Query(..., ge=1),
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
    cache_key = f"module_range_{track_id}_{start}_{end}"
    cached = cache_get(cache_key, ttl=30.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(
        compute_module_range_status,
        track_id,
        level_cfg,
        start=start,
        end=end,
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
):
    """Per-module LLM quality-gate scores from build artifacts on disk."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    return await asyncio.to_thread(compute_llm_qg_track, track_id, level_cfg, verbose=verbose)


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
    track_dir = CURRICULUM_ROOT / level_cfg["path"]
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
        "shippable": bool(full.get("shippable")),
        "blocking_issues": audit.get("blocking_issues") or [],
        "retry_count": retry_count,
        "worker": current_worker,
        "llm_qg": summarize_llm_qg(llm_qg),
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


# ==================== MANIFEST (#1309) ====================


@router.get("/manifest")
async def manifest(request: Request):
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
          "session": {"hash": "...", "url": "/api/session/current?agent=orchestrator&format=markdown"},
          "orient":  {"url": "/api/orient"},
          "inbox":   {"url_template": "/api/comms/inbox?agent={name}"},
          "activity": {"url": "/api/comms/agent-activity"}
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
    from .telemetry.response import add_json_telemetry, session_id_from_request

    session_id = session_id_from_request(request)
    return add_json_telemetry(
        {
            "generated_at": _dt.now(UTC).isoformat().replace("+00:00", "Z"),
            "rules": {
                "hash": rules_hash(),
                "url": "/api/rules?format=markdown",
                "format": "markdown",
                "note": "Condensed critical + non-negotiable + workflow rules. Drop straight into a system prompt.",
            },
            "session": {
                "hash": session_hash(),
                "url": "/api/session/current?agent=orchestrator&format=markdown",
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
            "activity": {
                "url": "/api/comms/agent-activity",
                "note": "Compact channel delivery/event snapshot for orchestration.",
            },
        },
        session_id=session_id,
    )
