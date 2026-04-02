import glob
import os
import re

import yaml

plan_dir = "curriculum/l2-uk-en/plans/b2"
files = sorted(glob.glob(os.path.join(plan_dir, "*.yaml")))

print(f"Found {len(files)} B2 plan files.")

errors = []
missing_refs = 0
wrong_target = 0
missing_activities = 0
missing_situations = 0
english_in_titles = 0

for fpath in files:
    slug = os.path.basename(fpath).replace('.yaml', '')
    with open(fpath, encoding="utf-8") as f:
        try:
            plan = yaml.safe_load(f)
        except Exception as e:
            errors.append(f"{slug}: YAML parse error - {e}")
            continue

    # AC2: word_target: 4000
    target = plan.get('word_target')
    expected_target = 4000
    if "checkpoint" in slug or "review" in slug or "finale" in slug or "practice-exam" in slug:
        expected_target = 1500

    # the instructions said 4000 (from config), so let's check what's there
    if target not in [1500, 2000, 2500, 3000, 4000]:
        wrong_target += 1
        errors.append(f"{slug}: Unusual word_target: {target}")
    if "checkpoint" not in slug and "review" not in slug and "finale" not in slug and "practice-exam" not in slug and target != 4000:
        wrong_target += 1
        errors.append(f"{slug}: Expected word_target 4000, found {target}")

    # AC3: 3-5 activity_hints
    activity_hints = plan.get('activity_hints', [])
    if not activity_hints or len(activity_hints) < 3:
        missing_activities += 1
        errors.append(f"{slug}: Only {len(activity_hints) if activity_hints else 0} activity_hints found. Expected 3-5.")

    # AC4: at least 2 of reading, listening, writing, discussion
    sits = 0
    if plan.get('reading_situations'): sits += 1
    if plan.get('writing_tasks'): sits += 1
    if plan.get('listening_situations'): sits += 1
    if plan.get('discussion_topics'): sits += 1

    if sits < 2:
        missing_situations += 1
        errors.append(f"{slug}: Only found {sits} situation types. Expected at least 2.")

    # AC7: references
    references = plan.get('references', [])
    if not references:
        missing_refs += 1
        errors.append(f"{slug}: Missing 'references'.")

    # English in headers
    outline = plan.get('content_outline', [])
    for item in outline:
        title = item.get('section', item.get('title', ''))
        if re.search(r'\([A-Za-z\s]+\)', title):
            english_in_titles += 1
            errors.append(f"{slug}: English found in title: '{title}'")

if errors:
    print(f"\nFound {len(errors)} issues across the B2 plans:")
    for err in errors[:20]:
        print(f"  - {err}")
    if len(errors) > 20:
         print(f"  ... and {len(errors) - 20} more.")
else:
    print("\nAll B2 plans conform to the basic structural criteria.")

print("\nStats:")
print(f"Missing refs: {missing_refs}")
print(f"Wrong target: {wrong_target}")
print(f"Missing/low activities: {missing_activities}")
print(f"Missing situations: {missing_situations}")
print(f"English in titles: {english_in_titles}")
