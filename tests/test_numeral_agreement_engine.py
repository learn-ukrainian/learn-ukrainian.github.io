"""Unit and integration tests for Ukrainian Numeral + Noun Agreement Engine.

Tests:
  1. Tier classification (Ends in 1 vs 2–4 vs 5+ vs teens 11–14 vs fractions vs collectives).
  2. Numeral word formatting and gender inflection (один/одна/одне, два/дві, півтора/півтори).
  3. Distractor taxonomy and pedagogical error models (Russianism calque, teen violation, compound agreement).
  4. Collective numeral restrictions (masculine animate and neuter only).
  5. Zero-collision guarantee across >= 1,000 noun items with VESUM grounding.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.practice.numeral_agreement_engine import (
    InterferenceType,
    NounParadigm,
    NumeralTier,
    classify_numeral_tier,
    format_numeral_words,
    generate_card_for_tier,
    generate_deck_across_all_tiers,
    load_noun_paradigms_from_db,
    validate_numeral_card,
)


def test_classify_numeral_tier():
    """Verify classification of numeral values into distinct agreement tiers."""
    # Tier 1: ends in 1, except 11
    assert classify_numeral_tier(1) == NumeralTier.TIER_1_SINGULAR
    assert classify_numeral_tier(21) == NumeralTier.TIER_1_SINGULAR
    assert classify_numeral_tier(31) == NumeralTier.TIER_1_SINGULAR
    assert classify_numeral_tier(101) == NumeralTier.TIER_1_SINGULAR
    assert classify_numeral_tier("51") == NumeralTier.TIER_1_SINGULAR

    # Tier 2: ends in 2, 3, 4, except 12–14
    assert classify_numeral_tier(2) == NumeralTier.TIER_2_PAUCAL
    assert classify_numeral_tier(3) == NumeralTier.TIER_2_PAUCAL
    assert classify_numeral_tier(4) == NumeralTier.TIER_2_PAUCAL
    assert classify_numeral_tier(22) == NumeralTier.TIER_2_PAUCAL
    assert classify_numeral_tier(33) == NumeralTier.TIER_2_PAUCAL
    assert classify_numeral_tier(44) == NumeralTier.TIER_2_PAUCAL
    assert classify_numeral_tier(102) == NumeralTier.TIER_2_PAUCAL
    assert classify_numeral_tier("24") == NumeralTier.TIER_2_PAUCAL

    # Tier 3: 5–20, 30, teens 11–14
    assert classify_numeral_tier(5) == NumeralTier.TIER_3_PLURAL
    assert classify_numeral_tier(10) == NumeralTier.TIER_3_PLURAL
    assert classify_numeral_tier(11) == NumeralTier.TIER_3_PLURAL
    assert classify_numeral_tier(12) == NumeralTier.TIER_3_PLURAL
    assert classify_numeral_tier(13) == NumeralTier.TIER_3_PLURAL
    assert classify_numeral_tier(14) == NumeralTier.TIER_3_PLURAL
    assert classify_numeral_tier(20) == NumeralTier.TIER_3_PLURAL
    assert classify_numeral_tier(112) == NumeralTier.TIER_3_PLURAL
    assert classify_numeral_tier(114) == NumeralTier.TIER_3_PLURAL

    # Tier 4: Fractional and decimals
    assert classify_numeral_tier("півтора") == NumeralTier.TIER_4_FRACTIONAL
    assert classify_numeral_tier("півтори") == NumeralTier.TIER_4_FRACTIONAL
    assert classify_numeral_tier(2.5) == NumeralTier.TIER_4_FRACTIONAL
    assert classify_numeral_tier(0.5) == NumeralTier.TIER_4_FRACTIONAL
    assert classify_numeral_tier("1.5") == NumeralTier.TIER_4_FRACTIONAL

    # Tier 5: Collectives
    assert classify_numeral_tier("двоє") == NumeralTier.TIER_5_COLLECTIVE
    assert classify_numeral_tier("троє") == NumeralTier.TIER_5_COLLECTIVE
    assert classify_numeral_tier("четверо") == NumeralTier.TIER_5_COLLECTIVE
    assert classify_numeral_tier("п'ятеро") == NumeralTier.TIER_5_COLLECTIVE


def test_format_numeral_words_gender():
    """Verify numeral word formatting agrees in gender with nouns."""
    # 1: один / одна / одне
    _, w_m = format_numeral_words(1, "m")
    assert w_m == "один"
    _, w_f = format_numeral_words(1, "f")
    assert w_f == "одна"
    _, w_n = format_numeral_words(1, "n")
    assert w_n == "одне"

    # 2: два / дві / два
    _, w2_m = format_numeral_words(2, "m")
    assert w2_m == "два"
    _, w2_f = format_numeral_words(2, "f")
    assert w2_f == "дві"
    _, w2_n = format_numeral_words(2, "n")
    assert w2_n == "два"

    # 21: двадцять один / двадцять одна / двадцять одне
    _, w21_m = format_numeral_words(21, "m")
    assert w21_m == "двадцять один"
    _, w21_f = format_numeral_words(21, "f")
    assert w21_f == "двадцять одна"
    _, w21_n = format_numeral_words(21, "n")
    assert w21_n == "двадцять одне"

    # 22: двадцять два / двадцять дві
    _, w22_m = format_numeral_words(22, "m")
    assert w22_m == "двадцять два"
    _, w22_f = format_numeral_words(22, "f")
    assert w22_f == "двадцять дві"

    # Fractions: півтора / півтори
    _, w_f1 = format_numeral_words("півтора", "f")
    assert w_f1 == "півтори"
    _, w_f2 = format_numeral_words("півтора", "m")
    assert w_f2 == "півтора"


def test_tier_2_russianism_calque_distractor():
    """Verify Tier 2 (2-4) identifies Russianism calque (Gen Sg) with explicit feedback."""
    noun = NounParadigm(
        lemma="журнал",
        gender="m",
        is_anim=False,
        cefr_level="A2",
        nom_sg="журнал",
        gen_sg="журналу",
        nom_pl="журнали",
        gen_pl="журналів",
    )
    card = generate_card_for_tier(noun, NumeralTier.TIER_2_PAUCAL, seed_idx=1)
    assert card is not None
    assert card.correct_form == "журнали"
    assert card.target_case == "називний"
    assert card.target_number == "plural"

    # Find Russianism distractor
    calque_d = next(
        (d for d in card.distractors if d["interference_type"] == InterferenceType.RUSSIANISM_CALQUE.value),
        None,
    )
    assert calque_d is not None
    assert calque_d["form"] == "журналу"
    assert "російській мові" in calque_d["explanation_ua"]
    assert "Russianism" in calque_d["explanation_en"]


def test_paucal_dropping_yn_exception():
    """Verify masculine nouns in -ин that drop suffix in plural take Gen Sg after 2, 3, 4."""
    noun = NounParadigm(
        lemma="громадянин",
        gender="m",
        is_anim=True,
        cefr_level="B1",
        nom_sg="громадянин",
        gen_sg="громадянина",
        nom_pl="громадяни",
        gen_pl="громадян",
        dat_pl="громадянам",
        loc_pl="громадянах",
        oru_sg="громадянином",
    )
    # Under paucal tier (2, 3, 4): correct form must be Genitive singular (два громадянина)
    card = generate_card_for_tier(noun, NumeralTier.TIER_2_PAUCAL, seed_idx=0)
    assert card is not None
    assert card.correct_form == "громадянина"
    assert card.target_case == "родовий"
    assert card.target_number == "singular"
    assert "два громадянина" in card.pedagogical_rule_ua or "родового відмінка однини" in card.pedagogical_rule_ua
    assert card.pravopys_ref == "Морфологія української мови (Волкова, Масло 2012, с. 91)"

    # Overgeneralized plural distractor (*громадяни) must NOT be labeled as Russianism calque
    nom_pl_distractor = next(d for d in card.distractors if d["form"] == "громадяни")
    assert nom_pl_distractor["interference_type"] == InterferenceType.OVERGENERALIZED_PLURAL.value
    assert "називним відмінком множини" in nom_pl_distractor["explanation_ua"]

    # Verify no distractor is labeled as Russianism calque
    assert not any(d["interference_type"] == InterferenceType.RUSSIANISM_CALQUE.value for d in card.distractors)

    # Test serialization contract
    card_dict = card.to_dict()
    assert card_dict["correctForm"] == "громадянина"
    assert card_dict["numeralDisplay"] == card.numeral_display
    assert card_dict["targetCase"] == "родовий"
    assert len(card_dict["distractors"]) == 3
    assert "explanationUa" in card_dict["distractors"][0]
    assert "interferenceType" in card_dict["distractors"][0]


def test_teen_tier_violation_distractor():
    """Verify teen numerals (11-14) test teen-tier violation (treating as paucal 1-4)."""
    noun = NounParadigm(
        lemma="студент",
        gender="m",
        is_anim=True,
        cefr_level="A1",
        nom_sg="студент",
        gen_sg="студента",
        nom_pl="студенти",
        gen_pl="студентів",
    )
    # Search across seeds for a teen numeral card
    teen_card = None
    for s in range(20):
        c = generate_card_for_tier(noun, NumeralTier.TIER_3_PLURAL, seed_idx=s)
        if c and int(c.numeral_display) in {11, 12, 13, 14}:
            teen_card = c
            break

    assert teen_card is not None
    assert teen_card.correct_form == "студентів"
    assert teen_card.target_case == "родовий"
    assert teen_card.target_number == "plural"

    teen_distractor = next(
        (d for d in teen_card.distractors if d["interference_type"] == InterferenceType.TEEN_TIER_VIOLATION.value),
        None,
    )
    assert teen_distractor is not None
    assert teen_distractor["form"] == "студенти"
    assert "-надцять" in teen_distractor["explanation_ua"]
    assert "Teens 11–14" in teen_distractor["explanation_en"]


def test_collective_numeral_restrictions():
    """Verify collective numerals apply strictly to masculine animates and neuters."""
    # Inanimate masculine: cannot combine with collective numeral in standard literary UA
    inanim_masc = NounParadigm(
        lemma="стіл",
        gender="m",
        is_anim=False,
        cefr_level="A1",
        nom_sg="стіл",
        gen_sg="стола",
        nom_pl="столи",
        gen_pl="столів",
    )
    assert generate_card_for_tier(inanim_masc, NumeralTier.TIER_5_COLLECTIVE) is None

    # Feminine: cannot combine with collective numeral
    fem_noun = NounParadigm(
        lemma="сестра",
        gender="f",
        is_anim=True,
        cefr_level="A1",
        nom_sg="сестра",
        gen_sg="сестри",
        nom_pl="сестри",
        gen_pl="сестер",
    )
    assert generate_card_for_tier(fem_noun, NumeralTier.TIER_5_COLLECTIVE) is None

    # Animate masculine: valid
    anim_masc = NounParadigm(
        lemma="хлопець",
        gender="m",
        is_anim=True,
        cefr_level="A1",
        nom_sg="хлопець",
        gen_sg="хлопця",
        nom_pl="хлопці",
        gen_pl="хлопців",
    )
    card_m = generate_card_for_tier(anim_masc, NumeralTier.TIER_5_COLLECTIVE)
    assert card_m is not None
    assert card_m.correct_form == "хлопців"
    assert card_m.tier == NumeralTier.TIER_5_COLLECTIVE

    # Neuter: valid (двоє вікон, четверо каченят)
    neuter_noun = NounParadigm(
        lemma="вікно",
        gender="n",
        is_anim=False,
        cefr_level="A1",
        nom_sg="вікно",
        gen_sg="вікна",
        nom_pl="вікна",
        gen_pl="вікон",
        dat_pl="вікнам",
        loc_pl="вікнах",
        oru_sg="вікном",
    )
    card_n = generate_card_for_tier(neuter_noun, NumeralTier.TIER_5_COLLECTIVE)
    assert card_n is not None
    assert card_n.correct_form == "вікон"


def test_fractional_numeral_governance():
    """Verify fractional numerals govern Genitive singular."""
    masc_noun = NounParadigm(
        lemma="рік",
        gender="m",
        is_anim=False,
        cefr_level="A1",
        nom_sg="рік",
        gen_sg="року",
        nom_pl="роки",
        gen_pl="років",
        dat_pl="рокам",
        loc_pl="роках",
        oru_sg="роком",
    )
    card_m = generate_card_for_tier(masc_noun, NumeralTier.TIER_4_FRACTIONAL, seed_idx=0)
    assert card_m is not None
    assert card_m.correct_form == "року"
    assert card_m.target_case == "родовий"
    assert card_m.target_number == "singular"

    fem_noun = NounParadigm(
        lemma="доба",
        gender="f",
        is_anim=False,
        cefr_level="B1",
        nom_sg="доба",
        gen_sg="доби",
        nom_pl="доби",
        gen_pl="діб",
        dat_pl="добам",
        loc_pl="добах",
        oru_sg="добою",
    )
    card_f = generate_card_for_tier(fem_noun, NumeralTier.TIER_4_FRACTIONAL, seed_idx=0)
    assert card_f is not None
    assert card_f.correct_form == "доби"
    assert card_f.target_case == "родовий"
    assert card_f.target_number == "singular"


def test_zero_collision_guarantee_fixture_paradigms():
    """Verify zero-collision guarantee across synthetic paradigms without DB dependency."""
    sample_paradigms = [
        NounParadigm(
            lemma="стіл",
            gender="m",
            is_anim=False,
            cefr_level="A1",
            nom_sg="стіл",
            gen_sg="стола",
            nom_pl="столи",
            gen_pl="столів",
            dat_pl="столам",
            loc_pl="столах",
            oru_sg="столом",
        ),
        NounParadigm(
            lemma="студент",
            gender="m",
            is_anim=True,
            cefr_level="A1",
            nom_sg="студент",
            gen_sg="студента",
            nom_pl="студенти",
            gen_pl="студентів",
            dat_pl="студентам",
            loc_pl="студентах",
            oru_sg="студентом",
        ),
        NounParadigm(
            lemma="сестра",
            gender="f",
            is_anim=True,
            cefr_level="A1",
            nom_sg="сестра",
            gen_sg="сестри",
            nom_pl="сестри",
            gen_pl="сестер",
            dat_pl="сестрам",
            loc_pl="сестрах",
            oru_sg="сестрою",
        ),
        NounParadigm(
            lemma="книжка",
            gender="f",
            is_anim=False,
            cefr_level="A1",
            nom_sg="книжка",
            gen_sg="книжки",
            nom_pl="книжки",
            gen_pl="книжок",
            dat_pl="книжкам",
            loc_pl="книжках",
            oru_sg="книжкою",
        ),
        NounParadigm(
            lemma="вікно",
            gender="n",
            is_anim=False,
            cefr_level="A1",
            nom_sg="вікно",
            gen_sg="вікна",
            nom_pl="вікна",
            gen_pl="вікон",
            dat_pl="вікнам",
            loc_pl="вікнах",
            oru_sg="вікном",
        ),
    ]

    cards = generate_deck_across_all_tiers(sample_paradigms * 10, target_count=50)
    assert len(cards) == 50
    for card in cards:
        errs = validate_numeral_card(card)
        assert not errs, f"Validation errors in {card.id}: {errs}"
        assert len(card.options) == 4
        assert len(set(card.options)) == 4, f"Duplicate options in {card.id}: {card.options}"
        assert card.correct_form in card.options
        for d in card.distractors:
            assert d["form"] != card.correct_form
            assert len(d["explanation_ua"].strip()) > 10
            assert len(d["explanation_en"].strip()) > 10


@pytest.mark.skipif(
    not Path("data/vesum.db").exists() or Path("data/vesum.db").stat().st_size < 1_000_000,
    reason="Requires full local data/vesum.db (>1MB); CI omits it",
)
def test_zero_collision_guarantee_large_scale():
    """Verify zero-collision guarantee across >= 1,000 generated cards."""
    paradigms = load_noun_paradigms_from_db(limit=1600)
    assert len(paradigms) >= 1000, f"Expected at least 1,000 paradigms, got {len(paradigms)}"

    cards = generate_deck_across_all_tiers(paradigms, target_count=1050)
    assert len(cards) >= 1000, f"Expected at least 1,000 cards, got {len(cards)}"

    for card in cards:
        errs = validate_numeral_card(card)
        assert not errs, f"Validation errors in {card.id}: {errs}"
        assert len(card.options) == 4
        assert len(set(card.options)) == 4, f"Duplicate options in {card.id}: {card.options}"
        assert card.correct_form in card.options
        for d in card.distractors:
            assert d["form"] != card.correct_form
            assert len(d["explanation_ua"].strip()) > 10
            assert len(d["explanation_en"].strip()) > 10
