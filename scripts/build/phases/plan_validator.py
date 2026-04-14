"""Deterministic plan consistency checks used by the v6 pre-build gate."""

from __future__ import annotations

import re

_DIALOGUE_TEXT_RE = re.compile(
    r"(діалог|діалоги|розмов|conversation|dialogue|role-?play|scenario|сценар)",
    re.IGNORECASE,
)
_EXCLUSION_RE = re.compile(
    r"\b(?:not|avoid)\s+([^.;:()\n]+)",
    re.IGNORECASE,
)
_TOKEN_RE = re.compile(r"[a-zа-яґєії0-9][a-zа-яґєії0-9'’-]*", re.IGNORECASE)
_STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "use",
    "with",
    "а",
    "але",
    "в",
    "для",
    "до",
    "з",
    "і",
    "й",
    "на",
    "не",
    "по",
    "про",
    "та",
    "у",
    "це",
    "цей",
    "ця",
    "ці",
    "що",
    "як",
}


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _excerpt(text: str, *, limit: int = 120) -> str:
    compact = _normalize_whitespace(text)
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _extract_exclusions(setting: str) -> list[tuple[str, set[str]]]:
    exclusions: list[tuple[str, set[str]]] = []
    for match in _EXCLUSION_RE.finditer(setting or ""):
        phrase = _normalize_whitespace(match.group(1))
        tokens = {
            token.lower()
            for token in _TOKEN_RE.findall(phrase)
            if len(token) >= 3 and token.lower() not in _STOPWORDS
        }
        if tokens:
            exclusions.append((phrase, tokens))
    return exclusions


def _dialogue_outline_points(plan: dict) -> list[str]:
    outline = plan.get("content_outline")
    if not isinstance(outline, list):
        return []

    points: list[str] = []
    for section in outline:
        if not isinstance(section, dict):
            continue

        section_title = str(section.get("section", ""))
        raw_points = section.get("points") or []
        if not isinstance(raw_points, list):
            continue

        section_has_dialogue = bool(_DIALOGUE_TEXT_RE.search(section_title))
        for point in raw_points:
            if not isinstance(point, str):
                continue
            if section_has_dialogue or _DIALOGUE_TEXT_RE.search(point):
                points.append(point)
    return points


def _matching_tokens(point_text: str, tokens: set[str]) -> list[str]:
    matched: list[str] = []
    for token in sorted(tokens):
        if re.search(rf"(?<![a-zа-яґєії0-9]){re.escape(token)}(?![a-zа-яґєії0-9])", point_text):
            matched.append(token)
    return matched


def validate_plan_consistency(plan: dict, slug: str) -> list[str]:
    """Return human-readable plan inconsistency messages for one module."""
    situations = plan.get("dialogue_situations")
    if not isinstance(situations, list) or not situations:
        return []

    dialogue_points = _dialogue_outline_points(plan)
    if not dialogue_points:
        return []

    messages: list[str] = []
    normalized_points = [(_excerpt(point), point.lower()) for point in dialogue_points]

    for index, situation in enumerate(situations, start=1):
        if not isinstance(situation, dict):
            continue

        setting = _normalize_whitespace(str(situation.get("setting", "")))
        if not setting:
            continue

        for phrase, tokens in _extract_exclusions(setting):
            for point_excerpt, point_lower in normalized_points:
                matched = _matching_tokens(point_lower, tokens)
                if not matched:
                    continue
                messages.append(
                    "plan_internal_consistency: "
                    f"{slug} dialogue_situations[{index - 1}] setting '{_excerpt(setting)}' "
                    f"excludes '{phrase}', but content_outline dialogue point mentions "
                    f"{', '.join(matched)}: '{point_excerpt}'"
                )
                break

    return messages
