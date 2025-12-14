"""
Comprehensive pedagogical validation checks.

Runs all pedagogical checks and provides the main entry point
for pedagogical validation.
"""

import re
from collections import Counter

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
)


def check_duplicate_content(content: str) -> list[dict]:
    """Check for duplicate/copy-pasted sentences."""
    violations = []

    # Pre-filter content to remove activity syntax that shouldn't be checked
    # Remove quiz options (- [ ] or - [x]), fill-in options/answers, table rows
    filtered_lines = []
    for line in content.split('\n'):
        stripped = line.strip()
        # Skip quiz checkbox options
        if re.match(r'^-\s*\[[ x]\]', stripped):
            continue
        # Skip blockquote callouts (options, answers, etc.)
        if re.match(r'^>\s*\[!', stripped):
            continue
        # Skip table rows
        if stripped.startswith('|'):
            continue
        # Skip fill-in options inline format
        if '|' in stripped and len(stripped.split('|')) >= 3:
            continue
        filtered_lines.append(line)

    filtered_content = '\n'.join(filtered_lines)

    sentences = []
    for sent in re.findall(r'[А-ЯІЇЄҐа-яіїєґ][^.!?]*[.!?]', filtered_content):
        words = re.findall(r'[\u0400-\u04ff]+', sent)
        if len(words) >= 5:
            normalized = ' '.join(w.lower() for w in words)
            sentences.append((normalized, sent.strip()[:50]))

    sentence_counts = Counter(s[0] for s in sentences)
    duplicates = [(sent, count) for sent, count in sentence_counts.items() if count >= 3]

    if duplicates:
        for sent, count in duplicates[:3]:
            original = next((s[1] for s in sentences if s[0] == sent), sent[:40])
            violations.append({
                'type': 'DUPLICATE',
                'issue': f"Sentence appears {count}x: '{original}...'",
                'fix': "Vary examples to reinforce learning through different contexts."
            })

    return violations


def check_ipa_validation(content: str) -> list[dict]:
    """Check for invalid IPA symbols in vocabulary table."""
    violations = []

    vocab_match = re.search(
        r'^#\s*(Vocabulary|Словник)\s*\n(.*?)(?=\n#\s|\Z)',
        content, re.MULTILINE | re.DOTALL
    )
    if not vocab_match:
        return violations

    vocab_section = vocab_match.group(2)

    valid_ipa = set('ɑɛɪɔuəɐeioaɨʲʃʒʧʤŋɲɾrljwmnbdɡkptfvszhxɦʋʔˈˌːˑ.̪̟̠̹̜̩̯̃̈͡ ')

    ipa_matches = re.findall(r'/([^/\n]+)/', vocab_section)

    for ipa in ipa_matches:
        if len(ipa) > 20 or '(' in ipa or ')' in ipa:
            continue
        invalid_chars = [c for c in ipa if c not in valid_ipa and not c.isspace()]
        if invalid_chars:
            violations.append({
                'type': 'IPA',
                'issue': f"Invalid IPA symbols in /{ipa}/: {invalid_chars}",
                'fix': "Use valid IPA symbols. Check https://en.wikipedia.org/wiki/IPA_for_Ukrainian"
            })
            if len(violations) >= 3:
                break

    return violations


def check_topic_consistency(content: str, frontmatter_str: str) -> list[dict]:
    """Check if content stays on topic based on title/objectives."""
    violations = []

    title_match = re.search(r'^title:\s*(.+)$', frontmatter_str, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""

    objectives_match = re.search(
        r'^objectives:\s*\n((?:\s*-\s*.+\n?)+)',
        frontmatter_str, re.MULTILINE
    )
    objectives = objectives_match.group(1) if objectives_match else ""

    topic_words = set()
    for text in [title, objectives]:
        words = re.findall(r'\b[a-zA-Zа-яА-ЯіїєґІЇЄҐ]{5,}\b', text.lower())
        topic_words.update(words)

    if topic_words:
        topic_mentions = sum(1 for w in topic_words if w in content.lower())
        if topic_mentions < len(topic_words) * 0.3:
            violations.append({
                'type': 'TOPIC',
                'issue': f"Low topic consistency: only {topic_mentions}/{len(topic_words)} key terms from title/objectives found",
                'fix': "Ensure content focuses on stated learning objectives."
            })

    return violations


def run_pedagogical_checks(
    content: str,
    core_content: str,
    level_code: str,
    module_num: int,
    pedagogy: str
) -> list[dict]:
    """Run all pedagogical checks and return violations."""
    all_violations = []

    # Extract frontmatter for some checks
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    frontmatter_str = fm_match.group(1) if fm_match else ""

    # 1. Grammar level violations
    all_violations.extend(check_grammar_violations(core_content, level_code, module_num))

    # 2. Sentence complexity (skip for B2/C1/C2/LIT - advanced levels allow complex sentences)
    if level_code not in ('B2', 'C1', 'C2', 'LIT'):
        all_violations.extend(check_sentence_complexity(core_content, level_code))

    # 3. Vocabulary sync and validation
    # Always sync vocabulary to database (keeps DB in sync with modules)
    vocab_items = extract_vocab_items(content)
    if vocab_items and level_code not in ('LIT',):
        sync_vocab_to_db(level_code, module_num, vocab_items)

    # Vocabulary violations check DISABLED for parallel module creation
    # Vocab is validated at the end when all modules are complete
    # See: npm run vocab:rebuild (after all modules done)

    # 4. Activity sequencing
    all_violations.extend(check_activity_sequencing(content, pedagogy))

    # 5. Answer position bias
    all_violations.extend(check_answer_position_bias(content))

    # 6. Duplicate content (exclude frontmatter to avoid false positives from objectives)
    body_match = re.match(r'^---\n.*?\n---\n(.*)', content, re.DOTALL)
    body_content = body_match.group(1) if body_match else content
    all_violations.extend(check_duplicate_content(body_content))

    # 7. Activity variety
    all_violations.extend(check_activity_variety(content))

    # 8. IPA validation
    all_violations.extend(check_ipa_validation(content))

    # 9. Gender agreement
    all_violations.extend(check_gender_agreement(content, level_code))

    # 10. Case government
    all_violations.extend(check_case_government(content, level_code))

    # 11. Topic consistency
    all_violations.extend(check_topic_consistency(content, frontmatter_str))

    # 12. Match-up misuse
    all_violations.extend(check_matchup_misuse(content))

    # 13. Activity level restrictions
    all_violations.extend(check_activity_level_restrictions(content, level_code, module_num))

    # 14. Activity focus alignment (B1/B2)
    all_violations.extend(check_activity_focus_alignment(content, level_code, module_num, frontmatter_str))

    # 15. Anagram minimum letters (must have 3+ letters)
    all_violations.extend(check_anagram_min_letters(content))

    return all_violations
