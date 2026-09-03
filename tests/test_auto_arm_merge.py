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
            _check("CI Gate", started_at="2026-08-31T10:01:00Z"),
            _check("Ruff", started_at="2026-08-31T10:02:00Z"),
        ],
    }
    result.update(changes)
    return result


@pytest.mark.parametrize(
    ("pr", "reason"),
    [
        (_pr(labels=[]), "opt_in_label_missing"),
        (_pr(labels=[{"name": "automerge-ok"}, {"name": "hold"}]), "blocking_label"),
        (_pr(labels=[{"name": "automerge-ok"}, {"name": "do-not-merge"}]), "blocking_label"),
        (_pr(isDraft=True), "draft_or_unknown"),
        (
            _pr(statusCheckRollup=[_check("CI Gate", "FAILURE"), _check("Ruff")]),
            "ci_gate_not_green",
        ),
        (
            _pr(statusCheckRollup=[_check("CI Gate"), _check("Ruff", "", status="IN_PROGRESS")]),
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

    assert decisions == [auto_arm_merge.ArmDecision(True, "ci_gate_green", 7539, HEAD)]
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
            f"auto-arm: queued at head {HEAD} (gate green)",
        ],
    ]


def test_workflow_is_dispatch_only_and_minimally_scoped() -> None:
    """Retire-CF-attest (2026-09-03 GO): schedule/workflow_run are retired so
    this workflow is never a live, automatic merge path — dispatch only."""
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    triggers = workflow.get("on", workflow.get(True))

    assert set(triggers) == {"workflow_dispatch"}
    arm_job = workflow["jobs"]["arm"]
    assert "needs" not in arm_job
    assert "red_completion_gate" not in workflow["jobs"]
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

    assert decisions == [auto_arm_merge.ArmDecision(True, "ci_gate_green", 7539, HEAD)]
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
