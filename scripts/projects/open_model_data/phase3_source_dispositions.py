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
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from scripts.projects.open_model_data import phase3_disposition_audit as disposition_audit
from scripts.projects.open_model_data import phase3_functional_roles as functional_roles
from scripts.projects.open_model_data.phase3_source_universe import canonical_json, sha256_file

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
DEFAULT_SCHEMA = CONTRACTS / "phase3_source_disposition_input_v1.schema.json"
DEFAULT_ROLE_CONTRACT = (
    ROOT / "data/projects/open_model_data/evidence/correction_protection_functional_role_contract_v2_1.json"
)
FREEZE_RECEIPT_FILE = "source-universe-freeze-receipt.json"
OUTPUT_LEDGER_FILE = "phase3-source-dispositions.jsonl"
OUTPUT_AUDIT_LEDGER_FILE = "phase3-disposition-ledger.json"
OUTPUT_RECEIPT_FILE = "phase3-source-dispositions-receipt.json"
OUTPUT_FILES = frozenset({OUTPUT_LEDGER_FILE, OUTPUT_AUDIT_LEDGER_FILE, OUTPUT_RECEIPT_FILE})
INPUT_SCHEMA_VERSION = "phase3_source_disposition_input_v2_2"
OUTPUT_SCHEMA_VERSION = "phase3_source_disposition_receipt_v2_1"
SOURCE_REVIEW_RECEIPT_SCHEMA_VERSION = "phase3_source_disposition_review_receipt_v2_1"
PRODUCER_TASK_ID = "phase3-v2-1-disposition-ledger-production"
ROLE_PROVIDERS = {
    "rule_author_extractor": "google",
    "ukrainian_source_reviewer": "xai",
}
DISPOSITION_CODES = frozenset({
    "converted", "not_rule_bearing", "duplicate_representation", "evaluation_only",
    "superseded_or_historical", "blocked_with_reason",
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


def _load_role_bindings(role_contract_path: Path) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    contract = _read_json(role_contract_path, "role contract")
    try:
        verified = functional_roles.verify_value(contract)
        result = {
            role_id: functional_roles.binding_for_role(verified, role_id)
            for role_id in ("rule_author_extractor", "ukrainian_source_reviewer")
        }
    except functional_roles.FunctionalRoleError as exc:
        raise DispositionError(str(exc)) from exc
    require(
        result["rule_author_extractor"]["task_id"] != result["ukrainian_source_reviewer"]["task_id"],
        "role contract reuses extractor and source reviewer task",
    )
    require(
        functional_roles.tasks_conflict(
            verified,
            result["rule_author_extractor"]["task_id"],
            result["ukrainian_source_reviewer"]["task_id"],
        ),
        "role graph lacks the author-to-source-review edge",
    )
    return verified, result


def _validate_action_receipt(
    action: Mapping[str, Any],
    *,
    role_contract: Mapping[str, Any],
    role_contract_path: Path,
    actor: Mapping[str, str],
    action_kind: str,
    input_manifest_sha256: str,
    output_sha256: str,
) -> None:
    require(set(action) == set(functional_roles.ACTION_RECEIPT_FIELDS), "functional action receipt fields drift")
    require(
        action.get("role_id") == actor["role_id"]
        and action.get("task_id") == actor["task_id"],
        "functional action receipt task binding mismatch",
    )
    role = next(item for item in role_contract["functional_roles"] if item["role_id"] == actor["role_id"])
    require(
        all(action.get(key) == role[key] for key in ("exact_model", "model_family", "harness")),
        "functional action receipt lane mismatch",
    )
    require(
        action.get("provider") == ROLE_PROVIDERS[actor["role_id"]],
        "functional action provider mismatch",
    )
    require(action.get("action_kind") == action_kind, "functional action kind mismatch")
    require(action.get("input_manifest_sha256") == input_manifest_sha256, "functional action input mismatch")
    require(action.get("output_sha256") == output_sha256, "functional action output mismatch")
    require(
        action.get("evaluation_cycle_id") == role_contract["evaluation_cycle"]["evaluation_cycle_id"],
        "functional action evaluation-cycle binding mismatch",
    )
    require(
        action.get("base_contract_sha256") == functional_roles.BASE_SHA256
        and action.get("amendment_sha256") == functional_roles.AMENDMENT_SHA256
        and action.get("combined_contract_sha256") == functional_roles.COMBINED_SHA256,
        "functional action contract binding mismatch",
    )
    require(
        action.get("functional_role_contract_sha256") == sha256_file(role_contract_path)
        and action.get("conflict_graph_sha256") == functional_roles.conflict_graph_sha256(role_contract),
        "functional action role-graph binding mismatch",
    )
    require(action.get("status") == "completed", "functional action is not complete")
    require(
        all(isinstance(action.get(key), str) and action[key] for key in ("receipt_id", "started_at", "completed_at")),
        "functional action metadata incomplete",
    )
    identity = {
        key: action[key]
        for key in ("role_id", "task_id", "input_manifest_sha256", "evaluation_cycle_id", "output_sha256", "status")
    }
    require(
        action["receipt_id"]
        == "phase3_functional_action:" + sha256_bytes(canonical_json(identity).encode("utf-8")),
        "functional action receipt ID mismatch",
    )


def _validate_provenance_bindings(
    reviewed: Mapping[str, Any], role_contract_path: Path, source_review_receipt_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    require(source_review_receipt_path.is_file() and not source_review_receipt_path.is_symlink(), "source review receipt is missing")
    role_contract, bindings = _load_role_bindings(role_contract_path)
    author = reviewed["author_binding"]
    reviewer = reviewed["source_review_binding"]
    require(author["task_id"] != reviewer["task_id"], "extractor and source reviewer tasks must differ")
    for role_id, supplied in (("rule_author_extractor", author), ("ukrainian_source_reviewer", reviewer)):
        expected = bindings[role_id]
        require(supplied["role_id"] == role_id, f"{role_id} role binding mismatch")
        require(supplied["task_id"] == expected["task_id"], f"{role_id} task binding mismatch")
    require(reviewer["receipt_sha256"] == sha256_file(source_review_receipt_path), "source review receipt binding mismatch")
    receipt = _read_json(source_review_receipt_path, "source review receipt")
    require(
        set(receipt) == {
            "schema_version",
            "text_free",
            "reviewer_role_id",
            "task_id",
            "source_freeze_receipt_sha256",
            "disposition_families_sha256",
            "reviewed_rule_artifacts_sha256",
            "verdict",
            "action_receipt",
        },
        "source review receipt fields are not closed and complete",
    )
    require(
        receipt["schema_version"] == SOURCE_REVIEW_RECEIPT_SCHEMA_VERSION and receipt["text_free"] is True,
        "source review receipt schema or text-free boundary mismatch",
    )
    require(receipt["reviewer_role_id"] == "ukrainian_source_reviewer", "source review receipt role mismatch")
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
    require(
        receipt["reviewed_rule_artifacts_sha256"] == reviewed["reviewed_rule_artifacts_sha256"],
        "source review receipt reviewed-rule-artifacts binding mismatch",
    )
    require(receipt["verdict"] == "APPROVE", "source review receipt does not approve the exact dispositions")
    author_action = author.get("action_receipt")
    require(isinstance(author_action, Mapping), "source disposition proposal lacks action receipt")
    families_sha256 = receipt["disposition_families_sha256"]
    _validate_action_receipt(
        author_action,
        role_contract=role_contract,
        role_contract_path=role_contract_path,
        actor=author,
        action_kind="source_disposition_proposal",
        input_manifest_sha256=sha256_bytes(
            canonical_json(
                {"source_freeze_receipt_sha256": receipt["source_freeze_receipt_sha256"]}
            ).encode("utf-8")
        ),
        output_sha256=families_sha256,
    )
    review_input_sha256 = sha256_bytes(
        canonical_json(
            {
                "source_freeze_receipt_sha256": receipt["source_freeze_receipt_sha256"],
                "disposition_families_sha256": families_sha256,
                "author_action_receipt_id": author_action["receipt_id"],
            }
        ).encode("utf-8")
    )
    action = receipt.get("action_receipt")
    require(isinstance(action, Mapping), "source review receipt lacks action receipt")
    _validate_action_receipt(
        action,
        role_contract=role_contract,
        role_contract_path=role_contract_path,
        actor=reviewer,
        action_kind="source_disposition_review",
        input_manifest_sha256=review_input_sha256,
        output_sha256=sha256_bytes(canonical_json({"verdict": "APPROVE"}).encode("utf-8")),
    )
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


def _audit_locator(prefix: str, sha256: str) -> str:
    """Render a text-free immutable locator accepted by the audit runtime."""
    return f"{prefix}.{sha256}"


def _audit_shape_row(row: Mapping[str, Any], repeated_reason_count: int | None) -> dict[str, Any]:
    """Translate a schema-validated review row into the audit's closed v2.1 shape."""
    converted = row["disposition_code"] == "converted"
    if converted:
        consumer = row["consumer_view"]
        return {
            "unit_id": row["unit_id"],
            "unit_sha256": row["unit_sha256"],
            "unit_locator_sha256": row["locator_sha256"],
            "disposition_code": row["disposition_code"],
            "document_or_edition_identity": row["document_or_edition_identity"],
            "source_role": row["source_role"],
            "claim_type": row["claim_type"],
            "canonical_content_identity": row["canonical_identity"],
            "evidence_artifact_locators": [
                _audit_locator("evidence", value) for value in row["evidence_locator_sha256s"]
            ],
            "consumer_view_ids": [consumer["view_id"]],
            "conversion_predicate_locator": _audit_locator("predicate", row["predicate_sha256"]),
            "reason_locator": None,
            "repeated_reason_count": None,
            "predicate_or_rationale_locator": None,
        }
    nonconversion = row["nonconversion"]
    reason_locator = f"reason.{nonconversion['reason_code']}"
    predicate_or_rationale_sha256 = nonconversion.get("reason_predicate_sha256") or nonconversion.get(
        "unit_specific_rationale_sha256"
    )
    return {
        "unit_id": row["unit_id"],
        "unit_sha256": row["unit_sha256"],
        "unit_locator_sha256": row["locator_sha256"],
        "disposition_code": row["disposition_code"],
        "document_or_edition_identity": row["document_or_edition_identity"],
        "source_role": None,
        "claim_type": None,
        "canonical_content_identity": None,
        "evidence_artifact_locators": [],
        "consumer_view_ids": [],
        "conversion_predicate_locator": None,
        "reason_locator": reason_locator,
        "repeated_reason_count": repeated_reason_count,
        "predicate_or_rationale_locator": (
            _audit_locator("predicate_or_rationale", predicate_or_rationale_sha256)
            if repeated_reason_count is not None and repeated_reason_count >= 10
            else None
        ),
    }


def _audit_shape_ledger(
    *,
    source_freeze_receipt: Mapping[str, Any],
    source_freeze_receipt_sha256: str,
    coverage_contract: Mapping[str, Any],
    role_contract_sha256: str,
    conflict_graph_sha256: str,
    family_receipts: list[dict[str, Any]],
    family_rows: Mapping[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Build the exact closed ledger consumed by the independent audit runtime."""
    artifact_manifest = source_freeze_receipt.get("artifact_manifest")
    require(isinstance(artifact_manifest, Mapping), "source freeze lacks artifact manifest for audit ledger")
    payload_manifest_sha256 = artifact_manifest.get("payload_manifest_sha256")
    require(isinstance(payload_manifest_sha256, str), "source freeze lacks payload manifest hash for audit ledger")
    audit_families: list[dict[str, Any]] = []
    receipts_by_family = {item["family_id"]: item for item in family_receipts}
    for family_id in sorted(FAMILY_IDS):
        rows = family_rows[family_id]
        reason_counts = Counter(
            f"reason.{row['nonconversion']['reason_code']}"
            for row in rows
            if row["disposition_code"] != "converted"
        )
        translated = [
            _audit_shape_row(
                row,
                reason_counts[f"reason.{row['nonconversion']['reason_code']}"]
                if row["disposition_code"] != "converted"
                else None,
            )
            for row in rows
        ]
        translated.sort(key=lambda row: row["unit_id"])
        audit_families.append({**receipts_by_family[family_id], "rows": translated})
    return {
        "schema_version": "phase3_disposition_ledger_v2_1",
        "text_free": True,
        "source_universe_receipt_sha256": source_freeze_receipt_sha256,
        "source_universe_payload_manifest_sha256": payload_manifest_sha256,
        "coverage_contract_sha256": disposition_audit.sha256_value(coverage_contract),
        "base_contract_sha256": functional_roles.BASE_SHA256,
        "amendment_sha256": functional_roles.AMENDMENT_SHA256,
        "combined_contract_sha256": functional_roles.COMBINED_SHA256,
        "functional_role_contract_sha256": role_contract_sha256,
        "conflict_graph_sha256": conflict_graph_sha256,
        "repair_generation": 0,
        "families": audit_families,
    }


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
    audit_coverage_contract_path: Path = disposition_audit.DEFAULT_COVERAGE_CONTRACT,
) -> dict[str, Any]:
    """Fail closed unless reviewed input is an exact disposition of the freeze."""
    require(reviewed_input_path.is_file(), "reviewed disposition input is missing")
    require(schema_path.is_file(), "disposition input schema is missing")
    require(role_contract_path.is_file(), "role contract is missing")
    require(audit_coverage_contract_path.is_file(), "audit coverage contract is missing")
    if output_dir.exists():
        require(output_dir.is_dir() and not output_dir.is_symlink(), "output directory is not a real directory")
        unexpected = {path.name for path in output_dir.iterdir()} - OUTPUT_FILES
        require(not unexpected, f"output directory contains stale or unexpected files: {sorted(unexpected)}")
    reviewed = _read_json(reviewed_input_path, "reviewed disposition input")
    _validate_input_schema(reviewed, schema_path)
    require(
        reviewed["phase3_v2_contract_sha256"] == functional_roles.BASE_SHA256
        and reviewed["phase3_v2_1_amendment_sha256"] == functional_roles.AMENDMENT_SHA256
        and reviewed["combined_contract_sha256"] == functional_roles.COMBINED_SHA256,
        "Phase 3 v2.1 contract binding mismatch",
    )
    require(reviewed["producer_task_id"] == PRODUCER_TASK_ID, "disposition producer task binding mismatch")
    role_contract = _read_json(role_contract_path, "role contract")
    try:
        functional_roles.verify_value(role_contract)
    except functional_roles.FunctionalRoleError as exc:
        raise DispositionError(str(exc)) from exc
    require(
        reviewed["conflict_graph_sha256"] == functional_roles.conflict_graph_sha256(role_contract),
        "role conflict-graph binding mismatch",
    )
    frozen, freeze_receipt_hash, source_freeze_receipt = _load_frozen_universe(source_freeze_dir)
    require(reviewed["source_freeze_receipt_sha256"] == freeze_receipt_hash, "source freeze receipt binding mismatch")
    require(reviewed["role_contract_sha256"] == sha256_file(role_contract_path), "role contract binding mismatch")
    families = reviewed["families"]
    family_map = {item["family_id"]: item for item in families}
    require(len(family_map) == len(families) and set(family_map) == FAMILY_IDS, "reviewed input family set is not exact")
    all_rows: list[dict[str, Any]] = []
    rows_by_family: dict[str, list[dict[str, Any]]] = {}
    family_receipts: list[dict[str, Any]] = []
    for family_id in sorted(FAMILY_IDS):
        family = family_map[family_id]
        source_ledger = source_freeze_dir / f"{family_id}.units.jsonl"
        require(family["ledger_sha256"] == sha256_file(source_ledger), f"input ledger binding mismatch: {family_id}")
        rows = _validate_family_rows(family, frozen[family_id])
        all_rows.extend(rows)
        rows_by_family[family_id] = rows
        audit_bindings = [
            {"unit_id": row["unit_id"], "unit_sha256": row["unit_sha256"]}
            for row in frozen[family_id]
        ]
        audit_universe_sha256 = disposition_audit.source_family_universe_sha256(audit_bindings)
        family_receipts.append({
            "family_id": family_id,
            "frozen_input_identity_total": len(frozen[family_id]),
            "family_unit_total": FAMILY_TOTALS[family_id],
            "ledger_input_total": len(rows),
            "disposition_row_sum": len(rows),
            "ledger_universe_sha256": audit_universe_sha256,
            "audit_universe_sha256": audit_universe_sha256,
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
    audit_coverage_contract = _read_json(audit_coverage_contract_path, "audit coverage contract")
    audit_ledger = _audit_shape_ledger(
        source_freeze_receipt=source_freeze_receipt,
        source_freeze_receipt_sha256=freeze_receipt_hash,
        coverage_contract=audit_coverage_contract,
        role_contract_sha256=sha256_file(role_contract_path),
        conflict_graph_sha256=functional_roles.conflict_graph_sha256(role_contract),
        family_receipts=family_receipts,
        family_rows=rows_by_family,
    )
    audit_ledger_bytes = (canonical_json(audit_ledger) + "\n").encode("utf-8")
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
        "phase3_v2_contract_sha256": functional_roles.BASE_SHA256,
        "phase3_v2_1_amendment_sha256": functional_roles.AMENDMENT_SHA256,
        "combined_contract_sha256": functional_roles.COMBINED_SHA256,
        "producer_task_id": PRODUCER_TASK_ID,
        "source_freeze_receipt_sha256": freeze_receipt_hash,
        "role_contract_sha256": sha256_file(role_contract_path),
        "conflict_graph_sha256": functional_roles.conflict_graph_sha256(role_contract),
        "reviewed_input_sha256": sha256_file(reviewed_input_path),
        "author_binding": author_binding,
        "source_review_binding": source_review_binding,
        "families": family_receipts,
        "zero_family_receipt": zero_receipt,
        "disposition_ledger": {"path": OUTPUT_LEDGER_FILE, "sha256": sha256_bytes(ledger_bytes), "row_count": len(all_rows)},
        "audit_disposition_ledger": {
            "path": OUTPUT_AUDIT_LEDGER_FILE,
            "sha256": sha256_bytes(audit_ledger_bytes),
            "row_count": len(all_rows),
        },
    }
    receipt_bytes = (canonical_json(receipt) + "\n").encode("utf-8")
    staged: list[tuple[Path, Path]] = []
    try:
        staged = [
            (_stage(output_dir / OUTPUT_LEDGER_FILE, ledger_bytes), output_dir / OUTPUT_LEDGER_FILE),
            (_stage(output_dir / OUTPUT_AUDIT_LEDGER_FILE, audit_ledger_bytes), output_dir / OUTPUT_AUDIT_LEDGER_FILE),
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
    parser.add_argument(
        "--audit-coverage-contract",
        dest="audit_coverage_contract_path",
        type=Path,
        default=disposition_audit.DEFAULT_COVERAGE_CONTRACT,
    )
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
