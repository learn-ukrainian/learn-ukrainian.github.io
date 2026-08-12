"""Tests for source-date-aware historical chronology v2."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_historical_document_chronology as chronology_v1
from scripts.projects.open_model_data import phase3_historical_document_chronology_source_dates as source_dates
from scripts.projects.open_model_data import phase3_historical_materialization as materialization
from scripts.projects.open_model_data import phase3_historical_periodization as periodization


def _v1_record(*, document_identity: str, collection_id: str = materialization.UD_COLLECTION_ID) -> dict:
    if collection_id == materialization.UD_COLLECTION_ID:
        source_file, source_file_sha256 = next(iter(materialization.UD_EXPECTED_SHA256.items()))
        locator = {
            "dataset_id": collection_id,
            "commit_sha": materialization.UD_COMMIT,
            "source_file": source_file,
            "newdoc_id": document_identity,
        }
        evidence = {
            "raw_date": None,
            "source_file_sha256": source_file_sha256,
            "metadata_row_sha256": "2" * 64,
        }
    else:
        locator = {
            "dataset_id": collection_id,
            "doi": materialization.PLUG2_DOI,
            "metadata_file": "fixture.psv",
            "member_path": document_identity,
        }
        evidence = {
            "raw_date": "1816",
            "source_file_sha256": materialization.PLUG2_METADATA_SHA256,
            "metadata_row_sha256": "4" * 64,
        }
    return {
        "collection_id": collection_id,
        "document_identity": document_identity,
        "locator": locator,
        "date_evidence": evidence,
    }


def _metadata(
    *,
    document_identity: str = "fixture",
    created: str | None = None,
    date: str | None = "1413",
) -> source_dates.UdDocumentMetadata:
    source_file, source_file_sha256 = next(iter(materialization.UD_EXPECTED_SHA256.items()))
    comment_lines = {"newdoc": 1, "language": 2, "title": 3}
    if created is not None:
        comment_lines["created"] = 4
    if date is not None:
        comment_lines["date"] = 5
    return source_dates.UdDocumentMetadata(
        document_identity=document_identity,
        source_file=source_file,
        source_file_sha256=source_file_sha256,
        language="orv-uk",
        title="fixture",
        created=created,
        date=date,
        comment_lines=comment_lines,
        sentence_count=2,
    )


def _record(
    *,
    document_identity: str = "fixture",
    created: str | None = None,
    date: str | None = "1413",
) -> dict:
    return source_dates.build_record(
        v1_record=_v1_record(document_identity=document_identity),
        freeze=periodization.load_freeze(),
        ud_metadata=_metadata(document_identity=document_identity, created=created, date=date),
        catalogue_sha256=source_dates.EXPECTED_RATUSHNA_CATALOGUE_SHA256,
        pdf_sha256=source_dates.EXPECTED_RATUSHNA_PDF_SHA256,
    )


def _reseal(record: dict) -> dict:
    record["record_sha256"] = source_dates._body_sha256(record, "record_sha256")
    return record


def test_contracts_are_strict_and_parent_runtime_binding_is_current():
    for path in (source_dates.RECORD_SCHEMA_PATH, source_dates.RECEIPT_SCHEMA_PATH):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False

    assert source_dates.file_sha256(Path(chronology_v1.__file__)) == (
        source_dates.EXPECTED_CHRONOLOGY_V1_IMPLEMENTATION_SHA256
    )


@pytest.mark.parametrize(
    ("raw_date", "expected"),
    [
        ("1413", (1413, 1413, "exact_year")),
        ("1580-1600", (1580, 1600, "bounded_interval")),
    ],
)
def test_source_date_parser_preserves_exact_years_and_intervals(raw_date, expected):
    assert source_dates.parse_source_date(raw_date) == expected


@pytest.mark.parametrize("raw_date", ["", "ca. 1413", "1413–1473", "1413-1413", "1600-1580", "0999"])
def test_source_date_parser_rejects_unknown_or_invalid_syntax(raw_date):
    with pytest.raises(source_dates.HistoricalSourceDateError):
        source_dates.parse_source_date(raw_date)


def test_exact_ud_date_comment_supersedes_v1_unknown_without_semantic_gold():
    record = _record()

    assert record["date_evidence"]["selected_field"] == "date"
    assert record["date_evidence"]["source_comment_line"] == 5
    assert record["projection"]["status"] == "exact_date_projected"
    assert record["projection"]["chronological_start_year"] == 1413
    assert record["projection"]["chronological_end_year"] == 1413
    assert [item["framework_id"] for item in record["projection"]["framework_projections"]] == list(
        source_dates.EXPECTED_FRAMEWORK_IDS
    )
    assert record["safeguards"]["linguistic_stage_gold"] is False
    assert record["safeguards"]["modern_correction_eligible"] is False


def test_bounded_interval_is_preserved_and_stable_across_all_frameworks():
    record = _record(date="1580-1600")

    assert record["projection"]["status"] == "bounded_interval_projected"
    assert record["projection"]["date_precision"] == "bounded_interval"
    assert record["projection"]["chronological_start_year"] == 1580
    assert record["projection"]["chronological_end_year"] == 1600
    assert {item["interval_stability"] for item in record["projection"]["framework_projections"]} == {
        "stable_across_interval"
    }


def test_boundary_sensitive_interval_does_not_collapse_candidate_stages():
    projections = source_dates._framework_projections(1386, 1414, periodization.load_freeze())

    assert any(item["interval_stability"] == "boundary_sensitive_interval" for item in projections)
    for item in projections:
        if item["interval_stability"] == "boundary_sensitive_interval":
            assert item["matches"] == []
            assert len(item["candidate_stage_ids"]) >= 2


def test_conflicting_created_and_date_fields_fail_closed():
    with pytest.raises(source_dates.HistoricalSourceDateError, match="conflicting UD source date fields"):
        _record(created="1413", date="1436")


def test_ratushna_record_requires_official_edition_binding_but_uses_source_comment_date():
    record = _record(document_identity="RatushnaKniga_1986__ratush02", date="1653")

    assert record["date_evidence"]["selected_field"] == "date"
    assert record["date_evidence"]["corroborating_edition"]["scope"] == (
        "edition_level_corroboration_not_date_inference"
    )
    assert record["date_evidence"]["raw_date"] == "1653"


def test_ratushna_agreeing_created_and_date_fields_prefer_date_comment():
    record = _record(
        document_identity="RatushnaKniga_1986__ratush02",
        created="1653",
        date="1653",
    )

    assert record["date_evidence"]["selected_field"] == "date"
    assert record["date_evidence"]["source_comment_line"] == 5
    assert record["date_evidence"]["source_field_values"]["created"] == "1653"
    assert record["date_evidence"]["source_field_values"]["date"] == "1653"


def test_ratushna_created_without_date_fails_closed():
    with pytest.raises(
        source_dates.HistoricalSourceDateError, match="Ratushna date must come from source date comment"
    ):
        _record(
            document_identity="RatushnaKniga_1986__ratush02",
            created="1653",
            date=None,
        )


def test_validator_rejects_date_projection_tamper_after_reseal():
    record = copy.deepcopy(_record(date="1580-1600"))
    record["projection"]["chronological_end_year"] = 1599

    with pytest.raises(source_dates.HistoricalSourceDateError, match="end year drift"):
        source_dates.validate_record(_reseal(record), freeze=periodization.load_freeze())


def test_validator_rejects_canonical_framework_selection_after_reseal():
    record = copy.deepcopy(_record())
    record["projection"]["canonical_framework_id"] = "university_five_stage_synthesis"

    with pytest.raises(source_dates.HistoricalSourceDateError, match="schema violation"):
        source_dates.validate_record(_reseal(record), freeze=periodization.load_freeze())


def test_validator_rejects_collection_specific_evidence_tamper_after_reseal():
    record = copy.deepcopy(_record())
    record["date_evidence"]["authority"] = "source_metadata_row"

    with pytest.raises(source_dates.HistoricalSourceDateError, match="UD date authority drift"):
        source_dates.validate_record(_reseal(record), freeze=periodization.load_freeze())


def test_validator_rejects_record_identity_tamper_after_reseal():
    record = copy.deepcopy(_record())
    record["record_id"] = "chronology-v2:tampered"

    with pytest.raises(source_dates.HistoricalSourceDateError, match="record identity drift"):
        source_dates.validate_record(_reseal(record), freeze=periodization.load_freeze())


def _conllu(document_marker: str, *, date_lines: list[str]) -> str:
    return "\n".join(
        [
            f"{document_marker}fixture",
            "# lang = orv-uk",
            "# title = Fixture",
            *date_lines,
            "# sent_id = fixture-1",
            "# text = слово",
            "1\tслово\tслово\tNOUN\t_\t_\t0\troot\t_\t_",
            "",
        ]
    )


def test_raw_ud_metadata_parser_supports_all_document_marker_spellings_and_lines(tmp_path, monkeypatch):
    ud_dir = tmp_path / "ud"
    ud_dir.mkdir()
    fixtures = {
        "dev.conllu": _conllu("# newdoc = ", date_lines=["# date = 1413"]),
        "test.conllu": _conllu("# newdoc_id = ", date_lines=["# date = 1413"]),
        "train.conllu": _conllu("# newdoc id = ", date_lines=["# date = 1413"]),
    }
    expected_hashes = {}
    for index, (filename, text) in enumerate(fixtures.items()):
        unique = text.replace("fixture", f"fixture-{index}")
        path = ud_dir / filename
        path.write_text(unique, encoding="utf-8")
        expected_hashes[filename] = source_dates.file_sha256(path)
    monkeypatch.setattr(materialization, "UD_EXPECTED_SHA256", expected_hashes)

    records = source_dates.parse_ud_document_metadata(ud_dir)

    assert sorted(records) == ["fixture-0", "fixture-1", "fixture-2"]
    assert {item.date for item in records.values()} == {"1413"}
    assert {item.comment_lines["date"] for item in records.values()} == {4}
    assert {item.sentence_count for item in records.values()} == {1}


def test_raw_ud_metadata_parser_rejects_duplicate_date_field(tmp_path, monkeypatch):
    ud_dir = tmp_path / "ud"
    ud_dir.mkdir()
    path = ud_dir / "fixture.conllu"
    path.write_text(
        _conllu("# newdoc = ", date_lines=["# date = 1413", "# date = 1436"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(materialization, "UD_EXPECTED_SHA256", {path.name: source_dates.file_sha256(path)})

    with pytest.raises(source_dates.HistoricalSourceDateError, match="duplicate UD date"):
        source_dates.parse_ud_document_metadata(ud_dir)


def _plug2_record() -> dict:
    return source_dates.build_record(
        v1_record=_v1_record(
            document_identity="a.txt",
            collection_id=materialization.PLUG2_COLLECTION_ID,
        ),
        freeze=periodization.load_freeze(),
        ud_metadata=None,
        catalogue_sha256=source_dates.EXPECTED_RATUSHNA_CATALOGUE_SHA256,
        pdf_sha256=source_dates.EXPECTED_RATUSHNA_PDF_SHA256,
    )


def _patch_small_denominator(monkeypatch):
    monkeypatch.setattr(
        source_dates,
        "EXPECTED_UD_DATE_DENOMINATOR",
        {
            "eligible_documents": 2,
            "exact_year_documents": 1,
            "bounded_interval_documents": 1,
            "undated_documents": 0,
        },
    )
    monkeypatch.setattr(
        source_dates,
        "EXPECTED_PLUG2_DATE_DENOMINATOR",
        {
            "eligible_documents": 1,
            "exact_year_documents": 1,
            "bounded_interval_documents": 0,
            "undated_documents": 0,
        },
    )
    monkeypatch.setattr(source_dates, "EXPECTED_TOTAL_DOCUMENTS", 3)
    monkeypatch.setattr(source_dates, "EXPECTED_TOTAL_EXACT_YEAR", 2)
    monkeypatch.setattr(source_dates, "EXPECTED_TOTAL_BOUNDED_INTERVAL", 1)


def test_receipt_and_private_bundle_are_rederived_and_immutable(tmp_path, monkeypatch):
    _patch_small_denominator(monkeypatch)
    records = sorted(
        [_record(), _record(document_identity="range", date="1580-1600"), _plug2_record()],
        key=lambda item: item["record_id"],
    )
    v1_receipt = {
        "receipt_sha256": source_dates.EXPECTED_V1_RECEIPT_SHA256,
        "output": {"sha256": source_dates.EXPECTED_V1_OUTPUT_SHA256},
    }
    monkeypatch.setattr(
        source_dates,
        "derive_records",
        lambda **_kwargs: (records, periodization.load_freeze(), v1_receipt),
    )
    output_dir = tmp_path / "private-output"

    receipt = source_dates.materialize(
        output_dir=output_dir,
        ud_dir=tmp_path / "unused-ud",
        plug2_metadata=tmp_path / "unused.psv",
        full_receipt_path=tmp_path / "unused-full.json",
        v1_chronology_dir=tmp_path / "unused-v1",
        ratushna_pdf=tmp_path / "unused.pdf",
        ratushna_catalogue=tmp_path / "unused.html",
    )

    assert receipt["denominators"]["total_exact_year"] == 2
    assert receipt["denominators"]["total_bounded_interval"] == 1
    assert receipt["coverage"]["undated_documents"] == 0
    assert receipt["phase_boundaries"]["phase4_blocked"] is True
    assert (
        source_dates.validate_bundle(
            output_dir=output_dir,
            ud_dir=tmp_path / "unused-ud",
            plug2_metadata=tmp_path / "unused.psv",
            full_receipt_path=tmp_path / "unused-full.json",
            v1_chronology_dir=tmp_path / "unused-v1",
            ratushna_pdf=tmp_path / "unused.pdf",
            ratushna_catalogue=tmp_path / "unused.html",
        )
        == receipt
    )
    with pytest.raises(source_dates.HistoricalSourceDateError, match="already exists"):
        source_dates.materialize(
            output_dir=output_dir,
            ud_dir=tmp_path / "unused-ud",
            plug2_metadata=tmp_path / "unused.psv",
            full_receipt_path=tmp_path / "unused-full.json",
            v1_chronology_dir=tmp_path / "unused-v1",
            ratushna_pdf=tmp_path / "unused.pdf",
            ratushna_catalogue=tmp_path / "unused.html",
        )


def test_private_output_guard_rejects_git_checkout_before_reading_inputs(tmp_path):
    output_dir = source_dates.ROOT / ".agent" / "chronology-v2-test-output-never-created"
    assert not output_dir.exists()

    with pytest.raises(source_dates.HistoricalSourceDateError, match="cannot be inside Git"):
        source_dates.materialize(
            output_dir=output_dir,
            ud_dir=tmp_path / "unused-ud",
            plug2_metadata=tmp_path / "unused.psv",
            full_receipt_path=tmp_path / "unused-full.json",
            v1_chronology_dir=tmp_path / "unused-v1",
            ratushna_pdf=tmp_path / "unused.pdf",
            ratushna_catalogue=tmp_path / "unused.html",
        )


def test_cli_reports_structured_blocked_status(tmp_path, monkeypatch, capsys):
    def fail_materialize(**_kwargs):
        raise chronology_v1.HistoricalDocumentChronologyError("v1 provenance drift")

    monkeypatch.setattr(source_dates, "materialize", fail_materialize)
    exit_code = source_dates.main(
        [
            "--ud-dir",
            str(tmp_path / "ud"),
            "--plug2-metadata",
            str(tmp_path / "metadata.psv"),
            "--full-receipt",
            str(tmp_path / "full.json"),
            "--v1-chronology-dir",
            str(tmp_path / "v1"),
            "--ratushna-pdf",
            str(tmp_path / "edition.pdf"),
            "--ratushna-catalogue",
            str(tmp_path / "catalogue.html"),
            "--output-dir",
            str(tmp_path / "output"),
        ]
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out) == {
        "status": "blocked",
        "error": "v1 provenance drift",
    }
