"""Tests for the incremental textbook ingest (#4593 wave-1 path)."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from ingest import incremental_textbook_ingest as iti

SCHEMA = """
CREATE TABLE textbooks (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT,
    title TEXT,
    text TEXT,
    source_file TEXT,
    subject TEXT,
    grade TEXT,
    author TEXT,
    author_uk TEXT DEFAULT '',
    char_count INTEGER
);
CREATE VIRTUAL TABLE textbooks_fts USING fts5(
    title, text, content='textbooks', content_rowid='id', tokenize='unicode61'
);
CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
    INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;
"""


@pytest.fixture()
def fixture_env(tmp_path, monkeypatch):
    db = tmp_path / "sources.db"
    conn = sqlite3.connect(str(db))
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

    chunks = tmp_path / "textbook_chunks"
    monkeypatch.setattr(iti, "CHUNKS_DIR", chunks)
    slug = "9-klas-khimiya-popel-2017"
    jsonl = chunks / "grade-09" / f"{slug}.jsonl"
    jsonl.parent.mkdir(parents=True)
    entries = [
        {"chunk_id": f"{slug}_s{i:04d}", "section_title": f"Сторінка {i}",
         "text": f"Хімія фотосинтез рівняння приклад {i}",
         "author": "popel", "author_uk": None, "grade": 9, "token_count": 10}
        for i in range(3)
    ]
    jsonl.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in entries))
    return db, slug


def test_ingest_inserts_with_subject_and_author_uk(fixture_env):
    db, slug = fixture_env
    counts = iti.ingest([slug], db_path=db, dry_run=False)
    assert counts == {slug: 3}
    conn = sqlite3.connect(str(db))
    rows = conn.execute(
        "SELECT subject, author_uk FROM textbooks WHERE source_file=?", (slug,)
    ).fetchall()
    assert rows == [("khimiya", "Попель")] * 3
    fts = conn.execute(
        "SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'фотосинтез'"
    ).fetchone()[0]
    assert fts == 3
    conn.close()


def test_reingest_is_idempotent(fixture_env):
    db, slug = fixture_env
    iti.ingest([slug], db_path=db, dry_run=False)
    iti.ingest([slug], db_path=db, dry_run=False)
    conn = sqlite3.connect(str(db))
    n = conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE source_file=?", (slug,)
    ).fetchone()[0]
    fts = conn.execute(
        "SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'фотосинтез'"
    ).fetchone()[0]
    assert (n, fts) == (3, 3), "delete+insert+fts-rebuild must not duplicate"
    conn.close()


def test_dry_run_rolls_back(fixture_env):
    db, slug = fixture_env
    iti.ingest([slug], db_path=db, dry_run=True)
    conn = sqlite3.connect(str(db))
    n = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
    assert n == 0
    conn.close()


def test_unmapped_author_refuses(fixture_env, tmp_path):
    db, _ = fixture_env
    slug = "9-klas-khimiya-nemaie-2017"
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    jsonl.write_text(json.dumps(
        {"chunk_id": "x", "text": "т", "author": "nemaie", "author_uk": None},
        ensure_ascii=False))
    with pytest.raises(iti.IngestError, match="no canonical Cyrillic form"):
        iti.ingest([slug], db_path=db, dry_run=True)


def test_missing_jsonl_refuses(fixture_env):
    db, _ = fixture_env
    with pytest.raises(iti.IngestError, match="chunk file missing"):
        iti.ingest(["5-klas-informatyka-ryvkind-2022"], db_path=db, dry_run=True)


def test_wave1_slugs_all_have_author_mappings():
    for slug in iti.WAVE1_SLUGS:
        author = slug.split("-")[-2]
        assert author.lower() in iti.AUTHOR_UK, slug
