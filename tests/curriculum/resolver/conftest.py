"""Synthetic fixtures for the resolver: an invented VESUM and a Sources bound to it."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from scripts.curriculum.evidence.sources import Sources


@pytest.fixture
def synthetic_vesum(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic-vesum.db"
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE forms_all (id INTEGER PRIMARY KEY, entry_id INTEGER,
                word_form TEXT, lemma TEXT, pos TEXT, tags TEXT, source_comment TEXT, source_location TEXT);
            CREATE TABLE form_markers (form_id INTEGER, marker TEXT, origin TEXT, marker_class TEXT);
            CREATE TABLE vesum_build_metadata (key TEXT, value TEXT);
            CREATE VIEW forms AS SELECT word_form, lemma, pos, tags FROM forms_all f
                WHERE NOT EXISTS (SELECT 1 FROM form_markers m WHERE m.form_id = f.id AND m.marker IN ('bad','obsc','subst'));
        """)
        conn.execute(
            "INSERT INTO vesum_build_metadata VALUES (?, ?)",
            ("canonical_jsonl_sha256", hashlib.sha256(b"synthetic-resolver-vesum").hexdigest()),
        )
        conn.executemany(
            "INSERT INTO forms_all VALUES (?,?,?,?,?,?,?,?)",
            [
                (1, 1, "глорт", "глорт", "noun", "noun:inanim:m:v_naz", "", "synthetic:1"),
                (2, 2, "трямс", "трямс", "verb", "verb:imperf:inf", "", "synthetic:2"),
                (3, 3, "вурдик", "вурдик", "noun", "noun:inanim:m:v_naz", "", "synthetic:3"),
            ],
        )
    return path


@pytest.fixture
def sources(synthetic_vesum: Path, tmp_path: Path):
    with Sources(sources_db=tmp_path / "synthetic-sources-unused.db", vesum_db=synthetic_vesum) as api:
        yield api
