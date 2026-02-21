#!/usr/bin/env python3
"""Scan all B1 modules and report their audit status"""
import subprocess
import re
from pathlib import Path

b1_dir = Path("curriculum/l2-uk-en/b1")
failing_mods = [29, 34, 41, 43, 46, 47, 48, 49, 50, 51, 53, 54, 56, 59, 60, 61, 62, 63, 64, 66, 67, 68, 69, 70, 71, 72, 73, 74, 76, 77, 78, 79, 80]

for mod in failing_mods:
    files = list(b1_dir.glob(f"{mod:02d}-*.md"))
    if not files:
        print(f"M{mod}: FILE NOT FOUND")
        continue
    
    file = files[0]
    result = subprocess.run(
        ["python3", "scripts/audit_module.py", str(file)],
        capture_output=True, text=True
    )
    output = result.stdout + result.stderr
    
    # Extract key metrics
    words = re.search(r"Words\s+[✅❌⚠️]+\s+(\d+)/(\d+)", output)
    acts = re.search(r"Activities\s+[✅❌]+\s+(\d+)/(\d+)", output)
    lint_errors = "LINT ERROR" in output
    translit = "Transliteration" in output
    ai_contam = "AI Contamination" in output
    
    words_str = f"{words.group(1)}/{words.group(2)}" if words else "??/?"
    acts_str = f"{acts.group(1)}/{acts.group(2)}" if acts else "??/?"
    
    issues = []
    if words and int(words.group(1)) < int(words.group(2)):
        issues.append(f"WORDS({words.group(1)})")
    if acts and int(acts.group(1)) < int(acts.group(2)):
        issues.append(f"ACTS({acts.group(1)})")
    if translit:
        issues.append("TRANSLIT")
    if ai_contam:
        issues.append("AI")
    if lint_errors and not (translit or ai_contam):
        issues.append("LINT")
    
    print(f"M{mod}: Words={words_str} Acts={acts_str} Issues={','.join(issues) if issues else 'OTHER'}")
