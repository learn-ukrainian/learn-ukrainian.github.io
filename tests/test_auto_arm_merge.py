"""Decision and workflow coverage for #7539 auto-arming."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.ci import auto_arm_merge

HEAD = "a" * 40
_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "auto-arm-merge.yml"


def _check(
    name: str,
    conclusion: str = "SUCCESS",
    *,
    status: str = "COMPLETED",
    started_at: str = "2026-08-31T10:00:00Z",
    details_url: str | None = None,
) -> dict:
    result = {
        "name": name,
        "workflowName": "CI",
        "status": status,
        "conclusion": conclusion,
        "startedAt": started_at,
    }
    if details_url is not None:
        result["detailsUrl"] = details_url
    return result


def _pr(**changes: object) -> dict:
    result = {
        "number": 7539,
        "state": "OPEN",
        "baseRefName": "main",
        "isDraft": False,
        "labels": [{"name": "automerge-ok"}],
        "headRefOid": HEAD,
        "autoMergeRequest": None,
        "statusCheckRollup": [
            _check("CF attest"),
            _check("CI Gate", started_at="2026-08-31T10:01:00Z"),
            _check("Ruff", started_at="2026-08-31T10:02:00Z"),
        ],
    }
    result.update(changes)
    return result


def _failed_cf_pr() -> dict:
    run_url = "https://github.com/org/repo/actions/runs/987654321/job/123456789"
    return _pr(
        statusCheckRollup=[
            _check("CF attest", "FAILURE", details_url=run_url),
            _check("CI Gate", "FAILURE", started_at="2026-08-31T10:01:00Z", details_url=run_url),
            _check("Ruff", started_at="2026-08-31T10:02:00Z"),
        ]
    )


def _attestation(head: str = HEAD, *, created_at: str = "2026-08-31T10:00:01Z") -> dict:
    return {
        "created_at": created_at,
        "body": (
            f"**VERDICT: APPROVE**\n\nCross-family review of record\nReviewer family: Anthropic\nAt exact head {head}"
        ),
    }


@pytest.mark.parametrize(
    ("pr", "reason"),
    [
        (_pr(labels=[]), "opt_in_label_missing"),
        (_pr(labels=[{"name": "automerge-ok"}, {"name": "hold"}]), "blocking_label"),
        (_pr(labels=[{"name": "automerge-ok"}, {"name": "do-not-merge"}]), "blocking_label"),
        (_pr(isDraft=True), "draft_or_unknown"),
        (_pr(statusCheckRollup=[_check("CI Gate"), _check("Ruff")]), "cf_attest_not_green_at_head"),
        (
            _pr(statusCheckRollup=[_check("CF attest", "FAILURE"), _check("CI Gate"), _check("Ruff")]),
            "cf_attest_not_green_at_head",
        ),
        (
            _pr(statusCheckRollup=[_check("CF attest"), _check("CI Gate", "FAILURE"), _check("Ruff")]),
            "ci_gate_not_green",
        ),
        (
            _pr(statusCheckRollup=[_check("CF attest"), _check("CI Gate"), _check("Ruff", "", status="IN_PROGRESS")]),
            "blocking_check_pending:Ruff",
        ),
        (_pr(autoMergeRequest={"enabledAt": "2026-08-31T10:03:00Z"}), "already_armed_or_queued"),
    ],
)
def test_decide_auto_arm_refuses_every_ineligible_case(pr: dict, reason: str) -> None:
    decision = auto_arm_merge.decide_auto_arm(pr)

    assert decision.should_arm is False
    assert decision.reason == reason


def test_arm_eligible_prs_arms_and_audits_exactly_one_green_pr() -> None:
    enabled: list[int] = []
    comments: list[tuple[int, str]] = []

    decisions = auto_arm_merge.arm_eligible_prs(
        [_pr()],
        enable=lambda number, _head_sha: enabled.append(number),
        comment=lambda number, head_sha: comments.append((number, head_sha)),
    )

    assert decisions == [auto_arm_merge.ArmDecision(True, "cf_attest_and_ci_gate_green", 7539, HEAD)]
    assert enabled == [7539]
    assert comments == [(7539, HEAD)]


def test_already_armed_pr_is_idempotent() -> None:
    enabled: list[int] = []
    comments: list[tuple[int, str]] = []

    decisions = auto_arm_merge.arm_eligible_prs(
        [_pr(autoMergeRequest={"enabledAt": "2026-08-31T10:03:00Z"})],
        enable=lambda number, _head_sha: enabled.append(number),
        comment=lambda number, head_sha: comments.append((number, head_sha)),
    )

    assert decisions[0].reason == "already_armed_or_queued"
    assert enabled == []
    assert comments == []


@pytest.mark.parametrize(
    ("comments", "run_attempt", "expected_reason", "should_rerun"),
    [
        ([_attestation()], 1, "reran_failed_cf_attest_after_exact_head_attestation", True),
        ([], 1, "exact_head_attestation_missing_or_stale", False),
        ([_attestation("b" * 40)], 1, "exact_head_attestation_missing_or_stale", False),
        ([_attestation(created_at="2026-08-31T10:00:00Z")], 1, "exact_head_attestation_missing_or_stale", False),
        ([_attestation()], 2, "cf_attest_run_not_initial_failed_head", False),
    ],
    ids=[
        "rerun-eligible",
        "no-attestation",
        "stale-attestation-sha",
        "attestation-before-failed-run",
        "already-retried",
    ],
)
def test_retry_stale_cf_attests_requires_a_fresh_exact_head_approval_once(
    comments: list[dict], run_attempt: int, expected_reason: str, should_rerun: bool
) -> None:
    rerun_ids: list[int] = []

    decisions = auto_arm_merge.retry_stale_cf_attests(
        [_failed_cf_pr()],
        get_run=lambda run_id: {
            "id": run_id,
            "head_sha": HEAD,
            "status": "completed",
            "conclusion": "failure",
            "run_attempt": run_attempt,
        },
        get_comments=lambda _number: comments,
        rerun=rerun_ids.append,
    )

    assert decisions[0].reason == expected_reason
    assert decisions[0].should_rerun is should_rerun
    assert rerun_ids == ([987654321] if should_rerun else [])


def test_kill_switch_exits_before_token_or_github_calls(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("AUTO_ARM_MERGE_DISABLED", "1")
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(auto_arm_merge, "list_open_prs", lambda *_args, **_kwargs: pytest.fail("must not list PRs"))

    assert auto_arm_merge.main(["--repo", "learn-ukrainian/learn-ukrainian.github.io"]) == 0
    assert "AUTO_ARM_MERGE_DISABLED=1" in capsys.readouterr().out


def test_gh_wrappers_only_enable_auto_merge_then_post_the_required_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_gh(args: object, *, token: str) -> SimpleNamespace:
        assert token == "token"
        calls.append(list(args))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(auto_arm_merge, "_gh", fake_gh)

    auto_arm_merge.enable_auto_merge("org/repo", 12, HEAD, token="token")
    auto_arm_merge.post_audit_comment("org/repo", 12, HEAD, token="token")

    assert calls == [
        ["pr", "merge", "12", "--repo", "org/repo", "--match-head-commit", HEAD, "--auto"],
        [
            "pr",
            "comment",
            "12",
            "--repo",
            "org/repo",
            "--body",
            f"auto-arm: queued at head {HEAD} (cf-attest+gate green)",
        ],
    ]


def test_rerun_wrapper_targets_only_failed_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_gh(args: object, *, token: str) -> SimpleNamespace:
        assert token == "token"
        calls.append(list(args))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(auto_arm_merge, "_gh", fake_gh)

    auto_arm_merge.rerun_failed_jobs("org/repo", 987654321, token="token")

    assert calls == [["run", "rerun", "987654321", "--repo", "org/repo", "--failed"]]


def test_workflow_is_scheduled_manual_serial_and_minimally_scoped() -> None:
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    triggers = workflow.get("on", workflow.get(True))

    assert set(triggers) == {"schedule", "workflow_dispatch"}
    assert triggers["schedule"] == [{"cron": "7,22,37,52 * * * *"}]
    assert workflow["permissions"] == {
        "actions": "write",
        "pull-requests": "write",
        "contents": "write",
        "checks": "read",
    }
    assert workflow["concurrency"] == {"group": "auto-arm-merge", "cancel-in-progress": False}
    assert "auto_arm_merge.py" in _WORKFLOW.read_text(encoding="utf-8")
