from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.orchestration import integration_sweep

NOW = datetime(2026, 8, 9, 12, tzinfo=UTC)
HEAD = "a" * 40


def _report(*, unique: bool = True, epics: list[int] | None = None) -> dict:
    return {
        "generated_at": int(time.time()),
        "effective_membership": {
            "42": {
                "epics": epics if epics is not None else [4707],
                "streams": ["infra"],
                "via": "native",
                "unique_stream": unique,
            }
        },
        "open_issue_numbers": [42],
    }


def _pr(**changes: object) -> dict:
    result = {
        "number": 99,
        "isDraft": False,
        "autoMergeRequest": None,
        "assignees": [],
        "updatedAt": (NOW - timedelta(hours=1, minutes=1)).isoformat(),
        "reviewDecision": "APPROVED",
        "headRefOid": HEAD,
        "reviews": [{"state": "APPROVED", "commit": {"oid": HEAD}}],
        "statusCheckRollup": [
            {
                "name": "CI Gate",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "startedAt": (NOW - timedelta(hours=1)).isoformat(),
                "completedAt": (NOW - timedelta(minutes=59)).isoformat(),
            }
        ],
        "body": "Refs #42\n",
        "closingIssuesReferences": [],
    }
    result.update(changes)
    return result


def test_decide_accepts_only_a_fully_proven_abandoned_pr() -> None:
    decision = integration_sweep.decide(_pr(), _report(), ["CI Gate"], now=NOW)

    assert decision.eligible is True
    assert decision.reason == "stream_epic_4707"


def test_decide_refuses_an_assigned_pr_even_when_every_other_gate_passes() -> None:
    decision = integration_sweep.decide(_pr(assignees=[{"login": "owner"}]), _report(), ["CI Gate"], now=NOW)

    assert decision == integration_sweep.Decision(99, False, "active_owner_assigned")


def test_decide_refuses_a_stale_approval() -> None:
    decision = integration_sweep.decide(
        _pr(reviews=[{"state": "APPROVED", "commit": {"oid": "b" * 40}}]), _report(), ["CI Gate"], now=NOW
    )

    assert decision == integration_sweep.Decision(99, False, "current_head_review_missing")


def test_decide_uses_the_latest_required_check_run() -> None:
    old_success = _pr()["statusCheckRollup"][0]
    pending = {
        "name": "CI Gate",
        "status": "IN_PROGRESS",
        "conclusion": "",
        "startedAt": (NOW - timedelta(minutes=1)).isoformat(),
        "completedAt": None,
    }
    decision = integration_sweep.decide(_pr(statusCheckRollup=[old_success, pending]), _report(), ["CI Gate"], now=NOW)

    assert decision == integration_sweep.Decision(99, False, "required_ci_not_green")


def test_decide_refuses_missing_or_ambiguous_membership() -> None:
    missing = integration_sweep.decide(_pr(body="No issue link"), _report(), ["CI Gate"], now=NOW)
    ambiguous = integration_sweep.decide(_pr(), _report(unique=False, epics=[4707, 5703]), ["CI Gate"], now=NOW)

    assert missing == integration_sweep.Decision(99, False, "no_explicit_issue_reference")
    assert ambiguous == integration_sweep.Decision(99, False, "ambiguous_membership")


def test_decide_accepts_an_exact_head_formal_review_comment() -> None:
    comment = {
        "body": (
            "## Cross-family review (AGY / Gemini) — review of record\n\n"
            f"**Head:** `{HEAD}`\n"
            "**Reviewer family:** Gemini (AGY) — outside OpenAI author family\n\n"
            "### VERDICT: APPROVED\n"
        )
    }

    decision = integration_sweep.decide(
        _pr(reviewDecision="", reviews=[]),
        _report(),
        ["CI Gate"],
        now=NOW,
        comments=[comment],
    )

    assert decision == integration_sweep.Decision(99, True, "stream_epic_4707")


def test_run_arms_only_eligible_prs(monkeypatch) -> None:
    class FakeAdapter:
        repo_root = Path(".")

        def __init__(self) -> None:
            self.armed: list[int] = []

        def required_check_contexts(self, _repository: str) -> list[str]:
            return ["CI Gate"]

        def list_open_prs(self, _repository: str) -> list[dict]:
            return [_pr(), _pr(number=100, isDraft=True)]

        def arm_auto_merge(self, _repository: str, number: int) -> None:
            self.armed.append(number)

    adapter = FakeAdapter()
    monkeypatch.setattr(integration_sweep.issue_stream_audit, "run_audit", lambda _root: _report())

    decisions = integration_sweep.run(adapter, "org/repo", apply=True, now=NOW)

    assert [decision.eligible for decision in decisions] == [True, False]
    assert adapter.armed == [99]


def test_run_is_read_only_without_apply(monkeypatch) -> None:
    class FakeAdapter:
        repo_root = Path(".")

        def required_check_contexts(self, _repository: str) -> list[str]:
            return ["CI Gate"]

        def list_open_prs(self, _repository: str) -> list[dict]:
            return [_pr()]

        def arm_auto_merge(self, _repository: str, _number: int) -> None:
            raise AssertionError("dry run must not mutate GitHub")

    monkeypatch.setattr(integration_sweep.issue_stream_audit, "run_audit", lambda _root: _report())

    decisions = integration_sweep.run(FakeAdapter(), "org/repo", apply=False, now=NOW)

    assert decisions == [integration_sweep.Decision(99, True, "stream_epic_4707")]


def test_required_check_contexts_never_calls_branch_protection() -> None:
    """GITHUB_TOKEN cannot call branches/.../protection (administration / HTTP 403)."""

    def runner(args: list[str]) -> str:
        joined = " ".join(args)
        assert "/branches/" not in joined and "/protection" not in joined, joined
        assert "graphql" in args
        return json.dumps(
            {
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": [
                                {
                                    "commits": {
                                        "nodes": [
                                            {
                                                "commit": {
                                                    "statusCheckRollup": {
                                                        "contexts": {
                                                            "nodes": [
                                                                {
                                                                    "__typename": "CheckRun",
                                                                    "name": "CI Gate",
                                                                    "isRequired": True,
                                                                },
                                                                {
                                                                    "__typename": "CheckRun",
                                                                    "name": "advisory",
                                                                    "isRequired": False,
                                                                },
                                                            ]
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        )

    adapter = integration_sweep.GitHubAdapter(Path("."), runner=runner)

    assert adapter.required_check_contexts("org/repo") == ["CI Gate"]


def test_required_check_contexts_falls_back_to_ci_gate_on_graphql_403() -> None:
    """Adapter 403 on required-context lookup must not crash; CI Gate remains."""

    def runner(args: list[str]) -> str:
        joined = " ".join(args)
        assert "/branches/" not in joined and "/protection" not in joined, joined
        raise integration_sweep.SweepError(
            "gh: Resource not accessible by integration (HTTP 403)"
        )

    adapter = integration_sweep.GitHubAdapter(Path("."), runner=runner)

    assert adapter.required_check_contexts("org/repo") == ["CI Gate"]


def test_run_survives_required_context_403_via_documented_default(monkeypatch) -> None:
    class SoftAdapter:
        repo_root = Path(".")

        def required_check_contexts(self, repository: str) -> list[str]:
            # Simulate the real adapter falling back after a 403.
            return integration_sweep.GitHubAdapter(
                Path("."),
                runner=lambda _args: (_ for _ in ()).throw(
                    integration_sweep.SweepError(
                        "gh: Resource not accessible by integration (HTTP 403)"
                    )
                ),
            ).required_check_contexts(repository)

        def list_open_prs(self, _repository: str) -> list[dict]:
            return [_pr()]

        def arm_auto_merge(self, _repository: str, _number: int) -> None:
            raise AssertionError("dry run must not mutate GitHub")

    monkeypatch.setattr(integration_sweep.issue_stream_audit, "run_audit", lambda _root: _report())

    decisions = integration_sweep.run(SoftAdapter(), "org/repo", apply=False, now=NOW)

    assert decisions == [integration_sweep.Decision(99, True, "stream_epic_4707")]


def test_main_schedule_soft_skips_http_403(monkeypatch, capsys) -> None:
    monkeypatch.setenv("EVENT_NAME", "schedule")

    def boom(*_args, **_kwargs):
        raise integration_sweep.SweepError(
            "gh: Resource not accessible by integration (HTTP 403)"
        )

    monkeypatch.setattr(integration_sweep, "run", boom)

    assert integration_sweep.main(["--repo", "org/repo", "--apply"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("integration sweep skipped:")
    assert "HTTP 403" in out


def test_main_non_schedule_still_refuses_http_403(monkeypatch, capsys) -> None:
    monkeypatch.setenv("EVENT_NAME", "workflow_dispatch")
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)

    def boom(*_args, **_kwargs):
        raise integration_sweep.SweepError(
            "gh: Resource not accessible by integration (HTTP 403)"
        )

    monkeypatch.setattr(integration_sweep, "run", boom)

    assert integration_sweep.main(["--repo", "org/repo"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("integration sweep refused:")
    assert "HTTP 403" in out