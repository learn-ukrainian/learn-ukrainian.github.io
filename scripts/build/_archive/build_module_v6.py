#!/usr/bin/env python3
"""E2E Module Builder v6 — minimal LLM calls, no fix loops.

Usage:
    %(prog)s a1 3                          # Full build
    %(prog)s a1 3 --restart-from content   # Restart from content phase
    %(prog)s a1 3 --rebuild                # Nuke state, restart
    %(prog)s a1 3 --dry-run                # Show plan, no dispatches
    %(prog)s a1 3 --preflight-only         # Stop after preflight

Issue: #960
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import yaml
from batch_gemini_config import (
    PROJECT_ROOT,
    get_module_paths,
    get_track_config,
    slug_for_num,
)
from pipeline.core import (
    ModuleContext,
    build_placeholders,
    log,
)
from pipeline.state import load_state, save_state

# ---------------------------------------------------------------------------
# Phase names (in order)
# ---------------------------------------------------------------------------

V6_PHASES = ["preflight", "content", "activities", "audit", "review", "final_audit"]


def _build_ctx(args: argparse.Namespace) -> ModuleContext:
    """Build ModuleContext from CLI args."""
    track = args.track.lower()
    module_num = args.module_num
    slug = slug_for_num(track, module_num)
    if not slug:
        print(f"ERROR: No slug found for {track} #{module_num}")
        sys.exit(1)

    track_config = get_track_config(track)
    paths = get_module_paths(track, slug)

    # Read plan
    plan_path = paths.get("plan")
    plan = {}
    if plan_path and plan_path.exists():
        plan = yaml.safe_load(plan_path.read_text("utf-8")) or {}

    # Word target from config
    from audit.config import LEVEL_CONFIG
    base = track.split("-")[0].upper()
    level_cfg = LEVEL_CONFIG.get(base, {})
    word_target = level_cfg.get("target_words", 1200)

    # Resolve writer/reviewer models
    writer_model = _resolve_model(args.writer) if args.writer else track_config.get("model", "gemini-3-flash-preview")
    reviewer_model = _resolve_model(args.reviewer) if args.reviewer else _auto_reviewer(writer_model)

    ctx = ModuleContext(
        track=track,
        module_num=module_num,
        slug=slug,
        mode="v6",
        word_target=word_target,
        paths=paths,
        plan=plan,
        track_config=track_config,
        model=writer_model,
        dry_run=args.dry_run,
    )
    ctx.writer_model = writer_model  # type: ignore[attr-defined]
    ctx.reviewer_model = reviewer_model  # type: ignore[attr-defined]

    # Set orchestration dir
    ctx.orch_dir = paths.get("orchestration", paths["md"].parent / "orchestration" / slug)
    ctx.orch_dir.mkdir(parents=True, exist_ok=True)

    # Build placeholders
    build_placeholders(ctx)

    return ctx


# Model name aliases → actual model IDs
_MODEL_ALIASES = {
    "gemini-flash": "gemini-3-flash-preview",
    "flash": "gemini-3-flash-preview",
    "gemini-pro": "gemini-3.1-pro-preview",
    "pro": "gemini-3.1-pro-preview",
    "claude-sonnet": "claude-sonnet-4-6",
    "sonnet": "claude-sonnet-4-6",
    "claude-opus": "claude-opus-4-6",
    "opus": "claude-opus-4-6",
}


def _resolve_model(name: str) -> str:
    """Resolve model alias to actual model ID."""
    return _MODEL_ALIASES.get(name.lower(), name)


def _auto_reviewer(writer_model: str) -> str:
    """Pick the opposite agent's strong model as reviewer."""
    if writer_model.startswith("claude"):
        return "gemini-3.1-pro-preview"
    return "claude-opus-4-6"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pipeline v6 — minimal LLM calls, no fix loops",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("track", help="Track (e.g., a1, b1, hist)")
    parser.add_argument("module_num", type=int, help="Module number")
    parser.add_argument("--dry-run", action="store_true", help="Show plan, no dispatches")
    parser.add_argument("--rebuild", action="store_true", help="Nuke state, restart from scratch")
    parser.add_argument("--restart-from", dest="restart_from", type=str, default=None,
                        choices=V6_PHASES, help="Restart from this phase")
    parser.add_argument("--preflight-only", action="store_true", dest="preflight_only",
                        help="Stop after preflight phase")
    parser.add_argument("--writer", type=str, default=None,
                        help="Writer model (e.g., gemini-flash, gemini-pro, claude-sonnet, claude-opus)")
    parser.add_argument("--reviewer", type=str, default=None,
                        help="Reviewer model (e.g., gemini-pro, claude-opus, claude-sonnet)")

    args = parser.parse_args()
    t0 = time.time()

    ctx = _build_ctx(args)
    log(f"Module: {ctx.track} #{ctx.module_num} → {ctx.slug}")

    # Handle --rebuild
    state = load_state(ctx)
    if args.rebuild:
        state = {"phases": {}}
        save_state(ctx, state)
        log("State: Rebuilt from scratch")

    # Handle --restart-from
    if args.restart_from:
        restart_idx = V6_PHASES.index(args.restart_from)
        for phase in V6_PHASES[restart_idx:]:
            state.get("phases", {}).pop(phase, None)
        save_state(ctx, state)
        log(f"State: Restarting from {args.restart_from}")

    log(f"Log: {PROJECT_ROOT / 'logs' / f'build-{ctx.slug}-v6.log'}")

    # Import v6 pipeline
    from pipeline_v6 import (
        phase_audit,
        phase_final_audit,
        phase_preflight,
        phase_review_fix,
        phase_write_activities,
        phase_write_content,
    )

    # Run phases
    ok = True

    # Phase 1: Preflight
    if ok:
        ok = phase_preflight(ctx, state)
    if args.preflight_only:
        log("  PREFLIGHT-ONLY — stopping")
        elapsed = time.time() - t0
        log(f"\nVERDICT: PARTIAL — preflight only (v6) [{elapsed:.0f}s]")
        return 0

    # Phase 2: Write content
    if ok:
        ok = phase_write_content(ctx, state)

    # Phase 3: Write activities + vocabulary
    if ok:
        ok = phase_write_activities(ctx, state)

    # Phase 4: Deterministic audit
    audit_passed = False
    audit_output = ""
    if ok:
        audit_passed, audit_output = phase_audit(ctx, state)
        if audit_passed:
            log("  pipeline: Audit passed — skipping review")
            ok = True
        else:
            # Phase 5: Review + fix
            ok = phase_review_fix(ctx, state, audit_output)
            if ok:
                # Phase 6: Final audit
                ok = phase_final_audit(ctx, state)

    elapsed = time.time() - t0
    verdict = "PASS" if ok else "FAIL"
    log(f"\nVERDICT: {verdict} (v6) [{elapsed:.0f}s]")

    # Save completion report
    completion = ctx.orch_dir / "completion.md"
    completion.write_text(
        f"{verdict}: pipeline {ctx.track} {ctx.module_num}\n\n"
        f"  Module:   {ctx.slug}\n"
        f"  Track:    {ctx.track}\n"
        f"  Mode:     v6\n"
        f"  Words:    {len(ctx.paths['md'].read_text('utf-8').split()) if ctx.paths['md'].exists() else 0}"
        f" (target: {ctx.word_target})\n"
        f"  Verdict:  {verdict}\n"
        f"  Date:     {datetime.now(UTC).isoformat()}\n",
        "utf-8",
    )

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
