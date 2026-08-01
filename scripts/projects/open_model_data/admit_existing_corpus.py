"""Produce fail-closed, content-blind admission dispositions for an existing corpus.

The runner is deliberately not an exporter.  It reads source text only long
enough to count lexical words and test the frozen evaluation registry; its
manifest contains hashes and logical identifiers, never text or host paths.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import resource
import sqlite3
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data.inventory_existing_assets import WORD_RE
from scripts.projects.open_model_data.model_view_exporter import (
    build_exclusion_registry,
    registry_receipt,
)
from scripts.projects.open_model_data.validate_source_records import validate_path as validate_source_record_path

CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
CONFIG_SCHEMA = CONTRACTS / "corpus_admission_config_v1.schema.json"
EVIDENCE_SCHEMA = CONTRACTS / "corpus_admission_evidence_v1.schema.json"
RECEIPT_SCHEMA = CONTRACTS / "corpus_admission_receipt_v1.schema.json"
SOURCE_RECORD_SCHEMA = CONTRACTS / "source_record_v1.schema.json"


class AdmissionError(ValueError):
    """Raised when a corpus cannot be processed without weakening a gate."""


@dataclass(frozen=True)
class AdmissionRun:
    """The deterministic receipt and coverage outcome from one admission pass."""

    receipt: dict[str, Any]
    receipt_path: Path

    @property
    def complete(self) -> bool:
        return bool(self.receipt["coverage"]["complete"])


def canonical_json(value: Any) -> str:
    """Serialize stable UTF-8 JSON suitable for byte-for-byte receipts."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    """Hash an artifact without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _empty_artifact() -> dict[str, Any]:
    return {"bytes": 0, "records": 0, "sha256": hashlib.sha256(b"").hexdigest()}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdmissionError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AdmissionError(f"expected JSON object: {path}")
    return value


def _validator(path: Path) -> Draft202012Validator:
    schema = _read_json(path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _validate(value: Mapping[str, Any], validator: Draft202012Validator, label: str) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if errors:
        location = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise AdmissionError(f"{label} does not satisfy its schema at {location}: {errors[0].message}")


def _identifier(value: str) -> str:
    if not value.replace("_", "a").isalnum() or value[:1].isdigit():
        raise AdmissionError(f"unsafe SQLite identifier: {value!r}")
    return f'"{value}"'


def _connect_read_only(path: Path) -> sqlite3.Connection:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(path)
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _value(row: sqlite3.Row, name: str, specification: Mapping[str, Any]) -> str:
    value = specification.get("constant")
    if "column" in specification:
        value = row[f"attribute_{name}"]
    normalized = str(value or "").strip()
    return normalized if normalized else "unknown"


def _opaque_id(prefix: str, value: str) -> str:
    """Return a stable non-locator identifier for a source/work/record grouping."""
    return f"{prefix}.{hashlib.sha256(value.encode('utf-8')).hexdigest()[:24]}"


def _stage_json(path: Path, value: Mapping[str, Any]) -> Path:
    """Write and sync JSON beside its destination without publishing it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name, suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write((canonical_json(value) + "\n").encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    temporary = _stage_json(path, value)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _backup_path(output: Path) -> Path:
    with tempfile.NamedTemporaryFile(
        dir=output.parent,
        prefix=output.name,
        suffix=".rollback",
        delete=False,
    ) as handle:
        backup = Path(handle.name)
    backup.unlink()
    return backup


def _promote_staged_artifacts(artifacts: Sequence[tuple[Path, Path]]) -> None:
    """Promote a staged artifact set and restore prior outputs on failure."""
    outputs = [output.absolute() for _, output in artifacts]
    if len(set(outputs)) != len(outputs):
        raise AdmissionError("artifact outputs must be distinct")
    for temporary, output in artifacts:
        if not temporary.is_file():
            raise AdmissionError(f"staged artifact is missing: {temporary}")
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists() and not output.is_file():
            raise AdmissionError(f"artifact destination is not a file: {output}")

    backups: list[tuple[Path, Path]] = []
    promoted: list[Path] = []
    try:
        for temporary, output in artifacts:
            if output.exists():
                backup = _backup_path(output)
                os.replace(output, backup)
                backups.append((output, backup))
            os.replace(temporary, output)
            promoted.append(output)
    except Exception as exc:
        rollback_errors: list[str] = []
        for output in reversed(promoted):
            try:
                output.unlink(missing_ok=True)
            except OSError as rollback_exc:
                rollback_errors.append(f"remove {output}: {rollback_exc}")
        for output, backup in reversed(backups):
            try:
                if backup.exists():
                    os.replace(backup, output)
            except OSError as rollback_exc:
                rollback_errors.append(f"restore {output}: {rollback_exc}")
        for temporary, _ in artifacts:
            temporary.unlink(missing_ok=True)
        if rollback_errors:
            raise AdmissionError(
                "artifact promotion failed and rollback was incomplete: "
                + "; ".join(rollback_errors)
            ) from exc
        raise
    else:
        for _, backup in backups:
            backup.unlink(missing_ok=True)


@dataclass
class AtomicJsonl:
    """Write a local manifest atomically while retaining only a running hash."""

    output: Path
    handle: TextIO
    temporary: Path
    digest: Any
    records: int = 0
    bytes_written: int = 0

    @classmethod
    def open(cls, output: Path) -> AtomicJsonl:
        output.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(  # noqa: SIM115 - closed by finish/abort
            mode="w", encoding="utf-8", newline="", dir=output.parent,
            prefix=output.name, suffix=".tmp.jsonl", delete=False,
        )
        return cls(output, handle, Path(handle.name), hashlib.sha256())

    def write(self, value: Mapping[str, Any]) -> None:
        encoded = (canonical_json(value) + "\n").encode("utf-8")
        self.handle.write(encoded.decode("utf-8"))
        self.digest.update(encoded)
        self.records += 1
        self.bytes_written += len(encoded)

    def finish(self) -> dict[str, Any]:
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.handle.close()
        return {"bytes": self.bytes_written, "records": self.records, "sha256": self.digest.hexdigest()}

    def abort(self) -> None:
        if not self.handle.closed:
            self.handle.close()
        self.temporary.unlink(missing_ok=True)


def _profile_sources(profile: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    sources = profile.get("sources")
    if not isinstance(sources, list):
        raise AdmissionError("profile config lacks sources")
    result = {str(source.get("source_family")): source for source in sources if isinstance(source, dict)}
    if len(result) != len(sources):
        raise AdmissionError("profile config has duplicate or invalid source families")
    return result


def _evidence_sources(config: Mapping[str, Any], input_root: Path) -> dict[str, Mapping[str, Any]]:
    logical_path = config.get("evidence_packet")
    if logical_path is None:
        return {}
    packet = _read_json(input_root / str(logical_path))
    _validate(packet, _validator(EVIDENCE_SCHEMA), "admission evidence packet")
    sources = packet["sources"]
    result = {str(source["source_record_evidence_id"]): source for source in sources}
    if len(result) != len(sources):
        raise AdmissionError("admission evidence packet has duplicate source-record evidence IDs")
    for source in sources:
        evidence = source["evidence"]
        evidence_by_id = {str(item["evidence_id"]): item for item in evidence}
        if len(evidence_by_id) != len(evidence):
            raise AdmissionError("admission evidence packet has duplicate evidence IDs")
        rights = source["rights"]
        missing = set(rights["evidence_ids"]) - set(evidence_by_id)
        if missing or rights["license_terms_evidence_id"] not in evidence_by_id:
            raise AdmissionError(f"admission rights evidence references are incomplete: {sorted(missing)}")
        for cohort in source["acquisition"]["code_cohorts"]:
            item = evidence_by_id.get(cohort["evidence_id"])
            if item is None or item["sha256"] != cohort["sha256"] or item["receipt_url"] != cohort["url"]:
                raise AdmissionError(f"acquisition code receipt mismatch: {cohort['evidence_id']}")
        if sum(int(cohort["rows"]) for cohort in source["acquisition"]["code_cohorts"]) != source["snapshot"]["rows"]:
            raise AdmissionError("acquisition code cohorts do not reconcile to snapshot rows")
    return result


def _source_query(profile_source: Mapping[str, Any], family: Mapping[str, Any]) -> str:
    adapter = profile_source["adapter"]
    attributes = family["attributes"]
    selected = {
        "record_id": adapter["id_column"],
        "text": adapter["text_column"],
        "source_group": family["source_group_column"],
        "work_group": family["work_group_column"],
    }
    for name, specification in attributes.items():
        if "column" in specification:
            selected[f"attribute_{name}"] = specification["column"]
    source_record = family.get("source_record")
    if source_record is not None:
        for name in ("title", "url", "retrieved_at"):
            selected[f"source_record_{name}"] = source_record[f"{name}_column"]
    query_columns = [f"{_identifier(column)} AS {_identifier(alias)}" for alias, column in sorted(selected.items())]
    where = ""
    exclusion = adapter.get("exclude")
    if exclusion:
        values = exclusion["values"]
        literals = ", ".join("?" for _ in values)
        where = f" WHERE {_identifier(exclusion['column'])} NOT IN ({literals})"
    query = (
        f"SELECT {', '.join(query_columns)} FROM {_identifier(adapter['table'])}{where} "
        f"ORDER BY {_identifier(adapter['id_column'])} ASC"
    )
    return query


def _query_parameters(profile_source: Mapping[str, Any]) -> tuple[str, ...]:
    exclusion = profile_source["adapter"].get("exclude")
    return tuple(exclusion["values"]) if exclusion else ()


def _unresolved_reasons(evidence: Mapping[str, Any]) -> list[str]:
    required = ("provenance", "acquisition", "snapshot", "rights", "origin", "contamination")
    return [f"{name}_{evidence.get(name, 'missing')}" for name in required if evidence.get(name) != "complete"]


def _disposition(
    *, evidence: Mapping[str, Any], destination: str | None, contamination: str | None
) -> tuple[str, list[str]]:
    if contamination is not None:
        return "excluded", [f"evaluation_contamination_{contamination}"]
    reasons = _unresolved_reasons(evidence)
    if reasons:
        return "unresolved", reasons
    if destination is None:
        return "investigation_only", ["destination_not_declared"]
    # Human acceptance is intentionally outside this runner.  A complete
    # family can be proposed, but this program never emits training_eligible.
    return "proposed_admission", ["operator_acceptance_required"]


def _utc_timestamp(value: str) -> datetime.datetime:
    try:
        parsed = datetime.datetime.fromisoformat(value)
    except ValueError as exc:
        raise AdmissionError(f"invalid acquisition timestamp: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != datetime.timedelta(0):
        raise AdmissionError(f"acquisition timestamp is not UTC: {value!r}")
    return parsed


def _code_cohort(evidence_source: Mapping[str, Any], retrieved_at: str) -> Mapping[str, Any]:
    captured = _utc_timestamp(retrieved_at)
    matches = [
        cohort
        for cohort in evidence_source["acquisition"]["code_cohorts"]
        if _utc_timestamp(cohort["first_retrieved_at"]) <= captured <= _utc_timestamp(cohort["last_retrieved_at"])
    ]
    if len(matches) != 1:
        raise AdmissionError(f"capture timestamp maps to {len(matches)} acquisition-code cohorts: {retrieved_at}")
    return matches[0]


def _source_record(
    *,
    row: sqlite3.Row,
    raw_record_id: str,
    family: Mapping[str, Any],
    evidence_source: Mapping[str, Any],
    text: str,
    usage_role: str,
) -> dict[str, Any]:
    title = str(row["source_record_title"] or "").strip()
    url = str(row["source_record_url"] or "").strip()
    retrieved_at = str(row["source_record_retrieved_at"] or "").strip()
    if not title or not url or not retrieved_at:
        raise AdmissionError(f"source-record identity is incomplete for {family['source_family']}:{raw_record_id}")
    retrieved = _utc_timestamp(retrieved_at)
    content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    cohort = _code_cohort(evidence_source, retrieved_at)
    evidence_by_id = {item["evidence_id"]: item for item in evidence_source["evidence"]}
    evidence_ids = [*evidence_source["rights"]["evidence_ids"], cohort["evidence_id"]]
    evidence = [
        {
            "evidence_id": evidence_id,
            "citation": evidence_by_id[evidence_id]["citation"],
            "url": evidence_by_id[evidence_id]["receipt_url"],
            "retrieved_on": evidence_by_id[evidence_id]["retrieved_on"],
            "sha256": evidence_by_id[evidence_id]["sha256"],
        }
        for evidence_id in evidence_ids
    ]
    receipt_material = "\u001f".join((url, retrieved_at, content_sha256, cohort["commit"], cohort["sha256"]))
    rights = evidence_source["rights"]
    rights_statement = {
        "status": rights["status"],
        "jurisdiction": rights["jurisdiction"],
        "evidence_ids": list(rights["evidence_ids"]),
        "legal_conclusion": rights["legal_conclusion"],
        "license_expression": rights["license_expression"],
        "license_terms_evidence_id": rights["license_terms_evidence_id"],
    }
    bibliographic = evidence_source["bibliographic"]
    description = evidence_source["description"]
    return {
        "schema_version": "source_record_v1",
        "contract_schema_sha256": sha256_file(SOURCE_RECORD_SCHEMA),
        "record_id": _opaque_id(f"record.{family['source_family']}", raw_record_id),
        "work_id": _opaque_id(f"work.{family['source_family']}", title),
        "source_id": _opaque_id(f"source.{family['source_family']}", url),
        "acquisition": {
            "receipt_id": _opaque_id(f"receipt.{family['source_family']}", receipt_material),
            "source_or_catalog_url": url,
            "retrieved_on": retrieved.date().isoformat(),
        },
        "bibliographic": {
            "edition": f"{title}; article-level plaintext capture at {retrieved_at}",
            "editor": bibliographic["editor"],
            "publisher": bibliographic["publisher"],
            "translation_origin": bibliographic["translation_origin"],
        },
        "description": {
            "author": description["author"],
            "date": retrieved.date().isoformat(),
            "period": description["period"],
            "genre": description["genre"],
            "register": description["register"],
            "region": description["region"],
        },
        "content": {"sha256": content_sha256, "hash_scope": evidence_source["snapshot"]["content_hash_scope"]},
        "derivation": {"kind": "source", "parent_content_sha256": None, "transform_receipt_id": None},
        "rights": {name: dict(rights_statement) for name in ("copyright", "license", "redistribution", "model_training")},
        "evidence": evidence,
        "review": dict(evidence_source["review"]),
        "usage": {"role": usage_role, "contamination_exclusion_ids": ["eval.foundry_eval_exclusion_v1"]},
    }


def _empty_receipt(config: Mapping[str, Any], profile: Mapping[str, Any], inaccessible: list[dict[str, str]]) -> dict[str, Any]:
    profile_sources = _profile_sources(profile)
    configured_names = [str(family["source_family"]) for family in config["families"]]
    expected_rows = sum(int(profile_sources[name]["expected"]["rows"]) for name in configured_names)
    expected_words = sum(int(profile_sources[name]["expected"]["lexical_words"]) for name in configured_names)
    zero = {name: {"rows": 0, "lexical_words": 0} for name in ("excluded", "investigation_only", "proposed_admission", "unresolved")}
    return {
        "schema_version": "corpus_admission_receipt_v1", "admission_id": config["admission_id"],
        "coverage": {"complete": False, "expected_rows": expected_rows, "expected_lexical_words": expected_words,
                     "processed_rows": 0, "processed_lexical_words": 0, "inaccessible_families": inaccessible},
        "dispositions": zero, "families": [], "evaluation_exclusion": {"applied": False, "reason": "source_database_inaccessible"},
        "outputs": {"manifest": _empty_artifact(), "source_records": _empty_artifact()},
        "determinism": {"manifest_order": "source family, SQLite record id", "serialization": "UTF-8 canonical JSON with sorted keys and LF", "timestamps_omitted": True},
        "training_eligible_emitted": False,
    }


def admit_corpus(
    *,
    config_path: Path,
    input_root: Path,
    manifest_output: Path,
    receipt_output: Path,
    source_record_output: Path | None = None,
    runtime_output: Path | None = None,
) -> AdmissionRun:
    """Process every configured row, or emit an incomplete receipt without drops."""
    config = _read_json(config_path)
    _validate(config, _validator(CONFIG_SCHEMA), "admission config")
    profile = _read_json(input_root / config["profile_config"])
    profile_sources = _profile_sources(profile)
    evidence_sources = _evidence_sources(config, input_root)
    families = list(config["families"])
    family_names = [str(family["source_family"]) for family in families]
    if len(family_names) != len(set(family_names)):
        raise AdmissionError("admission config has duplicate source families")
    unknown = {family["source_family"] for family in families} - set(profile_sources)
    if unknown:
        raise AdmissionError(f"admission family absent from profile: {sorted(unknown)}")
    source_record_families = [family for family in families if family["source_record"] is not None]
    if source_record_families and source_record_output is None:
        raise AdmissionError("--source-record-output is required when source-record evidence is configured")
    for family in source_record_families:
        evidence_source_id = family["source_record"]["evidence_source_id"]
        evidence_source = evidence_sources.get(evidence_source_id)
        if evidence_source is None or evidence_source["source_family"] != family["source_family"]:
            raise AdmissionError(f"source-record evidence is missing or mismatched: {evidence_source_id}")
        if _unresolved_reasons(family["evidence"]) or family["proposed_destination"] is None:
            raise AdmissionError(f"source-record evidence configured for incomplete family: {family['source_family']}")

    inaccessible: list[dict[str, str]] = []
    for family in families:
        source = profile_sources[family["source_family"]]
        database = input_root / source["adapter"]["database"]
        try:
            with _connect_read_only(database) as connection:
                columns = {str(row[1]) for row in connection.execute(f"PRAGMA table_info({_identifier(source['adapter']['table'])})")}
                needed = {source["adapter"]["id_column"], source["adapter"]["text_column"], family["source_group_column"], family["work_group_column"]}
                needed.update(spec["column"] for spec in family["attributes"].values() if "column" in spec)
                if family["source_record"] is not None:
                    needed.update(family["source_record"][f"{name}_column"] for name in ("title", "url", "retrieved_at"))
                missing = sorted(needed - columns)
                if missing:
                    raise AdmissionError("missing columns: " + ", ".join(missing))
        except (FileNotFoundError, sqlite3.Error, AdmissionError) as exc:
            inaccessible.append({"source_family": family["source_family"], "reason": type(exc).__name__})
    if inaccessible:
        receipt = _empty_receipt(config, profile, sorted(inaccessible, key=lambda item: item["source_family"]))
        _validate(receipt, _validator(RECEIPT_SCHEMA), "incomplete admission receipt")
        empty_manifest = AtomicJsonl.open(manifest_output)
        empty_manifest.finish()
        empty_source_records = AtomicJsonl.open(source_record_output) if source_record_output is not None else None
        if empty_source_records is not None:
            empty_source_records.finish()
        receipt_temporary: Path | None = None
        try:
            receipt_temporary = _stage_json(receipt_output, receipt)
            staged = [(empty_manifest.temporary, manifest_output)]
            if empty_source_records is not None and source_record_output is not None:
                staged.append((empty_source_records.temporary, source_record_output))
            staged.append((receipt_temporary, receipt_output))
            _promote_staged_artifacts(staged)
        finally:
            empty_manifest.abort()
            if empty_source_records is not None:
                empty_source_records.abort()
            if receipt_temporary is not None:
                receipt_temporary.unlink(missing_ok=True)
        return AdmissionRun(receipt=receipt, receipt_path=receipt_output)

    started = time.monotonic()
    registry = build_exclusion_registry(
        v011_manifest=ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json",
        v02_packet=ROOT / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl",
    )
    disposition_counts: dict[str, Counter[str]] = {name: Counter() for name in ("excluded", "investigation_only", "proposed_admission", "unresolved")}
    family_results: list[dict[str, Any]] = []
    processed_rows = processed_words = 0
    seen_record_ids: set[str] = set()
    manifest = AtomicJsonl.open(manifest_output)
    source_records = AtomicJsonl.open(source_record_output) if source_record_output is not None else None
    source_record_validator = _validator(SOURCE_RECORD_SCHEMA)
    try:
        for family in families:
            source = profile_sources[family["source_family"]]
            database = input_root / source["adapter"]["database"]
            rows = words = 0
            by_disposition: dict[str, Counter[str]] = {name: Counter() for name in disposition_counts}
            source_record_rows = 0
            source_record_timestamps: set[str] = set()
            source_record_cohorts: Counter[str] = Counter()
            with _connect_read_only(database) as connection:
                cursor = connection.execute(_source_query(source, family), _query_parameters(source))
                for row in cursor:
                    raw_record_id = str(row["record_id"])
                    record_id = _opaque_id(f"record.{family['source_family']}", raw_record_id)
                    if record_id in seen_record_ids:
                        raise AdmissionError(f"duplicate record identity in manifest: {record_id}")
                    seen_record_ids.add(record_id)
                    text = str(row["text"] or "")
                    word_count = len(WORD_RE.findall(text))
                    match = registry.match(text)
                    disposition, reasons = _disposition(
                        evidence=family["evidence"], destination=family["proposed_destination"], contamination=match.method if match.matched else None,
                    )
                    attributes = {
                        name: _value(row, name, spec)
                        for name, spec in sorted(family["attributes"].items())
                    }
                    manifest_row = {
                        "attributes": attributes, "disposition": disposition,
                        "evidence_state": dict(sorted(family["evidence"].items())), "reasons": reasons,
                        "record_id": record_id, "source_family": family["source_family"],
                        "source_group_id": _opaque_id(f"source.{family['source_family']}", str(row["source_group"] or "unknown")),
                        "word_count": word_count, "work_group_id": _opaque_id(f"work.{family['source_family']}", str(row["work_group"] or "unknown")),
                    }
                    source_record_config = family["source_record"]
                    if source_record_config is not None:
                        evidence_source = evidence_sources[source_record_config["evidence_source_id"]]
                        source_record = _source_record(
                            row=row,
                            raw_record_id=raw_record_id,
                            family=family,
                            evidence_source=evidence_source,
                            text=text,
                            # The frozen source-record contract has no
                            # pending-operator role.  Keep every proposal
                            # mechanically excluded until the operator gate
                            # is recorded; a later accepted pass may emit
                            # training_candidate without changing this
                            # evidence packet.
                            usage_role="excluded",
                        )
                        _validate(source_record, source_record_validator, f"source record {record_id}")
                        assert source_records is not None
                        source_records.write(source_record)
                        manifest_row["source_record_id"] = source_record["record_id"]
                        retrieved_at = str(row["source_record_retrieved_at"])
                        source_record_rows += 1
                        source_record_timestamps.add(retrieved_at)
                        source_record_cohorts[_code_cohort(evidence_source, retrieved_at)["evidence_id"]] += 1
                    manifest.write(manifest_row)
                    rows += 1
                    words += word_count
                    processed_rows += 1
                    processed_words += word_count
                    disposition_counts[disposition]["rows"] += 1
                    disposition_counts[disposition]["lexical_words"] += word_count
                    by_disposition[disposition]["rows"] += 1
                    by_disposition[disposition]["lexical_words"] += word_count
            expected = source["expected"]
            family_result: dict[str, Any] = {
                "source_family": family["source_family"],
                "actual": {"rows": rows, "lexical_words": words},
                "expected": expected,
                "matches_expected": rows == expected["rows"] and words == expected["lexical_words"],
                "dispositions": {name: {"rows": by_disposition[name]["rows"], "lexical_words": by_disposition[name]["lexical_words"]} for name in sorted(by_disposition)},
            }
            if family["source_record"] is not None:
                evidence_source = evidence_sources[family["source_record"]["evidence_source_id"]]
                snapshot = evidence_source["snapshot"]
                expected_cohorts = {cohort["evidence_id"]: cohort["rows"] for cohort in evidence_source["acquisition"]["code_cohorts"]}
                source_evidence_matches = (
                    source_record_rows == snapshot["rows"] == rows
                    and snapshot["lexical_words"] == words
                    and len(source_record_timestamps) == snapshot["capture_timestamps"]
                    and min(source_record_timestamps) == snapshot["first_retrieved_at"]
                    and max(source_record_timestamps) == snapshot["last_retrieved_at"]
                    and dict(sorted(source_record_cohorts.items())) == dict(sorted(expected_cohorts.items()))
                )
                if not source_evidence_matches:
                    raise AdmissionError(f"source-record evidence arithmetic mismatch: {family['source_family']}")
                family_result["source_record_evidence"] = {
                    "records": source_record_rows,
                    "capture_timestamps": len(source_record_timestamps),
                    "first_retrieved_at": min(source_record_timestamps),
                    "last_retrieved_at": max(source_record_timestamps),
                    "code_cohorts": dict(sorted(source_record_cohorts.items())),
                    "matches_snapshot": True,
                }
            family_results.append(family_result)
        artifact = manifest.finish()
        source_record_artifact = source_records.finish() if source_records is not None else _empty_artifact()
        if source_records is not None:
            source_record_validation = validate_source_record_path(source_records.temporary)
            rejection_counts = source_record_validation["rejection_reason_counts"]
            if (
                source_record_validation["admitted_records"] != 0
                or source_record_validation["rejected_records"] != source_record_artifact["records"]
                or source_record_validation["input_sha256"] != source_record_artifact["sha256"]
                or rejection_counts != {"record_marked_excluded": source_record_artifact["records"]}
            ):
                raise AdmissionError("pending source-record manifest failed the frozen admission contract")
        expected_rows = sum(int(profile_sources[name]["expected"]["rows"]) for name in family_names)
        expected_words = sum(int(profile_sources[name]["expected"]["lexical_words"]) for name in family_names)
        complete = processed_rows == expected_rows and processed_words == expected_words and all(
            item["matches_expected"] for item in family_results
        )
        receipt = {
            "schema_version": "corpus_admission_receipt_v1", "admission_id": config["admission_id"],
            "coverage": {"complete": complete, "expected_rows": expected_rows, "expected_lexical_words": expected_words,
                         "processed_rows": processed_rows, "processed_lexical_words": processed_words, "inaccessible_families": []},
            "dispositions": {name: {"rows": disposition_counts[name]["rows"], "lexical_words": disposition_counts[name]["lexical_words"]} for name in sorted(disposition_counts)},
            "families": sorted(family_results, key=lambda item: item["source_family"]),
            "evaluation_exclusion": {"applied": True, **registry_receipt(registry)},
            "outputs": {"manifest": artifact, "source_records": source_record_artifact},
            "determinism": {"manifest_order": "configuration source-family order, SQLite record id", "source_record_order": "configuration source-family order, SQLite record id", "source_record_contract_sha256": sha256_file(SOURCE_RECORD_SCHEMA), "serialization": "UTF-8 canonical JSON with sorted keys and LF", "run_timestamps_omitted": True},
            "training_eligible_emitted": False,
        }
        # The receipt is the commit marker for downstream consumers.  Validate
        # it while both manifests still have temporary names so a receipt
        # contract failure cannot leave rights-bearing outputs behind.
        _validate(receipt, _validator(RECEIPT_SCHEMA), "admission receipt")
        receipt_temporary = _stage_json(receipt_output, receipt)
        staged = [(manifest.temporary, manifest_output)]
        if source_records is not None and source_record_output is not None:
            staged.append((source_records.temporary, source_record_output))
        # Publish the receipt last: it is the commit marker.  The promotion
        # helper restores any prior outputs if a later rename fails.
        staged.append((receipt_temporary, receipt_output))
        _promote_staged_artifacts(staged)
    except Exception:
        manifest.abort()
        if source_records is not None:
            source_records.abort()
        raise
    if runtime_output is not None:
        _atomic_json(
            runtime_output,
            {
                "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "peak_rss_unit": "platform_rusage_ru_maxrss",
                "schema_version": "corpus_admission_runtime_v1",
                "wall_seconds": round(time.monotonic() - started, 6),
            },
        )
    return AdmissionRun(receipt=receipt, receipt_path=receipt_output)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed admission pass for the existing Ukrainian corpus")
    parser.add_argument("--config", type=Path, default=ROOT / "data/projects/open_model_data/admission/public_external_full_corpus_admission_v1.json")
    parser.add_argument("--input-root", type=Path, default=ROOT)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--source-record-output", type=Path)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--runtime-output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = admit_corpus(config_path=args.config, input_root=args.input_root, manifest_output=args.manifest_output, receipt_output=args.receipt_output, source_record_output=args.source_record_output, runtime_output=args.runtime_output)
    except AdmissionError as exc:
        parser.error(str(exc))
    print(canonical_json(result.receipt))
    return 0 if result.complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
