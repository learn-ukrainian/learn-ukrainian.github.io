#!/usr/bin/env python3
"""Report BIO learner-surface leakage, LLM fingerprint, and activity split.

This is intentionally lightweight and deterministic. It does not replace
independent review; it gives BIO orchestrators a repeatable score to include in
PR notes and a strict mode for targeted release gates.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BIO_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "bio"

INJECT_RE = re.compile(r"<!--\s*INJECT_ACTIVITY:\s*([A-Za-z0-9_-]+)\s*-->")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
URL_RE = re.compile(r"https?://\S+|www\.\S+")
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
DIRECTIVE_RE = re.compile(r"^:::[A-Za-z0-9_-]+(?:\[[^\n]*\])?\s*$|^:::\s*$", re.MULTILINE)
CALLOUT_TAG_RE = re.compile(r"\[![A-Za-z0-9_-]+\]")
LATIN_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_-]{2,}\b")

LATIN_ALLOWLIST = {
    "KGB",
    "NKVD",
    "OUN",
    "UPA",
    "UNESCO",
    "URL",
    "PDF",
    "HTML",
    "MDX",
}

INTERNAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("meta-course: цей урок", re.compile(r"\bцей\s+урок\b", re.IGNORECASE)),
    ("meta-course: цей модуль", re.compile(r"\bцей\s+модуль\b", re.IGNORECASE)),
    ("meta-course: ця біографія", re.compile(r"\bця\s+біографія\b", re.IGNORECASE)),
    ("meta-course: у курсі", re.compile(r"\bу\s+курсі\b", re.IGNORECASE)),
    ("meta-course: для учня", re.compile(r"\bдля\s+учн\w*\b", re.IGNORECASE)),
    ("meta-course: для рівня", re.compile(r"\bдля\s+рівн\w*\b", re.IGNORECASE)),
    ("meta-course: навчальна біографія", re.compile(r"\bнавчальн\w*\s+біограф", re.IGNORECASE)),
    ("self-instruction: важливо показати", re.compile(r"\bважливо\s+показати\b", re.IGNORECASE)),
    ("self-instruction: треба пам'ятати", re.compile(r"\bтреба\s+пам[’'ʼ]?ятати\b", re.IGNORECASE)),
    ("self-instruction: не треба перетворювати", re.compile(r"\bне\s+треба\s+перетворювати\b", re.IGNORECASE)),
    ("answer coaching: сильна відповідь", re.compile(r"\bсильн\w*\s+відповід", re.IGNORECASE)),
    ("answer coaching: добра відповідь", re.compile(r"\bдобр\w*\s+відповід", re.IGNORECASE)),
    ("English residue: lesson/module", re.compile(r"\b(?:lesson|module|learner|workbook|inline)\b", re.IGNORECASE)),
    ("English residue: process term", re.compile(r"\b(?:source-tier|gate|prompt|audit|review|telemetry|LLM)\b", re.IGNORECASE)),
)

FINGERPRINT_PATTERNS: tuple[tuple[str, re.Pattern[str], int], ...] = (
    ("formula: не лише X, а й Y", re.compile(r"\bне\s+лише\b.{0,100}?\bа\s+й\b", re.IGNORECASE | re.DOTALL), 1),
    ("hedge: варто зазначити", re.compile(r"\bварто\s+зазначити\b", re.IGNORECASE), 2),
    ("hedge: можна сказати", re.compile(r"\bможна\s+сказати\b", re.IGNORECASE), 1),
    ("teacher register: важливо розуміти", re.compile(r"\bважливо\s+розуміти\b", re.IGNORECASE), 1),
    ("teacher register: треба пам'ятати", re.compile(r"\bтреба\s+пам[’'ʼ]?ятати\b", re.IGNORECASE), 2),
)


def _strip_non_prose(text: str) -> str:
    text = FRONTMATTER_RE.sub("", text)
    text = CODE_FENCE_RE.sub("", text)
    text = HTML_COMMENT_RE.sub("", text)
    text = URL_RE.sub("", text)
    text = DIRECTIVE_RE.sub("", text)
    text = CALLOUT_TAG_RE.sub("", text)
    return text


def _line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _find_pattern_hits(text: str, specs: tuple[tuple[str, re.Pattern[str]], ...]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for label, pattern in specs:
        for match in pattern.finditer(text):
            hits.append(
                {
                    "label": label,
                    "line": _line_for_offset(text, match.start()),
                    "match": match.group(0).replace("\n", " ")[:120],
                }
            )
    return hits


def _latin_words(text: str) -> list[dict[str, Any]]:
    words: list[dict[str, Any]] = []
    for match in LATIN_WORD_RE.finditer(text):
        word = match.group(0)
        if word.upper() in LATIN_ALLOWLIST:
            continue
        words.append({"word": word, "line": _line_for_offset(text, match.start())})
    return words


def _fingerprint_score(text: str) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    penalty = 0
    for label, pattern, weight in FINGERPRINT_PATTERNS:
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        # Repetition is the signal. A single natural transition is not a flaw.
        count_penalty = max(0, len(matches) - 1) * weight
        if label.startswith("formula:") and len(matches) == 1:
            count_penalty = 0
        penalty += count_penalty
        hits.append(
            {
                "label": label,
                "count": len(matches),
                "penalty": count_penalty,
                "lines": [_line_for_offset(text, match.start()) for match in matches[:8]],
            }
        )
    score = max(1, 10 - penalty)
    if score >= 9:
        band = "low"
    elif score >= 7:
        band = "watch"
    else:
        band = "blocker"
    return {"score": score, "band": band, "hits": hits}


def _activity_id(item: Any) -> str | None:
    if not isinstance(item, dict):
        return None
    raw = item.get("id") or item.get("activity_id")
    return str(raw) if raw is not None else None


def _activity_report(module_text: str, activities_path: Path) -> dict[str, Any]:
    if not activities_path.exists():
        return {
            "schema": "missing",
            "status": "fail",
            "inline_count": 0,
            "workbook_count": 0,
            "issues": [f"missing {activities_path}"],
        }

    data = yaml.safe_load(activities_path.read_text(encoding="utf-8"))
    markers = INJECT_RE.findall(module_text)
    issues: list[str] = []

    if isinstance(data, list):
        return {
            "schema": "v1-list",
            "status": "warn",
            "inline_count": 0,
            "workbook_count": len(data),
            "markers": markers,
            "issues": ["legacy V1 activities; BIO production should use V2 inline/workbook split"],
        }

    if not isinstance(data, dict):
        return {
            "schema": "unknown",
            "status": "fail",
            "inline_count": 0,
            "workbook_count": 0,
            "markers": markers,
            "issues": ["activities.yaml must be a V2 object or legacy V1 list"],
        }

    if "activities" in data:
        issues.append("do not wrap activity lists in an activities: key")

    inline = data.get("inline") or []
    workbook = data.get("workbook") or []
    inline_ids = [_activity_id(item) for item in inline]
    workbook_ids = [_activity_id(item) for item in workbook]
    inline_ids = [item_id for item_id in inline_ids if item_id]
    workbook_ids = [item_id for item_id in workbook_ids if item_id]

    marker_set = set(markers)
    inline_set = set(inline_ids)
    workbook_set = set(workbook_ids)
    for item_id in sorted(inline_set - marker_set):
        issues.append(f"inline activity {item_id} has no INJECT_ACTIVITY marker")
    for item_id in sorted(marker_set - inline_set):
        issues.append(f"INJECT_ACTIVITY marker {item_id} has no inline activity")
    for item_id in sorted(workbook_set & marker_set):
        issues.append(f"workbook activity {item_id} must not be injected in lesson prose")
    if not workbook:
        issues.append("workbook activity list is empty")

    return {
        "schema": "v2",
        "status": "pass" if not issues else "fail",
        "inline_count": len(inline),
        "workbook_count": len(workbook),
        "markers": markers,
        "inline_ids": inline_ids,
        "workbook_ids": workbook_ids,
        "issues": issues,
    }


def resolve_module(raw: str) -> Path:
    candidate = Path(raw)
    if candidate.exists():
        return candidate
    module_path = BIO_ROOT / raw / "module.md"
    if module_path.exists():
        return module_path
    raise SystemExit(f"BIO module not found: {raw}")


def build_report(raw_target: str) -> dict[str, Any]:
    module_path = resolve_module(raw_target).resolve()
    module_text = module_path.read_text(encoding="utf-8")
    prose = _strip_non_prose(module_text)
    activities_path = module_path.with_name("activities.yaml")

    internal_hits = _find_pattern_hits(prose, INTERNAL_PATTERNS)
    latin_hits = _latin_words(prose)
    fingerprint = _fingerprint_score(prose)
    activities = _activity_report(module_text, activities_path)

    passed = not internal_hits and activities["status"] != "fail" and fingerprint["score"] >= 7
    return {
        "target": str(module_path.relative_to(PROJECT_ROOT)),
        "slug": module_path.parent.name,
        "passed": passed,
        "internal_leakage": {
            "status": "pass" if not internal_hits else "fail",
            "count": len(internal_hits),
            "hits": internal_hits,
        },
        "english_leakage": {
            "status": "pass" if not latin_hits else "warn",
            "count": len(latin_hits),
            "examples": latin_hits[:20],
        },
        "llm_fingerprint": fingerprint,
        "activity_split": activities,
    }


def print_text_report(report: dict[str, Any]) -> None:
    activity = report["activity_split"]
    print(f"BIO surface quality: {report['slug']}")
    print(f" target: {report['target']}")
    print(f" passed: {report['passed']}")
    print(
        " activity_split: "
        f"inline={activity['inline_count']} workbook={activity['workbook_count']} "
        f"schema={activity['schema']} status={activity['status']}"
    )
    print(
        " leakage: "
        f"english={report['english_leakage']['status']}({report['english_leakage']['count']}) "
        f"internal={report['internal_leakage']['status']}({report['internal_leakage']['count']})"
    )
    fingerprint = report["llm_fingerprint"]
    print(f" llm_fingerprint: {fingerprint['score']}/10 band={fingerprint['band']}")
    for issue in activity.get("issues", []):
        print(f" activity_issue: {issue}")
    for hit in report["internal_leakage"]["hits"][:20]:
        print(f" internal_hit: line {hit['line']}: {hit['label']} -> {hit['match']}")
    for hit in fingerprint["hits"]:
        if hit["penalty"]:
            print(f" fingerprint_hit: {hit['label']} count={hit['count']} penalty={hit['penalty']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="BIO slug or path to curriculum/l2-uk-en/bio/<slug>/module.md")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when the report does not pass")
    args = parser.parse_args(argv)

    report = build_report(args.target)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    return 1 if args.strict and not report["passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
