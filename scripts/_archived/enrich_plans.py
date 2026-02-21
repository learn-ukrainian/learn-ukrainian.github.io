#!/usr/bin/env python3
"""Batch Plan Enrichment — Feed research findings back into plan YAML files.

Reads plan YAML + research MD for each module, dispatches to Gemini Flash
to produce enriched content_outline + vocabulary_hints, validates, and writes
the enriched plan (with backup).

Usage:
    .venv/bin/python scripts/enrich_plans.py a2 3                   # Single module
    .venv/bin/python scripts/enrich_plans.py a2 --all               # All modules in track
    .venv/bin/python scripts/enrich_plans.py a2 --range 1-20        # Range of modules
    .venv/bin/python scripts/enrich_plans.py a2 --all --dry-run     # Preview only
    .venv/bin/python scripts/enrich_plans.py --all-core             # A1 through C1
    .venv/bin/python scripts/enrich_plans.py --all-tracks           # ALL tracks
    .venv/bin/python scripts/enrich_plans.py c2 --all               # C2 only
    .venv/bin/python scripts/enrich_plans.py b2-hist --all          # Seminar track

Tracked in: GitHub issue #598
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ---------------------------------------------------------------------------
# Setup: ensure scripts/ is on sys.path
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

import yaml
from batch_gemini_config import (
    CURRICULUM_DIR,
    FLASH_MODEL,
    PHASES_DIR,
    PROJECT_ROOT,
    get_module_index,
    get_module_paths,
    slug_for_num,
)
from build_module import dispatch_gemini, log, _init_log

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEMPLATE_PATH = PHASES_DIR / "plan-enrichment.md"
MIN_RESEARCH_LENGTH = 200  # Skip if research is shorter than this

# All core tracks in priority order
CORE_TRACKS = ["a1", "a2", "b1", "b2", "c1", "c2"]

# All tracks including C2 and seminars
ALL_TRACKS = [
    "a1", "a2", "b1", "b2", "c1", "c2",
    "b2-hist", "c1-bio", "c1-hist",
    "lit", "lit-essay", "lit-hist-fic", "lit-fantastika", "lit-war", "lit-humor", "lit-juvenile",
    "oes", "ruth", "b2-pro", "c1-pro",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def extract_between(text: str, start_delim: str, end_delim: str) -> str | None:
    """Extract text between two delimiter lines (exclusive).

    Uses the LAST occurrence of the start delimiter to skip prompt echoes
    (the broker echoes the full prompt before Gemini's actual output).
    """
    start_idx = text.rfind(start_delim)
    if start_idx == -1:
        return None
    start_idx += len(start_delim)
    end_idx = text.find(end_delim, start_idx)
    if end_idx == -1:
        return None
    return text[start_idx:end_idx].strip()


def validate_enrichment(enriched: dict, original_plan: dict) -> list[str]:
    """Validate enriched outline against structural rules. Returns list of errors."""
    errors = []
    outline = enriched.get("content_outline", [])
    word_target = original_plan.get("word_target", 0)
    has_explicit_target = "word_target" in original_plan

    if not isinstance(outline, list):
        return ["content_outline is not a list"]

    total_words = sum(s.get("words", 0) for s in outline if isinstance(s, dict))

    # If plan has no explicit word_target, use Gemini's proposed sum as reference
    # (validates structure only, not word budget adherence)
    if not has_explicit_target:
        word_target = total_words if total_words > 0 else 2000

    # Section count
    min_sections = 5 if word_target >= 3000 else 4
    if len(outline) < min_sections:
        errors.append(f"only {len(outline)} sections (need {min_sections}+)")

    # Word allocation sum — only enforce when plan has an explicit target
    if has_explicit_target and word_target > 0 and abs(total_words - word_target) > word_target * 0.10:
        errors.append(f"word sum {total_words} too far from target {word_target} (>10%)")

    # No monolithic sections (>35% of target)
    max_section_words = word_target * 0.35
    for s in outline:
        if not isinstance(s, dict):
            errors.append(f"section is not a dict: {s!r}")
            continue
        section_words = s.get("words", 0)
        if section_words > max_section_words:
            errors.append(
                f"section '{s.get('section', '?')}' too large: "
                f"{section_words}w > {int(max_section_words)}w (35%)"
            )

    # Each section has points
    for s in outline:
        if not isinstance(s, dict):
            continue
        if not s.get("points"):
            errors.append(f"section '{s.get('section', '?')}' has no points")

    return errors


def clear_build_state(track: str, num: int) -> None:
    """Clear v3/v2 build state for a module so --all rebuild doesn't skip it."""
    slug = slug_for_num(track, num)
    paths = get_module_paths(track, slug)
    orch_dir = paths["orchestration"]
    phase_ids = [
        "v3-A", "v3-B", "v3-C", "v3-audit", "v3-D", "v3-E", "v3-F",
        "9-final-review",
    ]
    for state_file in [orch_dir / "state-v3.json", orch_dir / "state.json"]:
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            phases = state.get("phases", {})
            for sid in phase_ids:
                phases.pop(sid, None)
            state_file.write_text(
                json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except (json.JSONDecodeError, KeyError):
            pass


def enrich_module(
    track: str, num: int, *, dry_run: bool = False
) -> str:
    """Enrich a single module's plan with research findings.

    Returns: "ok", "skip", "fail", or "no-plan".
    """
    slug = slug_for_num(track, num)
    paths = get_module_paths(track, slug)
    plan_path = paths["plan"]
    research_path = paths["research"]
    orch_dir = paths["orchestration"]

    log(f"  [{track}#{num}] {slug}")

    # 1. Check plan exists
    if not plan_path.exists():
        log(f"    SKIP: no plan file at {plan_path}")
        return "no-plan"

    plan_text = plan_path.read_text(encoding="utf-8")
    plan = yaml.safe_load(plan_text)
    if not plan:
        log(f"    SKIP: plan file is empty")
        return "no-plan"

    # 2. Check research exists and is substantial
    if not research_path.exists():
        log(f"    SKIP: no research file")
        return "skip"

    research_text = research_path.read_text(encoding="utf-8")
    if len(research_text.strip()) < MIN_RESEARCH_LENGTH:
        log(f"    SKIP: research too short ({len(research_text.strip())} chars)")
        return "skip"

    # 3. Quick pre-check: does plan already have enriched outline?
    existing_outline = plan.get("content_outline", [])
    if isinstance(existing_outline, list) and len(existing_outline) >= 5:
        has_words = all(
            isinstance(s, dict) and s.get("words", 0) > 0
            for s in existing_outline
        )
        if has_words:
            log(f"    SKIP: plan already has {len(existing_outline)} sections with word allocations")
            return "skip"

    if dry_run:
        word_target = plan.get("word_target", 2000)
        log(f"    DRY-RUN: would enrich (word_target={word_target}, "
            f"current sections={len(existing_outline)}, "
            f"research={len(research_text)} chars)")
        return "ok"

    # 4. Build prompt
    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    prompt = template_text.replace("{PLAN_YAML}", plan_text)
    prompt = prompt.replace("{RESEARCH_MD}", research_text)

    # 5. Dispatch to Gemini Flash
    task_id = f"enrich-{slug}"
    output_file = orch_dir / f"{slug}-enrichment.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    ok, output = dispatch_gemini(
        prompt,
        task_id=task_id,
        model=FLASH_MODEL,
        stdout_only=True,
        output_file=output_file,
        timeout=300,
    )

    if not ok or not output.strip():
        log(f"    FAIL: Gemini dispatch failed or empty output")
        return "fail"

    # 6. Extract delimited sections
    outline_yaml = extract_between(
        output, "===ENRICHED_OUTLINE_START===", "===ENRICHED_OUTLINE_END==="
    )
    vocab_yaml = extract_between(
        output, "===ENRICHED_VOCAB_START===", "===ENRICHED_VOCAB_END==="
    )

    if not outline_yaml:
        log(f"    FAIL: could not extract ENRICHED_OUTLINE from output")
        return "fail"

    # 7. Parse and validate
    try:
        enriched = yaml.safe_load(outline_yaml)
    except yaml.YAMLError as e:
        log(f"    FAIL: YAML parse error in outline: {e}")
        return "fail"

    if not isinstance(enriched, dict):
        log(f"    FAIL: parsed outline is not a dict")
        return "fail"

    errors = validate_enrichment(enriched, plan)
    if errors:
        log(f"    FAIL: validation errors:")
        for err in errors:
            log(f"      - {err}")
        return "fail"

    # 8. Merge — only content_outline and vocabulary_hints
    plan["content_outline"] = enriched["content_outline"]

    if vocab_yaml:
        try:
            vocab = yaml.safe_load(vocab_yaml)
            if isinstance(vocab, dict) and "vocabulary_hints" in vocab:
                plan["vocabulary_hints"] = vocab["vocabulary_hints"]
        except yaml.YAMLError:
            log(f"    WARN: could not parse vocabulary YAML — keeping original")

    # 9. Write enriched plan (backup original first)
    backup_path = plan_path.with_suffix(".yaml.bak")
    if not backup_path.exists():
        shutil.copy2(plan_path, backup_path)
        log(f"    Backed up original to {backup_path.name}")

    plan_path.write_text(
        yaml.dump(plan, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    # 10. Clear v3 + v2 state (force full pipeline re-run from enriched plan)
    _PHASE_IDS_TO_CLEAR = [
        "v3-A", "v3-B", "v3-C", "v3-audit", "v3-D", "v3-E", "v3-F",
        "9-final-review",  # Also clear final review so --all doesn't skip
    ]
    for state_file in [orch_dir / "state-v3.json", orch_dir / "state.json"]:
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            phases = state.get("phases", {})
            cleared = []
            for sid in _PHASE_IDS_TO_CLEAR:
                if sid in phases:
                    del phases[sid]
                    cleared.append(sid)
            if cleared:
                state_file.write_text(
                    json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                log(f"    Cleared {state_file.name}: {', '.join(cleared)}")
        except (json.JSONDecodeError, KeyError):
            log(f"    WARN: could not parse {state_file.name} — skipping state clear")

    # Report enrichment stats
    new_outline = plan["content_outline"]
    total_words = sum(s.get("words", 0) for s in new_outline if isinstance(s, dict))
    log(f"    OK: {len(new_outline)} sections, {total_words}w allocated "
        f"(target: {plan.get('word_target', '?')})")

    return "ok"


def enrich_track(
    track: str, *, dry_run: bool = False,
    num_range: tuple[int, int] | None = None, jobs: int = 1,
) -> dict:
    """Enrich all modules in a track. Returns counts by result type."""
    idx = get_module_index(track)
    total = idx["total"]
    start, end = num_range if num_range else (1, total)

    log(f"\n{'='*60}")
    log(f"Enriching {track.upper()} — modules {start}-{end} of {total}"
        f" (jobs={jobs})")
    log(f"{'='*60}")

    counts: dict[str, int] = {"ok": 0, "skip": 0, "fail": 0, "no-plan": 0}
    modules = list(range(start, end + 1))

    def _run_one(num: int) -> tuple[int, str]:
        try:
            return num, enrich_module(track, num, dry_run=dry_run)
        except (ValueError, FileNotFoundError) as e:
            log(f"  [{track}#{num}] ERROR: {e}")
            return num, "fail"

    if jobs <= 1:
        for num in modules:
            _, result = _run_one(num)
            counts[result] = counts.get(result, 0) + 1
    else:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = {pool.submit(_run_one, num): num for num in modules}
            for future in as_completed(futures):
                num, result = future.result()
                counts[result] = counts.get(result, 0) + 1

    log(f"\n{track.upper()} summary: "
        f"{counts['ok']} ok, {counts['skip']} skip, "
        f"{counts['fail']} fail, {counts['no-plan']} no-plan")
    return counts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_range(range_str: str) -> tuple[int, int]:
    """Parse '1-20' into (1, 20)."""
    m = re.match(r"^(\d+)-(\d+)$", range_str)
    if not m:
        raise argparse.ArgumentTypeError(f"Invalid range: {range_str!r} (expected N-M)")
    return int(m.group(1)), int(m.group(2))


def main():
    parser = argparse.ArgumentParser(
        description="Enrich plan YAML files with research findings via Gemini Flash"
    )
    parser.add_argument("track", nargs="?", help="Track name (a1, b2-hist, lit, ...)")
    parser.add_argument("num", nargs="?", type=int, help="Module number (1-indexed)")
    parser.add_argument("--all", action="store_true", help="All modules in track")
    parser.add_argument("--range", dest="range_str", help="Module range (e.g., 1-20)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no writes")
    parser.add_argument("--all-core", action="store_true", help="All core tracks (A1-C2)")
    parser.add_argument("--all-tracks", action="store_true", help="ALL tracks")
    parser.add_argument("-j", "--jobs", type=int, default=4,
                        help="Parallel Gemini calls (default: 4)")
    parser.add_argument("--clear-state", action="store_true",
                        help="Only clear build state (no enrichment) — use after enrichment "
                             "to force v3 rebuild")

    args = parser.parse_args()

    # Initialize logging
    _init_log("enrich-plans")

    t0 = time.time()
    grand_counts: dict[str, int] = {"ok": 0, "skip": 0, "fail": 0, "no-plan": 0}

    if args.all_core:
        tracks = CORE_TRACKS
    elif args.all_tracks:
        tracks = ALL_TRACKS
    elif args.track:
        tracks = [args.track]
    else:
        parser.error("Provide a track name, --all-core, or --all-tracks")

    # Clear-state-only mode
    if args.clear_state:
        total = 0
        for track in tracks:
            idx = get_module_index(track)
            start, end = parse_range(args.range_str) if args.range_str else (1, idx["total"])
            for num in range(start, end + 1):
                clear_build_state(track, num)
                total += 1
            log(f"Cleared state for {track.upper()} #{start}-{end}")
        log(f"\nCleared {total} modules. Ready for rebuild.")
        sys.exit(0)

    # Single module mode
    if args.num and not args.all and not args.range_str:
        if len(tracks) != 1:
            parser.error("Cannot specify module number with --all-core or --all-tracks")
        result = enrich_module(tracks[0], args.num, dry_run=args.dry_run)
        log(f"\nResult: {result}")
        sys.exit(0 if result in ("ok", "skip") else 1)

    # Batch mode
    for track in tracks:
        try:
            num_range = parse_range(args.range_str) if args.range_str else None
            if not args.all and not args.range_str and not args.all_core and not args.all_tracks:
                parser.error(f"Specify --all, --range, --all-core, or --all-tracks for batch mode")
            counts = enrich_track(track, dry_run=args.dry_run, num_range=num_range, jobs=args.jobs)
            for k, v in counts.items():
                grand_counts[k] = grand_counts.get(k, 0) + v
        except ValueError as e:
            log(f"\nERROR: Track {track!r}: {e}")
            grand_counts["fail"] += 1

    elapsed = time.time() - t0
    m, s = divmod(int(elapsed), 60)

    log(f"\n{'='*60}")
    log(f"GRAND TOTAL: {grand_counts['ok']} ok, {grand_counts['skip']} skip, "
        f"{grand_counts['fail']} fail, {grand_counts['no-plan']} no-plan")
    log(f"Elapsed: {m}m {s:02d}s")
    log(f"{'='*60}")

    sys.exit(0 if grand_counts["fail"] == 0 else 1)


if __name__ == "__main__":
    main()
