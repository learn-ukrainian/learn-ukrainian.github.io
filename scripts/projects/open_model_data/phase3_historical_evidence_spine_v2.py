#!/usr/bin/env python3
"""Validate the current historical evidence and gap matrix.

Version 2 preserves the evidence-first v1 spine and binds the later Spas,
Lavra, and document-chronology receipts.  It records source progress without
turning a date, title, reconstruction, or corpus language tag into semantic
historical-stage gold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_historical_evidence_spine as spine_v1
from scripts.projects.open_model_data import phase3_historical_periodization as periodization

ROOT = Path(__file__).resolve().parents[3]
SPINE_PATH = ROOT / "data/projects/open_model_data/admission/phase3_historical_evidence_spine_v2.json"
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_historical_evidence_spine_v2.schema.json"
SCHEMA_VERSION = "phase3_historical_evidence_spine_v2"

EXPECTED_SPINE_SHA256 = "4a7a8f8648a7f5f8bbf05c9a9e60b348a646f054e4e5e69ebf1585447b573891"
EXPECTED_V1_SHA256 = "61a937f150a4cbecf6b12774ef812d67289705d9523c4e766c95e721b7451076"
EXPECTED_V1_SCHEMA_SHA256 = "6fe120add7739962f8ee2727e0aeef3db0f34af5a14949b638ed65948645da10"
EXPECTED_V1_RECEIPT_SHA256 = "cc19bc1189b6c31714434027ce46c340c9f00a8ef6574e22005a2a5c44a2ae71"
EXPECTED_PROMPT_V3_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"
EXPECTED_PROMPT_V2_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"

EXPECTED_CODE_BINDINGS = {
    "data/projects/open_model_data/contracts/phase3_historical_document_chronology_receipt_v2.schema.json": (
        "b0e19c906b1c487b8ad390987c1c3ba6afc6171afe584170e45ec0497d03e9f6"
    ),
    "data/projects/open_model_data/contracts/phase3_lavra_near_caves_intake_receipt_v1.schema.json": (
        "b516cf879c07ea7267f1c1a481f454bc7c4765c5b8e5b94042632436166b25be"
    ),
    "data/projects/open_model_data/contracts/phase3_spas_catalog_materialization_receipt_v1.schema.json": (
        "63605b8825627701dd696f97a9e29b9ed6a67ad6b4dea0613af7b7af2b99daae"
    ),
    "data/projects/open_model_data/contracts/phase3_spas_glyph_adapter_receipt_v1.schema.json": (
        "50931ae2ecb7eecad58fa88a902b54838e22ec64f9b23f43832d610f1832f081"
    ),
    "data/projects/open_model_data/contracts/phase3_spas_layout_candidate_receipt_v1.schema.json": (
        "26ad006a4e654f94e18779f8ae21900630660611490ef638ff76f8e490cfc140"
    ),
    "data/projects/open_model_data/contracts/phase3_spas_source_attribution_receipt_v1.schema.json": (
        "d8be596ce5ce0cf17e2d133f7b1a863388cdcb1e54f8aefd156d831e94a161a6"
    ),
    "scripts/projects/open_model_data/phase3_historical_document_chronology_source_dates.py": (
        "d2c1433e0df574de067f560ff9ec09bfef2470a090df31fe5de16925ce7f56e1"
    ),
    "scripts/projects/open_model_data/phase3_lavra_near_caves_intake.py": (
        "83a5d310aa85697c4d04e29c95b9b199bd227fb044f3a860411bffd224a314d9"
    ),
    "scripts/projects/open_model_data/phase3_spas_catalog_materialization.py": (
        "5f48b921aec53faa62b742fc3c433dfb6b92efc9be429e2e1731c5ce9a38a26d"
    ),
    "scripts/projects/open_model_data/phase3_spas_glyph_adapter.py": (
        "7686f499550f0c3e29896f7f40d41d1b8f1711ae2d32a690f7bd4130570d80f4"
    ),
    "scripts/projects/open_model_data/phase3_spas_layout_candidates.py": (
        "2bc7a49dfea7a7cb9118321f4a8010d54b34f1aded3031a400ae84e5a0c4a034"
    ),
    "scripts/projects/open_model_data/phase3_spas_source_attribution.py": (
        "b2d1aedc003a202b613a1c7cecab596ad0826b488eff05c496f8a470e7ce00d0"
    ),
}

EXPECTED_PRIVATE_RECEIPTS = {
    "historical-document-chronology-source-dates-v2": {
        "drive_relative_path": (
            "processed/phase3-v3-historical-document-chronology-source-dates-v2/"
            "historical-document-chronology-receipt-v2.json"
        ),
        "schema_version": "phase3_historical_document_chronology_receipt_v2",
        "file_sha256": "11a047c5c830799b5b311c18b8f883198f5d3e72edb14881c4fd4e3a8a291647",
        "receipt_sha256": "c7cdae56c4e0f46c353c4bb52e957942a708d31fec212c3f1681929cf2ac33b3",
        "output_records": 56162,
        "output_sha256": "dc0ecd7df0c8daa9f46f758d25464c1bb9882db345845ec82ffa87fd3f4a0829",
    },
    "lavra-near-caves-intake-v1": {
        "drive_relative_path": (
            "processed/phase3-v3-lavra-near-caves-dipinto-raw-v1/near-caves-intake-receipt-v1.json"
        ),
        "schema_version": "phase3_lavra_near_caves_intake_receipt_v1",
        "file_sha256": "994bec4ca662d3e8f856daba69b437108cb74c370ba31e0755f9cc7975344adc",
        "receipt_sha256": "8921ee7e5c5de2943de83ef7a450d6827e85a0332a64b3d7694cae6995ec0455",
        "output_records": 19,
        "output_sha256": "9766e85751c64a52ee402e517ae7e5bfa6ea4c94eee8f8668e4aaf384c60eed7",
    },
    "spas-catalog-materialization-v1": {
        "drive_relative_path": ("processed/phase3-v3-spas-na-berestovi-raw-v1/materialization-receipt-v1.json"),
        "schema_version": "phase3_spas_catalog_materialization_receipt_v1",
        "file_sha256": "fe14a7c0dfb7fcb1304cf5ad360cba11135bcc42bb4cd78ef314773e948a492b",
        "receipt_sha256": "a2521b1026878520e9180a04a11f68a683845cf214b44d3794c8c761c309b7d3",
        "output_records": 477,
        "output_sha256": "974f05399d69faadc2fd7ffe96a06e0e2d1d409464a1eb1de9962bf772fabd05",
    },
    "spas-glyph-adapter-v1": {
        "drive_relative_path": ("processed/phase3-v3-spas-bukyvede-unicode-v2/glyph-adapter-receipt-v1.json"),
        "schema_version": "phase3_spas_glyph_adapter_receipt_v1",
        "file_sha256": "8278b133026ded0b197e8518167730189963a9a781d91e1ac7751eb73b3ca372",
        "receipt_sha256": "e494cd3030b74d40574a03498ca6089d23a6827e9e8283b5df0d34965c02adf8",
        "output_records": 477,
        "output_sha256": "3a828f0a4ca57e5f44a4bf72536ed6de8597f6633e2987bab663cacc55dbf6d4",
    },
    "spas-layout-candidates-v1": {
        "drive_relative_path": ("processed/phase3-v3-spas-layout-candidates-v2/layout-candidate-receipt-v1.json"),
        "schema_version": "phase3_spas_layout_candidate_receipt_v1",
        "file_sha256": "aa8a67b32c478a309826a08c94679a45d31e5cfa558fa4e977bf2959a034c3d4",
        "receipt_sha256": "5d2ff83247101de7d7de26f61d17a1d34fcd20c24ead14e5f7b0a515de2482d1",
        "output_records": 477,
        "output_sha256": "661a8f247ecb5f0a6413c53346e72a8255a63e51fbe7b47ef1d2d10b89bd90d6",
    },
    "spas-source-attribution-v1": {
        "drive_relative_path": ("processed/phase3-v3-spas-source-attribution-v3/source-attribution-receipt-v1.json"),
        "schema_version": "phase3_spas_source_attribution_receipt_v1",
        "file_sha256": "3962bf91c7c78f844cf5f58689dfa0177ef1065f1891c0b31095eb632c7b80cd",
        "receipt_sha256": "37b04a45a389de127d5b172055d75e56a3b752010ef3cb2cb9a3b94fe6d12875",
        "output_records": 90,
        "output_sha256": "2e6a1e0ea3ca43240ca59e141b3d61c372fc4604c70d69e0df86601d66902858",
    },
}

EXPECTED_RECEIPT_SCHEMAS = {
    "historical-document-chronology-source-dates-v2": (
        ROOT / "data/projects/open_model_data/contracts/phase3_historical_document_chronology_receipt_v2.schema.json"
    ),
    "lavra-near-caves-intake-v1": (
        ROOT / "data/projects/open_model_data/contracts/phase3_lavra_near_caves_intake_receipt_v1.schema.json"
    ),
    "spas-catalog-materialization-v1": (
        ROOT / "data/projects/open_model_data/contracts/phase3_spas_catalog_materialization_receipt_v1.schema.json"
    ),
    "spas-glyph-adapter-v1": (
        ROOT / "data/projects/open_model_data/contracts/phase3_spas_glyph_adapter_receipt_v1.schema.json"
    ),
    "spas-layout-candidates-v1": (
        ROOT / "data/projects/open_model_data/contracts/phase3_spas_layout_candidate_receipt_v1.schema.json"
    ),
    "spas-source-attribution-v1": (
        ROOT / "data/projects/open_model_data/contracts/phase3_spas_source_attribution_receipt_v1.schema.json"
    ),
}

EXPECTED_COLLECTION_IDS = {
    "saint-sophia-inscriptions",
    "korniienko-spas-na-berestovi-2013",
    "bobrovskyy-near-caves-dipinto-2010",
    "ud-old-east-slavic-ruthenian-05a029e00ccf",
    "plug2-zenodo-19482961",
}
EXPECTED_SEQUENCE_IDS = [
    "kyiv_medieval_epigraphy",
    "old_ukrainian_documentary_and_literary",
    "middle_ukrainian_documentary_and_print",
    "new_and_modern_ukrainian",
    "comparative_reconstruction_backlink",
]
EXPECTED_GAP_STATES = {
    "lavra_epigraphy_not_materialized": "narrowed_open",
    "saint_sophia_public_residual": "open",
    "saint_sophia_license_expression_missing": "accepted_operational_risk",
    "kyiv_graffito_108_scholarly_crosswalk": "open",
    "old_ukrainian_direct_text_depth": "narrowed_open",
    "ud_document_date_and_provenance_review": "narrowed_open",
    "middle_ukrainian_genre_and_region_depth": "narrowed_open",
    "nimchuk_primary_periodization_text": "open",
    "spas_catalog_layer_separation": "open",
    "lavra_legacy_font_and_layer_separation": "open",
    "qualified_historical_semantic_review": "open",
}
EXPECTED_COLLECTIONS_SHA256 = "021491aeafe24755b871f3bc468776aaab0f7722efb14156db90c23ce6249419"
EXPECTED_COVERAGE_MATRIX_SHA256 = "22f6b74d3676447d8170fed6513e6d16fb080a82d415902afc820c9fe0ad0341"
EXPECTED_GAP_DISPOSITIONS_SHA256 = "1dc3c3a9e8ab32e2e3796e108ae39e0134681cebc43d08d8f15d1fa0cd9719f3"


class HistoricalEvidenceSpineV2Error(ValueError):
    """The v2 historical evidence matrix is stale, incomplete, or unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HistoricalEvidenceSpineV2Error(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalEvidenceSpineV2Error(f"cannot read {label}: {path}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _validate_with_schema(value: Mapping[str, Any], schema_path: Path, label: str) -> None:
    schema = _read_json(schema_path, f"{label} schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or label
        raise HistoricalEvidenceSpineV2Error(f"{label} schema violation at {location}: {errors[0].message}")


def _items_by_id(items: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result = {item[key]: item for item in items}
    require(len(result) == len(items), f"duplicate {label} ID")
    return result


def _expected_bindings() -> dict[str, Any]:
    private = []
    for receipt_id, binding in EXPECTED_PRIVATE_RECEIPTS.items():
        private.append({"receipt_id": receipt_id, **binding})
    return {
        "phase3_reboot_prompt_v3_sha256": EXPECTED_PROMPT_V3_SHA256,
        "phase3_recovery_prompt_v2_sha256": EXPECTED_PROMPT_V2_SHA256,
        "historical_periodization_freeze_sha256": periodization.EXPECTED_FREEZE_SHA256,
        "historical_evidence_spine_v1_sha256": EXPECTED_V1_SHA256,
        "historical_evidence_spine_v1_schema_sha256": EXPECTED_V1_SCHEMA_SHA256,
        "code_bindings": [
            {"logical_path": logical_path, "sha256": digest} for logical_path, digest in EXPECTED_CODE_BINDINGS.items()
        ],
        "private_receipts": private,
    }


def validate_spine(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the text-free matrix, exact denominators, and fail-closed gates."""
    spine = json.loads(json.dumps(value, ensure_ascii=False))
    _validate_with_schema(spine, SCHEMA_PATH, "historical evidence spine v2")
    require(spine["schema_version"] == SCHEMA_VERSION, "historical evidence spine v2 version drift")

    body = {key: item for key, item in spine.items() if key != "receipt_sha256"}
    require(spine["receipt_sha256"] == sha256_value(body), "historical evidence spine v2 seal mismatch")
    require(spine["bindings"] == _expected_bindings(), "historical evidence spine v2 bindings drift")
    require(
        spine["supersedes"]
        == {
            "v1_file_sha256": EXPECTED_V1_SHA256,
            "v1_receipt_sha256": EXPECTED_V1_RECEIPT_SHA256,
            "reason": (
                "The v1 spine predates the bounded Lavra intake, Spas catalogue pipeline, and "
                "source-derived chronology for all 56,162 UD and PluG2 documents."
            ),
        },
        "historical evidence spine v2 supersession drift",
    )

    framework = spine["framework_policy"]
    require(framework["canonical_framework_id"] is None, "historical frameworks cannot be collapsed")
    require(
        set(framework["bound_framework_ids"]) == set(periodization.REQUIRED_FRAMEWORKS),
        "historical framework denominator drift",
    )

    collections = _items_by_id(spine["collections"], "collection_id", "collection")
    require(sha256_value(spine["collections"]) == EXPECTED_COLLECTIONS_SHA256, "collection matrix drift")
    require(set(collections) == EXPECTED_COLLECTION_IDS, "historical collection denominator drift")
    for item in collections.values():
        require(item["phase3_historical_training_eligible"] is False, "unreviewed collection entered training")
        require(item["semantic_gold"] is False, "unreviewed collection entered semantic gold")
        require(item["modern_correction_eligible"] is False, "historical collection entered correction gold")

    require(
        collections["korniienko-spas-na-berestovi-2013"]["counts"]
        == {
            "catalog_records": 477,
            "candidate_records": 90,
            "source_attributed_records": 81,
            "unresolved_candidate_records": 12,
        },
        "Spas denominator drift",
    )
    require(
        collections["bobrovskyy-near-caves-dipinto-2010"]["counts"]
        == {"article_pages": 19, "inscription_witnesses": 1, "legacy_font_spans": 559},
        "Lavra bounded denominator drift",
    )
    require(
        collections["ud-old-east-slavic-ruthenian-05a029e00ccf"]["counts"]
        == {
            "documents": 82,
            "exact_year_documents": 80,
            "bounded_interval_documents": 2,
            "sentences": 1311,
            "token_rows": 35081,
        },
        "UD chronology denominator drift",
    )
    require(
        collections["plug2-zenodo-19482961"]["counts"]
        == {"documents": 56080, "exact_year_documents": 56080, "token_sum": 71802066},
        "PluG2 denominator drift",
    )

    gaps = _items_by_id(spine["gap_dispositions"], "gap_id", "gap")
    require(
        sha256_value(spine["gap_dispositions"]) == EXPECTED_GAP_DISPOSITIONS_SHA256,
        "gap disposition matrix drift",
    )
    require(
        {gap_id: gap["current_state"] for gap_id, gap in gaps.items()} == EXPECTED_GAP_STATES,
        "historical gap disposition drift",
    )
    referenced_gaps = {gap_id for item in collections.values() for gap_id in item["residual_gap_ids"]} | {
        gap_id for cell in spine["coverage_matrix"] for gap_id in cell["residual_gap_ids"]
    }
    require(referenced_gaps <= set(gaps), "collection or coverage cell refers to an unknown gap")

    coverage = spine["coverage_matrix"]
    require(sha256_value(coverage) == EXPECTED_COVERAGE_MATRIX_SHA256, "coverage matrix drift")
    require([item["sequence_id"] for item in coverage] == EXPECTED_SEQUENCE_IDS, "coverage sequence drift")
    require([item["position"] for item in coverage] == [1, 2, 3, 4, 5], "coverage positions drift")
    for cell in coverage:
        require(set(cell["collection_ids"]) <= set(collections), "coverage cell refers to unknown collection")
    require(coverage[0]["evidence_mode"] == "direct_attestation", "direct attestation must lead the spine")
    require(
        coverage[-1]["evidence_mode"] == "comparative_reconstruction" and not coverage[-1]["collection_ids"],
        "comparative reconstruction cannot masquerade as a direct corpus",
    )

    gates = spine["gates"]
    require(gates["historical_content_gap_matrix_current"] is True, "historical gap matrix is not current")
    require(
        gates["incremental_private_receipt_and_output_hashes_verified"] is True,
        "incremental receipt and output hash verification is disabled",
    )
    require(gates["qualified_historical_semantic_review_complete"] is False, "semantic review is overclaimed")
    for key in (
        "historical_source_coverage_ready",
        "historical_source_freeze_ready",
        "phase3_complete",
        "phase4_authorized",
    ):
        require(gates[key] is False, f"{key} cannot be asserted")
    require(gates["phase4_blocked"] is True, "Phase 4 must remain blocked")
    require(spine["text_free"] is True and spine["provider_calls"] is False, "matrix must be local and text-free")
    return spine


def load_spine(path: Path = SPINE_PATH) -> dict[str, Any]:
    """Load the exact v2 matrix and prove that its v1 base is still current."""
    checked_v1 = spine_v1.load_spine()
    require(checked_v1["receipt_sha256"] == EXPECTED_V1_RECEIPT_SHA256, "v1 receipt identity drift")
    require(sha256_file(spine_v1.SPINE_PATH) == EXPECTED_V1_SHA256, "v1 spine byte drift")
    require(sha256_file(spine_v1.SCHEMA_PATH) == EXPECTED_V1_SCHEMA_SHA256, "v1 spine schema byte drift")
    for logical_path, expected_sha256 in EXPECTED_CODE_BINDINGS.items():
        require(sha256_file(ROOT / logical_path) == expected_sha256, f"bound source byte drift: {logical_path}")
    checked = validate_spine(_read_json(path, "historical evidence spine v2"))
    if path.resolve() == SPINE_PATH.resolve():
        require(sha256_file(path) == EXPECTED_SPINE_SHA256, "tracked historical evidence spine v2 byte drift")
    return checked


def audit_private_receipts(*, drive_root: Path, spine_value: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Verify every new private receipt and exact output hash from one Drive root."""
    checked = load_spine() if spine_value is None else validate_spine(spine_value)
    root = Path(drive_root).resolve()
    require(root.is_dir(), f"historical Drive root is missing: {root}")
    verified: list[dict[str, Any]] = []
    for binding in checked["bindings"]["private_receipts"]:
        receipt_id = binding["receipt_id"]
        relative = Path(binding["drive_relative_path"])
        require(not relative.is_absolute() and ".." not in relative.parts, "unsafe private receipt path")
        receipt_path = (root / relative).resolve()
        require(receipt_path.is_relative_to(root), "private receipt path escapes Drive root")
        require(receipt_path.is_file(), f"missing private receipt: {relative.as_posix()}")
        require(sha256_file(receipt_path) == binding["file_sha256"], f"private receipt byte drift: {receipt_id}")
        receipt = _read_json(receipt_path, f"{receipt_id} receipt")
        _validate_with_schema(receipt, EXPECTED_RECEIPT_SCHEMAS[receipt_id], receipt_id)
        require(receipt.get("schema_version") == binding["schema_version"], f"receipt version drift: {receipt_id}")
        body = {key: item for key, item in receipt.items() if key != "receipt_sha256"}
        require(sha256_value(body) == binding["receipt_sha256"], f"receipt seal mismatch: {receipt_id}")
        require(receipt.get("receipt_sha256") == binding["receipt_sha256"], f"receipt identity drift: {receipt_id}")
        output = receipt.get("output")
        require(isinstance(output, dict), f"receipt has no single output: {receipt_id}")
        require(output.get("records") == binding["output_records"], f"output denominator drift: {receipt_id}")
        require(output.get("sha256") == binding["output_sha256"], f"output identity drift: {receipt_id}")
        output_path = receipt_path.parent / output["filename"]
        require(output_path.is_file(), f"missing private output: {output_path}")
        require(sha256_file(output_path) == binding["output_sha256"], f"private output byte drift: {receipt_id}")
        verified.append(
            {
                "receipt_id": receipt_id,
                "receipt_file_sha256": binding["file_sha256"],
                "output_records": binding["output_records"],
                "output_sha256": binding["output_sha256"],
            }
        )

    by_id = {item["receipt_id"]: item for item in checked["bindings"]["private_receipts"]}
    chronology = _read_json(
        root / by_id["historical-document-chronology-source-dates-v2"]["drive_relative_path"],
        "chronology receipt",
    )
    require(
        chronology["denominators"]
        == {
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
        "chronology source-date denominator drift",
    )
    require(
        chronology["coverage"]["qualified_historical_semantic_review_complete"] is False,
        "chronology receipt overclaims semantic review",
    )

    attribution = _read_json(
        root / by_id["spas-source-attribution-v1"]["drive_relative_path"],
        "Spas attribution receipt",
    )
    require(
        attribution["denominator"]
        == {
            "attributed_unresolved_record_overlap": 3,
            "candidate_lines": 101,
            "candidate_records": 90,
            "input_records": 477,
            "source_attributed_lines": 82,
            "source_attributed_records": 81,
            "unresolved_lines": 19,
            "unresolved_records": 12,
        },
        "Spas attribution denominator drift",
    )
    require(attribution["safeguards"]["semantic_gold"] is False, "Spas attribution became semantic gold")

    lavra = _read_json(
        root / by_id["lavra-near-caves-intake-v1"]["drive_relative_path"],
        "Lavra receipt",
    )
    require(lavra["denominator"]["article_pages"] == 19, "Lavra page denominator drift")
    require(lavra["residuals"]["lavra_cave_corpus_gap_closed"] is False, "Lavra corpus gap was overclosed")
    require(lavra["safeguards"]["training_eligible"] is False, "Lavra intake entered training")

    return {
        "schema_version": "phase3_historical_evidence_private_audit_v2",
        "verified_receipt_count": len(verified),
        "verified_output_record_sum": sum(item["output_records"] for item in verified),
        "verified_receipts": verified,
        "text_free": True,
        "provider_calls": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spine", type=Path, default=SPINE_PATH)
    parser.add_argument("--drive-root", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    spine = load_spine(args.spine)
    result: dict[str, Any] = {
        "schema_version": spine["schema_version"],
        "status": spine["status"],
        "receipt_sha256": spine["receipt_sha256"],
        "collection_count": len(spine["collections"]),
        "gap_count": len(spine["gap_dispositions"]),
        "phase3_complete": spine["gates"]["phase3_complete"],
        "phase4_blocked": spine["gates"]["phase4_blocked"],
        "provider_calls": False,
    }
    if args.drive_root is not None:
        result["private_audit"] = audit_private_receipts(drive_root=args.drive_root, spine_value=spine)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
