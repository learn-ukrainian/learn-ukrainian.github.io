"""A failed advisory shadow cannot veto an otherwise ready merge (#9900)."""

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.ci.advisory_checks import is_advisory
from scripts.opsec.prepublish import PublishBlocked
from scripts.orchestration import integration_sweep as sweep
from scripts.publish.merge_guard import ensure_merge_ready

HEAD = "a" * 40


@pytest.fixture
def shadow_name():
    workflow_path = Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"
    workflow = yaml.safe_load(workflow_path.read_text())
    name = workflow["jobs"]["component-shadow"]["name"]
    assert name == "Component shadow (advisory)"
    assert is_advisory(name)
    return name


@pytest.mark.parametrize("required_bucket", ["pass", "fail", "pending"])
def test_failed_shadow_does_not_change_merge_guard_readiness(shadow_name, required_bucket):
    def runner(args, **kwargs):
        if args[2] == "view":
            return subprocess.CompletedProcess(args, 0, json.dumps({
                "number": 1, "isDraft": False, "headRefOid": HEAD}), "")
        assert args[2] == "checks"
        checks = [{"name": "CI Gate", "bucket": required_bucket},
                  {"name": shadow_name, "bucket": "fail"}]
        return subprocess.CompletedProcess(args, 1, json.dumps(checks), "")

    if required_bucket == "pass":
        assert ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={}) == HEAD
    else:
        with pytest.raises(PublishBlocked):
            ensure_merge_ready("unit/public", 1, runner=runner, cwd=".", environment={})


@pytest.mark.parametrize("required_conclusion,expected", [
    ("SUCCESS", []), ("FAILURE", ["CI red CI Gate"]),
])
@pytest.mark.parametrize("shadow_conclusion", ["FAILURE", "CANCELLED", "TIMED_OUT"])
def test_failed_shadow_is_not_reported_red_by_integration_sweep(
    shadow_name, required_conclusion, expected, shadow_conclusion,
):
    pr = {"number": 1, "headRefOid": HEAD, "statusCheckRollup": [
        {"name": "CI Gate", "status": "COMPLETED", "conclusion": required_conclusion},
        {"name": shadow_name, "status": "COMPLETED", "conclusion": shadow_conclusion},
    ]}
    report = sweep.classify_pr(pr, sweep.Verdict("APPROVED"), queued=False, observed_at="fixture")
    assert report.blockers == tuple(expected)
