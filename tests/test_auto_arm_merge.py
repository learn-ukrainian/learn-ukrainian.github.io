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

    # workflow_run added as the event-driven fallback for the unreliable cron:
    # arm right after a CI run completes, with red runs admitted by the
    # read-only label gate below.
    assert set(triggers) == {"schedule", "workflow_dispatch", "workflow_run"}
    assert triggers["schedule"] == [{"cron": "7,22,37,52 * * * *"}]
    assert triggers["workflow_run"] == {"workflows": ["CI"], "types": ["completed"]}
    arm_job = workflow["jobs"]["arm"]
    assert arm_job["needs"] == "red_completion_gate"
    assert workflow["permissions"] == {
        "contents": "read",
    }
    assert arm_job["permissions"] == {
        "actions": "write",
        "pull-requests": "write",
        "contents": "write",
        "checks": "read",
        "issues": "read",
    }
    assert workflow["concurrency"] == {"group": "auto-arm-merge", "cancel-in-progress": False}
    source = _WORKFLOW.read_text(encoding="utf-8")
    # Module invocation keeps the repo root importable (scripts.ci.cf_attest).
    assert "python -m scripts.ci.auto_arm_merge" in source
    # #7586: arming must not use GITHUB_TOKEN (merge_group would never run).
    arm_steps = arm_job["steps"]
    mint = next(step for step in arm_steps if step.get("id") == "app")
    assert mint["uses"].startswith("actions/create-github-app-token@")
    assert "bcd2ba49218906704ab6c1aa796996da409d3eb1" in mint["uses"]
    arm = next(step for step in arm_steps if step.get("name") == "Arm opted-in green pull requests")
    assert arm["env"]["GH_TOKEN"] == "${{ steps.app.outputs.token }}"
    assert "${{ github.token }}" not in str(arm.get("env"))
    assert "Never fall back to github.token" in source
    skip = next(step for step in arm_steps if step.get("name") == "Skip arming when the App is not configured")
    assert skip["if"] == "${{ steps.app.outputs.token == '' }}"
    assert arm["if"] == "${{ steps.app.outputs.token != '' }}"


@pytest.mark.parametrize(
    ("head_repository", "conclusion", "has_label", "expected"),
    [
        ("fork-owner/repo", "failure", True, False),
        ("org/repo", "failure", False, False),
        ("org/repo", "failure", True, True),
    ],
    ids=["fork-red-run", "same-repo-red-run-without-label", "same-repo-red-labeled"],
)
def test_workflow_run_privilege_boundary_cases(
    head_repository: str, conclusion: str, has_label: bool, expected: bool
) -> None:
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    gate = workflow["jobs"]["red_completion_gate"]
    arm_if = workflow["jobs"]["arm"]["if"]

    assert gate["if"] == (
        "github.event_name == 'workflow_run' && "
        "github.event.workflow_run.conclusion != 'success' && "
        "github.event.workflow_run.head_repository.full_name == github.repository"
    )
    assert gate["permissions"] == {"contents": "read", "pull-requests": "read"}
    label_step = gate["steps"][0]
    assert label_step["env"]["WORKFLOW_PULL_REQUESTS"] == "${{ toJSON(github.event.workflow_run.pull_requests) }}"
    assert "repos/${REPOSITORY}/pulls/${number}" in label_step["run"]
    assert '"automerge-ok"' in label_step["run"]
    assert ".[0:100]" in label_step["run"]
    assert "github.event.workflow_run.head_repository.full_name == github.repository" in arm_if
    assert "github.event.workflow_run.conclusion == 'success'" in arm_if
    assert "needs.red_completion_gate.outputs.has_automerge_label == 'true'" in arm_if

    # This is the job-level condition's red-run truth table: fork runs fail the
    # repository boundary, while a same-repository red run needs the label gate.
    repository = "org/repo"
    allowed = head_repository == repository and (conclusion == "success" or has_label)
    assert allowed is expected


def test_already_queued_pr_is_not_rearmed_or_recommented() -> None:
    """#7573: a live mergeQueueEntry at the same head suppresses the
    re-arm + "queued" re-comment loop (autoMergeRequest reads null there)."""
    enabled: list[int] = []
    comments: list[tuple[int, str]] = []

    decisions = auto_arm_merge.arm_eligible_prs(
        [_pr()],
        enable=lambda number, _head_sha: enabled.append(number),
        comment=lambda number, head_sha: comments.append((number, head_sha)),
        is_queued=lambda _number, _head_sha: True,
    )

    assert decisions == [auto_arm_merge.ArmDecision(False, "already_armed_or_queued", 7539, HEAD)]
    assert enabled == []
    assert comments == []


def test_not_queued_green_pr_still_arms_and_comments_once() -> None:
    enabled: list[int] = []
    comments: list[tuple[int, str]] = []

    decisions = auto_arm_merge.arm_eligible_prs(
        [_pr()],
        enable=lambda number, _head_sha: enabled.append(number),
        comment=lambda number, head_sha: comments.append((number, head_sha)),
        is_queued=lambda _number, _head_sha: False,
    )

    assert decisions == [auto_arm_merge.ArmDecision(True, "cf_attest_and_ci_gate_green", 7539, HEAD)]
    assert enabled == [7539]
    assert comments == [(7539, HEAD)]


def test_arm_eligible_prs_is_queued_graphql_failure_does_not_abort_scan_or_later_prs() -> None:
    """#7593 r3: GraphQL failure on one PR degrades to advisory and does not block later PRs."""
    pr1 = _pr(number=101, headRefOid="1" * 40)
    pr2 = _pr(number=102, headRefOid="2" * 40)

    enabled: list[int] = []
    comments: list[tuple[int, str]] = []

    def flaky_is_queued(number: int, _head_sha: str) -> bool:
        if number == 101:
            raise RuntimeError("GraphQL 502 Bad Gateway")
        return False

    decisions = auto_arm_merge.arm_eligible_prs(
        [pr1, pr2],
        enable=lambda number, _head_sha: enabled.append(number),
        comment=lambda number, head_sha: comments.append((number, head_sha)),
        is_queued=flaky_is_queued,
    )

    assert len(decisions) == 2
    assert decisions[0].should_arm is True
    assert decisions[0].number == 101
    assert decisions[1].should_arm is True
    assert decisions[1].number == 102
    assert enabled == [101, 102]
    assert comments == [(101, "1" * 40), (102, "2" * 40)]


@pytest.mark.parametrize(
    "exc",
    [
        RuntimeError("HTTP 500 internal server error"),
        ValueError("malformed GraphQL payload"),
        KeyError("mergeQueueEntry"),
    ],
)
def test_arm_eligible_prs_is_queued_exceptions_degrade_to_advisory(exc: Exception) -> None:
    pr1 = _pr(number=101, headRefOid="1" * 40)
    pr2 = _pr(number=102, headRefOid="2" * 40)

    enabled: list[int] = []
    comments: list[tuple[int, str]] = []

    def failing_is_queued(number: int, _head_sha: str) -> bool:
        if number == 101:
            raise exc
        return False

    decisions = auto_arm_merge.arm_eligible_prs(
        [pr1, pr2],
        enable=lambda number, _head_sha: enabled.append(number),
        comment=lambda number, head_sha: comments.append((number, head_sha)),
        is_queued=failing_is_queued,
    )

    assert [d.number for d in decisions if d.should_arm] == [101, 102]
    assert enabled == [101, 102]


def test_get_merge_queue_entry_parses_graphql_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    import json as _json

    calls: list[list[str]] = []

    def fake_gh(args: object, *, token: str) -> SimpleNamespace:
        calls.append(list(args))
        return SimpleNamespace(
            returncode=0,
            stdout=_json.dumps(
                {"data": {"repository": {"pullRequest": {"mergeQueueEntry": {"position": 3}}}}}
            ),
            stderr="",
        )

    monkeypatch.setattr(auto_arm_merge, "_gh", fake_gh)

    entry = auto_arm_merge.get_merge_queue_entry("org/repo", 12, token="token")

    assert entry == {"position": 3}
    assert calls[0][0:2] == ["api", "graphql"]
    assert any("mergeQueueEntry" in arg for arg in calls[0])
    assert "number=12" in calls[0]


def test_get_merge_queue_entry_null_when_not_queued(monkeypatch: pytest.MonkeyPatch) -> None:
    import json as _json

    def fake_gh(args: object, *, token: str) -> SimpleNamespace:
        return SimpleNamespace(
            returncode=0,
            stdout=_json.dumps(
                {"data": {"repository": {"pullRequest": {"mergeQueueEntry": None}}}}
            ),
            stderr="",
        )

    monkeypatch.setattr(auto_arm_merge, "_gh", fake_gh)

    assert auto_arm_merge.get_merge_queue_entry("org/repo", 12, token="token") is None


def _ejection_event(event_id: int = 777, head: str = HEAD) -> dict:
    return {
        "id": event_id,
        "event": "removed_from_merge_queue",
        "commit_id": head,
        "created_at": "2026-09-01T10:00:00Z",
    }


def test_queue_ejection_posts_once_per_event() -> None:
    posted: list[str] = []

    decisions = auto_arm_merge.notify_queue_ejections(
        [_pr()],
        get_events=lambda _number: [_ejection_event()],
        get_comments=lambda _number: [],
        get_run_details=lambda _number: (
            "https://github.com/org/repo/actions/runs/5",
            ["CI Gate", "pytest-fastlane"],
        ),
        comment=lambda _number, body: posted.append(body),
    )

    assert decisions == [
        auto_arm_merge.EjectionDecision(
            True, "queue_ejection_unreported", 7539, "777", HEAD, "2026-09-01T10:00:00Z"
        )
    ]
    assert len(posted) == 1
    assert "removed from the merge queue" in posted[0]
    assert "actions/runs/5" in posted[0]
    assert "CI Gate, pytest-fastlane" in posted[0]
    assert "<!-- auto-arm:queue-ejection:777 -->" in posted[0]

    # Second scan with the marker comment present: silent, no run lookup.
    reposted: list[str] = []
    decisions = auto_arm_merge.notify_queue_ejections(
        [_pr()],
        get_events=lambda _number: [_ejection_event()],
        get_comments=lambda _number: [{"body": posted[0]}],
        get_run_details=lambda _number: pytest.fail("no run lookup when deduped"),
        comment=lambda _number, body: reposted.append(body),
    )
    assert decisions[0].reason == "ejection_already_noted"
    assert reposted == []


def test_queue_ejection_distinct_events_each_get_one_comment() -> None:
    posted: list[str] = []
    auto_arm_merge.notify_queue_ejections(
        [_pr()],
        get_events=lambda _number: [_ejection_event(777), _ejection_event(888)],
        get_comments=lambda _number: [
            {"body": "prior note <!-- auto-arm:queue-ejection:777 -->"}
        ],
        get_run_details=lambda _number: (None, []),
        comment=lambda _number, body: posted.append(body),
    )
    # Only the LATEST ejection is reported; the older one is superseded.
    assert len(posted) == 1
    assert "<!-- auto-arm:queue-ejection:888 -->" in posted[0]
    assert "queue rebuild or manual removal" in posted[0]


def test_queue_ejection_skips_prs_without_opt_in_or_events() -> None:
    decisions = auto_arm_merge.notify_queue_ejections(
        [_pr(labels=[])],
        get_events=lambda _number: pytest.fail("must not scan unlabeled PRs"),
        get_comments=lambda _number: pytest.fail("must not scan unlabeled PRs"),
        get_run_details=lambda _number: pytest.fail("must not scan unlabeled PRs"),
        comment=lambda _number, _body: pytest.fail("must not comment"),
    )
    assert decisions == []

    decisions = auto_arm_merge.notify_queue_ejections(
        [_pr()],
        get_events=lambda _number: [],
        get_comments=lambda _number: [],
        get_run_details=lambda _number: pytest.fail("no run lookup without ejection"),
        comment=lambda _number, _body: pytest.fail("must not comment"),
    )
    assert decisions == [auto_arm_merge.EjectionDecision(False, "no_queue_ejection", 7539)]


def test_queue_ejection_scan_failure_is_advisory_not_fatal() -> None:
    decisions = auto_arm_merge.notify_queue_ejections(
        [_pr()],
        get_events=lambda _number: (_ for _ in ()).throw(RuntimeError("HTTP 403")),
        get_comments=lambda _number: [],
        get_run_details=lambda _number: (None, []),
        comment=lambda _number, _body: pytest.fail("must not comment"),
    )
    assert decisions[0].should_comment is False
    assert decisions[0].reason.startswith("ejection_scan_unavailable")
