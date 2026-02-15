"""
Dashboard API router — unified endpoints for the ukraine-ops dashboard suite.

Mounted at /api/dashboard/ in main.py.
Endpoints: overview, track detail, module deep-dive, pipeline status, activity config.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from .config import BATCH_STATE_DIR, CURRICULUM_ROOT, LEVELS, PROJECT_ROOT

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audit.status_cache import read_status, get_source_paths

router = APIRouter(tags=["dashboard"])


def _load_manifest() -> dict:
    manifest_path = CURRICULUM_ROOT / "curriculum.yaml"
    if not manifest_path.exists():
        return {}
    with open(manifest_path) as f:
        return yaml.safe_load(f) or {}


def _parse_slug(entry) -> str:
    if isinstance(entry, str):
        return entry.split("#")[0].strip()
    return str(entry)


def _scan_track(track_id: str, track_path: str, manifest_modules: list) -> dict:
    """Scan a single track and return module-level detail."""
    track_dir = CURRICULUM_ROOT / track_path
    plans_dir = CURRICULUM_ROOT / "plans" / track_id
    status_dir = track_dir / "status"
    meta_dir = track_dir / "meta"

    modules = []
    for idx, m_entry in enumerate(manifest_modules):
        slug = _parse_slug(m_entry)
        num = idx + 1

        # File existence
        sp = get_source_paths(track_dir, slug) if track_dir.exists() else {}
        has_md = sp.get("md") and sp["md"].exists() if sp else False
        has_meta = sp.get("meta") and sp["meta"].exists() if sp else False
        has_activities = sp.get("activities") and sp["activities"].exists() if sp else False
        has_vocab = sp.get("vocabulary") and sp["vocabulary"].exists() if sp else False
        plan_file = plans_dir / f"{slug}.yaml"
        has_plan = plan_file.exists()

        # Status
        status_file = status_dir / f"{slug}.json"
        result = read_status(status_file, source_paths=sp) if status_file.exists() else None

        # Determine state
        overall_status = "missing"
        gates = {}
        word_count = 0
        word_target = 0
        deferred_count = 0
        last_audit = None

        if result and result.data:
            overall_status = result.data.get("overall", {}).get("status", "fail")
            gates = result.data.get("gates", {})
            deferred_count = result.data.get("overall", {}).get("deferred_count", 0)
            last_audit = result.data.get("timestamp")

            # Extract word count from lesson gate message
            lesson_msg = gates.get("lesson", {}).get("message", "")
            if "/" in str(lesson_msg):
                parts = str(lesson_msg).split("/")
                try:
                    word_count = int(parts[0].strip().split()[-1]) if parts[0].strip() else 0
                except (ValueError, IndexError):
                    pass
                try:
                    word_target = int(parts[1].strip().split()[0]) if len(parts) > 1 else 0
                except (ValueError, IndexError):
                    pass
        elif has_md:
            overall_status = "unaudited"
            md_content = sp["md"].read_text() if sp.get("md") else ""
            word_count = len(md_content.split())

        # Get word target from plan if not in status
        if word_target == 0 and has_plan:
            try:
                with open(plan_file) as f:
                    plan_data = yaml.safe_load(f)
                word_target = plan_data.get("word_target", 0) if plan_data else 0
            except Exception:
                pass

        modules.append({
            "slug": slug,
            "num": num,
            "status": overall_status,
            "word_count": word_count,
            "word_target": word_target,
            "deferred_count": deferred_count,
            "gates": gates,
            "files": {
                "plan": has_plan,
                "meta": has_meta,
                "lesson": has_md,
                "activities": has_activities,
                "vocabulary": has_vocab,
            },
            "last_audit": last_audit,
            "is_fresh": result.is_fresh if result else False,
        })

    # Aggregate stats
    stats = {
        "pass": sum(1 for m in modules if m["status"] == "pass"),
        "content_complete": sum(1 for m in modules if m["status"] == "content-complete"),
        "fail": sum(1 for m in modules if m["status"] == "fail"),
        "unaudited": sum(1 for m in modules if m["status"] == "unaudited"),
        "missing": sum(1 for m in modules if m["status"] == "missing"),
    }

    return {
        "track_id": track_id,
        "track_path": track_path,
        "module_count": len(modules),
        "stats": stats,
        "modules": modules,
    }


# ==================== ENDPOINTS ====================


@router.get("/overview")
async def overview():
    """All tracks with module counts and pass/prose/fail stats."""
    manifest = _load_manifest()
    levels = manifest.get("levels", {})

    tracks = []
    totals = {"pass": 0, "content_complete": 0, "fail": 0, "unaudited": 0, "missing": 0, "total": 0}

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        track_modules = levels.get(track_id, {}).get("modules", [])
        if not track_modules:
            continue

        track_data = _scan_track(track_id, level_cfg["path"], track_modules)
        s = track_data["stats"]
        pct = round(s["pass"] / track_data["module_count"] * 100) if track_data["module_count"] > 0 else 0

        tracks.append({
            "id": track_id,
            "name": level_cfg["name"],
            "module_count": track_data["module_count"],
            "stats": s,
            "pct_complete": pct,
        })

        for key in totals:
            if key == "total":
                totals["total"] += track_data["module_count"]
            elif key in s:
                totals[key] += s[key]

    return {
        "tracks": tracks,
        "totals": totals,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/track/{track_id}")
async def track_detail(track_id: str):
    """Per-module detail for one track."""
    manifest = _load_manifest()
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")

    track_modules = manifest.get("levels", {}).get(track_id, {}).get("modules", [])
    return _scan_track(track_id, level_cfg["path"], track_modules)


@router.get("/module/{track_id}/{slug}")
async def module_detail(track_id: str, slug: str):
    """Deep inspection of a single module: plan, meta, gates, orchestration."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")

    track_dir = CURRICULUM_ROOT / level_cfg["path"]
    result = {"slug": slug, "track": track_id}

    # Plan
    plan_file = CURRICULUM_ROOT / "plans" / track_id / f"{slug}.yaml"
    if plan_file.exists():
        try:
            with open(plan_file) as f:
                result["plan"] = yaml.safe_load(f)
        except Exception:
            result["plan"] = None
    else:
        result["plan"] = None

    # Meta
    meta_file = track_dir / "meta" / f"{slug}.yaml"
    if meta_file.exists():
        try:
            with open(meta_file) as f:
                result["meta"] = yaml.safe_load(f)
        except Exception:
            result["meta"] = None
    else:
        result["meta"] = None

    # Status / gates
    status_file = track_dir / "status" / f"{slug}.json"
    if status_file.exists():
        try:
            with open(status_file) as f:
                result["status"] = json.load(f)
        except Exception:
            result["status"] = None
    else:
        result["status"] = None

    # Lesson summary
    sp = get_source_paths(track_dir, slug)
    md_path = sp.get("md")
    if md_path and md_path.exists():
        content = md_path.read_text()
        sections = [line.strip() for line in content.splitlines() if line.startswith("## ")]
        result["lesson"] = {
            "word_count": len(content.split()),
            "sections": sections,
            "last_modified": datetime.fromtimestamp(
                md_path.stat().st_mtime, tz=timezone.utc
            ).isoformat(),
        }
    else:
        result["lesson"] = None

    # Activities summary
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

    # Orchestration phases
    orch_dir = track_dir / "orchestration" / slug
    if orch_dir.exists():
        phases = []
        for f in sorted(orch_dir.iterdir(), key=lambda x: x.stat().st_mtime):
            if f.is_file():
                phases.append({
                    "file": f.name,
                    "size": f.stat().st_size,
                    "timestamp": datetime.fromtimestamp(
                        f.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                })
        result["orchestration"] = phases
    else:
        result["orchestration"] = []

    return result


@router.get("/pipeline")
async def pipeline_status():
    """Two-stage pipeline status: otaman queue, hetman queue, active builds."""
    # Active builds (orchestration dirs modified in last 15 min)
    active_builds = []
    for track_dir in CURRICULUM_ROOT.iterdir():
        if not track_dir.is_dir():
            continue
        orch_dir = track_dir / "orchestration"
        if not orch_dir.exists():
            continue
        for module_dir in orch_dir.iterdir():
            if not module_dir.is_dir():
                continue
            latest_mtime = 0
            latest_file = ""
            for f in module_dir.iterdir():
                if f.is_file() and f.stat().st_mtime > latest_mtime:
                    latest_mtime = f.stat().st_mtime
                    latest_file = f.name
            age = datetime.now().timestamp() - latest_mtime
            if age < 900:
                # Determine stage from file names
                files = [f.name for f in module_dir.iterdir() if f.is_file()]
                has_phase3 = any("phase-3" in fn for fn in files)
                has_phase7 = any("phase-7" in fn or "final-review" in fn for fn in files)
                stage = "hetman" if has_phase3 or has_phase7 else "otaman"

                active_builds.append({
                    "slug": module_dir.name,
                    "track": track_dir.name,
                    "stage": stage,
                    "latest_file": latest_file,
                    "seconds_ago": int(age),
                })

    # Scan for otaman queue (modules needing content) and hetman queue (content-complete, needs activities)
    manifest = _load_manifest()
    otaman_queue = []
    hetman_queue = []

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        status_dir = track_dir / "status"
        track_modules = manifest.get("levels", {}).get(track_id, {}).get("modules", [])

        for idx, m_entry in enumerate(track_modules):
            slug = _parse_slug(m_entry)
            status_file = status_dir / f"{slug}.json"

            if not status_file.exists():
                # No status = needs otaman
                md_exists = any(
                    (track_dir / f).exists()
                    for f in [f"{slug}.md"]
                    + [f"{idx+1:02d}-{slug}.md", f"{idx+1}-{slug}.md"]
                )
                if not md_exists:
                    otaman_queue.append({"track": track_id, "slug": slug, "num": idx + 1})
                continue

            try:
                with open(status_file) as f:
                    data = json.load(f)
                overall = data.get("overall", {}).get("status", "")
                deferred = data.get("overall", {}).get("deferred_count", 0)

                if overall == "content-complete" or deferred > 0:
                    hetman_queue.append({"track": track_id, "slug": slug, "num": idx + 1})
                elif overall == "fail":
                    # Check if it even has content
                    gates = data.get("gates", {})
                    lesson_status = gates.get("lesson", {}).get("status", "")
                    if lesson_status == "fail":
                        otaman_queue.append({"track": track_id, "slug": slug, "num": idx + 1})
            except Exception:
                pass

    # Broker messages (last 20)
    broker_messages = []
    db_path = PROJECT_ROOT / ".mcp" / "servers" / "message-broker" / "messages.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT id, task_id, from_llm, to_llm, message_type, content, timestamp, status
                FROM messages ORDER BY id DESC LIMIT 20
            """)
            broker_messages = [dict(row) for row in cur.fetchall()]
            conn.close()
        except Exception:
            pass

    # Batch dispatcher state
    dispatcher_state = {}
    ds_file = BATCH_STATE_DIR / "dispatcher_state.json"
    if ds_file.exists():
        try:
            with open(ds_file) as f:
                dispatcher_state = json.load(f)
        except Exception:
            pass

    return {
        "active_builds": active_builds,
        "otaman_queue": otaman_queue[:50],
        "hetman_queue": hetman_queue[:50],
        "otaman_queue_total": len(otaman_queue),
        "hetman_queue_total": len(hetman_queue),
        "broker_messages": broker_messages,
        "dispatcher_state": dispatcher_state,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/activity-config")
async def activity_config():
    """Activity type reference: types, min items per level, forbidden types."""
    from audit.config import (
        VALID_ACTIVITY_TYPES,
        ACTIVITY_COMPLEXITY,
        ACTIVITY_RESTRICTIONS,
        LEVEL_CONFIG,
    )

    # Build type info
    types = []
    for act_type in VALID_ACTIVITY_TYPES:
        complexity = ACTIVITY_COMPLEXITY.get(act_type, {})
        available_levels = list(complexity.keys()) if complexity else []
        types.append({
            "type": act_type,
            "available_levels": available_levels,
            "complexity": complexity,
        })

    # Build level configs (slim version)
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

    # Restrictions per level
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
