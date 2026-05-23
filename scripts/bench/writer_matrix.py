#!/usr/bin/env python3
"""V7 writer-bench v0 — 6 writers × 5 modules sequential bench.

Runs the V7 build pipeline for each (writer, module) cell in sequence
and produces a per-cell JSON record + an HTML grid report. Intended as
an overnight measurement of writer prompt-adherence variance across
writer backends, judged by the deterministic ``python_qg`` gates plus
the writer trace.

Design lock per ``docs/session-state/2026-05-22-writer-bench-design-locked-...``:

- Sequential, NOT fanout — the ``sources`` MCP server (port 8766)
  doesn't currently support concurrent writer clients (see #M-9 +
  the handoff §2.4 rationale).
- N=1 per cell. No variance measurement in v0. Promote to N=3 only
  on cells too close to call.
- Each writer runs at its V7 default effort (production behavior,
  not theoretical ceiling). Override via ``--writer-effort
  writer=high,writer=xhigh`` if needed.
- Outer loop modules, inner loop writers — so a flaky writer poisons
  fewer cells than if all 6 writers hit the same module first.

Quality is judged downstream of this script: a cell that reaches
``python_qg`` with all gates green is a candidate ANCHOR; the bench
log records the per-gate pass/fail breakdown for cross-writer
comparison. The bench script itself does not promote or judge — it
runs the pipeline and captures observable state.

Usage::

    # Default 6×5 overnight bench (~5-7.5 h wall-clock at ~10-15 min/cell):
    .venv/bin/python scripts/bench/writer_matrix.py --out-dir audit/writer-bench-2026-05-22

    # Smaller smoke (1 writer × 1 module):
    .venv/bin/python scripts/bench/writer_matrix.py \\
        --writers codex-tools --modules a1/my-morning \\
        --out-dir audit/writer-bench-smoke

    # Resume an interrupted run (skips cells already in cells.jsonl):
    .venv/bin/python scripts/bench/writer_matrix.py --out-dir audit/writer-bench-2026-05-22 --resume
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html as _html
import json
import subprocess
import sys
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = PROJECT_ROOT / ".venv/bin/python"
V7_BUILD = PROJECT_ROOT / "scripts/build/v7_build.py"

# Locked matrix per 2026-05-22 handoff §2.3 + Section 9 user direction:
# "sonnet 4.6 high for claude, gemini 3.1.pro high, gpt-5.5 xhigh,
#  deepseek v4 pro, qwen 3.6 plus, agy gemini 3.5-flash high"
DEFAULT_WRITERS: tuple[str, ...] = (
    "claude-tools",
    "gemini-tools",
    "codex-tools",
    "deepseek-tools",
    "qwen-tools",
    "agy-tools",
)

# Five A1 modules covering letter / grammar / milestone / functional.
# (Handoff §2.3 said "A2/checkpoint-first-contact" and "A2/at-the-cafe"
# but those slugs only exist under plans/a1/ — bench v0 uses the
# confirmed-existing A1 plans.)
DEFAULT_MODULES: tuple[str, ...] = (
    "a1/sounds-letters-and-hello",
    "a1/things-have-gender",
    "a1/my-morning",
    "a1/checkpoint-first-contact",
    "a1/at-the-cafe",
)

# Optional per-writer effort overrides (handoff §2.3). gemini-tools and
# claude-tools default to the V7 baseline (high / xhigh respectively);
# codex-tools default is "high" per scripts/build/linear_pipeline.py
# WRITER_DEFAULTS — bench bumps to xhigh per the locked matrix.
DEFAULT_EFFORT_OVERRIDES: dict[str, str] = {
    "codex-tools": "xhigh",
}

# Phase progression — used to compute ``phase_reached`` per cell.
PHASE_ORDER: tuple[str, ...] = (
    "knowledge_packet",
    "writer",
    "writer_trace_isolation",
    "python_qg",
    "wiki_coverage_gate",
    "wiki_coverage_review",
    "llm_qg",
    "mdx_assemble",
)


@dataclass
class BenchCell:
    """One (writer, module) bench-result record."""

    writer: str
    level: str
    slug: str
    effort: str | None
    started_at: str
    wall_clock_s: float
    exit_code: int
    phase_reached: str
    writer_passed: bool
    python_qg_passed: bool | None
    gates_passed: list[str] = field(default_factory=list)
    gates_failed: list[str] = field(default_factory=list)
    gates_pending: list[str] = field(default_factory=list)
    failure_class: str | None = None
    failure_detail: dict[str, Any] = field(default_factory=dict)
    writer_tool_call_count: int = 0
    writer_non_sources_tool_calls: int = 0
    worktree_path: str | None = None
    notes: str | None = None


def _module_dir(worktree: Path, level: str, slug: str) -> Path:
    return worktree / "curriculum" / "l2-uk-en" / level / slug


def _parse_phase_reached(worktree: Path, level: str, slug: str, exit_code: int) -> str:
    """Determine the furthest pipeline phase reached for this cell.

    Walks the artifact set in reverse: latest known artifact wins.
    A successful build produces (in order) writer_prompt.md →
    knowledge_packet.md → writer_output.raw.md → activities.yaml + module.md
    → python_qg.json → wiki_manifest.json → assembled mdx.
    """
    mod = _module_dir(worktree, level, slug)
    if not mod.exists():
        return "setup"
    if (mod / "python_qg.json").exists():
        if exit_code == 0:
            return "module_done"
        return "python_qg"
    if (mod / "module.md").exists() and (mod / "writer_output.raw.md").exists():
        return "writer"
    if (mod / "knowledge_packet.md").exists():
        return "knowledge_packet"
    return "setup"


def _load_python_qg(worktree: Path, level: str, slug: str) -> dict[str, Any] | None:
    p = _module_dir(worktree, level, slug) / "python_qg.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _classify_gates(qg: dict[str, Any] | None) -> tuple[list[str], list[str], list[str]]:
    """Return (passed, failed, pending) gate names from a python_qg.json."""
    if not qg or not isinstance(qg, dict):
        return [], [], []
    gates = qg.get("gates", {})
    if not isinstance(gates, dict):
        return [], [], []
    passed, failed, pending = [], [], []
    for name, gate in gates.items():
        if not isinstance(gate, dict):
            (passed if gate else failed).append(name)
            continue
        verdict = gate.get("passed")
        if verdict is True:
            passed.append(name)
        elif verdict is False:
            failed.append(name)
        else:
            pending.append(name)
    return sorted(passed), sorted(failed), sorted(pending)


def _count_writer_tool_calls(worktree: Path, level: str, slug: str) -> tuple[int, int]:
    """Return (total_calls, non_sources_calls) from writer_tool_calls.json."""
    p = _module_dir(worktree, level, slug) / "writer_tool_calls.json"
    if not p.exists():
        return 0, 0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0, 0
    if not isinstance(data, list):
        return 0, 0
    total = len(data)
    non_sources = sum(
        1
        for c in data
        if isinstance(c, dict) and not str(c.get("name", "")).startswith(("mcp__sources__", "mcp_sources_"))
    )
    return total, non_sources


def _run_one_cell(
    writer: str,
    level: str,
    slug: str,
    effort: str | None,
    out_dir: Path,
) -> BenchCell:
    started = _dt.datetime.now(_dt.UTC).isoformat()
    cell_log = out_dir / "cell-logs" / f"{writer}__{level}__{slug.replace('/', '_')}.log"
    cell_log.parent.mkdir(parents=True, exist_ok=True)
    argv = [
        str(PYTHON),
        str(V7_BUILD),
        level,
        slug,
        "--writer",
        writer,
        "--worktree",
    ]
    if effort:
        argv.extend(["--effort", effort])

    t0 = time.monotonic()
    worktree_path: str | None = None
    with cell_log.open("w", encoding="utf-8") as logf:
        proc = subprocess.run(
            argv,
            cwd=PROJECT_ROOT,
            stdout=logf,
            stderr=subprocess.STDOUT,
            check=False,
        )
    duration = time.monotonic() - t0

    # The build prints BUILD_WORKTREE=<path> as its final summary; scrape it.
    try:
        for line in cell_log.read_text(encoding="utf-8").splitlines():
            if line.startswith("BUILD_WORKTREE="):
                worktree_path = line.split("=", 1)[1].strip()
    except OSError:
        pass
    worktree = Path(worktree_path) if worktree_path else PROJECT_ROOT

    phase = _parse_phase_reached(worktree, level, slug, proc.returncode)
    qg = _load_python_qg(worktree, level, slug)
    passed, failed, pending = _classify_gates(qg)
    total_calls, non_sources = _count_writer_tool_calls(worktree, level, slug)

    writer_passed = phase in {"python_qg", "module_done"} or (phase == "writer" and proc.returncode == 0)
    python_qg_passed: bool | None
    if qg is None:
        python_qg_passed = None
    else:
        # Top-level "passed" boolean is set on a clean QG sweep (all
        # mandatory gates green + no terminal advisories).
        top = qg.get("gates", {}).get("passed")
        python_qg_passed = top if isinstance(top, bool) else (len(failed) == 0 and len(passed) > 0)

    failure_class: str | None = None
    failure_detail: dict[str, Any] = {}
    if proc.returncode != 0:
        if phase in {"setup", "knowledge_packet"}:
            failure_class = "infra"
        elif phase == "writer":
            failure_class = "writer_crash_or_trace"
        elif phase == "python_qg":
            failure_class = "python_qg_fail"
            failure_detail = {name: qg["gates"].get(name) for name in failed} if qg else {}
        else:
            failure_class = f"{phase}_fail"

    return BenchCell(
        writer=writer,
        level=level,
        slug=slug,
        effort=effort,
        started_at=started,
        wall_clock_s=round(duration, 2),
        exit_code=proc.returncode,
        phase_reached=phase,
        writer_passed=writer_passed,
        python_qg_passed=python_qg_passed,
        gates_passed=passed,
        gates_failed=failed,
        gates_pending=pending,
        failure_class=failure_class,
        failure_detail=failure_detail,
        writer_tool_call_count=total_calls,
        writer_non_sources_tool_calls=non_sources,
        worktree_path=worktree_path,
    )


def _render_html_report(cells: list[BenchCell], out_path: Path) -> None:
    """Render a writers × modules grid HTML report."""
    writers = sorted({c.writer for c in cells})
    modules = sorted({f"{c.level}/{c.slug}" for c in cells})
    by_cell = {(c.writer, f"{c.level}/{c.slug}"): c for c in cells}

    def _cell_html(c: BenchCell | None) -> str:
        if c is None:
            return '<td class="empty">—</td>'
        n_gates = len(c.gates_passed) + len(c.gates_failed)
        score = f"{len(c.gates_passed)}/{n_gates}" if n_gates else "n/a"
        klass = "fail"
        if c.python_qg_passed is True:
            klass = "pass"
        elif c.python_qg_passed is False and len(c.gates_passed) > 0.7 * max(1, n_gates):
            klass = "warn"
        return (
            f'<td class="{klass}" title="{_html.escape(c.failure_class or "")}">'
            f"{score}<br/><small>{_html.escape(c.phase_reached)} · {c.wall_clock_s:.0f}s</small></td>"
        )

    rows: list[str] = []
    for w in writers:
        cells_for_writer = [by_cell.get((w, m)) for m in modules]
        tds = " ".join(_cell_html(c) for c in cells_for_writer)
        rows.append(f"<tr><th>{_html.escape(w)}</th>{tds}</tr>")
    head_cols = " ".join(f"<th>{_html.escape(m)}</th>" for m in modules)
    body = "\n".join(rows)
    out_path.write_text(
        f"""<!doctype html>
<html><head><meta charset="utf-8"><title>V7 writer-bench v0</title>
<style>
  body{{font:14px/1.4 system-ui,Arial,sans-serif;padding:24px;color:#222}}
  table{{border-collapse:collapse;margin-top:16px}}
  th,td{{border:1px solid #ccc;padding:8px 12px;text-align:center}}
  th{{background:#f7f7f7;font-weight:600}}
  td.pass{{background:#dcefdc}}
  td.warn{{background:#fff5d6}}
  td.fail{{background:#fadbd6}}
  td.empty{{color:#999}}
  small{{color:#555}}
</style>
</head><body>
<h1>V7 writer-bench v0</h1>
<p>{len(cells)} cells · {len(writers)} writers × {len(modules)} modules · sequential N=1</p>
<table><tr><th>writer ╲ module</th>{head_cols}</tr>
{body}
</table>
</body></html>
""",
        encoding="utf-8",
    )


def _load_existing_cells(jsonl_path: Path) -> list[BenchCell]:
    if not jsonl_path.exists():
        return []
    out: list[BenchCell] = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            out.append(BenchCell(**payload))
        except TypeError:
            continue
    return out


def _append_cell(jsonl_path: Path, cell: BenchCell) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(cell), ensure_ascii=False) + "\n")


def _resolve_effort_overrides(spec: Iterable[str] | None) -> dict[str, str]:
    overrides = dict(DEFAULT_EFFORT_OVERRIDES)
    if not spec:
        return overrides
    for entry in spec:
        if "=" not in entry:
            continue
        writer, effort = entry.split("=", 1)
        overrides[writer.strip()] = effort.strip()
    return overrides


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--writers",
        default=",".join(DEFAULT_WRITERS),
        help="Comma-separated writer list (default: locked matrix)",
    )
    p.add_argument(
        "--modules",
        default=",".join(DEFAULT_MODULES),
        help="Comma-separated level/slug list (default: 5 A1 modules)",
    )
    p.add_argument(
        "--writer-effort",
        action="append",
        default=[],
        metavar="WRITER=EFFORT",
        help="Per-writer effort override (e.g. --writer-effort codex-tools=xhigh). Default: codex-tools=xhigh.",
    )
    p.add_argument(
        "--out-dir",
        required=True,
        help="Output directory; cells.jsonl, report.html, cell-logs/ land here.",
    )
    p.add_argument(
        "--resume",
        action="store_true",
        help="Skip cells already present in cells.jsonl.",
    )
    p.add_argument(
        "--max-cells",
        type=int,
        default=None,
        help="Run at most N cells (cap for smoke tests).",
    )
    args = p.parse_args(argv)

    writers = [w.strip() for w in args.writers.split(",") if w.strip()]
    modules = [m.strip() for m in args.modules.split(",") if m.strip()]
    overrides = _resolve_effort_overrides(args.writer_effort)

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cells_path = out_dir / "cells.jsonl"
    report_path = out_dir / "report.html"

    cells: list[BenchCell] = []
    done_keys: set[tuple[str, str]] = set()
    if args.resume:
        cells = _load_existing_cells(cells_path)
        done_keys = {(c.writer, f"{c.level}/{c.slug}") for c in cells}
        print(f"Resuming with {len(cells)} cells already recorded.", file=sys.stderr)

    queue: list[tuple[str, str]] = []
    # Outer loop modules, inner loop writers (handoff §2.4).
    for mod in modules:
        for writer in writers:
            if (writer, mod) in done_keys:
                continue
            queue.append((writer, mod))
    if args.max_cells is not None:
        queue = queue[: args.max_cells]

    print(
        f"Bench plan: {len(queue)} cells queued ({len(writers)} writers × {len(modules)} modules) "
        f"out of {len(writers) * len(modules)} matrix slots.",
        file=sys.stderr,
    )

    for idx, (writer, mod) in enumerate(queue, start=1):
        level, slug = mod.split("/", 1)
        effort = overrides.get(writer)
        print(
            f"[{idx}/{len(queue)}] {writer} → {mod}" + (f" (effort={effort})" if effort else ""),
            file=sys.stderr,
        )
        cell = _run_one_cell(writer=writer, level=level, slug=slug, effort=effort, out_dir=out_dir)
        cells.append(cell)
        _append_cell(cells_path, cell)
        print(
            f"  → phase={cell.phase_reached} exit={cell.exit_code} "
            f"wall={cell.wall_clock_s:.1f}s gates_passed={len(cell.gates_passed)} "
            f"gates_failed={len(cell.gates_failed)}",
            file=sys.stderr,
        )
        # Render the report incrementally so a partial bench is still
        # browsable while the next cell runs.
        _render_html_report(cells, report_path)

    print(
        f"Bench complete. {len(cells)} cells recorded at {cells_path}, report at {report_path}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
