#!/usr/bin/env python3
"""Build deterministic Ukrainian correction-review packets and adjudications.

This module is an intake and control boundary.  It validates span/evidence
records, binds them to the frozen evaluation inventories, enforces qualified
human review, and writes non-exportable correction records.  It never turns a
detector result into gold and never produces a model-training export.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
import unicodedata
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
CANDIDATE_SCHEMA_PATH = CONTRACTS / "correction_candidate_v1.schema.json"
DECISION_SCHEMA_PATH = CONTRACTS / "correction_reviewer_decision_v1.schema.json"
RECORD_SCHEMA_PATH = CONTRACTS / "correction_record_v1.schema.json"
RECEIPT_SCHEMA_PATH = CONTRACTS / "correction_factory_receipt_v1.schema.json"
SCHEMA_PATHS = (
    CANDIDATE_SCHEMA_PATH,
    DECISION_SCHEMA_PATH,
    RECORD_SCHEMA_PATH,
    RECEIPT_SCHEMA_PATH,
)
DEFAULT_EVALUATION_MANIFEST = (
    ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json"
)
DEFAULT_V02_PACKET = (
    ROOT / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl"
)

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
SLOVNYK_DICTIONARY_LOCATOR_RE = re.compile(
    r"^https://slovnyk\.me/dict/(?P<dictionary_slug>[A-Za-z0-9_-]+)/.+$"
)
NEAR_DUPLICATE_THRESHOLD = 0.90
MIN_CONTAINMENT_CHARACTERS = 32
PROTECTED_PERIOD_MARKERS = (
    "historical",
    "middle_ukrainian",
    "old_east_slavic",
    "archaic",
)
PROTECTED_REGISTER_MARKERS = (
    "dialect",
    "folk",
    "heritage",
    "regional",
    "archaic",
    "rare",
    "slang",
    "marked",
)
UKRAINIAN_ESCALATION_SOURCES = frozenset(
    {"ulif_dictua", "heritage_dictionary", "slovnyk_me", "ukrainian_corpus"}
)


class FactoryError(ValueError):
    """A packet, review, or safety state violates the correction contract."""


@dataclass(frozen=True)
class EvaluationRegistry:
    """Frozen source fingerprints used to prevent evaluation contamination."""

    v011_exact: frozenset[str]
    v011_texts: tuple[str, ...]
    v02_exact: frozenset[str]
    v02_texts: tuple[str, ...]
    v011_manifest_sha256: str
    v02_packet_sha256: str

    @property
    def source_fingerprint_count(self) -> int:
        return len(self.v011_exact | self.v02_exact)


def canonical_json(value: Any) -> str:
    """Return the byte-stable JSON representation used by every artifact."""
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


def normalize_evaluation_text(value: str) -> str:
    """Normalize only for duplicate comparison; never mutate source payloads."""
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FactoryError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FactoryError(f"expected JSON object: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load non-empty JSONL records with attributable line failures."""
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise FactoryError(f"cannot read JSONL {path}: {exc}") from exc
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FactoryError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise FactoryError(f"expected object at {path}:{line_number}")
        rows.append(row)
    return rows


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FactoryError(message)


def _schema_bundle() -> tuple[dict[Path, dict[str, Any]], Registry]:
    schemas = {path: _read_json(path) for path in SCHEMA_PATHS}
    registry = Registry()
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(
            str(schema["$id"]), Resource.from_contents(schema)
        )
    return schemas, registry


def _validator(
    path: Path,
    *,
    schemas: Mapping[Path, dict[str, Any]],
    registry: Registry,
) -> Draft202012Validator:
    return Draft202012Validator(schemas[path], registry=registry)


def _validate_schema(
    value: Mapping[str, Any],
    validator: Draft202012Validator,
    *,
    label: str,
) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if errors:
        path = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise FactoryError(f"{label} schema violation at {path}: {errors[0].message}")


def _expanded_manifest_sources(manifest: Mapping[str, Any]) -> list[tuple[str, str]]:
    layout = manifest.get("record_layouts", {}).get("item")
    items = manifest.get("items")
    _require(isinstance(layout, list) and isinstance(items, list), "invalid evaluation manifest layout")
    _require("source" in layout and "source_sha256" in layout, "evaluation manifest lacks source fields")
    source_index = layout.index("source")
    hash_index = layout.index("source_sha256")
    result: list[tuple[str, str]] = []
    for row in items:
        _require(isinstance(row, list) and len(row) == len(layout), "invalid evaluation manifest item")
        source, source_hash = row[source_index], row[hash_index]
        _require(isinstance(source, str) and isinstance(source_hash, str), "invalid evaluation source")
        _require(sha256_text(source) == source_hash, "evaluation source hash mismatch")
        result.append((source, source_hash))
    return result


def _v02_sources(rows: Sequence[Mapping[str, Any]]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for row in rows:
        blind = row.get("blind_reviewer_view")
        receipts = row.get("frozen_receipts")
        _require(isinstance(blind, Mapping) and isinstance(receipts, Mapping), "invalid v0.2 packet row")
        source, source_hash = blind.get("source"), receipts.get("source_sha256")
        _require(isinstance(source, str) and isinstance(source_hash, str), "invalid v0.2 source")
        _require(sha256_text(source) == source_hash, "v0.2 source hash mismatch")
        result.append((source, source_hash))
        references = blind.get("references")
        _require(isinstance(references, list), "invalid v0.2 reference list")
        for reference in references:
            _require(isinstance(reference, list) and len(reference) >= 3, "invalid v0.2 reference")
            text, reference_hash = reference[1], reference[2]
            _require(isinstance(text, str) and isinstance(reference_hash, str), "invalid v0.2 reference fields")
            _require(sha256_text(text) == reference_hash, "v0.2 reference hash mismatch")
            result.append((text, reference_hash))
    return result


def load_evaluation_registry(
    *,
    v011_manifest_path: Path = DEFAULT_EVALUATION_MANIFEST,
    v02_packet_path: Path = DEFAULT_V02_PACKET,
) -> EvaluationRegistry:
    """Load v0.1.1 and v0.2 source/gold fingerprints fail closed."""
    v011_rows = _expanded_manifest_sources(_read_json(v011_manifest_path))
    v02_rows_raw = read_jsonl(v02_packet_path)
    _require(v02_rows_raw, "empty v0.2 review packet")
    v02_rows = _v02_sources(v02_rows_raw)
    return EvaluationRegistry(
        v011_exact=frozenset(item[1] for item in v011_rows),
        v011_texts=tuple(sorted({normalize_evaluation_text(item[0]) for item in v011_rows})),
        v02_exact=frozenset(item[1] for item in v02_rows),
        v02_texts=tuple(sorted({normalize_evaluation_text(item[0]) for item in v02_rows})),
        v011_manifest_sha256=sha256_file(v011_manifest_path),
        v02_packet_sha256=sha256_file(v02_packet_path),
    )


def _near_duplicate(text: str, reference_texts: Sequence[str]) -> bool:
    normalized = normalize_evaluation_text(text)
    if not normalized:
        return False
    for reference in reference_texts:
        if normalized == reference:
            return True
        if min(len(normalized), len(reference)) >= MIN_CONTAINMENT_CHARACTERS and (
            normalized in reference or reference in normalized
        ):
            return True
        length_ratio = min(len(normalized), len(reference)) / max(len(normalized), len(reference))
        if length_ratio < NEAR_DUPLICATE_THRESHOLD:
            continue
        if SequenceMatcher(None, normalized, reference, autojunk=False).ratio() >= NEAR_DUPLICATE_THRESHOLD:
            return True
    return False


def contamination_states(
    text: str,
    registry: EvaluationRegistry,
    *,
    additional_sha256: Sequence[str] = (),
) -> dict[str, str]:
    """Compute exact and near-duplicate dispositions for one bounded context."""
    exact_hashes = {sha256_text(text), *additional_sha256}
    _require(
        all(SHA256_RE.fullmatch(value) for value in exact_hashes),
        "invalid additional contamination hash",
    )
    return {
        "v0_1_1_exact": "match" if exact_hashes & registry.v011_exact else "clear",
        "v0_1_1_near": "match" if _near_duplicate(text, registry.v011_texts) else "clear",
        "v0_2_exact": "match" if exact_hashes & registry.v02_exact else "clear",
        "v0_2_near": "match" if _near_duplicate(text, registry.v02_texts) else "clear",
    }


def _is_protected(candidate: Mapping[str, Any]) -> bool:
    source = candidate["source"]
    span = candidate["span"]
    period = str(source["period"]).casefold()
    register = str(source["register"]).casefold()
    return (
        any(marker in period for marker in PROTECTED_PERIOD_MARKERS)
        or any(marker in register for marker in PROTECTED_REGISTER_MARKERS)
        or "protected_variation" in candidate["candidate_layers"]
        or span["language_identity"] in {
            "historical_east_slavic_unresolved",
            "church_slavonic_candidate",
        }
        or span["downstream_disposition"]
        == "protected_historical_or_register_variation"
    )


def _validate_evidence(candidate: Mapping[str, Any]) -> None:
    evidence = candidate["evidence"]
    sources = {item["source"] for item in evidence}
    identities = {(item["source"], item["source_identity"], item["locator"]) for item in evidence}
    _require(len(identities) == len(evidence), "duplicate source-specific evidence")

    vesum_miss = any(
        item["source"] == "vesum" and item["status"] == "not_found"
        for item in evidence
    )
    if vesum_miss:
        missing = sorted(UKRAINIAN_ESCALATION_SOURCES - sources)
        _require(not missing, f"VESUM miss lacks Ukrainian escalation sources: {', '.join(missing)}")

    for item in evidence:
        if item["source"] == "slovnyk_me":
            locator_match = SLOVNYK_DICTIONARY_LOCATOR_RE.fullmatch(item["locator"])
            _require(
                locator_match is not None,
                "slovnyk.me evidence requires a per-dictionary /dict/<slug>/ locator",
            )
            _require(
                item["source_identity"].casefold()
                == locator_match.group("dictionary_slug").casefold(),
                "slovnyk.me source identity must equal the underlying dictionary slug",
            )
            _require(not item["raw_payload_export_allowed"], "slovnyk.me raw payload cannot enter the packet")
        if item["source"] == "ulif_dictua":
            _require(not item["raw_payload_export_allowed"], "ULIF raw payload cannot enter the packet")
            if item["status"] == "attested":
                _require(item["parser_status"] == "ok", "attested ULIF evidence requires parser status ok")
                _require(item["content_sha256"] is not None, "attested ULIF evidence requires a content hash")
            if item["evidence_type"] == "synonym_group" and item["status"] == "attested":
                _require(item["sense_groups"], "ULIF synonym evidence lacks sense groups")

    phonetic = candidate["span"]["representation"] == "ukrainian_phonetic_rendering_of_russian"
    reconstructions = candidate["reconstructions"]
    _require(phonetic == bool(reconstructions), "phonetic-Russian classification and reconstructions must agree")
    for reconstruction in reconstructions:
        _require(
            reconstruction["original_surface"] in candidate["span"]["text"],
            "reconstruction surface is absent from the preserved span",
        )

    if "russian_interference" in candidate["candidate_layers"]:
        _require("r2u" in sources and "russian_morphology" in sources, "Russian-interference candidate lacks r2u or morphology evidence")

    shared_form_only = (
        any(item["source"] == "vesum" and item["status"] == "attested" for item in evidence)
        and any(item["source"] == "r2u" and item["status"] == "attested" for item in evidence)
        and sources <= {"vesum", "r2u", "russian_morphology"}
        and not reconstructions
        and not phonetic
    )
    if shared_form_only:
        _require(candidate["span"]["language_identity"] == "uncertain", "bare r2u hit cannot decide a shared form")
        _require(candidate["views"]["correction"] == "unresolved", "shared form must remain unresolved")


def validate_candidate(
    candidate: Mapping[str, Any],
    *,
    validator: Draft202012Validator,
    evaluation_registry: EvaluationRegistry,
) -> None:
    """Validate schema, offsets, evidence routing, views, and safety joins."""
    _validate_schema(candidate, validator, label="correction candidate")
    source = candidate["source"]
    context = source["context"]
    span = candidate["span"]
    _require(context["end"] - context["start"] == len(context["text"]), "context offsets do not match text")
    _require(context["sha256"] == sha256_text(context["text"]), "context hash mismatch")
    _require(context["start"] <= span["start"] < span["end"] <= context["end"], "span lies outside context")
    local_start = span["start"] - context["start"]
    local_end = span["end"] - context["start"]
    _require(context["text"][local_start:local_end] == span["text"], "span offsets do not reproduce original text")

    _validate_evidence(candidate)
    views = candidate["views"]
    role = span["discourse_role"]
    if span["language_identity"] == "russian" and role in {"quotation", "dialogue"}:
        _require(views["faithful_literary"] == "retain_original", "Russian speech must remain source-faithful")
        _require(views["modern_literary_ukrainian"] in {"mask_span_from_loss", "exclude_span_or_record"}, "Russian speech must be masked or excluded from modern loss")
        _require(views["correction"] in {"not_applicable", "protected"}, "Russian speech is not correction gold")
    if _is_protected(candidate):
        _require(views["correction"] in {"protected", "not_applicable", "unresolved"}, "protected variation cannot be a correction candidate")

    contamination = candidate["safety"]["contamination"]
    expected_states = contamination_states(
        context["text"],
        evaluation_registry,
        additional_sha256=(source["content_sha256"],),
    )
    for field, expected in expected_states.items():
        _require(contamination[field] == expected, f"stale or false contamination state: {field}")
    expected_artifacts = {
        "v0_1_1_manifest": evaluation_registry.v011_manifest_sha256,
        "v0_2_packet": evaluation_registry.v02_packet_sha256,
    }
    _require(contamination["registry_artifact_sha256"] == expected_artifacts, "evaluation registry receipt mismatch")

    source_origin = source["origin"]
    safety_origin = candidate["safety"]["origin"]
    expected_origin = {
        "human_authored": "verified_human_authorship",
        "machine_generated": "verified_synthetic",
        "machine_translated": "verified_synthetic",
        "human_revised_synthetic": "verified_synthetic",
    }.get(source_origin)
    if expected_origin is None:
        _require(
            safety_origin in {"unknown", "conflicting"},
            "unknown source origin cannot be marked verified",
        )
    else:
        _require(
            safety_origin == expected_origin,
            "source origin and safety evidence contradict each other",
        )


def _projection(review: Mapping[str, Any]) -> Mapping[str, Any]:
    value = review.get("projection")
    _require(isinstance(value, Mapping), "review lacks projection")
    return value


def adjudicative_core(projection: Mapping[str, Any]) -> dict[str, Any]:
    """Canonical linguistic judgment, excluding independently authored evidence prose."""
    return {
        "acceptable_alternatives": sorted(projection["acceptable_alternatives"]),
        "accepted_correction": projection["accepted_correction"],
        "decision": projection["decision"],
        "discourse_role": projection["discourse_role"],
        "language_identity": projection["language_identity"],
        "representation": projection["representation"],
        "views": projection["views"],
    }


def first_pass_core_agreement(first: Sequence[Mapping[str, Any]]) -> bool:
    """Whether two reviews agree on every adjudicative field."""
    _require(len(first) == 2, "first-pass consensus requires exactly two reviews")
    return adjudicative_core(_projection(first[0])) == adjudicative_core(_projection(first[1]))


def merge_first_pass_agreement(first: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Merge independent evidence while preserving one agreed linguistic core."""
    _require(first_pass_core_agreement(first), "cannot merge disagreeing first-pass reviews")
    projections = [_projection(review) for review in first]
    if projections[0] == projections[1]:
        return copy.deepcopy(dict(projections[0]))
    merged = copy.deepcopy(adjudicative_core(projections[0]))
    for field in ("citations", "uncertainty"):
        values: list[Any] = []
        seen: set[str] = set()
        for projection in projections:
            for value in projection[field]:
                encoded = canonical_json(value)
                if encoded not in seen:
                    seen.add(encoded)
                    values.append(copy.deepcopy(value))
        merged[field] = values
    merged["rationale"] = "\n\n".join(
        f"Первинний рецензент {label}: {projection['rationale']}"
        for label, projection in zip(("A", "B"), projections, strict=True)
    )
    return merged


def validate_decision(
    decision: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    validator: Draft202012Validator,
    allow_test_fixtures: bool,
) -> None:
    """Enforce two-person review and a distinct third-person conflict path."""
    _validate_schema(decision, validator, label="reviewer decision")
    _require(decision["candidate_id"] == candidate["candidate_id"], "decision candidate ID mismatch")
    candidate_hash = sha256_text(canonical_json(candidate))
    _require(decision["candidate_sha256"] == candidate_hash, "decision candidate hash mismatch")

    first = decision["first_pass_reviews"]
    first_ids = [item["reviewer"]["reviewer_id"] for item in first]
    _require(len(set(first_ids)) == 2, "first-pass reviewers must be distinct")
    first_fixtures = [item["reviewer"]["test_fixture"] for item in first]
    _require(allow_test_fixtures or not any(first_fixtures), "fixture reviewer cannot be a real adjudicator")
    resolution = decision["final_resolution"]
    final = decision["final"]

    if first_pass_core_agreement(first):
        _require(resolution["kind"] == "first_pass_agreement", "matching first passes require agreement resolution")
        _require("third_review" not in resolution, "agreement resolution cannot contain a third review")
        _require(
            final == merge_first_pass_agreement(first),
            "final projection must preserve the agreed core and both reviewers' evidence",
        )
    elif resolution["kind"] == "unresolved_conflict":
        _require("third_review" not in resolution, "unresolved conflict cannot contain a third review")
        _require(final["decision"] == "unresolved", "unresolved conflict requires unresolved final decision")
    else:
        _require(resolution["kind"] == "third_human_adjudication", "conflict needs a third human or unresolved state")
        third = resolution.get("third_review")
        _require(isinstance(third, Mapping), "third-human adjudication lacks a review")
        reviewer = third["reviewer"]
        _require(reviewer["reviewer_id"] not in first_ids, "third reviewer must be distinct")
        _require(allow_test_fixtures or not reviewer["test_fixture"], "fixture third reviewer cannot be a real adjudicator")
        _require(_projection(third)["decision"] != "unresolved", "unresolved third review cannot adjudicate")
        _require(final == _projection(third), "final projection must equal third-human adjudication")

    unresolved = final["decision"] == "unresolved"
    _require((decision["review_state"] == "unresolved") == unresolved, "review state contradicts final decision")
    if final["decision"] == "correction":
        _require(final["accepted_correction"] is not None, "correction decision lacks accepted correction")
    else:
        _require(final["accepted_correction"] is None, "non-correction decision cannot carry accepted correction")

    span = candidate["span"]
    if _is_protected(candidate):
        _require(final["decision"] != "correction", "protected variation cannot be adjudicated as correction")
    if span["language_identity"] == "russian" and span["discourse_role"] in {"quotation", "dialogue"}:
        _require(final["decision"] in {"quoted_or_multilingual", "protected_variation", "exclude", "unresolved"}, "source-faithful Russian speech cannot become a correction")
        _require(final["views"]["faithful_literary"] == "retain_original", "final review must preserve quotation bytes")
        _require(final["views"]["modern_literary_ukrainian"] in {"mask_span_from_loss", "exclude_span_or_record"}, "final review must mask or exclude Russian speech")


def _evidence_incomplete(candidate: Mapping[str, Any]) -> bool:
    return any(
        item["status"] in {"incomplete", "parse_error", "transient_error"}
        or item["parser_status"] in {"parse_error", "transient_error"}
        for item in candidate["evidence"]
    )


def _safety_blockers(
    candidate: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> list[str]:
    safety = candidate["safety"]
    blockers: list[str] = []
    checks = (
        (safety["provenance"] == "complete", "provenance_not_complete"),
        (safety["rights"] == "granted", "rights_not_granted"),
        (safety["permitted_use"] == "correction_eligible", "permitted_use_not_correction_eligible"),
        (safety["origin"] in {"verified_human_authorship", "verified_synthetic"}, "origin_not_verified"),
        (safety["private_data"] == "clear", "private_data_not_clear"),
    )
    blockers.extend(reason for passed, reason in checks if not passed)
    for field in ("v0_1_1_exact", "v0_1_1_near", "v0_2_exact", "v0_2_near"):
        if safety["contamination"][field] != "clear":
            blockers.append(f"contamination_{field}")
    if _evidence_incomplete(candidate):
        blockers.append("evidence_incomplete")
    if _is_protected(candidate):
        blockers.append("protected_variation")
    if decision["review_state"] != "adjudicated":
        blockers.append("review_unresolved")
    if decision["final"]["decision"] != "correction":
        blockers.append("decision_not_correction")
    reviewers = [item["reviewer"] for item in decision["first_pass_reviews"]]
    third = decision["final_resolution"].get("third_review")
    if isinstance(third, Mapping):
        reviewers.append(third["reviewer"])
    if any(reviewer["test_fixture"] for reviewer in reviewers):
        blockers.append("test_fixture_reviewer")
    return sorted(set(blockers))


def _handoff(candidate: Mapping[str, Any], decision: Mapping[str, Any], blockers: Sequence[str]) -> str:
    final_decision = decision["final"]["decision"]
    if not blockers:
        return "correction_intake_ready"
    if final_decision in {"acceptable_as_is", "protected_variation", "quoted_or_multilingual"} or _is_protected(candidate):
        return "faithful_or_protected_only"
    if final_decision == "exclude" or any(
        blocker.startswith("contamination_") or blocker in {"rights_not_granted", "private_data_not_clear"}
        for blocker in blockers
    ):
        return "excluded"
    return "unresolved"


def build_correction_record(
    candidate: dict[str, Any], decision: dict[str, Any]
) -> dict[str, Any]:
    """Build the canonical non-exportable #6121 handoff record.

    Issue #6122 imports this function to recompute the handoff rather than
    trusting caller-supplied blockers or export-control fields.
    """
    candidate_hash = sha256_text(canonical_json(candidate))
    decision_hash = sha256_text(canonical_json(decision))
    blockers = _safety_blockers(candidate, decision)
    resolution_kind = decision["final_resolution"]["kind"]
    conflict_state = {
        "first_pass_agreement": "none",
        "third_human_adjudication": "resolved_by_third_human",
        "unresolved_conflict": "unresolved",
    }[resolution_kind]
    return {
        "candidate": candidate,
        "candidate_sha256": candidate_hash,
        "conflict_state": conflict_state,
        "decision": decision,
        "decision_sha256": decision_hash,
        "export_control": {
            "handoff": _handoff(candidate, decision, blockers),
            "model_training_or_export_eligible": False,
            "owner_issue": 6122,
            "qualified_correction_intake": not blockers,
        },
        "record_id": f"correction:{sha256_text(candidate_hash + decision_hash)}",
        "safety_blockers": blockers,
        "schema_version": "correction_record_v1",
    }


def _record(candidate: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    """Backward-compatible internal alias for existing focused tests."""
    return build_correction_record(candidate, decision)


def _jsonl_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    return "".join(canonical_json(row) + "\n" for row in rows).encode("utf-8")


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=path.name,
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _schema_hashes() -> dict[str, str]:
    return {path.name: sha256_file(path) for path in SCHEMA_PATHS}


def _receipt(
    *,
    operation: str,
    input_records: int,
    input_hash: str,
    output_rows: Sequence[Mapping[str, Any]],
    registry: EvaluationRegistry,
    counts: Mapping[str, int],
) -> dict[str, Any]:
    output_bytes = _jsonl_bytes(output_rows)
    return {
        "counts": dict(sorted(counts.items())),
        "determinism": {
            "ordering": "input packet order",
            "serialization": "UTF-8 canonical JSON with sorted keys and LF",
            "timestamps_omitted": True,
        },
        "evaluation_registry": {
            "near_duplicate_threshold": NEAR_DUPLICATE_THRESHOLD,
            "normalization": "NFKC; casefold; collapse whitespace",
            "source_fingerprint_count": registry.source_fingerprint_count,
            "v0_1_1_manifest_sha256": registry.v011_manifest_sha256,
            "v0_2_packet_sha256": registry.v02_packet_sha256,
        },
        "input": {"records": input_records, "sha256": input_hash},
        "operation": operation,
        "output": {"records": len(output_rows), "sha256": sha256_bytes(output_bytes)},
        "safety": {
            "automatic_gold_created": False,
            "dataset_export_or_publication_performed": False,
            "model_training_performed": False,
            "raw_dictionary_payload_exported": False,
        },
        "schema_version": "correction_factory_receipt_v1",
        "schemas": _schema_hashes(),
    }


def prepare_review_packet(
    *,
    candidates_path: Path,
    packet_output: Path,
    receipt_output: Path,
    evaluation_registry: EvaluationRegistry,
) -> dict[str, Any]:
    """Validate unresolved candidates and write a deterministic review packet."""
    rows = read_jsonl(candidates_path)
    _require(rows, "empty correction candidate input")
    schemas, schema_registry = _schema_bundle()
    candidate_validator = _validator(
        CANDIDATE_SCHEMA_PATH, schemas=schemas, registry=schema_registry
    )
    receipt_validator = _validator(
        RECEIPT_SCHEMA_PATH, schemas=schemas, registry=schema_registry
    )
    seen: set[str] = set()
    counts: Counter[str] = Counter()
    for line_number, candidate in enumerate(rows, 1):
        validate_candidate(
            candidate,
            validator=candidate_validator,
            evaluation_registry=evaluation_registry,
        )
        candidate_id = candidate["candidate_id"]
        _require(candidate_id not in seen, f"duplicate candidate ID at line {line_number}: {candidate_id}")
        seen.add(candidate_id)
        counts["candidate_records"] += 1
        counts["unresolved_records"] += 1
        for layer in candidate["candidate_layers"]:
            counts[f"layer_{layer}"] += 1

    input_hash = sha256_file(candidates_path)
    receipt = _receipt(
        operation="prepare_review_packet",
        input_records=len(rows),
        input_hash=input_hash,
        output_rows=rows,
        registry=evaluation_registry,
        counts=counts,
    )
    _validate_schema(receipt, receipt_validator, label="factory receipt")
    packet_bytes = _jsonl_bytes(rows)
    _require(receipt["output"]["sha256"] == sha256_bytes(packet_bytes), "internal packet hash mismatch")
    _write_atomic(packet_output, packet_bytes)
    _write_atomic(receipt_output, (canonical_json(receipt) + "\n").encode("utf-8"))
    return receipt


def adjudicate(
    *,
    packet_path: Path,
    decisions_path: Path,
    records_output: Path,
    receipt_output: Path,
    evaluation_registry: EvaluationRegistry,
    allow_test_fixtures: bool = False,
) -> dict[str, Any]:
    """Join an exact packet to qualified reviews and emit controlled records."""
    candidates = read_jsonl(packet_path)
    decisions = read_jsonl(decisions_path)
    _require(candidates, "empty correction review packet")
    _require(len(candidates) == len(decisions), "missing or extra reviewer decisions")
    schemas, schema_registry = _schema_bundle()
    candidate_validator = _validator(
        CANDIDATE_SCHEMA_PATH, schemas=schemas, registry=schema_registry
    )
    decision_validator = _validator(
        DECISION_SCHEMA_PATH, schemas=schemas, registry=schema_registry
    )
    record_validator = _validator(RECORD_SCHEMA_PATH, schemas=schemas, registry=schema_registry)
    receipt_validator = _validator(
        RECEIPT_SCHEMA_PATH, schemas=schemas, registry=schema_registry
    )

    records: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    seen_candidates: set[str] = set()
    for candidate, decision in zip(candidates, decisions, strict=True):
        validate_candidate(
            candidate,
            validator=candidate_validator,
            evaluation_registry=evaluation_registry,
        )
        candidate_id = candidate["candidate_id"]
        _require(candidate_id not in seen_candidates, f"duplicate packet candidate: {candidate_id}")
        seen_candidates.add(candidate_id)
        validate_decision(
            decision,
            candidate,
            validator=decision_validator,
            allow_test_fixtures=allow_test_fixtures,
        )
        record = build_correction_record(candidate, decision)
        _validate_schema(record, record_validator, label="correction record")
        records.append(record)
        counts["candidate_records"] += 1
        counts[f"decision_{decision['final']['decision']}"] += 1
        counts[f"handoff_{record['export_control']['handoff']}"] += 1
        if record["export_control"]["qualified_correction_intake"]:
            counts["qualified_correction_intake"] += 1
        else:
            counts["blocked_records"] += 1

    combined_input_hash = sha256_text(
        canonical_json(
            {
                "decisions_sha256": sha256_file(decisions_path),
                "packet_sha256": sha256_file(packet_path),
            }
        )
    )
    receipt = _receipt(
        operation="adjudicate",
        input_records=len(candidates),
        input_hash=combined_input_hash,
        output_rows=records,
        registry=evaluation_registry,
        counts=counts,
    )
    _validate_schema(receipt, receipt_validator, label="factory receipt")
    records_bytes = _jsonl_bytes(records)
    _require(receipt["output"]["sha256"] == sha256_bytes(records_bytes), "internal record hash mismatch")
    _write_atomic(records_output, records_bytes)
    _write_atomic(receipt_output, (canonical_json(receipt) + "\n").encode("utf-8"))
    return receipt


def _evaluation_registry_from_args(args: argparse.Namespace) -> EvaluationRegistry:
    return load_evaluation_registry(
        v011_manifest_path=args.evaluation_manifest,
        v02_packet_path=args.v02_packet,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evaluation-manifest",
        type=Path,
        default=DEFAULT_EVALUATION_MANIFEST,
    )
    parser.add_argument("--v02-packet", type=Path, default=DEFAULT_V02_PACKET)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="validate and freeze a review packet")
    prepare_parser.add_argument("--candidates", required=True, type=Path)
    prepare_parser.add_argument("--packet-output", required=True, type=Path)
    prepare_parser.add_argument("--receipt-output", required=True, type=Path)

    adjudicate_parser = subparsers.add_parser("adjudicate", help="join qualified decisions")
    adjudicate_parser.add_argument("--packet", required=True, type=Path)
    adjudicate_parser.add_argument("--decisions", required=True, type=Path)
    adjudicate_parser.add_argument("--records-output", required=True, type=Path)
    adjudicate_parser.add_argument("--receipt-output", required=True, type=Path)
    adjudicate_parser.add_argument(
        "--allow-test-fixtures",
        action="store_true",
        help="tests only; fixture reviewers remain blocked from qualified intake",
    )
    args = parser.parse_args(argv)

    try:
        registry = _evaluation_registry_from_args(args)
        if args.command == "prepare":
            receipt = prepare_review_packet(
                candidates_path=args.candidates,
                packet_output=args.packet_output,
                receipt_output=args.receipt_output,
                evaluation_registry=registry,
            )
        else:
            receipt = adjudicate(
                packet_path=args.packet,
                decisions_path=args.decisions,
                records_output=args.records_output,
                receipt_output=args.receipt_output,
                evaluation_registry=registry,
                allow_test_fixtures=args.allow_test_fixtures,
            )
    except FactoryError as exc:
        parser.error(str(exc))
    print(canonical_json(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
