"""Tests for pipeline_lib textbook prefetch functions.

These functions prepare textbook grounding content for Gemini prompts.
They depend on RAG (search_text) which we mock to avoid needing Qdrant.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, "scripts")


# Minimal ModuleContext for testing — mirrors the real dataclass fields we use
@dataclass
class FakeContext:
    track: str = "a1"
    module_num: int = 47
    slug: str = "imperative-and-requests"
    mode: str = "full"
    paths: dict = field(default_factory=dict)
    orch_dir: Path = field(default=Path("."))
    plan: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)
    word_target: int = 1200
    topic_title: str = "Imperative and Requests"
    content_outline: list = field(default_factory=list)


def _make_hit(chunk_id: str, text: str, grade: int = 7, author: str = "avramenko"):
    """Create a fake RAG search result."""
    return {
        "chunk_id": chunk_id,
        "text": text,
        "grade": grade,
        "author": author,
        "section_title": f"Сторінка {grade}0",
        "section": f"Сторінка {grade}0",
    }


# Exercise text that contains marker verbs (will pass the filter)
EXERCISE_TEXT = "Утворіть усі можливі форми наказового способу. Запишіть їх."
# Text without exercise markers (will be filtered out)
NON_EXERCISE_TEXT = "Наказовий спосіб означає наказ, прохання і спонукання до дії."


class TestGetTextbookGrade:
    """Tests for _get_textbook_grade."""

    def test_a1_early(self):
        from pipeline_lib import _get_textbook_grade
        ctx = FakeContext(track="a1", module_num=5)
        assert _get_textbook_grade(ctx) == "1-2"

    def test_a1_late(self):
        from pipeline_lib import _get_textbook_grade
        ctx = FakeContext(track="a1", module_num=47)
        assert _get_textbook_grade(ctx) == "3-5"

    def test_a2(self):
        from pipeline_lib import _get_textbook_grade
        ctx = FakeContext(track="a2", module_num=10)
        assert _get_textbook_grade(ctx) == "3-5"

    def test_b1(self):
        from pipeline_lib import _get_textbook_grade
        ctx = FakeContext(track="b1", module_num=1)
        assert _get_textbook_grade(ctx) == "5-7"

    def test_b2(self):
        from pipeline_lib import _get_textbook_grade
        ctx = FakeContext(track="b2", module_num=1)
        assert _get_textbook_grade(ctx) == "8-9"

    def test_c1(self):
        from pipeline_lib import _get_textbook_grade
        ctx = FakeContext(track="c1", module_num=1)
        assert _get_textbook_grade(ctx) == "9-10"

    def test_c2(self):
        from pipeline_lib import _get_textbook_grade
        ctx = FakeContext(track="c2", module_num=1)
        assert _get_textbook_grade(ctx) == "10-11"

    def test_hist(self):
        from pipeline_lib import _get_textbook_grade
        ctx = FakeContext(track="hist", module_num=1)
        assert _get_textbook_grade(ctx) == "9-11"

    def test_bio(self):
        from pipeline_lib import _get_textbook_grade
        ctx = FakeContext(track="bio", module_num=1)
        assert _get_textbook_grade(ctx) == "9-11"


class TestPrefetchActivityExamples:
    """Tests for _prefetch_textbook_activity_examples."""

    def test_returns_empty_when_rag_unavailable(self):
        """When RAG import fails, return empty string."""
        from pipeline_lib import _prefetch_textbook_activity_examples
        ctx = FakeContext()
        with patch.dict("sys.modules", {"rag.query": None}):
            with patch("builtins.__import__", side_effect=ImportError):
                result = _prefetch_textbook_activity_examples(ctx)
        assert result == ""

    def test_a1_m15_plus_uses_targeted_grades(self):
        """A1 M15+ should search grades 3,5,6,7 (where grammar is taught)."""

        ctx = FakeContext(
            track="a1", module_num=47,
            content_outline=[
                {"section": "Наказовий спосіб (Imperative mood)"},
                {"section": "Вісім обов'язкових дієслів (Eight required verbs)"},
            ]
        )

        mock_search = MagicMock(return_value=[
            _make_hit("chunk1", EXERCISE_TEXT, grade=7),
        ])

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": MagicMock(search_text=mock_search)}):
            with patch("pipeline_lib.search_text", mock_search, create=True):
                import importlib

                import pipeline_lib
                importlib.reload(pipeline_lib)
                result = pipeline_lib._prefetch_textbook_activity_examples(ctx)

        # Should have called search_text with grades from [3, 5, 6, 7]
        call_args_list = mock_search.call_args_list
        assert len(call_args_list) > 0
        grades_used = {call.kwargs.get("grade") for call in call_args_list}
        assert grades_used <= {3, 5, 6, 7}, f"Expected grades from [3,5,6,7], got {grades_used}"

    def test_a1_m15_plus_uses_section_titles_as_queries(self):
        """A1 M15+ should derive search terms from content_outline section titles."""

        ctx = FakeContext(
            track="a1", module_num=47,
            content_outline=[
                {"section": "Наказовий спосіб (Imperative mood)"},
                {"section": "Ввічливе прохання (Polite requests)"},
            ]
        )

        mock_search = MagicMock(return_value=[
            _make_hit("chunk1", EXERCISE_TEXT),
        ])

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": MagicMock(search_text=mock_search)}):
            import importlib

            import pipeline_lib
            importlib.reload(pipeline_lib)
            result = pipeline_lib._prefetch_textbook_activity_examples(ctx)

        # Check that section titles were used as search terms
        search_queries = [call[0][0] for call in mock_search.call_args_list]
        assert any("Наказовий спосіб" in q for q in search_queries)

    def test_a1_early_uses_bukvar(self):
        """A1 M1-14 should search bukvar with grades 1-2."""

        ctx = FakeContext(track="a1", module_num=5)
        mock_search = MagicMock(return_value=[])

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": MagicMock(search_text=mock_search)}):
            import importlib

            import pipeline_lib
            importlib.reload(pipeline_lib)
            pipeline_lib._prefetch_textbook_activity_examples(ctx)

        # Should search with grade=1 or grade=2, subject=bukvar
        for call in mock_search.call_args_list:
            assert call.kwargs.get("grade") in (1, 2)
            assert call.kwargs.get("subject") == "bukvar"

    def test_filters_non_exercise_content(self):
        """Chunks without exercise marker verbs should be filtered out."""

        ctx = FakeContext(
            track="b1", module_num=10,
            content_outline=[{"section": "Морфологія"}]
        )

        mock_search = MagicMock(return_value=[
            _make_hit("no_exercise", NON_EXERCISE_TEXT),
        ])

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": MagicMock(search_text=mock_search)}):
            import importlib

            import pipeline_lib
            importlib.reload(pipeline_lib)
            result = pipeline_lib._prefetch_textbook_activity_examples(ctx)

        assert result == ""  # Filtered out because no exercise markers

    def test_grade_label_formatting(self):
        """Grade label in output must show actual grades, not None."""

        ctx = FakeContext(
            track="a1", module_num=47,
            content_outline=[{"section": "Наказовий спосіб (Imperative mood)"}]
        )

        mock_search = MagicMock(return_value=[
            _make_hit("chunk1", EXERCISE_TEXT, grade=7),
        ])

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": MagicMock(search_text=mock_search)}):
            import importlib

            import pipeline_lib
            importlib.reload(pipeline_lib)
            result = pipeline_lib._prefetch_textbook_activity_examples(ctx)

        # Must not crash, and should not contain "grade None"
        assert "None" not in result
        assert "### Real Textbook Exercises" in result

    def test_deduplicates_chunks(self):
        """Same chunk_id from different search terms should not appear twice."""

        ctx = FakeContext(
            track="b1", module_num=10,
            content_outline=[{"section": "Test1"}, {"section": "Test2"}]
        )

        # Return same chunk for both queries
        mock_search = MagicMock(return_value=[
            _make_hit("same_chunk", EXERCISE_TEXT),
        ])

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": MagicMock(search_text=mock_search)}):
            import importlib

            import pipeline_lib
            importlib.reload(pipeline_lib)
            result = pipeline_lib._prefetch_textbook_activity_examples(ctx)

        # Chunk should appear only once
        assert result.count("same_chunk") <= 1

    def test_caps_at_5_results(self):
        """Should return at most 5 textbook exercise blocks."""

        ctx = FakeContext(
            track="b1", module_num=10,
            content_outline=[{"section": f"Section {i}"} for i in range(5)]
        )

        mock_search = MagicMock(return_value=[
            _make_hit(f"chunk_{i}", EXERCISE_TEXT + f" {i}")
            for i in range(10)
        ])

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": MagicMock(search_text=mock_search)}):
            import importlib

            import pipeline_lib
            importlib.reload(pipeline_lib)
            result = pipeline_lib._prefetch_textbook_activity_examples(ctx)

        # Count result blocks by their header pattern (each starts with **Grade)
        assert result.count("**Grade") <= 5


class TestPrefetchTextbookExamples:
    """Tests for _prefetch_textbook_examples."""

    def test_returns_empty_when_rag_unavailable(self):
        from pipeline_lib import _prefetch_textbook_examples
        ctx = FakeContext()
        ctx.content_outline = []
        ctx.plan = {}
        ctx.meta = {}
        ctx.slug = ""
        ctx.topic_title = ""
        # No search terms and no RAG → empty
        result = _prefetch_textbook_examples(ctx)
        assert result == ""

    def test_a1_m15_plus_searches_grammar_grades(self):
        """A1 M15+ should search higher grades first, no subject filter."""

        ctx = FakeContext(
            track="a1", module_num=20,
            content_outline=[{"section": "Минулий час (Past tense)"}],
            plan={"keywords": ["минулий час"]},
        )

        mock_search = MagicMock(return_value=[
            _make_hit("chunk1", "Дієслова минулого часу змінюються за родами.", grade=4),
        ])

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": MagicMock(search_text=mock_search)}):
            import importlib

            import pipeline_lib
            importlib.reload(pipeline_lib)
            result = pipeline_lib._prefetch_textbook_examples(ctx)

        # Subject filter dropped (Grade 4 books lack metadata), grades 7→3
        for call in mock_search.call_args_list:
            assert call.kwargs.get("subject") is None
            assert call.kwargs.get("grade") in [3, 4, 5, 6, 7]

    def test_uses_plan_keywords_as_search_terms(self):
        """Should use plan keywords first, then section titles."""

        ctx = FakeContext(
            track="b1", module_num=10,
            plan={"keywords": ["відмінювання", "іменник"]},
            content_outline=[{"section": "Родовий відмінок"}],
        )

        mock_search = MagicMock(return_value=[])

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": MagicMock(search_text=mock_search)}):
            import importlib

            import pipeline_lib
            importlib.reload(pipeline_lib)
            pipeline_lib._prefetch_textbook_examples(ctx)

        queries = [call[0][0] for call in mock_search.call_args_list]
        # Plan keywords should appear in search queries
        assert any("відмінювання" in q for q in queries)

    def test_strips_english_parenthetical_from_section_titles(self):
        """Section titles like 'Наказовий спосіб (The Imperative Mood)' should
        search only the Ukrainian part 'Наказовий спосіб'."""

        ctx = FakeContext(
            track="a1", module_num=47,
            plan={},
            content_outline=[
                {"section": "Наказовий спосіб (The Imperative Mood)"},
                {"section": "Ввічливе прохання (Polite Requests)"},
            ],
        )

        mock_search = MagicMock(return_value=[])

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": MagicMock(search_text=mock_search)}):
            import importlib

            import pipeline_lib
            importlib.reload(pipeline_lib)
            pipeline_lib._prefetch_textbook_examples(ctx)

        queries = [call[0][0] for call in mock_search.call_args_list]
        # Should NOT contain English text
        for q in queries:
            assert "Imperative" not in q, f"English leaked into search query: {q}"
            assert "Polite" not in q, f"English leaked into search query: {q}"
        # Should contain Ukrainian parts
        assert any("Наказовий спосіб" in q for q in queries)
        assert any("Ввічливе прохання" in q for q in queries)

    def test_handles_english_first_emdash_titles(self):
        """Section titles like 'Capstone — Комплексний проєкт' should
        extract the Ukrainian part after the em-dash."""

        ctx = FakeContext(
            track="b2", module_num=10,
            plan={},
            content_outline=[
                {"section": "Capstone — Комплексний академічний проєкт"},
            ],
        )

        mock_search = MagicMock(return_value=[])

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": MagicMock(search_text=mock_search)}):
            import importlib

            import pipeline_lib
            importlib.reload(pipeline_lib)
            pipeline_lib._prefetch_textbook_examples(ctx)

        queries = [call[0][0] for call in mock_search.call_args_list]
        # Should search for the Ukrainian part, not "Capstone"
        assert any("Комплексний" in q for q in queries)
        for q in queries:
            assert q != "Capstone", f"English-only query leaked: {q}"
