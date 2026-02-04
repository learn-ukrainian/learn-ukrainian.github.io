#!/usr/bin/env python3
"""
Extract track metrics from curriculum modules.

This script extracts all quantitative metrics from modules in a track
without any LLM calls. Output can be used for scoring or analysis.

Usage:
    python scripts/extract_track_metrics.py b2-hist
    python scripts/extract_track_metrics.py c1-bio --format json
    python scripts/extract_track_metrics.py --all
"""

import argparse
import json
import sys
from pathlib import Path
from dataclasses import asdict

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scoring.metrics import extract_all_module_metrics, ModuleMetrics
from scoring.aggregator import aggregate_track_metrics
from scoring.config import get_all_track_ids, get_track_config


def main():
    parser = argparse.ArgumentParser(
        description='Extract metrics from curriculum modules',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/extract_track_metrics.py b2-hist
    python scripts/extract_track_metrics.py c1-bio --format json
    python scripts/extract_track_metrics.py --all --format json > metrics.json
        """
    )

    parser.add_argument(
        'track',
        nargs='?',
        help='Track ID to extract metrics from (e.g., b2-hist, c1-bio, lit, a1)'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Extract metrics from all tracks'
    )

    parser.add_argument(
        '--format',
        choices=['console', 'json'],
        default='console',
        help='Output format (default: console)'
    )

    parser.add_argument(
        '--per-module',
        action='store_true',
        help='Output per-module metrics instead of aggregated'
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
    tracks = get_all_track_ids() if args.all else [args.track]

    all_results = {}

    for track_id in tracks:
        try:
            config = get_track_config(track_id)
        except ValueError as e:
            print(f"Warning: Skipping unknown track '{track_id}': {e}", file=sys.stderr)
            continue

        level_dir = curriculum_path / config['level_dir']
        if not level_dir.exists():
            print(f"Warning: Level directory not found for {track_id}: {level_dir}", file=sys.stderr)
            continue

        print(f"Extracting metrics for {track_id}...", file=sys.stderr)

        try:
            module_metrics = extract_all_module_metrics(curriculum_path, track_id)
            aggregated = aggregate_track_metrics(module_metrics, track_id)

            if args.per_module:
                # Convert to serializable format
                modules_data = []
                for m in module_metrics:
                    data = asdict(m)
                    modules_data.append(data)
                all_results[track_id] = {
                    'track_name': config['name'],
                    'modules': modules_data,
                }
            else:
                # Convert aggregated to dict
                all_results[track_id] = {
                    'track_name': config['name'],
                    'total_modules': aggregated.total_modules,
                    'modules_found': aggregated.modules_found,
                    'passing_modules': aggregated.passing_modules,
                    'failing_modules': aggregated.failing_modules,
                    'modules_with_activities': aggregated.modules_with_activities,
                    'modules_with_vocabulary': aggregated.modules_with_vocabulary,
                    'total_quote_callouts': aggregated.total_quote_callouts,
                    'avg_quote_callouts': aggregated.avg_quote_callouts,
                    'total_myth_buster_callouts': aggregated.total_myth_buster_callouts,
                    'avg_myth_buster_callouts': aggregated.avg_myth_buster_callouts,
                    'total_agency_markers': aggregated.total_agency_markers,
                    'agency_marker_ratio': aggregated.agency_marker_ratio,
                    'total_cross_references': aggregated.total_cross_references,
                    'avg_cross_references': aggregated.avg_cross_references,
                    'avg_citation_ratio': aggregated.avg_citation_ratio,
                    'total_analysis_sections': aggregated.total_analysis_sections,
                    'total_legacy_sections': aggregated.total_legacy_sections,
                    'avg_naturalness_score': aggregated.avg_naturalness_score,
                }

        except Exception as e:
            print(f"Error extracting metrics for {track_id}: {e}", file=sys.stderr)
            all_results[track_id] = {'error': str(e)}

    # Output results
    if args.format == 'json':
        print(json.dumps(all_results, indent=2, ensure_ascii=False))
    else:
        for track_id, data in all_results.items():
            print(f"\n{'='*60}")
            print(f"Track: {track_id}")
            print(f"{'='*60}")

            if 'error' in data:
                print(f"Error: {data['error']}")
                continue

            if args.per_module:
                print(f"Modules: {len(data['modules'])}")
                for m in data['modules'][:5]:  # Show first 5
                    print(f"  - {m['module_slug']}: quotes={m['quote_callouts']}, xrefs={m['cross_references']}")
                if len(data['modules']) > 5:
                    print(f"  ... and {len(data['modules']) - 5} more")
            else:
                print(f"Modules: {data['modules_found']}/{data['total_modules']}")
                print(f"Passing: {data['passing_modules']}")
                print(f"Quotes: {data['total_quote_callouts']} (avg: {data['avg_quote_callouts']:.2f})")
                print(f"Myth-busters: {data['total_myth_buster_callouts']} (avg: {data['avg_myth_buster_callouts']:.2f})")
                print(f"Cross-refs: {data['total_cross_references']} (avg: {data['avg_cross_references']:.2f})")
                print(f"Agency ratio: {data['agency_marker_ratio']:.2%}")


if __name__ == '__main__':
    main()
