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
        {"chunk_id": f"{slug}_s{i:04d}", "section_title": "§ 1. Хімія",
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
    char_counts = conn.execute(
        "SELECT char_count, length(text) FROM textbooks WHERE source_file=? ORDER BY id",
        (slug,),
    ).fetchall()
    assert char_counts == [(len(text), len(text)) for text in (
        "Хімія фотосинтез рівняння приклад 0",
        "Хімія фотосинтез рівняння приклад 1",
        "Хімія фотосинтез рівняння приклад 2",
    )]
    sections = conn.execute(
        "SELECT section_title, chunk_count FROM textbook_sections WHERE source_file=?",
        (slug,),
    ).fetchall()
    assert sections == [("§ 1. Хімія", 3)]
    linked = conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE source_file=? AND parent_section_id IS NOT NULL",
        (slug,),
    ).fetchone()[0]
    assert linked == 3
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
    assert conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name='textbook_sections'"
    ).fetchone()[0] == 0
    conn.close()


def test_chunks_root_override_is_threaded_without_using_default(fixture_env, tmp_path):
    db, slug = fixture_env
    canonical = tmp_path / "canonical-drive" / "textbook_chunks"
    jsonl = canonical / "grade-09" / f"{slug}.jsonl"
    jsonl.parent.mkdir(parents=True)
    jsonl.write_text(
        json.dumps(
            {
                "chunk_id": "canonical_s0000",
                "section_title": "§ 1. Канонічне джерело",
                "text": "Канонічний текст фотосинтезу для перевірки.",
                "author": "popel",
                "author_uk": None,
                "grade": 9,
                "token_count": 1,
            },
            ensure_ascii=False,
        )
        + "\n",
    )
    assert iti.find_jsonl(slug, chunks_root=canonical) == jsonl
    assert iti.ingest([slug], db_path=db, dry_run=False, chunks_root=canonical) == {slug: 1}
    conn = sqlite3.connect(str(db))
    assert conn.execute("SELECT chunk_id FROM textbooks").fetchone()[0] == "canonical_s0000"
    conn.close()


def test_section_replacement_preserves_other_sources_and_fts(fixture_env):
    db, slug = fixture_env
    iti.ingest([slug], db_path=db, dry_run=False)
    conn = sqlite3.connect(str(db))
    conn.execute(
        """INSERT INTO textbooks
           (chunk_id, title, text, source_file, subject, grade, author, author_uk, char_count)
           VALUES ('other_s0000', 'Other', 'інший корпус', 'other-source', 'other', '9', '', '', 12)"""
    )
    other_id = conn.execute("SELECT id FROM textbooks WHERE chunk_id='other_s0000'").fetchone()[0]
    conn.execute(
        """INSERT INTO textbook_sections
           (source_file, grade, section_title, section_number, page_start, page_end, chunk_count, full_text)
           VALUES ('other-source', 9, '§ other', 'other', 1, 1, 1, 'інший корпус')"""
    )
    other_section = conn.execute(
        "SELECT section_id FROM textbook_sections WHERE source_file='other-source'"
    ).fetchone()[0]
    conn.execute("UPDATE textbooks SET parent_section_id=? WHERE id=?", (other_section, other_id))
    conn.commit()
    conn.close()

    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    entries = [
        {
            "chunk_id": f"replacement_s{i:04d}",
            "section_title": "§ 2. Оновлена тема",
            "text": f"Оновлений хлорофіл рядок {i}.",
            "author": "popel",
            "author_uk": None,
            "grade": 9,
            "token_count": 999,
        }
        for i in range(2)
    ]
    jsonl.write_text(
        "\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + "\n",
        encoding="utf-8",
    )
    iti.ingest([slug], db_path=db, dry_run=False)

    conn = sqlite3.connect(str(db))
    assert conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE source_file=?", (slug,)
    ).fetchone()[0] == 2
    assert conn.execute(
        "SELECT section_title FROM textbook_sections WHERE source_file=?", (slug,)
    ).fetchall() == [("§ 2. Оновлена тема",)]
    assert conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE source_file=? AND parent_section_id IS NOT NULL",
        (slug,),
    ).fetchone()[0] == 2
    assert conn.execute(
        "SELECT section_title FROM textbook_sections WHERE source_file='other-source'"
    ).fetchall() == [("§ other",)]
    assert conn.execute(
        "SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'оновлений'"
    ).fetchone()[0] == 2
    assert conn.execute(
        "SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'хлорофіл'"
    ).fetchone()[0] == 2
    assert conn.execute(
        "SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'фотосинтез'"
    ).fetchone()[0] == 0
    conn.close()


def test_failure_after_replacement_rolls_back_rows_sections_and_fts(fixture_env, monkeypatch):
    db, slug = fixture_env
    iti.ingest([slug], db_path=db, dry_run=False)
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    jsonl.write_text(
        json.dumps(
            {
                "chunk_id": "failed_s0000",
                "section_title": "§ 9. Не застосовано",
                "text": "Нова лексема, яка не має залишитися.",
                "author": "popel",
                "author_uk": None,
                "grade": 9,
                "token_count": 1,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    def fail_fts(*_args, **_kwargs):
        raise iti.IngestError("forced FTS failure")

    monkeypatch.setattr(iti, "_fts_source_evidence", fail_fts)
    with pytest.raises(iti.IngestError, match="forced FTS failure"):
        iti.ingest([slug], db_path=db, dry_run=False)

    conn = sqlite3.connect(str(db))
    assert conn.execute(
        "SELECT chunk_id FROM textbooks WHERE source_file=?", (slug,)
    ).fetchall() == [(f"{slug}_s0000",), (f"{slug}_s0001",), (f"{slug}_s0002",)]
    assert conn.execute(
        "SELECT section_title FROM textbook_sections WHERE source_file=?", (slug,)
    ).fetchall() == [("§ 1. Хімія",)]
    assert conn.execute(
        "SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'фотосинтез'"
    ).fetchone()[0] == 3
    conn.close()


def test_unlinked_school_rows_fail_closed(fixture_env):
    db, slug = fixture_env
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    entries = [
        {
            "chunk_id": f"unlinked_s{i:04d}",
            "section_title": f"Сторінка {i + 1}",
            "text": "Текст без заголовка, який не можна невидимо прийняти.",
            "author": "popel",
            "author_uk": None,
            "grade": 9,
        }
        for i in range(2)
    ]
    jsonl.write_text(
        "\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(iti.IngestError, match="remain unlinked"):
        iti.ingest([slug], db_path=db, dry_run=False)
    conn = sqlite3.connect(str(db))
    assert conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0] == 0
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
