"""Unit and integration tests for Ukrainian Verb Deep Mechanics Practice Engine.

Tests:
  1. Conjugation class rules [Правопис 2019 § 115]:
     - Class I: -е-/-є- (-уть/-ють) (пишеш, чуєш, борються, мелють).
     - Class II: -и-/-ї- (-ать/-ять) (летиш, сидить, клеїш, стоять, біжать).
  2. Stem alternations [Правопис 2019 § 115]:
     - Epenthetic [л'] after labials (любити -> люблю, люблять; спати -> сплю, сплять).
     - Dental/alveolar alternations in 1sg: д->дж, т->ч, с->ш, з->ж, ст->щ, зд->ждж.
     - Class I present stem alternations: с->ш, к->ч, г->ж, vowel ablaut.
  3. Aspectual pairs & derivation [Правопис 2019 § 115]:
     - Prefixation (писати <-> написати, робити <-> зробити).
     - Suffixation & root vowel ablaut о <-> а (допомогти <-> допомагати, перемогти <-> перемагати).
     - Suppletive pairs (брати <-> взяти, говорити <-> сказати, ловити <-> піймати).
  4. Imperative mood [Правопис 2019 § 116]:
     - Synthetic endings: -и/-іть vs - / -те (роби, пишіть vs читай, стань, вірте).
     - Inclusive 1pl encouragement: -мо / -імо (ходімо, робімо, читаймо).
     - Eradication of Russian calques (*давай підемо -> ходімо).
  5. Verbals [Правопис 2019 §§ 119–120]:
     - Passive participles in -ний / -тий [§ 119] (написаний, зроблений, розбитий).
     - Active participle calque eradication [§ 119] (*бажаючий -> охочий, *діючий -> чинний).
     - Impersonal forms in -но / -то [§ 119] (виконано, прийнято, відкрито).
     - Gerund aspect markers [§ 120]: imperfective -учи/-ючи vs perfective -вши/-ши.
  6. Deck validation: zero collisions, valid option counts, prompt blank markers.
  7. Balanced deterministic shuffle distribution across indices 0..3.
  8. Committed deck file parity.
  9. VESUM database validation for all target inflected forms.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.practice.verb_mechanics_engine import (
    VerbCategory,
    build_canonical_verb_cards,
    export_verb_mechanics_deck,
    resolve_conjugation_class_rule,
    resolve_dental_mutation_rule,
    resolve_epenthesis_rule,
    resolve_gerund_aspect_rule,
    resolve_imperative_rule,
    resolve_impersonal_form_rule,
    resolve_participle_anti_calque_rule,
    validate_verb_card,
    verify_deck_with_vesum,
    verify_distractors_with_vesum,
)


def test_resolve_conjugation_class_rule():
    """Verify conjugation class rules per Правопис 2019 § 115."""
    ind_i, ua_i, en_i = resolve_conjugation_class_rule(VerbCategory.CONJ_CLASS_I_VOWEL_E_YE)
    assert "-е- / -є-" in ind_i
    assert "-уть/-ють" in ua_i
    assert "-ut/-yut" in en_i

    ind_ii, ua_ii, en_ii = resolve_conjugation_class_rule(VerbCategory.CONJ_CLASS_II_VOWEL_Y_YI)
    assert "-и- / -ї-" in ind_ii
    assert "-ать/-ять" in ua_ii
    assert "-at/-iat" in en_ii


def test_resolve_epenthesis_rule():
    """Verify epenthetic [л'] after labials per Правопис 2019 § 115."""
    ind, ua, en = resolve_epenthesis_rule()
    assert ind == "[л']"
    assert "після губних" in ua
    assert "Epenthetic" in en


def test_resolve_dental_mutation_rule():
    """Verify dental/alveolar consonant alternations per Правопис 2019 § 115."""
    cases = [
        ("d_dzh", "д -> дж", "ходжу"),
        ("t_ch", "т -> ч", "лечу"),
        ("s_sh", "с -> ш", "прошу"),
        ("z_zh", "з -> ж", "вожу"),
        ("st_shch", "ст -> щ", "мощу"),
        ("zd_zhdzh", "зд -> ждж", "їжджу"),
    ]
    for key, expected_mut, expected_example in cases:
        mut, ua, en = resolve_dental_mutation_rule(key)
        assert mut == expected_mut
        assert expected_example in ua
        assert "alternates" in en

    for invalid_key in ("unknown_key", "constructor", "toString", "__proto__"):
        with pytest.raises(ValueError, match="Unknown dental mutation key"):
            resolve_dental_mutation_rule(invalid_key)


def test_resolve_imperative_rule():
    """Verify imperative mood rules per Правопис 2019 § 116."""
    ind_str, ua_str, en_str = resolve_imperative_rule("stressed_or_cluster")
    assert ind_str == "-и / -іть"
    assert "Під наголосом" in ua_str
    assert "-y" in en_str

    ind_vow, ua_vow, en_vow = resolve_imperative_rule("vowel_or_soft")
    assert "нульове" in ind_vow
    assert "читай" in ua_vow
    assert "zero ending" in en_vow

    ind_inc, ua_inc, en_inc = resolve_imperative_rule("inclusive_1pl")
    assert "-мо / -імо" in ind_inc
    assert "заклик до спільної дії" in ua_inc
    assert "-mo" in en_inc


def test_resolve_verbal_rules():
    """Verify participle and gerund rules per Правопис 2019 §§ 119–120."""
    # Participle anti-calque
    ind_part, ua_part, _ = resolve_participle_anti_calque_rule()
    assert "активних" in ind_part
    assert "охочий, чинний" in ua_part

    # Impersonal predicate
    ind_imp, ua_imp, _ = resolve_impersonal_form_rule()
    assert ind_imp == "-но / -то"
    assert "безособових" in ua_imp

    # Gerund imperfective
    ind_g_imp, ua_g_imp, _ = resolve_gerund_aspect_rule("imperfective")
    assert "-учи/-ючи" in ind_g_imp
    assert "одночасної дії" in ua_g_imp

    # Gerund perfective
    ind_g_perf, ua_g_perf, _ = resolve_gerund_aspect_rule("perfective")
    assert "-вши / -ши" in ind_g_perf
    assert "передуючої" in ua_g_perf


def test_canonical_cards_integrity():
    """Verify canonical cards meet all strict pedagogical and structural constraints."""
    cards = build_canonical_verb_cards()
    assert len(cards) >= 75

    categories_seen = {c.category for c in cards}
    assert len(categories_seen) == 15, "Must cover all 15 verb categories"

    card_ids = [c.card_id for c in cards]
    assert len(card_ids) == len(set(card_ids)), "Card IDs must be strictly unique"

    for card in cards:
        # Check validation function does not raise
        validate_verb_card(card)

        # Prompt blank check
        assert "___" in card.prompt_sentence

        # Option count and collision check
        assert len(card.distractors) == 3
        opts = card.all_options()
        assert len(opts) == 4
        assert len(set(opts)) == 4, f"Collision in card {card.card_id}: {opts}"
        assert card.correct_answer in opts

        # CEFR level validity
        assert card.cefr_level in {"A1", "A2", "B1", "B2"}

        # Rule summary and Pravopys citations
        assert "Правопис 2019" in card.pravopys_section
        assert len(card.rule_summary["ua"]) > 10
        assert len(card.rule_summary["en"]) > 10

        for dist in card.distractors:
            assert dist.text != card.correct_answer
            assert len(dist.explanation["ua"]) > 10
            assert len(dist.explanation["en"]) > 10


def test_shuffle_distribution_balance():
    """Verify deterministic shuffle produces a balanced distribution of correct answers across 0..3."""
    cards = build_canonical_verb_cards()
    correct_indices: list[int] = []

    for card in cards:
        opts = card.all_options()
        idx = opts.index(card.correct_answer)
        correct_indices.append(idx)

    counts = Counter(correct_indices)
    assert len(counts) == 4, "All 4 option slots (0, 1, 2, 3) must be used"

    # With 75 cards, average is ~18.75 per slot; ensure each slot has at least 10 cards
    for slot in range(4):
        assert counts[slot] >= 10, f"Slot {slot} has insufficient distribution: {counts[slot]}"


def test_export_and_committed_deck_parity(tmp_path: Path):
    """Verify exported JSON deck matches committed deck file."""
    cards = build_canonical_verb_cards()
    out_file = tmp_path / "verb_mechanics_deck.json"
    data = export_verb_mechanics_deck(cards, out_file)

    assert data["card_count"] == len(cards)
    assert len(data["cards"]) == len(cards)

    repo_deck_path = Path("data/practice/verb_mechanics_deck.json")
    assert repo_deck_path.exists(), "Committed deck file data/practice/verb_mechanics_deck.json must exist"

    with open(repo_deck_path, encoding="utf-8") as f:
        committed_data = json.load(f)

    assert data == committed_data, "Committed deck differs from fresh generator export"


@pytest.mark.skipif(
    not Path("data/vesum.db").exists() or Path("data/vesum.db").stat().st_size < 1_000_000,
    reason="Requires full local data/vesum.db (>1MB); CI omits it",
)
def test_vesum_verification():
    """Verify that VESUM database confirms all target words and validates corruption distractors."""
    cards = build_canonical_verb_cards()
    report = verify_deck_with_vesum(cards)
    assert report["verified"] is True, f"VESUM verification failed: {report.get('missing_forms', [])}"
    assert report["checked_word_count"] >= 70

    dist_report = verify_distractors_with_vesum(cards)
    assert dist_report["verified"] is True, (
        f"Corruption distractors matched valid standard words in VESUM: {dist_report.get('invalid_distractors', [])}"
    )
    assert dist_report["checked_distractor_count"] >= 100


def test_non_ablaut_distractors_feedback():
    """Verify that non-ablaut distractors (e.g. прочитавав, збудовували, переписавав, відкривують)
    do not receive the generic root vowel ablaut explanation."""
    cards = {c.card_id: c for c in build_canonical_verb_cards()}

    chytaty_card = cards["verb_aspect_pref_chytaty_perf"]
    prochytavav = next(d for d in chytaty_card.distractors if d.text == "прочитавав")
    assert "ablaut" not in prochytavav.explanation["en"].lower()
    assert "чергуван" not in prochytavav.explanation["ua"].lower()
    assert "нарощенням суфікса" in prochytavav.explanation["ua"]

    buduvaty_card = cards["verb_aspect_pref_buduvaty_perf"]
    zbudovuvaly = next(d for d in buduvaty_card.distractors if d.text == "збудовували")
    assert "ablaut" not in zbudovuvaly.explanation["en"].lower()
    assert "чергуван" not in zbudovuvaly.explanation["ua"].lower()
    assert "недоконаного виду" in zbudovuvaly.explanation["ua"]

    pysaty_card = cards["verb_aspect_suff_pysaty_impersuff"]
    perepysavav = next(d for d in pysaty_card.distractors if d.text == "переписавав")
    assert "ablaut" not in perepysavav.explanation["en"].lower()
    assert "-ава-" in perepysavav.explanation["ua"]

    vidkryvaty_card = cards["verb_aspect_suff_vidkryvaty"]
    vidkryvuiut = next(d for d in vidkryvaty_card.distractors if d.text == "відкривують")
    assert "ablaut" not in vidkryvuiut.explanation["en"].lower()
    assert "-ува-" in vidkryvuiut.explanation["ua"]


def test_gerund_distractors_feedback():
    """Verify that gerund distractors (e.g. прочитано, принесши) do not receive unrelated generic feedback."""
    cards = {c.card_id: c for c in build_canonical_verb_cards()}

    prochytavshy_card = cards["verb_gerund_prochytavshy"]
    prochytano = next(d for d in prochytavshy_card.distractors if d.text == "прочитано")
    assert "безособова предикативна форма" in prochytano.explanation["ua"]
    assert "impersonal predicative form" in prochytano.explanation["en"].lower()
    assert "дієприслівник" in prochytano.explanation["ua"]
    assert "impersonal predicates in ukrainian" not in prochytano.explanation["en"].lower()

    prynisshy_card = cards["verb_gerund_prynisshy"]
    prynesshy = next(d for d in prynisshy_card.distractors if d.text == "принесши")
    assert "дієприслівник" in prynesshy.explanation["ua"].lower()
    assert "теперішнього часу" not in prynesshy.explanation["ua"]
    assert "present-tense" not in prynesshy.explanation["en"].lower()
    assert "prynisshy" in prynesshy.explanation["en"]
