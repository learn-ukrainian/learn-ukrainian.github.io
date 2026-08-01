"""Produce real, text-local Ukrainian Foundry model-view evidence.

This module prepares the admitted Ukrainian Wikipedia source payloads, projects
the non-human #6168 detector/silver routes into conservative character loss
masks, measures a pinned tokenizer, and freezes text-free feasibility evidence.
It never trains a model, uploads data, or promotes silver to human gold.
"""

from __future__ import annotations

import argparse
import array
import collections
import json
import math
import platform
import re
import sqlite3
import unicodedata
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from importlib import metadata
from itertools import pairwise, zip_longest
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from tokenizers import Tokenizer

from scripts.projects.open_model_data import model_view_exporter as exporter
from scripts.projects.open_model_data import silver_evidence_factory as silver
from scripts.projects.open_model_data import validate_source_records as source_record_contract
from scripts.verification.vesum import verify_words

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
PAYLOAD_SCHEMA = CONTRACTS / "foundry_source_payload_v1.schema.json"
SILVER_SCHEMA = CONTRACTS / "language_contact_silver_record_v1.schema.json"
PAYLOAD_RECEIPT_SCHEMA = CONTRACTS / "source_payload_preparation_receipt_v1.schema.json"
TOKENIZER_RECEIPT_SCHEMA = CONTRACTS / "tokenizer_diagnostics_v1.schema.json"
PRODUCTION_RECEIPT_SCHEMA = CONTRACTS / "model_ready_view_production_v1.schema.json"
DEFAULT_DETECTOR_RECEIPT = ROOT / "data/projects/open_model_data/detector/language_contact_receipt_v1.json"
DEFAULT_SILVER_RECEIPT = ROOT / "data/projects/open_model_data/silver/language_contact_silver_receipt_v1.json"
DEFAULT_ADMISSION_RECEIPT = (
    ROOT / "data/projects/open_model_data/admission/public_external_accepted_admission_receipt_v1.json"
)
DEFAULT_OPERATOR_PACKET = (
    ROOT / "data/projects/open_model_data/admission/public_external_operator_decision_packet_v1.json"
)
WORD_RE = re.compile(r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+(?:[’ʼ'][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+)*", re.UNICODE)
BYTE_TOKEN_RE = re.compile(r"^<0x[0-9A-F]{2}>$")
EMPTY_SHA256 = exporter.sha256_bytes(b"")


class ProductionError(ValueError):
    """A model-view production input or output violates the frozen contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProductionError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductionError(f"cannot read JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def validator(path: Path) -> Draft202012Validator:
    schemas = [read_json(candidate) for candidate in sorted(CONTRACTS.glob("*.schema.json"))]
    registry = Registry()
    for schema in schemas:
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(str(schema["$id"]), Resource.from_contents(schema))
    active = read_json(path)
    return Draft202012Validator(active, registry=registry, format_checker=FormatChecker())


def validate(value: Mapping[str, Any], active: Draft202012Validator, label: str) -> None:
    errors = sorted(active.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        location = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise ProductionError(f"{label} schema violation at {location}: {errors[0].message}")


def artifact(path: Path, *, records: int) -> dict[str, Any]:
    return {
        "bytes": path.stat().st_size,
        "records": records,
        "sha256": exporter.sha256_file(path),
    }


def receipt_artifact(path: Path) -> dict[str, Any]:
    return artifact(path, records=1)


def strict_artifact(value: Mapping[str, Any]) -> dict[str, Any]:
    """Project a richer upstream artifact receipt onto the strict binding."""
    return {
        "bytes": int(value["bytes"]),
        "records": int(value["records"]),
        "sha256": str(value["sha256"]),
    }


def sqlite_schema_sha256(path: Path) -> str:
    with closing(connect_read_only(path)) as connection:
        rows = connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name, tbl_name, sql"
        ).fetchall()
    return exporter.sha256_text(exporter.canonical_json([list(row) for row in rows]))


def verify_artifact(path: Path, expected: Mapping[str, Any], label: str) -> None:
    require(path.is_file(), f"{label} artifact is missing: {path}")
    require(path.stat().st_size == int(expected["bytes"]), f"{label} byte count mismatch")
    require(exporter.sha256_file(path) == expected["sha256"], f"{label} SHA-256 mismatch")


def policy_hash(label: str, material: Mapping[str, Any]) -> str:
    return exporter.sha256_text(exporter.canonical_json({"label": label, **material}))


@dataclass(frozen=True)
class MaskSignal:
    start: int
    end: int
    candidate_id: str
    category: str
    disposition: str
    evidence_grade: str
    language_identity: str
    representation: str
    discourse_role: str
    reason: str


REASON_BY_CATEGORY = {
    "historical_unresolved": "historical_or_heritage",
    "mixed_surzhyk_candidate": "russian_or_mixed_language",
    "modern_narration_interference": "russian_or_mixed_language",
    "ocr_or_encoding_candidate": "ocr_or_encoding",
    "other_language": "quoted_or_multilingual",
    "proper_name": "context_uncertain",
    "protected_authentic_ukrainian": "context_uncertain",
    "russian_quotation": "quoted_or_multilingual",
    "ukrainian_phonetic_russian": "russian_or_mixed_language",
    "uncertain": "context_uncertain",
    "valid_word_contact_candidate": "context_uncertain",
}
REASON_PRIORITY = {
    "russian_or_mixed_language": 0,
    "quoted_or_multilingual": 1,
    "historical_or_heritage": 2,
    "ocr_or_encoding": 3,
    "context_uncertain": 4,
}


def iter_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    raise ProductionError(f"blank JSONL row at {path}:{line_number}")
                value = json.loads(line)
                require(isinstance(value, dict), f"JSONL row is not an object at {path}:{line_number}")
                yield line_number, value
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductionError(f"cannot read JSONL {path}: {exc}") from exc


def load_wikipedia_silver(
    path: Path,
    *,
    expected: Mapping[str, Any],
) -> tuple[dict[int, list[MaskSignal]], collections.Counter[str]]:
    verify_artifact(path, expected, "silver")
    active = validator(SILVER_SCHEMA)
    masks: dict[int, list[MaskSignal]] = collections.defaultdict(list)
    counts: collections.Counter[str] = collections.Counter()
    for line_number, record in iter_jsonl(path):
        counts["input_silver_records"] += 1
        candidate = record.get("detector_candidate")
        if not isinstance(candidate, Mapping) or candidate.get("source_family") != "wikipedia":
            continue
        validate(record, active, f"Wikipedia silver line {line_number}")
        require(record["claim_boundary"]["human_reviewed"] is False, "silver record claims human review")
        require(
            record["claim_boundary"]["model_training_or_export_eligible"] is False,
            "silver record claims export eligibility",
        )
        raw_id = int(candidate["record_id"])
        span = candidate["span"]
        start, end = int(span["core_start_char"]), int(span["core_end_char"])
        classification = candidate["classification"]
        category = str(classification["category"])
        decision = record["decision"]
        reason = REASON_BY_CATEGORY[category]
        masks[raw_id].append(
            MaskSignal(
                start=start,
                end=end,
                candidate_id=str(record["candidate_id"]),
                category=category,
                disposition=str(decision["disposition"]),
                evidence_grade=str(decision["evidence_grade"]),
                language_identity=str(classification["language_identity"]),
                representation=str(classification["representation"]),
                discourse_role=str(classification["discourse_role"]),
                reason=reason,
            )
        )
        counts["wikipedia_silver_records"] += 1
        counts[f"category:{category}"] += 1
        counts[f"disposition:{decision['disposition']}"] += 1
        counts[f"evidence_grade:{decision['evidence_grade']}"] += 1
    require(counts["input_silver_records"] == int(expected["records"]), "silver record count mismatch")
    return dict(masks), counts


def _selected_signal(active: Iterable[MaskSignal]) -> MaskSignal:
    return min(
        active,
        key=lambda item: (
            REASON_PRIORITY[item.reason],
            item.category,
            item.evidence_grade,
            item.candidate_id,
        ),
    )


def operational_partition(text: str, signals: Sequence[MaskSignal]) -> list[dict[str, Any]]:
    for signal in signals:
        require(0 <= signal.start < signal.end <= len(text), "silver core span lies outside source text")
    boundaries = sorted({0, len(text), *(item.start for item in signals), *(item.end for item in signals)})
    spans: list[dict[str, Any]] = []
    for start, end in pairwise(boundaries):
        if start == end:
            continue
        active = [item for item in signals if item.start < end and start < item.end]
        if active:
            selected = _selected_signal(active)
            span = {
                "start": start,
                "end": end,
                "language_identity": selected.language_identity,
                "representation": selected.representation,
                "discourse_role": selected.discourse_role,
                "modern_loss_action": "mask_from_loss",
                "reason": selected.reason,
            }
        else:
            span = {
                "start": start,
                "end": end,
                "language_identity": "ukrainian",
                "representation": "standard_orthography",
                "discourse_role": "narration",
                "modern_loss_action": "retain",
                "reason": "other_reviewed",
            }
        if spans and all(spans[-1][key] == span[key] for key in span if key not in {"start", "end"}):
            spans[-1]["end"] = end
        else:
            spans.append(span)
    require(spans and spans[0]["start"] == 0 and spans[-1]["end"] == len(text), "partition is incomplete")
    return spans


def connect_read_only(path: Path) -> sqlite3.Connection:
    require(path.is_file(), f"source database is missing: {path}")
    connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def load_source_records(path: Path) -> list[dict[str, Any]]:
    schema, schema_hash = source_record_contract.load_schema()
    active = Draft202012Validator(schema, format_checker=FormatChecker())
    rows = source_record_contract.load_records(path)
    require(len(rows) == 1029, "source-record artifact must contain all 1,029 admitted Wikipedia rows")
    for row in rows:
        result = source_record_contract.validate_record(row, active, schema_hash)
        require(result["admitted"], f"source record is not admitted: {row.get('record_id')}")
    return rows


def signal_count_rows(
    masks: Mapping[int, Sequence[MaskSignal]],
    attribute: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = collections.defaultdict(
        lambda: {"records": set(), "spans": 0, "characters": 0}
    )
    for record_id, signals in masks.items():
        for signal in signals:
            code = str(getattr(signal, attribute))
            grouped[code]["records"].add(record_id)
            grouped[code]["spans"] += 1
            grouped[code]["characters"] += signal.end - signal.start
    return [
        {
            "code": code,
            "records": len(values["records"]),
            "spans": values["spans"],
            "characters": values["characters"],
        }
        for code, values in sorted(grouped.items())
    ]


def prepare_payloads(
    *,
    source_records_path: Path,
    sources_db: Path,
    detector_candidates_path: Path,
    silver_records_path: Path,
    output: Path,
    receipt_output: Path,
    detector_receipt_path: Path,
    silver_receipt_path: Path,
    admission_receipt_path: Path,
    operator_packet_path: Path,
) -> dict[str, Any]:
    detector_receipt = read_json(detector_receipt_path)
    silver_receipt = read_json(silver_receipt_path)
    admission_receipt = read_json(admission_receipt_path)
    operator_packet = read_json(operator_packet_path)
    detector_expected = detector_receipt["outputs"]["review_candidates"]
    silver_expected = silver_receipt["output"]
    verify_artifact(detector_candidates_path, detector_expected, "detector candidate")
    masks, silver_counts = load_wikipedia_silver(silver_records_path, expected=silver_expected)
    source_records = load_source_records(source_records_path)
    expected_source = admission_receipt["outputs"]["source_records"]
    verify_artifact(source_records_path, expected_source, "source-record")
    require(admission_receipt["dispositions"]["admitted"]["rows"] == 1029, "Wikipedia admission is incomplete")
    require(operator_packet["operator_decision_status"] == "accepted", "operator admission is not accepted")
    policy_material = {
        "admission_receipt_sha256": exporter.sha256_file(admission_receipt_path),
        "detector_receipt_sha256": exporter.sha256_file(detector_receipt_path),
        "silver_receipt_sha256": exporter.sha256_file(silver_receipt_path),
        "partition_policy": "detector-silver-operational-mask-v1",
    }
    origin_receipt = policy_hash("human-authored-wikipedia-origin-v1", policy_material)
    privacy_receipt = policy_hash("public-wikimedia-private-repository-data-screen-v1", policy_material)
    normalization_receipt = policy_hash("identity-normalization-v1", policy_material)
    language_receipt = policy_hash("nonhuman-operational-span-partition-v1", policy_material)
    writer = silver.AtomicJsonl.open(output)
    counts: collections.Counter[str] = collections.Counter()
    payload_active = validator(PAYLOAD_SCHEMA)
    try:
        with closing(connect_read_only(sources_db)) as connection:
            db_rows = list(connection.execute("SELECT id, text FROM wikipedia ORDER BY id"))
        require(len(db_rows) == len(source_records) == 1029, "Wikipedia/source-record cardinality mismatch")
        for db_row, source_record in zip(db_rows, source_records, strict=True):
            raw_id = int(db_row["id"])
            text = str(db_row["text"] or "")
            require(text, f"empty Wikipedia text: {raw_id}")
            require(exporter.sha256_text(text) == source_record["content"]["sha256"], "source content hash mismatch")
            spans = operational_partition(text, masks.get(raw_id, ()))
            masked_chars = sum(
                item["end"] - item["start"] for item in spans if item["modern_loss_action"] == "mask_from_loss"
            )
            counts["processed_records"] += 1
            counts["lexical_words"] += len(WORD_RE.findall(text))
            counts["masked_characters"] += masked_chars
            counts["retained_characters"] += len(text) - masked_chars
            counts["partition_spans"] += len(spans)
            counts["records_with_masks"] += int(masked_chars > 0)
            payload = {
                "schema_version": "foundry_source_payload_v1",
                "payload_id": f"payload.wikipedia.{raw_id:06d}",
                "source_record_id": source_record["record_id"],
                "source_content_sha256": source_record["content"]["sha256"],
                "derivation": {
                    "kind": "full_source",
                    "source_start_char": None,
                    "source_end_char": None,
                    "receipt_sha256": policy_hash(
                        "full-source-derivation-v1",
                        {"record_id": source_record["record_id"], "content_sha256": source_record["content"]["sha256"]},
                    ),
                },
                "text": text,
                "text_sha256": exporter.sha256_text(text),
                "origin": "human_authored",
                "origin_evidence": {
                    "status": "verified",
                    "method": "accepted article-level Ukrainian Wikipedia source record",
                    "receipt_sha256": origin_receipt,
                },
                "private_data": "clear",
                "private_data_review": {
                    "status": "complete",
                    "method": "public-source boundary; no private repository or collaborator payload",
                    "receipt_sha256": privacy_receipt,
                },
                "normalization": {
                    "status": "complete",
                    "version": "identity-utf8-v1",
                    "receipt_sha256": normalization_receipt,
                },
                "language_span_review": {
                    "status": "complete",
                    "reviewer_qualification": "non-human detector/silver operational partition; not linguistic gold",
                    "receipt_sha256": language_receipt,
                    "character_spans": spans,
                },
                "test_fixture": False,
            }
            validate(payload, payload_active, f"Wikipedia payload {raw_id}")
            exporter.validate_source_payload_semantics(payload)
            writer.write(payload)
        require(set(masks) <= {int(row["id"]) for row in db_rows}, "silver references unknown Wikipedia row")
        output_artifact = writer.finish()
        require(output_artifact["records"] == 1029, "payload output did not cover all admitted records")
        config_sha256 = policy_hash("source-payload-preparation-v1", policy_material)
        stratum = {
            "records": counts["processed_records"],
            "spans": silver_counts["wikipedia_silver_records"],
            "retained_characters": counts["retained_characters"],
            "masked_characters": counts["masked_characters"],
        }
        receipt = {
            "schema_version": "source_payload_preparation_receipt_v1",
            "preparation_id": "source-payload-preparation:" + config_sha256,
            "config_sha256": config_sha256,
            "inputs": {
                "admission_receipt": receipt_artifact(admission_receipt_path),
                "operator_packet": receipt_artifact(operator_packet_path),
                "source_records": expected_source,
                "detectors": {
                    "artifact": detector_expected,
                    "receipt": receipt_artifact(detector_receipt_path),
                },
                "silver": {
                    "artifact": silver_expected,
                    "receipt": receipt_artifact(silver_receipt_path),
                },
            },
            "source_database_snapshot": {
                "database_identity": "data.sources.db:wikipedia",
                "snapshot_sha256": exporter.sha256_file(sources_db),
                "schema_sha256": sqlite_schema_sha256(sources_db),
            },
            "policies": {
                "identity_normalization": "NFC; casefold only for identity comparison; preserve source character positions for payload derivation",
                "automated_span_partition": {
                    "execution": "automated detector and silver operational outputs",
                    "human_reviewed": False,
                    "linguistic_gold_claimed": False,
                    "partition_policy": "retain approved spans; mask loss for operationally excluded spans; exclude records when any exclusion policy requires it",
                },
                "evaluation_firewall": "NFKC; casefold; collapse whitespace; exact and near duplicate matches against held-out evaluation are excluded",
                "origin_evidence": "retain only source-record origin evidence state and receipt hash; unresolved origin is not promoted to verified",
                "private_data_evidence": "retain only source-record private-data review state and receipt hash; present or unknown is not admitted",
            },
            "output_payload": output_artifact,
            "counts": {
                "source_records_processed": counts["processed_records"],
                "candidate_records": len(masks),
                "candidate_spans": silver_counts["wikipedia_silver_records"],
                "retained_records": counts["processed_records"],
                "masked_records": counts["records_with_masks"],
                "excluded_records": 0,
                "retained_characters": counts["retained_characters"],
                "masked_characters": counts["masked_characters"],
                "excluded_characters": 0,
                "reason_counts": signal_count_rows(masks, "reason"),
                "category_counts": signal_count_rows(masks, "category"),
                "evidence_grade_counts": signal_count_rows(masks, "evidence_grade"),
            },
            "strata": {
                "source": [{"category": "wikipedia", **stratum}],
                "period": [{"category": "modern", **stratum}],
                "genre": [{"category": "encyclopedia", **stratum}],
                "register": [{"category": "reference", **stratum}],
            },
            "determinism": {
                "serialization": "UTF-8 canonical JSON with sorted keys and LF",
                "input_order": "ascending wikipedia.id with source-record identity and content hash revalidated",
                "candidate_order": "source record ID then source character start then source character end",
                "timestamps_omitted": True,
            },
            "safety": {
                "record_text_emitted": False,
                "span_text_emitted": False,
                "training_performed": False,
                "model_call_performed": False,
                "upload_performed": False,
                "publication_performed": False,
                "human_gold_created": False,
            },
        }
        validate(receipt, validator(PAYLOAD_RECEIPT_SCHEMA), "payload preparation receipt")
        receipt_temporary = silver.stage_json(receipt_output, receipt)
        silver.promote_outputs(((writer.temporary, output), (receipt_temporary, receipt_output)))
        return receipt
    except Exception:
        writer.abort()
        raise


def _merge_masks(masks: Sequence[Mapping[str, Any]], text_length: int) -> tuple[list[tuple[int, int]], int]:
    normalized: list[tuple[int, int]] = []
    for mask in masks:
        start, end = int(mask["start_char"]), int(mask["end_char"])
        require(0 <= start < end <= text_length, "character mask lies outside source text")
        normalized.append((start, end))
    normalized.sort()
    merged: list[tuple[int, int]] = []
    coalesced = 0
    for start, end in normalized:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            coalesced += 1
        else:
            merged.append((start, end))
    return merged, coalesced


def _percentiles(values: Sequence[float]) -> dict[str, float]:
    require(values, "cannot summarize an empty measurement")
    ordered = sorted(values)
    return {f"p{q}": ordered[math.ceil((q / 100) * len(ordered)) - 1] for q in (50, 90, 95, 99)}


def _histogram(values: Sequence[float]) -> list[dict[str, Any]]:
    require(values, "cannot histogram an empty measurement")
    maximum = max(values)
    boundaries = [float(index) for index in range(17)]
    if maximum >= 16:
        boundaries.append(float(math.floor(maximum) + 1))
    rows = [
        {
            "lower_inclusive": lower,
            "upper_exclusive": upper,
            "count": sum(lower <= value < upper for value in values),
        }
        for lower, upper in pairwise(boundaries)
        if any(lower <= value < upper for value in values)
    ]
    require(rows, "histogram has no populated bins")
    return rows


def _distribution(values: Sequence[float]) -> dict[str, Any]:
    require(values, "cannot summarize an empty distribution")
    return {
        "population": len(values),
        "sum": sum(values),
        "mean": sum(values) / len(values),
        "minimum": min(values),
        "maximum": max(values),
        "histogram": _histogram(values),
        "percentiles": _percentiles(values),
    }


def _assign_tokens_to_words(
    token_offsets: Sequence[tuple[int, int]],
    words: Sequence[re.Match[str]],
) -> tuple[list[int], collections.Counter[str]]:
    """Assign ordered tokenizer offsets to words in linear time.

    Tokens that include leading whitespace are assigned by maximum positive
    character overlap. Equal overlaps resolve to the earlier word.
    """
    assignments = [0] * len(words)
    counters: collections.Counter[str] = collections.Counter()
    word_cursor = 0
    previous_start = 0
    for token_start, token_end in token_offsets:
        require(token_start >= previous_start, "token offsets are not ordered")
        previous_start = token_start
        if token_start == token_end:
            counters["zero_width_tokens"] += 1
            continue
        while word_cursor < len(words) and words[word_cursor].end() <= token_start:
            word_cursor += 1
        best_overlap = 0
        best_index = -1
        overlap_count = 0
        index = word_cursor
        while index < len(words) and words[index].start() < token_end:
            overlap = max(
                0,
                min(token_end, words[index].end()) - max(token_start, words[index].start()),
            )
            if overlap:
                overlap_count += 1
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_index = index
            index += 1
        if best_index < 0:
            counters["unassigned_non_special_tokens"] += 1
            continue
        assignments[best_index] += 1
        counters["assigned_non_special_tokens"] += 1
        counters["tokens_overlapping_multiple_words"] += int(overlap_count > 1)
    return assignments, counters


def _project_masks_to_tokens(
    token_offsets: Sequence[tuple[int, int]],
    masks: Sequence[tuple[int, int]],
) -> collections.Counter[str]:
    """Project ordered half-open character masks onto ordered token offsets."""
    counters: collections.Counter[str] = collections.Counter()
    mask_cursor = 0
    previous_start = 0
    for token_start, token_end in token_offsets:
        require(token_start >= previous_start, "token offsets are not ordered")
        previous_start = token_start
        if token_start >= token_end:
            continue
        while mask_cursor < len(masks) and masks[mask_cursor][1] <= token_start:
            mask_cursor += 1
        overlap = 0
        index = mask_cursor
        while index < len(masks) and masks[index][0] < token_end:
            start, end = masks[index]
            overlap += max(0, min(token_end, end) - max(token_start, start))
            index += 1
        if overlap:
            counters["tokens_overlapping_masks"] += 1
            counters[
                "tokens_fully_masked" if overlap >= token_end - token_start else "tokens_partially_masked"
            ] += 1
    counters["zero_loss_tokens"] = counters["tokens_overlapping_masks"]
    return counters


def _verify_words_batched(
    words: Sequence[str],
    *,
    db_path: Path,
    batch_size: int = 5000,
) -> dict[str, list[dict[str, Any]]]:
    """Bound SQLite placeholders while preserving deterministic lookup order."""
    require(batch_size > 0, "VESUM batch size must be positive")
    results: dict[str, list[dict[str, Any]]] = {}
    for start in range(0, len(words), batch_size):
        batch = list(words[start : start + batch_size])
        results.update(verify_words(batch, db_path=db_path))
    return results


def tokenizer_diagnostics(
    *,
    faithful_view_path: Path,
    faithful_view_receipt_path: Path,
    modern_view_path: Path,
    modern_view_receipt_path: Path,
    tokenizer_path: Path,
    tokenizer_identifier: str,
    tokenizer_revision: str,
    vesum_db: Path,
    output: Path,
) -> dict[str, Any]:
    faithful_expected = read_json(faithful_view_receipt_path)["output"]
    modern_expected = read_json(modern_view_receipt_path)["output"]
    verify_artifact(faithful_view_path, faithful_expected, "faithful continued-pretraining view")
    verify_artifact(modern_view_path, modern_expected, "modern continued-pretraining view")
    require(faithful_expected["records"] == modern_expected["records"], "source-view cardinalities differ")
    tokenizer_json = tokenizer_path / "tokenizer.json"
    require(tokenizer_json.is_file(), "tokenizer.json is missing")
    tokenizer = Tokenizer.from_file(str(tokenizer_json))
    record_lengths = array.array("I")
    word_piece_lengths = array.array("I")
    characters_per_token: list[float] = []
    surface_counts: collections.Counter[str] = collections.Counter()
    surface_piece_sums: collections.Counter[str] = collections.Counter()
    surface_piece_histograms: dict[str, collections.Counter[int]] = collections.defaultdict(collections.Counter)
    counters: collections.Counter[str] = collections.Counter()
    view_active = validator(CONTRACTS / "continued_pretraining_view_v1.schema.json")
    mask_counts_per_record = array.array("I")
    for faithful_item, modern_item in zip_longest(
        iter_jsonl(faithful_view_path),
        iter_jsonl(modern_view_path),
    ):
        require(faithful_item is not None and modern_item is not None, "source-view lengths differ")
        faithful_line, faithful_row = faithful_item
        line_number, row = modern_item
        validate(faithful_row, view_active, f"faithful view line {faithful_line}")
        validate(row, view_active, f"continued-pretraining view line {line_number}")
        require(
            faithful_row["payload"]["text_sha256"] == row["payload"]["text_sha256"],
            "faithful and modern source texts differ",
        )
        text = row["payload"]["text"]
        encoding = tokenizer.encode(text)
        model_tokens = [
            (token_id, token, offset)
            for token_id, token, offset, special in zip(
                encoding.ids,
                encoding.tokens,
                encoding.offsets,
                encoding.special_tokens_mask,
                strict=True,
            )
            if not special
        ]
        record_lengths.append(len(model_tokens))
        counters["records"] += 1
        counters["characters"] += len(text)
        counters["non_special_tokens"] += len(model_tokens)
        counters["byte_fallback_tokens"] += sum(bool(BYTE_TOKEN_RE.fullmatch(token)) for _, token, _ in model_tokens)
        words = list(WORD_RE.finditer(text))
        counters["lexical_words"] += len(words)
        token_offsets = [offset for _token_id, _token, offset in model_tokens]
        assignments, assignment_counts = _assign_tokens_to_words(token_offsets, words)
        counters.update(assignment_counts)
        for word, pieces in zip(words, assignments, strict=True):
            normalized = unicodedata.normalize(
                "NFC",
                word.group(0).casefold().replace("'", "ʼ").replace("’", "ʼ"),
            )
            surface_counts[normalized] += 1
            surface_piece_sums[normalized] += pieces
            surface_piece_histograms[normalized][pieces] += 1
            word_piece_lengths.append(pieces)
        if model_tokens:
            characters_per_token.append(len(text) / len(model_tokens))
        merged_masks, coalesced = _merge_masks(row["payload"]["character_mask_spans"], len(text))
        counters["records_with_character_masks"] += int(bool(merged_masks))
        counters["raw_character_masks"] += len(row["payload"]["character_mask_spans"])
        counters["merged_character_masks"] += len(merged_masks)
        counters["coalesced_character_masks"] += coalesced
        mask_projection = _project_masks_to_tokens(token_offsets, merged_masks)
        counters.update(mask_projection)
        mask_counts_per_record.append(mask_projection["zero_loss_tokens"])
    require(counters["records"] == int(modern_expected["records"]), "tokenized view record count mismatch")
    analyses = _verify_words_batched(sorted(surface_counts), db_path=vesum_db)
    primary_groups: dict[tuple[str, str], dict[str, Any]] = collections.defaultdict(
        lambda: {"forms": set(), "occurrences": 0, "assigned_tokens": 0}
    )
    attested_occurrences = ambiguous_occurrences = 0
    attested_piece_total = 0
    ambiguity_counts = array.array("I")
    attested_piece_values = array.array("I")
    for surface in sorted(surface_counts):
        options = analyses.get(surface, [])
        if not options:
            continue
        distinct = sorted({(item["lemma"], item["pos"], item["tags"]) for item in options})
        ambiguity_counts.extend([len(distinct)] * surface_counts[surface])
        ambiguous_occurrences += surface_counts[surface] * int(len(distinct) > 1)
        lemma, pos, _tags = distinct[0]
        occurrences = surface_counts[surface]
        pieces = surface_piece_sums[surface]
        for piece_count, occurrence_count in surface_piece_histograms[surface].items():
            attested_piece_values.extend([piece_count] * occurrence_count)
        attested_occurrences += occurrences
        attested_piece_total += pieces
        group = primary_groups[(lemma, pos)]
        group["forms"].add(surface)
        group["occurrences"] += occurrences
        group["assigned_tokens"] += pieces
    paradigm_groups = [group for group in primary_groups.values() if len(group["forms"]) >= 2]
    paradigm_token_values = array.array(
        "I", (int(group["assigned_tokens"]) for group in primary_groups.values())
    )
    diagnostic_hash = policy_hash(
        "tokenizer-diagnostics-v1",
        {
            "faithful": faithful_expected["sha256"],
            "modern": modern_expected["sha256"],
            "tokenizer": exporter.sha256_file(tokenizer_json),
            "vesum": exporter.sha256_file(vesum_db),
        },
    )
    result = {
        "schema_version": "tokenizer_diagnostics_v1",
        "diagnostics_id": "tokenizer-diagnostics:" + diagnostic_hash,
        "tokenizer": {
            "identifier": tokenizer_identifier,
            "revision": tokenizer_revision,
            "tokenizer_json_sha256": exporter.sha256_file(tokenizer_json),
            "libraries": {
                "tokenizers": metadata.version("tokenizers"),
                "transformers": metadata.version("transformers"),
                "python": platform.python_version(),
            },
        },
        "vesum": {
            "snapshot_sha256": exporter.sha256_file(vesum_db),
            "interface": {
                "version": "scripts.verification.vesum.verify_words-v1",
                "lookup_policy": "NFC; Ukrainian casefold; exact surface lookup; report ambiguity without resolution",
            },
        },
        "source_views": {
            "faithful_continued_pretraining": {
                "artifact": strict_artifact(faithful_expected),
                "receipt": receipt_artifact(faithful_view_receipt_path),
            },
            "modern_continued_pretraining": {
                "artifact": strict_artifact(modern_expected),
                "receipt": receipt_artifact(modern_view_receipt_path),
            },
        },
        "metrics": {
            "non_special_token_count": counters["non_special_tokens"],
            "lexical_word_count": counters["lexical_words"],
            "assigned_token_count": counters["assigned_non_special_tokens"],
            "byte_fallback_token_count": counters["byte_fallback_tokens"],
            "record_length": _distribution(record_lengths),
            "lexical_fertility": _distribution(word_piece_lengths),
            "characters_per_token": _distribution(characters_per_token),
            "vesum_attestation": {
                "lexical_words_considered": counters["lexical_words"],
                "attested_lexical_words": attested_occurrences,
                "unattested_lexical_words": counters["lexical_words"] - attested_occurrences,
                "ambiguous_lexical_words": ambiguous_occurrences,
                "ambiguity_histogram": _histogram(ambiguity_counts),
            },
            "lexical_fragmentation_proxy": {
                "attested_lexical_words": attested_occurrences,
                "assigned_tokens": attested_piece_total,
                "tokens_per_attested_lexical_word": attested_piece_total / max(1, attested_occurrences),
                "histogram": _histogram(attested_piece_values),
                "percentiles": _percentiles(attested_piece_values),
            },
            "paradigm_fragmentation_proxy": {
                "attested_lemma_paradigms": len(primary_groups),
                "paradigms_with_multiple_forms": len(paradigm_groups),
                "assigned_tokens": int(sum(paradigm_token_values)),
                "tokens_per_paradigm": sum(paradigm_token_values) / max(1, len(paradigm_token_values)),
                "histogram": _histogram(paradigm_token_values),
                "percentiles": _percentiles(paradigm_token_values),
            },
            "mask_projection": {
                "counters": {
                    "records_considered": counters["records"],
                    "records_with_character_masks": counters["records_with_character_masks"],
                    "character_mask_spans": counters["raw_character_masks"],
                    "tokens_overlapping_masks": counters["tokens_overlapping_masks"],
                    "tokens_fully_masked": counters["tokens_fully_masked"],
                    "tokens_partially_masked": counters["tokens_partially_masked"],
                    "zero_loss_tokens": counters["zero_loss_tokens"],
                    "projection_failures": 0,
                },
                "histogram": _histogram(mask_counts_per_record),
                "percentiles": _percentiles(mask_counts_per_record),
            },
        },
        "determinism": {
            "serialization": "UTF-8 canonical JSON with sorted keys and LF",
            "view_order": "bound source-view artifact order",
            "tokenization": "exact tokenizer identifier, revision, tokenizer.json, and library versions recorded in this receipt",
            "word_segmentation": "Unicode letter runs after NFC; punctuation and whitespace excluded",
            "mask_projection": "token receives zero loss when its character interval overlaps a character_mask_span",
            "timestamps_omitted": True,
        },
        "safety": {
            "record_text_emitted": False,
            "surface_forms_emitted": False,
            "token_strings_emitted": False,
            "offset_arrays_emitted": False,
            "training_performed": False,
            "model_call_performed": False,
            "upload_performed": False,
            "publication_performed": False,
            "human_gold_created": False,
        },
    }
    validate(result, validator(TOKENIZER_RECEIPT_SCHEMA), "tokenizer diagnostics")
    temporary = silver.stage_json(output, result)
    silver.promote_outputs(((temporary, output),))
    return result


def _blocked_lane(total_records: int) -> dict[str, Any]:
    empty = {"records": 0, "bytes": 0, "sha256": EMPTY_SHA256}
    return {
        "state": "blocked",
        "eligible": 0,
        "emitted": 0,
        "blocked": total_records,
        "blocked_reasons": ["no_eligible_records"],
        "artifact": empty,
        "receipt": empty,
    }


def _recipe_binding(path: Path) -> dict[str, Any]:
    return {
        "artifact": receipt_artifact(path),
        "training_authorized": False,
        "model_call_performed": False,
        "training_performed": False,
    }


def assemble_production_receipt(
    *,
    source_records_path: Path,
    detector_candidates_path: Path,
    silver_records_path: Path,
    payload_path: Path,
    payload_receipt_path: Path,
    faithful_view_path: Path,
    faithful_view_receipt_path: Path,
    modern_view_path: Path,
    modern_view_receipt_path: Path,
    heldout_view_path: Path,
    heldout_view_receipt_path: Path,
    tokenizer_diagnostics_path: Path,
    faithful_recipe_path: Path,
    modern_recipe_path: Path,
    output: Path,
    detector_receipt_path: Path,
    silver_receipt_path: Path,
    admission_receipt_path: Path,
    operator_packet_path: Path,
) -> dict[str, Any]:
    detector_receipt = read_json(detector_receipt_path)
    silver_receipt = read_json(silver_receipt_path)
    admission_receipt = read_json(admission_receipt_path)
    payload_receipt = read_json(payload_receipt_path)
    faithful_receipt = read_json(faithful_view_receipt_path)
    modern_receipt = read_json(modern_view_receipt_path)
    heldout_receipt = read_json(heldout_view_receipt_path)
    tokenizer_receipt = read_json(tokenizer_diagnostics_path)
    detector_expected = detector_receipt["outputs"]["review_candidates"]
    silver_expected = silver_receipt["output"]
    source_expected = admission_receipt["outputs"]["source_records"]
    verify_artifact(detector_candidates_path, detector_expected, "detector candidate")
    verify_artifact(silver_records_path, silver_expected, "silver")
    verify_artifact(source_records_path, source_expected, "source record")
    for path, expected, label in (
        (payload_path, payload_receipt["output_payload"], "source payload"),
        (faithful_view_path, faithful_receipt["output"], "faithful view"),
        (modern_view_path, modern_receipt["output"], "modern view"),
        (heldout_view_path, heldout_receipt["output"], "heldout view"),
    ):
        verify_artifact(path, expected, label)
    validate(tokenizer_receipt, validator(TOKENIZER_RECEIPT_SCHEMA), "tokenizer diagnostics")
    require(faithful_receipt["view_kind"] == "continued_pretraining", "wrong faithful view kind")
    require(modern_receipt["view_kind"] == "continued_pretraining", "wrong modern view kind")
    require(heldout_receipt["view_kind"] == "heldout_evaluation", "wrong heldout view kind")
    require(
        faithful_receipt["counts"].get("exported_records")
        == modern_receipt["counts"].get("exported_records"),
        "continued-pretraining arm cardinalities differ",
    )
    faithful_records = int(faithful_receipt["output"]["records"])
    silver_records = int(silver_expected["records"])
    empty_recipe = {
        "artifact": {"records": 0, "bytes": 0, "sha256": EMPTY_SHA256},
        "training_authorized": False,
        "model_call_performed": False,
        "training_performed": False,
    }
    evaluation_blocked = sum(
        count
        for receipt in (faithful_receipt, modern_receipt)
        for code, count in receipt["counts"].items()
        if code.startswith("excluded_evaluation_contamination_")
    )
    duplicate_blocked = sum(
        count
        for code, count in faithful_receipt["counts"].items()
        if code.startswith("excluded_intra_view_duplicate_")
    )
    evidence_grade = silver_receipt["counts"]["by_evidence_grade"]
    payload_evidence_grade = payload_receipt["counts"]["evidence_grade_counts"]
    identity = {
        "admission": exporter.sha256_file(admission_receipt_path),
        "detector": detector_expected["sha256"],
        "silver": silver_expected["sha256"],
        "payload": payload_receipt["output_payload"]["sha256"],
        "faithful": faithful_receipt["output"]["sha256"],
        "modern": modern_receipt["output"]["sha256"],
        "heldout": heldout_receipt["output"]["sha256"],
        "tokenizer": exporter.sha256_file(tokenizer_diagnostics_path),
        "faithful_recipe": exporter.sha256_file(faithful_recipe_path),
        "modern_recipe": exporter.sha256_file(modern_recipe_path),
    }
    question_evidence = policy_hash(
        "wikipedia-modern-loss-mask-effect-v1",
        {
            "faithful": identity["faithful"],
            "modern": identity["modern"],
            "heldout": identity["heldout"],
            "tokenizer": identity["tokenizer"],
        },
    )
    receipt = {
        "schema_version": "model_ready_view_production_v1",
        "production_id": "model-ready-production:" + exporter.sha256_text(exporter.canonical_json(identity)),
        "admission": {
            "receipt": receipt_artifact(admission_receipt_path),
            "operator_packet": receipt_artifact(operator_packet_path),
            "source_records": source_expected,
        },
        "detectors": {
            "artifact": detector_expected,
            "receipt": receipt_artifact(detector_receipt_path),
        },
        "silver": {
            "artifact": silver_expected,
            "receipt": receipt_artifact(silver_receipt_path),
        },
        "source_payload": payload_receipt["output_payload"],
        "continued_pretraining_views": {
            "faithful": {
                "artifact": strict_artifact(faithful_receipt["output"]),
                "receipt": receipt_artifact(faithful_view_receipt_path),
            },
            "modern": {
                "artifact": strict_artifact(modern_receipt["output"]),
                "receipt": receipt_artifact(modern_view_receipt_path),
            },
        },
        "silver_lanes": {
            "correction_instruction": _blocked_lane(silver_records),
            "pairwise_preference": _blocked_lane(silver_records),
            "quality_filter": _blocked_lane(silver_records),
        },
        "tokenizer_diagnostics": receipt_artifact(tokenizer_diagnostics_path),
        "recipe_manifests": {
            "faithful_continued_pretraining": _recipe_binding(faithful_recipe_path),
            "modern_continued_pretraining": _recipe_binding(modern_recipe_path),
            "correction_instruction": empty_recipe,
            "pairwise_preference": empty_recipe,
            "quality_filter": empty_recipe,
        },
        "evaluation_firewall": {
            "state": "verified",
            "exclusion_registry": receipt_artifact(heldout_view_receipt_path),
            "heldout_evaluation_view": {
                "artifact": strict_artifact(heldout_receipt["output"]),
                "receipt": receipt_artifact(heldout_view_receipt_path),
            },
            "exact_overlap_count": 0,
            "near_overlap_count": 0,
            "blocked_records": evaluation_blocked,
            "policy": "NFKC; casefold; collapse whitespace; exact and near duplicate matches are blocked from non-evaluation views",
        },
        "deduplication": {
            "state": "verified",
            "artifact": receipt_artifact(faithful_view_receipt_path),
            "algorithm_version": "foundry-intra-view-dedup-v2",
            "normalization": "NFKC; casefold; collapse whitespace",
            "near_duplicate_threshold": 0.9,
            "input_records": int(faithful_receipt["counts"]["input_records"]),
            "accepted_records": faithful_records,
            "blocked_records": duplicate_blocked,
        },
        "stratified_counts": {
            "source": [{"category": "wikipedia", "records": faithful_records, "bytes": faithful_receipt["output"]["bytes"]}],
            "period": [{"category": "modern", "records": faithful_records, "bytes": faithful_receipt["output"]["bytes"]}],
            "genre": [{"category": "encyclopedia", "records": faithful_records, "bytes": faithful_receipt["output"]["bytes"]}],
            "register": [{"category": "reference", "records": faithful_records, "bytes": faithful_receipt["output"]["bytes"]}],
            "evidence_grade": [
                {"category": code, "records": int(count), "bytes": 0}
                for code, count in sorted(evidence_grade.items())
            ],
            "protected_unresolved": [
                {
                    "category": str(row["code"]),
                    "records": int(row["records"]),
                    "bytes": 0,
                }
                for row in payload_evidence_grade
            ],
        },
        "feasibility": {
            "decision": "REVISE",
            "prerequisites": [
                {"code": "real_cpt_input", "state": "satisfied", "evidence_sha256": identity["faithful"]},
                {"code": "evaluation_firewall", "state": "satisfied", "evidence_sha256": identity["heldout"]},
                {"code": "tokenizer_loss_mask_diagnostics", "state": "satisfied", "evidence_sha256": identity["tokenizer"]},
                {"code": "protected_no_change_inventory", "state": "satisfied", "evidence_sha256": identity["silver"]},
                {"code": "operator_compute_ceiling", "state": "pending", "evidence_sha256": None},
                {"code": "exact_treatment_preregistration", "state": "pending", "evidence_sha256": None},
            ],
            "blockers": [
                {"code": "operator_compute_ceiling", "state": "pending", "evidence_sha256": None},
                {"code": "exact_treatment_preregistration", "state": "pending", "evidence_sha256": None},
            ],
            "question": {
                "code": "wikipedia_modern_loss_mask_effect",
                "state": "open",
                "evidence_sha256": question_evidence,
            },
            "decision_changing_scope": {
                "additional_records": 0,
                "additional_bytes": 0,
                "additional_runtime_seconds": 0,
                "additional_cost_usd": 0,
                "condition_codes": ["operator_compute_ceiling", "exact_treatment_preregistration"],
            },
            "estimates": {
                "runtime_seconds": None,
                "storage_bytes": faithful_receipt["output"]["bytes"] + modern_receipt["output"]["bytes"],
                "cost_usd": None,
            },
            "operator_ceiling_state": "ceiling_not_declared",
        },
        "determinism": {
            "serialization": "UTF-8 canonical JSON with sorted keys and LF",
            "source_order": "validated ascending source payload ID",
            "view_order": "canonical upstream packet order; unique output record ID",
            "timestamps_omitted": True,
        },
        "safety": {
            "training_performed": False,
            "model_call_performed": False,
            "upload_performed": False,
            "publication_performed": False,
            "human_gold_created": False,
            "human_gold_used": False,
            "record_text_emitted": False,
        },
    }
    validate(receipt, validator(PRODUCTION_RECEIPT_SCHEMA), "model-ready production receipt")
    temporary = silver.stage_json(output, receipt)
    silver.promote_outputs(((temporary, output),))
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Produce real Ukrainian Foundry model-view evidence")
    subparsers = parser.add_subparsers(dest="command", required=True)
    payloads = subparsers.add_parser("prepare-payloads")
    payloads.add_argument("--source-records", type=Path, required=True)
    payloads.add_argument("--sources-db", type=Path, required=True)
    payloads.add_argument("--detector-candidates", type=Path, required=True)
    payloads.add_argument("--silver-records", type=Path, required=True)
    payloads.add_argument("--output", type=Path, required=True)
    payloads.add_argument("--receipt-output", type=Path, required=True)
    payloads.add_argument("--detector-receipt", type=Path, default=DEFAULT_DETECTOR_RECEIPT)
    payloads.add_argument("--silver-receipt", type=Path, default=DEFAULT_SILVER_RECEIPT)
    payloads.add_argument("--admission-receipt", type=Path, default=DEFAULT_ADMISSION_RECEIPT)
    payloads.add_argument("--operator-packet", type=Path, default=DEFAULT_OPERATOR_PACKET)
    diagnostics = subparsers.add_parser("tokenizer-diagnostics")
    diagnostics.add_argument("--faithful-view", type=Path, required=True)
    diagnostics.add_argument("--faithful-view-receipt", type=Path, required=True)
    diagnostics.add_argument("--modern-view", type=Path, required=True)
    diagnostics.add_argument("--modern-view-receipt", type=Path, required=True)
    diagnostics.add_argument("--tokenizer-path", type=Path, required=True)
    diagnostics.add_argument("--tokenizer-identifier", required=True)
    diagnostics.add_argument("--tokenizer-revision", required=True)
    diagnostics.add_argument("--vesum-db", type=Path, required=True)
    diagnostics.add_argument("--output", type=Path, required=True)
    production = subparsers.add_parser("assemble-production-receipt")
    production.add_argument("--source-records", type=Path, required=True)
    production.add_argument("--detector-candidates", type=Path, required=True)
    production.add_argument("--silver-records", type=Path, required=True)
    production.add_argument("--payload", type=Path, required=True)
    production.add_argument("--payload-receipt", type=Path, required=True)
    production.add_argument("--faithful-view", type=Path, required=True)
    production.add_argument("--faithful-view-receipt", type=Path, required=True)
    production.add_argument("--modern-view", type=Path, required=True)
    production.add_argument("--modern-view-receipt", type=Path, required=True)
    production.add_argument("--heldout-view", type=Path, required=True)
    production.add_argument("--heldout-view-receipt", type=Path, required=True)
    production.add_argument("--tokenizer-diagnostics", type=Path, required=True)
    production.add_argument("--faithful-recipe", type=Path, required=True)
    production.add_argument("--modern-recipe", type=Path, required=True)
    production.add_argument("--output", type=Path, required=True)
    production.add_argument("--detector-receipt", type=Path, default=DEFAULT_DETECTOR_RECEIPT)
    production.add_argument("--silver-receipt", type=Path, default=DEFAULT_SILVER_RECEIPT)
    production.add_argument("--admission-receipt", type=Path, default=DEFAULT_ADMISSION_RECEIPT)
    production.add_argument("--operator-packet", type=Path, default=DEFAULT_OPERATOR_PACKET)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare-payloads":
            result = prepare_payloads(
                source_records_path=args.source_records,
                sources_db=args.sources_db,
                detector_candidates_path=args.detector_candidates,
                silver_records_path=args.silver_records,
                output=args.output,
                receipt_output=args.receipt_output,
                detector_receipt_path=args.detector_receipt,
                silver_receipt_path=args.silver_receipt,
                admission_receipt_path=args.admission_receipt,
                operator_packet_path=args.operator_packet,
            )
        elif args.command == "tokenizer-diagnostics":
            result = tokenizer_diagnostics(
                faithful_view_path=args.faithful_view,
                faithful_view_receipt_path=args.faithful_view_receipt,
                modern_view_path=args.modern_view,
                modern_view_receipt_path=args.modern_view_receipt,
                tokenizer_path=args.tokenizer_path,
                tokenizer_identifier=args.tokenizer_identifier,
                tokenizer_revision=args.tokenizer_revision,
                vesum_db=args.vesum_db,
                output=args.output,
            )
        else:
            result = assemble_production_receipt(
                source_records_path=args.source_records,
                detector_candidates_path=args.detector_candidates,
                silver_records_path=args.silver_records,
                payload_path=args.payload,
                payload_receipt_path=args.payload_receipt,
                faithful_view_path=args.faithful_view,
                faithful_view_receipt_path=args.faithful_view_receipt,
                modern_view_path=args.modern_view,
                modern_view_receipt_path=args.modern_view_receipt,
                heldout_view_path=args.heldout_view,
                heldout_view_receipt_path=args.heldout_view_receipt,
                tokenizer_diagnostics_path=args.tokenizer_diagnostics,
                faithful_recipe_path=args.faithful_recipe,
                modern_recipe_path=args.modern_recipe,
                output=args.output,
                detector_receipt_path=args.detector_receipt,
                silver_receipt_path=args.silver_receipt,
                admission_receipt_path=args.admission_receipt,
                operator_packet_path=args.operator_packet,
            )
    except (ProductionError, exporter.ExportError, silver.SilverError) as exc:
        raise SystemExit(str(exc)) from exc
    print(exporter.canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
