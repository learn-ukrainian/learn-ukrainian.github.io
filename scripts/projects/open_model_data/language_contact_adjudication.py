#!/usr/bin/env python3
"""Prepare real language-contact candidates for blind Ukrainian-human review.

The detector output is a sampling frame, not gold.  This module streams that
large JSONL into a compact text-free frame, applies only an explicitly approved
sampling plan, adapts selected rows into the existing correction factory, and
builds two independently ordered blind reviewer packets and offline workspaces.
It never supplies linguistic decisions or training/export eligibility.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import heapq
import importlib
import json
import os
import re
import sqlite3
import stat
import sys
import tempfile
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime
from itertools import pairwise
from pathlib import Path
from statistics import NormalDist
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
correction_factory = importlib.import_module("scripts.projects.open_model_data.correction_factory")

CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
DETECTOR_CONFIG = ROOT / "data/projects/open_model_data/detector/language_contact_config_v1.json"
DETECTOR_CANDIDATE_SCHEMA = CONTRACTS / "language_contact_candidate_v1.schema.json"
DETECTOR_RECEIPT_SCHEMA = CONTRACTS / "language_contact_receipt_v1.schema.json"
FRAME_ITEM_SCHEMA = CONTRACTS / "language_contact_frame_item_v1.schema.json"
FRAME_RECEIPT_SCHEMA = CONTRACTS / "language_contact_frame_receipt_v1.schema.json"
SAMPLING_PLAN_SCHEMA = CONTRACTS / "language_contact_sampling_plan_v1.schema.json"
BLIND_ITEM_SCHEMA = CONTRACTS / "language_contact_blind_review_item_v1.schema.json"
BLIND_RESPONSE_SCHEMA = CONTRACTS / "language_contact_blind_response_v1.schema.json"
WAVE_RECEIPT_SCHEMA = CONTRACTS / "language_contact_wave_receipt_v1.schema.json"
FIRST_PASS_SUMMARY_SCHEMA = CONTRACTS / "language_contact_first_pass_summary_v1.schema.json"
CAMPAIGN_RECEIPT_SCHEMA = CONTRACTS / "language_contact_campaign_receipt_v1.schema.json"
RESOLVER_ITEM_SCHEMA = CONTRACTS / "language_contact_resolver_review_item_v1.schema.json"
RESOLVER_RESPONSE_SCHEMA = CONTRACTS / "language_contact_resolver_response_v1.schema.json"
GOLD_FREEZE_RECEIPT_SCHEMA = CONTRACTS / "language_contact_gold_freeze_receipt_v1.schema.json"
CORRECTION_CANDIDATE_SCHEMA = CONTRACTS / "correction_candidate_v1.schema.json"
CORRECTION_DECISION_SCHEMA = CONTRACTS / "correction_reviewer_decision_v1.schema.json"

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
IDENTITY_ALGORITHM = "lcc. + sha256(canonical language_contact_candidate_v1 JSON UTF-8)"
RANK_ALGORITHM = "sha256(detector candidate artifact sha256 + NUL + candidate_id)"
STRATA = (
    "modern_interference",
    "valid_word_contact",
    "false_positive_rescue",
    "historical",
    "regional_or_dialectal_candidate",
    "conversational_or_marked",
    "quoted_or_multilingual",
    "uncertain",
    "technical_or_ocr",
    "proper_name",
)


class AdjudicationError(ValueError):
    """An input or output violates the blind-adjudication boundary."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdjudicationError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AdjudicationError(f"expected JSON object: {path}")
    return value


def read_secret(path: Path) -> str:
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
        value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise AdjudicationError(f"cannot read packet-salt file {path}: {exc}") from exc
    require(mode & 0o077 == 0, f"packet-salt file must deny group/other access: {path}")
    require(bool(value), f"packet-salt file is empty: {path}")
    return value


def validator(path: Path) -> Draft202012Validator:
    schema = read_json(path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate(value: Mapping[str, Any], active: Draft202012Validator, label: str) -> None:
    errors = sorted(active.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        location = ".".join(str(item) for item in errors[0].path) or "<root>"
        raise AdjudicationError(f"{label} schema violation at {location}: {errors[0].message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AdjudicationError(message)


def iter_jsonl_bytes(path: Path) -> Iterator[tuple[int, int, int, bytes, dict[str, Any]]]:
    """Yield line number, byte offset/length, raw bytes, and JSON object."""
    try:
        with path.open("rb") as handle:
            line_number = 0
            while True:
                offset = handle.tell()
                raw = handle.readline()
                if not raw:
                    break
                line_number += 1
                if not raw.strip():
                    continue
                try:
                    value = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise AdjudicationError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
                if not isinstance(value, dict):
                    raise AdjudicationError(f"expected JSON object at {path}:{line_number}")
                yield line_number, offset, len(raw), raw, value
    except OSError as exc:
        raise AdjudicationError(f"cannot read JSONL {path}: {exc}") from exc


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    for _line, _offset, _length, _raw, value in iter_jsonl_bytes(path):
        yield value


def _temporary_path(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        return Path(handle.name)


def _promote_outputs(temporary_to_output: Sequence[tuple[Path, Path]]) -> None:
    """Promote a related artifact set and restore previous outputs on failure."""
    backups: dict[Path, Path] = {}
    reserved_backups: list[Path] = []
    promoted: list[Path] = []
    try:
        for _temporary, output in temporary_to_output:
            if output.exists():
                backup = _temporary_path(output)
                reserved_backups.append(backup)
                try:
                    os.replace(output, backup)
                except OSError:
                    backup.unlink(missing_ok=True)
                    raise
                backups[output] = backup
        for temporary, output in temporary_to_output:
            os.replace(temporary, output)
            promoted.append(output)
    except OSError:
        for output in reversed(promoted):
            output.unlink(missing_ok=True)
        for output, backup in backups.items():
            if backup.exists():
                os.replace(backup, output)
        raise
    else:
        for backup in backups.values():
            backup.unlink(missing_ok=True)
    finally:
        for temporary, _output in temporary_to_output:
            temporary.unlink(missing_ok=True)
        for backup in reserved_backups:
            backup.unlink(missing_ok=True)


def _category_strata(candidate: Mapping[str, Any]) -> list[str]:
    classification = candidate["classification"]
    category = classification["category"]
    period = str(candidate["metadata"]["period"])
    register = str(candidate["metadata"]["register"])
    role = classification["discourse_role"]
    result: set[str] = set()
    if category in {
        "modern_narration_interference",
        "mixed_surzhyk_candidate",
        "ukrainian_phonetic_russian",
    }:
        result.add("modern_interference")
    if category == "valid_word_contact_candidate":
        result.add("valid_word_contact")
    if category == "protected_authentic_ukrainian":
        result.update({"false_positive_rescue", "regional_or_dialectal_candidate"})
    if category == "historical_unresolved" or period != "modern":
        result.add("historical")
    if register in {"scripted", "conversational", "marked"} or role in {
        "dialogue",
        "metalinguistic_example",
    }:
        result.add("conversational_or_marked")
    if category in {"russian_quotation", "other_language"} or role in {
        "quotation",
        "epigraph",
        "citation_or_document",
    }:
        result.add("quoted_or_multilingual")
    if category in {"uncertain", "mixed_surzhyk_candidate"}:
        result.add("uncertain")
    if category == "ocr_or_encoding_candidate":
        result.add("technical_or_ocr")
    if category == "proper_name":
        result.add("proper_name")
    if not result:
        result.add("uncertain")
    return sorted(result)


def _frame_item(
    candidate: Mapping[str, Any],
    *,
    line_number: int,
    byte_offset: int,
    byte_length: int,
    stream_sha256: str,
) -> dict[str, Any]:
    candidate_sha256 = sha256_text(canonical_json(candidate))
    candidate_id = f"lcc.{candidate_sha256}"
    classification = candidate["classification"]
    metadata = candidate["metadata"]
    return {
        "calibration_strata": _category_strata(candidate),
        "candidate_id": candidate_id,
        "candidate_sha256": candidate_sha256,
        "category": classification["category"],
        "discourse_role": classification["discourse_role"],
        "language_identity": classification["language_identity"],
        "input": {
            "byte_length": byte_length,
            "byte_offset": byte_offset,
            "line_number": line_number,
        },
        "locator": candidate["locator"],
        "period": metadata["period"],
        "queue_route": candidate["queue_route"],
        "rank_sha256": sha256_text(f"{stream_sha256}\0{candidate_id}"),
        "register": metadata["register"],
        "schema_version": "language_contact_frame_item_v1",
        "source_family": candidate["source_family"],
        "source_record_id": candidate["source_record_id"],
    }


def build_frame(
    *,
    candidates_path: Path,
    detector_receipt_path: Path,
    frame_output: Path,
    receipt_output: Path,
) -> dict[str, Any]:
    """Stream the detector artifact into a deterministic text-free frame."""
    detector_receipt = read_json(detector_receipt_path)
    validate(detector_receipt, validator(DETECTOR_RECEIPT_SCHEMA), "detector receipt")
    expected = detector_receipt["outputs"]["review_candidates"]
    actual_bytes = candidates_path.stat().st_size
    actual_sha256 = sha256_file(candidates_path)
    require(actual_bytes == expected["bytes"], "candidate byte count differs from receipt")
    require(actual_sha256 == expected["sha256"], "candidate hash differs from receipt")

    candidate_validator = validator(DETECTOR_CANDIDATE_SCHEMA)
    item_validator = validator(FRAME_ITEM_SCHEMA)
    receipt_validator = validator(FRAME_RECEIPT_SCHEMA)
    temporary_frame = _temporary_path(frame_output)
    seen: set[str] = set()
    logical_digest = hashlib.sha256()
    counts = {
        "category": Counter(),
        "period": Counter(),
        "register": Counter(),
        "source_family": Counter(),
        "stratum": Counter(),
    }
    records = 0
    try:
        with temporary_frame.open("wb") as output:
            for line_number, offset, length, _raw, candidate in iter_jsonl_bytes(candidates_path):
                validate(candidate, candidate_validator, f"candidate line {line_number}")
                item = _frame_item(
                    candidate,
                    line_number=line_number,
                    byte_offset=offset,
                    byte_length=length,
                    stream_sha256=actual_sha256,
                )
                validate(item, item_validator, f"frame item line {line_number}")
                require(item["candidate_id"] not in seen, "duplicate frame candidate ID")
                seen.add(item["candidate_id"])
                encoded = (canonical_json(item) + "\n").encode("utf-8")
                output.write(encoded)
                logical_digest.update(encoded)
                records += 1
                for dimension in ("category", "period", "register", "source_family"):
                    counts[dimension][str(item[dimension])] += 1
                for stratum in item["calibration_strata"]:
                    counts["stratum"][stratum] += 1
        require(records == expected["records"], "candidate record count differs from receipt")
        frame_sha256 = logical_digest.hexdigest()
        require(frame_sha256 == sha256_file(temporary_frame), "frame hash mismatch")
        receipt = {
            "claims": {
                "labels_created": False,
                "gold_created": False,
                "publication_performed": False,
                "training_performed": False,
            },
            "counts": {f"by_{dimension}": dict(sorted(counter.items())) for dimension, counter in counts.items()},
            "detector_candidate_input": {
                "bytes": actual_bytes,
                "records": records,
                "sha256": actual_sha256,
            },
            "detector_receipt_sha256": sha256_file(detector_receipt_path),
            "determinism": {
                "ordering": "detector JSONL byte order",
                "serialization": "UTF-8 canonical JSON with sorted keys and LF",
                "timestamps_omitted": True,
            },
            "logical_frame_artifact": {
                "records": records,
                "sha256": frame_sha256,
            },
            "identity_algorithm": IDENTITY_ALGORITHM,
            "rank_algorithm": RANK_ALGORITHM,
            "schema_version": "language_contact_frame_receipt_v1",
        }
        validate(receipt, receipt_validator, "frame receipt")
        temporary_receipt = _temporary_path(receipt_output)
        temporary_receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        _promote_outputs(((temporary_frame, frame_output), (temporary_receipt, receipt_output)))
        return receipt
    except Exception:
        temporary_frame.unlink(missing_ok=True)
        raise


def draft_sampling_plan(
    *,
    frame_receipt_path: Path,
    plan_output: Path,
    plan_id: str,
    issue_url: str,
) -> dict[str, Any]:
    """Write a measured pending plan without inventing capacity or stop rules."""
    receipt = read_json(frame_receipt_path)
    validate(receipt, validator(FRAME_RECEIPT_SCHEMA), "frame receipt")
    observed = receipt["counts"]["by_stratum"]
    require(set(observed) == set(STRATA), "frame receipt lacks required calibration strata")
    plan = {
        "approval": {
            "approved_at": None,
            "issue_url": issue_url,
            "operator_id": None,
            "rationale": (
                "Pending named qualified Ukrainian reviewers, measured reviewer "
                "capacity, and an operator-approved statistical stop rule."
            ),
            "status": "pending",
        },
        "frame_sha256": receipt["logical_frame_artifact"]["sha256"],
        "packet_controls": None,
        "plan_id": plan_id,
        "reviewer_capacity": None,
        "schema_version": "language_contact_sampling_plan_v1",
        "statistical_stop": None,
        "strata": [
            {
                "calibration_target": None,
                "observed_frame_count": observed[stratum],
                "production_target": None,
                "rationale": (
                    "Measured frame stratum; targets remain unset until reviewer "
                    "capacity and the statistical stop rule are approved."
                ),
                "stratum_id": stratum,
            }
            for stratum in STRATA
        ],
    }
    validate(plan, validator(SAMPLING_PLAN_SCHEMA), "pending sampling plan")
    temporary = _temporary_path(plan_output)
    try:
        temporary.write_text(canonical_json(plan) + "\n", encoding="utf-8")
        _promote_outputs(((temporary, plan_output),))
    finally:
        temporary.unlink(missing_ok=True)
    return plan


def _approved_targets(plan: Mapping[str, Any], stage: str) -> dict[str, int]:
    require(plan["approval"]["status"] == "approved", "sampling plan is not approved")
    field = "calibration_target" if stage == "calibration" else "production_target"
    targets = {row["stratum_id"]: row[field] for row in plan["strata"]}
    require(
        len(plan["strata"]) == len(STRATA) and set(targets) == set(STRATA),
        "sampling plan must contain every stratum exactly once",
    )
    require(
        all(isinstance(value, int) and value > 0 for value in targets.values()), f"approved plan lacks {field} values"
    )
    capacity = plan["reviewer_capacity"]
    first_pass_ids = capacity["first_pass_reviewer_ids"]
    require(
        capacity["third_resolver_id"] not in first_pass_ids,
        "third resolver must be distinct from both first-pass reviewers",
    )
    return targets


def _select_frame_items(
    frame_path: Path,
    *,
    plan: Mapping[str, Any],
    stage: str,
    excluded_candidate_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    targets = _approved_targets(plan, stage)
    excluded = excluded_candidate_ids or set()
    frame_validator = validator(FRAME_ITEM_SCHEMA)
    # Store inverse integer ranks so heap[0] is the current worst retained row.
    numeric_heaps: dict[str, list[tuple[int, str, dict[str, Any]]]] = {stratum: [] for stratum in STRATA}
    for line_number, item in enumerate(iter_jsonl(frame_path), 1):
        validate(item, frame_validator, f"frame line {line_number}")
        if item["candidate_id"] in excluded:
            continue
        rank_int = int(item["rank_sha256"], 16)
        for stratum in item["calibration_strata"]:
            target = targets[stratum]
            heap = numeric_heaps[stratum]
            entry = (-rank_int, item["candidate_id"], item)
            if len(heap) < target:
                heapq.heappush(heap, entry)
            elif entry > heap[0]:
                heapq.heapreplace(heap, entry)
    selected_by_id: dict[str, dict[str, Any]] = {}
    for stratum, heap in numeric_heaps.items():
        require(len(heap) == targets[stratum], f"frame cannot satisfy stratum {stratum}")
        for _rank, _candidate_id, item in heap:
            selected_by_id[item["candidate_id"]] = item
    selected = sorted(selected_by_id.values(), key=lambda item: (item["rank_sha256"], item["candidate_id"]))
    capacity = plan["reviewer_capacity"]
    per_reviewer_capacity = int(capacity["items_per_hour"] * capacity["hours_per_person_per_wave"])
    require(
        len(selected) <= per_reviewer_capacity,
        "selected union exceeds the approved per-reviewer wave capacity",
    )
    return selected


def _prior_wave_exclusions(
    *,
    receipt_paths: Sequence[Path],
    selected_manifest_paths: Sequence[Path],
    plan_path: Path,
    frame_path: Path,
    stage: str,
    wave_number: int,
) -> tuple[set[str], list[dict[str, Any]]]:
    """Validate the complete prior-wave chain and return its candidate IDs."""
    require(
        len(receipt_paths) == len(selected_manifest_paths),
        "prior wave receipts and selected manifests must be paired",
    )
    if stage == "calibration":
        require(wave_number == 1, "calibration is exactly wave 1")
        require(not receipt_paths, "calibration wave cannot have prior waves")
        return set(), []
    require(wave_number >= 1, "production wave number must be positive")
    require(receipt_paths, "production requires the calibration wave chain")

    plan_sha256 = sha256_file(plan_path)
    frame_sha256 = sha256_file(frame_path)
    frame_validator = validator(FRAME_ITEM_SCHEMA)
    seen_wave_keys: set[tuple[str, int]] = set()
    prior_receipts: list[Mapping[str, Any]] = []
    excluded: set[str] = set()
    evidence: list[dict[str, Any]] = []
    for receipt_path, selected_path in zip(receipt_paths, selected_manifest_paths, strict=True):
        receipt = read_json(receipt_path)
        validate(receipt, validator(WAVE_RECEIPT_SCHEMA), f"prior wave receipt {receipt_path}")
        require(receipt["plan_sha256"] == plan_sha256, "prior wave uses another sampling plan")
        require(receipt["frame_sha256"] == frame_sha256, "prior wave uses another frame")
        prior_receipts.append(receipt)
        key = (receipt["stage"], receipt["wave_number"])
        require(key not in seen_wave_keys, f"duplicate prior wave: {key}")
        seen_wave_keys.add(key)
        rows = _unique_rows(
            selected_path,
            active_validator=frame_validator,
            label="prior selected frame item",
            key="candidate_id",
        )
        artifact = _artifact(selected_path, len(rows))
        require(
            artifact == receipt["selected_manifest"],
            "prior selected manifest does not match its wave receipt",
        )
        overlap = excluded.intersection(rows)
        require(not overlap, "candidate appears in more than one prior wave")
        excluded.update(rows)
        evidence.append(
            {
                "receipt_sha256": sha256_file(receipt_path),
                "selected_manifest": artifact,
                "stage": receipt["stage"],
                "wave_number": receipt["wave_number"],
            }
        )
    require(("calibration", 1) in seen_wave_keys, "production chain lacks calibration wave 1")
    expected_production = {("production", number) for number in range(1, wave_number)}
    actual_production = {key for key in seen_wave_keys if key[0] == "production"}
    require(
        actual_production == expected_production,
        "production chain must contain every earlier production wave exactly once",
    )
    require(
        seen_wave_keys == {("calibration", 1), *expected_production},
        "prior wave chain contains unexpected stages or wave numbers",
    )
    for receipt in prior_receipts:
        if receipt["stage"] == "calibration":
            expected_receipt_chain: set[tuple[str, int]] = set()
        else:
            expected_receipt_chain = {("calibration", 1)} | {
                ("production", number) for number in range(1, receipt["wave_number"])
            }
        actual_receipt_chain = {
            (item["stage"], item["wave_number"])
            for item in receipt["prior_waves"]
        }
        require(
            actual_receipt_chain == expected_receipt_chain,
            "prior wave receipt does not bind its complete earlier chain",
        )
    return excluded, sorted(evidence, key=lambda row: (row["stage"] != "calibration", row["wave_number"]))


def _read_candidate_at(
    handle: Any,
    frame_item: Mapping[str, Any],
    *,
    active_validator: Draft202012Validator,
) -> dict[str, Any]:
    handle.seek(frame_item["input"]["byte_offset"])
    raw = handle.read(frame_item["input"]["byte_length"])
    try:
        candidate = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdjudicationError(f"cannot reconstruct {frame_item['candidate_id']}: {exc}") from exc
    validate(candidate, active_validator, f"selected {frame_item['candidate_id']}")
    digest = sha256_text(canonical_json(candidate))
    require(digest == frame_item["candidate_sha256"], "selected candidate hash mismatch")
    require(f"lcc.{digest}" == frame_item["candidate_id"], "selected candidate ID mismatch")
    return candidate


def _source_config(config: Mapping[str, Any], source_family: str) -> Mapping[str, Any]:
    matches = [item for item in config["sources"] if item["source_family"] == source_family]
    require(len(matches) == 1, f"missing or duplicate source config: {source_family}")
    return matches[0]


def _dimension(adapter: Mapping[str, Any], row: sqlite3.Row, name: str) -> str:
    spec = adapter["dimensions"][name]
    if "constant" in spec:
        return str(spec["constant"])
    value = row[str(spec["column"])]
    return str(value) if value not in {None, ""} else "unknown"


def _selected_source_metadata(
    candidate: Mapping[str, Any],
    *,
    detector_config: Mapping[str, Any],
    input_root: Path,
) -> dict[str, Any]:
    source = _source_config(detector_config, candidate["source_family"])
    adapter = source["adapter"]
    database = (input_root / adapter["database"]).resolve()
    require(database.exists(), f"source database unavailable: {adapter['database']}")
    table = str(adapter["table"])
    id_column = str(adapter["id_column"])
    allowed = {
        "literary_texts": ("title", "author", "work", "year", "genre"),
        "textbooks": ("title", "author_uk", "author", "grade", "subject"),
        "external_articles": ("title", "speaker", "publish_date", "domain", "register_tag"),
        "wikipedia": ("title",),
    }
    require(table in allowed, f"unsupported selected source table: {table}")
    columns = [id_column, str(adapter["text_column"]), *allowed[table]]
    quoted = ", ".join(f'"{name}"' for name in columns)
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            f'SELECT {quoted} FROM "{table}" WHERE "{id_column}" = ?',
            (candidate["record_id"],),
        ).fetchone()
    finally:
        connection.close()
    require(row is not None, f"selected source record missing: {candidate['source_record_id']}")
    text = str(row[str(adapter["text_column"])])
    require(sha256_text(text) == candidate["record_hash"], "selected source record hash mismatch")
    values = {name: row[name] for name in allowed[table]}
    if table == "literary_texts":
        author, work, year = values["author"], values["work"], values["year"]
        genre = values["genre"] or _dimension(adapter, row, "genre")
    elif table == "textbooks":
        author = values["author_uk"] or values["author"]
        work, year = values["title"], None
        genre = values["subject"] or "textbook"
    elif table == "external_articles":
        author, work, year = values["speaker"], values["title"], values["publish_date"]
        genre = "article_or_transcript"
    else:
        author, work, year, genre = None, values["title"], None, "encyclopedia"
    year_value: int | None = None
    if year not in {None, ""}:
        match = re.search(r"\d{4}", str(year))
        if match:
            year_value = int(match.group(0))
    return {
        "author": str(author) if author not in {None, ""} else None,
        "genre": str(genre) if genre not in {None, ""} else "unknown",
        "period": str(candidate["metadata"]["period"]),
        "register": str(candidate["metadata"]["register"]),
        "title": str(values.get("title") or work or "unknown"),
        "work": str(work) if work not in {None, ""} else None,
        "year": year_value,
    }


def _evidence_item(
    *,
    source: str,
    identity: str,
    query: str,
    status: str,
    evidence_type: str,
    supports: str,
    locator: str,
    period: str,
    register: str,
    content_sha256: str | None = None,
) -> dict[str, Any]:
    return {
        "content_sha256": content_sha256,
        "evidence_type": evidence_type,
        "locator": locator,
        "official_url": None,
        "parser_status": "not_applicable" if status != "attested" else "ok",
        "parser_version": None,
        "period": period,
        "query": query,
        "raw_payload_export_allowed": False,
        "register": register,
        "rights_posture": "bounded_internal_reference",
        "sense_groups": [],
        "source": source,
        "source_identity": identity,
        "status": status,
        "supports": supports,
    }


def _adapt_evidence(candidate: Mapping[str, Any], source_meta: Mapping[str, Any]) -> list[dict[str, Any]]:
    period, register = source_meta["period"], source_meta["register"]
    evidence = candidate["evidence"]
    items: list[dict[str, Any]] = []
    for index, token in enumerate(evidence["vesum"].get("tokens", [])):
        attested = bool(token.get("analyses"))
        items.append(
            _evidence_item(
                source="vesum",
                identity=str(evidence["vesum"].get("snapshot_id", "VESUM pinned snapshot")),
                query=str(token["surface"]),
                status="attested" if attested else "not_found",
                evidence_type="morphology",
                supports="ukrainian_attestation" if attested else "no_conclusion",
                locator=f"vesum://local/{index}/{sha256_text(str(token['surface']))}",
                period=period,
                register=register,
            )
        )
    for index, token in enumerate(evidence["russian_morphology"].get("tokens", [])):
        items.append(
            _evidence_item(
                source="russian_morphology",
                identity="check_ru_morph pinned local morphology",
                query=str(token["token"]),
                status="attested",
                evidence_type="morphology",
                supports="russian_attestation",
                locator=f"ru-morph://local/{index}/{sha256_text(str(token['token']))}",
                period=period,
                register=register,
            )
        )
    for index, lookup in enumerate(evidence["r2u"].get("lookups", [])):
        hit = lookup.get("status") == "hit"
        items.append(
            _evidence_item(
                source="r2u",
                identity=str(evidence["r2u"].get("cache_id", "bounded R2U cache")),
                query=str(lookup["query"]),
                status="attested" if hit else "incomplete",
                evidence_type="translation_equivalent",
                supports="alternative_candidate" if hit else "no_conclusion",
                locator=f"r2u-cache://{index}/{sha256_text(str(lookup['query']))}",
                period=period,
                register=register,
            )
        )
    for lookup_index, lookup in enumerate(evidence["heritage"].get("lookups", [])):
        for hit_index, hit in enumerate(lookup.get("hits", [])):
            items.append(
                _evidence_item(
                    source="heritage_dictionary",
                    identity=str(hit["dictionary_identity"]),
                    query=str(lookup["surface"]),
                    status="attested",
                    evidence_type="form",
                    supports="protected_variation",
                    locator=f"heritage://local/{lookup_index}/{hit_index}/{sha256_text(str(lookup['surface']))}",
                    period=period,
                    register=register,
                )
            )
    if not any(item["source"] == "heritage_dictionary" for item in items):
        items.append(
            _evidence_item(
                source="heritage_dictionary",
                identity="selected-row heritage lookup pending",
                query=candidate["span"]["original_text"],
                status="incomplete",
                evidence_type="form",
                supports="no_conclusion",
                locator=f"heritage-pending://{candidate['span']['span_hash']}",
                period=period,
                register=register,
            )
        )
    core_query = candidate["span"]["original_text"]
    # Required Ukrainian escalation sources remain explicitly incomplete until
    # bounded selected-row lookups occur.  Presence is not attestation.
    items.extend(
        [
            _evidence_item(
                source="ulif_dictua",
                identity="ULIF DictUA selected-row lookup pending",
                query=core_query,
                status="incomplete",
                evidence_type="synonym_group",
                supports="no_conclusion",
                locator=f"ulif-pending://{candidate['span']['span_hash']}",
                period=period,
                register=register,
            ),
            _evidence_item(
                source="slovnyk_me",
                identity="pending_dictionary",
                query=core_query,
                status="incomplete",
                evidence_type="definition",
                supports="no_conclusion",
                locator="https://slovnyk.me/dict/pending_dictionary/lookup-pending",
                period=period,
                register=register,
            ),
            _evidence_item(
                source="ukrainian_corpus",
                identity=str(candidate["source_family"]),
                query=core_query,
                status="attested",
                evidence_type="corpus_context",
                supports="context_only",
                locator=f"corpus-context://{candidate['span']['span_hash']}",
                period=period,
                register=register,
                content_sha256=candidate["span"]["span_hash"],
            ),
        ]
    )
    return items


def _candidate_layers(candidate: Mapping[str, Any]) -> list[str]:
    category = candidate["classification"]["category"]
    layers = {"language_span"}
    if category in {
        "modern_narration_interference",
        "mixed_surzhyk_candidate",
        "ukrainian_phonetic_russian",
    }:
        layers.add("russian_interference")
    if category in {"historical_unresolved", "protected_authentic_ukrainian"}:
        layers.add("protected_variation")
    for route in candidate["evidence"].get("valid_word_routes", []):
        route_type = str(route.get("route_type", ""))
        if "collocation" in route_type or "government" in route_type:
            layers.add("collocation_or_government")
        else:
            layers.add("semantic_calque")
    return sorted(layers)


def _views(candidate: Mapping[str, Any]) -> dict[str, str]:
    category = candidate["classification"]["category"]
    if category in {"historical_unresolved", "protected_authentic_ukrainian"}:
        modern, correction, preference = "protected", "protected", "protected"
    elif category in {"russian_quotation", "other_language"}:
        modern, correction, preference = "mask_span_from_loss", "not_applicable", "not_applicable"
    else:
        modern, correction, preference = "unresolved", "unresolved", "unresolved"
    return {
        "correction": correction,
        "evaluation": "excluded_from_non_evaluation_views",
        "faithful_literary": "retain_original",
        "modern_literary_ukrainian": modern,
        "preference": preference,
    }


def adapt_candidate(
    candidate: Mapping[str, Any],
    frame_item: Mapping[str, Any],
    *,
    source_meta: Mapping[str, Any],
    evaluation_registry: correction_factory.EvaluationRegistry,
) -> dict[str, Any]:
    context = candidate["span"]
    local_start = context["core_start_char"] - context["start_char"]
    local_end = context["core_end_char"] - context["start_char"]
    span_text = context["original_text"][local_start:local_end]
    classification = candidate["classification"]
    origin = "human_authored" if candidate["metadata"]["origin"] == "human_authored_source" else "unknown"
    contamination = correction_factory.contamination_states(
        context["original_text"],
        evaluation_registry,
        additional_sha256=(candidate["record_hash"],),
    )
    contamination["registry_artifact_sha256"] = {
        "v0_1_1_manifest": evaluation_registry.v011_manifest_sha256,
        "v0_2_packet": evaluation_registry.v02_packet_sha256,
    }
    reconstructions = []
    for item in candidate["evidence"].get("reconstruction_candidates", []):
        if item.get("validated") is not True:
            continue
        reconstructions.append(
            {
                "candidate": item["candidate"],
                "gate": "russian_anchor",
                "original_surface": item["original_surface"],
                "r2u": {"query": item["r2u_cache"]["query"], "status": "attested"},
                "russian_morphology": {
                    "lemma": item["ru_morph"]["lemma"],
                    "status": "attested",
                },
                "score": float(item["ru_morph"]["confidence"]),
                "transformation_path": item["transformation_path"],
            }
        )
    adapted = {
        "candidate_id": frame_item["candidate_id"],
        "candidate_layers": _candidate_layers(candidate),
        "detector": {
            "automatic_error_label": False,
            "kind": "combined",
            "model_output_used_as_gold": False,
            "producer": "ukrainian-foundry-language-contact-v1",
        },
        "evidence": _adapt_evidence(candidate, source_meta),
        "reconstructions": reconstructions,
        "review_state": "unresolved",
        "safety": {
            "contamination": contamination,
            "origin": "verified_human_authorship" if origin == "human_authored" else "unknown",
            "permitted_use": "investigation",
            "private_data": "unknown",
            "provenance": "incomplete",
            "rights": "unknown",
        },
        "schema_version": "correction_candidate_v1",
        "source": {
            "content_sha256": candidate["record_hash"],
            "context": {
                "end": context["end_char"],
                "sha256": context["span_hash"],
                "start": context["start_char"],
                "text": context["original_text"],
            },
            "genre": source_meta["genre"],
            "locator": candidate["locator"],
            "origin": origin,
            "period": source_meta["period"],
            "record_id": candidate["record_id"],
            "region": "unknown",
            "register": source_meta["register"],
            "source_family": candidate["source_family"],
            "source_record_id": candidate["source_record_id"],
        },
        "span": {
            "discourse_role": classification["discourse_role"],
            "downstream_disposition": classification["downstream_disposition"],
            "end": context["core_end_char"],
            "language_identity": classification["language_identity"],
            "representation": classification["representation"],
            "start": context["core_start_char"],
            "text": span_text,
        },
        "uncertainty": ["automatic detector route; requires two blind qualified Ukrainian-human reviews"],
        "upstream": {
            "candidate_schema_version": "language_contact_candidate_v1",
            "candidate_sha256": frame_item["candidate_sha256"],
            "profile_id": "ukrainian-foundry-language-contact-v1",
        },
        "views": _views(candidate),
    }
    return adapted


def _blind_item(
    candidate: Mapping[str, Any],
    frame_item: Mapping[str, Any],
    *,
    source_meta: Mapping[str, Any],
    packet_id: str,
    order: int,
) -> dict[str, Any]:
    span = candidate["span"]
    return {
        "blind_context": {
            "absolute_end_offset": span["end_char"],
            "absolute_start_offset": span["start_char"],
            "context_sha256": span["span_hash"],
            "core_sha256": sha256_text(
                span["original_text"][
                    span["core_start_char"] - span["start_char"] : span["core_end_char"] - span["start_char"]
                ]
            ),
            "relative_core_end_offset": span["core_end_char"] - span["start_char"],
            "relative_core_start_offset": span["core_start_char"] - span["start_char"],
            "text": span["original_text"],
        },
        "candidate_id": frame_item["candidate_id"],
        "candidate_sha256": frame_item["candidate_sha256"],
        "evidence_references": [],
        "hidden_authority": {
            "detector_output_included": False,
            "model_vote_included": False,
            "prior_label_included": False,
            "prior_reviewer_output_included": False,
        },
        "item_id": f"{packet_id}.item.{order:06d}",
        "order": order,
        "packet_id": packet_id,
        "review_form_seed": {
            "decision_options": [
                "correction",
                "acceptable_as_is",
                "protected_variation",
                "quoted_or_multilingual",
                "exclude",
                "unresolved",
            ],
            "discourse_role_options": [
                "narration",
                "quotation",
                "dialogue",
                "epigraph",
                "title",
                "citation_or_document",
                "metalinguistic_example",
                "unknown",
            ],
            "language_identity_options": [
                "ukrainian",
                "russian",
                "mixed_ukrainian_russian",
                "historical_east_slavic_unresolved",
                "church_slavonic_candidate",
                "other_language",
                "uncertain",
            ],
            "requires_evidence": True,
            "requires_rationale": True,
        },
        "schema_version": "language_contact_blind_review_item_v1",
        "source": {
            "author": source_meta["author"],
            "family": candidate["source_family"],
            "genre": source_meta["genre"],
            "locator_token_or_sha256": sha256_text(str(candidate["locator"])),
            "period": source_meta["period"],
            "register": source_meta["register"],
            "source_record_id_sha256": sha256_text(candidate["source_record_id"]),
            "work": source_meta["work"],
            "year": source_meta["year"],
        },
    }


def _salted_order(
    rows: Sequence[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]], salt: str
) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    return sorted(
        rows,
        key=lambda row: (
            sha256_text(f"{salt}\0{row[0]['candidate_id']}"),
            row[0]["candidate_id"],
        ),
    )


def _workspace_html(
    packet_id: str,
    rows: Sequence[Mapping[str, Any]],
    *,
    reviewer_id: str,
    resolver_mode: bool = False,
) -> bytes:
    """Build an offline workspace for a blind first pass or conflict resolver."""
    payload = base64.b64encode(canonical_json(list(rows)).encode("utf-8")).decode("ascii")
    template = """<!doctype html>
<html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title><style>
body{font-family:system-ui,sans-serif;max-width:920px;margin:auto;padding:24px;background:#f5f7fb;color:#172033}
main{background:white;padding:24px;border-radius:16px;box-shadow:0 8px 30px #17203318}mark{background:#ffe38a;padding:2px}
label{display:block;margin:14px 0 5px;font-weight:650}select,textarea,input{width:100%;box-sizing:border-box;padding:9px}
button{padding:10px 16px;margin:16px 8px 0 0}.meta{color:#53627a;font-size:.9rem}.progress{font-weight:700}
.profile{border:1px solid #ccd5e4;padding:16px;margin-bottom:20px;border-radius:10px}.error{color:#a40000;font-weight:700}
</style></head><body><main><h1>__TITLE__</h1>
<section class="profile"><h2>Профіль рецензента</h2><label>Ідентифікатор<input id="reviewer_id" readonly></label>
<label>Кваліфікація<select id="qualification"><option value="">— оберіть —</option><option value="native_or_near_native_ukrainian_editor">редактор — носій або майже носій української</option><option value="credentialed_ukrainian_linguist">дипломований український мовознавець</option><option value="qualified_ukrainian_language_reviewer">кваліфікований рецензент української мови</option></select></label>
<label>Підтвердження кваліфікації<textarea id="qualification_evidence"></textarea></label>
<label><input id="independence" type="checkbox" style="width:auto"> __INDEPENDENCE__</label></section>
<div class="progress" id="progress"></div><p class="meta" id="meta"></p><blockquote id="context"></blockquote><section id="prior" hidden><h2>Дві незалежні первинні оцінки</h2><pre id="prior_text"></pre></section>
<label>Рішення<select id="decision"><option value="">— оберіть —</option><option value="acceptable_as_is">прийнятно як є</option><option value="correction">потребує виправлення</option><option value="protected_variation">захищений історичний/діалектний/регіональний варіант</option><option value="quoted_or_multilingual">цитата або інша мова</option><option value="exclude">вилучити з навчального виду</option><option value="unresolved">не можу визначити</option></select></label>
<label>Мовна ідентичність<select id="language"><option value="ukrainian">Українська</option><option value="russian">Російська</option><option value="mixed_ukrainian_russian">Змішана українсько-російська</option><option value="historical_east_slavic_unresolved">Історична східнослов’янська — не визначено</option><option value="church_slavonic_candidate">Ймовірно церковнослов’янська</option><option value="other_language">Інша мова</option><option value="uncertain" selected>Не визначено</option></select></label>
<label>Репрезентація<select id="representation"><option value="standard_orthography">Стандартний правопис</option><option value="ukrainian_phonetic_rendering_of_russian">Українська фонетична передача російської</option><option value="historical_orthography">Історичний правопис</option><option value="transliteration">Транслітерація</option><option value="ocr_or_encoding_candidate">Ймовірна помилка OCR або кодування</option><option value="unknown" selected>Не визначено</option></select></label>
<label>Роль<select id="role"><option value="narration">Оповідь</option><option value="quotation">Цитата</option><option value="dialogue">Діалог</option><option value="epigraph">Епіграф</option><option value="title">Заголовок або назва</option><option value="citation_or_document">Цитування або документ</option><option value="metalinguistic_example">Метамовний приклад</option><option value="unknown" selected>Не визначено</option></select></label>
<label>Прийняте виправлення (лише для рішення «потребує виправлення»)<input id="correction"></label>
<label>Прийнятні альтернативи (по одному на рядок)<textarea id="alternatives"></textarea></label>
<label>Невпевненість / сумніви (щонайменше один рядок; якщо немає — «немає»)<textarea id="uncertainty"></textarea></label>
<h2>Подання у видах даних</h2><label>Сучасна літературна українська<select id="modern_view"><option value="retain_original">Зберегти оригінал</option><option value="mask_span_from_loss">Замаскувати фрагмент для обчислення втрат</option><option value="exclude_span_or_record">Вилучити фрагмент або запис</option><option value="protected">Захищена варіативність</option><option value="unresolved" selected>Не визначено</option></select></label>
<label>Корекційний вид<select id="correction_view"><option value="eligible_intake">Придатне до включення</option><option value="not_applicable">Не застосовується</option><option value="protected">Захищена варіативність</option><option value="unresolved" selected>Не визначено</option></select></label>
<label>Преференційний вид<select id="preference_view"><option value="eligible_intake">Придатне до включення</option><option value="not_applicable">Не застосовується</option><option value="protected">Захищена варіативність</option><option value="unresolved" selected>Не визначено</option></select></label>
<h2>Доказ</h2><label>Переглянуті джерела (по одному на рядок)<textarea id="evidence_viewed"></textarea></label>
<label>Тип цитованого джерела<select id="source_kind"><option value="primary_source">Першоджерело</option><option value="dictionary">Словник</option><option value="grammar">Граматика</option><option value="corpus">Корпус</option><option value="editorial_policy">Редакційна настанова</option><option value="other">Інше</option></select></label>
<label>Назва / ідентичність джерела<input id="source_identity"></label><label>Локатор (URL, стаття, сторінка)<input id="source_locator"></label>
<label>Що саме підтверджує джерело<textarea id="source_supports"></textarea></label><label>SHA-256 вмісту (необов'язково)<input id="source_sha256"></label>
<label>Обґрунтування<textarea id="rationale"></textarea></label><p class="error" id="error"></p>
<button id="save">Зберегти й далі</button><button id="back">Назад</button><button id="download">Завантажити відповіді JSONL</button></main>
<script>
const PACKET=__PACKET__,REVIEWER=__REVIEWER__,RESOLVER=__RESOLVER__,ITEMS=JSON.parse(new TextDecoder().decode(Uint8Array.from(atob('__PAYLOAD__'),c=>c.charCodeAt(0))));
let index=0,answers=JSON.parse(localStorage.getItem(PACKET)||'{}'),starts=JSON.parse(localStorage.getItem(PACKET+'.starts')||'{}');
const ids=['decision','language','representation','role','correction','alternatives','uncertainty','modern_view','correction_view','preference_view','evidence_viewed','source_kind','source_identity','source_locator','source_supports','source_sha256','rationale'];
const defaults={language:'uncertain',representation:'unknown',role:'unknown',modern_view:'unresolved',correction_view:'unresolved',preference_view:'unresolved',source_kind:'primary_source'};
document.getElementById('reviewer_id').value=REVIEWER;
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function lines(id){return [...new Set(document.getElementById(id).value.split('\n').map(x=>x.trim()).filter(Boolean))];}
function show(){const x=ITEMS[index],c=x.blind_context,t=c.text,a=c.relative_core_start_offset,b=c.relative_core_end_offset;document.getElementById('progress').textContent=`${index+1} / ${ITEMS.length}`;document.getElementById('meta').textContent=`${x.source.family} · ${x.source.period} · ${x.source.genre} · ${x.source.register} · ${x.source.author||''}`;document.getElementById('context').innerHTML=esc(t.slice(0,a))+'<mark>'+esc(t.slice(a,b))+'</mark>'+esc(t.slice(b));const prior=document.getElementById('prior');prior.hidden=!RESOLVER;if(RESOLVER)document.getElementById('prior_text').textContent=JSON.stringify(x.first_pass_projections,null,2);const old=answers[x.item_id]?answers[x.item_id].__form||{}:{};ids.forEach(id=>document.getElementById(id).value=old[id]??defaults[id]??'');if(!starts[x.item_id]){starts[x.item_id]=new Date().toISOString();localStorage.setItem(PACKET+'.starts',JSON.stringify(starts));}document.getElementById('error').textContent='';}
function save(){const x=ITEMS[index],form={};ids.forEach(id=>form[id]=document.getElementById(id).value.trim());const qualification=document.getElementById('qualification').value,qualificationEvidence=document.getElementById('qualification_evidence').value.trim(),independent=document.getElementById('independence').checked,evidence=lines('evidence_viewed'),uncertainty=lines('uncertainty');let errors=[];if(!qualification||!qualificationEvidence||!independent)errors.push('Заповніть профіль і підтвердьте незалежність.');if(!form.decision||!form.language||!form.representation||!form.role||!form.modern_view||!form.correction_view||!form.preference_view||!form.source_kind||!form.rationale||!evidence.length||!uncertainty.length||!form.source_identity||!form.source_locator||!form.source_supports)errors.push('Заповніть рішення, мовні осі, сумніви, доказ, подання у видах та обґрунтування.');if(form.decision==='correction'&&!form.correction)errors.push('Для виправлення потрібна прийнята форма.');if(form.decision!=='correction'&&form.correction)errors.push('Прийнята форма дозволена лише для виправлення.');if(form.source_sha256&&!/^[a-f0-9]{64}$/.test(form.source_sha256))errors.push('SHA-256 має містити 64 малі шістнадцяткові символи.');if(errors.length){document.getElementById('error').textContent=errors.join(' ');return;}const completed=new Date(),started=new Date(starts[x.item_id]);const response={schema_version:RESOLVER?'language_contact_resolver_response_v1':'language_contact_blind_response_v1',packet_id:PACKET,item_id:x.item_id,candidate_id:x.candidate_id,candidate_sha256:x.candidate_sha256,reviewer:{reviewer_id:REVIEWER,human:true,ukrainian_qualification:qualification,qualification_evidence:qualificationEvidence,independence_attested:true,test_fixture:false},process:{started_at:started.toISOString(),completed_at:completed.toISOString(),duration_seconds:Math.max(1,(completed-started)/1000),evidence_viewed:evidence,detector_output_exposed:false,prior_reviewer_output_exposed:RESOLVER},projection:{decision:form.decision,language_identity:form.language,representation:form.representation,discourse_role:form.role,accepted_correction:form.correction||null,acceptable_alternatives:lines('alternatives'),views:{faithful_literary:'retain_original',modern_literary_ukrainian:form.modern_view,correction:form.correction_view,preference:form.preference_view,evaluation:'excluded_from_non_evaluation_views'},uncertainty,citations:[{source_kind:form.source_kind,source_identity:form.source_identity,locator:form.source_locator,supports:form.source_supports,content_sha256:form.source_sha256||null}],rationale:form.rationale},__form:form};answers[x.item_id]=response;localStorage.setItem(PACKET,JSON.stringify(answers));if(index<ITEMS.length-1){index++;show();}}
document.getElementById('save').onclick=save;document.getElementById('back').onclick=()=>{if(index){index--;show();}};document.getElementById('download').onclick=()=>{const missing=ITEMS.filter(x=>!answers[x.item_id]);if(missing.length){document.getElementById('error').textContent=`Не заповнено: ${missing.length}.`;return;}const text=ITEMS.map(x=>{const value={...answers[x.item_id]};delete value.__form;return JSON.stringify(value);}).join('\n')+'\n';const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'application/x-ndjson'}));a.download=PACKET+'.responses.jsonl';a.click();};show();
</script></body></html>"""
    return (
        template.replace("__PACKET__", canonical_json(packet_id))
        .replace("__REVIEWER__", canonical_json(reviewer_id))
        .replace("__RESOLVER__", "true" if resolver_mode else "false")
        .replace(
            "__TITLE__",
            "Українське вирішення розбіжностей" if resolver_mode else "Українська експертна перевірка",
        )
        .replace(
            "__INDEPENDENCE__",
            (
                "Підтверджую незалежність: я не бачив/ла результату детектора; дві первинні оцінки показано лише для вирішення розбіжності."
                if resolver_mode
                else "Підтверджую незалежність: я не бачив/ла результату детектора й відповідей іншого рецензента."
            ),
        )
        .replace("__PAYLOAD__", payload)
        .encode("utf-8")
    )


def _artifact(path: Path, records: int) -> dict[str, Any]:
    return {"records": records, "sha256": sha256_file(path)}


def _artifact_with_bytes(path: Path, records: int) -> dict[str, Any]:
    return {
        "bytes": path.stat().st_size,
        "records": records,
        "sha256": sha256_file(path),
    }


def prepare_wave(
    *,
    candidates_path: Path,
    detector_receipt_path: Path,
    frame_path: Path,
    frame_receipt_path: Path,
    plan_path: Path,
    input_root: Path,
    stage: str,
    wave_number: int,
    prior_wave_receipt_paths: Sequence[Path],
    prior_selected_manifest_paths: Sequence[Path],
    salt_a: str,
    salt_b: str,
    selected_output: Path,
    correction_output: Path,
    blind_a_output: Path,
    blind_b_output: Path,
    workspace_a_output: Path,
    workspace_b_output: Path,
    receipt_output: Path,
) -> dict[str, Any]:
    """Prepare one approved, capacity-bounded blind calibration/production wave."""
    require(salt_a and salt_b and salt_a != salt_b, "two distinct non-empty packet salts are required")
    plan = read_json(plan_path)
    validate(plan, validator(SAMPLING_PLAN_SCHEMA), "sampling plan")
    frame_receipt = read_json(frame_receipt_path)
    validate(frame_receipt, validator(FRAME_RECEIPT_SCHEMA), "frame receipt")
    detector_receipt = read_json(detector_receipt_path)
    validate(detector_receipt, validator(DETECTOR_RECEIPT_SCHEMA), "detector receipt")
    require(sha256_file(frame_path) == frame_receipt["logical_frame_artifact"]["sha256"], "frame hash mismatch")
    require(plan["frame_sha256"] == frame_receipt["logical_frame_artifact"]["sha256"], "plan targets another frame")
    require(
        sha256_file(candidates_path) == detector_receipt["outputs"]["review_candidates"]["sha256"],
        "candidate stream differs from detector receipt",
    )
    excluded, prior_waves = _prior_wave_exclusions(
        receipt_paths=prior_wave_receipt_paths,
        selected_manifest_paths=prior_selected_manifest_paths,
        plan_path=plan_path,
        frame_path=frame_path,
        stage=stage,
        wave_number=wave_number,
    )
    selected = _select_frame_items(
        frame_path,
        plan=plan,
        stage=stage,
        excluded_candidate_ids=excluded,
    )
    salt_hashes = [sha256_text(salt_a), sha256_text(salt_b)]
    require(
        plan["packet_controls"]["first_pass_packet_salt_sha256"] == salt_hashes,
        "packet salts do not match the approved plan",
    )
    detector_config = read_json(DETECTOR_CONFIG)
    detector_candidate_validator = validator(DETECTOR_CANDIDATE_SCHEMA)
    correction_validator = validator(CORRECTION_CANDIDATE_SCHEMA)
    blind_validator = validator(BLIND_ITEM_SCHEMA)
    evaluation_registry = correction_factory.load_evaluation_registry()
    selected_rows: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    with candidates_path.open("rb") as candidates_handle:
        for frame_item in selected:
            candidate = _read_candidate_at(
                candidates_handle,
                frame_item,
                active_validator=detector_candidate_validator,
            )
            source_meta = _selected_source_metadata(
                candidate,
                detector_config=detector_config,
                input_root=input_root,
            )
            selected_rows.append((frame_item, candidate, source_meta))

    packet_root = f"{plan['plan_id']}.{stage}.{wave_number}"
    order_a = _salted_order(selected_rows, salt_a)
    order_b = _salted_order(selected_rows, salt_b)
    blind_a = [
        _blind_item(candidate, frame, source_meta=meta, packet_id=f"{packet_root}.a", order=index)
        for index, (frame, candidate, meta) in enumerate(order_a, 1)
    ]
    blind_b = [
        _blind_item(candidate, frame, source_meta=meta, packet_id=f"{packet_root}.b", order=index)
        for index, (frame, candidate, meta) in enumerate(order_b, 1)
    ]
    for item in [*blind_a, *blind_b]:
        validate(item, blind_validator, f"blind item {item['item_id']}")

    adapted: list[dict[str, Any]] = []
    for frame, candidate, meta in selected_rows:
        value = adapt_candidate(
            candidate,
            frame,
            source_meta=meta,
            evaluation_registry=evaluation_registry,
        )
        correction_factory.validate_candidate(
            value,
            validator=correction_validator,
            evaluation_registry=evaluation_registry,
        )
        adapted.append(value)

    outputs = {
        selected_output: b"".join((canonical_json(item) + "\n").encode("utf-8") for item in selected),
        correction_output: b"".join((canonical_json(item) + "\n").encode("utf-8") for item in adapted),
        blind_a_output: b"".join((canonical_json(item) + "\n").encode("utf-8") for item in blind_a),
        blind_b_output: b"".join((canonical_json(item) + "\n").encode("utf-8") for item in blind_b),
        workspace_a_output: _workspace_html(
            f"{packet_root}.a",
            blind_a,
            reviewer_id=plan["reviewer_capacity"]["first_pass_reviewer_ids"][0],
        ),
        workspace_b_output: _workspace_html(
            f"{packet_root}.b",
            blind_b,
            reviewer_id=plan["reviewer_capacity"]["first_pass_reviewer_ids"][1],
        ),
    }
    temporary: dict[Path, Path] = {}
    try:
        for output, payload in outputs.items():
            temporary[output] = _temporary_path(output)
            temporary[output].write_bytes(payload)
        selected_counts = Counter()
        for item in selected:
            selected_counts.update(item["calibration_strata"])
        artifact_rows = len(selected)
        receipt = {
            "adapted_correction_packet": _artifact(temporary[correction_output], artifact_rows),
            "claims": {
                "gold_created": False,
                "labels_created": False,
                "publication_performed": False,
                "training_performed": False,
            },
            "determinism": {
                "packet_ordering": "sha256(operator salt + NUL + candidate_id)",
                "selection_algorithm": "lowest deterministic rank per approved stratum; unique union",
                "timestamps_omitted": True,
            },
            "first_pass_blind_packets": [
                _artifact(temporary[blind_a_output], artifact_rows),
                _artifact(temporary[blind_b_output], artifact_rows),
            ],
            "frame_sha256": sha256_file(frame_path),
            "human_review_gate": {
                "human_review_completed": False,
                "qualified_reviewer_ids": [],
            },
            "input_sha256": sha256_file(candidates_path),
            "offline_html_workspaces": {
                "reviewer_a": _artifact_with_bytes(temporary[workspace_a_output], artifact_rows),
                "reviewer_b": _artifact_with_bytes(temporary[workspace_b_output], artifact_rows),
            },
            "packet_salt_sha256": salt_hashes,
            "per_stratum_selected_counts": dict(sorted(selected_counts.items())),
            "plan_sha256": sha256_file(plan_path),
            "prior_waves": prior_waves,
            "schema_version": "language_contact_wave_receipt_v1",
            "selected_manifest": _artifact(temporary[selected_output], artifact_rows),
            "stage": stage,
            "wave_number": wave_number,
        }
        validate(receipt, validator(WAVE_RECEIPT_SCHEMA), "wave receipt")
        temporary_receipt = _temporary_path(receipt_output)
        temporary_receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        promotions = [(temporary[output], output) for output in outputs]
        promotions.append((temporary_receipt, receipt_output))
        _promote_outputs(promotions)
        return receipt
    except Exception:
        for path in temporary.values():
            path.unlink(missing_ok=True)
        raise


def _unique_rows(
    path: Path,
    *,
    active_validator: Draft202012Validator,
    label: str,
    key: str,
    allow_empty: bool = False,
) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line_number, row in enumerate(iter_jsonl(path), 1):
        validate(row, active_validator, f"{label} line {line_number}")
        identifier = str(row[key])
        require(identifier not in rows, f"duplicate {label} {key}: {identifier}")
        rows[identifier] = row
    require(allow_empty or bool(rows), f"{label} is empty")
    return rows


def _validated_response_packet(
    *,
    blind_path: Path,
    responses_path: Path,
    expected_packet_id: str,
    expected_reviewer_id: str,
) -> dict[str, dict[str, Any]]:
    blind = _unique_rows(
        blind_path,
        active_validator=validator(BLIND_ITEM_SCHEMA),
        label="blind item",
        key="item_id",
    )
    responses = _unique_rows(
        responses_path,
        active_validator=validator(BLIND_RESPONSE_SCHEMA),
        label="blind response",
        key="item_id",
    )
    require(set(responses) == set(blind), "response packet does not exactly cover its blind packet")
    by_candidate: dict[str, dict[str, Any]] = {}
    reviewer_profile: str | None = None
    packet_ids = {item["packet_id"] for item in blind.values()}
    require(len(packet_ids) == 1, "blind packet contains multiple packet IDs")
    require(packet_ids == {expected_packet_id}, "blind packet ID does not match plan and stage")
    for item_id, response in responses.items():
        item = blind[item_id]
        require(response["packet_id"] == item["packet_id"], "response packet ID mismatch")
        require(response["candidate_id"] == item["candidate_id"], "response candidate ID mismatch")
        require(response["candidate_sha256"] == item["candidate_sha256"], "response candidate hash mismatch")
        require(
            response["reviewer"]["reviewer_id"] == expected_reviewer_id,
            "response reviewer does not match the approved plan",
        )
        encoded_reviewer = canonical_json(response["reviewer"])
        if reviewer_profile is None:
            reviewer_profile = encoded_reviewer
        require(encoded_reviewer == reviewer_profile, "reviewer profile changes inside one response packet")
        started = datetime.fromisoformat(response["process"]["started_at"].replace("Z", "+00:00"))
        completed = datetime.fromisoformat(response["process"]["completed_at"].replace("Z", "+00:00"))
        elapsed = (completed - started).total_seconds()
        require(elapsed > 0, "review completion must follow review start")
        require(
            abs(elapsed - float(response["process"]["duration_seconds"])) <= 0.01,
            "review duration does not match its timestamps",
        )
        candidate_id = str(response["candidate_id"])
        require(candidate_id not in by_candidate, f"duplicate response candidate: {candidate_id}")
        by_candidate[candidate_id] = response
    return by_candidate


def _review_from_response(response: Mapping[str, Any]) -> dict[str, Any]:
    # Timing, evidence-view, and blinding attestations remain in the validated
    # blind-response artifacts. The frozen correction decision v1 contract has
    # no process field, and a later conflict resolver must see prior reviews.
    return {
        "projection": response["projection"],
        "reviewer": response["reviewer"],
    }


def _unresolved_conflict_projection(
    first_a: Mapping[str, Any],
    first_b: Mapping[str, Any],
) -> dict[str, Any]:
    citations: list[dict[str, Any]] = []
    seen_citations: set[str] = set()
    for review in (first_a, first_b):
        for citation in review["projection"]["citations"]:
            encoded = canonical_json(citation)
            if encoded not in seen_citations:
                seen_citations.add(encoded)
                citations.append(dict(citation))
    return {
        "acceptable_alternatives": [],
        "accepted_correction": None,
        "citations": citations,
        "decision": "unresolved",
        "discourse_role": "unknown",
        "language_identity": "uncertain",
        "rationale": (
            "Two independent qualified Ukrainian-human first passes disagree; "
            "no linguistic conclusion is promoted before distinct third-human adjudication."
        ),
        "representation": "unknown",
        "uncertainty": ["unresolved first-pass conflict"],
        "views": {
            "correction": "unresolved",
            "evaluation": "excluded_from_non_evaluation_views",
            "faithful_literary": "retain_original",
            "modern_literary_ukrainian": "unresolved",
            "preference": "unresolved",
        },
    }


def _rate(numerator: int, denominator: int, confidence_level: float) -> dict[str, Any]:
    """Return an identified Wilson interval, preserving insufficient-data state."""
    if denominator == 0:
        return {"denominator": 0, "interval": None, "numerator": numerator, "value": None}
    value = numerator / denominator
    z = NormalDist().inv_cdf(0.5 + confidence_level / 2)
    z2 = z * z
    denominator_term = 1 + z2 / denominator
    center = (value + z2 / (2 * denominator)) / denominator_term
    margin = (
        z
        * ((value * (1 - value) / denominator + z2 / (4 * denominator * denominator)) ** 0.5)
        / denominator_term
    )
    return {
        "denominator": denominator,
        "interval": {
            "confidence_level": confidence_level,
            "lower": max(0.0, center - margin),
            "method": "wilson",
            "upper": min(1.0, center + margin),
        },
        "numerator": numerator,
        "value": value,
    }


def _metrics(counter: Counter[str], confidence_level: float) -> dict[str, Any]:
    reviewed = counter["reviewed"]
    return {
        "conflict_rate": _rate(counter["conflicts"], reviewed, confidence_level),
        "correction_yield_rate": _rate(counter["corrections"], reviewed, confidence_level),
        "decision_agreement": _rate(counter["decision_agreements"], reviewed, confidence_level),
        "adjudicative_core_agreement": _rate(counter["core_agreements"], reviewed, confidence_level),
        "reviewed": reviewed,
    }


def _first_pass_measurements(
    decisions: Sequence[Mapping[str, Any]],
    selected: Mapping[str, Mapping[str, Any]],
    confidence_level: float,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    overall: Counter[str] = Counter()
    by_stratum: dict[str, Counter[str]] = {stratum: Counter() for stratum in STRATA}
    for decision in decisions:
        first_a, first_b = decision["first_pass_reviews"]
        projection_a = first_a["projection"]
        projection_b = first_b["projection"]
        increments = Counter(
            {
                "conflicts": int(decision["final_resolution"]["kind"] == "unresolved_conflict"),
                "corrections": int(decision["final"]["decision"] == "correction"),
                "decision_agreements": int(projection_a["decision"] == projection_b["decision"]),
                "core_agreements": int(
                    correction_factory.adjudicative_core(projection_a)
                    == correction_factory.adjudicative_core(projection_b)
                ),
                "reviewed": 1,
            }
        )
        overall.update(increments)
        for stratum in selected[decision["candidate_id"]]["calibration_strata"]:
            by_stratum[stratum].update(increments)
    return (
        _metrics(overall, confidence_level),
        {stratum: _metrics(by_stratum[stratum], confidence_level) for stratum in STRATA},
    )


def assemble_first_pass_decisions(
    *,
    plan_path: Path,
    stage: str,
    wave_number: int,
    wave_receipt_path: Path,
    selected_manifest_path: Path,
    correction_packet_path: Path,
    blind_a_path: Path,
    blind_b_path: Path,
    responses_a_path: Path,
    responses_b_path: Path,
    decisions_output: Path,
    summary_output: Path,
) -> dict[str, Any]:
    """Validate two complete blind responses and preserve any conflict unresolved."""
    plan = read_json(plan_path)
    validate(plan, validator(SAMPLING_PLAN_SCHEMA), "sampling plan")
    _approved_targets(plan, stage)
    wave_receipt = read_json(wave_receipt_path)
    validate(wave_receipt, validator(WAVE_RECEIPT_SCHEMA), "wave receipt")
    require(wave_receipt["stage"] == stage, "wave receipt stage mismatch")
    require(wave_receipt["wave_number"] == wave_number, "wave receipt number mismatch")
    require(wave_receipt["plan_sha256"] == sha256_file(plan_path), "wave receipt plan mismatch")
    require(
        wave_receipt["selected_manifest"] == _artifact(
            selected_manifest_path,
            sum(1 for _ in iter_jsonl(selected_manifest_path)),
        ),
        "selected manifest does not match wave receipt",
    )
    require(
        wave_receipt["adapted_correction_packet"] == _artifact(
            correction_packet_path,
            sum(1 for _ in iter_jsonl(correction_packet_path)),
        ),
        "correction packet does not match wave receipt",
    )
    for label, path, expected in (
        ("blind A", blind_a_path, wave_receipt["first_pass_blind_packets"][0]),
        ("blind B", blind_b_path, wave_receipt["first_pass_blind_packets"][1]),
    ):
        require(
            expected == _artifact(path, sum(1 for _ in iter_jsonl(path))),
            f"{label} packet does not match wave receipt",
        )
    reviewer_ids = plan["reviewer_capacity"]["first_pass_reviewer_ids"]
    require(len(set(reviewer_ids)) == 2, "approved first-pass reviewers must be distinct")
    packet_root = f"{plan['plan_id']}.{stage}.{wave_number}"
    responses_a = _validated_response_packet(
        blind_path=blind_a_path,
        responses_path=responses_a_path,
        expected_packet_id=f"{packet_root}.a",
        expected_reviewer_id=reviewer_ids[0],
    )
    responses_b = _validated_response_packet(
        blind_path=blind_b_path,
        responses_path=responses_b_path,
        expected_packet_id=f"{packet_root}.b",
        expected_reviewer_id=reviewer_ids[1],
    )
    require(set(responses_a) == set(responses_b), "first-pass packets cover different candidates")
    selected = _unique_rows(
        selected_manifest_path,
        active_validator=validator(FRAME_ITEM_SCHEMA),
        label="selected frame item",
        key="candidate_id",
    )
    require(set(selected) == set(responses_a), "selected manifest and response packets cover different candidates")

    candidate_validator = validator(CORRECTION_CANDIDATE_SCHEMA)
    decision_validator = validator(CORRECTION_DECISION_SCHEMA)
    evaluation_registry = correction_factory.load_evaluation_registry()
    decisions: list[dict[str, Any]] = []
    seen_candidates: set[str] = set()
    counts = Counter()
    for candidate in iter_jsonl(correction_packet_path):
        correction_factory.validate_candidate(
            candidate,
            validator=candidate_validator,
            evaluation_registry=evaluation_registry,
        )
        candidate_id = str(candidate["candidate_id"])
        require(candidate_id not in seen_candidates, f"duplicate correction candidate: {candidate_id}")
        seen_candidates.add(candidate_id)
        require(candidate_id in responses_a, f"correction candidate missing first-pass responses: {candidate_id}")
        response_a = responses_a[candidate_id]
        response_b = responses_b[candidate_id]
        require(
            response_a["candidate_sha256"] == candidate["upstream"]["candidate_sha256"],
            "blind response does not bind the upstream detector candidate",
        )
        first = [_review_from_response(response_a), _review_from_response(response_b)]
        if correction_factory.first_pass_core_agreement(first):
            final = correction_factory.merge_first_pass_agreement(first)
            resolution = {"kind": "first_pass_agreement"}
            counts["first_pass_agreement"] += 1
        else:
            final = _unresolved_conflict_projection(first[0], first[1])
            resolution = {"kind": "unresolved_conflict"}
            counts["unresolved_conflict"] += 1
        decision = {
            "candidate_id": candidate_id,
            "candidate_sha256": sha256_text(correction_factory.canonical_json(candidate)),
            "final": final,
            "final_resolution": resolution,
            "first_pass_reviews": first,
            "review_state": "unresolved" if final["decision"] == "unresolved" else "adjudicated",
            "schema_version": "correction_reviewer_decision_v1",
        }
        correction_factory.validate_decision(
            decision,
            candidate,
            validator=decision_validator,
            allow_test_fixtures=False,
        )
        counts["adjudicated_rows" if decision["review_state"] == "adjudicated" else "unresolved_rows"] += 1
        decisions.append(decision)
    require(seen_candidates == set(responses_a), "responses include candidates absent from correction packet")
    temporary = _temporary_path(decisions_output)
    temporary_summary: Path | None = None
    try:
        temporary.write_bytes(b"".join((canonical_json(item) + "\n").encode("utf-8") for item in decisions))
        confidence_level = float(plan["statistical_stop"]["confidence_level"])
        overall, measured_strata = _first_pass_measurements(decisions, selected, confidence_level)
        summary = {
            "all_conflicts_resolved": counts["unresolved_conflict"] == 0,
            "decision_counts": dict(sorted(counts.items())),
            "decisions": _artifact(temporary, len(decisions)),
            "first_pass_review_completed": True,
            "frame_sha256": wave_receipt["frame_sha256"],
            "inputs": {
                "responses_a": _artifact(responses_a_path, len(responses_a)),
                "responses_b": _artifact(responses_b_path, len(responses_b)),
            },
            "overall": overall,
            "per_stratum": measured_strata,
            "plan_sha256": sha256_file(plan_path),
            "reviewer_ids": reviewer_ids,
            "schema_version": "language_contact_first_pass_summary_v1",
            "stage": stage,
            "wave_number": wave_number,
            "wave_receipt_sha256": sha256_file(wave_receipt_path),
        }
        validate(summary, validator(FIRST_PASS_SUMMARY_SCHEMA), "first-pass summary")
        temporary_summary = _temporary_path(summary_output)
        temporary_summary.write_text(canonical_json(summary) + "\n", encoding="utf-8")
        _promote_outputs(((temporary, decisions_output), (temporary_summary, summary_output)))
    finally:
        temporary.unlink(missing_ok=True)
        if temporary_summary is not None:
            temporary_summary.unlink(missing_ok=True)
    return summary


def prepare_resolver_packet(
    *,
    plan_path: Path,
    stage: str,
    wave_number: int,
    wave_receipt_path: Path,
    first_pass_summary_path: Path,
    decisions_path: Path,
    blind_a_path: Path,
    packet_output: Path,
    workspace_output: Path,
) -> dict[str, Any]:
    """Build a conflict-only packet for the predeclared distinct resolver."""
    plan = read_json(plan_path)
    validate(plan, validator(SAMPLING_PLAN_SCHEMA), "sampling plan")
    _approved_targets(plan, stage)
    wave_receipt = read_json(wave_receipt_path)
    validate(wave_receipt, validator(WAVE_RECEIPT_SCHEMA), "wave receipt")
    summary = read_json(first_pass_summary_path)
    validate(summary, validator(FIRST_PASS_SUMMARY_SCHEMA), "first-pass summary")
    require(summary["plan_sha256"] == sha256_file(plan_path), "first-pass summary plan mismatch")
    require(summary["wave_receipt_sha256"] == sha256_file(wave_receipt_path), "summary wave mismatch")
    require(
        (summary["stage"], summary["wave_number"]) == (stage, wave_number),
        "first-pass summary identity mismatch",
    )
    decisions = _unique_rows(
        decisions_path,
        active_validator=validator(CORRECTION_DECISION_SCHEMA),
        label="first-pass decision",
        key="candidate_id",
    )
    require(summary["decisions"] == _artifact(decisions_path, len(decisions)), "summary decisions mismatch")
    blind = _unique_rows(
        blind_a_path,
        active_validator=validator(BLIND_ITEM_SCHEMA),
        label="blind A item",
        key="candidate_id",
    )
    conflicts = [
        decision
        for decision in decisions.values()
        if decision["final_resolution"]["kind"] == "unresolved_conflict"
    ]
    require(all(item["candidate_id"] in blind for item in conflicts), "conflict absent from blind packet")
    packet_id = f"{plan['plan_id']}.{stage}.{wave_number}.resolver"
    rows: list[dict[str, Any]] = []
    for order, decision in enumerate(sorted(conflicts, key=lambda row: row["candidate_id"]), 1):
        source_item = dict(blind[decision["candidate_id"]])
        source_item.update(
            {
                "first_pass_projections": [
                    {"projection": review["projection"], "reviewer_slot": slot}
                    for slot, review in zip(("a", "b"), decision["first_pass_reviews"], strict=True)
                ],
                "hidden_authority": {
                    "detector_output_included": False,
                    "model_vote_included": False,
                    "prior_label_included": False,
                    "prior_reviewer_output_included": True,
                },
                "item_id": f"{packet_id}.item.{order:06d}",
                "order": order,
                "packet_id": packet_id,
                "schema_version": "language_contact_resolver_review_item_v1",
            }
        )
        rows.append(source_item)
    item_validator = validator(RESOLVER_ITEM_SCHEMA)
    for row in rows:
        validate(row, item_validator, f"resolver item {row['item_id']}")
    packet_bytes = b"".join((canonical_json(row) + "\n").encode("utf-8") for row in rows)
    workspace_bytes = (
        _workspace_html(
            packet_id,
            rows,
            reviewer_id=plan["reviewer_capacity"]["third_resolver_id"],
            resolver_mode=True,
        )
        if rows
        else "<!doctype html><html lang=\"uk\"><meta charset=\"utf-8\"><title>Розбіжностей немає</title><p>У цій хвилі немає розбіжностей для вирішення.</p></html>".encode()
    )
    temporary_packet = _temporary_path(packet_output)
    temporary_workspace = _temporary_path(workspace_output)
    try:
        temporary_packet.write_bytes(packet_bytes)
        temporary_workspace.write_bytes(workspace_bytes)
        receipt = {
            "claims": {"gold_created": False, "human_resolution_completed": False},
            "conflicts": len(rows),
            "first_pass_summary_sha256": sha256_file(first_pass_summary_path),
            "packet": _artifact(temporary_packet, len(rows)),
            "plan_sha256": sha256_file(plan_path),
            "resolver_id": plan["reviewer_capacity"]["third_resolver_id"],
            "schema_version": "language_contact_resolver_packet_receipt_v1",
            "stage": stage,
            "wave_number": wave_number,
            "workspace": _artifact_with_bytes(temporary_workspace, len(rows)),
        }
        _promote_outputs(((temporary_packet, packet_output), (temporary_workspace, workspace_output)))
    finally:
        temporary_packet.unlink(missing_ok=True)
        temporary_workspace.unlink(missing_ok=True)
    return receipt


def _validated_resolver_responses(
    *,
    packet_path: Path,
    responses_path: Path,
    resolver_id: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    packet = _unique_rows(
        packet_path,
        active_validator=validator(RESOLVER_ITEM_SCHEMA),
        label="resolver item",
        key="candidate_id",
        allow_empty=True,
    )
    responses = _unique_rows(
        responses_path,
        active_validator=validator(RESOLVER_RESPONSE_SCHEMA),
        label="resolver response",
        key="candidate_id",
        allow_empty=True,
    )
    require(set(packet) == set(responses), "resolver responses do not exactly cover the packet")
    profile: str | None = None
    for candidate_id, response in responses.items():
        item = packet[candidate_id]
        blind_projection = dict(item)
        blind_projection.pop("first_pass_projections")
        blind_projection["schema_version"] = "language_contact_blind_review_item_v1"
        blind_projection["hidden_authority"] = {
            **blind_projection["hidden_authority"],
            "prior_reviewer_output_included": False,
        }
        validate(
            blind_projection,
            validator(BLIND_ITEM_SCHEMA),
            f"resolver source item {item['item_id']}",
        )
        require(response["packet_id"] == item["packet_id"], "resolver packet ID mismatch")
        require(response["item_id"] == item["item_id"], "resolver item ID mismatch")
        require(response["candidate_sha256"] == item["candidate_sha256"], "resolver candidate hash mismatch")
        require(response["reviewer"]["reviewer_id"] == resolver_id, "unexpected conflict resolver")
        encoded = canonical_json(response["reviewer"])
        if profile is None:
            profile = encoded
        require(profile == encoded, "resolver profile changes inside one packet")
        started = datetime.fromisoformat(response["process"]["started_at"].replace("Z", "+00:00"))
        completed = datetime.fromisoformat(response["process"]["completed_at"].replace("Z", "+00:00"))
        elapsed = (completed - started).total_seconds()
        require(elapsed > 0, "resolver completion must follow start")
        require(
            abs(elapsed - float(response["process"]["duration_seconds"])) <= 0.01,
            "resolver duration does not match timestamps",
        )
    return packet, responses


def resolve_conflicts(
    *,
    plan_path: Path,
    packet_path: Path,
    responses_path: Path,
    decisions_path: Path,
    correction_packet_path: Path,
    decisions_output: Path,
    summary_output: Path,
) -> dict[str, Any]:
    """Apply distinct-human resolutions; unresolved resolver answers stay unresolved."""
    plan = read_json(plan_path)
    validate(plan, validator(SAMPLING_PLAN_SCHEMA), "sampling plan")
    _approved_targets(plan, "calibration")
    resolver_id = plan["reviewer_capacity"]["third_resolver_id"]
    packet, responses = _validated_resolver_responses(
        packet_path=packet_path,
        responses_path=responses_path,
        resolver_id=resolver_id,
    )
    decisions = _unique_rows(
        decisions_path,
        active_validator=validator(CORRECTION_DECISION_SCHEMA),
        label="first-pass decision",
        key="candidate_id",
    )
    candidates = _unique_rows(
        correction_packet_path,
        active_validator=validator(CORRECTION_CANDIDATE_SCHEMA),
        label="correction candidate",
        key="candidate_id",
    )
    require(set(decisions) == set(candidates), "decisions and correction candidates differ")
    expected_conflicts = {
        candidate_id
        for candidate_id, decision in decisions.items()
        if decision["final_resolution"]["kind"] == "unresolved_conflict"
    }
    require(set(packet) == expected_conflicts, "resolver packet is not the complete conflict set")
    decision_validator = validator(CORRECTION_DECISION_SCHEMA)
    counts = Counter()
    final_rows: list[dict[str, Any]] = []
    for candidate_id in candidates:
        decision = dict(decisions[candidate_id])
        if candidate_id in responses:
            response = responses[candidate_id]
            expected_projections = [review["projection"] for review in decision["first_pass_reviews"]]
            packet_projections = [item["projection"] for item in packet[candidate_id]["first_pass_projections"]]
            require(packet_projections == expected_projections, "resolver packet first-pass projections drifted")
            if response["projection"]["decision"] == "unresolved":
                counts["resolver_left_unresolved"] += 1
            else:
                third_review = {
                    "projection": response["projection"],
                    "reviewer": response["reviewer"],
                }
                decision["final"] = response["projection"]
                decision["final_resolution"] = {
                    "kind": "third_human_adjudication",
                    "third_review": third_review,
                }
                decision["review_state"] = "adjudicated"
                counts["third_human_adjudication"] += 1
        correction_factory.validate_decision(
            decision,
            candidates[candidate_id],
            validator=decision_validator,
            allow_test_fixtures=False,
        )
        counts[decision["review_state"]] += 1
        final_rows.append(decision)
    temporary_decisions = _temporary_path(decisions_output)
    temporary_summary = _temporary_path(summary_output)
    try:
        temporary_decisions.write_bytes(
            b"".join((canonical_json(row) + "\n").encode("utf-8") for row in final_rows)
        )
        summary = {
            "counts": dict(sorted(counts.items())),
            "decisions": _artifact(temporary_decisions, len(final_rows)),
            "input_decisions_sha256": sha256_file(decisions_path),
            "packet_sha256": sha256_file(packet_path),
            "plan_sha256": sha256_file(plan_path),
            "resolver_id": resolver_id,
            "responses_sha256": sha256_file(responses_path),
            "schema_version": "language_contact_resolution_summary_v1",
        }
        temporary_summary.write_text(canonical_json(summary) + "\n", encoding="utf-8")
        _promote_outputs(
            ((temporary_decisions, decisions_output), (temporary_summary, summary_output))
        )
    finally:
        temporary_decisions.unlink(missing_ok=True)
        temporary_summary.unlink(missing_ok=True)
    return summary


def summarize_campaign(
    *,
    plan_path: Path,
    first_pass_summary_paths: Sequence[Path],
    wave_receipt_paths: Sequence[Path],
    output_path: Path,
) -> dict[str, Any]:
    """Evaluate the frozen multi-wave stop rule without claiming gold."""
    require(
        len(first_pass_summary_paths) == len(wave_receipt_paths) and first_pass_summary_paths,
        "campaign summaries and wave receipts must be non-empty paired inputs",
    )
    plan = read_json(plan_path)
    validate(plan, validator(SAMPLING_PLAN_SCHEMA), "sampling plan")
    _approved_targets(plan, "calibration")
    plan_sha256 = sha256_file(plan_path)
    summaries: list[dict[str, Any]] = []
    wave_rows: list[dict[str, Any]] = []
    for summary_path, wave_receipt_path in zip(
        first_pass_summary_paths,
        wave_receipt_paths,
        strict=True,
    ):
        summary = read_json(summary_path)
        validate(summary, validator(FIRST_PASS_SUMMARY_SCHEMA), f"first-pass summary {summary_path}")
        wave_receipt = read_json(wave_receipt_path)
        validate(wave_receipt, validator(WAVE_RECEIPT_SCHEMA), f"wave receipt {wave_receipt_path}")
        require(summary["plan_sha256"] == plan_sha256, "first-pass summary uses another plan")
        require(wave_receipt["plan_sha256"] == plan_sha256, "wave receipt uses another plan")
        require(summary["frame_sha256"] == wave_receipt["frame_sha256"], "summary frame mismatch")
        require(
            summary["wave_receipt_sha256"] == sha256_file(wave_receipt_path),
            "summary does not bind its wave receipt",
        )
        require(
            (summary["stage"], summary["wave_number"])
            == (wave_receipt["stage"], wave_receipt["wave_number"]),
            "summary and wave receipt identity differ",
        )
        summaries.append(summary)
        wave_rows.append(
            {
                "stage": summary["stage"],
                "summary": _artifact(summary_path, 1),
                "wave_number": summary["wave_number"],
                "wave_receipt": _artifact(wave_receipt_path, 1),
            }
        )
    keys = [(row["stage"], row["wave_number"]) for row in wave_rows]
    expected_keys = [("calibration", 1)] + [
        ("production", number) for number in range(1, len(keys))
    ]
    require(keys == expected_keys, "campaign inputs must be calibration wave 1 then contiguous production waves")
    frame_sha256 = summaries[0]["frame_sha256"]
    require(all(row["frame_sha256"] == frame_sha256 for row in summaries), "campaign frame hash drifts")

    production = [row for row in summaries if row["stage"] == "production"]
    accumulated: dict[str, Counter[str]] = {stratum: Counter() for stratum in STRATA}
    for summary in production:
        for stratum in STRATA:
            metrics = summary["per_stratum"][stratum]
            accumulated[stratum].update(
                {
                    "conflicts": metrics["conflict_rate"]["numerator"],
                    "corrections": metrics["correction_yield_rate"]["numerator"],
                    "adjudicative_core_agreements": metrics["adjudicative_core_agreement"]["numerator"],
                    "reviewed": metrics["reviewed"],
                }
            )
    accumulated_payload = {
        stratum: {
            "conflicts": accumulated[stratum]["conflicts"],
            "corrections": accumulated[stratum]["corrections"],
            "adjudicative_core_agreements": accumulated[stratum]["adjudicative_core_agreements"],
            "reviewed": accumulated[stratum]["reviewed"],
        }
        for stratum in STRATA
    }

    stop = plan["statistical_stop"]
    required = int(stop["consecutive_stable_waves"])
    recent = production[-required:]
    category_minimum = int(stop["category_coverage_rule"]["minimum_reviewed_per_stratum"])
    category_coverage_met = bool(production) and all(
        accumulated[stratum]["reviewed"] >= category_minimum for stratum in STRATA
    )
    interval_width_met = len(recent) == required and all(
        metrics["adjudicative_core_agreement"]["interval"] is not None
        and metrics["adjudicative_core_agreement"]["interval"]["upper"]
        - metrics["adjudicative_core_agreement"]["interval"]["lower"]
        <= float(stop["maximum_interval_width"])
        for summary in recent
        for metrics in summary["per_stratum"].values()
    )
    consecutive_stability_met = len(recent) == required and all(
        abs(
            float(right["per_stratum"][stratum]["adjudicative_core_agreement"]["value"])
            - float(left["per_stratum"][stratum]["adjudicative_core_agreement"]["value"])
        )
        <= float(stop["maximum_consecutive_wave_change"])
        for left, right in pairwise(recent)
        for stratum in STRATA
        if left["per_stratum"][stratum]["adjudicative_core_agreement"]["value"] is not None
        and right["per_stratum"][stratum]["adjudicative_core_agreement"]["value"] is not None
    )
    if len(recent) == required:
        consecutive_stability_met = consecutive_stability_met and all(
            summary["per_stratum"][stratum]["adjudicative_core_agreement"]["value"] is not None
            for summary in recent
            for stratum in STRATA
        )
    learning_curve_met = len(recent) == required and all(
        abs(
            float(right["overall"]["correction_yield_rate"]["value"])
            - float(left["overall"]["correction_yield_rate"]["value"])
        )
        <= float(stop["learning_curve_rule"]["maximum_consecutive_wave_change"])
        for left, right in pairwise(recent)
        if left["overall"]["correction_yield_rate"]["value"] is not None
        and right["overall"]["correction_yield_rate"]["value"] is not None
    )
    if len(recent) == required:
        learning_curve_met = learning_curve_met and all(
            summary["overall"]["correction_yield_rate"]["value"] is not None
            for summary in recent
        )
    calibration_only = not production
    stop_eligible = all(
        (
            not calibration_only,
            category_coverage_met,
            interval_width_met,
            consecutive_stability_met,
            learning_curve_met,
        )
    )
    checks = (
        (calibration_only, "calibration_only"),
        (not category_coverage_met, "category_coverage_not_met"),
        (not interval_width_met, "interval_width_not_met"),
        (not consecutive_stability_met, "consecutive_stability_not_met"),
        (not learning_curve_met, "learning_curve_not_met"),
    )
    reasons = [reason for failed, reason in checks if failed]
    unresolved_conflicts = sum(
        int(summary["decision_counts"].get("unresolved_conflict", 0)) for summary in summaries
    )
    receipt = {
        "accumulated_per_stratum": accumulated_payload,
        "claims": {
            "campaign_complete": stop_eligible,
            "gold_frozen": False,
            "publication_performed": False,
            "training_performed": False,
        },
        "frame_sha256": frame_sha256,
        "plan_sha256": plan_sha256,
        "production_wave_count": len(production),
        "schema_version": "language_contact_campaign_receipt_v1",
        "stop_evaluation": {
            "calibration_only": calibration_only,
            "category_coverage_met": category_coverage_met,
            "consecutive_stability_met": consecutive_stability_met,
            "interval_width_met": interval_width_met,
            "learning_curve_met": learning_curve_met,
            "reasons": reasons,
            "stop_eligible": stop_eligible,
            "unresolved_conflicts": unresolved_conflicts,
        },
        "waves": wave_rows,
    }
    validate(receipt, validator(CAMPAIGN_RECEIPT_SCHEMA), "campaign receipt")
    temporary = _temporary_path(output_path)
    try:
        temporary.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        _promote_outputs(((temporary, output_path),))
    finally:
        temporary.unlink(missing_ok=True)
    return receipt


def freeze_gold(
    *,
    plan_path: Path,
    campaign_receipt_path: Path,
    wave_receipt_paths: Sequence[Path],
    first_pass_summary_paths: Sequence[Path],
    responses_a_paths: Sequence[Path],
    responses_b_paths: Sequence[Path],
    resolver_packet_paths: Sequence[Path],
    resolver_responses_paths: Sequence[Path],
    resolution_summary_paths: Sequence[Path],
    correction_packet_paths: Sequence[Path],
    final_decisions_paths: Sequence[Path],
    records_output: Path,
    factory_receipt_output: Path,
    freeze_receipt_output: Path,
) -> dict[str, Any]:
    """Freeze a complete stopped campaign without granting training/export eligibility."""
    inputs = (
        wave_receipt_paths,
        first_pass_summary_paths,
        responses_a_paths,
        responses_b_paths,
        resolver_packet_paths,
        resolver_responses_paths,
        resolution_summary_paths,
        correction_packet_paths,
        final_decisions_paths,
    )
    lengths = {len(paths) for paths in inputs}
    require(len(lengths) == 1 and next(iter(lengths), 0) >= 3, "gold freeze requires paired complete waves")
    plan = read_json(plan_path)
    validate(plan, validator(SAMPLING_PLAN_SCHEMA), "sampling plan")
    _approved_targets(plan, "calibration")
    campaign = read_json(campaign_receipt_path)
    validate(campaign, validator(CAMPAIGN_RECEIPT_SCHEMA), "campaign receipt")
    require(campaign["plan_sha256"] == sha256_file(plan_path), "campaign plan mismatch")
    require(campaign["stop_evaluation"]["stop_eligible"] is True, "campaign stop rule is not met")
    require(campaign["claims"]["campaign_complete"] is True, "campaign is not complete")
    wave_count = len(wave_receipt_paths)
    require(len(campaign["waves"]) == wave_count, "freeze wave count differs from campaign receipt")

    wave_evidence: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    seen_candidates: set[str] = set()
    campaign_counts: Counter[str] = Counter()
    for index in range(wave_count):
        wave_receipt_path = wave_receipt_paths[index]
        first_pass_summary_path = first_pass_summary_paths[index]
        correction_packet_path = correction_packet_paths[index]
        final_decisions_path = final_decisions_paths[index]
        wave_receipt = read_json(wave_receipt_path)
        validate(wave_receipt, validator(WAVE_RECEIPT_SCHEMA), "freeze wave receipt")
        summary = read_json(first_pass_summary_path)
        validate(summary, validator(FIRST_PASS_SUMMARY_SCHEMA), "freeze first-pass summary")
        campaign_wave = campaign["waves"][index]
        require(
            campaign_wave["wave_receipt"] == _artifact(wave_receipt_path, 1),
            "campaign wave receipt artifact mismatch",
        )
        require(
            campaign_wave["summary"] == _artifact(first_pass_summary_path, 1),
            "campaign first-pass summary artifact mismatch",
        )
        require(
            summary["inputs"]["responses_a"]
            == _artifact(responses_a_paths[index], len(_unique_rows(
                responses_a_paths[index],
                active_validator=validator(BLIND_RESPONSE_SCHEMA),
                label="freeze response A",
                key="candidate_id",
            ))),
            "response A artifact mismatch",
        )
        require(
            summary["inputs"]["responses_b"]
            == _artifact(responses_b_paths[index], len(_unique_rows(
                responses_b_paths[index],
                active_validator=validator(BLIND_RESPONSE_SCHEMA),
                label="freeze response B",
                key="candidate_id",
            ))),
            "response B artifact mismatch",
        )
        resolution_summary = read_json(resolution_summary_paths[index])
        require(
            resolution_summary.get("input_decisions_sha256") == summary["decisions"]["sha256"],
            "resolution summary does not bind first-pass decisions",
        )
        require(
            resolution_summary.get("packet_sha256") == sha256_file(resolver_packet_paths[index]),
            "resolution summary packet mismatch",
        )
        require(
            resolution_summary.get("responses_sha256") == sha256_file(resolver_responses_paths[index]),
            "resolution summary responses mismatch",
        )
        candidates = list(iter_jsonl(correction_packet_path))
        decisions = list(iter_jsonl(final_decisions_path))
        require(len(candidates) == len(decisions), "freeze candidate/decision count mismatch")
        require(
            resolution_summary.get("decisions") == _artifact(final_decisions_path, len(decisions)),
            "resolution summary final decisions mismatch",
        )
        for candidate, decision in zip(candidates, decisions, strict=True):
            candidate_id = candidate["candidate_id"]
            require(candidate_id == decision["candidate_id"], "freeze candidate/decision order mismatch")
            require(candidate_id not in seen_candidates, "candidate appears in multiple frozen waves")
            seen_candidates.add(candidate_id)
            campaign_counts[f"{wave_receipt['stage']}_records"] += 1
            campaign_counts[f"{wave_receipt['stage']}_{decision['review_state']}"] += 1
        candidate_rows.extend(candidates)
        decision_rows.extend(decisions)
        wave_evidence.append(
            {
                "correction_packet": _artifact(correction_packet_path, len(candidates)),
                "final_decisions": _artifact(final_decisions_path, len(decisions)),
                "first_pass_summary_sha256": sha256_file(first_pass_summary_path),
                "resolution_summary_sha256": sha256_file(resolution_summary_paths[index]),
                "resolver_packet_sha256": sha256_file(resolver_packet_paths[index]),
                "resolver_responses_sha256": sha256_file(resolver_responses_paths[index]),
                "responses_a_sha256": sha256_file(responses_a_paths[index]),
                "responses_b_sha256": sha256_file(responses_b_paths[index]),
                "stage": wave_receipt["stage"],
                "wave_number": wave_receipt["wave_number"],
                "wave_receipt_sha256": sha256_file(wave_receipt_path),
            }
        )

    combined_candidates = _temporary_path(records_output.with_name("combined-candidates.jsonl"))
    combined_decisions = _temporary_path(records_output.with_name("combined-decisions.jsonl"))
    temporary_records = _temporary_path(records_output)
    temporary_factory_receipt = _temporary_path(factory_receipt_output)
    temporary_freeze_receipt = _temporary_path(freeze_receipt_output)
    try:
        combined_candidates.write_bytes(
            b"".join((canonical_json(row) + "\n").encode("utf-8") for row in candidate_rows)
        )
        combined_decisions.write_bytes(
            b"".join((canonical_json(row) + "\n").encode("utf-8") for row in decision_rows)
        )
        evaluation_registry = correction_factory.load_evaluation_registry()
        factory_receipt = correction_factory.adjudicate(
            packet_path=combined_candidates,
            decisions_path=combined_decisions,
            records_output=temporary_records,
            receipt_output=temporary_factory_receipt,
            evaluation_registry=evaluation_registry,
            allow_test_fixtures=False,
        )
        records = list(iter_jsonl(temporary_records))
        totals = Counter()
        for record in records:
            totals[record["decision"]["review_state"]] += 1
            totals[f"decision_{record['decision']['final']['decision']}"] += 1
            totals["qualified_correction_intake"] += int(
                record["export_control"]["qualified_correction_intake"]
            )
        totals["records"] = len(records)
        totals.update(campaign_counts)
        totals["headline_gold"] = campaign_counts["production_adjudicated"]
        totals["calibration_evidence_non_gold"] = campaign_counts["calibration_records"]
        totals["unresolved_non_gold"] = totals["unresolved"]
        freeze_receipt = {
            "campaign_receipt_sha256": sha256_file(campaign_receipt_path),
            "claims": {
                "campaign_complete": True,
                "gold_frozen": True,
                "model_training_or_export_eligible": False,
                "publication_performed": False,
                "qualified_human_evidence": True,
                "training_performed": False,
            },
            "correction_factory_receipt": _artifact(temporary_factory_receipt, 1),
            "correction_records": _artifact(temporary_records, len(records)),
            "evaluation_registry": {
                "v0_1_1_manifest_sha256": evaluation_registry.v011_manifest_sha256,
                "v0_2_packet_sha256": evaluation_registry.v02_packet_sha256,
            },
            "plan_sha256": sha256_file(plan_path),
            "schema_version": "language_contact_gold_freeze_receipt_v1",
            "totals": dict(sorted(totals.items())),
            "waves": wave_evidence,
        }
        require(
            factory_receipt["output"] == freeze_receipt["correction_records"],
            "factory receipt and frozen records differ",
        )
        validate(freeze_receipt, validator(GOLD_FREEZE_RECEIPT_SCHEMA), "gold freeze receipt")
        temporary_freeze_receipt.write_text(canonical_json(freeze_receipt) + "\n", encoding="utf-8")
        _promote_outputs(
            (
                (temporary_records, records_output),
                (temporary_factory_receipt, factory_receipt_output),
                (temporary_freeze_receipt, freeze_receipt_output),
            )
        )
    finally:
        for path in (
            combined_candidates,
            combined_decisions,
            temporary_records,
            temporary_factory_receipt,
            temporary_freeze_receipt,
        ):
            path.unlink(missing_ok=True)
    return freeze_receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    frame = subparsers.add_parser("build-frame", help="stream a text-free sampling frame")
    frame.add_argument("--candidates", type=Path, required=True)
    frame.add_argument("--detector-receipt", type=Path, required=True)
    frame.add_argument("--frame-output", type=Path, required=True)
    frame.add_argument("--receipt-output", type=Path, required=True)

    draft = subparsers.add_parser("draft-plan", help="write a measured pending plan with no invented targets")
    draft.add_argument("--frame-receipt", type=Path, required=True)
    draft.add_argument("--plan-output", type=Path, required=True)
    draft.add_argument("--plan-id", required=True)
    draft.add_argument("--issue-url", required=True)

    wave = subparsers.add_parser("prepare-wave", help="prepare an approved blind wave")
    wave.add_argument("--candidates", type=Path, required=True)
    wave.add_argument("--detector-receipt", type=Path, required=True)
    wave.add_argument("--frame", type=Path, required=True)
    wave.add_argument("--frame-receipt", type=Path, required=True)
    wave.add_argument("--plan", type=Path, required=True)
    wave.add_argument("--input-root", type=Path, required=True)
    wave.add_argument("--stage", choices=("calibration", "production"), required=True)
    wave.add_argument("--wave-number", type=int, required=True)
    wave.add_argument("--prior-wave-receipt", type=Path, action="append", default=[])
    wave.add_argument("--prior-selected-manifest", type=Path, action="append", default=[])
    wave.add_argument("--salt-a-file", type=Path, required=True)
    wave.add_argument("--salt-b-file", type=Path, required=True)
    wave.add_argument("--selected-output", type=Path, required=True)
    wave.add_argument("--correction-output", type=Path, required=True)
    wave.add_argument("--blind-a-output", type=Path, required=True)
    wave.add_argument("--blind-b-output", type=Path, required=True)
    wave.add_argument("--workspace-a-output", type=Path, required=True)
    wave.add_argument("--workspace-b-output", type=Path, required=True)
    wave.add_argument("--receipt-output", type=Path, required=True)

    assemble = subparsers.add_parser(
        "assemble-first-pass",
        help="validate two blind human response packets and preserve conflicts unresolved",
    )
    assemble.add_argument("--plan", type=Path, required=True)
    assemble.add_argument("--stage", choices=("calibration", "production"), required=True)
    assemble.add_argument("--wave-number", type=int, required=True)
    assemble.add_argument("--wave-receipt", type=Path, required=True)
    assemble.add_argument("--selected-manifest", type=Path, required=True)
    assemble.add_argument("--correction-packet", type=Path, required=True)
    assemble.add_argument("--blind-a", type=Path, required=True)
    assemble.add_argument("--blind-b", type=Path, required=True)
    assemble.add_argument("--responses-a", type=Path, required=True)
    assemble.add_argument("--responses-b", type=Path, required=True)
    assemble.add_argument("--decisions-output", type=Path, required=True)
    assemble.add_argument("--summary-output", type=Path, required=True)

    campaign = subparsers.add_parser(
        "summarize-campaign",
        help="evaluate frozen coverage, uncertainty, stability, and learning-curve rules",
    )
    campaign.add_argument("--plan", type=Path, required=True)
    campaign.add_argument("--first-pass-summary", type=Path, action="append", required=True)
    campaign.add_argument("--wave-receipt", type=Path, action="append", required=True)
    campaign.add_argument("--output", type=Path, required=True)

    resolver = subparsers.add_parser(
        "prepare-resolver",
        help="build a conflict-only packet for the predeclared distinct resolver",
    )
    resolver.add_argument("--plan", type=Path, required=True)
    resolver.add_argument("--stage", choices=("calibration", "production"), required=True)
    resolver.add_argument("--wave-number", type=int, required=True)
    resolver.add_argument("--wave-receipt", type=Path, required=True)
    resolver.add_argument("--first-pass-summary", type=Path, required=True)
    resolver.add_argument("--decisions", type=Path, required=True)
    resolver.add_argument("--blind-a", type=Path, required=True)
    resolver.add_argument("--packet-output", type=Path, required=True)
    resolver.add_argument("--workspace-output", type=Path, required=True)

    resolve = subparsers.add_parser(
        "resolve-conflicts",
        help="validate the distinct resolver response and preserve unresolved answers",
    )
    resolve.add_argument("--plan", type=Path, required=True)
    resolve.add_argument("--packet", type=Path, required=True)
    resolve.add_argument("--responses", type=Path, required=True)
    resolve.add_argument("--decisions", type=Path, required=True)
    resolve.add_argument("--correction-packet", type=Path, required=True)
    resolve.add_argument("--decisions-output", type=Path, required=True)
    resolve.add_argument("--summary-output", type=Path, required=True)

    freeze = subparsers.add_parser(
        "freeze-gold",
        help="freeze one complete stopped campaign with real qualified-human evidence",
    )
    freeze.add_argument("--plan", type=Path, required=True)
    freeze.add_argument("--campaign-receipt", type=Path, required=True)
    freeze.add_argument("--wave-receipt", type=Path, action="append", required=True)
    freeze.add_argument("--first-pass-summary", type=Path, action="append", required=True)
    freeze.add_argument("--responses-a", type=Path, action="append", required=True)
    freeze.add_argument("--responses-b", type=Path, action="append", required=True)
    freeze.add_argument("--resolver-packet", type=Path, action="append", required=True)
    freeze.add_argument("--resolver-responses", type=Path, action="append", required=True)
    freeze.add_argument("--resolution-summary", type=Path, action="append", required=True)
    freeze.add_argument("--correction-packet", type=Path, action="append", required=True)
    freeze.add_argument("--final-decisions", type=Path, action="append", required=True)
    freeze.add_argument("--records-output", type=Path, required=True)
    freeze.add_argument("--factory-receipt-output", type=Path, required=True)
    freeze.add_argument("--freeze-receipt-output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build-frame":
            receipt = build_frame(
                candidates_path=args.candidates,
                detector_receipt_path=args.detector_receipt,
                frame_output=args.frame_output,
                receipt_output=args.receipt_output,
            )
        elif args.command == "draft-plan":
            receipt = draft_sampling_plan(
                frame_receipt_path=args.frame_receipt,
                plan_output=args.plan_output,
                plan_id=args.plan_id,
                issue_url=args.issue_url,
            )
        elif args.command == "prepare-wave":
            salt_a = read_secret(args.salt_a_file)
            salt_b = read_secret(args.salt_b_file)
            receipt = prepare_wave(
                candidates_path=args.candidates,
                detector_receipt_path=args.detector_receipt,
                frame_path=args.frame,
                frame_receipt_path=args.frame_receipt,
                plan_path=args.plan,
                input_root=args.input_root,
                stage=args.stage,
                wave_number=args.wave_number,
                prior_wave_receipt_paths=args.prior_wave_receipt,
                prior_selected_manifest_paths=args.prior_selected_manifest,
                salt_a=salt_a,
                salt_b=salt_b,
                selected_output=args.selected_output,
                correction_output=args.correction_output,
                blind_a_output=args.blind_a_output,
                blind_b_output=args.blind_b_output,
                workspace_a_output=args.workspace_a_output,
                workspace_b_output=args.workspace_b_output,
                receipt_output=args.receipt_output,
            )
        elif args.command == "assemble-first-pass":
            receipt = assemble_first_pass_decisions(
                plan_path=args.plan,
                stage=args.stage,
                wave_number=args.wave_number,
                wave_receipt_path=args.wave_receipt,
                selected_manifest_path=args.selected_manifest,
                correction_packet_path=args.correction_packet,
                blind_a_path=args.blind_a,
                blind_b_path=args.blind_b,
                responses_a_path=args.responses_a,
                responses_b_path=args.responses_b,
                decisions_output=args.decisions_output,
                summary_output=args.summary_output,
            )
        elif args.command == "summarize-campaign":
            receipt = summarize_campaign(
                plan_path=args.plan,
                first_pass_summary_paths=args.first_pass_summary,
                wave_receipt_paths=args.wave_receipt,
                output_path=args.output,
            )
        elif args.command == "prepare-resolver":
            receipt = prepare_resolver_packet(
                plan_path=args.plan,
                stage=args.stage,
                wave_number=args.wave_number,
                wave_receipt_path=args.wave_receipt,
                first_pass_summary_path=args.first_pass_summary,
                decisions_path=args.decisions,
                blind_a_path=args.blind_a,
                packet_output=args.packet_output,
                workspace_output=args.workspace_output,
            )
        elif args.command == "resolve-conflicts":
            receipt = resolve_conflicts(
                plan_path=args.plan,
                packet_path=args.packet,
                responses_path=args.responses,
                decisions_path=args.decisions,
                correction_packet_path=args.correction_packet,
                decisions_output=args.decisions_output,
                summary_output=args.summary_output,
            )
        else:
            receipt = freeze_gold(
                plan_path=args.plan,
                campaign_receipt_path=args.campaign_receipt,
                wave_receipt_paths=args.wave_receipt,
                first_pass_summary_paths=args.first_pass_summary,
                responses_a_paths=args.responses_a,
                responses_b_paths=args.responses_b,
                resolver_packet_paths=args.resolver_packet,
                resolver_responses_paths=args.resolver_responses,
                resolution_summary_paths=args.resolution_summary,
                correction_packet_paths=args.correction_packet,
                final_decisions_paths=args.final_decisions,
                records_output=args.records_output,
                factory_receipt_output=args.factory_receipt_output,
                freeze_receipt_output=args.freeze_receipt_output,
            )
    except (AdjudicationError, OSError, sqlite3.Error) as exc:
        print(f"language-contact-adjudication: {exc}", file=sys.stderr)
        return 2
    print(canonical_json(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
