from pathlib import Path

import yaml

manifest_path = "curriculum/l2-uk-en/curriculum.yaml"
with open(manifest_path) as f:
    manifest = yaml.safe_load(f)

lit_modules = manifest["levels"]["lit"].get("modules", [])

plan_dir = Path("curriculum/l2-uk-en/plans/lit")
plan_files = [f.stem for f in plan_dir.glob("*.yaml")]

for p in plan_files:
    if p not in lit_modules:
        print(f"Orphaned plan file found in lit track: {p}.yaml")
