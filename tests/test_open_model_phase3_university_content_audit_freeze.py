from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_university_content_audit_freeze as freeze

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = freeze.DEFAULT_OUTPUT_PATH


def _artifact() -> dict:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def _rehash(document: dict) -> dict:
    document["receipt_sha256"] = freeze.receipt_sha256(document)
    return document


def test_tracked_freeze_validates_and_is_byte_pinned() -> None:
    document = freeze.validate_document(_artifact())
    assert freeze.sha256_file(ARTIFACT_PATH) == freeze.EXPECTED_OUTPUT_SHA256
    assert document["status"] == freeze.STATUS
    assert document["database"] == freeze.EXPECTED_DATABASE
    assert document["gates"] == {
        "university_content_audit_complete": True,
        "university_database_reconciled": True,
        "university_source_freeze_ready": True,
        "source_coverage_ready": False,
        "overall_phase3_source_freeze_ready": False,
        "phase3_complete": False,
        "phase4_blocked": True,
    }


def test_rejects_database_source_set_substitution_even_with_fresh_receipt_hash() -> None:
    document = copy.deepcopy(_artifact())
    document["source_universe"]["database_resident_source_ids"][0] = "uni-ukrmova-vlasova-2023"
    with pytest.raises(freeze.UniversityContentAuditFreezeError, match="database_resident_source_ids"):
        freeze.validate_document(_rehash(document))


def test_rejects_suppressed_partial_gap_even_with_fresh_receipt_hash() -> None:
    document = copy.deepcopy(_artifact())
    topic = next(row for row in document["topic_coverage"]["topics"] if row["status"] == "partial")
    topic["qualified_source_needed"] = "None; suppressed."
    with pytest.raises(freeze.UniversityContentAuditFreezeError, match="cannot suppress"):
        freeze.validate_document(_rehash(document))


def test_authority_lane() -> None:
    document = copy.deepcopy(_artifact())
    universe = document["source_universe"]
    contextual_id = next(
        iter(set(universe["database_resident_source_ids"]) - set(universe["mandatory_conversion_source_ids"]))
    )
    topic = next(row for row in document["topic_coverage"]["topics"] if row["status"] == "sufficient")
    topic["supporting_source_ids"] = [contextual_id]
    with pytest.raises(freeze.UniversityContentAuditFreezeError, match="mandatory authority"):
        freeze.validate_document(_rehash(document))


def test_rejects_source_coverage_or_phase_completion_claims() -> None:
    for field in ("source_coverage_ready", "overall_phase3_source_freeze_ready", "phase3_complete"):
        document = copy.deepcopy(_artifact())
        document["gates"][field] = True
        with pytest.raises(freeze.UniversityContentAuditFreezeError):
            freeze.validate_document(_rehash(document))
