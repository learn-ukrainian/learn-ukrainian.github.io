"""Parse the Oho! A1 workbook ``Словничок`` pages (design r3 §2, §4, §10 (a) point 6).

Pure functions, no I/O. Used by ``scripts/lexicon/import_ohoiko_vocab.py``.

The 17 vocabulary pages of ``owned-oho-a1-workbook`` hold one dictionary line
per entry (list grammar ``oho_line``)::

    head(, label)*(, head(, label)*)*, gloss
    австралі́єць, ч., австралі́йка, ж., Australian
    жи́ти (я живу́, ми живе́мо́), недок., to live

Labels come from the closed abbreviation key printed on the first page
(``ч.``, ``ж.``, ``с.``, ``недок.``, ``док.``, ``прикм.``, ``присл.``). Each head
is a member with its own labels; a trailing parenthetical on a head is kept
verbatim with that member's grammar and is never split. The gloss starts at
the first top-level segment whose letters are mostly Latin; a following line
with no Cyrillic letter (``(he has dinner)``) continues that gloss.

Every line gets exactly one disposition: ``entry``, ``lesson_heading``,
``abbreviation_key``, ``continuation`` or ``page_furniture``. The ``Урок N``
and ``Розділ N`` headings are recorded where they are printed. In the stored
page text they follow the entries out of order (for example ``Урок 08``
before ``Урок 07``, all at the end of the page), so the text does not bind an
entry to one lesson; the page is the finest lesson context the text supports.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from scripts.lexicon.ulp_glossary_parse import CYRILLIC_RE, LATIN_RE, has_cyrillic

SOURCE_FILE = "owned-oho-a1-workbook"
PAGE_HEADING = "Словничок"
LABELS = frozenset({"ч.", "ж.", "с.", "недок.", "док.", "прикм.", "присл."})
LESSON_HEADING_RE = re.compile(r"^(?:Урок|Розділ)\s+\d+$")
ABBREVIATION_KEY_FIRST = "Скорочення"
ABBREVIATION_KEY_LAST = "Abbreviations"
HEADING_SEARCH_LINES = 6

ENTRY = "entry"
LESSON_HEADING = "lesson_heading"
ABBREVIATION_KEY = "abbreviation_key"
CONTINUATION = "continuation"
PAGE_FURNITURE = "page_furniture"
_TRAILING_PAREN_RE = re.compile(r"\s*\(([^()]*)\)\s*$")


class OhoLineError(ValueError):
    """A Cyrillic line on a vocabulary page fits no disposition of the line grammar."""


@dataclass(frozen=True)
class OhoMember:
    """One head of an entry line. ``raw`` is ``line[start:end]`` exactly."""

    raw: str
    start: int
    end: int
    labels: tuple[str, ...] = ()
    grammar_raw: str | None = None  # verbatim parenthetical and labels after the head


@dataclass
class OhoEntry:
    line_no: int
    head_raw: str  # ``line[:head_end]``: every member with its labels
    head_end: int
    members: list[OhoMember]
    gloss: str
    continuation_lines: list[int] = field(default_factory=list)


@dataclass
class OhoPage:
    dispositions: list[str]
    entries: list[OhoEntry]
    lesson_headings: list[tuple[int, str]]


def is_vocabulary_page(text: str) -> bool:
    """True for a ``Словничок`` page: the heading line sits in the page header."""
    return any(line.strip() == PAGE_HEADING for line in text.splitlines()[:HEADING_SEARCH_LINES])


def _segments(line: str) -> list[tuple[int, int]]:
    """``(start, end)`` of each top-level ``", "``-separated segment (never inside parentheses)."""
    spans: list[tuple[int, int]] = []
    depth = 0
    start = 0
    i = 0
    while i < len(line):
        ch = line[i]
        depth += ch == "("
        depth -= ch == ")"
        if depth == 0 and ch == "," and (i + 1 == len(line) or line[i + 1] == " "):
            spans.append((start, i))
            start = i + 2
            i += 2
            continue
        i += 1
    if start < len(line):
        spans.append((start, len(line)))
    return spans


def _is_ukrainian(text: str) -> bool:
    """Mostly Cyrillic letters: a head (``Cпасибі`` with a Latin ``C`` is still a head)."""
    cyrillic = len(CYRILLIC_RE.findall(text))
    return cyrillic > 0 and cyrillic > len(LATIN_RE.findall(text))


def _strip_span(line: str, start: int, end: int) -> tuple[int, int]:
    while start < end and line[start].isspace():
        start += 1
    while end > start and line[end - 1].isspace():
        end -= 1
    return start, end


def parse_entry_line(line: str, line_no: int) -> OhoEntry | None:
    """Parse one dictionary line; None when it has no head before its gloss."""
    members: list[OhoMember] = []
    gloss_start: int | None = None
    head_end = 0
    for seg_start, seg_end in _segments(line):
        start, end = _strip_span(line, seg_start, seg_end)
        if start == end:
            continue
        text = line[start:end]
        if text in LABELS and members:
            member = members[-1]
            grammar_start = member.end
            members[-1] = OhoMember(member.raw, member.start, member.end, (*member.labels, text),
                                    line[grammar_start:end].lstrip(" ,"))
            head_end = end
            continue
        if not _is_ukrainian(text):
            gloss_start = start
            break
        raw_end = end
        grammar = None
        paren = _TRAILING_PAREN_RE.search(text)
        if paren and text[: paren.start()].strip():
            raw_end = start + paren.start()
            grammar = text[paren.start():].strip()
        members.append(OhoMember(line[start:raw_end], start, raw_end, (), grammar))
        head_end = end
    if not members:
        return None
    gloss = line[gloss_start:].strip() if gloss_start is not None else ""
    return OhoEntry(line_no, line[:head_end], head_end, members, gloss)


def parse_page(text: str) -> OhoPage:
    """Disposition every line of one ``Словничок`` page and parse its entries."""
    lines = text.splitlines()
    heading = next((i for i, line in enumerate(lines[:HEADING_SEARCH_LINES]) if line.strip() == PAGE_HEADING), None)
    if heading is None:
        raise OhoLineError("not a Словничок page")
    stripped = [line.strip() for line in lines]
    key_range: range = range(0)
    if ABBREVIATION_KEY_FIRST in stripped and ABBREVIATION_KEY_LAST in stripped:
        key_range = range(heading + 2, stripped.index(ABBREVIATION_KEY_LAST) + 1)
    dispositions: list[str] = []
    entries: list[OhoEntry] = []
    lesson_headings: list[tuple[int, str]] = []
    for line_no, line in enumerate(lines):
        text = stripped[line_no]
        if line_no <= heading + 1 or not text:
            dispositions.append(PAGE_FURNITURE)
        elif line_no in key_range:
            dispositions.append(ABBREVIATION_KEY)
        elif LESSON_HEADING_RE.match(text):
            dispositions.append(LESSON_HEADING)
            lesson_headings.append((line_no, text))
        elif not has_cyrillic(text):
            if not entries:
                raise OhoLineError(f"line {line_no}: text with no Cyrillic before any entry")
            entries[-1].continuation_lines.append(line_no)
            entries[-1].gloss = f"{entries[-1].gloss} {text}".strip()
            dispositions.append(CONTINUATION)
        else:
            entry = parse_entry_line(line, line_no)
            if entry is None:
                raise OhoLineError(f"line {line_no}: no head before the gloss")
            entries.append(entry)
            dispositions.append(ENTRY)
    return OhoPage(dispositions, entries, lesson_headings)
