"""Strict merge-check transport regressions for #9358; no network calls."""

import json
import subprocess
from pathlib import Path

import pytest

from scripts.opsec.prepublish import PublishBlocked
from scripts.publish.merge_guard import ensure_merge_ready


@pytest.fixture(autouse=True)
def _advisory_fixture_workflow(monkeypatch):
    """The real ci.yml has no advisory job; cover the rule with a fixture workflow."""
    from scripts.ci import advisory_checks

    monkeypatch.setattr(
        advisory_checks,
        "CI_WORKFLOW_PATH",
        Path(__file__).resolve().parents[2] / "tests/fixtures/ci_advisory_workflow.yml",
    )

def merge_with_checks(stdout, returncode=0):
    def runner(args, **kwargs):
        if args[1] == "api":
            checks = json.loads(stdout)
            if "/check-runs?" in args[4]:
                body = {"total_count": len(checks), "check_runs": [
                    {"name": row["name"], "head_sha": "a" * 40,
                     "status": "in_progress" if row["bucket"] == "pending" else "completed",
                     "conclusion": "" if row["bucket"] == "pending" else
                         "failure" if row["bucket"] == "fail" else "success",
                     "app": {"id": 15368, "slug": "github-actions"}, "check_suite": {"id": i},
                     "details_url": f"https://github.com/unit/public/actions/runs/{i}/job/{i}"}
                    for i, row in enumerate(checks, 1)
                ]}
            else:
                i = int(args[4].rsplit("/", 1)[1])
                body = {"id": i, "head_sha": "a" * 40, "check_suite_id": i,
                        "workflow_id": i, "name": checks[i - 1].get("workflow")}
            return subprocess.CompletedProcess(args, 0, json.dumps(body), "")
        if args[2] == "view":
            meta = {"number": 1, "isDraft": False, "headRefOid": "a" * 40}
            if "headRefOid,statusCheckRollup" in args:
                checks = json.loads(stdout)
                meta["statusCheckRollup"] = [
                    {"__typename": "CheckRun", "name": row["name"],
                     "detailsUrl": f"https://github.com/unit/public/actions/runs/{i}/job/{i}",
                     "status": "IN_PROGRESS" if row["bucket"] == "pending" else "COMPLETED",
                     "conclusion": "" if row["bucket"] == "pending" else
                         "FAILURE" if row["bucket"] == "fail" else "SUCCESS"}
                    for i, row in enumerate(checks, 1)
                ]
            return subprocess.CompletedProcess(args, 0, json.dumps(meta), "")
        assert args[2] == "checks"
        return subprocess.CompletedProcess(args, returncode, stdout, "")

    return ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})


@pytest.mark.parametrize("stdout", ["", " \n\t", "not JSON", "[", "null", "{}"])
def test_unestablished_check_state_is_refused(stdout):
    with pytest.raises(PublishBlocked, match="cannot establish check state"):
        merge_with_checks(stdout)


def test_explicit_empty_json_check_list_is_allowed():
    assert merge_with_checks("[]") == "a" * 40


@pytest.mark.parametrize("returncode", [2, 3])
def test_valid_json_with_transport_failure_is_refused(returncode):
    with pytest.raises(PublishBlocked, match="cannot establish check state"):
        merge_with_checks("[]", returncode)


@pytest.mark.parametrize("returncode,bucket", [(1, "fail"), (8, "pending")])
def test_known_nonzero_check_statuses_still_block(returncode, bucket):
    with pytest.raises(PublishBlocked):
        merge_with_checks(json.dumps([{"name": "CI Gate", "bucket": bucket}]), returncode)


def test_empty_json_check_list_with_exit_code_1_is_refused():
    with pytest.raises(PublishBlocked, match="cannot establish check state"):
        merge_with_checks("[]", returncode=1)


def test_failing_advisory_check_with_exit_code_1_allows_merge():
    checks = [
        {"name": "CI Gate", "bucket": "pass"},
        {"name": "Component shadow (advisory)", "bucket": "fail", "workflow": "CI"},
    ]
    assert merge_with_checks(json.dumps(checks), returncode=1) == "a" * 40


@pytest.mark.parametrize("identity", [
    {}, {"workflow": None}, {"workflow": ""}, {"workflow": "Nightly"}, {"workflowName": "CI"},
])
def test_failing_advisory_name_without_ci_workflow_blocks_merge(identity):
    checks = [
        {"name": "CI Gate", "bucket": "pass"},
        {"name": "Component shadow (advisory)", "bucket": "fail", **identity},
    ]
    with pytest.raises(PublishBlocked, match=r"merge refused: FAILING checks\."):
        merge_with_checks(json.dumps(checks), returncode=1)


# --- OO-48 external advisory provenance (#11184) ------------------------------------------
# The publisher/hook parity matrix lives in tests/test_advisory_checks.py.

HEAD = "a" * 40
ENTIRE_ROWS = [{"name": "CI Gate", "bucket": "pass", "workflow": "CI"}, {"name": "Entire Gates", "bucket": "pending"}]
RUNS = f"repos/unit/public/commits/{HEAD}/check-runs?check_name=Entire%20Gates&filter=all&per_page=100"
STATUS = f"repos/unit/public/commits/{HEAD}/status?per_page=100"


BOUND_ROLLUP = [
    {"__typename": "CheckRun", "name": "CI Gate", "status": "COMPLETED", "conclusion": "SUCCESS", "workflowName": "CI"},
    {"__typename": "CheckRun", "name": "Entire Gates", "status": "IN_PROGRESS", "conclusion": "", "workflowName": ""},
]


def entire_runner(app, calls, *, head=HEAD, error=None, bound=None, extra_documents=None):
    def runner(args, **kwargs):
        calls.append(args)
        if args[2:5] == ["view", "1", "--json"] and args[5] == "headRefOid,statusCheckRollup":
            reply = {"headRefOid": head, "statusCheckRollup": BOUND_ROLLUP} if bound is None else bound
            return subprocess.CompletedProcess(args, 0, json.dumps(reply), "")
        if args[2] == "view":
            return subprocess.CompletedProcess(args, 0, json.dumps({"number": 1, "isDraft": False, "headRefOid": head}), "")
        if args[2] == "checks":
            return subprocess.CompletedProcess(args, 8, json.dumps(ENTIRE_ROWS), "")
        if error is not None:
            raise error
        documents = {
            STATUS: {"total_count": 0, "statuses": []},
            RUNS: {"total_count": 1, "check_runs": [{"name": "Entire Gates", "head_sha": HEAD, "app": app}]},
            **(extra_documents or {}),
        }
        if args[:4] == ["gh", "api", "--method", "GET"] and args[4] in documents:
            return subprocess.CompletedProcess(args, 0, json.dumps(documents[args[4]]), "")
        return subprocess.CompletedProcess(args, 1, "", "HTTP 404")

    return runner


def test_oo48_publisher_proves_entire_gates_at_the_metadata_head():
    """Superseded Actions cancellations must preserve the external app proof gate."""
    calls = []
    app = {"id": 2626939, "slug": "entire"}
    old = {"name": "Body guard", "head_sha": HEAD, "status": "completed", "conclusion": "cancelled",
           "started_at": "2026-10-23T20:00:00Z", "check_suite": {"id": 1},
           "app": {"id": 15368, "slug": "github-actions"},
           "details_url": "https://github.com/unit/public/actions/runs/11/job/21"}
    current = {**old, "conclusion": "success", "started_at": "2026-10-23T21:00:00Z",
               "check_suite": {"id": 2}, "details_url": "https://github.com/unit/public/actions/runs/12/job/22"}
    rest = [current, old,
            {"name": "CI Gate", "head_sha": HEAD, "status": "completed", "conclusion": "success",
             "details_url": "https://github.com/unit/public/runs/23"},
            {"name": "Entire Gates", "head_sha": HEAD, "status": "in_progress", "app": app,
             "details_url": "https://github.com/unit/public/runs/24"}]
    rollup = [{"__typename": "CheckRun", "name": row["name"], "status": row["status"].upper(),
               "conclusion": str(row.get("conclusion") or "").upper(), "detailsUrl": row["details_url"]}
              for row in rest]
    endpoint = f"repos/unit/public/commits/{HEAD}/check-runs?filter=all&per_page=100"
    documents = {endpoint: {"total_count": len(rest), "check_runs": rest},
                 "repos/unit/public/actions/runs/11": {"id": 11, "head_sha": HEAD, "check_suite_id": 1,
                                                       "workflow_id": 7, "name": "Body guard"},
                 "repos/unit/public/actions/runs/12": {"id": 12, "head_sha": HEAD, "check_suite_id": 2,
                                                       "workflow_id": 7, "name": "Body guard"}}
    runner = entire_runner(app, calls, bound={"headRefOid": HEAD, "statusCheckRollup": rollup},
                           extra_documents=documents)
    assert ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={}, match_head=HEAD) == HEAD
    assert [call[1:6] for call in calls] == [
        ["pr", "view", "1", "--json", "number,isDraft,headRefOid"],
        ["pr", "checks", "1", "--json", "name,bucket,state,workflow"],
        ["pr", "view", "1", "--json", "headRefOid,statusCheckRollup"],
        ["api", "--method", "GET", STATUS], ["api", "--method", "GET", RUNS],
        ["api", "--method", "GET", endpoint],
        ["api", "--method", "GET", "repos/unit/public/actions/runs/12"],
        ["api", "--method", "GET", "repos/unit/public/actions/runs/11"]]


@pytest.mark.parametrize("bound", [
    {"headRefOid": "b" * 40, "statusCheckRollup": BOUND_ROLLUP},
    {"statusCheckRollup": BOUND_ROLLUP},
    {"headRefOid": HEAD, "statusCheckRollup": None},
    {"headRefOid": HEAD},
    [],
])
def test_oo48_publisher_refuses_rows_not_bound_to_the_metadata_head(bound):
    calls = []
    runner = entire_runner({"id": 2626939, "slug": "entire"}, calls, bound=bound)
    with pytest.raises(PublishBlocked, match="cannot establish check state"):
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={}, match_head=HEAD)
    assert all(call[1] != "api" for call in calls)


def test_oo48_publisher_judges_the_bound_rollup_not_the_headless_rows():
    red = [{**BOUND_ROLLUP[0], "conclusion": "FAILURE"}, BOUND_ROLLUP[1]]
    runner = entire_runner({"id": 2626939, "slug": "entire"}, [], bound={"headRefOid": HEAD, "statusCheckRollup": red})
    with pytest.raises(PublishBlocked, match=r"merge refused: FAILING checks\."):
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})


OLD_CLIENT = (
    "unknown flag: --json\n\nUsage:  gh pr checks [<number> | <url> | <branch>] [flags]\n\n"
    "Flags:\n      --fail-fast         Exit watch mode on first check failure\n"
)


@pytest.mark.parametrize("rollup,ready", [(None, False), ({}, False), ("", False), (False, False), (0, False),
                                          ([], True)])
def test_publisher_old_client_rollup_must_be_a_list(rollup, ready):
    def runner(args, **kwargs):
        if args[2] == "checks":
            return subprocess.CompletedProcess(args, 1, "", OLD_CLIENT)
        if "headRefOid,statusCheckRollup" in args:
            return subprocess.CompletedProcess(args, 0, json.dumps({"headRefOid": HEAD, "statusCheckRollup": rollup}), "")
        return subprocess.CompletedProcess(args, 0, json.dumps({"number": 1, "isDraft": False, "headRefOid": HEAD}), "")

    if ready:
        assert ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={}) == HEAD
    else:
        with pytest.raises(PublishBlocked, match="cannot establish check state"):
            ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})


@pytest.mark.parametrize("app", [{"id": 15368, "slug": "github-actions"}, None, {"id": "2626939", "slug": "entire"}])
def test_oo48_publisher_refuses_unproven_entire_gates(app):
    with pytest.raises(PublishBlocked, match="cannot establish check state"):
        ensure_merge_ready("unit/public", 1, runner=entire_runner(app, []), cwd=".", environment={})


def test_oo48_exemption_never_waives_the_reviewed_head():
    runner = entire_runner({"id": 2626939, "slug": "entire"}, [])
    with pytest.raises(PublishBlocked, match="reviewed head changed"):
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={}, match_head="b" * 40)


def test_oo48_rate_limit_during_provenance_is_not_masked():
    from scripts.common.github_client import GitHubRateLimited

    limited = GitHubRateLimited(None, "fixture")
    runner = entire_runner({"id": 2626939, "slug": "entire"}, [], error=limited)
    with pytest.raises(GitHubRateLimited):
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})


def test_oo48_garbage_provenance_reply_is_refused():
    def runner(args, **kwargs):
        if args[1] == "api":
            return subprocess.CompletedProcess(args, 0, "not JSON", "")
        return entire_runner({"id": 2626939, "slug": "entire"}, [])(args, **kwargs)

    with pytest.raises(PublishBlocked, match="cannot establish check state"):
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})
