#!/usr/bin/env python3
"""Bind verified Phase 3 v3 inputs without claiming the final freeze is closed.

The receipt is deliberately text-free and fail-closed.  It proves which
deterministic and source-custody prerequisites are ready, while preserving the
hard block on authoring, broad providers, and Phase 4 until the evidence-backed
held-out package is actually sealed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_historical_evidence_spine_v2 as historical_evidence
from scripts.projects.open_model_data import phase3_historical_full_materialization as historical
from scripts.projects.open_model_data import phase3_linguistic_canary as canary
from scripts.projects.open_model_data import phase3_linguistic_representation as representation
from scripts.projects.open_model_data import phase3_saint_sophia_db_reconciliation as sophia_reconciliation
from scripts.projects.open_model_data import phase3_ua_gec_complete_context as ua_context
from scripts.projects.open_model_data import phase3_university_content_audit_freeze as university
from scripts.projects.open_model_data import phase3_v2_compatibility as compatibility
from scripts.projects.open_model_data import phase3_vspu_post_ingest_audit as vspu_audit
from scripts.projects.open_model_data import university_source_policy

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCRIPT_PATH = Path(__file__).resolve()
SCHEMA_PATH = DATA / "contracts/phase3_v3_prefreeze_readiness_v2.schema.json"
V2_COMPATIBILITY_MATRIX_PATH = DATA / "evidence/phase3_v2_compatibility_matrix_v1.json"
V2_EVALUATION_CONTRACT_PATH = DATA / "evidence/correction_protection_evaluation_contract_v1.json"
V2_FUNCTIONAL_ROLE_CONTRACT_PATH = DATA / "evidence/correction_protection_functional_role_contract_v2_1.json"
NEAR_DUPLICATE_POLICY_PATH = DATA / "evidence/correction_protection_near_duplicate_policy_v1.json"
UNIVERSITY_FREEZE_PATH = DATA / "admission/phase3_university_content_audit_freeze_v1.json"
VSPU_ADDITIVE_POLICY_PATH = DATA / "admission/phase3_vspu_additive_university_source_policy_v3.json"
V2_PROMPT_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V3_PROMPT_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"
PRIVATE_FILE_MODE = 0o600


class PrefreezeReadinessError(ValueError):
    """A required input cannot support a truthful v3 pre-freeze receipt."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PrefreezeReadinessError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise PrefreezeReadinessError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    return sha256_bytes(canonical_bytes(body))


def _regular_file(path: Path, label: str) -> None:
    try:
        result = Path(path).lstat()
    except OSError as exc:
        raise PrefreezeReadinessError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    _regular_file(path, label)
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PrefreezeReadinessError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _validate_schema(value: Mapping[str, Any], schema_path: Path, label: str) -> None:
    schema = _read_json(schema_path, f"{label} schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or label
        raise PrefreezeReadinessError(f"{label} schema violation at {location}: {errors[0].message}")


def _validate_reboot_prompt(path: Path) -> None:
    _regular_file(path, "Phase 3 reboot v3 prompt")
    require(sha256_file(path) == V3_PROMPT_SHA256, "Phase 3 reboot v3 prompt byte drift")


def _validate_sources_database(path: Path) -> str:
    _regular_file(path, "sources database")
    return sha256_file(path)


def _validate_ua_context_receipt(path: Path, sources_database_sha256: str) -> tuple[dict[str, Any], str]:
    value = _read_json(path, "UA-GEC complete-context receipt")
    try:
        validated = ua_context.validate_receipt(value)
    except ua_context.UaGecCompleteContextError as exc:
        raise PrefreezeReadinessError(str(exc)) from exc
    bindings = validated["bindings"]
    expected_bindings = {
        "implementation_sha256": sha256_file(Path(ua_context.__file__).resolve()),
        "receipt_schema_sha256": sha256_file(ua_context.SCHEMA_PATH),
        "representation_implementation_sha256": sha256_file(Path(ua_context.representation.__file__).resolve()),
        "representation_schema_sha256": sha256_file(ua_context.representation.SCHEMA_PATH),
        "sources_database_sha256": sources_database_sha256,
    }
    for key, expected in expected_bindings.items():
        require(bindings[key] == expected, f"UA-GEC complete-context {key} drift")
    require(bindings["phase3_recovery_prompt_v2_sha256"] == V2_PROMPT_SHA256, "UA-GEC v2 prompt drift")
    require(bindings["phase3_reboot_prompt_v3_sha256"] == V3_PROMPT_SHA256, "UA-GEC v3 prompt drift")
    return validated, sha256_file(path)


def _validate_historical_receipt(path: Path, gate_file_sha256: str) -> tuple[dict[str, Any], str]:
    value = _read_json(path, "historical full-materialization receipt")
    _validate_schema(value, historical.RECEIPT_SCHEMA_PATH, "historical full-materialization receipt")
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    require(value["receipt_sha256"] == representation.sha256_value(body), "historical receipt body hash drift")
    require(value["gate_sha256"] == gate_file_sha256, "historical receipt gate binding drift")
    require(value["coverage"]["full_materialization_complete"] is True, "historical full materialization is incomplete")
    require(value["safeguards"]["historical_forms_protected"] is True, "historical forms are not protected")
    require(value["safeguards"]["modern_correction_eligible"] is False, "historical forms became modern corrections")
    require(value["safeguards"]["provider_calls"] is False, "historical receipt reports provider calls")
    require(value["phase_boundaries"]["phase4_blocked"] is True, "historical receipt opens Phase 4")
    return value, sha256_file(path)


def _validate_saint_sophia_reconciliation_receipt(
    path: Path, *, university_database_sha256: str, current_database_sha256: str
) -> tuple[dict[str, Any], str]:
    value = _read_json(path, "Saint Sophia database reconciliation receipt")
    require(
        stat.S_IMODE(Path(path).stat().st_mode) == PRIVATE_FILE_MODE,
        "Saint Sophia reconciliation receipt must be mode 0600",
    )
    try:
        receipt = sophia_reconciliation.validate_receipt(value)
    except sophia_reconciliation.SaintSophiaReconciliationError as exc:
        raise PrefreezeReadinessError(str(exc)) from exc
    bindings = receipt["bindings"]
    require(
        bindings["implementation_sha256"] == sha256_file(Path(sophia_reconciliation.__file__).resolve()),
        "Saint Sophia reconciliation implementation drift",
    )
    require(
        bindings["schema_sha256"] == sha256_file(sophia_reconciliation.SCHEMA_PATH),
        "Saint Sophia reconciliation schema drift",
    )
    require(
        bindings["denominator_sha256"] == sha256_file(sophia_reconciliation.DENOMINATOR_PATH),
        "Saint Sophia reconciliation denominator drift",
    )
    require(
        receipt["database"]["pre_sha256"] == university_database_sha256,
        "Saint Sophia pre-database hash does not equal university freeze",
    )
    require(
        receipt["database"]["post_sha256"] == current_database_sha256,
        "Saint Sophia post-database hash does not equal current sources database",
    )
    return receipt, sha256_file(path)


def _validate_vspu_post_ingest_audit(path: Path, *, current_database_sha256: str) -> tuple[dict[str, Any], str, str]:
    value = _read_json(path, "VSPU post-ingest audit receipt")
    try:
        receipt = vspu_audit.validate_receipt(value)
    except vspu_audit.VspuPostIngestAuditError as exc:
        raise PrefreezeReadinessError(str(exc)) from exc
    database = receipt["database"]
    require(
        database["post_sha256"] == current_database_sha256,
        "VSPU post-database hash does not equal current sources database",
    )
    require(database["pre_sha256"] != database["post_sha256"], "VSPU database chain did not advance")
    require(database["target_rows"] == 158, "VSPU row denominator drift")
    require(database["target_fts_rows"] == 158, "VSPU FTS denominator drift")
    require(database["target_section_rows"] == 158, "VSPU section denominator drift")
    require(database["target_linked_rows"] == 158, "VSPU linkage denominator drift")
    require(
        receipt["phase_boundaries"]["source_universe_frozen"] is False,
        "VSPU audit overclaims source-universe freeze",
    )
    require(receipt["phase_boundaries"]["source_coverage_ready"] is False, "VSPU audit overclaims coverage")
    require(receipt["phase_boundaries"]["phase3_complete"] is False, "VSPU audit overclaims Phase 3")
    require(receipt["phase_boundaries"]["phase4_blocked"] is True, "VSPU audit opens Phase 4")
    try:
        policy, policy_sha256 = university_source_policy.load_policy(VSPU_ADDITIVE_POLICY_PATH)
    except university_source_policy.UniversitySourcePolicyError as exc:
        raise PrefreezeReadinessError(str(exc)) from exc
    require(
        policy_sha256 == vspu_audit.cutover.EXPECTED_ADDITIVE_POLICY_SHA256,
        "VSPU additive policy byte drift",
    )
    require(policy["source_count"] == 1 and len(policy["sources"]) == 1, "VSPU additive policy denominator drift")
    source = policy["sources"][0]
    authority = receipt["authority"]
    require(source["source_file"] == authority["source_id"], "VSPU policy/audit source identity drift")
    require(source["content_disposition"] == authority["content_disposition"], "VSPU disposition drift")
    require(source["allowed_lanes"] == authority["allowed_lanes"], "VSPU allowed-lane drift")
    require(authority["normative_rule_authority"] is False, "VSPU gained normative rule authority")
    require(authority["semantic_gold"] is False, "VSPU gained semantic-gold authority")
    require(authority["public_redistribution_authorized"] is False, "VSPU gained redistribution authority")
    return receipt, sha256_file(path), policy_sha256


def _validate_university_freeze() -> tuple[dict[str, Any], str]:
    value = _read_json(UNIVERSITY_FREEZE_PATH, "university content-audit freeze")
    try:
        validated = university.validate_document(value)
    except university.UniversityContentAuditFreezeError as exc:
        raise PrefreezeReadinessError(str(exc)) from exc
    gates = validated["gates"]
    require(gates["university_content_audit_complete"] is True, "university content audit is incomplete")
    require(gates["university_database_reconciled"] is True, "university database is unreconciled")
    require(gates["university_source_freeze_ready"] is True, "university source freeze is not ready")
    require(gates["overall_phase3_source_freeze_ready"] is False, "university receipt overclaims overall freeze")
    return validated, sha256_file(UNIVERSITY_FREEZE_PATH)


def _validate_canary(ua_gec_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    battery = canary.build_canary_battery()
    try:
        verification = canary.verify_pinned_corpus(battery, Path(ua_gec_root))
    except representation.LinguisticRepresentationError as exc:
        raise PrefreezeReadinessError(str(exc)) from exc
    packets = battery["packets"]
    shapes = [packet["edit_shape"] for packet in packets]
    require(
        shapes == ["substitution", "insertion", "deletion", "reordering", "punctuation_only", "multi_edit"],
        "semantic canary edit-shape order drift",
    )
    require(battery["provider_calls"] is False, "semantic canary reports provider calls")
    require(all(packet["source"]["complete_text"] for packet in packets), "semantic canary contains a fragment")
    require(verification["documents_verified"] == 12, "semantic canary document denominator drift")
    require(verification["retrievals_verified"] == 12, "semantic canary retrieval denominator drift")
    return battery, verification


def build_readiness(
    *,
    phase3_reboot_prompt_path: Path,
    sources_database_path: Path,
    ua_gec_root: Path,
    ua_gec_context_receipt_path: Path,
    historical_full_receipt_path: Path,
    saint_sophia_reconciliation_receipt_path: Path | None = None,
    vspu_post_ingest_audit_path: Path | None = None,
) -> dict[str, Any]:
    """Build and validate the deterministic, explicitly incomplete receipt."""
    _validate_reboot_prompt(Path(phase3_reboot_prompt_path))
    sources_database_sha256 = _validate_sources_database(Path(sources_database_path))
    try:
        compatibility_result = compatibility.verify()
        historical_gate, historical_gate_file_sha256 = historical.load_gate()
    except (compatibility.CompatibilityError, historical.HistoricalFullMaterializationError) as exc:
        raise PrefreezeReadinessError(str(exc)) from exc

    evaluation_contract = _read_json(V2_EVALUATION_CONTRACT_PATH, "v2 evaluation contract")
    aggregate_total = evaluation_contract["nonlexical_disposition_totals"]["aggregate_total"]
    require(aggregate_total == 67_041, "v2 source-unit denominator drift")
    require(compatibility_result["source_authoring_blocked"] is True, "v2 compatibility opens source authoring")
    require(compatibility_result["phase4_blocked"] is True, "v2 compatibility opens Phase 4")

    university_freeze, university_file_sha256 = _validate_university_freeze()
    historical_receipt, historical_receipt_file_sha256 = _validate_historical_receipt(
        Path(historical_full_receipt_path), historical_gate_file_sha256
    )
    vspu_receipt: dict[str, Any] | None = None
    vspu_receipt_file_sha256: str | None = None
    vspu_policy_sha256: str | None = None
    pre_vspu_database_sha256 = sources_database_sha256
    if vspu_post_ingest_audit_path is not None:
        vspu_receipt, vspu_receipt_file_sha256, vspu_policy_sha256 = _validate_vspu_post_ingest_audit(
            Path(vspu_post_ingest_audit_path),
            current_database_sha256=sources_database_sha256,
        )
        pre_vspu_database_sha256 = vspu_receipt["database"]["pre_sha256"]
    sophia_receipt: dict[str, Any] | None = None
    sophia_receipt_file_sha256: str | None = None
    if saint_sophia_reconciliation_receipt_path is not None:
        sophia_receipt, sophia_receipt_file_sha256 = _validate_saint_sophia_reconciliation_receipt(
            Path(saint_sophia_reconciliation_receipt_path),
            university_database_sha256=university_freeze["database"]["sha256"],
            current_database_sha256=pre_vspu_database_sha256,
        )
    else:
        require(
            university_freeze["database"]["sha256"] == pre_vspu_database_sha256,
            "university freeze and next database-chain state disagree",
        )
    ua_receipt, ua_receipt_file_sha256 = _validate_ua_context_receipt(
        Path(ua_gec_context_receipt_path), pre_vspu_database_sha256
    )
    battery, canary_verification = _validate_canary(Path(ua_gec_root))
    historical_evidence_spine = historical_evidence.load_spine()

    ua_complete = ua_receipt["complete_context"]
    university_sources = university_freeze["source_universe"]
    university_topics = university_freeze["topic_coverage"]["counts"]
    historical_denominators = historical_receipt["denominators"]
    excluded_units = sum(ua_complete["excluded_v2_unit_count_by_reason"].values())
    require(ua_complete["eligible_v2_unit_count"] + excluded_units == 8_937, "UA-GEC accounting drift")
    require(6_462 + 2_930 == 9_392 and 906 + 8_486 == 9_392, "Cycle 002 diagnostic accounting drift")

    body: dict[str, Any] = {
        "schema_version": "phase3_v3_prefreeze_readiness_v2",
        "status": "PREFREEZE_BLOCKED_PENDING_COMPLETE_EVALUATION_PACKAGE",
        "text_free": True,
        "provider_calls": False,
        "bindings": {
            "phase3_recovery_prompt_v2_sha256": V2_PROMPT_SHA256,
            "phase3_reboot_prompt_v3_sha256": V3_PROMPT_SHA256,
            "v2_compatibility_matrix_sha256": sha256_file(V2_COMPATIBILITY_MATRIX_PATH),
            "v2_evaluation_contract_sha256": sha256_file(V2_EVALUATION_CONTRACT_PATH),
            "v2_functional_role_contract_sha256": sha256_file(V2_FUNCTIONAL_ROLE_CONTRACT_PATH),
            "near_duplicate_policy_sha256": sha256_file(NEAR_DUPLICATE_POLICY_PATH),
            "linguistic_representation_implementation_sha256": sha256_file(Path(representation.__file__).resolve()),
            "linguistic_representation_schema_sha256": sha256_file(representation.SCHEMA_PATH),
            "linguistic_canary_implementation_sha256": sha256_file(Path(canary.__file__).resolve()),
            "ua_gec_representation_adapter_implementation_sha256": sha256_file(
                Path(ua_context.representation.__file__).resolve()
            ),
            "ua_gec_complete_context_receipt_file_sha256": ua_receipt_file_sha256,
            "ua_gec_complete_context_receipt_sha256": ua_receipt["receipt_sha256"],
            "university_content_audit_freeze_file_sha256": university_file_sha256,
            "university_content_audit_freeze_receipt_sha256": university_freeze["receipt_sha256"],
            "historical_full_gate_file_sha256": historical_gate_file_sha256,
            "historical_full_gate_receipt_sha256": historical_gate["receipt_sha256"],
            "historical_full_receipt_file_sha256": historical_receipt_file_sha256,
            "historical_full_receipt_sha256": historical_receipt["receipt_sha256"],
            "historical_evidence_spine_v2_file_sha256": sha256_file(historical_evidence.SPINE_PATH),
            "historical_evidence_spine_v2_receipt_sha256": historical_evidence_spine["receipt_sha256"],
            "historical_evidence_spine_v2_implementation_sha256": sha256_file(
                Path(historical_evidence.__file__).resolve()
            ),
            "historical_evidence_spine_v2_schema_sha256": sha256_file(historical_evidence.SCHEMA_PATH),
            **(
                {
                    "saint_sophia_reconciliation_receipt_file_sha256": sophia_receipt_file_sha256,
                    "saint_sophia_reconciliation_receipt_sha256": sophia_receipt["receipt_sha256"],
                    "saint_sophia_reconciliation_implementation_sha256": sha256_file(
                        Path(sophia_reconciliation.__file__).resolve()
                    ),
                    "saint_sophia_reconciliation_schema_sha256": sha256_file(sophia_reconciliation.SCHEMA_PATH),
                }
                if sophia_receipt is not None
                else {}
            ),
            **(
                {
                    "vspu_post_ingest_audit_file_sha256": vspu_receipt_file_sha256,
                    "vspu_post_ingest_audit_receipt_sha256": vspu_receipt["receipt_sha256"],
                    "vspu_post_ingest_audit_implementation_sha256": sha256_file(Path(vspu_audit.__file__).resolve()),
                    "vspu_post_ingest_audit_schema_sha256": sha256_file(vspu_audit.SCHEMA_PATH),
                    "vspu_additive_policy_sha256": vspu_policy_sha256,
                }
                if vspu_receipt is not None
                else {}
            ),
            "sources_database_sha256": sources_database_sha256,
            "prefreeze_implementation_sha256": sha256_file(SCRIPT_PATH),
            "prefreeze_schema_sha256": sha256_file(SCHEMA_PATH),
        },
        "denominators": {
            "v2": {"source_units": aggregate_total, "evaluation_identities": 9_392, "ua_gec_units": 8_937},
            "ua_gec_complete_context": {
                "eligible_records": ua_complete["eligible_context_record_count"],
                "represented_v2_units": ua_complete["eligible_v2_unit_count"],
                "excluded_v2_units": excluded_units,
            },
            "university": {
                "candidate_sources": university_sources["candidate_source_count"],
                "database_sources": university_sources["database_resident_source_count"],
                "mandatory_conversion_sources": university_sources["mandatory_conversion_source_count"],
                "partial_topics": university_topics["partial"],
                "sufficient_topics": university_topics["sufficient"],
            },
            **(
                {
                    "vspu_additive_university": {
                        "policy_sources": 1,
                        "database_sources": 1,
                        "database_rows": vspu_receipt["database"]["target_rows"],
                        "database_fts_rows": vspu_receipt["database"]["target_fts_rows"],
                        "database_section_rows": vspu_receipt["database"]["target_section_rows"],
                        "database_linked_rows": vspu_receipt["database"]["target_linked_rows"],
                    }
                }
                if vspu_receipt is not None
                else {}
            ),
            "historical": {
                "ud_documents": historical_denominators["ud_explicit_orv_uk"]["documents"],
                "ud_sentences": historical_denominators["ud_explicit_orv_uk"]["sentences"],
                "ud_token_rows": historical_denominators["ud_explicit_orv_uk"]["token_rows"],
                "plug2_uk_documents": historical_denominators["plug2"]["uk_documents"],
                "plug2_uk_metadata_tokens": historical_denominators["plug2_candidate_uk_token_sum"],
            },
            "v3_evaluation": {"required_evidence_backed_labels": 9_392, "frozen_evidence_backed_labels": 0},
        },
        "additive_sources": {
            "university_and_historical_outside_v2_totals": True,
            "v2_denominators_unchanged": True,
            "historical_forms_protected": True,
            "historical_modern_correction_eligible": False,
            "conversion_started": False,
            "vspu_contextual_source_ingested": vspu_receipt is not None,
            "vspu_normative_rule_authority": False,
            "vspu_semantic_gold": False,
            "vspu_public_redistribution_authorized": False,
        },
        "cycle002": {
            "identities": 9_392,
            "agreements": 6_462,
            "disagreements": 2_930,
            "rows_with_ua_gec_evidence": 906,
            "rows_without_authoritative_evidence": 8_486,
            "provider_independent": False,
            "semantic_gold": False,
            "disposition": "diagnostic_only",
        },
        "semantic_canary": {
            "packet_count": len(battery["packets"]),
            "edit_shapes": [packet["edit_shape"] for packet in battery["packets"]],
            "ua_gec_commit": canary.UA_GEC_COMMIT,
            "battery_sha256": battery["battery_sha256"],
            "verification_sha256": canary_verification["verification_sha256"],
            "documents_verified": canary_verification["documents_verified"],
            "retrievals_verified": canary_verification["retrievals_verified"],
            "complete_context": True,
            "provider_calls": False,
            "operator_display_required_before_provider": True,
            "operator_display_confirmed": True,
        },
        "readiness": {
            "inventory_compatibility_ready": True,
            "university_content_audit_ready": True,
            "university_source_freeze_ready": True,
            "historical_full_materialization_ready": True,
            "historical_evidence_gap_matrix_current": True,
            "saint_sophia_db_reconciliation_ready": sophia_receipt is not None,
            "vspu_post_ingest_audit_ready": vspu_receipt is not None,
            "linguistic_representation_ready": True,
            "semantic_canary_ready": True,
            "functional_role_contract_ready": True,
            "complete_evaluation_package_ready": False,
            "overall_source_freeze_ready": False,
            "missing_requirements": [
                "university_topic_coverage_21_partial",
                "historical_periodization_and_document_level_review_pending",
                "additive_source_role_membership_not_frozen",
                "evidence_backed_v3_heldout_labels_and_sealed_evaluation_package_missing",
            ],
        },
        "gates": {
            "new_train_development_extraction_authorized": False,
            "broad_provider_run_authorized": False,
            "source_authoring_authorized": False,
            "evaluation_partition_frozen": False,
            "source_coverage_ready": False,
            "source_freeze_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }
    receipt = {**body, "receipt_sha256": sha256_bytes(canonical_bytes(body))}
    return validate_readiness(receipt)


def validate_readiness(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    _validate_schema(receipt, SCHEMA_PATH, "v3 pre-freeze readiness receipt")
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "v3 pre-freeze receipt body hash drift")
    require(receipt["provider_calls"] is False, "pre-freeze receipt reports provider calls")
    require(receipt["cycle002"]["semantic_gold"] is False, "Cycle 002 was promoted to semantic gold")
    require(receipt["readiness"]["complete_evaluation_package_ready"] is False, "evaluation package overclaim")
    require(receipt["gates"]["source_authoring_authorized"] is False, "source authoring opened before freeze")
    require(receipt["gates"]["phase4_blocked"] is True, "Phase 4 opened before Phase 3 completion")
    bindings = receipt["bindings"]
    current_historical_evidence = historical_evidence.load_spine()
    require(
        bindings["historical_evidence_spine_v2_file_sha256"] == sha256_file(historical_evidence.SPINE_PATH),
        "historical evidence spine v2 file binding drift",
    )
    require(
        bindings["historical_evidence_spine_v2_receipt_sha256"] == current_historical_evidence["receipt_sha256"],
        "historical evidence spine v2 receipt binding drift",
    )
    require(
        bindings["historical_evidence_spine_v2_implementation_sha256"]
        == sha256_file(Path(historical_evidence.__file__).resolve()),
        "historical evidence spine v2 implementation binding drift",
    )
    require(
        bindings["historical_evidence_spine_v2_schema_sha256"] == sha256_file(historical_evidence.SCHEMA_PATH),
        "historical evidence spine v2 schema binding drift",
    )
    sophia_keys = {
        "saint_sophia_reconciliation_receipt_file_sha256",
        "saint_sophia_reconciliation_receipt_sha256",
        "saint_sophia_reconciliation_implementation_sha256",
        "saint_sophia_reconciliation_schema_sha256",
    }
    require(
        sophia_keys.issubset(bindings) or not sophia_keys.intersection(bindings),
        "partial Saint Sophia reconciliation binding",
    )
    readiness_value = receipt["readiness"].get("saint_sophia_db_reconciliation_ready")
    if readiness_value is not None:
        require(
            readiness_value is sophia_keys.issubset(bindings),
            "Saint Sophia readiness does not equal reconciliation binding presence",
        )
    vspu_keys = {
        "vspu_post_ingest_audit_file_sha256",
        "vspu_post_ingest_audit_receipt_sha256",
        "vspu_post_ingest_audit_implementation_sha256",
        "vspu_post_ingest_audit_schema_sha256",
        "vspu_additive_policy_sha256",
    }
    require(
        vspu_keys.issubset(bindings) or not vspu_keys.intersection(bindings),
        "partial VSPU post-ingest binding",
    )
    vspu_bound = vspu_keys.issubset(bindings)
    require(
        receipt["readiness"]["vspu_post_ingest_audit_ready"] is vspu_bound,
        "VSPU readiness does not equal post-ingest binding presence",
    )
    require(
        receipt["additive_sources"]["vspu_contextual_source_ingested"] is vspu_bound,
        "VSPU ingest state does not equal post-ingest binding presence",
    )
    vspu_denominator = receipt["denominators"].get("vspu_additive_university")
    require((vspu_denominator is not None) is vspu_bound, "VSPU denominator does not equal binding presence")
    if vspu_bound:
        require(
            bindings["sources_database_sha256"] == _validate_sources_database(vspu_audit.cutover.DEFAULT_LIVE_DB),
            "live VSPU successor database binding drift",
        )
        current_vspu, current_file_sha256, current_policy_sha256 = _validate_vspu_post_ingest_audit(
            vspu_audit.DEFAULT_RECEIPT_PATH,
            current_database_sha256=bindings["sources_database_sha256"],
        )
        expected_vspu_bindings = {
            "vspu_post_ingest_audit_file_sha256": current_file_sha256,
            "vspu_post_ingest_audit_receipt_sha256": current_vspu["receipt_sha256"],
            "vspu_post_ingest_audit_implementation_sha256": sha256_file(Path(vspu_audit.__file__).resolve()),
            "vspu_post_ingest_audit_schema_sha256": sha256_file(vspu_audit.SCHEMA_PATH),
            "vspu_additive_policy_sha256": current_policy_sha256,
        }
        for key, expected in expected_vspu_bindings.items():
            require(bindings[key] == expected, f"{key} drift")
        require(
            current_vspu["database"]["post_sha256"] == bindings["sources_database_sha256"],
            "VSPU successor/database binding drift",
        )
        require(
            vspu_denominator
            == {
                "policy_sources": 1,
                "database_sources": 1,
                "database_rows": current_vspu["database"]["target_rows"],
                "database_fts_rows": current_vspu["database"]["target_fts_rows"],
                "database_section_rows": current_vspu["database"]["target_section_rows"],
                "database_linked_rows": current_vspu["database"]["target_linked_rows"],
            },
            "VSPU additive denominator drift",
        )
    return receipt


def _atomic_write(path: Path, payload: bytes) -> None:
    parent = Path(path).parent
    require(not parent.is_symlink(), "output parent must not be a symlink")
    parent.mkdir(parents=True, exist_ok=True)
    require(parent.is_dir(), "output parent must be a directory")
    with tempfile.NamedTemporaryFile(dir=parent, prefix=f".{Path(path).name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, PRIVATE_FILE_MODE)
    os.replace(temporary, path)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase3-reboot-prompt", type=Path, required=True)
    parser.add_argument("--sources-database", type=Path, required=True)
    parser.add_argument("--ua-gec-root", type=Path, required=True)
    parser.add_argument("--ua-gec-context-receipt", type=Path, required=True)
    parser.add_argument("--historical-full-receipt", type=Path, required=True)
    parser.add_argument("--saint-sophia-reconciliation-receipt", type=Path)
    parser.add_argument("--vspu-post-ingest-audit", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        receipt = build_readiness(
            phase3_reboot_prompt_path=args.phase3_reboot_prompt,
            sources_database_path=args.sources_database,
            ua_gec_root=args.ua_gec_root,
            ua_gec_context_receipt_path=args.ua_gec_context_receipt,
            historical_full_receipt_path=args.historical_full_receipt,
            saint_sophia_reconciliation_receipt_path=args.saint_sophia_reconciliation_receipt,
            vspu_post_ingest_audit_path=args.vspu_post_ingest_audit,
        )
        _atomic_write(args.output, canonical_bytes(receipt))
        print(canonical_json({"ok": True, "output": str(args.output), "receipt_sha256": receipt["receipt_sha256"]}))
    except PrefreezeReadinessError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
