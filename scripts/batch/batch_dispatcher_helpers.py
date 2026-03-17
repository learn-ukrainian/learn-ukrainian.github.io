"""Batch dispatcher helper functions.

Track scanning, dependency checking, priority scoring, strategy selection,
state management, subprocess dispatch, and progress detection for the
batch dispatcher system.
"""

import json
import logging
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from audit.status_cache import get_source_paths, read_status
from batch_dispatcher_config import (
    COST_ESTIMATES,
    RUNNER_MAX_CONSECUTIVE_FAILURES,
    RUNNER_MAX_FAILURE_RATE,
    SCORING_WEIGHTS,
    SUBPROCESS_TIMEOUT_SECONDS,
    TRACK_BY_NAME,
    TRACKS,
    TrackState,
)
from batch_gemini_config import PROJECT_ROOT, SEMINAR_TRACKS, VENV_PYTHON, get_module_index, get_module_paths
from batch_utils import atomic_write_json

log = logging.getLogger("dispatcher")

BATCH_RUNNER = str(PROJECT_ROOT / "scripts" / "batch_gemini_runner.py")
CLAUDE_BIN = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")
BATCH_STATE_DIR = PROJECT_ROOT / "batch_state"
LOCK_DIR = BATCH_STATE_DIR / "locks"
FAILURES_DIR = BATCH_STATE_DIR / "failures"
CLAUDE_FIX_TIMEOUT = 1800  # 30 minutes per module


def scan_track(track_name: str, trust_cache: bool = False) -> dict:
    """Scan a track's modules and return pass/fail/stale/total counts.

    Reads per-module status JSON via read_status() with freshness checking.
    Three-way classification (from #561):
        - passed: fresh cache with PASS status
        - failed: fresh cache with FAIL status, or has content but no status
        - stale: cache exists and shows PASS but source files are newer
        - unbuilt: no content (.md < 500 bytes) and no status

    Stale PASS modules count toward dependency thresholds (pass_rate) to avoid
    oscillation, but are flagged for cheap re-audit before Gemini dispatch.
    """
    try:
        idx = get_module_index(track_name)
    except ValueError:
        return {"total": 0, "passed": 0, "failed": 0, "stale": 0, "unbuilt": 0,
                "error": "Track not in curriculum.yaml"}

    total = idx["total"]
    passed = 0
    failed = 0
    stale = 0
    unbuilt = 0

    track_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / track_name

    for num in range(1, total + 1):
        slug = idx["num_to_slug"][num]
        try:
            paths = get_module_paths(track_name, slug)
        except Exception:
            unbuilt += 1
            continue

        md_path = paths["md"]
        has_content = md_path.exists() and md_path.stat().st_size >= 500

        status_path = paths["status"]
        source_paths = get_source_paths(track_dir, slug) if not trust_cache else None
        result = read_status(status_path, source_paths=source_paths)

        if result is None:
            if has_content:
                failed += 1
            else:
                unbuilt += 1
        elif result.status.upper() == "PASS":
            if result.is_fresh:
                passed += 1
            else:
                stale += 1
                log.debug(f"  Stale PASS: {slug} (changed: {','.join(result.stale_sources)})")
        elif has_content:
            failed += 1
        else:
            unbuilt += 1

    effective_passed = passed + stale
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "stale": stale,
        "unbuilt": unbuilt,
        "pass_rate": effective_passed / total if total > 0 else 0,
    }


def read_batch_state(track_name: str) -> dict | None:
    """Read the batch_gemini_runner state file for a track."""
    state_file = BATCH_STATE_DIR / f"state_{track_name}.json"
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def check_dependencies(track_name: str, track_scans: dict[str, dict]) -> tuple[bool, list[str]]:
    """Check if all dependencies for a track are satisfied.

    Returns (satisfied, [list of unmet dependency descriptions]).
    """
    track_info = TRACK_BY_NAME.get(track_name)
    if not track_info:
        return False, [f"Unknown track: {track_name}"]

    deps = track_info[4]  # dependencies list
    if not deps:
        return True, []

    unmet = []
    for dep_track, min_rate in deps:
        scan = track_scans.get(dep_track)
        if scan is None:
            unmet.append(f"{dep_track}: not scanned")
            continue
        actual_rate = scan.get("pass_rate", 0)
        if actual_rate < min_rate:
            unmet.append(f"{dep_track}: {actual_rate:.0%} < {min_rate:.0%}")

    return len(unmet) == 0, unmet


def compute_priority_score(track_name: str, scan: dict, track_scans: dict[str, dict],
                           dispatcher_state: dict) -> float:
    """Compute weighted priority score for tiebreaking.

    Primary order is user-specified (TRACKS list). This score is secondary.
    """
    total = scan.get("total", 1)
    passed = scan.get("passed", 0) + scan.get("stale", 0)
    failed = scan.get("failed", 0)
    unbuilt = scan.get("unbuilt", 0)

    quick_win = 10 * ((passed / total if total > 0 else 0) ** 2)
    impact = min(10, (failed + unbuilt) / 10)

    batch_state = read_batch_state(track_name)
    if batch_state and batch_state.get("summary"):
        summary = batch_state["summary"]
        hist_processed = summary.get("processed", 0)
        hist_passed = summary.get("passed", 0)
        success_rate = (hist_passed / hist_processed * 10) if hist_processed > 0 else 5
    else:
        success_rate = 5

    downstream_count = 0
    for t in TRACKS:
        for dep_track, _ in t[4]:
            if dep_track == track_name:
                downstream_count += 1
    dependency_score = min(10, downstream_count * 2)

    track_info = TRACK_BY_NAME.get(track_name)
    is_seminar = track_info[3] == "seminar" if track_info else False
    has_unbuilt = unbuilt > 0
    if is_seminar:
        cost = COST_ESTIMATES["seminar_build"] if has_unbuilt else COST_ESTIMATES["seminar_fix"]
    else:
        cost = COST_ESTIMATES["core_build"] if has_unbuilt else COST_ESTIMATES["core_fix"]

    w = SCORING_WEIGHTS
    score = (
        w["quick_win"] * quick_win +
        w["impact"] * impact +
        w["success_rate"] * success_rate +
        w["dependency"] * dependency_score +
        w["cost_penalty"] * cost
    )

    return round(score, 3)


def select_strategy(track_name: str, scan: dict) -> tuple[str, list[str]]:
    """Determine execution strategy for a track.

    Returns (mode, extra_args) for batch_gemini_runner.
    """
    unbuilt = scan.get("unbuilt", 0)
    failed = scan.get("failed", 0)

    if unbuilt > 0 or failed > 0:
        return "auto", []
    else:
        return "fix", []


def load_dispatcher_state(state_file: Path) -> dict:
    """Load or initialize dispatcher state."""
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "started": datetime.now(UTC).isoformat(),
        "tracks": {},
        "dispatch_history": [],
        "stats": {
            "total_dispatches": 0,
            "total_cooldowns": 0,
            "total_stalls": 0,
            "rotations_completed": 0,
        },
    }


def save_dispatcher_state(state: dict, state_file: Path):
    """Save dispatcher state atomically."""
    state["last_updated"] = datetime.now(UTC).isoformat()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(state_file, state)


def get_track_dstate(state: dict, track_name: str) -> dict:
    """Get or create per-track state within dispatcher state."""
    if track_name not in state["tracks"]:
        state["tracks"][track_name] = {
            "state": TrackState.PENDING,
            "stall_count": 0,
            "last_dispatch": None,
            "last_result": None,
            "cooldown_until": None,
            "dispatches": 0,
            "last_passed": 0,
            "last_failed": 0,
        }
    return state["tracks"][track_name]


def dispatch_track(track_name: str, mode: str, extra_args: list[str],
                   timeout: int = SUBPROCESS_TIMEOUT_SECONDS) -> dict:
    """Dispatch batch_gemini_runner as a subprocess.

    Returns dict with success, returncode, duration_s, quota_hit, stderr, stdout_tail.
    """
    cmd = [VENV_PYTHON, BATCH_RUNNER, track_name, "--mode", mode,
           "--max-consecutive-failures", str(RUNNER_MAX_CONSECUTIVE_FAILURES),
           "--max-failure-rate", str(RUNNER_MAX_FAILURE_RATE),
           "--json-log", *extra_args]

    log.info(f"  Dispatching: {' '.join(cmd[-6:])}")

    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=str(PROJECT_ROOT),
        )
        elapsed = time.monotonic() - start
        stderr = result.stderr[-2000:] if result.stderr else ""
        stdout_tail = result.stdout[-2000:] if result.stdout else ""
        combined = (stderr + stdout_tail).lower()
        quota_hit = any(kw in combined for kw in ("quota", "429", "rate limit", "resource_exhausted"))

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "duration_s": round(elapsed, 1),
            "quota_hit": quota_hit,
            "stderr": stderr,
            "stdout_tail": stdout_tail,
        }
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        log.error(f"  Subprocess timeout after {elapsed:.0f}s")
        return {"success": False, "returncode": -1, "duration_s": round(elapsed, 1),
                "quota_hit": False, "stderr": "TimeoutExpired", "stdout_tail": ""}
    except Exception as e:
        elapsed = time.monotonic() - start
        log.error(f"  Subprocess error: {e}")
        return {"success": False, "returncode": -2, "duration_s": round(elapsed, 1),
                "quota_hit": False, "stderr": str(e), "stdout_tail": ""}


def dispatch_claude_fix(track_name: str, slug: str, module_num: int,
                        failure_data: dict | None = None,
                        timeout: int = CLAUDE_FIX_TIMEOUT) -> dict:
    """Dispatch Claude Code to do a full rebuild of an escalated module.

    Uses /full-rebuild for seminar tracks and /full-rebuild-core for core tracks.
    """
    is_seminar = track_name in SEMINAR_TRACKS

    context_parts = [
        f"Module {track_name} {module_num} (slug: {slug}) needs a full rebuild.",
        "",
        "This module was escalated from the Gemini batch runner after exhausting fix iterations.",
    ]
    if failure_data:
        gates = failure_data.get("failed_gates", {})
        if gates:
            context_parts.append(f"Failed gates: {', '.join(gates.keys())}")
            for name, info in gates.items():
                msg = info.get("message", "")
                if msg:
                    context_parts.append(f"  {name}: {msg}")
        blocking = failure_data.get("blocking_issues", [])
        if blocking:
            context_parts.append(f"Blocking issues: {'; '.join(blocking)}")
        actions = failure_data.get("actions_tried", [])
        if actions:
            tried = [a.get("diagnosis", "?") for a in actions]
            context_parts.append(f"Gemini tried ({len(actions)}x): {', '.join(tried)}")

    rebuild_cmd = f"/full-rebuild {track_name} {module_num}" if is_seminar else f"/full-rebuild-core {track_name} {module_num}"

    context_parts.extend([
        "",
        f"Run: {rebuild_cmd}",
        "",
        "This runs the full pipeline: research, build, review, verify, and MDX generation.",
        "The command is resumable — it will skip already-completed phases.",
        "Work until ALL audit gates pass and MDX is generated.",
    ])

    prompt = "\n".join(context_parts)
    budget = "10" if is_seminar else "8"
    cmd = [
        CLAUDE_BIN, "-p", prompt,
        "--allowedTools", "Bash,Edit,Read,Write,Glob,Grep,WebSearch,WebFetch",
        "--permission-mode", "bypassPermissions",
        "--max-budget-usd", budget,
    ]

    log.info(f"  Claude fix: {track_name}/{slug} (module {module_num})")

    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=str(PROJECT_ROOT),
        )
        elapsed = time.monotonic() - start
        stdout_tail = result.stdout[-3000:] if result.stdout else ""
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "duration_s": round(elapsed, 1),
            "stdout_tail": stdout_tail,
        }
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        log.error(f"  Claude fix timeout after {elapsed:.0f}s for {track_name}/{slug}")
        return {"success": False, "returncode": -1, "duration_s": round(elapsed, 1),
                "stdout_tail": "TimeoutExpired"}
    except Exception as e:
        elapsed = time.monotonic() - start
        log.error(f"  Claude fix error for {track_name}/{slug}: {e}")
        return {"success": False, "returncode": -2, "duration_s": round(elapsed, 1),
                "stdout_tail": str(e)}


def detect_progress(track_name: str, scan_before: dict, scan_after: dict) -> dict:
    """Compare before/after scans to detect progress."""
    delta_passed = scan_after["passed"] - scan_before["passed"]
    delta_failed = scan_after["failed"] - scan_before["failed"]
    delta_unbuilt = scan_before["unbuilt"] - scan_after["unbuilt"]

    return {
        "delta_passed": delta_passed,
        "delta_failed": delta_failed,
        "delta_unbuilt": delta_unbuilt,
        "made_progress": delta_passed > 0 or delta_unbuilt > 0,
    }
