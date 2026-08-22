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
    # Amendment step 12: raw_payload_publication_allowed=false and the
    # non-authoritative claim-boundary flags are frozen constants, never
    # hand-editable to a truthy value.
    if record.get("raw_payload_publication_allowed") is not False:
        _fail("evidence_shape_drift", "raw_payload_publication_allowed must be false")
    claim_boundary = record.get("claim_boundary")
    if not isinstance(claim_boundary, Mapping) or any(
        claim_boundary.get(key) is not False
        for key in ("authoritative", "human_gold", "model_vote_authoritative", "vesum_absence_only_authoritative")
    ):
        _fail("evidence_shape_drift", "claim_boundary must be the frozen all-false non-authoritative flag set")


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
    """Validate every row in one packet's compiled sidecar.

    Amendment step 12: also re-derives ``sidecar_id`` and checks
    ``row_count`` against the actual ``rows`` list, and, when a
    ``retrieval_payloads`` dedup table is present, that every evidence
    record's ``retrieval_sha256`` resolves to an entry in it (nothing is
    silently missing from the private payload table it claims to hold).
    """
    if sidecar.get("schema_version") != "phase3_cycle007_evidence_sidecar_v1":
        _fail("sidecar_shape_drift", "unexpected sidecar schema_version")
    rows = sidecar.get("rows", [])
    if not isinstance(rows, list) or not rows:
        _fail("sidecar_shape_drift", "sidecar has no rows")
    if sidecar.get("row_count") != len(rows):
        _fail("sidecar_shape_drift", "sidecar row_count does not match len(rows)")
    if "sidecar_id" in sidecar:
        body = {key: value for key, value in sidecar.items() if key != "sidecar_id"}
        recomputed_sidecar_id = "cycle007_sidecar:" + contract.sha256_value(body)
        if recomputed_sidecar_id != sidecar["sidecar_id"]:
            _fail("sidecar_id_hash_drift", "sidecar_id does not match its own content hash")
    retrieval_payloads = sidecar.get("retrieval_payloads")
    seen_units: set[tuple[str, str]] = set()
    for row_evidence in rows:
        validate_row_evidence(row_evidence)
        key = (row_evidence["unit_id"], row_evidence["unit_sha256"])
        if key in seen_units:
            _fail("duplicate_row", f"duplicate row identity within one sidecar: {key}")
        seen_units.add(key)
        if isinstance(retrieval_payloads, Mapping):
            for record in row_evidence.get("evidence", []):
                if str(record["retrieval_sha256"]) not in retrieval_payloads:
                    _fail(
                        "retrieval_payload_missing",
                        f"evidence {record['evidence_id']} retrieval_sha256 absent from retrieval_payloads",
                    )


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate the text-free compile manifest's own content hash and shape.

    Amendment step 12: re-derives ``manifest_sha256`` and requires
    ``packet_count``/``row_count`` to match the actual ``sidecars`` list.
    """
    if manifest.get("schema_version") != "phase3_cycle007_evidence_manifest_v1":
        _fail("manifest_shape_drift", "unexpected manifest schema_version")
    if manifest.get("text_free") is not True:
        _fail("manifest_shape_drift", "manifest must be text_free=true")
    sidecars = manifest.get("sidecars")
    if not isinstance(sidecars, list) or not sidecars:
        _fail("manifest_shape_drift", "manifest has no sidecars")
    if manifest.get("packet_count") != len(sidecars):
        _fail("manifest_shape_drift", "manifest packet_count does not match len(sidecars)")
    row_count = sum(int(entry.get("row_count", 0)) for entry in sidecars if isinstance(entry, Mapping))
    if manifest.get("row_count") != row_count:
        _fail("manifest_shape_drift", "manifest row_count does not match the sum of sidecar row_counts")
    if "manifest_sha256" in manifest:
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
