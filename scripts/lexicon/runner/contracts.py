"""Shared types and version pins for the enrichment runner (#5230)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

ENGINE_VERSION = "runner-pr1-v1"
SERIALIZATION_VERSION = "lemma-artifact-v1"
CEFR_ALGORITHM_VERSION = "grac-cohort-quantile-v1"
RELATION_CLOSURE_VERSION = "reciprocal-closure-v1"
SIDE_DB_SCHEMA_VERSION = "side-db-v1"

# Host memory policy (16 GiB local host). Platform/VPS ceilings are selected
# below physical RAM with explicit OS headroom — never copy 8/10 onto a smaller host.
DEFAULT_MEMORY_HIGH_BYTES = 8 * 1024**3
DEFAULT_MEMORY_MAX_BYTES = 10 * 1024**3


class ChunkState(StrEnum):
    """Chunk lifecycle states used by PR1 splits (ledger vocabulary expands in PR2)."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    SUPERSEDED = "superseded"
    FAILED_TERMINAL = "failed_terminal"


class ErrorCode(StrEnum):
    FAILED_OOM = "failed_oom"
    FINGERPRINT_MISMATCH_REFUSED = "fingerprint_mismatch_refused"
    STALE_COMMIT_REJECTED = "stale_commit_rejected"


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


# --- PR2/PR3/PR4 stubs (interfaces only; not implemented in PR1) ---


@dataclass(frozen=True, slots=True)
class LedgerStub:
    """PR2: real-unit ledger, fencing, leases. PR1 does not open this for writing."""

    run_id: str
    fingerprint: str
    note: str = "PR2 stub — ledger/leases/fencing not implemented in PR1"


@dataclass(frozen=True, slots=True)
class PacketStub:
    """PR3: content-addressed request packet (.tar.zst)."""

    packet_id: str
    note: str = "PR3 stub — network cache/packets not implemented in PR1"


@dataclass(frozen=True, slots=True)
class SealStub:
    """PR4: leaf seal transaction + streaming assembly."""

    chunk_id: str
    note: str = "PR4 stub — leaf sealing/assembly not implemented in PR1"


def canonical_json(obj: Any) -> str:
    """Deterministic JSON for hashing (sorted keys, compact separators)."""
    import json

    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
