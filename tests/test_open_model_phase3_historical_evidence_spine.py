"""Hermetic tests for the evidence-first historical Ukrainian coverage spine."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_historical_evidence_spine as spine


def _tracked() -> dict:
    return json.loads(spine.SPINE_PATH.read_text(encoding="utf-8"))


def _reseal(value: dict) -> dict:
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    value["receipt_sha256"] = hashlib.sha256((spine.canonical_json(body) + "\n").encode()).hexdigest()
    return value


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _full_receipt_fixture() -> dict:
    body = {
        "schema_version": "phase3_historical_full_materialization_receipt_v1",
        "text_free": True,
        "coverage": {
            "full_materialization_complete": True,
            "non_eligible_inputs_excluded": True,
            "periodization_assignment_state": "unresolved_pending_qualified_historical_review",
            "plug2_eligible_set_equal": True,
            "ud_eligible_set_equal": True,
        },
        "denominators": {
            "plug2": {
                "documents": 56245,
                "non_uk_or_unknown_documents": 165,
                "token_sum": 74497787,
                "uk_documents": 56080,
            },
            "plug2_candidate_uk_token_sum": 71802066,
            "ud_explicit_orv_uk": {"documents": 82, "sentences": 1311, "token_rows": 35081},
            "ud_other_or_unresolved_sentences": 4054,
        },
        "outputs": {
            "plug2": {
                "bytes": 2075643781,
                "filename": "plug2-uk-full.jsonl.gz",
                "records": 1910748,
                "sha256": "7cf7efd0ff48827f84c503ecb84c578cb540b0d08e6fc5c857bf72ad20f96b94",
            },
            "ud": {
                "bytes": 2150133,
                "filename": "ud-orv-uk-full.jsonl.gz",
                "records": 1311,
                "sha256": "e883abd511121a2d01b3b1bc7559c4672c9dae3d0e0af3a8df1f7a6a05865cb0",
            },
        },
        "safeguards": {
            "historical_forms_protected": True,
            "modern_correction_eligible": False,
            "phase4_authorized": False,
            "provider_calls": False,
            "source_bytes_preserved": True,
        },
    }
    body["receipt_sha256"] = hashlib.sha256(spine.canonical_json(body).encode()).hexdigest()
    return body


def test_validator_rejects_audited_fact_tampering_even_when_resealed():
    value = copy.deepcopy(_tracked())
    sophia = next(item for item in value["collections"] if item["collection_id"] == "saint-sophia-inscriptions")
    sophia["facts"]["language_labels"]["Ukrainian"] += 1
    sophia["facts"]["language_labels"]["unlabelled"] -= 1

    with pytest.raises(spine.HistoricalEvidenceSpineError, match="audited facts drift"):
        spine.validate_spine(_reseal(value))


def test_validator_rejects_rights_overclaim_even_when_resealed():
    value = copy.deepcopy(_tracked())
    sophia = next(item for item in value["collections"] if item["collection_id"] == "saint-sophia-inscriptions")
    sophia["rights"]["status"] = "admitted"
    sophia["rights"]["reuse_scope"] = "public_training_with_attribution"

    with pytest.raises(spine.HistoricalEvidenceSpineError, match="rights posture drift"):
        spine.validate_spine(_reseal(value))


def test_validator_rejects_reblocking_accepted_rights_risk_even_when_resealed():
    value = copy.deepcopy(_tracked())
    license_gap = next(
        item for item in value["gaps"]
        if item["gap_id"] == "saint_sophia_license_expression_missing"
    )
    license_gap["state"] = "open"

    with pytest.raises(spine.HistoricalEvidenceSpineError, match="gap disposition drift"):
        spine.validate_spine(_reseal(value))


def test_validator_rejects_instructional_collection_reshuffle_even_when_resealed():
    value = copy.deepcopy(_tracked())
    old = next(
        item for item in value["instructional_sequence"]
        if item["sequence_id"] == "old_ukrainian_documentary_and_literary"
    )
    old["collection_ids"] = ["plug2-zenodo-19482961"]

    with pytest.raises(spine.HistoricalEvidenceSpineError, match="sequence evidence binding drift"):
        spine.validate_spine(_reseal(value))


def test_validator_rejects_erased_gap_even_when_resealed():
    value = copy.deepcopy(_tracked())
    value["gaps"] = [item for item in value["gaps"] if item["gap_id"] != "lavra_epigraphy_not_materialized"]

    with pytest.raises(spine.HistoricalEvidenceSpineError, match="gap denominator drift"):
        spine.validate_spine(_reseal(value))


def test_validator_rejects_receipt_drift():
    value = copy.deepcopy(_tracked())
    value["gaps"][0]["next_action"] += " drift"

    with pytest.raises(spine.HistoricalEvidenceSpineError, match="seal mismatch"):
        spine.validate_spine(value)


def test_saint_sophia_private_audit_excludes_missing_reversed_and_out_of_bounds_dates(tmp_path):
    source = tmp_path / "sophia.jsonl"
    rows = [
        {
            "disposition": "text_bearing",
            "source_language_label": "Ukrainian",
            "source_writing_system_label": "Cyrillic",
            "min_year": 1100,
            "max_year": 1100,
            "metadata": {
                "source_record": {
                    "bibliography": [{"id": 11, "title": "Part IX", "authors": "Korniienko"}],
                    "korniienko_image": [
                        {"type_of_license": "CC BY-NC", "type_of_image": "Photograph"}
                    ],
                }
            },
        },
        {
            "disposition": "text_bearing",
            "source_language_label": "Church Slavonic",
            "source_writing_system_label": "Cyrillic",
            "min_year": 1450,
            "max_year": 1600,
            "metadata": {
                "source_record": {
                    "bibliography": [
                        {"id": 11, "title": "Part IX", "authors": "Korniienko"},
                        {"id": 99, "title": "Reanalysis", "authors": "Gippius"},
                    ],
                    "korniienko_image": [
                        {"type_of_license": "CC BY-NC", "type_of_image": "Drawing"}
                    ],
                }
            },
        },
        {
            "disposition": "quarantined_metadata",
            "source_language_label": None,
            "source_writing_system_label": None,
            "min_year": 1600,
            "max_year": 1597,
            "metadata": {"source_record": {"bibliography": [], "korniienko_image": []}},
        },
        {
            "disposition": "quarantined_metadata",
            "source_language_label": None,
            "source_writing_system_label": None,
            "min_year": 1025,
            "max_year": 13015,
            "metadata": {"source_record": {"bibliography": [], "korniienko_image": []}},
        },
        {
            "disposition": "non_textual_or_no_text",
            "source_language_label": None,
            "source_writing_system_label": None,
            "min_year": None,
            "max_year": None,
            "metadata": {"source_record": {"bibliography": [], "korniienko_image": []}},
        },
    ]
    _write_jsonl(source, rows)

    result = spine.audit_saint_sophia(source, expected_sha256=spine.sha256_file(source))

    assert result["records"] == 5
    assert result["dates"] == {
        "valid_intervals": 2,
        "exact_year_intervals": 1,
        "century_or_wider_intervals": 1,
        "missing_intervals": 1,
        "invalid_intervals": 2,
    }
    assert result["coarse_date_observations"]["old_1000_1399"]["interval_wholly_inside"] == 1
    assert result["coarse_date_observations"]["middle_1400_1799"]["interval_wholly_inside"] == 1
    assert result["bibliography"] == {
        "distinct_items": 2,
        "gippius_2023_portal_bibliography_matches": 1,
        "part_ix_bibliography_id": 11,
        "part_ix_linked_records": 2,
    }
    assert result["media_assets"] == {
        "asset_count": 2,
        "license_counts": {"CC BY-NC": 2},
        "type_counts": {"Drawing": 1, "Photograph": 1},
    }


def test_plug2_private_audit_uses_original_language_and_exact_dates(tmp_path):
    source = tmp_path / "metadata.psv"
    fieldnames = ["path", "doc.original", "doc.date", "doc.tokenCount"]
    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="|", quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerow({"path": "uk-old.txt", "doc.original": "UK", "doc.date": "1816", "doc.tokenCount": "10"})
        writer.writerow({"path": "uk-new.txt", "doc.original": "UK", "doc.date": "1954", "doc.tokenCount": "20"})
        writer.writerow({"path": "translation.txt", "doc.original": "PL", "doc.date": "1900", "doc.tokenCount": "30"})

    result = spine.audit_plug2_metadata(source, expected_sha256=spine.sha256_file(source))

    assert result == {
        "all_documents": 3,
        "uk_documents": 2,
        "uk_token_sum": 30,
        "date_min": 1816,
        "date_max": 1954,
        "pre_1800_documents": 0,
        "exact_dated_documents": 2,
    }


def test_ud_private_audit_preserves_missing_dates_as_unresolved(tmp_path):
    source = tmp_path / "fixture.conllu"
    source.write_text(
        "# newdoc id = dated\n"
        "# lang = orv-uk\n"
        "# created = 1413\n"
        "# sent_id = dated-1\n"
        "# text = Слово.\n"
        "1\tСлово\tслово\tNOUN\t_\t_\t0\troot\t_\tSpaceAfter=No\n"
        "2\t.\t.\tPUNCT\t_\t_\t1\tpunct\t_\t_\n\n"
        "# newdoc id = undated\n"
        "# lang = orv-uk\n"
        "# sent_id = undated-1\n"
        "# text = Текст.\n"
        "1\tТекст\tтекст\tNOUN\t_\t_\t0\troot\t_\tSpaceAfter=No\n"
        "2\t.\t.\tPUNCT\t_\t_\t1\tpunct\t_\t_\n\n"
        "# newdoc id = other\n"
        "# lang = orv-be\n"
        "# sent_id = other-1\n"
        "# text = Інше.\n"
        "1\tІнше\tінший\tDET\t_\t_\t0\troot\t_\tSpaceAfter=No\n"
        "2\t.\t.\tPUNCT\t_\t_\t1\tpunct\t_\t_\n\n",
        encoding="utf-8",
    )

    result = spine.audit_ud(tmp_path, expected_hashes={source.name: spine.sha256_file(source)})

    assert result == {
        "documents": 2,
        "sentences": 2,
        "token_rows": 4,
        "exact_dated_documents": 1,
        "exact_years": [1413],
        "undated_documents": 1,
        "nonexact_dated_documents": 0,
    }


def test_full_materialization_receipt_is_hash_and_seal_bound(tmp_path):
    path = tmp_path / "full-receipt.json"
    receipt = _full_receipt_fixture()
    path.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
    file_sha256 = spine.sha256_file(path)

    result = spine.audit_full_materialization_receipt(
        path,
        expected_file_sha256=file_sha256,
        expected_receipt_sha256=receipt["receipt_sha256"],
    )

    assert result["full_materialization_complete"] is True
    assert result["file_sha256"] == file_sha256

    receipt["outputs"]["plug2"]["records"] -= 1
    path.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(spine.HistoricalEvidenceSpineError, match="byte drift"):
        spine.audit_full_materialization_receipt(
            path,
            expected_file_sha256=file_sha256,
            expected_receipt_sha256=receipt["receipt_sha256"],
        )
