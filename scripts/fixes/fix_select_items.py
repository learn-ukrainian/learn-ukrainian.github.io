#!/usr/bin/env python3
"""Add 2 more items to activity 14 (select) to meet minItems: 8 requirement."""

import yaml

# Read activities
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'r') as f:
    activities = yaml.safe_load(f)

# Activity 14 needs 2 more items (currently 6, need 8)
activities[14]['items'].extend([
    {
        'question': 'Які навички необхідні для успішної професійної комунікації в українському бізнес-середовищі?',
        'min_correct': 3,
        'options': [
            {'text': 'Формальний стиль мовлення', 'correct': True},
            {'text': 'Критичне мислення', 'correct': True},
            {'text': 'Аргументація з даними', 'correct': True},
            {'text': 'Використання англіцизмів', 'correct': False},
            {'text': 'Емоційні маніпуляції', 'correct': False}
        ],
        'explanation': 'Професійна комунікація вимагає формального стилю, критичного мислення та обґрунтованої аргументації.'
    },
    {
        'question': 'Що характеризує високу якість професійної презентації українською мовою?',
        'min_correct': 3,
        'options': [
            {'text': 'Логічна структура викладу', 'correct': True},
            {'text': 'Підтвердження тез фактами', 'correct': True},
            {'text': 'Вміння відповідати на питання', 'correct': True},
            {'text': 'Читання тексту зі слайдів', 'correct': False},
            {'text': 'Надмірне використання технічних термінів', 'correct': False}
        ],
        'explanation': 'Якісна презентація має чітку структуру, фактичну базу та інтерактивність з аудиторією.'
    }
])

print(f"✅ Added 2 items to activity 14 (now {len(activities[14]['items'])} items total)")

# Write back
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'w') as f:
    yaml.dump(activities, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print("✅ Activity 14 now meets minItems: 8 requirement")
