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
from pathlib import Path

from scripts.practice.verb_mechanics_engine import (
    build_canonical_verb_cards,
    export_verb_mechanics_deck,
    validate_verb_card,
    verify_deck_with_vesum,
    verify_distractors_with_vesum,
)


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


def test_export_and_committed_deck_parity(tmp_path: Path):
    """Verify exported JSON deck matches committed deck file."""
    cards = build_canonical_verb_cards()
    out_file = tmp_path / "verb_mechanics_deck.json"
    data = export_verb_mechanics_deck(cards, out_file)

    assert data["card_count"] == len(cards)
    assert len(data["cards"]) == len(cards)

    repo_deck_path = Path("registry/practice/verb_mechanics_deck.json")
    assert repo_deck_path.exists(), "Committed deck file registry/practice/verb_mechanics_deck.json must exist"

    with open(repo_deck_path, encoding="utf-8") as f:
        committed_data = json.load(f)

    assert data == committed_data, "Committed deck differs from fresh generator export"


def test_vesum_verification(requires_vesum_db):
    """Verify that VESUM database confirms all target words and validates corruption distractors."""
    cards = build_canonical_verb_cards()
    report = verify_deck_with_vesum(cards, requires_vesum_db)
    assert report["verified"] is True, f"VESUM verification failed: {report.get('missing_forms', [])}"
    assert report["checked_word_count"] >= 70

    dist_report = verify_distractors_with_vesum(cards, requires_vesum_db)
    assert dist_report["verified"] is True, (
        f"Corruption distractors matched valid standard words in VESUM: {dist_report.get('invalid_distractors', [])}"
    )
    assert dist_report["checked_distractor_count"] >= 100
