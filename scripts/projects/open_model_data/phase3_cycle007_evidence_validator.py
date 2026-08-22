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

from collections.abc import Mapping, Sequence
from typing import Any

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

# Decisions that require sufficient normative/attestation evidence (amendment
# model-contract section). Any other outcome is the fail-closed uncertainty
# path and never needs sufficiency.
SUFFICIENT_REQUIRED_DECISIONS = frozenset({"agree", "positive", "acceptable_control", "protected"})
UNCERTAINTY_DECISIONS = frozenset({"reject_insufficient_locator_evidence", "abstention", "disagreement"})
KNOWN_DECISIONS = SUFFICIENT_REQUIRED_DECISIONS | UNCERTAINTY_DECISIONS

# Channels whose absence/ambiguity actually drives a sufficiency classification.
_DECISIVE_CHANNELS = frozenset({"vesum_attestation", "heritage_attestation", "pravopys_2026_normative"})


class EvidenceValidationError(ValueError):
    """A Cycle 007 evidence sidecar or label evidence reference fails closed."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise EvidenceValidationError(code, message)


def validate_evidence_record(record: Mapping[str, Any]) -> None:
    """Re-derive the evidence ID and re-check the closed claim boundary."""
    for key in (
        "schema_version",
        "evidence_id",
        "channel",
        "source_identity",
        "source_version",
        "locator",
        "query_sha256",
        "status",
        "supports",
        "retrieval_sha256",
        "parser_id",
        "parser_version",
        "row_identity",
        "phenomenon_id",
    ):
        if key not in record:
            _fail("evidence_shape_drift", f"evidence record missing {key!r}")
    if record["schema_version"] != contract.EVIDENCE_SCHEMA_VERSION:
        _fail("evidence_shape_drift", "unexpected evidence schema_version")
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
    if record["status"] == "attested" and record.get("negative_reason") is not None:
        _fail("evidence_shape_drift", "attested evidence cannot carry a negative_reason")
    if record["status"] != "attested" and record["supports"] != "no_conclusion":
        _fail("source_role_boundary_violation", "non-attested evidence must carry supports=no_conclusion")


def validate_row_evidence(row_evidence: Mapping[str, Any]) -> None:
    """Validate one row's compiled evidence set: unique IDs, correct scoping, closed boundaries."""
    unit_id = row_evidence.get("unit_id")
    unit_sha256 = row_evidence.get("unit_sha256")
    if not (isinstance(unit_id, str) and unit_id and isinstance(unit_sha256, str) and len(unit_sha256) == 64):
        _fail("row_identity_drift", "row evidence missing/malformed unit_id or unit_sha256")

    evidence: Sequence[Mapping[str, Any]] = row_evidence.get("evidence", [])
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

    declared_ids = list(row_evidence.get("evidence_ids", []))
    if declared_ids != sorted(set(declared_ids)):
        _fail("evidence_id_order_drift", "row evidence_ids must be sorted and unique")
    if set(declared_ids) != seen_ids:
        _fail("evidence_id_set_drift", "declared evidence_ids does not match the compiled evidence records")

    phenomenon_ids: Mapping[str, Any] = row_evidence.get("phenomenon_evidence_ids", {})
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


def validate_sidecar(sidecar: Mapping[str, Any]) -> None:
    """Validate every row in one packet's compiled sidecar."""
    if sidecar.get("schema_version") != "phase3_cycle007_evidence_sidecar_v1":
        _fail("sidecar_shape_drift", "unexpected sidecar schema_version")
    rows = sidecar.get("rows", [])
    if not isinstance(rows, list) or not rows:
        _fail("sidecar_shape_drift", "sidecar has no rows")
    seen_units: set[tuple[str, str]] = set()
    for row_evidence in rows:
        validate_row_evidence(row_evidence)
        key = (row_evidence["unit_id"], row_evidence["unit_sha256"])
        if key in seen_units:
            _fail("duplicate_row", f"duplicate row identity within one sidecar: {key}")
        seen_units.add(key)


def classify_sufficiency(row_evidence: Mapping[str, Any]) -> str:
    """Classify why a row's evidence is (in)sufficient for a positive decision.

    Returns one of ``"sufficient"``, ``"insufficient_conflicting"``,
    ``"insufficient_unavailable"``, ``"insufficient_missing"``. Priority:
    conflicting > unavailable > missing, matching "missing, conflicting,
    truncated, unparseable, or unavailable source evidence is marked
    unresolved" (amendment, "Frozen Sources MCP evidence layer").
    """
    evidence = row_evidence.get("evidence", [])
    if any(contract.is_sufficient_positive(record) for record in evidence):
        return "sufficient"
    decisive = [record for record in evidence if record["channel"] in _DECISIVE_CHANNELS]
    if any(record["status"] in {"ambiguous", "incomplete", "parse_error"} for record in decisive):
        return "insufficient_conflicting"
    if any(record["status"] == "unavailable" for record in decisive):
        return "insufficient_unavailable"
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
        if not any(contract.is_sufficient_positive(record) for record in cited_records):
            sufficiency = classify_sufficiency(row_evidence)
            _fail(
                "insufficient_evidence_for_decision",
                f"decision_code={decision_code!r} requires sufficient normative/attestation evidence "
                f"(sufficiency={sufficiency}); only the uncertainty path is valid here",
            )
