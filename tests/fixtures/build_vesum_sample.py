#!/usr/bin/env python3
"""Build the small VESUM sqlite fixture for heritage-classifier CI coverage."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(__file__).with_name("vesum_sample.db")

LEMMA_FIXTURE_SET = (
    "бути",
    "автобус",
    "журналіст",
    "книга",
    "білий",
    "гарний",
    "адреса",
    "банкір",
    "вельми",
    "гетьман",
    "десятина",
    "вчителька",
    "учителька",
    "кобіта",
    "глагол",
)

SCHEMA_SQL = """
CREATE TABLE forms (
    word_form TEXT NOT NULL,
    lemma TEXT NOT NULL,
    tags TEXT NOT NULL,
    pos TEXT NOT NULL
);
"""


def _default_source_db() -> Path:
    worktree_db = PROJECT_ROOT / "data" / "vesum.db"
    if worktree_db.exists():
        return worktree_db

    parts = PROJECT_ROOT.parts
    if ".worktrees" in parts:
        main_root = Path(*parts[: parts.index(".worktrees")])
        main_db = main_root / "data" / "vesum.db"
        if main_db.exists():
            return main_db

    return worktree_db


def _placeholders(count: int) -> str:
    return ",".join("?" for _ in range(count))


def _extract_rows(source_conn: sqlite3.Connection) -> list[tuple[str, str, str, str]]:
    lemma_placeholders = _placeholders(len(LEMMA_FIXTURE_SET))
    rows = source_conn.execute(
        f"""
        SELECT word_form, lemma, tags, pos
        FROM forms
        WHERE lemma IN ({lemma_placeholders})
            OR word_form IN ({lemma_placeholders})
        ORDER BY lemma, word_form, pos, tags
        """,
        (*LEMMA_FIXTURE_SET, *LEMMA_FIXTURE_SET),
    ).fetchall()

    deduped = {
        (row["word_form"], row["lemma"], row["tags"], row["pos"])
        for row in rows
    }
    return sorted(deduped, key=lambda row: (row[1], row[0], row[3], row[2]))


def build(
    db_path: Path = DB_PATH,
    source_db: Path | None = None,
) -> Path:
    """Rebuild the fixture from the local full VESUM database."""
    source = source_db or _default_source_db()
    if not source.exists():
        raise FileNotFoundError(f"local VESUM database not found: {source}")

    if db_path.exists():
        db_path.unlink()

    source_conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    source_conn.row_factory = sqlite3.Row
    try:
        rows = _extract_rows(source_conn)
    finally:
        source_conn.close()

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(SCHEMA_SQL)
        conn.executemany(
            "INSERT INTO forms(word_form, lemma, tags, pos) VALUES (?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-db", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=DB_PATH)
    args = parser.parse_args()

    print(build(db_path=args.output, source_db=args.source_db))


if __name__ == "__main__":
    main()
