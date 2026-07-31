"""Validate source-record provenance contracts without creating dataset artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_DIR = ROOT / "data/projects/open_model_data/contracts"
SCHEMA_PATH = CONTRACT_DIR / "source_record_v1.schema.json"
LEGACY_MISSING_FIELDS = (
    "acquisition_source",
    "copyright_status",
    "edition_or_editor",
    "external_source_or_catalog_id",
    "license",
    "model_training_permission",
    "redistribution_permission",
    "region",
    "register",
    "translation_origin",
)
REQUIRED_GRANTED_RIGHTS = ("copyright", "license", "redistribution", "model_training")


def canonical_json(value: Any) -> str:
    """Return stable JSON for machine-readable receipts."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    """Hash an input without retaining or emitting its contents."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_schema() -> tuple[dict[str, Any], str]:
    """Load the pinned Draft 2020-12 schema and its byte hash."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema, sha256_file(SCHEMA_PATH)


def load_records(path: Path) -> list[dict[str, Any]]:
    """Load one JSON record, a JSON list, or JSONL deterministically."""
    raw = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in raw.splitlines() if line.strip()]
    value = json.loads(raw)
    return value if isinstance(value, list) else [value]


def _schema_errors(record: dict[str, Any], validator: Draft202012Validator) -> list[str]:
    return sorted(error.message for error in validator.iter_errors(record))


def _semantic_reasons(record: dict[str, Any], schema_hash: str) -> list[str]:
    reasons: list[str] = []
    if record.get("contract_schema_sha256") != schema_hash:
        reasons.append("contract_schema_sha256_mismatch")
    derivation = record.get("derivation", {})
    if derivation.get("kind") == "source" and any(
        derivation.get(field) is not None for field in ("parent_content_sha256", "transform_receipt_id")
    ):
        reasons.append("source_record_has_derivation_lineage")
    if derivation.get("kind") == "derived" and any(
        derivation.get(field) is None for field in ("parent_content_sha256", "transform_receipt_id")
    ):
        reasons.append("derived_record_missing_lineage")
    evidence_ids = {item["evidence_id"] for item in record.get("evidence", []) if "evidence_id" in item}
    for right_name in REQUIRED_GRANTED_RIGHTS:
        statement = record.get("rights", {}).get(right_name, {})
        if statement.get("status") != "granted":
            reasons.append(f"{right_name}_status_{statement.get('status', 'missing')}")
        if not set(statement.get("evidence_ids", [])).issubset(evidence_ids):
            reasons.append(f"{right_name}_evidence_reference_missing")
    license_statement = record.get("rights", {}).get("license", {})
    terms_id = license_statement.get("license_terms_evidence_id")
    evidence_by_id = {item.get("evidence_id"): item for item in record.get("evidence", [])}
    if license_statement.get("status") == "granted":
        if not license_statement.get("license_expression"):
            reasons.append("license_expression_missing")
        terms_evidence = evidence_by_id.get(terms_id)
        if terms_id not in license_statement.get("evidence_ids", []) or not terms_evidence:
            reasons.append("license_exact_terms_evidence_missing")
        elif not terms_evidence.get("url") or not terms_evidence.get("sha256"):
            reasons.append("license_exact_terms_receipt_incomplete")
    review = record.get("review", {})
    if review.get("unresolved") is True:
        reasons.append("review_unresolved")
    usage = record.get("usage", {})
    if usage.get("role") == "evaluation_only":
        reasons.append("evaluation_only_never_admitted_to_training_or_export")
    if usage.get("role") == "excluded":
        reasons.append("record_marked_excluded")
    return sorted(set(reasons))


def validate_record(record: dict[str, Any], validator: Draft202012Validator, schema_hash: str) -> dict[str, Any]:
    """Return a content-blind admission disposition for one contract record."""
    schema_errors = _schema_errors(record, validator)
    if schema_errors:
        return {"admitted": False, "record_id": record.get("record_id"), "reasons": ["schema_invalid"]}
    reasons = _semantic_reasons(record, schema_hash)
    return {"admitted": not reasons, "record_id": record["record_id"], "reasons": reasons}


def validate_path(path: Path) -> dict[str, Any]:
    """Validate a source-contract input and emit deterministic aggregate results."""
    schema, schema_hash = load_schema()
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records = load_records(path)
    outcomes: list[dict[str, Any]] = []
    legacy_input = False
    for record in records:
        if record.get("schema_version") != "source_record_v1":
            legacy_input = True
            outcomes.append({"admitted": False, "record_id": None, "reasons": list(LEGACY_MISSING_FIELDS)})
        else:
            outcomes.append(validate_record(record, validator, schema_hash))
    counts = Counter(reason for outcome in outcomes for reason in outcome["reasons"])
    return {
        "admitted_records": sum(outcome["admitted"] for outcome in outcomes),
        "contract_schema_sha256": schema_hash,
        "input_kind": "legacy_non_contract" if legacy_input else "source_record_v1",
        "input_sha256": sha256_file(path),
        "rejected_records": len(outcomes) - sum(outcome["admitted"] for outcome in outcomes),
        "rejection_reason_counts": dict(sorted(counts.items())),
        "results": [] if legacy_input else sorted(outcomes, key=lambda item: (str(item["record_id"]), canonical_json(item))),
        "total_records": len(outcomes),
        "validator_version": "source_record_v1",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed source-record contract validator")
    parser.add_argument("input", type=Path, help="JSON, JSON-list, or JSONL input")
    args = parser.parse_args()
    print(canonical_json(validate_path(args.input)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
