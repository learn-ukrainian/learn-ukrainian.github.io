#!/usr/bin/env python3
"""Map source-verified Bukyvede glyphs to Unicode without admitting training data.

The adapter consumes the immutable Spas na Berestovi raw catalogue, revalidates
it against the canonical PDF, and writes a second private layer.  Raw text is
retained byte-for-byte in every output record.  Only five source-verified
Bukyvede patterns are mapped; any other private-use character fails closed.

This step is a technical encoding adapter, not semantic gold.  The output
remains ineligible for training until inscription readings are separated from
the editor's prose and independently reviewed.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data.phase3_linguistic_representation import canonical_json, sha256_value
from scripts.projects.open_model_data.phase3_spas_catalog_materialization import (
    COLLECTION_ID,
    EXPECTED_CATALOG_RECORDS,
    EXPECTED_PRIVATE_USE_COUNTS,
    SOURCE_PDF_SHA256,
    SpasCatalogMaterializationError,
    _inside_git_checkout,
    file_sha256,
    validate_existing_materialization,
)
from scripts.projects.open_model_data.phase3_spas_catalog_materialization import (
    OUTPUT_FILENAME as RAW_OUTPUT_FILENAME,
)
from scripts.projects.open_model_data.phase3_spas_catalog_materialization import (
    RECEIPT_FILENAME as RAW_RECEIPT_FILENAME,
)

ROOT = Path(__file__).resolve().parents[3]
RECEIPT_SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_spas_glyph_adapter_receipt_v1.schema.json"

SCHEMA_VERSION = "phase3_spas_glyph_adapter_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_spas_glyph_adapter_v1"
OUTPUT_FILENAME = "spas-na-berestovi-unicode-adapter-v1.jsonl.gz"
RECEIPT_FILENAME = "glyph-adapter-receipt-v1.json"
MAPPING_EVIDENCE_FILENAME = "bukyvede-glyph-mapping-evidence-v1.json"

EXPECTED_RAW_OUTPUT_SHA256 = "974f05399d69faadc2fd7ffe96a06e0e2d1d409464a1eb1de9962bf772fabd05"
EXPECTED_RAW_RECEIPT_FILE_SHA256 = "fe14a7c0dfb7fcb1304cf5ad360cba11135bcc42bb4cd78ef314773e948a492b"
EXPECTED_RAW_RECEIPT_SHA256 = "a2521b1026878520e9180a04a11f68a683845cf214b44d3794c8c761c309b7d3"
EXPECTED_MAPPING_EVIDENCE_SHA256 = "e91c0476c5a712ad4d050524c2fff5ea68b9601ed8702c0ca3a961ce6fef5552"
EXPECTED_FONT_SHA256 = "7a8621566ed351efdd44c97ba7730c3e5566148c79a972be215b887991e6d7c9"
EXPECTED_TO_UNICODE_SHA256 = "47d569411ebc3ab0f2ebba34f8c7f291afdd089d3a658ff2f1ab609e4f16ff21"
EXPECTED_RAW_RECORD_CHARACTERS = 228066
EXPECTED_NORMALIZED_CHARACTERS = 228036
EXPECTED_RECORDS_WITH_MAPPINGS = 39
EXPECTED_MAPPING_EVENTS = 57


class SpasGlyphAdapterError(ValueError):
    """A provenance, mapping, or immutable-output invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SpasGlyphAdapterError(message)


def _codepoints(text: str) -> list[str]:
    return [f"U+{ord(char):04X}" for char in text]


def _private_use_counts(text: str) -> dict[str, int]:
    counts = Counter(f"U+{ord(char):04X}" for char in text if 0xE000 <= ord(char) <= 0xF8FF)
    return dict(sorted(counts.items()))


@dataclass(frozen=True)
class MappingRule:
    mapping_id: str
    raw: str
    normalized: str
    unicode_name: str
    expected_occurrences: int

    def receipt_entry(self) -> dict[str, Any]:
        return {
            "mapping_id": self.mapping_id,
            "raw_pattern": _codepoints(self.raw),
            "normalized_pattern": _codepoints(self.normalized),
            "unicode_name": self.unicode_name,
            "expected_occurrences": self.expected_occurrences,
        }


MAPPING_RULES = (
    MappingRule(
        "capital_iotation_plus_a_to_iotified_a",
        "\ue02e\u0410",
        "\ua656",
        "CYRILLIC CAPITAL LETTER IOTIFIED A",
        3,
    ),
    MappingRule(
        "small_iotation_plus_a_to_iotified_a",
        "\ue02f\u0430",
        "\ua657",
        "CYRILLIC SMALL LETTER IOTIFIED A",
        27,
    ),
    MappingRule(
        "titolongcap_to_combining_cyrillic_titlo",
        "\ue002",
        "\u0483",
        "COMBINING CYRILLIC TITLO",
        13,
    ),
    MappingRule(
        "cyfitamidbar_to_cyrillic_capital_fita",
        "\ue026",
        "\u0472",
        "CYRILLIC CAPITAL LETTER FITA",
        4,
    ),
    MappingRule(
        "lowercase_fita_to_cyrillic_small_fita",
        "\ue027",
        "\u0473",
        "CYRILLIC SMALL LETTER FITA",
        10,
    ),
)
RULE_BY_ID = {rule.mapping_id: rule for rule in MAPPING_RULES}
EXPECTED_MAPPING_COUNTS = {rule.mapping_id: rule.expected_occurrences for rule in MAPPING_RULES}


def apply_bukyvede_mapping(raw_text: str) -> tuple[str, list[dict[str, Any]]]:
    """Apply only the frozen longest-first mapping contract."""
    require(isinstance(raw_text, str) and raw_text != "", "raw text must be nonempty")
    normalized_parts: list[str] = []
    events: list[dict[str, Any]] = []
    raw_offset = 0
    normalized_offset = 0
    while raw_offset < len(raw_text):
        rule = next((candidate for candidate in MAPPING_RULES if raw_text.startswith(candidate.raw, raw_offset)), None)
        if rule is None:
            char = raw_text[raw_offset]
            require(
                not 0xE000 <= ord(char) <= 0xF8FF,
                f"unmapped private-use character at raw offset {raw_offset}: U+{ord(char):04X}",
            )
            normalized_parts.append(char)
            raw_offset += 1
            normalized_offset += 1
            continue

        raw_end = raw_offset + len(rule.raw)
        normalized_end = normalized_offset + len(rule.normalized)
        events.append(
            {
                "mapping_id": rule.mapping_id,
                "raw_start_char": raw_offset,
                "raw_end_char": raw_end,
                "raw_pattern": _codepoints(rule.raw),
                "raw_pattern_sha256": hashlib.sha256(rule.raw.encode("utf-8")).hexdigest(),
                "normalized_start_char": normalized_offset,
                "normalized_end_char": normalized_end,
                "normalized_pattern": _codepoints(rule.normalized),
                "normalized_pattern_sha256": hashlib.sha256(rule.normalized.encode("utf-8")).hexdigest(),
            }
        )
        normalized_parts.append(rule.normalized)
        raw_offset = raw_end
        normalized_offset = normalized_end

    normalized_text = "".join(normalized_parts)
    require(_private_use_counts(normalized_text) == {}, "normalized text still contains private-use characters")
    return normalized_text, events


def reconstruct_raw_text(normalized_text: str, events: Sequence[Mapping[str, Any]]) -> str:
    """Reverse the adapter using normalized offsets and frozen event patterns."""
    parts: list[str] = []
    cursor = 0
    previous_raw_end = 0
    for event in events:
        require(
            set(event)
            == {
                "mapping_id",
                "raw_start_char",
                "raw_end_char",
                "raw_pattern",
                "raw_pattern_sha256",
                "normalized_start_char",
                "normalized_end_char",
                "normalized_pattern",
                "normalized_pattern_sha256",
            },
            "mapping event fields drift",
        )
        mapping_id = event["mapping_id"]
        require(mapping_id in RULE_BY_ID, "mapping event id drift")
        rule = RULE_BY_ID[mapping_id]
        start = event["normalized_start_char"]
        end = event["normalized_end_char"]
        require(isinstance(start, int) and isinstance(end, int), "mapping event offsets must be integers")
        require(cursor <= start < end <= len(normalized_text), "normalized mapping event offsets drift")
        expected_raw_start = previous_raw_end + (start - cursor)
        require(event["raw_start_char"] == expected_raw_start, "raw mapping event start offset drift")
        require(event["raw_end_char"] - event["raw_start_char"] == len(rule.raw), "raw mapping width drift")
        require(event["raw_pattern"] == _codepoints(rule.raw), "raw mapping pattern drift")
        require(event["normalized_pattern"] == _codepoints(rule.normalized), "normalized mapping pattern drift")
        require(normalized_text[start:end] == rule.normalized, "normalized mapping text drift")
        require(
            event["raw_pattern_sha256"] == hashlib.sha256(rule.raw.encode("utf-8")).hexdigest(),
            "raw mapping pattern hash drift",
        )
        require(
            event["normalized_pattern_sha256"] == hashlib.sha256(rule.normalized.encode("utf-8")).hexdigest(),
            "normalized mapping pattern hash drift",
        )
        parts.append(normalized_text[cursor:start])
        parts.append(rule.raw)
        cursor = end
        previous_raw_end = event["raw_end_char"]
    parts.append(normalized_text[cursor:])
    return "".join(parts)


def build_normalized_record(raw_record: Mapping[str, Any], *, upstream_raw_sha256: str) -> dict[str, Any]:
    """Build one reversible private record from one validated raw record."""
    required = {
        "record_id",
        "collection_id",
        "graffito_number",
        "source_pdf_sha256",
        "source_text",
        "source_text_sha256",
        "private_use_codepoint_counts",
    }
    require(required <= set(raw_record), "raw record lacks required adapter fields")
    raw_text = raw_record["source_text"]
    require(isinstance(raw_text, str) and raw_text != "", "raw record source text must be nonempty")
    require(raw_record["collection_id"] == COLLECTION_ID, "raw record collection drift")
    require(raw_record["source_pdf_sha256"] == SOURCE_PDF_SHA256, "raw record PDF identity drift")
    require(
        raw_record["source_text_sha256"] == hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
        "raw record source text hash drift",
    )
    require(
        raw_record["private_use_codepoint_counts"] == _private_use_counts(raw_text),
        "raw record private-use counts drift",
    )

    normalized_text, events = apply_bukyvede_mapping(raw_text)
    reconstructed = reconstruct_raw_text(normalized_text, events)
    require(reconstructed == raw_text, "normalized record does not reverse to exact raw text")
    counts = Counter(event["mapping_id"] for event in events)
    return {
        "schema_version": "phase3_spas_glyph_normalized_record_v1",
        "record_id": f"{raw_record['record_id']}:unicode-v1",
        "source_record_id": raw_record["record_id"],
        "collection_id": COLLECTION_ID,
        "graffito_number": raw_record["graffito_number"],
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "upstream_raw_catalog_sha256": upstream_raw_sha256,
        "raw_source_text": raw_text,
        "raw_source_text_sha256": raw_record["source_text_sha256"],
        "normalized_text": normalized_text,
        "normalized_text_sha256": hashlib.sha256(normalized_text.encode("utf-8")).hexdigest(),
        "raw_offset_basis": "unicode_code_points_in_pypdf_native_page_text",
        "normalized_offset_basis": "unicode_code_points_after_bukyvede_adapter_v1",
        "mapping_events": events,
        "mapping_event_counts": dict(sorted(counts.items())),
        "input_private_use_codepoint_counts": raw_record["private_use_codepoint_counts"],
        "output_private_use_codepoint_counts": {},
        "mapping_status": "source_verified_bukyvede_glyph_adapter",
        "raw_source_preserved": True,
        "commentary_and_inscription_layers_separated": False,
        "training_eligible": False,
        "modern_correction_eligible": False,
        "inferred_character_repairs": False,
        "provider_calls": False,
    }


def _load_json_object(path: Path, *, description: str) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), f"{description} is missing or unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpasGlyphAdapterError(f"cannot read {description}: {exc}") from exc
    require(isinstance(value, dict), f"{description} must be an object")
    return value


def validate_mapping_evidence(path: Path, *, expected_sha256: str | None = None) -> None:
    """Validate the exact text-free evidence note and its frozen mapping contract."""
    if expected_sha256 is None:
        expected_sha256 = EXPECTED_MAPPING_EVIDENCE_SHA256
    require(path.name == MAPPING_EVIDENCE_FILENAME, "mapping evidence filename drift")
    require(file_sha256(path) == expected_sha256, "mapping evidence SHA-256 drift")
    evidence = _load_json_object(path, description="mapping evidence")
    require(file_sha256(path) == expected_sha256, "mapping evidence changed while validating")
    require(
        evidence.get("schema_version") == "private_phase3_spas_bukyvede_glyph_mapping_evidence_v1",
        "mapping evidence schema drift",
    )
    require(evidence.get("text_free") is True, "mapping evidence must be text-free")
    source = evidence.get("source", {})
    require(source.get("collection_id") == COLLECTION_ID, "mapping evidence collection drift")
    require(source.get("source_pdf_sha256") == SOURCE_PDF_SHA256, "mapping evidence PDF identity drift")
    require(source.get("catalog_records") == EXPECTED_CATALOG_RECORDS, "mapping evidence record denominator drift")
    require(source.get("raw_catalog_jsonl_sha256") == EXPECTED_RAW_OUTPUT_SHA256, "mapping evidence raw output drift")
    require(
        source.get("raw_materialization_receipt_sha256") == EXPECTED_RAW_RECEIPT_SHA256,
        "mapping evidence raw receipt drift",
    )
    font = evidence.get("embedded_font", {})
    require(font.get("font_sha256") == EXPECTED_FONT_SHA256, "mapping evidence font identity drift")
    require(font.get("to_unicode_sha256") == EXPECTED_TO_UNICODE_SHA256, "mapping evidence ToUnicode identity drift")
    candidates = evidence.get("source_verified_mapping_candidates")
    require(
        isinstance(candidates, list) and len(candidates) == len(MAPPING_RULES), "mapping candidate denominator drift"
    )
    observed = {
        (tuple(candidate.get("raw_pattern", [])), tuple(candidate.get("normalized_pattern", []))): candidate.get(
            "occurrences"
        )
        for candidate in candidates
        if isinstance(candidate, dict)
    }
    expected = {
        (tuple(_codepoints(rule.raw)), tuple(_codepoints(rule.normalized))): rule.expected_occurrences
        for rule in MAPPING_RULES
    }
    require(observed == expected, "mapping evidence rule contract drift")
    denominator = evidence.get("denominator_checks", {})
    require(
        denominator.get("private_use_occurrences") == EXPECTED_MAPPING_EVENTS, "mapping evidence PUA denominator drift"
    )
    require(
        denominator.get("raw_pattern_occurrence_sum") == EXPECTED_MAPPING_EVENTS,
        "mapping evidence pattern denominator drift",
    )
    require(denominator.get("unexpected_private_use_codepoints") == 0, "mapping evidence contains unexpected PUA")
    safeguards = evidence.get("safeguards", {})
    require(
        safeguards.get("mapping_is_deterministic_source_adapter_not_semantic_gold") is True,
        "mapping evidence authority drift",
    )
    require(safeguards.get("training_eligible") is False, "mapping evidence cannot authorize training")
    require(safeguards.get("phase4_authorized") is False, "mapping evidence cannot authorize Phase 4")


def _write_jsonl_gzip(path: Path, records: Sequence[Mapping[str, Any]]) -> tuple[int, int, str]:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        with (
            temporary.open("wb") as raw_handle,
            gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle,
        ):
            for record in records:
                gzip_handle.write(canonical_json(record).encode("utf-8") + b"\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return len(records), path.stat().st_size, file_sha256(path)


def _receipt_with_hash(body: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(body)
    receipt["receipt_sha256"] = sha256_value(body)
    return receipt


def _validate_receipt(receipt: Mapping[str, Any]) -> None:
    try:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpasGlyphAdapterError(f"cannot read receipt schema: {RECEIPT_SCHEMA_PATH}") from exc
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda item: list(item.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "receipt"
        raise SpasGlyphAdapterError(f"receipt schema violation at {location}: {errors[0].message}")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    require(receipt["receipt_sha256"] == sha256_value(body), "receipt self-hash drift")
    denominator = receipt["denominator"]
    require(
        denominator["input_records"] == denominator["output_records"] == receipt["output"]["records"],
        "receipt record denominator drift",
    )
    require(
        denominator["input_private_use_occurrences"]
        == denominator["mapping_events"]
        == sum(receipt["mapping_contract"]["observed_counts"].values()),
        "receipt mapping denominator drift",
    )
    require(denominator["output_private_use_occurrences"] == 0, "receipt output PUA denominator drift")
    require(
        denominator["input_characters"] - denominator["output_characters"] == 30,
        "receipt character-width delta drift",
    )
    require(
        receipt["mapping_contract"]["rules"] == [rule.receipt_entry() for rule in MAPPING_RULES],
        "receipt mapping-rule contract drift",
    )


def _write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    _validate_receipt(receipt)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_raw_records(path: Path) -> list[dict[str, Any]]:
    require(path.is_file() and not path.is_symlink(), "raw catalogue JSONL is missing or unsafe")
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            records = [json.loads(line) for line in handle]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SpasGlyphAdapterError(f"cannot read raw catalogue JSONL: {exc}") from exc
    require(all(isinstance(record, dict) for record in records), "raw catalogue rows must be objects")
    return records


def _load_output_records(path: Path) -> list[dict[str, Any]]:
    require(path.is_file() and not path.is_symlink(), "glyph adapter JSONL is missing or unsafe")
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            records = [json.loads(line) for line in handle]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SpasGlyphAdapterError(f"cannot read glyph adapter JSONL: {exc}") from exc
    require(all(isinstance(record, dict) for record in records), "glyph adapter rows must be objects")
    return records


def _validate_normalized_record(record: Mapping[str, Any], raw_record: Mapping[str, Any]) -> None:
    expected = build_normalized_record(raw_record, upstream_raw_sha256=EXPECTED_RAW_OUTPUT_SHA256)
    require(record == expected, f"normalized record {raw_record['graffito_number']} deterministic replay drift")
    require(
        reconstruct_raw_text(record["normalized_text"], record["mapping_events"]) == record["raw_source_text"],
        "raw reconstruction drift",
    )


def _remove_staging_dir(staging_dir: Path) -> None:
    for filename in (OUTPUT_FILENAME, RECEIPT_FILENAME):
        candidate = staging_dir / filename
        if candidate.is_file() or candidate.is_symlink():
            candidate.unlink()
    if staging_dir.exists():
        staging_dir.rmdir()


def adapt_spas_glyphs(
    *,
    pdf_path: Path,
    raw_catalog_dir: Path,
    mapping_evidence_path: Path,
    private_output_dir: Path,
    expected_raw_output_sha256: str = EXPECTED_RAW_OUTPUT_SHA256,
    expected_raw_receipt_file_sha256: str = EXPECTED_RAW_RECEIPT_FILE_SHA256,
    expected_raw_receipt_sha256: str = EXPECTED_RAW_RECEIPT_SHA256,
    expected_mapping_evidence_sha256: str = EXPECTED_MAPPING_EVIDENCE_SHA256,
    expected_records: int = EXPECTED_CATALOG_RECORDS,
    expected_raw_characters: int = EXPECTED_RAW_RECORD_CHARACTERS,
    expected_normalized_characters: int = EXPECTED_NORMALIZED_CHARACTERS,
    expected_records_with_mappings: int = EXPECTED_RECORDS_WITH_MAPPINGS,
    expected_mapping_events: int = EXPECTED_MAPPING_EVENTS,
) -> dict[str, Any]:
    """Write an immutable private Unicode-adapter layer and text-free receipt."""
    resolved_output = private_output_dir.resolve()
    require(not _inside_git_checkout(resolved_output), "private text output cannot be inside a Git checkout")
    require(not private_output_dir.exists(), "immutable private output directory already exists")
    require(private_output_dir.parent.is_dir(), "private output parent directory does not exist")
    require(
        mapping_evidence_path.parent.resolve() == raw_catalog_dir.resolve(),
        "mapping evidence must accompany raw catalogue",
    )

    upstream = validate_existing_materialization(pdf_path=pdf_path, private_output_dir=raw_catalog_dir)
    require(upstream["source_pdf_sha256"] == SOURCE_PDF_SHA256, "upstream PDF identity drift")
    require(upstream["records"] == expected_records, "upstream record denominator drift")
    require(upstream["private_jsonl_sha256"] == expected_raw_output_sha256, "upstream raw output identity drift")
    require(upstream["receipt_sha256"] == expected_raw_receipt_sha256, "upstream raw receipt identity drift")
    require(upstream["training_eligible"] is False, "upstream raw layer cannot authorize training")

    raw_path = raw_catalog_dir / RAW_OUTPUT_FILENAME
    raw_receipt_path = raw_catalog_dir / RAW_RECEIPT_FILENAME
    require(file_sha256(raw_path) == expected_raw_output_sha256, "raw catalogue SHA-256 drift")
    require(file_sha256(raw_receipt_path) == expected_raw_receipt_file_sha256, "raw receipt file SHA-256 drift")
    validate_mapping_evidence(mapping_evidence_path, expected_sha256=expected_mapping_evidence_sha256)
    raw_records = _load_raw_records(raw_path)
    require(file_sha256(raw_path) == expected_raw_output_sha256, "raw catalogue changed while adapting")
    require(len(raw_records) == expected_records, "raw catalogue record denominator drift")
    require(
        [record.get("graffito_number") for record in raw_records] == list(range(1, expected_records + 1)),
        "raw catalogue sequence drift",
    )

    normalized_records = [
        build_normalized_record(record, upstream_raw_sha256=expected_raw_output_sha256) for record in raw_records
    ]
    raw_characters = sum(len(record["raw_source_text"]) for record in normalized_records)
    normalized_characters = sum(len(record["normalized_text"]) for record in normalized_records)
    records_with_mappings = sum(bool(record["mapping_events"]) for record in normalized_records)
    mapping_events = sum(len(record["mapping_events"]) for record in normalized_records)
    mapping_counts: Counter[str] = Counter()
    input_pua: Counter[str] = Counter()
    output_pua: Counter[str] = Counter()
    for record in normalized_records:
        mapping_counts.update(record["mapping_event_counts"])
        input_pua.update(record["input_private_use_codepoint_counts"])
        output_pua.update(record["output_private_use_codepoint_counts"])
    require(raw_characters == expected_raw_characters, "raw record character denominator drift")
    require(normalized_characters == expected_normalized_characters, "normalized character denominator drift")
    require(records_with_mappings == expected_records_with_mappings, "mapped-record denominator drift")
    require(mapping_events == expected_mapping_events, "mapping-event denominator drift")
    require(dict(sorted(mapping_counts.items())) == EXPECTED_MAPPING_COUNTS, "mapping-rule counts drift")
    require(dict(sorted(input_pua.items())) == EXPECTED_PRIVATE_USE_COUNTS, "input private-use counts drift")
    require(not output_pua, "output contains private-use characters")

    identity_manifest = [
        {
            "graffito_number": record["graffito_number"],
            "raw_source_text_sha256": record["raw_source_text_sha256"],
            "normalized_text_sha256": record["normalized_text_sha256"],
            "mapping_event_counts": record["mapping_event_counts"],
        }
        for record in normalized_records
    ]
    staging_dir = Path(tempfile.mkdtemp(prefix=f".{private_output_dir.name}.staging-", dir=private_output_dir.parent))
    try:
        output_path = staging_dir / OUTPUT_FILENAME
        output_records, output_bytes, output_sha256 = _write_jsonl_gzip(output_path, normalized_records)
        body: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "implementation_version": IMPLEMENTATION_VERSION,
            "mode": "source_verified_bukyvede_to_unicode_adapter",
            "text_free": True,
            "inputs": {
                "collection_id": COLLECTION_ID,
                "source_pdf_sha256": SOURCE_PDF_SHA256,
                "raw_catalog_filename": RAW_OUTPUT_FILENAME,
                "raw_catalog_sha256": expected_raw_output_sha256,
                "raw_materialization_receipt_filename": RAW_RECEIPT_FILENAME,
                "raw_materialization_receipt_file_sha256": expected_raw_receipt_file_sha256,
                "raw_materialization_receipt_sha256": expected_raw_receipt_sha256,
                "mapping_evidence_filename": MAPPING_EVIDENCE_FILENAME,
                "mapping_evidence_sha256": expected_mapping_evidence_sha256,
                "embedded_font_sha256": EXPECTED_FONT_SHA256,
                "to_unicode_cmap_sha256": EXPECTED_TO_UNICODE_SHA256,
                "implementation_sha256": file_sha256(Path(__file__)),
                "receipt_schema_sha256": file_sha256(RECEIPT_SCHEMA_PATH),
            },
            "mapping_contract": {
                "rules": [rule.receipt_entry() for rule in MAPPING_RULES],
                "observed_counts": dict(sorted(mapping_counts.items())),
                "longest_match_first": True,
                "offset_basis": "unicode_code_points",
                "source_adapter_not_semantic_gold": True,
            },
            "denominator": {
                "input_records": len(raw_records),
                "output_records": output_records,
                "input_characters": raw_characters,
                "output_characters": normalized_characters,
                "records_with_mappings": records_with_mappings,
                "mapping_events": mapping_events,
                "input_private_use_occurrences": sum(input_pua.values()),
                "output_private_use_occurrences": sum(output_pua.values()),
                "raw_reconstruction_failures": 0,
            },
            "output": {
                "filename": OUTPUT_FILENAME,
                "records": output_records,
                "bytes": output_bytes,
                "sha256": output_sha256,
                "record_identity_manifest_sha256": sha256_value(identity_manifest),
            },
            "rights_and_scope": {
                "inherits_upstream_accepted_operational_risk": True,
                "attribution_and_field_level_removal_preserved": True,
                "binary_media_reuse_authorized": False,
                "full_publication_training_export_authorized": False,
                "adapt_on_substantiated_rights_notice": True,
            },
            "safeguards": {
                "raw_source_preserved_in_every_record": True,
                "historical_forms_protected": True,
                "deterministic_mapping_only": True,
                "commentary_and_inscription_layers_separated": False,
                "training_eligible": False,
                "modern_correction_eligible": False,
                "semantic_gold": False,
                "provider_calls": False,
                "phase4_authorized": False,
            },
            "residuals": {
                "glyph_mapping_pending": False,
                "commentary_transcription_separation_pending": True,
                "qualified_historical_review_pending": True,
                "lavra_cave_corpus_gap_closed": False,
            },
        }
        receipt = _receipt_with_hash(body)
        _write_receipt(staging_dir / RECEIPT_FILENAME, receipt)
        require(not private_output_dir.exists(), "immutable private output directory appeared during publication")
        os.replace(staging_dir, private_output_dir)
        return receipt
    finally:
        _remove_staging_dir(staging_dir)


def validate_existing_glyph_adapter(
    *,
    pdf_path: Path,
    raw_catalog_dir: Path,
    mapping_evidence_path: Path,
    private_output_dir: Path,
) -> dict[str, Any]:
    """Rebind an existing adapter output to the PDF, raw layer, and mapping note."""
    receipt_path = private_output_dir / RECEIPT_FILENAME
    output_path = private_output_dir / OUTPUT_FILENAME
    receipt = _load_json_object(receipt_path, description="glyph adapter receipt")
    _validate_receipt(receipt)
    inputs = receipt["inputs"]
    denominator = receipt["denominator"]
    require(inputs["collection_id"] == COLLECTION_ID, "receipt collection identity drift")
    require(inputs["source_pdf_sha256"] == SOURCE_PDF_SHA256, "receipt PDF identity drift")
    require(inputs["raw_catalog_sha256"] == EXPECTED_RAW_OUTPUT_SHA256, "receipt raw catalogue identity drift")
    require(
        inputs["raw_materialization_receipt_file_sha256"] == EXPECTED_RAW_RECEIPT_FILE_SHA256,
        "receipt raw receipt file identity drift",
    )
    require(
        inputs["raw_materialization_receipt_sha256"] == EXPECTED_RAW_RECEIPT_SHA256, "receipt upstream identity drift"
    )
    require(
        inputs["mapping_evidence_sha256"] == EXPECTED_MAPPING_EVIDENCE_SHA256, "receipt mapping evidence identity drift"
    )
    require(inputs["embedded_font_sha256"] == EXPECTED_FONT_SHA256, "receipt font identity drift")
    require(inputs["to_unicode_cmap_sha256"] == EXPECTED_TO_UNICODE_SHA256, "receipt ToUnicode identity drift")
    require(inputs["implementation_sha256"] == file_sha256(Path(__file__)), "receipt implementation identity drift")
    require(inputs["receipt_schema_sha256"] == file_sha256(RECEIPT_SCHEMA_PATH), "receipt schema identity drift")
    require(denominator["input_records"] == EXPECTED_CATALOG_RECORDS, "receipt input record denominator drift")
    require(
        denominator["input_characters"] == EXPECTED_RAW_RECORD_CHARACTERS, "receipt raw character denominator drift"
    )
    require(
        denominator["output_characters"] == EXPECTED_NORMALIZED_CHARACTERS,
        "receipt normalized character denominator drift",
    )
    require(
        denominator["records_with_mappings"] == EXPECTED_RECORDS_WITH_MAPPINGS,
        "receipt mapped-record denominator drift",
    )
    require(denominator["mapping_events"] == EXPECTED_MAPPING_EVENTS, "receipt mapping-event denominator drift")
    require(receipt["mapping_contract"]["observed_counts"] == EXPECTED_MAPPING_COUNTS, "receipt mapping counts drift")

    upstream = validate_existing_materialization(pdf_path=pdf_path, private_output_dir=raw_catalog_dir)
    require(upstream["private_jsonl_sha256"] == EXPECTED_RAW_OUTPUT_SHA256, "upstream raw output identity drift")
    require(upstream["receipt_sha256"] == EXPECTED_RAW_RECEIPT_SHA256, "upstream raw receipt identity drift")
    require(
        file_sha256(raw_catalog_dir / RAW_RECEIPT_FILENAME) == EXPECTED_RAW_RECEIPT_FILE_SHA256,
        "upstream receipt file drift",
    )
    validate_mapping_evidence(mapping_evidence_path)
    require(output_path.is_file() and not output_path.is_symlink(), "glyph adapter JSONL is missing or unsafe")
    require(output_path.stat().st_size == receipt["output"]["bytes"], "glyph adapter byte count drift")
    require(file_sha256(output_path) == receipt["output"]["sha256"], "glyph adapter SHA-256 drift")

    raw_path = raw_catalog_dir / RAW_OUTPUT_FILENAME
    require(file_sha256(raw_path) == EXPECTED_RAW_OUTPUT_SHA256, "raw catalogue SHA-256 drift")
    raw_records = _load_raw_records(raw_path)
    output_records = _load_output_records(output_path)
    require(len(raw_records) == len(output_records) == EXPECTED_CATALOG_RECORDS, "adapter record count drift")
    expected_records = [
        build_normalized_record(record, upstream_raw_sha256=EXPECTED_RAW_OUTPUT_SHA256) for record in raw_records
    ]
    require(output_records == expected_records, "glyph adapter output does not equal deterministic replay")
    for record, raw_record in zip(output_records, raw_records, strict=True):
        _validate_normalized_record(record, raw_record)
    manifest = [
        {
            "graffito_number": record["graffito_number"],
            "raw_source_text_sha256": record["raw_source_text_sha256"],
            "normalized_text_sha256": record["normalized_text_sha256"],
            "mapping_event_counts": record["mapping_event_counts"],
        }
        for record in output_records
    ]
    require(
        sha256_value(manifest) == receipt["output"]["record_identity_manifest_sha256"],
        "adapter record identity manifest drift",
    )
    return {
        "ok": True,
        "records": len(output_records),
        "mapping_events": denominator["mapping_events"],
        "output_sha256": receipt["output"]["sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "training_eligible": False,
        "phase4_authorized": False,
    }


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--raw-catalog-dir", type=Path, required=True)
    parser.add_argument("--mapping-evidence", type=Path, required=True)
    parser.add_argument("--private-output-dir", type=Path, required=True)
    parser.add_argument("--validate-existing", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.validate_existing:
            result = validate_existing_glyph_adapter(
                pdf_path=args.pdf,
                raw_catalog_dir=args.raw_catalog_dir,
                mapping_evidence_path=args.mapping_evidence,
                private_output_dir=args.private_output_dir,
            )
            status = "glyph_adapter_validated"
        else:
            receipt = adapt_spas_glyphs(
                pdf_path=args.pdf,
                raw_catalog_dir=args.raw_catalog_dir,
                mapping_evidence_path=args.mapping_evidence,
                private_output_dir=args.private_output_dir,
            )
            result = {
                "records": receipt["output"]["records"],
                "mapping_events": receipt["denominator"]["mapping_events"],
                "output_sha256": receipt["output"]["sha256"],
                "receipt_sha256": receipt["receipt_sha256"],
                "training_eligible": False,
                "phase4_authorized": False,
            }
            status = "glyph_adapter_materialized"
    except (SpasGlyphAdapterError, SpasCatalogMaterializationError) as exc:
        print(canonical_json({"status": "blocked", "error": str(exc)}))
        return 2
    print(canonical_json({"status": status, **result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
