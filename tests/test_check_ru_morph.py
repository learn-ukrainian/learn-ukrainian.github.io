from unittest.mock import patch

from scripts.verification.check_ru_morph import get_ru_confidence, is_russian_pattern


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

@patch("scripts.rag.query.verify_word")
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
