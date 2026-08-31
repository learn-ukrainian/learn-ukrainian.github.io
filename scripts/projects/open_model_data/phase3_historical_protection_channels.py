#!/usr/bin/env python3
"""Freeze the metadata-only historical protection channels for issue #7429.

The historical channels are a protection/admission boundary, not a source
materializer.  This module reads only committed JSON metadata and schemas.  It
never reads source text, private receipts, labels, provider output, or model
artifacts, and it never creates training rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
ADMISSION = DATA / "admission"
CONTRACTS = DATA / "contracts"
EVIDENCE = DATA / "evidence"

OUTPUT = ADMISSION / "phase3_historical_protection_channels_v1.json"
SCHEMA_PATH = CONTRACTS / "phase3_historical_protection_channels_v1.schema.json"
# Keep an immutable reference to the path pinned into this generator.  The
# public ``SCHEMA_PATH`` remains easy to inspect, but changing it at runtime
# must not silently redirect the contract builder to an unpinned schema.
PINNED_SCHEMA_PATH = SCHEMA_PATH

P1 = EVIDENCE / "phase3_p1_universe_freeze_v1.json"
P1_SCHEMA = CONTRACTS / "phase3_p1_universe_freeze_v1.schema.json"
P1_AMENDMENT = EVIDENCE / "phase3_p1_dialect_regional_protection_amendment_v1.json"
P1_AMENDMENT_SCHEMA = CONTRACTS / "phase3_p1_dialect_regional_protection_amendment_v1.schema.json"
P2 = EVIDENCE / "phase3_p2_canonical_contracts_v1.json"
P2_SCHEMA = CONTRACTS / "phase3_p2_canonical_contracts_v1.schema.json"
SCOPE_FIREWALL = EVIDENCE / "phase3_scope_circularity_firewall_v1.json"
SCOPE_FIREWALL_SCHEMA = CONTRACTS / "phase3_scope_circularity_firewall_v1.schema.json"
HISTORICAL_SPINE = ADMISSION / "phase3_historical_evidence_spine_v2.json"
HISTORICAL_SPINE_SCHEMA = CONTRACTS / "phase3_historical_evidence_spine_v2.schema.json"
PERIODIZATION = ADMISSION / "phase3_historical_periodization_freeze_v1.json"
PERIODIZATION_SCHEMA = CONTRACTS / "phase3_historical_periodization_freeze_v1.schema.json"

OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
SCHEMA_VERSION = "phase3_historical_protection_channels_v1"
RECORD_SCHEMA_VERSION = "phase3_historical_protection_disposition_v1"
SCHEMA_BINDING_NAME = "historical_protection_channels_schema"
SCHEMA_SHA256 = "7dbf2a92fff8f78860ae5fd71768742bbd037ee7b86263c6f397afa3342e4d9d"
UNKNOWN_DIMENSIONS = (
    "period_id",
    "region_id",
    "register_id",
    "recension_editorial_layer_id",
)
CONTRACT_REQUIRED_KEYS = (
    "schema_version",
    "text_free",
    "status",
    "controlling_outcome_sha256",
    "bindings",
    "input_state",
    "historical_protection",
    "source_contract",
    "source_inventory",
    "channels",
    "disposition_contract",
    "review_contract",
    "heldout_contract",
    "denominator",
    "zero_counters",
    "safety",
    "generator",
    "receipt_sha256",
)

PINS = {
    PINNED_SCHEMA_PATH: SCHEMA_SHA256,
    P1: "0b1cd81448b96b4e818aa1dedd7df7633ff88eb500bb4d6ac3668be02962a35b",
    P1_SCHEMA: "24d1547695da9c5928d1351fa149ec1010c12acceb20c250e7c4d7a650225d34",
    P1_AMENDMENT: "5a4b259f764a3d41499f0a989c02fed921c18b62c9831d361d18d19dcc948afa",
    P1_AMENDMENT_SCHEMA: "d4b987925484fb5d1e08a94d266d2f3ad01e6779335df13725244db6c61cdb10",
    P2: "dc8dfdf207728ef386cea14ddb328289b2beee5159afb98bf076e5f117602ea3",
    P2_SCHEMA: "8e93c51af812b8d32e91ae7ff55eff2332668feb7c6b990e350f2df50880d5bf",
    SCOPE_FIREWALL: "4470448c6d0f665196375cf28255d7c092148700a99934b2d0dd1f43a8a3e24c",
    SCOPE_FIREWALL_SCHEMA: "fb419508d86ee00c3d28d90bd5a999ae45483e93789907a6be4cddca568ac4ae",
    HISTORICAL_SPINE: "4a7a8f8648a7f5f8bbf05c9a9e60b348a646f054e4e5e69ebf1585447b573891",
    HISTORICAL_SPINE_SCHEMA: "8bce6863f05d20b3d31f890ff79b0fc162497fbed3b04e83014aa9a254b55108",
    PERIODIZATION: "94d07a2e4e2fe453334a494007bc823cf4be7ce07f0a21779c73163ac821a198",
    PERIODIZATION_SCHEMA: "4098ce26e3cb4ea1b4df7164d2487f9877121876ca3994a25a7481e7e5ad7c01",
}

BOUND_ARTIFACTS = {
    SCHEMA_BINDING_NAME: PINNED_SCHEMA_PATH,
    "p1": P1,
    "p1_schema": P1_SCHEMA,
    "p1_dialect_amendment": P1_AMENDMENT,
    "p1_dialect_amendment_schema": P1_AMENDMENT_SCHEMA,
    "p2": P2,
    "p2_schema": P2_SCHEMA,
    "scope_circularity_firewall": SCOPE_FIREWALL,
    "scope_circularity_firewall_schema": SCOPE_FIREWALL_SCHEMA,
    "historical_spine_v2": HISTORICAL_SPINE,
    "historical_spine_v2_schema": HISTORICAL_SPINE_SCHEMA,
    "periodization_freeze_v1": PERIODIZATION,
    "periodization_freeze_v1_schema": PERIODIZATION_SCHEMA,
}


def _bound_artifact_paths() -> dict[str, Path]:
    """Return bindings with the live schema path, so path replacement fails closed."""

    paths = dict(BOUND_ARTIFACTS)
    paths[SCHEMA_BINDING_NAME] = SCHEMA_PATH
    return paths

HISTORICAL_CLASSES = (
    "old_east_slavic_kyivan_rus",
    "middle_ukrainian",
    "church_slavonic_recension",
    "source_attested_rusyn",
)
PROTECTED_RECORD_KINDS = (
    "protected_old_east_slavic",
    "protected_middle_ukrainian",
    "protected_church_slavonic_recension",
    "protected_rusyn",
)
SAFE_RECORD_KINDS = (*PROTECTED_RECORD_KINDS, "abstention", "unresolved", "coverage_blocked")
CLAIM_ROLES = (
    "protected_historical_identity",
    "rights_provenance",
    "source_qualified_human_adjudication",
    "abstention_or_not_applicable_authority",
)
FORBIDDEN_RECORD_KEYS = frozenset(
    {
        "source_text",
        "evidence_text",
        "gold_text",
        "source_body",
        "evidence_body",
        "content",
        "text",
        "label",
        "gold",
        "prompt",
        "model_output",
        "provider_output",
        "modern_normalization",
        "modern_successor",
        "mapped_to_modern",
        "normalized_identity",
    }
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,255}$")

NON_ERASURE_INVARIANTS = {
    "historical_forms_protected": True,
    "modern_correction_eligible": False,
    "old_east_slavic_is_modern_russian": False,
    "historical_ruskyi_auto_mapped_to_modern_russian": False,
    "automatic_mapping_to_modern_national_successor": False,
    "recension_and_editorial_layer_required": True,
}


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, str]:
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_pinned(path: Path) -> dict[str, Any]:
    expected = PINS[path]
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{path.name}:hash_drift")
    return _read_json(path)


def _read_contract_schema() -> dict[str, Any]:
    """Read the canonical schema only after verifying its immutable identity."""

    if SCHEMA_PATH != PINNED_SCHEMA_PATH:
        raise ValueError("historical_protection_schema_path_drift")
    if not SCHEMA_PATH.is_file():
        raise ValueError("historical_protection_schema_missing")
    if PINS.get(PINNED_SCHEMA_PATH) != SCHEMA_SHA256:
        raise ValueError("historical_protection_schema_pin_drift")
    if sha256_file(SCHEMA_PATH) != SCHEMA_SHA256:
        raise ValueError("historical_protection_schema_hash_drift")
    schema = _read_json(SCHEMA_PATH)
    if (
        schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
        or schema.get("type") != "object"
        or schema.get("additionalProperties") is not False
        or schema.get("required") != list(CONTRACT_REQUIRED_KEYS)
    ):
        raise ValueError("historical_protection_schema_shape_drift")
    properties = schema.get("properties")
    bindings = properties.get("bindings") if isinstance(properties, Mapping) else None
    if not isinstance(bindings, Mapping) or bindings.get("additionalProperties") is not False:
        raise ValueError("historical_protection_schema_bindings_drift")
    binding_properties = bindings.get("properties")
    binding_required = bindings.get("required")
    expected_binding_names = list(_bound_artifact_paths())
    if (
        not isinstance(binding_properties, Mapping)
        or set(binding_properties) != set(expected_binding_names)
        or set(binding_required or ()) != set(expected_binding_names)
        or binding_properties.get(SCHEMA_BINDING_NAME) != {"$ref": "#/$defs/artifact"}
    ):
        raise ValueError("historical_protection_schema_binding_shape_drift")
    return schema


def _pinned_inputs() -> dict[str, dict[str, Any]]:
    _read_contract_schema()
    paths = _bound_artifact_paths()
    values = {name: _read_pinned(path) for name, path in paths.items() if path.suffix == ".json"}
    p1 = values["p1"]
    amendment = values["p1_dialect_amendment"]
    p2 = values["p2"]
    firewall = values["scope_circularity_firewall"]
    spine = values["historical_spine_v2"]
    periodization = values["periodization_freeze_v1"]

    if p1.get("schema_version") != "phase3_p1_universe_freeze_v1" or p1.get("text_free") is not True:
        raise ValueError("p1_shape_drift")
    if p1.get("controlling_outcome_sha256") != OUTCOME_SHA256:
        raise ValueError("p1_outcome_drift")
    source_units = p1.get("source_manifest", {}).get("source_units")
    if not isinstance(source_units, list) or len(source_units) != 57:
        raise ValueError("source_unit_denominator_drift")

    if (
        amendment.get("schema_version") != "phase3_p1_dialect_regional_protection_amendment_v1"
        or amendment.get("text_free") is not True
        or amendment.get("controlling_outcome_sha256") != OUTCOME_SHA256
        or amendment.get("base_p1_manifest") != artifact(P1)
    ):
        raise ValueError("p1_amendment_binding_drift")
    amendment_body = amendment.get("amendment", {})
    if amendment_body.get("composite_required_cell_count") != 16 or amendment_body.get("base_required_cell_count") != 15:
        raise ValueError("p1_amendment_denominator_drift")

    p2_binding = p2.get("p1_binding", {})
    if (
        p2.get("schema_version") != "phase3_p2_canonical_contracts_v1"
        or p2.get("text_free") is not True
        or p2.get("controlling_outcome_sha256") != OUTCOME_SHA256
        or p2_binding.get("source_unit_count") != 57
        or p2_binding.get("unknown_rights_blocker_count") != 39
        or p2_binding.get("required_cell_count") != 15
        or p2_binding.get("composite_required_cell_count") != 16
        or p2_binding.get("p1_manifest") != artifact(P1)
        or p2_binding.get("dialect_regional_protection_amendment") != artifact(P1_AMENDMENT)
    ):
        raise ValueError("p2_binding_drift")
    if p2.get("rule_slot_universe", {}).get("slot_count") != 0:
        raise ValueError("p2_rule_denominator_drift")

    firewall_denominator = firewall.get("denominator", {})
    if (
        firewall.get("schema_version") != "phase3_scope_circularity_firewall_v1"
        or firewall.get("text_free") is not True
        or firewall.get("controlling_outcome_sha256") != OUTCOME_SHA256
        or firewall_denominator.get("source_units") != 57
        or firewall_denominator.get("unknown_rights_blockers") != 39
        or firewall_denominator.get("base_required_cells") != 15
        or firewall_denominator.get("composite_required_cells") != 16
        or firewall_denominator.get("rule_slots_R") != 0
    ):
        raise ValueError("scope_firewall_binding_drift")

    collection_ids = {item.get("collection_id") for item in spine.get("collections", []) if isinstance(item, dict)}
    expected_collection_ids = {
        "saint-sophia-inscriptions",
        "korniienko-spas-na-berestovi-2013",
        "bobrovskyy-near-caves-dipinto-2010",
        "ud-old-east-slavic-ruthenian-05a029e00ccf",
        "plug2-zenodo-19482961",
    }
    gates = spine.get("gates", {})
    if (
        spine.get("schema_version") != "phase3_historical_evidence_spine_v2"
        or spine.get("text_free") is not True
        or collection_ids != expected_collection_ids
        or gates.get("qualified_historical_semantic_review_complete") is not False
        or gates.get("historical_source_coverage_ready") is not False
        or gates.get("historical_source_freeze_ready") is not False
        or gates.get("phase3_complete") is not False
        or gates.get("phase4_authorized") is not False
        or gates.get("phase4_blocked") is not True
    ):
        raise ValueError("historical_spine_gate_drift")

    scope = periodization.get("scope", {})
    if (
        periodization.get("schema_version") != "phase3_historical_periodization_freeze_v1"
        or periodization.get("source_text_committed") is not False
        or periodization.get("periodization_layer_ready") is not True
        or periodization.get("overall_phase3_source_freeze_ready") is not False
        or scope.get("historical_forms_protected") is not True
        or scope.get("old_east_slavic_is_modern_russian") is not False
        or scope.get("historical_ruskyi_auto_mapped_to_modern_russian") is not False
    ):
        raise ValueError("periodization_binding_drift")
    return values


def _safe_counts(collection: Mapping[str, Any]) -> dict[str, int]:
    counts = collection.get("counts", {})
    if not isinstance(counts, Mapping):
        return {}
    keys = ("public_api_records", "text_bearing_records", "source_labelled_ukrainian_records")
    return {key: counts[key] for key in keys if isinstance(counts.get(key), int) and not isinstance(counts[key], bool)}


def _source_inventory(spine: Mapping[str, Any]) -> list[dict[str, Any]]:
    collections = spine.get("collections")
    if not isinstance(collections, list):
        raise ValueError("historical_collection_shape_drift")
    inventory = []
    for collection in sorted(collections, key=lambda item: item.get("collection_id", "")):
        if not isinstance(collection, Mapping):
            raise ValueError("historical_collection_shape_drift")
        collection_id = collection.get("collection_id")
        if not isinstance(collection_id, str) or not collection_id:
            raise ValueError("historical_collection_identity_missing")
        rights = collection.get("rights")
        if not isinstance(rights, Mapping):
            raise ValueError("historical_collection_rights_missing")
        safe_identity = {
            key: collection.get(key)
            for key in (
                "collection_id",
                "source_kind",
                "custody_state",
                "date_evidence_state",
                "source_attribution_state",
                "modern_correction_eligible",
                "phase3_historical_training_eligible",
                "counts",
                "rights",
                "semantic_gold",
            )
        }
        provenance = {
            "collection_id": collection_id,
            "source_kind": collection.get("source_kind"),
            "custody_state": collection.get("custody_state"),
            "date_evidence_state": collection.get("date_evidence_state"),
            "source_attribution_state": collection.get("source_attribution_state"),
            "rights_status": rights.get("status"),
        }
        inventory.append(
            {
                "source_unit_id": f"historical.{collection_id}",
                "collection_id": collection_id,
                "source_kind": collection.get("source_kind"),
                "custody_state": collection.get("custody_state"),
                "date_evidence_state": collection.get("date_evidence_state"),
                "source_attribution_state": collection.get("source_attribution_state"),
                "rights_status": rights.get("status"),
                "semantic_gold": collection.get("semantic_gold") is True,
                "phase3_historical_training_eligible": collection.get("phase3_historical_training_eligible") is True,
                "record_counts": _safe_counts(collection),
                "source_artifact_sha256": PINS[HISTORICAL_SPINE],
                "source_identity_sha256": sha256_bytes(canonical_json(safe_identity)),
                "provenance_sha256": sha256_bytes(canonical_json(provenance)),
                "metadata_only": True,
            }
        )
    return inventory


def _source_ref(collection_id: str) -> str:
    return f"historical.{collection_id}"


def _channels() -> list[dict[str, Any]]:
    return [
        {
            "channel_id": "old_east_slavic_kyivan_rus",
            "protected_identity": "old_east_slavic_kyivan_rus",
            "source_unit_ids": [_source_ref("saint-sophia-inscriptions"), _source_ref("ud-old-east-slavic-ruthenian-05a029e00ccf")],
            "status": "coverage_blocked",
            "blocker_codes": [
                "qualified_historical_review_pending",
                "source_coverage_incomplete",
                "periodization_is_not_linguistic_stage_gold",
            ],
            "identity_policy": "preserve_old_east_slavic_kyivan_rus_continuum_without_modern_successor_mapping",
            "historical_forms_protected": True,
            "modern_correction_eligible": False,
        },
        {
            "channel_id": "middle_ukrainian",
            "protected_identity": "middle_ukrainian",
            "source_unit_ids": [
                _source_ref("bobrovskyy-near-caves-dipinto-2010"),
                _source_ref("korniienko-spas-na-berestovi-2013"),
                _source_ref("plug2-zenodo-19482961"),
            ],
            "status": "coverage_blocked",
            "blocker_codes": [
                "private_rights_or_redistribution_blocked",
                "qualified_historical_review_pending",
                "source_layer_or_genre_coverage_incomplete",
            ],
            "identity_policy": "preserve_middle_ukrainian_period_region_register_and_editorial_layer",
            "historical_forms_protected": True,
            "modern_correction_eligible": False,
        },
        {
            "channel_id": "church_slavonic_recension",
            "protected_identity": "church_slavonic_recension",
            "source_unit_ids": [
                _source_ref("korniienko-spas-na-berestovi-2013"),
                _source_ref("saint-sophia-inscriptions"),
                _source_ref("plug2-zenodo-19482961"),
            ],
            "status": "coverage_blocked",
            "blocker_codes": [
                "church_slavonic_historical_ukrainian_layer_separation_pending",
                "qualified_historical_review_pending",
                "rights_not_uniform",
            ],
            "identity_policy": "preserve_church_slavonic_recension_without_collapsing_mixed_layers",
            "historical_forms_protected": True,
            "modern_correction_eligible": False,
        },
        {
            "channel_id": "source_attested_rusyn",
            "protected_identity": "source_attested_rusyn",
            "source_unit_ids": [_source_ref("ud-old-east-slavic-ruthenian-05a029e00ccf")],
            "status": "unresolved",
            "blocker_codes": [
                "source_attested_identity_crosswalk_pending",
                "periodization_assignment_unresolved",
                "qualified_historical_review_pending",
            ],
            "identity_policy": "accept_source_attested_rusyn_only_with_source_qualified_identity",
            "historical_forms_protected": True,
            "modern_correction_eligible": False,
        },
        {
            "channel_id": "unresolved_historical_cyrillic",
            "protected_identity": "unresolved_historical_cyrillic",
            "source_unit_ids": [],
            "status": "coverage_blocked",
            "blocker_codes": [
                "source_artifact_not_frozen",
                "historical_identity_unresolved",
                "qualified_historical_review_pending",
            ],
            "identity_policy": "abstain_or_protect_unresolved_historical_cyrillic_without_inference",
            "historical_forms_protected": True,
            "modern_correction_eligible": False,
        },
    ]


def _binding_map() -> dict[str, dict[str, str]]:
    return {name: artifact(path) for name, path in _bound_artifact_paths().items()}


def _receipt_sha256(body: Mapping[str, Any]) -> str:
    unsigned = {key: value for key, value in body.items() if key != "receipt_sha256"}
    return sha256_bytes(canonical_json(unsigned))


def build_contract() -> dict[str, Any]:
    values = _pinned_inputs()
    spine = values["historical_spine_v2"]
    p2 = values["p2"]
    firewall = values["scope_circularity_firewall"]
    periodization = values["periodization_freeze_v1"]
    inventory = _source_inventory(spine)
    channels = _channels()
    bindings = _binding_map()
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "text_free": True,
        "status": "FROZEN_METADATA_ONLY",
        "controlling_outcome_sha256": OUTCOME_SHA256,
        "bindings": bindings,
        "input_state": {
            "historical_spine_status": spine.get("status"),
            "historical_spine_gates": {
                "qualified_historical_semantic_review_complete": False,
                "historical_source_coverage_ready": False,
                "historical_source_freeze_ready": False,
                "phase3_complete": False,
                "phase4_authorized": False,
                "phase4_blocked": True,
            },
            "periodization_status": periodization.get("status"),
            "periodization_layer_ready": True,
            "overall_phase3_source_freeze_ready": False,
            "p2_composite_input_sha256": p2["p1_binding"]["composite_input_sha256"],
            "p2_empty_rule_manifest_sha256": p2["rule_slot_universe"]["rule_manifest_sha256"],
            "scope_firewall_status": firewall.get("status"),
        },
        "historical_protection": {
            **NON_ERASURE_INVARIANTS,
            "protected_identity_classes": list(HISTORICAL_CLASSES),
            "unresolved_historical_cyrillic_identity": "unresolved_historical_cyrillic",
            "no_automatic_successor_mapping": True,
            "script_is_not_language_identity": True,
            "mixed_layers_allowed": True,
            "forced_single_label_forbidden": True,
            "identity_dimensions": [
                "language_identity",
                "script_profile",
                "context_role",
                "scope_status",
                "period_id",
                "region_id",
                "register_id",
                "recension_editorial_layer_id",
                "identity_candidates",
            ],
        },
        "source_contract": {
            "source_unit_fields_required": [
                "source_unit_id",
                "source_identity_sha256",
                "source_artifact_sha256",
                "provenance_sha256",
                "source_kind",
                "rights_status",
            ],
            "source_qualified_identity_required": True,
            "period_region_register_recension_required": True,
            "recension_editorial_layer_is_distinct": True,
            "mixed_layers_require_separate_identity_fields": True,
            "source_attested_rusyn_requires_source_attested_identity": True,
            "source_attested_rusyn_policy": {
                "requires_source_qualified_identity": True,
                "ruthenian_is_not_rusyn_alias": True,
                "unresolved_without_source_attestation": True,
            },
            "unknown_rights_route": "coverage_blocked",
            "private_only_route": "coverage_blocked",
            "unresolved_identity_route": "abstention_or_coverage_blocked",
            "source_bodies_in_contract": False,
            "public_locator_policy": "text_free_hash_bound_receipt_only",
        },
        "source_inventory": inventory,
        "channels": channels,
        "disposition_contract": {
            "record_schema_version": RECORD_SCHEMA_VERSION,
            "states": ["protected_historical", "abstention", "unresolved", "coverage_blocked"],
            "protected_record_kinds": list(PROTECTED_RECORD_KINDS),
            "semantic_admission_permitted": False,
            "exactly_one_primary_state": True,
            "coverage_blocked_emits_record": False,
            "coverage_blocked_emission_scope": "dataset_rows_only",
            "modern_correction_record_kind_forbidden": True,
            "required_identity_fields": [
                "period_id",
                "region_id",
                "register_id",
                "recension_editorial_layer_id",
                "identity_candidates",
            ],
            "required_unknown_dimensions": list(UNKNOWN_DIMENSIONS),
            "protected_requires_source_qualified_review": True,
            "unresolved_requires_explicit_unknown_dimensions": True,
            "forbidden_record_keys": sorted(FORBIDDEN_RECORD_KEYS),
        },
        "review_contract": {
            "source_qualified_human_required": True,
            "adjudication_registry_status": "FROZEN_NONADMITTING",
            "semantic_admission_permitted": False,
            "model_output_is_not_authority": True,
            "claim_typed_evidence_required": True,
            "immutable_adjudication_record_required": True,
            "required_evidence_claim_roles": list(CLAIM_ROLES),
            "protected_identity_requires_role": "protected_historical_identity",
            "rights_requires_role": "rights_provenance",
            "unresolved_route": "abstention_or_coverage_blocked",
        },
        "heldout_contract": {
            "firewall_artifact_sha256": PINS[SCOPE_FIREWALL],
            "state": "evaluation_only",
            "builder_receives_membership": False,
            "heldout_cases_selected": 0,
            "zero_heldout_cases_state": "BLOCKED_NOT_ZERO",
            "split_atomicity": [
                "source",
                "document",
                "work",
                "edition",
                "exact_duplicate_component",
                "near_duplicate_connected_component",
            ],
            "deny_namespaces": [
                "row_ids",
                "packets",
                "examples",
                "source_units",
                "document_groups",
                "work_groups",
                "edition_groups",
                "sidecars",
                "annotations",
                "labels",
                "prompts",
                "paraphrases",
                "synthetic_siblings",
                "duplicates",
                "derivatives",
                "fingerprints",
            ],
            "requirements": [
                "source_document_work_edition_split_is_disjoint",
                "cycle007_rows_sidecars_prompts_labels_and_derivatives_are_denied",
                "uncertain_lineage_fails_closed",
                "heldout_spans_and_annotations_are_not_exposed_to_builders",
            ],
        },
        "denominator": {
            "source_units": 57,
            "unknown_rights_blockers": 39,
            "p1_base_required_cells": 15,
            "p1_composite_required_cells": 16,
            "p2_rule_slots_R": 0,
            "historical_source_collections": len(inventory),
            "modern_correction_denominator_unchanged": True,
            "historical_channels_additive_protection_only": True,
            "blocked_and_unresolved_remain_denominator_visible": True,
            "partial_denominator_permitted": False,
            "cell_status_counts": {"coverage_blocked": 14, "not_applicable_with_evidence": 2},
        },
        "zero_counters": {
            "source_rows_emitted": 0,
            "historical_protected_rows_admitted": 0,
            "rusyn_rows_admitted": 0,
            "church_slavonic_rows_admitted": 0,
            "middle_ukrainian_rows_admitted": 0,
            "modern_correction_rows_created": 0,
            "heldout_cases_selected": 0,
            "provider_calls": 0,
            "labels_created": 0,
            "gold_created": 0,
            "training_rows": 0,
        },
        "safety": {
            "source_text_emitted": False,
            "modernized_text_emitted": False,
            "private_locator_emitted": False,
            "dataset_rows_emitted": False,
            "labels_created": False,
            "gold_created": False,
            "provider_calls": False,
            "training_performed": False,
        },
        "generator": artifact(Path(__file__)),
    }
    body["receipt_sha256"] = _receipt_sha256(body)
    return body


def validate_contract_integrity(contract: Mapping[str, Any]) -> bool:
    if not isinstance(contract, Mapping):
        return False
    try:
        expected = build_contract()
        return canonical_json(dict(contract)) == canonical_json(expected) and contract.get("receipt_sha256") == _receipt_sha256(contract)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def validate_contract(contract: Mapping[str, Any]) -> bool:
    """Compatibility alias for callers that use the shorter validator name."""

    return validate_contract_integrity(contract)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def _is_identifier(value: Any) -> bool:
    return isinstance(value, str) and IDENTIFIER_RE.fullmatch(value) is not None


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        if any(key in FORBIDDEN_RECORD_KEYS for key in value):
            return True
        return any(_contains_forbidden_key(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _validation_contract(contract: Mapping[str, Any] | None) -> dict[str, Any] | None:
    try:
        if contract is None:
            return build_contract()
        if not validate_contract_integrity(contract):
            return None
        return dict(contract)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _source_maps(contract: Mapping[str, Any]) -> tuple[dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    units = contract.get("source_inventory")
    channels = contract.get("channels")
    if not isinstance(units, list) or not isinstance(channels, list):
        return {}, {}
    by_unit = {item.get("source_unit_id"): item for item in units if isinstance(item, Mapping)}
    by_channel = {item.get("channel_id"): item for item in channels if isinstance(item, Mapping)}
    return by_unit, by_channel


def validate_source_channel(channel: Mapping[str, Any], contract: Mapping[str, Any] | None = None) -> bool:
    frozen = _validation_contract(contract)
    if frozen is None or not isinstance(channel, Mapping):
        return False
    _, channels = _source_maps(frozen)
    channel_id = channel.get("channel_id")
    expected = channels.get(channel_id)
    return expected is not None and canonical_json(dict(channel)) == canonical_json(dict(expected))


def validate_channel(channel: Mapping[str, Any], contract: Mapping[str, Any] | None = None) -> bool:
    return validate_source_channel(channel, contract)


def _validate_invariants(record: Mapping[str, Any]) -> bool:
    invariants = record.get("protection_invariants")
    return isinstance(invariants, Mapping) and dict(invariants) == NON_ERASURE_INVARIANTS


def _validate_layers(record: Mapping[str, Any]) -> bool:
    layers = record.get("language_layer_ids")
    if not isinstance(layers, list) or not layers or len(set(layers)) != len(layers) or not all(_is_identifier(item) for item in layers):
        return False
    return record.get("mixed_layers_allowed") is True and record.get("single_label_forced") is False


def _validate_identity_dimensions(record: Mapping[str, Any], *, required_values: bool) -> bool:
    dimensions = UNKNOWN_DIMENSIONS
    if not all(key in record for key in dimensions):
        return False
    if required_values:
        return all(_is_identifier(record.get(key)) for key in dimensions)
    return all(value is None or _is_identifier(value) for value in (record.get(key) for key in dimensions))


def _validate_unknown_dimensions(record: Mapping[str, Any]) -> bool:
    """Require the complete unresolved identity tuple in canonical order."""

    return record.get("unknown_dimensions") == list(UNKNOWN_DIMENSIONS)


def _validate_evidence_refs(record: Mapping[str, Any], contract: Mapping[str, Any], channel_id: str) -> bool:
    refs = record.get("evidence_refs")
    if not isinstance(refs, list) or not refs:
        return False
    units, channels = _source_maps(contract)
    channel = channels.get(channel_id)
    if channel is None:
        return False
    allowed_source_units = set(channel.get("source_unit_ids", []))
    record_source_units = record.get("source_unit_ids")
    if not isinstance(record_source_units, list) or not record_source_units:
        return False
    if len(set(record_source_units)) != len(record_source_units) or not set(record_source_units) <= allowed_source_units:
        return False
    seen: set[str] = set()
    referenced_source_units: set[str] = set()
    required_roles: set[str] = set()
    for ref in refs:
        if not isinstance(ref, Mapping):
            return False
        required_keys = {
            "evidence_ref_id",
            "claim_role",
            "source_unit_id",
            "source_unit_identity_sha256",
            "source_artifact_sha256",
            "provenance_sha256",
        }
        if set(ref) != required_keys:
            return False
        evidence_id = ref.get("evidence_ref_id")
        source_unit_id = ref.get("source_unit_id")
        role = ref.get("claim_role")
        if not _is_identifier(evidence_id) or evidence_id in seen or role not in CLAIM_ROLES or source_unit_id not in allowed_source_units:
            return False
        unit = units.get(source_unit_id)
        if unit is None or ref.get("source_unit_identity_sha256") != unit.get("source_identity_sha256"):
            return False
        if ref.get("source_artifact_sha256") != unit.get("source_artifact_sha256") or ref.get("provenance_sha256") != unit.get("provenance_sha256"):
            return False
        if not all(_is_sha256(ref.get(key)) for key in ("source_unit_identity_sha256", "source_artifact_sha256", "provenance_sha256")):
            return False
        seen.add(evidence_id)
        referenced_source_units.add(source_unit_id)
        required_roles.add(role)
    review = record.get("review")
    review_ids = review.get("evidence_ref_ids") if isinstance(review, Mapping) else None
    return (
        {"protected_historical_identity", "rights_provenance"} <= required_roles
        and referenced_source_units == set(record_source_units)
        and isinstance(review_ids, list)
        and set(review_ids) == seen
    )


def _validate_review(record: Mapping[str, Any], contract: Mapping[str, Any]) -> bool:
    review = record.get("review")
    if not isinstance(review, Mapping):
        return False
    required = {
        "reviewer_kind",
        "qualification_status",
        "adjudication_record_sha256",
        "evidence_ref_ids",
    }
    return (
        set(review) == required
        and review.get("reviewer_kind") == "human"
        and review.get("qualification_status") == "registered_source_qualified_human"
        and _is_sha256(review.get("adjudication_record_sha256"))
        and isinstance(review.get("evidence_ref_ids"), list)
        and bool(review.get("evidence_ref_ids"))
        and contract.get("review_contract", {}).get("adjudication_registry_status") == "BOUND"
    )


def validate_disposition_shape(record: Mapping[str, Any], contract: Mapping[str, Any] | None = None) -> bool:
    """Validate a body-free disposition shape without admitting semantic gold.

    Protected semantic shapes additionally require a bound adjudication
    registry; the frozen v1 registry therefore rejects them outright.
    """

    frozen = _validation_contract(contract)
    if frozen is None or not isinstance(record, Mapping) or _contains_forbidden_key(record):
        return False
    kind = record.get("record_kind")
    if kind not in SAFE_RECORD_KINDS or record.get("schema_version") != RECORD_SCHEMA_VERSION:
        return False
    if not _is_identifier(record.get("record_id")) or not _is_identifier(record.get("channel_id")):
        return False
    if record.get("body_free") is not True or not _validate_invariants(record) or not _validate_layers(record):
        return False
    _, channels = _source_maps(frozen)
    channel = channels.get(record.get("channel_id"))
    if channel is None:
        return False
    if kind == "coverage_blocked":
        return (
            set(record)
            == {
                "schema_version",
                "record_kind",
                "record_id",
                "channel_id",
                "blocker_code",
                "unknown_dimensions",
                "language_layer_ids",
                "mixed_layers_allowed",
                "single_label_forced",
                "protection_invariants",
                "body_free",
            }
            and _is_identifier(record.get("blocker_code"))
            and _validate_unknown_dimensions(record)
        )
    if kind in {"unresolved", "abstention"}:
        state_key = "unresolved_code" if kind == "unresolved" else "abstention_code"
        required_keys = {
            "schema_version",
            "record_kind",
            "record_id",
            "channel_id",
            state_key,
            "unknown_dimensions",
            "identity_candidates",
            "period_id",
            "region_id",
            "register_id",
            "recension_editorial_layer_id",
            "language_layer_ids",
            "mixed_layers_allowed",
            "single_label_forced",
            "protection_invariants",
            "body_free",
        }
        candidates = record.get("identity_candidates")
        channel_identity = channel.get("protected_identity")
        return (
            set(record) == required_keys
            and _is_identifier(record.get(state_key))
            and _validate_unknown_dimensions(record)
            and isinstance(candidates, list)
            and bool(candidates)
            and all(_is_identifier(item) for item in candidates)
            and len(set(candidates)) == len(candidates)
            and set(candidates) <= {*HISTORICAL_CLASSES, "unresolved_historical_cyrillic"}
            and (channel_identity == "unresolved_historical_cyrillic" or channel_identity in candidates)
            and _validate_identity_dimensions(record, required_values=False)
        )
    # A review-shaped record is not a valid protected semantic shape while
    # the pinned adjudication registry is explicitly non-admitting.  This
    # prevents laundering an arbitrary SHA plus source and rights references
    # through the shape validator.
    if frozen.get("review_contract", {}).get("adjudication_registry_status") != "BOUND":
        return False
    expected_identity = {
        "protected_old_east_slavic": "old_east_slavic_kyivan_rus",
        "protected_middle_ukrainian": "middle_ukrainian",
        "protected_church_slavonic_recension": "church_slavonic_recension",
        "protected_rusyn": "source_attested_rusyn",
    }[kind]
    required_keys = {
        "schema_version",
        "record_kind",
        "record_id",
        "channel_id",
        "language_identity",
        "source_qualified_identity",
        "source_unit_ids",
        "evidence_refs",
        "review",
        "period_id",
        "region_id",
        "register_id",
        "recension_editorial_layer_id",
        "identity_candidates",
        "language_layer_ids",
        "mixed_layers_allowed",
        "single_label_forced",
        "protection_invariants",
        "body_free",
    }
    source_units = record.get("source_unit_ids")
    candidates = record.get("identity_candidates")
    return (
        set(record) == required_keys
        and record.get("language_identity") == expected_identity
        and record.get("source_qualified_identity") is True
        and isinstance(source_units, list)
        and bool(source_units)
        and len(set(source_units)) == len(source_units)
        and all(_is_identifier(item) for item in source_units)
        and isinstance(candidates, list)
        and expected_identity in candidates
        and set(candidates) <= set(HISTORICAL_CLASSES)
        and all(_is_identifier(item) for item in candidates)
        and _validate_identity_dimensions(record, required_values=True)
        and _validate_evidence_refs(record, frozen, record["channel_id"])
        and _validate_review(record, frozen)
        and channel.get("protected_identity") == expected_identity
    )


def validate_disposition_record(record: Mapping[str, Any], contract: Mapping[str, Any] | None = None) -> bool:
    """Admit only safe blocked/unresolved/abstention routes under current gaps."""

    if not validate_disposition_shape(record, contract):
        return False
    # The registry and source-qualified review gate are intentionally
    # non-admitting in this dataset version.
    return record.get("record_kind") not in PROTECTED_RECORD_KINDS


def validate_record(record: Mapping[str, Any], contract: Mapping[str, Any] | None = None) -> bool:
    return validate_disposition_record(record, contract)


def validate_historical_disposition(record: Mapping[str, Any], contract: Mapping[str, Any] | None = None) -> bool:
    return validate_disposition_record(record, contract)


def build_coverage_blocked_record(channel_id: str, blocker_code: str = "qualified_historical_review_pending") -> dict[str, Any]:
    """Create a deterministic safe fixture/receipt record without source text."""

    return {
        "schema_version": RECORD_SCHEMA_VERSION,
        "record_kind": "coverage_blocked",
        "record_id": f"blocked:{channel_id}",
        "channel_id": channel_id,
        "blocker_code": blocker_code,
        "unknown_dimensions": list(UNKNOWN_DIMENSIONS),
        "language_layer_ids": ["historical_layer:unresolved"],
        "mixed_layers_allowed": True,
        "single_label_forced": False,
        "protection_invariants": dict(NON_ERASURE_INVARIANTS),
        "body_free": True,
    }


def build_unresolved_record(channel_id: str, *, abstention: bool = False) -> dict[str, Any]:
    kind = "abstention" if abstention else "unresolved"
    candidates_by_channel = {
        "old_east_slavic_kyivan_rus": ["old_east_slavic_kyivan_rus"],
        "middle_ukrainian": ["middle_ukrainian"],
        "church_slavonic_recension": ["church_slavonic_recension"],
        "source_attested_rusyn": ["source_attested_rusyn", "old_east_slavic_kyivan_rus"],
        "unresolved_historical_cyrillic": ["unresolved_historical_cyrillic"],
    }
    return {
        "schema_version": RECORD_SCHEMA_VERSION,
        "record_kind": kind,
        "record_id": f"{kind}:{channel_id}",
        "channel_id": channel_id,
        "abstention_code" if abstention else "unresolved_code": "source_qualified_identity_pending",
        "unknown_dimensions": list(UNKNOWN_DIMENSIONS),
        "identity_candidates": candidates_by_channel.get(channel_id, ["unresolved_historical_cyrillic"]),
        "period_id": None,
        "region_id": None,
        "register_id": None,
        "recension_editorial_layer_id": None,
        "language_layer_ids": ["historical_layer:unresolved"],
        "mixed_layers_allowed": True,
        "single_label_forced": False,
        "protection_invariants": dict(NON_ERASURE_INVARIANTS),
        "body_free": True,
    }


def write_contract(path: Path = OUTPUT) -> dict[str, Any]:
    contract = build_contract()
    path.write_bytes(canonical_json(contract))
    return contract


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the committed artifact without writing")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.check:
        expected = build_contract()
        actual = _read_json(OUTPUT)
        if canonical_json(actual) != canonical_json(expected):
            raise SystemExit("historical_protection_artifact_drift")
        return 0
    write_contract()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
