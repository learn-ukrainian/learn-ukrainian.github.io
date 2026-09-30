"""D2 admission and exact node selection checks."""

from datetime import date, timedelta

import pytest

from scripts.common.flake_quarantine import load_registry, rerun_node_ids
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
    }


def test_registry_lint_rejects_missing_bad_expiry_second_renewal_and_duplicate_runs(tmp_path):
    today = date(2026, 9, 28)
    entry = _entry(today)
    path = tmp_path / "registry.yaml"
    path.write_text("entries:\n  - node_id: tests/test_sample.py::test_flaky\n", encoding="utf-8")
    with pytest.raises(ValueError, match="required fields"):
        load_registry(path)
    import yaml

    for change, message in (
        ({"expires_on": today + timedelta(days=31)}, "30 days"),
        ({"renewals": 2}, "one renewal"),
        ({"observed_run_ids": [101, 101]}, "distinct"),
        ({"observed_run_ids": [101]}, "at least two"),
    ):
        bad = entry | change
        path.write_text(yaml.safe_dump({"entries": [bad]}), encoding="utf-8")
        with pytest.raises(ValueError, match=message):
            load_registry(path)
    path.write_text(yaml.safe_dump({"entries": [entry]}), encoding="utf-8")
    assert load_registry(path) == [entry]


def test_selection_listed_unlisted_schedule_and_expired(monkeypatch):
    today = date.today()
    entry = _entry(today)
    assert rerun_node_ids([entry], today=today, event_name="merge_group") == {entry["node_id"]}
    assert rerun_node_ids([entry], today=today, event_name="schedule") == set()
    entry["expires_on"] = today - timedelta(days=7)
    assert rerun_node_ids([entry], today=today, event_name="pull_request") == {entry["node_id"]}
    entry["expires_on"] = today - timedelta(days=8)
    assert rerun_node_ids([entry], today=today, event_name="pull_request") == set()

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
    monkeypatch.setattr(root_conftest, "load_registry", lambda: [entry])
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
