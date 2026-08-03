"""Reconcile text-free model-readiness receipts into a deterministic product audit.

The auditor deliberately consumes only small JSON receipts and contracts.  It
does not open any model, silver, correction, or evaluation payload.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
CONTRACTS = DATA / "contracts"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
SCHEMA_PATH = CONTRACTS / "model_ready_product_audit_v1.schema.json"


class AuditError(ValueError):
    """Raised when receipt-only evidence cannot support the audit."""


@dataclass(frozen=True)
class AuditInputs:
    producer: Path
    mutation_tests: Path
    production: Path
    silver: Path
    faithful_cpt: Path
    modern_cpt: Path
    heldout_evaluation: Path
    silver_contract: Path
    correction_contract: Path
    correction_view_contract: Path
    preference_contract: Path
    quality_contract: Path
    inventory: Path
    schema: Path


def default_inputs(root: Path = ROOT) -> AuditInputs:
    data = root / "data/projects/open_model_data"
    contracts = data / "contracts"
    return AuditInputs(
        producer=root / "scripts/projects/open_model_data/audit_model_ready_receipts.py",
        mutation_tests=root / "tests/test_model_ready_receipt_audit.py",
        production=data / "model_views/model_ready_view_production_v1.json",
        silver=data / "silver/language_contact_silver_receipt_v1.json",
        faithful_cpt=data / "model_views/wikipedia_faithful_cpt_export_receipt_v1.json",
        modern_cpt=data / "model_views/wikipedia_modern_cpt_export_receipt_v1.json",
        heldout_evaluation=data / "model_views/heldout_evaluation_export_receipt_v1.json",
        silver_contract=contracts / "language_contact_silver_record_v1.schema.json",
        correction_contract=contracts / "correction_record_v1.schema.json",
        correction_view_contract=contracts / "correction_instruction_view_v1.schema.json",
        preference_contract=contracts / "preference_view_v1.schema.json",
        quality_contract=contracts / "quality_filter_view_v1.schema.json",
        inventory=data / "inventory/aggregate_summary_v1.json",
        schema=contracts / "model_ready_product_audit_v1.schema.json",
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise AuditError(f"cannot read input {path}: {exc}") from exc
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot read JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def artifact(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": sha256_file(path)}


def input_artifacts(inputs: AuditInputs) -> dict[str, dict[str, Any]]:
    root = inputs.production.parents[4]
    entries = {
        path.relative_to(root).as_posix(): artifact(path)
        for path in (
            inputs.producer,
            inputs.mutation_tests,
            inputs.production,
            inputs.silver,
            inputs.faithful_cpt,
            inputs.modern_cpt,
            inputs.heldout_evaluation,
            inputs.silver_contract,
            inputs.correction_contract,
            inputs.correction_view_contract,
            inputs.preference_contract,
            inputs.quality_contract,
            inputs.inventory,
            inputs.schema,
        )
    }
    return dict(sorted(entries.items()))


def _contract_const(contract: Mapping[str, Any], *path: str) -> Any:
    value: Any = contract
    for key in path:
        require(isinstance(value, Mapping) and key in value, f"contract field missing: {'.'.join(path)}")
        value = value[key]
    return value


def _empty_artifact(value: Mapping[str, Any], label: str) -> None:
    require(value == {"bytes": 0, "records": 0, "sha256": EMPTY_SHA256}, f"{label} is not empty")


def strict_artifact(value: Mapping[str, Any]) -> dict[str, Any]:
    return {"bytes": int(value["bytes"]), "records": int(value["records"]), "sha256": str(value["sha256"])}


def _validate_source_evidence(
    production: Mapping[str, Any],
    silver: Mapping[str, Any],
    faithful: Mapping[str, Any],
    modern: Mapping[str, Any],
    heldout: Mapping[str, Any],
    inventory: Mapping[str, Any],
    contracts: Mapping[str, Mapping[str, Any]],
) -> None:
    require(production.get("schema_version") == "model_ready_view_production_v1", "unexpected production receipt")
    require(silver.get("schema_version") == "language_contact_silver_receipt_v1", "unexpected silver receipt")
    require(faithful.get("view_kind") == modern.get("view_kind") == "continued_pretraining", "CPT receipt kind mismatch")
    require(heldout.get("view_kind") == "heldout_evaluation", "heldout receipt kind mismatch")
    require(faithful["counts"]["exported_records"] == 1028, "faithful CPT record count mismatch")
    require(modern["counts"]["exported_records"] == 1028, "modern CPT record count mismatch")
    require(heldout["counts"]["exported_records"] == 691, "heldout evaluation record count mismatch")
    public_inventory = inventory["distinct_content_totals"]["by_data_boundary"]["public_or_external_source"]
    require(public_inventory["content_units_by_unit_label"]["database_rows"] == 189_150, "inventory database-row count mismatch")
    require(public_inventory["lexical_words"] == 50_298_925, "inventory lexical-word count mismatch")
    require(inventory["safety_assertions"]["potential_training_admission_assets"] == 0, "historical inventory gate mismatch")
    require(inventory["eligibility_views"]["potential_training_admission"] == [], "historical inventory eligibility view changed")
    require(silver["output"]["records"] == 739_503, "silver record count mismatch")
    require(sum(silver["counts"]["by_disposition"].values()) == 739_503, "silver disposition arithmetic mismatch")
    for name in ("by_evidence_grade", "by_source_family", "by_period", "by_genre", "by_register"):
        require(sum(silver["counts"][name].values()) == 739_503, f"silver {name} arithmetic mismatch")
    require(silver["claims"] == {
        "export_admission_created": False,
        "human_gold_created": False,
        "human_review_claimed": False,
        "precision_or_recall_claimed": False,
        "publication_performed": False,
        "training_performed": False,
    }, "silver safety claims changed")
    require(production["evaluation_firewall"]["heldout_evaluation_view"]["artifact"]["records"] == 691, "evaluation binding mismatch")
    require(production["evaluation_firewall"]["exact_overlap_count"] == 0, "evaluation exact overlap is nonzero")
    require(production["evaluation_firewall"]["near_overlap_count"] == 0, "evaluation near overlap is nonzero")
    for lane_name, lane in production["silver_lanes"].items():
        require(lane_name in {"correction_instruction", "pairwise_preference", "quality_filter"}, "unknown silver lane")
        require(lane["state"] == "blocked", f"{lane_name} is not blocked")
        require(lane["eligible"] == lane["emitted"] == 0, f"{lane_name} is not empty")
        require(lane["blocked"] == 739_503, f"{lane_name} blocked count mismatch")
        require(lane["blocked_reasons"] == ["no_eligible_records"], f"{lane_name} reason mismatch")
        _empty_artifact(lane["artifact"], f"{lane_name} artifact")
        _empty_artifact(lane["receipt"], f"{lane_name} receipt")
    require(_contract_const(contracts["silver"], "properties", "claim_boundary", "properties", "model_training_or_export_eligible", "const") is False, "silver contract no longer denies export eligibility")
    require(_contract_const(contracts["correction"], "properties", "export_control", "properties", "model_training_or_export_eligible", "const") is False, "correction contract no longer denies export eligibility")
    require(
        _contract_const(contracts["correction_view"], "properties", "eligibility", "$ref") == "#/$defs/eligibility",
        "unexpected correction-view contract",
    )
    for name in ("preference", "quality"):
        require(contracts[name].get("additionalProperties") is False, f"{name} contract is not strict")


def build_receipt(inputs: AuditInputs) -> dict[str, Any]:
    production = read_json(inputs.production)
    silver = read_json(inputs.silver)
    faithful = read_json(inputs.faithful_cpt)
    modern = read_json(inputs.modern_cpt)
    heldout = read_json(inputs.heldout_evaluation)
    inventory = read_json(inputs.inventory)
    contracts = {
        "silver": read_json(inputs.silver_contract),
        "correction": read_json(inputs.correction_contract),
        "correction_view": read_json(inputs.correction_view_contract),
        "preference": read_json(inputs.preference_contract),
        "quality": read_json(inputs.quality_contract),
    }
    _validate_source_evidence(production, silver, faithful, modern, heldout, inventory, contracts)
    direct_inputs = input_artifacts(inputs)
    source_counts = silver["counts"]
    lanes = production["silver_lanes"]
    payloads = {
        "faithful_continued_pretraining": {"logical_path": "data/projects/open_model_data/model_views/wikipedia_faithful_cpt_view_v1.jsonl", "state": "not_present_in_checkout", "receipt_artifact": strict_artifact(faithful["output"])},
        "modern_continued_pretraining": {"logical_path": "data/projects/open_model_data/model_views/wikipedia_modern_cpt_view_v1.jsonl", "state": "not_present_in_checkout", "receipt_artifact": strict_artifact(modern["output"])},
        "heldout_evaluation": {"logical_path": "data/projects/open_model_data/model_views/heldout_evaluation_view_v1.jsonl", "state": "not_present_in_checkout", "receipt_artifact": strict_artifact(heldout["output"])},
    }
    input_root = inputs.production.parents[4]
    for payload in payloads.values():
        require(not (input_root / payload["logical_path"]).exists(), f"payload availability changed: {payload['logical_path']}")
    material = {
        "schema_version": "model_ready_product_audit_v1",
        "direct_inputs": direct_inputs,
        "validation": {"schema_valid": True, "source_receipts_reconciled": True, "payload_rows_read": False},
        "invariants": {
            "faithful_cpt_records": 1028,
            "modern_cpt_records": 1028,
            "silver_records": 739_503,
            "heldout_evaluation_records": 691,
            "silver_distributions_sum_to_output": True,
            "evaluation_isolated_from_non_evaluation_views": True,
            "silver_lanes_block_all_silver_records": True,
            "silver_and_correction_contracts_deny_training_or_export": True,
        },
        "product_truth": {
            "corpus_inventory": {
                "public_or_external_source": {
                    "database_rows": 189_150,
                    "database_rows_unit": "database_rows",
                    "lexical_words": 50_298_925,
                    "lexical_words_unit": "lexical_words",
                },
                "historical_combined_gate": {
                    "potential_training_admission_assets": 0,
                    "scope": "historical_existing_asset_inventory",
                },
                "capability_specific_wikipedia_cpt_rows": 1028,
                "interpretation": "The historical asset-inventory gate is distinct from later capability-specific Wikipedia CPT rows.",
            },
            "continued_pretraining": {
                "faithful": {"records": 1028, "record_learning_eligible": True, "operation_training_authorized": False},
                "modern": {"records": 1028, "record_learning_eligible": True, "operation_training_authorized": False},
            },
            "silver": {
                "records": 739_503,
                "distributions": {name: source_counts[name] for name in ("by_disposition", "by_evidence_grade", "by_source_family", "by_period", "by_genre", "by_register")},
                "record_learning_or_export_eligible": False,
                "lanes": copy.deepcopy(lanes),
            },
            "heldout_evaluation": {"records": 691, "learning_eligible": False, "isolation_verified": True},
        },
        "empty_lane_explanation": {
            "blocked_records": 739_503,
            "reason": "The current silver and correction contracts force model training/export eligibility false.",
            "interpretation": "This contract state does not determine whether source material is usable.",
            "reclassification_performed": False,
        },
        "payload_availability": payloads,
        "public_release_and_redistribution": {
            "status": "unknown",
            "publication_performed_in_receipts": False,
            "redistribution_permission_evidence": "unknown",
            "note": "No receipt evidence authorizes public release or redistribution; absence is not permission.",
        },
        "safety_claims": {
            "training_performed": False,
            "model_call_performed": False,
            "upload_performed": False,
            "publication_performed": False,
            "human_gold_created": False,
            "record_text_emitted": False,
        },
        "phase_1_entry_conditions": {
            "state": "ready",
            "satisfied": [
                "receipt_reconciliation",
                "no_reclassification",
                "receipt_only_no_payload_text",
                "evaluation_isolation",
                "mutation_canary_contract_bound",
            ],
        },
        "phase_1_remaining_deliverables": [
            "deterministic_document_signal_manifest",
            "planted_mutation_canary_harness",
            "lineage_and_limitations_receipt",
            "source_family_rights_state_input",
        ],
    }
    material["audit_id"] = "model-ready-product-audit:" + hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()
    validate_receipt(material, inputs.schema, inputs)
    return material


def validate_receipt(
    value: Mapping[str, Any],
    schema_path: Path = SCHEMA_PATH,
    inputs: AuditInputs | None = None,
) -> None:
    schema = read_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # jsonschema's schema error has no stable common base.
        raise AuditError(f"invalid audit schema: {exc}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        location = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise AuditError(f"audit schema violation at {location}: {errors[0].message}")
    expected_id_material = dict(value)
    audit_id = expected_id_material.pop("audit_id", None)
    require(isinstance(audit_id, str), "audit ID missing")
    expected_id = "model-ready-product-audit:" + hashlib.sha256(canonical_json(expected_id_material).encode("utf-8")).hexdigest()
    require(audit_id == expected_id, "audit ID does not bind receipt content")
    if inputs is not None:
        require(value["direct_inputs"] == input_artifacts(inputs), "direct input hashes do not match current files")
        source_silver = read_json(inputs.silver)
        require(
            value["product_truth"]["silver"]["distributions"]
            == {
                name: source_silver["counts"][name]
                for name in ("by_disposition", "by_evidence_grade", "by_source_family", "by_period", "by_genre", "by_register")
            },
            "silver distributions do not match the direct receipt",
        )
        require(
            value["product_truth"]["silver"]["lanes"] == read_json(inputs.production)["silver_lanes"],
            "silver lanes do not match the production receipt",
        )
    invariants = value["invariants"]
    truth = value["product_truth"]
    require(truth["continued_pretraining"]["faithful"]["records"] == invariants["faithful_cpt_records"], "faithful count invariant mismatch")
    require(truth["corpus_inventory"]["capability_specific_wikipedia_cpt_rows"] == invariants["faithful_cpt_records"], "inventory/CPT distinction mismatch")
    require(truth["continued_pretraining"]["modern"]["records"] == invariants["modern_cpt_records"], "modern count invariant mismatch")
    require(truth["silver"]["records"] == invariants["silver_records"], "silver count invariant mismatch")
    require(truth["heldout_evaluation"]["records"] == invariants["heldout_evaluation_records"], "evaluation count invariant mismatch")
    for distribution in truth["silver"]["distributions"].values():
        require(sum(distribution.values()) == truth["silver"]["records"], "silver distribution does not sum to records")
    for lane in truth["silver"]["lanes"].values():
        require(lane["state"] == "blocked" and lane["eligible"] == lane["emitted"] == 0, "silver lane truth mismatch")
        require(lane["blocked"] == truth["silver"]["records"], "silver lane blocked count mismatch")
        _empty_artifact(lane["artifact"], "silver lane artifact")
    explanation = value["empty_lane_explanation"]
    require(explanation["blocked_records"] == truth["silver"]["records"], "empty-lane count mismatch")
    require(explanation["reclassification_performed"] is False, "empty-lane audit reclassified data")
    require(value["public_release_and_redistribution"]["status"] == "unknown", "release status must remain unknown")
    require(value["public_release_and_redistribution"]["redistribution_permission_evidence"] == "unknown", "permission evidence must remain unknown")
    require(all(flag is False for flag in value["safety_claims"].values()), "safety claim became true")


def write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(receipt) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="canonical audit receipt path")
    parser.add_argument("--verify-existing", action="store_true", help="compare generated bytes to the existing output")
    args = parser.parse_args(argv)
    try:
        receipt = build_receipt(default_inputs())
        rendered = canonical_json(receipt) + "\n"
        if args.verify_existing:
            require(args.output.is_file(), f"canonical receipt is missing: {args.output}")
            require(args.output.read_text(encoding="utf-8") == rendered, "canonical receipt differs from current inputs")
        else:
            write_receipt(args.output, receipt)
    except AuditError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
