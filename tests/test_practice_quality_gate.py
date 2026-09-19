"""Unit tests for Practice Quality Gate (Issue #7944)."""

import json
from pathlib import Path

import pytest

from scripts.audit.practice_quality_gate import (
    VOLUME_THRESHOLDS,
    audit_card_ambiguity,
    audit_error_correction_deck,
    audit_practice_shards,
    audit_sentence_inventory,
    audit_teacher_cloze_deck,
    run_all_practice_audits,
)


def test_audit_teacher_cloze_validates_blank_count(tmp_path: Path):
    deck = {
        "cloze": [
            {
                "clozeId": "good_1",
                "sentence": "Це гарне _____ речення.",
                "form": "гарне",
                "options": [{"label": "гарне", "kind": "answer"}, {"label": "погане", "kind": "distractor"}],
            },
            {
                "clozeId": "bad_multi",
                "sentence": "Перше _____ і друге _____ речення.",
                "form": "гарне",
                "options": [{"label": "гарне", "kind": "answer"}, {"label": "погане", "kind": "distractor"}],
            },
        ]
    }
    deck_path = tmp_path / "cloze.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

    violations = audit_teacher_cloze_deck(deck_path)
    assert any(v["type"] == "INVALID_BLANK_COUNT" and v["item"] == "bad_multi" for v in violations)
    assert not any(v["item"] == "good_1" for v in violations)


def test_audit_teacher_cloze_detects_intentional_error_leak(tmp_path: Path):
    deck = {
        "cloze": [
            {
                "clozeId": "leaked_1",
                "sentence": "НЕПРАВИЛЬНО ПРАВИЛЬНО _____ рішення зволікати з рішенням",
                "form": "затягувати",
                "options": [{"label": "затягувати", "kind": "answer"}, {"label": "робити", "kind": "distractor"}],
            }
        ]
    }
    deck_path = tmp_path / "cloze.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

    violations = audit_teacher_cloze_deck(deck_path)
    assert any(v["type"] == "INTENTIONAL_ERROR_LEAK" for v in violations)


def test_audit_teacher_cloze_detects_duplicate_options(tmp_path: Path):
    deck = {
        "cloze": [
            {
                "clozeId": "dup_opt",
                "sentence": "Я читаю цікаву _____ увечері.",
                "form": "книгу",
                "options": [
                    {"label": "книгу", "kind": "answer"},
                    {"label": "книгу", "kind": "distractor"},
                ],
            }
        ]
    }
    deck_path = tmp_path / "cloze.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

    violations = audit_teacher_cloze_deck(deck_path)
    assert any(v["type"] == "DUPLICATE_OPTIONS" for v in violations)


def test_audit_error_correction_validates_contract(tmp_path: Path):
    valid_deck = {
        "drills": [
            {
                "id": "drill_good",
                "sentence": "Він приймав участь у зборах.",
                "errorWord": "приймав участь",
                "correctForm": "брав участь",
                "options": ["брав участь", "приймав участь"],
                "explanation": "Калька з російської мови.",
            },
            {
                "id": "drill_missing_target",
                "sentence": "Він прийшов додому вчасно.",
                "errorWord": "приймав участь",
                "correctForm": "брав участь",
                "options": ["брав участь", "приймав участь"],
                "explanation": "Калька з російської мови.",
            },
            {
                "id": "drill_missing_in_options",
                "sentence": "У нього був високий авторитет.",
                "errorWord": "авторитет",
                "correctForm": "престиж",
                "options": ["повага", "визнання"],
                "explanation": "Стилістична заміна.",
            },
        ]
    }
    deck_path = tmp_path / "ec.json"
    deck_path.write_text(json.dumps(valid_deck, ensure_ascii=False), encoding="utf-8")

    violations = audit_error_correction_deck(deck_path)
    assert any(v["type"] == "ERROR_TARGET_NOT_IN_SENTENCE" and v["item"] == "drill_missing_target" for v in violations)
    assert any(
        v["type"] == "CORRECT_TARGET_MISSING_IN_OPTIONS" and v["item"] == "drill_missing_in_options" for v in violations
    )
    assert not any(v["item"] == "drill_good" for v in violations)


def test_audit_sentence_inventory_intentional_errors(tmp_path: Path):
    inv = {
        "rows": [
            {"lemma": "тест", "sentence": "Це звичайне речення."},
            {"lemma": "помилка", "sentence": "Помилку допущено у варіанті А."},
        ]
    }
    inv_path = tmp_path / "inv.json"
    inv_path.write_text(json.dumps(inv, ensure_ascii=False), encoding="utf-8")

    violations = audit_sentence_inventory(inv_path)
    assert len(violations) == 1
    assert violations[0]["type"] == "INTENTIONAL_ERROR_LEAK"


def test_audit_error_correction_vesum_attestation(tmp_path: Path, monkeypatch):
    """Verify that unattested Ukrainian words in error-correction drills are flagged by VESUM."""
    from scripts.audit import practice_quality_gate

    deck = {
        "drills": [
            {
                "id": "drill_valid",
                "sentence": "Він брав участь у зборах.",
                "errorWord": "приймав участь",
                "correctForm": "брав",
                "options": ["брав", "приймав"],
                "explanation": "Калька.",
            },
            {
                "id": "drill_unattested",
                "sentence": "Це неіснуючеслово речення.",
                "errorWord": "помилка",
                "correctForm": "неіснуючеслово",
                "options": ["неіснуючеслово", "варіант"],
                "explanation": "Неіснуюче слово.",
            },
        ]
    }
    deck_path = tmp_path / "ec.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")

    def mock_verify_word(word: str, db_path=None):
        return word == "брав"

    monkeypatch.setattr(practice_quality_gate, "verify_word", mock_verify_word)
    fake_db = tmp_path / "mock_vesum.db"
    fake_db.touch()

    violations = audit_error_correction_deck(deck_path, vesum_db=fake_db)
    assert any(v["type"] == "VESUM_UNATTESTED" and v["item"] == "drill_unattested" for v in violations), (
        f"Expected VESUM_UNATTESTED violation, got: {violations}"
    )


def test_audit_practice_shards_volume_thresholds(tmp_path: Path):
    """Verify that thin-mode volume thresholds (paronym>=250, homonym>=150, heritage>=250) are enforced."""
    # Under-threshold paronym shard (only 2 items)
    paronym_data = {
        "paronym": [
            {
                "paronymId": f"par_{i}",
                "prompt": "Сьогодні він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Бігти vs бігати.",
            }
            for i in range(2)
        ]
    }
    shard_file = tmp_path / "practice-paronym.A1.json"
    shard_file.write_text(json.dumps(paronym_data, ensure_ascii=False), encoding="utf-8")

    counts, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=True, verify_vesum=False, modes=["paronym"]
    )
    assert counts["paronym"] == 2
    assert any(v["type"] == "VOLUME_BELOW_THRESHOLD" and v["item"] == "paronym" for v in violations)


def test_audit_practice_shards_blank_syntax(tmp_path: Path):
    """Verify that fill-in blank modes must contain exactly 1 blank (___)."""
    shard_data = {
        "paronym": [
            {
                "paronymId": "p_bad_no_blank",
                "prompt": "Він бігає у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Різниця значень.",
            },
            {
                "paronymId": "p_bad_two_blanks",
                "prompt": "Він ___ у парку і ___ на стадіоні.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Різниця значень.",
            },
            {
                "paronymId": "p_good",
                "prompt": "Він ___ у парку щоранку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Різниця значень.",
            },
        ]
    }
    shard_file = tmp_path / "practice-paronym.A1.json"
    shard_file.write_text(json.dumps(shard_data, ensure_ascii=False), encoding="utf-8")

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    bad_items = [v["item"] for v in violations if v["type"] == "INVALID_BLANK_COUNT"]
    assert any("p_bad_no_blank" in item for item in bad_items)
    assert any("p_bad_two_blanks" in item for item in bad_items)
    assert not any("p_good" in item for item in bad_items)


def test_audit_practice_shards_options_and_homonym_rule(tmp_path: Path):
    """Verify option count >= 2, no duplicates (except homonym mode where forms are homonymous)."""
    # Paronym with duplicate options -> violation
    par_data = {
        "paronym": [
            {
                "paronymId": "p_dup",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "бігає"}],
                "distinction_gloss_uk": "Різниця значень.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    # Homonym with homonymous options -> allowed
    hom_data = {
        "homonym": [
            {
                "homonymId": "h_ok",
                "prompt": "Старенька ___ спекла пиріг.",
                "answer": "баба",
                "options": [{"label": "баба"}, {"label": "баба"}],
                "distinction_gloss_uk": "Омоніми баба.",
            }
        ]
    }
    (tmp_path / "practice-homonym.A1.json").write_text(json.dumps(hom_data, ensure_ascii=False), encoding="utf-8")

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym", "homonym"]
    )
    assert any(v["type"] == "DUPLICATE_OPTIONS" and "p_dup" in v["item"] for v in violations)
    assert not any("h_ok" in v["item"] for v in violations)


def test_audit_practice_shards_target_in_options(tmp_path: Path):
    """Verify target answer must be present in options list."""
    par_data = {
        "paronym": [
            {
                "paronymId": "p_missing_ans",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "гуляє"}, {"label": "сидить"}],
                "distinction_gloss_uk": "Різниця значень.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    assert any(v["type"] == "ANSWER_NOT_IN_OPTIONS" and "p_missing_ans" in v["item"] for v in violations)


def test_audit_practice_shards_metadata_required(tmp_path: Path):
    """Verify that pedagogical explanation metadata is required."""
    par_data = {
        "paronym": [
            {
                "paronymId": "p_no_meta",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    assert any(v["type"] == "MISSING_EXPLANATION" and "p_no_meta" in v["item"] for v in violations)


def test_audit_practice_shards_vesum_attestation(tmp_path: Path, monkeypatch):
    """Verify that target answers not attested in VESUM trigger VESUM_UNATTESTED."""
    from scripts.audit import practice_quality_gate

    par_data = {
        "paronym": [
            {
                "paronymId": "p_unattested",
                "prompt": "Він ___ у парку.",
                "answer": "неіснуючеслово",
                "options": [{"label": "неіснуючеслово"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Пояснення.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    def mock_verify(word: str, db_path=None):
        return False

    monkeypatch.setattr(practice_quality_gate, "verify_word", mock_verify)
    fake_db = tmp_path / "mock_vesum.db"
    fake_db.touch()

    _, violations = audit_practice_shards(
        shards_dir=tmp_path,
        vesum_db=fake_db,
        check_volume=False,
        verify_vesum=True,
        modes=["paronym"],
    )
    assert any(v["type"] == "VESUM_UNATTESTED" and "p_unattested" in v["item"] for v in violations)


def test_audit_card_ambiguity_mocked(tmp_path: Path):
    """Verify audit_card_ambiguity with mock TypeSafe System One responses."""
    par_data = {
        "paronym": [
            {
                "paronymId": "p_test",
                "prompt": "Вранці він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    mock_resp = {
        "model": "mock-jev",
        "answers": {
            "distractor_plausibility": {"score": 1.8, "confidence": 0.95},
            "is_unambiguous": {"noul": 0.92},
            "anti_calque_yield": {"noul": 0.10},
            "card_quality": {"choice": "pass", "confidence": 0.95},
        },
    }

    verdicts, violations = audit_card_ambiguity(
        shards_dir=tmp_path,
        sample_size=1,
        mock_response=mock_resp,
        strict_ambiguity=True,
    )
    assert len(verdicts) == 1
    assert verdicts[0]["verdict"] == "pass"
    assert len(violations) == 0


def test_audit_practice_shards_missing_vesum_db_fails_closed(tmp_path: Path):
    """Finding 3: missing VESUM database must fail closed with VESUM_DB_MISSING violation."""
    par_data = {
        "paronym": [
            {
                "paronymId": "p_1",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Пояснення.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    nonexistent_db = tmp_path / "nonexistent_vesum.db"
    _, violations = audit_practice_shards(
        shards_dir=tmp_path,
        vesum_db=nonexistent_db,
        check_volume=False,
        verify_vesum=True,
        modes=["paronym"],
    )
    assert any(v["type"] == "VESUM_DB_MISSING" for v in violations)


def test_audit_practice_shards_requires_prompt_and_options(tmp_path: Path):
    """Finding 2: required card fields (prompt, options) and answer count must be enforced."""
    # Card missing prompt
    bad_prompt_data = {
        "paronym": [
            {
                "paronymId": "p_no_prompt",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
                "distinction_gloss_uk": "Пояснення.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(
        json.dumps(bad_prompt_data, ensure_ascii=False), encoding="utf-8"
    )

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    assert any(v["type"] == "MISSING_PROMPT" and "p_no_prompt" in v["item"] for v in violations)

    # Card missing options list
    bad_opt_data = {
        "paronym": [
            {
                "paronymId": "p_no_opts",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "distinction_gloss_uk": "Пояснення.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(bad_opt_data, ensure_ascii=False), encoding="utf-8")

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    assert any(v["type"] == "MISSING_OPTIONS" and "p_no_opts" in v["item"] for v in violations)

    # Card with marked options but zero correct answers
    zero_ans_data = {
        "cloze": [
            {
                "clozeId": "c_zero_ans",
                "sentence": "Це гарне _____ речення.",
                "form": "гарне",
                "options": [
                    {"label": "гарне", "kind": "distractor"},
                    {"label": "погане", "kind": "distractor"},
                ],
                "caseRule": "правило",
            }
        ]
    }
    (tmp_path / "practice-cloze.A1.json").write_text(json.dumps(zero_ans_data, ensure_ascii=False), encoding="utf-8")

    _, violations = audit_practice_shards(shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["cloze"])
    assert any(v["type"] == "WRONG_ANSWER_COUNT" and "c_zero_ans" in v["item"] for v in violations)


def test_audit_card_ambiguity_offline_strict_fails(tmp_path: Path, monkeypatch):
    """Finding 1: offline ambiguity validation in strict mode must report unavailable and not fabricate a pass."""
    from scripts.practice import typesafe_distractor_validator

    par_data = {
        "paronym": [
            {
                "paronymId": "p_test",
                "prompt": "Вранці він ___ у парку.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(typesafe_distractor_validator, "resolve_api_key", lambda: None)
    monkeypatch.setattr(
        typesafe_distractor_validator,
        "ground_with_sources",
        lambda target, distractors, vesum_db_path=None: {
            "target": {"in_vesum": True},
            "distractors": {d: {"in_vesum": True} for d in distractors},
        },
    )

    verdicts, violations = audit_card_ambiguity(
        shards_dir=tmp_path,
        sample_size=1,
        mock_response=None,
        strict_ambiguity=True,
        client=None,
    )
    assert len(verdicts) == 1
    assert verdicts[0]["verdict"] == "unverified_offline"
    assert verdicts[0]["unambiguous_prob"] is None
    assert any(v["type"] == "AMBIGUITY_VALIDATION_UNAVAILABLE" for v in violations)


def test_audit_card_ambiguity_honors_sample_size(tmp_path: Path):
    """Finding 4: candidate sampling must collect requested sample_size cards across modes."""
    par_data = {
        "paronym": [
            {
                "paronymId": f"p_{i}",
                "prompt": f"Він ___ у парку {i}.",
                "answer": "бігає",
                "options": [{"label": "бігає"}, {"label": "біжить"}],
            }
            for i in range(10)
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(json.dumps(par_data, ensure_ascii=False), encoding="utf-8")

    mock_resp = {
        "model": "mock-jev",
        "answers": {
            "distractor_plausibility": {"score": 1.8, "confidence": 0.95},
            "is_unambiguous": {"noul": 0.92},
            "anti_calque_yield": {"noul": 0.10},
            "card_quality": {"choice": "pass", "confidence": 0.95},
        },
    }

    verdicts, violations = audit_card_ambiguity(
        shards_dir=tmp_path,
        sample_size=8,
        mock_response=mock_resp,
        strict_ambiguity=False,
    )
    assert len(verdicts) == 8
    assert len(violations) == 0


def test_audit_practice_shards_marked_answer_must_match_target(tmp_path: Path):
    """R2 Finding 1: Option marked as answer must match target form or accepted answers."""
    mismatched_card_data = {
        "paronym": [
            {
                "paronymId": "p_mismatched",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "options": [
                    {"label": "бігає", "kind": "distractor"},
                    {"label": "біжить", "kind": "answer"},
                ],
                "distinction_gloss_uk": "Пояснення.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(
        json.dumps(mismatched_card_data, ensure_ascii=False), encoding="utf-8"
    )

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    assert any(v["type"] == "MARKED_ANSWER_MISMATCH" and "p_mismatched" in v["item"] for v in violations)


def test_audit_practice_shards_empty_option_label_fails(tmp_path: Path):
    """R2 Finding 2: Missing, empty, or whitespace-only option labels must be rejected."""
    empty_label_data = {
        "paronym": [
            {
                "paronymId": "p_empty_label",
                "prompt": "Він ___ у парку.",
                "answer": "бігає",
                "options": [
                    {"label": "бігає"},
                    {"label": "   "},
                ],
                "distinction_gloss_uk": "Пояснення.",
            }
        ]
    }
    (tmp_path / "practice-paronym.A1.json").write_text(
        json.dumps(empty_label_data, ensure_ascii=False), encoding="utf-8"
    )

    _, violations = audit_practice_shards(
        shards_dir=tmp_path, check_volume=False, verify_vesum=False, modes=["paronym"]
    )
    assert any(v["type"] == "EMPTY_OPTION_LABEL" and "p_empty_label" in v["item"] for v in violations)


def test_production_practice_quality_gate_passes():
    """Verify that current repository practice datasets pass with 0 violations."""
    results = run_all_practice_audits()
    total_violations = sum(len(v) for v in results.values())
    assert total_violations == 0, f"Practice Quality Gate failed with violations: {results}"


@pytest.mark.skipif(
    not Path("data/vesum.db").exists() or not Path("site/public/lexicon/practice-index.A1.json").exists(),
    reason="Requires local data/vesum.db and generated practice shards in site/public/lexicon/",
)
def test_production_practice_shards_all_modes_gate_passes():
    """Verify that all practice shards across all modes satisfy volume thresholds and linguistic gates."""
    results = run_all_practice_audits(all_modes=True, verify_vesum=True)
    total_violations = sum(len(v) for v in results.values())
    assert total_violations == 0, f"Practice Shards Quality Gate failed with violations: {results}"

    # Assert volume thresholds
    assert results.shard_counts.get("paronym", 0) >= VOLUME_THRESHOLDS["paronym"]
    assert results.shard_counts.get("homonym", 0) >= VOLUME_THRESHOLDS["homonym"]
    assert results.shard_counts.get("heritage", 0) >= VOLUME_THRESHOLDS["heritage"]
