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
        if args[2] == "view":
            meta = {"number": 1, "isDraft": False, "headRefOid": "a" * 40}
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
