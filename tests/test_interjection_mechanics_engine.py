"""Unit tests for the Interjection and Onomatopoeia Deep Mechanics Practice Engine (Issue #8275).

Covers:
- 12 category rule resolutions and citations (Правопис 2019 § 46)
- 60 canonical cards count, distribution, uniqueness, and option balance
- Emotional valence and volitional animal call discrimination
- Orthography rules (§ 46, п. 1 repeated/particles hyphenation vs § 46, п. 2 separate phrases)
- Syntax & punctuation: vocative particle О/Ой without comma vs independent interjection with comma
- VESUM verification with CI skip guard
- JSON export parity with committed data/practice/interjection_mechanics_deck.json
- CLI --verify-vesum and --export flags
"""

import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.practice.interjection_mechanics_engine import (
    InterjectionCategory,
    InterjectionInterferenceKey,
    build_canonical_interjection_cards,
    export_deck,
    main,
    resolve_emotional_negative_rule,
    resolve_emotional_positive_rule,
    resolve_etiquette_gratitude_apology_rule,
    resolve_etiquette_greeting_farewell_rule,
    resolve_onomatopoeia_animal_sounds_rule,
    resolve_onomatopoeia_nature_mechanics_rule,
    resolve_spelling_hyphen_repeated_rule,
    resolve_spelling_multiword_separate_rule,
    resolve_spelling_particles_hyphen_rule,
    resolve_syntax_punctuation_particle_rule,
    resolve_volitional_animal_rule,
    resolve_volitional_imperative_rule,
    verify_deck_with_vesum,
)


def test_resolve_interjection_rules():
    """Verify that all 12 rule resolver functions return valid citations and summaries."""
    resolvers = [
        resolve_emotional_positive_rule,
        resolve_emotional_negative_rule,
        resolve_volitional_imperative_rule,
        resolve_volitional_animal_rule,
        resolve_etiquette_greeting_farewell_rule,
        resolve_etiquette_gratitude_apology_rule,
        resolve_onomatopoeia_nature_mechanics_rule,
        resolve_onomatopoeia_animal_sounds_rule,
        resolve_spelling_hyphen_repeated_rule,
        resolve_spelling_particles_hyphen_rule,
        resolve_spelling_multiword_separate_rule,
        resolve_syntax_punctuation_particle_rule,
    ]

    assert len(resolvers) == 12
    for r in resolvers:
        cit, ua, en = r()
        assert "Правопис" in cit
        assert "§ 46" in cit
        assert len(ua) > 30
        assert len(en) > 30

    # Specific subsection verification
    cit_rep, _, _ = resolve_spelling_hyphen_repeated_rule()
    assert "§ 46, п. 1, а)" in cit_rep

    cit_part, _, _ = resolve_spelling_particles_hyphen_rule()
    assert "§ 46, п. 1, б), в)" in cit_part

    cit_sep, _, _ = resolve_spelling_multiword_separate_rule()
    assert "§ 46, п. 2" in cit_sep


def test_build_canonical_interjection_cards_count_and_distribution():
    """Verify that 60 cards are built with exactly 5 cards per category across 12 categories."""
    cards = build_canonical_interjection_cards()
    assert len(cards) == 60

    cat_counts = Counter(c.category for c in cards)
    assert len(cat_counts) == 12

    for cat in InterjectionCategory:
        assert cat_counts[cat] == 5, f"Category {cat} does not have exactly 5 cards: {cat_counts[cat]}"


def test_cards_zero_collision_and_unique_options():
    """Verify that card IDs are unique, each card has 4 unique options, and distractors are well-formed."""
    cards = build_canonical_interjection_cards()
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
            assert isinstance(d.interference_key, InterjectionInterferenceKey)
            assert len(d.explanation_ua) > 15
            assert len(d.explanation_en) > 15


def test_card_prompt_display_and_full_sentence():
    """Verify that every card prompt contains the blank indicator _______."""
    cards = build_canonical_interjection_cards()
    for card in cards:
        assert "_______" in card.prompt, f"Card {card.card_id} prompt missing blank indicator: {card.prompt}"
        # Target token components should match the correct answer
        clean_target = card.target_token.strip(".,!?:;—…\"'«»`()[]").lower()
        clean_answer = card.correct_answer.strip(".,!?:;—…\"'«»`()[]").lower()
        for tok in clean_target.split():
            assert tok in clean_answer, (
                f"Card {card.card_id} target token component '{tok}' missing from answer '{clean_answer}'"
            )


def test_shuffled_options_balanced_distribution():
    """Verify that deterministic shuffle distributes correct answer across positions 0..3."""
    cards = build_canonical_interjection_cards()
    positions = []

    for card in cards:
        opts = card.all_options()
        idx = opts.index(card.correct_answer)
        positions.append(idx)

    pos_counts = Counter(positions)
    for pos in range(4):
        # With 60 cards, expected average is 15 per position; ensure each has >= 7
        assert pos_counts[pos] >= 7, f"Position {pos} count {pos_counts[pos]} is under-represented"


def test_emotional_interjections_semantics():
    """Verify emotional valence accuracy in categories 1 and 2."""
    cards = build_canonical_interjection_cards()
    pos_cards = [c for c in cards if c.category == InterjectionCategory.EMOTIONAL_POSITIVE]
    neg_cards = [c for c in cards if c.category == InterjectionCategory.EMOTIONAL_NEGATIVE]

    assert len(pos_cards) == 5
    assert len(neg_cards) == 5

    pos_answers = {c.correct_answer for c in pos_cards}
    assert pos_answers == {"Ура", "Ах", "Ох", "Леле", "Овва"}

    neg_answers = {c.correct_answer for c in neg_cards}
    assert neg_answers == {"Ой", "Ай", "лишенько", "Пхе", "Тьху"}


def test_volitional_commands_and_animal_calls():
    """Verify volitional human commands and animal calls in categories 3 and 4."""
    cards = build_canonical_interjection_cards()
    imp_cards = [c for c in cards if c.category == InterjectionCategory.VOLITIONAL_IMPERATIVE]
    anim_cards = [c for c in cards if c.category == InterjectionCategory.VOLITIONAL_ANIMAL]

    assert len(imp_cards) == 5
    assert len(anim_cards) == 5

    imp_answers = {c.correct_answer for c in imp_cards}
    assert imp_answers == {"Гайда", "марш", "Годі", "Геть", "Цить"}

    anim_answers = {c.correct_answer for c in anim_cards}
    assert anim_answers == {"Киць-киць", "Киш", "Тпру", "Но", "Вйо"}


def test_etiquette_separate_spelling_guardrails():
    """Verify that etiquette multi-word phrases test separate spelling without hyphens."""
    cards = build_canonical_interjection_cards()
    etiquette_cards = [
        c
        for c in cards
        if c.category
        in (
            InterjectionCategory.ETIQUETTE_GREETING_FAREWELL,
            InterjectionCategory.ETIQUETTE_GRATITUDE_APOLOGY,
            InterjectionCategory.SPELLING_MULTIWORD_SEPARATE,
        )
    ]

    card_map = {c.card_id: c for c in etiquette_cards}

    # Card 21: Добрий день
    c21 = card_map["interjection_card_21"]
    assert c21.correct_answer == "Добрий день"
    assert any(
        d.text == "Добрий-день" and d.interference_key == InterjectionInterferenceKey.UNWARRANTED_HYPHEN
        for d in c21.distractors
    )

    # Card 23: До побачення
    c23 = card_map["interjection_card_23"]
    assert c23.correct_answer == "До побачення"
    assert any(
        d.text == "До-побачення" and d.interference_key == InterjectionInterferenceKey.UNWARRANTED_HYPHEN
        for d in c23.distractors
    )
    assert any(
        d.text == "Допобачення" and d.interference_key == InterjectionInterferenceKey.UNWARRANTED_FUSION
        for d in c23.distractors
    )

    # Card 26: будь ласка
    c26 = card_map["interjection_card_26"]
    assert c26.correct_answer == "будь ласка"
    assert any(
        d.text == "будь-ласка" and d.interference_key == InterjectionInterferenceKey.UNWARRANTED_HYPHEN
        for d in c26.distractors
    )
    assert any(
        d.text == "будьласка" and d.interference_key == InterjectionInterferenceKey.UNWARRANTED_FUSION
        for d in c26.distractors
    )


def test_syntax_punctuation_particle_vs_interjection():
    """Verify syntax discrimination: vocative particle without comma vs interjection with comma."""
    cards = build_canonical_interjection_cards()
    syntax_cards = {c.card_id: c for c in cards if c.category == InterjectionCategory.SYNTAX_PUNCTUATION_PARTICLE}
    assert len(syntax_cards) == 5

    # Card 56: Vocative particle О without comma
    c56 = syntax_cards["interjection_card_56"]
    assert c56.correct_answer == "О краю"
    assert any(
        d.text == "О, краю" and d.interference_key == InterjectionInterferenceKey.PUNCTUATION_UNWARRANTED_COMMA_PARTICLE
        for d in c56.distractors
    )

    # Card 57: Vocative particle Ой without comma
    c57 = syntax_cards["interjection_card_57"]
    assert c57.correct_answer == "Ой Дніпре"
    assert any(
        d.text == "Ой, Дніпре"
        and d.interference_key == InterjectionInterferenceKey.PUNCTUATION_UNWARRANTED_COMMA_PARTICLE
        for d in c57.distractors
    )

    # Card 58: Independent interjection О with comma before address
    c58 = syntax_cards["interjection_card_58"]
    assert c58.correct_answer == "О, краю мій"
    assert any(
        d.text == "О краю мій" and d.interference_key == InterjectionInterferenceKey.PUNCTUATION_COMMA_OMISSION
        for d in c58.distractors
    )

    # Card 59: High exclamation intonation followed by capitalized sentence
    c59 = syntax_cards["interjection_card_59"]
    assert c59.correct_answer == "Леле!"
    assert any(
        d.text == "Леле," and d.interference_key == InterjectionInterferenceKey.PUNCTUATION_EXCLAMATION_OMISSION
        for d in c59.distractors
    )

    # Card 60: Calm narrative intonation with lowercase subsequent word
    c60 = syntax_cards["interjection_card_60"]
    assert c60.correct_answer == "Ох,"
    assert any(
        d.text == "Ох!" and d.interference_key == InterjectionInterferenceKey.PUNCTUATION_EXCLAMATION_OMISSION
        for d in c60.distractors
    )


def test_vesum_verification_100_percent():
    """Verify 100% VESUM coverage for all 60 canonical cards."""
    cards = build_canonical_interjection_cards()
    db_path = Path(__file__).resolve().parents[1] / "data/vesum.db"

    res = verify_deck_with_vesum(cards, db_path)
    if res.get("status") == "skipped":
        pytest.skip(f"VESUM db not available: {res.get('message')}")

    assert res["status"] == "passed"
    assert res["vesum_verified"] is True
    assert res["total_cards"] == 60
    assert res["target_tokens_count"] >= 60
    assert len(res["missing_targets"]) == 0
    assert len(res["empty_cards"]) == 0


def test_interjection_deck_json_export_and_file_parity(tmp_path: Path):
    """Verify JSON export schema and parity with committed artifact."""
    cards = build_canonical_interjection_cards()
    export_file = tmp_path / "interjection_mechanics_deck.json"
    payload = export_deck(cards, export_file)

    assert payload["schema_version"] == "1.0"
    assert payload["card_count"] == 60
    assert len(payload["categories"]) == 12
    assert len(payload["cards"]) == 60

    committed_path = Path(__file__).resolve().parents[1] / "data/practice/interjection_mechanics_deck.json"
    assert committed_path.exists(), "Committed data/practice/interjection_mechanics_deck.json does not exist"

    with open(committed_path, encoding="utf-8") as f:
        committed_data = json.load(f)

    assert committed_data["card_count"] == payload["card_count"]
    assert committed_data["categories"] == payload["categories"]
    assert committed_data["schema_version"] == payload["schema_version"]

    for i, c in enumerate(payload["cards"]):
        comm_card = committed_data["cards"][i]
        assert c["id"] == comm_card["id"]
        assert c["category"] == comm_card["category"]
        assert c["target_token"] == comm_card["target_token"]
        assert c["correct_answer"] == comm_card["correct_answer"]
        assert c["options"] == comm_card["options"]


def test_cli_verify_vesum_and_export(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, tmp_path: Path):
    """Verify CLI flags --verify-vesum, --export, and --json."""
    export_target = str(tmp_path / "cli_deck.json")
    monkeypatch.setattr(
        "sys.argv",
        ["interjection_mechanics_engine.py", "--verify-vesum", "--export", "--output", export_target],
    )
    main()
    out = capsys.readouterr().out
    assert "Cards: 60" in out
    assert "VESUM verification: PASSED" in out or "VESUM verification: SKIPPED" in out
    assert "Successfully exported 60 cards" in out
    assert Path(export_target).exists()
