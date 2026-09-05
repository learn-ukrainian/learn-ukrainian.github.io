#!/usr/bin/env python3
"""V4 A5 expression-free evidence enrichment: content-blind structural
evidence bound to A4's already-published, hash-only extraction commitments.

A5 is the builder-facing role that turns A4's private, per-span extraction
ledger (``source_unit_commitment_sha256``, ``span_index``, ``span_byte_length``,
``input_sha256``, ``output_sha256`` -- never span text) into a small, public,
*expression-free* structural-evidence summary, keyed only by the same
``source_unit_commitment_sha256`` values A4's own ``builder_packet_
consumption.unit_commitments`` already publishes. "Expression-free" means
this module never reads, counts, buckets, or otherwise interprets a span's
*content* -- not the words, not even the hashes' bit patterns -- only the one
already-public-shaped numeric field A4's ledger rows carry alongside their
hashes: ``span_byte_length``. Every other ledger field this module touches
(``source_unit_commitment_sha256``, the row count) is used only for grouping
and cross-checking, never interpreted as language.

Like A4, A5 is firewalled from the held-out pool: see
``dataset_v4_a3_heldout_source_family_seal_receipt_v1.json``'s
``access_firewall``, where ``A5_evidence_enrichment`` is locked to
``heldout_family_pool_visible: false`` and forbidden from every held-out
field. This module never opens ``batch_state/open-model-data/v4-a3-heldout/
v4_a3_heldout_membership_v1.json`` and never opens the private builder packet
either -- its only private input is A4's own already-materialized extraction
ledger and ledger manifest, both hash-only, both already independent of the
held-out membership by construction (A4 itself never learns held-out
identity; see that module's docstring).

Three independent parts:

1. ``ENRICHMENT_ALGORITHM_DESCRIPTOR`` -- the frozen, hashed, content-blind
   aggregation formula: stream A4's private extraction ledger once, group by
   ``source_unit_commitment_sha256`` (one of the (currently 8) values A4's
   own receipt already publishes -- never a value this module invents), and
   accumulate ``span_count``/``total_span_bytes``/``min_span_byte_length``/
   ``max_span_byte_length`` per commitment. The accumulator holds one small
   fixed-size dict (one entry per known commitment, currently 8) regardless
   of how many millions of rows stream through it -- never a list of rows,
   matching A4's own memory discipline (see ``aggregate_ledger_rows`` and
   ``stream_ledger_rows_for_units`` in ``v4_a4_deterministic_extraction.py``,
   whose ``iter_private_artifact_lines`` this module reuses directly rather
   than re-opening the ledger file itself).
2. ``check_enrichment_gate`` -- independently re-derives whether A5 may run
   at all from the bound, public A4 receipt on disk (never trusting the A5
   receipt's own declared fields): the A4 receipt must independently
   validate (``v4_a4_deterministic_extraction.validate_receipt_
   independently``) and its ``builder_packet_consumption.packet_consumed``
   must be true. Public-only -- passes in a fresh checkout with no
   ``batch_state/``.
3. ``compute_evidence_enrichment`` -- the real streaming pass: opens A4's
   private extraction-ledger manifest (verify-only; never writes anything),
   requires it matches the live A4 receipt's declared
   ``extraction_ledger_commitment`` exactly, then streams the private ledger
   file itself (never ``.read()``, never a materialized row list) and
   accumulates the per-commitment aggregates. Fails closed
   (``EnrichmentError``/``heldout.AssignmentError``/``MemoryBudgetExceeded``)
   if the private manifest or ledger is missing, unreadable, drifted, or a
   streamed row references a commitment outside A4's own public
   ``unit_commitments`` set.

Run with no arguments to verify the checked-in A5 receipt reproduces all
three parts and is consistent with the bound A4 receipt on disk -- using only
public artifacts, so this passes in a fresh checkout with no ``batch_state/``.
Pass ``--consume`` (only meaningful where A4's private extraction ledger
actually exists) to stream it for real and (re)compute the real per-
commitment structural evidence; add ``--write-receipt`` to persist a freshly
assembled public receipt. Pass ``--verify-private`` to additionally
re-derive the checked-in receipt's ``evidence_enrichment`` fields
cryptographically from a full streaming replay of the private ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from learn_ukrainian_v4_runtime.resources import resource_root

try:
    import resource
except ImportError:  # pragma: no cover - resource is POSIX-only; this project targets Linux
    resource = None  # type: ignore[assignment]

_SELF_ROOT = resource_root()

from learn_ukrainian_v4_runtime import v4_a3_heldout_family_assignment as heldout
from learn_ukrainian_v4_runtime import v4_a4_deterministic_extraction as extraction

ROOT = heldout.ROOT
PRIMARY_ROOT = heldout.PRIMARY_ROOT
PRIVATE_ROOT = heldout.PRIVATE_ROOT

ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
A5_SCHEMA_PATH = CONTRACTS / "dataset_v4_a5_evidence_enrichment_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"

# A5 has no private state of its own: its only private input is A4's own
# already-materialized ledger/manifest (read-only, never written to, never
# copied). Same directory A4 itself uses.
DEFAULT_A4_PRIVATE_DIR = extraction.DEFAULT_A4_PRIVATE_DIR

# Hard cap on a streaming pass's own incremental resident-memory growth --
# generous, since the accumulator itself never grows past one small dict
# keyed by A4's (currently 8) known commitments regardless of ledger size;
# this exists only as defense-in-depth against a future change accidentally
# buffering rows. Bounds growth relative to a baseline snapshot taken at the
# start of the pass (see ``_require_within_memory_budget``), never the host
# process's absolute, process-lifetime ``ru_maxrss`` high-water mark.
DEFAULT_A5_MEMORY_CAP_BYTES = 512 * 1024 * 1024
_MEMORY_CHECK_INTERVAL_ROWS = 2_000

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# Fields no builder-facing artifact -- including this one -- may ever carry.
# Mirrors v4_a4_deterministic_extraction.FORBIDDEN_KEYS.
FORBIDDEN_KEYS = frozenset(
    {
        "content",
        "text",
        "source_body",
        "source_text",
        "source_unit_id",
        "prompt",
        "label",
        "gold",
        "heldout_membership",
        "heldout_locator",
        "heldout_fingerprint",
        "heldout_neighbour",
        "heldout_near_neighbour",
        "held_out_membership",
        "heldout_family_pool",
        "heldout_membership_locator",
        "salt",
        "salt_hex",
        "private_salt",
    }
)

# Substrings that would, by themselves, leak a real or held-out identity if
# they ever appeared in this (public) receipt's serialized form -- checked in
# addition to FORBIDDEN_KEYS, which only screens field *names*.
FORBIDDEN_SUBSTRINGS = ("fam-", "db.", "historical.")


class EnrichmentError(ValueError):
    """Enrichment cannot proceed safely, or a receipt/binding failed to verify."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EnrichmentError(message)


canonical_json = heldout.canonical_json


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- frozen, content-blind, expression-blind aggregation algorithm ---------
#
# Reads only ``source_unit_commitment_sha256`` (for grouping, already public
# via A4's ``unit_commitments``) and ``span_byte_length`` (a bare integer,
# never interpreted as language) from each private ledger row. Never reads
# ``input_sha256``/``output_sha256`` for anything but pass-through row
# identity -- this module does not even need them, and never emits them.

ENRICHMENT_ALGORITHM_DESCRIPTOR: dict[str, Any] = {
    "algorithm_id": "v4-a5-structural-evidence-enrichment-v1",
    "algorithm_version": "v1",
    "unit_of_enrichment": "source_unit_commitment",
    "content_blind": True,
    "expression_blind": True,
    "ordering": "source_unit_commitment_sha256_ascending",
    "aggregated_fields": ["span_count", "total_span_bytes", "min_span_byte_length", "max_span_byte_length"],
    "aggregation_formula": (
        "for each row in A4's private extraction ledger (only source_unit_commitment_sha256 and "
        "span_byte_length are read -- input_sha256/output_sha256/span text are never inspected): "
        "span_count[commitment] += 1; total_span_bytes[commitment] += span_byte_length; "
        "min_span_byte_length[commitment] = min(existing, span_byte_length); "
        "max_span_byte_length[commitment] = max(existing, span_byte_length); a commitment with no rows "
        "keeps span_count 0, total_span_bytes 0, min/max null"
    ),
    "evidence_commitment_formula": (
        "sha256(canonical_json(per_unit_evidence sorted by source_unit_commitment_sha256))"
    ),
    "text_emitted": False,
    "expression_emitted": False,
    "reproducibility": (
        "byte_stable_given_the_identical_private_a4_extraction_ledger_and_the_frozen_aggregation_formula"
    ),
}

ENRICHMENT_ALGORITHM_DESCRIPTOR_SHA256 = sha256_text(canonical_json(ENRICHMENT_ALGORITHM_DESCRIPTOR))

EMPTY_EVIDENCE_COMMITMENT_SHA256 = sha256_text(canonical_json([]))


def new_unit_accumulator() -> dict[str, Any]:
    return {"span_count": 0, "total_span_bytes": 0, "min_span_byte_length": None, "max_span_byte_length": None}


def accumulate_row(accumulator: dict[str, Any], span_byte_length: int) -> None:
    """Pure mutation of a single commitment's running aggregate. Never sees a
    hash, never sees text -- only the one bare integer field."""
    accumulator["span_count"] += 1
    accumulator["total_span_bytes"] += span_byte_length
    accumulator["min_span_byte_length"] = (
        span_byte_length
        if accumulator["min_span_byte_length"] is None
        else min(accumulator["min_span_byte_length"], span_byte_length)
    )
    accumulator["max_span_byte_length"] = (
        span_byte_length
        if accumulator["max_span_byte_length"] is None
        else max(accumulator["max_span_byte_length"], span_byte_length)
    )


class MemoryBudgetExceeded(EnrichmentError):
    """A streaming enrichment pass would exceed its configured resident-
    memory cap. Raised, never silently ignored -- see
    ``v4_a4_deterministic_extraction.MemoryBudgetExceeded`` for the sibling
    guard this mirrors."""


def _current_rss_bytes() -> int:
    if resource is None:  # pragma: no cover - POSIX-only module, see import above
        return 0
    ru_maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return ru_maxrss if sys.platform == "darwin" else ru_maxrss * 1024


def _require_within_memory_budget(baseline_rss_bytes: int, memory_cap_bytes: int) -> None:
    """Fail closed once *this pass's own* resident-memory growth -- current
    ``ru_maxrss`` minus the ``baseline_rss_bytes`` snapshot taken before the
    pass started -- exceeds ``memory_cap_bytes``. Deliberately never compares
    the raw absolute ``ru_maxrss`` to the cap: ``ru_maxrss`` is a process-
    lifetime high-water mark, so in a long-lived host process (thousands of
    prior pytest cases, a long-running worker) it can already sit well above
    a 512 MiB cap before this pass ever streams a single row -- that
    inherited high-water is not this pass's memory use and must not trip the
    guard on its own."""
    rss_bytes = _current_rss_bytes()
    incremental_bytes = rss_bytes - baseline_rss_bytes
    if incremental_bytes > memory_cap_bytes:
        raise MemoryBudgetExceeded(
            f"streaming enrichment aborted: this pass's incremental resident memory {incremental_bytes} "
            f"bytes (baseline {baseline_rss_bytes}, current {rss_bytes}) exceeded the configured cap of "
            f"{memory_cap_bytes} bytes -- failing closed"
        )


def aggregate_ledger_rows(
    ledger_lines: Iterable[str],
    known_commitments: Iterable[str],
    *,
    memory_cap_bytes: int = DEFAULT_A5_MEMORY_CAP_BYTES,
    memory_check_interval: int = _MEMORY_CHECK_INTERVAL_ROWS,
    baseline_rss_bytes: int | None = None,
) -> tuple[dict[str, dict[str, Any]], int]:
    """Stream ``ledger_lines`` (one JSON line per span row, as produced by
    ``v4_a4_deterministic_extraction.iter_private_artifact_lines``) exactly
    once, accumulating per-commitment aggregates. Never materializes the
    ledger as a list -- the only state held across iterations is the
    accumulator dict, one entry per ``known_commitments`` (currently 8),
    never one per row. Fails closed (``EnrichmentError``) if a row names a
    commitment outside ``known_commitments`` (private-artifact drift or
    corruption), and (``MemoryBudgetExceeded``) if this pass's own resident
    memory growth would exceed ``memory_cap_bytes``.

    ``baseline_rss_bytes`` is snapshotted once, at the start of this call, so
    the cap bounds only the growth this pass itself causes -- never the host
    process's inherited high-water mark. Pass it explicitly only to amortize
    one baseline across multiple passes sharing a budget; the default (taking
    a fresh snapshot here) is correct for a standalone call."""
    if baseline_rss_bytes is None:
        baseline_rss_bytes = _current_rss_bytes()
    accumulators = {commitment: new_unit_accumulator() for commitment in known_commitments}
    total_rows = 0
    for line in ledger_lines:
        row = json.loads(line)
        commitment = row["source_unit_commitment_sha256"]
        require(
            commitment in accumulators,
            "private extraction ledger row references a commitment outside A4's public unit_commitments "
            "-- refusing (private-artifact drift or corruption)",
        )
        accumulate_row(accumulators[commitment], row["span_byte_length"])
        total_rows += 1
        if total_rows % memory_check_interval == 0:
            _require_within_memory_budget(baseline_rss_bytes, memory_cap_bytes)
    _require_within_memory_budget(baseline_rss_bytes, memory_cap_bytes)
    return accumulators, total_rows


def build_per_unit_evidence(accumulators: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Sorted by commitment value -- every known commitment appears exactly
    once, uniformly, whether or not it has any spans (mirrors A4's own
    ``derive_source_unit_extraction_residuals``: never selectively silent
    about a zero-evidence commitment, which would itself be a signal)."""
    return [
        {"source_unit_commitment_sha256": commitment, **accumulators[commitment]} for commitment in sorted(accumulators)
    ]


def evidence_commitment_sha256(per_unit_evidence: list[dict[str, Any]]) -> str:
    return sha256_text(canonical_json(per_unit_evidence))


# --- enrichment gate (public-only) ------------------------------------------


def check_enrichment_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive whether A5 may enrich at all, from the bound,
    public A4 receipt on disk -- never trusting the A5 receipt's own
    declared fields, never opening ``batch_state/``. Requires the A4 receipt
    to itself independently validate (schema, bindings, gate, residuals) and
    to declare ``builder_packet_consumption.packet_consumed`` true."""
    a4_receipt_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a4_deterministic_extraction_receipt_v1.json"
    ).resolve()
    require(root.resolve() in a4_receipt_path.parents, "A4 receipt path escapes the repository root -- refusing")

    if not a4_receipt_path.is_file():
        return {
            "gate_id": "v4-a5-enrichment-gate-v1",
            "a4_receipt_present": False,
            "a4_receipt_valid": False,
            "a4_extraction_available": False,
            "owner_role": "A4_deterministic_extraction",
            "blocked_reason_code": "a4_receipt_missing",
        }

    a4_receipt = _load(a4_receipt_path)
    require(
        a4_receipt.get("controlling_outcome_sha256") == V4_SHA256,
        "A4 receipt is not bound to the expected V4 controlling outcome -- refusing",
    )

    try:
        extraction.validate_receipt_independently(a4_receipt, root)
        a4_receipt_valid = True
    except extraction.ExtractionError:
        a4_receipt_valid = False

    packet_consumed = bool(a4_receipt.get("builder_packet_consumption", {}).get("packet_consumed"))
    gate_open = a4_receipt_valid and packet_consumed
    blocked_reason_code = None
    if not gate_open:
        blocked_reason_code = "a4_receipt_invalid" if not a4_receipt_valid else "a4_packet_not_consumed"

    return {
        "gate_id": "v4-a5-enrichment-gate-v1",
        "a4_receipt_present": True,
        "a4_receipt_valid": a4_receipt_valid,
        "a4_extraction_available": gate_open,
        "owner_role": "A4_deterministic_extraction",
        "blocked_reason_code": blocked_reason_code,
    }


# --- real evidence-ledger consumption ---------------------------------------


def compute_evidence_enrichment(
    a4_receipt: dict[str, Any],
    a4_private_dir: Path = DEFAULT_A4_PRIVATE_DIR,
    memory_cap_bytes: int = DEFAULT_A5_MEMORY_CAP_BYTES,
) -> dict[str, Any]:
    """Open A4's real private extraction-ledger manifest (verify-only) and,
    if it declares any rows, stream the real private ledger file itself
    (never A4's private packet, never the held-out membership -- A5 has no
    access to either) to compute the real per-commitment structural
    evidence.

    Fails closed (``EnrichmentError``/``heldout.AssignmentError``/
    ``MemoryBudgetExceeded``) if ``a4_receipt`` does not declare a consumed
    builder packet, if A4's private manifest/ledger is missing, unreadable,
    or drifted against the live A4 receipt's own declared
    ``extraction_ledger_commitment``, or if the streamed row count does not
    match the manifest's own declared count."""
    consumption = a4_receipt["builder_packet_consumption"]
    known_commitments = consumption["unit_commitments"]

    if not consumption["packet_consumed"]:
        return {
            "ledger_consumed": False,
            "per_unit_evidence": [],
            "evidence_commitment_sha256": EMPTY_EVIDENCE_COMMITMENT_SHA256,
            "spans_covered": 0,
            "units_with_evidence": 0,
        }

    ledger_commitment = consumption["extraction_ledger_commitment"]
    manifest_path = a4_private_dir / extraction.A4_LEDGER_MANIFEST_FILENAME
    stored_manifest = heldout.load_private_artifact(
        manifest_path, required_fields=extraction.A4_LEDGER_MANIFEST_REQUIRED_FIELDS
    )
    require(
        stored_manifest["row_count"] == ledger_commitment["row_count"]
        and stored_manifest["root_sha256"] == ledger_commitment["root_sha256"],
        "private A4 extraction-ledger manifest drift against the live A4 receipt's "
        "extraction_ledger_commitment -- refusing (A4 must be re-run/re-verified first)",
    )

    if ledger_commitment["row_count"] == 0:
        accumulators = {commitment: new_unit_accumulator() for commitment in known_commitments}
        total_rows = 0
    else:
        ledger_path = a4_private_dir / extraction.A4_LEDGER_FILENAME
        lines = extraction.iter_private_artifact_lines(ledger_path)
        accumulators, total_rows = aggregate_ledger_rows(lines, known_commitments, memory_cap_bytes=memory_cap_bytes)
        require(
            total_rows == ledger_commitment["row_count"],
            "streamed row count does not match A4's declared extraction_ledger_commitment.row_count -- "
            "refusing (truncated, appended-to, or drifted private ledger)",
        )

    per_unit_evidence = build_per_unit_evidence(accumulators)
    return {
        "ledger_consumed": True,
        "per_unit_evidence": per_unit_evidence,
        "evidence_commitment_sha256": evidence_commitment_sha256(per_unit_evidence),
        "spans_covered": sum(entry["span_count"] for entry in per_unit_evidence),
        "units_with_evidence": sum(1 for entry in per_unit_evidence if entry["span_count"] > 0),
    }


def verify_evidence_privately(
    receipt: dict[str, Any],
    a4_receipt: dict[str, Any],
    a4_private_dir: Path = DEFAULT_A4_PRIVATE_DIR,
) -> None:
    """Full re-derivation of ``evidence_enrichment`` from a fresh streaming
    replay of A4's real private ledger. Not called by
    ``validate_receipt_independently`` (and therefore never required by the
    pytest suite, which must pass in a fresh checkout with no
    ``batch_state/``) -- call this explicitly (``--verify-private``) whenever
    A4's private artifacts are actually present."""
    recomputed = compute_evidence_enrichment(a4_receipt, a4_private_dir)
    declared = receipt["evidence_enrichment"]
    require(
        declared["ledger_consumed"] == recomputed["ledger_consumed"]
        and declared["per_unit_evidence"] == recomputed["per_unit_evidence"]
        and declared["evidence_commitment_sha256"] == recomputed["evidence_commitment_sha256"]
        and declared["spans_covered"] == recomputed["spans_covered"]
        and declared["units_with_evidence"] == recomputed["units_with_evidence"],
        "receipt evidence_enrichment does not reproduce from a fresh streaming replay of A4's real "
        "private extraction ledger -- refusing",
    )


# --- A5's own per-commitment residuals (public, content-blind) -------------

A5_RESIDUAL_REASON_EVIDENCE_COMPUTED = "structural_evidence_computed"
A5_RESIDUAL_REASON_EVIDENCE_PENDING = "structural_evidence_pending_source_ingestion"


def derive_a5_unit_evidence_residuals(
    a4_receipt: dict[str, Any], per_unit_evidence: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """One typed, per-known-commitment residual -- a pure function of A4's
    already-public ``unit_commitments`` plus this receipt's own
    ``per_unit_evidence`` (both already-trusted inputs; this never re-opens
    private state itself). Ordered by commitment value, like every other
    per-commitment array in this receipt family."""
    evidence_by_commitment = {entry["source_unit_commitment_sha256"]: entry for entry in per_unit_evidence}
    residuals = []
    for commitment in a4_receipt["builder_packet_consumption"]["unit_commitments"]:
        entry = evidence_by_commitment.get(commitment)
        span_count = entry["span_count"] if entry else 0
        if span_count > 0:
            reason_code = A5_RESIDUAL_REASON_EVIDENCE_COMPUTED
            owner_role = "A5_evidence_enrichment"
            next_action = (
                "no further action required -- structural evidence (span count and byte-length "
                "aggregates) is already computed for this commitment"
            )
            retryability = "not_retryable"
        else:
            reason_code = A5_RESIDUAL_REASON_EVIDENCE_PENDING
            owner_role = "V4_source_byte_ingestion"
            next_action = (
                "no byte-level spans exist yet for this commitment in A4's private extraction ledger -- "
                "structural evidence can only be computed once V4_source_byte_ingestion admits real byte "
                "content for the underlying source unit and A4 re-extracts"
            )
            retryability = "retryable"
        residuals.append(
            {
                "residual_id": f"a5-residual-{reason_code.replace('_', '-')}-{commitment[:16]}",
                "subject_kind": "source_unit_commitment",
                "subject_id": commitment,
                "stage": "A5",
                "reason_code": reason_code,
                "owner_role": owner_role,
                "next_action": next_action,
                "retryability": retryability,
                "evidence_refs": [
                    "admission.dataset_v4_a4_deterministic_extraction_receipt_v1.builder_packet_consumption",
                    "admission.dataset_v4_a5_evidence_enrichment_receipt_v1.evidence_enrichment",
                ],
            }
        )
    residuals.sort(key=lambda residual: residual["subject_id"])
    return residuals


# --- receipt assembly --------------------------------------------------------


def build_receipt(enrichment: dict[str, Any], gate: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)

    a2_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A2", "status": "unresolved_carried_to_a5"}
        for entry in a2_receipt["residuals"]
    ]
    a4_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A4", "status": "unresolved_carried_to_a5"}
        for entry in a4_receipt["a4_residuals"]
    ]

    a4_ledger_commitment = a4_receipt["builder_packet_consumption"]["extraction_ledger_commitment"]

    return {
        "schema_version": "dataset_v4_a5_evidence_enrichment_receipt_v1",
        "receipt_id": "dataset-v4-a5-evidence-enrichment-v1",
        "status": "A5_EVIDENCE_ENRICHMENT_COMPUTED_TEXT_FREE_EXPRESSION_FREE_NO_COMPLEMENT_ENUMERATION",
        "text_free": True,
        "expression_free": True,
        "controlling_outcome_sha256": V4_SHA256,
        "control_surfaces": {"public_control_issue": 7423, "pilot_child_issue": 7430, "private_operational_board": 622},
        "bindings": {
            "a2_source_operation_admission": {
                "path": str(A2_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A2_RECEIPT_PATH),
                "schema_version": "dataset_v4_a2_source_operation_admission_receipt_v1",
            },
            "a4_deterministic_extraction": {
                "path": str(A4_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A4_RECEIPT_PATH),
                "schema_version": "dataset_v4_a4_deterministic_extraction_receipt_v1",
            },
            "enrichment_algorithm_implementation": {
                "path": "scripts/projects/open_model_data/v4_a5_evidence_enrichment.py",
                "sha256": sha256_file(root / "scripts/projects/open_model_data/v4_a5_evidence_enrichment.py"),
                "schema_version": "v4_a5_evidence_enrichment_script_v1",
            },
        },
        "enrichment_algorithm": {
            **ENRICHMENT_ALGORITHM_DESCRIPTOR,
            "algorithm_descriptor_sha256": ENRICHMENT_ALGORITHM_DESCRIPTOR_SHA256,
        },
        "enrichment_gate": {
            "gate_id": gate["gate_id"],
            "status": "A4_EXTRACTION_AVAILABLE_GATE_OPEN"
            if gate["a4_extraction_available"]
            else "AWAITING_A4_EXTRACTION",
            "requires": ["a4_receipt_independently_valid", "a4_builder_packet_consumed"],
            "a4_receipt_present": gate["a4_receipt_present"],
            "a4_receipt_valid": gate["a4_receipt_valid"],
            "a4_extraction_available": gate["a4_extraction_available"],
            "owner_role": gate["owner_role"],
            "blocked_reason_code": gate["blocked_reason_code"],
        },
        "evidence_enrichment": {
            "enrichment_id": "v4-a5-structural-evidence-enrichment-v1",
            "ledger_opened_by": "A5_evidence_enrichment",
            "ledger_consumed": enrichment["ledger_consumed"],
            "a4_ledger_binding": {
                "row_count": a4_ledger_commitment["row_count"],
                "root_sha256": a4_ledger_commitment["root_sha256"],
            },
            "per_unit_evidence": enrichment["per_unit_evidence"],
            "evidence_commitment_sha256": enrichment["evidence_commitment_sha256"],
            "spans_covered": enrichment["spans_covered"],
            "units_with_evidence": enrichment["units_with_evidence"],
        },
        "a2_residuals_carried_forward": a2_residuals_carried,
        "a4_residuals_carried_forward": a4_residuals_carried,
        "a5_residuals": derive_a5_unit_evidence_residuals(a4_receipt, enrichment["per_unit_evidence"]),
        "execution_counters": {
            "dataset_rows_emitted": 0,
            "new_source_fetches": 0,
            "source_units_enriched": enrichment["units_with_evidence"],
            "spans_covered": enrichment["spans_covered"],
            "ledgers_consumed": 1 if enrichment["ledger_consumed"] else 0,
        },
        "safety_assertions": {
            "rows_not_admitted": True,
            "text_emitted": False,
            "expression_emitted": False,
            "held_out_membership_referenced": False,
            "enrichment_executed_without_a4_extraction": False,
            "mac_corpus_copy_created": False,
            "historical_v3_control_not_used": True,
            "modern_rusyn_not_mapped_to_dialect": True,
            "prebuilder_state_claimed": False,
            "training_ready_silver_claimed": False,
            "later_release_state_claimed": False,
            "epic_done_claimed": False,
            "builder_eligible_ids_present_in_public_diff": False,
        },
    }


# --- receipt verification ---------------------------------------------------


def _load_schema() -> dict[str, Any]:
    schema = _load(A5_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_receipt_schema(receipt: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(_load_schema()).iter_errors(receipt), key=lambda e: list(e.path))
    require(not errors, f"receipt fails schema validation: {errors[0].message}" if errors else "")


def validate_algorithm_metadata(receipt: dict[str, Any]) -> None:
    algorithm = receipt["enrichment_algorithm"]
    declared = {k: algorithm.get(k) for k in ENRICHMENT_ALGORITHM_DESCRIPTOR}
    require(
        declared == ENRICHMENT_ALGORITHM_DESCRIPTOR,
        "receipt enrichment_algorithm does not match the frozen ENRICHMENT_ALGORITHM_DESCRIPTOR -- refusing",
    )
    require(
        algorithm.get("algorithm_descriptor_sha256") == ENRICHMENT_ALGORITHM_DESCRIPTOR_SHA256,
        "receipt algorithm_descriptor_sha256 does not match the locally recomputed frozen descriptor hash -- refusing",
    )


def validate_bindings_hash_to_disk(receipt: dict[str, Any], root: Path) -> None:
    for name, binding in receipt["bindings"].items():
        bound_path = (root / binding["path"]).resolve()
        require(
            root.resolve() in bound_path.parents or bound_path == root.resolve(),
            f"binding {name!r} path escapes the repository root -- refusing: {binding['path']}",
        )
        require(bound_path.is_file(), f"binding {name!r} does not point at a file: {bound_path}")
        actual = sha256_file(bound_path)
        require(
            actual == binding["sha256"],
            f"binding {name!r} on-disk sha256 ({actual}) does not match the receipt's declared "
            f"sha256 ({binding['sha256']}) for {binding['path']} -- refusing",
        )


def validate_gate_matches_receipt(receipt: dict[str, Any], root: Path) -> None:
    gate = check_enrichment_gate(root)
    declared = receipt["enrichment_gate"]
    require(
        declared["a4_receipt_present"] == gate["a4_receipt_present"]
        and declared["a4_receipt_valid"] == gate["a4_receipt_valid"]
        and declared["a4_extraction_available"] == gate["a4_extraction_available"]
        and declared["blocked_reason_code"] == gate["blocked_reason_code"],
        "receipt enrichment_gate does not match the state independently re-derived from the live A4 "
        "receipt -- refusing (re-verify/regenerate required)",
    )

    enrichment = receipt["evidence_enrichment"]
    if gate["a4_extraction_available"]:
        require(
            enrichment["ledger_consumed"] is True,
            "enrichment_gate is open but evidence_enrichment.ledger_consumed is not true -- refusing",
        )
    else:
        require(
            enrichment["ledger_consumed"] is False and enrichment["per_unit_evidence"] == [],
            "enrichment_gate is closed but evidence_enrichment claims a ledger was consumed -- refusing",
        )


def validate_evidence_enrichment_shape(receipt: dict[str, Any]) -> None:
    """Public-only structural verification: internal shape/count consistency
    and the pure ``evidence_commitment_sha256 == sha256(canonical_json(
    per_unit_evidence))`` re-derivation -- both computable with no private
    ledger at all. Never re-derives the aggregate *values* from the real
    ledger; see ``verify_evidence_privately`` for that."""
    a4_receipt = _load(A4_RECEIPT_PATH)
    known_commitments = a4_receipt["builder_packet_consumption"]["unit_commitments"]
    enrichment = receipt["evidence_enrichment"]
    per_unit_evidence = enrichment["per_unit_evidence"]

    require(
        enrichment["a4_ledger_binding"]
        == {
            "row_count": a4_receipt["builder_packet_consumption"]["extraction_ledger_commitment"]["row_count"],
            "root_sha256": a4_receipt["builder_packet_consumption"]["extraction_ledger_commitment"]["root_sha256"],
        },
        "evidence_enrichment.a4_ledger_binding does not match the live A4 receipt's "
        "extraction_ledger_commitment -- refusing",
    )
    require(
        enrichment["evidence_commitment_sha256"] == evidence_commitment_sha256(per_unit_evidence),
        "evidence_enrichment.evidence_commitment_sha256 does not reproduce from per_unit_evidence -- refusing",
    )

    commitments = [entry["source_unit_commitment_sha256"] for entry in per_unit_evidence]
    require(commitments == sorted(commitments), "per_unit_evidence is not sorted by commitment value -- refusing")
    require(len(set(commitments)) == len(commitments), "per_unit_evidence contains duplicate commitments -- refusing")
    require(
        set(commitments) <= set(known_commitments),
        "per_unit_evidence names a commitment outside A4's public unit_commitments -- refusing",
    )

    spans_covered = 0
    units_with_evidence = 0
    for entry in per_unit_evidence:
        span_count = entry["span_count"]
        require(span_count >= 0, "per_unit_evidence span_count is negative -- refusing")
        if span_count == 0:
            require(
                entry["total_span_bytes"] == 0
                and entry["min_span_byte_length"] is None
                and entry["max_span_byte_length"] is None,
                "per_unit_evidence entry has span_count 0 but non-empty byte-length aggregates -- refusing",
            )
        else:
            require(
                entry["min_span_byte_length"] is not None
                and entry["max_span_byte_length"] is not None
                and entry["min_span_byte_length"] <= entry["max_span_byte_length"]
                and entry["total_span_bytes"] >= entry["max_span_byte_length"],
                "per_unit_evidence entry has an internally inconsistent byte-length aggregate -- refusing",
            )
            units_with_evidence += 1
        spans_covered += span_count

    require(
        enrichment["spans_covered"] == spans_covered and enrichment["units_with_evidence"] == units_with_evidence,
        "evidence_enrichment spans_covered/units_with_evidence do not match per_unit_evidence -- refusing",
    )
    if enrichment["ledger_consumed"]:
        require(
            spans_covered == a4_receipt["builder_packet_consumption"]["extraction_ledger_commitment"]["row_count"],
            "evidence_enrichment.spans_covered does not match A4's extraction_ledger_commitment.row_count -- refusing",
        )
    require(
        receipt["execution_counters"]["spans_covered"] == enrichment["spans_covered"]
        and receipt["execution_counters"]["source_units_enriched"] == enrichment["units_with_evidence"]
        and receipt["execution_counters"]["ledgers_consumed"] == (1 if enrichment["ledger_consumed"] else 0),
        "execution_counters does not match evidence_enrichment -- refusing",
    )


def validate_no_forbidden_keys(receipt: dict[str, Any]) -> None:
    def _all_keys(value: Any) -> set[str]:
        if isinstance(value, dict):
            return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
        if isinstance(value, list):
            return set().union(*(_all_keys(item) for item in value), set())
        return set()

    leaked = _all_keys(receipt) & FORBIDDEN_KEYS
    require(not leaked, f"receipt carries forbidden key(s): {sorted(leaked)} -- refusing")

    serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    leaked_substrings = [needle for needle in FORBIDDEN_SUBSTRINGS if needle in serialized]
    require(not leaked_substrings, f"receipt carries forbidden substring(s): {leaked_substrings} -- refusing")


def validate_residuals_carried_from_a2_and_a4(receipt: dict[str, Any]) -> None:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a4_receipt = _load(A4_RECEIPT_PATH)

    expected_a2_ids = {entry["residual_id"] for entry in a2_receipt["residuals"]}
    carried_a2_ids = {entry["residual_id"] for entry in receipt["a2_residuals_carried_forward"]}
    require(carried_a2_ids == expected_a2_ids, "a2_residuals_carried_forward does not reproduce from A2 -- refusing")
    for entry in receipt["a2_residuals_carried_forward"]:
        require(
            entry["origin_stage"] == "A2" and entry["status"] == "unresolved_carried_to_a5",
            "a2_residuals_carried_forward entry has an unexpected origin_stage/status -- refusing",
        )

    expected_a4_ids = {entry["residual_id"] for entry in a4_receipt["a4_residuals"]}
    carried_a4_ids = {entry["residual_id"] for entry in receipt["a4_residuals_carried_forward"]}
    require(carried_a4_ids == expected_a4_ids, "a4_residuals_carried_forward does not reproduce from A4 -- refusing")
    for entry in receipt["a4_residuals_carried_forward"]:
        require(
            entry["origin_stage"] == "A4" and entry["status"] == "unresolved_carried_to_a5",
            "a4_residuals_carried_forward entry has an unexpected origin_stage/status -- refusing",
        )

    expected_a5_residuals = derive_a5_unit_evidence_residuals(
        a4_receipt, receipt["evidence_enrichment"]["per_unit_evidence"]
    )
    require(
        receipt["a5_residuals"] == expected_a5_residuals,
        "a5_residuals does not reproduce from A4's public unit_commitments and this receipt's own "
        "per_unit_evidence -- refusing",
    )


def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    validate_algorithm_metadata(receipt)
    from learn_ukrainian_v4_runtime.provenance import validate_receipt_bindings

    validate_receipt_bindings(receipt, root, validate_bindings_hash_to_disk)
    validate_gate_matches_receipt(receipt, root)
    validate_evidence_enrichment_shape(receipt)
    validate_no_forbidden_keys(receipt)
    validate_residuals_carried_from_a2_and_a4(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=A5_RECEIPT_PATH,
        help="A5 receipt JSON to verify (default: the tracked V4 A5 evidence enrichment receipt).",
    )
    parser.add_argument(
        "--consume",
        action="store_true",
        help=(
            "Stream A4's real private extraction ledger and (re)compute the real per-commitment structural "
            "evidence. Requires the enrichment gate to be open -- fails closed otherwise. Prints the "
            "enrichment summary."
        ),
    )
    parser.add_argument(
        "--a4-private-dir",
        type=Path,
        default=DEFAULT_A4_PRIVATE_DIR,
        help="directory holding A4's own private extraction ledger and manifest (read-only)",
    )
    parser.add_argument(
        "--write-receipt",
        action="store_true",
        help="With --consume, assemble and write the freshly computed receipt to --receipt.",
    )
    parser.add_argument(
        "--verify-private",
        action="store_true",
        help="Additionally re-derive evidence_enrichment cryptographically from a private ledger replay.",
    )
    parser.add_argument(
        "--memory-cap-bytes",
        type=int,
        default=DEFAULT_A5_MEMORY_CAP_BYTES,
        help=(
            "With --consume, the hard resident-memory cap the real streaming pass fails closed against "
            f"(default: {DEFAULT_A5_MEMORY_CAP_BYTES} bytes)."
        ),
    )
    args = parser.parse_args(argv)

    if args.consume:
        gate = check_enrichment_gate()
        require(
            gate["a4_extraction_available"],
            f"enrichment_gate is not open (blocked_reason_code={gate['blocked_reason_code']!r}) -- refusing to consume",
        )
        a4_receipt = _load(A4_RECEIPT_PATH)
        enrichment = compute_evidence_enrichment(a4_receipt, args.a4_private_dir, args.memory_cap_bytes)
        if args.write_receipt:
            receipt = build_receipt(enrichment, gate)
            validate_receipt_independently(receipt)
            args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json(enrichment))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    if args.verify_private:
        a4_receipt = _load(A4_RECEIPT_PATH)
        verify_evidence_privately(receipt, a4_receipt, args.a4_private_dir)
    gate = check_enrichment_gate()
    print(canonical_json({"status": receipt["status"], "enrichment_gate": gate}))


if __name__ == "__main__":
    try:
        main()
    except EnrichmentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
