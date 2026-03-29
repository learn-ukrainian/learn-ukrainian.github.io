#!/usr/bin/env python3
"""Generate curriculum-stats.json from curriculum.yaml for the Starlight site.

Run this whenever curriculum.yaml changes to keep module counts in sync.
Output: starlight/src/data/curriculum-stats.json

Usage:
    .venv/bin/python scripts/generate_curriculum_stats.py
"""

import json
import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent
CURRICULUM = ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
OUTPUT = ROOT / "starlight" / "src" / "data" / "curriculum-stats.json"


def main():
    with open(CURRICULUM) as f:
        data = yaml.safe_load(f)

    stats = {}
    total = 0
    for level_id, level_data in data["levels"].items():
        count = len(level_data.get("modules", []))
        stats[level_id] = {"modules": count}
        total += count

    stats["_total"] = total

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"Generated {OUTPUT} — {len(stats) - 1} levels, {total} total modules")


if __name__ == "__main__":
    main()
