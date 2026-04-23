"""Dashboard API router -- unified endpoints for the ukraine-ops dashboard suite.

Mounted at /api/dashboard/ in main.py.
Endpoints: overview, track detail, module deep-dive, pipeline status, activity config,
comms monitoring.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.thresholds import REVIEW_PASS_FLOOR

from .config import CURRICULUM_ROOT, LEVELS
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
    default_research_info,
    extract_review_info,
    find_active_builds,
    get_orchestration_info,
    load_manifest,
    read_yaml_file,
    scan_pipeline_queues,
    scan_track_cached,
    scan_track_summary_cached,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audit.status_cache import get_source_paths, read_status
from research_quality import assess_research_compat, find_research_path

router = APIRouter(tags=["dashboard"])


# ==================== ENDPOINTS ====================


@router.get("/overview")
async def overview():
    """All tracks with module counts and pass/prose/fail stats."""
    manifest = load_manifest()
    levels = manifest.get("levels", {})

    tracks = []
    totals = {"pass": 0, "content_complete": 0, "fail": 0, "unaudited": 0, "missing": 0, "shippable": 0, "total": 0}

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        track_modules = levels.get(track_id, {}).get("modules", [])
        if not track_modules:
            continue

        track_data = scan_track_cached(track_id, level_cfg["path"], track_modules)
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
    manifest = load_manifest()
    levels = manifest.get("levels", {})

    tracks = []
    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        track_modules = levels.get(track_id, {}).get("modules", [])
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


@router.get("/track/{track_id}/summary")
async def track_summary(track_id: str):
    """Lightweight per-module summary: slug, status, pipeline version, review badges only."""
    manifest = load_manifest()
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")

    track_modules = manifest.get("levels", {}).get(track_id, {}).get("modules", [])
    return scan_track_summary_cached(track_id, level_cfg["path"], track_modules)


@router.get("/track/{track_id}")
async def track_detail(track_id: str):
    """Per-module detail for one track."""
    manifest = load_manifest()
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")

    track_modules = manifest.get("levels", {}).get(track_id, {}).get("modules", [])
    return scan_track_cached(track_id, level_cfg["path"], track_modules)


@router.get("/module/{track_id}/{slug}")
async def module_detail(track_id: str, slug: str):
    """Deep inspection of a single module: plan, meta, gates, orchestration."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")

    track_dir = CURRICULUM_ROOT / level_cfg["path"]
    result = {"slug": slug, "track": track_id}

    result["plan"] = read_yaml_file(CURRICULUM_ROOT / "plans" / track_id / f"{slug}.yaml")
    result["meta"] = read_yaml_file(track_dir / "meta" / f"{slug}.yaml")

    sp = get_source_paths(track_dir, slug)
    status_result = read_status(track_dir / "status" / f"{slug}.json", source_paths=sp)
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
            "last_modified": datetime.fromtimestamp(
                md_path.stat().st_mtime, tz=UTC
            ).isoformat(),
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
    orch_dir = track_dir / "orchestration" / slug
    friction_path = orch_dir / "friction.yaml"
    result["friction_active"] = 0
    result["friction_resolved"] = 0
    if friction_path.exists():
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
    from audit.config import (
        ACTIVITY_COMPLEXITY,
        ACTIVITY_RESTRICTIONS,
        LEVEL_CONFIG,
        VALID_ACTIVITY_TYPES,
    )

    types = []
    for act_type in VALID_ACTIVITY_TYPES:
        complexity = ACTIVITY_COMPLEXITY.get(act_type, {})
        available_levels = list(complexity.keys()) if complexity else []
        types.append({
            "type": act_type,
            "available_levels": available_levels,
            "complexity": complexity,
        })

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
    result["delivery_stats"] = {
        (row[0] or "pending"): row[1] for row in cur.fetchall()
    }

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
