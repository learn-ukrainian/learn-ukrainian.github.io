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
    _heuristic_score,
    _is_exercise_chunk,
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


# --- Heuristic reranking tests (#1098) ---


def test_is_exercise_chunk_detects_exercises():
    exercise_text = (
        "Вправа 42\n"
        "1. Прочитайте текст і випишіть іменники.\n"
        "2. Визначте рід і число кожного іменника.\n"
        "3. Запишіть слова у зошит.\n"
    )
    assert _is_exercise_chunk(exercise_text) is True


def test_is_exercise_chunk_passes_theory():
    theory_text = (
        "Іменник — це самостійна частина мови, яка називає предмет "
        "і відповідає на питання хто? що? Іменники бувають трьох родів: "
        "чоловічого, жіночого і середнього."
    )
    assert _is_exercise_chunk(theory_text) is False


def test_is_exercise_chunk_single_marker_passes():
    """A single exercise marker doesn't trigger — it might be an example."""
    text = "Прочитайте правило у рамці. Іменник називає предмет."
    assert _is_exercise_chunk(text) is False


def test_heuristic_score_priority_author_early():
    hit = {"author": "bolshakova", "grade": 1, "text": "Theory text " * 100}
    score = _heuristic_score(hit, grade_hint=1)
    assert score > 0.2  # Author boost + grade match + length bonus


def test_heuristic_score_priority_author_late():
    hit = {"author": "avramenko", "grade": 7, "text": "Theory text " * 100}
    score = _heuristic_score(hit, grade_hint=7)
    assert score > 0.2


def test_heuristic_score_exercise_penalty():
    hit = {
        "author": "unknown",
        "grade": 5,
        "text": "Вправа 1\nСпишіть слова.\nЗапишіть речення.\nВипишіть іменники.\nВизначте рід.",
    }
    score = _heuristic_score(hit, grade_hint=1)
    # Exercise penalty with no boosts → negative
    assert score < 0.0


def test_heuristic_score_grade_mismatch():
    hit = {"author": "unknown", "grade": 11, "text": "Short text"}
    score = _heuristic_score(hit, grade_hint=1)
    assert score == 0.0  # No boosts, no penalties


def test_heuristic_score_adjacent_grade():
    hit = {"author": "unknown", "grade": 2, "text": "Short text"}
    score = _heuristic_score(hit, grade_hint=1)
    assert score == 0.05  # Adjacent grade boost only


def test_heuristic_reranking_reorders_results():
    """Priority author should outrank a higher-scored non-priority hit."""
    from unittest.mock import patch as _patch

    hits = [
        {"text": "Generic content " * 50, "grade": 1, "author": "unknown",
         "score": 0.90, "chunk_id": "c1", "page": "1"},
        {"text": "Priority author content " * 50, "grade": 1, "author": "bolshakova",
         "score": 0.85, "chunk_id": "c2", "page": "2"},
    ]

    def mock_search(query, grade=None, limit=5):
        return [dict(h) for h in hits]  # Return copies

    with _patch("build.research.build_knowledge_packet._search_rag.__wrapped__", mock_search, create=True):
        # Test via _heuristic_score directly — cleaner than mocking imports
        pass

    # Direct test: apply heuristic scores and verify reordering
    for h in hits:
        h["final_score"] = h["score"] + _heuristic_score(h, grade_hint=1)

    hits.sort(key=lambda x: x["final_score"], reverse=True)
    # bolshakova (0.85 + 0.25 boost = 1.10) should outrank unknown (0.90 + 0.10 = 1.00)
    assert hits[0]["author"] == "bolshakova"


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


# --- МійКлас integration tests (#1040) ---


_FAKE_MIYKLAS_INDEX = [
    {
        "title": "Голосні й приголосні звуки",
        "tags": ["звуки", "голосні", "приголосні", "фонетика"],
        "url": "/p/ukrainska-mova/5-klas/fonetika/golosni",
        "grade": 5,
        "category": "phonetics",
    },
]


def test_build_packet_includes_miyklas_section(tmp_path):
    """build_packet appends МійКлас section when grammar matches."""
    plan = {
        "module": "a1-001",
        "level": "A1",
        "sequence": 1,
        "slug": "test-phonetics",
        "title": "Test Phonetics Module",
        "grammar": ["Голосні і приголосні звуки"],
        "focus": "phonetics",
        "content_outline": [
            {
                "section": "Звуки (Sounds)",
                "words": 300,
                "points": ["Голосні та приголосні звуки української мови."],
            },
        ],
        "references": [],
    }

    plan_path = tmp_path / "test-phonetics.yaml"
    plan_path.write_text(yaml.dump(plan, allow_unicode=True), "utf-8")

    with (
        patch("build.research.build_knowledge_packet._search_rag", _mock_search_text),
        patch("build.miyklas._load_index", return_value=list(_FAKE_MIYKLAS_INDEX)),
    ):
        result = build_packet(plan_path)

    assert "МійКлас Grammar References" in result
    assert "Голосні й приголосні звуки" in result
    assert "miyklas.com.ua" in result


def test_build_packet_no_miyklas_when_no_grammar_match(tmp_path):
    """build_packet omits МійКлас section when no grammar overlap."""
    plan = {
        "module": "a1-001",
        "level": "A1",
        "sequence": 1,
        "slug": "test-greetings",
        "title": "Test Greetings Module",
        "content_outline": [
            {
                "section": "Привітання (Greetings)",
                "words": 300,
                "points": ["Привіт, як справи?"],
            },
        ],
        "references": [],
    }

    plan_path = tmp_path / "test-greetings.yaml"
    plan_path.write_text(yaml.dump(plan, allow_unicode=True), "utf-8")

    with (
        patch("build.research.build_knowledge_packet._search_rag", _mock_search_text),
        patch("build.miyklas._load_index", return_value=list(_FAKE_MIYKLAS_INDEX)),
    ):
        result = build_packet(plan_path)

    assert "МійКлас Grammar References" not in result


def test_build_packet_miyklas_failure_graceful(tmp_path):
    """build_packet continues even if miyklas module raises."""
    plan = {
        "module": "a1-001",
        "level": "A1",
        "sequence": 1,
        "slug": "test-fallback",
        "title": "Test Fallback",
        "grammar": ["Голосні звуки"],
        "content_outline": [
            {
                "section": "Звуки (Sounds)",
                "words": 300,
                "points": ["Голосні звуки в українській."],
            },
        ],
        "references": [],
    }

    plan_path = tmp_path / "test-fallback.yaml"
    plan_path.write_text(yaml.dump(plan, allow_unicode=True), "utf-8")

    def _failing_miyklas(*args, **kwargs):
        raise RuntimeError("МійКлас unavailable")

    with (
        patch("build.research.build_knowledge_packet._search_rag", _mock_search_text),
        patch("build.miyklas.build_miyklas_knowledge_section", side_effect=_failing_miyklas),
    ):
        result = build_packet(plan_path)

    # Should still produce a valid packet without МійКлас
    assert "# Knowledge Packet: Test Fallback" in result
    assert "МійКлас" not in result


def test_build_packet_miyklas_section_before_footer(tmp_path):
    """МійКлас section appears between refs and footer."""
    plan = {
        "module": "a1-001",
        "level": "A1",
        "sequence": 1,
        "slug": "test-order",
        "title": "Test Order",
        "grammar": ["Голосні і приголосні звуки"],
        "content_outline": [
            {
                "section": "Звуки (Sounds)",
                "words": 300,
                "points": ["Голосні та приголосні звуки."],
            },
        ],
        "references": [
            {"title": "Ref Grade 1, p.10", "notes": "test ref"},
        ],
    }

    plan_path = tmp_path / "test-order.yaml"
    plan_path.write_text(yaml.dump(plan, allow_unicode=True), "utf-8")

    with (
        patch("build.research.build_knowledge_packet._search_rag", _mock_search_text),
        patch("build.miyklas._load_index", return_value=list(_FAKE_MIYKLAS_INDEX)),
    ):
        result = build_packet(plan_path)

    # МійКлас appears after references section and before footer
    miyklas_pos = result.index("МійКлас Grammar References")
    footer_pos = result.index("Knowledge Packet generated")
    assert miyklas_pos < footer_pos
