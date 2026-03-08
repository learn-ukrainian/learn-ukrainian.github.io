#!/usr/bin/env python3
"""
Research quality assessment and upgrade pipeline.

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
    DIMENSION_SHORT_LABELS,
    assess_research_compat,
    find_research_path,
    get_dimensions,
    get_rubric,
)


def _clear_v3_phase_a(track_id: str, slug: str) -> bool:
    """Clear Phase A from state-v3.json so build_module re-runs it with improved research.

    Called after --upgrade successfully upgrades a module's research to 9+.
    Without this, v3 would skip Phase A (still marked complete) and use a stale
    meta outline generated from the old weak research.
    """
    _curriculum_root = Path(__file__).resolve().parent.parent / "curriculum" / "l2-uk-en"
    orch_dir = _curriculum_root / track_id / "orchestration" / slug
    state_file = orch_dir / "state-v3.json"
    if not state_file.exists():
        return False  # No v3 state — nothing to clear
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

# Track config — keep in sync with:
#   api/config.py (LEVELS), batch_dispatcher_config.py (TRACKS), manifest_utils.py (CORE_LEVELS/TRACKS)
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

        info = assess_research_compat(rp, track_id, content_path) if rp else None

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
GREEN = "\033[32m"
RED = "\033[31m"


def _colored(text: str, quality: str | None) -> str:
    color = COLORS.get(quality, "")
    return f"{color}{text}{RESET}" if color else text


def _render_quality_table(track_id: str, results: list[dict], manifest: dict, show_gaps: bool = False):
    """Render a quality table for tracks with a rubric."""
    rubric_name = get_rubric(track_id)
    dim_names = get_dimensions(rubric_name)
    dim_labels = [DIMENSION_SHORT_LABELS.get(d, d[:3]) for d in dim_names]

    track_name = _get_track_name(track_id)
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
    summary_parts = []
    for label in ["exemplary", "solid", "adequate", "thin", "stub"]:
        if counts.get(label, 0) > 0:
            summary_parts.append(f"{counts[label]} {label}")
    module_count = len(manifest.get("levels", {}).get(track_id, {}).get("modules", []))
    print(f"Summary: {', '.join(summary_parts)} | {total}/{module_count} researched | avg {avg}/10")
    print()


def _render_coverage_only(track_id: str, results: list[dict]):
    """Render coverage-only output for tracks without a rubric."""
    track_name = _get_track_name(track_id)
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

        dims = info.get("dimensions") or {}
        if dims:
            print("\n  Dimensions:")
            for dim_name, dim_data in dims.items():
                label = DIMENSION_SHORT_LABELS.get(dim_name, dim_name)
                bar = "\u2588" * dim_data["score"] + "\u2591" * (dim_data["max"] - dim_data["score"])
                print(f"    {label:>3} [{bar}] {dim_data['score']}/{dim_data['max']}  {dim_data['detail']}")

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
    track_name = _get_track_name(track_id)
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


def _process_refresh_queue(track_id: str, results: list[dict]):
    """Process the refresh queue — run build_module_v5.py --refresh for each module."""
    import subprocess

    queue = _build_refresh_queue(results)
    if not queue:
        print("No modules need content refresh.")
        return

    track_name = _get_track_name(track_id)
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
            str(SCRIPTS_DIR / "build_module_v5.py"),
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


MAX_RESEARCH_UPGRADE_RETRIES = 3  # Total attempts per module


def _build_upgrade_queue(results: list[dict], min_score: int = 9) -> list[dict]:
    """Extract modules with research below min_score."""
    queue = []
    for r in results:
        info = r["info"]
        if info is None:
            # No research file — needs generation
            queue.append(r)
            continue
        score = info.get("score")
        if score is not None and score < min_score:
            queue.append(r)
    # Sort by score ascending (weakest first = most improvement needed)
    queue.sort(key=lambda r: (r["info"] or {}).get("score", -1))
    return queue


def _render_upgrade_queue(track_id: str, results: list[dict], min_score: int = 9):
    """Render modules with research below min_score threshold."""
    track_name = _get_track_name(track_id)
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


def _process_upgrade_queue(track_id: str, results: list[dict], min_score: int = 9):
    """Process the upgrade queue — regenerate research with retries until threshold met."""
    import subprocess

    queue = _build_upgrade_queue(results, min_score)
    if not queue:
        print(f"All modules at {min_score}/10+. Nothing to upgrade.")
        return

    track_name = _get_track_name(track_id)
    total = len(queue)
    max_attempts = MAX_RESEARCH_UPGRADE_RETRIES
    print(f"\n{BOLD}{track_name}: Upgrading research for {total} module(s) (max {max_attempts} attempts each){RESET}")
    print("\u2550" * 70)

    passed = 0
    failed = 0
    attempt_log = []  # (slug, attempts_used, final_score)
    for i, r in enumerate(queue, 1):
        num = r["num"]
        slug = r["slug"]
        old_score = (r["info"] or {}).get("score", "?")
        print(f"\n[{i}/{total}] M{num:02d} {slug} (current: {old_score}/10)")
        print("\u2500" * 50)

        module_passed = False
        last_score = old_score
        attempts_used = 0

        for attempt in range(1, max_attempts + 1):
            attempts_used = attempt
            # Clear v3 Phase A state so research is regenerated (not skipped)
            _clear_v3_phase_a(track_id, slug)
            # Delete old research file so the phase is forced to regenerate it
            # (otherwise ADOPT logic sees existing content+meta and skips)
            track_dir = CURRICULUM_ROOT / track_id
            old_rp = find_research_path(track_dir, slug)
            if old_rp and old_rp.exists():
                backup = old_rp.with_suffix(".md.bak")
                old_rp.rename(backup)
                print(f"  Backed up old research → {backup.name}")
            # --force-phase research: bypass v4 "already complete" guard
            # --rebuild: bypass ADOPT logic (skips content+meta existence check)
            cmd = [
                str(SCRIPTS_DIR / ".." / ".venv" / "bin" / "python"),
                str(SCRIPTS_DIR / "build_module_v5.py"),
                track_id, str(num), "--force-phase", "research", "--rebuild",
            ]
            try:
                result = subprocess.run(cmd, timeout=600)
                if result.returncode == 0:
                    # Re-assess to check new score
                    track_dir = CURRICULUM_ROOT / track_id
                    rp = find_research_path(track_dir, slug)
                    if rp:
                        new_info = assess_research_compat(rp, track_id)
                        new_score = (new_info or {}).get("score", "?")
                        print(f"  Attempt {attempt}: {last_score}/10 \u2192 {new_score}/10", end="")
                        if isinstance(new_score, int) and new_score >= min_score:
                            print(f" {BOLD}\033[32m\u2713{RESET}")
                            module_passed = True
                            last_score = new_score
                            # Clear v3 Phase A so meta outline is regenerated from improved research
                            if _clear_v3_phase_a(track_id, slug):
                                print("  v3 Phase A reset → meta outline will regenerate on next v3 run")
                            break
                        elif attempt < max_attempts:
                            print(f" (below {min_score}, retrying...)")
                            last_score = new_score
                        else:
                            print(f" {BOLD}\033[33mstill below {min_score} after {max_attempts} attempts{RESET}")
                            last_score = new_score
                    else:
                        print(f"  Attempt {attempt}: {BOLD}\033[31mno research file after build{RESET}")
                        break
                else:
                    print(f"  Attempt {attempt}: {BOLD}\033[31mFAIL (exit {result.returncode}){RESET}")
                    break
            except subprocess.TimeoutExpired:
                print(f"  Attempt {attempt}: {BOLD}\033[31mTIMEOUT (10min){RESET}")
                break
            except KeyboardInterrupt:
                print(f"\n\nInterrupted at M{num:02d} attempt {attempt}/{max_attempts}")
                print(f"Progress: {passed} passed, {failed} failed out of {i}/{total} modules")
                return

        attempt_log.append((slug, attempts_used, last_score))
        if module_passed:
            passed += 1
        else:
            failed += 1

    print(f"\n{'═' * 70}")
    print(f"Done: {passed} upgraded to {min_score}+, {failed} still below")
    multi = [(s, a) for s, a, _ in attempt_log if a > 1]
    if multi:
        print(f"Multi-attempt: {', '.join(f'{s}({a}x)' for s, a in multi)}")
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
        for _idx, m_entry in enumerate(modules_list):
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


def _is_plan_already_enriched(track_id: str, slug: str) -> bool:
    """Check if a plan already has enrichment markers (em-dash annotations)."""
    plan_path = CURRICULUM_ROOT / "plans" / track_id / f"{slug}.yaml"
    if not plan_path.exists():
        return False
    try:
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
        return any(
            "\u2014" in str(p) or "learner error:" in str(p) or "cultural hook:" in str(p)
            for section in plan.get("content_outline", [])
            for p in section.get("points", [])
        )
    except Exception:
        return False


def _process_enrich_plans(track_id: str, results: list[dict], min_score: int = 9):
    """Enrich plans for modules with research at or above min_score."""
    import subprocess

    # Filter: modules with research score >= min_score AND not already enriched
    queue = []
    skipped = 0
    for r in results:
        info = r["info"]
        if info is None:
            continue
        score = info.get("score")
        if score is not None and score >= min_score:
            if _is_plan_already_enriched(track_id, r["slug"]):
                skipped += 1
                continue
            queue.append(r)

    track_name = _get_track_name(track_id)
    if not queue:
        print(f"No {track_name} modules need enrichment ({skipped} already enriched).")
        return

    total = len(queue)
    print(f"\n{BOLD}{track_name}: Enriching plans for {total} module(s) (research {min_score}+/10, {skipped} already done){RESET}")
    print("\u2550" * 70)

    passed = 0
    failed = 0
    for i, r in enumerate(queue, 1):
        num = r["num"]
        slug = r["slug"]
        score = (r["info"] or {}).get("score", "?")
        print(f"\n[{i}/{total}] M{num:02d} {slug} (research: {score}/10)")
        print("\u2500" * 50)

        cmd = [
            str(SCRIPTS_DIR / ".." / ".venv" / "bin" / "python"),
            str(SCRIPTS_DIR / "build_module_v5.py"),
            track_id, str(num), "--force-phase", "research",
        ]
        try:
            result = subprocess.run(cmd, timeout=300)
            if result.returncode == 0:
                passed += 1
                print(f"  {BOLD}\033[32mENRICHED{RESET}")
            else:
                failed += 1
                print(f"  {BOLD}\033[31mFAIL (exit {result.returncode}){RESET}")
        except subprocess.TimeoutExpired:
            failed += 1
            print(f"  {BOLD}\033[31mTIMEOUT (5min){RESET}")
        except KeyboardInterrupt:
            print(f"\n\nInterrupted after {i-1}/{total} modules ({passed} enriched, {failed} failed)")
            return

    print(f"\n{'=' * 70}")
    print(f"Done: {passed} enriched, {failed} failed out of {total} ({skipped} previously enriched)")
    print()


# ==================== MAIN ====================


def _coverage_for_track(track_id: str, manifest: dict) -> dict:
    """Compute research coverage for a track. Returns {total, researched, gaps: [slug]}."""
    track_cfg = next((t for t in TRACKS if t["id"] == track_id), None)
    if not track_cfg:
        return {"total": 0, "researched": 0, "gaps": []}
    track_dir = CURRICULUM_ROOT / track_cfg["path"]
    modules_list = manifest.get("levels", {}).get(track_id, {}).get("modules", [])
    gaps = []
    researched = 0
    for m_entry in modules_list:
        slug = _parse_slug(m_entry)
        rp = find_research_path(track_dir, slug)
        if rp:
            researched += 1
        else:
            gaps.append(slug)
    return {"total": len(modules_list), "researched": researched, "gaps": gaps}


def _render_coverage_table(track_id: str, manifest: dict):
    """Render coverage table for a single track."""
    cov = _coverage_for_track(track_id, manifest)
    track_name = _get_track_name(track_id)
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


def _compute_all_coverage(manifest: dict) -> dict[str, dict]:
    """Compute coverage for all non-empty tracks. Returns {track_id: coverage_dict}."""
    result = {}
    for track_cfg in TRACKS:
        tid = track_cfg["id"]
        cov = _coverage_for_track(tid, manifest)
        if cov["total"] > 0:
            result[tid] = cov
    return result


def _render_all_coverage(all_cov: dict[str, dict]):
    """Render coverage overview table from pre-computed coverage data."""
    print(f"\n{BOLD}Research Coverage Overview{RESET}")
    print("\u2550" * 70)
    print(f"{'Track':<14} {'Manifest':>8} {'Research':>9} {'Gaps':>5}  {'Coverage':>9}")
    print("\u2500" * 70)
    total_gaps = 0
    for track_cfg in TRACKS:
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


def _handle_coverage_mode(args, manifest, parser):
    """Handle --coverage flag."""
    if args.all:
        all_cov = _compute_all_coverage(manifest)
        if args.json:
            print(json.dumps(all_cov, indent=2, ensure_ascii=False))
        else:
            _render_all_coverage(all_cov)
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
        _render_coverage_table(track_id, manifest)
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
        _render_all_overview(manifest)


def _handle_single_track(args, track_id, results, manifest):
    """Handle single-track modes: upgrade, enrich, refresh, single module, list."""
    if args.upgrade:
        _render_upgrade_queue(track_id, results, args.min_score)
        if not args.dry_run:
            _process_upgrade_queue(track_id, results, args.min_score)
        return

    if args.enrich:
        _process_enrich_plans(track_id, results, args.min_score)
        return

    if args.refresh:
        _render_refresh_queue(track_id, results)
        if not args.dry_run:
            _process_refresh_queue(track_id, results)
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
        _render_quality_table(track_id, results, manifest, show_gaps=args.gaps)
    else:
        _render_coverage_only(track_id, results)


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
