#!/usr/bin/env python3
"""Deterministic, non-correction representation for historical Ukrainian data.

The representation preserves attributed historical layers and uncertainty.  It
never promotes a historical form into modern correction gold and never treats
model output as linguistic authority.
"""

from __future__ import annotations

import copy
import functools
import json
import unicodedata
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data.phase3_linguistic_representation import (
    CLAIM_TYPES,
    CONSUMER_VIEWS,
    PRIMARY_ROLE_IDS,
    canonical_json,
    sha256_bytes,
    sha256_text,
    sha256_value,
    tokenize,
)

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_historical_representation_v3.schema.json"
SCHEMA_VERSION = "phase3_historical_representation_v3"

TEXT_LAYER_IDS = frozenset({"original_diplomatic", "restored_reading", "modern_ukrainian_translation"})
HISTORICAL_PRIMARY_ROLES = frozenset(
    {"historical_or_literary_excerpt", "quotation", "metalinguistic_mention", "ambiguous_or_ocr"}
)
HISTORICAL_CLAIM_TYPES = frozenset({"historical_advice", "attestation_only", "unresolved"})
DERIVED_BUNDLES = frozenset(
    {
        "historical_recognition",
        "historical_alignment",
        "periodization",
        "language_label_disambiguation",
        "language_change_explanation",
    }
)


class HistoricalRepresentationError(ValueError):
    """The historical representation is structurally inconsistent."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HistoricalRepresentationError(message)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


@functools.cache
def _schema_validator() -> Draft202012Validator:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalRepresentationError(f"cannot read historical representation schema: {SCHEMA_PATH}") from exc
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _validate_schema(value: Mapping[str, Any]) -> None:
    errors = sorted(_schema_validator().iter_errors(value), key=lambda item: list(item.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "packet"
        raise HistoricalRepresentationError(f"schema violation at {location}: {errors[0].message}")


def _normalization(text: str) -> dict[str, Any]:
    nfc = unicodedata.normalize("NFC", text)
    nfkc = unicodedata.normalize("NFKC", text)
    return {
        "nfc": nfc,
        "nfkc": nfkc,
        "nfc_sha256": sha256_text(nfc),
        "nfkc_sha256": sha256_text(nfkc),
        "source_is_nfc": text == nfc,
        "source_is_nfkc": text == nfkc,
    }


def _normalize_text_layer(raw: Mapping[str, Any]) -> dict[str, Any]:
    base_fields = {"layer_id", "text", "authority", "evidence_ids"}
    _require(
        set(raw) in {frozenset(base_fields), frozenset(base_fields | {"tokens"})},
        "text layer input fields must be exact",
    )
    layer_id = raw["layer_id"]
    text = raw["text"]
    _require(layer_id in TEXT_LAYER_IDS, "unknown historical text layer")
    _require(isinstance(text, str) and text, "historical text layer must contain complete text")
    span = {"start": 0, "end": len(text)}
    return {
        "layer_id": layer_id,
        "text": text,
        "text_utf8_sha256": sha256_bytes(text.encode("utf-8")),
        "text_sha256": sha256_text(text),
        "offset_basis": "unicode_code_points",
        "source_layer_preserved": True,
        "normalization": _normalization(text),
        "tokens": (
            [dict(token) for token in raw["tokens"]]
            if "tokens" in raw
            else tokenize(text, paragraph_span=span, sentence_span=span)
        ),
        "authority": raw["authority"],
        "evidence_ids": list(raw["evidence_ids"]),
    }


def _validate_source_tokens(text: str, tokens: Sequence[Mapping[str, Any]]) -> None:
    """Validate an authoritative source-token layer without retokenizing it."""
    _require(bool(tokens), "source-token layer must not be empty")
    previous_end = 0
    for index, token in enumerate(tokens, start=1):
        _require(token["token_id"] == f"tok:{index:06d}", "source-token ids must be sequential")
        start, end = token["start"], token["end"]
        _require(start >= previous_end and start < end <= len(text), "source-token offsets are invalid")
        _require(text[previous_end:start].isspace() or start == previous_end, "source-token gap is not whitespace")
        _require(text[start:end] == token["text"], "source token does not round-trip Unicode offsets")
        _require(
            token["normalized_text"] == unicodedata.normalize("NFC", token["text"]),
            "source-token normalization is stale",
        )
        has_lexical_character = any(
            unicodedata.category(char)[0] in {"L", "N", "M"} or char == "_" for char in token["text"]
        )
        expected_kind = "word" if has_lexical_character else "punctuation"
        _require(token["kind"] == expected_kind, "source-token kind is inconsistent with its surface")
        previous_end = end
    _require(text[previous_end:].isspace() or previous_end == len(text), "source-token trailing gap is not whitespace")


def _normalize_evidence(raw: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_id",
        "kind",
        "locator",
        "source_document_bytes_sha256",
        "evidence_text",
        "text_exposure",
        "authority",
        "rights",
    }
    _require(set(raw) == expected, "evidence input fields must be exact")
    locator = raw["locator"]
    text = raw["evidence_text"]
    _require(isinstance(locator, Mapping) and locator, "evidence locator is required")
    _require(isinstance(text, str) and text, "evidence text is required")
    return {
        "evidence_id": raw["evidence_id"],
        "kind": raw["kind"],
        "locator": dict(locator),
        "locator_sha256": sha256_value(locator),
        "source_document_bytes_sha256": raw["source_document_bytes_sha256"],
        "evidence_text": text,
        "evidence_text_sha256": sha256_text(text),
        "text_exposure": raw["text_exposure"],
        "authority": raw["authority"],
        "rights": dict(raw["rights"]),
    }


def _normalize_alignment(raw: Mapping[str, Any], layers: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    expected = {
        "alignment_id",
        "from_layer_id",
        "to_layer_id",
        "segments",
        "authority",
        "evidence_ids",
        "ambiguity",
    }
    _require(set(raw) == expected, "alignment input fields must be exact")
    source_id, target_id = raw["from_layer_id"], raw["to_layer_id"]
    _require(source_id in layers and target_id in layers, "alignment refers to an unknown text layer")
    source_text, target_text = layers[source_id]["text"], layers[target_id]["text"]
    segments: list[dict[str, Any]] = []
    for segment in raw["segments"]:
        _require(
            set(segment) == {"source_start", "source_end", "target_start", "target_end"},
            "alignment segment input fields must be exact",
        )
        source_start, source_end = segment["source_start"], segment["source_end"]
        target_start, target_end = segment["target_start"], segment["target_end"]
        _require(
            all(isinstance(item, int) for item in (source_start, source_end, target_start, target_end)),
            "alignment offsets must be integers",
        )
        _require(0 <= source_start <= source_end <= len(source_text), "source alignment offset is outside layer")
        _require(0 <= target_start <= target_end <= len(target_text), "target alignment offset is outside layer")
        segments.append(
            {
                "source_start": source_start,
                "source_end": source_end,
                "source_text": source_text[source_start:source_end],
                "target_start": target_start,
                "target_end": target_end,
                "target_text": target_text[target_start:target_end],
            }
        )
    return {
        "alignment_id": raw["alignment_id"],
        "from_layer_id": source_id,
        "to_layer_id": target_id,
        "segments": segments,
        "authority": raw["authority"],
        "evidence_ids": list(raw["evidence_ids"]),
        "ambiguity": list(raw["ambiguity"]),
    }


def _normalize_feature(raw: Mapping[str, Any], layers: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    expected = {
        "feature_id",
        "domain",
        "claim",
        "layer_id",
        "spans",
        "status",
        "attribution",
        "evidence_ids",
        "ambiguity",
    }
    _require(set(raw) == expected, "linguistic feature input fields must be exact")
    layer_id = raw["layer_id"]
    _require(layer_id in layers, "linguistic feature refers to an unknown text layer")
    text = layers[layer_id]["text"]
    spans: list[dict[str, Any]] = []
    for span in raw["spans"]:
        _require(set(span) == {"start", "end"}, "feature span input fields must be exact")
        start, end = span["start"], span["end"]
        _require(isinstance(start, int) and isinstance(end, int), "feature offsets must be integers")
        _require(0 <= start <= end <= len(text), "feature offset is outside text layer")
        spans.append({"start": start, "end": end, "text": text[start:end]})
    return {
        "feature_id": raw["feature_id"],
        "domain": raw["domain"],
        "claim": raw["claim"],
        "layer_id": layer_id,
        "spans": spans,
        "status": raw["status"],
        "attribution": raw["attribution"],
        "evidence_ids": list(raw["evidence_ids"]),
        "ambiguity": list(raw["ambiguity"]),
    }


def build_historical_representation(
    *,
    record_id: str,
    collection_identity: str,
    document_or_edition_identity: str,
    source_record_identity: str,
    frozen_locator: Mapping[str, Any],
    source_document_bytes_sha256: str,
    source_record_bytes_sha256: str,
    historical_context: Mapping[str, Any],
    text_layers: Sequence[Mapping[str, Any]],
    alignments: Sequence[Mapping[str, Any]],
    periodizations: Sequence[Mapping[str, Any]],
    language_labels: Sequence[Mapping[str, Any]],
    language_layers: Sequence[Mapping[str, Any]],
    linguistic_features: Sequence[Mapping[str, Any]],
    interpretations: Sequence[Mapping[str, Any]],
    evidence: Sequence[Mapping[str, Any]],
    rights: Mapping[str, Any],
    derived_bundle_rights: Sequence[Mapping[str, Any]],
    primary_role_id: str = "historical_or_literary_excerpt",
    claim_type: str = "attestation_only",
    consumer_views: Sequence[str] = ("protection", "research_only"),
    derived_bundles: Sequence[str] = ("historical_recognition",),
    evidence_grade: str = "source_grounded_historical",
    linguistic_analyses: Sequence[Mapping[str, Any]] = (),
    analysis_provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build and validate one immutable historical source record."""
    for label, value in (
        ("record id", record_id),
        ("collection identity", collection_identity),
        ("document identity", document_or_edition_identity),
        ("source record identity", source_record_identity),
    ):
        _require(isinstance(value, str) and value, f"{label} is required")
    _require(isinstance(frozen_locator, Mapping) and frozen_locator, "frozen locator is required")
    _require(_is_sha256(source_document_bytes_sha256), "source document bytes SHA-256 is required")
    _require(_is_sha256(source_record_bytes_sha256), "source record bytes SHA-256 is required")
    _require(primary_role_id in PRIMARY_ROLE_IDS, "primary role is not frozen v2 vocabulary")
    _require(claim_type in CLAIM_TYPES, "claim type is not frozen v2 vocabulary")
    _require(set(consumer_views) <= CONSUMER_VIEWS, "consumer view is not frozen v2 vocabulary")
    _require(set(derived_bundles) <= DERIVED_BUNDLES, "unknown derived historical bundle")

    normalized_layers = [_normalize_text_layer(item) for item in text_layers]
    layers_by_id = {item["layer_id"]: item for item in normalized_layers}
    _require(len(layers_by_id) == len(normalized_layers), "duplicate historical text layer")
    normalized_evidence = [_normalize_evidence(item) for item in evidence]
    packet: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_id": record_id,
        "source": {
            "collection_identity": collection_identity,
            "document_or_edition_identity": document_or_edition_identity,
            "source_record_identity": source_record_identity,
            "frozen_locator": dict(frozen_locator),
            "frozen_locator_sha256": sha256_value(frozen_locator),
            "source_document_bytes_sha256": source_document_bytes_sha256,
            "source_record_bytes_sha256": source_record_bytes_sha256,
        },
        "historical_context": dict(historical_context),
        "text_layers": normalized_layers,
        "alignments": [_normalize_alignment(item, layers_by_id) for item in alignments],
        "periodizations": [dict(item) for item in periodizations],
        "language_labels": [dict(item) for item in language_labels],
        "language_layers": [dict(item) for item in language_layers],
        "linguistic_features": [_normalize_feature(item, layers_by_id) for item in linguistic_features],
        "interpretations": [dict(item) for item in interpretations],
        "linguistic_analyses": [dict(item) for item in linguistic_analyses],
        "analysis_provenance": dict(analysis_provenance or {"status": "absent"}),
        "evidence": normalized_evidence,
        "rights": dict(rights),
        "classification": {
            "primary_role_id": primary_role_id,
            "claim_type": claim_type,
            "consumer_views": list(consumer_views),
            "derived_bundles": list(derived_bundles),
            "derived_bundle_rights": [
                {"bundle_id": item["bundle_id"], "rights": dict(item["rights"])}
                for item in derived_bundle_rights
            ],
            "evidence_grade": evidence_grade,
        },
        "safeguards": {
            "historical_forms_protected": True,
            "modern_correction_eligible": False,
            "russkyi_auto_mapped_to_modern_russian": False,
            "old_east_slavic_is_modern_russian": False,
            "scalar_language_age_claim_allowed": False,
        },
        "provider_calls": False,
    }
    validate_historical_representation(packet)
    return packet


build_packet = build_historical_representation


def _assert_evidence_references(items: Sequence[Mapping[str, Any]], evidence_ids: set[str], label: str) -> None:
    for item in items:
        _require(set(item["evidence_ids"]) <= evidence_ids, f"{label} refers to unknown evidence")


def _validate_rights(rights: Mapping[str, Any], label: str) -> None:
    if rights["reuse_scope"] == "public_training":
        _require(rights["status"] == "admitted", f"{label} public training requires admitted rights")
        _require(rights["license"].casefold() not in {"unknown", "unresolved"}, f"{label} requires a license")


def _reachable_layers(alignments: Sequence[Mapping[str, Any]]) -> set[str]:
    reachable = {"original_diplomatic"}
    changed = True
    while changed:
        changed = False
        for alignment in alignments:
            if alignment["from_layer_id"] in reachable and alignment["to_layer_id"] not in reachable:
                reachable.add(alignment["to_layer_id"])
                changed = True
    return reachable


def validate_historical_representation(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate hashes, offsets, evidence, rights, and historical safeguards."""
    packet = copy.deepcopy(dict(value))
    _validate_schema(packet)
    _require(packet["provider_calls"] is False, "provider calls are forbidden")

    source = packet["source"]
    _require(source["frozen_locator_sha256"] == sha256_value(source["frozen_locator"]), "stale frozen locator hash")
    _require(_is_sha256(source["source_document_bytes_sha256"]), "invalid source document bytes hash")
    _require(_is_sha256(source["source_record_bytes_sha256"]), "invalid source record bytes hash")

    layers = packet["text_layers"]
    layer_ids = [item["layer_id"] for item in layers]
    _require(len(layer_ids) == len(set(layer_ids)), "duplicate historical text layer")
    _require(layer_ids.count("original_diplomatic") == 1, "exactly one original diplomatic layer is required")
    layers_by_id = {item["layer_id"]: item for item in layers}
    original = layers_by_id["original_diplomatic"]
    _require(original["authority"] == "source_transcription", "original layer must retain source authority")
    provenance = packet["analysis_provenance"]
    for layer in layers:
        text = layer["text"]
        _require(layer["text_utf8_sha256"] == sha256_bytes(text.encode("utf-8")), "stale text UTF-8 hash")
        _require(layer["text_sha256"] == sha256_text(text), "stale text hash")
        _require(layer["normalization"] == _normalization(text), "stale text normalization facts")
        span = {"start": 0, "end": len(text)}
        deterministic_tokens = tokenize(text, paragraph_span=span, sentence_span=span)
        if layer["tokens"] != deterministic_tokens:
            _require(
                provenance["status"] == "present" and provenance["tokenization_alignment"] == "exact",
                "non-deterministic source tokens require exact analysis provenance",
            )
            _validate_source_tokens(text, layer["tokens"])

    evidence = packet["evidence"]
    evidence_ids = [item["evidence_id"] for item in evidence]
    _require(len(evidence_ids) == len(set(evidence_ids)), "duplicate evidence id")
    evidence_id_set = set(evidence_ids)
    evidence_by_id = {item["evidence_id"]: item for item in evidence}
    for item in evidence:
        _require(item["locator_sha256"] == sha256_value(item["locator"]), "stale evidence locator hash")
        _require(item["evidence_text_sha256"] == sha256_text(item["evidence_text"]), "stale evidence text hash")
        _validate_rights(item["rights"], "evidence")
        if item["rights"]["reuse_scope"] != "public_training":
            _require(item["text_exposure"] != "verbatim", "non-public evidence cannot expose verbatim text")
    _require(
        any(
            item["kind"] == "source_record"
            and item["source_document_bytes_sha256"] == source["source_document_bytes_sha256"]
            and item["evidence_text_sha256"] == source["source_record_bytes_sha256"]
            and original["text"] in item["evidence_text"]
            for item in evidence
        ),
        "original text is not bound to source-record evidence",
    )

    _assert_evidence_references(layers, evidence_id_set, "text layer")
    alignment_ids = [item["alignment_id"] for item in packet["alignments"]]
    _require(len(alignment_ids) == len(set(alignment_ids)), "duplicate alignment id")
    for alignment in packet["alignments"]:
        _require(
            alignment["from_layer_id"] in layers_by_id and alignment["to_layer_id"] in layers_by_id,
            "alignment refers to an unknown text layer",
        )
        _require(alignment["from_layer_id"] != alignment["to_layer_id"], "alignment cannot target its own layer")
        source_text = layers_by_id[alignment["from_layer_id"]]["text"]
        target_text = layers_by_id[alignment["to_layer_id"]]["text"]
        previous_source_end = previous_target_end = -1
        for segment in alignment["segments"]:
            _require(segment["source_start"] >= previous_source_end, "alignment source segments overlap or reorder")
            _require(segment["target_start"] >= previous_target_end, "alignment target segments overlap or reorder")
            _require(
                source_text[segment["source_start"] : segment["source_end"]] == segment["source_text"],
                "stale source alignment offset",
            )
            _require(
                target_text[segment["target_start"] : segment["target_end"]] == segment["target_text"],
                "stale target alignment offset",
            )
            previous_source_end, previous_target_end = segment["source_end"], segment["target_end"]
    _assert_evidence_references(packet["alignments"], evidence_id_set, "alignment")
    _require(set(layer_ids) <= _reachable_layers(packet["alignments"]), "derived text layer is not aligned to original")

    context = packet["historical_context"]
    min_year, max_year = context["min_year"], context["max_year"]
    _require((min_year is None) == (max_year is None), "historical date bounds must be both present or both absent")
    if min_year is not None:
        _require(min_year <= max_year, "historical date range is reversed")
    if context["date_certainty"] == "unknown":
        _require(min_year is None, "unknown historical date cannot assert bounds")
    if context["date_certainty"] == "exact":
        _require(min_year is not None and min_year == max_year, "exact historical date must have one year")

    period_keys: set[tuple[str, str]] = set()
    for item in packet["periodizations"]:
        key = (item["framework_id"], item["stage_id"])
        _require(key not in period_keys, "duplicate periodization framework stage")
        period_keys.add(key)
        start_year, end_year = item["start_year"], item["end_year"]
        _require((start_year is None) == (end_year is None), "periodization bounds must be both present or absent")
        if start_year is not None:
            _require(start_year <= end_year, "periodization range is reversed")
            if min_year is not None:
                _require(start_year <= min_year and max_year <= end_year, "periodization stage excludes record date")
    _assert_evidence_references(packet["periodizations"], evidence_id_set, "periodization")
    _assert_evidence_references(packet["language_labels"], evidence_id_set, "language label")
    _assert_evidence_references(packet["language_layers"], evidence_id_set, "language layer")
    _assert_evidence_references(packet["interpretations"], evidence_id_set, "interpretation")

    for feature in packet["linguistic_features"]:
        _require(feature["layer_id"] in layers_by_id, "linguistic feature refers to an unknown text layer")
        text = layers_by_id[feature["layer_id"]]["text"]
        for span in feature["spans"]:
            _require(text[span["start"] : span["end"]] == span["text"], "stale linguistic feature offset")
    _assert_evidence_references(packet["linguistic_features"], evidence_id_set, "linguistic feature")

    analyses = packet["linguistic_analyses"]
    _require(
        (not analyses and provenance["status"] == "absent") or (analyses and provenance["status"] == "present"),
        "analysis provenance status disagrees with analyses",
    )
    token_positions_by_layer = {
        layer_id: {token["token_id"]: index for index, token in enumerate(layer["tokens"])}
        for layer_id, layer in layers_by_id.items()
    }
    analysis_by_id = {analysis["analysis_id"]: analysis for analysis in analyses}
    _require(len(analysis_by_id) == len(analyses), "duplicate linguistic analysis id")
    for analysis in analyses:
        layer_id = analysis["layer_id"]
        _require(layer_id in token_positions_by_layer, "analysis refers to an unknown text layer")
        token_positions = token_positions_by_layer[layer_id]
        _require(set(analysis["token_ids"]) <= set(token_positions), "analysis refers to an unknown token")
        positions = [token_positions[token_id] for token_id in analysis["token_ids"]]
        _require(
            positions == list(range(positions[0], positions[0] + len(positions))),
            "analysis tokens must be contiguous and source ordered",
        )
        layer_tokens = layers_by_id[layer_id]["tokens"]
        start, end = layer_tokens[positions[0]]["start"], layer_tokens[positions[-1]]["end"]
        _require(
            layers_by_id[layer_id]["text"][start:end] == analysis["source_surface"],
            "analysis source surface does not round-trip token offsets",
        )
        head = analysis["head_analysis_id"]
        _require(
            head is None or head in analysis_by_id,
            "analysis head refers to an unknown analysis",
        )
        if head is not None:
            _require(analysis_by_id[head]["layer_id"] == layer_id, "analysis head crosses text layers")

    if provenance["status"] == "present" and provenance["tokenization_alignment"] == "exact":
        token_references = [
            (analysis["layer_id"], token_id)
            for analysis in analyses
            for token_id in analysis["token_ids"]
        ]
        analysis_layer_ids = {analysis["layer_id"] for analysis in analyses}
        exact_layer_tokens = {
            (layer["layer_id"], token["token_id"])
            for layer in layers
            if layer["layer_id"] in analysis_layer_ids
            for token in layer["tokens"]
        }
        _require(
            len(token_references) == len(set(token_references)),
            "exact source-token analyses must not overlap",
        )
        _require(
            set(token_references) == exact_layer_tokens,
            "exact source-token analyses must cover every source token",
        )

    classification = packet["classification"]
    _require(classification["primary_role_id"] in HISTORICAL_PRIMARY_ROLES, "non-historical primary role is forbidden")
    _require(classification["claim_type"] in HISTORICAL_CLAIM_TYPES, "correction claim is forbidden for historical data")
    _require(set(classification["consumer_views"]) <= CONSUMER_VIEWS, "invalid frozen consumer view")
    _require("protection" in classification["consumer_views"], "historical data requires the protection view")
    _require(set(classification["derived_bundles"]) <= DERIVED_BUNDLES, "unknown derived historical bundle")
    bundle_rights = {item["bundle_id"]: item["rights"] for item in classification["derived_bundle_rights"]}
    _require(
        len(bundle_rights) == len(classification["derived_bundle_rights"])
        and set(bundle_rights) == set(classification["derived_bundles"]),
        "derived bundle rights must cover every bundle exactly once",
    )
    bundle_sources = {
        "historical_recognition": layers,
        "historical_alignment": packet["alignments"],
        "periodization": packet["periodizations"],
        "language_label_disambiguation": [*packet["language_labels"], *packet["language_layers"]],
        "language_change_explanation": [*packet["linguistic_features"], *packet["interpretations"]],
    }
    for bundle_id, bundle_policy in bundle_rights.items():
        _validate_rights(bundle_policy, "derived bundle")
        if packet["rights"]["reuse_scope"] != "public_training":
            _require(bundle_policy["reuse_scope"] != "public_training", "derived bundle exceeds source rights")
        referenced = {
            evidence_id
            for item in bundle_sources[bundle_id]
            for evidence_id in item["evidence_ids"]
        }
        if any(evidence_by_id[evidence_id]["rights"]["reuse_scope"] != "public_training" for evidence_id in referenced):
            _require(bundle_policy["reuse_scope"] != "public_training", "derived bundle exceeds evidence rights")
    rights = packet["rights"]
    _validate_rights(rights, "historical source")
    if rights["reuse_scope"] != "public_training":
        _require("research_only" in classification["consumer_views"], "non-public rights require research-only view")
        _require(
            not {"supervised_pair", "preference", "automatic"} & set(classification["consumer_views"]),
            "non-public historical data cannot enter learning views",
        )

    safeguards = packet["safeguards"]
    _require(safeguards["historical_forms_protected"] is True, "historical forms are not protected")
    _require(safeguards["modern_correction_eligible"] is False, "historical text entered modern correction gold")
    _require(
        safeguards["russkyi_auto_mapped_to_modern_russian"] is False,
        "historical руський cannot be auto-mapped to modern Russian",
    )
    _require(
        safeguards["old_east_slavic_is_modern_russian"] is False,
        "Old East Slavic cannot be equated with modern Russian",
    )
    _require(safeguards["scalar_language_age_claim_allowed"] is False, "unsupported scalar age claim is enabled")
    return packet


__all__ = [
    "SCHEMA_PATH", "SCHEMA_VERSION", "HistoricalRepresentationError",
    "build_historical_representation", "build_packet", "canonical_json", "validate_historical_representation",
]
