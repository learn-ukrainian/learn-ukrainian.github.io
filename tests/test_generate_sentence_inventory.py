from __future__ import annotations

import json
import sqlite3

from scripts.audit.generate_sentence_inventory import (
    build_inventory,
    load_daily_lemmas,
    load_daily_targets,
    write_inventory,
)


def _sources_db(tmp_path):
    db = tmp_path / "sources.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT, text TEXT);
        CREATE VIRTUAL TABLE textbooks_fts USING fts5(title, text, content='textbooks', content_rowid='id');
        CREATE TABLE external_articles (id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT, text TEXT, source_file TEXT);
        CREATE VIRTUAL TABLE external_fts USING fts5(title, text, content='external_articles', content_rowid='id');
        INSERT INTO textbooks VALUES (1, 'grade-1-p-4', 'Grade 1', 'Ми живемо в Україні. Наша мова — українська.');
        INSERT INTO textbooks_fts(rowid, title, text) VALUES (1, 'Grade 1', 'Ми живемо в Україні. Наша мова — українська.');
        INSERT INTO external_articles VALUES (1, 'private-local-id', 'Private title', 'Я читаю українською щодня.', 'ulp_youtube');
        INSERT INTO external_fts(rowid, title, text) VALUES (1, 'Private title', 'Я читаю українською щодня.');
        """
    )
    conn.commit()
    conn.close()
    return db


def test_extracts_attributed_textbook_sentence(tmp_path) -> None:
    rows = build_inventory([{"lemma": "Україні", "lemmaId": "ukraini", "cefr": "A1"}], _sources_db(tmp_path))

    assert rows == [
        {
            "lemma": "Україні",
            "lemmaId": "ukraini",
            "sentence": "Ми живемо в Україні.",
            "targetForm": "Україні",
            "cefr": "A1",
            "uses": ["example"],
            "provenance": {
                "source": "textbook",
                "label": "Ukrainian school textbook",
                "locator": "grade-1-p-4",
                "title": "Grade 1",
            },
            "license": {
                "status": "not_openly_licensed",
                "useBasis": "short educational quotation with attribution",
            },
        }
    ]


def test_ulp_provenance_never_exposes_private_locator(tmp_path) -> None:
    rows = build_inventory(
        [{"lemma": "українською", "lemmaId": "ukrainskoiu"}], _sources_db(tmp_path), include_ulp=True
    )

    assert rows[0]["provenance"] == {"source": "ulp", "label": "Ukrainian Lessons Podcast"}
    assert "private-local-id" not in json.dumps(rows, ensure_ascii=False)
    assert "Private title" not in json.dumps(rows, ensure_ascii=False)


def test_daily_lemmas_and_written_schema(tmp_path) -> None:
    pool = tmp_path / "daily.json"
    pool.write_text(
        json.dumps([{"lemma": "дім", "slug": "dim", "cefr": "A1"}, {"lemma": "дім"}, {"lemma": ""}]),
        encoding="utf-8",
    )
    assert load_daily_lemmas(pool) == ["дім"]
    assert load_daily_targets(pool) == [{"lemma": "дім", "lemmaId": "dim", "cefr": "A1"}]
    out = tmp_path / "inventory.json"
    write_inventory([], out)
    assert json.loads(out.read_text(encoding="utf-8")) == {
        "schema": "atlas-sentence-inventory",
        "schemaVersion": 1,
        "rows": [],
    }
