#!/usr/bin/env python3
"""Build disjoint, lineage-preserving Ukrainian model-consumer views.

The exporter is the #6122 admission boundary. It revalidates source contracts,
qualified correction handoffs, privacy/origin state, and evaluation
contamination before writing one homogeneous local artifact. It never runs a
model, starts training, uploads data, or publishes an artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, TextIO

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from scripts.projects.open_model_data import correction_factory
from scripts.projects.open_model_data import validate_source_records as source_contract

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

SOURCE_PAYLOAD_SCHEMA = CONTRACTS / "foundry_source_payload_v1.schema.json"
PRETRAIN_SCHEMA = CONTRACTS / "continued_pretraining_view_v1.schema.json"
CORRECTION_VIEW_SCHEMA = CONTRACTS / "correction_instruction_view_v1.schema.json"
PREFERENCE_SCHEMA = CONTRACTS / "preference_view_v1.schema.json"
QUALITY_SCHEMA = CONTRACTS / "quality_filter_view_v1.schema.json"
EVALUATION_SCHEMA = CONTRACTS / "heldout_evaluation_view_v1.schema.json"
EXPORT_RECEIPT_SCHEMA = CONTRACTS / "model_view_export_receipt_v1.schema.json"
RECIPE_CONFIG_SCHEMA = CONTRACTS / "training_recipe_config_v1.schema.json"
RECIPE_MANIFEST_SCHEMA = CONTRACTS / "training_recipe_manifest_v1.schema.json"

CANDIDATE_SCHEMA = CONTRACTS / "correction_candidate_v1.schema.json"
DECISION_SCHEMA = CONTRACTS / "correction_reviewer_decision_v1.schema.json"
CORRECTION_RECORD_SCHEMA = CONTRACTS / "correction_record_v1.schema.json"
SOURCE_RECORD_SCHEMA = CONTRACTS / "source_record_v1.schema.json"

NEW_SCHEMA_PATHS = (
    SOURCE_PAYLOAD_SCHEMA,
    PRETRAIN_SCHEMA,
    CORRECTION_VIEW_SCHEMA,
    PREFERENCE_SCHEMA,
    QUALITY_SCHEMA,
    EVALUATION_SCHEMA,
    EXPORT_RECEIPT_SCHEMA,
    RECIPE_CONFIG_SCHEMA,
    RECIPE_MANIFEST_SCHEMA,
)
DEPENDENCY_SCHEMA_PATHS = (
    CANDIDATE_SCHEMA,
    DECISION_SCHEMA,
    CORRECTION_RECORD_SCHEMA,
    SOURCE_RECORD_SCHEMA,
)
ALL_SCHEMA_PATHS = NEW_SCHEMA_PATHS + DEPENDENCY_SCHEMA_PATHS

DEFAULT_V011_MANIFEST = ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json"
DEFAULT_V02_PACKET = ROOT / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl"
DEFAULT_EVALUATION_ARTIFACTS = (
    DEFAULT_V011_MANIFEST,
    DEFAULT_V02_PACKET,
    ROOT / "data/projects/ua_eval_harness/evalset_v1.jsonl",
    ROOT / "data/projects/ua_eval_harness/analysis/v0.1.1/item_evidence.jsonl",
    ROOT / "data/projects/ua_eval_harness/scoring_dispositions_v1.json",
    ROOT / "data/projects/ua_eval_harness/development/taxonomy.yaml",
    ROOT / "data/projects/ua_eval_harness/minimal_edit_prompt_v1.txt",
)

VIEW_SCHEMAS = {
    "continued_pretraining": PRETRAIN_SCHEMA,
    "correction_instruction": CORRECTION_VIEW_SCHEMA,
    "preference": PREFERENCE_SCHEMA,
    "quality_filter": QUALITY_SCHEMA,
    "heldout_evaluation": EVALUATION_SCHEMA,
}
OBJECTIVES = {
    "continued_pretraining": "causal_language_modeling",
    "correction_instruction": "supervised_correction",
    "preference": "pairwise_preference",
    "quality_filter": "binary_quality_classification",
    "heldout_evaluation": "heldout_evaluation_only",
}
TARGET_LOSS_POLICIES = {
    "continued_pretraining": "unmasked_text_tokens",
    "correction_instruction": "target_fields_only",
    "preference": "target_fields_only",
    "quality_filter": "target_fields_only",
    "heldout_evaluation": "no_training_evaluation_only",
}
ORIGINS = (
    "human_authored",
    "machine_generated",
    "machine_translated",
    "human_revised_synthetic",
)

NEAR_DUPLICATE_THRESHOLD = 0.90
MIN_CONTAINMENT_CHARACTERS = 32
CANDIDATE_ANCHOR_CHARACTERS = 8
MAX_CHARACTER_ANCHORS_PER_TEXT = 64
MAX_EXACT_SEQUENCE_CHARACTERS = 4096
LONG_SEQUENCE_QGRAM_OVERLAP_THRESHOLDS = (
    (2, 0.80),
    (3, 0.70),
    (4, 0.60),
    (5, 0.50),
)
MIN_DERIVED_RULE_CHARACTERS = 16
SHINGLE_WIDTH = 3
PROTECTED_REASONS = frozenset(
    {
        "russian_or_mixed_language",
        "quoted_or_multilingual",
        "historical_or_heritage",
        "dialectal_or_regional",
        "marked_register",
        "ocr_or_encoding",
        "context_uncertain",
    }
)


class ExportError(ValueError):
    """An input or requested export violates the Foundry contract."""


@dataclass(frozen=True)
class SourceAdmission:
    record: dict[str, Any]
    sha256: str
    admitted: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ExclusionMatch:
    matched: bool
    method: str | None = None


@dataclass
class EvaluationExclusionRegistry:
    exact_hashes: set[str]
    near_texts: list[str]
    near_shingles: list[frozenset[str]]
    shingle_index: dict[str, set[int]]
    character_index: dict[str, set[int]]
    artifacts: list[dict[str, str]]

    def add_text(self, text: str, *, explicit_evaluation_text: bool) -> None:
        normalized = normalize_text(text)
        if not normalized:
            return
        if explicit_evaluation_text or len(normalized) >= MIN_DERIVED_RULE_CHARACTERS:
            self.exact_hashes.add(sha256_text(normalized))
        if len(normalized) < MIN_CONTAINMENT_CHARACTERS:
            return
        if not explicit_evaluation_text and len(normalized.split()) < SHINGLE_WIDTH:
            return
        index = len(self.near_texts)
        shingles = frozenset(word_shingles(normalized))
        self.near_texts.append(normalized)
        self.near_shingles.append(shingles)
        for shingle in shingles:
            self.shingle_index[shingle].add(index)
        for offset in character_anchor_offsets(normalized):
            self.character_index[normalized[offset : offset + CANDIDATE_ANCHOR_CHARACTERS]].add(index)

    def match(self, text: str) -> ExclusionMatch:
        normalized = normalize_text(text)
        if not normalized:
            return ExclusionMatch(False)
        if sha256_text(normalized) in self.exact_hashes:
            return ExclusionMatch(True, "exact_normalized")

        candidate_indexes: set[int] = set()
        shingles = frozenset(word_shingles(normalized))
        for shingle in shingles:
            candidate_indexes.update(self.shingle_index.get(shingle, ()))
        if len(normalized) >= CANDIDATE_ANCHOR_CHARACTERS:
            for offset in character_anchor_offsets(normalized):
                candidate_indexes.update(
                    self.character_index.get(normalized[offset : offset + CANDIDATE_ANCHOR_CHARACTERS], ())
                )

        for index in sorted(candidate_indexes):
            reference = self.near_texts[index]
            reference_shingles = self.near_shingles[index]
            if min(len(normalized), len(reference)) >= MIN_CONTAINMENT_CHARACTERS:
                shorter, longer = (
                    (normalized, reference)
                    if len(normalized) <= len(reference)
                    else (reference, normalized)
                )
                final_anchor = len(shorter) - CANDIDATE_ANCHOR_CHARACTERS
                containment_anchors = {
                    shorter[offset : offset + CANDIDATE_ANCHOR_CHARACTERS]
                    for offset in (0, final_anchor // 2, final_anchor)
                }
                # Exact containment preserves these deterministic character
                # anchors. The probes are necessary conditions, so they only
                # skip impossible pairs before the frozen substring check.
                if all(anchor in longer for anchor in containment_anchors) and shorter in longer:
                    return ExclusionMatch(True, "character_containment")
            if shingles and reference_shingles:
                shingle_size_ratio = min(len(shingles), len(reference_shingles)) / max(
                    len(shingles), len(reference_shingles)
                )
                if shingle_size_ratio >= NEAR_DUPLICATE_THRESHOLD:
                    union = shingles | reference_shingles
                    if len(shingles & reference_shingles) / len(union) >= NEAR_DUPLICATE_THRESHOLD:
                        return ExclusionMatch(True, "word_shingle_jaccard")
            length_ratio = min(len(normalized), len(reference)) / max(len(normalized), len(reference))
            if length_ratio >= NEAR_DUPLICATE_THRESHOLD and character_sequence_matches(
                normalized,
                reference,
                threshold=NEAR_DUPLICATE_THRESHOLD,
            ):
                return ExclusionMatch(True, "character_sequence")
        return ExclusionMatch(False)


def sequence_ratio_can_reach(first: str, second: str, *, threshold: float) -> bool:
    """Return false only when q-gram bounds disprove a SequenceMatcher hit.

    A SequenceMatcher ratio at ``threshold`` needs a minimum number of matched
    characters. Its ordered matching blocks necessarily contribute q-grams
    shared by both strings. Counting the maximum possible number of blocks
    from unmatched characters gives a conservative lower bound on those
    shared q-grams. Failing either width therefore makes the expensive exact
    ratio mathematically impossible without changing the decision boundary.
    """
    required_matches = math.ceil(threshold * (len(first) + len(second)) / 2)
    if required_matches > min(len(first), len(second)):
        return False
    maximum_blocks = len(first) + len(second) - (2 * required_matches) + 1
    for width in (2, 3):
        if min(len(first), len(second)) < width:
            continue
        required_shared = max(0, required_matches - ((width - 1) * maximum_blocks))
        if required_shared == 0:
            continue
        first_grams = Counter(first[index : index + width] for index in range(len(first) - width + 1))
        second_grams = Counter(second[index : index + width] for index in range(len(second) - width + 1))
        shared = sum((first_grams & second_grams).values())
        if shared < required_shared:
            return False
    return True


def qgram_overlap_coefficient(first: str, second: str, *, width: int) -> float:
    """Return multiset q-gram overlap divided by the smaller q-gram count."""
    require(width > 0, "q-gram width must be positive")
    if min(len(first), len(second)) < width:
        return float(first == second)
    first_grams = Counter(first[index : index + width] for index in range(len(first) - width + 1))
    second_grams = Counter(second[index : index + width] for index in range(len(second) - width + 1))
    shared = sum((first_grams & second_grams).values())
    return shared / min(sum(first_grams.values()), sum(second_grams.values()))


def character_sequence_matches(first: str, second: str, *, threshold: float) -> bool:
    """Bounded character-sequence fallback for the near-duplicate firewall.

    Exact ``autojunk=False`` matching is retained for bounded strings. On long
    strings, where both difflib modes can take hours on ordinary language, use
    a deterministic multiset q-gram ladder. Its thresholds represent the
    operational lower envelope for surviving 2–5-grams around a 10% edit
    boundary: a single substitution, insertion, or deletion disrupts at most
    ``q`` source q-grams. The ladder is deliberately a bounded detector rather
    than a claim of formal equivalence to difflib on every adversarial edit
    layout. Containment, word-shingle, and character-anchor checks remain
    independent routes, while realistic long-text substitution, insertion,
    deletion, clustered-edit, and repetitive-text cases are regression-tested.
    """
    if max(len(first), len(second)) <= MAX_EXACT_SEQUENCE_CHARACTERS:
        matcher = SequenceMatcher(None, first, second, autojunk=False)
        return (
            matcher.quick_ratio() >= threshold
            and sequence_ratio_can_reach(first, second, threshold=threshold)
            and matcher.ratio() >= threshold
        )
    return all(
        qgram_overlap_coefficient(first, second, width=width) >= minimum_overlap
        for width, minimum_overlap in LONG_SEQUENCE_QGRAM_OVERLAP_THRESHOLDS
    )


def character_anchor_offsets(normalized: str) -> tuple[int, ...]:
    """Return deterministic, evenly spaced anchors with bounded index growth."""
    windows = len(normalized) - CANDIDATE_ANCHOR_CHARACTERS + 1
    if windows <= 0:
        return ()
    if windows <= MAX_CHARACTER_ANCHORS_PER_TEXT:
        return tuple(range(windows))
    final_offset = windows - 1
    return tuple(
        (anchor * final_offset) // (MAX_CHARACTER_ANCHORS_PER_TEXT - 1)
        for anchor in range(MAX_CHARACTER_ANCHORS_PER_TEXT)
    )


def empty_text_registry() -> EvaluationExclusionRegistry:
    return EvaluationExclusionRegistry(
        exact_hashes=set(),
        near_texts=[],
        near_shingles=[],
        shingle_index=defaultdict(set),
        character_index=defaultdict(set),
        artifacts=[],
    )


@dataclass
class AtomicJsonl:
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
            mode="w",
            encoding="utf-8",
            newline="",
            dir=output.parent,
            prefix=output.name,
            suffix=".tmp",
            delete=False,
        )
        return cls(output, handle, Path(handle.name), hashlib.sha256())

    def write(self, row: Mapping[str, Any]) -> None:
        encoded = (canonical_json(row) + "\n").encode("utf-8")
        self.handle.write(encoded.decode("utf-8"))
        self.digest.update(encoded)
        self.records += 1
        self.bytes_written += len(encoded)

    def finish(self) -> dict[str, Any]:
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.handle.close()
        return {
            "bytes": self.bytes_written,
            "records": self.records,
            "sha256": self.digest.hexdigest(),
        }

    def replace(self) -> None:
        os.replace(self.temporary, self.output)

    def abort(self) -> None:
        if not self.handle.closed:
            self.handle.close()
        self.temporary.unlink(missing_ok=True)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


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
        raise ExportError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def word_shingles(value: str) -> Iterator[str]:
    tokens = value.split()
    for index in range(len(tokens) - SHINGLE_WIDTH + 1):
        yield " ".join(tokens[index : index + SHINGLE_WIDTH])


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExportError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExportError(f"cannot read JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def iter_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        raise ExportError(f"cannot read JSONL {path}: {exc}") from exc
    with handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ExportError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
            require(isinstance(row, dict), f"expected object at {path}:{line_number}")
            yield line_number, row


def artifact(path: Path, *, role: str, records: int) -> dict[str, Any]:
    try:
        byte_count = path.stat().st_size
    except OSError as exc:
        raise ExportError(f"cannot stat {path}: {exc}") from exc
    return {
        "bytes": byte_count,
        "records": records,
        "role": role,
        "sha256": sha256_file(path),
    }


def schema_bundle() -> tuple[dict[Path, dict[str, Any]], Registry]:
    schemas = {path: read_json(path) for path in ALL_SCHEMA_PATHS}
    registry = Registry()
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(str(schema["$id"]), Resource.from_contents(schema))
    return schemas, registry


def validator_for(
    path: Path,
    *,
    schemas: Mapping[Path, dict[str, Any]],
    registry: Registry,
    format_checker: bool = False,
) -> Draft202012Validator:
    return Draft202012Validator(
        schemas[path],
        registry=registry,
        format_checker=FormatChecker() if format_checker else None,
    )


def validate_schema(value: Mapping[str, Any], validator: Draft202012Validator, *, label: str) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if errors:
        location = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise ExportError(f"{label} schema violation at {location}: {errors[0].message}")


def logical_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return f"external:{sha256_text(str(resolved))[:16]}"


def recursive_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from recursive_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from recursive_strings(item)


def jsonl_values(path: Path) -> Iterator[dict[str, Any]]:
    for _line_number, row in iter_jsonl(path):
        yield row


def artifact_strings(path: Path) -> Iterator[str]:
    if path.suffix == ".jsonl":
        for row in jsonl_values(path):
            yield from recursive_strings(row)
        return
    if path.suffix == ".json":
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ExportError(f"cannot parse evaluation artifact {path}: {exc}") from exc
        yield from recursive_strings(value)
        return
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ExportError(f"cannot read evaluation artifact {path}: {exc}") from exc
    yield raw
    yield from (line for line in raw.splitlines() if line.strip())


def v011_items(path: Path) -> list[dict[str, Any]]:
    manifest = read_json(path)
    layouts = manifest.get("record_layouts", {})
    item_layout = layouts.get("item")
    reference_layout = layouts.get("reference")
    items = manifest.get("items")
    require(
        isinstance(item_layout, list) and isinstance(reference_layout, list) and isinstance(items, list),
        "invalid v0.1.1 manifest layouts",
    )
    required_item_fields = {"id", "source", "source_sha256", "references"}
    require(
        required_item_fields.issubset(item_layout),
        "v0.1.1 item layout lacks required fields",
    )
    required_reference_fields = {"annotator_index", "target", "target_sha256"}
    require(
        required_reference_fields.issubset(reference_layout),
        "v0.1.1 reference layout lacks required fields",
    )
    rows: list[dict[str, Any]] = []
    for packed in items:
        require(
            isinstance(packed, list) and len(packed) == len(item_layout),
            "invalid v0.1.1 item",
        )
        item = dict(zip(item_layout, packed, strict=True))
        source = item["source"]
        source_hash = item["source_sha256"]
        require(
            isinstance(source, str) and isinstance(source_hash, str) and sha256_text(source) == source_hash,
            "v0.1.1 source hash mismatch",
        )
        references: list[dict[str, str]] = []
        for packed_reference in item["references"]:
            require(
                isinstance(packed_reference, list) and len(packed_reference) == len(reference_layout),
                "invalid v0.1.1 reference",
            )
            reference = dict(zip(reference_layout, packed_reference, strict=True))
            target = reference["target"]
            target_hash = reference["target_sha256"]
            require(
                isinstance(target, str) and isinstance(target_hash, str) and sha256_text(target) == target_hash,
                "v0.1.1 reference hash mismatch",
            )
            references.append(
                {
                    "reference_id": str(reference["annotator_index"]),
                    "sha256": target_hash,
                    "text": target,
                }
            )
        require(references, "v0.1.1 evaluation item lacks references")
        rows.append(
            {
                "item_id": str(item["id"]),
                "references": references,
                "source": source,
                "source_sha256": source_hash,
            }
        )
    require(rows, "empty v0.1.1 manifest")
    return rows


def v02_items(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _line_number, row in iter_jsonl(path):
        blind = row.get("blind_reviewer_view")
        receipts = row.get("frozen_receipts")
        require(
            isinstance(blind, Mapping) and isinstance(receipts, Mapping),
            "invalid v0.2 packet row",
        )
        source = blind.get("source")
        source_hash = receipts.get("source_sha256")
        require(
            isinstance(source, str) and isinstance(source_hash, str) and sha256_text(source) == source_hash,
            "v0.2 source hash mismatch",
        )
        references: list[dict[str, str]] = []
        for reference in blind.get("references", []):
            require(
                isinstance(reference, list) and len(reference) >= 3,
                "invalid v0.2 reference",
            )
            reference_id, text, target_hash = reference[:3]
            require(
                isinstance(text, str) and isinstance(target_hash, str) and sha256_text(text) == target_hash,
                "v0.2 reference hash mismatch",
            )
            references.append(
                {
                    "reference_id": str(reference_id),
                    "sha256": target_hash,
                    "text": text,
                }
            )
        require(references, "v0.2 evaluation item lacks references")
        rows.append(
            {
                "item_id": str(row["item_id"]),
                "references": references,
                "source": source,
                "source_sha256": source_hash,
            }
        )
    require(rows, "empty v0.2 packet")
    return rows


def build_exclusion_registry(
    *,
    v011_manifest: Path,
    v02_packet: Path,
    extra_artifacts: Sequence[Path] = (),
) -> EvaluationExclusionRegistry:
    registry = empty_text_registry()
    defaults = [
        v011_manifest,
        v02_packet,
        *(path for path in DEFAULT_EVALUATION_ARTIFACTS if path not in {DEFAULT_V011_MANIFEST, DEFAULT_V02_PACKET}),
    ]
    paths: list[Path] = []
    seen_paths: set[Path] = set()
    for path in (*defaults, *extra_artifacts):
        resolved = path.resolve()
        if resolved in seen_paths:
            continue
        require(path.is_file(), f"missing evaluation exclusion artifact: {path}")
        seen_paths.add(resolved)
        paths.append(path)

    for item in v011_items(v011_manifest):
        registry.add_text(item["source"], explicit_evaluation_text=True)
        for reference in item["references"]:
            registry.add_text(reference["text"], explicit_evaluation_text=True)
    for item in v02_items(v02_packet):
        registry.add_text(item["source"], explicit_evaluation_text=True)
        for reference in item["references"]:
            registry.add_text(reference["text"], explicit_evaluation_text=True)

    for path in paths:
        registry.artifacts.append({"logical_path": logical_path(path), "sha256": sha256_file(path)})
        if path.resolve() in {v011_manifest.resolve(), v02_packet.resolve()}:
            continue
        for text in artifact_strings(path):
            registry.add_text(text, explicit_evaluation_text=False)

    registry.artifacts.sort(key=lambda item: item["logical_path"])
    require(registry.exact_hashes, "empty exact evaluation exclusion registry")
    require(registry.near_texts, "empty near-duplicate evaluation exclusion registry")
    return registry


def registry_receipt(registry: EvaluationExclusionRegistry) -> dict[str, Any]:
    return {
        "algorithm_version": "foundry-eval-exclusion-v2",
        "artifacts": registry.artifacts,
        "candidate_anchor_characters": CANDIDATE_ANCHOR_CHARACTERS,
        "maximum_character_anchors_per_text": MAX_CHARACTER_ANCHORS_PER_TEXT,
        "exact_fingerprints": len(registry.exact_hashes),
        "minimum_containment_characters": MIN_CONTAINMENT_CHARACTERS,
        "near_duplicate_threshold": NEAR_DUPLICATE_THRESHOLD,
        "near_fingerprints": len(registry.near_texts),
        "normalization": "NFKC; casefold; collapse whitespace",
    }


def admission_receipt(
    admissions: Mapping[str, SourceAdmission] | None,
) -> dict[str, Any]:
    total = len(admissions) if admissions is not None else 0
    admitted = sum(1 for admission in admissions.values() if admission.admitted) if admissions is not None else 0
    return {
        "applied": admissions is not None,
        "policy": "recompute source_record_v1 admission; unknown is denial",
        "source_records_admitted": admitted,
        "source_records_denied": total - admitted,
        "source_records_total": total,
    }


def deduplication_receipt(accepted_fingerprints: int | None, *, partitioning: str) -> dict[str, Any]:
    return {
        "accepted_fingerprints": accepted_fingerprints or 0,
        "algorithm_version": "foundry-intra-view-dedup-v2",
        "applied": accepted_fingerprints is not None,
        "candidate_anchor_characters": CANDIDATE_ANCHOR_CHARACTERS,
        "maximum_character_anchors_per_text": MAX_CHARACTER_ANCHORS_PER_TEXT,
        "minimum_containment_characters": MIN_CONTAINMENT_CHARACTERS,
        "near_duplicate_threshold": NEAR_DUPLICATE_THRESHOLD,
        "normalization": "NFKC; casefold; collapse whitespace",
        "partitioning": partitioning,
    }


def load_source_admissions(path: Path) -> tuple[dict[str, SourceAdmission], int]:
    schema, schema_hash = source_contract.load_schema()
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    try:
        rows = source_contract.load_records(path)
    except (OSError, json.JSONDecodeError) as exc:
        raise ExportError(f"cannot read source records {path}: {exc}") from exc
    admissions: dict[str, SourceAdmission] = {}
    for index, row in enumerate(rows, 1):
        require(isinstance(row, dict), f"source record {index} is not an object")
        record_id = row.get("record_id")
        require(isinstance(record_id, str), f"source record {index} lacks record_id")
        require(record_id not in admissions, f"duplicate source record ID: {record_id}")
        result = source_contract.validate_record(row, validator, schema_hash)
        admissions[record_id] = SourceAdmission(
            record=row,
            sha256=sha256_text(canonical_json(row)),
            admitted=bool(result["admitted"]),
            reasons=tuple(result["reasons"]),
        )
    require(rows, "empty source-record input")
    return admissions, len(rows)


def source_lineage(
    admission: SourceAdmission,
    *,
    correction_record: Mapping[str, Any] | None = None,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    base = {
        "source_content_sha256": admission.record["content"]["sha256"],
        "source_record_id": admission.record["record_id"],
        "source_record_sha256": admission.sha256,
    }
    if correction_record is not None:
        base.update(
            {
                "candidate_sha256": correction_record["candidate_sha256"],
                "correction_record_id": correction_record["record_id"],
                "correction_record_sha256": sha256_text(canonical_json(correction_record)),
                "decision_sha256": correction_record["decision_sha256"],
            }
        )
    if payload is not None:
        base.update(
            {
                "language_span_receipt_sha256": payload["language_span_review"]["receipt_sha256"],
                "source_derivation_receipt_sha256": payload["derivation"]["receipt_sha256"],
                "normalization_receipt_sha256": payload["normalization"]["receipt_sha256"],
                "source_payload_id": payload["payload_id"],
                "source_payload_sha256": sha256_text(canonical_json(payload)),
            }
        )
    return base


def eligibility(*, test_fixture: bool, qualified: bool | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "model_training_eligible": not test_fixture,
        "source_contract_admitted": True,
        "test_fixture": test_fixture,
    }
    if qualified is not None:
        value["qualified_adjudication"] = qualified
    return value


def require_stable_order(current: str, previous: str | None, *, label: str) -> str:
    require(previous is None or current > previous, f"{label} IDs must be unique and strictly ascending")
    return current


def validate_source_payload_semantics(payload: Mapping[str, Any]) -> None:
    require(payload["text_sha256"] == sha256_text(payload["text"]), "source payload text hash mismatch")
    derivation = payload["derivation"]
    if derivation["kind"] == "character_span":
        require(
            derivation["source_start_char"] < derivation["source_end_char"],
            "source payload derivation span is empty or reversed",
        )
        require(
            derivation["source_end_char"] - derivation["source_start_char"] == len(payload["text"]),
            "source payload derivation span length does not match segment text",
        )
    spans = payload["language_span_review"]["character_spans"]
    previous_end = 0
    for span in spans:
        require(0 <= span["start"] < span["end"] <= len(payload["text"]), "language span lies outside payload text")
        require(
            span["start"] == previous_end,
            "language spans must form a gap-free ordered partition",
        )
        previous_end = span["end"]
        protected = (
            span["language_identity"] != "ukrainian"
            or span["representation"] != "standard_orthography"
            or span["reason"] in PROTECTED_REASONS
        )
        if protected:
            require(
                span["modern_loss_action"] in {"mask_from_loss", "exclude_record"},
                "protected/non-Ukrainian span cannot be retained in modern loss",
            )
    require(
        previous_end == len(payload["text"]),
        "language spans must cover the complete payload text",
    )


def safety_reason_for_source_payload(
    payload: Mapping[str, Any],
    admission: SourceAdmission | None,
    registry: EvaluationExclusionRegistry,
) -> str | None:
    if admission is None:
        return "source_record_missing"
    if not admission.admitted:
        return "source_record_not_admitted"
    if payload["source_content_sha256"] != admission.record["content"]["sha256"]:
        raise ExportError("source payload parent content hash does not match source record")
    if payload["origin"] == "unknown":
        return "origin_unknown"
    origin_evidence = payload["origin_evidence"]
    if (
        origin_evidence["status"] != "verified"
        or origin_evidence["method"] is None
        or origin_evidence["receipt_sha256"] is None
    ):
        return "origin_unverified"
    if payload["private_data"] != "clear":
        return "private_data_not_clear"
    private_review = payload["private_data_review"]
    if private_review["status"] != "complete" or private_review["receipt_sha256"] is None:
        return "private_data_review_incomplete"
    normalization = payload["normalization"]
    if normalization["status"] != "complete" or normalization["receipt_sha256"] is None:
        return "normalization_incomplete"
    span_review = payload["language_span_review"]
    if (
        span_review["status"] != "complete"
        or span_review["reviewer_qualification"] is None
        or span_review["receipt_sha256"] is None
    ):
        return "language_span_review_incomplete"
    contamination = registry.match(payload["text"])
    if contamination.matched:
        return f"evaluation_contamination_{contamination.method}"
    return None


def correction_fixture_state(record: Mapping[str, Any]) -> bool:
    reviewers = [item["reviewer"] for item in record["decision"]["first_pass_reviews"]]
    third = record["decision"]["final_resolution"].get("third_review")
    if isinstance(third, Mapping):
        reviewers.append(third["reviewer"])
    return any(reviewer["test_fixture"] for reviewer in reviewers)


def validate_correction_handoff(
    record: Mapping[str, Any],
    *,
    candidate_validator: Draft202012Validator,
    decision_validator: Draft202012Validator,
    record_validator: Draft202012Validator,
    evaluation_registry: correction_factory.EvaluationRegistry,
    allow_test_fixtures: bool,
) -> None:
    validate_schema(record, record_validator, label="correction record")
    candidate = record["candidate"]
    decision = record["decision"]
    correction_factory.validate_candidate(
        candidate,
        validator=candidate_validator,
        evaluation_registry=evaluation_registry,
    )
    correction_factory.validate_decision(
        decision,
        candidate,
        validator=decision_validator,
        allow_test_fixtures=allow_test_fixtures,
    )
    expected = correction_factory.build_correction_record(candidate, decision)
    require(record == expected, "correction record does not equal canonical #6121 handoff")
    require(
        record["export_control"]["model_training_or_export_eligible"] is False,
        "#6121 handoff flag must remain false at the #6122 boundary",
    )
    require(record["export_control"]["owner_issue"] == 6122, "wrong correction handoff owner")


def correction_source_reason(record: Mapping[str, Any], admission: SourceAdmission | None) -> str | None:
    if admission is None:
        return "source_record_missing"
    if not admission.admitted:
        return "source_record_not_admitted"
    candidate = record["candidate"]
    if candidate["source"]["content_sha256"] != admission.record["content"]["sha256"]:
        raise ExportError("correction/source-record content hash mismatch")
    safety = candidate["safety"]
    checks = (
        (safety["provenance"] == "complete", "provenance_not_complete"),
        (safety["rights"] == "granted", "rights_not_granted"),
        (safety["permitted_use"] == "correction_eligible", "permitted_use_not_eligible"),
        (safety["origin"] in {"verified_human_authorship", "verified_synthetic"}, "origin_not_verified"),
        (safety["private_data"] == "clear", "private_data_not_clear"),
    )
    for passed, reason in checks:
        if not passed:
            return reason
    if any(
        safety["contamination"][field] != "clear"
        for field in ("v0_1_1_exact", "v0_1_1_near", "v0_2_exact", "v0_2_near")
    ):
        return "evaluation_contamination_upstream"
    return None


def corrected_context(record: Mapping[str, Any]) -> tuple[str, int, int]:
    candidate = record["candidate"]
    context = candidate["source"]["context"]
    span = candidate["span"]
    correction = record["decision"]["final"]["accepted_correction"]
    require(isinstance(correction, str), "correction handoff lacks accepted correction")
    local_start = span["start"] - context["start"]
    local_end = span["end"] - context["start"]
    target = context["text"][:local_start] + correction + context["text"][local_end:]
    return target, local_start, local_end


def any_contamination(values: Iterable[str], registry: EvaluationExclusionRegistry) -> ExclusionMatch:
    for value in values:
        match = registry.match(value)
        if match.matched:
            return match
    return ExclusionMatch(False)


def correction_deduplication_parts(view_kind: str, row: Mapping[str, Any]) -> tuple[str, str]:
    payload = row["payload"]
    if view_kind == "correction_instruction":
        signature = {
            "acceptable_alternatives": payload["acceptable_alternatives"],
            "accepted_correction": payload["accepted_correction"],
            "original_span": payload["original_span"],
            "span_end_char": payload["span_end_char"],
            "span_start_char": payload["span_start_char"],
        }
        return canonical_json(signature), payload["input_text"]
    if view_kind == "preference":
        signature = {
            "acceptable_alternatives": payload["acceptable_alternatives"],
            "chosen": payload["chosen"],
            "rejected": payload["rejected"],
        }
        return canonical_json(signature), payload["prompt"]
    signature = {"decision": payload["decision"], "label": payload["label"]}
    return canonical_json(signature), payload["text"]


def reserved_rollback_path(path: Path) -> Path:
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        prefix=f"{path.name}.rollback-",
        suffix=".bak",
        delete=False,
    ) as handle:
        rollback = Path(handle.name)
    return rollback


def replace_output_pair(*, writer: AtomicJsonl, receipt_temporary: Path, receipt_output: Path) -> None:
    require(
        writer.output.resolve() != receipt_output.resolve(),
        "view output and receipt output must be different paths",
    )
    output_backup: Path | None = None
    receipt_backup: Path | None = None
    output_backed_up = False
    receipt_backed_up = False
    output_installed = False
    receipt_installed = False
    try:
        if writer.output.exists():
            output_backup = reserved_rollback_path(writer.output)
            os.replace(writer.output, output_backup)
            output_backed_up = True
        if receipt_output.exists():
            receipt_backup = reserved_rollback_path(receipt_output)
            os.replace(receipt_output, receipt_backup)
            receipt_backed_up = True
        writer.replace()
        output_installed = True
        os.replace(receipt_temporary, receipt_output)
        receipt_installed = True
    except Exception as exc:
        rollback_errors: list[OSError] = []
        for installed, path in (
            (output_installed, writer.output),
            (receipt_installed, receipt_output),
        ):
            if installed:
                try:
                    path.unlink(missing_ok=True)
                except OSError as rollback_exc:
                    rollback_errors.append(rollback_exc)
        for backed_up, backup, destination in (
            (output_backed_up, output_backup, writer.output),
            (receipt_backed_up, receipt_backup, receipt_output),
        ):
            if backed_up and backup is not None:
                try:
                    os.replace(backup, destination)
                except OSError as rollback_exc:
                    rollback_errors.append(rollback_exc)
        if rollback_errors:
            raise ExportError(f"view/receipt commit failed and rollback failed: {rollback_errors[0]}") from exc
        raise
    finally:
        writer.abort()
        receipt_temporary.unlink(missing_ok=True)
        if output_backup is not None:
            output_backup.unlink(missing_ok=True)
        if receipt_backup is not None:
            receipt_backup.unlink(missing_ok=True)


def finalize_export(
    *,
    writer: AtomicJsonl,
    receipt_output: Path,
    view_kind: str,
    input_artifacts: list[dict[str, Any]],
    counts: Counter[str],
    registry: EvaluationExclusionRegistry,
    schemas_used: Sequence[Path],
    receipt_validator: Draft202012Validator,
    admissions: Mapping[str, SourceAdmission] | None,
    deduplication_fingerprints: int | None,
    deduplication_partitioning: str,
    ordering: str,
) -> dict[str, Any]:
    receipt_temporary: Path | None = None
    try:
        output_artifact = writer.finish()
        output_artifact["role"] = f"{view_kind}_view"
        receipt = {
            "admission": admission_receipt(admissions),
            "counts": dict(sorted(counts.items())),
            "deduplication": deduplication_receipt(
                deduplication_fingerprints,
                partitioning=deduplication_partitioning,
            ),
            "determinism": {
                "ordering": ordering,
                "serialization": "UTF-8 canonical JSON with sorted keys and LF",
                "timestamps_omitted": True,
            },
            "evaluation_exclusion_registry": registry_receipt(registry),
            "input_artifacts": input_artifacts,
            "output": output_artifact,
            "safety": {
                "evaluation_data_entered_non_evaluation_view": False,
                "local_artifact_written": True,
                "private_data_exported": False,
                "publication_performed": False,
                "test_fixture_mode": bool(counts.get("fixture_records", 0)),
                "training_performed": False,
                "upload_performed": False,
            },
            "schema_version": "model_view_export_receipt_v1",
            "schemas": {path.name: sha256_file(path) for path in sorted(set(schemas_used), key=lambda item: item.name)},
            "view_kind": view_kind,
        }
        validate_schema(receipt, receipt_validator, label="model-view receipt")
        receipt_bytes = (canonical_json(receipt) + "\n").encode("utf-8")
        receipt_output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=receipt_output.parent,
            prefix=receipt_output.name,
            suffix=".tmp",
            delete=False,
        ) as handle:
            receipt_temporary = Path(handle.name)
            handle.write(receipt_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        replace_output_pair(
            writer=writer,
            receipt_temporary=receipt_temporary,
            receipt_output=receipt_output,
        )
        return receipt
    except Exception:
        writer.abort()
        if receipt_temporary is not None:
            receipt_temporary.unlink(missing_ok=True)
        raise


def export_pretraining(
    *,
    source_records_path: Path,
    payloads_path: Path,
    origin: str,
    representation_view: str,
    output: Path,
    receipt_output: Path,
    allow_test_fixtures: bool,
    v011_manifest: Path,
    v02_packet: Path,
    extra_evaluation_artifacts: Sequence[Path],
) -> dict[str, Any]:
    schemas, schema_registry = schema_bundle()
    payload_validator = validator_for(SOURCE_PAYLOAD_SCHEMA, schemas=schemas, registry=schema_registry)
    output_validator = validator_for(PRETRAIN_SCHEMA, schemas=schemas, registry=schema_registry)
    receipt_validator = validator_for(EXPORT_RECEIPT_SCHEMA, schemas=schemas, registry=schema_registry)
    admissions, source_count = load_source_admissions(source_records_path)
    exclusion_registry = build_exclusion_registry(
        v011_manifest=v011_manifest,
        v02_packet=v02_packet,
        extra_artifacts=extra_evaluation_artifacts,
    )
    writer = AtomicJsonl.open(output)
    deduplication_registry = empty_text_registry()
    counts: Counter[str] = Counter()
    previous_id: str | None = None
    try:
        for line_number, payload in iter_jsonl(payloads_path):
            counts["input_records"] += 1
            validate_schema(payload, payload_validator, label=f"source payload line {line_number}")
            validate_source_payload_semantics(payload)
            previous_id = require_stable_order(payload["payload_id"], previous_id, label="source payload")
            if payload["test_fixture"] and not allow_test_fixtures:
                raise ExportError("test fixture source payload requires --allow-test-fixtures")
            require(payload["origin"] == origin, "source payload origin differs from homogeneous export origin")
            admission = admissions.get(payload["source_record_id"])
            reason = safety_reason_for_source_payload(payload, admission, exclusion_registry)
            if (
                reason is None
                and representation_view == "modern_literary_ukrainian"
                and any(
                    span["modern_loss_action"] == "exclude_record"
                    for span in payload["language_span_review"]["character_spans"]
                )
            ):
                reason = "modern_view_record_excluded"
            if reason is not None:
                counts["excluded_records"] += 1
                counts[f"excluded_{reason}"] += 1
                continue
            duplicate = deduplication_registry.match(payload["text"])
            if duplicate.matched:
                counts["excluded_records"] += 1
                counts[f"excluded_intra_view_duplicate_{duplicate.method}"] += 1
                continue
            assert admission is not None
            mask_spans = []
            if representation_view == "modern_literary_ukrainian":
                mask_spans = [
                    {
                        "end_char": span["end"],
                        "reason": span["reason"],
                        "start_char": span["start"],
                    }
                    for span in payload["language_span_review"]["character_spans"]
                    if span["modern_loss_action"] == "mask_from_loss"
                ]
            lineage = source_lineage(admission, payload=payload)
            record_id = "pretrain:" + sha256_text(
                canonical_json(
                    {
                        "lineage": lineage,
                        "representation_view": representation_view,
                        "text_sha256": payload["text_sha256"],
                    }
                )
            )
            row = {
                "denied_destinations": [
                    "supervised_correction",
                    "pairwise_preference",
                    "quality_filter",
                    "heldout_evaluation",
                ],
                "eligibility": eligibility(test_fixture=payload["test_fixture"]),
                "lineage": lineage,
                "origin": origin,
                "payload": {
                    "character_mask_spans": mask_spans,
                    "text": payload["text"],
                    "text_sha256": payload["text_sha256"],
                },
                "permitted_destination": "continued_pretraining",
                "record_id": record_id,
                "representation_view": representation_view,
                "schema_version": "continued_pretraining_view_v1",
            }
            validate_schema(row, output_validator, label="continued-pretraining output")
            deduplication_registry.add_text(payload["text"], explicit_evaluation_text=True)
            writer.write(row)
            counts["exported_records"] += 1
            counts["fixture_records" if payload["test_fixture"] else "model_training_eligible_records"] += 1
        require(counts["input_records"] > 0, "empty source-payload input")
        return finalize_export(
            writer=writer,
            receipt_output=receipt_output,
            view_kind="continued_pretraining",
            input_artifacts=[
                artifact(source_records_path, role="source_records", records=source_count),
                artifact(payloads_path, role="source_payloads", records=counts["input_records"]),
            ],
            counts=counts,
            registry=exclusion_registry,
            schemas_used=(SOURCE_RECORD_SCHEMA, SOURCE_PAYLOAD_SCHEMA, PRETRAIN_SCHEMA, EXPORT_RECEIPT_SCHEMA),
            receipt_validator=receipt_validator,
            admissions=admissions,
            deduplication_fingerprints=len(deduplication_registry.exact_hashes),
            deduplication_partitioning="source text",
            ordering="validated ascending source payload ID",
        )
    except Exception:
        writer.abort()
        raise


def correction_output_row(
    *,
    view_kind: str,
    record: Mapping[str, Any],
    admission: SourceAdmission,
    origin: str,
    test_fixture: bool,
) -> tuple[dict[str, Any], list[str]]:
    candidate = record["candidate"]
    decision = record["decision"]
    final = decision["final"]
    context = candidate["source"]["context"]
    span = candidate["span"]
    target, local_start, local_end = (
        corrected_context(record)
        if final["decision"] == "correction"
        else (context["text"], span["start"] - context["start"], span["end"] - context["start"])
    )
    lineage = source_lineage(admission, correction_record=record)
    common = {
        "eligibility": eligibility(test_fixture=test_fixture, qualified=True),
        "lineage": lineage,
        "origin": origin,
    }
    alternatives = final["acceptable_alternatives"]
    if view_kind == "correction_instruction":
        payload = {
            "acceptable_alternatives": alternatives,
            "accepted_correction": final["accepted_correction"],
            "input_text": context["text"],
            "original_span": span["text"],
            "span_end_char": local_end,
            "span_start_char": local_start,
            "target_text": target,
        }
        identity = {"lineage": lineage, "payload": payload}
        row = {
            **common,
            "denied_destinations": [
                "continued_pretraining",
                "pairwise_preference",
                "quality_filter",
                "heldout_evaluation",
            ],
            "payload": payload,
            "permitted_destination": "supervised_correction",
            "record_id": "correction-view:" + sha256_text(canonical_json(identity)),
            "schema_version": "correction_instruction_view_v1",
        }
        texts = [context["text"], target, span["text"], final["accepted_correction"], *alternatives]
        return row, texts
    if view_kind == "preference":
        payload = {
            "acceptable_alternatives": alternatives,
            "chosen": final["accepted_correction"],
            "prompt": context["text"],
            "rejected": span["text"],
        }
        identity = {"lineage": lineage, "payload": payload}
        row = {
            **common,
            "denied_destinations": [
                "continued_pretraining",
                "supervised_correction",
                "quality_filter",
                "heldout_evaluation",
            ],
            "payload": payload,
            "permitted_destination": "pairwise_preference",
            "record_id": "preference-view:" + sha256_text(canonical_json(identity)),
            "schema_version": "preference_view_v1",
        }
        texts = [context["text"], final["accepted_correction"], span["text"], *alternatives]
        return row, texts
    label = "needs_correction" if final["decision"] == "correction" else "acceptable"
    payload = {
        "decision": final["decision"],
        "label": label,
        "text": context["text"],
    }
    identity = {"lineage": lineage, "payload": payload}
    row = {
        **common,
        "denied_destinations": [
            "continued_pretraining",
            "supervised_correction",
            "pairwise_preference",
            "heldout_evaluation",
        ],
        "payload": payload,
        "permitted_destination": "quality_filter",
        "record_id": "quality-view:" + sha256_text(canonical_json(identity)),
        "schema_version": "quality_filter_view_v1",
    }
    return row, [context["text"]]


def export_correction_family(
    *,
    view_kind: str,
    source_records_path: Path,
    correction_records_path: Path,
    origin: str,
    output: Path,
    receipt_output: Path,
    allow_test_fixtures: bool,
    v011_manifest: Path,
    v02_packet: Path,
    extra_evaluation_artifacts: Sequence[Path],
) -> dict[str, Any]:
    require(view_kind in {"correction_instruction", "preference", "quality_filter"}, "invalid correction-family view")
    schemas, schema_registry = schema_bundle()
    candidate_validator = validator_for(CANDIDATE_SCHEMA, schemas=schemas, registry=schema_registry)
    decision_validator = validator_for(DECISION_SCHEMA, schemas=schemas, registry=schema_registry)
    correction_validator = validator_for(CORRECTION_RECORD_SCHEMA, schemas=schemas, registry=schema_registry)
    output_validator = validator_for(VIEW_SCHEMAS[view_kind], schemas=schemas, registry=schema_registry)
    receipt_validator = validator_for(EXPORT_RECEIPT_SCHEMA, schemas=schemas, registry=schema_registry)
    admissions, source_count = load_source_admissions(source_records_path)
    exclusion_registry = build_exclusion_registry(
        v011_manifest=v011_manifest,
        v02_packet=v02_packet,
        extra_artifacts=extra_evaluation_artifacts,
    )
    evaluation_registry = correction_factory.load_evaluation_registry(
        v011_manifest_path=v011_manifest,
        v02_packet_path=v02_packet,
    )
    writer = AtomicJsonl.open(output)
    deduplication_registries: dict[str, EvaluationExclusionRegistry] = {}
    counts: Counter[str] = Counter()
    seen_record_ids: set[str] = set()
    try:
        for _line_number, record in iter_jsonl(correction_records_path):
            counts["input_records"] += 1
            record_id = record.get("record_id", "")
            require(
                record_id not in seen_record_ids,
                "correction record IDs must be unique",
            )
            seen_record_ids.add(record_id)
            validate_correction_handoff(
                record,
                candidate_validator=candidate_validator,
                decision_validator=decision_validator,
                record_validator=correction_validator,
                evaluation_registry=evaluation_registry,
                allow_test_fixtures=allow_test_fixtures,
            )
            fixture = correction_fixture_state(record)
            if fixture and not allow_test_fixtures:
                raise ExportError("fixture reviewer requires --allow-test-fixtures")
            candidate = record["candidate"]
            require(
                candidate["source"]["origin"] == origin,
                "correction record origin differs from homogeneous export origin",
            )
            admission = admissions.get(candidate["source"]["source_record_id"])
            reason = correction_source_reason(record, admission)
            final_decision = record["decision"]["final"]["decision"]
            if reason is None and view_kind in {"correction_instruction", "preference"}:
                export_control = record["export_control"]
                production_handoff = (
                    export_control["qualified_correction_intake"] is True
                    and export_control["handoff"] == "correction_intake_ready"
                    and record["safety_blockers"] == []
                    and final_decision == "correction"
                )
                fixture_proof_handoff = (
                    fixture
                    and allow_test_fixtures
                    and record["safety_blockers"] == ["test_fixture_reviewer"]
                    and record["decision"]["review_state"] == "adjudicated"
                    and final_decision == "correction"
                )
                if not (production_handoff or fixture_proof_handoff):
                    reason = "qualified_correction_handoff_missing"
            if reason is None and view_kind == "quality_filter":
                if final_decision not in {"correction", "acceptable_as_is"}:
                    reason = "quality_decision_not_eligible"
                else:
                    allowed_blockers = set()
                    if final_decision == "acceptable_as_is":
                        allowed_blockers.add("decision_not_correction")
                    if fixture and allow_test_fixtures:
                        allowed_blockers.add("test_fixture_reviewer")
                    unexpected = set(record["safety_blockers"]) - allowed_blockers
                    if unexpected:
                        reason = "quality_safety_blocker"
                    elif record["decision"]["review_state"] != "adjudicated":
                        reason = "quality_review_unresolved"
            if reason is not None:
                counts["excluded_records"] += 1
                counts[f"excluded_{reason}"] += 1
                continue
            assert admission is not None
            row, text_fields = correction_output_row(
                view_kind=view_kind,
                record=record,
                admission=admission,
                origin=origin,
                test_fixture=fixture,
            )
            contamination = any_contamination(text_fields, exclusion_registry)
            if contamination.matched:
                counts["excluded_records"] += 1
                counts[f"excluded_evaluation_contamination_{contamination.method}"] += 1
                continue
            deduplication_signature, deduplication_text = correction_deduplication_parts(view_kind, row)
            deduplication_registry = deduplication_registries.setdefault(deduplication_signature, empty_text_registry())
            duplicate = deduplication_registry.match(deduplication_text)
            if duplicate.matched:
                counts["excluded_records"] += 1
                counts[f"excluded_intra_view_duplicate_{duplicate.method}"] += 1
                continue
            validate_schema(row, output_validator, label=f"{view_kind} output")
            deduplication_registry.add_text(deduplication_text, explicit_evaluation_text=True)
            writer.write(row)
            counts["exported_records"] += 1
            counts["fixture_records" if fixture else "model_training_eligible_records"] += 1
        require(counts["input_records"] > 0, "empty correction-record input")
        return finalize_export(
            writer=writer,
            receipt_output=receipt_output,
            view_kind=view_kind,
            input_artifacts=[
                artifact(source_records_path, role="source_records", records=source_count),
                artifact(correction_records_path, role="correction_records", records=counts["input_records"]),
            ],
            counts=counts,
            registry=exclusion_registry,
            schemas_used=(
                SOURCE_RECORD_SCHEMA,
                CANDIDATE_SCHEMA,
                DECISION_SCHEMA,
                CORRECTION_RECORD_SCHEMA,
                VIEW_SCHEMAS[view_kind],
                EXPORT_RECEIPT_SCHEMA,
            ),
            receipt_validator=receipt_validator,
            admissions=admissions,
            deduplication_fingerprints=sum(
                len(registry.exact_hashes) for registry in deduplication_registries.values()
            ),
            deduplication_partitioning=("exact destination semantic signature, then plain-text context"),
            ordering="canonical upstream packet order; unique correction record ID",
        )
    except Exception:
        writer.abort()
        raise


def evaluation_rows(*, v011_manifest: Path, v02_packet: Path, release: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    artifacts = {
        "v0.1.1": (v011_manifest, "frozen_public", v011_items(v011_manifest)),
        "v0.2": (v02_packet, "frozen_review_inventory", v02_items(v02_packet)),
    }
    selected = ("v0.1.1", "v0.2") if release == "all" else (release,)
    for version in selected:
        path, state, items = artifacts[version]
        artifact_hash = sha256_file(path)
        for item in items:
            identity = {"item_id": item["item_id"], "release": version, "source_sha256": item["source_sha256"]}
            rows.append(
                {
                    "denied_destinations": [
                        "continued_pretraining",
                        "supervised_correction",
                        "pairwise_preference",
                        "quality_filter",
                    ],
                    "evaluation_release": version,
                    "evaluation_state": state,
                    "lineage": {
                        "artifact_logical_path": logical_path(path),
                        "artifact_sha256": artifact_hash,
                        "item_id": item["item_id"],
                    },
                    "model_training_eligible": False,
                    "payload": {
                        "references": item["references"],
                        "source": item["source"],
                        "source_sha256": item["source_sha256"],
                    },
                    "permitted_destination": "heldout_evaluation",
                    "record_id": "evaluation-view:" + sha256_text(canonical_json(identity)),
                    "schema_version": "heldout_evaluation_view_v1",
                }
            )
    return sorted(
        rows,
        key=lambda row: (
            row["evaluation_release"],
            row["lineage"]["item_id"],
        ),
    )


def export_evaluation(
    *,
    release: str,
    output: Path,
    receipt_output: Path,
    v011_manifest: Path,
    v02_packet: Path,
    extra_evaluation_artifacts: Sequence[Path],
) -> dict[str, Any]:
    schemas, schema_registry = schema_bundle()
    output_validator = validator_for(EVALUATION_SCHEMA, schemas=schemas, registry=schema_registry)
    receipt_validator = validator_for(EXPORT_RECEIPT_SCHEMA, schemas=schemas, registry=schema_registry)
    exclusion_registry = build_exclusion_registry(
        v011_manifest=v011_manifest,
        v02_packet=v02_packet,
        extra_artifacts=extra_evaluation_artifacts,
    )
    rows = evaluation_rows(v011_manifest=v011_manifest, v02_packet=v02_packet, release=release)
    writer = AtomicJsonl.open(output)
    counts: Counter[str] = Counter()
    try:
        for row in rows:
            validate_schema(row, output_validator, label="held-out evaluation output")
            writer.write(row)
            counts["exported_records"] += 1
            counts[f"release_{row['evaluation_release']}"] += 1
        input_artifacts = []
        if release in {"v0.1.1", "all"}:
            input_artifacts.append(
                artifact(v011_manifest, role="v0.1.1_manifest", records=len(v011_items(v011_manifest)))
            )
        if release in {"v0.2", "all"}:
            input_artifacts.append(artifact(v02_packet, role="v0.2_packet", records=len(v02_items(v02_packet))))
        return finalize_export(
            writer=writer,
            receipt_output=receipt_output,
            view_kind="heldout_evaluation",
            input_artifacts=input_artifacts,
            counts=counts,
            registry=exclusion_registry,
            schemas_used=(EVALUATION_SCHEMA, EXPORT_RECEIPT_SCHEMA),
            receipt_validator=receipt_validator,
            admissions=None,
            deduplication_fingerprints=None,
            deduplication_partitioning="not applicable",
            ordering="evaluation release then item ID",
        )
    except Exception:
        writer.abort()
        raise


def validate_view_artifact(
    *,
    view_path: Path,
    view_kind: str,
    validator: Draft202012Validator,
) -> tuple[int, int, int]:
    seen_ids: set[str] = set()
    total = 0
    eligible = 0
    fixtures = 0
    for line_number, row in iter_jsonl(view_path):
        validate_schema(row, validator, label=f"view artifact line {line_number}")
        require(row["record_id"] not in seen_ids, "view artifact contains duplicate record IDs")
        seen_ids.add(row["record_id"])
        total += 1
        if view_kind == "heldout_evaluation":
            continue
        row_eligibility = row["eligibility"]
        eligible += int(row_eligibility["model_training_eligible"])
        fixtures += int(row_eligibility["test_fixture"])
    return total, eligible, fixtures


def build_recipe_manifest(
    *,
    config_path: Path,
    view_path: Path,
    view_receipt_path: Path,
    output: Path,
    allow_test_fixtures: bool,
) -> dict[str, Any]:
    schemas, schema_registry = schema_bundle()
    config_validator = validator_for(RECIPE_CONFIG_SCHEMA, schemas=schemas, registry=schema_registry)
    manifest_validator = validator_for(RECIPE_MANIFEST_SCHEMA, schemas=schemas, registry=schema_registry)
    receipt_validator = validator_for(EXPORT_RECEIPT_SCHEMA, schemas=schemas, registry=schema_registry)
    config = read_json(config_path)
    validate_schema(config, config_validator, label="training recipe config")
    view_kind = config["view_kind"]
    require(config["objective"] == OBJECTIVES[view_kind], "recipe objective does not match view")
    preparation = config["data_preparation"]
    require(
        preparation["rendering_template_sha256"] == sha256_text(preparation["rendering_template"]),
        "recipe rendering template hash mismatch",
    )
    require(
        preparation["target_loss_policy"] == TARGET_LOSS_POLICIES[view_kind],
        "recipe target-loss policy does not match view",
    )
    split = preparation["split"]
    if view_kind == "heldout_evaluation":
        require(
            split["strategy"] == "preserve_evaluation_release"
            and split["modulus"] is None
            and split["validation_buckets"] is None,
            "evaluation recipe must preserve the frozen evaluation release",
        )
    else:
        require(
            split["strategy"] == "sha256_record_id_modulo"
            and isinstance(split["modulus"], int)
            and isinstance(split["validation_buckets"], int)
            and split["validation_buckets"] < split["modulus"],
            "training recipe requires a valid deterministic validation split",
        )
    hyperparameters = config["hyperparameters"]
    require(
        Decimal(hyperparameters["learning_rate"]) > 0,
        "recipe learning_rate must be greater than zero",
    )
    require(
        Decimal(hyperparameters["weight_decay"]) >= 0,
        "recipe weight_decay must not be negative",
    )
    require(
        Decimal(hyperparameters["epochs"]) > 0,
        "recipe epochs must be greater than zero",
    )
    view_receipt = read_json(view_receipt_path)
    validate_schema(view_receipt, receipt_validator, label="view receipt")
    require(view_receipt["view_kind"] == view_kind, "view receipt kind does not match recipe")
    view_validator = validator_for(VIEW_SCHEMAS[view_kind], schemas=schemas, registry=schema_registry)
    records, eligible_records, fixture_records = validate_view_artifact(
        view_path=view_path,
        view_kind=view_kind,
        validator=view_validator,
    )
    view_artifact = {
        "bytes": view_path.stat().st_size,
        "records": records,
        "sha256": sha256_file(view_path),
    }
    require(view_receipt["output"]["records"] == records, "view receipt record count mismatch")
    require(view_receipt["output"]["bytes"] == view_artifact["bytes"], "view receipt byte count mismatch")
    require(view_receipt["output"]["sha256"] == view_artifact["sha256"], "view receipt hash mismatch")
    if view_kind != "heldout_evaluation":
        require(records > 0, "training recipe cannot bind an empty non-evaluation view")
        if fixture_records and not allow_test_fixtures:
            raise ExportError("fixture view requires --allow-test-fixtures for recipe proof")
        require(
            fixture_records == 0 or eligible_records == 0,
            "fixture and model-training-eligible rows cannot share a view",
        )
    config_hash = sha256_text(canonical_json(config))
    view_receipt_artifact = {
        "bytes": view_receipt_path.stat().st_size,
        "records": 1,
        "sha256": sha256_file(view_receipt_path),
    }
    manifest_identity = {
        "config_sha256": config_hash,
        "view_receipt_sha256": view_receipt_artifact["sha256"],
        "view_sha256": view_artifact["sha256"],
    }
    manifest = {
        "config": config,
        "config_sha256": config_hash,
        "determinism": {
            "serialization": "UTF-8 canonical JSON with sorted keys and LF",
            "timestamps_omitted": True,
        },
        "execution": {
            "execution_state": "not_run",
            "model_call_performed": False,
            "test_fixture_mode": bool(fixture_records),
            "training_authorized": False,
            "training_performed": False,
        },
        "manifest_id": "recipe:" + sha256_text(canonical_json(manifest_identity)),
        "preparation": {
            "input_validation": "validate every JSONL row against the bound view schema before preparation",
            "loss_mask_projection": (
                "tokenizer projects character_mask_spans after tokenization; masked tokens receive zero loss"
                if view_kind == "continued_pretraining"
                else "not applicable to this view"
            ),
            "model_training_eligible_records": eligible_records,
            "record_order": "view artifact order bound by export receipt",
            "shuffle": (
                "not applicable; preserve held-out artifact order"
                if view_kind == "heldout_evaluation"
                else "SHA-256(seed || record_id), ascending digest"
            ),
            "test_fixture_records": fixture_records,
        },
        "schema_hashes": {
            path.name: sha256_file(path)
            for path in sorted(
                {RECIPE_CONFIG_SCHEMA, RECIPE_MANIFEST_SCHEMA, EXPORT_RECEIPT_SCHEMA, VIEW_SCHEMAS[view_kind]},
                key=lambda item: item.name,
            )
        },
        "schema_version": "training_recipe_manifest_v1",
        "view_artifact": view_artifact,
        "view_receipt": view_receipt_artifact,
    }
    validate_schema(manifest, manifest_validator, label="training recipe manifest")
    output_bytes = (canonical_json(manifest) + "\n").encode("utf-8")
    write_json_atomic(output, output_bytes)
    return manifest


def write_json_atomic(path: Path, value: bytes) -> None:
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
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def add_evaluation_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--v011-manifest", type=Path, default=DEFAULT_V011_MANIFEST)
    parser.add_argument("--v02-packet", type=Path, default=DEFAULT_V02_PACKET)
    parser.add_argument(
        "--extra-evaluation-artifact",
        action="append",
        type=Path,
        default=[],
        help="Additional evaluation-only or derived-rule artifact to fingerprint",
    )


def add_common_export_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-records", type=Path, required=True)
    parser.add_argument("--origin", choices=ORIGINS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--allow-test-fixtures", action="store_true")
    add_evaluation_options(parser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build disjoint Ukrainian Data Foundry model-consumer views")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pretraining = subparsers.add_parser("continued-pretraining")
    add_common_export_options(pretraining)
    pretraining.add_argument("--payloads", type=Path, required=True)
    pretraining.add_argument(
        "--representation-view",
        choices=("faithful_literary", "modern_literary_ukrainian"),
        required=True,
    )

    for command in ("correction", "preference", "quality-filter"):
        child = subparsers.add_parser(command)
        add_common_export_options(child)
        child.add_argument("--correction-records", type=Path, required=True)

    evaluation = subparsers.add_parser("evaluation")
    evaluation.add_argument("--release", choices=("v0.1.1", "v0.2", "all"), default="all")
    evaluation.add_argument("--output", type=Path, required=True)
    evaluation.add_argument("--receipt-output", type=Path, required=True)
    add_evaluation_options(evaluation)

    recipe = subparsers.add_parser("recipe")
    recipe.add_argument("--config", type=Path, required=True)
    recipe.add_argument("--view-artifact", type=Path, required=True)
    recipe.add_argument("--view-receipt", type=Path, required=True)
    recipe.add_argument("--output", type=Path, required=True)
    recipe.add_argument("--allow-test-fixtures", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "continued-pretraining":
            receipt = export_pretraining(
                source_records_path=args.source_records,
                payloads_path=args.payloads,
                origin=args.origin,
                representation_view=args.representation_view,
                output=args.output,
                receipt_output=args.receipt_output,
                allow_test_fixtures=args.allow_test_fixtures,
                v011_manifest=args.v011_manifest,
                v02_packet=args.v02_packet,
                extra_evaluation_artifacts=args.extra_evaluation_artifact,
            )
            print(canonical_json(receipt))
            return 0
        if args.command in {"correction", "preference", "quality-filter"}:
            view_kind = {
                "correction": "correction_instruction",
                "preference": "preference",
                "quality-filter": "quality_filter",
            }[args.command]
            receipt = export_correction_family(
                view_kind=view_kind,
                source_records_path=args.source_records,
                correction_records_path=args.correction_records,
                origin=args.origin,
                output=args.output,
                receipt_output=args.receipt_output,
                allow_test_fixtures=args.allow_test_fixtures,
                v011_manifest=args.v011_manifest,
                v02_packet=args.v02_packet,
                extra_evaluation_artifacts=args.extra_evaluation_artifact,
            )
            print(canonical_json(receipt))
            return 0
        if args.command == "evaluation":
            receipt = export_evaluation(
                release=args.release,
                output=args.output,
                receipt_output=args.receipt_output,
                v011_manifest=args.v011_manifest,
                v02_packet=args.v02_packet,
                extra_evaluation_artifacts=args.extra_evaluation_artifact,
            )
            print(canonical_json(receipt))
            return 0
        manifest = build_recipe_manifest(
            config_path=args.config,
            view_path=args.view_artifact,
            view_receipt_path=args.view_receipt,
            output=args.output,
            allow_test_fixtures=args.allow_test_fixtures,
        )
        print(canonical_json(manifest))
        return 0
    except (ExportError, correction_factory.FactoryError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
