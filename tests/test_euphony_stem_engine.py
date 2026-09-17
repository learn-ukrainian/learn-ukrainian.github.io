"""Unit and integration tests for Ukrainian Euphony and Stem Alternations Engine.

Tests:
  1. Preposition euphony: У vs В, З vs ІЗ vs ЗІ.
  2. Conjunction euphony: І vs Й.
  3. Historical vowel alternations [о], [е] <-> [і] in open vs closed syllables.
  4. Second palatalization (г, к, х -> з', ц', с' in Dative/Locative).
  5. First palatalization in Vocative (г, к, х -> ж, ч, ш).
  6. Verb iotation (epenthetic л and dental shifts in 1st person singular).
  7. Large-scale zero-collision guarantee across all categories.
"""

from __future__ import annotations

from scripts.practice.euphony_stem_engine import (
    EuphonyCategory,
    EuphonyInterferenceType,
    generate_comprehensive_euphony_deck,
    generate_first_palatalization_vocative_card,
    generate_second_palatalization_card,
    generate_verb_iotation_card,
    generate_vowel_shift_card,
    resolve_i_y_rule,
    resolve_u_v_rule,
    resolve_z_iz_zi_rule,
    validate_euphony_card,
)


def test_resolve_u_v_euphony():
    """Verify у vs в alternation rules."""
    # Between consonants -> у
    u1, _, _ = resolve_u_v_rule("день", "школі")
    assert u1 == "у"
    u2, _, _ = resolve_u_v_rule("він", "лісі")
    assert u2 == "у"

    # Between vowels -> в
    v1, _, _ = resolve_u_v_rule("була", "Одесі")
    assert v1 == "в"
    v2, _, _ = resolve_u_v_rule("жила", "Умані")
    assert v2 == "в"

    # Before в, ф, or clusters with в/ф (regardless of preceding letter) -> у
    u_fr, _, _ = resolve_u_v_rule("була", "Франції")
    assert u_fr == "у"
    u_lv, _, _ = resolve_u_v_rule("поїхала", "Львові")
    assert u_lv == "у"
    u_vod, _, _ = resolve_u_v_rule("пірнув", "воду")
    assert u_vod == "у"

    # Start of sentence before consonant -> у, before vowel -> в
    u_start, _, _ = resolve_u_v_rule(None, "Києві")
    assert u_start == "у"
    v_start, _, _ = resolve_u_v_rule(None, "очах")
    assert v_start == "в"


def test_resolve_i_y_euphony():
    """Verify і vs й alternation rules."""
    # Between consonants -> і
    i1, _, _ = resolve_i_y_rule("брат", "сестра")
    assert i1 == "і"

    # Between vowels -> й
    y1, _, _ = resolve_i_y_rule("мама", "Ольга")
    assert y1 == "й"

    # After vowel before consonant -> й
    y2, _, _ = resolve_i_y_rule("весна", "літо")
    assert y2 == "й"

    # After consonant before vowel -> і
    i2, _, _ = resolve_i_y_rule("дуб", "ясен")
    assert i2 == "і"

    # Start of sentence -> і
    i_start, _, _ = resolve_i_y_rule(None, "день")
    assert i_start == "і"


def test_resolve_z_iz_zi_euphony():
    """Verify з vs із vs зі alternation rules."""
    # Before pronoun «мною» -> зі
    zi_mnoiu, _, _ = resolve_z_iz_zi_rule(None, "мною")
    assert zi_mnoiu == "зі"

    # Before sibilant clusters (сну, школи, страху) -> зі
    zi_snu, _, _ = resolve_z_iz_zi_rule("прокинувся", "сну")
    assert zi_snu == "зі"
    zi_shkoly, _, _ = resolve_z_iz_zi_rule("вийшов", "школи")
    assert zi_shkoly == "зі"

    # Before vowel -> з
    z_vowel, _, _ = resolve_z_iz_zi_rule("зустрівся", "артистом")
    assert z_vowel == "з"

    # Before single non-sibilant consonant -> з
    z_cons, _, _ = resolve_z_iz_zi_rule("приїхали", "братом")
    assert z_cons == "з"


def test_vowel_shifts_closed_open():
    """Verify vowel shifts [о], [е] <-> [і] in open vs closed syllables."""
    item = {
        "lemma": "кіт",
        "closed_nom_sg": "кіт",
        "open_gen_sg": "кота",
        "open_nom_pl": "коти",
        "frame": "Ми взяли додому маленького (кіт) ➔ ___.",
        "target": "кота",
        "calque_wrong": "кіта",
        "russian_wrong": "кот",
        "vowel_pair": "і/о",
    }
    card = generate_vowel_shift_card(item, 0)
    assert card.correct_answer == "кота"
    assert card.category == EuphonyCategory.VOWEL_SHIFT_O_E_I
    assert len(card.options) == 4
    assert len(set(card.options)) == 4

    # Calque distractor (*кіта)
    calque_d = next(
        (d for d in card.distractors if d["interference_type"] == EuphonyInterferenceType.NON_ALTERNATING_STEM.value),
        None,
    )
    assert calque_d is not None
    assert calque_d["form"] == "кіта"
    assert "відкритому складі" in calque_d["explanation_ua"]

    # Russianism distractor (*кот)
    rus_d = next(
        (
            d
            for d in card.distractors
            if d["interference_type"] == EuphonyInterferenceType.RUSSIAN_CLOSED_SYLLABLE_CALQUE.value
        ),
        None,
    )
    assert rus_d is not None
    assert rus_d["form"] == "кот"


def test_second_palatalization():
    """Verify second palatalization in Dative/Locative (г, к, х -> з', ц', с')."""
    item = {
        "lemma": "рука",
        "consonant": "к",
        "target": "руці",
        "frame": "У мене в (рука) ➔ ___ був квиток.",
        "wrong_unaltered": "рукі",
        "wrong_first_palat": "ручі",
        "other_form": "руку",
    }
    card = generate_second_palatalization_card(item, 0)
    assert card.correct_answer == "руці"
    assert card.category == EuphonyCategory.SECOND_PALATALIZATION
    assert len(card.options) == 4
    assert len(set(card.options)) == 4

    # Unaltered Russianism distractor (*рукі)
    unaltered_d = next(
        (d for d in card.distractors if d["interference_type"] == EuphonyInterferenceType.NON_ALTERNATING_STEM.value),
        None,
    )
    assert unaltered_d is not None
    assert unaltered_d["form"] == "рукі"
    assert "калькою" in unaltered_d["explanation_ua"]


def test_first_palatalization_vocative():
    """Verify first palatalization in Vocative singular (г, к, х -> ж, ч, ш)."""
    item = {
        "lemma": "друг",
        "consonant": "г",
        "target": "друже",
        "frame": "Мій дорогий (друг) ➔ ___, як справи?",
        "wrong_unaltered": "друге",
        "wrong_second": "друзе",
        "other_form": "друга",
    }
    card = generate_first_palatalization_vocative_card(item, 0)
    assert card.correct_answer == "друже"
    assert card.category == EuphonyCategory.FIRST_PALATALIZATION_VOCATIVE
    assert len(card.options) == 4
    assert len(set(card.options)) == 4

    unaltered = next(
        (d for d in card.distractors if d["interference_type"] == EuphonyInterferenceType.NON_ALTERNATING_STEM.value),
        None,
    )
    assert unaltered is not None
    assert unaltered["form"] == "друге"


def test_verb_iotation():
    """Verify verb iotation (epenthetic л and dental shifts)."""
    # Labial: любити -> люблю (not любу)
    labial_item = {
        "infinitive": "любити",
        "stem_type": "labial",
        "target": "люблю",
        "frame": "Я дуже (любити) ➔ ___ пісні.",
        "wrong_missing_l": "любу",
        "wrong_person": "любиш",
        "wrong_plural": "люблять",
        "rule_ua": "Губні приголосні (б, п, в, м, ф) вимагають вставного [л]: любити ➔ люблю.",
        "rule_en": "Labial consonants require epenthetic [л]: любити ➔ люблю.",
    }
    card_l = generate_verb_iotation_card(labial_item, 0)
    assert card_l.correct_answer == "люблю"
    assert card_l.category == EuphonyCategory.VERB_IOTATION

    missing_l = next(
        (d for d in card_l.distractors if d["interference_type"] == EuphonyInterferenceType.MISSING_EPENTHETIC_L.value),
        None,
    )
    assert missing_l is not None
    assert missing_l["form"] == "любу"

    # Dental: ходити -> ходжу (not ходю)
    dental_item = {
        "infinitive": "ходити",
        "stem_type": "dental_d",
        "target": "ходжу",
        "frame": "Щовечора я (ходити) ➔ ___ пішки.",
        "wrong_missing_l": "ходю",
        "wrong_person": "ходиш",
        "wrong_plural": "ходять",
        "rule_ua": "Зубний [д] чергується з [дж]: ходити ➔ ходжу.",
        "rule_en": "Dental [д] alternates with [дж]: ходити ➔ ходжу.",
    }
    card_d = generate_verb_iotation_card(dental_item, 0)
    assert card_d.correct_answer == "ходжу"


def test_zero_collision_large_scale():
    """Verify zero-collision guarantee across >= 1,000 generated euphony/stem cards."""
    cards = generate_comprehensive_euphony_deck(target_count=1050)
    assert len(cards) >= 1000

    for card in cards:
        errs = validate_euphony_card(card)
        assert not errs, f"Validation errors in {card.id}: {errs}"
        assert len(card.options) == 4
        assert len(set(card.options)) == 4, f"Duplicate options in {card.id}: {card.options}"
        assert card.correct_answer in card.options
        for d in card.distractors:
            assert d["form"] != card.correct_answer
            assert len(d["explanation_ua"].strip()) > 5
            assert len(d["explanation_en"].strip()) > 5
