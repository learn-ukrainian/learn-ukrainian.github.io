"""Build a deterministic, text-free VESUM-unattested occurrence sample.

This is an evidence-routing sampler.  A VESUM miss is a population-membership
fact only: it never becomes a correction or an error label.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import os
import sqlite3
import sys
import tempfile
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import document_signal_manifest as phase1
from scripts.projects.open_model_data import language_contact_detector as detector
from scripts.projects.open_model_data import profile_corpus as profile

CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECORD_SCHEMA = CONTRACTS / "vesum_unattested_sample_record_v1.schema.json"
RECEIPT_SCHEMA = CONTRACTS / "vesum_unattested_sample_receipt_v1.schema.json"
GENERATOR_PATH = Path(__file__).resolve()
DETECTOR_GENERATOR_PATH = Path(detector.__file__).resolve()
PRODUCTION_DENOMINATOR = 9_292_022
FAMILIES = ("literary", "public_textbooks", "external_articles", "wikipedia")
ALGORITHM = "phase3-stratified-largest-remainder-sha256-v1"
SELECTION_DOMAIN = "vesum-unattested-sample-selection-v1"
RANK_DOMAIN = "vesum-unattested-sample-rank-v1"
EVIDENCE_DOMAIN = "vesum-unattested-sample-evidence-v1"
COMPARISON_ALGORITHM = "independent-artifact-byte-identity-sha256-v1"
CLASSIFICATION_SAFETY_PRIORITY = {
    "legitimate_ukrainian_variation": 0,
    "historical_orthography": 1,
    "foreign_or_russian_quotation": 2,
    "proper_name": 3,
    "ocr_or_noise": 4,
    "phonetic_russian": 5,
    "plausible_modern_ukrainian_error": 6,
    "unresolved": 7,
}


class SampleError(ValueError):
    """The sample cannot be safely built or verified."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SampleError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SampleError(f"expected JSON object: {path}")
    return value


def _validator(path: Path) -> Draft202012Validator:
    schema = _read_json(path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _validate(value: Mapping[str, Any], validator: Draft202012Validator, label: str) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        where = ".".join(str(part) for part in error.path) or "<root>"
        raise SampleError(f"{label} schema failure at {where}: {error.message}")


def _stage(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except OSError:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _replace(temporary: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    os.replace(temporary, output)


def _load_config(path: Path) -> dict[str, Any]:
    config = _read_json(path)
    expected = {"schema_version", "expected_denominator", "family_quotas"}
    missing = expected - set(config)
    if missing or config.get("schema_version") != "vesum_unattested_sample_config_v1":
        raise SampleError("invalid sample config")
    denominator = config["expected_denominator"]
    quotas = config["family_quotas"]
    if type(denominator) is not int or denominator < 1:
        raise SampleError("expected_denominator must be a positive integer")
    if not isinstance(quotas, dict) or set(quotas) != set(FAMILIES):
        raise SampleError(f"family_quotas must name exactly {', '.join(FAMILIES)}")
    if any(type(value) is not int or value < 1 for value in quotas.values()):
        raise SampleError("family quotas must be positive integers")
    return config


def _phase1_rows(manifest_path: Path, receipt_path: Path) -> dict[str, dict[str, Any]]:
    try:
        phase1.verify_existing(manifest_path=manifest_path, receipt_path=receipt_path)
    except (phase1.ManifestError, OSError, json.JSONDecodeError) as exc:
        raise SampleError(f"invalid Phase 1 binding: {exc}") from exc
    rows: dict[str, dict[str, Any]] = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        record_id = row["record_id"]
        if record_id in rows:
            raise SampleError("duplicate Phase 1 record identity")
        rows[record_id] = row
    return rows


def _sample_identity(
    *, family: str, record: Mapping[str, Any], locator: str, start: int, end: int, surface_hash: str
) -> str:
    payload = [
        SELECTION_DOMAIN,
        family,
        record["record_id"],
        record["work_id"],
        record["source_id"],
        locator,
        start,
        end,
        record["content_sha256"],
        surface_hash,
    ]
    return _sha256_text(canonical_json(payload))


def _rank(sample_id: str) -> int:
    return int(_sha256_text(f"{RANK_DOMAIN}:{sample_id}"), 16)


def _largest_remainder(counts: Mapping[tuple[str, str, str], int], quota: int) -> dict[tuple[str, str, str], int]:
    total = sum(counts.values())
    if total < quota:
        raise SampleError(f"family has only {total} unattested occurrences for quota {quota}")
    allocated = {key: count * quota // total for key, count in counts.items()}
    remaining = quota - sum(allocated.values())
    remainders = sorted(
        ((-(count * quota % total), key) for key, count in counts.items()),
        key=lambda item: (item[0], item[1]),
    )
    for _remainder, key in remainders[:remaining]:
        allocated[key] += 1
    return allocated


def _detector_bucket(category: str) -> str:
    """Map only an existing detector category; any unknown/no-hit remains unresolved."""
    return {
        "ocr_or_encoding_candidate": "ocr_or_noise",
        "proper_name": "proper_name",
        "historical_unresolved": "historical_orthography",
        "russian_quotation": "foreign_or_russian_quotation",
        "other_language": "foreign_or_russian_quotation",
        "ukrainian_phonetic_russian": "phonetic_russian",
        "modern_narration_interference": "plausible_modern_ukrainian_error",
        "valid_word_contact_candidate": "unresolved",
        "protected_authentic_ukrainian": "legitimate_ukrainian_variation",
    }.get(category, "unresolved")


def _classification_for_record(
    *, text: str, source: Mapping[str, Any], phase1_row: Mapping[str, Any], locator: str,
    vesum_matches: Mapping[str, Sequence[Mapping[str, Any]]], detector_config: Mapping[str, Any], input_root: Path,
    selected: list[dict[str, Any]],
) -> dict[str, str]:
    """Run the incumbent detector once and route selected offsets only from its output."""
    try:
        candidates = detector.run_detector_on_text(
            text=text,
            record_id=str(phase1_row["record_id"]), locator=locator,
            source_family=str(source["source_family"]), source_record_id=str(phase1_row["record_id"]),
            period=str(phase1_row["dimensions"]["period"]), register=str(phase1_row["dimensions"]["register"]),
            origin=str(phase1_row["dimensions"]["origin"]), vesum_matches=vesum_matches,
            config=detector_config, input_root=input_root,
        )
    except (OSError, ValueError, sqlite3.Error):
        # A detector evidence-runtime failure cannot be promoted into a label.
        candidates = []
    detector_spans: list[tuple[int, int, str]] = []
    for candidate in candidates:
        span = candidate.get("span", {})
        classification = candidate.get("classification", {})
        if isinstance(span, Mapping) and isinstance(classification, Mapping):
            detector_spans.append(
                (int(span.get("core_start_char", -1)), int(span.get("core_end_char", -1)), str(classification.get("category", "")))
            )
    routed: dict[str, str] = {}
    for item in selected:
        categories = sorted(
            category for start, end, category in detector_spans if start <= item["start"] and item["end"] <= end
        )
        buckets = {_detector_bucket(category) for category in categories}
        routed[item["sample_id"]] = (
            min(buckets, key=lambda bucket: (CLASSIFICATION_SAFETY_PRIORITY[bucket], bucket))
            if buckets else "unresolved"
        )
    return routed


def _scan(
    *, profile_config: Mapping[str, Any], source_database: Path, vesum_database: Path,
    phase1_rows: Mapping[str, Mapping[str, Any]], quotas: Mapping[str, int],
) -> tuple[dict[tuple[str, str, str, str], int], dict[tuple[str, str, str, str], list[tuple[int, str, dict[str, Any]]]], int]:
    if not source_database.is_file() or not vesum_database.is_file():
        raise SampleError("source and VESUM databases must be readable files")
    stratum_counts: Counter[tuple[str, str, str, str]] = Counter()
    heaps: dict[tuple[str, str, str, str], list[tuple[int, str, dict[str, Any]]]] = defaultdict(list)
    denominator = 0
    scanned_rows = 0
    for source in profile_config["sources"]:
        family = str(source["source_family"])
        if family not in quotas:
            raise SampleError(f"profile contains unconfigured family: {family}")
        with profile._connect_read_only(source_database) as connection:
            query, parameters = profile._source_query(source, profile._table_columns(connection, source["adapter"]["table"]))
            cursor = connection.execute(query, parameters)
            for rows in profile._iter_batches(cursor, int(profile_config["record_batch_size"])):
                prepared: list[tuple[sqlite3.Row, str, list[Any]]] = []
                forms: set[str] = set()
                for row in rows:
                    text = str(row["__text"] or "")
                    tokens = detector.tokenize_with_offsets(text)
                    prepared.append((row, text, tokens))
                    forms.update(token.normalized for token in tokens)
                matches = profile._lookup_vesum(forms, database=vesum_database, batch_size=int(profile_config["vesum"]["batch_size"]))
                for row, text, tokens in prepared:
                    scanned_rows += 1
                    raw_id = str(row["__record_id"])
                    record_id = phase1._opaque_id(f"record.{family}", raw_id)
                    phase1_row = phase1_rows.get(record_id)
                    if phase1_row is None:
                        raise SampleError(f"missing Phase 1 stable record identity: {record_id}")
                    content_hash = _sha256_text(text)
                    if content_hash != phase1_row["content_sha256"]:
                        raise SampleError(f"Phase 1 content pin drift: {record_id}")
                    axes = phase1_row["dimensions"]
                    for axis in ("period", "genre", "register"):
                        if str(axes[axis]) != profile._dimension(row, source, axis):
                            raise SampleError(f"Phase 1 axis drift for {record_id}: {axis}")
                    locator_value = str(row["__locator"])
                    locator = f"sqlite:{source['adapter']['database']}#{source['adapter']['table']}/{locator_value}"
                    stratum = (family, str(axes["period"]), str(axes["genre"]), str(axes["register"]))
                    for token in tokens:
                        if matches.get(token.normalized):
                            continue
                        denominator += 1
                        stratum_counts[stratum] += 1
                        surface_hash = _sha256_text(token.surface)
                        sample_id = _sample_identity(
                            family=family, record=phase1_row, locator=locator, start=token.start_char,
                            end=token.end_char, surface_hash=surface_hash,
                        )
                        item = {
                            "sample_id": sample_id, "family": family, "record_id": record_id,
                            "locator": locator, "start": token.start_char, "end": token.end_char,
                            "surface_hash": surface_hash, "content_sha256": content_hash,
                            "phase1": phase1_row, "axes": {name: str(axes[name]) for name in ("period", "genre", "register")},
                        }
                        heap = heaps[stratum]
                        candidate = (-_rank(sample_id), sample_id, item)
                        if len(heap) < quotas[family]:
                            heapq.heappush(heap, candidate)
                        elif candidate > heap[0]:
                            heapq.heapreplace(heap, candidate)
    if scanned_rows != len(phase1_rows):
        raise SampleError(
            f"Phase 1 row coverage mismatch: manifest has {len(phase1_rows)}, scan processed {scanned_rows}"
        )
    return dict(stratum_counts), heaps, denominator


def _selected_records(
    *, counts: Mapping[tuple[str, str, str, str], int], heaps: Mapping[tuple[str, str, str, str], list[tuple[int, str, dict[str, Any]]]], quotas: Mapping[str, int],
) -> list[dict[str, Any]]:
    allocations: dict[tuple[str, str, str, str], int] = {}
    for family in FAMILIES:
        family_counts = {(period, genre, register): count for (name, period, genre, register), count in counts.items() if name == family}
        for key, allocated in _largest_remainder(family_counts, int(quotas[family])).items():
            allocations[(family, *key)] = allocated
    selected: list[dict[str, Any]] = []
    for stratum, allocated in sorted(allocations.items()):
        ranked = sorted((entry[2] for entry in heaps[stratum]), key=lambda item: (_rank(item["sample_id"]), item["sample_id"]))
        if len(ranked) < allocated:
            raise SampleError("bounded selection heap is incomplete")
        selected.extend(ranked[:allocated])
    if len(selected) != sum(quotas.values()):
        raise SampleError("stratified allocation did not meet total quota")
    return sorted(selected, key=lambda item: item["sample_id"])


def _classify_selected(
    *, selected: list[dict[str, Any]], profile_config: Mapping[str, Any], source_database: Path,
    vesum_database: Path, detector_config: Mapping[str, Any], detector_input_root: Path,
) -> dict[str, str]:
    targets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in selected:
        targets[item["record_id"]].append(item)
    routed: dict[str, str] = {}
    for source in profile_config["sources"]:
        family = str(source["source_family"])
        with profile._connect_read_only(source_database) as connection:
            query, parameters = profile._source_query(source, profile._table_columns(connection, source["adapter"]["table"]))
            for row in connection.execute(query, parameters):
                record_id = phase1._opaque_id(f"record.{family}", str(row["__record_id"]))
                relevant = targets.get(record_id)
                if not relevant:
                    continue
                text = str(row["__text"] or "")
                tokens = detector.tokenize_with_offsets(text)
                matches = profile._lookup_vesum((token.normalized for token in tokens), database=vesum_database, batch_size=int(profile_config["vesum"]["batch_size"]))
                locator = relevant[0]["locator"]
                routed.update(_classification_for_record(
                    text=text, source=source, phase1_row=relevant[0]["phase1"], locator=locator,
                    vesum_matches=matches, detector_config=detector_config, input_root=detector_input_root, selected=relevant,
                ))
    if set(routed) != {item["sample_id"] for item in selected}:
        raise SampleError("selected record could not be re-read for deterministic detector routing")
    return routed


def _record(item: Mapping[str, Any], classification: str, phase1_manifest_hash: str) -> dict[str, Any]:
    phase1_row = item["phase1"]
    return {
        "schema_version": "vesum_unattested_sample_record_v1",
        "sample_id": f"vesum_sample:{item['sample_id']}",
        "assurance_tier": "evidence_graded_non_gold", "authoritative": False,
        "source": {
            "record_id": phase1_row["record_id"], "work_id": phase1_row["work_id"], "source_id": phase1_row["source_id"],
            "revision_pin": f"phase1_manifest:{phase1_manifest_hash}", "locator": item["locator"],
            "content_sha256": item["content_sha256"],
            "source_axes": {"source_family": item["family"], **item["axes"]},
        },
        "span": {"start_offset": item["start"], "end_offset": item["end"], "surface_sha256": item["surface_hash"]},
        "classification": classification,
        "evidence_refs": [f"cp_evidence:{_sha256_text(canonical_json([EVIDENCE_DOMAIN, item['sample_id'], classification]))}"],
        "claim_boundary": {"human_gold": False, "human_reviewed": False, "text_published": False, "training_eligible": False},
    }


def build_sample(
    *, config_path: Path, profile_path: Path, profile_receipt_path: Path, phase1_manifest_path: Path,
    phase1_receipt_path: Path, source_database: Path, vesum_database: Path, detector_config_path: Path,
    output_path: Path, receipt_path: Path | None, comparison_output_path: Path | None,
    detector_input_root: Path = ROOT,
) -> dict[str, Any]:
    """Build and publish a sample only after matching an independent candidate."""
    if (receipt_path is None) != (comparison_output_path is None):
        raise SampleError("receipt and comparison output must be supplied together")
    if comparison_output_path is not None and comparison_output_path.resolve() == output_path.resolve():
        raise SampleError("comparison output must be a distinct independently built artifact")
    config = _load_config(config_path)
    profile_config = profile._load_and_validate_config(profile_path)
    profile_receipt = _read_json(profile_receipt_path)
    if profile_receipt.get("coverage", {}).get("complete") is not True:
        raise SampleError("profile receipt is incomplete")
    if profile_receipt.get("vesum", {}).get("tokens_unknown") != config["expected_denominator"]:
        raise SampleError("profile receipt unattested denominator does not match sample config")
    phase1_rows = _phase1_rows(phase1_manifest_path, phase1_receipt_path)
    if profile_receipt.get("coverage", {}).get("processed_rows") != len(phase1_rows):
        raise SampleError("profile receipt row count differs from Phase 1 manifest")
    detector_config = detector._load_and_validate_config(detector_config_path)
    counts, heaps, denominator = _scan(
        profile_config=profile_config, source_database=source_database, vesum_database=vesum_database,
        phase1_rows=phase1_rows, quotas=config["family_quotas"],
    )
    if denominator != config["expected_denominator"]:
        raise SampleError(f"unattested denominator mismatch: expected {config['expected_denominator']}, observed {denominator}")
    if int(config.get("production_expected_denominator", PRODUCTION_DENOMINATOR)) != PRODUCTION_DENOMINATOR:
        raise SampleError("production denominator pin must remain 9292022")
    selected = _selected_records(counts=counts, heaps=heaps, quotas=config["family_quotas"])
    classifications = _classify_selected(
        selected=selected, profile_config=profile_config, source_database=source_database, vesum_database=vesum_database,
        detector_config=detector_config, detector_input_root=detector_input_root,
    )
    manifest_hash = sha256_file(phase1_manifest_path)
    record_validator = _validator(RECORD_SCHEMA)
    records = [_record(item, classifications[item["sample_id"]], manifest_hash) for item in selected]
    for record in records:
        _validate(record, record_validator, "sample record")
    encoded = "".join(canonical_json(record) + "\n" for record in records).encode("utf-8")
    output_hash = hashlib.sha256(encoded).hexdigest()
    if comparison_output_path is None:
        temporary_output = _stage(output_path, encoded)
        try:
            _replace(temporary_output, output_path)
        finally:
            temporary_output.unlink(missing_ok=True)
        return {"logical_path": output_path.name, "records": len(records), "sha256": output_hash}
    try:
        comparison_bytes = comparison_output_path.read_bytes()
    except OSError as exc:
        raise SampleError(f"cannot read independent comparison output: {exc}") from exc
    comparison_hash = hashlib.sha256(comparison_bytes).hexdigest()
    if comparison_bytes != encoded:
        raise SampleError(
            "independent build mismatch: candidate and current output are not byte-identical"
        )
    family_counts = Counter(record["source"]["source_axes"]["source_family"] for record in records)
    category_counts = Counter(record["classification"] for record in records)
    pins = {
        "config_sha256": sha256_file(config_path), "database_sha256": sha256_file(source_database),
        "vesum_sha256": sha256_file(vesum_database), "profile_sha256": sha256_file(profile_path),
        "profile_receipt_sha256": sha256_file(profile_receipt_path), "phase1_manifest_sha256": manifest_hash,
        "phase1_receipt_sha256": sha256_file(phase1_receipt_path),
        "sampler_sha256": sha256_file(GENERATOR_PATH),
        "detector_config_sha256": sha256_file(detector_config_path),
        "detector_generator_sha256": sha256_file(DETECTOR_GENERATOR_PATH),
        "record_schema_sha256": sha256_file(RECORD_SCHEMA),
        "receipt_schema_sha256": sha256_file(RECEIPT_SCHEMA),
    }
    receipt = {
        "schema_version": "vesum_unattested_sample_receipt_v1", "denominator": denominator,
        "production_expected_denominator": PRODUCTION_DENOMINATOR, "pins": pins,
        "stratification": {"algorithm": ALGORITHM, "algorithm_sha256": _sha256_text(ALGORITHM), "quotas": dict(sorted(config["family_quotas"].items()))},
        "output": {"logical_path": output_path.name, "records": len(records), "sha256": output_hash},
        "sample_counts": dict(sorted({"total": len(records), **{f"family:{key}": value for key, value in family_counts.items()}, **{f"classification:{key}": value for key, value in category_counts.items()}}.items())),
        "sample_hashes": [record["sample_id"].split(":", 1)[1] for record in records],
        "coverage": dict(sorted({f"stratum:{'|'.join(key)}": value for key, value in counts.items()}.items())),
        "limitations": ["VESUM non-attestation is not an error label", "detector no-hit and unavailable evidence route to unresolved", "sample records contain no source text or raw external evidence"],
        "two_build_identity": {
            "comparison_algorithm": COMPARISON_ALGORITHM,
            "first_output": {"logical_path": comparison_output_path.name, "sha256": comparison_hash},
            "second_output": {"logical_path": output_path.name, "sha256": output_hash},
            "identical": True,
        },
        "safety": {"text_published": False, "training": False, "human_gold": False, "authoritative": False},
    }
    receipt_validator = _validator(RECEIPT_SCHEMA)
    _validate(receipt, receipt_validator, "sample receipt")
    temporary_output = _stage(output_path, encoded)
    try:
        _replace(temporary_output, output_path)
        if receipt_path is None:  # Guarded above; keeps the type checker honest.
            raise SampleError("receipt path is required for a compared build")
        temporary_receipt = _stage(receipt_path, (canonical_json(receipt) + "\n").encode("utf-8"))
        try:
            _replace(temporary_receipt, receipt_path)
        finally:
            temporary_receipt.unlink(missing_ok=True)
    finally:
        temporary_output.unlink(missing_ok=True)
    return receipt


def build_candidate(
    *, config_path: Path, profile_path: Path, profile_receipt_path: Path, phase1_manifest_path: Path,
    phase1_receipt_path: Path, source_database: Path, vesum_database: Path, detector_config_path: Path,
    output_path: Path, detector_input_root: Path = ROOT,
) -> dict[str, Any]:
    """Perform the first complete build without manufacturing a release receipt."""
    return build_sample(
        config_path=config_path, profile_path=profile_path,
        profile_receipt_path=profile_receipt_path, phase1_manifest_path=phase1_manifest_path,
        phase1_receipt_path=phase1_receipt_path, source_database=source_database,
        vesum_database=vesum_database, detector_config_path=detector_config_path,
        output_path=output_path, receipt_path=None, comparison_output_path=None,
        detector_input_root=detector_input_root,
    )


def verify_sample(
    *, config_path: Path, profile_path: Path, profile_receipt_path: Path, phase1_manifest_path: Path,
    phase1_receipt_path: Path, source_database: Path, vesum_database: Path, detector_config_path: Path,
    output_path: Path, receipt_path: Path,
) -> dict[str, Any]:
    """Validate all receipt pins and the complete text-free public artifact."""
    config = _load_config(config_path)
    receipt = _read_json(receipt_path)
    _validate(receipt, _validator(RECEIPT_SCHEMA), "sample receipt")
    expected_pins = {
        "config_sha256": sha256_file(config_path), "database_sha256": sha256_file(source_database),
        "vesum_sha256": sha256_file(vesum_database), "profile_sha256": sha256_file(profile_path),
        "profile_receipt_sha256": sha256_file(profile_receipt_path), "phase1_manifest_sha256": sha256_file(phase1_manifest_path),
        "phase1_receipt_sha256": sha256_file(phase1_receipt_path),
        "sampler_sha256": sha256_file(GENERATOR_PATH),
        "detector_config_sha256": sha256_file(detector_config_path),
        "detector_generator_sha256": sha256_file(DETECTOR_GENERATOR_PATH),
        "record_schema_sha256": sha256_file(RECORD_SCHEMA),
        "receipt_schema_sha256": sha256_file(RECEIPT_SCHEMA),
    }
    if receipt["pins"] != expected_pins:
        raise SampleError("receipt input pin drift")
    if receipt["denominator"] != config["expected_denominator"]:
        raise SampleError("receipt denominator differs from config")
    if _read_json(profile_receipt_path).get("vesum", {}).get("tokens_unknown") != config["expected_denominator"]:
        raise SampleError("profile receipt unattested denominator does not match sample config")
    if receipt["production_expected_denominator"] != PRODUCTION_DENOMINATOR:
        raise SampleError("receipt production denominator pin drift")
    digest, records, previous = hashlib.sha256(), [], ""
    validator = _validator(RECORD_SCHEMA)
    forbidden = {"text", "original_text", "surface_form", "raw_payload", "raw_evidence"}

    def contains_forbidden_key(value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(key in forbidden or contains_forbidden_key(nested) for key, nested in value.items())
        if isinstance(value, list):
            return any(contains_forbidden_key(nested) for nested in value)
        return False
    with output_path.open("rb") as handle:
        for line in handle:
            if not line.endswith(b"\n") or b"\r" in line:
                raise SampleError("output is not LF JSONL")
            digest.update(line)
            record = json.loads(line.decode("utf-8"))
            _validate(record, validator, "sample record")
            if contains_forbidden_key(record):
                raise SampleError("sample output contains text-bearing field")
            sample_id = record["sample_id"]
            if sample_id <= previous:
                raise SampleError("sample ordering is not deterministic")
            previous = sample_id
            records.append(record)
    if receipt["output"] != {"logical_path": output_path.name, "records": len(records), "sha256": digest.hexdigest()}:
        raise SampleError("sample output artifact drift")
    if receipt["sample_hashes"] != [record["sample_id"].split(":", 1)[1] for record in records]:
        raise SampleError("sample identity list drift")
    family_counts = Counter(record["source"]["source_axes"]["source_family"] for record in records)
    category_counts = Counter(record["classification"] for record in records)
    expected_counts = dict(sorted({
        "total": len(records),
        **{f"family:{key}": value for key, value in family_counts.items()},
        **{f"classification:{key}": value for key, value in category_counts.items()},
    }.items()))
    if receipt["sample_counts"] != expected_counts:
        raise SampleError("sample count drift")
    quotas = receipt["stratification"]["quotas"]
    if set(quotas) != set(FAMILIES) or any(family_counts.get(family, 0) != quota for family, quota in quotas.items()):
        raise SampleError("family quota coverage drift")
    identity = receipt["two_build_identity"]
    if identity["comparison_algorithm"] != COMPARISON_ALGORITHM:
        raise SampleError("two-build comparison algorithm drift")
    if identity["first_output"]["logical_path"] == identity["second_output"]["logical_path"]:
        raise SampleError("two-build identity does not name distinct artifacts")
    if identity["first_output"]["sha256"] != digest.hexdigest() or identity["second_output"] != {
        "logical_path": output_path.name,
        "sha256": digest.hexdigest(),
    }:
        raise SampleError("two-build identity hash drift")
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("candidate", "build", "verify"))
    for name in ("config", "profile", "profile-receipt", "phase1-manifest", "phase1-receipt", "source-database", "vesum-database", "detector-config", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--comparison-output", type=Path)
    parser.add_argument("--detector-input-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    values = {
        "config_path": args.config, "profile_path": args.profile, "profile_receipt_path": args.profile_receipt,
        "phase1_manifest_path": args.phase1_manifest, "phase1_receipt_path": args.phase1_receipt,
        "source_database": args.source_database, "vesum_database": args.vesum_database,
        "detector_config_path": args.detector_config, "output_path": args.output,
    }
    try:
        if args.mode == "candidate":
            if args.receipt is not None or args.comparison_output is not None:
                raise SampleError("candidate mode does not accept receipt or comparison output")
            result = build_candidate(**values, detector_input_root=args.detector_input_root)
        elif args.mode == "build":
            if args.receipt is None or args.comparison_output is None:
                raise SampleError("build mode requires --receipt and --comparison-output")
            result = build_sample(
                **values, receipt_path=args.receipt, comparison_output_path=args.comparison_output,
                detector_input_root=args.detector_input_root,
            )
        else:
            if args.receipt is None or args.comparison_output is not None:
                raise SampleError("verify mode requires --receipt and rejects --comparison-output")
            result = verify_sample(**values, receipt_path=args.receipt)
    except (SampleError, OSError, sqlite3.Error, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
