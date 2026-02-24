import yaml
import re
from pathlib import Path

manifest_path = "curriculum/l2-uk-en/curriculum.yaml"
with open(manifest_path) as f:
    manifest = yaml.safe_load(f)

levels = manifest.get("levels", {})

new_tracks = ["lit-doc", "lit-drama", "lit-crimea", "lit-youth"]

for track in new_tracks:
    research_dir = Path("curriculum/l2-uk-en") / track / "research"
    if not research_dir.exists(): continue
    
    actual_slugs = [f.stem.replace("-research", "") for f in research_dir.glob("*-research.md")]
    
    for slug in actual_slugs:
        # Remove from any other track
        for t_name, t_data in levels.items():
            if t_name != track and slug in t_data.get("modules", []):
                t_data["modules"].remove(slug)
                print(f"Removed {slug} from {t_name}")
                
        # Ensure it is in the target track
        if slug not in levels[track].get("modules", []):
            levels[track]["modules"].append(slug)
            print(f"Added {slug} to {track}")

with open(manifest_path, "w") as f:
    yaml.dump(manifest, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
