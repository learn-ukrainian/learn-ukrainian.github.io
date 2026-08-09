from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_evaluation_reproduction as evaluation
from scripts.projects.open_model_data import phase3_functional_roles as roles


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


def _run_git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()


def _artifact_root(tmp_path: Path) -> tuple[Path, dict[str, dict[str, str]]]:
    root = tmp_path / "outsider-worktree"
    proof = root / "proof"
    proof.mkdir(parents=True)
    contents = {
        "fixed_release": b"fixed release bytes\n",
        "heldout_evaluation_freeze_container": b"sealed heldout container bytes\n",
        "denominator_contract": b"denominator contract bytes\n",
        "threshold_contract": b"threshold contract bytes\n",
        "published_inputs_manifest": b"published inputs bytes\n",
        "sealed_evaluator_interface": b"sealed interface bytes\n",
        "release_instructions": b"release instructions bytes\n",
        "ukrainian_recipe": b"ukrainian recipe bytes\n",
        "english_recipe": b"english recipe bytes\n",
        "scorer_metrics": b"scorer metrics bytes\n",
        "first_build": b"byte-identical reproduced export\n",
        "second_build": b"byte-identical reproduced export\n",
        "reproduced_export": b"byte-identical reproduced export\n",
    }
    locators: dict[str, dict[str, str]] = {}
    for artifact_id, content in contents.items():
        relative_path = f"proof/{artifact_id}.bin"
        artifact = root / relative_path
        artifact.write_bytes(content)
        locators[artifact_id] = {
            "relative_path": relative_path,
            "sha256": evaluation.sha256_file(artifact),
        }
    _run_git("init", cwd=root)
    _run_git("config", "user.email", "test@example.invalid", cwd=root)
    _run_git("config", "user.name", "Phase 3 test", cwd=root)
    _run_git("add", "proof", cwd=root)
    _run_git("commit", "-m", "test artifacts", cwd=root)
    return root, locators


def _bundle(tmp_path: Path) -> tuple[dict[str, Any], Path]:
    artifact_root, locators = _artifact_root(tmp_path)
    role_contract = json.loads(evaluation.ROLE_CONTRACT_PATH.read_text(encoding="utf-8"))
    evaluation_input = {
        "schema_version": evaluation.INPUT_SCHEMA_VERSION,
        "evaluation_cycle_id": evaluation.EVALUATION_CYCLE_ID,
        "fixed_release_task_id": evaluation.FIXED_RELEASE_TASK_ID,
        "fixed_release_sha256": locators["fixed_release"]["sha256"],
        "heldout_evaluation_freeze_sha256": locators["heldout_evaluation_freeze_container"]["sha256"],
        "denominator_contract_sha256": locators["denominator_contract"]["sha256"],
        "threshold_contract_sha256": locators["threshold_contract"]["sha256"],
        "published_inputs_manifest_sha256": locators["published_inputs_manifest"]["sha256"],
        "sealed_evaluator_interface_sha256": locators["sealed_evaluator_interface"]["sha256"],
        "release_instructions_sha256": locators["release_instructions"]["sha256"],
        "ukrainian_recipe_sha256": locators["ukrainian_recipe"]["sha256"],
        "english_recipe_sha256": locators["english_recipe"]["sha256"],
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
        "metrics_sha256": locators["scorer_metrics"]["sha256"],
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
        "fresh_worktree_commit_sha": _run_git("rev-parse", "HEAD", cwd=artifact_root),
        "source_blind": True,
        "fresh_clean_worktree": True,
        "author_worktree_used": False,
        "private_heldout_plaintext_available": False,
        "public_canary_evidence_allowed": False,
    }
    outsider_input_sha = evaluation.sha256_value(outsider_input)
    reproduction = {
        "outsider_input_manifest_sha256": outsider_input_sha,
        "first_build_sha256": locators["first_build"]["sha256"],
        "second_build_sha256": locators["second_build"]["sha256"],
        "reproduced_export_sha256": locators["reproduced_export"]["sha256"],
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
        "artifact_locators": locators,
        "evaluation_input_manifest": evaluation_input,
        "evaluation_input_manifest_sha256": evaluation_input_sha,
        "scorer_result": scorer_result,
        "scorer_result_sha256": scorer_result_sha,
        "scorer_action_receipt": _action(
            role_contract, "scorer", evaluation.SCORER_ACTION_KIND, evaluation_input_sha, scorer_result_sha
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
            "phase3_complete_claimed": False,
            "phase4_authorized": False,
        },
    }, artifact_root


def _refresh_reproduction_receipt(bundle: dict[str, Any]) -> None:
    role_contract = json.loads(evaluation.ROLE_CONTRACT_PATH.read_text(encoding="utf-8"))
    reproduction_sha = evaluation.sha256_value(bundle["reproduction_result"])
    bundle["reproduction_result_sha256"] = reproduction_sha
    bundle["outsider_action_receipt"] = _action(
        role_contract,
        "outsider_reproducer",
        evaluation.OUTSIDER_ACTION_KIND,
        bundle["outsider_input_manifest_sha256"],
        reproduction_sha,
    )


def test_valid_bundle_proves_mechanics_without_claiming_completion(tmp_path: Path) -> None:
    bundle, artifact_root = _bundle(tmp_path)
    result = evaluation.validate_bundle(bundle, artifact_root=artifact_root)
    assert result["ok"] is True
    assert result["mechanics_verified"] is True
    assert result["consumer_proven"] is False
    assert result["phase4_authorized"] is False


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("evaluation_input_manifest", "fixed_release_sha256"), "d" * 64),
        (("evaluation_input_manifest", "heldout_evaluation_freeze_sha256"), "e" * 64),
        (("scorer_result", "rules_modified"), True),
        (("scorer_result", "thresholds_modified"), True),
        (("scorer_result", "heldout_plaintext_exported"), True),
        (("outsider_input_manifest", "author_worktree_used"), True),
        (("outsider_input_manifest", "private_heldout_plaintext_available"), True),
        (("outsider_input_manifest", "public_canary_evidence_allowed"), True),
        (("reproduction_result", "second_build_sha256"), "d" * 64),
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
    tmp_path: Path, path: tuple[str, str], value: Any
) -> None:
    bundle, artifact_root = _bundle(tmp_path)
    bundle[path[0]][path[1]] = value
    with pytest.raises(evaluation.EvaluationReproductionError):
        evaluation.validate_bundle(bundle, artifact_root=artifact_root)


@pytest.mark.parametrize("receipt_name", ["scorer_action_receipt", "outsider_action_receipt"])
def test_action_receipt_identity_and_cycle_tampering_fail_closed(tmp_path: Path, receipt_name: str) -> None:
    bundle, artifact_root = _bundle(tmp_path)
    bundle[receipt_name]["evaluation_cycle_id"] = "phase3-v2-1-evaluation-cycle-999"
    with pytest.raises(evaluation.EvaluationReproductionError):
        evaluation.validate_bundle(bundle, artifact_root=artifact_root)

    bundle, artifact_root = _bundle(tmp_path / "second")
    bundle[receipt_name]["receipt_id"] = "phase3_functional_action:" + "0" * 64
    with pytest.raises(evaluation.EvaluationReproductionError, match="receipt ID"):
        evaluation.validate_bundle(bundle, artifact_root=artifact_root)


def test_outsider_and_scorer_roles_cannot_be_swapped(tmp_path: Path) -> None:
    bundle, artifact_root = _bundle(tmp_path)
    bundle["outsider_action_receipt"] = copy.deepcopy(bundle["scorer_action_receipt"])
    with pytest.raises(evaluation.EvaluationReproductionError, match="task binding"):
        evaluation.validate_bundle(bundle, artifact_root=artifact_root)


def test_schema_is_closed(tmp_path: Path) -> None:
    schema = json.loads(evaluation.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    for definition in schema["$defs"].values():
        if definition.get("type") == "object":
            assert definition["additionalProperties"] is False

    bundle, _ = _bundle(tmp_path)
    bundle["scorer_action_receipt"]["controller_identity_id"] = "controller_scorer"
    errors = list(Draft202012Validator(schema).iter_errors(bundle))
    assert errors


def test_fabricated_equal_hashes_without_artifact_bytes_fail_closed(tmp_path: Path) -> None:
    bundle, artifact_root = _bundle(tmp_path)
    fabricated = "c" * 64
    for artifact_id, field in (
        ("first_build", "first_build_sha256"),
        ("second_build", "second_build_sha256"),
        ("reproduced_export", "reproduced_export_sha256"),
    ):
        bundle["reproduction_result"][field] = fabricated
        bundle["artifact_locators"][artifact_id] = {
            "relative_path": f"proof/fabricated-{artifact_id}.bin",
            "sha256": fabricated,
        }
    _refresh_reproduction_receipt(bundle)
    with pytest.raises(evaluation.EvaluationReproductionError, match="missing"):
        evaluation.validate_bundle(bundle, artifact_root=artifact_root)


def test_tampered_bytes_fail(tmp_path: Path) -> None:
    bundle, artifact_root = _bundle(tmp_path)
    artifact = artifact_root / bundle["artifact_locators"]["scorer_metrics"]["relative_path"]
    artifact.write_bytes(b"tampered scorer metrics\n")
    with pytest.raises(evaluation.EvaluationReproductionError, match="bytes hash mismatch"):
        evaluation.validate_bundle(bundle, artifact_root=artifact_root)


@pytest.mark.parametrize("attack", ["traversal", "symlink"])
def test_artifact_locator_traversal_and_symlink_fail_closed(tmp_path: Path, attack: str) -> None:
    bundle, artifact_root = _bundle(tmp_path)
    locator = bundle["artifact_locators"]["first_build"]
    artifact = artifact_root / locator["relative_path"]
    if attack == "traversal":
        locator["relative_path"] = "../outside.bin"
    else:
        target = artifact.with_name("first-build-target.bin")
        target.write_bytes(artifact.read_bytes())
        artifact.unlink()
        artifact.symlink_to(target.name)
    with pytest.raises(evaluation.EvaluationReproductionError, match=r"schema violation|locator"):
        evaluation.validate_bundle(bundle, artifact_root=artifact_root)


def test_artifact_root_head_binds_outsider_commit(tmp_path: Path) -> None:
    bundle, artifact_root = _bundle(tmp_path)
    _run_git("commit", "--allow-empty", "-m", "different head", cwd=artifact_root)
    with pytest.raises(evaluation.EvaluationReproductionError, match="HEAD"):
        evaluation.validate_bundle(bundle, artifact_root=artifact_root)


def test_cli_verifies_bundle_but_returns_mechanics_only(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bundle, artifact_root = _bundle(tmp_path)
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    assert evaluation.main([str(bundle_path), "--artifact-root", str(artifact_root)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["mechanics_verified"] is True
    assert result["consumer_proven"] is False
    assert result["phase4_authorized"] is False
