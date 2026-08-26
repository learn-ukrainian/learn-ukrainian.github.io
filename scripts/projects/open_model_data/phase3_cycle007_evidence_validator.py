#!/usr/bin/env python3
"""Validate Cycle 007 evidence sidecars and candidate label evidence references.

Two layers:

1. ``validate_sidecar`` / ``validate_row_evidence`` re-derive every evidence
   ID from its own identity payload and re-check the closed channel/supports
   claim boundary, so a hand-edited or drifted sidecar fails closed even if
   it was never produced by the compiler.
2. ``validate_label_evidence_refs`` is the fail-closed gate a later labeling
   stage must call before accepting any model decision: it rejects
   cross-row, cross-phenomenon, invented, duplicate, and out-of-order IDs,
   and it refuses an ``agree``/``positive``/``acceptable_control``/
   ``protected`` decision unless the referenced evidence is actually
   sufficient (normative or attestation grade, per
   ``phase3_cycle007_evidence_contract.SUFFICIENT_SUPPORTS``).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

# Decisions that require sufficient normative/attestation evidence (amendment
# model-contract section). Clean-label rejections and residual abstention or
# disagreement are the closed fail-closed uncertainty paths and never need
# sufficiency. Keep the clean-label set aligned with the frozen public label
# semantics; otherwise a schema-valid provider response can fail later as an
# unknown decision.
SUFFICIENT_REQUIRED_DECISIONS = frozenset({"agree", "positive", "acceptable_control", "protected"})
CLEAN_REJECTION_DECISIONS = frozenset(
    {
        "reject_fragment_or_too_short",
        "reject_exercise_or_task_prompt",
        "reject_error_or_contrast_example",
        "reject_table_list_formula_code",
        "reject_metalinguistic_or_grammar_talk",
        "reject_quoted_literary_or_anthology",
        "reject_archaic_historical_language",
        "reject_dialectal_regional_surzhyk",
        "reject_foreign_or_translation_artifact",
        "reject_learner_or_simplified_broken",
        "reject_parallel_norm_or_pre2026_only",
        "reject_mixed_or_uncertain",
        "reject_insufficient_locator_evidence",
    }
)
UNCERTAINTY_DECISIONS = CLEAN_REJECTION_DECISIONS | {"abstention", "disagreement"}
KNOWN_DECISIONS = SUFFICIENT_REQUIRED_DECISIONS | UNCERTAINTY_DECISIONS

# Channels whose absence/ambiguity actually drives a sufficiency classification.
_DECISIVE_CHANNELS = frozenset({"vesum_attestation", "heritage_attestation", "pravopys_2026_normative"})

_SHA256_RE = re.compile(r"[a-f0-9]{64}\Z")
_EVIDENCE_ID_RE = re.compile(r"cycle007_evidence:[a-f0-9]{64}\Z")
_SIDECAR_ID_RE = re.compile(r"cycle007_sidecar:[a-f0-9]{64}\Z")
_PACKET_BASENAME_RE = re.compile(r"packet-[0-9]{4}\.json\Z")
_SOURCE_EVALUATION_CYCLE_ID = "phase3-v2-1-evaluation-cycle-005"

_EVIDENCE_RECORD_FIELDS = frozenset(
    {
        "schema_version", "evidence_id", "channel", "source_identity", "source_version", "locator", "query",
        "query_sha256", "status", "supports", "retrieval_sha256", "parser_id", "parser_version", "row_identity",
        "phenomenon_id", "negative_reason", "raw_payload_publication_allowed", "claim_boundary",
    }
)
_ROW_EVIDENCE_FIELDS = frozenset(
    {
        "unit_id", "unit_sha256", "tokenizer_id", "tokenizer_version", "extracted_forms", "evidence",
        "evidence_ids", "phenomenon_evidence_ids", "sufficient_support", "archaic_only_risk",
        "russian_shadow_suspected",
    }
)
_CODE_HASH_FIELDS = frozenset(
    {
        "compiler_id", "compiler_sha256", "tokenizer_id", "tokenizer_version", "tokenizer_sha256",
        "compound_parser_id", "compound_parser_version", "compound_parser_sha256", "mcp_response_parser_id",
        "mcp_response_parser_version", "mcp_response_parser_sha256", "query_plan_id", "query_plan_version",
        "query_plan_sha256",
    }
)
_CODE_HASH_DIGEST_FIELDS = frozenset(
    {
        "compiler_sha256", "tokenizer_sha256", "compound_parser_sha256", "mcp_response_parser_sha256",
        "query_plan_sha256",
    }
)


class EvidenceValidationError(ValueError):
    """A Cycle 007 evidence sidecar or label evidence reference fails closed."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise EvidenceValidationError(code, message)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_code_hashes(code_hashes: Any, *, code: str) -> None:
    if not isinstance(code_hashes, Mapping) or set(code_hashes) != _CODE_HASH_FIELDS:
        _fail(code, "code_hashes has an unexpected shape")
    for field, value in code_hashes.items():
        if field in _CODE_HASH_DIGEST_FIELDS:
            if not _is_sha256(value):
                _fail(code, f"code_hashes.{field} must be a hex sha256")
        elif not _is_nonempty_string(value):
            _fail(code, f"code_hashes.{field} must be a non-empty string")


def validate_evidence_record(record: Mapping[str, Any]) -> None:
    """Re-derive the evidence ID and re-check the closed claim boundary."""
    if not isinstance(record, Mapping) or set(record) != _EVIDENCE_RECORD_FIELDS:
        _fail("evidence_shape_drift", "evidence record has an unexpected shape")
    if record["schema_version"] != contract.EVIDENCE_SCHEMA_VERSION:
        _fail("evidence_shape_drift", "unexpected evidence schema_version")
    if not _EVIDENCE_ID_RE.fullmatch(str(record["evidence_id"])):
        _fail("evidence_shape_drift", "evidence_id must be a cycle007 hex identity")
    for field in ("source_identity", "source_version", "locator", "parser_id", "parser_version"):
        if not _is_nonempty_string(record[field]):
            _fail("evidence_shape_drift", f"evidence record {field} must be a non-empty string")
    if record["query"] is not None and not isinstance(record["query"], str):
        _fail("evidence_shape_drift", "evidence record query must be a string or null")
    if not _is_sha256(record["query_sha256"]) or not _is_sha256(record["retrieval_sha256"]):
        _fail("evidence_shape_drift", "evidence record query/retrieval hashes must be hex sha256 values")
    if record["channel"] not in contract.CHANNELS or record["status"] not in contract.STATUSES or record["supports"] not in contract.SUPPORTS:
        _fail("evidence_shape_drift", "evidence record has an unknown channel, status, or supports value")
    row_identity = record["row_identity"]
    if (
        not isinstance(row_identity, Mapping)
        or set(row_identity) != {"unit_id", "unit_sha256"}
        or not _is_nonempty_string(row_identity.get("unit_id"))
        or not _is_sha256(row_identity.get("unit_sha256"))
    ):
        _fail("evidence_shape_drift", "evidence record row_identity has an unexpected shape")
    if record["phenomenon_id"] is not None and (
        not _is_nonempty_string(record["phenomenon_id"])
        or record["phenomenon_id"] not in contract.RESIDUAL_PHENOMENON_TAXONOMY
    ):
        _fail("evidence_shape_drift", "evidence record phenomenon_id is invalid")
    if record["negative_reason"] is not None and not isinstance(record["negative_reason"], str):
        _fail("evidence_shape_drift", "evidence record negative_reason must be a string or null")
    try:
        identity = contract.evidence_identity(
            channel=record["channel"],
            source_identity=record["source_identity"],
            source_version=record["source_version"],
            locator=record["locator"],
            query_sha256=record["query_sha256"],
            status=record["status"],
            supports=record["supports"],
            retrieval_sha256=record["retrieval_sha256"],
            parser_id=record["parser_id"],
            parser_version=record["parser_version"],
            row=record["row_identity"],
            phenomenon_id=record["phenomenon_id"],
        )
    except contract.EvidenceContractError as exc:
        _fail("source_role_boundary_violation", str(exc))
        return
    recomputed = contract.evidence_id(identity)
    if recomputed != record["evidence_id"]:
        _fail("evidence_id_hash_drift", f"evidence_id does not match its own identity payload: {record['evidence_id']}")
    # Amendment (fixes v3, item 5): require the private ``query`` field and
    # recompute ``query_sha256`` from it (or, when there is no query, from
    # the fixed no-query domain-separated hash) — a caller-supplied
    # ``query_sha256`` alone is never trusted, so mutating or deleting
    # ``query`` while leaving ``query_sha256``/``evidence_id`` untouched
    # fails closed.
    expected_query_sha256 = contract.expected_query_sha256(
        record["query"],
        channel=record["channel"],
        source_identity=record["source_identity"],
        locator=record["locator"],
    )
    if expected_query_sha256 != record["query_sha256"]:
        _fail("query_sha256_hash_drift", "query_sha256 does not match a recompute from the private query field")
    if record["status"] == "attested" and record.get("negative_reason") is not None:
        _fail("evidence_shape_drift", "attested evidence cannot carry a negative_reason")
    if record["status"] != "attested" and record["supports"] != "no_conclusion":
        _fail("source_role_boundary_violation", "non-attested evidence must carry supports=no_conclusion")
    # Amendment step 12: raw_payload_publication_allowed=false and the
    # non-authoritative claim-boundary flags are frozen constants, never
    # hand-editable to a truthy value.
    if record.get("raw_payload_publication_allowed") is not False:
        _fail("evidence_shape_drift", "raw_payload_publication_allowed must be false")
    claim_boundary = record["claim_boundary"]
    if not isinstance(claim_boundary, Mapping) or set(claim_boundary) != {
        "authoritative", "human_gold", "model_vote_authoritative", "vesum_absence_only_authoritative"
    } or any(value is not False for value in claim_boundary.values()):
        _fail("evidence_shape_drift", "claim_boundary must be the frozen all-false non-authoritative flag set")


def validate_row_evidence(row_evidence: Mapping[str, Any]) -> None:
    """Validate one row's compiled evidence set: unique IDs, correct scoping, closed boundaries."""
    if not isinstance(row_evidence, Mapping) or set(row_evidence) != _ROW_EVIDENCE_FIELDS:
        _fail("row_shape_drift", "row evidence has an unexpected shape")
    unit_id = row_evidence.get("unit_id")
    unit_sha256 = row_evidence.get("unit_sha256")
    if not (_is_nonempty_string(unit_id) and _is_sha256(unit_sha256)):
        _fail("row_identity_drift", "row evidence missing/malformed unit_id or unit_sha256")
    if not _is_nonempty_string(row_evidence["tokenizer_id"]) or not _is_nonempty_string(row_evidence["tokenizer_version"]):
        _fail("row_shape_drift", "row tokenizer identity must be non-empty strings")
    if not isinstance(row_evidence["extracted_forms"], list) or not all(isinstance(form, str) for form in row_evidence["extracted_forms"]):
        _fail("row_shape_drift", "row extracted_forms must be a string array")
    if not isinstance(row_evidence["evidence"], list) or not row_evidence["evidence"]:
        _fail("row_shape_drift", "row evidence must be a non-empty array")
    for field in ("sufficient_support", "archaic_only_risk", "russian_shadow_suspected"):
        if not isinstance(row_evidence[field], bool):
            _fail("row_shape_drift", f"row {field} must be a boolean")

    evidence: Sequence[Mapping[str, Any]] = row_evidence["evidence"]
    seen_ids: set[str] = set()
    for record in evidence:
        validate_evidence_record(record)
        row_identity = record["row_identity"]
        if row_identity.get("unit_id") != unit_id or row_identity.get("unit_sha256") != unit_sha256:
            _fail("cross_row_evidence", f"evidence {record['evidence_id']} bound to a different row")
        evidence_id = str(record["evidence_id"])
        if evidence_id in seen_ids:
            _fail("duplicate_evidence_id", f"duplicate evidence id within one row: {evidence_id}")
        seen_ids.add(evidence_id)

    if not isinstance(row_evidence["evidence_ids"], list) or not all(_EVIDENCE_ID_RE.fullmatch(value) for value in row_evidence["evidence_ids"] if isinstance(value, str)) or not all(isinstance(value, str) for value in row_evidence["evidence_ids"]):
        _fail("row_shape_drift", "row evidence_ids must be cycle007 evidence identities")
    declared_ids = list(row_evidence["evidence_ids"])
    if declared_ids != sorted(set(declared_ids)):
        _fail("evidence_id_order_drift", "row evidence_ids must be sorted and unique")
    if set(declared_ids) != seen_ids:
        _fail("evidence_id_set_drift", "declared evidence_ids does not match the compiled evidence records")

    phenomenon_ids = row_evidence["phenomenon_evidence_ids"]
    if not isinstance(phenomenon_ids, Mapping) or any(
        not _is_nonempty_string(phenomenon_id) or not isinstance(ids, list) or not all(isinstance(value, str) and _EVIDENCE_ID_RE.fullmatch(value) for value in ids)
        for phenomenon_id, ids in phenomenon_ids.items()
    ):
        _fail("row_shape_drift", "phenomenon_evidence_ids has an unexpected shape")
    for phenomenon_id, ids in phenomenon_ids.items():
        ids_list = list(ids)
        if ids_list != sorted(set(ids_list)):
            _fail("evidence_id_order_drift", f"phenomenon {phenomenon_id!r} evidence ids must be sorted and unique")
        by_id = {str(record["evidence_id"]): record for record in evidence}
        for evidence_id in ids_list:
            record = by_id.get(evidence_id)
            if record is None:
                _fail("cross_phenomenon_evidence", f"evidence {evidence_id} absent from this row")
            elif str(record.get("phenomenon_id")) != str(phenomenon_id):
                _fail("cross_phenomenon_evidence", f"evidence {evidence_id} bound to a different phenomenon")
    expected_phenomenon_evidence_ids: dict[str, list[str]] = {}
    for record in evidence:
        phenomenon_id = record["phenomenon_id"]
        if phenomenon_id is not None:
            expected_phenomenon_evidence_ids.setdefault(phenomenon_id, []).append(record["evidence_id"])
    expected_phenomenon_evidence_ids = {
        phenomenon_id: sorted(set(ids)) for phenomenon_id, ids in expected_phenomenon_evidence_ids.items()
    }
    if dict(phenomenon_ids) != expected_phenomenon_evidence_ids:
        _fail("phenomenon_evidence_set_drift", "phenomenon_evidence_ids does not exactly index phenomenon-scoped evidence")

    if row_evidence["sufficient_support"] != any(contract.is_sufficient_positive(record) for record in evidence):
        _fail("row_count_drift", "row sufficient_support does not match its evidence")
    if row_evidence["archaic_only_risk"] != contract.is_archaic_only_risk(evidence):
        _fail("row_count_drift", "row archaic_only_risk does not match its evidence")
    if row_evidence["russian_shadow_suspected"] != any(
        record["channel"] == "russian_shadow_suspicion" and record["status"] == "attested" for record in evidence
    ):
        _fail("row_count_drift", "row russian_shadow_suspected does not match its evidence")


# Amendment (fixes v3, item 5): every one of these fields is REQUIRED, not
# conditionally checked — a sidecar/manifest missing any of them fails
# closed rather than silently skipping the check that field would have
# driven.
_REQUIRED_SIDECAR_FIELDS: tuple[str, ...] = (
    "schema_version",
    "evaluation_cycle_id",
    "lane",
    "packet_binding",
    "packet_index",
    "row_count",
    "tokenizer_id",
    "tokenizer_version",
    "code_hashes",
    "server_code_sha256",
    "sources_db_sha256",
    "vesum_db_sha256",
    "network_lookups_performed",
    "rows",
    "retrieval_payloads",
    "sidecar_id",
)
_SIDECAR_FIELDS = frozenset(_REQUIRED_SIDECAR_FIELDS)
_PACKET_BINDING_FIELDS: frozenset[str] = frozenset({"canonical_basename", "raw_sha256", "packet_identity_set_sha256"})


def _validate_packet_binding(packet_binding: Any, *, code: str) -> None:
    if not isinstance(packet_binding, Mapping) or set(packet_binding) != _PACKET_BINDING_FIELDS:
        _fail(code, "packet_binding must carry exactly canonical_basename/raw_sha256/packet_identity_set_sha256")
    basename = packet_binding.get("canonical_basename")
    if not isinstance(basename, str) or _PACKET_BASENAME_RE.fullmatch(basename) is None:
        _fail(code, "packet_binding.canonical_basename must be a safe packet-NNNN.json basename")
    for field in ("raw_sha256", "packet_identity_set_sha256"):
        value = packet_binding.get(field)
        if not _is_sha256(value):
            _fail(code, f"packet_binding.{field} must be a hex sha256")
_IDENTITY_FIELDS: tuple[str, ...] = (
    "tokenizer_id",
    "tokenizer_version",
    "code_hashes",
    "server_code_sha256",
    "sources_db_sha256",
    "vesum_db_sha256",
)
_SIDECAR_LANES: frozenset[str] = frozenset({"clean_label", "residual_label"})


def _validate_row_phenomenon_scope(lane: str, row_evidence: Mapping[str, Any]) -> None:
    """Amendment (fixes v3, item 5): lane-appropriate phenomenon-map shape.

    A clean-lane row must carry no phenomenon-scoped evidence at all; a
    residual-lane row must carry exactly the frozen 23-phenomenon keys —
    never a subset, never an extra key.
    """
    if not isinstance(row_evidence, Mapping):
        return  # validate_row_evidence emits the shape error below.
    phenomenon_evidence_ids = row_evidence.get("phenomenon_evidence_ids")
    evidence = row_evidence.get("evidence")
    if not isinstance(phenomenon_evidence_ids, Mapping) or not isinstance(evidence, list) or not all(
        isinstance(record, Mapping) for record in evidence
    ):
        return  # validate_row_evidence emits the shape error below.
    phenomenon_ids = set(phenomenon_evidence_ids)
    if lane == "clean_label":
        if phenomenon_ids or any(record.get("phenomenon_id") is not None for record in evidence):
            _fail("clean_lane_phenomenon_contamination", "clean-lane row carries phenomenon-scoped evidence")
    else:
        expected = set(contract.RESIDUAL_PHENOMENON_TAXONOMY)
        if phenomenon_ids != expected:
            _fail(
                "residual_lane_phenomenon_scope_drift",
                "residual-lane row phenomenon keys do not match the frozen 23-phenomenon taxonomy: "
                f"missing={sorted(expected - phenomenon_ids)} extra={sorted(phenomenon_ids - expected)}",
            )


def validate_sidecar(sidecar: Mapping[str, Any], *, expected_identity: Mapping[str, Any]) -> None:
    """Validate every row in one packet's compiled sidecar.

    Every schema field and exact constant is required, not conditionally
    checked. ``expected_identity`` (mapping over ``_IDENTITY_FIELDS``) must
    be the caller's own independently/freshly computed current code and
    source-database identity (e.g. the compiler's own ``CODE_HASHES`` and a
    fresh ``server_identity()``) — never taken from the sidecar under test —
    so a rehashed sidecar that self-consistently substitutes arbitrary
    code/source hashes still fails closed.

    Amendment step 12: re-derives ``sidecar_id`` and checks ``row_count``
    against the actual ``rows`` list. Amendment (fixes v3, item 5):
    ``retrieval_payloads`` must be a mapping whose every value's own
    canonical SHA-256 equals its key, every evidence record's
    ``retrieval_sha256`` must resolve to an entry in it, and every entry
    must be referenced by at least one evidence record (no unreferenced
    payloads). Sidecars carry their lane; a clean-lane row must have no
    phenomenon-scoped evidence and a residual-lane row must have exactly
    the frozen 23 phenomenon keys.
    """
    if not isinstance(sidecar, Mapping) or set(sidecar) != _SIDECAR_FIELDS:
        _fail("sidecar_shape_drift", "sidecar has an unexpected shape")
    if sidecar["schema_version"] != "phase3_cycle007_evidence_sidecar_v1":
        _fail("sidecar_shape_drift", "unexpected sidecar schema_version")
    if sidecar["evaluation_cycle_id"] != "phase3-v2-1-evaluation-cycle-007":
        _fail("sidecar_shape_drift", "unexpected sidecar evaluation_cycle_id")
    if sidecar["lane"] not in _SIDECAR_LANES:
        _fail("sidecar_shape_drift", f"unknown lane: {sidecar['lane']!r}")
    _validate_packet_binding(sidecar["packet_binding"], code="packet_binding_shape_drift")
    if not isinstance(sidecar["packet_index"], int) or isinstance(sidecar["packet_index"], bool) or sidecar["packet_index"] < 1:
        _fail("sidecar_shape_drift", "sidecar packet_index must be a positive int")
    if sidecar["network_lookups_performed"] != 0:
        _fail("sidecar_shape_drift", "network_lookups_performed must be 0")
    rows = sidecar["rows"]
    if not isinstance(rows, list) or not rows:
        _fail("sidecar_shape_drift", "sidecar has no rows")
    if sidecar["row_count"] != len(rows):
        _fail("sidecar_shape_drift", "sidecar row_count does not match len(rows)")
    if not _is_nonempty_string(sidecar["tokenizer_id"]) or not _is_nonempty_string(sidecar["tokenizer_version"]):
        _fail("sidecar_shape_drift", "sidecar tokenizer identity must be non-empty strings")
    _validate_code_hashes(sidecar["code_hashes"], code="sidecar_shape_drift")
    if (
        sidecar["code_hashes"]["tokenizer_id"] != sidecar["tokenizer_id"]
        or sidecar["code_hashes"]["tokenizer_version"] != sidecar["tokenizer_version"]
    ):
        _fail("sidecar_shape_drift", "sidecar tokenizer identity disagrees with code_hashes")
    for field in ("server_code_sha256", "sources_db_sha256", "vesum_db_sha256"):
        if not _is_sha256(sidecar[field]):
            _fail("sidecar_shape_drift", f"sidecar {field} must be a hex sha256")
    if not _SIDECAR_ID_RE.fullmatch(str(sidecar["sidecar_id"])):
        _fail("sidecar_shape_drift", "sidecar_id must be a cycle007 hex identity")

    for field in _IDENTITY_FIELDS:
        if sidecar[field] != expected_identity.get(field):
            _fail("identity_hash_drift", f"sidecar {field!r} does not match the expected current identity")

    body = {key: value for key, value in sidecar.items() if key != "sidecar_id"}
    recomputed_sidecar_id = "cycle007_sidecar:" + contract.sha256_value(body)
    if recomputed_sidecar_id != sidecar["sidecar_id"]:
        _fail("sidecar_id_hash_drift", "sidecar_id does not match its own content hash")

    retrieval_payloads = sidecar["retrieval_payloads"]
    if not isinstance(retrieval_payloads, Mapping):
        _fail("retrieval_payload_table_shape_drift", "retrieval_payloads must be a mapping")
    for key, value in retrieval_payloads.items():
        if contract.sha256_value(value) != key:
            _fail("retrieval_payload_hash_drift", f"retrieval_payloads entry {key} does not hash to its own key")

    seen_units: set[tuple[str, str]] = set()
    referenced_hashes: set[str] = set()
    for row_evidence in rows:
        _validate_row_phenomenon_scope(sidecar["lane"], row_evidence)
        validate_row_evidence(row_evidence)
        if (
            row_evidence["tokenizer_id"] != sidecar["tokenizer_id"]
            or row_evidence["tokenizer_version"] != sidecar["tokenizer_version"]
        ):
            _fail("row_identity_drift", "row tokenizer identity disagrees with its sidecar")
        key = (row_evidence["unit_id"], row_evidence["unit_sha256"])
        if key in seen_units:
            _fail("duplicate_row", f"duplicate row identity within one sidecar: {key}")
        seen_units.add(key)
        for record in row_evidence.get("evidence", []):
            rsha = str(record["retrieval_sha256"])
            referenced_hashes.add(rsha)
            if rsha not in retrieval_payloads:
                _fail(
                    "retrieval_payload_missing",
                    f"evidence {record['evidence_id']} retrieval_sha256 absent from retrieval_payloads",
                )

    unreferenced = set(retrieval_payloads) - referenced_hashes
    if unreferenced:
        _fail(
            "retrieval_payload_unreferenced",
            f"retrieval_payloads has entries no evidence record references: {sorted(unreferenced)}",
        )


_REQUIRED_MANIFEST_FIELDS: tuple[str, ...] = (
    "schema_version",
    "text_free",
    "evaluation_cycle_id",
    "tokenizer_id",
    "tokenizer_version",
    "code_hashes",
    "server_code_sha256",
    "sources_db_sha256",
    "vesum_db_sha256",
    "packet_count",
    "row_count",
    "network_lookups_performed",
    "counts_by_channel",
    "counts_by_status",
    "counts_by_supports",
    "sufficient_support_rows",
    "archaic_only_risk_rows",
    "russian_shadow_suspected_rows",
    "sidecars",
    "source_package_binding",
    "mcp_transport_attestation",
    "manifest_sha256",
)
_MANIFEST_FIELDS = frozenset(_REQUIRED_MANIFEST_FIELDS)
_SIDECAR_INDEX_ENTRY_FIELDS: frozenset[str] = frozenset(
    {"packet_index", "row_count", "sidecar_sha256", "sidecar_id", "lane", "packet_binding"}
)
_SOURCE_PACKAGE_BINDING_FIELDS: frozenset[str] = frozenset(
    {
        "source_evaluation_cycle_id",
        "custody_receipt_raw_sha256",
        "materialization_manifest_sha256",
        "ordered_identity_commitment_sha256",
        "identity_union_commitment_sha256",
        "ordered_packet_commitment_sha256",
        "packet_count",
        "row_count",
    }
)
_MCP_TRANSPORT_ATTESTATION_FIELDS: frozenset[str] = frozenset(
    {
        "schema_version",
        "transport",
        "endpoint_sha256",
        "required_tool_set_sha256",
        "tool_call_count",
        "counts_by_tool",
        "server_identity_call_count",
        "ordered_call_commitment_sha256",
    }
)
_REAL_PACKET_COUNT = 204
_REAL_ROW_COUNT = 10_159
_EXPECTED_MCP_ENDPOINT_SHA256 = contract.sha256_text("http://127.0.0.1:8766/mcp")


def validate_manifest(manifest: Mapping[str, Any], *, expected_identity: Mapping[str, Any]) -> None:
    """Validate the text-free compile manifest's own content hash and shape.

    Every schema field and exact constant is required, not conditionally
    checked; see ``validate_sidecar`` for ``expected_identity``'s contract.
    Amendment step 12: re-derives ``manifest_sha256`` and requires
    ``packet_count``/``row_count`` to match the actual ``sidecars`` list.
    Amendment (fixes v3, item 4): every sidecar index entry carries its
    packet's lane/binding; ``source_package_binding`` is required to be
    *present* (the materialization custody/manifest hashes and ordered
    identity commitment when a real source package backs this compile) but
    its value may be ``None`` for a bare, package-free compile.
    """
    if not isinstance(manifest, Mapping) or set(manifest) != _MANIFEST_FIELDS:
        _fail("manifest_shape_drift", "manifest has an unexpected shape")
    if manifest["schema_version"] != "phase3_cycle007_evidence_manifest_v1":
        _fail("manifest_shape_drift", "unexpected manifest schema_version")
    if manifest["text_free"] is not True:
        _fail("manifest_shape_drift", "manifest must be text_free=true")
    if manifest["evaluation_cycle_id"] != "phase3-v2-1-evaluation-cycle-007":
        _fail("manifest_shape_drift", "unexpected manifest evaluation_cycle_id")
    if manifest["network_lookups_performed"] != 0:
        _fail("manifest_shape_drift", "network_lookups_performed must be 0")
    sidecars = manifest["sidecars"]
    if not isinstance(sidecars, list):
        _fail("manifest_shape_drift", "manifest sidecars must be an array")
    if manifest["packet_count"] != len(sidecars):
        _fail("manifest_shape_drift", "manifest packet_count does not match len(sidecars)")
    row_count = 0
    seen_sidecar_ids: set[str] = set()
    expected_packet_index = 1
    for entry in sidecars:
        if not isinstance(entry, Mapping) or set(entry) != _SIDECAR_INDEX_ENTRY_FIELDS:
            _fail("manifest_shape_drift", "sidecar index entry has an unexpected shape")
        packet_index = entry["packet_index"]
        if not isinstance(packet_index, int) or isinstance(packet_index, bool) or packet_index != expected_packet_index:
            _fail("manifest_shape_drift", "sidecar entries must have ordered, unique packet_index values starting at 1")
        expected_packet_index += 1
        if not isinstance(entry["row_count"], int) or isinstance(entry["row_count"], bool) or entry["row_count"] < 1:
            _fail("manifest_shape_drift", "sidecar index entry row_count must be a positive integer")
        if not _is_sha256(entry["sidecar_sha256"]) or not _SIDECAR_ID_RE.fullmatch(str(entry["sidecar_id"])):
            _fail("manifest_shape_drift", "sidecar index entry hashes must be cycle007 hex identities")
        if entry["sidecar_id"] in seen_sidecar_ids:
            _fail("manifest_shape_drift", "sidecar index entries must have unique sidecar_id values")
        seen_sidecar_ids.add(entry["sidecar_id"])
        if entry["lane"] not in _SIDECAR_LANES:
            _fail("manifest_shape_drift", f"sidecar index entry has an unknown lane: {entry['lane']!r}")
        _validate_packet_binding(entry["packet_binding"], code="packet_binding_shape_drift")
        row_count += entry["row_count"]
    if manifest["row_count"] != row_count:
        _fail("manifest_shape_drift", "manifest row_count does not match the sum of sidecar row_counts")
    if not _is_nonnegative_int(manifest["packet_count"]) or not _is_nonnegative_int(manifest["row_count"]):
        _fail("manifest_shape_drift", "manifest packet_count and row_count must be non-negative integers")
    if not _is_nonempty_string(manifest["tokenizer_id"]) or not _is_nonempty_string(manifest["tokenizer_version"]):
        _fail("manifest_shape_drift", "manifest tokenizer identity must be non-empty strings")
    _validate_code_hashes(manifest["code_hashes"], code="manifest_shape_drift")
    if (
        manifest["code_hashes"]["tokenizer_id"] != manifest["tokenizer_id"]
        or manifest["code_hashes"]["tokenizer_version"] != manifest["tokenizer_version"]
    ):
        _fail("manifest_shape_drift", "manifest tokenizer identity disagrees with code_hashes")
    for field in ("server_code_sha256", "sources_db_sha256", "vesum_db_sha256", "manifest_sha256"):
        if not _is_sha256(manifest[field]):
            _fail("manifest_shape_drift", f"manifest {field} must be a hex sha256")

    count_maps = (
        ("counts_by_channel", frozenset(contract.CHANNELS)),
        ("counts_by_status", frozenset(contract.STATUSES)),
        ("counts_by_supports", frozenset(contract.SUPPORTS)),
    )
    count_totals: list[int] = []
    for field, vocabulary in count_maps:
        counts = manifest[field]
        if not isinstance(counts, Mapping) or any(
            not isinstance(key, str) or key not in vocabulary or not _is_nonnegative_int(value)
            for key, value in counts.items()
        ):
            _fail("manifest_shape_drift", f"manifest {field} has an unexpected shape")
        count_totals.append(sum(counts.values()))
    if len(set(count_totals)) != 1:
        _fail("manifest_shape_drift", "manifest evidence count maps disagree on their total")
    for field in ("sufficient_support_rows", "archaic_only_risk_rows", "russian_shadow_suspected_rows"):
        if not _is_nonnegative_int(manifest[field]) or manifest[field] > manifest["row_count"]:
            _fail("manifest_shape_drift", f"manifest {field} must be a non-negative count within row_count")

    source_package_binding = manifest["source_package_binding"]
    if source_package_binding is not None:
        if not isinstance(source_package_binding, Mapping) or set(source_package_binding) != _SOURCE_PACKAGE_BINDING_FIELDS:
            _fail("source_package_binding_shape_drift", "source_package_binding has an unexpected shape")
        if source_package_binding["source_evaluation_cycle_id"] != _SOURCE_EVALUATION_CYCLE_ID:
            _fail("source_package_binding_shape_drift", "source_package_binding has an unexpected source cycle")
        for field in (
            "custody_receipt_raw_sha256", "materialization_manifest_sha256", "ordered_identity_commitment_sha256",
            "identity_union_commitment_sha256", "ordered_packet_commitment_sha256",
        ):
            if not _is_sha256(source_package_binding[field]):
                _fail("source_package_binding_shape_drift", f"source_package_binding {field} must be a hex sha256")
        for field in ("packet_count", "row_count"):
            if not _is_nonnegative_int(source_package_binding[field]):
                _fail("source_package_binding_shape_drift", f"source_package_binding {field} must be a non-negative integer")
        if (
            source_package_binding["packet_count"] != manifest["packet_count"]
            or source_package_binding["row_count"] != manifest["row_count"]
        ):
            _fail("source_package_binding_shape_drift", "source_package_binding counts disagree with the manifest")

    transport_attestation = manifest["mcp_transport_attestation"]
    if transport_attestation is not None:
        if (
            not isinstance(transport_attestation, Mapping)
            or set(transport_attestation) != _MCP_TRANSPORT_ATTESTATION_FIELDS
        ):
            _fail("mcp_transport_attestation_drift", "MCP transport attestation has an unexpected shape")
        if transport_attestation["schema_version"] != "phase3_cycle007_mcp_transport_attestation_v1":
            _fail("mcp_transport_attestation_drift", "unexpected MCP transport attestation schema")
        for field in ("endpoint_sha256", "required_tool_set_sha256", "ordered_call_commitment_sha256"):
            if not _is_sha256(transport_attestation[field]):
                _fail("mcp_transport_attestation_drift", f"{field} must be a hex sha256")
        counts_by_tool = transport_attestation["counts_by_tool"]
        if not isinstance(counts_by_tool, Mapping) or any(
            not _is_nonempty_string(tool) or not _is_nonnegative_int(count)
            for tool, count in counts_by_tool.items()
        ):
            _fail("mcp_transport_attestation_drift", "counts_by_tool has an unexpected shape")
        if (
            not _is_nonnegative_int(transport_attestation["tool_call_count"])
            or sum(counts_by_tool.values()) != transport_attestation["tool_call_count"]
            or not _is_nonnegative_int(transport_attestation["server_identity_call_count"])
            or counts_by_tool.get("mcp_server_identity", 0)
            != transport_attestation["server_identity_call_count"]
        ):
            _fail("mcp_transport_attestation_drift", "MCP tool-call counts do not reconcile")

    real_denominator = (
        manifest["packet_count"] == _REAL_PACKET_COUNT
        and manifest["row_count"] == _REAL_ROW_COUNT
        and source_package_binding is not None
    )
    if real_denominator and (
        not isinstance(transport_attestation, Mapping)
        or transport_attestation.get("transport") != "streamable_http"
        or transport_attestation.get("endpoint_sha256") != _EXPECTED_MCP_ENDPOINT_SHA256
        or transport_attestation.get("server_identity_call_count") != 1
        or not isinstance(transport_attestation.get("tool_call_count"), int)
        or transport_attestation.get("tool_call_count", 0) <= manifest["row_count"]
    ):
        _fail(
            "mcp_transport_attestation_drift",
            "the real denominator requires one identity check and committed streamable-HTTP tool calls",
        )

    for field in _IDENTITY_FIELDS:
        if manifest[field] != expected_identity.get(field):
            _fail("identity_hash_drift", f"manifest {field!r} does not match the expected current identity")

    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    recomputed = contract.sha256_value(body)
    if recomputed != manifest["manifest_sha256"]:
        _fail("manifest_id_hash_drift", "manifest_sha256 does not match its own content hash")


def classify_sufficiency(row_evidence: Mapping[str, Any], *, phenomenon_id: str | None = None) -> str:
    """Classify why a row's evidence is (in)sufficient for a positive decision.

    Returns one of ``"sufficient"``, ``"insufficient_conflicting"``,
    ``"insufficient_unavailable"``, ``"insufficient_missing"``. Amendment
    step 7 ("Frozen Sources MCP evidence layer" / "Fix sufficiency
    ordering"): a decisive channel's own missing/conflicting/ambiguous/
    incomplete/parse-error/unavailable result forces the uncertainty path
    *even when another record is attested* — a negative decisive-channel
    result is checked first and is never overridden by an unrelated
    sufficient-positive record. Only once every decisive channel is clean
    does an attested sufficient-positive record count. When
    ``phenomenon_id`` is given, both the decisive-channel scan and the
    sufficient-positive scan are restricted to that phenomenon's bound
    evidence (row-level channels never satisfy a residual phenomenon).
    """
    evidence: Sequence[Mapping[str, Any]] = row_evidence.get("evidence", [])
    if phenomenon_id is not None:
        evidence = [record for record in evidence if str(record.get("phenomenon_id")) == str(phenomenon_id)]
    decisive = [record for record in evidence if record["channel"] in _DECISIVE_CHANNELS]
    if any(record["status"] in {"ambiguous", "incomplete", "parse_error"} for record in decisive):
        return "insufficient_conflicting"
    if any(record["status"] == "unavailable" for record in decisive):
        return "insufficient_unavailable"
    if any(record["status"] == "not_found" for record in decisive):
        if any(contract.is_sufficient_positive(record) for record in evidence):
            return "insufficient_conflicting"
        return "insufficient_missing"
    if any(contract.is_sufficient_positive(record) for record in evidence):
        return "sufficient"
    return "insufficient_missing"


def validate_label_evidence_refs(
    row_evidence: Mapping[str, Any],
    *,
    decision_code: str,
    evidence_ids: Sequence[str],
    phenomenon_id: str | None = None,
) -> None:
    """Fail-closed gate for one candidate label decision's evidence references.

    Call this once per clean label (``phenomenon_id=None``) or once per
    residual phenomenon (``phenomenon_id=<id>``) before accepting any model
    decision code.
    """
    if decision_code not in KNOWN_DECISIONS:
        _fail("unknown_decision_code", decision_code)

    ids_list = list(evidence_ids)
    if ids_list != sorted(set(ids_list)):
        _fail("evidence_id_order_drift", "label evidence_ids must be sorted and unique")

    if phenomenon_id is None:
        available = set(row_evidence.get("evidence_ids", []))
        scope_error_code = "cross_row_evidence"
    else:
        available = set(row_evidence.get("phenomenon_evidence_ids", {}).get(phenomenon_id, []))
        scope_error_code = "cross_phenomenon_evidence"

    invented_or_out_of_scope = set(ids_list) - available
    if invented_or_out_of_scope:
        _fail(scope_error_code, f"evidence ids not bound to this exact row/phenomenon: {sorted(invented_or_out_of_scope)}")

    if decision_code in SUFFICIENT_REQUIRED_DECISIONS:
        by_id = {str(record["evidence_id"]): record for record in row_evidence.get("evidence", [])}
        cited_records = [by_id[evidence_id] for evidence_id in ids_list if evidence_id in by_id]
        # Amendment step 7: a decisive channel's own negative/unresolved
        # result forces the uncertainty path even when the label additionally
        # cites an attested sufficient-positive record elsewhere. Sufficiency
        # is judged over the row's (or, for a residual label, this exact
        # phenomenon's) full decisive-channel evidence, not merely the cited
        # subset — a label cannot silently omit a conflicting citation to
        # manufacture sufficiency.
        sufficiency = classify_sufficiency(row_evidence, phenomenon_id=phenomenon_id)
        cited_sufficient_positive = any(contract.is_sufficient_positive(record) for record in cited_records)
        if sufficiency != "sufficient" or not cited_sufficient_positive:
            _fail(
                "insufficient_evidence_for_decision",
                f"decision_code={decision_code!r} requires sufficient normative/attestation evidence "
                f"(sufficiency={sufficiency}); only the uncertainty path is valid here",
            )
