#!/usr/bin/env python3
"""
YAML Activity Validator CLI

Validates YAML activity files against JSON schemas and business logic rules.

Usage:
    python scripts/validate_yaml.py <yaml_file> [--level LEVEL] [--verbose]
    python scripts/validate_yaml.py curriculum/l2-uk-en/b1/01-dative.activities.yaml
    python scripts/validate_yaml.py --dir curriculum/l2-uk-en/b1/
    python scripts/validate_yaml.py --all

Options:
    --level LEVEL   Override auto-detected level (a1, a2, b1, b2, c1, c2)
    --verbose       Show detailed output including MDX preview
    --dir PATH      Validate all .activities.yaml files in directory
    --all           Validate all .activities.yaml files in curriculum
    --fix           Attempt to auto-fix common issues (not implemented yet)
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from yaml_activities import ActivityParser


def detect_level(file_path: Path) -> str:
    """Detect CEFR level from file path."""
    path_str = str(file_path).lower()
    for level in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
        if f'/{level}/' in path_str or path_str.startswith(f'{level}/'):
            return level
    return 'b1'  # Default to B1


def format_error(error) -> str:
    """Format a validation error for display."""
    parts = [f"  \033[31mERROR\033[0m: {error.message}"]
    if error.path and error.path != '/':
        parts[0] = f"  \033[31mERROR\033[0m [{error.path}]: {error.message}"
    if error.activity_type:
        parts.append(f"    Activity type: {error.activity_type}")
    if error.activity_title:
        parts.append(f"    Activity title: {error.activity_title}")
    return '\n'.join(parts)


def format_warning(warning) -> str:
    """Format a validation warning for display."""
    parts = [f"  \033[33mWARN\033[0m: {warning.message}"]
    if warning.path and warning.path != '/':
        parts[0] = f"  \033[33mWARN\033[0m [{warning.path}]: {warning.message}"
    return '\n'.join(parts)


def validate_file(yaml_path: Path, level: str = None, verbose: bool = False) -> bool:
    """
    Validate a single YAML activity file.

    Returns True if valid, False if errors found.
    """
    if not yaml_path.exists():
        print(f"\033[31mERROR\033[0m: File not found: {yaml_path}")
        return False

    if level is None:
        level = detect_level(yaml_path)

    parser = ActivityParser()

    # Parse YAML
    try:
        activities = parser.parse(yaml_path)
    except Exception as e:
        print(f"\n\033[31m✗\033[0m {yaml_path}")
        print(f"  \033[31mPARSE ERROR\033[0m: {e}")
        return False

    # Validate
    result = parser.validate(activities, level=level)

    # Display results
    if result.ok:
        print(f"\033[32m✓\033[0m {yaml_path} ({len(activities)} activities, level={level})")

        if result.warnings:
            for warning in result.warnings:
                print(format_warning(warning))

        if verbose:
            print(f"\n  Activities:")
            for i, act in enumerate(activities, 1):
                item_count = len(getattr(act, 'items', getattr(act, 'pairs', getattr(act, 'groups', getattr(act, 'blanks', getattr(act, 'lines', []))))))
                print(f"    {i}. {act.type}: {act.title} ({item_count} items)")

            # Show MDX preview
            mdx = parser.to_mdx(activities)
            print(f"\n  MDX output: {len(mdx)} chars")
            print(f"  First 300 chars:\n    {mdx[:300].replace(chr(10), chr(10) + '    ')}...")

        return True
    else:
        print(f"\n\033[31m✗\033[0m {yaml_path} ({len(activities)} activities, level={level})")

        for error in result.errors:
            print(format_error(error))

        for warning in result.warnings:
            print(format_warning(warning))

        return False


def validate_directory(dir_path: Path, level: str = None, verbose: bool = False) -> tuple[int, int]:
    """
    Validate all .activities.yaml files in a directory.

    Returns (passed_count, failed_count).
    """
    yaml_files = sorted(dir_path.glob('*.activities.yaml'))

    if not yaml_files:
        print(f"No .activities.yaml files found in {dir_path}")
        return 0, 0

    passed = 0
    failed = 0

    for yaml_file in yaml_files:
        if validate_file(yaml_file, level=level, verbose=verbose):
            passed += 1
        else:
            failed += 1

    return passed, failed


def validate_all(base_path: Path = None, verbose: bool = False) -> tuple[int, int]:
    """
    Validate all .activities.yaml files in the curriculum.

    Returns (passed_count, failed_count).
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent / 'curriculum' / 'l2-uk-en'

    total_passed = 0
    total_failed = 0

    for level in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
        level_dir = base_path / level
        if level_dir.exists():
            print(f"\n\033[1m{level.upper()}\033[0m")
            passed, failed = validate_directory(level_dir, level=level, verbose=verbose)
            total_passed += passed
            total_failed += failed

    return total_passed, total_failed


def main():
    parser = argparse.ArgumentParser(
        description='Validate YAML activity files against schemas and business logic.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s module.activities.yaml           Validate single file
  %(prog)s --dir curriculum/l2-uk-en/b1/    Validate all in directory
  %(prog)s --all                            Validate entire curriculum
  %(prog)s module.yaml --level a2           Override level detection
  %(prog)s module.yaml --verbose            Show detailed output
'''
    )

    parser.add_argument(
        'file',
        nargs='?',
        help='YAML activity file to validate'
    )
    parser.add_argument(
        '--level',
        choices=['a1', 'a2', 'b1', 'b2', 'c1', 'c2'],
        help='Override auto-detected CEFR level'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output including MDX preview'
    )
    parser.add_argument(
        '--dir',
        type=Path,
        help='Validate all .activities.yaml files in directory'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Validate all .activities.yaml files in curriculum'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.file and not args.dir and not args.all:
        parser.print_help()
        sys.exit(1)

    # Run validation
    if args.all:
        print("Validating all YAML activity files...")
        passed, failed = validate_all(verbose=args.verbose)
    elif args.dir:
        print(f"Validating YAML files in {args.dir}...")
        passed, failed = validate_directory(args.dir, level=args.level, verbose=args.verbose)
    else:
        yaml_path = Path(args.file)
        if validate_file(yaml_path, level=args.level, verbose=args.verbose):
            sys.exit(0)
        else:
            sys.exit(1)

    # Summary for batch operations
    print(f"\n\033[1mSummary:\033[0m {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
