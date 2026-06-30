"""Shared predicate: is a manifest entry a real Ukrainian lexeme (Atlas headword)?

Non-lexeme rows leak into the Word Atlas from module ``built_vocabulary`` — chiefly
grammar *metaterms* tagged ``pos == "grammar term"`` (e.g. *singularia tantum*,
*знахідний відмінок*). These render as word cards at ``/lexicon/<slug>/`` and pollute
search, but they are not lemmas a learner looks up. Filter them at the CONSUMERS
(search index, daily pool, practice deck, word-page routes), NOT in the manifest:
the manifest is fingerprint-pinned and shipped as a GitHub Release asset, so editing
it to drop 10/4148 rows would force a disproportionate asset republish (#3775 / the
manifest-scaling decision).

Two predicates, deliberately different in strictness:

* :func:`is_lexeme_entry` — "render as an Atlas word page / show in search". Excludes
  only grammar metaterms. Inflected *form-of* pages (e.g. «Іване» → «Іван») ARE valid
  headword routes and still render.
* :func:`is_practice_eligible` — "use as a study card". Stricter: also drops inflected
  duplicates and ``surzhyk_to_avoid`` forms (drilling a learner to *produce* surzhyk is
  harmful — the daily pool deliberately keeps surzhyk for a "watch out" moment, the
  practice deck must not).

Keep this module dependency-free and import it as ``scripts.audit.lexeme_filter`` (the
generators run via ``python -m scripts.audit.<name>``).
"""

from __future__ import annotations

from typing import Any

# pos value the manifest carries for Latin/Ukrainian grammar metaterms.
GRAMMAR_TERM_POS = "grammar term"

# Inflected / normalized duplicates of a canonical lemma (e.g. "Іване" voc. of "Іван",
# "автобусом" instr. of "автобус"). Not study headwords — the #3450 class.
DERIVED_FORM_SOURCES = frozenset(
    {
        "built_vocabulary_form",
        "built_vocabulary_normalized",
        "built_vocabulary_canonicalized",
    }
)

# Surzhyk forms curated for the Atlas "avoid" tier — shown with a warning, never drilled.
SURZHYK_SOURCE = "surzhyk_to_avoid"

# Source-inventory growth is reviewed enough for Atlas search/browse, but each
# learner-facing surface needs a separate curriculum decision.
SOURCE_INVENTORY_SOURCE = "source_inventory_grow"
SURFACE_ADMISSION_FIELD = "surface_admission"
SURFACE_DAILY = "daily"
SURFACE_PRACTICE = "practice"
SURFACE_CLOZE = "cloze"


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_surface_admitted(entry: dict[str, Any], surface: str) -> bool:
    """True when *entry* may appear on a learner-facing surface.

    Non-source-inventory entries keep their existing behavior. Reviewed
    source-inventory rows default to Atlas search/browse only unless a later
    curriculum decision opts them into the requested surface.
    """
    if entry.get("primary_source") != SOURCE_INVENTORY_SOURCE:
        return True

    admission = entry.get(SURFACE_ADMISSION_FIELD)
    if isinstance(admission, dict):
        return admission.get(surface) is True
    if isinstance(admission, (list, tuple, set)):
        return surface in admission
    return False


def is_lexeme_entry(entry: dict[str, Any]) -> bool:
    """True when *entry* is a real Atlas word-page headword.

    Requires a lemma + url_slug and rejects grammar metaterms. Form-of pages are kept
    (they are legitimate routes); the practice deck drops those separately via
    :func:`is_practice_eligible`.
    """
    if not _has_text(entry.get("lemma")) or not _has_text(entry.get("url_slug")):
        return False
    return entry.get("pos") != GRAMMAR_TERM_POS


def _has_course_usage(entry: dict[str, Any]) -> bool:
    course_usage = entry.get("course_usage")
    if isinstance(course_usage, dict):
        return True
    return isinstance(course_usage, list) and len(course_usage) > 0


def _has_cefr_level(entry: dict[str, Any]) -> bool:
    """True when enrichment carries a CEFR level (any of A1–C2).

    In the real manifest ``enrichment.cefr`` is a dict ``{"level": "A1", ...}``; a bare
    string is tolerated defensively.
    """
    enrichment = entry.get("enrichment")
    cefr = enrichment.get("cefr") if isinstance(enrichment, dict) else None
    level = cefr.get("level") if isinstance(cefr, dict) else cefr
    if _has_text(level):
        return True
    root_cefr = entry.get("cefr")
    root_level = root_cefr.get("level") if isinstance(root_cefr, dict) else root_cefr
    return _has_text(root_level)


def is_practice_eligible(entry: dict[str, Any]) -> bool:
    """True when *entry* is a clean study card for the practice deck.

    Lexeme + glossed + curriculum-anchored (course usage or a CEFR level), excluding
    inflected duplicates and surzhyk-to-avoid forms.
    """
    if not is_lexeme_entry(entry):
        return False
    if not _has_text(entry.get("gloss")):
        return False
    if entry.get("primary_source") in DERIVED_FORM_SOURCES:
        return False
    if entry.get("primary_source") == SURZHYK_SOURCE:
        return False
    if not is_surface_admitted(entry, SURFACE_PRACTICE):
        return False
    return _has_course_usage(entry) or _has_cefr_level(entry)
