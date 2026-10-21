from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki import dense_rerank


def test_iter_textbook_units_includes_unsectioned_chunks():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE textbook_sections (
            section_id INTEGER, source_file TEXT, section_title TEXT, full_text TEXT
        );
        CREATE TABLE textbooks (
            id INTEGER, chunk_id TEXT, source_file TEXT, title TEXT, text TEXT,
            parent_section_id INTEGER
        );
        INSERT INTO textbook_sections VALUES (7, 'section-book', 'Section', 'section text');
        INSERT INTO textbooks VALUES (1, 'section-chunk', 'section-book', 'Child', 'child text', 7);
        INSERT INTO textbooks VALUES (2, 'ulp-chunk', 'ulp-book', 'ULP title', 'unsectioned text', NULL);
        """
    )

    units = list(dense_rerank._iter_textbook_units(conn))

    assert [unit.unit_key for unit in units] == [
        "textbook_sections:7",
        "textbook_sections:ulp-chunk",
    ]
    assert units[1].text == "unsectioned text"
    assert units[1].parent_key == "ulp-book"
    conn.close()
