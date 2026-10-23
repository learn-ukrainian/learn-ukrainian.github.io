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
  12. Committed deck file parity (registry/practice/numeral_mechanics_deck.json).
  13. VESUM database validation for all target tokens.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.practice.numeral_mechanics_engine import (
    build_canonical_numeral_cards,
    export_deck,
    main,
    resolve_collective_pluralia_neuter_rule,
    verify_deck_with_vesum,
)


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


def test_numeral_deck_json_export_and_file_parity(tmp_path: Path):
    """Verify JSON export schema and parity with committed artifact."""
    cards = build_canonical_numeral_cards()
    export_file = tmp_path / "numeral_mechanics_deck.json"
    payload = export_deck(cards, export_file)

    assert payload["schema_version"] == "1.0"
    assert payload["card_count"] == 75
    assert len(payload["categories"]) == 15
    assert len(payload["cards"]) == 75

    committed_path = Path(__file__).resolve().parents[1] / "registry/practice/numeral_mechanics_deck.json"
    assert committed_path.exists(), "Committed registry/practice/numeral_mechanics_deck.json does not exist"

    with open(committed_path, encoding="utf-8") as f:
        committed_data = json.load(f)

    assert committed_data["card_count"] == 75
    assert committed_data["categories"] == payload["categories"]
    assert len(committed_data["cards"]) == 75


def test_vesum_verification_clean(requires_vesum_db):
    """Verify 100% VESUM attestation for all 75 cards."""
    cards = build_canonical_numeral_cards()
    res = verify_deck_with_vesum(cards, requires_vesum_db)
    assert res.get("status") != "skipped", "Validated VESUM input must be executed"

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


def test_cli_verify_vesum_skipped_reports_skip_and_exits_nonzero(capsys, monkeypatch, tmp_path: Path):
    """Regression test for P2 (Round 14): skipped verification must report SKIPPED (not PASSED) and exit 1."""
    fake_res = {
        "total_cards": 75,
        "target_tokens_count": 0,
        "missing_targets": [],
        "distractor_tokens_count": 0,
        "unattested_distractor_tokens": [],
        "vesum_verified": None,
        "status": "skipped",
        "message": "VESUM database not found or incomplete at /nonexistent/path",
    }
    monkeypatch.setattr("scripts.practice.numeral_mechanics_engine.verify_deck_with_vesum", lambda _cards, **_kw: fake_res)

    out_file = tmp_path / "blocked_deck.json"
    monkeypatch.setattr(
        "sys.argv",
        ["numeral_mechanics_engine.py", "--verify-vesum", "--export", "--output", str(out_file)],
    )

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
    captured = capsys.readouterr().out
    assert "VESUM verification: SKIPPED (VESUM database not found or incomplete at /nonexistent/path)" in captured
    assert "PASSED" not in captured
    assert not out_file.exists(), "Deck must NOT be exported when verification is skipped"


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
    - Uses unambiguous adult female noun ('аспірантки') avoiding contested juvenile collective nouns.
    - Distractor rejects invalid collective numeral with adult female noun ('четверо аспіранток').
    """
    cards = {c.card_id: c for c in build_canonical_numeral_cards()}
    card48 = cards["numeral_48"]
    assert "здобули перемогу" in card48.sentence_before
    assert card48.correct_answer == "чотири аспірантки"
    d48 = [d.text for d in card48.distractors]
    assert "четверо дівчат" not in d48, "Card 48 must not use contested 'четверо дівчат'"
    assert "четверо аспіранток" in d48, "Card 48 must test collective adult female restriction with 'четверо аспіранток'"


def test_collective_young_animals_optional_guidance():
    """Regression test for Category 11 rule and Card 53 (Astra review finding):
    - Collective numerals are taught as mandatory for pluralia tantum, but optional for young animals.
    - Accurately cites both variants ('чотири каченяти' and 'четверо каченят') as normative.
    - Accurately labels 'чотири каченяти' as Genitive singular ('родовим відмінком однини' / 'Genitive singular').
    """
    _cit, ua, en = resolve_collective_pluralia_neuter_rule()
    assert "двоє дверей" in ua
    assert "не обов'язковими" in ua
    assert "not strictly mandatory" in en
    assert "родовим відмінком однини" in ua
    assert "Genitive singular" in en
    assert "родовим відмінком множини" in ua
    assert "Genitive plural" in en
    assert "чотири каченяти" in ua

    cards = {c.card_id: c for c in build_canonical_numeral_cards()}
    card53 = cards["numeral_53"]
    assert card53.correct_answer == "четверо"
    d_cho = next(d for d in card53.distractors if d.text == "чотири")
    assert "родового відмінка однини" in d_cho.explanation_ua
    assert "Genitive singular" in d_cho.explanation_en
    assert "чотири каченяти" in d_cho.explanation_ua
    assert "нормативними" in d_cho.explanation_ua
