"""
PyMorphy3 wrapper for detecting Russian-shadow word forms.

Heuristic tuning rationale:
Ukrainian words are phonetically spelled in Cyrillic (e.g. 'получити', 'здача').
PyMorphy3's RU parser interprets these phonetics effectively.
We determine a 'Russian pattern' if:
1. The deduced normal form is a known Russian word (e.g. 'получити' -> 'получить' -> 1.0 confidence).
2. The parser uses the real DictionaryAnalyzer (meaning it found a known Russian root/suffix, e.g. 'дача' in 'здача').
3. Otherwise, confidence drops to the FakeDictionary score.
A default threshold of 0.7 correctly separates Russian shadows from clean Ukrainian words.
"""

from typing import Optional

from pymorphy3 import MorphAnalyzer

# Global analyzers
_morph_ru = MorphAnalyzer(lang="ru")
_morph_uk = MorphAnalyzer(lang="uk")

def get_ru_confidence(word: str) -> tuple[float, str | None]:
    """
    Returns (confidence_score, russian_lemma).
    """
    ru_parses = _morph_ru.parse(word)
    if not ru_parses:
        return 0.0, None

    # Known Russian word directly?
    for p in ru_parses:
        if _morph_ru.word_is_known(p.normal_form):
            return 1.0, p.normal_form

    # Found in the Russian dictionary?
    dict_parses = [
        p for p in ru_parses
        if any("DictionaryAnalyzer" in str(m[0]) for m in p.methods_stack)
    ]
    if dict_parses:
        best = max(dict_parses, key=lambda p: p.score)
        return best.score, best.normal_form

    # Fallback to the top heuristic guess
    best = ru_parses[0]
    return best.score, best.normal_form

def is_russian_pattern(word: str, threshold: float = 0.7) -> dict:
    """
    Analyzes if a word follows Russian morphology. Returns dict with results.
    """
    word = word.lower().strip()
    if not word:
        return {
            "matches_russian": False,
            "russian_lemma": None,
            "ukrainian_alternative": None,
            "confidence": 0.0
        }

    # Cross-check VESUM: if it's a real Ukrainian lemma, do not flag.
    # We use the existing verify_word from mcp sources/rag logic.
    from scripts.verification.vesum import verify_word
    try:
        vesum_results = verify_word(word)
        if vesum_results:
            # Word exists in VESUM as a valid Ukrainian form
            return {
                "matches_russian": False,
                "russian_lemma": None,
                "ukrainian_alternative": None,
                "confidence": 0.0
            }
    except Exception:
        # If DB connection fails, proceed with heuristic
        pass

    conf, ru_lemma = get_ru_confidence(word)

    return {
        "matches_russian": conf >= threshold,
        "russian_lemma": ru_lemma,
        "ukrainian_alternative": None,  # Without translation dict, we can't reliably guess the UK alt
        "confidence": conf
    }
