from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_university_content_audit_freeze as freeze

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = (
    ROOT
    / "data/projects/open_model_data/admission/phase3_university_content_audit_freeze_v1.json"
)


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


def test_policy_and_database_subsets_are_exact_and_disjoint() -> None:
    universe = _artifact()["source_universe"]
    candidates = set(universe["candidate_source_ids"])
    database = set(universe["database_resident_source_ids"])
    references = set(universe["reference_only_source_ids"])
    quarantines = set(universe["quarantine_source_ids"])
    mandatory = set(universe["mandatory_conversion_source_ids"])
    assert len(candidates) == 30
    assert len(database) == 20
    assert len(references) == 6
    assert len(quarantines) == 4
    assert len(mandatory) == 11
    assert not (database & references or database & quarantines or references & quarantines)
    assert database | references | quarantines == candidates
    assert mandatory <= database
    assert set(universe["live_ingested_source_ids"]) == freeze.LIVE_INGESTED_SOURCE_IDS


def test_all_26_topic_gaps_are_explicit_without_quarantine_support() -> None:
    document = _artifact()
    topics = document["topic_coverage"]["topics"]
    quarantines = set(document["source_universe"]["quarantine_source_ids"])
    assert {topic["area"] for topic in topics} == freeze.EXPECTED_TOPIC_AREAS
    assert sum(topic["status"] == "partial" for topic in topics) == 21
    assert sum(topic["status"] == "sufficient" for topic in topics) == 5
    assert all(topic["qualified_source_needed"].strip() for topic in topics)
    assert all(not (set(topic["supporting_source_ids"]) & quarantines) for topic in topics)
    text_linguistics = next(topic for topic in topics if topic["area"] == "text linguistics")
    assert "candidate" not in text_linguistics["supported_depth"]
    assert text_linguistics["qualified_source_needed"].startswith("None;")
    assert document["topic_coverage"]["post_review_reconciliations"] == [
        {
            "area": "text linguistics",
            "prior_status": "partial",
            "final_status": "sufficient",
            "reason": (
                "The final Ukrainian source review admitted Shevel and Bilyk (2024) with no missing evidence, "
                "and the exact 282-row source is now live database-resident and Drive-backed."
            ),
        }
    ]


def test_rejects_database_source_set_substitution_even_with_fresh_receipt_hash() -> None:
    document = copy.deepcopy(_artifact())
    document["source_universe"]["database_resident_source_ids"][0] = (
        "uni-ukrmova-vlasova-2023"
    )
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
        iter(
            set(universe["database_resident_source_ids"])
            - set(universe["mandatory_conversion_source_ids"])
        )
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


def test_text_guard() -> None:
    document = copy.deepcopy(_artifact())
    document["topic_coverage"]["topics"][0]["source_text"] = "forbidden"
    with pytest.raises(freeze.UniversityContentAuditFreezeError, match="Additional properties"):
        freeze.validate_document(_rehash(document))


def test_cli_check_validates_tracked_freeze() -> None:
    assert freeze.main([]) == 0
