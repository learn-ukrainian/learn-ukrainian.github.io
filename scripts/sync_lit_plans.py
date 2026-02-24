import os
import shutil
from pathlib import Path

curriculum_dir = Path("curriculum/l2-uk-en")
plans_dir = curriculum_dir / "plans"

new_tracks = ["lit-doc", "lit-drama", "lit-crimea", "lit-youth"]

for track in new_tracks:
    research_dir = curriculum_dir / track / "research"
    if not research_dir.exists(): continue
    
    actual_slugs = [f.stem.replace("-research", "") for f in research_dir.glob("*-research.md")]
    
    for slug in actual_slugs:
        # Move plans from old tracks
        for old_track in ["lit", "lit-essay", "lit-war"]:
            old_plan = plans_dir / old_track / f"{slug}.yaml"
            new_plan = plans_dir / track / f"{slug}.yaml"
            if old_plan.exists() and not new_plan.exists():
                old_plan.rename(new_plan)
                print(f"Moved plan {slug}.yaml to {track}")
