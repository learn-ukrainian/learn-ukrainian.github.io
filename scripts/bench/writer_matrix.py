"""V7 writer-bench v0 — sequential 6 writers × 5 modules matrix.

Locked design: docs/session-state/2026-05-22-writer-bench-design-locked-after-multi-writer-failures.md §2.

Execution policy:
- Sequential, NO fanout. The MCP `sources` server at port 8766 doesn't
  support concurrent writer clients today (Python-wrapper serialization,
  not a SQLite FTS5 limit). Per MEMORY #M-9 anyway (laptop crash
  protection for local subprocess fanout).
- Outer loop = modules, inner loop = writers. A flaky writer poisoning
  ALL of one writer's later cells (retry cooldown) hurts less than
  ALL 6 writers' first cell being on the same poisonous module.
- Per-cell support budget: 30 min subprocess timeout. If a writer
  can't reach `python_qg` within the window, record the phase reached
  and move on. Don't sink hours per writer in v0.
- N=1 single-shot per cell. No variance measurement.
- Effort: each writer's V7 default (no override) — bench measures
  production behavior, not theoretical ceiling.

Deviation from locked design: PR #2221 §2.3 specifies the Claude cell
should use `claude-sonnet-4-6` (vs the default `claude-opus-4-7`). The
current v7_build.py CLI has no `--model` flag — model comes from
`WRITER_DEFAULTS`. v0 ships with the defaults; per-cell model override
is filed as a follow-up. This is noted in the per-cell record's
`model` field so the eventual reader can see what actually ran.

Per-cell record schema (mirrors PR #2221 §2.5):
- writer: str
- model: str
- effort: str
- level: str
- slug: str
- wall_clock_s: float
- phase_reached: str    # "plan" | "knowledge_packet" | "writer" | "python_qg" | "wiki_coverage_gate" | "module_done" | "<crash>"
- writer_passed: bool
- python_qg_passed: bool
- gates_passed: list[str]
- gates_failed: list[str]
- failure_class: str    # "ok" | "writer_unparseable" | "writer_trace_isolation_fail" | "python_qg_fail" | "timeout" | "subprocess_fail"
- failure_detail: dict[str, Any]
- artifact_dir: str | None
- telemetry_path: str | None

Outputs to `audit/writer-bench-v0/<YYYYMMDD-HHMMSS>/`:
- matrix.json — full per-cell records
- report.html — pivoted rows=writers × cols=modules grid with drill-down

Usage:
    .venv/bin/python -m scripts.bench.writer_matrix             # fire the full 6×5
    .venv/bin/python -m scripts.bench.writer_matrix --dry-run   # print the plan
    .venv/bin/python -m scripts.bench.writer_matrix --writers codex-tools,gemini-tools  # subset
    .venv/bin/python -m scripts.bench.writer_matrix --modules a1/my-morning             # subset

Issue: writer-bench-v0 (per PR #2221).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Canonical writer → (model, effort) matrix. Pinned in the bench so a
# silent change to `scripts/build/linear_pipeline.py::WRITER_DEFAULTS`
# can't quietly change what got measured. If you intentionally change
# defaults upstream, mirror the change here in a separate commit so the
# bench history makes the intent legible.
WRITER_DEFAULTS: dict[str, dict[str, str]] = {
    "claude-tools":   {"model": "claude-opus-4-7",       "effort": "xhigh"},
    "gemini-tools":   {"model": "gemini-3.1-pro-preview","effort": "high"},
    "codex-tools":    {"model": "gpt-5.5",               "effort": "high"},
    "deepseek-tools": {"model": "deepseek-v4-pro",       "effort": "medium"},
    "qwen-tools":     {"model": "qwen/qwen3.6-plus",     "effort": "medium"},
    "agy-tools":      {"model": "gemini-3.5-flash-high", "effort": "medium"},
}

# ---------------------------------------------------------------------
# Matrix
# ---------------------------------------------------------------------

# 6 writers — one per agent family. Effort defaults to V7-default per
# the locked policy ("bench measures production behavior, not
# theoretical ceiling").  WRITER_DEFAULTS lookup happens per-cell so the
# bench reports whatever v7_build.py would actually run.
WRITERS: tuple[str, ...] = (
    "claude-tools",
    "gemini-tools",
    "codex-tools",
    "deepseek-tools",
    "qwen-tools",
    "agy-tools",
)

# 5 modules — A1 letter / grammar / milestone + A2 entry / functional.
# Module order is irrelevant for results but affects wall-clock
# scheduling (outer loop). Worst-case first means later writers retry
# against an already-warm MCP server cache.
MODULES: tuple[tuple[str, str], ...] = (
    ("a1", "sounds-letters-and-hello"),
    ("a1", "things-have-gender"),
    ("a1", "my-morning"),
    ("a2", "checkpoint-first-contact"),
    ("a2", "at-the-cafe"),
)

# Per-cell budget — kill the subprocess if v7_build.py doesn't return
# within 30 minutes (1800 s).  Per PR #2221 §2.4 support-budget
# directive.  The subprocess itself also has its own --writer-timeout
# (silence timeout) which fires earlier on stalled writers.
PER_CELL_TIMEOUT_S: int = 1800

# Phase ordering — match `v7_build.py::_run` for parse_telemetry().
# `module_done` only emits when the full pipeline (including llm_qg)
# completes.  For v0, we treat python_qg as the bench-pass predicate.
PHASE_ORDER: tuple[str, ...] = (
    "plan",
    "knowledge_packet",
    "writer",
    "python_qg",
    "wiki_coverage_gate",
    "wiki_coverage_review",
    "llm_qg",
    "module_done",
)


# ---------------------------------------------------------------------
# Cell record
# ---------------------------------------------------------------------


@dataclass
class CellRecord:
    """Result of one writer × module bench cell."""

    writer: str
    model: str
    effort: str
    level: str
    slug: str
    wall_clock_s: float = 0.0
    phase_reached: str = "<start>"
    writer_passed: bool = False
    python_qg_passed: bool = False
    gates_passed: list[str] = field(default_factory=list)
    gates_failed: list[str] = field(default_factory=list)
    failure_class: str = "<unstarted>"
    failure_detail: dict[str, Any] = field(default_factory=dict)
    artifact_dir: str | None = None
    telemetry_path: str | None = None
    exit_code: int | None = None


# ---------------------------------------------------------------------
# Per-cell execution
# ---------------------------------------------------------------------


def _resolve_writer_defaults(writer: str) -> tuple[str, str]:
    """Return ``(model, effort)`` for ``writer`` from the pinned matrix."""
    defaults = WRITER_DEFAULTS.get(writer)
    if defaults is None:
        raise ValueError(f"Unknown writer: {writer!r}")
    return defaults["model"], defaults["effort"]


def _build_command(
    *,
    writer: str,
    level: str,
    slug: str,
    telemetry_out: Path,
    extra_args: list[str] | None = None,
) -> list[str]:
    """Build the v7_build.py invocation for one bench cell.

    Always passes ``--worktree`` so the build runs in an isolated
    `.worktrees/builds/...` and main stays clean (per #M-10 +
    `delegate-must-use-worktree.md`).  The telemetry JSONL stream is
    redirected to ``telemetry_out`` so the bench parser doesn't have
    to share stdout with subprocess noise.
    """
    cmd = [
        str(_REPO_ROOT / ".venv" / "bin" / "python"),
        "-u",
        str(_REPO_ROOT / "scripts" / "build" / "v7_build.py"),
        level,
        slug,
        "--writer",
        writer,
        "--worktree",
        "--telemetry-out",
        str(telemetry_out),
    ]
    if extra_args:
        cmd.extend(extra_args)
    return cmd


_WORKTREE_LINE_RE = ("BUILD_WORKTREE=", "build worktree:")


def _extract_build_worktree(log_path: Path) -> Path | None:
    """Find the build's worktree path from the subprocess log.

    v7_build.py prints ``BUILD_WORKTREE=<path>`` near the end of every
    run (success or failure) via ``_print_worktree_summary``.  Parsing
    that line lets us locate ``python_qg.json`` even when the
    subprocess exits non-zero.
    """
    if not log_path.exists():
        return None
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        line = line.strip()
        for prefix in _WORKTREE_LINE_RE:
            if line.startswith(prefix):
                candidate = Path(line[len(prefix):].strip())
                if candidate.exists():
                    return candidate
    return None


def _parse_telemetry(
    telemetry_path: Path,
    *,
    log_path: Path | None = None,
    level: str = "",
    slug: str = "",
) -> dict[str, Any]:
    """Parse JSONL events emitted by v7_build.py for one cell.

    Returns:
    - phase_reached: highest phase that emitted phase_done before any failure
    - writer_passed: phase_done emitted for `writer` AND no
      writer_runtime_gate_failed / writer_trace_isolation_failed event seen
    - python_qg_passed: parsed from ``<worktree>/curriculum/l2-uk-en/<level>/<slug>/python_qg.json``
      (gates.passed). v7_build.py's ``phase_done(python_qg)`` event itself does
      NOT carry the gates list — the artifact JSON does (see v7_build.py:1220).
    - gates_passed / gates_failed: per-gate passed flags from python_qg.json
    - failure_class: one of the documented classes
    - failure_detail: free-form dict
    - module_dir: resolved build worktree's module dir, if found
    """
    state: dict[str, Any] = {
        "phase_reached": "<start>",
        "writer_passed": False,
        "python_qg_passed": False,
        "gates_passed": [],
        "gates_failed": [],
        "failure_class": "<unparsed>",
        "failure_detail": {},
        "module_dir": None,
    }

    saw_writer_phase_done = False
    saw_python_qg_phase_done = False

    if telemetry_path.exists():
        for raw in telemetry_path.read_text(encoding="utf-8", errors="replace").splitlines():
            raw = raw.strip()
            if not raw or not raw.startswith("{"):
                continue
            try:
                evt = json.loads(raw)
            except json.JSONDecodeError:
                continue

            name = evt.get("event")
            if name == "phase_done":
                phase = evt.get("phase")
                if phase in PHASE_ORDER:
                    cur_rank = (
                        PHASE_ORDER.index(state["phase_reached"])
                        if state["phase_reached"] in PHASE_ORDER
                        else -1
                    )
                    new_rank = PHASE_ORDER.index(phase)
                    if new_rank > cur_rank:
                        state["phase_reached"] = phase
                if phase == "writer":
                    saw_writer_phase_done = True
                elif phase == "python_qg":
                    saw_python_qg_phase_done = True

            elif name in {
                "writer_runtime_gate_failed",
                "writer_trace_isolation_failed",
            }:
                state["failure_class"] = "writer_trace_isolation_fail"
                state["failure_detail"] = {
                    "gate": evt.get("gate"),
                    "sub_class": evt.get("sub_class"),
                    "evidence": evt.get("evidence"),
                }

            elif name == "module_done":
                state["phase_reached"] = "module_done"
    else:
        state["failure_class"] = "no_telemetry"
        state["failure_detail"] = {"reason": "telemetry file missing"}

    # Resolve module_dir from the subprocess log so we can read
    # python_qg.json even when the build exited non-zero.
    if log_path is not None and level and slug:
        worktree = _extract_build_worktree(log_path)
        if worktree is not None:
            module_dir = worktree / "curriculum" / "l2-uk-en" / level / slug
            if module_dir.exists():
                state["module_dir"] = str(module_dir)
                qg_path = module_dir / "python_qg.json"
                if qg_path.exists():
                    try:
                        qg = json.loads(qg_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        qg = None
                    if isinstance(qg, dict):
                        gates_block = qg.get("gates") or {}
                        if isinstance(gates_block, dict):
                            state["python_qg_passed"] = bool(gates_block.get("passed", False))
                            results = gates_block.get("results") or {}
                            if isinstance(results, dict):
                                for gate_name, gate_data in results.items():
                                    passed = (
                                        isinstance(gate_data, dict)
                                        and bool(gate_data.get("passed", False))
                                    )
                                    if passed:
                                        state["gates_passed"].append(gate_name)
                                    else:
                                        state["gates_failed"].append(gate_name)

    state["writer_passed"] = saw_writer_phase_done and state["failure_class"] not in {
        "writer_trace_isolation_fail",
    }

    # Reclassify only when the parser hasn't already committed to a
    # diagnosis. ``no_telemetry`` stays sticky — we have no signal at
    # all and must not pretend the writer crashed early when really we
    # just couldn't find the JSONL file.
    if state["failure_class"] == "<unparsed>":
        if state["python_qg_passed"]:
            state["failure_class"] = "ok"
        elif saw_python_qg_phase_done and not state["python_qg_passed"]:
            state["failure_class"] = "python_qg_fail"
        elif saw_writer_phase_done:
            state["failure_class"] = "writer_passed_qg_unreached"
        elif state["phase_reached"] in {"<start>", "plan", "knowledge_packet"}:
            state["failure_class"] = "writer_unparseable"

    return state


def run_cell(
    *,
    writer: str,
    level: str,
    slug: str,
    bench_dir: Path,
    timeout_s: int = PER_CELL_TIMEOUT_S,
) -> CellRecord:
    """Run one writer × module bench cell.

    Side effects:
    - Creates a build worktree under `.worktrees/builds/{level}-{slug}-*/`.
    - Writes telemetry JSONL to `bench_dir/cells/{writer}-{level}-{slug}.jsonl`.
    - Writes subprocess stderr+stdout to `bench_dir/cells/{writer}-{level}-{slug}.log`.

    Returns a fully-populated CellRecord even on subprocess failure —
    one bench cell never raises out of v0; the matrix records every
    outcome.
    """
    model, effort = _resolve_writer_defaults(writer)
    cells_dir = bench_dir / "cells"
    cells_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{writer}-{level}-{slug}"
    telemetry_path = cells_dir / f"{stem}.jsonl"
    log_path = cells_dir / f"{stem}.log"

    record = CellRecord(
        writer=writer,
        model=model,
        effort=effort,
        level=level,
        slug=slug,
        telemetry_path=str(telemetry_path),
    )

    cmd = _build_command(
        writer=writer,
        level=level,
        slug=slug,
        telemetry_out=telemetry_path,
    )

    started = time.monotonic()
    try:
        with log_path.open("w", encoding="utf-8") as logf:
            proc = subprocess.run(
                cmd,
                cwd=str(_REPO_ROOT),
                stdout=logf,
                stderr=subprocess.STDOUT,
                timeout=timeout_s,
                check=False,
            )
        record.exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        record.wall_clock_s = round(time.monotonic() - started, 3)
        record.failure_class = "timeout"
        record.failure_detail = {"timeout_s": timeout_s}
        record.exit_code = -1
        # Try to recover whatever telemetry was emitted before the kill.
        parsed = _parse_telemetry(
            telemetry_path,
            log_path=log_path,
            level=level,
            slug=slug,
        )
        record.phase_reached = parsed["phase_reached"]
        record.writer_passed = parsed["writer_passed"]
        return record
    except Exception as exc:  # v0 records every outcome; never raises out of one cell
        record.wall_clock_s = round(time.monotonic() - started, 3)
        record.failure_class = "subprocess_fail"
        record.failure_detail = {"exception": type(exc).__name__, "message": str(exc)}
        record.exit_code = -2
        return record

    record.wall_clock_s = round(time.monotonic() - started, 3)
    parsed = _parse_telemetry(
        telemetry_path,
        log_path=log_path,
        level=level,
        slug=slug,
    )
    record.phase_reached = parsed["phase_reached"]
    record.writer_passed = parsed["writer_passed"]
    record.python_qg_passed = parsed["python_qg_passed"]
    record.gates_passed = parsed["gates_passed"]
    record.gates_failed = parsed["gates_failed"]
    record.failure_class = parsed["failure_class"]
    record.failure_detail = parsed["failure_detail"]
    record.artifact_dir = parsed["module_dir"]
    # Subprocess exit code overrides failure_class for non-zero exits
    # that the JSONL didn't pick up.
    if record.exit_code != 0 and record.failure_class == "ok":
        record.failure_class = "subprocess_fail_post_success"
        record.failure_detail = {"exit_code": record.exit_code}

    return record


# ---------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------


_CELL_COLOR_BY_CLASS = {
    "ok": "#2d6a4f",                              # green
    "python_qg_fail": "#e76f51",                  # orange-red
    "writer_passed_qg_unreached": "#f4a261",      # amber
    "writer_trace_isolation_fail": "#c1121f",     # red
    "writer_unparseable": "#a4133c",              # deep red
    "subprocess_fail": "#590d22",                 # almost black
    "subprocess_fail_post_success": "#9d4edd",    # purple
    "timeout": "#3a0ca3",                         # blue
    "no_telemetry": "#6c757d",                    # gray
    "<unstarted>": "#dee2e6",                     # light gray
}


def render_report(records: list[CellRecord], out_path: Path) -> None:
    """Write a single-file HTML matrix report.

    Layout: rows = writers, cols = modules. Each cell shows the
    failure_class colored, gates-passed count, wall-clock, and links
    to the per-cell log/telemetry.
    """
    modules_in_order = [(lvl, slg) for lvl, slg in MODULES]
    by_cell: dict[tuple[str, str, str], CellRecord] = {}
    for rec in records:
        by_cell[(rec.writer, rec.level, rec.slug)] = rec

    lines: list[str] = [
        "<!DOCTYPE html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        "<title>V7 Writer Bench v0 — Matrix</title>",
        "<style>",
        "  body { font-family: -apple-system, system-ui, sans-serif; margin: 24px; color: #1d3557; }",
        "  h1 { margin-bottom: 4px; }",
        "  .subtitle { color: #6c757d; margin-top: 0; }",
        "  table { border-collapse: collapse; margin-top: 24px; }",
        "  th, td { border: 1px solid #ced4da; padding: 8px 10px; vertical-align: top; font-size: 13px; }",
        "  th { background: #f1f3f5; text-align: left; }",
        "  td.cell { color: white; min-width: 180px; }",
        "  td.cell .class { font-weight: 600; font-size: 12px; text-transform: uppercase; }",
        "  td.cell .meta { font-size: 11px; opacity: 0.85; margin-top: 4px; }",
        "  td.cell a { color: #ffd6a5; }",
        "  .legend { margin-top: 24px; font-size: 12px; }",
        "  .legend .swatch { display: inline-block; width: 12px; height: 12px; margin-right: 4px; vertical-align: middle; }",
        "</style>",
        "</head><body>",
        "<h1>V7 writer-bench v0 — matrix</h1>",
        f"<p class='subtitle'>Locked design: PR #2221 §2. Generated {html.escape(_dt.datetime.now(_dt.UTC).isoformat())}.</p>",
        "<table><thead><tr><th>writer / module</th>",
    ]
    for lvl, slg in modules_in_order:
        lines.append(f"<th>{html.escape(f'{lvl}/{slg}')}</th>")
    lines.append("</tr></thead><tbody>")

    for writer in WRITERS:
        lines.append("<tr>")
        lines.append(f"<th>{html.escape(writer)}</th>")
        for lvl, slg in modules_in_order:
            rec = by_cell.get((writer, lvl, slg))
            if rec is None:
                lines.append("<td>—</td>")
                continue
            color = _CELL_COLOR_BY_CLASS.get(rec.failure_class, "#6c757d")
            gates_summary = f"{len(rec.gates_passed)} ✓ / {len(rec.gates_failed)} ✗"
            wall_clock = f"{rec.wall_clock_s:.0f}s"
            log_path = Path(rec.telemetry_path or "").with_suffix(".log") if rec.telemetry_path else None
            log_link = (
                f"<a href='{html.escape(str(log_path.relative_to(out_path.parent)))}'>log</a>"
                if log_path and log_path.exists()
                else ""
            )
            tele_link = (
                f"<a href='{html.escape(str(Path(rec.telemetry_path).relative_to(out_path.parent)))}'>jsonl</a>"
                if rec.telemetry_path and Path(rec.telemetry_path).exists()
                else ""
            )
            lines.append(
                "<td class='cell' style='background:" + color + "'>"
                f"<div class='class'>{html.escape(rec.failure_class)}</div>"
                f"<div class='meta'>phase: {html.escape(rec.phase_reached)}</div>"
                f"<div class='meta'>gates: {gates_summary}</div>"
                f"<div class='meta'>wall: {wall_clock}</div>"
                f"<div class='meta'>{log_link} {tele_link}</div>"
                "</td>"
            )
        lines.append("</tr>")
    lines.append("</tbody></table>")

    lines.append("<div class='legend'>")
    for cls, col in _CELL_COLOR_BY_CLASS.items():
        lines.append(
            f"<span><span class='swatch' style='background:{col}'></span>{html.escape(cls)}</span>&nbsp;&nbsp;"
        )
    lines.append("</div>")
    lines.append("</body></html>")
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------


def _bench_dir(stamp: str | None = None) -> Path:
    if stamp is None:
        stamp = _dt.datetime.now(_dt.UTC).strftime("%Y%m%d-%H%M%S")
    out = _REPO_ROOT / "audit" / "writer-bench-v0" / stamp
    out.mkdir(parents=True, exist_ok=True)
    return out


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="writer_matrix",
        description="V7 writer-bench v0 — sequential 6×5 matrix",
    )
    parser.add_argument(
        "--writers",
        default=",".join(WRITERS),
        help="Comma-separated writer subset (default: all 6).",
    )
    parser.add_argument(
        "--modules",
        default=",".join(f"{lvl}/{slg}" for lvl, slg in MODULES),
        help="Comma-separated <level>/<slug> module subset (default: all 5).",
    )
    parser.add_argument(
        "--timeout-s",
        type=int,
        default=PER_CELL_TIMEOUT_S,
        help=f"Per-cell subprocess timeout (default: {PER_CELL_TIMEOUT_S} s).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned matrix and exit without invoking v7_build.py.",
    )
    parser.add_argument(
        "--stamp",
        default=None,
        help="Override the bench-dir stamp (default: UTC YYYYMMDD-HHMMSS).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    writers = [w.strip() for w in args.writers.split(",") if w.strip()]
    modules: list[tuple[str, str]] = []
    for entry in args.modules.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if "/" not in entry:
            print(f"writer_matrix: bad --modules entry {entry!r}; expected <level>/<slug>", file=sys.stderr)
            return 2
        lvl, slg = entry.split("/", 1)
        modules.append((lvl, slg))

    # Validate writers against the pinned matrix to fail fast on typos.
    for w in writers:
        if w not in WRITER_DEFAULTS:
            print(
                f"writer_matrix: unknown writer {w!r}; valid: {sorted(WRITER_DEFAULTS)}",
                file=sys.stderr,
            )
            return 2

    n_cells = len(writers) * len(modules)
    bench = _bench_dir(args.stamp)

    print(
        f"writer-bench v0: {len(writers)} writers × {len(modules)} modules = {n_cells} cells",
        flush=True,
    )
    print(f"bench dir: {bench}", flush=True)
    print(f"per-cell timeout: {args.timeout_s} s", flush=True)
    print(f"writers: {writers}", flush=True)
    print(f"modules: {modules}", flush=True)

    if args.dry_run:
        print("--dry-run: not invoking v7_build.py.", flush=True)
        return 0

    records: list[CellRecord] = []

    # Outer loop = modules, inner loop = writers (per PR #2221 §2.4).
    for lvl, slg in modules:
        for writer in writers:
            print(
                f"\n=== cell: writer={writer} level={lvl} slug={slg} ===",
                flush=True,
            )
            rec = run_cell(
                writer=writer,
                level=lvl,
                slug=slg,
                bench_dir=bench,
                timeout_s=args.timeout_s,
            )
            records.append(rec)
            print(
                f"  → phase={rec.phase_reached} class={rec.failure_class} "
                f"wall={rec.wall_clock_s:.0f}s exit={rec.exit_code}",
                flush=True,
            )
            # Persist after every cell so a mid-run abort still has
            # the partial matrix.
            (bench / "matrix.json").write_text(
                json.dumps([asdict(r) for r in records], indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            render_report(records, bench / "report.html")

    # Final summary.
    n_ok = sum(1 for r in records if r.failure_class == "ok")
    print(f"\nwriter-bench v0 complete: {n_ok}/{len(records)} cells passed python_qg", flush=True)
    print(f"matrix: {bench / 'matrix.json'}", flush=True)
    print(f"report: {bench / 'report.html'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
