#!/usr/bin/env python3
"""Fail-closed authorized candidate-only Cycle 007 resolver."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any

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
ROW_COUNT = 10_159
RESOLUTION_OUTPUT = "dual-label-final-cycle007-v1"
ADJUDICATION_OUTPUT = "dual-label-adjudication-cycle007-v1"
COMPARE_OUTPUT = "dual-label-output-cycle007-v1"

FAILURE_CODES = frozenset(
    {
        "authorization_binding_failure",
        "authorization_tamper_detected",
        "candidate_invention_drift",
        "unauthorized_row_drift",
        "missing_authorization",
        "identity_binding_failure",
        "identity_uniqueness_failure",
        "upstream_package_binding",
        "mode_drift",
        "json_binding_failure",
    }
)


class Error(ValueError):
    def __init__(self, code: str):
        self.code = code if code in FAILURE_CODES else "authorization_binding_failure"
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


def validate_authorization_file(path: Path, package: Path) -> dict[tuple[str, str], dict[str, Any]]:
    value, _raw = _read(path)
    custody_raw = (package / "custody-receipt.json").read_bytes()
    manifest_raw = (package / "manifest.json").read_bytes()

    if (
        not isinstance(value, dict)
        or value.get("schema_version") != "phase3_cycle007_operator_resolution_authorization_v1"
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("amendment_sha256") != AMENDMENT_SHA256
        or value.get("custody_receipt_raw_sha256") != digest(custody_raw)
        or value.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or value.get("manifest_raw_sha256") != digest(manifest_raw)
        or value.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
        or not isinstance(value.get("authorizations"), list)
    ):
        raise Error("authorization_binding_failure")

    authorizations: dict[tuple[str, str], dict[str, Any]] = {}
    seen: list[tuple[str, str]] = []

    for item in value["authorizations"]:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("unit_id"), str)
            or not isinstance(item.get("unit_sha256"), str)
            or item.get("selection") not in {"grok", "gemini"}
            or not isinstance(item.get("source_bound_rationale"), str)
            or not isinstance(item.get("source_authority_reference"), str)
        ):
            raise Error("authorization_tamper_detected")

        key = (item["unit_id"], item["unit_sha256"])
        seen.append(key)
        authorizations[key] = item

    if len(seen) != len(set(seen)):
        raise Error("identity_uniqueness_failure")

    return authorizations


def resolve_packet(
    package: Path,
    lane: str,
    index: int,
    authorizations: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    # 1. Read packet rows
    packet_path = package / lane / f"packet-{index:04d}.json"
    _regular(packet_path, 0o600)
    packet_data = json.loads(packet_path.read_bytes().decode("utf-8", "strict"), object_pairs_hook=_pairs)
    rows = packet_data["rows"]

    # 2. Read consensus records
    clean_p = package / COMPARE_OUTPUT / lane / f"clean-consensus-{index:04d}.json"
    risk_p = package / COMPARE_OUTPUT / lane / f"risk-consensus-{index:04d}.json"
    _regular(clean_p, 0o600)
    _regular(risk_p, 0o600)
    clean_val = json.loads(clean_p.read_bytes().decode("utf-8", "strict"), object_pairs_hook=_pairs)
    risk_val = json.loads(risk_p.read_bytes().decode("utf-8", "strict"), object_pairs_hook=_pairs)

    labels_by_unit: dict[tuple[str, str], dict[str, Any]] = {}
    decisions_by_unit: dict[tuple[str, str], dict[str, Any]] = {}

    for r in clean_val.get("records", []):
        uid = (r["source_row"]["unit_id"], r["source_row"]["unit_sha256"])
        labels_by_unit[uid] = r["label"]
        decisions_by_unit[uid] = {"origin": "clean_consensus", "selection": "consensus"}

    for r in risk_val.get("records", []):
        uid = (r["source_row"]["unit_id"], r["source_row"]["unit_sha256"])
        labels_by_unit[uid] = r["label"]
        decisions_by_unit[uid] = {"origin": "risk_consensus", "selection": "consensus", "risk_reasons": r.get("risk_reasons", [])}

    # 3. Read adjudicated labels and unresolved
    adj_labels_p = package / ADJUDICATION_OUTPUT / "final" / lane / f"labels-{index:04d}.json"
    adj_unres_p = package / ADJUDICATION_OUTPUT / "final" / lane / f"unresolved-{index:04d}.json"
    _regular(adj_labels_p, 0o600)
    _regular(adj_unres_p, 0o600)
    adj_labels_val = json.loads(adj_labels_p.read_bytes().decode("utf-8", "strict"), object_pairs_hook=_pairs)
    adj_unres_val = json.loads(adj_unres_p.read_bytes().decode("utf-8", "strict"), object_pairs_hook=_pairs)

    for lbl in adj_labels_val.get("labels", []):
        uid = (lbl["unit_id"], lbl["unit_sha256"])
        labels_by_unit[uid] = lbl
        decisions_by_unit[uid] = {"origin": "adjudication", "selection": "adjudicated"}

    for unres in adj_unres_val.get("records", []):
        uid = (unres["source_row"]["unit_id"], unres["source_row"]["unit_sha256"])
        if uid not in authorizations:
            raise Error("missing_authorization")
        auth = authorizations[uid]
        choice = auth["selection"]
        if choice == "grok":
            labels_by_unit[uid] = unres["grok_label"]
        elif choice == "gemini":
            labels_by_unit[uid] = unres["gemini_label"]
        else:
            raise Error("candidate_invention_drift")
        decisions_by_unit[uid] = {
            "origin": "operator_resolution",
            "selection": choice,
            "source_bound_rationale": auth["source_bound_rationale"],
            "source_authority_reference": auth["source_authority_reference"],
        }

    # Reassemble in exact packet row order
    ordered_labels: list[dict[str, Any]] = []
    ordered_decisions: list[dict[str, Any]] = []
    for row in rows:
        uid = (row["unit_id"], row["unit_sha256"])
        if uid not in labels_by_unit:
            raise Error("identity_binding_failure")
        ordered_labels.append(labels_by_unit[uid])
        ordered_decisions.append({
            "unit_id": uid[0],
            "unit_sha256": uid[1],
            **decisions_by_unit[uid],
        })

    out_dir = package / RESOLUTION_OUTPUT / "final" / lane
    _private_directory(package, out_dir)

    labels_hash = atomic(out_dir / f"labels-{index:04d}.json", {"labels": ordered_labels})
    decisions_hash = atomic(out_dir / f"decisions-{index:04d}.json", {"decisions": ordered_decisions})

    body = {
        "schema_version": "phase3_cycle007_operator_resolution_packet_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "row_count": len(rows),
        "labels_sha256": labels_hash,
        "decisions_sha256": decisions_hash,
        "unresolved_remaining_count": 0,
        "text_free": True,
    }
    body["receipt_sha256"] = digest(canonical(body))
    atomic(out_dir / f"receipt-{index:04d}.json", body)
    return body


def resolve_all(package: Path, authorization_path: Path | None = None) -> dict[str, Any]:
    _directory(package, 0o700)
    auth_path = authorization_path or (package / RESOLUTION_OUTPUT / "authorization.json")
    authorizations: dict[tuple[str, str], dict[str, Any]] = {}
    if auth_path.exists():
        authorizations = validate_authorization_file(auth_path, package)

    receipts: list[dict[str, Any]] = []
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            receipts.append(resolve_packet(package, lane, index, authorizations))

    out_root = package / RESOLUTION_OUTPUT
    _private_directory(package, out_root)

    body = {
        "schema_version": "phase3_cycle007_operator_resolution_batch_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "packet_count": len(receipts),
        "total_rows": sum(r["row_count"] for r in receipts),
        "unresolved_remaining_count": 0,
        "packet_receipt_union_sha256": digest(canonical([r["receipt_sha256"] for r in receipts])),
        "text_free": True,
    }
    body["receipt_sha256"] = digest(canonical(body))
    atomic(out_root / "batch-receipt.json", body)
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = resolve_all(args.package, args.authorization)
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
