"""The one normalizer: conformance vectors and key invariants (design r3 §4)."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest

from scripts.lexdata import case_signal, normalize, stress
from scripts.lexdata.rule_tables import REFUSAL_CODES

VECTORS = Path(normalize.__file__).with_name("normalization_vectors.json")
CASES = json.loads(VECTORS.read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", CASES, ids=[case["note"] for case in CASES])
def test_vector(case) -> None:
    result = normalize.normalize_span(case["input"])
    assert result.surface == case["surface"]
    assert result.key_stressed == case["key_stressed"]
    assert result.key_unstressed == case["key_unstressed"]
    assert result.key_fold == case["key_fold"]
    assert result.case_signal == case["case_signal"]
    assert result.refusal_code == case["refusal_code"]
    assert list(result.norm_flags) == case["norm_flags"]
    assert [repair["proposed"] for repair in result.proposed_repairs] == case["proposed_repairs"]


def test_vectors_cover_every_normalizer_refusal_and_case_signal() -> None:
    refusals = {case["refusal_code"] for case in CASES} - {None}
    normalizer_codes = {code for code in REFUSAL_CODES if code != "truncated_source"}
    assert refusals == normalizer_codes
    assert {case["case_signal"] for case in CASES} - {None} == case_signal.CASE_SIGNALS


@pytest.mark.parametrize("case", [c for c in CASES if c["refusal_code"] is None], ids=lambda c: c["note"])
def test_accepted_keys_obey_row_rules(case) -> None:
    result = normalize.normalize_span(case["input"])
    for key in (result.key_unstressed, result.key_fold):
        decomposed = unicodedata.normalize("NFD", key)
        assert "́" not in decomposed and "̀" not in decomposed
    assert "̀" not in unicodedata.normalize("NFD", result.key_stressed)
    assert not normalize.ENTITY_RE.search(result.key_stressed)
    assert all(normalize.letter_script(c) == "cyrillic" for c in result.key_fold if c.isalpha())
    assert result.surface == unicodedata.normalize("NFC", result.surface)
    # Keys are a fixed point: normalizing a key gives the same keys back.
    again = normalize.normalize_span(result.key_stressed)
    assert (again.key_stressed, again.key_unstressed, again.key_fold) == (
        result.key_stressed, result.key_unstressed, result.key_fold)


@pytest.mark.parametrize("pair", [("Ґанок", "Ганок"), ("ірис", "ирис"), ("Єва", "Ева"), ("їжак", "іжак")])
def test_letters_are_never_folded_together(pair) -> None:
    left, right = (normalize.normalize_span(text).key_fold for text in pair)
    assert left != right


def test_refused_rows_keep_surface_and_hold_no_keys() -> None:
    result = normalize.normalize_span("Cпасибі!")
    assert result.surface == "Cпасибі!"
    assert (result.key_stressed, result.key_unstressed, result.key_fold, result.case_signal) == (None,) * 4
    assert result.proposed_repairs[0]["proposer"] == normalize.NORMALIZER_ID


def test_stress_helpers() -> None:
    assert stress.stress_is_valid("за́мок") and stress.stress_is_valid("замо́к")
    assert not stress.stress_is_valid("з́амок")
    assert stress.unstressed_key("за́мок") == "замок"
    assert stress.stressed_key("прѝві́т") == "приві́т"
    assert stress.has_stress("шу́ба") and not stress.has_stress("шуба")
