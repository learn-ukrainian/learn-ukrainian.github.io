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
    return path
