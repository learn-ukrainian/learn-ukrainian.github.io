"""Tests for ukrlib quarantine reattribution (#807).

The reattribution ran once and its quarantine input is gone, so only the
post-execution checks remain: they verify the output after reattribution +
ingestion.
"""

import sys
from pathlib import Path
from typing import ClassVar

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lu_machinery.lib.readonly_sqlite import open_readonly

from rag.config import LITERARY_DIR

# ── Post-execution tests ─────────────────────────────────────────────




class TestPostNoCrossContamination:
    """Run cross-contamination audit on the reattributed files."""

    def test_post_no_cross_contamination(self):
        from rag.scrape_ukrlib import audit_cross_contamination

        passed, errors = audit_cross_contamination(LITERARY_DIR)
        assert passed, "Cross-contamination detected:\n" + "\n".join(errors)





class TestPostSearchQuality:
    """Verify reattributed authors have chunks in the SQLite source corpus."""

    AUTHOR_CHECKS: ClassVar[list[tuple[str, str]]] = [
        ("Коцюбинський М.", "Fata Morgana"),
        ("Котляревський І.", "Енеїда"),
        ("Мирний П.", "Хіба ревуть воли"),
        ("Тичина П.", "Арфами, арфами"),
        ("Нечуй-Левицький І.", "Кайдашева сім'я"),
    ]

    @pytest.mark.data_tier("sources", tables=("literary_texts",))
    @pytest.mark.parametrize("author,work_substr", AUTHOR_CHECKS)
    def test_post_author_chunks_in_sources_db(self, author, work_substr, data_store_factory):
        db_path = data_store_factory("sources", required_sqlite_tables=("literary_texts",))
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
