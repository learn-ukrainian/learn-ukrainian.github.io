"""
Tests for audit helper modules decomposed from audit_module.py.

Covers: lint, parsing, validators, report_helpers, activity_helpers,
activity_format_checks, activity_pedagogy_checks, activity_counting,
yaml_item_fixers, yaml_schema_fixes, phases_activity, phases_content,
phases_gates, phases_report.

Run with: pytest tests/test_audit_helpers.py -v
"""

import os
import sys
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.reads_content

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# TEST: scripts/audit/lint.py
# =============================================================================

from scripts.audit.lint import (
    _lint_activity_structure,
    _lint_ai_contamination,
    _lint_line_patterns,
    run_lint_checks,
)


class TestLintActivityStructure:
    def test_yaml_in_activity_section(self):
        lines = ["## Activities", "type: quiz", "items:"]
        errors = _lint_activity_structure(lines)
        assert any("YAML detected" in e for e in errors)

    def test_anagram_slash_format(self):
        lines = ["## Activities", "## anagram: Test", "а / б / в / г"]
        errors = _lint_activity_structure(lines)
        assert any("Invalid Anagram format" in e for e in errors)

    def test_fill_in_missing_placeholder(self):
        lines = ["## Activities", "## fill-in: Test", "1. Some sentence without blank"]
        errors = _lint_activity_structure(lines)
        assert any("missing '___'" in e for e in errors)

    def test_fill_in_with_placeholder(self):
        lines = ["## Activities", "## fill-in: Test", "1. Some ___ blank here", "> [!answer] word"]
        errors = _lint_activity_structure(lines)
        placeholder_errors = [e for e in errors if "missing '___'" in e]
        assert len(placeholder_errors) == 0

    def test_fill_in_missing_answer(self):
        lines = ["## Activities", "## fill-in: Test", "1. Some ___ here", "2. Another ___ here"]
        errors = _lint_activity_structure(lines)
        assert any("missing '> [!answer]'" in e for e in errors)

    def test_true_false_explanation(self):
        lines = ["## Activities", "## true-false: Test", "> [!explanation] This is why"]
        errors = _lint_activity_structure(lines)
        assert any("[!explanation]" in e for e in errors)


class TestLintLinePatterns:
    def test_old_answer_format(self):
        lines = ["## Activities", "**Answer:** something"]
        errors = _lint_line_patterns(lines, 1)
        assert any("Old format" in e for e in errors)

    def test_invalid_checkbox(self):
        lines = ["- [?] invalid"]
        errors = _lint_line_patterns(lines, 1)
        assert any("Invalid Checkbox" in e for e in errors)

    def test_valid_checkbox(self):
        lines = ["- [x] valid", "- [ ] unchecked"]
        errors = _lint_line_patterns(lines, 1)
        checkbox_errors = [e for e in errors if "Checkbox" in e]
        assert len(checkbox_errors) == 0

    def test_empty_header(self):
        lines = ["## "]
        errors = _lint_line_patterns(lines, 1)
        assert any("Empty Header" in e for e in errors)

    def test_transliteration_column_m21_plus(self):
        lines = ["| translit | word |"]
        errors = _lint_line_patterns(lines, 25)
        assert any("Transliteration Column" in e for e in errors)

    def test_transliteration_column_before_m21(self):
        lines = ["| translit | word |"]
        errors = _lint_line_patterns(lines, 10)
        assert len(errors) == 0

    def test_audio_outside_vocab(self):
        lines = ["Some text with audio_ link"]
        errors = _lint_line_patterns(lines, 1)
        assert any("audio_" in e for e in errors)

    def test_audio_in_vocab_table(self):
        lines = ["| Word | audio_uk_word | Translation | Category |"]
        errors = _lint_line_patterns(lines, 1)
        audio_errors = [e for e in errors if "audio_" in e]
        assert len(audio_errors) == 0


class TestLintAiContamination:
    def test_ai_pattern_detected(self):
        content = "Some text\nAI: This is a response\nMore text"
        errors = _lint_ai_contamination(content)
        assert any("AI Contamination" in e for e in errors)

    def test_no_contamination(self):
        content = "Clean content without any issues."
        errors = _lint_ai_contamination(content)
        assert len(errors) == 0


class TestRunLintChecks:
    def test_returns_errors_from_submodules(self):
        content = "## Activities\ntype: quiz\n"
        errors = run_lint_checks(content, {}, 1)
        assert len(errors) > 0


# =============================================================================
# TEST: scripts/audit/parsing.py
# =============================================================================

from scripts.audit.parsing import (
    AuditState,
    validate_required_metadata,
)


class TestAuditState:
    def test_fail_method(self):
        state = AuditState()
        state.fail("Test reason")
        assert state.has_critical_failure is True
        assert "Test reason" in state.critical_failure_reasons


class TestValidateRequiredMetadata:
    def test_all_present(self):
        fm = "duration: 30\ntransliteration: none\ntags: [a1]\nobjectives: [learn]\ngrammar: [nom]\npedagogy: PPP"
        missing = validate_required_metadata(fm)
        assert missing == []

    def test_missing_duration(self):
        fm = "transliteration: none\ntags: [a1]\nobjectives: [learn]\ngrammar: [nom]\npedagogy: PPP"
        missing = validate_required_metadata(fm)
        assert 'duration' in missing


# =============================================================================
# TEST: scripts/audit/validators.py
# =============================================================================

from scripts.audit.validators import (
    check_structure,
    validate_checkpoint_format,
    validate_tone,
)


class TestValidateTone:

    def test_kiev_usage(self):
        errors = validate_tone("The city of Kiev is beautiful.")
        assert any("Kiev" in e for e in errors)

    def test_kyiv_usage(self):
        errors = validate_tone("The city of Kyiv is beautiful.")
        assert len(errors) == 0


class TestCheckpointFormat:
    def test_missing_skill_sections(self):
        content = "# Checkpoint\n\nSome content without skills."
        errors = validate_checkpoint_format(content)
        assert any("Skill" in e or "Навичка" in e for e in errors)

    def test_valid_skill_section(self):
        content = "## Skill 1: Grammar\n### Model:\nExample\n### Practice:\nDo this\n### Self-Check\nCheck"
        errors = validate_checkpoint_format(content)
        assert len(errors) == 0

    def test_alternative_structure_rejected(self):
        content = "## Діагностика\nContent\n## Аналіз\nContent"
        errors = validate_checkpoint_format(content)
        assert any("REWRITE" in e for e in errors)

    def test_bold_format_rejected(self):
        content = "## Skill 1: Test\n**Model: something\n**Practice: something"
        errors = validate_checkpoint_format(content)
        assert any("bold" in e.lower() for e in errors)


class TestCheckStructure:
    def test_missing_summary(self):
        content = "## Vocabulary\n| Word | Translation |\n## Activities\nStuff"
        result = check_structure(content)
        assert result['summary'] is False

    def test_ukrainian_headers(self):
        content = "# Підсумок\nText\n## Словник\n| Слово | Переклад |"
        result = check_structure(content)
        assert result['summary'] is True
        assert result['vocab_header'] is True


# =============================================================================
# TEST: scripts/audit/report_helpers.py
# =============================================================================

from scripts.audit.gates import GateResult
from scripts.audit.report_helpers import (
    build_gates_dict,
    compute_overall_status,
    serialize_gate,
)


class TestSerializeGate:
    def test_none_input(self):
        result = serialize_gate(None)
        assert result['status'] == 'skipped'

    def test_pass_gate(self):
        gate = GateResult('PASS', '✅', '3000/3000')
        result = serialize_gate(gate)
        assert result['status'] == 'pass'
        assert result['violations'] == 0

    def test_fail_gate(self):
        gate = GateResult('FAIL', '❌', '2000/3000')
        result = serialize_gate(gate)
        assert result['status'] == 'fail'
        assert result['violations'] == 1

    def test_info_deferred(self):
        gate = GateResult('INFO', '⏳', 'Deferred (content-only audit)')
        result = serialize_gate(gate)
        assert result['status'] == 'deferred'


class TestBuildGatesDict:
    def test_basic_structure(self):
        results = {
            'structure': GateResult('PASS', '✅', 'Valid'),
            'words': GateResult('PASS', '✅', '3000/3000'),
            'activities': GateResult('PASS', '✅', '6/6'),
            'vocab': GateResult('PASS', '✅', '25/25'),
            'naturalness': GateResult('PASS', '✅', '9/10'),
            'research': GateResult('INFO', 'ℹ️', 'N/A'),
            'lint': GateResult('PASS', '✅', 'Clean'),
        }
        gates = build_gates_dict(results)
        assert 'meta' in gates
        assert 'lesson' in gates
        assert 'activities' in gates
        assert 'vocabulary' in gates
        assert 'naturalness' in gates

    def test_lint_failure_affects_meta(self):
        results = {
            'structure': GateResult('PASS', '✅', 'Valid'),
            'lint': GateResult('FAIL', '❌', '5 errors'),
            'words': GateResult('PASS', '✅', 'OK'),
            'activities': GateResult('PASS', '✅', 'OK'),
            'vocab': GateResult('PASS', '✅', 'OK'),
            'naturalness': GateResult('PASS', '✅', 'OK'),
            'research': GateResult('INFO', 'ℹ️', 'N/A'),
        }
        gates = build_gates_dict(results)
        assert gates['meta']['status'] == 'fail'


class TestComputeOverallStatus:
    def test_all_pass(self):
        gates = {
            'meta': {'status': 'pass', 'violations': 0, 'message': ''},
            'lesson': {'status': 'pass', 'violations': 0, 'message': ''},
        }
        result = compute_overall_status(gates, False, [])
        assert result['status'] == 'pass'
        assert result['pass_count'] == 2

    def test_has_failure(self):
        gates = {
            'meta': {'status': 'fail', 'violations': 1, 'message': 'bad'},
            'lesson': {'status': 'pass', 'violations': 0, 'message': ''},
        }
        result = compute_overall_status(gates, False, [])
        assert result['status'] == 'fail'
        assert result['fail_count'] == 1

    def test_critical_failure_overrides(self):
        gates = {
            'meta': {'status': 'pass', 'violations': 0, 'message': ''},
        }
        result = compute_overall_status(gates, True, ['Critical!'])
        assert result['status'] == 'fail'
        assert 'Critical!' in result['blocking_issues']

    def test_deferred_status(self):
        gates = {
            'meta': {'status': 'pass', 'violations': 0, 'message': ''},
            'activities': {'status': 'deferred', 'violations': 0, 'message': ''},
        }
        result = compute_overall_status(gates, False, [])
        assert result['status'] == 'content-complete'


# =============================================================================
# TEST: scripts/audit/checks/activity_helpers.py
# =============================================================================

from scripts.audit.checks.activity_helpers import (
    get_items,
)


class TestGetItems:

    def test_from_dict_returns_items_list(self):
        """get_items on a plain dict returns the 'items' list, NOT the
        dict.items() built-in method.  Regression for #1294."""
        activity_dict = {"type": "quiz", "items": [1, 2, 3]}
        assert get_items(activity_dict) == [1, 2, 3]


# =============================================================================
# TEST: scripts/audit/checks/activity_format_checks.py
# =============================================================================

from scripts.audit.checks.activity_format_checks import (
    check_activity_header_format,
    check_cloze_syntax_errors,
    check_hints_in_activities,
    check_mark_the_words_format,
    check_yaml_activity_types,
)


class TestCheckMarkTheWordsFormat:
    def test_missing_passage(self):
        activity = MagicMock()
        activity.type = 'mark-the-words'
        activity.title = 'Test'
        activity.text = ''
        activity.answers = []
        violations = check_mark_the_words_format([activity])
        assert any(v['type'] == 'MISSING_FIELD' for v in violations)

    def test_answer_not_in_passage(self):
        activity = MagicMock()
        activity.type = 'mark-the-words'
        activity.title = 'Test'
        activity.text = 'Він читає книгу'
        activity.answers = ['слово']
        violations = check_mark_the_words_format([activity])
        assert any(v['type'] == 'INVALID_ANSWER' for v in violations)

    def test_valid_mark_the_words(self):
        activity = MagicMock()
        activity.type = 'mark-the-words'
        activity.title = 'Test'
        activity.text = 'Він читає книгу'
        activity.answers = ['читає']
        violations = check_mark_the_words_format([activity])
        invalid_answers = [v for v in violations if v['type'] == 'INVALID_ANSWER']
        assert len(invalid_answers) == 0


class TestCheckHintsInActivities:
    def test_activity_level_hint(self):
        activity = MagicMock()
        activity.type = 'quiz'
        activity.title = 'Test'
        activity.hint = 'Some hint'
        activity.items = []
        violations = check_hints_in_activities([activity])
        assert any(v['type'] == 'HINT_IN_ACTIVITY' for v in violations)

    def test_no_hint(self):
        activity = MagicMock(spec=['type', 'title', 'items'])
        activity.type = 'quiz'
        activity.title = 'Test'
        activity.items = []
        violations = check_hints_in_activities([activity])
        assert len(violations) == 0


class TestCheckClozeErrors:
    def test_cloze_with_colon(self):
        activity = MagicMock()
        activity.type = 'cloze'
        activity.title = 'Test'
        activity.passage = 'Він {option1: word|option2} тут.'
        violations = check_cloze_syntax_errors([activity])
        assert any(v['type'] == 'CLOZE_SYNTAX_ERROR' for v in violations)

    def test_valid_cloze(self):
        activity = MagicMock()
        activity.type = 'cloze'
        activity.title = 'Test'
        activity.passage = 'Він {читає|читав} книгу.'
        violations = check_cloze_syntax_errors([activity])
        assert len(violations) == 0


class TestCheckYamlActivityTypes:
    def test_invalid_type(self):
        violations = check_yaml_activity_types([{'type': 'nonexistent-type'}])
        assert any(v['type'] == 'INVALID_ACTIVITY_TYPE' for v in violations)

    def test_missing_type(self):
        violations = check_yaml_activity_types([{'title': 'No type'}])
        assert any('missing' in v['issue'] for v in violations)

    def test_valid_type(self):
        violations = check_yaml_activity_types([{'type': 'quiz'}])
        assert len(violations) == 0


class TestCheckActivityHeaderFormat:
    def test_missing_title(self):
        content = "## quiz\nSome content"
        violations = check_activity_header_format(content)
        assert any(v['type'] == 'MALFORMED_ACTIVITY_HEADER' for v in violations)

    def test_empty_title(self):
        content = "## quiz: \nSome content"
        violations = check_activity_header_format(content)
        assert any('empty title' in v['issue'] for v in violations)

    def test_valid_header(self):
        content = "## quiz: Тестова вправа\nSome content"
        violations = check_activity_header_format(content)
        assert len(violations) == 0


# =============================================================================
# TEST: scripts/audit/checks/activity_pedagogy_checks.py
# =============================================================================

from scripts.audit.checks.activity_pedagogy_checks import (
    check_activity_variety,
    check_advanced_activities_presence,
)


class TestCheckAdvancedActivitiesPresence:
    def test_checkpoint_exempt(self):
        violations = check_advanced_activities_presence(['quiz'], 'B2', 'checkpoint')
        assert len(violations) == 0

    def test_b2_missing_essay(self):
        violations = check_advanced_activities_presence(['quiz', 'fill-in'], 'B2', None)
        assert any('essay-response' in v['issue'] for v in violations)

    def test_a1_not_required(self):
        violations = check_advanced_activities_presence(['quiz'], 'A1', None)
        assert len(violations) == 0

    def test_b2_biography_requirements(self):
        violations = check_advanced_activities_presence(['quiz'], 'B2', 'biography')
        assert len(violations) > 0


class TestCheckActivityVariety:
    def test_overused_type(self):
        content = "\n".join([
            "## quiz: Q1", "content",
            "## quiz: Q2", "content",
            "## quiz: Q3", "content",
            "## quiz: Q4", "content",
            "## quiz: Q5", "content",
        ])
        violations = check_activity_variety(content)
        assert any(v['type'] == 'VARIETY' for v in violations)

    def test_diverse_types(self):
        content = "## quiz: Q1\n## fill-in: F1\n## match-up: M1\n## true-false: TF1\n"
        violations = check_activity_variety(content)
        assert len(violations) == 0


# =============================================================================
# TEST: scripts/audit/checks/activity_counting.py
# =============================================================================



# =============================================================================
# TEST: scripts/audit/checks/yaml_item_fixers.py
# =============================================================================

from scripts.audit.checks.yaml_item_fixers import (
    DEFAULT_INSTRUCTIONS,
    fix_cloze_blank_lines,
    fix_error_correction_items,
    fix_fill_in_items,
    fix_group_sort_groups,
    fix_invalid_top_level_properties,
    fix_mark_the_words,
    fix_match_up_pairs,
    fix_missing_instruction,
    fix_quiz_select_items,
    fix_select_property_renames,
    fix_translate_items,
    fix_true_false_items,
    fix_unjumble_items,
)


class TestFixInvalidTopLevel:
    def test_remove_id(self):
        activity = {'id': 1, 'type': 'quiz', 'title': 'Test'}
        fixes = fix_invalid_top_level_properties(activity, 'quiz', {'type', 'title'})
        assert 'id' not in activity
        assert len(fixes) > 0


class TestFixMarkTheWords:
    def test_extract_answers(self):
        activity = {'text': 'Він *читає* *книгу* тут'}
        fixes = fix_mark_the_words(activity)
        assert activity['answers'] == ['читає', 'книгу']
        assert '*' not in activity['text']


class TestFixUnjumbleItems:
    def test_scrambled_to_words(self):
        activity = {'items': [{'scrambled': 'Він / читає / книгу'}]}
        fixes = fix_unjumble_items(activity)
        assert 'words' in activity['items'][0]
        assert 'scrambled' not in activity['items'][0]
        assert activity['items'][0]['words'] == ['Він', 'читає', 'книгу']


class TestFixTranslateItems:
    def test_answer_to_options(self):
        activity = {'items': [{'source': 'Привіт', 'answer': 'Hello'}]}
        fixes = fix_translate_items(activity)
        assert 'options' in activity['items'][0]
        assert activity['items'][0]['options'][0]['text'] == 'Hello'
        assert activity['items'][0]['options'][0]['correct'] is True


class TestFixTrueFalseItems:
    def test_rename_text_to_statement(self):
        activity = {'items': [{'text': 'Київ — столиця'}]}
        fixes = fix_true_false_items(activity)
        assert activity['items'][0]['statement'] == 'Київ — столиця'
        assert 'text' not in activity['items'][0]


class TestFixFillInItems:
    def test_rename_text_to_sentence(self):
        activity = {'items': [{'text': 'Він ___ книгу'}]}
        fixes = fix_fill_in_items(activity)
        assert activity['items'][0]['sentence'] == 'Він ___ книгу'
        assert 'text' not in activity['items'][0]


class TestFixErrorCorrectionItems:
    def test_rename_text_to_sentence(self):
        activity = {'items': [{'text': 'Він читає', 'error': 'читає', 'answer': 'читав'}]}
        fixes = fix_error_correction_items(activity)
        assert activity['items'][0]['sentence'] == 'Він читає'


class TestFixGroupSortGroups:
    def test_rename_title_to_name(self):
        activity = {'groups': [{'title': 'Group A', 'items': ['a', 'b']}]}
        fixes = fix_group_sort_groups(activity)
        assert activity['groups'][0]['name'] == 'Group A'
        assert 'title' not in activity['groups'][0]


class TestFixSelectPropertyRenames:
    def test_rename_answers_to_options(self):
        activity = {'items': [{'question': 'Test', 'answers': [{'text': 'A'}]}]}
        fixes = fix_select_property_renames(activity)
        assert 'options' in activity['items'][0]
        assert 'answers' not in activity['items'][0]


class TestFixMissingInstruction:
    def test_add_default_instruction(self):
        activity = {'type': 'quiz', 'items': []}
        fixes = fix_missing_instruction(activity, 'quiz')
        assert activity['instruction'] == DEFAULT_INSTRUCTIONS['quiz']
        assert len(fixes) == 1


class TestFixClozeBlankLines:
    def test_remove_blank_lines(self):
        activity = {'passage': 'Line 1\n\nLine 2\n\n\nLine 3'}
        fixes = fix_cloze_blank_lines(activity)
        assert '\n\n' not in activity['passage']
        assert len(fixes) == 1


class TestFixQuizSelectItems:
    def test_rename_prompt_to_question(self):
        activity = {'items': [{'prompt': 'What?', 'options': [{'text': 'A', 'correct': True}]}]}
        fixes = fix_quiz_select_items(activity, 'quiz')
        assert activity['items'][0]['question'] == 'What?'


class TestFixMatchUpPairs:
    def test_coerce_to_string(self):
        activity = {'pairs': [{'left': 123, 'right': 456}]}
        fixes = fix_match_up_pairs(activity)
        assert activity['pairs'][0]['left'] == '123'
        assert activity['pairs'][0]['right'] == '456'


# =============================================================================
# TEST: scripts/audit/checks/yaml_schema_fixes.py
# =============================================================================

from scripts.audit.checks.yaml_schema_fixes import (
    _convert_quotes_to_guillemets,
    _filter_activities,
    _fix_first_entry_indent,
)


class TestFixFirstEntryIndent:
    def test_fix_extra_indent(self):
        content = "  - type: quiz\n- type: fill-in"
        fixed, fixes = _fix_first_entry_indent(content)
        assert fixed.startswith("- type: quiz")
        assert len(fixes) == 1


class TestConvertQuotesToGuillemets:
    def test_conversion(self):
        assert _convert_quotes_to_guillemets('"hello"') == '«hello»'
class TestFilterActivities:
    def test_removes_forbidden(self):
        activities = [
            {'type': 'quiz', 'title': 'Q1'},
            {'type': 'fill-in', 'title': 'F1'},
        ]
        kept, removed, _msgs = _filter_activities(activities, {'quiz'}, 'LIT')
        assert removed == 1
        assert len(kept) == 1
        assert kept[0]['type'] == 'fill-in'


# =============================================================================
# TEST: scripts/audit/phases_activity.py (unit-testable parts)
# =============================================================================



if __name__ == '__main__':
    pytest.main([__file__, '-v'])
