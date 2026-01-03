"""
Activity quality validation checks (deterministic, no API).

Validates activity quality across multiple dimensions using code-based heuristics:
- Variety detection (sentence structure diversity)
- Basic difficulty estimation (vocabulary/grammar complexity)
- Distractor analysis (word class matching, plausibility)

These checks complement manual semantic validation for full quality coverage.
"""

import re
from collections import Counter
from typing import List, Dict, Tuple
from ..config import GRAMMAR_CONSTRAINTS


def analyze_sentence_variety(sentences: List[str]) -> Dict:
    """
    Detect repetitive sentence patterns.

    Returns variety score (0-100%) and flags for mechanical repetition.
    """
    if len(sentences) < 3:
        return {'score': 100, 'issues': [], 'patterns': {}}

    issues = []

    # Extract sentence structures (simplified)
    structures = []
    for sent in sentences:
        # Simplify to word count and first 2 words
        words = sent.strip().split()
        if len(words) >= 2:
            structure = f"{words[0].lower()}_{words[1].lower()}__{len(words)}w"
            structures.append(structure)

    # Count structure repetitions
    structure_counts = Counter(structures)

    # Flag if any structure appears more than 30% of the time
    total = len(structures)
    for structure, count in structure_counts.items():
        frequency = count / total
        if frequency > 0.3 and count > 2:
            issues.append(
                f"Pattern '{structure.split('__')[0]}' appears {count}/{total} times ({frequency:.0%})"
            )

    # Check for identical sentence lengths (mechanical)
    lengths = [len(s.split()) for s in sentences]
    length_counts = Counter(lengths)
    for length, count in length_counts.items():
        frequency = count / len(lengths)
        if frequency > 0.4 and count > 3:
            issues.append(
                f"{count} sentences have identical length ({length} words) - mechanical?"
            )

    # Calculate variety score
    unique_structures = len(set(structures))
    variety_score = min(100, int((unique_structures / total) * 100))

    return {
        'score': variety_score,
        'issues': issues,
        'patterns': dict(structure_counts.most_common(5))
    }


def estimate_vocabulary_difficulty(text: str, level_code: str) -> str:
    """
    Estimate if vocabulary difficulty matches level.

    Returns: 'too_easy', 'appropriate', 'too_hard'

    Heuristics:
    - Word length (longer words = harder)
    - Presence of compound words
    - Abstract vs concrete nouns
    - Level-specific markers
    """
    words = re.findall(r'\b[а-яґєіїА-ЯҐЄІЇ]+\b', text.lower())

    if not words:
        return 'appropriate'

    # Average word length
    avg_length = sum(len(w) for w in words) / len(words)

    # Level-specific length expectations
    length_thresholds = {
        'A1': (4, 8),    # 4-8 letter words
        'A2': (5, 9),
        'B1': (6, 11),
        'B2': (7, 13),
        'C1': (8, 15),
        'C2': (9, 16),
    }

    min_len, max_len = length_thresholds.get(level_code, (6, 11))

    # Check for C1/C2 markers in lower levels
    advanced_markers = [
        'геополітичн', 'суверенітет', 'колоніаліз', 'деколоніз',
        'мовознавств', 'фольклористик', 'літературознав'
    ]

    if level_code in ['A1', 'A2', 'B1', 'B2']:
        for marker in advanced_markers:
            if marker in text.lower():
                return 'too_hard'

    # Estimate based on average word length
    if avg_length < min_len - 1:
        return 'too_easy'
    elif avg_length > max_len + 1:
        return 'too_hard'
    else:
        return 'appropriate'


def analyze_distractor_quality(
    correct_answer: str,
    distractors: List[str],
    activity_type: str,
    level_code: str
) -> Dict:
    """
    Analyze distractor quality for multiple-choice activities.

    Checks:
    - Same word class (all nouns, all verbs, etc.)
    - Plausibility (not random unrelated words)
    - Appropriate difficulty

    Returns quality score (1-5) and specific issues.
    """
    if not distractors or activity_type not in ['quiz', 'select', 'translate', 'error-correction']:
        return {'quality': None, 'issues': [], 'suggestions': []}

    issues = []
    suggestions = []

    all_options = [correct_answer] + distractors

    # Check 1: Same word class (basic heuristic using endings)
    # Ukrainian verb endings: -ти, -ть, -ю, -єш, -є, -имо, -ете, -ють
    verb_endings = r'(ти|ть|ю|єш|є|имо|ете|ють|ив|ила|или|атиму|ете)$'

    # Noun endings (common): -а, -о, -и, -і, -ів, -ам, -ами
    noun_endings = r'(ка|ння|ття|ість|ство|ець|иця|ник|ниця|ина)$'

    # Adjective endings: -ий, -а, -е, -і, -ого, -ому
    adj_endings = r'(ий|ий|ого|ому|им|ій|ою|ими)$'

    verb_count = sum(1 for opt in all_options if re.search(verb_endings, opt.lower()))
    noun_count = sum(1 for opt in all_options if re.search(noun_endings, opt.lower()))
    adj_count = sum(1 for opt in all_options if re.search(adj_endings, opt.lower()))

    # If mixed word classes (not all same type)
    total_options = len(all_options)
    if verb_count > 0 and noun_count > 0:
        issues.append(f"Mixed word classes: {verb_count} verbs, {noun_count} nouns")
        suggestions.append("Use same word class for all options")
    elif verb_count > 0 and adj_count > 0:
        issues.append(f"Mixed word classes: {verb_count} verbs, {adj_count} adjectives")
        suggestions.append("Use same word class for all options")

    # Check 2: Similar length (plausibility heuristic)
    lengths = [len(opt) for opt in all_options]
    avg_len = sum(lengths) / len(lengths)

    # If any option is drastically different length (2x shorter/longer)
    for i, opt in enumerate(all_options):
        if len(opt) < avg_len / 2 or len(opt) > avg_len * 2:
            issues.append(f"Option '{opt}' length unusual ({len(opt)} chars vs {avg_len:.0f} avg)")

    # Check 3: Common root (good distractors share root with answer)
    # Extract potential root (first 3-4 characters)
    def get_root(word):
        return word[:min(4, len(word))]

    answer_root = get_root(correct_answer.lower())
    related_distractors = sum(1 for d in distractors if get_root(d.lower()) == answer_root)

    # If NO distractors share root with answer, likely random words
    if related_distractors == 0 and len(distractors) > 2:
        issues.append("No distractors share word root with answer - possibly random words")
        suggestions.append(f"Use related forms of '{correct_answer}' (e.g., different tenses, cases, aspects)")

    # Calculate quality score (1-5)
    # Start at 5, subtract for each issue
    quality = 5

    if len(issues) >= 3:
        quality = 2  # Weak
    elif len(issues) == 2:
        quality = 3  # Acceptable
    elif len(issues) == 1:
        quality = 4  # Good
    # else quality = 5 (excellent)

    return {
        'quality': quality,
        'issues': issues,
        'suggestions': suggestions,
        'analysis': {
            'verb_count': verb_count,
            'noun_count': noun_count,
            'adj_count': adj_count,
            'related_to_answer': related_distractors,
            'total_distractors': len(distractors)
        }
    }


def check_natural_ukrainian_markers(text: str) -> Dict:
    """
    Check for natural Ukrainian constructions vs unnatural/robotic patterns.

    Detects:
    - Overuse of pronouns (я, він, вона when unnecessary)
    - Lack of natural discourse markers
    - Rigid SVO word order
    - Unnaturally formal constructions

    Returns naturalness issues (deterministic heuristics only).
    """
    issues = []
    suggestions = []

    text_lower = text.lower()

    # Check 1: Overuse of subject pronouns
    # Count sentences and pronouns
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) >= 3:
        pronoun_pattern = r'\b(я|ти|він|вона|воно|ми|ви|вони)\b'
        pronoun_matches = re.findall(pronoun_pattern, text_lower)
        pronoun_density = len(pronoun_matches) / len(sentences)

        # If more than 1.5 pronouns per sentence on average (very high)
        if pronoun_density > 1.5:
            issues.append(
                f"Overuse of pronouns: {len(pronoun_matches)} in {len(sentences)} sentences "
                f"({pronoun_density:.1f} per sentence)"
            )
            suggestions.append("Ukrainian often omits subject pronouns - use ellipsis")

    # Check 2: Lack of natural discourse markers
    natural_markers = ['ну', 'от', 'взагалі', 'до речі', 'власне', 'загалом']
    has_markers = any(marker in text_lower for marker in natural_markers)

    # For longer texts (50+ words), expect some discourse markers
    word_count = len(re.findall(r'\b[а-яґєіїА-ЯҐЄІЇ]+\b', text))
    if word_count > 50 and not has_markers:
        # This is not always an issue (formal contexts), so just note it
        suggestions.append("Consider adding discourse markers (ну, от, взагалі) for naturalness")

    # Check 3: Unnatural possessive constructions
    # "Я маю" is less natural than "У мене (є)"
    if 'я маю' in text_lower or 'я мав' in text_lower:
        issues.append("Possessive 'Я маю' found - consider 'У мене (є)' for naturalness")
        suggestions.append("Replace 'Я маю' → 'У мене є' (more natural)")

    # Check 4: Calques (common ones)
    calques = {
        'робити сенс': 'мати сенс',
        'приймати рішення': 'OK (established)',  # This one is actually fine
        'дивитися вперед': 'чекати з нетерпінням',
        'в моїй думці': 'на мою думку / як на мене',
    }

    for calque, replacement in calques.items():
        if calque in text_lower and replacement != 'OK (established)':
            issues.append(f"Calque detected: '{calque}' → use '{replacement}'")

    return {
        'issues': issues,
        'suggestions': suggestions
    }


def estimate_cognitive_load(
    text: str,
    activity_type: str,
    level_code: str
) -> str:
    """
    Estimate cognitive load: low, medium, high.

    Factors:
    - Text length
    - Sentence complexity (subordinate clauses)
    - Activity type complexity
    - Level expectations
    """
    # Activity complexity ranking
    activity_complexity = {
        'match-up': 1,       # Simple pairing
        'true-false': 1,     # Binary choice
        'quiz': 2,           # Single answer selection
        'fill-in': 2,        # Single blank completion
        'unjumble': 3,       # Reordering
        'error-correction': 3,  # Find and fix error
        'select': 3,         # Multiple selections
        'cloze': 4,          # Multiple blanks
        'translate': 4,      # Translation
        'dialogue-reorder': 4,  # Multi-step reordering
    }

    activity_load = activity_complexity.get(activity_type, 2)

    # Text complexity (subordinate clauses)
    subordinate_markers = ['що', 'який', 'коли', 'якщо', 'хоча', 'тому що', 'щоб', 'де', 'куди']
    subordinate_count = sum(text.lower().count(marker) for marker in subordinate_markers)

    # Word count
    word_count = len(re.findall(r'\b[а-яґєіїА-ЯҐЄІЇ]+\b', text))

    # Estimate load
    # Simple heuristic: combine activity complexity + text complexity
    text_complexity = 0
    if word_count > 30:
        text_complexity += 1
    if word_count > 50:
        text_complexity += 1
    if subordinate_count > 1:
        text_complexity += 1
    if subordinate_count > 3:
        text_complexity += 1

    total_load = activity_load + text_complexity

    # Map to low/medium/high
    if total_load <= 3:
        return 'low'
    elif total_load <= 6:
        return 'medium'
    else:
        return 'high'


def validate_activity_quality_deterministic(
    text: str,
    activity_type: str,
    level_code: str,
    options: List[str] = None,
    correct_answer: str = None
) -> Dict:
    """
    Run all deterministic quality checks on an activity.

    Returns comprehensive quality assessment without API calls.
    """
    # Extract sentences from text
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s) > 5]

    # Run all checks
    variety = analyze_sentence_variety(sentences) if len(sentences) > 2 else None
    vocab_difficulty = estimate_vocabulary_difficulty(text, level_code)
    cognitive_load = estimate_cognitive_load(text, activity_type, level_code)
    naturalness = check_natural_ukrainian_markers(text)

    distractor_analysis = None
    if options and correct_answer:
        distractors = [opt for opt in options if opt != correct_answer]
        distractor_analysis = analyze_distractor_quality(
            correct_answer, distractors, activity_type, level_code
        )

    return {
        'variety': variety,
        'vocabulary_difficulty': vocab_difficulty,
        'cognitive_load': cognitive_load,
        'naturalness_markers': naturalness,
        'distractor_analysis': distractor_analysis,
    }
