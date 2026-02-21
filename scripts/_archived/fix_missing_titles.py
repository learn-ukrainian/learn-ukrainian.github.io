#!/usr/bin/env python3
"""Fix missing title fields in B2 history module activities.

These modules use an older format with 'id' and 'question' but no 'title'.
This script adds appropriate titles based on the activity type and content.
"""

import yaml
from pathlib import Path

# List of B2 modules with missing titles (from validation output)
MODULES_TO_FIX = [
    108, 115, 116, 117, 118, 120, 121, 122, 123, 124, 126, 127, 128, 129, 130,
    # Also check 109 (had 13 errors, might be missing some titles)
    109
]

def generate_title(activity_type: str, activity_id: str, question: str = None) -> str:
    """Generate appropriate title based on activity metadata."""

    # Title templates by activity type
    templates = {
        'quiz': 'Перевірка розуміння',
        'fill-in': 'Заповніть пропуски',
        'match-up': 'Встановіть відповідності',
        'error-correction': 'Виправте помилки',
        'select': 'Виберіть правильні відповіді',
        'mark-the-words': 'Позначте слова',
        'unjumble': 'Складіть речення',
        'group-sort': 'Розподіліть за групами',
        'cloze': 'Текст із пропусками',
        'translate': 'Переклад',
        'true-false': 'Правда чи неправда',
    }

    # If question exists and is short enough, use it as title
    if question and len(question) < 80:
        return question

    # Otherwise use template
    base_title = templates.get(activity_type, 'Вправа')

    # Add context from ID if available
    if activity_id:
        if 'reading' in activity_id.lower():
            base_title = 'Читання: ' + base_title
        elif 'vocab' in activity_id.lower():
            base_title = 'Лексика: ' + base_title
        elif 'grammar' in activity_id.lower():
            base_title = 'Граматика: ' + base_title

    return base_title


def fix_module(module_num: int) -> int:
    """Fix missing titles in a module. Returns number of fixes made."""

    activity_file = Path(f'curriculum/l2-uk-en/b2/activities/{module_num:03d}-*.yaml')
    matches = list(activity_file.parent.glob(f'{module_num:03d}-*.yaml'))

    if not matches:
        print(f"⚠️  Module {module_num}: No activity file found")
        return 0

    activity_file = matches[0]

    with open(activity_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not data or 'activities' not in data:
        print(f"⚠️  Module {module_num}: Invalid format")
        return 0

    activities = data['activities']
    fixes_made = 0

    for activity in activities:
        if 'title' not in activity or not activity['title']:
            # Generate title
            activity_type = activity.get('type', 'unknown')
            activity_id = activity.get('id', '')
            question = activity.get('question', '')

            title = generate_title(activity_type, activity_id, question)
            activity['title'] = title
            fixes_made += 1

    if fixes_made > 0:
        # Write back
        with open(activity_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

        print(f"✅ Module {module_num}: Fixed {fixes_made} activities")
    else:
        print(f"✓  Module {module_num}: No fixes needed")

    return fixes_made


def main():
    print("🔧 Fixing missing title fields in B2 history modules\n")

    total_fixes = 0

    for module_num in MODULES_TO_FIX:
        fixes = fix_module(module_num)
        total_fixes += fixes

    print(f"\n✅ Complete: Fixed {total_fixes} activities across {len(MODULES_TO_FIX)} modules")


if __name__ == '__main__':
    main()
