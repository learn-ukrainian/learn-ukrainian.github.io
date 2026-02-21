#!/usr/bin/env python3
"""
Batch fix YAML activity files.

Usage:
    .venv/bin/python scripts/fix_yaml_activities.py b1           # Fix all B1 files
    .venv/bin/python scripts/fix_yaml_activities.py b1 --dry-run # Preview only
    .venv/bin/python scripts/fix_yaml_activities.py b1 05        # Fix single module
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.audit.checks.yaml_schema_validation import fix_yaml_file


def main():
    if len(sys.argv) < 2:
        print("Usage: fix_yaml_activities.py LEVEL [MODULE_NUM] [--dry-run]")
        print("       fix_yaml_activities.py b1")
        print("       fix_yaml_activities.py b1 05")
        print("       fix_yaml_activities.py b1 --dry-run")
        sys.exit(1)

    level = sys.argv[1].lower()
    dry_run = '--dry-run' in sys.argv
    module_num = None

    # Check for module number argument
    for arg in sys.argv[2:]:
        if arg.isdigit() or (len(arg) == 2 and arg.isdigit()):
            module_num = arg.zfill(2)  # Pad to 2 digits

    # Find activity directory
    activities_dir = project_root / "curriculum" / "l2-uk-en" / level / "activities"
    if not activities_dir.exists():
        print(f"Error: Activities directory not found: {activities_dir}")
        sys.exit(1)

    # Find files to process
    if module_num:
        yaml_files = list(activities_dir.glob(f"{module_num}-*.yaml"))
    else:
        yaml_files = sorted(activities_dir.glob("*.yaml"))

    if not yaml_files:
        print(f"No YAML files found in {activities_dir}")
        sys.exit(0)

    print(f"{'[DRY RUN] ' if dry_run else ''}Processing {len(yaml_files)} files in {level.upper()}...")
    print()

    total_fixes = 0
    files_modified = 0

    for yaml_path in yaml_files:
        num_fixes, messages = fix_yaml_file(yaml_path, dry_run=dry_run)
        if num_fixes > 0:
            files_modified += 1
            total_fixes += num_fixes
            for msg in messages:
                print(msg)
            print()

    print("=" * 60)
    print(f"Summary: {total_fixes} fixes applied across {files_modified} files")
    if dry_run:
        print("(Dry run - no files were modified)")


if __name__ == "__main__":
    main()
