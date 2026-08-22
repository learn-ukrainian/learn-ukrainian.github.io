#!/usr/bin/env python3
"""Fail-closed, text-free certification of the complete Cycle 007 label path."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import tempfile
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract
from scripts.projects.open_model_data import phase3_cycle007_evidence_validator as validator

ROOT = Path(__file__).resolve().parents[1]
CYCLE = "phase3-v2-1-evaluation-cycle-007"
SOURCE_CYCLE = "phase3-v2-1-evaluation-cycle-005"
AMENDMENT_SHA256 = "4f2e3e58964cae391c3933ffdce531296a0744808b0154231ca513049602fea0"
CYCLE007_AMENDMENT_SHA256 = AMENDMENT_SHA256
SOURCE_CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
CUSTODY_SHA256 = SOURCE_CUSTODY_SHA256
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
MANIFEST_SHA256 = SOURCE_MANIFEST_SHA256
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"

LANES = {"clean_label": 40, "residual_label": 164}
LANE_ROW_COUNTS = {"clean_label": 2_000, "residual_label": 8_159}
ROW_COUNT = 10_159
PACKET_COUNT = 204

GROK_ROOT = "label-output-grok-cycle007-v1"
GEMINI_ROOT = "label-output-gemini-cycle007-v1"
COMPARE_ROOT = "dual-label-output-cycle007-v1"
COMPARE_OUTPUT = COMPARE_ROOT
AUDIT_ROOT = "consensus-audit-cycle007-v1"
ADJUDICATION_ROOT = "dual-label-adjudication-cycle007-v1"
ADJUDICATION_OUTPUT = ADJUDICATION_ROOT
RESOLUTION_ROOT = "dual-label-final-cycle007-v1"
RESOLUTION_OUTPUT = RESOLUTION_ROOT

EXPECTED_MODELS = {
    "grok": {"exact_model": "grok-4.5", "model_family": "xai", "harness": "native_grok"},
    "gemini": {
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
    },
}
CONTROL_ROOT = "control"
CONTROL_CODE_PATHS = {
    "gemini_runner": ROOT / "batch_state/phase3-run-cycle007-gemini-label-provider-batch-v1.py",
    "label_validator": ROOT / "batch_state/phase3-cycle007-label-validation-v1.py",
    "controller": ROOT / "batch_state/phase3-run-cycle007-controller-v1.py",
    "grok_runner": ROOT / "batch_state/phase3-run-cycle007-grok-label-provider-batch-v1.py",
    "compare_runner": ROOT / "batch_state/phase3-compare-cycle007-dual-labels-v1.py",
    "audit_runner": ROOT / "batch_state/phase3-audit-cycle007-consensus-v1.py",
    "adjudicate_runner": ROOT / "batch_state/phase3-run-cycle007-dual-label-adjudication-v1.py",
    "resolve_runner": ROOT / "batch_state/phase3-apply-cycle007-operator-resolutions-v1.py",
    "certify_runner": ROOT / "batch_state/phase3-verify-cycle007-label-completion-v1.py",
}
CANARY_RUNNER = ROOT / "batch_state/phase3-run-cycle007-public-canaries-v1.py"
EVIDENCE_COMPILER = ROOT / "scripts/projects/open_model_data/phase3_cycle007_evidence_compiler.py"
EVIDENCE_VALIDATOR = ROOT / "scripts/projects/open_model_data/phase3_cycle007_evidence_validator.py"
HEX64 = re.compile(r"^[0-9a-f]{64}$")

REJECTS = frozenset(
    {
        "agree",
        "reject_fragment_or_too_short",
        "reject_exercise_or_task_prompt",
        "reject_error_or_contrast_example",
        "reject_table_list_formula_code",
        "reject_metalinguistic_or_grammar_talk",
        "reject_quoted_literary_or_anthology",
        "reject_archaic_historical_language",
        "reject_dialectal_regional_surzhyk",
        "reject_foreign_or_translation_artifact",
        "reject_learner_or_simplified_broken",
        "reject_parallel_norm_or_pre2026_only",
        "reject_mixed_or_uncertain",
        "reject_insufficient_locator_evidence",
    }
)
GENRES = frozenset({"expository_narrative", "scientific_expository", "instructional_content_expository"})
TAX = contract.RESIDUAL_PHENOMENON_TAXONOMY
DEC = frozenset({"positive", "acceptable_control", "protected", "abstention", "disagreement"})

FAILURE_CODES = frozenset(
    {
        "package_modes",
        "no_temp_dirs",
        "no_provider_stop",
        "legacy_output_dependency",
        "source_manifest_binding",
        "exact_packet_denominator",
        "ordered_identity_denominator",
        "provider_receipt_coverage",
        "evidence_validation_failed",
        "comparison_receipts",
        "comparison_batch_receipt",
        "risk_review_incomplete",
        "sample_audit_incomplete",
        "terminal_audit_finding",
        "adjudication_candidate_partition",
        "resolution_authorization",
        "final_identity_union",
        "final_residual_zero",
        "closure_validation_failed",
    }
)

_CUSTODY_FIELDS = frozenset(
    {
        "schema_version",
        "evaluation_cycle_id",
        "source_evaluation_cycle_id",
        "amendment_reference",
        "source_custody_receipt_raw_sha256",
        "source_label_manifest_raw_sha256",
        "ordered_identity_commitment_sha256",
        "identity_union_commitment_sha256",
        "ordered_packet_commitment_sha256",
        "packet_count",
        "row_count",
        "lane_row_counts",
        "packet_size",
        "provider_artifacts_copied",
        "labels_copied",
        "responses_copied",
        "prompts_generated",
        "evidence_sidecars_generated",
        "text_free",
        "receipt_sha256",
    }
)
_MATERIALIZATION_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "evaluation_cycle_id",
        "source_evaluation_cycle_id",
        "text_free",
        "custody_receipt_raw_sha256",
        "ordered_identity_commitment_sha256",
        "identity_union_commitment_sha256",
        "ordered_packet_commitment_sha256",
        "packet_count",
        "row_count",
        "lane_row_counts",
        "packets",
        "receipt_sha256",
    }
)
_MATERIAL_PACKET_FIELDS = frozenset(
    {"lane", "packet_index", "canonical_basename", "row_count", "raw_sha256", "packet_identity_set_sha256"}
)
_PROVIDER_RECEIPT_COMMON_FIELDS = frozenset(
    {
        "schema_version",
        "evaluation_cycle_id",
        "amendment_sha256",
        "custody_receipt_raw_sha256",
        "materialization_manifest_raw_sha256",
        "evidence_manifest_raw_sha256",
        "lane",
        "packet_index",
        "row_count",
        "packet_raw_sha256",
        "packet_identity_set_sha256",
        "sidecar_raw_sha256",
        "sidecar_id",
        "raw_manifest_sha256",
        "labels_sha256",
        "exact_model",
        "model_family",
        "harness",
        "text_free",
        "receipt_sha256",
    }
)
_PROVIDER_RECEIPT_FIELDS = {
    "gemini": _PROVIDER_RECEIPT_COMMON_FIELDS | {"chunk_count"},
    "grok": _PROVIDER_RECEIPT_COMMON_FIELDS | {"response_raw_sha256", "prompt_path", "prompt_sha256", "attempt_count"},
}


def _receipt_hash(value: Mapping[str, Any]) -> str:
    return digest(canonical({key: item for key, item in value.items() if key != "receipt_sha256"}))


def _sealed_receipt(value: Mapping[str, Any], fields: frozenset[str], code: str) -> None:
    if set(value) != fields or value.get("receipt_sha256") != _receipt_hash(value):
        raise Error(code)


def _hex(value: Any) -> bool:
    return isinstance(value, str) and bool(HEX64.fullmatch(value))


def _public_fixture_hashes() -> dict[str, Any]:
    domain = "phase3-cycle007-public-canary-v1"
    rows = [
        {
            "unit_id": f"{domain}-trap",
            "unit_sha256": digest(f"{domain}:trap:слідуючий раз".encode()),
            "source_text": "слідуючий раз",
            "family_id": domain,
        },
        {
            "unit_id": f"{domain}-control",
            "unit_sha256": digest(f"{domain}:control:філіжанка".encode()),
            "source_text": "філіжанка",
            "family_id": domain,
        },
    ]
    return {
        "fixture_raw_sha256": digest(canonical(rows)),
        "row_count": 2,
        "identity_set_sha256": digest(canonical(sorted((row["unit_id"], row["unit_sha256"]) for row in rows))),
    }


_CANARY_FIELDS = frozenset(
    {
        "schema_version",
        "evaluation_cycle_id",
        "amendment_sha256",
        "ok",
        "execution_mode",
        "exact_model",
        "model_family",
        "harness",
        "provider_call_count",
        "fixture_hashes",
        "sidecar_hashes",
        "prompt_hashes",
        "code_hashes",
        "executable_sha256",
        "response_hashes",
        "sources_endpoint_identity",
        "sources_mcp_used",
        "valid_evidence_ids",
        "russian_surzhyk_trap_rejected",
        "heritage_control_preserved",
        "provenance_basis",
        "text_free",
        "receipt_sha256",
    }
)
_SOURCES_ENDPOINT_FIELDS = frozenset(
    {
        "server_code_sha256",
        "sources_db_sha256",
        "sources_db_bytes",
        "vesum_db_sha256",
        "vesum_db_bytes",
    }
)
_PREFLIGHT_FIELDS = frozenset(
    {
        "schema_version",
        "amendment_sha256",
        "package_custody_receipt_sha256",
        "package_manifest_sha256",
        "package_evidence_manifest_sha256",
        "gemini_canary_receipt_sha256",
        "grok_canary_receipt_sha256",
        "code_hashes",
        "backup_receipt_sha256",
        "review_hashes",
        "ci_proof_bindings",
        "sources_endpoint_identity",
        "text_free",
        "receipt_sha256",
    }
)


def _exact_hash_map(value: Any, fields: frozenset[str]) -> bool:
    return isinstance(value, dict) and set(value) == fields and all(_hex(item) for item in value.values())


def _valid_canary_provenance(provider: str, value: Any, response_hashes: Mapping[str, Any]) -> bool:
    if not isinstance(value, dict):
        return False
    if provider == "gemini":
        fields = {
            "init_model",
            "result_status",
            "init_conversation_id",
            "result_conversation_id",
            "challenge_sha256",
            "raw_stream_sha256",
        }
        return (
            set(value) == fields
            and isinstance(value["init_model"], str)
            and bool(value["init_model"])
            and isinstance(value["result_status"], str)
            and bool(value["result_status"])
            and all(
                value[key] is None or isinstance(value[key], str)
                for key in ("init_conversation_id", "result_conversation_id")
            )
            and _hex(value["challenge_sha256"])
            and value["raw_stream_sha256"] == response_hashes["raw_stream_sha256"]
        )
    fields = {"challenge_sha256", "response_raw_sha256"}
    return (
        set(value) == fields
        and _hex(value["challenge_sha256"])
        and value["response_raw_sha256"] == response_hashes["response_raw_sha256"]
    )


def _validate_controls(
    package: Path,
    *,
    fixture: bool,
    custody_hash: str,
    manifest_hash: str,
    evidence_hash: str,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    control = package / CONTROL_ROOT
    _directory(control)
    preflight, preflight_raw = _read_json(control / "preflight-receipt.json")
    canaries: dict[str, tuple[dict[str, Any], bytes]] = {}
    expected_sources: dict[str, Any] | None = None
    providers = (
        ("gemini", EXPECTED_MODELS["gemini"], frozenset({"raw_stream_sha256", "labels_raw_sha256"})),
        ("grok", EXPECTED_MODELS["grok"], frozenset({"response_raw_sha256", "labels_raw_sha256"})),
    )
    expected_canary_code_hashes = {
        "compiler_sha256": digest(EVIDENCE_COMPILER.read_bytes()),
        "validator_sha256": digest(CONTROL_CODE_PATHS["label_validator"].read_bytes()),
        "canary_runner_sha256": digest(CANARY_RUNNER.read_bytes()),
    }
    for provider, expected_model, response_keys in providers:
        value, raw = _read_json(control / f"{provider}-canary-receipt.json")
        endpoint = value.get("sources_endpoint_identity")
        sidecar_hashes = value.get("sidecar_hashes")
        prompt_hashes = value.get("prompt_hashes")
        response_hashes = value.get("response_hashes")
        endpoint_is_valid = (
            isinstance(endpoint, dict)
            and set(endpoint) == _SOURCES_ENDPOINT_FIELDS
            and all(_hex(endpoint.get(key)) for key in ("server_code_sha256", "sources_db_sha256", "vesum_db_sha256"))
            and all(
                isinstance(endpoint.get(key), int) and not isinstance(endpoint.get(key), bool) and endpoint[key] > 0
                for key in ("sources_db_bytes", "vesum_db_bytes")
            )
        )
        if (
            raw != canonical(value)
            or set(value) != _CANARY_FIELDS
            or value.get("schema_version") != f"phase3_cycle007_{provider}_public_canary_receipt_v1"
            or value.get("evaluation_cycle_id") != CYCLE
            or value.get("amendment_sha256") != AMENDMENT_SHA256
            or value.get("execution_mode") != ("fixture" if fixture else "real")
            or any(value.get(key) != item for key, item in expected_model.items())
            or value.get("ok") is not True
            or value.get("text_free") is not True
            or not isinstance(value.get("provider_call_count"), int)
            or isinstance(value.get("provider_call_count"), bool)
            or value["provider_call_count"] < 1
            or value.get("fixture_hashes") != _public_fixture_hashes()
            or not isinstance(sidecar_hashes, dict)
            or set(sidecar_hashes) != {"sidecar_id", "sidecar_raw_sha256"}
            or not isinstance(sidecar_hashes.get("sidecar_id"), str)
            or not sidecar_hashes["sidecar_id"].startswith("cycle007_sidecar:")
            or not _hex(sidecar_hashes.get("sidecar_raw_sha256"))
            or not _exact_hash_map(prompt_hashes, frozenset({"prompt_sha256"}))
            or value.get("code_hashes") != expected_canary_code_hashes
            or not _hex(value.get("executable_sha256"))
            or not _exact_hash_map(response_hashes, response_keys)
            or not endpoint_is_valid
            or any(
                value.get(key) is not True
                for key in (
                    "sources_mcp_used",
                    "valid_evidence_ids",
                    "russian_surzhyk_trap_rejected",
                    "heritage_control_preserved",
                )
            )
            or not _valid_canary_provenance(provider, value.get("provenance_basis"), response_hashes)
            or value.get("receipt_sha256") != _receipt_hash(value)
        ):
            raise Error("closure_validation_failed")
        if expected_sources is None:
            expected_sources = endpoint
        if endpoint != expected_sources:
            raise Error("closure_validation_failed")
        canaries[provider] = (value, raw)
    assert expected_sources is not None
    if any(
        evidence.get(key) != expected_sources[key]
        for key in ("server_code_sha256", "sources_db_sha256", "vesum_db_sha256")
    ):
        raise Error("evidence_validation_failed")
    code_hashes = {key: digest(path.read_bytes()) for key, path in CONTROL_CODE_PATHS.items()}
    if (
        preflight_raw != canonical(preflight)
        or set(preflight) != _PREFLIGHT_FIELDS
        or preflight.get("schema_version") != "phase3_cycle007_preflight_receipt_v1"
        or preflight.get("amendment_sha256") != AMENDMENT_SHA256
        or preflight.get("package_custody_receipt_sha256") != custody_hash
        or preflight.get("package_manifest_sha256") != manifest_hash
        or preflight.get("package_evidence_manifest_sha256") != evidence_hash
        or preflight.get("gemini_canary_receipt_sha256") != digest(canaries["gemini"][1])
        or preflight.get("grok_canary_receipt_sha256") != digest(canaries["grok"][1])
        or preflight.get("code_hashes") != code_hashes
        or not _hex(preflight.get("backup_receipt_sha256"))
        or not isinstance(preflight.get("review_hashes"), dict)
        or not preflight["review_hashes"]
        or not all(isinstance(key, str) and key and _hex(item) for key, item in preflight["review_hashes"].items())
        or not isinstance(preflight.get("ci_proof_bindings"), dict)
        or not preflight["ci_proof_bindings"]
        or not all(isinstance(key, str) and key and _hex(item) for key, item in preflight["ci_proof_bindings"].items())
        or preflight.get("sources_endpoint_identity") != expected_sources
        or preflight.get("text_free") is not True
        or preflight.get("receipt_sha256") != _receipt_hash(preflight)
    ):
        raise Error("closure_validation_failed")
    preflight_hash = digest(preflight_raw)
    seals = {}
    for stage in ("gemini", "grok", "compare", "audit", "adjudicate", "resolve"):
        seal, raw = _read_json(control / f"stage-{stage}.complete.json")
        expected = {
            "schema_version": "phase3_cycle007_stage_complete_v1",
            "evaluation_cycle_id": CYCLE,
            "stage": stage,
            "preflight_receipt_sha256": preflight_hash,
            "text_free": True,
        }
        if raw != canonical(seal) or seal != expected:
            raise Error("closure_validation_failed")
        seals[stage] = digest(raw)
    certify_seal = {
        "schema_version": "phase3_cycle007_stage_complete_v1",
        "evaluation_cycle_id": CYCLE,
        "stage": "certify",
        "preflight_receipt_sha256": preflight_hash,
        "text_free": True,
    }
    certify_expected = digest(canonical(certify_seal))
    certify_path = control / "stage-certify.complete.json"
    if certify_path.exists():
        seal, raw = _read_json(certify_path)
        if raw != canonical(seal) or seal != certify_seal:
            raise Error("closure_validation_failed")
    return {
        "preflight_receipt_sha256": preflight_hash,
        "gemini_canary_receipt_sha256": digest(canaries["gemini"][1]),
        "grok_canary_receipt_sha256": digest(canaries["grok"][1]),
        "sources_endpoint_identity_sha256": digest(canonical(expected_sources)),
        "stage_seal_hashes": seals,
        "expected_certify_stage_seal_sha256": certify_expected,
        "sources_endpoint_identity": expected_sources,
    }


class Error(ValueError):
    def __init__(self, code: str):
        self.code = code if code in FAILURE_CODES else "closure_validation_failed"
        self.failure_code = self.code
        super().__init__(self.code)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise Error("closure_validation_failed")
        value[key] = item
    return value


def _regular(path: Path, mode: int = 0o600) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise Error("closure_validation_failed") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != mode:
        raise Error("package_modes")


def _directory(path: Path, mode: int = 0o700) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise Error("closure_validation_failed") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != mode:
        raise Error("package_modes")


def _read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    _regular(path)
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Error) as exc:
        raise Error("closure_validation_failed") from exc
    if not isinstance(value, dict):
        raise Error("closure_validation_failed")
    return value, raw


def _atomic(path: Path, value: dict[str, Any]) -> str:
    data = canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists() or path.is_symlink():
        _regular(path)
        if path.read_bytes() != data:
            raise Error("closure_validation_failed")
        return digest(data)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        os.chmod(path, 0o600)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return digest(data)


def _walk_modes(package: Path) -> None:
    _directory(package)
    for path in (package, *package.rglob("*")):
        if path.is_symlink():
            raise Error("package_modes")
        if path.is_dir():
            if stat.S_IMODE(path.stat().st_mode) != 0o700:
                raise Error("package_modes")
        elif path.is_file():
            if stat.S_IMODE(path.stat().st_mode) != 0o600:
                raise Error("package_modes")
        else:
            raise Error("package_modes")


def _no_temp_dirs(package: Path) -> None:
    for path in package.rglob("*"):
        if path.is_dir() and (path.name.startswith(".cycle007-") or path.name.startswith(".packet-")):
            raise Error("no_temp_dirs")


def _package_roots(package: Path) -> None:
    legacy = {
        "label-output",
        "label-output-gemini-v2",
        "dual-label-output",
        "label-output-grok-cycle006-v1",
        "label-output-gemini-cycle006-v1",
        "dual-label-adjudication-cycle006-v1",
        "dual-label-final-cycle006-v1",
        "label-output-grok-cycle006-v2",
        "label-output-gemini-cycle006-v2",
        "dual-label-output-cycle006-v2",
        "dual-label-adjudication-cycle006-v2",
        "dual-label-final-cycle006-v2",
    }
    if any((package / name).exists() or (package / name).is_symlink() for name in legacy):
        raise Error("legacy_output_dependency")
    stop_roots = (GROK_ROOT, GEMINI_ROOT, COMPARE_ROOT, AUDIT_ROOT, ADJUDICATION_ROOT, RESOLUTION_ROOT)
    for root in stop_roots:
        if (package / root / "provider-stop.json").exists() or (package / root / "stop.json").exists():
            raise Error("no_provider_stop")


def validate_label(
    lane: str,
    label: dict[str, Any],
    row: dict[str, Any],
    row_evidence: Mapping[str, Any] | None = None,
) -> None:
    if (label.get("unit_id"), label.get("unit_sha256")) != (row.get("unit_id"), row.get("unit_sha256")):
        raise Error("final_identity_union")
    if lane == "clean_label":
        if (
            not isinstance(label, dict)
            or set(label)
            != {
                "unit_id",
                "unit_sha256",
                "decision_code",
                "clean_modern_standard_prose",
                "modern_genre_id",
                "evidence_ids",
            }
            or label.get("decision_code") not in REJECTS
            or type(label.get("clean_modern_standard_prose")) is not bool
            or not isinstance(label.get("evidence_ids"), list)
        ):
            raise Error("final_identity_union")
        agrees = label["decision_code"] == "agree"
        if (
            agrees != label["clean_modern_standard_prose"]
            or (agrees and label["modern_genre_id"] not in GENRES)
            or (not agrees and label["modern_genre_id"] is not None)
        ):
            raise Error("final_identity_union")
        evidence_ids = label["evidence_ids"]
        if evidence_ids != sorted(set(evidence_ids)):
            raise Error("final_identity_union")
        if row_evidence is not None:
            available = set(row_evidence.get("evidence_ids", []))
            if set(evidence_ids) - available:
                raise Error("final_identity_union")
            if agrees:
                try:
                    validator.validate_label_evidence_refs(
                        row_evidence,
                        decision_code="agree",
                        evidence_ids=evidence_ids,
                        phenomenon_id=None,
                    )
                except validator.EvidenceValidationError as exc:
                    raise Error("final_identity_union") from exc
            elif label["decision_code"] in validator.KNOWN_DECISIONS:
                try:
                    validator.validate_label_evidence_refs(
                        row_evidence,
                        decision_code=label["decision_code"],
                        evidence_ids=evidence_ids,
                        phenomenon_id=None,
                    )
                except validator.EvidenceValidationError as exc:
                    raise Error("final_identity_union") from exc
    elif lane == "residual_label":
        if (
            not isinstance(label, dict)
            or set(label) != {"unit_id", "unit_sha256", "phenomena", "primary_phenomenon_id", "item_decision_rollup"}
            or not isinstance(label.get("phenomena"), list)
            or not label["phenomena"]
            or label.get("item_decision_rollup") not in DEC
        ):
            raise Error("final_identity_union")
        names: list[str] = []
        decisions: dict[str, str] = {}
        for p in label["phenomena"]:
            if (
                not isinstance(p, dict)
                or set(p) != {"phenomenon_id", "decision_code", "evidence_sufficiency", "evidence_ids"}
                or p.get("phenomenon_id") not in TAX
                or p.get("decision_code") not in DEC
                or p.get("evidence_sufficiency") not in {"sufficient", "insufficient"}
                or not isinstance(p.get("evidence_ids"), list)
            ):
                raise Error("final_identity_union")
            if (
                p["decision_code"] in {"positive", "acceptable_control", "protected"}
                and p["evidence_sufficiency"] != "sufficient"
            ):
                raise Error("final_identity_union")
            if row.get("family_id") == "pravopys_2019_complete" and p["decision_code"] == "positive":
                raise Error("final_identity_union")
            p_ids = p["evidence_ids"]
            if p_ids != sorted(set(p_ids)):
                raise Error("final_identity_union")
            if row_evidence is not None:
                try:
                    validator.validate_label_evidence_refs(
                        row_evidence,
                        decision_code=p["decision_code"],
                        evidence_ids=p_ids,
                        phenomenon_id=p["phenomenon_id"],
                    )
                except validator.EvidenceValidationError as exc:
                    raise Error("final_identity_union") from exc
            names.append(p["phenomenon_id"])
            decisions[p["phenomenon_id"]] = p["decision_code"]

        if len(names) != len(set(names)) or names != sorted(names, key=TAX.index):
            raise Error("final_identity_union")
        viable = [name for name in names if decisions[name] not in {"abstention", "disagreement"}]
        primary = label["primary_phenomenon_id"]
        if viable and (primary not in viable or label["item_decision_rollup"] != decisions[primary]):
            raise Error("final_identity_union")
        if not viable and (
            primary is not None
            or label["item_decision_rollup"]
            != ("disagreement" if "disagreement" in decisions.values() else "abstention")
        ):
            raise Error("final_identity_union")
    else:
        raise Error("final_identity_union")


def is_risk_triggered(
    row: dict[str, Any],
    row_evidence: Mapping[str, Any],
    grok_label: dict[str, Any],
    gemini_label: dict[str, Any],
) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    is_neg = (
        row.get("is_negative_control") is True
        or row.get("negative_control") is True
        or row.get("is_russianism_control") is True
        or row.get("is_surzhyk_control") is True
        or row.get("is_source_conflict_control") is True
        or row.get("control_type") in {"russianism", "surzhyk", "source_conflict"}
        or row.get("negative_control_type") is not None
        or row.get("family_id") in {"russianism", "surzhyk", "source_conflict", "synthetic_control", "negative_control"}
        or bool(set(row.get("tags") or []) & {"russianism", "surzhyk", "negative_control", "source_conflict"})
    )
    if is_neg:
        reasons.append("negative_control")

    evidence_records: list[dict[str, Any]] = list(row_evidence.get("evidence", []))

    for record in evidence_records:
        if (
            record.get("channel") == "vesum_attestation"
            and record.get("status") == "not_found"
            and "vesum_miss" not in reasons
        ):
            reasons.append("vesum_miss")
        if record.get("supports") == "archaic_attestation" and "archaic_only_form" not in reasons:
            reasons.append("archaic_only_form")
    if (
        row_evidence.get("has_only_archaic_form") is True or row.get("has_only_archaic_form") is True
    ) and "archaic_only_form" not in reasons:
        reasons.append("archaic_only_form")

    for record in evidence_records:
        ch = record.get("channel")
        st = record.get("status")
        if ch == "ua_gec_calque" and st == "attested" and "ua_gec_warning" not in reasons:
            reasons.append("ua_gec_warning")
        elif ch == "russian_shadow_suspicion" and st == "attested" and "russian_shadow_warning" not in reasons:
            reasons.append("russian_shadow_warning")
        elif ch == "antonenko_style" and st == "attested" and "style_guide_warning" not in reasons:
            reasons.append("style_guide_warning")

    for record in evidence_records:
        ch = record.get("channel")
        st = record.get("status")
        if (
            st in {"ambiguous", "incomplete", "parse_error", "unavailable"}
            and "unresolved_source_result" not in reasons
        ):
            reasons.append("unresolved_source_result")
        if (
            ch == "heritage_attestation"
            and st in {"ambiguous", "incomplete", "parse_error", "unavailable"}
            and "heritage_source_conflict" not in reasons
        ):
            reasons.append("heritage_source_conflict")

    if "phenomena" in grok_label:
        pravopys_records = [r for r in evidence_records if r.get("channel") == "pravopys_2026_normative"]
        if (
            not pravopys_records
            or any(r.get("status") != "attested" or r.get("supports") == "no_conclusion" for r in pravopys_records)
        ) and "missing_normative_rule" not in reasons:
            reasons.append("missing_normative_rule")

    if (
        grok_label.get("decision_code") == "agree"
        and validator.classify_sufficiency(row_evidence) != "sufficient"
        and "insufficient_evidence_cited" not in reasons
    ):
        reasons.append("insufficient_evidence_cited")
    if "phenomena" in grok_label:
        for p in grok_label.get("phenomena", []):
            if (
                p.get("decision_code") in {"positive", "acceptable_control", "protected"}
                and validator.classify_sufficiency(row_evidence, phenomenon_id=p.get("phenomenon_id")) != "sufficient"
                and "insufficient_evidence_cited" not in reasons
            ):
                reasons.append("insufficient_evidence_cited")

    return bool(reasons), sorted(reasons)


def compute_zero_event_bound(population_count: int) -> float:
    if population_count <= 0:
        return 0.0
    return 1.0 - (0.05 ** (1.0 / population_count))


def _reviewer_is_source_qualified(reviewer: Any) -> bool:
    if (
        not isinstance(reviewer, dict)
        or not isinstance(reviewer.get("exact_model"), str)
        or not reviewer["exact_model"]
    ):
        return False
    if reviewer.get("model_family") == "anthropic":
        return set(reviewer) == {"exact_model", "model_family", "harness"} and isinstance(reviewer.get("harness"), str)
    return (
        set(reviewer) == {"exact_model", "model_family", "harness", "source_qualified"}
        and reviewer.get("model_family") == "human"
        and reviewer.get("harness") == "local-operator"
        and reviewer.get("source_qualified") is True
    )


def _validate_live_audit(
    package: Path,
    *,
    custody_hash: str,
    manifest_hash: str,
    manifest: Mapping[str, Any],
    expected_commitment: str,
    ev_manifest_raw: bytes,
    expected_identity: Mapping[str, Any],
    sidecar_by_uid: Mapping[tuple[str, str], Mapping[str, Any]],
    clean_records: list[dict[str, Any]],
    risk_records: list[dict[str, Any]],
    sample_records: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Validate the sealed, bounded source-review audit without reading provider text."""
    audit_dir = package / AUDIT_ROOT
    sample_doc, _ = _read_json(audit_dir / "clean-consensus-sample.json")
    sampler_seal, sampler_seal_raw = _read_json(audit_dir / "clean-consensus-sampler-seal.json")
    sampler_receipt, _ = _read_json(audit_dir / "clean-consensus-sampler-seal-receipt.json")
    plan, plan_raw = _read_json(audit_dir / "source-review-plan.json")
    plan_receipt, _ = _read_json(audit_dir / "source-review-plan-receipt.json")
    review_results, review_results_raw = _read_json(audit_dir / "source-review-results.json")
    review_receipt, _ = _read_json(audit_dir / "source-review-receipt.json")
    risk_receipt, _ = _read_json(audit_dir / "risk-review-receipt.json")
    clean_receipt, _ = _read_json(audit_dir / "clean-audit-receipt.json")
    audit_batch, _ = _read_json(audit_dir / "batch-receipt.json")

    seed = digest(
        f"phase3-cycle007-consensus-audit-v1\n{SOURCE_CUSTODY_SHA256}{SOURCE_MANIFEST_SHA256}{expected_commitment}".encode()
    )
    ranked_clean = []
    for record in clean_records:
        copy = dict(record)
        row = copy["source_row"]
        copy["rank"] = digest(f"{seed}{copy['lane']}{row['unit_id']}{row['unit_sha256']}".encode())
        ranked_clean.append(copy)
    strata: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in ranked_clean:
        if record["lane"] == "clean_label":
            strata[f"clean:{record['label'].get('decision_code', 'unknown')}"].append(record)
        else:
            for phenomenon in record["label"].get("phenomena", []):
                strata[
                    f"residual:{phenomenon.get('phenomenon_id', 'unknown')}:{phenomenon.get('decision_code', 'unknown')}"
                ].append(record)
    chosen: dict[tuple[str, str], dict[str, Any]] = {}
    for members in strata.values():
        for record in sorted(members, key=lambda item: item["rank"])[:10]:
            row = record["source_row"]
            chosen.setdefault((row["unit_id"], row["unit_sha256"]), record)
    mandatory = list(chosen.values())
    if len(ranked_clean) <= 600:
        expected_sample = sorted(ranked_clean, key=lambda item: item["rank"])
    elif len(mandatory) >= 600:
        expected_sample = mandatory
    else:
        expected_sample = (
            mandatory
            + sorted(
                (
                    record
                    for record in ranked_clean
                    if (record["source_row"]["unit_id"], record["source_row"]["unit_sha256"]) not in chosen
                ),
                key=lambda item: item["rank"],
            )[: 600 - len(mandatory)]
        )
    expected_sample = sorted(
        expected_sample,
        key=lambda item: (item["lane"], item["source_row"]["unit_id"], item["source_row"]["unit_sha256"]),
    )
    sample_identities = [(item["source_row"]["unit_id"], item["source_row"]["unit_sha256"]) for item in expected_sample]
    sample_fields = {
        "schema_version",
        "evaluation_cycle_id",
        "amendment_sha256",
        "custody_receipt_raw_sha256",
        "source_label_manifest_raw_sha256",
        "manifest_raw_sha256",
        "ordered_identity_commitment_sha256",
        "population_count",
        "audited_count",
        "one_sided_95_bound",
        "seed",
        "seed_source_custody_sha256",
        "seed_source_manifest_sha256",
        "strata_counts",
        "sample_identity_commitment_sha256",
        "text_free",
        "receipt_sha256",
    }
    if (
        set(sample_doc) != sample_fields
        or sample_doc.get("schema_version") != "phase3_cycle007_clean_consensus_sample_receipt_v1"
        or sample_doc.get("evaluation_cycle_id") != CYCLE
        or sample_doc.get("amendment_sha256") != AMENDMENT_SHA256
        or sample_doc.get("custody_receipt_raw_sha256") != custody_hash
        or sample_doc.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or sample_doc.get("manifest_raw_sha256") != manifest_hash
        or sample_doc.get("ordered_identity_commitment_sha256") != expected_commitment
        or sample_doc.get("seed") != seed
        or sample_doc.get("seed_source_custody_sha256") != SOURCE_CUSTODY_SHA256
        or sample_doc.get("seed_source_manifest_sha256") != SOURCE_MANIFEST_SHA256
        or sample_doc.get("population_count") != len(ranked_clean)
        or sample_doc.get("audited_count") != len(expected_sample)
        or sample_doc.get("one_sided_95_bound") != compute_zero_event_bound(len(expected_sample))
        or sample_doc.get("strata_counts") != {key: len(value) for key, value in sorted(strata.items())}
        or sample_doc.get("sample_identity_commitment_sha256") != digest(canonical(sample_identities))
        or sample_doc.get("text_free") is not True
        or sample_doc.get("receipt_sha256") != _receipt_hash(sample_doc)
    ):
        raise Error("sample_audit_incomplete")

    clean_seal = [
        {
            "lane": item["lane"],
            "packet_index": item["packet_index"],
            "unit_id": item["source_row"]["unit_id"],
            "unit_sha256": item["source_row"]["unit_sha256"],
            "rank": item["rank"],
            "strata": (
                [f"clean:{item['label'].get('decision_code', 'unknown')}"]
                if item["lane"] == "clean_label"
                else [
                    f"residual:{p.get('phenomenon_id', 'unknown')}:{p.get('decision_code', 'unknown')}"
                    for p in item["label"].get("phenomena", [])
                ]
            ),
        }
        for item in ranked_clean
    ]
    risk_seal = [
        [item["lane"], item["packet_index"], item["source_row"]["unit_id"], item["source_row"]["unit_sha256"]]
        for item in risk_records
    ]
    selected_seal = [
        [item["lane"], item["packet_index"], item["source_row"]["unit_id"], item["source_row"]["unit_sha256"]]
        for item in expected_sample
    ]
    if (
        set(sampler_seal)
        != {
            "schema_version",
            "evaluation_cycle_id",
            "sample_receipt_sha256",
            "clean_population",
            "risk_exclusions",
            "selected_identities",
        }
        or sampler_seal
        != {
            "schema_version": "phase3_cycle007_clean_consensus_sampler_seal_v1",
            "evaluation_cycle_id": CYCLE,
            "sample_receipt_sha256": sample_doc["receipt_sha256"],
            "clean_population": clean_seal,
            "risk_exclusions": risk_seal,
            "selected_identities": selected_seal,
        }
        or set(sampler_receipt)
        != {
            "schema_version",
            "evaluation_cycle_id",
            "amendment_sha256",
            "clean_population_count",
            "risk_exclusion_count",
            "selected_count",
            "clean_population_identity_commitment_sha256",
            "risk_exclusion_identity_commitment_sha256",
            "rank_and_strata_commitment_sha256",
            "selected_identity_commitment_sha256",
            "private_sampler_seal_sha256",
            "sample_receipt_sha256",
            "text_free",
            "receipt_sha256",
        }
        or sampler_receipt.get("schema_version") != "phase3_cycle007_clean_consensus_sampler_seal_receipt_v1"
        or sampler_receipt.get("evaluation_cycle_id") != CYCLE
        or sampler_receipt.get("amendment_sha256") != AMENDMENT_SHA256
        or sampler_receipt.get("clean_population_count") != len(clean_seal)
        or sampler_receipt.get("risk_exclusion_count") != len(risk_seal)
        or sampler_receipt.get("selected_count") != len(selected_seal)
        or sampler_receipt.get("clean_population_identity_commitment_sha256")
        != digest(
            canonical(
                [(item["lane"], item["packet_index"], item["unit_id"], item["unit_sha256"]) for item in clean_seal]
            )
        )
        or sampler_receipt.get("risk_exclusion_identity_commitment_sha256") != digest(canonical(risk_seal))
        or sampler_receipt.get("rank_and_strata_commitment_sha256")
        != digest(
            canonical(
                [
                    (
                        item["lane"],
                        item["packet_index"],
                        item["unit_id"],
                        item["unit_sha256"],
                        item["rank"],
                        item["strata"],
                    )
                    for item in clean_seal
                ]
            )
        )
        or sampler_receipt.get("selected_identity_commitment_sha256") != digest(canonical(selected_seal))
        or sampler_receipt.get("private_sampler_seal_sha256") != digest(sampler_seal_raw)
        or sampler_receipt.get("sample_receipt_sha256") != sample_doc["receipt_sha256"]
        or sampler_receipt.get("text_free") is not True
        or sampler_receipt.get("receipt_sha256") != _receipt_hash(sampler_receipt)
    ):
        raise Error("sample_audit_incomplete")

    targets = []
    for scope, records in (("risk", risk_records), ("clean_sample", expected_sample)):
        for item in records:
            row = item["source_row"]
            evidence = sidecar_by_uid.get((row["unit_id"], row["unit_sha256"]))
            if evidence is None:
                raise Error("sample_audit_incomplete")
            targets.append(
                {
                    "scope": scope,
                    "lane": item["lane"],
                    "packet_index": item["packet_index"],
                    "source_row": row,
                    "label": item["label"],
                    "row_evidence": evidence,
                    "source_evidence_sha256": digest(canonical(evidence)),
                }
            )
    if len(
        {
            (item["lane"], item["packet_index"], item["source_row"]["unit_id"], item["source_row"]["unit_sha256"])
            for item in targets
        }
    ) != len(targets):
        raise Error("sample_audit_incomplete")
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for target in targets:
        grouped[(target["lane"], target["packet_index"])].append(target)
    batches = []
    for number, ((lane, index), members) in enumerate(sorted(grouped.items()), 1):
        ordered = sorted(
            members, key=lambda item: (item["scope"], item["source_row"]["unit_id"], item["source_row"]["unit_sha256"])
        )
        identities = [
            (item["lane"], item["packet_index"], item["source_row"]["unit_id"], item["source_row"]["unit_sha256"])
            for item in ordered
        ]
        batches.append(
            {
                "batch_index": number,
                "lane": lane,
                "packet_index": index,
                "target_count": len(ordered),
                "identity_commitment_sha256": digest(canonical(identities)),
                "targets": ordered,
            }
        )
    descriptors = [
        {
            key: batch[key]
            for key in ("batch_index", "lane", "packet_index", "target_count", "identity_commitment_sha256")
        }
        for batch in batches
    ]
    target_identity = digest(
        canonical(
            [
                (item["lane"], item["packet_index"], item["source_row"]["unit_id"], item["source_row"]["unit_sha256"])
                for item in targets
            ]
        )
    )
    identity_hash = digest(canonical(expected_identity))
    if (
        set(plan)
        != {
            "schema_version",
            "evaluation_cycle_id",
            "amendment_sha256",
            "sample_receipt_sha256",
            "risk_target_count",
            "clean_sample_target_count",
            "target_identity_commitment_sha256",
            "evidence_manifest_raw_sha256",
            "sources_identity_commitment_sha256",
            "batches",
            "targets",
        }
        or plan
        != {
            "schema_version": "phase3_cycle007_consensus_source_review_plan_v1",
            "evaluation_cycle_id": CYCLE,
            "amendment_sha256": AMENDMENT_SHA256,
            "sample_receipt_sha256": sample_doc["receipt_sha256"],
            "risk_target_count": len(risk_records),
            "clean_sample_target_count": len(expected_sample),
            "target_identity_commitment_sha256": target_identity,
            "evidence_manifest_raw_sha256": digest(ev_manifest_raw),
            "sources_identity_commitment_sha256": identity_hash,
            "batches": descriptors,
            "targets": targets,
        }
        or set(plan_receipt)
        != {
            "schema_version",
            "evaluation_cycle_id",
            "amendment_sha256",
            "risk_target_count",
            "clean_sample_target_count",
            "target_identity_commitment_sha256",
            "review_batch_count",
            "review_batch_union_commitment_sha256",
            "evidence_manifest_raw_sha256",
            "sources_identity_commitment_sha256",
            "source_review_plan_sha256",
            "sample_receipt_sha256",
            "text_free",
            "receipt_sha256",
        }
        or plan_receipt.get("schema_version") != "phase3_cycle007_consensus_source_review_plan_receipt_v1"
        or plan_receipt.get("evaluation_cycle_id") != CYCLE
        or plan_receipt.get("amendment_sha256") != AMENDMENT_SHA256
        or plan_receipt.get("risk_target_count") != len(risk_records)
        or plan_receipt.get("clean_sample_target_count") != len(expected_sample)
        or plan_receipt.get("target_identity_commitment_sha256") != target_identity
        or plan_receipt.get("review_batch_count") != len(batches)
        or plan_receipt.get("review_batch_union_commitment_sha256")
        != digest(canonical([batch["identity_commitment_sha256"] for batch in batches]))
        or plan_receipt.get("evidence_manifest_raw_sha256") != digest(ev_manifest_raw)
        or plan_receipt.get("sources_identity_commitment_sha256") != identity_hash
        or plan_receipt.get("source_review_plan_sha256") != digest(plan_raw)
        or plan_receipt.get("sample_receipt_sha256") != sample_doc["receipt_sha256"]
        or plan_receipt.get("text_free") is not True
        or plan_receipt.get("receipt_sha256") != _receipt_hash(plan_receipt)
    ):
        raise Error("sample_audit_incomplete")

    if set(review_results) != {"reviews"} or not isinstance(review_results["reviews"], list):
        raise Error("sample_audit_incomplete")
    expected_reviews = []
    for batch in batches:
        expected_reviews.extend(batch["targets"])
    review_identities = []
    for review, target in zip(review_results["reviews"], expected_reviews, strict=False):
        if not isinstance(review, dict) or set(review) != {
            "lane",
            "packet_index",
            "unit_id",
            "unit_sha256",
            "source_evidence_sha256",
            "outcome",
        }:
            raise Error("sample_audit_incomplete")
        actual = (
            review["lane"],
            review["packet_index"],
            review["unit_id"],
            review["unit_sha256"],
            review["source_evidence_sha256"],
        )
        expected = (
            target["lane"],
            target["packet_index"],
            target["source_row"]["unit_id"],
            target["source_row"]["unit_sha256"],
            target["source_evidence_sha256"],
        )
        if actual != expected or review.get("outcome") != "pass":
            raise Error("terminal_audit_finding")
        review_identities.append(actual)
    if len(review_results["reviews"]) != len(expected_reviews) or len(set(review_identities)) != len(expected_reviews):
        raise Error("sample_audit_incomplete")
    if (
        set(review_receipt)
        != {
            "schema_version",
            "evaluation_cycle_id",
            "amendment_sha256",
            "source_review_plan_sha256",
            "target_identity_commitment_sha256",
            "reviewed_count",
            "review_result_sha256",
            "review_input_sha256",
            "reviewer",
            "attempt_count",
            "review_batch_count",
            "review_batch_receipt_union_sha256",
            "evidence_manifest_raw_sha256",
            "sources_identity_commitment_sha256",
            "terminal_findings_count",
            "text_free",
            "receipt_sha256",
        }
        or review_receipt.get("schema_version") != "phase3_cycle007_consensus_source_review_receipt_v1"
        or review_receipt.get("evaluation_cycle_id") != CYCLE
        or review_receipt.get("amendment_sha256") != AMENDMENT_SHA256
        or review_receipt.get("source_review_plan_sha256") != digest(plan_raw)
        or review_receipt.get("target_identity_commitment_sha256") != target_identity
        or review_receipt.get("reviewed_count") != len(expected_reviews)
        or review_receipt.get("review_result_sha256") != digest(review_results_raw)
        or not _hex(review_receipt.get("review_input_sha256"))
        or not _reviewer_is_source_qualified(review_receipt.get("reviewer"))
        or not isinstance(review_receipt.get("attempt_count"), int)
        or review_receipt.get("review_batch_count") != len(batches)
        or review_receipt.get("evidence_manifest_raw_sha256") != digest(ev_manifest_raw)
        or review_receipt.get("sources_identity_commitment_sha256") != identity_hash
        or review_receipt.get("terminal_findings_count") != 0
        or review_receipt.get("text_free") is not True
        or review_receipt.get("receipt_sha256") != _receipt_hash(review_receipt)
    ):
        raise Error("terminal_audit_finding")
    batch_hashes = []
    for batch in batches:
        result, result_raw = _read_json(audit_dir / f"source-review-results-batch-{batch['batch_index']:04d}.json")
        receipt, _ = _read_json(audit_dir / f"source-review-batch-receipt-{batch['batch_index']:04d}.json")
        prior_batches = len(batch_hashes)
        start = sum(item["target_count"] for item in batches[:prior_batches])
        end = sum(item["target_count"] for item in batches[: prior_batches + 1])
        expected_batch_reviews = review_results["reviews"][start:end]
        if (
            result != {"reviews": expected_batch_reviews}
            or set(receipt)
            != {
                "schema_version",
                "evaluation_cycle_id",
                "amendment_sha256",
                "source_review_plan_sha256",
                "batch_index",
                "lane",
                "packet_index",
                "identity_commitment_sha256",
                "reviewed_count",
                "review_result_sha256",
                "review_input_sha256",
                "evidence_manifest_raw_sha256",
                "sources_identity_commitment_sha256",
                "reviewer",
                "attempt_count",
                "terminal_findings_count",
                "text_free",
                "receipt_sha256",
            }
            or receipt.get("schema_version") != "phase3_cycle007_consensus_source_review_batch_receipt_v1"
            or receipt.get("evaluation_cycle_id") != CYCLE
            or receipt.get("amendment_sha256") != AMENDMENT_SHA256
            or receipt.get("source_review_plan_sha256") != digest(plan_raw)
            or receipt.get("batch_index") != batch["batch_index"]
            or receipt.get("lane") != batch["lane"]
            or receipt.get("packet_index") != batch["packet_index"]
            or receipt.get("identity_commitment_sha256") != batch["identity_commitment_sha256"]
            or receipt.get("reviewed_count") != batch["target_count"]
            or receipt.get("review_result_sha256") != digest(result_raw)
            or not _hex(receipt.get("review_input_sha256"))
            or receipt.get("reviewer") != review_receipt["reviewer"]
            or not isinstance(receipt.get("attempt_count"), int)
            or receipt.get("evidence_manifest_raw_sha256") != digest(ev_manifest_raw)
            or receipt.get("sources_identity_commitment_sha256") != identity_hash
            or receipt.get("terminal_findings_count") != 0
            or receipt.get("text_free") is not True
            or receipt.get("receipt_sha256") != _receipt_hash(receipt)
        ):
            raise Error("sample_audit_incomplete")
        batch_hashes.append(receipt["receipt_sha256"])
    if review_receipt.get("review_batch_receipt_union_sha256") != digest(canonical(batch_hashes)):
        raise Error("sample_audit_incomplete")
    audit_receipt_common = {
        "schema_version",
        "evaluation_cycle_id",
        "amendment_sha256",
        "custody_receipt_raw_sha256",
        "source_label_manifest_raw_sha256",
        "manifest_raw_sha256",
        "ordered_identity_commitment_sha256",
        "source_review_receipt_sha256",
        "reviewer",
        "terminal_findings_count",
        "text_free",
        "receipt_sha256",
    }
    audit_receipt_shapes = (
        (
            risk_receipt,
            "phase3_cycle007_risk_review_receipt_v1",
            "risk_population_count",
            len(risk_records),
            audit_receipt_common | {"risk_population_count", "reviewed_count"},
        ),
        (
            clean_receipt,
            "phase3_cycle007_clean_audit_receipt_v1",
            "clean_population_count",
            len(ranked_clean),
            audit_receipt_common | {"clean_population_count", "audited_count", "one_sided_95_bound"},
        ),
    )
    for receipt, schema, count_field, count, fields in audit_receipt_shapes:
        if (
            set(receipt) != fields
            or receipt.get("schema_version") != schema
            or receipt.get("evaluation_cycle_id") != CYCLE
            or receipt.get("amendment_sha256") != AMENDMENT_SHA256
            or receipt.get("custody_receipt_raw_sha256") != custody_hash
            or receipt.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
            or receipt.get("manifest_raw_sha256") != manifest_hash
            or receipt.get("ordered_identity_commitment_sha256") != expected_commitment
            or receipt.get(count_field) != count
            or receipt.get("source_review_receipt_sha256") != review_receipt["receipt_sha256"]
            or receipt.get("reviewer") != review_receipt["reviewer"]
            or receipt.get("terminal_findings_count") != 0
            or receipt.get("text_free") is not True
            or receipt.get("receipt_sha256") != _receipt_hash(receipt)
        ):
            raise Error("risk_review_incomplete" if receipt is risk_receipt else "sample_audit_incomplete")
    if risk_receipt.get("reviewed_count") != len(risk_records):
        raise Error("risk_review_incomplete")
    if (
        clean_receipt.get("audited_count") != len(expected_sample)
        or clean_receipt.get("one_sided_95_bound") != sample_doc["one_sided_95_bound"]
    ):
        raise Error("sample_audit_incomplete")
    if (
        set(audit_batch)
        != {
            "schema_version",
            "evaluation_cycle_id",
            "amendment_sha256",
            "custody_receipt_raw_sha256",
            "source_label_manifest_raw_sha256",
            "manifest_raw_sha256",
            "ordered_identity_commitment_sha256",
            "risk_population_count",
            "risk_reviewed_count",
            "clean_population_count",
            "clean_audited_count",
            "one_sided_95_bound",
            "sample_receipt_sha256",
            "sampler_seal_receipt_sha256",
            "source_review_plan_receipt_sha256",
            "source_review_receipt_sha256",
            "reviewer",
            "terminal_findings_count",
            "passed",
            "text_free",
            "receipt_sha256",
        }
        or audit_batch.get("schema_version") != "phase3_cycle007_consensus_audit_batch_receipt_v1"
        or audit_batch.get("evaluation_cycle_id") != CYCLE
        or audit_batch.get("amendment_sha256") != AMENDMENT_SHA256
        or audit_batch.get("custody_receipt_raw_sha256") != custody_hash
        or audit_batch.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or audit_batch.get("manifest_raw_sha256") != manifest_hash
        or audit_batch.get("ordered_identity_commitment_sha256") != expected_commitment
        or audit_batch.get("risk_population_count") != len(risk_records)
        or audit_batch.get("risk_reviewed_count") != len(risk_records)
        or audit_batch.get("clean_population_count") != len(ranked_clean)
        or audit_batch.get("clean_audited_count") != len(expected_sample)
        or audit_batch.get("one_sided_95_bound") != sample_doc["one_sided_95_bound"]
        or audit_batch.get("sample_receipt_sha256") != sample_doc["receipt_sha256"]
        or audit_batch.get("sampler_seal_receipt_sha256") != sampler_receipt["receipt_sha256"]
        or audit_batch.get("source_review_plan_receipt_sha256") != plan_receipt["receipt_sha256"]
        or audit_batch.get("source_review_receipt_sha256") != review_receipt["receipt_sha256"]
        or audit_batch.get("reviewer") != review_receipt["reviewer"]
        or audit_batch.get("terminal_findings_count") != 0
        or audit_batch.get("passed") is not True
        or audit_batch.get("text_free") is not True
        or audit_batch.get("receipt_sha256") != _receipt_hash(audit_batch)
    ):
        raise Error("terminal_audit_finding")
    return sample_doc, risk_receipt, clean_receipt


def certify_completion(package: Path, *, fixture: bool = False) -> dict[str, Any]:
    """Execute fail-closed certification over all gates."""
    # 1. Permission checks & file hygiene
    _walk_modes(package)
    _no_temp_dirs(package)
    _package_roots(package)

    # 2. Manifest and custody bindings
    custody, custody_raw = _read_json(package / "custody-receipt.json")
    manifest, manifest_raw = _read_json(package / "manifest.json")
    custody_hash = digest(custody_raw)
    manifest_hash = digest(manifest_raw)

    expected_custody_src = SOURCE_CUSTODY_SHA256 if not fixture else custody.get("source_custody_receipt_raw_sha256")
    expected_manifest_src = SOURCE_MANIFEST_SHA256 if not fixture else custody.get("source_label_manifest_raw_sha256")
    expected_commitment = (
        ORDERED_IDENTITY_COMMITMENT_SHA256 if not fixture else manifest.get("ordered_identity_commitment_sha256")
    )
    expected_packet_count = PACKET_COUNT if not fixture else len(manifest.get("packets", []))
    expected_row_count = ROW_COUNT if not fixture else sum(p.get("row_count", 0) for p in manifest.get("packets", []))

    if (
        set(custody) != _CUSTODY_FIELDS
        or custody.get("schema_version") != "phase3_cycle007_custody_receipt_v1"
        or custody.get("evaluation_cycle_id") != CYCLE
        or custody.get("source_evaluation_cycle_id") != SOURCE_CYCLE
        or custody.get("amendment_reference") != "batch_state/phase3-cycle007-source-grounded-amendment-v1.md"
        or custody.get("source_custody_receipt_raw_sha256") != expected_custody_src
        or custody.get("source_label_manifest_raw_sha256") != expected_manifest_src
        or custody.get("ordered_identity_commitment_sha256") != expected_commitment
        or custody.get("packet_count") != expected_packet_count
        or custody.get("row_count") != expected_row_count
        or custody.get("provider_artifacts_copied") is not False
        or custody.get("labels_copied") is not False
        or custody.get("responses_copied") is not False
        or custody.get("prompts_generated") is not False
        or custody.get("evidence_sidecars_generated") is not False
        or custody.get("text_free") is not True
        or custody.get("lane_row_counts")
        != (
            LANE_ROW_COUNTS
            if not fixture
            else {
                lane: sum(p.get("row_count", 0) for p in manifest.get("packets", []) if p.get("lane") == lane)
                for lane in LANES
            }
        )
        or not isinstance(custody.get("packet_size"), int)
        or custody.get("receipt_sha256") != _receipt_hash(custody)
    ):
        raise Error("source_manifest_binding")

    if (
        set(manifest) != _MATERIALIZATION_MANIFEST_FIELDS
        or manifest.get("schema_version") != "phase3_cycle007_materialization_manifest_v1"
        or manifest.get("evaluation_cycle_id") != CYCLE
        or manifest.get("source_evaluation_cycle_id") != SOURCE_CYCLE
        or manifest.get("custody_receipt_raw_sha256") != custody_hash
        or manifest.get("ordered_identity_commitment_sha256") != expected_commitment
        or manifest.get("packet_count") != expected_packet_count
        or manifest.get("row_count") != expected_row_count
        or manifest.get("text_free") is not True
        or not isinstance(manifest.get("packets"), list)
        or len(manifest["packets"]) != expected_packet_count
        or manifest.get("lane_row_counts") != custody.get("lane_row_counts")
        or manifest.get("identity_union_commitment_sha256") != custody.get("identity_union_commitment_sha256")
        or manifest.get("ordered_packet_commitment_sha256") != custody.get("ordered_packet_commitment_sha256")
        or manifest.get("receipt_sha256") != _receipt_hash(manifest)
    ):
        raise Error("source_manifest_binding")

    # 3. Evidence validation
    ev_manifest_path = package / "evidence" / "manifest.json"
    _regular(ev_manifest_path)
    ev_manifest, ev_manifest_raw = _read_json(ev_manifest_path)
    expected_identity = {k: ev_manifest.get(k) for k in validator._IDENTITY_FIELDS}
    try:
        validator.validate_manifest(ev_manifest, expected_identity=expected_identity)
    except validator.EvidenceValidationError as exc:
        raise Error("evidence_validation_failed") from exc

    sidecars = ev_manifest.get("sidecars", [])
    if len(sidecars) != expected_packet_count:
        raise Error("evidence_validation_failed")

    source_package_binding = {
        "source_evaluation_cycle_id": SOURCE_CYCLE,
        "custody_receipt_raw_sha256": custody_hash,
        "materialization_manifest_sha256": manifest["receipt_sha256"],
        "ordered_identity_commitment_sha256": expected_commitment,
        "identity_union_commitment_sha256": manifest["identity_union_commitment_sha256"],
        "ordered_packet_commitment_sha256": manifest["ordered_packet_commitment_sha256"],
        "packet_count": expected_packet_count,
        "row_count": expected_row_count,
    }
    if ev_manifest.get("source_package_binding") != source_package_binding:
        raise Error("evidence_validation_failed")

    material_packets: dict[tuple[str, int], dict[str, Any]] = {}
    for record in manifest["packets"]:
        if not isinstance(record, dict) or set(record) != _MATERIAL_PACKET_FIELDS:
            raise Error("exact_packet_denominator")
        key = (record.get("lane"), record.get("packet_index"))
        if (
            key in material_packets
            or key[0] not in LANES
            or not isinstance(key[1], int)
            or record.get("canonical_basename") != f"packet-{key[1]:04d}.json"
            or not isinstance(record.get("row_count"), int)
            or not _hex(record.get("raw_sha256"))
            or not _hex(record.get("packet_identity_set_sha256"))
        ):
            raise Error("exact_packet_denominator")
        material_packets[key] = record

    sidecar_by_uid: dict[tuple[str, str], dict[str, Any]] = {}
    sidecar_artifacts: dict[tuple[str, int], tuple[Path, bytes, dict[str, Any]]] = {}
    sidecar_packet_keys: set[tuple[str, int]] = set()
    sidecar_indexes: set[int] = set()
    for entry in sidecars:
        p_idx = entry["packet_index"]
        s_path = package / "evidence" / f"sidecar-{p_idx:04d}.json"
        _regular(s_path)
        s_data, s_raw = _read_json(s_path)
        try:
            validator.validate_sidecar(s_data, expected_identity=expected_identity)
        except validator.EvidenceValidationError as exc:
            raise Error("evidence_validation_failed") from exc
        key = (entry.get("lane"), p_idx)
        matching_packets = [
            (packet_key, packet)
            for packet_key, packet in material_packets.items()
            if packet_key[0] == entry.get("lane")
            and entry.get("packet_binding")
            == {field: packet[field] for field in ("canonical_basename", "raw_sha256", "packet_identity_set_sha256")}
        ]
        packet_key, packet_record = matching_packets[0] if len(matching_packets) == 1 else (None, None)
        if (
            p_idx in sidecar_indexes
            or packet_record is None
            or entry.get("row_count") != packet_record["row_count"]
            or entry.get("packet_binding")
            != {
                field: packet_record[field]
                for field in ("canonical_basename", "raw_sha256", "packet_identity_set_sha256")
            }
            or entry.get("sidecar_sha256") != digest(s_raw)
            or entry.get("sidecar_id") != s_data.get("sidecar_id")
            or s_data.get("lane") != entry.get("lane")
            or s_data.get("packet_index") != p_idx
            or s_data.get("row_count") != packet_record["row_count"]
            or s_data.get("packet_binding") != entry.get("packet_binding")
        ):
            raise Error("evidence_validation_failed")
        sidecar_indexes.add(p_idx)
        sidecar_packet_keys.add(packet_key)
        sidecar_artifacts[packet_key] = (s_path, s_raw, s_data)
        for r in s_data.get("rows", []):
            uid = (r["unit_id"], r["unit_sha256"])
            if uid in sidecar_by_uid:
                raise Error("evidence_validation_failed")
            sidecar_by_uid[uid] = r
    if set(material_packets) != sidecar_packet_keys or set(material_packets) != set(sidecar_artifacts):
        raise Error("evidence_validation_failed")
    controls = _validate_controls(
        package,
        fixture=fixture,
        custody_hash=custody_hash,
        manifest_hash=manifest_hash,
        evidence_hash=digest(ev_manifest_raw),
        evidence=ev_manifest,
    )

    # 4. Check packets and row order
    ordered_identities: list[list[Any]] = []
    seen_identities: list[tuple[str, str]] = []
    packet_data_lookup: dict[tuple[str, int], dict[str, Any]] = {}
    lane_rows: dict[str, int] = defaultdict(int)
    lane_packets: dict[str, int] = defaultdict(int)

    for packet_record in manifest["packets"]:
        lane = packet_record["lane"]
        idx = packet_record["packet_index"]
        packet_path = package / lane / f"packet-{idx:04d}.json"
        _regular(packet_path)
        p_data, p_raw = _read_json(packet_path)
        packet_data_lookup[(lane, idx)] = p_data
        if (
            digest(p_raw) != packet_record["raw_sha256"]
            or p_data.get("packet_identity_set_sha256") != packet_record["packet_identity_set_sha256"]
            or not isinstance(p_data.get("rows"), list)
            or len(p_data["rows"]) != packet_record["row_count"]
        ):
            raise Error("exact_packet_denominator")
        packet_identities: list[tuple[str, str]] = []
        for r_idx, row in enumerate(p_data.get("rows", [])):
            uid = (row["unit_id"], row["unit_sha256"])
            packet_identities.append(uid)
            ordered_identities.append([lane, idx, r_idx, uid[0], uid[1]])
            seen_identities.append(uid)
        if digest(canonical(sorted(packet_identities))) != packet_record["packet_identity_set_sha256"]:
            raise Error("exact_packet_denominator")
        lane_rows[lane] += len(packet_identities)
        lane_packets[lane] += 1

    expected_lane_packets = LANES if not fixture else {lane: lane_packets[lane] for lane in LANES}
    if (
        len(seen_identities) != expected_row_count
        or len(seen_identities) != len(set(seen_identities))
        or lane_rows != manifest["lane_row_counts"]
        or lane_packets != expected_lane_packets
    ):
        raise Error("ordered_identity_denominator")

    recomputed_commitment = digest(canonical(ordered_identities))
    if (
        recomputed_commitment != expected_commitment
        or digest(canonical(sorted(seen_identities))) != manifest["identity_union_commitment_sha256"]
        or digest(canonical(manifest["packets"])) != manifest["ordered_packet_commitment_sha256"]
        or len(sidecar_by_uid) != len(seen_identities)
        or set(sidecar_by_uid) != set(seen_identities)
    ):
        raise Error("ordered_identity_denominator")

    # 5. Check Provider Receipt Coverage (Grok & Gemini)
    for provider_name, provider_root in [("grok", GROK_ROOT), ("gemini", GEMINI_ROOT)]:
        expected_spec = EXPECTED_MODELS[provider_name]
        p_dir = package / provider_root
        if not p_dir.exists():
            raise Error("provider_receipt_coverage")
        for packet_record in manifest["packets"]:
            lane = packet_record["lane"]
            idx = packet_record["packet_index"]
            rcpt_p = p_dir / lane / f"receipt-{idx:04d}.json"
            lbl_p = p_dir / lane / f"labels-{idx:04d}.json"
            if not rcpt_p.exists() or not lbl_p.exists():
                raise Error("provider_receipt_coverage")
            rcpt_val, _ = _read_json(rcpt_p)
            lbl_val, lbl_raw = _read_json(lbl_p)
            p_rows = packet_data_lookup[(lane, idx)]["rows"]
            _sidecar_path, sidecar_raw, sidecar = sidecar_artifacts[(lane, idx)]
            raw_manifest_path = p_dir / lane / f"raw-manifest-{idx:04d}.json"
            try:
                _regular(raw_manifest_path)
            except Error as exc:
                raise Error("provider_receipt_coverage") from exc
            provider_extras: dict[str, Any]
            if provider_name == "gemini":
                provider_extras = {"chunk_count": (len(p_rows) + 19) // 20}
            else:
                raw_path = p_dir / lane / f"raw-{idx:04d}.raw"
                prompt_path = package / "prompts" / f"grok-{'clean' if lane == 'clean_label' else 'residual'}-label.md"
                try:
                    _regular(raw_path)
                    _regular(prompt_path)
                except Error as exc:
                    raise Error("provider_receipt_coverage") from exc
                provider_extras = {
                    "response_raw_sha256": digest(raw_path.read_bytes()),
                    "prompt_path": prompt_path.relative_to(package).as_posix(),
                    "prompt_sha256": digest(prompt_path.read_bytes()),
                    "attempt_count": rcpt_val.get("attempt_count"),
                }
            if (
                set(rcpt_val) != _PROVIDER_RECEIPT_FIELDS[provider_name]
                or set(lbl_val) != {"labels"}
                or not isinstance(lbl_val.get("labels"), list)
                or rcpt_val.get("schema_version") != f"phase3_cycle007_{provider_name}_packet_label_receipt_v1"
                or rcpt_val.get("evaluation_cycle_id") != CYCLE
                or rcpt_val.get("amendment_sha256") != AMENDMENT_SHA256
                or rcpt_val.get("custody_receipt_raw_sha256") != custody_hash
                or rcpt_val.get("materialization_manifest_raw_sha256") != manifest_hash
                or rcpt_val.get("evidence_manifest_raw_sha256") != digest(ev_manifest_raw)
                or rcpt_val.get("lane") != lane
                or rcpt_val.get("packet_index") != idx
                or rcpt_val.get("row_count") != len(p_rows)
                or rcpt_val.get("packet_raw_sha256") != packet_record["raw_sha256"]
                or rcpt_val.get("packet_identity_set_sha256") != packet_record["packet_identity_set_sha256"]
                or rcpt_val.get("sidecar_raw_sha256") != digest(sidecar_raw)
                or rcpt_val.get("sidecar_id") != sidecar["sidecar_id"]
                or rcpt_val.get("raw_manifest_sha256") != digest(raw_manifest_path.read_bytes())
                or rcpt_val.get("exact_model") != expected_spec["exact_model"]
                or rcpt_val.get("model_family") != expected_spec["model_family"]
                or rcpt_val.get("harness") != expected_spec["harness"]
                or rcpt_val.get("labels_sha256") != digest(lbl_raw)
                or any(rcpt_val.get(key) != value for key, value in provider_extras.items())
                or (provider_name == "grok" and rcpt_val.get("attempt_count") not in {1, 2})
                or rcpt_val.get("text_free") is not True
                or rcpt_val.get("receipt_sha256") != _receipt_hash(rcpt_val)
            ):
                raise Error("provider_receipt_coverage")
            labels_list = lbl_val.get("labels", [])
            if len(labels_list) != len(p_rows):
                raise Error("provider_receipt_coverage")
            for row, lbl in zip(p_rows, labels_list, strict=True):
                r_ev = sidecar_by_uid.get((row["unit_id"], row["unit_sha256"]))
                if r_ev is None:
                    raise Error("provider_receipt_coverage")
                try:
                    validate_label(lane, lbl, row, r_ev)
                except Error as exc:
                    raise Error("provider_receipt_coverage") from exc

    # 6. Recompute and Check Comparison Stage
    comp_packet_receipts: list[dict[str, Any]] = []
    all_clean_records: list[dict[str, Any]] = []
    all_risk_records: list[dict[str, Any]] = []
    all_disagreements: list[dict[str, Any]] = []

    for packet_record in manifest["packets"]:
        lane = packet_record["lane"]
        idx = packet_record["packet_index"]
        p_rows = packet_data_lookup[(lane, idx)]["rows"]

        grok_lbl_val, _ = _read_json(package / GROK_ROOT / lane / f"labels-{idx:04d}.json")
        gemini_lbl_val, _ = _read_json(package / GEMINI_ROOT / lane / f"labels-{idx:04d}.json")
        grok_labels = grok_lbl_val["labels"]
        gemini_labels = gemini_lbl_val["labels"]

        comp_rcpt_p = package / COMPARE_ROOT / lane / f"receipt-{idx:04d}.json"
        clean_p = package / COMPARE_ROOT / lane / f"clean-consensus-{idx:04d}.json"
        risk_p = package / COMPARE_ROOT / lane / f"risk-consensus-{idx:04d}.json"
        disag_p = package / COMPARE_ROOT / lane / f"disagreements-{idx:04d}.json"

        if not comp_rcpt_p.exists() or not clean_p.exists() or not risk_p.exists() or not disag_p.exists():
            raise Error("comparison_receipts")

        comp_rcpt, _ = _read_json(comp_rcpt_p)
        clean_val, clean_raw = _read_json(clean_p)
        risk_val, risk_raw = _read_json(risk_p)
        disag_val, disag_raw = _read_json(disag_p)

        if (
            comp_rcpt.get("clean_consensus_sha256") != digest(clean_raw)
            or comp_rcpt.get("risk_consensus_sha256") != digest(risk_raw)
            or comp_rcpt.get("disagreements_sha256") != digest(disag_raw)
            or comp_rcpt.get("receipt_sha256")
            != digest(canonical({k: v for k, v in comp_rcpt.items() if k != "receipt_sha256"}))
        ):
            raise Error("comparison_receipts")

        # Recompute partition
        expected_clean: list[dict[str, Any]] = []
        expected_risk: list[dict[str, Any]] = []
        expected_disag: list[dict[str, Any]] = []

        for row, g_lbl, m_lbl in zip(p_rows, grok_labels, gemini_labels, strict=True):
            r_ev = sidecar_by_uid.get((row["unit_id"], row["unit_sha256"]))
            sem_g = {k: v for k, v in g_lbl.items() if k not in {"unit_id", "unit_sha256"}}
            sem_m = {k: v for k, v in m_lbl.items() if k not in {"unit_id", "unit_sha256"}}
            if sem_g == sem_m:
                is_risk, reasons = is_risk_triggered(row, r_ev, g_lbl, m_lbl)
                rec = {"source_row": row, "label": g_lbl}
                if is_risk:
                    expected_risk.append({**rec, "risk_reasons": reasons})
                else:
                    expected_clean.append(rec)
            else:
                expected_disag.append({"source_row": row, "grok_label": g_lbl, "gemini_label": m_lbl})

        if (
            clean_val.get("records", []) != expected_clean
            or risk_val.get("records", []) != expected_risk
            or disag_val.get("records", []) != expected_disag
        ):
            raise Error("comparison_receipts")

        for r in expected_clean:
            all_clean_records.append({**r, "lane": lane, "packet_index": idx})
        for r in expected_risk:
            all_risk_records.append({**r, "lane": lane, "packet_index": idx})
        for r in expected_disag:
            all_disagreements.append({**r, "lane": lane, "packet_index": idx})
        comp_packet_receipts.append(comp_rcpt)

    comp_batch_path = package / COMPARE_ROOT / "batch-receipt.json"
    _regular(comp_batch_path)
    comp_batch, _ = _read_json(comp_batch_path)
    if (
        comp_batch.get("schema_version") != "phase3_cycle007_dual_label_batch_receipt_v1"
        or comp_batch.get("evaluation_cycle_id") != CYCLE
        or comp_batch.get("row_count") != expected_row_count
        or comp_batch.get("packet_count") != expected_packet_count
        or comp_batch.get("clean_consensus_count") != len(all_clean_records)
        or comp_batch.get("risk_triggered_consensus_count") != len(all_risk_records)
        or comp_batch.get("disagreement_count") != len(all_disagreements)
        or comp_batch.get("packet_receipt_union_sha256")
        != digest(canonical([r["receipt_sha256"] for r in comp_packet_receipts]))
        or comp_batch.get("receipt_sha256")
        != digest(canonical({k: v for k, v in comp_batch.items() if k != "receipt_sha256"}))
        or comp_batch.get("text_free") is not True
    ):
        raise Error("comparison_batch_receipt")

    # 7. Validate all sealed bounded source-review artifacts and their exact links.
    sample_doc, _risk_rcpt, _clean_rcpt = _validate_live_audit(
        package,
        custody_hash=custody_hash,
        manifest_hash=manifest_hash,
        manifest=manifest,
        expected_commitment=expected_commitment,
        ev_manifest_raw=ev_manifest_raw,
        expected_identity=expected_identity,
        sidecar_by_uid=sidecar_by_uid,
        clean_records=all_clean_records,
        risk_records=all_risk_records,
        sample_records=[],
    )
    # 8. Check Adjudication Stage
    adj_packet_receipts: list[dict[str, Any]] = []
    all_adj_labels: list[dict[str, Any]] = []
    all_unresolved: list[dict[str, Any]] = []

    for packet_record in manifest["packets"]:
        lane = packet_record["lane"]
        idx = packet_record["packet_index"]
        disag_p = package / COMPARE_OUTPUT / lane / f"disagreements-{idx:04d}.json"
        disag_val, _ = _read_json(disag_p)
        packet_disags = disag_val.get("records", [])

        adj_rcpt_p = package / ADJUDICATION_ROOT / "final" / lane / f"receipt-{idx:04d}.json"
        adj_lbl_p = package / ADJUDICATION_ROOT / "final" / lane / f"labels-{idx:04d}.json"
        adj_unres_p = package / ADJUDICATION_ROOT / "final" / lane / f"unresolved-{idx:04d}.json"

        if not adj_rcpt_p.exists() or not adj_lbl_p.exists() or not adj_unres_p.exists():
            raise Error("adjudication_candidate_partition")

        adj_rcpt, _ = _read_json(adj_rcpt_p)
        adj_lbl, adj_lbl_raw = _read_json(adj_lbl_p)
        adj_unres, adj_unres_raw = _read_json(adj_unres_p)

        if (
            adj_rcpt.get("model_family") != "anthropic"
            or adj_rcpt.get("labels_sha256") != digest(adj_lbl_raw)
            or adj_rcpt.get("unresolved_sha256") != digest(adj_unres_raw)
            or adj_rcpt.get("receipt_sha256")
            != digest(canonical({k: v for k, v in adj_rcpt.items() if k != "receipt_sha256"}))
        ):
            raise Error("adjudication_candidate_partition")

        p_adj_labels = adj_lbl.get("labels", [])
        p_unres = adj_unres.get("records", [])
        if len(p_adj_labels) + len(p_unres) != len(packet_disags):
            raise Error("adjudication_candidate_partition")

        # Verify candidate-only binding
        disag_by_u = {(d["source_row"]["unit_id"], d["source_row"]["unit_sha256"]): d for d in packet_disags}
        for lbl in p_adj_labels:
            uid = (lbl["unit_id"], lbl["unit_sha256"])
            if uid not in disag_by_u:
                raise Error("adjudication_candidate_partition")
            d = disag_by_u[uid]
            sem_lbl = {k: v for k, v in lbl.items() if k not in {"unit_id", "unit_sha256"}}
            sem_g = {k: v for k, v in d["grok_label"].items() if k not in {"unit_id", "unit_sha256"}}
            sem_m = {k: v for k, v in d["gemini_label"].items() if k not in {"unit_id", "unit_sha256"}}
            if sem_lbl != sem_g and sem_lbl != sem_m:
                raise Error("adjudication_candidate_partition")

        all_adj_labels.extend(p_adj_labels)
        all_unresolved.extend(p_unres)
        adj_packet_receipts.append(adj_rcpt)

    adj_batch_path = package / ADJUDICATION_ROOT / "batch-receipt.json"
    _regular(adj_batch_path)
    adj_batch, _ = _read_json(adj_batch_path)
    if (
        adj_batch.get("schema_version") != "phase3_cycle007_dual_label_adjudication_batch_receipt_v1"
        or adj_batch.get("evaluation_cycle_id") != CYCLE
        or adj_batch.get("model_family") != "anthropic"
        or adj_batch.get("total_disagreements") != len(all_disagreements)
        or adj_batch.get("total_adjudicated") != len(all_adj_labels)
        or adj_batch.get("total_unresolved") != len(all_unresolved)
        or adj_batch.get("packet_receipt_union_sha256")
        != digest(canonical([r["receipt_sha256"] for r in adj_packet_receipts]))
        or adj_batch.get("receipt_sha256")
        != digest(canonical({k: v for k, v in adj_batch.items() if k != "receipt_sha256"}))
        or adj_batch.get("text_free") is not True
    ):
        raise Error("adjudication_candidate_partition")

    # 9. Check Resolution & Authorization Stage
    if all_unresolved:
        auth_file = package / RESOLUTION_ROOT / "authorization.json"
        if not auth_file.exists():
            raise Error("resolution_authorization")
        auth_val, _ = _read_json(auth_file)
        unres_uids = {(r["source_row"]["unit_id"], r["source_row"]["unit_sha256"]) for r in all_unresolved}
        auths_list = auth_val.get("authorizations", [])
        if len(auths_list) != len(unres_uids) or {(a["unit_id"], a["unit_sha256"]) for a in auths_list} != unres_uids:
            raise Error("resolution_authorization")

    res_packet_receipts: list[dict[str, Any]] = []
    final_seen: list[tuple[str, str]] = []
    for packet_record in manifest["packets"]:
        lane = packet_record["lane"]
        idx = packet_record["packet_index"]
        p_rows = packet_data_lookup[(lane, idx)]["rows"]

        res_rcpt_p = package / RESOLUTION_ROOT / "final" / lane / f"receipt-{idx:04d}.json"
        lbl_path = package / RESOLUTION_ROOT / "final" / lane / f"labels-{idx:04d}.json"
        dec_path = package / RESOLUTION_ROOT / "final" / lane / f"decisions-{idx:04d}.json"

        if not res_rcpt_p.exists() or not lbl_path.exists() or not dec_path.exists():
            raise Error("resolution_authorization")

        res_rcpt, _ = _read_json(res_rcpt_p)
        lbl_data, lbl_raw = _read_json(lbl_path)
        dec_data, dec_raw = _read_json(dec_path)

        if (
            res_rcpt.get("labels_sha256") != digest(lbl_raw)
            or res_rcpt.get("decisions_sha256") != digest(dec_raw)
            or res_rcpt.get("unresolved_remaining_count") != 0
            or res_rcpt.get("receipt_sha256")
            != digest(canonical({k: v for k, v in res_rcpt.items() if k != "receipt_sha256"}))
        ):
            raise Error("resolution_authorization")

        labels_list = lbl_data.get("labels", [])
        decisions_list = dec_data.get("decisions", [])
        if len(labels_list) != len(p_rows) or len(decisions_list) != len(p_rows):
            raise Error("final_identity_union")

        for row, lbl in zip(p_rows, labels_list, strict=True):
            uid = (lbl["unit_id"], lbl["unit_sha256"])
            final_seen.append(uid)
            r_ev = sidecar_by_uid.get(uid)
            validate_label(lane, lbl, row, r_ev)

        res_packet_receipts.append(res_rcpt)

    res_batch_path = package / RESOLUTION_ROOT / "batch-receipt.json"
    _regular(res_batch_path)
    res_batch, _ = _read_json(res_batch_path)
    if (
        res_batch.get("schema_version") != "phase3_cycle007_operator_resolution_batch_receipt_v1"
        or res_batch.get("evaluation_cycle_id") != CYCLE
        or res_batch.get("total_rows") != expected_row_count
        or res_batch.get("packet_count") != expected_packet_count
        or res_batch.get("unresolved_remaining_count") != 0
        or res_batch.get("packet_receipt_union_sha256")
        != digest(canonical([r["receipt_sha256"] for r in res_packet_receipts]))
        or res_batch.get("receipt_sha256")
        != digest(canonical({k: v for k, v in res_batch.items() if k != "receipt_sha256"}))
        or res_batch.get("text_free") is not True
    ):
        raise Error("final_residual_zero")

    if final_seen != seen_identities:
        raise Error("final_identity_union")

    # Certification receipt
    cert_receipt = {
        "schema_version": "phase3_cycle007_label_completion_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "source_custody_receipt_raw_sha256": SOURCE_CUSTODY_SHA256
        if not fixture
        else custody.get("source_custody_receipt_raw_sha256"),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256
        if not fixture
        else custody.get("source_label_manifest_raw_sha256"),
        "custody_receipt_raw_sha256": custody_hash,
        "manifest_raw_sha256": manifest_hash,
        "evidence_manifest_raw_sha256": digest(ev_manifest_raw),
        "preflight_receipt_sha256": controls["preflight_receipt_sha256"],
        "gemini_canary_receipt_sha256": controls["gemini_canary_receipt_sha256"],
        "grok_canary_receipt_sha256": controls["grok_canary_receipt_sha256"],
        "sources_endpoint_identity_sha256": controls["sources_endpoint_identity_sha256"],
        "stage_seal_hashes": controls["stage_seal_hashes"],
        "expected_certify_stage_seal_sha256": controls["expected_certify_stage_seal_sha256"],
        "ordered_identity_commitment_sha256": expected_commitment,
        "packet_count": expected_packet_count,
        "row_count": expected_row_count,
        "clean_consensus_count": len(all_clean_records),
        "risk_triggered_consensus_count": len(all_risk_records),
        "disagreement_count": len(all_disagreements),
        "audited_consensus_count": sample_doc["audited_count"],
        "one_sided_95_bound": sample_doc.get("one_sided_95_bound"),
        "unresolved_remaining_count": 0,
        "terminal_findings_count": 0,
        "text_free": True,
    }
    cert_receipt["receipt_sha256"] = digest(canonical(cert_receipt))

    cert_path = package / RESOLUTION_ROOT / "certification-receipt.json"
    _atomic(cert_path, cert_receipt)
    return cert_receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        result = certify_completion(args.package, fixture=args.fixture)
        if args.receipt is not None:
            _atomic(args.receipt, result)
    except Error as exc:
        result = {"ok": False, "failure_code": exc.failure_code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "closure_validation_failed", "text_free": True}
    else:
        result = {"ok": True, **result}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
