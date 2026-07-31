#!/usr/bin/env python3
"""Build the deterministic v0.2, human-review-only priority packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "data/projects/ua_eval_harness/analysis/v0.1.1/item_evidence.jsonl"
MANIFEST = ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json"
FREEZE = ROOT / "data/projects/ua_eval_harness/releases/v0.1.1/freeze_manifest.json"
EXPECTED_FREEZE_SHA256 = "b95edea210ae9133059181a4e2d161c8682108bfcacdde50f98adaae2221e65f"
DEFAULT_OUTPUT = ROOT / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl"
PACKET_SCHEMA = "ua_eval_v02_review_packet.v1"
ANNOTATION_SCHEMA_PATH = ROOT / "data/projects/ua_eval_harness/v0.2/annotation_schema_v1.json"


class PacketError(ValueError):
    """The frozen evidence cannot produce a trustworthy review packet."""


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packet_row_validator() -> Any:
    """Load and meta-validate the frozen Draft 2020-12 packet-row contract."""
    try:
        import jsonschema
    except ImportError as exc:
        raise PacketError("jsonschema is required for packet validation") from exc
    try:
        schema = json.loads(ANNOTATION_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PacketError(f"cannot read packet annotation schema: {exc}") from exc
    try:
        validator_class = jsonschema.validators.validator_for(schema)
        validator_class.check_schema(schema)
    except jsonschema.exceptions.SchemaError as exc:
        raise PacketError(f"invalid packet annotation schema: {exc.message}") from exc
    return validator_class(schema)


def validate_packet_rows(rows: list[dict[str, Any]]) -> None:
    """Reject structural drift before a packet can be written or consumed."""
    schema_validator = packet_row_validator()
    for line_number, row in enumerate(rows, 1):
        errors = sorted(schema_validator.iter_errors(row), key=lambda error: list(error.path))
        if errors:
            path = ".".join(str(part) for part in errors[0].path) or "record"
            raise PacketError(f"packet schema violation at row {line_number} ({path}): {errors[0].message}")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise PacketError(f"cannot read {path}: {exc}") from exc
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(lines, 1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PacketError(f"invalid JSONL at {path}:{number}") from exc
        if not isinstance(value, dict):
            raise PacketError(f"expected object at {path}:{number}")
        rows.append(value)
    return rows


def manifest_items() -> dict[str, dict[str, Any]]:
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PacketError(f"cannot read manifest: {exc}") from exc
    items = manifest.get("items")
    layout = manifest.get("record_layouts", {}).get("item")
    if not isinstance(items, list) or not isinstance(layout, list):
        raise PacketError("manifest has no item list")
    required = {"id", "source", "source_sha256", "references"}
    if not required.issubset(layout):
        raise PacketError("manifest item layout is incomplete")
    normalized: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            normalized.append(item)
        elif isinstance(item, list) and len(item) == len(layout):
            normalized.append(dict(zip(layout, item, strict=True)))
        else:
            raise PacketError("manifest item does not match its declared layout")
    indexed = {item.get("id"): item for item in normalized}
    if len(indexed) != len(items) or None in indexed:
        raise PacketError("manifest item IDs are missing or duplicate")
    return indexed


def build_rows() -> list[dict[str, Any]]:
    if sha256(FREEZE) != EXPECTED_FREEZE_SHA256:
        raise PacketError("v0.1.1 freeze manifest bytes changed")
    items = manifest_items()
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for evidence in read_jsonl(EVIDENCE):
        item_id = evidence.get("item_id")
        flags = {
            "needs_ua_review": evidence.get("next_disposition") == "needs_ua_review",
            "possible_benchmark_defect": bool(evidence.get("possible_reference_ambiguity_or_benchmark_defect")),
            "protected_variation_risk": bool(evidence.get("protected_heritage_dialect_register_risk")),
        }
        if not any(flags.values()):
            continue
        if not isinstance(item_id, str) or item_id in seen or item_id not in items:
            raise PacketError("selected item ID is missing, duplicate, or absent from manifest")
        seen.add(item_id)
        item = items[item_id]
        source = item.get("source")
        source_sha256 = item.get("source_sha256")
        if source_sha256 != evidence.get("source_sha256") or not isinstance(source, str):
            raise PacketError(f"source receipt mismatch for {item_id}")
        selected.append({
            "schema_version": PACKET_SCHEMA,
            "packet_order": len(selected) + 1,
            "item_id": item_id,
            "review_state": "pending",
            "decision": None,
            "frozen_receipts": {
                "freeze_manifest_sha256": EXPECTED_FREEZE_SHA256,
                "heldout_manifest_sha256": sha256(MANIFEST),
                "item_evidence_file_sha256": sha256(EVIDENCE),
                "source_sha256": source_sha256,
            },
            "blind_reviewer_view": {
                "source": source,
                "references": item.get("references"),
                "reference_count": evidence.get("acceptable_reference_count"),
                "observed_tags": evidence.get("observed_tags"),
                "uncertainty": evidence.get("uncertainty"),
                "instruction": "Make a linguistic judgment; exact measurement and saved model output are not linguistic authority.",
            },
            "coordinator_priority_metadata": {
                "signals": sorted(name for name, present in flags.items() if present),
                "measurement_note": "Priority signals are evidence-routing flags, not adjudicated truth.",
            },
            "data_handling": {"classification": "evaluation_only", "training_or_export_eligible": False},
        })
    if len(selected) != 14:
        raise PacketError(f"expected 14 union rows, found {len(selected)}")
    validate_packet_rows(selected)
    return selected


def write_packet(output: Path) -> list[dict[str, Any]]:
    rows = build_rows()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(canonical(row) + "\n" for row in rows), encoding="utf-8")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    write_packet(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
