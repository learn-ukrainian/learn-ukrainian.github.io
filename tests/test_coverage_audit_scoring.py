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

class TestUnjumbleChecks:
    def test_check_unjumble_empty_jumbled(self):
        from audit.checks.activity_validation import check_unjumble_empty_jumbled
        activities = [
            {"type": "unjumble", "title": "Test", "items": [{"words": ["a", "b"]}, {}]},
        ]
        violations = check_unjumble_empty_jumbled(activities)
        assert len(violations) == 1
        assert violations[0]["type"] == "EMPTY_UNJUMBLE_CONTENT"

    def test_check_unjumble_runon_answer(self):
        from audit.checks.activity_validation import check_unjumble_runon_answer
        activities = [
            {"type": "unjumble", "title": "T", "items": [
                {"answer": "Привіт друже Це маленький подарунок"}
            ]},
        ]
        violations = check_unjumble_runon_answer(activities)
        assert len(violations) == 1
        assert violations[0]["type"] == "UNJUMBLE_RUNON_SENTENCE"

    def test_check_unjumble_out_of_scope_dative(self):
        from audit.checks.activity_validation import check_unjumble_out_of_scope_dative
        activities = [
            {"type": "unjumble", "title": "T", "items": [
                {"words": ["моїй", "сестрі", "подобається"]}
            ]},
        ]
        violations = check_unjumble_out_of_scope_dative(activities)
        assert len(violations) == 1


class TestMdxUnjumbleRendering:
    def test_check_mdx_unjumble_rendering(self):
        from audit.checks.activity_validation import check_mdx_unjumble_rendering
        mdx = '<Unjumble key="1" title="Test" items={JSON.parse(`[{"jumbled":""}]`)}'
        violations = check_mdx_unjumble_rendering(mdx)
        assert len(violations) == 1


class TestMarkTheWords:
    def test_check_morpheme_patterns(self):
        from audit.checks.activity_validation import check_morpheme_patterns
        activities = [
            {"type": "mark-the-words", "title": "T",
             "text": "Слово *при*йшов у текст", "answers": None},
        ]
        violations = check_morpheme_patterns(activities)
        assert len(violations) == 0

    def test_check_mark_the_words_format_mixed(self):
        from audit.checks.activity_validation import check_mark_the_words_format
        activities = [
            {"type": "mark-the-words", "title": "T",
             "text": "[слово](noun) and *при*йшов together"},
        ]
        violations = check_mark_the_words_format(activities)
        assert len(violations) == 1
        assert violations[0]["type"] == "MIXED_MARK_FORMAT"

    def test_check_mark_the_words_answers_in_text(self):
        from audit.checks.activity_validation import check_mark_the_words_answers_in_text
        activities = [
            {"type": "mark-the-words", "title": "T",
             "text": "This is a test sentence", "answers": ["missing_word"]},
        ]
        violations = check_mark_the_words_answers_in_text(activities)
        assert len(violations) == 1


class TestMorphemePedagogy:
    def test_vague_instruction(self):
        from audit.checks.activity_validation import check_morpheme_pedagogy
        activities = [
            {"type": "mark-the-words", "title": "T",
             "text": "Click on any morphemes in the text\n\n*при*йшов"},
        ]
        violations = check_morpheme_pedagogy(activities)
        assert any(v["type"] == "VAGUE_MORPHEME_INSTRUCTION" for v in violations)

    def test_too_many_morphemes(self):
        from audit.checks.activity_validation import check_morpheme_pedagogy
        # Generate 12 distinct Ukrainian morpheme markers
        words = ["при", "від", "пере", "над", "під", "роз", "без", "ви", "за", "до", "по", "об"]
        morphemes = " ".join(f"*{w}*йшов" for w in words)
        activities = [
            {"type": "mark-the-words", "title": "T",
             "text": f"Знайдіть префікси\n\n{morphemes}"},
        ]
        violations = check_morpheme_pedagogy(activities)
        assert any(v["type"] == "TOO_MANY_MORPHEMES" for v in violations)


class TestQuizValidation:
    def test_quiz_single_correct(self):
        from audit.checks.activity_validation import check_quiz_single_correct
        activities = [
            {"type": "quiz", "title": "Q", "items": [
                {"options": [{"correct": True}, {"correct": True}, {"correct": False}]}
            ]}
        ]
        violations = check_quiz_single_correct(activities)
        assert len(violations) == 1


class TestSelectMinCorrect:
    def test_mismatch(self):
        from audit.checks.activity_validation import check_select_min_correct
        activities = [
            {"type": "select", "title": "S", "items": [
                {"min_correct": 2, "options": [{"correct": True}, {"correct": True}, {"correct": True}]}
            ]}
        ]
        violations = check_select_min_correct(activities)
        assert len(violations) == 1


class TestFillInAnswerInOptions:
    def test_answer_missing(self):
        from audit.checks.activity_validation import check_fill_in_answer_in_options
        activities = [
            {"type": "fill-in", "title": "F", "items": [
                {"answer": "correct", "options": ["wrong1", "wrong2"]}
            ]}
        ]
        violations = check_fill_in_answer_in_options(activities)
        assert len(violations) == 1


class TestTranslateSingleCorrect:
    def test_multiple_correct(self):
        from audit.checks.activity_validation import check_translate_single_correct
        activities = [
            {"type": "translate", "title": "T", "items": [
                {"options": [{"correct": True}, {"correct": True}]}
            ]}
        ]
        violations = check_translate_single_correct(activities)
        assert len(violations) == 1


class TestSeminarReadingPairing:
    def test_missing_reading_id(self):
        from audit.checks.activity_validation import check_seminar_reading_pairing
        activities = [
            {"type": "reading", "title": "Read 1"},
            {"type": "essay-response", "title": "Essay", "source_reading": "reading-01"},
        ]
        violations = check_seminar_reading_pairing(activities, "lit")
        assert any(v["type"] == "READING_MISSING_ID" for v in violations)

    def test_invalid_source_reading(self):
        from audit.checks.activity_validation import check_seminar_reading_pairing
        activities = [
            {"type": "reading", "title": "Read 1", "id": "reading-01"},
            {"type": "critical-analysis", "title": "Analysis", "source_reading": "reading-99"},
        ]
        violations = check_seminar_reading_pairing(activities, "hist")
        assert any(v["type"] == "INVALID_SOURCE_READING" for v in violations)

    def test_orphan_reading(self):
        from audit.checks.activity_validation import check_seminar_reading_pairing
        activities = [
            {"type": "reading", "title": "Orphan", "id": "reading-02"},
        ]
        violations = check_seminar_reading_pairing(activities, "bio")
        assert any(v["type"] == "ORPHAN_READING" for v in violations)

    def test_missing_source_reading(self):
        from audit.checks.activity_validation import check_seminar_reading_pairing
        activities = [
            {"type": "essay-response", "title": "Essay"},
        ]
        violations = check_seminar_reading_pairing(activities, "lit")
        assert any(v["type"] == "MISSING_SOURCE_READING" for v in violations)


class TestEnglishHintsInActivities:
    def test_english_hints_detected(self):
        from audit.checks.activity_validation import check_english_hints_in_activities
        activities = [
            {"type": "cloze", "title": "C", "passage": "Він (big) будинок (small) кімната (old)"}
        ]
        violations = check_english_hints_in_activities(activities, "B1", 5)
        assert len(violations) == 1

    def test_english_hints_a1_lenient(self):
        from audit.checks.activity_validation import check_english_hints_in_activities
        activities = [
            {"type": "fill-in", "title": "F", "items": [
                {"sentence": "Це (example) слово (hint) тут"}
            ]}
        ]
        violations = check_english_hints_in_activities(activities, "A1", 1)
        assert len(violations) == 0  # scaffolding hints allowed at A1


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

    def test_a1_format(self):
        from audit.checks.vocabulary import extract_vocab_items
        content = """## Vocabulary
| Word | English | POS | Gender | Note |
|---|---|---|---|---|
| книга | book | noun | f | basic |
"""
        items = extract_vocab_items(content)
        assert len(items) == 1


class TestCheckVocabViolations:
    def test_missing_vocab(self):
        from audit.checks.vocabulary import check_vocab_violations
        content = "Full content with книга and стіл"
        core_content = "книга книга стіл стіл новий новий"
        vocab_words = {"книга"}
        violations = check_vocab_violations(content, core_content, vocab_words)
        # "стіл" and "новий" used 2+ times but not in vocab
        assert len(violations) >= 1


class TestCheckMetalanguageScaffolding:
    def test_a1_metalanguage(self):
        from audit.checks.vocabulary import check_metalanguage_scaffolding
        content = "У цьому уроці іменник дуже важливий"
        vocab = set()
        violations = check_metalanguage_scaffolding(content, vocab, "A1", 1)
        assert len(violations) >= 1


class TestCheckVocabTableFormat:
    def test_a1_wrong_header(self):
        from audit.checks.vocabulary import check_vocab_table_format
        content = """## Словник
| Слово | Переклад | Примітка |
|---|---|---|
| книга | book | - |
"""
        violations = check_vocab_table_format(content, "A1")
        assert any(v["type"] == "VOCAB_HEADER" for v in violations)

    def test_a1_wrong_columns(self):
        from audit.checks.vocabulary import check_vocab_table_format
        content = """## Vocabulary
| Word | English | Note |
|---|---|---|
| книга | book | - |
"""
        violations = check_vocab_table_format(content, "A1")
        assert any(v["type"] == "VOCAB_FORMAT" for v in violations)


# ============================================================================
# 5. pipeline/screen.py
# ============================================================================


class TestScreenFixIpaBrackets:
    def test_strip_ipa(self):
        from pipeline.screen import _fix_ipa_brackets
        text = "слово [slo-vo] (word)"
        result, count = _fix_ipa_brackets(text)
        assert count >= 1
        assert "[slo-vo]" not in result


class TestScreenIpaScan:
    def test_ipa_detection(self):
        from pipeline.screen import _run_ipa_scan
        text = "Some text with [ɑɛɪɔʊ] transcription"
        issues = _run_ipa_scan(text)
        assert len(issues) >= 1
        assert issues[0]["type"] == "IPA_BANNED"

    def test_whitelist(self):
        from pipeline.screen import _run_ipa_scan
        text = "Zero form: [Ø]"
        issues = _run_ipa_scan(text)
        assert len(issues) == 0


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
