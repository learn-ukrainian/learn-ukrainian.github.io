#!/usr/bin/env python3
"""
Remove 'id' properties from A1/A2/C1 activity YAML files.

The 'id' property was added on Jan 7, 2026 (commit 331e2847) then removed from
the schema on Jan 10, 2026 (commit d1056994). B1/B2 were cleaned up but A1/A2/C1
were not. This script completes the cleanup.

Expected to remove:
- A1: ~300 id properties (34 files)
- A2: ~585 id properties (57 files)
- C1: ~803 id properties
Total: 1,688 violations
"""

import yaml
from pathlib import Path


def remove_activity_ids(yaml_file):
    """Remove 'id' property from all activities in YAML file."""
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"  ⚠️  Error reading {yaml_file.name}: {e}")
        return 0

    if not data:
        return 0

    # Handle both direct array format and dict with 'activities' key
    if isinstance(data, dict) and 'activities' in data:
        activities = data['activities']
    elif isinstance(data, list):
        activities = data
    else:
        return 0

    count = 0
    for activity in activities:
        if isinstance(activity, dict) and 'id' in activity:
            del activity['id']
            count += 1

    if count > 0:
        try:
            with open(yaml_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            return count
        except Exception as e:
            print(f"  ⚠️  Error writing {yaml_file.name}: {e}")
            return 0

    return count


def main():
    levels = ['a1', 'a2', 'c1']
    grand_total = 0
    files_modified = 0

    for level in levels:
        activity_dir = Path(f'curriculum/l2-uk-en/{level}/activities')

        if not activity_dir.exists():
            print(f"⚠️  Directory not found: {activity_dir}")
            continue

        print(f"\n{'='*60}")
        print(f"Processing {level.upper()}")
        print(f"{'='*60}")

        level_total = 0
        level_files = 0

        for yaml_file in sorted(activity_dir.glob('*.yaml')):
            count = remove_activity_ids(yaml_file)
            if count > 0:
                print(f"  ✅ {yaml_file.name:45} removed {count:3} id properties")
                level_total += count
                level_files += 1

        print(f"\n{level.upper()} Summary: {level_files} files modified, {level_total} id properties removed")
        grand_total += level_total
        files_modified += level_files

    print(f"\n{'='*60}")
    print(f"TOTAL: {files_modified} files modified, {grand_total} id properties removed")
    print(f"{'='*60}")

    # Verification suggestion
    print("\n📋 Next steps:")
    print("1. Verify with audit:")
    print("   .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/01-the-cyrillic-code-i.md")
    print("\n2. Count remaining violations:")
    print("   for level in a1 a2 c1; do echo \"$level: $(rg '^  id: ' curriculum/l2-uk-en/$level/activities/*.yaml 2>/dev/null | wc -l | tr -d ' ')\"; done")
    print("\n3. Commit changes:")
    print("   git add curriculum/l2-uk-en/{a1,a2,c1}/activities/*.yaml")
    print(f"   git commit -m 'fix(a1/a2/c1): Remove {grand_total} invalid id properties from activity YAMLs'")


if __name__ == "__main__":
    main()
