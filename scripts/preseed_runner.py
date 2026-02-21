#!/usr/bin/env python3
"""
Controllable research preseed runner.

Runs build_module_v3.py --research-only for queued tracks, one module at a time
per engine (Gemini/Claude). Clean signal handling — Ctrl+C stops after current module.

Usage:
    # Wave 1: almost-done tracks, 1 Gemini + 1 Claude
    .venv/bin/python scripts/preseed_runner.py wave1

    # Wave 2: lit tracks, 3 Gemini + 3 Claude (overnight)
    .venv/bin/python scripts/preseed_runner.py wave2

    # Custom: specific tracks
    .venv/bin/python scripts/preseed_runner.py --gemini oes ruth --claude c2 c1-pro

    # Control parallelism
    .venv/bin/python scripts/preseed_runner.py wave2 --gemini-slots 3 --claude-slots 3

    # Dry run
    .venv/bin/python scripts/preseed_runner.py wave1 --dry-run

    # Status check (no run)
    .venv/bin/python scripts/preseed_runner.py status
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURRICULUM = PROJECT_ROOT / "curriculum" / "l2-uk-en"
PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
BUILDER = str(PROJECT_ROOT / "scripts" / "build_module_v3.py")
LOG_DIR = PROJECT_ROOT / "logs" / "preseed"

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
    done = 0
    remaining = []

    # Use curriculum.yaml index for proper numbering
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from batch_gemini_config import get_module_index
        idx = get_module_index(track)

        for num in sorted(idx["num_to_slug"].keys()):
            slug = idx["num_to_slug"][num]
            if slug in research_files:
                done += 1
            else:
                remaining.append((num, slug))
    except Exception as e:
        # Fallback: just count
        done = len(research_files)
        remaining = [(i, f.stem) for i, f in enumerate(plan_files, 1)
                     if f.stem not in research_files]

    return {
        "track": track,
        "total": total,
        "done": done,
        "remaining_count": len(remaining),
        "remaining": remaining,  # [(num, slug), ...]
    }


def scan_all_tracks() -> dict:
    """Scan all tracks with remaining research."""
    all_tracks = []
    plans_root = CURRICULUM / "plans"
    if plans_root.is_dir():
        all_tracks = sorted([d.name for d in plans_root.iterdir() if d.is_dir()])

    results = {}
    for t in all_tracks:
        info = scan_track(t)
        if info["remaining_count"] > 0:
            results[t] = info
    return results


# ── Runner ───────────────────────────────────────────────────────────────

def run_track(track: str, engine: str, log_file: Path, use_claude_flag: bool = False,
              dry_run: bool = False) -> dict:
    """Run research for one track, one module at a time. Returns stats."""
    info = scan_track(track)
    remaining = info["remaining"]

    if not remaining:
        print(f"  [{engine}] {track}: nothing to do (0 remaining)", flush=True)
        return {"track": track, "passed": 0, "failed": 0, "skipped": 0}

    total = len(remaining)
    passed = 0
    failed = 0

    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "a", encoding="utf-8") as lf:
        lf.write(f"=== {track} via {engine} — {datetime.now().isoformat()} ===\n")
        lf.write(f"Remaining: {total} modules\n\n")

        for i, (num, slug) in enumerate(remaining, 1):
            if _stop_requested:
                lf.write(f"\n[STOPPED] Ctrl+C after {i-1}/{total}\n")
                print(f"  [{engine}] {track}: stopped after {i-1}/{total}", flush=True)
                break

            ts = datetime.now().strftime("%H:%M:%S")
            print(f"  [{engine}] {track} [{i}/{total}] #{num} {slug} ({ts})", flush=True)
            lf.write(f"[{i}/{total}] #{num} {slug}\n")
            lf.flush()

            if dry_run:
                lf.write(f"  DRY-RUN: would build\n")
                passed += 1
                continue

            cmd = [PYTHON, BUILDER, track, str(num), "--research-only"]
            if use_claude_flag:
                cmd.extend(["--use-claude", "A"])

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

                stdout, _ = proc.communicate(timeout=600)  # 10 min max per module

                with _lock:
                    if proc in _active_procs:
                        _active_procs.remove(proc)

                rc = proc.returncode
                lf.write(f"  rc={rc}\n")
                if stdout:
                    # Write last 10 lines to log (not everything)
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


def run_queue(tracks: list[str], engine: str, use_claude: bool = False,
              dry_run: bool = False) -> list[dict]:
    """Run a queue of tracks sequentially on one engine."""
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    results = []

    for track in tracks:
        if _stop_requested:
            break
        log_file = LOG_DIR / f"{track}-{engine}-{ts}.log"
        print(f"\n[{engine}] Starting {track}...", flush=True)
        result = run_track(track, engine, log_file, use_claude_flag=use_claude, dry_run=dry_run)
        results.append(result)
        print(f"  [{engine}] {track}: passed={result['passed']} failed={result['failed']}", flush=True)

    return results


def run_parallel_queues(gemini_tracks: list[str], claude_tracks: list[str],
                        gemini_slots: int = 1, claude_slots: int = 1,
                        dry_run: bool = False):
    """Run Gemini and Claude queues in parallel threads."""
    # Split tracks across slots
    def split_tracks(tracks, n_slots):
        """Distribute tracks round-robin across slots."""
        slots = [[] for _ in range(n_slots)]
        for i, t in enumerate(tracks):
            slots[i % n_slots].append(t)
        return [s for s in slots if s]  # remove empty

    gemini_queues = split_tracks(gemini_tracks, gemini_slots)
    claude_queues = split_tracks(claude_tracks, claude_slots)

    threads = []
    all_results = []
    results_lock = threading.Lock()

    def _worker(tracks, engine, use_claude):
        results = run_queue(tracks, engine, use_claude=use_claude, dry_run=dry_run)
        with results_lock:
            all_results.extend(results)

    # Start Gemini threads
    for i, q in enumerate(gemini_queues):
        name = f"gemini-{i+1}" if len(gemini_queues) > 1 else "gemini"
        t = threading.Thread(target=_worker, args=(q, name, False), name=name)
        threads.append(t)

    # Start Claude threads
    for i, q in enumerate(claude_queues):
        name = f"claude-{i+1}" if len(claude_queues) > 1 else "claude"
        t = threading.Thread(target=_worker, args=(q, name, True), name=name)
        threads.append(t)

    print(f"\nStarting {len(threads)} worker(s): "
          f"{len(gemini_queues)} Gemini + {len(claude_queues)} Claude", flush=True)
    print(f"Press Ctrl+C to stop after current module(s)\n", flush=True)

    t0 = time.time()
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    elapsed = time.time() - t0
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    # Summary
    print(f"\n{'='*60}", flush=True)
    print(f"PRESEED COMPLETE — {mins}m {secs}s", flush=True)
    total_passed = sum(r["passed"] for r in all_results)
    total_failed = sum(r["failed"] for r in all_results)
    print(f"  Passed: {total_passed}  Failed: {total_failed}", flush=True)
    if _stop_requested:
        print(f"  (Stopped early by user)", flush=True)
    for r in sorted(all_results, key=lambda x: x["track"]):
        status = "OK" if r["failed"] == 0 else "ISSUES"
        print(f"  {r['track']:20s}  passed={r['passed']:3d}  failed={r['failed']:3d}  [{status}]", flush=True)
    print(f"{'='*60}", flush=True)


# ── Wave definitions ─────────────────────────────────────────────────────

WAVE1 = {
    "gemini": ["oes", "ruth", "b2"],
    "claude": ["c2", "c1-pro"],
    "gemini_slots": 1,
    "claude_slots": 1,
}

WAVE2 = {
    "gemini": ["lit", "lit-essay", "lit-juvenile"],
    "claude": ["lit-fantastika", "lit-war", "lit-humor", "lit-hist-fic"],
    "gemini_slots": 3,
    "claude_slots": 3,
}


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Controllable research preseed runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s wave1                     # Almost-done tracks (1G + 1C)
  %(prog)s wave2                     # Lit tracks overnight (3G + 3C)
  %(prog)s --gemini oes --claude c2  # Custom tracks
  %(prog)s status                    # Show remaining research counts
  %(prog)s wave1 --dry-run           # Preview without running
        """
    )
    parser.add_argument("wave", nargs="?", choices=["wave1", "wave2", "status"],
                        help="Predefined wave or 'status' to check counts")
    parser.add_argument("--gemini", nargs="*", default=[],
                        help="Tracks for Gemini engine")
    parser.add_argument("--claude", nargs="*", default=[],
                        help="Tracks for Claude engine (--use-claude A)")
    parser.add_argument("--gemini-slots", type=int, default=1,
                        help="Parallel Gemini workers (default: 1)")
    parser.add_argument("--claude-slots", type=int, default=1,
                        help="Parallel Claude workers (default: 1)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would run without actually building")

    args = parser.parse_args()

    # Status mode
    if args.wave == "status" or (not args.wave and not args.gemini and not args.claude):
        remaining = scan_all_tracks()
        if not remaining:
            print("All tracks have complete research!")
            return

        print(f"\n{'Track':20s} {'Done':>6s} {'Total':>6s} {'Left':>6s} {'%':>5s}")
        print("-" * 50)
        total_done = 0
        total_all = 0
        for track, info in sorted(remaining.items()):
            pct = info['done'] / info['total'] * 100 if info['total'] else 0
            print(f"{track:20s} {info['done']:6d} {info['total']:6d} {info['remaining_count']:6d} {pct:5.1f}%")
            total_done += info['done']
            total_all += info['total']
        print("-" * 50)
        total_left = total_all - total_done
        pct = total_done / total_all * 100 if total_all else 0
        print(f"{'TOTAL':20s} {total_done:6d} {total_all:6d} {total_left:6d} {pct:5.1f}%")
        return

    # Resolve tracks
    if args.wave == "wave1":
        wave = WAVE1
        gemini_tracks = wave["gemini"]
        claude_tracks = wave["claude"]
        gemini_slots = wave["gemini_slots"]
        claude_slots = wave["claude_slots"]
    elif args.wave == "wave2":
        wave = WAVE2
        gemini_tracks = wave["gemini"]
        claude_tracks = wave["claude"]
        gemini_slots = wave["gemini_slots"]
        claude_slots = wave["claude_slots"]
    else:
        gemini_tracks = args.gemini
        claude_tracks = args.claude
        gemini_slots = args.gemini_slots
        claude_slots = args.claude_slots

    if not gemini_tracks and not claude_tracks:
        parser.print_help()
        return

    # Show plan
    print(f"\n{'='*60}", flush=True)
    print(f"PRESEED RESEARCH RUNNER", flush=True)
    print(f"{'='*60}", flush=True)

    for engine, tracks in [("Gemini", gemini_tracks), ("Claude", claude_tracks)]:
        if tracks:
            slots = gemini_slots if engine == "Gemini" else claude_slots
            for t in tracks:
                info = scan_track(t)
                print(f"  [{engine}] {t}: {info['remaining_count']} remaining / {info['total']} total", flush=True)
            print(f"  [{engine}] slots: {slots}", flush=True)

    if args.dry_run:
        print(f"\n  DRY RUN — no builds will execute\n", flush=True)

    print(f"\nLogs: {LOG_DIR}/", flush=True)
    print(f"{'='*60}\n", flush=True)

    run_parallel_queues(
        gemini_tracks=gemini_tracks,
        claude_tracks=claude_tracks,
        gemini_slots=gemini_slots,
        claude_slots=claude_slots,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
