"""Diminutive/augmentative English gloss fallback for the reenrich translation path.

Dictionaries index the root lemma, so derived nouns such as «білочка» or
«вовчище» frequently come back from the sourced translation lookups with no
English gloss of their own. When the base noun lives in the same manifest and
already carries a sourced ``translation.en``, this module derives a labeled
fallback gloss: base EN + ``" (diminutive)"`` / ``" (augmentative)"``.

The fallback is deliberately conservative:

- base candidates come from a small deterministic suffix table — never from
  invented lemmas;
- a candidate is accepted only when it exists as a noun entry in the same
  manifest with a non-empty, sourced ``translation.en``;
- when the in-repo VESUM database is reachable, both the surface form and the
  base noun must be VESUM-attested (base as a noun); when VESUM is unavailable
  the manifest-membership gate alone applies.

Integration (#6876): call :func:`derived_translation_fallback` from the
reenrich translation path (``scripts/lexicon/reenrich_thin_manifest_entries.py``,
``_translation_for_entry`` fallback chain) after the direct and VESUM-base
lookups miss. It is intentionally not wired there yet to avoid colliding with
the AGY adverb lane working in the same file.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from typing import Any

DIMINUTIVE = "diminutive"
AUGMENTATIVE = "augmentative"

_ACUTE_RE = re.compile("[\u0301\u0300]")
_MIN_STEM_LEN = 3
_HUSHING_TO_VELAR = {"ж": "г", "ч": "к", "ш": "х"}

# verify callable shape: (word, pos_filter) -> list of VESUM match dicts.
VesumVerify = Callable[[str, str | None], list[dict]]


def derived_base_candidates(lemma: str) -> list[dict[str, str]]:
    """Return deterministic diminutive/augmentative base candidates for ``lemma``.

    Rows have ``surface``, ``kind``, ``rule``, and ``base`` keys. This is not an
    authenticity oracle: callers must confirm each candidate against the
    manifest (and VESUM, when available) before accepting it.
    """
    normalized = _normalize(lemma)
    if not normalized:
        return []

    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for kind, rule, base in _iter_rule_bases(normalized):
        if base == normalized or base in seen:
            continue
        if not _looks_like_single_ukrainian_token(base):
            continue
        seen.add(base)
        rows.append({"surface": normalized, "kind": kind, "rule": rule, "base": base})
    return rows


def manifest_lemma_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build a normalized-lemma → entry index over a manifest's entries."""
    index: dict[str, dict[str, Any]] = {}
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        return index
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = _normalize(entry.get("lemma"))
        if key and key not in index:
            index[key] = entry
    return index


def derived_translation_fallback(
    entry: dict[str, Any],
    entries_by_lemma: Mapping[str, dict[str, Any]],
    *,
    vesum_verify: VesumVerify | bool | None = None,
) -> dict[str, Any] | None:
    """Derive a labeled EN translation for a diminutive/augmentative noun entry.

    ``entries_by_lemma`` maps normalized lemmas to manifest entries (see
    :func:`manifest_lemma_index`). ``vesum_verify`` controls the VESUM gate:
    ``None`` auto-detects the in-repo VESUM database and degrades gracefully
    when it is unreachable, ``False`` skips the check, and a callable is used
    as-is (``(word, pos_filter) -> matches``).

    Returns a ``{"en": [...], "source": ...}`` translation block, or ``None``
    when no manifest-resident base noun with a sourced EN gloss exists.
    """
    lemma = _normalize(entry.get("lemma"))
    if not lemma or not _is_noun_pos(entry.get("pos")):
        return None

    verify = _resolve_vesum_verify(vesum_verify)
    for candidate in derived_base_candidates(lemma):
        base = candidate["base"]
        base_entry = entries_by_lemma.get(_normalize(base))
        if base_entry is None or not _is_noun_pos(base_entry.get("pos")):
            continue
        translation = _sourced_translation(base_entry)
        if translation is None:
            continue
        if not _vesum_accepts(verify, lemma, base):
            continue
        return _build_translation(translation, candidate)
    return None


def _iter_rule_bases(lemma: str) -> Iterable[tuple[str, str, str]]:
    yield from _diminutive_rule_bases(lemma)
    yield from _augmentative_rule_bases(lemma)


def _diminutive_rule_bases(lemma: str) -> Iterable[tuple[str, str, str]]:
    for suffix in ("очка", "ечка"):
        stem = _stem_before_suffix(lemma, suffix)
        if stem:
            yield DIMINUTIVE, f"noun-diminutive:-{suffix}->-ка", f"{stem}ка"
            yield DIMINUTIVE, f"noun-diminutive:-{suffix}->-а", f"{stem}а"

    for suffix in ("онька", "енька"):
        stem = _stem_before_suffix(lemma, suffix)
        if stem:
            yield DIMINUTIVE, f"noun-diminutive:-{suffix}->-ка", f"{stem}ка"
            yield DIMINUTIVE, f"noun-diminutive:-{suffix}->-а", f"{stem}а"
            for velar in _hushing_to_velar_stems(stem):
                yield DIMINUTIVE, f"noun-diminutive:-{suffix}->velar-а", f"{velar}а"

    for suffix in ("очко", "ечко", "енько"):
        stem = _stem_before_suffix(lemma, suffix)
        if stem:
            yield DIMINUTIVE, f"noun-diminutive:-{suffix}->-о", f"{stem}о"
            yield DIMINUTIVE, f"noun-diminutive:-{suffix}->-е", f"{stem}е"
            yield DIMINUTIVE, f"noun-diminutive:-{suffix}->-це", f"{stem}це"

    stem = _stem_before_suffix(lemma, "енятко")
    if stem:
        yield DIMINUTIVE, "noun-diminutive:-енятко->-еня", f"{stem}еня"
        yield DIMINUTIVE, "noun-diminutive:-енятко->-я", f"{stem}я"
        yield DIMINUTIVE, "noun-diminutive:-енятко->-а", f"{stem}а"

    stem = _stem_before_suffix(lemma, "ятко")
    if stem:
        yield DIMINUTIVE, "noun-diminutive:-ятко->-я", f"{stem}я"
        yield DIMINUTIVE, "noun-diminutive:-ятко->-а", f"{stem}а"

    for suffix in ("очок", "ечок", "ок", "ик"):
        stem = _stem_before_suffix(lemma, suffix)
        if stem:
            yield DIMINUTIVE, f"noun-diminutive:-{suffix}->stem", stem
            for velar in _hushing_to_velar_stems(stem):
                yield DIMINUTIVE, f"noun-diminutive:-{suffix}->velar-stem", velar
            yield DIMINUTIVE, f"noun-diminutive:-{suffix}->-о", f"{stem}о"


def _augmentative_rule_bases(lemma: str) -> Iterable[tuple[str, str, str]]:
    for suffix in ("ище", "іще"):
        stem = _stem_before_suffix(lemma, suffix)
        if stem:
            yield AUGMENTATIVE, f"noun-augmentative:-{suffix}->stem", stem
            yield AUGMENTATIVE, f"noun-augmentative:-{suffix}->-а", f"{stem}а"
            yield AUGMENTATIVE, f"noun-augmentative:-{suffix}->-о", f"{stem}о"
            for velar in _hushing_to_velar_stems(stem):
                yield AUGMENTATIVE, f"noun-augmentative:-{suffix}->velar-stem", velar
                yield AUGMENTATIVE, f"noun-augmentative:-{suffix}->velar-а", f"{velar}а"

    for suffix in ("ища", "іща"):
        stem = _stem_before_suffix(lemma, suffix)
        if stem:
            yield AUGMENTATIVE, f"noun-augmentative:-{suffix}->-а", f"{stem}а"
            yield AUGMENTATIVE, f"noun-augmentative:-{suffix}->stem", stem
            for velar in _hushing_to_velar_stems(stem):
                yield AUGMENTATIVE, f"noun-augmentative:-{suffix}->velar-а", f"{velar}а"

    stem = _stem_before_suffix(lemma, "юга")
    if stem:
        yield AUGMENTATIVE, "noun-augmentative:-юга->stem", stem
        yield AUGMENTATIVE, "noun-augmentative:-юга->-а", f"{stem}а"


def _sourced_translation(base_entry: dict[str, Any]) -> dict[str, Any] | None:
    enrichment = base_entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return None
    translation = enrichment.get("translation")
    if not isinstance(translation, dict):
        return None
    terms = translation.get("en")
    if not isinstance(terms, list) or not any(str(term).strip() for term in terms):
        return None
    if not str(translation.get("source") or "").strip():
        return None
    return translation


def _build_translation(base_translation: dict[str, Any], candidate: dict[str, str]) -> dict[str, Any]:
    kind = candidate["kind"]
    base = candidate["base"]
    first_en = next(str(term).strip() for term in base_translation["en"] if str(term).strip())
    source = str(base_translation.get("source") or "").strip()
    label = f"{kind} of {base}"
    return {
        "en": [f"{first_en} ({kind})"],
        "source": f"{source} ({label})" if source else label,
    }


def _resolve_vesum_verify(vesum_verify: VesumVerify | bool | None) -> VesumVerify | None:
    if vesum_verify is False:
        return None
    if callable(vesum_verify):
        return vesum_verify

    def _auto_verify(word: str, pos_filter: str | None) -> list[dict]:
        from scripts.verification.vesum import verify_word

        return verify_word(word, pos_filter=pos_filter)

    try:
        _auto_verify("вода", "noun")
    except Exception:
        return None
    return _auto_verify


def _vesum_accepts(verify: VesumVerify | None, surface: str, base: str) -> bool:
    if verify is None:
        return True
    try:
        if not verify(surface, None):
            return False
        return bool(verify(base, "noun"))
    except Exception:
        return True


def _is_noun_pos(pos: object) -> bool:
    normalized = str(pos or "").strip().casefold()
    return bool(re.match(r"noun(?![a-z])", normalized))


def _stem_before_suffix(lemma: str, suffix: str) -> str | None:
    if not lemma.endswith(suffix) or len(lemma) < len(suffix) + _MIN_STEM_LEN:
        return None
    return lemma[: -len(suffix)]


def _hushing_to_velar_stems(stem: str) -> Iterable[str]:
    replacement = _HUSHING_TO_VELAR.get(stem[-1:])
    if replacement:
        yield f"{stem[:-1]}{replacement}"


def _normalize(text: object) -> str:
    normalized = _ACUTE_RE.sub("", str(text or "").strip().casefold())
    return normalized.replace("`", "ʼ").replace("'", "ʼ").replace("’", "ʼ")


def _looks_like_single_ukrainian_token(text: str) -> bool:
    return bool(re.fullmatch(r"[а-яєіїґʼ-]+", text))
