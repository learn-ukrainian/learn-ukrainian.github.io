"""Contract-level safety gates for the evidence-graded correction/protection lane."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
SHA = "a" * 64
GOLD_LANE_HASHES = {
    CONTRACTS / "correction_record_v1.schema.json": "35bd6ccc85fc38f60879db4ec74fbf1979cccb1754ffb108c525d5f136ca747a",
    CONTRACTS / "correction_reviewer_decision_v1.schema.json": "c4d697b0afd6338eb7493c09b54ec265d82cc60bbc6a905f4b9707b0647177a6",
    ROOT / "scripts/projects/open_model_data/model_view_exporter.py": "a1c2f3693a8672f7ab1d8e745fafd75c5c45eab2ba2bcd5e17d9ac4739635aee",
}
SCHEMA_NAMES = (
    "correction_protection_source_v1.schema.json",
    "correction_protection_evidence_v1.schema.json",
    "correction_protection_disagreement_v1.schema.json",
    "correction_protection_case_v1.schema.json",
    "correction_protection_release_receipt_v1.schema.json",
    "vesum_unattested_sample_record_v1.schema.json",
    "vesum_unattested_sample_receipt_v1.schema.json",
    "ukrainian_nlp_ecosystem_delta_v1.schema.json",
)
CATEGORY_IDS = (
    "russian_lexical_inflectional_intrusion",
    "contextual_calque_government_valency",
    "modern_literary_ukrainian_control",
    "marked_russian_quotation_code_switch",
    "phonetic_russian_in_literature",
    "historical_archaic_ukrainian",
    "dialect_regional_heritage_folklore",
    "surzhyk_contested_contact",
)


def _schema(name: str) -> dict[str, Any]:
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


def _validate(name: str, instance: dict[str, Any]) -> None:
    Draft202012Validator(_schema(name)).validate(instance)


def _ref(prefix: str) -> str:
    return f"{prefix}:{SHA}"


def _source(*, text: str | None = None, publication: str = "not_permitted") -> dict[str, Any]:
    return {
        "schema_version": "correction_protection_source_v1",
        "source_locator_id": _ref("cp_source"),
        "record_id": "record:fixture",
        "work_id": "work:fixture",
        "source_id": "source:fixture",
        "revision_pin": "fixture-revision",
        "locator": "fixture:source/42",
        "content_sha256": SHA,
        "source_axes": {"source_family": "fixture", "period": "modern", "genre": "prose", "register": "neutral"},
        "phase2_capability": {"decision_id": "phase2:fixture", "decision_sha256": SHA, "evidence_refs": ["phase2-evidence:fixture"]},
        "context": {
            "start_offset": 1,
            "end_offset": 2,
            "context_sha256": SHA,
            "publication_capability_state": publication,
            "publication_capability_evidence_refs": ["publication:fixture"] if text is not None else [],
            "context_text": text,
        },
    }


def _evidence() -> dict[str, Any]:
    return {
        "schema_version": "correction_protection_evidence_v1",
        "evidence_id": _ref("cp_evidence"),
        "channel": "vesum",
        "source_identity": "vesum-fixture",
        "source_version": "fixture-v1",
        "locator": "fixture:vesum/query",
        "query": None,
        "query_sha256": SHA,
        "status": "not_found",
        "supports": "no_conclusion",
        "receipt": {"retrieval_id": "receipt:fixture", "retrieval_sha256": SHA, "parser_id": "fixture-parser", "parser_version": "v1", "parser_status": "passed"},
        "raw_payload_publication_allowed": False,
        "claim_boundary": {"authoritative": False, "human_gold": False, "model_vote_authoritative": False, "vesum_absence_only_authoritative": False},
    }


def _case(*, disposition: str = "correction") -> dict[str, Any]:
    case = {
        "schema_version": "correction_protection_case_v1",
        "case_id": _ref("cp_case"),
        "assurance_tier": "evidence_graded_non_gold",
        "authoritative": False,
        "source": {"source_locator_id": _ref("cp_source"), "source_locator_sha256": SHA},
        "original": {"start_offset": 1, "end_offset": 2, "surface_sha256": SHA, "immutable": True},
        "evidence_refs": [{"evidence_id": _ref("cp_evidence"), "channel": "ukrainian_corpus", "evidence_sha256": SHA}],
        "category_gate": {"category_id": CATEGORY_IDS[0], "state": "passed", "correction_release_allowed": True, "threshold_config_sha256": SHA, "evidence_refs": ["gate-evidence:fixture"]},
        "disposition": disposition,
        "claim_boundary": {"human_gold": False, "human_reviewed": False, "model_vote_authoritative": False, "vesum_absence_only_authoritative": False, "training_eligible": False, "upload_eligible": False, "accelerator_eligible": False},
    }
    if disposition == "correction":
        case["proposal"] = {"replacement": "fixture", "replacement_sha256": "b" * 64, "original_surface_sha256": SHA, "reversible": True, "proposal_sha256": "c" * 64}
    return case


def _artifact() -> dict[str, Any]:
    return {"logical_path": "private/fixture.jsonl", "records": 1, "sha256": SHA}


def test_schemas_are_meta_valid_and_strict() -> None:
    for name in SCHEMA_NAMES:
        schema = _schema(name)
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False
        assert schema["$id"] == f"https://learn-ukrainian.github.io/schemas/open-model-data/{name}"


def test_positive_contract_fixtures_validate() -> None:
    _validate("correction_protection_source_v1.schema.json", _source())
    _validate("correction_protection_evidence_v1.schema.json", _evidence())
    _validate("correction_protection_case_v1.schema.json", _case())
    protected = _case(disposition="protected")
    protected["category_gate"].update({"state": "research_only", "correction_release_allowed": False})
    _validate("correction_protection_case_v1.schema.json", protected)
    _validate("correction_protection_disagreement_v1.schema.json", {
        "schema_version": "correction_protection_disagreement_v1", "disagreement_id": _ref("cp_disagreement"), "case_id": _ref("cp_case"),
        "proposals": [{"provider": "fixture-provider", "family": "fixture-family", "harness": "fixture-harness", "exact_model_id": "fixture-model", "proposal_sha256": SHA, "evidence_refs": [_ref("cp_evidence")], "dissent": "fixture dissent"}],
        "evidence_refs": [_ref("cp_evidence")], "challenge": "fixture challenge",
        "consensus": {"state": "model_only", "human_reviewed": False, "human_gold": False, "authoritative": False},
        "claim_boundary": {"assurance_tier": "evidence_graded_non_gold", "authoritative": False},
    })
    _validate("correction_protection_release_receipt_v1.schema.json", {
        "schema_version": "correction_protection_release_receipt_v1", "inputs": {"cases": _artifact()}, "schemas": {"case": SHA}, "config": {"gate": SHA}, "output": _artifact(), "counts": {"all": 1},
        "category_gates": {category: {"state": "research_only" if category == "surzhyk_contested_contact" else "passed", "research_only": category == "surzhyk_contested_contact", "correction_release_allowed": category in CATEGORY_IDS[:2], "threshold_config_sha256": SHA} for category in CATEGORY_IDS}, "axes_coverage": {axis: {"fixture": 1} for axis in ("source_family", "period", "genre", "register")},
        "dispositions": {name: 0 for name in ("correct", "correction", "protected", "excluded", "unresolved")}, "evidence_grades": {"fixture": 1}, "disagreement": _artifact(),
        "rights_and_publication": {"rights_decision_refs": ["rights:fixture"], "publication_decision_refs": ["publication:fixture"], "raw_payloads_published": False}, "contamination_registry": _artifact(),
        "determinism": {"algorithm": "fixture", "algorithm_sha256": SHA, "serialization": "UTF-8 canonical JSON with sorted keys and LF", "timestamps_omitted": True}, "held_back_strategy": {"locator": "private:held-back/fixture", "public_repo_copy": False},
        "safety": {"training": False, "upload": False, "model": False, "accelerator": False, "human_gold": False, "authoritative": False},
    })
    _validate("vesum_unattested_sample_record_v1.schema.json", {
        "schema_version": "vesum_unattested_sample_record_v1", "sample_id": _ref("vesum_sample"), "assurance_tier": "evidence_graded_non_gold", "authoritative": False,
        "source": {"record_id": "record:fixture", "work_id": "work:fixture", "source_id": "source:fixture", "revision_pin": "fixture", "locator": "fixture:source", "content_sha256": SHA, "source_axes": {"source_family": "fixture", "period": "modern", "genre": "prose", "register": "neutral"}},
        "span": {"start_offset": 1, "end_offset": 2, "surface_sha256": SHA}, "classification": "unresolved", "evidence_refs": [_ref("cp_evidence")], "claim_boundary": {"human_gold": False, "human_reviewed": False, "text_published": False, "training_eligible": False},
    })
    _validate("vesum_unattested_sample_receipt_v1.schema.json", {
        "schema_version": "vesum_unattested_sample_receipt_v1", "denominator": 9292022, "production_expected_denominator": 9292022, "pins": {"config_sha256": SHA, "database_sha256": SHA, "vesum_sha256": SHA, "profile_sha256": SHA, "profile_receipt_sha256": SHA, "phase1_manifest_sha256": SHA, "phase1_receipt_sha256": SHA, "sampler_sha256": SHA, "detector_config_sha256": SHA, "detector_generator_sha256": SHA, "record_schema_sha256": SHA, "receipt_schema_sha256": SHA},
        "stratification": {"algorithm": "fixture", "algorithm_sha256": SHA, "quotas": {"fixture": 1}}, "output": _artifact(), "sample_counts": {"fixture": 1}, "sample_hashes": [SHA], "coverage": {"fixture": 1}, "limitations": ["fixture limitation"],
        "two_build_identity": {
            "comparison_algorithm": "independent-artifact-byte-identity-sha256-v1",
            "first_output": {"logical_path": "candidate.jsonl", "sha256": SHA},
            "second_output": {"logical_path": "sample.jsonl", "sha256": SHA},
            "identical": True,
        }, "safety": {"text_published": False, "training": False, "human_gold": False, "authoritative": False},
    })
    _validate("ukrainian_nlp_ecosystem_delta_v1.schema.json", {
        "schema_version": "ukrainian_nlp_ecosystem_delta_v1", "delta_id": _ref("uk_nlp_delta"), "tool_or_source": "fixture", "revision": "v1", "inspected_on": "2026-08-04", "official_url": "https://example.invalid/official", "primary_urls": ["https://example.invalid/primary"],
        "observations": {"interface": "fixture", "phenomena": "fixture", "protected_context": "fixture", "evidence_granularity": "fixture", "output": "fixture", "license": "fixture"},
        "overlap_claims": [], "delta_claims": [], "limitations": ["inspected scope only"], "reproduction": {"commands": ["fixture command"], "command_sha256": SHA, "input_sha256": SHA},
    })


def test_forbidden_weakenings_fail_closed() -> None:
    missing_query_identity = _evidence()
    missing_query_identity["query_sha256"] = None
    with pytest.raises(ValidationError):
        _validate("correction_protection_evidence_v1.schema.json", missing_query_identity)
    missing_proposal = _case()
    del missing_proposal["proposal"]
    with pytest.raises(ValidationError):
        _validate("correction_protection_case_v1.schema.json", missing_proposal)
    model_only = _case()
    model_only["evidence_refs"][0]["channel"] = "model_proposal"
    with pytest.raises(ValidationError):
        _validate("correction_protection_case_v1.schema.json", model_only)
    vesum_only = _case()
    vesum_only["evidence_refs"][0]["channel"] = "vesum"
    with pytest.raises(ValidationError):
        _validate("correction_protection_case_v1.schema.json", vesum_only)
    research_only_correction = _case()
    research_only_correction["category_gate"].update({"state": "research_only", "correction_release_allowed": False})
    with pytest.raises(ValidationError):
        _validate("correction_protection_case_v1.schema.json", research_only_correction)
    protected_with_proposal = _case()
    protected_with_proposal["disposition"] = "protected"
    with pytest.raises(ValidationError):
        _validate("correction_protection_case_v1.schema.json", protected_with_proposal)
    unpublished_text = _source(text="fixture text", publication="not_permitted")
    with pytest.raises(ValidationError):
        _validate("correction_protection_source_v1.schema.json", unpublished_text)
    consensus = {
        "schema_version": "correction_protection_disagreement_v1", "disagreement_id": _ref("cp_disagreement"), "case_id": _ref("cp_case"), "proposals": [{"provider": "p", "family": "f", "harness": "h", "exact_model_id": "m", "proposal_sha256": SHA, "evidence_refs": [_ref("cp_evidence")], "dissent": "d"}], "evidence_refs": [_ref("cp_evidence")], "challenge": "c", "consensus": {"state": "model_only", "human_reviewed": False, "human_gold": False, "authoritative": False}, "claim_boundary": {"assurance_tier": "evidence_graded_non_gold", "authoritative": False},
    }
    consensus["consensus"]["human_gold"] = True
    with pytest.raises(ValidationError):
        _validate("correction_protection_disagreement_v1.schema.json", consensus)
    sample = {"schema_version": "vesum_unattested_sample_record_v1", "sample_id": _ref("vesum_sample"), "assurance_tier": "evidence_graded_non_gold", "authoritative": False, "source": {"record_id": "r:1", "work_id": "w:1", "source_id": "s:1", "revision_pin": "v1", "locator": "fixture", "content_sha256": SHA, "source_axes": {"source_family": "f", "period": "p", "genre": "g", "register": "r"}}, "span": {"start_offset": 0, "end_offset": 1, "surface_sha256": SHA}, "classification": "unresolved", "evidence_refs": [_ref("cp_evidence")], "claim_boundary": {"human_gold": False, "human_reviewed": False, "text_published": False, "training_eligible": False}}
    sample["classification"] = "automatic_error"
    with pytest.raises(ValidationError):
        _validate("vesum_unattested_sample_record_v1.schema.json", sample)


def test_fixed_dispositions_namespace_and_release_safety() -> None:
    case = _case(disposition="correct")
    case["case_id"] = _ref("correction")
    with pytest.raises(ValidationError):
        _validate("correction_protection_case_v1.schema.json", case)
    assert _schema("correction_protection_case_v1.schema.json")["properties"]["disposition"]["enum"] == ["correct", "correction", "protected", "excluded", "unresolved"]
    category_gates = _schema("correction_protection_release_receipt_v1.schema.json")["properties"]["category_gates"]
    assert set(category_gates["required"]) == set(CATEGORY_IDS)
    assert set(category_gates["properties"]) == set(CATEGORY_IDS)
    safety = _schema("correction_protection_release_receipt_v1.schema.json")["properties"]["safety"]["properties"]
    assert {key: value["const"] for key, value in safety.items()} == {key: False for key in ("training", "upload", "model", "accelerator", "human_gold", "authoritative")}


def test_existing_gold_lane_and_exporter_are_untouched() -> None:
    for path, expected in GOLD_LANE_HASHES.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
