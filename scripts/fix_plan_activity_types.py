#!/usr/bin/env python3
"""Fix forbidden activity types in plan files across all levels.

Reads each plan's activity_hints, checks the level's forbidden types,
and replaces them with allowed alternatives. Focus field is adjusted
to match the new type.

Usage:
    .venv/bin/python scripts/fix_plan_activity_types.py          # Dry run (default)
    .venv/bin/python scripts/fix_plan_activity_types.py --fix     # Apply fixes
    .venv/bin/python scripts/fix_plan_activity_types.py --level b1  # Fix only B1
"""

import argparse
import sys
from pathlib import Path

import yaml

# ── Forbidden types per level/track (from config.py + quick-refs) ────────────

FORBIDDEN_TYPES = {
    # Core tracks
    'a1': {'cloze', 'error-correction', 'mark-the-words', 'select', 'translate',
            'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent',
            'group-sort', 'unjumble', 'anagram'},
    'a2': {'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent',
            'anagram'},
    'b1': {'cloze', 'group-sort', 'unjumble', 'anagram',
            'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent'},
    'b2': {'anagram'},
    'b2-pro': {'anagram'},
    'c1': {'anagram'},
    'c1-pro': {'anagram'},
    'c2': {'anagram'},
    # Seminar tracks — most core types forbidden
    'b2-hist': {'quiz', 'fill-in', 'cloze', 'match-up', 'error-correction',
                'unjumble', 'mark-the-words', 'group-sort', 'select', 'translate', 'anagram'},
    'c1-bio': {'match-up', 'fill-in', 'cloze', 'group-sort', 'unjumble', 'anagram', 'mark-the-words'},
    'c1-hist': {'match-up', 'fill-in', 'cloze', 'group-sort', 'unjumble', 'anagram', 'mark-the-words'},
    'lit': {'quiz', 'match-up', 'fill-in', 'unjumble', 'anagram', 'cloze', 'mark-the-words'},
    'oes': {'quiz', 'match-up', 'fill-in', 'unjumble', 'anagram', 'cloze',
            'mark-the-words', 'group-sort', 'select', 'translate'},
    'ruth': {'quiz', 'match-up', 'fill-in', 'unjumble', 'anagram', 'cloze',
             'mark-the-words', 'group-sort', 'select', 'translate'},
}

# Inherit lit config for lit sub-genres
for sub in ('lit-essay', 'lit-hist-fic', 'lit-fantastika', 'lit-war', 'lit-humor', 'lit-juvenile'):
    FORBIDDEN_TYPES[sub] = FORBIDDEN_TYPES['lit']

# ── Replacement mapping per level ────────────────────────────────────────────
# Maps (level, forbidden_type) -> replacement_type
# Falls back to level-generic mapping, then to None (delete)

REPLACEMENTS = {
    # A1: very restricted
    'a1': {
        'cloze': 'fill-in',
        'error-correction': 'quiz',
        'mark-the-words': 'match-up',
        'select': 'quiz',
        'translate': 'fill-in',
        'essay-response': None,  # delete — way too advanced
        'critical-analysis': None,
        'comparative-study': None,
        'authorial-intent': None,
        'group-sort': 'match-up',
        'unjumble': 'quiz',
        'anagram': 'quiz',
    },
    # A2
    'a2': {
        'essay-response': None,
        'critical-analysis': None,
        'comparative-study': None,
        'authorial-intent': None,
        'anagram': 'mark-the-words',
    },
    # B1: the big one
    'b1': {
        'cloze': 'fill-in',
        'group-sort': 'true-false',
        'unjumble': 'error-correction',
        'anagram': 'mark-the-words',
        'essay-response': None,
        'critical-analysis': None,
        'comparative-study': None,
        'authorial-intent': None,
    },
    # B2+: minimal
    'b2': {'anagram': 'mark-the-words'},
    'b2-pro': {'anagram': 'mark-the-words'},
    'c1': {'anagram': 'mark-the-words'},
    'c1-pro': {'anagram': 'mark-the-words'},
    'c2': {'anagram': 'mark-the-words'},
    # Seminar tracks: replace with seminar-appropriate types
    'b2-hist': {
        'quiz': 'critical-analysis', 'fill-in': 'essay-response',
        'cloze': 'essay-response', 'match-up': 'comparative-study',
        'error-correction': 'essay-response', 'unjumble': 'essay-response',
        'mark-the-words': 'reading', 'group-sort': 'critical-analysis',
        'select': 'critical-analysis', 'translate': 'essay-response',
        'anagram': 'reading',
    },
    'c1-bio': {
        'match-up': 'comparative-study', 'fill-in': 'essay-response',
        'cloze': 'essay-response', 'group-sort': 'critical-analysis',
        'unjumble': 'essay-response', 'anagram': 'reading',
        'mark-the-words': 'reading',
    },
    'c1-hist': {
        'match-up': 'comparative-study', 'fill-in': 'essay-response',
        'cloze': 'essay-response', 'group-sort': 'critical-analysis',
        'unjumble': 'essay-response', 'anagram': 'reading',
        'mark-the-words': 'reading',
    },
    'lit': {
        'quiz': 'critical-analysis', 'match-up': 'comparative-study',
        'fill-in': 'essay-response', 'unjumble': 'essay-response',
        'anagram': 'reading', 'cloze': 'essay-response',
        'mark-the-words': 'reading',
    },
    'oes': {
        'quiz': 'grammar-identify', 'match-up': 'etymology-trace',
        'fill-in': 'transcription', 'unjumble': 'grammar-identify',
        'anagram': 'etymology-trace', 'cloze': 'transcription',
        'mark-the-words': 'grammar-identify', 'group-sort': 'grammar-identify',
        'select': 'grammar-identify', 'translate': 'transcription',
    },
    'ruth': {
        'quiz': 'grammar-identify', 'match-up': 'etymology-trace',
        'fill-in': 'transcription', 'unjumble': 'grammar-identify',
        'anagram': 'etymology-trace', 'cloze': 'transcription',
        'mark-the-words': 'grammar-identify', 'group-sort': 'grammar-identify',
        'select': 'grammar-identify', 'translate': 'transcription',
    },
}

# Inherit lit replacements for sub-genres
for sub in ('lit-essay', 'lit-hist-fic', 'lit-fantastika', 'lit-war', 'lit-humor', 'lit-juvenile'):
    REPLACEMENTS[sub] = REPLACEMENTS['lit']


def detect_level(plan_dir_name: str) -> str:
    """Detect level from plan directory name."""
    return plan_dir_name.lower()


def fix_plan(plan_path: Path, level: str, dry_run: bool = True) -> list[str]:
    """Fix forbidden activity types in a single plan file.

    Returns list of change descriptions.
    """
    changes = []
    forbidden = FORBIDDEN_TYPES.get(level, set())
    replacements = REPLACEMENTS.get(level, {})

    if not forbidden:
        return changes

    with open(plan_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not data or 'activity_hints' not in data:
        return changes

    hints = data['activity_hints']
    if not isinstance(hints, list):
        return changes

    new_hints = []
    for hint in hints:
        act_type = hint.get('type', '')
        if act_type in forbidden:
            replacement = replacements.get(act_type)
            if replacement is None:
                changes.append(f"  DELETE: {act_type} (no valid replacement at {level})")
                continue  # skip this hint entirely
            else:
                old_type = act_type
                hint['type'] = replacement
                # Keep original focus text — it's descriptive enough for Gemini
                changes.append(f"  {old_type} → {replacement}")
        new_hints.append(hint)

    if changes:
        data['activity_hints'] = new_hints
        if not dry_run:
            with open(plan_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)

    return changes


def main():
    parser = argparse.ArgumentParser(description='Fix forbidden activity types in plan files')
    parser.add_argument('--fix', action='store_true', help='Apply fixes (default: dry run)')
    parser.add_argument('--level', type=str, help='Only fix this level (e.g., b1, a1, c1-bio)')
    args = parser.parse_args()

    plans_root = Path('curriculum/l2-uk-en/plans')
    if not plans_root.exists():
        print(f"ERROR: {plans_root} not found")
        sys.exit(1)

    total_files = 0
    total_changes = 0
    total_fixed_files = 0

    mode = "FIX" if args.fix else "DRY RUN"
    print(f"\n{'='*60}")
    print(f"  Plan Activity Type Fixer [{mode}]")
    print(f"{'='*60}\n")

    for level_dir in sorted(plans_root.iterdir()):
        if not level_dir.is_dir():
            continue

        level = detect_level(level_dir.name)
        if args.level and level != args.level.lower():
            continue

        if level not in FORBIDDEN_TYPES:
            continue

        plan_files = sorted(level_dir.glob('*.yaml'))
        level_changes = 0

        for plan_file in plan_files:
            total_files += 1
            changes = fix_plan(plan_file, level, dry_run=not args.fix)
            if changes:
                total_fixed_files += 1
                level_changes += len(changes)
                print(f"  {plan_file.relative_to(plans_root)}:")
                for c in changes:
                    print(f"    {c}")

        if level_changes:
            total_changes += level_changes
            print(f"  [{level.upper()}] {level_changes} changes in {len(plan_files)} files\n")

    print(f"\n{'='*60}")
    print(f"  Summary: {total_changes} changes across {total_fixed_files}/{total_files} files")
    if not args.fix:
        print(f"  Run with --fix to apply changes")
    else:
        print(f"  All changes applied!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
