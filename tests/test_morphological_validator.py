"""Tests for VESUM-based morphological validator.

Issue: #753
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from audit.checks.morphological_validator import (
    _should_skip_line,
    check_replacements,
    validate_morphology,
)

# ---------------------------------------------------------------------------
# Constraint configuration tests
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Line filtering tests
# ---------------------------------------------------------------------------

class TestLineFiltering:

    def test_english_with_ukrainian_not_skipped(self):
        """English-dominant lines with Ukrainian words are now checked."""
        assert _should_skip_line("This is an English sentence with one word собака") is False


# ---------------------------------------------------------------------------
# Allowed chunks tests
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Core validation tests (TC1-TC9 from issue #753)
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("requires_vesum_db")
class TestVerbDetection:
    """TC1: Verbs caught in pre-verb modules (M01-M03 have no_verbs=True)."""

    def test_standalone_verb_caught(self):
        issues = validate_morphology("Він робить домашнє завдання.", "A1", 2, "a1")
        assert any("робить" in i["text"] and "verb" in i["text"].lower() for i in issues)

    def test_verb_after_m15_ok(self):
        issues = validate_morphology("Він робить домашнє завдання.", "A1", 16, "a1")
        verb_issues = [i for i in issues if "verb" in i["text"].lower() and "Verb" in i["text"]]
        assert len(verb_issues) == 0


@pytest.mark.usefixtures("requires_vesum_db")
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


@pytest.mark.usefixtures("requires_vesum_db")
class TestChunkExceptions:
    """TC3: Memorized chunks exempt from constraints."""

    def test_farewell_exempt(self):
        issues = validate_morphology("До побачення! Як справи?", "A1", 8, "a1")
        assert len(issues) == 0


@pytest.mark.usefixtures("requires_vesum_db")
class TestImperativeDetection:
    """TC8: Imperative forms detected via VESUM tags."""

    def test_imperative_caught(self):
        issues = validate_morphology("Запам'ятайте це правило!", "A1", 5, "a1")
        assert any("imperative" in i["text"].lower() for i in issues)

    def test_imperative_after_m47_ok(self):
        issues = validate_morphology("Запам'ятайте це правило!", "A1", 50, "a1")
        assert len(issues) == 0


@pytest.mark.usefixtures("requires_vesum_db")
class TestPOSMismatch:
    """TC9: Words used as wrong POS detected in no_verbs phase."""


@pytest.mark.usefixtures("requires_vesum_db")
class TestStressMarks:
    """Stress marks (combining acute accent) handled correctly."""

    def test_stressed_words_not_split(self):
        issues = validate_morphology("Це вели́кий собо́р.", "A1", 10, "a1")
        # великий and собор are nominative — should be 0 issues
        assert len(issues) == 0


@pytest.mark.usefixtures("requires_vesum_db")
class TestAccusativeConstraint:
    """Accusative case detected in nominative-only modules."""

    def test_accusative_caught_nom_only(self):
        """M10 has nominative_only=True via heuristic (<= 14)."""
        issues = validate_morphology("Я читаю книгу.", "A1", 10, "a1")
        assert any("accusative" in i["text"].lower() or "книгу" in i["text"] for i in issues)


@pytest.mark.usefixtures("requires_vesum_db")
class TestPresentTenseOnly:
    """Non-present tense detected in present-only modules."""

    def test_past_tense_caught(self):
        """Use plan-driven constraint to test present_only (heuristic fallback doesn't have it)."""
        plan = {"phase": "A1.2"}
        issues = validate_morphology("Вчора він читав книгу.", "A1", 10, "a1", plan=plan)
        assert any("читав" in i["text"] for i in issues)

    def test_noun_homonym_not_flagged_as_past(self):
        """'став' as noun (pond) should not be flagged as past tense verb."""
        issues = validate_morphology("Великий став.", "A1", 20, "a1")
        past_issues = [i for i in issues if "past" in i.get("text", "").lower() or "tense" in i.get("text", "").lower()]
        assert len(past_issues) == 0


@pytest.mark.usefixtures("requires_vesum_db")
class TestAccusativeHomonyms:
    """Accusative escape hatch for verb homonyms."""

    def test_verb_homonym_not_flagged_as_acc(self):
        """'дію' as verb (I act) should not be flagged as accusative noun."""
        issues = validate_morphology("Я дію швидко.", "A1", 20, "a1")
        acc_issues = [i for i in issues if "accusative" in i.get("text", "").lower()]
        assert len(acc_issues) == 0


@pytest.mark.usefixtures("requires_vesum_db")
class TestNonA1Imperatives:
    """Non-A1 tracks should not block imperatives."""


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


# ---------------------------------------------------------------------------
# Agreement tests
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("requires_vesum_db")
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


# ---------------------------------------------------------------------------
# Bracket stripping — phonetic transcriptions (#1053)
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("requires_vesum_db")
class TestBracketStripping:
    """Phonetic transcriptions in [brackets] should not be validated (#1053)."""

    def test_phonetic_brackets_skipped(self):
        """Words inside [...] should not produce any issues."""
        # [йаблуко] is not a valid VESUM word, but should be stripped before checking
        content = "Звук [й] вимовляється м'яко. Слово [йаблуко] починається з й."
        issues = validate_morphology(content, "A1", 5, "a1")
        # Should not have issues about й or йаблуко
        bracket_issues = [i for i in issues if "й" in i.get("text", "") or "йаблуко" in i.get("text", "")]
        assert len(bracket_issues) == 0
