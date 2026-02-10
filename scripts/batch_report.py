#!/usr/bin/env python3
"""
Report module processing status to batch_state for the monitor.

Usage (from any workflow - full-rebuild, manual, etc.):
    .venv/bin/python scripts/batch_report.py <track> <slug> running
    .venv/bin/python scripts/batch_report.py <track> <slug> pass [--duration 120]
    .venv/bin/python scripts/batch_report.py <track> <slug> fail [--duration 120]

This updates batch_state/state_{track}.json so the playground monitor can track it.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "batch_state"


def update_state(track: str, slug: str, status: str, duration: float | None = None, mode: str = "manual"):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / f"state_{track}.json"

    # Load existing state or create new
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state = {}
    else:
        state = {}

    if "batch" not in state:
        state["batch"] = track
        state["range"] = "manual"
        state["started"] = datetime.now(timezone.utc).isoformat()

    if "modules" not in state:
        state["modules"] = {}

    now = datetime.now(timezone.utc).isoformat()

    if status == "running":
        state["modules"][slug] = {
            "status": "running",
            "mode": mode,
            "start_time": now,
        }
    elif status in ("pass", "fail"):
        existing = state.get("modules", {}).get(slug, {})
        entry = {
            "status": status,
            "mode": mode,
            "start_time": existing.get("start_time", now),
            "end_time": now,
        }
        if duration is not None:
            entry["duration"] = duration
        elif "start_time" in existing:
            try:
                start = datetime.fromisoformat(existing["start_time"])
                end = datetime.fromisoformat(now)
                entry["duration"] = (end - start).total_seconds()
            except (ValueError, TypeError):
                pass
        state["modules"][slug] = entry

    # Update current_module count
    state["current_module"] = len(state.get("modules", {}))

    # Atomic write
    tmp = state_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.rename(state_file)

    print(f"[batch_report] {track}/{slug} → {status}")


def main():
    parser = argparse.ArgumentParser(description="Report module status to batch monitor")
    parser.add_argument("track", help="Track name (e.g. c1-bio, b2-hist)")
    parser.add_argument("slug", help="Module slug (e.g. knyahynia-olha)")
    parser.add_argument("status", choices=["running", "pass", "fail"], help="Module status")
    parser.add_argument("--duration", type=float, help="Duration in seconds")
    parser.add_argument("--mode", default="manual", help="Processing mode (manual, fix, build)")
    args = parser.parse_args()

    update_state(args.track, args.slug, args.status, args.duration, args.mode)


if __name__ == "__main__":
    main()
