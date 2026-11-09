"""Curriculum batch progress: ``/api/comms/batch-progress*`` and the fleet batch snapshot.

The routes keep their ``/api/comms`` prefix; the product entry mounts this
router there next to the machinery comms router. ``fleet_batch_snapshot``
feeds the batch section of the machinery ``GET /api/fleet/operations``
through the product contribution (Monitor split, C-4687).
"""

import asyncio
import logging
import os
import re
import subprocess
import time
from datetime import UTC, datetime

import yaml

logger = logging.getLogger(__name__)

from typing import Any

from fastapi import APIRouter, Depends

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.project_api package import (production)


from scripts.api.monitor_context import MonitorContext, get_ctx, resolve_context
from scripts.api.state_helpers import cache_get, cache_set
from scripts.api.telemetry.legacy_comms import LegacyCommsTelemetryRoute

router = APIRouter(tags=["comms"], route_class=LegacyCommsTelemetryRoute)

BATCH_LOG_TAIL_BYTES = 256 * 1024


def _read_tail_text(path, max_bytes: int = BATCH_LOG_TAIL_BYTES) -> tuple[str, bool]:
    """Read at most the tail of a log file for dashboard polling."""
    size = path.stat().st_size
    if size <= max_bytes:
        return path.read_text(errors="replace"), False
    with path.open("rb") as handle:
        handle.seek(-max_bytes, os.SEEK_END)
        return handle.read().decode("utf-8", errors="replace"), True


# ==================== BATCH PROGRESS ====================


def _preseed_log_dir(ctx: MonitorContext):
    """Research-preseed log directory under the context's logs root."""
    return ctx.roots.logs_dir / "research-preseed"


def _scan_preseed_logs(ctx: MonitorContext) -> list[dict]:
    """Scan preseed log files for progress info."""
    log_dir = _preseed_log_dir(ctx)
    if not log_dir.exists():
        return []

    # Find the most recent batch of logs (same timestamp suffix)
    log_files = sorted(log_dir.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
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
    for lf in log_dir.glob(f"*-{latest_ts}.log"):
        track = lf.name.replace(f"-{latest_ts}.log", "")
        stat = lf.stat()

        # Parse a bounded tail for progress. Full historical preseed logs
        # can be multi-MB and this endpoint is polled by dashboards.
        text, truncated = _read_tail_text(lf)
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

        results.append(
            {
                "track": track,
                "log_file": lf.name,
                "log_size_kb": round(stat.st_size / 1024, 1),
                "last_modified": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                "age_seconds": int(time.time() - stat.st_mtime),
                "passed": passed,
                "failed": failed,
                "complete": batch_complete,
                "last_line": last_line,
                "truncated": truncated,
            }
        )

    return sorted(results, key=lambda r: r["track"])


def _scan_track_progress(ctx: MonitorContext, track: str) -> dict:
    """Count research files and check running processes for a track."""
    curriculum_root = ctx.roots.curriculum_root
    try:
        track_dir = safe_join(curriculum_root, track)
        research_dir = safe_join(track_dir, "research")
    except ValueError:
        return {
            "track": track,
            "total_expected": 0,
            "research_done": 0,
            "remaining": 0,
            "recent_30min": 0,
            "throughput_per_hour": 0,
            "last_created": None,
        }

    research_files = []
    if research_dir.exists():
        for rf in research_dir.glob("*-research.md"):
            research_files.append(
                {
                    "slug": rf.stem.replace("-research", ""),
                    "mtime": rf.stat().st_mtime,
                }
            )

    # Count total expected from curriculum.yaml
    total_expected = 0
    load_errors: list[str] = []
    curriculum_yaml = curriculum_root / "curriculum.yaml"
    if curriculum_yaml.exists():
        try:
            data = yaml.safe_load(curriculum_yaml.read_text(encoding="utf-8"))
            if data is None:
                data = {}
            if not isinstance(data, dict):
                raise TypeError(f"curriculum.yaml root is {type(data).__name__}")
            modules = data.get("levels", {}).get(track, {}).get("modules", [])
            total_expected = len(modules)
        except (OSError, UnicodeDecodeError, yaml.YAMLError, AttributeError, TypeError) as exc:
            logger.warning(
                "comms batch progress: failed to load %s for track %s: %s",
                curriculum_yaml.name,
                track,
                exc,
            )
            load_errors.append(f"{track}: {curriculum_yaml.name}: {type(exc).__name__}")

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

    progress = {
        "track": track,
        "total_expected": total_expected,
        "research_done": len(research_files),
        "remaining": max(0, total_expected - len(research_files)),
        "recent_30min": len(recent),
        "throughput_per_hour": throughput_per_hour,
        "last_created": last_created,
    }
    if load_errors:
        progress["errors"] = load_errors
    return progress


def _check_build_processes() -> tuple[list[dict], str | None]:
    """Find running legacy build_module.py processes.

    ``([], error)`` means ``ps`` failed or timed out. That is not an empty
    process list: callers must not report it as zero running processes.
    """
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired as exc:
        logger.warning("batch progress: ps timed out: %s", exc)
        return [], "ps: TimeoutExpired"
    except Exception as exc:
        logger.warning("batch progress: ps failed: %s", exc)
        return [], f"ps: {type(exc).__name__}"
    if result.returncode != 0:
        logger.warning("batch progress: ps exited %s", result.returncode)
        return [], f"ps: exit {result.returncode}"
    procs = []
    for line in result.stdout.splitlines():
        if "build_module.py" in line and "python" in line.lower():
            parts = line.split()
            pid = int(parts[1])
            # Extract track from command line
            track_match = re.search(r"build_module\.py\s+(\S+)", line)
            track = track_match.group(1) if track_match else "unknown"
            procs.append(
                {
                    "pid": pid,
                    "track": track,
                    "version": "legacy",
                    "cmd": " ".join(parts[10:])[:200],
                }
            )
    return procs, None


@router.get("/batch-progress")
async def batch_progress(ctx: MonitorContext = Depends(get_ctx)):
    """Live batch progress: logs + research files + running processes.

    This is the main endpoint for monitoring overnight/background builds.
    """
    cache_key = f"comms_batch_progress_{_preseed_log_dir(ctx)}_{ctx.roots.pid_dir}"
    cached = cache_get(cache_key, ttl=10.0)
    if cached is not None:
        return cached

    logs, process_probe = await asyncio.gather(
        asyncio.to_thread(_scan_preseed_logs, ctx),
        asyncio.to_thread(_check_build_processes),
    )
    processes, process_error = process_probe

    # Get all tracks that have logs or processes
    all_tracks = set()
    for log in logs:
        all_tracks.add(log["track"])
    for proc in processes:
        all_tracks.add(proc["track"])

    # Scan each track's actual file progress
    track_progress = {}
    for track in sorted(all_tracks):
        tp = await asyncio.to_thread(_scan_track_progress, ctx, track)

        # Find matching log
        log = next((l for l in logs if l["track"] == track), None)

        # Find matching process
        proc = next((p for p in processes if p["track"] == track), None)

        # Determine health status. A failed ps probe is not evidence the build exited.
        if log and log["complete"]:
            health = "complete"
        elif proc:
            health = "healthy" if tp["recent_30min"] > 0 or (log and log["age_seconds"] < 900) else "stalled"
        elif process_error:
            health = "unknown"
        elif log and not log["complete"] and log["age_seconds"] > 600:
            health = "dead"
        else:
            health = "unknown"

        track_row = {
            **tp,
            "health": health,
            "log": log,
            "process": proc,
        }
        if process_error and health == "unknown":
            track_row["reason"] = process_error
        track_progress[track] = track_row

    result: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "running_processes": None if process_error else len(processes),
        "tracks": track_progress,
    }
    if process_error:
        result["errors"] = [process_error]
    cache_set(cache_key, result)
    return result


@router.get("/batch-progress/{track}")
async def batch_progress_track(track: str, ctx: MonitorContext = Depends(get_ctx)):
    """Detailed progress for one track."""
    tp = await asyncio.to_thread(_scan_track_progress, ctx, track)

    # Get research file timeline (last 20 files)
    try:
        research_dir = safe_join(ctx.roots.curriculum_root, track, "research")
    except ValueError:
        return {**tp, "recent_files": []}
    timeline = []
    if research_dir.exists():
        files = sorted(research_dir.glob("*-research.md"), key=lambda f: f.stat().st_mtime, reverse=True)
        now = time.time()
        for rf in files[:20]:
            timeline.append(
                {
                    "slug": rf.stem.replace("-research", ""),
                    "created_ago_seconds": int(now - rf.stat().st_mtime),
                    "created_at": datetime.fromtimestamp(rf.stat().st_mtime, tz=UTC).isoformat(),
                    "size_kb": round(rf.stat().st_size / 1024, 1),
                }
            )

    return {**tp, "recent_files": timeline}


def _non_negative_int(value: Any) -> int:
    """Normalize legacy numeric fields without reflecting arbitrary values."""
    if isinstance(value, bool):
        return int(value)
    try:
        return max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return 0


def fleet_batch_snapshot(ctx: MonitorContext | None = None) -> dict[str, Any]:
    """Collect the batch read models for ``GET /api/fleet/operations`` without populating their cache.

    The machinery fleet router sanitizes this raw snapshot into its batch
    projection; the product contribution supplies it (C-4687).
    """
    resolved_ctx = resolve_context(ctx)
    logs = _scan_preseed_logs(resolved_ctx)
    processes, process_error = _check_build_processes()
    all_tracks = {
        str(item.get("track"))
        for item in [*logs, *processes]
        if isinstance(item, dict) and item.get("track")
    }
    tracks: dict[str, dict[str, Any]] = {}
    for track in sorted(all_tracks):
        progress = _scan_track_progress(resolved_ctx, track)
        log = next(
            (item for item in logs if isinstance(item, dict) and item.get("track") == track),
            None,
        )
        process = next(
            (
                item
                for item in processes
                if isinstance(item, dict) and item.get("track") == track
            ),
            None,
        )
        if log and log.get("complete"):
            health = "complete"
        elif process:
            recent = _non_negative_int(progress.get("recent_30min"))
            log_is_recent = bool(
                log
                and "age_seconds" in log
                and _non_negative_int(log.get("age_seconds")) < 900
            )
            health = "healthy" if recent > 0 or log_is_recent else "stalled"
        elif process_error:
            # A failed ps probe is not evidence the build exited.
            health = "unknown"
        elif (
            log
            and not log.get("complete")
            and _non_negative_int(log.get("age_seconds")) > 600
        ):
            health = "dead"
        else:
            health = "unknown"
        track_row = {**progress, "health": health}
        if process_error and health == "unknown":
            track_row["reason"] = process_error
        tracks[track] = track_row
    snapshot: dict[str, Any] = {
        "running_processes": None if process_error else len(processes),
        "tracks": tracks,
    }
    if process_error:
        snapshot["errors"] = [process_error]
    return snapshot
