#!/usr/bin/env python3
"""Extract intentional error-correction exercises from Ukrainian textbooks and style guides.

Also provides guardrail classifiers to prevent naive cloze/reading pipelines from ingesting
deliberate pedagogical errors from textbook exercise prompts.

Every extracted pair must be backed by its source (#8723): a row of a real
НЕПРАВИЛЬНО/ПРАВИЛЬНО table (or a style-guide contrast), split at a point the row
itself evidences, and — for single-word lexical claims — corroborated by VESUM.
Anything the sources cannot decide is withheld with a reason instead of guessed.

Regenerate the bundled Culture-of-Speech deck (and the audited registry copy):

    .venv/bin/python scripts/practice/extract_textbook_error_corrections.py \\
        --db data/sources.db --vesum-db data/vesum.db \\
        --export-json site/src/data/practice-error-corrections.json \\
        --export-json registry/practice/textbook-error-corrections.json \\
        --withheld-json /tmp/error-corrections-withheld.json

Pairs a language reviewer rejected are withheld by their text through the committed,
reviewed list ``registry/practice/error-correction-withheld.yaml``.
"""

import argparse
import json
import re
import sqlite3
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import yaml

# Trigger patterns that identify deliberate pedagogical error prompts/tables
ERROR_CONTEXT_PATTERNS = [
    re.compile(
        r"(?i)\b(?:виправте|виправляючи|відредагуйте|відредагувати|знайдіть\s+помилк\w*|помилково\s+вжито|уникайте\s+помилок|антисуржик|культура\s+слова|культура\s+мовлення)\b"
    ),
    re.compile(r"(?i)\bНЕПРАВИЛЬНО\b[\s\S]{1,100}\bПРАВИЛЬНО\b"),
    re.compile(r"(?i)\bпомилк[а-я]*\s+у\s+(?:слововживанні|будові|узгодженні|керуванні)\b"),
    re.compile(r"(?i)\bвставте\s+пропущен[іі]\s+(?:букви|літери)\b"),
    re.compile(r"(?i)\bрозкрийте\s+дужки\b"),
]

REVIEWED_WITHHELD_PATH = Path(__file__).resolve().parents[2] / "registry/practice/error-correction-withheld.yaml"
REVIEW_CODES = frozenset({"WRONG_ERROR", "WRONG_FIX", "CONTESTED"})

CULTURE_DECK_ID = "culture-error-correction"
CULTURE_DECK_TITLE = "Культура мовлення: Редагування помилок"
CULTURE_DECK_TITLE_EN = "Culture of Speech: Error Editing"

MAX_PHRASE_CHARS = 60
# Register labels the pre-#8723 builder appended to fabricate distractors.
REGISTER_LABEL_RE = re.compile(r"\s\((?:розм|заст|застаріле|книжн|діал|жарг|прост)\.?\)\s*$")

# Table headers. Avramenko's upper-case "… НЕПРАВИЛЬНО ПРАВИЛЬНО" heads horizontal
# tables: one "<incorrect> <correct>" pair per line. Every other header spelling
# ("Неправильно Правильно", "ПРАВИЛЬНО НЕПРАВИЛЬНО", "Правильно НЕправильно") heads a
# vertical table: the whole first column, then the whole second column, in the
# column order the header names.
_HORIZONTAL_HEADER_RE = re.compile(r"(?:^|\s)НЕПРАВИЛЬНО\s+ПРАВИЛЬНО$")
_ANY_HEADER_RE = re.compile(r"(?:^|\s)((?:не)?правильно)\s+((?:не)?правильно)$", re.IGNORECASE)
_ALTERNATIVES_ROW_RE = re.compile(r"^\S+ / \S+$")

_LETTERS = "а-щьюяєіїґА-ЩЬЮЯЄІЇҐ"
_APOSTROPHES = "’'ʼ"
_WORD_RE = re.compile(rf"[{_LETTERS}{_APOSTROPHES}]+(?:-[{_LETTERS}{_APOSTROPHES}]+)*")
_ALLOWED_PHRASE_RE = re.compile(rf"^[{_LETTERS}{_APOSTROPHES}\- ,()/]+$")
_LOWER_START_RE = re.compile(r"^[а-щьюяєіїґ]")
_UPPER_START_RE = re.compile(r"^[А-ЩЬЮЯЄІЇҐ]")

_TABLE_STOP_RE = re.compile(r"^(?:\d|[А-ЩЬЮЯЄІЇҐA-Z]\.)")
# A comma before a relative word joins a clause ("град, що випав"); other commas and
# " / " separate alternative corrections ("по п’ятницях, щоп’ятниці").
_ALTERNATIVE_SEPARATOR_RE = re.compile(r", | / ")
_RELATIVE_WORDS = frozenset(
    {"що", "хто", "який", "яка", "яке", "які", "де", "куди", "коли", "чий", "чия", "чиє", "чиї"}
)
_PARENTHETICAL_RE = re.compile(r"\(([^()]*)\)")
# Analytic comparison is one unit with the synthetic degree it replaces
# ("найбільш потрібний" ~ "найпотрібніший"); VESUM tags comparatives "compc".
_ANALYTIC_DEGREE = {"більш": "compc", "менш": "compc", "найбільш": "comps", "найменш": "comps"}
_DEGREES = ("compb", "compc", "comps")
_CASES = ("v_naz", "v_rod", "v_dav", "v_zna", "v_oru", "v_mis", "v_kly")
_FUNCTION_POS = frozenset({"prep", "part", "conj", "intj"})
_MAX_TABLE_ROWS = 9
_MAX_ROW_CHARS = 90


def is_intentional_error_context(text: str) -> bool:
    """Return True if the text belongs to an intentional error exercise or contrastive table."""
    if not text or not isinstance(text, str):
        return False
    return any(p.search(text) for p in ERROR_CONTEXT_PATTERNS)


# ---------------------------------------------------------------------------
# VESUM access (read-only)
# ---------------------------------------------------------------------------


class VesumLookup:
    """Read-only VESUM view: word-form status and part-of-speech sets.

    ``status`` is ``"marked"`` when any analysis of the form carries a ``bad`` /
    ``subst`` marker (VESUM records it as a known error), ``"clean"`` when the form
    is attested only as standard Ukrainian, and ``"unattested"`` when VESUM has no
    such form. ``signatures`` are the inflectional slots a substitute must fill.
    """

    _ERROR_MARKERS = ("bad", "subst")

    def __init__(self, db_path: Path | str):
        self._conn = sqlite3.connect(f"file:{Path(db_path)}?mode=ro", uri=True)
        self._cache: dict[str, list[tuple[str, str, bool]]] = {}

    def _analyses(self, word: str) -> list[tuple[str, str, bool]]:
        # VESUM spells the apostrophe as ASCII "'"; a word capitalised in the source is
        # also looked up lowercased, never the reverse ("десна" is not the river Десна).
        key = word.replace("’", "'").replace("ʼ", "'")
        if key not in self._cache:
            rows = self._conn.execute(
                """
                SELECT f.pos, f.tags, EXISTS (
                    SELECT 1 FROM form_markers m
                    WHERE m.form_id = f.id AND m.marker IN (?, ?)
                )
                FROM forms_all f WHERE f.word_form IN (?, ?)
                """,
                (*self._ERROR_MARKERS, key, key.lower()),
            ).fetchall()
            self._cache[key] = [(pos, tags, bool(marked)) for pos, tags, marked in rows]
        return self._cache[key]

    def status(self, word: str) -> str:
        analyses = self._analyses(word)
        if not analyses:
            return "unattested"
        if any(marked for *_, marked in analyses):
            return "marked"
        return "clean"

    def pos(self, word: str) -> set[str]:
        return {pos for pos, *_ in self._analyses(word)}

    def signatures(self, word: str) -> set[tuple[str | None, ...]]:
        return {_signature(pos, tags) for pos, tags, _ in self._analyses(word)}


def _pick(features: set[str], values: Iterable[str]) -> str | None:
    return next((value for value in values if value in features), None)


def _signature(pos: str, tags: str) -> tuple[str | None, ...]:
    """Inflectional slot of one VESUM analysis.

    Adjectives must agree (gender/number, case, degree), verbs keep their form, person,
    number and gender; aspect and a noun's case (set by its governing word: «згідно з
    планом» / «відповідно до плану») may differ between variants.
    """
    features = set(tags.split(":"))
    if pos == "adj":
        return (pos, _pick(features, "mfnp"), _pick(features, _CASES), _pick(features, _DEGREES) or "compb")
    if pos == "adv":
        return (pos, _pick(features, _DEGREES) or "compb")
    if pos == "verb":
        form = _pick(features, ("inf", "pres", "futr", "past", "impr", "impers"))
        return (pos, form, _pick(features, "123"), _pick(features, "sp"), _pick(features, "mfn"))
    return (pos,)


# ---------------------------------------------------------------------------
# Pair validation
# ---------------------------------------------------------------------------


def _words(phrase: str) -> list[str]:
    return _WORD_RE.findall(phrase)


def _longest_common_substring(a: str, b: str) -> int:
    best = 0
    for i in range(len(a)):
        for j in range(len(b)):
            k = 0
            while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                k += 1
            best = max(best, k)
    return best


def _related(a: str, b: str) -> bool:
    """Same word, or two words sharing a stem.

    A stem is a common prefix of >= 4 letters, a short stem (>= 3 letters covering
    most of the shorter word: "ціною"/"ціну", "небом"/"неба"), or a shared core of
    >= 5 letters ("питання"/"запитання").
    """
    a, b = a.casefold(), b.casefold()
    if a == b:
        return True
    prefix = 0
    for x, y in zip(a, b, strict=False):
        if x != y:
            break
        prefix += 1
    if prefix >= 4 or (prefix >= 3 and prefix > 0.6 * min(len(a), len(b))):
        return True
    return _longest_common_substring(a, b) >= 5


def _alignment_score(left: list[str], right: list[str]) -> int:
    """Order-preserving count of related word pairs (LCS under ``_related``)."""
    rows = [[0] * (len(right) + 1) for _ in range(len(left) + 1)]
    for i, a in enumerate(left, 1):
        for j, b in enumerate(right, 1):
            rows[i][j] = rows[i - 1][j - 1] + 1 if _related(a, b) else max(rows[i - 1][j], rows[i][j - 1])
    return rows[-1][-1]


def _balanced_parentheses(phrase: str) -> bool:
    depth = 0
    for ch in phrase:
        depth += ch == "("
        depth -= ch == ")"
        if depth < 0:
            return False
    return depth == 0


def _shape_reason(error: str, correct: str) -> str | None:
    """Return why a pair cannot be a source-faithful error/correction phrase, else None."""
    if not error or not correct:
        return "empty_side"
    if error.casefold() == correct.casefold():
        return "identical_sides"
    if len(error) > MAX_PHRASE_CHARS or len(correct) > MAX_PHRASE_CHARS:
        return "phrase_too_long"
    for phrase in (error, correct):
        if not _ALLOWED_PHRASE_RE.match(phrase):
            return "unsupported_characters"
        if not _balanced_parentheses(phrase) or phrase.startswith("("):
            return "unbalanced_parentheses"
        if not _words(phrase):
            return "no_words"
    if any(ch in error for ch in ",/("):
        return "error_side_lists_alternatives"
    error_words, correct_words = _words(error), _words(correct)
    if not all(any(len(w) >= 3 for w in words) for words in (error_words, correct_words)):
        return "no_content_word"
    if _LOWER_START_RE.match(error) and _LOWER_START_RE.match(correct):
        return None
    # Capitalised sides are a sentence-level contrast only when both open with the
    # same word ("Головну увагу мною…" → "Головну увагу я…"), never sentence→fragment.
    if (
        _UPPER_START_RE.match(error)
        and _UPPER_START_RE.match(correct)
        and error_words[0].casefold() == correct_words[0].casefold()
    ):
        return None
    return "not_a_lowercase_phrase"


def _tidy(phrase: str) -> str:
    return " ".join(phrase.split()).replace(" ,", ",")


def split_alternatives(text: str) -> list[str]:
    """Top-level alternative corrections of one source correction (outside parentheses)."""
    segments, start = [], 0
    for match in _ALTERNATIVE_SEPARATOR_RE.finditer(text):
        before = text[: match.start()]
        if before.count("(") != before.count(")"):
            continue
        following = _words(text[match.end() :])
        if match.group() == ", " and following and following[0].casefold() in _RELATIVE_WORDS:
            continue
        segments.append(text[start : match.start()])
        start = match.end()
    segments.append(text[start:])
    return [_tidy(segment) for segment in segments if segment.strip()]


def _units(words: list[str], vesum: VesumLookup) -> list[tuple[int, frozenset]]:
    """``(word count, signatures)`` per syntactic unit.

    An analytic comparison ("найбільш довгий") and a compound preposition (a
    preposition-only word plus a function word: "незважаючи на") are one unit each.
    """
    units: list[tuple[int, frozenset]] = []
    i = 0
    while i < len(words):
        word, following = words[i], words[i + 1] if i + 1 < len(words) else None
        degree = _ANALYTIC_DEGREE.get(word.casefold())
        if degree and following:
            analytic = frozenset(
                (*sig[:-1], degree)
                for sig in vesum.signatures(following)
                if sig[0] in {"adj", "adv"} and sig[-1] == "compb"
            )
            if analytic:
                units.append((2, analytic))
                i += 2
                continue
        if following and vesum.pos(word) == {"prep"} and vesum.pos(following) <= _FUNCTION_POS and vesum.pos(following):
            units.append((2, frozenset({("prep",)})))
            i += 2
            continue
        units.append((1, frozenset(vesum.signatures(word))))
        i += 1
    return units


def _expand_parentheticals(segment: str, vesum: VesumLookup | None) -> list[str] | None:
    """Every reading of a correction with parenthetical variants, or None if one is not parallel.

    A parenthetical variant stands for the units right before it: "брати (узяти)
    участь" reads "брати участь" / "узяти участь". It is parallel when it has as many
    units as it replaces and each fills the same VESUM inflectional slot. An insertion
    ("дехто (з нас)"), a government hint ("ставлення (до когось)") or a different
    construction ("є в продажу (поступила в продаж)") is not a variant of the main form.
    """
    match = _PARENTHETICAL_RE.search(segment)
    if not match:
        return [_tidy(segment)]
    prefix, suffix = segment[: match.start()], segment[match.end() :]
    readings = [_tidy(f"{prefix} {suffix}")]
    if vesum is not None:
        prefix_words = list(_WORD_RE.finditer(prefix))
        prefix_units = _units([m.group() for m in prefix_words], vesum)
        for alternative in split_alternatives(match.group(1)):
            alternative_units = _units(_words(alternative), vesum)
            count = len(alternative_units)
            if not count or count > len(prefix_units):
                return None
            replaced = prefix_units[-count:]
            if not all(a[1] & b[1] for a, b in zip(replaced, alternative_units, strict=True)):
                return None
            first_word = prefix_words[-sum(size for size, _ in replaced)]
            readings.append(
                _tidy(f"{prefix[: first_word.start()]}{alternative}{prefix[prefix_words[-1].end() :]} {suffix}")
            )
    expanded: list[str] = []
    for reading in readings:
        more = _expand_parentheticals(reading, vesum)
        if more is None:
            return None
        expanded.extend(more)
    return expanded


def _expand_slashed_words(segment: str) -> list[str]:
    """Both readings of a slash inside one token: "барви/кольори осіннього лісу"."""
    readings = [""]
    for token in segment.split(" "):
        options = token.split("/") if "/" in token.strip("/") else [token]
        readings = [f"{reading} {option}" for reading in readings for option in options]
    return [_tidy(reading) for reading in readings]


def _complete_head_alternative(segment: str, following: str, vesum: VesumLookup) -> str:
    """Complete a head-only alternative: "вразливе / слабке місце" -> "вразливе місце"."""
    if "(" in segment or "(" in following:
        return segment
    units, following_units = _units(_words(segment), vesum), _units(_words(following), vesum)
    count = len(units)
    if not count or count >= len(following_units):
        return segment
    if not all(a[1] & b[1] for a, b in zip(units, following_units[:count], strict=True)):
        return segment
    following_words = list(_WORD_RE.finditer(following))
    return _tidy(f"{segment} {following[following_words[sum(size for size, _ in following_units[:count])].start() :]}")


def correction_answers(correct: str, vesum: VesumLookup | None = None) -> list[str] | None:
    """Corrections a learner may type for ``correct``, or None when a variant is not parallel.

    The source correction itself comes first, then every alternative and variant reading
    it lists. Without VESUM a parenthetical cannot be verified, so only its main
    reading is derived.
    """
    answers = [correct]
    segments = split_alternatives(correct)
    for index, segment in enumerate(segments):
        if vesum is not None and index + 1 < len(segments):
            segment = _complete_head_alternative(segment, segments[index + 1], vesum)
        for reading in _expand_slashed_words(segment):
            expanded = _expand_parentheticals(reading, vesum)
            if expanded is None:
                return None
            answers.extend(expanded)
    return list(dict.fromkeys(answers))


def assess_pair(error: str, correct: str, vesum: VesumLookup | None = None) -> tuple[str | None, str | None]:
    """Validate an error→correction pair against its own text and VESUM.

    Returns ``(evidence, None)`` for an accepted pair or ``(None, reason)`` for a
    withheld one. Evidence kinds:

    * ``shared_stem`` — the two sides share a word or stem (minimal-pair edit);
    * ``pos_parallel`` — multi-word sides with the same VESUM part-of-speech sequence;
    * ``vesum_marked_error`` / ``vesum_unattested_error`` — a single-word error that
      VESUM itself records as an error, or does not know as Ukrainian at all;
    * ``parallel_shape`` / ``table_row`` — structural-only evidence used when VESUM is
      unavailable (audit fallback; the extractor always runs with VESUM).

    A correction whose parenthetical variant is not parallel to its main form is
    withheld (language review of #8723).
    """
    reason = _shape_reason(error, correct)
    if reason:
        return None, reason

    error_words, correct_words = _words(error), _words(correct)
    shared = _alignment_score(error_words, correct_words) > 0

    if vesum is not None:
        for word in correct_words:
            if vesum.status(word) == "unattested":
                return None, "correct_form_unattested_in_vesum"
        if correction_answers(correct, vesum) is None:
            return None, "non_parallel_parenthetical_variant"

    if len(error_words) == 1:
        if vesum is None:
            return ("shared_stem" if shared else "table_row"), None
        status = vesum.status(error_words[0])
        if status == "clean":
            # VESUM lists the "error" as standard Ukrainian: the claim is contested
            # until a source adjudicates it (e.g. україномовний, #8723).
            return None, "error_form_standard_in_vesum"
        if len(correct_words) == 1:
            error_pos, correct_pos = vesum.pos(error_words[0]), vesum.pos(correct_words[0])
            if error_pos and correct_pos and not error_pos & correct_pos:
                return None, "part_of_speech_mismatch"
        return f"vesum_{status}_error", None

    if shared:
        return "shared_stem", None
    if len(error_words) == len(correct_words):
        if vesum is None:
            return "parallel_shape", None
        if all(vesum.pos(a) & vesum.pos(b) for a, b in zip(error_words, correct_words, strict=True)):
            return "pos_parallel", None
    return None, "unrelated_replacement"


def split_contrastive_row(line: str, vesum: VesumLookup | None = None) -> tuple[str, str] | str:
    """Split one horizontal table row "<incorrect> <correct>" at an evidenced point."""
    split = _split_row(line, vesum)
    return split if isinstance(split, str) else split[:2]


def _split_row(line: str, vesum: VesumLookup | None = None) -> tuple[str, str, str] | str:
    """Split a table row into ``(error, correct, basis)`` or return a withhold reason.

    Returns ``(error, correct)`` or a withhold reason. Candidate split points must
    leave both sides well-formed. A split is evidenced when the two sides open or
    close with related words ("влучний вираз | влучний вислів", "виписка з
    протоколу | витяг з протоколу"); ties go to the most aligned words, then to a
    repeated opening word. Without edge evidence the row must have exactly one legal
    split, or a VESUM part-of-speech parallel at its midpoint; otherwise the split
    is ambiguous and the row is withheld.
    """
    tokens = line.split()
    if len(tokens) < 2:
        return "row_has_one_token"
    legal: list[tuple[int, str, str]] = []
    for k in range(1, len(tokens)):
        error, correct = " ".join(tokens[:k]), " ".join(tokens[k:])
        if _shape_reason(error, correct) is None:
            legal.append((k, error, correct))
    if not legal:
        return _shape_reason(" ".join(tokens[:1]), " ".join(tokens[1:])) or "no_legal_split"

    edged = []
    for _k, error, correct in legal:
        error_words, correct_words = _words(error), _words(correct)
        head = _related(error_words[0], correct_words[0])
        tail = _related(error_words[-1], correct_words[-1])
        if head or tail:
            edged.append((_alignment_score(error_words, correct_words), head, error, correct))
    if edged:
        best = max(score for score, *_ in edged)
        top = [row for row in edged if row[0] == best]
        if len(top) > 1:
            top = [row for row in top if row[1]]
        if len(top) == 1:
            return top[0][2], top[0][3], "edge"
        return "ambiguous_split"

    if len(legal) == 1:
        return legal[0][1], legal[0][2], "unique"
    if vesum is not None and len(tokens) % 2 == 0:
        half = len(tokens) // 2
        for k, error, correct in legal:
            if k == half and assess_pair(error, correct, vesum)[0] == "pos_parallel":
                return error, correct, "pos_parallel"
    return "ambiguous_split"


def interleaved_with_next_row(error: str, correct: str, next_row: str | None) -> bool:
    """True when the correction carries words of the following table row.

    Broken PDF columns can merge two rows ("не дивлячись на труднощі кумедна
    собака незважаючи на (попри) труднощі" + "кумедний собака"): the next row is
    then a leftover fragment whose every word sits among the correction's extra
    words (those that do not come from the error).
    """
    if not next_row:
        return False
    error_words = _words(error)
    extras = [w for w in _words(correct) if not any(_related(w, e) for e in error_words)]
    next_words = [w for w in _words(next_row) if len(w) >= 3]
    return bool(extras and next_words) and all(any(_related(n, w) for w in extras) for n in next_words)


# ---------------------------------------------------------------------------
# Source parsers
# ---------------------------------------------------------------------------


def _withhold(
    withheld: list[dict[str, Any]] | None,
    source: str,
    reason: str,
    *,
    line: str = "",
    error: str = "",
    correct: str = "",
) -> None:
    if withheld is not None:
        withheld.append({"source": source, "reason": reason, "line": line, "error": error, "correct": correct})


def _is_table_stop(line: str) -> bool:
    """Lines that end a table: numbered/lettered exercises, headings, prose."""
    return (
        bool(_TABLE_STOP_RE.match(line))
        or (line.isupper() and len(line) > 10)
        or len(line) > _MAX_ROW_CHARS
        or " — " in line
        or ":" in line
        or len(line.split()) < 2
        # Prose and titles; capitalised table rows are exclamations ("Велике дякую!").
        or (bool(_UPPER_START_RE.match(line)) and "!" not in line)
    )


def _horizontal_rows(lines: list[str], start: int) -> Iterable[str]:
    for line in lines[start : start + _MAX_TABLE_ROWS]:
        if _is_table_stop(line) or _HORIZONTAL_HEADER_RE.search(line):
            return
        yield line


def _header_order(line: str) -> str | None:
    """Column order named by a table header line: "error_first" / "correct_first"."""
    match = _ANY_HEADER_RE.search(line)
    if not match:
        return None
    first, second = match.group(1).casefold(), match.group(2).casefold()
    if first == second:
        return None
    preceding = line[: match.start(1)].split()
    if preceding and preceding[-1].casefold() in {"правильно", "неправильно"}:
        return None  # four-column layout ("Правильно НЕправильно Правильно НЕправильно")
    return "error_first" if first == "неправильно" else "correct_first"


def _vertical_rows(lines: list[str], start: int) -> list[str] | None:
    rows: list[str] = []
    for line in lines[start:]:
        if (
            _TABLE_STOP_RE.match(line)
            or not _LOWER_START_RE.match(line)
            or _ALTERNATIVES_ROW_RE.match(line)  # a separate "уключи / увімкни" list
            or len(line) > MAX_PHRASE_CHARS
            or _ANY_HEADER_RE.search(line)
        ):
            break
        if "[" in line or "]" in line:
            return None  # phonetic transcription table, not word usage
        rows.append(line)
    return rows


def _vertical_pairs(rows: list[str], order: str) -> list[tuple[str, str]] | None:
    """Pair a vertical table's rows as ``(error, correct)``, or None when unaligned.

    Two layouts occur: column blocks (all of one column, then all of the other) and
    interleaved rows (a pair per two lines). The layout whose pairs share stems more
    often (then more words) wins; at least two thirds of its pairs must share one.
    Equal evidence for both layouts is ambiguous.
    """
    if not rows or len(rows) % 2:
        return None
    half = len(rows) // 2
    layouts = [list(zip(rows[:half], rows[half:], strict=True)), list(zip(rows[0::2], rows[1::2], strict=True))]
    if order == "correct_first":
        layouts = [[(e, c) for c, e in layout] for layout in layouts]

    def strength(layout: list[tuple[str, str]]) -> tuple[int, int]:
        scores = [_alignment_score(_words(e), _words(c)) for e, c in layout]
        return sum(score > 0 for score in scores), sum(scores)

    ranked = sorted(layouts, key=strength, reverse=True)
    best = strength(ranked[0])
    if len(rows) > 2 and best == strength(ranked[1]):
        return None
    if best[0] * 3 < half * 2:
        return None
    return ranked[0]


def _textbook_source(grade: Any, author: str, title: str) -> str:
    return f"Textbook Gr {grade} ({author or title})"


def parse_contrastive_textbook_tables(
    conn: sqlite3.Connection,
    vesum: VesumLookup | None = None,
    withheld: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Extract НЕПРАВИЛЬНО → ПРАВИЛЬНО pairs from school-textbook contrast tables."""
    query = """
    SELECT grade, author, title, text
    FROM textbooks
    WHERE text LIKE '%ПРАВИЛЬНО%' OR text LIKE '%равильно%'
    ORDER BY id
    """
    results = []
    seen = set()

    def accept(error: str, correct: str, source: str, grade: Any, line: str, *, inferred_rows: bool = False) -> None:
        evidence, reason = assess_pair(error, correct, vesum)
        if evidence in {"pos_parallel", "parallel_shape"} and inferred_rows:
            # Vertical columns are paired by position; a bare part-of-speech parallel
            # cannot tell a real pair from a column shifted by a wrapped line.
            evidence, reason = None, "vertical_pair_without_shared_stem"
        if reason:
            _withhold(withheld, source, reason, line=line, error=error, correct=correct)
            return
        pair_key = (error.casefold(), correct.casefold())
        if pair_key in seen:
            return
        seen.add(pair_key)
        results.append(
            {
                "source": source,
                "error": error,
                "correct": correct,
                "category": "lexical_norm",
                "grade": grade,
                "evidence": evidence,
            }
        )

    def horizontal(rows: list[str], source: str, grade: Any, *, correct_first: bool = False) -> None:
        for row, next_row in zip(rows, [*rows[1:], None], strict=True):
            split = _split_row(row, vesum)
            if isinstance(split, str):
                _withhold(withheld, source, split, line=row)
                continue
            error, correct = (split[1], split[0]) if correct_first else split[:2]
            if interleaved_with_next_row(error, correct, next_row):
                _withhold(withheld, source, "row_interleaved_with_next_row", line=row)
            else:
                accept(error, correct, source, grade, row)

    for grade, author, title, text in conn.execute(query):
        source = _textbook_source(grade, author, title)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            if _HORIZONTAL_HEADER_RE.search(line):
                horizontal(list(_horizontal_rows(lines, idx + 1)), source, grade)
                continue
            order = _header_order(line)
            if order is None:
                continue
            rows = _vertical_rows(lines, idx + 1)
            if rows is None:
                _withhold(withheld, source, "phonetic_transcription_table", line=line)
                continue
            if not rows:
                continue
            pairs = _vertical_pairs(rows, order)
            if pairs:
                for error, correct in pairs:
                    accept(error, correct, source, grade, f"{error} | {correct}", inferred_rows=True)
            elif all(not isinstance(split := _split_row(row, vesum), str) and split[2] == "edge" for row in rows):
                # A header over one-line pairs ("звук звучить звук лунає").
                horizontal(rows, source, grade, correct_first=order == "correct_first")
            else:
                _withhold(withheld, source, "vertical_table_unaligned", line=" | ".join(rows))

    return results


def parse_style_guide_entries(
    conn: sqlite3.Connection,
    vesum: VesumLookup | None = None,
    withheld: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Extract stylistic corrections and explanations from Antonenko-Davydovych."""
    query = """
    SELECT word, section, text
    FROM style_guide
    ORDER BY id
    """
    results = []
    seen = set()

    for word, section, text in conn.execute(query):
        # Look for explicit quotation contrast patterns in text
        # e.g. Неправильно: ... а треба ... / Замість ... слід казати ...
        matches = re.findall(
            r"(?i)(?:не\s+можна\s+казати|замість|неправильно)[^«\"']*[«\"']([^»\"']+)[»\"'][^«\"']*(?:слід|треба|правильно)[^«\"']*[«\"']([^»\"']+)[»\"']",
            text,
        )
        source = f"Antonenko-Davydovych: {word} ({section})"
        for bad, good in matches:
            bad = " ".join(bad.split())
            good = " ".join(good.split())
            evidence, reason = assess_pair(bad, good, vesum)
            if reason:
                _withhold(withheld, source, reason, error=bad, correct=good)
                continue
            pair_key = (bad.lower(), good.lower())
            if pair_key in seen:
                continue
            seen.add(pair_key)

            # First sentence of text as explanation
            first_sent = text.split(".")[0].strip().replace("\n", " ")
            explanation = first_sent if len(first_sent) < 160 else f"Норма слововживання: {word}"

            results.append(
                {
                    "source": source,
                    "error": bad,
                    "correct": good,
                    "explanation": explanation,
                    "category": "style_norm",
                    "evidence": evidence,
                }
            )

    return results


def withhold_conflicting_pairs(
    pairs: list[dict[str, Any]], withheld: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    """Drop pairs whose sources contradict each other (A→B in one, B→A in another)."""
    keys = {(p["error"].casefold(), p["correct"].casefold()) for p in pairs}
    kept = []
    for pair in pairs:
        if (pair["correct"].casefold(), pair["error"].casefold()) in keys:
            _withhold(
                withheld,
                pair["source"],
                "conflicting_sources",
                error=pair["error"],
                correct=pair["correct"],
            )
            continue
        kept.append(pair)
    return kept


def pair_key(error: str, correct: str) -> tuple[str, str]:
    """Text key of a pair, stable across regeneration (ids are positional)."""

    def norm(text: str) -> str:
        return _tidy(re.sub(f"[{_APOSTROPHES}]", "’", text)).casefold()

    return norm(error), norm(correct)


def load_reviewed_withholds(path: Path | str = REVIEWED_WITHHELD_PATH) -> dict[tuple[str, str], dict[str, Any]]:
    """Pairs a language reviewer rejected, keyed by ``pair_key``."""
    entries = (yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}).get("withheld") or []
    reviewed: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        missing = [field for field in ("error", "correct", "code", "reason", "reviewer") if not entry.get(field)]
        if missing:
            raise ValueError(f"{path}: withheld entry {entry!r} lacks {missing}")
        if entry["code"] not in REVIEW_CODES:
            raise ValueError(f"{path}: unknown review code {entry['code']!r} (expected one of {sorted(REVIEW_CODES)})")
        key = pair_key(entry["error"], entry["correct"])
        if key in reviewed:
            raise ValueError(f"{path}: duplicate withheld pair {entry['error']!r} → {entry['correct']!r}")
        reviewed[key] = entry
    return reviewed


def apply_reviewed_withholds(
    pairs: list[dict[str, Any]],
    reviewed: dict[tuple[str, str], dict[str, Any]],
    withheld: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Drop the pairs a language reviewer rejected, recording the review code as reason."""
    kept = []
    for pair in pairs:
        entry = reviewed.get(pair_key(pair["error"], pair["correct"]))
        if entry is None:
            kept.append(pair)
            continue
        _withhold(
            withheld,
            pair["source"],
            f"reviewed_{entry['code'].lower()}",
            error=pair["error"],
            correct=pair["correct"],
        )
    return kept


# ---------------------------------------------------------------------------
# Drill + deck assembly
# ---------------------------------------------------------------------------


def create_error_correction_drill(
    error_phrase: str,
    correct_phrase: str,
    explanation: str | None = None,
    source: str = "textbook",
    answers: list[str] | None = None,
) -> dict[str, Any]:
    """Format an error-correction drill conforming to ErrorCorrectionItemProps.

    Options are only the two forms the source itself contrasts; no distractor is
    invented (the pre-#8723 builder appended "(розм.)"/"(застаріле)" labels).
    ``answers`` are the corrections a learner may type (``correction_answers``).
    """
    sentence = f"Уважно прочитайте: «{error_phrase}» — тут допущено помилку."
    expl = explanation or f"Правильно вживати «{correct_phrase}» замість помилкового «{error_phrase}»."

    return {
        "sentence": sentence,
        "errorWord": error_phrase,
        "correctForm": correct_phrase,
        "options": sorted([correct_phrase, error_phrase]),
        "answers": answers or [correct_phrase],
        "explanation": expl,
        "isUkrainian": True,
        "source": source,
    }


def build_culture_deck(drills: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap drills in the bundled Culture-of-Speech deck shape with stable ordinal ids."""
    numbered = [{"id": f"err_{idx:04d}", **drill} for idx, drill in enumerate(drills, 1)]
    return {
        "deckId": CULTURE_DECK_ID,
        "title": CULTURE_DECK_TITLE,
        "titleEn": CULTURE_DECK_TITLE_EN,
        "totalDrills": len(numbered),
        "drills": numbered,
    }


def extract_error_correction_deck(
    conn: sqlite3.Connection,
    vesum: VesumLookup | None = None,
    withheld: list[dict[str, Any]] | None = None,
    *,
    reviewed: dict[tuple[str, str], dict[str, Any]] | None = None,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    textbook_pairs = parse_contrastive_textbook_tables(conn, vesum, withheld)
    style_pairs = parse_style_guide_entries(conn, vesum, withheld)
    log(f"Extracted {len(textbook_pairs)} textbook contrastive pairs.")
    log(f"Extracted {len(style_pairs)} style-guide contrastive pairs.")
    pairs = withhold_conflicting_pairs(textbook_pairs + style_pairs, withheld)
    if reviewed:
        already = {pair_key(row["error"], row["correct"]) for row in withheld or []} & reviewed.keys()
        before = len(pairs)
        pairs = apply_reviewed_withholds(pairs, reviewed, withheld)
        log(
            f"Reviewed withholds: {before - len(pairs)} applied, {len(already)} already withheld by a rule, "
            f"{len(reviewed) - (before - len(pairs)) - len(already)} not extracted."
        )

    drills = [
        create_error_correction_drill(
            item["error"],
            item["correct"],
            explanation=item.get("explanation"),
            source=item["source"],
            answers=correction_answers(item["correct"], vesum),
        )
        for item in pairs
    ]
    log(f"Total error-correction drills synthesized: {len(drills)}")
    return build_culture_deck(drills)


def main():
    parser = argparse.ArgumentParser(description="Extract error-correction drills from textbooks and style guide.")
    parser.add_argument("--db", type=Path, default=Path("data/sources.db"), help="Path to sources.db")
    parser.add_argument("--vesum-db", type=Path, default=Path("data/vesum.db"), help="Path to vesum.db")
    parser.add_argument(
        "--export-json",
        type=Path,
        action="append",
        default=[],
        help="Write the deck JSON here (repeatable: site bundle and registry copy)",
    )
    parser.add_argument("--withheld-json", type=Path, help="Write withheld source rows with reasons here")
    parser.add_argument(
        "--reviewed-withheld",
        type=Path,
        default=REVIEWED_WITHHELD_PATH,
        help="Reviewed list of pairs to withhold (language review)",
    )
    parser.add_argument("--check-string", type=str, help="Test if string is intentional error context")
    args = parser.parse_args()

    if args.check_string:
        flag = is_intentional_error_context(args.check_string)
        print(f"Is intentional error context: {flag}")
        return

    if not args.vesum_db.exists():
        parser.error(f"VESUM database not found: {args.vesum_db} (required to corroborate single-word claims)")

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    withheld: list[dict[str, Any]] = []
    deck = extract_error_correction_deck(
        conn, VesumLookup(args.vesum_db), withheld, reviewed=load_reviewed_withholds(args.reviewed_withheld)
    )
    print(f"Withheld {len(withheld)} source rows.")

    for path in args.export_json:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(deck, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Exported drills to {path}")
    if args.withheld_json:
        args.withheld_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.withheld_json, "w", encoding="utf-8") as f:
            json.dump({"withheld": withheld}, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Exported withheld rows to {args.withheld_json}")


if __name__ == "__main__":
    main()
