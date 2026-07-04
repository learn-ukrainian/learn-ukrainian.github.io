"""Pure-logic tests for the UK-writing bakeoff scorer.

The DB-backed scoring (VESUM / russian-shadow) is covered by the underlying
modules' own tests; here we lock the scorer's own logic: section splitting,
apostrophe normalization (the false-russicism bug), and junk-token filtering.
"""

from scripts.audit.probe_uk_writing_score import (
    _APOS_TRANS,
    _is_word,
    latin_ratio,
    split_sections,
)


def test_split_sections_by_heading():
    text = "## SECTION 1\nfoo\n## SECTION 2\nbar baz\n### SECTION 3\nqux"
    parts = split_sections(text)
    assert parts == {1: "foo", 2: "bar baz", 3: "qux"}


def test_split_sections_missing_returns_partial():
    parts = split_sections("## SECTION 1\nonly one")
    assert set(parts) == {1}


def test_apostrophe_normalization_maps_typographic_to_ascii():
    # U+2019 ’ and U+02BC ʼ must both normalize to ASCII U+0027 so VESUM matches.
    assert "з’являються".translate(_APOS_TRANS) == "з'являються"
    assert "кавʼярня".translate(_APOS_TRANS) == "кав'ярня"
    # ASCII apostrophe is untouched (idempotent).
    assert "кав'ярня".translate(_APOS_TRANS) == "кав'ярня"


def test_is_word_rejects_vowelless_junk():
    assert _is_word("веснянки") is True
    assert _is_word("з'являються") is True
    assert _is_word("---") is False  # markdown rule — the false-flag class
    assert _is_word("№") is False


def test_latin_ratio_counts_scripts():
    latin, cyr, ratio = latin_ratio("кава (coffee) — смачна")
    assert latin == 1  # "coffee"
    assert cyr == 2  # "кава", "смачна"
    assert abs(ratio - 1 / 3) < 1e-6
