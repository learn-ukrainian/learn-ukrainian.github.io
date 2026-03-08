#!/usr/bin/env python3
"""
Batch Otaman Dispatcher — Autonomous scheduler using the Gemini Otaman pipeline.

Dispatches modules to Gemini's /otaman skill (Phases 0-7) via ask-gemini --allow-write.
Each otaman session is fully autonomous — no Claude in the loop.

Max 2 parallel sessions across DIFFERENT tracks (same track = file conflicts).

Usage:
    # Continuous mode — process everything
    .venv/bin/python scripts/batch_otaman.py run

    # Single module, then exit
    .venv/bin/python scripts/batch_otaman.py run --one-shot

    # Dry run — show what would be dispatched
    .venv/bin/python scripts/batch_otaman.py scan

    # Show current state
    .venv/bin/python scripts/batch_otaman.py status

    # Force a specific track
    .venv/bin/python scripts/batch_otaman.py dispatch-one --track a1

    # Filter tracks
    --include-tracks a1 a2 b1
    --exclude-tracks c2 b2-pro

    # Parallelism
    --workers 2  (default, max 2)

    # Safety timeout
    --max-runtime-hours 12
"""

import argparse
import fcntl
import json
import logging
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

# Ensure scripts/ is on sys.path for sibling imports
sys.path.insert(0, str(Path(__file__).parent))

from audit.status_cache import get_source_paths, read_status
from batch_dispatcher_config import (
    COOLDOWN_SECONDS,
    TRACK_BY_NAME,
    TRACKS,
    TrackState,
)
from batch_gemini_config import PROJECT_ROOT, VENV_PYTHON, get_module_index, get_module_paths

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

log = logging.getLogger("batch_otaman")

BRIDGE_SCRIPT = str(PROJECT_ROOT / "scripts" / "ai_agent_bridge" / "__main__.py")
STATE_FILE = PROJECT_ROOT / "batch_state" / "otaman_state.json"
FOREMAN_TIMEOUT = 45 * 60  # 45 minutes per module (Phases 0-7)
INTER_DISPATCH_PAUSE = 10  # Seconds between dispatches
MAX_WORKERS = 2

# Graceful shutdown
_shutdown_requested = False
_state_lock = Lock()


def _signal_handler(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True
    log.warning(f"Shutdown requested (signal {signum}). Finishing current modules...")


# ---------------------------------------------------------------------------
# Module scanning
# ---------------------------------------------------------------------------

def _is_content_complete(result) -> bool:
    """Check if a module is content-complete (activities deferred).

    Returns True if lesson gates pass but activities are deferred.
    """
    if result is None:
        return False
    gates = result.gates
    activities = gates.get("activities", {})
    lesson = gates.get("lesson", {})
    return (
        activities.get("status") == "deferred"
        and lesson.get("status") == "pass"
    )


def find_next_module(track_name: str, *, content_only: bool = True) -> dict | None:
    """Find the next unbuilt or failed module in a track.

    Returns dict with {num, slug, reason} or None if track is complete.
    Scans sequentially — returns first non-passing module.

    Args:
        content_only: When True (default), content-complete modules (activities
                      deferred) are treated as "done" for otaman purposes.
                      Set False for hetman to find them.
    """
    try:
        idx = get_module_index(track_name)
    except ValueError:
        return None

    track_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / track_name

    for num in range(1, idx["total"] + 1):
        slug = idx["num_to_slug"][num]
        try:
            paths = get_module_paths(track_name, slug)
        except Exception:
            return {"num": num, "slug": slug, "reason": "no_paths"}

        # Check if content exists
        md_path = paths["md"]
        has_content = md_path.exists() and md_path.stat().st_size >= 500

        if not has_content:
            return {"num": num, "slug": slug, "reason": "unbuilt"}

        # Check status cache
        status_path = paths["status"]
        source_paths = get_source_paths(track_dir, slug)
        result = read_status(status_path, source_paths=source_paths)

        if result is None:
            return {"num": num, "slug": slug, "reason": "no_status"}

        # Content-complete modules (activities deferred) — skip for otaman
        if content_only and _is_content_complete(result):
            continue

        if result.status.upper() != "PASS":
            return {"num": num, "slug": slug, "reason": "failed"}

        if not result.is_fresh:
            return {"num": num, "slug": slug, "reason": "stale"}

    return None  # All modules passing (or content-complete for otaman)


def find_next_enrichable(track_name: str) -> dict | None:
    """Find the next content-complete module that needs activity enrichment.

    Returns dict with {num, slug, reason} or None if no eligible modules.
    Used by hetman batch mode.
    """
    try:
        idx = get_module_index(track_name)
    except ValueError:
        return None

    track_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / track_name

    for num in range(1, idx["total"] + 1):
        slug = idx["num_to_slug"][num]
        try:
            paths = get_module_paths(track_name, slug)
        except Exception:
            continue

        status_path = paths["status"]
        source_paths = get_source_paths(track_dir, slug)
        result = read_status(status_path, source_paths=source_paths)

        if _is_content_complete(result):
            return {"num": num, "slug": slug, "reason": "activities_deferred"}

    return None  # No content-complete modules needing enrichment


def scan_track_summary(track_name: str) -> dict:
    """Quick summary of a track's status."""
    try:
        idx = get_module_index(track_name)
    except ValueError:
        return {"total": 0, "passed": 0, "content_complete": 0, "remaining": 0, "error": "not_found"}

    track_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / track_name
    passed = 0
    content_complete = 0
    total = idx["total"]

    for num in range(1, total + 1):
        slug = idx["num_to_slug"][num]
        try:
            paths = get_module_paths(track_name, slug)
        except Exception:
            continue

        md_path = paths["md"]
        if not (md_path.exists() and md_path.stat().st_size >= 500):
            continue

        status_path = paths["status"]
        source_paths = get_source_paths(track_dir, slug)
        result = read_status(status_path, source_paths=source_paths)

        if _is_content_complete(result):
            content_complete += 1
        elif result and result.status.upper() == "PASS":
            passed += 1

    remaining = total - passed - content_complete
    return {"total": total, "passed": passed, "content_complete": content_complete, "remaining": remaining}


def check_dependencies(track_name: str, track_summaries: dict) -> tuple[bool, list[str]]:
    """Check if all dependencies for a track are satisfied."""
    track_info = TRACK_BY_NAME.get(track_name)
    if not track_info:
        return False, [f"Unknown track: {track_name}"]

    deps = track_info[4]
    if not deps:
        return True, []

    unmet = []
    for dep_track, min_rate in deps:
        summary = track_summaries.get(dep_track)
        if summary is None or summary.get("total", 0) == 0:
            unmet.append(f"{dep_track}: not scanned")
            continue
        rate = summary["passed"] / summary["total"]
        if rate < min_rate:
            unmet.append(f"{dep_track}: {rate:.0%} < {min_rate:.0%}")

    return len(unmet) == 0, unmet


# ---------------------------------------------------------------------------
# Otaman dispatch
# ---------------------------------------------------------------------------

def dispatch_otaman(track_name: str, num: int, slug: str,
                    timeout: int = FOREMAN_TIMEOUT) -> dict:
    """Dispatch a single module to the Gemini Otaman.

    Calls: ask-gemini "/otaman {track} {num}" --task-id otaman-{slug}
           --allow-write --model gemini-3.1-pro-preview

    Returns dict with success, returncode, duration_s, quota_hit, stderr.
    """
    task_id = f"otaman-{slug}"

    cmd = [
        VENV_PYTHON, BRIDGE_SCRIPT, "ask-gemini",
        f"otaman {track_name} {num}",
        "--task-id", task_id,
        "--allow-write",
        "--model", "gemini-3.1-pro-preview",
        "--stdout-only",
    ]

    log.info(f"  [{track_name}] Dispatching: otaman {track_name} {num} (slug={slug})")

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

        combined = (stderr + stdout_tail).lower()
        quota_hit = any(kw in combined for kw in (
            "quota", "429", "rate limit", "resource_exhausted"
        ))

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
        log.error(f"  [{track_name}] Otaman timeout after {elapsed:.0f}s for {slug}")
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
        log.error(f"  [{track_name}] Otaman error for {slug}: {e}")
        return {
            "success": False,
            "returncode": -2,
            "duration_s": round(elapsed, 1),
            "quota_hit": False,
            "stderr": str(e),
            "stdout_tail": "",
        }


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def _state_lockfile() -> Path:
    """Path for the state file advisory lock."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    return STATE_FILE.with_suffix(".lock")


def load_state() -> dict:
    """Load or initialize dispatcher state (with file lock for inter-process safety)."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock_path = _state_lockfile()
    try:
        with open(lock_path, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_SH)
            try:
                if STATE_FILE.exists():
                    return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN)
    except OSError:
        # Fallback: read without lock
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
    return {
        "started": datetime.now(UTC).isoformat(),
        "tracks": {},
        "history": [],
        "running_tracks": [],
        "stats": {
            "total_dispatches": 0,
            "total_modules_passed": 0,
            "total_quota_hits": 0,
        },
    }


def save_state(state: dict):
    """Save state atomically (with file lock for inter-process safety)."""
    with _state_lock:
        state["last_updated"] = datetime.now(UTC).isoformat()
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        lock_path = _state_lockfile()
        try:
            with open(lock_path, "w") as lf:
                fcntl.flock(lf, fcntl.LOCK_EX)
                try:
                    tmp = STATE_FILE.with_suffix(".tmp")
                    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
                    tmp.replace(STATE_FILE)
                finally:
                    fcntl.flock(lf, fcntl.LOCK_UN)
        except OSError as e:
            log.warning(f"File lock failed during save: {e}. Writing without lock.")
            tmp = STATE_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(STATE_FILE)


def get_track_state(state: dict, track_name: str) -> dict:
    """Get or create per-track state."""
    if track_name not in state["tracks"]:
        state["tracks"][track_name] = {
            "state": TrackState.PENDING,
            "dispatches": 0,
            "last_dispatch": None,
            "last_slug": None,
            "cooldown_until": None,
            "consecutive_failures": 0,
        }
    return state["tracks"][track_name]


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

class BatchOtaman:
    """Autonomous scheduler that dispatches modules to Gemini Otaman."""

    def __init__(self, *, one_shot=False, dry_run=False,
                 include_tracks=None, exclude_tracks=None,
                 max_runtime_hours=None, force_track=None,
                 workers=MAX_WORKERS):
        self.one_shot = one_shot
        self.dry_run = dry_run
        self.include_tracks = set(include_tracks) if include_tracks else None
        self.exclude_tracks = set(exclude_tracks) if exclude_tracks else set()
        self.max_runtime_hours = max_runtime_hours
        self.force_track = force_track
        self.workers = min(workers, MAX_WORKERS)
        self.start_time = time.monotonic()
        self.state = load_state()
        # Tracks currently running (prevent same-track parallel)
        self._running_tracks: set[str] = set()
        self._running_lock = Lock()
        self._daemon_lock_fd = None
        # Crash recovery: only in non-dry-run mode and only if we hold the daemon lock (#603)
        if not self.dry_run:
            self._acquire_daemon_lock()
            stale_running = self.state.get("running_tracks", [])
            if stale_running:
                log.warning(f"Crash recovery: clearing {len(stale_running)} stale running tracks: {stale_running}")
                for track_name in stale_running:
                    ts = get_track_state(self.state, track_name)
                    if ts["state"] == TrackState.RUNNING:
                        ts["state"] = TrackState.ELIGIBLE
                self.state["running_tracks"] = []
                save_state(self.state)

    def _acquire_daemon_lock(self):
        """Acquire exclusive daemon lock to prevent multiple dispatchers (#603)."""
        daemon_lock_path = STATE_FILE.parent / "otaman_daemon.lock"
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._daemon_lock_fd = open(daemon_lock_path, "w")  # noqa: SIM115 — fd kept open for flock lifetime
            fcntl.flock(self._daemon_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._daemon_lock_fd.write(str(os.getpid()))
            self._daemon_lock_fd.flush()
        except BlockingIOError:
            log.error("Another batch_otaman dispatcher is already running. Exiting.")
            sys.exit(1)
        except OSError as e:
            log.warning(f"Could not acquire daemon lock: {e}. Proceeding without lock.")

    def _release_daemon_lock(self):
        """Release daemon lock on clean exit."""
        if self._daemon_lock_fd:
            try:
                fcntl.flock(self._daemon_lock_fd, fcntl.LOCK_UN)
                self._daemon_lock_fd.close()
            except OSError:
                pass
            self._daemon_lock_fd = None

    def _should_include(self, track_name: str) -> bool:
        if track_name in self.exclude_tracks:
            return False
        return not (self.include_tracks is not None and track_name not in self.include_tracks)

    def _runtime_exceeded(self) -> bool:
        if self.max_runtime_hours is None:
            return False
        return (time.monotonic() - self.start_time) / 3600 >= self.max_runtime_hours

    def _scan_all(self) -> dict[str, dict]:
        """Scan all included tracks."""
        summaries = {}
        for _, track_name, _, _, _ in TRACKS:
            if self._should_include(track_name):
                summaries[track_name] = scan_track_summary(track_name)
        return summaries

    def _pick_modules(self, summaries: dict) -> list[dict]:
        """Pick up to `self.workers` modules from different eligible tracks.

        Returns list of {track, num, slug, reason} dicts.
        """
        candidates = []

        for _, track_name, _, _, _deps in TRACKS:
            if not self._should_include(track_name):
                continue

            # Skip tracks already running
            with self._running_lock:
                if track_name in self._running_tracks:
                    continue

            # Force track override
            if self.force_track and track_name != self.force_track:
                continue

            # Check track state
            ts = get_track_state(self.state, track_name)

            # Skip DONE
            summary = summaries.get(track_name, {})
            if summary.get("remaining", 1) == 0:
                ts["state"] = TrackState.DONE
                continue

            # Skip COOLDOWN
            if ts["state"] == TrackState.COOLDOWN:
                cooldown_until = ts.get("cooldown_until")
                if cooldown_until:
                    try:
                        until = datetime.fromisoformat(cooldown_until)
                        if datetime.now(UTC) < until:
                            continue
                    except (ValueError, TypeError):
                        # Replace malformed timestamp with fresh cooldown to prevent permanent brick
                        fresh = datetime.fromtimestamp(
                            time.time() + COOLDOWN_SECONDS, tz=UTC
                        ).isoformat()
                        log.warning(f"  [{track_name}] Malformed cooldown_until={cooldown_until!r}, reset to {fresh}")
                        ts["cooldown_until"] = fresh
                        continue
                ts["state"] = TrackState.ELIGIBLE

            # Check dependencies
            deps_ok, unmet = check_dependencies(track_name, summaries)
            if not deps_ok:
                ts["state"] = TrackState.BLOCKED
                ts["blocked_by"] = unmet
                continue

            # Too many consecutive failures — stall
            if ts.get("consecutive_failures", 0) >= 3:
                ts["state"] = TrackState.STALLED
                continue

            # Find next module
            module = find_next_module(track_name)
            if module is None:
                ts["state"] = TrackState.DONE
                continue

            module["track"] = track_name
            candidates.append(module)

            if len(candidates) >= self.workers:
                break

        return candidates

    def _dispatch_one(self, module: dict) -> dict:
        """Dispatch a single module and return result."""
        track = module["track"]
        num = module["num"]
        slug = module["slug"]

        with self._running_lock:
            self._running_tracks.add(track)
            self.state["running_tracks"] = sorted(self._running_tracks)
        save_state(self.state)

        try:
            result = dispatch_otaman(track, num, slug)

            # Check if module now passes
            passed_after = False
            if result["success"]:
                try:
                    paths = get_module_paths(track, slug)
                    track_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / track
                    source_paths = get_source_paths(track_dir, slug)
                    status = read_status(paths["status"], source_paths=source_paths)
                    if status and status.status.upper() == "PASS":
                        passed_after = True
                except Exception:
                    pass

            result["track"] = track
            result["num"] = num
            result["slug"] = slug
            result["passed_after"] = passed_after
            return result
        finally:
            with self._running_lock:
                self._running_tracks.discard(track)
                self.state["running_tracks"] = sorted(self._running_tracks)
            save_state(self.state)

    def _format_table(self, summaries: dict) -> str:
        """Format status table."""
        lines = []
        lines.append(f"{'#':>2}  {'Track':<16}  {'State':<10}  {'Pass':>5}  {'Prose':>5}  {'Remain':>6}  {'Total':>5}  {'Rate':>6}")
        lines.append("-" * 72)

        for _, track_name, _, _, _ in TRACKS:
            if not self._should_include(track_name):
                continue
            s = summaries.get(track_name, {})
            ts = get_track_state(self.state, track_name)
            total = s.get("total", 0)
            passed = s.get("passed", 0)
            content_complete = s.get("content_complete", 0)
            remaining = s.get("remaining", 0)
            rate = f"{passed/total:.0%}" if total > 0 else "0%"
            lines.append(
                f"{TRACK_BY_NAME[track_name][0]:>2}  {track_name:<16}  "
                f"{ts['state']:<10}  {passed:>5}  {content_complete:>5}  {remaining:>6}  {total:>5}  {rate:>6}"
            )

        return "\n".join(lines)

    def run(self):
        """Main loop."""
        log.info("=" * 60)
        log.info("  Batch Otaman Dispatcher")
        log.info(f"  Workers: {self.workers} | Mode: {'DRY RUN' if self.dry_run else 'ONE-SHOT' if self.one_shot else 'CONTINUOUS'}")
        log.info("=" * 60)

        cycle = 0
        while True:
            cycle += 1

            if _shutdown_requested:
                log.info("Shutdown requested. Exiting.")
                break

            if self._runtime_exceeded():
                log.info(f"Max runtime ({self.max_runtime_hours}h) exceeded.")
                break

            log.info(f"\n--- Cycle {cycle} ---")

            # Scan
            summaries = self._scan_all()
            table = self._format_table(summaries)
            total_passed = sum(s.get("passed", 0) for s in summaries.values())
            total_modules = sum(s.get("total", 0) for s in summaries.values())
            total_remaining = sum(s.get("remaining", 0) for s in summaries.values())
            log.info(f"\n{table}")
            log.info(f"\n  >>> {total_passed}/{total_modules} passing | {total_remaining} remaining\n")

            # Pick modules
            modules = self._pick_modules(summaries)

            if not modules:
                # Check if all done
                all_done = all(
                    get_track_state(self.state, name)["state"] in (TrackState.DONE, TrackState.BLOCKED, TrackState.STALLED)
                    for _, name, _, _, _ in TRACKS
                    if self._should_include(name)
                )
                if all_done:
                    log.info("All tracks DONE/BLOCKED/STALLED. Exiting.")
                    break

                # Everything in cooldown — wait
                log.info("No eligible modules. Waiting 60s...")
                save_state(self.state)
                time.sleep(60)
                continue

            if self.dry_run:
                for m in modules:
                    log.info(f"  DRY RUN: /otaman {m['track']} {m['num']} ({m['slug']}, {m['reason']})")
                if self.one_shot:
                    break
                continue

            # Dispatch (parallel if multiple)
            log.info(f"Dispatching {len(modules)} module(s):")
            for m in modules:
                log.info(f"  -> {m['track']} #{m['num']} ({m['slug']}) [{m['reason']}]")

            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures: dict[Future, dict] = {}
                for m in modules:
                    ts = get_track_state(self.state, m["track"])
                    ts["state"] = TrackState.RUNNING
                    ts["last_dispatch"] = datetime.now(UTC).isoformat()
                    ts["last_slug"] = m["slug"]
                    ts["dispatches"] = ts.get("dispatches", 0) + 1
                    self.state["stats"]["total_dispatches"] += 1

                    f = executor.submit(self._dispatch_one, m)
                    futures[f] = m

                save_state(self.state)

                # Collect results
                for future in as_completed(futures):
                    m = futures[future]
                    try:
                        result = future.result()
                    except Exception as e:
                        log.error(f"  [{m['track']}] Exception: {e}")
                        result = {
                            "success": False, "returncode": -3,
                            "duration_s": 0, "quota_hit": False,
                            "passed_after": False,
                            "track": m["track"], "num": m["num"], "slug": m["slug"],
                        }

                    track = result["track"]
                    ts = get_track_state(self.state, track)

                    # Record history
                    self.state["history"].append({
                        "track": track,
                        "num": result["num"],
                        "slug": result["slug"],
                        "timestamp": datetime.now(UTC).isoformat(),
                        "success": result["success"],
                        "passed_after": result.get("passed_after", False),
                        "duration_s": result["duration_s"],
                        "quota_hit": result.get("quota_hit", False),
                    })
                    # Keep last 500
                    if len(self.state["history"]) > 500:
                        self.state["history"] = self.state["history"][-500:]

                    if result.get("passed_after"):
                        log.info(f"  [{track}] {result['slug']}: PASSED ({result['duration_s']}s)")
                        ts["consecutive_failures"] = 0
                        ts["state"] = TrackState.ELIGIBLE
                        self.state["stats"]["total_modules_passed"] += 1
                    elif result.get("quota_hit"):
                        log.warning(f"  [{track}] {result['slug']}: QUOTA HIT ({result['duration_s']}s)")
                        cooldown_until = datetime.fromtimestamp(
                            time.time() + COOLDOWN_SECONDS, tz=UTC
                        ).isoformat()
                        ts["state"] = TrackState.COOLDOWN
                        ts["cooldown_until"] = cooldown_until
                        self.state["stats"]["total_quota_hits"] += 1
                    elif result["success"]:
                        # Process completed but module didn't pass audit
                        log.warning(f"  [{track}] {result['slug']}: completed but NOT passing ({result['duration_s']}s)")
                        ts["consecutive_failures"] = ts.get("consecutive_failures", 0) + 1
                        ts["state"] = TrackState.ELIGIBLE
                    else:
                        log.error(f"  [{track}] {result['slug']}: FAILED rc={result['returncode']} ({result['duration_s']}s)")
                        ts["consecutive_failures"] = ts.get("consecutive_failures", 0) + 1
                        ts["state"] = TrackState.ELIGIBLE

            save_state(self.state)

            if self.one_shot:
                log.info("One-shot mode: exiting.")
                break

            log.info(f"Pausing {INTER_DISPATCH_PAUSE}s...")
            time.sleep(INTER_DISPATCH_PAUSE)

        # Clean exit: clear running_tracks (#603)
        with self._running_lock:
            self._running_tracks.clear()
            self.state["running_tracks"] = []
        # Final summary
        self._print_summary()
        save_state(self.state)
        self._release_daemon_lock()

    def _print_summary(self):
        stats = self.state.get("stats", {})
        elapsed_h = (time.monotonic() - self.start_time) / 3600
        log.info("\n" + "=" * 60)
        log.info("  Batch Otaman Summary")
        log.info("=" * 60)
        log.info(f"  Runtime: {elapsed_h:.1f}h")
        log.info(f"  Dispatches: {stats.get('total_dispatches', 0)}")
        log.info(f"  Modules passed: {stats.get('total_modules_passed', 0)}")
        log.info(f"  Quota hits: {stats.get('total_quota_hits', 0)}")

        # Recent history
        history = self.state.get("history", [])
        if history:
            recent = history[-10:]
            log.info(f"\n  Recent ({len(recent)}):")
            for h in recent:
                status = "PASS" if h.get("passed_after") else "QUOTA" if h.get("quota_hit") else "FAIL"
                log.info(f"    {h['timestamp'][:19]}  {h['track']:<12} #{h['num']:>3}  {status}  {h['duration_s']}s")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_scan(args):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    bf = BatchOtaman(
        dry_run=True,
        include_tracks=args.include_tracks,
        exclude_tracks=args.exclude_tracks or [],
    )
    summaries = bf._scan_all()
    print(bf._format_table(summaries))

    modules = bf._pick_modules(summaries)
    if modules:
        print(f"\nNext dispatch ({len(modules)}):")
        for m in modules:
            print(f"  /otaman {m['track']} {m['num']} ({m['slug']}) [{m['reason']}]")
    else:
        print("\nNo eligible modules.")


def cmd_status(args):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if not STATE_FILE.exists():
        print("No state file. Run 'scan' or 'run' first.")
        return

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    stats = state.get("stats", {})

    print("=" * 60)
    print("  Batch Otaman — State")
    print("=" * 60)
    print(f"  Started: {state.get('started', '?')}")
    print(f"  Updated: {state.get('last_updated', '?')}")
    print(f"  Dispatches: {stats.get('total_dispatches', 0)}")
    print(f"  Passed: {stats.get('total_modules_passed', 0)}")
    print(f"  Quota hits: {stats.get('total_quota_hits', 0)}")

    tracks = state.get("tracks", {})
    if tracks:
        print(f"\n{'Track':<16}  {'State':<10}  {'Dispatches':>10}  {'Fails':>6}  {'Last Slug'}")
        print("-" * 70)
        for _, name, _, _, _ in TRACKS:
            if name not in tracks:
                continue
            t = tracks[name]
            print(
                f"{name:<16}  {t['state']:<10}  {t.get('dispatches', 0):>10}  "
                f"{t.get('consecutive_failures', 0):>6}  {t.get('last_slug', '-')}"
            )

    history = state.get("history", [])
    if history:
        recent = history[-5:]
        print(f"\nRecent ({len(recent)}):")
        for h in recent:
            status = "PASS" if h.get("passed_after") else "QUOTA" if h.get("quota_hit") else "FAIL"
            print(f"  {h['timestamp'][:19]}  {h['track']:<12} #{h['num']:>3}  {status}  {h['duration_s']}s")


def cmd_run(args):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    bf = BatchOtaman(
        one_shot=args.one_shot,
        dry_run=args.dry_run,
        include_tracks=args.include_tracks,
        exclude_tracks=args.exclude_tracks or [],
        max_runtime_hours=args.max_runtime_hours,
        workers=getattr(args, 'workers', MAX_WORKERS),
    )
    bf.run()


def cmd_dispatch_one(args):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    bf = BatchOtaman(
        one_shot=True,
        force_track=args.track,
        dry_run=args.dry_run,
    )
    bf.run()


def main():
    parser = argparse.ArgumentParser(
        description="Batch Otaman Dispatcher — Autonomous Gemini Otaman scheduler",
    )
    subs = parser.add_subparsers(dest="command", required=True)

    p_scan = subs.add_parser("scan", help="Show priorities (no dispatch)")
    p_scan.add_argument("--include-tracks", nargs="+", metavar="T")
    p_scan.add_argument("--exclude-tracks", nargs="+", metavar="T")

    subs.add_parser("status", help="Show current state")

    p_run = subs.add_parser("run", help="Run dispatcher")
    p_run.add_argument("--one-shot", action="store_true")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.add_argument("--include-tracks", nargs="+", metavar="T")
    p_run.add_argument("--exclude-tracks", nargs="+", metavar="T")
    p_run.add_argument("--max-runtime-hours", type=float, metavar="H")
    p_run.add_argument("--workers", type=int, default=MAX_WORKERS, help="Max parallel sessions (default 2)")

    p_one = subs.add_parser("dispatch-one", help="Force one track")
    p_one.add_argument("--track", required=True)
    p_one.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    {"scan": cmd_scan, "status": cmd_status, "run": cmd_run, "dispatch-one": cmd_dispatch_one}[args.command](args)


if __name__ == "__main__":
    main()
