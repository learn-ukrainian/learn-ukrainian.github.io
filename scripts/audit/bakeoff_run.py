#!/usr/bin/env python3
"""Run the V7 three-writer bakeoff and cross-review harness."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.agent_runtime.registry import get_agent_entry
from scripts.build import linear_pipeline

DEFAULT_WRITERS = "claude-tools,gemini-tools,codex-tools"
PYTHON = Path(".venv/bin/python")
V7_BUILD = Path("scripts/build/v7_build.py")
V7_REVIEW = Path("scripts/build/v7_review.py")
BAKEOFF_AGGREGATE_SCRIPT = Path("scripts/audit/bakeoff_aggregate.py")
BAKEOFF_AGGREGATE = PROJECT_ROOT / BAKEOFF_AGGREGATE_SCRIPT

WRITER_ALIASES = {
    "claude": "claude-tools",
    "gemini": "gemini-tools",
    "codex": "codex-tools",
    "gpt": "codex-tools",
    "gpt55": "codex-tools",
    "gpt-5.5": "codex-tools",
    "openai": "codex-tools",
}


def _load_bakeoff_aggregate():
    spec = importlib.util.spec_from_file_location("bakeoff_aggregate", BAKEOFF_AGGREGATE)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {BAKEOFF_AGGREGATE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


bakeoff_aggregate = _load_bakeoff_aggregate()


@dataclass(frozen=True, slots=True)
class StepResult:
    label: str
    ok: bool
    skipped: bool = False
    detail: str = ""
    returncode: int | None = None


def _resolve_project_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _normalize_writer(raw: str) -> str:
    value = raw.strip().casefold().replace("_tools", "-tools")
    return WRITER_ALIASES.get(value, value)


def _parse_writers(raw: str) -> list[str]:
    writers: list[str] = []
    for part in raw.split(","):
        if not part.strip():
            continue
        writer = _normalize_writer(part)
        if writer not in writers:
            writers.append(writer)
    return writers


def _short_name(writer: str) -> str:
    return bakeoff_aggregate.normalize_agent(writer)


def _jsonl_has_event(path: Path, event: str) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("event") == event:
            return True
    return False


def _writer_complete(path: Path) -> bool:
    return _jsonl_has_event(path, "phase_writer_summary")


def _review_complete(path: Path) -> bool:
    return _jsonl_has_event(path, "phase_review_summary")


def _truncate_telemetry(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _validate_writer(writer: str) -> str | None:
    if writer not in linear_pipeline.WRITER_CHOICES:
        return (
            f"unknown writer {writer!r}; expected one of "
            f"{', '.join(linear_pipeline.WRITER_CHOICES)}"
        )
    agent_name = writer.split("-", 1)[0]
    try:
        get_agent_entry(agent_name)
    except KeyError:
        return f"writer {writer!r} does not resolve in agent runtime registry"
    return None


def _preflight(level: str, slug: str, writers: Sequence[str]) -> list[str]:
    errors: list[str] = []
    plan_path = linear_pipeline.plan_path_for(level, slug)
    if not plan_path.exists():
        errors.append(f"missing plan: {_display_path(plan_path)}")
    else:
        try:
            plan = linear_pipeline.load_plan(plan_path)
            linear_pipeline.validate_plan(plan)
        except Exception as exc:
            errors.append(f"invalid plan {_display_path(plan_path)}: {exc}")

    try:
        article_paths = linear_pipeline._wiki_article_paths(level, slug)
    except Exception as exc:
        errors.append(f"could not inspect wiki packet for {level}/{slug}: {exc}")
    else:
        if not article_paths:
            errors.append(f"missing wiki packet for {level}/{slug}")

    for writer in writers:
        error = _validate_writer(writer)
        if error:
            errors.append(error)
    return errors


def run_command(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_or_report(label: str, argv: Sequence[str]) -> StepResult:
    result = run_command(argv)
    if result.returncode == 0:
        return StepResult(label=label, ok=True, returncode=result.returncode)
    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    detail = stderr or stdout or f"exit {result.returncode}"
    print(f"error: {label} failed: {detail}", file=sys.stderr)
    return StepResult(label=label, ok=False, detail=detail, returncode=result.returncode)


def _spike(level: str, slug: str, writer: str) -> StepResult:
    return _run_or_report(
        f"spike {writer}",
        [
            str(PYTHON),
            str(V7_BUILD),
            level,
            slug,
            "--writer",
            writer,
            "--dry-run",
        ],
    )


def _copy_writer_markdown(out_dir: Path, bakeoff_dir: Path, slug: str, short: str) -> None:
    candidates = [
        out_dir / f"{slug}.md",
        out_dir / f"{slug}.mdx",
        out_dir / "module.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            shutil.copyfile(candidate, bakeoff_dir / f"{short}.md")
            return
    searched = ", ".join(path.name for path in candidates)
    raise FileNotFoundError(f"no writer markdown found in {out_dir}; checked {searched}")


def _run_writer(
    *,
    level: str,
    slug: str,
    writer: str,
    bakeoff_dir: Path,
    resume: bool,
) -> StepResult:
    short = _short_name(writer)
    telemetry = bakeoff_dir / f"{short}.write.jsonl"
    out_dir = bakeoff_dir / short
    if resume and _writer_complete(telemetry):
        return StepResult(label=f"write {writer}", ok=True, skipped=True)
    _truncate_telemetry(telemetry)

    result = _run_or_report(
        f"write {writer}",
        [
            str(PYTHON),
            str(V7_BUILD),
            level,
            slug,
            "--writer",
            writer,
            "--out",
            str(out_dir),
            "--telemetry-out",
            str(telemetry),
        ],
    )
    if not result.ok:
        return result
    try:
        _copy_writer_markdown(out_dir, bakeoff_dir, slug, short)
    except OSError as exc:
        print(f"error: write {writer} copy failed: {exc}", file=sys.stderr)
        return StepResult(label=f"write {writer}", ok=False, detail=str(exc))
    return result


def _run_review(
    *,
    level: str,
    slug: str,
    writer: str,
    reviewer: str,
    bakeoff_dir: Path,
    resume: bool,
) -> StepResult:
    writer_short = _short_name(writer)
    reviewer_short = _short_name(reviewer)
    target = bakeoff_dir / f"{writer_short}-{reviewer_short}.review.jsonl"
    if resume and _review_complete(target):
        return StepResult(
            label=f"review {writer}->{reviewer}",
            ok=True,
            skipped=True,
        )
    content = bakeoff_dir / f"{writer_short}.md"
    if not content.exists():
        detail = f"missing writer markdown for review: {content}"
        print(f"error: {detail}", file=sys.stderr)
        return StepResult(label=f"review {writer}->{reviewer}", ok=False, detail=detail)
    _truncate_telemetry(target)

    return _run_or_report(
        f"review {writer}->{reviewer}",
        [
            str(PYTHON),
            str(V7_REVIEW),
            level,
            slug,
            "--content",
            str(content),
            "--reviewer",
            reviewer,
            "--telemetry-out",
            str(target),
        ],
    )


def _run_aggregate(bakeoff_dir: Path, writers: Sequence[str]) -> StepResult:
    writer_shorts = ",".join(_short_name(writer) for writer in writers)
    return _run_or_report(
        "aggregate",
        [
            str(PYTHON),
            str(BAKEOFF_AGGREGATE_SCRIPT),
            "--bakeoff-dir",
            str(bakeoff_dir),
            "--writers",
            writer_shorts,
        ],
    )


def _print_summary(
    writer_results: Sequence[StepResult],
    review_results: Sequence[StepResult],
    aggregate_result: StepResult | None,
) -> None:
    print("Bakeoff summary")
    print("Writers:")
    if writer_results:
        for result in writer_results:
            state = "skipped" if result.skipped else ("pass" if result.ok else "fail")
            print(f"  {result.label}: {state}")
    else:
        print("  skipped")
    print("Reviews:")
    if review_results:
        for result in review_results:
            state = "skipped" if result.skipped else ("pass" if result.ok else "fail")
            print(f"  {result.label}: {state}")
    else:
        print("  skipped")
    if aggregate_result is None:
        print("Aggregate: skipped")
    else:
        state = "pass" if aggregate_result.ok else "fail"
        print(f"Aggregate: {state} exit_code={aggregate_result.returncode}")


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description=(
            "Run V7 bakeoff writes, cross-reviews, and aggregation for one module.\n"
            "Use for the A1/20 writer bakeoff; do not use it for V6 or bulk curriculum builds."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/audit/bakeoff_run.py \\\n"
            "    --bakeoff-dir audit/bakeoff-2026-05-05 \\\n"
            "    --level a1 --slug my-morning\n"
            "  .venv/bin/python scripts/audit/bakeoff_run.py \\\n"
            "    --bakeoff-dir audit/bakeoff-2026-05-05 \\\n"
            "    --level a1 --slug my-morning \\\n"
            "    --writers gemini-tools,codex-tools --writers-only\n"
            "  .venv/bin/python scripts/audit/bakeoff_run.py \\\n"
            "    --bakeoff-dir audit/bakeoff-2026-05-05 \\\n"
            "    --level a1 --slug my-morning --resume --reviewers-only\n\n"
            "Outputs:\n"
            "  Writes <writer>.md, <writer>.write.jsonl, "
            "<writer>-<reviewer>.review.jsonl, per-writer output directories, "
            "and REPORT.md unless --skip-aggregate is set. No curriculum, "
            "status, audit-review, or review-review files are modified.\n\n"
            "Exit codes:\n"
            "  0 when requested phases and aggregation all pass or are intentionally skipped.\n"
            "  1 on pre-flight failure or any failed write, review, or aggregate step.\n"
            "  2 on command-line usage errors from argparse.\n\n"
            "Related:\n"
            "  Builder: scripts/build/v7_build.py\n"
            "  Review-only CLI: scripts/build/v7_review.py\n"
            "  Aggregator: scripts/audit/bakeoff_aggregate.py\n"
            "  Brief: docs/dispatch-briefs/2026-05-05-a1-20-bakeoff-with-new-prompts.md\n"
            "  Issue: #1703"
        ),
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    parser.add_argument(
        "--bakeoff-dir",
        required=True,
        type=Path,
        help=(
            "Directory for bakeoff outputs; relative paths resolve from the "
            "repository root. Example: audit/bakeoff-2026-05-05."
        ),
    )
    parser.add_argument(
        "--level",
        required=True,
        help="Curriculum level code to build and review; example: a1.",
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="Module slug matching the plan and wiki packet; example: my-morning.",
    )
    parser.add_argument(
        "--writers",
        default=DEFAULT_WRITERS,
        help=(
            "Comma-separated writer/reviewer backends in execution order. "
            f"Default: {DEFAULT_WRITERS}."
        ),
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Skip already-complete writer/review JSONL outputs when present "
            "and marked by a terminal success event (default: false)."
        ),
    )
    parser.add_argument(
        "--skip-aggregate",
        action="store_true",
        help="Skip the final bakeoff_aggregate.py invocation (default: false).",
    )
    parser.add_argument(
        "--writers-only",
        action="store_true",
        help="Run writer phases only and skip cross-reviews (default: false).",
    )
    parser.add_argument(
        "--reviewers-only",
        action="store_true",
        help="Run cross-reviews only and skip writer phases (default: false).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.writers_only and args.reviewers_only:
        print("error: --writers-only and --reviewers-only cannot be combined", file=sys.stderr)
        return 1

    level = args.level.lower()
    slug = args.slug
    writers = _parse_writers(args.writers)
    if not writers:
        print("error: --writers must name at least one writer", file=sys.stderr)
        return 1

    errors = _preflight(level, slug, writers)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    bakeoff_dir = _resolve_project_path(args.bakeoff_dir)
    bakeoff_dir.mkdir(parents=True, exist_ok=True)

    writer_results: list[StepResult] = []
    review_results: list[StepResult] = []
    aggregate_result: StepResult | None = None

    if not args.reviewers_only:
        spike = _spike(level, slug, writers[0])
        if not spike.ok:
            _print_summary([], [], None)
            return 1

        for writer in writers:
            writer_results.append(
                _run_writer(
                    level=level,
                    slug=slug,
                    writer=writer,
                    bakeoff_dir=bakeoff_dir,
                    resume=args.resume,
                )
            )

    if not args.writers_only:
        for writer in writers:
            for reviewer in writers:
                if writer == reviewer:
                    continue
                review_results.append(
                    _run_review(
                        level=level,
                        slug=slug,
                        writer=writer,
                        reviewer=reviewer,
                        bakeoff_dir=bakeoff_dir,
                        resume=args.resume,
                    )
                )

    if not args.skip_aggregate:
        aggregate_result = _run_aggregate(bakeoff_dir, writers)

    _print_summary(writer_results, review_results, aggregate_result)
    failures = [result for result in (*writer_results, *review_results) if not result.ok]
    if aggregate_result is not None and not aggregate_result.ok:
        failures.append(aggregate_result)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
