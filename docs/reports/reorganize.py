import glob
import os
import shutil

import ruamel.yaml

manifest_path = "curriculum/l2-uk-en/curriculum.yaml"
plans_a2_dir = "curriculum/l2-uk-en/plans/a2"
plans_b1_dir = "curriculum/l2-uk-en/plans/b1"
content_a2_dir = "curriculum/l2-uk-en/a2"
content_b1_dir = "curriculum/l2-uk-en/b1"

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)

with open(manifest_path, encoding="utf-8") as f:
    manifest = yaml.load(f)

a2_modules = manifest["levels"]["a2"]["modules"]
b1_modules = manifest["levels"]["b1"]["modules"]

modules_to_move = [
    "metalanguage-phonetics",
    "metalanguage-morphology",
    "metalanguage-syntax-cases"
]

# 1. Remove from B1
for m in modules_to_move:
    if m in b1_modules:
        b1_modules.remove(m)

# 2. Insert into A2 (after metalanguage-sentences-and-classroom)
try:
    insert_idx = a2_modules.index("metalanguage-sentences-and-classroom") + 1
except ValueError:
    insert_idx = len(a2_modules)

for m in reversed(modules_to_move):
    if m not in a2_modules:
        a2_modules.insert(insert_idx, m)

# Save manifest
with open(manifest_path, "w", encoding="utf-8") as f:
    yaml.dump(manifest, f)
print("Updated curriculum.yaml.")

def update_track(modules, level_str, target_plan_dir, target_content_dir):
    level_lower = level_str.lower()
    for idx, slug in enumerate(modules):
        seq = idx + 1
        mod_id = f"{level_lower}-{seq:03d}"

        # Determine where the plan currently lives
        current_plan_path = None
        for pdir in [plans_a2_dir, plans_b1_dir]:
            test_path = os.path.join(pdir, f"{slug}.yaml")
            if os.path.exists(test_path):
                current_plan_path = test_path
                break

        if not current_plan_path:
            print(f"Warning: plan for {slug} not found.")
            continue

        with open(current_plan_path, encoding="utf-8") as f:
            plan = yaml.load(f)

        old_level = plan.get("level", "")
        plan["module"] = mod_id
        plan["sequence"] = seq
        plan["level"] = level_str

        # Save back to its current path first
        with open(current_plan_path, "w", encoding="utf-8") as f:
            yaml.dump(plan, f)

        new_plan_path = os.path.join(target_plan_dir, f"{slug}.yaml")

        if current_plan_path != new_plan_path:
            print(f"Moving {slug} from {os.path.basename(os.path.dirname(current_plan_path))} to {os.path.basename(target_plan_dir)}")
            shutil.move(current_plan_path, new_plan_path)

            old_base_dir = "curriculum/l2-uk-en/b1" if old_level == "B1" else "curriculum/l2-uk-en/a2"

            # move .md file
            old_md = os.path.join(old_base_dir, f"{slug}.md")
            new_md = os.path.join(target_content_dir, f"{slug}.md")
            if os.path.exists(old_md):
                shutil.move(old_md, new_md)

            # move orchestration
            old_orch = os.path.join(old_base_dir, "orchestration", slug)
            new_orch = os.path.join(target_content_dir, "orchestration", slug)
            if os.path.exists(old_orch):
                shutil.move(old_orch, new_orch)

            # move review
            old_reviews = glob.glob(os.path.join(old_base_dir, "review", f"{slug}*"))
            for old_rev in old_reviews:
                new_rev = os.path.join(target_content_dir, "review", os.path.basename(old_rev))
                if not os.path.exists(os.path.dirname(new_rev)):
                    os.makedirs(os.path.dirname(new_rev))
                shutil.move(old_rev, new_rev)

print("Updating A2 track sequence and moving files...")
update_track(a2_modules, "A2", plans_a2_dir, content_a2_dir)

print("Updating B1 track sequence and moving files...")
update_track(b1_modules, "B1", plans_b1_dir, content_b1_dir)

print("Curriculum reorganization complete.")
