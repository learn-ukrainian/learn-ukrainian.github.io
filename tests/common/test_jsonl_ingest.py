"""JSONL ingestion preserves Unicode separators inside stored string values."""

import json
import sqlite3

import pytest

from scripts.ingest import ohoiko_to_jsonl, ulp_to_jsonl


@pytest.mark.parametrize("ingester", [ohoiko_to_jsonl, ulp_to_jsonl], ids=["ohoiko", "ulp"])
@pytest.mark.parametrize("sep", ["\u0085", "\u2028", "\u2029"], ids=["NEL", "LS", "PS"])
def test_ingest_jsonl_preserves_unicode_separators(tmp_path, ingester, sep):
    db = tmp_path / "fixture.db"
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT, text TEXT, "
            "source_file TEXT, grade TEXT, author TEXT, char_count INTEGER, parent_section_id TEXT, "
            "author_uk TEXT, subject TEXT)"
        )
        conn.execute("CREATE VIRTUAL TABLE textbooks_fts USING fts5(text, content='textbooks', content_rowid='id')")
    rows = [
        {"chunk_id": f"c{i}", "source_file": "fixture", "section_title": f"title{sep}{i}", "text": f"a{sep}b{i}"}
        for i in range(2)
    ]
    path = tmp_path / "input.jsonl"
    path.write_text("\r\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\r\n", encoding="utf-8")

    result = ingester.ingest_jsonl(path, db_path=db, force=False)

    assert result["inserted"] == 2
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT title, text FROM textbooks ORDER BY chunk_id").fetchall() == [
            (row["section_title"], row["text"]) for row in rows
        ]
