#!/usr/bin/env python3
"""
wire_navigation.py — Add connects_to and prerequisites to unwired plan files.

Wiring rules:
  1. Each module lists its immediate predecessor as prerequisite (prev slug)
  2. Each module connects_to its immediate successor
  3. First module of each level: prerequisite = previous level's final exam
  4. Last module of each level: connects_to = next level's first module
  5. Checkpoints: prerequisite = all modules since previous checkpoint

Only adds fields if they're missing or empty. Does NOT overwrite existing wiring.

Usage:
  .venv/bin/python scripts/wire_navigation.py --dry-run
  .venv/bin/python scripts/wire_navigation.py
  .venv/bin/python scripts/wire_navigation.py --level a2

GH issue: #702 (Tier 2)
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

PLANS_ROOT = Path("curriculum/l2-uk-en/plans")
CURRICULUM_YAML = Path("curriculum/l2-uk-en/curriculum.yaml")

# Cross-level wiring: level → (previous_level_final_slug, next_level_first_slug)
LEVEL_CHAIN = {
    "a1": (None, "the-dative-i-pronouns"),  # A1 → A2
    "a2": ("a1-final-exam", "how-to-talk-about-grammar"),  # A2 → B1
    "b1": ("a2-final-exam", "passive-voice-system"),  # B1 → B2
    "b2": ("b1-final-exam", "b2-review-bridge"),  # B2 → C1
    "c1": ("b2-final-exam", "c1-bridge-assessment"),  # C1 → C2
    "c2": ("c1-final-checkpoint", None),  # C2 (terminal)
}

# Levels that get navigation wiring
CORE_LEVELS = ["a1", "a2", "b1", "b2", "c1", "c2"]
SEMINAR_LEVELS = ["hist", "bio", "istorio", "lit", "oes", "ruth", "b2-pro", "c1-pro"]


def load_curriculum_order():
    """Load curriculum.yaml and return {level: [slug1, slug2, ...]}."""
    with open(CURRICULUM_YAML) as f:
        data = yaml.safe_load(f)
    result = {}
    for level_key, level_data in data.get("levels", {}).items():
        modules = level_data.get("modules", [])
        result[level_key] = modules
    return result


def parse_phases_from_curriculum(level):
    """Parse phase comments from curriculum.yaml to get phase boundaries.

    Returns list of (phase_name, start_idx, end_idx) tuples (0-indexed).
    """
    with open(CURRICULUM_YAML) as f:
        lines = f.readlines()

    # Find the level section
    in_level = False
    in_modules = False
    phases = []
    current_phase = None
    module_idx = 0
    phase_start = 0

    for line in lines:
        stripped = line.strip()

        # Detect level start
        if re.match(rf"^\s*{re.escape(level)}:\s*$", line):
            in_level = True
            continue

        if in_level and not in_modules:
            if stripped == "modules:":
                in_modules = True
            elif re.match(r"^\s*\w+:", stripped) and "type:" not in stripped:
                # Hit next level
                break
            continue

        if in_modules:
            # Check for phase comment
            phase_match = re.match(r"\s*#\s*(Phase|──)\s*(.+?)(?:\s*──.*)?$", stripped)
            if phase_match:
                if current_phase is not None and module_idx > phase_start:
                    phases.append((current_phase, phase_start, module_idx - 1))
                current_phase = phase_match.group(2).strip()
                phase_start = module_idx
                continue

            # Check for module entry
            module_match = re.match(r"\s*-\s+(\S+)", stripped)
            if module_match:
                module_idx += 1
                continue

            # Check for end of modules list (next level or end of file)
            if re.match(r"^\s*\w+:", stripped) and not stripped.startswith("#"):
                break

    # Close last phase
    if current_phase is not None and module_idx > phase_start:
        phases.append((current_phase, phase_start, module_idx - 1))

    return phases


def wire_level(level, slugs, dry_run=False):
    """Wire connects_to and prerequisites for all plans in a level.

    Returns (files_modified, changes_count).
    """
    plans_dir = PLANS_ROOT / level
    if not plans_dir.exists():
        return 0, 0

    files_modified = 0
    changes_count = 0
    prev_level_final = LEVEL_CHAIN.get(level, (None, None))[0] if level in LEVEL_CHAIN else None
    next_level_first = LEVEL_CHAIN.get(level, (None, None))[1] if level in LEVEL_CHAIN else None

    for i, slug in enumerate(slugs):
        plan_file = plans_dir / f"{slug}.yaml"
        if not plan_file.exists():
            continue

        try:
            with open(plan_file) as f:
                data = yaml.safe_load(f)
            if not data:
                continue
        except yaml.YAMLError:
            continue

        changed = False
        i + 1  # 1-indexed

        # --- Prerequisites ---
        existing_prereqs = data.get("prerequisites")
        if not existing_prereqs:
            prereqs = []
            if i == 0:
                # First module: prerequisite is previous level's final
                if prev_level_final:
                    prereqs.append(prev_level_final)
            else:
                # Previous module in sequence
                prev_slug = slugs[i - 1]
                prereqs.append(prev_slug)

            if prereqs:
                data["prerequisites"] = prereqs
                changed = True
                changes_count += 1

        # --- Connects_to ---
        existing_connects = data.get("connects_to")
        if not existing_connects:
            connects = []
            if i < len(slugs) - 1:
                # Next module in sequence
                next_slug = slugs[i + 1]
                connects.append(next_slug)
            else:
                # Last module: connect to next level's first
                if next_level_first:
                    connects.append(next_level_first)

            if connects:
                data["connects_to"] = connects
                changed = True
                changes_count += 1

        if changed:
            files_modified += 1
            if not dry_run:
                with open(plan_file, "w") as f:
                    yaml.dump(
                        data, f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                        width=120,
                    )

    return files_modified, changes_count


def wire_seminar_level(level, slugs, dry_run=False):
    """Wire connects_to for seminar tracks (sequential chain only, no cross-level).

    Returns (files_modified, changes_count).
    """
    plans_dir = PLANS_ROOT / level
    if not plans_dir.exists():
        return 0, 0

    files_modified = 0
    changes_count = 0

    for i, slug in enumerate(slugs):
        plan_file = plans_dir / f"{slug}.yaml"
        if not plan_file.exists():
            continue

        try:
            with open(plan_file) as f:
                data = yaml.safe_load(f)
            if not data:
                continue
        except yaml.YAMLError:
            continue

        changed = False

        # --- Prerequisites ---
        if not data.get("prerequisites") and i > 0:
            data["prerequisites"] = [slugs[i - 1]]
            changed = True
            changes_count += 1

        # --- Connects_to ---
        if not data.get("connects_to") and i < len(slugs) - 1:
            data["connects_to"] = [slugs[i + 1]]
            changed = True
            changes_count += 1

        if changed:
            files_modified += 1
            if not dry_run:
                with open(plan_file, "w") as f:
                    yaml.dump(
                        data, f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                        width=120,
                    )

    return files_modified, changes_count


def main():
    parser = argparse.ArgumentParser(description="Wire navigation graph for plan files")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument("--level", type=str, help="Wire only this level")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    curriculum_order = load_curriculum_order()
    total_files = 0
    total_changes = 0
    summary = {}

    all_levels = CORE_LEVELS + SEMINAR_LEVELS
    levels_to_wire = [args.level] if args.level else all_levels

    for level in levels_to_wire:
        if level not in curriculum_order:
            continue

        slugs = curriculum_order[level]
        if level in CORE_LEVELS:
            files, changes = wire_level(level, slugs, args.dry_run)
        else:
            files, changes = wire_seminar_level(level, slugs, args.dry_run)

        summary[level] = {"files": files, "changes": changes, "total": len(slugs)}
        total_files += files
        total_changes += changes

    print("\n" + "=" * 50)
    print(f"{'LEVEL':<12} {'WIRED':>6} {'CHANGES':>8} {'TOTAL':>6}")
    print("-" * 50)
    for level, stats in summary.items():
        print(f"{level:<12} {stats['files']:>6} {stats['changes']:>8} {stats['total']:>6}")
    print("-" * 50)
    print(f"{'TOTAL':<12} {total_files:>6} {total_changes:>8}")
    print("=" * 50)

    if args.dry_run:
        print("\n(DRY RUN — no files modified)")
    else:
        print(f"\n{total_files} files updated, {total_changes} navigation links added.")


if __name__ == "__main__":
    sys.exit(main())
