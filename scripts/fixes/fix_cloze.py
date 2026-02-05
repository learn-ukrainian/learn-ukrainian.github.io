#!/usr/bin/env python3
"""Fix cloze activity - rename 'text' to 'passage' and remove 'blanks' integer."""

import yaml

# Read activities
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'r') as f:
    activities = yaml.safe_load(f)

# Fix activity 11 (index 10) - cloze
cloze = activities[10]

# Rename 'text' to 'passage'
if 'text' in cloze:
    cloze['passage'] = cloze.pop('text')
    print("✅ Renamed 'text' field to 'passage'")

# Remove 'blanks' integer (it should be array if used, but not needed for inline format)
if 'blanks' in cloze:
    del cloze['blanks']
    print("✅ Removed 'blanks' field (not needed for inline {option|option} format)")

# Write back
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'w') as f:
    yaml.dump(activities, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print("\n✅ Cloze activity now matches schema (uses 'passage' field)")
