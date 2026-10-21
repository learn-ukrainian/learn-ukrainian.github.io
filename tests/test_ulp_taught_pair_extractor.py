"""Fixture-level tests for ULP taught-pair extractor (#7550 Unit B)."""

from __future__ import annotations

from scripts.lexicon.ulp_taught_pair_extractor import (
    extract_taught_pairs_from_text,
)


def test_extract_basic_margin_pair() -> None:
    sample_text = (
        "Ви не уявляєте, яка я щаслива говорити до вас знову.              уявля́ти ― to imagine\n"
        "записувала нових епізодів, але я повернулася!                     умо́ви ― conditions\n"
    )
    pairs = extract_taught_pairs_from_text(sample_text, source_file="ulp-6-00-lesson-notes", season=6)
    assert len(pairs) == 2
    assert pairs[0].ukrainian_headword == "уявля́ти"
    assert pairs[0].english_gloss == "to imagine"
    assert pairs[0].season == 6
    assert pairs[1].ukrainian_headword == "умо́ви"
    assert pairs[1].english_gloss == "conditions"


def test_extract_key_vocabulary_table_pairs() -> None:
    sample_text = (
        "Key Vocabulary 1-01\n"
        "              моро́зиво                                         ice cream\n"
        "              Приві́т!                                          Hi!\n"
        "              чудо́во                                           great, wonderful (adverb)\n"
    )
    pairs = extract_taught_pairs_from_text(sample_text, source_file="ulp-1-00-lesson-notes", season=1)
    assert len(pairs) == 3
    assert pairs[0].ukrainian_headword == "моро́зиво"
    assert pairs[0].english_gloss == "ice cream"
    assert pairs[1].ukrainian_headword == "Приві́т!"
    assert pairs[1].english_gloss == "Hi!"
    assert pairs[2].ukrainian_headword == "чудо́во"
    assert pairs[2].english_gloss == "great, wonderful (adverb)"


def test_extract_inline_dash_pairs() -> None:
    sample_text = "Чудо́во! — Great! Wonderful!\nДу́же до́бре! — Very good!\nДо́бре. — Fine.\n"
    pairs = extract_taught_pairs_from_text(sample_text, source_file="ulp-1-00-lesson-notes", season=1)
    assert len(pairs) == 3
    assert pairs[0].ukrainian_headword == "Чудо́во!"
    assert pairs[0].english_gloss == "Great! Wonderful!"
    assert pairs[2].ukrainian_headword == "До́бре."
    assert pairs[2].english_gloss == "Fine."


def test_uncurated_note_token_soup_yields_zero_taught_pairs() -> None:
    """Fail-closed: prose / bare tokens / adjacent mixed-language are not taught pairs."""
    soup = (
        # Running UA prose without an Anna EN gloss column
        "Привіт! Мене звати Анна. Сьогодні ми говоримо про погоду.\n"
        # Bare note-token candidates (content_token intake soup)
        "уявляти\n"
        "умови\n"
        "морозиво\n"
        "записувала\n"
        # Adjacent mixed-language material without taught-pair layout (<4 spaces)
        "The transcript mentions привіт near Hi but not as a gloss row.\n"
        "привіт Hi\n"
        "чудово wonderful\n"
        # Reversed EN—UK order (not UK headword + Anna EN gloss)
        "Hello — Привіт\n"
        "Fine. — До́бре.\n"
        # Embedded tokens beside English commentary, not separator glosses
        "She said чудово, and later the commentary used wonderful casually.\n"
        "умови: mentioned in the episode notes without an Anna gloss column\n"
        # Latin inside the UK side fails curated line-shape checks
        "привіт (hello) — not a curated taught pair\n"
    )
    pairs = extract_taught_pairs_from_text(soup, source_file="ulp-1-00-lesson-notes", season=1)
    assert pairs == []
