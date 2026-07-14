#!/usr/bin/env python3
"""Validate tracked Word Atlas source-inventory review decisions."""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from scripts.audit.generate_source_inventory_review_candidates import (
    COMMITTED_SOURCE_INVENTORIES,
)
from scripts.audit.source_inventory_intake import (
    SourceInventoryError,
    SourceInventoryRecord,
    read_source_inventories,
)
from scripts.lexicon.content_lexicon_reconciler import PROJECT_ROOT

DECISION_KIND = "atlas_source_inventory_review_decisions"
DECISION_VERSION = 1
DEFAULT_DECISION_DIR = PROJECT_ROOT / "data/lexicon/source-inventory-review-decisions"
SOURCE_INVENTORY_DIR = PROJECT_ROOT / "data/lexicon/source-inventory"
QUEUE_WORKFLOW = "source_inventory_publish_review_queue.v1"
ALLOWED_DECISIONS = {
    "approve_for_publish",
    "needs_more_evidence",
    "reject",
    "merge_duplicate",
}

TOP_LEVEL_FIELDS = {
    "version",
    "kind",
    "batch_id",
    "batch_label",
    "reviewer",
    "reviewed_at",
    "source_queue",
    "production_outputs_updated",
    "decisions",
}
SOURCE_QUEUE_FIELDS = {
    "workflow",
    "generated_from_pr",
    "total_queue_rows",
    "approved_in_queue",
    "first_promotion_batch_size",
    "promotion_batch_size",
}
DECISION_FIELDS = {
    "lemma",
    "decision",
    "approved_pos",
    "approved_gloss",
    "sense_note",
    "source_inventory",
    "evidence_refs",
    "review_queue_reasons",
    "original_flags",
    "surface_admission",
    "supersedes",
}
SURFACE_ADMISSION_FIELDS = {"daily", "practice", "cloze"}
SOURCE_INVENTORY_FIELDS = {
    "key",
    "path",
    "locator",
    "source_id",
    "source_family",
}


def source_inventory_key(*, lemma: str, inventory_path: str, locator: str) -> str:
    """Return stable source-record key independent of review queue row numbering."""
    key_material = f"{lemma}\0{inventory_path}\0{locator}"
    return hashlib.sha256(key_material.encode("utf-8")).hexdigest()[:16]


def validate_committed_decision_files(
    paths: Sequence[Path] | None = None,
) -> dict[str, Any]:
    decision_paths = list(paths) if paths else sorted(DEFAULT_DECISION_DIR.glob("*.yaml"))
    if not decision_paths:
        raise SourceInventoryError("no source-inventory review decision files found")

    summaries = [validate_decision_file(path) for path in decision_paths]
    decision_counts: Counter[str] = Counter()
    total_rows = 0
    for summary in summaries:
        decision_counts.update(summary["decision_counts"])
        total_rows += summary["rows"]
    return {
        "files": len(summaries),
        "rows": total_rows,
        "decision_counts": dict(sorted(decision_counts.items())),
    }


def validate_decision_file(
    path: Path,
    *,
    source_index: Mapping[tuple[str, str, str], SourceInventoryRecord] | None = None,
) -> dict[str, Any]:
    payload = _read_yaml_mapping(path)
    # Check `kind` BEFORE unknown-field rejection: a document of a different
    # kind dropped into the decisions directory (2026-07-10 incident — grow
    # triage ledgers, #4888/#4889) should fail with "this is the wrong kind
    # of file for this directory", not a wall of unknown-field noise.
    # Non-decision documents belong elsewhere (see
    # data/lexicon/grow-triage-ledgers/README.md).
    _require_equal(path, payload.get("kind"), DECISION_KIND, "kind")
    _reject_unknown_fields(path, payload, allowed=TOP_LEVEL_FIELDS, scope="top level")
    _require_equal(path, payload.get("version"), DECISION_VERSION, "version")
    for field in ("batch_id", "batch_label", "reviewer", "reviewed_at"):
        _require_text(path, payload.get(field), field)
    if payload.get("production_outputs_updated") != []:
        raise SourceInventoryError(f"{path}: production_outputs_updated must be []")

    source_queue = payload.get("source_queue")
    if not isinstance(source_queue, Mapping):
        raise SourceInventoryError(f"{path}: source_queue must be a mapping")
    _reject_unknown_fields(path, source_queue, allowed=SOURCE_QUEUE_FIELDS, scope="source_queue")
    _require_equal(path, source_queue.get("workflow"), QUEUE_WORKFLOW, "source_queue.workflow")
    batch_size_fields = [
        field
        for field in ("first_promotion_batch_size", "promotion_batch_size")
        if field in source_queue
    ]
    if len(batch_size_fields) != 1:
        raise SourceInventoryError(
            f"{path}: source_queue must define exactly one promotion batch size field"
        )
    _require_positive_int(
        path,
        source_queue[batch_size_fields[0]],
        f"source_queue.{batch_size_fields[0]}",
    )

    decisions = payload.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        raise SourceInventoryError(f"{path}: decisions must be a non-empty list")

    index = source_index or _source_record_index(
        read_source_inventories(
            inventory_paths_for_decision_payload(payload),
            project_root=PROJECT_ROOT,
        )
    )
    seen_source_keys: set[str] = set()
    decision_counts: Counter[str] = Counter()
    for idx, row in enumerate(decisions, start=1):
        if not isinstance(row, Mapping):
            raise SourceInventoryError(f"{path}: decisions[{idx}] must be a mapping")
        _validate_decision_row(path, idx, row, source_index=index, seen_source_keys=seen_source_keys)
        decision_counts[str(row["decision"])] += 1

    return {
        "path": str(path),
        "rows": len(decisions),
        "decision_counts": dict(sorted(decision_counts.items())),
    }


def _validate_decision_row(
    path: Path,
    idx: int,
    row: Mapping[str, Any],
    *,
    source_index: Mapping[tuple[str, str, str], SourceInventoryRecord],
    seen_source_keys: set[str],
) -> None:
    prefix = f"{path}: decisions[{idx}]"
    _reject_unknown_fields(path, row, allowed=DECISION_FIELDS, scope=f"decisions[{idx}]")
    lemma = _require_text(path, row.get("lemma"), f"decisions[{idx}].lemma")
    decision = _require_text(path, row.get("decision"), f"decisions[{idx}].decision")
    if decision not in ALLOWED_DECISIONS:
        raise SourceInventoryError(f"{prefix} invalid decision {decision!r}")
    if decision == "approve_for_publish":
        _require_text(path, row.get("approved_pos"), f"decisions[{idx}].approved_pos")
        _require_text(path, row.get("approved_gloss"), f"decisions[{idx}].approved_gloss")
    _require_text(path, row.get("sense_note"), f"decisions[{idx}].sense_note")
    _validate_text_list(path, row.get("evidence_refs"), f"decisions[{idx}].evidence_refs")
    if "review_queue_reasons" in row:
        _validate_text_list(
            path,
            row.get("review_queue_reasons"),
            f"decisions[{idx}].review_queue_reasons",
        )
    if "original_flags" in row:
        _validate_text_list(path, row.get("original_flags"), f"decisions[{idx}].original_flags")
    if "surface_admission" in row:
        _validate_surface_admission(
            path,
            row.get("surface_admission"),
            f"decisions[{idx}].surface_admission",
        )

    source_inventory = row.get("source_inventory")
    if not isinstance(source_inventory, Mapping):
        raise SourceInventoryError(f"{prefix} source_inventory must be a mapping")
    _reject_unknown_fields(
        path,
        source_inventory,
        allowed=SOURCE_INVENTORY_FIELDS,
        scope=f"decisions[{idx}].source_inventory",
    )
    source_key = _require_text(path, source_inventory.get("key"), f"decisions[{idx}].source_inventory.key")
    inventory_path = _require_text(
        path,
        source_inventory.get("path"),
        f"decisions[{idx}].source_inventory.path",
    )
    locator = _require_text(
        path,
        source_inventory.get("locator"),
        f"decisions[{idx}].source_inventory.locator",
    )
    expected_key = source_inventory_key(lemma=lemma, inventory_path=inventory_path, locator=locator)
    if source_key != expected_key:
        raise SourceInventoryError(
            f"{prefix} source_inventory.key {source_key!r} does not match {expected_key!r}"
        )
    if source_key in seen_source_keys:
        raise SourceInventoryError(f"{prefix} duplicate source_inventory.key {source_key!r}")
    seen_source_keys.add(source_key)

    record = source_index.get((lemma, inventory_path, locator))
    if record is None:
        raise SourceInventoryError(
            f"{prefix} source inventory record not found for {lemma!r} at {inventory_path}:{locator}"
        )
    if source_inventory.get("source_id") != record.source_id:
        raise SourceInventoryError(f"{prefix} source_id does not match committed inventory")
    if source_inventory.get("source_family") != record.source_family:
        raise SourceInventoryError(f"{prefix} source_family does not match committed inventory")


def _source_record_index(
    records: Sequence[SourceInventoryRecord],
) -> dict[tuple[str, str, str], SourceInventoryRecord]:
    return {
        (record.lemma, record.inventory_path, record.source_locator): record
        for record in records
    }


def inventory_paths_for_decision_payload(payload: Mapping[str, Any]) -> tuple[Path, ...]:
    """Locate referenced staged inventories without broadening the review corpus."""

    paths: list[Path] = list(COMMITTED_SOURCE_INVENTORIES)
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        return tuple(paths)
    for row in decisions:
        if not isinstance(row, Mapping):
            continue
        source_inventory = row.get("source_inventory")
        if not isinstance(source_inventory, Mapping):
            continue
        inventory_path = source_inventory.get("path")
        if not isinstance(inventory_path, str) or not inventory_path.strip():
            continue
        paths.append(resolve_staged_inventory_path(inventory_path))
    return tuple(dict.fromkeys(paths))


def resolve_staged_inventory_path(inventory_path: str) -> Path:
    """Resolve one ledger-referenced inventory, restricted to the inventory directory."""

    candidate = (PROJECT_ROOT / inventory_path).resolve()
    try:
        candidate.relative_to(SOURCE_INVENTORY_DIR.resolve())
    except ValueError as exc:
        raise SourceInventoryError(
            "source_inventory.path must be inside data/lexicon/source-inventory: "
            f"{inventory_path}"
        ) from exc
    return candidate


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SourceInventoryError(f"{path}: not found") from exc
    if not isinstance(payload, dict):
        raise SourceInventoryError(f"{path}: expected mapping")
    return payload


def _reject_unknown_fields(
    path: Path,
    mapping: Mapping[str, Any],
    *,
    allowed: set[str],
    scope: str,
) -> None:
    unknown = sorted(str(key) for key in mapping if key not in allowed)
    if unknown:
        raise SourceInventoryError(f"{path}: {scope} unknown field(s): {', '.join(unknown)}")


def _require_text(path: Path, value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceInventoryError(f"{path}: {field} must be non-empty text")
    return value.strip()


def _require_equal(path: Path, actual: object, expected: object, field: str) -> None:
    if actual != expected:
        raise SourceInventoryError(f"{path}: {field} must be {expected!r}")


def _require_positive_int(path: Path, value: object, field: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise SourceInventoryError(f"{path}: {field} must be a positive integer")
    return value


def _validate_surface_admission(path: Path, value: object, field: str) -> None:
    if not isinstance(value, Mapping):
        raise SourceInventoryError(f"{path}: {field} must be a mapping")
    unknown = sorted(set(value) - SURFACE_ADMISSION_FIELDS)
    if unknown:
        raise SourceInventoryError(f"{path}: {field} unknown keys {', '.join(unknown)}")
    for key, admitted in value.items():
        if not isinstance(admitted, bool):
            raise SourceInventoryError(f"{path}: {field}.{key} must be boolean")


def _validate_text_list(path: Path, value: object, field: str) -> None:
    if not isinstance(value, list) or not value:
        raise SourceInventoryError(f"{path}: {field} must be a non-empty list")
    for idx, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            raise SourceInventoryError(f"{path}: {field}[{idx}] must be non-empty text")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate tracked Word Atlas source-inventory review decisions."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help=f"Decision YAML paths (default: {DEFAULT_DECISION_DIR})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = validate_committed_decision_files(args.paths or None)
    except SourceInventoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(
        "source_inventory_review_decisions: "
        f"files={summary['files']} rows={summary['rows']} "
        f"decisions={summary['decision_counts']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
