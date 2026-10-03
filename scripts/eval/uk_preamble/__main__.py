"""CLI for the Ukrainian preamble comparison (#9623): run, score, report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .common import (
    SEATS,
    HarnessError,
    ResultsDir,
    read_json,
    sha256_file,
    sha256_text,
    validate_run_tag,
    write_private_json,
    write_private_text,
)
from .dataset import load_set, parse_variants
from .dispatch import DelegateDispatcher, Dispatcher, workspace_probe
from .report import build_report, render_markdown
from .runner import (
    DEFAULT_LENGTH_RATIO,
    KINDS,
    Executor,
    candidate_slots,
    ensure_manifest,
    frozen_plan,
    load_manifest,
    pair_checks,
    plan_candidate_tasks,
    plan_judge_tasks,
    resolve_seats,
    rules_block,
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
  --results must resolve outside every Git work tree; it is refused before anything is written.
  Dispatches create delegate task records under batch_state/tasks/.

Exit codes:
  0 success (run: every planned task accepted); 1 run finished with failed or unrun tasks;
  2 invalid input, results directory inside a Git work tree, frozen-plan mismatch or harness error.

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


def make_dispatcher(args: argparse.Namespace, worker_cwd: Path) -> Dispatcher:
    return DelegateDispatcher(
        python=args.python or _primary_python(),
        delegate=REPO_ROOT / "scripts" / "delegate.py",
        cwd=worker_cwd,
        hard_timeout=args.hard_timeout,
    )


def make_workspace(worker_cwd: Path) -> Callable[[], dict[str, Any]]:
    return workspace_probe(worker_cwd)


def make_sources() -> SourcesClient:
    return LocalSources()


def make_executor(args: argparse.Namespace, results: ResultsDir, worker_cwd: Path) -> Executor:
    return Executor(
        make_dispatcher(args, worker_cwd),
        results,
        worker_cwd=worker_cwd,
        workspace=make_workspace(worker_cwd),
        max_parallel=args.max_parallel,
        spawn_interval=args.spawn_interval,
        retry_failed=args.retry_failed,
    )


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


def _ratio(value: str) -> float:
    number = float(value)
    if not 0.0 < number <= 1.0:
        raise argparse.ArgumentTypeError("must be in (0, 1]")
    return number


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
    run.add_argument(
        "--results",
        type=Path,
        required=True,
        help="Private results directory outside every Git work tree (created if missing).",
    )
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
        help="Task-id tag frozen in the manifest: lowercase letters, digits and '-', at most 32. "
        "Default: first 10 hex digits of the set's SHA-256.",
    )
    run.add_argument(
        "--smoke",
        action="store_true",
        help="Accept a set or plan below Protocol v2 (set minimums, 3 repeats, both task kinds). "
        "A smoke run is reported as incomplete and never authorises adoption. Default: refuse.",
    )
    run.add_argument(
        "--dry-run",
        action="store_true",
        help="Write prompts and validate every dispatch with delegate --dry-run; spawn nothing.",
    )
    run.add_argument(
        "--worker-cwd",
        type=Path,
        default=None,
        help="Working directory (delegate --cwd) of every task, frozen in the manifest; its commit and "
        "instruction files are fingerprinted per task. Default: this checkout.",
    )
    run.add_argument(
        "--seat",
        action="append",
        choices=list(SEATS),
        help="Seat to include (repeatable), frozen in the manifest. Default: all three seats.",
    )
    run.add_argument("--repeats", type=_positive, default=3, help="Repeats per seat x variant cell. Default: 3.")
    run.add_argument(
        "--kinds",
        type=_kinds,
        default=list(KINDS),
        help="Comma list of task kinds: review,writing. Default: both.",
    )
    _add_dispatch_args(run)

    score = commands.add_parser(
        "score",
        help="Score the frozen plan deterministically; optionally run the blind judges",
        description="Span-level review scoring, sources-tool writing metrics and (with --judge) blind pairwise "
        "judging, over the seats, repeats, kinds and items frozen by 'run'.",
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
    score.add_argument(
        "--judge-length-ratio",
        type=_ratio,
        default=DEFAULT_LENGTH_RATIO,
        help="Length control: judge a pair only when the shorter text has at least this share of the longer "
        f"text's words; frozen at first use. Default: {DEFAULT_LENGTH_RATIO}.",
    )
    _add_dispatch_args(score)

    report = commands.add_parser(
        "report",
        help="Paired differences, bootstrap CIs and the adoption rule",
        description="Read scores.json, check it against the frozen plan and apply the pre-registered adoption rule "
        "per seat.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )
    report.add_argument("--results", type=Path, required=True, help="Results directory holding scores.json.")
    report.add_argument("--bootstrap", type=_positive, default=10_000, help="Bootstrap iterations. Default: 10000.")
    report.add_argument("--seed", type=int, default=9623, help="Bootstrap seed. Default: 9623.")
    return parser


def _worker_cwd(path: Path | None) -> Path:
    cwd = (path or REPO_ROOT).expanduser().resolve()
    if not cwd.is_dir():
        raise HarnessError(f"--worker-cwd {cwd} is not a directory")
    return cwd


def _cmd_run(args: argparse.Namespace) -> int:
    results = ResultsDir(args.results)  # refused inside a Git work tree before anything is written
    eval_set = load_set(args.set)
    variants = parse_variants(args.variant)
    run_tag = validate_run_tag(args.run_tag or eval_set.sha256[:10])
    worker_cwd = _worker_cwd(args.worker_cwd)
    block = rules_block()
    plan = frozen_plan(
        eval_set,
        variants,
        resolve_seats(args.seat),
        args.repeats,
        args.kinds,
        args.chunk_size,
        run_tag,
        worker_cwd,
        block,
    )
    if plan["protocol_shortfalls"] and not args.smoke:
        raise HarnessError("plan below Protocol v2: " + "; ".join(plan["protocol_shortfalls"]) + " (--smoke to test)")
    ensure_manifest(results, plan, args.set.resolve())
    tasks = plan_candidate_tasks(eval_set, variants, plan, block)
    executor = make_executor(args, results, worker_cwd)
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


def _judge_terms(args: argparse.Namespace, manifest: dict[str, Any], block: str) -> dict[str, Any]:
    """The judge terms frozen at first use; a later call with different terms is refused."""
    terms = {
        "seed": args.judge_seed,
        "chunk_size": args.judge_chunk_size,
        "length_ratio_min": args.judge_length_ratio,
    }
    frozen = manifest.get("judge")
    if frozen is None:
        return {**terms, "rules_core_sha256": sha256_text(block)}
    if {key: frozen.get(key) for key in terms} != terms:
        raise HarnessError(f"judge terms were frozen as {frozen}")
    if frozen.get("rules_core_sha256") != sha256_text(block):
        raise HarnessError("the rules core changed since judging started; judge prompts would differ")
    return frozen


def _cmd_score(args: argparse.Namespace) -> int:
    results = ResultsDir(args.results)
    manifest = load_manifest(results)
    plan = manifest["frozen"]
    eval_set = _set_for(args, manifest)
    slots = candidate_slots(plan)
    exit_code = 0
    judge_tasks, exclusions, terms = [], [], manifest.get("judge")
    if "writing" in plan["kinds"] and (args.judge or terms is not None):
        block = rules_block()
        terms = _judge_terms(args, manifest, block)
        judge_tasks, exclusions = plan_judge_tasks(eval_set, results, plan, terms, block)
        if args.judge and judge_tasks:
            if manifest.get("judge") is None:
                manifest["judge"] = terms
                write_private_json(results.path("manifest.json"), manifest)
            summary = make_executor(args, results, Path(plan["worker_cwd"])).run(judge_tasks)
            exit_code = 0 if summary.complete else 1
    sources = make_sources()
    scored: dict[str, Any] = score_candidates(results, eval_set, slots, sources)
    scored["pairs"] = pair_checks(results, plan, slots)
    scored["judge"] = score_judgements(results, judge_tasks)
    scored["judge_exclusions"] = exclusions
    scored["judge_terms"] = terms
    scored["plan"] = plan
    scored["manifest_sha256"] = sha256_file(results.path("manifest.json"))
    scored["denominator"] = {
        "review_items": len(plan["item_ids"]["review"]),
        "seeded_errors": eval_set.error_count,
        "protected_spans": eval_set.protected_count,
        "writing_tasks": len(plan["item_ids"]["writing"]),
        "seats": len(plan["seats"]),
        "variants": len(plan["variants"]),
        "repeats": plan["repeats"],
        "kinds": ",".join(plan["kinds"]),
    }
    write_private_json(results.path("scores.json"), scored)
    failed = sum(r["failed"] for kind in ("review", "writing") for r in scored[kind])
    total = len(scored["review"]) + len(scored["writing"])
    invalid_pairs = sum(1 for pair in scored["pairs"] if pair["problem"])
    print(
        json.dumps(
            {
                "scored_items": total,
                "failed_items": failed,
                "invalid_pairs": invalid_pairs,
                "judgements": len(scored["judge"]),
                "judge_exclusions": len(exclusions),
            }
        )
    )
    return exit_code


def _cmd_report(args: argparse.Namespace) -> int:
    results = ResultsDir(args.results)
    manifest = load_manifest(results)
    path = results.path("scores.json")
    if not path.is_file():
        raise HarnessError(f"{path} not found; run 'score' first")
    scores = read_json(path)
    if scores.get("plan") != manifest["frozen"] or scores.get("manifest_sha256") != sha256_file(
        results.path("manifest.json")
    ):
        raise HarnessError("scores.json was not computed from the current manifest's frozen plan; run 'score' again")
    report = build_report(scores, manifest["frozen"], iterations=args.bootstrap, seed=args.seed)
    markdown = render_markdown(report)
    write_private_json(results.path("report.json"), report)
    write_private_text(results.path("report.md"), markdown)
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
