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
    """Distinct vendor details and canonical check URLs must preserve App proof."""
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
             "id": 24, "html_url": "https://github.com/unit/public/runs/24",
             "details_url": "https://entire.com/gh/unit/public/trails/7"}]
    rollup = [{"__typename": "CheckRun", "name": row["name"], "status": row["status"].upper(),
               "conclusion": str(row.get("conclusion") or "").upper(),
               "detailsUrl": row.get("html_url", row["details_url"])}
              for row in rest]
    rollup.append({"__typename": "StatusContext", "context": "external-status", "state": "SUCCESS"})
    endpoint = f"repos/unit/public/commits/{HEAD}/check-runs?filter=all&per_page=100"
    documents = {STATUS: {"total_count": 1, "statuses": [{"context": "external-status", "state": "success"}]},
                 endpoint: {"total_count": len(rest), "check_runs": rest},
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


# --- pr-merge's own read transport over a multi-page head ------------------------------------
# The publisher sends the guard's reads through merge_readiness_runner, where github_client
# translates `gh pr view --json statusCheckRollup` and `gh api` into REST pages. A head with
# more check runs than one page must reach the verdict a plain gh runner reaches.

API = "https://api.github.com/"
ACTIONS = {"id": 15368, "slug": "github-actions"}


def _check_run(number, name="", **fields):
    return {"id": number, "name": name or f"Job {number}", "head_sha": HEAD, "status": "completed",
            "conclusion": "success", "html_url": f"https://github.com/unit/public/runs/{number}",
            "details_url": f"https://example.invalid/{number}", "started_at": "2026-10-28T16:00:00Z", **fields}


def _multi_page_head(runs, *, second_total=None):
    """REST documents for a head whose check runs span two pages of 100."""
    pull = {"number": 1, "state": "open", "draft": False, "head": {"sha": HEAD, "ref": "fix", "repo": {"full_name": "unit/public"}},
            "base": {"ref": "main", "repo": {"full_name": "unit/public"}}}
    documents = {"repos/unit/public/pulls/1": (pull, None),
                 f"repos/unit/public/commits/{HEAD}/status?per_page=100": ({"total_count": 0, "statuses": []}, None)}
    for endpoint in (f"repos/unit/public/commits/{HEAD}/check-runs?per_page=100",
                     f"repos/unit/public/commits/{HEAD}/check-runs?filter=all&per_page=100"):
        documents[endpoint] = ({"total_count": len(runs), "check_runs": runs[:100]}, f"{API}{endpoint}&page=2")
        documents[endpoint + "&page=2"] = ({"total_count": second_total or len(runs), "check_runs": runs[100:]}, None)
    return documents


def _publisher_transport(tmp_path, monkeypatch, documents, checks):
    """merge_readiness_runner over a real GitHubClient whose HTTP and native gh are fixtures."""
    from scripts.common import github_client as gh
    from scripts.publish.github import merge_readiness_runner

    real_client, requested = gh.GitHubClient, []

    def transport(method, endpoint, headers, body, timeout):
        path = endpoint.removeprefix(API)
        requested.append(path)
        if path not in documents:
            return gh.Response(404, {"X-RateLimit-Remaining": "5000"}, b'{"message": "Not Found"}')
        value, link = documents[path]
        reply = {"ETag": f'"{len(requested)}"', "X-RateLimit-Remaining": "5000", "X-RateLimit-Reset": "2000"}
        if link:
            reply["Link"] = f'<{link}>; rel="next"'
        return gh.Response(200, reply, json.dumps(value).encode())

    def native(args, **kwargs):
        assert args[1:3] == ["pr", "checks"], args
        return subprocess.CompletedProcess(args, 0, json.dumps(checks).encode(), b"")

    monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(gh, "GitHubClient", lambda **kwargs: real_client(
        **{**kwargs, "cache_dir": tmp_path, "transport": transport, "runner": native}))
    return merge_readiness_runner(), requested


def test_publisher_transport_reads_every_check_run_page_of_a_multi_page_head(tmp_path, monkeypatch):
    """136 check runs, two of one name superseded across workflow runs: READY, as with plain gh."""
    runs = [_check_run(n) for n in range(1, 135)]
    runs += [_check_run(135, "Body guard", conclusion="cancelled", app=ACTIONS, check_suite={"id": 1},
                        started_at="2026-10-28T15:00:00Z",
                        details_url="https://github.com/unit/public/actions/runs/11/job/135"),
             _check_run(136, "Body guard", app=ACTIONS, check_suite={"id": 2},
                        details_url="https://github.com/unit/public/actions/runs/12/job/136")]
    documents = _multi_page_head(runs)
    for run_id, suite in ((11, 1), (12, 2)):
        documents[f"repos/unit/public/actions/runs/{run_id}"] = (
            {"id": run_id, "head_sha": HEAD, "check_suite_id": suite, "workflow_id": 7, "name": "Body guard"}, None)
    checks = [{"name": row["name"], "bucket": "pass", "state": "SUCCESS", "workflow": ""} for row in runs]
    runner, requested = _publisher_transport(tmp_path, monkeypatch, documents, checks)
    environment = {"GH_HOST": "github.com", "GH_TOKEN": "fixture-only"}
    assert ensure_merge_ready("unit/public", 1, runner=runner, cwd=tmp_path, environment=environment,
                              match_head=HEAD) == HEAD
    assert f"repos/unit/public/commits/{HEAD}/check-runs?per_page=100&page=2" in requested
    assert f"repos/unit/public/commits/{HEAD}/check-runs?filter=all&per_page=100&page=2" in requested
    assert {"repos/unit/public/actions/runs/11", "repos/unit/public/actions/runs/12"} <= set(requested)


def test_publisher_transport_refusal_names_the_read_that_failed(tmp_path, monkeypatch):
    """A rollup whose total shifts between pages stays unverifiable, and the refusal says which read."""
    runs = [_check_run(n) for n in range(1, 137)]
    documents = _multi_page_head(runs, second_total=137)
    checks = [{"name": row["name"], "bucket": "pass", "state": "SUCCESS", "workflow": ""} for row in runs]
    runner, _ = _publisher_transport(tmp_path, monkeypatch, documents, checks)
    environment = {"GH_HOST": "github.com", "GH_TOKEN": "fixture-only"}
    with pytest.raises(PublishBlocked) as refused:
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=tmp_path, environment=environment)
    assert str(refused.value) == (
        "OPSEC: merge refused: cannot establish check state (pr view rollup: github_checks_incomplete).")


@pytest.mark.parametrize("second", [
    {"total_count": 101, "check_runs": [_check_run(101), _check_run(102)]},
    {"total_count": True, "check_runs": [_check_run(101)]},
    {"total_count": 101.0, "check_runs": [_check_run(101)]},
    {"total_count": 101},
])
def test_publisher_transport_refuses_an_inexact_multi_page_walk(tmp_path, monkeypatch, second):
    """More rows than the total, a non-integer total or a page without its collection is incomplete."""
    runs = [_check_run(n) for n in range(1, 101)]
    documents = _multi_page_head([*runs, _check_run(101)])
    for endpoint in [path for path in documents if path.endswith("&page=2")]:
        documents[endpoint] = (second, None)
    checks = [{"name": row["name"], "bucket": "pass", "state": "SUCCESS", "workflow": ""} for row in runs]
    runner, _ = _publisher_transport(tmp_path, monkeypatch, documents, checks)
    environment = {"GH_HOST": "github.com", "GH_TOKEN": "fixture-only"}
    with pytest.raises(PublishBlocked, match=r"pr view rollup: github_checks_incomplete"):
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=tmp_path, environment=environment)


def test_publisher_transport_refuses_a_repeated_check_run_across_pages(tmp_path, monkeypatch):
    runs = [_check_run(n) for n in range(1, 137)]
    runs[120] = runs[5]
    checks = [{"name": row["name"], "bucket": "pass", "state": "SUCCESS", "workflow": ""} for row in runs]
    runner, _ = _publisher_transport(tmp_path, monkeypatch, _multi_page_head(runs), checks)
    environment = {"GH_HOST": "github.com", "GH_TOKEN": "fixture-only"}
    with pytest.raises(PublishBlocked, match=r"pr view rollup: github_checks_incomplete"):
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=tmp_path, environment=environment)


def test_refusal_names_a_failed_status_read_for_a_plain_runner():
    base = entire_runner({"id": 2626939, "slug": "entire"}, [])

    def runner(args, **kwargs):
        if args[1] == "api" and args[4] == STATUS:
            return subprocess.CompletedProcess(args, 1, "", "")
        return base(args, **kwargs)

    with pytest.raises(PublishBlocked) as refused:
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})
    assert str(refused.value) == "OPSEC: merge refused: cannot establish check state (commit statuses: exit 1)."


def test_refusal_names_a_failed_actions_run_read_with_gh_http_status():
    details = "https://github.com/unit/public/actions/runs/12/job/22"
    rest = [{"name": "Body guard", "head_sha": HEAD, "status": "completed", "conclusion": "success",
             "check_suite": {"id": 2}, "app": ACTIONS, "details_url": details}]
    rollup = [{"__typename": "CheckRun", "name": "Body guard", "status": "COMPLETED", "conclusion": "SUCCESS",
               "detailsUrl": details}] * 2
    documents = {f"repos/unit/public/commits/{HEAD}/check-runs?filter=all&per_page=100":
                 {"total_count": 1, "check_runs": rest}}
    base = entire_runner({"id": 2626939, "slug": "entire"}, [], extra_documents=documents,
                         bound={"headRefOid": HEAD, "statusCheckRollup": rollup})

    def runner(args, **kwargs):
        if args[1] == "api" and args[4] == "repos/unit/public/actions/runs/12":
            return subprocess.CompletedProcess(args, 1, "", "gh: Not Found (HTTP 404)")
        return base(args, **kwargs)

    with pytest.raises(PublishBlocked) as refused:
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})
    assert str(refused.value) == (
        "OPSEC: merge refused: cannot establish check state (actions run: exit 1 HTTP 404).")


def test_refusal_names_a_read_that_raised():
    base = entire_runner({"id": 2626939, "slug": "entire"}, [])

    def runner(args, **kwargs):
        if "headRefOid,statusCheckRollup" in args:
            raise subprocess.TimeoutExpired(args, 15)
        return base(args, **kwargs)

    with pytest.raises(PublishBlocked) as refused:
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})
    assert str(refused.value) == "OPSEC: merge readiness unverifiable (pr view rollup: TimeoutExpired)."


@pytest.mark.parametrize("returncode,stdout,stderr,named", [
    (1, "", "gh: Not Found (HTTP 404)", "pr checks: exit 1 HTTP 404"),
    (0, "{}", "", "pr checks: invalid shape"),
    (0, "not JSON", "", "pr checks: malformed JSON"),
    (1, "[]", "", "pr checks: empty failing list"),
])
def test_refusal_names_how_the_checks_read_failed(returncode, stdout, stderr, named):
    def runner(args, **kwargs):
        if args[2] == "checks":
            return subprocess.CompletedProcess(args, returncode, stdout, stderr)
        return subprocess.CompletedProcess(args, 0, json.dumps({"number": 1, "isDraft": False, "headRefOid": HEAD}), "")

    with pytest.raises(PublishBlocked) as refused:
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})
    assert str(refused.value) == f"OPSEC: merge refused: cannot establish check state ({named})."


@pytest.mark.parametrize("bound,named", [
    ({"headRefOid": HEAD, "statusCheckRollup": None}, "pr view rollup: invalid shape"),
    (None, "no read failed; check rows unverifiable"),
])
def test_refusal_names_an_invalid_shape_or_says_no_read_failed(bound, named):
    rollup = {"headRefOid": "b" * 40, "statusCheckRollup": BOUND_ROLLUP} if bound is None else bound
    runner = entire_runner({"id": 2626939, "slug": "entire"}, [], bound=rollup)
    with pytest.raises(PublishBlocked) as refused:
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})
    assert str(refused.value) == f"OPSEC: merge refused: cannot establish check state ({named})."


def test_refusal_names_a_status_read_of_the_wrong_shape():
    base = entire_runner({"id": 2626939, "slug": "entire"}, [])

    def runner(args, **kwargs):
        if args[1] == "api" and args[4] == STATUS:
            return subprocess.CompletedProcess(args, 0, json.dumps({"statuses": []}), "")
        return base(args, **kwargs)

    with pytest.raises(PublishBlocked) as refused:
        ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})
    assert str(refused.value) == "OPSEC: merge refused: cannot establish check state (commit statuses: invalid shape)."
