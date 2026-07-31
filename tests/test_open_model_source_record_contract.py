"""Focused tests for the fail-closed open-model source-record contract."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/projects/open_model_data/validate_source_records.py"
EXAMPLE = ROOT / "data/projects/open_model_data/contracts/source_record_v1.example.json"
OLD_CANDIDATE = ROOT / "data/datasets/hramatka_literary_poltava_v1/hramatka_literary_poltava_v1.jsonl"
SPEC = importlib.util.spec_from_file_location("source_record_contract", SCRIPT)
CONTRACT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CONTRACT)


def example_record() -> dict[str, object]:
    record = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    record["contract_schema_sha256"] = CONTRACT.load_schema()[1]
    return record


def test_schema_and_synthetic_example_are_admitted() -> None:
    schema, schema_hash = CONTRACT.load_schema()
    committed_receipt = CONTRACT.validate_path(EXAMPLE)
    assert committed_receipt["contract_schema_sha256"] == schema_hash
    assert committed_receipt["input_kind"] == "source_record_v1"
    assert committed_receipt["admitted_records"] == 1
    assert committed_receipt["rejected_records"] == 0
    assert committed_receipt["results"] == [
        {"admitted": True, "record_id": "record.synthetic-001", "reasons": []}
    ]
    record = example_record()
    assert list(Draft202012Validator(schema).iter_errors(record)) == []
    result = CONTRACT.validate_record(record, Draft202012Validator(schema), schema_hash)
    assert result == {"admitted": True, "record_id": "record.synthetic-001", "reasons": []}


def test_fail_closed_unknown_conflicting_rejected_and_evaluation_only() -> None:
    schema, schema_hash = CONTRACT.load_schema()
    validator = Draft202012Validator(schema)
    for status, expected in (("unknown", "license_status_unknown"), ("conflicting", "license_status_conflicting"), ("denied", "license_status_denied")):
        record = example_record()
        record["rights"]["license"]["status"] = status
        record["rights"]["license"]["license_expression"] = None
        record["rights"]["license"]["license_terms_evidence_id"] = None
        assert expected in CONTRACT.validate_record(record, validator, schema_hash)["reasons"]
    evaluation = example_record()
    evaluation["usage"]["role"] = "evaluation_only"
    assert CONTRACT.validate_record(evaluation, validator, schema_hash)["reasons"] == [
        "evaluation_only_never_admitted_to_training_or_export"
    ]


def test_granted_license_requires_exact_terms_receipt() -> None:
    schema, schema_hash = CONTRACT.load_schema()
    validator = Draft202012Validator(schema)
    missing_expression = example_record()
    missing_expression["rights"]["license"]["license_expression"] = None
    assert "license_expression_missing" in CONTRACT.validate_record(missing_expression, validator, schema_hash)["reasons"]
    missing_receipt = example_record()
    missing_receipt["evidence"][0]["sha256"] = None
    assert "license_exact_terms_receipt_incomplete" in CONTRACT.validate_record(missing_receipt, validator, schema_hash)["reasons"]
    duplicate_receipt = example_record()
    duplicate_receipt["evidence"].append(copy.deepcopy(duplicate_receipt["evidence"][0]))
    assert "duplicate_evidence_id" in CONTRACT.validate_record(duplicate_receipt, validator, schema_hash)["reasons"]


def test_provenance_urls_are_validated_without_optional_format_packages() -> None:
    schema, schema_hash = CONTRACT.load_schema()
    validator = Draft202012Validator(schema)
    invalid_acquisition = example_record()
    invalid_acquisition["acquisition"]["source_or_catalog_url"] = "not a url"
    assert "acquisition_source_or_catalog_url_invalid" in CONTRACT.validate_record(
        invalid_acquisition, validator, schema_hash
    )["reasons"]
    invalid_evidence = example_record()
    invalid_evidence["evidence"][0]["url"] = "https://named-user@example.invalid/terms"
    assert "evidence_url_invalid" in CONTRACT.validate_record(invalid_evidence, validator, schema_hash)[
        "reasons"
    ]


def test_derived_requires_complete_lineage_and_schema_hash() -> None:
    schema, schema_hash = CONTRACT.load_schema()
    validator = Draft202012Validator(schema)
    derived = example_record()
    derived["derivation"] = {"kind": "derived", "parent_content_sha256": "a" * 64, "transform_receipt_id": "receipt.synthetic-transform"}
    assert CONTRACT.validate_record(derived, validator, schema_hash)["admitted"] is True
    incomplete = copy.deepcopy(derived)
    incomplete["derivation"]["transform_receipt_id"] = None
    assert "derived_record_missing_lineage" in CONTRACT.validate_record(incomplete, validator, schema_hash)["reasons"]
    stale = copy.deepcopy(derived)
    stale["contract_schema_sha256"] = "b" * 64
    assert "contract_schema_sha256_mismatch" in CONTRACT.validate_record(stale, validator, schema_hash)["reasons"]


def test_remaining_fail_closed_admission_reasons() -> None:
    schema, schema_hash = CONTRACT.load_schema()
    validator = Draft202012Validator(schema)
    source_with_lineage = example_record()
    source_with_lineage["derivation"]["parent_content_sha256"] = "a" * 64
    assert "source_record_has_derivation_lineage" in CONTRACT.validate_record(
        source_with_lineage, validator, schema_hash
    )["reasons"]
    missing_evidence_reference = example_record()
    missing_evidence_reference["rights"]["copyright"]["evidence_ids"] = ["evidence.missing"]
    assert "copyright_evidence_reference_missing" in CONTRACT.validate_record(
        missing_evidence_reference, validator, schema_hash
    )["reasons"]
    missing_terms_receipt = example_record()
    missing_terms_receipt["rights"]["license"]["license_terms_evidence_id"] = "evidence.missing"
    assert "license_exact_terms_evidence_missing" in CONTRACT.validate_record(
        missing_terms_receipt, validator, schema_hash
    )["reasons"]
    unresolved = example_record()
    unresolved["review"]["unresolved"] = True
    assert "review_unresolved" in CONTRACT.validate_record(unresolved, validator, schema_hash)["reasons"]
    excluded = example_record()
    excluded["usage"]["role"] = "excluded"
    assert "record_marked_excluded" in CONTRACT.validate_record(excluded, validator, schema_hash)["reasons"]
    schema_invalid = example_record()
    del schema_invalid["rights"]
    assert CONTRACT.validate_record(schema_invalid, validator, schema_hash)["reasons"] == ["schema_invalid"]


def test_legacy_candidate_is_content_blind_deterministic_and_unchanged() -> None:
    before = CONTRACT.sha256_file(OLD_CANDIDATE)
    first = CONTRACT.validate_path(OLD_CANDIDATE)
    second = CONTRACT.validate_path(OLD_CANDIDATE)
    assert first == second
    assert first["total_records"] == 5000
    assert first["admitted_records"] == 0
    assert first["input_sha256"] == before == "06923700a0f5a6bbb077221325b8b7cc2b5e0a094100569494af32acd52c3424"
    assert set(first["rejection_reason_counts"]) == set(CONTRACT.LEGACY_MISSING_FIELDS)
    assert first["input_kind"] == "legacy_non_contract"
    assert first["legacy_records"] == 5000
    assert first["contract_records"] == 0
    assert first["results"] == []
    assert CONTRACT.sha256_file(OLD_CANDIDATE) == before


def test_mixed_batch_preserves_per_record_dispositions(tmp_path: Path) -> None:
    mixed_path = tmp_path / "mixed.json"
    mixed_path.write_text(
        json.dumps([example_record(), "legacy content is not emitted"]),
        encoding="utf-8",
    )

    result = CONTRACT.validate_path(mixed_path)

    assert result["input_kind"] == "mixed"
    assert result["contract_records"] == 1
    assert result["legacy_records"] == 1
    assert result["admitted_records"] == 1
    assert result["rejected_records"] == 1
    assert result["results"] == [
        {"admitted": False, "record_id": None, "reasons": list(CONTRACT.LEGACY_MISSING_FIELDS)},
        {"admitted": True, "record_id": "record.synthetic-001", "reasons": []},
    ]


def test_empty_input_has_an_explicit_receipt_kind(tmp_path: Path) -> None:
    empty_path = tmp_path / "empty.json"
    empty_path.write_text("[]", encoding="utf-8")

    result = CONTRACT.validate_path(empty_path)

    assert result["input_kind"] == "empty"
    assert result["total_records"] == 0
    assert result["contract_records"] == 0
    assert result["legacy_records"] == 0
    assert result["admitted_records"] == 0
    assert result["rejected_records"] == 0
    assert result["results"] == []
