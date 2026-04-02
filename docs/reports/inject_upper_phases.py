import os
import re

import ruamel.yaml

manifest_path = "curriculum/l2-uk-en/curriculum.yaml"
with open(manifest_path, encoding="utf-8") as f:
    manifest_lines = f.read().split("\n")

yaml_handler = ruamel.yaml.YAML()
yaml_handler.preserve_quotes = True
yaml_handler.indent(mapping=2, sequence=4, offset=2)

mapping = {}

for level in ["B2", "C1", "C2"]:
    md_path = f"docs/l2-uk-en/{level}-PLAN-GENERATED.md"
    if not os.path.exists(md_path):
        continue
    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    current_phase = None
    for line in content.split("\n"):
        phase_match = re.match(r"^\#\#+\s+Phase\s+([A-C][1-2]\.\w+):\s+(.*?)\s*(\(|$)", line, re.IGNORECASE)
        if phase_match:
            current_phase = f"{phase_match.group(1)} [{phase_match.group(2).strip()}]"
            continue

        table_match = re.match(r"^\|\s*\d+\s*\|\s*([a-z0-9-]+)\s*\|", line)
        if table_match and current_phase:
            slug = table_match.group(1)
            slug = re.sub(r"^\d+-", "", slug)
            if slug not in mapping:
                mapping[slug] = current_phase

# Now apply mapping to plans
for level in ["b2", "c1", "c2"]:
    plan_dir = f"curriculum/l2-uk-en/plans/{level}"
    if not os.path.exists(plan_dir): continue
    for f in os.listdir(plan_dir):
        if not f.endswith(".yaml"): continue
        slug = f.replace(".yaml", "")
        if slug in mapping:
            fpath = os.path.join(plan_dir, f)
            with open(fpath, encoding="utf-8") as pf:
                try:
                    plan = yaml_handler.load(pf)
                except:
                    continue
            if plan.get("phase") != mapping[slug]:
                plan["phase"] = mapping[slug]
                with open(fpath, "w", encoding="utf-8") as pf:
                    yaml_handler.dump(plan, pf)

# Now inject phases into curriculum.yaml
out_lines = []
current_level = None
in_modules = False
last_phase = None

for line in manifest_lines:
    level_match = re.match(r"^  ([a-z0-9-]+):", line)
    if level_match:
        current_level = level_match.group(1)
        in_modules = False
        last_phase = None

    modules_match = re.match(r"^\s+modules:", line)
    if modules_match:
        in_modules = True

    if current_level in ["b2", "c1", "c2"] and in_modules:
        if re.match(r"^\s+#\s*[A-Z][1-2]\.\w+", line):
            continue  # Skip existing phase comment

    slug_match = re.match(r"^(\s+)-\s+([a-z0-9-]+)", line)
    if current_level in ["b2", "c1", "c2"] and in_modules and slug_match:
        indent = slug_match.group(1)
        slug = slug_match.group(2)

        phase = mapping.get(slug, "")
        if not phase:
            plan_path = f"curriculum/l2-uk-en/plans/{current_level}/{slug}.yaml"
            if os.path.exists(plan_path):
                with open(plan_path, encoding="utf-8") as pf:
                    try:
                        plan = yaml_handler.load(pf)
                        phase = plan.get("phase", "")
                    except:
                        pass

        if phase and phase != last_phase:
            comment_line = f"{indent}# {phase}"
            if not out_lines or out_lines[-1] != comment_line:
                out_lines.append(comment_line)
            last_phase = phase

    out_lines.append(line)

with open(manifest_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))

print("Phase comments injected into B2, C1, C2 in curriculum.yaml.")
