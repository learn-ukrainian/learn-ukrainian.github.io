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


def test_tracked_spine_starts_with_direct_kyiv_epigraphy_and_keeps_frameworks_attributed():
    value = spine.load_spine()

    assert spine.sha256_file(spine.SPINE_PATH) == spine.EXPECTED_SPINE_SHA256
    assert value["instructional_sequence"][0]["sequence_id"] == "kyiv_medieval_epigraphy"
    assert value["instructional_sequence"][0]["evidence_mode"] == "direct_attestation"
    assert value["instructional_sequence"][-1]["sequence_id"] == "comparative_reconstruction_backlink"
    assert value["framework_policy"]["canonical_framework_id"] is None
    assert value["framework_policy"]["instructional_navigation_scope"] == "coarse_navigation_only_not_semantic_gold"
    assert set(value["framework_policy"]["bound_framework_ids"]) == {
        "university_five_stage_synthesis",
        "shevelov_detailed_six_period",
        "nimchuk_five_stage_with_middle_subperiods",
    }


def test_saint_sophia_and_lavra_are_separate_and_only_one_is_materialized():
    collections = {item["collection_id"]: item for item in spine.load_spine()["collections"]}
    sophia = collections["saint-sophia-inscriptions"]
    lavra = collections["kyiv-pechersk-lavra-graffiti"]

    assert sophia["record_count"] == 4157
    assert sophia["facts"]["retrieval_scope"] == "complete_current_public_api"
    assert sophia["facts"]["stage_labels_assigned"] == 0
    assert lavra["custody_state"] == "not_materialized"
    assert lavra["record_count"] is None
    assert lavra["facts"]["corpus_count_known"] is False
    assert lavra["facts"]["separate_from_saint_sophia"] is True


def test_saint_sophia_provenance_binds_official_download_part_ix_and_ai_disclosure():
    sophia = next(
        item for item in spine.load_spine()["collections"]
        if item["collection_id"] == "saint-sophia-inscriptions"
    )
    provenance = sophia["facts"]["source_provenance"]

    assert provenance["official_bulk_download"] == {
        "api_url": "https://saintsophia.dh.gu.se/api/inscriptions/inscription/?depth=2",
        "download_label": "Download all inscription data",
        "record_count_at_snapshot": 4157,
        "same_public_api_stream": True,
    }
    assert provenance["part_ix"]["bibliography_id"] == 11
    assert provenance["part_ix"]["linked_public_records"] == 306
    assert provenance["gippius_2023"]["portal_bibliography_present"] is False
    assert provenance["ai_assistance"]["human_gold_eligible_without_review"] is False
    assert provenance["license_evidence"]["explicit_data_license_at_pinned_sources"] is None
    assert provenance["license_evidence"]["korniienko_media_assets"] == {
        "asset_count_at_snapshot": 6477,
        "included_in_text_training": False,
        "license_label": "CC BY-NC",
        "license_version_declared": False,
    }
    assert provenance["license_evidence"]["operator_use_decision"] == {
        "binary_media_in_scope": False,
        "decision": "proceed_without_pre_use_permission_wait",
        "decision_date": "2026-08-12",
        "full_publications_in_scope": False,
        "response_policy": "adapt_remove_or_reclassify_affected_material_on_substantiated_rights_notice",
        "scope": "public_structured_text_and_metadata_for_phase3_training_with_attribution_and_field_level_provenance",
    }
    assert sophia["rights"]["status"] == "publicly_downloadable_license_not_declared"
    assert sophia["rights"]["reuse_scope"] == (
        "phase3_textual_dataset_training_and_derived_data_release_with_attribution_"
        "field_provenance_and_takedown_readiness"
    )

    locators = {(item["locator_role"], item["url"]) for item in sophia["locators"]}
    assert (
        "official_bulk_download_implementation",
        "https://github.com/gu-gridh/multimodal-map/blob/574914b6a740b639eb8e90f143664aae9a86cac7/projects/sophia/Footer.vue",
    ) in locators
    assert ("scholarly_reanalysis_doi", "https://doi.org/10.4324/9781003256236-14") in locators


def test_current_materialized_coverage_does_not_fake_old_or_middle_depth():
    collections = {item["collection_id"]: item for item in spine.load_spine()["collections"]}
    sophia = collections["saint-sophia-inscriptions"]["facts"]
    ud = collections["ud-old-east-slavic-ruthenian-05a029e00ccf"]["facts"]
    plug2 = collections["plug2-zenodo-19482961"]["facts"]

    assert sophia["old_date_band"]["interval_wholly_inside"] == 1225
    assert sophia["old_date_band"]["text_bearing_ukrainian_label_wholly_inside"] == 7
    assert sophia["old_date_band"]["semantic_stage_assignment"] == "pending_qualified_review"
    assert ud["exact_years"] == [1413, 1436, 1456, 1473]
    assert ud["undated_documents"] == 78
    assert ud["periodization_assignment_state"] == "unresolved"
    assert plug2["date_min"] == 1816
    assert plug2["date_max"] == 1954
    assert plug2["pre_1800_documents"] == 0


def test_learner_material_is_preserved_but_not_historical_authority():
    learner = spine.load_spine()["authority_policy"]["learner_exposition"]

    assert learner["preserve_for_instructional_evaluation"] is True
    assert learner["historical_authority_eligible"] is False
    assert learner["training_text_eligibility"] == "pending_separate_rights_and_quality_review"


def test_phase_boundaries_remain_fail_closed():
    value = spine.load_spine()

    assert value["gates"] == {
        "evidence_first_spine_defined": True,
        "historical_source_coverage_ready": False,
        "historical_source_freeze_ready": False,
        "phase3_complete": False,
        "phase4_authorized": False,
        "phase4_blocked": True,
        "private_corpus_audit_reproducible": True,
    }
    gap_states = {item["gap_id"]: item["state"] for item in value["gaps"]}
    assert gap_states["saint_sophia_license_expression_missing"] == "accepted_operational_risk"
    assert {
        state for gap_id, state in gap_states.items()
        if gap_id != "saint_sophia_license_expression_missing"
    } == {"open"}


def test_validator_rejects_framework_collapse_even_when_resealed():
    value = copy.deepcopy(_tracked())
    value["framework_policy"]["canonical_framework_id"] = "university_five_stage_synthesis"

    with pytest.raises(spine.HistoricalEvidenceSpineError, match="schema violation"):
        spine.validate_spine(_reseal(value))


def test_validator_rejects_fabricated_lavra_denominator_even_when_resealed():
    value = copy.deepcopy(_tracked())
    lavra = next(item for item in value["collections"] if item["collection_id"] == "kyiv-pechersk-lavra-graffiti")
    lavra["record_count"] = 100
    lavra["facts"]["corpus_count_known"] = True

    with pytest.raises(spine.HistoricalEvidenceSpineError, match="schema violation"):
        spine.validate_spine(_reseal(value))


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


def test_validator_rejects_erased_operator_use_decision_even_when_resealed():
    value = copy.deepcopy(_tracked())
    sophia = next(item for item in value["collections"] if item["collection_id"] == "saint-sophia-inscriptions")
    sophia["facts"]["source_provenance"]["license_evidence"]["operator_use_decision"]["decision"] = (
        "wait_for_pre_use_permission"
    )

    with pytest.raises(spine.HistoricalEvidenceSpineError, match="schema violation"):
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


def test_validator_rejects_ai_assisted_portal_fields_as_unreviewed_human_gold():
    value = copy.deepcopy(_tracked())
    sophia = next(item for item in value["collections"] if item["collection_id"] == "saint-sophia-inscriptions")
    sophia["facts"]["source_provenance"]["ai_assistance"]["human_gold_eligible_without_review"] = True

    with pytest.raises(spine.HistoricalEvidenceSpineError, match="schema violation"):
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


def test_private_audit_uses_supplied_spine_without_reloading_default(monkeypatch, tmp_path):
    checked = spine.validate_spine(_tracked())
    monkeypatch.setattr(spine, "load_spine", lambda *_args, **_kwargs: pytest.fail("default spine reloaded"))
    monkeypatch.setattr(spine, "audit_saint_sophia", lambda *_args, **_kwargs: copy.deepcopy(spine.EXPECTED_SOPHIA_PRIVATE_AUDIT))
    monkeypatch.setattr(
        spine,
        "audit_plug2_metadata",
        lambda *_args, **_kwargs: {
            "all_documents": 56245,
            "uk_documents": 56080,
            "uk_token_sum": 71802066,
            "date_min": 1816,
            "date_max": 1954,
            "pre_1800_documents": 0,
            "exact_dated_documents": 56080,
        },
    )
    monkeypatch.setattr(
        spine,
        "audit_ud",
        lambda *_args, **_kwargs: {
            "documents": 82,
            "sentences": 1311,
            "token_rows": 35081,
            "exact_dated_documents": 4,
            "exact_years": [1413, 1436, 1456, 1473],
            "undated_documents": 78,
            "nonexact_dated_documents": 0,
        },
    )
    monkeypatch.setattr(
        spine,
        "audit_full_materialization_receipt",
        lambda *_args, **_kwargs: {"full_materialization_complete": True},
    )

    result = spine.audit_private_inputs(
        sophia_jsonl=tmp_path / "sophia.jsonl",
        plug2_metadata=tmp_path / "metadata.psv",
        ud_root=tmp_path / "ud",
        full_materialization_receipt=tmp_path / "receipt.json",
        spine_value=checked,
    )

    assert result["full_materialization_receipt"]["full_materialization_complete"] is True
