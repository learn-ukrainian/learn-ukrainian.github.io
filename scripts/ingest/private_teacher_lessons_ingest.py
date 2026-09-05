"""Import a private DOCX lesson log without emitting or persisting extracted files.

The inspected master uses date-prefixed paragraphs for lessons and Word's
``Title`` style for the following reference appendix. Front matter and that
appendix are counted but not attributed to a lesson. Each dated marker remains
one unit, including header-only entries and combined-date headings.

Read only word/document.xml from the ZIP: loading media through a document
converter is unnecessary. Paragraph traversal includes table cells, hyperlinks,
and content controls in document order. Images are not OCR'd. Text and source
paths must never appear in diagnostics, fixtures, or public evidence.

Mirrors ulp_lesson_notes_ingest's textbooks + textbook_sections contract.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from lxml import etree

from scripts.ingest._section_coverage import LessonSection, ensure_section_schema, link_lesson_sections

SOURCE_FILE = "private-teacher-lessons-a"
AUTHOR = "private_teacher_lesson"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DATE_START = re.compile(r"^(\d{2})[./](\d{2})[./](\d{4})(?!\d)")


@dataclass(frozen=True)
class Lesson:
    key: str
    text: str
    body_paragraphs: int

    @property
    def chunk_id(self) -> str:
        digest = hashlib.sha256(self.key.encode()).hexdigest()[:20]
        return f"{SOURCE_FILE}_{digest}"

    @property
    def title(self) -> str:
        return f"Private lesson {self.chunk_id.removeprefix(SOURCE_FILE + '_')}"


@dataclass(frozen=True)
class ParsedDocument:
    lessons: list[Lesson]
    paragraphs: int
    front_matter: int
    appendix: int


def parse_docx(path: Path) -> ParsedDocument:
    """Extract dated units; fail before DB access on ambiguous/invalid structure.

    Counts for front matter and appendix include nonempty paragraphs only.
    Duplicate dates are rejected rather than silently overwriting a lesson.
    """
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    with ZipFile(path) as archive, archive.open("word/document.xml") as document:
        root = etree.parse(document, parser).getroot()
    if root.getroottree().docinfo.doctype:
        raise ValueError("Document type declarations are unsupported")
    body = root.find(f"{W}body")
    if body is None or body.find(f".//{W}txbxContent") is not None:
        raise ValueError("Missing body or unsupported nested text boxes")

    lessons: list[Lesson] = []
    lines: list[str] = []
    current_key: str | None = None
    seen: set[str] = set()
    front = appendix = paragraphs = 0
    ended = False

    def finish() -> None:
        if current_key is not None:
            lessons.append(Lesson(current_key, "\n".join(lines) + "\n", len(lines) - 1))

    for paragraph in body.iter(f"{W}p"):
        paragraphs += 1
        fragments = []
        for node in paragraph.iter():
            if node.tag == f"{W}t":
                fragments.append(node.text or "")
            elif node.tag == f"{W}tab":
                fragments.append("\t")
            elif node.tag in {f"{W}br", f"{W}cr"}:
                fragments.append("\n")
        text = "".join(fragments).strip()
        if not text:
            continue
        in_table = any(parent.tag == f"{W}tbl" for parent in paragraph.iterancestors())
        marker = None if in_table else DATE_START.match(text)
        style = paragraph.find(f"{W}pPr/{W}pStyle")
        if current_key is not None and not in_table and style is not None and style.get(f"{W}val") == "Title":
            ended = True
        if ended:
            if marker:
                raise ValueError("Dated unit after appendix boundary")
            appendix += 1
            continue
        if marker:
            day, month, year = map(int, marker.groups())
            key = date(year, month, day).isoformat()
            if key in seen:
                raise ValueError("Duplicate lesson date")
            seen.add(key)
            finish()
            current_key = key
            lines = [text]
        elif current_key is None:
            front += 1
        else:
            lines.append(text)
    finish()
    if not lessons:
        raise ValueError("No dated lesson units")
    return ParsedDocument(lessons, paragraphs, front, appendix)


def ingest_lessons(conn: sqlite3.Connection, lessons: list[Lesson], *, force: bool = False) -> tuple[int, int]:
    """Atomically insert/reconcile this source only; commit on success.

    Unchanged reruns skip exact matches. Changed or removed units require
    --force, preventing a successful-looking mixture of source revisions.
    """
    if not lessons or len({lesson.chunk_id for lesson in lessons}) != len(lessons):
        raise ValueError("Empty or duplicate lesson set")
    with conn:
        # Lock the source snapshot against concurrent writers before reading it.
        conn.execute("BEGIN IMMEDIATE")
        ensure_section_schema(conn)
        existing = {
            row[0]: row[1:]
            for row in conn.execute(
                "SELECT chunk_id, title, text, author, author_uk, grade, char_count FROM textbooks WHERE source_file = ?",
                (SOURCE_FILE,),
            )
        }
        desired = {
            lesson.chunk_id: (lesson.title, lesson.text, AUTHOR, AUTHOR, "", len(lesson.text))
            for lesson in lessons
        }
        if not force and (existing.keys() - desired.keys() or any(
            existing[key] != desired[key] for key in existing.keys() & desired.keys()
        )):
            raise ValueError("Source changed; use --force to replace this source only")
        if force:
            conn.execute("DELETE FROM textbooks WHERE source_file = ?", (SOURCE_FILE,))
            conn.execute("DELETE FROM textbook_sections WHERE source_file = ?", (SOURCE_FILE,))
            existing = {}
        inserted = 0
        for lesson in lessons:
            if lesson.chunk_id not in existing:
                conn.execute(
                    """INSERT INTO textbooks
                    (chunk_id, title, text, author, author_uk, grade, char_count, source_file)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (lesson.chunk_id, *desired[lesson.chunk_id], SOURCE_FILE),
                )
                inserted += 1
        link_lesson_sections(conn, source_file=SOURCE_FILE, sections=[
            LessonSection(lesson.chunk_id, lesson.title, lesson.key, lesson.text)
            for lesson in lessons
        ])
    return inserted, len(lessons) - inserted


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(
        description="Ingest a private dated DOCX lesson log into an existing sources.db.\n"
        "Use for machine-local corpus intake, never for publishing private text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.ingest.private_teacher_lessons_ingest --docx /private/lessons.docx --dry-run
  .venv/bin/python -m scripts.ingest.private_teacher_lessons_ingest --docx /private/lessons.docx --db /private/sources.db --force
Outputs: counts only; updates textbooks and textbook_sections in the specified DB.
No extracted files, images, or lesson snippets are written or printed.
Exit codes: 0 success; 2 invalid arguments, extraction, validation, or DB failure.
Related: #4850; scripts/ingest/ulp_lesson_notes_ingest.py.
""",
    )
    cli.add_argument("--docx", type=Path, required=True, help="Private input DOCX path; no default (e.g. /private/lessons.docx).")
    cli.add_argument("--db", type=Path, help="Existing sources.db path; required unless --dry-run, no default.")
    cli.add_argument("--dry-run", action="store_true", help="Report parsing counts without DB access (default: false).")
    cli.add_argument("--force", action="store_true", help=f"Atomically replace only {SOURCE_FILE} (default: false).")
    args = cli.parse_args(argv)
    if not args.dry_run and args.db is None:
        cli.error("--db is required unless --dry-run")
    try:
        parsed = parse_docx(args.docx)
        print(f"PARSED: units={len(parsed.lessons)} paragraphs={parsed.paragraphs} "
              f"header_only={sum(lesson.body_paragraphs == 0 for lesson in parsed.lessons)} "
              f"front_matter={parsed.front_matter} appendix={parsed.appendix} "
              f"chars={sum(len(lesson.text) for lesson in parsed.lessons)}")
        if args.dry_run:
            return 0
        conn = sqlite3.connect(args.db.resolve().as_uri() + "?mode=rw", uri=True, timeout=30)
        try:
            query = "SELECT COUNT(*) FROM textbooks WHERE source_file = ?"
            before = conn.execute(query, (SOURCE_FILE,)).fetchone()[0]
            print(f"BEFORE: source_rows={before}")
            inserted, skipped = ingest_lessons(conn, parsed.lessons, force=args.force)
            after = conn.execute(query, (SOURCE_FILE,)).fetchone()[0]
            print(f"AFTER: source_rows={after} inserted={inserted} skipped={skipped}")
        finally:
            conn.close()
    except (OSError, BadZipFile, KeyError, ValueError, etree.XMLSyntaxError, sqlite3.Error) as exc:
        # Exception messages may contain paths, SQL values, or private XML.
        print(f"ERROR: ingest failed ({type(exc).__name__}); no private details emitted.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
