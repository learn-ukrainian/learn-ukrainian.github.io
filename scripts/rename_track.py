#!/usr/bin/env python3
"""Track rename migration script.

Renames a track slug across the entire project: filesystem paths, file contents,
config keys, and schemas. Uses git mv for directory renames to preserve history.

Usage:
    .venv/bin/python scripts/rename_track.py hist hist --dry-run
    .venv/bin/python scripts/rename_track.py hist hist
    .venv/bin/python scripts/rename_track.py istorio istorio --dry-run
    .venv/bin/python scripts/rename_track.py bio bio

Config mapping (must be defined in RENAME_CONFIG below for each rename).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories/files to skip entirely during content replacement
SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "scripts/_archived",
    ".astro",
}

# File extensions to process for content replacement
CONTENT_EXTENSIONS = {
    ".py", ".yaml", ".yml", ".json", ".md", ".ts", ".tsx",
    ".mjs", ".js", ".toml", ".cfg", ".sh",
}

# Known rename configurations
RENAME_CONFIG = {
    "hist": {
        "new_slug": "hist",
        "old_config_key": "history",
        "new_config_key": "history",
        "old_quick_ref": "HIST",
        "new_quick_ref": "HIST",
    },
    "istorio": {
        "new_slug": "istorio",
        "old_config_key": "istorio",
        "new_config_key": "istorio",
        "old_quick_ref": "ISTORIO",
        "new_quick_ref": "ISTORIO",
    },
    "bio": {
        "new_slug": "bio",
        "old_config_key": "biography",
        "new_config_key": "biography",
        "old_quick_ref": "BIO",
        "new_quick_ref": "BIO",
    },
}


def should_skip(path: Path) -> bool:
    """Check if a path should be skipped."""
    rel = path.relative_to(PROJECT_ROOT)
    parts = rel.parts
    for skip in SKIP_DIRS:
        skip_parts = Path(skip).parts
        for i in range(len(parts) - len(skip_parts) + 1):
            if parts[i:i + len(skip_parts)] == skip_parts:
                return True
    return False


def git_mv(src: Path, dst: Path, dry_run: bool) -> bool:
    """Rename using git mv. Returns True on success."""
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(f"  [DRY-RUN] git mv {src.relative_to(PROJECT_ROOT)} → {dst.relative_to(PROJECT_ROOT)}")
        return True
    result = subprocess.run(
        ["git", "mv", str(src), str(dst)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  [ERROR] git mv failed: {result.stderr.strip()}")
        return False
    print(f"  git mv {src.relative_to(PROJECT_ROOT)} → {dst.relative_to(PROJECT_ROOT)}")
    return True


def filesystem_renames(old_slug: str, new_slug: str, config: dict, dry_run: bool) -> int:
    """Layer 1: Filesystem renames using git mv. Returns count of renames."""
    count = 0
    old_upper = config["old_quick_ref"]
    new_upper = config["new_quick_ref"]

    # Directory renames
    dir_pairs = [
        # Curriculum content directory
        (f"curriculum/l2-uk-en/{old_slug}", f"curriculum/l2-uk-en/{new_slug}"),
        # Plans subdirectory
        (f"curriculum/l2-uk-en/plans/{old_slug}", f"curriculum/l2-uk-en/plans/{new_slug}"),
        # Docusaurus docs (if exists)
        (f"docusaurus/docs/{old_slug}", f"docusaurus/docs/{new_slug}"),
    ]

    for old_rel, new_rel in dir_pairs:
        src = PROJECT_ROOT / old_rel
        dst = PROJECT_ROOT / new_rel
        if src.exists() and src.is_dir() and git_mv(src, dst, dry_run):
            count += 1

    # File renames
    file_pairs = [
        # Plan file
        (f"curriculum/l2-uk-en/plans/{old_slug}.yaml", f"curriculum/l2-uk-en/plans/{new_slug}.yaml"),
        # Activity schema
        (f"schemas/activities-{old_slug}.schema.json", f"schemas/activities-{new_slug}.schema.json"),
        # Quick-ref
        (f"claude_extensions/quick-ref/{old_upper}.md", f"claude_extensions/quick-ref/{new_upper}.md"),
        # Batch state checkpoint
        (f"batch_state/checkpoint_{old_slug}.json", f"batch_state/checkpoint_{new_slug}.json"),
        # Batch state API usage summary
        (f"batch_state/api_usage/summary_{old_slug}.json", f"batch_state/api_usage/summary_{new_slug}.json"),
    ]

    for old_rel, new_rel in file_pairs:
        src = PROJECT_ROOT / old_rel
        dst = PROJECT_ROOT / new_rel
        if src.exists() and src.is_file() and git_mv(src, dst, dry_run):
            count += 1

    return count


def build_replacements(old_slug: str, new_slug: str, config: dict) -> list[tuple[str, str]]:
    """Build all string replacement pairs (old → new), ordered longest-first to avoid partial matches."""
    pairs = [
        # Config keys (longest first to avoid partial matches)
        (config["old_config_key"], config["new_config_key"]),
        # Quick-ref names
        (config["old_quick_ref"], config["new_quick_ref"]),
        # Kebab-case slug (the primary one)
        (old_slug, new_slug),
    ]

    # Add underscore variant if different from kebab
    old_under = old_slug.replace("-", "_")
    new_under = new_slug.replace("-", "_")
    if old_under != old_slug:
        pairs.append((old_under, new_under))

    # Sort longest-first to prevent partial matches
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


def content_replacements(old_slug: str, new_slug: str, config: dict, dry_run: bool) -> tuple[int, int]:
    """Layer 2: Content replacements in all qualifying files.

    Returns (files_changed, lines_changed).
    """
    replacements = build_replacements(old_slug, new_slug, config)
    files_changed = 0
    total_lines_changed = 0

    for root, dirs, files in os.walk(PROJECT_ROOT):
        root_path = Path(root)

        # Prune skip directories
        dirs[:] = [
            d for d in dirs
            if not should_skip(root_path / d)
        ]

        for fname in files:
            fpath = root_path / fname
            if fpath.suffix not in CONTENT_EXTENSIONS:
                continue
            if should_skip(fpath):
                continue

            try:
                content = fpath.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue

            new_content = content
            for old_str, new_str in replacements:
                new_content = new_content.replace(old_str, new_str)

            if new_content != content:
                lines_changed = sum(
                    1 for a, b in zip(content.splitlines(), new_content.splitlines(), strict=False) if a != b
                )
                # Account for different line counts
                lines_changed = max(lines_changed, abs(len(content.splitlines()) - len(new_content.splitlines())))

                rel = fpath.relative_to(PROJECT_ROOT)
                if dry_run:
                    print(f"  [DRY-RUN] {rel} ({lines_changed} lines)")
                else:
                    fpath.write_text(new_content, encoding="utf-8")
                    print(f"  {rel} ({lines_changed} lines)")

                files_changed += 1
                total_lines_changed += lines_changed

    return files_changed, total_lines_changed


def main():
    parser = argparse.ArgumentParser(
        description="Rename a track slug across the entire project"
    )
    parser.add_argument("old_slug", help="Current track slug (e.g., hist)")
    parser.add_argument("new_slug", help="New track slug (e.g., hist)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without touching files",
    )

    args = parser.parse_args()
    old_slug = args.old_slug
    new_slug = args.new_slug

    # Validate the rename is known
    if old_slug not in RENAME_CONFIG:
        print(f"Error: '{old_slug}' not in RENAME_CONFIG. Known renames: {list(RENAME_CONFIG.keys())}")
        sys.exit(1)

    config = RENAME_CONFIG[old_slug]
    if config["new_slug"] != new_slug:
        print(f"Error: expected new slug '{config['new_slug']}' for '{old_slug}', got '{new_slug}'")
        sys.exit(1)

    # Verify we're in the project root
    if not (PROJECT_ROOT / ".git").is_dir():
        print("Error: must run from a git repository")
        sys.exit(1)

    mode = "[DRY-RUN] " if args.dry_run else ""
    print(f"\n{mode}Renaming track: {old_slug} → {new_slug}")
    print(f"  Config key: {config['old_config_key']} → {config['new_config_key']}")
    print(f"  Quick-ref:  {config['old_quick_ref']} → {config['new_quick_ref']}")
    print()

    # Layer 1: Filesystem renames
    print("=== Layer 1: Filesystem renames (git mv) ===")
    rename_count = filesystem_renames(old_slug, new_slug, config, args.dry_run)
    print(f"  Total: {rename_count} renames\n")

    # Layer 2: Content replacements
    print("=== Layer 2: Content replacements ===")
    files_changed, lines_changed = content_replacements(old_slug, new_slug, config, args.dry_run)
    print(f"  Total: {files_changed} files, {lines_changed} lines\n")

    # Summary
    print("=== Summary ===")
    print(f"  Filesystem renames: {rename_count}")
    print(f"  Files modified:     {files_changed}")
    print(f"  Lines changed:      {lines_changed}")

    if args.dry_run:
        print("\n  Run without --dry-run to apply changes.")
    else:
        print("\n  Done. Review with 'git diff --stat' then commit.")


if __name__ == "__main__":
    main()
