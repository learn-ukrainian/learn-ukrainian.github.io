#!/usr/bin/env python3
"""Find modules that need Phase D reset: review score < 9.0 AND v3-D complete."""

import glob
import re
import json
import os

BASE = "curriculum/l2-uk-en"
results = []

# Find all review files matching *-review.md (but not *-final-review.md)
review_files = glob.glob(f"{BASE}/*/review/*-review.md")

for rf in review_files:
    # Skip final-review files
    if "-final-review.md" in rf:
        continue

    # Extract track and slug from path
    parts = rf.split("/")
    track = parts[2]
    filename = parts[-1]
    slug = filename.replace("-review.md", "")

    # Read the review file and extract score
    with open(rf, "r") as f:
        content = f.read()

    match = re.search(r"\*\*Overall Score:\*\*\s*([\d.]+)/10", content)
    if not match:
        continue
    score = float(match.group(1))

    # Only interested in score < 9.0
    if score >= 9.0:
        continue

    # Find corresponding state-v3.json
    state_path = f"{BASE}/{track}/orchestration/{slug}/state-v3.json"
    if not os.path.exists(state_path):
        continue

    with open(state_path, "r") as f:
        state = json.load(f)

    # Check v3-D status
    phases = state.get("phases", {})
    d_phase = phases.get("v3-D", {})
    d_status = d_phase.get("status", "not-found")

    if d_status == "complete":
        results.append((track, slug, score, d_status))

# Sort by score ascending
results.sort(key=lambda x: x[2])

# Print header and results
header_fmt = "{:<12} {:<45} {:<7} {}"
print(header_fmt.format("TRACK", "SLUG", "SCORE", "CURRENT_D_STATUS"))
print("-" * 80)
for track, slug, score, status in results:
    print(header_fmt.format(track, slug, f"{score:.1f}", status))

print(f"\nTotal: {len(results)} modules need Phase D reset")
