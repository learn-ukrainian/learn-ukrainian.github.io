#!/usr/bin/env python3
"""CLI wrapper for the V7 linear module pipeline."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build import linear_pipeline
from scripts.common.thresholds import QG_DIMS

WRITER_ALIASES = {
    "claude": "claude-tools",
    "gemini": "gemini-tools",
}
WRITER_CHOICES = (*linear_pipeline.WRITER_CHOICES, *WRITER_ALIASES)


def emit_event(event: str, **fields: Any) -> None:
    payload = {
        "event": event,
        "ts": datetime.now(UTC).isoformat(),
        **fields,
    }
    print(json.dumps(payload, ensure_ascii=False, default=str), flush=True)


def _default_module_dir(level: str, slug: str) -> Path:
    return PROJECT_ROOT / "curriculum" / "l2-uk-en" / level.lower() / slug


def _resolve_output_dir(raw: str | None, level: str, slug: str) -> Path:
    if raw is None:
        return _default_module_dir(level, slug)
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


def _writer_prompt(
    *,
    plan: Mapping[str, Any],
    plan_content: str,
    knowledge_packet: str,
) -> str:
    return linear_pipeline.render_phase_prompt(
        PROJECT_ROOT / "scripts" / "build" / "phases" / "linear-write.md",
        linear_pipeline.writer_context(plan, plan_content, knowledge_packet),
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
            tool_config={"output_format": "text"},
        )
        response = str(getattr(result, "response", "") or "")
        report[dim] = linear_pipeline.parse_review_response(response, dim)

    return linear_pipeline.aggregate_llm_review(report, str(plan["level"]))


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
            "  .venv/bin/python scripts/build/v7_build.py b1-pro intro --out /tmp/v7-intro\n\n"
            "Outputs:\n"
            "  Emits JSONL monitor events to stdout. Full builds write the writer "
            "artifacts, knowledge_packet.md, writer_prompt.md, python_qg.json, "
            "llm_qg.json, and {slug}.mdx under --out or "
            "curriculum/l2-uk-en/{level}/{slug}/. Dry runs do not write files.\n\n"
            "Exit codes:\n"
            "  0 on successful build or dry run.\n"
            "  1 on plan, packet, writer, QG, review, MDX, or filesystem failure.\n"
            "  2 on command-line usage errors from argparse.\n\n"
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
            "(default: claude-tools; claude/gemini aliases normalize to "
            "claude-tools/gemini-tools)."
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    level = args.level.lower()
    slug = args.slug
    writer = _normalize_writer(args.writer)
    module_started_at = time.monotonic()
    phase = "start"

    emit_event("module_start", level=level, slug=slug)

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
        knowledge_packet = linear_pipeline.build_knowledge_packet(
            level=level,
            slug=slug,
            plan=plan,
        )
        _phase_done(phase, started_at, level=level, slug=slug)

        if args.dry_run:
            emit_event(
                "module_done",
                level=level,
                slug=slug,
                dry_run=True,
                duration_s=round(time.monotonic() - module_started_at, 3),
            )
            return 0

        module_dir = _resolve_output_dir(args.out, level, slug)

        phase = "writer"
        started_at = time.monotonic()
        module_dir.mkdir(parents=True, exist_ok=True)
        prompt = _writer_prompt(
            plan=plan,
            plan_content=plan_content,
            knowledge_packet=knowledge_packet,
        )
        writer_output = linear_pipeline.invoke_writer(
            prompt,
            writer,
            cwd=module_dir,
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
        artifacts = linear_pipeline.parse_writer_output(writer_output)
        linear_pipeline.write_writer_artifacts(module_dir, artifacts)
        _phase_done(phase, started_at, level=level, slug=slug, writer=writer)

        phase = "python_qg"
        started_at = time.monotonic()
        python_qg = linear_pipeline.run_python_qg_with_corrections(
            module_dir,
            plan_path,
            writer=writer,
        )
        linear_pipeline.write_json(module_dir / "python_qg.json", python_qg)
        _phase_done(phase, started_at, level=level, slug=slug)
        gates = python_qg.get("gates")
        if not isinstance(gates, Mapping) or gates.get("passed") is not True:
            raise linear_pipeline.LinearPipelineError(
                "Python QG failed after ADR-008 correction paths"
            )

        phase = "llm_qg"
        started_at = time.monotonic()
        llm_qg = _run_llm_qg(
            plan=plan,
            plan_content=plan_content,
            module_dir=module_dir,
            writer=writer,
        )
        linear_pipeline.write_json(module_dir / "llm_qg.json", llm_qg)
        aggregate = llm_qg["aggregate"]
        emit_event(
            "review_score",
            level=level,
            slug=slug,
            score=aggregate["min_score"],
            verdict=aggregate["verdict"],
        )
        _phase_done(phase, started_at, level=level, slug=slug)
        if aggregate["verdict"] != "PASS":
            raise linear_pipeline.LinearPipelineError(
                f"LLM QG verdict was {aggregate['verdict']}"
            )

        phase = "mdx"
        started_at = time.monotonic()
        mdx_path = module_dir / f"{slug}.mdx"
        linear_pipeline.assemble_mdx(module_dir, mdx_path, plan_path)
        _phase_done(phase, started_at, level=level, slug=slug, output=mdx_path)

        emit_event(
            "module_done",
            level=level,
            slug=slug,
            duration_s=round(time.monotonic() - module_started_at, 3),
        )
        return 0
    except Exception as exc:
        emit_event(
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
