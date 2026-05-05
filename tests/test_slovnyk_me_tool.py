"""Smoke tests for #1715 slovnyk.me and heritage MCP backing functions."""

import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))


@pytest.fixture()
def slovnyk_sources_db(tmp_path, monkeypatch):
    from wiki.slovnyk_me import db_row_values, ensure_slovnyk_me_schema, normalize_word

    from wiki import sources_db as sdb

    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(str(db_path))
    ensure_slovnyk_me_schema(conn)
    conn.executescript(
        """
        CREATE TABLE grinchenko (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT ''
        );
        CREATE INDEX idx_grinchenko_word ON grinchenko(word COLLATE NOCASE);

        CREATE TABLE style_guide (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            section TEXT DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT ''
        );
        CREATE INDEX idx_style_word ON style_guide(word COLLATE NOCASE);

        CREATE TABLE esum_etymology_meta (
            id INTEGER PRIMARY KEY,
            lemma TEXT NOT NULL,
            vol INTEGER NOT NULL,
            page INTEGER NOT NULL,
            entry_hash TEXT NOT NULL DEFAULT '',
            etymology_text TEXT NOT NULL DEFAULT '',
            cognates TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT 'ЕСУМ'
        );
        CREATE VIRTUAL TABLE esum_etymology USING fts5(
            lemma,
            etymology_text,
            cognates,
            vol UNINDEXED,
            page UNINDEXED,
            content='esum_etymology_meta',
            content_rowid='id',
            tokenize='unicode61'
        );
        """
    )

    rows = [
        {
            "query": "блакитний",
            "word": "блакитний",
            "normalized_word": normalize_word("блакитний"),
            "dictionary_slug": "newsum",
            "dictionary_label": "Словник української мови у 20 томах (СУМ-20)",
            "source_type": "modern_explanatory",
            "source_url": "https://slovnyk.me/dict/newsum/блакитний",
            "title": "блакитний — СУМ-20",
            "snippet": "БЛАКИ́ТНИЙ, а, е. Небесно-голубого кольору; голубий.",
            "text": "БЛАКИ́ТНИЙ, а, е. Небесно-голубого кольору; голубий.",
            "is_modern": True,
            "is_dialect": False,
            "is_russianism": False,
            "sovietization_risk": 0,
            "sovietization_keywords": "",
            "fetched_at": "2026-05-05T00:00:00+00:00",
        },
        {
            "query": "кобета",
            "word": "кобіта",
            "normalized_word": normalize_word("кобіта"),
            "dictionary_slug": "slang_lviv",
            "dictionary_label": "Лексикон львівський: поважно і на жарт",
            "source_type": "heritage_or_regional",
            "source_url": "https://slovnyk.me/dict/slang_lviv/кобіта",
            "title": "кобіта — Лексикон львівський",
            "snippet": "кобі́та (кубі́та) жінка; дівчина (м, ср, ст).",
            "text": "кобі́та (кубі́та) жінка; дівчина (м, ср, ст).",
            "is_modern": False,
            "is_dialect": True,
            "is_russianism": False,
            "sovietization_risk": 0,
            "sovietization_keywords": "",
            "fetched_at": "2026-05-05T00:00:00+00:00",
        },
        {
            "query": "гаразд",
            "word": "гаразд",
            "normalized_word": normalize_word("гаразд"),
            "dictionary_slug": "newsum",
            "dictionary_label": "Словник української мови у 20 томах (СУМ-20)",
            "source_type": "modern_explanatory",
            "source_url": "https://slovnyk.me/dict/newsum/гаразд",
            "title": "гаразд — СУМ-20",
            "snippet": "ГАРА́ЗД. Уживається для вираження згоди; добре.",
            "text": "ГАРА́ЗД. Уживається для вираження згоди; добре.",
            "is_modern": True,
            "is_dialect": False,
            "is_russianism": False,
            "sovietization_risk": 0,
            "sovietization_keywords": "",
            "fetched_at": "2026-05-05T00:00:00+00:00",
        },
        {
            "query": "гаразд",
            "word": "гаразд",
            "normalized_word": normalize_word("гаразд"),
            "dictionary_slug": "hrinchenko",
            "dictionary_label": "Словник української мови Грінченка",
            "source_type": "dictionary",
            "source_url": "https://slovnyk.me/dict/hrinchenko/гаразд",
            "title": "гаразд — Грінченко on slovnyk.me",
            "snippet": "Duplicate copy that should be blocked by search_slovnyk_me.",
            "text": "Duplicate copy that should be blocked by search_slovnyk_me.",
            "is_modern": False,
            "is_dialect": False,
            "is_russianism": False,
            "sovietization_risk": 0,
            "sovietization_keywords": "",
            "fetched_at": "2026-05-05T00:00:00+00:00",
        },
        {
            "query": "радянський",
            "word": "радянський",
            "normalized_word": normalize_word("радянський"),
            "dictionary_slug": "newsum",
            "dictionary_label": "Словник української мови у 20 томах (СУМ-20)",
            "source_type": "modern_explanatory",
            "source_url": "https://slovnyk.me/dict/newsum/радянський",
            "title": "радянський — СУМ-20",
            "snippet": "РАДЯ́НСЬКИЙ. Стос. до рад, СРСР.",
            "text": "РАДЯ́НСЬКИЙ. Стос. до рад, СРСР.",
            "is_modern": True,
            "is_dialect": False,
            "is_russianism": False,
            "sovietization_risk": 1,
            "sovietization_keywords": "радянськ,срср",
            "fetched_at": "2026-05-05T00:00:00+00:00",
        },
    ]
    conn.executemany(
        """
        INSERT INTO slovnyk_me_entries (
            query, word, normalized_word, dictionary_slug, dictionary_label,
            source_type, source_url, title, snippet, text, is_modern,
            is_dialect, is_russianism, sovietization_risk,
            sovietization_keywords, fetched_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [db_row_values(row) for row in rows],
    )
    conn.execute(
        "INSERT INTO grinchenko (word, definition, source) VALUES (?, ?, ?)",
        (
            "гаразд I",
            "Гаразд нар. 1) Ладно, хорошо. 2) Хорошо.",
            "Грінченко",
        ),
    )
    conn.execute(
        """
        INSERT INTO esum_etymology_meta
            (lemma, vol, page, entry_hash, etymology_text, cognates, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "гаразд",
            1,
            470,
            "garage-test",
            "гаразд — псл. основа, споріднене з гараздувати.",
            '["псл."]',
            "ЕСУМ vol. 1",
        ),
    )
    conn.execute(
        """
        INSERT INTO esum_etymology(rowid, lemma, etymology_text, cognates, vol, page)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "гаразд",
            "гаразд — псл. основа, споріднене з гараздувати.",
            '["псл."]',
            1,
            470,
        ),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(sdb, "SOURCES_DB_PATH", db_path)
    monkeypatch.setattr(sdb, "_conn", None)
    yield db_path
    if sdb._conn is not None:
        sdb._conn.close()
        monkeypatch.setattr(sdb, "_conn", None)


def test_search_slovnyk_me_blakytnyi_returns_modern_sum20_row(slovnyk_sources_db):
    from wiki.sources_db import search_slovnyk_me

    hits = search_slovnyk_me("блакитний", live=False)

    assert hits
    assert any(hit["dictionary_slug"] == "newsum" and hit["is_modern"] for hit in hits)


def test_search_slovnyk_me_kobeta_returns_dialect_not_russianism(slovnyk_sources_db):
    from wiki.sources_db import search_slovnyk_me

    hits = search_slovnyk_me("кобета", live=False)

    assert hits
    assert any(hit["word"] == "кобіта" and hit["is_dialect"] for hit in hits)
    assert not any(hit["is_russianism"] for hit in hits)


def test_search_heritage_harazd_merges_grinchenko_slovnyk_and_esum(slovnyk_sources_db):
    from wiki.sources_db import search_heritage

    hits = search_heritage("гаразд", include_live_slovnyk=False)
    families = {hit["source_family"] for hit in hits}

    assert {"grinchenko", "slovnyk_me", "esum"}.issubset(families)
    assert all(
        hit["is_authentic_ukrainian"]
        for hit in hits
        if hit["source_family"] in {"grinchenko", "slovnyk_me", "esum"}
    )


def test_search_slovnyk_me_blocks_duplicate_local_dictionary_rows(slovnyk_sources_db):
    from wiki.sources_db import search_slovnyk_me

    assert search_slovnyk_me("гаразд", dictionaries=["hrinchenko"], live=False) == []

    hits = search_slovnyk_me("гаразд", live=False)

    assert hits
    assert not any(hit["dictionary_slug"] == "hrinchenko" for hit in hits)


def test_search_heritage_demotes_slovnyk_sovietization_risk(slovnyk_sources_db):
    from wiki.sources_db import search_heritage

    hits = search_heritage("радянський", include_live_slovnyk=False)
    slovnyk_hit = next(hit for hit in hits if hit["source_family"] == "slovnyk_me")

    assert slovnyk_hit["sovietization_risk"] == 1
    assert slovnyk_hit["score"] == 77.0
