#!/usr/bin/env python3
"""
CLI tool for research quality assessment.

Usage:
  .venv/bin/python scripts/assess_research.py b2-hist                # quality table (has rubric)
  .venv/bin/python scripts/assess_research.py b2-hist 5              # single module
  .venv/bin/python scripts/assess_research.py b2-hist --gaps         # only modules with gaps
  .venv/bin/python scripts/assess_research.py a1                     # quality table (has rubric)
  .venv/bin/python scripts/assess_research.py b1                     # coverage only (no rubric)
  .venv/bin/python scripts/assess_research.py --all                  # all tracks overview
  .venv/bin/python scripts/assess_research.py b2-hist --json         # JSON output
  .venv/bin/python scripts/assess_research.py a1 --refresh-queue     # modules needing content refresh
  .venv/bin/python scripts/assess_research.py a1 --process          # rebuild all stale modules
"""

import argparse
import json
import sys
from pathlib import Path

# Add scripts/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml
from research_quality import (
    DIMENSION_SHORT_LABELS,
    assess_research_compat,
    find_research_path,
    get_dimensions,
    get_rubric,
)

# Project paths
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"

# Track config (mirrors api/config.py)
TRACKS = [
    {"id": "a1", "name": "A1", "path": "a1"},
    {"id": "a2", "name": "A2", "path": "a2"},
    {"id": "b1", "name": "B1", "path": "b1"},
    {"id": "b2", "name": "B2", "path": "b2"},
    {"id": "b2-pro", "name": "B2-PRO", "path": "b2-pro"},
    {"id": "c1", "name": "C1", "path": "c1"},
    {"id": "c1-pro", "name": "C1-PRO", "path": "c1-pro"},
    {"id": "c2", "name": "C2", "path": "c2"},
    {"id": "b2-hist", "name": "B2-HIST", "path": "b2-hist"},
    {"id": "c1-hist", "name": "C1-HIST", "path": "c1-hist"},
    {"id": "c1-bio", "name": "C1-BIO", "path": "c1-bio"},
    {"id": "lit", "name": "LIT", "path": "lit"},
    {"id": "oes", "name": "OES", "path": "oes"},
    {"id": "ruth", "name": "RUTH", "path": "ruth"},
]


def _load_manifest() -> dict:
    manifest_path = CURRICULUM_ROOT / "curriculum.yaml"
    if not manifest_path.exists():
        print(f"Error: {manifest_path} not found", file=sys.stderr)
        sys.exit(1)
    with open(manifest_path) as f:
        return yaml.safe_load(f) or {}


def _parse_slug(entry) -> str:
    if isinstance(entry, str):
        return entry.split("#")[0].strip()
    return str(entry)


def _find_content_path(track_dir: Path, slug: str) -> Path | None:
    """Find the module content .md file."""
    # Try common naming patterns
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

        if rp:
            info = assess_research_compat(rp, track_id, content_path)
        else:
            info = None

        results.append({
            "num": num,
            "slug": slug,
            "research_path": str(rp) if rp else None,
            "has_content": content_path is not None,
            "info": info,
        })

    return results


# ==================== OUTPUT FORMATTERS ====================

# Quality label colors (ANSI)
COLORS = {
    "exemplary": "\033[32m",  # green
    "solid": "\033[34m",      # blue
    "adequate": "\033[33m",   # yellow
    "thin": "\033[38;5;208m", # orange
    "stub": "\033[31m",       # red
}
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def _colored(text: str, quality: str | None) -> str:
    color = COLORS.get(quality, "")
    return f"{color}{text}{RESET}" if color else text


def _render_quality_table(track_id: str, results: list[dict], show_gaps: bool = False):
    """Render a quality table for tracks with a rubric."""
    rubric_name = get_rubric(track_id)
    dim_names = get_dimensions(rubric_name)
    dim_labels = [DIMENSION_SHORT_LABELS.get(d, d[:3]) for d in dim_names]

    track_name = next((t["name"] for t in TRACKS if t["id"] == track_id), track_id.upper())
    print(f"\n{BOLD}{track_name} Research Quality ({rubric_name} rubric){RESET}")
    print("\u2550" * 90)

    # Header
    dim_header = " ".join(f"{l:>3}" for l in dim_labels)
    refresh_col = "  Refresh?" if show_gaps else ""
    print(f"{'#':>3}  {'Module':<35} {'Score':>6}  {'Quality':<11} {dim_header}  {'Gaps'}{refresh_col}")
    print("\u2500" * 90)

    # Filter for --gaps mode
    if show_gaps:
        results = [r for r in results if r["info"] and (
            r["info"].get("gaps") or
            r["info"].get("content_alignment", {}).get("refresh_recommended")
        )]

    total = len([r for r in results if r["info"]])
    counts = {"exemplary": 0, "solid": 0, "adequate": 0, "thin": 0, "stub": 0}
    score_sum = 0

    for r in results:
        info = r["info"]
        if info is None:
            if not show_gaps:
                print(f"{r['num']:>3}  {r['slug']:<35} {DIM}{'---':>6}  {'missing':<11}{RESET}")
            continue

        score = info.get("score", 0)
        quality = info.get("quality", "stub")
        dims = info.get("dimensions") or {}
        gaps = info.get("gaps") or []

        counts[quality] = counts.get(quality, 0) + 1
        score_sum += score

        dim_scores = " ".join(
            f"{dims.get(d, {}).get('score', '-'):>3}" for d in dim_names
        )

        gap_str = ", ".join(g.split(":")[0] for g in gaps[:3])
        if len(gaps) > 3:
            gap_str += f" +{len(gaps) - 3}"

        refresh_str = ""
        if show_gaps:
            alignment = info.get("content_alignment", {})
            if alignment.get("refresh_recommended"):
                reasons = alignment.get("reasons", [])
                refresh_str = f"  YES: {reasons[0]}" if reasons else "  YES"
            else:
                refresh_str = f"  {DIM}\u2014{RESET}"

        print(
            f"{r['num']:>3}  {r['slug']:<35} "
            f"{_colored(f'{score:>2}/10', quality)}  "
            f"{_colored(f'{quality:<11}', quality)} "
            f"{dim_scores}  "
            f"{gap_str}{refresh_str}"
        )

    print("\u2550" * 90)
    avg = f"{score_sum / total:.1f}" if total > 0 else "0"
    total_modules = len([r for r in _all_results if r["info"] is not None]) if '_all_results' in dir() else total
    summary_parts = []
    for label in ["exemplary", "solid", "adequate", "thin", "stub"]:
        if counts.get(label, 0) > 0:
            summary_parts.append(f"{counts[label]} {label}")
    manifest = _load_manifest()
    module_count = len(manifest.get("levels", {}).get(track_id, {}).get("modules", []))
    print(f"Summary: {', '.join(summary_parts)} | {total}/{module_count} researched | avg {avg}/10")
    print()


def _render_coverage_only(track_id: str, results: list[dict]):
    """Render coverage-only output for tracks without a rubric."""
    track_name = next((t["name"] for t in TRACKS if t["id"] == track_id), track_id.upper())
    researched = [r for r in results if r["info"] is not None]
    total = len(results)
    pct = f"{len(researched) / total * 100:.1f}" if total > 0 else "0"

    print(f"\n{BOLD}{track_name} Research Coverage{RESET}")
    print("\u2550" * 50)
    print(f"Coverage: {len(researched)}/{total} ({pct}%)")
    print(f"No quality rubric defined \u2014 complete research coverage first.")

    if researched:
        print(f"\nFiles found:")
        for r in researched:
            words = r["info"].get("words", 0)
            print(f"  - {r['slug']}-research.md ({words}w)")

    print("\u2550" * 50)
    print()


def _render_single_module(track_id: str, result: dict):
    """Render detailed output for a single module."""
    info = result["info"]
    rubric_name = get_rubric(track_id)

    print(f"\n{BOLD}#{result['num']:03d} {result['slug']}{RESET} ({track_id})")
    print("\u2500" * 50)

    if info is None:
        print(f"  Research: {DIM}not found{RESET}")
        return

    print(f"  Words:   {info['words']}")
    print(f"  Rubric:  {info.get('profile') or 'none'}")

    if info.get("score") is not None:
        quality = info["quality"]
        score_val = info["score"]
        print(f"  Score:   {_colored(f'{score_val}/10 ({quality})', quality)}")

        dims = info.get("dimensions") or {}
        if dims:
            print(f"\n  Dimensions:")
            for dim_name, dim_data in dims.items():
                label = DIMENSION_SHORT_LABELS.get(dim_name, dim_name)
                bar = "\u2588" * dim_data["score"] + "\u2591" * (dim_data["max"] - dim_data["score"])
                print(f"    {label:>3} [{bar}] {dim_data['score']}/{dim_data['max']}  {dim_data['detail']}")

        gaps = info.get("gaps") or []
        if gaps:
            print(f"\n  Gaps:")
            for g in gaps:
                print(f"    - {g}")

        alignment = info.get("content_alignment")
        if alignment:
            if alignment.get("refresh_recommended"):
                print(f"\n  {BOLD}Refresh recommended:{RESET}")
                for reason in alignment["reasons"]:
                    print(f"    \u26a0 {reason}")
            elif alignment.get("content_exists"):
                print(f"\n  Content alignment: OK")
    else:
        print(f"  Score:   {DIM}no rubric{RESET}")

    print()


def _build_refresh_queue(results: list[dict]) -> list[dict]:
    """Extract and sort modules where content refresh is recommended."""
    queue = []
    for r in results:
        info = r["info"]
        if info is None:
            continue
        alignment = info.get("content_alignment", {})
        if not alignment.get("refresh_recommended"):
            continue
        queue.append(r)
    queue.sort(key=lambda r: r["info"].get("score", 0), reverse=True)
    return queue


def _render_refresh_queue(track_id: str, results: list[dict]):
    """Render modules where content refresh is recommended (research upgraded, content stale)."""
    track_name = next((t["name"] for t in TRACKS if t["id"] == track_id), track_id.upper())
    queue = _build_refresh_queue(results)

    print(f"\n{BOLD}{track_name} Refresh Queue (research upgraded, content stale){RESET}")
    print("\u2550" * 70)
    print(f"{'#':>3}  {'Module':<35} {'Score':>6}  Reason")
    print("\u2500" * 70)

    for r in queue:
        info = r["info"]
        score = info.get("score", 0)
        quality = info.get("quality", "")
        reasons = info.get("content_alignment", {}).get("reasons", [])
        reason_str = reasons[0] if reasons else "research upgraded"
        print(
            f"{r['num']:>3}  {r['slug']:<35} "
            f"{_colored(f'{score:>2}/10', quality)}  "
            f"{reason_str}"
        )

    print("\u2550" * 70)
    if queue:
        print(f"{len(queue)} module(s) ready for content refresh")
        print(f"Run: .venv/bin/python scripts/build_module_v2.py {track_id} {{num}} --refresh")
    else:
        print("No modules need content refresh.")
    print()


def _process_refresh_queue(track_id: str, results: list[dict]):
    """Process the refresh queue — run build_module_v2.py --refresh for each module."""
    import subprocess

    queue = _build_refresh_queue(results)
    if not queue:
        print("No modules need content refresh.")
        return

    track_name = next((t["name"] for t in TRACKS if t["id"] == track_id), track_id.upper())
    total = len(queue)
    print(f"\n{BOLD}{track_name}: Processing {total} module(s){RESET}")
    print("\u2550" * 70)

    passed = 0
    failed = 0
    for i, r in enumerate(queue, 1):
        num = r["num"]
        slug = r["slug"]
        print(f"\n[{i}/{total}] M{num:02d} {slug}")
        print("\u2500" * 50)

        cmd = [
            str(SCRIPTS_DIR / ".." / ".venv" / "bin" / "python"),
            str(SCRIPTS_DIR / "build_module_v2.py"),
            track_id, str(num), "--refresh",
        ]
        try:
            result = subprocess.run(cmd, timeout=600)
            if result.returncode == 0:
                passed += 1
                print(f"  {BOLD}\033[32mPASS{RESET}")
            else:
                failed += 1
                print(f"  {BOLD}\033[31mFAIL (exit {result.returncode}){RESET}")
        except subprocess.TimeoutExpired:
            failed += 1
            print(f"  {BOLD}\033[31mTIMEOUT (10min){RESET}")
        except KeyboardInterrupt:
            print(f"\n\nInterrupted after {i-1}/{total} modules ({passed} passed, {failed} failed)")
            return

    print(f"\n{'═' * 70}")
    print(f"Done: {passed} passed, {failed} failed out of {total}")
    print()


def _render_all_overview(manifest: dict):
    """Render overview of all tracks."""
    print(f"\n{BOLD}Research Overview{RESET}")
    print("\u2550" * 60)
    print(f"{'Track':<12} {'Rubric':<10} {'Coverage':<16} {'Avg Score'}")
    print("\u2500" * 60)

    for track_cfg in TRACKS:
        track_id = track_cfg["id"]
        modules_list = manifest.get("levels", {}).get(track_id, {}).get("modules", [])
        if not modules_list:
            continue

        track_dir = CURRICULUM_ROOT / track_cfg["path"]
        total = len(modules_list)
        rubric_name = get_rubric(track_id) or "\u2014"

        researched = 0
        score_sum = 0
        scored_count = 0
        for idx, m_entry in enumerate(modules_list):
            slug = _parse_slug(m_entry)
            rp = find_research_path(track_dir, slug)
            if rp:
                researched += 1
                if get_rubric(track_id):
                    info = assess_research_compat(rp, track_id)
                    if info and info.get("score") is not None:
                        score_sum += info["score"]
                        scored_count += 1

        pct = f"{researched / total * 100:.0f}%" if total > 0 else "0%"
        coverage = f"{researched}/{total} ({pct})"
        avg = f"{score_sum / scored_count:.1f}/10" if scored_count > 0 else "\u2014"

        print(f"{track_cfg['name']:<12} {rubric_name:<10} {coverage:<16} {avg}")

    print("\u2550" * 60)
    print()


# ==================== MAIN ====================


def main():
    parser = argparse.ArgumentParser(description="Research quality assessment")
    parser.add_argument("track", nargs="?", help="Track ID (e.g. b2-hist, a1)")
    parser.add_argument("num", nargs="?", type=int, help="Module number")
    parser.add_argument("--gaps", action="store_true", help="Only show modules with gaps")
    parser.add_argument("--refresh-queue", action="store_true", help="List modules where content refresh is recommended")
    parser.add_argument("--process", action="store_true", help="Process the refresh queue (run build_module_v2.py --refresh for each)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--all", action="store_true", help="Overview of all tracks")
    args = parser.parse_args()

    manifest = _load_manifest()

    if args.all:
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
            _render_all_overview(manifest)
        return

    if not args.track:
        parser.print_help()
        sys.exit(1)

    track_id = args.track.lower()
    if not any(t["id"] == track_id for t in TRACKS):
        print(f"Error: Unknown track '{track_id}'", file=sys.stderr)
        sys.exit(1)

    results = _scan_track(track_id, manifest)

    if getattr(args, "process", False):
        _render_refresh_queue(track_id, results)
        _process_refresh_queue(track_id, results)
        return

    if getattr(args, "refresh_queue", False):
        _render_refresh_queue(track_id, results)
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
        _render_quality_table(track_id, results, show_gaps=args.gaps)
    else:
        _render_coverage_only(track_id, results)


if __name__ == "__main__":
    main()
