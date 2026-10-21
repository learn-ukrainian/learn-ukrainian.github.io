"""Author controls for exact execution binding; independent review is separate."""
from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from urllib.parse import parse_qs, urlsplit

import pytest

from scripts.opsec import prepublish as gate
from scripts.orchestration import lifecycle_observation as lo
from scripts.orchestration import merge_closeout as mc
from scripts.orchestration import task_closeout
from scripts.orchestration import task_lifecycle as tl
from tests.orchestration.test_task_lifecycle import (
    HEAD,
    MERGE,
    NOW,
    REVIEW_URL,
    _behavior_receipt_reference,
    _identity,
    _observation,
)

RUN_URL = "https://github.com/org/repo/actions/runs/123"
JOB_URL = RUN_URL + "/job/456"
BODY = "- [x] **AC-RUN** — The criterion has executed tests and CI.\n"


def evidence(ledger, kind, *, ac_id="AC-RUN", url=JOB_URL, details=None):
    return tl.add_evidence(
        ledger, ac_id=ac_id, evidence_type=kind, summary="criterion evidence",
        url=url, commit=HEAD, details=details or {}, recorded_at=NOW,
    )[0]


@pytest.fixture
def bound_case():
    snapshot = tl.build_ac_snapshot(BODY, {
        "AC-RUN": {"due_state": "MERGED", "required_evidence": ["test", "ci", "review"]},
    }, finalized_at=NOW)
    ledger = tl.build_lifecycle(_identity(), author_family="codex", ac_snapshot=snapshot,
                                required_checks=["CI Gate"], now=NOW, pr_number=77)
    ledger = evidence(ledger, "test", details={"step_names": ["Run criterion tests"]})
    ledger = evidence(ledger, "review", url=REVIEW_URL, details={
        "author_family": "codex", "reviewer_family": "claude", "verdict": "pass",
    })
    ledger, _, _ = tl.reconcile(ledger, _observation(BODY), now=NOW)
    pull = {
        "number": 77, "html_url": "https://github.com/org/repo/pull/77", "merged": True,
        "merged_at": NOW, "merge_commit_sha": MERGE, "state": "closed", "head": {"sha": HEAD},
        "base": {"ref": "main", "repo": {"full_name": "org/repo"}},
        "created_at": "2026-07-16T08:00:00Z",
    }
    run = {
        "id": 123, "run_attempt": 2, "repository": {"full_name": "org/repo"},
        "event": "merge_group", "head_sha": MERGE, "head_branch": "gh-readonly-queue/main/pr-77-abcdef",
        "html_url": RUN_URL, "path": ".github/workflows/ci.yml", "status": "completed", "conclusion": "success",
        "created_at": "2026-07-16T09:00:00Z", "run_started_at": "2026-07-16T09:01:00Z",
    }
    step = {"name": "Run criterion tests", "status": "completed", "conclusion": "success",
            "started_at": "2026-07-16T09:02:00Z", "completed_at": "2026-07-16T09:03:00Z"}
    job = {"id": 456, "run_id": 123, "run_attempt": 2, "head_sha": MERGE, "html_url": JOB_URL,
           "name": "CI Gate", "status": "completed", "conclusion": "success",
           "started_at": "2026-07-16T09:01:00Z", "completed_at": "2026-07-16T09:05:00Z", "steps": [step]}
    return ledger, _observation(BODY, pr_state="MERGED", clean=True), pull, run, [job]


def derive(case):
    ledger, observation, pull, run, jobs = case
    return lo.merged_run_evidence(ledger, observation, pull=pull, run=run, jobs=jobs, now=NOW)


@pytest.fixture
def run_transport(bound_case, monkeypatch):
    """Model the counted GitHub search cap at the actual typed GET boundary."""
    _, _, pull, run, jobs = bound_case
    state = {"history": [deepcopy(run)], "detail": deepcopy(run), "jobs": deepcopy(jobs),
             "pages": None, "requests": []}
    monkeypatch.setattr(gate, "catalog", lambda: {
        "public": {"github": "org/repo", "default": True, "local_name": "fixture", "role": "public-monorepo"},
    })

    def send(argv, **kwargs):
        assert argv[:4] == ["gh", "api", "--method", "GET"]
        assert kwargs["fresh"] is True
        endpoint = urlsplit(argv[4])
        query = parse_qs(endpoint.query)
        state["requests"].append((endpoint.path, query))
        if endpoint.path == "repos/org/repo/pulls/77":
            payload = pull
        elif endpoint.path == "repos/org/repo/actions/runs":
            assert argv[-2:] == ["--paginate", "--slurp"]
            assert query["event"] == ["merge_group"]
            assert query["created"] == [pull["created_at"] + ".." + pull["merged_at"]]
            assert query["per_page"] == ["100"]
            rows = [row for row in state["history"]
                    if row.get("event") in query["event"]
                    and ("head_sha" not in query or row.get("head_sha") in query["head_sha"])]
            payload = state["pages"]
            if payload is None:
                capped = rows[:1000]
                payload = [{"total_count": len(rows), "workflow_runs": capped[i:i + 100]}
                           for i in range(0, max(1, len(capped)), 100)]
        elif endpoint.path == "repos/org/repo/actions/runs/123":
            payload = state["detail"]
        elif endpoint.path == "repos/org/repo/actions/runs/123/jobs":
            assert argv[-2:] == ["--paginate", "--slurp"]
            payload = [{"total_count": len(state["jobs"]), "jobs": state["jobs"]}]
        else:
            pytest.fail(f"unexpected execution identity: {endpoint.path}")
        return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")

    monkeypatch.setattr(mc.github_client, "run", send)
    return state


def collect_at_boundary(bound_case, tmp_path):
    return mc.collect_merged_run_evidence(tmp_path, *bound_case[:2], now=NOW)


def test_exact_merge_survives_more_unrelated_newer_runs_than_search_cap(bound_case, run_transport, tmp_path):
    """F3: a 1,002-row global history hides the eligible run behind the 1,000 cap."""
    run = bound_case[3]
    run_transport["history"] = [
        {**run, "id": run_id, "head_sha": "c" * 40} for run_id in range(1124, 123, -1)
    ] + [deepcopy(run)]
    updated, report = collect_at_boundary(bound_case, tmp_path)
    assert report["closure_ready"] is True
    assert updated["evidence"][-1]["details"]["run_id"] == 123
    assert run_transport["requests"][1][1]["head_sha"] == [MERGE]
    assert [path for path, _ in run_transport["requests"]] == [
        "repos/org/repo/pulls/77", "repos/org/repo/actions/runs",
        "repos/org/repo/actions/runs/123", "repos/org/repo/actions/runs/123/jobs",
    ]


def test_exact_target_paginates_all_matching_runs_before_choosing_newest(bound_case, run_transport, tmp_path):
    """A matching run on page two cannot be hidden by a short first-page read."""
    run_transport["history"] = [{**bound_case[3], "id": run_id} for run_id in range(21, 124)]
    _, report = collect_at_boundary(bound_case, tmp_path)
    assert report["closure_ready"] is True
    assert run_transport["requests"][1][1]["head_sha"] == [MERGE]


@pytest.mark.parametrize("history_change", ["missing", "wrong_sha", "wrong_event", "wrong_workflow"])
def test_exact_query_cannot_supply_an_unrelated_execution(bound_case, run_transport, tmp_path, history_change):
    """Empty or unrelated search results cannot create merged-run proof."""
    if history_change == "missing":
        run_transport["history"] = []
    else:
        key, value = {"wrong_sha": ("head_sha", "c" * 40), "wrong_event": ("event", "push"),
                      "wrong_workflow": ("path", ".github/workflows/other.yml")}[history_change]
        run_transport["history"][0][key] = value
    with pytest.raises(mc.MergeCloseoutError, match=r"^CLOSEOUT_MERGE_RUN_MISSING$"):
        collect_at_boundary(bound_case, tmp_path)
    assert len(run_transport["requests"]) == 2


@pytest.mark.parametrize("key,value", [
    ("event", "pull_request"), ("head_sha", "c" * 40), ("path", ".github/workflows/other.yml"),
    ("conclusion", "failure"), ("conclusion", "cancelled"), ("status", "in_progress"),
    ("repository", {"full_name": "other/repo"}),
])
def test_fresh_detail_cannot_turn_wrong_or_red_execution_into_proof(
    bound_case, run_transport, tmp_path, key, value,
):
    """The server-side filter never substitutes for fresh detail validation."""
    run_transport["detail"][key] = value
    with pytest.raises(lo.ObservationRefusal, match=r"^CLOSEOUT_MERGE_RUN_MISMATCH$"):
        collect_at_boundary(bound_case, tmp_path)


@pytest.mark.parametrize("conclusion", ["failure", "cancelled"])
def test_newest_red_run_never_falls_back_to_older_green(bound_case, run_transport, tmp_path, conclusion):
    """A successful older match must not mask the newest failed execution."""
    newest = {**bound_case[3], "conclusion": conclusion}
    run_transport["history"] = [{**bound_case[3], "id": 122}, newest]
    run_transport["detail"] = newest
    with pytest.raises(lo.ObservationRefusal, match=r"^CLOSEOUT_MERGE_RUN_MISMATCH$"):
        collect_at_boundary(bound_case, tmp_path)
    assert run_transport["requests"][2][0] == "repos/org/repo/actions/runs/123"


@pytest.mark.parametrize("key,value", [("run_attempt", 3), ("run_attempt", None), ("id", 124)])
def test_fresh_attempt_or_identity_moving_is_refused(bound_case, run_transport, tmp_path, key, value):
    """A rerun between listing and detail fetch invalidates that snapshot."""
    run_transport["detail"][key] = value
    with pytest.raises(mc.MergeCloseoutError, match=r"^CLOSEOUT_RUN_ATTEMPT_MOVED$"):
        collect_at_boundary(bound_case, tmp_path)
    assert len(run_transport["requests"]) == 3


@pytest.mark.parametrize("attempt", [None, 0, True, "2"])
def test_list_without_a_proven_latest_attempt_is_refused(bound_case, run_transport, tmp_path, attempt):
    """Malformed attempt metadata cannot authorize fetching arbitrary run jobs."""
    run_transport["history"][0]["run_attempt"] = attempt
    with pytest.raises(mc.MergeCloseoutError, match=r"^CLOSEOUT_RUN_ID_INVALID$"):
        collect_at_boundary(bound_case, tmp_path)


def test_jobs_from_an_older_attempt_cannot_prove_the_new_rerun(bound_case, run_transport, tmp_path):
    """Successful jobs for attempt one do not prove listed and fetched attempt two."""
    run_transport["jobs"][0]["run_attempt"] = 1
    with pytest.raises(lo.ObservationRefusal, match=r"^CLOSEOUT_JOB_RUN_MISMATCH$"):
        collect_at_boundary(bound_case, tmp_path)


@pytest.mark.parametrize("malformation", [
    "empty", "partial", "duplicate", "malformed_row", "missing_count", "count_drift", "not_pages", "target_cap",
])
def test_target_query_keeps_counted_completeness_fail_closed(bound_case, run_transport, tmp_path, malformation):
    """SHA filtering cannot excuse truncation, duplicate pages or malformed collections."""
    run = bound_case[3]
    run_transport["pages"] = {
        "empty": [],
        "partial": [{"total_count": 2, "workflow_runs": [run]}],
        "duplicate": [{"total_count": 2, "workflow_runs": [run]}, {"total_count": 2, "workflow_runs": [run]}],
        "malformed_row": [{"total_count": 1, "workflow_runs": [None]}],
        "missing_count": [{"workflow_runs": [run]}],
        "count_drift": [{"total_count": 1, "workflow_runs": [run]}, {"total_count": 2, "workflow_runs": []}],
        "not_pages": {},
        "target_cap": None,
    }[malformation]
    if malformation == "target_cap":
        run_transport["history"] = [{**run, "id": run_id} for run_id in range(1124, 123, -1)]
    reason = "UNREADABLE" if malformation == "not_pages" else "INCOMPLETE"
    with pytest.raises(mc.MergeCloseoutError, match=f"^CLOSEOUT_EXECUTION_{reason}$"):
        collect_at_boundary(bound_case, tmp_path)
    assert len(run_transport["requests"]) == 2


def test_bound_execution_derives_only_ci_and_replays_without_duplicate(bound_case):
    original = deepcopy(bound_case[0])
    updated, report = derive(bound_case)
    assert report["closure_ready"] is True
    assert report["cleanup_residual"] is False
    assert report["criteria"] == [{
        "ac_id": "AC-RUN", "passed": True, "missing": [], "executed": [
            {"evidence_id": original["evidence"][0]["id"], "type": "test", "job_id": 456,
             "check": "CI Gate", "step_names": ["Run criterion tests"], "url": JOB_URL},
            {"evidence_id": updated["evidence"][-1]["id"], "type": "ci", "job_id": 456,
             "check": "CI Gate", "step_names": ["Run criterion tests"], "url": JOB_URL},
        ],
    }]
    assert updated["evidence"][:-1] == original["evidence"]
    assert updated["evidence"][-1]["details"]["merge_sha"] == MERGE
    assert updated["evidence"][-1]["details"]["run_attempt"] == 2
    assert original == bound_case[0]
    bound_case = (updated, *bound_case[1:])
    replay, again = derive(bound_case)
    assert replay["evidence"] == updated["evidence"]
    assert again["closure_ready"] is True


@pytest.mark.parametrize("consumer", ["sync-acs", "close-issue", "issue-body"])
@pytest.mark.parametrize("target,key,value,expected", [
    ("observation", "observed_at", "2026-07-17T10:00:00Z", "CLOSEOUT_RECEIPT_STALE_OR_MISMATCHED"),
    ("report", "execution_sha256", "bad", "CLOSEOUT_RECEIPT_STALE_OR_MISMATCHED"),
    ("report", "repository", "other/repo", "CLOSEOUT_RECEIPT_STALE_OR_MISMATCHED"),
    ("report", "issue", 999, "CLOSEOUT_RECEIPT_STALE_OR_MISMATCHED"),
    ("report", "pr", 78, "CLOSEOUT_RECEIPT_STALE_OR_MISMATCHED"),
    ("report", "head_sha", "c" * 40, "CLOSEOUT_RECEIPT_STALE_OR_MISMATCHED"),
    ("report", "merge_sha", "c" * 40, "CLOSEOUT_RECEIPT_STALE_OR_MISMATCHED"),
    ("report", "run_id", "123", "CLOSEOUT_RECEIPT_STALE_OR_MISMATCHED"),
    ("report", "run_attempt", 3, "CLOSEOUT_RECEIPT_STALE_OR_MISMATCHED"),
    ("report", "run_url", RUN_URL + "0", "CLOSEOUT_RECEIPT_STALE_OR_MISMATCHED"),
    ("github", "closeout_run", None, "CLOSEOUT_RECEIPT_MISSING_OR_INVALID"),
    ("github", "closeout_run", {}, "CLOSEOUT_RECEIPT_MISSING_OR_INVALID"),
    ("github", "closeout_run", [], "CLOSEOUT_RECEIPT_MISSING_OR_INVALID"),
    ("report", "execution", None, "CLOSEOUT_RECEIPT_MISSING_OR_INVALID"),
    ("run", "run_attempt", 3, "CLOSEOUT_JOB_RUN_MISMATCH"),
    ("run", "event", "pull_request", "CLOSEOUT_MERGE_RUN_MISMATCH"),
    ("run", "created_at", None, "CLOSEOUT_MERGE_RUN_STALE"),
    ("pull", "number", 78, "CLOSEOUT_MERGED_PR_MISMATCH"),
    ("job", "conclusion", "skipped", "CLOSEOUT_REQUIRED_CHECK_NOT_EXECUTED"),
    ("execution", "jobs", [], "CLOSEOUT_JOBS_INCOMPLETE"),
])
def test_merged_consumers_preserve_refusal_cause(bound_case, consumer, target, key, value, expected):
    """A generic ValueError handler must not relabel typed closeout refusals."""
    ledger, report = derive(bound_case)
    observation = bound_case[1]
    execution = report["execution"]
    targets = {"observation": observation, "github": observation["github"], "report": report,
               "execution": execution, "pull": execution["pull"], "run": execution["run"],
               "job": execution["jobs"][0]}
    targets[target][key] = value
    if target in {"execution", "pull", "run", "job"}:
        report["execution_sha256"] = tl.digest(execution)
    elif target == "report" and key == "execution":
        report["execution_sha256"] = tl.digest(value)
    with pytest.raises(lo.ObservationRefusal) as caught:
        if consumer == "issue-body":
            task_closeout.evidenced_issue_body(ledger, observation)
        else:
            task_closeout._assert_mutation_ready(consumer, ledger, observation)
    assert str(caught.value) == expected


def test_missing_merged_receipt_remains_refused(bound_case):
    ledger, _ = derive(bound_case)
    observation = bound_case[1]
    del observation["github"]["closeout_run"]
    with pytest.raises(lo.ObservationRefusal) as caught:
        task_closeout._assert_mutation_ready("close-issue", ledger, observation)
    assert str(caught.value) == "CLOSEOUT_RECEIPT_MISSING_OR_INVALID"


def test_current_merged_receipt_still_permits_closeout(bound_case):
    ledger, _ = derive(bound_case)
    observation = bound_case[1]
    evaluation = task_closeout._assert_mutation_ready("close-issue", ledger, observation)
    assert evaluation["goal_reached"] is True
    assert evaluation["hard_blockers"] == []
    assert task_closeout.evidenced_issue_body(ledger, observation) == (BODY, ["AC-RUN"])


def test_copied_success_cannot_bypass_recomputed_criterion_gate(bound_case):
    ledger, report = derive(bound_case)
    observation = bound_case[1]
    report["execution"]["jobs"][0]["steps"][0]["conclusion"] = "skipped"
    report["execution_sha256"] = tl.digest(report["execution"])
    assert report["closure_ready"] is True
    assert task_closeout.evidenced_issue_body(ledger, observation)[1] == []
    with pytest.raises(tl.LifecycleError, match="merged criterion execution and closure proof"):
        task_closeout._assert_mutation_ready("close-issue", ledger, observation)


@pytest.mark.parametrize("target,key,value,reason", [
    ("pull", "head", None, "MERGED_PR_MISMATCH"),
    ("run", "repository", None, "MERGE_RUN_MISMATCH"),
    ("pull", "number", 78, "MERGED_PR_MISMATCH"),
    ("pull", "head", {"sha": "c" * 40}, "MERGED_PR_MISMATCH"),
    ("pull", "merge_commit_sha", "c" * 40, "MERGED_PR_MISMATCH"),
    ("pull", "merged", False, "MERGED_PR_MISMATCH"),
    ("pull", "base", {"repo": {"full_name": "other/repo"}}, "MERGED_PR_MISMATCH"),
    ("run", "id", True, "MERGE_RUN_MISMATCH"),
    ("run", "run_attempt", 0, "MERGE_RUN_MISMATCH"),
    ("run", "event", "pull_request", "MERGE_RUN_MISMATCH"),
    ("run", "head_sha", "c" * 40, "MERGE_RUN_MISMATCH"),
    ("run", "repository", {"full_name": "other/repo"}, "MERGE_RUN_MISMATCH"),
    ("run", "head_branch", "gh-readonly-queue/main/pr-78-abcdef", "MERGE_RUN_MISMATCH"),
    ("run", "path", ".github/workflows/unrelated.yml", "MERGE_RUN_MISMATCH"),
    ("run", "status", "in_progress", "MERGE_RUN_MISMATCH"),
    ("run", "conclusion", "cancelled", "MERGE_RUN_MISMATCH"),
    ("run", "conclusion", "skipped", "MERGE_RUN_MISMATCH"),
    ("run", "run_started_at", "2026-07-17T10:00:00Z", "MERGE_RUN_STALE"),
    ("run", "created_at", None, "MERGE_RUN_STALE"),
    ("run", "created_at", "2026-07-15T09:00:00Z", "MERGE_RUN_STALE"),
    ("job", "started_at", "2026-07-16T09:00:00Z", "REQUIRED_CHECK_NOT_EXECUTED"),
    ("job", "run_id", 124, "JOB_RUN_MISMATCH"),
    ("job", "run_attempt", 1, "JOB_RUN_MISMATCH"),
    ("job", "head_sha", "c" * 40, "JOB_RUN_MISMATCH"),
    ("job", "html_url", RUN_URL + "/job/999", "JOB_RUN_MISMATCH"),
    ("job", "conclusion", "skipped", "REQUIRED_CHECK_NOT_EXECUTED"),
    ("job", "conclusion", "cancelled", "REQUIRED_CHECK_NOT_EXECUTED"),
    ("job", "status", "in_progress", "REQUIRED_CHECK_NOT_EXECUTED"),
    ("job", "started_at", "not-a-timestamp", "REQUIRED_CHECK_NOT_EXECUTED"),
    ("job", "completed_at", None, "REQUIRED_CHECK_NOT_EXECUTED"),
    ("job", "completed_at", "2026-07-17T10:00:00Z", "REQUIRED_CHECK_NOT_EXECUTED"),
])
def test_rejects_wrong_or_unexecuted_authority(bound_case, target, key, value, reason):
    _, _, pull, run, jobs = bound_case
    {"pull": pull, "run": run, "job": jobs[0]}[target][key] = value
    with pytest.raises(lo.ObservationRefusal, match="CLOSEOUT_" + reason):
        derive(bound_case)


@pytest.mark.parametrize("jobs", [[], [{"id": 1}, {"id": 1}]])
def test_incomplete_jobs_are_not_receipts(bound_case, jobs):
    with pytest.raises(lo.ObservationRefusal, match="JOBS_INCOMPLETE"):
        derive((*bound_case[:4], jobs))


@pytest.mark.parametrize("mutation", ["no_mapping", "wrong_job", "missing_step", "skipped_step", "cancelled_step",
                                      "unfinished_step", "no_steps", "malformed_steps", "missing_required_check", "step_after_job", "step_before_job"])
def test_green_gate_never_substitutes_for_executed_criterion(bound_case, mutation):
    ledger, observation, _pull, _run, jobs = bound_case
    row = ledger["evidence"][0]
    if mutation == "no_mapping":
        row["details"] = {}
    elif mutation == "wrong_job":
        row["url"] = RUN_URL + "/job/999"
    elif mutation == "missing_step":
        row["details"]["step_names"] = ["Unexecuted tests"]
    elif mutation == "skipped_step":
        jobs[0]["steps"][0]["conclusion"] = "skipped"
    elif mutation == "cancelled_step":
        jobs[0]["steps"][0]["conclusion"] = "cancelled"
    elif mutation == "unfinished_step":
        jobs[0]["steps"][0]["status"] = "in_progress"
    elif mutation == "no_steps":
        jobs[0]["steps"] = []
    elif mutation == "malformed_steps":
        jobs[0]["steps"] = [None]
    elif mutation == "step_after_job":
        jobs[0]["steps"][0]["completed_at"] = "2026-07-16T09:06:00Z"
    elif mutation == "step_before_job":
        jobs[0]["steps"][0]["started_at"] = "2026-07-16T09:00:00Z"
    elif mutation == "missing_required_check":
        jobs[0]["name"] = "Other workflow"
        with pytest.raises(lo.ObservationRefusal, match="REQUIRED_CHECK_NOT_EXECUTED"):
            derive(bound_case)
        return
    row["id"] = tl.digest(tl._evidence_payload(row))
    updated, report = derive(bound_case)
    assert report["closure_ready"] is False
    assert report["criteria"] == [{"ac_id": "AC-RUN", "passed": False, "missing": ["ci", "test"], "executed": []}]
    assert updated["evidence"] == ledger["evidence"]
    assert observation["github"]["error"] == "CLOSEOUT_CRITERION_EXECUTION_OR_PROOF_MISSING"


@pytest.mark.parametrize("kind", ["behavior_proof", "deployment"])
def test_product_or_deployment_evidence_is_never_created(bound_case, kind):
    ledger, _observation_value, *_ = bound_case
    ledger["ac_snapshot"]["criteria"][0]["required_evidence"].append(kind)
    ledger["ac_snapshot"]["content_hash"] = tl.ac_content_hash(ledger["ac_snapshot"]["criteria"])
    updated, report = derive(bound_case)
    assert report["closure_ready"] is False
    assert report["criteria"][0]["missing"] == [kind]
    assert all(row["type"] != kind for row in updated["evidence"])
    assert report["cleanup_residual"] is False


def test_genuine_behavior_reference_is_retained_and_revalidated(bound_case, tmp_path):
    ledger, observation, pull, run, jobs = bound_case
    ledger["ac_snapshot"]["criteria"][0]["required_evidence"].append("behavior_proof")
    ledger["ac_snapshot"]["content_hash"] = tl.ac_content_hash(ledger["ac_snapshot"]["criteria"])
    details = _behavior_receipt_reference(tmp_path)
    ledger = evidence(ledger, "behavior_proof", details=details)
    updated, report = derive((ledger, observation, pull, run, jobs))
    assert report["closure_ready"] is True
    assert updated["evidence"][-2]["details"] == details
    reference = details["behavior_proof_receipt"]
    from pathlib import Path
    Path(reference["receipt_path"]).write_text("{}")
    _, rejected = derive((ledger, _observation(BODY, pr_state="MERGED", clean=True), pull, run, jobs))
    assert rejected["closure_ready"] is False
    assert rejected["criteria"][0]["missing"] == ["behavior_proof"]


def test_cleanup_residual_is_distinct_from_product_proof(bound_case):
    _ledger_value, observation, *_ = bound_case
    observation["local"]["worktree_present"] = True
    _, report = derive(bound_case)
    assert report["criteria_passed"] is True
    assert report["cleanup_residual"] is True
    assert report["closure_ready"] is False
    assert report["criteria"][0]["missing"] == []


def test_all_closure_due_criteria_include_cleanup_boundary(bound_case):
    ledger, observation, *_ = bound_case
    criteria = ledger["ac_snapshot"]["criteria"]
    criteria.append({"id": "AC-CLEAN", "text": "Cleanup is proven.", "applicable": True,
                     "due_state": "CLEANED_UP", "required_evidence": ["cleanup"], "behavior_proof_required": False})
    ledger["ac_snapshot"]["content_hash"] = tl.ac_content_hash(criteria)
    observation["github"]["issue"]["body"] += "- [x] **AC-CLEAN** — Cleanup is proven.\n"
    _, report = derive(bound_case)
    assert report["criteria"][1] == {"ac_id": "AC-CLEAN", "passed": False, "missing": ["cleanup"], "executed": []}
    assert report["closure_ready"] is False


def test_capture_persists_bound_receipt_without_inventing_local_history(bound_case, tmp_path, monkeypatch):
    ledger, observation, pull, run, jobs = bound_case
    monkeypatch.setattr(tl, "canonical_state_root", lambda _: tmp_path)
    path = tl.lifecycle_path(tmp_path, ledger["identity"])
    tl.write_lifecycle(path, ledger)
    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "observe", lambda *a, **k: deepcopy(observation))
    def api(root, request):
        if request.verb == "read-pull":
            return pull
        if request.verb == "read-jobs":
            assert request.fields["number"] == 123
            return [{"total_count": 1, "jobs": jobs}]
        if request.verb == "read-run":
            return run
        assert request.verb == "read-runs"
        return [{"total_count": 1, "workflow_runs": [run]}]
    monkeypatch.setattr(mc, "_closeout_api", api)
    pr = mc.PullRequestInfo(77, "MERGED", "codex/42-closeout", HEAD)
    reports = mc.collect_criterion_receipts(tmp_path, pr, repo="org/repo")
    assert len(reports) == 1
    assert reports[0]["closure_ready"] is True
    saved = tl.load_lifecycle(path)
    assert saved["evidence"][:-1] == ledger["evidence"]
    assert saved["observation_receipts"][-1]["observation"]["github"]["closeout_run"]["run_id"] == 123
    assert saved["observation_receipts"][-1]["observation"]["local"] == observation["local"]
    assert mc.collect_criterion_receipts(tmp_path, pr, repo="org/repo")[0]["closure_ready"] is True
    assert len(tl.load_lifecycle(path)["evidence"]) == len(saved["evidence"])


@pytest.mark.parametrize("failure", ["moved_head", "missing_merge", "no_run", "invalid_run", "unreadable"])
def test_capture_failure_does_not_append_evidence(bound_case, tmp_path, monkeypatch, failure):
    ledger, observation, pull, run, _ = bound_case
    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "observe", lambda *a, **k: deepcopy(observation))
    monkeypatch.setattr(tl, "canonical_state_root", lambda _: tmp_path)
    path = tl.lifecycle_path(tmp_path, ledger["identity"])
    tl.write_lifecycle(path, ledger)
    before = path.read_bytes()
    def api(root, request):
        if failure == "unreadable":
            raise mc.MergeCloseoutError("CLOSEOUT_EXECUTION_UNREADABLE")
        if request.verb == "read-pull":
            if failure == "moved_head":
                pull["head"]["sha"] = "c" * 40
            if failure == "missing_merge":
                pull["merge_commit_sha"] = None
            return pull
        if failure == "invalid_run":
            run["id"] = True
        return [{"total_count": 0 if failure == "no_run" else 1,
                 "workflow_runs": [] if failure == "no_run" else [run]}]
    monkeypatch.setattr(mc, "_closeout_api", api)
    report = mc.collect_criterion_receipts(tmp_path, mc.PullRequestInfo(77, "MERGED", "branch", HEAD), repo="org/repo")
    assert report[0]["closure_ready"] is False
    assert "CLOSEOUT_" in report[0]["error"]
    assert path.read_bytes() == before


@pytest.mark.parametrize("payload", ["invalid-json", "null", "42"])
def test_api_unreadable_is_a_typed_refusal(tmp_path, monkeypatch, payload):
    monkeypatch.setattr(mc, "request_run", lambda *a, **k: subprocess.CompletedProcess([], 0, payload, ""))
    with pytest.raises(mc.MergeCloseoutError, match="EXECUTION_UNREADABLE"):
        mc._closeout_api(tmp_path, mc.Request("read-run", repo="org/repo", number=123))


def test_api_transport_error_is_a_typed_refusal(tmp_path, monkeypatch):
    def fail(*a, **k):
        raise subprocess.TimeoutExpired("gh", 30)
    monkeypatch.setattr(mc, "request_run", fail)
    with pytest.raises(mc.MergeCloseoutError, match="EXECUTION_UNREADABLE"):
        mc._closeout_api(tmp_path, mc.Request("read-run", repo="org/repo", number=123))


def test_pages_require_complete_execution(tmp_path, monkeypatch):
    pages = [{"total_count": 2, "jobs": [{"id": 1}]}, {"total_count": 2, "jobs": [{"id": 2}]}]
    monkeypatch.setattr(mc, "_closeout_api", lambda *a: pages)
    assert mc._closeout_pages(tmp_path, "endpoint", "jobs") == [{"id": 1}, {"id": 2}]


@pytest.mark.parametrize("page", [{"jobs": []}, {"total_count": 1, "jobs": []}, {"total_count": 0, "jobs": [None]}])
def test_pages_reject_missing_or_incomplete_results(tmp_path, monkeypatch, page):
    monkeypatch.setattr(mc, "_closeout_api", lambda *a: [page])
    with pytest.raises(mc.MergeCloseoutError, match="EXECUTION_INCOMPLETE"):
        mc._closeout_pages(tmp_path, "endpoint", "jobs")


def test_nonapplicable_criterion_stays_outside_denominator(bound_case):
    ledger = bound_case[0]
    ledger["ac_snapshot"]["criteria"].append({
        "id": "AC-NA", "text": "Not applicable.", "applicable": False, "due_state": "MERGED",
        "required_evidence": ["deployment"], "behavior_proof_required": False,
    })
    ledger["ac_snapshot"]["content_hash"] = tl.ac_content_hash(ledger["ac_snapshot"]["criteria"])
    bound_case[1]["github"]["issue"]["body"] += "- [ ] **AC-NA** — Not applicable.\n"
    _, report = derive(bound_case)
    assert report["closure_ready"] is True
    assert [item["ac_id"] for item in report["criteria"]] == ["AC-RUN"]


def test_ci_alone_cannot_substitute_for_deploy_terminal_goal(bound_case):
    original, observation, pull, run, jobs = bound_case
    ledger = tl.build_lifecycle(_identity("deploy"), author_family="codex", ac_snapshot=original["ac_snapshot"],
                               required_checks=["CI Gate"], now=NOW, pr_number=77)
    ledger["evidence"] = original["evidence"]
    ledger, _, _ = tl.reconcile(ledger, _observation(BODY), now=NOW)
    _, report = derive((ledger, observation, pull, run, jobs))
    assert report["criteria_passed"] is True
    assert report["closure_ready"] is False
    assert report["cleanup_residual"] is False


def test_unchecked_late_criterion_cannot_pass_close_gate(bound_case):
    bound_case[1]["github"]["issue"]["body"] = BODY.replace("[x]", "[ ]")
    _, report = derive(bound_case)
    assert report["criteria_passed"] is True
    assert report["closure_ready"] is False
    assert report["unchecked_criteria"] == ["AC-RUN"]


def test_run_attempt_moving_during_read_is_not_persisted(bound_case, tmp_path, monkeypatch):
    ledger, observation, pull, run, _ = bound_case
    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "observe", lambda *a, **k: deepcopy(observation))
    monkeypatch.setattr(tl, "canonical_state_root", lambda _: tmp_path)
    path = tl.lifecycle_path(tmp_path, ledger["identity"])
    tl.write_lifecycle(path, ledger)
    before = path.read_bytes()
    def api(root, request):
        if request.verb == "read-pull":
            return pull
        if request.verb == "read-runs":
            return [{"total_count": 1, "workflow_runs": [run]}]
        return {**run, "run_attempt": 3}
    monkeypatch.setattr(mc, "_closeout_api", api)
    report = mc.collect_criterion_receipts(tmp_path, mc.PullRequestInfo(77, "MERGED", "branch", HEAD), repo="org/repo")
    assert report == [{"closure_ready": False, "error": "CLOSEOUT_RUN_ATTEMPT_MOVED"}]
    assert path.read_bytes() == before


def test_capture_no_ledger_and_unknown_repository_are_explicit(tmp_path, monkeypatch):
    monkeypatch.setattr(tl, "canonical_state_root", lambda _: tmp_path)
    pr = mc.PullRequestInfo(77, "MERGED", "branch", HEAD)
    assert mc.collect_criterion_receipts(tmp_path, pr, repo="org/repo") == []
    monkeypatch.setattr(mc.rw, "_github_owner_repo", lambda _: None)
    assert mc.collect_criterion_receipts(tmp_path, pr, repo=None) == [
        {"closure_ready": False, "error": "CLOSEOUT_REPOSITORY_UNKNOWN"},
    ]


def test_pages_refuse_a_count_that_changes_between_pages(tmp_path, monkeypatch):
    monkeypatch.setattr(mc, "_closeout_api", lambda *a: [
        {"total_count": 2, "jobs": [{"id": 1}]}, {"total_count": 1, "jobs": []},
    ])
    with pytest.raises(mc.MergeCloseoutError, match="EXECUTION_INCOMPLETE"):
        mc._closeout_pages(tmp_path, "request", "jobs")


def test_duplicate_pages_cannot_hide_another_execution(tmp_path, monkeypatch):
    monkeypatch.setattr(mc, "_closeout_api", lambda *a: [
        {"total_count": 2, "jobs": [{"id": 1}]}, {"total_count": 2, "jobs": [{"id": 1}]},
    ])
    with pytest.raises(mc.MergeCloseoutError, match="EXECUTION_INCOMPLETE"):
        mc._closeout_pages(tmp_path, "request", "jobs")
