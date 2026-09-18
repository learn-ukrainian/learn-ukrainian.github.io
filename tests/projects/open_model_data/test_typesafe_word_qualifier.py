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


def test_vesum_tag_markers_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test VESUM tag marker parsing for nonstandard, obscene, and variant forms."""
    qualifier = TypeSafeWordQualifier(api_key=None)

    class MockCursor:
        def __init__(self, tag_val: str):
            self.tag_val = tag_val

        def execute(self, query: str, params: tuple) -> None:
            pass

        def fetchall(self) -> list[tuple[str, str]]:
            return [("noun", self.tag_val)]

    class MockConn:
        def __init__(self, tag_val: str):
            self.tag_val = tag_val

        def cursor(self) -> MockCursor:
            return MockCursor(self.tag_val)

    # 1. Obscene tag -> PEJORATIVE_SLUR
    monkeypatch.setattr(qualifier, "_get_vesum_conn", lambda: MockConn("noun:m:v_naz:obsc"))
    res_obsc = qualifier._heuristic_qualify("лайкаслово")
    assert res_obsc.stratum == LexicalStratum.PEJORATIVE_SLUR
    assert res_obsc.needs_verification is True

    # 2. Nonstandard 'subst' tag -> CALQUE_RUSSIANISM
    monkeypatch.setattr(qualifier, "_get_vesum_conn", lambda: MockConn("noun:n:v_naz:subst"))
    res_subst = qualifier._heuristic_qualify("суржикслово")
    assert res_subst.stratum == LexicalStratum.CALQUE_RUSSIANISM
    assert res_subst.needs_verification is True

    # 3. Orthographic variant 'alt' tag -> STANDARD_LITERARY with priority 1.5
    monkeypatch.setattr(qualifier, "_get_vesum_conn", lambda: MockConn("noun:f:v_naz:alt"))
    res_alt = qualifier._heuristic_qualify("варіантслово")
    assert res_alt.stratum == LexicalStratum.STANDARD_LITERARY
    assert res_alt.pedagogical_priority == 1.5
    assert res_alt.needs_verification is False


def test_vesum_multi_analysis_order_independence(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that multiple VESUM analyses flag nonstandard usage regardless of database row order."""
    qualifier = TypeSafeWordQualifier(api_key=None)

    class MultiMockCursor:
        def __init__(self, rows: list[tuple[str, str]]):
            self.rows = rows

        def execute(self, query: str, params: tuple) -> None:
            pass

        def fetchall(self) -> list[tuple[str, str]]:
            return self.rows

    class MultiMockConn:
        def __init__(self, rows: list[tuple[str, str]]):
            self.rows = rows

        def cursor(self) -> MultiMockCursor:
            return MultiMockCursor(self.rows)

    clean_row = ("noun", "noun:m:v_naz")
    obsc_row = ("noun", "noun:m:v_naz:obsc")

    # Order 1: Clean row first, obscene row second
    monkeypatch.setattr(qualifier, "_get_vesum_conn", lambda: MultiMockConn([clean_row, obsc_row]))
    res1 = qualifier._heuristic_qualify("тестслово")
    assert res1.stratum == LexicalStratum.PEJORATIVE_SLUR
    assert res1.needs_verification is True

    # Order 2: Obscene row first, clean row second
    monkeypatch.setattr(qualifier, "_get_vesum_conn", lambda: MultiMockConn([obsc_row, clean_row]))
    res2 = qualifier._heuristic_qualify("тестслово")
    assert res2.stratum == LexicalStratum.PEJORATIVE_SLUR
    assert res2.needs_verification is True


@patch("urllib.request.urlopen")
def test_invalid_api_response_validation(mock_urlopen: MagicMock) -> None:
    """Invalid choices, missing answers, or out-of-bounds metrics must not be auto-accepted."""
    import io
    # 1. Invalid choice label with high confidence
    resp_mock = io.BytesIO(b'{"answers": {"w0_stratum": {"choice": "INVALID", "confidence": 0.99}}}')
    mock_urlopen.return_value.__enter__.return_value = resp_mock

    qualifier = TypeSafeWordQualifier(api_key="fake-key", batch_size=10)
    report = qualifier.qualify_words(["перемога"])
    assert report.total_processed == 1
    assert report.qualifications[0].needs_verification is True
    assert report.qualifications[0].confidence == 0.0

    # 2. Out of bounds metric
    resp_mock2 = io.BytesIO(
        b'{"answers": {"w0_stratum": {"choice": "standard_literary", "confidence": 1.5}, '
        b'"w0_shadow": {"noul": 0.1}, "w0_priority": {"score": 3.0}, "w0_ocr": {"noul": 0.0}}}'
    )
    mock_urlopen.return_value.__enter__.return_value = resp_mock2
    report2 = qualifier.qualify_words(["перемога"])
    assert report2.total_processed == 1
    assert report2.qualifications[0].needs_verification is True
    assert report2.qualifications[0].confidence == 0.0

    # 3. Boolean metric (confidence: true) must be rejected, not converted to 1.0
    resp_mock3 = io.BytesIO(
        b'{"answers": {"w0_stratum": {"choice": "standard_literary", "confidence": true}, '
        b'"w0_shadow": {"noul": 0.1}, "w0_priority": {"score": 3.0}, "w0_ocr": {"noul": 0.0}}}'
    )
    mock_urlopen.return_value.__enter__.return_value = resp_mock3
    report3 = qualifier.qualify_words(["перемога"])
    assert report3.qualifications[0].needs_verification is True
    assert report3.qualifications[0].confidence == 0.0

    # 4. answers: null
    resp_mock4 = io.BytesIO(b'{"answers": null}')
    mock_urlopen.return_value.__enter__.return_value = resp_mock4
    report4 = qualifier.qualify_words(["і"])
    assert report4.qualifications[0].needs_verification is True
    assert report4.qualifications[0].confidence == 0.0

    # 5. choice is list: []
    resp_mock5 = io.BytesIO(b'{"answers": {"w0_stratum": {"choice": [], "confidence": 0.99}}}')
    mock_urlopen.return_value.__enter__.return_value = resp_mock5
    report5 = qualifier.qualify_words(["і"])
    assert report5.qualifications[0].needs_verification is True
    assert report5.qualifications[0].confidence == 0.0

    # 6. Remote network error on stopword enforces needs_verification on fallback
    mock_urlopen.side_effect = OSError("API network timeout")
    report6 = qualifier.qualify_words(["і"])
    assert report6.qualifications[0].needs_verification is True
    assert "Remote API failed" in report6.qualifications[0].reason
