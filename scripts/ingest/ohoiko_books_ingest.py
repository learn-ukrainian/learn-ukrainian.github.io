#!/usr/bin/env python3
"""Ingest Anna Ohoiko book .txt files into ``data/sources.db`` textbooks table.

Source files live in ``docs/references/private/`` (gitignored). Currently
supports the 2-edition "1000 Most Useful Ukrainian Words" book; the parser
is extensible to "500+ Ukrainian Verbs" and future Ohoiko books.

Schema fit:
- One row per numbered entry → one chunk
- ``author = 'Anna Ohoiko'`` (Анна Огойко)
- ``source_file`` is a stable per-book slug (e.g.
  ``anna-ohoiko-1000-words-2nd-ed``)
- ``title`` is the Ukrainian headword(s) with stress marks
- ``text`` is the full entry body (headword + alt forms + English
  translation + example sentences UK/EN)
- ``grade`` is left empty — Ohoiko's word lists are level-agnostic;
  CEFR mapping is a downstream concern.

Idempotent: the ingest checks each chunk_id against the DB and skips
existing rows. Re-running on an unchanged source produces zero new
inserts; re-running after edits inserts only the changed entries (caveat:
mid-entry edits to the source produce the same chunk_id with different
text — see ``--force`` to overwrite).

Deterministic verification: prints BEFORE / AFTER row counts and a
sample row for each call. Mirrors the evidence convention applied to
the 2026-05-14 channel_id fix (#1976).

Usage:
    .venv/bin/python -m scripts.ingest.ohoiko_books_ingest --book 1000-words
    .venv/bin/python -m scripts.ingest.ohoiko_books_ingest --book 1000-words --dry-run
    .venv/bin/python -m scripts.ingest.ohoiko_books_ingest --book 1000-words --force

Reference:
- ``docs/references/private/1000-Ukrainian-Words-2.0-Ukrainian-Lessons-PDF-4mwsom.txt``
- ``docs/references/private/500+ Ukrainian Verbs - Ukrainian Lessons - PDF.txt``
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "sources.db"
REFERENCES_DIR = PROJECT_ROOT / "docs" / "references" / "private"

# Page-furniture patterns that should be stripped from entry bodies.
# These match Ohoiko's PDF-extracted text exactly; do not over-generalise.
_PAGE_FOOTER_RE = re.compile(r"^\s*Inspiring resources for learning Ukrainian — UkrainianLessons\.com\s+\d+\s*$")
_BARE_PAGE_NUMBER_RE = re.compile(r"^\s*\d+\s*$")
# Page header is a single right-aligned word (the running headword). It
# follows the page footer line and precedes the next entry. We detect it
# heuristically as "≥ 20 leading spaces + 1-3 word tokens with Cyrillic
# content".
_PAGE_HEADER_RE = re.compile(r"^\s{20,}[А-Яа-яҐґЄєІіЇї'’\-\sʼ́]{2,}$")
_ENTRY_START_RE = re.compile(r"^(?P<num>\d{1,4})\.\s+(?P<headword>.+?)(?:\s{2,}(?P<english>.+))?$")

# Headwords in Ohoiko's word list are Ukrainian — Cyrillic letters,
# stress marks, hyphens, apostrophes, optional ``= альт-форма`` segments.
# This filter cleanly rejects matches against:
# - the "How to Use Anki" numbered instruction list earlier in the book
#   (steps like ``2. Anki uses a spaced repetition algorithm…``),
# - back-matter promotional pages where the first character is Latin.
# Allows apostrophes/quotes/parens around the leading char for unusual
# headwords (e.g. quoted clitics), but the leading non-space char must
# eventually be Cyrillic.
_CYRILLIC_CHAR_RE = re.compile(r"[А-ЯҐЄІЇа-яґєії]")

# Hard cap on body lines per entry. A verb-pair entry with two examples
# tops out around ~10 lines (verb pair + aspectual annotation + 2 UK
# examples + 2 EN examples, each potentially wrapping). 25 is generous
# and guarantees we stop accumulating before runaway parsing past the
# last real entry sweeps in promotional back-matter.
_MAX_BODY_LINES = 25

# Lines that signal the end of the word-list section. When we see one
# of these inside an in-flight entry's body, finalize and stop
# accumulating. Matched as a substring on the stripped body line so we
# tolerate leading spacing variation.
_SECTION_TERMINATORS = (
    "Кросворд",  # "Crossword №N" section headers (post-1000)
    "Хай щастить",  # Author's closing line before back-matter
    "Find out more at",  # Promotional back-matter URLs
    "Most Useful Ukrainian Words",  # Repeating header in back-matter pages
    "My New Ukrainian Words",  # Blank-journal section header
)


@dataclass(frozen=True)
class BookConfig:
    slug: str  # CLI key, e.g. "1000-words"
    source_file: str  # textbooks.source_file value
    txt_filename: str  # relative to REFERENCES_DIR
    author: str
    # Canonical Cyrillic author (populates textbooks.author_uk; required
    # by the Cyrillic-native matcher).
    author_uk: str
    grade: str  # left empty for Ohoiko books; reserved for CEFR mapping later
    max_entry_number: int  # advertised entry count (hard cap)


BOOKS: dict[str, BookConfig] = {
    "1000-words": BookConfig(
        slug="1000-words",
        source_file="anna-ohoiko-1000-words-2nd-ed",
        txt_filename="1000-Ukrainian-Words-2.0-Ukrainian-Lessons-PDF-4mwsom.txt",
        author="Anna Ohoiko",
        author_uk="Анна Огоїко",
        grade="",
        # The 2nd edition advertises "1000 Most Useful Ukrainian Words"
        # and the alphabetical entries run #1..#1000 exactly. After
        # entry #1000 the book continues with crossword puzzles and
        # blank journal slots (1001+) for the reader to fill in their
        # own words — none of which is corpus-grade content.
        max_entry_number=1000,
    ),
    # "500-verbs" added in C2 once the 1000-words ingest is verified.
}


@dataclass
class Entry:
    number: int
    headword: str
    english: str
    body_lines: list[str]

    def full_text(self) -> str:
        """Render the entry body as a single text block for indexing.

        Format:
            <headword>  —  <english translation>

            <example UK 1>
                <example EN 1>
            <example UK 2>
                <example EN 2>
        """
        lines = [f"{self.headword}  —  {self.english}".rstrip(" —")]
        if self.body_lines:
            lines.append("")
            lines.extend(self.body_lines)
        return "\n".join(lines).strip() + "\n"


def _is_cyrillic_headword(headword: str) -> bool:
    """True iff the headword starts with (or contains as its first
    non-punctuation char) a Cyrillic letter. Filters out English-headed
    matches like ``Anki uses a spaced repetition…`` from the Anki
    instructions section.
    """
    for ch in headword:
        if ch.isspace() or ch in "\"'’«»()[]{}—-":
            continue
        return bool(_CYRILLIC_CHAR_RE.match(ch))
    return False


def parse_book(txt_path: Path, max_entry_number: int | None = None) -> list[Entry]:
    """Parse a Ohoiko book .txt into a list of Entry objects.

    Pipeline:
    1. Strip page furniture (PDF page footers, bare page numbers,
       right-aligned running headers).
    2. Match ``NNN. <headword> <english>`` entry starts.
    3. Filter to Cyrillic-headed entries only (rejects the
       ``How to Use Anki`` numbered-instruction section that uses the
       same ``NNN.`` shape).
    4. Cap body accumulation at ``_MAX_BODY_LINES`` per entry — guards
       against runaway accumulation past the last real entry (the book's
       back-matter promotional pages have no entry markers, so they
       would otherwise flow into entry #1109's body indefinitely).

    Each Entry starts at a ``NNN.`` marker and consumes subsequent
    non-empty lines until the next marker or the body cap.
    """
    if not txt_path.exists():
        raise FileNotFoundError(f"Source not found: {txt_path}")

    entries: list[Entry] = []
    current: Entry | None = None
    previous_was_footer = False

    with txt_path.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")

            # Page footer + the right-aligned running headword that
            # follows it on the next line.
            if _PAGE_FOOTER_RE.match(line):
                previous_was_footer = True
                continue
            if previous_was_footer:
                previous_was_footer = False
                if _PAGE_HEADER_RE.match(line):
                    continue

            # Bare page-number lines (rare; mostly absorbed by the footer
            # rule above, but a few survive in odd page-break contexts).
            if _BARE_PAGE_NUMBER_RE.match(line) and current is None:
                continue

            m = _ENTRY_START_RE.match(line)
            if m:
                num = int(m.group("num"))
                headword = m.group("headword").strip()
                english = (m.group("english") or "").strip()

                # GATE 1: hard cap. After the advertised word count,
                # the book contains crossword puzzles and blank journal
                # slots (1001+) that should NOT enter the corpus.
                # Finalize whatever entry was in flight and stop opening
                # new ones.
                if max_entry_number is not None and num > max_entry_number:
                    if current is not None:
                        entries.append(current)
                        current = None
                    continue

                # GATE 2: Cyrillic-headed only. Non-Cyrillic ``NNN.``
                # markers belong to the Anki instruction list or other
                # meta-content.
                if not _is_cyrillic_headword(headword):
                    if current is not None:
                        entries.append(current)
                        current = None
                    continue

                # GATE 3: monotonicity. Crossword answer sections after
                # entry #1000 restart numbering at 1; even with the
                # max-entry cap, a mid-book numbering reset would be
                # corruption. Drop any backwards/duplicate number.
                if entries and num <= entries[-1].number:
                    if current is not None:
                        entries.append(current)
                        current = None
                    continue

                # Finalize the previous in-flight entry now that we
                # have a fresh real-entry start.
                if current is not None:
                    entries.append(current)

                current = Entry(
                    number=num,
                    headword=headword,
                    english=english,
                    body_lines=[],
                )
                continue

            # Body line for the in-flight entry.
            if current is not None:
                stripped = line.strip()
                if not stripped:
                    continue
                if any(term in stripped for term in _SECTION_TERMINATORS):
                    # Section break (crossword start, journal section,
                    # back-matter). Finalize the current entry without
                    # absorbing the marker line, and stop accumulating
                    # until the next valid entry start arrives.
                    entries.append(current)
                    current = None
                    continue
                if len(current.body_lines) >= _MAX_BODY_LINES:
                    # Hard cap hit — either a runaway long entry (rare
                    # but possible for verb-pair entries with many
                    # examples) OR we've fallen off the end of the word
                    # list into promotional back-matter. Either way,
                    # finalize and stop accumulating until the next
                    # valid entry start arrives (or doesn't).
                    entries.append(current)
                    current = None
                    continue
                current.body_lines.append(stripped)

    if current is not None:
        entries.append(current)

    return entries


def ingest_entries(
    conn: sqlite3.Connection,
    book: BookConfig,
    entries: list[Entry],
    *,
    force: bool = False,
) -> tuple[int, int]:
    """Insert each entry as one row in textbooks AND link a 1:1
    ``textbook_sections`` row. Returns (inserted, skipped).

    Idempotent: skips chunk_ids that already exist unless ``force=True``,
    in which case existing rows are DELETED before re-insert (the FTS5
    AFTER-INSERT trigger handles the FTS index).

    Section coverage (added 2026-05-14 per #1981 follow-up): each entry
    also produces a ``textbook_sections`` row so the chunk is visible to
    ``_search_sections_fts5`` in scripts/wiki/sources_db.py. Without
    this, the entry's chunk is FTS-searchable but invisible to
    section-level retrieval. See ``_section_coverage.py`` for details.
    """
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
    for e in entries:
        chunk_id = f"{book.source_file}_e{e.number:04d}"
        if chunk_id in existing_ids:
            skipped += 1
            continue
        text = e.full_text()
        batch.append(
            (
                chunk_id,
                e.headword,
                text,
                book.source_file,
                book.grade,
                book.author,
                book.author_uk,
                len(text),
            )
        )
        # Section title format: ``Entry N: <headword>`` — N
        # disambiguates collisions (e.g. ``мати`` as both "mother" and
        # "to have" could share a headword in some books). The unique
        # constraint on (source_file, section_title) keeps this safe.
        new_sections.append(
            LessonSection(
                chunk_id=chunk_id,
                section_title=f"Entry {e.number}: {e.headword}",
                section_number=str(e.number),
                full_text=text,
            )
        )
        inserted += 1

    if batch:
        cur.executemany(
            """INSERT INTO textbooks
                  (chunk_id, title, text, source_file, grade, author,
                   author_uk, char_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            batch,
        )
        link_lesson_sections(
            conn,
            source_file=book.source_file,
            sections=new_sections,
        )

    return inserted, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ingest Anna Ohoiko book .txt files into data/sources.db",
    )
    parser.add_argument(
        "--book",
        choices=sorted(BOOKS),
        required=True,
        help="Which Ohoiko book to ingest (slug).",
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

    book = BOOKS[args.book]
    txt_path = REFERENCES_DIR / book.txt_filename
    if not txt_path.exists():
        print(f"❌ Source file not found: {txt_path}", file=sys.stderr)
        return 2

    print(f"📚 Parsing {book.txt_filename}")
    entries = parse_book(txt_path, max_entry_number=book.max_entry_number)
    print(f"   parsed entries: {len(entries)}")
    print(f"   number range: {entries[0].number}..{entries[-1].number}")
    body_chars = sum(len(e.full_text()) for e in entries)
    print(f"   total body chars: {body_chars:,}")

    if args.dry_run:
        # Show 3 sample renders for spot-check
        print("\n--- DRY-RUN sample (first / middle / last entry) ---")
        for sample in (entries[0], entries[len(entries) // 2], entries[-1]):
            print(f"\n### entry #{sample.number} ###")
            print(sample.full_text())
        return 0

    print(f"\n🗃️  Writing to {args.db}")
    conn = sqlite3.connect(str(args.db))
    try:
        # Deterministic BEFORE evidence
        before = conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file = ?",
            (book.source_file,),
        ).fetchone()[0]
        total_before = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
        print(f"   BEFORE: {before} rows for {book.source_file!r} (table total: {total_before:,})")

        inserted, skipped = ingest_entries(conn, book, entries, force=args.force)
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

        # Sample row evidence
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


if __name__ == "__main__":
    raise SystemExit(main())
