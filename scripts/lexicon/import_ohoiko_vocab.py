#!/usr/bin/env python3
"""Read-only generator of lexdata L1 records for the Anna Ohoiko dictionary parts (OO-38).

Design r3 §10 (a)/(b). Four sources, each a ``SourceAdapter`` of the typed
record interface ``scripts/lexdata/records.py``:

- ``ohoiko_1000_words``: one unit per ``textbooks`` entry chunk of the
  1000-words book (list grammar ``ohoiko_eq``: ``=`` members are
  ``equivalent_lexeme`` leaves, ``,`` members ``variant`` leaves).
- ``ohoiko_500_verbs``: one unit per verb, the ``textbooks`` chunk joined to
  its ``textbook_sections`` page on ``section_number = entry_no``. Everything
  is parsed from the page's ``full_text``: the aspect pair (perfective members
  are ``aspect_partner`` leaves), stems, every conjugation-table cell
  (``l1_verb_form``), case government and examples. A verb without its page
  is refused ``truncated_source``; the truncated chunk text is never parsed.
- ``oho_a1_workbook_glossary``: the 17 ``Словничок`` pages of the Oho! A1
  workbook at line grain (``scripts/lexicon/oho_workbook_glossary_parse.py``).
- ``ulp_lesson_notes``: the 240 ULP lesson-note sections at line grain; the
  vocabulary zones and margin glosses only (``scripts/lexicon/ulp_glossary_parse.py``).

The parsers never write a database and never derive keys: ``build_store``
derives keys, refusals, rights and fingerprints from these records with the
one lexdata normalizer. Every ``raw_span`` is the printed span byte for byte
(``locate_span``), never the parser's joined view; every repair (a displaced
acute put back, a hyphen wrap joined, a Latin homoglyph or misplaced acute
respelled, an OCR split joined) is a ``proposed_repairs`` entry only. Stress
is the normalizer's verdict on the printed marks: a span printed without a
mark is accepted with stress absent; a printed mark that does not follow one
vowel is refused ``stress_invalid``, and a span with mixed scripts
``homoglyph_mixed_script``, each keeping the proposals.

The CLI is a dry run over ``sources.db`` opened read-only: per-source
conservation, refusals by code, record digests (an unchanged input must give
identical digests), and, for the evaluator only, the §8 held-out samples.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.common.repo_root import main_checkout_root
from scripts.lexdata import records as rec
from scripts.lexdata.canonical import canonical_json, sha256_canonical
from scripts.lexdata.derive import derive_leaf
from scripts.lexdata.normalize import normalize_span
from scripts.lexicon import oho_workbook_glossary_parse as oho
from scripts.lexicon import ulp_glossary_parse as gp
from scripts.lexicon.ohoiko_quality_enrichment import (
    GOVERNMENT_CASE_KEYWORDS,
    GOVERNMENT_LABEL_RE,
    SOURCE_500_VERBS,
    SOURCE_1000_WORDS,
    STEMS_LABEL,
    _extract_500_verbs_government,
    _extract_500_verbs_stems,
    is_grammar_note,
    iter_500_verbs_examples,
    iter_1000_words_examples,
    normalize_500_verbs_lines,
    normalize_chunk_lines,
    parse_500_verbs_head_and_gloss,
    parse_1000_words_head_and_gloss,
)
from scripts.lib.readonly_sqlite import SQLiteConnection, open_readonly
from scripts.storage import topology
from scripts.storage.topology import StoreBinding, StoreRefusal, resolve_store

PARSER_VERSION = "1"
WORDS_SOURCE_ID = "ohoiko_1000_words"
VERBS_SOURCE_ID = "ohoiko_500_verbs"
OHO_SOURCE_ID = "oho_a1_workbook_glossary"
ULP_SOURCE_ID = "ulp_lesson_notes"
SOURCE_IDS = (WORDS_SOURCE_ID, VERBS_SOURCE_ID, OHO_SOURCE_ID, ULP_SOURCE_ID)
ULP_SOURCES = tuple(f"ulp-{season}-00-lesson-notes" for season in range(1, 7))
EXPECTED_UNITS = {WORDS_SOURCE_ID: 1000, VERBS_SOURCE_ID: 500, OHO_SOURCE_ID: 17, ULP_SOURCE_ID: 240}
SAMPLE_SIZES = {"ohoiko_entries": 30, "oho_lines": 30, "ulp_lines": 50}
PROPOSER_REPAIR = "scripts.lexicon.ulp_glossary_parse.repair_ukrainian"
PROPOSER_JOIN = "scripts.lexicon.ulp_glossary_parse.join_split_stress"
PROPOSER_REJOIN = "scripts.lexicon.import_ohoiko_vocab.propose_repairs"


class ParseFailure(ValueError):
    """A unit contradicts its source's grammar; the run stops instead of guessing.

    The refusal catalog (``scripts/lexdata/rule_tables.py``) has no code for a
    structural parse failure, so none is invented here: the failure is
    reported and the generation is not built.
    """

    def __init__(self, code: str, locator: str = "") -> None:
        super().__init__(f"{code}: {locator}" if locator else code)
        self.code = code


# ---------------------------------------------------------------------------
# L0 access (read-only handles only)
# ---------------------------------------------------------------------------


def _dict_rows(conn: SQLiteConnection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor = conn.execute(sql, params)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def _locator(table: str, key: str, value: object) -> str:
    return f"sources:{table}:{key}={value}"


def _l0(table: str, key: str, row: Mapping[str, Any]) -> rec.L0Row:
    return rec.L0Row(_locator(table, key, row[key]), rec.row_fingerprint(row))


def _snapshot(query: str, rows: Iterable[Mapping[str, Any]]) -> rec.SelectionSnapshot:
    prints = [rec.row_fingerprint(row) for row in rows]
    return rec.SelectionSnapshot(query, len(prints), rec.selection_digest(prints))


def _entry_no(chunk_id: str) -> int | None:
    match = re.search(r"_e(\d+)$", chunk_id)
    return int(match.group(1)) if match else None


# ---------------------------------------------------------------------------
# Leaves: one builder for every source
# ---------------------------------------------------------------------------


# Line-wrap repairs, proposed only: an acute the OCR printed at the start of the
# next line together with the word's tail ("клієн" / "́ т"), and a hyphenated
# word wrapped after its hyphen ("соціалісти́чно-" / "комуністи́чний").
_DISPLACED_ACUTE_RE = re.compile(rf"\s*\n\s*{gp.ACUTE}[^\S\n]*")
_HYPHEN_WRAP_RE = re.compile(r"(?<=\w-)\n\s*(?=\w)")


def _collapsed(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def propose_repairs(raw: str, *, join_splits: bool) -> tuple[rec.ProposedRepair, ...]:
    """Repair proposals for one verbatim span, each building on the previous one.

    The span itself is never changed (design r3 §10 (a) point 3): F derives
    the keys and the stress verdict from ``raw_span``; a reviewer may adopt a
    proposal. Line-wrap rejoins come first, then the OCR proposers.
    """
    proposals: list[rec.ProposedRepair] = []
    current = _collapsed(raw)
    for pattern, replacement, kind in ((_DISPLACED_ACUTE_RE, gp.ACUTE, "displaced_acute_rejoined"),
                                       (_HYPHEN_WRAP_RE, "", "line_wrap_hyphen_joined")):
        if pattern.search(raw):
            raw = pattern.sub(replacement, raw)
            current = _collapsed(raw)
            proposals.append(rec.ProposedRepair(PROPOSER_REJOIN, kind, current))
    repaired, codes = gp.repair_ukrainian(current)
    if codes and repaired != current:
        proposals.append(rec.ProposedRepair(PROPOSER_REPAIR, "+".join(sorted(set(codes))), repaired))
        current = repaired
    if join_splits:
        joined, join_codes = gp.join_split_stress(current)
        if join_codes and joined != current:
            proposals.append(rec.ProposedRepair(PROPOSER_JOIN, "+".join(sorted(set(join_codes))), joined))
    return tuple(proposals)


# ---------------------------------------------------------------------------
# Verbatim spans: the parser's view of a span back to the printed source text
# ---------------------------------------------------------------------------

# A line break inside a span (at most one blank line), with the other column's
# text after the span on its line ("автомобі́ль = авто́ =  car" / "маши́на") and
# before it on the next line (a margin head wrapped beside lesson prose): the
# span keeps the line break and leaves the other columns out.
_WRAP = r"(?:[^\S\n]*(?:[^\S\n][^\n]*?)?\n){1,2}(?:[^\n]*?[^\S\n]{2,})?[^\S\n]*"


def _without_other_columns(piece: str) -> str:
    """A wrapped piece as printed, minus the other columns' text on its lines.

    Every line keeps its line break, its blank lines, its indentation and any
    trailing whitespace (``"\\r"`` included); only a line's other-column text,
    from its first character through its last non-space one, is left out.
    """
    if "\n" not in piece:
        return piece
    return "\n".join(line[len(line.rstrip()):] if line.strip() else line for line in piece.split("\n"))


@dataclass(frozen=True)
class SourceSpan:
    start: int
    end: int
    raw: str


def locate_span(text: str, start: int, view: str) -> SourceSpan | None:
    """Find the printed span of ``view`` in ``text`` at or after ``start``.

    ``view`` is what a parser read: whitespace collapsed, wrapped lines joined
    with a space (or ``" / "``), and a displaced acute put back after its
    letters (``клієн́т`` for ``клієн`` / ``́ т``). The returned ``raw`` is the
    printed span byte for byte: every character of the span as printed, with
    each line break, blank line, indentation and ``"\\r"`` it crosses kept, and
    only the text of other columns on those lines left out. ``start``/``end`` are offsets into ``text``.
    """
    parts: list[str] = []
    index = 0
    while index < len(view):
        char = view[index]
        if view.startswith(" / ", index):
            parts.append(rf"([^\S\n]*/[^\S\n]*|{_WRAP})")  # a printed slash stays on its line
            index += 3
        elif char == " ":
            parts.append(rf"([^\S\n]+|{_WRAP})")
            index += 1
        elif char == gp.ACUTE:
            parts.append(rf"((?:{_WRAP})?){gp.ACUTE}([^\S\n]*)")
            index += 1
        else:
            parts.append(re.escape(char))
            index += 1
    match = re.compile("".join(parts)).search(text, start)
    if match is None:
        return None
    raw: list[str] = []
    position = match.start()
    for group in range(1, (match.lastindex or 0) + 1):
        a, b = match.span(group)
        if a < 0:
            continue
        raw.append(text[position:a])
        raw.append(_without_other_columns(text[a:b]))
        position = b
    raw.append(text[position:match.end()])
    return SourceSpan(match.start(), match.end(), "".join(raw))


@dataclass(frozen=True)
class Member:
    raw: str
    role: str
    sense_refs: tuple[int, ...] = ()
    grammar_raw: str | None = None
    grammar_labels: tuple[str, ...] = ()
    span: tuple[int, int] | None = None


@dataclass
class EntryShape:
    """What a parser found for one dictionary entry, as printed."""

    head_raw: str
    members: list[Member]
    senses: list[str] = field(default_factory=list)
    grammar_raw: str | None = None
    grammar_labels: tuple[str, ...] = ()
    examples: list[tuple[str, str]] = field(default_factory=list)
    verb_forms: list[rec.VerbFormRecord] = field(default_factory=list)
    governments: list[str] = field(default_factory=list)
    line_no: int | None = None
    head_span: tuple[int, int] | None = None


def _join(*parts: str | None) -> str | None:
    kept = [part for part in parts if part]
    return "; ".join(kept) or None


@dataclass(frozen=True)
class PrintedText:
    """Where an entry's spans are printed: the unit text, the offset to search
    from, and the offset that ``span_start``/``span_end`` count from (the start
    of line ``line_no`` for line-grain sources, else the start of the text)."""

    text: str
    anchor: int
    origin: int = 0


def entry_items(prefix: str, shape: EntryShape, *, join_splits: bool,
                printed: PrintedText | None = None) -> list[rec.LexItemRecord]:
    """Leaves of one entry: one leaf, or a list parent plus one leaf per member.

    The gloss is printed once per entry, so with several members every member
    carries the senses with ``applies_to='all_members'`` (only the senses its
    ``(1)``/``(2)`` references name, when it has any); examples, government,
    verb forms and entry-level grammar sit on the top item.

    With ``printed``, every leaf's ``raw_span`` is its printed span
    (``locate_span``), never the parser's joined view; a span that cannot be
    found stops the run. Without it (Oho!), the parser's spans are already
    ``line[start:end]``.
    """
    if not shape.members:
        raise ParseFailure("no_forms", prefix)
    sense_count = len(shape.senses)
    top_extra = {
        "examples": tuple(rec.ExampleRecord(n, uk, en) for n, (uk, en) in enumerate(shape.examples, 1)),
        "verb_forms": tuple(shape.verb_forms),
        "governments": tuple(rec.GovernmentRecord(g) for g in shape.governments),
    }
    position = {"line_no": shape.line_no}

    def senses_for(member: Member, applies_to: str) -> tuple[rec.SenseRecord, ...]:
        numbers = member.sense_refs or tuple(range(1, sense_count + 1))
        if any(n < 1 or n > sense_count for n in numbers):
            raise ParseFailure("sense_reference", prefix)
        return tuple(rec.SenseRecord(n, shape.senses[n - 1], applies_to) for n in numbers)

    def printed_span(view: str, start: int, given: tuple[int, int] | None) -> tuple[str, int | None, int | None, int]:
        if printed is None:
            span = given or (None, None)
            return view, span[0], span[1], start
        found = locate_span(printed.text, start, view)
        if found is None:
            raise ParseFailure("raw_span_not_located", f"{prefix}: {view!r}")
        return found.raw, found.start - printed.origin, found.end - printed.origin, found.end

    def leaf(local_id: str, raw: str, role: str, span: tuple[int | None, int | None], **extra: Any) -> rec.LexItemRecord:
        return rec.LexItemRecord(local_id, raw, role, span_start=span[0], span_end=span[1],
                                 proposed_repairs=propose_repairs(raw, join_splits=join_splits), **position, **extra)

    cursor = printed.anchor if printed else 0
    if len(shape.members) == 1:
        member = shape.members[0]
        raw, start, end, _ = printed_span(member.raw, cursor, member.span)
        return [leaf(prefix, raw, member.role, (start, end), grammar_raw=_join(shape.grammar_raw, member.grammar_raw),
                     grammar_labels=(*shape.grammar_labels, *member.grammar_labels),
                     senses=senses_for(member, "self"), **top_extra)]
    raw, start, end, _ = printed_span(shape.head_raw, cursor, shape.head_span)
    items = [leaf(prefix, raw, "headword", (start, end), grammar_raw=shape.grammar_raw,
                  grammar_labels=shape.grammar_labels, **top_extra)]
    cursor = (printed.origin + start) if printed and start is not None else cursor
    for index, member in enumerate(shape.members, 1):
        raw, start, end, cursor = printed_span(member.raw, cursor, member.span)
        items.append(leaf(f"{prefix}.m{index}", raw, member.role, (start, end), parent=prefix, member_index=index,
                          grammar_raw=member.grammar_raw, grammar_labels=member.grammar_labels,
                          senses=senses_for(member, "all_members")))
    return items


def _role(form: gp.Form) -> str:
    return {None: "headword", "=": "equivalent_lexeme"}.get(form.separator, "variant")


def _form_member(form: gp.Form, role: str | None = None) -> Member:
    grammar = _join("[ся]" if form.reflexive else None, *form.notes)
    return Member(form.raw, role or _role(form), form.senses, grammar)


def split_gloss(gloss: str) -> list[str]:
    """Numbered senses when the numbering is intact; otherwise the gloss as printed, unsplit."""
    if not gloss:
        return []
    return gp.split_senses(gloss) or [gloss]


# ---------------------------------------------------------------------------
# 1000 words
# ---------------------------------------------------------------------------


def _header_columns(line: str) -> tuple[str, str]:
    stripped = line.strip()
    gap = re.search(r"\s{2,}", stripped)
    if gap:
        return stripped[: gap.start()].strip(), stripped[gap.end() :].strip()
    if gp.has_latin(stripped) and not gp.has_cyrillic(stripped):
        return "", stripped
    return stripped, ""


def _is_header_continuation(line: str) -> bool:
    """A headword/gloss wrap line: lowercase headword fragment and/or gloss tail, no sentence."""
    left, right = _header_columns(line)
    if left and (gp.has_latin(left) or not left[0].islower() or re.search(r"[.?!…«»\"“”—]", left)):
        return False
    if right and (
        gp.has_cyrillic(right)
        or not (is_grammar_note(right) or right[0].islower() or right[0] == "(" or re.match(r"\d+\)", right))
    ):
        return False
    return bool(left or right)


@dataclass
class WordEntry:
    entry_no: int
    shape: EntryShape
    parse_notes: list[str]


def _truncate_ocr_gloss_tail(gloss: str) -> tuple[str, bool]:
    """Cut example text an OCR-wrapped acute pulled onto the gloss line ("side, sideśу ти бо́ці?").

    An accented English word ("café") has no Ukrainian text after it.
    """
    decomposed = unicodedata.normalize("NFD", gloss)
    stray = decomposed.find(gp.ACUTE)
    if stray != -1 and gp.has_cyrillic(decomposed[stray:]):
        return unicodedata.normalize("NFC", decomposed[:stray].rstrip()), True
    return gloss, False


def parse_word_chunk(chunk_id: str, text: str) -> WordEntry:
    """Parse one 1000-words chunk; the head is split as printed, never repaired."""
    entry_no = _entry_no(chunk_id)
    lines = normalize_chunk_lines(text)
    if entry_no is None or not lines:
        raise ParseFailure("unparseable_chunk", chunk_id)
    number = re.match(r"^\s*(\d+)\.\s", lines[0])
    if not number or int(number.group(1)) != entry_no:
        raise ParseFailure("entry_number_mismatch", chunk_id)

    head, gloss, body_start = parse_1000_words_head_and_gloss(lines)
    notes: list[str] = []
    for marker in re.finditer(r"(?:^|(?<=\s))(\d+\))\s*", head):
        if head[: marker.start()].count("(") == head[: marker.start()].count(")"):
            # "задзвони́ти (1), 1) to ring;": the bare sense marker belongs to the gloss
            head = head[: marker.start()] + head[marker.end() :]
            gloss = f"{marker.group(1)} {gloss}"
            notes.append("sense_marker_moved_to_gloss")
            break
    while body_start < len(lines) and _is_header_continuation(lines[body_start]):
        left, right = _header_columns(lines[body_start])
        if left:
            head = f"{head} {left}"
            notes.append("headword_wrap_joined")
        if right and not is_grammar_note(right):
            gloss = f"{gloss} {right}"
        body_start += 1
    header_text = " ".join(lines[:body_start])

    head = re.sub(r"\s+", " ", head).strip()
    gloss = re.sub(r"\s+", " ", gloss).strip()
    gloss, truncated = _truncate_ocr_gloss_tail(gloss)
    if truncated:
        notes.append("gloss_ocr_tail_truncated")
    gloss, aspect = gp.extract_aspect_notes(gloss)
    aspect += [n for n in gp.extract_aspect_notes(header_text)[1] if n not in aspect]
    senses = split_gloss(gloss)
    if gloss and gp.split_senses(gloss) is None:
        raise ParseFailure("sense_numbering", chunk_id)

    parsed = gp.split_headword(head)
    if parsed.empty_forms:
        notes.append("dangling_separator_dropped")
    examples: list[tuple[str, str]] = []
    for _, example in iter_1000_words_examples(lines, start_i=body_start):
        if gp.example_is_complete(example["uk"], example["en"]):
            examples.append((example["uk"], example["en"]))
        else:
            notes.append("incomplete_example_dropped")
    shape = EntryShape(head, [_form_member(form) for form in parsed.forms], senses,
                       grammar_raw=gp.unique_notes(aspect), examples=examples)
    return WordEntry(entry_no, shape, notes)


# ---------------------------------------------------------------------------
# 500 verbs: aspect pair, stems, conjugation table, government, examples
# ---------------------------------------------------------------------------

_CONJUGATION_RE = re.compile(r"^(?:Two-Aspect Verb|Impersonal Verb|Conjugation:)")
TABLE_SECTION_RE = re.compile(r"^\s*([А-ЯІЇЄҐ ]+?)\s*―\s*([A-Z ()]+?)\s*$")
TABLE_SECTIONS = {
    "PRESENT TENSE": "present",
    "PAST TENSE": "past",
    "FUTURE TENSE": "future",
    "CONDITIONAL MOOD": "conditional",
    "SUBJUNCTIVE MOOD": "subjunctive",
    "IMPERATIVE MOOD": "imperative",
    "VERBAL ADJECTIVES (PARTICIPLES)": "participle",
    "VERBAL ADVERBS": "verbal_adverb",
    "IMPERSONAL FORMS": "impersonal",
}
ROW_LABELS = ("він, вона, воно", "він (я, ти)", "вона (я, ти)", "вони (ми, ви)", "безособова",
              "impersonal form", "форма", "ACTIVE", "PASSIVE", "вони", "воно", "вона", "він", "я", "ти", "ми", "ви")
# Label lines that only continue a two-line label ("безособова / форма / impersonal form").
CONTINUATION_LABELS = frozenset({"безособова", "impersonal form"})
_ROW_LABEL_RE = re.compile(r"^\s*(" + "|".join(re.escape(label) for label in ROW_LABELS) + r")(?=\s{2,}|\s*$)")
_TABLE_SUBHEAD_RE = re.compile(r"^(?:ANALYTIC\s+SYNTHETIC|PERSON\s+IMPERFECTIVE ASPECT\s+PERFECTIVE ASPECT)$")
# Inside one cell a single space only follows an auxiliary or precedes a clitic/marker.
_CELL_AUX_RE = re.compile(r"^(?:бу́ду|бу́деш|бу́де|бу́демо|бу́дете|бу́дуть|\(не\)ха́й)$")
_CELL_TAIL_RE = re.compile(r"^(?:би|б|\[б\]|\[с[яь]\]|\[ться\])(?:[,;]|/\S*)?$")
_LATIN = re.compile(r"[A-Za-z]")
_VOWELS = frozenset("аеєиіїоуюяАЕЄИІЇОУЮЯ")
# The perfective column starts this many display columns left of its header, or further right.
PERFECTIVE_HEADER_SLACK = 32
# A cell placed in the perfective column by count but this far left of it is reported as suspect.
SUSPECT_PERFECTIVE_SLACK = 24


def _display_col(line: str, index: int) -> int:
    return sum(1 for ch in line[:index] if not unicodedata.combining(ch))


def _ends_with_displaced_acute(token: str) -> bool:
    """An acute on a consonant at the end of a token: the OCR split the word after it (``об’єд́ ную``)."""
    decomposed = unicodedata.normalize("NFD", token)
    return len(decomposed) >= 2 and decomposed[-1] == gp.ACUTE and decomposed[-2] not in _VOWELS


def table_cells(line: str, start: int) -> list[tuple[int, int, int]]:
    """``(display_col, start, end)`` of each cell right of ``start``.

    Cells are split at two or more spaces, and at one space unless the space
    sits inside a known multi-word cell (``бу́ду X``, ``X би``, ``(не)ха́й X``,
    ``X [ся]``, ``X, Y``, a one-letter OCR fragment, an English note) or an
    OCR word split (a token after a displaced acute). A token that is only a
    combining mark joins both neighbours.
    """
    cells: list[list[int]] = []
    previous = ""
    glue_next = False
    for match in re.finditer(r"\S+", line[start:]):
        a, b, token = start + match.start(), start + match.end(), match.group(0)
        marks_only = all(unicodedata.combining(ch) for ch in token)
        gap = a - cells[-1][1] if cells else 0
        if cells and (glue_next or marks_only or (gap == 1 and (
            _CELL_AUX_RE.match(previous) or _CELL_TAIL_RE.match(token) or previous.endswith((",", "/"))
            or sum(ch.isalpha() for ch in token) <= 1 or _ends_with_displaced_acute(previous)
            or (_LATIN.search(previous) and _LATIN.search(token))
        ))):
            cells[-1][1] = b
        else:
            cells.append([a, b])
        glue_next = marks_only
        previous = token
    return [(_display_col(line, a), a, b) for a, b in cells]


@dataclass
class TableParse:
    cells: list[rec.VerbFormRecord]
    unassigned: int
    suspect: int
    tokens: int
    cell_tokens: int
    end_line: int
    footnotes: list[str] = field(default_factory=list)


def _assign_by_region(row: list[tuple[int, int, int]], *, section: str, perfective_col: int,
                      has_imperfective: bool, has_perfective: bool) -> list[tuple[tuple[str | None, str], int, int]]:
    """Merge a row's cells by column region when their count does not match the columns.

    Cells right of the perfective column merge into the perfective cell; the
    others into the imperfective cell (future: the first is analytic, the rest
    merge into the synthetic cell). Merged cells keep the printed text between them.
    """
    out: list[tuple[tuple[str | None, str], int, int]] = []
    for col, a, b in row:
        if has_perfective and (col >= perfective_col or not has_imperfective):
            key: tuple[str | None, str] = ("perfective", section)
        elif not has_imperfective:
            key = (None, section)
        elif section == "future":
            key = ("imperfective", "future_analytic" if not out else "future_synthetic")
        else:
            key = ("imperfective", section)
        if out and out[-1][0] == key:
            out[-1] = (key, out[-1][1], b)
        else:
            out.append((key, a, b))
    return out


def parse_conjugation_table(lines: list[str], *, has_imperfective: bool, has_perfective: bool) -> TableParse:
    """Every non-empty cell of the conjugation table as one ``VerbFormRecord``.

    Columns: in the future tense the imperfective analytic and synthetic forms
    and the perfective form; elsewhere imperfective and perfective. A row with
    as many cells as columns is assigned in order (a cell put in the
    perfective column far left of it is counted as ``suspect``); any other row
    by column region (``_assign_by_region``). A cell no column takes keeps
    ``aspect=None``. ``tokens``/``cell_tokens`` must match: no table text is lost.
    A footnote row (``*є in the meaning …``) is not a cell: it goes to ``footnotes``.
    """
    header = next((i for i, line in enumerate(lines) if "ДОКОНАНИЙ ВИД" in line and "НЕДОКОНАНИЙ ВИД" in line), None)
    if header is None:
        return TableParse([], 0, 0, 0, 0, 0, [])
    header_line = lines[header]
    perfective_col = _display_col(
        header_line, header_line.index("ДОКОНАНИЙ ВИД", header_line.index("НЕДОКОНАНИЙ ВИД") + 5)
    ) - PERFECTIVE_HEADER_SLACK
    cells: list[dict[str, Any]] = []
    unassigned = suspect = tokens = 0
    footnotes: list[str] = []
    section: str | None = None
    label: str | None = None
    end = len(lines)
    for index in range(header + 1, len(lines)):
        line = lines[index]
        heading = TABLE_SECTION_RE.match(line)
        if heading and heading.group(2).strip() in TABLE_SECTIONS:
            section, label = TABLE_SECTIONS[heading.group(2).strip()], None
            continue
        text = line.strip()
        if section is None or not text or _TABLE_SUBHEAD_RE.match(text):
            continue
        if text.startswith("*"):
            footnotes.append(text)
            continue
        row_label = _ROW_LABEL_RE.match(line)
        if not row_label and len(line) - len(line.lstrip()) < 8:
            end = index
            break
        label_text = row_label.group(1) if row_label else None
        continuation = label_text is None or label_text in CONTINUATION_LABELS
        if label_text is not None and label_text not in CONTINUATION_LABELS:
            label = label_text
        row = table_cells(line, row_label.end() if row_label else 0)
        tokens += sum(len(line[a:b].split()) for _, a, b in row)
        columns: list[tuple[str | None, str]] = []
        if has_imperfective:
            columns += [("imperfective", "future_analytic"), ("imperfective", "future_synthetic")] \
                if section == "future" else [("imperfective", section)]
        if has_perfective:
            columns.append(("perfective", section))
        if len(row) == len(columns):
            placed = [(key, a, b) for key, (_, a, b) in zip(columns, row, strict=True)]
            suspect += sum(1 for (aspect, _), (col, _, _) in zip(columns, row, strict=True)
                           if aspect == "perfective" and col < perfective_col - SUSPECT_PERFECTIVE_SLACK)
        else:
            placed = _assign_by_region(row, section=section, perfective_col=perfective_col,
                                       has_imperfective=has_imperfective, has_perfective=has_perfective)
        for (aspect, tense), a, b in placed:
            unassigned += aspect is None
            value = line[a:b]
            previous = next((c for c in reversed(cells) if c["aspect"] == aspect and c["tense"] == tense), None)
            if continuation and previous is not None and previous["form_raw"].endswith(","):
                previous["form_raw"] = f"{previous['form_raw']} {value}"  # a cell wrapped after a comma
                continue
            cells.append({"aspect": aspect, "tense": tense, "person_number": label, "form_raw": value})
    records = [rec.VerbFormRecord(c["aspect"], c["tense"], c["person_number"], c["form_raw"]) for c in cells]
    cell_tokens = sum(len(r.form_raw.split()) for r in records)
    return TableParse(records, unassigned, suspect, tokens, cell_tokens, end, footnotes)


def _verb_stems(lines: list[str], notes: list[str]) -> list[str] | None:
    stems = _extract_500_verbs_stems(lines)
    if stems is None:  # value wrapped onto the line below an empty label
        for index, line in enumerate(lines[:6]):
            if line.rstrip().endswith(STEMS_LABEL.rstrip()) and index + 1 < len(lines):
                value = re.split(r"\s{2,}", lines[index + 1].strip())[0]
                stems = [part.strip() for part in value.split("|") if part.strip()] or None
                if stems:
                    notes.append("stems_wrap_joined")
                break
    if stems and len(stems) == 1 and re.search(r"\sI\s", stems[0]):
        stems = [part.strip() for part in re.split(r"\sI\s", stems[0])]
        notes.append("ocr_pipe_as_I")
    return stems


def _verb_conjugation(lines: list[str]) -> str | None:
    found = []
    for line in lines[:4]:
        for segment in re.split(r"\s{2,}", line.strip()):
            if _CONJUGATION_RE.match(segment) and segment not in found:
                found.append(segment)
    return "; ".join(found) or None


@dataclass
class VerbEntry:
    entry_no: int
    shape: EntryShape
    parse_notes: list[str]
    table: TableParse


def parse_verb_page(entry_no: int, page: str) -> VerbEntry:
    """Parse one 500-verbs page (``textbook_sections.full_text``) as printed."""
    lines = normalize_500_verbs_lines(page)
    head_raw, gloss_line = parse_500_verbs_head_and_gloss(lines)
    notes: list[str] = []
    if not head_raw:
        raise ParseFailure("missing_headword", f"verb {entry_no}")
    head = re.sub(r"\s+", " ", head_raw).strip()
    if "|" not in head and re.search(r"\sI\s", head):
        legs = [leg.strip() for leg in re.split(r"\sI\s", head, maxsplit=1)]  # an OCR pipe read as "I"
        notes.append("ocr_pipe_as_I")
    else:
        legs = [leg.strip() for leg in head.split("|")]
    if len(legs) != 2:
        raise ParseFailure("verb_pair_shape", f"verb {entry_no}")
    imperfective = gp.split_headword(legs[0])
    perfective = gp.split_headword(legs[1])
    if imperfective.empty_forms or perfective.empty_forms:
        notes.append("dangling_separator_dropped")
    if not imperfective.forms and not perfective.forms:
        raise ParseFailure("no_forms", f"verb {entry_no}")

    gloss = re.split(r"\s{2,}", gloss_line.strip())[0] if gloss_line else ""
    gloss_index = next((i for i, line in enumerate(lines[:4]) if gloss and gloss in line), None)
    while (
        gloss
        and gloss_index is not None
        and gloss_index + 1 < len(lines)
        and (gloss.endswith((",", "(")) or gloss.count("(") > gloss.count(")") or gloss.count("[") > gloss.count("]"))
    ):
        tail = re.split(r"\s{2,}", lines[gloss_index + 1].strip())[0]
        if not tail or not tail[0].islower():
            break
        gloss = f"{gloss} {tail}"
        gloss_index += 1
        notes.append("gloss_wrap_joined")
    gloss = gloss.strip().rstrip(";").strip()

    members = [_form_member(form, "headword" if i == 0 else "variant") for i, form in enumerate(imperfective.forms)]
    members += [_form_member(form, "aspect_partner") for form in perfective.forms]
    if not imperfective.forms:
        members[0] = Member(members[0].raw, "headword", members[0].sense_refs, members[0].grammar_raw)

    verb_forms: list[rec.VerbFormRecord] = []
    stems = _verb_stems(lines, notes)
    legs_present = [aspect for aspect, parsed in (("imperfective", imperfective), ("perfective", perfective))
                    if parsed.forms]
    for index, stem in enumerate(stems or []):
        aspect = legs_present[index] if len(stems or []) == len(legs_present) else None
        tense = {"imperfective": "present_stem", "perfective": "future_stem"}.get(aspect or "", "stem")
        verb_forms.append(rec.VerbFormRecord(aspect, tense, None, stem))
    table = parse_conjugation_table(lines, has_imperfective=bool(imperfective.forms),
                                    has_perfective=bool(perfective.forms))
    verb_forms += table.cells

    labels = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if GOVERNMENT_LABEL_RE.match(stripped) and any(kw in stripped.lower() for kw in GOVERNMENT_CASE_KEYWORDS):
            labels.append(index)
    examples: list[tuple[str, str]] = []
    for _, example in iter_500_verbs_examples(lines, start_i=max(2, table.end_line)):
        if gp.example_is_complete(example["uk"], example["en"]):
            examples.append((example["uk"], example["en"]))
        else:
            notes.append("incomplete_example_dropped")
    shape = EntryShape(head, members, split_gloss(gloss), grammar_raw=_join(_verb_conjugation(lines), *table.footnotes),
                       examples=examples, verb_forms=verb_forms,
                       governments=_extract_500_verbs_government(lines))
    return VerbEntry(entry_no, shape, notes, table)


# ---------------------------------------------------------------------------
# Source adapters (scripts.lexdata.records.SourceAdapter)
# ---------------------------------------------------------------------------


@dataclass
class UnitStats:
    """Parse diagnostics kept by an adapter for the dry-run report (never stored in L1)."""

    parse_notes: Counter[str] = field(default_factory=Counter)
    table_cells: int = 0
    table_cells_unassigned: int = 0
    table_cells_suspect: int = 0
    table_token_mismatch_units: list[str] = field(default_factory=list)
    gloss_like_prose_lines: int = 0


class _Adapter:
    source_id = ""
    parser_id = ""
    stores = ("sources",)
    query = ""

    def __init__(self) -> None:
        self.stats = UnitStats()

    def _selected(self, l0: Mapping[str, Any]) -> list[dict[str, Any]]:
        raise NotImplementedError

    def snapshot(self, l0: Mapping[str, Any]) -> rec.SelectionSnapshot:
        return _snapshot(self.query, self._selected(l0))


class Words1000Adapter(_Adapter):
    source_id = parser_id = WORDS_SOURCE_ID
    query = f"SELECT * FROM textbooks WHERE source_file = '{SOURCE_1000_WORDS}' ORDER BY chunk_id"

    def _selected(self, l0: Mapping[str, Any]) -> list[dict[str, Any]]:
        return _dict_rows(l0["sources"], "SELECT * FROM textbooks WHERE source_file = ? ORDER BY chunk_id",
                          (SOURCE_1000_WORDS,))

    def iter_units(self, l0: Mapping[str, Any]) -> Iterator[rec.UnitInput]:
        for row in self._selected(l0):
            yield rec.UnitInput(self.source_id, _locator("textbooks", "chunk_id", row["chunk_id"]), "chunk",
                                (_l0("textbooks", "chunk_id", row),), payload=row)

    def parse(self, unit: rec.UnitInput) -> rec.ParsedUnit:
        row = unit.payload
        entry = parse_word_chunk(row["chunk_id"], row["text"])
        self.stats.parse_notes.update(entry.parse_notes)
        number = re.match(r"\s*\d+\.\s", row["text"])
        printed = PrintedText(row["text"], number.end() if number else 0)
        return rec.ParsedUnit(unit, "imported", tuple(entry_items("entry", entry.shape, join_splits=True,
                                                                  printed=printed)))


class Verbs500Adapter(_Adapter):
    source_id = parser_id = VERBS_SOURCE_ID
    query = (f"SELECT * FROM textbooks WHERE source_file = '{SOURCE_500_VERBS}' ORDER BY chunk_id; "
             f"SELECT * FROM textbook_sections WHERE source_file = '{SOURCE_500_VERBS}' ORDER BY section_id")

    def _chunks_and_pages(self, l0: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        conn = l0["sources"]
        chunks = _dict_rows(conn, "SELECT * FROM textbooks WHERE source_file = ? ORDER BY chunk_id",
                            (SOURCE_500_VERBS,))
        pages = _dict_rows(conn, "SELECT * FROM textbook_sections WHERE source_file = ? ORDER BY section_id",
                           (SOURCE_500_VERBS,))
        return chunks, pages

    def _selected(self, l0: Mapping[str, Any]) -> list[dict[str, Any]]:
        chunks, pages = self._chunks_and_pages(l0)
        return chunks + pages

    def iter_units(self, l0: Mapping[str, Any]) -> Iterator[rec.UnitInput]:
        chunks, pages = self._chunks_and_pages(l0)
        by_number: dict[str, list[dict[str, Any]]] = {}
        for page in pages:
            by_number.setdefault(str(page["section_number"]), []).append(page)
        for chunk in chunks:
            entry_no = _entry_no(chunk["chunk_id"])
            matched = by_number.get(str(entry_no), []) if entry_no is not None else []
            rows = (_l0("textbooks", "chunk_id", chunk),
                    *(_l0("textbook_sections", "section_id", page) for page in matched))
            yield rec.UnitInput(self.source_id, _locator("textbooks", "chunk_id", chunk["chunk_id"]),
                                "section" if matched else "chunk", rows,
                                payload={"entry_no": entry_no, "pages": matched})

    def parse(self, unit: rec.UnitInput) -> rec.ParsedUnit:
        entry_no, pages = unit.payload["entry_no"], unit.payload["pages"]
        if entry_no is None or len(pages) != 1 or not (pages[0]["full_text"] or "").strip():
            # The chunk text is a truncated stub of the page: never parsed (design r3 §10 (a) point 5).
            return rec.ParsedUnit(unit, "refused:truncated_source")
        entry = parse_verb_page(entry_no, pages[0]["full_text"])
        self.stats.parse_notes.update(entry.parse_notes)
        self.stats.table_cells += len(entry.table.cells)
        self.stats.table_cells_unassigned += entry.table.unassigned
        self.stats.table_cells_suspect += entry.table.suspect
        if entry.table.tokens != entry.table.cell_tokens:
            self.stats.table_token_mismatch_units.append(unit.l0_locator)
        printed = PrintedText(pages[0]["full_text"], 0)
        return rec.ParsedUnit(unit, "imported", tuple(entry_items("entry", entry.shape, join_splits=True,
                                                                  printed=printed)))


def _line_records(lines: list[str], dispositions: list[str]) -> tuple[rec.LineRecord, ...]:
    return tuple(rec.LineRecord(n, line, disposition)
                 for n, (line, disposition) in enumerate(zip(lines, dispositions, strict=True)))


class OhoWorkbookAdapter(_Adapter):
    source_id = parser_id = OHO_SOURCE_ID
    query = (f"SELECT * FROM textbook_sections WHERE source_file = '{oho.SOURCE_FILE}' ORDER BY section_id "
             f"-- kept: pages whose header holds the line '{oho.PAGE_HEADING}'")

    def _selected(self, l0: Mapping[str, Any]) -> list[dict[str, Any]]:
        rows = _dict_rows(l0["sources"], "SELECT * FROM textbook_sections WHERE source_file = ? ORDER BY section_id",
                          (oho.SOURCE_FILE,))
        return [row for row in rows if oho.is_vocabulary_page(row["full_text"] or "")]

    def iter_units(self, l0: Mapping[str, Any]) -> Iterator[rec.UnitInput]:
        for row in self._selected(l0):
            yield rec.UnitInput(self.source_id, _locator("textbook_sections", "section_id", row["section_id"]),
                                "page", (_l0("textbook_sections", "section_id", row),), payload=row)

    def parse(self, unit: rec.UnitInput) -> rec.ParsedUnit:
        text = unit.payload["full_text"]
        lines = text.splitlines()
        page = oho.parse_page(text)
        items: list[rec.LexItemRecord] = []
        for entry in page.entries:
            members = [Member(m.raw, "headword" if i == 0 else "variant", (), m.grammar_raw, m.labels,
                              (m.start, m.end)) for i, m in enumerate(entry.members)]
            shape = EntryShape(entry.head_raw, members, split_gloss(entry.gloss), line_no=entry.line_no,
                               head_span=(0, entry.head_end))
            items += entry_items(f"l{entry.line_no}", shape, join_splits=False)
        return rec.ParsedUnit(unit, "imported", tuple(items), _line_records(lines, page.dispositions))


_GLOSS_LIKE_RE = re.compile(rf"[Ѐ-ӿ]{gp.ACUTE}?[Ѐ-ӿ]*\s[{gp.DASH_CHARS}]\s+[A-Za-z(]")


class UlpAdapter(_Adapter):
    source_id = parser_id = ULP_SOURCE_ID
    query = ("SELECT * FROM textbook_sections WHERE source_file IN "
             f"({', '.join(repr(s) for s in ULP_SOURCES)}) ORDER BY source_file, CAST(section_number AS INTEGER)")

    def _selected(self, l0: Mapping[str, Any]) -> list[dict[str, Any]]:
        placeholders = ", ".join("?" * len(ULP_SOURCES))
        return _dict_rows(
            l0["sources"],
            f"SELECT * FROM textbook_sections WHERE source_file IN ({placeholders}) "
            "ORDER BY source_file, CAST(section_number AS INTEGER), section_id",
            ULP_SOURCES,
        )

    def iter_units(self, l0: Mapping[str, Any]) -> Iterator[rec.UnitInput]:
        for row in self._selected(l0):
            yield rec.UnitInput(self.source_id, _locator("textbook_sections", "section_id", row["section_id"]),
                                "section", (_l0("textbook_sections", "section_id", row),), payload=row)

    def parse(self, unit: rec.UnitInput) -> rec.ParsedUnit:
        text = unit.payload["full_text"] or ""
        lines = text.splitlines()
        lesson = gp.parse_lesson(text)
        dispositions = gp.line_dispositions(lines, lesson)
        items: list[rec.LexItemRecord] = []
        ordinal: Counter[int] = Counter()
        line_starts = [0]
        for line in text.splitlines(keepends=True):
            line_starts.append(line_starts[-1] + len(line))
        # Items that share a margin run start at one column: search each after the previous one.
        run_end: dict[tuple[int, int], int] = {}
        for entry in lesson.entries:
            self.stats.parse_notes.update(entry.parse_notes)
            if entry.errors:
                self.stats.parse_notes.update(entry.errors)
                continue
            ordinal[entry.line_index] += 1
            shape = EntryShape(entry.headword_raw, [_form_member(form) for form in entry.forms],
                               split_gloss(entry.english_gloss), grammar_raw=entry.grammar_note,
                               examples=[(ex["uk"], ex["en"]) for ex in entry.examples],
                               line_no=entry.line_index)
            origin = line_starts[entry.line_index]
            run = (entry.line_index, entry.column)
            printed = PrintedText(text, run_end.get(run, origin + entry.column), origin)
            leaves = entry_items(f"l{entry.line_index}.i{ordinal[entry.line_index]}", shape, join_splits=False,
                                 printed=printed)
            run_end[run] = origin + max(leaf.span_end or 0 for leaf in leaves)
            items += leaves
        self.stats.gloss_like_prose_lines += sum(
            1 for line, disposition in zip(lines, dispositions, strict=True)
            if disposition == gp.PROSE_EXCLUDED and _GLOSS_LIKE_RE.search(line)
        )
        return rec.ParsedUnit(unit, "imported", tuple(items), _line_records(lines, dispositions))


ADAPTERS = {
    WORDS_SOURCE_ID: Words1000Adapter,
    VERBS_SOURCE_ID: Verbs500Adapter,
    OHO_SOURCE_ID: OhoWorkbookAdapter,
    ULP_SOURCE_ID: UlpAdapter,
}


# ---------------------------------------------------------------------------
# Dry run: conservation, refusals, digests
# ---------------------------------------------------------------------------


@dataclass
class SourceRun:
    source_id: str
    snapshot_before: rec.SelectionSnapshot
    snapshot_after: rec.SelectionSnapshot
    units: list[rec.ParsedUnit]
    stats: UnitStats


def run_source(source_id: str, l0: Mapping[str, Any]) -> SourceRun:
    """Parse every unit of one source through the record interface (no writes)."""
    adapter = ADAPTERS[source_id]()
    before = adapter.snapshot(l0)
    sink = rec.CollectingSink()
    rec.drain(adapter, l0, sink)
    after = adapter.snapshot(l0)
    return SourceRun(source_id, before, after, list(sink), adapter.stats)


def derived_rows(unit: rec.ParsedUnit, rights_class: str = "owned_cite_only") -> list[dict[str, Any]]:
    """The L1 leaf columns ``build_store`` would write, derived with the production normalizer."""
    return [derive_leaf(unit.unit, item, normalizer=normalize_span, rights_class=rights_class,
                        importer_version=f"{unit.unit.source_id}/{PARSER_VERSION}")
            for item in unit.ordered_items()]


def unit_digest(unit: rec.ParsedUnit) -> str:
    """Digest of everything a unit contributes to L1 (units, lines, leaves, attributes)."""
    leaves = []
    for item, fields in zip(unit.ordered_items(), derived_rows(unit), strict=True):
        leaves.append({
            "fields": fields,
            "senses": [[s.sense_no, s.gloss_raw, s.applies_to] for s in item.senses],
            "examples": [[e.ex_no, e.uk_raw, e.en_raw] for e in item.examples],
            "verb_forms": [[f.aspect, f.tense, f.person_number, f.form_raw] for f in item.verb_forms],
            "governments": [g.pattern_raw for g in item.governments],
        })
    return sha256_canonical({
        "unit": [unit.unit.source_id, unit.unit.l0_locator, unit.unit.unit_kind, unit.unit.unit_input_fingerprint],
        "disposition": unit.disposition,
        "lines": [[line.line_no, hashlib.sha256(line.raw_line.encode()).hexdigest(), line.disposition]
                  for line in unit.lines],
        "leaves": leaves,
    })


def source_report(run: SourceRun) -> dict[str, Any]:
    unit_dispositions = Counter(unit.disposition for unit in run.units)
    line_dispositions = Counter(line.disposition for unit in run.units for line in unit.lines)
    refusals: Counter[str] = Counter()
    roles: Counter[str] = Counter()
    leaves = accepted = unstressed = 0
    for unit in run.units:
        for item, fields in zip(unit.ordered_items(), derived_rows(unit), strict=True):
            leaves += 1
            roles[item.role] += 1
            if fields["refusal_code"]:
                refusals[fields["refusal_code"]] += 1
            else:
                accepted += 1
                unstressed += gp.ACUTE not in fields["key_stressed"]
    lines_total = sum(len(unit.lines) for unit in run.units)
    expected = EXPECTED_UNITS[run.source_id]
    imported = unit_dispositions.get("imported", 0)
    report: dict[str, Any] = {
        "units": len(run.units),
        "expected_units": expected,
        "unit_dispositions": dict(sorted(unit_dispositions.items())),
        "conservation": {
            "units_equal_expected": len(run.units) == expected,
            "units_equal_imported_plus_refused": imported + sum(
                n for d, n in unit_dispositions.items() if d != "imported") == len(run.units),
            "lines": lines_total,
            "lines_equal_sum_of_dispositions": lines_total == sum(line_dispositions.values()),
            # Line-grain sources: every line of every section's full_text has exactly one disposition.
            "every_section_line_dispositioned": all(
                len(unit.lines) == len((unit.unit.payload.get("full_text") or "").splitlines())
                for unit in run.units if run.source_id in (OHO_SOURCE_ID, ULP_SOURCE_ID)
            ),
        },
        "line_dispositions": dict(sorted(line_dispositions.items())),
        "leaves": leaves,
        "leaves_accepted": accepted,
        "leaves_accepted_without_stress_mark": unstressed,
        "leaves_refused_by_code": dict(sorted(refusals.items())),
        "leaf_roles": dict(sorted(roles.items())),
        "senses": sum(len(i.senses) for u in run.units for i in u.items),
        "examples": sum(len(i.examples) for u in run.units for i in u.items),
        "verb_forms": sum(len(i.verb_forms) for u in run.units for i in u.items),
        "governments": sum(len(i.governments) for u in run.units for i in u.items),
        "proposed_repairs": sum(len(i.proposed_repairs) for u in run.units for i in u.items),
        "parse_notes": dict(sorted(run.stats.parse_notes.items())),
        "snapshot": run.snapshot_before.as_json(),
        "snapshot_unchanged": run.snapshot_before == run.snapshot_after,
        "records_digest": sha256_canonical([unit_digest(unit) for unit in run.units]),
    }
    if run.source_id == VERBS_SOURCE_ID:
        report["conjugation_table"] = {
            "cells": run.stats.table_cells,
            "cells_without_aspect": run.stats.table_cells_unassigned,
            "cells_placed_by_count_far_left_of_perfective_column": run.stats.table_cells_suspect,
            "pages_with_token_mismatch": run.stats.table_token_mismatch_units,
        }
    if run.source_id == ULP_SOURCE_ID:
        per_season: dict[str, Counter[str]] = {}
        for unit in run.units:
            season = unit.unit.payload["source_file"]
            per_season.setdefault(season, Counter()).update(line.disposition for line in unit.lines)
        report["line_dispositions_by_season"] = {k: dict(sorted(v.items())) for k, v in sorted(per_season.items())}
        report["prose_excluded_lines_that_look_like_glosses"] = run.stats.gloss_like_prose_lines
    if run.source_id == OHO_SOURCE_ID:
        report["section_ids"] = [unit.unit.payload["section_id"] for unit in run.units]
    return report


def build_report(runs: Mapping[str, SourceRun]) -> dict[str, Any]:
    sources = {source_id: source_report(run) for source_id, run in runs.items()}
    refusals: Counter[str] = Counter()
    for report in sources.values():
        refusals.update(report["leaves_refused_by_code"])
        refusals.update({d: n for d, n in report["unit_dispositions"].items() if d != "imported"})
        refusals.update({d: n for d, n in report["line_dispositions"].items() if d.startswith("refused:")})
    return {
        "parser_version": PARSER_VERSION,
        "sources": sources,
        "refusals_by_code": dict(sorted(refusals.items())),
        "ok": all(r["conservation"]["units_equal_expected"] and r["conservation"]["units_equal_imported_plus_refused"]
                  and r["conservation"]["lines_equal_sum_of_dispositions"]
                  and r["conservation"]["every_section_line_dispositioned"] and r["snapshot_unchanged"]
                  for r in sources.values()),
        "digest": sha256_canonical({s: r["records_digest"] for s, r in sorted(sources.items())}),
    }


# ---------------------------------------------------------------------------
# §8 held-out samples (evaluator only)
# ---------------------------------------------------------------------------


def _order_key(seed: str, unit_key: str) -> str:
    return hashlib.sha256(f"{seed}\x1f{unit_key}".encode()).hexdigest()


def _leaf_sheet(unit: rec.ParsedUnit, line_no: int | None) -> list[dict[str, Any]]:
    rows = []
    for item, fields in zip(unit.ordered_items(), derived_rows(unit), strict=True):
        if line_no is not None and item.line_no != line_no:
            continue
        rows.append({
            "local_id": item.local_id, "role": item.role, "raw_span": item.raw_span,
            "key_stressed": fields["key_stressed"], "refusal_code": fields["refusal_code"],
            "grammar_raw": item.grammar_raw, "senses": [s.gloss_raw for s in item.senses],
            "examples": [[e.uk_raw, e.en_raw] for e in item.examples],
            "proposed_repairs": json.loads(fields["proposed_repairs"]),
            "verb_forms": len(item.verb_forms),
        })
    return rows


def draw_samples(runs: Mapping[str, SourceRun], seed: str) -> dict[str, list[dict[str, Any]]]:
    """§8 samples, ordered by ``sha256(seed || unit_key)``; drawn from source units and lines.

    (a) 30 Ohoiko entries (1000-words and 500-verbs units); (a) 30 Oho! page
    lines, any disposition; (b) 50 ULP lines, non-blank, stratified by season
    and disposition (one per stratum first, then by hash order).
    """
    entries = [(unit, None) for source in (WORDS_SOURCE_ID, VERBS_SOURCE_ID) for unit in runs[source].units]
    entries.sort(key=lambda pair: _order_key(seed, pair[0].unit.l0_locator))
    oho_lines = [(unit, line) for unit in runs[OHO_SOURCE_ID].units for line in unit.lines]
    oho_lines.sort(key=lambda pair: _order_key(seed, f"{pair[0].unit.l0_locator}#{pair[1].line_no}"))
    ulp_lines = [(unit, line) for unit in runs[ULP_SOURCE_ID].units for line in unit.lines if line.raw_line.strip()]
    ulp_lines.sort(key=lambda pair: _order_key(seed, f"{pair[0].unit.l0_locator}#{pair[1].line_no}"))
    strata: dict[tuple[str, str], list[Any]] = {}
    for unit, line in ulp_lines:
        strata.setdefault((unit.unit.payload["source_file"], line.disposition), []).append((unit, line))
    chosen = [members[0] for _, members in sorted(strata.items())][: SAMPLE_SIZES["ulp_lines"]]
    picked = {id(pair[1]) for pair in chosen}
    chosen += [pair for pair in ulp_lines if id(pair[1]) not in picked][: SAMPLE_SIZES["ulp_lines"] - len(chosen)]

    def line_sheet(pair: tuple[rec.ParsedUnit, rec.LineRecord]) -> dict[str, Any]:
        unit, line = pair
        return {"unit": unit.unit.l0_locator, "line_no": line.line_no, "raw_line": line.raw_line,
                "disposition": line.disposition, "leaves": _leaf_sheet(unit, line.line_no)}

    return {
        "ohoiko_entries": [
            {"unit": unit.unit.l0_locator, "disposition": unit.disposition, "leaves": _leaf_sheet(unit, None)}
            for unit, _ in entries[: SAMPLE_SIZES["ohoiko_entries"]]
        ],
        "oho_lines": [line_sheet(pair) for pair in oho_lines[: SAMPLE_SIZES["oho_lines"]]],
        "ulp_lines": [line_sheet(pair) for pair in chosen],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


SQLITE_SIDECARS = ("", "-wal", "-shm", "-journal")


def _protected_paths(db: Path | None, seed: Path | None) -> list[Path]:
    """Every file an output must never replace: the inputs and each registered store.

    The registered stores are ``topology.STORE_FILES`` at the primary checkout
    and at their environment overrides, whether or not the file exists yet.
    Every store is protected as given and with its symlinks resolved, and each
    form with its SQLite sidecars (SQLite names ``-wal``/``-shm``/``-journal``
    after the resolved file, so a symlinked store has sidecars at both names).
    Resolution opens nothing.
    """
    stores: list[Path] = [db] if db is not None else []
    primary = main_checkout_root(topology.default_repository_root())
    for store, (filename, override) in topology.STORE_FILES.items():
        stores.append(primary / "data" / filename)
        if os.environ.get(override, "").strip():
            stores.append(Path(os.environ[override]))
        resolved = resolve_store(store)
        if isinstance(resolved, StoreBinding):
            stores.append(resolved.path)
    stores += [store.resolve() for store in stores]
    protected = [Path(f"{store}{suffix}") for store in stores for suffix in SQLITE_SIDECARS]
    return protected + ([seed] if seed is not None else [])


def same_file(a: Path, b: Path) -> bool:
    """True when two paths name one file: equal after resolving symlinks, ``.`` and ``..``, or hard links."""
    if os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b)):
        return True
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def output_collision(outputs: Mapping[str, Path | None], protected: Iterable[Path]) -> str | None:
    """The first output option that names a protected file or another output, else ``None``."""
    given = [(name, path) for name, path in outputs.items() if path is not None]
    guarded = list(protected)
    for index, (name, path) in enumerate(given):
        if any(same_file(path, other) for other in guarded):
            return name
        if any(same_file(path, other) for _, other in given[index + 1:]):
            return name
    return None


def _resolve_sources(explicit: Path | None) -> Path:
    binding = StoreBinding("sources", explicit) if explicit is not None else None
    resolved = resolve_store("sources", binding=binding)
    if isinstance(resolved, StoreRefusal):
        raise SystemExit(f"error: sources store unavailable ({resolved.reason})")
    return resolved.path


def run_all(conn: SQLiteConnection, sources: Iterable[str] = SOURCE_IDS) -> dict[str, SourceRun]:
    return {source_id: run_source(source_id, {"sources": conn}) for source_id in sources}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run the read-only lexdata L1 parsers for Anna Ohoiko's dictionary parts: the 1000-words and "
            "500-verbs books, the Oho! A1 workbook Словничок and the ULP lesson-note vocabulary zones.\n"
            "Use it to check conservation, refusals and record digests before a lexdata build. It never writes "
            "a database; the lexdata store is written only by `python -m scripts.lexdata build`."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/lexicon/import_ohoiko_vocab.py
  .venv/bin/python scripts/lexicon/import_ohoiko_vocab.py --source ohoiko_500_verbs --report /abs/report.json
  .venv/bin/python scripts/lexicon/import_ohoiko_vocab.py --sample-seed-file /abs/seed --sample-out /abs/sheets.json

Outputs:
  stdout: JSON report: per source the unit and line conservation, line dispositions, leaves accepted (and
  how many of them carry no stress mark: the source printed none) and refused by code, roles, senses/examples/verb forms, parse notes, the selection snapshot (taken before and
  after the run; it must not change) and a records digest; an unchanged input gives identical digests.
  --sample-seed-file: writes the design §8 held-out sample sheets (30 Ohoiko entries, 30 Oho! lines,
  50 ULP lines) to --sample-out. For the evaluator only: the implementer never draws or reads them.
  Sample sheets quote private source text: keep them out of the repository (reports hold counts and digests).

Exit codes:
  0  every source conserved (units, lines) and its selection snapshot unchanged
  1  conservation failed, a snapshot changed, or a unit contradicts its source grammar (parse failure)
  2  store unavailable or invalid arguments, including an output (--report, --sample-out) that names
     an input, a registered store (sources, vesum, lexdata, with SQLite sidecars) or the other output
     through any alias (symlink, "..", hard link); refused before anything is opened

Related: OO-38; design r3 §10 (a)/(b); scripts/lexdata/records.py (record interface);
  scripts/lexdata/transforms.py (parser registration); docs/corpus-inventory.md.""",
    )
    parser.add_argument(
        "--db", type=Path, default=None,
        help="Absolute path of sources.db, opened read-only. Default: resolve_store('sources') "
        "(LU_SOURCES_DB or the primary checkout's data/sources.db).",
    )
    parser.add_argument("--source", action="append", choices=SOURCE_IDS,
                        help="Parse only this source (repeatable). Default: all four.")
    parser.add_argument("--report", type=Path, default=None,
                        help="Also write the JSON report to this absolute path (outside the repository).")
    parser.add_argument("--sample-seed-file", type=Path, default=None,
                        help="Evaluator only: file holding the private sample seed (needs all four sources).")
    parser.add_argument("--sample-out", type=Path, default=None,
                        help="Absolute path for the sample sheets; required with --sample-seed-file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    for name in ("db", "report", "sample_seed_file", "sample_out"):
        value = getattr(args, name)
        if value is not None and not value.is_absolute():
            print(f"error: --{name.replace('_', '-')} must be an absolute path", file=sys.stderr)
            return 2
    if (args.sample_seed_file is None) != (args.sample_out is None):
        print("error: --sample-seed-file and --sample-out go together", file=sys.stderr)
        return 2
    sources = tuple(args.source or SOURCE_IDS)
    if args.sample_seed_file is not None and set(sources) != set(SOURCE_IDS):
        print("error: samples need all four sources", file=sys.stderr)
        return 2
    # Before anything is opened: an output must not replace an input, a store or another output.
    collision = output_collision({"report": args.report, "sample-out": args.sample_out},
                                 _protected_paths(args.db, args.sample_seed_file))
    if collision is not None:
        print(f"error: --{collision} names an input, a registered store or another output; nothing was read "
              "or written", file=sys.stderr)
        return 2
    try:
        db_path = _resolve_sources(args.db)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2

    conn = open_readonly(db_path)
    try:
        try:
            runs = run_all(conn, sources)
        except (ParseFailure, oho.OhoLineError) as exc:
            print(canonical_json({"ok": False, "parse_failure": str(exc)}))
            return 1
        report = build_report(runs)
        if args.sample_seed_file is not None:
            seed = args.sample_seed_file.read_text(encoding="utf-8").strip()
            args.sample_out.write_text(json.dumps(draw_samples(runs, seed), ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
            report["samples_written"] = True
    finally:
        conn.close()
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report is not None:
        args.report.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
