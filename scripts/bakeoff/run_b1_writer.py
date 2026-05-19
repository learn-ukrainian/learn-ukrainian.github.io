#!/usr/bin/env python3
"""Writer-only B1 bakeoff runner — invokes ONE V7 writer-tools adapter
against a single B1 module and saves the raw output.

Mirrors v7_build.py's writer-phase code path (load plan → build knowledge
packet → build wiki manifest → seed implementation map → render writer
prompt → invoke_writer), but stops after the writer phase. No reviewer,
no audit gates, no fix loop. Output is the raw writer response.

This is the bakeoff methodology used by the 2026-05-19 multi-agent
routing audit at audit/2026-05-19-multi-agent-routing-assessment/REPORT.html
— same shape, but for B1 modules with the production writer-tools
adapters (claude-tools, codex-tools, gemini-tools, deepseek-tools,
qwen-tools).

Usage:
    .venv/bin/python scripts/bakeoff/run_b1_writer.py \
        --level b1 \
        --slug genitive-nuances \
        --writer claude-tools \
        --out audit/2026-05-19-b1-writer-bakeoff/claude-tools

Output files (under --out):
    writer_prompt.md            — rendered prompt (60K+ tokens) for reproducibility
    knowledge_packet.md         — textbook chunks the prompt embedded
    wiki_manifest.json          — manifest the prompt embedded
    implementation_map.json     — seeded contract
    writer_output.md            — RAW writer response (the bakeoff artifact)
    writer_tool_calls.json      — tool-call telemetry
    summary.json                — duration, bytes, writer label, model
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Ensure scripts/ is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import (
    seed_implementation_map,
    write_implementation_map,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", required=True, help="e.g. b1, a1")
    parser.add_argument("--slug", required=True, help="module slug")
    parser.add_argument(
        "--writer",
        required=True,
        choices=linear_pipeline.WRITER_CHOICES,
        help="V7 writer-tools label",
    )
    parser.add_argument(
        "--out", required=True, type=Path, help="output directory"
    )
    parser.add_argument(
        "--writer-timeout",
        type=int,
        default=1800,
        help="stdout silence timeout for the writer subprocess",
    )
    parser.add_argument(
        "--effort",
        choices=("low", "medium", "high", "xhigh", "max"),
        default=None,
        help=(
            "Override reasoning effort for the writer. Defaults to "
            "WRITER_DEFAULTS[writer]['effort'] when unset. Used by the bakeoff "
            "to probe whether silent-failure writers (e.g. codex-tools at B1) "
            "recover at higher reasoning budgets."
        ),
    )
    args = parser.parse_args()

    level = args.level.lower()
    slug = args.slug
    writer = args.writer
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    started_at = time.monotonic()
    print(f"[bakeoff] level={level} slug={slug} writer={writer} out={out_dir}")

    # 1. Plan
    plan_path = linear_pipeline.plan_path_for(level, slug)
    plan_content = plan_path.read_text(encoding="utf-8")
    plan = linear_pipeline.load_plan(plan_path)
    linear_pipeline.validate_plan(plan)

    # 2. Knowledge packet
    knowledge_packet = linear_pipeline.build_knowledge_packet(
        level=level, slug=slug, plan=plan
    )
    (out_dir / "knowledge_packet.md").write_text(knowledge_packet, encoding="utf-8")

    # 3. Wiki manifest
    wiki_manifest_data = linear_pipeline.build_wiki_manifest_data(
        level=level, slug=slug, plan=plan
    )
    wiki_manifest = json.dumps(wiki_manifest_data, ensure_ascii=False, indent=2)
    (out_dir / "wiki_manifest.json").write_text(wiki_manifest, encoding="utf-8")

    # 4. Seed implementation map
    impl_map = seed_implementation_map(wiki_manifest_data, plan=plan)
    write_implementation_map(impl_map, out_dir / "implementation_map.json")

    # 5. Render prompt
    prompt = linear_pipeline.render_writer_prompt(
        plan=plan,
        plan_content=plan_content,
        knowledge_packet=knowledge_packet,
        wiki_manifest=wiki_manifest,
        implementation_map=impl_map,
        writer=writer,
    )
    (out_dir / "writer_prompt.md").write_text(prompt, encoding="utf-8")
    prompt_chars = len(prompt)

    # 6. Pick cwd (matches v7_build.py:748 — gemini-tools needs PROJECT_ROOT)
    writer_cwd = PROJECT_ROOT if writer == "gemini-tools" else out_dir

    # 7. Resolve effort (CLI override falls back to writer default)
    resolved_effort = args.effort or linear_pipeline.WRITER_DEFAULTS[writer]["effort"]

    # 8. Invoke writer
    print(
        f"[bakeoff] invoking writer ({prompt_chars} prompt chars, "
        f"effort={resolved_effort})..."
    )
    invoke_started = time.monotonic()
    writer_output = linear_pipeline.invoke_writer(
        prompt,
        writer,
        cwd=writer_cwd,
        tool_trace_path=out_dir / "writer_tool_calls.json",
        stdout_silence_timeout=args.writer_timeout,
        effort=args.effort,
    )
    invoke_duration = time.monotonic() - invoke_started

    (out_dir / "writer_output.md").write_text(writer_output, encoding="utf-8")
    output_chars = len(writer_output)

    total_duration = time.monotonic() - started_at
    summary = {
        "level": level,
        "slug": slug,
        "writer": writer,
        "model": linear_pipeline.WRITER_DEFAULTS[writer]["model"],
        "effort": resolved_effort,
        "effort_overridden": args.effort is not None,
        "prompt_chars": prompt_chars,
        "output_chars": output_chars,
        "invoke_duration_s": round(invoke_duration, 2),
        "total_duration_s": round(total_duration, 2),
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"[bakeoff] done: {output_chars} output chars in {invoke_duration:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
