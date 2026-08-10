#!/usr/bin/env python3
"""Deterministic complete-context representation for public Phase 3 data.

The module represents already-authorized corrections.  It does not decide
whether a correction is linguistically valid or whether a source is admitted.
"""

from __future__ import annotations

import copy
import hashlib
import json
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_linguistic_representation_v3.schema.json"
SCHEMA_VERSION = "phase3_linguistic_representation_v3"

# Copied verbatim from the immutable v2 source-production contract.
PRIMARY_ROLE_IDS = frozenset(
    {
        "explicit_rule",
        "correct_example",
        "incorrect_example",
        "corrected_example",
        "editing_exercise",
        "answer_key",
        "distractor",
        "quotation",
        "historical_or_literary_excerpt",
        "metalinguistic_mention",
        "ordinary_narration",
        "ambiguous_or_ocr",
    }
)
EDIT_SHAPES = frozenset({"substitution", "insertion", "deletion", "reordering", "punctuation_only", "multi_edit"})
CLAIM_TYPES = frozenset(
    {
        "prescriptive_rule",
        "human_correction_pair",
        "style_preference",
        "acceptable_variant",
        "historical_advice",
        "attestation_only",
        "unresolved",
    }
)
CONSUMER_VIEWS = frozenset(
    {"supervised_pair", "preference", "protection", "filtering", "review", "automatic", "research_only"}
)


class LinguisticRepresentationError(ValueError):
    """The representation is structurally or cryptographically inconsistent."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_value(value: Any) -> str:
    return sha256_text(canonical_json(value))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LinguisticRepresentationError(message)


def _word_character(text: str, index: int) -> bool:
    """Return whether a code point belongs to a lexical token at *index*."""
    char = text[index]
    category = unicodedata.category(char)
    if category[0] in {"L", "N", "M"} or char == "_":
        return True
    if char in "'’ʼ-‐‑":
        return (
            0 < index < len(text) - 1
            and _word_character(text, index - 1)
            and (unicodedata.category(text[index + 1])[0] in {"L", "N", "M"} or text[index + 1] == "_")
        )
    return False


def _contains_lexical_character(text: str) -> bool:
    return any(unicodedata.category(char)[0] in {"L", "N", "M"} or char == "_" for char in text)


def tokenize(
    text: str,
    *,
    offset: int = 0,
    paragraph_span: Mapping[str, int] | None = None,
    sentence_span: Mapping[str, int] | None = None,
) -> list[dict[str, Any]]:
    """Tokenize deterministically using Unicode code-point offsets.

    Whitespace is not a token. Letters, marks, numbers, and internal
    apostrophes/hyphens form words; every other non-space code point is emitted
    as a punctuation token. Model subwords are deliberately not represented.
    """
    tokens: list[dict[str, Any]] = []
    index = 0
    while index < len(text):
        if text[index].isspace():
            index += 1
            continue
        start = index
        if _word_character(text, index):
            index += 1
            while index < len(text) and _word_character(text, index):
                index += 1
            kind = "word"
        else:
            index += 1
            kind = "punctuation"
        absolute_start = offset + start
        absolute_end = offset + index
        in_paragraph = paragraph_span is None or (
            paragraph_span["start"] <= absolute_start and absolute_end <= paragraph_span["end"]
        )
        in_sentence = sentence_span is None or (
            sentence_span["start"] <= absolute_start and absolute_end <= sentence_span["end"]
        )
        tokens.append(
            {
                "token_id": f"tok:{len(tokens) + 1:06d}",
                "kind": kind,
                "text": text[start:index],
                "normalized_text": unicodedata.normalize("NFC", text[start:index]),
                "start": absolute_start,
                "end": absolute_end,
                "paragraph_index": 0 if in_paragraph else None,
                "sentence_index": 0 if in_sentence else None,
            }
        )
    return tokens


def apply_edits(source_text: str, edits: Sequence[Mapping[str, Any]]) -> str:
    """Apply non-overlapping source-coordinate edits deterministically."""
    previous_end = -1
    for edit in edits:
        start, end = edit["start"], edit["end"]
        require(isinstance(start, int) and isinstance(end, int), "edit offsets must be integers")
        require(0 <= start <= end <= len(source_text), "edit offsets are outside complete source text")
        require(start >= previous_end, "edits overlap or are not in deterministic source order")
        previous_end = end
    corrected = source_text
    for edit in reversed(edits):
        corrected = corrected[: edit["start"]] + edit["replacement"] + corrected[edit["end"] :]
    return corrected


def _operation(start: int, end: int, replacement: str) -> str:
    if start == end:
        require(replacement, "insertion must have a non-empty replacement")
        return "insertion"
    if not replacement:
        return "deletion"
    return "substitution"


def _normalize_edits(source_text: str, edits: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw in edits:
        edit = dict(raw)
        require(set(edit) == {"start", "end", "replacement"}, "edit fields must be exact")
        start, end, replacement = edit["start"], edit["end"], edit["replacement"]
        require(isinstance(start, int) and isinstance(end, int), "edit offsets must be integers")
        require(isinstance(replacement, str), "edit replacement must be text")
        require(0 <= start <= end <= len(source_text), "edit offsets are outside complete source text")
        normalized.append(
            {
                "start": start,
                "end": end,
                "source_text": source_text[start:end],
                "replacement": replacement,
                "operation": _operation(start, end, replacement),
            }
        )
    require(normalized, "at least one correction edit is required")
    normalized.sort(key=lambda item: (item["start"], item["end"]))
    apply_edits(source_text, normalized)
    delta = 0
    for edit in normalized:
        target_start = edit["start"] + delta
        target_end = target_start + len(edit["replacement"])
        edit.update(
            {
                "target_start": target_start,
                "target_end": target_end,
                "target_text": edit["replacement"],
            }
        )
        delta += len(edit["replacement"]) - (edit["end"] - edit["start"])
    return normalized


def _shape_tokens(text: str) -> list[str]:
    return [item["normalized_text"].casefold() for item in tokenize(text)]


def _validate_edit_shape(edit_shape: str, edits: Sequence[Mapping[str, Any]]) -> None:
    require(edit_shape in EDIT_SHAPES, "invalid edit shape")
    operations = [item["operation"] for item in edits]
    if edit_shape in {"substitution", "insertion", "deletion"}:
        require(len(edits) == 1 and operations == [edit_shape], f"{edit_shape} shape requires one matching edit")
    elif edit_shape == "reordering":
        require(len(edits) == 1 and operations == ["substitution"], "reordering requires one contiguous substitution")
        source_tokens = _shape_tokens(edits[0]["source_text"])
        target_tokens = _shape_tokens(edits[0]["replacement"])
        require(
            len(source_tokens) >= 2
            and source_tokens != target_tokens
            and Counter(source_tokens) == Counter(target_tokens),
            "reordering must preserve a multi-token multiset while changing order",
        )
    elif edit_shape == "punctuation_only":
        require(
            all(not _contains_lexical_character(item["source_text"] + item["replacement"]) for item in edits),
            "punctuation-only edit contains a lexical character",
        )
    elif edit_shape == "multi_edit":
        require(len(edits) >= 2, "multi-edit shape requires at least two edits")


def _span(source_text: str, span: Mapping[str, Any], label: str) -> dict[str, Any]:
    require(set(span) == {"start", "end"}, f"{label} fields must be exact")
    start, end = span["start"], span["end"]
    require(isinstance(start, int) and isinstance(end, int), f"{label} offsets must be integers")
    require(0 <= start <= end <= len(source_text), f"{label} offsets are outside complete source text")
    return {"start": start, "end": end, "text": source_text[start:end]}


def _schema_validator() -> Draft202012Validator:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LinguisticRepresentationError(f"cannot read representation schema: {SCHEMA_PATH}") from exc
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _validate_schema(value: Mapping[str, Any]) -> None:
    errors = sorted(_schema_validator().iter_errors(value), key=lambda item: list(item.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "packet"
        raise LinguisticRepresentationError(f"schema violation at {location}: {errors[0].message}")


def build_representation(
    *,
    document_or_edition_identity: str,
    frozen_locator: Mapping[str, Any],
    source_document_bytes_sha256: str,
    source_text: str,
    paragraph_span: Mapping[str, int],
    sentence_span: Mapping[str, int],
    edit_shape: str,
    edits: Sequence[Mapping[str, Any]],
    minimal_edit_spans: Sequence[Mapping[str, int]],
    construction_spans: Sequence[Mapping[str, int]],
    unchanged_function_word_token_ids: Iterable[str],
    primary_role_id: str,
    correction_evidence: Sequence[Mapping[str, Any]],
    corroborating_corpus_evidence: Sequence[Mapping[str, Any]],
    rights: Mapping[str, str],
    claim_type: str = "human_correction_pair",
    secondary_attributes: Sequence[str] = (),
    scope: str = "source-derived complete-context correction",
    exceptions: Sequence[str] = (),
    register: str = "unspecified",
    period: str = "unspecified",
    genre: str = "unspecified",
    evidence_grade: str = "qualified_human_with_corroboration",
    consumer_views: Sequence[str] = ("supervised_pair",),
    linguistic_analyses: Sequence[Mapping[str, Any]] = (),
    analysis_provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build and validate a complete-context, hash-bound public packet."""
    require(document_or_edition_identity, "document or edition identity is required")
    require(isinstance(source_text, str) and source_text, "complete source text is required")
    require(isinstance(frozen_locator, Mapping) and frozen_locator, "immutable locator is required")
    require(len(source_document_bytes_sha256) == 64, "source document bytes hash is required")
    require(primary_role_id in PRIMARY_ROLE_IDS, "primary role id is not a frozen v2 role")
    require(claim_type in CLAIM_TYPES, "claim type is not a frozen v2 claim type")
    require(set(consumer_views) <= CONSUMER_VIEWS, "consumer view is not recognized")
    require(rights.get("status") and rights.get("license"), "rights status and license are required")

    normalized_edits = _normalize_edits(source_text, edits)
    _validate_edit_shape(edit_shape, normalized_edits)
    corrected = apply_edits(source_text, normalized_edits)
    require(corrected != source_text, "correction edits must change complete source text")
    paragraph = _span(source_text, paragraph_span, "paragraph")
    sentence = _span(source_text, sentence_span, "sentence")
    require(
        paragraph["start"] == 0 and paragraph["end"] == len(source_text), "complete source must be a full paragraph"
    )
    require(
        paragraph["start"] <= sentence["start"] <= sentence["end"] <= paragraph["end"],
        "sentence must be in paragraph context",
    )
    minimal = [_span(source_text, item, "minimal edit span") for item in minimal_edit_spans]
    constructions = [_span(source_text, item, "construction span") for item in construction_spans]
    require(minimal, "minimal edit spans are required")
    require(constructions, "construction spans are required")
    require(
        [(item["start"], item["end"], item["text"]) for item in minimal]
        == [(item["start"], item["end"], item["source_text"]) for item in normalized_edits],
        "minimal edit spans must correspond exactly to source edits",
    )
    for minimal_span in minimal:
        require(
            any(
                construction["start"] <= minimal_span["start"]
                and minimal_span["end"] <= construction["end"]
                and (construction["start"], construction["end"]) != (minimal_span["start"], minimal_span["end"])
                for construction in constructions
            ),
            "each minimal edit must have a strictly larger construction span",
        )

    tokens = tokenize(source_text, paragraph_span=paragraph, sentence_span=sentence)
    packet: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "document": {
            "document_or_edition_identity": document_or_edition_identity,
            "frozen_locator": dict(frozen_locator),
            "frozen_locator_sha256": sha256_value(frozen_locator),
            "source_document_bytes_sha256": source_document_bytes_sha256,
        },
        "source": {
            "complete_text": source_text,
            "complete_text_utf8_sha256": sha256_bytes(source_text.encode("utf-8")),
            "source_text_sha256": sha256_text(source_text),
            "offset_basis": "unicode_code_points",
            "original_preserved": True,
            "normalization": {
                "nfc": unicodedata.normalize("NFC", source_text),
                "nfkc": unicodedata.normalize("NFKC", source_text),
                "nfc_sha256": sha256_text(unicodedata.normalize("NFC", source_text)),
                "nfkc_sha256": sha256_text(unicodedata.normalize("NFKC", source_text)),
                "source_is_nfc": source_text == unicodedata.normalize("NFC", source_text),
                "source_is_nfkc": source_text == unicodedata.normalize("NFKC", source_text),
            },
        },
        "context": {
            "paragraphs": [paragraph],
            "sentences": [sentence],
            "focal_paragraph_index": 0,
            "focal_sentence_index": 0,
        },
        "tokens": tokens,
        "edit_shape": edit_shape,
        "edits": normalized_edits,
        "minimal_edit_spans": minimal,
        "construction_spans": constructions,
        "unchanged_function_word_token_ids": list(unchanged_function_word_token_ids),
        "corrected": {"complete_text": corrected, "complete_text_sha256": sha256_text(corrected)},
        "evidence": {
            "correction_evidence": [dict(item) for item in correction_evidence],
            "corroborating_corpus_evidence": [dict(item) for item in corroborating_corpus_evidence],
        },
        "classification": {
            "primary_role_id": primary_role_id,
            "secondary_attributes": list(secondary_attributes),
            "claim_type": claim_type,
            "scope": scope,
            "exceptions": list(exceptions),
            "register": register,
            "period": period,
            "genre": genre,
            "rights": dict(rights),
            "evidence_grade": evidence_grade,
            "consumer_views": list(consumer_views),
        },
        "linguistic_analyses": [dict(item) for item in linguistic_analyses],
        "analysis_provenance": dict(analysis_provenance or {"status": "absent"}),
        "model_subword_diagnostics": {"status": "absent"},
        "provider_calls": False,
    }
    validate_representation(packet)
    return packet


build_packet = build_representation


def validate_representation(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate schema plus hash, offset, provenance, and round-trip invariants."""
    packet = copy.deepcopy(dict(value))
    _validate_schema(packet)
    require(packet["provider_calls"] is False, "provider calls are forbidden")
    source = packet["source"]
    text = source["complete_text"]
    require(text, "fragment-only packet: complete source text is required")
    require(source["complete_text_utf8_sha256"] == sha256_bytes(text.encode("utf-8")), "stale source UTF-8 bytes hash")
    require(source["source_text_sha256"] == sha256_text(text), "stale source text hash")
    locator = packet["document"]["frozen_locator"]
    require(packet["document"]["frozen_locator_sha256"] == sha256_value(locator), "stale frozen locator hash")
    facts = source["normalization"]
    nfc, nfkc = unicodedata.normalize("NFC", text), unicodedata.normalize("NFKC", text)
    require(facts["nfc"] == nfc and facts["nfc_sha256"] == sha256_text(nfc), "stale NFC normalization fact")
    require(facts["nfkc"] == nfkc and facts["nfkc_sha256"] == sha256_text(nfkc), "stale NFKC normalization fact")
    require(facts["source_is_nfc"] == (text == nfc), "stale NFC identity fact")
    require(facts["source_is_nfkc"] == (text == nfkc), "stale NFKC identity fact")

    paragraph = packet["context"]["paragraphs"][0]
    sentence = packet["context"]["sentences"][0]
    require(paragraph["start"] == 0 and paragraph["end"] == len(text), "fragment-only paragraph context")
    for label, span in (("paragraph", paragraph), ("sentence", sentence)):
        require(text[span["start"] : span["end"]] == span["text"], f"stale {label} context offsets")
    require(
        paragraph["start"] <= sentence["start"] <= sentence["end"] <= paragraph["end"],
        "sentence is not contained by paragraph",
    )

    expected_edits = _normalize_edits(
        text,
        [{"start": item["start"], "end": item["end"], "replacement": item["replacement"]} for item in packet["edits"]],
    )
    require(packet["edits"] == expected_edits, "edit source or target offsets are stale")
    _validate_edit_shape(packet["edit_shape"], packet["edits"])
    minimal = packet["minimal_edit_spans"]
    constructions = packet["construction_spans"]
    require(
        [(item["start"], item["end"], item["text"]) for item in minimal]
        == [(item["start"], item["end"], item["source_text"]) for item in packet["edits"]],
        "minimal edit spans do not correspond to source edits",
    )
    for label, spans in (("minimal edit", minimal), ("construction", constructions)):
        for span in spans:
            require(text[span["start"] : span["end"]] == span["text"], f"stale {label} offsets")
    for minimal_span in minimal:
        require(
            any(
                construction["start"] <= minimal_span["start"]
                and minimal_span["end"] <= construction["end"]
                and (construction["start"], construction["end"]) != (minimal_span["start"], minimal_span["end"])
                for construction in constructions
            ),
            "minimal and construction spans are not distinct",
        )

    expected_tokens = tokenize(text, paragraph_span=paragraph, sentence_span=sentence)
    require(packet["tokens"] == expected_tokens, "tokens are stale or do not round-trip source offsets")
    token_by_id = {token["token_id"]: token for token in expected_tokens}
    selected = packet["unchanged_function_word_token_ids"]
    require(
        len(selected) == len(set(selected)) and set(selected) <= set(token_by_id),
        "unknown or duplicate unchanged function-word token id",
    )
    edit_ranges = [(edit["start"], edit["end"]) for edit in packet["edits"]]
    for token_id in selected:
        token = token_by_id[token_id]
        require(token["kind"] == "word", "unchanged function-word selection is not a word token")
        require(
            any(span["start"] <= token["start"] and token["end"] <= span["end"] for span in constructions),
            "unchanged function-word token is outside every construction span",
        )
        require(
            all(token["end"] <= start or token["start"] >= end for start, end in edit_ranges),
            "function-word token was changed",
        )

    corrected = apply_edits(text, packet["edits"])
    require(corrected == packet["corrected"]["complete_text"], "edits do not round-trip to corrected full context")
    require(corrected != text, "correction edits must change complete source text")
    require(packet["corrected"]["complete_text_sha256"] == sha256_text(corrected), "stale corrected context hash")

    classification = packet["classification"]
    require(classification["primary_role_id"] in PRIMARY_ROLE_IDS, "invalid frozen primary role id")
    require(classification["claim_type"] in CLAIM_TYPES, "invalid frozen claim type")
    require(set(classification["consumer_views"]) <= CONSUMER_VIEWS, "invalid consumer view")
    correction_evidence = packet["evidence"]["correction_evidence"]
    require(correction_evidence, "missing qualified-human correction evidence")
    require(
        all(item["authority"] != "model_output" for item in correction_evidence),
        "model output cannot be correction authority",
    )
    require(
        any(item["qualified_human"] is True and item["authority"] == "qualified_human" for item in correction_evidence),
        "missing qualified-human correction evidence",
    )
    for item in correction_evidence:
        require(item["locator_sha256"] == sha256_value(item["locator"]), "stale evidence locator hash")
        require(
            item["source_document_bytes_sha256"] == packet["document"]["source_document_bytes_sha256"],
            "correction evidence does not bind source document bytes",
        )
        require(
            item["evidence_text_sha256"] == sha256_text(item["evidence_text"]), "stale correction evidence text hash"
        )
        require(item["source_context_sha256"] == sha256_text(text), "correction evidence does not bind source context")
        require(
            item["corrected_context_sha256"] == sha256_text(corrected),
            "correction evidence does not bind corrected context",
        )
    corroborating = packet["evidence"]["corroborating_corpus_evidence"]
    require(corroborating, "missing corroborating corpus evidence")
    correction_locator_hashes = {item["locator_sha256"] for item in correction_evidence}
    for item in corroborating:
        require(item["locator_sha256"] == sha256_value(item["locator"]), "stale corroborating locator hash")
        require(
            item["locator_sha256"] not in correction_locator_hashes,
            "corroborating evidence must use a distinct corpus locator",
        )
        require(
            item["source_document_bytes_sha256"] != packet["document"]["source_document_bytes_sha256"],
            "corroborating evidence must bind a distinct source document",
        )
        require(
            item["retrieved_text_sha256"] == sha256_text(item["retrieved_text"]), "corroborating retrieval is not exact"
        )
        normalized_retrieval = unicodedata.normalize("NFC", item["retrieved_text"]).casefold()
        normalized_correction = unicodedata.normalize("NFC", corrected).casefold()
        require(
            normalized_retrieval in normalized_correction or normalized_correction in normalized_retrieval,
            "corroborating retrieval does not support corrected context",
        )

    analyses = packet["linguistic_analyses"]
    provenance = packet["analysis_provenance"]
    require(
        (not analyses and provenance["status"] == "absent") or (analyses and provenance["status"] == "present"),
        "analysis provenance status disagrees with analyses",
    )
    for analysis in analyses:
        require(analysis["token_id"] in token_by_id, "analysis refers to an unknown token")
        require("ambiguity" in analysis, "linguistic analysis must state ambiguity explicitly")
    return packet
