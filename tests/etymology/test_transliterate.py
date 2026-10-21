from scripts.etymology.transliterate import transliterate


def test_examples_and_stress_mark_stripping():
    assert transliterate("серце") == "sertse"
    assert transliterate("дім") == "dim"
    assert transliterate("жінка") == "zhinka"
    assert transliterate("абре́віатура") == "abreviatura"


def test_apostrophes_soft_sign_and_edge_cases():
    assert transliterate("") == ""
    assert transliterate("п'ять") == "piat"
    assert transliterate("пʼять") == "piat"
    assert transliterate("льон") == "lon"
