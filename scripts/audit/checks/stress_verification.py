"""Deterministic stress mark verification using ukrainian-word-stress.

Extracts Ukrainian words with stress marks (combining acute accent U+0301)
from module content, verifies each against the ukrainian-word-stress dictionary,
and reports mismatches. Context-aware via Stanza for heteronym disambiguation.

Issue: #961, #969 AC1
"""

from __future__ import annotations

import re

# Combining acute accent (U+0301) — the stress mark used in our content
STRESS_MARK = "\u0301"

# Cyrillic word with at least one stress mark
_STRESSED_WORD_RE = re.compile(
    r"[А-ЯҐЄІЇа-яґєіїʼ']*[а-яґєіїА-ЯҐЄІЇ]"  # chars before stress
    + STRESS_MARK
    + r"[А-ЯҐЄІЇа-яґєіїʼ']*",  # chars after stress
    re.UNICODE,
)

# Hyphenated syllable pattern: мо-ло-ко, се-стра, ав-то-бус
_SYLLABLE_PATTERN_RE = re.compile(
    r"[А-ЯҐЄІЇа-яґєіїʼ']{1,5}-[А-ЯҐЄІЇа-яґєіїʼ']{1,5}(?:-[А-ЯҐЄІЇа-яґєіїʼ']{1,5})*",
    re.UNICODE,
)

# Strikethrough (deliberate errors) — skip these
_STRIKETHROUGH_RE = re.compile(r"~~[^~]+~~")

# Lazy-loaded Stressifier
_stressifier = None


def _get_stressifier():
    """Lazy load the Stressifier (loads Stanza model on first call)."""
    global _stressifier
    if _stressifier is None:
        from ukrainian_word_stress import Stressifier, StressSymbol
        _stressifier = Stressifier(stress_symbol=StressSymbol.CombiningAcuteAccent)
    return _stressifier


def _strip_stress(word: str) -> str:
    """Remove all stress marks from a word."""
    return word.replace(STRESS_MARK, "")


def _extract_stressed_words(text: str) -> list[tuple[str, int]]:
    """Extract all stressed Ukrainian words with their approximate line numbers.

    Returns list of (stressed_word, line_number) tuples.
    Skips words inside strikethrough markers and syllable-fragment patterns.
    """
    # Remove strikethrough content
    clean = _STRIKETHROUGH_RE.sub("", text)

    # Find all syllable-break positions to skip
    syllable_spans = set()
    for m in _SYLLABLE_PATTERN_RE.finditer(clean):
        syllable_spans.add((m.start(), m.end()))

    results = []
    for m in _STRESSED_WORD_RE.finditer(clean):
        # Skip if this word is inside a syllable breakdown
        in_syllable = any(
            s <= m.start() and m.end() <= e for s, e in syllable_spans
        )
        if in_syllable:
            continue

        word = m.group()
        # Must have at least one stress mark
        if STRESS_MARK not in word:
            continue
        # Skip single-char + stress (like а́)
        if len(_strip_stress(word)) <= 1:
            continue

        line_num = clean[:m.start()].count("\n") + 1
        results.append((word, line_num))

    return results


def verify_stress_marks(text: str, module_num: int = 0) -> list[dict]:
    """Verify stress marks in Ukrainian text against the stress dictionary.

    Args:
        text: Module content (markdown).
        module_num: Module number (for A1.1 syllable-fragment exemption).

    Returns:
        List of issue dicts with type, severity, text, fix, location.
    """
    stressed_words = _extract_stressed_words(text)
    if not stressed_words:
        return []

    try:
        stressifier = _get_stressifier()
    except Exception as e:
        return [{
            "type": "STRESS_CHECK_ERROR",
            "severity": "INFO",
            "text": f"Stress verification unavailable: {e}",
            "fix": "Install ukrainian-word-stress: pip install ukrainian-word-stress",
        }]

    issues = []
    seen = set()  # Avoid duplicate reports for the same word

    for stressed_word, line_num in stressed_words:
        bare = _strip_stress(stressed_word).lower()
        if bare in seen:
            continue
        seen.add(bare)

        # Get dictionary stress
        try:
            dict_stressed = stressifier(bare)
        except Exception:
            continue

        # If dictionary returns no stress mark, word might not be in dictionary
        if STRESS_MARK not in dict_stressed:
            # Monosyllabic words don't need stress marks — skip
            vowels = sum(1 for c in bare if c in "аеиіоуяюєї")
            if vowels <= 1:
                continue
            issues.append({
                "type": "STRESS_UNKNOWN",
                "severity": "INFO",
                "location": f"~line {line_num}",
                "text": f"Stressed word not in dictionary: {stressed_word} ({bare})",
                "fix": "Verify stress manually — word not found in ukrainian-word-stress dictionary.",
            })
            continue

        # Compare: strip to lowercase for comparison
        content_stress = stressed_word.lower()
        dict_stress = dict_stressed.lower()

        if content_stress != dict_stress:
            issues.append({
                "type": "STRESS_MISMATCH",
                "severity": "HIGH",
                "location": f"~line {line_num}",
                "text": (
                    f"Wrong stress: '{stressed_word}' → should be '{dict_stressed}'"
                ),
                "fix": f"Replace '{stressed_word}' with '{dict_stressed}'.",
            })

    return issues
