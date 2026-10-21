"""Tests for lexical_sandbox.py — VESUM-validated word bank.

Covers:
- Word extraction from hints
- VESUM tag parsing (gender, case)
- Constraint-based form filtering
- Resource request parsing
- Word extraction from requests

Issue: #783
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.checks.morphological_validator import GrammarConstraint
from lexical_sandbox import (
    _collect_candidates,
    _extract_case,
    _extract_gender,
    _form_allowed,
    _select_primary_match,
    extract_words_from_request,
    parse_resource_request,
)

# =============================================================================
# _extract_ukr_word
# =============================================================================


# =============================================================================
# _extract_gender
# =============================================================================

class TestExtractGender:
    def test_masculine(self):
        assert _extract_gender("noun:m:v_naz") == "m"

    def test_no_gender(self):
        assert _extract_gender("verb:imperf:pres:s:1") is None


# =============================================================================
# _extract_case
# =============================================================================

class TestExtractCase:
    def test_nominative(self):
        assert _extract_case("noun:m:v_naz") == "v_naz"

    def test_no_case(self):
        assert _extract_case("verb:imperf:inf") is None


# =============================================================================
# _form_allowed
# =============================================================================

class TestFormAllowed:
    @pytest.fixture
    def no_verbs(self):
        return GrammarConstraint(no_verbs=True)

    @pytest.fixture
    def nom_only(self):
        return GrammarConstraint(nominative_only=True)

    @pytest.fixture
    def no_acc(self):
        return GrammarConstraint(no_accusative=True)

    @pytest.fixture
    def no_impr(self):
        return GrammarConstraint(no_imperatives=True)

    @pytest.fixture
    def present_only(self):
        return GrammarConstraint(present_only=True)

    # No verbs
    def test_no_verbs_blocks_verb(self, no_verbs):
        assert not _form_allowed("verb:imperf:pres:s:1", no_verbs)

    # Nominative only
    def test_nom_only_allows_nominative(self, nom_only):
        assert _form_allowed("noun:m:v_naz", nom_only)

    def test_nom_only_blocks_genitive(self, nom_only):
        assert not _form_allowed("noun:m:v_rod", nom_only)

    # No accusative
    def test_no_acc_blocks_accusative(self, no_acc):
        assert not _form_allowed("noun:f:v_zna", no_acc)

    # No imperatives
    def test_no_impr_blocks_imperative(self, no_impr):
        assert not _form_allowed("verb:imperf:impr:s:2", no_impr)

    # Present only
    def test_present_only_allows_present(self, present_only):
        assert _form_allowed("verb:imperf:pres:s:1", present_only)

    def test_present_only_blocks_past(self, present_only):
        assert not _form_allowed("verb:imperf:past:m", present_only)


# =============================================================================
# parse_resource_request
# =============================================================================

class TestParseResourceRequest:
    def test_delimited_json(self):
        raw = """Some text
===RESOURCE_REQUEST_START===
{"requested_vocabulary": {"nouns": ["собака", "кіт"]}}
===RESOURCE_REQUEST_END===
More text"""
        result = parse_resource_request(raw)
        assert result is not None
        assert result["requested_vocabulary"]["nouns"] == ["собака", "кіт"]

    def test_json_code_block(self):
        raw = """```json
{"requested_vocabulary": {"verbs": ["читати"]}}
```"""
        result = parse_resource_request(raw)
        assert result is not None
        assert result["requested_vocabulary"]["verbs"] == ["читати"]

    def test_invalid_json(self):
        raw = "This is not JSON at all"
        result = parse_resource_request(raw)
        assert result is None


# =============================================================================
# extract_words_from_request
# =============================================================================

class TestExtractWordsFromRequest:
    def test_dict_vocabulary(self):
        request = {
            "requested_vocabulary": {
                "nouns": ["собака", "кіт"],
                "verbs": ["читати"],
            }
        }
        words = extract_words_from_request(request)
        assert "собака" in words
        assert "кіт" in words
        assert "читати" in words


# =============================================================================
# _collect_candidates
# =============================================================================

class TestCollectCandidates:
    def test_dict_vocab_hints(self):
        plan = {"vocabulary_hints": {"nouns": ["собака", "кіт"]}}
        candidates = _collect_candidates(plan)
        assert "собака" in candidates
        assert "кіт" in candidates


# =============================================================================
# _select_primary_match
# =============================================================================

class TestSelectPrimaryMatch:
    def test_common_word_prefers_non_noun(self):
        matches = [
            {"pos": "noun", "lemma": "кіл", "tags": "noun:m:v_rod"},
            {"pos": "adv", "lemma": "коли", "tags": "adv"},
        ]
        result = _select_primary_match("коли", matches, is_common=True)
        assert result["pos"] == "adv"

    def test_verb_ending_prefers_verb(self):
        matches = [
            {"pos": "noun", "lemma": "дата", "tags": "noun:f:v_rod"},
            {"pos": "verb", "lemma": "дати", "tags": "verb:perf:inf"},
        ]
        result = _select_primary_match("дати", matches, is_common=False)
        assert result["pos"] == "verb"
        assert result["lemma"] == "дати"

    def test_regular_word_uses_first_match(self):
        matches = [
            {"pos": "noun", "lemma": "собака", "tags": "noun:f:v_naz"},
            {"pos": "adj", "lemma": "собачий", "tags": "adj:m:v_naz"},
        ]
        result = _select_primary_match("собака", matches, is_common=False)
        assert result["pos"] == "noun"


# =============================================================================
# _describe_constraints
# =============================================================================


# =============================================================================
# _prioritize_verb_forms
# =============================================================================
