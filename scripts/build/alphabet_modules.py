"""Alphabet-module contract shared by the writer-prompt filter and the lesson gate (#8237).

The three A1 alphabet modules teach syllables, not line breaks. Syllable
divisions and typographic line breaks are different things, so these modules
must not teach a "correct" hyphenation. The prompt filter drops plan text about
``перенос`` before the writer sees it; the lesson gate fails a build that
still ships it.
"""
from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from typing import Any

ALPHABET_SLUGS = frozenset({
    "sounds-letters-and-hello",
    "reading-ukrainian",
    "special-signs",
})

_APOS = "['’ʼ`]"
# Word-stem match: перенос / переносу / переносі / переносити.
LINE_BREAK_RE = re.compile(
    rf"перенос|line[- ]?break|divide-words|"
    rf"Мар{_APOS}-яна|дере-в{_APOS}яний|бур{_APOS}-ян|паль-ці",
    re.IGNORECASE,
)
LINE_BREAK_MODELS = ("Мар'-яна", "дере-в'яний", "бур'-ян", "паль-ці")
_MODEL_RE = re.compile(
    rf"Мар{_APOS}-яна|дере-в{_APOS}яний|бур{_APOS}-ян|паль-ці", re.IGNORECASE,
)

# Structural plan keys the section/word-budget contract reads; never removed.
_STRUCTURAL_KEYS = frozenset({"section", "title", "id", "slug", "words", "type"})
# Lists whose dict entries are whole self-contained instructions.
_WHOLE_ENTRY_LISTS = frozenset({"activity_hints", "pronunciation_videos"})

BANNED_LEARNER_PHRASES = (
    "mastery of all 33 letters",
    "comprehensive command of the complete 33-letter",
    "use only prepared models",
    "before you leave the lesson tab",
    "Stay inside Ukrainian for this lesson",
)


def is_alphabet_slug(slug: object) -> bool:
    return str(slug or "").strip().lower() in ALPHABET_SLUGS


def mentions_line_breaks(text: object) -> bool:
    return isinstance(text, str) and bool(LINE_BREAK_RE.search(text))


def contains_line_break_model(text: object) -> bool:
    return isinstance(text, str) and bool(_MODEL_RE.search(text))


def banned_phrases_in(text: str) -> list[str]:
    low = text.casefold()
    return [p for p in BANNED_LEARNER_PHRASES if p.casefold() in low]


def _has_match(value: Any) -> bool:
    if isinstance(value, str):
        return mentions_line_breaks(value)
    if isinstance(value, Mapping):
        return any(_has_match(v) for v in value.values())
    if isinstance(value, list):
        return any(_has_match(v) for v in value)
    return False


def _filter(value: Any, key: str | None = None) -> Any:
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, str):
                if not mentions_line_breaks(item):
                    out.append(item)
            elif isinstance(item, Mapping):
                if key in _WHOLE_ENTRY_LISTS and _has_match(item):
                    continue
                out.append(_filter(item))
            else:
                out.append(_filter(item, key))
        return out
    if isinstance(value, Mapping):
        out_map = {}
        for k, v in value.items():
            if isinstance(v, str):
                if k not in _STRUCTURAL_KEYS and mentions_line_breaks(v):
                    continue
                out_map[k] = v
            else:
                out_map[k] = _filter(v, str(k))
        return out_map
    return value


def filter_line_break_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of ``plan`` with line-break text removed for alphabet slugs.

    Objectives, section points, activity hints and free-text notes that mention
    ``перенос`` (or the four hyphenation models) are dropped. Structural keys
    (section titles, word budgets) stay, because the section gate reads them.
    Other slugs are returned unchanged.
    """
    if not is_alphabet_slug(plan.get("slug")):
        return dict(plan)
    return _filter(copy.deepcopy(dict(plan)))


def is_line_break_activity(activity: Any) -> bool:
    """True for a divide-words activity or one whose text teaches line breaks."""
    if not isinstance(activity, Mapping):
        return False
    return activity.get("type") == "divide-words" or _has_match(dict(activity))


def filter_line_break_activities(activities: Any) -> Any:
    """Drop line-break activities from a parsed ``activities.yaml`` (mapping or list)."""
    if isinstance(activities, Mapping):
        return {
            k: [a for a in v if not is_line_break_activity(a)] if isinstance(v, list) else v
            for k, v in activities.items()
        }
    if isinstance(activities, list):
        return [a for a in activities if not is_line_break_activity(a)]
    return activities


def filter_line_break_paragraphs(markdown: str) -> str:
    """Drop prose paragraphs that teach line breaks; headings are structural and stay."""
    kept = []
    for para in re.split(r"\n\s*\n", markdown):
        heading_only = para.lstrip().startswith("#") and "\n" not in para.strip()
        if heading_only or not mentions_line_breaks(para):
            kept.append(para)
    return "\n\n".join(kept)
