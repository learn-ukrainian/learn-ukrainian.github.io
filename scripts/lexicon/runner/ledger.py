"""Real-unit ledger, fencing, and resume (#5230 PR2).

Implements the LOCKED design in ENRICH-RUNNER-SPEC-v2.md §2, §6–§8:

- durable SQLite ledger with exclusive single-writer OS lock
- transactional claims with monotonic ``lease_generation``
- CAS on heartbeat / result / split / import / seal
- state vocabulary + total attempt caps + operator retry records
- fingerprint start/resume refusal and ``fingerprint_mismatch_refused``
- deterministic OOM-split child IDs with ``superseded`` parents + leaf-only seals

Workers never open this ledger for writing. Only the coordinator does.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import sqlite3
import time
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from scripts.lexicon.runner.contracts import (
    ENGINE_VERSION,
    LEDGER_SCHEMA_VERSION,
    SERIALIZATION_VERSION,
    ErrorCode,
    PhaseOutcome,
    canonical_json,
)
from scripts.lexicon.runner.split import child_chunk_id, split_on_oom

# Total automatic attempts per (run, unit, phase). Exhaustion → failed_terminal;
# only an audited operator action may reopen (spec §6).
DEFAULT_MAX_ATTEMPTS = 5

# Active-computation lease wall-clock; heartbeats extend. Transport holds no lease.
DEFAULT_LEASE_TTL_SECONDS = 300


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SchedulableState(StrEnum):
    """Schedulable unit states (spec §6)."""

    PENDING = "pending"
    LEASED = "leased"


class UnitOutcome(StrEnum):
    """Terminal / phase outcomes (spec §6)."""

    DONE = "done"
    NO_DATA = "no_data"
    FAILED_TERMINAL = "failed_terminal"
    RETRY_SCHEDULED = "retry_scheduled"


class ChunkLedgerState(StrEnum):
    PENDING = "pending"
    LEASED = "leased"
    DONE = "done"
    SUPERSEDED = "superseded"
    FAILED_TERMINAL = "failed_terminal"
    SEALED = "sealed"


class CasStatus(StrEnum):
    OK = "ok"
    STALE_COMMIT_REJECTED = "stale_commit_rejected"
    FINGERPRINT_MISMATCH_REFUSED = "fingerprint_mismatch_refused"
    DUPLICATE_RUNNER_REFUSED = "duplicate_runner_refused"
    ATTEMPT_CAP_EXHAUSTED = "attempt_cap_exhausted"
    NOT_FOUND = "not_found"
    INVALID_STATE = "invalid_state"
    NOT_LEAF = "not_leaf"
    LOCK_REQUIRED = "lock_required"


class OperatorActionKind(StrEnum):
    RETRY_FAILED = "retry_failed"
    ABANDON_PACKET = "abandon_packet"
    ACCEPT_FAILED = "accept_failed"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    status TEXT NOT NULL,
    manual_retry_epoch INTEGER NOT NULL DEFAULT 0,
    engine_version TEXT NOT NULL,
    serialization_version TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    config_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_runs_fingerprint ON runs(fingerprint);

CREATE TABLE IF NOT EXISTS run_phases (
    run_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    state TEXT NOT NULL,
    seal_sha256 TEXT,
    generation INTEGER NOT NULL DEFAULT 0,
    updated_at REAL NOT NULL,
    PRIMARY KEY (run_id, phase),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS chunks (
    run_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    parent_chunk_id TEXT,
    split_epoch INTEGER NOT NULL DEFAULT 0,
    lemma_ids_json TEXT NOT NULL,
    state TEXT NOT NULL,
    is_leaf INTEGER NOT NULL DEFAULT 1,
    lease_generation INTEGER NOT NULL DEFAULT 0,
    owner TEXT,
    leased_until REAL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    result_hash TEXT,
    error_code TEXT,
    seal_sha256 TEXT,
    updated_at REAL NOT NULL,
    PRIMARY KEY (run_id, chunk_id),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_chunks_state ON chunks(run_id, state);

CREATE TABLE IF NOT EXISTS work_units (
    run_id TEXT NOT NULL,
    unit_id TEXT NOT NULL,
    unit_kind TEXT NOT NULL,
    phase TEXT NOT NULL,
    state TEXT NOT NULL,
    lease_generation INTEGER NOT NULL DEFAULT 0,
    owner TEXT,
    leased_until REAL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    result_hash TEXT,
    error_code TEXT,
    packet_generation INTEGER NOT NULL DEFAULT 0,
    updated_at REAL NOT NULL,
    PRIMARY KEY (run_id, unit_id, phase),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_work_units_state ON work_units(run_id, phase, state);

CREATE TABLE IF NOT EXISTS host_cooldowns (
    host TEXT PRIMARY KEY,
    next_allowed_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS packets (
    run_id TEXT NOT NULL,
    packet_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    state TEXT NOT NULL,
    content_hash TEXT,
    created_at REAL NOT NULL,
    abandoned_at REAL,
    PRIMARY KEY (run_id, packet_id, generation),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS imports (
    run_id TEXT NOT NULL,
    lemma_id TEXT NOT NULL,
    packet_generation INTEGER NOT NULL,
    result_hash TEXT NOT NULL,
    lease_generation INTEGER NOT NULL,
    owner TEXT NOT NULL,
    imported_at REAL NOT NULL,
    PRIMARY KEY (run_id, lemma_id, packet_generation),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS seals (
    run_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    seal_sha256 TEXT NOT NULL,
    lemma_ids_json TEXT NOT NULL,
    lease_generation INTEGER NOT NULL,
    owner TEXT NOT NULL,
    sealed_at REAL NOT NULL,
    PRIMARY KEY (run_id, chunk_id),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS operator_actions (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    unit_id TEXT,
    phase TEXT,
    created_at REAL NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    event TEXT NOT NULL,
    created_at REAL NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS unit_request_keys (
    run_id TEXT NOT NULL,
    unit_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    request_key TEXT NOT NULL,
    packet_generation INTEGER NOT NULL,
    updated_at REAL NOT NULL,
    PRIMARY KEY (run_id, unit_id, phase),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);
"""


@dataclass(frozen=True, slots=True)
class CasResult:
    status: CasStatus
    detail: str = ""
    lease_generation: int | None = None
    run_id: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is CasStatus.OK


@dataclass(frozen=True, slots=True)
class ClaimResult:
    status: CasStatus
    unit_id: str
    lease_generation: int | None = None
    attempt_count: int | None = None
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status is CasStatus.OK


@dataclass(frozen=True, slots=True)
class StartRunResult:
    status: CasStatus
    run_id: str | None = None
    resumable_run_id: str | None = None
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status is CasStatus.OK


@dataclass(frozen=True, slots=True)
class ResumeRunResult:
    status: CasStatus
    run_id: str | None = None
    fingerprint: str | None = None
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status is CasStatus.OK


def compute_run_fingerprint(
    *,
    cohort_digest: str,
    engine_version: str = ENGINE_VERSION,
    serialization_version: str = SERIALIZATION_VERSION,
    enrichment_config: dict[str, Any] | None = None,
    source_digests: dict[str, str] | None = None,
    side_db_digests: dict[str, str] | None = None,
    cefr_versions: dict[str, str] | None = None,
    relation_versions: dict[str, str] | None = None,
    network_versions: dict[str, str] | None = None,
) -> str:
    """Deterministic run fingerprint (spec §2)."""
    payload = {
        "cohort_digest": cohort_digest,
        "engine_version": engine_version,
        "serialization_version": serialization_version,
        "enrichment_config": enrichment_config or {},
        "source_digests": source_digests or {},
        "side_db_digests": side_db_digests or {},
        "cefr_versions": cefr_versions or {},
        "relation_versions": relation_versions or {},
        "network_versions": network_versions or {},
        "ledger_schema": LEDGER_SCHEMA_VERSION,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class DuplicateRunnerError(RuntimeError):
    """Raised when a second coordinator tries to open the same ledger for writing."""


class Ledger:
    """Single-writer durable ledger for real lemma/chunk units."""

    def __init__(
        self,
        path: Path,
        *,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        lease_ttl_seconds: float = DEFAULT_LEASE_TTL_SECONDS,
        owner_id: str | None = None,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.max_attempts = int(max_attempts)
        self.lease_ttl_seconds = float(lease_ttl_seconds)
        self.owner_id = owner_id or f"coord-{uuid.uuid4().hex[:12]}"
        self._conn: sqlite3.Connection | None = None
        self._lock_fh: Any | None = None
        self._locked = False
        # Crash-injection points for tests (no-ops in production).
        self.crash_after_claim = False
        self.crash_mid_split = False
        self.crash_mid_seal = False
        self.crash_after_result = False
        self.crash_after_import = False
        # When True, marks the target packet generation abandoned inside the
        # commit_import write fence (before validation) to prove concurrent
        # abandon cannot slip past pre-txn reads (PR #5365 review finding 4).
        self.crash_import_concurrent_abandon = False

    # --- lock + open ---------------------------------------------------------

    def open(self, *, create: bool = True) -> None:
        """Open the ledger DB and acquire the exclusive single-writer OS lock."""
        if self._conn is not None:
            return
        if create:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_fh = open(lock_path, "a+", encoding="utf-8")  # noqa: SIM115
        try:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            lock_fh.close()
            raise DuplicateRunnerError(
                f"duplicate runner refused: ledger lock held on {lock_path}"
            ) from exc
        self._lock_fh = lock_fh
        self._locked = True
        lock_fh.seek(0)
        lock_fh.truncate()
        lock_fh.write(f"{self.owner_id}\n{time.time():.6f}\n")
        lock_fh.flush()

        self._conn = sqlite3.connect(self.path, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA synchronous = FULL")
        self._conn.executescript(SCHEMA_SQL)
        self._conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            ("schema_version", LEDGER_SCHEMA_VERSION),
        )

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        if self._lock_fh is not None:
            with contextlib.suppress(OSError):
                fcntl.flock(self._lock_fh.fileno(), fcntl.LOCK_UN)
            self._lock_fh.close()
            self._lock_fh = None
        self._locked = False

    def __enter__(self) -> Ledger:
        self.open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _require(self) -> sqlite3.Connection:
        if self._conn is None or not self._locked:
            raise RuntimeError("ledger not open under exclusive writer lock")
        return self._conn

    def _now(self, now: float | None = None) -> float:
        return time.time() if now is None else float(now)

    def _event(self, event: str, run_id: str | None = None, **payload: Any) -> None:
        conn = self._require()
        conn.execute(
            "INSERT INTO events(run_id, event, created_at, payload_json) VALUES (?, ?, ?, ?)",
            (run_id, event, self._now(), canonical_json(payload)),
        )

    # --- run lifecycle / fingerprint -----------------------------------------

    def find_incomplete_by_fingerprint(self, fingerprint: str) -> str | None:
        conn = self._require()
        row = conn.execute(
            "SELECT run_id FROM runs WHERE fingerprint = ? AND status = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (fingerprint, RunStatus.RUNNING.value),
        ).fetchone()
        return None if row is None else str(row["run_id"])

    def start_run(
        self,
        fingerprint: str,
        *,
        force_new: bool = False,
        config: dict[str, Any] | None = None,
        now: float | None = None,
    ) -> StartRunResult:
        """``start``: refuse duplication of an incomplete same-fingerprint run."""
        conn = self._require()
        ts = self._now(now)
        if not force_new:
            existing = self.find_incomplete_by_fingerprint(fingerprint)
            if existing is not None:
                self._event(
                    "fingerprint_reuse_refused",
                    existing,
                    fingerprint=fingerprint,
                    resumable_run_id=existing,
                )
                return StartRunResult(
                    status=CasStatus.INVALID_STATE,
                    resumable_run_id=existing,
                    detail=(
                        f"incomplete run already exists for fingerprint; "
                        f"resume run_id={existing}"
                    ),
                )
        run_id = f"run-{uuid.uuid4().hex}"
        conn.execute(
            "INSERT INTO runs("
            "run_id, fingerprint, status, manual_retry_epoch, "
            "engine_version, serialization_version, created_at, updated_at, config_json"
            ") VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?)",
            (
                run_id,
                fingerprint,
                RunStatus.RUNNING.value,
                ENGINE_VERSION,
                SERIALIZATION_VERSION,
                ts,
                ts,
                canonical_json(config or {}),
            ),
        )
        self._event("run_started", run_id, fingerprint=fingerprint, force_new=force_new)
        return StartRunResult(status=CasStatus.OK, run_id=run_id)

    def resume_run(
        self,
        run_id: str,
        fingerprint: str,
        *,
        now: float | None = None,
    ) -> ResumeRunResult:
        """``resume --run-id``: require exact fingerprint match."""
        conn = self._require()
        row = conn.execute(
            "SELECT run_id, fingerprint, status FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            return ResumeRunResult(
                status=CasStatus.NOT_FOUND,
                detail=f"run_id {run_id!r} not found",
            )
        if str(row["fingerprint"]) != fingerprint:
            self._event(
                ErrorCode.FINGERPRINT_MISMATCH_REFUSED.value,
                run_id,
                expected=str(row["fingerprint"]),
                got=fingerprint,
            )
            return ResumeRunResult(
                status=CasStatus.FINGERPRINT_MISMATCH_REFUSED,
                run_id=run_id,
                fingerprint=str(row["fingerprint"]),
                detail="fingerprint_mismatch_refused",
            )
        if str(row["status"]) == RunStatus.ABANDONED.value:
            return ResumeRunResult(
                status=CasStatus.INVALID_STATE,
                run_id=run_id,
                fingerprint=fingerprint,
                detail="run is abandoned",
            )
        ts = self._now(now)
        conn.execute(
            "UPDATE runs SET updated_at = ? WHERE run_id = ?",
            (ts, run_id),
        )
        self._event("run_resumed", run_id, fingerprint=fingerprint)
        return ResumeRunResult(
            status=CasStatus.OK,
            run_id=run_id,
            fingerprint=fingerprint,
        )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        conn = self._require()
        row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        return None if row is None else dict(row)

    def mark_run_completed(self, run_id: str, *, now: float | None = None) -> None:
        conn = self._require()
        conn.execute(
            "UPDATE runs SET status = ?, updated_at = ? WHERE run_id = ?",
            (RunStatus.COMPLETED.value, self._now(now), run_id),
        )
        self._event("run_completed", run_id)

    # --- registration --------------------------------------------------------

    def set_phase(
        self,
        run_id: str,
        phase: str,
        state: str,
        *,
        seal_sha256: str | None = None,
        now: float | None = None,
    ) -> None:
        conn = self._require()
        ts = self._now(now)
        row = conn.execute(
            "SELECT generation FROM run_phases WHERE run_id = ? AND phase = ?",
            (run_id, phase),
        ).fetchone()
        gen = 0 if row is None else int(row["generation"]) + 1
        conn.execute(
            "INSERT INTO run_phases(run_id, phase, state, seal_sha256, generation, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(run_id, phase) DO UPDATE SET "
            "state=excluded.state, seal_sha256=excluded.seal_sha256, "
            "generation=excluded.generation, updated_at=excluded.updated_at",
            (run_id, phase, state, seal_sha256, gen, ts),
        )

    def register_chunk(
        self,
        run_id: str,
        chunk_id: str,
        lemma_ids: Sequence[str],
        *,
        parent_chunk_id: str | None = None,
        split_epoch: int = 0,
        is_leaf: bool = True,
        state: str = ChunkLedgerState.PENDING.value,
        now: float | None = None,
    ) -> None:
        conn = self._require()
        ts = self._now(now)
        conn.execute(
            "INSERT OR IGNORE INTO chunks("
            "run_id, chunk_id, parent_chunk_id, split_epoch, lemma_ids_json, state, "
            "is_leaf, lease_generation, owner, leased_until, attempt_count, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL, NULL, 0, ?)",
            (
                run_id,
                chunk_id,
                parent_chunk_id,
                int(split_epoch),
                canonical_json(list(lemma_ids)),
                state,
                1 if is_leaf else 0,
                ts,
            ),
        )

    def register_work_unit(
        self,
        run_id: str,
        unit_id: str,
        *,
        unit_kind: Literal["lemma", "chunk"] = "lemma",
        phase: str = "offline_enrich",
        state: str = SchedulableState.PENDING.value,
        now: float | None = None,
    ) -> None:
        conn = self._require()
        ts = self._now(now)
        conn.execute(
            "INSERT OR IGNORE INTO work_units("
            "run_id, unit_id, unit_kind, phase, state, lease_generation, owner, "
            "leased_until, attempt_count, packet_generation, updated_at"
            ") VALUES (?, ?, ?, ?, ?, 0, NULL, NULL, 0, 0, ?)",
            (run_id, unit_id, unit_kind, phase, state, ts),
        )

    def register_chunk_work_units(
        self,
        run_id: str,
        chunks: Sequence[tuple[str, Sequence[str]]],
        *,
        phase: str = "offline_enrich",
        now: float | None = None,
    ) -> None:
        """Register chunk rows + one work unit per chunk (scheduling unit)."""
        for chunk_id, lemma_ids in chunks:
            self.register_chunk(run_id, chunk_id, lemma_ids, now=now)
            self.register_work_unit(
                run_id,
                chunk_id,
                unit_kind="chunk",
                phase=phase,
                now=now,
            )
            for lemma_id in lemma_ids:
                self.register_work_unit(
                    run_id,
                    lemma_id,
                    unit_kind="lemma",
                    phase=phase,
                    now=now,
                )

    # --- reclaim expired leases ----------------------------------------------

    def reclaim_expired(
        self,
        run_id: str,
        *,
        now: float | None = None,
    ) -> list[str]:
        """Release expired leases to pending; next claim increments generation."""
        conn = self._require()
        ts = self._now(now)
        reclaimed: list[str] = []
        rows = conn.execute(
            "SELECT unit_id, phase, lease_generation FROM work_units "
            "WHERE run_id = ? AND state = ? AND leased_until IS NOT NULL AND leased_until < ?",
            (run_id, SchedulableState.LEASED.value, ts),
        ).fetchall()
        for row in rows:
            conn.execute(
                "UPDATE work_units SET state = ?, owner = NULL, leased_until = NULL, "
                "updated_at = ? WHERE run_id = ? AND unit_id = ? AND phase = ? "
                "AND lease_generation = ? AND state = ?",
                (
                    SchedulableState.PENDING.value,
                    ts,
                    run_id,
                    row["unit_id"],
                    row["phase"],
                    int(row["lease_generation"]),
                    SchedulableState.LEASED.value,
                ),
            )
            reclaimed.append(str(row["unit_id"]))
            self._event(
                "lease_reclaimed",
                run_id,
                unit_id=str(row["unit_id"]),
                phase=str(row["phase"]),
                lease_generation=int(row["lease_generation"]),
            )
        # Chunk rows mirror work-unit leases when used as scheduling units.
        crows = conn.execute(
            "SELECT chunk_id, lease_generation FROM chunks "
            "WHERE run_id = ? AND state = ? AND leased_until IS NOT NULL AND leased_until < ?",
            (run_id, ChunkLedgerState.LEASED.value, ts),
        ).fetchall()
        for row in crows:
            conn.execute(
                "UPDATE chunks SET state = ?, owner = NULL, leased_until = NULL, "
                "updated_at = ? WHERE run_id = ? AND chunk_id = ? "
                "AND lease_generation = ? AND state = ?",
                (
                    ChunkLedgerState.PENDING.value,
                    ts,
                    run_id,
                    row["chunk_id"],
                    int(row["lease_generation"]),
                    ChunkLedgerState.LEASED.value,
                ),
            )
            if str(row["chunk_id"]) not in reclaimed:
                reclaimed.append(str(row["chunk_id"]))
        return reclaimed

    # --- claim / heartbeat / result ------------------------------------------

    def claim_unit(
        self,
        run_id: str,
        unit_id: str,
        owner: str,
        *,
        phase: str = "offline_enrich",
        now: float | None = None,
        host: str | None = None,
    ) -> ClaimResult:
        """Transactional claim: increments monotonic lease_generation."""
        conn = self._require()
        ts = self._now(now)
        if host is not None:
            cool = conn.execute(
                "SELECT next_allowed_at FROM host_cooldowns WHERE host = ?",
                (host,),
            ).fetchone()
            if cool is not None and float(cool["next_allowed_at"]) > ts:
                return ClaimResult(
                    status=CasStatus.INVALID_STATE,
                    unit_id=unit_id,
                    detail=f"host cooldown until {cool['next_allowed_at']}",
                )

        self.reclaim_expired(run_id, now=ts)

        # work_units + chunks must move atomically (review #5341 finding 1, 4).
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute(
                "SELECT * FROM work_units WHERE run_id = ? AND unit_id = ? AND phase = ?",
                (run_id, unit_id, phase),
            ).fetchone()
            if row is None:
                conn.execute("ROLLBACK")
                return ClaimResult(
                    status=CasStatus.NOT_FOUND, unit_id=unit_id, detail="unit missing"
                )

            state = str(row["state"])
            attempt_count = int(row["attempt_count"])
            if state in {
                UnitOutcome.DONE.value,
                UnitOutcome.NO_DATA.value,
                UnitOutcome.FAILED_TERMINAL.value,
                ChunkLedgerState.SEALED.value,
                ChunkLedgerState.SUPERSEDED.value,
            }:
                conn.execute("ROLLBACK")
                return ClaimResult(
                    status=CasStatus.INVALID_STATE,
                    unit_id=unit_id,
                    detail=f"unit not claimable in state={state}",
                )
            if state == SchedulableState.LEASED.value and float(row["leased_until"] or 0) >= ts:
                conn.execute("ROLLBACK")
                return ClaimResult(
                    status=CasStatus.INVALID_STATE,
                    unit_id=unit_id,
                    detail="unit already leased",
                )
            if attempt_count >= self.max_attempts:
                conn.execute(
                    "UPDATE work_units SET state = ?, error_code = ?, updated_at = ? "
                    "WHERE run_id = ? AND unit_id = ? AND phase = ?",
                    (
                        UnitOutcome.FAILED_TERMINAL.value,
                        "attempt_cap_exhausted",
                        ts,
                        run_id,
                        unit_id,
                        phase,
                    ),
                )
                # Mirror terminal outcome onto chunk row when unit is a chunk.
                conn.execute(
                    "UPDATE chunks SET state = ?, error_code = ?, owner = NULL, "
                    "leased_until = NULL, updated_at = ? "
                    "WHERE run_id = ? AND chunk_id = ?",
                    (
                        ChunkLedgerState.FAILED_TERMINAL.value,
                        "attempt_cap_exhausted",
                        ts,
                        run_id,
                        unit_id,
                    ),
                )
                self._event(
                    "attempt_cap_exhausted",
                    run_id,
                    unit_id=unit_id,
                    phase=phase,
                    attempt_count=attempt_count,
                )
                conn.execute("COMMIT")
                return ClaimResult(
                    status=CasStatus.ATTEMPT_CAP_EXHAUSTED,
                    unit_id=unit_id,
                    attempt_count=attempt_count,
                    detail="total automatic attempts exhausted",
                )

            new_gen = int(row["lease_generation"]) + 1
            new_attempts = attempt_count + 1
            leased_until = ts + self.lease_ttl_seconds
            cur = conn.execute(
                "UPDATE work_units SET state = ?, lease_generation = ?, owner = ?, "
                "leased_until = ?, attempt_count = ?, updated_at = ? "
                "WHERE run_id = ? AND unit_id = ? AND phase = ? "
                "AND lease_generation = ? AND state IN (?, ?, ?)",
                (
                    SchedulableState.LEASED.value,
                    new_gen,
                    owner,
                    leased_until,
                    new_attempts,
                    ts,
                    run_id,
                    unit_id,
                    phase,
                    int(row["lease_generation"]),
                    SchedulableState.PENDING.value,
                    UnitOutcome.RETRY_SCHEDULED.value,
                    SchedulableState.LEASED.value,
                ),
            )
            if cur.rowcount != 1:
                conn.execute("ROLLBACK")
                return ClaimResult(
                    status=CasStatus.STALE_COMMIT_REJECTED,
                    unit_id=unit_id,
                    detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                )

            # Keep chunk row in sync when unit is a chunk scheduling unit.
            conn.execute(
                "UPDATE chunks SET state = ?, lease_generation = ?, owner = ?, "
                "leased_until = ?, attempt_count = ?, updated_at = ? "
                "WHERE run_id = ? AND chunk_id = ? AND is_leaf = 1 "
                "AND state IN (?, ?)",
                (
                    ChunkLedgerState.LEASED.value,
                    new_gen,
                    owner,
                    leased_until,
                    new_attempts,
                    ts,
                    run_id,
                    unit_id,
                    ChunkLedgerState.PENDING.value,
                    ChunkLedgerState.LEASED.value,
                ),
            )
            self._event(
                "chunk_claimed" if str(row["unit_kind"]) == "chunk" else "unit_claimed",
                run_id,
                unit_id=unit_id,
                phase=phase,
                lease_generation=new_gen,
                owner=owner,
                attempt_count=new_attempts,
            )
            # Crash mid-transaction: both work_units and chunks roll back together.
            if self.crash_after_claim:
                raise RuntimeError("injected crash: after_claim")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

        return ClaimResult(
            status=CasStatus.OK,
            unit_id=unit_id,
            lease_generation=new_gen,
            attempt_count=new_attempts,
        )

    def heartbeat(
        self,
        run_id: str,
        unit_id: str,
        owner: str,
        lease_generation: int,
        *,
        phase: str = "offline_enrich",
        now: float | None = None,
    ) -> CasResult:
        """CAS heartbeat: only the current owner+generation may extend the lease."""
        conn = self._require()
        ts = self._now(now)
        leased_until = ts + self.lease_ttl_seconds
        cur = conn.execute(
            "UPDATE work_units SET leased_until = ?, updated_at = ? "
            "WHERE run_id = ? AND unit_id = ? AND phase = ? "
            "AND owner = ? AND lease_generation = ? AND state = ?",
            (
                leased_until,
                ts,
                run_id,
                unit_id,
                phase,
                owner,
                int(lease_generation),
                SchedulableState.LEASED.value,
            ),
        )
        if cur.rowcount != 1:
            self._event(
                ErrorCode.STALE_COMMIT_REJECTED.value,
                run_id,
                unit_id=unit_id,
                op="heartbeat",
                lease_generation=lease_generation,
                owner=owner,
            )
            return CasResult(
                status=CasStatus.STALE_COMMIT_REJECTED,
                detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                lease_generation=lease_generation,
                run_id=run_id,
            )
        conn.execute(
            "UPDATE chunks SET leased_until = ?, updated_at = ? "
            "WHERE run_id = ? AND chunk_id = ? AND owner = ? AND lease_generation = ?",
            (leased_until, ts, run_id, unit_id, owner, int(lease_generation)),
        )
        return CasResult(status=CasStatus.OK, lease_generation=lease_generation, run_id=run_id)

    def commit_result(
        self,
        run_id: str,
        unit_id: str,
        owner: str,
        lease_generation: int,
        outcome: PhaseOutcome | str,
        *,
        result_hash: str | None = None,
        error_code: str | None = None,
        phase: str = "offline_enrich",
        now: float | None = None,
    ) -> CasResult:
        """CAS result commit for a work unit."""
        conn = self._require()
        ts = self._now(now)
        outcome_s = str(outcome)
        if outcome_s not in {
            UnitOutcome.DONE.value,
            UnitOutcome.NO_DATA.value,
            UnitOutcome.FAILED_TERMINAL.value,
            UnitOutcome.RETRY_SCHEDULED.value,
        }:
            return CasResult(
                status=CasStatus.INVALID_STATE,
                detail=f"invalid outcome {outcome_s!r}",
            )
        new_state = outcome_s
        # Mirror terminal outcomes onto chunk rows when unit is a chunk.
        chunk_state = {
            UnitOutcome.DONE.value: ChunkLedgerState.DONE.value,
            UnitOutcome.NO_DATA.value: ChunkLedgerState.DONE.value,
            UnitOutcome.FAILED_TERMINAL.value: ChunkLedgerState.FAILED_TERMINAL.value,
            UnitOutcome.RETRY_SCHEDULED.value: ChunkLedgerState.PENDING.value,
        }[new_state]
        # work_units + chunks must move atomically (review #5341 finding 1).
        conn.execute("BEGIN IMMEDIATE")
        try:
            # All outcomes release the active lease; retry_scheduled returns to pending
            # so the scheduler can reclaim after cooldown without holding owner.
            cur = conn.execute(
                "UPDATE work_units SET state = ?, result_hash = ?, error_code = ?, "
                "owner = NULL, leased_until = NULL, updated_at = ? "
                "WHERE run_id = ? AND unit_id = ? AND phase = ? "
                "AND owner = ? AND lease_generation = ? AND state = ?",
                (
                    new_state,
                    result_hash,
                    error_code,
                    ts,
                    run_id,
                    unit_id,
                    phase,
                    owner,
                    int(lease_generation),
                    SchedulableState.LEASED.value,
                ),
            )
            if cur.rowcount != 1:
                conn.execute("ROLLBACK")
                self._event(
                    ErrorCode.STALE_COMMIT_REJECTED.value,
                    run_id,
                    unit_id=unit_id,
                    op="commit_result",
                    lease_generation=lease_generation,
                    owner=owner,
                )
                return CasResult(
                    status=CasStatus.STALE_COMMIT_REJECTED,
                    detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                    lease_generation=lease_generation,
                    run_id=run_id,
                )
            conn.execute(
                "UPDATE chunks SET state = ?, result_hash = ?, error_code = ?, "
                "owner = NULL, leased_until = NULL, updated_at = ? "
                "WHERE run_id = ? AND chunk_id = ? AND lease_generation = ?",
                (
                    chunk_state,
                    result_hash,
                    error_code,
                    ts,
                    run_id,
                    unit_id,
                    int(lease_generation),
                ),
            )
            self._event(
                "result_committed",
                run_id,
                unit_id=unit_id,
                outcome=new_state,
                result_hash=result_hash,
                lease_generation=lease_generation,
            )
            # Crash mid-transaction: both work_units and chunks roll back together.
            if self.crash_after_result:
                raise RuntimeError("injected crash: after_result")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return CasResult(status=CasStatus.OK, lease_generation=lease_generation, run_id=run_id)

    def set_host_cooldown(self, host: str, next_allowed_at: float) -> None:
        conn = self._require()
        conn.execute(
            "INSERT INTO host_cooldowns(host, next_allowed_at) VALUES (?, ?) "
            "ON CONFLICT(host) DO UPDATE SET next_allowed_at = excluded.next_allowed_at",
            (host, float(next_allowed_at)),
        )

    # --- split (CAS) ---------------------------------------------------------

    def commit_split(
        self,
        run_id: str,
        parent_chunk_id: str,
        owner: str,
        lease_generation: int,
        *,
        phase: str = "offline_enrich",
        now: float | None = None,
    ) -> CasResult:
        """CAS OOM split: create deterministic children; mark parent ``superseded``.

        Crash mid-transaction leaves either the parent active or parent+both children
        (SQLite single transaction). Retry recreates the same child IDs.
        """
        conn = self._require()
        ts = self._now(now)
        parent = conn.execute(
            "SELECT * FROM chunks WHERE run_id = ? AND chunk_id = ?",
            (run_id, parent_chunk_id),
        ).fetchone()
        if parent is None:
            return CasResult(status=CasStatus.NOT_FOUND, detail="parent chunk missing")
        if int(parent["is_leaf"]) != 1:
            return CasResult(status=CasStatus.NOT_LEAF, detail="parent is not a leaf")
        if (
            str(parent["owner"]) != owner
            or int(parent["lease_generation"]) != int(lease_generation)
            or str(parent["state"]) != ChunkLedgerState.LEASED.value
        ):
            self._event(
                ErrorCode.STALE_COMMIT_REJECTED.value,
                run_id,
                unit_id=parent_chunk_id,
                op="commit_split",
                lease_generation=lease_generation,
            )
            return CasResult(
                status=CasStatus.STALE_COMMIT_REJECTED,
                detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                lease_generation=lease_generation,
                run_id=run_id,
            )

        lemma_ids = json.loads(str(parent["lemma_ids_json"]))
        if not isinstance(lemma_ids, list) or not lemma_ids:
            return CasResult(status=CasStatus.INVALID_STATE, detail="empty parent lemmas")

        from scripts.lexicon.runner.contracts import ChunkSpec, ChunkState, OomSplitChildren

        parent_spec = ChunkSpec(
            chunk_id=parent_chunk_id,
            lemma_ids=[str(x) for x in lemma_ids],
            parent_chunk_id=parent["parent_chunk_id"],
            split_epoch=int(parent["split_epoch"]),
            state=ChunkState.PENDING,
        )
        split_result = split_on_oom(parent_spec)

        # Single-lemma and multi-lemma paths both need atomic work_units+chunks
        # transitions (review #5341 findings 1, 3).
        conn.execute("BEGIN IMMEDIATE")
        try:
            if not isinstance(split_result, OomSplitChildren):
                failed, code = split_result
                # Single-lemma OOM: failed_terminal, never split.
                cur = conn.execute(
                    "UPDATE chunks SET state = ?, error_code = ?, owner = NULL, "
                    "leased_until = NULL, updated_at = ? "
                    "WHERE run_id = ? AND chunk_id = ? AND owner = ? AND lease_generation = ?",
                    (
                        ChunkLedgerState.FAILED_TERMINAL.value,
                        code,
                        ts,
                        run_id,
                        parent_chunk_id,
                        owner,
                        int(lease_generation),
                    ),
                )
                if cur.rowcount != 1:
                    conn.execute("ROLLBACK")
                    return CasResult(
                        status=CasStatus.STALE_COMMIT_REJECTED,
                        detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                    )
                # Crash after first write, before work_units sync — exercises rollback.
                if self.crash_mid_split:
                    raise RuntimeError("injected crash: mid_split")
                conn.execute(
                    "UPDATE work_units SET state = ?, error_code = ?, owner = NULL, "
                    "leased_until = NULL, updated_at = ? "
                    "WHERE run_id = ? AND unit_id = ? AND phase = ? "
                    "AND owner = ? AND lease_generation = ?",
                    (
                        UnitOutcome.FAILED_TERMINAL.value,
                        code,
                        ts,
                        run_id,
                        parent_chunk_id,
                        phase,
                        owner,
                        int(lease_generation),
                    ),
                )
                self._event(
                    "failed_oom",
                    run_id,
                    chunk_id=parent_chunk_id,
                    lemma_ids=failed.lemma_ids,
                )
                conn.execute("COMMIT")
                return CasResult(
                    status=CasStatus.OK, lease_generation=lease_generation, run_id=run_id
                )

            cur = conn.execute(
                "UPDATE chunks SET state = ?, is_leaf = 0, owner = NULL, "
                "leased_until = NULL, updated_at = ? "
                "WHERE run_id = ? AND chunk_id = ? AND owner = ? AND lease_generation = ? "
                "AND state = ?",
                (
                    ChunkLedgerState.SUPERSEDED.value,
                    ts,
                    run_id,
                    parent_chunk_id,
                    owner,
                    int(lease_generation),
                    ChunkLedgerState.LEASED.value,
                ),
            )
            if cur.rowcount != 1:
                conn.execute("ROLLBACK")
                return CasResult(
                    status=CasStatus.STALE_COMMIT_REJECTED,
                    detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                )
            # Crash mid-transaction (after parent chunk write, before children).
            if self.crash_mid_split:
                raise RuntimeError("injected crash: mid_split")
            # CAS fence on parent work unit (review #5341 finding 3).
            cur_unit = conn.execute(
                "UPDATE work_units SET state = ?, owner = NULL, leased_until = NULL, "
                "updated_at = ? WHERE run_id = ? AND unit_id = ? AND phase = ? "
                "AND owner = ? AND lease_generation = ?",
                (
                    ChunkLedgerState.SUPERSEDED.value,
                    ts,
                    run_id,
                    parent_chunk_id,
                    phase,
                    owner,
                    int(lease_generation),
                ),
            )
            if cur_unit.rowcount != 1:
                conn.execute("ROLLBACK")
                return CasResult(
                    status=CasStatus.STALE_COMMIT_REJECTED,
                    detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                )
            for child in (split_result.left, split_result.right):
                # INSERT OR IGNORE keeps child IDs stable across crash-retry.
                conn.execute(
                    "INSERT OR IGNORE INTO chunks("
                    "run_id, chunk_id, parent_chunk_id, split_epoch, lemma_ids_json, "
                    "state, is_leaf, lease_generation, attempt_count, updated_at"
                    ") VALUES (?, ?, ?, ?, ?, ?, 1, 0, 0, ?)",
                    (
                        run_id,
                        child.chunk_id,
                        parent_chunk_id,
                        int(split_result.split_epoch),
                        canonical_json(list(child.lemma_ids)),
                        ChunkLedgerState.PENDING.value,
                        ts,
                    ),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO work_units("
                    "run_id, unit_id, unit_kind, phase, state, lease_generation, "
                    "attempt_count, packet_generation, updated_at"
                    ") VALUES (?, ?, 'chunk', ?, ?, 0, 0, 0, ?)",
                    (
                        run_id,
                        child.chunk_id,
                        phase,
                        SchedulableState.PENDING.value,
                        ts,
                    ),
                )
                for lemma_id in child.lemma_ids:
                    conn.execute(
                        "INSERT OR IGNORE INTO work_units("
                        "run_id, unit_id, unit_kind, phase, state, lease_generation, "
                        "attempt_count, packet_generation, updated_at"
                        ") VALUES (?, ?, 'lemma', ?, ?, 0, 0, 0, ?)",
                        (
                            run_id,
                            lemma_id,
                            phase,
                            SchedulableState.PENDING.value,
                            ts,
                        ),
                    )
            self._event(
                "chunk_split",
                run_id,
                parent=parent_chunk_id,
                left=split_result.left.chunk_id,
                right=split_result.right.chunk_id,
                split_epoch=split_result.split_epoch,
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

        # Prove child_id formula matches split module.
        assert split_result.left.chunk_id == child_chunk_id(
            parent_chunk_id, split_result.split_epoch, split_result.left.lemma_ids
        )
        return CasResult(status=CasStatus.OK, lease_generation=lease_generation, run_id=run_id)

    # --- import (CAS, per-lemma atomic) --------------------------------------

    def commit_import(
        self,
        run_id: str,
        lemma_id: str,
        owner: str,
        lease_generation: int,
        *,
        packet_generation: int,
        result_hash: str,
        expected_fingerprint: str | None = None,
        expected_request_key: str | None = None,
        phase: str = "network_import",
        now: float | None = None,
    ) -> CasResult:
        """CAS per-lemma import. Matching-hash re-import is a no-op success.

        Rejects abandoned/stale packet generations and optional request-key mismatch
        (PR3 / spec §Phase 6).

        All validation reads run under ``BEGIN IMMEDIATE`` so a concurrent
        abandon cannot race past stale pre-txn checks (PR #5365 review finding 4).
        """
        conn = self._require()
        ts = self._now(now)
        # Fence first: every validation read below is inside this transaction.
        conn.execute("BEGIN IMMEDIATE")
        try:
            # Test hook: simulate concurrent abandon after the write fence is
            # held but before validation — must still reject the import.
            if self.crash_import_concurrent_abandon:
                conn.execute(
                    "UPDATE packets SET state = 'abandoned', abandoned_at = ? "
                    "WHERE run_id = ? AND generation = ?",
                    (ts, run_id, int(packet_generation)),
                )

            run = self.get_run(run_id)
            if run is None:
                conn.execute("ROLLBACK")
                return CasResult(status=CasStatus.NOT_FOUND, detail="run missing")
            if expected_fingerprint is not None and str(run["fingerprint"]) != expected_fingerprint:
                conn.execute("ROLLBACK")
                self._event(
                    ErrorCode.FINGERPRINT_MISMATCH_REFUSED.value,
                    run_id,
                    op="import",
                    lemma_id=lemma_id,
                )
                return CasResult(
                    status=CasStatus.FINGERPRINT_MISMATCH_REFUSED,
                    detail=ErrorCode.FINGERPRINT_MISMATCH_REFUSED.value,
                    run_id=run_id,
                )

            # Stale/abandoned packet generation: refuse before any state change.
            if not self.packet_generation_active(run_id, int(packet_generation)):
                # Allow no-op re-import of an already-committed matching hash even if
                # the generation was later abandoned (artifacts already accepted).
                existing_early = conn.execute(
                    "SELECT result_hash FROM imports "
                    "WHERE run_id = ? AND lemma_id = ? AND packet_generation = ?",
                    (run_id, lemma_id, int(packet_generation)),
                ).fetchone()
                if existing_early is not None and str(existing_early["result_hash"]) == result_hash:
                    conn.execute("ROLLBACK")
                    return CasResult(
                        status=CasStatus.OK, lease_generation=lease_generation, run_id=run_id
                    )
                conn.execute("ROLLBACK")
                self._event(
                    "stale_packet_generation_rejected",
                    run_id,
                    lemma_id=lemma_id,
                    packet_generation=int(packet_generation),
                )
                return CasResult(
                    status=CasStatus.INVALID_STATE,
                    detail="stale_packet_generation",
                    run_id=run_id,
                )

            if expected_request_key is not None:
                key_row = conn.execute(
                    "SELECT request_key, packet_generation FROM unit_request_keys "
                    "WHERE run_id = ? AND unit_id = ? AND phase = ?",
                    (run_id, lemma_id, phase),
                ).fetchone()
                if key_row is not None:
                    if str(key_row["request_key"]) != expected_request_key:
                        conn.execute("ROLLBACK")
                        return CasResult(
                            status=CasStatus.INVALID_STATE,
                            detail="request_key_mismatch",
                            run_id=run_id,
                        )
                    if int(key_row["packet_generation"]) != int(packet_generation):
                        conn.execute("ROLLBACK")
                        return CasResult(
                            status=CasStatus.INVALID_STATE,
                            detail="stale_packet_generation",
                            run_id=run_id,
                        )

            existing = conn.execute(
                "SELECT result_hash FROM imports "
                "WHERE run_id = ? AND lemma_id = ? AND packet_generation = ?",
                (run_id, lemma_id, int(packet_generation)),
            ).fetchone()
            if existing is not None:
                if str(existing["result_hash"]) == result_hash:
                    conn.execute("ROLLBACK")
                    return CasResult(
                        status=CasStatus.OK, lease_generation=lease_generation, run_id=run_id
                    )
                conn.execute("ROLLBACK")
                return CasResult(
                    status=CasStatus.INVALID_STATE,
                    detail="import hash conflict for same packet generation",
                    run_id=run_id,
                )

            # Optional work-unit fencing when a leased import unit exists.
            unit = conn.execute(
                "SELECT * FROM work_units WHERE run_id = ? AND unit_id = ? AND phase = ?",
                (run_id, lemma_id, phase),
            ).fetchone()
            if (
                unit is not None
                and str(unit["state"]) == SchedulableState.LEASED.value
                and (
                    str(unit["owner"]) != owner
                    or int(unit["lease_generation"]) != int(lease_generation)
                )
            ):
                conn.execute("ROLLBACK")
                self._event(
                    ErrorCode.STALE_COMMIT_REJECTED.value,
                    run_id,
                    unit_id=lemma_id,
                    op="commit_import",
                    lease_generation=lease_generation,
                )
                return CasResult(
                    status=CasStatus.STALE_COMMIT_REJECTED,
                    detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                    lease_generation=lease_generation,
                    run_id=run_id,
                )

            conn.execute(
                "INSERT INTO imports("
                "run_id, lemma_id, packet_generation, result_hash, "
                "lease_generation, owner, imported_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    lemma_id,
                    int(packet_generation),
                    result_hash,
                    int(lease_generation),
                    owner,
                    ts,
                ),
            )
            if unit is not None:
                cur = conn.execute(
                    "UPDATE work_units SET state = ?, result_hash = ?, owner = NULL, "
                    "leased_until = NULL, packet_generation = ?, updated_at = ? "
                    "WHERE run_id = ? AND unit_id = ? AND phase = ? "
                    "AND owner = ? AND lease_generation = ?",
                    (
                        UnitOutcome.DONE.value,
                        result_hash,
                        int(packet_generation),
                        ts,
                        run_id,
                        lemma_id,
                        phase,
                        owner,
                        int(lease_generation),
                    ),
                )
                # Always reject when CAS misses — including reclaimed PENDING units
                # (review #5341 finding 2: prior-state LEASED guard was a bypass).
                if cur.rowcount != 1:
                    conn.execute("ROLLBACK")
                    return CasResult(
                        status=CasStatus.STALE_COMMIT_REJECTED,
                        detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                        lease_generation=lease_generation,
                        run_id=run_id,
                    )
            if self.crash_after_import:
                raise RuntimeError("injected crash: after_import")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

        self._event(
            "import_committed",
            run_id,
            lemma_id=lemma_id,
            packet_generation=packet_generation,
            result_hash=result_hash,
        )
        return CasResult(status=CasStatus.OK, lease_generation=lease_generation, run_id=run_id)

    # --- packets (PR3 transport) ---------------------------------------------

    def next_packet_generation(self, run_id: str) -> int:
        """Monotonic packet generation for a run (1-based)."""
        conn = self._require()
        row = conn.execute(
            "SELECT COALESCE(MAX(generation), 0) AS g FROM packets WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        return int(row["g"]) + 1

    def record_packet_exported(
        self,
        run_id: str,
        packet_id: str,
        generation: int,
        *,
        content_hash: str | None = None,
        now: float | None = None,
    ) -> CasResult:
        """Durable ``packet_exported`` — transport holds no lease (spec §Phase 4)."""
        conn = self._require()
        ts = self._now(now)
        existing = conn.execute(
            "SELECT state FROM packets WHERE run_id = ? AND packet_id = ? AND generation = ?",
            (run_id, packet_id, int(generation)),
        ).fetchone()
        if existing is not None and str(existing["state"]) == "abandoned":
            return CasResult(
                status=CasStatus.INVALID_STATE,
                detail="packet generation already abandoned",
                run_id=run_id,
            )
        conn.execute(
            "INSERT INTO packets("
            "run_id, packet_id, generation, state, content_hash, created_at, abandoned_at"
            ") VALUES (?, ?, ?, 'packet_exported', ?, ?, NULL) "
            "ON CONFLICT(run_id, packet_id, generation) DO UPDATE SET "
            "state = CASE WHEN packets.state = 'abandoned' THEN packets.state "
            "ELSE 'packet_exported' END, "
            "content_hash = COALESCE(excluded.content_hash, packets.content_hash)",
            (run_id, packet_id, int(generation), content_hash or packet_id, ts),
        )
        # Re-check abandoned race.
        row = conn.execute(
            "SELECT state FROM packets WHERE run_id = ? AND packet_id = ? AND generation = ?",
            (run_id, packet_id, int(generation)),
        ).fetchone()
        if row is not None and str(row["state"]) == "abandoned":
            return CasResult(
                status=CasStatus.INVALID_STATE,
                detail="packet generation already abandoned",
                run_id=run_id,
            )
        self._event(
            "packet_exported",
            run_id,
            packet_id=packet_id,
            generation=int(generation),
            content_hash=content_hash or packet_id,
        )
        return CasResult(status=CasStatus.OK, run_id=run_id)

    def packet_generation_active(self, run_id: str, generation: int) -> bool:
        """True when generation is importable.

        - No packets recorded for the run → allow (direct/PR2 import paths).
        - Generation has a non-abandoned row → allow.
        - Generation missing while other packets exist, or only abandoned → refuse.
        Active transport is never expired by wall-clock alone (spec §2).
        """
        conn = self._require()
        any_packets = conn.execute(
            "SELECT 1 FROM packets WHERE run_id = ? LIMIT 1",
            (run_id,),
        ).fetchone()
        if any_packets is None:
            return True
        rows = conn.execute(
            "SELECT state FROM packets WHERE run_id = ? AND generation = ?",
            (run_id, int(generation)),
        ).fetchall()
        if not rows:
            return False
        return any(str(r["state"]) != "abandoned" for r in rows)

    def get_packet(
        self, run_id: str, packet_id: str, generation: int
    ) -> dict[str, Any] | None:
        conn = self._require()
        row = conn.execute(
            "SELECT * FROM packets WHERE run_id = ? AND packet_id = ? AND generation = ?",
            (run_id, packet_id, int(generation)),
        ).fetchone()
        return None if row is None else dict(row)

    def set_work_unit_packet_generation(
        self,
        run_id: str,
        unit_id: str,
        packet_generation: int,
        *,
        phase: str = "network_import",
        request_key: str | None = None,
        now: float | None = None,
    ) -> None:
        """Bind a work unit to the active packet generation (and optional request key)."""
        conn = self._require()
        ts = self._now(now)
        conn.execute(
            "UPDATE work_units SET packet_generation = ?, updated_at = ? "
            "WHERE run_id = ? AND unit_id = ? AND phase = ?",
            (int(packet_generation), ts, run_id, unit_id, phase),
        )
        if request_key is not None:
            conn.execute(
                "INSERT INTO unit_request_keys("
                "run_id, unit_id, phase, request_key, packet_generation, updated_at"
                ") VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(run_id, unit_id, phase) DO UPDATE SET "
                "request_key = excluded.request_key, "
                "packet_generation = excluded.packet_generation, "
                "updated_at = excluded.updated_at",
                (run_id, unit_id, phase, request_key, int(packet_generation), ts),
            )

    def handle_http_429(
        self,
        run_id: str,
        unit_id: str,
        owner: str,
        lease_generation: int,
        *,
        host: str,
        next_allowed_at: float,
        phase: str = "network_fetch",
        now: float | None = None,
    ) -> CasResult:
        """429 → ``retry_scheduled`` + host cooldown; does not abandon packets.

        Active transport (``packet_exported`` rows) is intentionally untouched.
        """
        conn = self._require()
        ts = self._now(now)
        conn.execute("BEGIN IMMEDIATE")
        try:
            cur = conn.execute(
                "UPDATE work_units SET state = ?, error_code = ?, owner = NULL, "
                "leased_until = NULL, updated_at = ? "
                "WHERE run_id = ? AND unit_id = ? AND phase = ? "
                "AND owner = ? AND lease_generation = ? AND state = ?",
                (
                    UnitOutcome.RETRY_SCHEDULED.value,
                    "http_429",
                    ts,
                    run_id,
                    unit_id,
                    phase,
                    owner,
                    int(lease_generation),
                    SchedulableState.LEASED.value,
                ),
            )
            if cur.rowcount != 1:
                conn.execute("ROLLBACK")
                return CasResult(
                    status=CasStatus.STALE_COMMIT_REJECTED,
                    detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                    lease_generation=lease_generation,
                    run_id=run_id,
                )
            conn.execute(
                "INSERT INTO host_cooldowns(host, next_allowed_at) VALUES (?, ?) "
                "ON CONFLICT(host) DO UPDATE SET next_allowed_at = excluded.next_allowed_at",
                (host, float(next_allowed_at)),
            )
            self._event(
                "http_429_retry_scheduled",
                run_id,
                unit_id=unit_id,
                host=host,
                next_allowed_at=float(next_allowed_at),
                lease_generation=int(lease_generation),
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return CasResult(status=CasStatus.OK, lease_generation=lease_generation, run_id=run_id)

    # --- seal (CAS, leaf-only) -----------------------------------------------

    def commit_seal(
        self,
        run_id: str,
        chunk_id: str,
        owner: str,
        lease_generation: int,
        *,
        seal_sha256: str,
        lemma_ids: Sequence[str] | None = None,
        phase: str = "offline_enrich",
        now: float | None = None,
    ) -> CasResult:
        """CAS leaf seal. Interrupted seal leaves no seal row (spec crash matrix)."""
        conn = self._require()
        ts = self._now(now)
        chunk = conn.execute(
            "SELECT * FROM chunks WHERE run_id = ? AND chunk_id = ?",
            (run_id, chunk_id),
        ).fetchone()
        if chunk is None:
            return CasResult(status=CasStatus.NOT_FOUND, detail="chunk missing")
        if int(chunk["is_leaf"]) != 1:
            return CasResult(
                status=CasStatus.NOT_LEAF,
                detail="only leaf chunks may seal; parents stay superseded",
            )
        if str(chunk["state"]) == ChunkLedgerState.SUPERSEDED.value:
            return CasResult(
                status=CasStatus.NOT_LEAF,
                detail="superseded parents never seal",
            )
        # CAS: active lease owner+generation, OR a DONE leaf with matching generation
        # after the coordinator already released the owner (seal pass).
        owner_ok = str(chunk["owner"]) == owner and int(chunk["lease_generation"]) == int(
            lease_generation
        )
        done_ok = (
            str(chunk["state"]) == ChunkLedgerState.DONE.value
            and int(chunk["lease_generation"]) == int(lease_generation)
        )
        if not owner_ok and not done_ok:
            self._event(
                ErrorCode.STALE_COMMIT_REJECTED.value,
                run_id,
                unit_id=chunk_id,
                op="commit_seal",
                lease_generation=lease_generation,
            )
            return CasResult(
                status=CasStatus.STALE_COMMIT_REJECTED,
                detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                lease_generation=lease_generation,
                run_id=run_id,
            )

        if lemma_ids is None:
            lemma_ids = json.loads(str(chunk["lemma_ids_json"]))
        lemma_list = [str(x) for x in lemma_ids]

        conn.execute("BEGIN IMMEDIATE")
        try:
            # Re-check leaf under the write transaction.
            again = conn.execute(
                "SELECT is_leaf, state, lease_generation, owner FROM chunks "
                "WHERE run_id = ? AND chunk_id = ?",
                (run_id, chunk_id),
            ).fetchone()
            if again is None or int(again["is_leaf"]) != 1:
                conn.execute("ROLLBACK")
                return CasResult(status=CasStatus.NOT_LEAF, detail="not a leaf at seal time")
            if int(again["lease_generation"]) != int(lease_generation):
                conn.execute("ROLLBACK")
                return CasResult(
                    status=CasStatus.STALE_COMMIT_REJECTED,
                    detail=ErrorCode.STALE_COMMIT_REJECTED.value,
                )
            conn.execute(
                "INSERT INTO seals("
                "run_id, chunk_id, seal_sha256, lemma_ids_json, "
                "lease_generation, owner, sealed_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    chunk_id,
                    seal_sha256,
                    canonical_json(lemma_list),
                    int(lease_generation),
                    owner,
                    ts,
                ),
            )
            # Crash mid-transaction after seal insert — no half-seal rows survive.
            if self.crash_mid_seal:
                raise RuntimeError("injected crash: mid_seal")
            conn.execute(
                "UPDATE chunks SET state = ?, seal_sha256 = ?, owner = NULL, "
                "leased_until = NULL, updated_at = ? "
                "WHERE run_id = ? AND chunk_id = ? AND lease_generation = ?",
                (
                    ChunkLedgerState.SEALED.value,
                    seal_sha256,
                    ts,
                    run_id,
                    chunk_id,
                    int(lease_generation),
                ),
            )
            conn.execute(
                "UPDATE work_units SET state = ?, result_hash = ?, owner = NULL, "
                "leased_until = NULL, updated_at = ? "
                "WHERE run_id = ? AND unit_id = ? AND phase = ?",
                (
                    ChunkLedgerState.SEALED.value,
                    seal_sha256,
                    ts,
                    run_id,
                    chunk_id,
                    phase,
                ),
            )
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            # Seal already exists — idempotent only if hash matches.
            existing = conn.execute(
                "SELECT seal_sha256 FROM seals WHERE run_id = ? AND chunk_id = ?",
                (run_id, chunk_id),
            ).fetchone()
            if existing is not None and str(existing["seal_sha256"]) == seal_sha256:
                return CasResult(status=CasStatus.OK, lease_generation=lease_generation, run_id=run_id)
            return CasResult(status=CasStatus.INVALID_STATE, detail="seal conflict")
        except Exception:
            conn.execute("ROLLBACK")
            raise

        self._event(
            "chunk_sealed",
            run_id,
            chunk_id=chunk_id,
            seal_sha256=seal_sha256,
            lease_generation=lease_generation,
        )
        return CasResult(status=CasStatus.OK, lease_generation=lease_generation, run_id=run_id)

    # --- operator actions ----------------------------------------------------

    def retry_failed(
        self,
        run_id: str,
        unit_id: str,
        reason: str,
        *,
        phase: str = "offline_enrich",
        now: float | None = None,
    ) -> CasResult:
        """Only audited operator path to reopen terminal failures (spec §2, §6)."""
        if not reason or not str(reason).strip():
            return CasResult(status=CasStatus.INVALID_STATE, detail="reason required")
        conn = self._require()
        ts = self._now(now)
        row = conn.execute(
            "SELECT * FROM work_units WHERE run_id = ? AND unit_id = ? AND phase = ?",
            (run_id, unit_id, phase),
        ).fetchone()
        if row is None:
            return CasResult(status=CasStatus.NOT_FOUND, detail="unit missing")
        if str(row["state"]) != UnitOutcome.FAILED_TERMINAL.value:
            return CasResult(
                status=CasStatus.INVALID_STATE,
                detail=f"retry-failed only applies to failed_terminal, got {row['state']}",
            )
        # work_units + chunks + run epoch + audit row must move atomically
        # (review #5341 finding 1).
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute(
                "UPDATE work_units SET state = ?, error_code = NULL, result_hash = NULL, "
                "owner = NULL, leased_until = NULL, attempt_count = 0, updated_at = ? "
                "WHERE run_id = ? AND unit_id = ? AND phase = ?",
                (SchedulableState.PENDING.value, ts, run_id, unit_id, phase),
            )
            conn.execute(
                "UPDATE chunks SET state = ?, error_code = NULL, result_hash = NULL, "
                "owner = NULL, leased_until = NULL, attempt_count = 0, updated_at = ? "
                "WHERE run_id = ? AND chunk_id = ?",
                (ChunkLedgerState.PENDING.value, ts, run_id, unit_id),
            )
            conn.execute(
                "UPDATE runs SET manual_retry_epoch = manual_retry_epoch + 1, updated_at = ? "
                "WHERE run_id = ?",
                (ts, run_id),
            )
            conn.execute(
                "INSERT INTO operator_actions("
                "run_id, action, reason, unit_id, phase, created_at, payload_json"
                ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    OperatorActionKind.RETRY_FAILED.value,
                    reason,
                    unit_id,
                    phase,
                    ts,
                    canonical_json({"prior_lease_generation": int(row["lease_generation"])}),
                ),
            )
            self._event(
                "operator_retry_failed",
                run_id,
                unit_id=unit_id,
                phase=phase,
                reason=reason,
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return CasResult(status=CasStatus.OK, run_id=run_id)

    def abandon_packet(
        self,
        run_id: str,
        packet_id: str,
        generation: int,
        reason: str,
        *,
        now: float | None = None,
    ) -> CasResult:
        """Explicitly invalidate an outstanding transport generation (spec §2)."""
        if not reason or not str(reason).strip():
            return CasResult(status=CasStatus.INVALID_STATE, detail="reason required")
        conn = self._require()
        ts = self._now(now)
        conn.execute(
            "INSERT INTO packets(run_id, packet_id, generation, state, created_at, abandoned_at) "
            "VALUES (?, ?, ?, 'abandoned', ?, ?) "
            "ON CONFLICT(run_id, packet_id, generation) DO UPDATE SET "
            "state = 'abandoned', abandoned_at = excluded.abandoned_at",
            (run_id, packet_id, int(generation), ts, ts),
        )
        conn.execute(
            "INSERT INTO operator_actions("
            "run_id, action, reason, unit_id, phase, created_at, payload_json"
            ") VALUES (?, ?, ?, ?, NULL, ?, ?)",
            (
                run_id,
                OperatorActionKind.ABANDON_PACKET.value,
                reason,
                packet_id,
                ts,
                canonical_json({"generation": int(generation)}),
            ),
        )
        self._event(
            "packet_abandoned",
            run_id,
            packet_id=packet_id,
            generation=generation,
            reason=reason,
        )
        return CasResult(status=CasStatus.OK, run_id=run_id)

    # --- queries for resume --------------------------------------------------

    def list_pending_chunk_ids(
        self,
        run_id: str,
        *,
        phase: str = "offline_enrich",
    ) -> list[str]:
        conn = self._require()
        rows = conn.execute(
            "SELECT unit_id FROM work_units "
            "WHERE run_id = ? AND phase = ? AND unit_kind = 'chunk' "
            "AND state IN (?, ?, ?) ORDER BY unit_id",
            (
                run_id,
                phase,
                SchedulableState.PENDING.value,
                UnitOutcome.RETRY_SCHEDULED.value,
                SchedulableState.LEASED.value,
            ),
        ).fetchall()
        return [str(r["unit_id"]) for r in rows]

    def list_completed_chunk_ids(self, run_id: str) -> list[str]:
        conn = self._require()
        rows = conn.execute(
            "SELECT chunk_id FROM chunks WHERE run_id = ? AND state IN (?, ?) ORDER BY chunk_id",
            (
                run_id,
                ChunkLedgerState.DONE.value,
                ChunkLedgerState.SEALED.value,
            ),
        ).fetchall()
        return [str(r["chunk_id"]) for r in rows]

    def get_chunk(self, run_id: str, chunk_id: str) -> dict[str, Any] | None:
        conn = self._require()
        row = conn.execute(
            "SELECT * FROM chunks WHERE run_id = ? AND chunk_id = ?",
            (run_id, chunk_id),
        ).fetchone()
        return None if row is None else dict(row)

    def get_work_unit(
        self,
        run_id: str,
        unit_id: str,
        *,
        phase: str = "offline_enrich",
    ) -> dict[str, Any] | None:
        conn = self._require()
        row = conn.execute(
            "SELECT * FROM work_units WHERE run_id = ? AND unit_id = ? AND phase = ?",
            (run_id, unit_id, phase),
        ).fetchone()
        return None if row is None else dict(row)

    def count_operator_actions(self, run_id: str, action: str | None = None) -> int:
        conn = self._require()
        if action is None:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM operator_actions WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM operator_actions WHERE run_id = ? AND action = ?",
                (run_id, action),
            ).fetchone()
        return int(row["n"]) if row else 0

    def list_events(self, run_id: str | None = None, event: str | None = None) -> list[dict[str, Any]]:
        conn = self._require()
        sql = "SELECT * FROM events WHERE 1=1"
        params: list[Any] = []
        if run_id is not None:
            sql += " AND run_id = ?"
            params.append(run_id)
        if event is not None:
            sql += " AND event = ?"
            params.append(event)
        sql += " ORDER BY event_id"
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
