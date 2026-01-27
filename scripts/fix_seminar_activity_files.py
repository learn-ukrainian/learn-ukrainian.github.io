#!/usr/bin/env python3
"""
Fix activity YAML files in seminar tracks.

Removes forbidden grammar drill activity types from actual activity files
(not plans, but the curriculum/l2-uk-en/{level}/activities/*.yaml files).

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

# Seminar tracks
SEMINAR_TRACKS = ['b2-hist', 'c1-hist', 'c1-bio', 'lit']


def fix_activities(activities: list) -> tuple[list, int, list[str]]:
    """
    Remove forbidden activity types from activity list.

    Returns (new_activities, num_removed, removed_types).
    """
    if not activities or not isinstance(activities, list):
        return activities, 0, []

    new_activities = []
    removed_types = []

    for activity in activities:
        if isinstance(activity, dict):
            activity_type = activity.get('type', '').lower()
            if activity_type in FORBIDDEN_TYPES:
                removed_types.append(activity_type)
            else:
                new_activities.append(activity)
        else:
            new_activities.append(activity)

    return new_activities, len(removed_types), removed_types


def process_file(file_path: Path, dry_run: bool = False) -> tuple[bool, int, list[str]]:
    """
    Process a single activity file.

    Returns (was_modified, num_removed, removed_types).
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        activities = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"  YAML error in {file_path.name}: {e}")
        return False, 0, []

    if not activities:
        return False, 0, []

    # Activity files should be a bare list at root
    if isinstance(activities, list):
        new_activities, num_removed, removed_types = fix_activities(activities)

        if num_removed > 0 and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(new_activities, f, allow_unicode=True, sort_keys=False,
                         default_flow_style=False, width=120)

        return num_removed > 0, num_removed, removed_types

    # Some files might have activities wrapped in a dict (shouldn't happen but check)
    elif isinstance(activities, dict) and 'activities' in activities:
        new_activities, num_removed, removed_types = fix_activities(activities['activities'])

        if num_removed > 0 and not dry_run:
            activities['activities'] = new_activities
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(activities, f, allow_unicode=True, sort_keys=False,
                         default_flow_style=False, width=120)

        return num_removed > 0, num_removed, removed_types

    return False, 0, []


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fix activity files in seminar tracks")
    parser.add_argument('--dry-run', action='store_true', help="Show what would be changed without modifying files")
    parser.add_argument('--track', choices=SEMINAR_TRACKS, help="Process only a specific track")
    parser.add_argument('--verbose', '-v', action='store_true', help="Show details for each file")
    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    curriculum_dir = project_root / 'curriculum' / 'l2-uk-en'

    tracks_to_process = [args.track] if args.track else SEMINAR_TRACKS

    total_files = 0
    total_modified = 0
    total_removed = 0
    type_counts = {}

    for track in tracks_to_process:
        activities_dir = curriculum_dir / track / 'activities'
        if not activities_dir.exists():
            print(f"Activities directory not found: {activities_dir}")
            continue

        activity_files = sorted(activities_dir.glob('*.yaml'))
        track_modified = 0
        track_removed = 0

        print(f"\n{'='*60}")
        print(f"Processing {track.upper()} ({len(activity_files)} files)")
        print('='*60)

        for activity_file in activity_files:
            total_files += 1
            was_modified, num_removed, removed_types = process_file(activity_file, dry_run=args.dry_run)

            if was_modified:
                track_modified += 1
                track_removed += num_removed
                total_modified += 1
                total_removed += num_removed

                for rt in removed_types:
                    type_counts[rt] = type_counts.get(rt, 0) + 1

                if args.verbose:
                    print(f"  {activity_file.name}: removed {num_removed} ({', '.join(removed_types)})")

        print(f"  Modified: {track_modified}/{len(activity_files)} files")
        print(f"  Removed: {track_removed} forbidden activities")

    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Total files processed: {total_files}")
    print(f"Files modified: {total_modified}")
    print(f"Activities removed: {total_removed}")

    if type_counts:
        print("\nRemoved types breakdown:")
        for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {t}: {count}")

    if args.dry_run:
        print("\nDRY RUN - no files were modified")
        print("Run without --dry-run to apply changes")


if __name__ == '__main__':
    main()
