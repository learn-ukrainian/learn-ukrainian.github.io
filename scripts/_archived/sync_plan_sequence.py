#!/usr/bin/env python3
"""
Sync sequence numbers in plan files from curriculum.yaml.

Adds/updates the 'sequence' field in each plan file to match its
position in curriculum.yaml (the source of truth).

Usage:
    .venv/bin/python scripts/sync_plan_sequence.py              # All levels
    .venv/bin/python scripts/sync_plan_sequence.py b2-hist      # Single level
    .venv/bin/python scripts/sync_plan_sequence.py --fix        # Auto-update plans
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

# Project root
ROOT = Path(__file__).parent.parent

# ANSI color codes
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
BOLD = '\033[1m'
RESET = '\033[0m'


def load_curriculum() -> dict:
    """Load curriculum.yaml."""
    curriculum_path = ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    with open(curriculum_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def sync_level_plans(level: str, modules: List[str], fix: bool = False) -> Tuple[int, int]:
    """
    Sync sequence numbers for a level's plan files.

    Returns: (discrepancies_found, total_modules)
    """
    print(f"\n{BOLD}{BLUE}Checking {level.upper()} plans...{RESET}")

    plans_dir = ROOT / "curriculum" / "l2-uk-en" / "plans" / level
    if not plans_dir.exists():
        print(f"  {YELLOW}⚠️  No plans directory found{RESET}")
        return 0, 0

    discrepancies = 0
    total = len(modules)

    for i, slug in enumerate(modules, start=1):
        expected_sequence = i
        plan_file = plans_dir / f"{slug}.yaml"

        if not plan_file.exists():
            print(f"  {YELLOW}⚠️  M{expected_sequence:03d} {slug}: plan file missing{RESET}")
            continue

        # Read plan file
        try:
            with open(plan_file, 'r', encoding='utf-8') as f:
                plan = yaml.safe_load(f)

            actual_sequence = plan.get('sequence')
            has_error = False

            if actual_sequence is None:
                has_error = True
                print(f"  {RED}❌ M{expected_sequence:03d} {slug}:{RESET}")
                print(f"      sequence: MISSING (expected: {expected_sequence})")
            elif actual_sequence != expected_sequence:
                has_error = True
                print(f"  {RED}❌ M{expected_sequence:03d} {slug}:{RESET}")
                print(f"      sequence: {actual_sequence} (expected: {expected_sequence})")

            if has_error:
                discrepancies += 1

                if fix:
                    # Add/update sequence field
                    plan['sequence'] = expected_sequence

                    # Write back with preserved order (insert sequence after level)
                    with open(plan_file, 'w', encoding='utf-8') as f:
                        # Custom serialization to control field order
                        ordered_plan = {}
                        # Standard order
                        for key in ['module', 'level', 'sequence', 'slug', 'version', 'title', 'subtitle']:
                            if key in plan:
                                ordered_plan[key] = plan[key]
                        # Add remaining keys
                        for key, value in plan.items():
                            if key not in ordered_plan:
                                ordered_plan[key] = value

                        yaml.dump(ordered_plan, f, default_flow_style=False,
                                 allow_unicode=True, sort_keys=False)

                    print(f"      {GREEN}✓ Fixed{RESET}")

        except Exception as e:
            print(f"  {RED}❌ M{expected_sequence:03d} {slug}: Error - {e}{RESET}")
            discrepancies += 1

    return discrepancies, total


def main():
    """Main sync routine."""
    args = sys.argv[1:]

    fix_mode = '--fix' in args
    args = [arg for arg in args if arg != '--fix']

    target_level = args[0] if args else None

    print(f"{BOLD}Plan Sequence Number Sync{RESET}")
    if fix_mode:
        print(f"{YELLOW}⚠️  FIX MODE ENABLED - Will update plan files{RESET}")
    print()

    curriculum = load_curriculum()
    levels = curriculum.get('levels', {})

    total_discrepancies = 0
    total_modules = 0

    # Filter levels
    levels_to_check = {target_level: levels[target_level]} if target_level and target_level in levels else levels

    for level_name, level_data in levels_to_check.items():
        modules = level_data.get('modules', [])
        if not modules:
            continue

        disc, total = sync_level_plans(level_name, modules, fix=fix_mode)
        total_discrepancies += disc
        total_modules += total

    # Summary
    print(f"\n{BOLD}Summary:{RESET}")
    print(f"  Total modules checked: {total_modules}")

    if total_discrepancies == 0:
        print(f"  {GREEN}✅ All plan files have correct sequence numbers!{RESET}")
    else:
        print(f"  {RED}❌ Plans missing/wrong sequence: {total_discrepancies}{RESET}")
        if not fix_mode:
            print(f"\n{YELLOW}💡 Run with --fix to add sequence numbers to plan files{RESET}")
        sys.exit(1)


if __name__ == '__main__':
    main()
