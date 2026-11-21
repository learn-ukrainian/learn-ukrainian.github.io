
import asyncio
import sqlite3
from contextlib import closing

import pytest

from scripts.verification.check_ru_morph import (
    _morph_ru,
    check_russian_patterns_batch,
    get_ru_confidence,
    is_russian_pattern,
)
from tests.mcp.sources_golden_set import load_server


@pytest.fixture(autouse=True)
def healthy_vesum(empty_vesum_db):
    attested_words = (
        "минулий", "сплячий", "сидячий", "стоячий", "получити", "здача", "книга",
        "вода", "день", "сонце", "стіл", "привіт", "котрий",
    )
    with closing(sqlite3.connect(empty_vesum_db)) as conn:
        conn.executemany(
            "INSERT INTO forms VALUES (?, ?, '', '')",
            [(word, word) for word in attested_words],
        )
        conn.commit()


@pytest.fixture
def sources_with_malformed_vesum(tmp_path, monkeypatch):
    vesum_db = tmp_path / "vesum.db"
    vesum_db.write_bytes(b"not a SQLite database")
    monkeypatch.setenv("LU_VESUM_DB", str(vesum_db))
    monkeypatch.setenv("LU_SOURCES_DB", str(tmp_path / "absent-sources.db"))
    monkeypatch.setattr("scripts.wiki.sources_db._conn", None)
    return load_server()


def test_check_russian_shadow_reports_database_unavailable_on_malformed_vesum(sources_with_malformed_vesum):
    server = sources_with_malformed_vesum
    params = server.CallToolRequestParams(name="check_russian_shadow", arguments={"word": "спасибо"})
    result = asyncio.run(server._on_call_tool(None, params))

    assert result.is_error is True
    assert result.structured_content["status"] == "error"
    assert result.structured_content["error_code"] == "database_unavailable"
    assert result.structured_content["database"] == "vesum.db"
    assert "matches_russian" not in result.structured_content


def test_verify_stress_reports_database_unavailable_on_malformed_vesum(sources_with_malformed_vesum):
    server = sources_with_malformed_vesum
    params = server.CallToolRequestParams(name="verify_stress", arguments={"word": "село"})
    result = asyncio.run(server._on_call_tool(None, params))

    assert result.is_error is True
    assert result.structured_content["status"] == "error"
    assert result.structured_content["error_code"] == "database_unavailable"
    assert result.structured_content["database"] == "vesum.db"
    assert "result" not in result.structured_content


def test_get_ru_confidence():
    # 'получити' -> Maps to Russian word 'получить' -> 1.0
    conf, lemma = get_ru_confidence("получити")
    assert conf == 1.0
    assert lemma == "получить"

    # 'здача' -> Maps via DictionaryAnalyzer for Russian 'дача'
    conf, lemma = get_ru_confidence("здача")
    assert conf > 0.9

    # 'привіт' -> clean UK, FakeDictionary fallback without inventing fake lemma
    conf, lemma = get_ru_confidence("привіт")
    assert conf < 0.5
    assert lemma is None

    # 'слідуючий' / 'учбовий' -> FakeDictionary fallback without inventing fake lemma
    _, lemma_slid = get_ru_confidence("слідуючий")
    assert lemma_slid is None
    _, lemma_uch = get_ru_confidence("учбовий")
    assert lemma_uch is None


# ---------------------------------------------------------------------------
# Live fail table tests (Issue #7027)
# ---------------------------------------------------------------------------


def test_word_sliduiuchyi():
    # слідуючий: flag; no fake RU lemma
    res = is_russian_pattern("слідуючий")
    assert res["matches_russian"] is True
    assert res["russian_lemma"] is None
    assert res["confidence"] >= 0.7
    assert res["ukrainian_alternative"] is None


def test_word_poluchyty():
    # получити: heuristic runs (do not VESUM-short-circuit to false/0.0)
    res = is_russian_pattern("получити")
    assert res["matches_russian"] is True
    assert res["russian_lemma"] == "получить"
    assert res["confidence"] == 1.0
    assert res["ukrainian_alternative"] is None


# ---------------------------------------------------------------------------
# VESUM-attested actv/Dist participles must stay clean (Issue #7039)
# ---------------------------------------------------------------------------


def test_vesum_attested_permanent_quality_adjectives_stay_clean():
    # минулий/сплячий/сидячий/стоячий are lexicalised VESUM adjectives that
    # pymorphy3's uk parser also tags actv/Dist on — the actv/Dist heuristic
    # must not override a real VESUM attestation.
    for word in ["минулий", "сплячий", "сидячий", "стоячий"]:
        res = is_russian_pattern(word)
        assert res["matches_russian"] is False, f"Expected {word} to be clean negative"
        assert res["russian_lemma"] is None
        assert res["confidence"] == 0.0


def test_documented_calques_still_flag_when_vesum_has_no_match():
    # Real calques (not VESUM-attested) must still flag despite the VESUM gate
    # on the actv/Dist heuristic.
    for word in ["слідуючий", "учбовий"]:
        res = is_russian_pattern(word)
        assert res["matches_russian"] is True, f"Expected {word} to flag"
        assert res["russian_lemma"] is None
        assert res["confidence"] >= 0.7


def test_flagged_words_never_return_an_unverified_lemma():
    # Any word this module returns a russian_lemma for must be a genuinely
    # known RU dictionary word, never an invented DictionaryAnalyzer guess.
    words = [
        "получити", "здача", "врач", "привіт", "книга",
        "слідуючий", "учбовий", "минулий", "сплячий", "сидячий", "стоячий",
    ]
    for word in words:
        res = is_russian_pattern(word)
        lemma = res["russian_lemma"]
        if lemma is not None:
            assert _morph_ru.word_is_known(lemma), (
                f"{word} returned unverified lemma {lemma!r}"
            )


# ---------------------------------------------------------------------------
# Lexicalised safe and clean Ukrainian words
# ---------------------------------------------------------------------------


def test_lexicalised_safe_and_clean_ukrainian_words():
    # Safe lexicalised adjectives should not be flagged as calques
    for safe_word in ["квітучий", "лежачий", "блискучий", "ріжучий", "керуючий"]:
        res = is_russian_pattern(safe_word)
        assert res["matches_russian"] is False, f"Expected {safe_word} to be clean negative"
        assert res["confidence"] == 0.0

    # Clean Ukrainian words in VESUM
    for clean_word in ["вода", "день", "сонце", "стіл", "привіт", "котрий"]:
        res = is_russian_pattern(clean_word)
        assert res["matches_russian"] is False, f"Expected {clean_word} to be clean negative"
        assert res["confidence"] == 0.0


def test_batch_handles_live_fail_table():
    batch_results = check_russian_patterns_batch(
        ["слідуючий", "учбовий", "получити", "здача", "врач", "книга"],
        verified_words={"получити", "здача", "книга"},
    )
    assert batch_results["слідуючий"]["matches_russian"] is True
    assert batch_results["слідуючий"]["russian_lemma"] is None

    assert batch_results["учбовий"]["matches_russian"] is True
    assert batch_results["учбовий"]["russian_lemma"] is None

    assert batch_results["получити"]["matches_russian"] is True
    assert batch_results["получити"]["russian_lemma"] == "получить"

    assert batch_results["здача"]["matches_russian"] is True
    assert batch_results["здача"]["confidence"] >= 0.7

    assert batch_results["врач"]["matches_russian"] is True
    assert batch_results["врач"]["russian_lemma"] == "врач"

    assert batch_results["книга"]["matches_russian"] is False
    assert batch_results["книга"]["confidence"] == 0.0
