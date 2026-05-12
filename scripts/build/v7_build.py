#!/usr/bin/env python3
"""CLI wrapper for the V7 linear module pipeline."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.agent_runtime.errors import AgentStalledError
from scripts.build import linear_pipeline
from scripts.common.thresholds import QG_DIMS

DEFAULT_WRITER_TIMEOUT_S = 1800
WRITER_ALIASES = {
    "claude": "claude-tools",
    "gemini": "gemini-tools",
    "codex": "codex-tools",
}
WRITER_CHOICES = (*linear_pipeline.WRITER_CHOICES, *WRITER_ALIASES)


@dataclass(slots=True)
class LastEventTracker:
    event_type: str | None = None
    event_ts: str | None = None

    def emit(self, event: str, **fields: Any) -> None:
        self.event_type = event
        self.event_ts = datetime.now(UTC).isoformat()
        emit_event(event, **fields)


def emit_event(event: str, **fields: Any) -> None:
    linear_pipeline.emit_event(event, **fields)


def _positive_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def _default_module_dir(level: str, slug: str) -> Path:
    return PROJECT_ROOT / "curriculum" / "l2-uk-en" / level.lower() / slug


def _resolve_output_dir(raw: str | None, level: str, slug: str) -> Path:
    if raw is None:
        return _default_module_dir(level, slug)
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _resolve_project_path(raw: str | None) -> Path | None:
    if raw is None:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _phase_done(
    phase: str,
    started_at: float,
    *,
    level: str,
    slug: str,
    event_sink: Callable[..., None] = emit_event,
    **fields: Any,
) -> None:
    event_sink(
        "phase_done",
        level=level,
        slug=slug,
        phase=phase,
        duration_s=round(time.monotonic() - started_at, 3),
        **fields,
    )


def _writer_prompt(
    *,
    plan: Mapping[str, Any],
    plan_content: str,
    knowledge_packet: str,
    wiki_manifest: str | Mapping[str, Any],
) -> str:
    return linear_pipeline.render_phase_prompt(
        PROJECT_ROOT / "scripts" / "build" / "phases" / "linear-write.md",
        linear_pipeline.writer_context(plan, plan_content, knowledge_packet, wiki_manifest),
    )


def _generated_content(module_dir: Path) -> str:
    parts = []
    for artifact in linear_pipeline.WRITER_ARTIFACTS:
        path = module_dir / artifact
        parts.append(f"## {artifact}\n\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def _reviewer_for_writer(writer: str) -> str:
    if writer == "claude-tools":
        return "gemini-tools"
    return "claude-tools"


def _normalize_writer(writer: str) -> str:
    return WRITER_ALIASES.get(writer, writer)


def _run_llm_qg(
    *,
    plan: Mapping[str, Any],
    plan_content: str,
    module_dir: Path,
    writer: str,
    stdout_silence_timeout: int | None = None,
) -> dict[str, Any]:
    from scripts.agent_runtime.runner import invoke

    reviewer = _reviewer_for_writer(writer)
    defaults = linear_pipeline.WRITER_DEFAULTS[reviewer]
    agent_name = reviewer.split("-", 1)[0]
    generated_content = _generated_content(module_dir)
    report: dict[str, Any] = {}

    for dim in QG_DIMS:
        prompt = linear_pipeline.render_review_prompt(
            plan,
            plan_content,
            generated_content,
            dim,
        )
        result = invoke(
            agent_name,
            prompt,
            mode="read-only",
            cwd=module_dir,
            model=defaults["model"],
            task_id=f"linear-v7-qg-{plan['slug']}-{dim}",
            entrypoint="dispatch",
            effort=defaults["effort"],
            tool_config={"output_format": "stream-json"},
            stdout_silence_timeout=stdout_silence_timeout,
        )
        response = str(getattr(result, "response", "") or "")
        report[dim] = linear_pipeline.parse_review_response(response, dim)

    return linear_pipeline.aggregate_llm_review(report, str(plan["level"]))


def _run_wiki_coverage_review(
    *,
    plan: Mapping[str, Any],
    plan_content: str,
    module_dir: Path,
    writer: str,
    wiki_manifest: str | Mapping[str, Any],
    wiki_coverage_gate: Mapping[str, Any],
    stdout_silence_timeout: int | None = None,
) -> dict[str, Any]:
    from scripts.agent_runtime.runner import invoke

    reviewer = _reviewer_for_writer(writer)
    defaults = linear_pipeline.REVIEWER_DEFAULTS[reviewer]
    agent_name = reviewer.split("-", 1)[0]
    generated_content = _generated_content(module_dir)
    prompt = linear_pipeline.render_wiki_coverage_review_prompt(
        plan,
        plan_content,
        generated_content,
        wiki_manifest,
        wiki_coverage_gate,
    )
    result = invoke(
        agent_name,
        prompt,
        mode="read-only",
        cwd=module_dir,
        model=defaults["model"],
        task_id=f"linear-v7-wiki-coverage-{plan['slug']}",
        entrypoint="dispatch",
        effort=defaults["effort"],
        tool_config={"output_format": "stream-json"},
        stdout_silence_timeout=stdout_silence_timeout,
    )
    response = str(getattr(result, "response", "") or "")
    return linear_pipeline.parse_wiki_coverage_review_response(response)


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description=(
            "Build one V7 curriculum module through scripts.build.linear_pipeline.\n"
            "Use for single-module V7 reboot builds; do not use for V6 legacy "
            "batch, resume, rewrite, or regeneration workflows."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/build/v7_build.py a1 my-morning --dry-run\n"
            "  .venv/bin/python scripts/build/v7_build.py a1 my-morning --writer gemini-tools\n"
            "  .venv/bin/python scripts/build/v7_build.py a1 my-morning --writer codex-tools --telemetry-out audit/bakeoff-2026-05-05/gpt55.write.jsonl\n"
            "  .venv/bin/python scripts/build/v7_build.py b1-pro intro --out /tmp/v7-intro\n\n"
            "Outputs:\n"
            "  Emits JSONL monitor events to stdout, or appends them to --telemetry-out. Full builds write the writer "
            "artifacts, knowledge_packet.md, writer_prompt.md, python_qg.json, "
            "llm_qg.json, and {slug}.mdx under --out or "
            "curriculum/l2-uk-en/{level}/{slug}/. Dry runs do not write files.\n\n"
            "Exit codes:\n"
            "  0 on successful build or dry run.\n"
            "  1 on plan, packet, writer, QG, review, MDX, or filesystem failure.\n"
            "  2 on command-line usage errors from argparse.\n\n"
            "  124 when a writer subprocess is killed after --writer-timeout "
            "seconds of stdout silence.\n\n"
            "Related:\n"
            "  Pipeline: scripts/build/linear_pipeline.py\n"
            "  Writer prompt: scripts/build/phases/linear-write.md\n"
            "  Reviewer prompt: scripts/build/phases/linear-review-dim.md\n"
            "  ADR-007: docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md\n"
            "  ADR-008: docs/decisions/2026-04-28-targeted-gate-correction-paths.md\n"
            "  Issue: #1637"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        "--writer",
        choices=WRITER_CHOICES,
        default="claude-tools",
        help=(
            "Writer backend for the one-shot V7 write phase "
            "(default: claude-tools; claude/gemini/codex aliases normalize to "
            "claude-tools/gemini-tools/codex-tools)."
        ),
    )
    parser.add_argument(
        "--writer-timeout",
        metavar="SECONDS",
        type=_positive_int,
        default=DEFAULT_WRITER_TIMEOUT_S,
        help=(
            "Kill the writer subprocess and exit 124 if it produces no stdout "
            f"for SECONDS (default: {DEFAULT_WRITER_TIMEOUT_S})."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Load the plan and build the knowledge packet, then stop before "
            "writer invocation and file writes (default: false)."
        ),
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        default=None,
        help=(
            "Output directory for full-build artifacts (default: "
            "curriculum/l2-uk-en/{level}/{slug}/). Relative paths resolve "
            "from the repository root."
        ),
    )
    parser.add_argument(
        "--telemetry-out",
        metavar="PATH",
        default=None,
        help=(
            "Append JSONL monitor events to PATH instead of stdout. Relative "
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
    writer = _normalize_writer(args.writer)
    module_started_at = time.monotonic()
    phase = "start"
    timeout_agent = writer
    tracker = LastEventTracker()

    tracker.emit("module_start", level=level, slug=slug)

    try:
        phase = "plan"
        started_at = time.monotonic()
        plan_path = linear_pipeline.plan_path_for(level, slug)
        plan_content = plan_path.read_text(encoding="utf-8")
        plan = linear_pipeline.load_plan(plan_path)
        linear_pipeline.validate_plan(plan)
        _phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)

        phase = "knowledge_packet"
        started_at = time.monotonic()
        knowledge_packet = linear_pipeline.build_knowledge_packet(
            level=level,
            slug=slug,
            plan=plan,
        )
        wiki_manifest = linear_pipeline.build_wiki_manifest(
            level=level,
            slug=slug,
            plan=plan,
        )
        _phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)

        if args.dry_run:
            sections = [
                str(item.get("section"))
                for item in plan.get("content_outline", [])
                if isinstance(item, Mapping) and item.get("section")
            ]
            linear_pipeline.emit_writer_response_telemetry(
                "",
                writer=writer,
                module=f"{level.lower()}/{int(plan['sequence'])}",
                sections=sections,
                tool_calls=[],
                event_sink=tracker.emit,
            )
            tracker.emit(
                "module_done",
                level=level,
                slug=slug,
                dry_run=True,
                duration_s=round(time.monotonic() - module_started_at, 3),
            )
            return 0

        module_dir = _resolve_output_dir(args.out, level, slug)

        phase = "writer"
        timeout_agent = writer
        started_at = time.monotonic()
        module_dir.mkdir(parents=True, exist_ok=True)
        prompt = _writer_prompt(
            plan=plan,
            plan_content=plan_content,
            knowledge_packet=knowledge_packet,
            wiki_manifest=wiki_manifest,
        )
        # gemini-tools must load .gemini/settings.json from repo root;
        # module_dir cwd would leave its MCP catalog empty. See
        # audit/gemini-tools-review-2026-05-09/REPORT.html E5/E6.
        writer_cwd = PROJECT_ROOT if writer == "gemini-tools" else module_dir
        writer_output = linear_pipeline.invoke_writer(
            prompt,
            writer,
            cwd=writer_cwd,
            tool_trace_path=module_dir / "writer_tool_calls.json",
            stdout_silence_timeout=args.writer_timeout,
        )
        # Save raw writer output + prompt + knowledge packet BEFORE parse so any
        # parse failure is fully debuggable. Without this, a parse error like
        # "Writer output contains unnamed fenced block at line 113" leaves
        # nothing on disk to inspect — the writer_output is held only in memory
        # and is lost on the LinearPipelineError raise.
        (module_dir / "writer_output.raw.md").write_text(
            writer_output,
            encoding="utf-8",
        )
        (module_dir / "writer_prompt.md").write_text(prompt, encoding="utf-8")
        (module_dir / "knowledge_packet.md").write_text(
            knowledge_packet,
            encoding="utf-8",
        )
        (module_dir / "wiki_manifest.json").write_text(
            wiki_manifest,
            encoding="utf-8",
        )
        artifacts = linear_pipeline.parse_writer_output(writer_output)
        linear_pipeline.write_writer_artifacts(module_dir, artifacts)
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            writer=writer,
            event_sink=tracker.emit,
        )

        phase = "python_qg"
        started_at = time.monotonic()
        python_qg = linear_pipeline.run_python_qg_with_corrections(
            module_dir,
            plan_path,
            writer=writer,
        )
        linear_pipeline.write_json(module_dir / "python_qg.json", python_qg)
        _phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)
        gates = python_qg.get("gates")
        if not isinstance(gates, Mapping) or gates.get("passed") is not True:
            raise linear_pipeline.LinearPipelineError(
                "Python QG failed after ADR-008 correction paths"
            )

        phase = "wiki_coverage_gate"
        started_at = time.monotonic()
        wiki_coverage_gate = linear_pipeline.run_wiki_coverage_gate(
            manifest=wiki_manifest,
            writer_output=writer_output,
            module_dir=module_dir,
            level=level,
        )
        linear_pipeline.write_json(module_dir / "wiki_coverage_gate.json", wiki_coverage_gate)
        _phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)
        if wiki_coverage_gate.get("passed") is not True:
            raise linear_pipeline.LinearPipelineError("Wiki coverage gate failed")

        phase = "wiki_coverage_review"
        timeout_agent = _reviewer_for_writer(writer)
        started_at = time.monotonic()
        wiki_coverage_review = _run_wiki_coverage_review(
            plan=plan,
            plan_content=plan_content,
            module_dir=module_dir,
            writer=writer,
            wiki_manifest=wiki_manifest,
            wiki_coverage_gate=wiki_coverage_gate,
            stdout_silence_timeout=args.writer_timeout,
        )
        linear_pipeline.write_json(
            module_dir / "wiki_coverage_review.json",
            wiki_coverage_review,
        )
        _phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)
        if wiki_coverage_review["overall_verdict"] == "FAIL":
            raise linear_pipeline.LinearPipelineError("Wiki coverage review failed")

        phase = "llm_qg"
        timeout_agent = _reviewer_for_writer(writer)
        started_at = time.monotonic()
        llm_qg = _run_llm_qg(
            plan=plan,
            plan_content=plan_content,
            module_dir=module_dir,
            writer=writer,
            stdout_silence_timeout=args.writer_timeout,
        )
        linear_pipeline.write_json(module_dir / "llm_qg.json", llm_qg)
        aggregate = llm_qg["aggregate"]
        tracker.emit(
            "review_score",
            level=level,
            slug=slug,
            score=aggregate["min_score"],
            verdict=aggregate["verdict"],
        )
        _phase_done(phase, started_at, level=level, slug=slug, event_sink=tracker.emit)
        if aggregate["verdict"] != "PASS":
            raise linear_pipeline.LinearPipelineError(
                f"LLM QG verdict was {aggregate['verdict']}"
            )

        phase = "mdx"
        started_at = time.monotonic()
        mdx_path = module_dir / f"{slug}.mdx"
        linear_pipeline.assemble_mdx(module_dir, mdx_path, plan_path)
        _phase_done(
            phase,
            started_at,
            level=level,
            slug=slug,
            output=mdx_path,
            event_sink=tracker.emit,
        )

        tracker.emit(
            "module_done",
            level=level,
            slug=slug,
            duration_s=round(time.monotonic() - module_started_at, 3),
        )
        return 0
    except AgentStalledError as exc:
        tracker.emit(
            "writer_timeout",
            level=level,
            slug=slug,
            writer=timeout_agent,
            phase=phase,
            timeout_s=args.writer_timeout,
            last_event_type=tracker.event_type,
            last_event_ts=tracker.event_ts,
            total_wall_time_s=round(time.monotonic() - module_started_at, 3),
        )
        print(f"v7_build timed out in phase {phase}: {exc}", file=sys.stderr, flush=True)
        return 124
    except Exception as exc:
        tracker.emit(
            "module_failed",
            level=level,
            slug=slug,
            phase=phase,
            reason=str(exc)[:500],
        )
        print(f"v7_build failed in phase {phase}: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
