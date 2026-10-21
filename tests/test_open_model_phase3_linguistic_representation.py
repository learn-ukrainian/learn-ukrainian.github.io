"""Qualified-human canaries and structural tests for v3 representation."""

from __future__ import annotations

import copy

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_linguistic_canary as canary
from scripts.projects.open_model_data import phase3_linguistic_representation as representation


def _battery() -> dict[str, object]:
    return canary.build_canary_battery()


def _packet(shape: str) -> dict[str, object]:
    return next(packet for packet in _battery()["packets"] if packet["edit_shape"] == shape)


def test_exact_agreement_spread_regression_has_complete_context_and_unchanged_z() -> None:
    packet = _packet("substitution")
    text = packet["source"]["complete_text"]
    tokens = packet["tokens"]
    construction_tokens = [
        token
        for token in tokens
        if packet["construction_spans"][0]["start"] <= token["start"] < packet["construction_spans"][0]["end"]
    ]
    assert [token["text"] for token in construction_tokens] == ["з", "іншої", "сторони"]
    assert [(token["text"], text[token["start"] : token["end"]]) for token in construction_tokens] == [
        ("з", "з"),
        ("іншої", "іншої"),
        ("сторони", "сторони"),
    ]
    z_id = construction_tokens[0]["token_id"]
    assert packet["unchanged_function_word_token_ids"] == [z_id]
    assert packet["minimal_edit_spans"][0]["text"] == "іншої сторони"
    assert packet["construction_spans"][0]["text"] == "з іншої сторони"
    assert "з іншого боку" in packet["corrected"]["complete_text"]
    assert packet["evidence"]["correction_evidence"][0]["locator"]["path"].endswith("0192.a2.ann")
    assert packet["evidence"]["corroborating_corpus_evidence"][0]["retrieved_text"] == "З іншого боку"
    assert representation.validate_representation(packet) == packet


def test_remaining_canaries_are_real_ua_gec_train_rows_and_cover_every_shape() -> None:
    battery = _battery()
    packets = battery["packets"]
    assert {packet["edit_shape"] for packet in packets} == representation.EDIT_SHAPES
    for packet in packets:
        locator = packet["document"]["frozen_locator"]
        evidence = packet["evidence"]["correction_evidence"][0]
        corroborating = packet["evidence"]["corroborating_corpus_evidence"][0]
        assert locator["repository"] == canary.UA_GEC_REPOSITORY
        assert locator["commit"] == canary.UA_GEC_COMMIT
        assert evidence["qualified_human"] is True
        assert evidence["authority"] == "qualified_human"
        assert evidence["source_document_bytes_sha256"] == packet["document"]["source_document_bytes_sha256"]
        assert corroborating["locator"]["path"] != locator["path"]
        assert corroborating["source_document_bytes_sha256"] != packet["document"]["source_document_bytes_sha256"]
        assert (
            "corrected sentence at line" in corroborating["locator"].get("selection", "")
            or packet["edit_shape"] == "substitution"
        )
        assert (
            representation.apply_edits(packet["source"]["complete_text"], packet["edits"])
            == packet["corrected"]["complete_text"]
        )
    assert all(packet["document"]["frozen_locator"]["partition"].endswith("/train") for packet in packets[1:])
    assert all(
        packet["evidence"]["corroborating_corpus_evidence"][0]["locator"]["path"]
        != packet["document"]["frozen_locator"]["path"]
        for packet in packets
    )
    assert battery["provider_calls"] is False


def test_multi_edit_has_exact_source_and_target_coordinates() -> None:
    packet = _packet("multi_edit")
    source = packet["source"]["complete_text"]
    target = packet["corrected"]["complete_text"]
    assert len(packet["edits"]) == 3
    assert len(packet["minimal_edit_spans"]) == 3
    for edit in packet["edits"]:
        assert source[edit["start"] : edit["end"]] == edit["source_text"]
        assert target[edit["target_start"] : edit["target_end"]] == edit["target_text"]


def test_unicode_code_point_offsets_and_word_boundaries_round_trip() -> None:
    text = "Півʼяблука та cafe\u0301 — тест."
    tokens = representation.tokenize(
        text,
        paragraph_span={"start": 0, "end": len(text)},
        sentence_span={"start": 0, "end": len(text)},
    )
    assert [token["text"] for token in tokens] == ["Півʼяблука", "та", "cafe\u0301", "—", "тест", "."]
    assert all(text[token["start"] : token["end"]] == token["text"] for token in tokens)
    assert tokens[2]["end"] - tokens[2]["start"] == len("cafe\u0301")
    assert tokens[2]["normalized_text"] == "café"


def test_schema_is_strict_and_every_canary_matches_it() -> None:
    schema = __import__("json").loads(representation.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for packet in _battery()["packets"]:
        validator.validate(packet)
    broken = copy.deepcopy(_packet("substitution"))
    broken["unknown"] = True
    with pytest.raises(representation.LinguisticRepresentationError, match="Additional properties"):
        representation.validate_representation(broken)


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda packet: packet["source"].update({"complete_text": "fragment"}), "stale source UTF-8 bytes hash"),
        (lambda packet: packet["edits"][0].update({"start": 1}), "stale|outside|overlap"),
        (lambda packet: packet["corrected"].update({"complete_text": "not a round trip"}), "round-trip"),
        (
            lambda packet: packet["evidence"].update({"correction_evidence": []}),
            "schema violation|missing qualified-human",
        ),
        (
            lambda packet: packet["classification"].update({"primary_role_id": "invented_role"}),
            "schema violation|invalid frozen",
        ),
        (
            lambda packet: packet["classification"].update({"claim_type": "invented_claim"}),
            "schema violation|invalid frozen",
        ),
        (
            lambda packet: packet["evidence"]["correction_evidence"][0].update({"authority": "model_output"}),
            "model output",
        ),
        (lambda packet: packet.update({"provider_calls": True}), "schema violation|provider calls"),
        (
            lambda packet: packet["evidence"]["corroborating_corpus_evidence"][0].update({"retrieved_text": "drift"}),
            "not exact",
        ),
        (
            lambda packet: packet["unchanged_function_word_token_ids"].append(
                packet["unchanged_function_word_token_ids"][0]
            ),
            "duplicate|schema violation",
        ),
    ],
)
def test_validator_rejects_stale_or_unauthorized_packets(mutate: object, message: str) -> None:
    packet = copy.deepcopy(_packet("substitution"))
    assert callable(mutate)
    mutate(packet)
    with pytest.raises(representation.LinguisticRepresentationError, match=message):
        representation.validate_representation(packet)


def test_reordering_rejects_non_permutation() -> None:
    packet = copy.deepcopy(_packet("reordering"))
    packet["edits"][0]["replacement"] = "зовсім інші слова"
    with pytest.raises(representation.LinguisticRepresentationError, match=r"stale|reordering"):
        representation.validate_representation(packet)


def test_validator_rejects_function_word_outside_construction() -> None:
    packet = copy.deepcopy(_packet("substitution"))
    packet["unchanged_function_word_token_ids"] = ["tok:000001"]
    with pytest.raises(representation.LinguisticRepresentationError, match="outside every construction"):
        representation.validate_representation(packet)


def test_validator_rejects_self_corroboration() -> None:
    packet = copy.deepcopy(_packet("insertion"))
    correction = packet["evidence"]["correction_evidence"][0]
    corroborating = packet["evidence"]["corroborating_corpus_evidence"][0]
    corroborating["locator"] = copy.deepcopy(correction["locator"])
    corroborating["locator_sha256"] = representation.sha256_value(corroborating["locator"])
    corroborating["source_document_bytes_sha256"] = packet["document"]["source_document_bytes_sha256"]
    with pytest.raises(representation.LinguisticRepresentationError, match=r"distinct corpus locator|distinct source"):
        representation.validate_representation(packet)


def test_validator_rejects_corroboration_that_only_repeats_error_context() -> None:
    packet = copy.deepcopy(_packet("deletion"))
    corroborating = packet["evidence"]["corroborating_corpus_evidence"][0]
    corroborating["retrieved_text"] = packet["source"]["complete_text"]
    corroborating["retrieved_text_sha256"] = representation.sha256_text(corroborating["retrieved_text"])
    with pytest.raises(representation.LinguisticRepresentationError, match="does not support corrected context"):
        representation.validate_representation(packet)
