"""Smoke tests for ``scripts/migrations/2026-05-15-add-author-uk-to-textbooks``.

The migration is the one-time bridge from Latin-romanized
``textbooks.author`` values to Cyrillic ``textbooks.author_uk``. Tests
verify (1) the column is added, (2) the back-fill resolves both
author-column rows and orphan rows via source_file inference, (3)
re-running is a no-op.
"""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path


def _load_migration():
    """Import the dated migration script under a stable module name.

    Filename starts with a digit, so ``import`` won't reach it — load via
    importlib.util.
    """
    repo = Path(__file__).resolve().parent.parent
    src = (
        repo
        / "scripts"
        / "migrations"
        / "2026-05-15-add-author-uk-to-textbooks.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_mig_author_uk_2026_05_15", src
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _build_pre_migration_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.executescript(
        """
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            grade TEXT DEFAULT '',
            author TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0
        );
        """
    )
    conn.executemany(
        "INSERT INTO textbooks (chunk_id, title, text, source_file, "
        "grade, author) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                "10-klas-ukrmova-karaman-2018_s0187",
                "Сторінка 187",
                "...",
                "10-klas-ukrmova-karaman-2018",
                "10",
                "karaman",
            ),
            # Orphan row: no author, but source_file contains the translit.
            (
                "4-klas-ukrmova-zaharijchuk_s0162",
                "Сторінка 162",
                "...",
                "4-klas-ukrmova-zaharijchuk",
                "4",
                "",
            ),
        ],
    )
    conn.commit()
    conn.close()


def test_migration_adds_column_and_backfills(tmp_path: Path) -> None:
    db = tmp_path / "sources.db"
    _build_pre_migration_db(db)
    mig = _load_migration()
    with sqlite3.connect(str(db)) as conn:
        status = mig.apply(conn, dry_run=False)
    assert status.column_added is True
    assert status.rows_updated == 2  # one author-row + one orphan-row
    with sqlite3.connect(str(db)) as conn:
        row = conn.execute(
            "SELECT author_uk FROM textbooks WHERE author = 'karaman'"
        ).fetchone()
        assert row[0] == "Караман"
        row = conn.execute(
            "SELECT author_uk FROM textbooks "
            "WHERE source_file = '4-klas-ukrmova-zaharijchuk'"
        ).fetchone()
        assert row[0] == "Захарійчук"


def test_migration_is_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "sources.db"
    _build_pre_migration_db(db)
    mig = _load_migration()
    with sqlite3.connect(str(db)) as conn:
        first = mig.apply(conn, dry_run=False)
    with sqlite3.connect(str(db)) as conn:
        second = mig.apply(conn, dry_run=False)
    assert first.column_added is True
    assert second.column_added is False
    assert second.rows_updated == 0
    assert second.unmapped_authors == []


def test_migration_dry_run_does_not_write(tmp_path: Path) -> None:
    db = tmp_path / "sources.db"
    _build_pre_migration_db(db)
    mig = _load_migration()
    with sqlite3.connect(str(db)) as conn:
        status = mig.apply(conn, dry_run=True)
    assert status.column_added is True  # would-add
    with sqlite3.connect(str(db)) as conn:
        # Column was not actually added in dry-run.
        cols = [
            row[1] for row in conn.execute("PRAGMA table_info(textbooks)").fetchall()
        ]
    assert "author_uk" not in cols
    assert status.rows_updated >= 1  # would-update count is non-zero


def test_migration_reports_unmapped_latin_authors(tmp_path: Path) -> None:
    db = tmp_path / "sources.db"
    _build_pre_migration_db(db)
    mig = _load_migration()
    with sqlite3.connect(str(db)) as conn:
        conn.execute(
            "INSERT INTO textbooks (chunk_id, source_file, grade, author) "
            "VALUES ('x', 'x.jsonl', '5', 'fictional_author_xyz')"
        )
        conn.commit()
        status = mig.apply(conn, dry_run=False)
    assert "fictional_author_xyz" in status.unmapped_authors
