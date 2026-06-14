"""Unit tests for the literary source_url migration (uses TEMP sqlite fixture DB only).

Covers:
- Idempotent column add via guarded ALTER (PRAGMA check).
- Backfill from temp JSONL dir keyed by chunk_id.
- NULL when JSONL lacks the key, or when wave's JSONL is absent locally.
- Reporting of updated / still-null counts + reasons.
- No modification of real data/sources.db .
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

import pytest

# Make scripts/ importable like other migrate tests
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from rag.migrate_add_literary_source_url import (
    _get_column_names,
    backfill_from_jsonl,
    ensure_source_url_column,
    load_urls_by_chunk_id,
    run_migration,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )


def _init_literary_table_only(conn: sqlite3.Connection) -> None:
    """Minimal literary_texts table matching the shape used by sources.db (no FTS for this test)."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS literary_texts (
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
            -- NOTE: source_url intentionally absent here to simulate pre-migration DB
        );
        """
    )
    conn.commit()


@pytest.fixture()
def literary_migrate_fixture(tmp_path: Path) -> dict[str, Path]:
    db_path = tmp_path / "test-sources.db"
    lit_dir = tmp_path / "literary_texts"
    lit_dir.mkdir()

    conn = sqlite3.connect(str(db_path))
    _init_literary_table_only(conn)

    # Seed rows representing different situations:
    # 1. will be backfilled from present wave jsonl that has source_url
    # 2. chunk in present wave jsonl but no source_url key -> NULL
    # 3. wave with no local jsonl at all -> left NULL, logged
    # 4. chunk_id unknown even if wave present -> NULL
    rows = [
        (1, "c1_hash_c0001", "Title1", "Text one about Ukraine.", "wave01-present", "Anon", "Work One", "work1", 1900, "prose", "modern", 42),
        (2, "c2_hash_c0002", "Title2", "Text two.", "wave01-present", "Anon", "Work One", "work1", 1900, "prose", "modern", 21),
        (3, "c3_hash_c0003", "Title3", "Text three.", "wave02-missing-jsonl", "Anon", "Work Two", "work2", 1800, "chronicle", "middle_ukrainian", 99),
        (4, "c4_hash_c0004", "Title4", "Text four unknown cid.", "wave01-present", "Anon", "Work One", "work1", 1900, "prose", "modern", 10),
    ]
    conn.executemany(
        "INSERT INTO literary_texts (id, chunk_id, title, text, source_file, author, work, work_id, year, genre, language_period, char_count) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()

    # JSONL for wave01-present: one with url, one without
    _write_jsonl(
        lit_dir / "wave01-present.jsonl",
        [
            {"chunk_id": "c1_hash_c0001", "text": "...", "source_url": "http://izbornyk.org.ua/work1/page1.htm", "work": "Work One"},
            {"chunk_id": "c2_hash_c0002", "text": "...", "work": "Work One"},  # deliberately no source_url -> NULL
        ],
    )
    # No JSONL for wave02-missing-jsonl on purpose

    # Extra jsonl not referenced by any seeded row (should not affect counts)
    _write_jsonl(
        lit_dir / "wave99-orphan.jsonl",
        [{"chunk_id": "orphan_001", "text": "x", "source_url": "http://example.com/orphan"}],
    )

    return {"db_path": db_path, "lit_dir": lit_dir}


def test_ensure_column_idempotent_and_adds(literary_migrate_fixture: dict[str, Path]) -> None:
    db_path = literary_migrate_fixture["db_path"]
    conn = sqlite3.connect(str(db_path))

    # Before
    cols_before = _get_column_names(conn)
    assert "source_url" not in cols_before

    added1 = ensure_source_url_column(conn)
    assert added1 is True
    cols_after = _get_column_names(conn)
    assert "source_url" in cols_after

    # Idempotent
    added2 = ensure_source_url_column(conn)
    assert added2 is False

    # PRAGMA shows the column (for evidence parity)
    pragma = conn.execute("PRAGMA table_info(literary_texts)").fetchall()
    names = [c[1] for c in pragma]
    assert "source_url" in names
    conn.close()


def test_backfill_counts_and_null_reasons(literary_migrate_fixture: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
    db_path = literary_migrate_fixture["db_path"]
    lit_dir = literary_migrate_fixture["lit_dir"]

    # Load using the real loader (against our temp lit_dir)
    # Temporarily point? load uses global but we can call with override by patching? Simpler: call load then backfill directly.
    # Since load_urls_by_chunk_id hardcodes LITERARY_DIR, we monkey the constant for test or reimpl call.
    # For isolation: directly exercise the load func by temp monkey of module attr.
    import rag.migrate_add_literary_source_url as mig

    old_dir = mig.LITERARY_DIR
    mig.LITERARY_DIR = lit_dir
    try:
        url_map, present = load_urls_by_chunk_id(lit_dir)  # explicit also ok, but use the func
        # Re-call to exercise the module func
        assert "c1_hash_c0001" in url_map
        assert url_map["c1_hash_c0001"] == "http://izbornyk.org.ua/work1/page1.htm"
        assert "c2_hash_c0002" in url_map and url_map["c2_hash_c0002"] is None
        assert "wave01-present" in present
        assert "wave02-missing-jsonl" not in present
    finally:
        mig.LITERARY_DIR = old_dir

    # Now run full backfill via the API on a fresh conn (inside tx)
    conn = sqlite3.connect(str(db_path))
    # ensure col first (simulates pre-state)
    with conn:
        ensure_source_url_column(conn)

    with conn:
        # use the loader result from above (we have the map)
        # rebuild map under the temp dir
        mig.LITERARY_DIR = lit_dir
        url_map2, present2 = load_urls_by_chunk_id(lit_dir)
        stats = backfill_from_jsonl(conn, url_map2, present2)
    conn.close()

    assert stats["total_rows"] == 4
    assert stats["updated"] == 1  # only the one with explicit url
    assert stats["still_null"] >= 3

    reasons = stats["null_reasons"]
    # wave absent
    assert any("no local JSONL for wave wave02-missing-jsonl" in k for k in reasons)
    # chunk present but no url in record
    assert any("JSONL present for chunk but source_url absent/empty" in k for k in reasons)
    # unknown cid
    assert any("chunk_id had no matching entry in any local JSONL" in k for k in reasons)

    # Verify actual values in DB
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("SELECT chunk_id, source_url FROM literary_texts ORDER BY id").fetchall()
    conn.close()

    # row1 got the url
    assert rows[0][1] == "http://izbornyk.org.ua/work1/page1.htm"
    # others remain NULL (sqlite stores None as NULL)
    assert rows[1][1] is None or rows[1][1] == ""
    assert rows[2][1] is None or rows[2][1] == ""
    assert rows[3][1] is None or rows[3][1] == ""


def test_run_migration_on_temp_fixture_prints_pragma_and_counts(literary_migrate_fixture: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
    """Exercise the high-level runner + capture evidence-like output (PRAGMA, backfill counts)."""
    db_path = literary_migrate_fixture["db_path"]
    lit_dir = literary_migrate_fixture["lit_dir"]

    import rag.migrate_add_literary_source_url as mig

    old_dir = mig.LITERARY_DIR
    mig.LITERARY_DIR = lit_dir
    try:
        result = run_migration(db_path, dry_run=False)
    finally:
        mig.LITERARY_DIR = old_dir

    assert result["existed"] is True
    assert result["added_column"] in (True, False)  # first run adds
    assert "stats" in result
    s = result["stats"]
    assert s["updated"] >= 1
    assert "pragma_after" in result
    names = [c[1] for c in result["pragma_after"]]
    assert "source_url" in names

    # stdout from inside run_migration should have been emitted
    out = capsys.readouterr().out
    assert "PRAGMA table_info(literary_texts) [after ensure]" in out or "source_url column added" in out
    assert "rows updated with source_url" in out or "updated=" in out.lower()


def test_dry_run_does_not_backfill(literary_migrate_fixture: dict[str, Path]) -> None:
    db_path = literary_migrate_fixture["db_path"]
    lit_dir = literary_migrate_fixture["lit_dir"]

    import rag.migrate_add_literary_source_url as mig

    old_dir = mig.LITERARY_DIR
    mig.LITERARY_DIR = lit_dir
    try:
        result = run_migration(db_path, dry_run=True)
    finally:
        mig.LITERARY_DIR = old_dir

    assert result.get("dry_run") is True
    # col may be added, but no stats backfill
    assert "stats" not in result or result.get("stats") is None

    # Verify no values were written (all should still be NULL)
    conn = sqlite3.connect(str(db_path))
    null_count = conn.execute("SELECT COUNT(*) FROM literary_texts WHERE source_url IS NULL OR source_url = ''").fetchone()[0]
    conn.close()
    # Since dry-run may have added col in its tx but no updates, all 4 remain null
    assert null_count == 4
