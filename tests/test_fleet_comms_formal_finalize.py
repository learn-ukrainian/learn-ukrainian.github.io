"""Tests for formal-job accept finalize glue (#5512)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.fleet_comms.formal_review_finalize import (
    FormalReviewFinalizeError,
    finalize_formal_review_verdict,
    resolve_verdict_token,
)
from scripts.fleet_comms.formal_review_jobs import FormalReviewJobService

_SHA = "a" * 40
_REPO = "learn-ukrainian/learn-ukrainian.github.io"


class FakeGh:
    def __init__(self, *, head: str = _SHA) -> None:
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
                command, 0, stdout="https://example.test/c\n", stderr=""
            )
        if len(command) >= 2 and command[1] == "api":
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="unexpected")


def test_resolve_verdict_token_sources(tmp_path: Path) -> None:
    assert resolve_verdict_token(verdict="approved") == "APPROVED"
    assert (
        resolve_verdict_token(verdict_text="notes\nVERDICT: CHANGES_REQUESTED\n")
        == "CHANGES_REQUESTED"
    )
    f = tmp_path / "f.json"
    f.write_text(json.dumps({"verdict": "BLOCKED"}), encoding="utf-8")
    assert resolve_verdict_token(findings_path=f) == "BLOCKED"
    with pytest.raises(FormalReviewFinalizeError, match="verdict_required"):
        resolve_verdict_token()


def test_finalize_creates_job_and_accepts(tmp_path: Path) -> None:
    root = tmp_path / "plane"
    gh = FakeGh()
    result = finalize_formal_review_verdict(
        pr_number=5571,
        model="zai-coding-plan/glm-5.2",
        family="zhipu",
        harness="opencode",
        verdict="APPROVED",
        plane_root=root,
        runner=gh,
    )
    assert result.job_created is True
    assert result.verdict == "APPROVED"
    assert result.head_sha == _SHA
    assert result.sealed_verdict_artifact_id is not None
    assert result.published is False
    with FormalReviewJobService(root=root) as svc:
        job = svc.get_job(result.review_id)
        assert job.has_sealed_verdict
        sealed = svc.load_sealed_verdict(result.review_id)
        assert sealed.model == "zai-coding-plan/glm-5.2"
        assert sealed.family == "zhipu"


def test_finalize_reuses_job_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "plane"
    gh = FakeGh()
    first = finalize_formal_review_verdict(
        pr_number=100,
        model="m",
        family="f",
        harness="h",
        verdict="APPROVED",
        plane_root=root,
        runner=gh,
    )
    second = finalize_formal_review_verdict(
        pr_number=100,
        model="m",
        family="f",
        harness="h",
        verdict="APPROVED",
        plane_root=root,
        runner=gh,
    )
    assert first.review_id == second.review_id
    assert second.job_created is False


def test_finalize_publish_dry_run_and_live(tmp_path: Path) -> None:
    root = tmp_path / "plane"
    gh = FakeGh()
    dry = finalize_formal_review_verdict(
        pr_number=200,
        model="m",
        family="f",
        harness="h",
        verdict="CHANGES_REQUESTED",
        plane_root=root,
        runner=gh,
        dry_run_publish=True,
    )
    assert dry.published is False
    assert dry.publication_summary is not None
    assert "posted=false" in dry.publication_summary or "action=" in dry.publication_summary

    gh2 = FakeGh()
    live = finalize_formal_review_verdict(
        pr_number=201,
        model="m",
        family="f",
        harness="h",
        verdict="APPROVED",
        plane_root=root,
        runner=gh2,
        publish=True,
    )
    assert live.published is True
    assert any(c[1:3] == ["pr", "comment"] for c in gh2.calls)


def test_cli_formal_job_accept(tmp_path: Path) -> None:
    from scripts.fleet_comms.cli import main

    root = tmp_path / "plane"
    # Inject head via --head-sha to avoid real gh
    rc = main(
        [
            "formal-job",
            "accept",
            "--pr",
            "300",
            "--verdict",
            "APPROVED",
            "--model",
            "m",
            "--family",
            "f",
            "--harness",
            "h",
            "--head-sha",
            _SHA,
            "--root",
            str(root),
        ]
    )
    assert rc == 0
    with FormalReviewJobService(root=root) as svc:
        jobs = svc.list_jobs(pr=300)
        assert len(jobs) == 1
        assert jobs[0].has_sealed_verdict
