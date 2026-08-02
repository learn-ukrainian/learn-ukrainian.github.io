#!/usr/bin/env python3
"""One public, zero-API entry point for portable Ukrainian Data Foundry runs.

The CLI accepts only a consumer-owned JSONL corpus plus explicitly named local
artifacts.  It preserves source text, keeps rights decisions capability-local,
emits disjoint views, applies the frozen evaluation firewall, and records what
it could not establish.  It never calls a model, network service, trainer, or
optimizer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from scripts.projects.open_model_data import model_view_exporter as exporter

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
INPUT_SCHEMA = CONTRACTS / "portable_corpus_record_v1.schema.json"
RECEIPT_SCHEMA = CONTRACTS / "foundry_run_receipt_v1.schema.json"
DETECTOR_CONFIG = ROOT / "data/projects/open_model_data/detector/language_contact_config_v1.json"
DEFAULT_V011_MANIFEST = ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json"
DEFAULT_V02_PACKET = ROOT / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl"
TOOL_VERSION = "1.0.0"
MAX_RECORD_LIMIT = 100_000
WORD_RE = re.compile(r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+(?:[’ʼ'][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+)*")
RUSSIAN_ORTHOGRAPHY_RE = re.compile(r"[ыэъё]", re.IGNORECASE)
LATIN_RUN_RE = re.compile(r"(?<![A-Za-z])(?:[A-Za-z][A-Za-z'-]*\s+){1,}[A-Za-z][A-Za-z'-]*(?![A-Za-z])")
OCR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]|(?:Ã.|Â.|Ð.|Ñ.){2,}")
QUOTE_PATTERNS = (
    re.compile(r"«(?P<body>[^»]+)»"),
    re.compile(r"“(?P<body>[^”]+)”"),
    re.compile(r"„(?P<body>[^“]+)“"),
    re.compile(r'"(?P<body>[^"\n]+)"'),
)
CAPABILITIES = (
    "local_model_learning",
    "raw_source_redistribution",
    "dataset_publication",
    "model_publication",
    "public_release",
)
VIEW_FILES = {
    "canonical_records": "canonical-records.jsonl",
    "contextual_evidence": "contextual-evidence.jsonl",
    "faithful_source": "faithful-source.jsonl",
    "modern_learning": "modern-learning.jsonl",
    "silver_correction": "silver-correction.jsonl",
    "preference": "preference.jsonl",
    "quality_filter": "quality-filter.jsonl",
    "heldout_evaluation": "heldout-evaluation.jsonl",
}
BUILTIN_EVIDENCE_LOCATOR = {
    "kind": "urn",
    "uri": "urn:learn-ukrainian:foundry:language-contact-config-v1",
    "retrieved_on": "2026-08-01",
    "sha256": None,
}


class FoundryError(ValueError):
    """A stable public Foundry contract error."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class PreparedRun:
    """A completed portable preparation run."""

    output_dir: Path
    receipt: dict[str, Any]


def canonical_json(value: Any) -> str:
    """Return the canonical UTF-8 JSON representation used in receipts."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise FoundryError("FNDY-E001", f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FoundryError("FNDY-E001", f"cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise FoundryError("FNDY-E001", f"expected a JSON object: {path}")
    return value


def validator(path: Path) -> Draft202012Validator:
    schema = read_json(path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate(value: Mapping[str, Any], active: Draft202012Validator, label: str) -> None:
    errors = sorted(active.iter_errors(value), key=lambda error: list(error.path))
    if not errors:
        return
    location = ".".join(str(part) for part in errors[0].path) or "<root>"
    raise FoundryError("FNDY-E002", f"{label} schema violation at {location}: {errors[0].message}")


def read_records(path: Path, *, max_records: int) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FoundryError("FNDY-E001", f"input JSONL is missing: {path}")
    if max_records < 1 or max_records > MAX_RECORD_LIMIT:
        raise FoundryError("FNDY-E001", f"--max-records must be between 1 and {MAX_RECORD_LIMIT}")
    active = validator(INPUT_SCHEMA)
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    raise FoundryError("FNDY-E001", f"blank JSONL line {line_number}")
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise FoundryError("FNDY-E001", f"invalid JSONL line {line_number}") from exc
                if not isinstance(record, dict):
                    raise FoundryError("FNDY-E001", f"JSONL line {line_number} is not an object")
                validate(record, active, f"input line {line_number}")
                record_id = str(record["record_id"])
                if record_id in seen:
                    raise FoundryError("FNDY-E002", f"duplicate record_id: {record_id}")
                seen.add(record_id)
                validate_semantics(record, line_number)
                records.append(record)
                if len(records) > max_records:
                    raise FoundryError("FNDY-E001", f"input exceeds the declared {max_records}-record bound")
    except OSError as exc:
        raise FoundryError("FNDY-E001", f"cannot read input JSONL: {path}") from exc
    if not records:
        raise FoundryError("FNDY-E001", "input JSONL is empty")
    return records


def validate_semantics(record: Mapping[str, Any], line_number: int) -> None:
    text = str(record["text"])
    for group in (record.get("evidence", []), record.get("corrections", [])):
        for item in group:
            start = int(item["start_char"])
            end = int(item["end_char"])
            if not 0 <= start < end <= len(text):
                raise FoundryError(
                    "FNDY-E002",
                    f"input line {line_number} span [{start}, {end}) is outside text length {len(text)}",
                )
    for name in CAPABILITIES:
        decision = record["capabilities"][name]
        if decision["status"] == "allowed" and not decision["evidence"]:
            raise FoundryError("FNDY-E002", f"input line {line_number} allows {name} without evidence")


def _builtin_locator() -> dict[str, Any]:
    locator = dict(BUILTIN_EVIDENCE_LOCATOR)
    locator["sha256"] = sha256_file(DETECTOR_CONFIG)
    return locator


def _quoted_intervals(text: str) -> list[tuple[int, int]]:
    intervals: list[tuple[int, int]] = []
    for pattern in QUOTE_PATTERNS:
        for match in pattern.finditer(text):
            intervals.append((match.start("body"), match.end("body")))
    return sorted(set(intervals))


def _inside(offset: int, intervals: Sequence[tuple[int, int]]) -> bool:
    return any(start <= offset < end for start, end in intervals)


def _signal(
    *,
    track: str,
    start: int,
    end: int,
    route: str,
    note: str,
    sources: Sequence[Mapping[str, Any]] | None = None,
    evidence_grade: str = "controlled_silver",
) -> dict[str, Any]:
    return {
        "track": track,
        "start_char": start,
        "end_char": end,
        "route": route,
        "evidence_grade": evidence_grade,
        "sources": [dict(item) for item in (sources or (_builtin_locator(),))],
        "note": note,
    }


def _literal_matches(text: str, value: str) -> Iterable[tuple[int, int]]:
    lower = text.casefold()
    needle = value.casefold()
    start = 0
    while (index := lower.find(needle, start)) >= 0:
        yield index, index + len(value)
        start = index + max(1, len(value))


def contextual_evidence(record: Mapping[str, Any], config: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return deterministic candidates and protected routes, never verdicts."""
    text = str(record["text"])
    context = record["context"]
    quoted = _quoted_intervals(text)
    signals = [dict(item) for item in record.get("evidence", [])]

    protected_track: str | None = None
    if context["period"] in {"historical", "archaic", "middle_ukrainian", "old_east_slavic"}:
        protected_track = "historical_archaic"
    elif context["register"] in {"dialectal", "regional"}:
        protected_track = "regional_dialect"
    elif context["register"] in {"conversational", "marked"}:
        protected_track = "register"
    if protected_track:
        signals.append(
            _signal(
                track=protected_track,
                start=0,
                end=len(text),
                route="protected",
                note="consumer-declared contextual stratum; preserve and report separately",
                sources=record["source"]["locators"],
                evidence_grade="source_backed_silver",
            )
        )

    for correction in record.get("corrections", []):
        signals.append(
            _signal(
                track=str(correction["track"]),
                start=int(correction["start_char"]),
                end=int(correction["end_char"]),
                route="candidate_error",
                note="consumer-supplied correction evidence; emitted as silver unless separately qualified",
                sources=correction["evidence"],
                evidence_grade=str(correction["evidence_grade"]),
            )
        )

    anchors = [str(item) for item in config["prefilter"]["russian_anchors"]]
    russian_matches: list[tuple[int, int]] = []
    for anchor in anchors:
        russian_matches.extend(_literal_matches(text, anchor))
    russian_matches.extend((match.start(), match.end()) for match in RUSSIAN_ORTHOGRAPHY_RE.finditer(text))
    for start, end in sorted(set(russian_matches)):
        in_quote = _inside(start, quoted)
        contextual_route = "unresolved" if protected_track else "candidate_error"
        signals.append(
            _signal(
                track="quoted_russian" if in_quote else "russian_interference",
                start=start,
                end=end,
                route="protected" if in_quote else contextual_route,
                note=(
                    "Russian-form signal inside quotation; preserve the quoted text"
                    if in_quote
                    else (
                        "Russian-form signal in a protected contextual stratum; unresolved, not an error verdict"
                        if protected_track
                        else "Russian-form signal in unquoted context; contextual review required"
                    )
                ),
            )
        )

    for route in config["valid_word_routes"]:
        for start, end in _literal_matches(text, str(route["pattern"])):
            signals.append(
                _signal(
                    track="calques",
                    start=start,
                    end=end,
                    route="candidate_error",
                    note=f"curated route {route['route_kind']} ({route['source_key']}); not an automatic verdict",
                    evidence_grade="source_backed_silver",
                )
            )

    for match in OCR_RE.finditer(text):
        signals.append(
            _signal(
                track="ocr",
                start=match.start(),
                end=match.end(),
                route="unresolved",
                note="control-character or mojibake signal; retain original bytes for inspection",
            )
        )
    for match in LATIN_RUN_RE.finditer(text):
        signals.append(
            _signal(
                track="other_language",
                start=match.start(),
                end=match.end(),
                route="protected",
                note="multi-token Latin-script span; preserve as multilingual text",
            )
        )

    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for item in signals:
        source_uris = tuple(sorted(str(source["uri"]) for source in item["sources"]))
        key = (
            item["track"],
            int(item["start_char"]),
            int(item["end_char"]),
            item["route"],
            item["evidence_grade"],
            source_uris,
        )
        unique[key] = item
    return [unique[key] for key in sorted(unique)]


def _capability_summary(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for capability in CAPABILITIES:
        counts = Counter(str(record["capabilities"][capability]["status"]) for record in records)
        summary[capability] = {status: counts[status] for status in ("allowed", "denied", "unknown", "not_applicable")}
    return summary


def _artifact(path: Path, records: int) -> dict[str, Any]:
    return {
        "logical_path": path.name,
        "bytes": path.stat().st_size,
        "records": records,
        "sha256": sha256_file(path),
    }


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.write_text("".join(canonical_json(dict(row)) + "\n" for row in rows), encoding="utf-8")


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(canonical_json(dict(value)) + "\n", encoding="utf-8")


def _learning_allowed(record: Mapping[str, Any], contaminated: bool) -> bool:
    return (
        record["usage_role"] == "learning_candidate"
        and record["capabilities"]["local_model_learning"]["status"] == "allowed"
        and not contaminated
    )


def _mask_spans(evidence: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    maskable = [item for item in evidence if item["route"] in {"candidate_error", "unresolved"}]
    spans = sorted(
        {
            (int(item["start_char"]), int(item["end_char"]), str(item["track"]))
            for item in maskable
        }
    )
    return [{"start_char": start, "end_char": end, "reason": track} for start, end, track in spans]


def _is_modern_context(record: Mapping[str, Any], evidence: Sequence[Mapping[str, Any]]) -> bool:
    return record["context"]["period"] == "modern" and not any(
        item["route"] == "protected" and item["track"] in {"historical_archaic", "regional_dialect", "register"}
        for item in evidence
    )


def _build_views(
    records: Sequence[Mapping[str, Any]],
    registry: exporter.EvaluationExclusionRegistry,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    views = {name: [] for name in VIEW_FILES}
    contaminated = Counter()
    normalized_seen: dict[str, str] = {}
    duplicate_records: dict[str, str] = {}
    evidence_counts: Counter[str] = Counter()

    for record in records:
        record_id = str(record["record_id"])
        text = str(record["text"])
        text_hash = sha256_text(text)
        normalized_hash = sha256_text(exporter.normalize_text(text))
        duplicate_of = normalized_seen.get(normalized_hash)
        if duplicate_of is None:
            normalized_seen[normalized_hash] = record_id
        else:
            duplicate_records[record_id] = duplicate_of
        match = registry.match(text)
        if match.matched:
            contaminated[str(match.method)] += 1
        evidence = contextual_evidence(record, read_json(DETECTOR_CONFIG))
        evidence_counts.update(str(item["track"]) for item in evidence)
        canonical = {
            "schema_version": "foundry_canonical_record_v1",
            "record_id": record_id,
            "original_text": text,
            "text_sha256": text_hash,
            "source": record["source"],
            "context": record["context"],
            "capabilities": record["capabilities"],
            "usage_role": record["usage_role"],
            "evaluation_firewall": {"matched": match.matched, "method": match.method},
            "duplicate_of": duplicate_of,
        }
        views["canonical_records"].append(canonical)
        for signal_index, item in enumerate(evidence):
            views["contextual_evidence"].append(
                {
                    "schema_version": "foundry_contextual_evidence_v1",
                    "evidence_id": f"evidence:{sha256_text(canonical_json([record_id, signal_index, item]))}",
                    "record_id": record_id,
                    "text_sha256": text_hash,
                    **item,
                    "automatic_error_label": False,
                    "original_text_changed": False,
                }
            )

        learning_allowed = _learning_allowed(record, match.matched) and duplicate_of is None
        if learning_allowed:
            lineage = {
                "source_record_id": record_id,
                "source_text_sha256": text_hash,
                "source_locator_uris": sorted(locator["uri"] for locator in record["source"]["locators"]),
            }
            views["faithful_source"].append(
                {
                    "schema_version": "foundry_faithful_source_view_v1",
                    "record_id": record_id,
                    "text": text,
                    "text_sha256": text_hash,
                    "context": record["context"],
                    "lineage": lineage,
                    "character_mask_spans": [],
                }
            )
            if _is_modern_context(record, evidence):
                views["modern_learning"].append(
                    {
                        "schema_version": "foundry_modern_learning_view_v1",
                        "record_id": record_id,
                        "text": text,
                        "text_sha256": text_hash,
                        "lineage": lineage,
                        "character_mask_spans": _mask_spans(evidence),
                    }
                )

        for correction_index, correction in enumerate(record.get("corrections", [])):
            if not learning_allowed:
                continue
            start = int(correction["start_char"])
            end = int(correction["end_char"])
            source_span = text[start:end]
            correction_id = f"correction:{sha256_text(canonical_json([record_id, correction_index, correction]))}"
            base = {
                "record_id": correction_id,
                "track": correction["track"],
                "source_record_id": record_id,
                "source_text_sha256": text_hash,
                "start_char": start,
                "end_char": end,
                "evidence_grade": correction["evidence_grade"],
                "evidence": correction["evidence"],
                "evaluation_firewall_matched": False,
            }
            views["silver_correction"].append(
                {
                    "schema_version": "foundry_silver_correction_view_v1",
                    **base,
                    "source_span": source_span,
                    "replacement": correction["replacement"],
                    "human_gold_claimed": correction["evidence_grade"] == "human_gold",
                }
            )
            views["preference"].append(
                {
                    "schema_version": "foundry_preference_view_v1",
                    **base,
                    "chosen": correction["replacement"],
                    "rejected": source_span,
                    "preference_kind": "evidence_backed_local_edit",
                }
            )

        views["quality_filter"].append(
            {
                "schema_version": "foundry_quality_filter_view_v1",
                "record_id": record_id,
                "text_sha256": text_hash,
                "local_model_learning_allowed": record["capabilities"]["local_model_learning"]["status"] == "allowed",
                "evaluation_firewall_matched": match.matched,
                "evaluation_firewall_method": match.method,
                "duplicate_of": duplicate_of,
                "evidence_tracks": sorted({str(item["track"]) for item in evidence}),
                "keep_for_faithful_learning": learning_allowed,
                "automatic_deletion_authorized": False,
            }
        )
        if record["usage_role"] == "evaluation_only":
            views["heldout_evaluation"].append(
                {
                    "schema_version": "foundry_heldout_evaluation_view_v1",
                    "record_id": record_id,
                    "text": text,
                    "text_sha256": text_hash,
                    "context": record["context"],
                    "evidence": evidence,
                    "denied_destinations": [
                        "faithful_source",
                        "modern_learning",
                        "silver_correction",
                        "preference",
                    ],
                }
            )

    firewall = {
        **exporter.registry_receipt(registry),
        "matched_records": sum(contaminated.values()),
        "matched_by_method": dict(sorted(contaminated.items())),
        "intra_input_duplicate_records": len(duplicate_records),
        "duplicates": dict(sorted(duplicate_records.items())),
        "learning_views_contain_matched_records": False,
    }
    return views, {"firewall": firewall, "evidence_counts": dict(sorted(evidence_counts.items()))}


def _tokenizer_receipt(
    views: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    tokenizer_path: Path | None,
    tokenizer_identifier: str | None,
    tokenizer_revision: str | None,
) -> dict[str, Any]:
    texts = [str(row["text"]) for row in views["faithful_source"]]
    lexical_words = sum(len(WORD_RE.findall(text)) for text in texts)
    receipt: dict[str, Any] = {
        "schema_version": "foundry_tokenizer_receipt_v1",
        "status": "lexical_only",
        "records": len(texts),
        "utf8_bytes": sum(len(text.encode("utf-8")) for text in texts),
        "lexical_words": lexical_words,
        "model_token_count": None,
        "tokens_per_lexical_word": None,
        "tokenizer": None,
        "model_download_performed": False,
    }
    if tokenizer_path is None:
        return receipt
    if not tokenizer_identifier or not tokenizer_revision:
        raise FoundryError(
            "FNDY-E005",
            "--tokenizer-identifier and --tokenizer-revision are required with --tokenizer-path",
        )
    candidate = tokenizer_path / "tokenizer.json" if tokenizer_path.is_dir() else tokenizer_path
    if not candidate.is_file():
        raise FoundryError("FNDY-E005", f"tokenizer JSON is missing: {candidate}")
    try:
        from tokenizers import Tokenizer

        tokenizer = Tokenizer.from_file(str(candidate))
        token_count = sum(len(tokenizer.encode(text, add_special_tokens=False).ids) for text in texts)
    except (ImportError, OSError, ValueError) as exc:
        raise FoundryError("FNDY-E005", f"cannot load local tokenizer: {candidate}") from exc
    receipt.update(
        {
            "status": "measured_local_tokenizer",
            "model_token_count": token_count,
            "tokens_per_lexical_word": (
                format(Decimal(token_count) / Decimal(lexical_words), ".8f") if lexical_words else None
            ),
            "tokenizer": {
                "identifier": tokenizer_identifier,
                "revision": tokenizer_revision,
                "sha256": sha256_file(candidate),
            },
        }
    )
    return receipt


def _decimal(config: Mapping[str, Any], name: str, *, minimum: Decimal = Decimal("0")) -> Decimal:
    try:
        value = Decimal(str(config[name]))
    except (KeyError, InvalidOperation) as exc:
        raise FoundryError("FNDY-E006", f"cost config has invalid {name}") from exc
    if not value.is_finite() or value < minimum:
        raise FoundryError("FNDY-E006", f"cost config has out-of-range {name}")
    return value


def _decimal_text(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    return format(rounded, "f")


def _cost_receipt(cost_path: Path | None, tokenizer: Mapping[str, Any]) -> dict[str, Any]:
    if cost_path is None:
        return {
            "schema_version": "foundry_cost_receipt_v1",
            "status": "not_requested",
            "reason": "supply --cost-config with exact consumer measurements",
            "scenario_is_quote": False,
            "training_authorized": False,
        }
    config = read_json(cost_path)
    required = {
        "schema_version",
        "train_tokens",
        "epochs",
        "measured_aggregate_tokens_per_second",
        "accelerator_count",
        "provider_rate_usd_per_accelerator_hour",
        "storage_usd",
        "evaluation_usd",
        "failed_run_allowance_percent",
    }
    if set(config) != required or config.get("schema_version") != "foundry_cost_config_v1":
        raise FoundryError("FNDY-E006", "cost config fields do not match foundry_cost_config_v1")
    train_tokens = _decimal(config, "train_tokens")
    epochs = _decimal(config, "epochs", minimum=Decimal("0.000001"))
    throughput = _decimal(config, "measured_aggregate_tokens_per_second", minimum=Decimal("0.000001"))
    accelerators = _decimal(config, "accelerator_count", minimum=Decimal("1"))
    if accelerators != accelerators.to_integral_value():
        raise FoundryError("FNDY-E006", "accelerator_count must be an integer")
    rate = _decimal(config, "provider_rate_usd_per_accelerator_hour")
    storage = _decimal(config, "storage_usd")
    evaluation = _decimal(config, "evaluation_usd")
    failed_percent = _decimal(config, "failed_run_allowance_percent")
    if failed_percent > Decimal("1000"):
        raise FoundryError("FNDY-E006", "failed_run_allowance_percent exceeds 1000")
    hours = train_tokens * epochs / throughput / Decimal(3600)
    compute = hours * accelerators * rate
    subtotal = compute + storage + evaluation
    failed_allowance = subtotal * failed_percent / Decimal(100)
    total = subtotal + failed_allowance
    measured_tokens = tokenizer.get("model_token_count")
    return {
        "schema_version": "foundry_cost_receipt_v1",
        "status": "calculated",
        "inputs": {key: str(config[key]) for key in sorted(required - {"schema_version"})},
        "results": {
            "wall_clock_hours": _decimal_text(hours),
            "compute_usd": _decimal_text(compute),
            "storage_usd": _decimal_text(storage),
            "evaluation_usd": _decimal_text(evaluation),
            "failed_run_allowance_usd": _decimal_text(failed_allowance),
            "total_usd": _decimal_text(total),
        },
        "tokenizer_count_matches_train_tokens": (
            int(train_tokens) == int(measured_tokens) if measured_tokens is not None else None
        ),
        "formula": "tokens * epochs / measured_aggregate_tokens_per_second / 3600; multiply hours by accelerator_count and rate; add storage, evaluation, and failed-run allowance",
        "scenario_is_quote": False,
        "training_authorized": False,
    }


def _recipe(
    views: Mapping[str, Mapping[str, Any]],
    tokenizer: Mapping[str, Any],
    cost: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "foundry_consumer_recipe_v1",
        "inputs": {
            name: {"logical_path": artifact["logical_path"], "sha256": artifact["sha256"]}
            for name, artifact in sorted(views.items())
        },
        "base_model": {"identifier": None, "revision": None, "consumer_must_pin": True},
        "tokenizer": tokenizer["tokenizer"],
        "objective": "consumer-selected; keep continued pretraining, correction, preference, and evaluation separate",
        "split": {"strategy": "sha256(record_id) in consumer namespace", "namespace": None},
        "dependency_lock_sha256": None,
        "hyperparameters": {
            "sequence_length": None,
            "precision": None,
            "optimizer": None,
            "learning_rate": None,
            "epochs": None,
            "seed": None,
        },
        "evaluation": {
            "human_gold_anchor": "UA Eval 0.1.1 (immutable)",
            "broad_suite": "separately versioned open-weight suite when supplied",
            "closed_model_judge_allowed": False,
        },
        "stop_conditions": [
            "evaluation contamination detected",
            "protected-track regression",
            "recipe or input hash mismatch",
            "consumer cost ceiling exceeded",
        ],
        "cost_receipt_status": cost["status"],
        "training_authorized": False,
        "execution_state": "not_run",
    }


def _limitations() -> dict[str, Any]:
    return {
        "schema_version": "foundry_limitations_v1",
        "claims_not_supported": [
            "a single Ukrainian quality score",
            "human-gold status for silver evidence",
            "automatic linguistic error verdicts",
            "fluency improvement",
            "model or tokenizer suitability",
            "training cost without measured throughput",
            "publication rights beyond each explicit capability decision",
        ],
        "risks": [
            "corpus scale may be insufficient for the consumer objective",
            "silver evidence may be wrong or context-incomplete",
            "automatic cleaning can erase historical, regional, dialectal, quoted, or multilingual text",
            "tokenizer and model revisions change measured behavior",
            "public benchmarks may be contaminated in model pretraining",
        ],
    }


def prepare(
    *,
    input_path: Path,
    output_dir: Path,
    max_records: int,
    evaluation_artifacts: Sequence[Path],
    tokenizer_path: Path | None,
    tokenizer_identifier: str | None,
    tokenizer_revision: str | None,
    cost_path: Path | None,
) -> PreparedRun:
    """Prepare a bounded portable corpus and publish one atomic output directory."""
    records = read_records(input_path, max_records=max_records)
    if output_dir.exists():
        raise FoundryError("FNDY-E004", f"refusing to replace existing output directory: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    try:
        try:
            registry = exporter.build_exclusion_registry(
                v011_manifest=DEFAULT_V011_MANIFEST,
                v02_packet=DEFAULT_V02_PACKET,
                extra_artifacts=evaluation_artifacts,
            )
        except exporter.ExportError as exc:
            raise FoundryError("FNDY-E003", str(exc)) from exc
        view_rows, summaries = _build_views(records, registry)
        artifacts: dict[str, dict[str, Any]] = {}
        for name, filename in VIEW_FILES.items():
            path = staging / filename
            _write_jsonl(path, view_rows[name])
            artifacts[name] = _artifact(path, len(view_rows[name]))

        tokenizer = _tokenizer_receipt(
            view_rows,
            tokenizer_path=tokenizer_path,
            tokenizer_identifier=tokenizer_identifier,
            tokenizer_revision=tokenizer_revision,
        )
        tokenizer_path_out = staging / "tokenizer-receipt.json"
        _write_json(tokenizer_path_out, tokenizer)
        cost = _cost_receipt(cost_path, tokenizer)
        cost_path_out = staging / "cost-receipt.json"
        _write_json(cost_path_out, cost)
        recipe = _recipe(artifacts, tokenizer, cost)
        recipe_path = staging / "recipe-manifest.json"
        _write_json(recipe_path, recipe)
        limitations = _limitations()
        limitations_path = staging / "limitations.json"
        _write_json(limitations_path, limitations)

        supporting = {
            "tokenizer_receipt": _artifact(tokenizer_path_out, 1),
            "cost_receipt": _artifact(cost_path_out, 1),
            "recipe_manifest": _artifact(recipe_path, 1),
            "limitations": _artifact(limitations_path, 1),
        }
        reproducible_artifacts = {**artifacts, **supporting}
        input_artifact = {
            "logical_path": input_path.name,
            "bytes": input_path.stat().st_size,
            "records": len(records),
            "sha256": sha256_file(input_path),
        }
        receipt = {
            "schema_version": "foundry_run_receipt_v1",
            "tool": {"name": "ukrainian-data-foundry", "version": TOOL_VERSION, "command": "prepare"},
            "input": input_artifact,
            "capability_summary": _capability_summary(records),
            "evidence_summary": {
                "by_track": summaries["evidence_counts"],
                "total": sum(summaries["evidence_counts"].values()),
                "automatic_error_labels": 0,
            },
            "views": artifacts,
            "evaluation_firewall": summaries["firewall"],
            "tokenizer": tokenizer,
            "cost": cost,
            "recipe": recipe,
            "limitations": limitations,
            "reproduction": {
                "serialization": "UTF-8 canonical JSON, sorted keys, LF",
                "timestamps_omitted": True,
                "host_paths_omitted": True,
                "artifacts": reproducible_artifacts,
            },
            "safety": {
                "original_text_preserved": True,
                "automatic_rewrite_performed": False,
                "model_call_performed": False,
                "model_download_performed": False,
                "training_performed": False,
                "optimizer_executed": False,
                "adapter_created": False,
                "weights_uploaded": False,
                "closed_api_required": False,
                "publication_authorized": False,
            },
        }
        validate(receipt, validator(RECEIPT_SCHEMA), "run receipt")
        _write_json(staging / "run-receipt.json", receipt)
        os.replace(staging, output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return PreparedRun(output_dir=output_dir, receipt=receipt)


def verify(output_dir: Path) -> dict[str, Any]:
    """Verify a completed run without using the original corpus or any model."""
    receipt_path = output_dir / "run-receipt.json"
    receipt = read_json(receipt_path)
    validate(receipt, validator(RECEIPT_SCHEMA), "run receipt")
    checked = 0
    for artifact in receipt["reproduction"]["artifacts"].values():
        path = output_dir / artifact["logical_path"]
        if not path.is_file():
            raise FoundryError("FNDY-E007", f"reproduction artifact is missing: {path.name}")
        if path.stat().st_size != artifact["bytes"] or sha256_file(path) != artifact["sha256"]:
            raise FoundryError("FNDY-E007", f"reproduction artifact hash mismatch: {path.name}")
        checked += 1
    return {
        "schema_version": "foundry_verification_receipt_v1",
        "status": "passed",
        "artifacts_checked": checked,
        "run_receipt_sha256": sha256_file(receipt_path),
        "training_performed": False,
        "model_call_performed": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ukrainian-data-foundry", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare", help="prepare deterministic model-ready views")
    prepare_parser.add_argument("--input", type=Path, required=True, help="consumer-owned portable_corpus_record_v1 JSONL")
    prepare_parser.add_argument("--output-dir", type=Path, required=True)
    prepare_parser.add_argument("--max-records", type=int, default=10_000)
    prepare_parser.add_argument("--evaluation-artifact", type=Path, action="append", default=[])
    prepare_parser.add_argument("--tokenizer-path", type=Path)
    prepare_parser.add_argument("--tokenizer-identifier")
    prepare_parser.add_argument("--tokenizer-revision")
    prepare_parser.add_argument("--cost-config", type=Path)
    verify_parser = subparsers.add_parser("verify", help="verify saved output hashes without a model")
    verify_parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(
                input_path=args.input,
                output_dir=args.output_dir,
                max_records=args.max_records,
                evaluation_artifacts=tuple(args.evaluation_artifact),
                tokenizer_path=args.tokenizer_path,
                tokenizer_identifier=args.tokenizer_identifier,
                tokenizer_revision=args.tokenizer_revision,
                cost_path=args.cost_config,
            )
            print(canonical_json(result.receipt))
        else:
            print(canonical_json(verify(args.output_dir)))
    except FoundryError as exc:
        parser.exit(2, f"{exc.code}: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
