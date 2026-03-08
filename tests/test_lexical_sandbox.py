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
from dataclasses import dataclass
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lexical_sandbox import (
    COMMON_WORDS,
    _collect_candidates,
    _describe_constraints,
    _extract_case,
    _extract_gender,
    _extract_ukr_word,
    _form_allowed,
    _prioritize_verb_forms,
    _select_primary_match,
    extract_words_from_request,
    parse_resource_request,
)
from audit.checks.morphological_validator import GrammarConstraint


# =============================================================================
# _extract_ukr_word
# =============================================================================

class TestExtractUkrWord:
    def test_simple_word(self):
        assert _extract_ukr_word("собака") == "собака"

    def test_word_with_translation(self):
        assert _extract_ukr_word("новий (new)") == "новий"

    def test_word_with_dash_notes(self):
        assert _extract_ukr_word("собака — Collocations: great dog") == "собака"

    def test_word_with_em_dash(self):
        assert _extract_ukr_word("великий (big/grand) — adj") == "великий"

    def test_mixed_cyrillic_latin(self):
        result = _extract_ukr_word("word собака more")
        assert result == "собака" or "собака" in result

    def test_empty_string(self):
        assert _extract_ukr_word("") == ""

    def test_only_latin(self):
        # Should return the original cleaned text
        result = _extract_ukr_word("dog")
        assert result == "dog"


# =============================================================================
# _extract_gender
# =============================================================================

class TestExtractGender:
    def test_masculine(self):
        assert _extract_gender("noun:m:v_naz") == "m"

    def test_feminine(self):
        assert _extract_gender("noun:f:v_naz") == "f"

    def test_neuter(self):
        assert _extract_gender("noun:n:v_naz") == "n"

    def test_plural(self):
        assert _extract_gender("noun:p:v_naz") == "p"

    def test_end_of_string(self):
        assert _extract_gender("adj:m") == "m"

    def test_no_gender(self):
        assert _extract_gender("verb:imperf:pres:s:1") is None

    def test_gender_in_middle(self):
        assert _extract_gender("adj:f:v_naz:compb") == "f"


# =============================================================================
# _extract_case
# =============================================================================

class TestExtractCase:
    def test_nominative(self):
        assert _extract_case("noun:m:v_naz") == "v_naz"

    def test_genitive(self):
        assert _extract_case("noun:f:v_rod") == "v_rod"

    def test_dative(self):
        assert _extract_case("noun:m:v_dav") == "v_dav"

    def test_accusative(self):
        assert _extract_case("noun:f:v_zna") == "v_zna"

    def test_instrumental(self):
        assert _extract_case("noun:m:v_oru") == "v_oru"

    def test_locative(self):
        assert _extract_case("noun:f:v_mis") == "v_mis"

    def test_vocative(self):
        assert _extract_case("noun:m:v_kly") == "v_kly"

    def test_no_case(self):
        assert _extract_case("verb:imperf:inf") is None


# =============================================================================
# _form_allowed
# =============================================================================

class TestFormAllowed:
    @pytest.fixture
    def unconstrained(self):
        return GrammarConstraint()

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

    # Unconstrained — everything allowed
    def test_unconstrained_noun(self, unconstrained):
        assert _form_allowed("noun:m:v_naz", unconstrained)

    def test_unconstrained_verb(self, unconstrained):
        assert _form_allowed("verb:imperf:pres:s:1", unconstrained)

    # No verbs
    def test_no_verbs_blocks_verb(self, no_verbs):
        assert not _form_allowed("verb:imperf:pres:s:1", no_verbs)

    def test_no_verbs_allows_noun(self, no_verbs):
        assert _form_allowed("noun:m:v_naz", no_verbs)

    # Nominative only
    def test_nom_only_allows_nominative(self, nom_only):
        assert _form_allowed("noun:m:v_naz", nom_only)

    def test_nom_only_allows_vocative(self, nom_only):
        assert _form_allowed("noun:m:v_kly", nom_only)

    def test_nom_only_blocks_genitive(self, nom_only):
        assert not _form_allowed("noun:m:v_rod", nom_only)

    def test_nom_only_blocks_accusative(self, nom_only):
        assert not _form_allowed("noun:f:v_zna", nom_only)

    def test_nom_only_blocks_instrumental(self, nom_only):
        assert not _form_allowed("noun:m:v_oru", nom_only)

    # No accusative
    def test_no_acc_blocks_accusative(self, no_acc):
        assert not _form_allowed("noun:f:v_zna", no_acc)

    def test_no_acc_allows_nominative(self, no_acc):
        assert _form_allowed("noun:m:v_naz", no_acc)

    def test_no_acc_allows_genitive(self, no_acc):
        assert _form_allowed("noun:m:v_rod", no_acc)

    # No imperatives
    def test_no_impr_blocks_imperative(self, no_impr):
        assert not _form_allowed("verb:imperf:impr:s:2", no_impr)

    def test_no_impr_allows_present(self, no_impr):
        assert _form_allowed("verb:imperf:pres:s:1", no_impr)

    # Present only
    def test_present_only_allows_present(self, present_only):
        assert _form_allowed("verb:imperf:pres:s:1", present_only)

    def test_present_only_blocks_past(self, present_only):
        assert not _form_allowed("verb:imperf:past:m", present_only)

    def test_present_only_blocks_future(self, present_only):
        assert not _form_allowed("verb:perf:futr:s:1", present_only)


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

    def test_empty_json(self):
        raw = '===RESOURCE_REQUEST_START===\n{}\n===RESOURCE_REQUEST_END==='
        result = parse_resource_request(raw)
        assert result == {}


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

    def test_list_vocabulary(self):
        request = {"requested_vocabulary": ["хліб", "молоко"]}
        words = extract_words_from_request(request)
        assert "хліб" in words
        assert "молоко" in words

    def test_with_phrases(self):
        request = {
            "requested_vocabulary": {},
            "requested_phrases": ["Добрий день!", "Як справи?"]
        }
        words = extract_words_from_request(request)
        assert "Добрий" in words
        assert "день" in words
        assert "Як" in words
        assert "справи" in words

    def test_deduplication(self):
        request = {
            "requested_vocabulary": {
                "a": ["собака"],
                "b": ["собака"],
            }
        }
        words = extract_words_from_request(request)
        assert words.count("собака") == 1

    def test_empty_request(self):
        request = {}
        words = extract_words_from_request(request)
        assert words == []

    def test_strips_whitespace(self):
        request = {"requested_vocabulary": {"a": ["  собака  ", "  кіт  "]}}
        words = extract_words_from_request(request)
        assert "собака" in words
        assert "кіт" in words


# =============================================================================
# _collect_candidates
# =============================================================================

class TestCollectCandidates:
    def test_includes_common_words(self):
        candidates = _collect_candidates({})
        assert "я" in candidates
        assert "він" in candidates
        assert "це" in candidates

    def test_dict_vocab_hints(self):
        plan = {"vocabulary_hints": {"nouns": ["собака", "кіт"]}}
        candidates = _collect_candidates(plan)
        assert "собака" in candidates
        assert "кіт" in candidates

    def test_list_vocab_hints(self):
        plan = {"vocabulary_hints": [
            "хліб",
            {"word": "молоко"},
        ]}
        candidates = _collect_candidates(plan)
        assert "хліб" in candidates
        assert "молоко" in candidates

    def test_dict_vocab_hints_with_translations(self):
        plan = {"vocabulary_hints": {"nouns": ["собака (dog)"]}}
        candidates = _collect_candidates(plan)
        assert "собака" in candidates

    def test_extra_words(self):
        candidates = _collect_candidates({}, extra_words=["додатковий"])
        assert "додатковий" in candidates

    def test_deduplicates(self):
        plan = {"vocabulary_hints": {"a": ["я"], "b": ["я"]}}
        candidates = _collect_candidates(plan)
        assert candidates.count("я") == 1

    def test_empty_plan(self):
        candidates = _collect_candidates({})
        # COMMON_WORDS has some duplicates (що, як) which get deduped
        assert len(candidates) == len(set(COMMON_WORDS))

    def test_strips_whitespace(self):
        plan = {"vocabulary_hints": {"a": ["  собака  "]}}
        candidates = _collect_candidates(plan)
        assert "собака" in candidates

    def test_list_hint_with_uk_key(self):
        plan = {"vocabulary_hints": [{"uk": "вода"}]}
        candidates = _collect_candidates(plan)
        assert "вода" in candidates

    def test_list_hint_with_lemma_key(self):
        plan = {"vocabulary_hints": [{"lemma": "будинок"}]}
        candidates = _collect_candidates(plan)
        assert "будинок" in candidates


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

    def test_common_word_falls_back_to_noun(self):
        matches = [{"pos": "noun", "lemma": "день", "tags": "noun:m:v_naz"}]
        result = _select_primary_match("день", matches, is_common=True)
        assert result["pos"] == "noun"

    def test_verb_ending_prefers_verb(self):
        matches = [
            {"pos": "noun", "lemma": "дата", "tags": "noun:f:v_rod"},
            {"pos": "verb", "lemma": "дати", "tags": "verb:perf:inf"},
        ]
        result = _select_primary_match("дати", matches, is_common=False)
        assert result["pos"] == "verb"
        assert result["lemma"] == "дати"

    def test_verb_ending_falls_back_to_first(self):
        matches = [{"pos": "noun", "lemma": "дата", "tags": "noun:f:v_rod"}]
        result = _select_primary_match("дати", matches, is_common=False)
        assert result["pos"] == "noun"

    def test_regular_word_uses_first_match(self):
        matches = [
            {"pos": "noun", "lemma": "собака", "tags": "noun:f:v_naz"},
            {"pos": "adj", "lemma": "собачий", "tags": "adj:m:v_naz"},
        ]
        result = _select_primary_match("собака", matches, is_common=False)
        assert result["pos"] == "noun"

    def test_tisia_ending_prefers_verb(self):
        matches = [
            {"pos": "noun", "lemma": "something", "tags": "noun:f:v_rod"},
            {"pos": "verb", "lemma": "вчитися", "tags": "verb:imperf:inf"},
        ]
        result = _select_primary_match("вчитися", matches, is_common=False)
        assert result["pos"] == "verb"


# =============================================================================
# _describe_constraints
# =============================================================================

class TestDescribeConstraints:
    def test_no_constraints(self):
        c = GrammarConstraint()
        assert _describe_constraints(c) == []

    def test_no_verbs(self):
        c = GrammarConstraint(no_verbs=True)
        result = _describe_constraints(c)
        assert any("verb" in s.lower() for s in result)

    def test_nominative_only(self):
        c = GrammarConstraint(nominative_only=True)
        result = _describe_constraints(c)
        assert any("nominative" in s.lower() for s in result)

    def test_multiple_constraints(self):
        c = GrammarConstraint(no_verbs=True, nominative_only=True, present_only=True)
        result = _describe_constraints(c)
        assert len(result) >= 2

    def test_no_accusative(self):
        c = GrammarConstraint(no_accusative=True)
        result = _describe_constraints(c)
        assert any("accusative" in s.lower() for s in result)

    def test_no_imperatives(self):
        c = GrammarConstraint(no_imperatives=True)
        result = _describe_constraints(c)
        assert any("imperative" in s.lower() for s in result)


# =============================================================================
# _prioritize_verb_forms
# =============================================================================

class TestPrioritizeVerbForms:
    def test_imperative_first(self):
        forms = [
            {"word_form": "читай", "tags": "verb:imperf:impr:s:2"},
            {"word_form": "читаю", "tags": "verb:imperf:pres:s:1"},
            {"word_form": "читати", "tags": "verb:imperf:inf"},
        ]
        result = _prioritize_verb_forms(forms)
        assert result[0] == "читай"

    def test_present_before_infinitive(self):
        forms = [
            {"word_form": "читати", "tags": "verb:imperf:inf"},
            {"word_form": "читаю", "tags": "verb:imperf:pres:s:1"},
        ]
        result = _prioritize_verb_forms(forms)
        idx_pres = result.index("читаю")
        idx_inf = result.index("читати")
        assert idx_pres < idx_inf

    def test_deduplicates(self):
        forms = [
            {"word_form": "читай", "tags": "verb:imperf:impr:s:2"},
            {"word_form": "читай", "tags": "verb:imperf:impr:s:2"},
        ]
        result = _prioritize_verb_forms(forms)
        assert result.count("читай") == 1

    def test_caps_at_max(self):
        forms = [{"word_form": f"form{i}", "tags": "verb:imperf:pres:s:1"} for i in range(20)]
        result = _prioritize_verb_forms(forms, max_forms=5)
        assert len(result) == 5

    def test_empty_forms(self):
        assert _prioritize_verb_forms([]) == []

    def test_other_forms_last(self):
        forms = [
            {"word_form": "читав", "tags": "verb:imperf:past:m"},
            {"word_form": "читай", "tags": "verb:imperf:impr:s:2"},
            {"word_form": "читаю", "tags": "verb:imperf:pres:s:1"},
        ]
        result = _prioritize_verb_forms(forms)
        assert result[-1] == "читав"
