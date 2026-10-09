"""Smoke tests for #1715 slovnyk.me and heritage MCP backing functions."""

import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))


@pytest.fixture()
def slovnyk_sources_db(tmp_path, monkeypatch):
    from wiki import sources_db as sdb
    from wiki.slovnyk_me import db_row_values, ensure_slovnyk_me_schema, normalize_word

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


def test_parse_entry_html_accepts_corrected_dictionary_article_id():
    from wiki.slovnyk_me import parse_entry_html

    row = parse_entry_html(
        """
        <html>
          <head>
            <title>вода — тест</title>
            <link rel="canonical" href="https://slovnyk.me/dict/synonyms/вода">
          </head>
          <body>
            <section id="dictionary-article">
              <article>
                <h1>вода</h1>
                <p>вода (газована) пиття, напій; П. багатослів'я.</p>
              </article>
            </section>
          </body>
        </html>
        """,
        query="вода",
        word="вода",
        dict_slug="synonyms",
        url="https://slovnyk.me/dict/synonyms/вода",
    )

    assert row is not None
    assert row["word"] == "вода"
    assert "пиття" in row["text"]


@pytest.mark.parametrize(
    ("cell", "article", "expected"),
    [
        ("C1 span fragmentation", "<span>лі</span><span>с</span><span>т</span>", "слово ліст"),
        ("C2 underline", "до<u>б</u>ре", "слово добре"),
        ("C3 superscript and punctuation", "[кни<sup>га</sup>]—так!", "слово [книга]—так!"),
        ("C4 combining acute across nodes", "а<span>\u0301</span>б", "слово а\u0301б"),
        ("C5 supplied interword space fragment", "<span>білий</span> <span>кіт</span>", "слово білий кіт"),
        ("C6 punctuation adjacency", "слово,<span>—</span>так.", "слово слово,—так."),
        ("C7 paragraph separation", "<p>перший</p><p>другий</p>", "слово перший другий"),
        ("C8 list item ordering and separation", "<ul><li>перший</li><li>другий</li></ul>", "слово перший другий"),
        ("C9 br separation", "перше<br>друге", "слово перше друге"),
    ],
)
def test_parse_entry_html_preserves_literal_inline_and_block_boundaries(cell, article, expected):
    from wiki.slovnyk_me import parse_entry_html

    row = parse_entry_html(
        f'<section id="dictionary-acticle"><article><h1>слово</h1><p>{article}</p></article></section>',
        query="слово",
        word="слово",
        dict_slug="vts",
        url="https://slovnyk.me/dict/vts/слово",
    )

    assert row is not None, cell
    assert row["text"] == expected, cell
    if cell == "C4 combining acute across nodes":
        assert row["text"].count("\u0301") == 1


def test_parse_entry_html_regression_inline_span_adjacency():
    from wiki.slovnyk_me import parse_entry_html

    row = parse_entry_html(
        "<section id='dictionary-acticle'><article><h1>ліст</h1>"
        "<p><span>лі</span><span>с</span><span>т</span></p></article></section>",
        query="ліст",
        word="ліст",
        dict_slug="vts",
        url="https://slovnyk.me/dict/vts/ліст",
    )

    assert row is not None
    assert row["text"] == "ліст ліст"


def test_parse_entry_html_preserves_inline_headword_title_and_lookup_normalization():
    from wiki.slovnyk_me import parse_entry_html

    row = parse_entry_html(
        "<html><head><title>книга — словник</title></head>"
        "<section id='dictionary-acticle'><article><h1>кн<span>и</span>га\u0301</h1>"
        "<p>текст</p></article></section></html>",
        query="книга",
        word="книга",
        dict_slug="vts",
        url="https://slovnyk.me/dict/vts/книга",
    )

    assert row is not None
    assert row["word"] == "книга\u0301"
    assert row["title"] == "книга — словник"
    assert row["normalized_word"] == "книга"


@pytest.mark.parametrize("section_id", ["dictionary-acticle", "dictionary-article"])
def test_parse_entry_html_keeps_article_alias_termination_and_excludes_outside_content(section_id):
    from wiki.slovnyk_me import parse_entry_html

    row = parse_entry_html(
        f"<p>before</p><section id='{section_id}'><article><h1>слово</h1>"
        "<p>всередині</p></article><p>поза article</p></section>"
        "<section id='dictionary-more'><p>інше</p></section><p>after</p>",
        query="слово",
        word="слово",
        dict_slug="vts",
        url="https://slovnyk.me/dict/vts/слово",
    )

    assert row is not None
    assert row["text"] == "слово всередині"


@pytest.mark.parametrize(
    ("metadata", "expected_title", "expected_snippet", "expected_url"),
    [
        (
            "<title>слово — заголовок</title><meta name='description' content='опис'>"
            "<link rel='canonical' href='https://slovnyk.me/canonical'>",
            "слово — заголовок",
            "опис",
            "https://slovnyk.me/canonical",
        ),
        ("", "слово", "слово те…", "https://fallback.example/entry"),
    ],
)
def test_parse_entry_html_preserves_schema_metadata_fallbacks_and_truncation(
    metadata, expected_title, expected_snippet, expected_url
):
    from wiki.slovnyk_me import parse_entry_html

    row = parse_entry_html(
        f"<html><head>{metadata}</head><section id='dictionary-acticle'><article>"
        "<h1>слово</h1><p>текст</p></article></section></html>",
        query="запит",
        word="слово",
        dict_slug="vts",
        url="https://fallback.example/entry",
        max_text_chars=9,
    )

    assert row is not None
    assert set(row) == {
        "query", "word", "normalized_word", "dictionary_slug", "dictionary_label", "source_type",
        "source_url", "title", "snippet", "text", "is_modern", "is_dialect", "is_russianism",
        "sovietization_risk", "sovietization_keywords", "fetched_at",
    }
    assert row["query"] == "запит"
    assert row["word"] == "слово"
    assert row["source_url"] == expected_url
    assert row["title"] == expected_title
    assert row["snippet"] == expected_snippet
    assert row["text"] == "слово те…"
    assert row["dictionary_slug"] == "vts"
    assert row["dictionary_label"] == "Великий тлумачний словник сучасної української мови"
    assert row["source_type"] == "modern_explanatory"
    assert row["is_modern"] is True
    assert row["is_dialect"] is False
    assert row["is_russianism"] is False
    assert {key: type(value) for key, value in row.items()} == {
        "query": str,
        "word": str,
        "normalized_word": str,
        "dictionary_slug": str,
        "dictionary_label": str,
        "source_type": str,
        "source_url": str,
        "title": str,
        "snippet": str,
        "text": str,
        "is_modern": bool,
        "is_dialect": bool,
        "is_russianism": bool,
        "sovietization_risk": int,
        "sovietization_keywords": str,
        "fetched_at": str,
    }


def test_parse_entry_html_empty_section_and_headword_fallbacks():
    from wiki.slovnyk_me import parse_entry_html

    empty = parse_entry_html(
        "<section id='dictionary-acticle'><article></article></section>",
        query="запит",
        word="слово",
        dict_slug="vts",
        url="https://slovnyk.me/dict/vts/слово",
    )
    row = parse_entry_html(
        "<section id='dictionary-acticle'><article><p>текст</p></article></section>",
        query="запит",
        word="СЛОВО\u0301",
        dict_slug="vts",
        url="https://slovnyk.me/dict/vts/слово",
    )

    assert empty is None
    assert row is not None
    assert row["word"] == "слово"
    assert row["title"] == "слово"
    assert row["text"] == "текст"


def test_search_slovnyk_me_returns_inline_text_through_real_fetch_chain(tmp_path, monkeypatch):
    from wiki import slovnyk_me, sources_db

    db_path = tmp_path / "sources.db"
    with sqlite3.connect(db_path) as conn:
        slovnyk_me.ensure_slovnyk_me_schema(conn)
    response_html = (
        "<title>книга — тест</title><section id='dictionary-acticle'><article><h1>кни<span>га</span></h1>"
        "<p>взірець<span>,</span> пункт.</p></article></section>"
    )
    calls = []

    class Response:
        status_code = 200
        text = response_html

        def raise_for_status(self):
            return None

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr(slovnyk_me.requests, "get", fake_get)
    rows, outages = sources_db.search_slovnyk_me_with_status(
        "книга", limit=1, dictionaries=["vts"], live=True, db_path=db_path
    )

    assert calls == [
        (
            "https://slovnyk.me/dict/vts/%D0%BA%D0%BD%D0%B8%D0%B3%D0%B0",
            {"timeout": 20, "headers": {"User-Agent": slovnyk_me.DEFAULT_USER_AGENT}},
        )
    ]
    assert len(rows) == 1
    assert rows[0]["word"] == "книга"
    assert rows[0]["text"] == "книга взірець, пункт."
    assert rows[0]["source_url"] == "https://slovnyk.me/dict/vts/%D0%BA%D0%BD%D0%B8%D0%B3%D0%B0"
    assert rows[0]["dictionary_slug"] == "vts"
    assert rows[0]["source"] == "slovnyk.me"
    assert outages == []


def test_primary_synonym_sense_text_cuts_later_groups():
    from wiki.slovnyk_me import primary_synonym_sense_text

    text = "місто д. город, ур. град, (головне) столиця, центр; (портове) порт; П. посада."

    assert primary_synonym_sense_text(text, "karavansky") == (
        "місто д. город, ур. град, (головне) столиця, центр"
    )
