"""D2 admission and exact node selection checks."""

import copy
import json
import subprocess
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.common import flake_quarantine
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
        "equivalent_coverage": {"tests/test_sample.py::test_stable": "Checks the same result without the timing dependency."},
        "admission_approval": 999,
    }


def test_registry_lint_rejects_missing_bad_expiry_second_renewal_and_duplicate_runs(tmp_path):
    today = date(2026, 9, 28)
    entry = _entry(today)
    path = tmp_path / "registry.yaml"
    path.write_text("entries:\n  - node_id: tests/test_sample.py::test_flaky\n", encoding="utf-8")
    with pytest.raises(ValueError, match="required fields"):
        load_registry(path)
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


@pytest.mark.parametrize("change,message", [
    ({"node_id": "tests/test_sample.py::test_flaky*"}, "invalid pytest node_id"),
    ({"node_id": "tests/../test_sample.py::test_flaky"}, "invalid pytest node_id"),
    ({"node_id": "tests/test_sample.py::test_flaky\n"}, "invalid pytest node_id"),
    ({"equivalent_coverage": {}}, "equivalent_coverage"),
    ({"equivalent_coverage": {"tests/test_sample.py::test_flaky": "same test"}}, "equivalent_coverage"),
    ({"equivalent_coverage": {"tests/test_sample.py::test_stable": " "}}, "equivalent_coverage"),
    ({"equivalent_coverage": {"tests/test_sample.py": "module"}}, "equivalent_coverage"),
    ({"admission_approval": True}, "admission_approval"),
    ({"owner": " "}, "owner"),
    ({"fix_issue": True}, "positive issue"),
    ({"observed_run_ids": [101, False]}, "positive observed run"),
    ({"renewals": 1, "renewed_on": date(2026, 10, 29)}, "first 30 days"),
    ({"renewals": 1, "renewed_on": date(2026, 9, 27)}, "first 30 days"),
    ({"expires_on": date(2026, 9, 27)}, "30 days"),
])
def test_registry_rejects_invalid_admission_fields(tmp_path, change, message):
    path = tmp_path / "registry.yaml"
    path.write_text(yaml.safe_dump({"entries": [_entry(date(2026, 9, 28)) | change]}))
    with pytest.raises(ValueError, match=message):
        load_registry(path)


def test_single_renewal_and_exact_parameterized_class_node(tmp_path):
    entry = _entry(date(2026, 9, 28)) | {
        "node_id": "tests/test_sample.py::TestSample::test_flaky[a*b]",
        "renewals": 1,
        "renewed_on": date(2026, 10, 28),
        "expires_on": date(2026, 11, 27),
    }
    path = tmp_path / "registry.yaml"
    path.write_text(yaml.safe_dump({"entries": [entry]}))
    assert load_registry(path) == [entry]
    assert rerun_node_ids([entry], today=date(2026, 12, 4), event_name="pull_request") == {entry["node_id"]}
    assert rerun_node_ids([entry], today=date(2026, 12, 5), event_name="pull_request") == set()
    entry["expires_on"] += timedelta(days=1)
    path.write_text(yaml.safe_dump({"entries": [entry]}))
    with pytest.raises(ValueError, match="30 days"):
        load_registry(path)


@pytest.mark.parametrize("renewals", [0, 1])
def test_reruns_start_on_admission_or_renewal_date(tmp_path, renewals):
    start = date(2027, 8, 1)
    entry = _entry(start)
    if renewals:
        entry.update(admitted_on=start - timedelta(days=30), renewals=1, renewed_on=start)
    path = tmp_path / "registry.yaml"
    path.write_text(yaml.safe_dump({"entries": [entry]}))
    entries = load_registry(path)
    assert rerun_node_ids(entries, today=date(2026, 10, 20), event_name="pull_request") == set()
    assert rerun_node_ids(entries, today=start - timedelta(days=1), event_name="pull_request") == set()
    assert rerun_node_ids(entries, today=start, event_name="pull_request") == {entry["node_id"]}
    expiry = entry["expires_on"]
    assert rerun_node_ids(entries, today=expiry, event_name="pull_request") == {entry["node_id"]}
    assert rerun_node_ids(entries, today=expiry + timedelta(days=7), event_name="pull_request") == {entry["node_id"]}
    assert rerun_node_ids(entries, today=expiry + timedelta(days=8), event_name="pull_request") == set()


@pytest.fixture
def admission(monkeypatch):
    entry = _entry(date(2026, 9, 28))
    prefix = "repos/example/project"
    issue_url = f"https://api.github.com/{prefix}/issues/123"
    sha = "a" * 40
    responses = {
        f"{prefix}/issues/123": {"state": "open", "url": issue_url},
        f"{prefix}/issues/comments/999": {
            "issue_url": issue_url, "author_association": "OWNER",
            "body": f"<!-- flake-quarantine-admission:{flake_quarantine.admission_digest(entry)}:APPROVE -->",
        },
        f"{prefix}/compare/{sha}...main": {"merge_base_commit": {"sha": sha}},
    }
    for run_id in (101, 102):
        responses[f"{prefix}/actions/runs/{run_id}"] = {
            "head_branch": "main", "head_sha": sha, "head_repository": {"full_name": "example/project"},
            "event": "schedule", "path": ".github/workflows/ci.yml", "status": "completed",
        }
    xml = (
        '<testsuite><testcase classname="tests.test_sample" name="test_flaky">'
        '<failure message="assert 0"/></testcase>'
        '<testcase classname="tests.test_sample" name="test_stable"/></testsuite>'
    )
    artifacts = {101: xml, 102: xml}
    duplicates = {}
    calls = []

    def gh(*args):
        calls.append(args)
        if args[0] == "api":
            return json.dumps(responses[args[1]])
        if args[:2] == ("repo", "view"):
            return '{"nameWithOwner":"example/project"}'
        assert args[:2] == ("run", "download")
        assert args[3:7] == ("--repo", "example/project", "--pattern", "pytest-junit-shard-*")
        Path(args[-1], "junit.xml").write_text(artifacts[int(args[2])])
        if int(args[2]) in duplicates:
            Path(args[-1], "junit-duplicate.xml").write_text(duplicates[int(args[2])])
        return ""

    monkeypatch.setattr(flake_quarantine, "_gh", gh)
    return SimpleNamespace(entry=entry, responses=responses, artifacts=artifacts, duplicates=duplicates,
                           calls=calls, prefix=prefix)


def test_admission_verifies_two_main_failures_coverage_issue_and_bound_approval(admission):
    assert flake_quarantine.check_admissions([admission.entry], [], repository="example/project") == 1
    assert [call[2] for call in admission.calls if call[:2] == ("run", "download")] == ["101", "102"]


@pytest.mark.parametrize("renewals", [0, 1])
def test_admission_refuses_future_start_before_fetching_evidence(admission, monkeypatch, renewals):
    class Today(date):
        @classmethod
        def today(cls):
            return cls(2026, 10, 20)

    monkeypatch.setattr(flake_quarantine, "date", Today)
    start = date(2026, 10, 21)
    admission.entry.update(admitted_on=start, expires_on=start + timedelta(days=20))
    if renewals:
        admission.entry.update(admitted_on=start - timedelta(days=30), renewals=1, renewed_on=start)
    admission.responses[f"{admission.prefix}/issues/comments/999"]["body"] = (
        f"<!-- flake-quarantine-admission:{flake_quarantine.admission_digest(admission.entry)}:APPROVE -->"
    )
    with pytest.raises(ValueError, match=r"start date.*future"):
        flake_quarantine.check_admissions([admission.entry], [], repository="example/project")
    assert admission.calls == []
    monkeypatch.setattr(Today, "today", classmethod(lambda cls: cls(2026, 10, 21)))
    assert flake_quarantine.check_admissions([admission.entry], [], repository="example/project") == 1


@pytest.mark.parametrize("leased", [True, False])
def test_admission_downloads_use_managed_scratch_and_are_removed(admission, monkeypatch, tmp_path, leased):
    from scripts.common import scratch

    fallback_calls = []

    def fallback():
        fallback_calls.append(True)
        return tmp_path

    monkeypatch.setattr(scratch, "ensure_scratch_root", fallback)
    if leased:
        monkeypatch.setenv("TMPDIR", str(tmp_path))
    else:
        monkeypatch.delenv("TMPDIR", raising=False)
    assert flake_quarantine.check_admissions([admission.entry], [], repository="example/project") == 1
    paths = [Path(call[-1]) for call in admission.calls if call[:2] == ("run", "download")]
    assert len(paths) == 2 and all(path.parent.parent == tmp_path for path in paths)
    assert fallback_calls == ([] if leased else [True])
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("resource,change,message", [
    ("issues/123", {"state": "closed"}, "open repair issue"),
    ("issues/123", {"pull_request": {}}, "not a PR"),
    ("issues/comments/999", {"issue_url": "another issue"}, "designated admission approval"),
    ("issues/comments/999", {"author_association": "NONE"}, "designated admission approval"),
    ("issues/comments/999", {"body": "APPROVE without the digest"}, "designated admission approval"),
    ("actions/runs/102", {"head_branch": "feature"}, "unmodified main"),
    ("actions/runs/102", {"head_repository": {"full_name": "someone/fork"}}, "unmodified main"),
    ("actions/runs/102", {"event": "merge_group"}, "unmodified main"),
    ("actions/runs/102", {"event": "pull_request_target"}, "unmodified main"),
    ("actions/runs/102", {"path": ".github/workflows/other.yml"}, "unmodified main"),
    ("actions/runs/102", {"status": "in_progress"}, "unmodified main"),
    ("actions/runs/102", {"head_sha": "not-a-sha"}, "unmodified main"),
    (f"compare/{'a' * 40}...main", {"merge_base_commit": {"sha": "b" * 40}}, "ancestor of main"),
])
def test_admission_refuses_nonbaseline_or_unapproved_evidence(admission, resource, change, message):
    admission.responses[f"{admission.prefix}/{resource}"].update(change)
    with pytest.raises(ValueError, match=message):
        flake_quarantine.check_admissions([admission.entry], [], repository="example/project")


@pytest.mark.parametrize("replacement,message", [
    (("test_flaky", "test_flaky[other]"), "exact-node baseline failure"),
    (('<failure message="assert 0"/>', ""), "exact-node baseline failure"),
    (('<failure message="assert 0"/>', '<skipped message="disabled"/>'), "exact-node baseline failure"),
    (("test_stable", "test_different"), "equivalent coverage"),
    (('name="test_stable"/>', 'name="test_stable"><failure/></testcase>'), "equivalent coverage"),
    (('name="test_stable"/>', 'name="test_stable"><skipped/></testcase>'), "equivalent coverage"),
    (('name="test_stable"/>', 'name="test_stable"><properties><property name="flake.reruns" value="1"/>'
      '</properties></testcase>'), "equivalent coverage"),
])
def test_admission_requires_exact_failed_node_and_passing_equivalent_coverage(admission, replacement, message):
    admission.artifacts[102] = admission.artifacts[102].replace(*replacement)
    with pytest.raises(ValueError, match=message):
        flake_quarantine.check_admissions([admission.entry], [], repository="example/project")


def test_first_failure_recovered_in_baseline_is_still_observed_evidence(admission):
    admission.artifacts[102] = admission.artifacts[102].replace(
        '<failure message="assert 0"/>',
        '<properties><property name="flake.reruns" value="1"/></properties>',
    )
    assert flake_quarantine.check_admissions([admission.entry], [], repository="example/project") == 1


@pytest.mark.parametrize("node,message", [
    ("test_flaky", "exact-node baseline failure"),
    ("test_stable", "equivalent coverage"),
])
def test_admission_refuses_duplicate_results_for_same_node(admission, node, message):
    duplicate = f'<testcase classname="tests.test_sample" name="{node}">'
    if node == "test_flaky":
        duplicate += '<failure message="assert 0"/>'
    duplicate += '</testcase>'
    admission.duplicates[102] = f"<testsuite>{duplicate}</testsuite>"
    with pytest.raises(ValueError, match=message):
        flake_quarantine.check_admissions([admission.entry], [], repository="example/project")


def test_unchanged_entries_and_removals_need_no_expiring_artifacts(admission):
    assert flake_quarantine.check_admissions([admission.entry], [copy.deepcopy(admission.entry)],
                                           repository="example/project") == 0
    assert flake_quarantine.check_admissions([], [admission.entry], repository="example/project") == 0
    assert admission.calls == []


def test_renewal_requires_new_bound_approval(admission):
    old = copy.deepcopy(admission.entry)
    admission.entry.update(renewals=1, renewed_on=date(2026, 10, 18), expires_on=date(2026, 11, 17))
    with pytest.raises(ValueError, match="bound to this entry"):
        flake_quarantine.check_admissions([admission.entry], [old], repository="example/project")
    admission.responses[f"{admission.prefix}/issues/comments/999"]["body"] = (
        f"<!-- flake-quarantine-admission:{flake_quarantine.admission_digest(admission.entry)}:APPROVE -->"
    )
    assert flake_quarantine.check_admissions([admission.entry], [old], repository="example/project") == 1


def test_github_unavailable_never_admits(admission, monkeypatch):
    def unavailable(*args):
        raise subprocess.CalledProcessError(1, ["gh", *args], stderr="unavailable")

    monkeypatch.setattr(flake_quarantine, "_gh", unavailable)
    with pytest.raises(subprocess.CalledProcessError, match="non-zero exit status"):
        flake_quarantine.check_admissions([admission.entry], [], repository="example/project")


def test_main_checks_changes_and_reports_empty_registry_without_github(admission, monkeypatch, capsys):
    monkeypatch.setattr(flake_quarantine.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout="entries: []"))
    monkeypatch.setattr(flake_quarantine, "load_registry", lambda: [admission.entry])
    assert flake_quarantine.main(["--base-ref", "origin/main"]) == 0
    assert "1 changed admissions verified" in capsys.readouterr().out
    admission.calls.clear()
    monkeypatch.setattr(flake_quarantine, "load_registry", lambda: [])
    assert flake_quarantine.main(["--base-ref", "origin/main"]) == 0
    assert "0 entries, 0 changed; offline lint passed" in capsys.readouterr().out
    assert admission.calls == []


def test_main_allows_removal_without_github(admission, monkeypatch, capsys):
    baseline = yaml.safe_dump({"entries": [admission.entry]})
    monkeypatch.setattr(flake_quarantine.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout=baseline))
    monkeypatch.setattr(flake_quarantine, "load_registry", lambda: [])
    assert flake_quarantine.main(["--base-ref", "origin/main"]) == 0
    assert "0 entries, 0 changed" in capsys.readouterr().out
    assert admission.calls == []


def test_github_transport_reads_fresh_with_a_timeout(monkeypatch):
    from scripts.common import github_client

    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(stdout='{"state":"open"}')

    monkeypatch.setattr(github_client, "run", run)
    assert flake_quarantine._gh("api", "repos/example/project/issues/123") == '{"state":"open"}'
    assert calls == [(["gh", "api", "repos/example/project/issues/123"], {
        "fresh": True, "capture_output": True, "text": True, "check": True, "timeout": 120,
    })]


def test_ci_checks_job_enforces_admission_with_read_only_evidence_permissions():
    workflow = yaml.safe_load(Path(".github/workflows/ci.yml").read_text())
    checks = workflow["jobs"]["checks"]
    step = next(step for step in checks["steps"] if step.get("name") == "Verify flake quarantine admissions")
    assert step["run"] == '.venv/bin/python -m scripts.common.flake_quarantine --base-ref "$BASE_SHA"'
    assert "github.event.pull_request.base.sha" in step["env"]["BASE_SHA"]
    assert "github.event.merge_group.base_sha" in step["env"]["BASE_SHA"]
    assert step["env"]["GH_TOKEN"] == "${{ github.token }}"
    assert not step.get("continue-on-error") and not step.get("if")
    assert checks["permissions"] == {"contents": "read", "actions": "read", "issues": "read"}


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
