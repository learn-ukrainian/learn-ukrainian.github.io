"""Shared source-blind matching rules for correction/protection products."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from scripts.projects.open_model_data import language_contact_detector


@dataclass(frozen=True, slots=True)
class RuleMatch:
    """One bounded rule occurrence and its structural protection decision."""

    rule: Mapping[str, Any]
    start: int
    end: int
    protected: bool


def protected_occurrence(text: str, start: int, end: int) -> bool:
    """Return whether an occurrence is inside a quoted, dialogue, or ``<ru>`` span."""
    structured = any(
        span.is_quoted and span.start_char <= start and end <= span.end_char
        for span in language_contact_detector.segment_structure(text)
    )
    tagged = any(
        match.start(1) <= start and end <= match.end(1)
        for match in re.finditer(r"<ru>(.*?)</ru>", text, re.DOTALL)
    )
    return structured or tagged


def bounded_occurrence(text: str, start: int, end: int) -> bool:
    """Require lexical boundaries so ``звучит`` never matches ``звучить``."""
    return not (
        (start > 0 and text[start - 1].isalpha() and text[start].isalpha())
        or (end < len(text) and text[end - 1].isalpha() and text[end].isalpha())
    )


def iter_rule_matches(
    text: str,
    rules: Sequence[Mapping[str, Any]],
) -> Iterator[RuleMatch]:
    """Yield non-overlapping rule matches using the released consumer semantics."""
    occupied: list[tuple[int, int]] = []
    for rule in rules:
        surface = str(rule["surface"])
        cursor = 0
        while True:
            start = text.find(surface, cursor)
            if start < 0:
                break
            end = start + len(surface)
            cursor = max(end, start + 1)
            if not bounded_occurrence(text, start, end):
                continue
            if any(left < end and start < right for left, right in occupied):
                continue
            occupied.append((start, end))
            yield RuleMatch(
                rule=rule,
                start=start,
                end=end,
                protected=protected_occurrence(text, start, end),
            )
