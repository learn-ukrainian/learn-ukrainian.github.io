#!/usr/bin/env python3
"""
Convert fill-in activities to cloze format.

Fill-in activities with 8+ items and related sentences are good candidates
for conversion to cloze (passage-based) format.

Issue: #372 - Expand cloze coverage to 10%+
"""

import yaml
import re
from pathlib import Path
import sys
import argparse

def is_good_cloze_candidate(activity: dict) -> bool:
    """Check if a fill-in activity is a good candidate for cloze conversion.

    IMPORTANT: Only converts fill-in activities. Never overwrites existing cloze.
    """
    # Only convert fill-in activities - NEVER touch existing cloze
    if activity.get('type') != 'fill-in':
        return False

    items = activity.get('items', [])

    # Need at least 6 items to make a meaningful passage
    if len(items) < 6:
        return False

    # Check if items have similar structure (related sentences)
    # Skip transformation exercises (contain →)
    for item in items:
        sentence = item.get('sentence', '')
        if '→' in sentence:
            return False

    # Skip single-word/very short sentences
    avg_words = sum(len(item.get('sentence', '').split()) for item in items) / len(items)
    if avg_words < 4:
        return False

    return True

def convert_to_cloze(activity: dict) -> dict:
    """Convert a fill-in activity to cloze format."""
    items = activity.get('items', [])

    # Build passage from items
    passage_parts = []
    for item in items:
        sentence = item.get('sentence', '')
        answer = item.get('answer', '')
        options = item.get('options', [])

        # Build blank with options (answer first, then other options)
        # Convert all to strings
        answer = str(answer) if answer else ''
        options = [str(opt) for opt in options if opt]

        if answer in options:
            # Put answer first
            other_options = [opt for opt in options if opt != answer]
            blank_options = [answer] + other_options[:3]  # Max 4 options
        else:
            blank_options = [answer] + options[:3]

        blank = '{' + '|'.join(blank_options) + '}'

        # Replace ___ with blank
        if '___' in sentence:
            new_sentence = sentence.replace('___', blank)
        else:
            # If no blank marker, append blank at end
            new_sentence = f"{sentence} {blank}"

        passage_parts.append(new_sentence)

    # Join sentences into passage with line breaks every 3 sentences
    passage_lines = []
    for i in range(0, len(passage_parts), 3):
        chunk = passage_parts[i:i+3]
        passage_lines.append(' '.join(chunk))

    passage = '\n\n'.join(passage_lines)

    return {
        'type': 'cloze',
        'title': activity.get('title', 'Complete the Passage'),
        'passage': passage
    }

def process_yaml_file(filepath: Path, dry_run: bool = False, max_per_file: int = 1, only_if_no_cloze: bool = False) -> dict:
    """Process a YAML file and convert suitable fill-in to cloze."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    activities = yaml.safe_load(content)
    if not activities or not isinstance(activities, list):
        return {'converted': 0, 'file': str(filepath)}

    # Check if file already has cloze activities
    if only_if_no_cloze:
        has_cloze = any(
            isinstance(a, dict) and a.get('type') == 'cloze'
            for a in activities
        )
        if has_cloze:
            return {'converted': 0, 'file': str(filepath)}

    converted_count = 0
    new_activities = []

    for activity in activities:
        if not isinstance(activity, dict):
            new_activities.append(activity)
            continue

        # Only convert limited number per file to maintain variety
        if converted_count < max_per_file and is_good_cloze_candidate(activity):
            print(f"  CONVERTING: {activity.get('title', 'Untitled')} ({len(activity.get('items', []))} items)")
            new_activities.append(convert_to_cloze(activity))
            converted_count += 1
        else:
            new_activities.append(activity)

    if converted_count > 0 and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(new_activities, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return {'converted': converted_count, 'file': str(filepath)}

def find_candidates(base_path: Path, levels: list) -> list:
    """Find all files with potential conversion candidates."""
    candidates = []

    for level in levels:
        activities_dir = base_path / level / 'activities'
        if not activities_dir.exists():
            continue

        for yaml_file in sorted(activities_dir.glob('*.yaml')):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                activities = yaml.safe_load(f)

            if not activities or not isinstance(activities, list):
                continue

            for i, activity in enumerate(activities):
                if isinstance(activity, dict) and is_good_cloze_candidate(activity):
                    candidates.append({
                        'file': str(yaml_file),
                        'index': i,
                        'title': activity.get('title', 'Untitled'),
                        'items': len(activity.get('items', []))
                    })

    return candidates

def main():
    parser = argparse.ArgumentParser(description='Convert fill-in activities to cloze')
    parser.add_argument('--dry-run', action='store_true', help='Show candidates without converting')
    parser.add_argument('--list', action='store_true', help='List candidates only')
    parser.add_argument('--max-per-file', type=int, default=1, help='Max conversions per file')
    parser.add_argument('--level', choices=['a2', 'b1', 'b2'], help='Specific level to process')
    parser.add_argument('--only-if-no-cloze', action='store_true', help='Only convert in files without existing cloze')
    args = parser.parse_args()

    base_path = Path('curriculum/l2-uk-en')
    levels = [args.level] if args.level else ['a2', 'b1', 'b2']

    if args.list:
        print("=== CLOZE CONVERSION CANDIDATES ===\n")
        candidates = find_candidates(base_path, levels)
        for c in candidates:
            print(f"  {c['file']}")
            print(f"    Activity: {c['title']} ({c['items']} items)")
        print(f"\nTotal candidates: {len(candidates)}")
        return

    total_converted = 0

    for level in levels:
        activities_dir = base_path / level / 'activities'
        if not activities_dir.exists():
            continue

        print(f"\n=== {level.upper()} ===")

        for yaml_file in sorted(activities_dir.glob('*.yaml')):
            result = process_yaml_file(
                yaml_file,
                dry_run=args.dry_run,
                max_per_file=args.max_per_file,
                only_if_no_cloze=args.only_if_no_cloze
            )
            if result['converted'] > 0:
                total_converted += result['converted']
                print(f"  Converted {result['converted']} in {yaml_file.name}")

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Total converted: {total_converted}")

if __name__ == '__main__':
    main()
