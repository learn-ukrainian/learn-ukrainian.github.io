"""Tests for lexical_sandbox.py — target >80% coverage.

Mocks VESUM database access to test pure logic: word extraction, form filtering,
constraint checking, sandbox formatting, resource request parsing.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


# ---------------------------------------------------------------------------
# _extract_ukr_word
# ---------------------------------------------------------------------------


class TestExtractUkrWord:
    def _import(self):
        from lexical_sandbox import _extract_ukr_word
        return _extract_ukr_word

    def test_simple_word(self):
        assert self._import()("собака") == "собака"

    def test_word_with_parentheses(self):
        assert self._import()("новий (new)") == "новий"

    def test_word_with_dash(self):
        assert self._import()("великий — Collocations: great") == "великий"

    def test_word_with_em_dash(self):
        assert self._import()("слово \u2014 word") == "слово"

    def test_mixed_script_extracts_cyrillic(self):
        assert self._import()("the собака dog") == "собака"

    def test_pure_cyrillic(self):
        assert self._import()("привіт") == "привіт"

    def test_with_apostrophe(self):
        assert self._import()("об'єкт") == "об'єкт"

    def test_empty_string(self):
        assert self._import()("") == ""

    def test_only_latin(self):
        f = self._import()
        result = f("hello")
        assert result == "hello"

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

    def test_feminine(self):
        assert self._import()("noun:f:v_naz") == "f"

    def test_neuter(self):
        assert self._import()("noun:n:v_naz") == "n"

    def test_plural(self):
        assert self._import()("noun:p:v_naz") == "p"

    def test_gender_at_end(self):
        assert self._import()("noun:v_naz:m") == "m"

    def test_no_gender(self):
        assert self._import()("adv") is None

    def test_gender_in_middle(self):
        assert self._import()("noun:f:v_rod") == "f"


# ---------------------------------------------------------------------------
# _extract_case
# ---------------------------------------------------------------------------


class TestExtractCase:
    def _import(self):
        from lexical_sandbox import _extract_case
        return _extract_case

    def test_nominative(self):
        assert self._import()("noun:m:v_naz") == "v_naz"

    def test_genitive(self):
        assert self._import()("noun:f:v_rod") == "v_rod"

    def test_dative(self):
        assert self._import()("noun:m:v_dav") == "v_dav"

    def test_accusative(self):
        assert self._import()("noun:m:v_zna") == "v_zna"

    def test_instrumental(self):
        assert self._import()("noun:m:v_oru") == "v_oru"

    def test_locative(self):
        assert self._import()("noun:m:v_mis") == "v_mis"

    def test_vocative(self):
        assert self._import()("noun:m:v_kly") == "v_kly"

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

    def test_no_constraints(self):
        f, GC = self._import()
        c = GC()
        assert f("noun:m:v_naz", c) is True

    def test_no_verbs_blocks_verb(self):
        f, GC = self._import()
        c = GC(no_verbs=True)
        assert f("verb:imperf:inf", c) is False

    def test_no_verbs_allows_noun(self):
        f, GC = self._import()
        c = GC(no_verbs=True)
        assert f("noun:m:v_naz", c) is True

    def test_no_imperatives_blocks_impr(self):
        f, GC = self._import()
        c = GC(no_imperatives=True)
        assert f("verb:imperf:impr:s:2", c) is False

    def test_no_imperatives_allows_inf(self):
        f, GC = self._import()
        c = GC(no_imperatives=True)
        assert f("verb:imperf:inf", c) is True

    def test_present_only_blocks_past(self):
        f, GC = self._import()
        c = GC(present_only=True)
        assert f("verb:imperf:past:m:s", c) is False

    def test_present_only_blocks_future(self):
        f, GC = self._import()
        c = GC(present_only=True)
        assert f("verb:perf:futr:s:1", c) is False

    def test_present_only_allows_present(self):
        f, GC = self._import()
        c = GC(present_only=True)
        assert f("verb:imperf:pres:s:1", c) is True

    def test_nominative_only_blocks_genitive(self):
        f, GC = self._import()
        c = GC(nominative_only=True)
        assert f("noun:m:v_rod", c) is False

    def test_nominative_only_allows_nominative(self):
        f, GC = self._import()
        c = GC(nominative_only=True)
        assert f("noun:m:v_naz", c) is True

    def test_nominative_only_allows_vocative(self):
        f, GC = self._import()
        c = GC(nominative_only=True)
        assert f("noun:m:v_kly", c) is True

    def test_no_accusative_blocks_accusative(self):
        f, GC = self._import()
        c = GC(no_accusative=True)
        assert f("noun:m:v_zna", c) is False

    def test_no_accusative_allows_dative(self):
        f, GC = self._import()
        c = GC(no_accusative=True)
        assert f("noun:m:v_dav", c) is True

    def test_adverb_passes_all(self):
        f, GC = self._import()
        c = GC(nominative_only=True, no_verbs=True)
        assert f("adv", c) is True


# ---------------------------------------------------------------------------
# _collect_candidates
# ---------------------------------------------------------------------------


class TestCollectCandidates:
    def _import(self):
        from lexical_sandbox import COMMON_WORDS, _collect_candidates
        return _collect_candidates, COMMON_WORDS

    def test_empty_plan(self):
        f, CW = self._import()
        result = f({})
        assert set(CW).issubset(set(result))

    def test_dict_vocab_hints(self):
        f, _ = self._import()
        plan = {"vocabulary_hints": {"food": ["яблуко", "хліб"]}}
        result = f(plan)
        assert "яблуко" in result
        assert "хліб" in result

    def test_list_vocab_hints(self):
        f, _ = self._import()
        plan = {"vocabulary_hints": ["один", "два"]}
        result = f(plan)
        assert "один" in result
        assert "два" in result

    def test_list_dict_items(self):
        f, _ = self._import()
        plan = {"vocabulary_hints": [{"word": "кіт"}, {"lemma": "собака"}]}
        result = f(plan)
        assert "кіт" in result
        assert "собака" in result

    def test_extra_words(self):
        f, _ = self._import()
        result = f({}, extra_words=["додатково"])
        assert "додатково" in result

    def test_deduplication(self):
        f, _ = self._import()
        plan = {"vocabulary_hints": {"a": ["так", "так", "так"]}}
        result = f(plan)
        assert result.count("так") == 1

    def test_string_vocab_hint(self):
        f, _ = self._import()
        plan = {"vocabulary_hints": {"greetings": "привіт"}}
        result = f(plan)
        assert "привіт" in result

    def test_strips_whitespace(self):
        f, _ = self._import()
        plan = {"vocabulary_hints": [" пробіл "]}
        result = f(plan)
        assert "пробіл" in result

    def test_empty_strings_skipped(self):
        f, _ = self._import()
        plan = {"vocabulary_hints": ["", "  ", "слово"]}
        result = f(plan)
        assert "" not in result
        assert "слово" in result

    def test_dict_with_uk_key(self):
        f, _ = self._import()
        plan = {"vocabulary_hints": [{"uk": "місто"}]}
        result = f(plan)
        assert "місто" in result


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

    def test_verb_ending_tися(self):
        f = self._import()
        matches = [
            {"pos": "verb", "lemma": "вчитися", "tags": "verb:imperf:inf"},
        ]
        result = f("вчитися", matches, is_common=False)
        assert result["pos"] == "verb"

    def test_regular_word_takes_first(self):
        f = self._import()
        matches = [
            {"pos": "noun", "lemma": "собака", "tags": "noun:f:v_naz"},
            {"pos": "adj", "lemma": "собачий", "tags": "adj:m:v_naz"},
        ]
        result = f("собака", matches, is_common=False)
        assert result["pos"] == "noun"


# ---------------------------------------------------------------------------
# _describe_constraints
# ---------------------------------------------------------------------------


class TestDescribeConstraints:
    def _import(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _describe_constraints
        return _describe_constraints, GrammarConstraint

    def test_no_constraints(self):
        f, GC = self._import()
        assert f(GC()) == []

    def test_no_verbs(self):
        f, GC = self._import()
        result = f(GC(no_verbs=True))
        assert any("verb" in s.lower() for s in result)

    def test_no_imperatives(self):
        f, GC = self._import()
        result = f(GC(no_imperatives=True))
        assert any("imperative" in s.lower() for s in result)

    def test_nominative_only(self):
        f, GC = self._import()
        result = f(GC(nominative_only=True))
        assert any("nominative" in s.lower() for s in result)

    def test_no_accusative(self):
        f, GC = self._import()
        result = f(GC(no_accusative=True))
        assert any("accusative" in s.lower() for s in result)

    def test_present_only(self):
        f, GC = self._import()
        result = f(GC(present_only=True))
        assert any("past" in s.lower() or "future" in s.lower() for s in result)

    def test_all_constraints(self):
        f, GC = self._import()
        result = f(GC(
            no_verbs=True, no_imperatives=True,
            nominative_only=True, no_accusative=True, present_only=True))
        assert len(result) >= 4


# ---------------------------------------------------------------------------
# _prioritize_verb_forms
# ---------------------------------------------------------------------------


class TestPrioritizeVerbForms:
    def _import(self):
        from lexical_sandbox import _prioritize_verb_forms
        return _prioritize_verb_forms

    def test_empty_forms(self):
        assert self._import()([]) == []

    def test_imperatives_first(self):
        f = self._import()
        forms = [
            {"word_form": "роби", "tags": "verb:imperf:impr:s:2"},
            {"word_form": "робити", "tags": "verb:imperf:inf"},
            {"word_form": "роблю", "tags": "verb:imperf:pres:s:1"},
        ]
        result = f(forms)
        assert result[0] == "роби"

    def test_present_before_inf(self):
        f = self._import()
        forms = [
            {"word_form": "робити", "tags": "verb:imperf:inf"},
            {"word_form": "роблю", "tags": "verb:imperf:pres:s:1"},
        ]
        result = f(forms)
        assert result.index("роблю") < result.index("робити")

    def test_truncation(self):
        f = self._import()
        forms = [{"word_form": f"form{i}", "tags": "verb:imperf:past:m:s"} for i in range(30)]
        result = f(forms, max_forms=5)
        assert len(result) == 5

    def test_deduplication(self):
        f = self._import()
        forms = [
            {"word_form": "роби", "tags": "verb:imperf:impr:s:2"},
            {"word_form": "роби", "tags": "verb:imperf:impr:s:2"},
        ]
        result = f(forms)
        assert result.count("роби") == 1


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

    def test_empty_delimiters(self):
        f = self._import()
        raw = '===RESOURCE_REQUEST_START===\n{}\n===RESOURCE_REQUEST_END==='
        result = f(raw)
        assert result == {}


# ---------------------------------------------------------------------------
# extract_words_from_request
# ---------------------------------------------------------------------------


class TestExtractWordsFromRequest:
    def _import(self):
        from lexical_sandbox import extract_words_from_request
        return extract_words_from_request

    def test_dict_vocab(self):
        f = self._import()
        result = f({"requested_vocabulary": {"food": ["яблуко", "хліб"]}})
        assert "яблуко" in result
        assert "хліб" in result

    def test_list_vocab(self):
        f = self._import()
        result = f({"requested_vocabulary": ["один", "два"]})
        assert "один" in result

    def test_phrases(self):
        f = self._import()
        result = f({"requested_phrases": ["Добрий ранок"]})
        assert "Добрий" in result
        assert "ранок" in result

    def test_deduplication(self):
        f = self._import()
        result = f({"requested_vocabulary": {"a": ["так", "так"]}})
        assert result.count("так") == 1

    def test_empty(self):
        f = self._import()
        result = f({})
        assert result == []

    def test_non_string_phrase_skipped(self):
        f = self._import()
        result = f({"requested_phrases": [123, None]})
        assert result == []


# ---------------------------------------------------------------------------
# _fetch_textbook_examples (mocked RAG)
# ---------------------------------------------------------------------------


class TestFetchTextbookExamples:
    def _import(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _fetch_textbook_examples
        return _fetch_textbook_examples, GrammarConstraint

    def test_import_error_returns_empty(self):
        f, GC = self._import()
        # Remove rag.query from modules to trigger ImportError
        orig = sys.modules.get("rag.query")
        sys.modules["rag.query"] = None  # Force ImportError on import
        try:
            result = f({"кіт"}, "a1", 1, GC(), 3)
            assert isinstance(result, list)
            assert len(result) == 0
        finally:
            if orig is not None:
                sys.modules["rag.query"] = orig
            else:
                sys.modules.pop("rag.query", None)

    @patch("lexical_sandbox.search_text", create=True)
    def test_with_mock_results(self, mock_search):
        f, GC = self._import()
        mock_results = [
            {"text": "Кіт сидить на столі. Він великий.", "source": "textbook1"},
        ]

        # Mock the import and function
        mock_module = MagicMock()
        mock_module.search_text = MagicMock(return_value=mock_results)

        with patch.dict("sys.modules", {"rag": MagicMock(), "rag.query": mock_module}):
            result = f({"кіт"}, "a1", 1, GC(), 3)
            assert isinstance(result, list)

    def test_max_examples_limit(self):
        f, GC = self._import()
        # With ImportError, returns empty
        result = f(set(), "a1", 1, GC(), 0)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# _format_sandbox
# ---------------------------------------------------------------------------


class TestFormatSandbox:
    def _import(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _format_sandbox
        return _format_sandbox, GrammarConstraint

    def test_empty_sections(self):
        f, GC = self._import()
        result = f("a1", 1, GC(),
                    {"nouns": [], "adjectives": [], "verbs": [], "other": []},
                    [], [], {})
        assert "Lexical Sandbox" in result
        assert "Usage Rules" in result

    def test_nouns_section(self):
        f, GC = self._import()
        sections = {
            "nouns": [{"lemma": "кіт", "pos": "noun", "original": "кіт",
                       "forms": [{"word_form": "кіт", "tags": "noun:m:v_naz"},
                                 {"word_form": "кота", "tags": "noun:m:v_rod"}]}],
            "adjectives": [], "verbs": [], "other": [],
        }
        result = f("a1", 1, GC(), sections, [], [], {})
        assert "### Nouns" in result
        assert "кіт" in result

    def test_adjectives_nominative_only(self):
        f, GC = self._import()
        sections = {
            "nouns": [],
            "adjectives": [{"lemma": "великий", "pos": "adj", "original": "великий",
                            "forms": [
                                {"word_form": "великий", "tags": "adj:m:v_naz"},
                                {"word_form": "велика", "tags": "adj:f:v_naz"},
                                {"word_form": "велике", "tags": "adj:n:v_naz"},
                                {"word_form": "великі", "tags": "adj:p:v_naz"},
                            ]}],
            "verbs": [], "other": [],
        }
        result = f("a1", 1, GC(nominative_only=True), sections, [], [], {})
        assert "Masculine" in result
        assert "Feminine" in result

    def test_adjectives_all_cases(self):
        f, GC = self._import()
        sections = {
            "nouns": [],
            "adjectives": [{"lemma": "новий", "pos": "adj", "original": "новий",
                            "forms": [{"word_form": "новий", "tags": "adj:m:v_naz"}]}],
            "verbs": [], "other": [],
        }
        result = f("b1", 1, GC(), sections, [], [], {})
        assert "Allowed Forms" in result

    def test_verbs_section(self):
        f, GC = self._import()
        sections = {
            "nouns": [], "adjectives": [],
            "verbs": [{"lemma": "робити", "pos": "verb", "original": "робити",
                       "forms": [{"word_form": "роблю", "tags": "verb:imperf:pres:s:1"},
                                 {"word_form": "робити", "tags": "verb:imperf:inf"}]}],
            "other": [],
        }
        result = f("a1", 1, GC(), sections, [], [], {})
        assert "### Verbs" in result
        assert "imperf" in result

    def test_other_section(self):
        f, GC = self._import()
        sections = {
            "nouns": [], "adjectives": [], "verbs": [],
            "other": [{"lemma": "дуже", "pos": "adv", "original": "дуже",
                       "forms": [{"word_form": "дуже", "tags": "adv"}]}],
        }
        result = f("a1", 1, GC(), sections, [], [], {})
        assert "### Other Words" in result
        assert "Adverb" in result

    def test_not_found_words(self):
        f, GC = self._import()
        result = f("a1", 1, GC(),
                    {"nouns": [], "adjectives": [], "verbs": [], "other": []},
                    [], ["невідоме"], {})
        assert "NOT IN VESUM" in result
        assert "невідоме" in result

    def test_constraint_description(self):
        f, GC = self._import()
        result = f("a1", 1, GC(no_verbs=True),
                    {"nouns": [], "adjectives": [], "verbs": [], "other": []},
                    [], [], {})
        assert "FORBIDDEN" in result

    def test_examples(self):
        f, GC = self._import()
        examples = [{"text": "Кіт сидить.", "source": "book1", "search_term": "кіт"}]
        result = f("a1", 1, GC(),
                    {"nouns": [], "adjectives": [], "verbs": [], "other": []},
                    examples, [], {})
        assert "Verified Example Sentences" in result
        assert "Кіт сидить." in result
        assert "book1" in result


# ---------------------------------------------------------------------------
# build_sandbox (integration, mocked VESUM)
# ---------------------------------------------------------------------------


class TestBuildSandbox:
    @patch("lexical_sandbox._fetch_textbook_examples", return_value=[])
    @patch("lexical_sandbox._get_all_forms")
    @patch("lexical_sandbox.vesum_batch_lookup")
    @patch("lexical_sandbox._get_constraints")
    def test_basic_build(self, mock_constraints, mock_vesum, mock_forms, mock_examples):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import build_sandbox

        mock_constraints.return_value = GrammarConstraint()
        mock_vesum.return_value = {
            "кіт": [{"lemma": "кіт", "pos": "noun", "tags": "noun:m:v_naz", "word_form": "кіт"}],
        }
        mock_forms.return_value = [
            {"word_form": "кіт", "lemma": "кіт", "pos": "noun", "tags": "noun:m:v_naz"},
            {"word_form": "кота", "lemma": "кіт", "pos": "noun", "tags": "noun:m:v_rod"},
        ]

        plan = {"vocabulary_hints": {"animals": ["кіт"]}}
        result = build_sandbox("a1", 1, plan)
        assert "Lexical Sandbox" in result
        assert "кіт" in result

    @patch("lexical_sandbox._fetch_textbook_examples", return_value=[])
    @patch("lexical_sandbox.vesum_batch_lookup", return_value={})
    @patch("lexical_sandbox._get_constraints")
    def test_empty_candidates(self, mock_constraints, mock_vesum, mock_examples):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import build_sandbox

        mock_constraints.return_value = GrammarConstraint()
        # No candidates beyond common words, but VESUM returns nothing
        result = build_sandbox("a1", 1, {})
        assert isinstance(result, str)

    @patch("lexical_sandbox._fetch_textbook_examples", return_value=[])
    @patch("lexical_sandbox._get_all_forms", return_value=[])
    @patch("lexical_sandbox.vesum_batch_lookup")
    @patch("lexical_sandbox._get_constraints")
    def test_filters_rare_forms(self, mock_constraints, mock_vesum, mock_forms, mock_examples):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import build_sandbox

        mock_constraints.return_value = GrammarConstraint()
        mock_vesum.return_value = {
            "кіт": [{"lemma": "кіт", "pos": "noun", "tags": "noun:m:v_naz", "word_form": "кіт"}],
        }
        # _get_all_forms returns empty, so it falls back to matches
        plan = {"vocabulary_hints": ["кіт"]}
        result = build_sandbox("a1", 1, plan)
        assert isinstance(result, str)

    @patch("lexical_sandbox._fetch_textbook_examples", return_value=[])
    @patch("lexical_sandbox._get_all_forms")
    @patch("lexical_sandbox.vesum_batch_lookup")
    @patch("lexical_sandbox._get_constraints")
    def test_common_word_as_function(self, mock_constraints, mock_vesum, mock_forms, mock_examples):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import build_sandbox

        mock_constraints.return_value = GrammarConstraint()
        # "так" is a common word and should be treated as particle, not noun
        mock_vesum.return_value = {
            "так": [{"lemma": "так", "pos": "part", "tags": "part", "word_form": "так"}],
        }

        result = build_sandbox("a1", 1, {})
        assert isinstance(result, str)
        # Common function words should appear in "Other Words" section
        # They don't get _get_all_forms called
        mock_forms.assert_not_called()

    @patch("lexical_sandbox._fetch_textbook_examples", return_value=[])
    @patch("lexical_sandbox._get_all_forms")
    @patch("lexical_sandbox.vesum_batch_lookup")
    @patch("lexical_sandbox._get_constraints")
    def test_verb_classification(self, mock_constraints, mock_vesum, mock_forms, mock_examples):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import build_sandbox

        mock_constraints.return_value = GrammarConstraint()
        mock_vesum.return_value = {
            "робити": [{"lemma": "робити", "pos": "verb", "tags": "verb:imperf:inf", "word_form": "робити"}],
        }
        mock_forms.return_value = [
            {"word_form": "роблю", "lemma": "робити", "pos": "verb", "tags": "verb:imperf:pres:s:1"},
            {"word_form": "робити", "lemma": "робити", "pos": "verb", "tags": "verb:imperf:inf"},
        ]

        plan = {"vocabulary_hints": ["робити"]}
        result = build_sandbox("a1", 5, plan)
        assert "### Verbs" in result

    @patch("lexical_sandbox._fetch_textbook_examples", return_value=[])
    @patch("lexical_sandbox._get_all_forms")
    @patch("lexical_sandbox.vesum_batch_lookup")
    @patch("lexical_sandbox._get_constraints")
    def test_adjective_classification(self, mock_constraints, mock_vesum, mock_forms, mock_examples):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import build_sandbox

        mock_constraints.return_value = GrammarConstraint()
        mock_vesum.return_value = {
            "великий": [{"lemma": "великий", "pos": "adj", "tags": "adj:m:v_naz", "word_form": "великий"}],
        }
        mock_forms.return_value = [
            {"word_form": "великий", "lemma": "великий", "pos": "adj", "tags": "adj:m:v_naz"},
        ]

        plan = {"vocabulary_hints": ["великий"]}
        result = build_sandbox("b1", 1, plan)
        assert "### Adjectives" in result

    @patch("lexical_sandbox._fetch_textbook_examples", return_value=[])
    @patch("lexical_sandbox._get_all_forms")
    @patch("lexical_sandbox.vesum_batch_lookup")
    @patch("lexical_sandbox._get_constraints")
    def test_deduplicate_lemma_pos(self, mock_constraints, mock_vesum, mock_forms, mock_examples):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import build_sandbox

        mock_constraints.return_value = GrammarConstraint()
        mock_vesum.return_value = {
            "кіт": [{"lemma": "кіт", "pos": "noun", "tags": "noun:m:v_naz", "word_form": "кіт"}],
        }
        mock_forms.return_value = [
            {"word_form": "кіт", "lemma": "кіт", "pos": "noun", "tags": "noun:m:v_naz"},
        ]

        # Same word twice in hints — _collect_candidates deduplicates
        plan = {"vocabulary_hints": {"a": ["кіт"], "b": ["кіт"]}}
        result = build_sandbox("a1", 1, plan)
        # Should appear in the output
        assert "кіт" in result


# ---------------------------------------------------------------------------
# _get_all_forms (mocked DB)
# ---------------------------------------------------------------------------


class TestGetAllForms:
    def test_returns_forms(self):
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = [
            {"word_form": "кіт", "lemma": "кіт", "pos": "noun", "tags": "noun:m:v_naz"},
            {"word_form": "кота", "lemma": "кіт", "pos": "noun", "tags": "noun:m:v_rod"},
        ]

        from lexical_sandbox import _get_all_forms
        with patch("rag_batch_verify.get_vesum_conn", return_value=mock_conn):
            result = _get_all_forms("кіт")
        assert len(result) == 2
        assert result[0]["word_form"] == "кіт"

    def test_empty_results(self):
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = []

        from lexical_sandbox import _get_all_forms
        with patch("rag_batch_verify.get_vesum_conn", return_value=mock_conn):
            result = _get_all_forms("неіснуюче")
        assert result == []


# ---------------------------------------------------------------------------
# COMMON_WORDS constant
# ---------------------------------------------------------------------------


class TestCommonWords:
    def test_common_words_exist(self):
        from lexical_sandbox import COMMON_WORDS
        assert len(COMMON_WORDS) > 20
        assert "я" in COMMON_WORDS
        assert "ти" in COMMON_WORDS
        assert "це" in COMMON_WORDS

    def test_common_words_are_strings(self):
        from lexical_sandbox import COMMON_WORDS
        assert all(isinstance(w, str) for w in COMMON_WORDS)


# ---------------------------------------------------------------------------
# Label dicts
# ---------------------------------------------------------------------------


class TestLabels:
    def test_gender_labels(self):
        from lexical_sandbox import _GENDER_LABELS
        assert _GENDER_LABELS["m"] == "masculine"
        assert _GENDER_LABELS["f"] == "feminine"
        assert _GENDER_LABELS["n"] == "neuter"

    def test_pos_labels(self):
        from lexical_sandbox import _POS_LABELS
        assert _POS_LABELS["noun"] == "Noun"
        assert _POS_LABELS["verb"] == "Verb"
        assert _POS_LABELS["adj"] == "Adjective"
