"""Helper functions for assess_research.py — output rendering, queue processing, coverage.

Extracted to reduce module complexity and improve maintainability index.
All functions are imported back into assess_research.py for backward compatibility.
"""

from __future__ import annotations

from pathlib import Path

from research_quality import (
    DIMENSION_SHORT_LABELS,
    assess_research_compat,
    find_research_path,
    get_dimensions,
    get_rubric,
)

# ANSI color constants
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
GREEN = "\033[32m"
RED = "\033[31m"


def _colored(text: str, quality: str | None) -> str:
    """Apply ANSI color for a quality label."""
    color = COLORS.get(quality, "")
    return f"{color}{text}{RESET}" if color else text


# ---------------------------------------------------------------------------
# Quality table rendering
# ---------------------------------------------------------------------------

def _format_quality_row(r: dict, dim_names: list[str], show_gaps: bool) -> str | None:
    """Format a single row for the quality table. Returns None for missing entries when show_gaps."""
    info = r["info"]
    if info is None:
        if not show_gaps:
            return f"{r['num']:>3}  {r['slug']:<35} {DIM}{'---':>6}  {'missing':<11}{RESET}"
        return None

    score = info.get("score", 0)
    quality = info.get("quality", "stub")
    dims = info.get("dimensions") or {}
    gaps = info.get("gaps") or []

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

    return (
        f"{r['num']:>3}  {r['slug']:<35} "
        f"{_colored(f'{score:>2}/10', quality)}  "
        f"{_colored(f'{quality:<11}', quality)} "
        f"{dim_scores}  "
        f"{gap_str}{refresh_str}"
    )


def _render_quality_table(
    track_id: str,
    results: list[dict],
    manifest: dict,
    show_gaps: bool,
    get_track_name_fn,
):
    """Render a quality table for tracks with a rubric."""
    rubric_name = get_rubric(track_id)
    dim_names = get_dimensions(rubric_name)
    dim_labels = [DIMENSION_SHORT_LABELS.get(d, d[:3]) for d in dim_names]

    track_name = get_track_name_fn(track_id)
    print(f"\n{BOLD}{track_name} Research Quality ({rubric_name} rubric){RESET}")
    print("\u2550" * 90)

    dim_header = " ".join(f"{l:>3}" for l in dim_labels)
    refresh_col = "  Refresh?" if show_gaps else ""
    print(f"{'#':>3}  {'Module':<35} {'Score':>6}  {'Quality':<11} {dim_header}  {'Gaps'}{refresh_col}")
    print("\u2500" * 90)

    if show_gaps:
        results = [r for r in results if r["info"] and (
            r["info"].get("gaps") or
            r["info"].get("content_alignment", {}).get("refresh_recommended")
        )]

    total = len([r for r in results if r["info"]])
    counts = {"exemplary": 0, "solid": 0, "adequate": 0, "thin": 0, "stub": 0}
    score_sum = 0

    for r in results:
        row = _format_quality_row(r, dim_names, show_gaps)
        if row is not None:
            print(row)
        info = r["info"]
        if info is not None:
            quality = info.get("quality", "stub")
            counts[quality] = counts.get(quality, 0) + 1
            score_sum += info.get("score", 0)

    print("\u2550" * 90)
    avg = f"{score_sum / total:.1f}" if total > 0 else "0"
    summary_parts = []
    for label in ["exemplary", "solid", "adequate", "thin", "stub"]:
        if counts.get(label, 0) > 0:
            summary_parts.append(f"{counts[label]} {label}")
    module_count = len(manifest.get("levels", {}).get(track_id, {}).get("modules", []))
    print(f"Summary: {', '.join(summary_parts)} | {total}/{module_count} researched | avg {avg}/10")
    print()


def _render_coverage_only(track_id: str, results: list[dict], get_track_name_fn):
    """Render coverage-only output for tracks without a rubric."""
    track_name = get_track_name_fn(track_id)
    researched = [r for r in results if r["info"] is not None]
    total = len(results)
    pct = f"{len(researched) / total * 100:.1f}" if total > 0 else "0"

    print(f"\n{BOLD}{track_name} Research Coverage{RESET}")
    print("\u2550" * 50)
    print(f"Coverage: {len(researched)}/{total} ({pct}%)")
    print("No quality rubric defined \u2014 complete research coverage first.")

    if researched:
        print("\nFiles found:")
        for r in researched:
            words = r["info"].get("words", 0)
            print(f"  - {r['slug']}-research.md ({words}w)")

    print("\u2550" * 50)
    print()


def _render_module_dimensions(info: dict):
    """Render dimension bars for a single module's detail view."""
    dims = info.get("dimensions") or {}
    if dims:
        print("\n  Dimensions:")
        for dim_name, dim_data in dims.items():
            label = DIMENSION_SHORT_LABELS.get(dim_name, dim_name)
            bar = "\u2588" * dim_data["score"] + "\u2591" * (dim_data["max"] - dim_data["score"])
            print(f"    {label:>3} [{bar}] {dim_data['score']}/{dim_data['max']}  {dim_data['detail']}")


def _render_module_gaps_alignment(info: dict):
    """Render gaps and content alignment for a single module."""
    gaps = info.get("gaps") or []
    if gaps:
        print("\n  Gaps:")
        for g in gaps:
            print(f"    - {g}")

    alignment = info.get("content_alignment")
    if alignment:
        if alignment.get("refresh_recommended"):
            print(f"\n  {BOLD}Refresh recommended:{RESET}")
            for reason in alignment["reasons"]:
                print(f"    \u26a0 {reason}")
        elif alignment.get("content_exists"):
            print("\n  Content alignment: OK")


def _render_single_module(track_id: str, result: dict):
    """Render detailed output for a single module."""
    info = result["info"]
    get_rubric(track_id)

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
        _render_module_dimensions(info)
        _render_module_gaps_alignment(info)
    else:
        print(f"  Score:   {DIM}no rubric{RESET}")

    print()


# ---------------------------------------------------------------------------
# Refresh queue
# ---------------------------------------------------------------------------

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


def _render_refresh_queue(track_id: str, results: list[dict], get_track_name_fn):
    """Render modules where content refresh is recommended."""
    track_name = get_track_name_fn(track_id)
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
        print(f"Run: .venv/bin/python scripts/build_module_v5.py {track_id} {{num}} --refresh")
    else:
        print("No modules need content refresh.")
    print()


def _build_upgrade_queue(results: list[dict], min_score: int = 9) -> list[dict]:
    """Extract modules with research below min_score."""
    queue = []
    for r in results:
        info = r["info"]
        if info is None:
            queue.append(r)
            continue
        score = info.get("score")
        if score is not None and score < min_score:
            queue.append(r)
    queue.sort(key=lambda r: (r["info"] or {}).get("score", -1))
    return queue


def _render_upgrade_queue(track_id: str, results: list[dict], min_score: int, get_track_name_fn):
    """Render modules with research below min_score threshold."""
    track_name = get_track_name_fn(track_id)
    queue = _build_upgrade_queue(results, min_score)

    print(f"\n{BOLD}{track_name} Upgrade Queue (research below {min_score}/10){RESET}")
    print("\u2550" * 70)
    print(f"{'#':>3}  {'Module':<35} {'Score':>6}  Gaps")
    print("\u2500" * 70)

    for r in queue:
        info = r["info"]
        if info is None:
            print(f"{r['num']:>3}  {r['slug']:<35} {DIM}{'---':>6}  missing{RESET}")
            continue
        score = info.get("score", 0)
        quality = info.get("quality", "")
        gaps = info.get("gaps") or []
        gap_str = ", ".join(g.split(":")[0] for g in gaps[:4])
        if len(gaps) > 4:
            gap_str += f" +{len(gaps) - 4}"
        print(
            f"{r['num']:>3}  {r['slug']:<35} "
            f"{_colored(f'{score:>2}/10', quality)}  "
            f"{gap_str}"
        )

    print("\u2550" * 70)
    if queue:
        print(f"{len(queue)} module(s) need research upgrade to {min_score}/10+")
    else:
        print(f"All modules at {min_score}/10+. Nothing to upgrade.")
    print()


    # Queue processing functions are in assess_research_queue.py


# ---------------------------------------------------------------------------
# All-tracks overview
# ---------------------------------------------------------------------------

def _compute_track_overview_row(
    track_cfg: dict, manifest: dict, curriculum_root: Path,
) -> dict | None:
    """Compute overview stats for a single track. Returns None if track has no modules."""
    track_id = track_cfg["id"]
    modules_list = manifest.get("levels", {}).get(track_id, {}).get("modules", [])
    if not modules_list:
        return None

    track_dir = curriculum_root / track_cfg["path"]
    total = len(modules_list)
    rubric_name = get_rubric(track_id) or "\u2014"

    researched = 0
    score_sum = 0
    scored_count = 0
    for m_entry in modules_list:
        slug = _parse_slug_entry(m_entry)
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

    return {
        "name": track_cfg["name"],
        "rubric": rubric_name,
        "coverage": coverage,
        "avg": avg,
    }


def _render_all_overview(manifest: dict, tracks: list[dict], curriculum_root: Path):
    """Render overview of all tracks."""
    print(f"\n{BOLD}Research Overview{RESET}")
    print("\u2550" * 60)
    print(f"{'Track':<12} {'Rubric':<10} {'Coverage':<16} {'Avg Score'}")
    print("\u2500" * 60)

    for track_cfg in tracks:
        row = _compute_track_overview_row(track_cfg, manifest, curriculum_root)
        if row:
            print(f"{row['name']:<12} {row['rubric']:<10} {row['coverage']:<16} {row['avg']}")

    print("\u2550" * 60)
    print()


# ---------------------------------------------------------------------------
# Coverage helpers
# ---------------------------------------------------------------------------

def _parse_slug_entry(entry) -> str:
    """Parse a slug from a manifest entry."""
    if isinstance(entry, str):
        return entry.split("#")[0].strip()
    return str(entry)


def _coverage_for_track(track_id: str, manifest: dict, tracks: list[dict], curriculum_root: Path) -> dict:
    """Compute research coverage for a track."""
    track_cfg = next((t for t in tracks if t["id"] == track_id), None)
    if not track_cfg:
        return {"total": 0, "researched": 0, "gaps": []}
    track_dir = curriculum_root / track_cfg["path"]
    modules_list = manifest.get("levels", {}).get(track_id, {}).get("modules", [])
    gaps = []
    researched = 0
    for m_entry in modules_list:
        slug = _parse_slug_entry(m_entry)
        rp = find_research_path(track_dir, slug)
        if rp:
            researched += 1
        else:
            gaps.append(slug)
    return {"total": len(modules_list), "researched": researched, "gaps": gaps}


def _render_coverage_table(track_id: str, manifest: dict, tracks: list[dict], curriculum_root: Path, get_track_name_fn):
    """Render coverage table for a single track."""
    cov = _coverage_for_track(track_id, manifest, tracks, curriculum_root)
    track_name = get_track_name_fn(track_id)
    total, researched = cov["total"], cov["researched"]
    pct = f"{researched / total * 100:.0f}%" if total > 0 else "0%"
    print(f"\n{BOLD}{track_name} Research Coverage{RESET}")
    print("\u2550" * 60)
    print(f"  Manifest modules:  {total}")
    print(f"  Research files:    {researched}")
    print(f"  Coverage:          {researched}/{total} ({pct})")
    if cov["gaps"]:
        print(f"\n  {BOLD}Missing research ({len(cov['gaps'])}):{RESET}")
        for slug in cov["gaps"]:
            print(f"    \u2022 {slug}")
    else:
        print(f"\n  {GREEN}\u2714 Full coverage{RESET}")
    print()


def _compute_all_coverage(manifest: dict, tracks: list[dict], curriculum_root: Path) -> dict[str, dict]:
    """Compute coverage for all non-empty tracks."""
    result = {}
    for track_cfg in tracks:
        tid = track_cfg["id"]
        cov = _coverage_for_track(tid, manifest, tracks, curriculum_root)
        if cov["total"] > 0:
            result[tid] = cov
    return result


def _render_all_coverage(all_cov: dict[str, dict], tracks: list[dict]):
    """Render coverage overview table from pre-computed coverage data."""
    print(f"\n{BOLD}Research Coverage Overview{RESET}")
    print("\u2550" * 70)
    print(f"{'Track':<14} {'Manifest':>8} {'Research':>9} {'Gaps':>5}  {'Coverage':>9}")
    print("\u2500" * 70)
    total_gaps = 0
    for track_cfg in tracks:
        tid = track_cfg["id"]
        cov = all_cov.get(tid)
        if not cov:
            continue
        pct = f"{cov['researched'] / cov['total'] * 100:.0f}%"
        gap_count = len(cov["gaps"])
        total_gaps += gap_count
        gap_color = RED if gap_count > 0 else GREEN
        print(f"{track_cfg['name']:<14} {cov['total']:>8} {cov['researched']:>9} {gap_color}{gap_count:>5}{RESET}  {pct:>9}")
    print("\u2550" * 70)
    print(f"  Total gaps: {total_gaps}")
    print()
