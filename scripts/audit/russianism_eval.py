#!/usr/bin/env python3
"""Run prompt x model Russianism evals through the local agent bridge."""

from __future__ import annotations

import argparse
import csv
import importlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ai_agent_bridge._db import get_db
from scripts.audit.checks.russicism_detection import check_russicisms

PYTHON, BRIDGE = Path(".venv/bin/python"), Path("scripts/ai_agent_bridge/__main__.py")
DEFAULT_MODELS = (
    "claude-opus-4-7,claude-sonnet-4-5,claude-haiku-4-5,"
    "gpt-5.5,gpt-5.5-mini,gemini-3.1-pro-preview,"
    "gemini-3-pro-preview,gemini-3.0-flash-preview"
)
FROM_AGENT = "russianism-eval"
_FOUND_COUNT_RE, _WORD_RE = re.compile(r"Found\s+(\d+)\s+Russicism", re.IGNORECASE), re.compile(r"[\w'’-]+", re.UNICODE)


@dataclass(frozen=True, slots=True)
class PromptCase:
    id: str
    category: str
    prompt_text: str
    expected_calque_categories: list[str]
    notes: str

@dataclass(frozen=True, slots=True)
class BridgeCall:
    prompt_id: str
    model: str
    family: str
    task_id: str
    argv: list[str]
    stdin: str | None

@dataclass(slots=True)
class EvalRow:
    prompt_id: str
    category: str
    model: str
    family: str
    task_id: str
    status: str
    output_text: str
    error: str
    word_count: int
    russicism_count: int
    gec_calque_count: int
    russicism_rate_per_100_words: float
    combined_rate_per_100_words: float
    findings: list[dict[str, Any]]


def _load_optional_gec_checker() -> Callable[[str], list[dict[str, Any]]] | None:
    try:
        checker = getattr(importlib.import_module("scripts.audit.checks.ua_gec_calques"), "check_ua_gec_calques", None)
    except ImportError:
        return None
    return checker if callable(checker) else None


CHECK_UA_GEC_CALQUES = _load_optional_gec_checker()

def _parse_models(raw: str) -> list[str]:
    models = [part.strip() for part in raw.split(",") if part.strip()]
    deduped = list(dict.fromkeys(models))
    if not deduped:
        raise ValueError("--models must name at least one model")
    return deduped

def _require_str(row: dict[str, Any], key: str, idx: int) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"prompt #{idx} field {key!r} must be a non-empty string")
    return value.strip()

def load_prompts(path: Path) -> list[PromptCase]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw_prompts = payload.get("prompts") if isinstance(payload, dict) else None
    if not isinstance(raw_prompts, list) or not raw_prompts:
        raise ValueError("prompt YAML must include a non-empty 'prompts' list")
    prompts: list[PromptCase] = []
    seen: set[str] = set()
    for idx, row in enumerate(raw_prompts, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"prompt #{idx} must be a mapping")
        prompt_id = _require_str(row, "id", idx)
        if prompt_id in seen:
            raise ValueError(f"duplicate prompt id: {prompt_id}")
        categories = row.get("expected_calque_categories")
        if not isinstance(categories, list) or not all(isinstance(item, str) for item in categories):
            raise ValueError(f"prompt {prompt_id!r} field 'expected_calque_categories' must be a list of strings")
        seen.add(prompt_id)
        prompts.append(
            PromptCase(
                prompt_id,
                _require_str(row, "category", idx),
                _require_str(row, "prompt_text", idx),
                list(categories),
                _require_str(row, "notes", idx),
            )
        )
    return prompts

def _family_for_model(model: str) -> str:
    if model.startswith("claude-"):
        return "claude"
    if model.startswith("gemini-"):
        return "gemini"
    if model.startswith(("gpt-", "o", "codex-")):
        return "codex"
    raise ValueError(f"cannot infer bridge family for model {model!r}")

def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")[:80]


class BridgeCaller:
    """Thin wrapper around scripts/ai_agent_bridge/__main__.py ask-* commands."""

    def __init__(self, run_id: str):
        self.run_id = run_id

    def plan(self, prompt: PromptCase, model: str) -> BridgeCall:
        family = _family_for_model(model)
        task_id = f"{self.run_id}-{_slug(prompt.id)}-{_slug(model)}"
        base = [str(PYTHON), str(BRIDGE)]
        if family == "claude":
            argv = [*base, "ask-claude", prompt.prompt_text, "--task-id", task_id, "--from", FROM_AGENT, "--to-model", model, "--new-session"]
            return BridgeCall(prompt.id, model, family, task_id, argv, None)
        if family == "codex":
            argv = [*base, "ask-codex", "-", "--task-id", task_id, "--from", FROM_AGENT, "--to-model", model, "--new-session"]
            return BridgeCall(prompt.id, model, family, task_id, argv, prompt.prompt_text)
        argv = [*base, "ask-gemini", "-", "--task-id", task_id, "--from", FROM_AGENT, "--model", model, "--stdout-only", "--skip-model-check", "--no-github"]
        return BridgeCall(prompt.id, model, family, task_id, argv, prompt.prompt_text)

    def __call__(self, prompt: PromptCase, model: str) -> tuple[BridgeCall, str]:
        call = self.plan(prompt, model)
        result = subprocess.run(call.argv, cwd=PROJECT_ROOT, input=call.stdin, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or f"exit {result.returncode}").strip())
        if call.family == "gemini" and result.stdout.strip():
            return call, result.stdout.strip()
        response = _latest_bridge_response(call.task_id, call.family)
        if response:
            return call, response
        raise RuntimeError(f"bridge completed but no response row found for task_id={call.task_id}")


def _latest_bridge_response(task_id: str, family: str) -> str | None:
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT content FROM messages
            WHERE task_id = ? AND from_llm = ? AND to_llm = ?
              AND message_type IN ('response', 'error')
            ORDER BY id DESC LIMIT 1
            """,
            (task_id, family, FROM_AGENT),
        ).fetchone()
    finally:
        conn.close()
    return str(row["content"]) if row else None

def _issue_count(violation: dict[str, Any]) -> int:
    match = _FOUND_COUNT_RE.search(str(violation.get("issue") or ""))
    return int(match.group(1)) if match else 1

def _rate(count: int, words: int) -> float:
    return round(count * 100 / (words or 1), 3)


def score_output(prompt: PromptCase, model: str, family: str, task_id: str, output: str) -> EvalRow:
    russ = check_russicisms(output, file_path=f"eval/russianism/{prompt.id}.md")
    gec = CHECK_UA_GEC_CALQUES(output) if CHECK_UA_GEC_CALQUES else []
    russ_count = sum(_issue_count(item) for item in russ)
    gec_count = len(gec)
    words = len(_WORD_RE.findall(output))
    findings = [{"source": "check_russicisms", **item} for item in russ]
    findings.extend({"source": "check_ua_gec_calques", **item} for item in gec)
    return EvalRow(
        prompt.id, prompt.category, model, family, task_id, "ok", output, "", words, russ_count, gec_count,
        _rate(russ_count, words), _rate(russ_count + gec_count, words), findings
    )

def error_row(prompt: PromptCase, model: str, family: str, task_id: str, error: str) -> EvalRow:
    return EvalRow(prompt.id, prompt.category, model, family, task_id, "error", "", error, 0, 0, 0, 0.0, 0.0, [])


def _model_summaries(rows: Sequence[EvalRow]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[EvalRow]] = defaultdict(list)
    for row in rows:
        grouped[row.model].append(row)
    summaries = {}
    for model, model_rows in grouped.items():
        words = sum(row.word_count for row in model_rows)
        russ = sum(row.russicism_count for row in model_rows)
        gec = sum(row.gec_calque_count for row in model_rows)
        summaries[model] = {
            "model": model, "family": model_rows[0].family, "prompt_count": len(model_rows),
            "ok_count": sum(row.status == "ok" for row in model_rows),
            "error_count": sum(row.status == "error" for row in model_rows), "word_count": words,
            "russicism_count": russ, "gec_calque_count": gec, "combined_count": russ + gec,
            "russicism_rate_per_100_words": _rate(russ, words),
            "combined_rate_per_100_words": _rate(russ + gec, words),
        }
    return summaries

def write_outputs(out_dir: Path, prompts_path: Path, rows: Sequence[EvalRow], models: Sequence[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "outputs.jsonl").write_text(
        "".join(json.dumps(asdict(row), ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )
    fields = [
        "prompt_id", "category", "model", "family", "task_id", "status", "word_count", "russicism_count",
        "gec_calque_count", "russicism_rate_per_100_words", "combined_rate_per_100_words", "error", "findings_json",
    ]
    with (out_dir / "scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            data = asdict(row) | {"findings_json": json.dumps(row.findings, ensure_ascii=False)}
            writer.writerow({field: data[field] for field in fields})
    summary = {
        "run_id": out_dir.name, "created_at": datetime.now(UTC).isoformat(), "prompt_file": _display_path(prompts_path),
        "models": list(models), "prompt_count": len({row.prompt_id for row in rows}), "dispatch_count": len(rows),
        "model_summaries": _model_summaries(rows), "rows": [asdict(row) for row in rows],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "REPORT.md").write_text(render_report(summary, rows), encoding="utf-8")

def render_report(summary: dict[str, Any], rows: Sequence[EvalRow]) -> str:
    leaderboard = sorted(
        summary["model_summaries"].values(),
        key=lambda item: (item["combined_rate_per_100_words"], item["combined_count"], item["model"]),
    )
    scorer = "`check_russicisms`" + (" + `check_ua_gec_calques`" if CHECK_UA_GEC_CALQUES else "")
    lines = [
        "# Russianism Eval Report", "", f"- Run: `{summary['run_id']}`", f"- Prompt file: `{summary['prompt_file']}`",
        f"- Dispatches: {summary['dispatch_count']}", f"- Scorer: {scorer}", "", "## Leaderboard", "",
        "Lower combined rate is better.", "",
        "| Rank | Model | Family | OK | Errors | Russianisms | GEC calques | Words | Combined / 100 words |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for rank, item in enumerate(leaderboard, start=1):
        lines.append(
            f"| {rank} | `{item['model']}` | {item['family']} | {item['ok_count']} | {item['error_count']} | "
            f"{item['russicism_count']} | {item['gec_calque_count']} | {item['word_count']} | "
            f"{item['combined_rate_per_100_words']:.3f} |"
        )
    lines += [
        "", "## Per-Prompt Breakdown", "",
        "| Prompt | Category | Model | Status | Russianisms | GEC calques | Words | Russ. / 100 words |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(rows, key=lambda item: (item.prompt_id, item.model)):
        lines.append(
            f"| `{row.prompt_id}` | {row.category} | `{row.model}` | {row.status} | {row.russicism_count} | "
            f"{row.gec_calque_count} | {row.word_count} | {row.russicism_rate_per_100_words:.3f} |"
        )
    bad = sorted(
        [row for row in rows if row.russicism_count + row.gec_calque_count > 0],
        key=lambda item: (item.combined_rate_per_100_words, item.russicism_count + item.gec_calque_count),
        reverse=True,
    )[:5]
    lines += ["", "## Sample Bad Outputs", ""]
    if not bad:
        lines.append("No scorer findings.")
    for row in bad:
        findings = "; ".join(str(item.get("issue") or item.get("type") or item) for item in row.findings[:3])
        lines += [f"### `{row.model}` on `{row.prompt_id}`", "", f"Findings: {findings}", "", "```text", _excerpt(row.output_text), "```", ""]
    return "\n".join(lines).rstrip() + "\n"


def _excerpt(text: str, limit: int = 700) -> str:
    trimmed = "\n".join(line.rstrip() for line in text.strip().splitlines())
    return trimmed[: limit - 3] + "..." if len(trimmed) > limit else trimmed


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def print_cost_report(rows: Sequence[EvalRow], prompts: Sequence[PromptCase], models: Sequence[str]) -> None:
    prompt_tokens = round(sum(len(prompt.prompt_text) for prompt in prompts) / 4)
    output_chars: dict[str, int] = defaultdict(int)
    for row in rows:
        output_chars[row.model] += len(row.output_text)
    print("Estimated token use (rough chars/4)")
    print("model,input_tokens,output_tokens,total_tokens")
    for model in models:
        output_tokens = round(output_chars[model] / 4)
        print(f"{model},{prompt_tokens},{output_tokens},{prompt_tokens + output_tokens}")


def _redacted_command(call: BridgeCall) -> str:
    parts = list(call.argv)
    if call.family == "claude" and "ask-claude" in parts and parts.index("ask-claude") + 1 < len(parts):
        parts[parts.index("ask-claude") + 1] = "<prompt_text>"
    return " ".join(parts)


def dry_run(prompts: Sequence[PromptCase], models: Sequence[str], max_parallel: int, caller: BridgeCaller) -> None:
    print(f"Dry run: prompts={len(prompts)} models={len(models)} dispatches={len(prompts) * len(models)}")
    print(f"Max parallel: {max_parallel}")
    for prompt in prompts:
        for model in models:
            call = caller.plan(prompt, model)
            stdin = " stdin=<prompt_text>" if call.stdin is not None else ""
            print(
                f"DRY-RUN prompt={prompt.id} model={model} family={call.family} "
                f"task_id={call.task_id} command={_redacted_command(call)}{stdin}"
            )
    print_cost_report([], prompts, models)
    print("No agent calls were made.")


def run_eval(
    prompts: Sequence[PromptCase],
    models: Sequence[str],
    out_dir: Path,
    max_parallel: int,
    caller: Callable[[PromptCase, str], tuple[BridgeCall, str]],
) -> list[EvalRow]:
    rows: list[EvalRow] = []
    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        futures = {executor.submit(caller, prompt, model): (prompt, model) for prompt in prompts for model in models}
        for future in as_completed(futures):
            prompt, model = futures[future]
            family = _family_for_model(model)
            try:
                call, output = future.result()
            except Exception as exc:
                rows.append(error_row(prompt, model, family, f"{out_dir.name}-{_slug(prompt.id)}-{_slug(model)}", str(exc)))
            else:
                rows.append(score_output(prompt, model, call.family, call.task_id, output))
    return sorted(rows, key=lambda item: (item.prompt_id, item.model))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Russianism eval prompts across bridge model variants.")
    parser.add_argument("--prompts", required=True, type=Path, help="Prompt YAML path.")
    parser.add_argument("--models", default=DEFAULT_MODELS, help=f"Comma-separated model list. Default: {DEFAULT_MODELS}")
    parser.add_argument("--out-dir", type=Path, help="Output directory. Default: audit/russianism-eval-{timestamp}.")
    parser.add_argument("--max-parallel", type=int, default=1, help="Maximum concurrent bridge calls.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print planned dispatches without agent calls.")
    return parser


def main(argv: Sequence[str] | None = None, caller: BridgeCaller | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        prompts, models = load_prompts(args.prompts), _parse_models(args.models)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.max_parallel < 1:
        print("error: --max-parallel must be >= 1", file=sys.stderr)
        return 2
    out_dir = args.out_dir or PROJECT_ROOT / "audit" / f"russianism-eval-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
    active_caller = caller or BridgeCaller(out_dir.name)
    if args.dry_run:
        dry_run(prompts, models, args.max_parallel, active_caller)
        return 0
    rows = run_eval(prompts, models, out_dir, args.max_parallel, active_caller)
    write_outputs(out_dir, args.prompts, rows, models)
    print_cost_report(rows, prompts, models)
    print(f"Wrote {_display_path(out_dir)}")
    return 1 if any(row.status == "error" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
