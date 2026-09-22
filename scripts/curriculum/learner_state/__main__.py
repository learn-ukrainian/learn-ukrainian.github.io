"""CLI entry point for learner state, immersion band, observed index, and inventory gate (issue #8414).

Usage:
  .venv/bin/python -m scripts.curriculum.learner_state planned <level> <position> <lesson>
  .venv/bin/python -m scripts.curriculum.learner_state band <level> <position> <lesson>
  .venv/bin/python -m scripts.curriculum.learner_state observed <level> <slug> <lesson>
  .venv/bin/python -m scripts.curriculum.learner_state gate <level> <slug> <lesson>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import codes
from .base_layer import BaseLayerError
from .immersion import ImmersionError, compute_lesson_immersion_band
from .inventory_gate import check_lesson
from .observed import ObservedError, check_observed, write_observed
from .planned import PlannedStateError, planned_state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.curriculum.learner_state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Learner state, immersion band, observed index, and inventory gate CLI (issue #8414).\n"
            "Use during planning, prompt assembly, preflight, or post-build verification; do NOT use for v1 modules."
        ),
        epilog=(
            "Commands:\n"
            "  planned   Compute planned learner state at (level, position, lesson)\n"
            "  band      Compute lesson immersion band and structural targets\n"
            "  observed  Write the post-build observed learner state index for a lesson\n"
            "  gate      Validate built lesson token resolutions against learner inventory allowlist\n\n"
            "Outputs: stdout only (except observed which writes lesson-<n>.observed.yaml + .lock).\n"
            "Exit codes: 0 = success / pass, 1 = failure / gate violations.\n"
            "Examples:\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state planned a1 1 1\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state planned a1 1 2 --json\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state band a1 1 1\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state observed a1 mod-01 1\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state gate a1 mod-01 1\n\n"
            "Related: docs/epics/fresh-build-plan-schema.md §4, §6; issues #8414, #8397. Outcome codes:\n"
            + codes.help_text()
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: planned
    planned_parser = subparsers.add_parser(
        "planned",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Compute planned learner state at a lesson position of a level (Brief #8414, Part 1).\n"
            "Use before lesson drafting or validation; do NOT use for post-build verification."
        ),
        epilog=(
            "Outputs: stdout only; read-only, no side effects.\n"
            "Exit codes: 0 = success, 1 = failure.\n"
            "Examples:\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state planned a1 1 1\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state planned a1 1 2 --json\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state planned a1 3 1 --allow-missing-prior\n\n"
            "Related: docs/epics/fresh-build-plan-schema.md §4; issues #8414, #8397. Outcome codes:\n"
            + codes.help_text()
        ),
    )
    planned_parser.add_argument("level", help="level directory under lesson-plans/, e.g. a1, a2")
    planned_parser.add_argument("position", type=int, help="arc position integer (1-indexed)")
    planned_parser.add_argument("lesson", type=int, help="lesson number integer within plan (1-indexed)")
    planned_parser.add_argument(
        "--allow-missing-prior",
        action="store_true",
        help="waive missing earlier plans for out-of-order pilot authoring",
    )
    planned_parser.add_argument(
        "--strict",
        action="store_true",
        help="refuse all waivers; fail closed when any earlier plan is missing",
    )
    planned_parser.add_argument(
        "--plans-dir",
        type=Path,
        default=None,
        help="override directory of lesson plans (for tests)",
    )
    planned_parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=None,
        help="override directory of evidence files (for tests)",
    )
    planned_parser.add_argument(
        "--words",
        type=Path,
        default=None,
        help="override path to _words.yaml (for tests)",
    )
    planned_parser.add_argument(
        "--base-request",
        type=Path,
        default=None,
        help="override path to _base.request.yaml (for tests)",
    )
    planned_parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON output instead of text summary",
    )

    # Subcommand: band
    band_parser = subparsers.add_parser(
        "band",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Compute the lesson immersion band and structural targets (Brief #8414, Part 1).\n"
            "Use during lesson planning or prompt construction; do NOT use for v1 modules."
        ),
        epilog=(
            "Outputs: stdout only; read-only, no side effects.\n"
            "Exit codes: 0 = success, 1 = failure.\n"
            "Examples:\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state band a1 1 1\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state band a1 1 1 --cumulative-count 250\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state band a2 1 1 --json\n\n"
            "Related: docs/epics/fresh-build-plan-schema.md §4; scripts/config.py; issues #8414, #8397. Outcome codes:\n"
            + codes.help_text()
        ),
    )
    band_parser.add_argument("level", help="level directory under lesson-plans/, e.g. a1, a2, b1")
    band_parser.add_argument("position", type=int, help="arc position integer (1-indexed)")
    band_parser.add_argument("lesson", type=int, help="lesson number integer within plan (1-indexed)")
    band_parser.add_argument(
        "--cumulative-count",
        type=int,
        default=None,
        help="override cumulative core vocabulary count (for dry-run/testing; defaults to computing planned state)",
    )
    band_parser.add_argument(
        "--allow-missing-prior",
        action="store_true",
        help="waive missing earlier plans for out-of-order pilot authoring",
    )
    band_parser.add_argument(
        "--strict",
        action="store_true",
        help="refuse all waivers; fail closed when any earlier plan is missing",
    )
    band_parser.add_argument(
        "--plans-dir",
        type=Path,
        default=None,
        help="override directory of lesson plans (for tests)",
    )
    band_parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=None,
        help="override directory of evidence files (for tests)",
    )
    band_parser.add_argument(
        "--words",
        type=Path,
        default=None,
        help="override path to _words.yaml (for tests)",
    )
    band_parser.add_argument(
        "--base-request",
        type=Path,
        default=None,
        help="override path to _base.request.yaml (for tests)",
    )
    band_parser.add_argument(
        "--arc-path",
        type=Path,
        default=None,
        help="override path to _arc.yaml (for tests)",
    )
    band_parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON output instead of text summary",
    )

    # Subcommand: observed
    observed_parser = subparsers.add_parser(
        "observed",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Write the post-build observed learner state index for a lesson (Brief #8414, Part 2).\n"
            "Use after lesson build and resolution receipts are emitted; do NOT use for unbuilt lessons."
        ),
        epilog=(
            "Outputs: writes curriculum/l2-uk-en/evidence/<level>/_state/<slug>/lesson-<n>.observed.yaml (+ .lock)\n"
            "Exit codes: 0 = success, 1 = failure.\n"
            "Examples:\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state observed a1 mod-01 1\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state observed a1 mod-01 1 --json\n\n"
            "Related: docs/epics/fresh-build-plan-schema.md §4; schemas/learner-observed-v1.schema.json; issues #8414, #8397. Outcome codes:\n"
            + codes.help_text()
        ),
    )
    observed_parser.add_argument("level", help="level directory under lesson-plans/, e.g. a1, a2")
    observed_parser.add_argument("slug", help="module plan slug, e.g. mod-01")
    observed_parser.add_argument("lesson", type=int, help="lesson number within plan (1-indexed)")
    observed_parser.add_argument(
        "--plans-dir",
        type=Path,
        default=None,
        help="override directory of lesson plans (for tests)",
    )
    observed_parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=None,
        help="override directory of evidence files (for tests)",
    )
    observed_parser.add_argument(
        "--words",
        type=Path,
        default=None,
        help="override path to _words.yaml (for tests)",
    )
    observed_parser.add_argument(
        "--base-request",
        type=Path,
        default=None,
        help="override path to _base.request.yaml (for tests)",
    )
    observed_parser.add_argument(
        "--resolutions",
        type=Path,
        default=None,
        help="override path to lesson-<n>.resolutions.yaml (for tests)",
    )
    observed_parser.add_argument(
        "--expanded",
        type=Path,
        default=None,
        help="override path to lesson-<n>.expanded.yaml (for tests)",
    )
    observed_parser.add_argument(
        "--grammar-path",
        type=Path,
        default=None,
        help="override path to _grammar.yaml (for tests)",
    )
    observed_parser.add_argument(
        "--allow-missing-prior",
        action="store_true",
        help="waive missing earlier plans for out-of-order pilot authoring",
    )
    observed_parser.add_argument(
        "--strict",
        action="store_true",
        help="refuse all waivers; fail closed when any earlier plan is missing",
    )
    observed_parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON output instead of text summary",
    )

    # Subcommand: gate
    gate_parser = subparsers.add_parser(
        "gate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Validate built lesson token resolutions against learner inventory allowlist (Brief #8414, Part 2).\n"
            "Use during post-build verification pass; do NOT use for unbuilt drafts."
        ),
        epilog=(
            "Outputs: stdout / stderr verification report only; read-only, no side effects.\n"
            "Exit codes: 0 = pass, 1 = fail (lemma outside state, core not introduced, etc.).\n"
            "Examples:\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state gate a1 mod-01 1\n"
            "  .venv/bin/python -m scripts.curriculum.learner_state gate a1 mod-01 1 --json\n\n"
            "Related: docs/epics/fresh-build-plan-schema.md §6; issues #8414, #8397. Outcome codes:\n"
            + codes.help_text()
        ),
    )
    gate_parser.add_argument("level", help="level directory under lesson-plans/, e.g. a1, a2")
    gate_parser.add_argument("slug", help="module plan slug, e.g. mod-01")
    gate_parser.add_argument("lesson", type=int, help="lesson number within plan (1-indexed)")
    gate_parser.add_argument(
        "--plans-dir",
        type=Path,
        default=None,
        help="override directory of lesson plans (for tests)",
    )
    gate_parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=None,
        help="override directory of evidence files (for tests)",
    )
    gate_parser.add_argument(
        "--words",
        type=Path,
        default=None,
        help="override path to _words.yaml (for tests)",
    )
    gate_parser.add_argument(
        "--base-request",
        type=Path,
        default=None,
        help="override path to _base.request.yaml (for tests)",
    )
    gate_parser.add_argument(
        "--resolutions",
        type=Path,
        default=None,
        help="override path to lesson-<n>.resolutions.yaml (for tests)",
    )
    gate_parser.add_argument(
        "--expanded",
        type=Path,
        default=None,
        help="override path to lesson-<n>.expanded.yaml (for tests)",
    )
    gate_parser.add_argument(
        "--allow-missing-prior",
        action="store_true",
        help="waive missing earlier plans for out-of-order pilot authoring",
    )
    gate_parser.add_argument(
        "--strict",
        action="store_true",
        help="refuse all waivers; fail closed when any earlier plan is missing",
    )
    gate_parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON output instead of text summary",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "planned":
            state = planned_state(
                args.level,
                args.position,
                args.lesson,
                allow_missing_prior=args.allow_missing_prior,
                strict=args.strict,
                plans_dir=args.plans_dir,
                evidence_dir=args.evidence_dir,
                words_path=args.words,
                base_request_path=args.base_request,
            )
            if args.json:
                print(json.dumps(state.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(state.render_text())
            return 0

        elif args.command == "band":
            track_key = args.level.lower().split("-")[0] if "-" in args.level else args.level.lower()
            count = args.cumulative_count
            waiver: str | None = None
            if track_key == "a1" and count is None:
                # Compute planned state only for A1 to get accurate cumulative core count
                state = planned_state(
                    args.level,
                    args.position,
                    args.lesson,
                    allow_missing_prior=args.allow_missing_prior,
                    strict=args.strict,
                    plans_dir=args.plans_dir,
                    evidence_dir=args.evidence_dir,
                    words_path=args.words,
                    base_request_path=args.base_request,
                )
                count = state.cumulative_core_count
                waiver = state.waiver

            band = compute_lesson_immersion_band(
                args.level,
                args.position,
                args.lesson,
                count,
                waiver=waiver,
                arc_path=args.arc_path,
            )
            if args.json:
                print(json.dumps(band.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(band.render_text())
            return 0

        elif args.command == "observed":
            out_path, digest = write_observed(
                args.level,
                args.slug,
                args.lesson,
                plans_dir=args.plans_dir,
                evidence_dir=args.evidence_dir,
                words_path=args.words,
                base_request_path=args.base_request,
                resolutions_path=args.resolutions,
                expanded_path=args.expanded,
                grammar_path=args.grammar_path,
                allow_missing_prior=args.allow_missing_prior,
                strict=args.strict,
            )
            doc = check_observed(out_path)
            if args.json:
                print(json.dumps(doc, ensure_ascii=False, indent=2))
            else:
                untaught = doc.get("untaught_forms") or {}
                print(
                    f"Observed index written: {out_path} (digest: {digest[:12]}...)\n"
                    f"  Records observed: {len(doc.get('records', []))}\n"
                    f"  Untaught forms: {untaught.get('count', 0)} (share: {untaught.get('share', 0.0)})"
                )
            return 0

        elif args.command == "gate":
            report = check_lesson(
                args.level,
                args.slug,
                args.lesson,
                plans_dir=args.plans_dir,
                evidence_dir=args.evidence_dir,
                words_path=args.words,
                base_request_path=args.base_request,
                resolutions_path=args.resolutions,
                expanded_path=args.expanded,
                allow_missing_prior=args.allow_missing_prior,
                strict=args.strict,
            )
            if args.json:
                print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
            else:
                if report.ok:
                    print(report.render_text())
                else:
                    print(report.render_text(), file=sys.stderr)
            return 0 if report.ok else 1

    except (PlannedStateError, BaseLayerError, ImmersionError, ObservedError) as err:
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "code": err.code, "error": str(err)}, ensure_ascii=False, indent=2))
        else:
            print(f"Error [{err.code}]: {err.message}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
