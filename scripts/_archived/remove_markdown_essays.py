#!/usr/bin/env python3
"""
Remove duplicate essay sections from markdown files.

Essays should live ONLY in activities/*.yaml, not in markdown.
This script removes ## Есе or # Есе sections from markdown files.
"""

import re
import sys
from pathlib import Path


def remove_essay_section(content: str) -> tuple[str, bool]:
    """
    Remove essay section from markdown content.

    Pattern: ## Есе or # Есе section, up to next H1/H2 header or end of file.
    Returns (new_content, was_modified).
    """
    # Pattern to match essay section:
    # - Starts with # Есе or ## Есе (with optional trailing text)
    # - Ends at next # or ## header, or end of file
    # - Include the --- separator before if present

    # First, try to match with preceding ---
    pattern_with_sep = r'\n---\s*\n+#{1,2}\s*Есе.*?(?=\n---\s*\n+#{1,2}\s+[^Е]|\n#{1,2}\s+[^Е]|\Z)'

    match = re.search(pattern_with_sep, content, re.DOTALL)
    if match:
        new_content = content[:match.start()] + content[match.end():]
        return new_content.strip() + '\n', True

    # Try without preceding ---
    pattern_no_sep = r'\n#{1,2}\s*Есе.*?(?=\n---\s*\n+#{1,2}\s+[^Е]|\n#{1,2}\s+[^Е]|\Z)'

    match = re.search(pattern_no_sep, content, re.DOTALL)
    if match:
        new_content = content[:match.start()] + content[match.end():]
        return new_content.strip() + '\n', True

    return content, False


def process_file(filepath: Path, dry_run: bool = False) -> bool:
    """Process a single markdown file. Returns True if modified."""
    content = filepath.read_text(encoding='utf-8')

    new_content, was_modified = remove_essay_section(content)

    if was_modified:
        if dry_run:
            print(f"  [DRY RUN] Would modify: {filepath}")
        else:
            filepath.write_text(new_content, encoding='utf-8')
            print(f"  [MODIFIED] {filepath}")
        return True
    else:
        return False


def process_track(track: str, dry_run: bool = False) -> tuple[int, int]:
    """Process all markdown files in a track. Returns (total, modified)."""
    base_path = Path('curriculum/l2-uk-en') / track

    if not base_path.exists():
        print(f"Track not found: {track}")
        return 0, 0

    md_files = list(base_path.glob('*.md'))
    total = len(md_files)
    modified = 0

    for filepath in sorted(md_files):
        if process_file(filepath, dry_run):
            modified += 1

    return total, modified


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Remove essay sections from markdown files')
    parser.add_argument('tracks', nargs='*', default=['b2-hist', 'c1-bio', 'lit'],
                        help='Tracks to process (default: b2-hist c1-bio lit)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')

    args = parser.parse_args()

    print("=" * 60)
    print("Essay Section Removal Script")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]\n")

    total_all = 0
    modified_all = 0

    for track in args.tracks:
        print(f"\n=== Processing {track.upper()} ===")
        total, modified = process_track(track, args.dry_run)
        total_all += total
        modified_all += modified
        print(f"  {track}: {modified}/{total} files modified")

    print("\n" + "=" * 60)
    print(f"TOTAL: {modified_all}/{total_all} files modified")
    print("=" * 60)

    if args.dry_run:
        print("\nTo apply changes, run without --dry-run")


if __name__ == '__main__':
    main()
