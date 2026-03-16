"""
Check functions for module auditing.

This package contains various validation checks organized by domain:
- grammar: Grammar constraint validation
- vocabulary: Vocabulary section validation
- activities: Activity structure and sequencing validation
- pedagogy: Comprehensive pedagogical checks
"""

from .activities import (
    check_activity_focus_alignment,
    check_activity_header_format,
    check_activity_level_restrictions,
    check_activity_sequencing,
    check_activity_ukrainian_content,
    check_activity_variety,
    check_advanced_activities_presence,
    check_anagram_min_letters,
    check_answer_position_bias,
    check_mark_the_words_format,
    check_matchup_misuse,
    check_resources_placement,
    check_resources_required,
    check_unjumble_word_match,
    check_yaml_activity_types,
    count_items,
)
from .activity_validation import (
    check_english_hints_in_activities,
    check_fill_in_answer_in_options,
    check_mark_the_words_answers_in_text,
    check_mdx_unjumble_rendering,
    check_morpheme_patterns,
    check_morpheme_pedagogy,
    check_quiz_single_correct,
    check_select_min_correct,
    check_seminar_reading_pairing,
    check_translate_single_correct,
    check_unjumble_empty_jumbled,
    check_unjumble_out_of_scope_dative,
    check_unjumble_runon_answer,
)
from .checkpoint_format import (
    check_checkpoint_format,
    get_checkpoint_structure_summary,
)
from .content_gaming import (
    check_content_gaming,
)
from .content_quality import (
    check_content_quality,
)
from .content_recall_detection import (
    check_cloze_year_answers,
    check_content_heavy_activity_count,
    check_content_recall_violations,
    check_fill_in_year_answers,
    check_yaml_cloze_year_blanks,
    check_yaml_fill_in_year_answers,
    is_content_heavy_module,
    run_all_content_recall_checks,
)
from .euphony import (
    check_euphony_violations,
)
from .grammar import (
    check_case_government,
    check_gender_agreement,
    check_grammar_violations,
    check_sentence_complexity,
)
from .imperial_terminology import (
    check_imperial_terminology,
)
from .markdown_format import (
    check_markdown_format,
)
from .pedagogy import (
    check_duplicate_content,
    check_topic_consistency,
    run_pedagogical_checks,
)
from .review_gaming import (
    check_review_gaming,
)
from .russicism_detection import (
    check_russicisms,
    check_semantic_false_friends,
)
from .section_order import (
    check_section_order,
    fix_section_order,
    get_section_order_summary,
    parse_sections,
)
from .vocabulary import (
    check_vocab_violations,
    extract_vocab_from_section,
    extract_vocab_items,
    get_cumulative_vocab,
    sync_vocab_to_db,
)
from .yaml_schema_validation import (
    check_activity_yaml_schema,
    validate_activity_yaml_file,
)

__all__ = [
    'check_activity_focus_alignment',
    'check_activity_header_format',
    'check_activity_level_restrictions',
    # Activities
    'check_activity_sequencing',
    'check_activity_ukrainian_content',
    'check_activity_variety',
    # YAML Schema Validation
    'check_activity_yaml_schema',
    'check_advanced_activities_presence',
    'check_anagram_min_letters',
    'check_answer_position_bias',
    'check_case_government',
    # Checkpoint Format
    'check_checkpoint_format',
    'check_cloze_year_answers',
    # Content Gaming Detection
    'check_content_gaming',
    'check_content_heavy_activity_count',
    # Content Quality
    'check_content_quality',
    # Content Recall Detection
    'check_content_recall_violations',
    'check_duplicate_content',
    'check_english_hints_in_activities',
    # Euphony
    'check_euphony_violations',
    'check_fill_in_answer_in_options',
    'check_fill_in_year_answers',
    'check_gender_agreement',
    # Grammar
    'check_grammar_violations',
    # Imperial Terminology
    'check_imperial_terminology',
    'check_mark_the_words_answers_in_text',
    'check_mark_the_words_format',
    # Markdown Format
    'check_markdown_format',
    'check_matchup_misuse',
    'check_mdx_unjumble_rendering',
    'check_morpheme_patterns',
    'check_morpheme_pedagogy',
    'check_quiz_single_correct',
    'check_resources_placement',
    'check_resources_required',
    # Review Gaming Detection
    'check_review_gaming',
    # Russicism Detection
    'check_russicisms',
    # Section Order
    'check_section_order',
    'check_select_min_correct',
    'check_semantic_false_friends',
    'check_seminar_reading_pairing',
    'check_sentence_complexity',
    'check_topic_consistency',
    'check_translate_single_correct',
    # Activity Validation
    'check_unjumble_empty_jumbled',
    'check_unjumble_out_of_scope_dative',
    'check_unjumble_runon_answer',
    'check_unjumble_word_match',
    'check_vocab_violations',
    'check_yaml_activity_types',
    'check_yaml_cloze_year_blanks',
    'check_yaml_fill_in_year_answers',
    'count_items',
    # Vocabulary
    'extract_vocab_from_section',
    'extract_vocab_items',
    'fix_section_order',
    'get_checkpoint_structure_summary',
    'get_cumulative_vocab',
    'get_section_order_summary',
    'is_content_heavy_module',
    'parse_sections',
    'run_all_content_recall_checks',
    # Pedagogy
    'run_pedagogical_checks',
    'sync_vocab_to_db',
    'validate_activity_yaml_file',
]
