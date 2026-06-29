"""Deterministic B2 rebuild lesson-shape contract checks."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

INJECT_ACTIVITY_RE = re.compile(r"<!--\s*INJECT_ACTIVITY:\s*([A-Za-z0-9_-]+)\s*-->")
RAW_CALLOUT_RE = re.compile(r"\[![A-Za-z][\w-]*\]")
ACCEPTED_CALLOUT_RE = re.compile(r"^\s*>\s*\[![A-Za-z][\w-]*\]")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

B2_REBUILD_EXEMPTION_KEY = "b2_rebuild_contract_exemption"
B2_INLINE_MIN = 4
B2_INLINE_SOFT_MAX = 6
B2_SECTION_PRACTICE_WORD_LIMIT = 900

CONTRAST_KEYWORDS = (
    "aspect",
    "case",
    "conjunction",
    "contrast",
    "coordination",
    "grammar",
    "lexical",
    "morphology",
    "punctuation",
    "register",
    "style",
    "synonym",
    "syntax",
    "відмін",
    "вид ",
    "грамат",
    "лексич",
    "морфолог",
    "пунктуац",
    "регістр",
    "синон",
    "сполуч",
    "стил",
    "суряд",
    "підряд",
    "протист",
    "зістав",
)

DECISION_RULE_PATTERNS = (
    re.compile(r"^#{2,4}\s+.*(?:decision rule|rule of thumb)", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^#{2,4}\s+.*(?:алгоритм|правило вибору|як вибрати|коли обрати)", re.IGNORECASE | re.MULTILINE),
    re.compile(r"(?im)^\s*(?:якщо|коли)\b.{12,120}\b(?:то|обирайте|уживайте)\b"),
)

NON_CONCEPT_SECTION_RE = re.compile(
    r"\b("
    r"summary|recap|resources|vocabulary|workbook|answer key|"
    r"підсумок|словник|зошит|ресурси|самоперевірка|рубрика"
    r")\b",
    re.IGNORECASE,
)


def check_b2_rebuild_contract(
    module_text: str,
    activities_path: Path | None,
    *,
    meta_data: Mapping[str, Any] | None = None,
    plan_data: Mapping[str, Any] | None = None,
    module_focus: str | None = None,
) -> list[dict[str, Any]]:
    """Return B2 rebuild contract findings for one module.

    Blocking findings are intended to fail normal B2 rebuild-era modules. A
    metadata exemption with a non-empty reason skips shape checks but is still
    reported as informational so exemptions cannot be silent.
    """

    meta_data = meta_data or {}
    plan_data = plan_data or {}
    if _level(meta_data, plan_data) != "b2":
        return []

    exemption_reason = _exemption_reason(meta_data, plan_data)
    if exemption_reason:
        return [
            _finding(
                "B2_REBUILD_EXEMPTION",
                f"B2 rebuild contract explicitly exempted: {exemption_reason}",
                "Review the exemption before accepting rebuilt B2 output.",
                severity="info",
                blocking=False,
            )
        ]

    findings: list[dict[str, Any]] = []
    raw_activities = _load_activities_yaml(activities_path)
    if raw_activities["error"]:
        findings.append(
            _finding(
                "B2_ACTIVITY_YAML_UNREADABLE",
                raw_activities["error"],
                "Provide readable V2 activities.yaml with inline and workbook lists.",
            )
        )
        inline_activities: list[dict[str, Any]] = []
        workbook_activities: list[dict[str, Any]] = []
    else:
        activities_data = raw_activities["data"]
        inline_activities, workbook_activities = _activity_buckets(activities_data)
        findings.extend(_check_inline_bucket(activities_data, inline_activities))

    findings.extend(_check_injection_markers(module_text, inline_activities, workbook_activities))
    findings.extend(_check_section_practice_spacing(module_text))
    findings.extend(_check_structured_contrast(module_text, meta_data, plan_data, module_focus))
    findings.extend(_check_callout_syntax(module_text))
    return findings


def _level(meta_data: Mapping[str, Any], plan_data: Mapping[str, Any]) -> str:
    return str(meta_data.get("level") or plan_data.get("level") or "").strip().lower()


def _exemption_reason(
    meta_data: Mapping[str, Any], plan_data: Mapping[str, Any]
) -> str | None:
    for source in (meta_data, plan_data):
        raw = source.get(B2_REBUILD_EXEMPTION_KEY)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        if isinstance(raw, Mapping):
            reason = raw.get("reason")
            if isinstance(reason, str) and reason.strip():
                return reason.strip()
    return None


def _load_activities_yaml(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"data": None, "error": "B2 rebuild contract requires activities.yaml."}
    try:
        return {"data": yaml.safe_load(path.read_text(encoding="utf-8")) or {}, "error": None}
    except yaml.YAMLError as exc:
        return {"data": None, "error": f"activities.yaml is invalid YAML: {exc}"}
    except OSError as exc:
        return {"data": None, "error": f"activities.yaml cannot be read: {exc}"}


def _activity_buckets(data: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(data, Mapping):
        return [], []
    inline = data.get("inline")
    workbook = data.get("workbook")
    return _dict_list(inline), _dict_list(workbook)


def _dict_list(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _check_inline_bucket(data: Any, inline_activities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not isinstance(data, Mapping) or "inline" not in data:
        findings.append(
            _finding(
                "B2_INLINE_BUCKET_MISSING",
                "Normal B2 rebuild modules must use activities.yaml inline/workbook buckets.",
                "Use V2 shape with inline lesson practice and workbook consolidation.",
            )
        )
        return findings

    if len(inline_activities) < B2_INLINE_MIN:
        findings.append(
            _finding(
                "B2_INLINE_ACTIVITY_FLOOR",
                f"Found {len(inline_activities)} inline activities; normal B2 modules require at least {B2_INLINE_MIN}.",
                "Add 4-6 inline lesson activities before workbook consolidation.",
            )
        )
    elif len(inline_activities) > B2_INLINE_SOFT_MAX:
        findings.append(
            _finding(
                "B2_INLINE_ACTIVITY_SOFT_MAX",
                f"Found {len(inline_activities)} inline activities; normal target is 4-6.",
                "Keep extra inline activities only when every concept needs lesson practice.",
                severity="warning",
                blocking=False,
            )
        )
    return findings


def _check_injection_markers(
    module_text: str,
    inline_activities: list[dict[str, Any]],
    workbook_activities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    markers = INJECT_ACTIVITY_RE.findall(module_text)
    findings: list[dict[str, Any]] = []
    if not markers:
        findings.append(
            _finding(
                "B2_INJECT_MARKERS_MISSING",
                "module.md has no INJECT_ACTIVITY markers.",
                "Insert lesson practice markers after short concept chunks.",
            )
        )
        return findings

    inline_ids = _ids(inline_activities)
    workbook_ids = _ids(workbook_activities)
    outside_inline = sorted({activity_id for activity_id in markers if activity_id not in inline_ids})
    if outside_inline:
        workbook_hits = sorted(set(outside_inline) & workbook_ids)
        detail = ", ".join(outside_inline)
        if workbook_hits:
            detail += f" (workbook-only: {', '.join(workbook_hits)})"
        findings.append(
            _finding(
                "B2_INJECT_MARKER_OUTSIDE_INLINE",
                f"INJECT_ACTIVITY references ids outside inline activities: {detail}.",
                "Move referenced activities into inline or change markers to inline ids.",
            )
        )

    unused_inline = sorted(inline_ids - set(markers))
    if unused_inline:
        findings.append(
            _finding(
                "B2_INLINE_ACTIVITY_NOT_INJECTED",
                f"Inline activities not referenced by INJECT_ACTIVITY markers: {', '.join(unused_inline)}.",
                "Every inline activity should appear in the lesson where it practices a concept.",
            )
        )
    return findings


def _ids(activities: list[dict[str, Any]]) -> set[str]:
    return {str(activity.get("id")).strip() for activity in activities if activity.get("id")}


def _check_section_practice_spacing(module_text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for title, section_text in _h2_sections(_strip_frontmatter(module_text)):
        if _is_non_concept_section(title):
            continue
        first_marker = section_text.find("INJECT_ACTIVITY")
        measured_text = section_text if first_marker < 0 else section_text[:first_marker]
        words_before_practice = _word_count(measured_text)
        if words_before_practice > B2_SECTION_PRACTICE_WORD_LIMIT:
            issue = (
                f"Section '{title}' has {words_before_practice} words before lesson practice; "
                f"limit is {B2_SECTION_PRACTICE_WORD_LIMIT}."
            )
            findings.append(
                _finding(
                    "B2_LONG_EXPOSITION_BEFORE_PRACTICE",
                    issue,
                    "Split the concept or add an inline practice marker earlier in the section.",
                )
            )
    return findings


def _strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, flags=re.DOTALL)


def _h2_sections(text: str) -> list[tuple[str, str]]:
    matches = list(H2_RE.finditer(text))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match.group(1).strip(), text[start:end]))
    return sections


def _is_non_concept_section(title: str) -> bool:
    return bool(NON_CONCEPT_SECTION_RE.search(title))


def _word_count(text: str) -> int:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    return len(re.findall(r"[A-Za-zА-Яа-яІіЇїЄєҐґ0-9]+", text))


def _check_structured_contrast(
    module_text: str,
    meta_data: Mapping[str, Any],
    plan_data: Mapping[str, Any],
    module_focus: str | None,
) -> list[dict[str, Any]]:
    if not _requires_structured_contrast(module_text, meta_data, plan_data, module_focus):
        return []
    if _has_markdown_table(module_text) or _has_decision_rule(module_text):
        return []
    return [
        _finding(
            "B2_STRUCTURED_CONTRAST_MISSING",
            "B2 grammar/lexical contrast module is prose-only: no table, contrast grid, or decision-rule block found.",
            "Add a compact table/grid or explicit decision-rule block for the contrast.",
        )
    ]


def _requires_structured_contrast(
    module_text: str,
    meta_data: Mapping[str, Any],
    plan_data: Mapping[str, Any],
    module_focus: str | None,
) -> bool:
    focus = str(module_focus or meta_data.get("focus") or plan_data.get("focus") or "").lower()
    tags = " ".join(str(tag).lower() for tag in meta_data.get("tags", []) if tag)
    title = str(meta_data.get("title") or plan_data.get("title") or "").lower()
    slug = str(meta_data.get("slug") or plan_data.get("slug") or "").lower()
    outline = " ".join(str(item).lower() for item in plan_data.get("content_outline", []) if item)
    haystack = " ".join([focus, tags, title, slug, outline, module_text[:2000].lower()])
    return any(keyword in haystack for keyword in CONTRAST_KEYWORDS)


def _has_markdown_table(text: str) -> bool:
    return any(TABLE_SEPARATOR_RE.match(line) for line in text.splitlines())


def _has_decision_rule(text: str) -> bool:
    return any(pattern.search(text) for pattern in DECISION_RULE_PATTERNS)


def _check_callout_syntax(module_text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    in_fence = False
    for line_no, line in enumerate(module_text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if RAW_CALLOUT_RE.search(line) and not ACCEPTED_CALLOUT_RE.match(line):
            findings.append(
                _finding(
                    "B2_MALFORMED_CALLOUT",
                    f"Line {line_no} uses raw callout syntax outside accepted blockquote form: {line.strip()}",
                    "Use '> [!note]' blockquote callouts or site-supported directive syntax.",
                )
            )
    return findings


def _finding(
    finding_type: str,
    issue: str,
    fix: str,
    *,
    severity: str = "error",
    blocking: bool = True,
) -> dict[str, Any]:
    return {
        "type": finding_type,
        "severity": severity,
        "blocking": blocking,
        "issue": issue,
        "fix": fix,
    }
