#!/usr/bin/env python3
"""Check that changes to MDX files have corresponding changes in curriculum sources."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MDX_DIR = PROJECT_ROOT / "starlight/src/content/docs"
SOURCE_DIR = PROJECT_ROOT / "curriculum/l2-uk-en"
LEGACY_TRACKS_FILE = PROJECT_ROOT / "scripts/audit/mdx_source_parity_legacy_tracks.yaml"

def get_legacy_levels() -> set[str]:
    if not LEGACY_TRACKS_FILE.exists():
        return set()
    try:
        with open(LEGACY_TRACKS_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return set(data.get("legacy_levels", []))
    except Exception:
        return set()

def get_changed_files(base: str | None = None, cached: bool = False) -> list[Path]:
    cmd = ["git", "diff", "--name-only"]
    if cached:
        cmd.append("--cached")
    elif base:
        try:
            merge_base = subprocess.check_output(["git", "merge-base", base, "HEAD"], text=True).strip()
            cmd.append(f"{merge_base}...HEAD")
        except subprocess.CalledProcessError:
            cmd.append(f"{base}...HEAD")

    try:
        output = subprocess.check_output(cmd, text=True)
        return [PROJECT_ROOT / f for f in output.splitlines() if f]
    except subprocess.CalledProcessError:
        return []

def is_whitespace_only(file_path: Path, base: str | None = None, cached: bool = False) -> bool:
    """Check if the diff for a file is purely whitespace."""
    cmd = ["git", "diff", "-U0", "-w", "--shortstat"]
    if cached:
        cmd.append("--cached")
    elif base:
        try:
            merge_base = subprocess.check_output(["git", "merge-base", base, "HEAD"], text=True).strip()
            cmd.append(f"{merge_base}...HEAD")
        except subprocess.CalledProcessError:
            cmd.append(f"{base}...HEAD")
    cmd.extend(["--", str(file_path)])

    try:
        output = subprocess.check_output(cmd, text=True).strip()
        # Empty output from shortstat means no non-whitespace changes
        return output == ""
    except subprocess.CalledProcessError:
        return False

def check_parity(mdx_files: list[Path], changed_files: set[Path], base: str | None = None, cached: bool = False) -> list[tuple[Path, str]]:
    legacy_levels = get_legacy_levels()
    violations = []

    # Extract level and slug for each changed MDX file
    for mdx_path in mdx_files:
        try:
            rel_path = mdx_path.relative_to(MDX_DIR)
        except ValueError:
            continue

        if rel_path.suffix != ".mdx":
            continue

        parts = rel_path.parts
        if len(parts) < 2:
            continue

        level = parts[0]
        slug = rel_path.stem

        if level in legacy_levels:
            continue

        # Check if it's a whitespace-only change
        if is_whitespace_only(mdx_path, base, cached):
            continue

        expected_source_dir = SOURCE_DIR / level / slug

        # Did any file in expected_source_dir change?
        source_changed = False
        for changed_file in changed_files:
            try:
                # Check if changed_file is under expected_source_dir
                changed_file.relative_to(expected_source_dir)
                source_changed = True
                break
            except ValueError:
                continue

        if not source_changed:
            violations.append((
                mdx_path,
                f"MDX file changed but no source files changed under curriculum/l2-uk-en/{level}/{slug}/"
            ))

    return violations

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check MDX source parity.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Scan whole repo (not usually used for parity check as it only applies to changes)")
    group.add_argument("--changed-vs-base", metavar="BASE", help="Compare against base branch, e.g. origin/main")
    group.add_argument("--files", nargs="+", type=Path, help="Scan explicit files (for pre-commit)")
    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if os.environ.get("MDX_PARITY_BULK_REGEN") == "1":
        # Check if the number of MDX files changed is > 50 (or just skip per brief)
        # Brief says: "if a commit changes >50 MDX files AND the commit message contains [regen-mdx] or [bulk-regen], allow through"
        # Since CI sets the env var conditionally based on commit message, we can just skip if set.
        # But we should still verify >50 files changed if possible, though the brief says "Handles the bulk-regen exemption via env var MDX_PARITY_BULK_REGEN=1 (CI sets it conditionally)"
        # Let's enforce the >50 rule here if we have changed files list.
        pass

    changed_files = []
    mdx_files = []
    base = None
    cached = False

    if args.changed_vs_base:
        base = args.changed_vs_base
        changed_files = get_changed_files(base=base)
        mdx_files = [f for f in changed_files if str(f).endswith(".mdx") and MDX_DIR in f.parents]
    elif args.files:
        # Pre-commit passes files. We need to check staged files.
        cached = True
        changed_files = get_changed_files(cached=True)
        # Include explicit files just in case
        mdx_files = [f.resolve() for f in args.files if f.suffix == ".mdx" and str(MDX_DIR) in str(f.resolve())]
        # Also ensure changed files contain them
        changed_files_set = set(f.resolve() for f in changed_files)
        for f in mdx_files:
            if f not in changed_files_set:
                changed_files.append(f)
    elif args.all:
        # scan whole repo? The parity rule is about CHANGES.
        # But if `--all` is provided, we can just check if any MDX file doesn't have a source dir.
        print("Checking structural parity for all MDX files...")
        legacy_levels = get_legacy_levels()
        violations = []
        for mdx_path in MDX_DIR.rglob("*.mdx"):
            rel_path = mdx_path.relative_to(MDX_DIR)
            parts = rel_path.parts
            if len(parts) < 2:
                continue
            level = parts[0]
            if level in legacy_levels:
                continue
            slug = rel_path.stem
            expected_source_dir = SOURCE_DIR / level / slug
            if not expected_source_dir.exists():
                violations.append((mdx_path, f"Missing source directory: {expected_source_dir}"))

        for path, msg in violations:
            print(f"{path}: {msg}")
        return 1 if violations else 0

    if os.environ.get("MDX_PARITY_BULK_REGEN") == "1" and len(mdx_files) > 50:
        print("Skipping due to MDX_PARITY_BULK_REGEN=1 and >50 MDX files changed.")
        return 0

    violations = check_parity(mdx_files, set(changed_files), base=base, cached=cached)

    for path, msg in violations:
        try:
            rel = path.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = path
        print(f"{rel}: {msg}")

    return 1 if violations else 0

if __name__ == "__main__":
    sys.exit(main())
