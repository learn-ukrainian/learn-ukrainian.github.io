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

    # 'привіт' -> clean UK, FakeDictionary or low score
    conf, lemma = get_ru_confidence("привіт")
    assert conf < 0.5

@patch("scripts.verification.vesum.verify_word")
def test_smoke_cases(mock_verify_word):
    # VESUM mock for smoke cases
    def mock_vesum(word):
        if word in ["получити", "здача"]:
            return [] # Missing -> not real UK word
        return [{"lemma": word, "pos": "noun", "tags": ""}]

    mock_verify_word.side_effect = mock_vesum

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
