from scripts.etymology.transliterate import UK_TO_ASCII, transliterate


def test_transliteration_table_covers_all_ukrainian_letters():
    alphabet = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"

    assert len(alphabet) == 33
    assert set(alphabet) <= set(UK_TO_ASCII)
    assert transliterate(alphabet) == "abvhgdeiezhzyiiyklmnoprstufkhtschshshchiuia"


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


def test_latin_pass_through_and_mixed_scripts():
    assert transliterate("Latin Only 123") == "latin-only-123"
    assert transliterate("серце / heart") == "sertse-heart"
    assert transliterate("  дім!!!жінка  ") == "dim-zhinka"
