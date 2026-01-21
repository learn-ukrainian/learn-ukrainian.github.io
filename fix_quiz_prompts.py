#!/usr/bin/env python3
"""Fix quiz prompts that are too short (4 words -> 5+ words)."""

import yaml

# Read activities
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'r') as f:
    activities = yaml.safe_load(f)

# Fix 1: "Виявлення упередження в медіа" Q3
for activity in activities:
    if activity.get('title') == 'Виявлення упередження в медіа':
        activity['items'][2]['question'] = 'Як правильно перевірити достовірність новини в мережі?'
        print(f"✅ Fixed quiz 'Виявлення упередження в медіа' Q3")
        print(f"   Old (4 words): Як перевірити достовірність новини?")
        print(f"   New (7 words): Як правильно перевірити достовірність новини в мережі?")

# Fix 2: "Підсумкова перевірка комунікаційних навичок" Q9
for activity in activities:
    if activity.get('title') == 'Підсумкова перевірка комунікаційних навичок':
        activity['items'][8]['question'] = 'Яка презентація буде найбільш ефективною для аудиторії?'
        print(f"✅ Fixed quiz 'Підсумкова перевірка комунікаційних навичок' Q9")
        print(f"   Old (4 words): Яка презентація буде найефективнішою?")
        print(f"   New (7 words): Яка презентація буде найбільш ефективною для аудиторії?")

# Write back
with open('curriculum/l2-uk-en/b2/activities/94-b2-final-exam.yaml', 'w') as f:
    yaml.dump(activities, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print("\n✅ All quiz prompts now meet minimum 5 words requirement")
