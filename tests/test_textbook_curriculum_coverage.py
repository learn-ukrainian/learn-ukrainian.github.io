from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import textbook_curriculum_coverage as coverage

ROOT = Path(__file__).resolve().parents[1]
DENOMINATOR = ROOT / "data" / "textbook_curriculum_denominator.yaml"


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
        "required_common": 68,
        "required_one_of": 59,
        "profile_or_track": 26,
        "optional_elective": 12,
        "no_textbook_required_or_unresolved": 11,
    }
    assert report["selection"]["selected_count"] == 116
    assert report["selection"]["is_official_curriculum_denominator"] is False
    assert report["input_hashes"] == {
        "denominator_sha256": hashlib.sha256(DENOMINATOR.read_bytes()).hexdigest(),
        "readiness_sha256": hashlib.sha256(readiness_path.read_bytes()).hexdigest(),
    }


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
