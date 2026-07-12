"""Regression tests for MiyKlas lexical-relation candidate parsing."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.lexicon.miyklas_relation_miner import clean_candidate_records, parse_relation_term

_CANDIDATES_PATH = Path("data/lexicon/relation_candidates_miyklas.json")


def test_strips_only_complete_dotted_qualifier_tokens() -> None:
    assert parse_relation_term("заст. заступник") == "заступник"
    assert parse_relation_term("зневаж. віршомаз") == "віршомаз"
    assert parse_relation_term("мат. тіло") == "тіло"


def test_never_chops_substrings_that_match_qualifier_labels() -> None:
    assert parse_relation_term("заступник") == "заступник"
    assert parse_relation_term("істинно") == "істинно"
    assert parse_relation_term("обручка") == "обручка"
    assert parse_relation_term("сильний") == "сильний"
    assert parse_relation_term("відгадка") == "відгадка"
    assert parse_relation_term("розгадка") == "розгадка"


def test_rejects_qualifier_labels_and_multiword_phrases() -> None:
    for label in ("розм", "заст", "поб", "суч", "тех", "мат", "зневаж", "спрт"):
        assert parse_relation_term(label) is None
    assert parse_relation_term("поб. здоровий глузд") is None
    for malformed in ("упник", "инно", "учка", "ьний", "адка"):
        assert parse_relation_term(malformed) is None


def test_clean_candidate_records_removes_labels_without_losing_valid_terms() -> None:
    records = [
        {"word_a": "фігура", "word_b": "мат"},
        {"word_a": "адвокат", "word_b": "упник"},
        {"word_a": "віла", "word_b": "вілла"},
        {"word_a": "зять", "word_b": "взять"},
    ]

    assert clean_candidate_records(records) == [
        {"word_a": "віла", "word_b": "вілла"},
        {"word_a": "зять", "word_b": "взять"},
    ]


def test_cleaned_artifact_has_no_known_label_or_chopped_headwords() -> None:
    candidates = json.loads(_CANDIDATES_PATH.read_text(encoding="utf-8"))
    forbidden = {
        "мат",
        "поб",
        "суч",
        "тех",
        "упник",
        "адка",
        "инно",
        "учка",
        "ьний",
    }

    assert not any(
        {candidate["word_a"], candidate["word_b"]} & forbidden for candidate in candidates
    )
    assert any(
        {candidate["word_a"], candidate["word_b"]} == {"віла", "вілла"}
        for candidate in candidates
    )
    assert any(
        {candidate["word_a"], candidate["word_b"]} == {"зять", "взять"}
        for candidate in candidates
    )
