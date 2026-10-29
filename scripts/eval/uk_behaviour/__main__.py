"""CLI for the Ukrainian behaviour evaluation (G3): prove, verify-pins, pin-code, plan."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

if __package__ in (None, ""):  # run as a file: put the repository root on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    __package__ = "scripts.eval.uk_behaviour"

from scripts.eval.uk_preamble.common import HarnessError, ResultsDir, enclosing_work_tree, validate_run_tag

from . import pins, prove
from .adapters import AdapterError, pinned_bytes
from .contract import JUDGE_SLOT, MANIFEST_PATH, PRIVATE_PROMPT_SLOTS, load_manifest, manifest_problems
from .rubric import rubric_sha256
from .runner import admission_refusal, load_bundle, plan_cells

EPILOG = """\
Examples:
  .venv/bin/python -m scripts.eval.uk_behaviour prove
  .venv/bin/python -m scripts.eval.uk_behaviour verify-pins --private-map ~/private/uk-behaviour/paths.json
  .venv/bin/python -m scripts.eval.uk_behaviour plan --requests ~/private/uk-behaviour/development-requests.json \\
      --private-map ~/private/uk-behaviour/paths.json --results ~/private/uk-behaviour/results --run-tag dev1 --dry-run

The private map is a JSON object from private slot to file, e.g.
  {"private://uk-behaviour-v2/card-review-prompt": "/private/card-review-prompt.md",
   "private://uk-behaviour-v2/semantic-scorer-and-judge-template#template": "/private/judge.md"}
Every mapped file must resolve outside every Git work tree.

Exit codes: 0 success; 1 a proof case or pin failed; 2 invalid input or refused execution.
"""


def _private_map(path: Path | None) -> dict[str, Path]:
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise HarnessError("private map is a JSON object")
    mapped = {}
    for slot, value in raw.items():
        target = Path(value).expanduser().resolve()
        if enclosing_work_tree(target) is not None:
            raise HarnessError(f"{slot} resolves inside a Git work tree; private bytes stay outside every repository")
        mapped[slot] = target
    return mapped


def _cmd_prove(args: argparse.Namespace) -> int:
    result = prove.run()
    failed = [case for case in result["cases"] if not case["pass"]]
    summary = {"proof": result["proof"], "cases": len(result["cases"]), "failed": failed, "pass": result["pass"]}
    print(json.dumps(result if args.verbose else summary, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


def _cmd_verify_pins(args: argparse.Namespace) -> int:
    manifest = load_manifest()
    found = manifest_problems(manifest) + pins.problems(manifest, private_paths=_private_map(args.private_map))
    print(json.dumps({"problems": found, "ok": not found}, ensure_ascii=False, indent=2))
    return 0 if not found else 1


def _cmd_pin_code(args: argparse.Namespace) -> int:
    """Re-pin the G3 code and rubric; the judge template digest is read from its private file."""
    manifest = load_manifest()
    g3 = manifest.setdefault("g3", {})
    g3["code"] = pins.code_pins()
    g3["rubric_sha256"] = rubric_sha256()
    if args.judge_template:
        g3["judge_template_sha256"] = pins.file_sha256(args.judge_template)
    if not g3.get("judge_template_sha256"):
        raise HarnessError("pass --judge-template the first time")
    entry = pins.private_ref(manifest, JUDGE_SLOT)
    entry["sha256"] = pins.g3_bundle_sha256(g3["code"], g3["rubric_sha256"], g3["judge_template_sha256"])
    entry["status"] = "PINNED"
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"code": len(g3["code"]), "bundle_sha256": entry["sha256"]}, indent=2))
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    results = ResultsDir(args.results)  # refused inside a Git work tree before anything is written
    manifest = load_manifest()
    paths = _private_map(args.private_map)
    found = manifest_problems(manifest) + pins.problems(manifest, private_paths=paths)
    if found:
        raise HarnessError("pins do not match: " + "; ".join(found))
    prompts = {}
    for family, slot in PRIVATE_PROMPT_SLOTS.items():
        if slot in paths:
            entry = pins.private_ref(manifest, slot)
            prompts[family] = pinned_bytes(paths[slot].read_bytes(), entry.get("sha256"), slot)
    tasks = plan_cells(load_bundle(args.requests), prompts, validate_run_tag(args.run_tag))
    if not args.dry_run:
        refusal = admission_refusal(manifest)
        if refusal:
            raise HarnessError(f"paid execution refused: {refusal}")
    from scripts.eval.uk_preamble.__main__ import make_dispatcher, make_executor

    worker_cwd = Path(args.worker_cwd or Path.cwd()).resolve()
    dispatch_args = argparse.Namespace(
        python=None,
        hard_timeout=1200,
        review_profile=None,
        max_parallel=2,
        spawn_interval=10.0,
        retry_failed=False,
    )
    dispatcher = make_dispatcher(dispatch_args, worker_cwd)
    executor = make_executor(dispatch_args, results, worker_cwd, dispatcher)
    if args.dry_run:
        summary = executor.preflight(tasks)
        print(json.dumps({"planned": len(tasks), "preflighted": summary.preflighted, "refused": summary.not_run}))
        return 0 if summary.complete else 1
    # Admitted only: the inherited executor, without retries (protocol: no rerun, resume by nonce).
    summary = executor.run(tasks)
    print(
        json.dumps(
            {"planned": len(tasks), "accepted": summary.accepted, "failed": summary.failed, "not_run": summary.not_run}
        )
    )
    return 0 if summary.complete else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.eval.uk_behaviour",
        description="Ukrainian behaviour evaluation (uk-behaviour/2): no-paid proof, pins and planning.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)
    proof = commands.add_parser("prove", help="Run the no-paid proof on synthetic fixtures (no provider calls)")
    proof.add_argument("--verbose", action="store_true", help="Print every case, not only failures. Default: off.")
    verify = commands.add_parser("verify-pins", help="Check every manifest pin against the bytes it names")
    verify.add_argument("--private-map", type=Path, default=None, help="JSON map of private slots to files.")
    pin = commands.add_parser("pin-code", help="Re-pin the G3 code, rubric and judge-template bundle in the manifest")
    pin.add_argument("--judge-template", type=Path, default=None, help="Private judge template file.")
    plan = commands.add_parser("plan", help="Render candidate cells and preflight (or, once admitted, run) them")
    plan.add_argument("--requests", type=Path, required=True, help="Private sealed request bundle.")
    plan.add_argument("--private-map", type=Path, required=True, help="JSON map of private slots to files.")
    plan.add_argument("--results", type=Path, required=True, help="Private results directory outside every work tree.")
    plan.add_argument("--run-tag", required=True, help="Lowercase letters, digits and '-', at most 32.")
    plan.add_argument("--worker-cwd", type=Path, default=None, help="Pinned dispatch worktree. Default: cwd.")
    plan.add_argument(
        "--dry-run",
        action="store_true",
        help="Preflight only. Without it the cells run, which is refused until the manifest admits the baseline.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {"prove": _cmd_prove, "verify-pins": _cmd_verify_pins, "pin-code": _cmd_pin_code, "plan": _cmd_plan}
    try:
        return handlers[args.command](args)
    except (HarnessError, AdapterError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
