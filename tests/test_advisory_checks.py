"""Workflow-derived advisory classification and all three readiness consumers."""

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.ci import advisory_checks as advisory
from scripts.opsec.prepublish import PublishBlocked
from scripts.orchestration import handoff_ready, integration_sweep
from scripts.publish.merge_guard import ensure_merge_ready, parse_checks

SHADOW = "Component shadow (advisory)"
HEAD = "a" * 40


def workflow_jobs():
    return {
        "build": {"name": "Build", "steps": []},
        "shadow": {"name": SHADOW, "continue-on-error": True, "steps": []},
        "ci-gate": {
            "name": "CI Gate", "if": "always()", "needs": ["build", "shadow"],
            "steps": [{"env": {"BUILD": "${{ needs.build.result }}"}, "run": "test $BUILD = success"}],
        },
    }


@pytest.fixture
def ci_file(tmp_path, monkeypatch):
    path = tmp_path / "ci.yml"
    monkeypatch.setattr(advisory, "CI_WORKFLOW_PATH", path)

    def write(jobs=None):
        path.write_text(yaml.safe_dump({"name": "CI", "jobs": jobs or workflow_jobs()}))
        return path

    write()
    return write


def test_current_workflow_exact_set_and_repository_root(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    real = advisory.load_advisory_checks()
    assert real.reason is None
    assert real.names == frozenset()
    assert Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml" == advisory.CI_WORKFLOW_PATH
    policy = advisory.load_advisory_checks(Path(__file__).resolve().parent / "fixtures/ci_advisory_workflow.yml")
    assert policy.names == frozenset({SHADOW})
    assert advisory.is_advisory(SHADOW, workflow="CI", policy=policy)
    for name in ["advisory", "ADVISORY smoke", "Lint (advisory)", SHADOW.lower(), SHADOW + " "]:
        assert not advisory.is_advisory(name, workflow="CI", policy=policy)
    assert not advisory.is_advisory(SHADOW, workflow="Nightly", policy=policy)


@pytest.mark.parametrize("workflow", [None, "", "Nightly"])
def test_missing_or_other_workflow_is_not_advisory(ci_file, workflow):
    policy = advisory.load_advisory_checks()
    assert SHADOW in policy.names
    assert not advisory.is_advisory(SHADOW, workflow=workflow, policy=policy)


@pytest.mark.parametrize("required_by", ["gate-result", "dependency", "implicit-gate", "no-result-references"])
def test_required_jobs_never_advisory_even_with_continue_on_error(ci_file, required_by):
    jobs = workflow_jobs()
    gate = jobs["ci-gate"]
    if required_by == "gate-result":
        gate["steps"].append({"run": "echo '${{ needs.shadow.result }}'"})
    elif required_by == "dependency":
        jobs["build"]["needs"] = "shadow"
    elif required_by == "implicit-gate":
        gate.pop("if")
    else:
        gate["steps"] = []
    ci_file(jobs)
    assert advisory.load_advisory_checks().names == frozenset()


@pytest.mark.parametrize("value", [False, "true", "${{ matrix.experimental }}", None])
def test_only_literal_job_level_true_qualifies(ci_file, value):
    jobs = workflow_jobs()
    jobs["shadow"]["continue-on-error"] = value
    jobs["shadow"]["steps"] = [{"continue-on-error": True, "run": "false"}]
    ci_file(jobs)
    assert not advisory.is_advisory(SHADOW, workflow="CI")


def test_static_matrix_include_exclude_and_name_expansion(ci_file):
    jobs = workflow_jobs()
    jobs["shadow"].update({
        "name": "Shadow (${{ matrix.os }}, ${{ matrix.version }}, ${{ matrix.label }})",
        "strategy": {"matrix": {
            "os": ["linux", "windows"], "version": [1, 2],
            "exclude": [{"os": "windows", "version": 1}],
            "include": [
                {"label": "default"}, {"os": "linux", "label": "linux"},
                {"os": "mac", "version": 3, "label": "extra"},
            ],
        }},
    })
    ci_file(jobs)
    policy = advisory.load_advisory_checks()
    assert policy.reason is None
    assert policy.names == frozenset({
        "Shadow (linux, 1, linux)", "Shadow (linux, 2, linux)",
        "Shadow (windows, 2, default)", "Shadow (mac, 3, extra)",
    })
    assert not advisory.is_advisory("Shadow (windows, 1, default)", workflow="CI")


def test_include_only_nested_matrix_values(ci_file):
    jobs = workflow_jobs()
    jobs["shadow"].update({
        "name": "Shadow ${{ matrix.node.version }} ${{ matrix.experimental }}",
        "strategy": {"matrix": {"include": [
            {"node": {"version": 22}, "experimental": True},
            {"node": {"version": 24}, "experimental": False},
        ]}},
    })
    ci_file(jobs)
    assert advisory.load_advisory_checks().names == frozenset({"Shadow 22 true", "Shadow 24 false"})


def test_matrix_default_job_name(ci_file):
    jobs = workflow_jobs()
    jobs["shadow"].pop("name")
    jobs["shadow"]["strategy"] = {"matrix": {"os": ["linux", "windows"], "version": [1, 2]}}
    ci_file(jobs)
    assert advisory.load_advisory_checks().names == frozenset({
        "shadow (linux, 1)", "shadow (linux, 2)", "shadow (windows, 1)", "shadow (windows, 2)",
    })


def test_duplicate_blocking_name_cannot_become_advisory(ci_file):
    jobs = workflow_jobs()
    jobs["build"]["name"] = SHADOW
    ci_file(jobs)
    assert not advisory.is_advisory(SHADOW, workflow="CI")


@pytest.mark.parametrize("change", [
    lambda jobs: jobs.pop("ci-gate"),
    lambda jobs: jobs["ci-gate"].update({"needs": 4}),
    lambda jobs: jobs["ci-gate"]["steps"].append({"run": "echo '${{ toJSON(needs) }}'"}),
    lambda jobs: jobs["build"].update({"needs": "missing"}),
    lambda jobs: jobs["shadow"].update({"name": "${{ github.ref }}"}),
    lambda jobs: jobs["shadow"].update({"strategy": {"matrix": "${{ fromJSON(needs.build.outputs.matrix) }}"}}),
    lambda jobs: jobs["shadow"].update({"strategy": {"matrix": {"os": ["${{ github.ref }}"]}}}),
    lambda jobs: jobs["shadow"].update({"strategy": {"matrix": {"include": "invalid"}}}),
])
def test_unsupported_workflow_fails_closed_with_reason(ci_file, change, caplog):
    jobs = workflow_jobs()
    change(jobs)
    ci_file(jobs)
    policy = advisory.load_advisory_checks()
    assert policy.names == frozenset()
    assert policy.reason and policy.reason in caplog.text


@pytest.mark.parametrize("consumer", ["handoff", "sweep", "merge", "merge-rollup"])
@pytest.mark.parametrize("case,ready", [
    ("advisory", True), ("blocking", False), ("blocking-advisory-name", False),
    ("unknown", False), ("other-workflow", False), ("missing-workflow", False),
    ("missing", False), ("invalid", False),
])
def test_all_consumers_fail_closed(ci_file, consumer, case, ready, monkeypatch, caplog):
    jobs = workflow_jobs()
    name, workflow = SHADOW, "CI"
    if case == "blocking":
        name = "Build"
    elif case == "blocking-advisory-name":
        name = "Security advisory validation"
        jobs["build"]["name"] = name
    elif case == "unknown":
        name = "Another workflow check"
    elif case == "other-workflow":
        workflow = "Nightly"
    path = ci_file(jobs)
    if case == "missing":
        path.unlink()
    elif case == "invalid":
        path.write_text("jobs: [")
    rows = [
        {"name": "CI Gate", "bucket": "pass", "status": "COMPLETED", "conclusion": "SUCCESS", "workflowName": "CI"},
        {"name": name, "bucket": "fail", "status": "COMPLETED", "conclusion": "FAILURE", "workflowName": workflow},
    ]
    if case == "missing-workflow":
        rows[1].pop("workflowName")
    pr = {"number": 1, "headRefOid": HEAD, "isDraft": False, "statusCheckRollup": rows,
          "state": "OPEN", "mergeStateStatus": "CLEAN"}
    if consumer == "handoff":
        monkeypatch.setattr(handoff_ready, "_gh_json", lambda *args: (0, pr))
        assert (handoff_ready.check_pr_checks(1)[0] == handoff_ready.OK) is ready
    elif consumer == "sweep":
        report = integration_sweep.classify_pr(pr, integration_sweep.Verdict("APPROVED"), queued=False, observed_at="fixture")
        assert (report.state == "ready") is ready
    else:
        def runner(args, **kwargs):
            if args[2] == "view":
                return subprocess.CompletedProcess(args, 0, json.dumps(pr), "")
            if consumer == "merge-rollup":
                return subprocess.CompletedProcess(args, 1, "", "unknown flag: --json\n"
                    "Usage: gh pr checks [<number> | <url> | <branch>] [flags]\nFlags:\n--fail-fast\n")
            checks = [{**row, "workflow": row.get("workflowName")} for row in rows]
            for check in checks:
                check.pop("workflowName", None)
            return subprocess.CompletedProcess(args, 1, json.dumps(checks), "")

        if ready:
            assert ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={}) == HEAD
        else:
            with pytest.raises(PublishBlocked):
                ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})
    if case in {"missing", "invalid"}:
        assert "all checks treated as blocking" in caplog.text


def test_workflow_reload_does_not_keep_a_stale_exemption(ci_file):
    checks = [{"name": SHADOW, "bucket": "fail", "workflow": "CI"}]
    assert parse_checks(checks) == ([], [])
    jobs = workflow_jobs()
    jobs["shadow"].pop("continue-on-error")
    ci_file(jobs)
    assert parse_checks(checks) == ([SHADOW], [])


# --- OO-48: the Entire Gates external check (#11184) ---------------------------------------

ENTIRE = advisory.OO48_ENTIRE_GATES
REPO = "owner/repo"
HOOK_PATH = Path(__file__).resolve().parents[1] / "agents_extensions/shared/hooks/guard-pr-merge.py"
RUNS_ENDPOINT = f"repos/{REPO}/commits/{HEAD}/check-runs?check_name=Entire%20Gates&filter=all&per_page=100"
STATUS_ENDPOINT = f"repos/{REPO}/commits/{HEAD}/status?per_page=100"
OLD_CLIENT_STDERR = (
    "unknown flag: --json\n\nUsage:  gh pr checks [<number> | <url> | <branch>] [flags]\n\n"
    "Flags:\n      --fail-fast         Exit watch mode on first check failure\n"
)


def respond(scenario, args):
    """A fake GitHub for both readiness paths: (returncode, stdout, stderr) for one gh argv."""
    import json

    head = scenario["head"]
    if args[:2] == ["pr", "view"] and "statusCheckRollup" in args:
        rollup = [
            {"__typename": "CheckRun", "name": row["name"], "status": row["status"],
             "conclusion": row["conclusion"], "workflowName": row["workflow"]}
            if isinstance(row, dict) else row
            for row in scenario["checks"]
        ]
        return 0, json.dumps({"statusCheckRollup": rollup}), ""
    if args[:2] == ["pr", "view"]:
        meta = {"number": 5, "isDraft": False, "baseRefName": "main", "body": "", "headRefOid": head,
                "url": scenario.get("url", "https://github.com/owner/repo/pull/5")}
        return 0, json.dumps(meta), ""
    if args[:2] == ["pr", "checks"]:
        if scenario.get("old_client"):
            return 1, "", scenario["old_client_stderr"]
        buckets = {row.get("bucket") for row in scenario["checks"] if isinstance(row, dict)}
        code = 1 if buckets & {"fail", "cancel"} else 8 if "pending" in buckets else 0
        return code, json.dumps(scenario["checks"]), ""
    if args[:3] == ["api", "--method", "GET"] and len(args) == 4 and not scenario.get("api_error"):
        documents = {
            f"repos/owner/repo/commits/{head}/status?per_page=100": scenario.get(
                "status_doc", {"total_count": len(scenario["statuses"]), "statuses": scenario["statuses"]}
            ),
            f"repos/owner/repo/commits/{head}/check-runs?check_name=Entire%20Gates&filter=all&per_page=100":
                scenario.get("runs_doc", {"total_count": len(scenario["runs"]), "check_runs": scenario["runs"]}),
        }
        if args[3] in documents:
            return 0, json.dumps(documents[args[3]]), ""
    return 1, "", "HTTP 404: Not Found"


def check(name, bucket, status, conclusion="", workflow="", state=None):
    return {"name": name, "bucket": bucket, "state": state or (conclusion or status),
            "status": status, "conclusion": conclusion, "workflow": workflow}


def entire_run(status="in_progress", conclusion=None, **changes):
    run = {"id": 118738463484, "name": ENTIRE.name, "head_sha": HEAD, "status": status, "conclusion": conclusion,
           "app": {"id": ENTIRE.app_id, "slug": ENTIRE.app_slug}}
    return {**run, **changes}


GREEN_GATE = check("CI Gate", "pass", "COMPLETED", "SUCCESS", "CI")
OBSERVED = check(ENTIRE.name, "pending", "IN_PROGRESS")  # PR #11171/#11172 at 17:31Z
ACTIONS_APP = {"id": 15368, "slug": "github-actions"}

# name -> (check rows, exact-head check runs, commit statuses, extra scenario fields, ready)
SCENARIOS = {
    "observed-pending-external-informational": ([GREEN_GATE, OBSERVED], [entire_run()], [], {}, True),
    "untracked-branch-neutral": (
        [GREEN_GATE, check(ENTIRE.name, "pass", "COMPLETED", "NEUTRAL")],
        [entire_run("completed", "neutral")], [], {}, True),
    "oo48-failure-advisory": (
        [GREEN_GATE, check(ENTIRE.name, "fail", "COMPLETED", "FAILURE")],
        [entire_run("completed", "failure")], [], {}, True),
    "oo48-cancelled-advisory": (
        [GREEN_GATE, check(ENTIRE.name, "cancel", "COMPLETED", "CANCELLED")],
        [entire_run("completed", "cancelled")], [], {}, True),
    "oo48-rerun-history-same-app": (
        [GREEN_GATE, OBSERVED], [entire_run(), entire_run("completed", "neutral", id=1)], [], {}, True),
    "normal-green-without-external": ([GREEN_GATE], [], [], {"api_error": True}, True),
    "wrong-app-id": ([GREEN_GATE, OBSERVED], [entire_run(app={"id": 2626940, "slug": "entire"})], [], {}, False),
    "app-id-as-string": ([GREEN_GATE, OBSERVED], [entire_run(app={"id": "2626939", "slug": "entire"})], [], {}, False),
    "app-id-as-bool": ([GREEN_GATE, OBSERVED], [entire_run(app={"id": True, "slug": "entire"})], [], {}, False),
    "wrong-app-slug": ([GREEN_GATE, OBSERVED], [entire_run(app={"id": ENTIRE.app_id, "slug": "other"})], [], {}, False),
    "missing-app-identity": ([GREEN_GATE, OBSERVED], [entire_run(app=None)], [], {}, False),
    "malformed-app-identity": ([GREEN_GATE, OBSERVED], [entire_run(app=[ENTIRE.app_id])], [], {}, False),
    "other-head": ([GREEN_GATE, OBSERVED], [entire_run(head_sha="b" * 40)], [], {}, False),
    "actions-job-name-collision": (
        [GREEN_GATE, OBSERVED, check(ENTIRE.name, "pass", "COMPLETED", "SUCCESS", "CI")],
        [entire_run(), entire_run("completed", "success", id=2, app=ACTIONS_APP)], [], {}, False),
    "commit-status-name-collision": (
        [GREEN_GATE, OBSERVED], [entire_run()], [{"context": ENTIRE.name, "state": "success"}], {}, False),
    "commit-status-alone": (
        [GREEN_GATE, check(ENTIRE.name, "pass", "COMPLETED", "SUCCESS")], [],
        [{"context": ENTIRE.name, "state": "success"}], {}, False),
    "no-provider-runs": ([GREEN_GATE, OBSERVED], [], [], {}, False),
    "incomplete-runs-page": (
        [GREEN_GATE, OBSERVED], [], [], {"runs_doc": {"total_count": 2, "check_runs": [entire_run()]}}, False),
    "malformed-runs-page": ([GREEN_GATE, OBSERVED], [], [], {"runs_doc": {"check_runs": "x"}}, False),
    "malformed-status-page": ([GREEN_GATE, OBSERVED], [entire_run()], [], {"status_doc": []}, False),
    "provenance-api-error": ([GREEN_GATE, OBSERVED], [entire_run()], [], {"api_error": True}, False),
    "required-ci-pending": (
        [check("CI Gate", "pending", "IN_PROGRESS", workflow="CI"), OBSERVED], [entire_run()], [], {}, False),
    "required-ci-red": (
        [check("CI Gate", "fail", "COMPLETED", "FAILURE", "CI"), OBSERVED], [entire_run()], [], {}, False),
    "required-ci-cancelled": (
        [check("CI Gate", "cancel", "COMPLETED", "CANCELLED", "CI"), OBSERVED], [entire_run()], [], {}, False),
    "unknown-external-pending": (
        [GREEN_GATE, OBSERVED, check("Other App Gate", "pending", "IN_PROGRESS")], [entire_run()], [], {}, False),
    "other-external-failure": (
        [GREEN_GATE, OBSERVED, check("Other App Gate", "fail", "COMPLETED", "FAILURE")], [entire_run()], [], {}, False),
    "near-miss-name-trailing-space": ([GREEN_GATE, check("Entire Gates ", "pending", "IN_PROGRESS")],
                                      [entire_run()], [], {}, False),
    "near-miss-name-case": ([GREEN_GATE, check("entire gates", "pending", "IN_PROGRESS")],
                            [entire_run()], [], {}, False),
    "malformed-check-row": ([GREEN_GATE, OBSERVED, "not-a-row"], [entire_run()], [], {}, False),
    "unknown-check-state": ([GREEN_GATE, OBSERVED, check("CI Extra", "mystery", "MYSTERY", workflow="CI")],
                            [entire_run()], [], {}, False),
}


def scenario(name, *, old_client=False):
    checks, runs, statuses, extra, ready = SCENARIOS[name]
    data = {"head": HEAD, "checks": checks, "runs": runs, "statuses": statuses,
            "old_client": old_client, "old_client_stderr": OLD_CLIENT_STDERR, **extra}
    return data, ready


def publisher_ready(data):
    calls = []

    def runner(args, **kwargs):
        calls.append(args[1:])
        code, stdout, stderr = respond(data, args[1:])
        return subprocess.CompletedProcess(args, code, stdout, stderr)

    try:
        assert ensure_merge_ready(REPO, 5, runner=runner, cwd=".", environment={}) == HEAD
        return True, calls
    except PublishBlocked:
        return False, calls


def hook_ready(data, tmp_path):
    import inspect
    import os
    import sys

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "gh"
    fake.write_text(
        f"#!{sys.executable}\n" + inspect.getsource(respond) + (
            "\nimport json, os, sys\n"
            "data = json.load(open(os.environ['FAKE_GH_SCENARIO']))\n"
            "with open(os.environ['FAKE_GH_LOG'], 'a') as log:\n"
            "    log.write(json.dumps(sys.argv[1:]) + '\\n')\n"
            "code, out, err = respond(data, sys.argv[1:])\n"
            "sys.stdout.write(out); sys.stderr.write(err); sys.exit(code)\n"
        )
    )
    fake.chmod(0o755)
    (tmp_path / "scenario.json").write_text(json.dumps(data))
    log = tmp_path / "gh.log"
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
           "FAKE_GH_SCENARIO": str(tmp_path / "scenario.json"), "FAKE_GH_LOG": str(log)}
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps({"tool_input": {"command": "gh pr merge 5 --squash"}}),
        capture_output=True, text=True, env=env, cwd=tmp_path, timeout=60,
    )
    assert result.returncode in {0, 2}, result.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    return result.returncode == 0, calls, result.stderr


@pytest.mark.parametrize("old_client", [False, True], ids=["checks-json", "old-client-rollup"])
@pytest.mark.parametrize("name", list(SCENARIOS))
def test_oo48_publisher_and_real_hook_agree(name, old_client, tmp_path):
    data, ready = scenario(name, old_client=old_client)
    published, publisher_calls = publisher_ready(data)
    hooked, hook_calls, stderr = hook_ready(data, tmp_path)
    assert published is ready
    assert hooked is ready, stderr
    for calls in (publisher_calls, hook_calls):
        api = [call[3] for call in calls if call[:1] == ["api"]]
        # Provenance is read only for an exact OO-48 name, and only at the exact head.
        if any(isinstance(row, dict) and ENTIRE.name in (row.get("name"),) for row in data["checks"]):
            assert set(api) <= {STATUS_ENDPOINT, RUNS_ENDPOINT}
        else:
            assert api == []


def test_oo48_is_one_exact_operator_entry():
    assert advisory.EXTERNAL_ADVISORY_CHECKS == (ENTIRE,)
    assert (ENTIRE.name, ENTIRE.app_id, ENTIRE.app_slug, ENTIRE.decision) == ("Entire Gates", 2626939, "entire", "OO-48")
    assert advisory.external_advisory_check("Entire Gates") is ENTIRE
    for name in ["entire gates", "Entire Gates ", "Entire", "Gates", "CI Gate", None, 7, ["Entire Gates"]]:
        assert advisory.external_advisory_check(name) is None
    # The ci.yml workflow policy is untouched: the name alone is never advisory.
    assert not advisory.is_advisory(ENTIRE.name, workflow="")
    assert not advisory.is_advisory(ENTIRE.name, workflow="CI")


@pytest.mark.parametrize("run,proven", [
    (entire_run(), True),
    (entire_run(name="Entire Gates "), False),
    (entire_run(head_sha=HEAD.upper()), False),
    (entire_run(app={"id": 2626939.0, "slug": "entire"}), False),
    (entire_run(app={"slug": "entire"}), False),
    (entire_run(app={"id": ENTIRE.app_id}), False),
    ({"name": ENTIRE.name, "head_sha": HEAD}, False),
    ("not-a-run", False),
])
def test_external_advisory_run_requires_exact_identity(run, proven):
    assert advisory.is_external_advisory_run(ENTIRE, run, HEAD) is proven


def test_prove_external_advisory_reads_only_exact_head_endpoints():
    from scripts.publish.merge_guard import prove_external_advisory

    seen = []
    documents = {STATUS_ENDPOINT: {"total_count": 0, "statuses": []},
                 RUNS_ENDPOINT: {"total_count": 1, "check_runs": [entire_run()]}}

    def get_json(endpoint):
        seen.append(endpoint)
        return documents.get(endpoint)

    names = frozenset({ENTIRE.name})
    assert prove_external_advisory(REPO, HEAD.upper(), names, get_json) == names
    assert seen == [STATUS_ENDPOINT, RUNS_ENDPOINT]
    assert prove_external_advisory(REPO, HEAD, frozenset(), pytest.fail) == frozenset()
    for repo, head in [(None, HEAD), ("owner/repo/x", HEAD), (REPO, "a" * 39), (REPO, None), (REPO, "g" * 40)]:
        assert prove_external_advisory(repo, head, names, pytest.fail) is None
    assert prove_external_advisory(REPO, HEAD, frozenset({"Unlisted"}), get_json) is None


def test_external_advisory_names_are_exact():
    from scripts.publish.merge_guard import external_advisory_names

    rows = [{"name": "Entire Gates"}, {"context": "Entire Gates"}, {"name": "entire gates"},
            {"name": ["Entire Gates"]}, "Entire Gates", {"name": "CI Gate"}]
    assert external_advisory_names(rows) == frozenset({ENTIRE.name})
    assert external_advisory_names({"name": "Entire Gates"}) == frozenset()


def test_unproven_name_is_never_skipped_by_parsers():
    from scripts.publish.merge_guard import _parse_status_rollup_rows

    rows = [check(ENTIRE.name, "pending", "IN_PROGRESS")]
    assert parse_checks(rows) == ([], [ENTIRE.name])
    assert parse_checks(rows, advisory=frozenset({ENTIRE.name})) == ([], [])
    rollup = [{"name": ENTIRE.name, "status": "IN_PROGRESS", "conclusion": ""}]
    assert _parse_status_rollup_rows(rollup) == ([], [ENTIRE.name])
    assert _parse_status_rollup_rows(rollup, advisory=frozenset({ENTIRE.name})) == ([], [])
    # A same-named commit status is a context, never a proven check-run name.
    status = [{"context": ENTIRE.name, "state": "PENDING"}]
    assert _parse_status_rollup_rows(status, advisory=frozenset({ENTIRE.name})) == ([], [ENTIRE.name])
