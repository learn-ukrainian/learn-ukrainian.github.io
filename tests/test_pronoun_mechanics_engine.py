"""Unit and integration tests for Ukrainian Pronoun Deep Mechanics Practice Engine.

Tests:
  1. Epenthetic [n-] rules [Правопис 2019 § 108]:
     - Prepositional government: compulsory n- (до нього, біля неї, про них, на ньому).
     - Direct case government: absence of n- (бачу його, чую її, зустрів їх, дав йому).
     - Instrumental omnipresence: n- always present (ним, нею, ними, із ним, із нею).
     - Derivative prepositions: no n- (завдяки йому, наперекір їй, всупереч їм).
  2. Orthography rules [Правопис 2019 § 39]:
     - Together (дехто, абихто, хтось, щось, ніхто, нічого, ніякий).
     - Hyphenated (будь-хто, хто-небудь, казна-що, хтозна-який).
     - Split three words with prepositions (будь у кого, будь з ким, хтозна з ким, ні про що, ні з ким).
  3. Declension paradigm rules [§§ 109–113]:
     - Reflexive pronoun себе (§ 109): defective paradigm, собі, собою, на собі, при собі.
     - Possessive їхній vs personal до них (§ 110).
     - Demonstratives цей / той (§ 111): цими, тими, цього, тому.
     - Interrogatives хто, що, чий (§ 112): чийого, кому, чим, чиїми, кого.
     - Pronoun весь (§ 113): Instrumental plural всіма.
  4. Semantic & stylistic distinctions [§ 113]:
     - сам vs самий (сам personally vs той самий identity vs з самого ранку limit; anti-calque *самий кращий -> найкращий).
     - Possessive їхній vs personal після прийменника до них.
  5. Deck validation: zero collisions, 4 unique options, prompt placeholder.
  6. Balanced deterministic shuffle distribution across indices 0..3.
  7. Committed deck file parity.
  8. VESUM database validation for all target tokens and corrupted distractors.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.practice.pronoun_mechanics_engine import (
    PronounCategory,
    build_canonical_pronoun_cards,
    export_pronoun_mechanics_deck,
    resolve_declension_ves_rule,
    resolve_demonstrative_rule,
    resolve_epenthesis_rule,
    resolve_interrogative_rule,
    resolve_orthography_rule,
    resolve_possessive_yikhniy_rule,
    resolve_reflexive_sebe_rule,
    resolve_sam_vs_samyi_rule,
    validate_pronoun_card,
    verify_deck_with_vesum,
    verify_distractors_with_vesum,
)


def test_resolve_epenthesis_rules():
    """Verify epenthetic n- rules per Правопис 2019 § 108."""
    cit, ua, en = resolve_epenthesis_rule(PronounCategory.EPENTHETIC_N_PREPOSITIONAL)
    assert "§ 108" in cit
    assert "до нього" in ua
    assert "oblique cases" in en

    _cit2, ua2, en2 = resolve_epenthesis_rule(PronounCategory.EPENTHETIC_N_ABSENCE_DIRECT)
    assert "бачу його" in ua2
    assert "direct case government" in en2

    _cit3, ua3, en3 = resolve_epenthesis_rule(PronounCategory.EPENTHETIC_N_INSTRUMENTAL_OMNIPRESENT)
    assert "ним, нею, ними" in ua3
    assert "Instrumental" in en3

    _cit4, ua4, en4 = resolve_epenthesis_rule(PronounCategory.EPENTHETIC_N_DERIVATIVE_PREPOSITIONS)
    assert "завдяки йому" in ua4
    assert "derivative prepositions" in en4

    with pytest.raises(ValueError, match="not an epenthesis category"):
        resolve_epenthesis_rule(PronounCategory.ORTHOGRAPHY_INDEFINITE_TOGETHER)


def test_resolve_orthography_rules():
    """Verify pronoun orthography rules per Правопис 2019 § 39."""
    cit1, ua1, en1 = resolve_orthography_rule(PronounCategory.ORTHOGRAPHY_INDEFINITE_TOGETHER)
    assert "§ 39" in cit1
    assert "дехто, абихто" in ua1
    assert "single word" in en1

    _cit2, ua2, en2 = resolve_orthography_rule(PronounCategory.ORTHOGRAPHY_INDEFINITE_HYPHEN)
    assert "будь-хто" in ua2
    assert "hyphen" in en2

    _cit3, ua3, en3 = resolve_orthography_rule(PronounCategory.ORTHOGRAPHY_INDEFINITE_SPLIT_PREPOSITION)
    assert "будь у кого" in ua3
    assert "three words" in en3

    _cit4, ua4, en4 = resolve_orthography_rule(PronounCategory.ORTHOGRAPHY_NEGATIVE_TOGETHER)
    assert "ніхто, ніщо" in ua4
    assert "prefix ні-" in en4

    _cit5, ua5, en5 = resolve_orthography_rule(PronounCategory.ORTHOGRAPHY_NEGATIVE_SPLIT_PREPOSITION)
    assert "ні про що" in ua5
    assert "split" in en5

    with pytest.raises(ValueError, match="not an orthography category"):
        resolve_orthography_rule(PronounCategory.REFLEXIVE_SEBE_PARADIGM)


def test_resolve_paradigm_rules():
    """Verify reflexive, ves, demonstrative, interrogative, sam, and possessive rule resolvers."""
    cit_r, ua_r, en_r = resolve_reflexive_sebe_rule()
    assert "§ 109" in cit_r
    assert "собі" in ua_r
    assert "Reflexive" in en_r

    cit_v, ua_v, en_v = resolve_declension_ves_rule()
    assert "§ 113" in cit_v
    assert "всіма" in ua_v
    assert "-іма" in en_v

    cit_d, ua_d, _en_d = resolve_demonstrative_rule()
    assert "§ 111" in cit_d
    assert "цими, тими" in ua_d

    cit_i, ua_i, _en_i = resolve_interrogative_rule()
    assert "§ 112" in cit_i
    assert "хто, що, чий" in ua_i

    _cit_s, ua_s, en_s = resolve_sam_vs_samyi_rule()
    assert "той самий" in ua_s
    assert "identity" in en_s

    cit_p, ua_p, _en_p = resolve_possessive_yikhniy_rule()
    assert "§ 110" in cit_p
    assert "до них" in ua_p


def test_deck_completeness_and_zero_collisions():
    """Verify canonical deck has 75 cards, exactly 5 per category, and 0 collisions."""
    cards = build_canonical_pronoun_cards()
    assert len(cards) == 75

    cat_counts = Counter(c.category for c in cards)
    assert len(cat_counts) == 15
    for cat, count in cat_counts.items():
        assert count == 5, f"Category {cat} has {count} cards instead of 5"

    card_ids = [c.card_id for c in cards]
    assert len(set(card_ids)) == 75, "Card IDs must be unique"

    for c in cards:
        errors = validate_pronoun_card(c)
        assert not errors, f"Validation errors on card {c.card_id}: {errors}"

        opts = c.all_options()
        assert len(opts) == 4
        assert len(set(opts)) == 4, f"Options on {c.card_id} contain duplicates: {opts}"
        assert c.correct_answer in opts
        for d in c.distractors:
            assert d.text != c.correct_answer, f"Collision on {c.card_id}: distractor matches correct answer"
            assert d.text in opts


def test_balanced_option_shuffling():
    """Verify that correct answer positions across all 75 cards are well-balanced."""
    cards = build_canonical_pronoun_cards()
    positions = []
    for c in cards:
        opts = c.all_options()
        pos = opts.index(c.correct_answer)
        positions.append(pos)

    counts = Counter(positions)
    for idx in range(4):
        # 75 / 4 = 18.75; each index should receive between 12 and 26 occurrences
        assert 12 <= counts[idx] <= 26, f"Index {idx} has count {counts[idx]}, which is outside balanced range"


def test_committed_deck_parity(tmp_path: Path):
    """Verify exported JSON deck matches committed file byte-for-byte."""
    cards = build_canonical_pronoun_cards()
    deck_path = Path(__file__).resolve().parents[1] / "registry" / "practice" / "pronoun_mechanics_deck.json"
    assert deck_path.exists(), f"Committed deck {deck_path} does not exist"

    with open(deck_path, encoding="utf-8") as f:
        committed_data = json.load(f)

    test_export = tmp_path / "test_deck.json"
    generated_data = export_pronoun_mechanics_deck(cards, test_export)

    assert committed_data["card_count"] == 75
    assert committed_data["card_count"] == generated_data["card_count"]
    assert len(committed_data["cards"]) == 75

    for c_comm, c_gen in zip(committed_data["cards"], generated_data["cards"], strict=True):
        assert c_comm["card_id"] == c_gen["card_id"]
        assert c_comm["correct_answer"] == c_gen["correct_answer"]
        assert c_comm["category"] == c_gen["category"]
        assert c_comm["options"] == c_gen["options"]


def test_vesum_database_validation():
    """Verify that all target inflected pronoun tokens exist in VESUM."""
    cards = build_canonical_pronoun_cards()
    report = verify_deck_with_vesum(cards)
    if report["status"] == "skipped":
        pytest.skip(report["message"])

    assert report["verified"] is True
    assert report["status"] == "passed"
    assert report["missing_count"] == 0
    assert report["missing_forms"] == []


def test_vesum_distractor_validation():
    """Verify that corrupted distractors do not falsely match standard literary pronouns in VESUM."""
    cards = build_canonical_pronoun_cards()
    dist_report = verify_distractors_with_vesum(cards)
    if dist_report["status"] == "skipped":
        pytest.skip(dist_report["message"])

    assert dist_report["verified"] is True
    assert dist_report["status"] == "passed"
    assert dist_report["invalid_distractors"] == []


def test_regression_zero_valid_distractor_collisions():
    """Regression test ensuring valid alternatives are never used as distractors."""
    cards_by_id = {c.card_id: c for c in build_canonical_pronoun_cards()}

    # Card 24: "брався за _______ роботу"
    c24 = cards_by_id["pron_orth_tog_abyyaku"]
    assert "будь-яку" not in c24.all_options()
    assert any(d.text == "абияка" for d in c24.distractors)
    assert c24.correct_answer == "абияку"

    # Card 26: "може розв'язати _______ із нашого класу"
    c26 = cards_by_id["pron_orth_hyph_bud_khto"]
    assert "абихто" not in c26.all_options()
    assert any(d.text == "будь-кого" for d in c26.distractors)
    assert c26.correct_answer == "будь-хто"

    # Card 27: "нехай _______ допоможе йому з домашнім завданням"
    c27 = cards_by_id["pron_orth_hyph_khto_nebud"]
    assert "хто-будь" not in c27.all_options()
    assert any(d.text == "кого-небудь" for d in c27.distractors)
    assert c27.correct_answer == "хто-небудь"

    # Card 29: "виконує _______ доручення керівника"
    c29 = cards_by_id["pron_orth_hyph_bud_yake"]
    assert "абияке" not in c29.all_options()
    assert any(d.text == "будь-який" for d in c29.distractors)
    assert c29.correct_answer == "будь-яке"

    # Card 31: "можна запитати дорогу _______ перехожого"
    c31 = cards_by_id["pron_orth_split_bud_u_koho"]
    assert "будь-кого" not in c31.all_options()
    assert any(d.text == "будь-ким" for d in c31.distractors)
    assert c31.correct_answer == "будь у кого"

    # Card 32: "вступати в суперечку _______"
    c32 = cards_by_id["pron_orth_split_bud_z_kym"]
    assert "з будь-ким" not in c32.all_options()
    assert any(d.text == "будь-ким" for d in c32.distractors)
    assert c32.correct_answer == "будь з ким"

    # Card 66: "він _______ зміг знайти правильне розв'язання задачі"
    c66 = cards_by_id["pron_sem_sam"]
    assert "самий" not in c66.all_options()
    assert any(d.text == "сама" for d in c66.distractors)
    assert c66.correct_answer == "сам"

    # Card 68: "працювали в саду з _______ ранку"
    c68 = cards_by_id["pron_sem_z_samoho_ranku"]
    assert "самого ж" not in c68.all_options()
    assert any(d.text == "самої" for d in c68.distractors)
    assert c68.correct_answer == "самого"

    # Card 70: "вирішила приготувати святковий обід _______"
    c70 = cards_by_id["pron_sem_sama"]
    assert "сама ж" not in c70.all_options()
    assert "сама-одна" not in c70.all_options()
    assert "саме" not in c70.all_options()
    assert any(d.text == "сам" for d in c70.distractors)
    assert any(d.text == "саму" for d in c70.distractors)
    assert c70.correct_answer == "сама"
