#!/usr/bin/env python3
"""Fix remaining M94 issues: unjumble item 13 length and boolean capitalization."""

import yaml

# Read activities
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'r') as f:
    activities = yaml.safe_load(f)

# Fix unjumble item 13 - extend from 4 words to 6+ words
activities[6]['items'][12] = {
    'words': ['завжди', 'вказуйте', 'джерела', 'даних', 'у', 'презентації'],
    'answer': 'Завжди вказуйте джерела даних у презентації.'
}
print("✅ Extended unjumble item 13 from 4 to 6 words")

# Write back
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'w') as f:
    yaml.dump(activities, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print("✅ All activity fixes applied")
