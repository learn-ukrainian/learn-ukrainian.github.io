"""V4 A2 source-operation admission is metadata-only and denominator-stable."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_a2_source_operation_admission_receipt_v1.schema.json"
V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"
V3_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
EXPECTED_QUOTAS = {
    "standard_correct": 15,
    "correction": 15,
    "literary": 15,
    "dialect_regional": 15,
    "archaic_historical": 15,
    "mixing": 10,
    "quotation_interference": 10,
    "abstention": 5,
}
REQUIRED_OPERATIONS = {
    "retention",
    "deterministic_local_analysis",
    "transmission_to_external_model_or_service",
    "derivation_of_annotations_or_examples",
    "training_use",
    "publication",
    "redistribution",
}
FORBIDDEN_KEYS = {
    "content",
    "text",
    "source_body",
    "source_text",
    "prompt",
    "label",
    "gold",
    "heldout_membership",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _receipt() -> dict[str, Any]:
    return _load(RECEIPT)


def _validator() -> Draft202012Validator:
    schema = _load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _errors(value: dict[str, Any]) -> list[object]:
    return sorted(_validator().iter_errors(value), key=lambda error: list(error.path))


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value)) if value else set()
    return set()


def test_a2_source_operation_schema_and_v4_control_binding() -> None:
    receipt = _receipt()

    assert not _errors(receipt)
    assert receipt["controlling_outcome_sha256"] == V4_SHA256
    assert receipt["status"] == "A2_SOURCE_OPERATION_RECEIPT_COMPLETE"
    assert receipt["text_free"] is True

    changed = copy.deepcopy(receipt)
    changed["controlling_outcome_sha256"] = "0" * 64
    assert _errors(changed)


def test_a2_source_operation_bindings_match_the_exact_inventory_inputs() -> None:
    receipt = _receipt()

    for binding in receipt["bindings"].values():
        bound_path = ROOT / binding["path"]
        assert bound_path.is_file()
        assert hashlib.sha256(bound_path.read_bytes()).hexdigest() == binding["sha256"]

    assert receipt["bindings"]["historical_protection_channels"]["historical_only"] is True
    assert receipt["bindings"]["modern_contact_channels"]["historical_only"] is True
    assert receipt["bindings"]["historical_p4_receipt"]["historical_only"] is True


def test_a2_source_operation_preserves_all_eight_frozen_strata_with_residuals() -> None:
    receipt = _receipt()
    denominator = {
        entry["stratum"]: entry["frozen_slots"]
        for entry in receipt["frozen_denominator"]["strata"]
    }
    coverage = {
        entry["stratum"]: entry
        for entry in receipt["stratum_coverage_map"]
    }
    residuals = {entry["residual_id"]: entry for entry in receipt["residuals"]}

    assert receipt["frozen_denominator"]["total_slots"] == 100
    assert denominator == EXPECTED_QUOTAS
    assert set(coverage) == set(EXPECTED_QUOTAS)
    assert sum(entry["frozen_slots"] for entry in coverage.values()) == 100

    empty_support = {
        stratum
        for stratum, entry in coverage.items()
        if not entry["supporting_existing_source_unit_ids"]
    }
    assert empty_support == {"dialect_regional", "mixing", "abstention"}

    for stratum, entry in coverage.items():
        assert entry["frozen_slots"] == EXPECTED_QUOTAS[stratum]
        assert entry["supporting_existing_source_unit_ids"] or entry["residual_ids"]
        assert set(entry["residual_ids"]) <= set(residuals)
        for residual_id in entry["residual_ids"]:
            residual = residuals[residual_id]
            assert residual["subject_kind"] == "stratum"
            assert residual["subject_id"] == stratum
            assert residual["reason_code"] in {
                "source_incomplete",
                "rights_unknown",
                "coverage_blocked",
            }
            assert residual["owner_role"]
            assert residual["next_action"]
            assert residual["retryability"] in {"retryable", "not_retryable"}


def test_a2_source_operation_ledger_is_per_unit_and_per_operation() -> None:
    receipt = _receipt()
    ledger = receipt["source_operation_ledger"]

    assert len(ledger) == receipt["inventory_reconciliation"]["a2_candidate_source_units"]
    assert len({entry["source_unit_id"] for entry in ledger}) == len(ledger)
    assert set(receipt["operations"]) == REQUIRED_OPERATIONS

    unknown_or_denied = []
    for source_unit in ledger:
        operation_rights = source_unit["operation_rights"]
        assert set(operation_rights) == REQUIRED_OPERATIONS
        assert source_unit["candidate_strata"]
        for operation, decision in operation_rights.items():
            assert decision["value"] in {"allowed", "denied", "unknown", "scope_bound"}
            assert decision["evidence_refs"]
            assert decision["scope"]
            if decision["value"] in {"unknown", "denied"}:
                unknown_or_denied.append((source_unit, operation, decision))
                assert decision["owner_role"]
                assert decision["next_action"]
                assert decision["retryability"] in {"retryable", "not_retryable"}

    assert unknown_or_denied
    assert receipt["safety_assertions"]["unknown_operations_global_block"] is False
    for source_unit, _operation, _decision in unknown_or_denied:
        assert any(
            decision["value"] in {"allowed", "scope_bound"}
            for decision in source_unit["operation_rights"].values()
        )


def test_a2_source_operation_receipt_is_payload_free_and_not_v3_controlled() -> None:
    receipt = _receipt()
    serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)

    assert not _all_keys(receipt) & FORBIDDEN_KEYS
    assert V3_SHA256 not in serialized
    assert receipt["safety_assertions"]["historical_v3_control_not_used"] is True
    assert receipt["safety_assertions"]["prebuilder_state_claimed"] is False
    assert receipt["safety_assertions"]["later_release_state_claimed"] is False
    assert receipt["execution_counters"] == {
        "dataset_rows_emitted": 0,
        "new_source_fetches": 0,
        "external_service_transmissions": 0,
        "annotation_or_example_derivations": 0,
        "publication_events": 0,
        "redistribution_events": 0,
        "training_events": 0,
    }
