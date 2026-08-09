from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.projects.open_model_data import textbook_curriculum_coverage as coverage

ROOT = Path(__file__).resolve().parents[1]
DENOMINATOR = ROOT / "data" / "textbook_curriculum_denominator.yaml"
UNIVERSITY_DENOMINATOR = ROOT / "data" / "university_corpus_denominator.yaml"


def _cell(
    cell_id: str,
    *,
    grade: int = 1,
    requirement_class: str = "required_common",
    applicability: str = "required",
    source_ids: list[str] | None = None,
    evidence_state: str = "resolved",
    coverage_unit_id: str | None = None,
    choice_group_id: str | None = None,
    choice_member_id: str | None = None,
    choice_member_requires: list[str] | None = None,
    legacy_ids: list[str] | None = None,
) -> dict:
    result = {
        "cell_id": cell_id,
        "grade": grade,
        "canonical_subject_id": "fixture_subject",
        "display_name_uk": "Тестова клітинка",
        "cohort_or_effective_basis": "fixture current basis",
        "requirement_class": requirement_class,
        "official_program_locator_ids": ["PROGRAM"],
        "official_edition_catalog_locator_ids": ["EDITION"],
        "textbook_applicability": applicability,
        "coverage": {
            "coverage_unit_id": coverage_unit_id or cell_id,
            "source_ids": source_ids or [],
            "source_groups": [],
            "source_match_mode": "any",
            "evidence_state": evidence_state,
            "legacy_inventory_source_ids": legacy_ids or [],
            "edition_policy": "fixture_current",
        },
        "evidence_note": "Fixture evidence note.",
    }
    if choice_group_id is not None:
        result["choice_group_id"] = choice_group_id
        result["choice_member_id"] = choice_member_id
        result["choice_member_requires"] = choice_member_requires or [cell_id]
    return result


def _denominator(*cells: dict) -> dict:
    return {
        "schema_version": "textbook_curriculum_denominator_v1",
        "requirement_classes": list(coverage.REQUIREMENT_CLASSES),
        "locator_registry": {
            "PROGRAM": "https://example.test/program",
            "EDITION": "https://example.test/edition",
        },
        "cells": list(cells),
    }


def _readiness(*sources: tuple[str, str], selected_count: int = 0) -> dict:
    return {
        "schema_version": "textbook_corpus_readiness_v1",
        "selection": {"selected_count": selected_count},
        "sources": [
            {"source": source, "status": status, "selection_ids": []}
            for source, status in sources
        ],
        "counts": {},
    }


def test_range_expansion_is_materialized_and_selection_is_separate(tmp_path: Path) -> None:
    denominator = coverage.load_denominator(DENOMINATOR)
    readiness_path = tmp_path / "readiness.json"
    readiness_path.write_text(
        json.dumps(_readiness(selected_count=116), sort_keys=True),
        encoding="utf-8",
    )
    report = coverage.build_report(
        denominator_path=DENOMINATOR,
        readiness_path=readiness_path,
    )

    assert len(denominator["cells"]) == 176
    assert {cell["grade"] for cell in denominator["cells"]} == set(range(1, 12))
    assert all(isinstance(cell["grade"], int) for cell in denominator["cells"])
    assert report["counts"]["by_requirement_class"] == {
        "required_common": 57,
        "required_one_of": 59,
        "profile_or_track": 26,
        "optional_elective": 23,
        "no_textbook_required_or_unresolved": 11,
    }
    assert report["selection"]["selected_count"] == 116
    assert report["selection"]["is_official_curriculum_denominator"] is False
    assert report["input_hashes"] == {
        "denominator_sha256": hashlib.sha256(DENOMINATOR.read_bytes()).hexdigest(),
        "readiness_sha256": hashlib.sha256(readiness_path.read_bytes()).hexdigest(),
    }


def test_foreign_languages_are_retained_but_non_gating() -> None:
    denominator = coverage.load_denominator(DENOMINATOR)
    foreign_cells = [
        cell
        for cell in denominator["cells"]
        if cell["canonical_subject_id"] == "foreign_language"
    ]

    assert {cell["grade"] for cell in foreign_cells} == set(range(1, 12))
    assert {cell["requirement_class"] for cell in foreign_cells} == {"optional_elective"}
    assert {cell["textbook_applicability"] for cell in foreign_cells} == {"optional"}


def test_grade_twelve_is_future_tracking_not_a_current_cell() -> None:
    denominator = coverage.load_denominator(DENOMINATOR)

    assert all(cell["grade"] <= 11 for cell in denominator["cells"])
    assert denominator["future_coverage"] == [
        {
            "future_id": "g12.all_subjects",
            "grade": 12,
            "status": "future_not_current",
            "hard_denominator": False,
            "acquisition_required_now": False,
            "earliest_applicable_school_year": "2029/30",
            "basis_note": "The new profile-school standard starts with Grade 10 on 1 September 2027; Grade 12 is tracked now but is not a current 2026/27 textbook gap.",
            "official_program_locator_ids": ["MON_P10_12"],
        }
    ]


def test_rights_blocked_grade_nine_candidate_cannot_close_coverage() -> None:
    denominator = coverage.load_denominator(DENOMINATOR)
    grade_nine = next(cell for cell in denominator["cells"] if cell["cell_id"] == "g09.ukrmova")
    candidate = grade_nine["candidate_sources"][0]

    assert grade_nine["coverage"]["source_ids"] == []
    assert grade_nine["coverage"]["evidence_state"] == "legacy_only"
    assert candidate["native_text_canary_state"] == "searchable_front_matter_verified"
    assert candidate["license_or_access_status"] == "public_download_all_rights_reserved"
    assert candidate["admission_state"] == "blocked_for_retention_and_model_corpus"


def test_gap_execution_plan_matches_the_non_gating_denominator() -> None:
    denominator = coverage.load_denominator(DENOMINATOR)
    plan = denominator["phase3_gap_execution"]
    exact_packets = plan["exact_page_verification_packets"]
    full_packets = plan["full_extraction_or_replacement_packets"]

    assert plan["hard_denominator_counts"] == {
        "required_cells": 116,
        "covered": 77,
        "choice_satisfied": 12,
        "extraction_missing": 20,
        "acquisition_missing": 7,
        "unresolved": 0,
    }
    assert plan["acquisition_interpretation"]["true_new_source_gap"] == ["g09.ukrmova"]
    assert sum(packet["affected_row_count"] for packet in exact_packets) == 13
    assert plan["exact_page_verification_status"]["verified_row_count"] == 13
    assert plan["covered_source_quality_status"]["repaired_row_count"] == 10
    assert (
        plan["covered_source_quality_status"][
            "verified_legitimate_foreign_diacritic_row_count"
        ]
        == 2
    )
    assert len(full_packets) == 12
    assert len({packet["source_file"] for packet in exact_packets + full_packets}) == 21
    assert all("angli" not in packet["source_file"] for packet in exact_packets + full_packets)


def test_university_layer_is_separate_and_topic_complete() -> None:
    university = yaml.safe_load(UNIVERSITY_DENOMINATOR.read_text(encoding="utf-8"))
    cells = university["topic_cells"]

    assert university["operation"]["counted_in_school_textbook_denominator"] is False
    assert len(cells) == 20
    assert len({cell["cell_id"] for cell in cells}) == len(cells)
    assert {cell["domain"] for cell in cells} == {
        "ukrainian_language",
        "ukrainian_literature",
        "history_of_ukraine",
        "arts",
    }
    assert all(cell["required"] is True for cell in cells)
    assert university["coverage_summary"] == {
        "required_cells": 20,
        "canary_passed": 18,
        "candidate": 2,
        "acquisition_research": 0,
        "residual_gap": 0,
        "accepted": 0,
        "acceptance_gate": (
            "A source closes a cell only after its rights, native text, Drive "
            "identities, and database identity pass."
        ),
    }
    assert university["source_admission_contract"]["quality_rules"]["guessed_text"] == "forbidden"
    sources = {source["source_id"]: source for source in university["sources"]}
    assert len(sources) == 12
    assert sum(source["admission_state"] == "accepted" for source in sources.values()) == 3
    assert sum(source["admission_state"] == "canary_passed" for source in sources.values()) == 7
    assert sum(source["admission_state"] == "candidate" for source in sources.values()) == 2
    assert all(
        source["database_identity"] is not None
        for source in sources.values()
        if source["admission_state"] == "accepted"
    )
    assert all(
        source["database_identity"] is None
        for source in sources.values()
        if source["admission_state"] != "accepted"
    )
    assert sources["uni-ukrlit-kalinichenko-2024"]["reuse_tier"] == "open_with_attribution"
    assert sources["uni-istoriya-levytska-2015"]["reuse_tier"] == "rights_scope_requires_confirmation"
    assert sources["uni-ukrmova-punctuation-marynenko-2021"]["native_text_canary_state"] == (
        "pass_no_ocr_276_of_276_pages_pypdf_backend"
    )
    assert sources["uni-mystetstvo-petutina-2012"]["native_text_canary_state"] == (
        "pass_no_ocr_136_of_136_pages_pdfkit_backend"
    )
    assert university["native_exactness_audit"]["source_count"] == 12
    assert university["native_exactness_audit"]["chunk_count"] == 2681
    assert university["native_exactness_audit"]["flagged_chunk_count"] == 62
    assert university["native_exactness_audit"]["verified_flagged_chunk_count"] == 62
    assert university["native_exactness_audit"]["unverified_flagged_chunk_count"] == 0
    assert sum(report["source_count"] for report in university["native_exactness_audit"]["reports"]) == 12
    rejected_ids = {
        item.get("source_id") for item in university["rejected_candidates"] if item.get("source_id")
    }
    assert {
        "uni-ukrmova-glukhovtseva-2021",
        "uni-ukrmova-morphology-aleksiienko-2014",
    } <= rejected_ids


def test_one_of_choice_is_satisfied_by_one_approved_alternative() -> None:
    first = _cell(
        "g01.choice_a",
        source_ids=["source-a"],
        choice_group_id="g01.fixture_choice",
        choice_member_id="a",
    )
    second = _cell(
        "g01.choice_b",
        source_ids=["source-b"],
        choice_group_id="g01.fixture_choice",
        choice_member_id="b",
    )
    report = coverage.evaluate(
        _denominator(first, second),
        _readiness(("source-a", "ready"), selected_count=2),
    )

    statuses = {item["cell_id"]: item["status"] for item in report["cells"]}
    assert statuses == {
        "g01.choice_a": "covered",
        "g01.choice_b": "choice_satisfied",
    }
    assert report["choice_groups"][0]["status"] == "choice_satisfied"
    assert report["choice_groups"][0]["selected_member_id"] == "a"


def test_combined_ten_eleven_art_volume_covers_both_grade_cells() -> None:
    report = coverage.evaluate(
        coverage.load_denominator(DENOMINATOR),
        _readiness(("3090-mystectvo-10-11-klas-nazarenko", "ready")),
    )
    cells = {
        item["cell_id"]: item
        for item in report["cells"]
        if item["cell_id"] in {"g10.mystetstvo", "g11.mystetstvo"}
    }
    assert {item["coverage_unit_id"] for item in cells.values()} == {"g10-11.mystetstvo_combined"}
    assert {item["status"] for item in cells.values()} == {"covered"}
    assert all(
        match["source"] == "3090-mystectvo-10-11-klas-nazarenko"
        for item in cells.values()
        for match in item["readiness_matches"]
    )


def test_combined_grade_two_language_reading_volume_covers_both_cells() -> None:
    report = coverage.evaluate(
        coverage.load_denominator(DENOMINATOR),
        _readiness(("3037-ukrmova-bolshakova-2-klas", "ready")),
    )
    cells = {
        item["cell_id"]: item
        for item in report["cells"]
        if item["cell_id"] in {"g02.ukrmova", "g02.chytannia"}
    }
    assert {item["coverage_unit_id"] for item in cells.values()} == {
        "g02.ukrmova_chytannia_combined"
    }
    assert {item["status"] for item in cells.values()} == {"covered"}


def test_no_textbook_applicability_is_not_an_automatic_pdf_gap() -> None:
    report = coverage.evaluate(coverage.load_denominator(DENOMINATOR), _readiness())
    physical_education = next(item for item in report["cells"] if item["cell_id"] == "g01.fizychna_kultura")
    assert physical_education["status"] == "unresolved"
    assert physical_education["status"] not in {"acquisition_missing", "extraction_missing"}

    not_required = _cell(
        "g01.no_book",
        requirement_class="no_textbook_required_or_unresolved",
        applicability="not_required",
    )
    fixture_report = coverage.evaluate(_denominator(not_required), _readiness())
    assert fixture_report["cells"][0]["status"] == "not_required"


def test_suspect_extraction_is_degraded() -> None:
    cell = _cell("g07.suspect", source_ids=["suspect-source"])
    report = coverage.evaluate(
        _denominator(cell),
        _readiness(("suspect-source", "suspect_extraction")),
    )
    assert report["cells"][0]["status"] == "degraded"


def test_current_cell_does_not_accept_legacy_inventory_source() -> None:
    cell = _cell(
        "g09.current_language",
        grade=9,
        source_ids=["current-2026"],
        evidence_state="legacy_only",
        legacy_ids=["legacy-2020"],
    )
    report = coverage.evaluate(
        _denominator(cell),
        _readiness(("legacy-2020", "ready"), selected_count=1),
    )
    result = report["cells"][0]
    assert result["status"] == "acquisition_missing"
    assert result["readiness_matches"] == []
    assert result["legacy_inventory_source_ids"] == ["legacy-2020"]


def test_pdf_without_chunks_is_extraction_missing() -> None:
    cell = _cell("g06.pdf_only", source_ids=["pdf-only"])
    report = coverage.evaluate(
        _denominator(cell),
        _readiness(("pdf-only", "pdf_without_chunks")),
    )
    assert report["cells"][0]["status"] == "extraction_missing"


def test_partial_page_quarantine_is_extraction_missing() -> None:
    cell = _cell("g06.partial", source_ids=["partial-source"])
    report = coverage.evaluate(
        _denominator(cell),
        _readiness(("partial-source", "partial_db_ingest")),
    )
    assert report["cells"][0]["status"] == "extraction_missing"


def test_all_source_groups_require_every_curricular_component() -> None:
    cell = _cell("g10.history", source_ids=["history-ua"])
    cell["coverage"].update(
        source_ids=[],
        source_groups=[["history-ua"], ["history-world"]],
        source_match_mode="all",
    )
    report = coverage.evaluate(
        _denominator(cell),
        _readiness(("history-ua", "ready")),
    )
    assert report["cells"][0]["status"] == "acquisition_missing"


def test_report_is_deterministic() -> None:
    denominator = coverage.load_denominator(DENOMINATOR)
    readiness = _readiness(("3090-mystectvo-10-11-klas-nazarenko", "ready"))
    first = coverage.evaluate(denominator, readiness)
    second = coverage.evaluate(denominator, readiness)
    assert coverage.canonical_json(first) == coverage.canonical_json(second)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda document: document["cells"][0].update(grade="1-4"), "explicit integer"),
        (lambda document: document["cells"][0].update(requirement_class="made_up"), "unknown requirement_class"),
        (
            lambda document: document["cells"].append(copy.deepcopy(document["cells"][0])),
            "duplicate cell_id",
        ),
    ],
)
def test_schema_failures_are_rejected(mutation, message: str) -> None:
    document = _denominator(_cell("g01.fixture"))
    mutation(document)
    with pytest.raises(coverage.CoverageError, match=message):
        coverage.evaluate(document, _readiness())
