#!/usr/bin/env python3
"""Project exact historical document dates through attributed frameworks.

The output is a private, metadata-only document manifest.  A calendar year is
chronological context, not proof that every form in a document belongs to a
linguistic stage.  The adapter therefore preserves every frozen Ukrainian
scholarly framework, creates no canonical winner or semantic gold, and leaves
documents without an exact source-metadata year unresolved.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.projects.open_model_data import phase3_historical_materialization as materialization
from scripts.projects.open_model_data import phase3_historical_periodization as periodization

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
RECORD_SCHEMA_PATH = DATA / "contracts/phase3_historical_document_chronology_record_v1.schema.json"
RECEIPT_SCHEMA_PATH = DATA / "contracts/phase3_historical_document_chronology_receipt_v1.schema.json"
PERIODIZATION_FREEZE_PATH = DATA / "admission/phase3_historical_periodization_freeze_v1.json"

RECORD_SCHEMA_VERSION = "phase3_historical_document_chronology_record_v1"
RECEIPT_SCHEMA_VERSION = "phase3_historical_document_chronology_receipt_v1"
OUTPUT_FILENAME = "historical-document-chronology-v1.jsonl.gz"
RECEIPT_FILENAME = "historical-document-chronology-receipt-v1.json"

EXPECTED_PERIODIZATION_FREEZE_SHA256 = periodization.EXPECTED_FREEZE_SHA256
EXPECTED_PERIODIZATION_IMPLEMENTATION_SHA256 = "cc311db5db46da73a6c5008186a5ea3acc4930baa96e21f3f16d1f4051d104ac"
EXPECTED_MATERIALIZATION_IMPLEMENTATION_SHA256 = "97e7cd63da36dacb7c88db0ec8225ea4075c3a5873ecd618e6d8b5ca4188536e"
EXPECTED_FULL_RECEIPT_FILE_SHA256 = "05322d450a8e90b103fff7521605395250e1da957fbf63e8ecf1df8d3d5f6307"
EXPECTED_FULL_RECEIPT_SHA256 = "8e3d33b4c5d5a5a4bd3c5da7788460d016e16b9058515b64a6683a725a14c2de"
EXPECTED_UD_DATE_DENOMINATOR = {
    "eligible_documents": 82,
    "exact_date_documents": 4,
    "unresolved_date_documents": 78,
    "min_exact_year": 1413,
    "max_exact_year": 1473,
}
EXPECTED_PLUG2_DATE_DENOMINATOR = {
    "eligible_documents": 56080,
    "exact_date_documents": 56080,
    "unresolved_date_documents": 0,
    "min_exact_year": 1816,
    "max_exact_year": 1954,
}
EXPECTED_FRAMEWORK_IDS = tuple(periodization.REQUIRED_FRAMEWORKS)


class HistoricalDocumentChronologyError(ValueError):
    """A source identity, date, projection, or output invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HistoricalDocumentChronologyError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalDocumentChronologyError(f"cannot read {label}: {path}") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


@lru_cache(maxsize=2)
def _validator(path: Path) -> Draft202012Validator:
    schema = read_json(path, "JSON schema")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _validate_schema(value: Mapping[str, Any], path: Path, label: str) -> None:
    errors = sorted(_validator(path).iter_errors(value), key=lambda error: list(error.absolute_path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or label
        raise HistoricalDocumentChronologyError(f"{label} schema violation at {location}: {errors[0].message}")


def _body_sha256(value: Mapping[str, Any], seal_key: str) -> str:
    return sha256_value({key: item for key, item in value.items() if key != seal_key})


def _framework_matches_for_year(year: int, freeze: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Apply one already-validated freeze without revalidating it per document."""
    framework_matches = []
    for framework in freeze["frameworks"]:
        matches = []
        for stage in framework["stages"]:
            status = periodization._year_match(stage, year)
            if status is not None:
                matches.append({"stage_id": stage["stage_id"], "match_status": status})
        require(matches, f"{framework['framework_id']}: year has no periodization match")
        framework_matches.append({"framework_id": framework["framework_id"], "matches": matches})
    return framework_matches


def build_record(
    *,
    collection_id: str,
    document_identity: str,
    locator: Mapping[str, str | int],
    date_field: str,
    raw_date: str | None,
    source_file_sha256: str,
    metadata_row_sha256: str,
    authority: str,
    freeze: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one sealed document-level chronological projection."""
    exact_year = int(raw_date) if raw_date is not None and re.fullmatch(r"[0-9]{4}", raw_date) else None
    if exact_year is None:
        status = "unresolved_no_exact_document_date"
        date_precision = "unknown"
        framework_matches: list[dict[str, Any]] = []
    else:
        status = "exact_date_projected"
        date_precision = "exact_year"
        framework_matches = _framework_matches_for_year(exact_year, freeze)

    body: dict[str, Any] = {
        "schema_version": RECORD_SCHEMA_VERSION,
        "record_id": f"chronology:{collection_id}:{sha256_value(dict(locator))[:24]}",
        "collection_id": collection_id,
        "document_identity": document_identity,
        "locator": dict(locator),
        "date_evidence": {
            "date_field": date_field,
            "raw_date": raw_date,
            "source_file_sha256": source_file_sha256,
            "metadata_row_sha256": metadata_row_sha256,
            "authority": authority,
        },
        "projection": {
            "role": "chronological_context_only",
            "status": status,
            "chronological_year": exact_year,
            "date_precision": date_precision,
            "canonical_framework_id": None,
            "framework_matches": framework_matches,
        },
        "safeguards": {
            "historical_forms_protected": True,
            "modern_correction_eligible": False,
            "linguistic_stage_gold": False,
            "semantic_label_created": False,
            "provider_calls": False,
            "phase4_authorized": False,
        },
    }
    record = {**body, "record_sha256": sha256_value(body)}
    validate_record(record, freeze=freeze)
    return record


def validate_record(value: Mapping[str, Any], *, freeze: Mapping[str, Any]) -> dict[str, Any]:
    record = json.loads(json.dumps(value, ensure_ascii=False))
    _validate_schema(record, RECORD_SCHEMA_PATH, "chronology record")
    require(record["record_sha256"] == _body_sha256(record, "record_sha256"), "record seal drift")
    projection = record["projection"]
    raw_date = record["date_evidence"]["raw_date"]
    expected_exact = raw_date is not None and re.fullmatch(r"[0-9]{4}", raw_date) is not None
    if expected_exact:
        year = int(raw_date)
        require(projection["status"] == "exact_date_projected", "exact date was not projected")
        require(projection["chronological_year"] == year, "projected year drift")
        require(projection["date_precision"] == "exact_year", "exact date precision drift")
        expected = _framework_matches_for_year(year, freeze)
        require(projection["framework_matches"] == expected, "framework projection drift")
        require(
            tuple(item["framework_id"] for item in expected) == EXPECTED_FRAMEWORK_IDS,
            "framework order or denominator drift",
        )
    else:
        require(
            projection["status"] == "unresolved_no_exact_document_date",
            "non-exact date must remain unresolved",
        )
        require(projection["chronological_year"] is None, "unresolved date gained a year")
        require(projection["date_precision"] == "unknown", "unresolved date precision drift")
        require(not projection["framework_matches"], "unresolved date gained framework matches")
    require(projection["canonical_framework_id"] is None, "canonical framework was selected")
    return record


def _load_full_receipt(path: Path) -> dict[str, Any]:
    require(Path(path).is_file(), f"missing historical full receipt: {path}")
    require(
        file_sha256(path) == EXPECTED_FULL_RECEIPT_FILE_SHA256,
        "historical full receipt file drift",
    )
    receipt = read_json(path, "historical full receipt")
    require(receipt.get("receipt_sha256") == EXPECTED_FULL_RECEIPT_SHA256, "full receipt seal drift")
    require(receipt.get("coverage", {}).get("full_materialization_complete") is True, "full corpus incomplete")
    require(receipt.get("phase_boundaries", {}).get("phase4_blocked") is True, "Phase 4 boundary drift")
    require(
        receipt.get("denominators", {}).get("ud_explicit_orv_uk") == materialization.UD_EXPECTED_DENOMINATOR,
        "full receipt UD denominator drift",
    )
    require(
        receipt.get("denominators", {}).get("plug2") == materialization.PLUG2_EXPECTED_DENOMINATOR,
        "full receipt PluG2 denominator drift",
    )
    require(receipt.get("inputs", {}).get("ud_file_sha256") == materialization.UD_EXPECTED_SHA256, "UD binding drift")
    require(
        receipt.get("inputs", {}).get("plug2_metadata_sha256") == materialization.PLUG2_METADATA_SHA256,
        "PluG2 metadata binding drift",
    )
    return receipt


def _verify_runtime_and_inputs(
    *,
    ud_dir: Path,
    plug2_metadata: Path,
    full_receipt_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    require(
        file_sha256(Path(periodization.__file__)) == EXPECTED_PERIODIZATION_IMPLEMENTATION_SHA256,
        "periodization implementation drift",
    )
    require(
        file_sha256(Path(materialization.__file__)) == EXPECTED_MATERIALIZATION_IMPLEMENTATION_SHA256,
        "historical materialization implementation drift",
    )
    freeze = periodization.load_freeze(PERIODIZATION_FREEZE_PATH)
    full_receipt = _load_full_receipt(full_receipt_path)
    for filename, expected_sha256 in materialization.UD_EXPECTED_SHA256.items():
        candidate = Path(ud_dir) / filename
        require(candidate.is_file(), f"missing UD input: {candidate}")
        require(file_sha256(candidate) == expected_sha256, f"UD input hash drift: {filename}")
    require(Path(plug2_metadata).is_file(), f"missing PluG2 metadata: {plug2_metadata}")
    require(
        file_sha256(plug2_metadata) == materialization.PLUG2_METADATA_SHA256,
        "PluG2 metadata hash drift",
    )
    return freeze, full_receipt


def _ud_records(ud_dir: Path, freeze: Mapping[str, Any]) -> list[dict[str, Any]]:
    sentences: list[materialization.UdSentence] = []
    for filename in sorted(materialization.UD_EXPECTED_SHA256):
        sentences.extend(
            materialization.parse_conllu(
                Path(ud_dir) / filename,
                source_file_sha256=materialization.UD_EXPECTED_SHA256[filename],
            )
        )
    candidates = [item for item in sentences if item.language == "orv-uk"]
    actual = {
        "documents": len({item.document_id for item in candidates}),
        "sentences": len(candidates),
        "token_rows": sum(len(item.tokens) for item in candidates),
    }
    require(actual == materialization.UD_EXPECTED_DENOMINATOR, "UD eligible denominator drift")

    grouped: dict[str, list[materialization.UdSentence]] = defaultdict(list)
    for sentence in candidates:
        grouped[sentence.document_id].append(sentence)
    records: list[dict[str, Any]] = []
    for document_identity in sorted(grouped):
        items = grouped[document_identity]
        metadata_values = {
            (
                item.source_file,
                item.source_file_sha256,
                item.language,
                item.created,
                item.title,
            )
            for item in items
        }
        require(len(metadata_values) == 1, f"UD document metadata drift: {document_identity}")
        source_file, source_sha256, language, created, title = next(iter(metadata_values))
        metadata = {
            "newdoc_id": document_identity,
            "lang": language,
            "created": created,
            "title": title,
            "sentence_count": len(items),
        }
        records.append(
            build_record(
                collection_id=materialization.UD_COLLECTION_ID,
                document_identity=document_identity,
                locator={
                    "dataset_id": materialization.UD_COLLECTION_ID,
                    "commit_sha": materialization.UD_COMMIT,
                    "source_file": source_file,
                    "newdoc_id": document_identity,
                },
                date_field="created",
                raw_date=created,
                source_file_sha256=source_sha256,
                metadata_row_sha256=sha256_value(metadata),
                authority="source_document_comment",
                freeze=freeze,
            )
        )
    return records


def _plug2_records(plug2_metadata: Path, freeze: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = materialization.load_plug2_metadata(plug2_metadata)
    candidate_rows = sorted(
        (row for row in rows if row.get("doc.original") == "UK"),
        key=lambda row: row["path"],
    )
    require(
        len(candidate_rows) == materialization.PLUG2_EXPECTED_DENOMINATOR["uk_documents"],
        "PluG2 eligible denominator drift",
    )
    return [
        build_record(
            collection_id=materialization.PLUG2_COLLECTION_ID,
            document_identity=row["path"],
            locator={
                "dataset_id": materialization.PLUG2_COLLECTION_ID,
                "doi": materialization.PLUG2_DOI,
                "metadata_file": Path(plug2_metadata).name,
                "member_path": row["path"],
            },
            date_field="doc.date",
            raw_date=row.get("doc.date") or None,
            source_file_sha256=materialization.PLUG2_METADATA_SHA256,
            metadata_row_sha256=sha256_value(row),
            authority="source_metadata_row",
            freeze=freeze,
        )
        for row in candidate_rows
    ]


def derive_records(
    *,
    ud_dir: Path,
    plug2_metadata: Path,
    full_receipt_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Re-derive every document projection from immutable source metadata."""
    freeze, full_receipt = _verify_runtime_and_inputs(
        ud_dir=ud_dir,
        plug2_metadata=plug2_metadata,
        full_receipt_path=full_receipt_path,
    )
    records = sorted(
        _ud_records(ud_dir, freeze) + _plug2_records(plug2_metadata, freeze),
        key=lambda item: item["record_id"],
    )
    record_ids = [item["record_id"] for item in records]
    require(len(record_ids) == len(set(record_ids)), "duplicate chronology record ID")
    require(record_ids == sorted(record_ids), "chronology records are not deterministically sorted")
    return records, freeze, full_receipt


def _denominator(records: Sequence[Mapping[str, Any]], collection_id: str) -> dict[str, int | None]:
    selected = [item for item in records if item["collection_id"] == collection_id]
    years = [item["projection"]["chronological_year"] for item in selected]
    exact_years = [year for year in years if year is not None]
    return {
        "eligible_documents": len(selected),
        "exact_date_documents": len(exact_years),
        "unresolved_date_documents": len(selected) - len(exact_years),
        "min_exact_year": min(exact_years) if exact_years else None,
        "max_exact_year": max(exact_years) if exact_years else None,
    }


def _projection_summary(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, Counter[tuple[str, str]]] = {framework_id: Counter() for framework_id in EXPECTED_FRAMEWORK_IDS}
    projected: Counter[str] = Counter()
    for record in records:
        for framework in record["projection"]["framework_matches"]:
            framework_id = framework["framework_id"]
            projected[framework_id] += 1
            for match in framework["matches"]:
                counts[framework_id][(match["stage_id"], match["match_status"])] += 1
    summary = []
    for framework_id in EXPECTED_FRAMEWORK_IDS:
        stage_ids = sorted({stage_id for stage_id, _status in counts[framework_id]})
        summary.append(
            {
                "framework_id": framework_id,
                "projected_documents": projected[framework_id],
                "stage_counts": [
                    {
                        "stage_id": stage_id,
                        "definite": counts[framework_id][(stage_id, "definite")],
                        "possible_boundary_overlap": counts[framework_id][(stage_id, "possible_boundary_overlap")],
                    }
                    for stage_id in stage_ids
                ],
            }
        )
    return summary


def _write_gzip(path: Path, records: Iterable[Mapping[str, Any]]) -> tuple[int, int, str]:
    count = 0
    with (
        path.open("wb") as raw_handle,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle,
    ):
        for record in records:
            gzip_handle.write(canonical_json(record).encode("utf-8") + b"\n")
            count += 1
    return count, path.stat().st_size, file_sha256(path)


def _read_gzip(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                value = json.loads(line)
                require(isinstance(value, dict), f"output line {line_number} is not an object")
                records.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalDocumentChronologyError(f"cannot read chronology output: {path}") from exc
    return records


def _build_receipt(
    *,
    records: Sequence[Mapping[str, Any]],
    full_receipt: Mapping[str, Any],
    output_bytes: int,
    output_sha256: str,
) -> dict[str, Any]:
    ud_denominator = _denominator(records, materialization.UD_COLLECTION_ID)
    plug2_denominator = _denominator(records, materialization.PLUG2_COLLECTION_ID)
    require(ud_denominator == EXPECTED_UD_DATE_DENOMINATOR, "UD date denominator drift")
    require(plug2_denominator == EXPECTED_PLUG2_DATE_DENOMINATOR, "PluG2 date denominator drift")
    body: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "text_free": True,
        "status": "DOCUMENT_CHRONOLOGY_PROJECTED_WITH_RESIDUALS",
        "bindings": {
            "historical_full_receipt_file_sha256": EXPECTED_FULL_RECEIPT_FILE_SHA256,
            "historical_full_receipt_sha256": full_receipt["receipt_sha256"],
            "historical_periodization_freeze_file_sha256": EXPECTED_PERIODIZATION_FREEZE_SHA256,
            "historical_periodization_freeze_receipt_sha256": periodization.load_freeze()["receipt_sha256"],
            "historical_periodization_implementation_sha256": EXPECTED_PERIODIZATION_IMPLEMENTATION_SHA256,
            "historical_materialization_implementation_sha256": EXPECTED_MATERIALIZATION_IMPLEMENTATION_SHA256,
            "ud_file_sha256": dict(sorted(materialization.UD_EXPECTED_SHA256.items())),
            "plug2_metadata_sha256": materialization.PLUG2_METADATA_SHA256,
        },
        "denominators": {
            "ud": ud_denominator,
            "plug2": plug2_denominator,
            "total_documents": len(records),
        },
        "projection_summary": _projection_summary(records),
        "output": {
            "filename": OUTPUT_FILENAME,
            "records": len(records),
            "bytes": output_bytes,
            "sha256": output_sha256,
            "record_identity_sha256": sha256_value([item["record_id"] for item in records]),
        },
        "coverage": {
            "source_document_denominator_equal": True,
            "exact_date_projection_complete": True,
            "undated_documents_preserved_unresolved": True,
            "qualified_historical_semantic_review_complete": False,
        },
        "safeguards": {
            "chronology_is_not_linguistic_stage_gold": True,
            "frameworks_preserved_without_collapse": True,
            "historical_forms_protected": True,
            "modern_correction_eligible": False,
            "provider_calls": False,
        },
        "phase_boundaries": {
            "source_freeze_ready": False,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }
    receipt = {**body, "receipt_sha256": sha256_value(body)}
    _validate_schema(receipt, RECEIPT_SCHEMA_PATH, "chronology receipt")
    return receipt


def validate_bundle(
    *,
    output_dir: Path,
    ud_dir: Path,
    plug2_metadata: Path,
    full_receipt_path: Path,
) -> dict[str, Any]:
    """Re-derive and compare every private record and text-free receipt field."""
    output_dir = Path(output_dir)
    output_path = output_dir / OUTPUT_FILENAME
    receipt_path = output_dir / RECEIPT_FILENAME
    require(output_path.is_file(), f"missing chronology output: {output_path}")
    require(receipt_path.is_file(), f"missing chronology receipt: {receipt_path}")
    expected_records, freeze, full_receipt = derive_records(
        ud_dir=ud_dir,
        plug2_metadata=plug2_metadata,
        full_receipt_path=full_receipt_path,
    )
    actual_records = _read_gzip(output_path)
    require(len(actual_records) == len(expected_records), "chronology output denominator drift")
    for index, (actual, expected) in enumerate(zip(actual_records, expected_records, strict=True)):
        validate_record(actual, freeze=freeze)
        require(actual == expected, f"chronology output source re-derivation drift at record {index}")
    actual_receipt = read_json(receipt_path, "chronology receipt")
    _validate_schema(actual_receipt, RECEIPT_SCHEMA_PATH, "chronology receipt")
    require(
        actual_receipt["receipt_sha256"] == _body_sha256(actual_receipt, "receipt_sha256"),
        "chronology receipt seal drift",
    )
    expected_receipt = _build_receipt(
        records=expected_records,
        full_receipt=full_receipt,
        output_bytes=output_path.stat().st_size,
        output_sha256=file_sha256(output_path),
    )
    require(actual_receipt == expected_receipt, "chronology receipt source re-derivation drift")
    return actual_receipt


def materialize(
    *,
    output_dir: Path,
    ud_dir: Path,
    plug2_metadata: Path,
    full_receipt_path: Path,
) -> dict[str, Any]:
    """Write one immutable private projection bundle, then replay-validate it."""
    output_dir = Path(output_dir).resolve()
    require(not materialization._inside_git_checkout(output_dir), "private output cannot be inside Git")
    require(not output_dir.exists(), "immutable chronology output directory already exists")
    require(output_dir.parent.is_dir(), "chronology output parent does not exist")
    records, _freeze, full_receipt = derive_records(
        ud_dir=ud_dir,
        plug2_metadata=plug2_metadata,
        full_receipt_path=full_receipt_path,
    )
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent))
    try:
        output_path = staging / OUTPUT_FILENAME
        count, output_bytes, output_sha256 = _write_gzip(output_path, records)
        require(count == len(records), "chronology output write denominator drift")
        receipt = _build_receipt(
            records=records,
            full_receipt=full_receipt,
            output_bytes=output_bytes,
            output_sha256=output_sha256,
        )
        (staging / RECEIPT_FILENAME).write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        validate_bundle(
            output_dir=staging,
            ud_dir=ud_dir,
            plug2_metadata=plug2_metadata,
            full_receipt_path=full_receipt_path,
        )
        os.replace(staging, output_dir)
        return receipt
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ud-dir", type=Path, required=True)
    parser.add_argument("--plug2-metadata", type=Path, required=True)
    parser.add_argument("--full-receipt", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--output-dir", type=Path)
    action.add_argument("--validate-dir", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.output_dir is not None:
            receipt = materialize(
                output_dir=args.output_dir,
                ud_dir=args.ud_dir,
                plug2_metadata=args.plug2_metadata,
                full_receipt_path=args.full_receipt,
            )
            status = "document_chronology_materialized"
        else:
            receipt = validate_bundle(
                output_dir=args.validate_dir,
                ud_dir=args.ud_dir,
                plug2_metadata=args.plug2_metadata,
                full_receipt_path=args.full_receipt,
            )
            status = "document_chronology_validated"
    except (HistoricalDocumentChronologyError, periodization.HistoricalPeriodizationError) as exc:
        print(canonical_json({"status": "blocked", "error": str(exc)}))
        return 2
    print(
        canonical_json(
            {
                "status": status,
                "records": receipt["output"]["records"],
                "ud_exact": receipt["denominators"]["ud"]["exact_date_documents"],
                "ud_unresolved": receipt["denominators"]["ud"]["unresolved_date_documents"],
                "plug2_exact": receipt["denominators"]["plug2"]["exact_date_documents"],
                "receipt_sha256": receipt["receipt_sha256"],
                "linguistic_stage_gold": False,
                "phase4_authorized": False,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
