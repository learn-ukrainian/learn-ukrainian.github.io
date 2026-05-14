"""Shared helper: link each ingested textbook chunk to a textbook_sections row.

Context
-------
``scripts/wiki/sources_db.py`` exposes section-level retrieval via
``_search_sections_fts5``. That function filters textbook chunks by
``parent_section_id IS NOT NULL`` and joins to ``textbook_sections`` for
section-grouped results. Any chunk with NULL parent_section_id is
invisible to section-level retrieval — even if it lives in the base
``textbooks`` table and is searchable via raw FTS.

The school-textbook pipeline at ``scripts/wiki/extract_sections.py`` is
designed for traditional textbook PDFs with markers like ``§ N``,
``Сторінка N``, ``Розділ N``. It does not produce sections for
lesson-style books (Anna Ohoiko's word lists, Ukrainian Lessons Podcast
lesson notes) — those books simply don't have those markers.

This helper provides the missing path: for any ingester whose source
unit naturally maps 1:1 to a chunk AND a section (e.g. one ULP lesson →
one chunk → one section), it writes the corresponding
``textbook_sections`` row and sets ``textbooks.parent_section_id``.

The helper is idempotent on the natural key (source_file, section_title)
and writes a sentinel ``grade=0`` for non-school reference material
(school books use grades 1-11; 0 is unused by them per audit
2026-05-14).

Usage
-----
    from scripts.ingest._section_coverage import LessonSection, link_lesson_sections

    sections = [
        LessonSection(
            chunk_id="ulp-1-00-lesson-notes_l0001",
            section_title="Lesson 1: Informal Greetings in Ukrainian",
            section_number="1",
            full_text="<lesson body>",
        ),
        ...
    ]
    inserted, linked = link_lesson_sections(
        conn,
        source_file="ulp-1-00-lesson-notes",
        sections=sections,
    )

Returns ``(inserted_section_rows, linked_chunk_rows)`` for evidence
reporting. Skipped sections/chunks are inferred as ``len(sections) -
inserted``.

The helper does NOT commit; the caller controls transactions.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

# Sentinel grade for non-school reference material (Anna Ohoiko books,
# Ukrainian Lessons Podcast lesson notes, etc.). School-textbook
# sections use grades 1-11; grade=0 is unused there per
# 2026-05-14 audit of textbook_sections.grade distribution.
NON_SCHOOL_GRADE = 0


@dataclass(frozen=True)
class LessonSection:
    """One chunk = one section. Reference-material ingest unit."""

    chunk_id: str
    section_title: str
    section_number: str  # textbook_sections.section_number is TEXT-typed
    full_text: str


def link_lesson_sections(
    conn: sqlite3.Connection,
    *,
    source_file: str,
    sections: list[LessonSection],
    grade: int = NON_SCHOOL_GRADE,
) -> tuple[int, int]:
    """Write textbook_sections rows and link textbooks.parent_section_id.

    Returns ``(inserted_section_rows, linked_chunk_rows)``.

    Idempotent:
    - The UNIQUE (source_file, section_title) constraint guards against
      duplicate inserts. We use ``INSERT OR IGNORE`` and re-read the
      section_id for each row after.
    - ``UPDATE textbooks SET parent_section_id = ?`` is unconditional —
      re-running on already-linked chunks is a no-op.

    Caller commits or rolls back. The helper performs no transaction
    management of its own.
    """
    cur = conn.cursor()
    inserted_count = 0
    linked_count = 0

    for sec in sections:
        # 1. INSERT OR IGNORE the section row (idempotent on unique key)
        before = cur.execute(
            "SELECT section_id FROM textbook_sections WHERE source_file = ? AND section_title = ?",
            (source_file, sec.section_title),
        ).fetchone()
        if before is None:
            cur.execute(
                """INSERT INTO textbook_sections
                       (source_file, grade, section_title, section_number,
                        page_start, page_end, chunk_count, full_text)
                   VALUES (?, ?, ?, ?, NULL, NULL, ?, ?)""",
                (
                    source_file,
                    grade,
                    sec.section_title,
                    sec.section_number,
                    1,  # chunk_count: 1:1 mapping
                    sec.full_text,
                ),
            )
            section_id = cur.lastrowid
            inserted_count += 1
        else:
            section_id = before[0]

        # 2. Link the corresponding textbooks row to this section
        result = cur.execute(
            "UPDATE textbooks SET parent_section_id = ? WHERE chunk_id = ? AND source_file = ?",
            (section_id, sec.chunk_id, source_file),
        )
        if result.rowcount > 0:
            linked_count += 1

    return inserted_count, linked_count


def ensure_section_schema(conn: sqlite3.Connection) -> None:
    """Create textbook_sections + parent_section_id column if missing.

    Defensive — the schema is normally provisioned by
    ``scripts/wiki/extract_sections.py``. This guards against running
    this helper against a fresh DB where the school-textbook pipeline
    has never run. No-op when the schema is already present.
    """
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS textbook_sections (
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
           )"""
    )
    # textbooks.parent_section_id is added by the school-textbook
    # pipeline. If it's missing, add it as a nullable INTEGER ref.
    cols = {r[1] for r in cur.execute("PRAGMA table_info(textbooks)").fetchall()}
    if "parent_section_id" not in cols:
        cur.execute(
            "ALTER TABLE textbooks ADD COLUMN parent_section_id INTEGER REFERENCES textbook_sections(section_id)"
        )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_textbooks_parent ON textbooks (parent_section_id)")
