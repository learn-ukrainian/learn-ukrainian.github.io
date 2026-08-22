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
            any(r.get("status") != "attested" or r.get("supports") == "no_conclusion" for r in pravopys_records)
            and "missing_normative_rule" not in reasons
        ):
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
        custody.get("schema_version") != "phase3_cycle007_custody_receipt_v1"
        or custody.get("evaluation_cycle_id") != CYCLE
        or custody.get("source_evaluation_cycle_id") != SOURCE_CYCLE
        or custody.get("source_custody_receipt_raw_sha256") != expected_custody_src
        or custody.get("source_label_manifest_raw_sha256") != expected_manifest_src
        or custody.get("ordered_identity_commitment_sha256") != expected_commitment
        or custody.get("packet_count") != expected_packet_count
        or custody.get("row_count") != expected_row_count
        or custody.get("provider_artifacts_copied") is not False
        or custody.get("labels_copied") is not False
        or custody.get("responses_copied") is not False
    ):
        raise Error("source_manifest_binding")

    if (
        manifest.get("schema_version") != "phase3_cycle007_materialization_manifest_v1"
        or manifest.get("evaluation_cycle_id") != CYCLE
        or manifest.get("source_evaluation_cycle_id") != SOURCE_CYCLE
        or manifest.get("custody_receipt_raw_sha256") != custody_hash
        or manifest.get("ordered_identity_commitment_sha256") != expected_commitment
        or manifest.get("packet_count") != expected_packet_count
        or manifest.get("row_count") != expected_row_count
        or manifest.get("text_free") is not True
        or not isinstance(manifest.get("packets"), list)
        or len(manifest["packets"]) != expected_packet_count
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

    sidecar_by_uid: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in sidecars:
        p_idx = entry["packet_index"]
        s_path = package / "evidence" / f"sidecar-{p_idx:04d}.json"
        _regular(s_path)
        s_data, _ = _read_json(s_path)
        try:
            validator.validate_sidecar(s_data, expected_identity=expected_identity)
        except validator.EvidenceValidationError as exc:
            raise Error("evidence_validation_failed") from exc
        for r in s_data.get("rows", []):
            sidecar_by_uid[(r["unit_id"], r["unit_sha256"])] = r

    # 4. Check packets and row order
    ordered_identities: list[list[Any]] = []
    seen_identities: list[tuple[str, str]] = []
    packet_data_lookup: dict[tuple[str, int], dict[str, Any]] = {}

    for packet_record in manifest["packets"]:
        lane = packet_record["lane"]
        idx = packet_record["packet_index"]
        packet_path = package / lane / f"packet-{idx:04d}.json"
        _regular(packet_path)
        p_data, p_raw = _read_json(packet_path)
        packet_data_lookup[(lane, idx)] = p_data
        if digest(p_raw) != packet_record["raw_sha256"]:
            raise Error("exact_packet_denominator")
        for r_idx, row in enumerate(p_data.get("rows", [])):
            uid = (row["unit_id"], row["unit_sha256"])
            ordered_identities.append([lane, idx, r_idx, uid[0], uid[1]])
            seen_identities.append(uid)

    if len(seen_identities) != expected_row_count or len(seen_identities) != len(set(seen_identities)):
        raise Error("ordered_identity_denominator")

    recomputed_commitment = digest(canonical(ordered_identities))
    if recomputed_commitment != expected_commitment:
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
            if (
                rcpt_val.get("evaluation_cycle_id") != CYCLE
                or rcpt_val.get("exact_model") != expected_spec["exact_model"]
                or rcpt_val.get("model_family") != expected_spec["model_family"]
                or rcpt_val.get("harness") != expected_spec["harness"]
                or rcpt_val.get("labels_sha256") != digest(lbl_raw)
                or rcpt_val.get("receipt_sha256")
                != digest(canonical({k: v for k, v in rcpt_val.items() if k != "receipt_sha256"}))
            ):
                raise Error("provider_receipt_coverage")
            labels_list = lbl_val.get("labels", [])
            p_rows = packet_data_lookup[(lane, idx)]["rows"]
            if len(labels_list) != len(p_rows):
                raise Error("provider_receipt_coverage")
            for row, lbl in zip(p_rows, labels_list, strict=True):
                r_ev = sidecar_by_uid.get((row["unit_id"], row["unit_sha256"]))
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

    # 7. Recompute and Check Consensus Audit
    sample_doc_p = package / AUDIT_ROOT / "clean-consensus-sample.json"
    risk_rcpt_p = package / AUDIT_ROOT / "risk-review-receipt.json"
    clean_rcpt_p = package / AUDIT_ROOT / "clean-audit-receipt.json"
    audit_batch_path = package / AUDIT_ROOT / "batch-receipt.json"

    if (
        not sample_doc_p.exists()
        or not risk_rcpt_p.exists()
        or not clean_rcpt_p.exists()
        or not audit_batch_path.exists()
    ):
        raise Error("sample_audit_incomplete")

    sample_doc, _ = _read_json(sample_doc_p)
    risk_rcpt, _ = _read_json(risk_rcpt_p)
    clean_rcpt, _ = _read_json(clean_rcpt_p)
    audit_batch, _ = _read_json(audit_batch_path)

    recomputed_seed = digest(
        f"phase3-cycle007-consensus-audit-v1\n{custody_hash}{manifest_hash}{expected_commitment}".encode()
    )
    if sample_doc.get("seed") != recomputed_seed:
        raise Error("sample_audit_incomplete")

    # Recompute stratified sampling
    for r in all_clean_records:
        u_id = r["source_row"]["unit_id"]
        u_sha = r["source_row"]["unit_sha256"]
        r["rank"] = digest(f"{recomputed_seed}{r['lane']}{u_id}{u_sha}".encode())

    strata: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in all_clean_records:
        lane = r["lane"]
        lbl = r["label"]
        if lane == "clean_label":
            code = lbl.get("decision_code", "unknown")
            strata[f"clean:{code}"].append(r)
        elif lane == "residual_label":
            for p in lbl.get("phenomena", []):
                p_id = p.get("phenomenon_id", "unknown")
                p_code = p.get("decision_code", "unknown")
                strata[f"residual:{p_id}:{p_code}"].append(r)

    selected_by_unit: dict[tuple[str, str], dict[str, Any]] = {}
    for _s_name, s_rows in sorted(strata.items()):
        sorted_s = sorted(s_rows, key=lambda x: x["rank"])
        for row in sorted_s[:10]:
            uid = (row["source_row"]["unit_id"], row["source_row"]["unit_sha256"])
            if uid not in selected_by_unit:
                selected_by_unit[uid] = row

    mandatory_union = list(selected_by_unit.values())
    pop_count = len(all_clean_records)
    if pop_count <= 600:
        sample = sorted(all_clean_records, key=lambda x: x["rank"])
    elif len(mandatory_union) >= 600:
        sample = mandatory_union
    else:
        rem = [
            r
            for r in all_clean_records
            if (r["source_row"]["unit_id"], r["source_row"]["unit_sha256"]) not in selected_by_unit
        ]
        rem_sorted = sorted(rem, key=lambda x: x["rank"])
        sample = mandatory_union + rem_sorted[: 600 - len(mandatory_union)]

    sample_sorted = sorted(
        sample, key=lambda x: (x["lane"], x["source_row"]["unit_id"], x["source_row"]["unit_sha256"])
    )
    recomputed_sample_commitment = digest(
        canonical([(r["source_row"]["unit_id"], r["source_row"]["unit_sha256"]) for r in sample_sorted])
    )

    if (
        sample_doc.get("sample_identity_commitment_sha256") != recomputed_sample_commitment
        or sample_doc.get("audited_count") != len(sample_sorted)
        or sample_doc.get("population_count") != pop_count
        or sample_doc.get("receipt_sha256")
        != digest(canonical({k: v for k, v in sample_doc.items() if k != "receipt_sha256"}))
    ):
        raise Error("sample_audit_incomplete")

    if (
        risk_rcpt.get("risk_population_count") != len(all_risk_records)
        or risk_rcpt.get("reviewed_count") != len(all_risk_records)
        or risk_rcpt.get("terminal_findings_count") != 0
        or risk_rcpt.get("receipt_sha256")
        != digest(canonical({k: v for k, v in risk_rcpt.items() if k != "receipt_sha256"}))
    ):
        raise Error("risk_review_incomplete")

    if (
        clean_rcpt.get("clean_population_count") != pop_count
        or clean_rcpt.get("audited_count") != len(sample_sorted)
        or clean_rcpt.get("terminal_findings_count") != 0
        or clean_rcpt.get("receipt_sha256")
        != digest(canonical({k: v for k, v in clean_rcpt.items() if k != "receipt_sha256"}))
    ):
        raise Error("sample_audit_incomplete")

    if (
        audit_batch.get("schema_version") != "phase3_cycle007_consensus_audit_batch_receipt_v1"
        or audit_batch.get("evaluation_cycle_id") != CYCLE
        or audit_batch.get("passed") is not True
        or audit_batch.get("terminal_findings_count") != 0
        or audit_batch.get("receipt_sha256")
        != digest(canonical({k: v for k, v in audit_batch.items() if k != "receipt_sha256"}))
        or audit_batch.get("text_free") is not True
    ):
        raise Error("terminal_audit_finding")

    # Re-verify terminal findings on risk and sample rows
    for r in all_risk_records + sample_sorted:
        source_row = r["source_row"]
        lbl = r["label"]
        is_neg = (
            source_row.get("is_negative_control") is True
            or source_row.get("negative_control") is True
            or source_row.get("is_russianism_control") is True
            or source_row.get("is_surzhyk_control") is True
            or source_row.get("control_type") in {"russianism", "surzhyk", "source_conflict"}
            or source_row.get("family_id") in {"russianism", "surzhyk", "source_conflict"}
        )
        if is_neg:
            if lbl.get("decision_code") == "agree":
                raise Error("terminal_audit_finding")
            if "phenomena" in lbl and any(p.get("decision_code") == "positive" for p in lbl.get("phenomena", [])):
                raise Error("terminal_audit_finding")

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
        "ordered_identity_commitment_sha256": expected_commitment,
        "packet_count": expected_packet_count,
        "row_count": expected_row_count,
        "clean_consensus_count": len(all_clean_records),
        "risk_triggered_consensus_count": len(all_risk_records),
        "disagreement_count": len(all_disagreements),
        "audited_consensus_count": len(sample_sorted),
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
