"""Tests for TypeSafe System One Semantic Firewall for Ukrainian Corpus Ingestion."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from scripts.projects.open_model_data.typesafe_corpus_firewall import (
    CorpusAction,
    TypeSafeCorpusFirewall,
    _resolve_typesafe_key,
)
from scripts.projects.open_model_data.typesafe_cyrillic_gate import (
    CurriculumAction,
    LexicalVariety,
)


def test_corpus_action_is_gate_curriculum_action() -> None:
    """Firewall must not invent a parallel disposition enum."""
    assert CorpusAction is CurriculumAction
    assert set(CurriculumAction) == {
        CurriculumAction.ADMIT_STANDARD,
        CurriculumAction.ADMIT_DIALECT_HERITAGE,
        CurriculumAction.USE_AS_ANTI_CALQUE,
        CurriculumAction.REJECT_DROP,
    }
    assert LexicalVariety.SOVIET_JARGON.value == "soviet_jargon"


def test_standard_literary_sentence_heuristic() -> None:
    """Verify that clean modern standard Ukrainian sentences are admitted to the standard corpus."""
    firewall = TypeSafeCorpusFirewall(api_key="")
    text = "Українська мова має багатовікову писемну традицію та розвинену граматичну систему."
    report = firewall.filter_sentences([text])

    assert report.total_processed == 1
    assert report.kept_standard == 1
    assert report.total_admitted == 1
    assert report.decisions[0].action == CurriculumAction.ADMIT_STANDARD
    assert report.decisions[0].lexical_variety == LexicalVariety.STANDARD_MODERN
    assert report.decisions[0].quality_score >= 3.0


def test_russian_letter_rejection_heuristic() -> None:
    """Verify that Russian alphabet characters are immediately rejected."""
    firewall = TypeSafeCorpusFirewall(api_key="")
    texts = [
        "Это предложение написано на русском языке с буквой ы.",
        "Этот текст содержит буквы э и ъ.",
    ]
    report = firewall.filter_sentences(texts)

    assert report.total_processed == 2
    assert report.dropped_russian_surzhyk == 2
    assert report.total_admitted == 0
    for d in report.decisions:
        assert d.action == CurriculumAction.REJECT_DROP
        assert d.quality_score == 0.0


def test_mixed_homoglyph_ocr_rejection_heuristic() -> None:
    """Verify that mixed Latin-Cyrillic homoglyph tokens are rejected as OCR noise."""
    firewall = TypeSafeCorpusFirewall(api_key="")
    # Word 'разом' with Latin 'a' (U+0061) and 'o' (U+006F)
    corrupted_sentence = "Ми р\u0061з\u006fm підемо до рідної школи."
    report = firewall.filter_sentences([corrupted_sentence])

    assert report.total_processed == 1
    assert report.dropped_ocr_noise == 1
    assert report.total_admitted == 0
    assert report.decisions[0].action == CurriculumAction.REJECT_DROP


def test_dialectal_and_historical_routing_heuristic() -> None:
    """Dialect and historical both admit via ADMIT_DIALECT_HERITAGE (gate taxonomy)."""
    firewall = TypeSafeCorpusFirewall(api_key="")
    dialect_text = "Файний ґазда зранку запалив ватру на високій полонині."
    historical_text = "Се половци придоша на русьскую землю, а князь володимер с полкы поиде противу."

    report = firewall.filter_sentences([dialect_text, historical_text])

    assert report.total_processed == 2
    assert report.kept_dialectal == 1
    assert report.kept_historical == 1
    assert report.total_admitted == 2
    assert report.decisions[0].action == CurriculumAction.ADMIT_DIALECT_HERITAGE
    assert report.decisions[0].lexical_variety == LexicalVariety.AUTHENTIC_DIALECT
    assert report.decisions[1].action == CurriculumAction.ADMIT_DIALECT_HERITAGE
    assert report.decisions[1].lexical_variety == LexicalVariety.HISTORICAL_LITERARY


@patch("urllib.request.urlopen")
def test_remote_batched_api_mock(mock_urlopen: MagicMock) -> None:
    """Verify remote batched API response handling with Choice, Score, and Noul."""
    resp_mock = MagicMock()
    resp_mock.read.return_value = json.dumps(
        {
            "model": "jev-latest",
            "answers": {
                "s0_route": {"type": "choice", "choice": "keep_standard_corpus", "confidence": 0.98},
                "s0_quality": {"type": "score", "score": 3.9, "confidence": 0.95},
                "s0_uncertainty": {"type": "noul", "noul": 0.05},
                "s1_route": {
                    "type": "choice",
                    "choice": "drop_russian_or_surzhyk",
                    "confidence": 0.99,
                },
                "s1_quality": {"type": "score", "score": 0.1, "confidence": 0.98},
                "s1_uncertainty": {"type": "noul", "noul": 0.02},
            },
        }
    ).encode("utf-8")

    mock_urlopen.return_value.__enter__.return_value = resp_mock

    firewall = TypeSafeCorpusFirewall(api_key="fake-key", batch_size=10)
    batch = [
        "Текст перший літературний.",
        "Текст второй с русизмами.",
    ]
    report = firewall.filter_sentences(batch)

    assert report.total_processed == 2
    assert report.kept_standard == 1
    assert report.dropped_russian_surzhyk == 1
    assert report.total_admitted == 1
    assert report.decisions[0].action == CurriculumAction.ADMIT_STANDARD
    assert report.decisions[1].action == CurriculumAction.USE_AS_ANTI_CALQUE
    assert report.decisions[0].confidence == 0.98
    assert report.decisions[1].quality_score == 0.1


@pytest.mark.skipif(not _resolve_typesafe_key(), reason="TypeSafe API key not present on host")
@pytest.mark.live_network
def test_live_typesafe_firewall_integration() -> None:
    """Integration test with live TypeSafe System One API."""
    firewall = TypeSafeCorpusFirewall()
    assert firewall.api_key != ""

    candidates = [
        "Тарас Шевченко народився у Моринцях і став символом українського відродження.",
        "Файний леґінь запалив ватру на полонині.",
        "Это сугубо русское предложение для проверки фильтрации.",
    ]
    report = firewall.filter_sentences(candidates)

    assert report.total_processed == 3
    assert report.kept_standard >= 1
    assert report.dropped_russian_surzhyk >= 1
    assert report.average_quality > 1.0


def test_russian_letter_precedence_over_markers() -> None:
    """Russian letters must reject immediately even if historical/dialect markers are present."""
    firewall = TypeSafeCorpusFirewall(api_key="")
    res = firewall.filter_sentences(["Это князь с буквой ы."])
    assert res.total_processed == 1
    assert res.dropped_russian_surzhyk == 1
    assert res.decisions[0].action == CurriculumAction.REJECT_DROP

    # Isolated single marker with ы
    res_isolated = firewall.filter_sentences(["Князь пришел с буквой ы сюда."])
    assert res_isolated.dropped_russian_surzhyk == 1
    assert res_isolated.decisions[0].action == CurriculumAction.REJECT_DROP

    # Dialect marker with ы (conflicting → anti-calque / Surzhyk bucket)
    res_dialect_conflict = firewall.filter_sentences(["Файний ґазда прийшов с буквой ы."])
    assert res_dialect_conflict.dropped_russian_surzhyk == 1
    assert res_dialect_conflict.decisions[0].action == CurriculumAction.USE_AS_ANTI_CALQUE


def test_non_ukrainian_and_numeric_noise_rejection() -> None:
    """Foreign text and numeric/punctuation noise must be dropped, not admitted as standard."""
    firewall = TypeSafeCorpusFirewall(api_key="")
    res_en = firewall.filter_sentences(["This is an English sentence."])
    assert res_en.dropped_ocr_noise == 1
    assert res_en.kept_standard == 0

    res_num = firewall.filter_sentences(["12345 67890 12345 67890."])
    assert res_num.dropped_ocr_noise == 1
    assert res_num.kept_standard == 0

    # Foreign-script letters (Greek) must count in the denominator
    res_greek = firewall.filter_sentences(["Αυτό είναι ελληνικό κείμενο για δοκιμή."])
    assert res_greek.dropped_ocr_noise == 1
    assert res_greek.kept_standard == 0


def test_verbatim_whitespace_preservation() -> None:
    """Original sentence strings with leading/trailing whitespace must be preserved verbatim."""
    firewall = TypeSafeCorpusFirewall(api_key="")
    original = "  Текст із пробілами на початку і табуляцією в кінці.\t"
    res = firewall.filter_sentences([original])
    assert res.total_processed == 1
    assert res.decisions[0].sentence == original


@patch("urllib.request.urlopen")
def test_malformed_api_response_validation(mock_urlopen: MagicMock) -> None:
    """Malformed, missing, or unknown choices in API answers must escalate to review."""
    import io

    resp_mock = io.BytesIO(b'{"answers": {"s0_route": {"choice": "invalid_choice"}}}')
    mock_urlopen.return_value.__enter__.return_value = resp_mock

    firewall = TypeSafeCorpusFirewall(api_key="fake-key", batch_size=10)
    res = firewall.filter_sentences(["Якийсь валідний текст для тестування."])
    assert res.total_processed == 1
    assert res.decisions[0].needs_human_review is True
    assert res.decisions[0].confidence == 0.0
    assert res.decisions[0].action == CurriculumAction.REJECT_DROP
    assert res.escalated_to_human == 1


@patch("urllib.request.urlopen")
def test_null_answers_container_escalates(mock_urlopen: MagicMock) -> None:
    """Null or non-object answers must not fall through to silent heuristic admission."""
    import io

    resp_mock = io.BytesIO(b'{"answers": null}')
    mock_urlopen.return_value.__enter__.return_value = resp_mock

    firewall = TypeSafeCorpusFirewall(api_key="fake-key", batch_size=10)
    res = firewall.filter_sentences(["Якийсь валідний текст для тестування."])
    assert res.total_processed == 1
    assert res.decisions[0].needs_human_review is True
    assert res.decisions[0].action == CurriculumAction.REJECT_DROP
    assert res.escalated_to_human == 1


def test_soviet_jargon_routes_to_anti_calque() -> None:
    """Soviet jargon markers map onto gate USE_AS_ANTI_CALQUE + SOVIET_JARGON variety."""
    firewall = TypeSafeCorpusFirewall(api_key="")
    text = "Колгоспниця і передовик працювали на партком у полі."
    res = firewall.filter_sentences([text])
    assert res.decisions[0].action == CurriculumAction.USE_AS_ANTI_CALQUE
    assert res.decisions[0].lexical_variety == LexicalVariety.SOVIET_JARGON
    assert res.dropped_russian_surzhyk == 1
