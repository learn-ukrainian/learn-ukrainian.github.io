#!/usr/bin/env python3
"""
Validate plan files for common issues.

Usage:
    .venv/bin/python scripts/validate_plans.py [level]

Examples:
    .venv/bin/python scripts/validate_plans.py          # All levels
    .venv/bin/python scripts/validate_plans.py hist  # Single level
"""

import sys
from collections import Counter
from pathlib import Path

import yaml


def validate_plan(plan_path: Path) -> list[dict]:
    """Validate a single plan file and return list of issues."""
    issues = []

    try:
        with open(plan_path, encoding='utf-8') as f:
            plan = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [{'severity': 'error', 'type': 'YAML_PARSE_ERROR', 'message': str(e)}]

    if not plan:
        return [{'severity': 'error', 'type': 'EMPTY_PLAN', 'message': 'Plan file is empty'}]

    # Check for content_outline
    outline = plan.get('content_outline', [])
    if not outline:
        issues.append({
            'severity': 'warning',
            'type': 'NO_OUTLINE',
            'message': 'Plan has no content_outline'
        })
        return issues

    # Check for duplicate sections
    section_names = [s.get('section', '') for s in outline if isinstance(s, dict)]
    duplicates = [name for name, count in Counter(section_names).items() if count > 1]

    for dup in duplicates:
        issues.append({
            'severity': 'error',
            'type': 'DUPLICATE_SECTION',
            'message': f"Section '{dup}' appears multiple times"
        })

    # Check required fields
    required_fields = ['module', 'level', 'title']
    for field in required_fields:
        if not plan.get(field):
            issues.append({
                'severity': 'warning',
                'type': 'MISSING_FIELD',
                'message': f"Missing required field: {field}"
            })

    return issues


def main():
    plans_dir = Path('curriculum/l2-uk-en/plans')

    # Determine which levels to check
    levels = [sys.argv[1]] if len(sys.argv) > 1 else [d.name for d in plans_dir.iterdir() if d.is_dir()]

    total_plans = 0
    total_errors = 0
    total_warnings = 0

    print("=" * 60)
    print("PLAN VALIDATION REPORT")
    print("=" * 60)

    for level in sorted(levels):
        level_dir = plans_dir / level
        if not level_dir.exists():
            print(f"\n[!] Level directory not found: {level}")
            continue

        plan_files = list(level_dir.glob('*.yaml'))
        level_errors = 0
        level_warnings = 0

        print(f"\n--- {level.upper()} ({len(plan_files)} plans) ---")

        for plan_path in sorted(plan_files):
            total_plans += 1
            issues = validate_plan(plan_path)

            errors = [i for i in issues if i['severity'] == 'error']
            warnings = [i for i in issues if i['severity'] == 'warning']

            level_errors += len(errors)
            level_warnings += len(warnings)

            if errors:
                print(f"\n  {plan_path.name}")
                for issue in errors:
                    print(f"    [ERROR] {issue['type']}: {issue['message']}")

            if warnings and not errors:
                # Only show warnings if no errors (to reduce noise)
                pass

        total_errors += level_errors
        total_warnings += level_warnings

        if level_errors == 0:
            print(f"  All {len(plan_files)} plans OK")

    print("\n" + "=" * 60)
    print(f"SUMMARY: {total_plans} plans checked")
    print(f"  Errors:   {total_errors}")
    print(f"  Warnings: {total_warnings}")

    if total_errors > 0:
        print("\n[!] Fix errors before proceeding.")
        sys.exit(1)
    else:
        print("\n[OK] All plans valid.")
        sys.exit(0)


if __name__ == '__main__':
    main()
