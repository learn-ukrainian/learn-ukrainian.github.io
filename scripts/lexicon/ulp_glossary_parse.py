"""Parse Anna Ohoiko glossary text: headword forms and ULP lesson-note dictionary parts.

Pure functions, no I/O. Used by ``scripts/lexicon/import_ohoiko_vocab.py``,
which turns their output into typed lexdata L1 records (design r3 §4, §10).

Two layers:

- Headword primitives shared by the 1000-words, 500-verbs, Oho! and ULP
  parsers: splitting a printed headword into its ``=`` groups and ``,`` members
  (``split_headword``, top level only, never inside parentheses), aspect-note
  extraction, numbered-sense splitting, the stress diagnostic ``stress_errors``
  and the OCR repair *proposers* ``repair_ukrainian`` / ``join_split_stress``.
  The proposers never change a stored span: callers attach their output to
  ``proposed_repairs`` and keep the original text.
- ULP lesson notes (``ulp-{1..6}-00-lesson-notes``), one lesson section at a
  time. ``kind='slovnychok'`` covers the vocabulary zones (Seasons 1-3 "Key
  Vocabulary N-NN" / "Bonus Vocabulary", Season 6 "Словничок" and "Словничок
  (з прикладами)"); ``kind='margin_gloss'`` covers right-margin glosses such as
  ``тео́рія — theory``. ``line_dispositions`` gives every line of the section
  exactly one disposition, so prose and exercises are accounted for, never
  emitted.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from scripts.lexicon.ohoiko_quality_enrichment import split_uk_en_line

ACUTE = "́"
VOWELS = frozenset("аеєиіїоуюяАЕЄИІЇОУЮЯ")
CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")
LATIN_RE = re.compile(r"[A-Za-z]")
CYRILLIC_UPPER_RE = re.compile(r"[А-ЯҐЄІЇ]")

# OCR substitutes visually identical letters across scripts.
_LATIN_TO_CYRILLIC = str.maketrans("aceiopxyACEHIKMOPTXB", "асеіорхуАСЕНІКМОРТХВ")
# NFC composes к/г + acute into ќ/ѓ, and OCR emits Latin accented vowels for
# stressed Cyrillic ones; spell both as base letter + combining acute.
_ACUTE_SPELLINGS = {
    "ќ": "к" + ACUTE,
    "Ќ": "К" + ACUTE,
    "ѓ": "г" + ACUTE,
    "Ѓ": "Г" + ACUTE,
    "á": "а" + ACUTE,
    "é": "е" + ACUTE,
    "í": "і" + ACUTE,
    "ó": "о" + ACUTE,
    "ý": "у" + ACUTE,
    "Á": "А" + ACUTE,
    "É": "Е" + ACUTE,
    "Í": "І" + ACUTE,
    "Ó": "О" + ACUTE,
}
ASPECT_NOTE_RE = re.compile(r"\(\s*((?:imperfective|perfective)[^)]*)\)", re.IGNORECASE)
DASH_CHARS = "—―–"
_DASH_SPLIT_RE = re.compile(rf"\s[{DASH_CHARS}](?:\s|$)")
_SENSE_MARK_RE = re.compile(r"(?:^|(?<=[\s;,]))(\d+)\)\s*")
_TERMINAL_RE = re.compile(r"[.?!…][\"'”»)\]]*$")


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def has_cyrillic(text: str) -> bool:
    return bool(CYRILLIC_RE.search(text))


def has_latin(text: str) -> bool:
    return bool(LATIN_RE.search(text))


def _acute_spelling(text: str) -> str:
    text = nfc(text)
    return "".join(_ACUTE_SPELLINGS.get(ch, ch) for ch in text)


def repair_ukrainian(text: str) -> tuple[str, list[str]]:
    """Propose an OCR repair of a stressed Ukrainian form; return (text, repair codes).

    A proposal only (design r3 §10 (a) point 3): callers store it in
    ``proposed_repairs`` and never replace the original span. Covers Latin
    homoglyphs inside Cyrillic words, precomposed accented letters, doubled
    acutes, an acute that opens a word, and an acute the OCR shifted onto the
    consonant after its vowel.
    """
    repairs: list[str] = []
    spelled = _acute_spelling(text)
    if spelled != nfc(text):
        repairs.append("precomposed_acute_respelled")
    text = spelled

    def fix_word(match: re.Match[str]) -> str:
        word = match.group(0)
        if has_cyrillic(word) and has_latin(word):
            fixed = word.translate(_LATIN_TO_CYRILLIC)
            if fixed != word:
                repairs.append("latin_homoglyph")
                return fixed
        return word

    text = re.sub(r"[\ẃ’'ʼ-]+", fix_word, text)
    if ACUTE + ACUTE in text:
        repairs.append("doubled_stress")
        text = re.sub(ACUTE + "+", ACUTE, text)
    if re.search(r"(^|[\s(=,/])" + ACUTE, text):
        repairs.append("stray_stress_dropped")
        text = re.sub(r"(^|[\s(=,/])" + ACUTE + "+", r"\1", text)
    chars = list(text)
    for i, ch in enumerate(chars):
        if ch != ACUTE or i == 0 or chars[i - 1] in VOWELS:
            continue
        j = i - 1
        while j >= 0 and chars[j] not in VOWELS and chars[j].isalpha():
            j -= 1
        if j >= 0 and chars[j] in VOWELS and (j + 1 >= len(chars) or chars[j + 1] != ACUTE):
            chars[i] = ""
            chars[j] = chars[j] + ACUTE
            repairs.append("stress_moved_to_vowel")
    return "".join(chars), repairs


def join_split_stress(text: str) -> tuple[str, list[str]]:
    """Propose joining OCR word splits (``бу́ ти`` -> ``бу́ти``, ``боя́ тися`` -> ``боя́тися``).

    A proposal only, like ``repair_ukrainian``. For book headword lists,
    never ULP phrases: there a stressed
    monosyllable followed by an unstressed lowercase fragment, or a detached
    ``-ти`` / ``-тися`` / ``-ся`` ending after a stressed word, is an OCR split.
    """
    repairs: list[str] = []
    tokens = text.split(" ")
    out: list[str] = []
    for token in tokens:
        fragment = re.fullmatch(r"[а-яґєії’]+[,=]?", token) and ACUTE not in token
        ending = re.fullmatch(r"(?:ти|тис[яь]|с[яь])[,=]?", token) and ACUTE in out[-1] if out else False
        if out and fragment and (_is_stressed_monosyllable(out[-1]) or ending) and out[-1][-1] not in ",=)":
            out[-1] = out[-1] + token
            repairs.append("ocr_split_joined")
            continue
        out.append(token)
    return " ".join(out), repairs


def _is_stressed_monosyllable(token: str) -> bool:
    return token.count(ACUTE) == 1 and sum(ch in VOWELS for ch in token) == 1 and token[-1] not in ",=)"


def stress_errors(form: str, *, allow_digits: bool = False) -> list[str]:
    """Diagnose a printed form: unstressed polysyllables, marks off a vowel, Latin letters, digits.

    A diagnostic only, never a refusal: the sources print some entries
    without stress (``Кримські татари``), and an unstressed span is accepted
    with stress absent. Whether printed marks are valid is decided by the
    lexdata normalizer (``scripts/lexdata/stress.py``), which refuses only a
    mark that does not follow one vowel (``stress_invalid``).
    """
    errors: list[str] = []
    if has_latin(form):
        errors.append("latin_in_ukrainian")
    if not allow_digits and re.search(r"\d", form):
        errors.append("digit_in_headword")
    for word in re.findall(r"[^\s.,!?;:«»\"“”()…/=–—―]+", form):
        letters = word.strip("’'ʼ-")
        if not letters or (letters.replace("-", "").isupper() and len(letters) > 1):
            continue  # acronyms (СРСР) carry no stress
        # Hyphenated compounds (коли-не́будь, все́-таки) are stressed on one part only.
        polysyllabic = any(sum(ch in VOWELS for ch in part) >= 2 for part in letters.split("-"))
        if polysyllabic and ACUTE not in letters:
            errors.append(f"unstressed_polysyllable:{word}")
        if re.search(r"[^аеєиіїоуюяАЕЄИІЇОУЮЯ]" + ACUTE, letters):
            errors.append(f"stress_not_on_vowel:{word}")
    return errors


@dataclass(frozen=True)
class Form:
    """One member of a printed headword, as printed (never repaired).

    ``raw`` is the member text without its sense references, Latin notes and
    ``[ся]`` marker; ``separator`` is what joined it to the previous member
    (``None`` for the first, ``"="`` or ``","``).
    """

    raw: str
    group: int
    separator: str | None = None
    senses: tuple[int, ...] = ()
    reflexive: bool = False
    notes: tuple[str, ...] = ()


@dataclass
class HeadwordParse:
    forms: list[Form] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    empty_forms: int = 0  # dangling "," / "=" separators


def _split_top_level(text: str, separators: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in text:
        depth += ch == "("
        depth -= ch == ")"
        if depth == 0 and ch in separators:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return parts


def split_headword(head: str, *, split_commas: bool = True) -> HeadwordParse:
    """Split a printed headword into members: ``=`` separates groups; ``,``, ``;`` and ``/`` members.

    Structure only, on the text as printed (list grammar ``ohoiko_eq``,
    top level only, never inside parentheses). Trailing ``(1)`` / ``(1, 2)``
    become sense references; other trailing parentheticals that are not
    purely Ukrainian (``(verb)``, ``(колі́нце — diminutive)``, ``(1283-1547)``)
    become the member's notes; ``(= X)`` becomes an ``=`` member; a purely
    Ukrainian parenthetical (``родови́й (відмі́нок)``) stays in the member.
    Stress is not judged here: the lexdata normalizer decides on the printed marks.
    """
    result = HeadwordParse()
    head = re.sub(r"\(\s*=\s*([^()]+)\)", r"= \1", head)
    separators = ",;/" if split_commas else "/"
    for group_index, group in enumerate(_split_top_level(head, "=")):
        first_in_group = True
        for raw in _split_top_level(group, separators):
            text = re.sub(r"^\s*[–—-]\s+", "", raw).strip()
            if not text:
                result.empty_forms += 1
                continue
            senses: tuple[int, ...] = ()
            notes: list[str] = []
            while text:
                match = re.search(r"\s*\(([^()]*)\)\s*$", text)
                if not match:
                    break
                inner = match.group(1).strip()
                # Sense references are one- or two-digit numbers; "(1943)" is a note.
                if re.fullmatch(r"\d{1,2}(?:\s*,\s*\d{1,2})*", inner) and text[: match.start()].strip():
                    senses = tuple(int(n) for n in re.findall(r"\d+", inner))
                elif has_cyrillic(inner) and not has_latin(inner):
                    break  # optional Ukrainian part, e.g. "родови́й (відмі́нок)": stays in the member
                else:
                    # A note; a member that is only a note keeps an empty span (refused ``empty_span``).
                    notes.insert(0, inner)
                text = text[: match.start()].strip()
            reflexive = bool(re.search(r"\[с[яь]\]", text))
            text = re.sub(r"\s*\[с[яь]\]", "", text).strip()
            if re.fullmatch(r"[―—–-]", text):
                continue  # "no aspect partner" placeholder in 500-verbs
            if not result.forms:
                separator = None
            elif first_in_group and group_index > 0:
                separator = "="
            else:
                separator = ","
            first_in_group = False
            result.forms.append(Form(text, group_index, separator, senses, reflexive, tuple(notes)))
    if not result.forms:
        result.errors.append("no_forms")
    return result


def extract_aspect_notes(text: str) -> tuple[str, list[str]]:
    """Remove ``(imperfective, perfective)``-style notes; return (text, normalized notes)."""
    notes = [re.sub(r"\s*,\s*", ", ", m.group(1).strip()) for m in ASPECT_NOTE_RE.finditer(text)]
    cleaned = re.sub(r"\s+", " ", ASPECT_NOTE_RE.sub(" ", text)).strip()
    return cleaned, notes


def split_senses(gloss: str) -> list[str] | None:
    """Split ``1) more; 2) anymore`` into senses; None when the numbering is broken."""
    marks = list(_SENSE_MARK_RE.finditer(gloss))
    if not marks:
        sense = gloss.strip().rstrip(";,").strip()
        return [sense] if sense else None
    if gloss[: marks[0].start()].strip() or [int(m.group(1)) for m in marks] != list(range(1, len(marks) + 1)):
        return None
    senses: list[str] = []
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(gloss)
        sense = gloss[mark.end() : end].strip().rstrip(";,").strip()
        if not sense:
            return None
        senses.append(sense)
    return senses


def example_is_complete(uk: str, en: str) -> bool:
    """Both sides end a sentence, or neither does (catches truncated OCR examples)."""
    return bool(_TERMINAL_RE.search(uk.strip())) == bool(_TERMINAL_RE.search(en.strip()))


def unique_notes(notes: list[str]) -> str | None:
    ordered: list[str] = []
    for note in notes:
        if note and note not in ordered:
            ordered.append(note)
    return "; ".join(ordered) or None


# ---------------------------------------------------------------------------
# ULP lesson notes
# ---------------------------------------------------------------------------

KIND_SLOVNYCHOK = "slovnychok"
KIND_MARGIN = "margin_gloss"
VOCAB_HEADING_RE = re.compile(r"^\s*(Key Vocabulary \d+-\d+|Bonus Vocabulary|Словничок \(з прикладами\)|Словничок)\s*$")
MARGIN_MIN_COL = 50
TABLE_GAP = 7
MAX_MARGIN_HEAD_WORDS = 10
_GAP_RE = re.compile(r"\s{2,}")


@dataclass
class GlossaryEntry:
    """One parsed dictionary item, text as printed.

    ``line_indices`` are every section line the item consumed; ``column`` is
    where its text starts on line ``line_index``. ``errors`` non-empty
    (``margin_head_too_long``, ``exercise_item``, ``margin_fragment``) means the
    item is not dictionary content: its lines are prose, and no record is
    emitted for it.
    """

    kind: str
    section_heading: str | None
    line_index: int
    line_indices: list[int]
    anchor: str
    column: int = 0
    headword_raw: str = ""
    forms: list[Form] = field(default_factory=list)
    english_gloss: str = ""
    grammar_note: str | None = None
    examples: list[dict[str, str]] = field(default_factory=list)
    parse_notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class LessonParse:
    entries: list[GlossaryEntry]
    sections: list[tuple[str, int, int]]
    non_gloss_margin_segments: int
    non_gloss_margin_lines: list[int] = field(default_factory=list)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _split_columns(line: str, right_col: int) -> tuple[int, str, str]:
    """Return (indent, left, right): right is the text starting near ``right_col``."""
    indent = _indent(line)
    if indent >= right_col - 8:
        return indent, "", line.strip()
    for gap in _GAP_RE.finditer(line, indent):
        if gap.end() >= right_col - 8:
            return indent, line[: gap.start()].strip(), line[gap.end() :].strip()
    return indent, line.strip(), ""


def _section_geometry(lines: list[str], start: int, end: int) -> tuple[int, int] | None:
    for line in lines[start:end]:
        if not line.strip() or not has_cyrillic(line):
            continue
        indent = _indent(line)
        gap = _GAP_RE.search(line, indent)
        if gap and gap.end() < len(line.rstrip()):
            return indent, gap.end()
    return None


def _is_section_end(line: str, previous: str, geometry: tuple[int, int] | None) -> bool:
    """True when ``line`` closes a vocabulary zone; layout only, never stress marks.

    Entries print unstressed as well as stressed (``Кримські татари``), so a
    missing acute says nothing about prose. A zone ends at the next zone
    heading, at an English heading left of the gloss column (``Bonus Exercises
    1-20``), at a single-column capitalised line indented past the entry column
    after a blank line (a centred heading such as ``Українська поезія. …``), or
    at a centred heading or numbered line at column 20 or more.
    """
    text = line.strip()
    if not text or VOCAB_HEADING_RE.match(line):
        return bool(text)
    indent = _indent(line)
    columns = _GAP_RE.split(text)
    single = len(columns) == 1 or (len(columns) == 2 and columns[1].isdigit())  # a page number
    if geometry is not None:
        left_col, right_col = geometry
        if single and not previous.strip() and indent > left_col + 1 and text[0].isupper():
            return True  # a centred heading; wrapped glosses and examples never follow a blank line
        if indent >= right_col - 8:
            return False  # gloss column only: a wrapped gloss
        if single and has_latin(text) and not has_cyrillic(text) and text[0].isupper():
            return True  # an English heading where only Ukrainian heads stand
    if indent < 20 or not single:
        return False
    if CYRILLIC_UPPER_RE.match(text[0]) or (text[0].isdigit() and not re.match(r"\d+\)", text)):
        return True  # a centered heading; "2) to note" is a wrapped numbered sense
    return geometry is not None and indent < geometry[1] - 8 and text[0].isupper()


def _continues_zone(line: str, geometry: tuple[int, int]) -> bool:
    """An entry line (head at the entry column, gloss at the gloss column) or an example line."""
    left_col, right_col = geometry
    indent = _indent(line)
    if line.lstrip().startswith("•"):
        return indent <= left_col + 4
    if re.match(r"\d+[.)]\s", line[indent:]):
        return False  # a numbered answer or exercise line, never a dictionary head
    gap = next((g for g in _GAP_RE.finditer(line, indent) if g.end() < len(line.rstrip())), None)
    # The gloss must start at the zone's gloss column: a lesson paragraph with a
    # margin gloss further right is not an entry line.
    return (abs(indent - left_col) <= 1 and gap is not None and abs(gap.end() - right_col) <= 8
            and has_cyrillic(line[indent:gap.start()]))


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold())


def is_running_title(line: str, title: str) -> bool:
    """True when ``line`` is the lesson title printed again as a page's running head.

    Seasons 1-3 repeat the English subtitle, Season 6 the whole title after
    ``Lesson N:``: the line's words are the title's last words, from a word
    boundary to its end, punctuation aside.
    """
    heading = _words(re.sub(r"^\s*Lesson\s+\d+\s*:", "", title))
    words = _words(line)
    return 0 < len(words) <= len(heading) and heading[len(heading) - len(words):] == words


def find_vocab_sections(lines: list[str]) -> list[tuple[str, int, int]]:
    """Return (heading, first_body_line, end_line) for every dictionary section.

    A zone ends at ANY heading that is not a vocabulary heading
    (``VOCAB_HEADING_RE``), whatever lines follow it: an exercise or answer
    heading never extends a zone because the next lines happen to be laid out
    like entries. The one heading a zone goes on after is the lesson title
    repeated as a running page head (``is_running_title``) when more entries
    follow in the zone's geometry.
    """
    sections: list[tuple[str, int, int]] = []
    title = lines[0] if lines else ""
    i = 0
    while i < len(lines):
        match = VOCAB_HEADING_RE.match(lines[i])
        if not match:
            i += 1
            continue
        j = i + 1
        geometry = None
        while j < len(lines):
            if geometry is None and lines[j].strip() and not VOCAB_HEADING_RE.match(lines[j]):
                geometry = _section_geometry(lines, j, min(len(lines), j + 6))
            if _is_section_end(lines[j], lines[j - 1], geometry):
                after = next((k for k in range(j + 1, len(lines)) if lines[k].strip()), None)
                if not (geometry is not None and after is not None and is_running_title(lines[j], title)
                        and _continues_zone(lines[after], geometry)):
                    break
            j += 1
        sections.append((match.group(1), i + 1, j))
        i = j
    return sections


def _finish_entry(entry: GlossaryEntry, head: str, gloss_parts: list[str]) -> GlossaryEntry:
    """Split the printed head into members and the gloss into gloss + aspect note; never repair."""
    head = re.sub(r"\s+", " ", head).strip()
    if re.match(r"\d+\.\s", head):  # numbered list in the margin: "2. студе́нт — student"
        head = re.sub(r"^\d+\.\s+", "", head)
        entry.parse_notes.append("list_number_dropped")
    entry.headword_raw = head
    gloss, notes = extract_aspect_notes(re.sub(r"\s+", " ", " ".join(gloss_parts)).strip())
    sentence_like = bool(re.search(r"[.!?…]", head))
    parsed = split_headword(head, split_commas=not sentence_like)
    entry.forms = parsed.forms
    if parsed.empty_forms:
        entry.parse_notes.append("dangling_separator_dropped")
    entry.grammar_note = unique_notes(notes)
    entry.english_gloss = gloss
    return entry


def parse_vocab_section(lines: list[str], heading: str, start: int, end: int) -> list[GlossaryEntry]:
    """Parse one two-column vocabulary section into entries (examples only in Season 6)."""
    geometry = _section_geometry(lines, start, end)
    if geometry is None:
        return []
    left_col, right_col = geometry
    entries: list[GlossaryEntry] = []
    current: GlossaryEntry | None = None
    head = ""
    gloss_parts: list[str] = []
    example: dict[str, str] | None = None

    def close() -> None:
        nonlocal current, example
        if current is None:
            return
        if example is not None:
            current.examples.append(example)
            example = None
        entries.append(_finish_entry(current, head, gloss_parts))
        current = None

    rows: list[tuple[int, int, str, str]] = []
    consumed: dict[int, list[int]] = {}
    for index in range(start, end):
        line = lines[index]
        if not line.strip():
            continue
        indent, left, right = _split_columns(line, right_col)
        if left and not right and has_cyrillic(left) and has_latin(left):
            pair = split_uk_en_line(left)  # columns separated by a single space
            if pair is not None:
                left, right = pair
        if left.startswith(ACUTE) and rows and rows[-1][2]:
            # OCR moved a word's acute and its tail to the next line ("Взаєм" / "́ но!"):
            # one head in the parser's view; the raw span keeps both lines.
            first, prev_indent, prev_left, prev_right = rows[-1]
            rows[-1] = (first, prev_indent, prev_left + re.sub(rf"^{ACUTE}\s*", ACUTE, left),
                        " ".join(part for part in (prev_right, right) if part))
            consumed.setdefault(first, []).append(index)
            continue
        rows.append((index, indent, left, right))

    for index, indent, left, right in rows:
        extra = consumed.get(index, [])
        if left.startswith("•"):
            if current is None:
                continue
            if example is not None:
                current.examples.append(example)
            example = {"uk": left.lstrip("• ").strip(), "en": right.lstrip("• ").strip()}
            current.line_indices.extend([index, *extra])
            continue
        if current is not None and example is not None and (indent > left_col + 1 or not left):
            example["uk"] = f"{example['uk']} {left}".strip()
            example["en"] = f"{example['en']} {right.lstrip('• ')}".strip()
            current.line_indices.extend([index, *extra])
            continue
        if not left:
            if current is not None:
                gloss_parts.append(right)
                current.line_indices.extend([index, *extra])
            continue
        if not has_cyrillic(left) or indent > left_col + 1:
            continue
        if (
            current is not None
            and not current.examples
            and example is None
            and (head.rstrip().endswith((",", "=")) or not right)
        ):
            joiner = " " if head.rstrip().endswith((",", "=")) else " / "
            head = f"{head}{joiner}{left}"
            if right:
                gloss_parts.append(right)
            current.line_indices.extend([index, *extra])
            continue
        close()
        current = GlossaryEntry(KIND_SLOVNYCHOK, heading, index, [index, *extra], anchor=left, column=indent)
        head = left
        gloss_parts = [right] if right else []
    close()
    for entry in entries:
        kept = []
        for ex in entry.examples:
            uk = re.sub(r"\s+", " ", ex["uk"]).strip()
            en = re.sub(r"\s+", " ", ex["en"]).strip()
            if uk and en and has_cyrillic(uk) and has_latin(en) and example_is_complete(uk, en):
                kept.append({"uk": uk, "en": en})
            else:
                entry.parse_notes.append("incomplete_example_dropped")
        entry.examples = kept
    return entries


def _margin_segment(line: str) -> tuple[int, str, bool]:
    """``(column, text, table_cell)`` of the right-margin cell of a lesson line.

    The cell starts after the first gap of three or more spaces that ends at
    ``MARGIN_MIN_COL`` or later (``(-1, '', False)`` when the line has none).
    In a table row (``вони пи́шуть      Пиши́! — Write!``) the cell is the last
    column after a gap of ``TABLE_GAP`` or more spaces (``table_cell``);
    justified margin text (``доє́днуватися,     доєдна́тися``) keeps its words.
    """
    indent = _indent(line)
    end = len(line.rstrip())
    if not line.strip():
        return -1, "", False
    start = indent if indent >= MARGIN_MIN_COL else next(
        (gap.end() for gap in re.finditer(r"\s{3,}", line) if MARGIN_MIN_COL <= gap.end() < end), -1)
    if start < 0:
        return -1, "", False
    table = [gap.end() for gap in re.finditer(rf"\s{{{TABLE_GAP},}}", line) if start < gap.end() < end]
    if table:
        return table[-1], line[table[-1]:end], True
    return start, line[start:end], False


def _split_margin_item(text: str) -> tuple[str, str] | None:
    """Split ``head — gloss`` at the last dash followed by English."""
    for match in reversed(list(_DASH_SPLIT_RE.finditer(text + " "))):
        head = text[: match.start()].strip()
        gloss = text[match.end() :].strip()
        if head and gloss and has_cyrillic(head) and re.match(r"[A-Za-z(“\"‘']|\d+\)\s*[A-Za-z(]", gloss):
            return head, gloss
    return None


_EXERCISE_ITEM_RE = re.compile(r"[А-ЯҐЄІЇA-Z]\)\s")
_EN_TO_UK_BOUNDARY_RE = re.compile(r"(?<=[A-Za-z)\].,;!?»”'])\s+(?=[«\"“]?[Ѐ-ӿ])")


def _split_margin_items(text: str) -> list[tuple[str, str]] | None:
    """Split a margin run into one or more ``head — gloss`` items.

    Two glosses can share a run when the layout leaves no blank line
    (``восени́ — in autumn ідеа́льний — perfect``); split at an English-to-
    Ukrainian boundary only when both sides are complete items, so a gloss
    that cites a Ukrainian word (``diminutive of «ка́ртка»``) stays whole.
    """
    whole = _split_margin_item(text)
    if whole is None:
        return None
    if not has_latin(whole[0]):
        return [whole]
    for boundary in _EN_TO_UK_BOUNDARY_RE.finditer(text):
        first = _split_margin_item(text[: boundary.start()].strip())
        rest = _split_margin_items(text[boundary.end() :].strip())
        if first is not None and not has_latin(first[0]) and rest:
            return [first, *rest]
    return [whole]


def parse_margin_glosses(
    lines: list[str], skip: list[tuple[int, int]]
) -> tuple[list[GlossaryEntry], int, list[int]]:
    """Collect right-margin ``uk — en`` glosses outside the vocabulary sections.

    Returns (entries, non_gloss_segments, non_gloss_lines): segments that never
    formed a ``head — gloss`` item (right-column prose, headings) are counted
    and their lines listed, never kept.
    """
    skipped = {i for start, end in skip for i in range(start, end)}
    entries: list[GlossaryEntry] = []
    non_gloss = 0
    non_gloss_lines: list[int] = []
    buf: list[str] = []
    buf_lines: list[int] = []
    buf_start = 0
    buf_col = 0
    buf_table = False

    def flush() -> None:
        nonlocal buf, buf_lines, non_gloss
        if not buf:
            return
        text = re.sub(r"\s+", " ", " ".join(buf)).strip()
        items = _split_margin_items(text) if any(ch in text for ch in DASH_CHARS) else None
        if items is None:
            non_gloss += 1
            non_gloss_lines.extend(buf_lines)
        for head, gloss in items or ():
            entry = GlossaryEntry(KIND_MARGIN, None, buf_start, list(buf_lines), anchor=buf[0], column=buf_col)
            if len(items or ()) > 1:
                entry.parse_notes.append("shared_margin_run_split")
            _finish_entry(entry, head, [gloss])
            if len(head.split()) > MAX_MARGIN_HEAD_WORDS:
                entry.errors.append("margin_head_too_long")
            unnumbered = _SENSE_MARK_RE.sub(" ", f"{head} {gloss}")
            if _EXERCISE_ITEM_RE.match(head):
                entry.errors.append("exercise_item")  # "Є) Її звати Марина. А це — (його, її)"
            elif unnumbered.count(")") > unnumbered.count("("):
                entry.errors.append("margin_fragment")  # the tail of a parenthetical: "прямо … — informal)."
            entries.append(entry)
        buf, buf_lines = [], []

    for index, line in enumerate(lines):
        column, segment, table_cell = (-1, "", False) if index in skipped else _margin_segment(line)
        if not segment:
            flush()
            continue
        if buf and segment.startswith(ACUTE) and has_cyrillic(buf[-1][-1:]):
            # A displaced acute and the word's tail on the next line ("підприєм" / "́ ець").
            buf[-1] += re.sub(rf"^{ACUTE}\s*", ACUTE, segment)
            buf_lines.append(index)
            continue
        if buf:
            text = " ".join(buf)
            split = _split_margin_item(text)
            has_dash = any(ch in text for ch in DASH_CHARS)
            starts_cyrillic = has_cyrillic(segment[:1]) or segment[:1] in "«"
            if split is not None:
                gloss = split[1]
                gloss_open = gloss.endswith((",", ";", "(", "/", "-", " or", " and")) or gloss.count("(") > gloss.count(
                    ")"
                )
                wrapped_tail = segment[:1].islower() or segment[:1] == "(" or bool(re.match(r"\d+\)", segment))
                # A finished item continues only with a wrapped English tail;
                # a new Ukrainian head or English prose starts a new buffer.
                if starts_cyrillic or not (gloss_open or wrapped_tail):
                    flush()
            elif has_dash:
                if starts_cyrillic and text.count("(") <= text.count(")") and _split_margin_item(segment):
                    flush()  # a complete new item after a dash run with no English gloss
            elif not (starts_cyrillic and text.rstrip().endswith((",", "="))) and not (
                # A Ukrainian head wrapped mid-phrase ("на відмі́ну від" / "(+ родовий відмінок) —"),
                # never across table rows or after a numbered (answer-key) line.
                has_cyrillic(text) and not has_latin(text) and not (table_cell or buf_table)
                and not re.match(r"\d+\.\s", text) and not re.search(r"[.!?…:;»\"”]$", text.rstrip())
                and (segment[:1] == "(" or (has_cyrillic(segment[:1]) and segment[:1].islower()))
            ):
                flush()
        if not buf:
            buf_start, buf_col = index, column
        buf_table = table_cell
        buf.append(segment)
        buf_lines.append(index)
    flush()
    return entries, non_gloss, non_gloss_lines


def parse_lesson(full_text: str) -> LessonParse:
    """Parse one lesson section's vocabulary zones and margin glosses, in line order."""
    lines = full_text.splitlines()
    sections = find_vocab_sections(lines)
    entries: list[GlossaryEntry] = []
    for heading, start, end in sections:
        entries.extend(parse_vocab_section(lines, heading, start, end))
    margin, non_gloss, non_gloss_lines = parse_margin_glosses(
        lines, [(start - 1, end) for _, start, end in sections]
    )
    entries.extend(margin)
    entries.sort(key=lambda entry: entry.line_index)
    return LessonParse(entries, sections, non_gloss, non_gloss_lines)


# Line dispositions of a ULP lesson section (design r3 §8): every line gets one.
ZONE_ENTRY = "zone_entry"
MARGIN_ENTRY = "margin_entry"
PROSE_EXCLUDED = "prose_excluded"
HEADING = "heading"
FURNITURE = "furniture"


def line_dispositions(lines: list[str], parse: LessonParse) -> list[str]:
    """One disposition per line of a lesson section.

    ``heading``: the lesson title (line 0) and every vocabulary-zone heading.
    ``zone_entry`` / ``margin_entry``: lines consumed by an emitted item (a line
    whose right margin holds a gloss is a ``margin_entry`` even when its left
    column is prose). ``furniture``: blank lines. Everything else, including
    margin runs that formed no item and items refused as prose
    (``margin_head_too_long``), is ``prose_excluded``.
    """
    result = [FURNITURE if not line.strip() else PROSE_EXCLUDED for line in lines]
    if lines and lines[0].strip():
        result[0] = HEADING
    for _, start, _ in parse.sections:
        result[start - 1] = HEADING
    for entry in parse.entries:
        if entry.errors:
            continue
        disposition = ZONE_ENTRY if entry.kind == KIND_SLOVNYCHOK else MARGIN_ENTRY
        for index in entry.line_indices:
            result[index] = disposition
    return result
