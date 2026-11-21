"""collection_stats scans each content table once per call."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.rag import query


def test_collection_stats_counts_each_content_table_once(tmp_path: Path) -> None:
    """Defect class: collection_stats issues COUNT(*) on a content table more than once per call.

    The fixture covers a populated table, an empty table, a view, a missing content
    table, and a table outside the content list. The total is the sum of the returned
    counts, on the same module object collection_stats calls.
    """
    database = tmp_path / "sources.db"
    setup = sqlite3.connect(database)
    setup.executescript(
        """
        CREATE TABLE textbooks (id INTEGER PRIMARY KEY);
        INSERT INTO textbooks (id) VALUES (1), (2), (3);
        CREATE TABLE wikipedia (id INTEGER PRIMARY KEY);
        CREATE TABLE style_guide_rows (id INTEGER PRIMARY KEY);
        INSERT INTO style_guide_rows (id) VALUES (1);
        CREATE VIEW style_guide AS SELECT id FROM style_guide_rows;
        CREATE TABLE not_content (id INTEGER PRIMARY KEY);
        INSERT INTO not_content (id) VALUES (9);
        """
    )
    statements: list[str] = []
    setup.set_trace_callback(statements.append)
    with query.sources_db.using_connection(setup):
        body = query.collection_stats()
    setup.close()

    sources = body["sources_db"]
    assert sources["status"] == "ok"
    assert "error" not in sources
    tables = sources["tables"]
    assert tables == {"textbooks": 3, "wikipedia": 0, "style_guide": 1}
    assert sources["points_count"] == sum(tables.values()) == 4

    exact = [statement.strip() for statement in statements]
    for name in tables:
        assert exact.count(f"SELECT COUNT(*) FROM {name}") == 1
    for name in query.sources_db.CONTENT_TABLES:
        if name not in tables:
            assert exact.count(f"SELECT COUNT(*) FROM {name}") == 0
    assert exact.count("SELECT COUNT(*) FROM not_content") == 0
    assert exact.count("SELECT COUNT(*) FROM style_guide_rows") == 0
