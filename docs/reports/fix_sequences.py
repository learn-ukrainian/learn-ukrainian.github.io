import os

import ruamel.yaml

manifest_path = "curriculum/l2-uk-en/curriculum.yaml"
plans_a2_dir = "curriculum/l2-uk-en/plans/a2"
plans_b1_dir = "curriculum/l2-uk-en/plans/b1"

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)

with open(manifest_path, encoding="utf-8") as f:
    manifest = yaml.load(f)

a2_modules = manifest["levels"]["a2"]["modules"]
b1_modules = manifest["levels"]["b1"]["modules"]

def fix_track(modules, level_str, plans_dir):
    level_lower = level_str.lower()
    for idx, slug in enumerate(modules):
        seq = idx + 1
        mod_id = f"{level_lower}-{seq:03d}"

        path = os.path.join(plans_dir, f"{slug}.yaml")
        if not os.path.exists(path):
            print(f"Error: {path} not found!")
            continue

        with open(path, encoding="utf-8") as f:
            plan = yaml.load(f)

        plan["module"] = mod_id
        plan["sequence"] = seq
        plan["level"] = level_str

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(plan, f)

print("Fixing A2 track sequences...")
fix_track(a2_modules, "A2", plans_a2_dir)

print("Fixing B1 track sequences...")
fix_track(b1_modules, "B1", plans_b1_dir)

print("All sequence numbers fixed.")
