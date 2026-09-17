"""Tests for TypeSafe System One Multi-Axis Lexicon Qualification Engine (#8181)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from scripts.projects.open_model_data.typesafe_word_qualifier import (
    LexicalStratum,
    TypeSafeWordQualifier,
    _resolve_typesafe_key,
)


def test_standard_literary_words_heuristic() -> None:
    """Verify that standard literary Ukrainian words are correctly qualified."""
    qualifier = TypeSafeWordQualifier(api_key="")
    words = ["мова", "книжка", "сонце", "думка"]
    report = qualifier.qualify_words(words)

    assert report.total_processed == 4
    assert report.standard_literary == 4
    assert report.average_priority >= 2.0
    for q in report.qualifications:
        assert q.stratum == LexicalStratum.STANDARD_LITERARY
        assert q.russian_shadow <= 0.15
        assert q.ocr_junk == 0.0


def test_russian_characters_calque_rejection() -> None:
    """Verify that words with Russian-only characters (ы, э, ъ, ё) are flagged as calques."""
    qualifier = TypeSafeWordQualifier(api_key="")
    words = ["мыло", "это", "объект"]
    report = qualifier.qualify_words(words)

    assert report.total_processed == 3
    assert report.calque_russianism == 3
    for q in report.qualifications:
        assert q.stratum == LexicalStratum.CALQUE_RUSSIANISM
        assert q.russian_shadow >= 0.95
        assert q.needs_verification is True
        assert q.verification_route == "style_guide_review"


def test_known_calques_routing() -> None:
    """Verify that documented Russian calques and Sovietisms are identified and routed for review."""
    qualifier = TypeSafeWordQualifier(api_key="")
    calques = ["мероприємство", "празнувати", "слідуючий", "взнос"]
    report = qualifier.qualify_words(calques)

    assert report.total_processed == 4
    assert report.calque_russianism == 4
    for q in report.qualifications:
        assert q.stratum == LexicalStratum.CALQUE_RUSSIANISM
        assert q.russian_shadow >= 0.85
        assert q.needs_verification is True
        assert q.verification_route == "style_guide_review"


def test_dialectal_and_archaism_routing() -> None:
    """Verify routing of regional dialect words and historic archaisms."""
    qualifier = TypeSafeWordQualifier(api_key="")
    words = ["файний", "ґазда", "ватра", "бяше", "рече", "кнѧз"]
    report = qualifier.qualify_words(words)

    assert report.total_processed == 6
    assert report.dialectal == 3
    assert report.archaism == 3
    assert report.calque_russianism == 0


def test_stopwords_and_cultural_gems_priority() -> None:
    """Verify pedagogical priority scaling: stopwords (0.0) vs cultural heritage gems (4.0)."""
    qualifier = TypeSafeWordQualifier(api_key="")
    words = ["і", "та", "на", "воля", "незалежність", "соборність", "вишиванка"]
    report = qualifier.qualify_words(words)

    stopwords_q = [q for q in report.qualifications if q.word in {"і", "та", "на"}]
    for q in stopwords_q:
        assert q.pedagogical_priority == 0.0

    gems_q = [q for q in report.qualifications if q.word in {"воля", "незалежність", "соборність", "вишиванка"}]
    for q in gems_q:
        assert q.pedagogical_priority == 4.0
        assert q.stratum == LexicalStratum.STANDARD_LITERARY


def test_mixed_homoglyph_ocr_rejection() -> None:
    """Verify that mixed Latin-Cyrillic homoglyphs are flagged as OCR junk."""
    qualifier = TypeSafeWordQualifier(api_key="")
    # 'міст\u006f' with Latin 'o'
    word = "міст\u006f"
    report = qualifier.qualify_words([word])

    assert report.total_processed == 1
    assert report.ocr_junk_count == 1
    q = report.qualifications[0]
    assert q.ocr_junk >= 0.90
    assert q.needs_verification is True
    assert q.verification_route == "ocr_filter"


@patch("urllib.request.urlopen")
def test_remote_batched_api_mock(mock_urlopen: MagicMock) -> None:
    """Verify remote batched API response handling with Choice, Score, and Noul."""
    resp_mock = MagicMock()
    resp_mock.read.return_value = json.dumps(
        {
            "model": "jev-latest",
            "answers": {
                "w0_stratum": {"type": "choice", "choice": "standard_literary", "confidence": 0.97},
                "w0_shadow": {"type": "noul", "noul": 0.03},
                "w0_priority": {"type": "score", "score": 3.8, "confidence": 0.94},
                "w0_ocr": {"type": "noul", "noul": 0.01},
                "w1_stratum": {"type": "choice", "choice": "calque_russianism", "confidence": 0.95},
                "w1_shadow": {"type": "noul", "noul": 0.88},
                "w1_priority": {"type": "score", "score": 0.5, "confidence": 0.90},
                "w1_ocr": {"type": "noul", "noul": 0.02},
            },
        }
    ).encode("utf-8")

    mock_urlopen.return_value.__enter__.return_value = resp_mock

    qualifier = TypeSafeWordQualifier(api_key="fake-key", batch_size=10)
    report = qualifier.qualify_words(["перемога", "мероприємство"])

    assert report.total_processed == 2
    assert report.standard_literary == 1
    assert report.calque_russianism == 1
    assert report.qualifications[0].needs_verification is False
    assert report.qualifications[1].needs_verification is True
    assert report.qualifications[1].verification_route == "style_guide_review"


@pytest.mark.live_network
def test_live_typesafe_api_lexicon_qualification() -> None:
    """Live network test against TypeSafe System One API if key is available."""
    api_key = _resolve_typesafe_key()
    if not api_key:
        pytest.skip("TypeSafe API key not found; skipping live API test")

    qualifier = TypeSafeWordQualifier(api_key=api_key, batch_size=15)
    candidates = [
        "гідність",
        "файно",
        "мероприємство",
        "інформатика",
        "і",
    ]
    report = qualifier.qualify_words(candidates)

    assert report.total_processed == 5
    assert len(report.qualifications) == 5
    assert report.elapsed_seconds > 0

    word_map = {q.word: q for q in report.qualifications}
    assert word_map["гідність"].pedagogical_priority >= 2.5
    assert word_map["мероприємство"].russian_shadow >= 0.40
    assert word_map["і"].pedagogical_priority <= 1.0
