#!/usr/bin/env python3
"""Freeze reviewed Phase 3 rules into one deterministic, closed release.

This module never reads held-out labels or source bodies.  Its output manifest
is text-free, binds every prerequisite by independently re-hashed bytes, and
is the sole opening point accepted by the sealed evaluator interface.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_disposition_audit as disposition_audit
from scripts.projects.open_model_data import phase3_functional_roles as roles

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
DEFAULT_SCHEMA = DATA / "contracts/phase3_fixed_release_manifest_v1.schema.json"
DEFAULT_ROLE_CONTRACT = DATA / "evidence/correction_protection_functional_role_contract_v2_1.json"
DEFAULT_EVALUATION_CONTRACT = DATA / "evidence/correction_protection_evaluation_contract_v1.json"
SCHEMA_VERSION = "phase3_fixed_release_manifest_v1"
TASK_ID = "phase3-v2-1-fixed-release-freeze"
EVALUATION_CYCLE_ID = "phase3-v2-1-evaluation-cycle-001"
RELEASE_FILES = (
    "fixed-release-rules.jsonl",
    "denominator-contract.json",
    "threshold-contract.json",
    "published-inputs-manifest.json",
    "release-instructions.json",
    "ukrainian-recipe.json",
    "english-recipe.json",
    "fixed-release-manifest.json",
)


class FixedReleaseError(ValueError):
    """A prerequisite is incomplete, stale, or unsafe for release."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FixedReleaseError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def _regular(path: Path, label: str) -> None:
    try:
        state = path.lstat()
    except OSError as exc:
        raise FixedReleaseError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(state.st_mode) and not path.is_symlink(), f"{label} must be a regular non-symlink file")


def sha256_file(path: Path) -> str:
    _regular(path, "artifact")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path, label: str) -> dict[str, Any]:
    _regular(path, label)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FixedReleaseError(f"cannot read {label}: {path}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _read_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    _regular(path, label)
    rows: list[dict[str, Any]] = []
    try:
        for number, raw in enumerate(path.read_bytes().splitlines(), start=1):
            value = json.loads(raw.decode("utf-8"))
            require(isinstance(value, dict), f"{label} row {number} must be an object")
            rows.append(value)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixedReleaseError(f"cannot read {label}: {path}") from exc
    return rows


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _prepare_output_dir(path: Path) -> None:
    require(not path.is_symlink(), "release output directory may not be a symlink")
    path.mkdir(parents=True, exist_ok=True)
    require(path.is_dir(), "release output must be a directory")
    unexpected = {child.name for child in path.iterdir()} - set(RELEASE_FILES)
    require(not unexpected, f"release output has unexpected artifacts: {sorted(unexpected)}")


def _verify_role_contract(path: Path) -> tuple[dict[str, Any], str]:
    value = _read_json(path, "functional role contract")
    try:
        roles.verify_value(value)
    except roles.FunctionalRoleError as exc:
        raise FixedReleaseError(str(exc)) from exc
    require(value["evaluation_cycle"]["evaluation_cycle_id"] == EVALUATION_CYCLE_ID, "evaluation cycle drift")
    return value, sha256_file(path)


def _verify_audit_bundle_pins(bundle: Mapping[str, Any], ledger: Mapping[str, Any]) -> None:
    """Check audit-bundle content-address pins without re-running its decision.

    The independently run auditor is the only producer of the bundle.  This
    release stage deliberately verifies its content-addressed assertions but
    does not reproduce an audit decision or inspect audit samples.
    """

    required = {
        "schema_version", "text_free", "source_universe_receipt_sha256", "coverage_contract_sha256",
        "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
        "functional_role_contract_sha256", "conflict_graph_sha256", "disposition_ledger_sha256",
        "population_freeze_sha256", "seed_receipt_sha256s", "sample_manifest_sha256", "audit_results_sha256",
    }
    require(set(bundle) == required, "audit bundle is not closed")
    require(bundle["schema_version"] == "phase3_disposition_audit_bundle_v2_1" and bundle["text_free"] is True, "audit bundle is not a v2.1 text-free bundle")
    require(
        bundle["disposition_ledger_sha256"] == disposition_audit.sha256_value(ledger),
        "audit bundle disposition ledger binding drift",
    )
    require(
        bundle["base_contract_sha256"] == roles.BASE_SHA256
        and bundle["amendment_sha256"] == roles.AMENDMENT_SHA256
        and bundle["combined_contract_sha256"] == roles.COMBINED_SHA256,
        "audit bundle contract binding drift",
    )
    require(isinstance(bundle["seed_receipt_sha256s"], list) and bundle["seed_receipt_sha256s"], "audit bundle has no passed samples")
    for field, value in bundle.items():
        if field.endswith("sha256"):
            require(isinstance(value, str) and len(value) == 64, f"audit bundle hash is incomplete: {field}")


def _rules(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    unit_ids: set[str] = set()
    for row in rows:
        require(set(row) == {"unit_id", "unit_sha256", "artifact_sha256", "artifact", "consumer_views"}, "reviewed rule artifact shape drift")
        unit_id = row["unit_id"]
        require(isinstance(unit_id, str) and unit_id and unit_id not in unit_ids, "duplicate reviewed rule unit")
        unit_ids.add(unit_id)
        require(sha256_value(row["artifact"]) == row["artifact_sha256"], "reviewed rule artifact hash drift")
        require(isinstance(row["consumer_views"], list) and row["consumer_views"], "reviewed rule has no consumer view")
        rules.append(dict(row))
    return sorted(rules, key=lambda row: (str(row["artifact_sha256"]), str(row["unit_id"])))


def _verify_release_prerequisites(
    *,
    public_receipt: Mapping[str, Any],
    disposition_receipt: Mapping[str, Any],
    ledger: Mapping[str, Any],
    audit_bundle: Mapping[str, Any],
    heldout_receipt: Mapping[str, Any],
    comprehensive_label_bundle: Mapping[str, Any],
    freeze_receipt: Mapping[str, Any],
    role_contract: Mapping[str, Any],
    evaluation_contract: Mapping[str, Any],
) -> None:
    require(public_receipt.get("schema_version") == "phase3_source_production_public_receipt_v1" and public_receipt.get("review_complete") is True, "source-production review is incomplete")
    denominator = public_receipt.get("denominator")
    require(isinstance(denominator, Mapping) and denominator.get("input_total") == 67041, "source-production denominator drift")
    require(disposition_receipt.get("schema_version") == "phase3_source_disposition_receipt_v2_1", "wrong disposition receipt")
    disposition = disposition_receipt.get("disposition_ledger")
    require(isinstance(disposition, Mapping) and disposition.get("row_count") == 67041, "disposition ledger denominator drift")
    require(ledger.get("schema_version") == "phase3_disposition_ledger_v2_1" and ledger.get("text_free") is True, "disposition ledger is not audit-compatible")
    _verify_audit_bundle_pins(audit_bundle, ledger)
    require(heldout_receipt.get("schema_version") == "phase3_heldout_label_public_receipt_v1", "wrong heldout-label receipt")
    require(heldout_receipt.get("complete") is True and heldout_receipt.get("row_count") == 2000, "heldout labels are incomplete")
    required_label_bundle = {
        "schema_version", "text_free", "evaluation_cycle_id", "evaluation_freeze_receipt_sha256",
        "partition_manifest_sha256", "sealed_labels_sha256", "row_count", "clean_modern_row_count",
        "phenomenon_strata_row_count", "phenomenon_stratum_commitments", "complete",
        "frozen_before_rule_extraction", "receipt_sha256",
    }
    require(set(comprehensive_label_bundle) == required_label_bundle, "comprehensive label bundle is not closed")
    require(
        comprehensive_label_bundle.get("schema_version") == "phase3_comprehensive_sealed_label_bundle_v1"
        and comprehensive_label_bundle.get("text_free") is True,
        "wrong comprehensive label bundle",
    )
    require(
        comprehensive_label_bundle.get("row_count") == 9392
        and comprehensive_label_bundle.get("clean_modern_row_count") == 2000
        and comprehensive_label_bundle.get("phenomenon_strata_row_count") == 7392,
        "comprehensive labels must cover 2,000 clean_modern plus 7,392 phenomenon strata",
    )
    commitments = comprehensive_label_bundle.get("phenomenon_stratum_commitments")
    require(isinstance(commitments, Mapping) and len(commitments) == 12, "comprehensive label phenomena are incomplete")
    require(
        comprehensive_label_bundle.get("complete") is True
        and comprehensive_label_bundle.get("frozen_before_rule_extraction") is True,
        "comprehensive labels were not frozen before extraction",
    )
    require(freeze_receipt.get("schema_version") == "phase3_evaluation_partition_receipt_v1", "wrong evaluation-freeze receipt")
    require(freeze_receipt.get("aggregates", {}).get("clean_modern_candidate_total") == 2000, "clean_modern denominator drift")
    require(freeze_receipt.get("input_bindings", {}).get("evaluation_cycle_id") == EVALUATION_CYCLE_ID, "evaluation-freeze cycle drift")
    require(evaluation_contract.get("functional_role_evaluation_cycle", {}).get("evaluation_cycle_id") == EVALUATION_CYCLE_ID, "evaluation contract cycle drift")
    require(role_contract["evaluation_cycle"]["evaluation_cycle_id"] == EVALUATION_CYCLE_ID, "role contract cycle drift")


def build(
    *,
    reviewed_rule_artifacts_path: Path,
    source_production_public_receipt_path: Path,
    disposition_ledger_path: Path,
    disposition_receipt_path: Path,
    disposition_audit_bundle_path: Path,
    heldout_label_public_receipt_path: Path,
    comprehensive_sealed_label_bundle_path: Path,
    evaluation_freeze_receipt_path: Path,
    denominator_contract_path: Path,
    threshold_contract_path: Path,
    output_dir: Path,
    role_contract_path: Path = DEFAULT_ROLE_CONTRACT,
    evaluation_contract_path: Path = DEFAULT_EVALUATION_CONTRACT,
    schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    """Write a deterministic release only after every upstream closure pin holds."""

    role_contract, role_hash = _verify_role_contract(role_contract_path)
    evaluation_contract = _read_json(evaluation_contract_path, "evaluation contract")
    public_receipt = _read_json(source_production_public_receipt_path, "source-production public receipt")
    ledger = _read_json(disposition_ledger_path, "disposition ledger")
    disposition_receipt = _read_json(disposition_receipt_path, "disposition receipt")
    audit_bundle = _read_json(disposition_audit_bundle_path, "disposition-audit bundle")
    heldout_receipt = _read_json(heldout_label_public_receipt_path, "heldout-label public receipt")
    comprehensive_label_bundle = _read_json(comprehensive_sealed_label_bundle_path, "comprehensive sealed-label bundle")
    freeze_receipt = _read_json(evaluation_freeze_receipt_path, "evaluation-freeze receipt")
    _verify_release_prerequisites(
        public_receipt=public_receipt, disposition_receipt=disposition_receipt, ledger=ledger,
        audit_bundle=audit_bundle, heldout_receipt=heldout_receipt, comprehensive_label_bundle=comprehensive_label_bundle,
        freeze_receipt=freeze_receipt,
        role_contract=role_contract, evaluation_contract=evaluation_contract,
    )
    bundle_body = dict(comprehensive_label_bundle)
    claimed_bundle_hash = bundle_body.pop("receipt_sha256")
    require(claimed_bundle_hash == sha256_value(bundle_body), "comprehensive label bundle self-hash drift")
    require(
        comprehensive_label_bundle["evaluation_cycle_id"] == EVALUATION_CYCLE_ID
        and comprehensive_label_bundle["evaluation_freeze_receipt_sha256"] == sha256_file(evaluation_freeze_receipt_path),
        "comprehensive label bundle evaluation-freeze binding drift",
    )
    rules = _rules(_read_jsonl(reviewed_rule_artifacts_path, "reviewed rule artifacts"))
    require(
        public_receipt.get("reviewed_rule_artifacts_sha256") == sha256_file(reviewed_rule_artifacts_path),
        "source-production receipt does not bind the reviewed rule artifacts",
    )
    require(
        public_receipt.get("author_manifest_comprehensive_sealed_label_bundle_sha256")
        == sha256_file(comprehensive_sealed_label_bundle_path),
        "source-production receipt does not prove its author manifest was bound to the comprehensive label freeze",
    )
    rules_payload = b"".join(canonical_bytes(row) for row in rules)
    input_hashes = {
        "reviewed_rule_artifacts_sha256": sha256_file(reviewed_rule_artifacts_path),
        "source_production_public_receipt_sha256": sha256_file(source_production_public_receipt_path),
        "disposition_ledger_sha256": sha256_file(disposition_ledger_path),
        "disposition_receipt_sha256": sha256_file(disposition_receipt_path),
        "disposition_audit_bundle_sha256": sha256_file(disposition_audit_bundle_path),
        "heldout_label_public_receipt_sha256": sha256_file(heldout_label_public_receipt_path),
        "comprehensive_sealed_label_bundle_sha256": sha256_file(comprehensive_sealed_label_bundle_path),
        "evaluation_freeze_receipt_sha256": sha256_file(evaluation_freeze_receipt_path),
        "denominator_contract_sha256": sha256_file(denominator_contract_path),
        "threshold_contract_sha256": sha256_file(threshold_contract_path),
        "functional_role_contract_sha256": role_hash,
        "conflict_graph_sha256": roles.conflict_graph_sha256(role_contract),
        "evaluation_contract_sha256": sha256_file(evaluation_contract_path),
        "base_contract_sha256": roles.BASE_SHA256,
        "amendment_sha256": roles.AMENDMENT_SHA256,
        "combined_contract_sha256": roles.COMBINED_SHA256,
    }
    _prepare_output_dir(output_dir)
    paths = {name: output_dir / name for name in RELEASE_FILES}
    _atomic_write(paths["fixed-release-rules.jsonl"], rules_payload)
    _atomic_write(paths["denominator-contract.json"], denominator_contract_path.read_bytes())
    _atomic_write(paths["threshold-contract.json"], threshold_contract_path.read_bytes())
    published_inputs = {"schema_version": "phase3_published_inputs_manifest_v1", "text_free": True, "input_hashes": input_hashes, "rule_count": len(rules)}
    _atomic_write(paths["published-inputs-manifest.json"], canonical_bytes(published_inputs))
    instructions = {"schema_version": "phase3_release_instructions_v1", "text_free": True, "fixed_release_task_id": TASK_ID, "rules_mutable": False, "thresholds_mutable": False, "heldout_plaintext_available": False}
    ukrainian_recipe = {"schema_version": "phase3_recipe_v1", "language": "uk", "text_free": True, "fixed_release_task_id": TASK_ID, "rule_count": len(rules)}
    english_recipe = {"schema_version": "phase3_recipe_v1", "language": "en", "text_free": True, "fixed_release_task_id": TASK_ID, "rule_count": len(rules)}
    _atomic_write(paths["release-instructions.json"], canonical_bytes(instructions))
    _atomic_write(paths["ukrainian-recipe.json"], canonical_bytes(ukrainian_recipe))
    _atomic_write(paths["english-recipe.json"], canonical_bytes(english_recipe))
    artifact_hashes = {name: sha256_file(path) for name, path in paths.items() if name != "fixed-release-manifest.json"}
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "text_free": True,
        "fixed_release_task_id": TASK_ID,
        "evaluation_cycle_id": EVALUATION_CYCLE_ID,
        "input_hashes": input_hashes,
        "artifact_hashes": artifact_hashes,
        "rule_count": len(rules),
        "denominator": {
            "source_disposition_total": 67041,
            "sealed_evaluation_total": 9392,
            "sealed_clean_modern_total": 2000,
            "sealed_phenomenon_strata_total": 7392,
        },
        "gates": {
            "reviewed_rules_complete": True,
            "disposition_audit_bundle_pins_present": True,
            "heldout_labels_complete": True,
            "heldout_plaintext_published": False,
            "release_mutation_allowed": False,
            "source_blind_outsider_required": True,
        },
    }
    manifest["manifest_sha256"] = sha256_value(manifest)
    schema = _read_json(schema_path, "fixed-release schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda error: list(error.path))
    require(not errors, f"fixed-release schema violation: {errors[0].message if errors else ''}")
    _atomic_write(paths["fixed-release-manifest.json"], canonical_bytes(manifest))
    return manifest


def validate_manifest(path: Path, *, schema_path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    """Re-hash one fixed release and reject any mutable or private leakage."""

    manifest = _read_json(path, "fixed-release manifest")
    schema = _read_json(schema_path, "fixed-release schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda error: list(error.path))
    require(not errors, f"fixed-release schema violation: {errors[0].message if errors else ''}")
    body = dict(manifest)
    claimed = body.pop("manifest_sha256")
    require(claimed == sha256_value(body), "fixed-release manifest self-hash drift")
    require(
        manifest["gates"]["release_mutation_allowed"] is False
        and manifest["gates"]["heldout_labels_complete"] is True
        and manifest["gates"]["heldout_plaintext_published"] is False,
        "fixed release is not closed or text-free",
    )
    for name, expected in manifest["artifact_hashes"].items():
        require(name in RELEASE_FILES and name != "fixed-release-manifest.json", "unknown release artifact")
        require(sha256_file(path.parent / name) == expected, f"fixed-release artifact hash drift: {name}")
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-rule-artifacts", type=Path, required=True)
    parser.add_argument("--source-production-public-receipt", type=Path, required=True)
    parser.add_argument("--disposition-ledger", type=Path, required=True)
    parser.add_argument("--disposition-receipt", type=Path, required=True)
    parser.add_argument("--disposition-audit-bundle", type=Path, required=True)
    parser.add_argument("--heldout-label-public-receipt", type=Path, required=True)
    parser.add_argument("--comprehensive-sealed-label-bundle", type=Path, required=True)
    parser.add_argument("--evaluation-freeze-receipt", type=Path, required=True)
    parser.add_argument("--denominator-contract", type=Path, required=True)
    parser.add_argument("--threshold-contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--role-contract", type=Path, default=DEFAULT_ROLE_CONTRACT)
    parser.add_argument("--evaluation-contract", type=Path, default=DEFAULT_EVALUATION_CONTRACT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)
    try:
        manifest = build(**vars(args))
    except FixedReleaseError as exc:
        parser.error(str(exc))
    print(canonical_json({"ok": True, "manifest_sha256": manifest["manifest_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
