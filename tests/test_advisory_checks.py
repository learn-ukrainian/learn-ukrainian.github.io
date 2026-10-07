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
    policy = advisory.load_advisory_checks()
    assert policy.reason is None
    assert policy.names == frozenset({SHADOW})
    assert Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml" == advisory.CI_WORKFLOW_PATH
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
