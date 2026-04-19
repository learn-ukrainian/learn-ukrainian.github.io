#!/usr/bin/env python3
"""Extract textbook parent sections from page-level chunks."""

from __future__ import annotations

import argparse
import math
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "data" / "corpus_audit" / "section_extraction_report.md"
UNASSIGNED_BLOCKER_RATE = 0.20

SECTION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS textbook_sections (
    section_id INTEGER PRIMARY KEY,
    source_file TEXT NOT NULL,
    grade INTEGER NOT NULL,
    section_title TEXT NOT NULL,
    section_number TEXT,
    page_start INTEGER,
    page_end INTEGER,
    chunk_count INTEGER NOT NULL,
    full_text TEXT NOT NULL,
    UNIQUE (source_file, section_title)
)
"""

SECTION_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_sections_source_grade "
    "ON textbook_sections (source_file, grade)",
    "CREATE INDEX IF NOT EXISTS idx_sections_grade ON textbook_sections (grade)",
    "CREATE INDEX IF NOT EXISTS idx_textbooks_parent ON textbooks (parent_section_id)",
)

TEXTBOOK_SECTION_INSERT_SQL = """
INSERT INTO textbook_sections (
    source_file,
    grade,
    section_title,
    section_number,
    page_start,
    page_end,
    chunk_count,
    full_text
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

PAGE_TITLE_RE = re.compile(r"^Сторінка\s+(\d+)$")
SECTION_MARKER_RE = re.compile(r"^§\s*([0-9IVXLCDM]+(?:[.][0-9]+)?)\s*[.:-]?\s*(.+)?$", re.IGNORECASE)
ROMAN_SECTION_RE = re.compile(r"^([IVXLCDM]{1,8})[.)]\s+(.+)$")
CHAPTER_RE = re.compile(r"^(розділ|частина|тема)\s+([0-9IVXLCDM]+)(?:[.:-])?\s*(.*)$", re.IGNORECASE)
ALLOWED_TITLE_CHAR_RE = re.compile(r"""[\w\s§№ІіЇїЄєҐґА-Яа-я'’.,:;!?()\-/\"«»•…]""")
SUPPORTED_LETTER_RE = re.compile(r"[A-Za-zА-Яа-яІіЇїЄєҐґ]")
INSTRUCTION_PREFIXES = tuple(
    phrase.lower()
    for phrase in (
        "прочитай",
        "прочитайте",
        "розглянь",
        "розгляньте",
        "поміркуй",
        "поміркуйте",
        "запиши",
        "запишіть",
        "виконай",
        "виконайте",
        "добери",
        "доберіть",
        "усно",
        "склади",
        "складіть",
        "поясни",
        "поясніть",
        "визнач",
        "визначте",
        "установи",
        "установіть",
        "порівняй",
        "порівняйте",
        "відгадай",
        "відгадайте",
        "обговоріть",
        "обговори",
        "досліди",
        "перевір",
        "перевірте",
        "пригадай",
        "пригадайте",
        "послухай",
        "послухайте",
        "перепиши",
        "спиши",
        "спишіть",
        "попрацюйте",
        "доведи",
        "доведіть",
        "розкажи",
        "розкажіть",
        "назви",
        "назвіть",
        "знайди",
        "знайдіть",
        "підготуй",
        "підготуйте",
        "випиши",
        "випишіть",
        "підкресли",
        "підкресліть",
        "познач",
        "позначте",
        "скористайся",
        "проведи",
        "проведіть",
        "простеж",
        "простежте",
        "з’ясуй",
        "з'ясуй",
        "дізнайся",
        "об’єднайтеся",
        "об'єднайтеся",
        "скануй",
        "приготуй",
        "заповни",
    )
)
EXACT_HEADING_STOPWORDS = {
    "зміст",
    "удк",
    "isbn",
    "до речі",
    "до речі…",
    "зразок",
    "практикум",
    "запитання та завдання",
}


class ExtractionBlockedError(RuntimeError):
    """Raised when the unassigned-chunk rate exceeds the configured blocker."""


@dataclass(frozen=True)
class ChunkRow:
    """A textbook chunk row loaded from the source database."""

    id: int
    chunk_id: str
    title: str
    text: str
    source_file: str
    grade: str


@dataclass(frozen=True)
class PreparedChunk:
    """Per-row heading candidates before stateful section assignment."""

    row: ChunkRow
    page_number: int | None
    strong_title: str | None
    strong_kind: str | None
    weak_title: str | None


@dataclass(frozen=True)
class SectionAssignment:
    """Assigned parent section for a chunk row."""

    row: ChunkRow
    page_number: int | None
    section_title: str | None


@dataclass
class SectionGroup:
    """Contiguous chunk run assigned to the same section title."""

    source_file: str
    grade: int
    section_title: str
    rows: list[SectionAssignment]
    section_number: str | None = None

    @property
    def page_start(self) -> int | None:
        pages = [row.page_number for row in self.rows if row.page_number is not None]
        return min(pages) if pages else None

    @property
    def page_end(self) -> int | None:
        pages = [row.page_number for row in self.rows if row.page_number is not None]
        return max(pages) if pages else None

    @property
    def chunk_count(self) -> int:
        return len(self.rows)

    @property
    def full_text(self) -> str:
        return "\n\n".join(row.row.text.strip() for row in self.rows if row.row.text.strip())


@dataclass(frozen=True)
class ExtractionReport:
    """Computed extraction statistics used for the DB backfill and markdown report."""

    sections: list[SectionGroup]
    assignments: list[SectionAssignment]
    total_chunks: int
    assigned_chunks: int
    unassigned_chunks: int
    unassigned_by_source: dict[str, list[str]]
    sections_by_grade: dict[int, int]

    @property
    def assigned_rate(self) -> float:
        return self.assigned_chunks / self.total_chunks if self.total_chunks else 0.0

    @property
    def unassigned_rate(self) -> float:
        return self.unassigned_chunks / self.total_chunks if self.total_chunks else 0.0


def clean_text(value: str) -> str:
    """Normalize OCR whitespace and trim obvious separators."""
    value = value.replace("\xa0", " ")
    value = re.sub(r"[\x00-\x1f\x7f\u2028\u2029]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value.strip(" .-")


def split_heading_lines(text: str, *, limit: int = 8) -> list[str]:
    """Return the first non-empty text lines after OCR cleanup."""
    lines: list[str] = []
    for raw_line in text.splitlines():
        normalized = clean_text(raw_line)
        if normalized:
            lines.append(normalized)
        if len(lines) >= limit:
            break
    return lines


def is_page_placeholder(title: str) -> bool:
    """True when the title is a generic page label instead of a semantic section title."""
    return bool(PAGE_TITLE_RE.fullmatch(clean_text(title)))


def parse_page_number(row: ChunkRow) -> int | None:
    """Infer a page number from the row title, text header, or chunk id suffix."""
    title_match = PAGE_TITLE_RE.fullmatch(clean_text(row.title))
    if title_match:
        return int(title_match.group(1))

    lines = split_heading_lines(row.text, limit=2)
    if lines and lines[0].isdigit():
        return int(lines[0])

    chunk_match = re.search(r"_s(\d+)$", row.chunk_id)
    if chunk_match:
        return int(chunk_match.group(1)) + 1
    return None


def parse_grade(grade: str) -> int:
    """Extract the numeric textbook grade from the stored grade value."""
    normalized = clean_text(grade)
    digits = re.search(r"\d+", normalized)
    if not digits:
        msg = f"Could not parse numeric grade from {grade!r}"
        raise ValueError(msg)
    return int(digits.group(0))


def has_letters(text: str) -> bool:
    """True when the string contains at least one alphabetic character."""
    return any(char.isalpha() for char in text)


def upper_ratio(text: str) -> float:
    """Fraction of alphabetic characters that are uppercase."""
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    return sum(char.isupper() for char in letters) / len(letters)


def word_count(text: str) -> int:
    """Count whitespace-delimited words in a cleaned title candidate."""
    return len([word for word in clean_text(text).split() if word])


def is_instructional_heading(text: str) -> bool:
    """Heuristic filter for exercise prompts that are not section titles."""
    return clean_text(text).lower().startswith(INSTRUCTION_PREFIXES)


def is_garbage_heading(text: str) -> bool:
    """Reject OCR noise and symbol-heavy strings as section titles."""
    normalized = clean_text(text)
    if not normalized or not has_letters(normalized):
        return True
    letters = [char for char in normalized if char.isalpha()]
    if len(letters) < 3:
        return True
    supported_letters = sum(bool(SUPPORTED_LETTER_RE.fullmatch(char)) for char in letters)
    if supported_letters / len(letters) < 0.80:
        return True
    allowed_chars = sum(bool(ALLOWED_TITLE_CHAR_RE.fullmatch(char)) for char in normalized)
    return allowed_chars / len(normalized) < 0.80


def is_sentence_like(text: str) -> bool:
    """Heuristic to reject body-paragraph lines as headings."""
    normalized = clean_text(text)
    if normalized.endswith((":", ";", "?", "!")):
        return True
    words = word_count(normalized)
    if words > 12:
        return True
    return "," in normalized and words > 6


def is_heading_atom(text: str) -> bool:
    """Identify short standalone heading lines worth using in section inference."""
    normalized = clean_text(text)
    if not normalized or is_garbage_heading(normalized):
        return False
    if normalized.lower() in EXACT_HEADING_STOPWORDS or is_instructional_heading(normalized):
        return False
    if re.match(r"^(УДК|ISBN|Рекомендовано|Видано|©)", normalized, re.IGNORECASE):
        return False
    if re.match(r"^\d+[.)]", normalized):
        return False
    if word_count(normalized) == 1 and upper_ratio(normalized) < 0.95:
        return False
    if len(normalized) > 90 or is_sentence_like(normalized):
        return False
    digit_ratio = sum(char.isdigit() for char in normalized) / len(normalized)
    if digit_ratio > 0.25:
        return False
    return normalized[0].isupper() or upper_ratio(normalized) > 0.60


def is_leaf_heading(text: str) -> bool:
    """Stricter heading filter for second-line subsection leaves."""
    normalized = clean_text(text)
    return is_heading_atom(normalized) and word_count(normalized) <= 6


def normalize_section_title(text: str) -> str:
    """Canonicalize a detected title before grouping or persisting it."""
    normalized = clean_text(text)
    match = SECTION_MARKER_RE.match(normalized)
    if match:
        number = match.group(1)
        rest = clean_text(match.group(2) or "")
        return f"§ {number}. {rest}" if rest else f"§ {number}"
    roman_match = ROMAN_SECTION_RE.match(normalized)
    if roman_match:
        return f"{roman_match.group(1)}. {clean_text(roman_match.group(2))}"
    return normalized


def strip_leading_section_marker(section_title: str) -> str:
    """Remove numbering/chapter markers for AC3 grouping normalization."""
    normalized = normalize_section_title(section_title)
    section_match = SECTION_MARKER_RE.match(normalized)
    if section_match:
        return clean_text(section_match.group(2) or "") or normalized

    chapter_match = CHAPTER_RE.match(normalized)
    if chapter_match:
        return clean_text(chapter_match.group(3) or "") or normalized

    roman_match = ROMAN_SECTION_RE.match(normalized)
    if roman_match:
        return clean_text(roman_match.group(2) or "") or normalized

    return normalized


def section_group_key(section_title: str) -> str:
    """Return the normalized grouping key for a section title."""
    return strip_leading_section_marker(section_title).casefold()


def extract_section_number(section_title: str) -> str | None:
    """Pull a section/chapter number out of the canonical section title."""
    normalized = normalize_section_title(section_title)
    section_match = SECTION_MARKER_RE.match(normalized)
    if section_match:
        return section_match.group(1)
    chapter_match = CHAPTER_RE.match(normalized)
    if chapter_match:
        return chapter_match.group(2)
    roman_match = ROMAN_SECTION_RE.match(normalized)
    if roman_match:
        return roman_match.group(1)
    return None


def is_chapter_only(title: str) -> bool:
    """True when the title encodes only a chapter wrapper without a section leaf."""
    match = CHAPTER_RE.match(normalize_section_title(title))
    return bool(match and not clean_text(match.group(3) or ""))


def infer_heading_candidates(lines: list[str]) -> tuple[str | None, str | None, str | None]:
    """Return strong and weak section-title candidates from the top text lines."""
    if not lines:
        return None, None, None

    if lines[0].lower().startswith("зміст"):
        return None, None, None

    for index, line in enumerate(lines[:6]):
        section_match = SECTION_MARKER_RE.match(line)
        if section_match:
            number = section_match.group(1)
            rest = clean_text(section_match.group(2) or "")
            if rest and not is_instructional_heading(rest):
                return normalize_section_title(f"§ {number}. {rest}"), "section", None
            if index + 1 < len(lines) and is_heading_atom(lines[index + 1]):
                return normalize_section_title(f"§ {number}. {lines[index + 1]}"), "section", None

    for index, line in enumerate(lines[:4]):
        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            label = normalize_section_title(line)
            if index + 1 < len(lines) and is_leaf_heading(lines[index + 1]):
                section_title = normalize_section_title(f"{label}. {lines[index + 1]}")
                return section_title, "chapter-section", None
            return label, "chapter", None

    for line in lines[:4]:
        roman_match = ROMAN_SECTION_RE.match(line)
        if roman_match and is_heading_atom(roman_match.group(2)):
            return normalize_section_title(line), "roman", None

    first = normalize_section_title(lines[0])
    second = normalize_section_title(lines[1]) if len(lines) > 1 else ""

    if any(separator in first for separator in (". ", " — ", "  ")) and is_heading_atom(first):
        if second and is_leaf_heading(second) and second.lower() not in first.lower() and upper_ratio(second) >= 0.20:
            return normalize_section_title(f"{first}. {second}"), "breadcrumb-leaf", None
        return first, "breadcrumb", None

    uppercase_lines: list[str] = []
    for line in lines[:3]:
        if is_heading_atom(line) and upper_ratio(line) > 0.70:
            uppercase_lines.append(normalize_section_title(line))
        else:
            break
    if uppercase_lines:
        return " ".join(uppercase_lines[:2]), "caps", None

    if second and is_heading_atom(first) and is_leaf_heading(second) and upper_ratio(second) > 0.70 and word_count(first) <= 5:
        return normalize_section_title(f"{first}. {second}"), "genre-title", None

    weak = first if is_heading_atom(first) else None
    return None, None, weak


def load_textbook_rows(conn: sqlite3.Connection) -> list[ChunkRow]:
    """Load all textbook chunks ordered by source and row id."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT id, chunk_id, title, text, source_file, grade
        FROM textbooks
        ORDER BY source_file, id
        """
    ).fetchall()
    return [
        ChunkRow(
            id=row["id"],
            chunk_id=row["chunk_id"],
            title=row["title"],
            text=row["text"],
            source_file=row["source_file"],
            grade=row["grade"],
        )
        for row in rows
    ]


def prepare_chunks(rows: list[ChunkRow]) -> list[PreparedChunk]:
    """Compute per-row candidate titles before applying section state."""
    prepared: list[PreparedChunk] = []
    for row in rows:
        page_number = parse_page_number(row)
        title = normalize_section_title(row.title)
        strong_title: str | None = None
        strong_kind: str | None = None
        weak_title: str | None = None

        if title and not is_page_placeholder(title) and not is_garbage_heading(title):
            strong_title = title
            strong_kind = "title"
        else:
            lines = split_heading_lines(row.text)
            if lines and lines[0].isdigit():
                lines = lines[1:]
            strong_title, strong_kind, weak_title = infer_heading_candidates(lines)

        prepared.append(
            PreparedChunk(
                row=row,
                page_number=page_number,
                strong_title=strong_title,
                strong_kind=strong_kind,
                weak_title=weak_title,
            )
        )
    return prepared


def accept_weak_heading(prepared: list[PreparedChunk], index: int) -> tuple[str | None, str | None]:
    """Promote a weak heading only when it repeats on adjacent pages in the same source."""
    item = prepared[index]
    if item.weak_title is None:
        return None, None

    previous_same = (
        index > 0
        and prepared[index - 1].row.source_file == item.row.source_file
        and item.weak_title in {prepared[index - 1].strong_title, prepared[index - 1].weak_title}
    )
    next_same = (
        index + 1 < len(prepared)
        and prepared[index + 1].row.source_file == item.row.source_file
        and item.weak_title in {prepared[index + 1].strong_title, prepared[index + 1].weak_title}
    )
    if previous_same or next_same:
        return item.weak_title, "weak-repeat"
    return None, None


def validate_grade_boundaries(rows: list[ChunkRow]) -> None:
    """Raise when a source file spans multiple grades."""
    grades_by_source: dict[str, set[int]] = defaultdict(set)
    for row in rows:
        grades_by_source[row.source_file].add(parse_grade(row.grade))

    for source_file, grades in grades_by_source.items():
        if len(grades) > 1:
            grade_list = ", ".join(str(grade) for grade in sorted(grades))
            msg = f"Source {source_file} spans multiple grades: {grade_list}"
            raise ValueError(msg)


def contextualize_title(title: str, current_chapter: str | None) -> str:
    """Prefix generic repeated labels with chapter context when available."""
    normalized = normalize_section_title(title)
    if not current_chapter:
        return normalized
    if normalized.startswith("§ ") or normalized.lower().startswith(("розділ", "частина", "тема")):
        return normalized
    if current_chapter.lower() in normalized.lower():
        return normalized
    generic_titles = {"практикум", "повторення", "узагальнення", "контрольна робота"}
    if normalized.lower() in generic_titles or word_count(normalized) <= 2:
        return normalize_section_title(f"{current_chapter}. {normalized}")
    return normalized


def assign_sections(rows: list[ChunkRow]) -> list[SectionAssignment]:
    """Assign each chunk row to a parent section title or leave it unassigned."""
    validate_grade_boundaries(rows)
    prepared = prepare_chunks(rows)
    assignments: list[SectionAssignment] = []
    current_source: str | None = None
    current_chapter: str | None = None
    current_section: str | None = None

    for index, item in enumerate(prepared):
        if item.row.source_file != current_source:
            current_source = item.row.source_file
            current_chapter = None
            current_section = None

        candidate_title = item.strong_title
        candidate_kind = item.strong_kind
        if candidate_title is None:
            candidate_title, candidate_kind = accept_weak_heading(prepared, index)

        if candidate_title:
            if candidate_kind == "chapter" or is_chapter_only(candidate_title):
                if current_section is not None and (current_chapter is None or candidate_title == current_chapter):
                    current_chapter = candidate_title
                elif candidate_title != current_chapter:
                    current_chapter = candidate_title
                    current_section = None
            else:
                current_section = contextualize_title(candidate_title, current_chapter)
                chapter_match = CHAPTER_RE.match(current_section)
                if chapter_match:
                    current_chapter = normalize_section_title(f"{chapter_match.group(1)} {chapter_match.group(2)}")

        assignments.append(
            SectionAssignment(
                row=item.row,
                page_number=item.page_number,
                section_title=current_section or current_chapter,
            )
        )

    return assignments


def mergeable_duplicate_title(title: str) -> bool:
    """Decide whether repeated disjoint groups should collapse into one parent section."""
    normalized = normalize_section_title(title)
    return (
        normalized.startswith("§ ")
        or normalized.lower().startswith(("розділ", "частина", "тема"))
        or extract_section_number(normalized) is not None
        or any(separator in normalized for separator in (". ", " — ", "  "))
    )


def title_has_leading_marker(title: str) -> bool:
    """True when the title starts with a structural section/chapter marker."""
    normalized = normalize_section_title(title)
    return bool(
        SECTION_MARKER_RE.match(normalized)
        or CHAPTER_RE.match(normalized)
        or ROMAN_SECTION_RE.match(normalized)
    )


def prefer_section_title(existing: str, candidate: str) -> str:
    """Keep the richer persisted title when grouping marker-normalized variants."""
    existing_normalized = normalize_section_title(existing)
    candidate_normalized = normalize_section_title(candidate)
    existing_score = (title_has_leading_marker(existing_normalized), len(existing_normalized))
    candidate_score = (title_has_leading_marker(candidate_normalized), len(candidate_normalized))
    if candidate_score > existing_score:
        return candidate_normalized
    return existing_normalized


def build_section_groups(assignments: list[SectionAssignment]) -> list[SectionGroup]:
    """Group contiguous assigned chunks into canonical section records."""
    contiguous_groups: list[SectionGroup] = []

    for assignment in assignments:
        if assignment.section_title is None:
            continue

        grade = parse_grade(assignment.row.grade)
        title = normalize_section_title(assignment.section_title)
        if not contiguous_groups:
            contiguous_groups.append(
                SectionGroup(
                    source_file=assignment.row.source_file,
                    grade=grade,
                    section_title=title,
                    section_number=extract_section_number(title),
                    rows=[assignment],
                )
            )
            continue

        current_group = contiguous_groups[-1]
        same_group = (
            current_group.source_file == assignment.row.source_file
            and section_group_key(current_group.section_title) == section_group_key(title)
            and current_group.grade == grade
        )
        if same_group:
            current_group.section_title = prefer_section_title(current_group.section_title, title)
            current_group.section_number = (
                extract_section_number(current_group.section_title)
                or current_group.section_number
            )
            current_group.rows.append(assignment)
            continue

        contiguous_groups.append(
            SectionGroup(
                source_file=assignment.row.source_file,
                grade=grade,
                section_title=title,
                section_number=extract_section_number(title),
                rows=[assignment],
            )
        )

    groups_by_key: dict[tuple[str, str], list[SectionGroup]] = defaultdict(list)
    for group in contiguous_groups:
        groups_by_key[(group.source_file, section_group_key(group.section_title))].append(group)

    finalized: list[SectionGroup] = []
    for duplicate_groups in groups_by_key.values():
        preferred_title = duplicate_groups[0].section_title
        for group in duplicate_groups[1:]:
            preferred_title = prefer_section_title(preferred_title, group.section_title)

        if len(duplicate_groups) == 1 or mergeable_duplicate_title(preferred_title):
            merged_rows = [row for group in duplicate_groups for row in group.rows]
            template = duplicate_groups[0]
            finalized.append(
                SectionGroup(
                    source_file=template.source_file,
                    grade=template.grade,
                    section_title=preferred_title,
                    section_number=extract_section_number(preferred_title),
                    rows=merged_rows,
                )
            )
            continue

        for group in duplicate_groups:
            page_start = group.page_start
            suffix = f" (p. {page_start})" if page_start is not None else f" (chunk {group.rows[0].row.chunk_id})"
            preferred_group_title = prefer_section_title(group.section_title, preferred_title)
            finalized.append(
                SectionGroup(
                    source_file=group.source_file,
                    grade=group.grade,
                    section_title=f"{preferred_group_title}{suffix}",
                    section_number=extract_section_number(preferred_group_title),
                    rows=group.rows,
                )
            )

    return sorted(finalized, key=lambda group: (group.source_file, group.rows[0].row.id))


def compute_report(assignments: list[SectionAssignment], sections: list[SectionGroup]) -> ExtractionReport:
    """Compute the section extraction statistics used for reporting and blocking."""
    total_chunks = len(assignments)
    assigned_chunks = sum(1 for assignment in assignments if assignment.section_title is not None)
    unassigned_chunks = total_chunks - assigned_chunks

    samples: dict[str, list[str]] = defaultdict(list)
    for assignment in assignments:
        if assignment.section_title is None and len(samples[assignment.row.source_file]) < 5:
            samples[assignment.row.source_file].append(assignment.row.chunk_id)

    sections_by_grade = Counter(group.grade for group in sections)
    return ExtractionReport(
        sections=sections,
        assignments=assignments,
        total_chunks=total_chunks,
        assigned_chunks=assigned_chunks,
        unassigned_chunks=unassigned_chunks,
        unassigned_by_source=dict(sorted(samples.items())),
        sections_by_grade=dict(sorted(sections_by_grade.items())),
    )


def percentile(values: list[int], p: float) -> float:
    """Return the percentile value using nearest-rank semantics."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = max(0, math.ceil(p * len(sorted_values)) - 1)
    return float(sorted_values[index])


def render_report(report: ExtractionReport) -> str:
    """Render the markdown validation report required by the ticket."""
    section_sizes = [section.chunk_count for section in report.sections]
    mean_size = mean(section_sizes) if section_sizes else 0.0
    median_size = median(section_sizes) if section_sizes else 0.0
    p95_size = percentile(section_sizes, 0.95)
    largest = sorted(report.sections, key=lambda section: (-section.chunk_count, section.source_file, section.section_title))[:10]
    smallest = sorted(report.sections, key=lambda section: (section.chunk_count, section.source_file, section.section_title))[:10]
    blocker = "BLOCKER" if report.unassigned_rate > UNASSIGNED_BLOCKER_RATE else "OK"

    lines = [
        "# Section Extraction Report",
        "",
        f"- Status: **{blocker}**",
        f"- Total chunks processed: **{report.total_chunks}**",
        f"- Chunks assigned to a section: **{report.assigned_chunks}** ({report.assigned_rate:.2%})",
        f"- Chunks left unassigned: **{report.unassigned_chunks}** ({report.unassigned_rate:.2%})",
        f"- Sections created: **{len(report.sections)}**",
        "",
        "## Unassigned Samples",
        "",
    ]

    if report.unassigned_by_source:
        for source_file, chunk_ids in report.unassigned_by_source.items():
            lines.append(f"- `{source_file}`: {', '.join(f'`{chunk_id}`' for chunk_id in chunk_ids)}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Sections by Grade",
            "",
        ]
    )
    for grade, count in report.sections_by_grade.items():
        lines.append(f"- Grade {grade}: {count}")

    lines.extend(
        [
            "",
            "## Chunks per Section",
            "",
            f"- Mean: {mean_size:.2f}",
            f"- Median: {median_size:.2f}",
            f"- P95: {p95_size:.2f}",
            "",
            "## Largest 10 Sections",
            "",
        ]
    )

    for section in largest:
        lines.append(
            f"- `{section.source_file}` — `{section.section_title}`: {section.chunk_count} chunks "
            f"(pages {section.page_start}–{section.page_end})"
        )

    lines.extend(["", "## Smallest 10 Sections", ""])
    for section in smallest:
        lines.append(
            f"- `{section.source_file}` — `{section.section_title}`: {section.chunk_count} chunks "
            f"(pages {section.page_start}–{section.page_end})"
        )

    return "\n".join(lines) + "\n"


def write_report(report_path: Path, content: str) -> None:
    """Persist the markdown audit report to disk."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check whether a normal SQLite table exists."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def index_exists(conn: sqlite3.Connection, index_name: str) -> bool:
    """Check whether a SQLite index exists."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = ?",
        (index_name,),
    ).fetchone()
    return row is not None


def column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    """Check whether a column exists on a SQLite table."""
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


def ensure_schema(conn: sqlite3.Connection, *, rebuild: bool = False) -> None:
    """Create additive schema artifacts for parent-section extraction."""
    if rebuild and table_exists(conn, "textbook_sections"):
        conn.execute("DROP TABLE textbook_sections")

    if not column_exists(conn, "textbooks", "parent_section_id"):
        conn.execute(
            "ALTER TABLE textbooks ADD COLUMN parent_section_id "
            "INTEGER REFERENCES textbook_sections(section_id)"
        )

    conn.execute(SECTION_TABLE_SQL)
    for statement in SECTION_INDEX_SQL:
        conn.execute(statement)


def persist_sections(conn: sqlite3.Connection, sections: list[SectionGroup], assignments: list[SectionAssignment]) -> None:
    """Write textbook sections and backfilled parent ids to the database."""
    conn.execute("DELETE FROM textbook_sections")
    conn.execute("UPDATE textbooks SET parent_section_id = NULL")

    section_id_by_row_id: dict[int, int] = {}
    for section in sections:
        cursor = conn.execute(
            TEXTBOOK_SECTION_INSERT_SQL,
            (
                section.source_file,
                section.grade,
                section.section_title,
                section.section_number,
                section.page_start,
                section.page_end,
                section.chunk_count,
                section.full_text,
            ),
        )
        section_id = cursor.lastrowid
        for assignment in section.rows:
            section_id_by_row_id[assignment.row.id] = section_id

    backfill_rows = [
        (
            section_id_by_row_id[assignment.row.id],
            assignment.row.id,
        )
        for assignment in assignments
        if assignment.section_title is not None
    ]
    conn.executemany("UPDATE textbooks SET parent_section_id = ? WHERE id = ?", backfill_rows)


def extract_sections(
    db_path: Path = DEFAULT_DB_PATH,
    *,
    report_path: Path = DEFAULT_REPORT_PATH,
    rebuild: bool = False,
) -> ExtractionReport:
    """Compute, validate, and persist textbook parent sections."""
    with sqlite3.connect(str(db_path)) as conn:
        rows = load_textbook_rows(conn)
        assignments = assign_sections(rows)
        sections = build_section_groups(assignments)
        report = compute_report(assignments, sections)
        write_report(report_path, render_report(report))

        if report.unassigned_rate > UNASSIGNED_BLOCKER_RATE:
            msg = (
                f"Unassigned chunk rate {report.unassigned_rate:.2%} exceeds blocker "
                f"threshold {UNASSIGNED_BLOCKER_RATE:.0%}"
            )
            raise ExtractionBlockedError(msg)

        with conn:
            ensure_schema(conn, rebuild=rebuild)
            persist_sections(conn, sections, assignments)
        return report


def parse_args() -> argparse.Namespace:
    """Parse CLI flags for the extraction run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to data/sources.db")
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Path to the markdown validation report",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Drop and recreate only the textbook_sections table before backfilling",
    )
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    args = parse_args()
    report = extract_sections(args.db, report_path=args.report, rebuild=args.rebuild)
    print(
        "Extracted "
        f"{len(report.sections)} sections from {report.total_chunks} chunks; "
        f"assigned {report.assigned_chunks} ({report.assigned_rate:.2%})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
