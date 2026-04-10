#!/usr/bin/env python3
"""Estimate token usage and USD spend from dispatch meta logs."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
COST_RATES_PATH = PROJECT_ROOT / "scripts" / "analytics" / "cost_rates.yaml"
DEFAULT_DIVISOR = 3.8
PROMPT_BLOAT_THRESHOLD = 30_000

_CYRILLIC_RE = re.compile(r"[А-Яа-яЇїІіЄєҐґ]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_AGENT_MODEL_RE = re.compile(r"\(([^()]+)\)\s*$")
_PHASE_SORT = {
    "pre-verify": 0,
    "skeleton": 1,
    "write": 2,
    "activities": 3,
    "vocab": 4,
    "enrich": 5,
    "review": 6,
}
_WRITER_PHASES = {"pre-verify", "skeleton", "write", "activities", "vocab"}
_WINDOW_SPECS = (
    ("all_time", None),
    ("last_7_days", 7),
    ("last_30_days", 30),
)


@dataclass(slots=True)
class CostRecord:
    path: Path
    level: str
    slug: str
    phase: str
    agent: str
    model: str
    model_source: str
    ok: bool
    timestamp: str | None
    mtime: datetime
    prompt_chars: int
    response_chars: int
    prompt_tokens_est: int
    response_tokens_est: int
    prompt_tokens_source: str
    response_tokens_source: str
    rate_model: str
    used_default_rate: bool
    cost_usd_est: float


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_since_date(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value).replace(tzinfo=UTC)
    except ValueError as exc:
        raise ValueError(f"Invalid --since date: {value!r}. Expected YYYY-MM-DD.") from exc


def _to_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return round(float(value))
    except (TypeError, ValueError):
        return 0


def _token_divisor_for_text(text: str | None) -> float:
    if not text:
        return DEFAULT_DIVISOR
    cyrillic = len(_CYRILLIC_RE.findall(text))
    latin = len(_LATIN_RE.findall(text))
    if cyrillic and not latin:
        return 3.5
    if latin and not cyrillic:
        return 4.0
    return DEFAULT_DIVISOR


def estimate_tokens(char_count: int, text: str | None = None) -> int:
    """Estimate tokens from chars using the shared heuristic."""
    if char_count <= 0:
        return 0
    return round(char_count / _token_divisor_for_text(text))


def _extract_model(agent: str, stored_model: Any) -> tuple[str, str]:
    model = str(stored_model).strip() if isinstance(stored_model, str) else ""
    if model:
        return model, "stored"
    match = _AGENT_MODEL_RE.search(agent or "")
    if match:
        return match.group(1).strip(), "agent"
    return "unknown", "missing"


def load_cost_rates(path: Path | None = None) -> dict[str, dict[str, float]]:
    rates_path = path or COST_RATES_PATH
    data = yaml.safe_load(rates_path.read_text(encoding="utf-8")) or {}
    rates: dict[str, dict[str, float]] = {}
    for model, raw in data.items():
        if not isinstance(raw, dict):
            continue
        rates[str(model)] = {
            "input": float(raw.get("input", 0.0)),
            "output": float(raw.get("output", 0.0)),
        }
    if "default" not in rates:
        raise ValueError(f"Missing 'default' rate in {rates_path}")
    return rates


def _model_rate_keys(model: str) -> list[str]:
    keys = [model]
    dotted = re.sub(r"-(\d+)-(\d+)$", r"-\1.\2", model)
    hyphenated = re.sub(r"-(\d+)\.(\d+)$", r"-\1-\2", model)
    for candidate in (dotted, hyphenated):
        if candidate not in keys:
            keys.append(candidate)
    return keys


def _resolve_rate_model(model: str, rates: dict[str, dict[str, float]]) -> str:
    for candidate in _model_rate_keys(model):
        if candidate in rates:
            return candidate
    return "default"


def _iter_dispatch_meta_files(
    *,
    root: Path | None = None,
    level: str | None = None,
    slug: str | None = None,
) -> Iterable[Path]:
    curriculum_root = root or CURRICULUM_ROOT
    level_part = level or "*"
    slug_part = slug or "*"
    pattern = f"{level_part}/orchestration/{slug_part}/dispatch/*-meta.json"
    yield from sorted(curriculum_root.glob(pattern))


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _record_from_meta(path: Path, meta: dict[str, Any], rates: dict[str, dict[str, float]]) -> CostRecord:
    level = path.parents[3].name
    slug = path.parents[1].name
    agent = str(meta.get("agent") or "")
    model, model_source = _extract_model(agent, meta.get("model"))

    prompt_chars = _to_int(meta.get("prompt_chars"))
    response_chars = _to_int(meta.get("response_chars"))

    if "prompt_tokens_est" in meta:
        prompt_tokens_est = _to_int(meta.get("prompt_tokens_est"))
        prompt_tokens_source = "stored"
    elif prompt_chars > 0:
        prompt_tokens_est = estimate_tokens(prompt_chars)
        prompt_tokens_source = "backfilled_chars"
    else:
        prompt_tokens_est = 0
        prompt_tokens_source = "missing"

    if "response_tokens_est" in meta:
        response_tokens_est = _to_int(meta.get("response_tokens_est"))
        response_tokens_source = "stored"
    elif response_chars > 0:
        response_tokens_est = estimate_tokens(response_chars)
        response_tokens_source = "backfilled_chars"
    else:
        response_tokens_est = 0
        response_tokens_source = "missing"

    rate_model = _resolve_rate_model(model, rates)
    rate = rates[rate_model]
    cost_usd_est = (
        (prompt_tokens_est * rate["input"]) + (response_tokens_est * rate["output"])
    ) / 1_000_000

    return CostRecord(
        path=path,
        level=level,
        slug=slug,
        phase=str(meta.get("phase") or "unknown"),
        agent=agent,
        model=model,
        model_source=model_source,
        ok=bool(meta.get("ok")),
        timestamp=str(meta.get("timestamp")) if meta.get("timestamp") else None,
        mtime=datetime.fromtimestamp(path.stat().st_mtime, tz=UTC),
        prompt_chars=prompt_chars,
        response_chars=response_chars,
        prompt_tokens_est=prompt_tokens_est,
        response_tokens_est=response_tokens_est,
        prompt_tokens_source=prompt_tokens_source,
        response_tokens_source=response_tokens_source,
        rate_model=rate_model,
        used_default_rate=rate_model == "default",
        cost_usd_est=cost_usd_est,
    )


def load_cost_records(
    *,
    root: Path | None = None,
    rates_path: Path | None = None,
    level: str | None = None,
    slug: str | None = None,
) -> list[CostRecord]:
    rates = load_cost_rates(rates_path)
    records: list[CostRecord] = []
    for path in _iter_dispatch_meta_files(root=root, level=level, slug=slug):
        meta = _read_json(path)
        if meta is None:
            continue
        records.append(_record_from_meta(path, meta, rates))
    return records


def _filter_records(
    records: Iterable[CostRecord],
    *,
    track: str | None = None,
    level: str | None = None,
    slug: str | None = None,
    phase: str | None = None,
    since: datetime | None = None,
) -> list[CostRecord]:
    target_level = level or track
    filtered: list[CostRecord] = []
    for record in records:
        if target_level and record.level != target_level:
            continue
        if slug and record.slug != slug:
            continue
        if phase and record.phase != phase:
            continue
        if since and record.mtime < since:
            continue
        filtered.append(record)
    return filtered


def _new_bucket() -> dict[str, Any]:
    return {
        "calls": 0,
        "ok_calls": 0,
        "prompt_chars": 0,
        "response_chars": 0,
        "prompt_tokens_est": 0,
        "response_tokens_est": 0,
        "cost_usd_est": 0.0,
    }


def _add_to_bucket(bucket: dict[str, Any], record: CostRecord) -> None:
    bucket["calls"] += 1
    bucket["ok_calls"] += int(record.ok)
    bucket["prompt_chars"] += record.prompt_chars
    bucket["response_chars"] += record.response_chars
    bucket["prompt_tokens_est"] += record.prompt_tokens_est
    bucket["response_tokens_est"] += record.response_tokens_est
    bucket["cost_usd_est"] += record.cost_usd_est


def _bucket_to_dict(name: str, bucket: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "calls": int(bucket["calls"]),
        "ok_calls": int(bucket["ok_calls"]),
        "prompt_chars": int(bucket["prompt_chars"]),
        "response_chars": int(bucket["response_chars"]),
        "prompt_tokens_est": int(bucket["prompt_tokens_est"]),
        "response_tokens_est": int(bucket["response_tokens_est"]),
        "cost_usd_est": round(float(bucket["cost_usd_est"]), 6),
    }


def build_cost_summary(
    *,
    records: Sequence[CostRecord] | None = None,
    root: Path | None = None,
    rates_path: Path | None = None,
    track: str | None = None,
    level: str | None = None,
    slug: str | None = None,
    phase: str | None = None,
    since: datetime | None = None,
) -> dict[str, Any]:
    source_records = list(records) if records is not None else load_cost_records(root=root, rates_path=rates_path)
    filtered = _filter_records(source_records, track=track, level=level, slug=slug, phase=phase, since=since)

    totals = _new_bucket()
    by_phase: dict[str, dict[str, Any]] = defaultdict(_new_bucket)
    by_model: dict[str, dict[str, Any]] = defaultdict(_new_bucket)
    by_module: dict[str, dict[str, Any]] = defaultdict(_new_bucket)
    phase_prompt_sizes: dict[str, list[int]] = defaultdict(list)
    unknown_models: set[str] = set()
    counts = Counter()

    for record in filtered:
        _add_to_bucket(totals, record)
        _add_to_bucket(by_phase[record.phase], record)
        _add_to_bucket(by_model[record.model], record)
        _add_to_bucket(by_module[f"{record.level}/{record.slug}"], record)
        if record.prompt_chars > 0:
            phase_prompt_sizes[record.phase].append(record.prompt_chars)

        if record.prompt_tokens_source == "backfilled_chars":
            counts["backfilled_prompt"] += 1
        elif record.prompt_tokens_source == "missing":
            counts["missing_prompt"] += 1
        if record.response_tokens_source == "backfilled_chars":
            counts["backfilled_response"] += 1
        elif record.response_tokens_source == "missing":
            counts["missing_response"] += 1
        if record.model_source != "stored":
            counts[f"model_{record.model_source}"] += 1
        if record.used_default_rate:
            unknown_models.add(record.model)

    warnings: list[str] = []
    if counts["backfilled_prompt"] or counts["backfilled_response"]:
        warnings.append(
            "Legacy meta without stored token estimates was backfilled from chars "
            f"({counts['backfilled_prompt']} prompt, {counts['backfilled_response']} response)."
        )
    if counts["missing_prompt"] or counts["missing_response"]:
        warnings.append(
            "Some legacy meta lacked both token estimates and char counts; those records contribute 0 est. tokens "
            f"({counts['missing_prompt']} prompt, {counts['missing_response']} response)."
        )
    if counts["model_agent"] or counts["model_missing"]:
        warnings.append(
            "Some meta lacked a stored model field; report inferred from agent label where possible "
            f"({counts['model_agent']} inferred, {counts['model_missing']} missing)."
        )
    if unknown_models:
        warnings.append(
            "Unknown model rates fell back to the YAML default for: "
            + ", ".join(sorted(unknown_models))
        )

    prompt_bloat_watch = []
    for phase_name, values in sorted(phase_prompt_sizes.items(), key=lambda item: (_PHASE_SORT.get(item[0], 99), item[0])):
        phase_median = round(median(values))
        if phase_median > PROMPT_BLOAT_THRESHOLD:
            prompt_bloat_watch.append(
                {
                    "phase": phase_name,
                    "median_prompt_chars": phase_median,
                    "calls": len(values),
                }
            )

    per_phase = [
        _bucket_to_dict(name, bucket)
        for name, bucket in sorted(by_phase.items(), key=lambda item: (_PHASE_SORT.get(item[0], 99), item[0]))
    ]
    per_model = [
        _bucket_to_dict(name, bucket)
        for name, bucket in sorted(
            by_model.items(),
            key=lambda item: (-float(item[1]["cost_usd_est"]), item[0]),
        )
    ]
    top_modules = [
        _bucket_to_dict(name, bucket)
        for name, bucket in sorted(
            by_module.items(),
            key=lambda item: (-float(item[1]["cost_usd_est"]), item[0]),
        )[:10]
    ]

    scope_parts = []
    if level or track:
        scope_parts.append(f"track={level or track}")
    if slug:
        scope_parts.append(f"module={slug}")
    if phase:
        scope_parts.append(f"phase={phase}")

    return {
        "scope": {
            "track": level or track,
            "slug": slug,
            "phase": phase,
            "label": ", ".join(scope_parts) if scope_parts else "all",
        },
        "since": _isoformat_z(since) if since else None,
        "records_total": len(filtered),
        "totals": _bucket_to_dict("total", totals),
        "per_phase": per_phase,
        "per_model": per_model,
        "top_modules": top_modules,
        "prompt_bloat_watch": prompt_bloat_watch,
        "warnings": warnings,
        "coverage": {
            "backfilled_prompt_records": counts["backfilled_prompt"],
            "backfilled_response_records": counts["backfilled_response"],
            "missing_prompt_records": counts["missing_prompt"],
            "missing_response_records": counts["missing_response"],
            "inferred_model_records": counts["model_agent"],
            "missing_model_records": counts["model_missing"],
        },
        "generated_at": _isoformat_z(datetime.now(UTC)),
    }


def build_cost_windows(
    *,
    root: Path | None = None,
    rates_path: Path | None = None,
    track: str | None = None,
    level: str | None = None,
    slug: str | None = None,
    phase: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    current_time = now or datetime.now(UTC)
    records = load_cost_records(root=root, rates_path=rates_path)
    windows: dict[str, Any] = {}
    for key, days in _WINDOW_SPECS:
        since = None if days is None else current_time - timedelta(days=days)
        windows[key] = build_cost_summary(
            records=records,
            track=track,
            level=level,
            slug=slug,
            phase=phase,
            since=since,
        )
    return {
        "scope": {
            "track": level or track,
            "slug": slug,
            "phase": phase,
        },
        "generated_at": _isoformat_z(current_time),
        "windows": windows,
    }


def format_module_cost_summary(level: str, slug: str) -> str | None:
    summary = build_cost_summary(level=level, slug=slug)
    total = float(summary["totals"]["cost_usd_est"])
    if total <= 0:
        return None

    phase_costs = {item["name"]: float(item["cost_usd_est"]) for item in summary["per_phase"]}
    writer_cost = sum(phase_costs.get(name, 0.0) for name in _WRITER_PHASES)
    review_cost = phase_costs.get("review", 0.0)
    enrich_cost = phase_costs.get("enrich", 0.0)

    parts = []
    if writer_cost > 0:
        parts.append(f"writer: ${writer_cost:.2f}")
    if review_cost > 0:
        parts.append(f"review: ${review_cost:.2f}")
    if enrich_cost > 0:
        parts.append(f"enrich: ${enrich_cost:.2f}")

    if parts:
        return f"💰 Cost: ~${total:.2f} USD ({', '.join(parts)})"
    return f"💰 Cost: ~${total:.2f} USD"


def _fmt_int(value: int) -> str:
    return f"{value:,}"


def _fmt_cost(value: float) -> str:
    return f"~${value:.2f}"


def _ansi(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    fmt = "  ".join("{:<" + str(width) + "}" for width in widths)
    lines = [fmt.format(*headers), fmt.format(*["-" * width for width in widths])]
    lines.extend(fmt.format(*row) for row in rows)
    return "\n".join(lines)


def render_terminal(summary: dict[str, Any]) -> str:
    totals = summary["totals"]
    lines = [
        _ansi("1;36", f"Estimated cost report [{summary['scope']['label']}]"),
        f"Calls: {totals['calls']}  Prompt est.: {_fmt_int(totals['prompt_tokens_est'])}  "
        f"Output est.: {_fmt_int(totals['response_tokens_est'])}  "
        f"Cost est.: {_ansi('1;32', _fmt_cost(float(totals['cost_usd_est'])) + ' USD')}",
    ]
    if summary["since"]:
        lines.append(f"Since mtime: {summary['since']}")
    if summary["warnings"]:
        lines.append(_ansi("1;33", "Warnings"))
        lines.extend(f"- {warning}" for warning in summary["warnings"])

    if summary["per_phase"]:
        phase_rows = [
            [
                item["name"],
                str(item["calls"]),
                _fmt_int(int(item["prompt_tokens_est"])),
                _fmt_int(int(item["response_tokens_est"])),
                _fmt_cost(float(item["cost_usd_est"])),
            ]
            for item in summary["per_phase"]
        ]
        lines.append(_ansi("1;34", "Per-Phase"))
        lines.append(_table(["phase", "calls", "prompt est.", "output est.", "usd est."], phase_rows))

    if summary["per_model"]:
        model_rows = [
            [
                item["name"],
                str(item["calls"]),
                _fmt_int(int(item["prompt_tokens_est"])),
                _fmt_int(int(item["response_tokens_est"])),
                _fmt_cost(float(item["cost_usd_est"])),
            ]
            for item in summary["per_model"]
        ]
        lines.append(_ansi("1;34", "Per-Model"))
        lines.append(_table(["model", "calls", "prompt est.", "output est.", "usd est."], model_rows))

    if summary["top_modules"]:
        module_rows = [
            [
                item["name"],
                str(item["calls"]),
                _fmt_int(int(item["prompt_tokens_est"])),
                _fmt_int(int(item["response_tokens_est"])),
                _fmt_cost(float(item["cost_usd_est"])),
            ]
            for item in summary["top_modules"]
        ]
        lines.append(_ansi("1;34", "Top 10 Modules"))
        lines.append(_table(["module", "calls", "prompt est.", "output est.", "usd est."], module_rows))

    if summary["prompt_bloat_watch"]:
        lines.append(_ansi("1;31", "Prompt Bloat Watch"))
        lines.extend(
            f"- {item['phase']}: median prompt_chars={_fmt_int(int(item['median_prompt_chars']))} across {item['calls']} call(s)"
            for item in summary["prompt_bloat_watch"]
        )

    return "\n".join(lines)


def render_markdown(summary: dict[str, Any]) -> str:
    totals = summary["totals"]
    lines = [
        f"## Estimated Cost Report `{summary['scope']['label']}`",
        "",
        f"- Calls: {totals['calls']}",
        f"- Prompt tokens est.: {_fmt_int(int(totals['prompt_tokens_est']))}",
        f"- Output tokens est.: {_fmt_int(int(totals['response_tokens_est']))}",
        f"- USD est.: {_fmt_cost(float(totals['cost_usd_est']))} USD",
    ]
    if summary["since"]:
        lines.append(f"- Since mtime: {summary['since']}")
    if summary["warnings"]:
        lines.extend(["", "### Warnings"])
        lines.extend(f"- {warning}" for warning in summary["warnings"])

    def add_table(title: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        lines.extend([
            "",
            f"### {title}",
            "",
            "| Name | Calls | Prompt est. | Output est. | USD est. |",
            "| --- | ---: | ---: | ---: | ---: |",
        ])
        for row in rows:
            lines.append(
                f"| {row['name']} | {row['calls']} | {_fmt_int(int(row['prompt_tokens_est']))} | "
                f"{_fmt_int(int(row['response_tokens_est']))} | {_fmt_cost(float(row['cost_usd_est']))} |"
            )

    add_table("Per-Phase", summary["per_phase"])
    add_table("Per-Model", summary["per_model"])
    add_table("Top 10 Most Expensive Modules", summary["top_modules"])

    if summary["prompt_bloat_watch"]:
        lines.extend(["", "### Prompt Bloat Watch"])
        lines.extend(
            f"- `{item['phase']}` median prompt_chars={_fmt_int(int(item['median_prompt_chars']))} across {item['calls']} call(s)"
            for item in summary["prompt_bloat_watch"]
        )
    return "\n".join(lines)


def _parse_module_arg(value: str) -> tuple[str, str]:
    level, sep, slug = value.partition("/")
    if not sep or not level or not slug:
        raise ValueError(f"Invalid --module value: {value!r}. Expected LEVEL/slug.")
    return level, slug


def _summary_from_args(args: argparse.Namespace) -> dict[str, Any]:
    since = _parse_since_date(args.since) if args.since else None
    if args.module:
        level, slug = _parse_module_arg(args.module)
        return build_cost_summary(level=level, slug=slug, since=since)
    if args.track:
        return build_cost_summary(track=args.track, since=since)
    if args.phase:
        return build_cost_summary(phase=args.phase, since=since)
    return build_cost_summary(since=since)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estimate dispatch token usage and USD cost from meta logs.")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--track", help="Track / level id, e.g. a1")
    scope.add_argument("--module", help="Module path, e.g. a1/my-family")
    scope.add_argument("--phase", help="Phase name across all modules, e.g. write")
    scope.add_argument("--all", action="store_true", help="Grand total across all dispatch meta")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    output.add_argument("--markdown", action="store_true", help="Emit Markdown")
    parser.add_argument("--since", help="Filter by meta file mtime, YYYY-MM-DD")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        summary = _summary_from_args(args)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    elif args.markdown:
        print(render_markdown(summary))
    else:
        print(render_terminal(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
