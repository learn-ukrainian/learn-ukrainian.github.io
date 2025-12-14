"""
Grammar-related validation checks.

Validates grammar constraints, sentence complexity, gender agreement,
and case government rules based on CEFR level.
"""

import re
from ..config import (
    GRAMMAR_CONSTRAINTS, CASE_PATTERNS,
    PARTICIPLE_EXCLUSIONS, NOMINATIVE_PLURAL_EXCLUSIONS,
    FIXED_PHRASES_INSTRUMENTAL, FIXED_PHRASES_DATIVE
)
from ..cleaners import extract_ukrainian_sentences


def is_fixed_phrase(match: str, text: str, phrase_set: set) -> bool:
    """Check if a match is part of a fixed phrase that's taught at A1."""
    match_lower = match.lower()
    text_lower = text.lower()

    # Check if the match appears in any fixed phrase context
    for phrase in phrase_set:
        if phrase in text_lower:
            # Check if match is part of this phrase
            if match_lower in phrase or any(word in match_lower for word in phrase.split()):
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
    constraints = GRAMMAR_CONSTRAINTS.get(level_code, GRAMMAR_CONSTRAINTS.get('B2'))

    # Check forbidden cases at A1
    if level_code == 'A1':
        # Check for Dative
        for pattern in CASE_PATTERNS['dative']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches[:3]:
                    # Filter out nominative plural adjectives that happen to match -ові pattern
                    if match.lower() in NOMINATIVE_PLURAL_EXCLUSIONS:
                        continue
                    # Filter out fixed phrases taught at A1 (e.g., "Бажаю тобі щастя")
                    if is_fixed_phrase(match, text, FIXED_PHRASES_DATIVE):
                        continue
                    violations.append({
                        'type': 'GRAMMAR',
                        'issue': f"Dative case used at A1: '{match}'",
                        'fix': "Dative case not allowed until A2 (M31+). Restructure sentence."
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
        # Only count words with 2+ characters (excludes single-letter endings like -а/-я/-о/-е)
        words = re.findall(r'[\u0400-\u04ff]{2,}', sent)
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
    """
    violations = []

    # Skip at A1 - patterns too simplistic for teaching materials
    if level_code == 'A1':
        return violations

    case_errors = [
        (r'\b[ву]\s+(стіл|книга|хлопець|дівчина|місто)\b(?!\w*[уіаюєоі])',
         'в/у + Nominative', 'Use Locative (в столі) or Accusative (в стіл)'),
        (r'\bз\s+(друг|подруга|брат|сестра)\b(?!\w*[аоюуиі])',
         'з + Nominative', 'Use Genitive (з друга) or Instrumental (з другом)'),
        (r'\bдо\s+(дім|школа|робота|магазин)\b(?!\w*[уаи])',
         'до + Nominative', 'Use Genitive (до дому, до школи)'),
        (r'\bна\s+(стіл|підлога|стіна)\b(?!\w*[іуі])',
         'на + Nominative', 'Use Locative (на столі) or Accusative (на стіл)'),
    ]

    for pattern, error_type, fix in case_errors:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            for match in matches[:2]:
                violations.append({
                    'type': 'CASE_GOV',
                    'issue': f"Case government error: {error_type} - '{match}'",
                    'fix': fix
                })

    return violations
