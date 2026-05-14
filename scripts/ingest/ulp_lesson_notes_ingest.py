#!/usr/bin/env python3
"""Ingest Ukrainian Lessons Podcast (ULP) lesson-notes .txt files into
``data/sources.db`` textbooks table.

Six "lesson notes (all in one file)" books cover six seasons of the
podcast (~40 lessons each, 240 total):

- ULP 1-00 (Season 1, lessons #1-40) — English-language podcast notes
- ULP 2-00 (Season 2, lessons #41-80)
- ULP 3-00 (Season 3, lessons #81-120)
- ULP 4-00 (Season 4, lessons #121-160) — Ukrainian-only podcast notes
- ULP 5-00 (Season 5, lessons #161-200)
- ULP 6-00 (Season 6, lessons #201-240)

Schema fit:
- One row per lesson (mid-grained — typical lesson body ~5-15K chars)
- ``author = 'Ukrainian Lessons Podcast'``
- ``source_file`` = per-book slug (e.g. ``ulp-1-00-lesson-notes``)
- ``title`` = "Lesson N: <title>"
- ``text`` = the lesson body with PDF page furniture stripped
- ``grade`` empty (CEFR mapping is a downstream concern)
- ``chunk_id`` = ``{source_file}_l{NNNN}`` (e.g. ``ulp-1-00-lesson-notes_l0001``)

Marker formats (verified empirically against all six books):
- Seasons 1-3: lesson start = ``Lesson Notes № N`` (with space between №
  and the number). Page running heads use ``Episode N — Title`` format
  in English and never conflict with the start marker.
- Seasons 4-6: lesson start = ``Конспект уроку № N`` (with space). Page
  running heads use ``Конспект уроку №N`` (NO space) — the spacing
  disambiguates them cleanly. This invariant is exercised by the test
  fixture.

Idempotent: each lesson's chunk_id is checked against the DB and skipped
when present. Re-running on an unchanged source produces zero new
inserts; use ``--force`` to delete existing rows for the source_file
before re-insert.

Deterministic verification: prints BEFORE / AFTER row counts and three
sample rows per call. Mirrors the evidence convention required by the
2026-05-14 determinism rule (see
``docs/best-practices/deterministic-over-hallucination.md``).

Usage:
    .venv/bin/python -m scripts.ingest.ulp_lesson_notes_ingest --book 1-00
    .venv/bin/python -m scripts.ingest.ulp_lesson_notes_ingest --book 1-00 --dry-run
    .venv/bin/python -m scripts.ingest.ulp_lesson_notes_ingest --all
    .venv/bin/python -m scripts.ingest.ulp_lesson_notes_ingest --book 1-00 --force

Source files (gitignored, in ``docs/references/private/``):
- ``ULP 1-00 Lesson Notes (all in one file) (2023).txt``
- ``ULP 2-00 Lesson Notes (all in one file).txt``
- ``ULP 3-00 Lesson Notes (all in one file).txt``
- ``ULP 4-00 Lesson Notes (all in one file).txt``
- ``ULP 5-00 Lesson Notes (all in one file).txt``
- ``ULP 6-00 Lesson Notes (all in one file).txt``
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "sources.db"
REFERENCES_DIR = PROJECT_ROOT / "docs" / "references" / "private"
AUTHOR = "Ukrainian Lessons Podcast"

# ---------------------------------------------------------------------------
# Marker patterns
# ---------------------------------------------------------------------------

# Lesson START anchor: requires at least one space between № and the
# number. This is the load-bearing disambiguator versus page running
# heads (which use ``Конспект уроку №NNN`` with no space).
_LESSON_START_RE = re.compile(
    r"^\s*(?P<heading>Lesson\s+Notes|Конспект\s+уроку)"
    r"\s+№\s+(?P<num>\d{1,4})\s*$"
)

# Page-running-head pattern for seasons 4-6: ``Конспект уроку №NNN``
# (NO space between № and the number). Always page furniture; the
# zero-space requirement is the disambiguator from the lesson-start
# anchor which always has ≥1 space between № and the number.
_RUNNING_HEAD_4_6_RE = re.compile(r"^\s*Конспект\s+уроку\s+№\d{1,4}\s*$")

# Page-running-head pattern for seasons 1-3: ``Episode N — Title``.
_RUNNING_HEAD_1_3_RE = re.compile(r"^\s*Episode\s+\d+\s+—")

# ``Link to audio: ukrainianlessons.com/episodeN`` appears in every
# lesson directly below the lesson title (verified 80/80 in spot-check
# of ULP 1-00 and 6-00). It serves as the title's natural lower bound:
# any non-blank/non-furniture lines between the lesson-start marker and
# this line make up the title (possibly multi-line, e.g. ``Василь Стус,
# шістдесятники та дисиденти`` is broken across two PDF lines).
_LINK_TO_AUDIO_RE = re.compile(r"^\s*Link to audio:")

# Page footer: ``Inspiring resources for learning Ukrainian — UkrainianLessons.com``
# May be followed by trailing spaces and a page number on the same or
# next line.
_PAGE_FOOTER_RE = re.compile(r"^\s*Inspiring resources for learning Ukrainian — UkrainianLessons\.com")

# ``Back to Contents <page-number>`` lines that follow the page footer.
_BACK_TO_CONTENTS_RE = re.compile(r"^\s*Back to Contents\s+\d+\s*$")

# Standalone ``UkrainianLessons.com`` lines that appear at page tops
# (cover-page style on first ~3 pages of each book).
_UKRLESSONS_BARE_RE = re.compile(r"^\s*UkrainianLessons\.com\s*$")

# Season header at page tops: ``Ukrainian Lessons Podcast: Season N``
_SEASON_HEADER_RE = re.compile(r"^\s*Ukrainian\s+Lessons\s+Podcast:\s+Season\s+\d+\s*$")

# Bare page-number lines (e.g., ``5``, ``190``). Strictly numeric +
# optional whitespace.
_BARE_PAGE_NUMBER_RE = re.compile(r"^\s*\d{1,4}\s*$")

# End-of-content terminators. When encountered AFTER all lessons have
# been opened (i.e. we're inside the last lesson's body), finalize the
# current lesson without absorbing the terminator line and stop
# accumulating.
_SECTION_TERMINATORS = (
    "Відповіді до вправ",  # "Answers to exercises" appendix (seasons 1-3)
    "Key Phrases ",  # "Key Phrases N-NNN" summary appendix (season 4)
)

# Hard cap on body lines per lesson. ULP lessons are long (~200-400
# stripped lines is typical). 2000 is the runaway-guard threshold —
# trips if the file structure unexpectedly shifts and we absorb
# back-matter into the final lesson.
_MAX_BODY_LINES = 2000


# ---------------------------------------------------------------------------
# Per-book config
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BookConfig:
    slug: str  # CLI key, e.g. "1-00"
    source_file: str  # textbooks.source_file value
    txt_filename: str  # relative to REFERENCES_DIR
    season: int  # 1..6
    expected_lessons: int = 40  # all six books are 40 lessons each


BOOKS: dict[str, BookConfig] = {
    "1-00": BookConfig(
        slug="1-00",
        source_file="ulp-1-00-lesson-notes",
        txt_filename="ULP 1-00 Lesson Notes (all in one file) (2023).txt",
        season=1,
    ),
    "2-00": BookConfig(
        slug="2-00",
        source_file="ulp-2-00-lesson-notes",
        txt_filename="ULP 2-00 Lesson Notes (all in one file).txt",
        season=2,
    ),
    "3-00": BookConfig(
        slug="3-00",
        source_file="ulp-3-00-lesson-notes",
        txt_filename="ULP 3-00 Lesson Notes (all in one file).txt",
        season=3,
    ),
    "4-00": BookConfig(
        slug="4-00",
        source_file="ulp-4-00-lesson-notes",
        txt_filename="ULP 4-00 Lesson Notes (all in one file).txt",
        season=4,
    ),
    "5-00": BookConfig(
        slug="5-00",
        source_file="ulp-5-00-lesson-notes",
        txt_filename="ULP 5-00 Lesson Notes (all in one file).txt",
        season=5,
    ),
    "6-00": BookConfig(
        slug="6-00",
        source_file="ulp-6-00-lesson-notes",
        txt_filename="ULP 6-00 Lesson Notes (all in one file).txt",
        season=6,
    ),
}


@dataclass
class Lesson:
    number: int
    title: str = ""
    body_lines: list[str] = field(default_factory=list)

    def render(self) -> str:
        """Render the lesson as a single text block for indexing.

        Format:
            Lesson N: <title>

            <body line 1>
            <body line 2>
            ...
        """
        header = f"Lesson {self.number}: {self.title}".rstrip(": ") if self.title else f"Lesson {self.number}"
        if not self.body_lines:
            return header + "\n"
        return header + "\n\n" + "\n".join(self.body_lines) + "\n"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def _is_page_furniture(line: str) -> bool:
    """Return True if ``line`` is PDF page furniture (footer, header,
    running head, bare page number, season header) that should be
    stripped from lesson bodies.
    """
    if not line.strip():
        return False  # blank lines handled separately
    return bool(
        _PAGE_FOOTER_RE.match(line)
        or _BACK_TO_CONTENTS_RE.match(line)
        or _UKRLESSONS_BARE_RE.match(line)
        or _SEASON_HEADER_RE.match(line)
        or _BARE_PAGE_NUMBER_RE.match(line)
        or _RUNNING_HEAD_4_6_RE.match(line)
        or _RUNNING_HEAD_1_3_RE.match(line)
    )


def parse_book(txt_path: Path) -> list[Lesson]:
    """Parse a ULP lesson-notes .txt into a list of Lesson objects.

    Pipeline:
    1. Locate the first lesson-start marker (``Lesson Notes № N`` or
       ``Конспект уроку № N`` with at least one space between № and the
       number). Skip everything before it (cover pages + ToC).
    2. For each subsequent line:
       a. If it matches another lesson-start marker AND the number is
          strictly greater than the current lesson, finalize the current
          and open a new one.
       b. If it matches the current lesson-start marker again (same N
          with space), treat as a page header redundancy and skip.
       c. If it matches page furniture, skip.
       d. If it contains a SECTION_TERMINATORS substring, finalize the
          current lesson and stop accumulating until EOF.
       e. Otherwise, append to the current lesson's body (stripped of
          trailing whitespace; leading whitespace preserved for column
          structure where present).
    3. Title heuristic: the first non-blank, non-furniture line AFTER
       the lesson start is captured as the title. The title line then
       does NOT enter the body — the renderer adds it via the header.
    """
    if not txt_path.exists():
        raise FileNotFoundError(f"Source not found: {txt_path}")

    lessons: list[Lesson] = []
    current: Lesson | None = None
    title_fragments: list[str] = []
    captured_title = False
    terminated = False
    consecutive_blanks = 0

    def _finalize_title() -> None:
        """Join accumulated title fragments with single spaces and
        clear the buffer."""
        nonlocal captured_title, title_fragments
        if current is not None and title_fragments:
            current.title = " ".join(title_fragments).strip().rstrip(",")
        captured_title = True
        title_fragments = []

    with txt_path.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip()  # trailing whitespace only

            m = _LESSON_START_RE.match(line)
            if m:
                num = int(m.group("num"))
                if current is None:
                    # First lesson opened.
                    current = Lesson(number=num)
                    title_fragments = []
                    captured_title = False
                    terminated = False
                    consecutive_blanks = 0
                    continue
                if num > current.number:
                    # Finalize current, open new. Any in-flight title
                    # fragments for the previous lesson get committed.
                    if not captured_title:
                        _finalize_title()
                    lessons.append(current)
                    current = Lesson(number=num)
                    title_fragments = []
                    captured_title = False
                    terminated = False
                    consecutive_blanks = 0
                    continue
                # num == current.number — repeated page header for the
                # same lesson (rare with the with-space pattern, but
                # defensive). Skip.
                continue

            # No lesson in flight yet → still in cover/ToC region.
            if current is None:
                continue

            # Already terminated for this lesson → wait for next marker
            # or EOF, ignore content.
            if terminated:
                continue

            if _is_page_furniture(line):
                continue

            stripped = line.strip()
            if not stripped:
                consecutive_blanks += 1
                # Compress runs of blanks: keep at most one blank line
                # between content blocks (PDF extraction produces 5-10
                # blank lines between paragraphs).
                if current.body_lines and current.body_lines[-1] != "" and consecutive_blanks == 1 and captured_title:
                    current.body_lines.append("")
                continue

            consecutive_blanks = 0

            # Title-capture phase: accumulate non-furniture, non-blank
            # lines between the lesson-start marker and the
            # ``Link to audio:`` landmark. Multi-line PDF titles
            # (e.g. ``Василь Стус,\nшістдесятники та дисиденти``) join
            # into one title via a single space.
            if not captured_title:
                if _LINK_TO_AUDIO_RE.match(line):
                    # Title block ends — finalize accumulated fragments
                    # (which may be empty if the PDF layout omitted the
                    # title entirely) and DROP the link line itself.
                    _finalize_title()
                    continue
                title_fragments.append(stripped)
                continue

            # Section terminator check: appears INSIDE the last
            # lesson's body to mark the start of an appendix.
            if any(term in stripped for term in _SECTION_TERMINATORS):
                terminated = True
                continue

            if len(current.body_lines) >= _MAX_BODY_LINES:
                # Runaway guard — should not trigger in practice.
                terminated = True
                continue

            current.body_lines.append(line.rstrip())

    if current is not None:
        # Trim trailing empty body lines.
        while current.body_lines and not current.body_lines[-1].strip():
            current.body_lines.pop()
        lessons.append(current)

    return lessons


# ---------------------------------------------------------------------------
# DB ingest
# ---------------------------------------------------------------------------


def ingest_lessons(
    conn: sqlite3.Connection,
    book: BookConfig,
    lessons: list[Lesson],
    *,
    force: bool = False,
) -> tuple[int, int]:
    """Insert each lesson as one row in textbooks. Returns (inserted, skipped).

    Idempotent: skips chunk_ids that already exist unless ``force=True``,
    in which case existing rows are DELETED for the source_file before
    re-insert.
    """
    # Section coverage (added 2026-05-14 per #1981 follow-up): each
    # lesson also produces a ``textbook_sections`` row so the chunk is
    # visible to ``_search_sections_fts5`` in scripts/wiki/sources_db.py.
    # Without this, the lesson's chunk is FTS-searchable but invisible
    # to section-level retrieval. See ``_section_coverage.py``.
    from scripts.ingest._section_coverage import (
        LessonSection,
        ensure_section_schema,
        link_lesson_sections,
    )

    ensure_section_schema(conn)

    cur = conn.cursor()
    existing_ids: set[str] = set()
    if not force:
        rows = cur.execute(
            "SELECT chunk_id FROM textbooks WHERE source_file = ?",
            (book.source_file,),
        ).fetchall()
        existing_ids = {r[0] for r in rows}

    if force:
        # Reset both textbooks rows and their section parents.
        cur.execute(
            "DELETE FROM textbook_sections WHERE source_file = ?",
            (book.source_file,),
        )
        cur.execute(
            "DELETE FROM textbooks WHERE source_file = ?",
            (book.source_file,),
        )

    inserted = 0
    skipped = 0
    batch: list[tuple] = []
    new_sections: list[LessonSection] = []
    for lesson in lessons:
        chunk_id = f"{book.source_file}_l{lesson.number:04d}"
        if chunk_id in existing_ids:
            skipped += 1
            continue
        text = lesson.render()
        title = f"Lesson {lesson.number}: {lesson.title}".rstrip(": ") if lesson.title else f"Lesson {lesson.number}"
        batch.append(
            (
                chunk_id,
                title,
                text,
                book.source_file,
                "",  # grade (textbooks.grade is TEXT; sections use sentinel 0)
                AUTHOR,
                len(text),
            )
        )
        new_sections.append(
            LessonSection(
                chunk_id=chunk_id,
                section_title=title,
                section_number=str(lesson.number),
                full_text=text,
            )
        )
        inserted += 1

    if batch:
        cur.executemany(
            """INSERT INTO textbooks
                  (chunk_id, title, text, source_file, grade, author, char_count)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            batch,
        )
        link_lesson_sections(
            conn,
            source_file=book.source_file,
            sections=new_sections,
        )

    return inserted, skipped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _run_book(
    book: BookConfig,
    *,
    db_path: Path,
    dry_run: bool,
    force: bool,
) -> int:
    txt_path = REFERENCES_DIR / book.txt_filename
    if not txt_path.exists():
        print(f"❌ Source file not found: {txt_path}", file=sys.stderr)
        return 2

    print(f"\n📚 Parsing {book.txt_filename}")
    lessons = parse_book(txt_path)
    print(f"   parsed lessons: {len(lessons)} (expected: {book.expected_lessons})")
    if lessons:
        print(f"   number range: {lessons[0].number}..{lessons[-1].number}")
        body_chars = sum(len(lesson.render()) for lesson in lessons)
        print(f"   total body chars: {body_chars:,}")

    if dry_run:
        print("\n--- DRY-RUN sample (first / middle / last lesson) ---")
        if not lessons:
            print("   (no lessons parsed)")
            return 0
        samples = [lessons[0], lessons[len(lessons) // 2], lessons[-1]]
        for sample in samples:
            print(f"\n### lesson #{sample.number}: {sample.title!r} ###")
            text = sample.render()
            # Show first 400 chars of body
            print(text[:400] + ("…" if len(text) > 400 else ""))
        return 0

    print(f"\n🗃️  Writing to {db_path}")
    conn = sqlite3.connect(str(db_path))
    try:
        before = conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file = ?",
            (book.source_file,),
        ).fetchone()[0]
        total_before = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
        print(f"   BEFORE: {before} rows for {book.source_file!r} (table total: {total_before:,})")

        inserted, skipped = ingest_lessons(conn, book, lessons, force=force)
        conn.commit()

        after = conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file = ?",
            (book.source_file,),
        ).fetchone()[0]
        total_after = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
        print(f"   inserted: {inserted}, skipped: {skipped}")
        print(
            f"   AFTER: {after} rows for {book.source_file!r} "
            f"(table total: {total_after:,}, delta +{total_after - total_before})"
        )

        sample = conn.execute(
            """SELECT chunk_id, title, char_count, substr(text, 1, 80) AS snippet
                 FROM textbooks WHERE source_file = ? ORDER BY chunk_id LIMIT 3""",
            (book.source_file,),
        ).fetchall()
        print("\n--- AFTER sample rows ---")
        for row in sample:
            print(f"  chunk_id={row[0]}")
            print(f"    title={row[1]!r}")
            print(f"    char_count={row[2]}")
            print(f"    snippet={row[3]!r}")
    finally:
        conn.close()

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ingest ULP lesson-notes .txt files into data/sources.db",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--book",
        choices=sorted(BOOKS),
        help="Ingest a single book by slug (e.g. 1-00).",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Ingest all six ULP books sequentially.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse + report, do not write to DB.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-insert: DELETE existing rows for this source_file before INSERT.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help="Override target DB path (testing only).",
    )
    args = parser.parse_args(argv)

    slugs = sorted(BOOKS) if args.all else [args.book]

    rc = 0
    for slug in slugs:
        result = _run_book(
            BOOKS[slug],
            db_path=args.db,
            dry_run=args.dry_run,
            force=args.force,
        )
        if result != 0:
            rc = result
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
