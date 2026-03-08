"""
Dashboard API router — unified endpoints for the ukraine-ops dashboard suite.

Mounted at /api/dashboard/ in main.py.
Endpoints: overview, track detail, module deep-dive, pipeline status, activity config.
"""

import json
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from .config import BATCH_STATE_DIR, CURRICULUM_ROOT, LEVELS, MESSAGE_DB, PROJECT_ROOT, SEMINAR_TRACK_IDS
from .state_router import V4_PHASE_ORDER, _detect_pipeline_version, _parse_v4_phase_status, _read_v4_state

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import contextlib

from audit.status_cache import get_source_paths, read_status
from research_quality import assess_research_compat, find_research_path, get_rubric

from .review_parsing import extract_plan_verdict, extract_review_score, extract_review_verdict

router = APIRouter(tags=["dashboard"])

# Simple TTL cache for _scan_track results
_track_cache: dict[str, tuple[float, dict]] = {}
_TRACK_CACHE_TTL = 30.0  # seconds


def _scan_track_cached(track_id: str, track_path: str, manifest_modules: list) -> dict:
    """Cached wrapper around _scan_track."""
    entry = _track_cache.get(track_id)
    if entry and (time.time() - entry[0]) < _TRACK_CACHE_TTL:
        return entry[1]
    result = _scan_track(track_id, track_path, manifest_modules)
    _track_cache[track_id] = (time.time(), result)
    return result


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
    track_dir / "meta"

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

        # Research file detection (all tracks)
        content_path = sp.get("md") if sp else None
        rp = find_research_path(track_dir, slug)
        research_info = assess_research_compat(rp, track_id, content_path) if rp else None
        if research_info is None:
            research_info = {
                "exists": False, "words": 0, "quality": None,
                "score": None, "markers": None,
                "profile": get_rubric(track_id),
                "dimensions": None, "gaps": None,
            }

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
                with contextlib.suppress(ValueError, IndexError):
                    word_count = int(parts[0].strip().split()[-1]) if parts[0].strip() else 0
                with contextlib.suppress(ValueError, IndexError):
                    word_target = int(parts[1].strip().split()[0]) if len(parts) > 1 else 0
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

        # Pipeline version detection
        orch_dir = track_dir / "orchestration" / slug
        orch_exists = orch_dir.exists()
        pipeline_version = _detect_pipeline_version(orch_dir) if orch_exists else "unbuilt"

        # Cross-agent review (Phase D) and optional final review (Phase F)
        review_file = track_dir / "review" / f"{slug}-review.md"
        has_review = review_file.exists()
        final_review_file = track_dir / "review" / f"{slug}-final-review.md"
        has_final_review = final_review_file.exists()

        # Content review score + verdict extraction
        review_score = None
        review_verdict = None
        if has_review:
            try:
                text = review_file.read_text(errors="replace")
                review_score = extract_review_score(text)
                review_verdict = extract_review_verdict(text)
            except Exception:
                pass

        # Plan review (from /plan-review skill)
        plan_review_file = track_dir / "audit" / f"{slug}-plan-review.md"
        has_plan_review = plan_review_file.exists()
        plan_review_verdict = None
        if has_plan_review:
            try:
                text = plan_review_file.read_text(errors="replace")
                plan_review_verdict = extract_plan_verdict(text)
            except Exception:
                pass

        # Friction count from orchestration
        friction_count = 0
        if orch_exists:
            friction_count = sum(1 for _ in orch_dir.glob("*friction*"))

        mod = {
            "slug": slug,
            "num": num,
            "pipeline_version": pipeline_version,
            "needs_rebuild": pipeline_version != "v4",
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
                "review": has_review,
                "final_review": has_final_review,
                "plan_review": has_plan_review,
            },
            "has_review": has_review,
            "has_final_review": has_final_review,
            "review_score": review_score,
            "review_verdict": review_verdict,
            "has_plan_review": has_plan_review,
            "plan_review_verdict": plan_review_verdict,
            "friction_count": friction_count,
            "last_audit": last_audit,
            "is_fresh": result.is_fresh if result else False,
        }
        mod["research"] = research_info
        modules.append(mod)

    # Aggregate stats
    is_seminar = track_id in SEMINAR_TRACK_IDS
    stats = {
        "pass": sum(1 for m in modules if m["status"] == "pass"),
        "content_complete": sum(1 for m in modules if m["status"] == "content-complete"),
        "fail": sum(1 for m in modules if m["status"] == "fail"),
        "unaudited": sum(1 for m in modules if m["status"] == "unaudited"),
        "missing": sum(1 for m in modules if m["status"] == "missing"),
        "reviewed": sum(1 for m in modules if m.get("has_review")),
        "final_review": sum(1 for m in modules if m.get("has_final_review")),
        "plan_reviewed": sum(1 for m in modules if m.get("has_plan_review")),
        "plan_pass": sum(1 for m in modules if m.get("plan_review_verdict") == "PASS"),
        "plan_needs_fixes": sum(1 for m in modules if m.get("plan_review_verdict") == "NEEDS FIXES"),
        "plan_fail": sum(1 for m in modules if m.get("plan_review_verdict") == "FAIL"),
    }

    # Research stats (all tracks)
    rubric_name = get_rubric(track_id)
    research_total = sum(1 for m in modules if m.get("research", {}).get("exists"))
    research_stats = {
        "total": research_total,
        "profile": rubric_name,
    }
    if rubric_name:
        for label in ["exemplary", "solid", "adequate", "thin", "stub"]:
            research_stats[label] = sum(
                1 for m in modules if m.get("research", {}).get("quality") == label
            )
    stats["research"] = research_stats

    return {
        "track_id": track_id,
        "track_path": track_path,
        "module_count": len(modules),
        "is_seminar": is_seminar,
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

        track_data = _scan_track_cached(track_id, level_cfg["path"], track_modules)
        s = track_data["stats"]
        pct = round(s["pass"] / track_data["module_count"] * 100) if track_data["module_count"] > 0 else 0

        track_entry = {
            "id": track_id,
            "name": level_cfg["name"],
            "module_count": track_data["module_count"],
            "stats": s,
            "pct_complete": pct,
        }
        if track_data.get("is_seminar"):
            track_entry["is_seminar"] = True
        tracks.append(track_entry)

        for key in totals:
            if key == "total":
                totals["total"] += track_data["module_count"]
            elif key in s:
                totals[key] += s[key]

    return {
        "tracks": tracks,
        "totals": totals,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/research")
async def research_overview():
    """Research coverage across all tracks with rubric-based quality scoring."""
    manifest = _load_manifest()
    levels = manifest.get("levels", {})

    tracks = []
    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        track_modules = levels.get(track_id, {}).get("modules", [])
        if not track_modules:
            continue

        track_data = _scan_track_cached(track_id, level_cfg["path"], track_modules)
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

        tracks.append({
            "id": track_id,
            "name": level_cfg["name"],
            "module_count": track_data["module_count"],
            "research_stats": rs,
            "modules": mod_research,
        })

    return {
        "tracks": tracks,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/track/{track_id}")
async def track_detail(track_id: str):
    """Per-module detail for one track."""
    manifest = _load_manifest()
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")

    track_modules = manifest.get("levels", {}).get(track_id, {}).get("modules", [])
    return _scan_track_cached(track_id, level_cfg["path"], track_modules)


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
                md_path.stat().st_mtime, tz=UTC
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

    # Research (all tracks)
    content_path = sp.get("md")
    rp = find_research_path(track_dir, slug)
    research_info = assess_research_compat(rp, track_id, content_path) if rp else None
    result["research"] = research_info or {
        "exists": False, "words": 0, "quality": None,
        "score": None, "markers": None,
        "profile": get_rubric(track_id),
        "dimensions": None, "gaps": None,
    }

    # Content review score + verdict
    review_file = track_dir / "review" / f"{slug}-review.md"
    if review_file.exists():
        try:
            text = review_file.read_text(errors="replace")
            result["review_score"] = extract_review_score(text)
            result["review_verdict"] = extract_review_verdict(text)
        except Exception:
            result["review_score"] = None
            result["review_verdict"] = None
    else:
        result["review_score"] = None
        result["review_verdict"] = None

    # Plan review verdict
    plan_review_file = track_dir / "audit" / f"{slug}-plan-review.md"
    if plan_review_file.exists():
        try:
            text = plan_review_file.read_text(errors="replace")
            result["plan_review_verdict"] = extract_plan_verdict(text)
        except Exception:
            result["plan_review_verdict"] = None
    else:
        result["plan_review_verdict"] = None

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
                        f.stat().st_mtime, tz=UTC
                    ).isoformat(),
                })
        result["orchestration"] = phases
        result["friction_count"] = sum(1 for _ in orch_dir.glob("*friction*"))

        # Pipeline version + v4 phase status
        version = _detect_pipeline_version(orch_dir)
        result["pipeline_version"] = version
        result["needs_rebuild"] = version != "v4"
        if version == "v4":
            v4 = _read_v4_state(orch_dir)
            result["v4_phases"] = {
                name: _parse_v4_phase_status(v4, name)
                for name in V4_PHASE_ORDER
            }
    else:
        result["orchestration"] = []
        result["friction_count"] = 0
        result["pipeline_version"] = "unbuilt"
        result["needs_rebuild"] = True

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
    final_review_queue = []

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
                    for f in [f"{slug}.md", f"{idx + 1:02d}-{slug}.md", f"{idx + 1}-{slug}.md"]
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
                elif overall == "pass":
                    # Check if Claude final review exists
                    review_file = track_dir / "review" / f"{slug}-final-review.md"
                    if not review_file.exists():
                        final_review_queue.append({"track": track_id, "slug": slug, "num": idx + 1})
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
    from audit.config import (
        ACTIVITY_COMPLEXITY,
        ACTIVITY_RESTRICTIONS,
        LEVEL_CONFIG,
        VALID_ACTIVITY_TYPES,
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


# ==================== COMMS MONITORING ====================

# Schema column check for backward compat
_BROKER_COLS: set | None = None


def _ensure_broker_cols(conn: sqlite3.Connection) -> set:
    """Cache the column names of the messages table."""
    global _BROKER_COLS
    if _BROKER_COLS is None:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(messages)")
        _BROKER_COLS = {row[1] for row in cur.fetchall()}
    return _BROKER_COLS

WATCHER_PID_FILE = PROJECT_ROOT / ".mcp" / "servers" / "message-broker" / "watcher.pid"
WATCHER_LOG_FILE = PROJECT_ROOT / ".mcp" / "servers" / "message-broker" / "watcher.log"
STUCK_DIR = CURRICULUM_ROOT / "stuck"


def _get_broker_db():
    """Get a read-only connection to the broker SQLite database."""
    if not MESSAGE_DB.exists():
        return None
    conn = sqlite3.connect(str(MESSAGE_DB))
    conn.row_factory = sqlite3.Row
    return conn


def _is_watcher_running() -> dict:
    """Check watcher daemon health."""
    import os
    pid = None
    running = False
    if WATCHER_PID_FILE.exists():
        try:
            pid = int(WATCHER_PID_FILE.read_text().strip())
            os.kill(pid, 0)  # Check if process exists
            running = True
        except (ValueError, OSError):
            pass
    return {"running": running, "pid": pid}


@router.get("/comms")
async def comms_status():
    """Communications monitoring: watcher health, message stats, delivery metrics."""
    result = {
        "watcher": _is_watcher_running(),
        "stats": {},
        "unread": {},
        "tasks": [],
        "stuck_tasks": [],
        "recent_messages": [],
        "delivery_stats": {},
        "watcher_log_tail": [],
        "timestamp": datetime.now(UTC).isoformat(),
    }

    conn = _get_broker_db()
    if not conn:
        result["error"] = "Broker database not found"
        return result

    cur = conn.cursor()

    # Overall message stats
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

    # Unread per agent
    cur.execute("""
        SELECT to_llm, COUNT(*) FROM messages
        WHERE acknowledged = 0
        GROUP BY to_llm
    """)
    result["unread"] = {row[0]: row[1] for row in cur.fetchall()}

    # Active tasks with stats
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

    # Delivery stats by status
    cur.execute("""
        SELECT status, COUNT(*) FROM messages
        GROUP BY status
    """)
    result["delivery_stats"] = {
        (row[0] or "pending"): row[1] for row in cur.fetchall()
    }

    # Recent messages (last 50) with full acknowledge/status info
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

    # Stuck tasks (from filesystem)
    if STUCK_DIR.exists():
        for f in sorted(STUCK_DIR.glob("*.md")):
            try:
                text = f.read_text()
                result["stuck_tasks"].append({
                    "file": f.name,
                    "task_id": f.stem,
                    "preview": text[:300],
                })
            except Exception:
                pass

    # Also check track-specific stuck dirs
    for track_dir in CURRICULUM_ROOT.iterdir():
        stuck_sub = track_dir / "stuck"
        if stuck_sub.exists() and stuck_sub.is_dir():
            for f in sorted(stuck_sub.glob("*.md")):
                try:
                    text = f.read_text()
                    result["stuck_tasks"].append({
                        "file": f"{track_dir.name}/{f.name}",
                        "task_id": f.stem,
                        "preview": text[:300],
                    })
                except Exception:
                    pass

    # Watcher log tail (last 20 lines)
    if WATCHER_LOG_FILE.exists():
        try:
            lines = WATCHER_LOG_FILE.read_text().splitlines()[-20:]
            result["watcher_log_tail"] = lines
        except Exception:
            pass

    return result


@router.get("/comms/message/{message_id}")
async def comms_message_detail(message_id: int):
    """Full content of a single message."""
    conn = _get_broker_db()
    if not conn:
        raise HTTPException(status_code=503, detail="Broker database not found")
    cur = conn.cursor()
    cols = _ensure_broker_cols(conn)
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
    conn = _get_broker_db()
    if not conn:
        raise HTTPException(status_code=503, detail="Broker database not found")
    cur = conn.cursor()
    cols = _ensure_broker_cols(conn)
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
    conn = _get_broker_db()
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
