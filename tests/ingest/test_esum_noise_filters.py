from scripts.ingest.esum_ingest import _is_pure_bibliography, _is_sane_lemma, _strip_front_and_back_matter


def test_is_sane_lemma_rejections():
    # Rule 1: Single char
    assert _is_sane_lemma("і") is False
    assert _is_sane_lemma("п") is False
    assert _is_sane_lemma("т") is False

    # Rule 4: Russian-only headwords
    assert _is_sane_lemma("последний") is False
    assert _is_sane_lemma("который") is False
    assert _is_sane_lemma("этот") is False
    assert _is_sane_lemma("тот") is False

    # Rule 2: Mixed-script / Latin / Non-Ukrainian characters
    assert _is_sane_lemma("і£і") is False
    assert _is_sane_lemma("pгазкас") is False  # Latin 'p'
    assert _is_sane_lemma("p") is False  # Latin p
    assert _is_sane_lemma("abc") is False
    # Mixed cases where we explicitly use Latin look-alikes
    assert _is_sane_lemma("нaдія") is False  # Latin 'a'
    assert _is_sane_lemma("надіi") is False  # Latin 'i'

    # Rule 3: Digits other than trailing homonym
    assert _is_sane_lemma("к88") is False
    assert _is_sane_lemma("з8оіуь") is False

    # Rule 5: Garbage headwords
    assert _is_sane_lemma("видавництво") is False
    assert _is_sane_lemma("тов") is False
    assert _is_sane_lemma("ргазкас") is False

    # Positive cases
    assert _is_sane_lemma("береза") is True
    assert _is_sane_lemma("голова") is True
    assert _is_sane_lemma("надія") is True
    assert _is_sane_lemma("надія1") is True  # No space, homonym marker 1


def test_is_pure_bibliography():
    bib_noise = "СУМ 9, 763; Бупр. Ш 222; Фасмер Ш 776; Преобр. П 397;"
    assert _is_pure_bibliography(bib_noise) is True

    real_entry = "береза; -- р. береза, бр. бяроза, др. береза; -- псл. berza. -- СУМ 1, 150."
    assert _is_pure_bibliography(real_entry) is False


def test_strip_backmatter_textpdf():
    lines = [
        "надія ( ( ... ) )",
        "надоба ( ( ... ) )",
        "видавництво АН України",
        "123",
        "456",
        "789",
        "000",
    ]
    # Standard BODY_END_RE doesn't match these
    stripped = _strip_front_and_back_matter(lines, source_format="text-pdf")
    assert len(stripped) == 2
    assert "надія" in stripped[0]
    assert "надоба" in stripped[1]
    assert "видавництво" not in "".join(stripped)


def test_strip_backmatter_djvutxt_no_regression():
    lines = [
        "а 1 (",
        "баба",
        "АКАДЕМИЯ НАУК УКРАИНСКОЙ ССР",
        "colophon stuff",
    ]
    stripped = _strip_front_and_back_matter(lines, source_format="djvutxt")
    assert len(stripped) == 2
    assert "а 1 (" in stripped
    assert "баба" in stripped
