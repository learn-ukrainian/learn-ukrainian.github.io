#!/usr/bin/env python3
"""
Validate module numbering consistency across curriculum.yaml and meta files.

Checks:
1. curriculum.yaml module numbering (source of truth)
2. meta/*.yaml module IDs match curriculum order
3. Reports all discrepancies

Usage:
    .venv/bin/python scripts/validate_module_numbering.py              # All levels
    .venv/bin/python scripts/validate_module_numbering.py b2-hist      # Single level
    .venv/bin/python scripts/validate_module_numbering.py --fix        # Auto-fix discrepancies
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


def check_level(level: str, modules: List[str], fix: bool = False) -> Tuple[int, int]:
    """
    Check module numbering for a single level.

    Returns: (discrepancies_found, total_modules)
    """
    print(f"\n{BOLD}{BLUE}Checking {level.upper()}...{RESET}")

    meta_dir = ROOT / "curriculum" / "l2-uk-en" / level / "meta"
    if not meta_dir.exists():
        print(f"  {YELLOW}⚠️  No meta directory found{RESET}")
        return 0, 0

    discrepancies = 0
    total = len(modules)

    for i, slug in enumerate(modules, start=1):
        expected_num = i

        # Determine padding based on total module count
        if total >= 100:
            expected_id = f"{level}-{expected_num:03d}"
        else:
            expected_id = f"{level}-{expected_num:02d}"

        # Try multiple filename patterns
        # Pattern 1: slug only (B2-HIST, C1-BIO, etc.)
        meta_file = meta_dir / f"{slug}.yaml"

        # Pattern 2: numbered prefix (A1, A2, etc.)
        if not meta_file.exists():
            if total >= 100:
                meta_file = meta_dir / f"{expected_num:03d}-{slug}.yaml"
            else:
                meta_file = meta_dir / f"{expected_num:02d}-{slug}.yaml"

        if not meta_file.exists():
            print(f"  {YELLOW}⚠️  M{expected_num:03d} {slug}: meta file missing{RESET}")
            continue

        # Read meta file
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = yaml.safe_load(f)

            actual_module = meta.get('module', 'MISSING')
            actual_id = meta.get('id', 'MISSING')

            # Check for discrepancies
            has_error = False
            errors = []

            if actual_module != expected_id:
                has_error = True
                errors.append(f"module: {actual_module} (expected: {expected_id})")

            if actual_id != expected_id:
                has_error = True
                errors.append(f"id: {actual_id} (expected: {expected_id})")

            if has_error:
                discrepancies += 1
                print(f"  {RED}❌ M{expected_num:03d} {slug}:{RESET}")
                for error in errors:
                    print(f"      {error}")

                if fix:
                    # Fix the meta file
                    meta['module'] = expected_id
                    meta['id'] = expected_id

                    with open(meta_file, 'w', encoding='utf-8') as f:
                        yaml.dump(meta, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

                    print(f"      {GREEN}✓ Fixed{RESET}")

        except Exception as e:
            print(f"  {RED}❌ M{expected_num:03d} {slug}: Error reading meta file - {e}{RESET}")
            discrepancies += 1

    return discrepancies, total


def main():
    """Main validation routine."""
    args = sys.argv[1:]

    fix_mode = '--fix' in args
    args = [arg for arg in args if arg != '--fix']

    target_level = args[0] if args else None

    print(f"{BOLD}Module Numbering Validation{RESET}")
    if fix_mode:
        print(f"{YELLOW}⚠️  FIX MODE ENABLED - Will update meta files{RESET}")
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

        disc, total = check_level(level_name, modules, fix=fix_mode)
        total_discrepancies += disc
        total_modules += total

    # Summary
    print(f"\n{BOLD}Summary:{RESET}")
    print(f"  Total modules checked: {total_modules}")

    if total_discrepancies == 0:
        print(f"  {GREEN}✅ No discrepancies found - all module numbers are consistent!{RESET}")
    else:
        print(f"  {RED}❌ Discrepancies found: {total_discrepancies}{RESET}")
        if not fix_mode:
            print(f"\n{YELLOW}💡 Run with --fix to automatically correct meta files{RESET}")
        sys.exit(1)


if __name__ == '__main__':
    main()
