#!/usr/bin/env python3
"""
Fix activity_hints in seminar track plan files.

Removes forbidden grammar drill activity types and ensures seminar-style
activities are specified instead.

Seminar tracks: B2-HIST, C1-HIST, C1-BIO, LIT
"""

import sys
from pathlib import Path
import yaml

# Forbidden activity types for seminar tracks
FORBIDDEN_TYPES = {
    'quiz', 'fill-in', 'cloze', 'match-up', 'error-correction',
    'unjumble', 'mark-the-words', 'group-sort', 'select', 'translate', 'anagram'
}

# Allowed seminar-style activity types
ALLOWED_TYPES = {
    'reading', 'essay-response', 'critical-analysis', 'comparative-study',
    'authorial-intent', 'true-false', 'source-evaluation', 'debate'
}

# Seminar tracks
SEMINAR_TRACKS = ['b2-hist', 'c1-hist', 'c1-bio', 'lit']


def fix_activity_hints(plan_data: dict) -> tuple[bool, int]:
    """
    Fix activity_hints and activities in a plan file.

    Returns (was_modified, num_removed).
    """
    total_removed = 0
    was_modified = False

    # Process both 'activity_hints' and 'activities' keys
    for key in ['activity_hints', 'activities']:
        hints = plan_data.get(key, [])
        if not hints:
            continue

        original_count = len(hints)

        # Filter out forbidden types
        new_hints = []
        for hint in hints:
            if isinstance(hint, dict):
                hint_type = hint.get('type', '').lower()
                if hint_type not in FORBIDDEN_TYPES:
                    new_hints.append(hint)

        removed_count = original_count - len(new_hints)

        if removed_count > 0:
            plan_data[key] = new_hints
            total_removed += removed_count
            was_modified = True

    return was_modified, total_removed


def process_file(file_path: Path, dry_run: bool = False) -> tuple[bool, int, list[str]]:
    """
    Process a single plan file.

    Returns (was_modified, num_removed, removed_types).
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        plan_data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"  ⚠️ YAML error in {file_path.name}: {e}")
        return False, 0, []

    if not plan_data or not isinstance(plan_data, dict):
        return False, 0, []

    # Track which types were removed (check both keys)
    removed_types = []
    for key in ['activity_hints', 'activities']:
        hints = plan_data.get(key, [])
        for hint in hints:
            if isinstance(hint, dict):
                hint_type = hint.get('type', '').lower()
                if hint_type in FORBIDDEN_TYPES:
                    removed_types.append(hint_type)

    was_modified, num_removed = fix_activity_hints(plan_data)

    if was_modified and not dry_run:
        # Write back with preserved formatting
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(plan_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=120)

    return was_modified, num_removed, removed_types


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fix activity_hints in seminar track plan files")
    parser.add_argument('--dry-run', action='store_true', help="Show what would be changed without modifying files")
    parser.add_argument('--track', choices=SEMINAR_TRACKS, help="Process only a specific track")
    parser.add_argument('--verbose', '-v', action='store_true', help="Show details for each file")
    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    plans_dir = project_root / 'curriculum' / 'l2-uk-en' / 'plans'

    tracks_to_process = [args.track] if args.track else SEMINAR_TRACKS

    total_files = 0
    total_modified = 0
    total_removed = 0
    type_counts = {}

    for track in tracks_to_process:
        track_dir = plans_dir / track
        if not track_dir.exists():
            print(f"⚠️ Track directory not found: {track_dir}")
            continue

        plan_files = sorted(track_dir.glob('*.yaml'))
        track_modified = 0
        track_removed = 0

        print(f"\n{'='*60}")
        print(f"Processing {track.upper()} ({len(plan_files)} files)")
        print('='*60)

        for plan_file in plan_files:
            total_files += 1
            was_modified, num_removed, removed_types = process_file(plan_file, dry_run=args.dry_run)

            if was_modified:
                track_modified += 1
                track_removed += num_removed
                total_modified += 1
                total_removed += num_removed

                for rt in removed_types:
                    type_counts[rt] = type_counts.get(rt, 0) + 1

                if args.verbose:
                    print(f"  ✏️ {plan_file.name}: removed {num_removed} ({', '.join(removed_types)})")

        print(f"  Modified: {track_modified}/{len(plan_files)} files")
        print(f"  Removed: {track_removed} forbidden activity hints")

    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Total files processed: {total_files}")
    print(f"Files modified: {total_modified}")
    print(f"Activity hints removed: {total_removed}")

    if type_counts:
        print("\nRemoved types breakdown:")
        for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {t}: {count}")

    if args.dry_run:
        print("\n⚠️ DRY RUN - no files were modified")
        print("Run without --dry-run to apply changes")


if __name__ == '__main__':
    main()
