#!/usr/bin/env python3
"""Research quality assessment and upgrade pipeline.

Workflow (run in order):
  1. Assess:   .venv/bin/python scripts/assess_research.py a1
  2. Upgrade:  .venv/bin/python scripts/assess_research.py a1 --upgrade
  3. Enrich:   .venv/bin/python scripts/assess_research.py a1 --enrich
  4. Refresh:  .venv/bin/python scripts/assess_research.py a1 --refresh

Other:
  .venv/bin/python scripts/assess_research.py a1 5             # single module detail
  .venv/bin/python scripts/assess_research.py a1 --gaps        # only modules with gaps
  .venv/bin/python scripts/assess_research.py --all            # all tracks overview
  .venv/bin/python scripts/assess_research.py a1 --json        # JSON output
  .venv/bin/python scripts/assess_research.py a1 --coverage    # research coverage gaps
  .venv/bin/python scripts/assess_research.py --all --coverage # full curriculum coverage

Flags:
  --dry-run       Preview what would be done (works with --upgrade, --refresh)
  --min-score N   Score threshold (default: 9)
  --coverage      Show research coverage gaps (manifest modules vs research files)
  --strict        With --coverage, exit 1 if any gaps found (for CI)
"""

import argparse
import json
import sys
from pathlib import Path

# Add scripts/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml
from research_quality import (
    assess_research_compat,
    find_research_path,
    get_rubric,
)

# Import helpers — all rendering, queue processing, and coverage logic
from assess_research_helpers import (
    _build_refresh_queue,
    _build_upgrade_queue,
    _colored,
    _compute_all_coverage,
    _coverage_for_track as _coverage_for_track_impl,
    _parse_slug_entry,
    _render_all_coverage,
    _render_all_overview,
    _render_coverage_only,
    _render_coverage_table,
    _render_quality_table,
    _render_refresh_queue,
    _render_single_module,
    _render_upgrade_queue,
    BOLD,
    COLORS,
    DIM,
    GREEN,
    RED,
    RESET,
)
from assess_research_queue import (
    _is_plan_already_enriched,
    _process_enrich_plans,
    _process_refresh_queue,
    _process_upgrade_queue,
)


def _clear_v3_phase_a(track_id: str, slug: str) -> bool:
    """Clear Phase A from state-v3.json so build_module re-runs it with improved research."""
    orch_dir = CURRICULUM_ROOT / track_id / "orchestration" / slug
    state_file = orch_dir / "state-v3.json"
    if not state_file.exists():
        return False
    try:
        state = json.loads(state_file.read_text("utf-8"))
        phases = state.get("phases", {})
        cleared = phases.pop("v3-A", None)
        if cleared is not None:
            state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), "utf-8")
            return True
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Could not clear v3 phase A for {track_id}/{slug}: {e}", file=sys.stderr)
    return False


# Project paths
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"

# Track config
TRACKS = [
    {"id": "a1", "name": "A1", "path": "a1"},
    {"id": "a2", "name": "A2", "path": "a2"},
    {"id": "b1", "name": "B1", "path": "b1"},
    {"id": "b2", "name": "B2", "path": "b2"},
    {"id": "b2-pro", "name": "B2-PRO", "path": "b2-pro"},
    {"id": "c1", "name": "C1", "path": "c1"},
    {"id": "c1-pro", "name": "C1-PRO", "path": "c1-pro"},
    {"id": "c2", "name": "C2", "path": "c2"},
    {"id": "hist", "name": "HIST", "path": "hist"},
    {"id": "istorio", "name": "ISTORIO", "path": "istorio"},
    {"id": "bio", "name": "BIO", "path": "bio"},
    {"id": "lit", "name": "LIT", "path": "lit"},
    {"id": "lit-essay", "name": "LIT-ESSAY", "path": "lit-essay"},
    {"id": "lit-fantastika", "name": "LIT-FANTASTIKA", "path": "lit-fantastika"},
    {"id": "lit-hist-fic", "name": "LIT-HIST-FIC", "path": "lit-hist-fic"},
    {"id": "lit-humor", "name": "LIT-HUMOR", "path": "lit-humor"},
    {"id": "lit-youth", "name": "LIT-YOUTH", "path": "lit-youth"},
    {"id": "lit-war", "name": "LIT-WAR", "path": "lit-war"},
    {"id": "lit-doc", "name": "LIT-DOC", "path": "lit-doc"},
    {"id": "lit-drama", "name": "LIT-DRAMA", "path": "lit-drama"},
    {"id": "lit-crimea", "name": "LIT-CRIMEA", "path": "lit-crimea"},
    {"id": "oes", "name": "OES", "path": "oes"},
    {"id": "ruth", "name": "RUTH", "path": "ruth"},
]

MAX_RESEARCH_UPGRADE_RETRIES = 3


def _get_track_name(track_id: str) -> str:
    return next((t["name"] for t in TRACKS if t["id"] == track_id), track_id.upper())


def _load_manifest() -> dict:
    manifest_path = CURRICULUM_ROOT / "curriculum.yaml"
    if not manifest_path.exists():
        print(f"Error: {manifest_path} not found", file=sys.stderr)
        sys.exit(1)
    with open(manifest_path) as f:
        return yaml.safe_load(f) or {}


def _parse_slug(entry) -> str:
    return _parse_slug_entry(entry)


def _find_content_path(track_dir: Path, slug: str) -> Path | None:
    """Find the module content .md file."""
    for pattern in [f"{slug}.md", f"*-{slug}.md"]:
        matches = list(track_dir.glob(pattern))
        if matches:
            return matches[0]
    return None


def _scan_track(track_id: str, manifest: dict) -> list[dict]:
    """Scan all modules in a track and return research assessment results."""
    track_cfg = next((t for t in TRACKS if t["id"] == track_id), None)
    if not track_cfg:
        print(f"Error: Unknown track '{track_id}'", file=sys.stderr)
        sys.exit(1)

    track_dir = CURRICULUM_ROOT / track_cfg["path"]
    modules_list = manifest.get("levels", {}).get(track_id, {}).get("modules", [])

    results = []
    for idx, m_entry in enumerate(modules_list):
        slug = _parse_slug(m_entry)
        num = idx + 1

        rp = find_research_path(track_dir, slug)
        content_path = _find_content_path(track_dir, slug)

        info = assess_research_compat(rp, track_id, content_path) if rp else None

        results.append({
            "num": num,
            "slug": slug,
            "research_path": str(rp) if rp else None,
            "has_content": content_path is not None,
            "info": info,
        })

    return results


# ---------------------------------------------------------------------------
# Backward-compatible wrappers (delegate to helpers with project context)
# ---------------------------------------------------------------------------

def _coverage_for_track(track_id: str, manifest: dict) -> dict:
    """Compute research coverage for a track."""
    return _coverage_for_track_impl(track_id, manifest, TRACKS, CURRICULUM_ROOT)


# ---------------------------------------------------------------------------
# CLI mode handlers
# ---------------------------------------------------------------------------

def _handle_coverage_mode(args, manifest, parser):
    """Handle --coverage flag."""
    if args.all:
        all_cov = _compute_all_coverage(manifest, TRACKS, CURRICULUM_ROOT)
        if args.json:
            print(json.dumps(all_cov, indent=2, ensure_ascii=False))
        else:
            _render_all_coverage(all_cov, TRACKS)
        total_gaps = sum(len(c["gaps"]) for c in all_cov.values())
        if args.strict and total_gaps > 0:
            sys.exit(1)
        return
    if not args.track:
        parser.print_help()
        sys.exit(1)
    track_id = args.track.lower()
    if not any(t["id"] == track_id for t in TRACKS):
        print(f"Error: Unknown track '{track_id}'", file=sys.stderr)
        sys.exit(1)
    cov = _coverage_for_track(track_id, manifest)
    if args.json:
        print(json.dumps(cov, indent=2, ensure_ascii=False))
    else:
        _render_coverage_table(track_id, manifest, TRACKS, CURRICULUM_ROOT, _get_track_name)
    if args.strict and cov["gaps"]:
        sys.exit(1)


def _handle_all_overview(args, manifest):
    """Handle --all flag (no --coverage)."""
    if args.json:
        overview = {}
        for track_cfg in TRACKS:
            tid = track_cfg["id"]
            modules_list = manifest.get("levels", {}).get(tid, {}).get("modules", [])
            if not modules_list:
                continue
            results = _scan_track(tid, manifest)
            researched = [r for r in results if r["info"] is not None]
            overview[tid] = {
                "rubric": get_rubric(tid),
                "total": len(results),
                "researched": len(researched),
                "modules": [
                    {"num": r["num"], "slug": r["slug"], **(r["info"] or {"exists": False})}
                    for r in results
                ],
            }
        print(json.dumps(overview, indent=2, ensure_ascii=False))
    else:
        _render_all_overview(manifest, TRACKS, CURRICULUM_ROOT)


def _handle_single_track(args, track_id, results, manifest):
    """Handle single-track modes: upgrade, enrich, refresh, single module, list."""
    if args.upgrade:
        _render_upgrade_queue(track_id, results, args.min_score, _get_track_name)
        if not args.dry_run:
            _process_upgrade_queue(
                track_id, results, args.min_score, MAX_RESEARCH_UPGRADE_RETRIES,
                SCRIPTS_DIR, CURRICULUM_ROOT, _clear_v3_phase_a, _get_track_name,
            )
        return

    if args.enrich:
        _process_enrich_plans(
            track_id, results, args.min_score,
            SCRIPTS_DIR, CURRICULUM_ROOT, _get_track_name,
        )
        return

    if args.refresh:
        _render_refresh_queue(track_id, results, _get_track_name)
        if not args.dry_run:
            _process_refresh_queue(track_id, results, SCRIPTS_DIR)
        return

    if args.num:
        result = next((r for r in results if r["num"] == args.num), None)
        if not result:
            print(f"Error: Module #{args.num} not found in {track_id}", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(json.dumps(result["info"] or {"exists": False}, indent=2, ensure_ascii=False))
        else:
            _render_single_module(track_id, result)
        return

    if args.json:
        output = [
            {"num": r["num"], "slug": r["slug"], **(r["info"] or {"exists": False})}
            for r in results
        ]
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    rubric_name = get_rubric(track_id)
    if rubric_name:
        _render_quality_table(track_id, results, manifest, show_gaps=args.gaps, get_track_name_fn=_get_track_name)
    else:
        _render_coverage_only(track_id, results, _get_track_name)


def main():
    epilog = """\
Example workflow:
  assess_research.py a1                  # 1. See quality table
  assess_research.py a1 --upgrade        # 2. Regenerate research below 9/10
  assess_research.py a1 --enrich         # 3. Enrich plans from 9+ research
  assess_research.py a1 --refresh        # 4. Rebuild stale content
  assess_research.py a1 --coverage       # Show research coverage gaps
  assess_research.py --all --coverage    # Full curriculum coverage

Add --dry-run to preview without making changes:
  assess_research.py a1 --upgrade --dry-run
"""
    parser = argparse.ArgumentParser(
        description="Research quality assessment and upgrade pipeline",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("track", nargs="?", help="Track ID (e.g. hist, a1, b1)")
    parser.add_argument("num", nargs="?", type=int, help="Module number (for single-module detail)")
    parser.add_argument("--upgrade", action="store_true", help="Regenerate research below --min-score (retries up to 3x)")
    parser.add_argument("--enrich", action="store_true", help="Enrich plans from research at --min-score or above")
    parser.add_argument("--refresh", action="store_true", help="Rebuild content for modules with upgraded research")
    parser.add_argument("--dry-run", action="store_true", help="Preview what would be done (no builds)")
    parser.add_argument("--min-score", type=int, default=9, help="Score threshold (default: 9)")
    parser.add_argument("--gaps", action="store_true", help="Only show modules with gaps")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--all", action="store_true", help="Overview of all tracks")
    parser.add_argument("--coverage", action="store_true", help="Show research coverage gaps (manifest vs research files)")
    parser.add_argument("--strict", action="store_true", help="With --coverage, exit 1 if any gaps found (for CI)")
    args = parser.parse_args()

    if args.strict and not args.coverage:
        parser.error("--strict requires --coverage")

    manifest = _load_manifest()

    if args.coverage:
        _handle_coverage_mode(args, manifest, parser)
        return

    if args.all:
        _handle_all_overview(args, manifest)
        return

    if not args.track:
        parser.print_help()
        sys.exit(1)

    track_id = args.track.lower()
    if not any(t["id"] == track_id for t in TRACKS):
        print(f"Error: Unknown track '{track_id}'", file=sys.stderr)
        sys.exit(1)

    results = _scan_track(track_id, manifest)
    _handle_single_track(args, track_id, results, manifest)


if __name__ == "__main__":
    main()
