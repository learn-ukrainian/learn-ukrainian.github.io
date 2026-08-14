from __future__ import annotations

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


def test_required_check_contexts_returns_documented_default_without_gh() -> None:
    """GitHub removed rollup ``isRequired`` (#6748) and branch protection is admin-only (#6717)."""

    def runner(args: list[str]) -> str:
        raise AssertionError(f"required-context lookup must not invoke gh: {' '.join(args)}")

    adapter = integration_sweep.GitHubAdapter(Path("."), runner=runner)

    assert adapter.required_check_contexts("org/repo") == ["CI Gate"]


def test_run_never_calls_gh_without_a_pr_number(monkeypatch) -> None:
    """A PR without a usable number is refused and never reaches a gh call."""

    class GuardedAdapter:
        repo_root = Path(".")

        def required_check_contexts(self, _repository: str) -> list[str]:
            return ["CI Gate"]

        def list_open_prs(self, _repository: str) -> list[dict]:
            return [_pr(number=0), _pr(number=100, reviewDecision="", reviews=[], body="Refs #42\n")]

        def comments(self, _repository: str, number: int) -> list[dict]:
            assert integration_sweep._is_usable_pr_number(number), number
            return []

        def arm_auto_merge(self, _repository: str, number: int) -> None:
            raise AssertionError(f"no PR should be armed: {number}")

    monkeypatch.setattr(integration_sweep.issue_stream_audit, "run_audit", lambda _root: _report())

    decisions = integration_sweep.run(GuardedAdapter(), "org/repo", apply=True, now=NOW)

    assert decisions == [
        integration_sweep.Decision(0, False, "invalid_pr_number"),
        integration_sweep.Decision(100, False, "current_head_review_missing"),
    ]


def test_run_skips_comments_and_merge_when_number_unusable(monkeypatch) -> None:
    """Even a pathological review-missing decision never invokes gh without a number."""

    class GuardedAdapter:
        repo_root = Path(".")

        def required_check_contexts(self, _repository: str) -> list[str]:
            return ["CI Gate"]

        def list_open_prs(self, _repository: str) -> list[dict]:
            return [_pr(number=0)]

        def comments(self, _repository: str, number: int) -> list[dict]:
            raise AssertionError(f"comments must not be fetched for number {number!r}")

        def arm_auto_merge(self, _repository: str, number: int) -> None:
            raise AssertionError(f"auto-merge must not be armed for number {number!r}")

    def fake_decide(pr, report, contexts, *, now, comments=None):
        del pr, report, contexts, now, comments
        return integration_sweep.Decision(0, True, "current_head_review_missing")

    monkeypatch.setattr(integration_sweep, "decide", fake_decide)
    monkeypatch.setattr(integration_sweep.issue_stream_audit, "run_audit", lambda _root: _report())

    decisions = integration_sweep.run(GuardedAdapter(), "org/repo", apply=True, now=NOW)

    assert decisions == [integration_sweep.Decision(0, True, "current_head_review_missing")]


def test_main_empty_sweep_noops_exit_zero(monkeypatch, capsys) -> None:
    """With nothing to comment on or apply, the sweep exits 0."""
    monkeypatch.setattr(integration_sweep, "run", lambda _adapter, _repository, **_kwargs: [])

    assert integration_sweep.main(["--repo", "org/repo", "--apply"]) == 0
    assert capsys.readouterr().out.strip() == "[]"


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
