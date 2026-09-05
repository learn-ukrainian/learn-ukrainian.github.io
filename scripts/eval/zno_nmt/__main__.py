"""Prepare, run, score, and compare ZNO/NMT exams with separate key custody."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .core import (
    ExamError,
    compare_runs,
    digest,
    prepare_exam,
    read_json,
    score_run,
    validate_packet,
    write_private_json,
)
from .importers import import_zno
from .runner import preflight, run_exam, validate_config


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(
        description=__doc__,
        epilog="Runtime artifacts are private. Only the export command emits an aggregate for sharing. "
        "See docs/evaluations/zno-nmt.md. Exit 0: success; 2: invalid input or failed trial.",
    )
    commands = cli.add_subparsers(dest="command", required=True)
    imp = commands.add_parser("import-zno", help="Import one whole NLPForUA/ZNO paper, rejecting unsupported tasks")
    imp.add_argument("--input", type=Path, required=True)
    imp.add_argument("--test-id", required=True)
    imp.add_argument("--metadata", type=Path, required=True)
    imp.add_argument("--output", type=Path, required=True)
    prep = commands.add_parser("prepare", help="Separate a normalized exam into question-only packet and key")
    prep.add_argument("--exam", type=Path, required=True)
    prep.add_argument("--questions", type=Path, required=True)
    prep.add_argument("--key", type=Path, required=True)
    for name in ("preflight", "run", "pair"):
        run = commands.add_parser(name, help={
            "preflight": "Check configuration and tool capabilities without generating answers",
            "run": "Run one fresh trial; never accepts a grading key",
            "pair": "Freeze a repeated paired plan and run fresh sessions; never accepts a grading key",
        }[name])
        run.add_argument("--config", type=Path, required=True)
        run.add_argument("--sources-url-env", default="SOURCES_MCP_URL")
        if name != "pair":
            run.add_argument("--condition", choices=["closed-book", "sources"], required=True)
        if name != "preflight":
            run.add_argument("--questions", type=Path, required=True)
            run.add_argument("--output" if name == "run" else "--out-dir", type=Path, required=True)
    for name in ("score", "compare"):
        scorer = commands.add_parser(name, help="Offline key-custodian scoring; no provider calls")
        scorer.add_argument("--questions", type=Path, required=True)
        scorer.add_argument("--key", type=Path, required=True)
        scorer.add_argument("--output", type=Path, required=True)
        if name == "score":
            scorer.add_argument("--run", type=Path, required=True)
        else:
            scorer.add_argument("--control", type=Path, required=True)
            scorer.add_argument("--treatment", type=Path, required=True)
    export = commands.add_parser("export", help="Emit allowlisted numeric aggregates only, without text, keys or logs")
    export.add_argument("--input", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    return cli


PUBLIC_NUMERIC_FIELDS = frozenset({
    "raw_points", "max_points", "correct_items", "missing_items", "invalid_items", "passed",
    "expected_items", "expected_points", "source_items", "supported_items", "attempted_items",
    "total_items", "item_count", "score_delta", "raw_points_delta", "wins", "losses", "ties",
    "control_points", "treatment_points", "elapsed_seconds", "cost_usd", "input_tokens", "output_tokens",
    "tool_calls", "point_delta", "delta_points", "total", "complete", "failed_items",
    "items", "points", "control", "treatment", "delta", "total_tokens",
})


def public_aggregate(report: dict) -> dict:
    """Deliberately excludes arbitrary strings, item IDs, traces, metadata and paths."""
    result = {key: value for key, value in report.items()
              if key in PUBLIC_NUMERIC_FIELDS and (value is None or type(value) in {int, float, bool})}
    for key in ("denominator", "metrics", "control", "treatment", "tool_calls", "elapsed_seconds", "cost_usd"):
        if isinstance(report.get(key), dict):
            result[key] = public_aggregate(report[key])
    return result


def execute(args: argparse.Namespace) -> int:
    if args.command == "import-zno":
        exam = import_zno(read_json(args.input), args.test_id, read_json(args.metadata))
        write_private_json(args.output, exam)
        print(json.dumps({"imported_items": len(exam["items"])}))
    elif args.command == "prepare":
        if args.questions.resolve() == args.key.resolve() or args.questions.exists() or args.key.exists():
            raise ExamError("question and key destinations must be distinct new files")
        packet, key = prepare_exam(read_json(args.exam))
        write_private_json(args.questions, packet)
        write_private_json(args.key, key)
        print(json.dumps({"prepared_items": len(packet["items"]), "packet_sha256": packet["packet_sha256"]}))
    elif args.command in {"preflight", "run", "pair"}:
        config = read_json(args.config)
        validate_config(config)
        endpoint = os.environ.get(args.sources_url_env)
        if args.command == "preflight":
            result = preflight(config, args.condition, endpoint)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        packet = read_json(args.questions)
        validate_packet(packet)
        plan = {"schema": "zno-nmt.plan.v1", "packet_sha256": packet["packet_sha256"],
                "config": config, "config_sha256": digest(config)}
        if args.command == "run":
            if args.output.exists():
                raise ExamError("refusing to replace a trial")
            write_private_json(args.output.with_suffix(".plan.json"), {**plan, "condition": args.condition})
            result = run_exam(packet, config, args.condition, sources_url=endpoint)
            write_private_json(args.output, result)
            print(json.dumps({"condition": args.condition, "status": result["status"]}))
            return 0 if result["status"] == "ok" else 2
        args.out_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
        schedule = [
            {"repeat": repeat, "condition": condition}
            for repeat in range(1, config["repeats"] + 1)
            for condition in (("closed-book", "sources") if repeat % 2 else ("sources", "closed-book"))
        ]
        write_private_json(args.out_dir / "plan.json", {**plan, "schedule": schedule})
        # Refuse paid execution if either condition cannot be configured.
        for condition in ("closed-book", "sources"):
            preflight(config, condition, endpoint)
        for trial in schedule:
            result = run_exam(packet, config, trial["condition"], sources_url=endpoint)
            result["repeat"] = trial["repeat"]
            write_private_json(args.out_dir / f"{trial['repeat']:03d}-{trial['condition']}.json", result)
            print(json.dumps({**trial, "status": result["status"]}), flush=True)
            if result["status"] != "ok":
                return 2
    elif args.command in {"score", "compare"}:
        packet, key = read_json(args.questions), read_json(args.key)
        if args.command == "score":
            report = score_run(packet, key, read_json(args.run))
        else:
            report = compare_runs(packet, key, read_json(args.control), read_json(args.treatment))
        write_private_json(args.output, report)
        print(json.dumps(public_aggregate(report), ensure_ascii=False))
    else:
        report = {"schema": "zno-nmt.public-aggregate.v1", **public_aggregate(read_json(args.input))}
        write_private_json(args.output, report)
        print(json.dumps(report, ensure_ascii=False))
    return 0


def main() -> int:
    args = parser().parse_args()
    try:
        return execute(args)
    except (ExamError, ValueError, OSError) as exc:
        # Even unexpected transport failures must not print a private endpoint or credential.
        print(json.dumps({"status": "failed", "error_class": type(exc).__name__}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
