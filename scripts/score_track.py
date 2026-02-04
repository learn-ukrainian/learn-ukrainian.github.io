#!/usr/bin/env python3
"""
Score curriculum tracks with automated verification.

This script calculates objective 10/10 scores for curriculum tracks
using automated metric extraction. No LLM calls required.

Usage:
    python scripts/score_track.py b2-hist
    python scripts/score_track.py c1-bio --format markdown
    python scripts/score_track.py --all
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.metrics import extract_all_module_metrics
from scoring.aggregator import aggregate_track_metrics, calculate_track_score
from scoring.report import generate_track_report
from scoring.config import get_all_track_ids, get_track_config


def score_single_track(curriculum_path: Path, track_id: str, output_format: str) -> dict:
    """
    Score a single track and return results.

    Args:
        curriculum_path: Path to curriculum directory
        track_id: Track identifier
        output_format: 'console' or 'markdown'

    Returns:
        Dictionary with scoring results
    """
    config = get_track_config(track_id)
    level_dir = curriculum_path / config['level_dir']

    if not level_dir.exists():
        return {
            'track_id': track_id,
            'error': f"Level directory not found: {level_dir}",
        }

    # Extract metrics
    module_metrics = extract_all_module_metrics(curriculum_path, track_id)

    # Aggregate metrics
    track_metrics = aggregate_track_metrics(module_metrics, track_id)

    # Calculate score
    track_score = calculate_track_score(track_metrics, track_id)

    # Generate report
    report = generate_track_report(track_metrics, track_score, output_format)

    return {
        'track_id': track_id,
        'track_name': config['name'],
        'modules_found': track_metrics.modules_found,
        'total_modules': track_metrics.total_modules,
        'final_score': track_score.total_weighted_score,
        'criterion_scores': track_score.final_criterion_scores,
        'caps_applied': len(track_score.caps_applied),
        'report': report,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Score curriculum tracks with automated verification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/score_track.py b2-hist
    python scripts/score_track.py c1-bio --format markdown > c1-bio-score.md
    python scripts/score_track.py --all --summary

Valid track IDs:
    Specialized tracks: b2-hist, c1-hist, c1-bio, lit
    Standard tracks: a1, a2, b1, b2, c1, c2
        """
    )

    parser.add_argument(
        'track',
        nargs='?',
        help='Track ID to score (e.g., b2-hist, c1-bio, lit, a1)'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Score all tracks'
    )

    parser.add_argument(
        '--format',
        choices=['console', 'markdown'],
        default='console',
        help='Output format (default: console)'
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary table instead of full report'
    )

    args = parser.parse_args()

    if not args.track and not args.all:
        parser.error("Either specify a track ID or use --all")

    # Determine curriculum path
    script_dir = Path(__file__).parent
    curriculum_path = script_dir.parent / 'curriculum' / 'l2-uk-en'

    if not curriculum_path.exists():
        print(f"Error: Curriculum path not found: {curriculum_path}", file=sys.stderr)
        sys.exit(1)

    # Get tracks to process
    if args.all:
        # Process specialized tracks first, then standard
        specialized = ['b2-hist', 'c1-bio', 'c1-hist', 'lit']
        standard = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']
        tracks = specialized + standard
    else:
        tracks = [args.track]

    results = []

    for track_id in tracks:
        try:
            config = get_track_config(track_id)
        except ValueError as e:
            print(f"Warning: Unknown track '{track_id}': {e}", file=sys.stderr)
            continue

        level_dir = curriculum_path / config['level_dir']
        if not level_dir.exists():
            print(f"Warning: Skipping {track_id} - directory not found", file=sys.stderr)
            continue

        print(f"Scoring {track_id}...", file=sys.stderr)

        try:
            result = score_single_track(curriculum_path, track_id, args.format)
            results.append(result)
        except Exception as e:
            print(f"Error scoring {track_id}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            results.append({
                'track_id': track_id,
                'error': str(e),
            })

    # Output results
    if args.summary:
        print_summary_table(results)
    else:
        for result in results:
            if 'error' in result:
                print(f"\nError for {result['track_id']}: {result['error']}")
            else:
                print(result['report'])


def print_summary_table(results: list[dict]):
    """Print summary table of all track scores."""
    print()
    print("=" * 70)
    print("  TRACK SCORING SUMMARY")
    print("=" * 70)
    print()
    print("┌───────────────────────────────┬──────────┬──────────┬──────────┐")
    print("│ Track                         │ Modules  │ Score    │ Caps     │")
    print("├───────────────────────────────┼──────────┼──────────┼──────────┤")

    total_score = 0
    count = 0

    for result in results:
        if 'error' in result:
            print(f"│ {result['track_id']:<29} │ {'ERROR':^8} │ {'—':^8} │ {'—':^8} │")
        else:
            track_name = result.get('track_name', result['track_id'])[:29]
            modules = f"{result['modules_found']}/{result['total_modules']}"
            score = f"{result['final_score']:.2f}/10"
            caps = str(result['caps_applied'])
            print(f"│ {track_name:<29} │ {modules:^8} │ {score:^8} │ {caps:^8} │")
            total_score += result['final_score']
            count += 1

    print("├───────────────────────────────┼──────────┼──────────┼──────────┤")

    if count > 0:
        avg_score = total_score / count
        print(f"│ {'AVERAGE':<29} │ {'':^8} │ {f'{avg_score:.2f}/10':^8} │ {'':^8} │")

    print("└───────────────────────────────┴──────────┴──────────┴──────────┘")
    print()


if __name__ == '__main__':
    main()
