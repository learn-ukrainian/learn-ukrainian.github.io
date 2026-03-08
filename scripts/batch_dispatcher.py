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
    .venv/bin/python scripts/batch_dispatcher.py dispatch-one --track bio

    # Filter tracks
    --include-tracks hist bio lit
    --exclude-tracks a1 b1 b2

    # Safety timeout
    --max-runtime-hours 12
"""

import argparse
import json
import logging
import os
import signal
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# Ensure scripts/ is on sys.path for sibling imports
sys.path.insert(0, str(Path(__file__).parent))

from batch_dispatcher_config import (
    COOLDOWN_SECONDS,
    DISPATCHER_STATE_FILE,
    INTER_DISPATCH_PAUSE,
    MAX_STALL_COUNT,
    TRACKS,
    TrackState,
)
from batch_dispatcher_helpers import (
    BATCH_STATE_DIR,
    FAILURES_DIR,
    check_dependencies,
    compute_priority_score,
    detect_progress,
    dispatch_claude_fix,
    dispatch_track,
    get_track_dstate,
    load_dispatcher_state,
    save_dispatcher_state,
    scan_track,
    select_strategy,
)
from batch_gemini_config import PROJECT_ROOT, SEMINAR_TRACKS

log = logging.getLogger("dispatcher")

# Graceful shutdown flag
_shutdown_requested = False


def _signal_handler(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True
    log.warning(f"Shutdown requested (signal {signum}). Finishing current dispatch...")



# ---------------------------------------------------------------------------
# Main dispatcher loop
# ---------------------------------------------------------------------------

class BatchDispatcher:
    """Autonomous scheduler that processes tracks in priority order."""

    def __init__(self, *, one_shot=False, dry_run=False,
                 include_tracks=None, exclude_tracks=None,
                 max_runtime_hours=None, force_track=None,
                 trust_cache=False):
        self.one_shot = one_shot
        self.dry_run = dry_run
        self.include_tracks = set(include_tracks) if include_tracks else None
        self.exclude_tracks = set(exclude_tracks) if exclude_tracks else set()
        self.max_runtime_hours = max_runtime_hours
        self.force_track = force_track
        self.trust_cache = trust_cache
        self.start_time = time.monotonic()

        self.state_file = PROJECT_ROOT / DISPATCHER_STATE_FILE
        self.state = load_dispatcher_state(self.state_file)

    def _should_include_track(self, track_name: str) -> bool:
        """Check if track passes include/exclude filters."""
        if track_name in self.exclude_tracks:
            return False
        return not (self.include_tracks is not None and track_name not in self.include_tracks)

    def _runtime_exceeded(self) -> bool:
        """Check if max runtime has been exceeded."""
        if self.max_runtime_hours is None:
            return False
        elapsed_hours = (time.monotonic() - self.start_time) / 3600
        return elapsed_hours >= self.max_runtime_hours

    def _scan_all_tracks(self) -> dict[str, dict]:
        """Scan all tracks and return their status."""
        scans = {}
        for _priority, track_name, _expected, _ttype, _deps in TRACKS:
            if not self._should_include_track(track_name):
                continue
            scans[track_name] = scan_track(track_name, trust_cache=self.trust_cache)
        return scans

    def _update_track_states(self, track_scans: dict[str, dict]):
        """Update state machine for all tracks based on current scans."""
        datetime.now(UTC).isoformat()

        for _priority, track_name, _expected, _ttype, _deps in TRACKS:
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
            # Use passed + stale for completion (stale PASS still counts — #561)
            if dstate["state"] == TrackState.DONE:
                effective = scan["passed"] + scan.get("stale", 0)
                if effective < scan["total"]:
                    # Regression — something changed
                    dstate["state"] = TrackState.PENDING
                    log.info(f"  {track_name}: Regression detected, re-evaluating")
                elif scan.get("stale", 0) > 0:
                    log.debug(f"  {track_name}: DONE but {scan['stale']} stale (re-audit recommended)")
                continue

            # RUNNING tracks: verify they're actually running (lock file + live PID)
            if dstate["state"] == TrackState.RUNNING:
                lock_file = BATCH_STATE_DIR / "locks" / f"batch_{track_name}.lock"
                if lock_file.exists():
                    # Lock exists — but is the PID actually alive?
                    try:
                        lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
                        pid = lock_data.get("pid", 0)
                        os.kill(pid, 0)  # Signal 0 = check if process exists
                        continue  # PID alive — actually running
                    except (ProcessLookupError, PermissionError):
                        # PID is dead — stale lock from crashed process
                        lock_file.unlink(missing_ok=True)
                        log.info(f"  {track_name}: Stale lock (PID {pid} dead), cleaned up")
                    except (json.JSONDecodeError, OSError, KeyError):
                        # Corrupt lock file — remove it
                        lock_file.unlink(missing_ok=True)
                        log.info(f"  {track_name}: Corrupt lock file, cleaned up")
                # Orphaned RUNNING state — process was killed or crashed
                log.info(f"  {track_name}: Orphaned RUNNING, resetting to PENDING")
                dstate["state"] = TrackState.PENDING
                # Fall through to re-evaluate

            # Check for DONE (passed + stale counts — #561)
            effective = scan["passed"] + scan.get("stale", 0)
            if effective >= scan["total"] and scan["total"] > 0:
                dstate["state"] = TrackState.DONE
                continue

            # Expire COOLDOWN
            if dstate["state"] == TrackState.COOLDOWN:
                cooldown_until = dstate.get("cooldown_until")
                if cooldown_until:
                    try:
                        until = datetime.fromisoformat(cooldown_until)
                        if datetime.now(UTC) >= until:
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
        for priority, track_name, _expected, _ttype, _deps in TRACKS:
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
                scan_track(track_name)
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
        lines.append(f"{'#':>2}  {'Track':<16}  {'State':<10}  {'Pass':>5}  {'Fail':>5}  {'Stale':>5}  {'New':>5}  {'Total':>5}  {'Rate':>6}  {'Esc':>4}  {'Score':>6}")
        lines.append("-" * 98)

        for priority, track_name, _expected, _ttype, _deps in TRACKS:
            if not self._should_include_track(track_name):
                continue

            scan = track_scans.get(track_name, {})
            dstate = get_track_dstate(self.state, track_name)

            total = scan.get("total", 0)
            passed = scan.get("passed", 0)
            failed = scan.get("failed", 0)
            stale = scan.get("stale", 0)
            unbuilt = scan.get("unbuilt", 0)
            rate = f"{scan.get('pass_rate', 0):.0%}"
            state = dstate["state"]
            score = compute_priority_score(track_name, scan, track_scans, self.state)
            esc = self._count_escalated(track_name)

            lines.append(
                f"{priority:>2}  {track_name:<16}  {state:<10}  {passed:>5}  {failed:>5}  {stale:>5}  {unbuilt:>5}  {total:>5}  {rate:>6}  {esc:>4}  {score:>6.2f}"
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

            # Step 3: Show status table + one-line summary
            table = self._format_track_table(track_scans)
            done_count = sum(1 for _, n, _, _, _ in TRACKS if self._should_include_track(n) and get_track_dstate(self.state, n)["state"] == TrackState.DONE)
            total_tracks = sum(1 for _, n, _, _, _ in TRACKS if self._should_include_track(n))
            total_passed = sum(s.get("passed", 0) for s in track_scans.values())
            total_modules = sum(s.get("total", 0) for s in track_scans.values())
            log.info(f"\n{table}")
            log.info(f"\n  >>> {done_count}/{total_tracks} tracks done | {total_passed}/{total_modules} modules passing ({total_passed/total_modules*100:.0f}%)\n")

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
            dstate["last_dispatch"] = datetime.now(UTC).isoformat()
            dstate["dispatches"] = dstate.get("dispatches", 0) + 1
            self.state["stats"]["total_dispatches"] = self.state["stats"].get("total_dispatches", 0) + 1
            save_dispatcher_state(self.state, self.state_file)

            result = dispatch_track(track_name, mode, extra_args)

            # Step 7: Analyze result
            log.info(f"  Done in {result['duration_s']}s {'(QUOTA HIT)' if result['quota_hit'] else ''}")

            # Re-scan to measure progress
            scan_after = scan_track(track_name)
            progress = detect_progress(track_name, scan_before, scan_after)
            log.info(f"  {track_name}: {scan_after['passed']}/{scan_after['total']} passing ({scan_after['passed']/scan_after['total']*100:.0f}%) — {scan_after['failed']} failing, {scan_after['unbuilt']} unbuilt")

            # Record dispatch history
            dispatch_record = {
                "track": track_name,
                "mode": mode,
                "timestamp": datetime.now(UTC).isoformat(),
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

            # Step 7.5: Process escalated modules (DISABLED - Claude not available)
            # esc_fixed = self._process_escalations(track_name, track_scans)
            esc_fixed = 0
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
            effective_after = scan_after["passed"] + scan_after.get("stale", 0)
            if effective_after >= scan_after["total"] and scan_after["total"] > 0:
                dstate["state"] = TrackState.DONE
                log.info(f"  {track_name}: DONE ({scan_after['passed']}/{scan_after['total']}, {scan_after.get('stale', 0)} stale)")
            elif result["quota_hit"]:
                # Quota hit → COOLDOWN
                cooldown_until = datetime.fromtimestamp(
                    time.time() + COOLDOWN_SECONDS, tz=UTC
                ).isoformat()
                dstate["state"] = TrackState.COOLDOWN
                dstate["cooldown_until"] = cooldown_until
                self.state["stats"]["total_cooldowns"] = self.state["stats"].get("total_cooldowns", 0) + 1
                log.info(f"  {track_name}: COOLDOWN until {cooldown_until} (quota hit)")
            elif result["returncode"] == -1:
                # Subprocess timeout → COOLDOWN
                cooldown_until = datetime.fromtimestamp(
                    time.time() + COOLDOWN_SECONDS, tz=UTC
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
        trust_cache=getattr(args, 'trust_cache', False),
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
        trust_cache=getattr(args, 'trust_cache', False),
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
    p_scan.add_argument("--trust-cache", action="store_true", help="Skip freshness checks on status cache")

    # --- status ---
    subparsers.add_parser("status", help="Show current dispatcher state")

    # --- run ---
    p_run = subparsers.add_parser("run", help="Run dispatcher (continuous by default)")
    p_run.add_argument("--one-shot", action="store_true", help="Single dispatch cycle, then exit")
    p_run.add_argument("--dry-run", action="store_true", help="Show what would be dispatched without running")
    p_run.add_argument("--include-tracks", nargs="+", metavar="TRACK", help="Only include these tracks")
    p_run.add_argument("--exclude-tracks", nargs="+", metavar="TRACK", help="Exclude these tracks")
    p_run.add_argument("--max-runtime-hours", type=float, metavar="HOURS", help="Stop after N hours")
    p_run.add_argument("--trust-cache", action="store_true", help="Skip freshness checks on status cache")

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
