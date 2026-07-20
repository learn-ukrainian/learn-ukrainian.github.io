"""Fake-GitHub tests for Fleet Comms PR-G live publisher (#5512)."""

from __future__ import annotations

import json
import subprocess
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
        "model": "claude-opus-4-6",
        "family": "anthropic",
        "harness": "claude",
    }
    base.update(overrides)
    return base


class FakeGh:
    """Records gh invocations and returns scripted responses."""

    def __init__(self, *, head: str = _SHA_A) -> None:
        self.head = head
        self.calls: list[list[str]] = []

    def __call__(
        self, command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(command))
        if len(command) >= 3 and command[1] == "pr" and command[2] == "view":
            return subprocess.CompletedProcess(command, 0, stdout=f"{self.head}\n", stderr="")
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
    with ArtifactStore(root=tmp_path / "plane") as store:
        result = publish_sealed_verdict(
            _sealed(verdict=verdict),
            current_head_sha=_SHA_A,
            mutate=True,
            runner=gh,
            store=store,
            require_receipt=True,
        )
    assert result.plan.action == "publish"
    assert result.plan.status_state == status
    assert result.status_posted is True
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
    assert "findings" not in body.lower()
    status_calls = [c for c in gh.calls if c[1] == "api"]
    assert any(f"state={status}" in " ".join(c) for c in status_calls)
    assert any(DEFAULT_STATUS_CONTEXT in " ".join(c) for c in status_calls)


def test_stale_head_refuses_without_github_mutation(tmp_path: Path) -> None:
    gh = FakeGh(head=_SHA_B)
    with ArtifactStore(root=tmp_path / "plane") as store:
        result = publish_sealed_verdict(
            _sealed(),
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
    assert result.publication_id is None
    assert gh.calls == []
    assert jobs == 0
    assert pubs == 0


def test_repeat_publish_is_idempotent(tmp_path: Path) -> None:
    gh = FakeGh(head=_SHA_A)
    root = tmp_path / "plane"
    with ArtifactStore(root=root) as store:
        first = publish_sealed_verdict(
            _sealed(),
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
            _sealed(),
            current_head_sha=_SHA_A,
            mutate=True,
            runner=gh2,
            store=store,
            require_receipt=True,
        )
    assert second.plan.action == "skip_idempotent"
    assert second.status_posted is False
    assert gh2.calls == []


def test_dry_run_never_posts(tmp_path: Path) -> None:
    gh = FakeGh(head=_SHA_A)
    with ArtifactStore(root=tmp_path / "plane") as store:
        result = publish_sealed_verdict(
            _sealed(),
            current_head_sha=_SHA_A,
            mutate=False,
            runner=gh,
            store=store,
        )
    assert result.plan.action == "publish"
    assert result.plan.mutate is False
    assert result.status_posted is False
    assert gh.calls == []


def test_require_receipt_without_conn_refuses_live() -> None:
    sealed = _sealed()
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
