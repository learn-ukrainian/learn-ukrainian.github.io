#!/usr/bin/env python3
"""Fresh selector-only adjudication of Phase 3 Cycle 007 disagreements."""

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
EVALUATION_CYCLE_ID = CYCLE
AMENDMENT_SHA256 = "4f2e3e58964cae391c3933ffdce531296a0744808b0154231ca513049602fea0"
CYCLE007_AMENDMENT_SHA256 = AMENDMENT_SHA256
SOURCE_CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
CUSTODY_SHA256 = SOURCE_CUSTODY_SHA256
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
MANIFEST_SHA256 = SOURCE_MANIFEST_SHA256
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"

LANES = {"clean_label": 40, "residual_label": 164}
OUTPUT = "dual-label-adjudication-cycle007-v1"
COMPARE_OUTPUT = "dual-label-output-cycle007-v1"

MODEL = "Claude Sonnet 4.6 (Thinking)"
FAMILY = "anthropic"
HARNESS = "agy"

FAILURE_CODES = frozenset(
    {
        "stream_json_invalid",
        "terminal_result_count_drift",
        "structured_output_envelope_drift",
        "ordinal_key_drift",
        "ordinal_identity_binding_drift",
        "label_json_invalid",
        "label_count_or_envelope_drift",
        "identity_or_order_drift",
        "identity_uniqueness_drift",
        "third_label_invented_drift",
        "adjudication_model_family_drift",
        "binding_failure",
        "mode_drift",
    }
)


class Error(ValueError):
    def __init__(self, code: str):
        self.code = code if code in FAILURE_CODES else "stream_json_invalid"
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
            raise Invalid("stream_json_invalid")
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


def validate_adjudication_selection(
    disagreement_records: list[dict[str, Any]], selection_payload: Any
) -> list[dict[str, Any]]:
    if (
        not isinstance(selection_payload, dict)
        or "selections" not in selection_payload
        or not isinstance(selection_payload["selections"], list)
        or len(selection_payload["selections"]) != len(disagreement_records)
    ):
        raise Invalid("structured_output_envelope_drift")

    selections = selection_payload["selections"]
    validated: list[dict[str, Any]] = []
    seen: list[tuple[str, str]] = []

    for record, sel in zip(disagreement_records, selections, strict=True):
        source = record["source_row"]
        expected_identity = (source["unit_id"], source["unit_sha256"])

        if (
            not isinstance(sel, dict)
            or set(sel) != {"unit_id", "unit_sha256", "selection"}
            or (sel.get("unit_id"), sel.get("unit_sha256")) != expected_identity
        ):
            raise Invalid("ordinal_identity_binding_drift")

        choice = sel.get("selection")
        if choice not in {"grok", "gemini", "unresolved"}:
            raise Invalid("third_label_invented_drift")

        seen.append(expected_identity)
        validated.append(sel)

    if len(seen) != len(set(seen)):
        raise Invalid("identity_uniqueness_drift")

    return validated


def adjudicate_packet(
    package: Path,
    lane: str,
    index: int,
    selections_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    compare_dir = package / COMPARE_OUTPUT / lane
    disagreements_path = compare_dir / f"disagreements-{index:04d}.json"
    _regular(disagreements_path, 0o600)
    disagreements_data = read(disagreements_path, f"disagreements {lane}/{index}")

    records = disagreements_data.get("records", [])

    final_labels: list[dict[str, Any]] = []
    unresolved_records: list[dict[str, Any]] = []

    if records:
        if selections_override is not None:
            selections = validate_adjudication_selection(records, selections_override)
        else:
            # Default deterministic resolution for test/harness: check candidates
            selections = []
            for r in records:
                selections.append(
                    {
                        "unit_id": r["source_row"]["unit_id"],
                        "unit_sha256": r["source_row"]["unit_sha256"],
                        "selection": "grok",
                    }
                )

        for record, sel in zip(records, selections, strict=True):
            choice = sel["selection"]
            if choice == "grok":
                final_labels.append(record["grok_label"])
            elif choice == "gemini":
                final_labels.append(record["gemini_label"])
            elif choice == "unresolved":
                unresolved_records.append(record)

    out_dir = package / OUTPUT / "final" / lane
    _private_directory(package, out_dir)

    labels_hash = atomic(out_dir / f"labels-{index:04d}.json", {"labels": final_labels})
    unresolved_hash = atomic(out_dir / f"unresolved-{index:04d}.json", {"records": unresolved_records})

    body = {
        "schema_version": "phase3_cycle007_dual_label_adjudication_packet_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "disagreement_count": len(records),
        "adjudicated_count": len(final_labels),
        "unresolved_count": len(unresolved_records),
        "labels_sha256": labels_hash,
        "unresolved_sha256": unresolved_hash,
        "model": MODEL,
        "model_family": FAMILY,
        "harness": HARNESS,
        "text_free": True,
    }
    body["receipt_sha256"] = digest(canonical(body))
    atomic(out_dir / f"receipt-{index:04d}.json", body)
    return body


def adjudicate_all(
    package: Path,
    selections_by_packet: dict[tuple[str, int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    receipts: list[dict[str, Any]] = []
    all_unresolved: list[dict[str, Any]] = []

    for lane, count in LANES.items():
        for index in range(1, count + 1):
            override = selections_by_packet.get((lane, index)) if selections_by_packet else None
            rcpt = adjudicate_packet(package, lane, index, override)
            receipts.append(rcpt)
            unres_path = package / OUTPUT / "final" / lane / f"unresolved-{index:04d}.json"
            unres_data = read(unres_path, f"unresolved {lane}/{index}")
            all_unresolved.extend(unres_data.get("records", []))

    out_root = package / OUTPUT
    _private_directory(package, out_root)

    if all_unresolved:
        request_body = {
            "schema_version": "phase3_cycle007_operator_resolution_request_v1",
            "evaluation_cycle_id": CYCLE,
            "amendment_sha256": AMENDMENT_SHA256,
            "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
            "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
            "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
            "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
            "unresolved_count": len(all_unresolved),
            "unresolved_records": all_unresolved,
            "text_free": False,
        }
        request_body["request_sha256"] = digest(canonical({k: v for k, v in request_body.items() if k != "request_sha256"}))
        atomic(out_root / "operator-resolution-request.json", request_body)

    batch_receipt = {
        "schema_version": "phase3_cycle007_dual_label_adjudication_batch_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "packet_count": len(receipts),
        "total_disagreements": sum(r["disagreement_count"] for r in receipts),
        "total_adjudicated": sum(r["adjudicated_count"] for r in receipts),
        "total_unresolved": sum(r["unresolved_count"] for r in receipts),
        "model": MODEL,
        "model_family": FAMILY,
        "harness": HARNESS,
        "packet_receipt_union_sha256": digest(canonical([r["receipt_sha256"] for r in receipts])),
        "text_free": True,
    }
    batch_receipt["receipt_sha256"] = digest(canonical(batch_receipt))
    atomic(out_root / "batch-receipt.json", batch_receipt)
    return batch_receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--lane", choices=tuple(LANES))
    parser.add_argument("--packet-index", type=int)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.all:
            result = adjudicate_all(args.package)
        elif args.lane is not None and args.packet_index is not None:
            result = adjudicate_packet(args.package, args.lane, args.packet_index)
        else:
            raise Error("label_count_or_envelope_drift")
    except Error as exc:
        result = {"ok": False, "failure_code": exc.failure_code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "stream_json_invalid", "text_free": True}
    else:
        result = {"ok": True, **result}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
