"""Formal review job skeleton (Fleet Comms Sol PR-F first slice / #5512).

Durable SQLite usage of ``formal_review_jobs`` / ``formal_review_attempts``
(schema from fleet_comms migrations). Unique active key:

    (repository, pr_number, head_sha, gate_kind)

Concurrent duplicate creates are rejected. This module does **not** cut over
``review-pr``, seal snapshots, resolve reviewers, validate verdicts, or publish
to GitHub (those are later PR-F / PR-G slices).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.contracts import CompletionState, new_id
from scripts.fleet_comms.migrations import apply_migrations

# Job lifecycle for this skeleton. Publication / sealed verdict acceptance land later.
JOB_STATES = frozenset({"open", "running", "complete", "failed", "blocked"})
ACTIVE_JOB_STATES = frozenset({"open", "running"})


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_completion_state(completion_state: CompletionState | str) -> str:
    if isinstance(completion_state, CompletionState):
        return completion_state.value
    value = str(completion_state).strip().lower()
    try:
        return CompletionState(value).value
    except ValueError as exc:
        raise FormalReviewJobsError(
            f"invalid completion_state: {completion_state!r}; "
            f"expected one of {[s.value for s in CompletionState]}"
        ) from exc


@dataclass(frozen=True, slots=True)
class FormalReviewAttempt:
    review_attempt_id: str
    review_id: str
    attempt_number: int
    completion_state: str
    raw_capture_artifact_id: str | None
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_attempt_id": self.review_attempt_id,
            "review_id": self.review_id,
            "attempt_number": self.attempt_number,
            "completion_state": self.completion_state,
            "raw_capture_artifact_id": self.raw_capture_artifact_id,
            "created_at": self.created_at,
        }


@dataclass(frozen=True, slots=True)
class FormalReviewJob:
    review_id: str
    repository: str
    pr_number: int
    head_sha: str
    gate_kind: str
    state: str
    snapshot_artifact_id: str | None
    created_at: str
    attempts: tuple[FormalReviewAttempt, ...] = field(default_factory=tuple)

    @property
    def unique_key(self) -> tuple[str, int, str, str]:
        return (self.repository, self.pr_number, self.head_sha, self.gate_kind)

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "repository": self.repository,
            "pr_number": self.pr_number,
            "head_sha": self.head_sha,
            "gate_kind": self.gate_kind,
            "state": self.state,
            "snapshot_artifact_id": self.snapshot_artifact_id,
            "created_at": self.created_at,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


class FormalReviewJobsError(RuntimeError):
    """Formal review job service refused an operation."""


class FormalReviewJobService:
    """SQLite writers/readers for formal review jobs and attempts (no GitHub)."""

    def __init__(
        self,
        *,
        store: ArtifactStore | None = None,
        root: Path | None = None,
    ) -> None:
        self.store = store or ArtifactStore(root=root)
        self._conn = self.store.connection
        apply_migrations(self._conn)

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> FormalReviewJobService:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def create_job(
        self,
        repository: str,
        pr: int,
        head_sha: str,
        gate_kind: str,
        *,
        snapshot_artifact_id: str | None = None,
        state: str = "open",
        review_id: str | None = None,
    ) -> FormalReviewJob:
        """Create a formal review job under the unique active key.

        Parameters
        ----------
        repository:
            ``owner/repo`` style identifier.
        pr:
            Pull request number (positive integer).
        head_sha:
            Immutable commit SHA under review.
        gate_kind:
            Gate discriminator (e.g. ``cross-family``).
        """
        repo = self._require_nonempty(repository, "repository")
        pr_number = self._require_pr(pr)
        sha = self._require_nonempty(head_sha, "head_sha").lower()
        gate = self._require_nonempty(gate_kind, "gate_kind")
        if state not in JOB_STATES:
            raise FormalReviewJobsError(
                f"invalid job state: {state!r}; expected one of {sorted(JOB_STATES)}"
            )
        if snapshot_artifact_id is not None:
            self._require_artifact(snapshot_artifact_id)

        existing = self._find_by_key(repo, pr_number, sha, gate)
        if existing is not None:
            raise FormalReviewJobsError(
                "concurrent duplicate formal review job rejected: "
                f"active key {(repo, pr_number, sha, gate)} already held by "
                f"{existing.review_id} (state={existing.state})"
            )

        rid = review_id or new_id("review")
        created = _utc_now()
        try:
            self._conn.execute(
                """INSERT INTO formal_review_jobs(
                    review_id, repository, pr_number, head_sha, gate_kind,
                    state, snapshot_artifact_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (rid, repo, pr_number, sha, gate, state, snapshot_artifact_id, created),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            self._conn.rollback()
            # Race: another writer inserted the same unique key between SELECT and INSERT.
            raced = self._find_by_key(repo, pr_number, sha, gate)
            if raced is not None:
                raise FormalReviewJobsError(
                    "concurrent duplicate formal review job rejected: "
                    f"active key {(repo, pr_number, sha, gate)} already held by "
                    f"{raced.review_id} (state={raced.state})"
                ) from exc
            raise FormalReviewJobsError(f"failed to create formal review job: {exc}") from exc
        return self.get_job(rid)

    def record_attempt(
        self,
        review_id: str,
        *,
        completion_state: CompletionState | str,
        raw_capture_artifact_id: str | None = None,
        review_attempt_id: str | None = None,
    ) -> FormalReviewAttempt:
        """Append one attempt row for an existing job.

        ``raw_capture_artifact_id`` is optional; when provided it must exist in
        the artifact store (FK is not enforced by schema, but the skeleton
        fails closed so callers cannot invent IDs).
        """
        job = self.get_job(review_id, include_attempts=False)
        state_value = _normalize_completion_state(completion_state)
        if raw_capture_artifact_id is not None:
            self._require_artifact(raw_capture_artifact_id)

        row = self._conn.execute(
            "SELECT COALESCE(MAX(attempt_number), 0) FROM formal_review_attempts WHERE review_id = ?",
            (job.review_id,),
        ).fetchone()
        next_number = int(row[0]) + 1 if row is not None else 1
        attempt_id = review_attempt_id or new_id("review-attempt")
        created = _utc_now()
        try:
            self._conn.execute(
                """INSERT INTO formal_review_attempts(
                    review_attempt_id, review_id, attempt_number,
                    completion_state, raw_capture_artifact_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    attempt_id,
                    job.review_id,
                    next_number,
                    state_value,
                    raw_capture_artifact_id,
                    created,
                ),
            )
            # Keep job state in step with the latest attempt (skeleton mapping only).
            new_job_state = self._map_completion_to_job_state(state_value, job.state)
            if new_job_state != job.state:
                self._conn.execute(
                    "UPDATE formal_review_jobs SET state = ? WHERE review_id = ?",
                    (new_job_state, job.review_id),
                )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            self._conn.rollback()
            raise FormalReviewJobsError(
                f"failed to record attempt for {job.review_id}: {exc}"
            ) from exc

        return FormalReviewAttempt(
            review_attempt_id=attempt_id,
            review_id=job.review_id,
            attempt_number=next_number,
            completion_state=state_value,
            raw_capture_artifact_id=raw_capture_artifact_id,
            created_at=created,
        )

    def get_job(self, review_id: str, *, include_attempts: bool = True) -> FormalReviewJob:
        rid = self._require_nonempty(review_id, "review_id")
        row = self._conn.execute(
            "SELECT * FROM formal_review_jobs WHERE review_id = ?", (rid,)
        ).fetchone()
        if row is None:
            raise FormalReviewJobsError(f"formal review job not found: {rid}")
        attempts: tuple[FormalReviewAttempt, ...] = ()
        if include_attempts:
            attempts = self._load_attempts(rid)
        return self._row_to_job(row, attempts=attempts)

    def list_jobs(
        self,
        *,
        repository: str | None = None,
        pr: int | None = None,
        head_sha: str | None = None,
        gate_kind: str | None = None,
        state: str | None = None,
        include_attempts: bool = False,
    ) -> list[FormalReviewJob]:
        """List jobs matching optional filters (``list_job`` API surface)."""
        clauses: list[str] = []
        params: list[Any] = []
        if repository is not None:
            clauses.append("repository = ?")
            params.append(self._require_nonempty(repository, "repository"))
        if pr is not None:
            clauses.append("pr_number = ?")
            params.append(self._require_pr(pr))
        if head_sha is not None:
            clauses.append("head_sha = ?")
            params.append(self._require_nonempty(head_sha, "head_sha").lower())
        if gate_kind is not None:
            clauses.append("gate_kind = ?")
            params.append(self._require_nonempty(gate_kind, "gate_kind"))
        if state is not None:
            if state not in JOB_STATES:
                raise FormalReviewJobsError(
                    f"invalid job state filter: {state!r}; expected one of {sorted(JOB_STATES)}"
                )
            clauses.append("state = ?")
            params.append(state)

        sql = "SELECT * FROM formal_review_jobs"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at ASC, review_id ASC"

        rows = self._conn.execute(sql, params).fetchall()
        jobs: list[FormalReviewJob] = []
        for row in rows:
            attempts: tuple[FormalReviewAttempt, ...] = ()
            if include_attempts:
                attempts = self._load_attempts(str(row["review_id"]))
            jobs.append(self._row_to_job(row, attempts=attempts))
        return jobs

    # Alias matching the brief's ``list_job`` naming.
    list_job = list_jobs

    def find_job(
        self,
        repository: str,
        pr: int,
        head_sha: str,
        gate_kind: str,
        *,
        include_attempts: bool = True,
    ) -> FormalReviewJob | None:
        """Lookup by unique active key; ``None`` if no job exists."""
        return self._find_by_key(
            self._require_nonempty(repository, "repository"),
            self._require_pr(pr),
            self._require_nonempty(head_sha, "head_sha").lower(),
            self._require_nonempty(gate_kind, "gate_kind"),
            include_attempts=include_attempts,
        )

    def _find_by_key(
        self,
        repository: str,
        pr_number: int,
        head_sha: str,
        gate_kind: str,
        *,
        include_attempts: bool = False,
    ) -> FormalReviewJob | None:
        row = self._conn.execute(
            """SELECT * FROM formal_review_jobs
               WHERE repository = ? AND pr_number = ? AND head_sha = ? AND gate_kind = ?""",
            (repository, pr_number, head_sha, gate_kind),
        ).fetchone()
        if row is None:
            return None
        attempts: tuple[FormalReviewAttempt, ...] = ()
        if include_attempts:
            attempts = self._load_attempts(str(row["review_id"]))
        return self._row_to_job(row, attempts=attempts)

    def _load_attempts(self, review_id: str) -> tuple[FormalReviewAttempt, ...]:
        rows = self._conn.execute(
            """SELECT * FROM formal_review_attempts
               WHERE review_id = ?
               ORDER BY attempt_number ASC""",
            (review_id,),
        ).fetchall()
        return tuple(
            FormalReviewAttempt(
                review_attempt_id=str(row["review_attempt_id"]),
                review_id=str(row["review_id"]),
                attempt_number=int(row["attempt_number"]),
                completion_state=str(row["completion_state"]),
                raw_capture_artifact_id=(
                    str(row["raw_capture_artifact_id"])
                    if row["raw_capture_artifact_id"] is not None
                    else None
                ),
                created_at=str(row["created_at"]),
            )
            for row in rows
        )

    @staticmethod
    def _row_to_job(
        row: sqlite3.Row,
        *,
        attempts: tuple[FormalReviewAttempt, ...],
    ) -> FormalReviewJob:
        return FormalReviewJob(
            review_id=str(row["review_id"]),
            repository=str(row["repository"]),
            pr_number=int(row["pr_number"]),
            head_sha=str(row["head_sha"]),
            gate_kind=str(row["gate_kind"]),
            state=str(row["state"]),
            snapshot_artifact_id=(
                str(row["snapshot_artifact_id"]) if row["snapshot_artifact_id"] is not None else None
            ),
            created_at=str(row["created_at"]),
            attempts=attempts,
        )

    def _require_artifact(self, artifact_id: str) -> None:
        aid = self._require_nonempty(artifact_id, "artifact_id")
        row = self._conn.execute(
            "SELECT 1 FROM artifacts WHERE artifact_id = ?", (aid,)
        ).fetchone()
        if row is None:
            raise FormalReviewJobsError(f"artifact not found: {aid}")

    @staticmethod
    def _require_nonempty(value: str, field_name: str) -> str:
        if value is None or not str(value).strip():
            raise FormalReviewJobsError(f"{field_name} is required")
        return str(value).strip()

    @staticmethod
    def _require_pr(pr: int) -> int:
        try:
            number = int(pr)
        except (TypeError, ValueError) as exc:
            raise FormalReviewJobsError(f"pr must be a positive integer, got {pr!r}") from exc
        if number < 1:
            raise FormalReviewJobsError(f"pr must be a positive integer, got {number}")
        return number

    @staticmethod
    def _map_completion_to_job_state(completion_state: str, current: str) -> str:
        if completion_state == CompletionState.COMPLETE.value:
            return "complete"
        if completion_state == CompletionState.FAILED.value:
            return "failed"
        if completion_state in {
            CompletionState.LENGTH_LIMITED.value,
            CompletionState.TRANSPORT_INCOMPLETE.value,
            CompletionState.UNKNOWN.value,
        }:
            # Keep open jobs runnable for retries; otherwise leave terminal alone.
            if current in ACTIVE_JOB_STATES:
                return "running"
            return current
        return current


def open_formal_review_jobs(root: Path | None = None) -> FormalReviewJobService:
    """Factory used by CLI/tests."""
    return FormalReviewJobService(root=root)
