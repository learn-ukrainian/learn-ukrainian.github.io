#!/usr/bin/env python3
"""UA-GEC v3 representation adapter for exact whitespace-projected evidence.

The shared representation implementation is byte-pinned by the historical
materialization gate.  UA-GEC sentence documents contain a small, verified
class of cases where the annotated stream and exact sentence-file retrieval
differ only in Unicode whitespace.  This adapter preserves the shared
invariants and adds a narrow validator for that explicitly located evidence
mode without changing the pinned implementation.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from scripts.projects.open_model_data import phase3_linguistic_representation as base

SCHEMA_PATH = base.SCHEMA_PATH
SCHEMA_VERSION = base.SCHEMA_VERSION

apply_edits = base.apply_edits
canonical_json = base.canonical_json
sha256_bytes = base.sha256_bytes
sha256_text = base.sha256_text
sha256_value = base.sha256_value
tokenize = base.tokenize


class UaGecLinguisticRepresentationError(base.LinguisticRepresentationError):
    """UA-GEC projected evidence is not compatible with the shared v3 contract."""


def _non_whitespace_text(value: str) -> str:
    return "".join(character for character in value if not character.isspace())


def _shared_validation_copy(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Substitute only verified whitespace projections for shared validation."""
    projected = copy.deepcopy(dict(packet))
    corrected = projected["corrected"]["complete_text"]
    for item in projected["evidence"]["corroborating_corpus_evidence"]:
        locator = item["locator"]
        if locator.get("context_alignment") != "unicode_whitespace_projection":
            continue
        if item["retrieved_text_sha256"] != sha256_text(item["retrieved_text"]):
            raise UaGecLinguisticRepresentationError("projected retrieval hash is stale")
        projected_hash = sha256_text(_non_whitespace_text(corrected))
        if locator.get("corrected_context_non_whitespace_sha256") != projected_hash:
            raise UaGecLinguisticRepresentationError("projected corrected-context hash is stale")
        if _non_whitespace_text(item["retrieved_text"]) != _non_whitespace_text(corrected):
            raise UaGecLinguisticRepresentationError("projected retrieval changes a non-whitespace code point")
        item["retrieved_text"] = corrected
        item["retrieved_text_sha256"] = sha256_text(corrected)
    return projected


def validate_representation(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate shared v3 invariants plus exact UA-GEC whitespace projection."""
    packet = copy.deepcopy(dict(value))
    base.validate_representation(_shared_validation_copy(packet))
    return packet


def build_representation(**kwargs: Any) -> dict[str, Any]:
    """Build through the pinned implementation, then restore exact retrievals."""
    original_corroborating = copy.deepcopy(list(kwargs["corroborating_corpus_evidence"]))
    corrected = apply_edits(kwargs["source_text"], kwargs["edits"])
    shared_corroborating = copy.deepcopy(original_corroborating)
    for item in shared_corroborating:
        if item["locator"].get("context_alignment") == "unicode_whitespace_projection":
            item["retrieved_text"] = corrected
            item["retrieved_text_sha256"] = sha256_text(corrected)
    shared_kwargs = dict(kwargs)
    shared_kwargs["corroborating_corpus_evidence"] = shared_corroborating
    packet = base.build_representation(**shared_kwargs)
    packet["evidence"]["corroborating_corpus_evidence"] = original_corroborating
    return validate_representation(packet)
