import glob
import os
import re

import yaml

plan_dir = "curriculum/l2-uk-en/plans/b1"
files = sorted(glob.glob(os.path.join(plan_dir, "*.yaml")))

total_files = len(files)
print(f"Found {total_files} B1 plan files.")

errors = []
missing_refs = 0
missing_vocab = 0
wrong_target = 0
missing_activities = 0
english_in_titles = 0

for fpath in files:
    slug = os.path.basename(fpath).replace('.yaml', '')
    with open(fpath, encoding="utf-8") as f:
        try:
            plan = yaml.safe_load(f)
        except Exception as e:
            errors.append(f"{slug}: YAML parse error - {e}")
            continue

    # AC1: RAG textbook grounding (references)
    references = plan.get('references', [])
    if not references:
        missing_refs += 1
        errors.append(f"{slug}: Missing 'references' section.")

    # AC3: vocabulary_hints present
    vocab_hints = plan.get('vocabulary_hints', [])
    if not vocab_hints:
        missing_vocab += 1
        errors.append(f"{slug}: Missing 'vocabulary_hints'.")

    # AC4: word_target: 4000
    target = plan.get('word_target')
    if target not in [1800, 2000, 2200, 2500, 3000, 4000]:
        wrong_target += 1
        errors.append(f"{slug}: Unusual word_target: {target}.")

    # AC5: activity_hints (4+)
    activity_hints = plan.get('activity_hints', [])
    if not activity_hints or len(activity_hints) < 4:
        missing_activities += 1
        errors.append(f"{slug}: Only {len(activity_hints) if activity_hints else 0} activity_hints found. Expected 4+.")

    # AC6: Full Ukrainian immersion (No English parentheticals in section titles)
    outline = plan.get('content_outline', [])
    for item in outline:
        title = item.get('title', '')
        if re.search(r'\([A-Za-z\s]+\)', title) or re.search(r'[a-zA-Z]', title):
            english_in_titles += 1
            errors.append(f"{slug}: English found in title: '{title}'")

if errors:
    print(f"\nFound {len(errors)} issues across the B1 plans:")
    for err in errors:
        print(f"  - {err}")
else:
    print("\nAll B1 plans conform to the basic structural criteria.")

print("\nStats:")
print(f"Missing refs: {missing_refs}")
print(f"Missing vocab: {missing_vocab}")
print(f"Unusual target: {wrong_target}")
print(f"Missing/low activities: {missing_activities}")
print(f"English in titles: {english_in_titles}")
