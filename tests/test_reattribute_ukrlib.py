"""Tests for ukrlib quarantine reattribution.

Pre-execution tests verify the plan is correct before running the script.
They are skipped once reattribution is complete (quarantine cleaned up).

Post-execution tests verify the output after reattribution + ingestion.
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import ClassVar

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rag.config import LITERARY_DIR

QUARANTINE_DIR = LITERARY_DIR / "_quarantine"

# Skip all pre-tests if quarantine has been cleaned up (reattribution done)
pre_requires_quarantine = pytest.mark.skipif(
    not QUARANTINE_DIR.exists(),
    reason="Quarantine directory already cleaned up — reattribution complete",
)


# ── Pre-execution tests ──────────────────────────────────────────────


@pre_requires_quarantine
class TestPreQuarantinedFilesExist:
    """All 8 quarantined files must be present."""

    EXPECTED_FILES: ClassVar[list[str]] = [
        "ukrlib-kotlyarevsky.jsonl",
        "ukrlib-kotsyubynsky.jsonl",
        "ukrlib-kvitka.jsonl",
        "ukrlib-myrny.jsonl",
        "ukrlib-nechuy.jsonl",
        "ukrlib-rylsky.jsonl",
        "ukrlib-tychyna.jsonl",
        "ukrlib-vynnychenko.jsonl",
    ]

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_pre_quarantined_file_exists(self, filename):
        path = QUARANTINE_DIR / filename
        assert path.exists(), f"Quarantined file missing: {path}"


@pre_requires_quarantine
class TestPreKnownWorksMatchRealAuthor:
    """Spot-check canonical works against expected real authors."""

    CANONICAL_CHECKS: ClassVar[list[tuple[str, str, str]]] = [
        # (quarantined file, work title substring, expected real author prefix)
        ("ukrlib-myrny.jsonl", "Енеїда", "Панас Мирний"),  # Real: Котляревський
        ("ukrlib-kvitka.jsonl", "Fata Morgana", "Григорій Квітка-Основ'яненко"),  # Real: Коцюбинський
        ("ukrlib-kvitka.jsonl", "Intermezzo", "Григорій Квітка-Основ'яненко"),  # Real: Коцюбинський
        ("ukrlib-tychyna.jsonl", "Хіба ревуть воли", "Павло Тичина"),  # Real: Мирний
        ("ukrlib-nechuy.jsonl", "Арфами, арфами", "Іван Нечуй-Левицький"),  # Real: Тичина
        ("ukrlib-rylsky.jsonl", "Кайдашева сім'я", "Максим Рильський"),  # Real: Нечуй-Левицький
        ("ukrlib-vynnychenko.jsonl", "Мартин Боруля", "Володимир Винниченко"),  # Real: Карпенко-Карий
        ("ukrlib-kotlyarevsky.jsonl", "Кобзар", "Іван Котляревський"),  # Real: Шевченко
        ("ukrlib-kotsyubynsky.jsonl", "Байки Харківські", "Михайло Коцюбинський"),  # Real: Сковорода
    ]

    @pytest.mark.parametrize("filename,work_substr,wrong_prefix", CANONICAL_CHECKS)
    def test_pre_known_work_has_wrong_author(self, filename, work_substr, wrong_prefix):
        """Verify the quarantined file has the WRONG author (confirming the bug)."""
        path = QUARANTINE_DIR / filename
        if not path.exists():
            pytest.skip(f"Quarantined file not found: {path}")

        found = False
        with open(path, encoding="utf-8") as f:
            for line in f:
                chunk = json.loads(line)
                if work_substr in chunk.get("work", ""):
                    assert chunk["work"].startswith(wrong_prefix), (
                        f"Expected work '{work_substr}' to have wrong prefix "
                        f"'{wrong_prefix}' but got: {chunk['work']}"
                    )
                    found = True
                    break

        assert found, f"Work containing '{work_substr}' not found in {filename}"


@pre_requires_quarantine
class TestPreDuplicatesAlreadyExist:
    """Correct files must exist for the 3 duplicates."""

    DUPLICATE_TARGETS: ClassVar[list[str]] = [
        "ukrlib-shevchenko.jsonl",
        "ukrlib-skovoroda.jsonl",
        "ukrlib-karpenko_karyi.jsonl",
    ]

    @pytest.mark.parametrize("filename", DUPLICATE_TARGETS)
    def test_pre_duplicate_target_exists(self, filename):
        path = LITERARY_DIR / filename
        assert path.exists(), f"Correct file missing for duplicate: {path}"


@pre_requires_quarantine
class TestPreNoTargetFileCollision:
    """The 5 new filenames must not already exist in data/literary_texts/."""

    NEW_FILENAMES: ClassVar[list[str]] = [
        "ukrlib-kotsyubynsky.jsonl",
        "ukrlib-kotlyarevsky.jsonl",
        "ukrlib-myrny.jsonl",
        "ukrlib-tychyna.jsonl",
        "ukrlib-nechuy.jsonl",
    ]

    @pytest.mark.parametrize("filename", NEW_FILENAMES)
    def test_pre_no_collision(self, filename):
        path = LITERARY_DIR / filename
        assert not path.exists(), f"Target file already exists (would be overwritten): {path}"


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
    db_path = Path(__file__).resolve().parents[1] / "data" / "sources.db"
    if not db_path.exists():
        return False
    try:
        with sqlite3.connect(db_path) as conn:
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
        db_path = Path(__file__).resolve().parents[1] / "data" / "sources.db"
        assert db_path.exists(), f"Missing source corpus DB: {db_path}"

        with sqlite3.connect(db_path) as conn:
            count = conn.execute(
                """
                SELECT count(*)
                FROM literary_texts
                WHERE author = ? AND work LIKE ?
                """,
                (author, f"%{work_substr}%"),
            ).fetchone()[0]

        assert count > 0, f"No chunks found for {author} / {work_substr}"
