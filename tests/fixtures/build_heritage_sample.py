#!/usr/bin/env python3
"""Build the small sqlite fixture for heritage-classifier CI coverage."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("heritage_sample.db")

SCHEMA_SQL = """
CREATE TABLE grinchenko (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);
CREATE INDEX idx_grinchenko_word ON grinchenko(word COLLATE NOCASE);

CREATE TABLE sum11 (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT '',
    sovietization_risk INTEGER NOT NULL DEFAULT 0,
    sovietization_keywords TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_sum11_word ON sum11(word COLLATE NOCASE);

CREATE TABLE wiktionary (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definitions TEXT DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);
CREATE INDEX idx_wiktionary_word ON wiktionary(word COLLATE NOCASE);

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
CREATE INDEX idx_esum_etymology_meta_lemma
    ON esum_etymology_meta(lemma COLLATE NOCASE);
CREATE INDEX idx_esum_etymology_meta_vol_page
    ON esum_etymology_meta(vol, page);
CREATE VIRTUAL TABLE esum_etymology USING fts5(
    lemma,
    etymology_text,
    cognates,
    vol UNINDEXED,
    page UNINDEXED,
    tokenize = 'unicode61 remove_diacritics 0'
);

CREATE TABLE literary_texts (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL DEFAULT '',
    author TEXT DEFAULT '',
    work TEXT DEFAULT '',
    work_id TEXT DEFAULT '',
    year INTEGER,
    genre TEXT DEFAULT '',
    language_period TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0
);
CREATE VIRTUAL TABLE literary_fts USING fts5(
    title,
    text,
    content='literary_texts',
    content_rowid='id',
    tokenize='unicode61'
);
CREATE TRIGGER literary_ai AFTER INSERT ON literary_texts BEGIN
    INSERT INTO literary_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;

CREATE TABLE slovnyk_me_entries (
    id INTEGER PRIMARY KEY,
    query TEXT NOT NULL DEFAULT '',
    word TEXT NOT NULL,
    normalized_word TEXT NOT NULL DEFAULT '',
    dictionary_slug TEXT NOT NULL,
    dictionary_label TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL DEFAULT 'slovnyk_me',
    source_url TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    snippet TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    is_modern INTEGER NOT NULL DEFAULT 0,
    is_dialect INTEGER NOT NULL DEFAULT 0,
    is_russianism INTEGER NOT NULL DEFAULT 0,
    sovietization_risk INTEGER NOT NULL DEFAULT 0,
    sovietization_keywords TEXT NOT NULL DEFAULT '',
    fetched_at TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_slovnyk_me_word
    ON slovnyk_me_entries(normalized_word COLLATE NOCASE);
CREATE INDEX idx_slovnyk_me_dict
    ON slovnyk_me_entries(dictionary_slug);
CREATE VIRTUAL TABLE slovnyk_me_entries_fts USING fts5(
    word,
    title,
    snippet,
    text,
    dictionary_label,
    content='slovnyk_me_entries',
    content_rowid='id',
    tokenize='unicode61'
);

CREATE TABLE style_guide (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    section TEXT DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);
CREATE INDEX idx_style_word ON style_guide(word COLLATE NOCASE);
"""

ESUM_ROWS = [
    (
        183648,
        "гаївка",
        1,
        450,
        "heritage-sample-hayivka",
        (
            "гаївка «веснянка», [агівка, гагівка, гагілка, ягівка, ягілка] "
            "«тс.»; регіональна великодня пісня-гра."
        ),
        "[]",
        "ЕСУМ vol. 1",
    ),
    (
        192763,
        "лагбйка",
        3,
        177,
        "heritage-sample-hahilka",
        (
            "[лагбйка] «весняна гра, пісня на Великдень»; видозміна форми "
            "[гагілка] «гаївка»."
        ),
        "[]",
        "ЕСУМ vol. 3",
    ),
    (
        198656,
        "опришок",
        4,
        203,
        "heritage-sample-opryshok",
        "опришок (іст.) «повстанець; учасник гірського загону».",
        '["п."]',
        "ЕСУМ vol. 4",
    ),
    (
        215389,
        "ягілка",
        6,
        532,
        "heritage-sample-yahilka",
        (
            "[ягілка] «весняна гра і пісня дівчат у Великодні дні», "
            "[ягівка], [гагівка], [гагілка] «тс.»."
        ),
        "[]",
        "ЕСУМ vol. 6",
    ),
]


def _insert_esum_rows(conn: sqlite3.Connection) -> None:
    conn.executemany(
        """
        INSERT INTO esum_etymology_meta (
            id, lemma, vol, page, entry_hash, etymology_text, cognates, source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ESUM_ROWS,
    )
    conn.executemany(
        """
        INSERT INTO esum_etymology(rowid, lemma, etymology_text, cognates, vol, page)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [(row[0], row[1], row[5], row[6], row[2], row[3]) for row in ESUM_ROWS],
    )


def build(db_path: Path = DB_PATH) -> Path:
    """Rebuild the fixture from deterministic inline rows."""
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            """
            INSERT INTO grinchenko(id, word, definition, source)
            VALUES (?, ?, ?, ?)
            """,
            (
                9370,
                "глагол",
                "Глагол, -лу, м. Слово, речь, глагол.",
                "Грінченко",
            ),
        )
        conn.execute(
            """
            INSERT INTO grinchenko(id, word, definition, source)
            VALUES (?, ?, ?, ?)
            """,
            (
                66903,
                "ягівка",
                "Ягівка, -ки, ж. = гагілка.",
                "Грінченко",
            ),
        )
        conn.execute(
            """
            INSERT INTO sum11(
                id, word, definition, text, source, sovietization_risk,
                sovietization_keywords
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                68512,
                "перекличка",
                (
                    "ПЕРЕКЛИЧКА, и, ж. 1. Перевірка присутності групи людей "
                    "викликом за прізвищами або іменами. 2. рідко. Те саме, "
                    "що переклик."
                ),
                (
                    "перекличка: ПЕРЕКЛИЧКА, и, ж. 1. Перевірка присутності "
                    "групи людей викликом за прізвищами або іменами."
                ),
                "СУМ-11",
                0,
                "",
            ),
        )
        _insert_esum_rows(conn)
        conn.execute(
            """
            INSERT INTO literary_texts(
                id, chunk_id, title, text, source_file, author, work, work_id,
                year, genre, language_period, char_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                108250,
                "feaa5fa7_c0610",
                "Купальські пісні",
                (
                    "Ми тебе Купайла скупаємо, на другоє літо поховаємо, "
                    "та й на той рочок сховаємо."
                ),
                "wave7-entsyklopediia-ukrainoznavstva",
                "Колектив",
                "Енциклопедія українознавства",
                "eu-1955",
                1955,
                "encyclopedia",
                "modern",
                96,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


if __name__ == "__main__":
    print(build())
