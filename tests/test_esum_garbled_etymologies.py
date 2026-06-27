import sqlite3

from scripts.lexicon.enrich_manifest import _source_etymology
from scripts.lexicon.esum_garbled import has_mojibake_marker, is_garbled_esum_lemma
from scripts.wiki.sources_db import search_esum

GARBLED_VARIANT = (
    "варіант, варіація, варіювати; — р. болг. вариант, бр. варьіянт, "
    "вл. \\тагіапіа; Веліа[ Е55) tail"
)
GOROH_VARIANT = (
    "запозичення з французької мови; фр. variante походить від лат. varians, "
    "-ntis, дієприкметника від дієслова vario."
)
GARBLED_BAZHANNIA = (
    "[бажання, «потреба; лит. разахотіти», нужда, злидні», "
    "іє. \"пац-, Зпоц-, \"пй- «стомлювати(ся)». -- Эндзелин РФВ 68"
)
GARBLED_ASPIRANT = "аспірант; фр. азрігапі; \\Уа1йе--НоГт. II 575; Веліа[ Е55) tail"
CLEAN_ESUM = "чистий ЕСУМ ряд без OCR-гарблення."


def _build_sources_db(path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE goroh_etymology (
                requested_lemma TEXT PRIMARY KEY,
                headword TEXT NOT NULL DEFAULT '',
                etymology_text TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL DEFAULT '',
                retrieved_at TEXT NOT NULL DEFAULT '',
                content_hash TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE esum_etymology_meta (
                id INTEGER PRIMARY KEY,
                lemma TEXT NOT NULL,
                vol INTEGER NOT NULL,
                page INTEGER NOT NULL,
                entry_hash TEXT NOT NULL DEFAULT '',
                etymology_text TEXT NOT NULL,
                cognates TEXT NOT NULL DEFAULT '[]',
                source TEXT NOT NULL DEFAULT 'ЕСУМ'
            );
            CREATE VIRTUAL TABLE esum_etymology USING fts5(
                lemma,
                etymology_text,
                cognates,
                vol UNINDEXED,
                page UNINDEXED,
                tokenize = 'unicode61 remove_diacritics 0'
            );
            """
        )
        conn.execute(
            """
            INSERT INTO goroh_etymology
                (requested_lemma, headword, etymology_text, source_url)
            VALUES (?, ?, ?, ?)
            """,
            ("варіант", "варіант", GOROH_VARIANT, "https://goroh.pp.ua/Етимологія/варіант"),
        )
        esum_rows = [
            (1, "варіант", 1, 332, GARBLED_VARIANT),
            (2, "бажання", 4, 115, GARBLED_BAZHANNIA),
        ]
        for rowid, lemma, vol, page, text in esum_rows:
            conn.execute(
                """
                INSERT INTO esum_etymology_meta
                    (id, lemma, vol, page, etymology_text)
                VALUES (?, ?, ?, ?, ?)
                """,
                (rowid, lemma, vol, page, text),
            )
            conn.execute(
                """
                INSERT INTO esum_etymology(rowid, lemma, etymology_text, cognates, vol, page)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (rowid, lemma, text, "[]", vol, page),
            )
        conn.commit()
    finally:
        conn.close()


def test_curated_goroh_override_cleans_manifest_etymology(tmp_path) -> None:
    db_path = tmp_path / "sources.db"
    _build_sources_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        etymology = _source_etymology(conn, "варіант", {})
    finally:
        conn.close()

    assert is_garbled_esum_lemma("варіант")
    assert etymology is not None
    assert etymology["source"] == "Горох (за ЕСУМ)"
    assert etymology["text"] == GOROH_VARIANT
    assert not has_mojibake_marker(etymology["text"])


def test_curated_entry_with_unstripped_marker_is_dropped_from_manifest(tmp_path) -> None:
    db_path = tmp_path / "sources.db"
    _build_sources_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM goroh_etymology WHERE requested_lemma = ?", ("варіант",))
        conn.commit()
        etymology = _source_etymology(conn, "варіант", {})
    finally:
        conn.close()

    assert is_garbled_esum_lemma("варіант")
    assert etymology is None


def test_curated_goroh_override_cleans_search_esum(tmp_path) -> None:
    db_path = tmp_path / "sources.db"
    _build_sources_db(db_path)

    hits = search_esum("варіант", limit=3, db_path=db_path)

    assert [hit["lemma"] for hit in hits] == ["варіант"]
    assert hits[0]["source"] == "Горох (за ЕСУМ)"
    assert hits[0]["etymology_text"] == GOROH_VARIANT
    assert not has_mojibake_marker(hits[0]["etymology_text"])


def test_uncurated_garbled_esum_row_is_filtered_from_search(tmp_path) -> None:
    db_path = tmp_path / "sources.db"
    _build_sources_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO esum_etymology_meta
            (id, lemma, vol, page, etymology_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (3, "аспірант", 1, 92, GARBLED_ASPIRANT),
        )
        conn.execute(
            """
            INSERT INTO esum_etymology(rowid, lemma, etymology_text, cognates, vol, page)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (3, "аспірант", GARBLED_ASPIRANT, "[]", 1, 92),
        )
        conn.commit()
    finally:
        conn.close()

    assert not is_garbled_esum_lemma("аспірант")
    assert search_esum("аспірант", limit=3, db_path=db_path) == []


def test_uncurated_clean_esum_row_still_surfaces(tmp_path) -> None:
    db_path = tmp_path / "sources.db"
    _build_sources_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO esum_etymology_meta
            (id, lemma, vol, page, etymology_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (3, "весна", 1, 92, CLEAN_ESUM),
        )
        conn.execute(
            """
            INSERT INTO esum_etymology(rowid, lemma, etymology_text, cognates, vol, page)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (3, "весна", CLEAN_ESUM, "[]", 1, 92),
        )
        conn.commit()

        etymology = _source_etymology(conn, "весна", {})
    finally:
        conn.close()

    assert not is_garbled_esum_lemma("весна")
    assert etymology == {"text": CLEAN_ESUM, "source": "ЕСУМ, т. 1, с. 92"}
    hits = search_esum("весна", limit=3, db_path=db_path)
    assert [hit["lemma"] for hit in hits] == ["весна"]
    assert hits[0]["etymology_text"] == CLEAN_ESUM


def test_strip_only_curated_entry_drops_garbled_tail(tmp_path) -> None:
    db_path = tmp_path / "sources.db"
    _build_sources_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        etymology = _source_etymology(conn, "бажання", {})
    finally:
        conn.close()

    assert is_garbled_esum_lemma("бажання")
    assert etymology is not None
    assert etymology["source"] == "ЕСУМ, т. 4, с. 115 (garbled tail stripped)"
    assert etymology["text"] == "[бажання, «потреба; лит. разахотіти», нужда, злидні»"
    assert not has_mojibake_marker(etymology["text"])

    hits = search_esum("бажання", limit=3, db_path=db_path)
    assert hits[0]["etymology_text"] == etymology["text"]
    assert not has_mojibake_marker(hits[0]["etymology_text"])


def test_uncurated_garbled_esum_row_falls_back_to_wiktionary(tmp_path) -> None:
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE goroh_etymology (
                requested_lemma TEXT PRIMARY KEY,
                headword TEXT NOT NULL DEFAULT '',
                etymology_text TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL DEFAULT '',
                retrieved_at TEXT NOT NULL DEFAULT '',
                content_hash TEXT NOT NULL DEFAULT ''
            );

            CREATE VIRTUAL TABLE esum_etymology
            USING fts5(lemma, etymology_text, cognates, vol UNINDEXED, page UNINDEXED);

            CREATE TABLE wiktionary_etymology (
                requested_lemma TEXT PRIMARY KEY,
                headword TEXT NOT NULL DEFAULT '',
                etymology_text TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL DEFAULT ''
            );
            """
        )
        conn.execute(
            """
            INSERT INTO esum_etymology(rowid, lemma, etymology_text, cognates, vol, page)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "аспірант",
                GARBLED_ASPIRANT,
                "[]",
                1,
                92,
            ),
        )
        conn.execute(
            """
            INSERT INTO wiktionary_etymology
            (requested_lemma, headword, etymology_text, source_url)
            VALUES (?, ?, ?, ?)
            """,
            (
                "аспірант",
                "аспірант",
                "Від французького aspirant, далі від латинського aspirans.",
                "https://example.test/aspirant",
            ),
        )
        conn.commit()

        etymology = _source_etymology(conn, "аспірант", {})
    finally:
        conn.close()

    assert not is_garbled_esum_lemma("аспірант")
    assert etymology is not None
    assert etymology["source"] == "Вікісловник (uk.wiktionary)"
    assert etymology["text"] == "Від французького aspirant, далі від латинського aspirans."
    assert not has_mojibake_marker(etymology["text"])
