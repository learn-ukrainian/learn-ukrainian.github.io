"""Unit and integration tests for Ukrainian Function Words Practice Engine.

Tests:
  1. Preposition orthography & government:
     - Hyphenation with з-/із- (§ 42, п. 2) vs solid compound (§ 42, п. 1) vs locutions (§ 42, п. 3).
     - Causal government: завдяки (+ Dat, positive) vs через (+ Acc, adverse/neutral).
     - Temporal government: протягом/упродовж vs literal air draft 'на протязі'.
  2. Conjunction disambiguation (§ 43, п. 1 та примітка):
     - проте/зате vs про те/за те.
     - щоб vs що б.
     - якби vs як би.
     - якщо vs як що.
     - також/теж vs так же/те ж (Правопис 2019, § 43, п. 1 vs § 44, п. 1.13; СУМ-20).
  3. Particle orthography (§ 44, п. 1 та 2):
     - не with nouns/adjectives: new concept (§ 44, п. 2.7) vs explicit contrast with 'а' (§ 44, п. 1.4).
     - не with verbs/gerunds: separate (§ 44, п. 1.1 та 1.2) unless bound root (§ 44, п. 2.5).
     - не with participles: isolated attribute (§ 44, п. 2.8) vs with dependent words (§ 44, п. 1.3).
     - Enclitics: -бо, -но, -то, -от, -таки (§ 44, п. 3.1) vs prepositive separate (§ 44, п. 3.1, прим. 2).
     - Prefix particles: будь-, казна-, хтозна- (§ 44, п. 3.2) vs split by preposition (§ 44, п. 1; § 34).
  4. Deck validation and zero collisions across all canonical cards.
  5. Deterministic balanced option distribution.
  6. Deck JSON export integrity and committed deck parity.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.practice.function_words_engine import (
    FunctionWordCategory,
    build_canonical_function_word_cards,
    export_function_word_deck,
    resolve_causal_preposition,
    resolve_conjunction_homophone,
    resolve_duration_preposition,
    resolve_particle_hyphenation,
    resolve_particle_ne,
    resolve_preposition_hyphenation,
    validate_function_word_card,
)


def test_resolve_preposition_hyphenation():
    """Verify compound preposition hyphenation rules per Правопис 2019 (§ 42, п. 2 vs § 42, п. 1)."""
    # Prepositions with initial з- / із- must be hyphenated (§ 42, п. 2)
    assert resolve_preposition_hyphenation("з-під")[0] is True
    assert resolve_preposition_hyphenation("з-за")[0] is True
    assert resolve_preposition_hyphenation("із-за")[0] is True
    assert resolve_preposition_hyphenation("з-поміж")[0] is True
    assert resolve_preposition_hyphenation("з-понад")[0] is True
    assert resolve_preposition_hyphenation("з-посеред")[0] is True

    # Compound prepositions without initial з-/із- are written solid (§ 42, п. 1)
    assert resolve_preposition_hyphenation("посеред")[0] is False
    assert resolve_preposition_hyphenation("задля")[0] is False
    assert resolve_preposition_hyphenation("заради")[0] is False
    assert resolve_preposition_hyphenation("внаслідок")[0] is False
    assert resolve_preposition_hyphenation("напередодні")[0] is False
    assert resolve_preposition_hyphenation("довкола")[0] is False


def test_resolve_causal_preposition():
    """Verify semantic polarity constraint on завдяки vs через."""
    # Positive outcome -> завдяки
    pos_prep, ua_pos, en_pos = resolve_causal_preposition(is_positive_factor=True)
    assert pos_prep == "завдяки"
    assert "позитивних" in ua_pos
    assert "positive" in en_pos

    # Adverse / negative outcome -> через
    neg_prep, ua_neg, en_neg = resolve_causal_preposition(is_positive_factor=False)
    assert neg_prep == "через"
    assert "небажаних" in ua_neg
    assert "adverse" in en_neg


def test_resolve_duration_preposition():
    """Verify duration (протягом) vs literal draft (на протязі)."""
    dur_prep, _, _ = resolve_duration_preposition(is_time_duration=True)
    assert dur_prep == "протягом"

    draft_prep, _, _ = resolve_duration_preposition(is_time_duration=False)
    assert draft_prep == "на протязі"


def test_resolve_conjunction_homophones():
    """Verify conjunction disambiguation from homophonous word sequences per § 43, п. 1 та примітка."""
    # проте vs про те
    assert resolve_conjunction_homophone("проте", is_conjunction=True)[0] == "проте"
    assert resolve_conjunction_homophone("проте", is_conjunction=False)[0] == "про те"

    # зате vs за те
    assert resolve_conjunction_homophone("зате", is_conjunction=True)[0] == "зате"
    assert resolve_conjunction_homophone("зате", is_conjunction=False)[0] == "за те"

    # щоб vs що б
    assert resolve_conjunction_homophone("щоб", is_conjunction=True)[0] == "щоб"
    assert resolve_conjunction_homophone("щоб", is_conjunction=False)[0] == "що б"

    # якби vs як би
    assert resolve_conjunction_homophone("якби", is_conjunction=True)[0] == "якби"
    assert resolve_conjunction_homophone("якби", is_conjunction=False)[0] == "як би"

    # якщо vs як що
    assert resolve_conjunction_homophone("якщо", is_conjunction=True)[0] == "якщо"
    assert resolve_conjunction_homophone("якщо", is_conjunction=False)[0] == "як що"

    # також vs так же
    assert resolve_conjunction_homophone("також", is_conjunction=True)[0] == "також"
    assert resolve_conjunction_homophone("також", is_conjunction=False)[0] == "так же"

    # теж vs те ж
    assert resolve_conjunction_homophone("теж", is_conjunction=True)[0] == "теж"
    assert resolve_conjunction_homophone("теж", is_conjunction=False)[0] == "те ж"

    with pytest.raises(ValueError):
        resolve_conjunction_homophone("невідомий", is_conjunction=True)


def test_resolve_particle_ne():
    """Verify orthography of 'не' per Правопис 2019 (§ 44, п. 1 та 2)."""
    # Bound root verbs always solid (§ 44, п. 2.5)
    assert resolve_particle_ne("verb", cannot_stand_without_ne=True)[0] == "разом"

    # Regular verbs always separate (§ 44, п. 1.1 та 1.2)
    assert resolve_particle_ne("verb")[0] == "окремо"
    assert resolve_particle_ne("gerund")[0] == "окремо"

    # Explicit contrast with 'а' always separate (§ 44, п. 1.4)
    assert resolve_particle_ne("noun", has_contrast=True)[0] == "окремо"
    assert resolve_particle_ne("adj", has_contrast=True)[0] == "окремо"
    assert resolve_particle_ne("adverb", has_contrast=True)[0] == "окремо"

    # Nouns & adjectives forming new concept -> solid (§ 44, п. 2.7)
    assert resolve_particle_ne("noun", forms_new_concept=True)[0] == "разом"
    assert resolve_particle_ne("adj", forms_new_concept=True)[0] == "разом"
    assert resolve_particle_ne("adv", forms_new_concept=True)[0] == "разом"

    # Participle without dependents -> solid (§ 44, п. 2.8)
    assert resolve_particle_ne("participle", has_dependent_words=False)[0] == "разом"

    # Participle with dependents -> separate (§ 44, п. 1.3)
    assert resolve_particle_ne("participle", has_dependent_words=True)[0] == "окремо"


def test_resolve_particle_hyphenation():
    """Verify enclitic and prefix particle hyphenation per § 44, п. 1 та 3."""
    # Enclitics -бо, -но, -то, -от (§ 44, п. 3.1)
    assert resolve_particle_hyphenation("бо")[0] == "дефіс"
    assert resolve_particle_hyphenation("но")[0] == "дефіс"
    assert resolve_particle_hyphenation("то")[0] == "дефіс"
    assert resolve_particle_hyphenation("от")[0] == "дефіс"

    # Таки: postpositive -> hyphen (§ 44, п. 3.1), prepositive -> separate (§ 44, п. 3.1, прим. 2)
    assert resolve_particle_hyphenation("таки", position_after_word=True)[0] == "дефіс"
    assert resolve_particle_hyphenation("таки", position_after_word=False)[0] == "окремо"

    # Будь-, хтозна-, казна-: standalone -> hyphen (§ 44, п. 3.2), with intervening preposition -> separate (§ 44, п. 1; § 34)
    assert resolve_particle_hyphenation("будь", has_intervening_preposition=False)[0] == "дефіс"
    assert resolve_particle_hyphenation("хтозна", has_intervening_preposition=False)[0] == "дефіс"
    assert resolve_particle_hyphenation("будь", has_intervening_preposition=True)[0] == "окремо"
    assert resolve_particle_hyphenation("хтозна", has_intervening_preposition=True)[0] == "окремо"


def test_canonical_cards_integrity_and_zero_collisions():
    """Ensure all canonical cards pass validation with zero errors and zero option collisions."""
    cards = build_canonical_function_word_cards()
    assert len(cards) >= 30, f"Expected at least 30 canonical cards, got {len(cards)}"

    all_ids = set()
    categories_present = set()

    for card in cards:
        # ID uniqueness
        assert card.card_id not in all_ids, f"Duplicate card ID: {card.card_id}"
        all_ids.add(card.card_id)
        categories_present.add(card.category)

        # Run validator
        errors = validate_function_word_card(card)
        assert not errors, f"Card {card.card_id} failed validation: {errors}"

        # Distinct options verification
        options = card.all_options()
        assert len(options) == 4, f"Card {card.card_id} does not have 4 options"
        assert len(set(options)) == 4, f"Collision detected in card {card.card_id}: {options}"
        assert card.correct_answer in options

        # Sentence rendering
        assert len(card.full_sentence) > len(card.correct_answer)
        assert card.correct_answer in card.full_sentence
        assert "_______" in card.prompt_display

    # Verify coverage across all FunctionWordCategory enums
    expected_categories = set(FunctionWordCategory)
    missing = expected_categories - categories_present
    assert not missing, f"Missing test cards for categories: {missing}"


def test_export_function_word_deck(tmp_path: Path):
    """Test exporting function word deck to JSON format and verify committed deck parity."""
    cards = build_canonical_function_word_cards()
    out_file = tmp_path / "function_words_deck.json"
    deck = export_function_word_deck(cards, output_path=out_file)

    assert deck["version"] == "1.0"
    assert deck["total_cards"] == len(cards)
    assert len(deck["cards"]) == len(cards)
    assert out_file.exists()

    with open(out_file, encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded["total_cards"] == len(cards)
    first_card = loaded["cards"][0]
    assert "prompt" in first_card
    assert "correctAnswer" in first_card
    assert len(first_card["options"]) == 4
    assert len(first_card["distractors"]) == 3

    # Verify committed deck matches fresh export
    repo_root = Path(__file__).resolve().parent.parent
    committed_deck_file = repo_root / "registry" / "practice" / "function_words_deck.json"
    assert committed_deck_file.exists(), f"Committed deck missing at {committed_deck_file}"
    with open(committed_deck_file, encoding="utf-8") as f:
        committed_deck = json.load(f)
    assert committed_deck == loaded, "Committed function_words_deck.json diverges from fresh export!"


def test_option_position_distribution():
    """Verify that card.all_options() distributes correct answers across positions 0..3."""
    cards = build_canonical_function_word_cards()
    positions = [card.all_options().index(card.correct_answer) for card in cards]
    position_counts = {p: positions.count(p) for p in range(4)}

    # Every position (0, 1, 2, 3) must be tightly distributed (7 <= count <= 14 for 42 cards)
    for p in range(4):
        assert 7 <= position_counts[p] <= 14, (
            f"Position {p} has {position_counts[p]} answers, expected between 7 and 14 (total {len(cards)})"
        )
