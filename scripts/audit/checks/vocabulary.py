"""
Vocabulary-related validation checks.

Validates vocabulary section content and checks for words used
but not defined in the vocabulary table.
"""

import re
from ..config import COMMON_WORDS


def extract_vocab_from_section(content: str) -> set[str]:
    """Extract vocabulary words from the Vocabulary section."""
    vocab_words = set()
    vocab_match = re.search(
        r'#+ (?:Vocabulary|Словник).*?(?=\n#|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )
    if vocab_match:
        vocab_text = vocab_match.group(0)
        # Extract from table rows line by line (first column)
        for line in vocab_text.split('\n'):
            if line.strip().startswith('|') and '---' not in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    first_col = parts[1].strip()
                    # Skip header row
                    if first_col.lower() in ('word', 'слово'):
                        continue
                    words = re.findall(r'[\u0400-\u04ff]+', first_col)
                    for w in words:
                        if len(w) > 1:
                            vocab_words.add(w.lower())
    return vocab_words


def check_vocab_violations(content: str, core_content: str, vocab_words: set[str]) -> list[dict]:
    """Check if Ukrainian words in core content are in the vocabulary section."""
    violations = []
    if not vocab_words:
        return violations

    # Extract all Ukrainian words from core content
    core_words = set(re.findall(r'[\u0400-\u04ff]+', core_content.lower()))

    # Find words not in vocab and not common
    unknown_words = core_words - vocab_words - COMMON_WORDS

    # Filter to words that appear multiple times (likely intentional)
    word_counts = {}
    for word in re.findall(r'[\u0400-\u04ff]+', core_content.lower()):
        word_counts[word] = word_counts.get(word, 0) + 1

    significant_unknown = [
        w for w in unknown_words
        if word_counts.get(w, 0) >= 2 and len(w) > 3
    ]

    if significant_unknown[:5]:
        violations.append({
            'type': 'VOCABULARY',
            'issue': f"Words used but not in Vocabulary section: {', '.join(significant_unknown[:5])}",
            'fix': "Add these words to Vocabulary table or replace with known vocabulary."
        })

    return violations


def count_vocab_rows(content: str) -> int:
    """Count vocabulary table rows."""
    vocab_section_match = re.search(
        r'(#+\s+(Vocabulary|Словник).*?)(?=\n#+|$)',
        content, re.DOTALL | re.IGNORECASE
    )
    if vocab_section_match:
        vocab_text = vocab_section_match.group(1)
        lines = vocab_text.split('\n')
        v_rows = len([
            l for l in lines
            if l.strip().startswith('|') and '---' not in l
        ])
        return max(0, v_rows - 1)  # Subtract header
    return 0
