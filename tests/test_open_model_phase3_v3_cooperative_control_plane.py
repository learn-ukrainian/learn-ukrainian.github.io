"""Adversarial metadata-only checks for the additive Phase 3 V3 contract."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_v3_cooperative_control_plane as control_plane


def _artifact() -> dict[str, Any]:
    value = json.loads(control_plane.ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _rehash(value: dict[str, Any]) -> None:
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    value["receipt_sha256"] = control_plane.sha256_bytes(control_plane.canonical_bytes(body))


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


def _reject(value: dict[str, Any], tmp_path: Path, pattern: str) -> None:
    _rehash(value)
    path = tmp_path / "contract.json"
    _write(path, value)
    with pytest.raises(control_plane.ControlPlaneError, match=pattern):
        control_plane.verify(path)


def test_tracked_contract_is_valid_metadata_only_and_deterministic() -> None:
    schema = json.loads(control_plane.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert _object_schemas(schema)
    assert all(item.get("additionalProperties") is False for item in _object_schemas(schema))
    result = control_plane.verify()
    assert result == {
        "ok": True,
        "schema_version": "phase3_v3_cooperative_control_plane_v1",
        "status": "FROZEN_REVIEWED_METADATA_ONLY",
        "artifact_sha256": control_plane.sha256_file(control_plane.ARTIFACT_PATH),
        "receipt_sha256": _artifact()["receipt_sha256"],
        "v2_cell_count": 16,
        "role_count": 9,
        "state_count": 24,
        "child_slot_count": 3,
        "provider_calls": False,
        "gold_authority": "HUMAN_STEWARD",
        "p4_v1_mutation_allowed": False,
    }
    assert control_plane.main(["--check"]) == 0


def test_hash_tampering_is_rejected_after_receipt_rehash(tmp_path: Path) -> None:
    value = _artifact()
    value["bindings"]["p4_v1"]["admission_file"]["sha256"] = "0" * 64
    _reject(value, tmp_path, "artifact schema violation|P4 v1 admission binding drift")


def test_p4_predecessor_bytes_are_actually_verified(monkeypatch: pytest.MonkeyPatch) -> None:
    original = control_plane.sha256_file
    p4_schema = control_plane.ROOT / control_plane.P4_SCHEMA_LOGICAL_PATH

    def tampered(path: Path) -> str:
        return "0" * 64 if path == p4_schema else original(path)

    monkeypatch.setattr(control_plane, "sha256_file", tampered)
    with pytest.raises(control_plane.ControlPlaneError, match="bound P4 v1 schema bytes drift"):
        control_plane.verify()


def test_forbidden_content_fields_are_rejected_even_when_schema_shape_is_bypassed(tmp_path: Path) -> None:
    value = _artifact()
    value["gates"]["provider_output"] = "opaque"
    _reject(value, tmp_path, "forbidden body field")


def test_only_human_steward_can_author_gold_and_quarantine_cannot_be_promoted(tmp_path: Path) -> None:
    value = _artifact()
    identity_lead = next(role for role in value["roles"] if role["role_id"] == "IDENTITY_LEAD")
    identity_lead["may_author_gold"] = True
    _reject(value, tmp_path, "gold authority drift")

    value = _artifact()
    value["quarantine_policy"]["gold_eligible"] = True
    _reject(value, tmp_path, "artifact schema violation")

    value = _artifact()
    quarantine = next(
        state
        for state in value["state_machine"]["states"]
        if state["state_id"] == "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD"
    )
    quarantine["legal_next_states"] = ["GOLD_ELIGIBLE"]
    _reject(value, tmp_path, "legal transition drift")

    value = _artifact()
    value["state_machine"]["transitions"].append(
        {
            "from_state": "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD",
            "to_state": "GOLD_ELIGIBLE",
            "condition_code": "illegal_direct_gold_promotion",
            "retry_or_substitute_allowed": False,
            "human_fallback": False,
        }
    )
    _reject(value, tmp_path, "transition table exact-set drift")


def test_provider_and_critic_failures_have_human_fallbacks_and_resumable_states() -> None:
    value = _artifact()
    transitions = {(item["from_state"], item["to_state"]) for item in value["state_machine"]["transitions"]}
    assert ("IDENTITY_PROVIDER_FAILURE", "IDENTITY_REVIEWS_PENDING") in transitions
    assert ("IDENTITY_PROVIDER_FAILURE", "IDENTITY_HUMAN_QUEUE") in transitions
    assert ("CANDIDATE_PROVIDER_FAILURE", "CASE_CANDIDATE_PENDING") in transitions
    assert ("CANDIDATE_PROVIDER_FAILURE", "CASE_HUMAN_QUEUE") in transitions
    assert ("DISPUTE_CRITIC_PENDING", "IDENTITY_HUMAN_QUEUE") in transitions
    states = {item["state_id"]: item for item in value["state_machine"]["states"]}
    assert states["IDENTITY_EVIDENCE_INSUFFICIENT"] == {
        "state_id": "IDENTITY_EVIDENCE_INSUFFICIENT",
        "terminal": True,
        "resumable": True,
        "legal_next_states": [],
        "resume_to_state": "IDENTITY_HUMAN_QUEUE",
        "counts_toward_coverage": False,
        "gold_eligible": False,
        "training_eligible": False,
    }
    assert states["IDENTITY_HUMAN_ABSTAINED"]["legal_next_states"] == ["CASE_CANDIDATE_PENDING"]
    assert states["MODEL_AGREEMENT_QUARANTINED_NOT_GOLD"] == {
        "state_id": "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD",
        "terminal": True,
        "resumable": True,
        "legal_next_states": [],
        "resume_to_state": "IDENTITY_AGREEMENT_QC",
        "counts_toward_coverage": False,
        "gold_eligible": False,
        "training_eligible": False,
    }


def test_compatibility_requires_all_sixteen_v2_semantic_cells(tmp_path: Path) -> None:
    value = _artifact()
    dialect = value["compatibility"]["cells"][-1]
    assert dialect["disposition"] == "carried_forward_exact"
    assert dialect["child_partition_ids"] == []
    assert dialect["denominator_effect"] == "same_parent_denominator"

    value = _artifact()
    value["compatibility"]["cells"].pop()
    _reject(value, tmp_path, "artifact schema violation")

    value = _artifact()
    value["compatibility"]["cells"][0]["v2_cell_id"] = "invented.v2.cell"
    _reject(value, tmp_path, "stable cell ID drift|V2 semantic cell set or order drift")


def test_child_dag_binds_taxonomy_before_control_plane_and_heldout(tmp_path: Path) -> None:
    value = _artifact()
    slots = {slot["slot_id"]: slot for slot in value["child_work_slots"]}
    assert slots["V3-B"]["dependencies"] == ["phase3_v3_cooperative_control_plane_v1", "issue_7560"]
    assert slots["V3-C"]["dependencies"] == ["phase3_v3_cooperative_control_plane_v1", "issue_7560"]

    value["child_work_slots"][1]["dependencies"] = ["phase3_v3_cooperative_control_plane_v1"]
    _reject(value, tmp_path, "V3 child dependency DAG drift")


def test_role_access_and_coverage_flags_cannot_drift_from_visibility(tmp_path: Path) -> None:
    value = _artifact()
    builder = next(role for role in value["roles"] if role["role_id"] == "CANDIDATE_BUILDER")
    builder["may_access_heldout"] = True
    _reject(value, tmp_path, "role/visibility held-out access disagreement")

    value = _artifact()
    human = next(role for role in value["roles"] if role["role_id"] == "HUMAN_STEWARD")
    human["may_count_toward_coverage"] = True
    _reject(value, tmp_path, "direct role coverage credit drift")
