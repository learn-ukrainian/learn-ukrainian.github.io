#!/usr/bin/env python3
"""
Module Audit CLI

Audits curriculum module files for quality, grammar constraints,
activity requirements, and pedagogical standards.

Usage:
    python3 scripts/audit_module.py <file.md> [file2.md ...]
Usage:
    python3 scripts/audit_module.py <file.md> [file2.md ...]
"""

import sys
import argparse
from audit import audit_module




def auto_fix_yaml_violations(file_path: str) -> tuple[int, list[str]]:
    """
    Automatically fix YAML schema violations in a module's activity file.

    Returns (num_fixes, list_of_messages).
    """
    from pathlib import Path
    from audit.checks.yaml_schema_validation import fix_yaml_file

    md_path = Path(file_path)
    slug = md_path.stem
    activities_dir = md_path.parent / "activities"
    yaml_path = activities_dir / f"{slug}.yaml"

    if not yaml_path.exists():
        return 0, [f"  ℹ️ No YAML file found: {yaml_path.name}"]

    num_fixes, messages = fix_yaml_file(yaml_path, dry_run=False)
    return num_fixes, messages


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Audit curriculum module files for quality and standards."
    )
    parser.add_argument("files", nargs="*", help="Module file(s) to audit")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix YAML schema violations"
    )

    args = parser.parse_args()

    if not args.files:
        print("Usage: python3 scripts/audit_module.py <file.md> [file2.md ...] [--fix]")
        sys.exit(1)

    any_failure = False
    for file_path in args.files:
        print(f"\n{'='*40}")

        # Auto-fix YAML violations if requested
        if args.fix:
            print("\n🔧 AUTO-FIX MODE: Attempting to fix YAML schema violations...")
            num_fixes, messages = auto_fix_yaml_violations(file_path)
            if messages:
                for msg in messages:
                    print(msg)
            if num_fixes > 0:
                print(f"\n✅ Applied {num_fixes} fixes. Re-running audit to verify...\n")

        # Run standard audit
        success = audit_module(file_path)


        if not success:
            any_failure = True

    if any_failure:
        sys.exit(1)
    else:
        sys.exit(0)
