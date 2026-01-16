import os
import re

audit_dir = "curriculum/l2-uk-en/a1/audit/"
failures = []

if not os.path.exists(audit_dir):
    print(f"Directory not found: {audit_dir}")
    exit(1)

for filename in os.listdir(audit_dir):
    if filename.endswith("-review.md"):
        filepath = os.path.join(audit_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            if "**Overall Status:** ❌ FAIL" in content:
                failures.append(filename)

print("Failed Modules:")
for f in sorted(failures):
    print(f"- {f}")
