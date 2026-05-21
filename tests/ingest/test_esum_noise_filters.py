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

    # Rule 2: Mixed-script — Basic-Latin letters in a Cyrillic lemma
    assert _is_sane_lemma("і£і") is False
    assert _is_sane_lemma("pгазкас") is False  # Latin 'p'
    assert _is_sane_lemma("p") is False  # Latin p
    assert _is_sane_lemma("abc") is False
    # Mixed cases where Latin look-alikes leak in
    assert _is_sane_lemma("нaдія") is False  # Latin 'a'
    assert _is_sane_lemma("надіi") is False  # Latin 'i'

    # Rule 3: Multiple digits / non-trailing digit
    assert _is_sane_lemma("к88") is False
    assert _is_sane_lemma("з8оіуь") is False
    assert _is_sane_lemma("8надія") is False  # leading digit

    # Rule 5: Garbage headwords (exact-match set)
    assert _is_sane_lemma("видавництво") is False
    assert _is_sane_lemma("тов") is False
    assert _is_sane_lemma("ргазкас") is False


def test_is_sane_lemma_positive_cases():
    # Plain lowercase Ukrainian
    assert _is_sane_lemma("береза") is True
    assert _is_sane_lemma("голова") is True
    assert _is_sane_lemma("надія") is True

    # Homonym markers 1-9 (ESUM uses up through ~9; PR2195 only allowed 1-3)
    assert _is_sane_lemma("надія1") is True
    assert _is_sane_lemma("баба4") is True
    assert _is_sane_lemma("банка4") is True
    assert _is_sane_lemma("байда5") is True
    assert _is_sane_lemma("бабка8") is True
    assert _is_sane_lemma("бабка7") is True

    # Stress marks (combining acute U+0301) — ESUM uses these extensively
    assert _is_sane_lemma("сму́шок") is True  # сму́шок
    assert _is_sane_lemma("береза́") is True

    # Uppercase Cyrillic — some ESUM lemmas are proper-noun-derived
    assert _is_sane_lemma("Іван") is True
    assert _is_sane_lemma("Аякс") is True

    # Hyphens, apostrophes (Ukrainian apostrophe ')
    assert _is_sane_lemma("а-") is True
    assert _is_sane_lemma("ім'я") is True
    assert _is_sane_lemma("надія-")  is True


def test_is_pure_bibliography():
    bib_noise = "СУМ 9, 763; Бупр. Ш 222; Фасмер Ш 776; Преобр. П 397;"
    assert _is_pure_bibliography(bib_noise) is True

    real_entry = "береза; -- р. береза, бр. бяроза, др. береза; -- псл. berza. -- СУМ 1, 150."
    assert _is_pure_bibliography(real_entry) is False


def test_strip_front_and_back_matter_djvutxt_unchanged():
    """djvutxt path: trim front matter on BODY_START_RE, back matter on BODY_END_RE."""
    lines = [
        "front matter line 1",
        "front matter line 2",
        "а 1 (опис; — псл. *а)",  # BODY_START_RE matches
        "баба 1 (mother)",
        "АКАДЕМИЯ НАУК УКРАИНСКОЙ ССР",  # BODY_END_RE matches
        "colophon stuff",
    ]
    stripped = _strip_front_and_back_matter(lines)
    assert len(stripped) == 2
    assert any("а 1 (" in line for line in stripped)
    assert any("баба" in line for line in stripped)
    assert not any("АКАДЕМИЯ" in line for line in stripped)


def test_strip_front_and_back_matter_textpdf_passes_through():
    """text-pdf path: no aggressive colophon strip; rely on lemma sanity gate
    + bibliography detector downstream. Earlier PR #2195 over-truncated by 50-67%."""
    lines = [
        "у1 ( ... )",
        "формат page-header noise should not truncate",  # 'формат' is a generic word
        "убавляти ( ... )",
        "тираж of an etymology body line",  # 'тираж' is a generic word
        "видавництво АН України",  # actually colophon-shaped, but only Layer 2 (sanity gate) rejects
    ]
    stripped = _strip_front_and_back_matter(lines)
    # All 5 lines preserved — colophon-like words inside the body must NOT trigger truncation.
    # The lemma `видавництво` is rejected downstream by _is_sane_lemma, not by this step.
    assert len(stripped) == 5
