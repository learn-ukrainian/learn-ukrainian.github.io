"""Small receipt-source fixtures; ids copied from the existing receipt tests.

Rows are structural test doubles, not Ukrainian attestation.
"""

import sqlite3
from collections.abc import Iterable
from pathlib import Path

import pytest

from scripts.curriculum.evidence.sources import Sources


def receipt_source_paths(root: Path, locations: Iterable[str] = (), *, records: Iterable[dict] = (), record_locations=None) -> tuple[Path, Path]:
    """Build tiny SQLite stores for real citation resolution, without host data."""
    locations = set(locations)
    locations.update({"487702-487719", "5682038-5682052", "6445807-6445825"})
    vesum_db = root / "receipt-vesum.db"
    with sqlite3.connect(vesum_db) as conn:
        conn.executescript("""
            CREATE TABLE forms_all (id INTEGER PRIMARY KEY, entry_id INTEGER, source_location TEXT,
                word_form TEXT, lemma TEXT, pos TEXT, tags TEXT);
            CREATE VIEW forms AS SELECT word_form, lemma, pos, tags FROM forms_all;
        """)
        spellings = {
            "487702-487719": {"one", "two", "брат", "брата", "брату"},
            "5682038-5682052": {"слово", "слова"},
            "6445807-6445825": {"хліб", "хліба", "хлібу"},
        }
        lemmas = {}
        for record in records:
            loc = (record_locations or {}).get(record["id"])
            if loc:
                spellings.setdefault(loc, set()).update(form["form"] for form in record["forms"])
                lemmas[loc] = record["lemma"]
        for index, loc in enumerate(sorted(locations)):
            for offset, form in enumerate(sorted(spellings.get(loc, {"fixture"}))):
                conn.execute("INSERT INTO forms_all VALUES (?, ?, ?, ?, ?, 'noun', 'noun')",
                             (int(loc.split("-")[0]) + offset, index + 1, loc, form, lemmas.get(loc, "fixture-lemma")))
    sources_db = root / "receipt-sources.db"
    with sqlite3.connect(sources_db) as conn:
        conn.executescript("""
            CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, text TEXT);
            INSERT INTO textbooks VALUES (1, 'real-chunk', 'one two fixture source bytes');
            CREATE TABLE grinchenko (id INTEGER PRIMARY KEY, definition TEXT, word TEXT DEFAULT 'one', lemma TEXT DEFAULT 'two');
            INSERT INTO grinchenko (id, definition) VALUES (11367, 'one two fixture source bytes');
            CREATE TABLE sum20_articles (id INTEGER PRIMARY KEY, wordid INTEGER, article_text TEXT, headword TEXT DEFAULT 'one', lemma TEXT DEFAULT 'two');
            INSERT INTO sum20_articles (id, wordid, article_text) VALUES (1, 2319, 'one two fixture source bytes');
            CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, status TEXT, canonical_headword TEXT, lemma TEXT DEFAULT 'two');
            INSERT INTO ulif_dictua_entries (id, status, canonical_headword) VALUES (18, 'ok', 'one');
            CREATE TABLE slovnyk_me_entries (id INTEGER PRIMARY KEY, dictionary_slug TEXT, text TEXT, word TEXT DEFAULT 'one', lemma TEXT DEFAULT 'two');
            INSERT INTO slovnyk_me_entries (id, dictionary_slug, text) VALUES (1, 'vts', 'one two fixture source bytes');
            INSERT INTO slovnyk_me_entries (id, dictionary_slug, text) VALUES (2, 'sum', 'wrong dictionary');
        """)
    return sources_db, vesum_db


@pytest.fixture(autouse=True)
def receipt_sources(tmp_path, monkeypatch, request):
    locations = getattr(request.module, "VESUM_LOCATIONS", {})
    records = [value for value in vars(request.module).values()
               if isinstance(value, dict) and "id" in value and "lemma" in value and "forms" in value]
    sources_db, vesum_db = receipt_source_paths(tmp_path, locations.values(), records=records, record_locations=locations)
    original_init = Sources.__init__

    def fixture_init(self, **kwargs):
        kwargs.setdefault("sources_db", sources_db)
        kwargs.setdefault("vesum_db", vesum_db)
        original_init(self, **kwargs)

    monkeypatch.setattr(Sources, "__init__", fixture_init)
    return sources_db, vesum_db
