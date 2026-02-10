#!/usr/bin/env python3
"""
One-shot migration: standardize review/audit/status file paths.

Actions:
  1. Move *-review.md and *-llm-review.md from audit/ → review/{bare_slug}-review.md
  2. Rename *-audit-report.md → {bare_slug}-audit.md
  3. Rename numbered status/*.json → {bare_slug}.json (update "module" field inside)
  4. Rename numbered audit artifacts (grammar, quality) → bare slug

Usage:
    .venv/bin/python scripts/migrate_audit_review_paths.py --dry-run
    .venv/bin/python scripts/migrate_audit_review_paths.py --apply

Safety:
  - Refuses to run if batch_state/lock exists
  - --dry-run is default (must pass --apply to actually move files)
  - Handles duplicates: keeps newest mtime
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from slug_utils import to_bare_slug

CURRICULUM_DIR = Path(__file__).parent.parent / "curriculum" / "l2-uk-en"

# All track directories to process
TRACK_DIRS = [
    d for d in CURRICULUM_DIR.iterdir()
    if d.is_dir() and d.name not in ("plans", "__pycache__")
]


def check_batch_lock():
    """Refuse to run if a batch is active."""
    lock_file = Path(__file__).parent.parent / "batch_state" / "lock"
    if lock_file.exists():
        print("ERROR: batch_state/lock exists. A batch is in progress.")
        print("Wait for the batch to complete or remove the lock file manually.")
        sys.exit(1)


def move_reviews(track_dir: Path, dry_run: bool) -> list[str]:
    """Move *-review.md files from audit/ to review/."""
    actions = []
    audit_dir = track_dir / "audit"
    review_dir = track_dir / "review"

    if not audit_dir.exists():
        return actions

    for f in sorted(audit_dir.iterdir()):
        if not f.name.endswith("-review.md"):
            continue

        # Determine bare slug from the review filename
        name = f.name
        if name.endswith("-llm-review.md"):
            slug_part = name[:-len("-llm-review.md")]
        else:
            slug_part = name[:-len("-review.md")]

        bare = to_bare_slug(slug_part)
        dest = review_dir / f"{bare}-review.md"

        if dest.exists() and f.exists():
            # Keep the one with newer mtime
            if f.stat().st_mtime > dest.stat().st_mtime:
                action = f"OVERWRITE {f} → {dest} (source is newer)"
                if not dry_run:
                    review_dir.mkdir(parents=True, exist_ok=True)
                    dest.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
                    f.unlink()
            else:
                action = f"DELETE {f} (dest is newer, keeping {dest})"
                if not dry_run:
                    f.unlink()
        else:
            action = f"MOVE {f} → {dest}"
            if not dry_run:
                review_dir.mkdir(parents=True, exist_ok=True)
                f.rename(dest)

        actions.append(action)

    return actions


def rename_audit_reports(track_dir: Path, dry_run: bool) -> list[str]:
    """Rename *-audit-report.md → {bare_slug}-audit.md."""
    actions = []
    audit_dir = track_dir / "audit"

    if not audit_dir.exists():
        return actions

    for f in sorted(audit_dir.iterdir()):
        if not f.name.endswith("-audit-report.md"):
            continue

        slug_part = f.name[:-len("-audit-report.md")]
        bare = to_bare_slug(slug_part)
        dest = audit_dir / f"{bare}-audit.md"

        if f == dest:
            continue  # Already correct

        if dest.exists():
            # Keep newer
            if f.stat().st_mtime > dest.stat().st_mtime:
                action = f"OVERWRITE {f.name} → {dest.name} (source is newer)"
                if not dry_run:
                    f.rename(dest)
            else:
                action = f"DELETE {f.name} (dest {dest.name} is newer)"
                if not dry_run:
                    f.unlink()
        else:
            action = f"RENAME {f.name} → {dest.name}"
            if not dry_run:
                f.rename(dest)

        actions.append(action)

    return actions


def rename_audit_artifacts(track_dir: Path, dry_run: bool) -> list[str]:
    """Rename numbered audit artifacts (grammar, quality) to bare slug."""
    actions = []
    audit_dir = track_dir / "audit"

    if not audit_dir.exists():
        return actions

    for f in sorted(audit_dir.iterdir()):
        if not f.is_file():
            continue

        # Only process numbered files
        stem = f.stem
        bare = to_bare_slug(stem)
        if bare == stem:
            continue  # Already bare

        # Reconstruct filename with bare slug
        dest = audit_dir / f"{bare}{f.suffix}"

        if f.name.endswith("-grammar.yaml") or f.name.endswith("-quality.md"):
            if dest.exists():
                if f.stat().st_mtime > dest.stat().st_mtime:
                    action = f"OVERWRITE {f.name} → {dest.name}"
                    if not dry_run:
                        f.rename(dest)
                else:
                    action = f"DELETE {f.name} (dest newer)"
                    if not dry_run:
                        f.unlink()
            else:
                action = f"RENAME {f.name} → {dest.name}"
                if not dry_run:
                    f.rename(dest)

            actions.append(action)

    return actions


def rename_status_files(track_dir: Path, dry_run: bool) -> list[str]:
    """Rename numbered status/*.json → {bare_slug}.json and update 'module' field."""
    actions = []
    status_dir = track_dir / "status"

    if not status_dir.exists():
        return actions

    for f in sorted(status_dir.iterdir()):
        if not f.name.endswith(".json"):
            continue

        stem = f.stem
        bare = to_bare_slug(stem)
        if bare == stem:
            continue  # Already bare slug

        dest = status_dir / f"{bare}.json"

        if dest.exists():
            # Keep newer, update module field in survivor
            if f.stat().st_mtime > dest.stat().st_mtime:
                action = f"OVERWRITE {f.name} → {dest.name} (update module field)"
                if not dry_run:
                    _update_status_module_field(f, bare)
                    f.rename(dest)
            else:
                action = f"DELETE {f.name} (dest {dest.name} is newer)"
                if not dry_run:
                    _update_status_module_field(dest, bare)
                    f.unlink()
        else:
            action = f"RENAME {f.name} → {dest.name} (update module field)"
            if not dry_run:
                _update_status_module_field(f, bare)
                f.rename(dest)

        actions.append(action)

    return actions


def _update_status_module_field(json_path: Path, bare_slug: str):
    """Update the 'module' field inside a status JSON to bare slug."""
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        if data.get("module") != bare_slug:
            data["module"] = bare_slug
            json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except (json.JSONDecodeError, IOError):
        pass  # Skip corrupted files


def main():
    parser = argparse.ArgumentParser(description="Migrate audit/review/status file paths")
    parser.add_argument("--apply", action="store_true", help="Actually move/rename files (default is dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done (default)")
    parser.add_argument("--track", help="Only process this track (e.g., 'a1', 'b2-hist')")
    args = parser.parse_args()

    dry_run = not args.apply

    if dry_run:
        print("=== DRY RUN (pass --apply to execute) ===\n")
    else:
        check_batch_lock()
        print("=== APPLYING CHANGES ===\n")

    tracks = TRACK_DIRS
    if args.track:
        tracks = [CURRICULUM_DIR / args.track]
        if not tracks[0].exists():
            print(f"ERROR: Track directory not found: {tracks[0]}")
            sys.exit(1)

    total_actions = 0
    for track_dir in sorted(tracks):
        if not track_dir.is_dir():
            continue

        track_actions = []
        track_actions.extend(move_reviews(track_dir, dry_run))
        track_actions.extend(rename_audit_reports(track_dir, dry_run))
        track_actions.extend(rename_audit_artifacts(track_dir, dry_run))
        track_actions.extend(rename_status_files(track_dir, dry_run))

        if track_actions:
            print(f"[{track_dir.name}] {len(track_actions)} actions:")
            for a in track_actions:
                print(f"  {a}")
            print()
            total_actions += len(track_actions)

    print(f"Total: {total_actions} actions")
    if dry_run and total_actions > 0:
        print("\nRun with --apply to execute these changes.")


if __name__ == "__main__":
    main()
