"""Tests for literary metadata restoration in the unified sources DB."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_builder_schema_and_insert_include_literary_metadata(tmp_path, monkeypatch):
    import wiki.build_sources_db as build_sources_db

    gdrive_dir = tmp_path / "gdrive"
    ext_dir = tmp_path / "external"
    textbook_dir = tmp_path / "textbooks"
    ext_dir.mkdir()
    textbook_dir.mkdir()
    _write_jsonl(
        gdrive_dir / "literary_texts" / "sample-work.jsonl",
        [
            {
                "chunk_id": "lit-001",
                "text": "Тут є текст літературного твору.",
                "work": "Літопис Грабянки",
                "author": "Грабянка Г.",
                "year": 1710,
                "genre": "chronicle",
                "language_period": "early-modern",
            }
        ],
    )

    monkeypatch.setattr(build_sources_db, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(build_sources_db, "LOG_DIR", tmp_path / "logs")
    db_path = tmp_path / "sources.db"
    build_sources_db.build(
        db_path=db_path,
        external_dir=ext_dir,
        textbook_dir=textbook_dir,
        gdrive_dir=gdrive_dir,
    )

    conn = sqlite3.connect(str(db_path))
    try:
        columns = {
            row[1]: row[2]
            for row in conn.execute("PRAGMA table_info(literary_texts)")
        }
        assert columns["work"] == "TEXT"
        assert columns["work_id"] == "TEXT"
        assert columns["year"] == "INTEGER"
        assert columns["language_period"] == "TEXT"

        indexes = {
            row[1]
            for row in conn.execute("PRAGMA index_list(literary_texts)")
        }
        assert "idx_literary_period" in indexes
        assert "idx_literary_work_id" in indexes
        assert "idx_literary_period_genre" in indexes

        row = conn.execute(
            """
            SELECT work, work_id, year, genre, language_period
            FROM literary_texts
            WHERE chunk_id = 'lit-001'
            """
        ).fetchone()
    finally:
        conn.close()

    assert row == (
        "Літопис Грабянки",
        "litopys_hrabyanky",
        1710,
        "chronicle",
        "middle_ukrainian",
    )
    assert any((tmp_path / "logs").glob("literary_metadata_restore_*.txt"))


def test_build_literary_row_computes_work_id_and_fallbacks():
    from wiki.sources import build_literary_row

    warnings: list[str] = []
    row = build_literary_row(
        {
            "chunk_id": "lit-002",
            "text": "Рядок без work.",
            "author": "Невідомий",
            "language_period": "modern",
        },
        source_file="fallback-source",
        chunk_index=0,
        warn=warnings.append,
    )

    assert row[5] == "fallback-source"
    assert row[6] == "fallback_source"
    assert row[7] is None
    assert row[8] == ""
    assert row[9] == "modern"
    assert warnings


def test_restore_literary_metadata_is_idempotent_and_preserves_text(tmp_path, monkeypatch):
    import wiki.build_sources_db as build_sources_db
    import wiki.restore_literary_metadata as restore_literary_metadata

    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            CREATE TABLE literary_texts (
                id INTEGER PRIMARY KEY,
                chunk_id TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                text TEXT NOT NULL DEFAULT '',
                source_file TEXT NOT NULL DEFAULT '',
                author TEXT DEFAULT '',
                genre TEXT DEFAULT '',
                char_count INTEGER DEFAULT 0
            );
            """
        )
        conn.execute(
            """
            INSERT INTO literary_texts
            (chunk_id, title, text, source_file, author, genre, char_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("legacy-001", "", "Незмінний текст.", "legacy-work", "Автор", "", 15),
        )
        conn.commit()
    finally:
        conn.close()

    literary_dir = tmp_path / "literary_texts"
    _write_jsonl(
        literary_dir / "legacy-work.jsonl",
        [
            {
                "chunk_id": "legacy-001",
                "text": "Незмінний текст.",
                "work": "Повість временних літ",
                "author": "Нестор",
                "year": 1113,
                "genre": "chronicle",
                "language_period": "old_east_slavic",
            }
        ],
    )

    monkeypatch.setattr(build_sources_db, "LOG_DIR", tmp_path / "logs")

    first = restore_literary_metadata.restore_literary_metadata(
        db_path,
        literary_dir=literary_dir,
    )
    second = restore_literary_metadata.restore_literary_metadata(
        db_path,
        literary_dir=literary_dir,
    )

    assert first["hashes_unchanged"] is True
    assert first["updated_rows"] == 1
    assert second["updated_rows"] == 0
    assert Path(first["report_path"]).exists()

    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            """
            SELECT text, work, work_id, year, genre, language_period
            FROM literary_texts
            WHERE chunk_id = 'legacy-001'
            """
        ).fetchone()
    finally:
        conn.close()

    assert row == (
        "Незмінний текст.",
        "Повість временних літ",
        "povist_vremennykh_lit",
        1113,
        "chronicle",
        "old_east_slavic",
    )


def test_restore_literary_metadata_uses_source_file_for_duplicate_chunk_ids(tmp_path, monkeypatch):
    import wiki.build_sources_db as build_sources_db
    import wiki.restore_literary_metadata as restore_literary_metadata

    db_path = tmp_path / "legacy-duplicates.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            CREATE TABLE literary_texts (
                id INTEGER PRIMARY KEY,
                chunk_id TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                text TEXT NOT NULL DEFAULT '',
                source_file TEXT NOT NULL DEFAULT '',
                author TEXT DEFAULT '',
                genre TEXT DEFAULT '',
                char_count INTEGER DEFAULT 0
            );
            """
        )
        conn.executemany(
            """
            INSERT INTO literary_texts
            (chunk_id, title, text, source_file, author, genre, char_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("dup-001", "", "Текст A.", "work-a", "Автор A", "", 7),
                ("dup-001", "", "Текст B.", "work-b", "Автор B", "", 7),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    literary_dir = tmp_path / "literary_texts"
    _write_jsonl(
        literary_dir / "work-a.jsonl",
        [
            {
                "chunk_id": "dup-001",
                "text": "Текст A.",
                "work": "Твір A",
                "author": "Автор A",
                "year": 1901,
                "genre": "poetry",
                "language_period": "modern",
            }
        ],
    )
    _write_jsonl(
        literary_dir / "work-b.jsonl",
        [
            {
                "chunk_id": "dup-001",
                "text": "Текст B.",
                "work": "Твір B",
                "author": "Автор B",
                "year": 1902,
                "genre": "prose",
                "language_period": "modern",
            }
        ],
    )

    monkeypatch.setattr(build_sources_db, "LOG_DIR", tmp_path / "logs")
    result = restore_literary_metadata.restore_literary_metadata(
        db_path,
        literary_dir=literary_dir,
    )

    assert result["updated_rows"] == 2

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            """
            SELECT source_file, work, work_id, year, genre, language_period
            FROM literary_texts
            ORDER BY source_file
            """
        ).fetchall()
    finally:
        conn.close()

    assert rows == [
        ("work-a", "Твір A", "tvir_a", 1901, "poetry", "modern"),
        ("work-b", "Твір B", "tvir_b", 1902, "prose", "modern"),
    ]
