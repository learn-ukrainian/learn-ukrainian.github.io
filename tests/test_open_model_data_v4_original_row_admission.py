"""Adversarial tests for deterministic original-row admission."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from scripts.projects.open_model_data import v4_original_row_admission as admission


def _row(tier: str = "silver") -> dict[str, object]:
    return {
        "row_id": "synthetic-row-001",
        "lineage": {"immutable": True, "source_ids": ["source.synthetic.001"], "evidence_ids": ["evidence.synthetic.001"]},
        "label_tier": tier,
        "authorship": {"independently_authored": True, "basis": "author_attestation"},
        "evidence": {"grade": "verified", "uncertainty": "resolved", "disposition": "supported", "basis": "source_review"},
        "rights": {"training": True, "derived_dataset_redistribution": True, "basis": "rights_receipt"},
        "split_duplicate_safety": {"passed": True, "receipt_id": "split.synthetic.001"},
        "reconstruction_gates": {gate: {"passed": True, "receipt_id": f"{gate}.synthetic.001"} for gate in admission.RECONSTRUCTION_GATES},
    }


def test_silver_is_training_admissible_only_after_every_gate_passes() -> None:
    receipt = admission.evaluate_row(_row())
    assert receipt["disposition"] == "admitted"
    assert receipt["training_eligible"] is True
    assert receipt["eligibility"]["gold"] is False


def test_gold_requires_non_model_authoritative_or_qualified_basis() -> None:
    row = _row("gold")
    rejected = admission.evaluate_row(row)
    assert "GOLD_BASIS_INVALID" in rejected["residual_codes"]
    row["gold_basis"] = {"kind": "independent_qualified_adjudication", "receipt_id": "qualified.synthetic.001"}
    assert admission.evaluate_row(row)["disposition"] == "admitted"
    row["gold_basis"] = {"kind": "model_agreement", "receipt_id": "arena.synthetic.001", "model_vote": True}
    assert "GOLD_BASIS_INVALID" in admission.evaluate_row(row)["residual_codes"]


def test_unknown_rights_and_heldout_split_failure_reject() -> None:
    row = _row()
    row["rights"]["training"] = "unknown"  # type: ignore[index]
    row["split_duplicate_safety"]["passed"] = False  # type: ignore[index]
    receipt = admission.evaluate_row(row)
    assert receipt["disposition"] == "rejected"
    assert {"TRAINING_RIGHTS_NOT_GRANTED", "SPLIT_DUPLICATE_SAFETY_FAILED"} <= set(receipt["residual_codes"])


def test_each_reconstruction_gate_fails_closed() -> None:
    for gate in admission.RECONSTRUCTION_GATES:
        row = _row()
        row["reconstruction_gates"][gate]["passed"] = False  # type: ignore[index]
        receipt = admission.evaluate_row(row)
        assert f"{gate.upper()}_RECONSTRUCTION_GATE_FAILED" in receipt["residual_codes"]
        assert receipt["training_eligible"] is False


def test_model_agreement_cannot_supply_required_admission_facts() -> None:
    row = _row()
    row["authorship"] = {"basis": "model_agreement", "model_agreement": True}
    row["model_agreement"] = True
    receipt = admission.evaluate_row(row)
    assert receipt["disposition"] == "rejected"
    assert "MODEL_AGREEMENT_CANNOT_SATISFY_AUTHORSHIP" in receipt["residual_codes"]
    assert "MODEL_AGREEMENT_CANNOT_SATISFY_ADMISSION" in receipt["residual_codes"]


def test_direct_text_clearance_is_an_authorship_alternative_and_hash_replays() -> None:
    row = _row()
    row["authorship"] = {"independently_authored": False, "direct_text_clearance": {"cleared": True, "operation_id": "clearance.synthetic.001"}}
    first = admission.admit_rows([row])
    assert first == admission.admit_rows([copy.deepcopy(row)])
    assert admission.verify_receipt(first) == first


def test_cli_retains_rejected_rows_instead_of_dropping_them(tmp_path: Path) -> None:
    rejected = _row()
    rejected["row_id"] = "synthetic-row-002"
    rejected["rights"]["derived_dataset_redistribution"] = False  # type: ignore[index]
    input_path, output_path = tmp_path / "rows.json", tmp_path / "receipt.json"
    input_path.write_text(json.dumps([_row(), rejected]), encoding="utf-8")
    command = [sys.executable, "scripts/projects/open_model_data/v4_original_row_admission.py", "--input", str(input_path), "--output", str(output_path)]
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    receipt = json.loads(output_path.read_text())
    assert receipt["counts"] == {"input_rows": 2, "admitted_rows": 1, "rejected_rows": 1}
    assert receipt["rows"][1]["residual_codes"] == ["DERIVED_DATASET_REDISTRIBUTION_RIGHTS_NOT_GRANTED"]


def test_rehashed_receipt_schema_drift_fails_closed() -> None:
    receipt = admission.admit_rows([_row()])
    receipt["unexpected"] = True
    receipt["receipt_sha256"] = admission.sha256_value({key: value for key, value in receipt.items() if key != "receipt_sha256"})
    try:
        admission.verify_receipt(receipt)
    except admission.OriginalRowAdmissionError as exc:
        assert "schema drift" in str(exc)
    else:
        raise AssertionError("rehashed schema drift was accepted")
