"""Tests for source-derived historical document chronology projection."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_historical_document_chronology as chronology
from scripts.projects.open_model_data import phase3_historical_materialization as materialization
from scripts.projects.open_model_data import phase3_historical_periodization as periodization


def _record(raw_date: str | None = "1413") -> dict:
    return chronology.build_record(
        collection_id=materialization.UD_COLLECTION_ID,
        document_identity="zudechiv_1413",
        locator={
            "dataset_id": materialization.UD_COLLECTION_ID,
            "commit_sha": materialization.UD_COMMIT,
            "source_file": "fixture.conllu",
            "newdoc_id": "zudechiv_1413",
        },
        date_field="created",
        raw_date=raw_date,
        source_file_sha256="1" * 64,
        metadata_row_sha256="2" * 64,
        authority="source_document_comment",
        freeze=periodization.load_freeze(),
    )


def _reseal_record(record: dict) -> dict:
    record["record_sha256"] = chronology._body_sha256(record, "record_sha256")
    return record


def test_tracked_contracts_are_strict_and_runtime_bindings_are_current():
    for path in (chronology.RECORD_SCHEMA_PATH, chronology.RECEIPT_SCHEMA_PATH):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False

    assert chronology.file_sha256(Path(periodization.__file__)) == (
        chronology.EXPECTED_PERIODIZATION_IMPLEMENTATION_SHA256
    )
    assert chronology.file_sha256(Path(materialization.__file__)) == (
        chronology.EXPECTED_MATERIALIZATION_IMPLEMENTATION_SHA256
    )
    assert chronology.file_sha256(chronology.PERIODIZATION_FREEZE_PATH) == (
        chronology.EXPECTED_PERIODIZATION_FREEZE_SHA256
    )


def test_exact_year_projects_every_attributed_framework_without_semantic_gold():
    record = _record()

    assert record["projection"]["role"] == "chronological_context_only"
    assert record["projection"]["chronological_year"] == 1413
    assert record["projection"]["canonical_framework_id"] is None
    assert [item["framework_id"] for item in record["projection"]["framework_matches"]] == list(
        chronology.EXPECTED_FRAMEWORK_IDS
    )
    assert record["safeguards"]["linguistic_stage_gold"] is False
    assert record["safeguards"]["semantic_label_created"] is False
    assert record["safeguards"]["modern_correction_eligible"] is False

    nimchuk = record["projection"]["framework_matches"][2]
    assert nimchuk["matches"] == [
        {
            "stage_id": "serednoukrainska_abo_serednoukrainoruska",
            "match_status": "possible_boundary_overlap",
        },
        {"stage_id": "rannia_serednoukrainska", "match_status": "possible_boundary_overlap"},
    ]


@pytest.mark.parametrize("raw_date", [None, "", "ca. 1413", "1413–1473", "1413-01-01"])
def test_non_exact_date_remains_unresolved_without_title_or_range_inference(raw_date):
    record = _record(raw_date)

    assert record["projection"] == {
        "role": "chronological_context_only",
        "status": "unresolved_no_exact_document_date",
        "chronological_year": None,
        "date_precision": "unknown",
        "canonical_framework_id": None,
        "framework_matches": [],
    }


def test_validator_rejects_forged_downgrade_even_when_record_is_resealed():
    record = copy.deepcopy(_record())
    record["projection"].update(
        {
            "status": "unresolved_no_exact_document_date",
            "chronological_year": None,
            "date_precision": "unknown",
            "framework_matches": [],
        }
    )

    with pytest.raises(chronology.HistoricalDocumentChronologyError, match="exact date was not projected"):
        chronology.validate_record(_reseal_record(record), freeze=periodization.load_freeze())


def test_validator_rejects_framework_collapse_even_when_record_is_resealed():
    record = copy.deepcopy(_record())
    record["projection"]["canonical_framework_id"] = "university_five_stage_synthesis"

    with pytest.raises(chronology.HistoricalDocumentChronologyError, match="schema violation"):
        chronology.validate_record(_reseal_record(record), freeze=periodization.load_freeze())


def test_schema_rejects_exact_status_without_all_three_frameworks():
    record = copy.deepcopy(_record())
    record["projection"]["framework_matches"] = []

    with pytest.raises(chronology.HistoricalDocumentChronologyError, match="schema violation"):
        chronology.validate_record(_reseal_record(record), freeze=periodization.load_freeze())


def _conllu(*, document_id: str, language: str, created: str | None, sent_id: str) -> str:
    lines = [f"# newdoc id = {document_id}", f"# lang = {language}"]
    if created is not None:
        lines.append(f"# created = {created}")
    lines.extend(
        [
            f"# title = {document_id}",
            f"# sent_id = {sent_id}",
            "# text = слово",
            "1\tслово\tслово\tNOUN\t_\t_\t0\troot\t_\t_",
            "",
        ]
    )
    return "\n".join(lines)


def _fixture_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    ud_dir = tmp_path / "ud"
    ud_dir.mkdir()
    files = {
        "orv_ruthenian-ud-dev.conllu": _conllu(
            document_id="fixture_exact", language="orv-uk", created="1413", sent_id="exact-1"
        ),
        "orv_ruthenian-ud-test.conllu": _conllu(
            document_id="fixture_unknown", language="orv-uk", created=None, sent_id="unknown-1"
        ),
        "orv_ruthenian-ud-train.conllu": _conllu(
            document_id="excluded", language="orv-be", created="1413", sent_id="excluded-1"
        ),
    }
    ud_hashes = {}
    for filename, text in files.items():
        path = ud_dir / filename
        path.write_text(text, encoding="utf-8")
        ud_hashes[filename] = chronology.file_sha256(path)

    plug2_metadata = tmp_path / "PluG2_metadata.psv"
    plug2_metadata.write_text(
        '"path"|"doc.date"|"doc.original"\n"a.txt"|"1816"|"UK"\n"b.txt"|"1954"|"UK"\n',
        encoding="utf-8",
    )
    plug2_hash = chronology.file_sha256(plug2_metadata)

    ud_denominator = {"documents": 2, "sentences": 2, "token_rows": 2}
    plug2_denominator = {
        "documents": 2,
        "token_sum": 2,
        "uk_documents": 2,
        "non_uk_or_unknown_documents": 0,
    }
    monkeypatch.setattr(materialization, "UD_EXPECTED_SHA256", ud_hashes)
    monkeypatch.setattr(materialization, "UD_EXPECTED_DENOMINATOR", ud_denominator)
    monkeypatch.setattr(materialization, "PLUG2_METADATA_SHA256", plug2_hash)
    monkeypatch.setattr(materialization, "PLUG2_EXPECTED_DENOMINATOR", plug2_denominator)
    monkeypatch.setattr(
        chronology,
        "EXPECTED_UD_DATE_DENOMINATOR",
        {
            "eligible_documents": 2,
            "exact_date_documents": 1,
            "unresolved_date_documents": 1,
            "min_exact_year": 1413,
            "max_exact_year": 1413,
        },
    )
    monkeypatch.setattr(
        chronology,
        "EXPECTED_PLUG2_DATE_DENOMINATOR",
        {
            "eligible_documents": 2,
            "exact_date_documents": 2,
            "unresolved_date_documents": 0,
            "min_exact_year": 1816,
            "max_exact_year": 1954,
        },
    )

    full_receipt = tmp_path / "historical-full-materialization-receipt-v1.json"
    full_receipt_body = {
        "receipt_sha256": "3" * 64,
        "coverage": {"full_materialization_complete": True},
        "phase_boundaries": {"phase4_blocked": True},
        "denominators": {
            "ud_explicit_orv_uk": ud_denominator,
            "plug2": plug2_denominator,
        },
        "inputs": {
            "ud_file_sha256": ud_hashes,
            "plug2_metadata_sha256": plug2_hash,
        },
    }
    full_receipt.write_text(json.dumps(full_receipt_body), encoding="utf-8")
    monkeypatch.setattr(chronology, "EXPECTED_FULL_RECEIPT_SHA256", "3" * 64)
    monkeypatch.setattr(
        chronology,
        "EXPECTED_FULL_RECEIPT_FILE_SHA256",
        chronology.file_sha256(full_receipt),
    )
    return ud_dir, plug2_metadata, full_receipt


def test_full_receipt_file_hash_guard_rejects_drift(tmp_path, monkeypatch):
    ud_dir, plug2_metadata, full_receipt = _fixture_inputs(tmp_path, monkeypatch)
    full_receipt.write_text(full_receipt.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(chronology.HistoricalDocumentChronologyError, match="receipt file drift"):
        chronology.derive_records(
            ud_dir=ud_dir,
            plug2_metadata=plug2_metadata,
            full_receipt_path=full_receipt,
        )


@pytest.mark.parametrize(
    ("field_path", "value", "message"),
    [
        (("receipt_sha256",), "4" * 64, "full receipt seal drift"),
        (("coverage", "full_materialization_complete"), False, "full corpus incomplete"),
        (("phase_boundaries", "phase4_blocked"), False, "Phase 4 boundary drift"),
        (("denominators", "ud_explicit_orv_uk", "documents"), 999, "UD denominator drift"),
        (("inputs", "plug2_metadata_sha256"), "5" * 64, "PluG2 metadata binding drift"),
    ],
)
def test_full_receipt_semantic_guards_fail_closed(tmp_path, monkeypatch, field_path, value, message):
    ud_dir, plug2_metadata, full_receipt = _fixture_inputs(tmp_path, monkeypatch)
    receipt = json.loads(full_receipt.read_text(encoding="utf-8"))
    target = receipt
    for key in field_path[:-1]:
        target = target[key]
    target[field_path[-1]] = value
    full_receipt.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(
        chronology,
        "EXPECTED_FULL_RECEIPT_FILE_SHA256",
        chronology.file_sha256(full_receipt),
    )

    with pytest.raises(chronology.HistoricalDocumentChronologyError, match=message):
        chronology.derive_records(
            ud_dir=ud_dir,
            plug2_metadata=plug2_metadata,
            full_receipt_path=full_receipt,
        )


def test_private_output_guard_rejects_git_checkout_before_writing(tmp_path):
    output_dir = chronology.ROOT / ".agent" / "chronology-test-output-never-created"
    assert not output_dir.exists()

    with pytest.raises(chronology.HistoricalDocumentChronologyError, match="cannot be inside Git"):
        chronology.materialize(
            output_dir=output_dir,
            ud_dir=tmp_path / "unused-ud",
            plug2_metadata=tmp_path / "unused-metadata",
            full_receipt_path=tmp_path / "unused-receipt",
        )

    assert not output_dir.exists()


def test_date_denominator_guard_rejects_source_derived_mismatch(tmp_path, monkeypatch):
    ud_dir, plug2_metadata, full_receipt_path = _fixture_inputs(tmp_path, monkeypatch)
    records, _freeze, full_receipt = chronology.derive_records(
        ud_dir=ud_dir,
        plug2_metadata=plug2_metadata,
        full_receipt_path=full_receipt_path,
    )
    expected = dict(chronology.EXPECTED_UD_DATE_DENOMINATOR)
    expected["exact_date_documents"] += 1
    monkeypatch.setattr(chronology, "EXPECTED_UD_DATE_DENOMINATOR", expected)

    with pytest.raises(chronology.HistoricalDocumentChronologyError, match="UD date denominator drift"):
        chronology._build_receipt(
            records=records,
            full_receipt=full_receipt,
            output_bytes=1,
            output_sha256="6" * 64,
        )


def test_cli_converts_upstream_parse_failure_to_blocked_status(tmp_path, monkeypatch, capsys):
    def fail_derive(**_kwargs):
        raise materialization.HistoricalMaterializationError("malformed upstream metadata")

    monkeypatch.setattr(chronology, "derive_records", fail_derive)
    exit_code = chronology.main(
        [
            "--ud-dir",
            str(tmp_path / "ud"),
            "--plug2-metadata",
            str(tmp_path / "metadata.psv"),
            "--full-receipt",
            str(tmp_path / "receipt.json"),
            "--output-dir",
            str(tmp_path / "output"),
        ]
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out) == {
        "status": "blocked",
        "error": "malformed upstream metadata",
    }


def test_private_bundle_is_rederived_end_to_end_and_refuses_overwrite(tmp_path, monkeypatch):
    ud_dir, plug2_metadata, full_receipt = _fixture_inputs(tmp_path, monkeypatch)
    output_dir = tmp_path / "private-output"

    receipt = chronology.materialize(
        output_dir=output_dir,
        ud_dir=ud_dir,
        plug2_metadata=plug2_metadata,
        full_receipt_path=full_receipt,
    )

    assert receipt["output"]["records"] == 4
    assert receipt["denominators"]["ud"]["unresolved_date_documents"] == 1
    assert receipt["denominators"]["plug2"]["exact_date_documents"] == 2
    assert receipt["coverage"]["qualified_historical_semantic_review_complete"] is False
    assert receipt["phase_boundaries"]["phase4_blocked"] is True
    assert (
        chronology.validate_bundle(
            output_dir=output_dir,
            ud_dir=ud_dir,
            plug2_metadata=plug2_metadata,
            full_receipt_path=full_receipt,
        )
        == receipt
    )

    with pytest.raises(chronology.HistoricalDocumentChronologyError, match="already exists"):
        chronology.materialize(
            output_dir=output_dir,
            ud_dir=ud_dir,
            plug2_metadata=plug2_metadata,
            full_receipt_path=full_receipt,
        )


def test_replay_rejects_resealed_record_not_derived_from_source(tmp_path, monkeypatch):
    ud_dir, plug2_metadata, full_receipt = _fixture_inputs(tmp_path, monkeypatch)
    output_dir = tmp_path / "private-output"
    chronology.materialize(
        output_dir=output_dir,
        ud_dir=ud_dir,
        plug2_metadata=plug2_metadata,
        full_receipt_path=full_receipt,
    )
    output_path = output_dir / chronology.OUTPUT_FILENAME
    records = chronology._read_gzip(output_path)
    records[0]["document_identity"] += "-forged"
    _reseal_record(records[0])
    chronology._write_gzip(output_path, records)

    with pytest.raises(chronology.HistoricalDocumentChronologyError, match="source re-derivation drift"):
        chronology.validate_bundle(
            output_dir=output_dir,
            ud_dir=ud_dir,
            plug2_metadata=plug2_metadata,
            full_receipt_path=full_receipt,
        )
