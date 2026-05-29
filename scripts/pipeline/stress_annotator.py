"""Post-process content to add stress marks using ukrainian-word-stress.

Reads generated .md content, finds Ukrainian words, adds combining acute
accent (U+0301) on the stressed vowel for words with 2+ syllables.
Marks every multi-syllable Ukrainian word occurrence. The annotator is
idempotent: already-stressed words are preserved and are not double-marked.

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

# Match Ukrainian words (2+ Cyrillic chars, may include apostrophe/soft sign/stress mark)
# Use lookbehind/lookahead instead of \b — \b doesn't work with Cyrillic
# Include \u0301 (combining acute accent) so already-stressed words are matched whole
_CYRILLIC_BASE_CLASS = "А-ЯҐЄІЇа-яґєії"
_CYRILLIC_LETTER_CLASS = f"{_CYRILLIC_BASE_CLASS}\u0301"
_CYRILLIC_WORD_RE = re.compile(
    rf"(?<![{_CYRILLIC_LETTER_CLASS}])"
    rf"([{_CYRILLIC_BASE_CLASS}][{_CYRILLIC_LETTER_CLASS}]*(?:[ʼ'][{_CYRILLIC_BASE_CLASS}][{_CYRILLIC_LETTER_CLASS}]*)*)"
    rf"(?![{_CYRILLIC_LETTER_CLASS}])",
    re.UNICODE,
)

# Ukrainian vowels — needed to count syllables
_VOWELS = set("аеиіїоуюяєАЕИІЇОУЮЯЄ")

# Contexts to skip: inside HTML comments, code blocks, URLs, JSX/HTML tags.
# DialogueBox uk="..." values are annotated in a focused second pass because
# they are learner-facing Ukrainian inside an otherwise-skipped JSX tag.
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
            if STRESS_MARK in stressed and stressed.replace(STRESS_MARK, "") == word.replace(STRESS_MARK, ""):
                stress_map[m.start(1)] = stressed
        return stress_map

    for orig_m, stress_m in zip(orig_words, stressed_words, strict=False):
        orig_word = orig_m.group(1)
        stressed_word = stress_m.group(1)

        # Strip stress marks from BOTH sides before comparing — the original
        # text may already contain some stress marks from vocab_gen or manual
        # annotation. Without this, pre-stressed words like "Зву́ки" fail the
        # comparison because stressed_clean="Звуки" != orig="Зву́ки".
        if stressed_word.replace(STRESS_MARK, "") != orig_word.replace(STRESS_MARK, ""):
            continue

        if STRESS_MARK in stressed_word:
            stress_map[orig_m.start(1)] = stressed_word

    return stress_map


_DIALOGUEBOX_UK_ATTR_RE = re.compile(
    r"(<DialogueBox\b[^>]*\buk\s*=\s*\")(?P<uk>[^\"]*)(\")",
    re.DOTALL,
)


def _annotate_dialoguebox_uk_attrs(text: str) -> tuple[str, int]:
    """Annotate Ukrainian inside DialogueBox uk="..." props only."""
    total = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal total
        value = match.group("uk")
        annotated, count = annotate_stress(value)
        total += count
        return f"{match.group(1)}{annotated}{match.group(3)}"

    return _DIALOGUEBOX_UK_ATTR_RE.sub(replace, text), total


def annotate_stress(text: str) -> tuple[str, int]:
    """Add stress marks to Ukrainian words in text.

    Returns (annotated_text, count_of_words_stressed).

    Strategy:
    - Only stress words with 2+ syllables (single-syllable = obvious)
    - Skip words inside HTML comments, code blocks, URLs, JSX tags
    - Skip words that already have stress marks
    - Add a focused second pass for DialogueBox uk="..." values
    - Use ukrainian-word-stress library with SENTENCE context for disambiguation
    """
    skip_ranges = _build_skip_mask(text)
    matches = list(_CYRILLIC_WORD_RE.finditer(text))

    # Build stress map using sentence-level processing (reuses matches)
    stress_map = _build_sentence_stress_map(text, matches)

    count = 0

    # Per-word fallback: if the sentence-level stressifier didn't stress a word,
    # try stressing it in isolation. The sentence processor sometimes drops words
    # (especially in mixed-language or tabular content).
    stressifier = _get_stressifier()
    for m in matches:
        pos = m.start(1)
        if pos in stress_map:
            continue
        word = m.group(1)
        clean = word.replace(STRESS_MARK, "")
        if _count_syllables(clean) < 2:
            continue
        try:
            stressed = stressifier(clean)
        except Exception:
            continue
        if STRESS_MARK in stressed and stressed.replace(STRESS_MARK, "") == clean:
            stress_map[pos] = stressed

    # Annotate every eligible occurrence (reverse for safe replacement).
    result = list(text)
    for i in reversed(range(len(matches))):
        m = matches[i]
        word = m.group(1)

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

    annotated = "".join(result)
    annotated, attr_count = _annotate_dialoguebox_uk_attrs(annotated)
    return annotated, count + attr_count


def annotate_file(path: Path) -> int:
    """Add stress marks to a content .md file in-place.

    Returns count of words stressed.
    """
    if not path.exists():
        return 0

    text = path.read_text("utf-8")

    annotated, count = annotate_stress(text)

    if count > 0:
        path.write_text(annotated, "utf-8")
        logger.info("stress_annotator: added stress marks to %d words in %s", count, path.name)

    return count
