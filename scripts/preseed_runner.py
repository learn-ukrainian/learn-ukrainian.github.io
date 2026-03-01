#!/usr/bin/env python3
"""
Controllable research preseed runner v2.

Runs build_module.py --research-only for queued tracks, one module at a time
per slot. Clean signal handling — Ctrl+C stops after current module.

Usage:
    # All remaining tracks via Gemini (2 parallel slots)
    .venv/bin/python scripts/preseed_runner.py wave2 all

    # Specific tracks
    .venv/bin/python scripts/preseed_runner.py wave2 lit lit-essay lit-war

    # Control parallelism and model
    .venv/bin/python scripts/preseed_runner.py wave2 all --slots 3 --model gemini-3.1-pro-preview

    # Dry run
    .venv/bin/python scripts/preseed_runner.py wave2 all --dry-run

    # Status check (no run)
    .venv/bin/python scripts/preseed_runner.py status
"""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURRICULUM = PROJECT_ROOT / "curriculum" / "l2-uk-en"
PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
BUILDER = str(PROJECT_ROOT / "scripts" / "build_module.py")
LOG_DIR = PROJECT_ROOT / "logs" / "preseed"

DEFAULT_MODEL = "gemini-3.1-pro-preview"
DEFAULT_SLOTS = 2

# ── Signal handling ──────────────────────────────────────────────────────

_stop_requested = False
_active_procs: list[subprocess.Popen] = []
_lock = threading.Lock()


def _signal_handler(sig, frame):
    global _stop_requested
    if _stop_requested:
        print("\n[FORCE] Second Ctrl+C — killing active processes...", flush=True)
        with _lock:
            for p in _active_procs:
                try:
                    p.kill()
                except Exception:
                    pass
        sys.exit(1)
    _stop_requested = True
    print("\n[STOP] Ctrl+C received — finishing current module(s), then stopping.", flush=True)
    print("[STOP] Press Ctrl+C again to force-kill immediately.", flush=True)


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ── Track scanning ───────────────────────────────────────────────────────

def scan_track(track: str) -> dict:
    """Get research status for a track."""
    plans_dir = CURRICULUM / "plans" / track
    research_dir = CURRICULUM / track / "research"

    plan_files = sorted(plans_dir.glob("*.yaml")) if plans_dir.is_dir() else []
    research_files = set()
    if research_dir.is_dir():
        research_files = {f.name.removesuffix("-research.md") for f in research_dir.glob("*-research.md")}

    total = len(plan_files)
    remaining = []

    try:
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from batch_gemini_config import get_module_index
        idx = get_module_index(track)

        done = 0
        for num in sorted(idx["num_to_slug"].keys()):
            slug = idx["num_to_slug"][num]
            if slug in research_files:
                done += 1
            else:
                remaining.append((num, slug))
    except Exception:
        done = len(research_files)
        remaining = [(i, f.stem) for i, f in enumerate(plan_files, 1)
                     if f.stem not in research_files]

    return {
        "track": track,
        "total": total,
        "done": done,
        "remaining_count": len(remaining),
        "remaining": remaining,
    }


def get_all_remaining_tracks() -> list[str]:
    """Return track names that still have remaining research."""
    plans_root = CURRICULUM / "plans"
    if not plans_root.is_dir():
        return []
    tracks = []
    for d in sorted(plans_root.iterdir()):
        if not d.is_dir():
            continue
        info = scan_track(d.name)
        if info["remaining_count"] > 0:
            tracks.append(d.name)
    return tracks


# ── Runner ───────────────────────────────────────────────────────────────

def run_track(track: str, slot_name: str, log_file: Path,
              model: str = DEFAULT_MODEL, dry_run: bool = False) -> dict:
    """Run research for one track, one module at a time. Returns stats."""
    info = scan_track(track)
    remaining = info["remaining"]

    if not remaining:
        print(f"  [{slot_name}] {track}: nothing to do (0 remaining)", flush=True)
        return {"track": track, "passed": 0, "failed": 0, "skipped": 0}

    total = len(remaining)
    passed = 0
    failed = 0

    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "a", encoding="utf-8") as lf:
        lf.write(f"=== {track} via {slot_name} (model={model}) — {datetime.now().isoformat()} ===\n")
        lf.write(f"Remaining: {total} modules\n\n")

        for i, (num, slug) in enumerate(remaining, 1):
            if _stop_requested:
                lf.write(f"\n[STOPPED] Ctrl+C after {i-1}/{total}\n")
                print(f"  [{slot_name}] {track}: stopped after {i-1}/{total}", flush=True)
                break

            ts = datetime.now().strftime("%H:%M:%S")
            print(f"  [{slot_name}] {track} [{i}/{total}] #{num} {slug} ({ts})", flush=True)
            lf.write(f"[{i}/{total}] #{num} {slug}\n")
            lf.flush()

            if dry_run:
                lf.write(f"  DRY-RUN: would build\n")
                passed += 1
                continue

            cmd = [PYTHON, BUILDER, track, str(num), "--research-only",
                   "--gemini-model", model]

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(PROJECT_ROOT),
                )
                with _lock:
                    _active_procs.append(proc)

                stdout, _ = proc.communicate(timeout=600)

                with _lock:
                    if proc in _active_procs:
                        _active_procs.remove(proc)

                rc = proc.returncode
                lf.write(f"  rc={rc}\n")
                if stdout:
                    lines = stdout.strip().split("\n")
                    for line in lines[-10:]:
                        lf.write(f"  {line}\n")
                lf.flush()

                if rc == 0:
                    passed += 1
                else:
                    failed += 1
                    print(f"    FAILED (rc={rc})", flush=True)

            except subprocess.TimeoutExpired:
                with _lock:
                    if proc in _active_procs:
                        _active_procs.remove(proc)
                proc.kill()
                proc.wait()
                failed += 1
                lf.write(f"  TIMEOUT (600s)\n")
                print(f"    TIMEOUT", flush=True)
            except Exception as e:
                failed += 1
                lf.write(f"  ERROR: {e}\n")
                print(f"    ERROR: {e}", flush=True)

        lf.write(f"\n=== DONE: passed={passed} failed={failed} total={total} ===\n")

    return {"track": track, "passed": passed, "failed": failed, "skipped": total - passed - failed}


def run_parallel(tracks: list[str], slots: int = DEFAULT_SLOTS,
                 model: str = DEFAULT_MODEL, dry_run: bool = False):
    """Run tracks in parallel across N slots."""
    # Distribute tracks round-robin across slots, ordered by remaining count (largest first)
    track_infos = [(t, scan_track(t)["remaining_count"]) for t in tracks]
    track_infos.sort(key=lambda x: -x[1])  # largest first for better load balance
    sorted_tracks = [t for t, _ in track_infos]

    slot_queues: list[list[str]] = [[] for _ in range(min(slots, len(sorted_tracks)))]
    for i, t in enumerate(sorted_tracks):
        slot_queues[i % len(slot_queues)].append(t)

    threads = []
    all_results: list[dict] = []
    results_lock = threading.Lock()
    ts = datetime.now().strftime("%Y%m%d-%H%M")

    def _worker(queue: list[str], slot_name: str):
        for track in queue:
            if _stop_requested:
                break
            log_file = LOG_DIR / f"{track}-{slot_name}-{ts}.log"
            print(f"\n[{slot_name}] Starting {track}...", flush=True)
            result = run_track(track, slot_name, log_file, model=model, dry_run=dry_run)
            with results_lock:
                all_results.append(result)
            print(f"  [{slot_name}] {track}: passed={result['passed']} failed={result['failed']}", flush=True)

    for i, q in enumerate(slot_queues):
        name = f"slot-{i+1}"
        t = threading.Thread(target=_worker, args=(q, name), name=name)
        threads.append(t)

    print(f"\nStarting {len(threads)} slot(s), model={model}", flush=True)
    print(f"Press Ctrl+C to stop after current module(s)\n", flush=True)

    t0 = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    elapsed = time.time() - t0
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    print(f"\n{'='*60}", flush=True)
    print(f"PRESEED COMPLETE — {mins}m {secs}s", flush=True)
    total_passed = sum(r["passed"] for r in all_results)
    total_failed = sum(r["failed"] for r in all_results)
    print(f"  Passed: {total_passed}  Failed: {total_failed}", flush=True)
    if _stop_requested:
        print(f"  (Stopped early by user)", flush=True)
    for r in sorted(all_results, key=lambda x: x["track"]):
        status = "OK" if r["failed"] == 0 else "ISSUES"
        print(f"  {r['track']:25s}  passed={r['passed']:3d}  failed={r['failed']:3d}  [{status}]", flush=True)
    print(f"{'='*60}", flush=True)


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Research preseed runner v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s wave2 all                          # All remaining tracks, 2 Gemini slots
  %(prog)s wave2 lit lit-essay                 # Specific tracks
  %(prog)s wave2 all --slots 3                 # 3 parallel slots
  %(prog)s wave2 all --model gemini-3.1-pro-preview  # Different model
  %(prog)s status                              # Show remaining research counts
  %(prog)s wave2 all --dry-run                 # Preview without running
        """
    )
    parser.add_argument("command", choices=["wave2", "status"],
                        help="'wave2' to run research, 'status' to check counts")
    parser.add_argument("tracks", nargs="*", default=[],
                        help="Track names or 'all' for all remaining tracks")
    parser.add_argument("--slots", type=int, default=DEFAULT_SLOTS,
                        help=f"Parallel Gemini slots (default: {DEFAULT_SLOTS})")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL,
                        help=f"Gemini model (default: {DEFAULT_MODEL})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would run without actually building")

    args = parser.parse_args()

    # Status mode
    if args.command == "status":
        remaining_tracks = get_all_remaining_tracks()
        if not remaining_tracks:
            print("All tracks have complete research!")
            return

        print(f"\n{'Track':25s} {'Done':>6s} {'Total':>6s} {'Left':>6s} {'%':>5s}")
        print("-" * 55)
        total_done = 0
        total_all = 0
        for track in remaining_tracks:
            info = scan_track(track)
            pct = info['done'] / info['total'] * 100 if info['total'] else 0
            print(f"{track:25s} {info['done']:6d} {info['total']:6d} {info['remaining_count']:6d} {pct:5.1f}%")
            total_done += info['done']
            total_all += info['total']
        print("-" * 55)
        total_left = total_all - total_done
        pct = total_done / total_all * 100 if total_all else 0
        print(f"{'TOTAL':25s} {total_done:6d} {total_all:6d} {total_left:6d} {pct:5.1f}%")
        return

    # wave2 mode
    if not args.tracks:
        parser.error("Specify track names or 'all' after wave2")

    if "all" in args.tracks:
        tracks = get_all_remaining_tracks()
    else:
        tracks = args.tracks

    if not tracks:
        print("No tracks with remaining research!")
        return

    # Show plan
    print(f"\n{'='*60}", flush=True)
    print(f"PRESEED RESEARCH RUNNER v2", flush=True)
    print(f"Model: {args.model}", flush=True)
    print(f"Slots: {args.slots}", flush=True)
    print(f"{'='*60}", flush=True)

    total_remaining = 0
    for t in tracks:
        info = scan_track(t)
        print(f"  {t:25s} {info['remaining_count']:4d} remaining / {info['total']:4d} total", flush=True)
        total_remaining += info['remaining_count']

    print(f"  {'─'*45}", flush=True)
    print(f"  {'TOTAL':25s} {total_remaining:4d} modules", flush=True)

    if args.dry_run:
        print(f"\n  DRY RUN — no builds will execute\n", flush=True)

    print(f"\nLogs: {LOG_DIR}/", flush=True)
    print(f"{'='*60}\n", flush=True)

    run_parallel(
        tracks=tracks,
        slots=args.slots,
        model=args.model,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
