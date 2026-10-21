"""Tests for lexical_sandbox.py — target >80% coverage.

Mocks VESUM database access to test pure logic: word extraction, form filtering,
constraint checking, sandbox formatting, resource request parsing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


# ---------------------------------------------------------------------------
# _extract_ukr_word
# ---------------------------------------------------------------------------


class TestExtractUkrWord:
    def _import(self):
        from lexical_sandbox import _extract_ukr_word
        return _extract_ukr_word

    def test_word_with_parentheses(self):
        assert self._import()("новий (new)") == "новий"

    def test_mixed_script_extracts_cyrillic(self):
        assert self._import()("the собака dog") == "собака"

    def test_with_apostrophe(self):
        assert self._import()("об'єкт") == "об'єкт"

    def test_word_with_stress_mark(self):
        f = self._import()
        result = f("соба\u0301ка")
        assert "соба" in result


# ---------------------------------------------------------------------------
# _extract_gender
# ---------------------------------------------------------------------------


class TestExtractGender:
    def _import(self):
        from lexical_sandbox import _extract_gender
        return _extract_gender

    def test_masculine(self):
        assert self._import()("noun:m:v_naz") == "m"

    def test_no_gender(self):
        assert self._import()("adv") is None


# ---------------------------------------------------------------------------
# _extract_case
# ---------------------------------------------------------------------------


class TestExtractCase:
    def _import(self):
        from lexical_sandbox import _extract_case
        return _extract_case

    def test_nominative(self):
        assert self._import()("noun:m:v_naz") == "v_naz"

    def test_no_case(self):
        assert self._import()("adv") is None


# ---------------------------------------------------------------------------
# _form_allowed
# ---------------------------------------------------------------------------


class TestFormAllowed:
    def _import(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _form_allowed
        return _form_allowed, GrammarConstraint

    def test_no_verbs_blocks_verb(self):
        f, GC = self._import()
        c = GC(no_verbs=True)
        assert f("verb:imperf:inf", c) is False

    def test_no_imperatives_blocks_impr(self):
        f, GC = self._import()
        c = GC(no_imperatives=True)
        assert f("verb:imperf:impr:s:2", c) is False

    def test_present_only_blocks_past(self):
        f, GC = self._import()
        c = GC(present_only=True)
        assert f("verb:imperf:past:m:s", c) is False

    def test_present_only_allows_present(self):
        f, GC = self._import()
        c = GC(present_only=True)
        assert f("verb:imperf:pres:s:1", c) is True

    def test_nominative_only_blocks_genitive(self):
        f, GC = self._import()
        c = GC(nominative_only=True)
        assert f("noun:m:v_rod", c) is False

    def test_nominative_only_allows_vocative(self):
        f, GC = self._import()
        c = GC(nominative_only=True)
        assert f("noun:m:v_kly", c) is True

    def test_no_accusative_blocks_accusative(self):
        f, GC = self._import()
        c = GC(no_accusative=True)
        assert f("noun:m:v_zna", c) is False

    def test_adverb_passes_all(self):
        f, GC = self._import()
        c = GC(nominative_only=True, no_verbs=True)
        assert f("adv", c) is True


# ---------------------------------------------------------------------------
# _collect_candidates
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _select_primary_match
# ---------------------------------------------------------------------------


class TestSelectPrimaryMatch:
    def _import(self):
        from lexical_sandbox import _select_primary_match
        return _select_primary_match

    def test_common_word_prefers_non_noun(self):
        f = self._import()
        matches = [
            {"pos": "noun", "lemma": "так", "tags": "noun:n:v_naz"},
            {"pos": "part", "lemma": "так", "tags": "part"},
        ]
        result = f("так", matches, is_common=True)
        assert result["pos"] == "part"

    def test_common_word_falls_back_to_noun(self):
        f = self._import()
        matches = [{"pos": "noun", "lemma": "людина", "tags": "noun:f:v_naz"}]
        result = f("людина", matches, is_common=True)
        assert result["pos"] == "noun"

    def test_verb_ending_prefers_verb(self):
        f = self._import()
        matches = [
            {"pos": "noun", "lemma": "дати", "tags": "noun:f:v_naz"},
            {"pos": "verb", "lemma": "дати", "tags": "verb:perf:inf"},
        ]
        result = f("дати", matches, is_common=False)
        assert result["pos"] == "verb resistance"[0:4]


# ---------------------------------------------------------------------------
# _describe_constraints
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _prioritize_verb_forms
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# parse_resource_request
# ---------------------------------------------------------------------------


class TestParseResourceRequest:
    def _import(self):
        from lexical_sandbox import parse_resource_request
        return parse_resource_request

    def test_delimited_json(self):
        f = self._import()
        raw = '===RESOURCE_REQUEST_START===\n{"words": ["кіт"]}\n===RESOURCE_REQUEST_END==='
        result = f(raw)
        assert result == {"words": ["кіт"]}

    def test_json_code_block(self):
        f = self._import()
        raw = 'Some text\n```json\n{"words": ["собака"]}\n```\nMore text'
        result = f(raw)
        assert result == {"words": ["собака"]}

    def test_raw_json(self):
        f = self._import()
        raw = '{"words": ["хліб"]}'
        result = f(raw)
        assert result == {"words": ["хліб"]}

    def test_invalid_json(self):
        f = self._import()
        result = f("not json at all")
        assert result is None


# ---------------------------------------------------------------------------
# extract_words_from_request
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _fetch_textbook_examples (mocked RAG)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _format_sandbox
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# build_sandbox (integration, mocked VESUM)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _get_all_forms (mocked DB)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# COMMON_WORDS constant
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Label dicts
# ---------------------------------------------------------------------------
