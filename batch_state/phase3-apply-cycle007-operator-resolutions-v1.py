#!/usr/bin/env python3
"""Fail-closed authorized candidate-only Cycle 007 resolver."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as evidence_compiler
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

RESOLUTION_OUTPUT = "dual-label-final-cycle007-v1"
ADJUDICATION_OUTPUT = "dual-label-adjudication-cycle007-v1"
COMPARE_OUTPUT = "dual-label-output-cycle007-v1"
AUTHORIZATION_SCHEMA_VERSION = "phase3_cycle007_operator_resolution_authorization_v2"
AUTHORITY_ATTESTATION_SCHEMA_VERSION = "phase3_cycle007_external_authority_attestation_v1"
NONCE_CONSUMPTION_SCHEMA_VERSION = "phase3_cycle007_authorization_nonce_consumption_v1"

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
        "authorization_binding_failure",
        "authorization_identity_failure",
        "authorization_schema_failure",
        "authorization_tamper_detected",
        "authorization_replay_detected",
        "candidate_invention_drift",
        "unauthorized_row_drift",
        "missing_authorization",
        "extra_authorization",
        "foreign_authorization",
        "already_resolved_authorization",
        "source_blind_authorization",
        "insufficient_evidence_for_decision",
        "evidence_reference_invalid",
        "missing_evidence_sidecar",
        "identity_binding_failure",
        "identity_or_order_drift",
        "identity_uniqueness_failure",
        "partition_overlap_drift",
        "partition_omission_drift",
        "upstream_package_binding",
        "upstream_receipt_drift",
        "mode_drift",
        "json_binding_failure",
        "final_label_validation_failure",
    }
)


class Error(ValueError):
    def __init__(self, code: str):
        self.code = code if code in FAILURE_CODES else "authorization_binding_failure"
        self.failure_code = self.code
        super().__init__(self.code)


class AuthorizationBundle(dict[tuple[str, str], dict[str, Any]]):
    """Validated per-row authorizations plus their immutable receipt metadata."""

    def __init__(self, values: dict[tuple[str, str], dict[str, Any]], metadata: dict[str, Any]):
        super().__init__(values)
        self.metadata = metadata


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise Error("json_binding_failure")
        value[key] = item
    return value


def _regular(path: Path, mode: int | None = 0o600) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise Error("authorization_binding_failure") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise Error("authorization_binding_failure")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("mode_drift")


def _directory(path: Path, mode: int | None = 0o700) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise Error("authorization_binding_failure") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise Error("authorization_binding_failure")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("mode_drift")


def _operator_owned_directory(path: Path) -> None:
    """Require an existing private directory owned by this operator process.

    The authority receipt and nonce ledger are deliberately outside the live
    package.  Ownership is not an identity assertion on its own; it prevents a
    package-controlled or shared directory from being substituted for the
    operator-controlled custody boundary defined by the Cycle006 pattern.
    """
    _directory(path, 0o700)
    try:
        if path.lstat().st_uid != os.geteuid():
            raise Error("authorization_identity_failure")
    except OSError:
        raise Error("authorization_binding_failure") from None


def _private_directory(package: Path, path: Path) -> None:
    """Create a package subtree and enforce private modes on every new level."""
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    current = path
    while current != package:
        current.chmod(0o700)
        current = current.parent
    _directory(package, 0o700)


def _read(path: Path) -> tuple[Any, bytes]:
    _regular(path, 0o600)
    raw = path.read_bytes()
    try:
        return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs), raw
    except (UnicodeDecodeError, json.JSONDecodeError, Error):
        raise Error("json_binding_failure") from None


def atomic(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _directory(path.parent, 0o700)
    data = canonical(value)
    if path.exists() or path.is_symlink():
        _regular(path, 0o600)
        if path.read_bytes() != data:
            raise Error("authorization_binding_failure")
        return digest(data)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with open(fd, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        temporary.replace(path)
        os.chmod(path, 0o600)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return digest(data)


def validate_clean_label(
    label: dict[str, Any],
    row: dict[str, Any],
    row_evidence: Mapping[str, Any] | None = None,
) -> None:
    if not isinstance(row_evidence, Mapping):
        raise Error("missing_evidence_sidecar")
    if (
        not isinstance(label, dict)
        or set(label)
        != {"unit_id", "unit_sha256", "decision_code", "clean_modern_standard_prose", "modern_genre_id", "evidence_ids"}
        or label.get("decision_code") not in REJECTS
        or type(label.get("clean_modern_standard_prose")) is not bool
        or not isinstance(label.get("evidence_ids"), list)
    ):
        raise Error("final_label_validation_failure")
    agrees = label["decision_code"] == "agree"
    if (
        agrees != label["clean_modern_standard_prose"]
        or (agrees and label["modern_genre_id"] not in GENRES)
        or (not agrees and label["modern_genre_id"] is not None)
    ):
        raise Error("final_label_validation_failure")
    evidence_ids = label["evidence_ids"]
    if evidence_ids != sorted(set(evidence_ids)):
        raise Error("evidence_reference_invalid")

    available_ids = set(row_evidence.get("evidence_ids", []))
    if set(evidence_ids) - available_ids:
        raise Error("evidence_reference_invalid")
    try:
        validator.validate_label_evidence_refs(
            row_evidence,
            decision_code=label["decision_code"],
            evidence_ids=evidence_ids,
            phenomenon_id=None,
        )
    except validator.EvidenceValidationError as exc:
        if exc.code == "insufficient_evidence_for_decision":
            raise Error("insufficient_evidence_for_decision") from exc
        raise Error("evidence_reference_invalid") from exc


def validate_residual_label(
    label: dict[str, Any],
    row: dict[str, Any],
    row_evidence: Mapping[str, Any] | None = None,
) -> None:
    if not isinstance(row_evidence, Mapping):
        raise Error("missing_evidence_sidecar")
    if (
        not isinstance(label, dict)
        or set(label) != {"unit_id", "unit_sha256", "phenomena", "primary_phenomenon_id", "item_decision_rollup"}
        or not isinstance(label.get("phenomena"), list)
        or not label["phenomena"]
        or label.get("item_decision_rollup") not in DEC
    ):
        raise Error("final_label_validation_failure")
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
            raise Error("final_label_validation_failure")
        if (
            p["decision_code"] in {"positive", "acceptable_control", "protected"}
            and p["evidence_sufficiency"] != "sufficient"
        ):
            raise Error("insufficient_evidence_for_decision")
        if row.get("family_id") == "pravopys_2019_complete" and p["decision_code"] == "positive":
            raise Error("final_label_validation_failure")
        p_ids = p["evidence_ids"]
        if p_ids != sorted(set(p_ids)):
            raise Error("evidence_reference_invalid")
        try:
            validator.validate_label_evidence_refs(
                row_evidence,
                decision_code=p["decision_code"],
                evidence_ids=p_ids,
                phenomenon_id=p["phenomenon_id"],
            )
        except validator.EvidenceValidationError as exc:
            if exc.code == "insufficient_evidence_for_decision":
                raise Error("insufficient_evidence_for_decision") from exc
            raise Error("evidence_reference_invalid") from exc
        names.append(p["phenomenon_id"])
        decisions[p["phenomenon_id"]] = p["decision_code"]

    if len(names) != len(set(names)) or names != sorted(names, key=TAX.index):
        raise Error("final_label_validation_failure")
    viable = [name for name in names if decisions[name] not in {"abstention", "disagreement"}]
    primary = label["primary_phenomenon_id"]
    if viable and (primary not in viable or label["item_decision_rollup"] != decisions[primary]):
        raise Error("final_label_validation_failure")
    if not viable and (
        primary is not None
        or label["item_decision_rollup"] != ("disagreement" if "disagreement" in decisions.values() else "abstention")
    ):
        raise Error("final_label_validation_failure")


def validate_label(
    lane: str,
    label: dict[str, Any],
    row: dict[str, Any],
    row_evidence: Mapping[str, Any] | None = None,
) -> None:
    if (label.get("unit_id"), label.get("unit_sha256")) != (row.get("unit_id"), row.get("unit_sha256")):
        raise Error("identity_or_order_drift")
    if lane == "clean_label":
        validate_clean_label(label, row, row_evidence)
    elif lane == "residual_label":
        validate_residual_label(label, row, row_evidence)
    else:
        raise Error("final_label_validation_failure")


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _identity_order_hash(identities: list[tuple[str, str]]) -> str:
    return digest(canonical([list(identity) for identity in identities]))


def _external_json(
    path: Path,
    package: Path,
    *,
    fixture: bool,
    authority_root: Path | None = None,
) -> tuple[dict[str, Any], bytes]:
    """Read a canonical authorization artifact outside the package boundary."""
    try:
        resolved_path = path.resolve(strict=True)
        inside_package = resolved_path.is_relative_to(package.resolve(strict=True))
    except OSError as exc:
        raise Error("authorization_binding_failure") from exc
    if inside_package and not fixture:
        raise Error("authorization_binding_failure")
    if authority_root is not None:
        try:
            resolved_root = authority_root.resolve(strict=True)
        except OSError as exc:
            raise Error("authorization_binding_failure") from exc
        _operator_owned_directory(resolved_root)
        if not resolved_path.is_relative_to(resolved_root):
            raise Error("authorization_binding_failure")
    value, raw = _read(path)
    if not isinstance(value, dict) or raw != canonical(value):
        raise Error("authorization_schema_failure")
    return value, raw


def _disk_evidence_identity() -> dict[str, Any]:
    """Recompute the evidence identity from reviewed local files, never its manifest.

    The evidence manifest is an input under validation, so deriving its
    expected identity from fields in that same manifest is circular.  The
    compiler records the exact files and code that define the frozen identity;
    calculate all hash-bearing values afresh from those paths before trusting a
    sidecar or manifest.
    """
    try:
        server_code = evidence_compiler.DEFAULT_SERVER_CODE
        sources_db = evidence_compiler.DEFAULT_SOURCES_DB
        vesum_db = evidence_compiler.DEFAULT_VESUM_DB
        for path in (server_code, sources_db, vesum_db):
            if not path.is_file():
                raise Error("missing_evidence_sidecar")
        return {
            "tokenizer_id": evidence_compiler.TOKENIZER_ID,
            "tokenizer_version": evidence_compiler.TOKENIZER_VERSION,
            "code_hashes": dict(evidence_compiler.CODE_HASHES),
            "server_code_sha256": contract.sha256_file(server_code),
            "sources_db_sha256": contract.sha256_file(sources_db),
            "vesum_db_sha256": contract.sha256_file(vesum_db),
        }
    except Error:
        raise
    except Exception:
        raise Error("missing_evidence_sidecar") from None


def _validate_authority_attestation(
    path: Path,
    package: Path,
    *,
    authority_root: Path,
    authorization_raw_sha256: str,
    request_raw_sha256: str,
    authorization_value: Mapping[str, Any],
) -> str:
    """Validate the independent authority receipt that admits an authorization.

    This is intentionally a distinct external file, so neither the resolution
    package nor the authorization document can self-attest its own authority.
    It binds every value that selects rows or decisions, without storing row
    text in the durable receipt.
    """
    value, raw = _external_json(path, package, fixture=False, authority_root=authority_root)
    required = {
        "schema_version",
        "evaluation_cycle_id",
        "amendment_sha256",
        "custody_receipt_raw_sha256",
        "source_label_manifest_raw_sha256",
        "manifest_raw_sha256",
        "ordered_identity_commitment_sha256",
        "authorization_receipt_raw_sha256",
        "request_raw_sha256",
        "decision_authority",
        "authorized_identity",
        "nonce_sha256",
        "text_free",
        "attestation_sha256",
    }
    if (
        set(value) != required
        or value.get("schema_version") != AUTHORITY_ATTESTATION_SCHEMA_VERSION
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("amendment_sha256") != AMENDMENT_SHA256
        or value.get("custody_receipt_raw_sha256") != digest((package / "custody-receipt.json").read_bytes())
        or value.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or value.get("manifest_raw_sha256") != digest((package / "manifest.json").read_bytes())
        or value.get("ordered_identity_commitment_sha256")
        != _read(package / "manifest.json")[0].get(
            "ordered_identity_commitment_sha256", ORDERED_IDENTITY_COMMITMENT_SHA256
        )
        or value.get("authorization_receipt_raw_sha256") != authorization_raw_sha256
        or value.get("request_raw_sha256") != request_raw_sha256
        or value.get("decision_authority") != authorization_value.get("decision_authority")
        or value.get("authorized_identity") != authorization_value.get("authorized_identity")
        or value.get("nonce_sha256") != authorization_value.get("nonce_sha256")
        or value.get("text_free") is not True
        or value.get("attestation_sha256")
        != digest(canonical({key: item for key, item in value.items() if key != "attestation_sha256"}))
    ):
        raise Error("authorization_binding_failure")
    return digest(raw)


def _consume_nonce(
    ledger: Path,
    package: Path,
    metadata: Mapping[str, Any],
) -> str:
    """Atomically burn a validated authorization nonce in external custody.

    A write failure leaves the nonce unavailable: retry requires a freshly
    attested authorization.  That conservative behavior prevents a crash or
    race from reopening a decision authority already observed by this runner.
    """
    try:
        resolved_ledger = ledger.resolve(strict=True)
        if resolved_ledger.is_relative_to(package.resolve(strict=True)):
            raise Error("authorization_binding_failure")
    except OSError as exc:
        raise Error("authorization_binding_failure") from exc
    _operator_owned_directory(resolved_ledger)
    nonce = metadata.get("nonce_sha256")
    if not _valid_sha256(nonce):
        raise Error("authorization_binding_failure")
    target = resolved_ledger / f"nonce-{nonce}.json"
    if target.exists() or target.is_symlink():
        raise Error("authorization_replay_detected")
    body = {
        "schema_version": NONCE_CONSUMPTION_SCHEMA_VERSION,
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": metadata["ordered_identity_commitment_sha256"],
        "authorization_receipt_raw_sha256": metadata["authorization_receipt_raw_sha256"],
        "authority_attestation_raw_sha256": metadata["authority_attestation_raw_sha256"],
        "request_raw_sha256": metadata["request_raw_sha256"],
        "nonce_sha256": nonce,
        "decision_authority": metadata["decision_authority"],
        "authorized_identity": metadata["authorized_identity"],
        "text_free": True,
    }
    body["consumption_sha256"] = digest(canonical(body))
    data = canonical(body)
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise Error("authorization_replay_detected") from None
    except OSError:
        raise Error("authorization_binding_failure") from None
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(target, 0o600)
        directory_fd = os.open(resolved_ledger, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        # The name was reserved with O_EXCL; leave any partial entry in place
        # so a second attempt cannot reuse the authorization after uncertainty.
        raise Error("authorization_binding_failure") from None
    return digest(data)


def validate_authorization_file(
    path: Path,
    package: Path,
    unresolved_identities: set[tuple[str, str]] | None = None,
    *,
    ordered_unresolved_identities: list[tuple[str, str]] | None = None,
    request_raw_sha256: str | None = None,
    fixture: bool = False,
    advisor_response_path: Path | None = None,
    authority_attestation_path: Path | None = None,
    authority_root: Path | None = None,
) -> AuthorizationBundle:
    if not fixture and (authority_attestation_path is None or authority_root is None):
        raise Error("authorization_binding_failure")
    value, raw = _external_json(path, package, fixture=fixture, authority_root=authority_root)
    custody_raw = (package / "custody-receipt.json").read_bytes()
    manifest_raw = (package / "manifest.json").read_bytes()
    manifest_val, _ = _read(package / "manifest.json")

    expected_commitment = manifest_val.get("ordered_identity_commitment_sha256", ORDERED_IDENTITY_COMMITMENT_SHA256)
    authority = value.get("decision_authority")
    authorized_identity = value.get("authorized_identity")
    if (
        value.get("schema_version") != AUTHORIZATION_SCHEMA_VERSION
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("amendment_sha256") != AMENDMENT_SHA256
        or value.get("custody_receipt_raw_sha256") != digest(custody_raw)
        or value.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or value.get("manifest_raw_sha256") != digest(manifest_raw)
        or value.get("ordered_identity_commitment_sha256") != expected_commitment
        or value.get("request_raw_sha256") != request_raw_sha256
        or authority not in {"operator", "designated_advisor"}
        or not isinstance(authorized_identity, dict)
        or set(authorized_identity) != {"identity_type", "identity_id"}
        or not isinstance(authorized_identity.get("identity_id"), str)
        or not authorized_identity["identity_id"].strip()
        or not _valid_sha256(value.get("nonce_sha256"))
        or not isinstance(value.get("identity_order_sha256"), str)
        or not isinstance(value.get("authorizations"), list)
        or value.get("text_free") is not True
    ):
        raise Error("authorization_binding_failure")

    base_keys = {
        "schema_version",
        "evaluation_cycle_id",
        "amendment_sha256",
        "custody_receipt_raw_sha256",
        "source_label_manifest_raw_sha256",
        "manifest_raw_sha256",
        "ordered_identity_commitment_sha256",
        "request_raw_sha256",
        "decision_authority",
        "authorized_identity",
        "identity_order_sha256",
        "nonce_sha256",
        "authorizations",
        "text_free",
        "receipt_sha256",
    }
    if authority == "operator":
        if (
            authorized_identity.get("identity_type") != "human"
            or advisor_response_path is not None
            or set(value) != base_keys | {"operator_id"}
            or not isinstance(value.get("operator_id"), str)
            or not value["operator_id"].strip()
            or value["operator_id"] != authorized_identity.get("identity_id")
        ):
            raise Error("authorization_identity_failure")
    else:
        advisor = value.get("advisor")
        expected_keys = base_keys | {"advisor"}
        if (
            authorized_identity.get("identity_type") != "designated_advisor"
            or set(value) != expected_keys
            or not isinstance(advisor, dict)
            or set(advisor)
            != {"identity_id", "exact_model", "model_family", "harness", "task_id", "response_raw_sha256"}
            or advisor.get("identity_id") != authorized_identity.get("identity_id")
            or not all(isinstance(advisor.get(key), str) and advisor[key].strip() for key in advisor)
            or not _valid_sha256(advisor.get("response_raw_sha256"))
            or advisor_response_path is None
        ):
            raise Error("authorization_identity_failure")
        _advisor_value, advisor_raw = _external_json(
            advisor_response_path,
            package,
            fixture=fixture,
            authority_root=authority_root,
        )
        if digest(advisor_raw) != advisor["response_raw_sha256"]:
            raise Error("authorization_binding_failure")

    authorizations: dict[tuple[str, str], dict[str, Any]] = {}
    seen: list[tuple[str, str]] = []

    for item in value["authorizations"]:
        if (
            not isinstance(item, dict)
            or set(item)
            != {"unit_id", "unit_sha256", "selection", "source_bound_rationale", "source_authority_reference"}
            or not isinstance(item.get("unit_id"), str)
            or not item["unit_id"]
            or not _valid_sha256(item.get("unit_sha256"))
            or not isinstance(item.get("source_bound_rationale"), str)
            or not item["source_bound_rationale"].strip()
            or not isinstance(item.get("source_authority_reference"), str)
            or not item["source_authority_reference"].strip()
            or item.get("selection") not in {"grok", "gemini"}
        ):
            raise Error("authorization_tamper_detected")

        key = (item["unit_id"], item["unit_sha256"])
        seen.append(key)
        authorizations[key] = item

    if len(seen) != len(set(seen)):
        raise Error("identity_uniqueness_failure")
    if unresolved_identities is not None:
        auth_keys = set(authorizations.keys())
        if auth_keys != unresolved_identities:
            if auth_keys - unresolved_identities:
                raise Error("unauthorized_row_drift")
            raise Error("missing_authorization")
    if ordered_unresolved_identities is not None and seen != ordered_unresolved_identities:
        raise Error("authorization_identity_failure")
    expected_order = ordered_unresolved_identities if ordered_unresolved_identities is not None else seen
    if value.get("identity_order_sha256") != _identity_order_hash(expected_order):
        raise Error("authorization_identity_failure")
    if not fixture and request_raw_sha256 is None:
        raise Error("authorization_binding_failure")
    if value.get("receipt_sha256") != digest(
        canonical({key: item for key, item in value.items() if key != "receipt_sha256"})
    ):
        raise Error("authorization_schema_failure")

    metadata: dict[str, Any] = {
        "authorization_receipt_raw_sha256": digest(raw),
        "authorization_receipt_sha256": value["receipt_sha256"],
        "decision_authority": authority,
        "authorized_identity": authorized_identity,
        "operator_id": value.get("operator_id"),
        "identity_order_sha256": value["identity_order_sha256"],
        "ordered_identity_commitment_sha256": value["ordered_identity_commitment_sha256"],
        "request_raw_sha256": value["request_raw_sha256"],
        "nonce_sha256": value["nonce_sha256"],
    }
    if not fixture:
        assert authority_attestation_path is not None and authority_root is not None
        metadata["authority_attestation_raw_sha256"] = _validate_authority_attestation(
            authority_attestation_path,
            package,
            authority_root=authority_root,
            authorization_raw_sha256=metadata["authorization_receipt_raw_sha256"],
            request_raw_sha256=value["request_raw_sha256"],
            authorization_value=value,
        )
    return AuthorizationBundle(authorizations, metadata)


def _evidence_sidecar(
    package: Path,
    lane: str,
    index: int,
    packet_path: Path,
    packet_data: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    fixture: bool,
) -> dict[tuple[str, str], dict[str, Any]]:
    """Resolve one exact packet sidecar; missing or incomplete evidence stops."""
    try:
        evidence_manifest_path = package / "evidence" / "manifest.json"
        _regular(evidence_manifest_path, 0o600)
        evidence_manifest, _ = _read(evidence_manifest_path)
    except Error as exc:
        raise Error("missing_evidence_sidecar") from exc
    if not isinstance(evidence_manifest, dict) or not isinstance(evidence_manifest.get("sidecars"), list):
        raise Error("missing_evidence_sidecar")

    binding = {
        "canonical_basename": packet_path.name,
        "raw_sha256": digest(packet_path.read_bytes()),
        "packet_identity_set_sha256": packet_data.get("packet_identity_set_sha256"),
    }
    matches = [
        entry
        for entry in evidence_manifest["sidecars"]
        if isinstance(entry, dict) and entry.get("lane") == lane and entry.get("packet_binding") == binding
    ]
    if len(matches) != 1:
        raise Error("missing_evidence_sidecar")
    entry = matches[0]
    sidecar_index = entry.get("packet_index")
    if not isinstance(sidecar_index, int) or sidecar_index < 1:
        raise Error("missing_evidence_sidecar")
    sidecar_path = package / "evidence" / f"sidecar-{sidecar_index:04d}.json"
    try:
        _regular(sidecar_path, 0o600)
        sidecar, sidecar_raw = _read(sidecar_path)
    except Error as exc:
        raise Error("missing_evidence_sidecar") from exc
    if (
        not isinstance(sidecar, dict)
        or entry.get("row_count") != len(rows)
        or entry.get("sidecar_sha256") != digest(sidecar_raw)
        or entry.get("sidecar_id") != sidecar.get("sidecar_id")
        or sidecar.get("schema_version") != "phase3_cycle007_evidence_sidecar_v1"
        or sidecar.get("evaluation_cycle_id") != CYCLE
        or sidecar.get("lane") != lane
        or sidecar.get("packet_index") != sidecar_index
        or sidecar.get("packet_binding") != binding
        or sidecar.get("row_count") != len(rows)
        or not isinstance(sidecar.get("rows"), list)
    ):
        raise Error("missing_evidence_sidecar")
    packet_ids = [(row.get("unit_id"), row.get("unit_sha256")) for row in rows]
    sidecar_rows = sidecar["rows"]
    sidecar_ids = [
        (row.get("unit_id"), row.get("unit_sha256")) if isinstance(row, dict) else (None, None) for row in sidecar_rows
    ]
    if len(sidecar_rows) != len(rows) or sidecar_ids != packet_ids or len(set(sidecar_ids)) != len(sidecar_ids):
        raise Error("missing_evidence_sidecar")
    if any(not isinstance(row, dict) for row in sidecar_rows):
        raise Error("missing_evidence_sidecar")

    if not fixture:
        expected_identity = _disk_evidence_identity()
        try:
            validator.validate_manifest(evidence_manifest, expected_identity=expected_identity)
            validator.validate_sidecar(sidecar, expected_identity=expected_identity)
        except validator.EvidenceValidationError as exc:
            raise Error("missing_evidence_sidecar") from exc
    return {key: row for key, row in zip(packet_ids, sidecar_rows, strict=True)}


def _validate_resolution_request(
    path: Path,
    expected_records: list[dict[str, Any]],
    *,
    custody_hash: str,
    manifest_hash: str,
    ordered_commitment: str,
) -> tuple[dict[str, Any], bytes]:
    """Validate the adjudicator's exact unresolved-record request before authorization."""
    try:
        value, raw = _read(path)
    except Error as exc:
        raise Error("authorization_binding_failure") from exc
    required = {
        "schema_version",
        "evaluation_cycle_id",
        "amendment_sha256",
        "custody_receipt_raw_sha256",
        "source_label_manifest_raw_sha256",
        "manifest_raw_sha256",
        "ordered_identity_commitment_sha256",
        "unresolved_count",
        "unresolved_records",
        "request_sha256",
        "text_free",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise Error("authorization_schema_failure")
    if (
        value.get("schema_version") != "phase3_cycle007_operator_resolution_request_v1"
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("amendment_sha256") != AMENDMENT_SHA256
        or value.get("custody_receipt_raw_sha256") != custody_hash
        or value.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or value.get("manifest_raw_sha256") != manifest_hash
        or value.get("ordered_identity_commitment_sha256") != ordered_commitment
        or value.get("unresolved_count") != len(expected_records)
        or value.get("text_free") is not False
        or not _valid_sha256(value.get("request_sha256"))
        or value.get("request_sha256")
        != digest(canonical({key: item for key, item in value.items() if key != "request_sha256"}))
        or raw != canonical(value)
    ):
        raise Error("authorization_binding_failure")
    if value.get("unresolved_records") != expected_records:
        raise Error("authorization_identity_failure")
    return value, raw


def resolve_packet(
    package: Path,
    lane: str,
    index: int,
    authorizations: dict[tuple[str, str], dict[str, Any]],
    *,
    fixture: bool = False,
) -> dict[str, Any]:
    # 1. Read packet rows
    packet_path = package / lane / f"packet-{index:04d}.json"
    _regular(packet_path, 0o600)
    packet_data, _ = _read(packet_path)
    if not isinstance(packet_data, dict) or "rows" not in packet_data or not isinstance(packet_data["rows"], list):
        raise Error("identity_binding_failure")
    rows = packet_data["rows"]
    packet_uids = [(r["unit_id"], r["unit_sha256"]) for r in rows]
    if len(packet_uids) != len(set(packet_uids)):
        raise Error("identity_uniqueness_failure")

    # Read and bind the required evidence sidecar before any label validation.
    sidecar_by_uid = _evidence_sidecar(
        package,
        lane,
        index,
        packet_path,
        packet_data,
        rows,
        fixture=fixture,
    )

    # 2. Read upstream comparison artifacts & receipts
    comp_dir = package / COMPARE_OUTPUT / lane
    comp_receipt_p = comp_dir / f"receipt-{index:04d}.json"
    clean_p = comp_dir / f"clean-consensus-{index:04d}.json"
    risk_p = comp_dir / f"risk-consensus-{index:04d}.json"
    disag_p = comp_dir / f"disagreements-{index:04d}.json"

    _regular(comp_receipt_p, 0o600)
    _regular(clean_p, 0o600)
    _regular(risk_p, 0o600)
    _regular(disag_p, 0o600)

    comp_receipt, _ = _read(comp_receipt_p)
    clean_val, clean_raw = _read(clean_p)
    risk_val, risk_raw = _read(risk_p)
    disag_val, disag_raw = _read(disag_p)

    if (
        comp_receipt.get("schema_version") != "phase3_cycle007_dual_label_packet_receipt_v1"
        or comp_receipt.get("evaluation_cycle_id") != CYCLE
        or comp_receipt.get("lane") != lane
        or comp_receipt.get("packet_index") != index
        or comp_receipt.get("row_count") != len(rows)
        or comp_receipt.get("clean_consensus_sha256") != digest(clean_raw)
        or comp_receipt.get("risk_consensus_sha256") != digest(risk_raw)
        or comp_receipt.get("disagreements_sha256") != digest(disag_raw)
        or comp_receipt.get("receipt_sha256")
        != digest(canonical({k: v for k, v in comp_receipt.items() if k != "receipt_sha256"}))
    ):
        raise Error("upstream_receipt_drift")

    # 3. Read upstream adjudication artifacts & receipts
    adj_dir = package / ADJUDICATION_OUTPUT / "final" / lane
    adj_receipt_p = adj_dir / f"receipt-{index:04d}.json"
    adj_labels_p = adj_dir / f"labels-{index:04d}.json"
    adj_unres_p = adj_dir / f"unresolved-{index:04d}.json"

    _regular(adj_receipt_p, 0o600)
    _regular(adj_labels_p, 0o600)
    _regular(adj_unres_p, 0o600)

    adj_receipt, _ = _read(adj_receipt_p)
    adj_labels_val, adj_labels_raw = _read(adj_labels_p)
    adj_unres_val, adj_unres_raw = _read(adj_unres_p)

    if (
        adj_receipt.get("schema_version") != "phase3_cycle007_dual_label_adjudication_packet_receipt_v1"
        or adj_receipt.get("evaluation_cycle_id") != CYCLE
        or adj_receipt.get("lane") != lane
        or adj_receipt.get("packet_index") != index
        or adj_receipt.get("model_family") != "anthropic"
        or adj_receipt.get("labels_sha256") != digest(adj_labels_raw)
        or adj_receipt.get("unresolved_sha256") != digest(adj_unres_raw)
        or adj_receipt.get("receipt_sha256")
        != digest(canonical({k: v for k, v in adj_receipt.items() if k != "receipt_sha256"}))
    ):
        raise Error("upstream_receipt_drift")

    authorization_metadata = getattr(authorizations, "metadata", None)
    if adj_unres_val.get("records") and not isinstance(authorization_metadata, dict):
        raise Error("authorization_binding_failure")

    # 4. Strict disjoint partition verification across clean, risk, adjudicated, and unresolved
    partition_map: dict[tuple[str, str], tuple[str, dict[str, Any], dict[str, Any]]] = {}

    for r in clean_val.get("records", []):
        uid = (r["source_row"]["unit_id"], r["source_row"]["unit_sha256"])
        if uid in partition_map:
            raise Error("partition_overlap_drift")
        partition_map[uid] = ("clean_consensus", r["label"], {"origin": "clean_consensus", "selection": "consensus"})

    for r in risk_val.get("records", []):
        uid = (r["source_row"]["unit_id"], r["source_row"]["unit_sha256"])
        if uid in partition_map:
            raise Error("partition_overlap_drift")
        partition_map[uid] = (
            "risk_consensus",
            r["label"],
            {"origin": "risk_consensus", "selection": "consensus", "risk_reasons": r.get("risk_reasons", [])},
        )

    disag_by_uid: dict[tuple[str, str], dict[str, Any]] = {}
    for r in disag_val.get("records", []):
        uid = (r["source_row"]["unit_id"], r["source_row"]["unit_sha256"])
        if uid in disag_by_uid:
            raise Error("identity_uniqueness_failure")
        disag_by_uid[uid] = r

    for lbl in adj_labels_val.get("labels", []):
        uid = (lbl["unit_id"], lbl["unit_sha256"])
        if uid not in disag_by_uid:
            raise Error("candidate_invention_drift")
        if uid in partition_map:
            raise Error("partition_overlap_drift")
        # Candidate-only check: label must match either grok or gemini candidate
        disag = disag_by_uid[uid]
        semantic_lbl = {k: v for k, v in lbl.items() if k not in {"unit_id", "unit_sha256"}}
        semantic_grok = {k: v for k, v in disag["grok_label"].items() if k not in {"unit_id", "unit_sha256"}}
        semantic_gemini = {k: v for k, v in disag["gemini_label"].items() if k not in {"unit_id", "unit_sha256"}}
        if semantic_lbl != semantic_grok and semantic_lbl != semantic_gemini:
            raise Error("candidate_invention_drift")
        partition_map[uid] = ("adjudication", lbl, {"origin": "adjudication", "selection": "adjudicated"})

    for unres in adj_unres_val.get("records", []):
        uid = (unres["source_row"]["unit_id"], unres["source_row"]["unit_sha256"])
        if uid not in disag_by_uid:
            raise Error("candidate_invention_drift")
        if uid in partition_map:
            raise Error("partition_overlap_drift")
        if uid not in authorizations:
            raise Error("missing_authorization")
        auth = authorizations[uid]
        choice = auth["selection"]
        if choice == "grok":
            chosen_label = unres["grok_label"]
        elif choice == "gemini":
            chosen_label = unres["gemini_label"]
        else:
            raise Error("candidate_invention_drift")

        # Source-bound validation
        rationale = auth.get("source_bound_rationale", "")
        reference = auth.get("source_authority_reference", "")
        if (
            not isinstance(rationale, str)
            or not rationale.strip()
            or not isinstance(reference, str)
            or not reference.strip()
        ):
            raise Error("source_blind_authorization")

        row_ev = sidecar_by_uid.get(uid)
        validate_label(lane, chosen_label, unres["source_row"], row_ev)

        partition_map[uid] = (
            "operator_resolution",
            chosen_label,
            {
                "origin": "operator_resolution",
                "selection": choice,
                "source_bound_rationale": rationale,
                "source_authority_reference": reference,
            },
        )

    # Check that all packet rows are strictly partitioned
    if set(partition_map.keys()) != set(packet_uids) or len(partition_map) != len(rows):
        raise Error("partition_omission_drift")

    # 5. Reassemble in exact frozen row order and validate
    ordered_labels: list[dict[str, Any]] = []
    ordered_decisions: list[dict[str, Any]] = []
    for row in rows:
        uid = (row["unit_id"], row["unit_sha256"])
        _origin, label, dec = partition_map[uid]
        row_ev = sidecar_by_uid.get(uid)
        validate_label(lane, label, row, row_ev)
        ordered_labels.append(label)
        ordered_decisions.append(
            {
                "unit_id": uid[0],
                "unit_sha256": uid[1],
                **dec,
            }
        )

    out_dir = package / RESOLUTION_OUTPUT / "final" / lane
    _private_directory(package, out_dir)

    labels_hash = atomic(out_dir / f"labels-{index:04d}.json", {"labels": ordered_labels})
    decisions_hash = atomic(out_dir / f"decisions-{index:04d}.json", {"decisions": ordered_decisions})

    custody_raw = (package / "custody-receipt.json").read_bytes()
    manifest_raw = (package / "manifest.json").read_bytes()
    manifest_val, _ = _read(package / "manifest.json")
    custody_val, _ = _read(package / "custody-receipt.json")

    expected_manifest_src = (
        SOURCE_MANIFEST_SHA256
        if not fixture
        else custody_val.get("source_label_manifest_raw_sha256", SOURCE_MANIFEST_SHA256)
    )
    expected_commitment = (
        ORDERED_IDENTITY_COMMITMENT_SHA256
        if not fixture
        else manifest_val.get("ordered_identity_commitment_sha256", ORDERED_IDENTITY_COMMITMENT_SHA256)
    )

    clean_count = len(clean_val.get("records", []))
    risk_count = len(risk_val.get("records", []))
    adj_count = len(adj_labels_val.get("labels", []))
    unres_count = len(adj_unres_val.get("records", []))

    body = {
        "schema_version": "phase3_cycle007_operator_resolution_packet_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest(custody_raw),
        "source_label_manifest_raw_sha256": expected_manifest_src,
        "manifest_raw_sha256": digest(manifest_raw),
        "ordered_identity_commitment_sha256": expected_commitment,
        "lane": lane,
        "packet_index": index,
        "row_count": len(rows),
        "labels_sha256": labels_hash,
        "decisions_sha256": decisions_hash,
        "compare_receipt_sha256": comp_receipt.get("receipt_sha256"),
        "adjudication_receipt_sha256": adj_receipt.get("receipt_sha256"),
        "clean_consensus_count": clean_count,
        "risk_consensus_count": risk_count,
        "adjudicated_count": adj_count,
        "operator_resolved_count": unres_count,
        "unresolved_remaining_count": 0,
        "authorization_receipt_raw_sha256": (
            authorization_metadata.get("authorization_receipt_raw_sha256")
            if isinstance(authorization_metadata, dict)
            else None
        ),
        "decision_authority": (
            authorization_metadata.get("decision_authority") if isinstance(authorization_metadata, dict) else None
        ),
        "authorized_identity": (
            authorization_metadata.get("authorized_identity") if isinstance(authorization_metadata, dict) else None
        ),
        "authority_attestation_raw_sha256": (
            authorization_metadata.get("authority_attestation_raw_sha256")
            if isinstance(authorization_metadata, dict)
            else None
        ),
        "nonce_consumption_sha256": (
            authorization_metadata.get("nonce_consumption_sha256") if isinstance(authorization_metadata, dict) else None
        ),
        "text_free": True,
    }
    body["receipt_sha256"] = digest(canonical(body))
    atomic(out_dir / f"receipt-{index:04d}.json", body)
    return body


def resolve_all(
    package: Path,
    authorization_path: Path | None = None,
    *,
    fixture: bool = False,
    advisor_response_path: Path | None = None,
    authority_attestation_path: Path | None = None,
    authority_root: Path | None = None,
    nonce_ledger: Path | None = None,
) -> dict[str, Any]:
    _directory(package, 0o700)

    # Validate package manifests
    custody_raw = (package / "custody-receipt.json").read_bytes()
    manifest_raw = (package / "manifest.json").read_bytes()
    custody_hash = digest(custody_raw)
    manifest_hash = digest(manifest_raw)
    manifest_val, _ = _read(package / "manifest.json")
    custody_val, _ = _read(package / "custody-receipt.json")

    # Validate upstream comparison batch receipt
    comp_batch_p = package / COMPARE_OUTPUT / "batch-receipt.json"
    _regular(comp_batch_p, 0o600)
    comp_batch, _ = _read(comp_batch_p)
    if (
        comp_batch.get("schema_version") != "phase3_cycle007_dual_label_batch_receipt_v1"
        or comp_batch.get("evaluation_cycle_id") != CYCLE
        or comp_batch.get("custody_receipt_raw_sha256") != custody_hash
        or comp_batch.get("manifest_raw_sha256") != manifest_hash
    ):
        raise Error("authorization_binding_failure")

    # Validate upstream adjudication batch receipt
    adj_batch_p = package / ADJUDICATION_OUTPUT / "batch-receipt.json"
    _regular(adj_batch_p, 0o600)
    adj_batch, _ = _read(adj_batch_p)
    if (
        adj_batch.get("schema_version") != "phase3_cycle007_dual_label_adjudication_batch_receipt_v1"
        or adj_batch.get("evaluation_cycle_id") != CYCLE
        or adj_batch.get("model_family") != "anthropic"
        or adj_batch.get("receipt_sha256")
        != digest(canonical({k: v for k, v in adj_batch.items() if k != "receipt_sha256"}))
    ):
        raise Error("upstream_receipt_drift")

    # Collect all unresolved identities across all packets
    all_unresolved_uids: set[tuple[str, str]] = set()
    all_unresolved_ordered: list[tuple[str, str]] = []
    all_unresolved_records: list[dict[str, Any]] = []
    all_resolved_uids: set[tuple[str, str]] = set()
    all_package_uids: set[tuple[str, str]] = set()

    expected_packets = [(item["lane"], item["packet_index"]) for item in manifest_val.get("packets", [])]
    if not expected_packets:
        expected_packets = [(lane, idx) for lane, count in LANES.items() for idx in range(1, count + 1)]

    for lane, index in expected_packets:
        p_path = package / lane / f"packet-{index:04d}.json"
        _regular(p_path, 0o600)
        p_val, _ = _read(p_path)
        for r in p_val.get("rows", []):
            all_package_uids.add((r["unit_id"], r["unit_sha256"]))

        c_p = package / COMPARE_OUTPUT / lane / f"clean-consensus-{index:04d}.json"
        r_p = package / COMPARE_OUTPUT / lane / f"risk-consensus-{index:04d}.json"
        _regular(c_p, 0o600)
        _regular(r_p, 0o600)
        c_val, _ = _read(c_p)
        r_val, _ = _read(r_p)
        for rec in c_val.get("records", []):
            all_resolved_uids.add((rec["source_row"]["unit_id"], rec["source_row"]["unit_sha256"]))
        for rec in r_val.get("records", []):
            all_resolved_uids.add((rec["source_row"]["unit_id"], rec["source_row"]["unit_sha256"]))

        adj_l_p = package / ADJUDICATION_OUTPUT / "final" / lane / f"labels-{index:04d}.json"
        adj_u_p = package / ADJUDICATION_OUTPUT / "final" / lane / f"unresolved-{index:04d}.json"
        _regular(adj_l_p, 0o600)
        _regular(adj_u_p, 0o600)
        adj_l_val, _ = _read(adj_l_p)
        adj_u_val, _ = _read(adj_u_p)
        for lbl in adj_l_val.get("labels", []):
            all_resolved_uids.add((lbl["unit_id"], lbl["unit_sha256"]))
        for rec in adj_u_val.get("records", []):
            uid = (rec["source_row"]["unit_id"], rec["source_row"]["unit_sha256"])
            all_unresolved_uids.add(uid)
            all_unresolved_ordered.append(uid)
            all_unresolved_records.append(rec)

    # Read and validate authorizations
    auth_path = authorization_path or (package / RESOLUTION_OUTPUT / "authorization.json")
    authorizations: AuthorizationBundle | dict[tuple[str, str], dict[str, Any]] = {}
    auth_payload_hash: str | None = None
    request_raw_sha256: str | None = None
    request_path = package / ADJUDICATION_OUTPUT / "operator-resolution-request.json"
    if all_unresolved_uids:
        if request_path.exists() or request_path.is_symlink():
            try:
                _request_value, request_raw = _validate_resolution_request(
                    request_path,
                    all_unresolved_records,
                    custody_hash=custody_hash,
                    manifest_hash=manifest_hash,
                    ordered_commitment=manifest_val.get(
                        "ordered_identity_commitment_sha256", ORDERED_IDENTITY_COMMITMENT_SHA256
                    ),
                )
            except Error as exc:
                raise Error(exc.failure_code) from exc
            request_raw_sha256 = digest(request_raw)
        elif not fixture:
            raise Error("authorization_binding_failure")

    if auth_path.exists():
        _regular(auth_path, 0o600)
        authorizations = validate_authorization_file(
            auth_path,
            package,
            request_raw_sha256=request_raw_sha256,
            fixture=fixture,
            advisor_response_path=advisor_response_path,
            authority_attestation_path=authority_attestation_path,
            authority_root=authority_root,
        )
        auth_uids = set(authorizations.keys())

        # Exact unresolved set check
        if auth_uids != all_unresolved_uids:
            extra = auth_uids - all_unresolved_uids
            if extra:
                if extra & all_resolved_uids:
                    raise Error("already_resolved_authorization")
                if extra - all_package_uids:
                    raise Error("foreign_authorization")
                raise Error("extra_authorization")
            missing = all_unresolved_uids - auth_uids
            if missing:
                raise Error("missing_authorization")
        if list(authorizations.keys()) != all_unresolved_ordered:
            raise Error("authorization_identity_failure")
        auth_payload_hash = authorizations.metadata["authorization_receipt_raw_sha256"]
    else:
        if all_unresolved_uids:
            raise Error("missing_authorization")

    if all_unresolved_uids and not fixture:
        if nonce_ledger is None or authority_root is None:
            raise Error("authorization_binding_failure")
        if not isinstance(authorizations, AuthorizationBundle):
            raise Error("authorization_binding_failure")
        try:
            if nonce_ledger.resolve(strict=True) == authority_root.resolve(strict=True):
                raise Error("authorization_binding_failure")
        except OSError as exc:
            raise Error("authorization_binding_failure") from exc
        nonce_consumption_sha256 = _consume_nonce(nonce_ledger, package, authorizations.metadata)
        authorizations.metadata["nonce_consumption_sha256"] = nonce_consumption_sha256

    receipts: list[dict[str, Any]] = []
    for lane, index in expected_packets:
        receipts.append(resolve_packet(package, lane, index, authorizations, fixture=fixture))

    out_root = package / RESOLUTION_OUTPUT
    _private_directory(package, out_root)

    expected_manifest_src = (
        SOURCE_MANIFEST_SHA256
        if not fixture
        else custody_val.get("source_label_manifest_raw_sha256", SOURCE_MANIFEST_SHA256)
    )
    expected_commitment = (
        ORDERED_IDENTITY_COMMITMENT_SHA256
        if not fixture
        else manifest_val.get("ordered_identity_commitment_sha256", ORDERED_IDENTITY_COMMITMENT_SHA256)
    )

    body = {
        "schema_version": "phase3_cycle007_operator_resolution_batch_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest(custody_raw),
        "source_label_manifest_raw_sha256": expected_manifest_src,
        "manifest_raw_sha256": digest(manifest_raw),
        "ordered_identity_commitment_sha256": expected_commitment,
        "packet_count": len(receipts),
        "total_rows": sum(r["row_count"] for r in receipts),
        "clean_consensus_count": sum(r["clean_consensus_count"] for r in receipts),
        "risk_consensus_count": sum(r["risk_consensus_count"] for r in receipts),
        "adjudicated_count": sum(r["adjudicated_count"] for r in receipts),
        "operator_resolved_count": sum(r["operator_resolved_count"] for r in receipts),
        "unresolved_remaining_count": 0,
        "packet_receipt_union_sha256": digest(canonical([r["receipt_sha256"] for r in receipts])),
        "authorization_payload_sha256": auth_payload_hash,
        "decision_authority": (
            authorizations.metadata.get("decision_authority")
            if isinstance(authorizations, AuthorizationBundle)
            else None
        ),
        "authorized_identity": (
            authorizations.metadata.get("authorized_identity")
            if isinstance(authorizations, AuthorizationBundle)
            else None
        ),
        "authority_attestation_raw_sha256": (
            authorizations.metadata.get("authority_attestation_raw_sha256")
            if isinstance(authorizations, AuthorizationBundle)
            else None
        ),
        "nonce_consumption_sha256": (
            authorizations.metadata.get("nonce_consumption_sha256")
            if isinstance(authorizations, AuthorizationBundle)
            else None
        ),
        "text_free": True,
    }
    body["receipt_sha256"] = digest(canonical(body))
    atomic(out_root / "batch-receipt.json", body)
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--lane", choices=tuple(LANES))
    parser.add_argument("--packet-index", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--advisor-response", type=Path)
    parser.add_argument(
        "--authority-attestation",
        type=Path,
        help="0600 external authority receipt bound to the authorization and exact unresolved request",
    )
    parser.add_argument(
        "--authority-root",
        type=Path,
        help="0700 operator-owned root containing external authority artifacts",
    )
    parser.add_argument(
        "--nonce-ledger",
        type=Path,
        help="separate 0700 operator-owned external directory for one-time authorization nonces",
    )
    args = parser.parse_args(argv)
    try:
        if args.all:
            result = resolve_all(
                args.package,
                args.authorization,
                fixture=args.fixture,
                advisor_response_path=args.advisor_response,
                authority_attestation_path=args.authority_attestation,
                authority_root=args.authority_root,
                nonce_ledger=args.nonce_ledger,
            )
        elif args.lane is not None and args.packet_index is not None:
            if not args.fixture:
                # The frozen live protocol resolves the complete emitted set.
                # A partial command could otherwise burn a valid authority
                # receipt without proving full unresolved-set coverage.
                raise Error("authorization_binding_failure")
            auth_path = args.authorization or (args.package / RESOLUTION_OUTPUT / "authorization.json")
            auths: AuthorizationBundle | dict[tuple[str, str], dict[str, Any]] = {}
            if auth_path.exists():
                unresolved_path = (
                    args.package
                    / ADJUDICATION_OUTPUT
                    / "final"
                    / args.lane
                    / f"unresolved-{args.packet_index:04d}.json"
                )
                unresolved_value, _ = _read(unresolved_path)
                unresolved_order = [
                    (item["source_row"]["unit_id"], item["source_row"]["unit_sha256"])
                    for item in unresolved_value.get("records", [])
                ]
                auths = validate_authorization_file(
                    auth_path,
                    args.package,
                    set(unresolved_order),
                    ordered_unresolved_identities=unresolved_order,
                    fixture=args.fixture,
                    advisor_response_path=args.advisor_response,
                    authority_attestation_path=args.authority_attestation,
                    authority_root=args.authority_root,
                )
            result = resolve_packet(args.package, args.lane, args.packet_index, auths, fixture=args.fixture)
        else:
            result = resolve_all(
                args.package,
                args.authorization,
                fixture=args.fixture,
                advisor_response_path=args.advisor_response,
                authority_attestation_path=args.authority_attestation,
                authority_root=args.authority_root,
                nonce_ledger=args.nonce_ledger,
            )
    except Error as exc:
        result = {"ok": False, "failure_code": exc.failure_code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "authorization_binding_failure", "text_free": True}
    else:
        result = {"ok": True, **result}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
