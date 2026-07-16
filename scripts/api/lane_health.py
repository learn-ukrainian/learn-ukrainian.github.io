"""Lane health tracker -- checks recent task outcomes to detect and demote unhealthy lanes.

Part of the routing-budget guard (epic #4707).
"""

import json
import logging
import os
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from agent_runtime.agent_identity import normalize_seat, seat_read_aliases
except ImportError:
    from scripts.agent_runtime.agent_identity import normalize_seat, seat_read_aliases

logger = logging.getLogger("lane_health")

# Constants per specification
# Default window for scan is 120 minutes (M)
DEFAULT_WINDOW_MINUTES = 120
# Default consecutive failures before marking lane unhealthy is 2 (N)
DEFAULT_FAILURES_THRESHOLD = 2
# Spawn-phase failure duration threshold (seconds)
# We tune this to 120s because typical sandbox/startup/provider credential issues
# manifest immediately during startup (under 2 minutes), whereas longer durations
# indicate task-specific work (e.g. executing tests or building files) rather than
# lane-spawning failure.
DEFAULT_SPAWN_DURATION_THRESHOLD_S = 120


def is_spawn_phase_failure(record: dict[str, Any], duration_threshold_s: int = DEFAULT_SPAWN_DURATION_THRESHOLD_S) -> bool:
    """Determine if a task record represents a spawn-phase failure.

    A spawn-phase failure is defined as:
    - status is "failed" or "error"
    - returncode is not None and not 0
    - duration_s is not None and less than the duration threshold
    """
    status = record.get("status")
    returncode = record.get("returncode")
    duration_s = record.get("duration_s")

    is_failed_status = status in ("failed", "error")
    # Treat clean exits (returncode == 0) and needs_finalize as healthy signals.
    # If returncode is None, the process is still running or hasn't updated its returncode yet.
    is_non_zero_rc = returncode is not None and returncode != 0
    is_short_duration = duration_s is not None and duration_s < duration_threshold_s

    return bool(is_failed_status and is_non_zero_rc and is_short_duration)


def normalize_agent_name(raw_agent: str | None) -> str | None:
    """Normalize agent name to match standard subscription/API lane names.

    Matches _agent_key from state_router.py. Permanent alias: grok-build → grok.
    """
    if not raw_agent:
        return None
    agent = str(raw_agent).lower().strip()
    # Permanent native-seat alias (see agent_identity.SEAT_ALIASES).
    if agent in {"grok", "grok-build"} or agent.startswith("grok ") or agent.startswith("grok("):
        return "grok"
    canonical = normalize_seat(agent)
    for name in ("claude", "codex", "gemini", "grok", "cursor", "kimi", "deepseek"):
        if canonical == name or agent in seat_read_aliases(name):
            return name
        if agent == name or agent.startswith(f"{name} ") or agent.startswith(f"{name}("):
            return name
    return canonical or agent


def compute_lane_health(
    batch_state_dir: Path | str,
    now: datetime | None = None,
    window_minutes: int = DEFAULT_WINDOW_MINUTES,
    failures_threshold: int = DEFAULT_FAILURES_THRESHOLD,
    spawn_duration_threshold_s: int = DEFAULT_SPAWN_DURATION_THRESHOLD_S,
) -> dict[str, dict[str, Any]]:
    """Scan recent batch task records to compute health status per lane.

    FAIL-OPEN: any error reading/parsing records yields an empty/healthy result,
    preserving the original behavior/ranking.
    """
    if now is None:
        now = datetime.now(UTC)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    health_data: dict[str, dict[str, Any]] = {}
    lane_tasks: dict[str, list[dict[str, Any]]] = {}

    tasks_path = Path(batch_state_dir)
    if not tasks_path.exists() or not tasks_path.is_dir():
        logger.debug("Tasks directory does not exist: %s", tasks_path)
        return health_data

    # Bounded by mtime cutoff
    cutoff_dt = now - timedelta(minutes=window_minutes)
    # 5 min buffer to prevent clock skew/file write delays from dropping edge files
    cutoff_timestamp = now.timestamp() - (window_minutes * 60) - 300

    try:
        for entry in os.scandir(tasks_path):
            if not entry.is_file() or not entry.name.endswith(".json"):
                continue

            try:
                # Fast mtime check to prevent loading massive directories
                stat = entry.stat()
                if stat.st_mtime < cutoff_timestamp:
                    continue

                with open(entry.path, encoding="utf-8") as f:
                    record = json.load(f)

                if not isinstance(record, dict):
                    continue

                started_at_str = record.get("started_at")
                if not started_at_str:
                    continue

                # Standardize datetime parsing
                started_at_str = started_at_str.replace("Z", "+00:00")
                started_at_dt = datetime.fromisoformat(started_at_str)
                if started_at_dt.tzinfo is None:
                    started_at_dt = started_at_dt.replace(tzinfo=UTC)

                if started_at_dt < cutoff_dt:
                    continue

                agent = record.get("agent")
                if not agent:
                    continue

                agent_norm = normalize_agent_name(agent)
                if not agent_norm:
                    continue

                # Save parsed datetime to avoid parsing it again during sorting
                record["_started_at_dt"] = started_at_dt
                lane_tasks.setdefault(agent_norm, []).append(record)

            except Exception as e:
                # Fail-open per file: log debug note, proceed
                logger.debug("Skipping invalid task record %s: %s", entry.name, e)

    except Exception as e:
        # Fail-open per directory scan: log debug note, return empty health
        logger.debug("Error scanning task records: %s", e)
        return health_data

    # Compute health per lane
    for lane, tasks in lane_tasks.items():
        # Sort oldest to newest
        tasks.sort(key=lambda t: t["_started_at_dt"])

        consecutive_failures = 0
        streak_tasks = []

        # Count consecutive spawn failures walking backward from the newest task
        for record in reversed(tasks):
            if is_spawn_phase_failure(record, spawn_duration_threshold_s):
                consecutive_failures += 1
                streak_tasks.append(record)
            else:
                # Streak broken by a healthy signal or non-spawn failure or running task
                break

        is_healthy = consecutive_failures < failures_threshold

        span_minutes = 0
        if not is_healthy and streak_tasks:
            # Time elapsed from the oldest failure in the consecutive streak to now
            oldest_streak_task = streak_tasks[-1]
            delta = now - oldest_streak_task["_started_at_dt"]
            span_minutes = max(1, round(delta.total_seconds() / 60))

        health_data[lane] = {
            "healthy": is_healthy,
            "consecutive_failures": consecutive_failures,
            "span_minutes": span_minutes,
        }

    return health_data
