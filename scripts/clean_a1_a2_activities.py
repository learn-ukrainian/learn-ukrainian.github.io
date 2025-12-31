#!/usr/bin/env python3
"""
Clean Activities from A1/A2 Markdown Files

Removes inline activities (## match-up:, ## quiz:, etc.) from markdown files
that already have corresponding YAML activity files.

Usage:
    python scripts/clean_a1_a2_activities.py [level]
    
    level: 'a1', 'a2', or 'all' (default: 'all')
"""

import re
import sys
from pathlib import Path

# Activity type patterns (H2 headers with activity type)
ACTIVITY_TYPES = [
    'match-up',
    'quiz',
    'fill-in',
    'true-false',
    'group-sort',
    'anagram',
    'unjumble',
    'error-correction',
    'cloze',
    'mark-the-words',
    'dialogue-reorder',
    'select',
    'translate',
]

def strip_inline_activities(md_content: str) -> str:
    """
    Remove inline activities from markdown content.
    
    Looks for activity type headers (## match-up:, ## quiz:, etc.)
    and removes everything from the first activity header until:
    - # Summary
    - # Vocabulary
    - # Словник
    - # Підсумок
    """
    # Build pattern for activity headers
    activity_pattern = r'^##\s+(' + '|'.join(ACTIVITY_TYPES) + r'):\s*'
    
    # Find first activity header
    first_activity = re.search(activity_pattern, md_content, re.MULTILINE | re.IGNORECASE)
    if not first_activity:
        return md_content
    
    start_pos = first_activity.start()
    
    # Find where to stop (next major section after activities)
    remaining = md_content[start_pos:]
    
    # Look for Summary, Vocabulary, or end sections
    end_pattern = r'^#\s*(Summary|Vocabulary|Словник|Підсумок)\s*$'
    next_section = re.search(end_pattern, remaining, re.MULTILINE)
    
    if next_section:
        end_pos = start_pos + next_section.start()
        # Keep the next section header, strip the activities
        stripped = md_content[:start_pos].rstrip('\n') + '\n\n' + md_content[start_pos + next_section.start():]
    else:
        # No end section found - strip to end (keep last ---\n for file delimiter)
        stripped = md_content[:start_pos].rstrip('\n') + '\n'
    
    # Clean up extra newlines
    stripped = re.sub(r'\n{3,}', '\n\n', stripped)
    
    return stripped


def clean_module(md_path: Path, dry_run: bool = False) -> bool:
    """
    Clean inline activities from a module if a YAML file exists.
    
    Returns True if changes were made.
    """
    # Check if corresponding YAML exists
    activities_dir = md_path.parent / 'activities'
    yaml_path = activities_dir / (md_path.stem + '.yaml')
    
    if not yaml_path.exists():
        print(f"  ⚠️  No YAML file found for {md_path.name}, skipping")
        return False
    
    with open(md_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    stripped_content = strip_inline_activities(original_content)
    
    if stripped_content == original_content:
        print(f"  ⏭️  No inline activities found in {md_path.name}")
        return False
    
    # Calculate removed lines
    original_lines = len(original_content.splitlines())
    new_lines = len(stripped_content.splitlines())
    removed = original_lines - new_lines
    
    if dry_run:
        print(f"  🔍 Would remove {removed} lines from {md_path.name}")
        return False
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(stripped_content)
    
    print(f"  ✅ Removed {removed} lines of inline activities from {md_path.name}")
    return True


def clean_level(level: str, dry_run: bool = False):
    """Clean all modules in a level."""
    base_dir = Path('curriculum/l2-uk-en') / level
    
    if not base_dir.exists():
        print(f"❌ Directory not found: {base_dir}")
        return
    
    md_files = sorted(base_dir.glob('*.md'))
    
    print(f"\n{'='*60}")
    print(f"Cleaning {level.upper()} modules ({len(md_files)} files)")
    print(f"{'='*60}")
    
    cleaned_count = 0
    for md_file in md_files:
        if clean_module(md_file, dry_run):
            cleaned_count += 1
    
    print(f"\n📊 {level.upper()} Summary: {cleaned_count}/{len(md_files)} files cleaned")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean inline activities from A1/A2 modules')
    parser.add_argument('level', nargs='?', default='all', choices=['a1', 'a2', 'all'],
                        help='Level to clean (a1, a2, or all)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    if args.level == 'all':
        clean_level('a1', args.dry_run)
        clean_level('a2', args.dry_run)
    else:
        clean_level(args.level, args.dry_run)
    
    if args.dry_run:
        print("\n💡 Run without --dry-run to apply changes")


if __name__ == '__main__':
    main()
