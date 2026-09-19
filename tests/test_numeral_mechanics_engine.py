"""Unit and integration tests for Ukrainian Numeral Deep Mechanics Practice Engine.

Tests:
  1. Decades 50–80 inflection rules [Правопис 2019 § 105.4].
  2. Hundreds 200–900 Genitive, Dative, Locative, Instrumental rules [§ 105.5].
  3. Paradigm rules for 40, 90, 100 [§ 105.7].
  4. Numeral + Noun case government: 2, 3, 4 (Nominative plural) vs 5+ (Genitive plural).
  5. Compound numeral last-digit agreement rules.
  6. Collective numeral rules: masculine animate, pluralia tantum, neuter young beings, and female restriction [Синтаксичні норми / § 105.8–10].
  7. Fractional numeral rules: півтора vs півтори + Genitive singular [§ 107].
  8. Ordinal compound declension: only last word inflects [§ 106.2].
  9. Authentic time and approximate quantity constructions.
  10. Deck validation: exactly 75 cards, 15 categories, zero collisions, 4 unique options.
  11. Option shuffling balance across positions 0..3.
  12. Committed deck file parity (data/practice/numeral_mechanics_deck.json).
  13. VESUM database validation for all target tokens.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.practice.numeral_mechanics_engine import (
    NumeralCategory,
    build_canonical_numeral_cards,
    export_deck,
    main,
    resolve_approximate_constructions_rule,
    resolve_cardinal_40_90_100_rule,
    resolve_cardinal_50_80_rule,
    resolve_cardinal_200_900_dative_locative_rule,
    resolve_cardinal_200_900_genitive_rule,
    resolve_cardinal_200_900_instrumental_rule,
    resolve_collective_feminine_restriction_rule,
    resolve_collective_masculine_rule,
    resolve_collective_pluralia_neuter_rule,
    resolve_fractional_pivtora_rule,
    resolve_government_2_3_4_rule,
    resolve_government_5_plus_rule,
    resolve_government_compound_last_digit_rule,
    resolve_ordinal_compound_declension_rule,
    resolve_time_expressions_rule,
    verify_deck_with_vesum,
)


def test_resolve_numeral_rules():
    """Verify all 15 category rule citations and bilingual summaries."""
    cit, ua, en = resolve_cardinal_50_80_rule()
    assert "§ 105.4" in cit
    assert "п'ятдесяти" in ua
    assert "invariant" in en

    cit2, ua2, en2 = resolve_cardinal_200_900_genitive_rule()
    assert "§ 105.5" in cit2
    assert "двохсот" in ua2
    assert "Genitive" in en2

    cit3, ua3, en3 = resolve_cardinal_200_900_dative_locative_rule()
    assert "§ 105.5" in cit3
    assert "-стам" in ua3
    assert "Locative" in en3

    cit4, ua4, en4 = resolve_cardinal_200_900_instrumental_rule()
    assert "§ 105.5" in cit4
    assert "-стами" in ua4
    assert "Instrumental" in en4

    cit5, ua5, en5 = resolve_cardinal_40_90_100_rule()
    assert "§ 105.7" in cit5
    assert "сорока, дев'яноста, ста" in ua5
    assert "oblique" in en5

    _cit6, ua6, en6 = resolve_government_2_3_4_rule()
    assert "називного" in ua6
    assert "Nominative plural" in en6

    _cit7, ua7, en7 = resolve_government_5_plus_rule()
    assert "родового" in ua7
    assert "Genitive plural" in en7

    _cit8, ua8, en8 = resolve_government_compound_last_digit_rule()
    assert "останнім словом" in ua8
    assert "last numeral" in en8

    _cit9, ua9, en9 = resolve_collective_masculine_rule()
    assert "Синтаксичні норми" in _cit9
    assert "105" in _cit9
    assert "троє друзів" in ua9
    assert "collective" in en9.lower()

    _cit10, ua10, en10 = resolve_collective_feminine_restriction_rule()
    assert "Синтаксичні норми" in _cit10
    assert "НЕ вживаються" in ua10
    assert "NOT used with feminine" in en10

    _cit11, ua11, en11 = resolve_collective_pluralia_neuter_rule()
    assert "Синтаксичні норми" in _cit11
    assert "105" in _cit11
    assert "двоє дверей" in ua11
    assert "pluralia tantum" in en11

    _cit12, ua12, en12 = resolve_fractional_pivtora_rule()
    assert "§ 107" in _cit12
    assert "родового відмінка ОДНИНИ" in ua12
    assert "Genitive SINGULAR" in en12

    _cit13, ua13, en13 = resolve_ordinal_compound_declension_rule()
    assert "§ 106.2" in _cit13
    assert "ЛИШЕ ОСТАННЄ" in ua13
    assert "ONLY the last word" in en13

    _cit14, ua14, en14 = resolve_time_expressions_rule()
    assert "о десятій годині" in ua14
    assert "calques" in en14

    _cit15, ua15, en15 = resolve_approximate_constructions_rule()
    assert "інверсією" in ua15
    assert "colloquial" in en15.lower()


def test_build_canonical_numeral_cards_count_and_distribution():
    """Verify card count, category coverage, and exact 5 cards per category."""
    cards = build_canonical_numeral_cards()
    assert len(cards) == 75

    cat_counts = Counter(c.category for c in cards)
    assert len(cat_counts) == 15
    for cat in NumeralCategory:
        assert cat_counts[cat] == 5, f"Category {cat} has {cat_counts[cat]} cards, expected 5"


def test_cards_zero_collision_and_unique_options():
    """Ensure every card has 0 collisions between correct answer and distractors."""
    cards = build_canonical_numeral_cards()

    for card in cards:
        target = card.correct_answer.strip()
        distractor_texts = [d.text.strip() for d in card.distractors]

        assert len(distractor_texts) == 3, f"Card {card.card_id} does not have 3 distractors"
        assert target not in distractor_texts, (
            f"Card {card.card_id} collision: target '{target}' found in distractors {distractor_texts}"
        )
        assert len(set(distractor_texts)) == 3, f"Card {card.card_id} has duplicate distractors: {distractor_texts}"

        options = card.all_options()
        assert len(options) == 4, f"Card {card.card_id} options length != 4"
        assert len(set(options)) == 4, f"Card {card.card_id} options not all unique"
        assert target in options, f"Card {card.card_id} target '{target}' missing from options"


def test_card_prompt_display_and_full_sentence():
    """Verify placeholder replacement and sentence rendering."""
    cards = build_canonical_numeral_cards()
    for card in cards:
        prompt = card.prompt_display
        assert "_______" in prompt, f"Card {card.card_id} prompt missing placeholder: {prompt}"

        full = card.full_sentence
        assert card.correct_answer in full, (
            f"Card {card.card_id} full_sentence missing target '{card.correct_answer}': {full}"
        )


def test_shuffled_options_balanced_distribution():
    """Verify that deterministic shuffle distributes correct answer across positions 0..3."""
    cards = build_canonical_numeral_cards()
    positions = []

    for card in cards:
        opts = card.all_options()
        idx = opts.index(card.correct_answer)
        positions.append(idx)

    pos_counts = Counter(positions)
    for pos in range(4):
        # With 75 cards, expected average is ~18.75 per position; ensure each has >= 10
        assert pos_counts[pos] >= 10, f"Position {pos} count {pos_counts[pos]} is under-represented"


def test_numeral_deck_json_export_and_file_parity(tmp_path: Path):
    """Verify JSON export schema and parity with committed artifact."""
    cards = build_canonical_numeral_cards()
    export_file = tmp_path / "numeral_mechanics_deck.json"
    payload = export_deck(cards, export_file)

    assert payload["schema_version"] == "1.0"
    assert payload["card_count"] == 75
    assert len(payload["categories"]) == 15
    assert len(payload["cards"]) == 75

    committed_path = Path(__file__).resolve().parents[1] / "data/practice/numeral_mechanics_deck.json"
    assert committed_path.exists(), "Committed data/practice/numeral_mechanics_deck.json does not exist"

    with open(committed_path, encoding="utf-8") as f:
        committed_data = json.load(f)

    assert committed_data["card_count"] == 75
    assert committed_data["categories"] == payload["categories"]
    assert len(committed_data["cards"]) == 75


def test_vesum_verification_clean():
    """Verify 100% VESUM attestation for all 75 cards."""
    cards = build_canonical_numeral_cards()
    res = verify_deck_with_vesum(cards)

    assert res["vesum_verified"] is True
    assert len(res["missing_targets"]) == 0, f"Missing target tokens in VESUM: {res['missing_targets']}"
    assert res["target_tokens_count"] >= 50


def test_cli_verify_vesum_json_failure_exits_and_blocks_export(monkeypatch, tmp_path: Path):
    """Regression test for P2: --verify-vesum failure must exit 1 regardless of --json mode and block export."""
    fake_res = {
        "total_cards": 75,
        "target_tokens_count": 88,
        "missing_targets": ["вигаданеслово"],
        "vesum_verified": False,
    }
    monkeypatch.setattr("scripts.practice.numeral_mechanics_engine.verify_deck_with_vesum", lambda _cards, **_kw: fake_res)

    out_file = tmp_path / "blocked_deck.json"
    monkeypatch.setattr(
        "sys.argv",
        ["numeral_mechanics_engine.py", "--verify-vesum", "--json", "--export", "--output", str(out_file)],
    )

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
    assert not out_file.exists(), "Deck must NOT be exported when verification fails"


def test_cli_verify_vesum_json_success_and_export(monkeypatch, tmp_path: Path):
    """Verify that CLI --verify-vesum --json --export succeeds and writes deck on clean verification."""
    fake_res = {
        "total_cards": 75,
        "target_tokens_count": 88,
        "missing_targets": [],
        "vesum_verified": True,
    }
    monkeypatch.setattr("scripts.practice.numeral_mechanics_engine.verify_deck_with_vesum", lambda _cards, **_kw: fake_res)

    out_file = tmp_path / "allowed_deck.json"
    monkeypatch.setattr(
        "sys.argv",
        ["numeral_mechanics_engine.py", "--verify-vesum", "--json", "--export", "--output", str(out_file)],
    )

    main()
    assert out_file.exists(), "Deck should be exported when verification succeeds"


def test_approximate_cards_register_and_unambiguous_distractors():
    """Regression test for Cards 71, 72, 74, and 75 (Astra review findings):
    - Card 71 explicitly specifies official register in the prompt before testing 'близько ста' vs colloquial 'біля ста'.
    - Cards 72, 74, and 75 use unambiguously incorrect distractors (no colloquial 'біля' rejected without formal register prompt).
    """
    cards = {c.card_id: c for c in build_canonical_numeral_cards()}

    card71 = cards["numeral_71"]
    assert "офіційному" in card71.sentence_before.lower(), "Card 71 must establish official register in prompt"
    assert card71.correct_answer == "близько ста"

    card72 = cards["numeral_72"]
    assert card72.correct_answer == "хвилин двадцять"
    d72 = [d.text for d in card72.distractors]
    assert "десь біля двадцяти хвилин" not in d72, "Card 72 must not reject 'десь біля двадцяти хвилин' without register prompt"
    assert "порядка двадцяти хвилин" in d72, "Card 72 should use unambiguously incorrect 'порядка двадцяти хвилин'"

    card74 = cards["numeral_74"]
    assert card74.correct_answer == "з десяток"
    d74 = [d.text for d in card74.distractors]
    assert "десь біля десяти" not in d74, "Card 74 must not reject 'десь біля десяти' without register prompt"
    assert "порядка десяти" in d74, "Card 74 should use unambiguously incorrect 'порядка десяти'"

    card75 = cards["numeral_75"]
    assert card75.correct_answer == "роки три"
    d75 = [d.text for d in card75.distractors]
    assert "біля трьох років" not in d75, "Card 75 must not reject bare 'біля трьох років' without register prompt"
    assert "порядка трьох років" in d75, "Card 75 should use unambiguously incorrect 'порядка трьох років'"


def test_card_48_subject_clarity_and_collective_distractor():
    """Regression test for Card 48 (Astra review finding):
    - Card 48 makes subject reading explicit ('здобули перемогу').
    - Distractor rejects invalid collective numeral with feminine noun ('четверо дівчат').
    - No ambiguous accusative distractor ('чотирьох дівчат').
    """
    cards = {c.card_id: c for c in build_canonical_numeral_cards()}
    card48 = cards["numeral_48"]
    assert "здобули перемогу" in card48.sentence_before
    assert card48.correct_answer == "чотири дівчини"
    d48 = [d.text for d in card48.distractors]
    assert "чотирьох дівчат" not in d48, "Card 48 must not reject accusative 'чотирьох дівчат'"
    assert "четверо дівчат" in d48, "Card 48 must test collective feminine restriction 'четверо дівчат'"
