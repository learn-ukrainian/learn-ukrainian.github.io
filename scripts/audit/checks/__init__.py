"""
Check functions for module auditing.

This package contains various validation checks organized by domain:
- grammar: Grammar constraint validation
- vocabulary: Vocabulary section validation
- activities: Activity structure and sequencing validation
- pedagogy: Comprehensive pedagogical checks
"""

from .grammar import (
    check_grammar_violations,
    check_sentence_complexity,
    check_gender_agreement,
    check_case_government,
)
from .vocabulary import (
    extract_vocab_from_section,
    extract_vocab_items,
    check_vocab_violations,
    get_cumulative_vocab,
    sync_vocab_to_db,
)
from .activities import (
    check_activity_sequencing,
    check_answer_position_bias,
    check_activity_variety,
    check_matchup_misuse,
    check_activity_level_restrictions,
    check_activity_focus_alignment,
    check_anagram_min_letters,
    count_items,
)
from .pedagogy import (
    run_pedagogical_checks,
    check_duplicate_content,
    check_ipa_validation,
    check_topic_consistency,
)

__all__ = [
    # Grammar
    'check_grammar_violations',
    'check_sentence_complexity',
    'check_gender_agreement',
    'check_case_government',
    # Vocabulary
    'extract_vocab_from_section',
    'extract_vocab_items',
    'check_vocab_violations',
    'get_cumulative_vocab',
    'sync_vocab_to_db',
    # Activities
    'check_activity_sequencing',
    'check_answer_position_bias',
    'check_activity_variety',
    'check_matchup_misuse',
    'check_activity_level_restrictions',
    'check_activity_focus_alignment',
    'check_anagram_min_letters',
    'count_items',
    # Pedagogy
    'run_pedagogical_checks',
    'check_duplicate_content',
    'check_ipa_validation',
    'check_topic_consistency',
]
