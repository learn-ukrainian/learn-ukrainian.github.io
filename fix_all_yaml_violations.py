#!/usr/bin/env python3
"""
Systematically fix all YAML schema violations across the curriculum.
"""

import sys
import yaml
from pathlib import Path

sys.path.insert(0, 'scripts')
from audit.checks.yaml_schema_validation import validate_activity_yaml_file, fix_yaml_file

def scan_and_fix_all_levels():
    """Scan all levels and fix YAML violations."""

    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']
    results = {
        'scanned': 0,
        'violations_found': 0,
        'fixed': 0,
        'failed': 0,
        'details': []
    }

    for level in levels:
        level_dir = Path(f'curriculum/l2-uk-en/{level}')
        if not level_dir.exists():
            continue

        activities_dir = level_dir / 'activities'
        if not activities_dir.exists():
            continue

        yaml_files = sorted(activities_dir.glob('*.yaml'))

        for yaml_path in yaml_files:
            results['scanned'] += 1

            # Validate
            is_valid, errors = validate_activity_yaml_file(yaml_path)

            if not is_valid:
                results['violations_found'] += 1
                module_name = yaml_path.stem

                print(f"\n{'='*60}")
                print(f"📁 {level.upper()} / {module_name}")
                print(f"   Violations: {len(errors)}")

                for i, err in enumerate(errors, 1):
                    print(f"   {i}. {err}")

                # Try auto-fix
                num_fixes, fix_messages = fix_yaml_file(yaml_path, dry_run=False)

                if num_fixes > 0:
                    results['fixed'] += 1
                    print(f"   ✅ Auto-fixed: {num_fixes} issues")
                    for msg in fix_messages:
                        print(f"      {msg}")
                else:
                    results['failed'] += 1
                    print(f"   ⚠️  Could not auto-fix")

                results['details'].append({
                    'level': level,
                    'module': module_name,
                    'errors': errors,
                    'fixed': num_fixes > 0
                })

    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Total YAML files scanned: {results['scanned']}")
    print(f"Files with violations: {results['violations_found']}")
    print(f"Files auto-fixed: {results['fixed']}")
    print(f"Files needing manual fix: {results['failed']}")

    return results

if __name__ == '__main__':
    results = scan_and_fix_all_levels()

    if results['failed'] > 0:
        print(f"\n⚠️  {results['failed']} files still have violations after auto-fix")
        print("Manual intervention required for complex issues.")
        sys.exit(1)
    else:
        print("\n✅ All YAML violations resolved!")
        sys.exit(0)
