"""
PyMorphy3 wrapper for detecting Russian-shadow word forms and documented calques.

Heuristic tuning rationale:
Ukrainian words are phonetically spelled in Cyrillic (e.g. 'получити', 'здача').
PyMorphy3's RU parser interprets these phonetics effectively.
We determine a 'Russian pattern' if:
1. The deduced normal form is a known Russian word (e.g. 'получити' -> 'получить' -> 1.0 confidence).
2. The parser uses the real DictionaryAnalyzer (meaning it found a known Russian root/suffix, e.g. 'дача' in 'здача').
3. The word is a documented Russianism or active-participle calque (e.g. 'слідуючий', 'учбовий').
4. Otherwise, confidence drops to the FakeDictionary score.
A default threshold of 0.7 correctly separates Russian shadows from clean Ukrainian words.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pymorphy3 import MorphAnalyzer

from scripts.lexicon.calque_corrections import CURATED_CALQUES, LEXICALISED_SAFE

# Global analyzers
_morph_ru = MorphAnalyzer(lang="ru")
_morph_uk = MorphAnalyzer(lang="uk")

# Known Russian-shadow / Russianism lemmas where a VESUM presence should not
# disable heuristic detection (e.g. 'получити', 'здача').
KNOWN_SHADOW_LEMMAS: frozenset[str] = frozenset({
    "получити",
    "получати",
    "здача",
    "відноситися",
    "добавити",
    "хватить",
    "надіятися",
    "скучати",
    "кушати",
    "нравитися",
    "конєшно",
    "вообще",
    "тапочки",
    "обязательно",
    "прикольний",
})


def _is_calque_or_shadow(word: str, *, is_in_vesum: bool = False) -> tuple[bool, bool]:
    """Check if word is a known Russian shadow or documented calque.

    Returns:
        (is_shadow_or_calque, is_documented_calque)
    """
    if word in LEXICALISED_SAFE:
        return False, False

    uk_parses = _morph_uk.parse(word)
    uk_lemma = uk_parses[0].normal_form if uk_parses else word
    if uk_lemma in LEXICALISED_SAFE:
        return False, False

    if word in CURATED_CALQUES or uk_lemma in CURATED_CALQUES:
        return True, True

    if word in KNOWN_SHADOW_LEMMAS or uk_lemma in KNOWN_SHADOW_LEMMAS:
        return True, False

    # Active present participle calques (-уч-/-юч-/-ач-/-яч- expressing active
    # participle). pymorphy3's uk dictionary tags a VESUM-attested permanent-
    # quality adjective (минулий, сплячий, сидячий, стоячий) with actv/Dist
    # alongside its normal adjective reading — that reading is real Ukrainian,
    # not a calque, so only run this heuristic for words VESUM does not know.
    if not is_in_vesum and any(
        "actv" in str(p.tag) or "Dist" in str(p.tag) for p in uk_parses
    ):
        return True, True

    return False, False


def get_ru_confidence(word: str) -> tuple[float, str | None]:
    """
    Returns (confidence_score, russian_lemma).

    If morph analysis fails to find a verified Russian word / dictionary entry,
    russian_lemma is None (we do not invent fake/garbage pymorphy3 lemmas).
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
        # dict_parses is already filtered to DictionaryAnalyzer hits (line
        # above), so a "DictionaryAnalyzer in methods_stack" disjunct here is
        # always true and defeats the word_is_known() check — it let pymorphy3
        # invent a lemma (e.g. 'минулия' for 'минулий') from an unknown-prefix/
        # known-suffix guess that merely touched the RU dictionary. Only a
        # genuinely known RU lemma is reported.
        lemma = best.normal_form if _morph_ru.word_is_known(best.normal_form) else None
        return best.score, lemma

    # Fallback to the top heuristic guess (FakeDictionary / UnknAnalyzer).
    # Failed morph analysis does NOT invent a fake/garbage Russian lemma.
    best = ru_parses[0]
    return best.score, None


def _analyze_word(
    word: str,
    *,
    is_in_vesum: bool,
    threshold: float = 0.7,
) -> dict[str, Any]:
    norm_word = word.lower().strip()
    if not norm_word:
        return {
            "matches_russian": False,
            "russian_lemma": None,
            "ukrainian_alternative": None,
            "confidence": 0.0,
        }

    # Lexicalised safe words (e.g. 'квітучий', 'лежачий', 'блискучий') are always clean negative
    if norm_word in LEXICALISED_SAFE:
        return {
            "matches_russian": False,
            "russian_lemma": None,
            "ukrainian_alternative": None,
            "confidence": 0.0,
        }

    uk_parses = _morph_uk.parse(norm_word)
    uk_lemma = uk_parses[0].normal_form if uk_parses else norm_word
    if uk_lemma in LEXICALISED_SAFE:
        return {
            "matches_russian": False,
            "russian_lemma": None,
            "ukrainian_alternative": None,
            "confidence": 0.0,
        }

    is_shadow, is_documented_calque = _is_calque_or_shadow(
        norm_word, is_in_vesum=is_in_vesum
    )

    # Clean Ukrainian words in VESUM stay negative unless they are known shadows/calques
    if is_in_vesum and not is_shadow:
        return {
            "matches_russian": False,
            "russian_lemma": None,
            "ukrainian_alternative": None,
            "confidence": 0.0,
        }

    conf, ru_lemma = get_ru_confidence(norm_word)

    if is_documented_calque:
        # Documented calques/Russianisms are flagged; morph failure gives None for lemma
        return {
            "matches_russian": True,
            "russian_lemma": ru_lemma,
            "ukrainian_alternative": None,
            "confidence": max(conf, 1.0) if conf < threshold else conf,
        }

    return {
        "matches_russian": conf >= threshold,
        "russian_lemma": ru_lemma,
        "ukrainian_alternative": None,
        "confidence": conf,
    }


def is_russian_pattern(
    word: str,
    threshold: float = 0.7,
    vesum_db_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Analyzes if a word follows Russian morphology or is a documented Russianism/calque.
    """
    norm_word = word.lower().strip()
    if not norm_word:
        return {
            "matches_russian": False,
            "russian_lemma": None,
            "ukrainian_alternative": None,
            "confidence": 0.0,
        }

    from scripts.verification.vesum import verify_word

    is_in_vesum = False
    try:
        vesum_results = (
            verify_word(norm_word)
            if vesum_db_path is None
            else verify_word(norm_word, db_path=vesum_db_path)
        )
        is_in_vesum = bool(vesum_results)
    except Exception:
        # If DB connection fails / DB is not provisioned (e.g. CI fastlane),
        # fall back to the built-in Ukrainian MorphAnalyzer dictionary.
        is_in_vesum = _morph_uk.word_is_known(norm_word)

    return _analyze_word(norm_word, is_in_vesum=is_in_vesum, threshold=threshold)


def check_russian_patterns_batch(
    words: list[str],
    threshold: float = 0.7,
    *,
    verified_words: set[str],
) -> dict[str, dict]:
    """Apply the Russian-shadow heuristic using already-batched VESUM results.

    ``is_russian_pattern`` verifies VESUM for each call. Composite vocabulary
    vetting has already completed that check in one SQL query, so this helper
    preserves the same VESUM check without N extra database lookups.
    """
    normalized_verified = {word.lower().strip() for word in verified_words}
    results: dict[str, dict] = {}
    for raw_word in words:
        norm_word = raw_word.lower().strip()
        is_in_vesum = norm_word in normalized_verified
        results[raw_word] = _analyze_word(
            norm_word,
            is_in_vesum=is_in_vesum,
            threshold=threshold,
        )
    return results
