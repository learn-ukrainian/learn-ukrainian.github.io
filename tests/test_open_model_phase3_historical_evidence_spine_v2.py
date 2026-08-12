"""Tests for the current Phase 3 historical evidence and gap matrix."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_historical_evidence_spine_v2 as spine


def _reseal(value: dict) -> dict:
    value["receipt_sha256"] = spine.sha256_value({key: item for key, item in value.items() if key != "receipt_sha256"})
    return value


def _tracked() -> dict:
    return json.loads(spine.SPINE_PATH.read_text(encoding="utf-8"))


def test_tracked_spine_validates_and_preserves_open_gates() -> None:
    value = spine.load_spine()
    assert value["status"] == "HISTORICAL_EVIDENCE_SPINE_UPDATED_SOURCE_GAPS_OPEN"
    assert len(value["collections"]) == 5
    assert len(value["gap_dispositions"]) == 11
    assert value["framework_policy"]["canonical_framework_id"] is None
    assert value["gates"] == {
        "historical_content_gap_matrix_current": True,
        "incremental_private_receipt_and_output_hashes_verified": True,
        "qualified_historical_semantic_review_complete": False,
        "historical_source_coverage_ready": False,
        "historical_source_freeze_ready": False,
        "phase3_complete": False,
        "phase4_authorized": False,
        "phase4_blocked": True,
    }


def test_every_collection_is_fail_closed_for_semantic_training() -> None:
    value = spine.load_spine()
    for collection in value["collections"]:
        assert collection["phase3_historical_training_eligible"] is False
        assert collection["semantic_gold"] is False
        assert collection["modern_correction_eligible"] is False
        assert collection["residual_gap_ids"]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value["framework_policy"].update(
                {"canonical_framework_id": "university_five_stage_synthesis"}
            ),
            "schema violation",
        ),
        (
            lambda value: value["collections"][1].update({"phase3_historical_training_eligible": True}),
            "schema violation",
        ),
        (
            lambda value: value["collections"][1]["counts"].update({"catalog_records": 476}),
            "collection matrix drift",
        ),
        (
            lambda value: value["gap_dispositions"][0].update({"current_state": "open"}),
            "gap disposition matrix drift",
        ),
        (
            lambda value: value["gates"].update({"phase3_complete": True}),
            "schema violation",
        ),
        (
            lambda value: value["coverage_matrix"][0]["residual_gap_ids"].append("unknown-gap"),
            "unknown gap",
        ),
    ],
)
def test_spine_rejects_overclaim_and_denominator_drift(mutation, message: str) -> None:
    value = _tracked()
    mutation(value)
    _reseal(value)
    with pytest.raises(spine.HistoricalEvidenceSpineV2Error, match=message):
        spine.validate_spine(value)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value["collections"][0]["rights"].update({"reuse_scope": "public_training"}),
            "collection matrix drift",
        ),
        (
            lambda value: value["coverage_matrix"][0].update({"coverage_state": "expanded_but_insufficient"}),
            "coverage matrix drift",
        ),
        (
            lambda value: value["gap_dispositions"][0].update({"do_not_claim": "weakened"}),
            "gap disposition matrix drift",
        ),
    ],
)
def test_spine_rejects_resealed_rights_coverage_and_gap_text_drift(mutation, message: str) -> None:
    value = _tracked()
    mutation(value)
    _reseal(value)
    with pytest.raises(spine.HistoricalEvidenceSpineV2Error, match=message):
        spine.validate_spine(value)


def test_spine_rejects_stale_receipt_seal() -> None:
    value = _tracked()
    value["gap_dispositions"][0]["evidence"] += " tampered"
    with pytest.raises(spine.HistoricalEvidenceSpineV2Error, match="seal mismatch"):
        spine.validate_spine(value)


def _fake_receipt(
    *,
    receipt_id: str,
    schema_version: str,
    output_records: int,
    output_bytes: bytes,
) -> dict:
    value: dict = {
        "schema_version": schema_version,
        "output": {
            "filename": f"{receipt_id}.jsonl.gz",
            "records": output_records,
            "sha256": hashlib.sha256(output_bytes).hexdigest(),
        },
    }
    if receipt_id == "historical-document-chronology-source-dates-v2":
        value.update(
            {
                "denominators": {
                    "plug2": {
                        "bounded_interval_documents": 0,
                        "eligible_documents": 56080,
                        "exact_year_documents": 56080,
                        "undated_documents": 0,
                    },
                    "total_bounded_interval": 2,
                    "total_documents": 56162,
                    "total_exact_year": 56160,
                    "ud": {
                        "bounded_interval_documents": 2,
                        "eligible_documents": 82,
                        "exact_year_documents": 80,
                        "undated_documents": 0,
                    },
                },
                "coverage": {"qualified_historical_semantic_review_complete": False},
            }
        )
    elif receipt_id == "spas-source-attribution-v1":
        value.update(
            {
                "denominator": {
                    "attributed_unresolved_record_overlap": 3,
                    "candidate_lines": 101,
                    "candidate_records": 90,
                    "input_records": 477,
                    "source_attributed_lines": 82,
                    "source_attributed_records": 81,
                    "unresolved_lines": 19,
                    "unresolved_records": 12,
                },
                "safeguards": {"semantic_gold": False},
            }
        )
    elif receipt_id == "lavra-near-caves-intake-v1":
        value.update(
            {
                "denominator": {"article_pages": 19},
                "residuals": {"lavra_cave_corpus_gap_closed": False},
                "safeguards": {"training_eligible": False},
            }
        )
    value["receipt_sha256"] = spine.sha256_value(value)
    return value


def _private_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict, Path]:
    drive_root = tmp_path / "historical_language_corpus"
    permissive_schema = tmp_path / "receipt.schema.json"
    permissive_schema.write_text(
        json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}),
        encoding="utf-8",
    )
    bindings: dict[str, dict] = {}
    schema_paths: dict[str, Path] = {}
    for index, (receipt_id, tracked_binding) in enumerate(spine.EXPECTED_PRIVATE_RECEIPTS.items(), start=1):
        relative = Path("processed") / receipt_id / f"{receipt_id}.json"
        receipt_path = drive_root / relative
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        output_bytes = f"private-output-{index}".encode()
        receipt = _fake_receipt(
            receipt_id=receipt_id,
            schema_version=tracked_binding["schema_version"],
            output_records=tracked_binding["output_records"],
            output_bytes=output_bytes,
        )
        output_path = receipt_path.parent / receipt["output"]["filename"]
        output_path.write_bytes(output_bytes)
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        bindings[receipt_id] = {
            "drive_relative_path": relative.as_posix(),
            "schema_version": tracked_binding["schema_version"],
            "file_sha256": spine.sha256_file(receipt_path),
            "receipt_sha256": receipt["receipt_sha256"],
            "output_records": tracked_binding["output_records"],
            "output_sha256": receipt["output"]["sha256"],
        }
        schema_paths[receipt_id] = permissive_schema

    monkeypatch.setattr(spine, "EXPECTED_PRIVATE_RECEIPTS", bindings)
    monkeypatch.setattr(spine, "EXPECTED_RECEIPT_SCHEMAS", schema_paths)
    value = _tracked()
    value["bindings"]["private_receipts"] = [
        {"receipt_id": receipt_id, **binding} for receipt_id, binding in bindings.items()
    ]
    _reseal(value)
    return value, drive_root


def test_private_receipt_replay_checks_receipts_and_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    value, drive_root = _private_fixture(tmp_path, monkeypatch)
    result = spine.audit_private_receipts(drive_root=drive_root, spine_value=value)
    assert result["verified_receipt_count"] == 6
    assert result["verified_output_record_sum"] == 57702
    assert result["text_free"] is True
    assert result["provider_calls"] is False


def test_private_receipt_replay_rejects_output_byte_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    value, drive_root = _private_fixture(tmp_path, monkeypatch)
    binding = value["bindings"]["private_receipts"][0]
    receipt_path = drive_root / binding["drive_relative_path"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    (receipt_path.parent / receipt["output"]["filename"]).write_bytes(b"tampered")
    with pytest.raises(spine.HistoricalEvidenceSpineV2Error, match="private output byte drift"):
        spine.audit_private_receipts(drive_root=drive_root, spine_value=value)


def test_v1_and_v2_artifacts_remain_distinct() -> None:
    value = spine.load_spine()
    assert value["supersedes"]["v1_file_sha256"] == spine.sha256_file(spine.spine_v1.SPINE_PATH)
    assert value["receipt_sha256"] != value["supersedes"]["v1_receipt_sha256"]


def test_load_rejects_bound_source_byte_drift(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    logical_path, expected_sha256 = next(iter(spine.EXPECTED_CODE_BINDINGS.items()))
    fake_root = tmp_path / "repo"
    fake_path = fake_root / logical_path
    fake_path.parent.mkdir(parents=True)
    fake_path.write_bytes(b"drifted")
    monkeypatch.setattr(spine, "ROOT", fake_root)
    monkeypatch.setattr(spine.spine_v1, "load_spine", lambda: {"receipt_sha256": spine.EXPECTED_V1_RECEIPT_SHA256})

    def fake_sha256(path: Path) -> str:
        path = Path(path)
        if path == spine.spine_v1.SPINE_PATH:
            return spine.EXPECTED_V1_SHA256
        if path == spine.spine_v1.SCHEMA_PATH:
            return spine.EXPECTED_V1_SCHEMA_SHA256
        if path == fake_path:
            return "0" * 64
        return expected_sha256

    monkeypatch.setattr(spine, "sha256_file", fake_sha256)
    with pytest.raises(spine.HistoricalEvidenceSpineV2Error, match="bound source byte drift"):
        spine.load_spine(spine.SPINE_PATH)
