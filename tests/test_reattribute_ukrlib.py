"""Tests for ukrlib quarantine reattribution (#807).

The reattribution ran once and its quarantine input is gone, so only the
post-execution checks remain: they verify the output after reattribution +
ingestion.
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import ClassVar

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rag.config import LITERARY_DIR
from scripts.lib.readonly_sqlite import open_readonly

_SOURCES_DB = Path(__file__).resolve().parents[1] / "data" / "sources.db"

# ── Post-execution tests ─────────────────────────────────────────────


class TestPostReattributedFilesValid:
    """Each new JSONL has correct author/work fields and valid chunk_ids."""

    EXPECTED_FILES: ClassVar[dict[str, str]] = {
        "ukrlib-kotsyubynsky.jsonl": "Коцюбинський М.",
        "ukrlib-kotlyarevsky.jsonl": "Котляревський І.",
        "ukrlib-myrny.jsonl": "Мирний П.",
        "ukrlib-tychyna.jsonl": "Тичина П.",
        "ukrlib-nechuy.jsonl": "Нечуй-Левицький І.",
    }

    EXPECTED_PREFIXES: ClassVar[dict[str, str]] = {
        "ukrlib-kotsyubynsky.jsonl": "Михайло Коцюбинський",
        "ukrlib-kotlyarevsky.jsonl": "Іван Котляревський",
        "ukrlib-myrny.jsonl": "Панас Мирний",
        "ukrlib-tychyna.jsonl": "Павло Тичина",
        "ukrlib-nechuy.jsonl": "Іван Нечуй-Левицький",
    }

    @pytest.mark.parametrize("filename,expected_author", list(EXPECTED_FILES.items()))
    def test_post_file_has_correct_author(self, filename, expected_author):
        path = LITERARY_DIR / filename
        if not path.exists():
            pytest.skip(f"Reattributed file not yet created: {path}")

        expected_prefix = self.EXPECTED_PREFIXES[filename]
        chunk_ids = set()
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                chunk = json.loads(line)
                assert chunk["author"] == expected_author, (
                    f"Line {i}: author={chunk['author']}, expected={expected_author}"
                )
                assert chunk["work"].startswith(expected_prefix + ". "), (
                    f"Line {i}: work does not start with '{expected_prefix}. ': {chunk['work']}"
                )
                assert chunk["chunk_id"] not in chunk_ids, (
                    f"Line {i}: duplicate chunk_id: {chunk['chunk_id']}"
                )
                chunk_ids.add(chunk["chunk_id"])
                # Verify required fields
                for field in ("text", "source_url", "year", "genre", "language_period"):
                    assert field in chunk, f"Line {i}: missing field '{field}'"


class TestPostNoCrossContamination:
    """Run cross-contamination audit on the reattributed files."""

    def test_post_no_cross_contamination(self):
        from rag.scrape_ukrlib import audit_cross_contamination

        passed, errors = audit_cross_contamination(LITERARY_DIR)
        assert passed, "Cross-contamination detected:\n" + "\n".join(errors)


def _literary_corpus_available() -> bool:
    """True only when sources.db has a populated literary_texts table.

    CI uses a stub sources.db without the literary corpus (#2928), so the
    post-reattribution corpus checks below skip there and run only locally
    against the full SQLite corpus.
    """
    db_path = _SOURCES_DB
    if not db_path.exists():
        return False
    try:
        with open_readonly(db_path) as conn:
            has_table = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='literary_texts'"
            ).fetchone()
            if not has_table:
                return False
            return conn.execute("SELECT count(*) FROM literary_texts").fetchone()[0] > 0
    except sqlite3.Error:
        return False


class TestPostSearchQuality:
    """Verify reattributed authors have chunks in the SQLite source corpus."""

    AUTHOR_CHECKS: ClassVar[list[tuple[str, str]]] = [
        ("Коцюбинський М.", "Fata Morgana"),
        ("Котляревський І.", "Енеїда"),
        ("Мирний П.", "Хіба ревуть воли"),
        ("Тичина П.", "Арфами, арфами"),
        ("Нечуй-Левицький І.", "Кайдашева сім'я"),
    ]

    @pytest.mark.skipif(
        not _literary_corpus_available(),
        reason="literary_texts corpus not present (CI uses a stub sources.db; #2928)",
    )
    @pytest.mark.parametrize("author,work_substr", AUTHOR_CHECKS)
    def test_post_author_chunks_in_sources_db(self, author, work_substr):
        db_path = _SOURCES_DB
        assert db_path.exists(), f"Missing source corpus DB: {db_path}"

        with open_readonly(db_path) as conn:
            count = conn.execute(
                """
                SELECT count(*)
                FROM literary_texts
                WHERE author = ? AND work LIKE ?
                """,
                (author, f"%{work_substr}%"),
            ).fetchone()[0]

        assert count > 0, f"No chunks found for {author} / {work_substr}"
