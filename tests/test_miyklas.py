"""Tests for scripts/build/miyklas.py — МійКлас grammar integration (#1040).

Covers: _tokenize, _extract_plan_keywords, find_matching_topics,
        build_miyklas_resource_entries, build_miyklas_knowledge_section.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.miyklas import (
    _extract_plan_keywords,
    _tokenize,
    build_miyklas_knowledge_section,
    build_miyklas_resource_entries,
    find_matching_topics,
)

# ---------------------------------------------------------------------------
# Fixtures — synthetic index entries used across tests
# ---------------------------------------------------------------------------

_FAKE_INDEX = [
    {
        "title": "Голосні й приголосні звуки",
        "tags": ["звуки", "голосні", "приголосні", "фонетика", "phonetics", "vowels", "consonants", "sounds"],
        "url": "/p/ukrainska-mova/5-klas/fonetika/golosni-i-prigolosni-zvuki",
        "grade": 5,
        "category": "phonetics",
    },
    {
        "title": "Наголос",
        "tags": ["наголос", "stress", "accent"],
        "url": "/p/ukrainska-mova/5-klas/fonetika/nagolos",
        "grade": 5,
        "category": "phonetics",
    },
    {
        "title": "Іменник як частина мови",
        "tags": ["іменник", "частини", "мови", "noun", "morphology"],
        "url": "/p/ukrainska-mova/6-klas/morfologiia/imennyk",
        "grade": 6,
        "category": "morphology",
    },
    {
        "title": "Дієслово: час і спосіб",
        "tags": ["дієслово", "час", "спосіб", "verb", "tense", "mood"],
        "url": "/p/ukrainska-mova/7-klas/morfologiia/diieslovo",
        "grade": 7,
        "category": "morphology",
    },
    {
        "title": "Складне речення",
        "tags": ["складне", "речення", "syntax", "sentence"],
        "url": "/p/ukrainska-mova/9-klas/syntaksys/skladne-rechennia",
        "grade": 9,
        "category": "syntax",
    },
]


def _mock_load_index() -> list[dict]:
    return list(_FAKE_INDEX)


# ---------------------------------------------------------------------------
# _tokenize — text normalization
# ---------------------------------------------------------------------------


class TestTokenize:
    def test_basic_ukrainian(self):
        tokens = _tokenize("Голосні й приголосні звуки")
        assert "голосні" in tokens
        assert "приголосні" in tokens
        assert "звуки" in tokens

    def test_strips_english_parenthetical(self):
        tokens = _tokenize("Іменник (Nouns)")
        assert "іменник" in tokens
        # The parenthetical content is removed
        assert "nouns" not in tokens

    def test_strips_punctuation(self):
        tokens = _tokenize("м'які, тверді — дзвінкі!")
        assert "м'які" not in tokens  # apostrophe stripped → мякі
        assert "тверді" in tokens
        assert "дзвінкі" in tokens

    def test_short_tokens_excluded(self):
        """Tokens with 2 or fewer characters are discarded."""
        tokens = _tokenize("а в і це слово")
        assert "а" not in tokens
        assert "в" not in tokens
        assert "і" not in tokens
        assert "це" not in tokens
        assert "слово" in tokens

    def test_empty_string(self):
        assert _tokenize("") == set()

    def test_all_short_tokens(self):
        assert _tokenize("а б в") == set()

    def test_mixed_languages(self):
        tokens = _tokenize("nouns іменник")
        assert "nouns" in tokens
        assert "іменник" in tokens

    def test_nested_parentheses(self):
        tokens = _tokenize("Тема (Topic (extra))")
        # After regex strips parenthetical, "тема" remains
        assert "тема" in tokens

    def test_lowercased(self):
        tokens = _tokenize("ЗВУКИ Фонетика")
        assert "звуки" in tokens
        assert "фонетика" in tokens


# ---------------------------------------------------------------------------
# _extract_plan_keywords — keyword extraction from plan dict
# ---------------------------------------------------------------------------


class TestExtractPlanKeywords:
    def test_grammar_field(self):
        plan = {"grammar": ["Голосні і приголосні звуки", "Наголос"]}
        kw = _extract_plan_keywords(plan)
        assert "голосні" in kw
        assert "приголосні" in kw
        assert "звуки" in kw
        assert "наголос" in kw

    def test_focus_field(self):
        plan = {"focus": "phonetics"}
        kw = _extract_plan_keywords(plan)
        assert "phonetics" in kw

    def test_content_outline_sections(self):
        plan = {
            "content_outline": [
                {"section": "Іменник (Nouns)", "words": 300, "points": []},
            ]
        }
        kw = _extract_plan_keywords(plan)
        assert "іменник" in kw
        # English parenthetical stripped
        assert "nouns" not in kw

    def test_empty_plan(self):
        assert _extract_plan_keywords({}) == set()

    def test_non_string_grammar_items_ignored(self):
        plan = {"grammar": [42, None, "Наголос"]}
        kw = _extract_plan_keywords(plan)
        assert "наголос" in kw

    def test_combined_sources(self):
        plan = {
            "grammar": ["Дієслово"],
            "focus": "morphology",
            "content_outline": [
                {"section": "Час і спосіб дієслова (Verb tense and mood)"},
            ],
        }
        kw = _extract_plan_keywords(plan)
        assert "дієслово" in kw
        assert "morphology" in kw
        assert "спосіб" in kw


# ---------------------------------------------------------------------------
# find_matching_topics — scoring + filtering
# ---------------------------------------------------------------------------


class TestFindMatchingTopics:
    @patch("build.miyklas._load_index", _mock_load_index)
    def test_basic_match(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        results = find_matching_topics(plan)
        assert len(results) >= 1
        assert results[0]["title"] == "Голосні й приголосні звуки"

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_grade_proximity_bonus(self):
        """A1 maps to grades 5-6; grade-5 entry should get bonus."""
        plan = {
            "grammar": ["Голосні звуки"],
            "level": "a1",
        }
        results = find_matching_topics(plan)
        for r in results:
            if r["grade"] == 5:
                # Score includes grade bonus
                assert r["score"] >= 2

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_category_bonus(self):
        """Focus=phonetics should boost phonetics-category entries."""
        plan = {
            "grammar": ["звуки"],
            "focus": "phonetics",
            "level": "a1",
        }
        results = find_matching_topics(plan)
        phonetics_scores = [r["score"] for r in results if r["category"] == "phonetics"]
        assert len(phonetics_scores) >= 1

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_minimum_threshold_filters_noise(self):
        """Single-word overlap with score < 2 is excluded."""
        plan = {
            "grammar": ["sentence"],  # only overlaps with "sentence" tag in index
            "level": "c1",
        }
        results = find_matching_topics(plan)
        # "sentence" alone = 1 overlap; grade 9 matches c1 band (9-11) → +1 = score 2
        # So it might still pass threshold if grade matches; verify no false positives
        for r in results:
            assert r["score"] >= 2

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_max_results_limit(self):
        plan = {
            "grammar": ["звуки", "голосні", "приголосні", "фонетика"],
            "level": "a1",
        }
        results = find_matching_topics(plan, max_results=2)
        assert len(results) <= 2

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_empty_plan_returns_empty(self):
        results = find_matching_topics({})
        assert results == []

    @patch("build.miyklas._load_index", return_value=[])
    def test_empty_index_returns_empty(self, _mock):
        plan = {"grammar": ["Голосні звуки"]}
        results = find_matching_topics(plan)
        assert results == []

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_no_overlap_returns_empty(self):
        plan = {"grammar": ["xyznonexistent"]}
        results = find_matching_topics(plan)
        assert results == []

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_results_sorted_by_score_desc(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки", "фонетика"],
            "focus": "phonetics",
            "level": "a1",
        }
        results = find_matching_topics(plan)
        if len(results) >= 2:
            scores = [r["score"] for r in results]
            assert scores == sorted(scores, reverse=True)

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_url_gets_base_prefix(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        results = find_matching_topics(plan)
        assert len(results) >= 1
        assert results[0]["url"].startswith("https://miyklas.com.ua/")

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_unknown_level_uses_full_range(self):
        """Unknown CEFR level defaults to (5, 11) range."""
        plan = {
            "grammar": ["Голосні звуки"],
            "level": "x9",  # not in _LEVEL_GRADE_MAP
        }
        results = find_matching_topics(plan)
        # Should still work, just no grade bonus for entries outside default
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# build_miyklas_resource_entries — resource tab entries
# ---------------------------------------------------------------------------


class TestBuildResourceEntries:
    @patch("build.miyklas._load_index", _mock_load_index)
    def test_returns_list_of_dicts(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        entries = build_miyklas_resource_entries(plan)
        assert isinstance(entries, list)
        if entries:
            entry = entries[0]
            assert "title" in entry
            assert "url" in entry
            assert "source" in entry
            assert "type" in entry

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_title_prefixed_with_miyklas(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        entries = build_miyklas_resource_entries(plan)
        assert len(entries) >= 1
        assert entries[0]["title"].startswith("МійКлас: ")

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_source_is_domain(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        entries = build_miyklas_resource_entries(plan)
        for e in entries:
            assert e["source"] == "miyklas.com.ua"

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_type_is_articles(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        entries = build_miyklas_resource_entries(plan)
        for e in entries:
            assert e["type"] == "articles"

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_max_3_entries(self):
        plan = {
            "grammar": ["звуки", "голосні", "приголосні", "фонетика", "наголос"],
            "level": "a1",
        }
        entries = build_miyklas_resource_entries(plan)
        assert len(entries) <= 3

    @patch("build.miyklas._load_index", return_value=[])
    def test_no_index_returns_empty(self, _mock):
        plan = {"grammar": ["Голосні звуки"]}
        entries = build_miyklas_resource_entries(plan)
        assert entries == []


# ---------------------------------------------------------------------------
# build_miyklas_knowledge_section — knowledge packet markdown
# ---------------------------------------------------------------------------


class TestBuildKnowledgeSection:
    @patch("build.miyklas._load_index", _mock_load_index)
    def test_returns_markdown_with_header(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        section = build_miyklas_knowledge_section(plan)
        assert "## МійКлас Grammar References" in section

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_contains_matched_topic_titles(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        section = build_miyklas_knowledge_section(plan)
        assert "Голосні й приголосні звуки" in section

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_contains_miyklas_links(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        section = build_miyklas_knowledge_section(plan)
        assert "[МійКлас](" in section
        assert "miyklas.com.ua" in section

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_contains_grade_info(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        section = build_miyklas_knowledge_section(plan)
        assert "Grade 5" in section

    @patch("build.miyklas._load_index", return_value=[])
    def test_empty_index_returns_empty_string(self, _mock):
        plan = {"grammar": ["Голосні звуки"]}
        section = build_miyklas_knowledge_section(plan)
        assert section == ""

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_no_matches_returns_empty_string(self):
        plan = {"grammar": ["xyznonexistent"]}
        section = build_miyklas_knowledge_section(plan)
        assert section == ""

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_max_5_entries(self):
        plan = {
            "grammar": ["звуки", "голосні", "приголосні", "фонетика", "наголос", "іменник", "дієслово"],
            "level": "a1",
        }
        section = build_miyklas_knowledge_section(plan)
        # Count bullet points
        bullets = [line for line in section.split("\n") if line.startswith("- **")]
        assert len(bullets) <= 5

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_has_webfetch_instruction(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        section = build_miyklas_knowledge_section(plan)
        assert "WebFetch" in section

    @patch("build.miyklas._load_index", _mock_load_index)
    def test_starts_with_separator(self):
        plan = {
            "grammar": ["Голосні і приголосні звуки"],
            "level": "a1",
        }
        section = build_miyklas_knowledge_section(plan)
        assert "---" in section


# ---------------------------------------------------------------------------
# _load_index — file loading edge cases (tested via find_matching_topics)
# ---------------------------------------------------------------------------


class TestLoadIndex:
    def test_nonexistent_index_returns_empty(self, tmp_path):
        """When the index file doesn't exist, _load_index returns []."""
        with patch("build.miyklas._INDEX_PATH", tmp_path / "nonexistent.yaml"):
            from build.miyklas import _load_index
            result = _load_index()
            assert result == []

    def test_malformed_yaml_returns_empty(self, tmp_path):
        """Malformed YAML file gracefully returns []."""
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text(": : : invalid yaml [[[", "utf-8")
        with patch("build.miyklas._INDEX_PATH", bad_file):
            from build.miyklas import _load_index
            result = _load_index()
            assert result == []

    def test_yaml_without_topics_key_returns_empty(self, tmp_path):
        """YAML file that lacks 'topics' key returns []."""
        no_topics = tmp_path / "no_topics.yaml"
        no_topics.write_text("version: '1.0'\nsource: test\n", "utf-8")
        with patch("build.miyklas._INDEX_PATH", no_topics):
            from build.miyklas import _load_index
            result = _load_index()
            assert result == []
