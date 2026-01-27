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
    from audit.checks.yaml_schema_validation import fix_yaml_file, remove_forbidden_activities
    from audit.core import detect_level, detect_focus, load_yaml_meta
    import re

    md_path = Path(file_path)
    slug = md_path.stem
    activities_dir = md_path.parent / "activities"
    yaml_path = activities_dir / f"{slug}.yaml"

    if not yaml_path.exists():
        return 0, [f"  ℹ️ No YAML file found: {yaml_path.name}"]

    total_fixes = 0
    all_messages = []

    # Run standard schema fixes first
    num_fixes, messages = fix_yaml_file(yaml_path, dry_run=False)
    total_fixes += num_fixes
    all_messages.extend(messages)

    # Detect level and focus for forbidden activity removal
    meta_data = load_yaml_meta(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Reconstruct frontmatter string for detection
    if meta_data:
        import yaml as yaml_lib
        frontmatter_str = yaml_lib.dump(meta_data, sort_keys=False, allow_unicode=True)
    else:
        frontmatter_str = content.split('---')[1] if '---' in content else ''

    level_code, module_num = detect_level(file_path, frontmatter_str)
    module_focus = detect_focus(frontmatter_str, level_code, module_num, meta_data.get('title') if meta_data else "", file_path)

    # Remove forbidden activities (for seminar tracks)
    num_removed, remove_messages = remove_forbidden_activities(yaml_path, level_code, module_focus, dry_run=False)
    total_fixes += num_removed
    all_messages.extend(remove_messages)

    return total_fixes, all_messages


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
