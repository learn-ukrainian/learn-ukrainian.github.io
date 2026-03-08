#!/usr/bin/env python3
"""
Fix invalid activity types in HIST plans with proper content transformation.

HIST allowed types: reading, essay-response, critical-analysis, comparative-study
HIST required types: reading, essay-response
HIST forbidden types: quiz, fill-in, cloze, match-up, error-correction, unjumble,
                          mark-the-words, group-sort, select, translate, anagram, true-false

Transformation strategy:
- timeline → critical-analysis with focus on analyzing cause-effect/sequence
- true-false → critical-analysis with focus on evaluating historical claims
"""

import argparse
import re
from pathlib import Path

import yaml


FORBIDDEN_TYPES = {
    'quiz', 'fill-in', 'cloze', 'match-up', 'error-correction', 'unjumble',
    'mark-the-words', 'group-sort', 'select', 'translate', 'anagram',
    'true-false', 'timeline'
}

ALLOWED_TYPES = {'reading', 'essay-response', 'critical-analysis', 'comparative-study'}


def transform_activity(activity: dict) -> dict | None:
    """Transform an invalid activity to a valid HIST activity type.

    Returns the transformed activity dict, or None if it should be removed.
    """
    act_type = activity.get('type', '')

    if act_type not in FORBIDDEN_TYPES:
        return activity  # Already valid

    focus = activity.get('focus', '')
    items = activity.get('items')

    if act_type == 'timeline':
        # Timeline → critical-analysis focusing on cause-effect relationships
        new_focus = focus
        if focus.lower() in ['хронологія подій', 'chronology of events', 'chronology']:
            new_focus = 'Аналіз причинно-наслідкових зв\'язків між подіями'
        elif 'хронологія' in focus.lower() or 'chronolog' in focus.lower():
            new_focus = f'Аналіз: {focus}'
        else:
            new_focus = f'Критичний аналіз послідовності: {focus}'

        result = {
            'type': 'critical-analysis',
            'focus': new_focus,
        }
        if items:
            result['items'] = min(items, 5)  # Cap at 5 for critical-analysis
        else:
            result['items'] = 3  # Default
        return result

    elif act_type == 'true-false':
        # True-false → critical-analysis evaluating historical claims
        new_focus = focus
        if focus.lower() in ['факти та міфи', 'facts and myths', 'myths']:
            new_focus = 'Критична оцінка історичних тверджень та міфів'
        elif 'міф' in focus.lower() or 'myth' in focus.lower():
            new_focus = f'Спростування міфів: {focus}'
        elif 'факт' in focus.lower() or 'fact' in focus.lower():
            new_focus = f'Верифікація фактів: {focus}'
        else:
            new_focus = f'Критична оцінка: {focus}'

        result = {
            'type': 'critical-analysis',
            'focus': new_focus,
        }
        if items:
            result['items'] = min(items, 5)  # Cap at 5 for critical-analysis
        else:
            result['items'] = 4  # Default for fact-checking type
        return result

    elif act_type == 'quiz':
        # Quiz → reading comprehension check
        result = {
            'type': 'reading',
            'focus': f'Перевірка розуміння: {focus}' if focus else 'Перевірка розуміння тексту',
        }
        if items:
            result['items'] = items
        return result

    elif act_type in ('fill-in', 'cloze', 'match-up'):
        # These become reading activities
        result = {
            'type': 'reading',
            'focus': focus if focus else 'Робота з текстом',
        }
        return result

    elif act_type == 'group-sort':
        # Group-sort → comparative-study
        result = {
            'type': 'comparative-study',
            'focus': f'Порівняльний аналіз: {focus}' if focus else 'Порівняльний аналіз',
        }
        if items:
            result['items'] = items
        return result

    else:
        # Default: convert to critical-analysis
        result = {
            'type': 'critical-analysis',
            'focus': focus if focus else 'Критичний аналіз',
        }
        if items:
            result['items'] = min(items, 5)
        return result


def fix_file(file_path: Path, dry_run: bool = True) -> dict:
    """Fix invalid activity types in a plan file."""
    content = file_path.read_text(encoding='utf-8')

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return {'file': str(file_path), 'error': str(e), 'changes': [], 'modified': False}

    if not data or 'activity_hints' not in data:
        return {'file': str(file_path), 'changes': [], 'modified': False}

    activity_hints = data.get('activity_hints', [])
    if not activity_hints:
        return {'file': str(file_path), 'changes': [], 'modified': False}

    changes = []
    new_hints = []

    for activity in activity_hints:
        if not isinstance(activity, dict):
            new_hints.append(activity)
            continue

        act_type = activity.get('type', '')

        if act_type in FORBIDDEN_TYPES:
            transformed = transform_activity(activity)
            if transformed:
                changes.append({
                    'old_type': act_type,
                    'new_type': transformed['type'],
                    'old_focus': activity.get('focus', ''),
                    'new_focus': transformed.get('focus', ''),
                })
                new_hints.append(transformed)
            else:
                changes.append({
                    'old_type': act_type,
                    'new_type': 'REMOVED',
                    'old_focus': activity.get('focus', ''),
                    'new_focus': '',
                })
        else:
            new_hints.append(activity)

    if not changes:
        return {'file': str(file_path), 'changes': [], 'modified': False}

    # Update the data
    data['activity_hints'] = new_hints

    if not dry_run:
        # Write back with proper YAML formatting
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)

    return {'file': str(file_path), 'changes': changes, 'modified': True}


def main():
    parser = argparse.ArgumentParser(description="Fix invalid activity types in HIST plans")
    parser.add_argument('--apply', action='store_true', help="Apply changes (default is dry-run)")
    parser.add_argument('--verbose', '-v', action='store_true', help="Show detailed output")
    args = parser.parse_args()

    plans_dir = Path("curriculum/l2-uk-en/plans/hist")

    if not plans_dir.exists():
        print(f"Error: Directory not found: {plans_dir}")
        return 1

    plan_files = sorted(plans_dir.glob("*.yaml"))

    if not plan_files:
        print("No plan files found")
        return 1

    print("═" * 70)
    print(f"  HIST Plan Activity Type Fixer (with content transformation)")
    print(f"  Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print("═" * 70)
    print()

    total_changes = 0
    files_modified = 0

    for plan_file in plan_files:
        result = fix_file(plan_file, dry_run=not args.apply)

        if 'error' in result:
            print(f"⚠️  {plan_file.name}: YAML error - {result['error']}")
            continue

        if result['modified']:
            files_modified += 1
            total_changes += len(result['changes'])

            if args.verbose or not args.apply:
                print(f"📝 {plan_file.name}:")
                for change in result['changes']:
                    print(f"   {change['old_type']} → {change['new_type']}")
                    if args.verbose:
                        print(f"      old: {change['old_focus'][:60]}...")
                        print(f"      new: {change['new_focus'][:60]}...")

    print()
    print("═" * 70)
    print("  Summary")
    print("═" * 70)
    print()
    print(f"Files scanned:  {len(plan_files)}")
    print(f"Files modified: {files_modified}")
    print(f"Total changes:  {total_changes}")
    print()

    if not args.apply and total_changes > 0:
        print("Run with --apply to make changes:")
        print("  .venv/bin/python scripts/fix_b2hist_activity_types.py --apply")

    return 0


if __name__ == "__main__":
    exit(main())
