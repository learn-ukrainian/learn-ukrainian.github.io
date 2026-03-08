#!/usr/bin/env python3
"""E2E Module Builder v5 — clean pipeline CLI (no v2/v3 legacy).

Usage:
    %(prog)s a1 12                           # RC mode (no review)
    %(prog)s a1 12 --review                  # Full mode (with Gemini review)
    %(prog)s a1 12 --review-claude           # Full mode (with Claude review)
    %(prog)s a1 --all                        # Build entire track
    %(prog)s a1 --range 1-20                 # Build range
    %(prog)s a1 12 --rebuild                 # Nuke state, restart
    %(prog)s a1 12 --dry-run                 # Show plan, no dispatches
    %(prog)s a1 12 --verify                  # Just audit
    %(prog)s a1 12 --force-phase validate    # Re-run validate only
    %(prog)s a1 12 --restart-from review     # Run: review → mdx
    %(prog)s a1 12 --stop-before review      # Stop before review phase

Issue: #750
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
import time
from pathlib import Path

# Ensure scripts/ is on sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

# Import v5 pipeline
from batch_gemini_config import (
    CURRICULUM_DIR,
    PRO_TRACKS,
    SEMINAR_TRACKS,
    get_module_index,
    get_module_paths,
    slug_for_num,
)
from pipeline_lib import (
    ModuleContext,
    _init_log,
    log,
    preflight_v2,
    run_verify,
    write_completion_report_v2,
    write_placeholders,
)
from pipeline_v5 import (
    CLAUDE_MODEL_ACTIVITIES,
    CLAUDE_MODEL_REVIEW,
    PHASE_FUNCTIONS,
    PHASES,
    load_state,
    run_pipeline,
)

# ============================================================================
# Preflight
# ============================================================================

def preflight(args: argparse.Namespace) -> ModuleContext:
    """Resolve all paths, load plan/meta, set pipeline attributes.

    Calls pipeline_lib.preflight_v2 for common setup (paths, plan, meta),
    then adds v5-specific flags. No v3 delegation.
    """
    ctx = preflight_v2(args)

    # Mode
    ctx.mode = "v5"  # type: ignore[attr-defined]
    ctx.state["mode"] = "v5"

    # Review flags
    ctx.review = getattr(args, "review", False) or getattr(args, "review_claude", False)  # type: ignore[attr-defined]
    ctx.skip_discover = getattr(args, "skip_discover", False)  # type: ignore[attr-defined]
    ctx.review_agent = "claude" if getattr(args, "review_claude", False) else "gemini"  # type: ignore[attr-defined]

    # --stop-before
    sb = getattr(args, "stop_before", None)
    if sb:
        sb_lower = sb.lower()
        if sb_lower not in PHASE_FUNCTIONS:
            log(f"  ERROR: Unknown phase '{sb}'. Valid: {', '.join(PHASES)}")
            raise SystemExit(1)
        ctx.stop_before_phase = sb_lower  # type: ignore[attr-defined]
    else:
        ctx.stop_before_phase = None  # type: ignore[attr-defined]

    # --restart-from
    rf = getattr(args, "restart_from", None)
    if rf:
        ctx.restart_from = rf.lower()  # type: ignore[attr-defined]

    # --force-phase
    ctx.force_phase = getattr(args, "force_phase", None)  # type: ignore[attr-defined]

    # --use-claude: set of phase IDs to dispatch via Claude
    use_claude_str = getattr(args, "use_claude", "") or ""
    ctx.use_claude = set(use_claude_str.replace(",", " ").upper().split()) if use_claude_str else set()  # type: ignore[attr-defined]

    # Per-phase Claude model
    _is_seminar = ctx.track in SEMINAR_TRACKS or ctx.track in PRO_TRACKS
    _default_gen_model = "claude-opus-4-6" if _is_seminar else CLAUDE_MODEL_ACTIVITIES
    ctx.claude_model_A = getattr(args, "claude_model_A", None) or _default_gen_model  # type: ignore[attr-defined]
    ctx.claude_model_C = getattr(args, "claude_model_C", None) or _default_gen_model  # type: ignore[attr-defined]
    ctx.claude_model_D = getattr(args, "claude_model_D", None) or CLAUDE_MODEL_REVIEW  # type: ignore[attr-defined]

    # --gemini-model override
    gemini_model_override = getattr(args, "gemini_model", None)
    if gemini_model_override:
        ctx.model = gemini_model_override  # type: ignore[attr-defined]

    # --rebuild forces content regeneration
    if getattr(args, "rebuild", False):
        ctx.refresh = True  # type: ignore[attr-defined]

    # --full-build: single-call mode (content + activities + vocabulary)
    # Auto-enabled for beginner tier (A1, A2 M1-20, B1 M1-5) unless --no-full-build
    from pipeline_lib import _get_prompt_tier
    explicit_full = getattr(args, "full_build", False)
    no_full = getattr(args, "no_full_build", False)
    auto_full = _get_prompt_tier(ctx.track, ctx.module_num) == "beginner"
    ctx.full_build = (explicit_full or auto_full) and not no_full  # type: ignore[attr-defined]

    # RAG: auto-enabled when .gemini/settings.json exists (MCP tools available)
    explicit_rag = getattr(args, "rag", False)
    auto_rag = (SCRIPTS_DIR.parent / ".gemini" / "settings.json").exists()
    ctx.rag = explicit_rag or auto_rag  # type: ignore[attr-defined]

    # --max-fix override
    ctx.max_fix = getattr(args, "max_fix", None)  # type: ignore[attr-defined]

    # Research-only mode
    ctx.research_only = getattr(args, "research_only", False)  # type: ignore[attr-defined]

    return ctx


# ============================================================================
# Single Module Runner
# ============================================================================

def _run_single_module(args: argparse.Namespace) -> int:
    """Run the pipeline for a single module. Returns 0 on success, 1 on failure."""
    try:
        # --rebuild: clean orchestration directory
        if args.rebuild:
            slug = slug_for_num(args.track, args.num)
            paths = get_module_paths(args.track, slug)
            orch_dir = paths.get("orchestration") or (
                CURRICULUM_DIR / "l2-uk-en" / args.track / "orchestration" / slug
            )
            if orch_dir.is_dir():
                removed = 0
                for f in orch_dir.iterdir():
                    if f.is_file():
                        f.unlink()
                        removed += 1
                print(f"  --rebuild: cleaned orchestration dir ({removed} files removed)", flush=True)

        ctx = preflight(args)
        _init_log(ctx.slug)
        write_placeholders(ctx)

        t0 = time.time()
        state = load_state(ctx)
        ok = run_pipeline(
            ctx, state,
            research_only=getattr(ctx, "research_only", False),
        )
        elapsed = time.time() - t0
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

        write_completion_report_v2(ctx, ok)

        if ok:
            if ctx.dry_run:
                log(f"\nDRY-RUN COMPLETE — would build {ctx.slug} in v5 mode [{elapsed_str}]")
            elif ctx.force_phase:
                log(f"\nVERDICT: PASS — phase {ctx.force_phase} complete [{elapsed_str}]")
            elif getattr(ctx, "research_only", False):
                log(f"\nVERDICT: PASS — research complete (v5) [{elapsed_str}]")
            elif getattr(ctx, "stop_before_phase", None):
                log(f"\nVERDICT: PARTIAL — stopped early (v5) [{elapsed_str}]")
            else:
                _final_skip_review = not getattr(ctx, "review", False)
                passed, output = run_verify(ctx.paths["md"], content_only=False,
                                           skip_review=_final_skip_review)
                if passed:
                    log(f"\nVERDICT: PASS — {ctx.slug} fully complete (v5) [{elapsed_str}]")
                else:
                    log(f"\nVERDICT: FAIL — final verification failed [{elapsed_str}]")
                    for line in output.strip().split("\n")[-15:]:
                        log(f"  {line}")
                    return 1
            return 0
        else:
            log(f"\nPIPELINE FAILED — check logs in {ctx.orch_dir} [{elapsed_str}]")
            return 1

    except FileNotFoundError as e:
        print(f"ERROR: {e}", flush=True)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", flush=True)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user", flush=True)
        return 130


# ============================================================================
# Batch Runner
# ============================================================================

def _run_batch(args: argparse.Namespace, nums: list[int]) -> int:
    """Run the pipeline for a batch of modules. Returns 0 if all pass, 1 otherwise."""
    passed_list, failed_list, skipped_list = [], [], []
    t0_batch = time.time()

    for i, n in enumerate(nums, 1):
        slug = slug_for_num(args.track, n)
        print(f"\n{'='*70}", flush=True)
        print(f"[{i}/{len(nums)}] {args.track} #{n} — {slug}", flush=True)
        print(f"{'='*70}", flush=True)

        # Batch skip: avoid rebuilding modules that already pass
        if not args.rebuild and not args.force_phase:
            try:
                paths = get_module_paths(args.track, slug)
                if paths["md"].exists():
                    full_passed, _ = run_verify(paths["md"], content_only=False)
                    if full_passed:
                        # Check v5 state — if review requested but not done, fall through
                        orch_dir = paths["md"].parent / "orchestration" / slug
                        want_review = getattr(args, "review", False) or getattr(args, "review_claude", False)
                        if want_review:
                            v5_state = orch_dir / "state.json"
                            review_done = False
                            if v5_state.exists():
                                st = json.loads(v5_state.read_text("utf-8"))
                                review_done = st.get("phases", {}).get("review", {}).get("status") == "complete"
                            if not review_done:
                                print("  PARTIAL: audit passes, needs review", flush=True)
                            else:
                                print("  SKIP: passing audit + review done", flush=True)
                                skipped_list.append((n, slug))
                                continue
                        else:
                            print("  SKIP: already passing full audit", flush=True)
                            skipped_list.append((n, slug))
                            continue
            except (FileNotFoundError, ValueError, KeyError):
                pass  # Module not yet built — fall through to build

        single_args = argparse.Namespace(**{
            **vars(args),
            "num": n,
            "build_all": False,
            "build_range": None,
            "verify": False,
        })
        rc = _run_single_module(single_args)
        if rc == 0:
            passed_list.append((n, slug))
        else:
            # Auto-rebuild: if validate exhausted, attempt one rebuild
            _rebuilt_ok = False
            _no_auto_rebuild = getattr(args, "no_auto_rebuild", False)
            if not args.rebuild and not _no_auto_rebuild:
                try:
                    _rb_paths = get_module_paths(args.track, slug)
                    _rb_orch = _rb_paths["md"].parent / "orchestration" / slug
                    _needs_rebuild = False
                    _rb_v5 = _rb_orch / "state.json"
                    if _rb_v5.exists():
                        _rb_st = json.loads(_rb_v5.read_text("utf-8"))
                        for phase_key in ("review", "validate"):
                            _ph = _rb_st.get("phases", {}).get(phase_key, {})
                            if _ph.get("note", "").startswith("needs-"):
                                _needs_rebuild = True
                                break
                    if _needs_rebuild:
                        print("  AUTO-REBUILD: review exhausted — attempting rebuild...", flush=True)
                        rebuild_args = argparse.Namespace(**vars(single_args))
                        rebuild_args.rebuild = True
                        if _run_single_module(rebuild_args) == 0:
                            passed_list.append((n, slug))
                            print("  AUTO-REBUILD: SUCCESS", flush=True)
                            _rebuilt_ok = True
                        else:
                            print("  AUTO-REBUILD: FAILED — module needs manual attention", flush=True)
                except Exception as _rbe:
                    print(f"  AUTO-REBUILD: error checking state — {_rbe}", flush=True)
            if not _rebuilt_ok:
                failed_list.append((n, slug))
                print("  FAILED — continuing to next module", flush=True)

    elapsed = time.time() - t0_batch
    elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
    print(f"\n{'='*70}", flush=True)
    print(f"BATCH COMPLETE — {args.track} v5 [{elapsed_str}]", flush=True)
    print(f"  Passed:  {len(passed_list)}", flush=True)
    print(f"  Failed:  {len(failed_list)}", flush=True)
    print(f"  Skipped: {len(skipped_list)} (already passing)", flush=True)
    if failed_list:
        print("  Failed modules:", flush=True)
        for n, slug in failed_list:
            print(f"    #{n} {slug}", flush=True)
    print(f"{'='*70}", flush=True)
    return 1 if failed_list else 0


# ============================================================================
# CLI
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="E2E Module Builder v5 — clean pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Pipeline phases: research → discover → content → activities → validate → [review] → mdx

            Examples:
              %(prog)s a1 12                            # RC mode (no review)
              %(prog)s a1 12 --review                   # Full mode (with Gemini review)
              %(prog)s a1 --all                         # Build entire track (RC)
              %(prog)s a1 --range 1-20                  # Build range
              %(prog)s a1 12 --rebuild                  # Nuke state, restart
              %(prog)s a1 12 --dry-run                  # Show plan, no dispatches
              %(prog)s a1 12 --verify                   # Just audit
              %(prog)s a1 12 --force-phase validate     # Re-run validate only
              %(prog)s a1 12 --restart-from review      # Run: review → mdx
              %(prog)s a1 12 --stop-before review       # Stop before review phase
        """),
    )
    parser.add_argument("track", help="Track identifier (a1, a2, b1, ..., bio, hist, ...)")
    parser.add_argument("num", type=int, nargs="?", default=None,
                        help="1-indexed module number (optional with --all or --range)")

    # Batch mode
    parser.add_argument("--all", action="store_true", dest="build_all",
                        help="Build all modules in the track sequentially")
    parser.add_argument("--range", type=str, default=None, dest="build_range",
                        help="Build a range of modules (e.g. 1-20)")

    # Pipeline control
    parser.add_argument("--rebuild", action="store_true",
                        help="Nuke state and rebuild from research")
    parser.add_argument("--no-auto-rebuild", action="store_true",
                        help="Disable automatic rebuild when validate exhausts fix attempts")
    parser.add_argument("--force-phase", type=str, default=None,
                        help="Re-run a single phase (research/content/activities/validate/review/mdx)")
    parser.add_argument("--restart-from", type=str, default=None,
                        help="Restart from a phase (e.g. --restart-from review)")
    parser.add_argument("--force-research", action="store_true",
                        help="Force fresh research even if research file exists")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show plan without dispatching")
    parser.add_argument("--refresh", action="store_true",
                        help="Regenerate prose from updated research")
    parser.add_argument("--verify", action="store_true",
                        help="Just run audit, print PASS/FAIL, exit")
    parser.add_argument("--research-only", action="store_true", dest="research_only",
                        help="Run research phase only")
    parser.add_argument("--skip-discover", action="store_true", dest="skip_discover",
                        help="Skip video/blog discovery phase")

    # Review
    parser.add_argument("--review", action="store_true",
                        help="Include Gemini RAG-grounded review phase")
    parser.add_argument("--review-claude", action="store_true", dest="review_claude",
                        help="Include Claude review phase (uses Claude instead of Gemini)")

    # Model overrides
    parser.add_argument("--use-claude", type=str, default="", dest="use_claude",
                        help="Phases to run via Claude instead of Gemini (e.g. 'A', 'C', 'A C')")
    parser.add_argument("--gemini-model", type=str, default=None, dest="gemini_model",
                        help="Override Gemini model for all phases")
    parser.add_argument("--claude-model-A", type=str, default=None, dest="claude_model_A",
                        help="Claude model for research")
    parser.add_argument("--claude-model-C", type=str, default=None, dest="claude_model_C",
                        help="Claude model for activities")
    parser.add_argument("--claude-model-D", type=str, default=None, dest="claude_model_D",
                        help="Claude model for review (default: claude-opus-4-6)")

    # Tuning
    parser.add_argument("--stop-before", type=str, default=None, dest="stop_before",
                        help="Stop before this phase (e.g. --stop-before validate)")
    parser.add_argument("--full-build", action="store_true", dest="full_build",
                        help="Single-call mode: content + activities + vocabulary in one Gemini call (auto for beginner)")
    parser.add_argument("--no-full-build", action="store_true", dest="no_full_build",
                        help="Disable auto full-build for beginner tier")
    parser.add_argument("--rag", action="store_true", dest="rag",
                        help="RAG-enabled mode: Gemini searches textbooks/VESUM via MCP (auto when .gemini/settings.json exists)")
    parser.add_argument("--max-fix", type=int, default=None, dest="max_fix",
                        help="Override max fix iterations (default: 6 core, 8 seminar)")

    args = parser.parse_args()

    # Validate: need num, --all, or --range
    if args.num is None and not args.build_all and not args.build_range:
        parser.error("Either provide a module number, --all, or --range")

    # --all / --range: batch mode
    if args.build_all or args.build_range:
        idx = get_module_index(args.track)
        total = idx["total"]

        if args.build_all:
            nums = list(range(1, total + 1))
            print(f"Building ALL {total} modules in {args.track} (v5)", flush=True)
        else:
            m = re.match(r"^(\d+)-(\d+)$", args.build_range)
            if not m:
                parser.error(f"Invalid range: {args.build_range!r} (expected N-M)")
            start, end = int(m.group(1)), int(m.group(2))
            if start < 1 or end > total or start > end:
                parser.error(f"Range {start}-{end} out of bounds (track has {total} modules)")
            nums = list(range(start, end + 1))
            print(f"Building {args.track} modules {start}-{end} ({len(nums)} modules, v5)", flush=True)

        return _run_batch(args, nums)

    # --verify mode
    if args.verify:
        try:
            slug = slug_for_num(args.track, args.num)
            paths = get_module_paths(args.track, slug)
            content_path = paths["md"]
            if not content_path.exists():
                print(f"FAIL: Content file not found: {content_path}", flush=True)
                return 1
            passed, output = run_verify(content_path, content_only=False)
            if passed:
                print(f"PASS: {slug} (fully complete)", flush=True)
                return 0
            else:
                passed_sr, _ = run_verify(content_path, skip_review=True)
                if passed_sr:
                    print(f"CONTENT+ACTIVITIES: {slug} (needs review)", flush=True)
                    return 0
                passed_co, _ = run_verify(content_path, content_only=True)
                if passed_co:
                    print(f"CONTENT-ONLY: {slug} (activities not validated)", flush=True)
                    return 0
                print(f"FAIL: {slug}", flush=True)
                for line in output.strip().split("\n")[-20:]:
                    print(f"  {line}", flush=True)
                return 1
        except Exception as e:
            print(f"ERROR: {e}", flush=True)
            return 1

    return _run_single_module(args)


if __name__ == "__main__":
    sys.exit(main())
