"""Small deterministic derivational base candidates for VESUM gaps.

This module is deliberately not an authenticity oracle. It only proposes full
base lemmas for a narrow set of productive Ukrainian derivations; callers must
verify each base with the heritage classifier before accepting a surface form.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

_ACUTE_RE = re.compile("[\u0301\u0300]")
_UK_MORPH_ANALYZER: Any = None
_UK_MORPH_ANALYZER_TRIED = False


def derivational_bases(surface: str) -> list[dict[str, str]]:
    """Return deterministic derivational base evidence rows for ``surface``.

    Rows have ``surface``, ``rule``, and ``base`` keys. The function first
    lemmatises with pymorphy3, then applies a small suffix-rule table to the
    lemma. If pymorphy3 is unavailable, it returns no candidates so the VESUM
    gate degrades to its existing surface/allowlist behavior.

    TODO(stage-2): extend this table for folk-song affective morphology
    (diminutives/augmentatives such as ``ніженьки`` and ``горілонька``) and
    prefixal iteratives (``по-...-увати`` such as ``почитувати``).
    """
    normalized_surface = _normalize(surface)
    if not normalized_surface:
        return []

    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for lemma, tag in _lemma_candidates(normalized_surface):
        if not lemma or "Dist" in tag:
            continue
        for rule, base in _bases_for_lemma(lemma, tag):
            if base == lemma or not _looks_like_single_ukrainian_token(base):
                continue
            key = (rule, base)
            if key in seen:
                continue
            seen.add(key)
            rows.append({"surface": normalized_surface, "rule": rule, "base": base})
    return rows


def _bases_for_lemma(lemma: str, tag: str) -> Iterable[tuple[str, str]]:
    if "ADJF" in tag:
        yield from _denominal_adjective_bases(lemma)
        yield from _deverbal_adjective_bases(lemma)
    if "VERB" in tag or "INFN" in tag:
        yield from _secondary_imperfective_bases(lemma)


def _denominal_adjective_bases(lemma: str) -> Iterable[tuple[str, str]]:
    if lemma.endswith("овий") and len(lemma) > len("овий") + 2:
        stem = lemma[: -len("овий")]
        if stem.endswith(("к", "г", "х", "ц", "ч", "ж", "ш")):
            yield "denominal-adjective:-овий->-а", f"{stem}а"
        yield "denominal-adjective:-овий->consonant", stem

    if lemma.endswith("евий") and len(lemma) > len("евий") + 2:
        stem = lemma[: -len("евий")]
        if stem.endswith("л"):
            yield "denominal-adjective:-евий->-ь", f"{stem}ь"
        yield "denominal-adjective:-евий->consonant", stem

    if lemma.endswith("ний") and len(lemma) > len("ний") + 4:
        stem = lemma[: -len("ний")]
        yield "denominal-adjective:-ний->consonant", stem

    if lemma.endswith("ський") and len(lemma) > len("ський") + 2:
        stem = lemma[: -len("ський")]
        yield "denominal-adjective:-ський->consonant", stem


def _deverbal_adjective_bases(lemma: str) -> Iterable[tuple[str, str]]:
    if lemma.endswith(("увальний", "ювальний")) and len(lemma) > len("вальний") + 2:
        stem = lemma[: -len("вальний")]
        yield "deverbal-adjective:-увальний/-ювальний->-увати/-ювати", f"{stem}вати"
        return

    if lemma.endswith("альний") and len(lemma) > len("альний") + 2:
        stem = lemma[: -len("альний")]
        yield "deverbal-adjective:-альний->-ати", f"{stem}ати"

    if lemma.endswith("ільний") and len(lemma) > len("ьний") + 2:
        stem = lemma[: -len("ьний")]
        yield "deverbal-adjective:-льний->-лити", f"{stem}ити"


def _secondary_imperfective_bases(lemma: str) -> Iterable[tuple[str, str]]:
    if lemma.endswith("увати") and len(lemma) > len("увати") + 2:
        stem = lemma[: -len("увати")]
        if stem.endswith(("ж", "ч", "ш", "щ")):
            yield "secondary-imperfective:-увати->-ити", f"{stem}ити"

    if lemma.endswith("ювати") and len(lemma) > len("ювати") + 2:
        stem = lemma[: -len("ювати")]
        if stem.endswith(("ж", "ч", "ш", "щ")):
            yield "secondary-imperfective:-ювати->-ити", f"{stem}ити"


def _lemma_candidates(surface: str) -> list[tuple[str, str]]:
    analyzer = _uk_morph_analyzer()
    if analyzer is None:
        return []

    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()
    try:
        parses = analyzer.parse(surface)[:5]
    except Exception:
        return []

    for parse in parses:
        lemma = _normalize(str(parse.normal_form or ""))
        if not lemma or lemma in seen:
            continue
        tag = str(parse.tag)
        if not any(part in tag for part in ("ADJF", "VERB", "INFN")):
            continue
        seen.add(lemma)
        candidates.append((lemma, tag))
    return candidates


def _uk_morph_analyzer() -> Any:
    global _UK_MORPH_ANALYZER, _UK_MORPH_ANALYZER_TRIED
    if not _UK_MORPH_ANALYZER_TRIED:
        _UK_MORPH_ANALYZER_TRIED = True
        try:
            import pymorphy3

            _UK_MORPH_ANALYZER = pymorphy3.MorphAnalyzer(lang="uk")
        except Exception:
            _UK_MORPH_ANALYZER = None
    return _UK_MORPH_ANALYZER


def _normalize(text: str) -> str:
    normalized = _ACUTE_RE.sub("", str(text or "").strip().casefold())
    return normalized.replace("`", "ʼ").replace("'", "ʼ").replace("’", "ʼ")


def _looks_like_single_ukrainian_token(text: str) -> bool:
    return bool(re.fullmatch(r"[а-яєіїґʼ-]+", text))
