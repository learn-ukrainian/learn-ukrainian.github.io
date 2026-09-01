#!/usr/bin/env python3
"""Fail-closed admission receipts for independently authored V4 silver/gold rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "v4-original-row-admission-v1"
RECONSTRUCTION_GATES = ("exact", "fuzzy", "structural", "cumulative", "reconstruction")
MODEL_ONLY_BASES = frozenset({"model_agreement", "arena_vote", "model_vote"})


class OriginalRowAdmissionError(ValueError):
    """The batch shape is not safe to evaluate."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_value(value: Any) -> str:
    return hashlib.sha256((canonical_json(value) + "\n").encode("utf-8")).hexdigest()


def _identifier_list(value: Any, field: str, residuals: list[str]) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value) or len(value) != len(set(value)):
        residuals.append(f"{field.upper()}_INVALID")
        return []
    return sorted(value)


def _basis_is_model_only(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    return value.get("basis") in MODEL_ONLY_BASES or value.get("model_agreement") is True or value.get("arena_vote") is True or value.get("model_vote") is True


def evaluate_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return a text-free accepted/rejected row receipt; never silently discard rows."""
    if not isinstance(row, Mapping):
        raise OriginalRowAdmissionError("row must be an object")
    residuals: list[str] = []
    row_id = row.get("row_id")
    if not isinstance(row_id, str) or not row_id:
        residuals.append("ROW_ID_INVALID")
        row_id = None
    lineage = row.get("lineage")
    if not isinstance(lineage, Mapping) or lineage.get("immutable") is not True:
        residuals.append("LINEAGE_NOT_IMMUTABLE")
        source_ids: list[str] = []
        evidence_ids: list[str] = []
    else:
        source_ids = _identifier_list(lineage.get("source_ids"), "source_lineage_ids", residuals)
        evidence_ids = _identifier_list(lineage.get("evidence_ids"), "evidence_lineage_ids", residuals)
    tier = row.get("label_tier")
    if tier not in {"silver", "gold"}:
        residuals.append("LABEL_TIER_INVALID")

    authorship = row.get("authorship")
    if _basis_is_model_only(authorship):
        residuals.append("MODEL_AGREEMENT_CANNOT_SATISFY_AUTHORSHIP")
    elif not isinstance(authorship, Mapping) or not (
        authorship.get("independently_authored") is True
        or (isinstance(authorship.get("direct_text_clearance"), Mapping) and authorship["direct_text_clearance"].get("cleared") is True and isinstance(authorship["direct_text_clearance"].get("operation_id"), str) and bool(authorship["direct_text_clearance"]["operation_id"]))
    ):
        residuals.append("AUTHORSHIP_OR_DIRECT_TEXT_CLEARANCE_REQUIRED")

    evidence = row.get("evidence")
    if _basis_is_model_only(evidence):
        residuals.append("MODEL_AGREEMENT_CANNOT_SATISFY_EVIDENCE")
    elif not isinstance(evidence, Mapping) or evidence.get("grade") != "verified" or evidence.get("uncertainty") not in {"resolved", "bounded"} or evidence.get("disposition") not in {"supported", "admitted"}:
        residuals.append("EVIDENCE_NOT_VERIFIED")

    rights = row.get("rights")
    if _basis_is_model_only(rights):
        residuals.append("MODEL_AGREEMENT_CANNOT_SATISFY_RIGHTS")
    if not isinstance(rights, Mapping) or rights.get("training") is not True:
        residuals.append("TRAINING_RIGHTS_NOT_GRANTED")
    if not isinstance(rights, Mapping) or rights.get("derived_dataset_redistribution") is not True:
        residuals.append("DERIVED_DATASET_REDISTRIBUTION_RIGHTS_NOT_GRANTED")

    split = row.get("split_duplicate_safety")
    if not isinstance(split, Mapping) or split.get("passed") is not True or not isinstance(split.get("receipt_id"), str) or not split.get("receipt_id"):
        residuals.append("SPLIT_DUPLICATE_SAFETY_FAILED")
    gates = row.get("reconstruction_gates")
    for gate in RECONSTRUCTION_GATES:
        value = gates.get(gate) if isinstance(gates, Mapping) else None
        if _basis_is_model_only(value):
            residuals.append("MODEL_AGREEMENT_CANNOT_SATISFY_RECONSTRUCTION")
        if not isinstance(value, Mapping) or value.get("passed") is not True or not isinstance(value.get("receipt_id"), str) or not value.get("receipt_id"):
            residuals.append(f"{gate.upper()}_RECONSTRUCTION_GATE_FAILED")

    if row.get("model_agreement") is True or row.get("arena_vote") is True:
        residuals.append("MODEL_AGREEMENT_CANNOT_SATISFY_ADMISSION")
    if tier == "gold":
        gold_basis = row.get("gold_basis")
        if not isinstance(gold_basis, Mapping) or gold_basis.get("kind") not in {"authoritative_deterministic", "independent_qualified_adjudication"} or not isinstance(gold_basis.get("receipt_id"), str) or not gold_basis.get("receipt_id") or _basis_is_model_only(gold_basis):
            residuals.append("GOLD_BASIS_INVALID")
    if row.get("training_eligible") is True and residuals:
        residuals.append("DECLARED_TRAINING_ELIGIBILITY_INVALID")

    residuals = sorted(set(residuals))
    result = {
        "row_id": row_id,
        "label_tier": tier if tier in {"silver", "gold"} else None,
        "source_lineage_ids": source_ids,
        "evidence_lineage_ids": evidence_ids,
        "disposition": "admitted" if not residuals else "rejected",
        "training_eligible": not residuals,
        "residual_codes": residuals,
        "eligibility": {"gold": tier == "gold" and not residuals, "training": not residuals, "evaluation": False, "teaching": False, "coverage": False},
    }
    result["receipt_sha256"] = sha256_value(result)
    return result


def admit_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise OriginalRowAdmissionError("rows must be a list")
    receipts = [evaluate_row(row) for row in rows]
    ids = [item["row_id"] for item in receipts]
    if any(item is None for item in ids) or len(ids) != len(set(ids)):
        raise OriginalRowAdmissionError("row IDs must be stable and unique in a batch")
    result = {
        "schema_version": SCHEMA_VERSION,
        "visibility": "machine_receipt_text_free",
        "rows": receipts,
        "counts": {"input_rows": len(receipts), "admitted_rows": sum(item["disposition"] == "admitted" for item in receipts), "rejected_rows": sum(item["disposition"] == "rejected" for item in receipts)},
    }
    result["receipt_sha256"] = sha256_value(result)
    return result


def verify_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise OriginalRowAdmissionError("receipt must be an object")
    body = dict(receipt)
    supplied = body.pop("receipt_sha256", None)
    if not isinstance(supplied, str) or supplied != sha256_value(body):
        raise OriginalRowAdmissionError("receipt hash drift")
    if body.get("schema_version") != SCHEMA_VERSION:
        raise OriginalRowAdmissionError("receipt schema drift")
    if set(body) != {"schema_version", "visibility", "rows", "counts"} or body.get("visibility") != "machine_receipt_text_free":
        raise OriginalRowAdmissionError("receipt schema drift")
    rows, counts = body.get("rows"), body.get("counts")
    if not isinstance(rows, list) or not isinstance(counts, Mapping):
        raise OriginalRowAdmissionError("receipt schema drift")
    if counts != {"input_rows": len(rows), "admitted_rows": sum(item.get("disposition") == "admitted" for item in rows if isinstance(item, Mapping)), "rejected_rows": sum(item.get("disposition") == "rejected" for item in rows if isinstance(item, Mapping))}:
        raise OriginalRowAdmissionError("receipt count drift")
    required_row_keys = {"row_id", "label_tier", "source_lineage_ids", "evidence_lineage_ids", "disposition", "training_eligible", "residual_codes", "eligibility", "receipt_sha256"}
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != required_row_keys:
            raise OriginalRowAdmissionError("row receipt schema drift")
        row_body = dict(row)
        row_hash = row_body.pop("receipt_sha256")
        if not isinstance(row_hash, str) or row_hash != sha256_value(row_body):
            raise OriginalRowAdmissionError("row receipt hash drift")
        if row.get("disposition") not in {"admitted", "rejected"} or row.get("training_eligible") != (row.get("disposition") == "admitted"):
            raise OriginalRowAdmissionError("row receipt eligibility drift")
    return dict(receipt)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON list of original row fixtures")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        rows = json.loads(args.input.read_text(encoding="utf-8"))
        receipt = admit_rows(rows)
        args.output.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
    except (OriginalRowAdmissionError, OSError, json.JSONDecodeError) as exc:
        print(f"V4 original-row admission: FAIL: {exc}", file=sys.stderr)
        return 1
    print(canonical_json({"receipt_sha256": receipt["receipt_sha256"], **receipt["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
