"""Small receipt-source fixtures; ids copied from the existing receipt tests.

Rows are structural test doubles, not Ukrainian attestation.
"""

import sqlite3

import pytest

from scripts.curriculum.evidence.sources import Sources


@pytest.fixture(autouse=True)
def receipt_sources(tmp_path, monkeypatch, request):
    locations = set(getattr(request.module, "VESUM_LOCATIONS", {}).values())
    locations.update({"487702-487719", "5682038-5682052", "6445807-6445825"})
    vesum_db = tmp_path / "receipt-vesum.db"
    with sqlite3.connect(vesum_db) as conn:
        conn.execute("CREATE TABLE forms_all (id INTEGER PRIMARY KEY, entry_id INTEGER, source_location TEXT)")
        conn.executemany(
            "INSERT INTO forms_all VALUES (?, ?, ?)",
            [(int(loc.split("-")[0]), index + 1, loc) for index, loc in enumerate(sorted(locations))],
        )
    sources_db = tmp_path / "receipt-sources.db"
    with sqlite3.connect(sources_db) as conn:
        conn.executescript("""
            CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, text TEXT);
            INSERT INTO textbooks VALUES (1, 'real-chunk', 'fixture source bytes');
            CREATE TABLE grinchenko (id INTEGER PRIMARY KEY, definition TEXT);
            INSERT INTO grinchenko VALUES (11367, 'fixture source bytes');
            CREATE TABLE sum20_articles (id INTEGER PRIMARY KEY, wordid INTEGER, article_text TEXT);
            INSERT INTO sum20_articles VALUES (1, 2319, 'fixture source bytes');
            CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, status TEXT);
            INSERT INTO ulif_dictua_entries VALUES (18, 'ok');
            CREATE TABLE slovnyk_me_entries (id INTEGER PRIMARY KEY, dictionary_slug TEXT, text TEXT);
            INSERT INTO slovnyk_me_entries VALUES (1, 'vts', 'fixture source bytes');
            INSERT INTO slovnyk_me_entries VALUES (2, 'sum', 'wrong dictionary');
        """)
    original_init = Sources.__init__

    def fixture_init(self, **kwargs):
        kwargs.setdefault("sources_db", sources_db)
        kwargs.setdefault("vesum_db", vesum_db)
        original_init(self, **kwargs)

    monkeypatch.setattr(Sources, "__init__", fixture_init)
    return sources_db, vesum_db
