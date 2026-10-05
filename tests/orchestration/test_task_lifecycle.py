from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.orchestration import task_closeout, task_identity, task_lifecycle
from tests import test_quick_fix

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


def _behavior_receipt_reference(tmp_path: Path, *, receipt_updates: dict | None = None) -> dict:
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
        "error": None,
    }
    receipt.update(receipt_updates or {})
    path = (tmp_path / "behavior-proof-receipt.json").resolve()
    receipt_bytes = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(receipt_bytes)
    return {
        "behavior_proof_receipt": {
            "receipt_path": str(path),
            "receipt_sha256": "sha256:" + hashlib.sha256(receipt_bytes).hexdigest(),
            "input_sha256": input_sha256,
            "target_sha": HEAD,
        }
    }


def _approved_actionable_receipt() -> dict:
    return {
        "final_disposition": "actionable",
        "exit_code": 1,
        "error": None,
        "reviewer_payload": {
            "overall": {"correctness": "correct"},
            "finding_ids": ["F001", "F002"],
        },
        "findings": [
            {
                "id": "F001",
                "outcome": "verified",
                "disposition": "in_scope_blocker",
                "disposition_rationale": "Acceptance record fulfilled without changing the head.",
            },
            {
                "id": "F002",
                "outcome": "verified",
                "disposition": "follow_up",
                "disposition_rationale": "Non-blocking hardening has a follow-up owner.",
            },
        ],
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
            "deployments": [{"environment": "production", "state": "SUCCESS", "sha": MERGE}] if deployed else [],
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
        _observation(_body(checked=True), issue_state="CLOSED", pr_state="MERGED", clean=True),
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
def test_terminal_goals_cannot_degrade(goal: str, deployment: bool, certification: bool, expected: str) -> None:
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
    ledger["evidence"][0]["id"] = task_lifecycle.digest(task_lifecycle._evidence_payload(ledger["evidence"][0]))
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


def test_approved_nonblocking_behavior_receipt_preserves_findings_and_snapshot(tmp_path: Path) -> None:
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=_approved_actionable_receipt())
    path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    original_bytes = path.read_bytes()
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL",
        "behavior_proof",
        details=reference,
    )
    original_ledger = deepcopy(ledger)

    updated, receipt, replayed = task_lifecycle.reconcile(ledger, _observation(_body()), now=NOW)

    assert receipt["state"] == "CI_PASSED"
    assert not receipt["hard_blockers"]
    assert replayed is False
    assert updated["ac_snapshot"] == original_ledger["ac_snapshot"]
    assert updated["evidence"] == original_ledger["evidence"]
    assert ledger == original_ledger
    assert path.read_bytes() == original_bytes


@pytest.mark.parametrize(
    ("field_path", "value"),
    [
        (("final_disposition",), "clean"),
        (("final_disposition",), "incomplete"),
        (("exit_code",), 0),
        (("exit_code",), 2),
        (("reviewer_payload", "overall", "correctness"), "incorrect"),
        (("reviewer_payload", "overall", "correctness"), "uncertain"),
        (("reviewer_payload",), None),
        (("reviewer_payload", "overall"), None),
        (("reviewer_payload", "finding_ids"), ["F001"]),
        (("reviewer_payload", "finding_ids"), ["F001", "F003"]),
        (("findings", 1, "id"), "F003"),
        (("reviewer_payload", "finding_ids"), None),
        (("findings",), None),
        (("findings", 1), None),
        (("findings", 1, "outcome"), "quote_missing"),
        (("findings", 1, "outcome"), None),
        (("findings", 1, "disposition"), None),
        (("findings", 1, "disposition"), " "),
        (("findings", 1, "disposition_rationale"), None),
        (("findings", 1, "disposition_rationale"), " "),
        (("findings", 1, "disposition"), "stop_and_escalate"),
        (("findings", 1, "disposition"), "STOP_AND_ESCALATE"),
        (("findings", 1, "disposition"), "stop_and_escalate "),
        (("findings", 1, "disposition"), "whatever"),
        (("error",), "envelope_proof_failed:tests_failed"),
        (("error",), ""),
        (("target", "head_sha"), "d" * 40),
        (("target", "input_sha256"), "d" * 64),
        (("reviewer", "family"), "openai"),
        (("schema_version",), "other-receipt.v1"),
        (("behavior_proof", "schema_version"), "other-proof.v1"),
        (("behavior_proof", "source_aware", "status"), "fail"),
        (("behavior_proof", "source_blind", "status"), "fail"),
        (("behavior_proof", "source_aware", "clauses"), []),
        (("behavior_proof", "source_blind", "clauses"), []),
    ],
    ids=[
        "clean-exit-one", "incomplete", "actionable-exit-zero", "actionable-exit-two",
        "incorrect", "uncertain", "missing-payload", "missing-overall",
        "omitted-finding-id", "mismatched-finding-id", "mismatched-receipt-id", "missing-payload-ids",
        "missing-findings", "malformed-finding", "unverified-second-finding",
        "missing-outcome", "missing-disposition", "blank-disposition",
        "missing-rationale", "blank-rationale", "stop-and-escalate",
        "mixed-case-disposition", "padded-disposition", "unknown-disposition",
        "forged-correct-with-error", "non-null-empty-error", "stale-target",
        "stale-fingerprint", "same-family", "noncanonical-receipt", "noncanonical-proof",
        "forged-correct-aware-failure", "forged-correct-blind-failure",
        "unbound-aware", "unbound-blind",
    ],
)
def test_actionable_behavior_receipt_refuses_each_failed_clause(
    tmp_path: Path, field_path: tuple, value: object,
) -> None:
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=_approved_actionable_receipt())
    path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    receipt = json.loads(path.read_bytes())
    entry = receipt
    for key in field_path[:-1]:
        entry = entry[key]
    entry[field_path[-1]] = value
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=receipt)
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "behavior_proof" not in result["valid_evidence"]["AC-IMPL"]
    assert any("behavior-proof" in blocker for blocker in result["hard_blockers"])


def test_actionable_behavior_receipt_without_findings_is_refused(tmp_path: Path) -> None:
    receipt = _approved_actionable_receipt()
    receipt["findings"] = []
    receipt["reviewer_payload"]["finding_ids"] = []
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=receipt)
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "behavior_proof" not in result["valid_evidence"]["AC-IMPL"]
    assert any("behavior-proof" in blocker for blocker in result["hard_blockers"])


@pytest.mark.parametrize("actionable", [False, True], ids=["clean", "actionable"])
def test_behavior_receipt_without_error_key_is_refused(tmp_path: Path, actionable: bool) -> None:
    reference = _behavior_receipt_reference(
        tmp_path, receipt_updates=_approved_actionable_receipt() if actionable else None,
    )
    path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    receipt = json.loads(path.read_bytes())
    del receipt["error"]
    receipt_bytes = (json.dumps(receipt) + "\n").encode()
    path.write_bytes(receipt_bytes)
    reference["behavior_proof_receipt"]["receipt_sha256"] = "sha256:" + hashlib.sha256(receipt_bytes).hexdigest()
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "behavior_proof" not in result["valid_evidence"]["AC-IMPL"]
    assert any("behavior-proof" in blocker for blocker in result["hard_blockers"])


def test_clean_behavior_receipt_with_error_is_refused(tmp_path: Path) -> None:
    reference = _behavior_receipt_reference(tmp_path, receipt_updates={"error": "runner failed"})
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "behavior_proof" not in result["valid_evidence"]["AC-IMPL"]


def test_forged_correct_without_receipt_finding_id_is_refused(tmp_path: Path) -> None:
    receipt = _approved_actionable_receipt()
    del receipt["findings"][1]["id"]
    receipt["reviewer_payload"]["finding_ids"] = ["F001", None]
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=receipt)
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "behavior_proof" not in result["valid_evidence"]["AC-IMPL"]


def test_closeout_cli_reconciles_original_actionable_receipt(
    tmp_path: Path, capsys: pytest.CaptureFixture,
) -> None:
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=_approved_actionable_receipt())
    receipt_path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    receipt_bytes = receipt_path.read_bytes()
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )
    state_file = tmp_path / "lifecycle.json"
    task_lifecycle.write_lifecycle(state_file, ledger)
    observation_file = tmp_path / "observation.json"
    observation_file.write_text(json.dumps(_observation(_body())), encoding="utf-8")

    code = task_closeout.main([
        "reconcile", "--state-file", str(state_file),
        "--observation-file", str(observation_file), "--now", NOW,
    ])

    assert code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["receipt"]["state"] == "CI_PASSED"
    assert output["receipt"]["hard_blockers"] == []
    persisted = task_lifecycle.load_lifecycle(state_file)
    assert persisted["current_state"] == "CI_PASSED"
    assert persisted["ac_snapshot"] == ledger["ac_snapshot"]
    assert persisted["evidence"] == ledger["evidence"]
    assert receipt_path.read_bytes() == receipt_bytes


def test_actionable_behavior_receipt_changed_bytes_fail_digest_validation(tmp_path: Path) -> None:
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=_approved_actionable_receipt())
    path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    path.write_bytes(path.read_bytes() + b"\n")
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "digest" in " ".join(result["hard_blockers"])


def test_carrier_preserves_identity_ac_snapshot_and_remaining_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
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
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True, timeout=30)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True, timeout=30)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
        check=True,
        timeout=30,
    )
    (repo / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, timeout=30)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True, timeout=30)
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
        timeout=30,
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
        Path("agents_extensions/shared/schemas/task-lifecycle.v1.schema.json").read_text(encoding="utf-8")
    )
    assert schema["additionalProperties"] is False
    assert task_lifecycle.validate_lifecycle(ledger) == ledger


@pytest.mark.parametrize("state", task_lifecycle.STATES)
def test_every_lifecycle_boundary_survives_durable_resume(tmp_path: Path, state: str) -> None:
    ledger = _ledger()
    ledger["current_state"] = state
    path = tmp_path / f"{state.lower()}.json"

    task_lifecycle.write_lifecycle(path, ledger)
    resumed = task_lifecycle.load_lifecycle(path)

    assert resumed == task_lifecycle.validate_lifecycle(ledger)
    assert task_lifecycle.carrier_projection(resumed)["current_state"] == state


# --------------------------------------------------------------------------- #
# #9719 — a verified quick-fix receipt is the approved alternative to an
# independent review; it never relaxes CI, head binding or the normal path.
# --------------------------------------------------------------------------- #
QUICK_FIX_URL = "https://github.com/org/repo/pull/77#issuecomment-9"


def _quick_fix_receipt(tmp_path: Path, *mutations) -> tuple[dict, dict]:
    repo, base, _ = test_quick_fix.make_repo(tmp_path)
    receipt = test_quick_fix.record(repo, base)
    for mutate in mutations:
        mutate(receipt)
    reference = test_quick_fix.write_reference((tmp_path / "quick-fix-42.json").resolve(), receipt)
    return receipt, reference


def _add_at(ledger: dict, ac_id: str, kind: str, head: str, *, url: str | None = None, details=None) -> dict:
    updated, _ = task_lifecycle.add_evidence(
        ledger,
        ac_id=ac_id,
        evidence_type=kind,
        summary=f"verified {ac_id}",
        url=url,
        commit=head,
        details=details,
        recorded_at=NOW,
    )
    return updated


def _quick_fix_ledger(receipt: dict, reference: dict) -> dict:
    head = receipt["head_sha"]
    ledger = _add_at(_ledger(behavior_proof=True), "AC-IMPL", "test", head)
    for ac_id in ("AC-IMPL", "AC-REVIEW"):
        ledger = _add_at(ledger, ac_id, "quick_fix", head, url=QUICK_FIX_URL, details={"quick_fix_receipt": reference})
    return ledger


def _quick_fix_observation(receipt: dict, reference: dict, *, pr_state: str = "OPEN", checks: str = "SUCCESS") -> dict:
    observation = _observation(_body(), pr_state=pr_state, checks=checks)
    observation["github"]["pr"]["head_sha"] = receipt["head_sha"]
    observation["github"]["comments"].append(
        {
            "url": QUICK_FIX_URL,
            "body": (
                "Quick fix — no separate model review. "
                f"Receipt {reference['receipt_sha256']} at head {reference['target_sha']}."
            ),
            "created_at": NOW,
        }
    )
    observation["local"]["commits"] = [{"sha": receipt["head_sha"], "x_agent_trailers": ["X-Agent: claude/fix-42"]}]
    observation["local"]["changed_paths"] = list(receipt["changed_paths"])
    return observation


def test_verified_quick_fix_passes_review_gate_without_a_model_review(tmp_path: Path) -> None:
    receipt, reference = _quick_fix_receipt(tmp_path)
    ledger = _quick_fix_ledger(receipt, reference)

    result = task_lifecycle.evaluate(ledger, _quick_fix_observation(receipt, reference))

    assert result["state"] == "CI_PASSED", result["hard_blockers"]
    assert not [record for record in ledger["evidence"] if record["type"] in {"review", "behavior_proof"}]
    assert "quick_fix" in result["valid_evidence"]["AC-REVIEW"]

    merged = task_lifecycle.evaluate(
        _add_at(ledger, "AC-MERGE", "github", receipt["head_sha"]),
        _quick_fix_observation(receipt, reference, pr_state="MERGED"),
    )
    assert merged["state"] == "MERGED", merged["hard_blockers"]


def test_quick_fix_never_waives_required_ci(tmp_path: Path) -> None:
    receipt, reference = _quick_fix_receipt(tmp_path)

    result = task_lifecycle.evaluate(
        _quick_fix_ledger(receipt, reference), _quick_fix_observation(receipt, reference, checks="FAILURE")
    )

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert result["hard_blockers"] == ["required CI failed: CI Gate"]


def _moved_head(observation: dict, reference: dict) -> None:
    observation["github"]["pr"]["head_sha"] = "d" * 40


def _no_declaration(observation: dict, reference: dict) -> None:
    observation["github"]["comments"] = [c for c in observation["github"]["comments"] if c["url"] != QUICK_FIX_URL]


def _vague_declaration(observation: dict, reference: dict) -> None:
    observation["github"]["comments"][-1]["body"] = "Quick fix, trust me."


def _tampered_receipt(observation: dict, reference: dict) -> None:
    path = Path(reference["receipt_path"])
    path.write_text(path.read_text(encoding="utf-8").replace('"exit_code": 1', '"exit_code": 0'), encoding="utf-8")


def _extra_changed_path(observation: dict, reference: dict) -> None:
    observation["local"]["changed_paths"].append("scripts/unrelated.py")


def _deleted_receipt(observation: dict, reference: dict) -> None:
    Path(reference["receipt_path"]).unlink()


@pytest.mark.parametrize(
    ("change", "message"),
    (
        (_moved_head, "not bound to current PR head"),
        (_no_declaration, "absent from authoritative PR comments"),
        (_vague_declaration, "does not name the receipt digest"),
        (_tampered_receipt, "digest does not match"),
        (_extra_changed_path, "differ from the observed PR diff"),
        (_deleted_receipt, "quick-fix receipt is unreadable"),
    ),
)
def test_quick_fix_refuses_moved_missing_or_stale_evidence(tmp_path: Path, change, message: str) -> None:
    receipt, reference = _quick_fix_receipt(tmp_path)
    observation = _quick_fix_observation(receipt, reference)
    change(observation, reference)

    result = task_lifecycle.evaluate(_quick_fix_ledger(receipt, reference), observation)

    assert result["state"] not in {"REVIEW_PASSED", "CI_PASSED", "MERGED"}
    assert "quick_fix" not in result["valid_evidence"].get("AC-REVIEW", [])
    assert any(message in blocker for blocker in result["hard_blockers"]), result["hard_blockers"]


def _authority_change(receipt: dict) -> None:
    receipt["changed_paths"] = sorted([*receipt["changed_paths"], "scripts/publish/merge.py"])
    receipt["fix_paths"] = sorted([*receipt["fix_paths"], "scripts/publish/merge.py"])


def _incomplete_exclusions(receipt: dict) -> None:
    del receipt["driver"]["exclusions"]["review_or_merge_authority"]


def _self_inspected(receipt: dict) -> None:
    receipt["driver"]["agent"] = receipt["author"]["agent"]


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (_authority_change, "review/merge-authority paths"),
        (_incomplete_exclusions, "every disqualifying change category"),
        (_self_inspected, "distinct from the author"),
    ),
)
def test_quick_fix_refuses_disqualified_or_incomplete_receipts(tmp_path: Path, mutation, message: str) -> None:
    receipt, reference = _quick_fix_receipt(tmp_path, mutation)
    observation = _quick_fix_observation(receipt, reference)

    result = task_lifecycle.evaluate(_quick_fix_ledger(receipt, reference), observation)

    assert result["state"] not in {"REVIEW_PASSED", "CI_PASSED"}
    assert any(message in blocker for blocker in result["hard_blockers"]), result["hard_blockers"]


def test_quick_fix_evidence_shape_is_bound_at_record_time(tmp_path: Path) -> None:
    receipt, reference = _quick_fix_receipt(tmp_path)
    ledger = _ledger()
    head = receipt["head_sha"]

    with pytest.raises(task_lifecycle.LifecycleError, match="PR declaration comment"):
        _add_at(ledger, "AC-REVIEW", "quick_fix", head, details={"quick_fix_receipt": reference})
    with pytest.raises(task_lifecycle.LifecycleError, match="does not match its evidence subject"):
        _add_at(ledger, "AC-REVIEW", "quick_fix", "e" * 40, url=QUICK_FIX_URL, details={"quick_fix_receipt": reference})
    with pytest.raises(task_lifecycle.LifecycleError, match=r"requires details\.quick_fix_receipt"):
        _add_at(
            ledger, "AC-REVIEW", "quick_fix", head, url=QUICK_FIX_URL, details={"behavior_proof_receipt": reference}
        )
    for path, message in (
        ("quick-fix.json", "quick-fix receipt path must be absolute"),
        ("/x/review/q.json", "forbidden"),
    ):
        with pytest.raises(task_lifecycle.LifecycleError, match=message):
            _add_at(
                ledger,
                "AC-REVIEW",
                "quick_fix",
                head,
                url=QUICK_FIX_URL,
                details={"quick_fix_receipt": {**reference, "receipt_path": path}},
            )


def test_without_review_or_quick_fix_the_normal_review_path_still_waits(tmp_path: Path) -> None:
    receipt, reference = _quick_fix_receipt(tmp_path)
    ledger = _add_at(_ledger(), "AC-IMPL", "test", receipt["head_sha"])

    open_result = task_lifecycle.evaluate(ledger, _quick_fix_observation(receipt, reference))
    merged_result = task_lifecycle.evaluate(ledger, _quick_fix_observation(receipt, reference, pr_state="MERGED"))

    assert open_result["state"] == "REVIEW_REQUESTED"
    assert "independent outside-author-family review is pending" in open_result["waiting"]
    assert any("lacks verified current-head outside-family review" in b for b in merged_result["hard_blockers"])


# --------------------------------------------------------------------------- #
# #6028 — resolve_membership: the ONE canonical native-or-unique-body proof
# shared by lifecycle initialization, reconciliation, and every mutation gate.
# --------------------------------------------------------------------------- #
def _fresh_report(now: float, index: dict) -> dict:
    return {
        "generated_at": now,
        "membership_complete": True,
        "incomplete_nodes": [],
        "effective_membership": index,
        "open_issue_numbers": [42, 10],
    }


def test_resolve_membership_native_success() -> None:
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=10,
        registered_epics=[10, 20],
        membership_report=None,
    )
    assert result == {
        "valid": True,
        "method": "native",
        "epic": 10,
        "generated_at": None,
        "digest": None,
        "reason": None,
    }


def test_resolve_membership_unique_body_success() -> None:
    import time

    now = time.time()
    report = _fresh_report(now, {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}})

    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        registered_epics=[10, 20],
        membership_report=report,
    )

    assert result["valid"] is True
    assert result["method"] == "body"
    assert result["epic"] == 10
    assert result["generated_at"] == now
    assert result["digest"].startswith("sha256:")


def test_resolve_membership_native_precedence_over_conflicting_body_evidence() -> None:
    """Native parentage decides the outcome outright — a native parent that
    disagrees with the identity's stream epic is rejected, never falls
    through to body evidence even when body evidence would say otherwise."""
    import time

    report = _fresh_report(
        time.time(),
        {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}},
    )

    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=20,
        registered_epics=[10, 20],
        membership_report=report,
    )

    assert result["valid"] is False
    assert result["method"] is None
    assert "native parent epic" in result["reason"]


def test_resolve_membership_rejects_missing_audit_evidence() -> None:
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        registered_epics=[10],
        membership_report=None,
    )
    assert result["valid"] is False
    assert result["method"] is None
    assert "missing" in result["reason"]


def test_resolve_membership_rejects_stale_audit_evidence() -> None:
    import time

    report = _fresh_report(
        time.time() - 10_000,
        {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}},
    )
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        registered_epics=[10],
        membership_report=report,
    )
    assert result["valid"] is False
    assert "stale" in result["reason"]


def test_resolve_membership_rejects_malformed_audit_evidence() -> None:
    import time

    report = _fresh_report(time.time(), {"42": {"epics": [10]}})  # missing required fields
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        registered_epics=[10],
        membership_report=report,
    )
    assert result["valid"] is False
    assert "malformed" in result["reason"]


def test_resolve_membership_rejects_orphan() -> None:
    """No native parent AND no entry at all in the fresh audit index — this is
    also the shape a CHILD-SIDE-ONLY ``Refs #10`` reference produces: the
    auditor's effective-membership index is built exclusively from what the
    epic body says, so a mention that lives only in the child issue's own
    prose never creates an entry here."""
    import time

    report = _fresh_report(time.time(), {})
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        registered_epics=[10],
        membership_report=report,
    )
    assert result["valid"] is False
    assert "orphan" in result["reason"]


def test_resolve_membership_rejects_wrong_epic() -> None:
    import time

    report = _fresh_report(
        time.time(),
        {"42": {"epics": [20], "streams": ["other"], "via": "body", "unique_stream": True}},
    )
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        registered_epics=[10, 20],
        membership_report=report,
    )
    assert result["valid"] is False
    assert "different epic" in result["reason"]


def test_resolve_membership_rejects_multi_home() -> None:
    import time

    report = _fresh_report(
        time.time(),
        {
            "42": {
                "epics": [10, 20],
                "streams": ["infra", "other"],
                "via": "body",
                "unique_stream": False,
            }
        },
    )
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        registered_epics=[10, 20],
        membership_report=report,
    )
    assert result["valid"] is False
    assert "ambiguously multi-homed" in result["reason"]


def test_resolve_membership_reviewer_case_fails_closed_on_incomplete_traversal() -> None:
    """Opus 5.5 review finding 1 (issue #8661): root #10 references #500,
    root #20 references #500, but #20's traversal was incomplete.
    Even though #500 is in effective_membership under #10 with unique_stream: True,
    resolve_membership must fail closed naming unread node #20."""
    import time

    incomplete_report = {
        "generated_at": time.time(),
        "membership_complete": False,
        "incomplete_nodes": [20],
        "warnings": [{"code": "traversal_incomplete", "issue": 20}],
        "effective_membership": {
            "500": {
                "epics": [10],
                "streams": ["stream10"],
                "via": "body",
                "unique_stream": True,
            }
        },
        "open_issue_numbers": [10, 500],
    }
    result = task_lifecycle.resolve_membership(
        issue_number=500,
        stream_epic=10,
        native_parent_epic=None,
        registered_epics=[10, 20],
        membership_report=incomplete_report,
    )
    assert result["valid"] is False
    assert "#20" in result["reason"]
    assert "incomplete" in result["reason"]


def test_resolve_membership_rejects_unflagged_or_mistyped_completeness() -> None:
    """A pre-flag cache, the string "false", or a non-list incomplete_nodes is unverified."""
    import time

    index = {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}}
    absent = _fresh_report(time.time(), index)
    del absent["membership_complete"]
    string_false = _fresh_report(time.time(), index)
    string_false["membership_complete"] = "false"
    non_list = _fresh_report(time.time(), index)
    non_list["incomplete_nodes"] = "false"
    for report in (absent, string_false, non_list):
        result = task_lifecycle.resolve_membership(
            issue_number=42,
            stream_epic=10,
            native_parent_epic=None,
            registered_epics=[10],
            membership_report=report,
        )
        assert result["valid"] is False
        assert "incomplete" in result["reason"]


def test_resolve_membership_accepts_complete_traversal_report() -> None:
    import time

    complete_report = {
        "generated_at": time.time(),
        "membership_complete": True,
        "incomplete_nodes": [],
        "warnings": [],
        "effective_membership": {
            "500": {
                "epics": [10],
                "streams": ["stream10"],
                "via": "body",
                "unique_stream": True,
            }
        },
        "open_issue_numbers": [10, 500],
    }
    result = task_lifecycle.resolve_membership(
        issue_number=500,
        stream_epic=10,
        native_parent_epic=None,
        registered_epics=[10, 20],
        membership_report=complete_report,
    )
    assert result["valid"] is True
    assert result["method"] == "body"
    assert result["epic"] == 10


def test_resolve_membership_rejects_unregistered_stream_epic() -> None:
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=10,
        registered_epics=[99],
        membership_report=None,
    )
    assert result["valid"] is False
    assert "registered issue-stream" in result["reason"]


def test_resolve_membership_digest_is_deterministic_over_the_index() -> None:
    import time

    now = time.time()
    index = {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}}
    first = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        registered_epics=[10],
        membership_report=_fresh_report(now, index),
    )
    second = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        registered_epics=[10],
        membership_report=_fresh_report(now, dict(index)),
    )
    changed = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        registered_epics=[10],
        membership_report=_fresh_report(
            now,
            {
                **index,
                "7": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True},
            },
        ),
    )
    assert first["digest"] == second["digest"]
    assert first["digest"] != changed["digest"]


# --------------------------------------------------------------------------- #
# #6028 — evaluate()/reconcile() wire resolve_membership in for the primary
# issue and drift is caught fresh on every subsequent reconcile.
# --------------------------------------------------------------------------- #
def test_evaluate_accepts_unique_body_membership_and_records_provenance() -> None:
    import time

    ledger = _ready_evidence(_ledger())
    observation = _observation(_body())
    observation["github"]["issue"]["parent_epic"] = None
    now = time.time()
    observation["github"]["membership_audit"] = _fresh_report(
        now, {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}}
    )

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] != "BLOCKED_WITH_RECEIPT"
    assert result["membership"] == {
        "valid": True,
        "method": "body",
        "epic": 10,
        "generated_at": now,
        "digest": result["membership"]["digest"],
        "reason": None,
    }
    assert result["membership"]["digest"].startswith("sha256:")


def test_evaluate_rejects_body_membership_without_fresh_audit() -> None:
    ledger = _ready_evidence(_ledger())
    observation = _observation(_body())
    observation["github"]["issue"]["parent_epic"] = None
    observation["github"]["membership_audit"] = None

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "issue membership" in " ".join(result["hard_blockers"])
    assert result["membership"]["valid"] is False


def test_reconcile_persists_membership_provenance_in_the_receipt() -> None:
    import time

    ledger = _ready_evidence(_ledger())
    observation = _observation(_body())
    observation["github"]["issue"]["parent_epic"] = None
    now = time.time()
    observation["github"]["membership_audit"] = _fresh_report(
        now, {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}}
    )

    _updated, receipt, _ = task_lifecycle.reconcile(ledger, observation, now=NOW)

    projection = receipt["observation"]["projection"]
    assert projection["membership"]["method"] == "body"
    assert projection["membership"]["epic"] == 10


def test_membership_drift_blocks_a_later_reconcile() -> None:
    """Membership accepted on one reconcile is NOT cached — a later
    reconcile with an observation that no longer proves membership (native
    parent gone, no fresh body audit) must fail closed, even though the
    ledger previously reconciled cleanly."""
    ledger = _ready_evidence(_ledger())
    first_observation = _observation(_body())
    ledger, first_receipt, _ = task_lifecycle.reconcile(ledger, first_observation, now=NOW)
    assert first_receipt["state"] != "BLOCKED_WITH_RECEIPT"

    drifted_observation = _observation(_body())
    drifted_observation["github"]["issue"]["parent_epic"] = None
    drifted_observation["github"]["membership_audit"] = None

    ledger, second_receipt, replayed = task_lifecycle.reconcile(ledger, drifted_observation, now="2026-07-16T11:00:00Z")

    assert replayed is False
    assert second_receipt["state"] == "BLOCKED_WITH_RECEIPT"
    assert "issue membership" in " ".join(second_receipt["hard_blockers"])
    assert ledger["current_state"] == "BLOCKED_WITH_RECEIPT"


def test_explicit_supersession_preserves_old_rows_and_accepts_current_replacement() -> None:
    ledger = _add_at(_ledger(), "AC-IMPL", "test", "d" * 40)
    old_id = ledger["evidence"][0]["id"]
    before = task_lifecycle.evaluate(ledger, _observation(_body()))
    assert any("not bound" in error for error in before["hard_blockers"])
    ledger = _add_at(ledger, "AC-IMPL", "test", HEAD, details={"supersedes_evidence_ids": [old_id]})
    result = task_lifecycle.evaluate(ledger, _observation(_body()))
    assert ledger["evidence"][0]["id"] == old_id
    assert result["valid_evidence"]["AC-IMPL"] == ["test"]
    assert not any("not bound" in error for error in result["hard_blockers"])
    moved = _observation(_body())
    moved["github"]["pr"]["head_sha"] = "e" * 40
    valid, invalid = task_lifecycle._evidence_status(ledger, head_sha="e" * 40, comment_bodies={})
    assert len(invalid) == 2 and not valid
    assert any("not bound" in error for error in task_lifecycle.evaluate(ledger, moved)["hard_blockers"])


@pytest.mark.parametrize("ac,kind,ids", [
    ("AC-MERGE", "test", None), ("AC-IMPL", "document", None),
    ("AC-IMPL", "test", ["sha256:" + "f" * 64]),
    ("AC-IMPL", "test", "bad"), ("AC-IMPL", "test", [1]),
])
def test_supersession_refuses_unbound_cross_criterion_or_kind(ac, kind, ids) -> None:
    ledger = _add_at(_ledger(), "AC-IMPL", "test", "d" * 40)
    with pytest.raises(task_lifecycle.LifecycleError, match="supersession"):
        _add_at(ledger, ac, kind, HEAD,
                details={"supersedes_evidence_ids": ids if ids is not None else [ledger["evidence"][0]["id"]]})


def test_unsuperseded_old_row_and_invalid_replacement_still_block(tmp_path: Path) -> None:
    ledger = _add_at(_ledger(), "AC-IMPL", "test", "d" * 40)
    ledger = _add_at(ledger, "AC-IMPL", "test", HEAD)
    assert any("not bound" in error for error in task_lifecycle.evaluate(ledger, _observation(_body()))["hard_blockers"])
    ledger = _add_at(_ledger(), "AC-REVIEW", "review", "d" * 40, url=REVIEW_URL,
                     details={"author_family": "codex", "reviewer_family": "claude", "verdict": "pass"})
    old_id = ledger["evidence"][0]["id"]
    ledger = _add_at(ledger, "AC-REVIEW", "review", HEAD, url=REVIEW_URL + "0",
                     details={"author_family": "codex", "reviewer_family": "claude", "verdict": "pass",
                              "supersedes_evidence_ids": [old_id]})
    result = task_lifecycle.evaluate(ledger, _observation(_body()))
    assert any("not bound" in error for error in result["hard_blockers"])
    assert "AC-REVIEW" not in result["valid_evidence"]


def _dispatcher_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, inherited_paths: tuple[str, ...] = (),
):
    inherited = dict.fromkeys(inherited_paths, "inherited change\n")
    worktree, base, _ = test_quick_fix.make_repo(tmp_path, fix=inherited or None)
    git = test_quick_fix._git
    if inherited_paths:
        git(worktree, "commit", "--amend", "-qm", "inherited\n\nX-Agent: codex/thread-old")
        base = git(worktree, "rev-parse", "HEAD")
        (worktree / "calc.py").write_text(test_quick_fix.FIXED)
        (worktree / "test_calc.py").write_text(test_quick_fix.REGRESSION)
        git(worktree, "add", "calc.py", "test_calc.py")
        git(worktree, "commit", "-qm", "fix")
    git(worktree, "commit", "--amend", "-qm", "fix\n\nX-Agent: codex/thread-new")
    head = git(worktree, "rev-parse", "HEAD")
    primary = task_lifecycle.canonical_state_root(worktree)
    (primary / ".git/info/exclude").write_text("batch_state/\n")
    tasks = primary / "batch_state/tasks"
    tasks.mkdir(parents=True)
    result = tasks / "thread-new.result"
    result.write_bytes(b"dispatcher result retained verbatim\n")
    dispatch_path = primary / ".worktrees/dispatch/codex/thread-new"
    record = {
        "task_id": "thread-new", "repository": "org/repo", "agent": "codex",
        "task_lifecycle": {"identity": _identity()}, "status": "done", "mode": "danger",
        "returncode": 0, "exit_code": 0, "finished_at": NOW, "commits_ahead": 1,
        "worktree_dirty_on_exit": False, "needs_finalize": False, "worktree_path": str(dispatch_path),
        "worktree_branch": "codex/thread-new", "final_branch_head_commit": head, "worktree_base_sha": base,
        "result_file": str(result), "result_sha256": hashlib.sha256(result.read_bytes()).hexdigest(),
        "owned_paths": ["calc.py", "test_calc.py"],
        "worktree_reap": {"action": "removed", "path": str(dispatch_path), "branch": "codex/thread-new",
                          "dirty": False, "reason": "settled clean worktree; branch ref kept", "error": None},
    }
    path = tasks / "thread-new.json"
    path.write_text(json.dumps(record))
    monkeypatch.chdir(worktree)
    pr_base = git(worktree, "rev-parse", f"{base}^") if inherited_paths else base
    git(worktree, "update-ref", "refs/remotes/origin/main", pr_base)
    entry = {"sha": head, "commit": {"message": git(worktree, "show", "-s", "--format=%B", head)}}
    entries = [entry]
    if inherited_paths:
        entries.insert(0, {"sha": base, "commit": {"message": git(worktree, "show", "-s", "--format=%B", base)}})
    kwargs = dict(head_sha=head, branch="codex/thread-new", worktree=str(dispatch_path), identity=_identity(),
                  github_commits=entries, base_sha=pr_base, merged=True)
    return worktree, path, record, kwargs


def test_reaped_dispatcher_proof_is_honest_and_supports_guarded_close(tmp_path, monkeypatch) -> None:
    repo, path, record, kwargs = _dispatcher_fixture(tmp_path, monkeypatch)
    local = task_lifecycle.observe_local_git(repo, **kwargs)
    assert local["worktree_present"] is False and local["dispatch_worktree_used"] is False
    assert not task_lifecycle._local_readiness(local)
    proof = local["dispatcher_provenance"]
    assert proof["author_head"] == record["final_branch_head_commit"]
    assert proof["record_sha256"] == "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    ledger = _ready_evidence(_ledger())
    # Bind existing typed evidence to the actual fixture Git head, preserving IDs.
    ledger["evidence"] = []
    for ac, kind in (("AC-IMPL", "test"), ("AC-REVIEW", "review"), ("AC-MERGE", "github")):
        ledger = _add_at(ledger, ac, kind, kwargs["head_sha"], url=REVIEW_URL if kind == "review" else None,
                         details={"author_family": "codex", "reviewer_family": "claude", "verdict": "pass"}
                         if kind == "review" else {})
    observation = _observation(_body(checked=True), pr_state="MERGED")
    observation["github"]["pr"]["head_sha"] = kwargs["head_sha"]
    observation["local"] = local
    evaluation = task_lifecycle.evaluate(ledger, observation)
    assert evaluation["goal_reached"] is True and not evaluation["hard_blockers"]
    task_closeout._assert_mutation_ready("close-issue", ledger, observation)


@pytest.mark.parametrize("inherited_paths", [("inherited.py",), ("inherited.py", ".python-version")])
def test_reaped_dispatcher_preserves_whole_pr_scope(tmp_path, monkeypatch, inherited_paths) -> None:
    repo, _, record, kwargs = _dispatcher_fixture(tmp_path, monkeypatch, inherited_paths=inherited_paths)
    local = task_lifecycle.observe_local_git(repo, **kwargs)
    packet_paths = ["calc.py", "test_calc.py"]
    assert local["provenance_error"] is None
    assert local["dispatcher_provenance"]["changed_paths"] == packet_paths
    assert local["changed_paths"] == sorted([*inherited_paths, *packet_paths])
    assert record["commits_ahead"] == 1
    assert len(local["commits"]) == 2
    protected = [".python-version"] if ".python-version" in inherited_paths else []
    assert local["forbidden_paths"] == protected
    assert task_lifecycle._local_readiness(local) == (
        ["forbidden/generated paths changed: .python-version"] if protected else []
    )


@pytest.mark.parametrize("failure", ["head", "merge-base", "diff"])
def test_reaped_dispatcher_refuses_unavailable_whole_pr_scope(tmp_path, monkeypatch, failure) -> None:
    repo, _, _, kwargs = _dispatcher_fixture(tmp_path, monkeypatch)
    run_git = task_lifecycle._run_git

    def unavailable_scope(root, args):
        if args[0] == failure and (failure != "merge-base" or args[1] == "origin/main"):
            raise task_lifecycle.LifecycleError("scope probe unavailable")
        return run_git(root, args)

    monkeypatch.setattr(task_lifecycle, "_run_git", unavailable_scope)
    if failure == "head":
        kwargs["head_sha"] = None
    local = task_lifecycle.observe_local_git(repo, **kwargs)
    assert local["dispatcher_provenance"] is None
    assert "whole-PR changed paths could not be established from Git" in local["provenance_error"]
    assert local["changed_paths"] == []
    assert any("authoring provenance refused" in error for error in task_lifecycle._local_readiness(local))


@pytest.mark.parametrize("change", [
    {"status": "failed"}, {"needs_finalize": True}, {"rescue_status": "unpushed work - needs rescue"},
    {"returncode": 1}, {"exit_code": 1}, {"mode": "read-only"}, {"worktree_dirty_on_exit": True},
    {"commits_ahead": 0}, {"commits_ahead": 2}, {"task_id": "other"}, {"repository": "other/repo"},
    {"task_lifecycle": {}}, {"worktree_path": "/other"}, {"worktree_branch": "other"},
    {"agent": "other"}, {"result_sha256": "f" * 64}, {"result_file": "/other/result"},
    {"final_branch_head_commit": "f" * 40}, {"worktree_base_sha": None}, {"owned_paths": ["other.py"]},
    {"worktree_reap": {}}, {"finished_at": None},
])
def test_dispatcher_proof_refuses_contradictory_or_unsuccessful_record(tmp_path, monkeypatch, change) -> None:
    repo, path, record, kwargs = _dispatcher_fixture(tmp_path, monkeypatch)
    record.update(change)
    path.write_text(json.dumps(record))
    local = task_lifecycle.observe_local_git(repo, **kwargs)
    assert local["dispatcher_provenance"] is None
    assert local["provenance_error"]
    assert task_lifecycle._local_readiness(local)


def test_dispatcher_proof_refuses_missing_result_and_unverified_post_dispatch_head(tmp_path, monkeypatch) -> None:
    repo, _path, record, kwargs = _dispatcher_fixture(tmp_path, monkeypatch)
    result = Path(record["result_file"])
    result.unlink()
    assert task_lifecycle.observe_local_git(repo, **kwargs)["provenance_error"]
    result.write_bytes(b"dispatcher result retained verbatim\n")
    (repo / "calc.py").write_text("unauthorized change\n")
    test_quick_fix._git(repo, "commit", "-am", "later\n\nX-Agent: codex/thread-new")
    head = test_quick_fix._git(repo, "rev-parse", "HEAD")
    kwargs["github_commits"].append({"sha": head, "commit": {"message": "later\n\nX-Agent: codex/thread-new"}})
    kwargs["head_sha"] = head
    local = task_lifecycle.observe_local_git(repo, **kwargs)
    assert "unverified post-dispatch" in local["provenance_error"]


def _github_merge_fixture(repo, base, author_head, *, edited=False):
    git = test_quick_fix._git
    git(repo, "checkout", "-qb", "base-update", base)
    (repo / "base-only.txt").write_text("base update\n")
    git(repo, "add", "base-only.txt")
    git(repo, "commit", "-qm", "base update")
    base_head = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-qb", "merge-fixture", author_head)
    git(repo, "merge", "--no-ff", "-qm", "base merge", base_head)
    if edited:
        (repo / "base-only.txt").write_text("hidden edit\n")
        git(repo, "commit", "-qam", "edited merge", "--amend")
    merge = git(repo, "rev-parse", "HEAD")
    raw = git(repo, "cat-file", "commit", merge)
    headers, _, _ = raw.partition("\n\n")
    headers = "\n".join(
        "committer GitHub <noreply@github.com> " + line.rsplit("> ", 1)[1]
        if line.startswith("committer ") else line for line in headers.splitlines()
    )
    message = "Merge branch 'main' into codex/thread-new"
    payload = headers + "\n\n" + message + "\n"
    signature = "-----BEGIN PGP SIGNATURE-----\nfixture\n-----END PGP SIGNATURE-----"
    signed = headers + "\ngpgsig " + signature.replace("\n", "\n ") + "\n\n" + message + "\n"
    run = subprocess.run(["git", "hash-object", "-w", "-t", "commit", "--stdin"], cwd=repo,
                         input=signed, text=True, capture_output=True, check=True, timeout=30)
    sha = run.stdout.strip()
    entry = {
        "sha": sha, "parents": [{"sha": author_head}, {"sha": base_head}],
        "committer": {"login": "web-flow"}, "commit": {
            "message": message, "committer": {"name": "GitHub", "email": "noreply@github.com"},
            "tree": {"sha": git(repo, "rev-parse", f"{sha}^{{tree}}")},
            "verification": {"verified": True, "reason": "valid", "payload": payload, "signature": signature},
        },
    }
    git(repo, "update-ref", "refs/remotes/origin/main", base_head)
    return entry, base_head


def test_only_verified_clean_github_base_update_passes_attribution(tmp_path, monkeypatch) -> None:
    repo, _, record, kwargs = _dispatcher_fixture(tmp_path, monkeypatch)
    entry, base_head = _github_merge_fixture(repo, record["worktree_base_sha"], kwargs["head_sha"])
    kwargs.update(head_sha=entry["sha"], base_sha=base_head)
    kwargs["github_commits"].append(entry)
    local = task_lifecycle.observe_local_git(repo, **kwargs)
    assert local["commits"][-1]["x_agent_trailers"] == []
    assert local["commits"][-1]["github_base_update"]["parents"][0] == record["final_branch_head_commit"]
    assert local["dispatcher_provenance"]["current_head"] == entry["sha"]
    assert not task_lifecycle._local_readiness(local)


@pytest.mark.parametrize("mutation", [
    lambda e: e["committer"].update(login="ordinary"),
    lambda e: e["commit"]["committer"].update(name="ordinary"),
    lambda e: e["commit"]["verification"].update(verified=False),
    lambda e: e["commit"]["verification"].update(payload="forged"),
    lambda e: e["commit"]["verification"].update(signature="forged"),
    lambda e: e["commit"].update(message="ordinary merge"),
    lambda e: e.update(parents=e["parents"][:1]),
    lambda e: e["commit"]["tree"].update(sha="f" * 40),
    lambda e: e.update(parents=list(reversed(e["parents"]))),
])
def test_github_merge_proof_refuses_unverified_or_contradictory_metadata(tmp_path, monkeypatch, mutation) -> None:
    repo, _, record, kwargs = _dispatcher_fixture(tmp_path, monkeypatch)
    entry, base_head = _github_merge_fixture(repo, record["worktree_base_sha"], kwargs["head_sha"])
    mutation(entry)
    kwargs.update(head_sha=entry["sha"], base_sha=base_head)
    kwargs["github_commits"].append(entry)
    local = task_lifecycle.observe_local_git(repo, **kwargs)
    assert local["dispatcher_provenance"] is None
    assert not local["commits"][-1].get("github_base_update")
    assert task_lifecycle._local_readiness(local)


def test_edited_merge_tree_never_gets_attribution_exception(tmp_path, monkeypatch) -> None:
    repo, _, record, kwargs = _dispatcher_fixture(tmp_path, monkeypatch)
    entry, base_head = _github_merge_fixture(repo, record["worktree_base_sha"], kwargs["head_sha"], edited=True)
    assert task_lifecycle._github_base_update(repo, entry, branch="codex/thread-new", base_sha=base_head) is None


def test_dispatcher_archive_preserves_original_result_digest(tmp_path, monkeypatch) -> None:
    repo, path, record, kwargs = _dispatcher_fixture(tmp_path, monkeypatch)
    archive = path.parent / "archive"
    archive.mkdir()
    path.rename(archive / path.name)
    Path(record["result_file"]).rename(archive / "thread-new.result")
    local = task_lifecycle.observe_local_git(repo, **kwargs)
    assert not task_lifecycle._local_readiness(local)
    assert Path(local["dispatcher_provenance"]["record_path"]).parent == archive
    assert Path(local["dispatcher_provenance"]["result_path"]).parent == archive


@pytest.mark.parametrize("target", ["record", "result", "dispatch"])
def test_dispatcher_proof_refuses_symlinked_paths(tmp_path, monkeypatch, target) -> None:
    repo, path, record, kwargs = _dispatcher_fixture(tmp_path, monkeypatch)
    selected = path if target == "record" else Path(record["result_file"]) if target == "result" else Path(record["worktree_path"])
    if target == "dispatch":
        selected.symlink_to(repo, target_is_directory=True)
        kwargs["worktree"] = str(selected.with_name("reaped-proof"))
    else:
        original = selected.with_suffix(".original")
        selected.rename(original)
        selected.symlink_to(original)
    local = task_lifecycle.observe_local_git(repo, **kwargs)
    assert local["dispatcher_provenance"] is None and local["provenance_error"]


def test_dispatcher_proof_refuses_missing_record_or_empty_result(tmp_path, monkeypatch) -> None:
    repo, path, record, kwargs = _dispatcher_fixture(tmp_path, monkeypatch)
    path.unlink()
    assert "record is missing" in task_lifecycle.observe_local_git(repo, **kwargs)["provenance_error"]
    path.write_text(json.dumps(record))
    Path(record["result_file"]).write_bytes(b"")
    assert "digest does not match" in task_lifecycle.observe_local_git(repo, **kwargs)["provenance_error"]


def test_supersession_duplicate_or_other_subject_never_validates() -> None:
    ledger = _add_at(_ledger(), "AC-IMPL", "test", "d" * 40)
    old_id = ledger["evidence"][0]["id"]
    with pytest.raises(task_lifecycle.LifecycleError, match="duplicate"):
        _add_at(ledger, "AC-IMPL", "test", HEAD, details={"supersedes_evidence_ids": [old_id, old_id]})
    ledger = _add_at(ledger, "AC-IMPL", "test", HEAD, details={"supersedes_evidence_ids": [old_id]})
    replacement = ledger["evidence"][-1]
    replacement["subject"]["pr"] = 78
    replacement["id"] = task_lifecycle.digest(task_lifecycle._evidence_payload(replacement))
    with pytest.raises(task_lifecycle.LifecycleError, match="subject binding differs"):
        task_lifecycle.validate_lifecycle(ledger)
