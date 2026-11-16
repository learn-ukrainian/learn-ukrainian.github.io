"""Product CI quarantine wiring and the suite collection hook."""







from datetime import date, timedelta
from pathlib import Path

import yaml

from tests import conftest as root_conftest


def _entry(today: date) -> dict:
    return {
        "node_id": "tests/test_sample.py::test_flaky",
        "fix_issue": 123,
        "owner": "infra",
        "admitted_on": today,
        "expires_on": today + timedelta(days=20),
        "observed_run_ids": [101, 102],
        "renewals": 0,
        "equivalent_coverage": {"tests/test_sample.py::test_stable": "Checks the same result without the timing dependency."},
        "admission_approval": 999,
    }


def test_ci_checks_job_enforces_admission_with_read_only_evidence_permissions():
    workflow = yaml.safe_load(Path(".github/workflows/ci.yml").read_text())
    checks = workflow["jobs"]["checks"]
    step = next(step for step in checks["steps"] if step.get("name") == "Verify flake quarantine admissions")
    assert step["run"] == '.venv/bin/python -m lu_machinery.common.flake_quarantine --base-ref "$BASE_SHA"'
    assert "github.event.pull_request.base.sha" in step["env"]["BASE_SHA"]
    assert "github.event.merge_group.base_sha" in step["env"]["BASE_SHA"]
    assert step["env"]["GH_TOKEN"] == "${{ github.token }}"
    assert not step.get("continue-on-error") and not step.get("if")
    assert checks["permissions"] == {"contents": "read", "actions": "read", "issues": "read"}


def test_selection_listed_unlisted_schedule_and_expired(monkeypatch):
    today = date.today()
    entry = _entry(today)
    class Item:
        def __init__(self, nodeid):
            self.nodeid = nodeid
            self.markers = []

        def add_marker(self, marker):
            self.markers.append(marker)

        def get_closest_marker(self, name):
            return None

    entry["expires_on"] = today
    listed = Item(entry["node_id"])
    unlisted = Item("tests/test_sample.py::test_other")
    monkeypatch.setattr(root_conftest, "load_registry", lambda _path: [entry])
    monkeypatch.setattr(root_conftest, "_sparse_missing_trees", lambda: set())
    monkeypatch.setenv("GITHUB_EVENT_NAME", "merge_group")
    root_conftest.pytest_collection_modifyitems(None, [listed, unlisted])
    assert len(listed.markers) == 1 and listed.markers[0].kwargs["reruns"] == 1
    assert unlisted.markers == []
    monkeypatch.setenv("GITHUB_EVENT_NAME", "schedule")
    listed.markers.clear()
    root_conftest.pytest_collection_modifyitems(None, [listed])
    assert listed.markers == []
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("LU_FLAKE_DISABLE_RERUN", "1")
    root_conftest.pytest_collection_modifyitems(None, [listed])
    assert listed.markers == []
