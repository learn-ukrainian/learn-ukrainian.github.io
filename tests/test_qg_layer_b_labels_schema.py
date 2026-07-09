"""Phase 0 contract tests for the QG Layer B labels sidecar.

The helper in this test module deliberately validates only static label data
against immutable reference-output fixtures. It is not imported by Layer A or
Layer B runtime code.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas/qg-layer-b-labels.v2.schema.json"
LABEL_SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(LABEL_SCHEMA)


@dataclass(frozen=True)
class OutputReference:
    """Immutable source bytes and identity material used only by these tests."""

    raw_output: str
    normalized_output: str
    canonical_identity_material: str


def _sha256(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _schema_errors(document: dict[str, Any]) -> list[str]:
    return sorted(error.message for error in VALIDATOR.iter_errors(document))


def _assert_schema_valid(document: dict[str, Any]) -> None:
    errors = _schema_errors(document)
    assert not errors, "schema validation failed: " + "; ".join(errors)


def _assert_label_data_invariants(document: dict[str, Any], references: dict[str, OutputReference]) -> None:
    """Validate invariants that standard JSON Schema cannot express.

    The references stand in for frozen source artifacts. A production label set
    would supply equivalent immutable source material to its validation command.
    """

    candidate_locations: dict[str, str] = {}
    canonical_identity_material: dict[str, str] = {}

    for case in document["cases"]:
        for event_output_id, candidates in case["candidates_by_event_output_id"].items():
            reference = references.get(event_output_id)
            if reference is None:
                raise AssertionError(f"missing reference output for event_output_id={event_output_id}")
            if _sha256(reference.raw_output) != candidates[0]["raw_output_sha256"]:
                raise AssertionError("raw-output SHA-256 does not match frozen reference output")
            if _sha256(reference.normalized_output) != candidates[0]["normalized_output_sha256"]:
                raise AssertionError("normalized-output SHA-256 does not match frozen reference output")

            for candidate in candidates:
                if _sha256(reference.raw_output) != candidate["raw_output_sha256"]:
                    raise AssertionError("raw-output SHA-256 does not match frozen reference output")
                if _sha256(reference.normalized_output) != candidate["normalized_output_sha256"]:
                    raise AssertionError("normalized-output SHA-256 does not match frozen reference output")

                previous_segment: dict[str, Any] | None = None
                for expected_index, segment in enumerate(candidate["ordered_segment_spans"]):
                    if segment["segment_index"] != expected_index:
                        raise AssertionError("segment indices must be consecutive and ordered")
                    if not (
                        segment["excerpt_normalized_start"] < segment["excerpt_normalized_end"]
                        and segment["output_normalized_start"] < segment["output_normalized_end"]
                        and segment["output_raw_start"] < segment["output_raw_end"]
                    ):
                        raise AssertionError("all spans must be non-empty and half-open")
                    if previous_segment is not None and (
                        previous_segment["output_normalized_end"] > segment["output_normalized_start"]
                        or previous_segment["output_raw_end"] > segment["output_raw_start"]
                    ):
                        raise AssertionError("segments must be ordered and non-overlapping")

                    normalized_segment = reference.normalized_output[
                        segment["output_normalized_start"] : segment["output_normalized_end"]
                    ]
                    raw_segment = reference.raw_output[segment["output_raw_start"] : segment["output_raw_end"]]
                    if raw_segment != normalized_segment:
                        raise AssertionError("normalized-to-raw round trip does not reproduce the segment")
                    if _sha256(normalized_segment) != segment["normalized_segment_sha256"]:
                        raise AssertionError("normalized segment SHA-256 does not match extracted text")
                    if _sha256(raw_segment) != segment["raw_segment_sha256"]:
                        raise AssertionError("raw segment SHA-256 does not match extracted text")
                    previous_segment = segment

                candidate_id = candidate["candidate_id"]
                previous_event_output_id = candidate_locations.setdefault(candidate_id, event_output_id)
                if previous_event_output_id != event_output_id:
                    raise AssertionError("one candidate_id must not span different event outputs")

                canonical_source_id = candidate["canonical_source_id"]
                previous_material = canonical_identity_material.setdefault(
                    canonical_source_id, reference.canonical_identity_material
                )
                if previous_material != reference.canonical_identity_material:
                    raise AssertionError("canonical_source_id has inconsistent identity material")


def _assert_contract_valid(document: dict[str, Any], references: dict[str, OutputReference]) -> None:
    _assert_schema_valid(document)
    _assert_label_data_invariants(document, references)


def _make_segment(
    *,
    index: int,
    excerpt_start: int,
    excerpt_end: int,
    output_start: int,
    output_end: int,
    reference: OutputReference,
) -> dict[str, Any]:
    normalized_segment = reference.normalized_output[output_start:output_end]
    raw_segment = reference.raw_output[output_start:output_end]
    return {
        "segment_index": index,
        "excerpt_normalized_start": excerpt_start,
        "excerpt_normalized_end": excerpt_end,
        "output_normalized_start": output_start,
        "output_normalized_end": output_end,
        "output_raw_start": output_start,
        "output_raw_end": output_end,
        "normalized_segment_sha256": _sha256(normalized_segment),
        "raw_segment_sha256": _sha256(raw_segment),
    }


def _valid_document(*, ordered_segments: bool = False) -> tuple[dict[str, Any], dict[str, OutputReference]]:
    raw_output = "Іван Франко навчався у Віденському університеті. У 1893 році він захистив дисертацію."
    reference = OutputReference(
        raw_output=raw_output,
        normalized_output=raw_output,
        canonical_identity_material="sources_query_wikipedia|Ivan_Franko|revision-1893|lead",
    )
    event_output_id = _sha256("event-output:franko-vienna")
    first_fragment = "Іван Франко"
    second_fragment = "1893"
    first_start = raw_output.index(first_fragment)
    second_start = raw_output.index(second_fragment)

    if ordered_segments:
        evidence_excerpt = f"{first_fragment} ... {second_fragment}"
        segments = [
            _make_segment(
                index=0,
                excerpt_start=0,
                excerpt_end=len(first_fragment),
                output_start=first_start,
                output_end=first_start + len(first_fragment),
                reference=reference,
            ),
            _make_segment(
                index=1,
                excerpt_start=len(first_fragment) + 5,
                excerpt_end=len(evidence_excerpt),
                output_start=second_start,
                output_end=second_start + len(second_fragment),
                reference=reference,
            ),
        ]
        match_type = "ORDERED_EXACT_SEGMENTS"
        layer_a_reason = "ANCHORED_ORDERED_SEGMENTS"
    else:
        evidence_excerpt = first_fragment
        segments = [
            _make_segment(
                index=0,
                excerpt_start=0,
                excerpt_end=len(first_fragment),
                output_start=first_start,
                output_end=first_start + len(first_fragment),
                reference=reference,
            )
        ]
        match_type = "EXACT_CONTIGUOUS"
        layer_a_reason = "ANCHORED_CONTIGUOUS"

    candidate = {
        "candidate_id": _sha256("candidate:franko-vienna"),
        "canonical_source_id": _sha256(reference.canonical_identity_material),
        "source_index": 0,
        "tool_identity": {
            "raw_name": "sources_query_wikipedia",
            "canonical_name": "sources_query_wikipedia",
        },
        "query_identity": {
            "canonical_json": '{"title":"Іван Франко"}',
            "sha256": _sha256('{"title":"Іван Франко"}'),
        },
        "raw_output_sha256": _sha256(reference.raw_output),
        "normalized_output_sha256": _sha256(reference.normalized_output),
        "output_capture_complete": True,
        "anchor_scan_complete": True,
        "match_type": match_type,
        "similarity": 1.0,
        "eligibility": "ELIGIBLE",
        "error_status": "NONE",
        "ordered_segment_spans": segments,
        "expected_source_relation": "ENTAILS",
        "expected_support_spans": [
            {
                "start": first_start,
                "end": first_start + len(first_fragment),
                "role": "SUPPORTS",
            }
        ],
    }
    artifact_hash = _sha256("audit:phase-0")
    document = {
        "schema_version": "qg-layer-b-labels.v2",
        "dataset_id": "qg-layer-b-contract-test",
        "source_artifacts": [
            {
                "artifact_sha256": artifact_hash,
                "fixture_set_sha256": _sha256("fixtures:qg-bakeoff"),
            }
        ],
        "qualification_eligible": False,
        "qualification_blockers": ["This is a partial contract-test label pilot."],
        "cases": [
            {
                "case_id": "franko-contiguous",
                "artifact_sha256": artifact_hash,
                "fixture_id": "franko-ivan",
                "fact_check_id": "fact-1",
                "fact_check_index": 0,
                "claim": "Іван Франко навчався у Віденському університеті.",
                "evidence_excerpt": evidence_excerpt,
                "claim_is_true": True,
                "expected_reviewer_verdict": "CONFIRMED",
                "expected_layer_a_decision": "ANCHOR",
                "expected_layer_a_reason": layer_a_reason,
                "anchor_scan_complete": True,
                "candidate_set_complete": True,
                "candidates_by_event_output_id": {event_output_id: [candidate]},
                "expected_aggregate_relation": "ENTAILS",
                "expected_fact_check_decision": "ACCEPT",
                "context_sufficient": True,
                "failure_class": "ELLIPSIZED_GENUINE_EXCERPT",
                "corpus_verification_status": "VERIFIED",
                "annotators": ["annotator-a", "annotator-b"],
                "adjudication": {
                    "status": "AGREED",
                    "adjudicator": None,
                    "note": "Independent annotations matched all material fields.",
                },
            }
        ],
    }
    return document, {event_output_id: reference}


def _only_candidate(document: dict[str, Any]) -> dict[str, Any]:
    candidates_by_event_output_id = document["cases"][0]["candidates_by_event_output_id"]
    return next(iter(candidates_by_event_output_id.values()))[0]


def test_01_accepts_a_valid_contiguous_candidate() -> None:
    document, references = _valid_document()

    _assert_contract_valid(document, references)


def test_02_accepts_a_valid_ordered_multi_segment_candidate() -> None:
    document, references = _valid_document(ordered_segments=True)

    _assert_contract_valid(document, references)


def test_03_requires_stable_event_output_raw_output_normalized_output_and_segment_hashes() -> None:
    document, references = _valid_document()
    candidate = _only_candidate(document)
    required_hashes = [
        (document["cases"][0]["candidates_by_event_output_id"], "event-output"),
        (candidate, "raw_output_sha256"),
        (candidate, "normalized_output_sha256"),
        (candidate["ordered_segment_spans"][0], "raw_segment_sha256"),
        (candidate["ordered_segment_spans"][0], "normalized_segment_sha256"),
    ]

    for _container, key in required_hashes:
        invalid = deepcopy(document)
        if key == "event-output":
            invalid["cases"][0]["candidates_by_event_output_id"] = {"not-a-sha256": [candidate]}
        else:
            if key in {"raw_output_sha256", "normalized_output_sha256"}:
                _only_candidate(invalid).pop(key)
            else:
                _only_candidate(invalid)["ordered_segment_spans"][0].pop(key)
        assert _schema_errors(invalid), f"missing {key} must be rejected"

    invalid = deepcopy(document)
    _only_candidate(invalid)["raw_output_sha256"] = "f" * 64
    with pytest.raises(AssertionError, match="raw-output SHA-256"):
        _assert_contract_valid(invalid, references)


def test_04_requires_complete_candidate_records_keyed_by_event_output_identity() -> None:
    document, _ = _valid_document()
    candidate = _only_candidate(document)
    candidate.pop("tool_identity")

    errors = _schema_errors(document)

    assert errors
    assert any("tool_identity" in error for error in errors)


def test_05_rejects_anchor_when_candidate_set_is_incomplete() -> None:
    document, _ = _valid_document()
    document["cases"][0]["candidate_set_complete"] = False

    assert _schema_errors(document)


def test_06_rejects_overlapping_or_out_of_order_segments() -> None:
    overlapping, overlapping_references = _valid_document(ordered_segments=True)
    second_segment = _only_candidate(overlapping)["ordered_segment_spans"][1]
    second_segment["output_normalized_start"] = 0
    second_segment["output_raw_start"] = 0

    with pytest.raises(AssertionError, match="ordered and non-overlapping"):
        _assert_contract_valid(overlapping, overlapping_references)

    out_of_order, out_of_order_references = _valid_document(ordered_segments=True)
    _only_candidate(out_of_order)["ordered_segment_spans"][1]["segment_index"] = 2

    with pytest.raises(AssertionError, match="consecutive and ordered"):
        _assert_contract_valid(out_of_order, out_of_order_references)


def test_07_rejects_segments_spanning_different_event_outputs() -> None:
    document, references = _valid_document(ordered_segments=True)
    candidates_by_event_output_id = document["cases"][0]["candidates_by_event_output_id"]
    candidate = deepcopy(_only_candidate(document))
    second_event_output_id = _sha256("event-output:franko-vienna-replay")
    candidates_by_event_output_id[second_event_output_id] = [candidate]
    original_reference = next(iter(references.values()))
    references[second_event_output_id] = original_reference

    with pytest.raises(AssertionError, match="must not span different event outputs"):
        _assert_contract_valid(document, references)


def test_08_rejects_invalid_normalized_to_raw_round_trips() -> None:
    document, references = _valid_document()
    segment = _only_candidate(document)["ordered_segment_spans"][0]
    segment["output_raw_start"] += 1

    with pytest.raises(AssertionError, match="normalized-to-raw round trip"):
        _assert_contract_valid(document, references)


def test_09_treats_source_index_as_diagnostic_rather_than_identity() -> None:
    document, references = _valid_document()
    _only_candidate(document)["source_index"] = 99

    _assert_contract_valid(document, references)


def test_10_rejects_inconsistent_canonical_source_identity() -> None:
    document, references = _valid_document()
    candidates_by_event_output_id = document["cases"][0]["candidates_by_event_output_id"]
    candidate = deepcopy(_only_candidate(document))
    second_event_output_id = _sha256("event-output:different-source")
    second_reference = OutputReference(
        raw_output="Окремий документ містить інший запис.",
        normalized_output="Окремий документ містить інший запис.",
        canonical_identity_material="sources_query_wikipedia|Different_document|revision-1|lead",
    )
    candidate["candidate_id"] = _sha256("candidate:different-source")
    candidate["raw_output_sha256"] = _sha256(second_reference.raw_output)
    candidate["normalized_output_sha256"] = _sha256(second_reference.normalized_output)
    candidate["ordered_segment_spans"] = [
        _make_segment(
            index=0,
            excerpt_start=0,
            excerpt_end=len("Окремий"),
            output_start=0,
            output_end=len("Окремий"),
            reference=second_reference,
        )
    ]
    candidate["expected_support_spans"] = [{"start": 0, "end": len("Окремий"), "role": "SUPPORTS"}]
    candidates_by_event_output_id[second_event_output_id] = [candidate]
    references[second_event_output_id] = second_reference

    with pytest.raises(AssertionError, match="inconsistent identity material"):
        _assert_contract_valid(document, references)


def test_11_accepts_mixed_as_a_human_source_relation() -> None:
    document, references = _valid_document()
    candidate = _only_candidate(document)
    candidate["expected_source_relation"] = "MIXED"
    candidate["expected_support_spans"].append(
        {
            "start": 0,
            "end": len("Іван"),
            "role": "CONTRADICTS",
        }
    )
    document["cases"][0]["expected_aggregate_relation"] = "MIXED"
    document["cases"][0]["expected_fact_check_decision"] = "AUDIT"

    _assert_contract_valid(document, references)


def test_12_requires_eligibility_and_error_status_for_every_candidate() -> None:
    document, _ = _valid_document()

    for field in ("eligibility", "error_status"):
        invalid = deepcopy(document)
        _only_candidate(invalid).pop(field)
        assert _schema_errors(invalid), f"missing {field} must be rejected"


def test_13_requires_qualification_eligible_false_for_a_partial_label_pilot() -> None:
    document, _ = _valid_document()
    document["qualification_eligible"] = True

    errors = _schema_errors(document)

    assert errors
    assert any("expected to be empty" in error for error in errors)


def test_14_rejects_unknown_decision_reason_relation_and_status_enums() -> None:
    document, _ = _valid_document()
    mutations = [
        (document["cases"][0], "expected_layer_a_decision"),
        (document["cases"][0], "expected_layer_a_reason"),
        (_only_candidate(document), "expected_source_relation"),
        (_only_candidate(document), "eligibility"),
        (_only_candidate(document), "error_status"),
        (document["cases"][0], "corpus_verification_status"),
        (document["cases"][0]["adjudication"], "status"),
    ]

    for _, field in mutations:
        invalid, _ = _valid_document()
        if field in {"expected_layer_a_decision", "expected_layer_a_reason", "corpus_verification_status"}:
            target = invalid["cases"][0]
        elif field == "status":
            target = invalid["cases"][0]["adjudication"]
        else:
            target = _only_candidate(invalid)
        target[field] = "UNKNOWN_ENUM"
        assert _schema_errors(invalid), f"unknown {field} must be rejected"
