#!/usr/bin/env python3
"""Generate or verify site/src/data/curriculum-stats.json from curriculum.yaml.

The home course map and the track overview routes read per-level module counts
from this file. Use it whenever curriculum.yaml gains or loses a module; use
`--check` (no writes) to verify the committed file still matches the manifest.

Usage:
    .venv/bin/python scripts/generate_curriculum_stats.py
    .venv/bin/python scripts/generate_curriculum_stats.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
CURRICULUM = ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
OUTPUT = ROOT / "site" / "src" / "data" / "curriculum-stats.json"
REGENERATE_COMMAND = ".venv/bin/python scripts/generate_curriculum_stats.py"


def build_stats(data: dict) -> dict:
    """Return `{level: {"modules": n}, ..., "_total": n}` for a parsed manifest."""
    stats: dict = {}
    total = 0
    for level_id, level_data in data["levels"].items():
        count = len((level_data or {}).get("modules", []))
        stats[level_id] = {"modules": count}
        total += count

    stats["_total"] = total
    return stats


def render_stats(stats: dict) -> str:
    """Serialize stats exactly as they are committed to disk."""
    return json.dumps(stats, indent=2) + "\n"


def load_stats(curriculum_path: Path | None = None) -> dict:
    """Compute the current stats from the manifest on disk."""
    with open(curriculum_path or CURRICULUM) as f:
        return build_stats(yaml.safe_load(f))


def stats_drift(expected: dict, output_path: Path | None = None) -> list[str]:
    """Describe how the file on disk differs from `expected`; empty means fresh.

    The manifest is the only oracle: the file is compared to counts derived from
    it, never to anything stored inside the file, so a self-consistent but
    outdated file (valid `_total`, old counts) is still reported.
    """
    path = output_path or OUTPUT
    if not path.exists():
        return [f"missing: {path}"]
    try:
        actual = json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError as exc:
        return [f"unparseable: {path} ({exc})"]
    if not isinstance(actual, dict):
        return [f"unexpected shape: {path} is not a JSON object"]

    problems = []
    for key, value in expected.items():
        if key not in actual:
            problems.append(f"missing key {key!r} (expected {value!r})")
        elif actual[key] != value:
            problems.append(f"stale key {key!r}: file has {actual[key]!r}, manifest gives {value!r}")
    problems.extend(f"unexpected key {key!r}" for key in actual if key not in expected)

    if not problems and path.read_text("utf-8") != render_stats(expected):
        problems.append(f"formatting differs from generator output: {path}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate site/src/data/curriculum-stats.json (module counts per level plus _total) from curriculum.yaml.\n"
            "Use after any curriculum.yaml module addition/removal; use --check to verify without writing."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/generate_curriculum_stats.py\n"
            "  .venv/bin/python scripts/generate_curriculum_stats.py --check\n"
            "\n"
            "Outputs: writes site/src/data/curriculum-stats.json (default); --check writes nothing.\n"
            "Exit codes: 0 = written / file is current; 1 = --check found missing, stale or malformed stats.\n"
            "Related: site/src/pages/index.astro and site/src/pages/[...slug].astro read this file; "
            "scripts/generate_landing_pages.py builds the track landings; #9754."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write; exit 1 if curriculum-stats.json differs from curriculum.yaml (default: write the file).",
    )
    args = parser.parse_args(argv)

    stats = load_stats()
    if args.check:
        problems = stats_drift(stats)
        if problems:
            print(f"Curriculum stats drift detected in {OUTPUT}:")
            for problem in problems:
                print(f"  {problem}")
            print(f"Regenerate with:\n  {REGENERATE_COMMAND}")
            return 1
        print(f"OK {OUTPUT} — {len(stats) - 1} levels, {stats['_total']} total modules")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render_stats(stats), "utf-8")
    print(f"Generated {OUTPUT} — {len(stats) - 1} levels, {stats['_total']} total modules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
