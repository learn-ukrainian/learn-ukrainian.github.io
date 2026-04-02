"""Tests for ukrlib quarantine reattribution.

Pre-execution tests verify the plan is correct before running the script.
They are skipped once reattribution is complete (quarantine cleaned up).

Post-execution tests verify the output after reattribution + ingestion.
"""

import json
import sys
from pathlib import Path

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

    EXPECTED_FILES = [
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

    CANONICAL_CHECKS = [
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

    DUPLICATE_TARGETS = [
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

    NEW_FILENAMES = [
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

    EXPECTED_FILES = {
        "ukrlib-kotsyubynsky.jsonl": "Коцюбинський М.",
        "ukrlib-kotlyarevsky.jsonl": "Котляревський І.",
        "ukrlib-myrny.jsonl": "Мирний П.",
        "ukrlib-tychyna.jsonl": "Тичина П.",
        "ukrlib-nechuy.jsonl": "Нечуй-Левицький І.",
    }

    EXPECTED_PREFIXES = {
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


class TestPostSearchQuality:
    """Verify reattributed authors have chunks in Qdrant with correct metadata."""

    AUTHOR_CHECKS = [
        ("Коцюбинський М.", "Fata Morgana", 1157),
        ("Котляревський І.", "Енеїда", 313),
        ("Мирний П.", "Хіба ревуть воли", 1281),
        ("Тичина П.", "Арфами, арфами", 351),
        ("Нечуй-Левицький І.", "Кайдашева сім'я", 4370),
    ]

    @pytest.mark.parametrize("author,work_substr,expected_count", AUTHOR_CHECKS)
    def test_post_author_chunks_in_qdrant(self, author, work_substr, expected_count):
        """Verify author has correct chunk count and contains expected work."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import FieldCondition, Filter, MatchValue
        except ImportError:
            pytest.skip("qdrant_client not installed")

        from rag.config import LITERARY_COLLECTION, QDRANT_HOST, QDRANT_REST_PORT

        try:
            client = QdrantClient(host=QDRANT_HOST, port=QDRANT_REST_PORT, timeout=5)
            client.get_collection(LITERARY_COLLECTION)
        except Exception:
            pytest.skip("Qdrant not available or collection not found")

        # Check total chunk count for author
        count = client.count(
            collection_name=LITERARY_COLLECTION,
            count_filter=Filter(must=[
                FieldCondition(key="author", match=MatchValue(value=author)),
            ]),
        ).count
        assert count == expected_count, (
            f"Expected {expected_count} chunks for '{author}', got {count}"
        )

        # Check that a known work exists with correct author
        # Scroll through all chunks to collect unique work titles
        works = set()
        offset = None
        while True:
            results, offset = client.scroll(
                collection_name=LITERARY_COLLECTION,
                scroll_filter=Filter(must=[
                    FieldCondition(key="author", match=MatchValue(value=author)),
                ]),
                limit=500,
                offset=offset,
                with_payload=["work"],
            )
            works.update(p.payload["work"] for p in results)
            if offset is None:
                break
        matching = [w for w in works if work_substr in w]
        assert matching, (
            f"Expected work containing '{work_substr}' for author '{author}', "
            f"found works: {works}"
        )
