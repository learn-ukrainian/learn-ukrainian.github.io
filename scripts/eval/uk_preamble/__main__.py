"""CLI for the Ukrainian preamble comparison (#9623): run, score, report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .common import SEATS, HarnessError, read_json, write_private_json, write_private_text
from .dataset import load_set, parse_variants, protocol_shortfalls
from .dispatch import DelegateDispatcher, Dispatcher
from .report import build_report, render_markdown
from .runner import (
    KINDS,
    Executor,
    candidate_slots,
    ensure_manifest,
    frozen_terms,
    load_manifest,
    plan_candidate_tasks,
    plan_judge_tasks,
    resolve_seats,
)
from .scoring import LocalSources, SourcesClient, score_candidates, score_judgements

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_JUDGE_SEED = 9623

EPILOG = """\
Examples:
  .venv/bin/python -m scripts.eval.uk_preamble run --set ~/private/uk-preamble/set-v1.json \\
      --results ~/private/uk-preamble/results --variant none \\
      --variant original=~/private/uk-preamble/original.md --variant adapted-v2=~/private/uk-preamble/adapted-v2.md
  .venv/bin/python -m scripts.eval.uk_preamble score --results ~/private/uk-preamble/results --judge
  .venv/bin/python -m scripts.eval.uk_preamble report --results ~/private/uk-preamble/results

Outputs (all under --results, owner-only files; never commit them):
  manifest.json, prompts/<task>.md, raw/<task>.json (run and score --judge);
  scores.json (score); report.json and report.md (report, also printed to stdout).
  Dispatches create delegate task records under batch_state/tasks/.

Exit codes:
  0 success (run: every planned task accepted); 1 run finished with failed or unrun tasks;
  2 invalid input, frozen-term mismatch or harness error.

Related:
  Protocol v2 on issue #9623; docs/evaluations/uk-preamble.md; scripts/delegate.py.
"""


def _primary_python() -> str:
    """The primary checkout's project interpreter (worktrees share it)."""
    try:
        common = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()
        return str(Path(common).parent / ".venv" / "bin" / "python")
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return str(REPO_ROOT / ".venv" / "bin" / "python")


def make_dispatcher(args: argparse.Namespace) -> Dispatcher:
    return DelegateDispatcher(
        python=args.python or _primary_python(),
        delegate=REPO_ROOT / "scripts" / "delegate.py",
        cwd=args.worker_cwd,
        hard_timeout=args.hard_timeout,
    )


def make_sources() -> SourcesClient:
    return LocalSources()


def _kinds(value: str) -> list[str]:
    kinds = [part.strip() for part in value.split(",") if part.strip()]
    if not kinds or any(kind not in KINDS for kind in kinds):
        raise argparse.ArgumentTypeError(f"expected a comma list of {', '.join(KINDS)}")
    return list(dict.fromkeys(kinds))


def _positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return number


def _add_plan_args(sub: argparse.ArgumentParser) -> None:
    sub.add_argument(
        "--seat",
        action="append",
        choices=list(SEATS),
        help="Seat to include (repeatable). Default: all three seats.",
    )
    sub.add_argument("--repeats", type=_positive, default=3, help="Repeats per seat x variant cell. Default: 3.")
    sub.add_argument(
        "--kinds",
        type=_kinds,
        default=list(KINDS),
        help="Comma list of task kinds: review,writing. Default: both.",
    )


def _add_dispatch_args(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--max-parallel", type=_positive, default=3, help="Concurrent dispatches. Default: 3.")
    sub.add_argument(
        "--spawn-interval",
        type=float,
        default=10.0,
        help="Minimum seconds between dispatch spawns (staggering). Default: 10.",
    )
    sub.add_argument(
        "--retry-failed",
        action="store_true",
        help="Re-dispatch stored tasks that were not accepted (failed, timed out or unattributable). Default: off.",
    )
    sub.add_argument(
        "--hard-timeout", type=_positive, default=3600, help="Per-task wall-clock limit in seconds. Default: 3600."
    )
    sub.add_argument(
        "--worker-cwd",
        type=Path,
        default=None,
        help="Working directory passed to delegate --cwd for every task. Default: the delegate's read-only worktree.",
    )
    sub.add_argument(
        "--python", default=None, help="Interpreter used to call scripts/delegate.py. Default: primary .venv python."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.eval.uk_preamble",
        description=(
            "Measure whether a Ukrainian system preamble improves Ukrainian review and writing per seat (#9623).\n"
            "Use it for the frozen preamble comparison only; it is not a general model benchmark."
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser(
        "run",
        help="Dispatch every seat x variant x repeat task (resumable)",
        description="Dispatch read-only review and writing tasks through scripts/delegate.py; resume safely.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )
    run.add_argument("--set", type=Path, required=True, help="Private evaluation set JSON (see dataset.py docstring).")
    run.add_argument("--results", type=Path, required=True, help="Private results directory (created if missing).")
    run.add_argument(
        "--variant",
        action="append",
        required=True,
        help="'none' or LABEL=PATH to a preamble file (repeatable; 'none' is required). "
        "Example: --variant none --variant adapted-v2=~/private/adapted-v2.md",
    )
    run.add_argument("--chunk-size", type=_positive, default=8, help="Items per dispatched task. Default: 8.")
    run.add_argument(
        "--run-tag",
        default=None,
        help="Task-id tag frozen in the manifest. Default: first 10 hex digits of the set's SHA-256.",
    )
    run.add_argument(
        "--allow-undersized-set",
        action="store_true",
        help="Accept a set below the Protocol v2 minimums (smoke runs only). Default: refuse.",
    )
    run.add_argument(
        "--dry-run",
        action="store_true",
        help="Write prompts and validate every dispatch with delegate --dry-run; spawn nothing.",
    )
    _add_plan_args(run)
    _add_dispatch_args(run)

    score = commands.add_parser(
        "score",
        help="Score stored outputs deterministically; optionally run the blind judges",
        description="Span-level review scoring, sources-tool writing metrics and (with --judge) blind pairwise judging.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )
    score.add_argument("--results", type=Path, required=True, help="Results directory written by 'run'.")
    score.add_argument(
        "--set", type=Path, default=None, help="Evaluation set JSON. Default: the manifest's path (hash-verified)."
    )
    score.add_argument(
        "--judge", action="store_true", help="Dispatch missing blind pairwise judge tasks before scoring. Default: off."
    )
    score.add_argument("--judge-chunk-size", type=_positive, default=8, help="Comparisons per judge task. Default: 8.")
    score.add_argument(
        "--judge-seed",
        type=int,
        default=DEFAULT_JUDGE_SEED,
        help=f"Seed for the A/B order randomisation; frozen at first use. Default: {DEFAULT_JUDGE_SEED}.",
    )
    _add_plan_args(score)
    _add_dispatch_args(score)

    report = commands.add_parser(
        "report",
        help="Paired differences, bootstrap CIs and the adoption rule",
        description="Read scores.json and apply the pre-registered adoption rule per seat.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )
    report.add_argument("--results", type=Path, required=True, help="Results directory holding scores.json.")
    report.add_argument("--bootstrap", type=_positive, default=10_000, help="Bootstrap iterations. Default: 10000.")
    report.add_argument("--seed", type=int, default=9623, help="Bootstrap seed. Default: 9623.")
    return parser


def _cmd_run(args: argparse.Namespace) -> int:
    eval_set = load_set(args.set)
    shortfalls = protocol_shortfalls(eval_set)
    if shortfalls and not args.allow_undersized_set:
        raise HarnessError("set below Protocol v2 minimums: " + "; ".join(shortfalls))
    variants = parse_variants(args.variant)
    run_tag = args.run_tag or eval_set.sha256[:10]
    frozen = frozen_terms(eval_set, variants, args.chunk_size, run_tag)
    ensure_manifest(args.results, frozen, args.set.resolve())
    seats = resolve_seats(args.seat)
    tasks = plan_candidate_tasks(eval_set, variants, seats, args.repeats, args.kinds, args.chunk_size, run_tag)
    executor = Executor(
        make_dispatcher(args),
        args.results,
        max_parallel=args.max_parallel,
        spawn_interval=args.spawn_interval,
        retry_failed=args.retry_failed,
    )
    if args.dry_run:
        summary = executor.preflight(tasks)
        print(json.dumps({"planned": len(tasks), "preflighted": summary.preflighted, "refused": summary.not_run}))
        return 0 if summary.complete else 1
    summary = executor.run(tasks)
    print(
        json.dumps(
            {
                "planned": len(tasks),
                "accepted": summary.accepted,
                "already_accepted": summary.skipped_accepted,
                "failed": summary.failed,
                "not_run": summary.not_run,
            },
            indent=2,
        )
    )
    return 0 if summary.complete else 1


def _set_for(args: argparse.Namespace, manifest: dict[str, Any]):
    path = args.set or Path(manifest["set_path"])
    eval_set = load_set(path)
    if eval_set.sha256 != manifest["frozen"]["set_sha256"]:
        raise HarnessError(f"{path} does not match the frozen set hash")
    return eval_set


def _cmd_score(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.results)
    eval_set = _set_for(args, manifest)
    frozen = manifest["frozen"]
    labels = list(frozen["variants"])
    seats = resolve_seats(args.seat)
    slots = candidate_slots(eval_set, seats, labels, args.repeats, args.kinds, frozen["chunk_size"], frozen["run_tag"])
    judge_terms = {"seed": args.judge_seed, "chunk_size": args.judge_chunk_size}
    if manifest.get("judge") not in (None, judge_terms):
        raise HarnessError(f"judge terms were frozen as {manifest['judge']}")
    judge_tasks = []
    if "writing" in args.kinds:
        judge_tasks = plan_judge_tasks(
            eval_set,
            args.results,
            slots,
            seats,
            labels,
            args.repeats,
            args.judge_chunk_size,
            args.judge_seed,
            frozen["run_tag"],
        )
    exit_code = 0
    if args.judge and judge_tasks:
        if manifest.get("judge") is None:
            manifest["judge"] = judge_terms
            write_private_json(args.results / "manifest.json", manifest)
        executor = Executor(
            make_dispatcher(args),
            args.results,
            max_parallel=args.max_parallel,
            spawn_interval=args.spawn_interval,
            retry_failed=args.retry_failed,
        )
        summary = executor.run(judge_tasks)
        exit_code = 0 if summary.complete else 1
    sources = make_sources()
    scored = score_candidates(args.results, eval_set, slots, sources)
    scored["judge"] = score_judgements(args.results, [task.task_id for task in judge_tasks])
    scored["denominator"] = {
        "review_items": len(eval_set.review),
        "seeded_errors": eval_set.error_count,
        "protected_spans": eval_set.protected_count,
        "writing_tasks": len(eval_set.writing),
        "seats": len(seats),
        "variants": len(labels),
        "repeats": args.repeats,
    }
    write_private_json(args.results / "scores.json", scored)
    failed = sum(r["failed"] for kind in ("review", "writing") for r in scored[kind])
    total = len(scored["review"]) + len(scored["writing"])
    print(json.dumps({"scored_items": total, "failed_items": failed, "judgements": len(scored["judge"])}))
    return exit_code


def _cmd_report(args: argparse.Namespace) -> int:
    path = args.results / "scores.json"
    if not path.is_file():
        raise HarnessError(f"{path} not found; run 'score' first")
    report = build_report(read_json(path), iterations=args.bootstrap, seed=args.seed)
    markdown = render_markdown(report)
    write_private_json(args.results / "report.json", report)
    write_private_text(args.results / "report.md", markdown)
    print(markdown, end="")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {"run": _cmd_run, "score": _cmd_score, "report": _cmd_report}
    try:
        return handlers[args.command](args)
    except HarnessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
