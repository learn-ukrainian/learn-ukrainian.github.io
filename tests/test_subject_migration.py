"""Tests for ``2026-07-06-add-subject-to-textbooks`` migration."""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest


def _load_migration():
    repo = Path(__file__).resolve().parent.parent
    src = repo / "scripts" / "migrations" / "2026-07-06-add-subject-to-textbooks.py"
    spec = importlib.util.spec_from_file_location("_mig_subject_2026_07_06", src)
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
            author_uk TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0
        );
        """
    )
    conn.executemany(
        """
        INSERT INTO textbooks (chunk_id, source_file, grade, author, author_uk)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("mova-1", "5-klas-ukrmova-avramenko-2022", "5", "avramenko", ""),
            ("lit-1", "6-klas-ukrlit-avramenko-2023", "6", "avramenko", ""),
            ("hist-1", "8-klas-istoria-ukr-schupak-2025", "8", "schupak", ""),
            ("lex-1", "anna-ohoiko-500-verbs", "", "Anna Ohoiko", ""),
        ],
    )
    conn.commit()
    conn.close()


def test_subject_migration_adds_column_index_and_backfills(tmp_path: Path) -> None:
    db = tmp_path / "sources.db"
    _build_pre_migration_db(db)
    mig = _load_migration()

    with sqlite3.connect(str(db)) as conn:
        status = mig.apply(conn, dry_run=False)

    assert status.column_added is True
    assert status.rows_updated == 4
    assert status.subject_counts == {
        "istoriya": 1,
        "lexicon": 1,
        "ukrlit": 1,
        "ukrmova": 1,
    }

    with sqlite3.connect(str(db)) as conn:
        rows = conn.execute(
            "SELECT source_file, subject FROM textbooks ORDER BY source_file"
        ).fetchall()
        assert rows == [
            ("5-klas-ukrmova-avramenko-2022", "ukrmova"),
            ("6-klas-ukrlit-avramenko-2023", "ukrlit"),
            ("8-klas-istoria-ukr-schupak-2025", "istoriya"),
            ("anna-ohoiko-500-verbs", "lexicon"),
        ]
        index_names = {
            row[1] for row in conn.execute("PRAGMA index_list(textbooks)").fetchall()
        }
        assert "idx_textbooks_subject" in index_names


def test_subject_migration_is_idempotent(tmp_path: Path) -> None:
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
    assert second.populated_subject == 4


def test_subject_migration_dry_run_reports_counts_without_writing(
    tmp_path: Path,
) -> None:
    db = tmp_path / "sources.db"
    _build_pre_migration_db(db)
    mig = _load_migration()

    with sqlite3.connect(str(db)) as conn:
        status = mig.apply(conn, dry_run=True)

    assert status.column_added is True
    assert status.rows_updated == 4
    assert status.subject_counts["ukrmova"] == 1
    with sqlite3.connect(str(db)) as conn:
        columns = [
            row[1] for row in conn.execute("PRAGMA table_info(textbooks)").fetchall()
        ]
    assert "subject" not in columns


def test_subject_migration_errors_on_unmapped_source_file(tmp_path: Path) -> None:
    db = tmp_path / "sources.db"
    _build_pre_migration_db(db)
    mig = _load_migration()

    with sqlite3.connect(str(db)) as conn:
        conn.execute(
            "INSERT INTO textbooks (chunk_id, source_file) VALUES (?, ?)",
            ("bad-1", "mystery-source-with-no-subject"),
        )
        conn.commit()
        with pytest.raises(mig.UnmappedTextbookSubjectsError) as exc_info:
            mig.apply(conn, dry_run=False)

    assert exc_info.value.source_files == ["mystery-source-with-no-subject"]
    with sqlite3.connect(str(db)) as conn:
        columns = [
            row[1] for row in conn.execute("PRAGMA table_info(textbooks)").fetchall()
        ]
    assert "subject" not in columns
