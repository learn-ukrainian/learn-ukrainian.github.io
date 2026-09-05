#!/usr/bin/env python3
"""Fail-closed admission receipts for independently authored V4 silver/gold rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "v4-original-row-admission-v1"
INPUT_SCHEMA_VERSION = "v4-original-row-admission-input-v1"
RECONSTRUCTION_GATES = ("exact", "fuzzy", "structural", "cumulative", "reconstruction")
MODEL_ONLY_BASES = frozenset({"model_agreement", "arena_vote", "model_vote"})
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RIGHTS_OPERATION_CELLS = frozenset({"training", "derived_dataset_redistribution"})


class OriginalRowAdmissionError(ValueError):
    """The batch shape is not safe to evaluate."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_value(value: Any) -> str:
    return hashlib.sha256((canonical_json(value) + "\n").encode("utf-8")).hexdigest()


def _sha256(value: Any, field: str, residuals: list[str]) -> str | None:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        residuals.append(f"{field.upper()}_INVALID")
        return None
    return value


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


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
    row_content_sha256 = _sha256(row.get("row_content_sha256"), "row_content_sha256", residuals)
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
    elif not isinstance(authorship, Mapping):
        residuals.append("AUTHORSHIP_OR_DIRECT_TEXT_CLEARANCE_REQUIRED")
    elif authorship.get("independently_authored") is True:
        if not _nonempty_string(authorship.get("receipt_id")):
            residuals.append("AUTHORSHIP_RECEIPT_ID_REQUIRED")
    else:
        clearance = authorship.get("direct_text_clearance")
        if not isinstance(clearance, Mapping) or clearance.get("cleared") is not True:
            residuals.append("AUTHORSHIP_OR_DIRECT_TEXT_CLEARANCE_REQUIRED")
        else:
            if not _nonempty_string(clearance.get("operation_id")):
                residuals.append("DIRECT_TEXT_CLEARANCE_OPERATION_ID_REQUIRED")
            if not _nonempty_string(clearance.get("receipt_id")):
                residuals.append("DIRECT_TEXT_CLEARANCE_RECEIPT_ID_REQUIRED")

    evidence = row.get("evidence")
    if _basis_is_model_only(evidence):
        residuals.append("MODEL_AGREEMENT_CANNOT_SATISFY_EVIDENCE")
    elif not isinstance(evidence, Mapping) or evidence.get("grade") != "verified" or evidence.get("uncertainty") not in {"resolved", "bounded"} or evidence.get("disposition") not in {"supported", "admitted"}:
        residuals.append("EVIDENCE_NOT_VERIFIED")
    elif not _nonempty_string(evidence.get("receipt_id")):
        residuals.append("VERIFIED_EVIDENCE_RECEIPT_ID_REQUIRED")

    rights = row.get("rights")
    if _basis_is_model_only(rights):
        residuals.append("MODEL_AGREEMENT_CANNOT_SATISFY_RIGHTS")
    if not isinstance(rights, Mapping) or rights.get("training") is not True:
        residuals.append("TRAINING_RIGHTS_NOT_GRANTED")
    if not isinstance(rights, Mapping) or rights.get("derived_dataset_redistribution") is not True:
        residuals.append("DERIVED_DATASET_REDISTRIBUTION_RIGHTS_NOT_GRANTED")
    if isinstance(rights, Mapping) and (
        rights.get("training") is True or rights.get("derived_dataset_redistribution") is True
    ):
        if not _nonempty_string(rights.get("receipt_id")):
            residuals.append("RIGHTS_RECEIPT_ID_REQUIRED")
        operation_cells = rights.get("operation_cells")
        if not isinstance(operation_cells, list) or not all(isinstance(cell, str) for cell in operation_cells):
            operation_cells = []
        for operation in RIGHTS_OPERATION_CELLS:
            if rights.get(operation) is True and operation not in operation_cells:
                residuals.append(f"{operation.upper()}_RIGHTS_OPERATION_CELL_UNCOVERED")

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

    if any(row.get(alias) is True for alias in MODEL_ONLY_BASES):
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
        "row_content_sha256": row_content_sha256,
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


def admit_rows(*, outcome_sha256: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise OriginalRowAdmissionError("rows must be a list")
    outcome_sha256 = _sha256(outcome_sha256, "outcome_sha256", [])
    if outcome_sha256 is None:
        raise OriginalRowAdmissionError("OUTCOME_SHA256_INVALID")
    receipts = [evaluate_row(row) for row in rows]
    ids = [item["row_id"] for item in receipts]
    if any(item is None for item in ids) or len(ids) != len(set(ids)):
        raise OriginalRowAdmissionError("row IDs must be stable and unique in a batch")
    result = {
        "schema_version": SCHEMA_VERSION,
        "visibility": "machine_receipt_text_free",
        "outcome_sha256": outcome_sha256,
        "rows": receipts,
        "counts": {"input_rows": len(receipts), "admitted_rows": sum(item["disposition"] == "admitted" for item in receipts), "rejected_rows": sum(item["disposition"] == "rejected" for item in receipts)},
    }
    result["receipt_sha256"] = sha256_value(result)
    return result


def assemble_receipt_from_row_receipts(*, outcome_sha256: str, row_receipts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Assemble an aggregate admission receipt from already-evaluated row
    receipts (each already produced by ``evaluate_row`` -- never re-derived
    or trusted beyond its own shape here).

    Downstream per-slot stages (A7/A8) carry forward already-evaluated,
    text-free row receipts from a private replay rather than raw row
    inputs (the raw inputs, and the real corpus/lineage facts behind them,
    stay in the private ledger that produced these receipts -- never here).
    The aggregate shape and hashing are byte-identical to ``admit_rows``'s
    own post-processing, so a caller with zero row receipts gets exactly
    ``admit_rows(rows=[])``'s output -- this never changes today's real,
    zero-completion production behavior.
    """
    if not isinstance(row_receipts, Sequence) or isinstance(row_receipts, (str, bytes)):
        raise OriginalRowAdmissionError("row_receipts must be a list")
    outcome_sha256 = _sha256(outcome_sha256, "outcome_sha256", [])
    if outcome_sha256 is None:
        raise OriginalRowAdmissionError("OUTCOME_SHA256_INVALID")
    receipts = list(row_receipts)
    ids = [item.get("row_id") if isinstance(item, Mapping) else None for item in receipts]
    if any(item is None for item in ids) or len(ids) != len(set(ids)):
        raise OriginalRowAdmissionError("row IDs must be stable and unique in a batch")
    result = {
        "schema_version": SCHEMA_VERSION,
        "visibility": "machine_receipt_text_free",
        "outcome_sha256": outcome_sha256,
        "rows": receipts,
        "counts": {
            "input_rows": len(receipts),
            "admitted_rows": sum(item.get("disposition") == "admitted" for item in receipts),
            "rejected_rows": sum(item.get("disposition") == "rejected" for item in receipts),
        },
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
    if set(body) != {"schema_version", "visibility", "outcome_sha256", "rows", "counts"} or body.get("visibility") != "machine_receipt_text_free":
        raise OriginalRowAdmissionError("receipt schema drift")
    if not isinstance(body.get("outcome_sha256"), str) or SHA256_RE.fullmatch(body["outcome_sha256"]) is None:
        raise OriginalRowAdmissionError("receipt outcome SHA-256 drift")
    rows, counts = body.get("rows"), body.get("counts")
    if not isinstance(rows, list) or not isinstance(counts, Mapping):
        raise OriginalRowAdmissionError("receipt schema drift")
    if counts != {"input_rows": len(rows), "admitted_rows": sum(item.get("disposition") == "admitted" for item in rows if isinstance(item, Mapping)), "rejected_rows": sum(item.get("disposition") == "rejected" for item in rows if isinstance(item, Mapping))}:
        raise OriginalRowAdmissionError("receipt count drift")
    required_row_keys = {"row_id", "row_content_sha256", "label_tier", "source_lineage_ids", "evidence_lineage_ids", "disposition", "training_eligible", "residual_codes", "eligibility", "receipt_sha256"}
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != required_row_keys:
            raise OriginalRowAdmissionError("row receipt schema drift")
        row_body = dict(row)
        row_hash = row_body.pop("receipt_sha256")
        if not isinstance(row_hash, str) or row_hash != sha256_value(row_body):
            raise OriginalRowAdmissionError("row receipt hash drift")
        row_content_sha256 = row.get("row_content_sha256")
        if row_content_sha256 is not None and (not isinstance(row_content_sha256, str) or SHA256_RE.fullmatch(row_content_sha256) is None):
            raise OriginalRowAdmissionError("row receipt content SHA-256 drift")
        if row.get("disposition") == "admitted" and row_content_sha256 is None:
            raise OriginalRowAdmissionError("row receipt content SHA-256 drift")
        if row.get("disposition") not in {"admitted", "rejected"} or row.get("training_eligible") != (row.get("disposition") == "admitted"):
            raise OriginalRowAdmissionError("row receipt eligibility drift")
    return dict(receipt)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="versioned JSON object containing outcome_sha256 and rows")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping) or set(payload) != {"schema_version", "outcome_sha256", "rows"} or payload.get("schema_version") != INPUT_SCHEMA_VERSION:
            raise OriginalRowAdmissionError("input schema drift")
        receipt = admit_rows(outcome_sha256=payload["outcome_sha256"], rows=payload["rows"])
        args.output.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
    except (OriginalRowAdmissionError, OSError, json.JSONDecodeError) as exc:
        print(f"V4 original-row admission: FAIL: {exc}", file=sys.stderr)
        return 1
    print(canonical_json({"receipt_sha256": receipt["receipt_sha256"], **receipt["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
