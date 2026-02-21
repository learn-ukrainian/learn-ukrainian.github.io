#!/usr/bin/env python3
"""
Remove [stage: ...] annotations from activity titles in YAML files.

Usage:
    python scripts/remove_stage_annotations.py [file1.yaml file2.yaml ...]

If no files specified, processes all YAML files in curriculum/ that contain stage annotations.
"""

import re
import sys
from pathlib import Path


def remove_stage_annotations(content: str) -> tuple[str, int]:
    """
    Remove [stage: ...] annotations from activity titles.

    Args:
        content: YAML file content

    Returns:
        Tuple of (modified content, count of replacements made)
    """
    # Pattern matches: 'Some Title [stage: something]' or "Some Title [stage: something]"
    # Captures the title part before the stage annotation
    pattern = r"(title:\s*['\"]?)([^'\"\n]+?)(\s*\[stage:\s*[^\]]+\])(['\"]?)"

    def replacement(match):
        prefix = match.group(1)  # "title: '" or "title: "
        title = match.group(2).strip()  # The actual title
        # group(3) is the [stage: ...] part we're removing
        suffix = match.group(4)  # closing quote if present
        return f"{prefix}{title}{suffix}"

    modified, count = re.subn(pattern, replacement, content)
    return modified, count


def process_file(filepath: Path, dry_run: bool = False) -> bool:
    """
    Process a single YAML file to remove stage annotations.

    Args:
        filepath: Path to YAML file
        dry_run: If True, don't write changes

    Returns:
        True if file was modified, False otherwise
    """
    try:
        # Make path absolute if relative
        filepath = filepath.resolve()

        content = filepath.read_text(encoding='utf-8')
        modified, count = remove_stage_annotations(content)

        # Try to get relative path, fallback to str if not possible
        try:
            display_path = filepath.relative_to(Path.cwd())
        except ValueError:
            display_path = filepath

        if count > 0:
            print(f"{'[DRY RUN] ' if dry_run else ''}✓ {display_path}: {count} annotation(s) removed")

            if not dry_run:
                filepath.write_text(modified, encoding='utf-8')

            return True
        else:
            print(f"  {display_path}: no stage annotations found")
            return False

    except Exception as e:
        print(f"✗ Error processing {filepath}: {e}")
        return False


def find_files_with_stage_annotations() -> list[Path]:
    """Find all YAML files containing [stage: ...] annotations."""
    curriculum_dir = Path("curriculum/l2-uk-en")

    if not curriculum_dir.exists():
        print(f"Error: {curriculum_dir} not found")
        return []

    files_with_annotations = []

    for yaml_file in curriculum_dir.rglob("*.yaml"):
        try:
            content = yaml_file.read_text(encoding='utf-8')
            if '[stage:' in content:
                files_with_annotations.append(yaml_file)
        except Exception as e:
            print(f"Warning: Could not read {yaml_file}: {e}")

    return files_with_annotations


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Remove [stage: ...] annotations from activity titles"
    )
    parser.add_argument(
        'files',
        nargs='*',
        help='YAML files to process (if none specified, auto-detects files with annotations)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )

    args = parser.parse_args()

    if args.files:
        files = [Path(f) for f in args.files]
    else:
        print("Searching for files with [stage: ...] annotations...")
        files = find_files_with_stage_annotations()

        if not files:
            print("No files with stage annotations found.")
            return 0

        print(f"\nFound {len(files)} file(s) with stage annotations:\n")

    modified_count = 0

    for filepath in files:
        if process_file(filepath, dry_run=args.dry_run):
            modified_count += 1

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary: {modified_count}/{len(files)} file(s) modified")

    if args.dry_run and modified_count > 0:
        print("\nRun without --dry-run to apply changes.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
