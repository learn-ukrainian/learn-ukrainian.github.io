from unittest.mock import patch

from scripts.verification.check_ru_morph import (
    check_russian_patterns_batch,
    get_ru_confidence,
    is_russian_pattern,
)


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


def test_word_uchbovyi():
    # учбовий: flag; no garbage pymorphy3 lemma
    res = is_russian_pattern("учбовий")
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


def test_word_zdacha():
    # здача: heuristic runs (do not VESUM-short-circuit to false/0.0)
    res = is_russian_pattern("здача")
    assert res["matches_russian"] is True
    assert res["confidence"] >= 0.7
    assert res["ukrainian_alternative"] is None


def test_word_vrach():
    # врач: stay true
    res = is_russian_pattern("врач")
    assert res["matches_russian"] is True
    assert res["russian_lemma"] == "врач"
    assert res["confidence"] == 1.0
    assert res["ukrainian_alternative"] is None


def test_word_knyha():
    # книга: stay clean negative
    res = is_russian_pattern("книга")
    assert res["matches_russian"] is False
    assert res["russian_lemma"] is None
    assert res["confidence"] == 0.0
    assert res["ukrainian_alternative"] is None


# ---------------------------------------------------------------------------
# Lexicalised safe and clean Ukrainian words
# ---------------------------------------------------------------------------


def test_lexicalised_safe_and_clean_ukrainian_words():
    # Safe lexicalised adjectives should not be flagged as calques
    for safe_word in ["квітучий", "лежачий", "блискучий"]:
        res = is_russian_pattern(safe_word)
        assert res["matches_russian"] is False, f"Expected {safe_word} to be clean negative"
        assert res["confidence"] == 0.0

    # Clean Ukrainian words in VESUM
    for clean_word in ["вода", "день", "сонце", "стіл", "привіт", "котрий"]:
        res = is_russian_pattern(clean_word)
        assert res["matches_russian"] is False, f"Expected {clean_word} to be clean negative"
        assert res["confidence"] == 0.0


def test_smoke_cases_unmocked():
    # 1. получити
    res = is_russian_pattern("получити")
    assert res["matches_russian"] is True

    # 2. здача
    res = is_russian_pattern("здача")
    assert res["matches_russian"] is True

    # 3. привіт
    res = is_russian_pattern("привіт")
    assert res["matches_russian"] is False

    # 4. котрий
    res = is_russian_pattern("котрий")
    assert res["matches_russian"] is False


@patch("scripts.verification.vesum.verify_word")
@patch("scripts.verification.check_ru_morph.get_ru_confidence")
def test_batch_reuses_preverified_vesum_results(mock_confidence, mock_verify_word):
    mock_confidence.return_value = (0.91, "выдуманный")

    results = check_russian_patterns_batch(
        ["привіт", "вигадане"],
        verified_words={"привіт"},
    )

    assert results["привіт"]["matches_russian"] is False
    assert results["вигадане"]["matches_russian"] is True
    assert results["вигадане"]["russian_lemma"] == "выдуманный"
    mock_confidence.assert_called_once_with("вигадане")
    mock_verify_word.assert_not_called()


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
