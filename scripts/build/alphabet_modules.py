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
import unicodedata
from collections.abc import Callable, Mapping, Set
from typing import Any

_ACUTE = "\u0301"
_APOS_CHARS = frozenset("'’ʼ`")

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


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _strip_acute(text: str) -> str:
    return _nfc(unicodedata.normalize("NFD", text).replace(_ACUTE, ""))


def _chip_key(text: str) -> str:
    return _strip_acute(text).lower()


def vesum_is_word(form: str) -> bool:
    """True when ``form`` (acute-stripped) exists in VESUM.

    Fail-open when VESUM is missing or unreadable (CI without ``data/vesum.db``):
    return False so alphabet EC repair does not treat chips as legal drops and
    never raises into ``run_lesson_gates``.
    """
    from scripts.verification.vesum import verify_word

    bare = _strip_acute(form)
    if not bare:
        return False
    try:
        return bool(verify_word(bare) or verify_word(bare.lower()))
    except FileNotFoundError:
        return False
    except OSError:
        return False
    except Exception as exc:
        if "VESUM database not found" in str(exc):
            return False
        raise


def _soft_sign_mutants(winner: str) -> list[str]:
    """Insert or delete ``ь``; acute marks on ``winner`` are kept."""
    out: list[str] = []
    for i, ch in enumerate(winner):
        if ch == "ь":
            out.append(winner[:i] + winner[i + 1 :])
    for i in range(len(winner) + 1):
        out.append(winner[:i] + "ь" + winner[i:])
    return out


def _apostrophe_mutants(winner: str) -> list[str]:
    """Insert, delete, or shift ``'`` by one position; keep stress marks."""
    out: list[str] = []
    for i, ch in enumerate(winner):
        if ch in _APOS_CHARS:
            out.append(winner[:i] + winner[i + 1 :])
    for i in range(len(winner) + 1):
        out.append(winner[:i] + "'" + winner[i:])
    for i, ch in enumerate(winner):
        if ch not in _APOS_CHARS:
            continue
        chars = list(winner)
        if i > 0:
            chars[i], chars[i - 1] = chars[i - 1], chars[i]
            out.append("".join(chars))
            chars = list(winner)
        if i + 1 < len(winner):
            chars[i], chars[i + 1] = chars[i + 1], chars[i]
            out.append("".join(chars))
    return out


def alphabet_ec_mutants(winner: str) -> list[str]:
    """Illegal spelling mutants of ``winner`` in a fixed order (no shuffle)."""
    seen: set[str] = set()
    out: list[str] = []
    for mutant in _soft_sign_mutants(winner) + _apostrophe_mutants(winner):
        if not mutant or mutant in seen:
            continue
        seen.add(mutant)
        out.append(mutant)
    return out


def repair_error_correction_options(
    error: object,
    correct_form: object,
    options: object,
    *,
    is_word: Callable[[str], bool],
) -> list:
    """Drop VESUM-legal Find-and-Fix chips; refill with illegal mutants (#7994).

    Alphabet slugs only (caller gates). Always keeps the winner. Drops chips that
    equal the winner or the spotted error, and any other chip ``is_word`` accepts.
    Fills to three with soft-sign / apostrophe mutants of the winner (acute kept).
    If no illegal second chip exists, returns the winner alone so the unique-2
    gate still fires — reveal-only is residual.
    """
    winner = correct_form if isinstance(correct_form, str) else (str(correct_form) if correct_form else "")
    err = error if isinstance(error, str) else (str(error) if error else "")
    # Missing / non-list options: assembler still fills illegal mutants (#7994 persist).
    opts = options if isinstance(options, list) else []

    winner_key = _chip_key(winner) if winner else ""
    err_key = _chip_key(err) if err else ""
    kept: list[str] = []
    seen: set[str] = set()

    def _accept(chip: str) -> bool:
        key = _chip_key(chip)
        if not chip or key in seen:
            return False
        if winner_key and key == winner_key:
            return False
        if err_key and key == err_key:
            return False
        if is_word(chip):
            return False
        seen.add(key)
        kept.append(chip)
        return True

    if winner:
        seen.add(winner_key)
        kept.append(winner)

    for opt in opts:
        if isinstance(opt, str):
            _accept(opt)

    for mutant in alphabet_ec_mutants(winner):
        if len(kept) >= 3:
            break
        _accept(mutant)

    if len(kept) < 2:
        return [winner] if winner else []
    return kept


def persist_alphabet_ec_options(
    activities: Any,
    *,
    is_word: Callable[[str], bool] | None = None,
) -> Any:
    """Rewrite Find-and-Fix ``options`` to the repaired chip list (#7994).

    Alphabet assemble only (caller gates). Mutates mappings in place so
    ``activities.yaml``, the contradictory-payload gate, MDX, and landing union
    all see one list. Missing ``options`` still become the repaired chips.
    """
    from scripts.build.activity_renderer import error_correction_render_values

    word_fn = is_word or vesum_is_word

    def _repair_item(item: Any) -> None:
        if not isinstance(item, dict):
            return
        raw_opts = item.get("options")
        opts = raw_opts if isinstance(raw_opts, list) else []
        correction = (
            item.get("correction")
            or item.get("answer")
            or item.get("correctForm")
            or ""
        )
        if not isinstance(correction, str):
            correction = str(correction) if correction else ""
        sentence = item.get("sentence", "")
        if not isinstance(sentence, str):
            sentence = ""
        error_tok = item.get("error", "") or ""
        _, repaired = error_correction_render_values(
            sentence,
            error_tok if isinstance(error_tok, str) else str(error_tok),
            correction,
            opts,
            alphabet=True,
            is_word=word_fn,
        )
        if isinstance(repaired, list):
            item["options"] = repaired

    def _repair_activity(act: Any) -> None:
        if not isinstance(act, dict) or act.get("type") != "error-correction":
            return
        items = act.get("items")
        if isinstance(items, list):
            for row in items:
                _repair_item(row)

    if isinstance(activities, Mapping):
        for key in ("inline", "workbook"):
            section = activities.get(key)
            if isinstance(section, list):
                for act in section:
                    _repair_activity(act)
        return activities
    if isinstance(activities, list):
        for act in activities:
            _repair_activity(act)
    return activities


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


def _omit_options(item: Any) -> Any:
    if not isinstance(item, Mapping) or "options" not in item:
        return item
    return {k: v for k, v in item.items() if k != "options"}


def legal_original_activity(activity: Any) -> Any:
    """The part of an original activity an upgrade writer is allowed to keep.

    The upgrade gates reject a worded empty-sign choice (the empty choice is
    ``""``) and an error-correction option that repeats the ``error`` token.
    The archive's error-correction ``options`` are ``[correction, error]``, so
    the legal remainder is a one-chip list the writer clones instead of
    building three distinct chips. Error-correction ``options`` are therefore
    left out: the writer authors them new. The prompt copy and the preservation
    baseline both use this form, so a writer who obeys those gates still
    preserves the original. ``sentence``, ``error`` and ``correction`` stay
    required; the baseline (``preservation_baseline_activity``) lets the
    explanation grow.
    """
    if not isinstance(activity, Mapping) or not isinstance(activity.get("items"), list):
        return activity
    items = [_blank_empty_sign_item(i) for i in activity["items"]]
    if activity.get("type") == "error-correction":
        items = [_omit_options(i) for i in items]
    return {**activity, "items": items}


def preservation_baseline_activity(activity: Any) -> Any:
    """``legal_original_activity`` as the preservation gate compares it.

    The writer still sees an error-correction ``explanation`` in the prompt and
    keeps its teaching, but may expand it mid-sentence (``потрібен апо́строф`` →
    ``потрібен апо́строф після губного…``), which is no prefix of the original.
    The baseline therefore holds ``sentence``, ``error`` and ``correction`` only.
    """
    legal = legal_original_activity(activity)
    if not isinstance(legal, Mapping) or legal.get("type") != "error-correction":
        return legal
    items = [
        {k: v for k, v in i.items() if k != "explanation"} if isinstance(i, Mapping) else i
        for i in legal.get("items") or []
    ]
    return {**legal, "items": items}


# Letter-module lessons open with ULP dialogues built from recycled A1 words; the
# a1-m01-03 calibration predates them. Four injected activities is what a letter
# lesson carries.
LETTER_MODULE_MIN_TAB3_ACTIVITIES = 4


def letter_module_floor_is_advisory(gate: str, result: Mapping[str, Any]) -> bool:
    """True when a failed immersion gate must not hard-fail an alphabet lesson.

    ``long_uk_ceiling`` flags dialogue/prose runs whose support is vocabulary
    the lesson already recycles, and ``l2_exposure_floor`` may miss only
    ``uk_tab3_activities`` while still meeting the letter-module floor. Any
    other shortfall stays blocking.
    """
    if gate == "long_uk_ceiling":
        return True
    if gate != "l2_exposure_floor":
        return False
    required, observed = result.get("required") or {}, result.get("observed") or {}
    short = {k for k, need in required.items() if observed.get(k, 0) < need}
    return short == {"uk_tab3_activities"} and observed["uk_tab3_activities"] >= LETTER_MODULE_MIN_TAB3_ACTIVITIES


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
