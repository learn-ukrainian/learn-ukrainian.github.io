"""CLI entry for fresh build engine prompt, writer, lesson and module commands.

Subcommands:
- render-prompt: render lesson prompt and run rendered-prompt check
- preflight: verify availability of evidence records, cited forms stress, and compute homographs
- write: dispatch explicit writer seat, harvest result, validate draft schema, save state
- build: run checks 1-12 for one lesson or an ordered module
- closure: recompute historical manifest staleness
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.build.fresh.draft_schema import LEVELS
from scripts.build.fresh.immersion import compute_immersion_payload
from scripts.build.fresh.preflight import preflight_lesson
from scripts.build.fresh.prompt import (
    check_rendered_prompt,
    extract_plan_citations,
    render_lesson_prompt,
    render_recap_prompt,
    style_card_info,
)
from scripts.build.fresh.writer import ALLOWED_WRITERS, dispatch_writer
from scripts.curriculum.evidence import lesson_lock, lock
from scripts.curriculum.evidence import pack as pack_module
from scripts.curriculum.learner_state.planned import PlannedState, planned_state
from scripts.curriculum.validate.loader import load_plan

REPO_ROOT = Path(__file__).resolve().parents[3]


def _resolve_repo_root(args: argparse.Namespace | None = None) -> Path:
    """Resolve repository root directory from CLI argument, env var, or default.

    Checks:
    1. --repo-root argument (if passed on CLI)
    2. LEARN_UKRAINIAN_REPO_ROOT or REPO_ROOT environment variable
    3. REPO_ROOT (detected from module path)
    """
    if args is not None and getattr(args, "repo_root", None) is not None:
        return Path(args.repo_root).resolve()
    env_root = os.environ.get("LEARN_UKRAINIAN_REPO_ROOT") or os.environ.get("REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return REPO_ROOT


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.build.fresh.cli",
        description=(
            "Fresh build engine — prompts, preflight, writer dispatch, and ordered builds.\n"
            "Use to render prompts, run preflights, write drafts, build lessons or modules, and recompute closure."
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
            "Environment variables:\n"
            "  LEARN_UKRAINIAN_REPO_ROOT, REPO_ROOT: Override repository root directory for path resolution.\n\n"
            "Related:\n"
            "  docs/epics/fresh-build-writer-contract.md (#8431 r3), sub-epic #8397 child 6"
        ),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root directory (default: auto-detected, or $LEARN_UKRAINIAN_REPO_ROOT / $REPO_ROOT)",
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
    p_render.add_argument(
        "--output", "-o", type=Path, default=None, help="Output file path for rendered prompt (default: stdout)"
    )
    p_render.add_argument(
        "--recap",
        dest="recap",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Assert recap prompt variant (fails if it disagrees with plan)",
    )
    p_render.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root directory (default: auto-detected, or $LEARN_UKRAINIAN_REPO_ROOT / $REPO_ROOT)",
    )

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
    p_preflight.add_argument(
        "--gap-report", type=Path, default=None, help="File path to write evidence gap report if preflight fails"
    )
    p_preflight.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root directory (default: auto-detected, or $LEARN_UKRAINIAN_REPO_ROOT / $REPO_ROOT)",
    )

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
    p_write.add_argument(
        "--writer",
        choices=ALLOWED_WRITERS,
        required=True,
        help="Explicit writer seat (claude, codex, agy, grok; code never auto-routes)",
    )
    p_write.add_argument(
        "--attempt", type=int, default=1, help="Attempt count for regeneration tracking (default: 1, e.g. 1 or 2)"
    )
    p_write.add_argument(
        "--fake-seat",
        type=Path,
        default=None,
        help="Optional script path for fake seat execution during testing (never makes paid call)",
    )
    p_write.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to save draft and state files (default: evidence/<level>/_state/<slug>/)",
    )
    p_write.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root directory (default: auto-detected, or $LEARN_UKRAINIAN_REPO_ROOT / $REPO_ROOT)",
    )
    p_write.add_argument(
        "--recap",
        dest="recap",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Assert recap prompt variant (fails if it disagrees with plan)",
    )

    # 4. assemble subcommand
    p_assemble = subparsers.add_parser(
        "assemble",
        description=(
            "Assemble a lesson draft into an expanded document, apply stress, build Slovnyk and Resursy tabs, and render MDX (#8431 §1, §7).\n"
            "Use to run deterministic assembly (check 5), stress and frontmatter (check 9), and verify shippability (check 11)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.build.fresh.cli assemble a1 sounds-letters-and-hello --lesson 1\n\n"
            "Outputs:\n"
            "  lesson-<n>.expanded.yaml, lesson-<n>.provenance.yaml, lesson-<n>.stressed.yaml, and lesson-<n>.mdx\n\n"
            "Exit codes:\n"
            "  0: Successful assembly\n"
            "  1: Assembly, stress, or render check failure\n\n"
            "Related:\n"
            "  scripts/build/fresh/assemble.py, writer contract #8431 §1, §7"
        ),
    )
    p_assemble.add_argument("level", choices=LEVELS, help="Curriculum level, e.g. 'a1', 'a2', 'b1', 'b2'")
    p_assemble.add_argument("slug", help="Module slug, e.g. 'sounds-letters-and-hello'")
    p_assemble.add_argument("--lesson", "-n", type=int, required=True, help="Lesson number (1-indexed), e.g. 1")
    p_assemble.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to save state files (default: evidence/<level>/_state/<slug>/)",
    )
    p_assemble.add_argument(
        "--site-dir",
        type=Path,
        default=None,
        help="Target site directory for MDX output (default: site/src/content/docs/<level>/<slug>/)",
    )
    p_assemble.add_argument(
        "--astro-build",
        action="store_true",
        default=False,
        help="Run astro build gate in check 11 if Astro is installed",
    )
    p_assemble.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root directory (default: auto-detected, or $LEARN_UKRAINIAN_REPO_ROOT / $REPO_ROOT)",
    )

    p_build = subparsers.add_parser(
        "build",
        help="Build one lesson or an ordered fresh module through check 12",
        description=(
            "Build one lesson or every module lesson through review attempt manifests.\n"
            "Use with locked evidence; supply a writer seat when a draft needs writing."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.build.fresh build a1 sounds-letters-and-hello --lesson 1\n"
            "  .venv/bin/python -m scripts.build.fresh build a1 sounds-letters-and-hello --lesson 1 --question-seat codex:gpt-6-sol\n\n"
            "Outputs:\n"
            "  Prints a JSON gate report; writes lesson-<n>.gates.yaml and other lesson state files under evidence/<level>/_state/<slug>/.\n\n"
            "Exit codes:\n"
            "  0: All checks passed\n"
            "  1: A check failed or an input could not be loaded\n\n"
            "Related:\n"
            "  scripts/build/fresh/runner.py, fresh lesson build issue #8397"
        ),
    )
    p_build.add_argument("level", choices=LEVELS, help="Curriculum level, e.g. 'a1', 'a2', 'b1', 'b2'")
    p_build.add_argument("slug", help="Module slug, e.g. 'sounds-letters-and-hello'")
    target = p_build.add_mutually_exclusive_group(required=True)
    target.add_argument("--lesson", "-n", type=int, help="Lesson number (1-indexed), e.g. 1")
    target.add_argument("--module", action="store_true", help="Build every lesson in order, recap last")
    p_build.add_argument("--writer-seat", help="Explicit agent:model seat when a draft needs writing")
    p_build.add_argument(
        "--question-seat",
        default=None,
        help=(
            "Explicit agent:model seat for open questions (e.g. codex:gpt-6-sol; no default). "
            "If absent when the lesson has open questions, stops with question_seat_required"
        ),
    )
    p_build.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root directory (default: auto-detected, or $LEARN_UKRAINIAN_REPO_ROOT / $REPO_ROOT)",
    )

    p_closure = subparsers.add_parser(
        "closure", help="Recompute stale lesson manifest dependencies",
        description="Recompute module dependency closure from all immutable lesson manifests.",
    )
    p_closure.add_argument("level", choices=LEVELS, help="Curriculum level")
    p_closure.add_argument("slug", help="Module slug")
    p_closure.add_argument("--repo-root", type=Path, default=None, help="Repository root directory")

    return parser


def _load_lesson_data(
    level: str,
    slug: str,
    lesson_n: int,
    *,
    repo_root: Path | None = None,
    plans_dir: Path | None = None,
    evidence_dir: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Path]]:
    """Helper to resolve paths and load plan, pack, and word store with lock integrity (#8431, Findings 1, 3, 12).

    Fails closed if plan, pack, or word store is missing or lock disagrees.
    """
    root = repo_root if repo_root is not None else _resolve_repo_root()
    paths = lesson_lock.resolve_paths(
        level,
        slug,
        plans_dir=plans_dir,
        evidence_dir=evidence_dir,
        repo_root=root,
    )

    # 1. Load plan via scripts.curriculum.validate.loader (Finding 1)
    if not paths["plan"].is_file():
        raise FileNotFoundError(f"Plan file not found: {paths['plan']}")
    plan_dict = load_plan(paths["plan"])

    lesson_entry = next((l for l in plan_dict.get("lessons", []) if l.get("n") == lesson_n), None)
    if lesson_entry is None:
        raise ValueError(f"Lesson {lesson_n} not found in plan {paths['plan']}")

    # 2. Load pack with lock verification (Finding 3)
    if not paths["pack"].is_file():
        raise FileNotFoundError(f"Pack file not found: {paths['pack']}")
    lock.require(paths["pack"])
    pack_dict = yaml.safe_load(paths["pack"].read_text(encoding="utf-8"))

    # 3. Load word store with lock verification (Finding 3)
    if not paths["words"].is_file():
        raise FileNotFoundError(f"Word store not found: {paths['words']}")
    lock.require(paths["words"])
    words_dict = yaml.safe_load(paths["words"].read_text(encoding="utf-8"))

    # 4. Check per-lesson lock if present (Finding 3)
    if paths["lock"].is_file():
        ok, diff = lesson_lock.check_lesson_lock(
            level,
            slug,
            plans_dir=plans_dir,
            evidence_dir=evidence_dir,
            repo_root=root,
        )
        if not ok:
            raise ValueError(f"Per-lesson lock mismatch for {level}/{slug}: {diff}")

    return plan_dict, lesson_entry, pack_dict, words_dict, paths


def _load_cited_records(
    lesson_entry: dict[str, Any],
    pack_dict: dict[str, Any],
    words_dict: dict[str, Any],
) -> dict[str, Any]:
    """Resolve cited record IDs from the locked pack and word store (#8431 §1, Finding 1)."""
    cited_ids = extract_plan_citations(lesson_entry)

    # Index pack records
    pack_records: dict[str, dict[str, Any]] = {}
    for list_name in pack_module.PACK_RECORD_LISTS:
        for rec in pack_dict.get(list_name) or []:
            if isinstance(rec, dict) and "id" in rec:
                pack_records[rec["id"]] = rec

    # Index word records
    word_records: dict[str, dict[str, Any]] = {}
    for rec in words_dict.get("words") or []:
        if isinstance(rec, dict) and "id" in rec:
            word_records[rec["id"]] = rec

    cited_records: dict[str, Any] = {}
    for cid in sorted(cited_ids):
        if cid in word_records:
            cited_records[cid] = word_records[cid]
        elif cid in pack_records:
            cited_records[cid] = pack_records[cid]

    return cited_records


def _compute_input_hashes(
    paths: dict[str, Path],
    lesson_n: int,
    p_state: PlannedState,
) -> dict[str, str]:
    """Compute the five real, non-zero input hashes from files and locks (#8431 §1, Finding 1)."""
    plan_sha256 = hashlib.sha256(paths["plan"].read_bytes()).hexdigest()
    pack_lock = hashlib.sha256(paths["pack"].read_bytes()).hexdigest()
    words_lock = hashlib.sha256(paths["words"].read_bytes()).hexdigest()

    lesson_lock_entry_sha256: str | None = None
    if paths["lock"].is_file():
        lock_doc = yaml.safe_load(paths["lock"].read_text(encoding="utf-8"))
        if isinstance(lock_doc, dict):
            for entry in lock_doc.get("lessons", []):
                if entry.get("n") == lesson_n:
                    entry_sha = entry.get("entry_sha256")
                    if entry_sha and entry_sha != "0" * 64:
                        lesson_lock_entry_sha256 = entry_sha
                    break

    if not lesson_lock_entry_sha256:
        raise ValueError(
            f"Lesson lock entry sha256 missing for lesson {lesson_n} in {paths.get('lock')}; "
            "missing lesson lock is a preflight gap."
        )

    learner_state_sha256 = hashlib.sha256(lock.yaml_bytes(p_state.to_dict())).hexdigest()

    return {
        "plan_sha256": plan_sha256,
        "pack_lock": pack_lock,
        "words_lock": words_lock,
        "lesson_lock_entry_sha256": lesson_lock_entry_sha256,
        "learner_state_sha256": learner_state_sha256,
    }


def _load_recap_built_lessons(
    state_dir: Path,
    level: str,
    slug: str,
    lesson_n: int,
    repo_root: Path,
) -> list[dict[str, Any]]:
    """Load built lessons 1..N-1 from real files; fail closed and name missing built lesson (#8431, Finding 1)."""
    built: list[dict[str, Any]] = []
    module_state_dir = state_dir / slug

    for prior_n in range(1, lesson_n):
        found = repo_root / "site/src/content/docs" / level / slug / f"{prior_n}.mdx"
        gates = module_state_dir / f"lesson-{prior_n}.gates.yaml"
        manifest = module_state_dir / f"lesson-{prior_n}.manifest.yaml"
        sidecar = module_state_dir / f"lesson-{prior_n}.manifest.sha256"
        try:
            gate_doc = yaml.safe_load(gates.read_text(encoding="utf-8")) if gates.is_file() else None
            manifest_doc = yaml.safe_load(manifest.read_text(encoding="utf-8")) if manifest.is_file() else None
        except (OSError, UnicodeError, yaml.YAMLError) as err:
            raise ValueError(f"recap_inputs_not_built: lesson {prior_n}: {err}") from err
        if (not found.is_file() or not gates.is_file() or not manifest.is_file() or not sidecar.is_file()
                or not isinstance(gate_doc, dict) or gate_doc.get("passed") is not True
                or hashlib.sha256(manifest.read_bytes()).hexdigest() != sidecar.read_text(encoding="ascii").strip()
                or not isinstance(manifest_doc, dict)
                or not isinstance(manifest_doc.get("inputs"), dict)
                or not isinstance(manifest_doc["inputs"].get("lesson"), dict)
                or manifest_doc["inputs"]["lesson"].get("sha256") != hashlib.sha256(found.read_bytes()).hexdigest()):
            raise ValueError(f"recap_inputs_not_built: lesson {prior_n}: {found}")
        text = found.read_text(encoding="utf-8")
        built.append({"n": prior_n, "title": f"Lesson {prior_n}", "content": text,
                      "sha256": hashlib.sha256(found.read_bytes()).hexdigest()})

    return built


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    repo_root = _resolve_repo_root(args)
    cards_dir = (repo_root / "docs" / "style-cards") if (repo_root / "docs" / "style-cards").is_dir() else None

    if args.command == "build":
        from scripts.build.fresh.module import build_module
        try:
            report = build_module(args.level, args.slug, repo_root=repo_root, lesson_n=args.lesson,
                                  writer_seat=args.writer_seat, question_seat=args.question_seat)
            stopped = report["lessons"][-1] if report["lessons"] else None
            if args.lesson is not None and stopped and stopped["stopping_check"] == 0:
                print(json.dumps({"check": 0, "reason": stopped["reason"], "layer": stopped["layer"]},
                                 ensure_ascii=False, sort_keys=True))
            else:
                print(json.dumps(report, ensure_ascii=False, sort_keys=True))
            return 0 if report["complete"] else 1
        except (OSError, ValueError, KeyError) as err:
            print(json.dumps({"check": 1, "reason": str(err), "layer": "driver"}, ensure_ascii=False), file=sys.stderr)
            return 1

    if args.command == "closure":
        from scripts.build.fresh.closure import compute_closure
        try:
            plan, _, _, _, paths = _load_lesson_data(args.level, args.slug, 1, repo_root=repo_root)
            report = compute_closure(args.level, args.slug, list(plan["lessons"]), repo_root=repo_root,
                                     state_dir=paths["state_dir"] / args.slug)
            print(json.dumps(report, ensure_ascii=False, sort_keys=True))
            return 0
        except (OSError, ValueError, KeyError) as err:
            print(json.dumps({"reason": str(err), "layer": "driver"}, ensure_ascii=False), file=sys.stderr)
            return 1

    if args.command == "render-prompt":
        plan_dict, lesson_entry, pack_dict, words_dict, paths = _load_lesson_data(
            args.level, args.slug, args.lesson, repo_root=repo_root
        )
        card_path, _, _card_sha = style_card_info(args.level, cards_dir=cards_dir)

        # Compute planned state and immersion payload
        pos = plan_dict.get("arc_ref", {}).get("position", 1)
        p_state = planned_state(
            args.level,
            pos,
            args.lesson,
            allow_missing_prior=True,
            plans_dir=paths["plan"].parent,
            evidence_dir=paths["words"].parent,
        )
        imm_payload = compute_immersion_payload(
            args.level, pos, args.lesson, cumulative_core_count=p_state.cumulative_core_count
        )

        # Load real cited records from pack and word store (Finding 1)
        cited_records = _load_cited_records(lesson_entry, pack_dict, words_dict)

        # Compute real input hashes (Finding 1)
        hashes = _compute_input_hashes(paths, args.lesson, p_state)

        is_recap = lesson_entry.get("kind") == "recap"
        if args.recap is not None and args.recap != is_recap:
            print(
                f"Error: --recap={args.recap} disagrees with plan lesson kind {lesson_entry.get('kind')!r}",
                file=sys.stderr,
            )
            return 1

        if is_recap:
            # Load built lessons 1..N-1 from real files, failing closed if missing (Finding 1)
            try:
                built = _load_recap_built_lessons(paths["state_dir"], args.level, args.slug, args.lesson, repo_root)
            except (FileNotFoundError, ValueError) as err:
                print(f"Error loading recap built lessons: {err}", file=sys.stderr)
                return 1

            rendered = render_recap_prompt(
                lesson_entry,
                built_lessons=built,
                cited_records=cited_records,
                learner_state=p_state,
                immersion=imm_payload,
                level=args.level,
                slug=args.slug,
                lesson_n=args.lesson,
                style_card_path=card_path,
                plan_sha256=hashes["plan_sha256"],
                pack_lock=hashes["pack_lock"],
                words_lock=hashes["words_lock"],
                lesson_lock_entry_sha256=hashes["lesson_lock_entry_sha256"],
                learner_state_sha256=hashes["learner_state_sha256"],
            )
            check_res = check_rendered_prompt(rendered, lesson_entry, card_path, is_recap=True, built_lessons=built)
        else:
            rendered = render_lesson_prompt(
                lesson_entry,
                cited_records=cited_records,
                learner_state=p_state,
                immersion=imm_payload,
                level=args.level,
                slug=args.slug,
                lesson_n=args.lesson,
                style_card_path=card_path,
                plan_sha256=hashes["plan_sha256"],
                pack_lock=hashes["pack_lock"],
                words_lock=hashes["words_lock"],
                lesson_lock_entry_sha256=hashes["lesson_lock_entry_sha256"],
                learner_state_sha256=hashes["learner_state_sha256"],
            )
            check_res = check_rendered_prompt(rendered, lesson_entry, card_path, is_recap=False)

        if not check_res.passed:
            print("Rendered-prompt check FAILED:", file=sys.stderr)
            for err in check_res.errors:
                print(f"  - {err}", file=sys.stderr)
            return 1

        # Always record prompt sha256 (#8431, Finding 11)
        state_dir = paths["state_dir"] / args.slug
        state_dir.mkdir(parents=True, exist_ok=True)
        sha_file = state_dir / f"lesson-{args.lesson}.prompt.sha256"
        lock.atomic_write(sha_file, f"{check_res.prompt_sha256}\n".encode("ascii"))

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            lock.atomic_write(args.output, rendered.encode("utf-8"))
            print(f"Rendered prompt written to {args.output} (sha256: {check_res.prompt_sha256})")
        else:
            print(rendered)
            print(f"# prompt sha256: {check_res.prompt_sha256}", file=sys.stderr)

        return 0

    elif args.command == "preflight":
        plan_dict, lesson_entry, pack_dict, words_dict, paths = _load_lesson_data(
            args.level, args.slug, args.lesson, repo_root=repo_root
        )
        pos = plan_dict.get("arc_ref", {}).get("position", 1)
        p_state = planned_state(
            args.level,
            pos,
            args.lesson,
            allow_missing_prior=True,
            plans_dir=paths["plan"].parent,
            evidence_dir=paths["words"].parent,
        )

        res = preflight_lesson(
            lesson_entry,
            pack=pack_dict,
            word_store=words_dict,
            gap_report_path=args.gap_report,
            pack_path=paths["pack"],
            words_path=paths["words"],
            level=args.level,
            slug=args.slug,
            learner_state=p_state,
            repo_root=repo_root,
            plans_dir=paths["plan"].parent,
            evidence_dir=paths["words"].parent,
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
        plan_dict, lesson_entry, pack_dict, words_dict, paths = _load_lesson_data(
            args.level, args.slug, args.lesson, repo_root=repo_root
        )
        card_path, _, _card_sha = style_card_info(args.level, cards_dir=cards_dir)
        pos = plan_dict.get("arc_ref", {}).get("position", 1)
        p_state = planned_state(
            args.level,
            pos,
            args.lesson,
            allow_missing_prior=True,
            plans_dir=paths["plan"].parent,
            evidence_dir=paths["words"].parent,
        )
        imm_payload = compute_immersion_payload(
            args.level, pos, args.lesson, cumulative_core_count=p_state.cumulative_core_count
        )

        out_dir = args.output_dir or (paths["state_dir"] / args.slug)
        out_dir.mkdir(parents=True, exist_ok=True)
        gap_report_file = out_dir / f"lesson-{args.lesson}.gaps.yaml"

        # 1. Run preflight first with gap report destination (#8431 §4, Finding 4)
        pre_res = preflight_lesson(
            lesson_entry,
            pack=pack_dict,
            word_store=words_dict,
            pack_path=paths["pack"],
            words_path=paths["words"],
            level=args.level,
            slug=args.slug,
            gap_report_path=gap_report_file,
            learner_state=p_state,
            repo_root=repo_root,
            plans_dir=paths["plan"].parent,
            evidence_dir=paths["words"].parent,
        )

        if not pre_res.passed:
            print("Preflight FAILED with evidence gaps. NO writer call made.", file=sys.stderr)
            print(f"Gap report written atomically to {gap_report_file}", file=sys.stderr)
            for g in pre_res.gaps:
                print(f"  [{g.step}] need: {g.need} — {g.detail}", file=sys.stderr)
            return 1

        # Check plan lesson kind vs --recap
        is_recap = lesson_entry.get("kind") == "recap"
        if getattr(args, "recap", None) is not None and args.recap != is_recap:
            print(
                f"Error: --recap={args.recap} disagrees with plan lesson kind {lesson_entry.get('kind')!r}",
                file=sys.stderr,
            )
            return 1

        # 2. Render prompt with real cited records and hashes (Finding 1, MAJOR B)
        cited_records = _load_cited_records(lesson_entry, pack_dict, words_dict)
        hashes = _compute_input_hashes(paths, args.lesson, p_state)

        if is_recap:
            try:
                built = _load_recap_built_lessons(paths["state_dir"], args.level, args.slug, args.lesson, repo_root)
            except (FileNotFoundError, ValueError) as err:
                print(f"Error loading recap built lessons: {err}", file=sys.stderr)
                return 1

            rendered_prompt = render_recap_prompt(
                lesson_entry,
                built_lessons=built,
                cited_records=cited_records,
                learner_state=p_state,
                immersion=imm_payload,
                level=args.level,
                slug=args.slug,
                lesson_n=args.lesson,
                style_card_path=card_path,
                plan_sha256=hashes["plan_sha256"],
                pack_lock=hashes["pack_lock"],
                words_lock=hashes["words_lock"],
                lesson_lock_entry_sha256=hashes["lesson_lock_entry_sha256"],
                learner_state_sha256=hashes["learner_state_sha256"],
            )
            check_res = check_rendered_prompt(
                rendered_prompt, lesson_entry, card_path, is_recap=True, built_lessons=built
            )
        else:
            rendered_prompt = render_lesson_prompt(
                lesson_entry,
                cited_records=cited_records,
                learner_state=p_state,
                immersion=imm_payload,
                level=args.level,
                slug=args.slug,
                lesson_n=args.lesson,
                style_card_path=card_path,
                plan_sha256=hashes["plan_sha256"],
                pack_lock=hashes["pack_lock"],
                words_lock=hashes["words_lock"],
                lesson_lock_entry_sha256=hashes["lesson_lock_entry_sha256"],
                learner_state_sha256=hashes["learner_state_sha256"],
            )
            check_res = check_rendered_prompt(rendered_prompt, lesson_entry, card_path, is_recap=False)

        if not check_res.passed:
            print("Rendered prompt check FAILED:", file=sys.stderr)
            for err in check_res.errors:
                print(f"  - {err}", file=sys.stderr)
            return 1

        # 3. Write prompt and prompt sha256 to state dir atomically (#8431 §1, Finding 11)
        prompt_file = out_dir / f"lesson-{args.lesson}.prompt.md"
        lock.atomic_write(prompt_file, rendered_prompt.encode("utf-8"))
        prompt_sha_file = out_dir / f"lesson-{args.lesson}.prompt.sha256"
        lock.atomic_write(prompt_sha_file, f"{check_res.prompt_sha256}\n".encode("ascii"))

        # 4. Dispatch writer with structural preflight gate (#8431 §1, §7 row 0, Finding 4)
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
            preflight_result=pre_res,
            attempt=args.attempt,
            plan_activity_types=plan_activity_types,
            fake_seat=args.fake_seat,
            repo_root=repo_root,
        )

        print(f"Writer call succeeded for {args.level}/{args.slug} lesson {args.lesson} (seat: {args.writer}).")
        print(f"Draft saved to {res['draft_file']}")
        return 0

    elif args.command == "assemble":
        from scripts.build.fresh.assemble import assemble_lesson

        res = assemble_lesson(
            level=args.level,
            slug=args.slug,
            lesson_n=args.lesson,
            repo_root=repo_root,
            output_dir=args.output_dir,
            site_dir=args.site_dir,
            astro_build=args.astro_build,
        )
        if not res.get("ok"):
            print("Assembly failed:", file=sys.stderr)
            blocking = res.get("blocking_tokens")
            failures = res.get("stream_failures")
            if blocking or failures:
                if res.get("message"):
                    print(f"  {res['message']}", file=sys.stderr)
                for tok in blocking or []:
                    print(f"  Blocking token: {tok}", file=sys.stderr)
                for f in failures or []:
                    print(f"  Stream failure: {f}", file=sys.stderr)
            elif "failure" in res:
                failure = res.get("failure") or {}
                print(f"  Check {failure.get('check')}: {failure.get('reason')}", file=sys.stderr)
            elif "message" in res:
                print(f"  {res['message']}", file=sys.stderr)
            return 1

        print(f"Assembly succeeded for {args.level}/{args.slug} lesson {args.lesson}.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
