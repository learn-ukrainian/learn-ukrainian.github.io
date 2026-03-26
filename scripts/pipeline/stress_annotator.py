"""Post-process content to add stress marks using ukrainian-word-stress.

Reads generated .md content, finds Ukrainian words, adds combining acute
accent (U+0301) on the stressed vowel for words with 2+ syllables.
Only marks first occurrence of each word form to avoid visual noise.

Uses sentence-level processing for context-aware heteronym disambiguation.
The Stressifier uses Stanza NLP internally — feeding full sentences allows
it to resolve heteronyms like вікна́ (gen sg) vs ві́кна (nom pl) via POS tags.

Called after content generation, before MDX generation.

Issue: #981, #1019
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

STRESS_MARK = "\u0301"

# If >5% of body words already have stress marks, the file was likely already annotated.
# Empirically: vocab_gen.py pre-stresses ~1-2% of body words via inline examples;
# a fully annotated file has ~15-20%. The 5% threshold sits safely between.
_ALREADY_STRESSED_THRESHOLD = 0.05

# Match Ukrainian words (2+ Cyrillic chars, may include apostrophe/soft sign/stress mark)
# Use lookbehind/lookahead instead of \b — \b doesn't work with Cyrillic
# Include \u0301 (combining acute accent) so already-stressed words are matched whole
_CYRILLIC_WORD_RE = re.compile(
    r"(?<![А-ЯҐЄІЇа-яґєіїʼ'\u0301])([А-ЯҐЄІЇа-яґєіїʼ'\u0301]{2,})(?![А-ЯҐЄІЇа-яґєіїʼ'\u0301])",
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


def _build_sentence_stress_map(
    text: str, orig_words: list[re.Match],
) -> dict[int, str]:
    """Build a map of word positions to their stressed forms using sentence context.

    Feeds the full text to the Stressifier in one call so that Stanza can use
    sentence context for heteronym disambiguation. This is both faster (one
    Stanza pass) and more accurate (full context available).

    Args:
        text: Full document text.
        orig_words: Pre-computed Cyrillic word matches from the text.

    Returns dict mapping match-start-position -> stressed word form.
    """
    stressifier = _get_stressifier()
    stress_map: dict[int, str] = {}

    try:
        stressed_text = stressifier(text)
    except Exception:
        logger.debug("stress_annotator: stressifier failed on full text")
        return stress_map

    stressed_words = list(_CYRILLIC_WORD_RE.finditer(stressed_text))

    if len(orig_words) != len(stressed_words):
        logger.warning(
            "stress_annotator: word count mismatch (%d vs %d), "
            "falling back to per-word stress",
            len(orig_words),
            len(stressed_words),
        )
        for m in orig_words:
            word = m.group(1)
            if _count_syllables(word) < 2 or _already_stressed(word):
                continue
            try:
                stressed = stressifier(word)
            except Exception:
                continue
            if STRESS_MARK in stressed and stressed.replace(STRESS_MARK, "") == word:
                stress_map[m.start(1)] = stressed
        return stress_map

    for orig_m, stress_m in zip(orig_words, stressed_words, strict=False):
        orig_word = orig_m.group(1)
        stressed_word = stress_m.group(1)

        if stressed_word.replace(STRESS_MARK, "") != orig_word:
            continue

        if STRESS_MARK in stressed_word:
            stress_map[orig_m.start(1)] = stressed_word

    return stress_map


def annotate_stress(text: str) -> tuple[str, int]:
    """Add stress marks to Ukrainian words in text.

    Returns (annotated_text, count_of_words_stressed).

    Strategy:
    - Only stress words with 2+ syllables (single-syllable = obvious)
    - Only stress FIRST occurrence of each word form
    - Skip words inside HTML comments, code blocks, URLs, JSX tags
    - Skip words that already have stress marks
    - Use ukrainian-word-stress library with SENTENCE context for disambiguation
    """
    skip_ranges = _build_skip_mask(text)
    matches = list(_CYRILLIC_WORD_RE.finditer(text))

    # Build stress map using sentence-level processing (reuses matches)
    stress_map = _build_sentence_stress_map(text, matches)

    count = 0

    # First pass: find first occurrence of each word form (forward order)
    first_occurrences: dict[str, int] = {}
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

        if first_occurrences.get(lower) != i:
            continue

        if _in_skip_range(m.start(), skip_ranges):
            continue

        if _already_stressed(word):
            continue

        if _count_syllables(word) < 2:
            continue

        stressed = stress_map.get(m.start(1))
        if stressed is None:
            continue

        start, end = m.start(1), m.end(1)
        result[start:end] = list(stressed)
        count += 1

    return "".join(result), count


def annotate_file(path: Path) -> int:
    """Add stress marks to a content .md file in-place.

    Returns count of words stressed.
    """
    if not path.exists():
        return 0

    text = path.read_text("utf-8")

    # Don't re-annotate if the BODY content already has significant stress marks.
    # We exclude the Словник/vocabulary section because vocab_gen.py pre-stresses
    # those words — counting them would falsely trigger the skip threshold.
    # Find the earliest tab marker to isolate body content
    body_text = text
    first_tab_idx = len(text)
    for tab_marker in ("<!-- TAB:Словник -->", "<!-- TAB:Ресурси -->"):
        idx = text.find(tab_marker)
        if idx != -1 and idx < first_tab_idx:
            first_tab_idx = idx
    body_text = text[:first_tab_idx]

    existing = body_text.count(STRESS_MARK)
    word_count = len(body_text.split())
    if word_count > 0 and existing > word_count * _ALREADY_STRESSED_THRESHOLD:
        logger.info("stress_annotator: skipping %s — body already has %d stress marks", path.name, existing)
        return 0

    annotated, count = annotate_stress(text)

    if count > 0:
        path.write_text(annotated, "utf-8")
        logger.info("stress_annotator: added stress marks to %d words in %s", count, path.name)

    return count
