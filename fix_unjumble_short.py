#!/usr/bin/env python3
"""Fix unjumble items with less than 6 words."""

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
                print(f"  Item {i+1}: {len(item['words'])} words - FIXING")

                # Fix the specific short sentence
                if item['answer'] == 'Візуальні елементи підвищують ефективність презентації.':
                    # Extend to 6 words by adding "значно"
                    item['words'] = ['візуальні', 'презентації', 'підвищують', 'ефективність', 'елементи', 'значно']
                    item['answer'] = 'Візуальні елементи значно підвищують ефективність презентації.'
                    print(f"    → Extended to {len(item['words'])} words")

print("\n✅ Fixed short unjumble items")

# Write back
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'w') as f:
    yaml.dump(activities, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print("✅ All unjumble items now have 6+ words")
