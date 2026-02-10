#!/usr/bin/env python3
"""
Sync module IDs across plan and meta YAMLs from curriculum.yaml (source of truth).

Module N = position N (1-indexed) in levels.{track}.modules array.

ID format:
  - Tracks with ≤99 modules:  {track}-{N}     (e.g. a1-39, lit-05)
  - Tracks with >99 modules:  {track}-{NNN}    (e.g. c1-bio-039, b2-hist-001)

Dry-run by default. Use --fix to apply changes.

Usage:
  .venv/bin/python scripts/sync_module_ids.py              # Audit all tracks
  .venv/bin/python scripts/sync_module_ids.py c1-bio       # Audit one track
  .venv/bin/python scripts/sync_module_ids.py c1-bio --fix # Fix one track
  .venv/bin/python scripts/sync_module_ids.py --fix        # Fix all tracks
"""

import argparse
import re
import sys
from pathlib import Path

from slug_utils import to_bare_slug

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"
CURRICULUM_YAML = CURRICULUM_DIR / "curriculum.yaml"
PLANS_DIR = CURRICULUM_DIR / "plans"

# Tracks where filenames use bare slugs (no numeric prefix)
SEMINAR_TRACKS = {"c1-bio", "b2-hist", "c1-hist", "lit", "oes", "ruth",
                  "b2-pro", "c1-pro"}


def load_curriculum():
    """Load curriculum.yaml and return {track: [slug, ...]} ordered arrays."""
    data = yaml.safe_load(CURRICULUM_YAML.read_text(encoding="utf-8"))
    tracks = {}
    for level, info in data.get("levels", {}).items():
        modules = info.get("modules", [])
        # Strip numeric prefix for core tracks: "39-buying-tickets" → "buying-tickets"
        slugs = [to_bare_slug(entry) for entry in modules]
        tracks[level] = {
            "slugs": slugs,
            "raw_entries": modules,
            "total": len(modules),
        }
    return tracks


def make_module_id(track, num, total):
    """Generate the canonical module ID string."""
    if total > 99:
        return f"{track}-{num:03d}"
    else:
        return f"{track}-{num:02d}"


def find_plan_file(track, slug, num=None):
    """Find the plan YAML for a slug (handles numeric-prefix filenames)."""
    plan_dir = PLANS_DIR / track

    # Seminar tracks: bare slug
    direct = plan_dir / f"{slug}.yaml"
    if direct.exists():
        return direct

    # Core tracks: {num}-{slug}.yaml — use exact number prefix if known
    if num is not None:
        numbered = plan_dir / f"{num:02d}-{slug}.yaml"
        if numbered.exists():
            return numbered

    # Fallback: glob but only match NN-{exact_slug}.yaml (not partial)
    matches = [p for p in plan_dir.glob(f"[0-9]*-{slug}.yaml")
               if re.match(rf"^\d+-{re.escape(slug)}\.yaml$", p.name)]
    if matches:
        return matches[0]

    return None


def find_meta_file(track, slug, num=None):
    """Find the meta YAML for a slug."""
    meta_dir = CURRICULUM_DIR / track / "meta"

    # Bare slug
    direct = meta_dir / f"{slug}.yaml"
    if direct.exists():
        return direct

    # Core tracks: {num}-{slug}.yaml — use exact number prefix if known
    if num is not None:
        numbered = meta_dir / f"{num:02d}-{slug}.yaml"
        if numbered.exists():
            return numbered

    # Fallback: glob but only match NN-{exact_slug}.yaml
    matches = [p for p in meta_dir.glob(f"[0-9]*-{slug}.yaml")
               if re.match(rf"^\d+-{re.escape(slug)}\.yaml$", p.name)]
    if matches:
        return matches[0]

    return None


def patch_yaml_field(filepath, field, new_value, dry_run=True):
    """Update a single field in a YAML file using regex (preserves formatting).

    Returns True if a change was made (or would be made in dry-run).
    """
    content = filepath.read_text(encoding="utf-8")

    # Match field at start of line: "module: old-value" or "sequence: 42"
    pattern = re.compile(rf"^({field}:\s*)(.+)$", re.MULTILINE)
    match = pattern.search(content)

    if match:
        old_value = match.group(2).strip().strip("'\"")
        str_new = str(new_value)

        if old_value == str_new:
            return False  # Already correct

        new_line = f"{match.group(1)}{str_new}"
        new_content = content[:match.start()] + new_line + content[match.end():]

        if not dry_run:
            filepath.write_text(new_content, encoding="utf-8")
        return True
    else:
        # Field doesn't exist — insert it after the --- header
        str_new = str(new_value)
        # Find the first non-comment, non-separator line
        lines = content.split("\n")
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip() == "---":
                insert_idx = i + 1
                continue
            if line.strip().startswith("#"):
                insert_idx = i + 1
                continue
            break

        lines.insert(insert_idx, f"{field}: {str_new}")
        new_content = "\n".join(lines)

        if not dry_run:
            filepath.write_text(new_content, encoding="utf-8")
        return True


def audit_track(track, track_data, fix=False):
    """Audit and optionally fix one track. Returns (changes, errors, missing)."""
    slugs = track_data["slugs"]
    total = track_data["total"]
    changes = []
    errors = []
    missing = []

    for i, slug in enumerate(slugs):
        num = i + 1
        expected_id = make_module_id(track, num, total)

        # --- Plan file ---
        plan_file = find_plan_file(track, slug, num)
        if plan_file:
            plan_data = yaml.safe_load(plan_file.read_text(encoding="utf-8"))
            if not isinstance(plan_data, dict):
                errors.append(f"  Plan {plan_file.name}: not a dict")
                continue

            # Check module field
            current_mod = str(plan_data.get("module", ""))
            if current_mod != expected_id:
                changes.append(f"  Plan {plan_file.name}: module {current_mod!r} → {expected_id!r}")
                patch_yaml_field(plan_file, "module", expected_id, dry_run=not fix)

            # Check sequence field
            current_seq = plan_data.get("sequence")
            if current_seq != num:
                changes.append(f"  Plan {plan_file.name}: sequence {current_seq!r} → {num}")
                patch_yaml_field(plan_file, "sequence", num, dry_run=not fix)
        else:
            missing.append(f"  Plan MISSING: {track}/{slug}.yaml (module {num})")

        # --- Meta file ---
        meta_file = find_meta_file(track, slug, num)
        if meta_file:
            meta_data = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
            if not isinstance(meta_data, dict):
                errors.append(f"  Meta {meta_file.name}: not a dict")
                continue

            # Check module field
            current_mod = str(meta_data.get("module", ""))
            if current_mod != expected_id:
                changes.append(f"  Meta {meta_file.name}: module {current_mod!r} → {expected_id!r}")
                patch_yaml_field(meta_file, "module", expected_id, dry_run=not fix)

            # Check id field
            current_id = str(meta_data.get("id", ""))
            if current_id != expected_id:
                changes.append(f"  Meta {meta_file.name}: id {current_id!r} → {expected_id!r}")
                patch_yaml_field(meta_file, "id", expected_id, dry_run=not fix)
        else:
            missing.append(f"  Meta MISSING: {track}/meta/{slug}.yaml (module {num})")

    return changes, errors, missing


def main():
    parser = argparse.ArgumentParser(description="Sync module IDs from curriculum.yaml")
    parser.add_argument("track", nargs="?", help="Specific track to audit (default: all)")
    parser.add_argument("--fix", action="store_true", help="Apply fixes (default: dry-run)")
    args = parser.parse_args()

    tracks = load_curriculum()

    if args.track:
        if args.track not in tracks:
            print(f"Track '{args.track}' not in curriculum.yaml.")
            print(f"Available: {', '.join(sorted(tracks.keys()))}")
            sys.exit(1)
        target_tracks = {args.track: tracks[args.track]}
    else:
        target_tracks = tracks

    mode = "FIX" if args.fix else "DRY-RUN"
    print(f"=== Module ID Sync ({mode}) ===\n")

    total_changes = 0
    total_missing = 0
    total_errors = 0

    for track_name in sorted(target_tracks):
        track_data = target_tracks[track_name]
        print(f"--- {track_name} ({track_data['total']} modules) ---")

        changes, errors, missing = audit_track(track_name, track_data, fix=args.fix)

        if changes:
            total_changes += len(changes)
            for c in changes[:20]:  # Show first 20
                print(c)
            if len(changes) > 20:
                print(f"  ... and {len(changes) - 20} more changes")
        if missing:
            total_missing += len(missing)
            for m in missing:
                print(m)
        if errors:
            total_errors += len(errors)
            for e in errors:
                print(e)
        if not changes and not missing and not errors:
            print("  All correct ✓")
        print()

    print(f"=== Summary ===")
    print(f"Changes: {total_changes} {'(applied)' if args.fix else '(dry-run, use --fix to apply)'}")
    print(f"Missing files: {total_missing}")
    print(f"Errors: {total_errors}")

    if total_changes > 0 and not args.fix:
        sys.exit(1)  # Non-zero exit for CI usage


if __name__ == "__main__":
    main()
