#!/usr/bin/env python3
"""
Great Slug Migration Script v1.1 (Non-Destructive)

Physically renames all files with numeric prefixes (e.g., 01-slug.md) to 
bare slugs (slug.md) across all curriculum tracks and sidecars.
SAFE MODE: Never unlinks files. Renames collisions to .bak.
"""

import os
import re
import subprocess
from pathlib import Path

_PREFIX_RE = re.compile(r"^\d+-")

CURRICULUM_DIR = Path("curriculum/l2-uk-en")

def migrate_directory(directory: Path):
    if not directory.exists():
        return

    print(f"🌍 Processing: {directory}")
    for item in directory.iterdir():
        if item.is_dir():
            # Recurse into meta, activities, etc.
            if item.name in ["meta", "activities", "vocabulary", "status", "research", "review"]:
                migrate_directory(item)
            continue

        if _PREFIX_RE.match(item.name):
            new_name = _PREFIX_RE.sub("", item.name)
            new_path = item.parent / new_name
            
            # SAFE COLLISION HANDLING
            if new_path.exists():
                bak_path = item.with_suffix(f"{item.suffix}.collision_bak")
                print(f"  ⚠️ Collision: {new_name} already exists. Renaming legacy to {bak_path.name}")
                item.rename(bak_path)
                continue

            print(f"  ✅ Renaming: {item.name} -> {new_name}")
            try:
                # Use git mv if tracked, else os.rename
                subprocess.run(["git", "mv", str(item), str(new_path)], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                item.rename(new_path)

def main():
    # 1. Migrate all tracks in curriculum
    for track_dir in CURRICULUM_DIR.iterdir():
        if track_dir.is_dir() and not track_dir.name.startswith("."):
            migrate_directory(track_dir)
    
    # 2. Migrate plans
    migrate_directory(CURRICULUM_DIR / "plans")

    print("\n🏁 Migration Complete.")

if __name__ == "__main__":
    main()
