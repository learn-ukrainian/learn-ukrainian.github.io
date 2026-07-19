#!/usr/bin/env python3
"""Convert ULP lesson-notes .txt into windowed JSONL + re-ingest into sources.db.

School textbooks already live as healthy ~1.5k-char JSONL. ULP seasons were
ingested as one row per lesson (~11k–37k chars). This script:

1. Parses each season with the existing lesson-boundary parser
2. Splits each lesson body into ~target-char windows
3. Writes JSONL under GDrive private_curriculum/ulp/ (or --out-root)
4. Optionally re-ingests into data/sources.db (delete+insert + FTS rebuild)

Copyrighted text stays out of git — only on Drive / local private paths.

Usage::

    .venv/bin/python -m scripts.ingest.ulp_to_jsonl --all --write-jsonl
    .venv/bin/python -m scripts.ingest.ulp_to_jsonl --all --write-jsonl --ingest --force
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ingest import ulp_lesson_notes_ingest as ulp

DEFAULT_TARGET_CHARS = 1500
DEFAULT_OVERLAP_CHARS = 120
DEFAULT_DB = PROJECT_ROOT / "data" / "sources.db"


def resolve_gdrive_root() -> Path | None:
    env = os.environ.get("LU_GDRIVE_DATA")
    if env:
        path = Path(env)
        return path if path.is_dir() else None
    matches = sorted(
        Path.home().glob("Library/CloudStorage/GoogleDrive-*/My Drive/Projects/learn-ukrainian-data")
    )
    return matches[0] if matches else None


def default_out_root() -> Path:
    gdrive = resolve_gdrive_root()
    if gdrive is not None:
        return gdrive / "private_curriculum" / "ulp"
    return PROJECT_ROOT / "data" / "private_curriculum" / "ulp"


def window_text(text: str, *, target: int, overlap: int) -> list[str]:
    """Split text into overlapping windows of ~target characters on line breaks."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= target:
        return [text]
    lines = text.splitlines()
    windows: list[str] = []
    buf: list[str] = []
    size = 0
    for line in lines:
        line_len = len(line) + 1
        if buf and size + line_len > target:
            windows.append("\n".join(buf).strip())
            # overlap: keep tail lines totaling ~overlap chars
            tail: list[str] = []
            tail_size = 0
            for prev in reversed(buf):
                if tail_size + len(prev) + 1 > overlap:
                    break
                tail.insert(0, prev)
                tail_size += len(prev) + 1
            buf = tail
            size = tail_size
        buf.append(line)
        size += line_len
    if buf:
        chunk = "\n".join(buf).strip()
        if chunk:
            windows.append(chunk)
    return windows


def lesson_records(
    book: ulp.BookConfig,
    lessons: Sequence[ulp.Lesson],
    *,
    target: int,
    overlap: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lesson in lessons:
        body = lesson.render()
        windows = window_text(body, target=target, overlap=overlap)
        for index, window in enumerate(windows, start=1):
            chunk_id = f"{book.source_file}_l{lesson.number:04d}_w{index:03d}"
            title = f"Lesson {lesson.number}: {lesson.title}".rstrip(": ") if lesson.title else f"Lesson {lesson.number}"
            if len(windows) > 1:
                title = f"{title} (part {index}/{len(windows)})"
            rows.append(
                {
                    "chunk_id": chunk_id,
                    "text": window,
                    "token_count": len(window.split()),
                    "section_title": title,
                    "section_level": 2,
                    "quality": {"is_clean": True, "clean_ratio": 1.0},
                    "grade": "",
                    "author": ulp.AUTHOR,
                    "author_uk": ulp.AUTHOR_UK,
                    "year": None,
                    "part": f"season-{book.season}",
                    "subject": "lexicon",
                    "trust_tier": 1,
                    "pdf_stem": book.source_file,
                    "source_file": book.source_file,
                    "lesson_number": lesson.number,
                    "window_index": index,
                    "window_count": len(windows),
                }
            )
    return rows


def write_season_jsonl(book: ulp.BookConfig, rows: Sequence[Mapping[str, Any]], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"season-{book.season:02d}" / f"{book.source_file}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def ingest_jsonl(path: Path, *, db_path: Path, force: bool) -> dict[str, int]:
    """Replace textbooks rows for this source_file from JSONL."""
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        return {"deleted": 0, "inserted": 0}
    source_file = str(rows[0]["source_file"])
    conn = sqlite3.connect(db_path)
    try:
        before = conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file = ?", (source_file,)
        ).fetchone()[0]
        if force:
            conn.execute("DELETE FROM textbooks WHERE source_file = ?", (source_file,))
        inserted = 0
        for row in rows:
            if not force:
                exists = conn.execute(
                    "SELECT 1 FROM textbooks WHERE chunk_id = ? LIMIT 1", (row["chunk_id"],)
                ).fetchone()
                if exists:
                    continue
            conn.execute(
                """
                INSERT INTO textbooks (
                    chunk_id, title, text, source_file, grade, author, char_count,
                    parent_section_id, author_uk, subject
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (
                    row["chunk_id"],
                    row["section_title"],
                    row["text"],
                    source_file,
                    row.get("grade") or "",
                    row.get("author") or ulp.AUTHOR,
                    len(row["text"]),
                    row.get("author_uk") or ulp.AUTHOR_UK,
                    row.get("subject") or "lexicon",
                ),
            )
            inserted += 1
        # FTS external-content rebuild for textbooks
        conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES('rebuild')")
        conn.commit()
        after = conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file = ?", (source_file,)
        ).fetchone()[0]
    finally:
        conn.close()
    return {"before": before, "after": after, "inserted": inserted, "deleted": before if force else 0}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--book", choices=sorted(ulp.BOOKS.keys()), action="append")
    p.add_argument("--all", action="store_true")
    p.add_argument("--out-root", type=Path, default=None)
    p.add_argument("--target-chars", type=int, default=DEFAULT_TARGET_CHARS)
    p.add_argument("--overlap-chars", type=int, default=DEFAULT_OVERLAP_CHARS)
    p.add_argument("--write-jsonl", action="store_true")
    p.add_argument("--ingest", action="store_true")
    p.add_argument("--force", action="store_true", help="Replace existing DB rows for source_file")
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    p.add_argument("--dry-run", action="store_true")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.all and not args.book:
        print("error: pass --all or --book", file=sys.stderr)
        return 2
    slugs = list(ulp.BOOKS.keys()) if args.all else list(args.book or [])
    out_root = args.out_root or default_out_root()
    print({"out_root": str(out_root), "books": slugs, "target": args.target_chars}, flush=True)

    for slug in slugs:
        book = ulp.BOOKS[slug]
        txt = ulp.REFERENCES_DIR / book.txt_filename
        if not txt.is_file():
            print(f"missing {txt}", file=sys.stderr)
            return 2
        lessons = ulp.parse_book(txt)
        rows = lesson_records(book, lessons, target=args.target_chars, overlap=args.overlap_chars)
        lengths = sorted(len(r["text"]) for r in rows)
        stats = {
            "book": book.source_file,
            "lessons": len(lessons),
            "windows": len(rows),
            "p50": lengths[len(lengths) // 2] if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "mean": int(sum(lengths) / len(lengths)) if lengths else 0,
        }
        print(stats, flush=True)
        if args.dry_run:
            continue
        if args.write_jsonl:
            path = write_season_jsonl(book, rows, out_root)
            print("wrote", path, flush=True)
            if args.ingest:
                result = ingest_jsonl(path, db_path=args.db, force=args.force)
                print("ingest", book.source_file, result, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
