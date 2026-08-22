#!/usr/bin/env python3
"""Deterministic full-denominator comparison for Phase 3 Cycle 007 dual labels."""

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

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract
from scripts.projects.open_model_data import phase3_cycle007_evidence_validator as validator

ROOT = Path(__file__).resolve().parents[1]
CYCLE = "phase3-v2-1-evaluation-cycle-007"
EVALUATION_CYCLE_ID = CYCLE
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
CHUNK_SIZE = 20

GROK = {
    "root": "label-output-grok-cycle007-v1",
    "exact_model": "grok-4.5",
    "model_family": "xai",
    "harness": "native_grok",
}
GEMINI = {
    "root": "label-output-gemini-cycle007-v1",
    "exact_model": "Gemini 3.6 Flash (High)",
    "model_family": "google",
    "harness": "agy",
}
OUTPUT = "dual-label-output-cycle007-v1"
OUTPUT_ROOT = OUTPUT

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
        "label_count_or_envelope_drift",
        "identity_or_order_drift",
        "identity_uniqueness_drift",
        "clean_label_schema_drift",
        "clean_label_invariant_drift",
        "residual_label_schema_drift",
        "residual_phenomenon_drift",
        "residual_scored_decision_insufficiency",
        "residual_2019_positive_forbidden",
        "residual_taxonomy_order_or_uniqueness_drift",
        "residual_primary_or_rollup_drift",
        "residual_null_rollup_drift",
        "evidence_reference_invalid",
        "insufficient_evidence_for_decision",
        "missing_evidence_sidecar",
        "unsealed_provider_lane",
        "mode_drift",
    }
)


class Error(ValueError):
    def __init__(self, code: str):
        self.code = code if code in FAILURE_CODES else "label_count_or_envelope_drift"
        self.failure_code = self.code
        super().__init__(self.code)


class Invalid(Error):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise Invalid("label_count_or_envelope_drift")
        value[key] = item
    return value


def _regular(path: Path, mode: int | None = 0o600) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise Error("label_count_or_envelope_drift") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise Error("label_count_or_envelope_drift")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("mode_drift")


def _directory(path: Path, mode: int | None = 0o700) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise Error("label_count_or_envelope_drift") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise Error("label_count_or_envelope_drift")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("mode_drift")


def _private_directory(package: Path, path: Path) -> None:
    """Create a package subtree and enforce private modes on every new level."""
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    current = path
    while current != package:
        current.chmod(0o700)
        current = current.parent
    _directory(package, 0o700)


def read(path: Path, label: str = "sealed value") -> Any:
    try:
        _regular(path, 0o600)
        return json.loads(path.read_bytes().decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Invalid, Error):
        raise Error("label_count_or_envelope_drift") from None


def atomic(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _directory(path.parent, 0o700)
    data = canonical(value)
    if path.exists() or path.is_symlink():
        _regular(path, 0o600)
        if path.read_bytes() != data:
            raise Error("label_count_or_envelope_drift")
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


def semantic(label: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in label.items() if key not in {"unit_id", "unit_sha256"}}


def validate_clean_label(label: dict[str, Any], row: dict[str, Any], row_evidence: Mapping[str, Any]) -> None:
    if (
        not isinstance(label, dict)
        or set(label)
        != {"unit_id", "unit_sha256", "decision_code", "clean_modern_standard_prose", "modern_genre_id", "evidence_ids"}
        or label.get("decision_code") not in REJECTS
        or type(label.get("clean_modern_standard_prose")) is not bool
        or not isinstance(label.get("evidence_ids"), list)
    ):
        raise Invalid("clean_label_schema_drift")
    agrees = label["decision_code"] == "agree"
    if (
        agrees != label["clean_modern_standard_prose"]
        or (agrees and label["modern_genre_id"] not in GENRES)
        or (not agrees and label["modern_genre_id"] is not None)
    ):
        raise Invalid("clean_label_invariant_drift")
    evidence_ids = label["evidence_ids"]
    if evidence_ids != sorted(set(evidence_ids)):
        raise Invalid("evidence_reference_invalid")

    available_ids = set(row_evidence.get("evidence_ids", []))
    if set(evidence_ids) - available_ids:
        raise Invalid("evidence_reference_invalid")

    if agrees:
        try:
            validator.validate_label_evidence_refs(
                row_evidence,
                decision_code="agree",
                evidence_ids=evidence_ids,
                phenomenon_id=None,
            )
        except validator.EvidenceValidationError as exc:
            if exc.code == "insufficient_evidence_for_decision":
                raise Invalid("insufficient_evidence_for_decision") from exc
            raise Invalid("evidence_reference_invalid") from exc


def validate_residual_label(label: dict[str, Any], row: dict[str, Any], row_evidence: Mapping[str, Any]) -> None:
    if (
        not isinstance(label, dict)
        or set(label) != {"unit_id", "unit_sha256", "phenomena", "primary_phenomenon_id", "item_decision_rollup"}
        or not isinstance(label.get("phenomena"), list)
        or not label["phenomena"]
        or label.get("item_decision_rollup") not in DEC
    ):
        raise Invalid("residual_label_schema_drift")
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
            raise Invalid("residual_phenomenon_drift")
        if p["decision_code"] in {"positive", "acceptable_control", "protected"} and p["evidence_sufficiency"] != "sufficient":
            raise Invalid("residual_scored_decision_insufficiency")
        if row.get("family_id") == "pravopys_2019_complete" and p["decision_code"] == "positive":
            raise Invalid("residual_2019_positive_forbidden")
        p_ids = p["evidence_ids"]
        if p_ids != sorted(set(p_ids)):
            raise Invalid("evidence_reference_invalid")
        try:
            validator.validate_label_evidence_refs(
                row_evidence,
                decision_code=p["decision_code"],
                evidence_ids=p_ids,
                phenomenon_id=p["phenomenon_id"],
            )
        except validator.EvidenceValidationError as exc:
            if exc.code == "insufficient_evidence_for_decision":
                raise Invalid("insufficient_evidence_for_decision") from exc
            raise Invalid("evidence_reference_invalid") from exc
        names.append(p["phenomenon_id"])
        decisions[p["phenomenon_id"]] = p["decision_code"]
    if len(names) != len(set(names)) or names != sorted(names, key=TAX.index):
        raise Invalid("residual_taxonomy_order_or_uniqueness_drift")
    viable = [name for name in names if decisions[name] not in {"abstention", "disagreement"}]
    primary = label["primary_phenomenon_id"]
    if viable and (primary not in viable or label["item_decision_rollup"] != decisions[primary]):
        raise Invalid("residual_primary_or_rollup_drift")
    if not viable and (
        primary is not None
        or label["item_decision_rollup"] != ("disagreement" if "disagreement" in decisions.values() else "abstention")
    ):
        raise Invalid("residual_null_rollup_drift")


def validate_label(lane: str, label: dict[str, Any], row: dict[str, Any], row_evidence: Mapping[str, Any]) -> None:
    if (label.get("unit_id"), label.get("unit_sha256")) != (row.get("unit_id"), row.get("unit_sha256")):
        raise Invalid("identity_or_order_drift")
    if lane == "clean_label":
        validate_clean_label(label, row, row_evidence)
    elif lane == "residual_label":
        validate_residual_label(label, row, row_evidence)
    else:
        raise Invalid("label_count_or_envelope_drift")


def is_risk_triggered(
    row: dict[str, Any],
    row_evidence: Mapping[str, Any],
    grok_label: dict[str, Any],
    gemini_label: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Determine if a consensus row triggers source-authority risk review."""
    reasons: list[str] = []

    # 1. Negative control check
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

    # 2. VESUM miss or archaic-only form
    for record in evidence_records:
        if record.get("channel") == "vesum_attestation" and record.get("status") == "not_found" and "vesum_miss" not in reasons:
            reasons.append("vesum_miss")
        if record.get("supports") == "archaic_attestation" and "archaic_only_form" not in reasons:
            reasons.append("archaic_only_form")
    if (row_evidence.get("has_only_archaic_form") is True or row.get("has_only_archaic_form") is True) and "archaic_only_form" not in reasons:
        reasons.append("archaic_only_form")

    # 3. UA-GEC, Russian-shadow, or style-guide warnings
    for record in evidence_records:
        ch = record.get("channel")
        st = record.get("status")
        if ch == "ua_gec_calque" and st == "attested" and "ua_gec_warning" not in reasons:
            reasons.append("ua_gec_warning")
        elif ch == "russian_shadow_suspicion" and st == "attested" and "russian_shadow_warning" not in reasons:
            reasons.append("russian_shadow_warning")
        elif ch == "antonenko_style" and st == "attested" and "style_guide_warning" not in reasons:
            reasons.append("style_guide_warning")

    # 4. Heritage conflict or unresolved source results
    for record in evidence_records:
        ch = record.get("channel")
        st = record.get("status")
        if st in {"ambiguous", "incomplete", "parse_error", "unavailable"} and "unresolved_source_result" not in reasons:
            reasons.append("unresolved_source_result")
        if ch == "heritage_attestation" and st in {"ambiguous", "incomplete", "parse_error", "unavailable"} and "heritage_source_conflict" not in reasons:
            reasons.append("heritage_source_conflict")

    # 5. Missing normative rule (in residual lane)
    if "phenomena" in grok_label:
        pravopys_records = [r for r in evidence_records if r.get("channel") == "pravopys_2026_normative"]
        if (
            not pravopys_records
            or any(r.get("status") != "attested" or r.get("supports") == "no_conclusion" for r in pravopys_records)
        ) and "missing_normative_rule" not in reasons:
            reasons.append("missing_normative_rule")

    # 6. Insufficient or non-normative evidence cited
    if grok_label.get("decision_code") == "agree" and validator.classify_sufficiency(row_evidence) != "sufficient" and "insufficient_evidence_cited" not in reasons:
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


def _manifest(package: Path, *, strict: bool = False) -> dict[str, Any]:
    _directory(package, 0o700)
    value = read(package / "manifest.json", "manifest")
    custody_val = read(package / "custody-receipt.json", "custody receipt")
    custody_hash = digest((package / "custody-receipt.json").read_bytes())
    if not isinstance(value, dict) or not isinstance(custody_val, dict):
        raise Error("label_count_or_envelope_drift")
    if (
        value.get("schema_version") != "phase3_cycle007_materialization_manifest_v1"
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("source_evaluation_cycle_id") != "phase3-v2-1-evaluation-cycle-005"
        or value.get("custody_receipt_raw_sha256") != custody_hash
        or custody_val.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or custody_val.get("source_custody_receipt_raw_sha256") != SOURCE_CUSTODY_SHA256
        or custody_val.get("amendment_reference") != "batch_state/phase3-cycle007-source-grounded-amendment-v1.md"
        or value.get("text_free") is not True
        or not isinstance(value.get("packets"), list)
        or value.get("packet_count") != len(value["packets"])
    ):
        raise Error("label_count_or_envelope_drift")
    if strict and (value.get("packet_count") != PACKET_COUNT or value.get("row_count") != ROW_COUNT):
        raise Error("label_count_or_envelope_drift")
    return value


def _source_package_binding(
    custody_bytes: bytes, manifest_bytes: bytes, manifest: Mapping[str, Any], evidence_manifest: Mapping[str, Any]
) -> None:
    """Require the evidence compiler's exact live-package custody binding."""
    binding = evidence_manifest.get("source_package_binding")
    expected = {
        "source_evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-005",
        "custody_receipt_raw_sha256": digest(custody_bytes),
        "materialization_manifest_sha256": manifest.get("receipt_sha256"),
        "ordered_identity_commitment_sha256": manifest.get("ordered_identity_commitment_sha256"),
        "identity_union_commitment_sha256": manifest.get("identity_union_commitment_sha256"),
        "ordered_packet_commitment_sha256": manifest.get("ordered_packet_commitment_sha256"),
        "packet_count": manifest.get("packet_count"),
        "row_count": manifest.get("row_count"),
    }
    if (
        not isinstance(binding, dict)
        or not isinstance(manifest.get("receipt_sha256"), str)
        or manifest.get("receipt_sha256") != digest(canonical({key: value for key, value in manifest.items() if key != "receipt_sha256"}))
        or digest(manifest_bytes) == binding.get("materialization_manifest_sha256")
        or binding != expected
    ):
        raise Error("missing_evidence_sidecar")


def _evidence_manifest(package: Path, materialization_manifest: dict[str, Any]) -> dict[str, Any]:
    evidence_dir = package / "evidence"
    _directory(evidence_dir, 0o700)
    manifest_path = evidence_dir / "manifest.json"
    _regular(manifest_path, 0o600)
    manifest = read(manifest_path, "evidence manifest")
    expected_identity = {k: manifest.get(k) for k in validator._IDENTITY_FIELDS}
    try:
        validator.validate_manifest(manifest, expected_identity=expected_identity)
    except validator.EvidenceValidationError as exc:
        raise Error("missing_evidence_sidecar") from exc
    _source_package_binding(
        (package / "custody-receipt.json").read_bytes(),
        (package / "manifest.json").read_bytes(),
        materialization_manifest,
        manifest,
    )
    return manifest


def _validate_evidence_coverage(
    package: Path, materialization_manifest: Mapping[str, Any], evidence_manifest: Mapping[str, Any]
) -> None:
    """Bind every manifest packet to one exact indexed sidecar and its rows."""
    packets = materialization_manifest.get("packets")
    entries = evidence_manifest.get("sidecars")
    if not isinstance(packets, list) or not isinstance(entries, list) or len(entries) != len(packets):
        raise Error("missing_evidence_sidecar")
    seen_packet_keys: set[tuple[str, int]] = set()
    seen_sidecar_indexes: set[int] = set()
    for packet_entry in packets:
        if not isinstance(packet_entry, dict):
            raise Error("missing_evidence_sidecar")
        lane, index = packet_entry.get("lane"), packet_entry.get("packet_index")
        if not isinstance(lane, str) or not isinstance(index, int) or (lane, index) in seen_packet_keys:
            raise Error("missing_evidence_sidecar")
        seen_packet_keys.add((lane, index))
        packet_path, packet = _packet(package, lane, index, materialization_manifest)
        binding = {
            "canonical_basename": packet_path.name,
            "raw_sha256": digest(packet_path.read_bytes()),
            "packet_identity_set_sha256": packet.get("packet_identity_set_sha256"),
        }
        matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("lane") == lane and entry.get("packet_binding") == binding]
        if len(matches) != 1:
            raise Error("missing_evidence_sidecar")
        entry = matches[0]
        sidecar_index = entry.get("packet_index")
        if not isinstance(sidecar_index, int) or sidecar_index < 1 or sidecar_index in seen_sidecar_indexes:
            raise Error("missing_evidence_sidecar")
        seen_sidecar_indexes.add(sidecar_index)
        sidecar_path = package / "evidence" / f"sidecar-{sidecar_index:04d}.json"
        _regular(sidecar_path, 0o600)
        sidecar = read(sidecar_path, f"sidecar {sidecar_index}")
        if (
            entry.get("row_count") != len(packet.get("rows", []))
            or entry.get("sidecar_sha256") != digest(sidecar_path.read_bytes())
            or entry.get("sidecar_id") != sidecar.get("sidecar_id")
            or sidecar.get("lane") != lane
            or sidecar.get("packet_binding") != binding
            or sidecar.get("row_count") != len(packet.get("rows", []))
            or not isinstance(sidecar.get("rows"), list)
        ):
            raise Error("missing_evidence_sidecar")
        packet_ids = [(row.get("unit_id"), row.get("unit_sha256")) for row in packet["rows"]]
        sidecar_ids = [(row.get("unit_id"), row.get("unit_sha256")) for row in sidecar["rows"]]
        if len(packet_ids) != len(set(packet_ids)) or sidecar_ids != packet_ids:
            raise Error("missing_evidence_sidecar")


def _packet(package: Path, lane: str, index: int, manifest_value: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    path = package / lane / f"packet-{index:04d}.json"
    _regular(path, 0o600)
    contents = read(path, f"packet {lane}/{index}")
    if not isinstance(contents, dict) or not isinstance(contents.get("rows"), list):
        raise Error("identity_or_order_drift")
    matches = [
        item
        for item in manifest_value["packets"]
        if isinstance(item, dict) and item.get("lane") == lane and item.get("packet_index") == index
    ]
    if len(matches) != 1:
        raise Error("identity_or_order_drift")
    expected = {
        "lane": lane,
        "packet_index": index,
        "canonical_basename": path.name,
        "row_count": len(contents["rows"]),
        "raw_sha256": digest(path.read_bytes()),
        "packet_identity_set_sha256": contents.get("packet_identity_set_sha256"),
    }
    if matches[0] != expected:
        raise Error("identity_or_order_drift")
    return path, contents


def _sidecar(
    package: Path,
    lane: str,
    index: int,
    packet_path: Path,
    packet: dict[str, Any],
    evidence_manifest: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    matching_entries = [
        entry
        for entry in evidence_manifest["sidecars"]
        if isinstance(entry, dict)
        and entry.get("lane") == lane
        and entry.get("packet_binding")
        == {
            "canonical_basename": packet_path.name,
            "raw_sha256": digest(packet_path.read_bytes()),
            "packet_identity_set_sha256": packet.get("packet_identity_set_sha256"),
        }
    ]
    if len(matching_entries) != 1:
        raise Error("missing_evidence_sidecar")

    sidecar_entry = matching_entries[0]
    sidecar_packet_index = sidecar_entry["packet_index"]
    sidecar_path = package / "evidence" / f"sidecar-{sidecar_packet_index:04d}.json"
    _regular(sidecar_path, 0o600)
    sidecar = read(sidecar_path, f"sidecar {sidecar_packet_index}")
    expected_identity = {k: sidecar.get(k) for k in validator._IDENTITY_FIELDS}
    try:
        validator.validate_sidecar(sidecar, expected_identity=expected_identity)
    except validator.EvidenceValidationError as exc:
        raise Error("missing_evidence_sidecar") from exc
    if (
        sidecar_entry.get("row_count") != len(packet.get("rows", []))
        or sidecar_entry.get("sidecar_sha256") != digest(sidecar_path.read_bytes())
        or sidecar_entry.get("sidecar_id") != sidecar.get("sidecar_id")
        or sidecar.get("packet_binding") != sidecar_entry.get("packet_binding")
        or sidecar.get("row_count") != len(packet.get("rows", []))
    ):
        raise Error("missing_evidence_sidecar")
    packet_ids = [(row.get("unit_id"), row.get("unit_sha256")) for row in packet.get("rows", [])]
    sidecar_ids = [(row.get("unit_id"), row.get("unit_sha256")) for row in sidecar.get("rows", [])]
    if len(packet_ids) != len(set(packet_ids)) or sidecar_ids != packet_ids:
        raise Error("missing_evidence_sidecar")
    return sidecar_path, sidecar


def _receipt_common(
    provider: dict[str, str],
    package: Path,
    lane: str,
    index: int,
    contents: dict[str, Any],
    packet_path: Path,
    sidecar_path: Path,
    sidecar: Mapping[str, Any],
) -> tuple[dict[str, Any], Path, Path, dict[str, Any]]:
    out = package / provider["root"] / lane
    _directory(package / provider["root"], 0o700)
    _directory(out, 0o700)
    labels_path = out / f"labels-{index:04d}.json"
    receipt_path = out / f"receipt-{index:04d}.json"
    _regular(labels_path, 0o600)
    _regular(receipt_path, 0o600)
    value = read(receipt_path, "provider receipt")
    if not isinstance(value, dict):
        raise Error("label_count_or_envelope_drift")
    common = {
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "materialization_manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "evidence_manifest_raw_sha256": digest((package / "evidence" / "manifest.json").read_bytes()),
        "lane": lane,
        "packet_index": index,
        "row_count": len(contents["rows"]),
        "packet_raw_sha256": digest(packet_path.read_bytes()),
        "packet_identity_set_sha256": contents.get("packet_identity_set_sha256"),
        "sidecar_raw_sha256": digest(sidecar_path.read_bytes()),
        "sidecar_id": sidecar.get("sidecar_id"),
        "labels_sha256": digest(labels_path.read_bytes()),
        "exact_model": provider["exact_model"],
        "model_family": provider["model_family"],
        "harness": provider["harness"],
        "text_free": True,
    }
    return value, labels_path, receipt_path, common


def _verify_grok(
    package: Path,
    lane: str,
    index: int,
    contents: dict[str, Any],
    packet_path: Path,
    sidecar: dict[str, Any],
) -> list[dict[str, Any]]:
    sidecar_path, _bound_sidecar = _sidecar(
        package, lane, index, packet_path, contents, _evidence_manifest(package, _manifest(package))
    )
    value, labels_path, _receipt_path, common = _receipt_common(
        GROK, package, lane, index, contents, packet_path, sidecar_path, sidecar
    )
    raw_path = package / GROK["root"] / lane / f"raw-{index:04d}.raw"
    raw_manifest_path = package / GROK["root"] / lane / f"raw-manifest-{index:04d}.json"
    prompt_path = package / "prompts" / f"grok-{'clean' if lane == 'clean_label' else 'residual'}-label.md"
    _regular(raw_path, 0o600)
    _regular(raw_manifest_path, 0o600)
    _regular(prompt_path, 0o600)
    expected = {
        "schema_version": "phase3_cycle007_grok_packet_label_receipt_v1",
        **common,
        "raw_manifest_sha256": digest(raw_manifest_path.read_bytes()),
        "response_raw_sha256": digest(raw_path.read_bytes()),
        "prompt_path": prompt_path.relative_to(package).as_posix(),
        "prompt_sha256": digest(prompt_path.read_bytes()),
        "attempt_count": value.get("attempt_count"),
    }
    if (
        value.get("attempt_count") not in {1, 2}
        or set(value) != set(expected) | {"receipt_sha256"}
        or any(value.get(key) != expected_value for key, expected_value in expected.items())
        or value.get("receipt_sha256") != digest(canonical(expected))
    ):
        raise Error("label_count_or_envelope_drift")
    labels = read(labels_path, "grok labels")
    if not isinstance(labels, dict) or "labels" not in labels or not isinstance(labels["labels"], list):
        raise Error("label_count_or_envelope_drift")
    if len(labels["labels"]) != len(contents["rows"]):
        raise Error("label_count_or_envelope_drift")

    sidecar_by_id = {(r["unit_id"], r["unit_sha256"]): r for r in sidecar.get("rows", [])}
    for row, label in zip(contents["rows"], labels["labels"], strict=True):
        row_ev = sidecar_by_id.get((row["unit_id"], row["unit_sha256"]))
        if row_ev is None:
            raise Error("missing_evidence_sidecar")
        validate_label(lane, label, row, row_ev)
    return labels["labels"]


def _verify_gemini(
    package: Path,
    lane: str,
    index: int,
    contents: dict[str, Any],
    packet_path: Path,
    sidecar: dict[str, Any],
) -> list[dict[str, Any]]:
    sidecar_path, _bound_sidecar = _sidecar(
        package, lane, index, packet_path, contents, _evidence_manifest(package, _manifest(package))
    )
    value, labels_path, _receipt_path, common = _receipt_common(
        GEMINI, package, lane, index, contents, packet_path, sidecar_path, sidecar
    )
    raw_manifest_path = package / GEMINI["root"] / lane / f"raw-manifest-{index:04d}.json"
    _regular(raw_manifest_path, 0o600)
    expected = {
        "schema_version": "phase3_cycle007_gemini_packet_label_receipt_v1",
        **common,
        "raw_manifest_sha256": digest(raw_manifest_path.read_bytes()),
        "chunk_count": (len(contents["rows"]) + CHUNK_SIZE - 1) // CHUNK_SIZE,
    }
    if (
        set(value) != set(expected) | {"receipt_sha256"}
        or any(value.get(key) != expected_value for key, expected_value in expected.items())
        or value.get("receipt_sha256") != digest(canonical(expected))
    ):
        raise Error("label_count_or_envelope_drift")
    labels = read(labels_path, "gemini labels")
    if not isinstance(labels, dict) or "labels" not in labels or not isinstance(labels["labels"], list):
        raise Error("label_count_or_envelope_drift")
    if len(labels["labels"]) != len(contents["rows"]):
        raise Error("label_count_or_envelope_drift")

    sidecar_by_id = {(r["unit_id"], r["unit_sha256"]): r for r in sidecar.get("rows", [])}
    for row, label in zip(contents["rows"], labels["labels"], strict=True):
        row_ev = sidecar_by_id.get((row["unit_id"], row["unit_sha256"]))
        if row_ev is None:
            raise Error("missing_evidence_sidecar")
        validate_label(lane, label, row, row_ev)
    return labels["labels"]


def inputs(
    package: Path,
    lane: str,
    index: int,
    manifest_value: dict[str, Any] | None = None,
    evidence_manifest: dict[str, Any] | None = None,
    *,
    verify_coverage: bool = True,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    val = manifest_value or _manifest(package)
    ev_val = evidence_manifest or _evidence_manifest(package, val)
    if verify_coverage:
        _validate_evidence_coverage(package, val, ev_val)
    packet_path, contents = _packet(package, lane, index, val)
    _sidecar_path, sidecar = _sidecar(package, lane, index, packet_path, contents, ev_val)
    grok = _verify_grok(package, lane, index, contents, packet_path, sidecar)
    gemini = _verify_gemini(package, lane, index, contents, packet_path, sidecar)
    if len(grok) != len(gemini) or len(grok) != len(contents["rows"]):
        raise Error("label_count_or_envelope_drift")
    return contents, sidecar, grok, gemini


def compare(
    package: Path,
    lane: str,
    index: int,
    prepared: tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    if lane not in LANES or index < 1:
        raise Error("label_count_or_envelope_drift")
    contents, sidecar, grok, gemini = prepared or inputs(package, lane, index)
    sidecar_by_id = {(r["unit_id"], r["unit_sha256"]): r for r in sidecar.get("rows", [])}

    clean_consensus: list[dict[str, Any]] = []
    risk_consensus: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []

    for source, left, right in zip(contents["rows"], grok, gemini, strict=True):
        identity = (source["unit_id"], source["unit_sha256"])
        if (left.get("unit_id"), left.get("unit_sha256")) != identity or (
            right.get("unit_id"),
            right.get("unit_sha256"),
        ) != identity:
            raise Error("identity_or_order_drift")
        row_ev = sidecar_by_id.get(identity)
        if row_ev is None:
            raise Error("missing_evidence_sidecar")

        if semantic(left) == semantic(right):
            is_risk, reasons = is_risk_triggered(source, row_ev, left, right)
            if is_risk:
                risk_consensus.append(
                    {
                        "source_row": source,
                        "label": left,
                        "risk_reasons": reasons,
                    }
                )
            else:
                clean_consensus.append(
                    {
                        "source_row": source,
                        "label": left,
                    }
                )
        else:
            disagreements.append(
                {
                    "source_row": source,
                    "grok_label": left,
                    "gemini_label": right,
                }
            )

    out = package / OUTPUT / lane
    _private_directory(package, out)

    clean_hash = atomic(out / f"clean-consensus-{index:04d}.json", {"records": clean_consensus})
    risk_hash = atomic(out / f"risk-consensus-{index:04d}.json", {"records": risk_consensus})
    disagreements_hash = atomic(out / f"disagreements-{index:04d}.json", {"records": disagreements})

    manifest_value = _manifest(package)
    evidence_manifest = _evidence_manifest(package, manifest_value)
    packet_path, packet_contents = _packet(package, lane, index, manifest_value)
    sidecar_path, bound_sidecar = _sidecar(package, lane, index, packet_path, packet_contents, evidence_manifest)
    if bound_sidecar != sidecar:
        raise Error("missing_evidence_sidecar")

    body = {
        "schema_version": "phase3_cycle007_dual_label_packet_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "row_count": len(contents["rows"]),
        "packet_identity_set_sha256": contents.get("packet_identity_set_sha256"),
        "sidecar_id": sidecar.get("sidecar_id"),
        "sidecar_sha256": digest(sidecar_path.read_bytes()),
        "grok": {key: GROK[key] for key in ("exact_model", "model_family", "harness")},
        "gemini": {key: GEMINI[key] for key in ("exact_model", "model_family", "harness")},
        "clean_consensus_count": len(clean_consensus),
        "risk_triggered_consensus_count": len(risk_consensus),
        "disagreement_count": len(disagreements),
        "clean_consensus_sha256": clean_hash,
        "risk_consensus_sha256": risk_hash,
        "disagreements_sha256": disagreements_hash,
        "silent_selection": False,
        "text_free": True,
    }
    body["receipt_sha256"] = digest(canonical(body))
    atomic(out / f"receipt-{index:04d}.json", body)
    return body


def compare_all(package: Path, *, fixture: bool = False) -> dict[str, Any]:
    val = _manifest(package, strict=not fixture)
    ev_val = _evidence_manifest(package, val)
    _validate_evidence_coverage(package, val, ev_val)
    expected_packets = {(item.get("lane"), item.get("packet_index")) for item in val["packets"] if isinstance(item, dict)}

    prepared: dict[tuple[str, int], tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]] = {}
    for lane, index in expected_packets:
        prepared[(lane, index)] = inputs(package, lane, index, val, ev_val, verify_coverage=False)

    receipts: list[dict[str, Any]] = []
    for lane, index in sorted(expected_packets):
        packet_prepared = prepared[(lane, index)]
        receipts.append(compare(package, lane, index, packet_prepared))

    if not fixture and sum(item["row_count"] for item in receipts) != ROW_COUNT:
        raise Error("label_count_or_envelope_drift")

    body = {
        "schema_version": "phase3_cycle007_dual_label_batch_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "packet_count": len(receipts),
        "row_count": sum(item["row_count"] for item in receipts),
        "clean_consensus_count": sum(item["clean_consensus_count"] for item in receipts),
        "risk_triggered_consensus_count": sum(item["risk_triggered_consensus_count"] for item in receipts),
        "disagreement_count": sum(item["disagreement_count"] for item in receipts),
        "packet_receipt_union_sha256": digest(canonical([item["receipt_sha256"] for item in receipts])),
        "grok": {key: GROK[key] for key in ("exact_model", "model_family", "harness")},
        "gemini": {key: GEMINI[key] for key in ("exact_model", "model_family", "harness")},
        "silent_selection": False,
        "text_free": True,
    }
    batch_path = package / OUTPUT / "batch-receipt.json"
    body["receipt_sha256"] = digest(canonical(body))
    atomic(batch_path, body)
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--lane", choices=tuple(LANES))
    parser.add_argument("--packet-index", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--fixture", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.all:
            result = compare_all(args.package, fixture=args.fixture)
        elif args.lane is not None and args.packet_index is not None:
            result = compare(args.package, args.lane, args.packet_index)
        else:
            raise Error("label_count_or_envelope_drift")
    except Error as exc:
        result = {"ok": False, "failure_code": exc.failure_code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "label_count_or_envelope_drift", "text_free": True}
    else:
        result = {"ok": True, **result}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
