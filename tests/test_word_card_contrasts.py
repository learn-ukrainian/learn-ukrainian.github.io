"""Synthetic mechanics only; these fixtures make no Ukrainian language claims."""

from copy import deepcopy

import pytest

from scripts.atlas.word_card_contrasts import validate_card_contrasts
from scripts.atlas.word_card_resolver import public_projection
from scripts.open_dataset.russification import QuarantineError
from tests.test_word_card_resolver import assertion


@pytest.fixture
def contrast_card():
    norm = assertion("sum20", "G-SUM20", 1, "definition_uk", "Modern correction.", "ws_x", "sense")
    imposed = assertion("sum11", "G-SUM11", 0, "russification_exposed", "pair:fixture", "ws_x", "sense")
    citation_keys = ("source_id", "snapshot_id", "locator")
    pair = {
        "pair_id": "pair:fixture", "sense_id": "ws_x", "distortion_type": "synthetic_fixture",
        "imposed": {
            "text": "Synthetic imposed quotation.",
            "citation": {**{k: imposed[k] for k in citation_keys}, "attribution": "Historical fixture"},
            "sovietization_risk": 1, "sovietization_keywords": ["synthetic"],
        },
        "norm": {
            "text": norm["value"], "assertion_id": norm["assertion_id"],
            "citation": {**{k: norm[k] for k in citation_keys}, "attribution": "Modern fixture"},
        },
    }
    imposed["value"] = {"red_flag": True, "soviet_colonization_context": pair}
    return {"card_id": "wc_x", "senses": [{"sense_id": "ws_x", "fields": {}}],
            "links": [], "assertions": [norm, imposed], "build": {}}


def test_public_projection_keeps_complete_flagged_pair_and_never_detaches_text(contrast_card):
    before = deepcopy(contrast_card)
    projected = public_projection(contrast_card)
    note = projected["assertions"][1]["value"]
    assert note == before["assertions"][1]["value"]
    assert projected["senses"][0]["fields"]["russification_exposed"]["values"][0]["value_norm"] == "pair:fixture"
    assert validate_card_contrasts(projected) == 1
    assert contrast_card == before


@pytest.mark.parametrize("source", ["sum20", "vts_busel_slovnyk_me", "antonenko_style_guide"])
def test_modern_comparator_sources(contrast_card, source):
    norm, imposed = contrast_card["assertions"]
    norm["source_id"] = norm["licence_ref"]["register_source_id"] = source
    imposed["value"]["soviet_colonization_context"]["norm"]["citation"]["source_id"] = source
    assert validate_card_contrasts(public_projection(contrast_card)) == 1


@pytest.mark.parametrize("value", ["bare Soviet quotation", {}, {"red_flag": False},
                                  {"red_flag": 1, "soviet_colonization_context": {}}])
def test_projection_refuses_unpaired_or_unflagged_text(contrast_card, value):
    contrast_card["assertions"][1]["value"] = value
    with pytest.raises(QuarantineError, match="red_flagged_contrast_required"):
        public_projection(contrast_card)


@pytest.mark.parametrize("side,key", [("norm", "citation"), ("norm", "text"), ("norm", "assertion_id"),
                                      ("imposed", "citation"), ("imposed", "text")])
def test_projection_requires_both_complete_sides(contrast_card, side, key):
    del contrast_card["assertions"][1]["value"]["soviet_colonization_context"][side][key]
    with pytest.raises(QuarantineError):
        public_projection(contrast_card)


@pytest.mark.parametrize("key,value", [("subject", {"kind": "card", "id": "wc_x"}),
                                      ("source_id", "sum20"), ("snapshot_id", "other"),
                                      ("locator", "other"), ("value_norm", "Synthetic imposed quotation.")])
def test_imposed_citation_and_sense_must_bind_to_assertion(contrast_card, key, value):
    contrast_card["assertions"][1][key] = value
    with pytest.raises(QuarantineError, match="contrast_assertion_binding_required"):
        public_projection(contrast_card)


@pytest.mark.parametrize("key,value", [("status", "suppressed"), ("status", "superseded"),
    ("review", {"status": "rejected"}), ("source_id", "sum11"), ("locator", "other"),
    ("snapshot_id", "other"), ("value", "Different correction"), ("tier", 0),
    ("subject", {"kind": "sense", "id": "ws_other"}),
    ("mapping", {"ambiguous": True}), ("mapping", {"confidence": "unresolved"})])
def test_norm_must_survive_with_matching_source_text_and_sense(contrast_card, key, value):
    contrast_card["assertions"][0][key] = value
    with pytest.raises(QuarantineError, match="modern_norm_assertion_binding_required"):
        public_projection(contrast_card)


def test_fabricated_norm_reference_is_refused(contrast_card):
    contrast_card["assertions"][1]["value"]["soviet_colonization_context"]["norm"]["assertion_id"] = "missing"
    with pytest.raises(QuarantineError, match="modern_norm_assertion_binding_required"):
        public_projection(contrast_card)


@pytest.mark.parametrize("field", ["definition_uk", "examples", "gloss_en", "practice_answer", "stress"])
@pytest.mark.parametrize("source,text", [("sum11", "Unpaired text"),
    ("sum20", "Prefix SYNTHETIC IMPOSED QUOTATION. suffix")])
def test_no_soviet_provenance_or_unlabelled_pair_quotation_in_other_assertions(contrast_card, field, source, text):
    contrast_card["assertions"].append(assertion(source, "G-test", 1, field, text, "ws_x", "sense"))
    with pytest.raises(QuarantineError, match="sum11_in_default_split"):
        public_projection(contrast_card)


def test_external_inventory_rejects_unlabelled_text_without_any_pairs(contrast_card):
    contrast_card["assertions"] = [contrast_card["assertions"][0]]
    assert validate_card_contrasts(contrast_card) == 0
    with pytest.raises(QuarantineError, match="sum11_in_default_split"):
        validate_card_contrasts(contrast_card, sum11_texts=["Modern correction."])
    with pytest.raises(QuarantineError, match="sum11_in_default_split"):
        public_projection(contrast_card, sum11_texts=["Modern correction."])


def test_quote_in_practice_metadata_is_refused_even_with_a_valid_pair(contrast_card):
    contrast_card["practice"] = {"answer": "Synthetic imposed quotation."}
    with pytest.raises(QuarantineError, match="sum11_in_default_split"):
        public_projection(contrast_card)


def test_duplicate_assertion_ids_are_refused(contrast_card):
    contrast_card["assertions"].append(deepcopy(contrast_card["assertions"][1]))
    with pytest.raises(QuarantineError, match="duplicate_contrast_assertion"):
        public_projection(contrast_card)


def test_suppressed_contrast_is_only_a_tombstone(contrast_card):
    contrast_card["assertions"][1]["status"] = "suppressed"
    projected = public_projection(contrast_card)
    assert projected["assertions"][1] == {
        "assertion_id": contrast_card["assertions"][1]["assertion_id"],
        "status": "suppressed", "suppression_ref": "",
    }
    assert validate_card_contrasts(projected) == 0


@pytest.mark.parametrize("value", [None, {}, {"soviet_colonization_context": None},
    {"soviet_colonization_context": {"imposed": None}}, "Synthetic imposed quotation."])
def test_withdrawn_unstructured_soviet_assertions_never_export(contrast_card, value):
    contrast_card["assertions"][1].update(status="suppressed", value=value)
    projected = public_projection(contrast_card)
    assert "value" not in projected["assertions"][1]


def test_withdrawing_pair_keeps_its_quote_in_the_leakage_inventory(contrast_card):
    contrast_card["assertions"][1]["status"] = "suppressed"
    contrast_card["practice"] = {"answer": "Synthetic imposed quotation."}
    with pytest.raises(QuarantineError, match="sum11_in_default_split"):
        public_projection(contrast_card)


def test_resolution_metadata_cannot_hide_a_detached_quote(contrast_card):
    projected = public_projection(contrast_card)
    projected["senses"][0]["fields"]["russification_exposed"]["note"] = "Synthetic imposed quotation."
    with pytest.raises(QuarantineError, match="sum11_in_default_split"):
        validate_card_contrasts(projected)


def test_duplicate_pair_ids_are_refused(contrast_card):
    duplicate = deepcopy(contrast_card["assertions"][1])
    duplicate["assertion_id"] = "wa_other"
    contrast_card["assertions"].append(duplicate)
    with pytest.raises(QuarantineError, match="duplicate_contrast_pair"):
        public_projection(contrast_card)


def test_pairs_must_name_a_sense_present_on_the_card(contrast_card):
    contrast_card["senses"] = []
    with pytest.raises(QuarantineError, match="contrast_assertion_binding_required"):
        public_projection(contrast_card)


@pytest.mark.parametrize("key,value", [
    ("mapping", {"confidence": "high", "note": "Synthetic imposed quotation."}),
    ("producer", {"kind": "source_extract", "name": "Synthetic imposed quotation."}),
    ("review", {"status": "none", "record": "Synthetic imposed quotation."}),
])
def test_contrast_metadata_cannot_repeat_the_quote_outside_the_pair(contrast_card, key, value):
    contrast_card["assertions"][1][key] = value
    with pytest.raises(QuarantineError, match="sum11_outside_contrast_pair"):
        public_projection(contrast_card)


def test_norm_cannot_reuse_the_imposed_text_of_another_pair(contrast_card):
    norm, imposed = contrast_card["assertions"]
    other_norm, other_imposed = deepcopy(norm), deepcopy(imposed)
    other_norm.update(assertion_id="wa_other_norm", value="Other modern correction.",
                      value_norm="Other modern correction.")
    other_imposed.update(assertion_id="wa_other_imposed", value_norm="pair:other")
    pair = other_imposed["value"]["soviet_colonization_context"]
    pair["pair_id"] = "pair:other"
    pair["imposed"]["text"] = norm["value"]
    pair["norm"].update(assertion_id=other_norm["assertion_id"], text=other_norm["value"])
    contrast_card["assertions"].extend([other_norm, other_imposed])
    with pytest.raises(QuarantineError, match="sum11_in_default_split"):
        public_projection(contrast_card)


@pytest.mark.parametrize("key,value", [("assertions", None), ("assertions", [None]),
    ("senses", None), ("senses", [None]), ("senses", [{"fields": None}])])
def test_invalid_card_collections_are_refused(contrast_card, key, value):
    contrast_card[key] = value
    with pytest.raises(QuarantineError, match="invalid_contrast_card"):
        validate_card_contrasts(contrast_card)
