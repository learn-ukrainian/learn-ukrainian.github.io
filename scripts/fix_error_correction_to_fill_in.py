#!/usr/bin/env python3
"""
Fix malformed error-correction activities that use transformation pattern.

These activities use "→ ___" pattern (transformation exercises) instead of
proper error-correction format with real error words. They should be converted
to fill-in activities.

Issue: #369
"""

import yaml
import re
from pathlib import Path
import sys

def is_malformed_error_correction(activity: dict) -> bool:
    """Check if an error-correction activity uses transformation/placeholder pattern."""
    if activity.get('type') != 'error-correction':
        return False

    items = activity.get('items', [])
    if not items:
        return False

    # Check for transformation pattern (→ ___) or blank error field
    malformed_count = 0
    for item in items:
        sentence = item.get('sentence', '')
        error = item.get('error', '')

        # Transformation pattern: "читати → ___"
        if '→' in sentence and '___' in sentence:
            malformed_count += 1
        # Blank/placeholder error
        elif error == '___' or error == '' or error is None:
            malformed_count += 1

    # If majority of items are malformed, the activity is malformed
    return malformed_count >= len(items) * 0.5

def convert_to_fill_in(activity: dict) -> dict:
    """Convert malformed error-correction to fill-in format."""
    new_activity = {
        'type': 'fill-in',
        'title': activity.get('title', 'Transform')
    }

    new_items = []
    for item in activity.get('items', []):
        new_item = {
            'sentence': item.get('sentence', ''),
            'answer': item.get('answer', ''),
            'options': item.get('options', [])
        }
        new_items.append(new_item)

    new_activity['items'] = new_items
    return new_activity

def fix_yaml_file(filepath: Path, dry_run: bool = False) -> dict:
    """Fix malformed error-correction activities in a YAML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse YAML
    activities = yaml.safe_load(content)
    if not activities:
        return {'fixed': 0, 'file': str(filepath)}

    # Handle both list and dict YAML structures
    if not isinstance(activities, list):
        return {'fixed': 0, 'file': str(filepath)}

    fixed_count = 0
    new_activities = []

    for activity in activities:
        # Skip non-dict entries
        if not isinstance(activity, dict):
            new_activities.append(activity)
            continue

        if is_malformed_error_correction(activity):
            print(f"  FIXING: {activity.get('title', 'Untitled')} (error-correction → fill-in)")
            new_activities.append(convert_to_fill_in(activity))
            fixed_count += 1
        else:
            new_activities.append(activity)

    if fixed_count > 0 and not dry_run:
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(new_activities, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return {'fixed': fixed_count, 'file': str(filepath)}

def main():
    dry_run = '--dry-run' in sys.argv

    # Find all activity YAML files
    base_path = Path('curriculum/l2-uk-en')
    levels = ['a2', 'b1', 'b2']

    total_fixed = 0

    for level in levels:
        activities_dir = base_path / level / 'activities'
        if not activities_dir.exists():
            continue

        print(f"\n=== {level.upper()} ===")

        for yaml_file in sorted(activities_dir.glob('*.yaml')):
            result = fix_yaml_file(yaml_file, dry_run=dry_run)
            if result['fixed'] > 0:
                total_fixed += result['fixed']
                print(f"  Fixed {result['fixed']} activities in {yaml_file.name}")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Total fixed: {total_fixed} activities")

    if dry_run:
        print("\nRun without --dry-run to apply fixes.")

if __name__ == '__main__':
    main()
