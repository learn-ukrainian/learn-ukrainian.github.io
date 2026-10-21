"""Tests targeting uncovered lines in audit, scoring, and pipeline modules.

Covers:
1. scripts/audit/report.py — report generation, terminal/markdown formatting
2. scripts/scoring/aggregator.py — criterion scorer functions + dispatch table
3. scripts/audit/checks/activity_validation.py — activity type validation
4. scripts/audit/checks/vocabulary.py — vocab gate checks
5. scripts/pipeline/screen.py — content screening (deterministic)
6. scripts/audit/phases_gates.py — gate evaluation phase (selected helpers)
7. scripts/audit/checks/content_quality.py — content quality scoring
8. scripts/manifest_utils.py — curriculum manifest utilities
9. scripts/lexical_sandbox.py — VESUM word bank
"""

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

# Add scripts/ to path
SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


# ============================================================================
# 1. audit/report.py
# ============================================================================


# ============================================================================
# 2. scoring/aggregator.py
# ============================================================================


# ============================================================================
# 3. audit/checks/activity_validation.py
# ============================================================================


class TestMarkTheWords:
    def test_check_morpheme_patterns(self):
        from audit.checks.activity_validation import check_morpheme_patterns
        activities = [
            {"type": "mark-the-words", "title": "T",
             "text": "Слово *при*йшов у текст", "answers": None},
        ]
        violations = check_morpheme_patterns(activities)
        assert len(violations) == 0


# ============================================================================
# 4. audit/checks/vocabulary.py
# ============================================================================

class TestGenerateInflections:
    def test_a_ending(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("книга")
        assert "книги" in forms
        assert "книгу" in forms
        assert "книга" in forms

    def test_ya_ending(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("земля")
        assert "землі" in forms
        assert "землю" in forms

    def test_o_ending(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("вікно")
        assert "вікна" in forms
        assert "вікном" in forms

    def test_e_ending(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("море")
        assert "моря" in forms
        assert "морем" in forms

    def test_consonant_ending(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("стіл")
        assert "стола" in forms  # i->o alternation
        assert "столи" in forms

    def test_adjective(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("новий")
        assert "нова" in forms
        assert "нове" in forms
        assert "нові" in forms

    def test_soft_sign_ending(self):
        from audit.checks.vocabulary import generate_inflections
        forms = generate_inflections("день")
        assert "день" in forms
        # soft-sign ending should not add consonant endings
        assert "деня" not in forms


class TestExtractVocabItems:
    def test_basic_table(self):
        from audit.checks.vocabulary import extract_vocab_items
        content = """## Vocabulary
| Слово | Переклад | Примітка |
|---|---|---|
| книга | book | basic |
| стіл | table | furniture |
"""
        items = extract_vocab_items(content)
        assert len(items) == 2
        assert items[0]["uk"] == "книга"


# ============================================================================
# 5. pipeline/screen.py
# ============================================================================


# ============================================================================
# 7. audit/checks/content_quality.py
# ============================================================================


class TestValidateCharactersInContent:
    def test_russian_chars(self):
        from audit.checks.content_quality import validate_characters_in_content
        content = "Це тест с ы"
        violations = validate_characters_in_content(content, "A1")
        assert any(v["type"] == "RUSSIAN_CHARACTERS" for v in violations)

    def test_oes_exempt(self):
        from audit.checks.content_quality import validate_characters_in_content
        content = "ъ ѣ old text"
        violations = validate_characters_in_content(content, "oes", "/path/oes/module.md")
        assert len(violations) == 0

    def test_historical_chars_in_modern(self):
        from audit.checks.content_quality import validate_characters_in_content
        content = "This ъ should not be here"
        violations = validate_characters_in_content(content, "A1")
        assert any(v["type"] == "HISTORICAL_CHARS_IN_MODERN" for v in violations)

    def test_historical_chars_in_blockquote(self):
        from audit.checks.content_quality import validate_characters_in_content
        content = "> Historical text with ъ"
        violations = validate_characters_in_content(content, "hist", "/path/hist/module.md")
        assert len(violations) == 0

    def test_russian_in_quotes_allowed(self):
        from audit.checks.content_quality import validate_characters_in_content
        content = 'Він каже "ы э" тут'
        violations = validate_characters_in_content(content, "A1")
        assert len(violations) == 0  # inside quotes


class TestValidateYamlVocabulary:
    def test_russian_chars(self):
        from audit.checks.content_quality import validate_yaml_vocabulary
        yaml_content = "uk: тест с ы"
        violations = validate_yaml_vocabulary(yaml_content)
        assert any(v["type"] == "RUSSIAN_CHARACTERS_YAML" for v in violations)

    def test_historical_in_modern_field(self):
        from audit.checks.content_quality import validate_yaml_vocabulary
        yaml_content = "uk: тест ъ\nen: test"
        violations = validate_yaml_vocabulary(yaml_content)
        assert any(v["type"] == "HISTORICAL_CHARS_IN_MODERN_YAML" for v in violations)

    def test_historical_in_allowed_field(self):
        from audit.checks.content_quality import validate_yaml_vocabulary
        yaml_content = "oes: тест ъ ѣ"
        violations = validate_yaml_vocabulary(yaml_content)
        assert not any(v["type"] == "HISTORICAL_CHARS_IN_MODERN_YAML" for v in violations)


class TestExtractModuleMetadata:
    def test_full_metadata(self):
        from audit.checks.content_quality import extract_module_metadata
        content = 'title: Test Module\nphase: A1\nmodule: 5\npedagogy: "communicative"\n\n# My Topic'
        metadata = extract_module_metadata(content)
        assert metadata["title"] == "Test Module"
        assert metadata["phase"] == "A1"
        assert metadata["module"] == 5
        assert metadata["topic"] == "My Topic"


class TestCheckContentQuality:
    def test_surzhyk_module_exempt(self):
        from audit.checks.content_quality import check_content_quality
        content = "---\ntitle: Surzhyk Module\n---\n\n# Surzhyk\n\nText with ы"
        violations = check_content_quality(content, "B1", 1)
        # Surzhyk modules should not flag Russian chars
        assert not any(v["type"] == "RUSSIAN_CHARACTERS" for v in violations)


# ============================================================================
# 8. manifest_utils.py
# ============================================================================
# ============================================================================
# 10. lexical_sandbox.py
# ============================================================================

class TestExtractUkrWord:
    def test_with_translation(self):
        from lexical_sandbox import _extract_ukr_word
        assert _extract_ukr_word("новий (new) — Collocations") == "новий"


class TestExtractGender:
    def test_masculine(self):
        from lexical_sandbox import _extract_gender
        assert _extract_gender("noun:m:v_naz") == "m"


class TestExtractCase:
    def test_nominative(self):
        from lexical_sandbox import _extract_case
        assert _extract_case("noun:m:v_naz") == "v_naz"


class TestFormAllowed:
    def test_no_verbs(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _form_allowed
        c = GrammarConstraint(no_verbs=True)
        assert not _form_allowed("verb:imperf:pres:s1", c)

    def test_no_imperatives(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _form_allowed
        c = GrammarConstraint(no_imperatives=True)
        assert not _form_allowed("verb:imperf:impr:s2", c)
        assert _form_allowed("verb:imperf:pres:s1", c)

    def test_present_only(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _form_allowed
        c = GrammarConstraint(present_only=True)
        assert not _form_allowed("verb:imperf:past:m", c)
        assert not _form_allowed("verb:perf:futr:s1", c)
        assert _form_allowed("verb:imperf:pres:s1", c)

    def test_nominative_only(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _form_allowed
        c = GrammarConstraint(nominative_only=True)
        assert _form_allowed("noun:m:v_naz", c)
        assert _form_allowed("noun:m:v_kly", c)
        assert not _form_allowed("noun:m:v_rod", c)

    def test_no_accusative(self):
        from audit.checks.morphological_validator import GrammarConstraint
        from lexical_sandbox import _form_allowed
        c = GrammarConstraint(no_accusative=True)
        assert not _form_allowed("noun:f:v_zna", c)
        assert _form_allowed("noun:f:v_naz", c)


class TestCollectCandidates:
    def test_from_dict_hints(self):
        from lexical_sandbox import _collect_candidates
        plan = {"vocabulary_hints": {"nouns": ["собака (dog)", "кіт"], "verbs": ["бігти"]}}
        candidates = _collect_candidates(plan)
        assert "собака" in candidates
        assert "кіт" in candidates
        assert "бігти" in candidates


class TestSelectPrimaryMatch:
    def test_common_word_non_noun(self):
        from lexical_sandbox import _select_primary_match
        matches = [
            {"lemma": "що", "pos": "noun", "tags": "noun:n:v_naz"},
            {"lemma": "що", "pos": "conj", "tags": "conj"},
        ]
        result = _select_primary_match("що", matches, True)
        assert result["pos"] == "conj"

    def test_verb_ending(self):
        from lexical_sandbox import _select_primary_match
        matches = [
            {"lemma": "дати", "pos": "noun", "tags": "noun:f:v_naz"},
            {"lemma": "дати", "pos": "verb", "tags": "verb:perf:inf"},
        ]
        result = _select_primary_match("дати", matches, False)
        assert result["pos"] == "verb"


class TestParseResourceRequest:
    def test_delimited(self):
        from lexical_sandbox import parse_resource_request
        raw = '===RESOURCE_REQUEST_START===\n{"requested_vocabulary": {"nouns": ["кіт"]}}\n===RESOURCE_REQUEST_END==='
        result = parse_resource_request(raw)
        assert result is not None
        assert "nouns" in result["requested_vocabulary"]

    def test_json_block(self):
        from lexical_sandbox import parse_resource_request
        raw = 'Some text\n```json\n{"key": "value"}\n```\nMore text'
        result = parse_resource_request(raw)
        assert result == {"key": "value"}

    def test_invalid_json(self):
        from lexical_sandbox import parse_resource_request
        result = parse_resource_request("not valid json at all")
        assert result is None


class TestExtractWordsFromRequest:
    def test_dict_vocab(self):
        from lexical_sandbox import extract_words_from_request
        req = {"requested_vocabulary": {"nouns": ["кіт", "собака"]},
               "requested_phrases": ["на добраніч"]}
        words = extract_words_from_request(req)
        assert "кіт" in words
        assert "собака" in words
        # phrases should extract Ukrainian words
        assert any("добраніч" in w for w in words)
