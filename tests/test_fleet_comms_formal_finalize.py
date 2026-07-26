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
_MODEL = "glm-5.2"


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


def test_finalize_refuses_explicit_approved_without_evidence(tmp_path: Path) -> None:
    gh = FakeGh()
    with pytest.raises(
        FormalReviewFinalizeError, match="approved_review_evidence_required"
    ):
        finalize_formal_review_verdict(
            pr_number=5571,
            model=_MODEL,
            family="zhipu",
            harness="opencode",
            verdict="APPROVED",
            plane_root=tmp_path / "plane",
            runner=gh,
        )
    assert gh.calls == []


def test_finalize_accepts_approved_findings_and_seals_evidence(tmp_path: Path) -> None:
    root = tmp_path / "plane"
    findings_path = tmp_path / "review-findings.json"
    findings_path.write_text(
        json.dumps(
            {
                "schema_version": "code-review-findings.v1",
                "overall": {
                    "correctness": "correct",
                    "explanation": "The reviewed change has no blocking defects.",
                    "confidence": 0.95,
                },
                "findings": [],
            }
        ),
        encoding="utf-8",
    )
    gh = FakeGh()
    result = finalize_formal_review_verdict(
        pr_number=5571,
        model=_MODEL,
        family="zhipu",
        harness="opencode",
        findings_path=findings_path,
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
        assert sealed.model == _MODEL
        assert sealed.family == "zhipu"
        assert sealed.review_evidence is not None
        assert sealed.review_evidence.explanation == "The reviewed change has no blocking defects."


def test_finalize_reuses_job_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "plane"
    gh = FakeGh()
    first = finalize_formal_review_verdict(
        pr_number=100,
        model=_MODEL,
        family="zhipu",
        harness="opencode",
        verdict="BLOCKED",
        plane_root=root,
        runner=gh,
    )
    second = finalize_formal_review_verdict(
        pr_number=100,
        model=_MODEL,
        family="zhipu",
        harness="opencode",
        verdict="BLOCKED",
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
        model=_MODEL,
        family="zhipu",
        harness="opencode",
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
        model=_MODEL,
        family="zhipu",
        harness="opencode",
        verdict="BLOCKED",
        plane_root=root,
        runner=gh2,
        publish=True,
    )
    assert live.published is True
    assert any(c[1:3] == ["pr", "comment"] for c in gh2.calls)


def test_finalize_preserves_canonical_evidence_for_publication(tmp_path: Path) -> None:
    root = tmp_path / "plane"
    findings_path = tmp_path / "review-findings.json"
    findings_path.write_text(
        json.dumps(
            {
                "schema_version": "code-review-findings.v1",
                "overall": {
                    "correctness": "incorrect",
                    "explanation": "The shared cache is retained between requests.",
                    "confidence": 0.95,
                },
                "findings": [
                    {
                        "id": "F001",
                        "title": "Shared cache survives requests",
                        "body": "The mutable cache is reused by the next request.",
                        "priority": "P1",
                        "confidence": 0.9,
                        "category": "regression",
                        "location": {
                            "path": "scripts/cache.py",
                            "start_line": 19,
                            "end_line": 19,
                            "claim_type": "present",
                        },
                        "verbatim": "cache.update(values)",
                        "why_wrong": "Requests observe stale entries.",
                        "smallest_fix": "Construct a new cache per request.",
                        "sources": ["none"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    gh = FakeGh()

    result = finalize_formal_review_verdict(
        pr_number=202,
        model=_MODEL,
        family="zhipu",
        harness="opencode",
        findings_path=findings_path,
        plane_root=root,
        runner=gh,
        publish=True,
    )

    assert result.verdict == "CHANGES_REQUESTED"
    with FormalReviewJobService(root=root) as service:
        sealed = service.load_sealed_verdict(result.review_id)
    assert sealed.review_evidence is not None
    assert sealed.review_evidence.explanation == "The shared cache is retained between requests."
    comment = next(call for call in gh.calls if call[1:3] == ["pr", "comment"])
    body = comment[comment.index("--body") + 1]
    assert "scripts/cache.py:19" in body
    assert "The mutable cache is reused by the next request." in body


@pytest.mark.parametrize("model", ["glm-5.2", "gemini-3.1-pro"])
def test_finalize_accepts_catalog_model_and_alias(tmp_path: Path, model: str) -> None:
    result = finalize_formal_review_verdict(
        pr_number=302,
        model=model,
        family="zhipu",
        harness="opencode",
        verdict="BLOCKED",
        plane_root=tmp_path / model,
        head_sha=_SHA,
    )
    assert result.verdict == "BLOCKED"


def test_finalize_refuses_unknown_reviewer_model(tmp_path: Path) -> None:
    with pytest.raises(
        FormalReviewFinalizeError, match=r"unknown_reviewer_model: 'gemini-1.5-pro'"
    ):
        finalize_formal_review_verdict(
            pr_number=301,
            model="gemini-1.5-pro",
            family="google",
            harness="agy",
            verdict="BLOCKED",
            plane_root=tmp_path / "plane",
            head_sha=_SHA,
        )


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
            "BLOCKED",
            "--model",
            _MODEL,
            "--family",
            "zhipu",
            "--harness",
            "opencode",
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
