"""Focused tests for the additive, text-free Phase 3 cycle002 contract layer."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_functional_roles as roles


def _json(path: Path, value: object) -> Path:
    path.write_text(roles.canonical_json(value) + "\n", encoding="utf-8")
    return path


def _value(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_cycle002_contracts_bind_the_actual_cycle001_void_receipt() -> None:
    result = roles.verify_cycle002_contracts()
    assert result["ok"] is True
    assert result["evaluation_cycle_id"] == "phase3-v2-1-evaluation-cycle-002"
    assert [item["task_id"] for item in result["labeling_protocol"]["passes"]] == [
        "phase3-v2-2-heldout-semantic-label-pass-a",
        "phase3-v2-2-heldout-semantic-label-pass-b",
    ]
    assert result["labeling_protocol"]["provider_independent"] is False
    assert result["labeling_protocol"]["deterministic_assembly_may_adjudicate"] is False
    assert result["source_authoring_blocked"] is True


@pytest.mark.parametrize("field", ["receipt_file_sha256", "receipt_sha256"])
def test_cycle002_contracts_reject_void_receipt_hash_drift(tmp_path: Path, field: str) -> None:
    role = copy.deepcopy(_value(roles.CYCLE002_ROLE_PATH))
    evaluation = copy.deepcopy(_value(roles.CYCLE002_EVALUATION_PATH))
    role["cycle001_void_receipt"][field] = "0" * 64  # type: ignore[index]
    role_path = _json(tmp_path / "role.json", role)
    evaluation_path = _json(tmp_path / "evaluation.json", evaluation)
    with pytest.raises(roles.FunctionalRoleError, match="void-receipt binding drift"):
        roles.verify_cycle002_contracts(role_path=role_path, evaluation_path=evaluation_path)


def test_cycle002_contracts_reject_unblocking_source_authoring(tmp_path: Path) -> None:
    role = copy.deepcopy(_value(roles.CYCLE002_ROLE_PATH))
    evaluation = copy.deepcopy(_value(roles.CYCLE002_EVALUATION_PATH))
    evaluation["source_authoring"] = {"blocked": False, "reason": "incorrect"}
    role_path = _json(tmp_path / "role.json", role)
    evaluation_path = _json(tmp_path / "evaluation.json", evaluation)
    with pytest.raises(roles.FunctionalRoleError, match="schema violation"):
        roles.verify_cycle002_contracts(role_path=role_path, evaluation_path=evaluation_path)


def test_cycle002_verifier_rejects_the_historical_v21_role_document() -> None:
    with pytest.raises(roles.FunctionalRoleError, match="schema violation"):
        roles.verify_cycle002_contracts(role_path=roles.LEDGER_PATH)


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("cycle002", "evaluation_cycle_id", "phase3-v2-1-evaluation-cycle-001"),
        ("cycle002", "frozen_labels_before_extraction", 9_391),
        ("preserved_constraints", "denominators_unchanged", False),
        ("preserved_constraints", "source_unit_total", 67_040),
        ("preserved_constraints", "evaluation_total", 9_391),
        ("preserved_constraints", "breadth_floors_unchanged", False),
        ("preserved_constraints", "positive_floor_per_phenomenon", 29),
        ("preserved_constraints", "distinct_document_floor_per_stratum", 2),
        ("preserved_constraints", "evaluation_thresholds_unchanged", False),
    ],
)
def test_cycle002_contracts_reject_restart_gate_drift(
    tmp_path: Path, section: str, field: str, value: object
) -> None:
    role = copy.deepcopy(_value(roles.CYCLE002_ROLE_PATH))
    evaluation = copy.deepcopy(_value(roles.CYCLE002_EVALUATION_PATH))
    role[section][field] = value  # type: ignore[index]
    evaluation[section][field] = value  # type: ignore[index]
    role_path = _json(tmp_path / "role.json", role)
    evaluation_path = _json(tmp_path / "evaluation.json", evaluation)
    with pytest.raises(roles.FunctionalRoleError, match=r"schema violation|binding drift"):
        roles.verify_cycle002_contracts(role_path=role_path, evaluation_path=evaluation_path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provider_independent", True),
        ("provider_reuse_disclosed", False),
        ("deterministic_assembly_may_adjudicate", True),
        ("disagreement_disposition", "deterministic_winner"),
    ],
)
def test_cycle002_contracts_reject_labeling_protocol_drift(
    tmp_path: Path, field: str, value: object
) -> None:
    role = copy.deepcopy(_value(roles.CYCLE002_ROLE_PATH))
    evaluation = copy.deepcopy(_value(roles.CYCLE002_EVALUATION_PATH))
    role["cycle002_labeling_protocol"][field] = value  # type: ignore[index]
    evaluation["cycle002_labeling_protocol"][field] = value  # type: ignore[index]
    role_path = _json(tmp_path / "role.json", role)
    evaluation_path = _json(tmp_path / "evaluation.json", evaluation)
    with pytest.raises(roles.FunctionalRoleError, match=r"schema violation|protocol drift"):
        roles.verify_cycle002_contracts(role_path=role_path, evaluation_path=evaluation_path)


def test_verify_value_preserves_v21_contract_semantics() -> None:
    baseline = roles.read_json(roles.LEDGER_PATH)
    assert roles.verify_value(baseline) == baseline
