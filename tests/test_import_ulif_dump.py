"""Tests for scripts/lexicon/tools/import_ulif_dump.py."""

from __future__ import annotations

import json
import sqlite3

from scripts.lexicon.tools.import_ulif_dump import (
    ensure_target_schema,
    import_batch,
    normalize_query,
)


def _setup_dump_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE ulif_entries (
            lemma TEXT PRIMARY KEY,
            canonical_headword TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL,
            retrieved_at TEXT NOT NULL DEFAULT '',
            paradigm_json TEXT,
            synonyms_json TEXT,
            phraseology_json TEXT,
            antonyms_json TEXT,
            raw_html_json TEXT
        );
        """
    )
    # 1. OK entry with sections
    syn_json = json.dumps([{"terms": [{"text": "хороший"}], "register_labels": ["розм."]}], ensure_ascii=False)
    ant_json = json.dumps([{"rows": [{"kind": "paired_sense", "left": {"terms": [{"text": "добрий"}]}, "right": {"terms": [{"text": "поганий"}]}}]}], ensure_ascii=False)
    conn.execute(
        "INSERT INTO ulif_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("добрий", "до́брий", "ok", "2026-09-12T23:00:00Z", '{"kind": "noun"}', syn_json, None, ant_json, None),
    )
    # 2. Not found entry
    conn.execute(
        "INSERT INTO ulif_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("невідомеслово", "", "not_found", "2026-09-12T23:01:00Z", None, None, None, None, None),
    )
    return conn


def _setup_target_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    ensure_target_schema(conn)
    return conn


def test_normalize_query() -> None:
    assert normalize_query("  Київ  ") == "київ"
    assert normalize_query("Слово  Друге") == "слово друге"


def test_import_batch_inserts_entries_and_sections() -> None:
    dump_conn = _setup_dump_db()
    target_conn = _setup_target_db()

    tally = import_batch(dump_conn, target_conn)

    assert tally["scanned"] == 2
    assert tally["inserted"] == 2
    assert tally["updated"] == 0
    assert tally["sections"] == 3  # paradigm, synonyms, antonyms

    # Verify target contents
    entries = target_conn.execute("SELECT normalized_query, canonical_headword, status FROM ulif_dictua_entries ORDER BY id").fetchall()
    assert len(entries) == 2
    assert entries[0] == ("добрий", "до́брий", "ok")
    assert entries[1] == ("невідомеслово", "", "not_found")

    sections = target_conn.execute("SELECT kind, source_order, sense_or_group_id FROM ulif_dictua_sections WHERE entry_id = 1 ORDER BY kind").fetchall()
    kinds = [s[0] for s in sections]
    assert "antonyms" in kinds
    assert "paradigm" in kinds
    assert "synonyms" in kinds

    # Second pass: idempotent skipping
    tally2 = import_batch(dump_conn, target_conn)
    assert tally2["scanned"] == 2
    assert tally2["inserted"] == 0
    assert tally2["updated"] == 0
    assert tally2["skipped"] == 2
