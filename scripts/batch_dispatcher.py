#!/usr/bin/env python3
"""
Smart Batch Dispatcher — Autonomous scheduler for curriculum batch processing.

Processes all 20 tracks (~1,250 modules) in priority order by dispatching to
batch_gemini_runner.py. Handles quota exhaustion, failures, and track rotation.

Philosophy: Slow but steady. Run continuously, one track at a time, hammering
Gemini until everything is done. On quota hit → pause, switch track, come back.
On stall → try once more, then move on, revisit later.

Usage:
    # Continuous mode — process everything
    .venv/bin/python scripts/batch_dispatcher.py run

    # Single cycle — pick one track, dispatch, exit
    .venv/bin/python scripts/batch_dispatcher.py run --one-shot

    # Dry run — show priorities without dispatching
    .venv/bin/python scripts/batch_dispatcher.py scan

    # Show current state
    .venv/bin/python scripts/batch_dispatcher.py status

    # Force a specific track
    .venv/bin/python scripts/batch_dispatcher.py dispatch-one --track c1-bio

    # Filter tracks
    --include-tracks b2-hist c1-bio lit
    --exclude-tracks a1 b1 b2

    # Safety timeout
    --max-runtime-hours 12
"""

import argparse
import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure scripts/ is on sys.path for sibling imports
sys.path.insert(0, str(Path(__file__).parent))

from batch_utils import atomic_write_json, BatchLock, LockConflictError, classify_error, ErrorCategory
from batch_gemini_config import get_module_index, get_module_paths, PROJECT_ROOT, SEMINAR_TRACKS
from batch_dispatcher_config import (
    TRACKS, TRACK_BY_NAME, TRACK_NAMES,
    SCORING_WEIGHTS, COST_ESTIMATES,
    COOLDOWN_SECONDS, SUBPROCESS_TIMEOUT_SECONDS, INTER_DISPATCH_PAUSE,
    MAX_STALL_COUNT, STALLED_REVISIT_AFTER_ROTATION,
    RUNNER_MAX_CONSECUTIVE_FAILURES, RUNNER_MAX_FAILURE_RATE,
    TrackState, DISPATCHER_STATE_FILE,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log = logging.getLogger("dispatcher")

VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
BATCH_RUNNER = str(PROJECT_ROOT / "scripts" / "batch_gemini_runner.py")
CLAUDE_BIN = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")
BATCH_STATE_DIR = PROJECT_ROOT / "batch_state"
LOCK_DIR = BATCH_STATE_DIR / "locks"
FAILURES_DIR = BATCH_STATE_DIR / "failures"
CLAUDE_FIX_TIMEOUT = 1800  # 30 minutes per module (full rebuilds take time)

# Graceful shutdown flag
_shutdown_requested = False


def _signal_handler(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True
    log.warning(f"Shutdown requested (signal {signum}). Finishing current dispatch...")


# ---------------------------------------------------------------------------
# Track scanning — read status JSONs to compute pass rates
# ---------------------------------------------------------------------------

def scan_track(track_name: str) -> dict:
    """Scan a track's modules and return pass/fail/total counts.

    Reads per-module status JSON cache files. Modules without a status file
    or without content (.md < 500 bytes) are counted as unbuilt.
    """
    try:
        idx = get_module_index(track_name)
    except ValueError:
        return {"total": 0, "passed": 0, "failed": 0, "unbuilt": 0, "error": f"Track not in curriculum.yaml"}

    total = idx["total"]
    passed = 0
    failed = 0
    unbuilt = 0

    for num in range(1, total + 1):
        slug = idx["num_to_slug"][num]
        try:
            paths = get_module_paths(track_name, slug)
        except Exception:
            unbuilt += 1
            continue

        # Check if content exists
        md_path = paths["md"]
        has_content = md_path.exists() and md_path.stat().st_size >= 500

        # Check status JSON
        status_path = paths["status"]
        if status_path.exists():
            try:
                status_data = json.loads(status_path.read_text(encoding="utf-8"))
                # Support both formats: top-level "overall_status" and nested "overall.status"
                overall = status_data.get("overall_status", "")
                if not overall:
                    overall = status_data.get("overall", {}).get("status", "")
                if overall.upper() == "PASS":
                    passed += 1
                elif has_content:
                    failed += 1
                else:
                    unbuilt += 1
            except (json.JSONDecodeError, OSError):
                if has_content:
                    failed += 1
                else:
                    unbuilt += 1
        elif has_content:
            failed += 1  # Has content but never audited
        else:
            unbuilt += 1

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "unbuilt": unbuilt,
        "pass_rate": passed / total if total > 0 else 0,
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


# ---------------------------------------------------------------------------
# Dependency checking
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Priority scoring
# ---------------------------------------------------------------------------

def compute_priority_score(track_name: str, scan: dict, track_scans: dict[str, dict],
                           dispatcher_state: dict) -> float:
    """Compute weighted priority score for tiebreaking.

    Primary order is user-specified (TRACKS list). This score is secondary.
    """
    total = scan.get("total", 1)
    passed = scan.get("passed", 0)
    failed = scan.get("failed", 0)
    unbuilt = scan.get("unbuilt", 0)

    # Quick win: 10 * (pass/total)^2 — boost near-complete tracks
    ratio = passed / total if total > 0 else 0
    quick_win = 10 * (ratio ** 2)

    # Impact: min(10, failing/10) — big failing tracks matter more
    impact = min(10, (failed + unbuilt) / 10)

    # Success rate from batch_state history
    batch_state = read_batch_state(track_name)
    if batch_state and batch_state.get("summary"):
        summary = batch_state["summary"]
        hist_processed = summary.get("processed", 0)
        hist_passed = summary.get("passed", 0)
        success_rate = (hist_passed / hist_processed * 10) if hist_processed > 0 else 5
    else:
        success_rate = 5  # neutral default

    # Dependency boost: count how many tracks depend on this one
    downstream_count = 0
    for t in TRACKS:
        for dep_track, _ in t[4]:
            if dep_track == track_name:
                downstream_count += 1
    dependency_score = min(10, downstream_count * 2)

    # Cost penalty
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


# ---------------------------------------------------------------------------
# Strategy selection
# ---------------------------------------------------------------------------

def select_strategy(track_name: str, scan: dict) -> tuple[str, list[str]]:
    """Determine execution strategy for a track.

    Returns (mode, extra_args) for batch_gemini_runner.
    """
    unbuilt = scan.get("unbuilt", 0)
    failed = scan.get("failed", 0)

    if unbuilt > 0:
        # Has unbuilt modules — use auto mode (builds new, fixes existing)
        return "auto", []
    elif failed > 0:
        # All built, some failing — use fix mode with retry-failures
        return "fix", ["--retry-failures"]
    else:
        # Everything passes
        return "fix", []  # Will be skipped as DONE anyway


# ---------------------------------------------------------------------------
# Dispatcher state management
# ---------------------------------------------------------------------------

def load_dispatcher_state(state_file: Path) -> dict:
    """Load or initialize dispatcher state."""
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "started": datetime.now(timezone.utc).isoformat(),
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
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
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


# ---------------------------------------------------------------------------
# Subprocess dispatch
# ---------------------------------------------------------------------------

def dispatch_track(track_name: str, mode: str, extra_args: list[str],
                   timeout: int = SUBPROCESS_TIMEOUT_SECONDS) -> dict:
    """Dispatch batch_gemini_runner as a subprocess.

    Returns dict with:
        success: bool
        returncode: int
        duration_s: float
        quota_hit: bool
        stderr: str (truncated)
        stdout_tail: str (last 2000 chars)
    """
    cmd = [
        VENV_PYTHON, BATCH_RUNNER, track_name,
        "--mode", mode,
        "--max-consecutive-failures", str(RUNNER_MAX_CONSECUTIVE_FAILURES),
        "--max-failure-rate", str(RUNNER_MAX_FAILURE_RATE),
        "--json-log",
    ] + extra_args

    log.info(f"  Dispatching: {' '.join(cmd[-6:])}")  # Show last args for readability

    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_ROOT),
        )
        elapsed = time.monotonic() - start
        stderr = result.stderr[-2000:] if result.stderr else ""
        stdout_tail = result.stdout[-2000:] if result.stdout else ""

        # Detect quota hit from stderr/stdout
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
        return {
            "success": False,
            "returncode": -1,
            "duration_s": round(elapsed, 1),
            "quota_hit": False,
            "stderr": "TimeoutExpired",
            "stdout_tail": "",
        }
    except Exception as e:
        elapsed = time.monotonic() - start
        log.error(f"  Subprocess error: {e}")
        return {
            "success": False,
            "returncode": -2,
            "duration_s": round(elapsed, 1),
            "quota_hit": False,
            "stderr": str(e),
            "stdout_tail": "",
        }


def dispatch_claude_fix(track_name: str, slug: str, module_num: int,
                        failure_data: dict = None,
                        timeout: int = CLAUDE_FIX_TIMEOUT) -> dict:
    """Dispatch Claude Code to do a full rebuild of an escalated module.

    Uses /full-rebuild for seminar tracks and /full-rebuild-core for core tracks.
    Runs claude -p in non-interactive mode. Gives Claude the full context
    from the failure file so it doesn't repeat what Gemini already tried.
    Waits for completion before returning.

    Returns dict with:
        success: bool
        returncode: int
        duration_s: float
        stdout_tail: str
    """
    is_seminar = track_name in SEMINAR_TRACKS

    # Build context from failure data
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

    # Use the appropriate full-rebuild command based on track type
    if is_seminar:
        rebuild_cmd = f"/full-rebuild {track_name} {module_num}"
    else:
        rebuild_cmd = f"/full-rebuild-core {track_name} {module_num}"

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
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_ROOT),
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
        return {
            "success": False,
            "returncode": -1,
            "duration_s": round(elapsed, 1),
            "stdout_tail": "TimeoutExpired",
        }
    except Exception as e:
        elapsed = time.monotonic() - start
        log.error(f"  Claude fix error for {track_name}/{slug}: {e}")
        return {
            "success": False,
            "returncode": -2,
            "duration_s": round(elapsed, 1),
            "stdout_tail": str(e),
        }


# ---------------------------------------------------------------------------
# Progress detection
# ---------------------------------------------------------------------------

def detect_progress(track_name: str, scan_before: dict, scan_after: dict) -> dict:
    """Compare before/after scans to detect progress."""
    delta_passed = scan_after["passed"] - scan_before["passed"]
    delta_failed = scan_after["failed"] - scan_before["failed"]
    delta_unbuilt = scan_before["unbuilt"] - scan_after["unbuilt"]  # unbuilt should decrease

    made_progress = delta_passed > 0 or delta_unbuilt > 0

    return {
        "delta_passed": delta_passed,
        "delta_failed": delta_failed,
        "delta_unbuilt": delta_unbuilt,
        "made_progress": made_progress,
    }


# ---------------------------------------------------------------------------
# Main dispatcher loop
# ---------------------------------------------------------------------------

class BatchDispatcher:
    """Autonomous scheduler that processes tracks in priority order."""

    def __init__(self, *, one_shot=False, dry_run=False,
                 include_tracks=None, exclude_tracks=None,
                 max_runtime_hours=None, force_track=None):
        self.one_shot = one_shot
        self.dry_run = dry_run
        self.include_tracks = set(include_tracks) if include_tracks else None
        self.exclude_tracks = set(exclude_tracks) if exclude_tracks else set()
        self.max_runtime_hours = max_runtime_hours
        self.force_track = force_track
        self.start_time = time.monotonic()

        self.state_file = PROJECT_ROOT / DISPATCHER_STATE_FILE
        self.state = load_dispatcher_state(self.state_file)

    def _should_include_track(self, track_name: str) -> bool:
        """Check if track passes include/exclude filters."""
        if track_name in self.exclude_tracks:
            return False
        if self.include_tracks is not None and track_name not in self.include_tracks:
            return False
        return True

    def _runtime_exceeded(self) -> bool:
        """Check if max runtime has been exceeded."""
        if self.max_runtime_hours is None:
            return False
        elapsed_hours = (time.monotonic() - self.start_time) / 3600
        return elapsed_hours >= self.max_runtime_hours

    def _scan_all_tracks(self) -> dict[str, dict]:
        """Scan all tracks and return their status."""
        scans = {}
        for priority, track_name, expected, ttype, deps in TRACKS:
            if not self._should_include_track(track_name):
                continue
            scans[track_name] = scan_track(track_name)
        return scans

    def _update_track_states(self, track_scans: dict[str, dict]):
        """Update state machine for all tracks based on current scans."""
        now = datetime.now(timezone.utc).isoformat()

        for priority, track_name, expected, ttype, deps in TRACKS:
            if not self._should_include_track(track_name):
                continue

            scan = track_scans.get(track_name)
            if not scan or scan.get("error"):
                continue

            dstate = get_track_dstate(self.state, track_name)

            # Always update scan data for UI visibility
            dstate["passed"] = scan["passed"]
            dstate["failed"] = scan["failed"]
            dstate["unbuilt"] = scan.get("unbuilt", 0)
            dstate["total"] = scan["total"]
            dstate["pass_rate"] = scan.get("pass_rate", 0)
            dstate["escalated_to_claude"] = self._count_escalated(track_name)

            # Already DONE? Check if still done
            if dstate["state"] == TrackState.DONE:
                if scan["passed"] < scan["total"]:
                    # Regression — something changed
                    dstate["state"] = TrackState.PENDING
                    log.info(f"  {track_name}: Regression detected, re-evaluating")
                continue

            # RUNNING tracks: verify they're actually running (lock file exists)
            if dstate["state"] == TrackState.RUNNING:
                lock_file = BATCH_STATE_DIR / "locks" / f"batch_{track_name}.lock"
                if lock_file.exists():
                    continue  # Actually running
                # Orphaned RUNNING state — process was killed or crashed
                log.info(f"  {track_name}: Orphaned RUNNING (no lock), resetting to PENDING")
                dstate["state"] = TrackState.PENDING
                # Fall through to re-evaluate

            # Check for DONE
            if scan["passed"] >= scan["total"] and scan["total"] > 0:
                dstate["state"] = TrackState.DONE
                continue

            # Expire COOLDOWN
            if dstate["state"] == TrackState.COOLDOWN:
                cooldown_until = dstate.get("cooldown_until")
                if cooldown_until:
                    try:
                        until = datetime.fromisoformat(cooldown_until)
                        if datetime.now(timezone.utc) >= until:
                            dstate["state"] = TrackState.ELIGIBLE
                            log.info(f"  {track_name}: Cooldown expired, now ELIGIBLE")
                        else:
                            continue  # Still cooling down
                    except (ValueError, TypeError):
                        dstate["state"] = TrackState.ELIGIBLE
                else:
                    dstate["state"] = TrackState.ELIGIBLE

            # STALLED tracks: check if should be revisited
            if dstate["state"] == TrackState.STALLED:
                # Will be promoted after full rotation (handled in _pick_track)
                continue

            # Check dependencies
            deps_ok, unmet = check_dependencies(track_name, track_scans)
            if not deps_ok:
                dstate["state"] = TrackState.BLOCKED
                dstate["blocked_by"] = unmet  # e.g. ["a2 needs 80% (currently 73%)"]
                continue
            else:
                dstate.pop("blocked_by", None)

            # Dependencies met → ELIGIBLE
            if dstate["state"] in (TrackState.PENDING, TrackState.BLOCKED):
                dstate["state"] = TrackState.ELIGIBLE

    def _pick_track(self, track_scans: dict[str, dict]) -> str | None:
        """Pick the highest-priority eligible track to dispatch.

        Returns track name or None if nothing to do.
        """
        # Force track override
        if self.force_track:
            dstate = get_track_dstate(self.state, self.force_track)
            if dstate["state"] == TrackState.DONE:
                log.info(f"  {self.force_track}: Already DONE")
                return None
            return self.force_track

        # Collect eligible tracks
        eligible = []
        for priority, track_name, expected, ttype, deps in TRACKS:
            if not self._should_include_track(track_name):
                continue
            dstate = get_track_dstate(self.state, track_name)
            if dstate["state"] == TrackState.ELIGIBLE:
                scan = track_scans.get(track_name, {})
                score = compute_priority_score(track_name, scan, track_scans, self.state)
                eligible.append((priority, score, track_name))

        if eligible:
            # Sort by priority first (ascending), then by score (descending)
            eligible.sort(key=lambda x: (x[0], -x[1]))
            return eligible[0][2]

        # No eligible tracks — check if STALLED tracks should be revisited
        all_stalled = [
            (p, name) for p, name, _, _, _ in TRACKS
            if self._should_include_track(name) and
            get_track_dstate(self.state, name)["state"] == TrackState.STALLED
        ]

        if all_stalled:
            # Promote all STALLED → ELIGIBLE for next rotation
            for _, name in all_stalled:
                dstate = get_track_dstate(self.state, name)
                dstate["state"] = TrackState.ELIGIBLE
                dstate["stall_count"] = 0
                log.info(f"  {name}: Promoting STALLED → ELIGIBLE (rotation)")
            self.state["stats"]["rotations_completed"] = (
                self.state["stats"].get("rotations_completed", 0) + 1
            )
            save_dispatcher_state(self.state, self.state_file)
            # Pick from the newly promoted tracks
            return self._pick_track(track_scans)

        return None  # All DONE or BLOCKED

    def _count_escalated(self, track_name: str) -> int:
        """Count modules escalated to Claude for this track."""
        failures_dir = BATCH_STATE_DIR / "failures" / track_name
        if not failures_dir.exists():
            return 0
        count = 0
        for f in failures_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("escalated"):
                    count += 1
            except Exception:
                pass
        return count

    def _get_escalated_modules(self, track_name: str) -> list[dict]:
        """Get all escalated modules for a track."""
        failures_dir = FAILURES_DIR / track_name
        if not failures_dir.exists():
            return []
        results = []
        for f in sorted(failures_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("escalated"):
                    data["_failure_file"] = str(f)
                    results.append(data)
            except Exception:
                pass
        return results

    def _process_escalations(self, track_name: str, track_scans: dict) -> int:
        """Process escalated modules for a track by dispatching Claude one by one.

        Returns the number of modules successfully fixed.
        """
        escalated = self._get_escalated_modules(track_name)
        if not escalated:
            return 0

        log.info(f"  Escalations: {len(escalated)} modules for {track_name}")

        try:
            idx = get_module_index(track_name)
        except ValueError:
            log.warning(f"  Cannot get module index for {track_name}")
            return 0

        fixed = 0
        for esc in escalated:
            if _shutdown_requested:
                log.info("  Shutdown requested, stopping escalation processing.")
                break

            slug = esc["slug"]
            module_num = idx["slug_to_num"].get(slug)
            if module_num is None:
                log.warning(f"  Cannot find module number for {slug} in {track_name}")
                continue

            log.info(f"  Dispatching Claude for {track_name}/{slug} (#{module_num})...")
            result = dispatch_claude_fix(track_name, slug, module_num, failure_data=esc)
            log.info(
                f"  Claude result: rc={result['returncode']}, "
                f"duration={result['duration_s']}s"
            )

            if result["success"]:
                # Re-audit to confirm fix
                scan_after = scan_track(track_name)
                # Check if this specific module now passes
                failure_file = Path(esc["_failure_file"])
                if failure_file.exists():
                    failure_file.unlink()
                    log.info(f"  Cleared failure file: {failure_file}")
                fixed += 1
                log.info(f"  Fixed: {track_name}/{slug}")
            else:
                log.warning(
                    f"  Claude could not fix {track_name}/{slug} "
                    f"(rc={result['returncode']})"
                )
                # Leave failure file — still escalated for next attempt

        if fixed > 0:
            log.info(f"  Escalation summary: {fixed}/{len(escalated)} fixed for {track_name}")

        return fixed

    def _format_track_table(self, track_scans: dict[str, dict]) -> str:
        """Format a readable table of all tracks and their status."""
        lines = []
        lines.append(f"{'#':>2}  {'Track':<16}  {'State':<10}  {'Pass':>5}  {'Fail':>5}  {'New':>5}  {'Total':>5}  {'Rate':>6}  {'Esc':>4}  {'Score':>6}")
        lines.append("-" * 90)

        for priority, track_name, expected, ttype, deps in TRACKS:
            if not self._should_include_track(track_name):
                continue

            scan = track_scans.get(track_name, {})
            dstate = get_track_dstate(self.state, track_name)

            total = scan.get("total", 0)
            passed = scan.get("passed", 0)
            failed = scan.get("failed", 0)
            unbuilt = scan.get("unbuilt", 0)
            rate = f"{scan.get('pass_rate', 0):.0%}"
            state = dstate["state"]
            score = compute_priority_score(track_name, scan, track_scans, self.state)
            esc = self._count_escalated(track_name)

            lines.append(
                f"{priority:>2}  {track_name:<16}  {state:<10}  {passed:>5}  {failed:>5}  {unbuilt:>5}  {total:>5}  {rate:>6}  {esc:>4}  {score:>6.2f}"
            )

        return "\n".join(lines)

    def run(self):
        """Main dispatcher loop."""
        log.info("=" * 70)
        log.info("  Smart Batch Dispatcher — Starting")
        log.info("=" * 70)

        if self.dry_run:
            log.info("  Mode: DRY RUN (no dispatching)")
        elif self.one_shot:
            log.info("  Mode: ONE-SHOT (single dispatch)")
        else:
            log.info("  Mode: CONTINUOUS")
            if self.max_runtime_hours:
                log.info(f"  Max runtime: {self.max_runtime_hours}h")

        cycle = 0
        while True:
            cycle += 1

            if _shutdown_requested:
                log.info("Shutdown requested. Exiting.")
                break

            if self._runtime_exceeded():
                log.info(f"Max runtime ({self.max_runtime_hours}h) exceeded. Exiting.")
                break

            log.info(f"\n--- Cycle {cycle} ---")

            # Step 1: Scan all tracks
            log.info("Scanning tracks...")
            track_scans = self._scan_all_tracks()

            # Step 2: Update states
            self._update_track_states(track_scans)

            # Step 3: Show status table
            table = self._format_track_table(track_scans)
            log.info(f"\n{table}\n")

            # Step 4: Pick track
            track_name = self._pick_track(track_scans)

            if track_name is None:
                # Check if everything is DONE
                active = [
                    name for _, name, _, _, _ in TRACKS
                    if self._should_include_track(name) and
                    get_track_dstate(self.state, name)["state"] not in (TrackState.DONE, TrackState.BLOCKED)
                ]
                if not active:
                    log.info("All tracks are DONE or BLOCKED. Exiting.")
                    break
                else:
                    # Everything is in cooldown — wait
                    log.info("All eligible tracks in cooldown. Waiting 60s...")
                    save_dispatcher_state(self.state, self.state_file)
                    time.sleep(60)
                    continue

            scan_before = track_scans[track_name]
            dstate = get_track_dstate(self.state, track_name)

            # Step 5: Select strategy
            mode, extra_args = select_strategy(track_name, scan_before)
            log.info(f"Selected: {track_name} (mode={mode}, pass={scan_before['passed']}/{scan_before['total']})")

            if self.dry_run:
                log.info(f"  DRY RUN: Would dispatch {track_name} --mode {mode} {' '.join(extra_args)}")
                if self.one_shot:
                    break
                continue

            # Step 6: Dispatch
            dstate["state"] = TrackState.RUNNING
            dstate["last_dispatch"] = datetime.now(timezone.utc).isoformat()
            dstate["dispatches"] = dstate.get("dispatches", 0) + 1
            self.state["stats"]["total_dispatches"] = self.state["stats"].get("total_dispatches", 0) + 1
            save_dispatcher_state(self.state, self.state_file)

            result = dispatch_track(track_name, mode, extra_args)

            # Step 7: Analyze result
            log.info(f"  Dispatch complete: rc={result['returncode']}, duration={result['duration_s']}s, quota_hit={result['quota_hit']}")

            # Re-scan to measure progress
            scan_after = scan_track(track_name)
            progress = detect_progress(track_name, scan_before, scan_after)
            log.info(f"  Progress: +{progress['delta_passed']} passed, {progress['delta_failed']:+d} failed, {progress['delta_unbuilt']:+d} unbuilt")

            # Record dispatch history
            dispatch_record = {
                "track": track_name,
                "mode": mode,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_s": result["duration_s"],
                "success": result["success"],
                "quota_hit": result["quota_hit"],
                "progress": progress,
                "scan_after": {
                    "passed": scan_after["passed"],
                    "failed": scan_after["failed"],
                    "unbuilt": scan_after["unbuilt"],
                    "total": scan_after["total"],
                },
            }
            self.state["dispatch_history"].append(dispatch_record)
            # Keep last 200 records
            if len(self.state["dispatch_history"]) > 200:
                self.state["dispatch_history"] = self.state["dispatch_history"][-200:]

            # Update track state
            dstate["last_result"] = {
                "success": result["success"],
                "quota_hit": result["quota_hit"],
                "duration_s": result["duration_s"],
                "progress": progress["made_progress"],
            }
            dstate["last_passed"] = scan_after["passed"]
            dstate["last_failed"] = scan_after["failed"]

            # Step 7.5: Process escalated modules (Claude fixes, one at a time)
            esc_fixed = self._process_escalations(track_name, track_scans)
            if esc_fixed > 0:
                # Re-scan after Claude fixes to get accurate counts
                scan_after = scan_track(track_name)
                progress = detect_progress(track_name, scan_before, scan_after)
                log.info(
                    f"  Post-escalation progress: +{progress['delta_passed']} passed, "
                    f"{progress['delta_failed']:+d} failed"
                )
                dstate["last_passed"] = scan_after["passed"]
                dstate["last_failed"] = scan_after["failed"]

            # Step 8: State transitions
            if scan_after["passed"] >= scan_after["total"] and scan_after["total"] > 0:
                dstate["state"] = TrackState.DONE
                log.info(f"  {track_name}: DONE ({scan_after['passed']}/{scan_after['total']})")
            elif result["quota_hit"]:
                # Quota hit → COOLDOWN
                cooldown_until = datetime.fromtimestamp(
                    time.time() + COOLDOWN_SECONDS, tz=timezone.utc
                ).isoformat()
                dstate["state"] = TrackState.COOLDOWN
                dstate["cooldown_until"] = cooldown_until
                self.state["stats"]["total_cooldowns"] = self.state["stats"].get("total_cooldowns", 0) + 1
                log.info(f"  {track_name}: COOLDOWN until {cooldown_until} (quota hit)")
            elif result["returncode"] == -1:
                # Subprocess timeout → COOLDOWN
                cooldown_until = datetime.fromtimestamp(
                    time.time() + COOLDOWN_SECONDS, tz=timezone.utc
                ).isoformat()
                dstate["state"] = TrackState.COOLDOWN
                dstate["cooldown_until"] = cooldown_until
                log.info(f"  {track_name}: COOLDOWN (subprocess timeout)")
            elif not progress["made_progress"]:
                # No progress
                dstate["stall_count"] = dstate.get("stall_count", 0) + 1
                if dstate["stall_count"] >= MAX_STALL_COUNT:
                    dstate["state"] = TrackState.STALLED
                    self.state["stats"]["total_stalls"] = self.state["stats"].get("total_stalls", 0) + 1
                    log.info(f"  {track_name}: STALLED ({dstate['stall_count']}x zero progress)")
                else:
                    dstate["state"] = TrackState.ELIGIBLE
                    log.info(f"  {track_name}: No progress ({dstate['stall_count']}/{MAX_STALL_COUNT}), retrying later")
            else:
                # Made progress → stay ELIGIBLE
                dstate["state"] = TrackState.ELIGIBLE
                dstate["stall_count"] = 0

            # Step 9: Save and pause
            save_dispatcher_state(self.state, self.state_file)

            if self.one_shot:
                log.info("One-shot mode: exiting after single dispatch.")
                break

            log.info(f"Pausing {INTER_DISPATCH_PAUSE}s before next cycle...")
            time.sleep(INTER_DISPATCH_PAUSE)

        # Final summary
        self._print_summary()
        save_dispatcher_state(self.state, self.state_file)

    def _print_summary(self):
        """Print final summary report."""
        stats = self.state.get("stats", {})
        elapsed = time.monotonic() - self.start_time
        elapsed_h = elapsed / 3600

        log.info("\n" + "=" * 70)
        log.info("  Dispatcher Summary")
        log.info("=" * 70)
        log.info(f"  Runtime: {elapsed_h:.1f}h")
        log.info(f"  Total dispatches: {stats.get('total_dispatches', 0)}")
        log.info(f"  Cooldowns: {stats.get('total_cooldowns', 0)}")
        log.info(f"  Stalls: {stats.get('total_stalls', 0)}")
        log.info(f"  Rotations: {stats.get('rotations_completed', 0)}")

        # Per-track summary
        done = []
        stalled = []
        blocked = []
        eligible = []
        for _, name, _, _, _ in TRACKS:
            if not self._should_include_track(name):
                continue
            dstate = get_track_dstate(self.state, name)
            s = dstate["state"]
            if s == TrackState.DONE:
                done.append(name)
            elif s == TrackState.STALLED:
                stalled.append(name)
            elif s == TrackState.BLOCKED:
                blocked.append(name)
            else:
                eligible.append(name)

        log.info(f"\n  DONE ({len(done)}): {', '.join(done) if done else '-'}")
        log.info(f"  STALLED ({len(stalled)}): {', '.join(stalled) if stalled else '-'}")
        log.info(f"  BLOCKED ({len(blocked)}): {', '.join(blocked) if blocked else '-'}")
        log.info(f"  ELIGIBLE ({len(eligible)}): {', '.join(eligible) if eligible else '-'}")
        log.info(f"\n  State file: {self.state_file}")


# ---------------------------------------------------------------------------
# CLI: scan command
# ---------------------------------------------------------------------------

def cmd_scan(args):
    """Scan all tracks and display priority table."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    dispatcher = BatchDispatcher(
        dry_run=True,
        include_tracks=args.include_tracks,
        exclude_tracks=args.exclude_tracks or [],
    )

    track_scans = dispatcher._scan_all_tracks()
    dispatcher._update_track_states(track_scans)

    table = dispatcher._format_track_table(track_scans)
    print(table)

    # Show what would be picked
    pick = dispatcher._pick_track(track_scans)
    print(f"\nNext dispatch: {pick or 'None (all DONE/BLOCKED)'}")

    save_dispatcher_state(dispatcher.state, dispatcher.state_file)


# ---------------------------------------------------------------------------
# CLI: status command
# ---------------------------------------------------------------------------

def cmd_status(args):
    """Show current dispatcher state."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    state_file = PROJECT_ROOT / DISPATCHER_STATE_FILE
    if not state_file.exists():
        print("No dispatcher state found. Run 'scan' or 'run' first.")
        return

    state = json.loads(state_file.read_text(encoding="utf-8"))
    stats = state.get("stats", {})

    print("=" * 70)
    print("  Smart Batch Dispatcher — Current State")
    print("=" * 70)
    print(f"  Started: {state.get('started', 'unknown')}")
    print(f"  Last updated: {state.get('last_updated', 'unknown')}")
    print(f"  Total dispatches: {stats.get('total_dispatches', 0)}")
    print(f"  Cooldowns: {stats.get('total_cooldowns', 0)}")
    print(f"  Stalls: {stats.get('total_stalls', 0)}")
    print(f"  Rotations: {stats.get('rotations_completed', 0)}")

    tracks = state.get("tracks", {})
    if tracks:
        print(f"\n{'Track':<16}  {'State':<10}  {'Dispatches':>10}  {'Pass':>5}  {'Fail':>5}  {'Stalls':>6}")
        print("-" * 70)
        for _, name, _, _, _ in TRACKS:
            if name not in tracks:
                continue
            t = tracks[name]
            print(
                f"{name:<16}  {t['state']:<10}  {t.get('dispatches', 0):>10}  "
                f"{t.get('last_passed', 0):>5}  {t.get('last_failed', 0):>5}  "
                f"{t.get('stall_count', 0):>6}"
            )

    # Recent dispatch history
    history = state.get("dispatch_history", [])
    if history:
        recent = history[-5:]
        print(f"\nRecent dispatches (last {len(recent)}):")
        for d in recent:
            p = d.get("progress", {})
            print(
                f"  {d['timestamp'][:19]}  {d['track']:<16}  "
                f"mode={d['mode']}  +{p.get('delta_passed', 0)}pass  "
                f"{'QUOTA' if d.get('quota_hit') else 'OK'}"
            )


# ---------------------------------------------------------------------------
# CLI: run command
# ---------------------------------------------------------------------------

def cmd_run(args):
    """Run the dispatcher (continuous or one-shot)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # Install signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    dispatcher = BatchDispatcher(
        one_shot=args.one_shot,
        dry_run=args.dry_run,
        include_tracks=args.include_tracks,
        exclude_tracks=args.exclude_tracks or [],
        max_runtime_hours=args.max_runtime_hours,
    )

    dispatcher.run()


# ---------------------------------------------------------------------------
# CLI: dispatch-one command
# ---------------------------------------------------------------------------

def cmd_dispatch_one(args):
    """Force-dispatch a specific track."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    dispatcher = BatchDispatcher(
        one_shot=True,
        force_track=args.track,
        dry_run=args.dry_run,
    )

    dispatcher.run()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Smart Batch Dispatcher — Autonomous curriculum batch processing scheduler",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- scan ---
    p_scan = subparsers.add_parser("scan", help="Scan tracks, show priorities (no dispatch)")
    p_scan.add_argument("--include-tracks", nargs="+", metavar="TRACK", help="Only include these tracks")
    p_scan.add_argument("--exclude-tracks", nargs="+", metavar="TRACK", help="Exclude these tracks")

    # --- status ---
    p_status = subparsers.add_parser("status", help="Show current dispatcher state")

    # --- run ---
    p_run = subparsers.add_parser("run", help="Run dispatcher (continuous by default)")
    p_run.add_argument("--one-shot", action="store_true", help="Single dispatch cycle, then exit")
    p_run.add_argument("--dry-run", action="store_true", help="Show what would be dispatched without running")
    p_run.add_argument("--include-tracks", nargs="+", metavar="TRACK", help="Only include these tracks")
    p_run.add_argument("--exclude-tracks", nargs="+", metavar="TRACK", help="Exclude these tracks")
    p_run.add_argument("--max-runtime-hours", type=float, metavar="HOURS", help="Stop after N hours")

    # --- dispatch-one ---
    p_one = subparsers.add_parser("dispatch-one", help="Force-dispatch a specific track")
    p_one.add_argument("--track", required=True, help="Track name to dispatch")
    p_one.add_argument("--dry-run", action="store_true", help="Show what would be dispatched")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "dispatch-one":
        cmd_dispatch_one(args)


if __name__ == "__main__":
    main()
