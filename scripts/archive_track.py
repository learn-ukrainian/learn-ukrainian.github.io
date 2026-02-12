#!/usr/bin/env python3
"""
Track Archival Script v1.1 (Senior Optimized)

Moves existing track content to an _archive folder before a full rebuild.
Ensures we have a 'Safe Restore' point for comparison.
"""

import sys
import shutil
from datetime import datetime
from pathlib import Path

def archive_track(track: str):
    if not track or track.strip() == "":
        print("Error: Track name cannot be empty.")
        return

    base_dir = Path(f"curriculum/l2-uk-en/{track}")
    if not base_dir.exists():
        print(f"Error: Track directory {base_dir} not found.")
        return

    # Create archive destination
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    archive_root = Path(f"_archive/{track}/{timestamp}")
    
    try:
        archive_root.mkdir(parents=True, exist_ok=True)
        print(f"📦 Archiving legacy content for {track} to {archive_root}...")

        # Archive .md files from track root
        md_files = list(base_dir.glob("*.md"))
        for item in md_files:
            shutil.copy2(item, archive_root / item.name)
        print(f"  📄 Archived {len(md_files)} Markdown files.")

        # Archive subdirectories
        subdirs = ["meta", "activities", "vocabulary", "review", "audit",
                   "status", "orchestration", "research"]

        for subdir in subdirs:
            src_path = base_dir / subdir
            if not src_path.exists() or not src_path.is_dir():
                continue
            dest_path = archive_root / subdir
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            print(f"  📁 Archived directory: {subdir}")

        # Archive MDX files from docusaurus/docs/{track}/
        mdx_dir = Path(f"docusaurus/docs/{track}")
        if mdx_dir.exists():
            mdx_dest = archive_root / "mdx"
            mdx_dest.mkdir(parents=True, exist_ok=True)
            for item in mdx_dir.glob("*.mdx"):
                shutil.copy2(item, mdx_dest / item.name)
            mdx_count = len(list(mdx_dest.glob("*.mdx")))
            print(f"  📄 Archived {mdx_count} MDX files from {mdx_dir}")

        print(f"✅ Archival complete. You can now safely run a 'Clean Slate' rebuild.")
    except Exception as e:
        print(f"🚨 Archival failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/archive_track.py <track_name>")
        sys.exit(1)
    
    archive_track(sys.argv[1])
