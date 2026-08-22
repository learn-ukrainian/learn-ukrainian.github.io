#!/usr/bin/env python3
"""Synthetic tests for the Cycle 007 label validation semantics."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract


def _load_validator() -> Any:
    path = ROOT / "batch_state" / "phase3-cycle007-label-validation-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_label_validation", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()
Invalid = VALIDATOR.Invalid

ROW_1 = {"unit_id": "u-001", "unit_sha256": "1" * 64, "family_id": "pravopys_2026_complete"}
ROW_2 = {"unit_id": "u-002", "unit_sha256": "2" * 64, "family_id": "pravopys_2026_complete"}
ROW_2019 = {"unit_id": "u-003", "unit_sha256": "3" * 64, "family_id": "pravopys_2019_complete"}


def _vesum_record(
    row: dict[str, Any], *, status: str = "attested", supports: str = "attestation", phenomenon_id: str | None = None
) -> dict[str, Any]:
    return contract.build_evidence_record(
        channel="vesum_attestation",
        source_identity="vesum",
        source_version="v1",
        locator="data/vesum.db#forms",
        query="слово",
        status=status,
        supports=supports if status == "attested" else "no_conclusion",
        retrieval_sha256=contract.sha256_text("vesum-payload"),
        parser_id="vesum-forms-v1",
        parser_version="1",
        row=row,
        phenomenon_id=phenomenon_id,
        negative_reason=None if status == "attested" else status,
    )


def _row_evidence(
    row: dict[str, Any], records: list[dict[str, Any]], *, phenomenon_evidence_ids: dict[str, list[str]] | None = None
) -> dict[str, Any]:
    evidence_ids = sorted({record["evidence_id"] for record in records})
    return {
        "unit_id": row["unit_id"],
        "unit_sha256": row["unit_sha256"],
        "evidence": records,
        "evidence_ids": evidence_ids,
        "phenomenon_evidence_ids": phenomenon_evidence_ids or {},
    }


def test_valid_clean_label_with_evidence() -> None:
    rec = _vesum_record(ROW_1, status="attested", supports="attestation")
    ev = _row_evidence(ROW_1, [rec])
    label = {
        "unit_id": ROW_1["unit_id"],
        "unit_sha256": ROW_1["unit_sha256"],
        "decision_code": "agree",
        "clean_modern_standard_prose": True,
        "modern_genre_id": "scientific_expository",
        "evidence_ids": [rec["evidence_id"]],
    }
    packet = {"rows": [ROW_1]}
    raw = json.dumps({"labels": [label]}).encode("utf-8")
    sidecar = {"rows": [ev]}
    res = VALIDATOR.validate("clean_label", packet, raw, sidecar=sidecar)
    assert len(res["labels"]) == 1


def test_valid_clean_label_uncertainty_with_empty_or_negative_evidence() -> None:
    rec = _vesum_record(ROW_1, status="not_found", supports="no_conclusion")
    ev = _row_evidence(ROW_1, [rec])
    label = {
        "unit_id": ROW_1["unit_id"],
        "unit_sha256": ROW_1["unit_sha256"],
        "decision_code": "reject_insufficient_locator_evidence",
        "clean_modern_standard_prose": False,
        "modern_genre_id": None,
        "evidence_ids": [rec["evidence_id"]],
    }
    packet = {"rows": [ROW_1]}
    raw = json.dumps({"labels": [label]}).encode("utf-8")
    sidecar = {"rows": [ev]}
    res = VALIDATOR.validate("clean_label", packet, raw, sidecar=sidecar)
    assert len(res["labels"]) == 1


def test_clean_label_rejects_missing_evidence_ids() -> None:
    label = {
        "unit_id": ROW_1["unit_id"],
        "unit_sha256": ROW_1["unit_sha256"],
        "decision_code": "agree",
        "clean_modern_standard_prose": True,
        "modern_genre_id": "scientific_expository",
    }
    packet = {"rows": [ROW_1]}
    raw = json.dumps({"labels": [label]}).encode("utf-8")
    with pytest.raises(Invalid, match="clean schema drift"):
        VALIDATOR.validate("clean_label", packet, raw)


def test_clean_label_rejects_unsorted_or_duplicate_evidence_ids() -> None:
    rec1 = _vesum_record(ROW_1, status="attested", supports="attestation")
    rec2 = contract.build_evidence_record(
        channel="pravopys_2026_normative",
        source_identity="pravopys_2026",
        source_version="v1",
        locator="p1",
        query=None,
        status="attested",
        supports="normative_rule",
        retrieval_sha256=contract.sha256_text("pravopys-payload"),
        parser_id="p-1",
        parser_version="1",
        row=ROW_1,
    )
    ev = _row_evidence(ROW_1, [rec1, rec2])
    # Unsorted
    ids_unsorted = sorted([rec1["evidence_id"], rec2["evidence_id"]], reverse=True)
    if ids_unsorted[0] != ids_unsorted[1]:
        label = {
            "unit_id": ROW_1["unit_id"],
            "unit_sha256": ROW_1["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "scientific_expository",
            "evidence_ids": ids_unsorted,
        }
        with pytest.raises(Invalid, match="evidence id order/unique drift"):
            VALIDATOR.validate(
                "clean_label",
                {"rows": [ROW_1]},
                json.dumps({"labels": [label]}).encode("utf-8"),
                sidecar={"rows": [ev]},
            )


def test_clean_label_rejects_cross_row_evidence() -> None:
    rec1 = _vesum_record(ROW_1, status="attested", supports="attestation")
    rec2 = _vesum_record(ROW_2, status="attested", supports="attestation")
    ev1 = _row_evidence(ROW_1, [rec1])
    label = {
        "unit_id": ROW_1["unit_id"],
        "unit_sha256": ROW_1["unit_sha256"],
        "decision_code": "agree",
        "clean_modern_standard_prose": True,
        "modern_genre_id": "scientific_expository",
        "evidence_ids": [rec2["evidence_id"]],
    }
    with pytest.raises(Invalid, match="cross_row_evidence"):
        VALIDATOR.validate(
            "clean_label", {"rows": [ROW_1]}, json.dumps({"labels": [label]}).encode("utf-8"), sidecar={"rows": [ev1]}
        )


def test_clean_label_rejects_invented_evidence() -> None:
    rec1 = _vesum_record(ROW_1, status="attested", supports="attestation")
    ev1 = _row_evidence(ROW_1, [rec1])
    label = {
        "unit_id": ROW_1["unit_id"],
        "unit_sha256": ROW_1["unit_sha256"],
        "decision_code": "agree",
        "clean_modern_standard_prose": True,
        "modern_genre_id": "scientific_expository",
        "evidence_ids": ["cycle007_evidence:invented" + "0" * 48],
    }
    with pytest.raises(Invalid, match="cross_row_evidence"):
        VALIDATOR.validate(
            "clean_label", {"rows": [ROW_1]}, json.dumps({"labels": [label]}).encode("utf-8"), sidecar={"rows": [ev1]}
        )


def test_clean_label_rejects_agree_when_insufficient() -> None:
    rec = _vesum_record(ROW_1, status="not_found", supports="no_conclusion")
    ev = _row_evidence(ROW_1, [rec])
    label = {
        "unit_id": ROW_1["unit_id"],
        "unit_sha256": ROW_1["unit_sha256"],
        "decision_code": "agree",
        "clean_modern_standard_prose": True,
        "modern_genre_id": "scientific_expository",
        "evidence_ids": [rec["evidence_id"]],
    }
    with pytest.raises(Invalid, match="insufficient_evidence_for_decision"):
        VALIDATOR.validate(
            "clean_label", {"rows": [ROW_1]}, json.dumps({"labels": [label]}).encode("utf-8"), sidecar={"rows": [ev]}
        )


def test_clean_label_invariants() -> None:
    label = {
        "unit_id": ROW_1["unit_id"],
        "unit_sha256": ROW_1["unit_sha256"],
        "decision_code": "agree",
        "clean_modern_standard_prose": False,  # Mismatch
        "modern_genre_id": "scientific_expository",
        "evidence_ids": [],
    }
    with pytest.raises(Invalid, match="clean invariant"):
        VALIDATOR.validate("clean_label", {"rows": [ROW_1]}, json.dumps({"labels": [label]}).encode("utf-8"))


def test_valid_residual_label_with_evidence() -> None:
    phenomenon_id = "apostrophe"
    rec = _vesum_record(ROW_1, status="attested", supports="attestation", phenomenon_id=phenomenon_id)
    ev = _row_evidence(ROW_1, [rec], phenomenon_evidence_ids={phenomenon_id: [rec["evidence_id"]]})
    label = {
        "unit_id": ROW_1["unit_id"],
        "unit_sha256": ROW_1["unit_sha256"],
        "phenomena": [
            {
                "phenomenon_id": phenomenon_id,
                "decision_code": "positive",
                "evidence_sufficiency": "sufficient",
                "evidence_ids": [rec["evidence_id"]],
            }
        ],
        "primary_phenomenon_id": phenomenon_id,
        "item_decision_rollup": "positive",
    }
    packet = {"rows": [ROW_1]}
    raw = json.dumps({"labels": [label]}).encode("utf-8")
    sidecar = {"rows": [ev]}
    res = VALIDATOR.validate("residual_label", packet, raw, sidecar=sidecar)
    assert len(res["labels"]) == 1


def test_residual_label_rejects_missing_evidence_ids() -> None:
    phenomenon_id = "apostrophe"
    label = {
        "unit_id": ROW_1["unit_id"],
        "unit_sha256": ROW_1["unit_sha256"],
        "phenomena": [
            {
                "phenomenon_id": phenomenon_id,
                "decision_code": "positive",
                "evidence_sufficiency": "sufficient",
            }
        ],
        "primary_phenomenon_id": phenomenon_id,
        "item_decision_rollup": "positive",
    }
    with pytest.raises(Invalid, match="residual phenomenon drift"):
        VALIDATOR.validate("residual_label", {"rows": [ROW_1]}, json.dumps({"labels": [label]}).encode("utf-8"))


def test_residual_label_rejects_cross_phenomenon_evidence() -> None:
    p1 = "apostrophe"
    p2 = "capitalization"
    rec1 = _vesum_record(ROW_1, status="attested", supports="attestation", phenomenon_id=p1)
    rec2 = _vesum_record(ROW_1, status="attested", supports="attestation", phenomenon_id=p2)
    ev = _row_evidence(
        ROW_1, [rec1, rec2], phenomenon_evidence_ids={p1: [rec1["evidence_id"]], p2: [rec2["evidence_id"]]}
    )
    # Phenomenon p1 cites rec2 from p2
    label = {
        "unit_id": ROW_1["unit_id"],
        "unit_sha256": ROW_1["unit_sha256"],
        "phenomena": [
            {
                "phenomenon_id": p1,
                "decision_code": "positive",
                "evidence_sufficiency": "sufficient",
                "evidence_ids": [rec2["evidence_id"]],
            }
        ],
        "primary_phenomenon_id": p1,
        "item_decision_rollup": "positive",
    }
    with pytest.raises(Invalid, match="cross_phenomenon_evidence"):
        VALIDATOR.validate(
            "residual_label", {"rows": [ROW_1]}, json.dumps({"labels": [label]}).encode("utf-8"), sidecar={"rows": [ev]}
        )


def test_residual_label_rejects_2019_positive() -> None:
    phenomenon_id = "apostrophe"
    rec = _vesum_record(ROW_2019, status="attested", supports="attestation", phenomenon_id=phenomenon_id)
    ev = _row_evidence(ROW_2019, [rec], phenomenon_evidence_ids={phenomenon_id: [rec["evidence_id"]]})
    label = {
        "unit_id": ROW_2019["unit_id"],
        "unit_sha256": ROW_2019["unit_sha256"],
        "phenomena": [
            {
                "phenomenon_id": phenomenon_id,
                "decision_code": "positive",
                "evidence_sufficiency": "sufficient",
                "evidence_ids": [rec["evidence_id"]],
            }
        ],
        "primary_phenomenon_id": phenomenon_id,
        "item_decision_rollup": "positive",
    }
    with pytest.raises(Invalid, match="2019 positive forbidden"):
        VALIDATOR.validate(
            "residual_label",
            {"rows": [ROW_2019]},
            json.dumps({"labels": [label]}).encode("utf-8"),
            sidecar={"rows": [ev]},
        )


def test_residual_label_taxonomy_order_drift() -> None:
    # prefix_and_suffix_spelling is after apostrophe in taxonomy
    p1 = "prefix_and_suffix_spelling"
    p2 = "apostrophe"
    label = {
        "unit_id": ROW_1["unit_id"],
        "unit_sha256": ROW_1["unit_sha256"],
        "phenomena": [
            {
                "phenomenon_id": p1,
                "decision_code": "abstention",
                "evidence_sufficiency": "insufficient",
                "evidence_ids": [],
            },
            {
                "phenomenon_id": p2,
                "decision_code": "abstention",
                "evidence_sufficiency": "insufficient",
                "evidence_ids": [],
            },
        ],
        "primary_phenomenon_id": None,
        "item_decision_rollup": "abstention",
    }
    with pytest.raises(Invalid, match="taxonomy order/unique drift"):
        VALIDATOR.validate("residual_label", {"rows": [ROW_1]}, json.dumps({"labels": [label]}).encode("utf-8"))


def test_duplicate_json_keys_rejected() -> None:
    raw = b'{"labels":[{"unit_id":"u-001","unit_id":"u-001"}]}'
    with pytest.raises(Invalid, match="response UTF-8/JSON invalid"):
        VALIDATOR.validate("clean_label", {"rows": [ROW_1]}, raw)


def main() -> int:
    test_valid_clean_label_with_evidence()
    test_valid_clean_label_uncertainty_with_empty_or_negative_evidence()
    test_clean_label_rejects_missing_evidence_ids()
    test_clean_label_rejects_unsorted_or_duplicate_evidence_ids()
    test_clean_label_rejects_cross_row_evidence()
    test_clean_label_rejects_invented_evidence()
    test_clean_label_rejects_agree_when_insufficient()
    test_clean_label_invariants()
    test_valid_residual_label_with_evidence()
    test_residual_label_rejects_missing_evidence_ids()
    test_residual_label_rejects_cross_phenomenon_evidence()
    test_residual_label_rejects_2019_positive()
    test_residual_label_taxonomy_order_drift()
    test_duplicate_json_keys_rejected()
    print(
        json.dumps(
            {"ok": True, "test": "cycle007_label_validation", "text_free": True}, sort_keys=True, separators=(",", ":")
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
