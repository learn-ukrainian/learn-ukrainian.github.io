"""Tests for the V6 knowledge packet builder."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build.research.build_knowledge_packet import (
    _extract_grade_hint,
    _extract_search_queries,
    _format_hit,
    _has_cyrillic,
    build_packet,
)

# --- Unit tests ---


def test_has_cyrillic():
    assert _has_cyrillic("Привіт") is True
    assert _has_cyrillic("Hello") is False
    assert _has_cyrillic("Mix Привіт Hello") is True
    assert _has_cyrillic("123!@#") is False


def test_extract_search_queries_basic():
    section = {
        "section": "Звуки і літери (Sounds and Letters)",
        "points": [
            "Голосні і приголосні звуки.",
            "Большакова Grade 1 p.24: правило.",
        ],
    }
    queries = _extract_search_queries(section)
    assert len(queries) >= 1
    # Should extract the Ukrainian title
    assert any("Звуки і літери" in q for q in queries)


def test_extract_search_queries_strips_english():
    section = {
        "section": "Він, вона, воно (The Gender Test)",
        "points": [],
    }
    queries = _extract_search_queries(section)
    assert queries[0] == "Він, вона, воно"


def test_extract_search_queries_limits_to_4():
    section = {
        "section": "Test",
        "points": [
            "Перша фраза тут. Друга фраза тут. Третя фраза тут. "
            "Четверта фраза тут. П'ята фраза тут. Шоста фраза тут."
        ],
    }
    queries = _extract_search_queries(section)
    assert len(queries) <= 4


def test_extract_grade_hint():
    plan = {
        "references": [
            {"title": "Большакова Grade 1, p.24", "notes": "test"},
            {"title": "Вашуленко Grade 3, p.112", "notes": "test"},
        ]
    }
    assert _extract_grade_hint(plan) == 1  # minimum grade

    plan_no_refs = {"references": []}
    assert _extract_grade_hint(plan_no_refs) is None


def test_format_hit():
    hit = {
        "text": "Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери. Голосні звуки утворюються за допомогою голосу.",
        "grade": 1,
        "author": "bolshakova",
        "page": "24",
        "score": 0.85,
        "chunk_id": "test-chunk-001",
    }
    result = _format_hit(hit)
    assert "> **Source:** Grade 1, bolshakova, p.24" in result
    assert "Ми чуємо і вимовляємо звуки" in result
    assert "test-chunk-001" in result


def test_format_hit_empty():
    assert _format_hit({"text": ""}) == ""
    assert _format_hit({"text": "   "}) == ""


def test_format_hit_truncates_long_text():
    hit = {
        "text": "А" * 500,
        "grade": 1,
        "author": "test",
        "page": "1",
        "score": 0.5,
        "chunk_id": "c1",
    }
    result = _format_hit(hit)
    assert "..." in result
    # Text portion should be truncated
    assert len(result) < 600


# --- Integration test with mocked RAG ---


def _mock_search_text(query, grade=None, limit=5):
    """Return fake RAG results for testing."""
    return [
        {
            "text": f"Textbook content for: {query}",
            "grade": grade or 1,
            "author": "test-author",
            "page": "42",
            "score": 0.75,
            "chunk_id": f"mock-{hash(query) % 1000}",
        }
    ]


def test_build_packet_structure(tmp_path):
    """Test that build_packet produces correct structure."""
    plan = {
        "module": "a1-001",
        "level": "A1",
        "sequence": 1,
        "slug": "test-module",
        "title": "Test Module",
        "content_outline": [
            {
                "section": "Перший розділ (First Section)",
                "words": 300,
                "points": ["Голосні звуки в українській мові."],
            },
            {
                "section": "Другий розділ (Second Section)",
                "words": 300,
                "points": ["Приголосні звуки."],
            },
        ],
        "references": [
            {"title": "Test Grade 2, p.10", "notes": "test ref"},
        ],
    }

    plan_path = tmp_path / "test-module.yaml"
    plan_path.write_text(yaml.dump(plan, allow_unicode=True), "utf-8")

    with patch("build.research.build_knowledge_packet._search_rag", _mock_search_text):
        result = build_packet(plan_path)

    # Check structure
    assert "# Knowledge Packet: Test Module" in result
    assert "### Перший розділ (First Section)" in result
    assert "### Другий розділ (Second Section)" in result
    assert "> **Source:**" in result
    assert "## Plan References" in result
    assert "Test Grade 2, p.10" in result


def test_build_packet_no_rag(tmp_path):
    """Test graceful degradation when RAG is unavailable."""
    plan = {
        "module": "a1-001",
        "level": "A1",
        "sequence": 1,
        "slug": "test-module",
        "title": "Test Module",
        "content_outline": [
            {
                "section": "Test Section",
                "words": 300,
                "points": ["Simple point."],
            },
        ],
        "references": [],
    }

    plan_path = tmp_path / "test-module.yaml"
    plan_path.write_text(yaml.dump(plan, allow_unicode=True), "utf-8")

    def _failing_search(*args, **kwargs):
        raise ConnectionError("RAG not running")

    with patch("build.research.build_knowledge_packet._search_rag", _failing_search):
        result = build_packet(plan_path)

    # Should still produce output without crashing
    assert "# Knowledge Packet: Test Module" in result
    # No Cyrillic in points → no queries → "No search queries extracted"
    assert "0 textbook excerpts" in result
