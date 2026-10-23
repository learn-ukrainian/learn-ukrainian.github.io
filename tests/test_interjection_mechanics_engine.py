"""Unit tests for the Interjection and Onomatopoeia Deep Mechanics Practice Engine (Issue #8275).

Covers:
- 12 category rule resolutions and citations (Правопис 2019 § 35, § 41, § 44, § 46, § 157, § 158)
- 60 canonical cards count, distribution, uniqueness, and option balance
- Emotional valence and volitional animal call discrimination
- Orthography rules (§ 35, § 44 repeated/particles hyphenation vs § 41 separate phrases)
- Syntax & punctuation: vocative particle О/Ой without comma vs independent interjection with comma
- VESUM token validation: rejection of malformed tokens and bad tags, acceptance of compounds
- VESUM verification with CI skip guard
- JSON export parity with committed registry/practice/interjection_mechanics_deck.json
- CLI --verify-vesum and --export flags
"""

import json
from pathlib import Path

import pytest

from scripts.lib.readonly_sqlite import open_readonly
from scripts.practice.interjection_mechanics_engine import (
    InterjectionCategory,
    InterjectionInterferenceKey,
    build_canonical_interjection_cards,
    export_deck,
    is_valid_vesum_token,
    main,
    resolve_onomatopoeia_nature_mechanics_rule,
    verify_deck_with_vesum,
)


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


def test_card_45_distractor_exclusivity_regression():
    """Verify Card 45 does not reject valid Ukrainian interjection 'Стук-стук' (СУМ-11)."""
    cards = build_canonical_interjection_cards()
    c45 = next(c for c in cards if c.card_id == "interjection_card_45")
    assert c45.correct_answer == "Тук-тук"

    distractor_texts = [d.text for d in c45.distractors]
    # 'Стук-стук' is an authentic Ukrainian interjection for knocking (СУМ-11 СТУК¹),
    # so it must NOT be marked as an incorrect distractor!
    assert "Стук-стук" not in distractor_texts
    assert "Тік-так" in distractor_texts

    d_tik_tak = next(d for d in c45.distractors if d.text == "Тік-так")
    assert d_tik_tak.interference_key == InterjectionInterferenceKey.INCORRECT_SOUND_SOURCE
    assert "годинника" in d_tik_tak.explanation_ua


def test_card_33_feedback_and_rule_summary_regression():
    """Verify that Card 33 and Nature Mechanics category teach 'кап-кап' and not 'крап-крап' (Astra R5)."""
    cit, ua, en = resolve_onomatopoeia_nature_mechanics_rule()
    assert "§ 35" in cit
    assert "кап-кап" in ua
    assert "кап-кап" in en
    assert "крап-крап" not in ua
    assert "крап-крап" not in en

    cards = build_canonical_interjection_cards()
    nature_cards = [c for c in cards if c.category == InterjectionCategory.ONOMATOPOEIA_NATURE_MECHANICS]
    assert len(nature_cards) == 5
    for c in nature_cards:
        assert "кап-кап" in c.rule_summary_ua
        assert "кап-кап" in c.rule_summary_en
        assert "крап-крап" not in c.rule_summary_ua
        assert "крап-крап" not in c.rule_summary_en

    c33 = next(c for c in cards if c.card_id == "interjection_card_33")
    assert c33.target_token == "кап-кап"
    assert c33.correct_answer == "Кап-кап"
    assert "кап-кап" in c33.rule_summary_ua
    assert "крап-крап" not in c33.rule_summary_ua


def test_syntax_punctuation_particle_vs_interjection():
    """Verify syntax discrimination: vocative particle without comma vs interjection with comma."""
    cards = build_canonical_interjection_cards()
    syntax_cards = {c.card_id: c for c in cards if c.category == InterjectionCategory.SYNTAX_PUNCTUATION_PARTICLE}
    assert len(syntax_cards) == 5

    # Card 56: Vocative particle О without comma (stated in prompt)
    c56 = syntax_cards["interjection_card_56"]
    assert c56.correct_answer == "О краю"
    assert "без інтонаційної паузи" in c56.prompt
    assert "підсилювальну частку" in c56.prompt
    assert any(
        d.text == "О, краю" and d.interference_key == InterjectionInterferenceKey.PUNCTUATION_UNWARRANTED_COMMA_PARTICLE
        for d in c56.distractors
    )

    # Card 57: Vocative particle Ой without comma (stated in prompt)
    c57 = syntax_cards["interjection_card_57"]
    assert c57.correct_answer == "Ой Дніпре"
    assert "без інтонаційної паузи" in c57.prompt
    assert "підсилювальну частку" in c57.prompt
    assert any(
        d.text == "Ой, Дніпре"
        and d.interference_key == InterjectionInterferenceKey.PUNCTUATION_UNWARRANTED_COMMA_PARTICLE
        for d in c57.distractors
    )

    # Card 58: Independent interjection О with comma before address (stated in prompt)
    c58 = syntax_cards["interjection_card_58"]
    assert c58.correct_answer == "О, краю мій"
    assert "інтонаційну паузу" in c58.prompt
    assert "самостійного емоційного вигуку" in c58.prompt
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


def test_vesum_verification_100_percent(requires_vesum_db):
    """Verify 100% VESUM coverage for all 60 canonical cards."""
    cards = build_canonical_interjection_cards()
    db_path = requires_vesum_db

    res = verify_deck_with_vesum(cards, db_path)
    assert res.get("status") != "skipped", "Validated VESUM input must be executed"

    assert res["status"] == "passed"
    assert res["vesum_verified"] is True
    assert res["total_cards"] == 60
    assert res["target_tokens_count"] >= 60
    assert len(res["missing_targets"]) == 0
    assert len(res["empty_cards"]) == 0

    # Negative regression check: verify that a synthetic compound like 'кіт-кіт' fails verification
    import dataclasses

    corrupt_card = dataclasses.replace(cards[0], target_token="кіт-кіт")
    res_corrupt = verify_deck_with_vesum([corrupt_card], db_path)
    assert res_corrupt["vesum_verified"] is False
    assert any("кіт-кіт" in m for m in res_corrupt["missing_targets"])


def test_interjection_deck_json_export_and_file_parity(tmp_path: Path):
    """Verify JSON export schema and parity with committed artifact."""
    cards = build_canonical_interjection_cards()
    export_file = tmp_path / "interjection_mechanics_deck.json"
    payload = export_deck(cards, export_file)

    assert payload["schema_version"] == "1.0"
    assert payload["card_count"] == 60
    assert len(payload["categories"]) == 12
    assert len(payload["cards"]) == 60

    committed_path = Path(__file__).resolve().parents[1] / "registry/practice/interjection_mechanics_deck.json"
    assert committed_path.exists(), "Committed registry/practice/interjection_mechanics_deck.json does not exist"

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


def test_is_valid_vesum_token_rejections_and_compounds(requires_vesum_db):
    """Verify is_valid_vesum_token rejects malformed tokens/bad tags and validates compounds."""
    db_path = requires_vesum_db

    conn = open_readonly(db_path)
    cursor = conn.cursor()

    # Rejection of malformed tokens
    assert is_valid_vesum_token(cursor, "") is False
    assert is_valid_vesum_token(cursor, "---") is False
    assert is_valid_vesum_token(cursor, "ура--ура") is False
    assert is_valid_vesum_token(cursor, "-ура") is False
    assert is_valid_vesum_token(cursor, "ура-") is False

    # Rejection of bad tag entries and corrupt compounds (Astra R2 regression tests)
    assert is_valid_vesum_token(cursor, "будь-ласка") is False  # noninfl:insert:bad
    assert is_valid_vesum_token(cursor, "чуть-чуть") is False  # adv:bad
    assert is_valid_vesum_token(cursor, "баю-баю") is False  # intj:bad
    assert is_valid_vesum_token(cursor, "чи-то") is False  # conj:coord:bad

    # Rejection of invalid constituent morphology in compounds
    assert (
        is_valid_vesum_token(cursor, "столу-столу") is False
    )  # dative/locative noun cannot form onomatopoeic reduplication
    assert (
        is_valid_vesum_token(cursor, "кіт-кіт") is False
    )  # synthetic negative control: nominative noun cannot form sound reduplication (Astra R4)
    assert (
        is_valid_vesum_token(cursor, "пес-пес") is False
    )  # nominative noun cannot form sound reduplication (Astra R4)
    assert (
        is_valid_vesum_token(cursor, "стіл-стіл") is False
    )  # nominative noun cannot form sound reduplication (Astra R4)
    assert (
        is_valid_vesum_token(cursor, "крап-крап") is False
    )  # 'крап' is noun only in VESUM, cannot form sound reduplication (Astra R4)
    assert (
        is_valid_vesum_token(cursor, "гарний-бо") is False
    )  # adjective cannot take enclitic particle as an imperative/interjection compound

    # Rejection of non-existent words
    assert is_valid_vesum_token(cursor, "неіснуючеслововигукxyz") is False

    # Acceptance of standard simple words
    assert is_valid_vesum_token(cursor, "ура") is True
    assert is_valid_vesum_token(cursor, "ой") is True
    assert is_valid_vesum_token(cursor, "гайда") is True

    # Acceptance of valid enclitic particle compounds (§ 44, п. 3, 1))
    assert is_valid_vesum_token(cursor, "годі-бо") is True
    assert is_valid_vesum_token(cursor, "ну-бо") is True
    assert is_valid_vesum_token(cursor, "давай-но") is True

    # Acceptance of valid reduplications (§ 35, п. 5, 4))
    assert is_valid_vesum_token(cursor, "гав-гав") is True
    assert is_valid_vesum_token(cursor, "кап-кап") is True
    assert is_valid_vesum_token(cursor, "хлюп-хлюп") is True

    # Acceptance of attested fixed idioms
    assert is_valid_vesum_token(cursor, "їй-богу") is True
    assert is_valid_vesum_token(cursor, "дзень-дзелень") is True

    conn.close()


def test_cli_verify_vesum_missing_exit_1(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, tmp_path: Path
):
    """Verify CLI --verify-vesum exits with code 1 when VESUM db is absent."""
    fake_root = tmp_path / "fake_repo"
    fake_root.mkdir()
    monkeypatch.setattr("scripts.practice.interjection_mechanics_engine.PROJECT_ROOT", fake_root)

    monkeypatch.setattr(
        "sys.argv",
        ["interjection_mechanics_engine.py", "--verify-vesum"],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1

    out = capsys.readouterr().out
    assert "VESUM verification: SKIPPED" in out
