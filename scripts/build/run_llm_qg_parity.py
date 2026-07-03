#!/usr/bin/env python3
"""Standalone LLM-QG parity runner.

Re-runs the V7 per-dimension LLM review on an already-built module and persists
``llm_qg.json`` plus the SQLite LLM-QG store, with a reviewer override.
Replicates ``v7_build._run_llm_qg``
(the handoff-prescribed mechanism) so folk modules that shipped python_qg-green
*without* an ``llm_qg.json`` can reach e2e-proper parity with kalendarna.

Reviewer defaults to ``codex-tools`` because gemini-family reviewers are
folk-culture-barred (±5 noise on dense UA prose; fleet policy #M0 / Session-1).
Writer defaults to ``claude-tools`` (the folk module writer) only to satisfy the
no-self-review assertion in ``_run_llm_qg`` — no writing happens here.

Usage:
    .venv/bin/python scripts/build/run_llm_qg_parity.py folk koliadky-shchedrivky
    .venv/bin/python scripts/build/run_llm_qg_parity.py folk <slug> --reviewer codex-tools

The shared QG runner resumes dimensions whose prompt/raw-response artifacts
already parse cleanly, and retries a dimension when the backend returns an empty
or malformed response.

Outputs ``<module_dir>/llm_qg.json``, persists the current DB record, and prints
the aggregate verdict line. Exit code 0 on success, 1 on missing plan/module.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build import linear_pipeline, v7_build


def run_parity(level: str, slug: str, *, writer: str, reviewer: str, out: str | None) -> int:
    plan_path = linear_pipeline.plan_path_for(level, slug)
    if not plan_path.exists():
        print(f"ERROR: no plan at {plan_path}", file=sys.stderr)
        return 1
    plan_content = plan_path.read_text(encoding="utf-8")
    plan = linear_pipeline.load_plan(plan_path)
    linear_pipeline.validate_plan(plan)
    profile = linear_pipeline.curriculum_profile_for_level(level)
    module_dir = v7_build._resolve_output_dir(out, level, slug)
    if not (module_dir / "module.md").exists():
        print(f"ERROR: no module.md at {module_dir}", file=sys.stderr)
        return 1

    print(
        f"[parity] {level}/{slug} reviewer={reviewer} writer={writer} "
        f"dims={list(v7_build.QG_DIMS)}",
        flush=True,
    )
    started = time.monotonic()
    llm_qg = v7_build._run_llm_qg(
        plan=plan,
        plan_content=plan_content,
        module_dir=module_dir,
        writer=writer,
        reviewer_override=reviewer,
        profile=profile,
    )
    linear_pipeline.write_json(module_dir / "llm_qg.json", llm_qg)
    v7_build._persist_llm_qg_result(
        level=level,
        slug=slug,
        module_dir=module_dir,
        llm_qg=llm_qg,
        reviewer=v7_build._reviewer_for_writer(writer, reviewer),
        source="run_llm_qg_parity",
    )
    agg = llm_qg["aggregate"]
    print(
        f"[parity] DONE {slug} in {round(time.monotonic() - started)}s :: "
        f"verdict={agg.get('verdict')} terminal_verdict={agg.get('terminal_verdict')} "
        f"min_score={agg.get('min_score')} min_dim={agg.get('min_dim')} "
        f"failing={agg.get('failing_dims')} rejected={agg.get('rejected_dims')}",
        flush=True,
    )
    print(f"LLM_QG_JSON_WRITTEN {module_dir / 'llm_qg.json'}", flush=True)
    print("LLM_QG_DB_PERSISTED true", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Re-run V7 LLM QG on a built module and write llm_qg.json (reviewer override).",
    )
    ap.add_argument("level", help="Curriculum level/track, e.g. folk.")
    ap.add_argument("slug", help="Module slug under curriculum/l2-uk-en/<level>/<slug>.")
    ap.add_argument("--writer", default="claude-tools", help="Writer-of-record (no-self-review guard).")
    ap.add_argument("--reviewer", default="codex-tools", help="Reviewer backend (default codex-tools).")
    ap.add_argument("--out", default=None, help="Module dir override; default curriculum/l2-uk-en/<level>/<slug>.")
    args = ap.parse_args(argv)
    return run_parity(
        args.level.lower(), args.slug, writer=args.writer, reviewer=args.reviewer, out=args.out
    )


if __name__ == "__main__":
    raise SystemExit(main())
