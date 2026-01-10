#!/usr/bin/env python3
"""
Remove invalid 'id' properties from basic activity types.

The schema only allows 'id' for:
- Cloze blanks (required)
- Advanced C1+ activities: comparative-study, authorial-intent, reading (optional)

All other activity types have additionalProperties: false and should NOT have 'id'.
"""

import yaml
import sys
from pathlib import Path

# Activity types that should NOT have id property
BASIC_ACTIVITIES = [
    'quiz', 'match-up', 'fill-in', 'true-false', 'group-sort',
    'unjumble', 'error-correction', 'cloze', 'mark-the-words',
    'select', 'translate', 'anagram'
]

# Activity types that CAN have id property
ADVANCED_ACTIVITIES = ['comparative-study', 'authorial-intent', 'reading', 'essay-response', 'critical-analysis']

def fix_activity_file(file_path):
    """Remove id properties from basic activities."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not data or 'activities' not in data:
        return 0

    removed_count = 0

    for activity in data['activities']:
        activity_type = activity.get('type')

        # Remove id from basic activities
        if activity_type in BASIC_ACTIVITIES and 'id' in activity:
            del activity['id']
            removed_count += 1
            print(f"  Removed id from {activity_type}: {activity.get('title', 'untitled')}")

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    return removed_count

def main():
    if len(sys.argv) < 2:
        print("Usage: fix_activity_ids.py <activity_file.yaml> [...]")
        print("   OR: fix_activity_ids.py <directory>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob('*.yaml'))
    else:
        print(f"Error: {path} is not a file or directory")
        sys.exit(1)

    total_removed = 0
    files_modified = 0

    for file_path in files:
        print(f"Processing {file_path.name}...")
        removed = fix_activity_file(file_path)
        if removed > 0:
            total_removed += removed
            files_modified += 1

    print(f"\nDone: Removed {total_removed} id properties from {files_modified} files")

if __name__ == '__main__':
    main()
