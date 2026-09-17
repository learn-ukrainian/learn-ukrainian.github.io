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


def test_standard_literary_sentence_heuristic() -> None:
    """Verify that clean modern standard Ukrainian sentences are admitted to the standard corpus."""
    firewall = TypeSafeCorpusFirewall(api_key="")
    text = "Українська мова має багатовікову писемну традицію та розвинену граматичну систему."
    report = firewall.filter_sentences([text])

    assert report.total_processed == 1
    assert report.kept_standard == 1
    assert report.total_admitted == 1
    assert report.decisions[0].action == CorpusAction.KEEP_STANDARD
    assert report.decisions[0].quality_score >= 3.0


def test_russian_letter_rejection_heuristic() -> None:
    """Verify that Russian alphabet characters are immediately rejected as Russian/Surzhyk interference."""
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
        assert d.action == CorpusAction.DROP_RUSSIAN_SURZHYK
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
    assert report.decisions[0].action == CorpusAction.DROP_OCR_NOISE


def test_dialectal_and_historical_routing_heuristic() -> None:
    """Verify routing of regional dialects and historical Old East Slavic texts."""
    firewall = TypeSafeCorpusFirewall(api_key="")
    dialect_text = "Файний ґазда зранку запалив ватру на високій полонині."
    historical_text = "Се половци придоша на русьскую землю, а князь володимер с полкы поиде противу."

    report = firewall.filter_sentences([dialect_text, historical_text])

    assert report.total_processed == 2
    assert report.kept_dialectal == 1
    assert report.kept_historical == 1
    assert report.total_admitted == 2
    assert report.decisions[0].action == CorpusAction.KEEP_DIALECTAL
    assert report.decisions[1].action == CorpusAction.KEEP_HISTORICAL


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
                "s1_route": {"type": "choice", "choice": "drop_russian_or_surzhyk", "confidence": 0.99},
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
