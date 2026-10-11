"""Regression test for ESUM foreign-key baseline and semantic query safety.

Issue #8417 / Epic #6321.
"""

from __future__ import annotations

import sqlite3


def test_esum_foreign_key_in_memory_simulation() -> None:
    """Validate in-memory foreign key behavior matching ESUM ID space divergence."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE esum_etymology_meta (
            id INTEGER PRIMARY KEY,
            lemma TEXT NOT NULL,
            vol INTEGER NOT NULL,
            page INTEGER NOT NULL,
            entry_hash TEXT NOT NULL DEFAULT '',
            etymology_text TEXT NOT NULL,
            cognates TEXT NOT NULL DEFAULT '[]',
            source TEXT NOT NULL DEFAULT 'ЕСУМ',
            UNIQUE(lemma, vol, page, entry_hash)
        );

        CREATE TABLE esum_cognate_forms (
            entry_id INTEGER PRIMARY KEY,
            cognate_forms TEXT NOT NULL DEFAULT '{}',
            proto_form TEXT,
            extracted_count INTEGER NOT NULL DEFAULT 0,
            expected_count INTEGER NOT NULL DEFAULT 0,
            cognate_forms_recovered TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY(entry_id) REFERENCES esum_etymology_meta(id)
        );

        -- Insert meta entries with ID range starting at 215658
        INSERT INTO esum_etymology_meta (id, lemma, vol, page, etymology_text)
        VALUES (215658, 'а1', 1, 37, 'р. а, бр. а, др. а');

        -- Insert cognate forms with historical ID range starting at 62945
        INSERT INTO esum_cognate_forms (entry_id, cognate_forms, proto_form, extracted_count, expected_count)
        VALUES (62945, '{"р.": "а", "бр.": "а"}', 'а', 2, 2);
        """
    )

    # With foreign_keys disabled by default in SQLite:
    # 1. Queries execute without raising OperationalError or IntegrityError.
    rows = conn.execute(
        """
        SELECT e.id, e.lemma, COALESCE(f.cognate_forms, '{}') AS cognates
        FROM esum_etymology_meta e
        LEFT JOIN esum_cognate_forms f ON f.entry_id = e.id
        """
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["id"] == 215658
    assert rows[0]["cognates"] == "{}"  # Disjoint ID means left join safely defaults

    # 2. PRAGMA foreign_key_check correctly flags the orphan record.
    fk_errors = conn.execute("PRAGMA foreign_key_check(esum_cognate_forms)").fetchall()
    assert len(fk_errors) == 1
    assert fk_errors[0][0] == "esum_cognate_forms"
    assert fk_errors[0][1] == 62945
    assert fk_errors[0][2] == "esum_etymology_meta"
    assert fk_errors[0][3] == 0
