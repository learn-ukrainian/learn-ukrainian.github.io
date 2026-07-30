from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.orchestration import issue_stream_audit, task_closeout, task_identity, task_lifecycle

NOW = "2026-07-16T10:00:00Z"
HEAD = "a" * 40
MERGE = "b" * 40
REVIEW_URL = "https://github.com/org/repo/pull/77#issuecomment-1"


def _body(*, checked: bool = False) -> str:
    mark = "x" if checked else " "
    return "\n".join(
        [
            f"- [{mark}] **AC-IMPL** — Implementation is verified.",
            f"- [{mark}] **AC-REVIEW** — Independent review passes.",
            f"- [{mark}] **AC-MERGE** — The pull request merges.",
            f"- [{mark}] **AC-CLOSE** — The issue is actually closed.",
            f"- [{mark}] **AC-CLEAN** — Branch and worktree are cleaned.",
            "",
        ]
    )


def _ledger(tmp_path: Path, *, review: bool = True, merged: bool = False) -> tuple[Path, dict]:
    identity = task_identity.build_identity(
        repository="org/repo",
        stream_epic=10,
        stream_epic_url=None,
        github_issue_number=42,
        github_issue_url=None,
        semantic_title="Enforce task closeout",
        task_family="infrastructure",
        role="implementer",
        predecessor_task_id="thread-old",
        replacement_task_id="thread-new",
        lineage_id="lineage-closeout",
        generation=2,
        terminal_goal="merge",
        lifecycle_state="confirmed",
    )
    policy = {
        "AC-IMPL": {"due_state": "IMPLEMENTATION_READY", "required_evidence": ["test"]},
        "AC-REVIEW": {"due_state": "REVIEW_PASSED", "required_evidence": ["review"]},
        "AC-MERGE": {"due_state": "MERGED", "required_evidence": ["github"]},
        "AC-CLOSE": {"due_state": "ISSUE_CLOSED", "required_evidence": ["github"]},
        "AC-CLEAN": {"due_state": "CLEANED_UP", "required_evidence": ["cleanup"]},
    }
    ledger = task_lifecycle.build_lifecycle(
        identity,
        author_family="codex",
        ac_snapshot=task_lifecycle.build_ac_snapshot(_body(), policy, finalized_at=NOW),
        required_checks=["CI Gate"],
        now=NOW,
        pr_number=77,
    )
    ledger, _ = task_lifecycle.add_evidence(
        ledger,
        ac_id="AC-IMPL",
        evidence_type="test",
        summary="focused tests pass",
        url=None,
        commit=HEAD,
        details={},
        recorded_at=NOW,
    )
    if review:
        ledger, _ = task_lifecycle.add_evidence(
            ledger,
            ac_id="AC-REVIEW",
            evidence_type="review",
            summary="outside-family review passes",
            url=REVIEW_URL,
            commit=HEAD,
            details={
                "author_family": "codex",
                "reviewer_family": "gemini",
                "verdict": "pass",
            },
            recorded_at=NOW,
        )
    if merged:
        ledger, _ = task_lifecycle.add_evidence(
            ledger,
            ac_id="AC-MERGE",
            evidence_type="github",
            summary="PR merged",
            url="https://github.com/org/repo/pull/77",
            commit=HEAD,
            details={},
            recorded_at=NOW,
        )
    path = tmp_path / "lifecycle.json"
    task_lifecycle.write_lifecycle(path, ledger)
    return path, ledger


def _observation(
    *,
    body: str | None = None,
    issue_state: str = "OPEN",
    pr_state: str = "OPEN",
    pr_body: str = "Refs #42",
) -> dict:
    return {
        "schema_version": task_lifecycle.OBSERVATION_SCHEMA_VERSION,
        "observed_at": NOW,
        "github": {
            "repository": "org/repo",
            "registered_stream_epics": [10],
            "issue": {
                "number": 42,
                "state": issue_state,
                "body": body if body is not None else _body(),
                "url": "https://github.com/org/repo/issues/42",
                "closed_at": NOW if issue_state == "CLOSED" else None,
                "parent_epic": 10,
            },
            "pr": {
                "number": 77,
                "url": "https://github.com/org/repo/pull/77",
                "state": pr_state,
                "is_draft": False,
                "head_sha": HEAD,
                "head_branch": "codex/42-closeout",
                "merge_sha": MERGE if pr_state == "MERGED" else None,
                "merged_at": NOW if pr_state == "MERGED" else None,
                "auto_merge_enabled_at": None,
                "review_decision": "APPROVED",
                "requested_changes": False,
                "reviews": [],
                "checks": [
                    {"name": "CI Gate", "status": "COMPLETED", "conclusion": "SUCCESS"}
                ],
                "body": pr_body,
            },
            "comments": [{"url": REVIEW_URL, "body": "PASS", "created_at": NOW}],
            "deployments": [],
            "follow_up": None,
        },
        "local": {
            "primary_checkout": "/repo",
            "primary_clean": True,
            "dispatch_worktree_used": True,
            "worktree": "/repo/.worktrees/dispatch/codex/42-closeout",
            "worktree_present": True,
            "actual_worktree_branch": "codex/42-closeout",
            "worktree_branch_matches": True,
            "branch": "codex/42-closeout",
            "local_branch_present": True,
            "remote_branch_present": True,
            "commits": [{"sha": HEAD, "x_agent_trailers": ["X-Agent: codex/42-closeout"]}],
            "changed_paths": ["scripts/example.py"],
            "forbidden_paths": [],
        },
    }


class FakeAdapter:
    def __init__(self, observation: dict) -> None:
        self.observation = deepcopy(observation)
        self.calls: list[str] = []

    def observe(self, _ledger: dict, **_kwargs: object) -> dict:
        return deepcopy(self.observation)

    def update_issue_body(self, _repository: str, _issue_number: int, body: str) -> None:
        self.calls.append("sync-acs")
        self.observation["github"]["issue"]["body"] = body

    def arm_auto_merge(self, _repository: str, _pr_number: int) -> None:
        self.calls.append("arm-auto-merge")
        self.observation["github"]["pr"]["auto_merge_enabled_at"] = NOW

    def close_issue(self, _repository: str, _issue_number: int) -> None:
        self.calls.append("close-issue")
        self.observation["github"]["issue"]["state"] = "CLOSED"
        self.observation["github"]["issue"]["closed_at"] = NOW


def test_sync_acs_checks_only_evidenced_criteria_and_replays(tmp_path: Path) -> None:
    path, _ = _ledger(tmp_path)
    adapter = FakeAdapter(_observation())

    first = task_closeout.perform_mutation(
        path,
        adapter,
        action="sync-acs",
        authorized_by="codex/5297",
        branch="codex/42-closeout",
        worktree="/repo/.worktrees/dispatch/codex/42-closeout",
        now=NOW,
    )
    second = task_closeout.perform_mutation(
        path,
        adapter,
        action="sync-acs",
        authorized_by="codex/5297",
        branch="codex/42-closeout",
        worktree="/repo/.worktrees/dispatch/codex/42-closeout",
        now=NOW,
    )

    body = adapter.observation["github"]["issue"]["body"]
    assert adapter.calls == ["sync-acs"]
    assert "- [x] **AC-IMPL**" in body
    assert "- [x] **AC-REVIEW**" in body
    assert "- [ ] **AC-MERGE**" in body
    assert first["remote_mutation_performed"] is True
    assert second["replayed"] is True
    assert second["remote_mutation_performed"] is False


def test_intent_recovery_does_not_repeat_remote_close(tmp_path: Path) -> None:
    path, ledger = _ledger(tmp_path, merged=True)
    operation_id = task_lifecycle.mutation_operation_id(ledger, "close-issue")
    ledger, _, _ = task_lifecycle.append_mutation_event(
        ledger,
        operation_id=operation_id,
        action="close-issue",
        status="intent",
        authorized_by="codex/5297",
        requested_at=NOW,
        completed_at=None,
        remote_mutation_performed=False,
        detail="intent persisted before simulated crash",
    )
    task_lifecycle.write_lifecycle(path, ledger)
    adapter = FakeAdapter(
        _observation(body=_body(checked=True), issue_state="CLOSED", pr_state="MERGED")
    )

    result = task_closeout.perform_mutation(
        path,
        adapter,
        action="close-issue",
        authorized_by="codex/5297",
        branch="codex/42-closeout",
        worktree="/repo/.worktrees/dispatch/codex/42-closeout",
        now=NOW,
    )

    assert adapter.calls == []
    assert result["replayed"] is True
    assert result["remote_mutation_performed"] is False
    assert task_lifecycle.mutation_status(
        task_lifecycle.load_lifecycle(path), operation_id
    ) == "complete"


def test_verified_merge_permits_one_explicit_close(tmp_path: Path) -> None:
    path, _ = _ledger(tmp_path, merged=True)
    adapter = FakeAdapter(_observation(body=_body(checked=True), pr_state="MERGED"))

    result = task_closeout.perform_mutation(
        path,
        adapter,
        action="close-issue",
        authorized_by="codex/5297",
        branch="codex/42-closeout",
        worktree="/repo/.worktrees/dispatch/codex/42-closeout",
        now=NOW,
    )

    assert adapter.calls == ["close-issue"]
    assert result["remote_mutation_performed"] is True
    assert adapter.observation["github"]["issue"]["state"] == "CLOSED"


def test_auto_merge_is_blocked_until_current_head_review(tmp_path: Path) -> None:
    path, _ = _ledger(tmp_path, review=False)
    adapter = FakeAdapter(_observation())

    with pytest.raises(task_lifecycle.LifecycleError, match="outside-family review"):
        task_closeout.perform_mutation(
            path,
            adapter,
            action="arm-auto-merge",
            authorized_by="codex/5297",
            branch="codex/42-closeout",
            worktree="/repo/.worktrees/dispatch/codex/42-closeout",
            now=NOW,
        )

    assert adapter.calls == []
    ledger = task_lifecycle.load_lifecycle(path)
    assert ledger["current_state"] == "BLOCKED_WITH_RECEIPT"
    assert ledger["mutation_receipts"][-1]["status"] == "failed"
    assert "outside-family review" in ledger["mutation_receipts"][-1]["detail"]


def test_missing_authorization_is_durable_and_nonmutating(tmp_path: Path) -> None:
    path, _ = _ledger(tmp_path)

    result = task_closeout.record_unauthorized_mutation(
        path,
        action="arm-auto-merge",
        actor="codex/5297",
        now=NOW,
    )
    ledger = task_lifecycle.load_lifecycle(path)

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert result["remote_mutation_performed"] is False
    assert ledger["current_state"] == "BLOCKED_WITH_RECEIPT"
    assert "--authorize" in ledger["mutation_receipts"][-1]["detail"]


def test_membership_audit_report_forwards_adapter_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Review finding F001 (PR #6030): ``GhGitHubAdapter.membership_audit_report``
    must carry ``self.repo_root`` into ``issue_stream_audit.run_audit`` — every
    call site that reaches it (init/reconcile/mutation/closeout, all routed
    through this one adapter method) must audit and cache against the
    checkout the adapter itself was constructed for, never the auditor
    module's own ``ROOT``."""
    captured: dict[str, object] = {}

    def fake_run_audit(repo_root: Path) -> dict:
        captured["repo_root"] = repo_root
        return {"ok": True, "effective_membership": {}}

    monkeypatch.setattr(issue_stream_audit, "run_audit", fake_run_audit)

    adapter = task_closeout.GhGitHubAdapter(tmp_path)
    report = adapter.membership_audit_report()

    assert report == {"ok": True, "effective_membership": {}}
    assert captured["repo_root"] == adapter.repo_root
    assert adapter.repo_root == tmp_path.resolve()
    assert adapter.repo_root != issue_stream_audit.ROOT


def test_github_adapter_normalizes_parent_pr_checks_and_deployments(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def runner(args: list[str], _stdin: str | None) -> str:
        calls.append(args)
        command = " ".join(args)
        if "issue view" in command:
            return json.dumps(
                {
                    "number": 42,
                    "state": "OPEN",
                    "body": _body(),
                    "url": "https://github.com/org/repo/issues/42",
                    "closedAt": None,
                }
            )
        if "api graphql" in command:
            return json.dumps(
                {"data": {"repository": {"issue": {"parent": {"number": 10}}}}}
            )
        if "pr view" in command:
            return json.dumps(
                {
                    "number": 77,
                    "url": "https://github.com/org/repo/pull/77",
                    "state": "MERGED",
                    "isDraft": False,
                    "headRefOid": HEAD,
                    "headRefName": "codex/42-closeout",
                    "mergeCommit": {"oid": MERGE},
                    "mergedAt": NOW,
                    "autoMergeRequest": {"enabledAt": NOW},
                    "reviewDecision": "APPROVED",
                    "reviews": [],
                    "statusCheckRollup": [
                        {
                            "__typename": "CheckRun",
                            "name": "CI Gate",
                            "status": "COMPLETED",
                            "conclusion": "SUCCESS",
                        }
                    ],
                    "body": "Refs #42",
                }
            )
        if "issues/77/comments" in command:
            return "[]"
        if "pulls/77/reviews" in command:
            return json.dumps(
                [
                    {
                        "html_url": REVIEW_URL.replace("issuecomment-1", "pullrequestreview-5"),
                        "body": "PASS",
                        "user": {"login": "reviewer"},
                        "submitted_at": NOW,
                        "state": "APPROVED",
                        "commit_id": HEAD,
                    }
                ]
            )
        if command.endswith("deployments -f sha=" + MERGE):
            return json.dumps([{"id": 9, "environment": "production", "sha": MERGE}])
        if "deployments/9/statuses" in command:
            return json.dumps([{"state": "success", "environment_url": "https://prod"}])
        raise AssertionError(f"unexpected command: {args}")

    adapter = task_closeout.GhGitHubAdapter(tmp_path, runner=runner)
    adapter.registered_stream_epics = lambda: [10]
    _, ledger = _ledger(tmp_path)
    ledger["terminal_goal"] = "deploy"
    ledger["identity"]["terminal_goal"] = "deploy"
    github = adapter._github_observation(task_lifecycle.validate_lifecycle(ledger))

    assert github["issue"]["parent_epic"] == 10
    assert github["pr"]["checks"][0]["conclusion"] == "SUCCESS"
    assert github["comments"][0]["kind"] == "pull_request_review"
    assert github["deployments"] == [
        {
            "id": 9,
            "environment": "production",
            "sha": MERGE,
            "state": "SUCCESS",
            "url": "https://prod",
        }
    ]
    deployment_call = next(
        args
        for args in calls
        if any(value.endswith("/deployments") for value in args) and "-f" in args
    )
    assert deployment_call[deployment_call.index("--method") + 1] == "GET"


def _transferred_ledger_and_reader(
    tmp_path: Path,
    *,
    primary_parent_epic: int | None,
    follow_up_parent_epic: int | None,
    follow_up_issue: int = 99,
) -> tuple[dict, list[int], object]:
    """Build a lifecycle whose remaining scope was transferred to a follow-up
    issue, plus a ``read_issue`` stub that records every issue number it is
    asked to read and reports the given native parents for the primary (#42)
    and follow-up (``follow_up_issue``) issues."""
    _, ledger = _ledger(tmp_path)
    ledger["remaining_scope"] = {
        "status": "transferred",
        "summary": "remaining work moved to the follow-up issue",
        "follow_up_issue": follow_up_issue,
        "follow_up_stream_epic": 20,
        "evidence_ids": [],
    }
    calls: list[int] = []
    parents = {42: primary_parent_epic, follow_up_issue: follow_up_parent_epic}

    def _read_issue(self, repository: str, issue_number: int) -> dict:
        calls.append(issue_number)
        return {
            "number": issue_number,
            "state": "OPEN",
            "body": f"Refs #{follow_up_issue}" if issue_number == 42 else "Refs #42",
            "url": f"https://github.com/{repository}/issues/{issue_number}",
            "closed_at": None,
            "parent_epic": parents[issue_number],
        }

    return ledger, calls, _read_issue


def test_github_observation_skips_audit_when_primary_and_follow_up_are_native(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Review finding F001 (PR #6030 second pass): a transferred-scope
    follow-up must not force a live membership audit when both the primary
    issue and the follow-up already have authoritative native parents."""
    ledger, calls, read_issue = _transferred_ledger_and_reader(
        tmp_path, primary_parent_epic=10, follow_up_parent_epic=20
    )
    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "read_issue", read_issue)

    def _fail_audit(self) -> dict:
        raise AssertionError("native primary + native follow-up must not trigger a live audit")

    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "membership_audit_report", _fail_audit)
    adapter = task_closeout.GhGitHubAdapter(tmp_path)
    monkeypatch.setattr(adapter, "registered_stream_epics", lambda: [10, 20])
    monkeypatch.setattr(adapter, "_read_pr", lambda repository, pr_number: {"number": pr_number, "checks": []})
    monkeypatch.setattr(adapter, "_comments", lambda repository, pr_number: [])

    github = adapter._github_observation(ledger)

    assert github["membership_audit"] is None
    assert github["follow_up"]["number"] == 99
    assert calls.count(42) == 1
    assert calls.count(99) == 1


@pytest.mark.parametrize(
    "primary_parent_epic,follow_up_parent_epic",
    [
        (None, 20),
        (10, None),
        (None, None),
    ],
    ids=["primary-lacks-native", "follow-up-lacks-native", "both-lack-native"],
)
def test_github_observation_fetches_audit_when_either_relevant_issue_lacks_native_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    primary_parent_epic: int | None,
    follow_up_parent_epic: int | None,
) -> None:
    """Body evidence (and therefore a live audit) is still required whenever
    the primary issue or the present transferred follow-up has no native
    parent to resolve membership on its own."""
    ledger, calls, read_issue = _transferred_ledger_and_reader(
        tmp_path,
        primary_parent_epic=primary_parent_epic,
        follow_up_parent_epic=follow_up_parent_epic,
    )
    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "read_issue", read_issue)
    monkeypatch.setattr(
        task_closeout.GhGitHubAdapter,
        "membership_audit_report",
        lambda self: {"sentinel": True},
    )
    adapter = task_closeout.GhGitHubAdapter(tmp_path)
    monkeypatch.setattr(adapter, "registered_stream_epics", lambda: [10, 20])
    monkeypatch.setattr(adapter, "_read_pr", lambda repository, pr_number: {"number": pr_number, "checks": []})
    monkeypatch.setattr(adapter, "_comments", lambda repository, pr_number: [])

    github = adapter._github_observation(ledger)

    assert github["membership_audit"] == {"sentinel": True}
    assert calls.count(42) == 1
    assert calls.count(99) == 1


def _identity_dict(**overrides: object) -> dict:
    identity = task_identity.build_identity(
        repository="org/repo",
        stream_epic=10,
        stream_epic_url=None,
        github_issue_number=42,
        github_issue_url=None,
        semantic_title="Enforce task closeout",
        task_family="infrastructure",
        role="implementer",
        predecessor_task_id="thread-old",
        replacement_task_id="thread-new",
        lineage_id="lineage-closeout",
        generation=2,
        terminal_goal="merge",
        lifecycle_state="confirmed",
    )
    identity.update(overrides)
    return identity


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _init_args(tmp_path: Path, identity_path: Path) -> object:
    policy_path = _write_json(
        tmp_path / "policy.json",
        {"AC-IMPL": {"due_state": "IMPLEMENTATION_READY", "required_evidence": ["test"]}},
    )
    return task_closeout.build_parser().parse_args(
        [
            "--repo-root",
            str(tmp_path),
            "init",
            "--identity-file",
            str(identity_path),
            "--ac-policy",
            str(policy_path),
            "--author-family",
            "codex",
            "--required-check",
            "CI Gate",
            "--state-file",
            str(tmp_path / "lifecycle.json"),
            "--now",
            NOW,
        ]
    )


def _stub_read_issue(*, parent_epic: int | None) -> object:
    def _read_issue(self, repository: str, issue_number: int) -> dict:
        return {
            "number": issue_number,
            "state": "OPEN",
            "body": "- [ ] **AC-IMPL** — Implementation is verified.\n",
            "url": f"https://github.com/{repository}/issues/{issue_number}",
            "closed_at": None,
            "parent_epic": parent_epic,
        }

    return _read_issue


def test_cmd_init_accepts_native_membership_without_a_live_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    identity_path = _write_json(tmp_path / "identity.json", _identity_dict())
    monkeypatch.setattr(
        task_closeout.GhGitHubAdapter, "read_issue", _stub_read_issue(parent_epic=10)
    )
    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "registered_stream_epics", lambda self: [10])

    def _fail_audit(self) -> dict:
        raise AssertionError("native membership must not trigger a live membership audit")

    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "membership_audit_report", _fail_audit)

    assert task_closeout.cmd_init(_init_args(tmp_path, identity_path)) == 0
    ledger = task_lifecycle.load_lifecycle(tmp_path / "lifecycle.json")
    assert ledger["identity"]["stream_epic"] == 10


def test_cmd_init_accepts_unique_body_membership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    identity_path = _write_json(tmp_path / "identity.json", _identity_dict())
    monkeypatch.setattr(
        task_closeout.GhGitHubAdapter, "read_issue", _stub_read_issue(parent_epic=None)
    )
    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "registered_stream_epics", lambda self: [10])
    monkeypatch.setattr(
        task_closeout.GhGitHubAdapter,
        "membership_audit_report",
        lambda self: {
            "generated_at": time.time(),
            "effective_membership": {
                "42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}
            },
            "open_issue_numbers": [42, 10],
        },
    )

    assert task_closeout.cmd_init(_init_args(tmp_path, identity_path)) == 0
    ledger = task_lifecycle.load_lifecycle(tmp_path / "lifecycle.json")
    assert ledger["identity"]["stream_epic"] == 10


def test_cmd_init_rejects_orphaned_issue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    identity_path = _write_json(tmp_path / "identity.json", _identity_dict())
    monkeypatch.setattr(
        task_closeout.GhGitHubAdapter, "read_issue", _stub_read_issue(parent_epic=None)
    )
    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "registered_stream_epics", lambda self: [10])
    monkeypatch.setattr(
        task_closeout.GhGitHubAdapter,
        "membership_audit_report",
        lambda self: {
            "generated_at": time.time(),
            "effective_membership": {},
            "open_issue_numbers": [42, 10],
        },
    )

    with pytest.raises(task_lifecycle.LifecycleError, match="stream epic"):
        task_closeout.cmd_init(_init_args(tmp_path, identity_path))
    assert not (tmp_path / "lifecycle.json").exists()


def test_mutation_gates_fail_closed_on_membership_drift(tmp_path: Path) -> None:
    """The exact same membership validator gates init, reconcile, AND every
    mutation action — a lifecycle that reconciled fine while native must
    still block sync-acs, arm-auto-merge, and close-issue once native
    parentage disappears with no fresh body-audit evidence available."""
    path, _ = _ledger(tmp_path, review=False)
    drifted = _observation()
    drifted["github"]["issue"]["parent_epic"] = None
    adapter = FakeAdapter(drifted)

    for action in ("sync-acs", "arm-auto-merge", "close-issue"):
        with pytest.raises(task_lifecycle.LifecycleError, match="stream epic"):
            task_closeout.perform_mutation(
                path,
                adapter,
                action=action,
                authorized_by="codex/5297",
                branch="codex/42-closeout",
                worktree="/repo/.worktrees/dispatch/codex/42-closeout",
                now=NOW,
            )
    assert adapter.calls == []


def test_github_read_failure_becomes_a_blocked_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path, ledger = _ledger(tmp_path)
    adapter = task_closeout.GhGitHubAdapter(tmp_path)

    def fail(_ledger: dict) -> dict:
        raise task_lifecycle.LifecycleError("offline")

    monkeypatch.setattr(adapter, "_github_observation", fail)
    monkeypatch.setattr(task_lifecycle, "observe_local_git", lambda *_args, **_kwargs: {})
    observation = adapter.observe(ledger, now=NOW)
    updated, receipt, _ = task_lifecycle.reconcile(
        task_lifecycle.load_lifecycle(path), observation, now=NOW
    )

    assert receipt["state"] == "BLOCKED_WITH_RECEIPT"
    assert "GitHub observation failed" in " ".join(receipt["hard_blockers"])
    assert updated["current_state"] == "BLOCKED_WITH_RECEIPT"
