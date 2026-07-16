from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.orchestration import task_identity, task_lifecycle

NOW = "2026-07-16T10:00:00Z"
HEAD = "a" * 40
MERGE = "b" * 40
REVIEW_URL = "https://github.com/org/repo/pull/77#issuecomment-1"


def _body(*, checked: bool = False, include_deploy: bool = False, include_certify: bool = False) -> str:
    mark = "x" if checked else " "
    lines = [
        f"- [{mark}] **AC-IMPL** — Implementation is verified.",
        f"- [{mark}] **AC-REVIEW** — Independent review passes.",
        f"- [{mark}] **AC-MERGE** — The pull request merges.",
    ]
    if include_deploy:
        lines.append(f"- [{mark}] **AC-DEPLOY** — The merged change deploys.")
    if include_certify:
        lines.append(f"- [{mark}] **AC-CERT** — The deployed change is certified.")
    lines.extend(
        [
            f"- [{mark}] **AC-CLOSE** — The issue is actually closed.",
            f"- [{mark}] **AC-CLEAN** — The task branch and worktree are cleaned.",
        ]
    )
    return "\n".join(lines) + "\n"


def _policy(
    *,
    include_deploy: bool = False,
    include_certify: bool = False,
    behavior_proof: bool = False,
) -> dict:
    policy = {
        "AC-IMPL": {"due_state": "IMPLEMENTATION_READY", "required_evidence": ["test"]},
        "AC-REVIEW": {"due_state": "REVIEW_PASSED", "required_evidence": ["review"]},
        "AC-MERGE": {"due_state": "MERGED", "required_evidence": ["github"]},
        "AC-CLOSE": {"due_state": "ISSUE_CLOSED", "required_evidence": ["github"]},
        "AC-CLEAN": {"due_state": "CLEANED_UP", "required_evidence": ["cleanup"]},
    }
    if include_deploy:
        policy["AC-DEPLOY"] = {"due_state": "DEPLOYED", "required_evidence": ["deployment"]}
    if include_certify:
        policy["AC-CERT"] = {"due_state": "CERTIFIED", "required_evidence": ["certification"]}
    if behavior_proof:
        policy["AC-IMPL"]["required_evidence"].append("behavior_proof")
        policy["AC-IMPL"]["behavior_proof_required"] = True
    return policy


def _identity(goal: str = "merge") -> dict:
    return task_identity.build_identity(
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
        terminal_goal=goal,
        lifecycle_state="confirmed",
    )


def _ledger(goal: str = "merge", *, behavior_proof: bool = False) -> dict:
    deploy = goal in {"deploy", "certify"}
    certify = goal == "certify"
    snapshot = task_lifecycle.build_ac_snapshot(
        _body(include_deploy=deploy, include_certify=certify),
        _policy(
            include_deploy=deploy,
            include_certify=certify,
            behavior_proof=behavior_proof,
        ),
        finalized_at=NOW,
    )
    return task_lifecycle.build_lifecycle(
        _identity(goal),
        author_family="codex",
        ac_snapshot=snapshot,
        required_checks=["CI Gate"],
        now=NOW,
        pr_number=77,
    )


def _add(
    ledger: dict,
    ac_id: str,
    kind: str,
    *,
    url: str | None = None,
    details: dict | None = None,
) -> dict:
    updated, _ = task_lifecycle.add_evidence(
        ledger,
        ac_id=ac_id,
        evidence_type=kind,
        summary=f"verified {ac_id}",
        url=url,
        commit=None if kind in {"cleanup", "follow_up"} else HEAD,
        details=details,
        recorded_at=NOW,
    )
    return updated


def _ready_evidence(ledger: dict) -> dict:
    ledger = _add(ledger, "AC-IMPL", "test")
    return _add(
        ledger,
        "AC-REVIEW",
        "review",
        url=REVIEW_URL,
        details={"author_family": "codex", "reviewer_family": "gemini", "verdict": "pass"},
    )


def _behavior_receipt_reference(tmp_path: Path) -> dict:
    input_sha256 = "c" * 64
    receipt = {
        "schema_version": "code-review-receipt.v1",
        "author": {"family": "openai"},
        "reviewer": {"family": "deepseek"},
        "target": {"head_sha": HEAD, "input_sha256": input_sha256},
        "behavior_proof": {
            "schema_version": "behavior-proof.v1",
            "source_aware": {
                "status": "pass",
                "clauses": [{"target_input_sha256": input_sha256}],
            },
            "source_blind": {
                "status": "pass",
                "blind_enforced": False,
                "clauses": [{"target_input_sha256": input_sha256}],
            },
        },
        "final_disposition": "clean",
        "exit_code": 0,
    }
    path = (tmp_path / "behavior-proof-receipt.json").resolve()
    receipt_bytes = (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()
    path.write_bytes(receipt_bytes)
    return {
        "behavior_proof_receipt": {
            "receipt_path": str(path),
            "receipt_sha256": "sha256:" + hashlib.sha256(receipt_bytes).hexdigest(),
            "input_sha256": input_sha256,
            "target_sha": HEAD,
        }
    }


def _observation(
    body: str,
    *,
    issue_state: str = "OPEN",
    pr_state: str = "OPEN",
    requested_changes: bool = False,
    checks: str = "SUCCESS",
    deployed: bool = False,
    clean: bool = False,
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
                "body": body,
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
                "auto_merge_enabled_at": NOW,
                "review_decision": "CHANGES_REQUESTED" if requested_changes else "APPROVED",
                "requested_changes": requested_changes,
                "reviews": [],
                "checks": [
                    {
                        "name": "CI Gate",
                        "status": "COMPLETED" if checks != "PENDING" else "IN_PROGRESS",
                        "conclusion": checks if checks != "PENDING" else "",
                    }
                ],
                "body": "Refs #42",
            },
            "comments": [{"url": REVIEW_URL, "body": "PASS", "created_at": NOW}],
            "deployments": [
                {"environment": "production", "state": "SUCCESS", "sha": MERGE}
            ]
            if deployed
            else [],
            "follow_up": None,
        },
        "local": {
            "primary_checkout": "/repo",
            "primary_clean": True,
            "dispatch_worktree_used": True,
            "worktree": "/repo/.worktrees/dispatch/codex/42-closeout",
            "worktree_present": not clean,
            "actual_worktree_branch": "codex/42-closeout" if not clean else None,
            "worktree_branch_matches": not clean,
            "branch": "codex/42-closeout",
            "local_branch_present": not clean,
            "remote_branch_present": not clean,
            "commits": [{"sha": HEAD, "x_agent_trailers": ["X-Agent: codex/42-closeout"]}],
            "changed_paths": ["scripts/example.py"],
            "forbidden_paths": [],
        },
    }


def test_snapshot_uses_stable_ids_and_rejects_text_drift() -> None:
    ledger = _ready_evidence(_ledger())
    observation = _observation(_body().replace("The pull request merges.", "The PR maybe merges."))

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert any("drift" in blocker for blocker in result["hard_blockers"])
    assert ledger["ac_snapshot"]["content_hash"].startswith("sha256:")


def test_open_pr_reaches_ci_passed_but_is_not_terminal() -> None:
    ledger = _ready_evidence(_ledger())

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "CI_PASSED"
    assert result["disposition"] == "waiting"
    assert result["goal_reached"] is False


def test_merged_pr_with_open_issue_is_nonterminal() -> None:
    ledger = _add(_ready_evidence(_ledger()), "AC-MERGE", "github")

    result = task_lifecycle.evaluate(
        ledger,
        _observation(_body(checked=True), pr_state="MERGED"),
    )

    assert result["state"] == "MERGED"
    assert result["disposition"] == "waiting"
    assert "actually closed issue" in " ".join(result["waiting"])


def test_auto_close_keyword_is_not_treated_as_issue_closeout() -> None:
    ledger = _add(_ready_evidence(_ledger()), "AC-MERGE", "github")
    observation = _observation(_body(checked=True), pr_state="MERGED")
    observation["github"]["pr"]["body"] = "Fixes #42"

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] == "MERGED"
    assert result["goal_reached"] is True
    assert "actually closed issue" in " ".join(result["waiting"])


def test_closed_issue_with_unverified_postclose_acs_is_rejected() -> None:
    ledger = _add(_ready_evidence(_ledger()), "AC-MERGE", "github")

    result = task_lifecycle.evaluate(
        ledger,
        _observation(_body(checked=True), issue_state="CLOSED", pr_state="MERGED"),
    )

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert any("AC-CLOSE" in blocker for blocker in result["hard_blockers"])


def test_all_evidence_issue_close_and_cleanup_are_terminal() -> None:
    ledger = _add(_ready_evidence(_ledger()), "AC-MERGE", "github")
    ledger = _add(ledger, "AC-CLOSE", "github")
    ledger = _add(ledger, "AC-CLEAN", "cleanup")
    ledger, _, _ = task_lifecycle.reconcile(
        ledger,
        _observation(_body(checked=True), pr_state="MERGED"),
        now=NOW,
    )

    result = task_lifecycle.evaluate(
        ledger,
        _observation(
            _body(checked=True), issue_state="CLOSED", pr_state="MERGED", clean=True
        ),
    )

    assert result["state"] == "CLEANED_UP"
    assert result["disposition"] == "complete"


def test_first_postmerge_reconcile_requires_retained_git_proof() -> None:
    ledger = _add(_ready_evidence(_ledger()), "AC-MERGE", "github")
    observation = _observation(_body(checked=True), pr_state="MERGED")
    observation["local"].update(
        {
            "dispatch_worktree_used": False,
            "worktree_present": False,
            "actual_worktree_branch": None,
            "worktree_branch_matches": False,
            "commits": [],
        }
    )

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "dispatch worktree" in " ".join(result["hard_blockers"])


@pytest.mark.parametrize(
    ("goal", "deployment", "certification", "expected"),
    [
        ("deploy", False, False, "MERGED"),
        ("certify", True, False, "DEPLOYED"),
    ],
)
def test_terminal_goals_cannot_degrade(
    goal: str, deployment: bool, certification: bool, expected: str
) -> None:
    ledger = _ready_evidence(_ledger(goal))
    ledger = _add(ledger, "AC-MERGE", "github")
    if deployment:
        ledger = _add(ledger, "AC-DEPLOY", "deployment")
    if certification:
        ledger = _add(ledger, "AC-CERT", "certification")

    result = task_lifecycle.evaluate(
        ledger,
        _observation(
            _body(include_deploy=True, include_certify=goal == "certify"),
            pr_state="MERGED",
            deployed=deployment,
        ),
    )

    assert result["last_success_state"] == expected
    assert result["goal_reached"] is False


def test_certify_goal_reaches_certified_only_with_typed_evidence() -> None:
    ledger = _ready_evidence(_ledger("certify"))
    for ac_id, kind in (
        ("AC-MERGE", "github"),
        ("AC-DEPLOY", "deployment"),
        ("AC-CERT", "certification"),
    ):
        ledger = _add(ledger, ac_id, kind)

    result = task_lifecycle.evaluate(
        ledger,
        _observation(
            _body(include_deploy=True, include_certify=True),
            pr_state="MERGED",
            deployed=True,
        ),
    )

    assert result["last_success_state"] == "CERTIFIED"
    assert result["goal_reached"] is True


def test_wrong_identity_requested_changes_and_git_hygiene_fail_closed() -> None:
    ledger = _ready_evidence(_ledger())
    observation = _observation(_body(), requested_changes=True)
    observation["github"]["repository"] = "org/wrong"
    observation["local"]["commits"][0]["x_agent_trailers"] = []
    observation["local"]["forbidden_paths"] = [".python-version"]

    result = task_lifecycle.evaluate(ledger, observation)

    blockers = "\n".join(result["hard_blockers"])
    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "repository" in blockers
    assert "requested changes" in blockers
    assert "X-Agent" in blockers
    assert ".python-version" in blockers


def test_spoofed_dispatch_worktree_metadata_fails_closed() -> None:
    ledger = _ready_evidence(_ledger())
    observation = _observation(_body())
    observation["local"].update(
        {
            "worktree_present": False,
            "actual_worktree_branch": "codex/wrong",
            "worktree_branch_matches": False,
        }
    )

    result = task_lifecycle.evaluate(ledger, observation)

    blockers = " ".join(result["hard_blockers"])
    assert "absent from git worktree list" in blockers
    assert "did not match Git authority" in blockers


def test_unregistered_stream_epic_fails_closed() -> None:
    ledger = _ready_evidence(_ledger())
    observation = _observation(_body())
    observation["github"]["registered_stream_epics"] = [99]

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "registered issue-stream" in " ".join(result["hard_blockers"])


def test_remaining_scope_requires_exact_reciprocal_follow_up() -> None:
    ledger = _ready_evidence(_ledger())
    ledger = _add(ledger, "AC-MERGE", "github")
    ledger = _add(ledger, "AC-CLOSE", "follow_up")
    evidence_id = ledger["evidence"][-1]["id"]
    ledger = task_lifecycle.set_remaining_scope(
        ledger,
        status="transferred",
        summary="Move documentation follow-up.",
        follow_up_issue=99,
        follow_up_stream_epic=10,
        evidence_ids=[evidence_id],
        now=NOW,
    )
    observation = _observation(_body(checked=True), pr_state="MERGED")
    observation["github"]["follow_up"] = {
        "number": 99,
        "parent_epic": 11,
        "reciprocal_links_verified": False,
    }

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "follow-up" in " ".join(result["hard_blockers"])


def test_identical_reconcile_is_idempotent() -> None:
    ledger = _ready_evidence(_ledger())
    observation = _observation(_body())

    once, receipt, replayed = task_lifecycle.reconcile(ledger, observation, now=NOW)
    twice, replay_receipt, replayed_again = task_lifecycle.reconcile(
        once, {**observation, "observed_at": "2026-07-16T10:01:00Z"}, now=NOW
    )

    assert replayed is False
    assert replayed_again is True
    assert replay_receipt["id"] == receipt["id"]
    assert len(twice["observation_receipts"]) == 1


def test_evidence_for_other_commit_is_stale() -> None:
    ledger = _ready_evidence(_ledger())
    ledger["evidence"][0]["subject"]["commit"] = "c" * 40
    ledger["evidence"][0]["id"] = task_lifecycle.digest(
        task_lifecycle._evidence_payload(ledger["evidence"][0])
    )
    ledger = task_lifecycle.validate_lifecycle(ledger)

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert any("current PR head" in blocker for blocker in result["hard_blockers"])


def test_user_visible_ac_requires_canonical_target_bound_behavior_receipt(
    tmp_path: Path,
) -> None:
    ledger = _ready_evidence(_ledger(behavior_proof=True))

    missing = task_lifecycle.evaluate(ledger, _observation(_body()))
    ledger = _add(
        ledger,
        "AC-IMPL",
        "behavior_proof",
        details=_behavior_receipt_reference(tmp_path),
    )
    valid = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert any("behavior_proof" in blocker for blocker in missing["hard_blockers"])
    assert "behavior_proof" in valid["valid_evidence"]["AC-IMPL"]
    assert valid["state"] == "CI_PASSED"


def test_changed_behavior_receipt_fails_digest_validation(tmp_path: Path) -> None:
    reference = _behavior_receipt_reference(tmp_path)
    ledger = _ready_evidence(_ledger(behavior_proof=True))
    ledger = _add(ledger, "AC-IMPL", "behavior_proof", details=reference)
    receipt_path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    receipt_path.write_text("{}\n", encoding="utf-8")

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "digest" in " ".join(result["hard_blockers"])


def test_carrier_preserves_identity_ac_snapshot_and_remaining_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    ledger = _ledger()
    path = task_lifecycle.lifecycle_path(tmp_path, ledger["identity"])
    task_lifecycle.write_lifecycle(path, ledger)

    carrier = task_lifecycle.carrier_projection(ledger, state_file=str(path))

    assert carrier["identity"] == ledger["identity"]
    assert carrier["ac_snapshot"] == ledger["ac_snapshot"]
    assert carrier["remaining_scope"] == ledger["remaining_scope"]
    assert path.name == "issue-42.json"


def test_local_git_observation_cross_checks_exact_worktree_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
        check=True,
    )
    (repo / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
    worktree = repo / ".worktrees" / "dispatch" / "codex" / "42-closeout"
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "worktree",
            "add",
            "-qb",
            "codex/42-closeout",
            str(worktree),
        ],
        check=True,
    )

    observed = task_lifecycle.observe_local_git(
        repo,
        head_sha=None,
        branch="codex/42-closeout",
        worktree=str(worktree),
    )
    wrong = task_lifecycle.observe_local_git(
        repo,
        head_sha=None,
        branch="codex/wrong",
        worktree=str(worktree),
    )

    assert observed["worktree_present"] is True
    assert observed["dispatch_worktree_used"] is True
    assert observed["actual_worktree_branch"] == "codex/42-closeout"
    assert observed["worktree_branch_matches"] is True
    assert wrong["worktree_branch_matches"] is False


def test_legacy_migration_preserves_proof_lists() -> None:
    ledger = _ready_evidence(_ledger())
    legacy = {
        "schema_version": "task-lifecycle.legacy",
        "pr_number": 77,
        "evidence": deepcopy(ledger["evidence"]),
        "observation_receipts": [],
        "mutation_receipts": [],
    }

    migrated = task_lifecycle.migrate_legacy(
        legacy,
        identity=_identity(),
        policy=_policy(),
        issue_body=_body(),
        required_checks=["CI Gate"],
        author_family="codex",
        now=NOW,
    )

    assert migrated["migration"]["legacy"] is True
    assert migrated["evidence"] == legacy["evidence"]


def test_schema_round_trip_is_strict() -> None:
    ledger = _ledger()
    schema = json.loads(
        Path("agents_extensions/shared/schemas/task-lifecycle.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert schema["additionalProperties"] is False
    assert task_lifecycle.validate_lifecycle(ledger) == ledger


@pytest.mark.parametrize("state", task_lifecycle.STATES)
def test_every_lifecycle_boundary_survives_durable_resume(
    tmp_path: Path, state: str
) -> None:
    ledger = _ledger()
    ledger["current_state"] = state
    path = tmp_path / f"{state.lower()}.json"

    task_lifecycle.write_lifecycle(path, ledger)
    resumed = task_lifecycle.load_lifecycle(path)

    assert resumed == task_lifecycle.validate_lifecycle(ledger)
    assert task_lifecycle.carrier_projection(resumed)["current_state"] == state
