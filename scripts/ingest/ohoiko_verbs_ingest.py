#!/usr/bin/env python3
"""Ingest Anna Ohoiko *"500+ Ukrainian Verbs"* (1st ed, 2024) into
``data/sources.db`` textbooks table.

Unlike the 2nd-edition *"1000 Most Useful Ukrainian Words"* book
(parsed by ``ohoiko_books_ingest.py``), this book has a *page-based*
shape: each verb gets a full page with its conjugation tables, stems,
aspectual info, and example sentences. Per-line markers like
``NNN. <headword> <english>`` don't apply here — instead a page-break
form-feed ``\\x0c`` followed by ``№N`` (or ``№ N`` with optional
spacing) opens each verb page.

Schema fit:
- One row per verb page (mid-grained chunk, ~3-5 KB per verb)
- ``author = 'Anna Ohoiko'``
- ``source_file = 'anna-ohoiko-500-verbs'``
- ``title = '<imperfective> | <perfective>'`` (the headword pair)
- ``text = full page body`` (stems + translation + conjugation tables
  + example sentences with bilingual UK/EN pairs)
- ``grade = ''`` (CEFR mapping is a downstream concern)
- ``chunk_id = '<source_file>_v<NNNN>'`` (``v`` for verb)

Section coverage: writes ``textbook_sections`` rows natively via the
shared ``_section_coverage`` helper so the chunks are visible to
section-level retrieval (``_search_sections_fts5``). Without this,
chunks land in textbooks + FTS but are invisible to the section query
path (see ``docs/session-state/2026-05-14-content-indexing-audit-brief.md``).

Idempotent: each verb's chunk_id is checked against the DB and skipped
when present. Re-running on an unchanged source produces zero new
inserts; use ``--force`` to delete existing rows for the source_file
before re-insert.

Deterministic verification: prints BEFORE / AFTER row counts and three
sample rows per call. Mirrors the evidence convention required by the
2026-05-14 determinism rule.

Usage:
    .venv/bin/python -m scripts.ingest.ohoiko_verbs_ingest
    .venv/bin/python -m scripts.ingest.ohoiko_verbs_ingest --dry-run
    .venv/bin/python -m scripts.ingest.ohoiko_verbs_ingest --force

Source file:
    docs/references/private/500+ Ukrainian Verbs - Ukrainian Lessons - PDF.txt
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

from scripts.ingest._section_coverage import (
    LessonSection,
    ensure_section_schema,
    link_lesson_sections,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "sources.db"
REFERENCES_DIR = PROJECT_ROOT / "docs" / "references" / "private"

SOURCE_FILE = "anna-ohoiko-500-verbs"
TXT_FILENAME = "500+ Ukrainian Verbs - Ukrainian Lessons - PDF.txt"
AUTHOR = "Anna Ohoiko"
# Canonical Cyrillic author; populates textbooks.author_uk so the
# Cyrillic-native matcher resolves citations.
AUTHOR_UK = "Анна Огоїко"
MAX_VERB_NUMBER = 500  # hard cap; book advertises "500+ verbs" but the
# numbered series ends at exactly #500.

# ---------------------------------------------------------------------------
# Marker patterns
# ---------------------------------------------------------------------------

# Verb-page START anchor.
# Format observed across the file:
#   * ``\f№1`` (form-feed + no space) for early pages
#   * ``№ 10`` and ``№ 211`` (with space, with optional leading
#     whitespace from PDF column-alignment artifacts)
#   * ``№ 212`` (form-feed + leading space + ``№`` + space + digits)
# The single regex below covers all variants. Leading whitespace,
# optional form-feed, optional whitespace, ``№``, optional whitespace,
# digits, optional trailing whitespace, end of line.
_VERB_START_RE = re.compile(r"^\s*\f?\s*№\s*(?P<num>\d+)\s*$")

# Page footer: ``Back to Contents Inspiring resources for learning
# Ukrainian — UkrainianLessons.com <page>``. Single line per page break.
_PAGE_FOOTER_RE = re.compile(r"^\s*Back to Contents\s+Inspiring resources for learning Ukrainian")

# Running section header at top of certain pages.
_SECTION_HEADER_RE = re.compile(r"^\s*Ukrainian Verb Conjugation Charts\s*$")

# Bare form-feed-only line (page break with nothing else).
_BARE_FF_RE = re.compile(r"^\s*\f\s*$")

# End-of-content terminator. After the last verb page, the book has
# alphabetical indexes of Ukrainian + English verbs. The first
# appearance of ``Index of Ukrainian Verbs`` (outside the ToC at the
# top of the file) marks the end of the verb content.
_INDEX_TERMINATOR = "Index of Ukrainian Verbs"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Verb:
    number: int
    body_lines: list[str] = field(default_factory=list)
    headword_line: str = ""  # cached: first non-empty body line

    @property
    def title(self) -> str:
        """Render a compact section title from the headword line.

        The headword line is shaped like
        ``аналізува́ти | проаналізува́ти   Present / Future Stems: …``.
        We keep only the imperfective + perfective pair (everything
        before two or more spaces).
        """
        line = self.headword_line.strip()
        # Split on the first multi-space gap (the headword and the
        # stems metadata are separated by long PDF column padding).
        m = re.match(r"^(.+?)\s{2,}", line)
        return (m.group(1) if m else line).strip()

    def render(self) -> str:
        """Render the verb page as a single text block for indexing.

        Format: headword pair + blank + body lines (joined with newlines).
        Lines retain their original leading whitespace so the
        conjugation-table column structure is preserved in retrieval
        snippets.
        """
        if not self.body_lines:
            return f"Verb {self.number}\n"
        # Keep title from being printed twice — the body already starts
        # with the headword line. Just join.
        return "\n".join(self.body_lines) + "\n"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def _is_furniture(line: str) -> bool:
    """Return True when ``line`` is PDF page furniture (page footer,
    running header, bare form-feed) that should be stripped from
    verb bodies."""
    if _PAGE_FOOTER_RE.match(line):
        return True
    if _SECTION_HEADER_RE.match(line):
        return True
    return bool(_BARE_FF_RE.match(line))


def parse_book(txt_path: Path) -> list[Verb]:
    """Parse the 500+ Ukrainian Verbs .txt into a list of Verb objects.

    Pipeline:
    1. Skip everything before the first verb-start marker. The book
       opens with a grammar guide + ToC + introduction; the numbered
       series of verb pages starts around line 2600.
    2. For each subsequent line:
       a. If it matches a verb-start marker AND ``num > current.number``:
          finalize the current verb, open a new one.
       b. If it matches a verb-start marker with the same number:
          treat as a page-header redundancy (rare; defensive). Skip.
       c. If it matches page furniture, skip.
       d. If it contains ``Index of Ukrainian Verbs``, finalize the
          current verb and stop accumulating (we've reached the
          alphabetical appendix).
       e. Otherwise, append to the current verb's body (preserve
          leading whitespace; strip trailing whitespace only).
    3. The first non-empty body line is captured as the
       ``headword_line`` for title extraction.
    """
    if not txt_path.exists():
        raise FileNotFoundError(f"Source not found: {txt_path}")

    verbs: list[Verb] = []
    current: Verb | None = None
    terminated = False

    with txt_path.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip()

            # Verb-start marker first (must precede furniture check
            # because the form-feed lives ON the marker line).
            m = _VERB_START_RE.match(line)
            if m:
                num = int(m.group("num"))
                if num > MAX_VERB_NUMBER:
                    # Defensive: book advertises "500+" but numbered
                    # series ends at #500. Anything past that is not a
                    # real entry — could be appendix material.
                    if current is not None:
                        verbs.append(current)
                        current = None
                    continue
                if current is None:
                    current = Verb(number=num)
                    terminated = False
                    continue
                if num > current.number:
                    verbs.append(current)
                    current = Verb(number=num)
                    terminated = False
                    continue
                # Same or lower number — page-header redundancy. Skip.
                continue

            if current is None:
                # Still in cover/ToC/intro region.
                continue

            if terminated:
                continue

            if _is_furniture(line):
                continue

            # End-of-content: alphabetical appendix.
            if _INDEX_TERMINATOR in line:
                terminated = True
                continue

            # Strip form-feed embedded inside a non-marker line
            # (defensive — should not happen, but guard anyway).
            cleaned = line.replace("\f", "").rstrip()
            if not cleaned.strip():
                # Blank line. Collapse: keep one blank between content
                # blocks, drop runs.
                if current.body_lines and current.body_lines[-1] != "":
                    current.body_lines.append("")
                continue

            # First non-empty content line of this verb = headword line.
            if not current.headword_line:
                current.headword_line = cleaned.strip()

            current.body_lines.append(cleaned)

    if current is not None:
        # Trim trailing blanks.
        while current.body_lines and not current.body_lines[-1].strip():
            current.body_lines.pop()
        verbs.append(current)

    return verbs


# ---------------------------------------------------------------------------
# DB ingest
# ---------------------------------------------------------------------------


def ingest_verbs(
    conn: sqlite3.Connection,
    verbs: list[Verb],
    *,
    force: bool = False,
) -> tuple[int, int]:
    """Insert each verb page as one row in textbooks AND one
    ``textbook_sections`` row, links via ``parent_section_id``.

    Returns (inserted, skipped).

    Idempotent: skips chunk_ids that already exist unless ``force=True``,
    in which case existing rows are DELETED (including their section
    parents) before re-insert.
    """
    ensure_section_schema(conn)

    cur = conn.cursor()
    existing_ids: set[str] = set()
    if not force:
        rows = cur.execute(
            "SELECT chunk_id FROM textbooks WHERE source_file = ?",
            (SOURCE_FILE,),
        ).fetchall()
        existing_ids = {r[0] for r in rows}

    if force:
        cur.execute(
            "DELETE FROM textbook_sections WHERE source_file = ?",
            (SOURCE_FILE,),
        )
        cur.execute(
            "DELETE FROM textbooks WHERE source_file = ?",
            (SOURCE_FILE,),
        )

    inserted = 0
    skipped = 0
    batch: list[tuple] = []
    new_sections: list[LessonSection] = []
    for verb in verbs:
        chunk_id = f"{SOURCE_FILE}_v{verb.number:04d}"
        if chunk_id in existing_ids:
            skipped += 1
            continue
        text = verb.render()
        title = verb.title or f"Verb {verb.number}"
        batch.append(
            (
                chunk_id,
                title,
                text,
                SOURCE_FILE,
                "",  # grade
                AUTHOR,
                AUTHOR_UK,
                len(text),
            )
        )
        new_sections.append(
            LessonSection(
                chunk_id=chunk_id,
                section_title=f"Verb {verb.number}: {title}",
                section_number=str(verb.number),
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
            source_file=SOURCE_FILE,
            sections=new_sections,
        )

    return inserted, skipped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Ingest Anna Ohoiko "500+ Ukrainian Verbs" into data/sources.db',
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

    txt_path = REFERENCES_DIR / TXT_FILENAME
    if not txt_path.exists():
        print(f"❌ Source file not found: {txt_path}", file=sys.stderr)
        return 2

    print(f"📚 Parsing {TXT_FILENAME}")
    verbs = parse_book(txt_path)
    print(f"   parsed verbs: {len(verbs)} (expected: {MAX_VERB_NUMBER})")
    if verbs:
        print(f"   number range: {verbs[0].number}..{verbs[-1].number}")
        body_chars = sum(len(v.render()) for v in verbs)
        print(f"   total body chars: {body_chars:,}")

    if args.dry_run:
        print("\n--- DRY-RUN sample (first / middle / last verb) ---")
        if not verbs:
            print("   (no verbs parsed)")
            return 0
        samples = [verbs[0], verbs[len(verbs) // 2], verbs[-1]]
        for sample in samples:
            print(f"\n### verb #{sample.number}: {sample.title!r} ###")
            text = sample.render()
            print(text[:400] + ("…" if len(text) > 400 else ""))
        return 0

    print(f"\n🗃️  Writing to {args.db}")
    conn = sqlite3.connect(str(args.db))
    try:
        before = conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file = ?",
            (SOURCE_FILE,),
        ).fetchone()[0]
        total_before = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
        sec_before = conn.execute(
            "SELECT COUNT(*) FROM textbook_sections WHERE source_file = ?",
            (SOURCE_FILE,),
        ).fetchone()[0]
        print(f"   BEFORE: {before} chunks, {sec_before} sections for {SOURCE_FILE!r} (table total: {total_before:,})")

        inserted, skipped = ingest_verbs(conn, verbs, force=args.force)
        conn.commit()

        after = conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file = ?",
            (SOURCE_FILE,),
        ).fetchone()[0]
        total_after = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
        sec_after = conn.execute(
            "SELECT COUNT(*) FROM textbook_sections WHERE source_file = ?",
            (SOURCE_FILE,),
        ).fetchone()[0]
        print(f"   inserted: {inserted}, skipped: {skipped}")
        print(
            f"   AFTER: {after} chunks, {sec_after} sections for {SOURCE_FILE!r} "
            f"(table total: {total_after:,}, delta +{total_after - total_before})"
        )

        sample = conn.execute(
            """SELECT chunk_id, title, char_count, substr(text, 1, 100) AS snippet
                 FROM textbooks WHERE source_file = ? ORDER BY chunk_id LIMIT 3""",
            (SOURCE_FILE,),
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
