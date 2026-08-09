from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_evaluation_reproduction as evaluation
from scripts.projects.open_model_data import phase3_functional_roles as roles


def _sha(char: str) -> str:
    return char * 64


def _action(
    role_contract: dict[str, Any],
    role_id: str,
    action_kind: str,
    input_sha256: str,
    output_sha256: str,
) -> dict[str, Any]:
    role = next(item for item in role_contract["functional_roles"] if item["role_id"] == role_id)
    action = {
        "role_id": role_id,
        "task_id": role["task_id"],
        "action_kind": action_kind,
        "provider": "local" if role_id == "scorer" else "zhipu",
        "exact_model": role["exact_model"],
        "model_family": role["model_family"],
        "harness": role["harness"],
        "input_manifest_sha256": input_sha256,
        "output_sha256": output_sha256,
        "evaluation_cycle_id": evaluation.EVALUATION_CYCLE_ID,
        "base_contract_sha256": roles.BASE_SHA256,
        "amendment_sha256": roles.AMENDMENT_SHA256,
        "combined_contract_sha256": roles.COMBINED_SHA256,
        "functional_role_contract_sha256": evaluation.sha256_file(evaluation.ROLE_CONTRACT_PATH),
        "conflict_graph_sha256": roles.conflict_graph_sha256(role_contract),
        "started_at": "2026-08-09T00:00:00Z",
        "completed_at": "2026-08-09T00:01:00Z",
        "status": "completed",
    }
    identity = {
        key: action[key]
        for key in ("role_id", "task_id", "input_manifest_sha256", "evaluation_cycle_id", "output_sha256", "status")
    }
    action["receipt_id"] = "phase3_functional_action:" + evaluation.sha256_value(identity)
    return action


def _bundle() -> dict[str, Any]:
    role_contract = json.loads(evaluation.ROLE_CONTRACT_PATH.read_text(encoding="utf-8"))
    evaluation_input = {
        "schema_version": evaluation.INPUT_SCHEMA_VERSION,
        "evaluation_cycle_id": evaluation.EVALUATION_CYCLE_ID,
        "fixed_release_task_id": evaluation.FIXED_RELEASE_TASK_ID,
        "fixed_release_sha256": _sha("1"),
        "heldout_evaluation_freeze_sha256": _sha("2"),
        "denominator_contract_sha256": _sha("3"),
        "threshold_contract_sha256": _sha("4"),
        "published_inputs_manifest_sha256": _sha("5"),
        "sealed_evaluator_interface_sha256": _sha("6"),
        "release_instructions_sha256": _sha("7"),
        "ukrainian_recipe_sha256": _sha("8"),
        "english_recipe_sha256": _sha("9"),
        "release_mutation_allowed": False,
        "threshold_mutation_allowed": False,
        "heldout_plaintext_exposed": False,
    }
    evaluation_input_sha = evaluation.sha256_value(evaluation_input)
    scorer_result = {
        "evaluation_input_manifest_sha256": evaluation_input_sha,
        "fixed_release_sha256": evaluation_input["fixed_release_sha256"],
        "heldout_evaluation_freeze_sha256": evaluation_input["heldout_evaluation_freeze_sha256"],
        "threshold_contract_sha256": evaluation_input["threshold_contract_sha256"],
        "metrics_sha256": _sha("a"),
        "rules_modified": False,
        "thresholds_modified": False,
        "heldout_plaintext_exported": False,
        "status": "completed",
    }
    scorer_result_sha = evaluation.sha256_value(scorer_result)
    outsider_input = {
        "schema_version": evaluation.OUTSIDER_INPUT_SCHEMA_VERSION,
        "evaluation_cycle_id": evaluation.EVALUATION_CYCLE_ID,
        "evaluation_input_manifest_sha256": evaluation_input_sha,
        "scorer_result_sha256": scorer_result_sha,
        "fixed_release_sha256": evaluation_input["fixed_release_sha256"],
        "published_inputs_manifest_sha256": evaluation_input["published_inputs_manifest_sha256"],
        "sealed_evaluator_interface_sha256": evaluation_input["sealed_evaluator_interface_sha256"],
        "release_instructions_sha256": evaluation_input["release_instructions_sha256"],
        "ukrainian_recipe_sha256": evaluation_input["ukrainian_recipe_sha256"],
        "english_recipe_sha256": evaluation_input["english_recipe_sha256"],
        "fresh_worktree_commit_sha": "b" * 40,
        "source_blind": True,
        "fresh_clean_worktree": True,
        "author_worktree_used": False,
        "private_heldout_plaintext_available": False,
        "public_canary_evidence_allowed": False,
    }
    outsider_input_sha = evaluation.sha256_value(outsider_input)
    reproduction = {
        "outsider_input_manifest_sha256": outsider_input_sha,
        "first_build_sha256": _sha("c"),
        "second_build_sha256": _sha("c"),
        "reproduced_export_sha256": _sha("c"),
        "scorer_metrics_sha256": scorer_result["metrics_sha256"],
        "input_bytes_preserved": True,
        "protected_material_preserved": True,
        "ukrainian_recipe_verified": True,
        "english_recipe_verified": True,
        "source_blind": True,
        "fresh_clean_worktree": True,
        "author_worktree_used": False,
        "private_heldout_plaintext_accessed": False,
        "canary_used_as_quality_coverage_or_completion_proof": False,
        "training_performed": False,
        "paid_compute_used": False,
        "hugging_face_mutated": False,
        "upload_performed": False,
        "outreach_performed": False,
        "no_phase4_actions": True,
        "status": "completed",
    }
    reproduction_sha = evaluation.sha256_value(reproduction)
    return {
        "schema_version": evaluation.SCHEMA_VERSION,
        "text_free": True,
        "contract_bindings": {
            "base_contract_sha256": roles.BASE_SHA256,
            "amendment_sha256": roles.AMENDMENT_SHA256,
            "combined_contract_sha256": roles.COMBINED_SHA256,
            "functional_role_contract_sha256": evaluation.sha256_file(evaluation.ROLE_CONTRACT_PATH),
            "conflict_graph_sha256": roles.conflict_graph_sha256(role_contract),
            "evaluation_cycle_id": evaluation.EVALUATION_CYCLE_ID,
        },
        "evaluation_input_manifest": evaluation_input,
        "evaluation_input_manifest_sha256": evaluation_input_sha,
        "scorer_result": scorer_result,
        "scorer_result_sha256": scorer_result_sha,
        "scorer_action_receipt": _action(
            role_contract,
            "scorer",
            evaluation.SCORER_ACTION_KIND,
            evaluation_input_sha,
            scorer_result_sha,
        ),
        "outsider_input_manifest": outsider_input,
        "outsider_input_manifest_sha256": outsider_input_sha,
        "reproduction_result": reproduction,
        "reproduction_result_sha256": reproduction_sha,
        "outsider_action_receipt": _action(
            role_contract,
            "outsider_reproducer",
            evaluation.OUTSIDER_ACTION_KIND,
            outsider_input_sha,
            reproduction_sha,
        ),
        "gate_claims": {
            "mechanics_verified": True,
            "engine_ready_claimed": False,
            "source_coverage_ready_claimed": False,
            "linguistically_validated_claimed": False,
            "consumer_proven_claimed": False,
            "phase4_authorized": False,
        },
    }


def test_valid_bundle_proves_mechanics_without_claiming_completion() -> None:
    result = evaluation.validate_bundle(_bundle())
    assert result["ok"] is True
    assert result["mechanics_verified"] is True
    assert result["consumer_proven"] is False
    assert result["phase4_authorized"] is False


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("evaluation_input_manifest", "fixed_release_sha256"), _sha("d")),
        (("evaluation_input_manifest", "heldout_evaluation_freeze_sha256"), _sha("e")),
        (("scorer_result", "rules_modified"), True),
        (("scorer_result", "thresholds_modified"), True),
        (("scorer_result", "heldout_plaintext_exported"), True),
        (("outsider_input_manifest", "author_worktree_used"), True),
        (("outsider_input_manifest", "private_heldout_plaintext_available"), True),
        (("outsider_input_manifest", "public_canary_evidence_allowed"), True),
        (("reproduction_result", "second_build_sha256"), _sha("d")),
        (("reproduction_result", "private_heldout_plaintext_accessed"), True),
        (("reproduction_result", "canary_used_as_quality_coverage_or_completion_proof"), True),
        (("reproduction_result", "training_performed"), True),
        (("reproduction_result", "paid_compute_used"), True),
        (("reproduction_result", "hugging_face_mutated"), True),
        (("reproduction_result", "upload_performed"), True),
        (("reproduction_result", "outreach_performed"), True),
    ],
)
def test_freeze_mutation_leakage_and_phase4_boundaries_fail_closed(
    path: tuple[str, str], value: Any,
) -> None:
    bundle = _bundle()
    bundle[path[0]][path[1]] = value
    with pytest.raises(evaluation.EvaluationReproductionError):
        evaluation.validate_bundle(bundle)


@pytest.mark.parametrize("receipt_name", ["scorer_action_receipt", "outsider_action_receipt"])
def test_action_receipt_identity_and_cycle_tampering_fail_closed(receipt_name: str) -> None:
    bundle = _bundle()
    bundle[receipt_name]["evaluation_cycle_id"] = "phase3-v2-1-evaluation-cycle-999"
    with pytest.raises(evaluation.EvaluationReproductionError):
        evaluation.validate_bundle(bundle)

    bundle = _bundle()
    bundle[receipt_name]["receipt_id"] = "phase3_functional_action:" + _sha("0")
    with pytest.raises(evaluation.EvaluationReproductionError, match="receipt ID"):
        evaluation.validate_bundle(bundle)


def test_outsider_and_scorer_roles_cannot_be_swapped() -> None:
    bundle = _bundle()
    bundle["outsider_action_receipt"] = copy.deepcopy(bundle["scorer_action_receipt"])
    with pytest.raises(evaluation.EvaluationReproductionError, match="task binding"):
        evaluation.validate_bundle(bundle)


def test_schema_is_nested_closed_and_controller_identity_is_not_current() -> None:
    schema = json.loads(evaluation.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    for definition in schema["$defs"].values():
        if definition.get("type") == "object":
            assert definition["additionalProperties"] is False

    bundle = _bundle()
    bundle["scorer_action_receipt"]["controller_identity_id"] = "controller_scorer"
    errors = list(Draft202012Validator(schema).iter_errors(bundle))
    assert errors


def test_cli_verifies_bundle_but_returns_mechanics_only(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(_bundle(), ensure_ascii=False), encoding="utf-8")
    assert evaluation.main([str(bundle_path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["mechanics_verified"] is True
    assert result["consumer_proven"] is False
