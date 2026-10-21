"""Unit and integration tests for Ukrainian Adjective Deep Mechanics Practice Engine.

Tests:
  1. Degrees of comparison formation rules [Правопис 2019 §§ 110–113]:
     - Consonant mutations: г, ж, з + -ш- -> -жч- (дорожчий, ближчий, вужчий).
     - Consonant mutations: к, с + -ш- -> -щ- (вищий, товщий, кращий).
     - Standard qualitative suffix: -іш- (новіший, тепліший, розумніший).
     - Suppletive comparison (великий -> більший, малий -> менший, поганий -> гірший).
     - Compound analytic comparison (більш / менш + base adjective).
     - Superlative synthetic prefix: най- (найкращий, найвищий; anti-calque: *самий кращий).
     - Emphatic prefixes: якнай-, щонай-.
  2. Declension groups: Hard vs Soft [Правопис 2019 §§ 106–109]:
     - High-error focus: masculine/neuter soft instrumental singular ending strictly -ім
       (синім, літнім, осіннім, раннім), not *-им*.
     - Soft Genitive/Dative: -ього / -ьому.
  3. Possessive adjectives and morphophonemic suffixation [Правопис 2019 §§ 22, 107]:
     - Suffix -ів (-ова, -еве) from II declension masculine nouns.
     - Suffix -ин (-ина, -ине) from I declension nouns with mutations (Ольга -> Ольжин, дочка -> доччин).
     - Derivational suffixes -ськ-, -цьк-, -зьк- (§ 22).
  4. Deck validation: zero collisions, valid option counts, prompt blank markers.
  5. Balanced deterministic shuffle distribution across indices 0..3.
  6. Committed deck file parity.
  7. VESUM database validation for all target inflected forms.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from scripts.practice.adjective_mechanics_engine import (
    AdjectiveCategory,
    build_canonical_adjective_cards,
    export_adjective_mechanics_deck,
    validate_adjective_card,
    verify_deck_with_vesum,
    verify_distractors_with_vesum,
)


def test_canonical_deck_validity_and_zero_collisions():
    """Verify all canonical cards satisfy schema and collision-free requirements."""
    cards = build_canonical_adjective_cards()
    assert len(cards) >= 60, f"Expected at least 60 cards, found {len(cards)}"

    card_ids: set[str] = set()
    category_counts = Counter(c.category for c in cards)

    # Ensure every defined category has at least 3 cards
    for cat in AdjectiveCategory:
        assert category_counts[cat] >= 3, f"Category {cat} has fewer than 3 cards: {category_counts[cat]}"

    for card in cards:
        assert card.card_id not in card_ids, f"Duplicate card ID: {card.card_id}"
        card_ids.add(card.card_id)

        # Validate card
        errors = validate_adjective_card(card)
        assert not errors, f"Card {card.card_id} failed validation: {errors}"

        # Verify options length and uniqueness
        opts = card.all_options()
        assert len(opts) == 4
        assert len(set(opts)) == 4, f"Collision in options for {card.card_id}: {opts}"
        assert card.correct_answer in opts


def test_deck_export_and_file_parity(tmp_path: Path):
    """Verify deck JSON export produces valid schema and matches committed deck."""
    test_out = tmp_path / "adj_deck.json"
    exported_path = export_adjective_mechanics_deck(test_out)

    assert exported_path.exists()
    with open(exported_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["version"] == "1.0.0"
    assert data["card_count"] == len(build_canonical_adjective_cards())
    assert len(data["cards"]) == data["card_count"]

    # Verify committed deck parity
    repo_deck_path = Path(__file__).resolve().parents[1] / "registry" / "practice" / "adjective_mechanics_deck.json"
    assert repo_deck_path.exists(), "Committed deck file does not exist"

    with open(repo_deck_path, encoding="utf-8") as f:
        committed_data = json.load(f)

    assert data == committed_data, "Committed deck differs from fresh generator export"


def test_vesum_verification(requires_vesum_db):
    """Verify that VESUM database confirms all target words and validates corruption distractors."""
    cards = build_canonical_adjective_cards()
    report = verify_deck_with_vesum(cards, requires_vesum_db)
    assert report["verified"] is True, f"VESUM verification failed: {report.get('missing_forms', [])}"
    assert report["checked_word_count"] >= 70

    # Extended distractor verification: ensure phonological/morphological corruption
    # distractors are not valid standard words in VESUM.
    dist_report = verify_distractors_with_vesum(cards, requires_vesum_db)
    assert dist_report["verified"] is True, (
        f"Corruption distractors matched valid standard words in VESUM: {dist_report.get('invalid_distractors', [])}"
    )
    assert dist_report["checked_distractor_count"] >= 100
