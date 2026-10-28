#!/usr/bin/env python3
"""
Batch scanner for structural activity errors across all tracks.

Finds activity YAML in both activities/<slug>.yaml and <slug>/activities.yaml
layouts, runs the existing structural checks, and reports coverage.

Usage:
    .venv/bin/python scripts/audit/scan_activity_errors.py
    .venv/bin/python scripts/audit/scan_activity_errors.py --track a1-v1
    .venv/bin/python scripts/audit/scan_activity_errors.py --track b2 hist bio
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from audit.checks.activity_validation import (
    check_activity_intentional_error_leak,
    check_duplicate_options,
    check_fill_in_answer_in_options,
    check_fill_in_blank_formatting,
    check_indeclinable_case_drills,
    check_mark_the_words_answers_in_text,
    check_quiz_single_correct,
    check_select_min_correct,
    check_translate_single_correct,
)
from yaml_activities import ActivityParser

# All known tracks (directories under curriculum/l2-uk-en/)
ALL_TRACKS = [
    "a1",
    "a1-v1",
    "a2",
    "b1",
    "b2",
    "c1",
    "c2",
    "hist",
    "bio",
    "istorio",
    "lit",
    "oes",
    "ruth",
]

CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"


def scan_file(yaml_path: Path) -> list[dict]:
    """Run structural and semantic correctness checks on a single activities YAML file."""
    try:
        parser = ActivityParser()
        activities = parser.parse(yaml_path)
    except Exception as e:
        return [
            {
                "file": str(yaml_path),
                "type": "PARSE_ERROR",
                "severity": "critical",
                "activity": "",
                "message": str(e),
                "suggestion": "Fix YAML syntax",
            }
        ]

    violations = []
    for v in (
        check_select_min_correct(activities)
        + check_quiz_single_correct(activities)
        + check_fill_in_answer_in_options(activities)
        + check_fill_in_blank_formatting(activities)
        + check_translate_single_correct(activities)
        + check_mark_the_words_answers_in_text(activities)
        + check_duplicate_options(activities)
        + check_indeclinable_case_drills(activities)
        + check_activity_intentional_error_leak(activities)
    ):
        v["file"] = str(yaml_path.relative_to(PROJECT_ROOT))
        violations.append(v)

    return violations


def _activity_files(track: str) -> list[Path]:
    track_dir = CURRICULUM_ROOT / track
    return sorted(set((track_dir / "activities").glob("*.yaml")) | set(track_dir.glob("*/activities.yaml")))


def scan_track(track: str) -> list[dict]:
    """Scan both published layouts; missing input is not a clean result."""
    files = _activity_files(track)
    if not files:
        return [{
            "file": str((CURRICULUM_ROOT / track).relative_to(PROJECT_ROOT)),
            "type": "SCAN_INPUT_ERROR",
            "severity": "critical",
            "activity": "",
            "message": f"No activity YAML files found for track {track!r}",
            "suggestion": "Check the track name and materialize its curriculum files before scanning",
        }]
    return [v for f in files for v in scan_file(f)]


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Scan both published activity YAML layouts for structural errors. "
            "Use for structural auditing, not source-backed Ukrainian language review."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/audit/scan_activity_errors.py --track a1-v1\n"
            "  .venv/bin/python scripts/audit/scan_activity_errors.py --track b2 hist bio\n"
            "Outputs: coverage and violations on stdout; no files written.\n"
            "Exit codes: 0 no critical structural violations; 1 critical violations or missing input; "
            "2 invalid arguments.\n"
            "Related: #8893; scripts/audit/checks/activity_validation.py"
        ),
    )
    parser.add_argument("--track", nargs="+", metavar="TRACK", help="Tracks to scan, e.g. a1-v1 (default: all known tracks)")
    parser.add_argument("--fix-report", action="store_true", help="Show only critical violations (default: show all)")
    args = parser.parse_args()

    tracks = args.track if args.track else ALL_TRACKS

    all_violations: list[dict] = []
    track_counts: dict[str, int] = {}

    for track in tracks:
        violations = scan_track(track)
        track_counts[track] = len(violations)
        all_violations.extend(violations)

    print(f"Scanned {sum(len(_activity_files(track)) for track in tracks)} activity file(s) across {len(tracks)} track(s).")
    print("Structural checks do not verify Ukrainian answer ambiguity or option validity.")

    if not all_violations:
        print("✅ No structural activity errors found across all scanned tracks.")
        return 0

    # Group by error type
    by_type: dict[str, list[dict]] = {}
    for v in all_violations:
        by_type.setdefault(v["type"], []).append(v)

    print(f"\n{'=' * 70}")
    print(f"  Activity Structural Error Scan — {len(all_violations)} issue(s)")
    print(f"{'=' * 70}\n")

    # Summary by track
    print("Issues by track:")
    for track in tracks:
        count = track_counts.get(track, 0)
        if count:
            print(f"  {track:20s}  {count} issue(s)")
    print()

    # Summary by type
    print("Issues by type:")
    type_labels = {
        "SCAN_INPUT_ERROR": "no activity files found",
        "SELECT_MIN_CORRECT_MISMATCH": "select min_correct mismatch",
        "QUIZ_CORRECT_COUNT": "quiz wrong correct count",
        "FILL_IN_ANSWER_NOT_IN_OPTIONS": "fill-in answer not in options",
        "FILL_IN_MISSING_BLANK": "fill-in missing blank marker",
        "FILL_IN_EMPTY_SENTENCE": "fill-in empty sentence",
        "FILL_IN_MULTIPLE_BLANKS": "fill-in multiple ambiguous blanks",
        "TRANSLATE_CORRECT_COUNT": "translate wrong correct count",
        "MARK_THE_WORDS_ANSWER_NOT_IN_TEXT": "mark-the-words answer not in text",
        "DUPLICATE_OPTIONS": "duplicate options",
        "INDECLINABLE_CASE_DRILL": "indeclinable case drill",
        "INTENTIONAL_ERROR_LEAK": "intentional error leak without error typing",
        "PARSE_ERROR": "YAML parse error",
    }
    for err_type, viols in sorted(by_type.items()):
        label = type_labels.get(err_type, err_type)
        print(f"  {label:45s}  {len(viols):3d}")
    print()

    # Detailed errors
    print("Detailed errors:")
    print("-" * 70)
    for v in all_violations:
        if args.fix_report and v["severity"] != "critical":
            continue
        sev = "🔴" if v["severity"] == "critical" else "⚠️ "
        print(f"{sev} [{v['type']}]")
        print(f"   File    : {v['file']}")
        print(f"   Activity: {v.get('activity', '')}")
        print(f"   Issue   : {v['message']}")
        print(f"   Fix     : {v['suggestion']}")
        print()

    return 1 if any(v["severity"] == "critical" for v in all_violations) else 0


if __name__ == "__main__":
    sys.exit(main())
