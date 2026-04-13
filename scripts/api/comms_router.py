"""
Comms API router — agent communication monitoring, batch progress, zombie detection.

Mounted at /api/comms/ in main.py.

Endpoints:
  GET /api/comms/messages              All messages (filterable)
  GET /api/comms/conversations         Grouped by task_id
  GET /api/comms/conversation/{id}     Full thread
  GET /api/comms/active-processes      Live bridge PIDs
  GET /api/comms/zombies               Stuck patterns
  GET /api/comms/stats                 Rate, latency, error %
  GET /api/comms/health                Broker DB health
  GET /api/comms/batch-progress        Live preseed/batch progress per track
  POST /api/comms/cleanup              Force-ack zombies
  POST /api/comms/acknowledge/{id}     Ack single message
"""

import json
import os
import re
import sqlite3
import time
from datetime import UTC, datetime

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import CURRICULUM_ROOT, MESSAGE_DB, PROJECT_ROOT

router = APIRouter(tags=["comms"])

# ==================== DB HELPERS ====================

PID_DIR = PROJECT_ROOT / ".mcp" / "servers" / "message-broker" / "pids"
LOG_DIR = PROJECT_ROOT / "logs" / "research-preseed"


def _get_db() -> sqlite3.Connection | None:
    """Get read-only broker DB connection. Returns None if DB missing."""
    if not MESSAGE_DB.exists():
        return None
    conn = sqlite3.connect(f"file:{MESSAGE_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _get_rw_db() -> sqlite3.Connection | None:
    """Get read-write broker DB connection."""
    if not MESSAGE_DB.exists():
        return None
    conn = sqlite3.connect(str(MESSAGE_DB))
    conn.row_factory = sqlite3.Row
    return conn


# ==================== MESSAGES (legacy broker) ====================
#
# Everything in this section reads/writes the legacy `messages` table
# backing the ask-claude / ask-gemini / ask-codex CLI commands. It is
# DEPRECATED for new conversations as of #1190 Phase B.5, but kept
# alive because 3 scripts still depend on ask-* (scripts/wiki/compile.py,
# scripts/audit/naturalness_check.py, scripts/batch/batch_fix_review.py).
# For new multi-agent conversations, code reviews, and design debates,
# use the channel bridge endpoints under /api/comms/channels/* and the
# `ab channel` / `ab post` / `ab discuss` CLI commands.
#
# Removal target: once the remaining ask-* consumers are migrated, an
# ADR in docs/decisions/ will set an expiry date and these routes can
# be yanked. Until then, they stay.


@router.get("/messages", deprecated=True)
async def list_messages(
    agent: str | None = Query(None, description="Filter by from_llm or to_llm"),
    task_id: str | None = Query(None),
    msg_type: str | None = Query(None),
    unacked_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """**Deprecated (#1190 B.5).** All broker messages with optional filters.

    Use /api/comms/channels/{name}/messages for channel-based
    conversations. Still backs the legacy comms.html Messages tab
    and the ask-* CLI path.
    """
    conn = _get_db()
    if not conn:
        return {"messages": [], "total": 0, "error": "Broker DB not found"}

    conditions = []
    params = []

    if agent:
        conditions.append("(from_llm = ? OR to_llm = ?)")
        params.extend([agent, agent])
    if task_id:
        conditions.append("task_id = ?")
        params.append(task_id)
    if msg_type:
        conditions.append("message_type = ?")
        params.append(msg_type)
    if unacked_only:
        conditions.append("acknowledged = 0")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    total = conn.execute(f"SELECT COUNT(*) FROM messages {where}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT id, task_id, from_llm, to_llm, message_type, "
        f"substr(content, 1, 300) as preview, length(content) as content_len, "
        f"timestamp, acknowledged "
        f"FROM messages {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()
    conn.close()

    return {
        "total": total,
        "messages": [dict(r) for r in rows],
    }


@router.get("/conversations", deprecated=True)
async def list_conversations(limit: int = Query(50, ge=1, le=200)):
    """**Deprecated (#1190 B.5).** Broker messages grouped by task_id.

    Use /api/comms/channels/{name}/threads/{thread_id} for
    channel-based threads.
    """
    conn = _get_db()
    if not conn:
        return {"conversations": []}

    rows = conn.execute("""
        SELECT task_id,
               COUNT(*) as msg_count,
               COUNT(CASE WHEN acknowledged = 0 THEN 1 END) as unacked,
               MIN(timestamp) as first_msg,
               MAX(timestamp) as last_msg,
               GROUP_CONCAT(DISTINCT from_llm) as agents,
               COUNT(CASE WHEN message_type = 'error' THEN 1 END) as errors
        FROM messages
        WHERE task_id IS NOT NULL AND task_id != ''
        GROUP BY task_id
        ORDER BY MAX(id) DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    return {"conversations": [dict(r) for r in rows]}


@router.get("/conversation/{task_id}", deprecated=True)
async def get_conversation(task_id: str):
    """**Deprecated (#1190 B.5).** Full broker thread for one task_id.

    Use /api/comms/channels/{name}/threads/{thread_id} for
    channel-based threads.
    """
    conn = _get_db()
    if not conn:
        return {"messages": []}

    rows = conn.execute("""
        SELECT id, task_id, from_llm, to_llm, message_type,
               substr(content, 1, 500) as preview, length(content) as content_len,
               data, timestamp, acknowledged
        FROM messages
        WHERE task_id = ?
        ORDER BY id ASC
    """, (task_id,)).fetchall()
    conn.close()

    return {"task_id": task_id, "count": len(rows), "messages": [dict(r) for r in rows]}


# ==================== ACTIVE PROCESSES ====================


@router.get("/active-processes")
async def active_processes():
    """Live bridge PIDs with health status."""
    if not PID_DIR.exists():
        return {"processes": [], "count": 0}

    processes = []
    for pf in sorted(PID_DIR.glob("*.json")):
        try:
            data = json.loads(pf.read_text())
            pid = data.get("pid", 0)
            alive = False
            try:
                os.kill(pid, 0)
                alive = True
            except (ProcessLookupError, PermissionError):
                pass

            started = data.get("started", "")
            age_min = 0
            if started:
                try:
                    st = datetime.fromisoformat(started)
                    age_min = (datetime.now(UTC) - st).total_seconds() / 60
                except (ValueError, TypeError):
                    pass

            processes.append({
                "file": pf.name,
                "pid": pid,
                "alive": alive,
                "agent": data.get("agent", ""),
                "task_id": data.get("task_id", ""),
                "model": data.get("model", ""),
                "mode": data.get("mode", ""),
                "started": started,
                "age_minutes": round(age_min, 1),
            })
        except Exception:
            processes.append({"file": pf.name, "error": "corrupt"})

    return {"count": len(processes), "alive": sum(1 for p in processes if p.get("alive")), "processes": processes}


# ==================== ZOMBIES ====================


@router.get("/zombies")
async def detect_zombies(
    stale_hours: float = Query(2.0, description="Unacked messages older than this = stale"),
    pingpong_threshold: int = Query(5, description="Round-trips on same task in 1h = loop"),
):
    """Auto-detect stuck patterns."""
    conn = _get_db()
    zombies = []

    if conn:
        now = datetime.now(UTC)

        # 1. Stale unacked messages
        rows = conn.execute(
            "SELECT id, task_id, from_llm, to_llm, message_type, timestamp, "
            "substr(content, 1, 100) as preview "
            "FROM messages WHERE acknowledged = 0 ORDER BY id"
        ).fetchall()

        for r in rows:
            try:
                ts = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))
                age_h = (now - ts).total_seconds() / 3600
                if age_h > stale_hours:
                    zombies.append({
                        "type": "stale_message",
                        "severity": "warning" if age_h < stale_hours * 2 else "critical",
                        "message_id": r["id"],
                        "task_id": r["task_id"],
                        "from": r["from_llm"],
                        "to": r["to_llm"],
                        "age_hours": round(age_h, 1),
                        "preview": r["preview"],
                    })
            except (ValueError, TypeError):
                pass

        # 2. Ping-pong detection (rapid back-and-forth)
        task_rows = conn.execute("""
            SELECT task_id, COUNT(*) as cnt,
                   MIN(timestamp) as first_ts, MAX(timestamp) as last_ts
            FROM messages
            WHERE task_id IS NOT NULL
              AND timestamp > datetime('now', '-1 hour')
            GROUP BY task_id
            HAVING COUNT(*) >= ?
        """, (pingpong_threshold,)).fetchall()

        for r in task_rows:
            zombies.append({
                "type": "pingpong",
                "severity": "warning",
                "task_id": r["task_id"],
                "message_count_1h": r["cnt"],
                "first_ts": r["first_ts"],
                "last_ts": r["last_ts"],
            })

        # 3. Error loops (3+ consecutive errors on same task)
        error_rows = conn.execute("""
            SELECT task_id, COUNT(*) as err_count
            FROM messages
            WHERE message_type = 'error'
              AND task_id IS NOT NULL
            GROUP BY task_id
            HAVING COUNT(*) >= 3
        """).fetchall()

        for r in error_rows:
            zombies.append({
                "type": "error_loop",
                "severity": "critical",
                "task_id": r["task_id"],
                "error_count": r["err_count"],
            })

        conn.close()

    # 4. Orphan PID files
    if PID_DIR.exists():
        for pf in PID_DIR.glob("*.json"):
            try:
                data = json.loads(pf.read_text())
                pid = data.get("pid", 0)
                try:
                    os.kill(pid, 0)
                except (ProcessLookupError, PermissionError):
                    zombies.append({
                        "type": "orphan_pid",
                        "severity": "warning",
                        "file": pf.name,
                        "pid": pid,
                        "task_id": data.get("task_id", ""),
                    })
            except Exception:
                zombies.append({"type": "corrupt_pid", "severity": "warning", "file": pf.name})

    return {"count": len(zombies), "zombies": zombies}


# ==================== STATS ====================


@router.get("/stats")
async def comms_stats():
    """Message rate, latency, error %, per-agent breakdown."""
    conn = _get_db()
    if not conn:
        return {"error": "Broker DB not found"}

    total = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    unacked = conn.execute("SELECT COUNT(*) FROM messages WHERE acknowledged = 0").fetchone()[0]
    errors = conn.execute("SELECT COUNT(*) FROM messages WHERE message_type = 'error'").fetchone()[0]

    # Per-agent counts
    agent_stats = {}
    for row in conn.execute(
        "SELECT from_llm, COUNT(*) as sent FROM messages GROUP BY from_llm"
    ).fetchall():
        agent_stats[row["from_llm"]] = {"sent": row["sent"]}
    for row in conn.execute(
        "SELECT to_llm, COUNT(*) as received FROM messages GROUP BY to_llm"
    ).fetchall():
        agent_stats.setdefault(row["to_llm"], {})["received"] = row["received"]

    # Messages in last hour
    last_hour = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE timestamp > datetime('now', '-1 hour')"
    ).fetchone()[0]

    # Messages in last 24h
    last_24h = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE timestamp > datetime('now', '-24 hours')"
    ).fetchone()[0]

    # Task count
    tasks = conn.execute(
        "SELECT COUNT(DISTINCT task_id) FROM messages WHERE task_id IS NOT NULL"
    ).fetchone()[0]

    conn.close()

    return {
        "total_messages": total,
        "unacked": unacked,
        "errors": errors,
        "error_rate": round(errors / total * 100, 1) if total > 0 else 0,
        "last_hour": last_hour,
        "last_24h": last_24h,
        "total_tasks": tasks,
        "per_agent": agent_stats,
    }


# ==================== HEALTH ====================


@router.get("/health")
async def broker_health():
    """Broker DB writable, queue depth."""
    health = {
        "db_exists": MESSAGE_DB.exists(),
        "db_writable": False,
        "db_size_kb": 0,
        "queue_depth": 0,
        "pid_dir_exists": PID_DIR.exists(),
        "alive_processes": 0,
    }

    if MESSAGE_DB.exists():
        health["db_size_kb"] = round(MESSAGE_DB.stat().st_size / 1024, 1)
        try:
            conn = sqlite3.connect(str(MESSAGE_DB))
            conn.execute("SELECT 1")
            health["db_writable"] = True
            health["queue_depth"] = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE acknowledged = 0"
            ).fetchone()[0]
            conn.close()
        except Exception:
            pass

    if PID_DIR.exists():
        for pf in PID_DIR.glob("*.json"):
            try:
                data = json.loads(pf.read_text())
                os.kill(data.get("pid", 0), 0)
                health["alive_processes"] += 1
            except Exception:
                pass

    return health


# ==================== BATCH PROGRESS ====================


def _scan_preseed_logs() -> list[dict]:
    """Scan preseed log files for progress info."""
    if not LOG_DIR.exists():
        return []

    # Find the most recent batch of logs (same timestamp suffix)
    log_files = sorted(LOG_DIR.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not log_files:
        return []

    # Group by timestamp suffix (e.g., 20260220-0110)
    latest_ts = None
    for lf in log_files:
        m = re.search(r"-(\d{8}-\d{4})\.log$", lf.name)
        if m:
            latest_ts = m.group(1)
            break

    if not latest_ts:
        return []

    results = []
    for lf in LOG_DIR.glob(f"*-{latest_ts}.log"):
        track = lf.name.replace(f"-{latest_ts}.log", "")
        stat = lf.stat()

        # Parse log for progress
        text = lf.read_text(errors="replace")
        passed = len(re.findall(r"VERDICT: PASS", text))
        failed = len(re.findall(r"VERDICT: FAIL|FAILED —|ERROR:", text))

        # Get last meaningful line
        lines = text.strip().split("\n")
        last_line = ""
        for line in reversed(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("="):
                last_line = stripped[:150]
                break

        # Check if batch is complete
        batch_complete = "BATCH COMPLETE" in text
        batch_match = re.search(r"Passed:\s+(\d+)", text)
        int(batch_match.group(1)) if batch_match else passed

        results.append({
            "track": track,
            "log_file": lf.name,
            "log_size_kb": round(stat.st_size / 1024, 1),
            "last_modified": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
            "age_seconds": int(time.time() - stat.st_mtime),
            "passed": passed,
            "failed": failed,
            "complete": batch_complete,
            "last_line": last_line,
        })

    return sorted(results, key=lambda r: r["track"])


def _scan_track_progress(track: str) -> dict:
    """Count research files and check running processes for a track."""
    track_dir = CURRICULUM_ROOT / track
    research_dir = track_dir / "research"

    research_files = []
    if research_dir.exists():
        for rf in research_dir.glob("*-research.md"):
            research_files.append({
                "slug": rf.stem.replace("-research", ""),
                "mtime": rf.stat().st_mtime,
            })

    # Count total expected from curriculum.yaml
    total_expected = 0
    try:
        import yaml
        curriculum_yaml = CURRICULUM_ROOT / "curriculum.yaml"
        if curriculum_yaml.exists():
            data = yaml.safe_load(curriculum_yaml.read_text()) or {}
            modules = data.get("levels", {}).get(track, {}).get("modules", [])
            total_expected = len(modules)
    except Exception:
        pass

    # Recent files (last 30 min)
    now = time.time()
    recent = [f for f in research_files if (now - f["mtime"]) < 1800]

    # Throughput: files created in last 30 min, annualized to per-hour
    throughput_per_hour = round(len(recent) * 2, 1) if recent else 0

    # Last file created
    last_created = None
    if research_files:
        newest = max(research_files, key=lambda f: f["mtime"])
        last_created = {
            "slug": newest["slug"],
            "seconds_ago": int(now - newest["mtime"]),
        }

    return {
        "track": track,
        "total_expected": total_expected,
        "research_done": len(research_files),
        "remaining": max(0, total_expected - len(research_files)),
        "recent_30min": len(recent),
        "throughput_per_hour": throughput_per_hour,
        "last_created": last_created,
    }


def _check_build_processes() -> list[dict]:
    """Find running build_module_v5.py (or legacy build_module.py) processes."""
    import subprocess
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True, text=True, timeout=5,
        )
        procs = []
        for line in result.stdout.splitlines():
            if "build_module" in line and "python" in line.lower():
                parts = line.split()
                pid = int(parts[1])
                # Extract track from command line
                track_match = re.search(r"build_module(?:_v5)?\.py\s+(\S+)", line)
                track = track_match.group(1) if track_match else "unknown"
                version = "v5" if "build_module_v5" in line else "legacy"
                procs.append({
                    "pid": pid,
                    "track": track,
                    "version": version,
                    "cmd": " ".join(parts[10:])[:200],
                })
        return procs
    except Exception:
        return []


@router.get("/batch-progress")
async def batch_progress():
    """Live batch progress: logs + research files + running processes.

    This is the main endpoint for monitoring overnight/background builds.
    """
    import asyncio

    logs, processes = await asyncio.gather(
        asyncio.to_thread(_scan_preseed_logs),
        asyncio.to_thread(_check_build_processes),
    )

    # Get all tracks that have logs or processes
    all_tracks = set()
    for log in logs:
        all_tracks.add(log["track"])
    for proc in processes:
        all_tracks.add(proc["track"])

    # Scan each track's actual file progress
    track_progress = {}
    for track in sorted(all_tracks):
        tp = await asyncio.to_thread(_scan_track_progress, track)

        # Find matching log
        log = next((l for l in logs if l["track"] == track), None)

        # Find matching process
        proc = next((p for p in processes if p["track"] == track), None)

        # Determine health status
        if log and log["complete"]:
            health = "complete"
        elif proc:
            health = "healthy" if tp["recent_30min"] > 0 or (log and log["age_seconds"] < 900) else "stalled"
        elif log and not log["complete"] and log["age_seconds"] > 600:
            health = "dead"
        else:
            health = "unknown"

        track_progress[track] = {
            **tp,
            "health": health,
            "log": log,
            "process": proc,
        }

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "running_processes": len(processes),
        "tracks": track_progress,
    }


@router.get("/batch-progress/{track}")
async def batch_progress_track(track: str):
    """Detailed progress for one track."""
    import asyncio

    tp = await asyncio.to_thread(_scan_track_progress, track)

    # Get research file timeline (last 20 files)
    research_dir = CURRICULUM_ROOT / track / "research"
    timeline = []
    if research_dir.exists():
        files = sorted(research_dir.glob("*-research.md"), key=lambda f: f.stat().st_mtime, reverse=True)
        now = time.time()
        for rf in files[:20]:
            timeline.append({
                "slug": rf.stem.replace("-research", ""),
                "created_ago_seconds": int(now - rf.stat().st_mtime),
                "created_at": datetime.fromtimestamp(rf.stat().st_mtime, tz=UTC).isoformat(),
                "size_kb": round(rf.stat().st_size / 1024, 1),
            })

    return {**tp, "recent_files": timeline}


# ==================== LIVE ACTIVITY ====================


def _scan_live_activity(minutes: int = 15) -> list[dict]:
    """Scan legacy and v6 state files for live module-level activity."""
    now = time.time()
    cutoff = now - (minutes * 60)
    activities = []

    # 1. Scan all orchestration state files modified recently
    for track_dir in CURRICULUM_ROOT.iterdir():
        if not track_dir.is_dir():
            continue
        orch_dir = track_dir / "orchestration"
        if not orch_dir.exists():
            continue
        track = track_dir.name
        for module_dir in orch_dir.iterdir():
            if not module_dir.is_dir():
                continue
            state_files = [
                module_dir / "state.json",
                module_dir / "state-v3.json",
            ]
            recent_state_file = None
            recent_mtime = 0.0
            for state_file in state_files:
                if not state_file.exists():
                    continue
                mtime = state_file.stat().st_mtime
                if mtime < cutoff or mtime <= recent_mtime:
                    continue
                recent_state_file = state_file
                recent_mtime = mtime
            if recent_state_file is None:
                continue

            try:
                state = json.loads(recent_state_file.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            slug = state.get("slug", module_dir.name)
            phases = state.get("phases", {})

            # Find the latest phase
            latest_phase = None
            latest_ts = ""
            for phase_key, phase_data in phases.items():
                ts = phase_data.get("ts", "")
                if ts > latest_ts:
                    latest_ts = ts
                    latest_phase = phase_key

            if not latest_phase:
                continue

            phase_data = phases[latest_phase]
            phase_status = phase_data.get("status", "unknown")

            # Check if there are recently modified files in the module dir
            # (indicates active work beyond just the state file)
            recent_files = []
            for f in module_dir.iterdir():
                if f.is_file() and f.stat().st_mtime > cutoff:
                    recent_files.append(f.name)

            activities.append({
                "track": track,
                "slug": slug,
                "phase": latest_phase.replace("v3-", "Phase "),
                "phase_status": phase_status,
                "timestamp": latest_ts,
                "seconds_ago": int(now - recent_mtime),
                "task_id": phase_data.get("task_id", ""),
                "mode": phase_data.get("mode", ""),
                "recent_files": recent_files,
            })

    # Sort by most recent first
    activities.sort(key=lambda a: a["seconds_ago"])
    return activities


def _scan_recent_completions(minutes: int = 60) -> list[dict]:
    """Scan research files created recently for a completion feed."""
    now = time.time()
    cutoff = now - (minutes * 60)
    completions = []

    for track_dir in CURRICULUM_ROOT.iterdir():
        if not track_dir.is_dir():
            continue
        research_dir = track_dir / "research"
        if not research_dir.exists():
            continue
        track = track_dir.name
        for rf in research_dir.glob("*-research.md"):
            mtime = rf.stat().st_mtime
            if mtime < cutoff:
                continue
            completions.append({
                "track": track,
                "slug": rf.stem.replace("-research", ""),
                "type": "research",
                "seconds_ago": int(now - mtime),
                "size_kb": round(rf.stat().st_size / 1024, 1),
                "timestamp": datetime.fromtimestamp(mtime, tz=UTC).isoformat(),
            })

    completions.sort(key=lambda c: c["seconds_ago"])
    return completions


@router.get("/live-activity")
async def live_activity(minutes: int = Query(15, ge=1, le=120)):
    """What's being built RIGHT NOW — module-level live feed.

    Returns:
      - in_progress: modules with recently updated state-v3.json
      - recent_completions: research files created in last hour
      - recent_messages: last N broker dispatches
    """
    import asyncio

    acts, completions = await asyncio.gather(
        asyncio.to_thread(_scan_live_activity, minutes),
        asyncio.to_thread(_scan_recent_completions, 60),
    )

    # Also get recent broker messages for the dispatch feed
    conn = _get_db()
    dispatches = []
    if conn:
        rows = conn.execute("""
            SELECT id, task_id, from_llm, to_llm, message_type,
                   substr(content, 1, 200) as preview, timestamp
            FROM messages
            ORDER BY id DESC
            LIMIT 30
        """).fetchall()
        conn.close()
        now_ts = datetime.now(UTC)
        for r in rows:
            try:
                ts = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))
                age = (now_ts - ts).total_seconds()
            except (ValueError, TypeError):
                age = 0
            dispatches.append({
                "id": r["id"],
                "task_id": r["task_id"],
                "from": r["from_llm"],
                "to": r["to_llm"],
                "type": r["message_type"],
                "preview": r["preview"],
                "seconds_ago": int(age),
            })

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "in_progress": acts,
        "recent_completions": completions[:30],
        "recent_dispatches": dispatches,
    }


# ==================== ACTIONS ====================


@router.post("/cleanup")
async def cleanup_zombies(max_age_hours: float = Query(24.0)):
    """Force-ack stale messages and clean orphan PIDs."""
    cleaned = 0

    # 1. Force-ack old unacked messages
    conn = _get_rw_db()
    if conn:
        cursor = conn.execute(
            "SELECT id, timestamp FROM messages WHERE acknowledged = 0"
        )
        now = datetime.now(UTC)
        for row in cursor.fetchall():
            try:
                ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                age_h = (now - ts).total_seconds() / 3600
                if age_h > max_age_hours:
                    conn.execute("UPDATE messages SET acknowledged = 1 WHERE id = ?", (row["id"],))
                    cleaned += 1
            except (ValueError, TypeError):
                pass
        conn.commit()
        conn.close()

    # 2. Clean orphan PIDs
    if PID_DIR.exists():
        for pf in PID_DIR.glob("*.json"):
            try:
                data = json.loads(pf.read_text())
                pid = data.get("pid", 0)
                os.kill(pid, 0)
            except (ProcessLookupError, PermissionError):
                pf.unlink(missing_ok=True)
                cleaned += 1
            except Exception:
                pf.unlink(missing_ok=True)
                cleaned += 1

    return {"cleaned": cleaned}


@router.post("/acknowledge/{message_id}")
async def acknowledge_message(message_id: int):
    """Acknowledge a single message."""
    conn = _get_rw_db()
    if not conn:
        return JSONResponse(status_code=500, content={"error": "DB not available"})

    conn.execute("UPDATE messages SET acknowledged = 1 WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    return {"acknowledged": message_id}


class SendMessageRequest(BaseModel):
    from_llm: str
    to_llm: str
    content: str
    task_id: str = ""
    message_type: str = "message"


@router.post("/send", deprecated=True)
async def send_message(msg: SendMessageRequest):
    """**Deprecated (#1190 B.5).** Send a raw broker message.

    Use POST /api/comms/channels/{name}/post for channel-based
    conversations. This endpoint stays live because the legacy
    comms.html compose form still hits it, but nothing new should
    grow on top of it.
    """
    conn = _get_rw_db()
    if not conn:
        return JSONResponse(status_code=500, content={"error": "DB not available"})

    now = datetime.now(UTC).isoformat()
    cursor = conn.execute(
        "INSERT INTO messages (task_id, from_llm, to_llm, message_type, content, timestamp, acknowledged) "
        "VALUES (?, ?, ?, ?, ?, ?, 0)",
        (msg.task_id or None, msg.from_llm, msg.to_llm, msg.message_type, msg.content, now),
    )
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return {"id": msg_id, "sent": True}


# ══════════════════════════════════════════════════════════════════
# Channel bridge endpoints (#1190 Phase B.3)
# ══════════════════════════════════════════════════════════════════
#
# These endpoints expose the channel bridge to the web dashboard
# (playgrounds/channels.html). They reuse the same broker DB as the
# legacy /api/comms/messages* endpoints but operate on the new
# `channels`, `channel_messages`, `deliveries` tables.
#
# Security model: the FastAPI server is bound to 0.0.0.0 by default,
# so we can't rely on binding alone. The POST endpoint enforces a
# per-request client-host check (`_require_localhost`) that rejects
# anything other than loopback. GET endpoints are read-only snapshots
# of data that is already stored locally and are not gated.
# Agents do NOT post via this API; only the human user (via the
# browser or curl from the same machine). Agents use the CLI
# (`ab p`, `ab post`, `ab discuss`) which has its own subprocess-
# level invocation path.


_LOCALHOST_HOSTS = {"127.0.0.1", "::1", "localhost"}


def _require_localhost(request: Request) -> JSONResponse | None:
    """Return a 403 JSONResponse if the request is not from loopback.

    Returns None when the caller is local — the handler should proceed
    normally. The check uses `request.client.host`, which FastAPI
    populates from the accepted TCP socket, not from any client-
    controllable header. X-Forwarded-For is deliberately ignored
    because there is no trusted proxy in this deployment.
    """
    client = request.client
    host = client.host if client else None
    if host not in _LOCALHOST_HOSTS:
        return JSONResponse(
            status_code=403,
            content={
                "error": "channel POST endpoint is localhost-only",
                "client_host": host,
            },
        )
    return None


class ChannelPostRequest(BaseModel):
    """Pydantic body for POST /channels/{name}/post."""
    body: str
    to_agents: list[str] = []
    parent_id: str | None = None
    correlation_id: str | None = None
    from_agent: str = "user"
    auto_snapshot: bool = True


@router.get("/channels")
async def list_channels_endpoint():
    """List all channels with row counts and last activity.

    Read-only. Safe to poll from the frontend every few seconds.
    """
    conn = _get_db()
    if not conn:
        return {"channels": [], "error": "Broker DB not found"}

    try:
        channel_rows = conn.execute(
            "SELECT name, description, include, subscribers, created_at "
            "FROM channels ORDER BY created_at ASC"
        ).fetchall()
        msg_counts = {}
        latest = {}
        for r in conn.execute(
            "SELECT channel, COUNT(*) AS n, MAX(created_at) AS latest "
            "FROM channel_messages GROUP BY channel"
        ).fetchall():
            msg_counts[r["channel"]] = r["n"]
            latest[r["channel"]] = r["latest"]
        pending_counts = {}
        for r in conn.execute(
            "SELECT cm.channel, COUNT(*) AS n "
            "FROM deliveries d JOIN channel_messages cm "
            "  ON cm.message_id = d.message_id "
            "WHERE d.status = 'pending' "
            "GROUP BY cm.channel"
        ).fetchall():
            pending_counts[r["channel"]] = r["n"]
    finally:
        conn.close()

    channels = []
    for r in channel_rows:
        name = r["name"]
        channels.append({
            "name": name,
            "description": r["description"] or "",
            "include": [s for s in (r["include"] or "").split(",") if s],
            "subscribers": [s for s in (r["subscribers"] or "").split(",") if s],
            "created_at": r["created_at"],
            "message_count": msg_counts.get(name, 0),
            "last_activity": latest.get(name),
            "pending_deliveries": pending_counts.get(name, 0),
        })
    return {"channels": channels, "count": len(channels)}


@router.get("/channels/{name}")
async def get_channel_endpoint(name: str):
    """Channel metadata + context preview + pending delivery count."""
    conn = _get_db()
    if not conn:
        return JSONResponse(
            status_code=500, content={"error": "Broker DB not found"}
        )

    try:
        row = conn.execute(
            "SELECT name, description, include, subscribers, created_at "
            "FROM channels WHERE name = ?",
            (name,),
        ).fetchone()
        if not row:
            return JSONResponse(
                status_code=404, content={"error": f"channel '{name}' not found"}
            )

        msg_count = conn.execute(
            "SELECT COUNT(*) FROM channel_messages WHERE channel = ?", (name,)
        ).fetchone()[0]
        pending = conn.execute(
            "SELECT COUNT(*) FROM deliveries d "
            "JOIN channel_messages cm ON cm.message_id = d.message_id "
            "WHERE cm.channel = ? AND d.status = 'pending'",
            (name,),
        ).fetchone()[0]
    finally:
        conn.close()

    # Context preview (best-effort — reads from the filesystem)
    context_preview = ""
    context_sha = ""
    try:
        from ai_agent_bridge import _channels as _ch
        ctx_path = _ch.channel_context_path(name)
        if ctx_path.exists():
            context_preview = ctx_path.read_text("utf-8")[:2000]
            context_sha = _ch.context_sha256(ctx_path)
    except Exception:
        pass  # context fetch is non-critical

    return {
        "name": row["name"],
        "description": row["description"] or "",
        "include": [s for s in (row["include"] or "").split(",") if s],
        "subscribers": [s for s in (row["subscribers"] or "").split(",") if s],
        "created_at": row["created_at"],
        "message_count": msg_count,
        "pending_deliveries": pending,
        "context_preview": context_preview,
        "context_sha256": context_sha,
    }


@router.get("/channels/{name}/messages")
async def list_channel_messages(
    name: str,
    tail: int = Query(20, ge=1, le=500),
):
    """Most recent messages in a channel, ordered oldest-first."""
    conn = _get_db()
    if not conn:
        return JSONResponse(
            status_code=500, content={"error": "Broker DB not found"}
        )
    try:
        # Verify the channel exists first
        ch = conn.execute(
            "SELECT name FROM channels WHERE name = ?", (name,)
        ).fetchone()
        if not ch:
            return JSONResponse(
                status_code=404, content={"error": f"channel '{name}' not found"}
            )

        rows = conn.execute(
            """
            SELECT message_id, channel, thread_id, parent_id, correlation_id,
                   round_index, from_agent, from_model, kind, body,
                   attachments, context_rev_shared, context_rev_channel,
                   created_at
            FROM (
                SELECT * FROM channel_messages
                WHERE channel = ?
                ORDER BY created_at DESC
                LIMIT ?
            )
            ORDER BY created_at ASC
            """,
            (name, tail),
        ).fetchall()
    finally:
        conn.close()

    messages = []
    for r in rows:
        messages.append({
            "message_id": r["message_id"],
            "channel": r["channel"],
            "thread_id": r["thread_id"],
            "parent_id": r["parent_id"],
            "correlation_id": r["correlation_id"],
            "round_index": r["round_index"],
            "from_agent": r["from_agent"],
            "from_model": r["from_model"],
            "kind": r["kind"],
            "body": r["body"],
            "attachments": (
                json.loads(r["attachments"]) if r["attachments"] else None
            ),
            "context_rev_shared": r["context_rev_shared"],
            "context_rev_channel": r["context_rev_channel"],
            "created_at": r["created_at"],
        })
    return {"channel": name, "count": len(messages), "messages": messages}


@router.get("/channels/{name}/threads/{thread_id}")
async def get_thread(name: str, thread_id: str):
    """All messages in a thread, ordered by round_index then created_at."""
    conn = _get_db()
    if not conn:
        return JSONResponse(
            status_code=500, content={"error": "Broker DB not found"}
        )
    try:
        rows = conn.execute(
            """
            SELECT message_id, channel, thread_id, parent_id, correlation_id,
                   round_index, from_agent, from_model, kind, body,
                   attachments, context_rev_shared, context_rev_channel,
                   created_at
            FROM channel_messages
            WHERE channel = ? AND thread_id = ?
            ORDER BY round_index ASC, created_at ASC
            """,
            (name, thread_id),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return JSONResponse(
            status_code=404,
            content={"error": f"thread '{thread_id}' not found in channel '{name}'"},
        )

    messages = []
    for r in rows:
        messages.append({
            "message_id": r["message_id"],
            "thread_id": r["thread_id"],
            "parent_id": r["parent_id"],
            "correlation_id": r["correlation_id"],
            "round_index": r["round_index"],
            "from_agent": r["from_agent"],
            "from_model": r["from_model"],
            "kind": r["kind"],
            "body": r["body"],
            "created_at": r["created_at"],
        })
    return {
        "channel": name,
        "thread_id": thread_id,
        "count": len(messages),
        "messages": messages,
    }


@router.get("/channels/{name}/deliveries")
async def channel_deliveries(
    name: str,
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=500),
):
    """Delivery status for messages in a channel."""
    conn = _get_db()
    if not conn:
        return JSONResponse(
            status_code=500, content={"error": "Broker DB not found"}
        )

    try:
        where = ["cm.channel = ?"]
        params: list = [name]
        if status:
            where.append("d.status = ?")
            params.append(status)
        params.append(limit)
        rows = conn.execute(
            f"""
            SELECT d.delivery_id, d.message_id, d.to_agent, d.to_model,
                   d.status, d.dispatched_at, d.delivered_at, d.error,
                   cm.body, cm.from_agent AS cm_from_agent, cm.created_at
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE {' AND '.join(where)}
            ORDER BY cm.created_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
    finally:
        conn.close()

    deliveries = []
    for r in rows:
        body = r["body"] or ""
        deliveries.append({
            "delivery_id": r["delivery_id"],
            "message_id": r["message_id"],
            "to_agent": r["to_agent"],
            "to_model": r["to_model"],
            "status": r["status"],
            "dispatched_at": r["dispatched_at"],
            "delivered_at": r["delivered_at"],
            "error": r["error"],
            "preview": body[:200] + ("..." if len(body) > 200 else ""),
            "from_agent": r["cm_from_agent"],
            "created_at": r["created_at"],
        })
    return {"channel": name, "count": len(deliveries), "deliveries": deliveries}


@router.post("/channels/{name}/post")
async def post_to_channel(name: str, req: ChannelPostRequest, request: Request):
    """Post a message to a channel (human-user only, localhost-gated).

    Agents NEVER post via this endpoint — they use the CLI subprocess
    path. This endpoint exists for (1) dashboard post forms, (2) future
    click-to-ask affordances from other dashboards, (3) scripts that
    want to drop messages without spawning a full CLI process.

    The localhost gate rejects any client whose socket address isn't
    127.0.0.1 / ::1. Since the API server binds to 0.0.0.0, this
    per-request check is the only thing keeping LAN peers out.
    """
    gate = _require_localhost(request)
    if gate is not None:
        return gate
    try:
        # Import inside handler so the bridge package isn't a hard
        # dependency for the rest of the API server startup.
        from ai_agent_bridge import _channels as _ch
    except ImportError as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"ai_agent_bridge not importable: {e}"},
        )

    try:
        result = _ch.post(
            name,
            req.from_agent,
            req.body,
            to_agents=req.to_agents,
            parent_id=req.parent_id,
            correlation_id=req.correlation_id,
            auto_snapshot=req.auto_snapshot,
        )
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"post failed: {e}"}
        )

    return {
        "message_id": result["message_id"],
        "thread_id": result["thread_id"],
        "round_index": result["round_index"],
        "delivery_ids": result["delivery_ids"],
        "created_at": result["created_at"],
        "posted": True,
    }


@router.get("/by-module/{track}/{slug}")
async def messages_by_module(track: str, slug: str, limit: int = 30):
    """Full communication trail for a module. Shows all broker messages where task_id contains the slug."""
    conn = _get_db()
    if not conn:
        return JSONResponse(status_code=500, content={"error": "DB not available"})

    rows = conn.execute(
        "SELECT id, task_id, from_llm, to_llm, message_type, "
        "content, data, timestamp, acknowledged "
        "FROM messages WHERE task_id LIKE ? "
        "ORDER BY id DESC LIMIT ?",
        (f"%{slug}%", limit),
    ).fetchall()
    conn.close()

    messages = []
    for r in rows:
        content = r["content"] or ""
        messages.append({
            "id": r["id"],
            "task_id": r["task_id"],
            "from": r["from_llm"],
            "to": r["to_llm"],
            "type": r["message_type"],
            "preview": content[:300] + ("..." if len(content) > 300 else ""),
            "full_length": len(content),
            "timestamp": r["timestamp"],
            "acknowledged": bool(r["acknowledged"]),
        })

    # Group by task_id for easy reading
    task_groups = {}
    for msg in messages:
        tid = msg["task_id"] or "no-task"
        task_groups.setdefault(tid, []).append(msg)

    return {
        "track": track,
        "slug": slug,
        "total_messages": len(messages),
        "task_groups": task_groups,
        "messages": messages,
    }
