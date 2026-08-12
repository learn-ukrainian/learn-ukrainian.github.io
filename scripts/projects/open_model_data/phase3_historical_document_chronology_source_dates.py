#!/usr/bin/env python3
"""Supersede the v1 chronology residual with explicit source date comments.

The v1 adapter consumed ``# created =`` but not the UD treebank's separate
``# date =`` document metadata.  This adapter replays the complete admitted
historical-document denominator, preserves exact years and bounded intervals,
and projects chronology through every frozen attributed Ukrainian framework.
It never derives dates from titles, filenames, or corpus-wide ranges.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.projects.open_model_data import phase3_historical_document_chronology as chronology_v1
from scripts.projects.open_model_data import phase3_historical_materialization as materialization
from scripts.projects.open_model_data import phase3_historical_periodization as periodization

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
RECORD_SCHEMA_PATH = DATA / "contracts/phase3_historical_document_chronology_record_v2.schema.json"
RECEIPT_SCHEMA_PATH = DATA / "contracts/phase3_historical_document_chronology_receipt_v2.schema.json"

RECORD_SCHEMA_VERSION = "phase3_historical_document_chronology_record_v2"
RECEIPT_SCHEMA_VERSION = "phase3_historical_document_chronology_receipt_v2"
OUTPUT_FILENAME = "historical-document-chronology-v2.jsonl.gz"
RECEIPT_FILENAME = "historical-document-chronology-receipt-v2.json"

EXPECTED_CHRONOLOGY_V1_IMPLEMENTATION_SHA256 = "67ae42be05f8cf783fc029c3be5871dbd5ca73e7648c57fe78281f6ebd6620e0"
EXPECTED_V1_OUTPUT_SHA256 = "a9b87bd7b6c8be7f7a43defaaeabd928d03f8181dca73197c39f6b5f31340be5"
EXPECTED_V1_RECEIPT_FILE_SHA256 = "88f892663081d2e0551e1e3a85ae7b60612de7d312e45c7c983e42f3c128ead2"
EXPECTED_V1_RECEIPT_SHA256 = "5e784812a14d4e66321657eda936ab966af2ca2c3be740c3e21251a7aea38b23"

RATUSHNA_PREFIX = "RatushnaKniga_1986__"
RATUSHNA_EDITION_IDENTITY = "Lohvytska-ratushna-knyha-1986"
RATUSHNA_CATALOGUE_URL = "https://resource.history.org.ua/item/0006486"
RATUSHNA_PDF_URL = "https://history.org.ua/LiberUA/e_dzherela_RatushnaKniga_1986/e_dzherela_RatushnaKniga_1986.pdf"
EXPECTED_RATUSHNA_CATALOGUE_SHA256 = "fdc0f3ae5cb585cfafe0ad2601634201c4337aa3094edf102fdf4c270aa02d2a"
EXPECTED_RATUSHNA_PDF_SHA256 = "4c0d47a993c6701ab8be7d0cd91f080d076de758c684a9c213957f8fb6007ac2"

EXPECTED_UD_DATE_DENOMINATOR = {
    "eligible_documents": 82,
    "exact_year_documents": 80,
    "bounded_interval_documents": 2,
    "undated_documents": 0,
}
EXPECTED_PLUG2_DATE_DENOMINATOR = {
    "eligible_documents": 56080,
    "exact_year_documents": 56080,
    "bounded_interval_documents": 0,
    "undated_documents": 0,
}
EXPECTED_TOTAL_DOCUMENTS = 56162
EXPECTED_TOTAL_EXACT_YEAR = 56160
EXPECTED_TOTAL_BOUNDED_INTERVAL = 2
EXPECTED_FRAMEWORK_IDS = tuple(periodization.REQUIRED_FRAMEWORKS)

_NEWDOC_RE = re.compile(r"^# newdoc(?:_id| id)? = (.+)$")
_EXACT_YEAR_RE = re.compile(r"^([0-9]{4})$")
_YEAR_INTERVAL_RE = re.compile(r"^([0-9]{4})-([0-9]{4})$")


class HistoricalSourceDateError(ValueError):
    """An immutable input, source date, projection, or output invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HistoricalSourceDateError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_value(value: Any) -> str:
    return chronology_v1.sha256_value(value)


def file_sha256(path: Path) -> str:
    return chronology_v1.file_sha256(path)


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalSourceDateError(f"cannot read {label}: {path}") from exc
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
        raise HistoricalSourceDateError(f"{label} schema violation at {location}: {errors[0].message}")


def _body_sha256(value: Mapping[str, Any], seal_key: str) -> str:
    return sha256_value({key: item for key, item in value.items() if key != seal_key})


@dataclass(frozen=True)
class UdDocumentMetadata:
    document_identity: str
    source_file: str
    source_file_sha256: str
    language: str | None
    title: str | None
    created: str | None
    date: str | None
    comment_lines: Mapping[str, int]
    sentence_count: int


def _flush_ud_document(
    current: dict[str, Any] | None,
    *,
    source_file: str,
    source_file_sha256: str,
    records: dict[str, UdDocumentMetadata],
) -> None:
    if current is None:
        return
    document_identity = current["document_identity"]
    require(document_identity not in records, f"duplicate UD document metadata: {document_identity}")
    records[document_identity] = UdDocumentMetadata(
        document_identity=document_identity,
        source_file=source_file,
        source_file_sha256=source_file_sha256,
        language=current.get("language"),
        title=current.get("title"),
        created=current.get("created"),
        date=current.get("date"),
        comment_lines=dict(current["comment_lines"]),
        sentence_count=current["sentence_count"],
    )


def parse_ud_document_metadata(ud_dir: Path) -> dict[str, UdDocumentMetadata]:
    """Parse only document comments, preserving exact source line locators."""
    records: dict[str, UdDocumentMetadata] = {}
    for filename, expected_sha256 in sorted(materialization.UD_EXPECTED_SHA256.items()):
        path = Path(ud_dir) / filename
        require(path.is_file(), f"missing UD input: {path}")
        require(file_sha256(path) == expected_sha256, f"UD input hash drift: {filename}")
        current: dict[str, Any] | None = None
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except OSError as exc:
            raise HistoricalSourceDateError(f"cannot read UD input: {path}") from exc
        for line_number, line in enumerate(lines, start=1):
            newdoc_match = _NEWDOC_RE.fullmatch(line)
            if newdoc_match:
                _flush_ud_document(
                    current,
                    source_file=filename,
                    source_file_sha256=expected_sha256,
                    records=records,
                )
                current = {
                    "document_identity": newdoc_match.group(1),
                    "comment_lines": {"newdoc": line_number},
                    "sentence_count": 0,
                }
                continue
            if current is None:
                continue
            field: str | None = None
            value: str | None = None
            for prefix, candidate_field in (
                ("# lang = ", "language"),
                ("# title = ", "title"),
                ("# created = ", "created"),
                ("# date = ", "date"),
            ):
                if line.startswith(prefix):
                    field = candidate_field
                    value = line[len(prefix) :]
                    break
            if field is not None:
                require(field not in current, f"duplicate UD {field}: {current['document_identity']}")
                current[field] = value
                current["comment_lines"][field] = line_number
            elif line.startswith("# sent_id = "):
                current["sentence_count"] += 1
        _flush_ud_document(
            current,
            source_file=filename,
            source_file_sha256=expected_sha256,
            records=records,
        )
    return records


def parse_source_date(raw_date: str) -> tuple[int, int, str]:
    exact_match = _EXACT_YEAR_RE.fullmatch(raw_date)
    if exact_match:
        year = int(exact_match.group(1))
        require(1000 <= year <= 2100, "source year outside supported historical bounds")
        return year, year, "exact_year"
    interval_match = _YEAR_INTERVAL_RE.fullmatch(raw_date)
    require(interval_match is not None, f"unsupported source date syntax: {raw_date}")
    start_year, end_year = (int(value) for value in interval_match.groups())
    require(1000 <= start_year < end_year <= 2100, "invalid source date interval")
    return start_year, end_year, "bounded_interval"


def _framework_projections(start_year: int, end_year: int, freeze: Mapping[str, Any]) -> list[dict[str, Any]]:
    per_year = {
        year: {
            item["framework_id"]: item["matches"] for item in chronology_v1._framework_matches_for_year(year, freeze)
        }
        for year in range(start_year, end_year + 1)
    }
    projections = []
    for framework_id in EXPECTED_FRAMEWORK_IDS:
        year_matches = [per_year[year][framework_id] for year in range(start_year, end_year + 1)]
        signatures = {canonical_json(matches) for matches in year_matches}
        candidate_stage_ids = sorted({match["stage_id"] for matches in year_matches for match in matches})
        if start_year == end_year:
            stability = "exact_year"
            matches = year_matches[0]
        elif len(signatures) == 1:
            stability = "stable_across_interval"
            matches = year_matches[0]
        else:
            stability = "boundary_sensitive_interval"
            matches = []
        projections.append(
            {
                "framework_id": framework_id,
                "interval_stability": stability,
                "matches": matches,
                "candidate_stage_ids": candidate_stage_ids,
            }
        )
    return projections


def _edition_binding(catalogue_sha256: str, pdf_sha256: str) -> dict[str, Any]:
    return {
        "edition_identity": RATUSHNA_EDITION_IDENTITY,
        "official_catalogue_url": RATUSHNA_CATALOGUE_URL,
        "official_pdf_url": RATUSHNA_PDF_URL,
        "official_catalogue_sha256": catalogue_sha256,
        "official_pdf_sha256": pdf_sha256,
        "scope": "edition_level_corroboration_not_date_inference",
    }


def _select_ud_date(metadata: UdDocumentMetadata) -> tuple[str, str, int]:
    values = [("created", metadata.created), ("date", metadata.date)]
    present = [(field, value) for field, value in values if value not in (None, "")]
    require(present, f"UD document lacks source date metadata: {metadata.document_identity}")
    if len(present) == 2:
        created_bounds = parse_source_date(present[0][1])
        date_bounds = parse_source_date(present[1][1])
        require(created_bounds == date_bounds, f"conflicting UD source date fields: {metadata.document_identity}")
    selected_field, raw_date = present[0]
    return selected_field, raw_date, metadata.comment_lines[selected_field]


def build_record(
    *,
    v1_record: Mapping[str, Any],
    freeze: Mapping[str, Any],
    ud_metadata: UdDocumentMetadata | None,
    catalogue_sha256: str,
    pdf_sha256: str,
) -> dict[str, Any]:
    collection_id = v1_record["collection_id"]
    document_identity = v1_record["document_identity"]
    if collection_id == materialization.UD_COLLECTION_ID:
        require(ud_metadata is not None, f"missing UD metadata: {document_identity}")
        require(ud_metadata.document_identity == document_identity, "UD document identity drift")
        require(ud_metadata.language == "orv-uk", f"UD language eligibility drift: {document_identity}")
        require(ud_metadata.source_file == v1_record["locator"]["source_file"], "UD source file drift")
        selected_field, raw_date, comment_line = _select_ud_date(ud_metadata)
        source_values = {"created": ud_metadata.created, "date": ud_metadata.date, "doc.date": None}
        metadata_row = {
            "newdoc_id": document_identity,
            "lang": ud_metadata.language,
            "title": ud_metadata.title,
            "created": ud_metadata.created,
            "date": ud_metadata.date,
            "sentence_count": ud_metadata.sentence_count,
            "comment_lines": dict(ud_metadata.comment_lines),
        }
        source_file_sha256 = ud_metadata.source_file_sha256
        authority = "source_document_comment"
        corroboration = (
            _edition_binding(catalogue_sha256, pdf_sha256) if document_identity.startswith(RATUSHNA_PREFIX) else None
        )
    else:
        require(collection_id == materialization.PLUG2_COLLECTION_ID, "unknown chronology collection")
        require(ud_metadata is None, f"unexpected UD metadata for PluG2 document: {document_identity}")
        selected_field = "doc.date"
        raw_date = v1_record["date_evidence"]["raw_date"]
        require(isinstance(raw_date, str), f"PluG2 document lacks source date: {document_identity}")
        comment_line = None
        source_values = {"created": None, "date": None, "doc.date": raw_date}
        metadata_row = {
            "document_identity": document_identity,
            "raw_date": raw_date,
            "v1_metadata_row_sha256": v1_record["date_evidence"]["metadata_row_sha256"],
        }
        source_file_sha256 = v1_record["date_evidence"]["source_file_sha256"]
        authority = "source_metadata_row"
        corroboration = None

    start_year, end_year, precision = parse_source_date(raw_date)
    status = "exact_date_projected" if precision == "exact_year" else "bounded_interval_projected"
    body: dict[str, Any] = {
        "schema_version": RECORD_SCHEMA_VERSION,
        "record_id": f"chronology-v2:{collection_id}:{sha256_value(dict(v1_record['locator']))[:24]}",
        "collection_id": collection_id,
        "document_identity": document_identity,
        "locator": dict(v1_record["locator"]),
        "date_evidence": {
            "selected_field": selected_field,
            "raw_date": raw_date,
            "source_field_values": source_values,
            "source_comment_line": comment_line,
            "source_file_sha256": source_file_sha256,
            "metadata_row_sha256": sha256_value(metadata_row),
            "authority": authority,
            "corroborating_edition": corroboration,
        },
        "projection": {
            "role": "chronological_context_only",
            "status": status,
            "chronological_start_year": start_year,
            "chronological_end_year": end_year,
            "date_precision": precision,
            "canonical_framework_id": None,
            "framework_projections": _framework_projections(start_year, end_year, freeze),
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
    _validate_schema(record, RECORD_SCHEMA_PATH, "chronology v2 record")
    require(record["record_sha256"] == _body_sha256(record, "record_sha256"), "record seal drift")
    collection_id = record["collection_id"]
    document_identity = record["document_identity"]
    locator = record["locator"]
    require(locator["dataset_id"] == collection_id, "record collection locator drift")
    expected_record_id = f"chronology-v2:{collection_id}:{sha256_value(locator)[:24]}"
    require(record["record_id"] == expected_record_id, "record identity drift")
    evidence = record["date_evidence"]
    projection = record["projection"]
    start_year, end_year, precision = parse_source_date(evidence["raw_date"])
    require(projection["chronological_start_year"] == start_year, "chronology start year drift")
    require(projection["chronological_end_year"] == end_year, "chronology end year drift")
    require(projection["date_precision"] == precision, "chronology date precision drift")
    expected_status = "exact_date_projected" if precision == "exact_year" else "bounded_interval_projected"
    require(projection["status"] == expected_status, "chronology projection status drift")
    require(
        projection["framework_projections"] == _framework_projections(start_year, end_year, freeze),
        "framework projection drift",
    )
    require(projection["canonical_framework_id"] is None, "canonical framework was selected")
    selected_field = evidence["selected_field"]
    require(
        evidence["source_field_values"][selected_field] == evidence["raw_date"],
        "selected source date field drift",
    )
    is_ratushna = document_identity.startswith(RATUSHNA_PREFIX)
    if collection_id == materialization.UD_COLLECTION_ID:
        require(locator.get("newdoc_id") == document_identity, "UD document locator drift")
        require(evidence["selected_field"] in {"created", "date"}, "UD source field authority drift")
        require(evidence["authority"] == "source_document_comment", "UD date authority drift")
        require(isinstance(evidence["source_comment_line"], int), "UD source comment line missing")
        require(evidence["source_field_values"]["doc.date"] is None, "UD metadata-row date leakage")
        source_file = locator.get("source_file")
        require(source_file in materialization.UD_EXPECTED_SHA256, "UD source file locator drift")
        require(
            evidence["source_file_sha256"] == materialization.UD_EXPECTED_SHA256[source_file],
            "UD source file hash drift",
        )
    else:
        require(collection_id == materialization.PLUG2_COLLECTION_ID, "unknown chronology collection")
        require(locator.get("member_path") == document_identity, "PluG2 document locator drift")
        require(evidence["selected_field"] == "doc.date", "PluG2 source field authority drift")
        require(evidence["authority"] == "source_metadata_row", "PluG2 date authority drift")
        require(evidence["source_comment_line"] is None, "PluG2 source comment line must be absent")
        require(evidence["source_field_values"]["created"] is None, "PluG2 created field leakage")
        require(evidence["source_field_values"]["date"] is None, "PluG2 date field leakage")
        require(evidence["source_file_sha256"] == materialization.PLUG2_METADATA_SHA256, "PluG2 metadata hash drift")
    if is_ratushna:
        require(collection_id == materialization.UD_COLLECTION_ID, "Ratushna identity outside UD collection")
        require(
            evidence["corroborating_edition"]
            == _edition_binding(EXPECTED_RATUSHNA_CATALOGUE_SHA256, EXPECTED_RATUSHNA_PDF_SHA256),
            "Ratushna edition corroboration drift",
        )
        require(evidence["selected_field"] == "date", "Ratushna date must come from source date comment")
    else:
        require(evidence["corroborating_edition"] is None, "unrelated edition corroboration attached")
    return record


def _verify_inputs(
    *,
    ud_dir: Path,
    plug2_metadata: Path,
    full_receipt_path: Path,
    v1_chronology_dir: Path,
    ratushna_pdf: Path,
    ratushna_catalogue: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    require(
        file_sha256(Path(chronology_v1.__file__)) == EXPECTED_CHRONOLOGY_V1_IMPLEMENTATION_SHA256,
        "chronology v1 implementation drift",
    )
    require(file_sha256(ratushna_pdf) == EXPECTED_RATUSHNA_PDF_SHA256, "Ratushna PDF hash drift")
    require(
        file_sha256(ratushna_catalogue) == EXPECTED_RATUSHNA_CATALOGUE_SHA256,
        "Ratushna catalogue hash drift",
    )
    v1_receipt_path = Path(v1_chronology_dir) / chronology_v1.RECEIPT_FILENAME
    require(file_sha256(v1_receipt_path) == EXPECTED_V1_RECEIPT_FILE_SHA256, "chronology v1 receipt file drift")
    v1_receipt = chronology_v1.validate_bundle(
        output_dir=v1_chronology_dir,
        ud_dir=ud_dir,
        plug2_metadata=plug2_metadata,
        full_receipt_path=full_receipt_path,
    )
    require(v1_receipt["receipt_sha256"] == EXPECTED_V1_RECEIPT_SHA256, "chronology v1 receipt seal drift")
    require(v1_receipt["output"]["sha256"] == EXPECTED_V1_OUTPUT_SHA256, "chronology v1 output drift")
    v1_records, freeze, _full_receipt = chronology_v1.derive_records(
        ud_dir=ud_dir,
        plug2_metadata=plug2_metadata,
        full_receipt_path=full_receipt_path,
    )
    return v1_records, freeze, v1_receipt


def derive_records(
    *,
    ud_dir: Path,
    plug2_metadata: Path,
    full_receipt_path: Path,
    v1_chronology_dir: Path,
    ratushna_pdf: Path,
    ratushna_catalogue: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    v1_records, freeze, v1_receipt = _verify_inputs(
        ud_dir=ud_dir,
        plug2_metadata=plug2_metadata,
        full_receipt_path=full_receipt_path,
        v1_chronology_dir=v1_chronology_dir,
        ratushna_pdf=ratushna_pdf,
        ratushna_catalogue=ratushna_catalogue,
    )
    ud_metadata = parse_ud_document_metadata(ud_dir)
    eligible_ud_ids = {
        item["document_identity"] for item in v1_records if item["collection_id"] == materialization.UD_COLLECTION_ID
    }
    require(
        len(eligible_ud_ids) == materialization.UD_EXPECTED_DENOMINATOR["documents"], "UD identity denominator drift"
    )
    require(eligible_ud_ids <= set(ud_metadata), "UD source metadata coverage drift")
    records = []
    for v1_record in v1_records:
        metadata = (
            ud_metadata[v1_record["document_identity"]]
            if v1_record["collection_id"] == materialization.UD_COLLECTION_ID
            else None
        )
        records.append(
            build_record(
                v1_record=v1_record,
                freeze=freeze,
                ud_metadata=metadata,
                catalogue_sha256=EXPECTED_RATUSHNA_CATALOGUE_SHA256,
                pdf_sha256=EXPECTED_RATUSHNA_PDF_SHA256,
            )
        )
    records.sort(key=lambda item: item["record_id"])
    record_ids = [item["record_id"] for item in records]
    require(len(record_ids) == len(set(record_ids)), "duplicate chronology v2 record ID")
    return records, freeze, v1_receipt


def _denominator(records: Sequence[Mapping[str, Any]], collection_id: str) -> dict[str, int]:
    selected = [item for item in records if item["collection_id"] == collection_id]
    exact = sum(item["projection"]["date_precision"] == "exact_year" for item in selected)
    intervals = sum(item["projection"]["date_precision"] == "bounded_interval" for item in selected)
    return {
        "eligible_documents": len(selected),
        "exact_year_documents": exact,
        "bounded_interval_documents": intervals,
        "undated_documents": len(selected) - exact - intervals,
    }


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
        raise HistoricalSourceDateError(f"cannot read chronology v2 output: {path}") from exc
    return records


def _build_receipt(
    *,
    records: Sequence[Mapping[str, Any]],
    v1_receipt: Mapping[str, Any],
    output_bytes: int,
    output_sha256: str,
) -> dict[str, Any]:
    ud_denominator = _denominator(records, materialization.UD_COLLECTION_ID)
    plug2_denominator = _denominator(records, materialization.PLUG2_COLLECTION_ID)
    require(ud_denominator == EXPECTED_UD_DATE_DENOMINATOR, "UD source-date denominator drift")
    require(plug2_denominator == EXPECTED_PLUG2_DATE_DENOMINATOR, "PluG2 source-date denominator drift")
    total_exact = ud_denominator["exact_year_documents"] + plug2_denominator["exact_year_documents"]
    total_intervals = ud_denominator["bounded_interval_documents"] + plug2_denominator["bounded_interval_documents"]
    require(len(records) == EXPECTED_TOTAL_DOCUMENTS, "total document denominator drift")
    require(total_exact == EXPECTED_TOTAL_EXACT_YEAR, "total exact-year denominator drift")
    require(total_intervals == EXPECTED_TOTAL_BOUNDED_INTERVAL, "total interval denominator drift")
    interval_records = [item for item in records if item["projection"]["date_precision"] == "bounded_interval"]
    all_intervals_stable = all(
        all(
            projection["interval_stability"] == "stable_across_interval"
            for projection in item["projection"]["framework_projections"]
        )
        for item in interval_records
    )
    require(all_intervals_stable, "a source date interval crosses an attributed framework boundary")
    body: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "text_free": True,
        "status": "DOCUMENT_SOURCE_DATES_PROJECTED_NO_UNDATED_DOCUMENTS",
        "supersedes": {
            "v1_output_sha256": v1_receipt["output"]["sha256"],
            "v1_receipt_file_sha256": EXPECTED_V1_RECEIPT_FILE_SHA256,
            "v1_receipt_sha256": v1_receipt["receipt_sha256"],
            "reason": "v1_parser_omitted_explicit_ud_date_comments",
        },
        "bindings": {
            "chronology_v1_implementation_sha256": EXPECTED_CHRONOLOGY_V1_IMPLEMENTATION_SHA256,
            "historical_periodization_freeze_file_sha256": chronology_v1.EXPECTED_PERIODIZATION_FREEZE_SHA256,
            "ud_file_sha256": dict(sorted(materialization.UD_EXPECTED_SHA256.items())),
            "plug2_metadata_sha256": materialization.PLUG2_METADATA_SHA256,
            "ratushna_official_catalogue_sha256": EXPECTED_RATUSHNA_CATALOGUE_SHA256,
            "ratushna_official_pdf_sha256": EXPECTED_RATUSHNA_PDF_SHA256,
        },
        "denominators": {
            "ud": ud_denominator,
            "plug2": plug2_denominator,
            "total_documents": len(records),
            "total_exact_year": total_exact,
            "total_bounded_interval": total_intervals,
        },
        "output": {
            "filename": OUTPUT_FILENAME,
            "records": len(records),
            "bytes": output_bytes,
            "sha256": output_sha256,
            "record_identity_sha256": sha256_value([item["record_id"] for item in records]),
        },
        "coverage": {
            "source_document_denominator_equal": True,
            "source_date_present_for_every_document": True,
            "undated_documents": 0,
            "bounded_intervals_preserved": True,
            "all_intervals_stable_within_each_framework": True,
            "qualified_historical_semantic_review_complete": False,
        },
        "safeguards": {
            "chronology_is_not_linguistic_stage_gold": True,
            "frameworks_preserved_without_collapse": True,
            "no_title_or_filename_date_inference": True,
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
    _validate_schema(receipt, RECEIPT_SCHEMA_PATH, "chronology v2 receipt")
    return receipt


def validate_bundle(
    *,
    output_dir: Path,
    ud_dir: Path,
    plug2_metadata: Path,
    full_receipt_path: Path,
    v1_chronology_dir: Path,
    ratushna_pdf: Path,
    ratushna_catalogue: Path,
) -> dict[str, Any]:
    output_path = Path(output_dir) / OUTPUT_FILENAME
    receipt_path = Path(output_dir) / RECEIPT_FILENAME
    require(output_path.is_file(), f"missing chronology v2 output: {output_path}")
    require(receipt_path.is_file(), f"missing chronology v2 receipt: {receipt_path}")
    expected_records, freeze, v1_receipt = derive_records(
        ud_dir=ud_dir,
        plug2_metadata=plug2_metadata,
        full_receipt_path=full_receipt_path,
        v1_chronology_dir=v1_chronology_dir,
        ratushna_pdf=ratushna_pdf,
        ratushna_catalogue=ratushna_catalogue,
    )
    actual_records = _read_gzip(output_path)
    require(len(actual_records) == len(expected_records), "chronology v2 output denominator drift")
    for index, (actual, expected) in enumerate(zip(actual_records, expected_records, strict=True)):
        validate_record(actual, freeze=freeze)
        require(actual == expected, f"chronology v2 source re-derivation drift at record {index}")
    actual_receipt = read_json(receipt_path, "chronology v2 receipt")
    _validate_schema(actual_receipt, RECEIPT_SCHEMA_PATH, "chronology v2 receipt")
    require(actual_receipt["receipt_sha256"] == _body_sha256(actual_receipt, "receipt_sha256"), "receipt seal drift")
    expected_receipt = _build_receipt(
        records=expected_records,
        v1_receipt=v1_receipt,
        output_bytes=output_path.stat().st_size,
        output_sha256=file_sha256(output_path),
    )
    require(actual_receipt == expected_receipt, "chronology v2 receipt source re-derivation drift")
    return actual_receipt


def materialize(
    *,
    output_dir: Path,
    ud_dir: Path,
    plug2_metadata: Path,
    full_receipt_path: Path,
    v1_chronology_dir: Path,
    ratushna_pdf: Path,
    ratushna_catalogue: Path,
) -> dict[str, Any]:
    output_dir = Path(output_dir).resolve()
    require(not materialization._inside_git_checkout(output_dir), "private output cannot be inside Git")
    require(not output_dir.exists(), "immutable chronology v2 output directory already exists")
    require(output_dir.parent.is_dir(), "chronology v2 output parent does not exist")
    records, _freeze, v1_receipt = derive_records(
        ud_dir=ud_dir,
        plug2_metadata=plug2_metadata,
        full_receipt_path=full_receipt_path,
        v1_chronology_dir=v1_chronology_dir,
        ratushna_pdf=ratushna_pdf,
        ratushna_catalogue=ratushna_catalogue,
    )
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent))
    try:
        output_path = staging / OUTPUT_FILENAME
        count, output_bytes, output_sha256 = _write_gzip(output_path, records)
        require(count == len(records), "chronology v2 write denominator drift")
        receipt = _build_receipt(
            records=records,
            v1_receipt=v1_receipt,
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
            v1_chronology_dir=v1_chronology_dir,
            ratushna_pdf=ratushna_pdf,
            ratushna_catalogue=ratushna_catalogue,
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
    parser.add_argument("--v1-chronology-dir", type=Path, required=True)
    parser.add_argument("--ratushna-pdf", type=Path, required=True)
    parser.add_argument("--ratushna-catalogue", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--output-dir", type=Path)
    action.add_argument("--validate-dir", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    common = {
        "ud_dir": args.ud_dir,
        "plug2_metadata": args.plug2_metadata,
        "full_receipt_path": args.full_receipt,
        "v1_chronology_dir": args.v1_chronology_dir,
        "ratushna_pdf": args.ratushna_pdf,
        "ratushna_catalogue": args.ratushna_catalogue,
    }
    try:
        if args.output_dir is not None:
            receipt = materialize(output_dir=args.output_dir, **common)
            status = "document_source_dates_materialized"
        else:
            receipt = validate_bundle(output_dir=args.validate_dir, **common)
            status = "document_source_dates_validated"
    except (
        HistoricalSourceDateError,
        chronology_v1.HistoricalDocumentChronologyError,
        materialization.HistoricalMaterializationError,
        periodization.HistoricalPeriodizationError,
    ) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "status": status,
                "records": receipt["output"]["records"],
                "exact_year": receipt["denominators"]["total_exact_year"],
                "bounded_interval": receipt["denominators"]["total_bounded_interval"],
                "undated": receipt["coverage"]["undated_documents"],
                "linguistic_stage_gold": False,
                "phase4_authorized": False,
                "receipt_sha256": receipt["receipt_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
