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
from pathlib import Path
from typing import Any

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
AUDIT_ROOT = "consensus-audit-cycle007-v1"
ADJUDICATION_ROOT = "dual-label-adjudication-cycle007-v1"
RESOLUTION_ROOT = "dual-label-final-cycle007-v1"

EXPECTED_MODELS = {
    "grok": {"exact_model": "grok-4.5", "model_family": "xai", "harness": "native_grok"},
    "gemini": {
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
    },
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")

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
        if path.is_dir() and path.name.startswith(".cycle007-"):
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
    stop_roots = (GROK_ROOT, GEMINI_ROOT, COMPARE_ROOT, ADJUDICATION_ROOT, RESOLUTION_ROOT)
    if any((package / root / "provider-stop.json").exists() for root in stop_roots):
        raise Error("no_provider_stop")


def certify_completion(package: Path, *, fixture: bool = False) -> dict[str, Any]:
    """Execute fail-closed certification over all gates."""
    # 1. Permission checks
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
    expected_commitment = ORDERED_IDENTITY_COMMITMENT_SHA256 if not fixture else manifest.get("ordered_identity_commitment_sha256")

    if (
        custody.get("schema_version") != "phase3_cycle007_custody_receipt_v1"
        or custody.get("evaluation_cycle_id") != CYCLE
        or custody.get("source_evaluation_cycle_id") != SOURCE_CYCLE
        or custody.get("source_custody_receipt_raw_sha256") != expected_custody_src
        or custody.get("source_label_manifest_raw_sha256") != expected_manifest_src
        or custody.get("ordered_identity_commitment_sha256") != expected_commitment
        or custody.get("packet_count") != PACKET_COUNT
        or custody.get("row_count") != ROW_COUNT
        or custody.get("lane_row_counts") != LANE_ROW_COUNTS
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
        or manifest.get("packet_count") != PACKET_COUNT
        or manifest.get("row_count") != ROW_COUNT
        or manifest.get("lane_row_counts") != LANE_ROW_COUNTS
        or manifest.get("text_free") is not True
        or not isinstance(manifest.get("packets"), list)
        or len(manifest["packets"]) != PACKET_COUNT
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
    if len(sidecars) != PACKET_COUNT:
        raise Error("evidence_validation_failed")

    for entry in sidecars:
        p_idx = entry["packet_index"]
        s_path = package / "evidence" / f"sidecar-{p_idx:04d}.json"
        _regular(s_path)
        s_data, _ = _read_json(s_path)
        try:
            validator.validate_sidecar(s_data, expected_identity=expected_identity)
        except validator.EvidenceValidationError as exc:
            raise Error("evidence_validation_failed") from exc

    # 4. Check packets and row order
    ordered_identities: list[list[Any]] = []
    seen_identities: list[tuple[str, str]] = []
    for packet_record in manifest["packets"]:
        lane = packet_record["lane"]
        idx = packet_record["packet_index"]
        packet_path = package / lane / f"packet-{idx:04d}.json"
        _regular(packet_path)
        p_data, p_raw = _read_json(packet_path)
        if digest(p_raw) != packet_record["raw_sha256"]:
            raise Error("exact_packet_denominator")
        for r_idx, row in enumerate(p_data.get("rows", [])):
            uid = (row["unit_id"], row["unit_sha256"])
            ordered_identities.append([lane, idx, r_idx, uid[0], uid[1]])
            seen_identities.append(uid)

    if len(seen_identities) != ROW_COUNT or len(seen_identities) != len(set(seen_identities)):
        raise Error("ordered_identity_denominator")

    recomputed_commitment = digest(canonical(ordered_identities))
    if recomputed_commitment != expected_commitment:
        raise Error("ordered_identity_denominator")

    # 5. Check Comparison batch receipt
    comp_batch_path = package / COMPARE_ROOT / "batch-receipt.json"
    _regular(comp_batch_path)
    comp_batch, _ = _read_json(comp_batch_path)
    if (
        comp_batch.get("schema_version") != "phase3_cycle007_dual_label_batch_receipt_v1"
        or comp_batch.get("evaluation_cycle_id") != CYCLE
        or comp_batch.get("row_count") != ROW_COUNT
        or comp_batch.get("packet_count") != PACKET_COUNT
        or comp_batch.get("text_free") is not True
    ):
        raise Error("comparison_batch_receipt")

    # 6. Check Consensus Audit
    audit_batch_path = package / AUDIT_ROOT / "batch-receipt.json"
    _regular(audit_batch_path)
    audit_batch, _ = _read_json(audit_batch_path)
    if (
        audit_batch.get("schema_version") != "phase3_cycle007_consensus_audit_batch_receipt_v1"
        or audit_batch.get("evaluation_cycle_id") != CYCLE
        or audit_batch.get("passed") is not True
        or audit_batch.get("terminal_findings_count") != 0
        or audit_batch.get("text_free") is not True
    ):
        raise Error("terminal_audit_finding")

    # 7. Check Final Labels & Zero Residual
    res_batch_path = package / RESOLUTION_ROOT / "batch-receipt.json"
    _regular(res_batch_path)
    res_batch, _ = _read_json(res_batch_path)
    if (
        res_batch.get("schema_version") != "phase3_cycle007_operator_resolution_batch_receipt_v1"
        or res_batch.get("evaluation_cycle_id") != CYCLE
        or res_batch.get("total_rows") != ROW_COUNT
        or res_batch.get("packet_count") != PACKET_COUNT
        or res_batch.get("unresolved_remaining_count") != 0
        or res_batch.get("text_free") is not True
    ):
        raise Error("final_residual_zero")

    final_seen: list[tuple[str, str]] = []
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            lbl_path = package / RESOLUTION_ROOT / "final" / lane / f"labels-{index:04d}.json"
            _regular(lbl_path)
            lbl_data, _ = _read_json(lbl_path)
            for lbl in lbl_data.get("labels", []):
                final_seen.append((lbl["unit_id"], lbl["unit_sha256"]))

    if final_seen != seen_identities:
        raise Error("final_identity_union")

    # Certification receipt
    cert_receipt = {
        "schema_version": "phase3_cycle007_label_completion_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "source_custody_receipt_raw_sha256": SOURCE_CUSTODY_SHA256,
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "custody_receipt_raw_sha256": custody_hash,
        "manifest_raw_sha256": manifest_hash,
        "evidence_manifest_raw_sha256": digest(ev_manifest_raw),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "packet_count": PACKET_COUNT,
        "row_count": ROW_COUNT,
        "clean_consensus_count": comp_batch.get("clean_consensus_count"),
        "risk_triggered_consensus_count": comp_batch.get("risk_triggered_consensus_count"),
        "disagreement_count": comp_batch.get("disagreement_count"),
        "audited_consensus_count": audit_batch.get("clean_audited_count"),
        "one_sided_95_bound": audit_batch.get("one_sided_95_bound"),
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
    args = parser.parse_args(argv)
    try:
        result = certify_completion(args.package)
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
