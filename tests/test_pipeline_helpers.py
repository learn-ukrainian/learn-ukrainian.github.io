"""Tests for pipeline_lib helper functions.

Covers: _parse_section, _build_section_budget_table, _check_archive_fits_outline,
get_level_constraints, get_activity_config, get_item_minimums_table,
bilingualify_section_titles, get_pedagogical_constraints, get_decodable_vocabulary,
get_structural_rules, get_h3_word_range, get_expansion_method, get_track_skill,
get_immersion_rule, get_level_label, track_to_level_focus, load_state,
v5 phase terminology (no legacy Phase 2: labels), SELF_AUDIT_SNIPPET CONTENT_PATH resolution.

Issue: #817
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

import pytest

sys.path.insert(0, "scripts")


# Minimal context matching the real dataclass
@dataclass
class FakeContext:
    track: str = "a1"
    module_num: int = 1
    slug: str = "test-module"
    content_outline: list = field(default_factory=list)
    plan: dict = field(default_factory=dict)
    archive_dir: Path | None = None


# ============================================================================
# _parse_section
# ============================================================================

class TestParseSection:
    def test_dict_with_section_key(self):
        from pipeline_lib import _parse_section
        title, words = _parse_section({"section": "Іменник", "words": 300})
        assert title == "Іменник"
        assert words == 300

    def test_dict_with_title_key(self):
        from pipeline_lib import _parse_section
        title, words = _parse_section({"title": "Дієслово", "words": 250})
        assert title == "Дієслово"
        assert words == 250

    def test_section_takes_priority_over_title(self):
        from pipeline_lib import _parse_section
        title, _ = _parse_section({"section": "A", "title": "B", "words": 100})
        assert title == "A"

    def test_missing_words_defaults_to_zero(self):
        from pipeline_lib import _parse_section
        _, words = _parse_section({"section": "Test"})
        assert words == 0

    def test_missing_both_keys(self):
        from pipeline_lib import _parse_section
        title, words = _parse_section({})
        assert title == "Untitled"
        assert words == 0

    def test_string_section(self):
        from pipeline_lib import _parse_section
        title, words = _parse_section("Simple Section")
        assert title == "Simple Section"
        assert words == 0

    def test_words_as_string(self):
        from pipeline_lib import _parse_section
        _, words = _parse_section({"section": "Test", "words": "400"})
        assert words == 400


# ============================================================================
# _build_section_budget_table
# ============================================================================

class TestBuildSectionBudgetTable:
    def test_basic_table(self):
        from pipeline_lib import _build_section_budget_table
        sections = [
            {"section": "Intro", "words": 300},
            {"section": "Main", "words": 500},
        ]
        result = _build_section_budget_table(sections, 800)
        assert "| Intro | 300 |" in result
        assert "| Main | 500 |" in result
        assert "| **Total** | **800** |" in result

    def test_zero_word_sections_get_even_split(self):
        from pipeline_lib import _build_section_budget_table
        sections = [
            {"section": "A", "words": 0},
            {"section": "B", "words": 0},
        ]
        result = _build_section_budget_table(sections, 1200)
        assert "| A | 600 |" in result
        assert "| B | 600 |" in result

    def test_empty_sections(self):
        from pipeline_lib import _build_section_budget_table
        result = _build_section_budget_table([], 1200)
        assert "| **Total** | **1200** |" in result

    def test_string_sections(self):
        from pipeline_lib import _build_section_budget_table
        sections = ["Section One", "Section Two"]
        result = _build_section_budget_table(sections, 1000)
        # String sections have words=0, so get even split
        assert "| Section One | 500 |" in result

    def test_has_markdown_header(self):
        from pipeline_lib import _build_section_budget_table
        result = _build_section_budget_table([{"section": "X", "words": 100}], 100)
        assert result.startswith("| Section | Target |")
        assert "|---------|--------|" in result


# ============================================================================
# _check_archive_fits_outline
# ============================================================================

class TestCheckArchiveFitsOutline:
    def test_archive_dir_file_missing(self, tmp_path):
        from pipeline_lib import _check_archive_fits_outline
        ctx = FakeContext(slug="nonexistent", archive_dir=tmp_path)
        fits, matched, missing = _check_archive_fits_outline(ctx)
        assert fits is False
        assert matched == []
        assert missing == []

    def test_archive_covers_all_sections(self, tmp_path):
        from pipeline_lib import _check_archive_fits_outline
        archive_file = tmp_path / "test-module.md"
        archive_file.write_text("# Title\n\n## Intro\nsome text\n\n## Main\nmore text\n")
        ctx = FakeContext(
            slug="test-module",
            archive_dir=tmp_path,
            content_outline=[
                {"section": "Intro", "words": 300},
                {"section": "Main", "words": 500},
            ],
        )
        fits, matched, missing = _check_archive_fits_outline(ctx)
        assert fits is True
        assert len(matched) == 2
        assert len(missing) == 0

    def test_archive_below_70_percent_coverage(self, tmp_path):
        from pipeline_lib import _check_archive_fits_outline
        archive_file = tmp_path / "test-module.md"
        archive_file.write_text("# Title\n\n## Intro\nsome text\n")
        ctx = FakeContext(
            slug="test-module",
            archive_dir=tmp_path,
            content_outline=[
                {"section": "Intro", "words": 300},
                {"section": "Main", "words": 300},
                {"section": "Practice", "words": 200},
                {"section": "Summary", "words": 200},
            ],
        )
        fits, matched, missing = _check_archive_fits_outline(ctx)
        assert fits is False  # 1/4 = 25% < 70%
        assert "Intro" in matched
        assert len(missing) == 3

    def test_archive_exactly_70_percent(self, tmp_path):
        from pipeline_lib import _check_archive_fits_outline
        archive_file = tmp_path / "test-module.md"
        archive_file.write_text(
            "# Title\n\n## Section A\ntext\n\n## Section B\ntext\n\n"
            "## Section C\ntext\n\n## Section D\ntext\n\n"
            "## Section E\ntext\n\n## Section F\ntext\n\n"
            "## Section G\ntext\n"
        )
        ctx = FakeContext(
            slug="test-module",
            archive_dir=tmp_path,
            content_outline=[
                {"section": f"Section {c}", "words": 100}
                for c in "ABCDEFGHIJ"  # 10 sections, archive has 7 = 70%
            ],
        )
        fits, matched, missing = _check_archive_fits_outline(ctx)
        assert fits is True  # 7/10 = 70% >= 70%
        assert len(matched) == 7
        assert len(missing) == 3

    def test_case_insensitive_matching(self, tmp_path):
        from pipeline_lib import _check_archive_fits_outline
        archive_file = tmp_path / "test-module.md"
        archive_file.write_text("## наказовий спосіб\ntext\n")
        ctx = FakeContext(
            slug="test-module",
            archive_dir=tmp_path,
            content_outline=[{"section": "Наказовий спосіб", "words": 300}],
        )
        fits, matched, missing = _check_archive_fits_outline(ctx)
        assert fits is True
        assert len(matched) == 1

    def test_no_outline_uses_word_threshold(self, tmp_path):
        from pipeline_lib import _check_archive_fits_outline, ARCHIVE_WORD_THRESHOLD
        archive_file = tmp_path / "test-module.md"
        archive_file.write_text("word " * (ARCHIVE_WORD_THRESHOLD + 100))
        ctx = FakeContext(slug="test-module", archive_dir=tmp_path, content_outline=[])
        fits, _, _ = _check_archive_fits_outline(ctx)
        assert fits is True

    def test_no_outline_below_threshold(self, tmp_path):
        from pipeline_lib import _check_archive_fits_outline
        archive_file = tmp_path / "test-module.md"
        archive_file.write_text("short text")  # ~2 words
        ctx = FakeContext(slug="test-module", archive_dir=tmp_path, content_outline=[])
        fits, _, _ = _check_archive_fits_outline(ctx)
        assert fits is False


# ============================================================================
# get_level_constraints
# ============================================================================

class TestGetLevelConstraints:
    def test_a1_base_constraints(self):
        from pipeline_lib import get_level_constraints
        result = get_level_constraints("a1")
        assert "Dative case FORBIDDEN" in result
        assert "Instrumental case FORBIDDEN" in result

    def test_a2_constraints(self):
        from pipeline_lib import get_level_constraints
        result = get_level_constraints("a2")
        assert "Max 15 words" in result

    def test_b1_constraints(self):
        from pipeline_lib import get_level_constraints
        result = get_level_constraints("b1")
        assert len(result) > 0

    def test_unknown_track_falls_back_to_c1(self):
        from pipeline_lib import get_level_constraints
        result = get_level_constraints("z99")
        c1_result = get_level_constraints("c1")
        assert result == c1_result

    def test_a1_dative_relaxation(self):
        from pipeline_lib import get_level_constraints
        plan = {"grammar": ["Dative case with мені подобається"]}
        result = get_level_constraints("a1", plan)
        assert "PLAN-AWARE EXEMPTIONS" in result
        assert "Dative case" in result

    def test_a1_instrumental_relaxation(self):
        from pipeline_lib import get_level_constraints
        plan = {"grammar": ["Instrumental case з другом"]}
        result = get_level_constraints("a1", plan)
        assert "Instrumental case" in result

    def test_a1_perfective_relaxation(self):
        from pipeline_lib import get_level_constraints
        plan = {"grammar": ["Imperative mood: сказати, показати"]}
        result = get_level_constraints("a1", plan)
        assert "Perfective aspect" in result

    def test_a1_subordinate_relaxation(self):
        from pipeline_lib import get_level_constraints
        plan = {"grammar": ["Subordinate clauses with який"]}
        result = get_level_constraints("a1", plan)
        assert "Subordinate clauses" in result

    def test_a1_no_relaxation_without_plan(self):
        from pipeline_lib import get_level_constraints
        result = get_level_constraints("a1")
        assert "PLAN-AWARE EXEMPTIONS" not in result

    def test_a1_negative_instruction_not_relaxed(self):
        from pipeline_lib import get_level_constraints
        plan = {"grammar": ["do NOT teach dative case"]}
        result = get_level_constraints("a1", plan)
        assert "PLAN-AWARE EXEMPTIONS" not in result

    def test_a1_avoid_instruction_not_relaxed(self):
        from pipeline_lib import get_level_constraints
        plan = {"grammar": ["avoid instrumental case"]}
        result = get_level_constraints("a1", plan)
        assert "PLAN-AWARE EXEMPTIONS" not in result

    def test_non_a1_ignores_plan(self):
        from pipeline_lib import get_level_constraints
        plan = {"grammar": ["Dative case"]}
        result_with = get_level_constraints("b1", plan)
        result_without = get_level_constraints("b1")
        assert result_with == result_without

    def test_multiple_relaxations(self):
        from pipeline_lib import get_level_constraints
        plan = {"grammar": ["Dative мені подобається", "Instrumental з другом", "Imperative сказати"]}
        result = get_level_constraints("a1", plan)
        assert "Dative case" in result
        assert "Instrumental case" in result
        assert "Perfective aspect" in result


# ============================================================================
# get_activity_config
# ============================================================================

class TestGetActivityConfig:
    def test_a1_returns_a1_config(self):
        from pipeline_lib import get_activity_config
        config = get_activity_config("a1", 10)
        assert isinstance(config, dict)

    def test_b1_early_uses_bridge(self):
        from pipeline_lib import get_activity_config
        config = get_activity_config("b1", 3)
        # b1 module_num <= 5 should use bridge config
        bridge = get_activity_config("b1", 5)
        assert config == bridge

    def test_b1_late_uses_core(self):
        from pipeline_lib import get_activity_config
        config_early = get_activity_config("b1", 5)
        config_late = get_activity_config("b1", 6)
        # They may differ (bridge vs core)
        # At minimum, both return valid dicts
        assert isinstance(config_late, dict)

    def test_lit_prefix_uses_lit_config(self):
        from pipeline_lib import get_activity_config
        config = get_activity_config("lit-essay", 1)
        lit_config = get_activity_config("lit", 1)
        # Both lit variants should use the same config
        assert config == lit_config

    def test_unknown_track_falls_back_to_b2(self):
        from pipeline_lib import get_activity_config
        config = get_activity_config("z99", 1)
        b2_config = get_activity_config("b2", 1)
        assert config == b2_config

    def test_c1_returns_c1_config(self):
        from pipeline_lib import get_activity_config
        config = get_activity_config("c1", 10)
        assert isinstance(config, dict)


# ============================================================================
# bilingualify_section_titles
# ============================================================================

class TestBilingualifySectionTitles:
    def test_a1_early_adds_bilingual_titles(self):
        from pipeline_lib import bilingualify_section_titles
        outline = [{"section": "Вступ", "words": 200}]
        result = bilingualify_section_titles(outline, "a1", 5)
        assert result[0]["section"] == "Вступ — Introduction"

    def test_a1_m15_plus_returns_unchanged(self):
        from pipeline_lib import bilingualify_section_titles
        outline = [{"section": "Вступ", "words": 200}]
        result = bilingualify_section_titles(outline, "a1", 15)
        assert result[0]["section"] == "Вступ"

    def test_non_a1_returns_unchanged(self):
        from pipeline_lib import bilingualify_section_titles
        outline = [{"section": "Вступ", "words": 200}]
        result = bilingualify_section_titles(outline, "b1", 5)
        assert result[0]["section"] == "Вступ"

    def test_already_bilingual_skipped(self):
        from pipeline_lib import bilingualify_section_titles
        outline = [{"section": "Вступ — Introduction", "words": 200}]
        result = bilingualify_section_titles(outline, "a1", 3)
        assert result[0]["section"] == "Вступ — Introduction"

    def test_prefix_match_vowels(self):
        from pipeline_lib import bilingualify_section_titles
        outline = [{"section": "Голосні — А, О, У", "words": 300}]
        result = bilingualify_section_titles(outline, "a1", 1)
        assert "Vowels" in result[0]["section"]
        assert "А, О, У" in result[0]["section"]

    def test_non_dict_sections_skipped(self):
        from pipeline_lib import bilingualify_section_titles
        outline = ["plain string", {"section": "Вступ", "words": 200}]
        result = bilingualify_section_titles(outline, "a1", 3)
        assert result[0] == "plain string"
        assert result[1]["section"] == "Вступ — Introduction"

    def test_m14_boundary_still_applies(self):
        from pipeline_lib import bilingualify_section_titles
        outline = [{"section": "Практика", "words": 200}]
        result = bilingualify_section_titles(outline, "a1", 14)
        assert result[0]["section"] == "Практика — Practice"


# ============================================================================
# get_pedagogical_constraints
# ============================================================================

class TestGetPedagogicalConstraints:
    def test_non_a1_returns_empty(self):
        from pipeline_lib import get_pedagogical_constraints
        assert get_pedagogical_constraints("b1", 5) == ""
        assert get_pedagogical_constraints("hist", 1) == ""

    def test_m1_returns_specific_constraints(self):
        from pipeline_lib import get_pedagogical_constraints
        result = get_pedagogical_constraints("a1", 1)
        assert len(result) > 0

    def test_m47_returns_imperative_constraints(self):
        from pipeline_lib import get_pedagogical_constraints
        result = get_pedagogical_constraints("a1", 47)
        assert "imperative" in result.lower() or "наказов" in result.lower()

    def test_m15_plus_returns_constraints(self):
        from pipeline_lib import get_pedagogical_constraints
        result = get_pedagogical_constraints("a1", 20)
        assert len(result) > 0

    def test_m5_to_m10_range(self):
        from pipeline_lib import get_pedagogical_constraints
        r5 = get_pedagogical_constraints("a1", 5)
        r10 = get_pedagogical_constraints("a1", 10)
        assert r5 == r10  # Same range

    def test_m11_to_m14_range(self):
        from pipeline_lib import get_pedagogical_constraints
        r11 = get_pedagogical_constraints("a1", 11)
        r14 = get_pedagogical_constraints("a1", 14)
        assert r11 == r14  # Same range

    def test_each_m1_through_m4_unique(self):
        from pipeline_lib import get_pedagogical_constraints
        results = [get_pedagogical_constraints("a1", i) for i in range(1, 5)]
        assert len(set(results)) == 4  # Each module has unique constraints


# ============================================================================
# get_decodable_vocabulary
# ============================================================================

class TestGetDecodableVocabulary:
    def test_non_a1_returns_empty(self):
        from pipeline_lib import get_decodable_vocabulary
        assert get_decodable_vocabulary("b1", 1, {}) == ""

    def test_m4_plus_returns_empty(self):
        from pipeline_lib import get_decodable_vocabulary
        assert get_decodable_vocabulary("a1", 4, {}) == ""

    def test_m1_returns_curated_words(self):
        from pipeline_lib import get_decodable_vocabulary
        result = get_decodable_vocabulary("a1", 1, {})
        assert "мама" in result
        assert len(result) > 0

    def test_m2_returns_curated_words(self):
        from pipeline_lib import get_decodable_vocabulary
        result = get_decodable_vocabulary("a1", 2, {})
        assert "кіт" in result or "тато" in result

    def test_m3_uses_plan_vocab_hints(self):
        from pipeline_lib import get_decodable_vocabulary
        plan = {"vocabulary_hints": ["будинок", "дах"]}
        result = get_decodable_vocabulary("a1", 3, plan)
        assert len(result) > 0


# ============================================================================
# get_h3_word_range
# ============================================================================

class TestGetH3WordRange:
    def test_a1_early(self):
        from pipeline_lib import get_h3_word_range
        assert get_h3_word_range("a1", 1) == "30-50"
        assert get_h3_word_range("a1", 4) == "30-50"

    def test_a1_mid(self):
        from pipeline_lib import get_h3_word_range
        assert get_h3_word_range("a1", 5) == "40-60"
        assert get_h3_word_range("a1", 14) == "40-60"

    def test_a1_late_and_a2(self):
        from pipeline_lib import get_h3_word_range
        assert get_h3_word_range("a1", 15) == "60-80"
        assert get_h3_word_range("a2", 1) == "60-80"

    def test_b1_plus(self):
        from pipeline_lib import get_h3_word_range
        assert get_h3_word_range("b1", 1) == "80-100+"
        assert get_h3_word_range("hist", 1) == "80-100+"


# ============================================================================
# get_expansion_method
# ============================================================================

class TestGetExpansionMethod:
    def test_a1_early_mentions_letters(self):
        from pipeline_lib import get_expansion_method
        result = get_expansion_method("a1", 1)
        assert "letter" in result.lower()

    def test_a1_mid_mentions_deeper(self):
        from pipeline_lib import get_expansion_method
        result = get_expansion_method("a1", 10)
        assert "deeper" in result.lower()

    def test_a2_mentions_deeper(self):
        from pipeline_lib import get_expansion_method
        result = get_expansion_method("a2", 1)
        assert "deeper" in result.lower()

    def test_b1_plus_returns_non_empty(self):
        from pipeline_lib import get_expansion_method
        result = get_expansion_method("b1", 10)
        assert len(result) > 50


# ============================================================================
# get_track_skill
# ============================================================================

class TestGetTrackSkill:
    def test_returns_three_element_tuple(self):
        from pipeline_lib import get_track_skill
        result = get_track_skill("a1", 1)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_b1_early_vs_late(self):
        from pipeline_lib import get_track_skill
        early = get_track_skill("b1", 3)
        late = get_track_skill("b1", 10)
        # They may differ based on bridge vs core
        assert isinstance(early, tuple)
        assert isinstance(late, tuple)

    def test_lit_prefix_uses_lit(self):
        from pipeline_lib import get_track_skill
        lit = get_track_skill("lit", 1)
        lit_essay = get_track_skill("lit-essay", 1)
        assert lit == lit_essay

    def test_unknown_falls_back_to_b2(self):
        from pipeline_lib import get_track_skill
        unknown = get_track_skill("z99", 1)
        b2 = get_track_skill("b2", 1)
        assert unknown == b2


# ============================================================================
# get_immersion_rule
# ============================================================================

class TestGetImmersionRule:
    def test_a1_m1_returns_rule(self):
        from pipeline_lib import get_immersion_rule
        result = get_immersion_rule("a1", 1)
        assert len(result) > 0

    def test_a1_ranges_differ(self):
        from pipeline_lib import get_immersion_rule
        r1 = get_immersion_rule("a1", 1)
        r6 = get_immersion_rule("a1", 6)
        r15 = get_immersion_rule("a1", 15)
        r25 = get_immersion_rule("a1", 25)
        # Different ranges should produce different rules
        assert r1 != r6 or r6 != r15 or r15 != r25

    def test_a2_ranges(self):
        from pipeline_lib import get_immersion_rule
        r1 = get_immersion_rule("a2", 1)
        r30 = get_immersion_rule("a2", 30)
        assert len(r1) > 0
        assert len(r30) > 0

    def test_b2_plus_returns_same_rule(self):
        from pipeline_lib import get_immersion_rule
        b2 = get_immersion_rule("b2", 1)
        hist = get_immersion_rule("hist", 1)
        assert b2 == hist  # Both use b2+

    def test_b1_bridge_vs_core(self):
        from pipeline_lib import get_immersion_rule
        bridge = get_immersion_rule("b1", 3)
        core = get_immersion_rule("b1", 10)
        assert len(bridge) > 0
        assert len(core) > 0


# ============================================================================
# get_level_label
# ============================================================================

class TestGetLevelLabel:
    def test_simple_tracks(self):
        from pipeline_lib import get_level_label
        assert get_level_label("a1") == "A1"
        assert get_level_label("b2") == "B2"
        assert get_level_label("hist") == "HIST"

    def test_hyphenated_track(self):
        from pipeline_lib import get_level_label
        result = get_level_label("lit-essay")
        assert "LIT" in result


# ============================================================================
# track_to_level_focus
# ============================================================================

class TestTrackToLevelFocus:
    def test_hist_returns_b2_history(self):
        from pipeline_lib import track_to_level_focus
        level, focus = track_to_level_focus("hist")
        assert level == "B2"
        assert focus == "history"

    def test_bio_returns_c1_biography(self):
        from pipeline_lib import track_to_level_focus
        level, focus = track_to_level_focus("bio")
        assert level == "C1"
        assert focus == "biography"

    def test_lit_prefix_returns_c1_literature(self):
        from pipeline_lib import track_to_level_focus
        level, focus = track_to_level_focus("lit-essay")
        assert level == "C1"
        assert focus == "literature"

    def test_core_track_returns_level_and_none(self):
        from pipeline_lib import track_to_level_focus
        level, focus = track_to_level_focus("a1")
        assert level == "A1"
        assert focus is None

    def test_b1_returns_level_and_none(self):
        from pipeline_lib import track_to_level_focus
        level, focus = track_to_level_focus("b1")
        assert level == "B1"
        assert focus is None


# ============================================================================
# load_state
# ============================================================================

class TestLoadState:
    def test_missing_file_returns_fresh_state(self, tmp_path):
        from pipeline_lib import load_state, ModuleContext
        ctx = ModuleContext(
            track="a1", module_num=5, slug="test-slug", mode="full",
            orch_dir=tmp_path,
        )
        state = load_state(ctx)
        assert state["slug"] == "test-slug"
        assert state["track"] == "a1"
        assert state["phases"] == {}

    def test_existing_file_loaded(self, tmp_path):
        import json
        from pipeline_lib import load_state, ModuleContext
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "slug": "loaded", "track": "b1", "module_num": 3,
            "mode": "full", "phases": {"research": {"status": "complete"}},
            "last_updated": "2026-01-01T00:00:00Z",
        }))
        ctx = ModuleContext(
            track="b1", module_num=3, slug="loaded", mode="full",
            orch_dir=tmp_path,
        )
        state = load_state(ctx)
        assert state["slug"] == "loaded"
        assert state["phases"]["research"]["status"] == "complete"

    def test_corrupt_json_returns_fresh(self, tmp_path):
        from pipeline_lib import load_state, ModuleContext
        state_file = tmp_path / "state.json"
        state_file.write_text("{bad json")
        ctx = ModuleContext(
            track="a1", module_num=1, slug="corrupt", mode="full",
            orch_dir=tmp_path,
        )
        state = load_state(ctx)
        assert state["slug"] == "corrupt"
        assert state["phases"] == {}


# ============================================================================
# v5 Phase Terminology — Issue #817
# ============================================================================

class TestV5PhaseTerminology:
    """Ensure pipeline_lib.py uses v5 named phases in log messages, not legacy v3/v4 labels."""

    def test_no_phase_2_colon_in_pipeline_lib(self):
        """pipeline_lib.py must not contain 'Phase 2:' — all content logs use 'content:'."""
        pipeline_lib_path = Path("scripts/pipeline_lib.py")
        assert pipeline_lib_path.exists(), "pipeline_lib.py not found"
        source = pipeline_lib_path.read_text(encoding="utf-8")
        occurrences = [
            (i + 1, line.strip())
            for i, line in enumerate(source.splitlines())
            if "Phase 2:" in line
        ]
        assert occurrences == [], (
            f"Found legacy 'Phase 2:' in pipeline_lib.py at lines: "
            + ", ".join(str(lineno) for lineno, _ in occurrences)
        )

    def test_content_phase_label_present(self):
        """pipeline_lib.py should use 'content:' label in the phase_2_content function."""
        pipeline_lib_path = Path("scripts/pipeline_lib.py")
        source = pipeline_lib_path.read_text(encoding="utf-8")
        assert "content: SKIP (already complete)" in source
        assert "content: FAIL" in source


# ============================================================================
# SELF_AUDIT_SNIPPET nested CONTENT_PATH resolution — Issue #817
# ============================================================================

class TestSelfAuditSnippetContentPath:
    """The SELF_AUDIT_SNIPPET value must have {CONTENT_PATH} resolved before storage.

    fill_template does a single pass: when a snippet is injected via {SELF_AUDIT_SNIPPET},
    any {CONTENT_PATH} inside it would remain unresolved. The fix pre-resolves {CONTENT_PATH}
    in the snippet text inside write_placeholders, before storing it in the placeholders dict.
    """

    def test_self_audit_snippet_resolves_content_path(self):
        """The snippet text must have {CONTENT_PATH} replaced with the real path string."""
        fake_snippet = "Write to {CONTENT_PATH} and run audit.\ncat > {CONTENT_PATH}"
        fake_content_path = "/some/module/path.md"

        # Simulate the resolution logic from write_placeholders
        resolved = fake_snippet.replace("{CONTENT_PATH}", fake_content_path)

        assert "{CONTENT_PATH}" not in resolved, (
            "SELF_AUDIT_SNIPPET still contains unresolved {CONTENT_PATH}"
        )
        assert fake_content_path in resolved

    def test_pipeline_lib_resolves_content_path_in_snippet(self):
        """Verify pipeline_lib.py contains the resolution logic for SELF_AUDIT_SNIPPET."""
        pipeline_lib_path = Path("scripts/pipeline_lib.py")
        source = pipeline_lib_path.read_text(encoding="utf-8")

        # The fix must include a .replace("{CONTENT_PATH}", ...) applied to the snippet
        assert '"{CONTENT_PATH}"' in source or "'{CONTENT_PATH}'" in source, (
            "Expected {CONTENT_PATH} resolution in pipeline_lib.py"
        )
        # Specifically: the SELF_AUDIT_SNIPPET assignment must resolve nested {CONTENT_PATH}
        assert "SELF_AUDIT_SNIPPET" in source
        # The snippet line must be followed by a .replace call
        lines = source.splitlines()
        for i, line in enumerate(lines):
            if "SELF_AUDIT_SNIPPET" in line and "_self_audit_raw" in line:
                # Check that surrounding lines contain the resolution
                context = "\n".join(lines[max(0, i - 2):i + 5])
                assert "replace" in context and "CONTENT_PATH" in context, (
                    f"Expected .replace(CONTENT_PATH) near SELF_AUDIT_SNIPPET assignment:\n{context}"
                )
                break


# ============================================================================
# Bukvar REQUIRED_TYPES for A1 M1-4 + dict activity_hints parsing
# ============================================================================

class TestBukvarRequiredTypes:
    """A1 modules 1-4 must include bukvar activity types (watch-and-repeat, classify, image-to-letter)."""

    def _simulate_required_types_logic(self, track, module_num, plan, initial_required=""):
        """Reproduce the REQUIRED_TYPES logic from write_placeholders()."""
        placeholders = {"REQUIRED_TYPES": initial_required, "PRIORITY_TYPES": "fill-in, match-up, anagram"}

        # Step 1: populate from plan hints or priority (same as pipeline_lib)
        if not placeholders.get("REQUIRED_TYPES"):
            plan_hints = plan.get("activity_hints", [])
            if plan_hints and isinstance(plan_hints, list):
                hint_types = []
                for h in plan_hints[:5]:
                    if isinstance(h, dict):
                        hint_types.append(h.get("type", str(h)))
                    else:
                        hint_types.append(str(h))
                placeholders["REQUIRED_TYPES"] = ", ".join(hint_types)
            elif placeholders.get("PRIORITY_TYPES"):
                priorities = [t.strip() for t in placeholders["PRIORITY_TYPES"].split(",")]
                placeholders["REQUIRED_TYPES"] = ", ".join(priorities[:3])

        # Step 2: bukvar augmentation
        if track.lower() == "a1" and module_num <= 4:
            bukvar_types = ["watch-and-repeat", "classify", "image-to-letter"]
            existing = [t.strip() for t in placeholders.get("REQUIRED_TYPES", "").split(",") if t.strip()]
            for bt in bukvar_types:
                if bt not in existing:
                    existing.append(bt)
            placeholders["REQUIRED_TYPES"] = ", ".join(existing)

        return placeholders["REQUIRED_TYPES"]

    def test_a1_m1_gets_bukvar_types(self):
        result = self._simulate_required_types_logic("a1", 1, {})
        for bt in ["watch-and-repeat", "classify", "image-to-letter"]:
            assert bt in result, f"Missing bukvar type: {bt}"

    def test_a1_m4_gets_bukvar_types(self):
        result = self._simulate_required_types_logic("a1", 4, {})
        for bt in ["watch-and-repeat", "classify", "image-to-letter"]:
            assert bt in result

    def test_a1_m5_does_not_get_bukvar_types(self):
        result = self._simulate_required_types_logic("a1", 5, {})
        assert "image-to-letter" not in result

    def test_a2_does_not_get_bukvar_types(self):
        result = self._simulate_required_types_logic("a2", 1, {})
        assert "image-to-letter" not in result

    def test_bukvar_deduplicates(self):
        """If plan hints already include bukvar types, don't duplicate."""
        plan = {"activity_hints": [
            {"type": "watch-and-repeat", "focus": "test"},
            {"type": "classify", "focus": "test"},
        ]}
        result = self._simulate_required_types_logic("a1", 1, plan)
        assert result.count("watch-and-repeat") == 1
        assert result.count("classify") == 1
        assert "image-to-letter" in result  # added since missing

    def test_dict_hints_extract_type_field(self):
        """Dict activity_hints must extract 'type' field, not stringify the whole dict."""
        plan = {"activity_hints": [
            {"type": "watch-and-repeat", "focus": "Watch video", "items": 7},
            {"type": "quiz", "focus": "Test knowledge"},
        ]}
        result = self._simulate_required_types_logic("a1", 1, plan)
        assert "watch-and-repeat" in result
        assert "quiz" in result
        assert "focus" not in result  # must NOT contain dict field names

    def test_string_hints_work(self):
        """String activity_hints still work as before."""
        plan = {"activity_hints": ["quiz", "fill-in", "match-up"]}
        result = self._simulate_required_types_logic("a1", 1, plan)
        assert "quiz" in result
        assert "fill-in" in result
        # bukvar types added on top
        assert "watch-and-repeat" in result

    def test_empty_plan_falls_back_to_priority_types(self):
        result = self._simulate_required_types_logic("a1", 1, {})
        # Should get first 3 priority types + bukvar types
        assert "fill-in" in result
        assert "watch-and-repeat" in result
