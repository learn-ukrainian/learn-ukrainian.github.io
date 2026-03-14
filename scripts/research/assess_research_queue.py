"""Queue processing helpers for assess_research.py -- upgrade, refresh, enrich.

Extracted from assess_research_helpers.py to improve maintainability index.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml
from assess_research_helpers import (
    BOLD,
    RESET,
    _build_refresh_queue,
    _build_upgrade_queue,
)
from research_quality import (
    assess_research_compat,
    find_research_path,
)


def _upgrade_single_module(
    track_id: str,
    r: dict,
    min_score: int,
    max_attempts: int,
    scripts_dir: Path,
    curriculum_root: Path,
    clear_v3_fn,
) -> tuple[bool, int, str | int]:
    """Upgrade a single module's research. Returns (passed, attempts_used, last_score)."""
    num = r["num"]
    slug = r["slug"]
    old_score = (r["info"] or {}).get("score", "?")
    last_score = old_score
    attempts_used = 0

    for attempt in range(1, max_attempts + 1):
        attempts_used = attempt
        clear_v3_fn(track_id, slug)
        track_dir = curriculum_root / track_id
        old_rp = find_research_path(track_dir, slug)
        if old_rp and old_rp.exists():
            backup = old_rp.with_suffix(".md.bak")
            old_rp.rename(backup)
            print(f"  Backed up old research -> {backup.name}")

        cmd = [
            str(scripts_dir / ".." / ".venv" / "bin" / "python"),
            str(scripts_dir / "build_module_v5.py"),
            track_id, str(num), "--force-phase", "research", "--rebuild",
        ]
        try:
            result = subprocess.run(cmd, timeout=900)
            if result.returncode == 0:
                rp = find_research_path(track_dir, slug)
                if rp:
                    new_info = assess_research_compat(rp, track_id)
                    new_score = (new_info or {}).get("score", "?")
                    print(f"  Attempt {attempt}: {last_score}/10 -> {new_score}/10", end="")
                    if isinstance(new_score, int) and new_score >= min_score:
                        print(f" {BOLD}\033[32m\u2713{RESET}")
                        last_score = new_score
                        if clear_v3_fn(track_id, slug):
                            print("  v3 Phase A reset")
                        return True, attempts_used, last_score
                    elif attempt < max_attempts:
                        print(f" (below {min_score}, retrying...)")
                        last_score = new_score
                    else:
                        print(f" {BOLD}\033[33mstill below {min_score} after {max_attempts} attempts{RESET}")
                        last_score = new_score
                else:
                    print(f"  Attempt {attempt}: {BOLD}\033[31mno research file after build{RESET}")
                    return False, attempts_used, last_score
            else:
                print(f"  Attempt {attempt}: {BOLD}\033[31mFAIL (exit {result.returncode}){RESET}")
                return False, attempts_used, last_score
        except subprocess.TimeoutExpired:
            print(f"  Attempt {attempt}: {BOLD}\033[31mTIMEOUT (15min){RESET}")
            return False, attempts_used, last_score

    return False, attempts_used, last_score


def _process_upgrade_queue(
    track_id: str,
    results: list[dict],
    min_score: int,
    max_attempts: int,
    scripts_dir: Path,
    curriculum_root: Path,
    clear_v3_fn,
    get_track_name_fn,
):
    """Process the upgrade queue -- regenerate research with retries."""
    queue = _build_upgrade_queue(results, min_score)
    if not queue:
        print(f"All modules at {min_score}/10+. Nothing to upgrade.")
        return

    track_name = get_track_name_fn(track_id)
    total = len(queue)
    print(f"\n{BOLD}{track_name}: Upgrading research for {total} module(s) (max {max_attempts} attempts each){RESET}")
    print("\u2550" * 70)

    passed = 0
    failed = 0
    attempt_log = []
    for i, r in enumerate(queue, 1):
        num = r["num"]
        slug = r["slug"]
        old_score = (r["info"] or {}).get("score", "?")
        print(f"\n[{i}/{total}] M{num:02d} {slug} (current: {old_score}/10)")
        print("\u2500" * 50)

        try:
            module_passed, attempts_used, last_score = _upgrade_single_module(
                track_id, r, min_score, max_attempts,
                scripts_dir, curriculum_root, clear_v3_fn,
            )
        except KeyboardInterrupt:
            print(f"\n\nInterrupted at M{num:02d}")
            print(f"Progress: {passed} passed, {failed} failed out of {i}/{total} modules")
            return

        attempt_log.append((slug, attempts_used, last_score))
        if module_passed:
            passed += 1
        else:
            failed += 1

    print(f"\n{'=' * 70}")
    print(f"Done: {passed} upgraded to {min_score}+, {failed} still below")
    multi = [(s, a) for s, a, _ in attempt_log if a > 1]
    if multi:
        print(f"Multi-attempt: {', '.join(f'{s}({a}x)' for s, a in multi)}")
    print()


def _process_refresh_queue(track_id: str, results: list[dict], scripts_dir: Path):
    """Process the refresh queue -- run build_module_v5.py --refresh for each module."""
    queue = _build_refresh_queue(results)
    if not queue:
        print("No modules need content refresh.")
        return

    total = len(queue)
    print(f"\n{BOLD}Processing {total} module(s){RESET}")
    print("\u2550" * 70)

    passed = 0
    failed = 0
    for i, r in enumerate(queue, 1):
        num = r["num"]
        slug = r["slug"]
        print(f"\n[{i}/{total}] M{num:02d} {slug}")
        print("\u2500" * 50)

        cmd = [
            str(scripts_dir / ".." / ".venv" / "bin" / "python"),
            str(scripts_dir / "build_module_v5.py"),
            track_id, str(num), "--refresh",
        ]
        try:
            result = subprocess.run(cmd, timeout=900)
            if result.returncode == 0:
                passed += 1
                print(f"  {BOLD}\033[32mPASS{RESET}")
            else:
                failed += 1
                print(f"  {BOLD}\033[31mFAIL (exit {result.returncode}){RESET}")
        except subprocess.TimeoutExpired:
            failed += 1
            print(f"  {BOLD}\033[31mTIMEOUT (15min){RESET}")
        except KeyboardInterrupt:
            print(f"\n\nInterrupted after {i-1}/{total} modules ({passed} passed, {failed} failed)")
            return

    print(f"\n{'=' * 70}")
    print(f"Done: {passed} passed, {failed} failed out of {total}")
    print()


def _is_plan_already_enriched(curriculum_root: Path, track_id: str, slug: str) -> bool:
    """Check if a plan already has enrichment markers."""
    plan_path = curriculum_root / "plans" / track_id / f"{slug}.yaml"
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


def _process_enrich_plans(
    track_id: str,
    results: list[dict],
    min_score: int,
    scripts_dir: Path,
    curriculum_root: Path,
    get_track_name_fn,
):
    """Enrich plans for modules with research at or above min_score."""
    queue = []
    skipped = 0
    for r in results:
        info = r["info"]
        if info is None:
            continue
        score = info.get("score")
        if score is not None and score >= min_score:
            if _is_plan_already_enriched(curriculum_root, track_id, r["slug"]):
                skipped += 1
                continue
            queue.append(r)

    track_name = get_track_name_fn(track_id)
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
            str(scripts_dir / ".." / ".venv" / "bin" / "python"),
            str(scripts_dir / "build_module_v5.py"),
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
