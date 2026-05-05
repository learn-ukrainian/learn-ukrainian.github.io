#!/usr/bin/env python3
"""Review-only CLI for the V7 linear module pipeline."""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build import linear_pipeline
from scripts.common.thresholds import QG_DIMS

AGENT_ALIASES = {
    "claude": "claude-tools",
    "gemini": "gemini-tools",
    "codex": "codex-tools",
    "gpt": "codex-tools",
    "gpt55": "codex-tools",
    "gpt-5.5": "codex-tools",
    "openai": "codex-tools",
}
REVIEWER_CHOICES = (*linear_pipeline.REVIEWER_CHOICES, *AGENT_ALIASES)
FRONTMATTER_RE = re.compile(r"^---\s*\n(?P<body>.*?)\n---\s*(?:\n|\Z)", re.DOTALL)


def emit_event(event: str, **fields: Any) -> None:
    linear_pipeline.emit_event(event, **fields)


def _resolve_project_path(raw: str | None) -> Path | None:
    if raw is None:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _normalize_agent(raw: str) -> str:
    value = raw.strip().casefold().replace("_tools", "-tools")
    return AGENT_ALIASES.get(value, value)


def _writer_from_frontmatter(text: str) -> str | None:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    try:
        payload = yaml.safe_load(match.group("body"))
    except yaml.YAMLError as exc:
        raise linear_pipeline.LinearPipelineError(
            f"Content front matter is invalid YAML: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        return None
    writer = payload.get("writer")
    if writer is None:
        return None
    return _normalize_agent(str(writer))


def _writer_from_content_path(path: Path) -> str | None:
    stem = path.stem.casefold()
    if stem in {"claude", "gemini", "gpt55"}:
        return _normalize_agent(stem)
    return None


def _phase_done(
    phase: str,
    started_at: float,
    *,
    level: str,
    slug: str,
    **fields: Any,
) -> None:
    emit_event(
        "phase_done",
        level=level,
        slug=slug,
        phase=phase,
        duration_s=round(time.monotonic() - started_at, 3),
        **fields,
    )


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description=(
            "Run only the V7 per-dimension LLM review for an existing lesson markdown file.\n"
            "Use for bakeoff cross-review or reviewer reruns; do not use it to write or repair modules."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/build/v7_review.py a1 my-morning \\\n"
            "    --content audit/bakeoff-2026-05-05/gemini.md \\\n"
            "    --reviewer claude-tools\n"
            "  .venv/bin/python scripts/build/v7_review.py a1 my-morning \\\n"
            "    --content audit/bakeoff-2026-05-05/gpt55.md \\\n"
            "    --reviewer gemini-tools \\\n"
            "    --telemetry-out audit/bakeoff-2026-05-05/gpt55-gemini.review.jsonl\n\n"
            "Outputs:\n"
            "  Emits reviewer_dim_evidence and phase_review_summary JSONL to stdout, "
            "or appends those events to --telemetry-out. No curriculum, status, "
            "audit-review, or review-review files are modified.\n\n"
            "Exit codes:\n"
            "  0 when every configured LLM QG dimension is reviewed and aggregated.\n"
            "  1 on missing plan, packet, content, self-review, reviewer, or parse failure.\n"
            "  2 on command-line usage errors from argparse.\n\n"
            "Related:\n"
            "  Pipeline: scripts/build/linear_pipeline.py\n"
            "  Reviewer prompt: scripts/build/phases/linear-review-dim.md\n"
            "  Aggregator: scripts/audit/bakeoff_aggregate.py\n"
            "  Issue: #1703"
        ),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    parser.add_argument(
        "level",
        help="Curriculum level code, for example a1, b1-pro, or hist.",
    )
    parser.add_argument(
        "slug",
        help="Module slug matching curriculum/l2-uk-en/plans/{level}/{slug}.yaml.",
    )
    parser.add_argument(
        "--content",
        required=True,
        metavar="PATH",
        help=(
            "Markdown or MDX lesson file to review. Relative paths resolve "
            "from the repository root; example: audit/bakeoff-2026-05-05/gemini.md."
        ),
    )
    parser.add_argument(
        "--reviewer",
        required=True,
        choices=REVIEWER_CHOICES,
        help=(
            "Reviewer backend for every per-dimension LLM QG call; choices are "
            "claude-tools, gemini-tools, codex-tools, plus short aliases."
        ),
    )
    parser.add_argument(
        "--telemetry-out",
        metavar="PATH",
        default=None,
        help=(
            "Append JSONL review events to PATH instead of stdout. Relative "
            "paths resolve from the repository root; default: stdout."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    telemetry_out = _resolve_project_path(args.telemetry_out)
    with linear_pipeline.telemetry_event_sink(telemetry_out):
        return _run(args)


def _run(args: argparse.Namespace) -> int:
    level = args.level.lower()
    slug = args.slug
    reviewer = _normalize_agent(args.reviewer)
    content_path = _resolve_project_path(args.content)
    assert content_path is not None
    module_started_at = time.monotonic()
    phase = "start"
    module_ref = f"{level}/{slug}"
    captured_events: list[dict[str, Any]] = []

    def event_sink(event: str, **fields: Any) -> None:
        captured_events.append({"event": event, **fields})
        emit_event(event, **fields)

    emit_event("module_start", level=level, slug=slug, reviewer=reviewer)

    try:
        phase = "plan"
        started_at = time.monotonic()
        plan_path = linear_pipeline.plan_path_for(level, slug)
        plan_content = plan_path.read_text(encoding="utf-8")
        plan = linear_pipeline.load_plan(plan_path)
        linear_pipeline.validate_plan(plan)
        _phase_done(phase, started_at, level=level, slug=slug)

        phase = "knowledge_packet"
        started_at = time.monotonic()
        linear_pipeline.build_knowledge_packet(level=level, slug=slug, plan=plan)
        _phase_done(phase, started_at, level=level, slug=slug)

        phase = "content"
        started_at = time.monotonic()
        content = content_path.read_text(encoding="utf-8")
        writer_under_review = (
            _writer_from_frontmatter(content)
            or _writer_from_content_path(content_path)
            or "unknown"
        )
        if writer_under_review == reviewer:
            raise linear_pipeline.LinearPipelineError(
                f"Self-review refused: writer and reviewer are both {reviewer}"
            )
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            content=content_path,
            writer_under_review=writer_under_review,
        )

        phase = "review"
        started_at = time.monotonic()
        report: dict[str, dict[str, Any]] = {}
        for dim in QG_DIMS:
            prompt = linear_pipeline.render_review_prompt(
                plan,
                plan_content,
                content,
                dim,
            )
            response = linear_pipeline.invoke_reviewer_dim(
                prompt,
                reviewer,
                dim=dim,
                writer_under_review=writer_under_review,
                cwd=content_path.parent,
                module=module_ref,
                event_sink=event_sink,
            )
            report[dim] = linear_pipeline.parse_review_response(response, dim)

        audit_calls_total = sum(
            1 for event in captured_events if event["event"] == "reviewer_audit_call"
        )
        flags_raised_total = sum(
            len(event.get("flags_raised") or [])
            for event in captured_events
            if event["event"] == "reviewer_audit_call"
        )
        emitted_dims = {
            event.get("dim")
            for event in captured_events
            if event["event"] == "reviewer_dim_evidence"
        }
        if emitted_dims != set(QG_DIMS):
            missing = sorted(set(QG_DIMS) - emitted_dims)
            raise linear_pipeline.LinearPipelineError(
                f"Reviewer telemetry missing dim events: {missing}"
            )
        aggregate = linear_pipeline.aggregate_llm_review(
            report,
            str(plan["level"]),
            reviewer=reviewer,
            module=module_ref,
            writer_under_review=writer_under_review,
            audit_calls_total=audit_calls_total,
            flags_raised_total=flags_raised_total,
            event_sink=event_sink,
        )
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            reviewer=reviewer,
            verdict=aggregate["aggregate"]["verdict"],
        )
        emit_event(
            "module_done",
            level=level,
            slug=slug,
            reviewer=reviewer,
            duration_s=round(time.monotonic() - module_started_at, 3),
        )
        return 0
    except Exception as exc:
        emit_event(
            "module_failed",
            level=level,
            slug=slug,
            reviewer=reviewer,
            phase=phase,
            reason=str(exc)[:500],
        )
        print(f"v7_review failed in phase {phase}: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
