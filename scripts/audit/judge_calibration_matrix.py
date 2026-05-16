#!/usr/bin/env python3
"""Run the Russianism judge calibration matrix across models and harnesses."""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import html
import json
import os
import shutil
import subprocess
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    from _judge_eval_lib import (
        PROJECT_ROOT,
        aggregate,
        build_judge_prompt_h2,
        parse_json_verdict,
        pull_calibration_cases,
        retrieve_evidence,
        score_case,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from scripts.audit._judge_eval_lib import (
        PROJECT_ROOT,
        aggregate,
        build_judge_prompt_h2,
        parse_json_verdict,
        pull_calibration_cases,
        retrieve_evidence,
        score_case,
        utc_timestamp,
    )

REQUEST_TIMEOUT_S = 480
HERMES_TIMEOUT_S = 600
HERMES_BIN = "hermes"
HERMES_CFG = Path.home() / ".hermes" / "config.yaml"
DEFAULT_OUT_DIR = PROJECT_ROOT / "audit" / "2026-05-17-judge-calibration-matrix"

FAMILIES = ("xai", "anthropic", "openai", "google")
HARNESSES = ("native_cli", "hermes")
MCP_STATES = ("with_mcp", "without_mcp")

FAMILY_MODELS: dict[str, tuple[str, ...]] = {
    "xai": ("grok-4.3",),
    "anthropic": (
        "claude-opus-4-7",
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-opus-4-5-20251101",
        "claude-sonnet-4-5-20250929",
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514",
        "claude-haiku-4-5-20251001",
    ),
    "openai": (
        "gpt-5.5",
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.3-codex",
        "gpt-5.3-codex-spark",
        "gpt-5.2",
    ),
    "google": ("gemini-3.0-flash-preview", "gemini-3.1-pro-preview"),
}

SUPPORTED_HARNESSES: dict[str, tuple[str, ...]] = {
    "xai": ("hermes",),
    "anthropic": ("native_cli", "hermes"),
    "openai": ("native_cli", "hermes"),
    "google": ("native_cli",),
}

DEFAULT_EFFORTS: dict[str, tuple[str, ...]] = {
    "xai": ("low", "minimal", "medium", "high", "xhigh"),
    "anthropic": ("low", "medium", "high", "xhigh"),
    "openai": ("low", "medium", "high"),
    "google": ("default",),
}

SMOKE_CELLS = (
    ("xai", "grok-4.3", "hermes", "medium", "with_mcp"),
    ("anthropic", "claude-haiku-4-5-20251001", "native_cli", "medium", "with_mcp"),
    ("openai", "gpt-5.4-mini", "native_cli", "medium", "with_mcp"),
    ("openai", "gpt-5.5", "hermes", "medium", "with_mcp"),
    ("google", "gemini-3.1-pro-preview", "native_cli", "default", "with_mcp"),
)


@dataclass(frozen=True)
class Cell:
    family: str
    model: str
    harness: str
    effort: str
    mcp_state: str


@dataclass(frozen=True)
class HarnessCall:
    ok: bool
    stdout: str
    stderr: str
    returncode: int | None
    duration_s: float
    cmd: tuple[str, ...]
    error: str | None = None


def parse_csv(raw: str | None, allowed: Iterable[str] | None = None) -> list[str] | None:
    """Parse comma-separated CLI values."""
    if raw is None:
        return None
    values = [part.strip() for part in raw.split(",") if part.strip()]
    if allowed is not None:
        allowed_set = set(allowed)
        bad = [value for value in values if value not in allowed_set]
        if bad:
            raise SystemExit(f"invalid value(s): {', '.join(bad)}; allowed: {', '.join(sorted(allowed_set))}")
    return values


def effort_palette(family: str, model: str) -> tuple[str, ...]:
    """Return the pre-locked effort palette for one model."""
    if family == "anthropic" and model == "claude-opus-4-7":
        return (*DEFAULT_EFFORTS["anthropic"], "max")
    return DEFAULT_EFFORTS[family]


def cell_path(out_dir: Path, cell: Cell) -> Path:
    """Return the per-cell JSON path."""
    return out_dir / cell.family / cell.model / cell.harness / f"{cell.effort}-{cell.mcp_state}.json"


def is_forbidden_cell(cell: Cell) -> bool:
    """Return True for combinations the matrix must not materialize."""
    return cell.family == "google" and cell.harness == "hermes"


def unsupported_reason(cell: Cell) -> str | None:
    """Return a deterministic skip reason for unsupported cells."""
    if cell.family not in FAMILIES:
        return f"unknown family: {cell.family}"
    if cell.model not in FAMILY_MODELS[cell.family]:
        return f"{cell.model} is not in the configured {cell.family} model palette"
    if cell.harness not in HARNESSES:
        return f"unknown harness: {cell.harness}"
    if cell.harness not in SUPPORTED_HARNESSES[cell.family]:
        return f"{cell.family} does not have a {cell.harness} route"
    if cell.mcp_state not in MCP_STATES:
        return f"unknown MCP state: {cell.mcp_state}"
    if cell.effort not in effort_palette(cell.family, cell.model):
        return (
            f"{cell.model} does not accept effort={cell.effort} via {cell.harness}; "
            f"configured palette: {', '.join(effort_palette(cell.family, cell.model))}"
        )
    return None


def build_matrix(
    *,
    families: list[str] | None,
    harnesses: list[str] | None,
    models: list[str] | None,
    efforts: list[str] | None,
    mcp_states: list[str] | None,
    smoke: bool,
) -> list[Cell]:
    """Build the requested sparse matrix."""
    selected_families = families or list(FAMILIES)
    selected_harnesses = harnesses or list(HARNESSES)
    selected_mcp_states = mcp_states or list(MCP_STATES)

    if smoke:
        cells = [
            Cell(*raw)
            for raw in SMOKE_CELLS
            if raw[0] in selected_families
            and raw[2] in selected_harnesses
            and raw[4] in selected_mcp_states
            and (models is None or raw[1] in models)
            and (efforts is None or raw[3] in efforts)
        ]
        return [cell for cell in cells if not is_forbidden_cell(cell)]

    cells: list[Cell] = []
    for family in selected_families:
        family_models = [model for model in FAMILY_MODELS[family] if models is None or model in models]
        for model in family_models:
            selected_efforts = efforts or list(effort_palette(family, model))
            for harness in selected_harnesses:
                for effort in selected_efforts:
                    for mcp_state in selected_mcp_states:
                        cell = Cell(family, model, harness, effort, mcp_state)
                        if not is_forbidden_cell(cell):
                            cells.append(cell)
    return cells


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write JSON deterministically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_na_cell(out_dir: Path, cell: Cell, reason: str) -> dict[str, Any]:
    """Write an unsupported-combo record."""
    record = {
        "cell": asdict(cell),
        "result": "n/a",
        "reason": reason,
        "checked_at": utc_timestamp(),
    }
    write_json(cell_path(out_dir, cell), record)
    return record


def command_version(binary: str) -> str:
    """Best-effort CLI version string for telemetry."""
    try:
        proc = subprocess.run(
            [binary, "--version"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        return f"unavailable: {exc}"
    combined = (proc.stdout or proc.stderr or "").strip()
    return combined.splitlines()[0] if combined else f"rc={proc.returncode}; empty version output"


def run_subprocess(cmd: list[str], *, timeout_s: int, stdin: str | None = None) -> HarnessCall:
    """Run a provider CLI and capture bounded telemetry."""
    display_cmd = tuple(cmd[:])
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            input=stdin,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except FileNotFoundError as exc:
        return HarnessCall(False, "", "", None, time.time() - t0, display_cmd, error=str(exc))
    except subprocess.TimeoutExpired as exc:
        return HarnessCall(
            False,
            exc.stdout or "",
            exc.stderr or "",
            None,
            time.time() - t0,
            display_cmd,
            error=f"timed out after {timeout_s}s",
        )
    return HarnessCall(
        proc.returncode == 0 and bool((proc.stdout or "").strip()),
        proc.stdout or "",
        proc.stderr or "",
        proc.returncode,
        time.time() - t0,
        display_cmd,
    )


def build_native_command(cell: Cell, prompt: str) -> list[str]:
    """Build the native CLI command for one prompt."""
    if cell.family == "anthropic":
        # Two operating modes for the anthropic native_cli lane:
        #
        # (1) CLAUDE_MATRIX_USE_BARE=1 (legacy fast path): `--bare` skips
        #     session init (hooks + LSP + plugin sync + CLAUDE.md autoload).
        #     Saves ~30s per call but FORBIDS OAuth + keychain reads (per
        #     `claude --help`), so this lane requires ANTHROPIC_API_KEY in
        #     env. Without the key, calls return "Not logged in · Please
        #     run /login".
        #
        # (2) DEFAULT (OAuth-inherit path, added 2026-05-17): drop `--bare`
        #     so the subprocess inherits the parent session's OAuth from
        #     ~/.claude/. No API key needed when invoked from a logged-in
        #     Claude Code context (e.g. dispatched headless worker). Costs
        #     ~30s extra init per call but eliminates the API-key
        #     requirement.
        #
        # See #2036 for the Hermes-anthropic silent-drop bug that makes the
        # hermes lane unusable as of 2026-05-17 (status reports `logged in`
        # but calls return empty stdout).
        use_bare = os.environ.get("CLAUDE_MATRIX_USE_BARE") == "1"
        cmd = ["claude", "-p"]
        if use_bare:
            cmd.append("--bare")
        cmd.extend(["--model", cell.model])
        if cell.effort != "default":
            cmd.extend(["--effort", cell.effort])
        if cell.mcp_state == "with_mcp" and (PROJECT_ROOT / ".mcp.json").exists():
            cmd.extend(["--mcp-config", str(PROJECT_ROOT / ".mcp.json")])
        cmd.extend(["--", prompt])
        return cmd

    if cell.family == "openai":
        cmd = [
            "codex",
            "exec",
            "--skip-git-repo-check",
            "-C",
            str(PROJECT_ROOT),
            "--color",
            "never",
            "--model",
            cell.model,
        ]
        if cell.effort != "default":
            cmd.extend(["-c", f"model_reasoning_effort={cell.effort}"])
        if cell.mcp_state == "with_mcp":
            cmd.extend(["-c", 'mcp_servers.sources.url="http://127.0.0.1:8766/mcp"'])
        cmd.append(prompt)
        return cmd

    if cell.family == "google":
        cmd = ["gemini", "-m", cell.model]
        if cell.mcp_state == "with_mcp":
            cmd.extend(["--allowed-mcp-server-names", "sources"])
        cmd.extend(["-p", prompt])
        return cmd

    raise ValueError(f"no native CLI route for {cell.family}")


def run_native_cli(cell: Cell, prompt: str) -> HarnessCall:
    """Invoke a native provider CLI for one calibration prompt."""
    return run_subprocess(build_native_command(cell, prompt), timeout_s=REQUEST_TIMEOUT_S)


def _read_effort_line(text: str) -> tuple[int, str] | None:
    """Find the agent-level Hermes ``reasoning_effort`` line."""
    for idx, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if line.startswith("  reasoning_effort:") and stripped.startswith("reasoning_effort:"):
            value = stripped.split(":", 1)[1].strip()
            return idx, value
    return None


def set_hermes_effort(config_path: Path, effort: str) -> str:
    """Edit Hermes config in place and return the previous effort."""
    text = config_path.read_text(encoding="utf-8")
    located = _read_effort_line(text)
    if located is None:
        raise RuntimeError(
            "could not locate `  reasoning_effort: <value>` in ~/.hermes/config.yaml; "
            "Hermes may have changed config shape"
        )
    line_idx, previous = located
    lines = text.splitlines(keepends=True)
    newline = "\n" if lines[line_idx].endswith("\n") else ""
    lines[line_idx] = f"  reasoning_effort: {effort}{newline}"
    config_path.write_text("".join(lines), encoding="utf-8")
    return previous


@contextlib.contextmanager
def hermes_effort_swap(config_path: Path, effort: str) -> Iterable[str]:
    """Lock, back up, edit, and restore Hermes effort for one call."""
    backup_path = config_path.with_name(f"{config_path.name}.judge-calibration-backup")
    with config_path.open("r", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        shutil.copy2(config_path, backup_path)
        previous = set_hermes_effort(config_path, effort)
        try:
            yield previous
        finally:
            shutil.copy2(backup_path, config_path)
            backup_path.unlink(missing_ok=True)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def hermes_mcp_command(action: str) -> HarnessCall:
    """Run ``hermes mcp disable/enable sources``."""
    call = run_subprocess([HERMES_BIN, "mcp", action, "sources"], timeout_s=60)
    if call.returncode == 0 and call.error is None:
        return HarnessCall(
            True,
            call.stdout,
            call.stderr,
            call.returncode,
            call.duration_s,
            call.cmd,
        )
    return call


def run_hermes(cell: Cell, prompt: str, *, config_path: Path = HERMES_CFG) -> HarnessCall:
    """Invoke Hermes one-shot mode with atomic effort config swapping."""
    try:
        with hermes_effort_swap(config_path, cell.effort):
            disabled: HarnessCall | None = None
            if cell.mcp_state == "without_mcp":
                disabled = hermes_mcp_command("disable")
                if not disabled.ok:
                    return disabled
            try:
                return run_subprocess(
                    [HERMES_BIN, "-z", prompt, "-m", cell.model],
                    timeout_s=HERMES_TIMEOUT_S,
                )
            finally:
                if disabled is not None:
                    hermes_mcp_command("enable")
    except (OSError, RuntimeError) as exc:
        return HarnessCall(False, "", "", None, 0.0, (HERMES_BIN, "-z", "-m", cell.model), error=str(exc))


def run_harness(cell: Cell, prompt: str) -> HarnessCall:
    """Dispatch a single prompt to the configured harness."""
    if cell.harness == "hermes":
        return run_hermes(cell, prompt)
    if cell.harness == "native_cli":
        return run_native_cli(cell, prompt)
    raise ValueError(f"unknown harness {cell.harness}")


def verdict_from_call(call: HarnessCall) -> dict[str, Any]:
    """Convert CLI output into a scoreable verdict."""
    if call.ok:
        return parse_json_verdict(call.stdout, duration_s=call.duration_s)
    return {
        "verdict": "judge_error",
        "error": call.error,
        "returncode": call.returncode,
        "stdout": call.stdout[:500],
        "stderr": call.stderr[:500],
        "duration_s": call.duration_s,
    }


def run_cell(
    *,
    out_dir: Path,
    cell: Cell,
    cases: list[dict[str, Any]],
    harness_runner: Callable[[Cell, str], HarnessCall] = run_harness,
) -> dict[str, Any]:
    """Run or n/a one cell and write its JSON artifact."""
    reason = unsupported_reason(cell)
    if reason:
        return write_na_cell(out_dir, cell, reason)

    started = utc_timestamp()
    t0 = time.time()
    scores: list[dict[str, Any]] = []
    judgments: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for case in cases:
        target = case["output_text"]
        prompt = build_judge_prompt_h2(target, retrieve_evidence(target))
        call = harness_runner(cell, prompt)
        verdict = verdict_from_call(call)
        score = score_case(verdict, case["gold"])
        scores.append(score)

        if verdict.get("verdict") in {"judge_error", "json_parse_error"}:
            errors.append(
                {
                    "case_id": case["prompt_id"],
                    "verdict": verdict.get("verdict"),
                    "error": verdict.get("error") or verdict.get("note"),
                    "returncode": verdict.get("returncode"),
                    "stdout": verdict.get("stdout") or verdict.get("raw"),
                    "stderr": verdict.get("stderr"),
                }
            )

        true_label = "clean" if score["expected_clean"] else "issues_found"
        # Capture evidence_type usage from H2 prompt verdicts. Older prompts
        # don't emit this field; rows then carry an empty list. Truncate each
        # issue dict so the per-cell JSON stays small.
        raw_issues = []
        for item in (verdict.get("issues") or []):
            if not isinstance(item, dict):
                continue
            raw_issues.append({
                "phrase": str(item.get("phrase", ""))[:200],
                "evidence_type": item.get("evidence_type"),
                "evidence_quote": str(item.get("evidence_quote", ""))[:200],
                "severity": item.get("severity"),
            })
        judgments.append(
            {
                "case_id": case["prompt_id"],
                "true_label": true_label,
                "model_label": verdict.get("verdict"),
                "model_confidence": verdict.get("confidence", "unspecified"),
                "raw_response_chars": len(call.stdout or verdict.get("raw", "") or ""),
                "case_acc": score["case_acc"],
                "judge_sev2_plus_count": score["judge_sev2_plus_count"],
                "expected_flags_count": score["expected_flags_count"],
                "raw_issues": raw_issues,
            }
        )

    agg = aggregate(scores)
    record = {
        "cell": asdict(cell),
        "started_at": started,
        "finished_at": utc_timestamp(),
        "duration_s": round(time.time() - t0, 2),
        "n_cases": len(cases),
        "judgments": judgments,
        "scores": {
            "f1": agg["f1"],
            "case_acc": agg["case_acc"],
            "precision": agg["precision"],
            "recall": agg["recall"],
        },
        "raw_telemetry": {
            "harness": cell.harness,
            "harness_version": command_version(HERMES_BIN if cell.harness == "hermes" else _native_binary(cell.family)),
            "model_id": cell.model,
            "effort_actual": cell.effort,
            "mcp_servers": ["sources"] if cell.mcp_state == "with_mcp" else [],
            "errors": errors,
        },
    }
    write_json(cell_path(out_dir, cell), record)
    return record


def _native_binary(family: str) -> str:
    if family == "anthropic":
        return "claude"
    if family == "openai":
        return "codex"
    if family == "google":
        return "gemini"
    return family


def existing_cell_complete(path: Path) -> bool:
    """Return True when a resume-able cell JSON already exists."""
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return isinstance(data, dict) and "cell" in data and (
        data.get("result") == "n/a" or "scores" in data or data.get("result") == "error"
    )


def run_cells(
    *,
    out_dir: Path,
    cells: list[Cell],
    cases: list[dict[str, Any]],
    resume: bool,
    max_parallel: int,
    harness_runner: Callable[[Cell, str], HarnessCall] = run_harness,
) -> list[dict[str, Any]]:
    """Run cells serially by family, with bounded intra-family parallelism."""
    records: list[dict[str, Any]] = []
    for family in FAMILIES:
        family_cells = [cell for cell in cells if cell.family == family]
        if not family_cells:
            continue

        runnable: list[Cell] = []
        for cell in family_cells:
            path = cell_path(out_dir, cell)
            if resume and existing_cell_complete(path):
                print(f"[resume] {path}")
                records.append(json.loads(path.read_text(encoding="utf-8")))
            else:
                runnable.append(cell)

        if not runnable:
            continue

        workers = max(1, min(max_parallel, len(runnable)))
        if workers == 1:
            for cell in runnable:
                records.append(run_cell(out_dir=out_dir, cell=cell, cases=cases, harness_runner=harness_runner))
            continue

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(run_cell, out_dir=out_dir, cell=cell, cases=cases, harness_runner=harness_runner): cell
                for cell in runnable
            }
            for future in as_completed(futures):
                records.append(future.result())
    return records


def write_probe_results(out_dir: Path, records: list[dict[str, Any]]) -> Path:
    """Write a compact JSONL probe summary for PR evidence."""
    path = out_dir / "probe-results.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for record in records:
        cell = record["cell"]
        errors = record.get("raw_telemetry", {}).get("errors") or []
        if record.get("result") == "n/a":
            result = "skipped"
            reason = record.get("reason")
        elif errors:
            result = "error"
            reason = errors[0].get("error") or errors[0].get("stdout") or errors[0].get("stderr")
        else:
            result = "valid_response"
            reason = None
        lines.append(
            json.dumps(
                {
                    "family": cell["family"],
                    "model": cell["model"],
                    "harness": cell["harness"],
                    "effort": cell["effort"],
                    "mcp_state": cell["mcp_state"],
                    "result": result,
                    "reason": reason,
                },
                ensure_ascii=False,
            )
        )
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path


def load_cell_results(out_dir: Path) -> list[dict[str, Any]]:
    """Load all per-cell JSON artifacts under the output directory."""
    results: list[dict[str, Any]] = []
    for path in sorted(out_dir.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and isinstance(data.get("cell"), dict):
            results.append(data)
    return results


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def table(headers: list[str], rows: list[list[str]]) -> list[str]:
    """Build a Markdown table."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def successful_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in results if isinstance(r.get("scores"), dict) and r.get("result") != "n/a"]


def failure_reason(result: dict[str, Any]) -> str:
    if result.get("result") == "n/a":
        return str(result.get("reason", "n/a"))
    errors = result.get("raw_telemetry", {}).get("errors") or []
    if errors:
        return json.dumps(errors[:3], ensure_ascii=False)
    return ""


def build_markdown_report(results: list[dict[str, Any]]) -> str:
    """Render the consolidated Markdown report."""
    ok_results = successful_results(results)
    na_results = [r for r in results if r.get("result") == "n/a"]
    errored_results = [
        r for r in ok_results
        if r.get("raw_telemetry", {}).get("errors")
    ]
    sorted_ok = sorted(ok_results, key=lambda r: r["scores"]["f1"], reverse=True)

    lines = [
        "# Russianism Judge Calibration Matrix",
        "",
        f"Generated: {utc_timestamp()}",
        "",
        "## Summary",
        "",
        f"- Cells scored: {len(ok_results)}",
        f"- Cells n/a: {len(na_results)}",
        f"- Cells with harness errors: {len(errored_results)}",
        "",
        "## Leaderboard",
        "",
    ]

    leaderboard_rows = []
    for result in sorted_ok:
        cell = result["cell"]
        scores = result["scores"]
        leaderboard_rows.append(
            [
                cell["family"],
                cell["model"],
                cell["harness"],
                cell["effort"],
                cell["mcp_state"],
                pct(scores.get("f1")),
                pct(scores.get("precision")),
                pct(scores.get("recall")),
                pct(scores.get("case_acc")),
                f"{result.get('duration_s', 0):.1f}s",
                "0",
            ]
        )
    lines.extend(
        table(
            ["family", "model", "harness", "effort", "mcp_state", "F1", "P", "R", "case_acc", "avg_dur", "n/a-count"],
            leaderboard_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", str(len(na_results))]],
        )
    )

    lines.extend(["", "## Harness Comparison", ""])
    lines.extend(table(["model", "effort", "mcp_state", "native_cli F1", "hermes F1", "delta"], harness_comparison_rows(ok_results)))

    lines.extend(["", "## MCP Impact", ""])
    lines.extend(table(["model", "harness", "effort", "without case_acc", "with case_acc", "delta"], mcp_impact_rows(ok_results)))

    lines.extend(["", "## Effort Scaling", ""])
    lines.extend(table(["model", "harness", "mcp_state", "F1 by effort"], effort_scaling_rows(ok_results)))

    lines.extend(["", "## Failure Log", ""])
    failure_rows = []
    for result in results:
        reason = failure_reason(result)
        if not reason:
            continue
        cell = result["cell"]
        failure_rows.append(
            [
                cell["family"],
                cell["model"],
                cell["harness"],
                cell["effort"],
                cell["mcp_state"],
                reason.replace("\n", " ")[:300],
            ]
        )
    lines.extend(table(["family", "model", "harness", "effort", "mcp_state", "reason"], failure_rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "none"]]))
    return "\n".join(lines) + "\n"


def harness_comparison_rows(results: list[dict[str, Any]]) -> list[list[str]]:
    by_key: dict[tuple[str, str, str], dict[str, float]] = {}
    for result in results:
        cell = result["cell"]
        key = (cell["model"], cell["effort"], cell["mcp_state"])
        by_key.setdefault(key, {})[cell["harness"]] = result["scores"]["f1"]
    rows = []
    for (model, effort, mcp_state), values in sorted(by_key.items()):
        if "native_cli" in values and "hermes" in values:
            delta = values["hermes"] - values["native_cli"]
            rows.append([model, effort, mcp_state, pct(values["native_cli"]), pct(values["hermes"]), f"{delta * 100:+.1f}pp"])
    return rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]


def mcp_impact_rows(results: list[dict[str, Any]]) -> list[list[str]]:
    by_key: dict[tuple[str, str, str], dict[str, float]] = {}
    for result in results:
        cell = result["cell"]
        key = (cell["model"], cell["harness"], cell["effort"])
        by_key.setdefault(key, {})[cell["mcp_state"]] = result["scores"]["case_acc"]
    rows = []
    for (model, harness, effort), values in sorted(by_key.items()):
        if "with_mcp" in values and "without_mcp" in values:
            delta = values["with_mcp"] - values["without_mcp"]
            rows.append([model, harness, effort, pct(values["without_mcp"]), pct(values["with_mcp"]), f"{delta * 100:+.1f}pp"])
    return rows or [["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]]


def effort_scaling_rows(results: list[dict[str, Any]]) -> list[list[str]]:
    by_key: dict[tuple[str, str, str], list[tuple[str, float]]] = {}
    for result in results:
        cell = result["cell"]
        key = (cell["model"], cell["harness"], cell["mcp_state"])
        by_key.setdefault(key, []).append((cell["effort"], result["scores"]["f1"]))
    rows = []
    for (model, harness, mcp_state), values in sorted(by_key.items()):
        if len(values) < 2:
            continue
        rendered = ", ".join(f"{effort}={pct(value)}" for effort, value in sorted(values))
        rows.append([model, harness, mcp_state, rendered])
    return rows or [["n/a", "n/a", "n/a", "n/a"]]


def markdown_to_html(md: str) -> str:
    """Render simple audit-style HTML from the generated Markdown."""
    body_lines: list[str] = []
    in_table = False
    for line in md.splitlines():
        if line.startswith("# "):
            body_lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_table:
                body_lines.append("</tbody></table>")
                in_table = False
            body_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            body_lines.append(f"<p>{html.escape(line)}</p>")
        elif line.startswith("| "):
            cells = [html.escape(part.strip()) for part in line.strip("|").split("|")]
            if set(cells) == {"---"}:
                continue
            tag = "th" if not in_table else "td"
            if not in_table:
                body_lines.append("<table><thead><tr>" + "".join(f"<th>{cell}</th>" for cell in cells) + "</tr></thead><tbody>")
                in_table = True
            else:
                body_lines.append("<tr>" + "".join(f"<{tag}>{cell}</{tag}>" for cell in cells) + "</tr>")
        elif line.strip():
            body_lines.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        body_lines.append("</tbody></table>")
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Russianism Judge Calibration Matrix</title>
<style>
body{font-family:system-ui,sans-serif;line-height:1.45;max-width:1180px;margin:32px auto;padding:0 24px;color:#1f2933}
h1{margin-bottom:8px}
h2{margin-top:32px;border-bottom:1px solid #cbd2d9;padding-bottom:4px}
table{border-collapse:collapse;width:100%;margin:16px 0 28px}
th,td{border:1px solid #cbd2d9;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#eef2f6}
td{font-variant-numeric:tabular-nums}
p{margin:6px 0}
</style>
</head>
<body>
""" + "\n".join(body_lines) + "\n</body>\n</html>\n"


def build_reports(out_dir: Path) -> tuple[Path, Path]:
    """Generate REPORT.md and REPORT.html from per-cell JSON files."""
    results = load_cell_results(out_dir)
    md = build_markdown_report(results)
    md_path = out_dir / "REPORT.md"
    html_path = out_dir / "REPORT.html"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    html_path.write_text(markdown_to_html(md), encoding="utf-8")
    return md_path, html_path


def print_dry_run(cells: list[Cell]) -> None:
    """Print the requested matrix without running model calls."""
    for cell in cells:
        reason = unsupported_reason(cell)
        status = "n/a" if reason else "run"
        suffix = f" reason={reason}" if reason else ""
        print(f"{status}: {cell.family}/{cell.model}/{cell.harness}/{cell.effort}-{cell.mcp_state}{suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--families", help="Comma-separated families (default: all)")
    parser.add_argument("--harnesses", help="Comma-separated harnesses: native_cli,hermes (default: all)")
    parser.add_argument("--models", help="Comma-separated model ids (default: all supported for selected families)")
    parser.add_argument("--efforts", help="Comma-separated efforts (default: per-model palette)")
    parser.add_argument("--mcp-states", help="Comma-separated MCP states: with_mcp,without_mcp (default: both)")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--smoke", action="store_true", help="Run the cheapest smoke subset")
    parser.add_argument("--dry-run", action="store_true", help="Print matrix without running")
    parser.add_argument("--resume", action="store_true", help="Skip complete cell JSON files")
    parser.add_argument("--max-parallel", type=int, default=4, help="Per-family parallelism")
    parser.add_argument("--build-report-only", action="store_true", help="Only rebuild REPORT.md and REPORT.html")
    args = parser.parse_args()

    if args.build_report_only:
        md_path, html_path = build_reports(args.out_dir)
        print(f"Wrote {md_path}")
        print(f"Wrote {html_path}")
        return 0

    families = parse_csv(args.families, FAMILIES)
    harnesses = parse_csv(args.harnesses, HARNESSES)
    models = parse_csv(args.models)
    efforts = parse_csv(args.efforts)
    mcp_states = parse_csv(args.mcp_states, MCP_STATES)
    cells = build_matrix(
        families=families,
        harnesses=harnesses,
        models=models,
        efforts=efforts,
        mcp_states=mcp_states,
        smoke=args.smoke,
    )

    if args.dry_run:
        print_dry_run(cells)
        return 0

    cases = pull_calibration_cases()
    if args.smoke:
        cases = cases[:1]
    records = run_cells(
        out_dir=args.out_dir,
        cells=cells,
        cases=cases,
        resume=args.resume,
        max_parallel=args.max_parallel,
    )
    probe_path = write_probe_results(args.out_dir, records)
    md_path, html_path = build_reports(args.out_dir)
    print(f"Wrote {probe_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
