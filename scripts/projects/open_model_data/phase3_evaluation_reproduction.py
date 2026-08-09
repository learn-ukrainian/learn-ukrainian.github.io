#!/usr/bin/env python3
"""Verify Phase 3 scorer and outsider-reproduction receipts.

This is a public, text-free mechanics verifier. It never reads held-out
plaintext, computes linguistic labels, scores a release, or claims that the
scorer or outsider actions occurred merely because this verifier ran.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_functional_roles as functional_roles

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA_PATH = DATA / "contracts/phase3_evaluation_reproduction_bundle_v1.schema.json"
ROLE_CONTRACT_PATH = functional_roles.LEDGER_PATH
SCHEMA_VERSION = "phase3_evaluation_reproduction_bundle_v1"
INPUT_SCHEMA_VERSION = "phase3_evaluation_input_manifest_v1"
OUTSIDER_INPUT_SCHEMA_VERSION = "phase3_outsider_reproduction_input_manifest_v1"
EVALUATION_CYCLE_ID = "phase3-v2-1-evaluation-cycle-001"
FIXED_RELEASE_TASK_ID = "phase3-v2-1-fixed-release-freeze"
SCORER_ACTION_KIND = "score_fixed_release_against_sealed_heldout"
OUTSIDER_ACTION_KIND = "fresh_worktree_byte_identical_reproduction"
SHA256_RE = re.compile(r"[a-f0-9]{64}")
GIT_SHA_RE = re.compile(r"[a-f0-9]{40}")


class EvaluationReproductionError(ValueError):
    """A scorer or outsider receipt is stale, malformed, or unsafe."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationReproductionError(message)


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationReproductionError(f"cannot read {label}: {path}") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _validate_schema(bundle: Mapping[str, Any]) -> None:
    schema = read_json(SCHEMA_PATH, "evaluation-reproduction schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(bundle), key=lambda error: list(error.path))
    require(not errors, f"evaluation-reproduction schema violation: {errors[0].message if errors else ''}")


def _validate_timestamp(value: Any, label: str) -> datetime:
    require(isinstance(value, str) and value.endswith("Z"), f"{label} must be a UTC timestamp")
    try:
        return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise EvaluationReproductionError(f"{label} is not an ISO-8601 timestamp") from exc


def _role_bindings(role_contract: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    try:
        verified = functional_roles.verify_value(role_contract)
        bindings = {
            role_id: functional_roles.binding_for_role(verified, role_id)
            for role_id in ("scorer", "outsider_reproducer")
        }
    except functional_roles.FunctionalRoleError as exc:
        raise EvaluationReproductionError(str(exc)) from exc
    require(bindings["scorer"]["task_id"] != bindings["outsider_reproducer"]["task_id"], "scorer and outsider tasks must differ")
    require(
        functional_roles.tasks_conflict(verified, FIXED_RELEASE_TASK_ID, bindings["scorer"]["task_id"]),
        "role graph lacks fixed-release-to-scorer edge",
    )
    require(
        functional_roles.tasks_conflict(verified, FIXED_RELEASE_TASK_ID, bindings["outsider_reproducer"]["task_id"]),
        "role graph lacks fixed-release-to-outsider edge",
    )
    return bindings


def _validate_action_receipt(
    receipt: Mapping[str, Any],
    *,
    role_contract: Mapping[str, Any],
    role_contract_path: Path,
    actor: Mapping[str, str],
    action_kind: str,
    input_sha256: str,
    output_sha256: str,
) -> None:
    require(set(receipt) == set(functional_roles.ACTION_RECEIPT_FIELDS), "functional action receipt fields drift")
    require(receipt.get("role_id") == actor["role_id"] and receipt.get("task_id") == actor["task_id"], "functional action task binding mismatch")
    role = next(item for item in role_contract["functional_roles"] if item["role_id"] == actor["role_id"])
    require(
        all(receipt.get(field) == role[field] for field in ("exact_model", "model_family", "harness")),
        "functional action lane mismatch",
    )
    require(isinstance(receipt.get("provider"), str) and bool(receipt["provider"]), "functional action provider metadata is missing")
    require(receipt.get("action_kind") == action_kind, "functional action kind mismatch")
    require(receipt.get("input_manifest_sha256") == input_sha256, "functional action input mismatch")
    require(receipt.get("output_sha256") == output_sha256, "functional action output mismatch")
    require(receipt.get("evaluation_cycle_id") == EVALUATION_CYCLE_ID, "functional action evaluation-cycle mismatch")
    require(
        receipt.get("base_contract_sha256") == functional_roles.BASE_SHA256
        and receipt.get("amendment_sha256") == functional_roles.AMENDMENT_SHA256
        and receipt.get("combined_contract_sha256") == functional_roles.COMBINED_SHA256,
        "functional action contract binding mismatch",
    )
    require(
        receipt.get("functional_role_contract_sha256") == sha256_file(role_contract_path)
        and receipt.get("conflict_graph_sha256") == functional_roles.conflict_graph_sha256(role_contract),
        "functional action role-graph binding mismatch",
    )
    require(receipt.get("status") == "completed", "functional action is not complete")
    started = _validate_timestamp(receipt.get("started_at"), "functional action started_at")
    completed = _validate_timestamp(receipt.get("completed_at"), "functional action completed_at")
    require(started <= completed, "functional action timestamps are reversed")
    identity = {
        key: receipt[key]
        for key in ("role_id", "task_id", "input_manifest_sha256", "evaluation_cycle_id", "output_sha256", "status")
    }
    require(
        receipt.get("receipt_id") == "phase3_functional_action:" + sha256_value(identity),
        "functional action receipt ID mismatch",
    )


def validate_bundle(bundle: Mapping[str, Any], *, role_contract_path: Path = ROLE_CONTRACT_PATH) -> dict[str, Any]:
    """Validate one already-produced scorer/outsider evidence bundle."""

    _validate_schema(bundle)
    require(bundle["schema_version"] == SCHEMA_VERSION and bundle["text_free"] is True, "wrong schema or text boundary")

    role_contract = read_json(role_contract_path, "functional-role ledger")
    bindings = _role_bindings(role_contract)
    contract = bundle["contract_bindings"]
    require(
        contract
        == {
            "base_contract_sha256": functional_roles.BASE_SHA256,
            "amendment_sha256": functional_roles.AMENDMENT_SHA256,
            "combined_contract_sha256": functional_roles.COMBINED_SHA256,
            "functional_role_contract_sha256": sha256_file(role_contract_path),
            "conflict_graph_sha256": functional_roles.conflict_graph_sha256(role_contract),
            "evaluation_cycle_id": EVALUATION_CYCLE_ID,
        },
        "evaluation-reproduction contract bindings drift",
    )

    evaluation_input = bundle["evaluation_input_manifest"]
    require(evaluation_input["schema_version"] == INPUT_SCHEMA_VERSION, "wrong evaluation input manifest schema")
    require(evaluation_input["evaluation_cycle_id"] == EVALUATION_CYCLE_ID, "evaluation input cycle drift")
    require(evaluation_input["fixed_release_task_id"] == FIXED_RELEASE_TASK_ID, "fixed-release task drift")
    require(evaluation_input["release_mutation_allowed"] is False, "fixed release may not be mutated")
    require(evaluation_input["threshold_mutation_allowed"] is False, "evaluation thresholds may not be mutated")
    require(evaluation_input["heldout_plaintext_exposed"] is False, "held-out plaintext exposure is forbidden")
    for field in (
        "fixed_release_sha256",
        "heldout_evaluation_freeze_sha256",
        "denominator_contract_sha256",
        "threshold_contract_sha256",
        "published_inputs_manifest_sha256",
        "sealed_evaluator_interface_sha256",
        "release_instructions_sha256",
        "ukrainian_recipe_sha256",
        "english_recipe_sha256",
    ):
        require(SHA256_RE.fullmatch(evaluation_input[field]) is not None, f"invalid evaluation input hash: {field}")
    evaluation_input_sha = sha256_value(evaluation_input)
    require(bundle["evaluation_input_manifest_sha256"] == evaluation_input_sha, "evaluation input manifest hash mismatch")

    scorer_result = bundle["scorer_result"]
    require(scorer_result["evaluation_input_manifest_sha256"] == evaluation_input_sha, "scorer result input mismatch")
    require(scorer_result["fixed_release_sha256"] == evaluation_input["fixed_release_sha256"], "scorer release freeze mismatch")
    require(
        scorer_result["heldout_evaluation_freeze_sha256"] == evaluation_input["heldout_evaluation_freeze_sha256"],
        "scorer evaluation freeze mismatch",
    )
    require(scorer_result["threshold_contract_sha256"] == evaluation_input["threshold_contract_sha256"], "scorer threshold contract mismatch")
    require(scorer_result["rules_modified"] is False, "scorer modified rules under test")
    require(scorer_result["thresholds_modified"] is False, "scorer modified frozen thresholds")
    require(scorer_result["heldout_plaintext_exported"] is False, "scorer exported held-out plaintext")
    require(scorer_result["status"] == "completed", "scorer result is not complete")
    scorer_result_sha = sha256_value(scorer_result)
    require(bundle["scorer_result_sha256"] == scorer_result_sha, "scorer result hash mismatch")
    _validate_action_receipt(
        bundle["scorer_action_receipt"],
        role_contract=role_contract,
        role_contract_path=role_contract_path,
        actor=bindings["scorer"],
        action_kind=SCORER_ACTION_KIND,
        input_sha256=evaluation_input_sha,
        output_sha256=scorer_result_sha,
    )

    outsider_input = bundle["outsider_input_manifest"]
    require(outsider_input["schema_version"] == OUTSIDER_INPUT_SCHEMA_VERSION, "wrong outsider input manifest schema")
    require(outsider_input["evaluation_cycle_id"] == EVALUATION_CYCLE_ID, "outsider input cycle drift")
    require(outsider_input["evaluation_input_manifest_sha256"] == evaluation_input_sha, "outsider evaluation input mismatch")
    require(outsider_input["scorer_result_sha256"] == scorer_result_sha, "outsider scorer result mismatch")
    for field in (
        "fixed_release_sha256",
        "published_inputs_manifest_sha256",
        "sealed_evaluator_interface_sha256",
        "release_instructions_sha256",
        "ukrainian_recipe_sha256",
        "english_recipe_sha256",
    ):
        require(outsider_input[field] == evaluation_input[field], f"outsider input binding mismatch: {field}")
    require(GIT_SHA_RE.fullmatch(outsider_input["fresh_worktree_commit_sha"]) is not None, "invalid outsider worktree commit")
    require(outsider_input["source_blind"] is True, "outsider is not source-blind")
    require(outsider_input["fresh_clean_worktree"] is True, "outsider did not use a fresh clean worktree")
    require(outsider_input["author_worktree_used"] is False, "outsider used an author worktree")
    require(outsider_input["private_heldout_plaintext_available"] is False, "outsider received private held-out plaintext")
    require(outsider_input["public_canary_evidence_allowed"] is False, "public canaries may not prove completion")
    outsider_input_sha = sha256_value(outsider_input)
    require(bundle["outsider_input_manifest_sha256"] == outsider_input_sha, "outsider input manifest hash mismatch")

    reproduction = bundle["reproduction_result"]
    require(reproduction["outsider_input_manifest_sha256"] == outsider_input_sha, "reproduction result input mismatch")
    build_hashes = {
        reproduction["first_build_sha256"],
        reproduction["second_build_sha256"],
        reproduction["reproduced_export_sha256"],
    }
    require(len(build_hashes) == 1, "complete builds and outsider export are not byte-identical")
    require(reproduction["scorer_metrics_sha256"] == scorer_result["metrics_sha256"], "outsider metrics do not reproduce scorer metrics")
    required_true = (
        "input_bytes_preserved",
        "protected_material_preserved",
        "ukrainian_recipe_verified",
        "english_recipe_verified",
        "source_blind",
        "fresh_clean_worktree",
        "no_phase4_actions",
    )
    required_false = (
        "author_worktree_used",
        "private_heldout_plaintext_accessed",
        "canary_used_as_quality_coverage_or_completion_proof",
        "training_performed",
        "paid_compute_used",
        "hugging_face_mutated",
        "upload_performed",
        "outreach_performed",
    )
    require(all(reproduction[field] is True for field in required_true), "outsider reproduction lacks a required positive proof")
    require(all(reproduction[field] is False for field in required_false), "outsider reproduction crossed a forbidden boundary")
    require(reproduction["status"] == "completed", "outsider reproduction is not complete")
    reproduction_sha = sha256_value(reproduction)
    require(bundle["reproduction_result_sha256"] == reproduction_sha, "reproduction result hash mismatch")
    _validate_action_receipt(
        bundle["outsider_action_receipt"],
        role_contract=role_contract,
        role_contract_path=role_contract_path,
        actor=bindings["outsider_reproducer"],
        action_kind=OUTSIDER_ACTION_KIND,
        input_sha256=outsider_input_sha,
        output_sha256=reproduction_sha,
    )

    require(
        bundle["gate_claims"]
        == {
            "mechanics_verified": True,
            "engine_ready_claimed": False,
            "source_coverage_ready_claimed": False,
            "linguistically_validated_claimed": False,
            "consumer_proven_claimed": False,
            "phase4_authorized": False,
        },
        "evaluation-reproduction verifier made an unauthorized gate claim",
    )
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "mechanics_verified": True,
        "evaluation_cycle_id": EVALUATION_CYCLE_ID,
        "fixed_release_sha256": evaluation_input["fixed_release_sha256"],
        "heldout_evaluation_freeze_sha256": evaluation_input["heldout_evaluation_freeze_sha256"],
        "scorer_receipt_id": bundle["scorer_action_receipt"]["receipt_id"],
        "outsider_receipt_id": bundle["outsider_action_receipt"]["receipt_id"],
        "consumer_proven": False,
        "phase4_authorized": False,
    }


def verify(path: Path, *, role_contract_path: Path = ROLE_CONTRACT_PATH) -> dict[str, Any]:
    return validate_bundle(read_json(path, "evaluation-reproduction bundle"), role_contract_path=role_contract_path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Phase 3 scorer and outsider-reproduction receipts.")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--role-contract", type=Path, default=ROLE_CONTRACT_PATH)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        print(canonical_json(verify(args.bundle, role_contract_path=args.role_contract)))
    except EvaluationReproductionError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
