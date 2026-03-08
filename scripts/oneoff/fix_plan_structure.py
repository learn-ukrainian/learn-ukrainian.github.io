#!/usr/bin/env python3
"""
fix_plan_structure.py — Tier 1 structural fixes for all plan files.

Fixes across all levels:
  T1.1: Sequence numbers (renumber to match curriculum.yaml order)
  T1.2: Add missing word_target field (from config.py)
  T1.3: Add per-section words to content_outline
  T1.4-T1.6: Schema migration (OES/RUTH description→points, ISTORIO subsections→points)
  T1.7: Fix B2-PRO word_target 2000→4000
  T1.8: Fix vocabulary_hints "[]" strings

Usage:
  .venv/bin/python scripts/fix_plan_structure.py --dry-run    # Preview changes
  .venv/bin/python scripts/fix_plan_structure.py              # Apply changes
  .venv/bin/python scripts/fix_plan_structure.py --level c2   # Fix one level only

GH issue: #702
"""

import argparse
import os
import sys
import math
from pathlib import Path
from collections import OrderedDict

import yaml

# --- Config ---

PLANS_ROOT = Path("curriculum/l2-uk-en/plans")
CURRICULUM_YAML = Path("curriculum/l2-uk-en/curriculum.yaml")

# Level directory name → config.py word target
# Based on scripts/audit/config.py (verified 2026-03-01)
WORD_TARGETS = {
    "a1": 2000,
    "a2": 3000,
    "b1": 4000,
    "b2": 4000,
    "b2-pro": 4000,  # B2 level = 4000 (was wrongly 2000 in plans)
    "c1": 4000,
    "c1-pro": 4000,  # C1 level = 4000
    "c2": 5000,
    "hist": 5000,
    "bio": 5000,
    "istorio": 5000,
    "lit": 5000,
    "oes": 5000,
    "ruth": 5000,
}

# Level directory name → level field value in plan YAML
LEVEL_NAMES = {
    "a1": "A1",
    "a2": "A2",
    "b1": "B1",
    "b2": "B2",
    "b2-pro": "B2-PRO",
    "c1": "C1",
    "c1-pro": "C1-PRO",
    "c2": "C2",
    "hist": "HIST",
    "bio": "BIO",
    "istorio": "ISTORIO",
    "lit": "LIT",
    "oes": "OES",
    "ruth": "RUTH",
}

# Module ID prefix
MODULE_PREFIXES = {
    "a1": "a1",
    "a2": "a2",
    "b1": "b1",
    "b2": "b2",
    "b2-pro": "b2-pro",
    "c1": "c1",
    "c1-pro": "c1-pro",
    "c2": "c2",
    "hist": "hist",
    "bio": "bio",
    "istorio": "istorio",
    "lit": "lit",
    "oes": "oes",
    "ruth": "ruth",
}


def load_curriculum_order():
    """Load curriculum.yaml and return {level_dir: [slug1, slug2, ...]}."""
    with open(CURRICULUM_YAML) as f:
        data = yaml.safe_load(f)

    result = {}
    for level_key, level_data in data.get("levels", {}).items():
        modules = level_data.get("modules", [])
        # level_key in curriculum.yaml matches directory name
        result[level_key] = modules
    return result


def slug_from_filename(filename):
    """Extract slug from plan filename (remove .yaml extension)."""
    return Path(filename).stem


def allocate_section_words(sections, total_words):
    """Proportionally allocate words across sections.

    If sections already have words, returns them unchanged.
    Otherwise distributes total_words evenly, rounding to nearest 50.
    """
    # Check if any section already has words
    has_words = any(s.get("words") for s in sections)
    if has_words:
        return sections

    n = len(sections)
    if n == 0:
        return sections

    # Even distribution, rounded to nearest 50
    base = round(total_words / n / 50) * 50
    if base < 200:
        base = 200

    allocated = 0
    for i, section in enumerate(sections):
        if i < n - 1:
            section["words"] = base
            allocated += base
        else:
            # Last section gets remainder
            section["words"] = total_words - allocated

    return sections


def migrate_content_outline(sections, track):
    """Migrate content_outline sections to Schema A format.

    - OES/RUTH: `description` (string) → `points` (list)
    - ISTORIO: `subsections` → `points`
    """
    for section in sections:
        # OES/RUTH: description → points
        if "description" in section and "points" not in section:
            desc = section.pop("description")
            if isinstance(desc, str) and desc.strip():
                section["points"] = [desc]
            else:
                section["points"] = []

        # ISTORIO: subsections → points
        if "subsections" in section and "points" not in section:
            section["points"] = section.pop("subsections")

        # Ensure points exists
        if "points" not in section:
            section["points"] = []

    return sections


def fix_vocabulary_hints(vocab_hints):
    """Fix vocabulary_hints from broken string '[]' to proper structure."""
    if isinstance(vocab_hints, str):
        # '[]' or empty string
        return {"required": [], "recommended": []}
    if vocab_hints is None:
        return {"required": [], "recommended": []}
    return vocab_hints


def fix_plan(plan_data, slug, sequence, level_dir, dry_run=False):
    """Apply all structural fixes to a plan. Returns (plan_data, changes_list)."""
    changes = []
    prefix = MODULE_PREFIXES[level_dir]
    level_name = LEVEL_NAMES[level_dir]
    word_target = WORD_TARGETS[level_dir]

    # --- T1.1: Fix sequence ---
    old_seq = plan_data.get("sequence")
    if old_seq != sequence:
        changes.append(f"sequence: {old_seq} → {sequence}")
        plan_data["sequence"] = sequence

    # --- T1.1: Fix module ID ---
    expected_module = f"{prefix}-{sequence:03d}"
    old_module = plan_data.get("module")
    if old_module != expected_module:
        changes.append(f"module: {old_module} → {expected_module}")
        plan_data["module"] = expected_module

    # --- T1.1: Fix slug ---
    old_slug = plan_data.get("slug")
    if old_slug != slug:
        changes.append(f"slug: {old_slug} → {slug}")
        plan_data["slug"] = slug

    # --- Add missing level ---
    old_level = plan_data.get("level")
    if old_level != level_name:
        changes.append(f"level: {old_level} → {level_name}")
        plan_data["level"] = level_name

    # --- Add missing version ---
    if not plan_data.get("version"):
        changes.append("version: (missing) → '2.0'")
        plan_data["version"] = "2.0"

    # --- T1.2: Add missing word_target ---
    old_wt = plan_data.get("word_target")
    if old_wt != word_target:
        changes.append(f"word_target: {old_wt} → {word_target}")
        plan_data["word_target"] = word_target

    # --- T1.3: Add per-section words + schema migration ---
    outline = plan_data.get("content_outline", [])
    if outline and isinstance(outline, list):
        # Track what needs migration
        had_subsections = any("subsections" in s for s in outline)
        had_description = any("description" in s and "points" not in s for s in outline)
        had_no_words = not any(s.get("words") for s in outline)

        # Migrate schema first
        outline = migrate_content_outline(outline, level_dir)
        if had_subsections:
            changes.append("content_outline: subsections → points")
        if had_description:
            changes.append("content_outline: description → points")

        # Then allocate words
        outline = allocate_section_words(outline, word_target)
        if had_no_words and len(outline) > 0:
            changes.append(f"content_outline: added per-section words ({len(outline)} sections)")

        plan_data["content_outline"] = outline

    # --- T1.8: Fix vocabulary_hints ---
    vocab_hints = plan_data.get("vocabulary_hints")
    if isinstance(vocab_hints, str) or vocab_hints is None:
        old_vh = repr(vocab_hints)
        plan_data["vocabulary_hints"] = fix_vocabulary_hints(vocab_hints)
        changes.append(f"vocabulary_hints: {old_vh} → proper map")

    # --- OES/RUTH: Migrate activity_types → activity_hints ---
    if "activity_types" in plan_data and "activity_hints" not in plan_data:
        at = plan_data.pop("activity_types")
        if isinstance(at, list):
            plan_data["activity_hints"] = [
                {"type": t, "focus": "", "items": 1} for t in at
            ]
            changes.append(f"activity_types → activity_hints ({len(at)} types)")

    # --- OES/RUTH: Remove duplicate fields ---
    for old_field in ["module_number", "phase_id", "phase_name", "title_en", "title_uk"]:
        if old_field in plan_data:
            # Preserve title_uk as title if title is missing
            if old_field == "title_uk" and not plan_data.get("title"):
                plan_data["title"] = plan_data[old_field]
                changes.append(f"title_uk → title")
            # Preserve title_en as subtitle if useful
            if old_field == "title_en" and not plan_data.get("subtitle"):
                plan_data["subtitle"] = plan_data[old_field]
                changes.append(f"title_en → subtitle")
            del plan_data[old_field]
            if old_field not in ("title_uk", "title_en"):
                changes.append(f"removed deprecated field: {old_field}")

    return plan_data, changes


def write_plan(filepath, plan_data):
    """Write plan data back to YAML, preserving field order."""
    # Define preferred field order
    field_order = [
        "module", "level", "sequence", "slug", "version",
        "title", "subtitle", "focus", "pedagogy", "phase",
        "word_target", "objectives", "sources",
        "content_outline", "vocabulary_hints", "vocabulary",
        "activity_hints", "activities",
        "connects_to", "prerequisites",
        "persona", "grammar", "register",
        "vocabulary_hints_extended",
    ]

    ordered = OrderedDict()
    for key in field_order:
        if key in plan_data:
            ordered[key] = plan_data[key]
    # Add any remaining keys not in the order list
    for key in plan_data:
        if key not in ordered:
            ordered[key] = plan_data[key]

    with open(filepath, "w") as f:
        yaml.dump(
            dict(ordered),
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )


def main():
    parser = argparse.ArgumentParser(description="Fix plan file structure across all levels")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--level", type=str, help="Fix only this level (e.g., c2, hist)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-file changes")
    args = parser.parse_args()

    # Load canonical order from curriculum.yaml
    curriculum_order = load_curriculum_order()

    total_files = 0
    total_changes = 0
    total_errors = 0
    summary = {}

    levels_to_fix = [args.level] if args.level else sorted(WORD_TARGETS.keys())

    for level_dir in levels_to_fix:
        if level_dir not in curriculum_order:
            print(f"  SKIP {level_dir}: not found in curriculum.yaml")
            continue

        slugs = curriculum_order[level_dir]
        plans_dir = PLANS_ROOT / level_dir

        if not plans_dir.exists():
            print(f"  SKIP {level_dir}: directory {plans_dir} does not exist")
            continue

        level_changes = 0
        level_files = 0
        level_errors = 0

        for seq_idx, slug in enumerate(slugs, start=1):
            plan_file = plans_dir / f"{slug}.yaml"
            if not plan_file.exists():
                if args.verbose:
                    print(f"  MISSING: {plan_file}")
                level_errors += 1
                continue

            try:
                with open(plan_file) as f:
                    plan_data = yaml.safe_load(f)
                if not plan_data or not isinstance(plan_data, dict):
                    print(f"  ERROR: {plan_file} — empty or invalid YAML")
                    level_errors += 1
                    continue
            except yaml.YAMLError as e:
                print(f"  ERROR: {plan_file} — YAML parse error: {e}")
                level_errors += 1
                continue

            plan_data, changes = fix_plan(plan_data, slug, seq_idx, level_dir)
            level_files += 1

            if changes:
                level_changes += len(changes)
                if args.verbose:
                    print(f"  {slug}.yaml: {len(changes)} changes")
                    for c in changes:
                        print(f"    - {c}")

                if not args.dry_run:
                    write_plan(plan_file, plan_data)

        summary[level_dir] = {
            "files": level_files,
            "changes": level_changes,
            "errors": level_errors,
            "total_modules": len(slugs),
        }
        total_files += level_files
        total_changes += level_changes
        total_errors += level_errors

    # Print summary
    print("\n" + "=" * 60)
    print(f"{'LEVEL':<12} {'FILES':>6} {'CHANGES':>8} {'ERRORS':>7} {'MODULES':>8}")
    print("-" * 60)
    for level, stats in summary.items():
        print(
            f"{level:<12} {stats['files']:>6} {stats['changes']:>8} "
            f"{stats['errors']:>7} {stats['total_modules']:>8}"
        )
    print("-" * 60)
    print(f"{'TOTAL':<12} {total_files:>6} {total_changes:>8} {total_errors:>7}")
    print("=" * 60)

    if args.dry_run:
        print("\n(DRY RUN — no files modified)")
    else:
        print(f"\n{total_files} files updated, {total_changes} changes applied.")

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
