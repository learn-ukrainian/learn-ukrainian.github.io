"""Adversarial tests for the metadata-only Phase 3 V3-B control plane."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_v3b_cooperative_control_plane as v3b

H = "1" * 64


def _artifact() -> dict[str, Any]:
    return json.loads(v3b.ARTIFACT_PATH.read_text(encoding="utf-8"))


def _schema() -> dict[str, Any]:
    return json.loads(v3b.SCHEMA_PATH.read_text(encoding="utf-8"))


def _rehash(value: dict[str, Any]) -> None:
    value["receipt_sha256"] = v3b.receipt_sha(value)


def _reject(value: dict[str, Any], pattern: str) -> None:
    _rehash(value)
    with pytest.raises(v3b.V3BError, match=pattern):
        v3b.validate(value, _schema())


def _identity_output() -> dict[str, Any]:
    return {
        "schema_version": "phase3-v3b-role-output-v1",
        "contract_id": "v3b.identity.opinion",
        "row_id": H,
        "packet_sha256": "2" * 64,
        "input_sha256": "3" * 64,
        "parser_state": "valid",
        "evidence_ref_ids": ["evidence.ref.1"],
        "abstain": False,
        "decision": {
            "span_offsets": [0, 1],
            "language_identity": "ukrainian",
            "identity_candidates": ["ukrainian"],
            "diachronic_status": "modern",
            "variety_status": "standard",
            "variety_id": "standard_ukrainian",
            "period_id": "modern",
            "region_id": "national_standard",
            "register_id": "general",
            "contact_composition": "none",
            "context_role": "production",
            "recension_editorial_layer_id": "none",
            "primary_case_state": "correct_modern_production",
            "modern_correction_eligible": True,
            "protection_flags": [],
            "confidence_or_abstention_state": "high",
        },
    }


def _human_adjudication(artifact: dict[str, Any]) -> dict[str, Any]:
    registry = artifact["single_human_registry"]
    entry = registry["entries"][0]
    value = {
        "schema_version": "phase3-v3b-human-adjudication-v1",
        "row_id": H,
        "registry_sha256": registry["registry_sha256"],
        "entry_id": entry["entry_id"],
        "qualification_snapshot_sha256": entry["qualification_snapshot_sha256"],
        "atomic_decision_key": {
            "source_unit_id": "source.unit.1",
            "source_revision": "revision.1",
            "span_offsets": [0, 1],
            "span_sha256": "2" * 64,
            "coverage_stratum_id": "stratum.1",
            "decision_layer": "identity",
            "claim_type": "language_identity",
            "source_class": "official_ukrainian_source",
            "identity_candidate": "ukrainian",
            "proposed_value_sha256": "3" * 64,
            "evidence_set_sha256": "4" * 64,
            "registry_sha256": registry["registry_sha256"],
        },
        "decision_state": "adjudicated",
        "evidence_ref_ids": ["evidence.ref.1"],
        "directly_inspected": True,
    }
    value["adjudication_record_sha256"] = v3b.receipt_sha(value, "adjudication_record_sha256")
    return value


def _transition_receipt(
    artifact: dict[str, Any], sequence: int, source: str, target: str, condition: str, previous: str | None
) -> dict[str, Any]:
    value = {
        "schema_version": "phase3-v3b-transition-receipt-v1",
        "row_id": H,
        "denominator_sha256": artifact["incidence_manifest"]["denominator_sha256"],
        "contract_sha256": artifact["receipt_sha256"],
        "sequence": sequence,
        "from_state": source,
        "to_state": target,
        "condition_code": condition,
        "role_id": "SOURCE_ADMISSION",
        "attempt_count": 0,
        "format_retry_used": False,
        "substitute_used": False,
        "resolved_route": {
            "provider_family": "deterministic_tooling",
            "model": "deterministic",
            "harness": "local",
            "effort": "none",
        },
        "input_sha256": "2" * 64,
        "prompt_sha256": "3" * 64,
        "output_sha256": "4" * 64,
        "parser_result": "not_applicable",
        "failure_code": None,
        "guard_bundle_sha256": "8" * 64,
        "guard_result": "not_applicable",
        "gold_guard_results": {field: False for field in v3b.GOLD_GUARD_FIELDS},
        "previous_receipt_sha256": previous,
    }
    identity = {
        "row_id": value["row_id"],
        "sequence": value["sequence"],
        "from_state": value["from_state"],
        "to_state": value["to_state"],
        "condition_code": value["condition_code"],
    }
    value["receipt_id"] = v3b.sha256_bytes(v3b.canonical_bytes(identity))
    value["receipt_sha256"] = v3b.receipt_sha(value)
    return value


def test_frozen_artifact_and_schema_are_strict_and_deterministic() -> None:
    schema = _schema()
    artifact = _artifact()
    Draft202012Validator.check_schema(schema)
    v3b.validate(artifact, schema)
    assert schema["additionalProperties"] is False
    assert v3b.SCHEMA_PATH.read_bytes() == v3b.canonical_bytes(v3b.build_schema())
    assert v3b.ARTIFACT_PATH.read_bytes() == v3b.canonical_bytes(v3b.build_artifact())


def test_exact_v3a_denominator_is_preserved_without_cartesian_product() -> None:
    artifact = _artifact()
    assert artifact["denominator"] == {
        "source_units": 57,
        "visible_cells": 19,
        "active_coverage_target_cells": 16,
        "active_coverage_blocked_cells": 16,
        "not_applicable_cells": 2,
        "lineage_only_parent_cells": 1,
        "rights_operation_cells": 399,
        "rule_slots_R": 0,
    }
    incidence = artifact["incidence_manifest"]
    assert incidence["implicit_cartesian_product"] is False
    assert incidence["source_cell_row_count"] == 0
    assert incidence["rows"] == []


def test_incidence_omission_duplicate_and_implicit_product_are_rejected() -> None:
    value = _artifact()
    value["incidence_manifest"]["implicit_cartesian_product"] = True
    _reject(value, "implicit Cartesian")

    value = _artifact()
    row = {"row_id": H, "source_unit_id": "s1", "coverage_stratum_id": "c1", "state": "blocked"}
    incidence = value["incidence_manifest"]
    incidence["rows"] = [row, copy.deepcopy(row)]
    incidence["source_cell_row_count"] = 2
    incidence["state_query_row_count"] = 2
    incidence["residual_query_row_count"] = 2
    body = dict(incidence)
    body.pop("denominator_sha256")
    incidence["denominator_sha256"] = v3b.sha256_bytes(v3b.canonical_bytes(body))
    value["human_work_manifest"]["population_denominator_sha256"] = incidence["denominator_sha256"]
    value["human_work_manifest"]["current_population_count"] = 2
    value["human_work_manifest"]["current_sample_count"] = 2
    _reject(value, "duplicate incidence row")


def test_identity_outputs_are_strict_label_blind_and_cross_family() -> None:
    lead = _identity_output()
    dissent = copy.deepcopy(lead)
    v3b.validate_identity_pair(lead, dissent, "anthropic", "google")

    leaked = copy.deepcopy(lead)
    leaked["model_order"] = 1
    with pytest.raises(v3b.V3BError, match="output schema violation"):
        v3b.validate_output("v3b.identity.opinion", leaked)

    mismatch = copy.deepcopy(dissent)
    mismatch["packet_sha256"] = "9" * 64
    with pytest.raises(v3b.V3BError, match="packet hash mismatch"):
        v3b.validate_identity_pair(lead, mismatch, "anthropic", "google")

    with pytest.raises(v3b.V3BError, match="family conflict"):
        v3b.validate_identity_pair(lead, dissent, "anthropic", "anthropic")


def test_malformed_or_body_bearing_model_outputs_are_rejected() -> None:
    missing = _identity_output()
    missing["decision"].pop("contact_composition")
    with pytest.raises(v3b.V3BError, match="output schema violation"):
        v3b.validate_output("v3b.identity.opinion", missing)

    bad_enum = _identity_output()
    bad_enum["decision"]["language_identity"] = "cyrillic_means_russian"
    with pytest.raises(v3b.V3BError, match="output schema violation"):
        v3b.validate_output("v3b.identity.opinion", bad_enum)

    body = _identity_output()
    body["source_body"] = "forbidden"
    with pytest.raises(v3b.V3BError, match=r"output schema violation|forbidden field"):
        v3b.validate_output("v3b.identity.opinion", body)


def test_quarantine_has_only_human_resume_and_never_direct_gold() -> None:
    machine = _artifact()["state_machine"]
    quarantine = [
        row for row in machine["transitions"] if row["from_state"] == "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD"
    ]
    assert {row["to_state"] for row in quarantine} == {"CASE_HUMAN_QUEUE", "IDENTITY_HUMAN_QUEUE"}
    assert not any(row["to_state"].startswith("GOLD") for row in quarantine)


def test_identity_abstention_cannot_reach_candidate_or_gold() -> None:
    machine = _artifact()["state_machine"]
    abstained = [row for row in machine["transitions"] if row["from_state"] == "IDENTITY_ABSTAINED_NON_GOLD"]
    assert abstained == [
        {
            "from_state": "IDENTITY_ABSTAINED_NON_GOLD",
            "to_state": "CASE_HUMAN_ABSTAINED",
            "condition_code": "abstention_case_preserved",
        }
    ]
    assert "TRAINING_ELIGIBLE" not in machine["states"]
    assert _artifact()["execution_gates"]["training_authorized"] is False


def test_retry_and_substitution_are_finite_and_family_safe() -> None:
    retry = _artifact()["retry_and_substitution"]
    assert retry["original_attempts"] == 1
    assert retry["format_retry_limit"] == 1
    assert retry["independent_family_substitute_limit"] == 1
    assert retry["maximum_attempts_per_role_per_row"] == 3
    assert _artifact()["blindness_and_conflicts"]["substitution_requires_new_provider_family"] is True


def test_single_operator_registry_is_procedural_not_fabricated_authority() -> None:
    registry = _artifact()["single_human_registry"]
    assert registry["entry_count"] == 1
    entry = registry["entries"][0]
    assert entry["entry_id"] == "solo_operator_v1"
    assert entry["actor_kind"] == "human"
    assert entry["credential_claimed"] is False
    assert entry["institutional_independence_claimed"] is False
    assert registry["registration_does_not_authorize_execution"] is True


def test_human_adjudication_requires_registry_atomic_key_and_direct_inspection() -> None:
    artifact = _artifact()
    value = _human_adjudication(artifact)
    v3b.validate_human_adjudication(value, artifact)

    unregistered = copy.deepcopy(value)
    unregistered["entry_id"] = "invented_external_expert"
    unregistered["adjudication_record_sha256"] = v3b.receipt_sha(
        unregistered, "adjudication_record_sha256"
    )
    with pytest.raises(v3b.V3BError, match="unregistered"):
        v3b.validate_human_adjudication(unregistered, artifact)

    incomplete = copy.deepcopy(value)
    incomplete["atomic_decision_key"].pop("coverage_stratum_id")
    incomplete["adjudication_record_sha256"] = v3b.receipt_sha(
        incomplete, "adjudication_record_sha256"
    )
    with pytest.raises(v3b.V3BError, match="atomic decision key"):
        v3b.validate_human_adjudication(incomplete, artifact)

    uninspected = copy.deepcopy(value)
    uninspected["directly_inspected"] = False
    uninspected["adjudication_record_sha256"] = v3b.receipt_sha(
        uninspected, "adjudication_record_sha256"
    )
    with pytest.raises(v3b.V3BError, match="direct human inspection"):
        v3b.validate_human_adjudication(uninspected, artifact)

    out_of_scope = copy.deepcopy(value)
    out_of_scope["atomic_decision_key"]["claim_type"] = "operation_rights"
    out_of_scope["adjudication_record_sha256"] = v3b.receipt_sha(
        out_of_scope, "adjudication_record_sha256"
    )
    with pytest.raises(v3b.V3BError, match="qualification out of scope"):
        v3b.validate_human_adjudication(out_of_scope, artifact)


def test_human_work_is_complete_bounded_and_overflow_is_resumable() -> None:
    artifact = _artifact()
    work = artifact["human_work_manifest"]
    assert work["sampling_mode"] == "complete_review"
    assert work["current_sample_count"] == work["current_population_count"] == 0
    assert work["all_admitted_rows_review_fraction"] == 1.0
    assert work["maximum_human_decisions"] == 64
    assert work["maximum_steward_minutes"] == 1920
    assert work["queue_overflow_state"] == "HUMAN_QUEUE_OVERFLOW"
    assert any(
        row["from_state"] == "HUMAN_QUEUE_OVERFLOW" and row["to_state"] == "CASE_HUMAN_QUEUE"
        for row in artifact["state_machine"]["transitions"]
    )

    weakened = _artifact()
    weakened["human_work_manifest"]["protected_high_risk_review_fraction"] = 0.5
    _reject(weakened, "protected review weakened")


def test_transition_receipts_are_hash_chained_and_append_only() -> None:
    artifact = _artifact()
    first = _transition_receipt(
        artifact, 0, "SOURCE_RIGHTS_BLOCKED", "SOURCE_RIGHTS_REVIEW_PENDING", "rights_evidence_supplied", None
    )
    second = _transition_receipt(
        artifact,
        1,
        "SOURCE_RIGHTS_REVIEW_PENDING",
        "SOURCE_ADMITTED",
        "operation_rights_verified",
        first["receipt_sha256"],
    )
    v3b.validate_transition_receipts([first, second], artifact)
    v3b.validate_transition_receipts([first, second, copy.deepcopy(first)], artifact)

    gap = copy.deepcopy(second)
    gap["sequence"] = 3
    gap["receipt_sha256"] = v3b.receipt_sha(gap)
    with pytest.raises(v3b.V3BError, match="sequence gap"):
        v3b.validate_transition_receipts([first, gap], artifact)

    wrong_previous = copy.deepcopy(second)
    wrong_previous["previous_receipt_sha256"] = "9" * 64
    wrong_previous["receipt_sha256"] = v3b.receipt_sha(wrong_previous)
    with pytest.raises(v3b.V3BError, match="previous hash mismatch"):
        v3b.validate_transition_receipts([first, wrong_previous], artifact)

    divergent = copy.deepcopy(first)
    divergent["failure_code"] = "changed"
    divergent["receipt_sha256"] = v3b.receipt_sha(divergent)
    with pytest.raises(v3b.V3BError, match="divergent transition receipt replay"):
        v3b.validate_transition_receipts([first, divergent], artifact)


def test_transition_from_state_and_contract_binding_are_enforced() -> None:
    artifact = _artifact()
    first = _transition_receipt(
        artifact, 0, "SOURCE_RIGHTS_BLOCKED", "SOURCE_RIGHTS_REVIEW_PENDING", "rights_evidence_supplied", None
    )
    wrong_from = _transition_receipt(
        artifact,
        1,
        "IDENTITY_PENDING",
        "IDENTITY_HUMAN_QUEUE",
        "model_budget_exhausted",
        first["receipt_sha256"],
    )
    with pytest.raises(v3b.V3BError, match="from-state mismatch"):
        v3b.validate_transition_receipts([first, wrong_from], artifact)

    wrong_contract = copy.deepcopy(first)
    wrong_contract["contract_sha256"] = "9" * 64
    wrong_contract["receipt_sha256"] = v3b.receipt_sha(wrong_contract)
    with pytest.raises(v3b.V3BError, match="contract drift"):
        v3b.validate_transition_receipts([wrong_contract], artifact)


def test_same_family_substitution_and_unguarded_gold_are_rejected() -> None:
    artifact = _artifact()
    first = _transition_receipt(
        artifact,
        0,
        "IDENTITY_PENDING",
        "IDENTITY_SUBSTITUTE_PENDING",
        "provider_failure_substitute_available",
        None,
    )
    first["role_id"] = "IDENTITY_LEAD"
    first["resolved_route"]["provider_family"] = "anthropic"
    first["receipt_sha256"] = v3b.receipt_sha(first)
    second = _transition_receipt(
        artifact,
        1,
        "IDENTITY_SUBSTITUTE_PENDING",
        "IDENTITY_PENDING",
        "family_safe_substitute_dispatched",
        first["receipt_sha256"],
    )
    second["role_id"] = "IDENTITY_LEAD"
    second["resolved_route"]["provider_family"] = "anthropic"
    second["substitute_used"] = True
    second["attempt_count"] = 1
    second["receipt_sha256"] = v3b.receipt_sha(second)
    with pytest.raises(v3b.V3BError, match="same-family substitution"):
        v3b.validate_transition_receipts([first, second], artifact)

    gold = _transition_receipt(
        artifact,
        0,
        "CASE_HUMAN_ADJUDICATED",
        "GOLD_ELIGIBLE_METADATA_ONLY",
        "all_gold_guards_satisfied",
        None,
    )
    gold["role_id"] = "HUMAN_STEWARD"
    gold["receipt_sha256"] = v3b.receipt_sha(gold)
    with pytest.raises(v3b.V3BError, match="gold transition guard"):
        v3b.validate_transition_receipts([gold], artifact)

    gold["guard_result"] = "pass"
    gold["receipt_sha256"] = v3b.receipt_sha(gold)
    with pytest.raises(v3b.V3BError, match="guard bundle incomplete"):
        v3b.validate_transition_receipts([gold], artifact)


def test_forbidden_body_and_heldout_fields_are_rejected() -> None:
    value = _artifact()
    value["incidence_manifest"]["heldout_membership"] = H
    _reject(value, "forbidden field")


def test_predecessor_byte_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = v3b.sha256_file

    def tampered(path: Path) -> str:
        return "0" * 64 if path == v3b.V3A_ARTIFACT_PATH else original(path)

    monkeypatch.setattr(v3b, "sha256_file", tampered)
    with pytest.raises(v3b.V3BError, match="predecessor byte drift"):
        v3b.verify_predecessors()
