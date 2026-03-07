"""Tests for VESUM-based morphological validator.

Issue: #753
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from audit.checks.morphological_validator import (
    GrammarConstraint,
    validate_morphology,
    check_replacements,
    check_agreement,
    _get_constraints,
    _should_skip_line,
    _is_in_allowed_chunk,
    _get_allowed_chunks,
)


# ---------------------------------------------------------------------------
# Constraint configuration tests
# ---------------------------------------------------------------------------

class TestConstraints:
    def test_a1_pre_verb(self):
        c = _get_constraints("a1", 8)
        assert c.no_verbs is True
        assert c.no_imperatives is True
        assert c.nominative_only is True

    def test_a1_verb_phase(self):
        c = _get_constraints("a1", 20)
        assert c.no_verbs is False
        assert c.no_imperatives is True
        assert c.present_only is True
        assert c.no_accusative is True

    def test_a1_post_imperative(self):
        c = _get_constraints("a1", 50)
        assert c.no_imperatives is False

    def test_non_a1_track(self):
        """Non-A1 tracks: imperatives already taught, no constraints."""
        c = _get_constraints("b1", 5)
        assert c.no_verbs is False
        assert c.no_imperatives is False


# ---------------------------------------------------------------------------
# Line filtering tests
# ---------------------------------------------------------------------------

class TestLineFiltering:
    def test_skip_empty(self):
        assert _should_skip_line("") is True
        assert _should_skip_line("   ") is True

    def test_skip_table(self):
        assert _should_skip_line("| робиш | you do |") is True

    def test_skip_code(self):
        assert _should_skip_line("```python") is True

    def test_skip_heading(self):
        assert _should_skip_line("## Світ прикметників") is True

    def test_skip_html_comment(self):
        assert _should_skip_line("<!-- SCOPE: letters -->") is True

    def test_skip_negative_example(self):
        assert _should_skip_line("WRONG: робиш") is True
        assert _should_skip_line("❌ робиш") is True

    def test_english_with_ukrainian_not_skipped(self):
        """English-dominant lines with Ukrainian words are now checked."""
        assert _should_skip_line("This is an English sentence with one word собака") is False

    def test_skip_pure_english(self):
        assert _should_skip_line("This is a purely English sentence.") is True

    def test_keep_ukrainian(self):
        assert _should_skip_line("Це собака. Собака гарна.") is False

    def test_callout_with_ukrainian(self):
        assert _should_skip_line("> Собака — це тварина.") is False

    def test_callout_english_only(self):
        assert _should_skip_line("> [!tip] Remember this rule!") is True

    def test_callout_empty(self):
        assert _should_skip_line("> [!culture]") is True


# ---------------------------------------------------------------------------
# Allowed chunks tests
# ---------------------------------------------------------------------------

class TestAllowedChunks:
    def test_m8_chunks(self):
        chunks = _get_allowed_chunks(8)
        assert "до побачення" in chunks
        assert "що ти робиш" in chunks

    def test_m11_chunks(self):
        chunks = _get_allowed_chunks(11)
        assert "до побачення" in chunks
        assert "що ти робиш" not in chunks  # Only in M5-10

    def test_m20_core_chunks(self):
        """M20 still has core chunks (будь ласка, вибачте etc.)"""
        chunks = _get_allowed_chunks(20)
        assert "будь ласка" in chunks
        assert "вибачте" in chunks

    def test_m50_no_chunks(self):
        """M50+ (post-imperative): no chunks needed"""
        chunks = _get_allowed_chunks(50)
        assert len(chunks) == 0

    def test_chunk_matching(self):
        chunks = {"до побачення", "як справи"}
        assert _is_in_allowed_chunk("побачення", "До побачення!", chunks) is True
        assert _is_in_allowed_chunk("побачення", "Побачення було добрим", chunks) is False


# ---------------------------------------------------------------------------
# Core validation tests (TC1-TC9 from issue #753)
# ---------------------------------------------------------------------------

class TestVerbDetection:
    """TC1: Verbs caught in pre-verb modules."""

    def test_standalone_verb_caught(self):
        issues = validate_morphology("Він робить домашнє завдання.", "A1", 8, "a1")
        assert any("робить" in i["text"] and "verb" in i["text"].lower() for i in issues)

    def test_verb_in_chunk_exempt(self):
        issues = validate_morphology("Що ти робиш?", "A1", 8, "a1")
        assert len(issues) == 0

    def test_verb_after_m15_ok(self):
        issues = validate_morphology("Він робить домашнє завдання.", "A1", 16, "a1")
        verb_issues = [i for i in issues if "verb" in i["text"].lower() and "Verb" in i["text"]]
        assert len(verb_issues) == 0


class TestCaseDetection:
    """TC2: Non-nominative cases caught in early modules."""

    def test_locative_caught(self):
        issues = validate_morphology("Вона на роботі. Він у місті.", "A1", 9, "a1")
        assert any("роботі" in i["text"] and "locative" in i["text"].lower() for i in issues)

    def test_nominative_ok(self):
        """TC7: No false positives on nominative."""
        issues = validate_morphology("Це собака. Собака гарна. Велике місто.", "A1", 10, "a1")
        assert len(issues) == 0

    def test_adverb_not_flagged_as_case(self):
        """чому is adverb, not dative."""
        issues = validate_morphology("Чому це важливо?", "A1", 10, "a1")
        assert len(issues) == 0


class TestChunkExceptions:
    """TC3: Memorized chunks exempt from constraints."""

    def test_farewell_exempt(self):
        issues = validate_morphology("До побачення! Як справи?", "A1", 8, "a1")
        assert len(issues) == 0


class TestTableExclusion:
    """TC4: Table rows excluded from validation."""

    def test_table_skipped(self):
        issues = validate_morphology("| робиш | you do |", "A1", 8, "a1")
        assert len(issues) == 0


class TestImperativeDetection:
    """TC8: Imperative forms detected via VESUM tags."""

    def test_imperative_caught(self):
        issues = validate_morphology("Запам'ятайте це правило!", "A1", 5, "a1")
        assert any("imperative" in i["text"].lower() for i in issues)

    def test_imperative_in_callout_caught(self):
        issues = validate_morphology("> Запам'ятайте це!", "A1", 5, "a1")
        assert any("imperative" in i["text"].lower() for i in issues)

    def test_imperative_after_m47_ok(self):
        issues = validate_morphology("Запам'ятайте це правило!", "A1", 50, "a1")
        assert len(issues) == 0


class TestPOSMismatch:
    """TC9: Words used as wrong POS detected."""

    def test_verb_only_word_caught(self):
        issues = validate_morphology("Правила переніс дуже важливі.", "A1", 5, "a1")
        assert any("переніс" in i["text"] for i in issues)


class TestStressMarks:
    """Stress marks (combining acute accent) handled correctly."""

    def test_stressed_words_not_split(self):
        issues = validate_morphology("Це вели́кий собо́р.", "A1", 10, "a1")
        # великий and собор are nominative — should be 0 issues
        assert len(issues) == 0

    def test_stressed_adjective_list(self):
        content = "*   вели́кий (big)\n*   мали́й (small)\n*   до́брий (good)"
        issues = validate_morphology(content, "A1", 11, "a1")
        assert len(issues) == 0


class TestAccusativeConstraint:
    """Accusative case detected in pre-M25 modules."""

    def test_accusative_caught_m20(self):
        issues = validate_morphology("Я читаю книгу.", "A1", 20, "a1")
        assert any("accusative" in i["text"].lower() or "книгу" in i["text"] for i in issues)


class TestPresentTenseOnly:
    """Non-present tense detected in M15-24."""

    def test_past_tense_caught(self):
        issues = validate_morphology("Вчора він читав книгу.", "A1", 20, "a1")
        assert any("читав" in i["text"] for i in issues)

    def test_noun_homonym_not_flagged_as_past(self):
        """'став' as noun (pond) should not be flagged as past tense verb."""
        issues = validate_morphology("Великий став.", "A1", 20, "a1")
        past_issues = [i for i in issues if "past" in i.get("text", "").lower() or "tense" in i.get("text", "").lower()]
        assert len(past_issues) == 0


class TestAccusativeHomonyms:
    """Accusative escape hatch for verb homonyms."""

    def test_verb_homonym_not_flagged_as_acc(self):
        """'дію' as verb (I act) should not be flagged as accusative noun."""
        issues = validate_morphology("Я дію швидко.", "A1", 20, "a1")
        acc_issues = [i for i in issues if "accusative" in i.get("text", "").lower()]
        assert len(acc_issues) == 0


class TestNonA1Imperatives:
    """Non-A1 tracks should not block imperatives."""

    def test_b1_imperative_ok(self):
        issues = validate_morphology("Запам'ятайте це правило!", "B1", 5, "b1")
        impr_issues = [i for i in issues if "imperative" in i.get("text", "").lower()]
        assert len(impr_issues) == 0


# ---------------------------------------------------------------------------
# Russicism / replacement tests
# ---------------------------------------------------------------------------

class TestReplacements:
    """LanguageTool-based Russicism and non-standard form detection."""

    def test_known_russicism_caught(self):
        # "автогонщик" → "автоперегонник" in LanguageTool rules
        issues = check_replacements("Він автогонщик.")
        assert any("автогонщик" in i["text"].lower() for i in issues)

    def test_clean_text_no_issues(self):
        issues = check_replacements("Це велике місто.")
        assert len(issues) == 0

    def test_table_rows_skipped(self):
        issues = check_replacements("| автогонщик | racer |")
        assert len(issues) == 0

    def test_deduplication(self):
        issues = check_replacements("Автогонщик і автогонщик.")
        assert len(issues) == 1


# ---------------------------------------------------------------------------
# Agreement tests
# ---------------------------------------------------------------------------

class TestAgreement:
    """Adjective-noun gender/case agreement detection."""

    def test_mismatch_caught(self):
        """великий місто — masc adj + neuter noun."""
        issues = validate_morphology("Великий місто тут.", "A1", 50, "a1")
        agr_issues = [i for i in issues if i["type"] == "AGREEMENT_ERROR"]
        assert len(agr_issues) > 0
        assert "великий" in agr_issues[0]["text"].lower()

    def test_correct_agreement_ok(self):
        """велике місто — neuter adj + neuter noun."""
        issues = validate_morphology("Велике місто тут.", "A1", 50, "a1")
        agr_issues = [i for i in issues if i["type"] == "AGREEMENT_ERROR"]
        assert len(agr_issues) == 0

    def test_це_not_flagged(self):
        """Це + noun should not trigger agreement check."""
        issues = validate_morphology("Це собака.", "A1", 50, "a1")
        agr_issues = [i for i in issues if i["type"] == "AGREEMENT_ERROR"]
        assert len(agr_issues) == 0

    def test_sentence_boundary_respected(self):
        """Words across sentence boundary not checked."""
        issues = validate_morphology("Гарна кішка. Великий пес.", "A1", 50, "a1")
        agr_issues = [i for i in issues if i["type"] == "AGREEMENT_ERROR"]
        assert len(agr_issues) == 0
