"""Alphabet-module contract shared by the writer-prompt filter and the lesson gate (#8237).

The three A1 alphabet modules teach syllables, not line breaks. Syllable
divisions and typographic line breaks are different things, so these modules
must not teach a "correct" hyphenation. The prompt filter drops plan text about
``перенос`` before the writer sees it; the lesson gate fails a build that
still ships it. The upgrade prompt gets the same treatment for the lesson map
and every original artifact, headings included: a lesson that is filtered out
of the prose but still named in the map is still an order to write it.
"""
from __future__ import annotations

import copy
import re
from collections.abc import Mapping, Set
from typing import Any

ALPHABET_SLUGS = frozenset({
    "sounds-letters-and-hello",
    "reading-ukrainian",
    "special-signs",
})

_APOS = "['’ʼ`]"
# Word-stem match: перенос / переносу / переносі / переносити. The English side
# covers the paraphrases the archived lessons actually use ("words split across a
# line", "Word Hyphenation Rules"); ``\s+`` because markdown wraps mid-phrase.
# Ordinary syllable hyphens (ма-ма) and the word ``склади`` never match.
LINE_BREAK_RE = re.compile(
    rf"перенос|line[-\s]?break|divide-words|hyphenat|"
    rf"split\s+across\s+(?:a|the)\s+line|alone\s+on\s+a\s+line|"
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


def _plain(text: str) -> str:
    # Published titles carry stress marks (перено́су); match the unstressed stem.
    return text.replace("\u0301", "")


def mentions_line_breaks(text: object) -> bool:
    return isinstance(text, str) and bool(LINE_BREAK_RE.search(_plain(text)))


def contains_line_break_model(text: object) -> bool:
    return isinstance(text, str) and bool(_MODEL_RE.search(_plain(text)))


def banned_phrases_in(text: str) -> list[str]:
    low = text.casefold()
    return [p for p in BANNED_LEARNER_PHRASES if p.casefold() in low]


def mentions_banned_phrase(text: object) -> bool:
    """True when ``text`` carries a banned learner phrase, hard-wrapped or not."""
    return isinstance(text, str) and bool(banned_phrases_in(re.sub(r"\s+", " ", _plain(text))))


def is_dropped_original_paragraph(text: object) -> bool:
    """An original paragraph the upgrade must not carry forward.

    It teaches line breaks or carries a banned learner phrase, so the lesson
    gate rejects a verbatim copy; the prompt copy and the preservation baseline
    both leave it out.
    """
    return mentions_line_breaks(text) or mentions_banned_phrase(text)


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


_TITLE_JOIN_RE = re.compile(r"\s+(і|й|та|and)\s+|\s*(,|·)\s*", re.IGNORECASE)


def strip_line_break_title(title: str) -> str:
    """Drop the line-break half of a joined title: ``Перенос і підсумок`` -> ``Підсумок``.

    Returns ``""`` when nothing else is left.
    """
    if not mentions_line_breaks(title):
        return title
    parts = _TITLE_JOIN_RE.split(title)  # text, word-joiner, punct-joiner, text, ...
    kept: list[str] = []
    for i in range(0, len(parts), 3):
        if mentions_line_breaks(parts[i]):
            continue
        if kept:
            kept.append(", " if parts[i - 1] == "," else f" {parts[i - 2] or parts[i - 1]} ")
        kept.append(parts[i])
    out = "".join(kept).strip()
    return out[:1].upper() + out[1:]


def line_break_free_titles(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Prompt-only copy of an alphabet plan whose section titles name no line breaks.

    ``filter_line_break_plan`` keeps section titles because the section gate reads
    them; the writer must not see a hyphenation title, so the copy a prompt shows
    renames the section (word budget kept) or drops it when nothing else is left.
    The plan file and the gate's plan are untouched.
    """
    if not is_alphabet_slug(plan.get("slug")):
        return dict(plan)
    out = copy.deepcopy(dict(plan))
    outline = []
    for section in out.get("content_outline") or []:
        if isinstance(section, Mapping) and isinstance(section.get("section"), str):
            title = strip_line_break_title(section["section"])
            if not title:
                continue
            section = {**section, "section": title}
        outline.append(section)
    if "content_outline" in out:
        out["content_outline"] = outline
    return out


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


# A whole choice that only words the empty sign: ``без знака``, ``Немає знака``,
# ``no sign``, or a bilingual pair of them. Prose that merely contains the phrase
# never matches; the three-way contrast is still taught in words.
_NO_SIGN = r"(?:(?:без|немає)\s+знака|no\s+sign)"
_EMPTY_SIGN_CHOICE_RE = re.compile(rf"\s*{_NO_SIGN}(?:\s*[—–-]\s*{_NO_SIGN})*\s*", re.IGNORECASE)


def is_empty_sign_choice(value: object) -> bool:
    return isinstance(value, str) and bool(_EMPTY_SIGN_CHOICE_RE.fullmatch(_plain(value)))


def _blank_choice(value: Any) -> Any:
    if is_empty_sign_choice(value):
        return ""
    if isinstance(value, Mapping) and is_empty_sign_choice(value.get("text")):
        return {**value, "text": ""}
    return value


def _blank_empty_sign_item(item: Any) -> Any:
    if not isinstance(item, Mapping):
        return item
    out = dict(item)
    if isinstance(out.get("options"), list):
        out["options"] = [_blank_choice(o) for o in out["options"]]
    for key in ("answer", "correct_answer"):
        if key in out:
            out[key] = _blank_choice(out[key])
    return out


def blank_empty_sign_choices(activities: Any) -> Any:
    """Rewrite worded empty-sign choices to ``""`` in a parsed ``activities.yaml``.

    The fill-in gate rejects ``без знака — no sign`` as an option or answer; the
    empty choice is the empty string. An original shown to the writer with the
    old wording gets copied, so the prompt copy carries ``""`` instead. Only item
    ``options`` / ``answer`` change: instructions, explanations and group-sort
    labels keep the phrase.
    """
    if isinstance(activities, Mapping):
        return {k: blank_empty_sign_choices(v) if isinstance(v, list) else v for k, v in activities.items()}
    if not isinstance(activities, list):
        return activities
    return [
        {**a, "items": [_blank_empty_sign_item(i) for i in a["items"]]}
        if isinstance(a, Mapping) and isinstance(a.get("items"), list) else a
        for a in activities
    ]


def _choice_key(value: Any) -> str | None:
    if isinstance(value, Mapping):
        value = value.get("text")
    return _plain(value).strip().casefold() if isinstance(value, str) else None


def _drop_error_option(item: Any) -> Any:
    if not isinstance(item, Mapping) or not isinstance(item.get("options"), list):
        return item
    error = next((_choice_key(item.get(k)) for k in ("error", "errorWord", "error_word") if item.get(k)), None)
    if not error:
        return item
    return {**item, "options": [o for o in item["options"] if _choice_key(o) != error]}


def legal_original_activity(activity: Any) -> Any:
    """The part of an original activity an upgrade writer is allowed to keep.

    The upgrade gates reject a worded empty-sign choice (the empty choice is
    ``""``) and an error-correction option that repeats the ``error`` token.
    The prompt copy and the preservation baseline both use this form, so a
    writer who obeys those gates still preserves the original. ``sentence``,
    ``error``, ``correction`` and every other option stay required.
    """
    if not isinstance(activity, Mapping) or not isinstance(activity.get("items"), list):
        return activity
    items = [_blank_empty_sign_item(i) for i in activity["items"]]
    if activity.get("type") == "error-correction":
        items = [_drop_error_option(i) for i in items]
    return {**activity, "items": items}


def legal_original_activities(activities: Any) -> Any:
    """Apply ``legal_original_activity`` across a parsed ``activities.yaml``."""
    if isinstance(activities, Mapping):
        return {k: legal_original_activities(v) if isinstance(v, list) else v for k, v in activities.items()}
    if not isinstance(activities, list):
        return activities
    return [legal_original_activity(a) for a in activities]


def filter_line_break_resources(resources: Any) -> Any:
    """Drop line-break notes from a parsed ``resources.yaml``.

    A source stays when only its note is about line breaks; an entry whose own
    title is about them goes whole.
    """
    if isinstance(resources, list):
        resources = [
            r for r in resources
            if not (isinstance(r, Mapping) and mentions_line_breaks(r.get("title")))
        ]
    return _filter(copy.deepcopy(resources))


def line_break_original_keys(activities: Any) -> set[tuple[str, int]]:
    """``(placement, index)`` of original activities that teach line breaks."""
    if not isinstance(activities, Mapping):
        return set()
    return {
        (placement, i)
        for placement in ("inline", "workbook")
        for i, a in enumerate(activities.get(placement) or [])
        if is_line_break_activity(a)
    }


def filter_line_break_lesson_map(
    lesson_map: Mapping[str, Any], dropped: Set[tuple[str, int]] = frozenset(),
) -> dict[str, Any]:
    """Return the lesson map the writer may see: no line-break lesson, section or activity.

    Lesson titles and section names that name line breaks are removed, and so
    are the provenance rows and item exemptions of ``dropped`` originals
    (``line_break_original_keys``). Lesson numbers, minutes, word targets and
    activity counts stay. The on-disk ``lessons.yaml`` is not changed.
    """
    out = copy.deepcopy(dict(lesson_map))
    for lesson in out.get("lessons") or []:
        if mentions_line_breaks(lesson.get("title")):
            del lesson["title"]
        if isinstance(lesson.get("sections"), list):
            lesson["sections"] = [s for s in lesson["sections"] if not mentions_line_breaks(s)]
    dropped_ids = set()
    kept = []
    for row in out.get("provenance") or []:
        if (row.get("placement"), row.get("index")) in dropped:
            dropped_ids.add(row.get("new_id"))
        else:
            kept.append(row)
    if "provenance" in out:
        out["provenance"] = kept
    if "items_min_exempt" in out:
        out["items_min_exempt"] = [e for e in out["items_min_exempt"] if e.get("id") not in dropped_ids]
    return out


def filter_dropped_original_paragraphs(markdown: str) -> str:
    """Drop paragraphs ``is_dropped_original_paragraph`` names, headings included.

    A kept ``## Перенос і письмо`` heading still orders the writer to build that
    lesson, so it goes too; its surviving paragraphs read on under the previous
    heading.
    """
    return "\n\n".join(
        para for para in re.split(r"\n\s*\n", markdown) if not is_dropped_original_paragraph(para)
    )
