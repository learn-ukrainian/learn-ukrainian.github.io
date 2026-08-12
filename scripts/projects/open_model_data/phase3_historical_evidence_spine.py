#!/usr/bin/env python3
"""Validate the evidence-first historical Ukrainian coverage spine.

The spine is deliberately not a fourth periodization.  It binds the existing
attributed Ukrainian scholarly frameworks and records what the locally held
corpora can actually prove.  Direct attestations lead the instructional order;
reconstruction and learner exposition remain separately labelled evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_historical_materialization as materialization
from scripts.projects.open_model_data import phase3_historical_periodization as periodization

ROOT = Path(__file__).resolve().parents[3]
SPINE_PATH = ROOT / "data/projects/open_model_data/admission/phase3_historical_evidence_spine_v1.json"
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_historical_evidence_spine_v1.schema.json"
DENOMINATOR_PATH = ROOT / "data/historical_language_corpus_denominator.yaml"
FULL_GATE_PATH = ROOT / "data/projects/open_model_data/admission/phase3_historical_full_materialization_gate_v1.json"

SCHEMA_VERSION = "phase3_historical_evidence_spine_v1"
EXPECTED_SPINE_SHA256 = "61a937f150a4cbecf6b12774ef812d67289705d9523c4e766c95e721b7451076"
EXPECTED_BINDINGS = {
    "historical_denominator_sha256": "4d89bfdb7e935008ad1332426ff9c40dca97efdf72053f35cdb1dad05117e6aa",
    "historical_full_materialization_gate_sha256": "3a4f409be28560dbc6a9c2c5defa043414dc659870be11a03f8e7297e8249e21",
    "historical_full_materialization_receipt_file_sha256": "05322d450a8e90b103fff7521605395250e1da957fbf63e8ecf1df8d3d5f6307",
    "historical_full_materialization_receipt_sha256": "8e3d33b4c5d5a5a4bd3c5da7788460d016e16b9058515b64a6683a725a14c2de",
    "historical_periodization_freeze_sha256": periodization.EXPECTED_FREEZE_SHA256,
    "phase3_reboot_prompt_v3_sha256": "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d",
    "phase3_recovery_prompt_v2_sha256": "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b",
}
EXPECTED_COLLECTIONS = {
    "saint-sophia-inscriptions",
    "kyiv-pechersk-lavra-graffiti",
    materialization.UD_COLLECTION_ID,
    materialization.PLUG2_COLLECTION_ID,
}
EXPECTED_AUTHORITY_ORDER = [
    "direct_attested_source",
    "qualified_edition_or_translation",
    "qualified_ukrainian_linguistic_analysis",
    "comparative_reconstruction",
    "learner_exposition",
]
EXPECTED_INSTRUCTIONAL_ORDER = [
    "kyiv_medieval_epigraphy",
    "old_ukrainian_documentary_and_literary",
    "middle_ukrainian_documentary_and_print",
    "new_and_modern_ukrainian",
    "comparative_reconstruction_backlink",
]
EXPECTED_SOPHIA_PROVENANCE = {
    "ai_assistance": {
        "affected_field_classes": ["english_translation_and_commentary", "romanisation"],
        "affected_record_membership_known": False,
        "disclosed_by_official_documentation": True,
        "human_gold_eligible_without_review": False,
    },
    "foundational_dataset": {
        "edition_title": "Корпус Графіті Софії Київської",
        "publication_year_end": 2020,
        "publication_year_start": 2009,
        "volume_count": 12,
    },
    "gippius_2023": {
        "doi": "10.4324/9781003256236-14",
        "portal_bibliography_present": False,
        "role": "qualified_secondary_reanalysis_candidate",
        "target": "Kyiv graffito No. 108",
    },
    "license_evidence": {
        "official_docs_describe_dataset_as_open": True,
        "official_docs_describe_api_as_open_and_reusable": True,
        "explicit_data_license_at_pinned_sources": None,
        "korniienko_media_assets": {
            "asset_count_at_snapshot": 6477,
            "included_in_text_training": False,
            "license_label": "CC BY-NC",
            "license_version_declared": False,
        },
        "operator_use_decision": {
            "binary_media_in_scope": False,
            "decision": "proceed_without_pre_use_permission_wait",
            "decision_date": "2026-08-12",
            "full_publications_in_scope": False,
            "response_policy": "adapt_remove_or_reclassify_affected_material_on_substantiated_rights_notice",
            "scope": "public_structured_text_and_metadata_for_phase3_training_with_attribution_and_field_level_provenance",
        },
    },
    "official_bulk_download": {
        "api_url": "https://saintsophia.dh.gu.se/api/inscriptions/inscription/?depth=2",
        "download_label": "Download all inscription data",
        "record_count_at_snapshot": 4157,
        "same_public_api_stream": True,
    },
    "part_ix": {
        "bibliography_id": 11,
        "linked_public_records": 306,
        "publication_year": 2019,
        "scope": "північні внутрішня та зовнішня галереї",
    },
    "portal_version": "v1.6",
}
EXPECTED_SOPHIA_FACTS = {
    "century_or_wider_intervals": 3550,
    "exact_year_intervals": 168,
    "invalid_date_intervals": 2,
    "known_identified_total_lower_bound": 7000,
    "known_unexposed_residual": True,
    "language_labels": {
        "Ancient Greek": 150,
        "Armenian": 32,
        "Church Slavonic": 1306,
        "Greek": 10,
        "Latin": 34,
        "Low German": 1,
        "Mixed": 10,
        "N/A": 12,
        "Polish": 286,
        "Russian": 10,
        "Ukrainian": 588,
        "unlabelled": 1718,
    },
    "middle_date_band": {
        "interval_overlaps": 2920,
        "interval_wholly_inside": 1155,
        "semantic_stage_assignment": "pending_qualified_review",
        "text_bearing_ukrainian_label_wholly_inside": 549,
        "year_end": 1799,
        "year_start": 1400,
    },
    "missing_date_intervals": 10,
    "non_textual_or_no_text": 11,
    "old_date_band": {
        "interval_overlaps": 2989,
        "interval_wholly_inside": 1225,
        "semantic_stage_assignment": "pending_qualified_review",
        "text_bearing_ukrainian_label_wholly_inside": 7,
        "year_end": 1399,
        "year_start": 1000,
    },
    "quarantined_metadata": 2,
    "source_provenance": EXPECTED_SOPHIA_PROVENANCE,
    "retrieval_scope": "complete_current_public_api",
    "stage_labels_assigned": 0,
    "text_bearing": 4144,
    "valid_date_intervals": 4145,
    "writing_system_labels": {
        "Armenian": 31,
        "Cyrillic": 1982,
        "Glagolitic": 1,
        "Greek": 157,
        "Latin": 367,
        "Mixed script": 7,
        "N/A": 2,
        "unlabelled": 1610,
    },
}
EXPECTED_GAPS = {
    "kyiv_graffito_108_scholarly_crosswalk",
    "lavra_epigraphy_not_materialized",
    "saint_sophia_public_residual",
    "saint_sophia_license_expression_missing",
    "old_ukrainian_direct_text_depth",
    "ud_document_date_and_provenance_review",
    "middle_ukrainian_genre_and_region_depth",
    "nimchuk_primary_periodization_text",
}
EXPECTED_GAP_STATES = {
    gap_id: ("accepted_operational_risk" if gap_id == "saint_sophia_license_expression_missing" else "open")
    for gap_id in EXPECTED_GAPS
}
EXPECTED_SEQUENCE_CONTRACT = [
    {
        "sequence_id": "kyiv_medieval_epigraphy",
        "position": 1,
        "evidence_mode": "direct_attestation",
        "collection_ids": ["saint-sophia-inscriptions", "kyiv-pechersk-lavra-graffiti"],
        "coverage_state": "materialized_with_open_gaps",
    },
    {
        "sequence_id": "old_ukrainian_documentary_and_literary",
        "position": 2,
        "evidence_mode": "direct_text",
        "collection_ids": ["saint-sophia-inscriptions"],
        "coverage_state": "insufficient",
    },
    {
        "sequence_id": "middle_ukrainian_documentary_and_print",
        "position": 3,
        "evidence_mode": "direct_text",
        "collection_ids": ["saint-sophia-inscriptions", materialization.UD_COLLECTION_ID],
        "coverage_state": "insufficient",
    },
    {
        "sequence_id": "new_and_modern_ukrainian",
        "position": 4,
        "evidence_mode": "direct_text",
        "collection_ids": [materialization.PLUG2_COLLECTION_ID],
        "coverage_state": "large_but_not_complete",
    },
    {
        "sequence_id": "comparative_reconstruction_backlink",
        "position": 5,
        "evidence_mode": "comparative_reconstruction",
        "collection_ids": [],
        "coverage_state": "comparative_only",
    },
]
EXPECTED_RIGHTS = {
    "saint-sophia-inscriptions": {
        "reuse_scope": "phase3_textual_dataset_training_and_derived_data_release_with_attribution_field_provenance_and_takedown_readiness",
        "source_text_committed": False,
        "status": "publicly_downloadable_license_not_declared",
    },
    "kyiv-pechersk-lavra-graffiti": {
        "reuse_scope": "no_corpus_use_until_source_and_rights_are_verified",
        "source_text_committed": False,
        "status": "unknown_pending_review",
    },
    materialization.UD_COLLECTION_ID: {
        "reuse_scope": "public_training_with_share_alike_and_attribution",
        "source_text_committed": False,
        "status": "admitted",
    },
    materialization.PLUG2_COLLECTION_ID: {
        "reuse_scope": "public_training_with_attribution",
        "source_text_committed": False,
        "status": "admitted",
    },
}
EXPECTED_SOPHIA_PRIVATE_AUDIT = {
    "records": 4157,
    "dispositions": {
        "non_textual_or_no_text": 11,
        "quarantined_metadata": 2,
        "text_bearing": 4144,
    },
    "languages": EXPECTED_SOPHIA_FACTS["language_labels"],
    "writing_systems": EXPECTED_SOPHIA_FACTS["writing_system_labels"],
    "dates": {
        "valid_intervals": EXPECTED_SOPHIA_FACTS["valid_date_intervals"],
        "exact_year_intervals": EXPECTED_SOPHIA_FACTS["exact_year_intervals"],
        "century_or_wider_intervals": EXPECTED_SOPHIA_FACTS["century_or_wider_intervals"],
        "missing_intervals": EXPECTED_SOPHIA_FACTS["missing_date_intervals"],
        "invalid_intervals": EXPECTED_SOPHIA_FACTS["invalid_date_intervals"],
    },
    "bibliography": {
        "distinct_items": 12,
        "gippius_2023_portal_bibliography_matches": 0,
        "part_ix_bibliography_id": 11,
        "part_ix_linked_records": 306,
    },
    "media_assets": {
        "asset_count": 6477,
        "license_counts": {"CC BY-NC": 6477},
        "type_counts": {"Drawing": 3248, "Photograph": 3229},
    },
    "coarse_date_observations": {
        "old_1000_1399": {
            "interval_wholly_inside": EXPECTED_SOPHIA_FACTS["old_date_band"]["interval_wholly_inside"],
            "interval_overlaps": EXPECTED_SOPHIA_FACTS["old_date_band"]["interval_overlaps"],
            "text_bearing_ukrainian_label_wholly_inside": EXPECTED_SOPHIA_FACTS["old_date_band"][
                "text_bearing_ukrainian_label_wholly_inside"
            ],
        },
        "middle_1400_1799": {
            "interval_wholly_inside": EXPECTED_SOPHIA_FACTS["middle_date_band"]["interval_wholly_inside"],
            "interval_overlaps": EXPECTED_SOPHIA_FACTS["middle_date_band"]["interval_overlaps"],
            "text_bearing_ukrainian_label_wholly_inside": EXPECTED_SOPHIA_FACTS["middle_date_band"][
                "text_bearing_ukrainian_label_wholly_inside"
            ],
        },
    },
}


class HistoricalEvidenceSpineError(ValueError):
    """The historical evidence spine is stale, overclaiming, or unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HistoricalEvidenceSpineError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalEvidenceSpineError(f"cannot read {label}: {path}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _schema_validator() -> Draft202012Validator:
    schema = _read_json(SCHEMA_PATH, "historical evidence spine schema")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _validate_schema(value: Mapping[str, Any]) -> None:
    errors = sorted(_schema_validator().iter_errors(value), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "spine"
        raise HistoricalEvidenceSpineError(
            f"historical evidence spine schema violation at {location}: {errors[0].message}"
        )


def _by_id(items: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result = {item[key]: item for item in items}
    require(len(result) == len(items), f"duplicate {label} ID")
    return result


def validate_spine(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the tracked text-free coverage and evidence-authority contract."""
    spine = json.loads(json.dumps(value, ensure_ascii=False))
    _validate_schema(spine)
    require(spine["schema_version"] == SCHEMA_VERSION, "historical evidence spine version drift")
    require(spine["bindings"] == EXPECTED_BINDINGS, "historical evidence spine bindings drift")

    body = {key: item for key, item in spine.items() if key != "receipt_sha256"}
    expected_receipt = hashlib.sha256((canonical_json(body) + "\n").encode()).hexdigest()
    require(spine["receipt_sha256"] == expected_receipt, "historical evidence spine seal mismatch")

    framework_policy = spine["framework_policy"]
    require(framework_policy["canonical_framework_id"] is None, "one chronology cannot be canonicalized")
    require(framework_policy["frameworks_preserved_without_collapse"], "attributed frameworks must be preserved")
    require(
        set(framework_policy["bound_framework_ids"]) == set(periodization.REQUIRED_FRAMEWORKS),
        "historical framework set drift",
    )

    authority = spine["authority_policy"]
    require(authority["ranked_layers"] == EXPECTED_AUTHORITY_ORDER, "evidence authority order drift")
    require(authority["scalar_language_age_claim_allowed"] is False, "scalar language-age claims are forbidden")
    require(authority["proto_reconstruction_is_direct_attestation"] is False, "reconstruction cannot become corpus fact")
    learner = authority["learner_exposition"]
    require(learner["historical_authority_eligible"] is False, "learner material cannot become historical authority")
    require(learner["preserve_for_instructional_evaluation"] is True, "learner material must remain available for evaluation")

    sequence = spine["instructional_sequence"]
    require([item["sequence_id"] for item in sequence] == EXPECTED_INSTRUCTIONAL_ORDER, "instructional sequence drift")
    sequence_contract = [
        {key: item[key] for key in ("sequence_id", "position", "evidence_mode", "collection_ids", "coverage_state")}
        for item in sequence
    ]
    require(sequence_contract == EXPECTED_SEQUENCE_CONTRACT, "instructional sequence evidence binding drift")
    require(sequence[0]["evidence_mode"] == "direct_attestation", "direct medieval evidence must lead the sequence")
    require(sequence[-1]["evidence_mode"] == "comparative_reconstruction", "reconstruction must remain a backlink")

    collections = _by_id(spine["collections"], "collection_id", "collection")
    require(set(collections) == EXPECTED_COLLECTIONS, "historical collection denominator drift")
    require(
        {collection_id: item["rights"] for collection_id, item in collections.items()} == EXPECTED_RIGHTS,
        "collection-specific rights posture drift",
    )

    sophia = collections["saint-sophia-inscriptions"]
    require(sophia["custody_state"] == "materialized", "Saint Sophia must remain materialized")
    require(sophia["record_count"] == 4157, "Saint Sophia record denominator drift")
    require(sophia["source_sha256"] == "6199f2a92bd948dfe63d12e9da68637b02a4d16ff58b0ddba3d5e252bb3ec4fe", "Saint Sophia source hash drift")
    require(sophia["facts"] == EXPECTED_SOPHIA_FACTS, "Saint Sophia audited facts drift")
    require(sophia["modern_correction_eligible"] is False, "Saint Sophia cannot become modern correction gold")
    require(
        {(item["locator_role"], item["url"]) for item in sophia["locators"]}
        == {
            ("source_portal", "https://saintsophia.dh.gu.se/"),
            ("api_root", "https://saintsophia.dh.gu.se/api/"),
            (
                "official_bulk_download_api",
                "https://saintsophia.dh.gu.se/api/inscriptions/inscription/?depth=2",
            ),
            (
                "dataset_documentation",
                "https://github.com/gu-gridh/documentation/blob/eee39a2f5b009efed451e083a9654a48785b896c/gridh-projects/saintsophia.md",
            ),
            (
                "dataset_repository",
                "https://github.com/gu-gridh/Saint_Sophia/tree/4eca1b8ad9293759ce3f39a139ff9daf027882ef",
            ),
            (
                "official_bulk_download_implementation",
                "https://github.com/gu-gridh/multimodal-map/blob/574914b6a740b639eb8e90f143664aae9a86cac7/projects/sophia/Footer.vue",
            ),
            (
                "foundational_bibliography_record",
                "https://saintsophia.dh.gu.se/api/inscriptions/bibliography-item/11/",
            ),
            ("scholarly_reanalysis_doi", "https://doi.org/10.4324/9781003256236-14"),
        },
        "Saint Sophia locator set drift",
    )

    lavra = collections["kyiv-pechersk-lavra-graffiti"]
    require(lavra["custody_state"] == "not_materialized", "Lavra coverage cannot be claimed before acquisition")
    require(lavra["record_count"] is None, "unknown Lavra denominator cannot be fabricated")
    require(lavra["facts"]["corpus_count_known"] is False, "Lavra corpus denominator must remain unknown")
    require(lavra["facts"]["source_bytes_acquired"] is False, "Lavra source bytes are not acquired")
    require(
        {(item["locator_role"], item["url"]) for item in lavra["locators"]}
        == {
            ("official_monument_evidence", "https://kplavra.kyiv.ua/ua/21-kvitnya-hrafiti-ukr"),
            ("bibliographic_catalog", "https://irbis-nbuv.gov.ua/ulib/item/UKR0004515"),
        },
        "Lavra acquisition locator set drift",
    )

    ud = collections[materialization.UD_COLLECTION_ID]
    require(ud["record_count"] == 82, "UD Ukrainian document denominator drift")
    require(ud["facts"]["sentences"] == 1311 and ud["facts"]["token_rows"] == 35081, "UD denominator drift")
    require(ud["facts"]["exact_dated_documents"] == 4, "UD exact-date denominator drift")
    require(ud["facts"]["undated_documents"] == 78, "UD unresolved-date denominator drift")
    require(ud["facts"]["periodization_assignment_state"] == "unresolved", "UD cannot be auto-periodized")
    require(ud["facts"]["file_sha256"] == materialization.UD_EXPECTED_SHA256, "UD file hash set drift")

    plug2 = collections[materialization.PLUG2_COLLECTION_ID]
    require(plug2["record_count"] == 56080, "PluG2 Ukrainian document denominator drift")
    require(plug2["facts"]["date_min"] == 1816 and plug2["facts"]["date_max"] == 1954, "PluG2 date span drift")
    require(plug2["facts"]["pre_1800_documents"] == 0, "PluG2 cannot claim medieval coverage")
    require(plug2["facts"]["uk_token_sum"] == 71802066, "PluG2 token denominator drift")
    require(plug2["source_sha256"] == materialization.PLUG2_METADATA_SHA256, "PluG2 metadata hash drift")
    require(plug2["facts"]["archive_sha256"] == materialization.PLUG2_ARCHIVE_SHA256, "PluG2 archive hash drift")

    gaps = _by_id(spine["gaps"], "gap_id", "gap")
    require(gaps.keys() == EXPECTED_GAPS, "historical coverage gap denominator drift")
    require(
        {gap_id: item["state"] for gap_id, item in gaps.items()} == EXPECTED_GAP_STATES,
        "historical coverage gap disposition drift",
    )

    gates = spine["gates"]
    require(gates["evidence_first_spine_defined"] is True, "evidence spine definition is incomplete")
    for key in (
        "historical_source_coverage_ready",
        "historical_source_freeze_ready",
        "phase3_complete",
        "phase4_authorized",
    ):
        require(gates[key] is False, f"{key} cannot be asserted")
    require(gates["phase4_blocked"] is True, "Phase 4 must remain blocked")
    require(spine["provider_calls"] is False and spine["text_free"] is True, "spine must be deterministic and text-free")
    return spine


def load_spine(path: Path = SPINE_PATH) -> dict[str, Any]:
    """Load the exact tracked spine and reject byte drift at canonical paths."""
    path = Path(path)
    spine = validate_spine(_read_json(path, "historical evidence spine"))
    require(sha256_file(periodization.FREEZE_PATH) == EXPECTED_BINDINGS["historical_periodization_freeze_sha256"], "periodization freeze byte drift")
    require(sha256_file(DENOMINATOR_PATH) == EXPECTED_BINDINGS["historical_denominator_sha256"], "historical denominator byte drift")
    require(sha256_file(FULL_GATE_PATH) == EXPECTED_BINDINGS["historical_full_materialization_gate_sha256"], "historical full gate byte drift")
    if path.resolve() == SPINE_PATH.resolve():
        require(sha256_file(path) == EXPECTED_SPINE_SHA256, "tracked historical evidence spine byte drift")
    return spine


def audit_saint_sophia(path: Path, *, expected_sha256: str | None = None) -> dict[str, Any]:
    """Derive text-free Saint Sophia coverage facts from canonical private rows."""
    path = Path(path)
    require(path.is_file(), f"missing Saint Sophia JSONL: {path}")
    if expected_sha256 is not None:
        require(sha256_file(path) == expected_sha256, "Saint Sophia JSONL byte drift")
    dispositions: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    writing_systems: Counter[str] = Counter()
    rows = 0
    valid_dates = 0
    exact_dates = 0
    broad_dates = 0
    missing_dates = 0
    invalid_dates = 0
    old_definite = old_possible = old_ukrainian_definite = 0
    middle_definite = middle_possible = middle_ukrainian_definite = 0
    bibliography_ids: set[int] = set()
    media_licenses: Counter[str] = Counter()
    media_types: Counter[str] = Counter()
    part_ix_linked_records = 0
    gippius_2023_matches = 0
    for line_number, raw_line in enumerate(path.open(encoding="utf-8"), start=1):
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise HistoricalEvidenceSpineError(f"invalid Saint Sophia JSONL line {line_number}") from exc
        require(isinstance(row, dict), f"Saint Sophia line {line_number} is not an object")
        rows += 1
        dispositions[str(row.get("disposition"))] += 1
        languages[str(row.get("source_language_label") or "unlabelled")] += 1
        writing_systems[str(row.get("source_writing_system_label") or "unlabelled")] += 1
        metadata = row.get("metadata")
        require(isinstance(metadata, dict), f"Saint Sophia line {line_number} metadata is not an object")
        source_record = metadata.get("source_record", {})
        require(isinstance(source_record, dict), f"Saint Sophia line {line_number} source record is not an object")
        bibliography = source_record.get("bibliography", [])
        require(isinstance(bibliography, list), f"Saint Sophia line {line_number} bibliography is not a list")
        has_part_ix = False
        has_gippius = False
        for item in bibliography:
            require(isinstance(item, dict), f"Saint Sophia line {line_number} bibliography item is not an object")
            bibliography_id = item.get("id")
            if isinstance(bibliography_id, int):
                bibliography_ids.add(bibliography_id)
                has_part_ix = has_part_ix or bibliography_id == 11
            bibliography_text = " ".join(
                str(item.get(key) or "") for key in ("title", "authors", "body_of_publication")
            ).casefold()
            has_gippius = has_gippius or any(name in bibliography_text for name in ("gippius", "гиппиус", "гіппіус"))
        part_ix_linked_records += has_part_ix
        gippius_2023_matches += has_gippius
        media_assets = source_record.get("korniienko_image", [])
        require(isinstance(media_assets, list), f"Saint Sophia line {line_number} media assets are not a list")
        for asset in media_assets:
            require(isinstance(asset, dict), f"Saint Sophia line {line_number} media asset is not an object")
            media_licenses[str(asset.get("type_of_license") or "unlabelled")] += 1
            media_types[str(asset.get("type_of_image") or "unlabelled")] += 1
        minimum, maximum = row.get("min_year"), row.get("max_year")
        if minimum is None or maximum is None:
            missing_dates += 1
            continue
        if not isinstance(minimum, int) or not isinstance(maximum, int) or not (0 <= minimum <= maximum <= 2026):
            invalid_dates += 1
            continue
        valid_dates += 1
        exact_dates += minimum == maximum
        broad_dates += maximum - minimum >= 99
        text_ukrainian = row.get("disposition") == "text_bearing" and row.get("source_language_label") == "Ukrainian"
        if minimum >= 1000 and maximum <= 1399:
            old_definite += 1
            old_ukrainian_definite += text_ukrainian
        if maximum >= 1000 and minimum <= 1399:
            old_possible += 1
        if minimum >= 1400 and maximum <= 1799:
            middle_definite += 1
            middle_ukrainian_definite += text_ukrainian
        if maximum >= 1400 and minimum <= 1799:
            middle_possible += 1
    return {
        "records": rows,
        "dispositions": dict(sorted(dispositions.items())),
        "languages": dict(sorted(languages.items())),
        "writing_systems": dict(sorted(writing_systems.items())),
        "dates": {
            "valid_intervals": valid_dates,
            "exact_year_intervals": exact_dates,
            "century_or_wider_intervals": broad_dates,
            "missing_intervals": missing_dates,
            "invalid_intervals": invalid_dates,
        },
        "bibliography": {
            "distinct_items": len(bibliography_ids),
            "gippius_2023_portal_bibliography_matches": gippius_2023_matches,
            "part_ix_bibliography_id": 11,
            "part_ix_linked_records": part_ix_linked_records,
        },
        "media_assets": {
            "asset_count": sum(media_licenses.values()),
            "license_counts": dict(sorted(media_licenses.items())),
            "type_counts": dict(sorted(media_types.items())),
        },
        "coarse_date_observations": {
            "old_1000_1399": {
                "interval_wholly_inside": old_definite,
                "interval_overlaps": old_possible,
                "text_bearing_ukrainian_label_wholly_inside": old_ukrainian_definite,
            },
            "middle_1400_1799": {
                "interval_wholly_inside": middle_definite,
                "interval_overlaps": middle_possible,
                "text_bearing_ukrainian_label_wholly_inside": middle_ukrainian_definite,
            },
        },
    }


def audit_plug2_metadata(path: Path, *, expected_sha256: str | None = None) -> dict[str, Any]:
    """Derive the exact Ukrainian-original PluG2 date denominator."""
    path = Path(path)
    require(path.is_file(), f"missing PluG2 metadata: {path}")
    if expected_sha256 is not None:
        require(sha256_file(path) == expected_sha256, "PluG2 metadata byte drift")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="|", quotechar='"'))
    selected = [row for row in rows if row.get("doc.original") == "UK"]
    years: list[int] = []
    tokens = 0
    for row in selected:
        raw_year = row.get("doc.date", "")
        require(raw_year.isdigit() and len(raw_year) == 4, f"non-exact PluG2 Ukrainian date: {raw_year!r}")
        years.append(int(raw_year))
        try:
            tokens += int(row.get("doc.tokenCount", ""))
        except ValueError as exc:
            raise HistoricalEvidenceSpineError("invalid PluG2 token count") from exc
    require(years, "PluG2 Ukrainian denominator is empty")
    return {
        "all_documents": len(rows),
        "uk_documents": len(selected),
        "uk_token_sum": tokens,
        "date_min": min(years),
        "date_max": max(years),
        "pre_1800_documents": sum(year < 1800 for year in years),
        "exact_dated_documents": len(years),
    }


def audit_ud(root: Path, *, expected_hashes: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Derive document/date facts for explicitly Ukrainian-labelled UD rows."""
    root = Path(root)
    expected = dict(materialization.UD_EXPECTED_SHA256 if expected_hashes is None else expected_hashes)
    sentences = []
    for name, digest in sorted(expected.items()):
        path = root / name
        require(path.is_file(), f"missing UD file: {path}")
        require(sha256_file(path) == digest, f"UD file byte drift: {name}")
        sentences.extend(materialization.parse_conllu(path, source_file_sha256=digest))
    selected = [sentence for sentence in sentences if sentence.language == "orv-uk"]
    documents: dict[str, dict[str, Any]] = {}
    for sentence in selected:
        entry = documents.setdefault(
            sentence.document_id,
            {"created": sentence.created, "sentences": 0, "tokens": 0},
        )
        require(entry["created"] == sentence.created, f"UD document date drift: {sentence.document_id}")
        entry["sentences"] += 1
        entry["tokens"] += len(sentence.tokens)
    exact_years = sorted(
        int(entry["created"])
        for entry in documents.values()
        if isinstance(entry["created"], str) and entry["created"].isdigit() and len(entry["created"]) == 4
    )
    undated = sum(entry["created"] is None for entry in documents.values())
    nonexact = len(documents) - len(exact_years) - undated
    return {
        "documents": len(documents),
        "sentences": len(selected),
        "token_rows": sum(len(sentence.tokens) for sentence in selected),
        "exact_dated_documents": len(exact_years),
        "exact_years": exact_years,
        "undated_documents": undated,
        "nonexact_dated_documents": nonexact,
    }


def audit_full_materialization_receipt(
    path: Path,
    *,
    expected_file_sha256: str,
    expected_receipt_sha256: str,
) -> dict[str, Any]:
    """Verify the text-free receipt that proves the full historical conversion ran."""
    path = Path(path)
    require(path.is_file(), f"missing historical full materialization receipt: {path}")
    require(sha256_file(path) == expected_file_sha256, "historical full materialization receipt byte drift")
    receipt = _read_json(path, "historical full materialization receipt")
    body = {key: item for key, item in receipt.items() if key != "receipt_sha256"}
    actual_receipt_sha256 = hashlib.sha256(canonical_json(body).encode()).hexdigest()
    require(receipt.get("receipt_sha256") == expected_receipt_sha256, "historical full materialization receipt identity drift")
    require(actual_receipt_sha256 == expected_receipt_sha256, "historical full materialization receipt seal mismatch")
    require(receipt.get("schema_version") == "phase3_historical_full_materialization_receipt_v1", "historical full materialization receipt version drift")
    require(receipt.get("text_free") is True, "historical full materialization receipt must be text-free")
    require(receipt.get("coverage") == {
        "full_materialization_complete": True,
        "non_eligible_inputs_excluded": True,
        "periodization_assignment_state": "unresolved_pending_qualified_historical_review",
        "plug2_eligible_set_equal": True,
        "ud_eligible_set_equal": True,
    }, "historical full materialization coverage drift")
    require(receipt.get("denominators") == {
        "plug2": {
            "documents": 56245,
            "non_uk_or_unknown_documents": 165,
            "token_sum": 74497787,
            "uk_documents": 56080,
        },
        "plug2_candidate_uk_token_sum": 71802066,
        "ud_explicit_orv_uk": {"documents": 82, "sentences": 1311, "token_rows": 35081},
        "ud_other_or_unresolved_sentences": 4054,
    }, "historical full materialization denominator drift")
    require(receipt.get("outputs", {}).get("plug2") == {
        "bytes": 2075643781,
        "filename": "plug2-uk-full.jsonl.gz",
        "records": 1910748,
        "sha256": "7cf7efd0ff48827f84c503ecb84c578cb540b0d08e6fc5c857bf72ad20f96b94",
    }, "PluG2 full materialization output drift")
    require(receipt.get("outputs", {}).get("ud") == {
        "bytes": 2150133,
        "filename": "ud-orv-uk-full.jsonl.gz",
        "records": 1311,
        "sha256": "e883abd511121a2d01b3b1bc7559c4672c9dae3d0e0af3a8df1f7a6a05865cb0",
    }, "UD full materialization output drift")
    require(receipt.get("safeguards") == {
        "historical_forms_protected": True,
        "modern_correction_eligible": False,
        "phase4_authorized": False,
        "provider_calls": False,
        "source_bytes_preserved": True,
    }, "historical full materialization safeguards drift")
    return {
        "file_sha256": expected_file_sha256,
        "receipt_sha256": expected_receipt_sha256,
        "full_materialization_complete": True,
        "plug2_output_sha256": receipt["outputs"]["plug2"]["sha256"],
        "ud_output_sha256": receipt["outputs"]["ud"]["sha256"],
    }


def audit_private_inputs(
    *,
    sophia_jsonl: Path,
    plug2_metadata: Path,
    ud_root: Path,
    full_materialization_receipt: Path,
    spine_value: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Reproduce the current text-free corpus facts without exporting source text."""
    checked_spine = load_spine() if spine_value is None else validate_spine(spine_value)
    collections = _by_id(checked_spine["collections"], "collection_id", "collection")
    sophia = audit_saint_sophia(
        sophia_jsonl,
        expected_sha256=collections["saint-sophia-inscriptions"]["source_sha256"],
    )
    plug2 = audit_plug2_metadata(
        plug2_metadata,
        expected_sha256=collections[materialization.PLUG2_COLLECTION_ID]["source_sha256"],
    )
    ud = audit_ud(ud_root)
    require(sophia == EXPECTED_SOPHIA_PRIVATE_AUDIT, "Saint Sophia private audit denominator drift")
    require(plug2 == {
        "all_documents": 56245,
        "uk_documents": 56080,
        "uk_token_sum": 71802066,
        "date_min": 1816,
        "date_max": 1954,
        "pre_1800_documents": 0,
        "exact_dated_documents": 56080,
    }, "PluG2 private audit denominator drift")
    require(ud == {
        "documents": 82,
        "sentences": 1311,
        "token_rows": 35081,
        "exact_dated_documents": 4,
        "exact_years": [1413, 1436, 1456, 1473],
        "undated_documents": 78,
        "nonexact_dated_documents": 0,
    }, "UD private audit denominator drift")
    full_receipt = audit_full_materialization_receipt(
        full_materialization_receipt,
        expected_file_sha256=checked_spine["bindings"]["historical_full_materialization_receipt_file_sha256"],
        expected_receipt_sha256=checked_spine["bindings"]["historical_full_materialization_receipt_sha256"],
    )
    return {
        "schema_version": "phase3_historical_evidence_private_audit_v1",
        "text_free": True,
        "provider_calls": False,
        "saint_sophia": sophia,
        "plug2": plug2,
        "ud": ud,
        "full_materialization_receipt": full_receipt,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spine", type=Path, default=SPINE_PATH)
    parser.add_argument("--saint-sophia-jsonl", type=Path)
    parser.add_argument("--plug2-metadata", type=Path)
    parser.add_argument("--ud-root", type=Path)
    parser.add_argument("--full-materialization-receipt", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    spine = load_spine(args.spine)
    supplied = [
        args.saint_sophia_jsonl,
        args.plug2_metadata,
        args.ud_root,
        args.full_materialization_receipt,
    ]
    require(all(item is None for item in supplied) or all(item is not None for item in supplied), "private audit paths must be supplied together")
    result: dict[str, Any] = {
        "schema_version": spine["schema_version"],
        "status": spine["status"],
        "receipt_sha256": spine["receipt_sha256"],
        "open_gap_count": sum(item["state"] == "open" for item in spine["gaps"]),
        "accepted_operational_risk_count": sum(
            item["state"] == "accepted_operational_risk" for item in spine["gaps"]
        ),
        "phase3_complete": spine["gates"]["phase3_complete"],
        "phase4_blocked": spine["gates"]["phase4_blocked"],
        "provider_calls": False,
    }
    if all(item is not None for item in supplied):
        result["private_audit"] = audit_private_inputs(
            sophia_jsonl=args.saint_sophia_jsonl,
            plug2_metadata=args.plug2_metadata,
            ud_root=args.ud_root,
            full_materialization_receipt=args.full_materialization_receipt,
            spine_value=spine,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
