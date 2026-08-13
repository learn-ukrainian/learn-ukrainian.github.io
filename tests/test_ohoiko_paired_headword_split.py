"""Fixture-level tests for Ohoiko paired-headword split policy (#6370)."""

from __future__ import annotations

from scripts.lexicon.ohoiko_paired_headword_split import (
    classify_split_leg,
    is_single_orthographic_word,
    recover_latin_lookalike,
    resolve_leg_lemma,
    split_paired_headword,
    strip_trailing_parentheticals,
)


def test_split_basic_gender_pair() -> None:
    assert split_paired_headword("актор, акторка") == ["актор", "акторка"]


def test_split_aspect_pair() -> None:
    assert split_paired_headword("бачити, побачити") == ["бачити", "побачити"]


def test_split_strips_whitespace_and_empty_legs() -> None:
    assert split_paired_headword("випити,") == ["випити"]
    assert split_paired_headword(" , акторка , ") == ["акторка"]


def test_strip_trailing_parentheticals_repeated() -> None:
    assert strip_trailing_parentheticals("побитися (1)") == "побитися"
    assert strip_trailing_parentheticals("мати (verb)") == "мати"
    assert strip_trailing_parentheticals("lemma (1) (2)") == "lemma"


def test_split_strips_trailing_parenthetical_on_legs() -> None:
    assert split_paired_headword("битися, побитися (1),") == ["битися", "побитися"]
    assert split_paired_headword("рости, вирости (1),") == ["рости", "вирости"]


def test_multiword_legs_detected() -> None:
    legs = split_paired_headword("боя тися, забоя тися")
    assert legs == ["боя тися", "забоя тися"]
    assert all(not is_single_orthographic_word(leg) for leg in legs)
    assert all(classify_split_leg(leg) == "multiword_after_split" for leg in legs)


def test_english_contaminated_second_leg_is_multiword(requires_vesum_db) -> None:
    legs = split_paired_headword("убивати, to kill (imperfective, perfective)")
    assert legs[0] == "убивати"
    assert classify_split_leg(legs[0]) != "multiword_after_split"
    assert any(classify_split_leg(leg) == "multiword_after_split" for leg in legs[1:])


def test_split_does_not_invent_lemmas() -> None:
    raw = "науковець, науковиця,"
    legs = split_paired_headword(raw)
    assert legs == ["науковець", "науковиця"]
    # No synthetic feminine/masculine forms beyond the split legs.
    assert "науковецька" not in legs


def test_recover_latin_lookalike_twarina_and_zhinka() -> None:
    assert recover_latin_lookalike("тваринa") == "тварина"
    assert recover_latin_lookalike("жiнка") == "жінка"
    assert recover_latin_lookalike("футболiст") == "футболіст"
    assert recover_latin_lookalike("чистий") == "чистий"


def test_resolve_leg_lemma_recovers_ocr_lookalikes() -> None:
    assert resolve_leg_lemma("тваринa") == "тварина"
    assert resolve_leg_lemma("жiнка") == "жінка"
    assert resolve_leg_lemma("футболiст") == "футболіст"

