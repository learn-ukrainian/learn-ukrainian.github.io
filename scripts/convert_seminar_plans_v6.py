#!/usr/bin/env python3
"""Convert seminar track plans to V6 format.

Normalizes seminar plans (HIST, BIO, ISTORIO, LIT, OES, RUTH, FOLK, etc.)
to V6-compatible format while preserving rich content (dates, quotes, tags).

Uses ruamel.yaml for round-trip preservation of formatting and comments.

Usage:
    # Convert one track:
    .venv/bin/python scripts/convert_seminar_plans_v6.py hist

    # Convert all seminar tracks:
    .venv/bin/python scripts/convert_seminar_plans_v6.py --all

    # Dry run (show changes without writing):
    .venv/bin/python scripts/convert_seminar_plans_v6.py hist --dry-run

Issue: #1020
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLANS_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# Word targets per track (from config.py)
WORD_TARGETS: dict[str, int] = {
    "hist": 5000,
    "bio": 5000,
    "istorio": 5000,
    "lit": 5000,
    "lit-essay": 5000,
    "lit-hist-fic": 5000,
    "lit-fantastika": 5000,
    "lit-war": 5000,
    "lit-humor": 5000,
    "lit-youth": 5000,
    "lit-drama": 5000,
    "folk": 5000,
    "oes": 5000,
    "ruth": 5000,
}

# Supported seminar activity types
SEMINAR_ACTIVITY_TYPES = {
    "reading", "critical-analysis", "essay-response", "source-evaluation",
    "debate", "comparative-study", "etymology-trace", "phonology-lab",
    "grammar-lab", "parallel-text", "paleography-analysis",
    # Also support core types (may appear in some seminar plans)
    "quiz", "fill-in", "match-up", "group-sort", "true-false",
}

yaml = YAML(typ="rt")
yaml.preserve_quotes = True
yaml.width = 120


def normalize_plan(file_path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """Normalize a single seminar plan to V6 format.

    Returns (was_modified, list of changes made).
    """
    changes: list[str] = []

    data = yaml.load(file_path)
    if not data:
        return False, ["SKIP: empty file"]

    # Some plans have a list at root (e.g., FOLK) — skip these
    if not isinstance(data, dict):
        return False, ["SKIP: root is not a dict (non-standard plan format)"]

    track = data.get("level", "").lower()
    if not track:
        # Try to infer from file path
        track = file_path.parent.name

    # 1. sources → references migration
    if "sources" in data and "references" not in data:
        sources = data.pop("sources")
        data["references"] = sources
        changes.append("sources → references")
    elif "sources" not in data and "references" not in data:
        data["references"] = []
        changes.append("added empty references")

    # 2. word_target normalization
    expected_target = WORD_TARGETS.get(track, 5000)
    current_target = data.get("word_target", 0)
    if current_target != expected_target:
        data["word_target"] = expected_target
        changes.append(f"word_target: {current_target} → {expected_target}")

    # 3. version bump to 3.0 (V6-compatible, distinguishes from old 2.0)
    old_version = data.get("version", "")
    if str(old_version) != "3.0":
        data["version"] = "3.0"
        changes.append(f"version: {old_version} → 3.0")

    # 4. register field
    if "register" not in data:
        data["register"] = "академічний"
        changes.append("added register: академічний")

    # 5. grammar field (empty list for seminars — no grammar scope restrictions)
    if "grammar" not in data:
        data["grammar"] = []
        changes.append("added grammar: []")

    # 6. Validate activity_hints types
    activity_hints = data.get("activity_hints", [])
    if not activity_hints:
        changes.append("WARNING: no activity_hints")
    else:
        for hint in activity_hints:
            if isinstance(hint, dict):
                hint_type = hint.get("type", "")
                if hint_type and hint_type not in SEMINAR_ACTIVITY_TYPES:
                    changes.append(f"WARNING: unknown activity type '{hint_type}'")

    # 7. Validate vocabulary_hints exists
    vocab = data.get("vocabulary_hints", {})
    if not vocab or not vocab.get("required", []):
        changes.append("WARNING: no vocabulary_hints.required")

    # 8. Validate content_outline has word budgets
    outline = data.get("content_outline", [])
    for section in outline:
        if isinstance(section, dict) and "words" not in section:
            section_name = section.get("section", "unknown")
            changes.append(f"WARNING: section '{section_name}' missing word budget")

    # Write back if modified
    if changes and not dry_run:
        # Only write if there are actual changes (not just warnings)
        real_changes = [c for c in changes if not c.startswith("WARNING")]
        if real_changes:
            yaml.dump(data, file_path)

    has_real_changes = any(not c.startswith("WARNING") for c in changes)
    return has_real_changes, changes


def process_track(track: str, dry_run: bool = False) -> dict:
    """Process all plans in a track directory."""
    track_dir = PLANS_ROOT / track
    if not track_dir.is_dir():
        print(f"❌ Track directory not found: {track_dir}")
        return {}

    plan_files = sorted(track_dir.glob("*.yaml"))
    print(f"\n{'='*60}")
    print(f"  Track: {track} ({len(plan_files)} plans)")
    print(f"{'='*60}")

    stats = {"total": 0, "modified": 0, "warnings": 0, "errors": 0}
    warnings: list[str] = []

    for plan_file in plan_files:
        stats["total"] += 1
        try:
            modified, changes = normalize_plan(plan_file, dry_run)
            if modified:
                stats["modified"] += 1

            # Log changes
            change_msgs = [c for c in changes if not c.startswith("WARNING") and not c.startswith("SKIP")]
            warning_msgs = [c for c in changes if c.startswith("WARNING")]

            if change_msgs:
                mode = "[DRY RUN] " if dry_run else ""
                print(f"  {mode}✏️  {plan_file.stem}: {', '.join(change_msgs)}")
            if warning_msgs:
                stats["warnings"] += len(warning_msgs)
                for w in warning_msgs:
                    warnings.append(f"  {plan_file.stem}: {w}")

        except Exception as e:
            stats["errors"] += 1
            print(f"  ❌ {plan_file.stem}: {e}")

    # Summary
    print(f"\n  Summary: {stats['modified']}/{stats['total']} modified, "
          f"{stats['warnings']} warnings, {stats['errors']} errors")

    if warnings:
        print("\n  Warnings:")
        for w in warnings[:20]:
            print(f"    {w}")
        if len(warnings) > 20:
            print(f"    ...and {len(warnings) - 20} more")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Convert seminar plans to V6 format")
    parser.add_argument("track", nargs="?", help="Track to convert (e.g., hist, bio, lit)")
    parser.add_argument("--all", action="store_true", help="Convert all seminar tracks")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    seminar_tracks = list(WORD_TARGETS.keys())

    if args.all:
        tracks = seminar_tracks
    elif args.track:
        if args.track not in seminar_tracks:
            print(f"Unknown track: {args.track}")
            print(f"Available: {', '.join(seminar_tracks)}")
            sys.exit(1)
        tracks = [args.track]
    else:
        parser.print_help()
        sys.exit(1)

    total_stats = {"total": 0, "modified": 0, "warnings": 0, "errors": 0}

    for track in tracks:
        stats = process_track(track, dry_run=args.dry_run)
        for key in total_stats:
            total_stats[key] += stats.get(key, 0)

    print(f"\n{'='*60}")
    print(f"  TOTAL: {total_stats['modified']}/{total_stats['total']} modified, "
          f"{total_stats['warnings']} warnings, {total_stats['errors']} errors")
    if args.dry_run:
        print("  (DRY RUN — no files were written)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
