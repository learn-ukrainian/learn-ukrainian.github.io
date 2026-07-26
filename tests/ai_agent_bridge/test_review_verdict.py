"""Thin GitHub verdict publisher tests."""

from __future__ import annotations

import json
import subprocess

import pytest
from ai_agent_bridge import _review_verdict as publisher
from ai_agent_bridge._review_safety import ReviewSafetyError


def test_publish_review_verdict_dry_run_is_thin_and_does_not_post() -> None:
    calls: list[list[str]] = []

    def fake_runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="deadbeef\n", stderr="")

    summary = publisher.publish_review_verdict(
        pr=5458,
        verdict="APPROVED",
        model="gpt-5.6-terra",
        family="openai",
        harness="codex",
        dry_run=True,
        runner=fake_runner,
    )

    assert calls == [["gh", "pr", "view", "5458", "--json", "headRefOid", "--jq", ".headRefOid"]]
    assert "pr=5458" in summary
    assert "head_sha=deadbeef" in summary
    assert len(summary.encode("utf-8")) <= publisher.MAX_VERDICT_SUMMARY_BYTES


def test_publish_review_verdict_marks_legacy_verdict_without_evidence() -> None:
    calls: list[list[str]] = []

    def fake_runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[2] == "view":
            return subprocess.CompletedProcess(command, 0, stdout="abc123\n", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    publisher.publish_review_verdict(
        pr=99,
        verdict="CHANGES_REQUESTED",
        model="glm-5.2",
        family="zhipu",
        harness="opencode",
        runner=fake_runner,
    )

    assert len(calls) == 2
    assert calls[1][:4] == ["gh", "pr", "comment", "99"]
    comment = calls[1][5]
    assert "VERDICT: CHANGES_REQUESTED" in comment
    assert "Head SHA: abc123" in comment
    assert "model=glm-5.2" in comment
    assert "NO EVIDENCE SUPPLIED" in comment


def test_publish_review_verdict_posts_structured_explanation_and_findings() -> None:
    calls: list[list[str]] = []

    def fake_runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[2] == "view":
            return subprocess.CompletedProcess(command, 0, stdout="abc123\n", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    publisher.publish_review_verdict(
        pr=99,
        verdict="CHANGES_REQUESTED",
        model="claude-sonnet-5",
        family="anthropic",
        harness="claude",
        review_evidence={
            "schema_version": "code-review-findings.v1",
            "overall": {
                "correctness": "incorrect",
                "explanation": "The shared index leaks state between calls.",
                "confidence": 0.95,
            },
            "findings": [
                {
                    "id": "F001",
                    "title": "Shared index state leaks",
                    "body": "A mutation survives into the next review request.",
                    "priority": "P1",
                    "confidence": 0.9,
                    "category": "regression",
                    "location": {
                        "path": "scripts/index.py",
                        "start_line": 42,
                        "end_line": 42,
                        "claim_type": "present",
                    },
                    "verbatim": "INDEX.append(item)",
                    "why_wrong": "The next request observes stale state.",
                    "smallest_fix": "Create an index for each request.",
                    "sources": ["none"],
                }
            ],
        },
        runner=fake_runner,
    )

    comment = calls[1][5]
    assert "The shared index leaks state between calls." in comment
    assert "scripts/index.py:42" in comment
    assert "Severity: P1" in comment
    assert "A mutation survives into the next review request." in comment


def test_verdict_from_findings_json_requires_explicit_verdict(tmp_path) -> None:
    findings = tmp_path / "findings.json"
    findings.write_text(
        json.dumps({"verdict": "BLOCKED", "findings": ["long body"]}),
        encoding="utf-8",
    )
    assert publisher.verdict_from_findings_json(findings) == "BLOCKED"

    findings.write_text('{"findings": []}', encoding="utf-8")
    with pytest.raises(ReviewSafetyError, match="missing_verdict"):
        publisher.verdict_from_findings_json(findings)
