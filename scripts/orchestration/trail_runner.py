#!/usr/bin/env python3
"""Command-line entry point for the SQLite-authoritative TrailSpec runner."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.orchestration.trails.executor import TrailExecutor
from scripts.orchestration.trails.models import ExitClass, TrailRunnerError, TrailRunResult
from scripts.orchestration.trails.store import TrailStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DATABASE_PATH = PROJECT_ROOT / "batch_state/trails/runs.sqlite3"
RECEIPTS_ROOT = PROJECT_ROOT / "batch_state/trails/receipts"
TRAILS_ROOT = PROJECT_ROOT / "scripts/config/trails"


class JsonArgumentParser(argparse.ArgumentParser):
    """Keep malformed invocations inside the one-JSON-object public contract."""

    def error(self, message: str) -> None:
        raise TrailRunnerError(message)


def build_parser() -> argparse.ArgumentParser:
    """Build exactly the P3 invocation surface from the normative memo."""
    parser = JsonArgumentParser(prog="trail_runner.py", add_help=False)
    commands = parser.add_subparsers(dest="command", required=True)

    begin = commands.add_parser("begin", add_help=False)
    begin.add_argument("--trail", required=True)
    begin.add_argument("--seat", required=True)
    begin.add_argument("--task-family", required=True)
    begin.add_argument("--params", required=True)

    status = commands.add_parser("status", add_help=False)
    status.add_argument("--run-id", required=True)

    step = commands.add_parser("step", add_help=False)
    step.add_argument("--run-id", required=True)
    step.add_argument("--expected-step", required=True)

    resume = commands.add_parser("resume", add_help=False)
    resume.add_argument("--run-id", required=True)
    resume.add_argument("--authority-receipt-id", required=True)

    verify_chain = commands.add_parser("verify-chain", add_help=False)
    verify_chain.add_argument("--run-id", required=True)

    close = commands.add_parser("close", add_help=False)
    close.add_argument("--run-id", required=True)
    return parser


def resolve_trail(value: str) -> Path:
    """Resolve a trail ID to shipped configuration or accept an explicit file path."""
    supplied = Path(value)
    if supplied.is_file():
        return supplied
    candidate = TRAILS_ROOT / f"{value}.trail.yaml"
    if candidate.is_file():
        return candidate
    raise TrailRunnerError(f"trail '{value}' is not a readable .trail.yaml file")


def load_params(path_value: str) -> dict[str, Any]:
    """Load the required JSON params object without accepting raw inline JSON."""
    path = Path(path_value)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TrailRunnerError(f"cannot read --params JSON file '{path}': {exc}") from exc
    if not isinstance(payload, dict):
        raise TrailRunnerError("--params JSON must contain an object")
    return payload


def default_executor() -> TrailExecutor:
    """Construct the production ledger rooted at the repository's batch state."""
    return TrailExecutor(
        TrailStore(RUNS_DATABASE_PATH, RECEIPTS_ROOT), project_root=PROJECT_ROOT
    )


def _invalid_result(command: str | None, error: str) -> TrailRunResult:
    return TrailRunResult(
        command=command if command in {"begin", "status", "step", "resume", "verify-chain", "close"} else "begin",
        exit_class=ExitClass.INVALID,
        outcome="invalid_input",
        error=error,
    )


def dispatch(args: argparse.Namespace, executor: TrailExecutor) -> TrailRunResult:
    """Call the selected verb without letting argparse print non-JSON output."""
    if args.command == "begin":
        return executor.begin(
            trail_path=resolve_trail(args.trail),
            seat=args.seat,
            task_family=args.task_family,
            params=load_params(args.params),
        )
    if args.command == "status":
        return executor.status(run_id=args.run_id)
    if args.command == "step":
        return executor.step(run_id=args.run_id, expected_step=args.expected_step)
    if args.command == "resume":
        return executor.resume(
            run_id=args.run_id, authority_receipt_id=args.authority_receipt_id
        )
    if args.command == "verify-chain":
        return executor.verify_chain(run_id=args.run_id)
    if args.command == "close":
        return executor.close(run_id=args.run_id)
    raise TrailRunnerError(f"unsupported command {args.command!r}")


def main(argv: Sequence[str] | None = None, *, executor: TrailExecutor | None = None) -> int:
    """Emit one JSON result object and return its contract-defined exit class."""
    parser = build_parser()
    command: str | None = None
    try:
        args = parser.parse_args(argv)
        command = args.command
        result = dispatch(args, executor or default_executor())
    except TrailRunnerError as exc:
        result = _invalid_result(command, str(exc))
    except Exception as exc:
        result = _invalid_result(command, f"runner failed closed: {type(exc).__name__}")
    print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
    return int(result.exit_class)


if __name__ == "__main__":
    raise SystemExit(main())
