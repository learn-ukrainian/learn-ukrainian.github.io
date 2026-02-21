#!/usr/bin/env python3
"""Batch-reset Phase D for modules whose review scored below threshold.

Usage:
    .venv/bin/python scripts/reset_phase_d_batch.py              # dry-run (default)
    .venv/bin/python scripts/reset_phase_d_batch.py --apply       # actually reset
    .venv/bin/python scripts/reset_phase_d_batch.py --threshold 8.5  # custom threshold
"""

import argparse
import glob
import json
import os
import re
import sys

BASE = "curriculum/l2-uk-en"


def find_modules_to_reset(threshold: float) -> list[dict]:
    """Find modules with completed Phase D but review score < threshold."""
    results = []

    review_files = glob.glob(f"{BASE}/*/review/*-review.md")

    for rf in review_files:
        if "-final-review.md" in rf:
            continue

        parts = rf.split("/")
        track = parts[2]
        slug = parts[-1].replace("-review.md", "")

        with open(rf, "r") as f:
            content = f.read()

        match = re.search(r"\*\*Overall Score:\*\*\s*([\d.]+)/10", content)
        if not match:
            continue
        score = float(match.group(1))

        if score >= threshold:
            continue

        state_path = f"{BASE}/{track}/orchestration/{slug}/state-v3.json"
        if not os.path.exists(state_path):
            continue

        with open(state_path, "r") as f:
            state = json.load(f)

        d_phase = state.get("phases", {}).get("v3-D", {})
        if d_phase.get("status") != "complete":
            continue

        results.append({
            "track": track,
            "slug": slug,
            "score": score,
            "state_path": state_path,
        })

    results.sort(key=lambda x: x["score"])
    return results


def reset_phase_d(state_path: str) -> None:
    """Reset v3-D phase to pending in state-v3.json."""
    with open(state_path, "r") as f:
        state = json.load(f)

    state["phases"]["v3-D"] = {
        "status": "pending",
        "ts": "",
        "attempts": 0,
        "note": "reset-review-score-below-threshold"
    }

    with open(state_path, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Batch-reset Phase D for low-scoring modules")
    parser.add_argument("--apply", action="store_true", help="Actually reset (default: dry-run)")
    parser.add_argument("--threshold", type=float, default=9.0, help="Score threshold (default: 9.0)")
    args = parser.parse_args()

    modules = find_modules_to_reset(args.threshold)

    if not modules:
        print(f"No modules found with completed Phase D and score < {args.threshold}")
        return

    fmt = "{:<12} {:<45} {:<7}"
    print(fmt.format("TRACK", "SLUG", "SCORE"))
    print("-" * 65)
    for m in modules:
        print(fmt.format(m["track"], m["slug"], f"{m['score']:.1f}"))

    print(f"\nTotal: {len(modules)} modules")

    if not args.apply:
        print("\nDRY RUN — no changes made. Use --apply to reset.")
        return

    for m in modules:
        reset_phase_d(m["state_path"])
        print(f"  RESET: {m['track']}/{m['slug']}")

    print(f"\nDone. Reset {len(modules)} modules to Phase D pending.")
    print("Re-run with (no --force-phase — pipeline continues through E/MDX):")
    # Group by track for batch commands
    tracks = sorted(set(m["track"] for m in modules))
    for t in tracks:
        print(f"  .venv/bin/python scripts/build_module_v3.py {t} --all")


if __name__ == "__main__":
    main()
