#!/usr/bin/env python3
"""Fix true-false activity 11 - rename 'text' to 'statement' and 'answer' to 'correct'."""

import yaml

# Read activities
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'r') as f:
    activities = yaml.safe_load(f)

# Fix activity 11 (true-false) - rename fields
for item in activities[11]['items']:
    if 'text' in item:
        item['statement'] = item.pop('text')
    if 'answer' in item:
        item['correct'] = item.pop('answer')

print(f"✅ Fixed {len(activities[11]['items'])} items in activity 11 (true-false)")
print(f"   Renamed 'text' → 'statement', 'answer' → 'correct'")

# Write back
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'w') as f:
    yaml.dump(activities, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print("✅ True-false activity now matches schema")
