"""Dashboard API router -- unified endpoints for the ukraine-ops dashboard suite.

Mounted at /api/dashboard/ in main.py.
Endpoints: overview, track detail, module deep-dive, pipeline status, activity config,
comms monitoring.
"""

import contextlib
import copy
import json
import logging
import os
import sys
import tempfile
import threading
from datetime import UTC, datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audit.config import ACTIVITY_COMPLEXITY, ACTIVITY_RESTRICTIONS, LEVEL_CONFIG, VALID_ACTIVITY_TYPES
from common.thresholds import REVIEW_PASS_FLOOR

from .config import CURRICULUM_ROOT, LEVELS, PROJECT_ROOT, SEMINAR_TRACK_IDS
from .dashboard_comms import (
    collect_stuck_tasks,
    ensure_broker_cols,
    fetch_broker_messages,
    get_broker_db,
    get_watcher_log_tail,
    is_watcher_running,
    read_dispatcher_state,
)
from .dashboard_helpers import (
    compute_track_stats,
    default_research_info,
    extract_review_info,
    find_active_builds,
    get_orchestration_info,
    load_manifest,
    present_module_count,
    read_yaml_file,
    scan_pipeline_queues,
    scan_track_cached,
    scan_track_summary_cached,
    stats_from_state_summary,
)
from .state_coverage import compute_summary
from .state_helpers import cache_get_with_age, cache_invalidate, cache_set, get_plan_slugs

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audit.status_cache import get_source_paths, read_status

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)
from research_quality import assess_research_compat, find_research_path

router = APIRouter(tags=["dashboard"])
logger = logging.getLogger(__name__)
DASHBOARD_STATE_SUMMARY_TTL_S = 60.0
DASHBOARD_OVERVIEW_CACHE_KEY = "dashboard_overview"
DASHBOARD_OVERVIEW_TTL_S = 60.0
DASHBOARD_OVERVIEW_LAST_GOOD_ENV = "DASHBOARD_OVERVIEW_LAST_GOOD_PATH"
_OVERVIEW_TOTAL_KEYS = (
    "pass",
    "content_complete",
    "fail",
    "unaudited",
    "missing",
    "shippable",
    "total",
    "published_mdx",
)

_overview_refresh_lock = threading.Lock()
_overview_refresh_thread: threading.Thread | None = None
_overview_last_good: dict | None = None
_overview_disk_loaded = False


def overview_last_good_path() -> Path:
    """Durable last-good snapshot written by the background overview scan."""
    override = os.environ.get(DASHBOARD_OVERVIEW_LAST_GOOD_ENV)
    if override:
        return Path(override)
    return PROJECT_ROOT / ".cache" / "dashboard_overview_last_good.json"


def reset_overview_state_for_tests() -> None:
    """Drop overview last-good + TTL cache so tests do not leak across cases.

    Skips reloading the host disk snapshot so pytest cannot pick up a
    previous Monitor process's last-good file.
    """
    global _overview_refresh_thread, _overview_last_good, _overview_disk_loaded
    thread: threading.Thread | None
    with _overview_refresh_lock:
        thread = _overview_refresh_thread
    if thread is not None:
        thread.join(timeout=2.0)
    _overview_last_good = None
    _overview_disk_loaded = True
    cache_invalidate(DASHBOARD_OVERVIEW_CACHE_KEY)
    with _overview_refresh_lock:
        _overview_refresh_thread = None


def simulate_overview_process_bounce_for_tests() -> None:
    """Clear process memory only; the durable last-good file remains."""
    global _overview_refresh_thread, _overview_last_good, _overview_disk_loaded
    thread: threading.Thread | None
    with _overview_refresh_lock:
        thread = _overview_refresh_thread
    if thread is not None:
        thread.join(timeout=2.0)
    _overview_last_good = None
    _overview_disk_loaded = False
    cache_invalidate(DASHBOARD_OVERVIEW_CACHE_KEY)
    with _overview_refresh_lock:
        _overview_refresh_thread = None


def _peek_state_summary() -> tuple[dict, str, float | None]:
    """Read the state-summary TTL cache without computing on the request path."""
    cached = cache_get_with_age("summary", ttl=DASHBOARD_STATE_SUMMARY_TTL_S)
    if cached is not None:
        value, age_s = cached
        return value, "hit", age_s
    return {}, "miss", None


def _empty_overview_totals() -> dict[str, int]:
    return {key: 0 for key in _OVERVIEW_TOTAL_KEYS}


def _overlay_research_from_summary(tracks: list[dict], state_tracks: dict) -> None:
    for track_entry in tracks:
        track_id = track_entry.get("id")
        summary_stats = state_tracks.get(track_id, {}) if isinstance(state_tracks, dict) else {}
        is_seminar = bool(track_entry.get("is_seminar") or summary_stats.get("is_seminar"))
        research_total_key = "dossier_done" if is_seminar else "research_done"
        stats = track_entry.setdefault("stats", {})
        stats["research"] = {
            **stats.get("research", {}),
            "total": summary_stats.get(research_total_key, stats.get("research", {}).get("total", 0)),
            "docs": summary_stats.get("dossier_docs", 0),
            "curriculum": summary_stats.get("dossier_curriculum", 0),
        }


def _overlay_presence_from_summary(tracks: list[dict], state_tracks: dict, totals: dict) -> None:
    """Treat published MDX as presence so Home is not 0/total-missing after a bounce.

    Does not copy published onto ``stats.pass`` — that stays audit-passing.
    """
    published_total = 0
    missing_total = 0
    research_total = 0
    for track_entry in tracks:
        track_id = track_entry.get("id")
        summary_stats = state_tracks.get(track_id, {}) if isinstance(state_tracks, dict) else {}
        published = int(summary_stats.get("published_mdx") or track_entry.get("published_mdx") or 0)
        generated = int(summary_stats.get("generated_md") or track_entry.get("generated_md") or 0)
        track_entry["published_mdx"] = published
        track_entry["generated_md"] = generated
        stats = track_entry.setdefault("stats", {})
        stats["published_mdx"] = published
        module_count = int(track_entry.get("module_count") or 0)
        scan_missing = int(stats.get("missing") or 0)
        scan_present = max(0, module_count - scan_missing) if module_count else 0
        present = present_module_count(
            total=module_count,
            generated_md=generated,
            published_mdx=published,
            scan_present=scan_present,
        )
        stats["missing"] = max(0, module_count - present)
        published_total += published
        missing_total += stats["missing"]
        research_total += int((stats.get("research") or {}).get("total") or 0)
    totals["missing"] = missing_total
    totals["published_mdx"] = published_total
    totals["research"] = research_total


def _apply_overview_summary_overlay(payload: dict, state_tracks: dict) -> None:
    tracks = payload.get("tracks") or []
    totals = payload.setdefault("totals", _empty_overview_totals())
    _overlay_research_from_summary(tracks, state_tracks)
    _overlay_presence_from_summary(tracks, state_tracks, totals)


def _atomic_write_text(path: Path, text: str) -> None:
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _usable_overview_last_good(payload: dict | None) -> dict | None:
    if not isinstance(payload, dict):
        return None
    tracks = payload.get("tracks")
    totals = payload.get("totals")
    if not isinstance(tracks, list) or not tracks:
        return None
    if not isinstance(totals, dict) or int(totals.get("total") or 0) <= 0:
        return None
    return payload


def persist_overview_last_good(payload: dict) -> None:
    """Write the full-scan overview snapshot so a Monitor bounce can reload it."""
    if _usable_overview_last_good(payload) is None:
        return
    try:
        _atomic_write_text(
            overview_last_good_path(),
            json.dumps(payload, ensure_ascii=False),
        )
    except OSError:
        logger.exception("dashboard overview last-good persist failed")


def read_persisted_overview_last_good() -> dict | None:
    path = overview_last_good_path()
    try:
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    return _usable_overview_last_good(data)


def hydrate_overview_last_good_from_disk() -> dict | None:
    """Load durable last-good into process memory once per lifetime (or bounce)."""
    global _overview_last_good, _overview_disk_loaded
    if _overview_last_good is not None:
        _overview_disk_loaded = True
        return _overview_last_good
    if _overview_disk_loaded:
        return None
    _overview_disk_loaded = True
    payload = read_persisted_overview_last_good()
    if payload is None:
        return None
    _overview_last_good = payload
    return payload


def _build_overview_from_state_summary(
    state_summary: dict,
    cache_state: str,
    age_s: float | None,
    *,
    track_scan: str,
) -> dict:
    """Assemble overview from cached summary + manifest. No per-module FS scan."""
    manifest = load_manifest()
    levels = manifest.get("levels", {})
    state_tracks = state_summary.get("tracks", {}) if isinstance(state_summary, dict) else {}

    tracks = []
    totals = _empty_overview_totals()

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        summary_stats = state_tracks.get(track_id, {})
        track_modules = levels.get(track_id, {}).get("modules", []) or [
            slug for _num, slug in get_plan_slugs(track_id)
        ]
        module_count = int(summary_stats.get("total") or 0) or len(track_modules)
        if not module_count:
            continue

        is_seminar = bool(summary_stats.get("is_seminar") or track_id in SEMINAR_TRACK_IDS)
        s = stats_from_state_summary(summary_stats, is_seminar=is_seminar)
        pct = round(s["pass"] / module_count * 100) if module_count > 0 else 0
        tracks.append(
            {
                "id": track_id,
                "name": level_cfg["name"],
                "module_count": module_count,
                "stats": s,
                "pct_complete": pct,
                "profile": summary_stats.get("profile", "seminar" if is_seminar else "core"),
                "is_seminar": is_seminar,
                "module_source": summary_stats.get("module_source"),
                "published_mdx": summary_stats.get("published_mdx", 0),
                "generated_md": summary_stats.get("generated_md", 0),
                "audit_stale": summary_stats.get("audit_stale", 0),
            }
        )
        for key in totals:
            if key == "total":
                totals["total"] += module_count
            elif key in s:
                totals[key] += s[key]

    meta = {
        "generated_at": state_summary.get("generated_at") if isinstance(state_summary, dict) else None,
        "source": "fs:manifest+state-summary",
        "cache": cache_state,
        "stale_after_s": DASHBOARD_OVERVIEW_TTL_S,
        "stale": cache_state != "hit",
        "track_scan": track_scan,
    }
    if age_s is not None:
        meta["age_s"] = round(age_s, 3)
    if cache_state == "miss" and track_scan == "skipped":
        meta["error"] = "overview_warming"
    payload = {
        "tracks": tracks,
        "totals": totals,
        "timestamp": datetime.now(UTC).isoformat(),
        "meta": meta,
    }
    _apply_overview_summary_overlay(payload, state_tracks)
    return payload


def _build_overview_payload_from_scans() -> dict:
    """Full overview including per-module status badges. Background refresh only."""
    manifest = load_manifest()
    levels = manifest.get("levels", {})
    cached = cache_get_with_age("summary", ttl=DASHBOARD_STATE_SUMMARY_TTL_S)
    if cached is not None:
        state_summary, age_s = cached
        cache_state = "hit"
    else:
        state_summary = compute_summary()
        cache_set("summary", state_summary)
        cache_state = "miss"
        age_s = 0.0
    state_tracks = state_summary.get("tracks", {})

    tracks = []
    totals = _empty_overview_totals()

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        track_modules = levels.get(track_id, {}).get("modules", []) or [
            slug for _num, slug in get_plan_slugs(track_id)
        ]
        if not track_modules:
            continue

        track_data = scan_track_summary_cached(track_id, level_cfg["path"], track_modules)
        track_data["stats"] = compute_track_stats(track_data["modules"], track_id)
        summary_stats = state_tracks.get(track_id, {})
        s = track_data["stats"]
        research_total_key = "dossier_done" if summary_stats.get("is_seminar") else "research_done"
        s["research"] = {
            **s.get("research", {}),
            "total": summary_stats.get(research_total_key, 0),
            "docs": summary_stats.get("dossier_docs", 0),
            "curriculum": summary_stats.get("dossier_curriculum", 0),
        }
        pct = round(s["pass"] / track_data["module_count"] * 100) if track_data["module_count"] > 0 else 0

        track_entry = {
            "id": track_id,
            "name": level_cfg["name"],
            "module_count": track_data["module_count"],
            "stats": s,
            "pct_complete": pct,
            "profile": summary_stats.get("profile", "seminar" if track_id in SEMINAR_TRACK_IDS else "core"),
            "is_seminar": bool(track_data.get("is_seminar") or summary_stats.get("is_seminar")),
            "module_source": summary_stats.get("module_source"),
            "published_mdx": summary_stats.get("published_mdx", 0),
            "generated_md": summary_stats.get("generated_md", 0),
            "audit_stale": summary_stats.get("audit_stale", 0),
        }
        tracks.append(track_entry)

        for key in totals:
            if key == "total":
                totals["total"] += track_data["module_count"]
            elif key in s:
                totals[key] += s[key]

    payload = {
        "tracks": tracks,
        "totals": totals,
        "timestamp": datetime.now(UTC).isoformat(),
        "meta": {
            "generated_at": state_summary.get("generated_at"),
            "source": "fs:dashboard-summary+state-summary",
            "cache": cache_state,
            "stale_after_s": DASHBOARD_OVERVIEW_TTL_S,
            "stale": False,
            "track_scan": "hit",
            **({"age_s": round(age_s, 3)} if age_s is not None else {}),
        },
    }
    _apply_overview_summary_overlay(payload, state_tracks)
    return payload


def _schedule_overview_refresh() -> None:
    global _overview_refresh_thread
    with _overview_refresh_lock:
        if _overview_refresh_thread is not None and _overview_refresh_thread.is_alive():
            return
        _overview_refresh_thread = threading.Thread(
            target=_run_overview_refresh,
            daemon=True,
            name="dashboard-overview-refresh",
        )
        _overview_refresh_thread.start()


def _overview_refresh_running() -> bool:
    with _overview_refresh_lock:
        thread = _overview_refresh_thread
    return thread is not None and thread.is_alive()


def _run_overview_refresh() -> None:
    global _overview_last_good, _overview_disk_loaded
    try:
        payload = _build_overview_payload_from_scans()
        if _usable_overview_last_good(payload) is None:
            logger.warning("dashboard overview refresh produced no tracks; keeping last-good")
            return
        cache_set(DASHBOARD_OVERVIEW_CACHE_KEY, payload)
        _overview_last_good = payload
        _overview_disk_loaded = True
        persist_overview_last_good(payload)
    except Exception:
        logger.exception("dashboard overview background refresh failed")


# ==================== ENDPOINTS ====================


@router.get("/overview")
async def overview():
    """All tracks with module counts and pass/prose/fail stats.

    The request path never walks the curriculum tree. A warm TTL cache or
    last-good full scan is returned immediately; otherwise a cheap
    manifest + cached-summary payload is served while a detached worker
    fills last-good. Last-good is also persisted to disk so a process
    bounce does not fall back to 0/total-missing. ``meta.cache`` remains
    the state-summary cache signal; ``meta.track_scan`` / ``meta.stale``
    / ``meta.error`` stay honest about whether the per-module scan has
    run. ``meta.refreshing`` is only set while warming (no last-good yet).
    """
    state_summary, cache_state, age_s = _peek_state_summary()
    state_tracks = state_summary.get("tracks", {}) if isinstance(state_summary, dict) else {}

    cached = cache_get_with_age(DASHBOARD_OVERVIEW_CACHE_KEY, ttl=DASHBOARD_OVERVIEW_TTL_S)
    if cached is not None:
        value, overview_age_s = cached
        payload = copy.deepcopy(value)
        payload["timestamp"] = datetime.now(UTC).isoformat()
        meta = dict(payload.get("meta") or {})
        meta["cache"] = cache_state
        meta["stale"] = False
        meta["track_scan"] = "hit"
        meta["stale_after_s"] = DASHBOARD_OVERVIEW_TTL_S
        meta.pop("error", None)
        meta.pop("refreshing", None)
        if cache_state == "hit" and age_s is not None:
            meta["age_s"] = round(age_s, 3)
        elif overview_age_s is not None:
            meta["age_s"] = round(overview_age_s, 3)
        _apply_overview_summary_overlay(payload, state_tracks)
        payload["meta"] = meta
        return payload

    last_good = hydrate_overview_last_good_from_disk()
    if last_good is not None:
        if not _overview_refresh_running():
            _schedule_overview_refresh()
        payload = copy.deepcopy(last_good)
        payload["timestamp"] = datetime.now(UTC).isoformat()
        meta = dict(payload.get("meta") or {})
        meta["cache"] = cache_state
        meta["stale"] = True
        meta["track_scan"] = "stale"
        meta["stale_after_s"] = DASHBOARD_OVERVIEW_TTL_S
        meta.pop("error", None)
        meta.pop("refreshing", None)
        if age_s is not None:
            meta["age_s"] = round(age_s, 3)
        _apply_overview_summary_overlay(payload, state_tracks)
        payload["meta"] = meta
        return payload

    _schedule_overview_refresh()
    payload = _build_overview_from_state_summary(
        state_summary,
        cache_state,
        age_s,
        track_scan="skipped",
    )
    payload.setdefault("meta", {})["refreshing"] = True
    return payload


@router.get("/research")
async def research_overview():
    """Research coverage across all tracks with rubric-based quality scoring."""
    manifest = load_manifest()
    levels = manifest.get("levels", {})

    tracks = []
    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        track_modules = levels.get(track_id, {}).get("modules", []) or [
            slug for _num, slug in get_plan_slugs(track_id)
        ]
        if not track_modules:
            continue

        track_data = scan_track_cached(track_id, level_cfg["path"], track_modules)
        rs = track_data["stats"].get("research", {})

        mod_research = []
        for m in track_data["modules"]:
            r = m.get("research", {})
            entry = {
                "num": m["num"],
                "slug": m["slug"],
                "exists": r.get("exists", False),
                "words": r.get("words", 0),
                "quality": r.get("quality"),
                "score": r.get("score"),
                "profile": r.get("profile"),
                "dimensions": r.get("dimensions"),
                "gaps": r.get("gaps"),
                "has_content": m["files"].get("lesson", False),
            }
            if "content_alignment" in r:
                entry["content_alignment"] = r["content_alignment"]
            mod_research.append(entry)

        tracks.append(
            {
                "id": track_id,
                "name": level_cfg["name"],
                "module_count": track_data["module_count"],
                "research_stats": rs,
                "modules": mod_research,
            }
        )

    return {
        "tracks": tracks,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/track/{track_id}/summary")
async def track_summary(track_id: str):
    """Lightweight per-module summary: slug, status, pipeline version, review badges only."""
    manifest = load_manifest()
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")

    track_modules = manifest.get("levels", {}).get(track_id, {}).get("modules", []) or [
        slug for _num, slug in get_plan_slugs(track_id)
    ]
    return scan_track_summary_cached(track_id, level_cfg["path"], track_modules)


@router.get("/track/{track_id}")
async def track_detail(track_id: str):
    """Per-module detail for one track."""
    manifest = load_manifest()
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")

    track_modules = manifest.get("levels", {}).get(track_id, {}).get("modules", []) or [
        slug for _num, slug in get_plan_slugs(track_id)
    ]
    return scan_track_cached(track_id, level_cfg["path"], track_modules)


@router.get("/module/{track_id}/{slug}")
async def module_detail(track_id: str, slug: str):
    """Deep inspection of a single module: plan, meta, gates, orchestration."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")

    try:
        track_dir = safe_join(CURRICULUM_ROOT, level_cfg["path"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid track path for {track_id}") from exc
    result = {"slug": slug, "track": track_id}

    try:
        result["plan"] = read_yaml_file(safe_join(CURRICULUM_ROOT, "plans", track_id, f"{slug}.yaml"))
        result["meta"] = read_yaml_file(safe_join(track_dir, "meta", f"{slug}.yaml"))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid track/slug: {track_id}/{slug}",
        ) from exc

    sp = get_source_paths(track_dir, slug)
    try:
        status_file = safe_join(track_dir, "status", f"{slug}.json")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid track/slug: {track_id}/{slug}") from exc
    status_result = read_status(status_file, source_paths=sp)
    result["status"] = status_result.data if status_result else None
    result["status_is_fresh"] = status_result.is_fresh if status_result else None
    result["status_stale_sources"] = status_result.stale_sources if status_result else []
    md_path = sp.get("md")
    if md_path and md_path.exists():
        content = md_path.read_text()
        sections = [line.strip() for line in content.splitlines() if line.startswith("## ")]
        result["lesson"] = {
            "word_count": len(content.split()),
            "sections": sections,
            "last_modified": datetime.fromtimestamp(md_path.stat().st_mtime, tz=UTC).isoformat(),
        }
    else:
        result["lesson"] = None

    act_path = sp.get("activities")
    if act_path and act_path.exists():
        try:
            with open(act_path) as f:
                activities = yaml.safe_load(f)
            if isinstance(activities, list):
                types = [a.get("type", "unknown") for a in activities]
                result["activities"] = {
                    "count": len(activities),
                    "types": types,
                    "unique_types": list(set(types)),
                }
            else:
                result["activities"] = None
        except Exception:
            result["activities"] = None
    else:
        result["activities"] = None

    content_path = sp.get("md")
    rp = find_research_path(track_dir, slug)
    research_info = assess_research_compat(rp, track_id, content_path) if rp else None
    result["research"] = research_info or default_research_info(track_id)

    review_info = extract_review_info(track_dir, slug)
    result["review_score"] = review_info["review_score"]
    result["review_verdict"] = review_info["review_verdict"]
    result["plan_review_verdict"] = review_info["plan_review_verdict"]

    # Shippable = audit pass + review >= REVIEW_PASS_FLOOR (#971)
    audit_status = result.get("status", {})
    overall = audit_status.get("overall", {}).get("status") if isinstance(audit_status, dict) else None
    r_score = review_info["review_score"]
    result["shippable"] = overall == "pass" and r_score is not None and r_score >= REVIEW_PASS_FLOOR

    # Friction from friction.yaml (#970)
    orch_dir = safe_join(track_dir, "orchestration", slug)
    friction_path = safe_join(orch_dir, "friction.yaml") if orch_dir else None
    result["friction_active"] = 0
    result["friction_resolved"] = 0
    if friction_path and friction_path.exists():
        try:
            fdata = yaml.safe_load(friction_path.read_text())
            for f in fdata.get("frictions", []) if fdata else []:
                if f.get("status") == "active":
                    result["friction_active"] += 1
                elif f.get("status") == "resolved":
                    result["friction_resolved"] += 1
        except Exception:
            pass

    orch_info = get_orchestration_info(orch_dir)
    result.update(orch_info)

    return result


@router.get("/pipeline")
async def pipeline_status():
    """Two-stage pipeline status: otaman queue, hetman queue, active builds."""
    active_builds = find_active_builds()
    otaman_queue, hetman_queue, final_review_queue = scan_pipeline_queues()
    broker_messages = fetch_broker_messages()
    dispatcher_state = read_dispatcher_state()

    return {
        "active_builds": active_builds,
        "otaman_queue": otaman_queue[:50],
        "hetman_queue": hetman_queue[:50],
        "final_review_queue": final_review_queue[:50],
        "otaman_queue_total": len(otaman_queue),
        "hetman_queue_total": len(hetman_queue),
        "final_review_queue_total": len(final_review_queue),
        "broker_messages": broker_messages,
        "dispatcher_state": dispatcher_state,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/activity-config")
async def activity_config():
    """Activity type reference: types, min items per level, forbidden types."""
    types = []
    for act_type in VALID_ACTIVITY_TYPES:
        complexity = ACTIVITY_COMPLEXITY.get(act_type, {})
        available_levels = list(complexity.keys()) if complexity else []
        types.append(
            {
                "type": act_type,
                "available_levels": available_levels,
                "complexity": complexity,
            }
        )

    levels = {}
    for level_key, cfg in LEVEL_CONFIG.items():
        levels[level_key] = {
            "target_words": cfg.get("target_words", 0),
            "min_activities": cfg.get("min_activities", 0),
            "min_items_per_activity": cfg.get("min_items_per_activity", 0),
            "min_types_unique": cfg.get("min_types_unique", 0),
            "priority_types": list(cfg.get("priority_types", set())),
            "required_types": list(cfg.get("required_types", set())),
            "forbidden_types": list(cfg.get("forbidden_types", set())),
        }

    restrictions = {}
    for level_key, r in ACTIVITY_RESTRICTIONS.items():
        restrictions[level_key] = {
            "forbidden": list(r.get("forbidden", [])),
        }

    return {
        "types": types,
        "levels": levels,
        "restrictions": restrictions,
    }


# ==================== COMMS MONITORING ====================


@router.get("/comms")
async def comms_status():
    """Communications monitoring: watcher health, message stats, delivery metrics."""
    result = {
        "watcher": is_watcher_running(),
        "stats": {},
        "unread": {},
        "tasks": [],
        "stuck_tasks": [],
        "recent_messages": [],
        "delivery_stats": {},
        "watcher_log_tail": [],
        "timestamp": datetime.now(UTC).isoformat(),
    }

    conn = get_broker_db()
    if not conn:
        result["error"] = "Broker database not found"
        return result

    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM messages")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM messages WHERE acknowledged = 0")
    unread_total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM messages WHERE status = 'delivery_failed'")
    failed_total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM messages WHERE message_type = 'error'")
    errors_total = cur.fetchone()[0]

    result["stats"] = {
        "total_messages": total,
        "unread": unread_total,
        "delivery_failed": failed_total,
        "errors": errors_total,
    }

    cur.execute("""
        SELECT to_llm, COUNT(*) FROM messages
        WHERE acknowledged = 0
        GROUP BY to_llm
    """)
    result["unread"] = {row[0]: row[1] for row in cur.fetchall()}

    cur.execute("""
        SELECT
            task_id,
            COUNT(*) as msg_count,
            SUM(CASE WHEN acknowledged = 0 THEN 1 ELSE 0 END) as unread,
            SUM(CASE WHEN status = 'delivery_failed' THEN 1 ELSE 0 END) as failed,
            MAX(timestamp) as last_activity,
            GROUP_CONCAT(DISTINCT from_llm) as participants
        FROM messages
        WHERE task_id IS NOT NULL
        GROUP BY task_id
        ORDER BY MAX(id) DESC
        LIMIT 20
    """)
    result["tasks"] = [
        {
            "task_id": row["task_id"],
            "message_count": row["msg_count"],
            "unread": row["unread"],
            "failed": row["failed"],
            "last_activity": row["last_activity"],
            "participants": row["participants"],
        }
        for row in cur.fetchall()
    ]

    cur.execute("""
        SELECT status, COUNT(*) FROM messages
        GROUP BY status
    """)
    result["delivery_stats"] = {(row[0] or "pending"): row[1] for row in cur.fetchall()}

    cur.execute("""
        SELECT id, task_id, from_llm, to_llm, message_type,
               SUBSTR(content, 1, 300) as content_preview,
               timestamp, acknowledged, status
        FROM messages
        ORDER BY id DESC LIMIT 50
    """)
    result["recent_messages"] = [
        {
            "id": row["id"],
            "task_id": row["task_id"],
            "from": row["from_llm"],
            "to": row["to_llm"],
            "type": row["message_type"],
            "content_preview": row["content_preview"],
            "timestamp": row["timestamp"],
            "acknowledged": bool(row["acknowledged"]),
            "status": row["status"] or "pending",
        }
        for row in cur.fetchall()
    ]

    conn.close()

    result["stuck_tasks"] = collect_stuck_tasks()
    result["watcher_log_tail"] = get_watcher_log_tail()

    return result


@router.get("/comms/message/{message_id}")
async def comms_message_detail(message_id: int):
    """Full content of a single message."""
    conn = get_broker_db()
    if not conn:
        raise HTTPException(status_code=503, detail="Broker database not found")
    cur = conn.cursor()
    cols = ensure_broker_cols(conn)
    select_cols = ["id", "task_id", "from_llm", "to_llm", "message_type", "content", "timestamp", "acknowledged"]
    if "status" in cols:
        select_cols.append("status")
    if "data" in cols:
        select_cols.append("data")
    cur.execute(f"SELECT {','.join(select_cols)} FROM messages WHERE id = ?", (message_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
    return {
        "id": row["id"],
        "task_id": row["task_id"],
        "from": row["from_llm"],
        "to": row["to_llm"],
        "type": row["message_type"],
        "content": row["content"],
        "data": row["data"] if "data" in cols else None,
        "timestamp": row["timestamp"],
        "acknowledged": bool(row["acknowledged"]),
        "status": row["status"] if "status" in cols else "unknown",
    }


@router.get("/comms/conversation/{task_id}")
async def comms_conversation(task_id: str):
    """Full conversation thread for a task, chronological order."""
    conn = get_broker_db()
    if not conn:
        raise HTTPException(status_code=503, detail="Broker database not found")
    cur = conn.cursor()
    cols = ensure_broker_cols(conn)
    select_cols = ["id", "task_id", "from_llm", "to_llm", "message_type", "content", "timestamp", "acknowledged"]
    if "status" in cols:
        select_cols.append("status")
    cur.execute(
        f"SELECT {','.join(select_cols)} FROM messages WHERE task_id = ? ORDER BY id ASC",
        (task_id,),
    )
    messages = [
        {
            "id": row["id"],
            "from": row["from_llm"],
            "to": row["to_llm"],
            "type": row["message_type"],
            "content": row["content"],
            "timestamp": row["timestamp"],
            "acknowledged": bool(row["acknowledged"]),
            "status": row["status"] if "status" in cols else "unknown",
        }
        for row in cur.fetchall()
    ]
    conn.close()
    return {"task_id": task_id, "messages": messages, "count": len(messages)}


@router.get("/comms/messages")
async def comms_messages(
    limit: int = 50,
    offset: int = 0,
    from_llm: str | None = None,
    to_llm: str | None = None,
    task_id: str | None = None,
    unread_only: bool = False,
):
    """Paginated, filterable message list."""
    conn = get_broker_db()
    if not conn:
        raise HTTPException(status_code=503, detail="Broker database not found")
    cur = conn.cursor()

    where_parts = []
    params: list = []
    if from_llm:
        where_parts.append("from_llm = ?")
        params.append(from_llm)
    if to_llm:
        where_parts.append("to_llm = ?")
        params.append(to_llm)
    if task_id:
        where_parts.append("task_id = ?")
        params.append(task_id)
    if unread_only:
        where_parts.append("acknowledged = 0")

    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    cur.execute(f"SELECT COUNT(*) FROM messages {where_clause}", params)
    total = cur.fetchone()[0]

    cur.execute(
        f"""SELECT id, task_id, from_llm, to_llm, message_type,
                   SUBSTR(content, 1, 500) as content_preview,
                   timestamp, acknowledged, status
            FROM messages {where_clause}
            ORDER BY id DESC LIMIT ? OFFSET ?""",
        [*params, limit, offset],
    )
    messages = [
        {
            "id": row["id"],
            "task_id": row["task_id"],
            "from": row["from_llm"],
            "to": row["to_llm"],
            "type": row["message_type"],
            "content_preview": row["content_preview"],
            "timestamp": row["timestamp"],
            "acknowledged": bool(row["acknowledged"]),
            "status": row["status"] or "pending",
        }
        for row in cur.fetchall()
    ]
    conn.close()
    return {"messages": messages, "total": total, "limit": limit, "offset": offset}
