#!/usr/bin/env python3
"""Batch fix script for issue #369: Fix 323 broken activities.

This script:
1. Auto-deletes 280+ malformed cloze activities (dialogue-reorder disguised as cloze)
2. Auto-fixes 16 cloze syntax errors (removes colons from blanks)
3. Generates rewrite task list for 27 error-correction activities

Usage:
    .venv/bin/python scripts/fix_broken_activities.py --dry-run   # Preview changes
    .venv/bin/python scripts/fix_broken_activities.py             # Apply fixes
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import yaml


def check_malformed_cloze(activity: dict) -> bool:
    """Check if cloze has dialogue lines as blanks."""
    if activity.get('type') != 'cloze':
        return False

    passage = activity.get('passage', '')
    if not passage:
        return False

    # Extract blanks
    blank_pattern = r'\{([^}]+)\}'
    blanks = re.findall(blank_pattern, passage)

    if not blanks:
        return False

    # Check if most blanks are complete dialogue lines
    dialogue_line_count = 0

    for blank in blanks:
        options = [opt.strip() for opt in blank.split('|')]

        for opt in options:
            word_count = len(opt.split())
            has_dialogue_marker = '—' in opt or '«' in opt or '»' in opt
            ends_with_punctuation = opt.endswith(('.', '?', '!'))

            if word_count >= 5 and (has_dialogue_marker or ends_with_punctuation):
                dialogue_line_count += 1
                break

    # If 50%+ blanks are dialogue lines, it's malformed
    return dialogue_line_count >= len(blanks) * 0.5


def check_cloze_syntax_error(activity: dict) -> bool:
    """Check if cloze has colons inside blanks."""
    if activity.get('type') != 'cloze':
        return False

    passage = activity.get('passage', '')
    if not passage:
        return False

    # Extract blanks
    blank_pattern = r'\{([^}]+)\}'
    blanks = re.findall(blank_pattern, passage)

    # Check for colons
    return any(':' in blank for blank in blanks)


def fix_cloze_syntax(activity: dict) -> dict:
    """Remove colons from cloze blanks."""
    if activity.get('type') != 'cloze':
        return activity

    passage = activity.get('passage', '')
    if not passage:
        return activity

    # Find and fix blanks with colons
    def fix_blank(match):
        blank_content = match.group(1)

        # Remove colons and text after them within each option
        # Example: {гукав|гукати: гукав|гукнув} → {гукав|гукати|гукнув}
        options = blank_content.split('|')
        fixed_options = []

        for opt in options:
            # Remove everything after colon
            if ':' in opt:
                opt = opt.split(':')[0].strip()
            fixed_options.append(opt)

        # Remove duplicates while preserving order
        seen = set()
        unique_options = []
        for opt in fixed_options:
            if opt not in seen:
                seen.add(opt)
                unique_options.append(opt)

        return '{' + '|'.join(unique_options) + '}'

    blank_pattern = r'\{([^}]+)\}'
    fixed_passage = re.sub(blank_pattern, fix_blank, passage)

    activity['passage'] = fixed_passage
    return activity


def check_malformed_error_correction(activity: dict) -> bool:
    """Check if error-correction uses placeholder syntax."""
    if activity.get('type') != 'error-correction':
        return False

    items = activity.get('items', [])
    placeholder_count = 0

    for item in items:
        if not isinstance(item, dict):
            continue

        sentence = item.get('sentence', '')
        error = item.get('error', '')

        # Check for placeholder patterns
        if error == '___' or error.strip() == '':
            placeholder_count += 1
        elif '→' in sentence and '___' in sentence:
            placeholder_count += 1
        elif error and error not in sentence:
            placeholder_count += 1

    return placeholder_count > 0


def process_activity_file(
    file_path: Path,
    dry_run: bool = True
) -> Tuple[int, int, int, List[str]]:
    """Process a single activity YAML file.

    Returns:
        (deleted_count, fixed_count, needs_rewrite_count, messages)
    """
    deleted = 0
    fixed = 0
    needs_rewrite = 0
    messages = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            return 0, 0, 0, []

        # Handle both formats: direct list or dict with 'activities' key
        if isinstance(data, list):
            activities = data
        elif isinstance(data, dict) and 'activities' in data:
            activities = data['activities']
        else:
            return 0, 0, 0, []

        if not isinstance(activities, list):
            return 0, 0, 0, []

        new_activities = []
        modified = False

        for activity in activities:
            if not isinstance(activity, dict):
                new_activities.append(activity)
                continue

            title = activity.get('title', 'Untitled')

            # Check 1: Malformed cloze (dialogue lines as blanks) → DELETE
            if check_malformed_cloze(activity):
                deleted += 1
                modified = True
                messages.append(f"  🗑️  Deleted malformed cloze: '{title}'")
                continue  # Don't add to new_activities

            # Check 2: Cloze syntax error → AUTO-FIX
            if check_cloze_syntax_error(activity):
                fixed_activity = fix_cloze_syntax(activity)
                new_activities.append(fixed_activity)
                fixed += 1
                modified = True
                messages.append(f"  🔧 Fixed cloze syntax: '{title}'")
                continue

            # Check 3: Malformed error-correction → FLAG for manual rewrite
            if check_malformed_error_correction(activity):
                needs_rewrite += 1
                messages.append(f"  ⚠️  Needs manual rewrite (error-correction): '{title}'")
                # Keep activity for now, will be manually rewritten later
                new_activities.append(activity)
                continue

            # No issues, keep as-is
            new_activities.append(activity)

        # Write changes if not dry-run and file was modified
        if modified and not dry_run:
            # Write back in same format as input
            if isinstance(data, list):
                output_data = new_activities
            else:
                data['activities'] = new_activities
                output_data = data

            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(output_data, f, allow_unicode=True, sort_keys=False, width=120)

        return deleted, fixed, needs_rewrite, messages

    except Exception as e:
        messages.append(f"  ❌ Error processing {file_path.name}: {e}")
        return 0, 0, 0, messages


def main():
    parser = argparse.ArgumentParser(description='Fix broken activities (issue #369)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    curriculum_dir = base_dir / 'curriculum' / 'l2-uk-en'

    levels = ['a2', 'b1', 'b2']

    total_deleted = 0
    total_fixed = 0
    total_needs_rewrite = 0
    rewrite_list = []

    print(f"\n{'=' * 80}")
    print(f"BATCH FIX SCRIPT - Issue #369: Fix 323 Broken Activities")
    print(f"{'=' * 80}")
    print(f"Mode: {'DRY RUN (preview only)' if args.dry_run else 'LIVE (applying changes)'}")
    print(f"{'=' * 80}\n")

    for level in levels:
        activity_dir = curriculum_dir / level / 'activities'

        if not activity_dir.exists():
            print(f"⚠️  Skipping {level.upper()}: activities directory not found")
            continue

        yaml_files = sorted(activity_dir.glob('*.yaml'))

        if not yaml_files:
            print(f"⚠️  Skipping {level.upper()}: no YAML files found")
            continue

        print(f"\n{'─' * 80}")
        print(f"Processing {level.upper()} ({len(yaml_files)} modules)")
        print(f"{'─' * 80}")

        level_deleted = 0
        level_fixed = 0
        level_needs_rewrite = 0

        for yaml_file in yaml_files:
            deleted, fixed, needs_rewrite, messages = process_activity_file(yaml_file, args.dry_run)

            if deleted > 0 or fixed > 0 or needs_rewrite > 0:
                print(f"\n📄 {yaml_file.name}")
                for msg in messages:
                    print(msg)

                if needs_rewrite > 0:
                    rewrite_list.append(f"{level.upper()} - {yaml_file.stem}")

            level_deleted += deleted
            level_fixed += fixed
            level_needs_rewrite += needs_rewrite

        print(f"\n{level.upper()} Summary:")
        print(f"  🗑️  Deleted: {level_deleted} malformed cloze activities")
        print(f"  🔧 Fixed: {level_fixed} cloze syntax errors")
        print(f"  ⚠️  Needs rewrite: {level_needs_rewrite} error-correction activities")

        total_deleted += level_deleted
        total_fixed += level_fixed
        total_needs_rewrite += level_needs_rewrite

    # Final summary
    print(f"\n{'=' * 80}")
    print(f"TOTAL SUMMARY")
    print(f"{'=' * 80}")
    print(f"  🗑️  Deleted: {total_deleted} malformed cloze activities")
    print(f"  🔧 Fixed: {total_fixed} cloze syntax errors")
    print(f"  ⚠️  Needs manual rewrite: {total_needs_rewrite} error-correction activities")
    print(f"{'=' * 80}\n")

    # Error-correction rewrite list
    if rewrite_list:
        print(f"\n{'=' * 80}")
        print(f"ERROR-CORRECTION ACTIVITIES NEEDING MANUAL REWRITE ({len(rewrite_list)})")
        print(f"{'=' * 80}")
        for module in rewrite_list:
            print(f"  - {module}")
        print(f"{'=' * 80}\n")

    if args.dry_run:
        print("✨ DRY RUN complete. Run without --dry-run to apply changes.\n")
    else:
        print("✅ FIXES APPLIED. Next steps:")
        print("  1. Review changes: git diff curriculum/")
        print("  2. Manually rewrite the error-correction activities listed above")
        print("  3. Run audit on all fixed modules to verify")
        print("  4. Regenerate MDX: npm run generate l2-uk-en a2 && npm run generate l2-uk-en b1 && npm run generate l2-uk-en b2")
        print("")


if __name__ == '__main__':
    main()
