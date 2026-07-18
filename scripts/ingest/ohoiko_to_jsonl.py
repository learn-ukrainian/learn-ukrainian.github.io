#!/usr/bin/env python3
"""Export Ohoiko books to entry-level private JSONL on GDrive + re-ingest.

- 1000 words: one JSONL row per numbered entry (already healthy in DB)
- 500 verbs: one JSONL row per verb; optional body trim for retrieval

Usage::

    .venv/bin/python -m scripts.ingest.ohoiko_to_jsonl --all --write-jsonl --ingest --force
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ingest import ohoiko_books_ingest as books
from scripts.ingest import ohoiko_verbs_ingest as verbs

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
        return gdrive / "private_curriculum" / "ohoiko"
    return PROJECT_ROOT / "data" / "private_curriculum" / "ohoiko"


def words_rows() -> list[dict[str, Any]]:
    cfg = books.BOOKS["1000-words"]
    path = books.REFERENCES_DIR / cfg.txt_filename
    entries = books.parse_book(path)
    rows: list[dict[str, Any]] = []
    for entry in entries:
        text_parts = [f"{entry.number}. {entry.headword}"]
        if entry.english:
            text_parts[0] += f"  {entry.english}"
        if entry.body_lines:
            text_parts.extend(entry.body_lines)
        text = "\n".join(text_parts).strip() + "\n"
        rows.append(
            {
                "chunk_id": f"{cfg.source_file}_e{entry.number:04d}",
                "text": text,
                "token_count": len(text.split()),
                "section_title": entry.headword,
                "section_level": 2,
                "quality": {"is_clean": True, "clean_ratio": 1.0},
                "grade": "",
                "author": cfg.author,
                "author_uk": cfg.author_uk,
                "year": 2023,
                "part": "1000-words",
                "subject": "lexicon",
                "trust_tier": 1,
                "pdf_stem": cfg.source_file,
                "source_file": cfg.source_file,
                "entry_number": entry.number,
                "english": entry.english,
            }
        )
    return rows


def verbs_rows() -> list[dict[str, Any]]:
    path = verbs.REFERENCES_DIR / verbs.TXT_FILENAME
    parsed = verbs.parse_book(path)
    rows: list[dict[str, Any]] = []
    for verb in parsed:
        # Prefer headword + English + a few examples; drop huge conjugation tables for RAG.
        body = list(verb.body_lines)
        head = verb.headword_line or (body[0] if body else f"verb {verb.number}")
        eng = ""
        examples: list[str] = []
        for line in body[1:]:
            s = line.strip()
            if not s:
                continue
            if not eng and s.lower().startswith("to "):
                eng = s.split("  ")[0].strip()
                continue
            # example lines often have UK + EN side by side
            if any("\u0400" <= ch <= "\u04ff" for ch in s) and len(s) > 20:
                examples.append(s)
            if len(examples) >= 4:
                break
        text_lines = [head.strip()]
        if eng:
            text_lines.append(eng)
        text_lines.extend(examples)
        text = "\n".join(text_lines).strip() + "\n"
        # keep full body if trimmed too hard
        if len(text) < 80 and body:
            text = "\n".join(body[:40]).strip() + "\n"
        rows.append(
            {
                "chunk_id": f"{verbs.SOURCE_FILE}_e{verb.number:04d}",
                "text": text,
                "token_count": len(text.split()),
                "section_title": head.strip()[:120],
                "section_level": 2,
                "quality": {"is_clean": True, "clean_ratio": 1.0},
                "grade": "",
                "author": verbs.AUTHOR,
                "author_uk": verbs.AUTHOR_UK,
                "year": None,
                "part": "500-verbs",
                "subject": "lexicon",
                "trust_tier": 1,
                "pdf_stem": verbs.SOURCE_FILE,
                "source_file": verbs.SOURCE_FILE,
                "entry_number": verb.number,
                "english": eng,
            }
        )
    return rows


def write_jsonl(path: Path, rows: Sequence[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def ingest_jsonl(path: Path, *, db_path: Path, force: bool) -> dict[str, int]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        return {"inserted": 0}
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
                    row.get("author") or "Anna Ohoiko",
                    len(row["text"]),
                    row.get("author_uk") or "Анна Огойко",
                    row.get("subject") or "lexicon",
                ),
            )
            inserted += 1
        conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES('rebuild')")
        conn.commit()
        after = conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file = ?", (source_file,)
        ).fetchone()[0]
    finally:
        conn.close()
    return {"before": before, "after": after, "inserted": inserted}


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-root", type=Path, default=None)
    p.add_argument("--write-jsonl", action="store_true")
    p.add_argument("--ingest", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    p.add_argument("--all", action="store_true")
    p.add_argument("--words", action="store_true")
    p.add_argument("--verbs", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    if not (args.all or args.words or args.verbs):
        print("error: pass --all or --words/--verbs", file=sys.stderr)
        return 2
    out_root = args.out_root or default_out_root()
    jobs: list[tuple[str, list[dict[str, Any]]]] = []
    if args.all or args.words:
        jobs.append(("1000-words-2nd-ed.jsonl", words_rows()))
    if args.all or args.verbs:
        jobs.append(("500-verbs.jsonl", verbs_rows()))

    for name, rows in jobs:
        lengths = sorted(len(r["text"]) for r in rows)
        print(
            {
                "file": name,
                "rows": len(rows),
                "p50": lengths[len(lengths) // 2] if lengths else 0,
                "max": max(lengths) if lengths else 0,
                "mean": int(sum(lengths) / len(lengths)) if lengths else 0,
            },
            flush=True,
        )
        if args.dry_run:
            continue
        if args.write_jsonl:
            path = write_jsonl(out_root / name, rows)
            print("wrote", path, flush=True)
            if args.ingest:
                print("ingest", ingest_jsonl(path, db_path=args.db, force=args.force), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
