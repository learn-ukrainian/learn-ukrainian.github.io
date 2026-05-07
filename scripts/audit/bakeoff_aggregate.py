#!/usr/bin/env python3
"""Aggregate bakeoff writer/reviewer telemetry into a comparison report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

try:
    from scripts.build.linear_pipeline import _TOOL_CITATION_RE
except ImportError:
    _TOOL_CITATION_RE = re.compile(
        r"`?(?P<name>(?:mcp__sources__|search_|verify_|check_|query_|translate_)\w+)`?"
    )

REPO_ROOT = Path(__file__).resolve().parents[2]
PLANS_ROOT = REPO_ROOT / "curriculum" / "l2-uk-en" / "plans"

EXPECTED_COT_FIELDS = frozenset(
    {
        "word_budget",
        "plan_vocab",
        "register",
        "teaching_sequence",
    }
)

CONTENT_DIMS: tuple[str, ...] = (
    "immersion",
    "word count",
    "naturalness",
    "activity quality",
    "vocabulary",
    "plan adherence",
)

CONTENT_WEIGHTS: dict[str, float] = {
    "immersion": 0.25,
    "word count": 0.15,
    "naturalness": 0.20,
    "activity quality": 0.15,
    "vocabulary": 0.10,
    "plan adherence": 0.15,
}

CORE_TOOLS: tuple[str, ...] = (
    "verify_words",
    "search_definitions",
    "search_definitions_slovnyk",
    "search_grinchenko_1907",
    "search_literary",
    "search_style_guide",
)

REVIEW_AUDIT_TYPES: tuple[str, ...] = (
    "source_attribution",
    "quote_verification",
    "sovietization_check",
    "modern_form_check",
)

ARCHAIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("тії", re.compile(r"\bтії\b", re.IGNORECASE)),
    ("сей/сія/сії", re.compile(r"\b(?:сей|сія|сії)\b", re.IGNORECASE)),
    ("standalone ся", re.compile(r"(?<![\w-])ся(?![\w-])", re.IGNORECASE)),
    ("іже", re.compile(r"\bіже\b", re.IGNORECASE)),
)

DIM_ALIASES: dict[str, str] = {
    "activity": "activity quality",
    "activity_quality": "activity quality",
    "activity-quality": "activity quality",
    "activity quality": "activity quality",
    "activities": "activity quality",
    "exercise quality": "activity quality",
    "immersion": "immersion",
    "language immersion": "immersion",
    "naturalness": "naturalness",
    "plan": "plan adherence",
    "plan_adherence": "plan adherence",
    "plan-adherence": "plan adherence",
    "plan adherence": "plan adherence",
    "vocab": "vocabulary",
    "vocabulary": "vocabulary",
    "vocabulary coverage": "vocabulary",
    "word_count": "word count",
    "word-count": "word count",
    "word count": "word count",
    "words": "word count",
}

TOOL_ALIASES: dict[str, str] = {
    "mcp__sources__verify_words": "verify_words",
    "mcp__sources__search_definitions": "search_definitions",
    "mcp__sources__search_definitions_slovnyk": "search_definitions_slovnyk",
    "mcp__sources__search_grinchenko_1907": "search_grinchenko_1907",
    "mcp__sources__search_literary": "search_literary",
    "mcp__sources__search_style_guide": "search_style_guide",
}


@dataclass
class PlanInfo:
    path: Path | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def word_target(self) -> int | None:
        value = self.data.get("word_target")
        if isinstance(value, int | float):
            return int(value)
        return None

    @property
    def display_path(self) -> str:
        if not self.path:
            return "unresolved"
        return self.path.relative_to(REPO_ROOT).as_posix()


@dataclass
class WriterData:
    name: str
    markdown_path: Path
    telemetry_path: Path
    text: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def telemetry_present(self) -> bool:
        return any(str(event.get("event", "")).startswith("writer_") for event in self.events) or any(
            event.get("event") == "phase_writer_summary" for event in self.events
        )

    @property
    def word_count(self) -> int:
        if not self.text:
            return 0
        return count_words(self.text)


@dataclass
class ReviewRun:
    writer: str
    reviewer: str
    path: Path
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def telemetry_present(self) -> bool:
        return any(str(event.get("event", "")).startswith("reviewer_") for event in self.events) or any(
            event.get("event") == "phase_review_summary" for event in self.events
        )


@dataclass
class BakeoffData:
    bakeoff_dir: Path
    writers: list[str]
    writer_data: dict[str, WriterData]
    review_runs: list[ReviewRun]
    plan: PlanInfo
    warnings: list[str]
    reviewer_protocol_broken: list[str] = field(default_factory=list)


def normalize_agent(raw: Any) -> str:
    value = str(raw or "").strip().casefold()
    value = value.replace("_tools", "-tools").removesuffix("-tools")
    value = value.replace(" ", "-")
    if "gemini" in value:
        return "gemini"
    if "claude" in value:
        return "claude"
    if "codex" in value or "gpt" in value or "openai" in value:
        return "gpt55"
    return value


def normalize_tool(raw: Any) -> str:
    value = str(raw or "").strip()
    if value in TOOL_ALIASES:
        return TOOL_ALIASES[value]
    if "__" in value:
        value = value.rsplit("__", 1)[-1]
    return value


def normalize_dim(raw: Any) -> str:
    value = re.sub(r"\s+", " ", str(raw or "").strip().casefold())
    value = value.removeprefix("dim ").strip()
    value = re.sub(r"^\d+[.)]\s*", "", value)
    return DIM_ALIASES.get(value, value)


def warn(warnings: list[str], message: str) -> None:
    warnings.append(message)
    print(f"warning: {message}", file=sys.stderr)


def read_jsonl(path: Path, warnings: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        warn(warnings, f"missing JSONL file: {path}")
        return []

    events: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text("utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            warn(warnings, f"malformed JSONL skipped: {path}:{line_no}: {exc.msg}")
            continue
        if not isinstance(payload, dict):
            warn(warnings, f"non-object JSONL skipped: {path}:{line_no}")
            continue
        if "event" not in payload:
            continue
        events.append(payload)
    return events


def count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-zА-Яа-яІіЇїЄєҐґ0-9]+(?:[-'][A-Za-zА-Яа-яІіЇїЄєҐґ0-9]+)?", text))


def parse_writer_list(raw: str) -> list[str]:
    writers = [normalize_agent(part) for part in raw.split(",") if part.strip()]
    deduped: list[str] = []
    for writer in writers:
        if writer and writer not in deduped:
            deduped.append(writer)
    return deduped


def collect_bakeoff_data(bakeoff_dir: Path, writers: list[str]) -> BakeoffData:
    warnings: list[str] = []
    writer_data: dict[str, WriterData] = {}
    for writer in writers:
        markdown_path = bakeoff_dir / f"{writer}.md"
        telemetry_path = bakeoff_dir / f"{writer}.write.jsonl"
        text = None
        if markdown_path.exists():
            text = markdown_path.read_text("utf-8")
        else:
            warn(warnings, f"missing writer markdown: {markdown_path}")
        events = read_jsonl(telemetry_path, warnings)
        writer_data[writer] = WriterData(
            name=writer,
            markdown_path=markdown_path,
            telemetry_path=telemetry_path,
            text=text,
            events=events,
        )
        if telemetry_path.exists() and not writer_data[writer].telemetry_present:
            warn(warnings, f"no writer telemetry events found in: {telemetry_path}")

    review_runs: list[ReviewRun] = []
    protocol_broken: list[str] = []
    seen_pairs: set[tuple[str, str]] = set()
    for path in sorted(bakeoff_dir.glob("*.review.jsonl")):
        match = re.fullmatch(r"(?P<writer>.+)-(?P<reviewer>.+)\.review\.jsonl", path.name)
        if not match:
            warn(warnings, f"review JSONL filename does not match <writer>-<reviewer>.review.jsonl: {path}")
            continue
        writer = normalize_agent(match.group("writer"))
        reviewer = normalize_agent(match.group("reviewer"))
        if writer not in writers or reviewer not in writers:
            warn(warnings, f"review JSONL ignored for agent outside --writers: {path}")
            continue
        seen_pairs.add((writer, reviewer))
        run = ReviewRun(
            writer=writer,
            reviewer=reviewer,
            path=path,
            events=read_jsonl(path, warnings),
        )
        review_runs.append(run)
        if any(event.get("event") == "reviewer_fixes_unparseable" for event in run.events):
            protocol_broken.append(f"{writer}-{reviewer} ({path.name})")
        if not run.telemetry_present:
            warn(warnings, f"no reviewer telemetry events found in: {path}")

    for writer in writers:
        for reviewer in writers:
            if writer == reviewer:
                continue
            expected = bakeoff_dir / f"{writer}-{reviewer}.review.jsonl"
            if (writer, reviewer) not in seen_pairs:
                warn(warnings, f"missing review JSONL file: {expected}")

    for writer, info in writer_data.items():
        warn_on_tool_count_drift(writer, info, warnings)

    plan = resolve_plan(writer_data.values(), review_runs, warnings)
    return BakeoffData(
        bakeoff_dir=bakeoff_dir,
        writers=writers,
        writer_data=writer_data,
        review_runs=review_runs,
        plan=plan,
        warnings=warnings,
        reviewer_protocol_broken=protocol_broken,
    )


def resolve_plan(
    writers: Iterable[WriterData],
    reviews: Iterable[ReviewRun],
    warnings: list[str],
) -> PlanInfo:
    module_ids: list[str] = []
    for writer in writers:
        module_ids.extend(str(event["module"]) for event in writer.events if event.get("module"))
        if writer.text:
            frontmatter = parse_frontmatter(writer.text)
            level = frontmatter.get("level")
            slug = frontmatter.get("slug")
            if level and slug:
                module_ids.append(f"{level}/{slug}")
            module = frontmatter.get("module")
            if level and module:
                module_ids.append(f"{level}/{module}")
    for review in reviews:
        module_ids.extend(str(event["module"]) for event in review.events if event.get("module"))

    for module_id in sorted(dict.fromkeys(module_ids)):
        plan = plan_from_module_id(module_id, warnings)
        if plan.path:
            return plan

    warn(warnings, "could not resolve plan YAML from telemetry module fields or markdown front matter")
    return PlanInfo()


def parse_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    match = re.match(r"^---\s*\n(?P<body>.*?)\n---\s*(?:\n|\Z)", text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        payload = yaml.safe_load(match.group("body"))
    except yaml.YAMLError:
        return {}
    return payload if isinstance(payload, dict) else {}


def plan_from_module_id(module_id: str, warnings: list[str]) -> PlanInfo:
    match = re.search(r"(?P<level>[A-Za-z]+\d?|[A-Za-z]+)[/-](?P<slug>[A-Za-z0-9_-]+)$", module_id.strip())
    if not match:
        return PlanInfo()
    level = match.group("level").casefold()
    slug_or_sequence = match.group("slug")

    direct = PLANS_ROOT / level / f"{slug_or_sequence}.yaml"
    if direct.exists():
        return load_plan(direct, warnings)

    if slug_or_sequence.isdigit():
        sequence = int(slug_or_sequence)
        plan = plan_by_sequence(level, sequence, warnings)
        if plan.path:
            return plan

    module_match = re.fullmatch(rf"{re.escape(level)}-(?P<sequence>\d+)", slug_or_sequence.casefold())
    if module_match:
        plan = plan_by_sequence(level, int(module_match.group("sequence")), warnings)
        if plan.path:
            return plan

    return PlanInfo()


def plan_by_sequence(level: str, sequence: int, warnings: list[str]) -> PlanInfo:
    level_dir = PLANS_ROOT / level
    if not level_dir.is_dir():
        return PlanInfo()
    module_ids = {f"{level}-{sequence:03d}", f"{level}-{sequence}"}
    for path in sorted(level_dir.glob("*.yaml")):
        try:
            payload = yaml.safe_load(path.read_text("utf-8"))
        except yaml.YAMLError as exc:
            warn(warnings, f"could not parse plan while resolving module {level}/{sequence}: {path}: {exc}")
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("sequence") == sequence or str(payload.get("module", "")).casefold() in module_ids:
            return PlanInfo(path=path, data=payload)
    return PlanInfo()


def load_plan(path: Path, warnings: list[str]) -> PlanInfo:
    try:
        payload = yaml.safe_load(path.read_text("utf-8"))
    except yaml.YAMLError as exc:
        warn(warnings, f"could not parse plan YAML: {path}: {exc}")
        return PlanInfo(path=path)
    return PlanInfo(path=path, data=payload if isinstance(payload, dict) else {})


def score_from_fraction(fraction: float) -> int:
    if fraction <= 0:
        return 0
    if fraction >= 0.98:
        return 3
    if fraction >= 0.66:
        return 2
    return 1


def format_score(score: int, detail: str = "") -> str:
    suffix = f" ({detail})" if detail else ""
    return f"{score}{suffix}"


def event_summary(writer: WriterData) -> dict[str, Any] | None:
    for event in reversed(writer.events):
        if event.get("event") == "phase_writer_summary":
            return event
    return None


def writer_tool_events(writer: WriterData) -> list[dict[str, Any]]:
    return [event for event in writer.events if event.get("event") == "writer_tool_call"]


def writer_tool_counts(writer: WriterData) -> Counter[str]:
    return Counter(normalize_tool(event.get("tool")) for event in writer_tool_events(writer))


def writer_tool_total(writer: WriterData) -> int:
    summary = event_summary(writer)
    if summary and isinstance(summary.get("tool_calls_total"), int | float):
        return int(summary["tool_calls_total"])
    return sum(writer_tool_counts(writer).values())


def warn_on_tool_count_drift(writer_name: str, writer: WriterData, warnings: list[str]) -> None:
    summary = event_summary(writer)
    if not summary or not isinstance(summary.get("tool_calls_total"), int | float):
        return
    summary_total = int(summary["tool_calls_total"])
    event_total = sum(writer_tool_counts(writer).values())
    if summary_total != event_total:
        warn(
            warnings,
            (
                f"writer tool-call total drift for {writer_name}: "
                f"phase_writer_summary.tool_calls_total={summary_total}, writer_tool_call events={event_total}"
            ),
        )


def writer_theatre_violation_count(writer: WriterData) -> int:
    summary = event_summary(writer)
    summary_count: int | None = None
    if summary and isinstance(summary.get("tool_theatre_violation_count"), int | float):
        summary_count = int(summary["tool_theatre_violation_count"])
    event_count = 0
    for event in writer.events:
        if event.get("event") != "writer_tool_theatre":
            continue
        violations = event.get("violations")
        event_count += len(violations) if isinstance(violations, list) else 1
    if summary_count is None:
        return event_count
    return max(summary_count, event_count)


def normalize_tool_citation(raw_tool: Any) -> str:
    return normalize_tool(str(raw_tool or "").removeprefix("mcp__sources__"))


def cited_tool_names(text: str | None) -> set[str]:
    if not text:
        return set()
    return {normalize_tool_citation(citation) for citation in _TOOL_CITATION_RE.findall(text)}


def writer_cites_tools_with_zero_calls(writer: WriterData) -> bool:
    return (
        writer.telemetry_present
        and writer_tool_total(writer) == 0
        and bool(cited_tool_names(writer.text))
    )


def cot_score(writer: WriterData) -> tuple[int | None, str]:
    if not writer.telemetry_present:
        return None, "telemetry absent"
    cot_events = [event for event in writer.events if event.get("event") == "writer_cot_emit"]
    if not cot_events:
        return 0, "0 sections"
    summary = event_summary(writer)
    sections_total = int(summary.get("sections_total", len(cot_events))) if summary else len(cot_events)
    sections_total = max(sections_total, len(cot_events), 1)
    sections_with_cot = int(summary.get("sections_with_cot", 0)) if summary else 0
    if not summary:
        sections_with_cot = sum(1 for event in cot_events if event.get("block_present"))
    filled_total = 0
    for event in cot_events:
        fields = event.get("fields_filled")
        if isinstance(fields, list):
            filled_total += len(set(str(field) for field in fields) & EXPECTED_COT_FIELDS)
    field_fraction = filled_total / (sections_total * len(EXPECTED_COT_FIELDS))
    block_fraction = sections_with_cot / sections_total
    score = score_from_fraction(field_fraction * block_fraction)
    return score, f"{sections_with_cot}/{sections_total} sections; {filled_total} fields"


def verify_density_score(writer: WriterData) -> tuple[int | None, str]:
    if not writer.telemetry_present:
        return None, "telemetry absent"
    summary = event_summary(writer)
    calls = None
    if summary and isinstance(summary.get("verify_words_calls"), int | float):
        calls = int(summary["verify_words_calls"])
    if calls is None:
        calls = writer_tool_counts(writer).get("verify_words", 0)
    density = calls_per_100(calls, writer.word_count)
    if calls <= 0:
        if writer_cites_tools_with_zero_calls(writer):
            return 0, "0 calls; cites tool names"
        return 0, "0 calls"
    if density >= 0.25:
        score = 3
    elif density >= 0.10:
        score = 2
    else:
        score = 1
    return score, f"{density:.2f}/100w"


def modern_ukrainian_score(writer: WriterData) -> tuple[int | None, str]:
    if writer.text is None:
        return None, "missing output"
    hits = archaic_hits(writer.text)
    if hits:
        return 0, ", ".join(hits[:3])
    return 3, "no flagged archaic forms"


def archaic_hits(text: str) -> list[str]:
    hits: list[str] = []
    for label, pattern in ARCHAIC_PATTERNS:
        if pattern.search(text):
            hits.append(label)
    return hits


def source_discipline_score(writer: WriterData) -> tuple[int | None, str]:
    if not writer.telemetry_present:
        return None, "telemetry absent"
    tool_events = writer_tool_events(writer)
    if not tool_events:
        return 0, "0 tool calls"
    success_count = sum(1 for event in tool_events if tool_call_succeeded(event))
    ratio = success_count / len(tool_events)
    if ratio >= 0.95:
        score = 3
    elif ratio >= 0.75:
        score = 2
    elif ratio > 0:
        score = 1
    else:
        score = 0
    return score, f"{success_count}/{len(tool_events)} success"


def tool_call_succeeded(event: Mapping[str, Any]) -> bool:
    summary = event.get("result_summary")
    if not isinstance(summary, Mapping):
        return False
    failed = summary.get("failed", 0)
    items_failed = summary.get("items_failed", 0)
    if isinstance(failed, int | float) and failed > 0:
        return False
    if isinstance(items_failed, int | float) and items_failed > 0:
        return False
    if summary.get("failed_words"):
        return False
    return bool(summary)


def end_gate_score(writer: WriterData) -> tuple[int | None, str]:
    if not writer.telemetry_present:
        return None, "telemetry absent"
    for event in reversed(writer.events):
        if event.get("event") == "writer_end_gate":
            fired = bool(event.get("gate_present"))
            return (3 if fired else 0), f"gate_present={str(fired).lower()}"
    summary = event_summary(writer)
    fired = bool(summary and summary.get("end_gate_fired"))
    return (3 if fired else 0), f"end_gate_fired={str(fired).lower()}"


def theatre_clean_score(writer: WriterData) -> tuple[int | None, str]:
    if not writer.telemetry_present:
        return None, "telemetry absent"
    violations = writer_theatre_violation_count(writer)
    if violations:
        return 0, f"{violations} violation(s)"
    return 3, "0 violations"


def writer_prompt_scores(data: BakeoffData) -> dict[str, dict[str, int | None]]:
    rows = {
        "CoT block usage (writer_cot_emit fields_filled)": cot_score,
        "verify_words density (calls per 100 words)": verify_density_score,
        "Modern-Ukrainian compliance (no archaic forms in output)": modern_ukrainian_score,
        "Source-citation discipline (writer_tool_call success ratio)": source_discipline_score,
        "End-gate fired (writer_end_gate gate_present)": end_gate_score,
        "Tool-theatre clean": theatre_clean_score,
    }
    scores: dict[str, dict[str, int | None]] = {writer: {} for writer in data.writers}
    for label, scorer in rows.items():
        for writer in data.writers:
            score, _detail = scorer(data.writer_data[writer])
            scores[writer][label] = score
    return scores


def writer_prompt_table(data: BakeoffData) -> tuple[str, dict[str, dict[str, int | None]]]:
    rows = {
        "CoT block usage (writer_cot_emit fields_filled)": cot_score,
        "verify_words density (calls per 100 words)": verify_density_score,
        "Modern-Ukrainian compliance (no archaic forms in output)": modern_ukrainian_score,
        "Source-citation discipline (writer_tool_call success ratio)": source_discipline_score,
        "End-gate fired (writer_end_gate gate_present)": end_gate_score,
        "Tool-theatre clean": theatre_clean_score,
    }
    score_map: dict[str, dict[str, int | None]] = {writer: {} for writer in data.writers}
    table_rows: list[list[str]] = []
    for label, scorer in rows.items():
        row = [label]
        for writer in data.writers:
            score, detail = scorer(data.writer_data[writer])
            score_map[writer][label] = score
            row.append(detail if score is None else format_score(score, detail))
        table_rows.append(row)
    return markdown_table(["sub-dim", *data.writers], table_rows), score_map


def review_runs_by_reviewer(data: BakeoffData) -> dict[str, list[ReviewRun]]:
    grouped: dict[str, list[ReviewRun]] = {reviewer: [] for reviewer in data.writers}
    for run in data.review_runs:
        grouped.setdefault(run.reviewer, []).append(run)
    return grouped


def reviewer_events(runs: Iterable[ReviewRun], event_name: str) -> list[dict[str, Any]]:
    return [event for run in runs for event in run.events if event.get("event") == event_name]


def reviewer_has_telemetry(runs: Iterable[ReviewRun]) -> bool:
    return any(run.telemetry_present for run in runs)


def reviewer_per_dim_cot_score(runs: list[ReviewRun]) -> tuple[int | None, str]:
    if not reviewer_has_telemetry(runs):
        return None, "telemetry absent"
    dim_events = reviewer_events(runs, "reviewer_dim_evidence")
    if not dim_events:
        return 0, "0 dim events"
    good = 0
    for event in dim_events:
        quotes = event.get("evidence_quotes")
        if isinstance(quotes, list) and len(quotes) >= 2:
            good += 1
    return score_from_fraction(good / len(dim_events)), f"{good}/{len(dim_events)} dims"


def reviewer_audit_calls_score(runs: list[ReviewRun]) -> tuple[int | None, str]:
    if not reviewer_has_telemetry(runs):
        return None, "telemetry absent"
    calls = reviewer_events(runs, "reviewer_audit_call")
    if not calls:
        return 0, "0 calls"
    counts = Counter(str(event.get("audit_type", "unknown")) for event in calls)
    covered_types = sum(1 for audit_type in REVIEW_AUDIT_TYPES if counts.get(audit_type, 0) > 0)
    score = score_from_fraction(covered_types / len(REVIEW_AUDIT_TYPES))
    detail = ", ".join(f"{audit_type}={counts[audit_type]}" for audit_type in sorted(counts))
    return score, detail


def reviewer_audit_type_score(runs: list[ReviewRun], audit_type: str) -> tuple[int | None, str]:
    if not reviewer_has_telemetry(runs):
        return None, "telemetry absent"
    calls = [event for event in reviewer_events(runs, "reviewer_audit_call") if event.get("audit_type") == audit_type]
    checked = sum(int(event.get("items_checked", 0) or 0) for event in calls)
    if checked <= 0:
        return 0, "0 checked"
    failed = sum(int(event.get("items_failed", 0) or 0) for event in calls)
    return 3, f"{checked} checked; {failed} failed"


def reviewed_writers_for_runs(runs: Iterable[ReviewRun]) -> set[str]:
    return {run.writer for run in runs}


def reviewer_sovietization_score(runs: list[ReviewRun], data: BakeoffData) -> tuple[int | None, str]:
    if not reviewer_has_telemetry(runs):
        return None, "telemetry absent"
    reviewed = reviewed_writers_for_runs(runs)
    applicable = any(
        writer_tool_counts(data.writer_data[writer]).get("search_definitions", 0) > 0
        or writer_tool_counts(data.writer_data[writer]).get("search_definitions_slovnyk", 0) > 0
        for writer in reviewed
        if writer in data.writer_data
    )
    calls = [event for event in reviewer_events(runs, "reviewer_audit_call") if event.get("audit_type") == "sovietization_check"]
    flags = sum(len(event.get("flags_raised", []) or []) for event in calls)
    if not applicable and not calls:
        return None, "n/a"
    if flags:
        return 3, f"{flags} flags"
    if calls:
        return 2, f"{len(calls)} audits; 0 flags"
    return 0, "applicable; no audit"


def reviewer_modern_form_score(runs: list[ReviewRun], data: BakeoffData) -> tuple[int | None, str]:
    if not reviewer_has_telemetry(runs):
        return None, "telemetry absent"
    reviewed = reviewed_writers_for_runs(runs)
    applicable = any(
        data.writer_data[writer].text and archaic_hits(data.writer_data[writer].text)
        for writer in reviewed
        if writer in data.writer_data
    )
    calls = [event for event in reviewer_events(runs, "reviewer_audit_call") if event.get("audit_type") == "modern_form_check"]
    if not applicable and not calls:
        return None, "n/a"
    if calls:
        checked = sum(int(event.get("items_checked", 0) or 0) for event in calls)
        return 3, f"{checked} checked"
    return 0, "applicable; no audit"


def reviewer_prompt_table(data: BakeoffData) -> str:
    grouped = review_runs_by_reviewer(data)
    rows: list[tuple[str, Any]] = [
        ("Per-dim CoT (reviewer_dim_evidence count >=2)", reviewer_per_dim_cot_score),
        ("Audit calls (reviewer_audit_call count, by audit_type)", reviewer_audit_calls_score),
        ("Source-attribution audit coverage", lambda runs: reviewer_audit_type_score(runs, "source_attribution")),
        ("Quote-verification coverage", lambda runs: reviewer_audit_type_score(runs, "quote_verification")),
        ("Sovietization flag triggered (when applicable)", lambda runs: reviewer_sovietization_score(runs, data)),
        ("Modern-form guard (when applicable)", lambda runs: reviewer_modern_form_score(runs, data)),
    ]
    table_rows: list[list[str]] = []
    for label, scorer in rows:
        row = [label]
        for reviewer in data.writers:
            score, detail = scorer(grouped.get(reviewer, []))
            row.append(detail if score is None else format_score(score, detail))
        table_rows.append(row)
    return markdown_table(["sub-dim", *data.writers], table_rows)


def review_scores(data: BakeoffData) -> dict[str, dict[str, dict[str, float]]]:
    scores: dict[str, dict[str, dict[str, float]]] = {
        writer: {reviewer: {} for reviewer in data.writers} for writer in data.writers
    }
    for run in data.review_runs:
        for event in run.events:
            if event.get("event") != "reviewer_dim_evidence":
                continue
            try:
                score = float(event["score"])
            except (KeyError, TypeError, ValueError):
                continue
            dim = normalize_dim(event.get("dim"))
            scores.setdefault(run.writer, {}).setdefault(run.reviewer, {})[dim] = score
    return scores


def review_summary_scores(data: BakeoffData) -> dict[str, dict[str, float]]:
    summaries: dict[str, dict[str, float]] = {writer: {} for writer in data.writers}
    for run in data.review_runs:
        for event in run.events:
            if event.get("event") != "phase_review_summary":
                continue
            try:
                summaries.setdefault(run.writer, {})[run.reviewer] = float(event["weighted_score"])
            except (KeyError, TypeError, ValueError):
                continue
    return summaries


def content_dim_values(data: BakeoffData) -> dict[str, dict[str, float]]:
    raw_scores = review_scores(data)
    values: dict[str, dict[str, float]] = {writer: {} for writer in data.writers}
    for writer in data.writers:
        for dim in CONTENT_DIMS:
            dim_scores = [
                reviewer_scores[dim]
                for reviewer_scores in raw_scores.get(writer, {}).values()
                if dim in reviewer_scores
            ]
            if dim_scores:
                values[writer][dim] = round(mean(dim_scores), 2)

        if "word count" not in values[writer]:
            deterministic = word_count_score(data.writer_data[writer], data.plan)
            if deterministic is not None:
                values[writer]["word count"] = deterministic
    return values


def word_count_score(writer: WriterData, plan: PlanInfo) -> float | None:
    target = plan.word_target
    if not target or writer.word_count <= 0:
        return None
    return round(min(10.0, writer.word_count / target * 10.0), 2)


def content_weighted_scores(data: BakeoffData) -> dict[str, float | None]:
    values = content_dim_values(data)
    raw_scores = review_scores(data)
    summary_scores = review_summary_scores(data)
    weighted: dict[str, float | None] = {}
    for writer in data.writers:
        observed_content_dims = {
            dim
            for reviewer_scores in raw_scores.get(writer, {}).values()
            for dim in reviewer_scores
            if dim in CONTENT_DIMS
        }
        if not observed_content_dims:
            summaries = list(summary_scores.get(writer, {}).values())
            if summaries:
                weighted[writer] = round(mean(summaries), 2)
                continue

        present = {dim: values[writer][dim] for dim in CONTENT_DIMS if dim in values[writer]}
        if present:
            total_weight = sum(CONTENT_WEIGHTS[dim] for dim in present)
            weighted[writer] = round(
                sum(score * CONTENT_WEIGHTS[dim] for dim, score in present.items()) / total_weight,
                2,
            )
            continue
        weighted[writer] = None
    return weighted


def content_min_dims(data: BakeoffData) -> dict[str, tuple[str, float] | None]:
    values = content_dim_values(data)
    result: dict[str, tuple[str, float] | None] = {}
    for writer in data.writers:
        present = {dim: values[writer][dim] for dim in CONTENT_DIMS if dim in values[writer]}
        if not present:
            result[writer] = None
            continue
        min_dim = min(present, key=present.__getitem__)
        result[writer] = (min_dim, present[min_dim])
    return result


def content_quality_table(data: BakeoffData) -> str:
    values = content_dim_values(data)
    weighted = content_weighted_scores(data)
    min_dims = content_min_dims(data)
    table_rows: list[list[str]] = []
    for dim in CONTENT_DIMS:
        row = [dim]
        for writer in data.writers:
            row.append(format_float(values[writer].get(dim)))
        table_rows.append(row)

    min_row = ["**min dim**"]
    for writer in data.writers:
        min_dim = min_dims[writer]
        min_row.append("n/a" if min_dim is None else f"{format_float(min_dim[1])} ({min_dim[0]})")
    table_rows.append(min_row)

    weighted_row = ["**weighted score**"]
    for writer in data.writers:
        weighted_row.append(format_float(weighted[writer]))
    table_rows.append(weighted_row)
    return markdown_table(["dim", *data.writers], table_rows)


def tool_usage_table(data: BakeoffData) -> str:
    all_tools = sorted(
        {
            tool
            for writer in data.writers
            for tool in writer_tool_counts(data.writer_data[writer])
            if tool
        }
    )
    extra_tools = [tool for tool in all_tools if tool not in CORE_TOOLS]
    table_tools = [*CORE_TOOLS, *extra_tools]
    table_rows: list[list[str]] = []
    for tool in table_tools:
        row = [tool]
        for writer in data.writers:
            writer_info = data.writer_data[writer]
            if not writer_info.telemetry_present:
                row.append("telemetry absent")
            else:
                row.append(str(writer_tool_counts(writer_info).get(tool, 0)))
        table_rows.append(row)

    row = ["other tools used"]
    for writer in data.writers:
        writer_info = data.writer_data[writer]
        if not writer_info.telemetry_present:
            row.append("telemetry absent")
            continue
        counts = writer_tool_counts(writer_info)
        others = [f"{tool}={counts[tool]}" for tool in sorted(counts) if tool not in CORE_TOOLS]
        row.append(", ".join(others) if others else "none")
    table_rows.append(row)

    density_row = ["**calls per 100 words**"]
    for writer in data.writers:
        writer_info = data.writer_data[writer]
        if not writer_info.telemetry_present:
            density_row.append("telemetry absent")
        else:
            density_row.append(f"{calls_per_100(writer_tool_total(writer_info), writer_info.word_count):.2f}")
    table_rows.append(density_row)
    return markdown_table(["tool", *data.writers], table_rows)


def writer_tool_density(data: BakeoffData, writer: str) -> float:
    writer_info = data.writer_data[writer]
    return calls_per_100(writer_tool_total(writer_info), writer_info.word_count)


def writer_winner_verdict(data: BakeoffData, writer: str, min_dims: dict[str, tuple[str, float] | None]) -> str:
    min_dim = min_dims[writer]
    if min_dim is None:
        return "blocked: no min_dim"
    if min_dim[1] < 8:
        return "blocked: min_dim < 8"
    if writer_theatre_violation_count(data.writer_data[writer]) > 0:
        return "blocked: tool theatre"
    return "eligible"


def winner_ranking_table(data: BakeoffData) -> str:
    min_dims = content_min_dims(data)
    ranked = sorted(
        data.writers,
        key=lambda writer: (
            writer_winner_verdict(data, writer, min_dims) == "eligible",
            writer_tool_density(data, writer) * (min_dims[writer][1] if min_dims[writer] else 0),
            min_dims[writer][1] if min_dims[writer] else -1,
        ),
        reverse=True,
    )
    table_rows: list[list[str]] = []
    for writer in ranked:
        writer_info = data.writer_data[writer]
        min_dim = min_dims[writer]
        min_display = "n/a" if min_dim is None else f"{format_float(min_dim[1])} ({min_dim[0]})"
        table_rows.append(
            [
                writer,
                f"{writer_tool_density(data, writer):.2f}",
                str(writer_theatre_violation_count(writer_info)),
                min_display,
                writer_winner_verdict(data, writer, min_dims),
            ]
        )
    return markdown_table(["writer", "density", "theatre violations", "min_dim", "verdict"], table_rows)


def calls_per_100(calls: int, word_count: int) -> float:
    if calls <= 0 or word_count <= 0:
        return 0.0
    return calls / word_count * 100.0


def cross_reviewer_bias_table(data: BakeoffData) -> str:
    scores = review_scores(data)
    observed_dims = sorted(
        {
            dim
            for writer_scores in scores.values()
            for reviewer_scores in writer_scores.values()
            for dim in reviewer_scores
            if dim not in CONTENT_DIMS
        }
    )
    dims = [*CONTENT_DIMS, *observed_dims]
    table_rows: list[list[str]] = []
    for writer in data.writers:
        for dim in dims:
            row = [writer, dim]
            if dim not in CONTENT_DIMS and not any(
                dim in reviewer_scores for reviewer_scores in scores.get(writer, {}).values()
            ):
                continue
            for reviewer in data.writers:
                row.append(format_float(scores.get(writer, {}).get(reviewer, {}).get(dim)))
            table_rows.append(row)
    return markdown_table(["writer", "dim", *[f"score from {reviewer}" for reviewer in data.writers]], table_rows)


def findings_table(
    data: BakeoffData,
    writer_prompt_score_map: dict[str, dict[str, int | None]],
) -> str:
    findings = generated_findings(data, writer_prompt_score_map)
    return markdown_table(["finding", "recommendation"], findings)


def generated_findings(
    data: BakeoffData,
    writer_prompt_score_map: dict[str, dict[str, int | None]],
) -> list[list[str]]:
    rows: list[list[str]] = []
    min_dims = content_min_dims(data)
    prompt_totals = {
        writer: sum(score for score in writer_prompt_score_map[writer].values() if isinstance(score, int))
        for writer in data.writers
    }
    prompt_max = 3 * len(next(iter(writer_prompt_score_map.values()), {}))
    eligible_writers = [
        writer
        for writer in data.writers
        if min_dims[writer] is not None
        and min_dims[writer][1] >= 8
        and writer_theatre_violation_count(data.writer_data[writer]) == 0
    ]

    content_leader = max(
        eligible_writers,
        key=lambda writer: (
            writer_tool_density(data, writer) * (min_dims[writer][1] if min_dims[writer] else 0),
            min_dims[writer][1] if min_dims[writer] else -1,
        ),
        default=None,
    )
    adherence_leader = max(data.writers, key=lambda writer: prompt_totals.get(writer, -1), default=None)
    if content_leader:
        adherence_detail = ""
        if adherence_leader:
            adherence_detail = (
                f" Writer prompt adherence: {content_leader}={prompt_totals[content_leader]}/{prompt_max}; "
                f"adherence leader={adherence_leader} ({prompt_totals[adherence_leader]}/{prompt_max})."
            )
        rows.append(
            [
                (
                    f"Candidate winner: {content_leader} passes min-dim gate "
                    f"({format_float(min_dims[content_leader][1] if min_dims[content_leader] else None)}) "
                    f"and leads eligible writers by tool-call density x min_dim "
                    f"({writer_tool_density(data, content_leader):.2f}/100w)."
                    f"{adherence_detail}"
                ),
                "Use this writer as the default candidate unless manual review finds a blocking quality issue.",
            ]
        )
    else:
        rows.append(
            [
                "No candidate winner could be computed after the min-dim >= 8 and theatre-clean gates.",
                "Run at least one writer with passing content dimensions and clean telemetry.",
            ]
        )

    blocked = [
        f"{writer} ({writer_winner_verdict(data, writer, min_dims)})"
        for writer in data.writers
        if writer_winner_verdict(data, writer, min_dims) != "eligible"
    ]
    if blocked:
        rows.append(
            [
                "Winner gate excluded: " + "; ".join(blocked) + ".",
                "Do not select excluded writers even when their weighted score is high.",
            ]
        )

    suspicious_zero = [writer for writer in data.writers if writer_cites_tools_with_zero_calls(data.writer_data[writer])]
    if suspicious_zero:
        rows.append(
            [
                (
                    "writer cites tools but emitted zero calls - suspect cross-contamination/theatre: "
                    + ", ".join(suspicious_zero)
                    + "."
                ),
                "Treat the writer telemetry as invalid until the raw trace and markdown are reconciled.",
            ]
        )

    zero_rows = []
    for label in next(iter(writer_prompt_score_map.values()), {}):
        scores = [writer_prompt_score_map[writer].get(label) for writer in data.writers]
        if scores and all(score == 0 for score in scores):
            zero_rows.append(label)
    if zero_rows:
        rows.append(
            [
                "All writers scored 0 on: " + "; ".join(zero_rows) + ".",
                "Revise the writer prompt or telemetry contract for these sub-dimensions before rerunning.",
            ]
        )
    else:
        rows.append(
            [
                "No writer prompt-adherence sub-dimension was a three-way zero.",
                "Keep the current prompt-adherence checks; inspect individual low cells for targeted fixes.",
            ]
        )

    bias_findings = self_family_bias_findings(data)
    if bias_findings:
        rows.extend(bias_findings)
    else:
        rows.append(
            [
                "No self-family over-rating signal was detected from available review telemetry.",
                "Keep cross-family reviews as the default; add self-review rows only when deliberately measuring bias.",
            ]
        )

    unused_tools = [
        tool
        for tool in CORE_TOOLS
        if all(writer_tool_counts(data.writer_data[writer]).get(tool, 0) == 0 for writer in data.writers)
    ]
    if unused_tools:
        rows.append(
            [
                "No writer used: " + ", ".join(unused_tools) + ".",
                "If these tools were expected, make the prompt/tool affordance more explicit.",
            ]
        )
    else:
        rows.append(
            [
                "Every core tool was used by at least one writer.",
                "Compare density rather than presence for the next bakeoff round.",
            ]
        )

    if data.warnings:
        rows.append(
            [
                f"{len(data.warnings)} input warning(s) occurred during aggregation.",
                "Review the Warnings section before treating rankings as complete.",
            ]
        )
    return rows


def self_family_bias_findings(data: BakeoffData) -> list[list[str]]:
    summaries = review_summary_scores(data)
    rows: list[list[str]] = []
    for reviewer in data.writers:
        self_score = summaries.get(reviewer, {}).get(reviewer)
        if self_score is None:
            continue
        other_scores = [
            score
            for other_reviewer, score in summaries.get(reviewer, {}).items()
            if other_reviewer != reviewer
        ]
        if not other_scores:
            continue
        delta = self_score - mean(other_scores)
        if delta >= 0.5:
            rows.append(
                [
                    (
                        f"{reviewer} over-rated its own-family writer by {delta:.2f} "
                        f"points versus other reviewers."
                    ),
                    "Down-weight or exclude self-family reviews when selecting the bakeoff winner.",
                ]
            )
    return rows


def format_float(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


def mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    lines = [
        "| " + " | ".join(escape_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _header in headers) + " |",
    ]
    for row in rows:
        padded = [*row, *([""] * (len(headers) - len(row)))]
        lines.append("| " + " | ".join(escape_cell(cell) for cell in padded[: len(headers)]) + " |")
    return "\n".join(lines)


def escape_cell(value: Any) -> str:
    text = str(value)
    text = text.replace("\n", "<br>")
    text = text.replace("|", "\\|")
    return text


def render_report(data: BakeoffData) -> str:
    writer_prompt, writer_prompt_score_map = writer_prompt_table(data)
    warnings_block = "\n".join(f"- {warning}" for warning in data.warnings) if data.warnings else "- none"
    protocol_broken_block = "\n".join(f"- {item}" for item in data.reviewer_protocol_broken)
    report_parts = [
        "# Bakeoff comparison report",
        "\n".join(
            [
                f"- Bakeoff dir: `{data.bakeoff_dir.as_posix()}`",
                f"- Writers: {', '.join(data.writers)}",
                f"- Plan: `{data.plan.display_path}`",
                f"- Word target: {data.plan.word_target if data.plan.word_target else 'unknown'}",
            ]
        ),
        "## Winner ranking by tool-call density\n\n" + winner_ranking_table(data),
    ]
    if data.reviewer_protocol_broken:
        report_parts.append(
            "## REVIEWER PROTOCOL BROKEN\n\n"
            + protocol_broken_block
            + "\n\nReview runs emitted `reviewer_fixes_unparseable`; reviewer correction telemetry is not trustworthy."
        )
    report_parts.extend(
        [
            "## Prompt adherence - writers\n\n" + writer_prompt,
            "## Prompt adherence - reviewers\n\n" + reviewer_prompt_table(data),
            "## Content quality - writers\n\n" + content_quality_table(data),
            "## Tool usage\n\n" + tool_usage_table(data),
            "## Cross-reviewer bias check\n\n" + cross_reviewer_bias_table(data),
            "## Findings + recommendations\n\n" + findings_table(data, writer_prompt_score_map),
            "## Warnings\n\n" + warnings_block,
        ]
    )
    return "\n\n".join(
        report_parts
    ) + "\n"


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description=(
            "Aggregate V7 bakeoff JSONL telemetry, writer markdown, and reviewer scores into REPORT.md.\n"
            "Use after writer/reviewer bakeoff runs; do NOT use it as a lesson audit or to regenerate curriculum files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Aggregate the standard three-writer bakeoff into the default REPORT.md\n"
            "  .venv/bin/python scripts/audit/bakeoff_aggregate.py \\\n"
            "    --bakeoff-dir audit/bakeoff-2026-05-05 \\\n"
            "    --writers gemini,claude,gpt55\n\n"
            "  # Write to an explicit report path\n"
            "  .venv/bin/python scripts/audit/bakeoff_aggregate.py \\\n"
            "    --bakeoff-dir audit/bakeoff-2026-05-05 \\\n"
            "    --writers gemini,claude,gpt55 \\\n"
            "    --output audit/bakeoff-2026-05-05/REPORT.md\n\n"
            "Outputs:\n"
            "  <bakeoff-dir>/REPORT.md unless --output is provided. No curriculum, status, audit-review,\n"
            "  or review-review files are modified.\n\n"
            "Exit codes:\n"
            "  0 on successful report write, including partial inputs with warnings.\n"
            "  1 on invalid CLI arguments or report write failure.\n\n"
            "Related:\n"
            "  docs/MONITOR-API.md — V7 linear JSONL event schema.\n"
            "  tests/test_linear_pipeline_telemetry.py — schema fixture tests.\n"
            "  docs/dispatch-briefs/2026-05-05-a1-20-bakeoff-with-new-prompts.md — bakeoff brief."
        ),
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    parser.add_argument(
        "--bakeoff-dir",
        required=True,
        type=Path,
        help=(
            "Directory containing <writer>.md, <writer>.write.jsonl, and "
            "<writer>-<reviewer>.review.jsonl files; example: audit/bakeoff-2026-05-05."
        ),
    )
    parser.add_argument(
        "--writers",
        default="gemini,claude,gpt55",
        help=(
            "Comma-separated writer/reviewer agent names, in report column order. "
            "Default: gemini,claude,gpt55. Aliases like codex-tools normalize to gpt55."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Markdown report path to write. Default: <bakeoff-dir>/REPORT.md. "
            "Example: audit/bakeoff-2026-05-05/REPORT.md."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    writers = parse_writer_list(args.writers)
    if not writers:
        print("error: --writers must name at least one writer", file=sys.stderr)
        return 1

    bakeoff_dir = args.bakeoff_dir
    if not bakeoff_dir.is_dir():
        print(f"error: --bakeoff-dir is not a directory: {bakeoff_dir}", file=sys.stderr)
        return 1

    output = args.output if args.output is not None else bakeoff_dir / "REPORT.md"
    data = collect_bakeoff_data(bakeoff_dir, writers)
    report = render_report(data)
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, "utf-8")
    except OSError as exc:
        print(f"error: could not write report {output}: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
