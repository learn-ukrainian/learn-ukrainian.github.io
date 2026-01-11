#!/usr/bin/env python3
"""
Batch fix all YAML schema violations systematically.
Run auto-fix on all modules, report results.
"""

import sys
from pathlib import Path

sys.path.insert(0, 'scripts')
from audit.checks.yaml_schema_validation import validate_activity_yaml_file, fix_yaml_file

def main():
    levels_with_violations = []

    # Scan B1 and B2 (where most violations are)
    for level in ['b1', 'b2']:
        activities_dir = Path(f'curriculum/l2-uk-en/{level}/activities')
        if not activities_dir.exists():
            continue

        yaml_files = sorted(activities_dir.glob('*.yaml'))

        for yaml_path in yaml_files:
            # Check if it has violations
            is_valid, errors = validate_activity_yaml_file(yaml_path)

            if not is_valid:
                # Try to auto-fix
                num_fixes, messages = fix_yaml_file(yaml_path, dry_run=False)

                # Re-validate
                is_valid_after, errors_after = validate_activity_yaml_file(yaml_path)

                status = "✅ FIXED" if is_valid_after else f"⚠️  {len(errors_after)} remaining"

                print(f"{level.upper()} / {yaml_path.stem}: {status}")

                if not is_valid_after:
                    levels_with_violations.append((level, yaml_path.stem, errors_after))

    # Summary
    print(f"\n{'='*60}")
    if levels_with_violations:
        print(f"⚠️  {len(levels_with_violations)} files still have violations:")
        for level, module, errors in levels_with_violations[:10]:  # Show first 10
            print(f"\n{level.upper()} / {module}:")
            for err in errors[:3]:  # Show first 3 errors
                print(f"  - {err}")

        if len(levels_with_violations) > 10:
            print(f"\n... and {len(levels_with_violations) - 10} more")
    else:
        print("✅ All YAML violations auto-fixed!")

if __name__ == '__main__':
    main()
