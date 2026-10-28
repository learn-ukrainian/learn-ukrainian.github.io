"""CLI: score a blind A/B comparison of two writers on Ukrainian lesson sections, offline from their outputs."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # run as a file: put the repository root on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    __package__ = "scripts.eval.lesson_ab"

from scripts.eval.human_eval_tracker import load_evaluations
from scripts.eval.uk_preamble.__main__ import _add_dispatch_args, _worker_cwd, make_executor, make_sources
from scripts.eval.uk_preamble.common import (
    SEATS,
    HarnessError,
    ResultsDir,
    read_json,
    sha256_text,
    validate_run_tag,
    write_private_json,
    write_private_text,
)
from scripts.eval.uk_preamble.runner import rules_block

from .core import HARNESS_VERSION, LocalChecks, Manifest, load_key, load_manifest, mechanical_checks
from .judge import plan_judge_tasks, resolve_judges, score_judgements, template_sha256
from .report import build_report, human_ratings, render_markdown

EPILOG = """\
Examples:
  # mechanical checks only (no model calls), blind report
  .venv/bin/python -m scripts.eval.lesson_ab --manifest ~/private/ab/manifest.json --results ~/private/ab/results
  # add both judges in both orders (dispatches 2 judges x tasks x 2 orders; accepted ones are never re-run)
  .venv/bin/python -m scripts.eval.lesson_ab --manifest ~/private/ab/manifest.json --results ~/private/ab/results \\
      --judge gemini-3.8-flash-high --judge claude-opus-5-5 --worker-cwd <isolated worktree>
  # unblind and import native-expert ratings, scoring stored judgements without dispatching
  .venv/bin/python -m scripts.eval.lesson_ab --manifest ~/private/ab/manifest.json --results ~/private/ab/results \\
      --judge gemini-3.8-flash-high --judge claude-opus-5-5 --no-dispatch --key ~/private/ab/key.json \\
      --human-ratings ~/private/ab/human

Outputs (owner-only, under --results, which must be outside every Git work tree):
  frozen.json (inputs, judge template and rules core, frozen on first use), prompts/ and raw/ (judges),
  scores.json, report-blind.{json,md} or report-unblinded.{json,md} (also printed).

Exit codes: 0 complete; 1 a judgement or mechanical check failed or was not run (kept in the report);
  2 invalid input, changed inputs since the first run, or a judge inside a writer's family.

Docs: docs/evaluations/lesson-ab.md.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.eval.lesson_ab",
        description="Blind A/B comparison of two writers on Ukrainian lesson sections, from already generated outputs.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--manifest", type=Path, required=True, help="Comparison manifest JSON (see the docs).")
    parser.add_argument("--results", type=Path, required=True, help="Private results directory outside Git.")
    parser.add_argument(
        "--judge",
        action="append",
        default=[],
        choices=sorted(SEATS),
        help="Judge seat (repeatable); refused when in a writer's family. Default: no judges.",
    )
    parser.add_argument("--no-dispatch", action="store_true", help="Score stored judgements only; dispatch nothing.")
    parser.add_argument("--dry-run", action="store_true", help="Write judge prompts and preflight them; spawn nothing.")
    parser.add_argument("--worker-cwd", type=Path, default=None, help="Isolated worktree judges run in.")
    parser.add_argument("--run-tag", default=None, help="Judge task-id tag. Default: manifest SHA-256 prefix.")
    parser.add_argument("--key", type=Path, default=None, help="Unblinding key JSON; read only after scoring.")
    parser.add_argument(
        "--human-ratings", type=Path, default=None, help="Directory of human_eval_tracker YAML ratings."
    )
    parser.add_argument("--bootstrap", type=int, default=2000, help="Bootstrap iterations. Default: 2000.")
    parser.add_argument("--seed", type=int, default=1028, help="Bootstrap seed. Default: 1028.")
    _add_dispatch_args(parser)
    return parser


def freeze(results: ResultsDir, manifest: Manifest, run_tag: str) -> dict[str, Any]:
    """Inputs, judge template and rules core frozen on first use; a changed input is refused later."""
    path = results.path("frozen.json")
    current = {
        "harness": HARNESS_VERSION,
        "manifest_sha256": manifest.sha256,
        "inputs": {task.task_id: task.digests for task in manifest.tasks},
        "judge_template_sha256": template_sha256(),
        "run_tag": run_tag,
    }
    if not path.is_file():
        block = rules_block()
        frozen = {**current, "rules_core_sha256": sha256_text(block), "rules_core": block}
        write_private_json(path, frozen)
        return frozen
    frozen = read_json(path)
    changed = sorted(k for k, v in current.items() if frozen.get(k) != v)
    if changed:
        raise HarnessError(f"{', '.join(changed)} changed since {path} was frozen; use a new --results directory")
    return frozen


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        results = ResultsDir(args.results)  # refused inside a Git work tree before anything is written
        manifest = load_manifest(args.manifest)
        run_tag = validate_run_tag(args.run_tag or manifest.sha256[:10])
        judges = resolve_judges(args.judge, manifest.writer_families)
        frozen = freeze(results, manifest, run_tag)
        tasks = plan_judge_tasks(manifest, judges, run_tag, frozen["rules_core"])
        exit_code = 0
        if tasks and not args.no_dispatch:
            executor = make_executor(args, results, _worker_cwd(args.worker_cwd))
            if args.dry_run:
                summary = executor.preflight(tasks)
                print(
                    json.dumps({"planned": len(tasks), "preflighted": summary.preflighted, "refused": summary.not_run})
                )
                return 0 if summary.complete else 1
            summary = executor.run(tasks)
            exit_code = 0 if summary.complete else 1
        mechanical = mechanical_checks(manifest, make_sources(), LocalChecks(), lambda m: print(m, file=sys.stderr))
        judgements = score_judgements(results, tasks)
        if any(r["failed"] for r in (*mechanical, *judgements)):
            exit_code = 1
        key = load_key(args.key, manifest) if args.key else None  # the key is read only here, at unblinding
        human = human_ratings(load_evaluations(args.human_ratings), manifest) if args.human_ratings else None
        frozen_summary = {k: v for k, v in frozen.items() if k != "rules_core"}
        report = build_report(
            manifest,
            mechanical,
            judgements,
            judges=[seat.seat_id for seat in judges],
            key=key,
            human=human,
            frozen=frozen_summary,
            iterations=args.bootstrap,
            seed=args.seed,
        )
    except HarnessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    write_private_json(results.path("scores.json"), {"mechanical": mechanical, "judgements": judgements})
    name = "report-blind" if key is None else "report-unblinded"
    markdown = render_markdown(report)
    write_private_json(results.path(f"{name}.json"), report)
    write_private_text(results.path(f"{name}.md"), markdown)
    print(markdown, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
