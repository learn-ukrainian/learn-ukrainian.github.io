"""Restore source-bound provenance and selection metadata for eligible non-OCR input.

Issue #7883 (PROV-1..PROV-4): the Phase 1 source/work locator snapshot retained
stable identities and partial canonical URLs, but ingestion dropped many
database URLs and external records lack register/domain fields.  This tool
restores source/work/edition/acquisition links strictly from retained evidence
(the locator snapshot, ``sources.db``, and the existing-asset inventory
reconciliation records), binds the restored rows to the original snapshot
hash, classifies period/register/domain/original-language/translation status
with explicit unknowns, and validates the result without waiting for
extraction or export.  It never guesses titles or URLs, never reacquires
content, emits no corpus text, and reopens no existing human-source approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import tempfile
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import source_work_locator_index as locators

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "data/projects/open_model_data/contracts/v4_provenance_restoration_v1.schema.json"
DEFAULT_CONFIG = ROOT / "data/projects/open_model_data/evidence/v4_provenance_restoration_config_v1.json"
CLASSIFICATION_FIELDS = ("period", "register", "domain", "original_language", "translation_status")
ORDERING = "cohort_id,source_id,work_id,locator_id"


class RestorationError(ValueError):
    """The provenance restoration artifacts cannot be built or verified safely."""


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


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RestorationError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RestorationError(f"expected JSON object: {path}")
    return value


def _validator(definition: str) -> Draft202012Validator:
    schema = _read_json(CONTRACT)
    target: Mapping[str, Any] = {"$ref": f"#/$defs/{definition}", "$defs": schema["$defs"]}
    Draft202012Validator.check_schema(target)
    return Draft202012Validator(target)


def _record_validator() -> Draft202012Validator:
    return Draft202012Validator(_read_json(CONTRACT))


def _validate(value: Mapping[str, Any], validator: Draft202012Validator, label: str) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        where = ".".join(str(item) for item in error.path) or "<root>"
        raise RestorationError(f"{label} schema failure at {where}: {error.message}")


def _stage(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except OSError:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _replace(source: Path, target: Path) -> None:
    """Test seam for the sole atomic publication operation."""
    os.replace(source, target)


def _publish(path: Path, content: bytes) -> None:
    staged = _stage(path, content)
    try:
        _replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def _group_value(value: Any) -> str:
    """phase1-opaque-id-v1 group normalization, matching the locator builder."""
    return str(value or "unknown")


def _normalized(value: Any) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    return str(value).strip()


def _connect(path: Path) -> sqlite3.Connection:
    if not path.is_file() or path.stat().st_size == 0:
        raise RestorationError(f"missing SQLite input: {path}")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _load_config(config_path: Path) -> dict[str, Any]:
    config = _read_json(config_path)
    _validate(config, _validator("config"), "restoration config")
    return config


def _load_snapshot(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Strictly expand the retained locator snapshot and return rows + binding."""
    rows = locators.compact_rows(path)
    try:
        with path.open(encoding="utf-8") as handle:
            header = json.loads(handle.readline())
    except (OSError, json.JSONDecodeError) as exc:
        raise RestorationError(f"cannot read locator snapshot header {path}: {exc}") from exc
    binding = {
        "evidence": "data/projects/open_model_data/evidence/source_work_locator_index_v1.compact.jsonl",
        "semantic_jsonl_sha256": header["semantic_jsonl_sha256"],
        "records": header["records"],
    }
    if binding["records"] != len(rows):
        raise RestorationError("locator snapshot header record count disagrees with expanded rows")
    return rows, binding


def _load_ledger(path: Path) -> dict[str, dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RestorationError(f"cannot read inventory ledger {path}: {exc}") from exc
    records: dict[str, dict[str, Any]] = {}
    for line in lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RestorationError(f"invalid inventory ledger JSON: {exc}") from exc
        if not isinstance(record, dict) or not isinstance(record.get("asset_id"), str):
            raise RestorationError("inventory ledger record lacks an asset_id")
        if record["asset_id"] in records:
            raise RestorationError(f"duplicate inventory ledger asset: {record['asset_id']}")
        records[record["asset_id"]] = record
    return records


def _check_ocr_exclusion_evidence(config: Mapping[str, Any], ledger: Mapping[str, dict[str, Any]]) -> None:
    """Fail closed unless every retained OCR candidate remains un-ingested."""
    for asset_id in sorted(config["ocr_exclusion_evidence"]["inventory_asset_ids"]):
        record = ledger.get(asset_id)
        if record is None:
            raise RestorationError(f"missing OCR exclusion evidence record: {asset_id}")
        status = record.get("lineage", {}).get("ingestion_status")
        if status != "not_ingested":
            raise RestorationError(
                f"OCR exclusion evidence {asset_id} reports ingestion_status={status!r}; "
                "the non-OCR cohort claim no longer holds"
            )


def _check_private_sources_absent(config: Mapping[str, Any], rows: list[dict[str, Any]]) -> None:
    private = set(config["private_source_exclusions"]["sources"])
    leaked = sorted(
        {
            row["source_locator"].get("source_file")
            for row in rows
            if row["source_family"] == "public_textbooks"
            and row["source_locator"].get("source_file") in private
        }
    )
    if leaked:
        raise RestorationError(f"private teaching sources present in snapshot: {', '.join(leaked)}")


def _acquisition_plan(
    cohort: Mapping[str, Any], ledger: Mapping[str, dict[str, Any]]
) -> tuple[str, set[str]]:
    binding = cohort["acquisition"]
    asset_id = binding["inventory_asset_id"]
    record = ledger.get(asset_id)
    if record is None:
        raise RestorationError(f"missing inventory reconciliation record: {asset_id}")
    details = record.get("details")
    if not isinstance(details, dict):
        raise RestorationError(f"inventory reconciliation {asset_id} missing or non-dict details object")
    for key in binding["require_empty_diffs"]:
        if key not in details:
            raise RestorationError(
                f"inventory reconciliation {asset_id} details missing required diff key: {key}"
            )
        diff_val = details[key]
        if not isinstance(diff_val, list) or len(diff_val) != 0:
            raise RestorationError(
                f"inventory reconciliation {asset_id} has a non-empty or non-list {key} diff: {diff_val!r}; "
                "acquisition links cannot be restored from retained evidence"
            )
    unresolved_key = binding.get("unresolved_detail_key")
    if unresolved_key is not None:
        if unresolved_key not in details:
            raise RestorationError(
                f"inventory reconciliation {asset_id} details missing unresolved detail key: {unresolved_key}"
            )
        unresolved_val = details[unresolved_key]
        if not isinstance(unresolved_val, list):
            raise RestorationError(
                f"inventory reconciliation {asset_id} unresolved detail key {unresolved_key} is not a list: {unresolved_val!r}"
            )
        unresolved = set(unresolved_val)
    else:
        unresolved = set()
    return binding["ref_template"], unresolved



def _column_classification(
    connection: sqlite3.Connection,
    cohort: Mapping[str, Any],
    bindings: Mapping[str, Mapping[str, Any]],
    snapshot_groups: set[tuple[str, str]],
) -> dict[tuple[str, str], dict[str, str | None]]:
    """Read constant-per-group classification columns with exact group-set parity."""
    table = cohort["table"]
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table) is None:
        raise RestorationError(f"unsafe table identifier: {table!r}")
    actual = {str(row[1]) for row in connection.execute(f'PRAGMA table_info("{table}")')}
    needed = {cohort["source_column"], cohort["work_column"]}
    needed |= {binding["column"] for binding in bindings.values()}
    missing = sorted(needed - actual)
    if missing:
        raise RestorationError(f"missing classification columns for {cohort['cohort_id']}: {', '.join(missing)}")
    select = ", ".join(f'"{column}"' for column in sorted(needed))
    seen: dict[tuple[str, str], dict[str, set[str | None]]] = {}
    for raw in connection.execute(f'SELECT {select} FROM "{table}"'):
        key = (_group_value(raw[cohort["source_column"]]), _group_value(raw[cohort["work_column"]]))
        entry = seen.setdefault(key, {field: set() for field in bindings})
        for field, binding in bindings.items():
            entry[field].add(_normalized(raw[binding["column"]]))
    result: dict[tuple[str, str], dict[str, str | None]] = {}
    for key, fields in seen.items():
        resolved: dict[str, str | None] = {}
        for field, observed in fields.items():
            if len(observed) > 1:
                raise RestorationError(
                    f"conflicting {field} classification within {cohort['cohort_id']} group {key[0]!r}/{key[1]!r}"
                )
            resolved[field] = next(iter(observed))
        result[key] = resolved
    if set(result) != snapshot_groups:
        only_db = sorted(set(result) - snapshot_groups)
        only_snapshot = sorted(snapshot_groups - set(result))
        raise RestorationError(
            f"classification group drift for {cohort['cohort_id']}: "
            f"{len(only_db)} database-only, {len(only_snapshot)} snapshot-only groups"
        )
    return result


def _classify(
    cohort: Mapping[str, Any],
    row: Mapping[str, Any],
    column_values: Mapping[str, str | None] | None,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    classification: dict[str, dict[str, Any]] = {}
    unresolved: list[str] = []
    for field in CLASSIFICATION_FIELDS:
        binding = cohort["classification"][field]
        kind = binding["kind"]
        if kind == "unresolved":
            classification[field] = {"value": "unknown", "status": "unresolved", "source_ref": None}
            unresolved.append(field)
            continue
        if kind == "column":
            if column_values is None:
                raise RestorationError(f"missing database classification values for {cohort['cohort_id']}")
            value = column_values[field]
        else:
            value = _normalized(row["metadata"].get(binding["field"]))
        if value is None:
            classification[field] = {"value": "unknown", "status": "unresolved", "source_ref": binding["source_ref"]}
            unresolved.append(field)
            continue
        if value not in binding["vocabulary"]:
            raise RestorationError(
                f"{field} value {value!r} for {cohort['cohort_id']} is outside the configured vocabulary"
            )
        classification[field] = {"value": value, "status": "restored", "source_ref": binding["source_ref"]}
    return classification, unresolved


def _restoration_record(
    cohort: Mapping[str, Any],
    row: Mapping[str, Any],
    ref_template: str,
    acquisition_unresolved_sources: set[str],
    column_values: Mapping[str, str | None] | None,
) -> dict[str, Any]:
    source_file = row["source_locator"].get("source_file")
    unresolved: list[str] = []
    canonical_url = row["canonical_url"]
    if canonical_url is None:
        unresolved.append("canonical_source_url")
    stem = Path(str(source_file)).stem if source_file else None
    if stem is None or stem in acquisition_unresolved_sources:
        acquisition_ref = None
        unresolved.append("acquisition_raw_locator")
    else:
        acquisition_ref = ref_template.format(source_stem=stem)
    classification, classification_unresolved = _classify(cohort, row, column_values)
    unresolved.extend(classification_unresolved)
    record = {
        "schema_version": "v4_provenance_restoration_v1",
        "restoration_id": locators.opaque_id("restore", canonical_json([cohort["cohort_id"], row["locator_id"]])),
        "cohort_id": cohort["cohort_id"],
        "source_family": row["source_family"],
        "inventory_asset_id": cohort["inventory_asset_id"],
        "consumer_view": cohort["consumer_view"],
        "locator_id": row["locator_id"],
        "source_id": row["source_id"],
        "work_id": row["work_id"],
        "source_locator": dict(row["source_locator"]),
        "work_locator": dict(row["work_locator"]),
        "links": {
            "canonical_url": canonical_url,
            "acquisition_ref": acquisition_ref,
            "edition": dict(row["metadata"]),
        },
        "classification": classification,
        "affected_records": row["affected_records"],
        "unresolved": sorted(set(unresolved)),
    }
    return record


def _verify_identity(cohort: Mapping[str, Any], row: Mapping[str, Any]) -> tuple[str, str]:
    """Recompute phase1 opaque identities from snapshot locators; fail on drift."""
    source_value = _group_value(row["source_locator"].get("source_file"))
    work_column = cohort["work_column"]
    work_value = _group_value(row["work_locator"].get(work_column))
    family = row["source_family"]
    if locators.opaque_id(f"source.{family}", source_value) != row["source_id"]:
        raise RestorationError(f"source identity drift for locator {row['locator_id']}")
    if locators.opaque_id(f"work.{family}", work_value) != row["work_id"]:
        raise RestorationError(f"work identity drift for locator {row['locator_id']}")
    return source_value, work_value


def _index_content(records: list[dict[str, Any]], header: Mapping[str, Any]) -> bytes:
    rows_bytes = "".join(canonical_json(record) + "\n" for record in records).encode("utf-8")
    complete_header = dict(header)
    complete_header["rows_sha256"] = sha256_bytes(rows_bytes)
    _validate(complete_header, _validator("indexHeader"), "restoration index header")
    try:
        return (canonical_json(complete_header) + "\n").encode("utf-8") + rows_bytes
    except UnicodeEncodeError as exc:
        raise RestorationError("restoration index cannot be encoded as UTF-8") from exc


def _build_unresolved_report(
    records: list[dict[str, Any]],
    *,
    index_sha256: str,
    config_sha256: str,
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    by_cohort: dict[str, dict[str, Any]] = {}
    for cohort_id in sorted({record["cohort_id"] for record in records}):
        cohort_records = [record for record in records if record["cohort_id"] == cohort_id]
        counts: Counter[str] = Counter()
        for record in cohort_records:
            counts.update(record["unresolved"])
        by_cohort[cohort_id] = {
            "records": len(cohort_records),
            "unresolved_keys": dict(sorted(counts.items())),
        }
    return {
        "schema_version": "v4_provenance_unresolved_report_v1",
        "index_sha256": index_sha256,
        "config_sha256": config_sha256,
        "snapshot_semantic_jsonl_sha256": snapshot["semantic_jsonl_sha256"],
        "by_cohort": by_cohort,
        "human_source_approvals_reopened": False,
        "notes": [
            "Unresolved fields are explicit unknowns pending retained-evidence discovery; no title or URL was guessed and no content was reacquired.",
            "No existing human-source approval is reopened by this report; unresolved rights and approval states remain with their existing owners.",
        ],
    }


def _family_exclusion_rows(config: Mapping[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exclusions = []
    for entry in sorted(config["family_exclusions"], key=lambda item: item["source_family"]):
        family = entry["source_family"]
        exclusions.append(
            {
                "basis": entry["basis"],
                "scope": family,
                "rows": sum(1 for row in rows if row["source_family"] == family),
            }
        )
    return exclusions


def _select_eligible_rows(
    config: Mapping[str, Any], snapshot_rows: list[dict[str, Any]]
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Deterministically partition snapshot rows into eligible cohorts, summaries, and exclusions."""
    selected_by_cohort: dict[str, list[dict[str, Any]]] = {}
    cohort_summaries: list[dict[str, Any]] = []
    excluded_subjects: Counter[str] = Counter()
    subject_unresolved_rows = 0

    for cohort in config["cohorts"]:
        family_rows = [row for row in snapshot_rows if row["source_family"] == cohort["source_family"]]
        excluded = set(cohort.get("subject_exclusions", {}).get("subjects", ()))
        selected: list[dict[str, Any]] = []
        selected_records = 0
        for row in family_rows:
            _verify_identity(cohort, row)
            subject = _normalized(row["metadata"].get("subject"))
            if cohort["source_family"] == "public_textbooks":
                if subject is not None and subject in excluded:
                    excluded_subjects[subject] += 1
                    continue
                if subject is None:
                    subject_unresolved_rows += 1
                    continue
            selected.append(row)
            selected_records += row["affected_records"]
        selected_by_cohort[cohort["cohort_id"]] = selected
        cohort_summaries.append(
            {
                "cohort_id": cohort["cohort_id"],
                "source_family": cohort["source_family"],
                "consumer_view": cohort["consumer_view"],
                "selected_rows": len(selected),
                "selected_records": selected_records,
            }
        )

    exclusions = _family_exclusion_rows(config, snapshot_rows)
    if excluded_subjects:
        exclusions.append(
            {
                "basis": "stem_operator_exclusion_2026-09-10",
                "scope": "public_textbooks",
                "rows": sum(excluded_subjects.values()),
                "subjects": dict(sorted(excluded_subjects.items())),
            }
        )
    exclusions.append(
        {
            "basis": "public_textbook_subject_unresolved_fail_safe",
            "scope": "public_textbooks",
            "rows": subject_unresolved_rows,
        }
    )
    exclusions.append(
        {
            "basis": config["private_source_exclusions"]["basis"],
            "scope": "db.textbooks.private",
            "rows": 0,
            "sources": sorted(config["private_source_exclusions"]["sources"]),
        }
    )
    exclusions.append(
        {
            "basis": config["ocr_exclusion_evidence"]["basis"],
            "scope": "un-ingested retained OCR candidates",
            "rows": 0,
            "inventory_asset_ids": sorted(config["ocr_exclusion_evidence"]["inventory_asset_ids"]),
        }
    )
    return selected_by_cohort, cohort_summaries, exclusions


def build(*, config_path: Path, input_root: Path, output_root: Path | None = None) -> dict[str, Any]:
    """Build and atomically publish the restoration index, report, and receipt."""
    config = _load_config(config_path)
    config_sha256 = sha256_file(config_path)
    output_root = input_root if output_root is None else output_root
    snapshot_rows, snapshot = _load_snapshot(input_root / config["inputs"]["locator_index"])
    ledger = _load_ledger(input_root / config["inputs"]["inventory_ledger"])
    _check_ocr_exclusion_evidence(config, ledger)
    _check_private_sources_absent(config, snapshot_rows)

    record_validator = _record_validator()
    records: list[dict[str, Any]] = []
    tables_read: set[str] = set()

    selected_by_cohort, cohort_summaries, exclusions = _select_eligible_rows(config, snapshot_rows)

    database_path = input_root / config["inputs"]["database"]
    connection: sqlite3.Connection | None = None
    column_evidence: dict[str, dict[str, str | None]] = {}
    try:
        for cohort in config["cohorts"]:
            cohort_id = cohort["cohort_id"]
            family_selected = selected_by_cohort[cohort_id]
            column_bindings = {
                field: cohort["classification"][field]
                for field in CLASSIFICATION_FIELDS
                if cohort["classification"][field]["kind"] == "column"
            }
            classification_by_group: dict[tuple[str, str], dict[str, str | None]] = {}
            if column_bindings:
                if connection is None:
                    connection = _connect(database_path)
                tables_read.add(cohort["table"])
                snapshot_groups = {
                    _verify_identity(cohort, row)
                    for row in snapshot_rows
                    if row["source_family"] == cohort["source_family"]
                }
                classification_by_group = _column_classification(
                    connection, cohort, column_bindings, snapshot_groups
                )
                for group_key, values in sorted(classification_by_group.items()):
                    group_id = f"{cohort_id}:{group_key[0]}#{group_key[1]}"
                    column_evidence[group_id] = values
            ref_template, acquisition_unresolved = _acquisition_plan(cohort, ledger)
            for row in family_selected:
                key = (
                    _group_value(row["source_locator"].get("source_file")),
                    _group_value(row["work_locator"].get(cohort["work_column"])),
                )
                record = _restoration_record(
                    cohort,
                    row,
                    ref_template,
                    acquisition_unresolved,
                    classification_by_group.get(key) if column_bindings else None,
                )
                _validate(record, record_validator, f"restoration record {record['restoration_id']}")
                records.append(record)
    finally:
        if connection is not None:
            connection.close()

    records.sort(key=lambda record: (record["cohort_id"], record["source_id"], record["work_id"], record["locator_id"]))
    header = {
        "schema_version": "v4_provenance_restoration_index_v1",
        "row_schema_version": "v4_provenance_restoration_v1",
        "snapshot": snapshot,
        "config_sha256": config_sha256,
        "records": len(records),
        "ordering": ORDERING,
    }
    index_content = _index_content(records, header)
    index_path = output_root / config["outputs"]["index"]
    _publish(index_path, index_content)
    index_sha256 = sha256_bytes(index_content)

    report = _build_unresolved_report(
        records, index_sha256=index_sha256, config_sha256=config_sha256, snapshot=snapshot
    )
    _validate(report, _validator("unresolvedReport"), "unresolved report")
    report_content = (canonical_json(report) + "\n").encode("utf-8")
    report_path = output_root / config["outputs"]["unresolved_report"]
    _publish(report_path, report_content)

    receipt = {
        "schema_version": "v4_provenance_restoration_receipt_v1",
        "config_sha256": config_sha256,
        "inputs": {
            "locator_index": {
                "path": config["inputs"]["locator_index"],
                "sha256": sha256_file(input_root / config["inputs"]["locator_index"]),
            },
            "inventory_ledger": {
                "path": config["inputs"]["inventory_ledger"],
                "sha256": sha256_file(input_root / config["inputs"]["inventory_ledger"]),
            },
            "database": {
                "path": config["inputs"]["database"],
                "access": "read_only",
                "tables": sorted(tables_read),
                "column_evidence": column_evidence,
            },
        },
        "selection": {
            "operator_decision_date": config["operator_decision"]["date"],
            "cohorts": cohort_summaries,
            "exclusions": exclusions,
        },
        "outputs": {
            "index": {
                "path": config["outputs"]["index"],
                "sha256": index_sha256,
                "records": len(records),
            },
            "unresolved_report": {
                "path": config["outputs"]["unresolved_report"],
                "sha256": sha256_bytes(report_content),
                "records": len(report["by_cohort"]),
            },
        },
        "human_source_approvals_reopened": False,
        "limitations": [
            "Restoration binds metadata only; no corpus text is read, emitted, or transformed.",
            "Unresolved period/register/domain/original-language/translation fields remain explicit unknowns pending retained-evidence discovery.",
            "End-to-end provenance propagation through extraction and export is verified separately under #7430 PILOT-1/PILOT-4.",
        ],
    }
    _validate(receipt, _validator("receipt"), "restoration receipt")
    receipt_content = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    receipt_path = output_root / config["outputs"]["receipt"]
    _publish(receipt_path, receipt_content)
    return {
        "records": len(records),
        "cohorts": cohort_summaries,
        "index_sha256": index_sha256,
        "unresolved_report_sha256": sha256_bytes(report_content),
        "receipt_sha256": sha256_bytes(receipt_content),
    }


def _read_index(path: Path, record_validator: Draft202012Validator) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        with path.open(encoding="utf-8") as handle:
            first = handle.readline()
            if not first.endswith("\n") or not first.strip():
                raise RestorationError("restoration index has a missing or unterminated header")
            header = json.loads(first)
            if not isinstance(header, dict):
                raise RestorationError("restoration index header is not an object")
            _validate(header, _validator("indexHeader"), "restoration index header")
            rows_bytes = b""
            records: list[dict[str, Any]] = []
            for line_number, line in enumerate(handle, start=2):
                if not line.endswith("\n") or not line.strip():
                    raise RestorationError(f"restoration index has a blank or unterminated row at {line_number}")
                rows_bytes += line.encode("utf-8")
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise RestorationError(f"restoration index row {line_number} is not an object")
                _validate(record, record_validator, f"restoration index row {line_number}")
                records.append(record)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RestorationError(f"cannot read restoration index {path}: {exc}") from exc
    if len(records) != header["records"]:
        raise RestorationError("restoration index record count disagrees with header")
    if sha256_bytes(rows_bytes) != header["rows_sha256"]:
        raise RestorationError("restoration index rows hash disagrees with header")
    ordered = sorted(
        records, key=lambda record: (record["cohort_id"], record["source_id"], record["work_id"], record["locator_id"])
    )
    if records != ordered:
        raise RestorationError("restoration index rows are reordered")
    return header, records


def verify(*, config_path: Path, input_root: Path, output_root: Path | None = None) -> dict[str, Any]:
    """Validate committed restoration artifacts against snapshot, ledger, and retained evidence."""
    config = _load_config(config_path)
    config_sha256 = sha256_file(config_path)
    output_root = input_root if output_root is None else output_root
    snapshot_rows, snapshot = _load_snapshot(input_root / config["inputs"]["locator_index"])
    snapshot_by_locator = {row["locator_id"]: row for row in snapshot_rows}
    if len(snapshot_by_locator) != len(snapshot_rows):
        raise RestorationError("duplicate locator_id in retained locator snapshot")

    ledger = _load_ledger(input_root / config["inputs"]["inventory_ledger"])
    _check_ocr_exclusion_evidence(config, ledger)
    _check_private_sources_absent(config, snapshot_rows)

    selected_by_cohort, expected_cohorts, expected_exclusions = _select_eligible_rows(config, snapshot_rows)
    expected_locators = {row["locator_id"] for rows in selected_by_cohort.values() for row in rows}
    cohort_by_id = {cohort["cohort_id"]: cohort for cohort in config["cohorts"]}

    index_path = output_root / config["outputs"]["index"]
    index_sha256 = sha256_file(index_path)
    header, records = _read_index(index_path, _record_validator())
    if header["snapshot"] != snapshot:
        raise RestorationError("restoration index snapshot binding disagrees with the retained locator snapshot")
    if header["config_sha256"] != config_sha256:
        raise RestorationError("restoration index config hash disagrees with the config file")
    if header["records"] != len(expected_locators):
        raise RestorationError(
            f"restoration index header record count {header['records']} disagrees with expected selection {len(expected_locators)}"
        )

    observed_locators: set[str] = set()
    for record in records:
        lid = record["locator_id"]
        if lid in observed_locators:
            raise RestorationError(f"duplicate locator_id {lid} in restoration index")
        observed_locators.add(lid)
    if observed_locators != expected_locators:
        missing = sorted(expected_locators - observed_locators)
        extra = sorted(observed_locators - expected_locators)
        raise RestorationError(
            f"restoration index does not match complete eligible selection: "
            f"{len(missing)} missing, {len(extra)} extra locators"
        )

    acquisition_plans = {
        cohort["cohort_id"]: _acquisition_plan(cohort, ledger)
        for cohort in config["cohorts"]
    }

    report_path = output_root / config["outputs"]["unresolved_report"]
    report = _read_json(report_path)
    _validate(report, _validator("unresolvedReport"), "unresolved report")
    if report["index_sha256"] != index_sha256:
        raise RestorationError("unresolved report does not reference the committed index")
    if report["config_sha256"] != config_sha256:
        raise RestorationError("unresolved report config hash disagrees with the config file")
    if report["snapshot_semantic_jsonl_sha256"] != snapshot["semantic_jsonl_sha256"]:
        raise RestorationError("unresolved report snapshot binding disagrees with the locator snapshot")
    recomputed_report = _build_unresolved_report(
        records, index_sha256=index_sha256, config_sha256=config_sha256, snapshot=snapshot
    )
    if report["by_cohort"] != recomputed_report["by_cohort"]:
        raise RestorationError("unresolved report cohort accounting disagrees with the index rows")

    receipt_path = output_root / config["outputs"]["receipt"]
    receipt = _read_json(receipt_path)
    _validate(receipt, _validator("receipt"), "restoration receipt")
    if receipt["config_sha256"] != config_sha256:
        raise RestorationError("receipt config hash disagrees with the config file")
    if receipt["inputs"]["locator_index"]["sha256"] != sha256_file(input_root / config["inputs"]["locator_index"]):
        raise RestorationError("receipt locator index hash disagrees with the retained snapshot file")
    if receipt["inputs"]["inventory_ledger"]["sha256"] != sha256_file(
        input_root / config["inputs"]["inventory_ledger"]
    ):
        raise RestorationError("receipt inventory ledger hash disagrees with the retained ledger file")
    if receipt["outputs"]["index"]["sha256"] != index_sha256:
        raise RestorationError("receipt index hash disagrees with the committed index")
    if receipt["outputs"]["unresolved_report"]["sha256"] != sha256_file(report_path):
        raise RestorationError("receipt unresolved-report hash disagrees with the committed report")
    if receipt["outputs"]["index"]["records"] != header["records"]:
        raise RestorationError("receipt record count disagrees with the committed index")

    if receipt["selection"]["cohorts"] != expected_cohorts:
        raise RestorationError("receipt cohort accounting disagrees with reconstructed selection")
    if receipt["selection"]["exclusions"] != expected_exclusions:
        raise RestorationError("receipt exclusion accounting disagrees with reconstructed selection")

    receipt_db = receipt["inputs"]["database"]
    column_evidence = receipt_db.get("column_evidence")
    if not isinstance(column_evidence, dict):
        raise RestorationError("receipt database input missing or non-dict column_evidence")
    database_path = input_root / config["inputs"]["database"]
    if database_path.is_file():
        connection = _connect(database_path)
        try:
            for cohort in config["cohorts"]:
                column_bindings = {
                    field: cohort["classification"][field]
                    for field in CLASSIFICATION_FIELDS
                    if cohort["classification"][field]["kind"] == "column"
                }
                if column_bindings:
                    family_rows = [row for row in snapshot_rows if row["source_family"] == cohort["source_family"]]
                    snapshot_groups = {_verify_identity(cohort, row) for row in family_rows}
                    live_db = _column_classification(connection, cohort, column_bindings, snapshot_groups)
                    for group_key, values in live_db.items():
                        group_id = f"{cohort['cohort_id']}:{group_key[0]}#{group_key[1]}"
                        if group_id not in column_evidence or column_evidence[group_id] != values:
                            raise RestorationError(
                                f"receipt column evidence diverges from database for {group_id}"
                            )
        finally:
            connection.close()

    for record in records:
        source = snapshot_by_locator[record["locator_id"]]
        cohort_id = record["cohort_id"]
        if cohort_id not in cohort_by_id:
            raise RestorationError(f"restored record {record['restoration_id']} has unknown cohort {cohort_id}")
        cohort = cohort_by_id[cohort_id]

        for key in ("source_id", "work_id", "source_family", "source_locator", "work_locator"):
            if record[key] != source[key]:
                raise RestorationError(f"restored record {record['restoration_id']} diverges from snapshot field {key}")
        if record["affected_records"] != source["affected_records"]:
            raise RestorationError(
                f"restored record {record['restoration_id']} affected_records diverges from snapshot"
            )

        if record["links"]["canonical_url"] != source["canonical_url"]:
            raise RestorationError(
                f"restored record {record['restoration_id']} canonical_url diverges from snapshot"
            )

        if record["links"]["edition"] != dict(source["metadata"]):
            raise RestorationError(
                f"restored record {record['restoration_id']} edition metadata diverges from snapshot metadata"
            )

        ref_template, acq_unresolved = acquisition_plans[cohort_id]
        source_file = record["source_locator"].get("source_file")
        stem = Path(str(source_file)).stem if source_file else None
        if stem is None or stem in acq_unresolved:
            expected_acq_ref = None
            expected_acq_unresolved = True
        else:
            expected_acq_ref = ref_template.format(source_stem=stem)
            expected_acq_unresolved = False
        if record["links"]["acquisition_ref"] != expected_acq_ref:
            raise RestorationError(
                f"restored record {record['restoration_id']} acquisition_ref diverges from ledger reconciliation: "
                f"expected {expected_acq_ref!r}, got {record['links']['acquisition_ref']!r}"
            )

        expected_unresolved: list[str] = []
        if source["canonical_url"] is None:
            expected_unresolved.append("canonical_source_url")
        if expected_acq_unresolved:
            expected_unresolved.append("acquisition_raw_locator")

        classification = record["classification"]
        for field in CLASSIFICATION_FIELDS:
            binding = cohort["classification"][field]
            entry = classification.get(field)
            if entry is None or not isinstance(entry, dict):
                raise RestorationError(f"restored record {record['restoration_id']} missing classification for {field}")
            kind = binding["kind"]
            if kind == "unresolved":
                if entry["status"] != "unresolved" or entry["value"] != "unknown" or entry["source_ref"] is not None:
                    raise RestorationError(
                        f"restored record {record['restoration_id']} field {field} invalid unresolved classification: {entry!r}"
                    )
                expected_unresolved.append(field)
            elif kind == "snapshot_metadata":
                raw_val = _normalized(source["metadata"].get(binding["field"]))
                if raw_val is None:
                    if entry["status"] != "unresolved" or entry["value"] != "unknown" or entry["source_ref"] != binding["source_ref"]:
                        raise RestorationError(
                            f"restored record {record['restoration_id']} field {field} invalid missing metadata classification: {entry!r}"
                        )
                    expected_unresolved.append(field)
                else:
                    if raw_val not in binding["vocabulary"]:
                        raise RestorationError(
                            f"restored record {record['restoration_id']} field {field} value {raw_val!r} outside vocabulary"
                        )
                    if entry["status"] != "restored" or entry["value"] != raw_val or entry["source_ref"] != binding["source_ref"]:
                        raise RestorationError(
                            f"restored record {record['restoration_id']} field {field} invalid restored metadata classification: {entry!r}"
                        )
            elif kind == "column":
                group_key = (
                    _group_value(source["source_locator"].get("source_file")),
                    _group_value(source["work_locator"].get(cohort["work_column"])),
                )
                group_id = f"{cohort_id}:{group_key[0]}#{group_key[1]}"
                if group_id not in column_evidence:
                    raise RestorationError(
                        f"restored record {record['restoration_id']} group {group_id} missing from column evidence"
                    )
                expected_val = column_evidence[group_id].get(field)
                if expected_val is None:
                    if entry["status"] != "unresolved" or entry["value"] != "unknown" or entry["source_ref"] != binding["source_ref"]:
                        raise RestorationError(
                            f"restored record {record['restoration_id']} field {field} invalid missing column classification: {entry!r}"
                        )
                    expected_unresolved.append(field)
                else:
                    if expected_val not in binding["vocabulary"]:
                        raise RestorationError(
                            f"restored record {record['restoration_id']} field {field} value {expected_val!r} outside vocabulary"
                        )
                    if entry["status"] != "restored" or entry["value"] != expected_val or entry["source_ref"] != binding["source_ref"]:
                        raise RestorationError(
                            f"restored record {record['restoration_id']} field {field} invalid restored column classification: {entry!r}"
                        )
            else:
                raise RestorationError(f"unsupported classification kind {kind!r}")

        if record["unresolved"] != sorted(set(expected_unresolved)):
            raise RestorationError(
                f"restored record {record['restoration_id']} unresolved keys diverge: "
                f"expected {sorted(set(expected_unresolved))}, got {record['unresolved']}"
            )

    return {
        "records": header["records"],
        "index_sha256": index_sha256,
        "snapshot_semantic_jsonl_sha256": snapshot["semantic_jsonl_sha256"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        command = subcommands.add_parser(name)
        command.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
        command.add_argument("--input-root", type=Path, default=ROOT)
        command.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = build(config_path=args.config, input_root=args.input_root, output_root=args.output_root)
        else:
            result = verify(config_path=args.config, input_root=args.input_root, output_root=args.output_root)
    except (RestorationError, locators.LocatorError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
