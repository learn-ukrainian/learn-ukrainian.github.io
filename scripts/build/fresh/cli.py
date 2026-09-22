"""CLI entry for fresh build engine Part E2 (issue #8397 child 6, #8431 r3).

Subcommands:
- render-prompt: render lesson prompt and run rendered-prompt check
- preflight: verify availability of evidence records, cited forms stress, and compute homographs
- write: dispatch explicit writer seat, harvest result, validate draft schema, save state
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.build.fresh.draft_schema import LEVELS
from scripts.build.fresh.immersion import compute_immersion_payload
from scripts.build.fresh.preflight import preflight_lesson
from scripts.build.fresh.prompt import (
    check_rendered_prompt,
    render_lesson_prompt,
    render_recap_prompt,
    style_card_info,
)
from scripts.build.fresh.writer import ALLOWED_WRITERS, dispatch_writer
from scripts.curriculum.evidence import lesson_lock, lock
from scripts.curriculum.learner_state.planned import planned_state
from scripts.curriculum.resolver.inputs import Allowlist

REPO_ROOT = Path(__file__).resolve().parents[3]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.build.fresh.cli",
        description=(
            "Fresh build engine E2 — prompt rendering, preflight verification, and writer dispatch.\n"
            "Use to render lesson prompts, run preflights, or invoke writer seats during fresh lesson builds."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.build.fresh.cli render-prompt a1 sounds-letters-and-hello --lesson 1\n"
            "  .venv/bin/python -m scripts.build.fresh.cli preflight a1 sounds-letters-and-hello --lesson 1\n"
            "  .venv/bin/python -m scripts.build.fresh.cli write a1 sounds-letters-and-hello --lesson 1 --writer agy\n\n"
            "Outputs:\n"
            "  Prompt files, gap reports, and lesson draft state files under curriculum/l2-uk-en/evidence/<level>/_state/<slug>/\n\n"
            "Exit codes:\n"
            "  0: Successful operation\n"
            "  1: Check failure, gap detected, or execution error\n\n"
            "Related:\n"
            "  docs/epics/fresh-build-writer-contract.md (#8431 r3), sub-epic #8397 child 6"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. render-prompt subcommand
    p_render = subparsers.add_parser(
        "render-prompt",
        description=(
            "Render the lesson writer prompt and validate it against the rendered-prompt check (#8431 §8.1).\n"
            "Use before dispatching a writer to verify prompt integrity and compute its deterministic SHA-256."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.build.fresh.cli render-prompt a1 sounds-letters-and-hello --lesson 1\n"
            "  .venv/bin/python -m scripts.build.fresh.cli render-prompt a1 sounds-letters-and-hello --lesson 1 -o /tmp/prompt.md\n"
            "  .venv/bin/python -m scripts.build.fresh.cli render-prompt a1 sounds-letters-and-hello --lesson 5 --recap\n\n"
            "Outputs:\n"
            "  Rendered prompt written to specified --output path or printed to stdout.\n\n"
            "Exit codes:\n"
            "  0: Prompt rendered successfully and passed rendered-prompt check\n"
            "  1: Prompt rendered but failed rendered-prompt check, or input loading failed\n\n"
            "Related:\n"
            "  scripts/build/fresh/prompts/lesson-writer.md.j2, writer contract #8431 §8.1"
        ),
    )
    p_render.add_argument("level", choices=LEVELS, help="Curriculum level, e.g. 'a1', 'a2', 'b1', 'b2'")
    p_render.add_argument("slug", help="Module slug, e.g. 'sounds-letters-and-hello'")
    p_render.add_argument("--lesson", "-n", type=int, required=True, help="Lesson number (1-indexed), e.g. 1")
    p_render.add_argument("--output", "-o", type=Path, default=None, help="Output file path for rendered prompt (default: stdout)")
    p_render.add_argument("--recap", action="store_true", help="Render recap prompt variant with built lessons 1..N-1 (default: False)")

    # 2. preflight subcommand
    p_preflight = subparsers.add_parser(
        "preflight",
        description=(
            "Run preflight verification for a lesson's evidence needs and compute homograph candidates (#8431 §4, §7 row 0).\n"
            "Use before dispatching a writer to stop early on missing records, unverified rights, or pending stress."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.build.fresh.cli preflight a1 sounds-letters-and-hello --lesson 1\n"
            "  .venv/bin/python -m scripts.build.fresh.cli preflight a1 sounds-letters-and-hello --lesson 1 --gap-report gaps.yaml\n\n"
            "Outputs:\n"
            "  Prints preflight summary to stdout; writes gap report YAML if gaps are found and --gap-report is set.\n\n"
            "Exit codes:\n"
            "  0: Preflight passed with 0 gaps\n"
            "  1: Gaps detected, missing records, or cited form pending stress\n\n"
            "Related:\n"
            "  scripts/build/fresh/preflight.py, writer contract #8431 §4"
        ),
    )
    p_preflight.add_argument("level", choices=LEVELS, help="Curriculum level, e.g. 'a1', 'a2', 'b1', 'b2'")
    p_preflight.add_argument("slug", help="Module slug, e.g. 'sounds-letters-and-hello'")
    p_preflight.add_argument("--lesson", "-n", type=int, required=True, help="Lesson number (1-indexed), e.g. 1")
    p_preflight.add_argument("--gap-report", type=Path, default=None, help="File path to write evidence gap report if preflight fails")

    # 3. write subcommand
    p_write = subparsers.add_parser(
        "write",
        description=(
            "Dispatch an explicit language-lane writer seat to write a lesson draft (#8431 r3 §1, §7).\n"
            "Use to dispatch claude, codex, agy, or grok, await completion, validate draft schema, and store state."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.build.fresh.cli write a1 sounds-letters-and-hello --lesson 1 --writer agy\n"
            "  .venv/bin/python -m scripts.build.fresh.cli write a1 sounds-letters-and-hello --lesson 1 --writer claude --attempt 2\n"
            "  .venv/bin/python -m scripts.build.fresh.cli write a1 sounds-letters-and-hello --lesson 1 --writer codex --fake-seat ./fake.py\n\n"
            "Outputs:\n"
            "  lesson-<n>.draft.yaml, lesson-<n>.raw.txt, and lesson-<n>.writer.yaml in state directory.\n\n"
            "Exit codes:\n"
            "  0: Writer finished, reply validated against draft schema, state files saved\n"
            "  1: Preflight failure, dispatch error, or draft schema validation failure (check 1)\n\n"
            "Related:\n"
            "  scripts/delegate.py, writer contract #8431 r3 §1, §7"
        ),
    )
    p_write.add_argument("level", choices=LEVELS, help="Curriculum level, e.g. 'a1', 'a2', 'b1', 'b2'")
    p_write.add_argument("slug", help="Module slug, e.g. 'sounds-letters-and-hello'")
    p_write.add_argument("--lesson", "-n", type=int, required=True, help="Lesson number (1-indexed), e.g. 1")
    p_write.add_argument("--writer", choices=ALLOWED_WRITERS, required=True, help="Explicit writer seat (claude, codex, agy, grok; code never auto-routes)")
    p_write.add_argument("--attempt", type=int, default=1, help="Attempt count for regeneration tracking (default: 1, e.g. 1 or 2)")
    p_write.add_argument("--fake-seat", type=Path, default=None, help="Optional script path for fake seat execution during testing (never makes paid call)")
    p_write.add_argument("--output-dir", type=Path, default=None, help="Directory to save draft and state files (default: evidence/<level>/_state/<slug>/)")

    return parser


def _load_lesson_data(level: str, slug: str, lesson_n: int) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Path]]:
    """Helper to resolve paths and load plan, pack, and word store."""
    paths = lesson_lock.resolve_paths(level, slug)
    if not paths["plan"].is_file():
        raise FileNotFoundError(f"Plan file not found: {paths['plan']}")
    plan_dict = yaml.safe_load(paths["plan"].read_text(encoding="utf-8"))

    pack_dict = {}
    if paths["pack"].is_file():
        pack_dict = yaml.safe_load(paths["pack"].read_text(encoding="utf-8"))

    words_dict = {}
    if paths["words"].is_file():
        words_dict = yaml.safe_load(paths["words"].read_text(encoding="utf-8"))

    lesson_entry = next((l for l in plan_dict.get("lessons", []) if l.get("n") == lesson_n), None)
    if lesson_entry is None:
        raise ValueError(f"Lesson {lesson_n} not found in plan {paths['plan']}")

    return plan_dict, lesson_entry, pack_dict, paths


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "render-prompt":
        plan_dict, lesson_entry, pack_dict, paths = _load_lesson_data(args.level, args.slug, args.lesson)
        card_path, _, card_sha = style_card_info(args.level)

        # Compute planned state and immersion payload
        pos = plan_dict.get("arc_ref", {}).get("position", 1)
        p_state = planned_state(args.level, pos, args.lesson, allow_missing_prior=True)
        imm_payload = compute_immersion_payload(args.level, pos, args.lesson, cumulative_core_count=p_state.cumulative_core_count)

        if args.recap:
            # Load built lessons 1..N-1 if available
            built = []
            for prior_n in range(1, args.lesson):
                built.append({"n": prior_n, "title": f"Lesson {prior_n}", "content": f"# Built lesson {prior_n}"})
            rendered = render_recap_prompt(
                lesson_entry,
                built_lessons=built,
                cited_records={},
                learner_state=p_state,
                immersion=imm_payload,
                level=args.level,
                slug=args.slug,
                lesson_n=args.lesson,
                style_card_path=card_path,
            )
        else:
            rendered = render_lesson_prompt(
                lesson_entry,
                cited_records={},
                learner_state=p_state,
                immersion=imm_payload,
                level=args.level,
                slug=args.slug,
                lesson_n=args.lesson,
                style_card_path=card_path,
            )

        check_res = check_rendered_prompt(rendered, lesson_entry, card_path, is_recap=args.recap)
        if not check_res.passed:
            print("Rendered-prompt check FAILED:", file=sys.stderr)
            for err in check_res.errors:
                print(f"  - {err}", file=sys.stderr)
            return 1

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Rendered prompt written to {args.output} (sha256: {check_res.prompt_sha256})")
        else:
            print(rendered)

        return 0

    elif args.command == "preflight":
        plan_dict, lesson_entry, pack_dict, paths = _load_lesson_data(args.level, args.slug, args.lesson)
        words_dict = yaml.safe_load(paths["words"].read_text(encoding="utf-8")) if paths["words"].is_file() else {}

        res = preflight_lesson(
            lesson_entry,
            pack=pack_dict,
            word_store=words_dict,
            gap_report_path=args.gap_report,
        )

        print(f"Preflight status: {res.status}")
        print(f"Homographs detected: {res.homograph_count}")
        if res.gaps:
            print(f"Gaps found ({len(res.gaps)}):")
            for g in res.gaps:
                print(f"  [{g.step}] need: {g.need} — {g.detail}")
            return 1

        return 0

    elif args.command == "write":
        plan_dict, lesson_entry, pack_dict, paths = _load_lesson_data(args.level, args.slug, args.lesson)
        card_path, _, card_sha = style_card_info(args.level)
        pos = plan_dict.get("arc_ref", {}).get("position", 1)
        p_state = planned_state(args.level, pos, args.lesson, allow_missing_prior=True)
        imm_payload = compute_immersion_payload(args.level, pos, args.lesson, cumulative_core_count=p_state.cumulative_core_count)

        # 1. Run preflight first
        words_dict = yaml.safe_load(paths["words"].read_text(encoding="utf-8")) if paths["words"].is_file() else {}
        pre_res = preflight_lesson(lesson_entry, pack=pack_dict, word_store=words_dict)
        if not pre_res.passed:
            print("Preflight FAILED with evidence gaps. NO writer call made.", file=sys.stderr)
            for g in pre_res.gaps:
                print(f"  [{g.step}] need: {g.need} — {g.detail}", file=sys.stderr)
            return 1

        # 2. Render prompt
        rendered_prompt = render_lesson_prompt(
            lesson_entry,
            cited_records={},
            learner_state=p_state,
            immersion=imm_payload,
            level=args.level,
            slug=args.slug,
            lesson_n=args.lesson,
            style_card_path=card_path,
        )
        check_res = check_rendered_prompt(rendered_prompt, lesson_entry, card_path)
        if not check_res.passed:
            print("Rendered prompt check FAILED:", file=sys.stderr)
            for err in check_res.errors:
                print(f"  - {err}", file=sys.stderr)
            return 1

        # 3. Write prompt to state dir
        out_dir = args.output_dir or (paths["state_dir"] / args.slug)
        out_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = out_dir / f"lesson-{args.lesson}.prompt.md"
        prompt_file.write_text(rendered_prompt, encoding="utf-8")

        # 4. Dispatch writer
        plan_activity_types = {
            act["id"]: act["type"] for act in lesson_entry.get("activities", []) if "id" in act and "type" in act
        }
        res = dispatch_writer(
            writer=args.writer,
            level=args.level,
            slug=args.slug,
            lesson_n=args.lesson,
            prompt_file=prompt_file,
            prompt_sha256=check_res.prompt_sha256,
            output_dir=out_dir,
            attempt=args.attempt,
            plan_activity_types=plan_activity_types,
            fake_seat=args.fake_seat,
        )

        print(f"Writer call succeeded for {args.level}/{args.slug} lesson {args.lesson} (seat: {args.writer}).")
        print(f"Draft saved to {res['draft_file']}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
