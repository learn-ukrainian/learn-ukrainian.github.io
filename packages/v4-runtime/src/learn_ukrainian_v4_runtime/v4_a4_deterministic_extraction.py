#!/usr/bin/env python3
"""V4 A4 deterministic extraction: frozen byte-level algorithm (still unexecuted),
real builder-packet consumption, packet-receipt-gated.

A4 is the builder-facing role that turns builder-eligible source units into
immutable, byte-stable, text-free extraction records (span identity +
input/output hashes, never the span text itself). It must never see which
source-family the A3 held-out firewall assigned to the held-out pool -- see
``dataset_v4_a3_heldout_source_family_seal_receipt_v1.json``'s
``access_firewall``, where ``A4_deterministic_extraction`` is locked to
``heldout_family_pool_visible: false`` and forbidden from every held-out
field. This module never opens ``batch_state/open-model-data/v4-a3-heldout/
v4_a3_heldout_membership_v1.json`` (the private membership artifact
A3_heldout owns) -- doing so from a builder-facing role would itself be the
leak this firewall exists to prevent, independent of whether the file
happens to be readable.

The only channel by which A4 may learn *which* source units are
builder-eligible is a **builder packet**: a distinct, A3_heldout-authored,
schema-bound private artifact (``v4_a3_builder_packet_v1.json``, in the same
directory as -- but never the same file as -- the private membership) whose
public commitment receipt (``dataset_v4_a3_builder_packet_receipt_v1.json``)
names the builder-eligible complement's *counts and commitments* and never
the held-out id. A3's own sealed receipt records
``temporal_firewall.builder_packet_issued`` as a permanent, past-tense fact
about the seal event itself (``false`` -- the seal really was completed
before any packet existed, and that never changes); this module therefore
never reads that field to decide whether *a* packet has since been issued
(see ``check_builder_packet_gate``, which reads only the packet's own public
receipt).

This module has four independent parts:

1. ``EXTRACTION_ALGORITHM_DESCRIPTOR`` -- the frozen, hashed, real-corpus
   span-extraction formula. Two implementations of it exist side by side:
   ``segment_sentence_spans`` / ``extract_ledger_rows_for_unit`` /
   ``run_deterministic_extraction`` is the small-scale, whole-bytes-in-memory
   reference implementation (used by tests and cheap dry runs); ``stream_
   sentence_spans`` / ``stream_ledger_rows_for_units`` is the real,
   memory-bounded *production* implementation, proven equivalent to the
   reference one (see the equivalence tests). A prior full in-memory consume
   of the largest admitted table exceeded 5 GiB RSS and had to be killed --
   the production path streams row-by-row (never ``.fetchall()``, never a
   joined blob, never a fully-materialized ledger list) and fails closed via
   ``MemoryBudgetExceeded`` the instant a configured RSS cap (default
   ``DEFAULT_A4_MEMORY_CAP_BYTES``, well under the ~512 MiB this module is
   scoped to prove) would be exceeded. The production default row provider,
   ``admitted_local_row_provider``, delegates to
   ``v4_source_byte_ingestion_admission.iter_admitted_unit_row_texts``,
   which streams ``data/sources.db`` -- read-only, never writes, never
   transmits -- only for the four ``db.*`` units that module's own
   ``dataset_v4_source_byte_ingestion_admission_receipt_v1.json`` admits for
   ``deterministic_local_analysis``. The five ``metadata_only``
   ``historical.*`` units still yield nothing at all (no real byte content
   was ever admitted for them in the first place), and so does any unit for
   which the local store or table is unreachable right now -- in either case
   ``consume_builder_packet`` skips it silently, and
   ``derive_source_unit_extraction_residuals`` (below) independently
   explains why. The real hash-only ledger rows -- keyed by the same
   per-unit HMAC commitment used in ``builder_packet_consumption``, never a
   plaintext ``source_unit_id`` -- are written to a **private**, gitignored,
   mode-0600 JSONL file under ``batch_state/`` (see
   ``materialize_streaming_ledger``); the public receipt's
   ``extraction_ledger_commitment`` carries only a row count and a
   root/rolling commitment over that private ledger, never the rows
   themselves -- a real admitted table can hold millions of spans, and
   nothing at that scale is ever committed to git. A generic local corpus
   database containing rows for a source unit is not by itself this
   V4-scoped ingestion admission -- only ``v4_source_byte_ingestion_
   admission``'s own frozen, receipt-bound ``ADMITTED_SOURCE_UNIT_IDS`` is.
   Frozen the same way A3 froze its assignment formula: any edit changes
   ``EXTRACTION_ALGORITHM_DESCRIPTOR_SHA256``, pinned as a schema ``const``.
2. ``UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR`` -- a second, distinct, also
   frozen and hashed algorithm that *does* run today: a content-blind,
   HMAC-keyed commitment over the real (private) builder-eligible
   ``source_unit_id`` set A4 learns from the packet. This is genuine,
   reproducible, immutable extraction-adjacent work over real private data
   -- but it is never described as satisfying
   ``EXTRACTION_ALGORITHM_DESCRIPTOR``'s ``sha256(raw_span_bytes_utf8)``
   formula, because it does not touch span bytes at all. Keeping the two
   algorithms distinct (separate ids, separate frozen hashes, separate
   receipt sections) means neither can be silently substituted for the
   other while still validating.
3. ``LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR`` -- a third, distinct, frozen
   and hashed algorithm: the content-blind rolling hash chain that folds the
   real (private) extraction ledger's per-row ``output_sha256`` values into
   the single public ``root_sha256`` the receipt carries. See
   ``new_ledger_rolling_state`` / ``ledger_rolling_update`` /
   ``materialize_streaming_ledger``.
4. ``check_builder_packet_gate`` -- independently re-derives the current
   gate state from the bound A3 seal receipt *and* the bound A3 builder
   packet receipt on disk (both public, never trusting the A4 receipt's own
   declared fields, never opening any private artifact).

Run with no arguments to verify the checked-in A4 receipt reproduces all
four parts and is consistent with the bound A2/A3 receipts on disk -- using
only public artifacts, so this passes in a fresh checkout with no
``batch_state/``. Pass ``--consume`` (only meaningful where the private
builder packet actually exists) to open it for real, independently verify
it against the public seal receipt's family registry, (re)compute the real
unit commitments, and stream the real extraction ledger to a private file
under a hard memory cap (``--memory-cap-bytes``); add ``--write-receipt`` to
persist a freshly assembled public receipt. Pass ``--verify-private`` to
additionally re-derive the checked-in receipt's ``builder_packet_
consumption`` commitments cryptographically from the private packet, the
private A4 salt artifact, and a full streaming replay of the private
extraction ledger.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import hmac
import json
import os
import re
import secrets
import stat
import sys
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from learn_ukrainian_v4_runtime.provenance import validation_session
from learn_ukrainian_v4_runtime.resources import resource_root

try:
    import resource
except ImportError:  # pragma: no cover - resource is POSIX-only; this project targets Linux
    resource = None  # type: ignore[assignment]

_SELF_ROOT = resource_root()

from learn_ukrainian_v4_runtime import v4_a3_builder_packet as packet
from learn_ukrainian_v4_runtime import v4_a3_heldout_family_assignment as heldout
from learn_ukrainian_v4_runtime import v4_source_byte_ingestion_admission as byte_ingestion

ROOT = heldout.ROOT
PRIMARY_ROOT = heldout.PRIMARY_ROOT
PRIVATE_ROOT = heldout.PRIVATE_ROOT

ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A4_SCHEMA_PATH = CONTRACTS / "dataset_v4_a4_deterministic_extraction_receipt_v1.schema.json"
A3_SEAL_RECEIPT_PATH = ADMISSION / "dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
A3_PACKET_RECEIPT_PATH = ADMISSION / "dataset_v4_a3_builder_packet_receipt_v1.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
BYTE_INGESTION_RECEIPT_PATH = ADMISSION / "dataset_v4_source_byte_ingestion_admission_receipt_v1.json"

# The packet A3 issued *to A4* -- distinct from, and stored alongside, the
# private membership file A4 must never open. Same directory (both owned by
# A3_heldout, both under the primary checkout's batch_state/), different
# filename.
DEFAULT_PRIVATE_PACKET_DIR = heldout.DEFAULT_PRIVATE_DIR
# A4's own private artifact directory: the salt behind the unit-commitment
# HMAC. Never shared with, and cryptographically independent of, A3's salt
# (which A4 cannot read: it lives only in the membership file).
DEFAULT_A4_PRIVATE_DIR = PRIVATE_ROOT / "open-model-data/v4-a4-extraction"
A4_SALT_FILENAME = "v4_a4_unit_commitment_salt_v1.json"
A4_SALT_REQUIRED_FIELDS = frozenset({"algorithm_id", "algorithm_version", "salt_hex", "receipt_binding_sha256"})

# The private, gitignored, hash-only extraction ledger and its small public-
# shaped manifest -- both live under the same per-run A4 private directory as
# the salt above, both mode 0600 (see heldout.PRIVATE_FILE_MODE). The ledger
# itself (one JSON line per span, never the span text) can hold millions of
# rows for a real admitted table; the manifest is the one small (counts +
# root commitment) file a rerun reads to verify-and-skip instead of
# re-streaming the whole table again. Neither is ever committed to git --
# see docs/best-practices/git-hygiene.md and this project's own
# .gitignore for batch_state/.
A4_LEDGER_FILENAME = "v4_a4_extraction_ledger_v1.jsonl"
A4_LEDGER_MANIFEST_FILENAME = "v4_a4_extraction_ledger_manifest_v1.json"
A4_LEDGER_MANIFEST_REQUIRED_FIELDS = frozenset(
    {
        "algorithm_id",
        "algorithm_version",
        "row_count",
        "root_sha256",
        "source_units_extracted",
        "receipt_binding_sha256",
    }
)

# Hard cap on resident memory during a real streaming consume, well under the
# ~512 MiB target this module is scoped to prove -- see MemoryBudgetExceeded
# and _require_within_memory_budget below. A prior full in-memory consume of
# the largest admitted table exceeded 5 GiB RSS and had to be killed; this
# cap exists so the same mistake fails closed instead of paging the host to
# death.
DEFAULT_A4_MEMORY_CAP_BYTES = 512 * 1024 * 1024
_MEMORY_CHECK_INTERVAL_SPANS = 2_000

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

# Fields no builder-facing artifact -- including this one -- may ever carry.
# Mirrors the A3 seal's own forbidden-field set plus the generic text/label
# leak surface every A-stage receipt in this project screens for.
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


class ExtractionError(ValueError):
    """Extraction cannot proceed safely, or a receipt/binding failed to verify."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExtractionError(message)


canonical_json = heldout.canonical_json


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    from learn_ukrainian_v4_runtime.provenance import binding_sha256

    return binding_sha256(path)


# --- frozen byte-level extraction algorithm (real code, real corpus not yet
# --- reachable) --------------------------------------------------------------
#
# Runnable today (see ``segment_sentence_spans`` / ``extract_ledger_rows_
# for_unit`` / ``run_deterministic_extraction`` below) but not yet exercised
# against any real source unit -- see the module docstring and the
# a4-residual carried in a4_residuals. Frozen and hashed now so that the
# moment byte-addressable, rights-clear source content exists for the
# builder-eligible complement, extraction runs against a formula that was
# fixed before any builder-eligible unit was known -- not tuned post hoc.
#
# Every identity field is keyed by ``source_unit_commitment_sha256`` -- the
# same per-unit HMAC commitment ``builder_packet_consumption.unit_
# commitments`` already publishes -- never the plaintext ``source_unit_id``.
# ``source_unit_id`` is only ever an *input* to that commitment's HMAC (see
# ``unit_commitment_sha256`` below); it is never itself a field of any
# public ledger row.

EXTRACTION_ALGORITHM_DESCRIPTOR: dict[str, Any] = {
    "algorithm_id": "v4-a4-deterministic-span-extraction-v1",
    "algorithm_version": "v1",
    "unit_of_extraction": "sentence_span",
    "content_blind": False,
    "ordering": "source_unit_commitment_sha256_ascending_then_span_index_ascending",
    "segmentation_rule": (
        "text = raw_unit_bytes.decode('utf-8'); spans = re.split(r'(?<=[.!?…])\\s+', text); "
        "spans = [span.strip() for span in spans if span.strip()]; span_index assigned in list "
        "order starting at 0"
    ),
    "input_hash_formula": "sha256(raw_span_bytes_utf8)",
    "output_hash_formula": (
        "sha256(canonical_json({source_unit_commitment_sha256, span_index, span_byte_length, "
        "input_sha256, extraction_algorithm_id, extraction_algorithm_version}))"
    ),
    "text_emitted": False,
    "reproducibility": "byte_stable_given_identical_source_unit_bytes_and_frozen_segmentation_rule",
}

EXTRACTION_ALGORITHM_DESCRIPTOR_SHA256 = sha256_text(canonical_json(EXTRACTION_ALGORITHM_DESCRIPTOR))

_SENTENCE_SPAN_BOUNDARY = re.compile(r"(?<=[.!?…])\s+")


def extraction_record_output_hash(
    source_unit_commitment_sha256: str, span_index: int, span_byte_length: int, input_sha256: str
) -> str:
    """Pure function implementing ``output_hash_formula`` above. Never touches
    span text -- only the record's own identity fields (keyed by the unit's
    HMAC commitment, never its plaintext id) and the already-hashed
    ``input_sha256`` are covered."""
    record = {
        "source_unit_commitment_sha256": source_unit_commitment_sha256,
        "span_index": span_index,
        "span_byte_length": span_byte_length,
        "input_sha256": input_sha256,
        "extraction_algorithm_id": EXTRACTION_ALGORITHM_DESCRIPTOR["algorithm_id"],
        "extraction_algorithm_version": EXTRACTION_ALGORITHM_DESCRIPTOR["algorithm_version"],
    }
    return sha256_text(canonical_json(record))


def segment_sentence_spans(raw_unit_bytes: bytes) -> list[str]:
    """Pure, frozen segmentation matching ``segmentation_rule`` above: UTF-8
    decode, split on the sentence-boundary regex, strip, drop empties.
    Returns span *text* -- callers must hash it immediately and never persist
    or print the return value; see ``extract_ledger_rows_for_unit``, the only
    caller in this module."""
    text = raw_unit_bytes.decode("utf-8")
    return [span.strip() for span in _SENTENCE_SPAN_BOUNDARY.split(text) if span.strip()]


def stream_sentence_spans(row_texts: Iterable[str]) -> Iterator[str]:
    """Streaming-equivalent of ``segment_sentence_spans("\\n\\n".join(row_texts)
    .encode("utf-8"))`` -- byte-identical output, without ever holding the
    full joined text (or the full row list) in memory: only a single,
    still-growing trailing fragment is carried from one row to the next.

    This is the standard incremental-regex-split technique and is exact
    (not an approximation) for this pattern: ``re.split`` scans left to
    right, and any match already *closed* by a following non-whitespace
    character already present in the buffer can never be reopened by
    appending more text -- only the single trailing (possibly still
    mid-match, possibly just unterminated) fragment can change as more text
    arrives. So after each row is appended, every split piece except the
    last is guaranteed final and is yielded immediately (stripped, empties
    dropped, matching ``segment_sentence_spans``'s own filtering); the last
    piece becomes the new pending fragment. See
    ``test_stream_sentence_spans_matches_segment_sentence_spans_for_joined_rows``
    for the equivalence proof against the frozen reference implementation.
    """
    pending = ""
    started = False
    for row_text in row_texts:
        pending = f"{pending}\n\n{row_text}" if started else row_text
        started = True
        parts = _SENTENCE_SPAN_BOUNDARY.split(pending)
        for part in parts[:-1]:
            stripped = part.strip()
            if stripped:
                yield stripped
        pending = parts[-1]
    if started:
        stripped = pending.strip()
        if stripped:
            yield stripped


def extract_ledger_rows_for_unit(raw_unit_bytes: bytes, source_unit_commitment_sha256: str) -> list[dict[str, Any]]:
    """Run the frozen extraction formula against one unit's real bytes, keyed
    by that unit's already-computed (HMAC, private-salted) commitment --
    never its plaintext ``source_unit_id``. Returns hash-only rows; each
    span's text is discarded the instant its hash is taken and never appears
    in the return value."""
    rows: list[dict[str, Any]] = []
    for span_index, span in enumerate(segment_sentence_spans(raw_unit_bytes)):
        span_bytes = span.encode("utf-8")
        input_sha256 = hashlib.sha256(span_bytes).hexdigest()
        span_byte_length = len(span_bytes)
        rows.append(
            {
                "source_unit_commitment_sha256": source_unit_commitment_sha256,
                "span_index": span_index,
                "span_byte_length": span_byte_length,
                "input_sha256": input_sha256,
                "output_sha256": extraction_record_output_hash(
                    source_unit_commitment_sha256, span_index, span_byte_length, input_sha256
                ),
            }
        )
    return rows


def no_v4_byte_ingestion_admission(source_unit_id: str) -> bytes | None:
    """Legacy no-op ``byte_provider``: always returns ``None``, for any
    source unit. Kept for callers/tests that want the pre-admission
    behaviour explicitly; no longer the production default -- see
    ``admitted_local_byte_provider``, wired below now that a real,
    rights-chain-verified V4-scoped byte ingestion admission exists for the
    four ``db.*`` units (``v4_source_byte_ingestion_admission``)."""
    return None


def admitted_local_byte_provider(source_unit_id: str) -> bytes | None:
    """Small-scale/synthetic ``byte_provider`` for ``run_deterministic_
    extraction`` below: delegates to ``v4_source_byte_ingestion_admission.
    provide_bytes_for_admitted_unit``, which ``.fetchall()``'s the admitted
    rows into one in-memory blob. Fine for tests and dry runs against a
    handful of rows; never the production default for a real admitted
    table -- see ``admitted_local_row_provider`` below, which streams
    instead."""
    return byte_ingestion.provide_bytes_for_admitted_unit(source_unit_id)


class MemoryBudgetExceeded(ExtractionError):
    """A streaming extraction pass would exceed its configured resident-
    memory cap. Raised, never silently ignored -- the caller must treat this
    as a hard stop: whatever the private ledger writer has already flushed
    to its temp file is discarded (never linked into place; see
    ``heldout.write_new_private_streamed_artifact``), so a run that fails
    this way leaves no partial private ledger and no receipt claiming a
    consumption that never finished."""


def _current_rss_bytes() -> int:
    """Current process resident set size, in bytes, via ``getrusage``'s
    high-water mark (``ru_maxrss``) -- a value that only ever grows within a
    process, which is exactly what a hard memory *cap* wants to catch: once
    it has crossed the cap, no later measurement can un-cross it. Returns
    ``0`` (never raises) on a platform where the ``resource`` module is
    unavailable (Windows) -- this project targets Linux, where ``ru_maxrss``
    is kibibytes; macOS/BSD report bytes instead, handled by ``sys.
    platform`` below."""
    if resource is None:  # pragma: no cover - POSIX-only module, see import above
        return 0
    ru_maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return ru_maxrss if sys.platform == "darwin" else ru_maxrss * 1024


def _require_within_memory_budget(memory_cap_bytes: int) -> None:
    rss_bytes = _current_rss_bytes()
    if rss_bytes > memory_cap_bytes:
        raise MemoryBudgetExceeded(
            f"streaming extraction aborted: resident memory {rss_bytes} bytes exceeded the configured "
            f"cap of {memory_cap_bytes} bytes -- failing closed rather than risk exhausting host memory "
            "(see the 5 GiB RSS full in-memory consume this module exists to never repeat)"
        )


def no_v4_row_provider(source_unit_id: str) -> Iterator[str]:
    """Streaming counterpart to ``no_v4_byte_ingestion_admission``: an
    immediately-exhausted generator (yields nothing) for any source unit.
    Kept for callers/tests that want the pre-admission behaviour explicitly,
    and wired by ``--no-real-bytes`` for a cheap dry-run consumption that
    never opens ``data/sources.db`` at all."""
    return iter(())


def admitted_local_row_provider(source_unit_id: str) -> Iterator[str]:
    """Production default ``row_provider`` for the real streaming consume:
    delegates to ``v4_source_byte_ingestion_admission.
    iter_admitted_unit_row_texts``, which streams one admitted row's text at
    a time via lazy SQLite cursor iteration -- never ``.fetchall()``, never
    a joined blob, never more than one row's text resident at once. Yields
    nothing at all for any unit outside that module's own frozen
    ``ADMITTED_SOURCE_UNIT_IDS``, exactly mirroring ``admitted_local_byte_
    provider``'s ``None`` for the same units. This function itself never
    reads a row of text; it only ever forwards to the one module admitted
    to do that."""
    yield from byte_ingestion.iter_admitted_unit_row_texts(source_unit_id)


def run_deterministic_extraction(
    source_unit_ids: list[str],
    salt: bytes,
    byte_provider: Callable[[str], bytes | None] = admitted_local_byte_provider,
) -> list[dict[str, Any]]:
    """For each builder-eligible unit, ask ``byte_provider`` for its real
    bytes; skip (silently -- the typed residual already explains why,
    independently) any unit for which it returns ``None``. Never receives or
    handles anything but already-open, already-rights-checked bytes -- rights
    gating happens upstream, in whatever real ``byte_provider`` a future
    change wires in. Rows are ordered by (commitment, span_index) ascending,
    matching ``EXTRACTION_ALGORITHM_DESCRIPTOR["ordering"]`` -- never by
    ``source_unit_id``, so publishing this list never leaks the units'
    original order either."""
    rows: list[dict[str, Any]] = []
    for unit_id in source_unit_ids:
        raw_bytes = byte_provider(unit_id)
        if raw_bytes is None:
            continue
        commitment = unit_commitment_sha256(salt, unit_id)
        rows.extend(extract_ledger_rows_for_unit(raw_bytes, commitment))
    rows.sort(key=lambda row: (row["source_unit_commitment_sha256"], row["span_index"]))
    return rows


def stream_ledger_rows_for_units(
    commitment_and_unit_ids: list[tuple[str, str]],
    row_provider: Callable[[str], Iterator[str]],
    *,
    memory_cap_bytes: int = DEFAULT_A4_MEMORY_CAP_BYTES,
    memory_check_interval: int = _MEMORY_CHECK_INTERVAL_SPANS,
) -> Iterator[dict[str, Any]]:
    """The real, memory-bounded production extraction pass: streams
    hash-only ledger rows for the given units, one span at a time, in the
    frozen ordering (``EXTRACTION_ALGORITHM_DESCRIPTOR["ordering"]``:
    commitment ascending, span_index ascending within a unit) -- without a
    final sort step, because callers already pass ``commitment_and_unit_ids``
    pre-sorted by commitment (commitments are cheap HMACs over ids, computed
    up front, independent of any unit's byte content) and each unit's own
    spans stream out in increasing span_index by construction (see
    ``stream_sentence_spans``).

    Never materializes the ledger itself: this is a generator, and each row
    is discarded by this function the instant it is yielded. Checks resident
    memory every ``memory_check_interval`` spans and fails closed
    (``MemoryBudgetExceeded``) the moment the configured cap is exceeded --
    callers must have already persisted whatever was yielded before that
    point (e.g. to a private ledger file), since nothing here buffers it for
    them. A unit for which ``row_provider`` yields no rows at all
    contributes zero spans and is silently skipped, exactly as
    ``run_deterministic_extraction`` skips a unit whose ``byte_provider``
    returns ``None``."""
    spans_seen = 0
    for commitment, unit_id in commitment_and_unit_ids:
        for span_index, span in enumerate(stream_sentence_spans(row_provider(unit_id))):
            span_bytes = span.encode("utf-8")
            input_sha256 = hashlib.sha256(span_bytes).hexdigest()
            span_byte_length = len(span_bytes)
            yield {
                "source_unit_commitment_sha256": commitment,
                "span_index": span_index,
                "span_byte_length": span_byte_length,
                "input_sha256": input_sha256,
                "output_sha256": extraction_record_output_hash(commitment, span_index, span_byte_length, input_sha256),
            }
            spans_seen += 1
            if spans_seen % memory_check_interval == 0:
                _require_within_memory_budget(memory_cap_bytes)
    _require_within_memory_budget(memory_cap_bytes)


# --- frozen unit-commitment algorithm (real, content-blind, runs today) ----
#
# Distinct from EXTRACTION_ALGORITHM_DESCRIPTOR above: this never touches
# span bytes, only the real (private) builder-eligible source_unit_id
# strings A4 learns from the packet. HMAC-keyed (never a plain hash) for the
# same reason A3's own commitments are keyed: with a small, fully public
# family_id/source_unit_id registry, an unsalted sha256(id) is enumerable --
# hash every one of the (currently 9) known ids and match. Keying on a
# private salt A4 generates and keeps for itself (never A3's salt, which A4
# cannot read) closes that off.

UNIT_COMMITMENT_DOMAIN = b"v4-a4-builder-eligible-unit-commitment-v1"
UNIT_COMMITMENT_ROOT_DOMAIN = b"v4-a4-builder-eligible-unit-commitment-root-v1"

UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR: dict[str, Any] = {
    "algorithm_id": "v4-a4-unit-commitment-hmac-sha256-v1",
    "algorithm_version": "v1",
    "identity_dimensions": ["source_unit_id"],
    "content_blind": True,
    "formula": (
        "unit_commitment_sha256(id) = hmac_sha256(key=private_a4_salt, "
        "msg=UNIT_COMMITMENT_DOMAIN + 0x00 + canonical_json({source_unit_id: id})); "
        "consumed_units_commitment_sha256(ids) = hmac_sha256(key=private_a4_salt, "
        "msg=UNIT_COMMITMENT_ROOT_DOMAIN + 0x00 + canonical_json({source_unit_ids: sorted(ids), "
        "count: len(ids)}))"
    ),
    "text_emitted": False,
    "reproducibility": "byte_stable_given_the_same_private_a4_salt_and_the_same_builder_eligible_source_unit_id_set",
}

UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR_SHA256 = sha256_text(canonical_json(UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR))


def unit_commitment_sha256(salt: bytes, source_unit_id: str) -> str:
    message = UNIT_COMMITMENT_DOMAIN + b"\x00" + canonical_json({"source_unit_id": source_unit_id}).encode("utf-8")
    return hmac.new(salt, message, hashlib.sha256).hexdigest()


def root_commitment_sha256(salt: bytes, source_unit_ids: list[str]) -> str:
    ordered = sorted(source_unit_ids)
    message = (
        UNIT_COMMITMENT_ROOT_DOMAIN
        + b"\x00"
        + canonical_json({"source_unit_ids": ordered, "count": len(ordered)}).encode("utf-8")
    )
    return hmac.new(salt, message, hashlib.sha256).hexdigest()


def builder_eligible_unit_commitments(salt: bytes, source_unit_ids: list[str]) -> list[str]:
    """Sorted by *commitment value*, not by source_unit_id -- so publishing
    this array never leaks the original ids' sort order either."""
    return sorted(unit_commitment_sha256(salt, unit_id) for unit_id in source_unit_ids)


# --- extraction-ledger rolling commitment (real, content-blind, runs today) -
#
# The one piece a real streaming consume against a large admitted table
# still needs a public-safe answer for: extraction_ledger can no longer be a
# literal public array (a real table can yield millions of rows -- see the
# module docstring's ~3.8M-span figure and the 5 GiB RSS a full in-memory
# consume once cost). This is a plain hash *chain* (not a Merkle tree): a
# running SHA-256 state, folded one row at a time over each row's own
# already-computed output_sha256, in the exact ledger order
# EXTRACTION_ALGORITHM_DESCRIPTOR["ordering"] already fixes. That makes it
# computable incrementally while streaming (see stream_ledger_rows_for_units
# / materialize_streaming_ledger below) and independently reproducible later
# by anyone holding the private ledger, without ever needing the ledger
# itself to be public. Unkeyed (plain SHA-256, not HMAC) -- unlike the unit
# commitment above, there is no small public candidate set to enumerate
# against a bare row-hash chain, so a private salt buys no real
# confidentiality here.

LEDGER_COMMITMENT_DOMAIN = b"v4-a4-extraction-ledger-rolling-commitment-v1"

LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR: dict[str, Any] = {
    "algorithm_id": "v4-a4-extraction-ledger-rolling-commitment-sha256-v1",
    "algorithm_version": "v1",
    "content_blind": True,
    "formula": (
        "state_0 = sha256(LEDGER_COMMITMENT_DOMAIN + 0x00).digest(); "
        "for each row in extraction_ledger order (source_unit_commitment_sha256 ascending, then "
        "span_index ascending): state_i = sha256(state_(i-1) + 0x00 + row.output_sha256.encode('ascii'))"
        ".digest(); root_sha256 = state_n.hexdigest() after all rows (root of an empty ledger is "
        "sha256(LEDGER_COMMITMENT_DOMAIN + 0x00).hexdigest())"
    ),
    "text_emitted": False,
    "reproducibility": "byte_stable_given_the_identical_ordered_sequence_of_row_output_hashes",
}

LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR_SHA256 = sha256_text(canonical_json(LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR))


def new_ledger_rolling_state() -> bytes:
    return hashlib.sha256(LEDGER_COMMITMENT_DOMAIN + b"\x00").digest()


def ledger_rolling_update(state: bytes, output_sha256_hex: str) -> bytes:
    return hashlib.sha256(state + b"\x00" + output_sha256_hex.encode("ascii")).digest()


EMPTY_LEDGER_ROOT_SHA256 = new_ledger_rolling_state().hex()


def ledger_rolling_commitment_sha256(rows: Iterable[dict[str, Any]]) -> str:
    """Pure, replay-based reference implementation: folds an already-materialized
    (or freshly streamed) sequence of rows into the same rolling state
    ``materialize_streaming_ledger`` computes incrementally while writing.
    Used by ``--verify-private`` to recompute the commitment by replaying the
    real private ledger file -- never by ordinary (public-only) receipt
    verification, which has no ledger to replay."""
    state = new_ledger_rolling_state()
    for row in rows:
        state = ledger_rolling_update(state, row["output_sha256"])
    return state.hex()


# --- private-artifact filesystem hardening, self-contained -----------------
#
# A4 could reuse ``heldout.write_new_private_json_artifact``'s directory-fd/
# symlink-safety discipline by adding a streamed sibling to it in
# ``v4_a3_heldout_family_assignment.py`` -- but that module's own file bytes
# are load-bearing: its SHA-256 is a ``bindings.assignment_algorithm_
# implementation`` entry inside the *already-sealed* A3 receipt, and that
# receipt's ``bindings`` block is itself covered by ``receipt_binding_
# sha256`` (see that module's ``receipt_binding_context``), which the real
# private builder packet and every downstream A4 private artifact are bound
# to. Editing that file at all -- even to add an unrelated, algorithm-
# independent generic helper -- would force re-sealing/re-issuing the whole
# already-completed A3 chain. So A4 keeps its own private-artifact
# filesystem hardening fully self-contained instead: the same create-only,
# symlink-safe, single-directory-fd, fsync'd-to-disk discipline as
# ``heldout.write_new_private_json_artifact``/``load_private_artifact``,
# reimplemented here rather than shared, specifically so this module's own
# (already-necessarily-changing) file hash never has to drag A3's sealed
# receipt chain along with it.


def _assert_no_symlink_components(path: Path) -> None:
    """Refuse if any component of an absolute path (leaf included) is a
    symlink."""
    require(path.is_absolute(), f"path must be absolute: {path}")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode), f"refusing symlink path component: {current}")


def _assert_contained(candidate: Path, base: Path) -> None:
    """Refuse a resolved path that escapes the intended base directory (traversal)."""
    resolved_candidate = candidate.resolve()
    resolved_base = base.resolve()
    require(
        resolved_candidate == resolved_base or resolved_base in resolved_candidate.parents,
        f"refusing path escaping private directory {resolved_base}: {candidate}",
    )


def _open_directory_no_symlink(path: Path) -> int:
    """Open ``path`` as a directory file descriptor, refusing a symlinked
    leaf. Every subsequent operation is anchored to this fd, closing the
    check-then-act race a pathname-based re-open would leave open. Caller
    closes the returned fd."""
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    return os.open(path, flags)


def write_new_private_streamed_artifact(path: Path, chunks: Iterable[bytes]) -> None:
    """Atomically *create* a private artifact at ``path`` from an iterable of
    raw byte chunks, writing each one to the temp file as it is produced --
    never buffering the whole payload as a single in-memory blob first. Same
    create-only, symlink-safe, single-directory-fd, fsync'd-to-disk
    discipline as ``heldout.write_new_private_json_artifact``, for a
    streamed payload (e.g. one JSON line per ledger row) instead of one
    ``canonical_json(payload)`` blob. An exception raised while iterating
    ``chunks`` (e.g. ``MemoryBudgetExceeded``) propagates out of this
    function with the destination path left untouched -- the temp file is
    unlinked, never linked into place."""
    private_dir = path.parent
    _assert_no_symlink_components(private_dir)
    private_dir.mkdir(parents=True, exist_ok=True, mode=heldout.PRIVATE_DIR_MODE)
    os.chmod(private_dir, heldout.PRIVATE_DIR_MODE)
    _assert_no_symlink_components(path)
    _assert_contained(path, private_dir)

    dir_fd = _open_directory_no_symlink(private_dir)
    try:
        try:
            os.stat(path.name, dir_fd=dir_fd, follow_symlinks=False)
            already_exists = True
        except FileNotFoundError:
            already_exists = False
        require(not already_exists, f"private artifact already exists, refusing to overwrite: {path}")

        temporary_name = f".{path.name}.{secrets.token_hex(8)}.tmp"
        descriptor = os.open(
            temporary_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, heldout.PRIVATE_FILE_MODE, dir_fd=dir_fd
        )
        try:
            with os.fdopen(descriptor, "wb") as handle:
                os.fchmod(handle.fileno(), heldout.PRIVATE_FILE_MODE)
                for chunk in chunks:
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary_name, path.name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
            except FileExistsError:
                raise ExtractionError(f"private artifact already exists, refusing to overwrite: {path}") from None
            os.fsync(dir_fd)
        finally:
            with contextlib.suppress(OSError):
                os.unlink(temporary_name, dir_fd=dir_fd)
    finally:
        os.close(dir_fd)


def iter_private_artifact_lines(path: Path) -> Iterator[str]:
    """Stream a private artifact's lines one at a time, with the same
    symlink-safe, regular-file, owner-only-mode checks ``heldout.
    load_private_artifact`` runs -- but never ``.read()``'s the whole file
    into memory first. Verify-only; used only by the explicit, operator-
    invoked ``--verify-private`` replay check, never by ordinary
    (public-only) receipt validation."""
    _assert_no_symlink_components(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        raise ExtractionError(f"private artifact missing: {path}") from None
    except OSError as exc:
        raise ExtractionError(f"private artifact is not a regular file: {path}") from exc

    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        require(stat.S_ISREG(info.st_mode), f"private artifact is not a regular file: {path}")
        require(
            stat.S_IMODE(info.st_mode) == heldout.PRIVATE_FILE_MODE,
            f"private artifact has unexpected mode (want {oct(heldout.PRIVATE_FILE_MODE)}): {path}",
        )
        for raw_line in handle:
            yield raw_line.decode("utf-8")


def materialize_streaming_ledger(rows: Iterator[dict[str, Any]], ledger_path: Path) -> dict[str, Any]:
    """Consume a ledger-row stream exactly once: write each row as one JSON
    line to a private, create-only, symlink-safe file (``write_new_private_
    streamed_artifact`` above) while incrementally folding it into the
    rolling commitment -- never holding more than one row in memory at a
    time, and never reading the file back to compute the commitment.

    If ``rows`` raises partway through (e.g. ``MemoryBudgetExceeded``), the
    exception propagates out of the inner generator and out of
    ``write_new_private_streamed_artifact`` in turn; that function's own
    create-then-link discipline means the destination ``ledger_path`` is
    never created in that case -- only a temp file, which it unlinks -- so a
    failed streaming pass never leaves a partial private ledger behind."""
    state = new_ledger_rolling_state()
    row_count = 0
    distinct_units: set[str] = set()

    def _line_chunks() -> Iterator[bytes]:
        nonlocal state, row_count
        for row in rows:
            distinct_units.add(row["source_unit_commitment_sha256"])
            state = ledger_rolling_update(state, row["output_sha256"])
            row_count += 1
            yield (canonical_json(row) + "\n").encode("utf-8")

    write_new_private_streamed_artifact(ledger_path, _line_chunks())
    return {
        "row_count": row_count,
        "root_sha256": state.hex(),
        "source_units_extracted": len(distinct_units),
    }


# --- builder-packet gate (public-only) --------------------------------------


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check_builder_packet_gate(root: Path = ROOT) -> dict[str, Any]:
    """Independently re-derive the current gate state from the bound A3 seal
    receipt *and* the bound A3 builder packet receipt on disk -- both
    public, git-tracked artifacts. Never trusts anything the A4 receipt
    itself declares, and never opens ``batch_state/`` (the private packet or
    the private membership file A3_heldout owns).

    Deliberately does not consult the sealed A3 receipt's own
    ``temporal_firewall.builder_packet_issued`` -- that field is a
    permanent, past-tense fact about the *seal event itself* (the seal
    really was completed before any packet existed, and stays ``false``
    forever). Whether a packet has since been issued is answered by the
    packet's own, later, distinct public receipt.
    """
    a3_seal_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
    ).resolve()
    require(root.resolve() in a3_seal_path.parents, "A3 seal receipt path escapes the repository root -- refusing")
    require(
        a3_seal_path.is_file(),
        f"A3 held-out seal receipt is missing, cannot evaluate the builder-packet gate: {a3_seal_path}",
    )

    a3_seal = _load(a3_seal_path)
    require(
        a3_seal.get("controlling_outcome_sha256") == V4_SHA256,
        "A3 seal receipt is not bound to the expected V4 controlling outcome -- refusing",
    )
    seal = a3_seal.get("heldout_partition_seal", {})
    a3_seal_complete = bool(seal.get("heldout_membership_assigned_privately")) and not bool(
        seal.get("heldout_membership_included")
    )

    a3_packet_receipt_path = (
        root / "data/projects/open_model_data/admission/dataset_v4_a3_builder_packet_receipt_v1.json"
    ).resolve()
    require(
        root.resolve() in a3_packet_receipt_path.parents,
        "A3 builder packet receipt path escapes the repository root -- refusing",
    )

    if not a3_packet_receipt_path.is_file():
        return {
            "gate_id": "v4-a4-builder-packet-gate-v1",
            "a3_seal_complete": a3_seal_complete,
            "builder_packet_issued": False,
            "builder_eligible_source_unit_ids_known_to_a4": False,
            "packet_receipt_binding_verified": False,
            "gate_open": False,
            "owner_role": "A3_heldout",
            "blocked_reason_code": "builder_packet_not_issued",
        }

    packet_receipt = _load(a3_packet_receipt_path)
    packet.validate_receipt_schema(packet_receipt)
    require(
        packet_receipt.get("controlling_outcome_sha256") == V4_SHA256,
        "A3 builder packet receipt is not bound to the expected V4 controlling outcome -- refusing",
    )
    actual_seal_sha256 = sha256_file(a3_seal_path)
    require(
        packet_receipt["seal_receipt_binding"]["sha256"] == actual_seal_sha256,
        "A3 builder packet receipt's seal_receipt_binding.sha256 does not match the live on-disk A3 seal "
        "receipt -- refusing (packet was issued against a different seal, or the seal has since drifted)",
    )

    temporal = packet_receipt["temporal_firewall_packet"]
    counters = packet_receipt["execution_counters"]
    builder_packet_issued = bool(temporal["builder_packet_issued"]) and counters["builder_packets_issued"] > 0
    gate_open = a3_seal_complete and builder_packet_issued

    return {
        "gate_id": "v4-a4-builder-packet-gate-v1",
        "a3_seal_complete": a3_seal_complete,
        "builder_packet_issued": builder_packet_issued,
        "builder_eligible_source_unit_ids_known_to_a4": gate_open,
        "packet_receipt_binding_verified": True,
        "gate_open": gate_open,
        "owner_role": "A3_heldout",
        "blocked_reason_code": None if gate_open else "builder_packet_not_issued",
    }


# --- real builder-packet consumption ----------------------------------------


def consume_builder_packet(
    seal_receipt_path: Path = A3_SEAL_RECEIPT_PATH,
    packet_dir: Path = DEFAULT_PRIVATE_PACKET_DIR,
    a4_private_dir: Path = DEFAULT_A4_PRIVATE_DIR,
    row_provider: Callable[[str], Iterator[str]] = admitted_local_row_provider,
    memory_cap_bytes: int = DEFAULT_A4_MEMORY_CAP_BYTES,
) -> dict[str, Any]:
    """Open the real private builder packet (never the membership file),
    independently verify its ``builder_eligible_source_unit_ids`` reproduce
    from its own ``builder_eligible_family_ids`` against the *public* seal
    receipt's family registry, resolve A4's own private unit-commitment salt
    (verify-only if one already exists; generate-once, create-only
    otherwise), compute the real, keyed, id-free commitments, and stream the
    frozen extraction formula (``stream_ledger_rows_for_units``, memory-
    capped at ``memory_cap_bytes``) against whatever rows ``row_provider``
    yields -- the production default (``admitted_local_row_provider``)
    streams real row text for whichever of the four ``db.*`` units are both
    builder-eligible (per the private packet) and actually reachable in
    ``data/sources.db`` right now, and nothing at all for every other unit
    (the five ``historical.*`` units, or any ``db.*`` unit whose local store
    happens to be unreachable), so the ledger holds hash-only rows exactly
    for that subset.

    The resulting hash-only rows are written to a private, gitignored,
    create-only, mode-0600 JSONL ledger under ``a4_private_dir`` -- never
    returned, never held in memory as a list, and never embedded in the
    return value or any public receipt; only counts and a rolling
    commitment are. A rerun against the *same* seal/packet binding is a
    cheap verify-only path (reads the small private manifest, never
    re-streams the whole table); a rerun against a *different* binding with
    the same ``a4_private_dir`` fails closed on manifest drift, mirroring
    the salt artifact's own fail-closed rerun discipline just above.

    Fails closed (raises ``ExtractionError``/``heldout.AssignmentError``/
    ``MemoryBudgetExceeded``) if the private packet is missing, unreadable,
    does not reproduce, or the streaming pass would exceed its memory cap --
    never guesses at the builder-eligible set and never leaves a partial
    private ledger behind (see ``materialize_streaming_ledger``)."""
    seal_receipt = _load(seal_receipt_path)
    heldout.validate_receipt_independently(seal_receipt)

    packet_path = packet_dir / packet.PACKET_FILENAME
    stored_packet = heldout.load_private_artifact(packet_path, required_fields=packet.PRIVATE_PACKET_REQUIRED_FIELDS)
    require(
        stored_packet["seal_receipt_binding_sha256"] == heldout.receipt_binding_sha256(seal_receipt),
        "private builder packet seal_receipt_binding_sha256 drift against the live A3 seal receipt -- refusing",
    )
    source_unit_ids = packet.builder_eligible_source_unit_ids(
        seal_receipt, stored_packet["builder_eligible_family_ids"]
    )
    require(
        source_unit_ids == stored_packet["builder_eligible_source_unit_ids"],
        "private builder packet builder_eligible_source_unit_ids does not reproduce from the live seal "
        "receipt's source_family_registry -- refusing (tampered artifact or registry drift)",
    )

    binding = sha256_text(
        canonical_json(
            {
                "controlling_outcome_sha256": V4_SHA256,
                "seal_receipt_binding_sha256": heldout.receipt_binding_sha256(seal_receipt),
                "packet_seal_receipt_binding_sha256": stored_packet["seal_receipt_binding_sha256"],
            }
        )
    )
    salt_path = a4_private_dir / A4_SALT_FILENAME
    if salt_path.exists() or salt_path.is_symlink():
        stored_salt = heldout.load_private_artifact(salt_path, required_fields=A4_SALT_REQUIRED_FIELDS)
        require(
            stored_salt["algorithm_id"] == UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_id"],
            "private A4 salt artifact algorithm_id does not match the frozen unit-commitment algorithm -- refusing",
        )
        require(
            stored_salt["receipt_binding_sha256"] == binding,
            "private A4 salt artifact receipt_binding_sha256 drift against the live A3 seal/packet -- "
            "refusing (reseal/regenerate required)",
        )
        salt = bytes.fromhex(stored_salt["salt_hex"])
    else:
        salt = secrets.token_bytes(32)
        heldout.write_new_private_json_artifact(
            salt_path,
            {
                "algorithm_id": UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_id"],
                "algorithm_version": UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_version"],
                "salt_hex": salt.hex(),
                "receipt_binding_sha256": binding,
            },
        )

    unit_commitments = builder_eligible_unit_commitments(salt, source_unit_ids)
    root_commitment = root_commitment_sha256(salt, source_unit_ids)

    ledger_path = a4_private_dir / A4_LEDGER_FILENAME
    manifest_path = a4_private_dir / A4_LEDGER_MANIFEST_FILENAME
    if manifest_path.exists() or manifest_path.is_symlink():
        stored_manifest = heldout.load_private_artifact(
            manifest_path, required_fields=A4_LEDGER_MANIFEST_REQUIRED_FIELDS
        )
        require(
            stored_manifest["algorithm_id"] == LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_id"],
            "private A4 extraction-ledger manifest algorithm_id does not match the frozen ledger-commitment "
            "algorithm -- refusing",
        )
        require(
            stored_manifest["receipt_binding_sha256"] == binding,
            "private A4 extraction-ledger manifest receipt_binding_sha256 drift against the live A3 "
            "seal/packet -- refusing (reseal/regenerate required)",
        )
        ledger_summary = {
            "row_count": stored_manifest["row_count"],
            "root_sha256": stored_manifest["root_sha256"],
            "source_units_extracted": stored_manifest["source_units_extracted"],
        }
    else:
        require(
            not (ledger_path.exists() or ledger_path.is_symlink()),
            f"private extraction ledger exists without its manifest -- refusing (corrupt or partially "
            f"written private state, needs manual recovery): {ledger_path}",
        )
        ordered_units = sorted((unit_commitment_sha256(salt, unit_id), unit_id) for unit_id in source_unit_ids)
        row_stream = stream_ledger_rows_for_units(ordered_units, row_provider, memory_cap_bytes=memory_cap_bytes)
        ledger_summary = materialize_streaming_ledger(row_stream, ledger_path)
        heldout.write_new_private_json_artifact(
            manifest_path,
            {
                "algorithm_id": LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_id"],
                "algorithm_version": LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_version"],
                "row_count": ledger_summary["row_count"],
                "root_sha256": ledger_summary["root_sha256"],
                "source_units_extracted": ledger_summary["source_units_extracted"],
                "receipt_binding_sha256": binding,
            },
        )

    return {
        "packet_consumed": True,
        "consumed_source_unit_count": len(source_unit_ids),
        "unit_commitments": unit_commitments,
        "consumed_units_commitment_sha256": root_commitment,
        "extraction_ledger_commitment": {
            "row_count": ledger_summary["row_count"],
            "root_sha256": ledger_summary["root_sha256"],
        },
        "source_units_extracted": ledger_summary["source_units_extracted"],
        "spans_extracted": ledger_summary["row_count"],
    }


def verify_builder_packet_consumption_privately(
    receipt: dict[str, Any],
    seal_receipt_path: Path = A3_SEAL_RECEIPT_PATH,
    packet_dir: Path = DEFAULT_PRIVATE_PACKET_DIR,
    a4_private_dir: Path = DEFAULT_A4_PRIVATE_DIR,
) -> None:
    """Full cryptographic re-derivation of ``builder_packet_consumption``:
    opens the real private builder packet and the private A4 salt artifact
    and requires every declared commitment to reproduce exactly. Not called
    by ``validate_receipt_independently`` (and therefore never required by
    the pytest suite, which must pass in a fresh checkout with no
    ``batch_state/``) -- call this explicitly (``--verify-private``)
    whenever the private artifacts are actually present."""
    consumption = receipt["builder_packet_consumption"]
    require(
        consumption["packet_consumed"] is True, "receipt does not claim the packet was consumed -- nothing to verify"
    )

    seal_receipt = _load(seal_receipt_path)
    heldout.validate_receipt_independently(seal_receipt)

    packet_path = packet_dir / packet.PACKET_FILENAME
    stored_packet = heldout.load_private_artifact(packet_path, required_fields=packet.PRIVATE_PACKET_REQUIRED_FIELDS)
    require(
        stored_packet["seal_receipt_binding_sha256"] == heldout.receipt_binding_sha256(seal_receipt),
        "private builder packet seal_receipt_binding_sha256 drift against the live A3 seal receipt -- refusing",
    )
    recomputed_ids = packet.builder_eligible_source_unit_ids(seal_receipt, stored_packet["builder_eligible_family_ids"])
    require(
        recomputed_ids == stored_packet["builder_eligible_source_unit_ids"],
        "private builder packet builder_eligible_source_unit_ids does not reproduce from the live seal "
        "receipt's source_family_registry -- refusing",
    )

    salt_path = a4_private_dir / A4_SALT_FILENAME
    stored_salt = heldout.load_private_artifact(salt_path, required_fields=A4_SALT_REQUIRED_FIELDS)
    require(
        stored_salt["algorithm_id"] == UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_id"],
        "private A4 salt artifact algorithm_id does not match the frozen unit-commitment algorithm -- refusing",
    )
    salt = bytes.fromhex(stored_salt["salt_hex"])

    expected_commitments = builder_eligible_unit_commitments(salt, recomputed_ids)
    require(
        expected_commitments == consumption["unit_commitments"],
        "receipt builder_packet_consumption.unit_commitments does not reproduce from the private packet's "
        "real ids and the private A4 salt -- refusing",
    )
    require(
        root_commitment_sha256(salt, recomputed_ids) == consumption["consumed_units_commitment_sha256"],
        "receipt builder_packet_consumption.consumed_units_commitment_sha256 does not reproduce -- refusing",
    )
    require(
        consumption["consumed_source_unit_count"] == len(recomputed_ids),
        "receipt builder_packet_consumption.consumed_source_unit_count does not match the recomputed real "
        "count -- refusing",
    )

    manifest_path = a4_private_dir / A4_LEDGER_MANIFEST_FILENAME
    stored_manifest = heldout.load_private_artifact(manifest_path, required_fields=A4_LEDGER_MANIFEST_REQUIRED_FIELDS)
    require(
        stored_manifest["algorithm_id"] == LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR["algorithm_id"],
        "private A4 extraction-ledger manifest algorithm_id does not match the frozen ledger-commitment "
        "algorithm -- refusing",
    )
    ledger_commitment = consumption["extraction_ledger_commitment"]
    require(
        stored_manifest["row_count"] == ledger_commitment["row_count"]
        and stored_manifest["root_sha256"] == ledger_commitment["root_sha256"],
        "receipt builder_packet_consumption.extraction_ledger_commitment does not reproduce from the "
        "private extraction-ledger manifest -- refusing",
    )
    require(
        stored_manifest["source_units_extracted"] == consumption["source_units_extracted"],
        "receipt builder_packet_consumption.source_units_extracted does not match the private "
        "extraction-ledger manifest -- refusing",
    )

    ledger_path = a4_private_dir / A4_LEDGER_FILENAME
    replayed_state = new_ledger_rolling_state()
    replayed_row_count = 0
    replayed_units: set[str] = set()
    if stored_manifest["row_count"] > 0:
        for line in iter_private_artifact_lines(ledger_path):
            row = json.loads(line)
            replayed_state = ledger_rolling_update(replayed_state, row["output_sha256"])
            replayed_row_count += 1
            replayed_units.add(row["source_unit_commitment_sha256"])
    require(
        replayed_row_count == stored_manifest["row_count"],
        "private extraction ledger row count does not match its own manifest -- refusing (truncated or "
        "appended-to ledger file)",
    )
    require(
        replayed_state.hex() == stored_manifest["root_sha256"],
        "private extraction ledger does not replay to its own manifest's root_sha256 -- refusing (tampered "
        "or corrupted ledger file)",
    )
    require(
        len(replayed_units) == stored_manifest["source_units_extracted"],
        "private extraction ledger's distinct commitments do not match its own manifest's "
        "source_units_extracted -- refusing",
    )


# --- per-source-unit byte-level extraction residuals (public, content-blind) -
#
# A2's source_operation_ledger already publicly names all 9 real
# source_unit_ids (4 db.* existing-corpus collections, 5 historical.* frozen
# units) together with each one's own ``metadata_only`` flag and
# ``deterministic_local_analysis`` right -- none of that is secret, unlike
# *which 8 of the 9* are builder-eligible. Deriving one residual per real
# unit, uniformly across the full public registry, therefore never discloses
# complement membership: A4 is not selectively silent about the held-out
# one -- it reports on every real unit identically regardless of its
# (secret, never-consulted-here) eligibility. This never opens
# ``batch_state/`` and never queries any private artifact, and -- unlike
# ``consume_builder_packet``'s real ``byte_provider`` -- it never touches
# ``data/sources.db`` or any other local filesystem state either. It is a
# pure function of A2's own already-committed, already-public fields plus
# one more public, static fact: whether
# ``v4_source_byte_ingestion_admission.ADMITTED_SOURCE_UNIT_IDS`` (a
# hardcoded, git-committed constant -- never a live filesystem probe) admits
# this unit at all. Deliberately excludes any live "is the local store
# actually reachable right now" check: that fact is real (see
# ``v4_source_byte_ingestion_admission.local_bytes_reachable``) but is
# environment-dependent (``data/sources.db`` is a ~1.9 GiB gitignored file
# present on some machines and not others -- see that module's own
# docstring), and this receipt's independent verification must reproduce
# identically in a fresh checkout with no ``batch_state/`` *and* no local
# ``data/sources.db``, matching every other test in this suite that needs
# that file (``@pytest.mark.skipif(not SOURCES_DB.exists(), ...)`` elsewhere
# in this repo's test suite). The per-unit *observed* reachability at
# admission-authoring time lives only in the separate, informational
# ``admitted_source_units[].local_store_reachable_at_admission`` field of
# ``dataset_v4_source_byte_ingestion_admission_receipt_v1.json`` itself,
# which is likewise never re-asserted live during ordinary validation.
#
# ``subject_id`` is ``sha256(source_unit_id)`` -- unsalted, and therefore
# trivially re-enumerable by anyone who hashes A2's own 9 public ids and
# matches (this codebase's own comment on ``unit_commitment_sha256`` names
# that exact limitation for the *true* secret, held-out identity, which is
# why that commitment is HMAC-keyed instead). This receipt has no comparable
# secret to protect here -- reason_code is itself a pure function of A2's own
# already-public ``metadata_only``/rights fields plus the one public,
# hardcoded admission fact above, so a reader can already derive which real
# id maps to which residual from A2 and the byte-ingestion admission's
# module constant alone, hash or no hash. The hash exists only so this
# receipt stays self-contained and never repeats a plaintext source_unit_id
# verbatim, not to add real confidentiality.

SOURCE_UNIT_RESIDUAL_REASON_METADATA_ONLY = "metadata_only"
SOURCE_UNIT_RESIDUAL_REASON_PENDING_V4_INGESTION = "source_byte_content_not_yet_ingested_for_v4"
SOURCE_UNIT_RESIDUAL_REASON_ANALYSIS_DENIED = "deterministic_local_analysis_denied"
SOURCE_UNIT_RESIDUAL_REASON_INGESTION_ADMITTED = "source_byte_content_ingestion_admitted_for_v4"


def derive_source_unit_extraction_residuals(
    a2_receipt: dict[str, Any],
    admitted_source_unit_ids: frozenset[str] = byte_ingestion.ADMITTED_SOURCE_UNIT_IDS,
) -> list[dict[str, Any]]:
    """One typed, per-real-source-unit status entry -- a residual explaining
    why byte-level extraction cannot run against it yet, or a confirmation
    that a V4-scoped ingestion admission now exists for it (whether this
    unit's spans actually end up in ``extraction_ledger`` for a given run
    stays undisclosed here; see the section comment above): ``metadata_only``
    (A2 admitted metadata only, no byte content),
    ``deterministic_local_analysis_denied`` (A2 rights block even local
    analysis -- not currently true for any V4 candidate unit, handled for
    correctness), ``source_byte_content_not_yet_ingested_for_v4`` (no
    V4-scoped byte ingestion admission exists yet for this unit), or
    ``source_byte_content_ingestion_admitted_for_v4`` (one now does).
    Ordered by the *commitment*, not the source_unit_id (which never
    appears in this receipt -- see the section comment above), matching how
    ``builder_eligible_unit_commitments`` orders by commitment value too."""
    residuals = []
    for entry in a2_receipt["source_operation_ledger"]:
        unit_id = entry["source_unit_id"]
        rights = entry["operation_rights"]["deterministic_local_analysis"]["value"]
        evidence_refs = [
            "admission.dataset_v4_a2_source_operation_admission_receipt_v1.source_operation_ledger",
            "admission.dataset_v4_a4_deterministic_extraction_receipt_v1.extraction_algorithm",
        ]
        if entry["metadata_only"]:
            reason_code = SOURCE_UNIT_RESIDUAL_REASON_METADATA_ONLY
            owner_role = "source_admission_steward"
            next_action = (
                "obtain a real byte-content admission (beyond metadata_only) for this source unit from "
                "source_admission_steward before byte-level extraction can run against it"
            )
            retryability = "retryable"
        elif rights not in ("allowed", "scope_bound"):
            reason_code = SOURCE_UNIT_RESIDUAL_REASON_ANALYSIS_DENIED
            owner_role = "rights_capability_steward"
            next_action = (
                f"obtain deterministic_local_analysis rights (currently {rights!r}) for this source unit "
                "before byte-level extraction can run against it"
            )
            retryability = "retryable"
        elif unit_id not in admitted_source_unit_ids:
            reason_code = SOURCE_UNIT_RESIDUAL_REASON_PENDING_V4_INGESTION
            owner_role = "V4_source_byte_ingestion"
            next_action = (
                "V4_source_byte_ingestion must issue a rights-chain-verified V4-scoped byte ingestion "
                "admission for this source unit -- distinct from its general local retention -- before the "
                "frozen sha256(raw_span_bytes_utf8) formula in extraction_algorithm can execute against it"
            )
            retryability = "retryable"
        else:
            reason_code = SOURCE_UNIT_RESIDUAL_REASON_INGESTION_ADMITTED
            owner_role = "V4_source_byte_ingestion"
            next_action = (
                "no further admission action required from V4_source_byte_ingestion for this source unit; "
                "whether its spans actually appear in extraction_ledger for a given V4 run depends on the "
                "private builder-eligible complement and on live local-store reachability, neither of which "
                "this residual discloses"
            )
            retryability = "not_retryable"
            evidence_refs = [
                *evidence_refs,
                "admission.dataset_v4_source_byte_ingestion_admission_receipt_v1.admitted_source_units",
            ]
        commitment = sha256_text(unit_id)
        residuals.append(
            {
                "residual_id": f"a4-residual-{reason_code.replace('_', '-')}-{commitment[:16]}",
                "subject_kind": "source_unit_commitment",
                "subject_id": commitment,
                "stage": "A4",
                "reason_code": reason_code,
                "owner_role": owner_role,
                "next_action": next_action,
                "retryability": retryability,
                "evidence_refs": evidence_refs,
            }
        )
    residuals.sort(key=lambda residual: residual["subject_id"])
    return residuals


# --- receipt assembly --------------------------------------------------------


def build_receipt(consumption: dict[str, Any], gate: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    a2_receipt = _load(A2_RECEIPT_PATH)
    a2_residuals_carried = [
        {"residual_id": entry["residual_id"], "origin_stage": "A2", "status": "unresolved_carried_to_a4"}
        for entry in a2_receipt["residuals"]
    ]

    return {
        "schema_version": "dataset_v4_a4_deterministic_extraction_receipt_v1",
        "receipt_id": "dataset-v4-a4-deterministic-extraction-v1",
        "status": "A4_BUILDER_PACKET_CONSUMED_GATE_OPEN_TEXT_FREE_NO_COMPLEMENT_ENUMERATION",
        "text_free": True,
        "controlling_outcome_sha256": V4_SHA256,
        "control_surfaces": {"public_control_issue": 7423, "pilot_child_issue": 7430, "private_operational_board": 622},
        "bindings": {
            "a2_source_operation_admission": {
                "path": str(A2_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A2_RECEIPT_PATH),
                "schema_version": "dataset_v4_a2_source_operation_admission_receipt_v1",
            },
            "a3_heldout_source_family_seal": {
                "path": str(A3_SEAL_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A3_SEAL_RECEIPT_PATH),
                "schema_version": "dataset_v4_a3_heldout_source_family_seal_receipt_v1",
            },
            "a3_builder_packet_receipt": {
                "path": str(A3_PACKET_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A3_PACKET_RECEIPT_PATH),
                "schema_version": "dataset_v4_a3_builder_packet_receipt_v1",
            },
            "v4_source_byte_ingestion_admission": {
                "path": str(BYTE_INGESTION_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(BYTE_INGESTION_RECEIPT_PATH),
                "schema_version": "dataset_v4_source_byte_ingestion_admission_receipt_v1",
            },
            "extraction_algorithm_implementation": {
                "path": "scripts/projects/open_model_data/v4_a4_deterministic_extraction.py",
                "sha256": sha256_file(root / "scripts/projects/open_model_data/v4_a4_deterministic_extraction.py"),
                "schema_version": "v4_a4_deterministic_extraction_script_v1",
            },
        },
        "extraction_algorithm": {
            **EXTRACTION_ALGORITHM_DESCRIPTOR,
            "algorithm_descriptor_sha256": EXTRACTION_ALGORITHM_DESCRIPTOR_SHA256,
        },
        "builder_packet_gate": {
            "gate_id": gate["gate_id"],
            "status": "BUILDER_PACKET_ISSUED_GATE_OPEN"
            if gate["gate_open"]
            else "AWAITING_A3_HELDOUT_BUILDER_PACKET_ISSUANCE",
            "requires": ["A3_seal_complete", "builder_packet_issued_by_a3_heldout"],
            "a3_seal_complete": gate["a3_seal_complete"],
            "builder_packet_issued": gate["builder_packet_issued"],
            "builder_eligible_source_unit_ids_known_to_a4": gate["builder_eligible_source_unit_ids_known_to_a4"],
            "packet_receipt_binding_verified": gate["packet_receipt_binding_verified"],
            "owner_role": gate["owner_role"],
            "blocked_reason_code": gate["blocked_reason_code"],
        },
        "builder_packet_consumption": {
            "consumption_id": "v4-a4-builder-packet-consumption-v1",
            "packet_opened_by": "A4_deterministic_extraction",
            "packet_consumed": consumption["packet_consumed"],
            "unit_commitment_algorithm": {
                **UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR,
                "algorithm_descriptor_sha256": UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR_SHA256,
            },
            "consumed_source_unit_count": consumption["consumed_source_unit_count"],
            "unit_commitments": consumption["unit_commitments"],
            "consumed_units_commitment_sha256": consumption["consumed_units_commitment_sha256"],
            "membership_disclosed": False,
            "heldout_family_id_disclosed": False,
            "source_units_extracted": consumption["source_units_extracted"],
            "extraction_ledger_commitment": {
                "commitment_algorithm": {
                    **LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR,
                    "algorithm_descriptor_sha256": LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR_SHA256,
                },
                "row_count": consumption["extraction_ledger_commitment"]["row_count"],
                "root_sha256": consumption["extraction_ledger_commitment"]["root_sha256"],
            },
        },
        "a2_residuals_carried_forward": a2_residuals_carried,
        "a4_residuals": derive_source_unit_extraction_residuals(a2_receipt),
        "execution_counters": {
            "dataset_rows_emitted": 0,
            "new_source_fetches": 0,
            "source_units_extracted": consumption.get("source_units_extracted", 0),
            "spans_extracted": consumption.get("spans_extracted", 0),
            "builder_packets_consumed": 1 if consumption["packet_consumed"] else 0,
            "builder_eligible_units_committed": consumption["consumed_source_unit_count"],
        },
        "safety_assertions": {
            "rows_not_admitted": True,
            "text_emitted": False,
            "held_out_membership_referenced": False,
            "extraction_executed_without_builder_packet": False,
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
    schema = _load(A4_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_receipt_schema(receipt: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(_load_schema()).iter_errors(receipt), key=lambda e: list(e.path))
    require(not errors, f"receipt fails schema validation: {errors[0].message}" if errors else "")


def validate_algorithm_metadata(receipt: dict[str, Any]) -> None:
    algorithm = receipt["extraction_algorithm"]
    declared = {k: algorithm.get(k) for k in EXTRACTION_ALGORITHM_DESCRIPTOR}
    require(
        declared == EXTRACTION_ALGORITHM_DESCRIPTOR,
        "receipt extraction_algorithm does not match the frozen EXTRACTION_ALGORITHM_DESCRIPTOR -- refusing",
    )
    require(
        algorithm.get("algorithm_descriptor_sha256") == EXTRACTION_ALGORITHM_DESCRIPTOR_SHA256,
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
    gate = check_builder_packet_gate(root)
    declared = receipt["builder_packet_gate"]
    require(
        declared["a3_seal_complete"] == gate["a3_seal_complete"]
        and declared["builder_packet_issued"] == gate["builder_packet_issued"]
        and declared["builder_eligible_source_unit_ids_known_to_a4"]
        == gate["builder_eligible_source_unit_ids_known_to_a4"]
        and declared["packet_receipt_binding_verified"] == gate["packet_receipt_binding_verified"]
        and declared["blocked_reason_code"] == gate["blocked_reason_code"],
        "receipt builder_packet_gate does not match the state independently re-derived from the live A3 "
        "seal and A3 builder packet receipts -- refusing (reseal/re-issue or regenerate required)",
    )

    validate_ledger_consistency_with_gate(receipt, gate)

    consumption = receipt["builder_packet_consumption"]
    if gate["gate_open"]:
        require(
            consumption["packet_consumed"] is True,
            "builder_packet_gate is open but builder_packet_consumption.packet_consumed is not true -- refusing",
        )
    else:
        require(
            consumption["packet_consumed"] is False and consumption["unit_commitments"] == [],
            "builder_packet_gate is closed but builder_packet_consumption claims a packet was consumed -- refusing",
        )


def validate_ledger_consistency_with_gate(receipt: dict[str, Any], gate: dict[str, Any]) -> None:
    """Pure, gate-dict-parameterized so it can be exercised directly against
    a synthetic gate in tests, independent of ``check_builder_packet_gate``'s
    live filesystem read. The extraction ledger commitment may only be
    non-empty once the packet gate is genuinely open *and* the packet was
    actually consumed -- extraction never runs ahead of, or without, a real
    consumption. ``dataset_rows_emitted`` is separately pinned to ``const 0``
    by the schema regardless: ledger rows are pre-admission span/unit
    hashes, never admitted dataset rows.

    This is necessarily a much weaker check than the old literal-array
    version it replaces: with the ledger itself private (see the module
    docstring), a public-only verifier can check the *commitment*'s shape
    and its cross-references to other public counters, but can never
    recompute ``root_sha256`` from row content it was never given --
    ``verify_builder_packet_consumption_privately`` does that, by replaying
    the real private ledger file."""
    consumption = receipt["builder_packet_consumption"]
    ledger_commitment = consumption["extraction_ledger_commitment"]
    row_count = ledger_commitment["row_count"]
    root_sha256 = ledger_commitment["root_sha256"]

    if not gate["gate_open"] or not consumption["packet_consumed"]:
        require(
            row_count == 0 and root_sha256 == EMPTY_LEDGER_ROOT_SHA256,
            "extraction_ledger_commitment is non-empty but the builder_packet_gate is not open and/or the "
            "packet was not consumed -- refusing (extraction must never run ahead of a real consumption)",
        )
    if row_count == 0:
        require(
            root_sha256 == EMPTY_LEDGER_ROOT_SHA256,
            "extraction_ledger_commitment.row_count is 0 but root_sha256 is not the frozen empty-ledger "
            "commitment -- refusing",
        )

    require(
        receipt["execution_counters"]["spans_extracted"] == row_count,
        "execution_counters.spans_extracted does not match builder_packet_consumption."
        "extraction_ledger_commitment.row_count -- refusing",
    )
    require(
        receipt["execution_counters"]["source_units_extracted"] == consumption["source_units_extracted"],
        "execution_counters.source_units_extracted does not match builder_packet_consumption."
        "source_units_extracted -- refusing",
    )
    require(
        consumption["source_units_extracted"] <= consumption["consumed_source_unit_count"],
        "builder_packet_consumption.source_units_extracted exceeds consumed_source_unit_count -- refusing "
        "(cannot have extracted spans for more units than were actually consumed)",
    )


def validate_builder_packet_consumption(receipt: dict[str, Any]) -> None:
    """Public-only structural verification of ``builder_packet_consumption``:
    the algorithm metadata/hash, internal count/shape consistency, and (when
    the packet receipt is available on disk) a cross-check of the declared
    count against the packet receipt's own public
    ``builder_eligible_source_unit_count``. Never re-derives the commitment
    *values* themselves -- that requires the private packet and the private
    A4 salt artifact; see ``verify_builder_packet_consumption_privately``."""
    consumption = receipt["builder_packet_consumption"]
    algorithm = consumption["unit_commitment_algorithm"]
    declared = {k: algorithm.get(k) for k in UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR}
    require(
        declared == UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR,
        "builder_packet_consumption.unit_commitment_algorithm does not match the frozen "
        "UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR -- refusing",
    )
    require(
        algorithm.get("algorithm_descriptor_sha256") == UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR_SHA256,
        "builder_packet_consumption.unit_commitment_algorithm.algorithm_descriptor_sha256 does not match the "
        "locally recomputed frozen descriptor hash -- refusing",
    )

    if not consumption["packet_consumed"]:
        require(
            consumption["consumed_source_unit_count"] == 0 and consumption["unit_commitments"] == [],
            "builder_packet_consumption.packet_consumed is false but declares consumed units -- refusing",
        )
        return

    require(
        len(consumption["unit_commitments"]) == consumption["consumed_source_unit_count"],
        "builder_packet_consumption.unit_commitments length does not match consumed_source_unit_count -- refusing",
    )
    require(
        len(set(consumption["unit_commitments"])) == len(consumption["unit_commitments"]),
        "builder_packet_consumption.unit_commitments contains duplicate commitments -- refusing",
    )
    require(
        consumption["unit_commitments"] == sorted(consumption["unit_commitments"]),
        "builder_packet_consumption.unit_commitments is not sorted by commitment value -- refusing",
    )

    if A3_PACKET_RECEIPT_PATH.is_file():
        packet_receipt = _load(A3_PACKET_RECEIPT_PATH)
        require(
            consumption["consumed_source_unit_count"] == packet_receipt["packet"]["builder_eligible_source_unit_count"],
            "builder_packet_consumption.consumed_source_unit_count does not match the public A3 builder "
            "packet receipt's builder_eligible_source_unit_count -- refusing",
        )

    validate_extraction_ledger_commitment_shape(consumption["extraction_ledger_commitment"])


def validate_extraction_ledger_commitment_shape(ledger_commitment: dict[str, Any]) -> None:
    """Public-only structural verification of ``extraction_ledger_commitment``:
    the frozen commitment-algorithm metadata/hash, and that ``row_count``/
    ``root_sha256`` agree with each other for the empty case. Never
    recomputes ``root_sha256`` from real rows -- the ledger itself is
    private; see ``verify_builder_packet_consumption_privately`` for the
    replay-based check that can."""
    algorithm = ledger_commitment["commitment_algorithm"]
    declared = {k: algorithm.get(k) for k in LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR}
    require(
        declared == LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR,
        "extraction_ledger_commitment.commitment_algorithm does not match the frozen "
        "LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR -- refusing",
    )
    require(
        algorithm.get("algorithm_descriptor_sha256") == LEDGER_COMMITMENT_ALGORITHM_DESCRIPTOR_SHA256,
        "extraction_ledger_commitment.commitment_algorithm.algorithm_descriptor_sha256 does not match the "
        "locally recomputed frozen descriptor hash -- refusing",
    )
    if ledger_commitment["row_count"] == 0:
        require(
            ledger_commitment["root_sha256"] == EMPTY_LEDGER_ROOT_SHA256,
            "extraction_ledger_commitment.row_count is 0 but root_sha256 is not the frozen empty-ledger "
            "commitment -- refusing",
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


def validate_a4_residuals_derivable_from_a2(receipt: dict[str, Any]) -> None:
    """Independently re-derives ``a4_residuals`` from the live, public A2
    receipt on disk and requires an exact match -- catches a stale, hand-
    edited, or incomplete residual list (e.g. one still scoped to only the
    secret builder-eligible subset, which would itself be a complement-
    membership leak) even though the derivation is otherwise pure."""
    a2_receipt = _load(A2_RECEIPT_PATH)
    expected = derive_source_unit_extraction_residuals(a2_receipt)
    require(
        receipt["a4_residuals"] == expected,
        "a4_residuals does not reproduce from A2's public source_operation_ledger -- refusing",
    )


@validation_session
def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    validate_algorithm_metadata(receipt)
    from learn_ukrainian_v4_runtime.provenance import validate_receipt_bindings

    validate_receipt_bindings(receipt, root, validate_bindings_hash_to_disk, require)
    validate_gate_matches_receipt(receipt, root)
    validate_builder_packet_consumption(receipt)
    validate_no_forbidden_keys(receipt)
    validate_a4_residuals_derivable_from_a2(receipt)
    validate_receipt_schema(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=A4_RECEIPT_PATH,
        help="A4 receipt JSON to verify (default: the tracked V4 A4 extraction receipt).",
    )
    parser.add_argument(
        "--consume",
        action="store_true",
        help=(
            "Open the real private builder packet, independently verify it, and (re)compute the real unit "
            "commitments. Requires the packet-gate to be open and the private packet to be present -- "
            "fails closed otherwise. Prints the consumption summary (id-free)."
        ),
    )
    parser.add_argument(
        "--seal-receipt", type=Path, default=A3_SEAL_RECEIPT_PATH, help="public A3 seal receipt JSON (read-only)"
    )
    parser.add_argument(
        "--packet-dir",
        type=Path,
        default=DEFAULT_PRIVATE_PACKET_DIR,
        help="directory holding the private builder packet A3 issued to A4 (read-only)",
    )
    parser.add_argument(
        "--a4-private-dir",
        type=Path,
        default=DEFAULT_A4_PRIVATE_DIR,
        help="directory for A4's own private unit-commitment salt artifact",
    )
    parser.add_argument(
        "--write-receipt",
        action="store_true",
        help="With --consume, assemble and write the freshly computed receipt to --receipt.",
    )
    parser.add_argument(
        "--verify-private",
        action="store_true",
        help="Additionally re-derive builder_packet_consumption cryptographically from the private artifacts.",
    )
    parser.add_argument(
        "--no-real-bytes",
        action="store_true",
        help=(
            "With --consume, force the no-op row_provider (no data/sources.db read at all) regardless of "
            "the real production default. Every other field (bindings, gate, unit commitments, a4_residuals) "
            "is still real; extraction_ledger_commitment stays at row_count 0. Use this for a cheap dry-run "
            "consumption that never opens data/sources.db at all -- the real production default "
            "(admitted_local_row_provider) streams row-by-row with a hard memory cap (see --memory-cap-bytes) "
            "specifically so it is safe to run against the real, larger admitted tables without this flag."
        ),
    )
    parser.add_argument(
        "--memory-cap-bytes",
        type=int,
        default=DEFAULT_A4_MEMORY_CAP_BYTES,
        help=(
            "With --consume (and not --no-real-bytes), the hard resident-memory cap the real streaming "
            f"extraction pass fails closed against (default: {DEFAULT_A4_MEMORY_CAP_BYTES} bytes)."
        ),
    )
    args = parser.parse_args(argv)

    if args.consume:
        gate = check_builder_packet_gate()
        require(
            gate["gate_open"],
            f"builder_packet_gate is not open (blocked_reason_code={gate['blocked_reason_code']!r}) -- "
            "refusing to consume",
        )
        row_provider = no_v4_row_provider if args.no_real_bytes else admitted_local_row_provider
        consumption = consume_builder_packet(
            args.seal_receipt, args.packet_dir, args.a4_private_dir, row_provider, args.memory_cap_bytes
        )
        if args.write_receipt:
            receipt = build_receipt(consumption, gate)
            validate_receipt_independently(receipt)
            args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json(consumption))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    if args.verify_private:
        verify_builder_packet_consumption_privately(receipt, args.seal_receipt, args.packet_dir, args.a4_private_dir)
    gate = check_builder_packet_gate()
    print(canonical_json({"status": receipt["status"], "builder_packet_gate": gate}))


if __name__ == "__main__":
    try:
        main()
    except ExtractionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
