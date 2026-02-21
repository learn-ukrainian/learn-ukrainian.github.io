#!/usr/bin/env python3
"""
Fix activity_hints in plans to match actual activities in activities.yaml.

The plan's activity_hints should only list types that exist in the activities file.
"""

import sys
from pathlib import Path
import yaml


def get_activity_types_from_file(activities_path: Path) -> set[str]:
    """Get unique activity types from activities.yaml."""
    if not activities_path.exists():
        return set()

    content = activities_path.read_text(encoding='utf-8')
    data = yaml.safe_load(content)

    if not data:
        return set()

    # Handle both wrapped (activities: [...]) and bare list formats
    if isinstance(data, dict) and 'activities' in data:
        activities = data['activities']
    elif isinstance(data, list):
        activities = data
    else:
        return set()

    types = set()
    for activity in activities:
        if isinstance(activity, dict) and 'type' in activity:
            types.add(activity['type'])

    return types


def fix_activity_hints(plan_path: Path, actual_types: set[str], dry_run: bool = False) -> bool:
    """Update activity_hints to only include types that exist in activities.yaml."""
    content = plan_path.read_text(encoding='utf-8')
    plan = yaml.safe_load(content)

    if not plan or 'activity_hints' not in plan:
        return False

    old_hints = plan['activity_hints']
    new_hints = []

    for hint in old_hints:
        if isinstance(hint, dict) and 'type' in hint:
            if hint['type'] in actual_types:
                new_hints.append(hint)
            # Skip hints for types that don't exist

    if len(new_hints) == len(old_hints):
        return False  # No change needed

    plan['activity_hints'] = new_hints

    if dry_run:
        removed = len(old_hints) - len(new_hints)
        print(f"  Would remove {removed} hints")
        return True

    with open(plan_path, 'w', encoding='utf-8') as f:
        yaml.dump(plan, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)

    return True


def main():
    dry_run = '--dry-run' in sys.argv
    level = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else 'a1'

    base_path = Path('curriculum/l2-uk-en')
    activities_path = base_path / level / 'activities'
    plans_path = base_path / 'plans' / level

    if not activities_path.exists() or not plans_path.exists():
        print(f"ERROR: Paths not found for level {level}")
        sys.exit(1)

    plan_files = sorted(plans_path.glob('*.yaml'))

    updated = 0
    skipped = 0

    for plan_file in plan_files:
        slug = plan_file.stem

        # Try both with and without number prefix
        act_file = activities_path / f"{slug}.yaml"
        if not act_file.exists():
            # Find by matching the slug part (without number)
            matching = list(activities_path.glob(f"*{slug.lstrip('0123456789-')}.yaml"))
            if matching:
                act_file = matching[0]

        print(f"Processing {slug}...", end=' ')

        actual_types = get_activity_types_from_file(act_file)

        if not actual_types:
            print("SKIP (no activities)")
            skipped += 1
            continue

        if fix_activity_hints(plan_file, actual_types, dry_run):
            print("FIXED")
            updated += 1
        else:
            print("OK")
            skipped += 1

    print(f"\nSummary: {updated} fixed, {skipped} skipped")
    if dry_run:
        print("(DRY RUN)")


if __name__ == '__main__':
    main()
