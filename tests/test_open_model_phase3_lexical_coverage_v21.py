"""Fail-closed tests for the Phase 3 v2.1 lexical mechanics."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_functional_roles as roles
from scripts.projects.open_model_data import phase3_lexical_coverage as lexical


def _token(value: str) -> str:
    return value * 64


def _role_contract() -> dict[str, Any]:
    return json.loads(lexical.DEFAULT_ROLE_CONTRACT.read_text(encoding="utf-8"))


def _action(
    contract: dict[str, Any], *, action_kind: str, input_sha256: str, output_sha256: str
) -> dict[str, Any]:
    binding = roles.binding_for_role(contract, "disposition_auditor")
    execution = next(item for item in contract["functional_roles"] if item["role_id"] == "disposition_auditor")
    identity = {
        "role_id": binding["role_id"],
        "task_id": binding["task_id"],
        "input_manifest_sha256": input_sha256,
        "evaluation_cycle_id": contract["evaluation_cycle"]["evaluation_cycle_id"],
        "output_sha256": output_sha256,
        "status": "completed",
    }
    return {
        "receipt_id": "phase3_functional_action:" + lexical.sha256_value(identity),
        **identity,
        "action_kind": action_kind,
        "provider": lexical.AUDITOR_PROVIDER,
        "exact_model": execution["exact_model"],
        "model_family": execution["model_family"],
        "harness": execution["harness"],
        "base_contract_sha256": roles.BASE_SHA256,
        "amendment_sha256": roles.AMENDMENT_SHA256,
        "combined_contract_sha256": roles.COMBINED_SHA256,
        "functional_role_contract_sha256": lexical.sha256_file(lexical.DEFAULT_ROLE_CONTRACT),
        "conflict_graph_sha256": roles.conflict_graph_sha256(contract),
        "started_at": "2026-08-09T00:00:00Z",
        "completed_at": "2026-08-09T00:01:00Z",
    }


def _population(contract: dict[str, Any]) -> dict[str, Any]:
    locator = {
        "kind": "release_artifact_immutable_locator",
        "artifact_id": "release_fixture",
        "artifact_sha256": _token("a"),
        "path": "release.json",
        "anchor_sha256": _token("b"),
    }
    families = []
    for index, family_id in enumerate(sorted(lexical.LEXICAL_FAMILIES)):
        rows = []
        if index == 0:
            rows = [{
                "family_id": family_id,
                "unit_id": f"unit.{family_id}.{_token('c')}",
                "unit_sha256": _token("d"),
                "evidence_locators": [locator],
            }]
        families.append({
            "family_id": family_id,
            "structural_universe_sha256": _token("e"),
            "used_subset_total": len(rows),
            "rows": rows,
            "used_subset_population_sha256": lexical.sha256_value(rows),
        })
    base = {
        "schema_version": "phase3_lexical_used_subset_population_freeze_v2_1",
        "text_free": True,
        "source_universe_receipt_sha256": _token("1"),
        "source_universe_payload_manifest_sha256": _token("2"),
        "lexical_structural_freeze_sha256": _token("3"),
        "release_artifact_manifest_sha256": _token("4"),
        "release_files_sha256": _token("5"),
        "coverage_contract_sha256": _token("6"),
        **lexical._contract_bindings(contract),
        "producer_task_id": lexical.POPULATION_FREEZE_TASK,
        "implementation_sha256": lexical.implementation_sha256(),
        "repair_generation": 0,
        "families": families,
    }
    return {**base, "population_freeze_sha256": lexical.sha256_value(base)}


def _census(population: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    families = []
    for family in population["families"]:
        rows = [{**row, "decision_code": "agree"} for row in family["rows"]]
        families.append({
            "family_id": family["family_id"],
            "used_subset_total": len(rows),
            "rows": rows,
            "used_subset_census_sha256": lexical.sha256_value(rows),
        })
    result = {
        "schema_version": "phase3_lexical_complete_census_v2_1",
        "text_free": True,
        "source_universe_receipt_sha256": population["source_universe_receipt_sha256"],
        "source_universe_payload_manifest_sha256": population["source_universe_payload_manifest_sha256"],
        "lexical_structural_freeze_sha256": population["lexical_structural_freeze_sha256"],
        "coverage_contract_sha256": population["coverage_contract_sha256"],
        **lexical._contract_bindings(contract),
        "population_freeze_sha256": population["population_freeze_sha256"],
        "implementation_sha256": lexical.implementation_sha256(),
        "repair_generation": 0,
        "seed_required": False,
        "families": families,
    }
    action_input = lexical.sha256_value({
        "population_freeze_sha256": result["population_freeze_sha256"],
        "repair_generation": result["repair_generation"],
    })
    result["action_receipt"] = _action(
        contract,
        action_kind="lexical_complete_census",
        input_sha256=action_input,
        output_sha256=lexical.sha256_value(families),
    )
    return result


def test_v21_complete_census_is_task_and_action_bound() -> None:
    contract = _role_contract()
    population = _population(contract)
    census = _census(population, contract)
    result = lexical.validate_complete_census(census, population, role_contract=contract)
    assert result["complete_census"] is True
    assert result["family_count"] == 13
    assert result["status"] == "MECHANICS_ONLY_NOT_SOURCE_COVERAGE_READY"


@pytest.mark.parametrize(
    ("target", "field"),
    [
        ("census", "auditor_task_id"),
        ("census", "conflict_graph_sha256"),
        ("census", "combined_contract_sha256"),
        ("action", "task_id"),
        ("action", "input_manifest_sha256"),
        ("action", "receipt_id"),
    ],
)
def test_v21_complete_census_rejects_binding_tampering(target: str, field: str) -> None:
    contract = _role_contract()
    population = _population(contract)
    census = _census(population, contract)
    candidate = census if target == "census" else census["action_receipt"]
    candidate[field] = _token("0")
    with pytest.raises(lexical.LexicalCoverageError):
        lexical.validate_complete_census(census, population, role_contract=contract)


def test_controller_identity_census_is_not_current_evidence() -> None:
    contract = _role_contract()
    population = _population(contract)
    census = _census(population, contract)
    census["schema_version"] = "phase3_lexical_complete_census_v2"
    census["auditor_controller_identity_id"] = "controller_phase3_disposition_auditor_claude_01"
    census.pop("auditor_task_id")
    with pytest.raises(lexical.LexicalCoverageError):
        lexical.validate_complete_census(census, population, role_contract=contract)


def test_population_freeze_rejects_v1_role_contract_shape() -> None:
    contract = _role_contract()
    population = _population(contract)
    old_contract = {"root": {"controller_identity_id": "controller_root"}, "seats": []}
    with pytest.raises(lexical.LexicalCoverageError):
        lexical.validate_complete_census(_census(population, contract), population, role_contract=old_contract)


def test_nonagree_and_missing_family_still_fail_closed() -> None:
    contract = _role_contract()
    population = _population(contract)
    census = _census(population, contract)
    nonempty = next(item for item in census["families"] if item["rows"])
    nonempty["rows"][0]["decision_code"] = "disagree_invalid_attestation"
    with pytest.raises(lexical.LexicalCoverageError):
        lexical.validate_complete_census(census, population, role_contract=contract)
    census = _census(population, contract)
    census["families"].pop()
    with pytest.raises(lexical.LexicalCoverageError):
        lexical.validate_complete_census(census, population, role_contract=contract)


def test_action_identity_cannot_be_rehashed_after_task_tampering() -> None:
    contract = _role_contract()
    population = _population(contract)
    census = _census(population, contract)
    action = census["action_receipt"]
    action["task_id"] = "phase3-v2-1-rule-author-extraction"
    identity = {
        key: action[key]
        for key in ("role_id", "task_id", "input_manifest_sha256", "evaluation_cycle_id", "output_sha256", "status")
    }
    action["receipt_id"] = "phase3_functional_action:" + lexical.sha256_value(identity)
    with pytest.raises(lexical.LexicalCoverageError):
        lexical.validate_complete_census(census, population, role_contract=contract)


def test_population_hash_detects_binding_mutation() -> None:
    contract = _role_contract()
    population = _population(contract)
    census = _census(population, contract)
    candidate = deepcopy(population)
    candidate["combined_contract_sha256"] = _token("0")
    base = {key: value for key, value in candidate.items() if key != "population_freeze_sha256"}
    candidate["population_freeze_sha256"] = lexical.sha256_value(base)
    with pytest.raises(lexical.LexicalCoverageError):
        lexical.validate_complete_census(census, candidate, role_contract=contract)


def test_v21_lexical_schema_is_closed() -> None:
    contract = _role_contract()
    population = _population(contract)
    census = _census(population, contract)
    schema_path = lexical.DATA / "contracts/phase3_disposition_audit_bundle_v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    validator.validate(population)
    validator.validate(census)
    census["action_receipt"]["unexpected"] = True
    assert not validator.is_valid(census)
