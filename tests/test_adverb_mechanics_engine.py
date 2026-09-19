"""Unit tests for the Adverb Deep Mechanics Practice Engine (Issue #8274).

Covers:
- 15 category rule resolutions and citations
- 75 canonical cards count, distribution, uniqueness, and option balance
- Homophone discrimination feedback logic (adverb vs prepositional phrase)
- Anti-calque distractor feedback logic
- VESUM verification with CI skip guard
- JSON export parity
- CLI --verify-vesum flags (success, failure, and skipped report handling)
"""

import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.practice.adverb_mechanics_engine import (
    AdverbCard,
    AdverbCategory,
    AdverbInterferenceKey,
    build_canonical_adverb_cards,
    export_deck,
    main,
    resolve_anti_calque_rule,
    resolve_cause_purpose_rule,
    resolve_comparison_superlative_rule,
    resolve_comparison_synthetic_rule,
    resolve_homophone_1_rule,
    resolve_homophone_2_rule,
    resolve_manner_action_rule,
    resolve_measure_degree_rule,
    resolve_particles_hyphen_rule,
    resolve_place_direction_rule,
    resolve_prefix_po_rule,
    resolve_reduplication_rule,
    resolve_separate_phrases_rule,
    resolve_time_rule,
    resolve_together_fused_rule,
    verify_deck_with_vesum,
)


def test_resolve_adverb_rules():
    """Verify that all 15 rule resolver functions return valid citations and summaries."""
    resolvers = [
        resolve_manner_action_rule,
        resolve_time_rule,
        resolve_place_direction_rule,
        resolve_measure_degree_rule,
        resolve_cause_purpose_rule,
        resolve_prefix_po_rule,
        resolve_particles_hyphen_rule,
        resolve_reduplication_rule,
        resolve_together_fused_rule,
        resolve_homophone_1_rule,
        resolve_homophone_2_rule,
        resolve_separate_phrases_rule,
        resolve_comparison_synthetic_rule,
        resolve_comparison_superlative_rule,
        resolve_anti_calque_rule,
    ]

    assert len(resolvers) == 15
    for r in resolvers:
        cit, ua, en = r()
        assert "Правопис" in cit
        assert len(ua) > 30
        assert len(en) > 30


def test_build_canonical_adverb_cards_count_and_distribution():
    """Verify that 75 cards are built with exactly 5 cards per category."""
    cards = build_canonical_adverb_cards()
    assert len(cards) == 75

    cat_counts = Counter(c.category for c in cards)
    assert len(cat_counts) == 15

    for cat in AdverbCategory:
        assert cat_counts[cat] == 5, f"Category {cat} does not have exactly 5 cards: {cat_counts[cat]}"


def test_cards_zero_collision_and_unique_options():
    """Verify that card IDs are unique, each card has 4 unique options, and distractors are well-formed."""
    cards = build_canonical_adverb_cards()
    card_ids = [c.card_id for c in cards]
    assert len(card_ids) == len(set(card_ids)), "Duplicate card IDs detected"

    for card in cards:
        opts = card.all_options()
        assert len(opts) == 4, f"Card {card.card_id} does not have exactly 4 options"
        assert len(set(opts)) == 4, f"Card {card.card_id} contains duplicate options: {opts}"
        assert card.correct_answer in opts, f"Card {card.card_id} correct answer not in options"

        distractor_texts = [d.text for d in card.distractors]
        assert len(distractor_texts) == 3
        assert len(set(distractor_texts)) == 3
        assert card.correct_answer not in distractor_texts

        for d in card.distractors:
            assert isinstance(d.interference_key, AdverbInterferenceKey)
            assert len(d.explanation_ua) > 15
            assert len(d.explanation_en) > 15


def test_card_prompt_display_and_full_sentence():
    """Verify that every card prompt contains the blank indicator _______."""
    cards = build_canonical_adverb_cards()
    for card in cards:
        assert "_______" in card.prompt, f"Card {card.card_id} prompt missing blank indicator: {card.prompt}"
        assert card.target_token in card.correct_answer, f"Card {card.card_id} target token mismatch"


def test_shuffled_options_balanced_distribution():
    """Verify that deterministic shuffle distributes correct answer across positions 0..3."""
    cards = build_canonical_adverb_cards()
    positions = []

    for card in cards:
        opts = card.all_options()
        idx = opts.index(card.correct_answer)
        positions.append(idx)

    pos_counts = Counter(positions)
    for pos in range(4):
        # With 75 cards, expected average is ~18.75 per position; ensure each has >= 10
        assert pos_counts[pos] >= 10, f"Position {pos} count {pos_counts[pos]} is under-represented"


def test_adverb_deck_json_export_and_file_parity(tmp_path: Path):
    """Verify JSON export schema and parity with committed artifact."""
    cards = build_canonical_adverb_cards()
    export_file = tmp_path / "adverb_mechanics_deck.json"
    payload = export_deck(cards, export_file)

    assert payload["schema_version"] == "1.0"
    assert payload["card_count"] == 75
    assert len(payload["categories"]) == 15
    assert len(payload["cards"]) == 75

    committed_path = Path(__file__).resolve().parents[1] / "data/practice/adverb_mechanics_deck.json"
    assert committed_path.exists(), "Committed data/practice/adverb_mechanics_deck.json does not exist"

    with open(committed_path, encoding="utf-8") as f:
        committed_data = json.load(f)

    assert committed_data["card_count"] == 75
    assert committed_data["categories"] == payload["categories"]
    assert len(committed_data["cards"]) == 75


@pytest.mark.skipif(
    not Path("data/vesum.db").exists() or Path("data/vesum.db").stat().st_size < 1_000_000,
    reason="Requires full local data/vesum.db (>1MB); CI omits it",
)
def test_vesum_verification_clean():
    """Verify 100% VESUM attestation for all 75 cards."""
    cards = build_canonical_adverb_cards()
    res = verify_deck_with_vesum(cards)
    if res.get("status") == "skipped":
        pytest.skip(res["message"])

    assert res["vesum_verified"] is True
    assert len(res["missing_targets"]) == 0, f"Missing target tokens in VESUM: {res['missing_targets']}"
    assert res["target_tokens_count"] >= 50


def test_cli_verify_vesum_json_failure_exits_and_blocks_export(monkeypatch, tmp_path: Path):
    """Verify that CLI --verify-vesum failure exits 1 and blocks deck export."""
    fake_res = {
        "total_cards": 75,
        "target_tokens_count": 79,
        "missing_targets": ["неіснуючеслово"],
        "vesum_verified": False,
    }
    monkeypatch.setattr(
        "scripts.practice.adverb_mechanics_engine.verify_deck_with_vesum", lambda _cards, **_kw: fake_res
    )

    out_file = tmp_path / "blocked_deck.json"
    monkeypatch.setattr(
        "sys.argv",
        ["adverb_mechanics_engine.py", "--verify-vesum", "--json", "--export", "--output", str(out_file)],
    )

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
    assert not out_file.exists(), "Deck must NOT be exported when verification fails"


def test_cli_verify_vesum_json_success_and_export(monkeypatch, tmp_path: Path):
    """Verify that CLI --verify-vesum --json --export succeeds and writes deck on clean verification."""
    fake_res = {
        "total_cards": 75,
        "target_tokens_count": 79,
        "missing_targets": [],
        "vesum_verified": True,
    }
    monkeypatch.setattr(
        "scripts.practice.adverb_mechanics_engine.verify_deck_with_vesum", lambda _cards, **_kw: fake_res
    )

    out_file = tmp_path / "allowed_deck.json"
    monkeypatch.setattr(
        "sys.argv",
        ["adverb_mechanics_engine.py", "--verify-vesum", "--json", "--export", "--output", str(out_file)],
    )

    main()
    assert out_file.exists(), "Deck should be exported when verification succeeds"


def test_cli_verify_vesum_skipped_reports_skip_and_exits_nonzero(capsys, monkeypatch, tmp_path: Path):
    """Verify that CLI without JSON reports SKIPPED and exits 1 when database is missing."""
    fake_res = {
        "total_cards": 75,
        "target_tokens_count": 0,
        "missing_targets": [],
        "vesum_verified": None,
        "status": "skipped",
        "message": "VESUM database not found or incomplete at /fake/path",
    }
    monkeypatch.setattr(
        "scripts.practice.adverb_mechanics_engine.verify_deck_with_vesum", lambda _cards, **_kw: fake_res
    )

    out_file = tmp_path / "blocked_deck.json"
    monkeypatch.setattr(
        "sys.argv",
        ["adverb_mechanics_engine.py", "--verify-vesum", "--export", "--output", str(out_file)],
    )

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
    captured = capsys.readouterr().out
    assert "VESUM verification: SKIPPED (VESUM database not found or incomplete at /fake/path)" in captured
    assert "PASSED" not in captured
    assert not out_file.exists(), "Deck must NOT be exported when verification is skipped"


def test_homophone_discrimination_card_pairs():
    """Verify that homophone cards correctly discriminate adverb vs noun+preposition."""
    cards_by_id = {c.card_id: c for c in build_canonical_adverb_cards()}

    # Card 46: на пам'ять (noun) vs Card 47: напам'ять (adverb)
    c46 = cards_by_id["adverb_card_46"]
    c47 = cards_by_id["adverb_card_47"]
    assert c46.correct_answer == "на пам'ять"
    assert any(
        d.text == "напам'ять" and d.interference_key == AdverbInterferenceKey.HOMOPHONE_ADVERB_CONFUSION
        for d in c46.distractors
    )
    assert c47.correct_answer == "напам'ять"
    assert any(
        d.text == "на пам'ять" and d.interference_key == AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION
        for d in c47.distractors
    )

    # Card 48: в день (noun) vs Card 49: вдень (adverb)
    c48 = cards_by_id["adverb_card_48"]
    c49 = cards_by_id["adverb_card_49"]
    assert c48.correct_answer == "в день"
    assert c49.correct_answer == "вдень"

    # Card 50: до дому (noun) vs Card 51: додому (adverb)
    c50 = cards_by_id["adverb_card_50"]
    c51 = cards_by_id["adverb_card_51"]
    assert c50.correct_answer == "до дому"
    assert c51.correct_answer == "додому"

    # Card 52: з гори (noun) vs Card 53: згори (adverb)
    c52 = cards_by_id["adverb_card_52"]
    c53 = cards_by_id["adverb_card_53"]
    assert c52.correct_answer == "з гори"
    assert c53.correct_answer == "згори"

    # Card 54: на зустріч (noun) vs Card 55: назустріч (adverb)
    c54 = cards_by_id["adverb_card_54"]
    c55 = cards_by_id["adverb_card_55"]
    assert c54.correct_answer == "на зустріч"
    assert c55.correct_answer == "назустріч"


def test_anti_calque_adverbials():
    """Verify that anti-calque category specifically rejects prominent Russian calques."""
    cards_by_id = {c.card_id: c for c in build_canonical_adverb_cards()}

    c71 = cards_by_id["adverb_card_71"]
    assert c71.correct_answer == "насамперед"
    assert any("в першу чергу" in d.text for d in c71.distractors)

    c72 = cards_by_id["adverb_card_72"]
    assert c72.correct_answer == "навряд чи"
    assert any("вряд ли" in d.text for d in c72.distractors)

    c73 = cards_by_id["adverb_card_73"]
    assert c73.correct_answer == "переважно"
    assert any("в основному" in d.text for d in c73.distractors)

    c74 = cards_by_id["adverb_card_74"]
    assert c74.correct_answer == "принаймні"
    assert any("по крайній мірі" in d.text for d in c74.distractors)

    c75 = cards_by_id["adverb_card_75"]
    assert c75.correct_answer == "у крайньому разі"
    assert any("в крайньому випадку" in d.text for d in c75.distractors)


def test_distractor_exclusivity_and_no_valid_synonym_rejection():
    """Verify that cards do not reject valid Ukrainian words (e.g. скорше) or valid phrases."""
    cards_by_id = {c.card_id: c for c in build_canonical_adverb_cards()}

    # Card 8: щодня must not penalize valid 'кожен день' as a calque
    c8 = cards_by_id["adverb_card_08"]
    distractor_texts_8 = [d.text for d in c8.distractors]
    assert "кожен день" not in distractor_texts_8, "Valid phrase 'кожен день' must not be used as distractor"
    assert "по-щодня" in distractor_texts_8
    assert "що дня" in distractor_texts_8
    assert "що-дня" in distractor_texts_8

    # Card 14: вперед must reject corrupted 'вперід'
    c14 = cards_by_id["adverb_card_14"]
    distractor_texts_14 = [d.text for d in c14.distractors]
    assert "вперід" in distractor_texts_14

    # Card 40: давним-давно must reject morphological corruption 'давнім-давно', not valid 'дуже давно'
    c40 = cards_by_id["adverb_card_40"]
    distractor_texts_40 = [d.text for d in c40.distractors]
    assert "дуже давно" not in distractor_texts_40, "Valid phrase 'дуже давно' must not be marked as error"
    assert "давнім-давно" in distractor_texts_40

    # Card 49: вдень must not penalize valid instrumental noun 'днем'
    c49 = cards_by_id["adverb_card_49"]
    distractor_texts_49 = [d.text for d in c49.distractors]
    assert "днем" not in distractor_texts_49, "Instrumental noun 'днем' must not be used as distractor"
    assert "у день" in distractor_texts_49

    # Card 61: швидше must not reject valid 'скорше' (attested in VESUM as adv:compc)
    c61 = cards_by_id["adverb_card_61"]
    distractor_texts_61 = [d.text for d in c61.distractors]
    assert "скорше" not in distractor_texts_61, "Valid Ukrainian word 'скорше' must not be used as distractor"
    assert "більш швидше" in distractor_texts_61
    assert "швидкіше" in distractor_texts_61

    # Card 64: глибше must not reject superlative 'найглибше' without comparative prompt context
    c64 = cards_by_id["adverb_card_64"]
    distractor_texts_64 = [d.text for d in c64.distractors]
    assert "найглибше" not in distractor_texts_64, "Superlative 'найглибше' must not be rejected in ambiguous prompt"
    assert "самий глибоко" in distractor_texts_64
    assert "більш глибше" in distractor_texts_64

    # Card 74: принаймні must reject orthographic corruption 'принаймі'
    c74 = cards_by_id["adverb_card_74"]
    distractor_texts_74 = [d.text for d in c74.distractors]
    assert "принаймі" in distractor_texts_74

    # Comprehensive deck-wide exclusivity audit across all 75 cards
    for card in cards_by_id.values():
        assert len(card.distractors) == 3
        d_texts = [d.text for d in card.distractors]
        assert len(set(d_texts)) == 3, f"Duplicate distractors in card {card.card_id}"
        assert card.correct_answer not in d_texts, f"Collision in card {card.card_id}: answer in distractors"
        assert card.target_token in card.correct_answer, f"Target token mismatch in card {card.card_id}"


@pytest.mark.skipif(
    not Path("data/vesum.db").exists() or Path("data/vesum.db").stat().st_size < 1_000_000,
    reason="Requires full local data/vesum.db (>1MB); CI omits it",
)
def test_vesum_sanitization_and_malformed_token_detection():
    """Verify that curly apostrophe is normalized and malformed tokens are rejected rather than skipped."""
    base_cards = build_canonical_adverb_cards()
    c1 = base_cards[0]

    # Card with curly apostrophe in answer should pass verification
    curly_card = AdverbCard(
        card_id="test_curly",
        category=c1.category,
        prompt="Тест _______.",
        target_token="напам’ять",
        correct_answer="напам’ять",
        distractors=c1.distractors,
        rule_citation=c1.rule_citation,
        rule_summary_ua=c1.rule_summary_ua,
        rule_summary_en=c1.rule_summary_en,
    )
    res_curly = verify_deck_with_vesum([curly_card])
    assert res_curly["vesum_verified"] is True
    assert len(res_curly["missing_targets"]) == 0

    # Card with malformed/non-Ukrainian token should fail and report card ID
    malformed_card = AdverbCard(
        card_id="test_malformed",
        category=c1.category,
        prompt="Тест _______.",
        target_token="xyz123",
        correct_answer="xyz123",
        distractors=c1.distractors,
        rule_citation=c1.rule_citation,
        rule_summary_ua=c1.rule_summary_ua,
        rule_summary_en=c1.rule_summary_en,
    )
    res_malformed = verify_deck_with_vesum([malformed_card])
    assert res_malformed["vesum_verified"] is False
    assert any("test_malformed" in err for err in res_malformed["missing_targets"])


@pytest.mark.skipif(
    not Path("data/vesum.db").exists() or Path("data/vesum.db").stat().st_size < 1_000_000,
    reason="Requires full local data/vesum.db (>1MB); CI omits it",
)
def test_vesum_rejects_empty_and_punctuation_answers():
    """Verify that empty or punctuation-only card answers fail verification and report offending card IDs."""
    base_cards = build_canonical_adverb_cards()
    valid_card = base_cards[0]

    empty_card = AdverbCard(
        card_id="card_empty",
        category=valid_card.category,
        prompt="Тест _______.",
        target_token="",
        correct_answer="",
        distractors=valid_card.distractors,
        rule_citation=valid_card.rule_citation,
        rule_summary_ua=valid_card.rule_summary_ua,
        rule_summary_en=valid_card.rule_summary_en,
    )

    punct_card = AdverbCard(
        card_id="card_punct",
        category=valid_card.category,
        prompt="Тест _______.",
        target_token="...",
        correct_answer="...",
        distractors=valid_card.distractors,
        rule_citation=valid_card.rule_citation,
        rule_summary_ua=valid_card.rule_summary_ua,
        rule_summary_en=valid_card.rule_summary_en,
    )

    # Deck with valid card + empty card must fail
    res_mixed = verify_deck_with_vesum([valid_card, empty_card])
    assert res_mixed["vesum_verified"] is False
    assert res_mixed["status"] == "failed"
    assert "card_empty" in res_mixed["empty_cards"]
    assert any("card_empty" in err for err in res_mixed["missing_targets"])

    # Deck with valid card + punctuation-only card must fail
    res_punct = verify_deck_with_vesum([valid_card, punct_card])
    assert res_punct["vesum_verified"] is False
    assert res_punct["status"] == "failed"
    assert "card_punct" in res_punct["empty_cards"]
    assert any("card_punct" in err for err in res_punct["missing_targets"])
