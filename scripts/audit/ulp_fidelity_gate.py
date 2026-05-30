"""Deterministic ULP S1 fidelity gate for A1/A2 core modules.

The gate checks the final post-processed ``module.md`` for Anna Ohoiko-style
Ukrainian-first immersion: stress marks, em-dash glosses, canonical
``DialogueBox uk/en`` turns, Ukrainian-first section openers, and the advisory
UK:EN ratio from the shared immersion policy.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from scripts.config import get_immersion_policy, get_immersion_range

STRESS_MARK = "\u0301"
STRESS_COVERAGE_MIN = 0.95
GLOSS_TOKEN_WINDOW = 8

# Terminal ULP checks are deterministic teaching *behaviours* (structural, binary):
# a genuine ULP lesson either has Ukrainian-first mixed lines, UK-only dialogue
# boxes, and Ukrainian-first openers \u2014 or it does not. Continuous/coverage signals
# are ADVISORY so mechanically useful but incomplete detectors do not false-REVISE
# otherwise teachable output.
_TERMINAL_CHECKS = ("em_dash_gloss", "dialoguebox_uk_en", "section_openers")

_UK_BASE_CLASS = "А-ЯҐЄІЇа-яґєії"
_UK_LETTER_CLASS = f"{_UK_BASE_CLASS}\u0301"
_UK_WORD_RE = re.compile(
    rf"(?<![{_UK_LETTER_CLASS}])"
    rf"([{_UK_BASE_CLASS}][{_UK_LETTER_CLASS}]*(?:[ʼ'][{_UK_BASE_CLASS}][{_UK_LETTER_CLASS}]*)*)"
    rf"(?![{_UK_LETTER_CLASS}])"
)
_WORD_RE = re.compile(
    r"[A-Za-zА-ЯҐЄІЇа-яґєії][A-Za-zА-ЯҐЄІЇа-яґєіїʼ'\u0301-]*"
)
_LATIN_RE = re.compile(r"[A-Za-z]")
_VOWELS = set("аеиіїоуюяєАЕИІЇОУЮЯЄ")
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_BAD_MARKER_RE = re.compile(r"<!--\s*bad\s*-->.*?<!--\s*/bad\s*-->", re.DOTALL | re.IGNORECASE)
_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]+`")
_URL_RE = re.compile(r"https?://\S+")
_PRONUNCIATION_LINE_RE = re.compile(r"\b(?:spoken|sounds?)\b.*\[[^\]]+\]", re.IGNORECASE)
_JSX_BLOCK_RE = re.compile(
    r"<[A-Z][A-Za-z0-9]*(?:[^<]|<(?![A-Z/]))*?(?:/>|</[A-Z][A-Za-z0-9]*>)",
    re.DOTALL,
)
_DIALOGUEBOX_RE = re.compile(
    r"<DialogueBox\b(?:[^<]|<(?![A-Z/]))*?(?:/>|</DialogueBox>)",
    re.DOTALL,
)
_ATTR_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\"([^\"]*)\"", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$", re.MULTILINE)
_TAB_BOUNDARY_RE = re.compile(r"<!--\s*TAB:(?:Словник|Вправи|Ресурси)\s*-->", re.IGNORECASE)
_STRUCTURAL_LINE_RE = re.compile(r"^\s*(?:\||>|[-*+]\s|\d+\.\s|:::|```|<!--|<)")
_LECTURE_OPENER_PATTERNS = (
    re.compile(r"^In this (?:section|module|lesson)\b", re.IGNORECASE),
    re.compile(r"^This (?:section|module|lesson)\b", re.IGNORECASE),
    re.compile(r"^Your .{0,60}\bneeds?\b", re.IGNORECASE),
    re.compile(r"^A good A[12]\b", re.IGNORECASE),
    re.compile(r"^The student must learn\b", re.IGNORECASE),
    re.compile(r"^To (?:build|make|tell|use|form)\b.{0,80}\byou need\b", re.IGNORECASE),
    re.compile(r"^(?:Before|Now that)\b.{0,80}\byou\b", re.IGNORECASE),
)


def _strip_stress(text: str) -> str:
    return text.replace(STRESS_MARK, "")


def _count_syllables(word: str) -> int:
    return sum(1 for char in _strip_stress(word) if char in _VOWELS)


def _basic_clean(text: str) -> str:
    text = _BAD_MARKER_RE.sub(" ", text)
    text = _COMMENT_RE.sub(" ", text)
    text = _FENCED_CODE_RE.sub(" ", text)
    text = _INLINE_CODE_RE.sub(" ", text)
    return _URL_RE.sub(" ", text)


def _attr_map(block: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for match in _ATTR_RE.finditer(block)}


def _learner_facing_text(text: str, *, include_all_jsx_strings: bool) -> str:
    clean = _basic_clean(text)
    jsx_values: list[str] = []
    for block in _JSX_BLOCK_RE.findall(clean):
        attrs = _attr_map(block)
        if include_all_jsx_strings:
            jsx_values.extend(attrs.values())
        else:
            uk = attrs.get("uk")
            if uk:
                jsx_values.append(uk)
    outside_jsx = _JSX_BLOCK_RE.sub(" ", clean)
    return "\n".join([outside_jsx, *jsx_values])


def _stress_coverage_check(text: str) -> dict[str, Any]:
    scan_text = _learner_facing_text(text, include_all_jsx_strings=False)
    words = [
        match.group(1)
        for match in _UK_WORD_RE.finditer(scan_text)
        if _count_syllables(match.group(1)) >= 2
    ]
    stressed = [word for word in words if STRESS_MARK in word]
    pct = round(len(stressed) / len(words), 4) if words else 0.0
    passed = bool(words) and pct >= STRESS_COVERAGE_MIN
    return {
        "passed": passed,
        "multi_syllable_uk_words": len(words),
        "stressed_multi_syllable_uk_words": len(stressed),
        "coverage": pct,
        "min_coverage": STRESS_COVERAGE_MIN,
        "missing_examples": [_strip_stress(word) for word in words if STRESS_MARK not in word][:10],
    }


def _token_window_after(text: str, start: int, *, max_tokens: int) -> str:
    matches = list(_WORD_RE.finditer(text[start:]))
    if len(matches) <= max_tokens:
        return text[start:]
    return text[start : start + matches[max_tokens].start()]


def _is_english_narration_line(line: str) -> bool:
    tokens = _WORD_RE.findall(line)
    if not tokens:
        return False
    if _UK_WORD_RE.search(tokens[0]):
        return False
    uk_count = sum(1 for token in tokens if _UK_WORD_RE.search(token))
    latin_count = sum(1 for token in tokens if _LATIN_RE.search(token))
    return latin_count > 0 and uk_count > 0 and latin_count >= uk_count


def _line_has_em_dash_gloss(line: str) -> bool:
    for match in _UK_WORD_RE.finditer(line):
        window = _token_window_after(line, match.end(1), max_tokens=GLOSS_TOKEN_WINDOW)
        if "—" not in window:
            continue
        post_dash = window.split("—", 1)[1]
        if _LATIN_RE.search(post_dash):
            return True
    return False


def _em_dash_gloss_check(text: str) -> dict[str, Any]:
    body = _JSX_BLOCK_RE.sub(" ", _basic_clean(text))
    checked: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    for line_no, raw_line in enumerate(body.splitlines(), start=1):
        line = raw_line.strip()
        if not line or _STRUCTURAL_LINE_RE.match(line):
            continue
        if not _is_english_narration_line(line):
            continue
        if _PRONUNCIATION_LINE_RE.search(line):
            continue
        terms = [
            match.group(1)
            for match in _UK_WORD_RE.finditer(line)
            if _count_syllables(match.group(1)) >= 2
        ]
        if not terms:
            continue
        has_gloss = _line_has_em_dash_gloss(line)
        record = {"line": line_no, "terms": terms[:8], "preview": line[:180]}
        checked.append(record)
        if not has_gloss:
            violations.append(record)
    return {
        "passed": not violations,
        "checked_lines": len(checked),
        "checked_terms": sum(len(record["terms"]) for record in checked),
        "violations": violations[:10],
        "token_window": GLOSS_TOKEN_WINDOW,
    }


def _tab1_text(text: str) -> str:
    match = _TAB_BOUNDARY_RE.search(text)
    return text[: match.start()] if match else text


def _dialoguebox_check(text: str) -> dict[str, Any]:
    tab1 = _tab1_text(text)
    blocks = _DIALOGUEBOX_RE.findall(tab1)
    canonical = 0
    violations: list[dict[str, Any]] = []
    for index, block in enumerate(blocks, start=1):
        attrs = _attr_map(block)
        uk = attrs.get("uk", "")
        reasons: list[str] = []
        if "uk" not in attrs:
            reasons.append("missing_uk_attr")
        if "en" not in attrs:
            reasons.append("missing_en_attr")
        if not block.strip().endswith("/>"):
            reasons.append("not_self_closing")
        if not uk or not _UK_WORD_RE.search(uk):
            reasons.append("uk_attr_has_no_ukrainian")
        if uk and _LATIN_RE.search(uk):
            reasons.append("uk_attr_contains_english")
        if "text" in attrs or "lines" in block:
            reasons.append("legacy_dialogue_shape")
        if reasons:
            violations.append({"index": index, "reasons": reasons, "preview": block[:160]})
        else:
            canonical += 1

    passed = canonical > 0 and not violations
    return {
        "passed": passed,
        "canonical_dialoguebox_count": canonical,
        "dialoguebox_count": len(blocks),
        "violations": violations,
        "reason": None if passed else "dialoguebox_uk_en_required",
    }


def _first_content_line_after(text: str, offset: int) -> tuple[int, str] | None:
    suffix = text[offset:]
    for relative_index, line in enumerate(suffix.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or _STRUCTURAL_LINE_RE.match(stripped):
            continue
        line_no = text[:offset].count("\n") + relative_index
        return line_no, stripped
    return None


def _section_opener_check(text: str) -> dict[str, Any]:
    tab1 = _tab1_text(_basic_clean(text))
    violations: list[dict[str, Any]] = []
    checked = 0
    for match in _HEADING_RE.finditer(tab1):
        opener = _first_content_line_after(tab1, match.end())
        if opener is None:
            continue
        line_no, line = opener
        checked += 1
        first_tokens = _WORD_RE.findall(line)[:8]
        first_slice = " ".join(first_tokens)
        all_english_start = bool(first_tokens) and _LATIN_RE.search(first_slice) and not _UK_WORD_RE.search(first_slice)
        lecture_pattern = next((pattern.pattern for pattern in _LECTURE_OPENER_PATTERNS if pattern.search(line)), None)
        if all_english_start or lecture_pattern is not None:
            violations.append(
                {
                    "heading": match.group(2).strip(),
                    "line": line_no,
                    "opener": line[:180],
                    "reason": "lecture_opener" if lecture_pattern else "all_english_opener",
                    "pattern": lecture_pattern,
                }
            )
    return {
        "passed": not violations,
        "checked_openers": checked,
        "violations": violations[:10],
    }


def _ratio_check(text: str, plan: Mapping[str, Any]) -> dict[str, Any]:
    level = str(plan.get("level") or "").lower()
    sequence = int(plan.get("sequence") or 0)
    min_pct, max_pct = get_immersion_range(level, sequence)
    counted_text = _learner_facing_text(text, include_all_jsx_strings=True)
    tokens = _WORD_RE.findall(counted_text)
    uk_tokens = [token for token in tokens if _UK_WORD_RE.search(token)]
    pct = round((len(uk_tokens) / len(tokens) * 100), 2) if tokens else 0.0
    return {
        "passed": min_pct <= pct <= max_pct,
        "pct": pct,
        "min_pct": min_pct,
        "max_pct": max_pct,
        "uk_tokens": len(uk_tokens),
        "total_tokens": len(tokens),
        "policy": get_immersion_policy(level, sequence)["key"],
    }


def _applies(plan: Mapping[str, Any], profile: str | None) -> bool:
    level = str(plan.get("level") or "").lower()
    if level not in {"a1", "a2"}:
        return False
    return profile in {None, "", "core"}


def check_ulp_fidelity(
    module_text: str,
    plan: Mapping[str, Any],
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    """Return a deterministic PASS/REVISE report for ULP fidelity."""
    level = str(plan.get("level") or "").lower()
    sequence = int(plan.get("sequence") or 0)
    if not _applies(plan, profile):
        return {
            "passed": True,
            "verdict": "SKIP",
            "level": level,
            "sequence": sequence,
            "profile": profile,
            "reason": "ulp_fidelity applies only to a1/a2 core",
            "failed_checks": [],
            "warnings": [],
            "checks": {},
        }

    checks = {
        "stress_coverage": _stress_coverage_check(module_text),
        "em_dash_gloss": _em_dash_gloss_check(module_text),
        "dialoguebox_uk_en": _dialoguebox_check(module_text),
        "section_openers": _section_opener_check(module_text),
        "uk_en_ratio": _ratio_check(module_text, plan),
    }
    # Only the deterministic structural checks are terminal. uk_en_ratio is
    # advisory: it surfaces as a warning but never drives the REVISE verdict.
    failed = [name for name in _TERMINAL_CHECKS if checks[name].get("passed") is not True]
    warnings = [
        name
        for name, check in checks.items()
        if name not in _TERMINAL_CHECKS and check.get("passed") is not True
    ]
    return {
        "passed": not failed,
        "verdict": "PASS" if not failed else "REVISE",
        "level": level,
        "sequence": sequence,
        "slug": str(plan.get("slug") or ""),
        "profile": profile or "core",
        "policy": get_immersion_policy(level, sequence)["key"],
        "failed_checks": failed,
        "warnings": warnings,
        "checks": checks,
    }


def check_ulp_fidelity_paths(
    module_path: Path,
    plan_path: Path,
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    plan_data = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    if not isinstance(plan_data, Mapping):
        raise TypeError(f"plan must be a mapping: {plan_path}")
    return check_ulp_fidelity(
        module_path.read_text(encoding="utf-8"),
        plan_data,
        profile=profile,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ULP fidelity gate.")
    parser.add_argument("module", type=Path, help="Path to final module.md")
    parser.add_argument("plan", type=Path, help="Path to plan YAML")
    parser.add_argument("--profile", default=None, help="Curriculum profile, e.g. core")
    args = parser.parse_args(argv)

    report = check_ulp_fidelity_paths(args.module, args.plan, profile=args.profile)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("passed") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
