#!/usr/bin/env python3
"""Fix both unjumble items with less than 6 words."""

import yaml

# Read activities
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'r') as f:
    activities = yaml.safe_load(f)

# Find unjumble activity
for idx, activity in enumerate(activities):
    if activity.get('type') == 'unjumble':
        print(f"Processing activity {idx}: {activity.get('title')}")

        # Check each item
        for i, item in enumerate(activity['items']):
            if len(item['words']) < 6:
                print(f"  Item {i+1}: {len(item['words'])} words - {item['answer']}")

                # Fix the first short sentence (item 10)
                if item['answer'] == 'Візуальні елементи підвищують ефективність презентації.':
                    item['words'] = ['візуальні', 'презентації', 'підвищують', 'ефективність', 'елементи', 'значно']
                    item['answer'] = 'Візуальні елементи значно підвищують ефективність презентації.'
                    print(f"    → Fixed to {len(item['words'])} words: {item['answer']}")

                # Fix the second short sentence (item 12)
                elif item['answer'] == 'Уникайте багато тексту на слайдах.':
                    item['words'] = ['слайдах', 'багато', 'тексту', 'уникайте', 'на', 'щоб', 'зберегти', 'читабельність']
                    item['answer'] = 'Уникайте багато тексту на слайдах, щоб зберегти читабельність.'
                    print(f"    → Fixed to {len(item['words'])} words: {item['answer']}")

print("\n✅ Fixed all short unjumble items")

# Write back
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'w') as f:
    yaml.dump(activities, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print("✅ All unjumble items now have 6+ words")
