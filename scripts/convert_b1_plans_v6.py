#!/usr/bin/env python3
"""Convert B1 plans to V6 format.

B1-specific conversions:
1. Strip extraneous fields: persona, immersion, module_type
2. Migrate sources -> references (map name -> title, drop type: reference)
3. Clean data types: cast activity_hints[].items from strings to integers
4. Add register field if missing (default: "розмовний")
5. Add grammar: [] if missing
6. Ensure version is "3.0"

Uses ruamel.yaml (YAML(typ='rt')) for round-trip preservation.

Usage:
    # Dry run (show changes without writing):
    .venv/bin/python scripts/convert_b1_plans_v6.py --dry-run

    # Convert all B1 plans:
    .venv/bin/python scripts/convert_b1_plans_v6.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLANS_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / "b1"

# B1 word target from config.py
WORD_TARGET = 4000

# Fields to strip (extraneous for V6)
EXTRANEOUS_FIELDS = {"persona", "immersion", "module_type"}

yaml = YAML(typ="rt")
yaml.preserve_quotes = True
yaml.width = 120


def cast_items_value(value: object) -> int | None:
    """Cast activity_hints items value to int.

    Handles strings like "12+", "12", and already-int values.
    Returns None if the value cannot be parsed.
    """
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        cleaned = re.sub(r"[^0-9]", "", value)
        if cleaned:
            return int(cleaned)
    return None


def migrate_sources_to_references(sources: list) -> list:
    """Migrate sources entries: name -> title, drop type: reference."""
    migrated = []
    for entry in sources:
        if not isinstance(entry, dict):
            migrated.append(entry)
            continue
        new_entry = {}
        for key, val in entry.items():
            if key == "name":
                new_entry["title"] = val
            elif key == "type" and val == "reference":
                continue  # drop type: reference
            else:
                new_entry[key] = val
        migrated.append(new_entry)
    return migrated


def normalize_plan(file_path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """Normalize a single B1 plan to V6 format.

    Returns (was_modified, list of changes made).
    """
    changes: list[str] = []

    data = yaml.load(file_path)
    if not data:
        return False, ["SKIP: empty file"]

    if not isinstance(data, dict):
        return False, ["SKIP: root is not a dict"]

    # 1. Strip extraneous fields
    for field in EXTRANEOUS_FIELDS:
        if field in data:
            del data[field]
            changes.append(f"removed {field}")

    # 2. Migrate sources -> references
    if "sources" in data:
        sources = data.pop("sources")
        data["references"] = migrate_sources_to_references(sources)
        changes.append("sources -> references (name->title, dropped type:reference)")
    elif "references" not in data:
        data["references"] = []
        changes.append("added empty references")

    # 3. Clean activity_hints[].items to integers
    activity_hints = data.get("activity_hints", [])
    if activity_hints:
        for hint in activity_hints:
            if isinstance(hint, dict) and "items" in hint:
                old_val = hint["items"]
                new_val = cast_items_value(old_val)
                if new_val is not None and not isinstance(old_val, int):
                    hint["items"] = new_val
                    changes.append(f"activity_hints items: '{old_val}' -> {new_val}")

    # 4. Add register if missing
    if "register" not in data:
        data["register"] = "розмовний"
        changes.append("added register: розмовний")

    # 5. Add grammar if missing
    if "grammar" not in data:
        data["grammar"] = []
        changes.append("added grammar: []")

    # 6. Version -> 3.0
    old_version = data.get("version", "")
    if str(old_version) != "3.0":
        data["version"] = "3.0"
        changes.append(f"version: {old_version} -> 3.0")

    # 7. word_target normalization
    current_target = data.get("word_target", 0)
    if current_target != WORD_TARGET:
        data["word_target"] = WORD_TARGET
        changes.append(f"word_target: {current_target} -> {WORD_TARGET}")

    # Validation warnings (non-blocking)
    if not activity_hints:
        changes.append("WARNING: no activity_hints")

    vocab = data.get("vocabulary_hints", {})
    if not vocab or not vocab.get("required", []):
        changes.append("WARNING: no vocabulary_hints.required")

    outline = data.get("content_outline", [])
    for section in outline:
        if isinstance(section, dict) and "words" not in section:
            section_name = section.get("section", "unknown")
            changes.append(f"WARNING: section '{section_name}' missing word budget")

    # Write back if there are real changes
    if changes and not dry_run:
        real_changes = [c for c in changes if not c.startswith("WARNING")]
        if real_changes:
            yaml.dump(data, file_path)

    has_real_changes = any(not c.startswith("WARNING") for c in changes)
    return has_real_changes, changes


def main():
    parser = argparse.ArgumentParser(description="Convert B1 plans to V6 format")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    if not PLANS_DIR.is_dir():
        print(f"B1 plans directory not found: {PLANS_DIR}")
        sys.exit(1)

    plan_files = sorted(PLANS_DIR.glob("*.yaml"))
    print(f"\n{'=' * 60}")
    print(f"  B1 Plans V6 Conversion ({len(plan_files)} plans)")
    if args.dry_run:
        print("  MODE: DRY RUN (no files will be written)")
    print(f"{'=' * 60}")

    stats = {"total": 0, "modified": 0, "warnings": 0, "errors": 0}
    warnings: list[str] = []

    for plan_file in plan_files:
        stats["total"] += 1
        try:
            modified, changes = normalize_plan(plan_file, args.dry_run)
            if modified:
                stats["modified"] += 1

            change_msgs = [c for c in changes if not c.startswith(("WARNING", "SKIP"))]
            warning_msgs = [c for c in changes if c.startswith("WARNING")]

            if change_msgs:
                prefix = "[DRY RUN] " if args.dry_run else ""
                print(f"  {prefix}{plan_file.stem}: {', '.join(change_msgs)}")
            if warning_msgs:
                stats["warnings"] += len(warning_msgs)
                for w in warning_msgs:
                    warnings.append(f"  {plan_file.stem}: {w}")

        except Exception as e:
            stats["errors"] += 1
            print(f"  ERROR {plan_file.stem}: {e}")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Summary: {stats['modified']}/{stats['total']} modified, "
          f"{stats['warnings']} warnings, {stats['errors']} errors")
    if args.dry_run:
        print("  (DRY RUN -- no files were written)")
    print(f"{'=' * 60}")

    if warnings:
        print(f"\n  Warnings ({len(warnings)}):")
        for w in warnings[:30]:
            print(f"    {w}")
        if len(warnings) > 30:
            print(f"    ...and {len(warnings) - 30} more")


if __name__ == "__main__":
    main()
