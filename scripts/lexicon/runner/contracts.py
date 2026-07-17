"""Shared types and version pins for the enrichment runner (#5230)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

ENGINE_VERSION = "runner-pr3-v1"
SERIALIZATION_VERSION = "lemma-artifact-v1"
CEFR_ALGORITHM_VERSION = "grac-cohort-quantile-v1"
RELATION_CLOSURE_VERSION = "reciprocal-closure-v1"
SIDE_DB_SCHEMA_VERSION = "side-db-v1"
LEDGER_SCHEMA_VERSION = "ledger-v1"
NETWORK_CACHE_SCHEMA_VERSION = "network-cache-v1"
ADAPTER_VERSION = "http-adapter-v1"
REQUEST_POLICY_VERSION = "request-policy-v1"
PARSER_VERSION = "parser-v1"
NORMALIZER_VERSION = "normalizer-v1"
PARSED_SCHEMA_VERSION = "parsed-schema-v1"
PACKET_SCHEMA_VERSION = "packet-v1"
BUNDLE_SCHEMA_VERSION = "bundle-v1"

# Host memory policy (16 GiB local host). Platform/VPS ceilings are selected
# below physical RAM with explicit OS headroom — never copy 8/10 onto a smaller host.
DEFAULT_MEMORY_HIGH_BYTES = 8 * 1024**3
DEFAULT_MEMORY_MAX_BYTES = 10 * 1024**3


class ChunkState(StrEnum):
    """Chunk lifecycle states (PR1 splits + PR2 ledger vocabulary)."""

    PENDING = "pending"
    LEASED = "leased"
    RUNNING = "running"
    DONE = "done"
    SUPERSEDED = "superseded"
    FAILED_TERMINAL = "failed_terminal"
    SEALED = "sealed"
    RETRY_SCHEDULED = "retry_scheduled"


class ErrorCode(StrEnum):
    FAILED_OOM = "failed_oom"
    FINGERPRINT_MISMATCH_REFUSED = "fingerprint_mismatch_refused"
    STALE_COMMIT_REJECTED = "stale_commit_rejected"
    DUPLICATE_RUNNER_REFUSED = "duplicate_runner_refused"
    ATTEMPT_CAP_EXHAUSTED = "attempt_cap_exhausted"
    LEASE_RECLAIMED = "lease_reclaimed"


PhaseOutcome = Literal["done", "no_data", "failed_terminal", "retry_scheduled"]


@dataclass(frozen=True, slots=True)
class SideDbArtifact:
    """Content-addressed immutable side database."""

    path: str
    kind: str
    sha256: str
    schema_version: str = SIDE_DB_SCHEMA_VERSION
    row_count: int = 0


@dataclass(frozen=True, slots=True)
class PhaseSeal:
    """Run-level seal for a global preprocessing phase."""

    phase: str
    seal_sha256: str
    algorithm_version: str
    row_count: int


@dataclass(slots=True)
class ChunkSpec:
    """Leaf chunk identity and ordered lemma range."""

    chunk_id: str
    lemma_ids: list[str]
    parent_chunk_id: str | None = None
    split_epoch: int = 0
    state: ChunkState = ChunkState.PENDING


@dataclass(slots=True)
class WorkerResult:
    """Per-chunk (or per-lemma) outcome returned over IPC."""

    chunk_id: str
    outcome: PhaseOutcome
    error_code: str | None = None
    lemma_artifacts: dict[str, str] = field(default_factory=dict)  # lemma_id -> content hash
    peak_rss_bytes: int | None = None
    message: str = ""


@dataclass(frozen=True, slots=True)
class OomSplitChildren:
    """Deterministic children created when a multi-lemma leaf OOMs."""

    parent_chunk_id: str
    left: ChunkSpec
    right: ChunkSpec
    split_epoch: int


# --- PR4 stubs (PR3 network cache/transport is real — see network_cache/transport) ---


@dataclass(frozen=True, slots=True)
class LedgerStub:
    """Compatibility handle pointing at a real PR2+ ledger run.

    Prefer :class:`scripts.lexicon.runner.ledger.Ledger` for all writes.
    """

    run_id: str
    fingerprint: str
    note: str = "PR2/PR3 real-unit ledger (see scripts.lexicon.runner.ledger.Ledger)"


@dataclass(frozen=True, slots=True)
class PacketRef:
    """Content-addressed request packet (.tar.zst) — PR3."""

    packet_id: str
    generation: int = 0
    path: str = ""
    content_hash: str = ""


# Back-compat alias used by offline_engine until callers switch to PacketRef.
PacketStub = PacketRef


@dataclass(frozen=True, slots=True)
class BundleRef:
    """Content-addressed result bundle (.tar.zst) — PR3."""

    bundle_id: str
    packet_id: str
    packet_generation: int
    path: str = ""
    content_hash: str = ""


@dataclass(frozen=True, slots=True)
class SealStub:
    """PR4: full streaming assembly + publication gate.

    Leaf seal *transactions* are implemented in PR2 (CAS + leaf-only rules);
    final streaming assembly remains PR4.
    """

    chunk_id: str
    note: str = "PR4 stub — streaming assembly/publication not implemented in PR2"


def canonical_json(obj: Any) -> str:
    """Deterministic JSON for hashing (sorted keys, compact separators)."""
    import json

    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
