"""Unit and integration tests for Ukrainian Noun Deep Mechanics Practice Engine.

Tests:
  1. II Declension Genitive singular endings (-а/-я vs -у/-ю) [Правопис 2019 § 82]:
     - Beings, persons, concrete objects, settlements, measures -> -а/-я.
     - Substances, materials, collective nouns, abstract processes, territories -> -у/-ю.
     - Semantic homonym pairs (каменя/каменю, листопада/листопаду, апарата/апарату, терміна/терміну).
  2. Vocative case endings (-е, -у, -ю, -о) [Правопис 2019 §§ 73, 87]:
     - Hard stems with consonant mutation (г->ж, к->ч, х->ш) -> -е.
     - Suffixes -ник, -ак, -ок and velars -> -у.
     - Soft stems and hypocoristics -> -ю.
     - 1st declension hard stems -> -о, soft stems -> -е/-є, affectionates -> -ю.
  3. Instrumental case mixed sibilant stems (-ем vs -ом) [Правопис 2019 § 80]:
     - Sibilant stems ж, ч, ш, щ strictly take -ем (ножем, товаришем, плащем, мечем).
  4. Animacy in Masculine Accusative:
     - Animate beings take Genitive form (Acc = Gen).
     - Inanimate objects strictly take Nominative form (Acc = Nom).
  5. Deck validation: zero collisions, valid option counts, prompt blank markers.
  6. Balanced deterministic shuffle distribution across indices 0..3.
  7. Committed deck file parity.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from scripts.practice.noun_mechanics_engine import (
    NounMechanicsCategory,
    build_canonical_noun_mechanics_cards,
    export_noun_mechanics_deck,
    resolve_animacy_accusative,
    resolve_instrumental_singular_ii,
    resolve_noun_genitive_ii,
    resolve_noun_vocative,
    validate_noun_mechanics_card,
)


def test_resolve_noun_genitive_ii():
    """Verify II declension genitive ending rules per Правопис 2019 § 82."""
    # Concrete being / item -> -а / -я
    end_concrete, ua_c, en_c = resolve_noun_genitive_ii(
        category=NounMechanicsCategory.GEN_II_BEING_CONCRETE,
        is_concrete_or_being=True,
    )
    assert end_concrete == "-а / -я"
    assert "істот" in ua_c
    assert "-a/-ya" in en_c

    # Settlement / measure -> -а / -я
    end_settle, ua_s, en_s = resolve_noun_genitive_ii(
        category=NounMechanicsCategory.GEN_II_SETTLEMENT_MEASURE,
        is_concrete_or_being=False,
        is_settlement_or_measure=True,
    )
    assert end_settle == "-а / -я"
    assert "населені пункти" in ua_s
    assert "-a/-ya" in en_s

    # Mass substance / abstract process / collective -> -у / -ю
    end_mass, ua_m, en_m = resolve_noun_genitive_ii(
        category=NounMechanicsCategory.GEN_II_SUBSTANCE_MASS,
        is_concrete_or_being=False,
    )
    assert end_mass == "-у / -ю"
    assert "речовини" in ua_m
    assert "-u/-yu" in en_m


def test_resolve_noun_vocative():
    """Verify vocative case endings per Правопис 2019 §§ 73, 87."""
    # II declension hard stem -> -е
    end_hard, ua_h, _ = resolve_noun_vocative(declension=2, stem_group="hard")
    assert end_hard == "-е"
    assert "чергуванням" in ua_h

    # II declension velar / suffix -ok -> -у
    end_velar, ua_v, _ = resolve_noun_vocative(
        declension=2, stem_group="hard", has_velar_or_diminutive=True
    )
    assert end_velar == "-у"
    assert "задньоязиковий" in ua_v

    # II declension soft stem -> -ю
    end_soft, ua_s, _ = resolve_noun_vocative(declension=2, stem_group="soft")
    assert end_soft == "-ю"
    assert "м'якої групи" in ua_s

    # I declension hard stem -> -о
    end_i_hard, ua_ih, _ = resolve_noun_vocative(declension=1, stem_group="hard")
    assert end_i_hard == "-о"
    assert "I відміни твердої" in ua_ih

    # I declension soft affectionate -> -ю
    end_i_aff, ua_ia, _ = resolve_noun_vocative(
        declension=1, stem_group="soft", is_soft_hypocoristic=True
    )
    assert end_i_aff == "-ю"
    assert "Пестливі" in ua_ia


def test_resolve_instrumental_singular_ii():
    """Verify II declension instrumental endings per Правопис 2019 § 80."""
    # Hard stem -> -ом
    assert resolve_instrumental_singular_ii("hard")[0] == "-ом"

    # Mixed sibilant stem -> -ем
    assert resolve_instrumental_singular_ii("mixed")[0] == "-ем"
    assert "шиплячий" in resolve_instrumental_singular_ii("mixed")[1]

    # Soft stem -> -ем / -єм
    assert "-ем" in resolve_instrumental_singular_ii("soft")[0]


def test_resolve_animacy_accusative():
    """Verify animacy vs inanimacy accusative government."""
    anim_form, ua_a, _ = resolve_animacy_accusative(is_animate=True)
    assert "Родовий" in anim_form
    assert "істот" in ua_a

    inanim_form, ua_in, _ = resolve_animacy_accusative(is_animate=False)
    assert "Називний" in inanim_form
    assert "неістот" in ua_in


def test_canonical_deck_validity_and_zero_collisions():
    """Verify all canonical cards satisfy schema and collision-free requirements."""
    cards = build_canonical_noun_mechanics_cards()
    assert len(cards) >= 50, f"Expected at least 50 cards, found {len(cards)}"

    card_ids: set[str] = set()
    category_counts = Counter(c.category for c in cards)

    # Ensure every defined category has cards
    for cat in NounMechanicsCategory:
        assert category_counts[cat] >= 3, f"Category {cat} has fewer than 3 cards: {category_counts[cat]}"

    for card in cards:
        assert card.card_id not in card_ids, f"Duplicate card ID: {card.card_id}"
        card_ids.add(card.card_id)

        # Validate card
        errors = validate_noun_mechanics_card(card)
        assert not errors, f"Card {card.card_id} failed validation: {errors}"

        # Verify options length and uniqueness
        opts = card.all_options()
        assert len(opts) == 4
        assert len(set(opts)) == 4, f"Collision in options for {card.card_id}: {opts}"
        assert card.correct_answer in opts


def test_balanced_option_distribution():
    """Verify that sha256 deterministic shuffle yields balanced correct answer positions."""
    cards = build_canonical_noun_mechanics_cards()
    positions = [card.all_options().index(card.correct_answer) for card in cards]
    counts = Counter(positions)

    # With 64 cards and 4 options, expected count per index is 16.
    # Assert balanced distribution with reasonable tolerance [10, 24].
    for idx in range(4):
        assert 10 <= counts[idx] <= 24, f"Unbalanced position {idx}: count={counts[idx]} in total {len(cards)}"


def test_deck_export_and_file_parity(tmp_path: Path):
    """Verify deck JSON export produces valid schema and matches committed deck."""
    test_out = tmp_path / "noun_deck.json"
    exported_path = export_noun_mechanics_deck(test_out)

    assert exported_path.exists()
    with open(exported_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["version"] == "1.0.0"
    assert data["card_count"] == len(build_canonical_noun_mechanics_cards())
    assert len(data["cards"]) == data["card_count"]

    # Verify committed deck parity
    repo_deck_path = Path(__file__).resolve().parents[1] / "registry" / "practice" / "noun_mechanics_deck.json"
    assert repo_deck_path.exists(), "Committed deck file does not exist"

    with open(repo_deck_path, encoding="utf-8") as f:
        committed_data = json.load(f)

    assert data == committed_data, "Committed deck differs from fresh generator export"


def test_homonym_pair_coverage():
    """Verify all 6 semantic homonym pairs (12 cards) are covered in the canonical deck."""
    cards = build_canonical_noun_mechanics_cards()
    homonym_cards = [c for c in cards if c.category.value == "gen_ii_homonym_pair"]
    assert len(homonym_cards) == 12

    answers = {c.correct_answer for c in homonym_cards}
    expected_pairs = [
        ("каменя", "каменю"),
        ("листопада", "листопаду"),
        ("апарата", "апарату"),
        ("папера", "паперу"),
        ("акта", "акту"),
        ("терміна", "терміну"),
    ]
    for form1, form2 in expected_pairs:
        assert form1 in answers, f"Missing homonym card for {form1}"
        assert form2 in answers, f"Missing homonym card for {form2}"
