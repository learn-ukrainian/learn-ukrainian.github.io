"""Synthetic fixtures exercise structure only; none claims dictionary attestation."""

import hashlib
import json
import sqlite3

import pytest


@pytest.fixture
def synthetic_vesum(tmp_path):
    path = tmp_path / "synthetic-vesum.db"
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE forms_all (id INTEGER PRIMARY KEY, entry_id INTEGER,
                word_form TEXT, lemma TEXT, pos TEXT, tags TEXT, source_comment TEXT, source_location TEXT);
            CREATE TABLE form_markers (form_id INTEGER, marker TEXT, origin TEXT, marker_class TEXT);
            CREATE TABLE vesum_build_metadata (key TEXT, value TEXT);
            CREATE VIEW forms AS SELECT word_form, lemma, pos, tags FROM forms_all;
        """)
        conn.execute(
            "INSERT INTO vesum_build_metadata VALUES (?, ?)",
            ("canonical_jsonl_sha256", hashlib.sha256(b"synthetic-vesum").hexdigest()),
        )
        conn.executemany(
            "INSERT INTO forms_all VALUES (?,?,?,?,?,?,?,?)",
            [
                (1, 10, "synthetic-a", "synthetic", "noun", "noun:inanim:f:v_naz", "", "synthetic:1"),
                (2, 10, "synthetic-b", "synthetic", "noun", "noun:inanim:f:v_rod", "", "synthetic:1"),
                (3, 20, "synthetic-a", "synthetic", "noun", "noun:inanim:f:v_naz", "", "synthetic:2"),
                (4, 30, "synthetic-a", "synthetic", "verb", "verb:inf", "", "synthetic:3"),
            ],
        )
        conn.execute("INSERT INTO form_markers VALUES (?,?,?,?)", (2, "alt", "synthetic", "synthetic"))
    return path


@pytest.fixture
def synthetic_sources(tmp_path):
    path = tmp_path / "synthetic-sources.db"
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, normalized_query TEXT,
                homonym_index INTEGER, canonical_headword TEXT, grammatical_label TEXT,
                sense_gloss TEXT, homonym_checked INTEGER, status TEXT, retrieved_at TEXT);
            CREATE TABLE ulif_dictua_sections (id INTEGER PRIMARY KEY, entry_id INTEGER,
                kind TEXT, source_order INTEGER, sense_or_group_id TEXT, payload_json TEXT);
            CREATE TABLE dmklinger_uk_en (id INTEGER PRIMARY KEY, word TEXT, pos TEXT,
                translations TEXT, text TEXT, source TEXT);
            CREATE TABLE puls_cefr (id INTEGER PRIMARY KEY, word TEXT, level TEXT);
            CREATE TABLE textbook_sections (section_id INTEGER PRIMARY KEY, source_file TEXT,
                grade INTEGER, section_title TEXT, section_number INTEGER, page_start INTEGER,
                page_end INTEGER, chunk_count INTEGER, full_text TEXT);
            CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT,
                text TEXT, source_file TEXT, grade INTEGER, author TEXT, char_count INTEGER,
                parent_section_id INTEGER, author_uk TEXT, subject TEXT);
            CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT,
                text TEXT, source_file TEXT, author TEXT, work TEXT, work_id TEXT, year INTEGER,
                genre TEXT, language_period TEXT, char_count INTEGER, source_url TEXT);
            CREATE TABLE ua_gec_errors (id INTEGER PRIMARY KEY, error TEXT, correct TEXT,
                error_type TEXT, doc_id TEXT, annotator_id TEXT, partition TEXT, is_native INTEGER,
                source_lang TEXT);
            CREATE TABLE style_guide (id INTEGER PRIMARY KEY, word TEXT, section TEXT,
                text TEXT, source TEXT, word_lower TEXT, excerpt_full TEXT, page INTEGER,
                russianism_pattern TEXT);
        """)
        conn.executemany(
            "INSERT INTO ulif_dictua_entries VALUES (?,?,?,?,?,?,?,?,?)",
            [
                (1, "synthetic", 1, "synthetic-original", "noun", "", 0, "ok", "synthetic-time"),
                (2, "synthetic-checked", 1, "synthetic-original", "noun", "synthetic-gloss", 1, "ok", "synthetic-time"),
                (3, "synthetic-mixed", 1, "synthetic-original", "noun", "", 1, "ok", "synthetic-time"),
                (4, "synthetic-mixed", 2, "synthetic-original", "noun", "", 0, "ok", "synthetic-time"),
            ],
        )
        conn.execute(
            "INSERT INTO ulif_dictua_sections VALUES (?,?,?,?,?,?)",
            (1, 1, "paradigm", 0, "", json.dumps({"synthetic": ["source-bytes"]})),
        )
        conn.executemany(
            "INSERT INTO dmklinger_uk_en VALUES (?,?,?,?,?,?)",
            [
                (3, "synthetic", "verb", '["wrong POS"]', "", "synthetic"),
                (2, "synthetic", "noun", '["second row"]', "", "synthetic"),
                (1, "synthetic", "noun", '["first translation", "second translation"]', "", "synthetic"),
                (4, "synthetic-adj", "adjective", '["adjective translation"]', "", "synthetic"),
            ],
        )
        conn.execute("INSERT INTO puls_cefr VALUES (1, 'synthetic', 'A1')")
        conn.execute(
            "INSERT INTO textbook_sections VALUES (?,?,?,?,?,?,?,?,?)",
            (10, "synthetic-file-1", 1, "synthetic section", 1, 42, 42, 2, "synthetic section text"),
        )
        conn.executemany(
            "INSERT INTO textbooks VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    1,
                    "chunk-1",
                    "title 1",
                    "synthetic-first middle text synthetic-last",
                    "synthetic-file-1",
                    1,
                    "synthetic-author",
                    40,
                    10,
                    "synthetic-author-uk",
                    "mova",
                ),
                (
                    2,
                    "chunk-2",
                    "title 2",
                    "second chunk text for testing",
                    "synthetic-file-1",
                    1,
                    "synthetic-author",
                    35,
                    10,
                    "synthetic-author-uk",
                    "mova",
                ),
                (
                    3,
                    "chunk-3",
                    "title 3",
                    "no section chunk synthetic-start to synthetic-end",
                    "synthetic-file-2",
                    2,
                    "author 2",
                    45,
                    None,
                    "author-uk",
                    "chytannia",
                ),
            ],
        )
        conn.execute(
            "INSERT INTO literary_texts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                1,
                "lit-1",
                "lit title",
                "synthetic literary sentence quote",
                "synthetic-lit-file",
                "author",
                "work",
                "w1",
                1920,
                "prose",
                "modern",
                30,
                "",
            ),
        )
        conn.executemany(
            "INSERT INTO ua_gec_errors VALUES (?,?,?,?,?,?,?,?,?)",
            [
                (1, "synthetic-bad", "synthetic-good", "Grammar", "doc1", "ann1", "train", 1, "uk"),
                (2, "synthetic-dup-err", "synthetic-dup-corr", "Lexical", "doc2", "ann1", "train", 1, "uk"),
                (3, "synthetic-dup-err", "synthetic-dup-corr", "Lexical", "doc3", "ann2", "train", 1, "uk"),
            ],
        )
        conn.execute(
            "INSERT INTO style_guide VALUES (?,?,?,?,?,?,?,?,?)",
            (
                1,
                "synthetic-note-word",
                "synthetic-sec",
                "synthetic note explanation text",
                "style guide",
                "synthetic-note-word",
                "synthetic excerpt",
                5,
                "synthetic pattern",
            ),
        )
    return path


@pytest.fixture
def synthetic_sources_wal(synthetic_sources):
    """The same synthetic DB declared WAL, as the live sources.db is: writers commit past a pinned reader."""
    with sqlite3.connect(synthetic_sources) as conn:
        assert conn.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    return synthetic_sources


@pytest.fixture
def synthetic_standard(tmp_path):
    path = tmp_path / "synthetic-standard.txt"
    lines = [
        "synthetic standard line 1",
        "synthetic standard line 2",
        "synthetic standard line 3",
        "synthetic standard line 4",
        "synthetic standard line 5",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
