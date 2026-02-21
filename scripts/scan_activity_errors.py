#!/usr/bin/env python3
"""
Batch scanner for structural activity errors across all tracks.

Finds all activities/*.yaml files and runs the 5 structural correctness
checks that audit/core.py now enforces, then reports a summary.

Usage:
    .venv/bin/python scripts/scan_activity_errors.py
    .venv/bin/python scripts/scan_activity_errors.py --track b2
    .venv/bin/python scripts/scan_activity_errors.py --track b2 b2-hist c1-bio
    .venv/bin/python scripts/scan_activity_errors.py --fix-report   # output fixable errors only
"""

import sys
import argparse
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from yaml_activities import ActivityParser
from audit.checks.activity_validation import (
    check_select_min_correct,
    check_quiz_single_correct,
    check_fill_in_answer_in_options,
    check_translate_single_correct,
    check_mark_the_words_answers_in_text,
)

# All known tracks (directories under curriculum/l2-uk-en/)
ALL_TRACKS = [
    'a1', 'a2', 'b1', 'b2', 'c1', 'c2',
    'b2-hist', 'b2-pro', 'c1-bio', 'c1-hist', 'c1-pro',
    'lit', 'oes', 'ruth',
]

CURRICULUM_ROOT = PROJECT_ROOT / 'curriculum' / 'l2-uk-en'


def scan_file(yaml_path: Path) -> list[dict]:
    """Run all 5 structural checks on a single activities YAML file."""
    try:
        parser = ActivityParser()
        activities = parser.parse(yaml_path)
    except Exception as e:
        return [{'file': str(yaml_path), 'type': 'PARSE_ERROR',
                 'severity': 'critical', 'activity': '', 'message': str(e), 'suggestion': 'Fix YAML syntax'}]

    violations = []
    for v in (
        check_select_min_correct(activities)
        + check_quiz_single_correct(activities)
        + check_fill_in_answer_in_options(activities)
        + check_translate_single_correct(activities)
        + check_mark_the_words_answers_in_text(activities)
    ):
        v['file'] = str(yaml_path.relative_to(PROJECT_ROOT))
        violations.append(v)

    return violations


def scan_track(track: str) -> list[dict]:
    """Scan all activities YAML files in a track."""
    track_dir = CURRICULUM_ROOT / track / 'activities'
    if not track_dir.exists():
        return []
    return [v for f in sorted(track_dir.glob('*.yaml')) for v in scan_file(f)]


def main():
    parser = argparse.ArgumentParser(description='Scan activity YAML files for structural errors')
    parser.add_argument('--track', nargs='+', metavar='TRACK', help='Tracks to scan (default: all)')
    parser.add_argument('--fix-report', action='store_true', help='Show only critical fixable errors')
    args = parser.parse_args()

    tracks = args.track if args.track else ALL_TRACKS

    all_violations: list[dict] = []
    track_counts: dict[str, int] = {}

    for track in tracks:
        violations = scan_track(track)
        track_counts[track] = len(violations)
        all_violations.extend(violations)

    if not all_violations:
        print('✅ No structural activity errors found across all scanned tracks.')
        return 0

    # Group by error type
    by_type: dict[str, list[dict]] = {}
    for v in all_violations:
        by_type.setdefault(v['type'], []).append(v)

    print(f'\n{"="*70}')
    print(f'  Activity Structural Error Scan — {len(all_violations)} issue(s)')
    print(f'{"="*70}\n')

    # Summary by track
    print('Issues by track:')
    for track in tracks:
        count = track_counts.get(track, 0)
        if count:
            print(f'  {track:20s}  {count} issue(s)')
    print()

    # Summary by type
    print('Issues by type:')
    type_labels = {
        'SELECT_MIN_CORRECT_MISMATCH': 'select min_correct mismatch',
        'QUIZ_CORRECT_COUNT':          'quiz wrong correct count',
        'FILL_IN_ANSWER_NOT_IN_OPTIONS': 'fill-in answer not in options',
        'TRANSLATE_CORRECT_COUNT':     'translate wrong correct count',
        'MARK_THE_WORDS_ANSWER_NOT_IN_TEXT': 'mark-the-words answer not in text',
        'PARSE_ERROR':                 'YAML parse error',
    }
    for err_type, viols in sorted(by_type.items()):
        label = type_labels.get(err_type, err_type)
        print(f'  {label:45s}  {len(viols):3d}')
    print()

    # Detailed errors
    print('Detailed errors:')
    print('-' * 70)
    for v in all_violations:
        sev = '🔴' if v['severity'] == 'critical' else '⚠️ '
        print(f"{sev} [{v['type']}]")
        print(f"   File    : {v['file']}")
        print(f"   Activity: {v.get('activity', '')}")
        print(f"   Issue   : {v['message']}")
        print(f"   Fix     : {v['suggestion']}")
        print()

    return 1 if any(v['severity'] == 'critical' for v in all_violations) else 0


if __name__ == '__main__':
    sys.exit(main())
