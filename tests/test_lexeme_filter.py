"""Tests for scripts.audit.lexeme_filter — the shared Atlas lexeme predicate.

Pure inline fixtures (no 39 MB manifest needed): the predicate is data-shape logic.
"""

from __future__ import annotations

from scripts.audit.lexeme_filter import (
    DERIVED_FORM_SOURCES,
    GRAMMAR_TERM_POS,
    SURFACE_CLOZE,
    SURFACE_DAILY,
    SURFACE_PRACTICE,
    SURZHYK_SOURCE,
    is_lexeme_entry,
    is_practice_eligible,
    is_surface_admitted,
)


def _noun(**over):
    base = {
        "lemma": "хліб",
        "url_slug": "khlib",
        "gloss": "bread",
        "pos": "noun",
        "primary_source": "built_vocabulary",
        "course_usage": [{"track": "a1", "module_num": 3, "slug": "food", "context": "built_vocabulary"}],
    }
    base.update(over)
    return base


# ---- is_lexeme_entry -------------------------------------------------------------

def test_lexeme_accepts_normal_noun():
    assert is_lexeme_entry(_noun()) is True


def test_lexeme_rejects_grammar_metaterm():
    # The singularia/pluralia-tantum leak the user reported.
    meta = _noun(lemma="singularia tantum", url_slug="singularia-tantum",
                 gloss="singular-only nouns", pos=GRAMMAR_TERM_POS)
    assert is_lexeme_entry(meta) is False


def test_lexeme_rejects_missing_lemma_or_slug():
    assert is_lexeme_entry(_noun(lemma="")) is False
    assert is_lexeme_entry(_noun(url_slug=None)) is False


def test_lexeme_keeps_inflected_form_pages():
    # Form-of pages ARE valid Atlas routes (handled separately by is_practice_eligible);
    # is_lexeme_entry must NOT drop them, only grammar metaterms.
    form = _noun(lemma="Іване", url_slug="ivane",
                 primary_source="built_vocabulary_form")
    assert is_lexeme_entry(form) is True


# ---- is_practice_eligible --------------------------------------------------------

def test_practice_accepts_glossed_course_word():
    assert is_practice_eligible(_noun()) is True


def test_practice_accepts_cefr_only_without_course_usage():
    entry = _noun(course_usage=[], enrichment={"cefr": {"level": "B2"}})
    assert is_practice_eligible(entry) is True


def test_practice_tolerates_cefr_as_bare_string():
    entry = _noun(course_usage=[], enrichment={"cefr": "A2"})
    assert is_practice_eligible(entry) is True


def test_practice_rejects_grammar_metaterm():
    assert is_practice_eligible(_noun(pos=GRAMMAR_TERM_POS)) is False


def test_practice_rejects_surzhyk_to_avoid():
    # Drilling a learner to PRODUCE surzhyk is harmful — daily pool keeps it, deck must not.
    assert is_practice_eligible(_noun(primary_source=SURZHYK_SOURCE)) is False


def test_practice_rejects_derived_forms():
    for src in DERIVED_FORM_SOURCES:
        assert is_practice_eligible(_noun(primary_source=src)) is False


def test_practice_rejects_glossless():
    assert is_practice_eligible(_noun(gloss=None)) is False


def test_practice_rejects_no_curriculum_anchor():
    # No course_usage and no CEFR level -> not curriculum-anchored.
    entry = _noun(course_usage=[], enrichment={})
    assert is_practice_eligible(entry) is False


def test_source_inventory_lexeme_defaults_to_browse_only() -> None:
    entry = _noun(primary_source="source_inventory_grow", course_usage=[])

    assert is_lexeme_entry(entry) is True
    assert is_surface_admitted(entry, SURFACE_DAILY) is False
    assert is_surface_admitted(entry, SURFACE_PRACTICE) is False
    assert is_surface_admitted(entry, SURFACE_CLOZE) is False
    assert is_practice_eligible(entry) is False


def test_source_inventory_practice_requires_explicit_surface_admission() -> None:
    entry = _noun(
        primary_source="source_inventory_grow",
        course_usage=[],
        enrichment={"cefr": {"level": "A1", "source": "fixture", "text": "A1"}},
        surface_admission={SURFACE_PRACTICE: True},
    )

    assert is_surface_admitted(entry, SURFACE_PRACTICE) is True
    assert is_practice_eligible(entry) is True
