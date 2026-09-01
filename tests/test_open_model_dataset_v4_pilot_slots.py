"""V4 pilot entry contract is deterministic, bounded, and expression-free."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
ADMISSION = ROOT / "data/projects/open_model_data/admission"
SCHEMA = CONTRACTS / "dataset_v4_pilot_slot_manifest_v1.schema.json"
MANIFEST = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    schema = _load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _errors(value: dict[str, Any]) -> list[object]:
    return sorted(_validator().iter_errors(value), key=lambda item: list(item.path))


def _slot_ids(manifest: dict[str, Any]) -> list[str]:
    return [
        f"{series['id_prefix']}-{number:03d}"
        for series in manifest["slot_series"]
        for number in range(series["start"], series["start"] + series["count"])
    ]


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value)) if value else set()
    return set()


def test_v4_pilot_slot_manifest_validates_and_binds_the_controlling_outcome() -> None:
    manifest = _load(MANIFEST)

    assert not _errors(manifest)
    assert manifest["controlling_outcome_sha256"] == V4_SHA256
    assert manifest["text_free"] is True


def test_v4_pilot_slot_series_expands_to_exactly_one_hundred_unique_stable_ids() -> None:
    manifest = _load(MANIFEST)
    ids = _slot_ids(manifest)
    quotas = {series["stratum"]: series["count"] for series in manifest["slot_series"]}

    assert len(ids) == 100
    assert len(set(ids)) == 100
    assert quotas == {
        "standard_correct": 15,
        "correction": 15,
        "literary": 15,
        "dialect_regional": 15,
        "archaic_historical": 15,
        "mixing": 10,
        "quotation_interference": 10,
        "abstention": 5,
    }


def test_v4_slot_schema_rejects_duplicate_missing_and_wrong_quota_series() -> None:
    manifest = _load(MANIFEST)

    duplicate = copy.deepcopy(manifest)
    duplicate["slot_series"][0] = copy.deepcopy(duplicate["slot_series"][1])
    assert _errors(duplicate)

    missing = copy.deepcopy(manifest)
    missing["slot_series"].pop()
    assert _errors(missing)

    wrong_quota = copy.deepcopy(manifest)
    wrong_quota["slot_series"][0]["count"] = 10
    assert _errors(wrong_quota)


def test_v4_pilot_slot_manifest_binds_the_frozen_non_goals() -> None:
    manifest = _load(MANIFEST)

    assert set(manifest["non_goals"]) == {
        "no_model_training_or_preference_optimization",
        "no_general_vernacular_or_knowledge_corpus",
        "no_dedicated_non_ukrainian_slavic_lanes",
        "no_modern_rusyn_remapping",
        "no_automatic_modernization_of_protected_material",
        "no_model_output_or_agreement_as_silver_or_gold",
        "no_source_text_publication_or_redistribution_without_operation_rights",
        "no_mac_corpus_or_data_producing_work",
        "no_dataset_or_model_performance_claims_without_release_gates",
    }

def test_v4_pilot_slot_manifest_has_required_roles_gates_and_no_private_payload() -> None:
    manifest = _load(MANIFEST)
    keys = _all_keys(manifest)

    assert manifest["role_ownership"] == {
        "A0": "scope_lead",
        "A1": "custody",
        "A2": "source_inventory_admission",
        "A3": "heldout",
        "A4": "deterministic_extraction",
        "A5": "evidence_enrichment",
        "A6": "safe_arena",
        "A7": "original_row_factory",
        "A8": "admission_assembly",
        "A9": "evaluation_package",
        "A10": "pilot_review",
        "A11": "training_ready_release",
        "A12": "later_gold_overlay",
        "A13": "cleanup_recovery",
    }
    assert set(manifest["required_role_ids"]) == {f"A{index}" for index in range(14)}
    assert set(manifest["required_gate_ids"]) == {
        "VPS_CUSTODY_CAPACITY",
        "SOURCE_OPERATION_ADMISSION",
        "SEALED_HELDOUT_SOURCE_FAMILY_SPLIT",
        "NON_SELF_ARENA_VOTING",
        "MODEL_AGREEMENT_NOT_SILVER_OR_GOLD",
        "SILVER_FIRST_STABLE_IDS",
        "INDEPENDENT_CROSS_FAMILY_EXACT_HEAD_REVIEW",
    }
    assert set(manifest["completion_vocabulary"]) == {
        "ARENA_SLICE_READY",
        "EVAL_ARTIFACT_READY",
        "TRAINING_READY_SILVER",
        "TRAINING_READY_GOLD_SUBSET",
        "GOLD_UPGRADE_READY",
        "BLOCKED_WITH_RESIDUALS",
    }
    assert manifest["completion_policy"] == {
        "blocked_with_residuals_is_success": False,
        "unresolved_required_slots_satisfy_eval": False,
        "unresolved_required_slots_satisfy_training_silver": False,
    }
    assert manifest["release_train"]["model_agreement_admits_silver"] is False
    assert manifest["release_train"]["model_agreement_creates_gold"] is False
    assert manifest["sealed_heldout_commitment"]["heldout_membership_included"] is False
    assert manifest["sealed_heldout_commitment"]["assignment_owner"] == "A2_A3_PRIVATE_ARTIFACT"
    assert not keys & {
        "content",
        "correction",
        "gold",
        "heldout_membership",
        "label",
        "provider_output",
        "source_body",
        "source_identity",
        "source_locator",
        "source_text",
        "text",
    }
