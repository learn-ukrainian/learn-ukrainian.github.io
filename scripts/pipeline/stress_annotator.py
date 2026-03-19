"""Post-process content to add stress marks using ukrainian-word-stress.

Reads generated .md content, finds Ukrainian words, adds combining acute
accent (U+0301) on the stressed vowel for words with 2+ syllables.
Only marks first occurrence of each word form to avoid visual noise.

Called after content generation, before MDX generation.

Issue: #981
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

STRESS_MARK = "\u0301"

# Match Ukrainian words (2+ Cyrillic chars, may include apostrophe/soft sign)
# Use lookbehind/lookahead instead of \b — \b doesn't work with Cyrillic
_CYRILLIC_WORD_RE = re.compile(
    r"(?<![А-ЯҐЄІЇа-яґєіїʼ'])([А-ЯҐЄІЇа-яґєіїʼ']{2,})(?![А-ЯҐЄІЇа-яґєіїʼ'])",
    re.UNICODE,
)

# Ukrainian vowels — needed to count syllables
_VOWELS = set("аеиіїоуюяєАЕИІЇОУЮЯЄ")

# Contexts to skip: inside HTML comments, YAML frontmatter, code blocks, URLs
_SKIP_PATTERNS = [
    re.compile(r"<!--.*?-->", re.DOTALL),
    re.compile(r"```.*?```", re.DOTALL),
    re.compile(r"`[^`]+`"),
    re.compile(r"https?://\S+"),
    re.compile(r"<[^>]+>"),  # JSX/HTML tags
]

# Lazy-loaded Stressifier
_stressifier = None


def _get_stressifier():
    """Lazy load the Stressifier (loads Stanza model on first call)."""
    global _stressifier
    if _stressifier is None:
        from ukrainian_word_stress import Stressifier, StressSymbol

        _stressifier = Stressifier(stress_symbol=StressSymbol.CombiningAcuteAccent)
    return _stressifier


def _count_syllables(word: str) -> int:
    """Count syllables by counting vowels."""
    return sum(1 for c in word if c in _VOWELS)


def _already_stressed(word: str) -> bool:
    """Check if word already has a stress mark."""
    return STRESS_MARK in word


def _build_skip_mask(text: str) -> list[tuple[int, int]]:
    """Build list of (start, end) ranges to skip (comments, code, URLs)."""
    ranges = []
    for pattern in _SKIP_PATTERNS:
        for m in pattern.finditer(text):
            ranges.append((m.start(), m.end()))
    # Sort and merge overlapping ranges
    ranges.sort()
    merged = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _in_skip_range(pos: int, skip_ranges: list[tuple[int, int]]) -> bool:
    """Check if position falls within a skip range (binary search)."""
    lo, hi = 0, len(skip_ranges) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        s, e = skip_ranges[mid]
        if pos < s:
            hi = mid - 1
        elif pos >= e:
            lo = mid + 1
        else:
            return True
    return False


def annotate_stress(text: str) -> tuple[str, int]:
    """Add stress marks to Ukrainian words in text.

    Returns (annotated_text, count_of_words_stressed).

    Strategy:
    - Only stress words with 2+ syllables (single-syllable = obvious)
    - Only stress FIRST occurrence of each word form
    - Skip words inside HTML comments, code blocks, URLs, JSX tags
    - Skip words that already have stress marks
    - Use ukrainian-word-stress library (Stanza-backed, context-aware)
    """
    stressifier = _get_stressifier()
    skip_ranges = _build_skip_mask(text)
    seen_forms: set[str] = set()
    count = 0

    # We need to process matches in reverse order so replacements
    # don't shift positions of subsequent matches
    matches = list(_CYRILLIC_WORD_RE.finditer(text))

    # First pass: find first occurrence of each word form (forward order)
    first_occurrences: dict[str, int] = {}  # lowercase form -> match index
    for i, m in enumerate(matches):
        word = m.group(1)
        lower = word.lower().replace(STRESS_MARK, "")
        if lower not in first_occurrences:
            first_occurrences[lower] = i

    # Second pass: annotate only first occurrences (reverse for safe replacement)
    result = list(text)
    for i in reversed(range(len(matches))):
        m = matches[i]
        word = m.group(1)
        lower = word.lower().replace(STRESS_MARK, "")

        # Skip if not first occurrence
        if first_occurrences.get(lower) != i:
            continue

        # Skip if in a skip range
        if _in_skip_range(m.start(), skip_ranges):
            continue

        # Skip if already stressed
        if _already_stressed(word):
            continue

        # Skip single-syllable words
        if _count_syllables(word) < 2:
            continue

        # Skip if already seen (shouldn't happen with first_occurrences, but safety)
        if lower in seen_forms:
            continue

        # Get stressed form from library (Stressifier is callable)
        try:
            stressed = stressifier(word)
        except Exception:
            continue

        # Verify stress was actually added
        if STRESS_MARK not in stressed:
            continue

        # Verify the stressed form is the same word (not a different word)
        if stressed.replace(STRESS_MARK, "") != word:
            continue

        # Replace in the result
        start, end = m.start(1), m.end(1)
        result[start:end] = list(stressed)
        seen_forms.add(lower)
        count += 1

    return "".join(result), count


def annotate_file(path: Path) -> int:
    """Add stress marks to a content .md file in-place.

    Returns count of words stressed.
    """
    if not path.exists():
        return 0

    text = path.read_text("utf-8")

    # Don't re-annotate if already has significant stress marks
    existing = text.count(STRESS_MARK)
    word_count = len(text.split())
    if existing > word_count * 0.02:  # >2% of words already stressed
        logger.info("stress_annotator: skipping %s — already has %d stress marks", path.name, existing)
        return 0

    annotated, count = annotate_stress(text)

    if count > 0:
        path.write_text(annotated, "utf-8")
        logger.info("stress_annotator: added stress marks to %d words in %s", count, path.name)

    return count
