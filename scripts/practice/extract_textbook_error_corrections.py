#!/usr/bin/env python3
"""Extract intentional error-correction exercises from Ukrainian textbooks and style guides.

Also provides guardrail classifiers to prevent naive cloze/reading pipelines from ingesting
deliberate pedagogical errors from textbook exercise prompts.

Every extracted pair must be backed by its source (#8723): a row of a real
НЕПРАВИЛЬНО/ПРАВИЛЬНО table (or a style-guide contrast), split at a point the row
itself evidences, and — for single-word lexical claims — corroborated by VESUM.
Each drill is bound to that exact source row: ``sourceRef`` names the
``sources.db`` row (``textbooks:<id>`` / ``style_guide:<id>``), the character spans
of the marked error and of its correction in the row text, and their direction.
The committed evidence snapshot records, per drill, the row id, the SHA-256 of the
row text and the two span strings, so the gate can check drills without
``sources.db`` and re-derive every pair from its row when the database is present.
Anything the sources cannot decide is withheld with a reason instead of guessed.

Regenerate the bundled Culture-of-Speech deck (and the audited registry copy):

    .venv/bin/python scripts/practice/extract_textbook_error_corrections.py \\
        --db data/sources.db --vesum-db data/vesum.db \\
        --export-json site/src/data/practice-error-corrections.json \\
        --export-json registry/practice/textbook-error-corrections.json \\
        --evidence-json registry/practice/error-correction-evidence.json \\
        --withheld-json /tmp/error-corrections-withheld.json

Pairs a language reviewer rejected are withheld by their text through the committed,
reviewed list ``registry/practice/error-correction-withheld.yaml``.
"""

import argparse
import hashlib
import json
import re
import unicodedata
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import yaml

from scripts.lib.readonly_sqlite import SQLiteConnection
from scripts.lib.readonly_sqlite import open_readonly as _open_readonly

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
EVIDENCE_SNAPSHOT_PATH = Path(__file__).resolve().parents[2] / "registry/practice/error-correction-evidence.json"
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

# ``sourceRef.rowId``: the sources.db table and row a drill was read from.
_ROW_ID_RE = re.compile(r"^(textbooks|style_guide):([1-9]\d*)$")
DIRECTIONS = ("error_first", "correct_first")


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
        self._conn = _open_readonly(Path(db_path))
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


def _changed_words(left: list[str], right: list[str]) -> tuple[list[str], list[str]]:
    """Words of each side left unaligned by ``_alignment_score``: what the edit replaces, adds or drops.

    Aligned words are the same word or share a stem ("нетактична"/"нетактовна");
    "брати участь" → "купити участь" leaves ``(["брати"], ["купити"])``.
    """
    rows = [[0] * (len(right) + 1) for _ in range(len(left) + 1)]
    for i in range(len(left) - 1, -1, -1):
        for j in range(len(right) - 1, -1, -1):
            if _related(left[i], right[j]):
                rows[i][j] = rows[i + 1][j + 1] + 1
            else:
                rows[i][j] = max(rows[i + 1][j], rows[i][j + 1])
    i = j = 0
    changed_left: list[str] = []
    changed_right: list[str] = []
    while i < len(left) and j < len(right):
        if _related(left[i], right[j]) and rows[i][j] == rows[i + 1][j + 1] + 1:
            i, j = i + 1, j + 1
        elif rows[i + 1][j] >= rows[i][j + 1]:
            changed_left.append(left[i])
            i += 1
        else:
            changed_right.append(right[j])
            j += 1
    return changed_left + left[i:], changed_right + right[j:]


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


def typed_answer_key(value: str) -> str:
    """Comparison key of a typed correction, as the site grades it.

    Mirrors ``normalizeTypedCorrection`` in ``site/src/components/ErrorCorrection.tsx``:
    stress marks, case, apostrophe variants, spacing around ``, ; :`` and final
    punctuation do not change an answer.
    """
    text = unicodedata.normalize("NFC", unicodedata.normalize("NFD", value).replace("\u0301", ""))
    text = re.sub("['ʼʹ`‘]", "’", text).lower()
    text = re.sub(r"\s*([,;:])\s*", r"\1 ", text)
    text = re.sub(r"\s+", " ", text)
    return re.sub(r"[\s.!?…,;:]+$", "", text).strip()


def assess_pair(error: str, correct: str, vesum: VesumLookup | None = None) -> tuple[str | None, str | None]:
    """Validate the text of an error→correction pair against VESUM.

    Returns ``(evidence, None)`` for a well-formed pair or ``(None, reason)`` for a
    withheld one. The evidence label names what backs the words the pair changes:

    * ``shared_stem`` — every changed word shares a stem with its replacement
      ("нетактична поведінка" → "нетактовна поведінка");
    * ``vesum_marked_error`` / ``vesum_unattested_error`` — VESUM records a changed
      error word as an error, or does not know it as Ukrainian;
    * ``source_row`` — a standard word replaced, added or dropped ("приймати участь"
      → "брати участь"): only the source's own contrast row evidences that.

    None of these makes a pair publishable on its own: a kept word or one marked
    error word says nothing about the rest of the edit ("брати участь" → "купити
    участь", "проявляти недостатки" → "становити інтерес"). Every drill is bound to
    its source row by ``sourceRef``, which the gate verifies.

    Multi-word sides that share no word must also be parallel (same length and, with
    VESUM, the same part of speech word by word). A correction whose parenthetical
    variant is not parallel to its main form is withheld (language review of #8723).
    """
    reason = _shape_reason(error, correct)
    if reason:
        return None, reason

    error_words, correct_words = _words(error), _words(correct)

    if vesum is not None:
        for word in correct_words:
            if vesum.status(word) == "unattested":
                return None, "correct_form_unattested_in_vesum"
        if correction_answers(correct, vesum) is None:
            return None, "non_parallel_parenthetical_variant"

    if len(error_words) == 1 and vesum is not None:
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

    if len(error_words) > 1 and _alignment_score(error_words, correct_words) == 0:
        if len(error_words) != len(correct_words):
            return None, "unrelated_replacement"
        if vesum is not None and not all(
            vesum.pos(a) & vesum.pos(b) for a, b in zip(error_words, correct_words, strict=True)
        ):
            return None, "unrelated_replacement"

    changed_error, changed_correct = _changed_words(error_words, correct_words)
    if not changed_error and not changed_correct:
        return "shared_stem", None
    if vesum is not None:
        statuses = {vesum.status(word) for word in changed_error} - {"clean"}
        if statuses:
            return ("vesum_marked_error" if "marked" in statuses else "vesum_unattested_error"), None
    return "source_row", None


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
            if (
                k == half
                and _alignment_score(_words(error), _words(correct)) == 0
                and assess_pair(error, correct, vesum)[1] is None
            ):
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


def _horizontal_rows(lines: list[str], start: int) -> list[int]:
    """Indices of the one-line rows of the horizontal table whose header is ``lines[start - 1]``."""
    rows = []
    for index in range(start, min(start + _MAX_TABLE_ROWS, len(lines))):
        if _is_table_stop(lines[index]) or _HORIZONTAL_HEADER_RE.search(lines[index]):
            break
        rows.append(index)
    return rows


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


def _vertical_rows(lines: list[str], start: int) -> list[int] | None:
    """Indices of the column cells under a vertical table header, or None for a phonetic table."""
    rows: list[int] = []
    for index in range(start, len(lines)):
        line = lines[index]
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
        rows.append(index)
    return rows


def _vertical_pairs(rows: list[str], order: str) -> list[tuple[int, int]] | None:
    """Pair a vertical table's rows as ``(error index, correct index)``, or None when unaligned.

    Two layouts occur: column blocks (all of one column, then all of the other) and
    interleaved rows (a pair per two lines). The layout whose pairs share stems more
    often (then more words) wins; at least two thirds of its pairs must share one.
    Equal evidence for both layouts is ambiguous.
    """
    if not rows or len(rows) % 2:
        return None
    half = len(rows) // 2
    layouts = [
        list(zip(range(half), range(half, len(rows)), strict=True)),
        list(zip(range(0, len(rows), 2), range(1, len(rows), 2), strict=True)),
    ]
    if order == "correct_first":
        layouts = [[(e, c) for c, e in layout] for layout in layouts]

    def strength(layout: list[tuple[int, int]]) -> tuple[int, int]:
        scores = [_alignment_score(_words(rows[e]), _words(rows[c])) for e, c in layout]
        return sum(score > 0 for score in scores), sum(scores)

    ranked = sorted(layouts, key=strength, reverse=True)
    best = strength(ranked[0])
    if len(rows) > 2 and best == strength(ranked[1]):
        return None
    if best[0] * 3 < half * 2:
        return None
    return ranked[0]


def _source_lines(text: str) -> list[tuple[str, int]]:
    """Non-blank lines of a source text, stripped, each with the offset of its first character."""
    lines, offset = [], 0
    for raw in text.splitlines(keepends=True):
        stripped = raw.strip()
        if stripped:
            lines.append((stripped, offset + len(raw) - len(raw.lstrip())))
        offset += len(raw)
    return lines


def _split_spans(line: str, offset: int, left_tokens: int) -> tuple[list[int], list[int]]:
    """Character spans of a row's two sides when its first ``left_tokens`` tokens form the left one."""
    tokens = [match.span() for match in re.finditer(r"\S+", line)]
    return (
        [offset + tokens[0][0], offset + tokens[left_tokens - 1][1]],
        [offset + tokens[left_tokens][0], offset + tokens[-1][1]],
    )


def span_text(text: str, span: list[int] | tuple[int, int]) -> str:
    """The phrase at ``span`` of a source text, whitespace collapsed as the drills store it."""
    start, end = span
    return " ".join(text[start:end].split())


def textbook_row_pairs(
    text: str,
    vesum: VesumLookup | None = None,
    withheld: list[dict[str, Any]] | None = None,
    source: str = "",
) -> list[dict[str, Any]]:
    """Accepted НЕПРАВИЛЬНО → ПРАВИЛЬНО pairs of one textbook text, each bound to its spans.

    Every pair carries ``error``, ``correct``, ``evidence``, the character spans
    ``errorSpan`` / ``correctSpan`` of both sides in ``text`` and the ``direction``
    ("error_first" when the error column precedes the correction). A cross-row
    combination (one row's error with another row's correction) is never derived.
    """
    lines = _source_lines(text)
    texts = [line for line, _ in lines]
    pairs: list[dict[str, Any]] = []

    def accept(
        error: str,
        correct: str,
        line: str,
        spans: tuple[list[int], list[int]],
        direction: str,
        *,
        inferred_rows: bool = False,
    ) -> None:
        evidence, reason = assess_pair(error, correct, vesum)
        if (
            evidence
            and inferred_rows
            and len(_words(error)) > 1
            and _alignment_score(_words(error), _words(correct)) == 0
        ):
            # Vertical columns are paired by position; a bare part-of-speech parallel
            # cannot tell a real pair from a column shifted by a wrapped line.
            evidence, reason = None, "vertical_pair_without_shared_stem"
        if reason:
            _withhold(withheld, source, reason, line=line, error=error, correct=correct)
            return
        pairs.append(
            {
                "error": error,
                "correct": correct,
                "evidence": evidence,
                "errorSpan": spans[0],
                "correctSpan": spans[1],
                "direction": direction,
            }
        )

    def horizontal(rows: list[int], *, correct_first: bool = False) -> None:
        for index, next_index in zip(rows, [*rows[1:], None], strict=True):
            row, offset = lines[index]
            split = _split_row(row, vesum)
            if isinstance(split, str):
                _withhold(withheld, source, split, line=row)
                continue
            left, right = split[:2]
            left_span, right_span = _split_spans(row, offset, len(left.split()))
            if correct_first:
                error, correct, spans, direction = right, left, (right_span, left_span), "correct_first"
            else:
                error, correct, spans, direction = left, right, (left_span, right_span), "error_first"
            if interleaved_with_next_row(error, correct, texts[next_index] if next_index is not None else None):
                _withhold(withheld, source, "row_interleaved_with_next_row", line=row)
            else:
                accept(error, correct, row, spans, direction)

    for idx, line in enumerate(texts):
        if _HORIZONTAL_HEADER_RE.search(line):
            horizontal(_horizontal_rows(texts, idx + 1))
            continue
        order = _header_order(line)
        if order is None:
            continue
        rows = _vertical_rows(texts, idx + 1)
        if rows is None:
            _withhold(withheld, source, "phonetic_transcription_table", line=line)
            continue
        if not rows:
            continue
        cells = [texts[index] for index in rows]
        pairs_at = _vertical_pairs(cells, order)
        if pairs_at:
            for error_at, correct_at in pairs_at:
                # Each column cell is a whole source line.
                (error_cell, error_offset), (correct_cell, correct_offset) = (
                    lines[rows[error_at]],
                    lines[rows[correct_at]],
                )
                accept(
                    " ".join(error_cell.split()),
                    " ".join(correct_cell.split()),
                    f"{error_cell} | {correct_cell}",
                    (
                        [error_offset, error_offset + len(error_cell)],
                        [correct_offset, correct_offset + len(correct_cell)],
                    ),
                    order,
                    inferred_rows=True,
                )
        elif all(not isinstance(split := _split_row(cell, vesum), str) and split[2] == "edge" for cell in cells):
            # A header over one-line pairs ("звук звучить звук лунає").
            horizontal(rows, correct_first=order == "correct_first")
        else:
            _withhold(withheld, source, "vertical_table_unaligned", line=" | ".join(cells))
    return pairs


# Explicit quotation contrasts: «Неправильно: … а треба …» / «Замість … слід казати …».
_STYLE_CONTRAST_RE = re.compile(
    r"(?i)(?:не\s+можна\s+казати|замість|неправильно)[^«\"']*[«\"']([^»\"']+)[»\"'][^«\"']*(?:слід|треба|правильно)[^«\"']*[«\"']([^»\"']+)[»\"']"
)


def _tight_span(match: re.Match[str], group: int) -> list[int]:
    start, end = match.span(group)
    value = match.group(group)
    return [start + len(value) - len(value.lstrip()), end - len(value) + len(value.rstrip())]


def style_guide_row_pairs(
    text: str,
    vesum: VesumLookup | None = None,
    withheld: list[dict[str, Any]] | None = None,
    source: str = "",
) -> list[dict[str, Any]]:
    """Accepted quotation contrasts of one style-guide entry, bound to their spans like ``textbook_row_pairs``."""
    pairs = []
    for match in _STYLE_CONTRAST_RE.finditer(text):
        bad = " ".join(match.group(1).split())
        good = " ".join(match.group(2).split())
        evidence, reason = assess_pair(bad, good, vesum)
        if reason:
            _withhold(withheld, source, reason, error=bad, correct=good)
            continue
        pairs.append(
            {
                "error": bad,
                "correct": good,
                "evidence": evidence,
                "errorSpan": _tight_span(match, 1),
                "correctSpan": _tight_span(match, 2),
                "direction": "error_first",
            }
        )
    return pairs


_ROW_PARSERS: dict[str, Callable[..., list[dict[str, Any]]]] = {
    "textbooks": textbook_row_pairs,
    "style_guide": style_guide_row_pairs,
}


def derive_row_pairs(row_id: str, text: str, vesum: VesumLookup | None = None) -> list[dict[str, Any]]:
    """The pairs the extractor derives from one source row (before cross-row dedup and review)."""
    match = _ROW_ID_RE.match(row_id)
    if not match:
        raise ValueError(f"not a source row id: {row_id!r}")
    return _ROW_PARSERS[match.group(1)](text, vesum)


def source_ref_problem(ref: Any) -> str | None:
    """Why a drill's ``sourceRef`` cannot bind it to a source row, else None."""
    if not isinstance(ref, dict):
        return "missing sourceRef"
    if not isinstance(ref.get("rowId"), str) or not _ROW_ID_RE.match(ref["rowId"]):
        return f"rowId {ref.get('rowId')!r} is not textbooks:<id> or style_guide:<id>"
    spans = [ref.get("errorSpan"), ref.get("correctSpan")]
    for span in spans:
        if not (
            isinstance(span, list)
            and len(span) == 2
            and all(isinstance(bound, int) and not isinstance(bound, bool) for bound in span)
            and 0 <= span[0] < span[1]
        ):
            return f"span {span!r} is not [start, end]"
    error_span, correct_span = spans
    if error_span[1] > correct_span[0] and correct_span[1] > error_span[0]:
        return "error and correction spans overlap"
    if ref.get("direction") not in DIRECTIONS:
        return f"direction {ref.get('direction')!r} is not one of {DIRECTIONS}"
    if (ref["direction"] == "error_first") != (error_span[0] < correct_span[0]):
        return f"spans are not in the {ref['direction']} order"
    return None


def load_source_row(conn: SQLiteConnection, row_id: str) -> str | None:
    """Text of the sources.db row ``row_id`` (``textbooks:<id>`` / ``style_guide:<id>``), or None."""
    match = _ROW_ID_RE.match(row_id or "")
    if not match:
        return None
    row = conn.execute(f"SELECT text FROM {match.group(1)} WHERE id = ?", (int(match.group(2)),)).fetchone()
    return row[0] if row else None


def row_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _textbook_source(grade: Any, author: str, title: str) -> str:
    return f"Textbook Gr {grade} ({author or title})"


def _style_guide_source(word: str, section: str) -> str:
    return f"Antonenko-Davydovych: {word} ({section})"


def source_label_for_row(conn: SQLiteConnection, row_id: str) -> str | None:
    """Learner-visible source label derived from the bound row's metadata."""
    match = _ROW_ID_RE.fullmatch(row_id or "")
    if not match:
        return None
    table, record_id = match.groups()
    if table == "textbooks":
        row = conn.execute("SELECT grade, author, title FROM textbooks WHERE id = ?", (int(record_id),)).fetchone()
        return _textbook_source(*row) if row else None
    row = conn.execute("SELECT word, section FROM style_guide WHERE id = ?", (int(record_id),)).fetchone()
    return _style_guide_source(*row) if row else None


_TEXTBOOK_TABLES_QUERY = """
    SELECT id, grade, author, title, text
    FROM textbooks
    WHERE text LIKE '%ПРАВИЛЬНО%' OR text LIKE '%равильно%'
    ORDER BY id
    """


def _source_ref(table: str, row_id: int, pair: dict[str, Any]) -> dict[str, Any]:
    return {
        "rowId": f"{table}:{row_id}",
        "errorSpan": pair["errorSpan"],
        "correctSpan": pair["correctSpan"],
        "direction": pair["direction"],
    }


def parse_contrastive_textbook_tables(
    conn: SQLiteConnection,
    vesum: VesumLookup | None = None,
    withheld: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Extract НЕПРАВИЛЬНО → ПРАВИЛЬНО pairs from school-textbook contrast tables."""
    results = []
    seen = set()
    for row_id, grade, author, title, text in conn.execute(_TEXTBOOK_TABLES_QUERY):
        source = _textbook_source(grade, author, title)
        for pair in textbook_row_pairs(text, vesum, withheld, source):
            key = (pair["error"].casefold(), pair["correct"].casefold())
            if key in seen:
                continue
            seen.add(key)
            results.append(
                {
                    "source": source,
                    "error": pair["error"],
                    "correct": pair["correct"],
                    "category": "lexical_norm",
                    "grade": grade,
                    "evidence": pair["evidence"],
                    "source_ref": _source_ref("textbooks", row_id, pair),
                }
            )
    return results


def parse_style_guide_entries(
    conn: SQLiteConnection,
    vesum: VesumLookup | None = None,
    withheld: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Extract stylistic corrections and explanations from Antonenko-Davydovych."""
    results = []
    seen = set()
    for row_id, word, section, text in conn.execute("SELECT id, word, section, text FROM style_guide ORDER BY id"):
        source = _style_guide_source(word, section)
        for pair in style_guide_row_pairs(text, vesum, withheld, source):
            key = (pair["error"].lower(), pair["correct"].lower())
            if key in seen:
                continue
            seen.add(key)

            # First sentence of text as explanation
            first_sent = text.split(".")[0].strip().replace("\n", " ")
            explanation = first_sent if len(first_sent) < 160 else f"Норма слововживання: {word}"

            results.append(
                {
                    "source": source,
                    "error": pair["error"],
                    "correct": pair["correct"],
                    "explanation": explanation,
                    "category": "style_norm",
                    "evidence": pair["evidence"],
                    "source_ref": _source_ref("style_guide", row_id, pair),
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
    source_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format an error-correction drill conforming to ErrorCorrectionItemProps.

    Options are only the two forms the source itself contrasts; no distractor is
    invented (the pre-#8723 builder appended "(розм.)"/"(застаріле)" labels).
    ``answers`` are the corrections a learner may type (``correction_answers``);
    ``source_ref`` binds the pair to the source row and spans it was read from.
    """
    sentence = f"Уважно прочитайте: «{error_phrase}» — тут допущено помилку."
    expl = explanation or f"Правильно вживати «{correct_phrase}» замість помилкового «{error_phrase}»."

    drill = {
        "sentence": sentence,
        "errorWord": error_phrase,
        "correctForm": correct_phrase,
        "options": sorted([correct_phrase, error_phrase]),
        "answers": answers or [correct_phrase],
        "explanation": expl,
        "isUkrainian": True,
        "source": source,
    }
    if source_ref:
        drill["sourceRef"] = source_ref
    return drill


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
    conn: SQLiteConnection,
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
            source_ref=item["source_ref"],
        )
        for item in pairs
    ]
    log(f"Total error-correction drills synthesized: {len(drills)}")
    return build_culture_deck(drills)


def build_evidence_snapshot(deck: dict[str, Any], conn: SQLiteConnection) -> dict[str, Any]:
    """Per-drill source evidence, read from sources.db, that the gate checks without the database.

    Each drill id maps to its source ``rowId``, the SHA-256 of that row's text,
    the row-derived display label, and the strings at its error and correction
    spans. A drill that disagrees with its row stops the export.
    """
    evidence: dict[str, dict[str, str]] = {}
    for drill in deck["drills"]:
        ref = drill.get("sourceRef")
        problem = source_ref_problem(ref)
        text = load_source_row(conn, ref["rowId"]) if problem is None else None
        if text is None:
            raise ValueError(f"{drill['id']}: cannot bind to a source row ({problem or 'row not in sources.db'})")
        source = source_label_for_row(conn, ref["rowId"])
        if source is None or drill.get("source") != source:
            raise ValueError(f"{drill['id']}: source label does not match its bound row metadata")
        error, correct = span_text(text, ref["errorSpan"]), span_text(text, ref["correctSpan"])
        if (error, correct) != (drill["errorWord"], drill["correctForm"]):
            raise ValueError(f"{drill['id']}: spans read {error!r} → {correct!r}, not the drill's pair")
        evidence[drill["id"]] = {
            "rowId": ref["rowId"],
            "rowSha256": row_sha256(text),
            "source": source,
            "error": error,
            "correct": correct,
        }
    return {"deckId": deck["deckId"], "drills": evidence}


def load_evidence_snapshot(path: Path | str = EVIDENCE_SNAPSHOT_PATH) -> dict[str, dict[str, str]]:
    """Committed per-drill evidence by drill id; empty when the snapshot file is absent."""
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("drills") or {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


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
    parser.add_argument(
        "--evidence-json",
        type=Path,
        help="Write the per-drill evidence snapshot (row id, row SHA-256, source label, span strings) here",
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

    conn = _open_readonly(args.db)
    withheld: list[dict[str, Any]] = []
    deck = extract_error_correction_deck(
        conn, VesumLookup(args.vesum_db), withheld, reviewed=load_reviewed_withholds(args.reviewed_withheld)
    )
    print(f"Withheld {len(withheld)} source rows.")
    evidence = build_evidence_snapshot(deck, conn)

    for path in args.export_json:
        _write_json(path, deck)
        print(f"Exported drills to {path}")
    if args.evidence_json:
        _write_json(args.evidence_json, evidence)
        print(f"Exported evidence snapshot to {args.evidence_json}")
    if args.withheld_json:
        _write_json(args.withheld_json, {"withheld": withheld})
        print(f"Exported withheld rows to {args.withheld_json}")


if __name__ == "__main__":
    main()
