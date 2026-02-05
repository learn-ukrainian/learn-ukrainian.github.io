#!/usr/bin/env python3
"""
Safe Dead Code Remover

Removes scripts identified as safe by analyze_dead_code.py
Supports dry-run mode and incremental removal by risk level.
"""

import json
import subprocess
import sys
from pathlib import Path
import argparse

def load_report():
    """Load the dead code analysis report"""
    report_path = '/tmp/dead_code_report.json'
    try:
        with open(report_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Report not found at {report_path}")
        print("Run: python3 scripts/analyze_dead_code.py first")
        sys.exit(1)

def remove_scripts(scripts, dry_run=True, project_root=None):
    """Remove specified scripts"""
    if project_root is None:
        project_root = Path(__file__).parent.parent

    removed = []
    failed = []

    for script_info in scripts:
        script_path = project_root / script_info['path']

        if not script_path.exists():
            print(f"⚠️  Already removed: {script_info['name']}")
            continue

        if dry_run:
            print(f"[DRY RUN] Would remove: {script_info['name']}")
            print(f"          Path: {script_info['path']}")
            print(f"          Category: {script_info['category']}")
            print(f"          Last modified: {script_info['days_since_modified']} days ago")
            print()
            removed.append(script_info['name'])
        else:
            try:
                script_path.unlink()
                print(f"✓ Removed: {script_info['name']}")
                removed.append(script_info['name'])
            except Exception as e:
                print(f"✗ Failed to remove {script_info['name']}: {e}")
                failed.append(script_info['name'])

    return removed, failed

def main():
    parser = argparse.ArgumentParser(description='Remove dead code safely')
    parser.add_argument('--low-risk', action='store_true',
                        help='Remove LOW risk scripts (safe, no references)')
    parser.add_argument('--medium-risk', action='store_true',
                        help='Remove MEDIUM risk scripts (one-time scripts >60 days)')
    parser.add_argument('--one-time-only', action='store_true',
                        help='Remove only one_time_* scripts from medium risk')
    parser.add_argument('--execute', action='store_true',
                        help='Actually remove files (default is dry-run)')
    parser.add_argument('--min-days', type=int, default=60,
                        help='Minimum days since modification for medium risk (default: 60)')

    args = parser.parse_args()

    if not (args.low_risk or args.medium_risk or args.one_time_only):
        parser.print_help()
        print("\nExample usage:")
        print("  # Dry run (safe)")
        print("  python3 scripts/remove_dead_code.py --low-risk")
        print()
        print("  # Actually remove low risk scripts")
        print("  python3 scripts/remove_dead_code.py --low-risk --execute")
        print()
        print("  # Remove one-time scripts >60 days old (dry run)")
        print("  python3 scripts/remove_dead_code.py --one-time-only")
        sys.exit(0)

    report = load_report()

    mode = "EXECUTE" if args.execute else "DRY RUN"
    print(f"\n{'=' * 70}")
    print(f"DEAD CODE REMOVAL - {mode}")
    print('=' * 70)
    print()

    to_remove = []

    if args.low_risk:
        to_remove.extend(report['low_risk_candidates'])
        print(f"✓ Including LOW risk scripts: {len(report['low_risk_candidates'])}")

    if args.medium_risk:
        to_remove.extend(report['medium_risk_candidates'])
        print(f"✓ Including MEDIUM risk scripts: {len(report['medium_risk_candidates'])}")

    if args.one_time_only:
        one_time_scripts = [
            s for s in report['medium_risk_candidates']
            if s['category'].startswith('one_time_') and
               (s['days_since_modified'] or 0) >= args.min_days
        ]
        to_remove.extend(one_time_scripts)
        print(f"✓ Including one-time scripts >{args.min_days} days: {len(one_time_scripts)}")

    if not to_remove:
        print("No scripts to remove.")
        sys.exit(0)

    print(f"\nTotal scripts to remove: {len(to_remove)}")
    print()

    removed, failed = remove_scripts(to_remove, dry_run=not args.execute)

    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print('=' * 70)
    print(f"Scripts removed: {len(removed)}")
    if failed:
        print(f"Failed: {len(failed)}")
        for name in failed:
            print(f"  - {name}")

    if not args.execute:
        print(f"\n{'=' * 70}")
        print("This was a DRY RUN - no files were actually removed.")
        print("To execute removal, add --execute flag")
        print('=' * 70)
    else:
        print(f"\n{'=' * 70}")
        print("Files have been removed. Recommend:")
        print("  1. Run tests to ensure nothing broke")
        print("  2. git add -A && git commit -m 'chore: remove dead code'")
        print('=' * 70)

if __name__ == '__main__':
    main()
