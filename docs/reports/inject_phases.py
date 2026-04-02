import os
import re

import yaml

manifest_path = "curriculum/l2-uk-en/curriculum.yaml"
with open(manifest_path, encoding="utf-8") as f:
    lines = f.read().split("\n")

core_levels = ["a1", "a2", "b1", "b2", "c1", "c2"]

out_lines = []
current_level = None
in_modules = False
seen_phases = set()
last_phase = None

for line in lines:
    level_match = re.match(r"^  ([a-z0-9-]+):", line)
    if level_match:
        current_level = level_match.group(1)
        in_modules = False
        last_phase = None

    modules_match = re.match(r"^\s+modules:", line)
    if modules_match:
        in_modules = True

    # Strip existing phase comments
    if current_level in core_levels and in_modules:
        if re.match(r"^\s+# [A-Z][1-2]\.\d+", line):
            continue  # Skip existing phase comment
        if re.match(r"^\s+# Metalanguage bridge", line):
            continue  # Skip existing phase comment

    slug_match = re.match(r"^(\s+)-\s+([a-z0-9-]+)", line)
    if current_level in core_levels and in_modules and slug_match:
        indent = slug_match.group(1)
        slug = slug_match.group(2)

        # Load plan to get phase
        plan_path = f"curriculum/l2-uk-en/plans/{current_level}/{slug}.yaml"
        phase = ""
        if os.path.exists(plan_path):
            with open(plan_path, encoding="utf-8") as pf:
                try:
                    plan = yaml.safe_load(pf)
                    phase = plan.get("phase", "")
                except:
                    pass

        if phase and phase != last_phase:
            # Check if out_lines already ends with this comment to prevent duplicates
            comment_line = f"{indent}# {phase}"
            if not out_lines or out_lines[-1] != comment_line:
                out_lines.append(comment_line)
            last_phase = phase

    out_lines.append(line)

with open(manifest_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))

print("Phase comments injected into curriculum.yaml.")
