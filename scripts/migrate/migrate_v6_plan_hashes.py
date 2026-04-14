#!/usr/bin/env python3
"""Backfill v6 state plan hashes and flag stale downstream phases.

Usage:
    .venv/bin/python scripts/migrate/migrate_v6_plan_hashes.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
import sys

sys.path.insert(0, str(SCRIPTS_DIR))

from build.plan_tracking import (
    PLAN_HASH_PHASES,
    current_plan_hash_for,
    detect_plan_timestamp_drift,
    ordered_phases_from,
    plan_mtime_for,
)

CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
PHASE_ORDER = [
    "check", "research", "skeleton", "pre-verify", "write",
    "exercises", "activities", "repair", "verify-exercises", "annotate",
    "vocab", "enrich", "verify", "review", "stress", "publish", "audit",
]
_PHASE_SATISFIED_STATUSES = {"complete", "skipped"}


def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.stem}-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def _mark_stale(phases: dict, names: tuple[str, ...], *, reason: str, current_plan_hash: str) -> int:
    touched = 0
    stale_detected_at = datetime.now(tz=UTC).isoformat()
    for name in names:
        info = phases.get(name)
        if not isinstance(info, dict):
            continue
        previous_status = info.get("status", "pending")
        if previous_status == "stale" and info.get("stale_reason") == reason:
            continue
        phases[name] = {
            **info,
            "previous_status": previous_status,
            "status": "stale",
            "stale_reason": reason,
            "stale_detected_at": stale_detected_at,
            "current_plan_hash": current_plan_hash,
            "plan_hash": info.get("plan_hash", current_plan_hash),
        }
        touched += 1
    return touched


def migrate_state_file(state_path: Path, *, apply: bool) -> dict | None:
    try:
        state = json.loads(state_path.read_text("utf-8"))
    except Exception:
        return None

    if not isinstance(state, dict) or state.get("mode") != "v6":
        return None

    track = str(state.get("track") or state_path.parts[-4])
    slug = str(state.get("slug") or state_path.parent.name)
    phases = state.get("phases")
    if not isinstance(phases, dict):
        return None

    plan_hash = current_plan_hash_for(CURRICULUM_ROOT, track, slug)
    if not plan_hash:
        return {
            "track": track,
            "scanned": 1,
            "updated": 0,
            "backfilled_phases": 0,
            "stale_modules": 0,
            "stale_phases": 0,
            "missing_plan": 1,
        }

    updated = False
    backfilled_phases = 0
    for phase in PLAN_HASH_PHASES:
        info = phases.get(phase)
        if not isinstance(info, dict):
            continue
        if info.get("status") not in _PHASE_SATISFIED_STATUSES:
            continue
        if info.get("plan_hash"):
            continue
        info["plan_hash"] = plan_hash
        backfilled_phases += 1
        updated = True

    stale_start = detect_plan_timestamp_drift(state, plan_mtime_for(CURRICULUM_ROOT, track, slug))
    stale_phases = 0
    stale_modules = 0
    if stale_start:
        stale_names = ordered_phases_from(PHASE_ORDER, stale_start, phases)
        stale_phases = _mark_stale(
            phases,
            stale_names,
            reason=f"plan modified after {stale_start} ran",
            current_plan_hash=plan_hash,
        )
        if stale_phases:
            stale_modules = 1
            updated = True

    if updated and apply:
        state["phases"] = phases
        _write_json_atomic(state_path, state)

    return {
        "track": track,
        "scanned": 1,
        "updated": int(updated),
        "backfilled_phases": backfilled_phases,
        "stale_modules": stale_modules,
        "stale_phases": stale_phases,
        "missing_plan": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill v6 plan hashes and flag stale phases")
    parser.add_argument("--apply", action="store_true", help="Write changes to state.json files")
    args = parser.parse_args()

    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for state_path in sorted(CURRICULUM_ROOT.glob("*/orchestration/*/state.json")):
        result = migrate_state_file(state_path, apply=args.apply)
        if not result:
            continue
        track = result.pop("track")
        for key, value in result.items():
            counts[track][key] += value

    action = "APPLY" if args.apply else "DRY RUN"
    print(f"\nV6 plan-hash migration — {action}\n")
    for track in sorted(counts):
        row = counts[track]
        print(
            f"{track}: scanned={row['scanned']} updated={row['updated']} "
            f"backfilled_phases={row['backfilled_phases']} stale_modules={row['stale_modules']} "
            f"stale_phases={row['stale_phases']} missing_plan={row['missing_plan']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
