#!/usr/bin/env python3
"""
Fix unjumble activity format in B1/B2 activity YAML files.

Problem: Many unjumble items have only 'answer' field, missing required
'words', 'jumbled', or 'prompt' fields.

Fix: Add 'words' array by splitting the answer sentence into words.

Affects: 169 files (46 B1 + 123 B2)
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml


def split_sentence_into_words(sentence: str) -> List[str]:
    """
    Split a Ukrainian sentence into words, handling punctuation properly.

    Example:
        "Микола Хвильовий застрелився у будинку Слово."
        → ["Микола", "Хвильовий", "застрелився", "у", "будинку", "Слово"]
    """
    # Remove trailing punctuation (., !, ?, ..., etc.)
    sentence = sentence.rstrip('.!?…,;:')

    # Remove quotes at beginning/end
    sentence = sentence.strip('"«»"„"\'')

    # Split by whitespace and filter empty strings
    words = [w.strip() for w in sentence.split() if w.strip()]

    # Remove punctuation from individual words but keep apostrophes
    cleaned_words = []
    for word in words:
        # Keep Ukrainian apostrophes (') in words like "зв'язок"
        # Remove other punctuation except hyphens
        cleaned = word.strip('.,!?;:«»"„"…')
        if cleaned:
            cleaned_words.append(cleaned)

    return cleaned_words


def fix_unjumble_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fix a single unjumble item by adding 'words' array if missing.

    Returns the fixed item with 'words' array added.
    """
    # Check if item needs fixing (has 'answer' but no 'words', 'jumbled', or 'prompt')
    has_answer = 'answer' in item
    missing_required = not any(k in item for k in ['words', 'jumbled', 'prompt'])

    if has_answer and missing_required:
        # Extract words from answer
        answer = item['answer']
        words = split_sentence_into_words(answer)

        # Create new item with 'words' first, then 'answer', then other fields
        fixed_item = {'words': words, 'answer': answer}

        # Copy any other fields
        for key, value in item.items():
            if key not in ['words', 'answer']:
                fixed_item[key] = value

        return fixed_item

    # Item doesn't need fixing, return as-is
    return item


def get_activities(data: Any) -> List[Dict[str, Any]]:
    """Extract activities list from YAML data structure."""
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'activities' in data:
        return data['activities']
    return []


def fix_activity_file(file_path: Path, dry_run: bool = False) -> bool:
    """
    Fix unjumble activities in a single YAML file.

    Returns True if file was modified, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            data = yaml.safe_load(content)

        if not data:
            return False

        activities = get_activities(data)
        if not activities:
            return False

        modified = False

        for activity in activities:
            if activity.get('type') == 'unjumble' and 'items' in activity:
                # Check if any item needs fixing
                items_before = activity['items']
                items_after = [fix_unjumble_item(item) for item in items_before]

                if items_before != items_after:
                    activity['items'] = items_after
                    modified = True

        if modified and not dry_run:
            # Write back with proper YAML formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f,
                         allow_unicode=True,
                         default_flow_style=False,
                         sort_keys=False,
                         width=120)
            print(f"✓ Fixed: {file_path.relative_to(file_path.parents[3])}")
            return True
        elif modified:
            print(f"Would fix: {file_path.relative_to(file_path.parents[3])}")
            return True

        return False

    except Exception as e:
        print(f"✗ Error processing {file_path.name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def main():
    """Fix all B1/B2 activity files with malformed unjumble activities."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Fix unjumble activity format in B1/B2 YAML files (Issue #366)'
    )
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without modifying files')
    parser.add_argument('--level', choices=['b1', 'b2', 'all'], default='all',
                       help='Which level to fix (default: all)')
    parser.add_argument('files', nargs='*',
                       help='Specific files to fix (overrides --level)')

    args = parser.parse_args()

    # Determine which files to process
    if args.files:
        files = [Path(f) for f in args.files]
    else:
        base_dir = Path(__file__).parent.parent / 'curriculum/l2-uk-en'
        files = []

        if args.level in ['b1', 'all']:
            b1_dir = base_dir / 'b1/activities'
            if b1_dir.exists():
                files.extend(sorted(b1_dir.glob('*.yaml')))

        if args.level in ['b2', 'all']:
            b2_dir = base_dir / 'b2/activities'
            if b2_dir.exists():
                files.extend(sorted(b2_dir.glob('*.yaml')))

    if not files:
        print("No files found to process.")
        return 1

    print(f"Processing {len(files)} files...")
    if args.dry_run:
        print("(DRY RUN - no changes will be made)\n")
    else:
        print()

    fixed_count = 0
    for file_path in files:
        if fix_activity_file(file_path, dry_run=args.dry_run):
            fixed_count += 1

    print()
    print(f"Summary: {fixed_count}/{len(files)} files {'would be ' if args.dry_run else ''}modified")

    return 0


if __name__ == '__main__':
    sys.exit(main())
