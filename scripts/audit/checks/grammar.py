"""
Grammar-related validation checks.

Validates grammar constraints, sentence complexity, gender agreement,
and case government rules based on CEFR level.
"""

import re

from ..cleaners import extract_ukrainian_sentences
from ..config import (
    CASE_PATTERNS,
    FIXED_PHRASES_DATIVE,
    FIXED_PHRASES_INSTRUMENTAL,
    GRAMMAR_CONSTRAINTS,
    NOMINATIVE_PLURAL_EXCLUSIONS,
    PARTICIPLE_EXCLUSIONS,
)


def is_fixed_phrase(match: str, text: str, phrase_set: set) -> bool:
    """Check if a match is part of a fixed phrase that's taught at A1."""
    match_lower = match.lower()
    text_lower = text.lower()

    # Check if the match appears in any fixed phrase context
    for phrase in phrase_set:
        if phrase in text_lower and (match_lower in phrase or any(word in match_lower for word in phrase.split())):
                return True

    # Special handling for dative pronouns near context words
    # e.g., "Мені ... років" where ellipsis separates the words
    if match_lower in ('мені', 'тобі', 'йому', 'їй'):
        # Check for age expressions (dative + років/рік/роки)
        if re.search(rf'{match_lower}\s*\.{{0,3}}\s*\w*\s*рок', text_lower):
            return True
        # Check for "подобається" (likes) expressions
        if match_lower + ' подобається' in text_lower or 'подобається ' + match_lower in text_lower:
            return True
        # Check for feeling/state expressions
        feeling_words = ['погано', 'добре', 'холодно', 'тепло', 'болить', 'потрібн', 'треба']
        for word in feeling_words:
            if re.search(rf'{match_lower}\s+{word}', text_lower):
                return True

    return False


def check_grammar_violations(text: str, level_code: str, module_num: int) -> list[dict]:
    """Check for grammar violations based on level constraints."""
    violations = []
    # Strip HTML comments — citations like <!-- Bolshakova: "які позначають..." -->
    # contain Ukrainian text that triggers false positives (#969)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    # Strip dialogue location labels — **(За столом / At the table)** is bilingual
    # context, not grammar being taught (#975)
    text = re.sub(r'\*\*\(.*?/.*?\)\*\*', '', text)
    constraints = GRAMMAR_CONSTRAINTS.get(level_code, GRAMMAR_CONSTRAINTS.get('B2'))

    # Check forbidden cases at A1
    if level_code == 'A1':
        # Dative at A1: INFO only (not a blocking violation).
        # Dative pronouns (мені, тобі) appear naturally in commands/requests.
        # Formal teaching happens at A2, but incidental exposure is fine.
        for pattern in CASE_PATTERNS['dative']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches[:3]:
                    if match.lower() in NOMINATIVE_PLURAL_EXCLUSIONS:
                        continue
                    if is_fixed_phrase(match, text, FIXED_PHRASES_DATIVE):
                        continue
                    violations.append({
                        'type': 'INFO',
                        'issue': f"Dative case used at A1: '{match}' (taught formally at A2)",
                        'fix': "No action needed — incidental dative exposure is acceptable.",
                        'blocking': False,
                    })

        # Check for Instrumental
        for pattern in CASE_PATTERNS['instrumental']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches[:3]:
                    # Filter out fixed phrases taught at A1 (e.g., "З Новим роком!")
                    if is_fixed_phrase(match, text, FIXED_PHRASES_INSTRUMENTAL):
                        continue
                    violations.append({
                        'type': 'GRAMMAR',
                        'issue': f"Instrumental case used at A1: '{match}'",
                        'fix': "Instrumental case not allowed until A2 (M36+). Restructure sentence."
                    })

    # Check for perfective aspect at A1
    if level_code == 'A1' and constraints.get('aspect') == 'imperfective_only':
        for pattern in CASE_PATTERNS['perfective_markers']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches[:3]:
                    violations.append({
                        'type': 'GRAMMAR',
                        'issue': f"Perfective aspect used at A1: '{match}'",
                        'fix': "Use imperfective forms at A1. Perfective taught at A2+."
                    })

    # Check for participles before B1
    if level_code in ('A1', 'A2') and not constraints.get('participles', False):
        for pattern in CASE_PATTERNS['participles']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches[:3]:
                    # Filter out common adjectives that match participle patterns
                    if match.lower() in PARTICIPLE_EXCLUSIONS:
                        continue
                    violations.append({
                        'type': 'GRAMMAR',
                        'issue': f"Participle used before B1: '{match}'",
                        'fix': "Participles not allowed until B1. Use relative clauses or simple sentences."
                    })

    # Check for subordinate clauses at A1
    if level_code == 'A1' and not constraints.get('subordinate_clauses'):
        for pattern in CASE_PATTERNS['subordinate_markers']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches[:3]:
                    violations.append({
                        'type': 'GRAMMAR',
                        'issue': f"Subordinate clause marker at A1: '{match}'",
                        'fix': "Complex sentences not allowed at A1. Use simple SVO sentences."
                    })

    return violations


def check_sentence_complexity(text: str, level_code: str) -> list[dict]:
    """Check sentence complexity against level limits."""
    violations = []
    constraints = GRAMMAR_CONSTRAINTS.get(level_code, GRAMMAR_CONSTRAINTS.get('B2'))
    max_words = constraints.get('max_words_per_sentence', 50)

    sentences = extract_ukrainian_sentences(text)
    for sent in sentences:
        # Only count words with 2+ Cyrillic chars (excludes single-letter endings like -а/-я/-о/-е)
        # Include combining accents (U+0301 stress marks) so "опи́суємо" is one word, not two
        words = re.findall(r'[\u0400-\u04ff\u0301]{2,}', sent)
        # Strip standalone accent marks that aren't part of a word
        words = [w for w in words if any(c in 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюяАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ' for c in w)]
        # Skip drill lists (all-caps syllable/letter sequences like "МА МО МУ НА НО НУ")
        if words and all(w == w.upper() and len(w) <= 3 for w in words):
            continue
        if len(words) > max_words:
            violations.append({
                'type': 'COMPLEXITY',
                'issue': f"Sentence too long for {level_code}: {len(words)} words (max {max_words})",
                'fix': f"Break into shorter sentences. First 5 words: '{' '.join(words[:5])}...'"
            })

    return violations


def check_gender_agreement(content: str, level_code: str) -> list[dict]:
    """Check for noun-adjective gender agreement errors."""
    violations = []

    # Strip deliberate errors (strikethrough ~~wrong form~~) before checking
    from .morphological_validator import _STRIKETHROUGH_RE
    content = _STRIKETHROUGH_RE.sub('', content)

    mismatch_patterns = [
        (r'\b(гарна|нова|стара|велика|мала|добра|погана)\s+(хлопець|чоловік|батько|брат|друг|студент|вчитель)\b',
         'Feminine adjective with masculine noun'),
        (r'\b(гарний|новий|старий|великий|малий|добрий|поганий)\s+(дівчина|жінка|мати|сестра|подруга|студентка|вчителька)\b',
         'Masculine adjective with feminine noun'),
        (r'\b(гарне|нове|старе|велике|мале|добре|погане)\s+(хлопець|дівчина|чоловік|жінка)\b',
         'Neuter adjective with non-neuter noun'),
    ]

    for pattern, desc in mismatch_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            for match in matches[:2]:
                phrase = ' '.join(match) if isinstance(match, tuple) else match
                violations.append({
                    'type': 'AGREEMENT',
                    'issue': f"Gender mismatch: '{phrase}' ({desc})",
                    'fix': "Ensure adjective gender matches noun gender."
                })

    return violations


def check_case_government(content: str, level_code: str) -> list[dict]:
    """Check for preposition + wrong case errors.

    Note: Skipped at A1 because:
    1. These patterns are too simplistic (e.g., "на стіл" is valid accusative)
    2. A1 modules teach these very patterns, creating false positives
    3. Quiz wrong answers (intentional errors) trigger false positives

    Also excludes error-correction sections which intentionally contain errors.
    """
    violations = []

    # Skip at A1 - patterns too simplistic for teaching materials
    if level_code == 'A1':
        return violations

    # Filter out error-correction activity sections which intentionally have wrong forms
    # Pattern: ## error-correction: ... until next ## or # section
    filtered_content = re.sub(
        r'##\s*error-correction:.*?(?=\n##\s|\n#\s|$)',
        '',
        content,
        flags=re.DOTALL | re.IGNORECASE
    )

    # Also filter out quiz/translate wrong answer lines (marked with - [ ])
    # These intentionally contain incorrect options for learners to reject
    filtered_content = re.sub(
        r'^-\s*\[\s*\].*$',
        '',
        filtered_content,
        flags=re.MULTILINE
    )

    # These patterns only catch OBVIOUS errors.
    # Note: Many preposition+nominative combinations are valid:
    # - "на стіл" is valid accusative (inanimate masculine = nominative form)
    # - "з друг" looks wrong but could be valid in some contexts
    # We ONLY flag patterns that are almost always wrong.
    case_errors = [
        # в/у + feminine nominative (should be locative -і or accusative -у)
        (r'\b[ву]\s+(книга|дівчина)\b(?=[^аоуиіюєї]|$)',
         'в/у + Nominative feminine', 'Use Locative (в книзі) or Accusative (в книгу)'),
        # до + feminine nominative (should be genitive -и/-і)
        (r'\bдо\s+(школа|робота)\b(?=[^иі]|$)',
         'до + Nominative feminine', 'Use Genitive (до школи, до роботи)'),
    ]

    for pattern, error_type, fix in case_errors:
        matches = re.findall(pattern, filtered_content, re.IGNORECASE)
        if matches:
            for match in matches[:2]:
                violations.append({
                    'type': 'CASE_GOV',
                    'issue': f"Case government error: {error_type} - '{match}'",
                    'fix': fix
                })

    return violations

