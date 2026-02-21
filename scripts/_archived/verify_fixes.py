
import glob
import subprocess
import os

files = glob.glob("curriculum/l2-uk-en/b2/*.md")
# List of IDs to check
id_targets = ["54", "55", "56", "57", "58", "59", "69", "83", "132", "133", "134", "135", "136", "137", "140", "142", "143", "144", "145"]

matches = []
for f in files:
    basename = os.path.basename(f)
    if basename.endswith("-review.md"): continue
    # extract ID
    try:
        mid = basename.split("-")[0]
        if mid in id_targets:
            matches.append(f)
    except:
        pass

matches.sort()
print(f"Found {len(matches)} modules to audit.")

for m in matches:
    print(f"Auditing {m}...")
    subprocess.run([".venv/bin/python", "scripts/audit_module.py", m], check=False)
