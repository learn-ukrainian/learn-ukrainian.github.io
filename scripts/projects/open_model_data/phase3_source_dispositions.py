#!/usr/bin/env python3
"""Compile reviewed, text-free dispositions against the frozen Phase 3 universe.

This adapter deliberately does not classify Ukrainian source material.  It only
checks that externally reviewed rows form an exact, hash-bound disposition of
the nonlexical source ledgers and writes deterministic text-free receipts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from scripts.projects.open_model_data.phase3_source_universe import canonical_json, sha256_file

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
DEFAULT_SCHEMA = CONTRACTS / "phase3_source_disposition_input_v1.schema.json"
DEFAULT_ROLE_CONTRACT = ROOT / "data/projects/open_model_data/evidence/correction_protection_role_contract_v1.json"
FREEZE_RECEIPT_FILE = "source-universe-freeze-receipt.json"
OUTPUT_LEDGER_FILE = "phase3-source-dispositions.jsonl"
OUTPUT_RECEIPT_FILE = "phase3-source-dispositions-receipt.json"
OUTPUT_FILES = frozenset({OUTPUT_LEDGER_FILE, OUTPUT_RECEIPT_FILE})
INPUT_SCHEMA_VERSION = "phase3_source_disposition_input_v1"
OUTPUT_SCHEMA_VERSION = "phase3_source_disposition_receipt_v1"
SOURCE_REVIEW_RECEIPT_SCHEMA_VERSION = "phase3_source_disposition_review_receipt_v1"
DISPOSITION_CODES = frozenset({
    "converted", "not_rule_bearing", "duplicate_representation", "evaluation_only",
    "rights_limited_locator_only", "superseded_or_historical", "blocked_with_reason",
})
FAMILY_TOTALS = {
    "antonenko_style_guide": 342,
    "ua_gec": 8_937,
    "school_textbooks": 54_979,
    "antonenko_textbook_representation": 169,
    "calque_inventory": 58,
    "pravopys_2019_complete": 1_090,
    "pravopys_2026_complete": 1_466,
    "other_normative_style_inventory": 0,
}
FAMILY_IDS = frozenset(FAMILY_TOTALS)
ANTONENKO_REPRESENTATION_SOURCE_ID = "source_identity.antonenko_davydovych_yak_my_hovorymo_v1"


class DispositionError(ValueError):
    """A reviewed disposition input cannot be safely joined to the freeze."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DispositionError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DispositionError(f"cannot read {label}: {path}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _validate_input_schema(input_document: Mapping[str, Any], schema_path: Path) -> None:
    schema = _read_json(schema_path, "input schema")
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(dict(input_document))
    except SchemaError as exc:
        raise DispositionError(f"invalid disposition input schema: {exc.message}") from exc
    except ValidationError as exc:
        location = ".".join(str(part) for part in exc.path) or "<root>"
        raise DispositionError(f"disposition input schema violation at {location}: {exc.message}") from exc


def _load_role_bindings(role_contract_path: Path) -> dict[str, dict[str, str]]:
    contract = _read_json(role_contract_path, "role contract")
    seats = contract.get("seats")
    task_bindings = contract.get("task_bindings")
    require(isinstance(seats, list) and isinstance(task_bindings, list), "role contract lacks seats or task bindings")
    assigned_identities = [
        seat.get("controller_identity_id")
        for seat in seats
        if isinstance(seat, Mapping) and seat.get("assignment_state") == "assigned_verified"
    ]
    require(
        all(isinstance(identity, str) and identity for identity in assigned_identities)
        and len(assigned_identities) == len(set(assigned_identities)),
        "role contract assigned identities are not unique",
    )
    required_roles = ("rule_author_extractor", "ukrainian_source_reviewer")
    result: dict[str, dict[str, str]] = {}
    for role_id in required_roles:
        seat_matches = [seat for seat in seats if isinstance(seat, Mapping) and seat.get("role_id") == role_id]
        task_matches = [item for item in task_bindings if isinstance(item, Mapping) and item.get("role_id") == role_id]
        require(len(seat_matches) == 1 and len(task_matches) == 1, f"role contract must contain exactly one {role_id} binding")
        seat, task = seat_matches[0], task_matches[0]
        controller, task_id = seat.get("controller_identity_id"), task.get("reserved_task_id")
        require(seat.get("assignment_state") == "assigned_verified", f"{role_id} is not assigned and verified")
        require(seat.get("controller_identity_attested") is True, f"{role_id} identity is not attested")
        require(isinstance(controller, str) and controller, f"{role_id} lacks controller identity")
        require(isinstance(task_id, str) and task_id, f"{role_id} lacks task binding")
        require(task.get("controller_identity_id") == controller, f"{role_id} task binding controller drift")
        require(task.get("status") == "identity_attested_pre_artifact", f"{role_id} task binding is not pre-artifact attested")
        result[role_id] = {"controller_identity_id": controller, "task_id": task_id}
    require(
        result["rule_author_extractor"]["controller_identity_id"] != result["ukrainian_source_reviewer"]["controller_identity_id"],
        "role contract reuses extractor and source reviewer identity",
    )
    return result


def _validate_provenance_bindings(
    reviewed: Mapping[str, Any], role_contract_path: Path, source_review_receipt_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    require(source_review_receipt_path.is_file() and not source_review_receipt_path.is_symlink(), "source review receipt is missing")
    bindings = _load_role_bindings(role_contract_path)
    author = reviewed["author_binding"]
    reviewer = reviewed["source_review_binding"]
    require(author["controller_identity_id"] != reviewer["controller_identity_id"], "extractor and source reviewer identities must differ")
    for role_id, supplied in (("rule_author_extractor", author), ("ukrainian_source_reviewer", reviewer)):
        expected = bindings[role_id]
        require(supplied["role_id"] == role_id, f"{role_id} role binding mismatch")
        require(supplied["controller_identity_id"] == expected["controller_identity_id"], f"{role_id} controller binding mismatch")
        require(supplied["task_id"] == expected["task_id"], f"{role_id} task binding mismatch")
    require(reviewer["receipt_sha256"] == sha256_file(source_review_receipt_path), "source review receipt binding mismatch")
    receipt = _read_json(source_review_receipt_path, "source review receipt")
    require(
        set(receipt) == {
            "schema_version",
            "text_free",
            "reviewer_role_id",
            "controller_identity_id",
            "task_id",
            "source_freeze_receipt_sha256",
            "disposition_families_sha256",
            "verdict",
        },
        "source review receipt fields are not closed and complete",
    )
    require(
        receipt["schema_version"] == SOURCE_REVIEW_RECEIPT_SCHEMA_VERSION and receipt["text_free"] is True,
        "source review receipt schema or text-free boundary mismatch",
    )
    require(receipt["reviewer_role_id"] == "ukrainian_source_reviewer", "source review receipt role mismatch")
    require(receipt["controller_identity_id"] == reviewer["controller_identity_id"], "source review receipt controller mismatch")
    require(receipt["task_id"] == reviewer["task_id"], "source review receipt task mismatch")
    require(
        receipt["source_freeze_receipt_sha256"] == reviewed["source_freeze_receipt_sha256"],
        "source review receipt freeze binding mismatch",
    )
    require(
        receipt["disposition_families_sha256"]
        == sha256_bytes(canonical_json(reviewed["families"]).encode("utf-8")),
        "source review receipt disposition binding mismatch",
    )
    require(receipt["verdict"] == "APPROVE", "source review receipt does not approve the exact dispositions")
    return dict(author), dict(reviewer)


def _ledger_records(path: Path, family_id: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DispositionError(f"cannot read frozen ledger: {path.name}") from exc
    for ordinal, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DispositionError(f"invalid frozen ledger JSON: {path.name}:{ordinal}") from exc
        require(isinstance(record, Mapping), f"frozen ledger record is not an object: {path.name}:{ordinal}")
        require(record.get("family_id") == family_id, f"frozen ledger family mismatch: {path.name}:{ordinal}")
        unit_id, unit_hash, locator = record.get("unit_id"), record.get("unit_sha256"), record.get("locator")
        require(isinstance(unit_id, str) and isinstance(unit_hash, str) and isinstance(locator, Mapping), f"invalid frozen binding: {path.name}:{ordinal}")
        binding = (unit_id, unit_hash, sha256_bytes(canonical_json(dict(locator)).encode("utf-8")))
        require(binding not in seen, f"duplicate frozen unit binding: {family_id}:{ordinal}")
        seen.add(binding)
        records.append({"unit_id": binding[0], "unit_sha256": binding[1], "locator_sha256": binding[2]})
    return records


def _load_frozen_universe(source_freeze_dir: Path) -> tuple[dict[str, list[dict[str, str]]], str, dict[str, Any]]:
    receipt_path = source_freeze_dir / FREEZE_RECEIPT_FILE
    require(source_freeze_dir.is_dir() and not source_freeze_dir.is_symlink(), "source freeze directory is not a real directory")
    receipt = _read_json(receipt_path, "source freeze receipt")
    require(receipt.get("schema_version") == "phase3_source_universe_freeze_v1", "unsupported source freeze receipt")
    require(receipt.get("text_free") is True, "source freeze receipt is not text-free")
    families = receipt.get("families")
    require(isinstance(families, list), "source freeze receipt lacks families")
    descriptors = {item.get("family_id"): item for item in families if isinstance(item, Mapping)}
    require(set(descriptors) >= FAMILY_IDS, "source freeze receipt lacks a required disposition family")
    frozen: dict[str, list[dict[str, str]]] = {}
    for family_id in sorted(FAMILY_IDS):
        descriptor = descriptors[family_id]
        ledger_file = descriptor.get("ledger_file")
        unit_count = descriptor.get("unit_count")
        ledger_hash = descriptor.get("ledger_sha256")
        require(isinstance(ledger_file, str) and ledger_file == f"{family_id}.units.jsonl", f"wrong frozen ledger file: {family_id}")
        require(isinstance(unit_count, int) and unit_count == FAMILY_TOTALS[family_id], f"wrong frozen family total: {family_id}")
        require(isinstance(ledger_hash, str), f"frozen ledger lacks hash: {family_id}")
        ledger_path = source_freeze_dir / ledger_file
        require(ledger_path.is_file() and not ledger_path.is_symlink(), f"missing frozen ledger: {family_id}")
        require(sha256_file(ledger_path) == ledger_hash, f"frozen ledger hash mismatch: {family_id}")
        records = _ledger_records(ledger_path, family_id)
        require(len(records) == unit_count, f"frozen ledger count mismatch: {family_id}")
        frozen[family_id] = records
    return frozen, sha256_file(receipt_path), receipt


def _rolling_universe_sha256(rows: Iterable[Mapping[str, str]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        encoded = canonical_json(dict(row)).encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _validate_family_rows(family: Mapping[str, Any], frozen_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    family_id = str(family["family_id"])
    input_rows = family["dispositions"]
    require(isinstance(input_rows, list), f"dispositions must be a list: {family_id}")
    require(family["unit_count"] == len(frozen_rows), f"input family total mismatch: {family_id}")
    expected = {(row["unit_id"], row["unit_sha256"], row["locator_sha256"]) for row in frozen_rows}
    actual: set[tuple[str, str, str]] = set()
    reason_counts: Counter[str] = Counter()
    output: list[dict[str, Any]] = []
    for row in input_rows:
        require(isinstance(row, Mapping), f"disposition row is not an object: {family_id}")
        binding = (str(row["unit_id"]), str(row["unit_sha256"]), str(row["locator_sha256"]))
        require(binding not in actual, f"duplicate disposition unit binding: {family_id}")
        require(binding in expected, f"disposition unit binding does not match freeze: {family_id}")
        actual.add(binding)
        code = row["disposition_code"]
        require(code in DISPOSITION_CODES, f"illegal disposition code: {family_id}")
        if code == "converted":
            require("nonconversion" not in row, f"converted row carries nonconversion payload: {family_id}")
        if family_id == "antonenko_textbook_representation" and code == "duplicate_representation":
            require(
                row.get("representation_source_identity") == ANTONENKO_REPRESENTATION_SOURCE_ID,
                "Antonenko representation duplicate lacks deterministic source identity",
            )
        if code != "converted":
            nonconversion = row.get("nonconversion")
            require(isinstance(nonconversion, Mapping), f"nonconverted row lacks reason: {family_id}")
            reason_counts[str(nonconversion["reason_code"])] += 1
        output.append({"family_id": family_id, **dict(row)})
    require(len(input_rows) == len(frozen_rows), f"input disposition count mismatch: {family_id}")
    require(actual == expected, f"disposition omits or adds frozen units: {family_id}")
    for row in input_rows:
        if row["disposition_code"] == "converted":
            continue
        nonconversion = row["nonconversion"]
        if reason_counts[str(nonconversion["reason_code"])] >= 10:
            require(
                "reason_predicate_sha256" in nonconversion or "unit_specific_rationale_sha256" in nonconversion,
                f"repeated nonconversion reason lacks predicate or rationale: {family_id}",
            )
    return output


def _stage(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        return Path(handle.name)


def compile_dispositions(
    *,
    source_freeze_dir: Path,
    reviewed_input_path: Path,
    output_dir: Path,
    source_review_receipt_path: Path,
    schema_path: Path = DEFAULT_SCHEMA,
    role_contract_path: Path = DEFAULT_ROLE_CONTRACT,
) -> dict[str, Any]:
    """Fail closed unless reviewed input is an exact disposition of the freeze."""
    require(reviewed_input_path.is_file(), "reviewed disposition input is missing")
    require(schema_path.is_file(), "disposition input schema is missing")
    require(role_contract_path.is_file(), "role contract is missing")
    if output_dir.exists():
        require(output_dir.is_dir() and not output_dir.is_symlink(), "output directory is not a real directory")
        unexpected = {path.name for path in output_dir.iterdir()} - OUTPUT_FILES
        require(not unexpected, f"output directory contains stale or unexpected files: {sorted(unexpected)}")
    reviewed = _read_json(reviewed_input_path, "reviewed disposition input")
    _validate_input_schema(reviewed, schema_path)
    frozen, freeze_receipt_hash, _ = _load_frozen_universe(source_freeze_dir)
    require(reviewed["source_freeze_receipt_sha256"] == freeze_receipt_hash, "source freeze receipt binding mismatch")
    require(reviewed["role_contract_sha256"] == sha256_file(role_contract_path), "role contract binding mismatch")
    families = reviewed["families"]
    family_map = {item["family_id"]: item for item in families}
    require(len(family_map) == len(families) and set(family_map) == FAMILY_IDS, "reviewed input family set is not exact")
    all_rows: list[dict[str, Any]] = []
    family_receipts: list[dict[str, Any]] = []
    for family_id in sorted(FAMILY_IDS):
        family = family_map[family_id]
        source_ledger = source_freeze_dir / f"{family_id}.units.jsonl"
        require(family["ledger_sha256"] == sha256_file(source_ledger), f"input ledger binding mismatch: {family_id}")
        rows = _validate_family_rows(family, frozen[family_id])
        all_rows.extend(rows)
        frozen_bindings = sorted(frozen[family_id], key=lambda row: row["unit_id"])
        audit_bindings = sorted(
            ({key: str(row[key]) for key in ("unit_id", "unit_sha256", "locator_sha256")} for row in rows),
            key=lambda row: row["unit_id"],
        )
        family_receipts.append({
            "family_id": family_id,
            "frozen_input_identity_total": len(frozen[family_id]),
            "family_unit_total": FAMILY_TOTALS[family_id],
            "ledger_input_total": len(rows),
            "disposition_row_sum": len(rows),
            "ledger_universe_sha256": _rolling_universe_sha256(frozen_bindings),
            "audit_universe_sha256": _rolling_universe_sha256(audit_bindings),
        })
    for receipt in family_receipts:
        require(
            receipt["frozen_input_identity_total"] == receipt["family_unit_total"] == receipt["ledger_input_total"] == receipt["disposition_row_sum"],
            f"disposition receipt equality failure: {receipt['family_id']}",
        )
        require(receipt["ledger_universe_sha256"] == receipt["audit_universe_sha256"], f"universe hash mismatch: {receipt['family_id']}")
    author_binding, source_review_binding = _validate_provenance_bindings(
        reviewed, role_contract_path, source_review_receipt_path,
    )
    all_rows.sort(key=lambda row: (str(row["family_id"]), str(row["unit_id"])))
    ledger_bytes = b"".join((canonical_json(row) + "\n").encode("utf-8") for row in all_rows)
    zero_receipt = {
        "family_id": "other_normative_style_inventory",
        "frozen_input_identity_total": 0,
        "input_disposition_row_count": 0,
        "output_disposition_row_count": 0,
        "status": "ZERO_FAMILY_ACCOUNTED",
    }
    receipt = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "text_free": True,
        "source_freeze_receipt_sha256": freeze_receipt_hash,
        "role_contract_sha256": sha256_file(role_contract_path),
        "reviewed_input_sha256": sha256_file(reviewed_input_path),
        "author_binding": author_binding,
        "source_review_binding": source_review_binding,
        "families": family_receipts,
        "zero_family_receipt": zero_receipt,
        "disposition_ledger": {"path": OUTPUT_LEDGER_FILE, "sha256": sha256_bytes(ledger_bytes), "row_count": len(all_rows)},
    }
    receipt_bytes = (canonical_json(receipt) + "\n").encode("utf-8")
    staged: list[tuple[Path, Path]] = []
    try:
        staged = [
            (_stage(output_dir / OUTPUT_LEDGER_FILE, ledger_bytes), output_dir / OUTPUT_LEDGER_FILE),
            (_stage(output_dir / OUTPUT_RECEIPT_FILE, receipt_bytes), output_dir / OUTPUT_RECEIPT_FILE),
        ]
        for temporary, target in staged:
            os.replace(temporary, target)
    except Exception:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
        raise
    return receipt


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile reviewed text-free Phase 3 source dispositions.")
    parser.add_argument("--source-freeze-dir", type=Path, required=True)
    parser.add_argument("--reviewed-input", dest="reviewed_input_path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-review-receipt", dest="source_review_receipt_path", type=Path, required=True)
    parser.add_argument("--schema", dest="schema_path", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--role-contract", dest="role_contract_path", type=Path, default=DEFAULT_ROLE_CONTRACT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        receipt = compile_dispositions(**vars(parse_args(argv)))
    except DispositionError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    print(canonical_json({"ok": True, "receipt": OUTPUT_RECEIPT_FILE, "rows": receipt["disposition_ledger"]["row_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
