"""Adversarial, metadata-only checks for the Phase 3 P4 pilot (#7430).

These tests deliberately exercise the frozen, zero-row state.  Fixtures use
only identifiers, statuses, counters, and digests; they never open source or
corpus bodies, expose held-out membership, call a provider, or create data.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from scripts.projects.open_model_data import build_phase3_p4_pilot as p4

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
EXPECTED_INPUT_BINDINGS = {
    "p2_canonical_contracts": (
        "data/projects/open_model_data/evidence/phase3_p2_canonical_contracts_v1.json",
        "dc8dfdf207728ef386cea14ddb328289b2beee5159afb98bf076e5f117602ea3",
    ),
    "scope_circularity_firewall": (
        "data/projects/open_model_data/evidence/phase3_scope_circularity_firewall_v1.json",
        "4470448c6d0f665196375cf28255d7c092148700a99934b2d0dd1f43a8a3e24c",
    ),
    "modern_contact_channels": (
        "data/projects/open_model_data/admission/phase3_modern_contact_channels_v1.json",
        "573e7d9b7c25f1d09a874e70a6f1ac573d14c228c86f9a67d619e70b07a8160a",
    ),
    "historical_protection_channels": (
        "data/projects/open_model_data/admission/phase3_historical_protection_channels_v1.json",
        "837e826ca2a4eb005def3ef438ef7e4e29c58e87414ee80ab482ee3fe8591654",
    ),
    "source_capability_policy": (
        "data/projects/open_model_data/evidence/source_capability_policy_v1.json",
        "3a4a3af2edb1f7d68ebec8717e617ba8465ec26e74c29b408812ef1503aa6c60",
    ),
    "source_record_contract": (
        "data/projects/open_model_data/contracts/source_record_v1.schema.json",
        "db39258d365b939fb36c1a913b3911d9c185ae7c36e41265e04671be43e36b29",
    ),
    "corpus_admission_validator": (
        "scripts/projects/open_model_data/admit_existing_corpus.py",
        "07b8329cd2c160c15cf3f892d4743ff4e3985156883bd35bd0410f97da9c4278",
    ),
    "model_view_export_admission_gate": (
        "scripts/projects/open_model_data/model_view_exporter.py",
        "ad782f925e7468bb9608d0d870b8cd00828f5ee570a5c5e89d68621ce19f12c1",
    ),
}
EXPECTED_DENOMINATOR = {
    "source_units": 57,
    "unknown_rights_blockers": 39,
    "base_required_cells": 15,
    "composite_required_cells": 16,
    "coverage_blocked_cells": 14,
    "not_applicable_cells": 2,
    "rule_slots_R": 0,
}
EXPECTED_COUNTERS = {
    "dataset_rows_emitted": 0,
    "case_rows_emitted": 0,
    "correction_targets_emitted": 0,
    "gold_created": 0,
    "labels_created": 0,
    "provider_requests": 0,
    "training_rows_emitted": 0,
}
EXPECTED_CLAIMS = {
    "pilot_validated_claimed": False,
    "dataset_ready_claimed": False,
    "training_validated_claimed": False,
    "nonempty_pilot_constructed": False,
    "historical_or_dialect_modernized": False,
}
CASE_ROLES = {
    "correct_modern_production": (
        "applicability_scope",
        "correction_authority",
        "rights_provenance",
        "source_qualified_human_adjudication",
    ),
    "source_backed_correction": (
        "applicability_scope",
        "correction_authority",
        "rights_provenance",
        "source_qualified_human_adjudication",
    ),
    "minimal_contrast": (
        "applicability_scope",
        "minimal_contrast_authority",
        "rights_provenance",
        "source_qualified_human_adjudication",
    ),
    "protected_historical_context": (
        "protected_historical_identity",
        "rights_provenance",
        "source_qualified_human_adjudication",
    ),
    "protected_dialect_or_regional_context": (
        "protected_dialect_or_regional_identity",
        "rights_provenance",
        "source_qualified_human_adjudication",
    ),
    "abstention": (
        "abstention_or_not_applicable_authority",
        "rights_provenance",
        "source_qualified_human_adjudication",
    ),
    "not_applicable_with_evidence": (
        "abstention_or_not_applicable_authority",
        "rights_provenance",
        "source_qualified_human_adjudication",
    ),
    "coverage_blocked": (),
}


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _admission() -> dict[str, Any]:
    return _json(p4.OUTPUT_PATH)


def _contract() -> dict[str, Any]:
    return copy.deepcopy(p4.build_contract())


def _rehash(value: dict[str, Any]) -> None:
    value["receipt_sha256"] = p4.sha256_bytes(
        p4.canonical_bytes({key: item for key, item in value.items() if key != "receipt_sha256"})
    )


def _set_path(value: dict[str, Any], path: tuple[str, ...], replacement: Any) -> None:
    target: Any = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement


def _reject_contract(value: dict[str, Any]) -> None:
    _rehash(value)
    with pytest.raises(p4.P4PilotError):
        p4.validate_contract(value)


def _object_schemas(value: Any) -> list[Mapping[str, Any]]:
    found: list[Mapping[str, Any]] = []
    if isinstance(value, Mapping):
        if value.get("type") == "object":
            found.append(value)
        for child in value.values():
            found.extend(_object_schemas(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_object_schemas(child))
    return found


def _candidate(case_role: str = "correct_modern_production") -> dict[str, Any]:
    roles = list(CASE_ROLES[case_role])
    return {
        "case_role": case_role,
        "canonical_rule_slot_id": "p2_rule_slot:" + "a" * 64,
        "claim_appropriate_evidence_ref_ids": ["evidence:synthetic-qualified"],
        "claim_appropriate_evidence_roles": roles,
        "adjudication": {
            "actor_kind": "human",
            "authority_kind": "source_qualified_human_adjudication",
            "qualification_status": "registered_source_qualified_human",
            "record_sha256": "b" * 64,
            "registry_sha256": "c" * 64,
        },
        "rights_provenance": {
            "rights_status": "evidenced",
            "provenance_status": "complete",
            "rights_evidence_ref_ids": ["evidence:synthetic-rights"],
        },
        "source_identity": {
            "source_unit_identity_sha256": "d" * 64,
            "source_artifact_sha256": "e" * 64,
            "provenance_sha256": "f" * 64,
        },
        "firewall_clearance": {
            "status": "clear",
            "clearance_receipt_sha256": "1" * 64,
            "builder_receives_heldout_membership": False,
            "cycle007_clear": True,
            "heldout_clear": True,
            "fingerprint_clear": True,
        },
        "lineage": {
            "source_family": "source_qualified_ukrainian_artifact",
            "cycle007_related": False,
            "cycle007_derivative": False,
            "cycle007_fingerprint_match": False,
            "heldout_related": False,
            "provider_authored_gold": False,
            "uncertain_lineage": False,
            "modern_correction": False,
        },
    }


def test_current_pilot_is_exact_zero_row_nonadmitting_contract() -> None:
    value = _contract()
    schema = _json(p4.SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    assert list(Draft202012Validator(schema).iter_errors(value)) == []
    assert value == _admission()
    assert p4.validate_contract(value) == value
    assert p4.main(["--check"]) == 0
    assert value["status"] == "BLOCKED_PENDING_SOURCE_QUALIFIED_ADJUDICATION"
    assert value["denominator"] == EXPECTED_DENOMINATOR
    assert value["safety_counters"] == EXPECTED_COUNTERS
    assert value["claims"] == EXPECTED_CLAIMS
    assert value["candidate_metadata_contract"] == {
        "canonical_rule_slot_required": True,
        "claim_appropriate_evidence_required": True,
        "registered_source_qualified_human_adjudication_required": True,
        "rights_provenance_required": True,
        "source_identity_required": True,
        "firewall_clearance_required": True,
        "candidate_preflight_only": True,
        "future_nonempty_version_must_verify_adjudication_registry_membership": True,
        "future_nonempty_version_must_verify_adjudication_evidence_binding": True,
        "forbidden_body_fields": [
            "content",
            "gold",
            "heldout_membership",
            "label",
            "prompt",
            "provider_output",
            "source_body",
            "source_text",
            "text",
        ],
    }
    assert value["current_construction"] == {
        "dataset_case_rows": [],
        "dataset_case_row_count": 0,
        "construction_state": "no_admitted_cases",
        "candidate_admission_implemented": True,
    }
    assert "PILOT_VALIDATED" not in p4.canonical_bytes(value).decode("utf-8")


def test_frozen_input_bindings_and_schema_digest_are_exact() -> None:
    value = _contract()
    expected = {
        name: {"path": path, "sha256": digest}
        for name, (path, digest) in EXPECTED_INPUT_BINDINGS.items()
    }
    assert value["bindings"] == expected
    assert value["controlling_outcome_sha256"] == EXPECTED_OUTCOME_SHA256
    assert value["generator"]["path"] == "scripts/projects/open_model_data/build_phase3_p4_pilot.py"
    assert value["generator"]["implementation_sha256"] == p4.sha256_file(Path(p4.__file__).resolve())
    assert value["generator"]["schema_sha256"] == p4.sha256_file(p4.SCHEMA_PATH)


def test_schema_is_draft_2020_12_and_strict_at_every_object_boundary() -> None:
    schema = _json(p4.SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    objects = _object_schemas(schema)
    assert objects
    assert all(item.get("additionalProperties") is False for item in objects)

    top_level = _contract()
    top_level["invented_metadata"] = "opaque"
    _reject_contract(top_level)

    nested = _contract()
    nested["denominator"]["denominator_alias"] = 57
    _reject_contract(nested)


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("schema_version",), "phase3_p4_pilot_construction_v2"),
        (("status",), "PILOT_VALIDATED"),
        (("text_free",), False),
        (("controlling_outcome_sha256",), "0" * 64),
        (("denominator", "source_units"), 56),
        (("denominator", "unknown_rights_blockers"), 38),
        (("denominator", "base_required_cells"), 14),
        (("denominator", "composite_required_cells"), 15),
        (("denominator", "coverage_blocked_cells"), 13),
        (("denominator", "not_applicable_cells"), 1),
        (("denominator", "rule_slots_R"), 1),
        (("generator", "schema_sha256"), "0" * 64),
        (("bindings", "p2_canonical_contracts", "sha256"), "0" * 64),
        (("bindings", "modern_contact_channels", "sha256"), "f" * 64),
        (("candidate_metadata_contract", "candidate_preflight_only"), False),
        (("candidate_metadata_contract", "future_nonempty_version_must_verify_adjudication_registry_membership"), False),
        (("candidate_metadata_contract", "future_nonempty_version_must_verify_adjudication_evidence_binding"), False),
    ],
)
def test_validator_rejects_denominator_claim_and_parent_hash_drift(
    path: tuple[str, ...], replacement: Any
) -> None:
    value = _contract()
    _set_path(value, path, replacement)
    _reject_contract(value)


@pytest.mark.parametrize("name", sorted(EXPECTED_INPUT_BINDINGS))
def test_builder_fails_closed_when_any_bound_input_digest_drifts(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = {
        "p2_canonical_contracts": p4.P2_PATH,
        "scope_circularity_firewall": p4.FIREWALL_PATH,
        "modern_contact_channels": p4.MODERN_PATH,
        "historical_protection_channels": p4.HISTORICAL_PATH,
        "source_capability_policy": p4.CAPABILITY_POLICY_PATH,
        "source_record_contract": p4.SOURCE_RECORD_SCHEMA_PATH,
        "corpus_admission_validator": p4.CORPUS_ADMISSION_VALIDATOR_PATH,
        "model_view_export_admission_gate": p4.EXPORT_ADMISSION_GATE_PATH,
    }[name]
    original = p4.sha256_file

    def drift(path: Path) -> str:
        if Path(path) == target:
            return "0" * 64
        return original(path)

    monkeypatch.setattr(p4, "sha256_file", drift)
    with pytest.raises(p4.P4PilotError, match="hash drift"):
        p4.build_contract()


def test_schema_presence_is_required_and_schema_drift_invalidates_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "missing-schema.json"
    monkeypatch.setattr(p4, "SCHEMA_PATH", missing)
    with pytest.raises(p4.P4PilotError):
        p4.build_contract()

    monkeypatch.undo()
    modified = tmp_path / "modified-schema.json"
    schema = _json(p4.SCHEMA_PATH)
    schema["description"] = "metadata-only hostile schema mutation"
    modified.write_bytes(p4.canonical_bytes(schema))
    original_output = _admission()
    monkeypatch.setattr(p4, "SCHEMA_PATH", modified)
    try:
        check_result = p4.main(["--check"])
    except p4.P4PilotError:
        pass
    else:
        assert check_result != 0
    with pytest.raises(p4.P4PilotError):
        p4.validate_contract(original_output)


def test_rebuild_is_byte_identical_and_does_not_touch_checked_in_output(tmp_path: Path) -> None:
    before = p4.OUTPUT_PATH.read_bytes()
    rebuilt = p4.build_contract()
    assert p4.canonical_bytes(rebuilt) == before

    destination = tmp_path / "pilot-receipt.json"
    written = p4.write_output(destination)
    assert destination.read_bytes() == p4.canonical_bytes(written)
    assert p4.OUTPUT_PATH.read_bytes() == before


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("current_construction", "dataset_case_rows"), [{"case_role": "coverage_blocked"}]),
        (("current_construction", "dataset_case_row_count"), 1),
        (("safety_counters", "dataset_rows_emitted"), 1),
        (("safety_counters", "case_rows_emitted"), 1),
        (("safety_counters", "correction_targets_emitted"), 1),
        (("safety_counters", "gold_created"), 1),
        (("safety_counters", "labels_created"), 1),
        (("safety_counters", "provider_requests"), 1),
        (("safety_counters", "training_rows_emitted"), 1),
        (("claims", "nonempty_pilot_constructed"), True),
        (("claims", "pilot_validated_claimed"), True),
        (("claims", "dataset_ready_claimed"), True),
        (("claims", "training_validated_claimed"), True),
    ],
)
def test_zero_row_state_rejects_any_emitted_row_counter_or_vacuous_claim(
    path: tuple[str, ...], replacement: Any
) -> None:
    value = _contract()
    _set_path(value, path, replacement)
    _reject_contract(value)


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("residuals",), [
            "canonical_rule_slots_R_zero",
            "source_qualified_adjudication_registry_frozen_nonadmitting",
            "unknown_rights_blockers_39",
            "modern_contact_channels_blocked",
            "historical_and_dialect_protection_source_gaps_open",
            "hidden_blocker",
        ]),
        (("residuals",), ["hidden_blocker"] * 6),
        (("current_construction", "construction_state"), "blocked_without_reason"),
        (("current_construction", "candidate_admission_implemented"), False),
        (("claims", "historical_or_dialect_modernized"), True),
    ],
)
def test_blockers_cannot_be_hidden_removed_or_reclassified(
    path: tuple[str, ...], replacement: Any
) -> None:
    value = _contract()
    _set_path(value, path, replacement)
    _reject_contract(value)


def test_role_map_keeps_modern_and_protection_roles_structurally_distinct() -> None:
    role_map = p4.case_role_requirements()
    assert [item["case_role"] for item in role_map] == list(CASE_ROLES)
    for item in role_map:
        role = item["case_role"]
        assert tuple(item["claim_appropriate_evidence_roles"]) == CASE_ROLES[role]
        assert item["emits_dataset_case"] is (role != "coverage_blocked")
        assert item["may_be_modern_correction"] is (
            role in {"correct_modern_production", "source_backed_correction", "minimal_contrast"}
        )


def test_firewall_deny_list_and_atomic_split_requirements_are_exact() -> None:
    expected = {
        "builder_receives_heldout_membership": False,
        "cycle007_lineage_denied": True,
        "cycle007_derivatives_denied": True,
        "cycle007_fingerprints_denied": True,
        "heldout_lineage_denied": True,
        "provider_authored_gold_denied": True,
        "wikipedia_denied": True,
        "uncertain_lineage_denied": True,
        "atomic_split_requirements": [
            "source",
            "document",
            "work",
            "edition",
            "exact_duplicate_component",
            "near_duplicate_connected_component",
        ],
    }
    value = _contract()
    assert value["firewall_constraints"] == expected

    mutations: list[Callable[[dict[str, Any]], None]] = []
    for key in (
        "cycle007_lineage_denied",
        "cycle007_derivatives_denied",
        "cycle007_fingerprints_denied",
        "heldout_lineage_denied",
        "provider_authored_gold_denied",
        "wikipedia_denied",
        "uncertain_lineage_denied",
    ):
        mutations.append(lambda item, key=key: item["firewall_constraints"].__setitem__(key, False))
    mutations.append(
        lambda item: item["firewall_constraints"].__setitem__(
            "atomic_split_requirements", ["source", "document"]
        )
    )
    for mutate in mutations:
        candidate = copy.deepcopy(value)
        mutate(candidate)
        _reject_contract(candidate)


def test_candidate_admission_is_present_but_current_r_zero_stays_fail_closed() -> None:
    candidate = _candidate()
    with pytest.raises(p4.P4PilotError, match="rule universe"):
        p4.validate_candidate_admission(candidate)


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("adjudication", "actor_kind"), "model"),
        (("adjudication", "authority_kind"), "model_proposal"),
        (("adjudication", "qualification_status"), "unregistered"),
        (("adjudication", "record_sha256"), "not-a-sha"),
        (("claim_appropriate_evidence_ref_ids",), []),
        (("claim_appropriate_evidence_roles",), ["untyped_evidence"]),
        (("rights_provenance", "rights_status"), "unknown"),
        (("rights_provenance", "provenance_status"), "incomplete"),
        (("rights_provenance", "rights_evidence_ref_ids"), []),
        (("source_identity", "source_artifact_sha256"), "fake-source"),
        (("firewall_clearance", "status"), "blocked"),
        (("firewall_clearance", "builder_receives_heldout_membership"), True),
        (("firewall_clearance", "cycle007_clear"), False),
        (("firewall_clearance", "heldout_clear"), False),
        (("firewall_clearance", "fingerprint_clear"), False),
        (("lineage", "source_family"), "wikipedia"),
        (("lineage", "cycle007_related"), True),
        (("lineage", "cycle007_derivative"), True),
        (("lineage", "cycle007_fingerprint_match"), True),
        (("lineage", "heldout_related"), True),
        (("lineage", "provider_authored_gold"), True),
        (("lineage", "uncertain_lineage"), True),
        (("canonical_rule_slot_id",), "script-as-identity"),
        (("canonical_rule_slot_id",), "p2_rule_slot:" + "A" * 64),
        (("canonical_rule_slot_id",), "p2_rule_slot:" + "a" * 63),
        (("claim_appropriate_evidence_ref_ids",), ["evidence:duplicate", "evidence:duplicate"]),
        (("claim_appropriate_evidence_ref_ids",), ["evidence:z", "evidence:a"]),
        (("rights_provenance", "rights_evidence_ref_ids"), ["evidence:duplicate", "evidence:duplicate"]),
        (("rights_provenance", "rights_evidence_ref_ids"), ["evidence:z", "evidence:a"]),
        (("lineage", "source_family"), "source family"),
        (("lineage", "source_family"), ""),
        (("lineage", "source_family"), "x"),
        (("lineage", "source_family"), "Source_family"),
        (("lineage", "cycle007_related"), 0),
    ],
)
def test_future_candidate_rejects_fake_authority_evidence_rights_and_denied_lineage(
    path: tuple[str, ...], replacement: Any
) -> None:
    candidate = _candidate()
    _set_path(candidate, path, replacement)
    with pytest.raises(p4.P4PilotError):
        p4.validate_candidate_admission(candidate)


@pytest.mark.parametrize(
    "forbidden_key",
    sorted(
        {
            "content",
            "source_body",
            "source_text",
            "text",
            "gold",
            "label",
            "prompt",
            "provider_output",
            "heldout_membership",
        }
    ),
)
def test_candidate_metadata_rejects_body_or_provider_fields(forbidden_key: str) -> None:
    candidate = _candidate()
    candidate[forbidden_key] = "opaque"  # type: ignore[index]
    with pytest.raises(p4.P4PilotError):
        p4.validate_candidate_admission(candidate)


@pytest.mark.parametrize(
    ("nested", "key", "replacement"),
    [
        ("adjudication", "registry_sha256", "unregistered"),
        ("source_identity", "identity_basis", "script_only"),
        ("source_identity", "cycle007_fingerprint", "a" * 64),
        ("firewall_clearance", "cycle007_derivative", True),
        ("lineage", "identity_candidate", "script_only"),
    ],
)
def test_candidate_rejects_script_identity_and_cycle007_identity_derivative_fingerprint(
    nested: str, key: str, replacement: Any
) -> None:
    candidate = _candidate()
    candidate[nested][key] = replacement  # type: ignore[index]
    with pytest.raises(p4.P4PilotError):
        p4.validate_candidate_admission(candidate)


@pytest.mark.parametrize("case_role", ["protected_historical_context", "protected_dialect_or_regional_context"])
def test_historical_and_dialect_protection_roles_cannot_be_modern_corrections(case_role: str) -> None:
    candidate = _candidate(case_role)
    candidate["lineage"]["modern_correction"] = True  # type: ignore[index]
    with pytest.raises(p4.P4PilotError, match="modern correction"):
        p4.validate_candidate_admission(candidate)


def test_model_proposal_cannot_be_promoted_by_extra_or_replaced_adjudication_metadata() -> None:
    extra = _candidate()
    extra["model_proposal"] = {"proposal_id": "synthetic"}
    with pytest.raises(p4.P4PilotError):
        p4.validate_candidate_admission(extra)

    replaced = _candidate()
    replaced["adjudication"] = {
        "actor_kind": "human",
        "authority_kind": "source_qualified_human_adjudication",
        "qualification_status": "registered_source_qualified_human",
        "record_sha256": "b" * 64,
        "registry_sha256": "c" * 64,
        "model_proposal_sha256": "d" * 64,
    }
    with pytest.raises(p4.P4PilotError):
        p4.validate_candidate_admission(replaced)


def test_candidate_requires_exact_source_identity_fields_and_no_missing_provenance() -> None:
    for key in ("source_unit_identity_sha256", "source_artifact_sha256", "provenance_sha256"):
        candidate = _candidate()
        del candidate["source_identity"][key]
        with pytest.raises(p4.P4PilotError):
            p4.validate_candidate_admission(candidate)

    candidate = _candidate()
    del candidate["rights_provenance"]["provenance_status"]
    with pytest.raises(p4.P4PilotError):
        p4.validate_candidate_admission(candidate)


def test_no_pilot_validation_can_be_claimed_from_model_agreement_or_schema_only() -> None:
    value = _contract()
    value["claims"]["pilot_validated_claimed"] = True  # type: ignore[index]
    value["claims"]["dataset_ready_claimed"] = True  # type: ignore[index]
    value["safety_counters"]["provider_requests"] = 1  # type: ignore[index]
    _reject_contract(value)


def test_schema_rejects_uppercase_or_noncanonical_hashes_before_contract_comparison() -> None:
    value = _contract()
    value["controlling_outcome_sha256"] = EXPECTED_OUTCOME_SHA256.upper()
    with pytest.raises(ValidationError):
        Draft202012Validator(_json(p4.SCHEMA_PATH)).validate(value)
    with pytest.raises(p4.P4PilotError):
        p4.validate_contract(value)
