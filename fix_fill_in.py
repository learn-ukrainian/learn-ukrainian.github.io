#!/usr/bin/env python3
"""Fix fill-in activity 9 - rename 'text' to 'sentence' and remove 'blank' field."""

import yaml

# Read activities
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'r') as f:
    activities = yaml.safe_load(f)

# Fix activity 9 (fill-in) - rename fields
for item in activities[9]['items']:
    if 'text' in item:
        item['sentence'] = item.pop('text')
    if 'blank' in item:
        del item['blank']  # Remove blank field - not in schema

print(f"✅ Fixed {len(activities[9]['items'])} items in activity 9 (fill-in)")
print(f"   Renamed 'text' → 'sentence', removed 'blank' field")

# Write back
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'w') as f:
    yaml.dump(activities, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print("✅ Fill-in activity now matches schema")
