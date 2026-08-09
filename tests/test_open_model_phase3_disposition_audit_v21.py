"""Focused v2.1 migration checks for the text-free disposition audit runtime."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from scripts.projects.open_model_data import phase3_disposition_audit as audit


def _token(value: str) -> str:
    return value * 64


def _coverage() -> dict[str, Any]:
    return {"text_free": True, "mandatory_families": [{"family_id": "fixture_source", "audit": {
        "auditor_role_id": "disposition_auditor", "seed_owner_role_id": "disposition_auditor",
        "nonconverted_formula": "min(nonconverted_total,max(100,ceil(0.02*family_unit_total)))",
        "converted_formula": "min(converted_total,max(100,ceil(0.02*family_unit_total)))",
        "nonconverted_stratification": ["disposition_code", "document_or_edition_identity"],
        "converted_stratification": ["source_role", "claim_type", "document_or_edition_identity"],
        "sampling_without_replacement": True,
        "nonconverted_decision_codes": ["agree", "disagree_should_be_converted", "disagree_wrong_code", "insufficient_locator_evidence"],
        "converted_miss_codes": ["disagree_stub_conversion", "disagree_misclassified_role_or_claim", "disagree_unsupported_evidence", "disagree_non_actionable_rule"],
        "repair_invalidates_both_samples": True, "passing_sample_reuse_forbidden": True,
    }}]}


def _bindings() -> dict[str, str]:
    roles = audit.read_json(audit.DEFAULT_ROLE_CONTRACT)
    return audit._current_contract_bindings(roles, role_contract_path=audit.DEFAULT_ROLE_CONTRACT)


def _ledger(coverage: dict[str, Any], unit_ids: list[str]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    bindings = _bindings()
    units = [{"unit_id": unit_id, "unit_sha256": audit.sha256_value({"unit_id": unit_id}), "unit_locator_sha256": audit.sha256_value({"locator": unit_id})} for unit_id in unit_ids]
    rows = []
    for index, unit in enumerate(units):
        converted = bool(index % 2)
        rows.append({
            "unit_id": unit["unit_id"], "unit_sha256": unit["unit_sha256"], "unit_locator_sha256": unit["unit_locator_sha256"],
            "disposition_code": "converted" if converted else "not_rule_bearing",
            "document_or_edition_identity": f"edition_{index % 2}",
            "source_role": "rule_source" if converted else None, "claim_type": "claim" if converted else None,
            "canonical_content_identity": "content_fixture" if converted else None,
            "evidence_artifact_locators": ["artifact_fixture"] if converted else [], "consumer_view_ids": ["view_fixture"] if converted else [],
            "conversion_predicate_locator": "predicate_fixture" if converted else None,
            "reason_locator": None if converted else "reason_fixture", "repeated_reason_count": None if converted else len(unit_ids) // 2,
            "predicate_or_rationale_locator": None,
        })
    total = len(units)
    return ({
        "schema_version": "phase3_disposition_ledger_v2_1", "text_free": True,
        "source_universe_receipt_sha256": _token("a"), "source_universe_payload_manifest_sha256": _token("b"),
        "coverage_contract_sha256": audit.sha256_value(coverage),
        **{name: bindings[name] for name in ("base_contract_sha256", "amendment_sha256", "combined_contract_sha256", "functional_role_contract_sha256", "conflict_graph_sha256")},
        "repair_generation": 0,
        "families": [{"family_id": "fixture_source", "frozen_input_identity_total": total, "family_unit_total": total, "ledger_input_total": total, "disposition_row_sum": total, "ledger_universe_sha256": audit.source_family_universe_sha256(units), "audit_universe_sha256": audit.source_family_universe_sha256(units), "rows": rows}],
    }, units)


@pytest.fixture
def frozen(monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    coverage = _coverage()
    ledger, units = _ledger(coverage, [f"unit.fixture.{index:03d}" for index in range(8)])
    source_receipt = {"artifact_manifest": {"payload_manifest_sha256": _token("b")}}
    monkeypatch.setattr(audit, "_source_receipt", lambda _: (source_receipt, _token("a"), {"fixture_source": units}))
    monkeypatch.setattr(audit, "_first_containing_squash_merge", lambda *args, **kwargs: "f" * 40)
    return ledger, coverage, audit.read_json(audit.DEFAULT_ROLE_CONTRACT)


def _seed(freeze: dict[str, Any], *, population_kind: str = "nonconverted", **changes: object) -> dict[str, Any]:
    bindings = _bindings()
    population = freeze["families"][0][population_kind]
    entropy, seed, first = audit.derive_entropy_seed(freeze, audit_kind="source_disposition", family_id="fixture_source", population_kind=population_kind, population_universe_sha256=audit._population_hash(population["records"]))
    receipt: dict[str, Any] = {
        "schema_version": "phase3_disposition_audit_seed_receipt_v2_1", "text_free": True,
        "audit_round_id": "audit_round_fixture", "seed": seed, "seed_commitment_sha256": audit.sha256_bytes(seed.encode("ascii")),
        "seed_owner_role_id": bindings["auditor_role_id"], "auditor_task_id": bindings["auditor_task_id"],
        "source_universe_receipt_sha256": freeze["source_universe_receipt_sha256"], "disposition_ledger_sha256": freeze["disposition_ledger_sha256"], "population_freeze_sha256": freeze["population_freeze_sha256"], "coverage_contract_sha256": freeze["coverage_contract_sha256"],
        **{name: freeze[name] for name in ("base_contract_sha256", "amendment_sha256", "combined_contract_sha256", "functional_role_contract_sha256", "conflict_graph_sha256")},
        "repair_generation": freeze["repair_generation"], "results_recorded": False, "reroll_count": 0, "prior_sample_reused": False, "proposal_task_ids": [],
        "family_id": "fixture_source", "population_kind": population_kind, "population_sha256": audit._population_hash(population["records"]), "strata_allocation_sha256": audit.sha256_value(population["strata"]),
        "entropy_contract_version": audit.ENTROPY_CONTRACT_VERSION, "origin_main_ref": audit.ORIGIN_MAIN_REF, "first_containing_squash_merge_sha": first, "audit_kind": "source_disposition", "entropy_tuple": entropy, "entropy_tuple_sha256": seed,
        "seed_committer_task_id": bindings["auditor_task_id"], "seed_attestor_task_id": bindings["auditor_task_id"], "derivation_mode": "unique_sha256_or_abort",
    }
    receipt.update(changes)
    return receipt


def _action(sample_manifest_sha256: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    bindings = _bindings()
    role = next(item for item in audit.read_json(audit.DEFAULT_ROLE_CONTRACT)["functional_roles"] if item["role_id"] == bindings["auditor_role_id"])
    identity = {"role_id": bindings["auditor_role_id"], "task_id": bindings["auditor_task_id"], "input_manifest_sha256": sample_manifest_sha256, "evaluation_cycle_id": bindings["evaluation_cycle_id"], "output_sha256": audit.sha256_value(rows), "status": "completed"}
    return {
        "receipt_id": "phase3_functional_action:" + audit.sha256_bytes(audit.canonical_json(identity).encode("utf-8")),
        "role_id": bindings["auditor_role_id"], "task_id": bindings["auditor_task_id"], "action_kind": "disposition_audit_results", "provider": "anthropic",
        "exact_model": role["exact_model"], "model_family": role["model_family"], "harness": role["harness"],
        "input_manifest_sha256": sample_manifest_sha256, "output_sha256": audit.sha256_value(rows), "evaluation_cycle_id": bindings["evaluation_cycle_id"],
        **{name: bindings[name] for name in ("base_contract_sha256", "amendment_sha256", "combined_contract_sha256", "functional_role_contract_sha256", "conflict_graph_sha256")},
        "started_at": "2026-08-09T00:00:00Z", "completed_at": "2026-08-09T00:00:01Z", "status": "completed",
    }


def test_v21_flow_preserves_denominators_and_requires_task_bound_receipts(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    freeze = audit.freeze_audit_populations(ledger, coverage_contract=coverage, role_contract=roles)
    seeds = [_seed(freeze), _seed(freeze, population_kind="converted")]
    manifest = audit.emit_samples(freeze, seeds, ledger=ledger, coverage_contract=coverage, role_contract=roles)
    task_id = _bindings()["auditor_task_id"]
    rows = [{"family_id": sample["family_id"], "sample_kind": sample["sample_kind"], "unit_id": unit_id, "decision_code": "agree", "auditor_task_id": task_id, "evidence_artifact_locators": ["artifact_result"]} for sample in manifest["samples"] for unit_id in sample["unit_ids"]]
    results = {"schema_version": "phase3_disposition_audit_results_v2_1", "text_free": True, "sample_manifest_sha256": manifest["sample_manifest_sha256"], "population_freeze_sha256": manifest["population_freeze_sha256"], **{name: manifest[name] for name in ("base_contract_sha256", "amendment_sha256", "combined_contract_sha256", "functional_role_contract_sha256", "conflict_graph_sha256")}, "repair_generation": 0, "action_receipt": _action(manifest["sample_manifest_sha256"], rows), "results": rows}
    assert audit.validate_audit_results(results, manifest, ledger=ledger, population_freeze=freeze, seed_receipts=seeds, coverage_contract=coverage, role_contract=roles)["zero_miss"] is True
    bundle = {"schema_version": "phase3_disposition_audit_bundle_v2_1", "text_free": True, "source_universe_receipt_sha256": freeze["source_universe_receipt_sha256"], "coverage_contract_sha256": audit.sha256_value(coverage), **{name: manifest[name] for name in ("base_contract_sha256", "amendment_sha256", "combined_contract_sha256", "functional_role_contract_sha256", "conflict_graph_sha256")}, "disposition_ledger_sha256": audit.sha256_value(ledger), "population_freeze_sha256": freeze["population_freeze_sha256"], "seed_receipt_sha256s": sorted(audit.sha256_value(seed) for seed in seeds), "sample_manifest_sha256": manifest["sample_manifest_sha256"], "audit_results_sha256": audit.sha256_value(results)}
    schema = json.loads((audit.DATA / "contracts/phase3_disposition_audit_bundle_v1.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    for artifact in [ledger, freeze, *seeds, manifest, results, bundle]:
        validator.validate(artifact)
    assert audit.validate_bundle(bundle, ledger=ledger, population_freeze=freeze, seed_receipts=seeds, sample_manifest=manifest, results=results, coverage_contract=coverage, role_contract=roles)["bundle_verified"] is True
    forged = deepcopy(results)
    forged["action_receipt"]["receipt_id"] = "phase3_functional_action:" + _token("0")
    with pytest.raises(audit.AuditError, match="receipt ID"):
        audit.validate_audit_results(forged, manifest, ledger=ledger, population_freeze=freeze, seed_receipts=seeds, coverage_contract=coverage, role_contract=roles)


def test_v21_rejects_legacy_identity_forms_and_binding_drift(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    with pytest.raises(audit.AuditError, match="functional-role binding"):
        audit.validate_disposition_ledger({**ledger, "conflict_graph_sha256": _token("0")}, coverage_contract=coverage, role_contract=roles)
    freeze = audit.freeze_audit_populations(ledger, coverage_contract=coverage, role_contract=roles)
    legacy = _seed(freeze)
    legacy["schema_version"] = "phase3_disposition_audit_seed_receipt_v1"
    with pytest.raises(audit.AuditError, match="v1 is historical"):
        audit.validate_seed_receipt(legacy, freeze, role_contract=roles, family_id="fixture_source", population_kind="nonconverted")
    malformed = _seed(freeze)
    malformed["auditor_task_id"] = "phase3-v2-1-rule-author-extraction"
    with pytest.raises(audit.AuditError, match="assigned auditor"):
        audit.validate_seed_receipt(malformed, freeze, role_contract=roles, family_id="fixture_source", population_kind="nonconverted")


def test_v21_schema_accepts_current_ledger_and_rejects_v1_shape(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, _, _ = frozen
    schema = json.loads((audit.DATA / "contracts/phase3_disposition_audit_bundle_v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    validator.validate(ledger)
    legacy = deepcopy(ledger)
    legacy["schema_version"] = "phase3_disposition_ledger_v1"
    with pytest.raises(ValidationError):
        validator.validate(legacy)


def test_v21_rights_code_cannot_escape_the_denominator(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    ledger["families"][0]["rows"][0]["disposition_code"] = "rights_limited_locator_only"
    with pytest.raises(audit.AuditError, match="disposition code"):
        audit.validate_disposition_ledger(ledger, coverage_contract=coverage, role_contract=roles)
