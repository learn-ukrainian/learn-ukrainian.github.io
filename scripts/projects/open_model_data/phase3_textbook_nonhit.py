#!/usr/bin/env python3
"""Freeze and sample the text-free Phase 3 textbook non-hit population.

This is deliberately not a linguistic scanner.  It imports classifications made
by an authorised external lane (or neutral empty classifications), preserves the
complete frozen chunk identity universe, and provides the deterministic audit
draw/validation boundary.  Source text is never read or written by this module.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import sqlite3
import tempfile
import unicodedata
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_functional_roles as functional_roles

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
BUNDLE_SCHEMA = CONTRACTS / "phase3_textbook_nonhit_bundle_v1.schema.json"
COVERAGE_SCHEMA = CONTRACTS / "correction_protection_coverage_contract_v1.schema.json"
ROLE_SCHEMA = CONTRACTS / "correction_protection_functional_role_contract_v2_1.schema.json"
SOURCE_FREEZE_SCHEMA = CONTRACTS / "phase3_source_universe_freeze_v1.schema.json"

EXPECTED_UNIT_TOTAL = 54_979
EXPECTED_TRACKED_FILE_TOTAL = 168
EXPECTED_SECTION_TOTAL = 7_250
SCANNER_IMPLEMENTATION_VERSION = "phase3_textbook_nonhit_v1"
SCANNER_SCRIPT_PATH = "scripts/projects/open_model_data/phase3_textbook_nonhit.py"
SAMPLER_VERSION = "phase3_textbook_nonhit_hamilton_v1"
AUDITOR_ROLE_ID = "textbook_nonhit_auditor"
SCANNER_IMPLEMENTATION_TASK_ID = "phase3-v2-1-textbook-scanner-implementation"
APPROVED_ENTROPY_MODULE = "scripts.projects.open_model_data.phase3_audit_entropy"
APPROVED_ENTROPY_VERIFIER = "verify_entropy_receipt"
CANDIDATE_CLASSES = (
    "rule_bearing",
    "error_correction",
    "editing_exercise",
    "contrast",
    "metalinguistic_candidate",
)
AUDIT_DECISIONS = ("agree", "missed_candidate", "ambiguous_eligibility")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
FORBIDDEN_TEXT_FIELDS = frozenset({"body", "content", "excerpt", "snippet", "source_text", "text"})


class TextbookNonhitError(ValueError):
    """The source-free scanner audit boundary has been violated."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _hash(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def _normal(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, Mapping):
        return {str(key): _normal(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normal(item) for item in value]
    return value


def _source_universe_unit_id(row_id: int) -> str:
    payload = {"table": "textbooks", "identity": {"id": row_id}}
    return f"unit.school_textbooks.{_hash(_normal(payload))}"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TextbookNonhitError(message)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TextbookNonhitError(f"cannot read JSON input: {path}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def _validate_schema(value: Mapping[str, Any], schema_path: Path, label: str) -> None:
    schema = _read_json(schema_path)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))
    if errors:
        location = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise TextbookNonhitError(f"{label} schema violation at {location}: {errors[0].message}")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        raise TextbookNonhitError(f"cannot read JSONL input: {path}") from exc
    with handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise TextbookNonhitError(f"invalid JSONL at {path}:{line_number}") from exc
            require(isinstance(value, dict), f"expected object at {path}:{line_number}")
            rows.append(value)
    return rows


def _unit_identity(row: Mapping[str, Any]) -> dict[str, Any]:
    require(not (FORBIDDEN_TEXT_FIELDS & set(row)), "source text is forbidden from textbook scanner artifacts")
    required = {"unit_id", "unit_sha256", "locator"}
    require(required <= set(row), "frozen school textbook unit lacks identity fields")
    unit_id, unit_hash, locator = row["unit_id"], row["unit_sha256"], row["locator"]
    require(isinstance(unit_id, str) and unit_id.startswith("unit.school_textbooks."), "invalid textbook unit_id")
    require(isinstance(unit_hash, str) and SHA256.fullmatch(unit_hash) is not None, "invalid textbook unit_sha256")
    require(isinstance(locator, Mapping), "invalid textbook unit locator")
    return {"unit_id": unit_id, "unit_sha256": unit_hash, "locator": dict(locator)}


def _load_source_units(path: Path) -> tuple[list[dict[str, Any]], str]:
    rows = _read_jsonl(path)
    units = [_unit_identity(row) for row in rows]
    require(len(units) == EXPECTED_UNIT_TOTAL, f"school textbook denominator must be {EXPECTED_UNIT_TOTAL}, got {len(units)}")
    unit_ids = [unit["unit_id"] for unit in units]
    require(len(set(unit_ids)) == len(unit_ids), "duplicate frozen textbook unit_id")
    identities = sorted(units, key=lambda item: str(item["unit_id"]))
    return identities, sha256_file(path)


def _school_family(receipt: Mapping[str, Any]) -> Mapping[str, Any]:
    families = receipt.get("families")
    require(isinstance(families, list), "source freeze lacks family receipts")
    matches = [family for family in families if isinstance(family, Mapping) and family.get("family_id") == "school_textbooks"]
    require(len(matches) == 1, "source freeze lacks one school_textbooks receipt")
    family = matches[0]
    require(family.get("unit_count") == EXPECTED_UNIT_TOTAL, "source freeze textbook denominator changed")
    require(isinstance(family.get("ledger_sha256"), str) and SHA256.fullmatch(str(family["ledger_sha256"])) is not None, "source freeze lacks textbook ledger hash")
    return family


def _functional_bindings(
    roles: Mapping[str, Any], *, role_contract_path: Path,
) -> dict[str, str]:
    """Resolve the one functional task allowed to attest textbook non-hits."""
    try:
        verified = functional_roles.verify_value(roles)
    except functional_roles.FunctionalRoleError as exc:
        raise TextbookNonhitError(str(exc)) from exc
    require(
        canonical_json(_read_json(role_contract_path)) == canonical_json(verified),
        "functional-role ledger path does not match supplied ledger",
    )
    try:
        auditor = functional_roles.binding_for_role(verified, AUDITOR_ROLE_ID)
        rubric_author = functional_roles.binding_for_role(verified, "ukrainian_source_reviewer")
        scope_critic = functional_roles.binding_for_role(verified, "scope_circularity_critic")
    except functional_roles.FunctionalRoleError as exc:
        raise TextbookNonhitError(str(exc)) from exc
    require(
        functional_roles.tasks_conflict(verified, SCANNER_IMPLEMENTATION_TASK_ID, auditor["task_id"]),
        "functional-role graph lacks scanner-to-textbook-nonhit-audit edge",
    )
    return {
        "base_contract_sha256": functional_roles.BASE_SHA256,
        "amendment_sha256": functional_roles.AMENDMENT_SHA256,
        "combined_contract_sha256": functional_roles.COMBINED_SHA256,
        "functional_role_contract_sha256": sha256_file(role_contract_path),
        "conflict_graph_sha256": functional_roles.conflict_graph_sha256(verified),
        "evaluation_cycle_id": str(verified["evaluation_cycle"]["evaluation_cycle_id"]),
        "auditor_role_id": auditor["role_id"],
        "auditor_task_id": auditor["task_id"],
        "auditor_execution": _role_execution(verified, AUDITOR_ROLE_ID),
        "rubric_author": rubric_author,
        "rubric_author_execution": _role_execution(verified, "ukrainian_source_reviewer"),
        "scope_critic": scope_critic,
        "scope_critic_execution": _role_execution(verified, "scope_circularity_critic"),
    }


def _role_execution(roles: Mapping[str, Any], role_id: str) -> dict[str, str]:
    role = next(item for item in roles["functional_roles"] if item["role_id"] == role_id)
    return {name: str(role[name]) for name in ("exact_model", "model_family", "harness")}


def _validate_functional_action_receipt(
    receipt: Mapping[str, Any],
    *,
    role_binding: Mapping[str, str],
    execution: Mapping[str, str],
    bindings: Mapping[str, Any],
    action_kind: str,
    input_manifest_sha256: str,
    output_sha256: str,
    label: str,
) -> None:
    require(set(receipt) == set(functional_roles.ACTION_RECEIPT_FIELDS), f"{label} action receipt fields drift")
    require(
        receipt.get("role_id") == role_binding["role_id"]
        and receipt.get("task_id") == role_binding["task_id"],
        f"{label} action receipt task binding drift",
    )
    require(receipt.get("action_kind") == action_kind, f"{label} action kind drift")
    require(
        all(receipt.get(key) == execution[key] for key in ("exact_model", "model_family", "harness")),
        f"{label} action execution lane drift",
    )
    require(isinstance(receipt.get("provider"), str) and receipt["provider"], f"{label} action provider missing")
    require(
        receipt.get("input_manifest_sha256") == input_manifest_sha256
        and receipt.get("output_sha256") == output_sha256,
        f"{label} action input/output binding drift",
    )
    require(
        receipt.get("evaluation_cycle_id") == bindings["evaluation_cycle_id"]
        and all(receipt.get(name) == bindings[name] for name in (
            "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256",
        )),
        f"{label} action functional-role binding drift",
    )
    require(receipt.get("status") == "completed", f"{label} action is not complete")
    require(
        all(isinstance(receipt.get(name), str) and receipt[name] for name in ("receipt_id", "started_at", "completed_at")),
        f"{label} action metadata incomplete",
    )
    identity = {
        name: receipt[name]
        for name in ("role_id", "task_id", "input_manifest_sha256", "evaluation_cycle_id", "output_sha256", "status")
    }
    require(
        receipt["receipt_id"] == "phase3_functional_action:" + _hash(identity),
        f"{label} action receipt ID mismatch",
    )


def _validate_auditor_action_receipt(
    receipt: Mapping[str, Any],
    *,
    bindings: Mapping[str, Any],
    input_manifest_sha256: str,
    output_sha256: str,
) -> None:
    """Require an actual closed action receipt; local mechanics are not an audit."""
    _validate_functional_action_receipt(
        receipt, role_binding=bindings["auditor_role_binding"], execution=bindings["auditor_execution"],
        bindings=bindings, action_kind="textbook_nonhit_audit_results",
        input_manifest_sha256=input_manifest_sha256, output_sha256=output_sha256, label="auditor",
    )


def _metadata_index(
    sources_db: Path,
    frozen_units: Sequence[Mapping[str, Any]],
    source_freeze: Mapping[str, Any],
) -> dict[str, Any]:
    """Reconstruct frozen unit IDs using only explicit non-text DB columns."""
    require(sources_db.is_file() and sources_db.stat().st_size > 0, "missing sources database")
    db_sha256 = sha256_file(sources_db)
    receipt_hash = source_freeze.get("input_sha256", {}).get("sources_db")
    require(receipt_hash == db_sha256, "sources database does not match source freeze")
    connection = sqlite3.connect(sources_db.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    try:
        textbook_columns = {row[1] for row in connection.execute('PRAGMA table_info("textbooks")')}
        required = {"id", "chunk_id", "source_file", "grade", "author", "char_count", "parent_section_id", "author_uk", "subject"}
        require(required <= textbook_columns, "textbooks lacks required non-text identity metadata")
        rows = connection.execute(
            'SELECT "id", "chunk_id", "source_file", "grade", "author", "char_count", '
            '"parent_section_id", "author_uk", "subject" FROM "textbooks" ORDER BY "id"'
        ).fetchall()
        section_columns = {row[1] for row in connection.execute('PRAGMA table_info("textbook_sections")')}
        section_required = {"section_id", "source_file", "grade", "section_number", "page_start", "page_end", "chunk_count"}
        require(section_required <= section_columns, "textbook_sections lacks required non-text metadata")
        sections = connection.execute(
            'SELECT "section_id", "source_file", "grade", "section_number", "page_start", '
            '"page_end", "chunk_count" FROM "textbook_sections" ORDER BY "section_id"'
        ).fetchall()
    finally:
        connection.close()
    require(len(rows) == EXPECTED_UNIT_TOTAL, f"sources DB textbook denominator must be {EXPECTED_UNIT_TOTAL}")
    require(len(sections) == EXPECTED_SECTION_TOTAL, f"section metadata denominator must be {EXPECTED_SECTION_TOTAL}")
    section_by_id = {row["section_id"]: row for row in sections}
    section_records = [_normal(dict(row)) for row in sections]
    section_hash_by_file: dict[str, str] = {}
    grouped_sections: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in section_records:
        grouped_sections[str(row["source_file"])].append(row)
    for source_file, values in grouped_sections.items():
        section_hash_by_file[source_file] = _hash(values)
    frozen_by_id = {str(unit["unit_id"]): unit for unit in frozen_units}
    index_rows: list[dict[str, Any]] = []
    for row in rows:
        row_id = row["id"]
        require(isinstance(row_id, int), "textbook primary key is not an integer")
        unit_id = _source_universe_unit_id(row_id)
        require(unit_id in frozen_by_id, "sources DB textbook row is absent from frozen unit ledger")
        source_file = row["source_file"]
        require(isinstance(source_file, str) and source_file, "textbook row lacks tracked source_file")
        parent = row["parent_section_id"]
        if parent is not None:
            require(parent in section_by_id, "textbook parent section is absent from section metadata")
            require(section_by_id[parent]["source_file"] == source_file, "textbook parent section source mismatch")
        source_basis = {
            "source_file": source_file,
            "grade": row["grade"],
            "author": row["author"],
            "author_uk": row["author_uk"],
            "subject": row["subject"],
            "section_metadata_sha256": section_hash_by_file.get(source_file),
        }
        metadata_basis = _normal(dict(row))
        index_rows.append({
            "unit_id": unit_id,
            "tracked_file": source_file,
            "source_identity": f"source.school_textbooks.{_hash(_normal(source_basis))}",
            "metadata_sha256": _hash(metadata_basis),
        })
    index_rows.sort(key=lambda item: item["unit_id"])
    index_ids = {row["unit_id"] for row in index_rows}
    require(len(index_ids) == EXPECTED_UNIT_TOTAL and index_ids == set(frozen_by_id), "metadata index is not a bijection with frozen units")
    tracked_files = {row["tracked_file"] for row in index_rows}
    require(len(tracked_files) == EXPECTED_TRACKED_FILE_TOTAL, f"tracked textbook file total must be {EXPECTED_TRACKED_FILE_TOTAL}")
    return {
        "sources_db_sha256": db_sha256,
        "metadata_index_sha256": _hash(index_rows),
        "tracked_file_total": len(tracked_files),
        "section_total": len(sections),
        "section_tracked_file_total": len(grouped_sections),
        "section_metadata_sha256": _hash(section_records),
        "rows": index_rows,
    }


def validate_bindings(
    *,
    coverage_contract: Path,
    role_contract: Path,
    source_freeze_receipt: Path,
    school_units: Path,
    sources_db: Path,
) -> dict[str, Any]:
    """Validate the current contracts and full frozen textbook identity ledger."""
    coverage = _read_json(coverage_contract)
    roles = _read_json(role_contract)
    receipt = _read_json(source_freeze_receipt)
    _validate_schema(coverage, COVERAGE_SCHEMA, "coverage contract")
    _validate_schema(roles, ROLE_SCHEMA, "role contract")
    _validate_schema(receipt, SOURCE_FREEZE_SCHEMA, "source-universe freeze receipt")
    require(coverage.get("text_free") is True and receipt.get("text_free") is True, "text-free contract binding missing")
    functional = _functional_bindings(roles, role_contract_path=role_contract)
    families = coverage.get("mandatory_families")
    require(isinstance(families, list), "coverage contract lacks mandatory families")
    school = next((family for family in families if isinstance(family, Mapping) and family.get("family_id") == "school_textbooks"), None)
    require(isinstance(school, Mapping), "coverage contract lacks school_textbooks")
    scanner = school.get("scanner_nonhit_audit")
    require(isinstance(scanner, Mapping), "coverage contract lacks scanner non-hit audit")
    require(scanner.get("auditor_role_id") == AUDITOR_ROLE_ID, "wrong non-hit auditor role")
    require(scanner.get("seed_owner_role_id") == AUDITOR_ROLE_ID, "wrong non-hit seed owner")
    require(scanner.get("sample_formula") == "min(1000,nonhit_total)", "weakened non-hit sample formula")
    require(scanner.get("stratification") == ["tracked_file", "source_identity"], "wrong non-hit stratification")
    require(scanner.get("rubric_frozen_before_sampling") is True and scanner.get("zero_misses_required") is True, "weakened non-hit acceptance contract")
    source_school = _school_family(receipt)
    units, ledger_file_sha256 = _load_source_units(school_units)
    require(source_school["ledger_sha256"] == ledger_file_sha256, "school unit ledger does not match frozen receipt")
    metadata = _metadata_index(sources_db, units, receipt)
    return {
        "coverage_contract_sha256": sha256_file(coverage_contract),
        "source_freeze_receipt_sha256": sha256_file(source_freeze_receipt),
        "school_ledger_sha256": ledger_file_sha256,
        "frozen_unit_identity_sha256": _hash(units),
        "sources_db_sha256": metadata["sources_db_sha256"],
        "metadata_index_sha256": metadata["metadata_index_sha256"],
        "tracked_file_total": metadata["tracked_file_total"],
        "section_total": metadata["section_total"],
        "section_tracked_file_total": metadata["section_tracked_file_total"],
        "section_metadata_sha256": metadata["section_metadata_sha256"],
        **functional,
        "auditor_execution": functional["auditor_execution"],
        "metadata_rows": metadata["rows"],
        "units": units,
    }


def neutral_classifications(units: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return source-free neutral stubs without caller-controlled strata."""
    rows: list[dict[str, Any]] = []
    for unit in units:
        unit_id = unit.get("unit_id")
        require(isinstance(unit_id, str), "neutral stub lacks frozen unit identity")
        rows.append({
            "unit_id": unit_id,
            "unit_sha256": unit.get("unit_sha256"),
            "locator": unit.get("locator"),
            "candidate_classes": [],
        })
    return rows


def _validated_classifications(
    units: Sequence[Mapping[str, Any]], metadata_rows: Sequence[Mapping[str, Any]],
    classifications: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {str(unit["unit_id"]): unit for unit in units}
    require(len(classifications) == len(units), "classification rows must account for every frozen textbook unit")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in classifications:
        require(isinstance(source, Mapping), "invalid scanner classification row")
        require(set(source) == {"unit_id", "unit_sha256", "locator", "candidate_classes"}, "classification fields must be closed and source-free")
        unit_id = source.get("unit_id")
        require(isinstance(unit_id, str) and unit_id in by_id, "classification references a non-frozen textbook unit")
        require(unit_id not in seen, "duplicate scanner classification unit")
        seen.add(unit_id)
        expected = by_id[unit_id]
        require(source.get("unit_sha256") == expected["unit_sha256"], "classification unit hash differs from freeze")
        require(source.get("locator") == expected["locator"], "classification locator differs from freeze")
        classes = source.get("candidate_classes")
        require(isinstance(classes, list) and all(isinstance(item, str) for item in classes), "invalid candidate classes")
        require(set(classes) <= set(CANDIDATE_CLASSES), "unknown candidate class")
        require(len(classes) == len(set(classes)), "duplicate candidate class")
        rows.append({
            **expected,
            "candidate_classes": sorted(classes),
        })
    require(seen == set(by_id), "classification universe is incomplete")
    metadata = {str(row["unit_id"]): row for row in metadata_rows}
    require(set(metadata) == set(by_id), "metadata strata are not a frozen-unit bijection")
    return sorted(({
        **row,
        "tracked_file": metadata[str(row["unit_id"])]["tracked_file"],
        "source_identity": metadata[str(row["unit_id"])]["source_identity"],
        "metadata_sha256": metadata[str(row["unit_id"])]["metadata_sha256"],
    } for row in rows), key=lambda item: str(item["unit_id"]))


def _validate_rubric(rubric: Mapping[str, Any]) -> dict[str, Any]:
    required = {"rubric_id", "candidate_classes", "positive_fixture_ids", "negative_fixture_ids", "expected_decisions"}
    require(set(rubric) == required, "eligibility rubric fields must be closed and complete")
    require(isinstance(rubric["rubric_id"], str) and rubric["rubric_id"], "rubric lacks identity")
    require(rubric["candidate_classes"] == list(CANDIDATE_CLASSES), "rubric candidate classes changed")
    positive, negative = rubric["positive_fixture_ids"], rubric["negative_fixture_ids"]
    require(isinstance(positive, list) and isinstance(negative, list) and positive and negative, "rubric needs positive and negative fixtures")
    require(all(isinstance(item, str) and item for item in positive + negative), "invalid rubric fixture identity")
    require(len(set(positive)) == len(positive) and len(set(negative)) == len(negative) and not (set(positive) & set(negative)), "rubric fixture identities overlap")
    expected = rubric["expected_decisions"]
    require(isinstance(expected, Mapping) and set(expected) == set(positive + negative), "rubric expected decisions do not bind every fixture")
    require(all(expected[item] is True for item in positive) and all(expected[item] is False for item in negative), "rubric fixture decisions do not match polarity")
    return dict(rubric)


def _validate_review_receipt(
    receipt_path: Path,
    *,
    bindings: Mapping[str, Any],
    classification_sha256: str,
    rubric_sha256: str,
    scanner_sha256: str,
    scanner_input_sha256: str,
    rubric: Mapping[str, Any],
) -> dict[str, Any]:
    receipt = _read_json(receipt_path)
    required = {
        "schema_version", "text_free", "producer_task_id", "scanner", "metadata_index_sha256",
        "classification_universe_sha256", "rubric_sha256", "input_manifest_sha256",
        "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
        "functional_role_contract_sha256", "conflict_graph_sha256", "evaluation_cycle_id",
        "rubric_author_action_receipt", "scope_critic_action_receipt",
    }
    require(set(receipt) == required, "scanner input receipt fields must be closed")
    require(receipt.get("schema_version") == "phase3_textbook_scanner_inputs_v2_1", "wrong scanner input receipt schema")
    require(receipt.get("text_free") is True, "scanner input receipt is not text-free")
    require(receipt.get("producer_task_id") == SCANNER_IMPLEMENTATION_TASK_ID, "scanner producer task drift")
    scanner = receipt.get("scanner")
    require(scanner == {
        "implementation_version": SCANNER_IMPLEMENTATION_VERSION,
        "script_path": SCANNER_SCRIPT_PATH,
        "script_sha256": scanner_sha256,
    }, "review receipt scanner identity changed")
    require(receipt.get("metadata_index_sha256") == bindings["metadata_index_sha256"], "review receipt metadata index hash changed")
    require(receipt.get("classification_universe_sha256") == classification_sha256, "review receipt classification hash changed")
    require(receipt.get("rubric_sha256") == rubric_sha256, "review receipt rubric hash changed")
    require(receipt.get("input_manifest_sha256") == scanner_input_sha256, "scanner/rubric input manifest drift")
    author_input_sha256 = _hash({
        "producer_task_id": SCANNER_IMPLEMENTATION_TASK_ID,
        "scanner_sha256": scanner_sha256,
        "candidate_classes": list(CANDIDATE_CLASSES),
        "rubric_id": rubric["rubric_id"],
    })
    _validate_functional_action_receipt(
        receipt["rubric_author_action_receipt"], role_binding=bindings["rubric_author"],
        execution=bindings["rubric_author_execution"], bindings=bindings,
        action_kind="textbook_eligibility_rubric_fixture_freeze",
        input_manifest_sha256=author_input_sha256, output_sha256=rubric_sha256,
        label="rubric author",
    )
    critic_input_sha256 = _hash({
        "rubric_author_action_receipt_sha256": _hash(receipt["rubric_author_action_receipt"]),
        "rubric_sha256": rubric_sha256,
        "positive_fixture_ids": rubric["positive_fixture_ids"],
        "negative_fixture_ids": rubric["negative_fixture_ids"],
        "expected_decisions": rubric["expected_decisions"],
    })
    _validate_functional_action_receipt(
        receipt["scope_critic_action_receipt"], role_binding=bindings["scope_critic"],
        execution=bindings["scope_critic_execution"], bindings=bindings,
        action_kind="textbook_eligibility_rubric_zero_miss_review",
        input_manifest_sha256=critic_input_sha256,
        output_sha256=_hash({"rubric_sha256": rubric_sha256, "zero_miss": True}),
        label="scope critic",
    )
    require(
        all(receipt.get(name) == bindings[name] for name in (
            "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256", "evaluation_cycle_id",
        )),
        "scanner input functional-role binding drift",
    )
    return {"receipt": receipt, "receipt_sha256": sha256_file(receipt_path)}


def _validate_bundle_integrity(bundle: Mapping[str, Any]) -> None:
    """Check semantic identities that JSON Schema cannot express."""
    _validate_schema(bundle, BUNDLE_SCHEMA, "textbook non-hit bundle")
    population = bundle["population"]
    all_units = population["all_units"]
    candidates = population["candidate_units"]
    nonhits = population["nonhit_units"]
    require(len(all_units) == EXPECTED_UNIT_TOTAL, "bundle does not retain every frozen textbook unit")
    require(len({row["unit_id"] for row in all_units}) == EXPECTED_UNIT_TOTAL, "bundle has duplicate frozen textbook unit")
    require(all(row["candidate_classes"] for row in candidates), "candidate universe includes non-candidate")
    require(all(not row["candidate_classes"] for row in nonhits), "non-hit universe includes candidate")
    all_ids = {row["unit_id"] for row in all_units}
    candidate_ids = {row["unit_id"] for row in candidates}
    nonhit_ids = {row["unit_id"] for row in nonhits}
    require(candidate_ids.isdisjoint(nonhit_ids) and candidate_ids | nonhit_ids == all_ids, "candidate/non-hit universes are not a complete complement")
    require(population["candidate_total"] == len(candidates) and population["nonhit_total"] == len(nonhits), "population totals drifted")
    require(population["all_units_sha256"] == _hash(all_units), "all-unit population hash drifted")
    require(population["candidate_universe_sha256"] == _hash(candidates), "candidate universe hash drifted")
    require(population["nonhit_universe_sha256"] == _hash(nonhits), "non-hit universe hash drifted")
    require(bundle["scanner"]["classification_universe_sha256"] == population["all_units_sha256"], "scanner classification hash drifted")
    frozen_projection = [{key: row[key] for key in ("unit_id", "unit_sha256", "locator")} for row in all_units]
    require(bundle["source_bindings"]["frozen_unit_identity_sha256"] == _hash(frozen_projection), "frozen unit identity binding drifted")
    metadata_projection = [{key: row[key] for key in ("unit_id", "tracked_file", "source_identity", "metadata_sha256")} for row in all_units]
    require(bundle["source_bindings"]["metadata_index_sha256"] == _hash(metadata_projection), "metadata index binding drifted")
    require(len({row["tracked_file"] for row in all_units}) == EXPECTED_TRACKED_FILE_TOTAL, "tracked file population drifted")
    rubric = dict(bundle["rubric"])
    rubric_hash = rubric.pop("rubric_sha256")
    _validate_rubric(rubric)
    require(rubric_hash == _hash(rubric), "rubric hash drifted")
    receipt = bundle["scanner_review"]["receipt"]
    require(bundle["scanner_review"]["receipt_sha256"] == _hash(receipt), "embedded scanner input receipt hash drifted")
    require(receipt["text_free"] is True, "embedded scanner input receipt is not text-free")
    require(receipt["producer_task_id"] == SCANNER_IMPLEMENTATION_TASK_ID, "scanner input producer task drifted")
    require(receipt["classification_universe_sha256"] == population["all_units_sha256"], "scanner review receipt classification hash drifted")
    require(receipt["classification_universe_sha256"] == bundle["scanner"]["classification_universe_sha256"], "scanner review/scanner classification binding drifted")
    require(receipt["metadata_index_sha256"] == bundle["source_bindings"]["metadata_index_sha256"], "scanner review receipt metadata hash drifted")
    require(receipt["rubric_sha256"] == rubric_hash, "scanner review receipt rubric hash drifted")
    require(receipt["scanner"] == {
        "implementation_version": bundle["scanner"]["implementation_version"],
        "script_path": bundle["scanner"]["script_path"],
        "script_sha256": bundle["scanner"]["script_sha256"],
    }, "scanner input receipt implementation identity drifted")
    require(receipt["input_manifest_sha256"] == bundle["scanner"]["input_manifest_sha256"], "scanner input manifest binding drifted")
    require(receipt["classification_universe_sha256"] == bundle["scanner"]["classification_universe_sha256"], "scanner input classification binding drifted")
    expected_input_manifest = _hash({
        "producer_task_id": SCANNER_IMPLEMENTATION_TASK_ID,
        "scanner_sha256": bundle["scanner"]["script_sha256"],
        "metadata_index_sha256": bundle["source_bindings"]["metadata_index_sha256"],
        "classification_universe_sha256": bundle["scanner"]["classification_universe_sha256"],
        "rubric_sha256": rubric_hash,
    })
    require(bundle["scanner"]["input_manifest_sha256"] == expected_input_manifest, "scanner/rubric input manifest is stale")
    author_input_sha256 = _hash({
        "producer_task_id": SCANNER_IMPLEMENTATION_TASK_ID,
        "scanner_sha256": bundle["scanner"]["script_sha256"],
        "candidate_classes": list(CANDIDATE_CLASSES),
        "rubric_id": rubric["rubric_id"],
    })
    _validate_functional_action_receipt(
        receipt["rubric_author_action_receipt"], role_binding=bundle["scanner"]["rubric_author_role_binding"],
        execution=bundle["scanner"]["rubric_author_execution"], bindings=bundle["scanner"],
        action_kind="textbook_eligibility_rubric_fixture_freeze", input_manifest_sha256=author_input_sha256,
        output_sha256=rubric_hash, label="rubric author",
    )
    critic_input_sha256 = _hash({
        "rubric_author_action_receipt_sha256": _hash(receipt["rubric_author_action_receipt"]),
        "rubric_sha256": rubric_hash,
        "positive_fixture_ids": rubric["positive_fixture_ids"],
        "negative_fixture_ids": rubric["negative_fixture_ids"],
        "expected_decisions": rubric["expected_decisions"],
    })
    _validate_functional_action_receipt(
        receipt["scope_critic_action_receipt"], role_binding=bundle["scanner"]["scope_critic_role_binding"],
        execution=bundle["scanner"]["scope_critic_execution"], bindings=bundle["scanner"],
        action_kind="textbook_eligibility_rubric_zero_miss_review", input_manifest_sha256=critic_input_sha256,
        output_sha256=_hash({"rubric_sha256": rubric_hash, "zero_miss": True}), label="scope critic",
    )
    require(
        all(bundle["source_bindings"][name] == bundle["scanner"][name] == bundle["audit_contract"][name] == receipt[name] for name in (
            "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256", "evaluation_cycle_id",
        )),
        "functional-role binding drifted across scanner bundle",
    )
    require(bundle["audit_contract"]["auditor_role_binding"] == {
        "role_id": AUDITOR_ROLE_ID,
        "task_id": bundle["audit_contract"]["auditor_task_id"],
    }, "auditor role binding drifted")


def build_bundle(
    *,
    coverage_contract: Path,
    role_contract: Path,
    source_freeze_receipt: Path,
    school_units: Path,
    sources_db: Path,
    classifications: Sequence[Mapping[str, Any]],
    rubric: Mapping[str, Any],
    scanner_review_receipt: Path,
) -> dict[str, Any]:
    """Compile a complete, immutable text-free candidate/non-hit universe."""
    bindings = validate_bindings(
        coverage_contract=coverage_contract, role_contract=role_contract,
        source_freeze_receipt=source_freeze_receipt, school_units=school_units,
        sources_db=sources_db,
    )
    classified = _validated_classifications(bindings["units"], bindings["metadata_rows"], classifications)
    frozen_rubric = _validate_rubric(rubric)
    scanner_sha256 = sha256_file(ROOT / SCANNER_SCRIPT_PATH)
    classification_sha256 = _hash(classified)
    rubric_sha256 = _hash(frozen_rubric)
    scanner_input_sha256 = _hash({
        "producer_task_id": SCANNER_IMPLEMENTATION_TASK_ID,
        "scanner_sha256": scanner_sha256,
        "metadata_index_sha256": bindings["metadata_index_sha256"],
        "classification_universe_sha256": classification_sha256,
        "rubric_sha256": rubric_sha256,
    })
    review = _validate_review_receipt(
        scanner_review_receipt,
        bindings=bindings,
        classification_sha256=classification_sha256,
        rubric_sha256=rubric_sha256,
        scanner_sha256=scanner_sha256,
        scanner_input_sha256=scanner_input_sha256,
        rubric=frozen_rubric,
    )
    candidates = [row for row in classified if row["candidate_classes"]]
    nonhits = [row for row in classified if not row["candidate_classes"]]
    require(len(candidates) + len(nonhits) == EXPECTED_UNIT_TOTAL, "candidate/non-hit complement does not equal frozen denominator")
    bundle = {
        "schema_version": "phase3_textbook_nonhit_bundle_v1",
        "text_free": True,
        "source_bindings": {key: bindings[key] for key in (
            "coverage_contract_sha256", "source_freeze_receipt_sha256",
            "school_ledger_sha256", "frozen_unit_identity_sha256",
            "sources_db_sha256", "metadata_index_sha256", "tracked_file_total",
            "section_total", "section_tracked_file_total",
            "section_metadata_sha256",
            "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256", "evaluation_cycle_id",
        )},
        "scanner": {
            "implementation_version": SCANNER_IMPLEMENTATION_VERSION,
            "script_path": SCANNER_SCRIPT_PATH,
            "script_sha256": scanner_sha256,
            "producer_task_id": SCANNER_IMPLEMENTATION_TASK_ID,
            "candidate_classes": list(CANDIDATE_CLASSES),
            "classification_universe_sha256": classification_sha256,
            "input_manifest_sha256": scanner_input_sha256,
            "rubric_author_role_binding": bindings["rubric_author"],
            "rubric_author_execution": bindings["rubric_author_execution"],
            "scope_critic_role_binding": bindings["scope_critic"],
            "scope_critic_execution": bindings["scope_critic_execution"],
            **{name: bindings[name] for name in (
                "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
                "functional_role_contract_sha256", "conflict_graph_sha256", "evaluation_cycle_id",
            )},
        },
        "rubric": {**frozen_rubric, "rubric_sha256": rubric_sha256},
        "scanner_review": {
            "receipt": review["receipt"],
            "receipt_sha256": _hash(review["receipt"]),
            "receipt_file_sha256": review["receipt_sha256"],
        },
        "population": {
            "frozen_unit_total": EXPECTED_UNIT_TOTAL,
            "candidate_total": len(candidates),
            "nonhit_total": len(nonhits),
            "all_units_sha256": _hash(classified),
            "candidate_universe_sha256": _hash(candidates),
            "nonhit_universe_sha256": _hash(nonhits),
            "all_units": classified,
            "candidate_units": candidates,
            "nonhit_units": nonhits,
        },
        "audit_contract": {
            "auditor_role_binding": {
                "role_id": bindings["auditor_role_id"],
                "task_id": bindings["auditor_task_id"],
            },
            "auditor_task_id": bindings["auditor_task_id"],
            "auditor_execution": bindings["auditor_execution"],
            **{name: bindings[name] for name in (
                "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
                "functional_role_contract_sha256", "conflict_graph_sha256", "evaluation_cycle_id",
            )},
            "sample_formula": "min(1000,nonhit_total)",
            "sampler_version": SAMPLER_VERSION,
            "stratification": ["tracked_file", "source_identity"],
            "sampling_without_replacement": True,
            "entropy_contract": "approved_common_anti_grinding_v1",
            "arbitrary_seed_forbidden": True,
            "first_containing_origin_main_squash_merge_required": True,
            "unique_canonical_tuple_seed_required": True,
            "auditor_sole_attestor_committer": True,
            "seed_choice_reroll_reuse_forbidden": True,
            "passing_sample_reuse_forbidden": True,
            "zero_misses_required": True,
            "miss_invalidates_population_and_sample": True,
        },
    }
    _validate_bundle_integrity(bundle)
    return bundle


def hamilton_quotas(counts: Mapping[str, int], sample_n: int) -> dict[str, int]:
    """Allocate without replacement using proportional Hamilton largest remainder."""
    require(sample_n >= 0 and all(isinstance(value, int) and value > 0 for value in counts.values()), "invalid stratum counts")
    total = sum(counts.values())
    require(sample_n <= total, "sample exceeds stratum population")
    keys = sorted(counts)
    if sample_n == 0:
        return {key: 0 for key in keys}
    baseline = {key: 0 for key in keys}
    if sample_n >= len(keys):
        baseline = {key: 1 for key in keys}
    remaining_n = sample_n - sum(baseline.values())
    capacity = {key: counts[key] - baseline[key] for key in keys}
    capacity_total = sum(capacity.values())
    if remaining_n == 0:
        return baseline
    exact = {key: remaining_n * capacity[key] / capacity_total for key in keys}
    quotas = {key: baseline[key] + int(exact[key]) for key in keys}
    unassigned = sample_n - sum(quotas.values())
    for key in sorted(keys, key=lambda item: (-(exact[item] - int(exact[item])), item))[:unassigned]:
        quotas[key] += 1
    require(all(quotas[key] <= counts[key] for key in keys), "Hamilton allocation exceeds a stratum")
    return quotas


def _select(rows: Sequence[Mapping[str, Any]], count: int, seed: str, namespace: str) -> list[dict[str, Any]]:
    ranked = sorted(rows, key=lambda row: (
        _hash({"sampler_version": SAMPLER_VERSION, "seed": seed, "namespace": namespace, "unit_id": row["unit_id"]}),
        str(row["unit_id"]),
    ))
    return [dict(row) for row in ranked[:count]]


def _verify_approved_entropy(bundle: Mapping[str, Any], entropy_receipt: Mapping[str, Any]) -> dict[str, str]:
    """Delegate anti-grinding verification to the approved common helper only."""
    try:
        module = importlib.import_module(APPROVED_ENTROPY_MODULE)
    except ImportError as exc:
        raise TextbookNonhitError("approved common anti-grinding entropy helper is unavailable") from exc
    verifier = getattr(module, APPROVED_ENTROPY_VERIFIER, None)
    require(callable(verifier), "approved common anti-grinding entropy verifier is unavailable")
    try:
        result = verifier(
            entropy_receipt,
            purpose="textbook_nonhit",
            frozen_bundle_sha256=_hash(bundle),
            frozen_population_sha256=bundle["population"]["nonhit_universe_sha256"],
            auditor_role_id=AUDITOR_ROLE_ID,
            auditor_task_id=bundle["audit_contract"]["auditor_task_id"],
        )
    except Exception as exc:
        raise TextbookNonhitError("approved common anti-grinding entropy receipt is invalid") from exc
    require(isinstance(result, Mapping), "approved entropy verifier returned an invalid result")
    required = {"derived_seed", "entropy_receipt_sha256", "first_containing_merge_sha", "canonical_tuple_sha256"}
    require(set(result) == required, "approved entropy verifier result shape changed")
    require(all(isinstance(result[key], str) and result[key] for key in required), "approved entropy verifier returned empty identity")
    require(SHA256.fullmatch(str(result["entropy_receipt_sha256"])) is not None, "invalid entropy receipt hash")
    require(SHA256.fullmatch(str(result["canonical_tuple_sha256"])) is not None, "invalid entropy tuple hash")
    require(re.fullmatch(r"[a-f0-9]{40}", str(result["first_containing_merge_sha"])) is not None, "invalid entropy merge SHA")
    return {key: str(result[key]) for key in required}


def draw_audit_sample(bundle: Mapping[str, Any], *, entropy_receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Draw one deterministic sample only after approved entropy verification."""
    _validate_bundle_integrity(bundle)
    entropy = _verify_approved_entropy(bundle, entropy_receipt)
    seed = entropy["derived_seed"]
    nonhits = bundle["population"]["nonhit_units"]
    require(isinstance(nonhits, list), "bundle lacks non-hit universe")
    sample_n = min(1000, len(nonhits))
    by_file: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in nonhits:
        by_file[row["tracked_file"]].append(row)
    file_quotas = hamilton_quotas({key: len(value) for key, value in by_file.items()}, sample_n)
    selected: list[dict[str, Any]] = []
    source_quotas: dict[str, dict[str, int]] = {}
    for tracked_file in sorted(by_file):
        rows = by_file[tracked_file]
        by_source: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for row in rows:
            by_source[row["source_identity"]].append(row)
        local_quotas = hamilton_quotas({key: len(value) for key, value in by_source.items()}, file_quotas[tracked_file])
        source_quotas[tracked_file] = local_quotas
        for source_identity in sorted(by_source):
            selected.extend(_select(by_source[source_identity], local_quotas[source_identity], seed, f"{tracked_file}:{source_identity}"))
    require(len(selected) == sample_n and len({row["unit_id"] for row in selected}) == sample_n, "sample is not without replacement")
    selected.sort(key=lambda row: str(row["unit_id"]))
    return {
        "schema_version": "phase3_textbook_nonhit_audit_sample_v1",
        "text_free": True,
        "bundle_sha256": _hash(bundle),
        "nonhit_universe_sha256": bundle["population"]["nonhit_universe_sha256"],
        "auditor_role_binding": bundle["audit_contract"]["auditor_role_binding"],
        "auditor_task_id": bundle["audit_contract"]["auditor_task_id"],
        **{name: bundle["audit_contract"][name] for name in (
            "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256", "evaluation_cycle_id",
        )},
        "entropy_receipt_sha256": entropy["entropy_receipt_sha256"],
        "first_containing_merge_sha": entropy["first_containing_merge_sha"],
        "canonical_tuple_sha256": entropy["canonical_tuple_sha256"],
        "derived_seed_sha256": _hash({"derived_seed": seed}),
        "sampler_version": SAMPLER_VERSION,
        "sample_n": sample_n,
        "nonhit_total": len(nonhits),
        "shortfall_census": sample_n == len(nonhits) and len(nonhits) < 1000,
        "file_quotas": file_quotas,
        "source_quotas": source_quotas,
        "sample_units": selected,
        "sample_sha256": _hash(selected),
    }


def validate_audit_results(
    bundle: Mapping[str, Any],
    sample: Mapping[str, Any],
    *,
    entropy_receipt: Mapping[str, Any],
    decision_receipt_path: Path,
) -> dict[str, Any]:
    """Recompute the sample and validate one immutable auditor decision receipt."""
    _validate_bundle_integrity(bundle)
    recomputed = draw_audit_sample(bundle, entropy_receipt=entropy_receipt)
    require(sample == recomputed, "sample differs from deterministic bundle/entropy recomputation")
    decision_receipt = _read_json(decision_receipt_path)
    required = {
        "schema_version", "text_free", "auditor_role_binding", "bundle_sha256", "sample_sha256",
        "entropy_receipt_sha256", "decisions", "decisions_sha256", "action_receipt",
    }
    require(set(decision_receipt) == required, "audit decision receipt fields must be closed")
    require(decision_receipt.get("schema_version") == "phase3_textbook_nonhit_decision_receipt_v1", "wrong audit decision receipt schema")
    require(decision_receipt.get("text_free") is True, "audit decision receipt is not text-free")
    require(decision_receipt.get("auditor_role_binding") == bundle["audit_contract"]["auditor_role_binding"], "audit decision task binding is not the assigned auditor")
    require(decision_receipt.get("bundle_sha256") == _hash(bundle), "decision receipt bundle hash changed")
    require(decision_receipt.get("sample_sha256") == sample["sample_sha256"], "decision receipt sample hash changed")
    require(decision_receipt.get("entropy_receipt_sha256") == sample["entropy_receipt_sha256"], "decision receipt entropy hash changed")
    decisions = decision_receipt.get("decisions")
    require(isinstance(decisions, list), "decision receipt lacks decisions")
    require(decision_receipt.get("decisions_sha256") == _hash(decisions), "audit decision rows hash changed")
    sample_units = recomputed["sample_units"]
    require(len(decisions) == len(sample_units), "every sample unit requires one audit decision")
    sample_ids = {row["unit_id"] for row in sample_units}
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for row in decisions:
        require(isinstance(row, Mapping), "invalid audit decision")
        require(set(row) == {"unit_id", "decision"}, "audit decision fields must be closed and source-free")
        unit_id, decision = row.get("unit_id"), row.get("decision")
        require(isinstance(unit_id, str) and unit_id in sample_ids and unit_id not in seen, "audit decision does not bind exactly one sample unit")
        require(decision in AUDIT_DECISIONS, "unknown audit decision")
        seen.add(unit_id)
        normalized.append({"unit_id": unit_id, "decision": decision})
    require(seen == sample_ids, "audit decisions omit a sample unit")
    _validate_auditor_action_receipt(
        decision_receipt["action_receipt"], bindings=bundle["audit_contract"],
        input_manifest_sha256=_hash({
            "bundle_sha256": _hash(bundle), "sample_sha256": sample["sample_sha256"],
            "entropy_receipt_sha256": sample["entropy_receipt_sha256"],
        }),
        output_sha256=decision_receipt["decisions_sha256"],
    )
    misses = sorted(row["unit_id"] for row in normalized if row["decision"] != "agree")
    result = {
        "schema_version": "phase3_textbook_nonhit_audit_result_v1",
        "text_free": True,
        "bundle_sha256": _hash(bundle),
        "sample_sha256": recomputed["sample_sha256"],
        "entropy_receipt_sha256": recomputed["entropy_receipt_sha256"],
        "auditor_role_binding": bundle["audit_contract"]["auditor_role_binding"],
        "auditor_task_id": bundle["audit_contract"]["auditor_task_id"],
        **{name: bundle["audit_contract"][name] for name in (
            "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256", "evaluation_cycle_id",
        )},
        "decision_receipt_file_sha256": sha256_file(decision_receipt_path),
        "decisions_sha256": decision_receipt["decisions_sha256"],
        "decision_total": len(normalized),
        "miss_total": len(misses),
        "missed_unit_ids": misses,
        "status": "PASS_ZERO_MISSES" if not misses else "INVALID_SCANNER_POPULATION_AND_SAMPLE",
        "requires_new_scanner_hash_and_auditor_seed": bool(misses),
        "prior_sample_reuse_forbidden": True,
    }
    return {**result, "result_sha256": _hash(result)}


def write_bundle(bundle: Mapping[str, Any], output: Path) -> None:
    """Atomically write a schema-validated text-free bundle."""
    _validate_bundle_integrity(bundle)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=output.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(canonical_json(bundle) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, output)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-contract", type=Path, required=True)
    parser.add_argument("--role-contract", type=Path, required=True)
    parser.add_argument("--source-freeze-receipt", type=Path, required=True)
    parser.add_argument("--school-units", type=Path, required=True)
    parser.add_argument("--sources-db", type=Path, required=True)
    parser.add_argument("--classifications", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--scanner-review-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    bundle = build_bundle(
        coverage_contract=args.coverage_contract, role_contract=args.role_contract,
        source_freeze_receipt=args.source_freeze_receipt, school_units=args.school_units,
        sources_db=args.sources_db, classifications=_read_jsonl(args.classifications),
        rubric=_read_json(args.rubric), scanner_review_receipt=args.scanner_review_receipt,
    )
    write_bundle(bundle, args.output)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
