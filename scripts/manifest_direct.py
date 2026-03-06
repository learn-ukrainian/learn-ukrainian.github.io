#!/usr/bin/env python3
"""Validate l2-uk-direct manifest.yaml integrity and detect drift.

Checks:
1. manifest.yaml parses correctly
2. Each slug in sequence has a corresponding .yaml file
3. Extra .yaml files not in manifest are reported
4. Module count matches declared count
5. No duplicate slugs within or across levels

Usage:
  .venv/bin/python scripts/manifest_direct.py
  .venv/bin/python scripts/manifest_direct.py --level a1
  .venv/bin/python scripts/manifest_direct.py --fix   # add untracked files to manifest
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "curriculum/l2-uk-direct/manifest.yaml"
CURRICULUM_DIR = REPO_ROOT / "curriculum/l2-uk-direct"


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(2)
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_level(level: str, level_data: dict) -> tuple[list[str], list[str], list[str]]:
    """Check a single level. Returns (errors, warnings, info)."""
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    sequence = level_data.get("sequence", [])
    declared_count = level_data.get("modules")
    level_dir = CURRICULUM_DIR / level

    # Check declared count matches actual sequence
    if declared_count is not None and declared_count != len(sequence):
        errors.append(
            f"[{level}] declared modules: {declared_count}, actual sequence: {len(sequence)}"
        )

    # Check for duplicate slugs
    seen: dict[str, int] = {}
    for i, slug in enumerate(sequence):
        if slug in seen:
            errors.append(f"[{level}] duplicate slug '{slug}' at positions {seen[slug]} and {i}")
        seen[slug] = i

    # Check each slug has a file
    missing_files: list[str] = []
    for slug in sequence:
        yaml_path = level_dir / f"{slug}.yaml"
        if not yaml_path.exists():
            missing_files.append(slug)
            errors.append(f"[{level}] manifest entry '{slug}' has no file: {yaml_path.name}")

    # Check for extra files not in manifest
    manifest_slugs = set(sequence)
    extra_files: list[str] = []
    if level_dir.exists():
        for f in sorted(level_dir.glob("*.yaml")):
            slug = f.stem
            if slug not in manifest_slugs:
                extra_files.append(slug)
                warnings.append(f"[{level}] file '{f.name}' exists but not in manifest")

    # Status files without corresponding YAML
    if level_dir.exists():
        for f in sorted(level_dir.glob("*.status.json")):
            slug = f.stem.replace(".status", "")
            yaml_path = level_dir / f"{slug}.yaml"
            if not yaml_path.exists():
                warnings.append(f"[{level}] orphan status file '{f.name}' (no matching YAML)")

    info.append(f"[{level}] {len(sequence)} modules in manifest, {len(sequence) - len(missing_files)} files found")
    if extra_files:
        info.append(f"[{level}] {len(extra_files)} extra files: {', '.join(extra_files)}")

    return errors, warnings, info


def check_cross_level(manifest: dict) -> list[str]:
    """Check for slug collisions across levels."""
    errors: list[str] = []
    slug_to_level: dict[str, str] = {}
    for level, level_data in manifest.get("levels", {}).items():
        for slug in level_data.get("sequence", []):
            if slug in slug_to_level:
                errors.append(
                    f"slug '{slug}' appears in both {slug_to_level[slug]} and {level}"
                )
            slug_to_level[slug] = level
    return errors


def fix_manifest(manifest: dict, level_filter: str | None) -> bool:
    """Add untracked YAML files to manifest. Returns True if changes made."""
    changed = False
    for level, level_data in manifest.get("levels", {}).items():
        if level_filter and level != level_filter:
            continue
        level_dir = CURRICULUM_DIR / level
        if not level_dir.exists():
            continue
        sequence = level_data.get("sequence", [])
        manifest_slugs = set(sequence)
        for f in sorted(level_dir.glob("*.yaml")):
            slug = f.stem
            if slug not in manifest_slugs:
                sequence.append(slug)
                print(f"  + [{level}] added '{slug}' to end of sequence")
                changed = True
        if changed:
            level_data["modules"] = len(sequence)

    if changed:
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            yaml.dump(manifest, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"\nManifest updated: {MANIFEST_PATH}")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate l2-uk-direct manifest integrity.")
    parser.add_argument("--level", help="Check only this level (e.g. a1)")
    parser.add_argument("--fix", action="store_true", help="Add untracked YAML files to manifest")
    args = parser.parse_args()

    manifest = load_manifest()
    levels = manifest.get("levels", {})

    if args.fix:
        if fix_manifest(manifest, args.level):
            print("Run without --fix to verify.")
        else:
            print("No changes needed.")
        return

    all_errors: list[str] = []
    all_warnings: list[str] = []
    all_info: list[str] = []

    for level, level_data in levels.items():
        if args.level and level != args.level:
            continue
        errors, warnings, info = check_level(level, level_data)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
        all_info.extend(info)

    # Cross-level checks (only if checking all levels)
    if not args.level:
        cross_errors = check_cross_level(manifest)
        all_errors.extend(cross_errors)

    # Print results
    print("l2-uk-direct Manifest Check")
    print("=" * 50)

    for msg in all_info:
        print(f"  \u2139  {msg}")

    if all_warnings:
        print()
        for msg in all_warnings:
            print(f"  \u26A0  {msg}")

    if all_errors:
        print()
        for msg in all_errors:
            print(f"  \u2717  {msg}")

    print()
    if all_errors:
        total = sum(len(ld.get("sequence", [])) for ld in levels.values())
        print(f"\u274C FAIL — {len(all_errors)} error(s), {len(all_warnings)} warning(s) ({total} total modules)")
        sys.exit(1)
    else:
        total = sum(len(ld.get("sequence", [])) for ld in levels.values())
        print(f"\u2705 PASS — {total} modules across {len(levels)} levels, {len(all_warnings)} warning(s)")


if __name__ == "__main__":
    main()
