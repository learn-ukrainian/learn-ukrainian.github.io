#!/usr/bin/env python3
"""
Remove [!resources] sections from all markdown files.
Resources are now injected during generation from external_resources.yaml.

Usage:
    # Dry run (preview changes)
    .venv/bin/python scripts/remove_resources_from_markdown.py \
        --curriculum curriculum/l2-uk-en/ \
        --dry-run

    # Execute (write changes)
    .venv/bin/python scripts/remove_resources_from_markdown.py \
        --curriculum curriculum/l2-uk-en/
"""

import re
import argparse
import shutil
from pathlib import Path


def remove_resources_block(content: str) -> str:
    """Remove [!resources] callout block from markdown content."""
    # Pattern: > [!resources] ... until next non-quoted line or end
    # This matches the entire block starting with > [!resources] and continuing
    # through all subsequent > lines
    pattern = r'^>[ ]*\[!resources\].*?(?:\n>.*?)*(?=\n(?!>)|\Z)'
    cleaned = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)

    # Clean up extra blank lines (reduce 3+ consecutive newlines to 2)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip() + '\n'


def process_module(file_path: Path, dry_run: bool = False) -> bool:
    """
    Process a single module file.

    Args:
        file_path: Path to markdown file
        dry_run: If True, only preview changes without writing

    Returns:
        True if file was modified (or would be in dry run), False otherwise
    """
    content = file_path.read_text(encoding='utf-8')

    # Check if has resources block
    if '[!resources]' not in content:
        return False

    # Remove resources block
    cleaned = remove_resources_block(content)

    if dry_run:
        print(f"Would update: {file_path}")
        return True

    # Backup original
    backup_path = file_path.with_suffix('.md.bak')
    shutil.copy2(file_path, backup_path)

    # Write cleaned content
    file_path.write_text(cleaned, encoding='utf-8')
    print(f"✅ Cleaned: {file_path}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Remove [!resources] sections from markdown files'
    )
    parser.add_argument(
        '--curriculum',
        type=Path,
        required=True,
        help='Curriculum directory (e.g., curriculum/l2-uk-en/)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without writing files'
    )
    args = parser.parse_args()

    curriculum_path = args.curriculum
    if not curriculum_path.exists():
        print(f"❌ Error: Curriculum directory not found: {curriculum_path}")
        return 1

    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']

    total = 0
    updated = 0

    print(f"\n{'🔍 DRY RUN MODE - No files will be modified' if args.dry_run else '🗑️  REMOVING [!resources] from markdown files'}")
    print(f"📁 Curriculum: {curriculum_path}\n")

    for level in levels:
        level_path = curriculum_path / level
        if not level_path.exists():
            continue

        level_files = 0
        level_updated = 0

        for md_file in sorted(level_path.glob('*.md')):
            if md_file.name.startswith('.'):
                continue

            total += 1
            level_files += 1

            if process_module(md_file, dry_run=args.dry_run):
                updated += 1
                level_updated += 1

        if level_files > 0:
            print(f"  📂 {level.upper()}: {level_updated}/{level_files} files with resources")

    print(f"\n{'=' * 60}")
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Processed {total} files, {'would update' if args.dry_run else 'updated'} {updated}")
    print(f"{'=' * 60}\n")

    if not args.dry_run and updated > 0:
        print(f"💾 Backups created: *.md.bak files")
        print(f"\nTo verify removal:")
        print(f"  rg \"\\[!resources\\]\" {curriculum_path}")
        print(f"\nTo restore from backups:")
        print(f"  find {curriculum_path} -name '*.md.bak' -exec sh -c 'mv \"$1\" \"${{1%.bak}}\"' _ {{}} \\;\n")

    return 0


if __name__ == '__main__':
    exit(main())
