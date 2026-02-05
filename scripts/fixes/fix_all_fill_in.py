#!/usr/bin/env python3
"""Fix ALL fill-in activities - rename 'text' to 'sentence' and remove 'blank' field."""

import yaml

# Read activities
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'r') as f:
    activities = yaml.safe_load(f)

# Find and fix all fill-in activities
fixed_count = 0
for idx, activity in enumerate(activities):
    if activity.get('type') == 'fill-in':
        print(f"Processing activity {idx}: {activity.get('title')}")
        for item in activity['items']:
            if 'text' in item:
                item['sentence'] = item.pop('text')
            if 'blank' in item:
                del item['blank']  # Remove blank field - not in schema
        fixed_count += 1
        print(f"  ✅ Fixed {len(activity['items'])} items")

print(f"\n✅ Fixed {fixed_count} fill-in activities total")

# Write back
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'w') as f:
    yaml.dump(activities, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print("✅ All fill-in activities now match schema")
