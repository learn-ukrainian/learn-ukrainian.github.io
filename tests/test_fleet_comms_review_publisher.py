"""Fake-GitHub tests for Fleet Comms PR-G live publisher (#5512)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.review_publication import (
    DEFAULT_STATUS_CONTEXT,
    STATUS_ERROR,
    STATUS_FAILURE,
    STATUS_SUCCESS,
    plan_publication,
)
from scripts.fleet_comms.review_publisher import (
    ReviewPublisherError,
    execute_publication,
    fetch_pr_head_sha,
    lookup_publication_receipt,
    publish_sealed_verdict,
    sealed_matches_job,
)
from scripts.orchestration import rail_path_guard
from scripts.orchestration.rail_status import RAIL_STATUS_CONTEXT

_SHA_A = "a" * 40
_SHA_B = "b" * 40
_REPO = "learn-ukrainian/learn-ukrainian.github.io"


def _sealed(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "review_id": "review_deadbeef",
        "repository": _REPO,
        "pr_number": 5512,
        "head_sha": _SHA_A,
        "gate_kind": "cross-family-review",
        "verdict": "APPROVED",
        "model": "claude-opus-5",
        "family": "anthropic",
        "harness": "claude",
    }
    base.update(overrides)
    return base


def _approved_evidence() -> dict[str, object]:
    return {
        "schema_version": "code-review-findings.v1",
        "overall": {
            "correctness": "correct",
            "explanation": "The review found no defects that block approval.",
            "confidence": 0.95,
        },
        "findings": [],
    }


class FakeGh:
    """Records gh invocations and returns scripted responses."""

    def __init__(
        self,
        *,
        head: str = _SHA_A,
        body: str = "",
        files: list[str] | None = None,
        file_items: list[dict[str, str]] | None = None,
        changed_files: int | None = None,
    ) -> None:
        self.head = head
        self.body = body
        self.file_items = file_items or [{"filename": path} for path in (files or [])]
        self.changed_files = (
            len(self.file_items) if changed_files is None else changed_files
        )
        self.calls: list[list[str]] = []

    def __call__(
        self, command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(command))
        if len(command) >= 3 and command[1] == "pr" and command[2] == "view":
            json_fields = command[command.index("--json") + 1]
            if json_fields == "headRefOid,body,changedFiles":
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=json.dumps(
                        {
                            "headRefOid": self.head,
                            "body": self.body,
                            "changedFiles": self.changed_files,
                        }
                    ),
                    stderr="",
                )
            return subprocess.CompletedProcess(command, 0, stdout=f"{self.head}\n", stderr="")
        if (
            len(command) >= 5
            and command[1] == "api"
            and "/pulls/" in command[-1]
            and "/files?" in command[-1]
        ):
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps([self.file_items]),
                stderr="",
            )
        if len(command) >= 3 and command[1] == "pr" and command[2] == "comment":
            return subprocess.CompletedProcess(
                command, 0, stdout="https://example.test/comment/1\n", stderr=""
            )
        if len(command) >= 2 and command[1] == "api" and "statuses" in command[2]:
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="unexpected")


def test_fetch_pr_head_sha_uses_repo_flag() -> None:
    gh = FakeGh(head=_SHA_A)
    assert fetch_pr_head_sha(repository=_REPO, pr_number=12, runner=gh) == _SHA_A
    assert "--repo" in gh.calls[0]
    assert _REPO in gh.calls[0]


@pytest.mark.parametrize(
    ("verdict", "status"),
    [
        ("APPROVED", STATUS_SUCCESS),
        ("CHANGES_REQUESTED", STATUS_FAILURE),
        ("BLOCKED", STATUS_ERROR),
    ],
)
def test_publish_matrix_posts_comment_and_status(
    tmp_path: Path, verdict: str, status: str
) -> None:
    gh = FakeGh(head=_SHA_A)
    payload = _sealed(verdict=verdict)
    if verdict == "APPROVED":
        payload["review_evidence"] = _approved_evidence()
    with ArtifactStore(root=tmp_path / "plane") as store:
        result = publish_sealed_verdict(
            payload,
            current_head_sha=_SHA_A,
            mutate=True,
            runner=gh,
            store=store,
            require_receipt=True,
        )
    assert result.plan.action == "publish"
    assert result.plan.status_state == status
    assert result.status_posted is True
    assert result.rail_status_posted is (verdict == "APPROVED")
    assert result.publication_id is not None
    assert result.comment_url == "https://example.test/comment/1"
    # view may be skipped when current_head_sha provided; comment + status required
    kinds = [c[1] for c in gh.calls]
    assert "pr" in kinds
    assert "api" in kinds
    comment_calls = [c for c in gh.calls if c[1:3] == ["pr", "comment"]]
    assert len(comment_calls) == 1
    body = comment_calls[0][comment_calls[0].index("--body") + 1]
    assert f"VERDICT: {verdict}" in body
    if verdict == "APPROVED":
        assert "The review found no defects that block approval." in body
    else:
        assert "NO EVIDENCE SUPPLIED" in body
    status_calls = [c for c in gh.calls if c[1] == "api"]
    assert any(f"state={status}" in " ".join(c) for c in status_calls)
    assert any(DEFAULT_STATUS_CONTEXT in " ".join(c) for c in status_calls)
    if verdict == "APPROVED":
        assert any(RAIL_STATUS_CONTEXT in " ".join(c) for c in status_calls)


def test_stale_head_refuses_without_github_mutation(tmp_path: Path) -> None:
    gh = FakeGh(head=_SHA_B)
    with ArtifactStore(root=tmp_path / "plane") as store:
        result = publish_sealed_verdict(
            _sealed(verdict="BLOCKED"),
            current_head_sha=_SHA_B,
            mutate=True,
            runner=gh,
            store=store,
        )
        # Stale path must not materialize formal_review_jobs or publications.
        jobs = store.connection.execute(
            "SELECT COUNT(*) FROM formal_review_jobs"
        ).fetchone()[0]
        pubs = store.connection.execute(
            "SELECT COUNT(*) FROM github_publications"
        ).fetchone()[0]
    assert result.plan.action == "refuse_stale"
    assert result.status_posted is False
    assert result.rail_status_posted is False
    assert result.publication_id is None
    assert gh.calls == []
    assert jobs == 0
    assert pubs == 0


def test_repeat_publish_is_idempotent(tmp_path: Path) -> None:
    gh = FakeGh(head=_SHA_A)
    root = tmp_path / "plane"
    with ArtifactStore(root=root) as store:
        first = publish_sealed_verdict(
            _sealed(verdict="BLOCKED"),
            current_head_sha=_SHA_A,
            mutate=True,
            runner=gh,
            store=store,
            require_receipt=True,
        )
        assert first.status_posted is True
        receipt = lookup_publication_receipt(
            store.connection, review_id="review_deadbeef"
        )
        assert receipt is not None

    gh2 = FakeGh(head=_SHA_A)
    with ArtifactStore(root=root) as store:
        second = publish_sealed_verdict(
            _sealed(verdict="BLOCKED"),
            current_head_sha=_SHA_A,
            mutate=True,
            runner=gh2,
            store=store,
            require_receipt=True,
        )
    assert second.plan.action == "skip_idempotent"
    assert second.status_posted is False
    assert second.rail_status_posted is False
    assert gh2.calls == []


def test_dry_run_never_posts(tmp_path: Path) -> None:
    gh = FakeGh(head=_SHA_A)
    with ArtifactStore(root=tmp_path / "plane") as store:
        result = publish_sealed_verdict(
            _sealed(verdict="BLOCKED"),
            current_head_sha=_SHA_A,
            mutate=False,
            runner=gh,
            store=store,
        )
    assert result.plan.action == "publish"
    assert result.plan.mutate is False
    assert result.status_posted is False
    assert result.rail_status_posted is False
    assert gh.calls == []


def test_require_receipt_without_conn_refuses_live() -> None:
    sealed = _sealed(verdict="BLOCKED")
    plan = plan_publication(
        __import__(
            "scripts.fleet_comms.review_publication", fromlist=["parse_sealed_verdict_payload"]
        ).parse_sealed_verdict_payload(sealed),
        current_head_sha=_SHA_A,
        mutate=True,
    )
    with pytest.raises(ReviewPublisherError, match="receipt_required"):
        execute_publication(plan, runner=FakeGh(), conn=None, require_receipt=True)


def test_sealed_matches_job_fail_closed() -> None:
    from scripts.fleet_comms.review_publication import parse_sealed_verdict_payload

    sealed = parse_sealed_verdict_payload(_sealed())
    with pytest.raises(ReviewPublisherError, match="sealed_job_mismatch"):
        sealed_matches_job(
            sealed,
            review_id="review_other",
            repository=_REPO,
            pr_number=5512,
            head_sha=_SHA_A,
            gate_kind="cross-family-review",
        )


def test_sealed_payload_file_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "sealed.json"
    path.write_text(json.dumps(_sealed(verdict="BLOCKED")), encoding="utf-8")
    gh = FakeGh(head=_SHA_A)
    with ArtifactStore(root=tmp_path / "plane") as store:
        result = publish_sealed_verdict(
            path,
            current_head_sha=_SHA_A,
            mutate=True,
            runner=gh,
            store=store,
        )
    assert result.plan.verdict == "BLOCKED"
    assert result.plan.status_state == STATUS_ERROR
    assert result.status_posted is True
    assert result.rail_status_posted is False


def test_publish_refuses_evidence_free_approved_without_github_mutation(
    tmp_path: Path,
) -> None:
    gh = FakeGh(head=_SHA_A)
    with ArtifactStore(root=tmp_path / "plane") as store:
        with pytest.raises(
            ReviewPublisherError, match="approved_review_evidence_required"
        ):
            publish_sealed_verdict(
                _sealed(),
                current_head_sha=_SHA_A,
                mutate=True,
                runner=gh,
                store=store,
            )
    assert gh.calls == []


def test_publish_from_review_id_via_accept_sealed(tmp_path: Path) -> None:
    """Sol milestone 2: publish without CLI-supplied provenance after accept."""
    from scripts.fleet_comms.formal_review_jobs import FormalReviewJobService

    root = tmp_path / "plane"
    gh = FakeGh(head=_SHA_A)
    with FormalReviewJobService(root=root) as svc:
        job = svc.create_job(_REPO, 5512, _SHA_A, "cross-family-review")
        svc.accept_sealed_verdict(
            job.review_id,
            {
                "review_id": job.review_id,
                "repository": _REPO,
                "pr_number": 5512,
                "head_sha": _SHA_A,
                "gate_kind": "cross-family-review",
                "verdict": "APPROVED",
                "model": "gpt-5.6-terra",
                "family": "openai",
                "harness": "codex",
                "review_evidence": _approved_evidence(),
            },
        )
        sealed = svc.load_sealed_verdict(job.review_id)
        result = publish_sealed_verdict(
            sealed,
            current_head_sha=_SHA_A,
            mutate=True,
            runner=gh,
            store=svc.store,
            require_receipt=True,
        )
    assert result.status_posted is True
    assert result.rail_status_posted is True
    assert result.plan.verdict == "APPROVED"
    assert result.publication_id is not None


class _ReceiptStore:
    source_id = "test-operator-api"
    source_kind = "api"

    def __init__(self, receipt: dict[str, object]) -> None:
        self.receipt = receipt

    def fetch_rail_approval_receipt(self, _receipt_id: str) -> dict[str, object]:
        return dict(self.receipt)


def _rail_resolver(path: str) -> rail_path_guard.ApprovedRailApprovalReceiptResolver:
    receipt = {
        "schema_version": "rail-approval-receipt.v1",
        "receipt_id": "rail-approval-" + "1" * 32,
        "issuer": "operator",
        "issued_at": "2026-07-31T00:00:00Z",
        "expires_at": "2026-08-01T00:00:00Z",
        "action": "rail-path-mutation",
        "task_id": "pr-5512",
        "head_sha": _SHA_A,
        "owned_paths": [path],
    }
    return rail_path_guard.ApprovedRailApprovalReceiptResolver(
        _ReceiptStore(receipt),
        now=lambda: datetime(2026, 7, 31, 1, tzinfo=UTC),
    )


def test_approved_rail_pr_requires_production_receipt_before_review_status(
    tmp_path: Path,
) -> None:
    path = "agents_extensions/shared/rules/model-assignment.md"
    gh = FakeGh(head=_SHA_A, files=[path])
    payload = _sealed(review_evidence=_approved_evidence())

    with ArtifactStore(root=tmp_path / "plane") as store:
        with pytest.raises(ReviewPublisherError, match="rail_authorization_refused"):
            publish_sealed_verdict(
                payload,
                current_head_sha=_SHA_A,
                mutate=True,
                runner=gh,
                store=store,
                require_receipt=True,
            )

    calls = [" ".join(call) for call in gh.calls]
    assert any(f"context={RAIL_STATUS_CONTEXT}" in call and "state=failure" in call for call in calls)
    assert not any(call[1:3] == ["pr", "comment"] for call in gh.calls)
    assert not any(f"context={DEFAULT_STATUS_CONTEXT}" in call for call in calls)


def test_approved_rail_pr_publishes_both_exact_head_statuses(tmp_path: Path) -> None:
    path = "agents_extensions/shared/rules/model-assignment.md"
    receipt_id = "rail-approval-" + "1" * 32
    gh = FakeGh(
        head=_SHA_A,
        files=[path],
        body=f"Summary\n\nRail-Approval-Receipt: {receipt_id}\n",
    )
    payload = _sealed(review_evidence=_approved_evidence())

    with ArtifactStore(root=tmp_path / "plane") as store:
        result = publish_sealed_verdict(
            payload,
            current_head_sha=_SHA_A,
            mutate=True,
            runner=gh,
            store=store,
            require_receipt=True,
            rail_receipt_resolver=_rail_resolver(path),
        )
        rail_receipt = lookup_publication_receipt(
            store.connection,
            review_id="review_deadbeef",
            status_context=RAIL_STATUS_CONTEXT,
        )

    calls = [" ".join(call) for call in gh.calls]
    assert result.status_posted is True
    assert result.rail_status_posted is True
    assert result.rail_status_reason == "rail_approval_verified"
    assert result.rail_publication_id is not None
    assert rail_receipt is not None
    assert any(f"context={RAIL_STATUS_CONTEXT}" in call and "state=success" in call for call in calls)
    assert any(f"context={DEFAULT_STATUS_CONTEXT}" in call and "state=success" in call for call in calls)


def test_approved_publication_refuses_when_expected_head_is_stale(
    tmp_path: Path,
) -> None:
    gh = FakeGh(head=_SHA_B)
    payload = _sealed(review_evidence=_approved_evidence())

    with ArtifactStore(root=tmp_path / "plane") as store:
        with pytest.raises(ReviewPublisherError, match="stale_rail_status_head"):
            publish_sealed_verdict(
                payload,
                current_head_sha=_SHA_A,
                mutate=True,
                runner=gh,
                store=store,
                require_receipt=True,
            )

    assert not any(call[1:3] == ["pr", "comment"] for call in gh.calls)
    assert not any("/statuses/" in " ".join(call) for call in gh.calls)


class _MovingHeadGh(FakeGh):
    def __init__(self) -> None:
        super().__init__(head=_SHA_A)
        self._head_reads = 0

    def __call__(
        self, command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if len(command) >= 3 and command[1:3] == ["pr", "view"]:
            self._head_reads += 1
            self.head = _SHA_A if self._head_reads == 1 else _SHA_B
        return super().__call__(command, **kwargs)


def test_approved_publication_refuses_if_head_moves_during_path_snapshot(
    tmp_path: Path,
) -> None:
    gh = _MovingHeadGh()
    payload = _sealed(review_evidence=_approved_evidence())

    with ArtifactStore(root=tmp_path / "plane") as store:
        with pytest.raises(ReviewPublisherError, match="rail_snapshot_head_changed"):
            publish_sealed_verdict(
                payload,
                current_head_sha=_SHA_A,
                mutate=True,
                runner=gh,
                store=store,
                require_receipt=True,
            )

    assert not any(call[1:3] == ["pr", "comment"] for call in gh.calls)
    assert not any("/statuses/" in " ".join(call) for call in gh.calls)


def test_approved_publication_refuses_incomplete_paginated_path_snapshot(
    tmp_path: Path,
) -> None:
    gh = FakeGh(head=_SHA_A, files=["README.md"], changed_files=2)
    payload = _sealed(review_evidence=_approved_evidence())

    with ArtifactStore(root=tmp_path / "plane") as store:
        with pytest.raises(ReviewPublisherError, match="rail_snapshot_file_count_mismatch"):
            publish_sealed_verdict(
                payload,
                current_head_sha=_SHA_A,
                mutate=True,
                runner=gh,
                store=store,
                require_receipt=True,
            )

    files_call = next(call for call in gh.calls if "/pulls/" in call[-1])
    assert "--paginate" in files_call
    assert "--slurp" in files_call
    assert "per_page=100" in files_call[-1]
    assert not any("/statuses/" in " ".join(call) for call in gh.calls)


def test_approved_publication_treats_previous_rename_path_as_rail(
    tmp_path: Path,
) -> None:
    gh = FakeGh(
        head=_SHA_A,
        file_items=[
            {
                "filename": "docs/retired-model-assignment.md",
                "previous_filename": "agents_extensions/shared/rules/model-assignment.md",
            }
        ],
    )
    payload = _sealed(review_evidence=_approved_evidence())

    with ArtifactStore(root=tmp_path / "plane") as store:
        with pytest.raises(ReviewPublisherError, match="rail_authorization_refused"):
            publish_sealed_verdict(
                payload,
                current_head_sha=_SHA_A,
                mutate=True,
                runner=gh,
                store=store,
                require_receipt=True,
            )

    calls = [" ".join(call) for call in gh.calls]
    assert any(f"context={RAIL_STATUS_CONTEXT}" in call for call in calls)
    assert not any(f"context={DEFAULT_STATUS_CONTEXT}" in call for call in calls)
