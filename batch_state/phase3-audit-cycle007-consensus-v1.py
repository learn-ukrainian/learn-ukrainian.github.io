#!/usr/bin/env python3
"""Deterministic consensus audit and source-authority review for Cycle 007."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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
EVALUATION_CYCLE_ID = CYCLE
AMENDMENT_SHA256 = "4f2e3e58964cae391c3933ffdce531296a0744808b0154231ca513049602fea0"
CYCLE007_AMENDMENT_SHA256 = AMENDMENT_SHA256
SOURCE_CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
CUSTODY_SHA256 = SOURCE_CUSTODY_SHA256
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
MANIFEST_SHA256 = SOURCE_MANIFEST_SHA256
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"

LANES = {"clean_label": 40, "residual_label": 164}
OUTPUT = "consensus-audit-cycle007-v1"
COMPARE_OUTPUT = "dual-label-output-cycle007-v1"

FAILURE_CODES = frozenset(
    {
        "audit_population_drift",
        "sample_size_drift",
        "stratum_selection_drift",
        "rank_calculation_drift",
        "seed_calculation_drift",
        "unsupported_acceptance_finding",
        "incorrect_positive_finding",
        "russianism_accepted_finding",
        "surzhyk_accepted_finding",
        "foreign_or_insufficient_evidence_finding",
        "terminal_audit_finding",
        "incomplete_risk_review",
        "binding_failure",
        "mode_drift",
    }
)


class Error(ValueError):
    def __init__(self, code: str):
        self.code = code if code in FAILURE_CODES else "terminal_audit_finding"
        self.failure_code = self.code
        super().__init__(self.code)


class TerminalAuditFindingError(Error):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise Error("binding_failure")
        value[key] = item
    return value


def _regular(path: Path, mode: int | None = 0o600) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise Error("binding_failure") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise Error("binding_failure")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("mode_drift")


def _directory(path: Path, mode: int | None = 0o700) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise Error("binding_failure") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise Error("binding_failure")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("mode_drift")


def read(path: Path, label: str = "sealed value") -> Any:
    try:
        _regular(path, 0o600)
        return json.loads(path.read_bytes().decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Error):
        raise Error("binding_failure") from None


def atomic(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _directory(path.parent, 0o700)
    data = canonical(value)
    if path.exists() or path.is_symlink():
        _regular(path, 0o600)
        if path.read_bytes() != data:
            raise Error("binding_failure")
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


def seed_clean_consensus(
    custody_sha256: str, manifest_sha256: str, ordered_identity_commitment_sha256: str
) -> str:
    raw = f"phase3-cycle007-consensus-audit-v1\n{custody_sha256}{manifest_sha256}{ordered_identity_commitment_sha256}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def rank_row(seed: str, lane: str, unit_id: str, unit_sha256: str) -> str:
    raw = f"{seed}{lane}{unit_id}{unit_sha256}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_zero_event_bound(population_count: int) -> float:
    if population_count <= 0:
        return 0.0
    return 1.0 - (0.05 ** (1.0 / population_count))


def sample_clean_consensus(
    package: Path, clean_consensus_records: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    custody_sha256 = digest((package / "custody-receipt.json").read_bytes())
    manifest_sha256 = digest((package / "manifest.json").read_bytes())
    ordered_identity_commitment = ORDERED_IDENTITY_COMMITMENT_SHA256
    seed = seed_clean_consensus(custody_sha256, manifest_sha256, ordered_identity_commitment)

    population_count = len(clean_consensus_records)

    # Attach ranks
    for r in clean_consensus_records:
        u_id = r["source_row"]["unit_id"]
        u_sha = r["source_row"]["unit_sha256"]
        r["rank"] = rank_row(seed, r["lane"], u_id, u_sha)

    # Group into strata
    strata: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in clean_consensus_records:
        lane = r["lane"]
        label = r["label"]
        if lane == "clean_label":
            code = label.get("decision_code", "unknown")
            strata[f"clean:{code}"].append(r)
        elif lane == "residual_label":
            for p in label.get("phenomena", []):
                p_id = p.get("phenomenon_id", "unknown")
                p_code = p.get("decision_code", "unknown")
                strata[f"residual:{p_id}:{p_code}"].append(r)

    # Sort each stratum by rank ascending and take top 10
    selected_by_unit: dict[tuple[str, str], dict[str, Any]] = {}
    for _stratum_name, stratum_rows in sorted(strata.items()):
        sorted_stratum = sorted(stratum_rows, key=lambda x: x["rank"])
        top_10 = sorted_stratum[:10]
        for row in top_10:
            uid = (row["source_row"]["unit_id"], row["source_row"]["unit_sha256"])
            if uid not in selected_by_unit:
                selected_by_unit[uid] = row

    mandatory_union = list(selected_by_unit.values())

    if population_count <= 600:
        # Whole population
        sample = sorted(clean_consensus_records, key=lambda x: x["rank"])
    elif len(mandatory_union) >= 600:
        # Expand rather than truncate
        sample = mandatory_union
    else:
        # Fill to 600 from remaining population by global rank
        remaining = [
            r
            for r in clean_consensus_records
            if (r["source_row"]["unit_id"], r["source_row"]["unit_sha256"]) not in selected_by_unit
        ]
        remaining_sorted = sorted(remaining, key=lambda x: x["rank"])
        needed = 600 - len(mandatory_union)
        sample = mandatory_union + remaining_sorted[:needed]

    sample_sorted = sorted(
        sample,
        key=lambda x: (x["lane"], x["source_row"]["unit_id"], x["source_row"]["unit_sha256"]),
    )

    bound = compute_zero_event_bound(population_count)

    sample_identities = [(r["source_row"]["unit_id"], r["source_row"]["unit_sha256"]) for r in sample_sorted]
    sample_commitment = digest(canonical(sample_identities))

    sample_receipt = {
        "schema_version": "phase3_cycle007_clean_consensus_sample_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": custody_sha256,
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": manifest_sha256,
        "ordered_identity_commitment_sha256": ordered_identity_commitment,
        "population_count": population_count,
        "audited_count": len(sample_sorted),
        "one_sided_95_bound": bound,
        "seed": seed,
        "strata_counts": {k: len(v) for k, v in sorted(strata.items())},
        "sample_identity_commitment_sha256": sample_commitment,
        "text_free": True,
    }
    sample_receipt["receipt_sha256"] = digest(canonical(sample_receipt))
    return sample_receipt, sample_sorted


def audit_row_evidence(
    record: dict[str, Any],
    row_evidence: Mapping[str, Any],
) -> None:
    """Check a reviewed/audited consensus row for any terminal audit findings."""
    source_row = record["source_row"]
    label = record["label"]
    evidence_records = list(row_evidence.get("evidence", []))

    # Check for Russianism/Surzhyk accepted as standard
    is_neg = (
        source_row.get("is_negative_control") is True
        or source_row.get("negative_control") is True
        or source_row.get("is_russianism_control") is True
        or source_row.get("is_surzhyk_control") is True
        or source_row.get("control_type") in {"russianism", "surzhyk", "source_conflict"}
        or source_row.get("family_id") in {"russianism", "surzhyk", "source_conflict"}
    )
    if is_neg:
        if label.get("decision_code") == "agree":
            raise TerminalAuditFindingError("russianism_accepted_finding")
        if "phenomena" in label:
            for p in label.get("phenomena", []):
                if p.get("decision_code") == "positive":
                    raise TerminalAuditFindingError("russianism_accepted_finding")

    # Check for unsupported acceptance or incorrect positive
    if label.get("decision_code") == "agree":
        suff = validator.classify_sufficiency(row_evidence)
        if suff != "sufficient":
            raise TerminalAuditFindingError("unsupported_acceptance_finding")
        # Evidence references must exist and be valid
        by_id = {str(r["evidence_id"]): r for r in evidence_records}
        cited = [by_id.get(eid) for eid in label.get("evidence_ids", [])]
        if any(c is None for c in cited) or not any(c is not None and contract.is_sufficient_positive(c) for c in cited):
            raise TerminalAuditFindingError("foreign_or_insufficient_evidence_finding")

    if "phenomena" in label:
        for p in label.get("phenomena", []):
            if p.get("decision_code") in {"positive", "acceptable_control", "protected"}:
                suff = validator.classify_sufficiency(row_evidence, phenomenon_id=p.get("phenomenon_id"))
                if suff != "sufficient":
                    raise TerminalAuditFindingError("unsupported_acceptance_finding")
                by_id = {str(r["evidence_id"]): r for r in evidence_records}
                cited = [by_id.get(eid) for eid in p.get("evidence_ids", [])]
                if any(c is None for c in cited) or not any(c is not None and contract.is_sufficient_positive(c) for c in cited):
                    raise TerminalAuditFindingError("foreign_or_insufficient_evidence_finding")


def run_audit(package: Path) -> dict[str, Any]:
    """Execute 100% review of risk-triggered consensus and sample audit of clean consensus."""
    _directory(package, 0o700)
    compare_dir = package / COMPARE_OUTPUT
    _directory(compare_dir, 0o700)

    # Load all clean-consensus and risk-consensus records
    clean_records: list[dict[str, Any]] = []
    risk_records: list[dict[str, Any]] = []

    # Read sidecars into lookup
    evidence_manifest_path = package / "evidence" / "manifest.json"
    _regular(evidence_manifest_path, 0o600)
    ev_manifest = read(evidence_manifest_path, "evidence manifest")
    expected_identity = {k: ev_manifest.get(k) for k in validator._IDENTITY_FIELDS}
    validator.validate_manifest(ev_manifest, expected_identity=expected_identity)

    sidecar_lookup: dict[tuple[str, int], dict[str, Any]] = {}
    for entry in ev_manifest["sidecars"]:
        p_idx = entry["packet_index"]
        lane = entry["lane"]
        sidecar_path = package / "evidence" / f"sidecar-{p_idx:04d}.json"
        _regular(sidecar_path, 0o600)
        s_data = read(sidecar_path, f"sidecar {p_idx}")
        validator.validate_sidecar(s_data, expected_identity=expected_identity)
        sidecar_lookup[(lane, p_idx)] = s_data

    # Map row unit to row_evidence
    unit_evidence_map: dict[tuple[str, str], dict[str, Any]] = {}
    for s_data in sidecar_lookup.values():
        for r_ev in s_data.get("rows", []):
            unit_evidence_map[(r_ev["unit_id"], r_ev["unit_sha256"])] = r_ev

    for lane, count in LANES.items():
        lane_dir = compare_dir / lane
        _directory(lane_dir, 0o700)
        for index in range(1, count + 1):
            clean_p = lane_dir / f"clean-consensus-{index:04d}.json"
            risk_p = lane_dir / f"risk-consensus-{index:04d}.json"
            _regular(clean_p, 0o600)
            _regular(risk_p, 0o600)
            c_val = read(clean_p, f"clean consensus {lane}/{index}")
            r_val = read(risk_p, f"risk consensus {lane}/{index}")
            for r in c_val.get("records", []):
                clean_records.append({**r, "lane": lane, "packet_index": index})
            for r in r_val.get("records", []):
                risk_records.append({**r, "lane": lane, "packet_index": index})

    # 1. 100% review of risk-triggered consensus
    for r in risk_records:
        uid = (r["source_row"]["unit_id"], r["source_row"]["unit_sha256"])
        r_ev = unit_evidence_map.get(uid)
        if r_ev is None:
            raise Error("binding_failure")
        audit_row_evidence(r, r_ev)

    # 2. Sample and audit clean consensus
    sample_receipt, sample_records = sample_clean_consensus(package, clean_records)
    for r in sample_records:
        uid = (r["source_row"]["unit_id"], r["source_row"]["unit_sha256"])
        r_ev = unit_evidence_map.get(uid)
        if r_ev is None:
            raise Error("binding_failure")
        audit_row_evidence(r, r_ev)

    out_dir = package / OUTPUT
    out_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    _directory(out_dir, 0o700)

    # Write sample
    atomic(out_dir / "clean-consensus-sample.json", sample_receipt)

    # Write risk review receipt
    risk_review_receipt = {
        "schema_version": "phase3_cycle007_risk_review_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "risk_population_count": len(risk_records),
        "reviewed_count": len(risk_records),
        "terminal_findings_count": 0,
        "text_free": True,
    }
    risk_review_receipt["receipt_sha256"] = digest(canonical(risk_review_receipt))
    atomic(out_dir / "risk-review-receipt.json", risk_review_receipt)

    # Write clean audit receipt
    clean_audit_receipt = {
        "schema_version": "phase3_cycle007_clean_audit_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "clean_population_count": len(clean_records),
        "audited_count": len(sample_records),
        "one_sided_95_bound": sample_receipt["one_sided_95_bound"],
        "terminal_findings_count": 0,
        "text_free": True,
    }
    clean_audit_receipt["receipt_sha256"] = digest(canonical(clean_audit_receipt))
    atomic(out_dir / "clean-audit-receipt.json", clean_audit_receipt)

    # Batch receipt
    batch_receipt = {
        "schema_version": "phase3_cycle007_consensus_audit_batch_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "risk_population_count": len(risk_records),
        "risk_reviewed_count": len(risk_records),
        "clean_population_count": len(clean_records),
        "clean_audited_count": len(sample_records),
        "one_sided_95_bound": sample_receipt["one_sided_95_bound"],
        "terminal_findings_count": 0,
        "passed": True,
        "text_free": True,
    }
    batch_receipt["receipt_sha256"] = digest(canonical(batch_receipt))
    atomic(out_dir / "batch-receipt.json", batch_receipt)
    return batch_receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run_audit(args.package)
    except Error as exc:
        result = {"ok": False, "failure_code": exc.failure_code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "terminal_audit_finding", "text_free": True}
    else:
        result = {"ok": True, **result}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
