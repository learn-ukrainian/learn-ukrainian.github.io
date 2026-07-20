"""Unit tests for Fleet Comms PR-F formal review job skeleton (#5512)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.contracts import CompletionState
from scripts.fleet_comms.formal_review_jobs import (
    FormalReviewJobsError,
    FormalReviewJobService,
    open_formal_review_jobs,
)

REPO = "learn-ukrainian/learn-ukrainian.github.io"
HEAD = "a" * 40
GATE = "cross-family"


def _service(tmp_path: Path) -> FormalReviewJobService:
    return FormalReviewJobService(root=tmp_path / "fleet-comms-v1")


def test_create_job_get_job_round_trip(tmp_path: Path) -> None:
    with _service(tmp_path) as svc:
        job = svc.create_job(REPO, 5512, HEAD, GATE)
        assert job.repository == REPO
        assert job.pr_number == 5512
        assert job.head_sha == HEAD
        assert job.gate_kind == GATE
        assert job.state == "open"
        assert job.snapshot_artifact_id is None
        assert job.review_id.startswith("review_")
        assert job.attempts == ()

        loaded = svc.get_job(job.review_id)
        assert loaded.to_dict() == job.to_dict()
        assert loaded.unique_key == (REPO, 5512, HEAD, GATE)

        by_key = svc.find_job(REPO, 5512, HEAD, GATE)
        assert by_key is not None
        assert by_key.review_id == job.review_id


def test_create_job_rejects_concurrent_duplicate(tmp_path: Path) -> None:
    with _service(tmp_path) as svc:
        first = svc.create_job(REPO, 100, HEAD, GATE)
        with pytest.raises(FormalReviewJobsError, match=r"concurrent duplicate"):
            svc.create_job(REPO, 100, HEAD, GATE)
        # Same PR different head is allowed (new commit).
        other = svc.create_job(REPO, 100, "b" * 40, GATE)
        assert other.review_id != first.review_id
        # Same head different gate is allowed.
        other_gate = svc.create_job(REPO, 100, HEAD, "advisory")
        assert other_gate.gate_kind == "advisory"


def test_record_attempt_with_and_without_raw_capture(tmp_path: Path) -> None:
    root = tmp_path / "fleet-comms-v1"
    with ArtifactStore(root=root) as store:
        capture = store.store_bytes(
            b'{"type":"task_complete"}',
            producer="test-formal-review",
            retention_class="raw-capture",
            logical_filename="attempt.capture",
        )
        with FormalReviewJobService(store=store) as svc:
            job = svc.create_job(REPO, 42, HEAD, GATE)
            a1 = svc.record_attempt(
                job.review_id,
                completion_state=CompletionState.TRANSPORT_INCOMPLETE,
            )
            assert a1.attempt_number == 1
            assert a1.raw_capture_artifact_id is None
            assert a1.completion_state == "transport_incomplete"

            a2 = svc.record_attempt(
                job.review_id,
                completion_state="complete",
                raw_capture_artifact_id=capture.artifact_id,
            )
            assert a2.attempt_number == 2
            assert a2.raw_capture_artifact_id == capture.artifact_id
            assert a2.completion_state == CompletionState.COMPLETE.value

            full = svc.get_job(job.review_id)
            assert [a.attempt_number for a in full.attempts] == [1, 2]
            assert full.state == "complete"

            with pytest.raises(FormalReviewJobsError, match=r"artifact not found"):
                svc.record_attempt(
                    job.review_id,
                    completion_state=CompletionState.FAILED,
                    raw_capture_artifact_id="artifact_does_not_exist",
                )


def test_list_jobs_filters_and_alias(tmp_path: Path) -> None:
    with _service(tmp_path) as svc:
        j1 = svc.create_job(REPO, 1, HEAD, GATE)
        j2 = svc.create_job(REPO, 2, HEAD, GATE)
        j3 = svc.create_job("other/repo", 1, HEAD, GATE)

        all_jobs = svc.list_jobs()
        assert {j.review_id for j in all_jobs} == {j1.review_id, j2.review_id, j3.review_id}

        only_repo = svc.list_job(repository=REPO)
        assert {j.review_id for j in only_repo} == {j1.review_id, j2.review_id}

        only_pr = svc.list_jobs(repository=REPO, pr=2)
        assert [j.review_id for j in only_pr] == [j2.review_id]

        only_open = svc.list_jobs(state="open")
        assert len(only_open) == 3

        svc.record_attempt(j1.review_id, completion_state=CompletionState.FAILED)
        failed = svc.list_jobs(state="failed")
        assert [j.review_id for j in failed] == [j1.review_id]


def test_get_job_missing_and_validation(tmp_path: Path) -> None:
    with _service(tmp_path) as svc:
        with pytest.raises(FormalReviewJobsError, match=r"not found"):
            svc.get_job("review_missing")
        with pytest.raises(FormalReviewJobsError, match=r"repository is required"):
            svc.create_job("  ", 1, HEAD, GATE)
        with pytest.raises(FormalReviewJobsError, match=r"positive integer"):
            svc.create_job(REPO, 0, HEAD, GATE)
        with pytest.raises(FormalReviewJobsError, match=r"invalid completion_state"):
            job = svc.create_job(REPO, 9, HEAD, GATE)
            svc.record_attempt(job.review_id, completion_state="not-a-state")


def test_open_formal_review_jobs_factory(tmp_path: Path) -> None:
    root = tmp_path / "v1"
    svc = open_formal_review_jobs(root)
    try:
        job = svc.create_job(REPO, 7, HEAD, GATE)
        assert svc.get_job(job.review_id).pr_number == 7
    finally:
        svc.close()


def test_snapshot_artifact_id_must_exist(tmp_path: Path) -> None:
    root = tmp_path / "v1"
    with ArtifactStore(root=root) as store:
        snap = store.store_text("sealed-snapshot", producer="test", logical_filename="snap.md")
        with FormalReviewJobService(store=store) as svc:
            job = svc.create_job(
                REPO,
                3,
                HEAD,
                GATE,
                snapshot_artifact_id=snap.artifact_id,
            )
            assert job.snapshot_artifact_id == snap.artifact_id
            with pytest.raises(FormalReviewJobsError, match=r"artifact not found"):
                svc.create_job(
                    REPO,
                    4,
                    HEAD,
                    GATE,
                    snapshot_artifact_id="artifact_nope",
                )
