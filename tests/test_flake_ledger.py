"""Ledger counts queue runs and acts only at the D2 escalation boundary."""

from datetime import date, timedelta

from scripts.ci import flake_ledger
from scripts.ci.flake_ledger import make_ledger, update_issues


def test_ledger_counts_distinct_queue_runs_and_expiry(tmp_path, monkeypatch):
    today = date(2026, 9, 28)
    node = "tests/test_sample.py::test_flaky"
    xml = tmp_path / "rerun.xml"
    xml.write_text(
        '<testsuite><testcase classname="tests.test_sample" name="test_flaky" file="tests/test_sample.py">'
        '<properties><property name="flake.reruns" value="1"/></properties></testcase></testsuite>',
        encoding="utf-8",
    )
    nightly = tmp_path / "nightly.xml"
    nightly.write_text(
        '<testsuite><testcase classname="tests.test_sample" name="test_flaky" file="tests/test_sample.py">'
        '<failure message="still flaky"/></testcase></testsuite>', encoding="utf-8",
    )
    entries = [{"node_id": node, "fix_issue": 123, "owner": "infra", "expires_on": today}]
    ledger = make_ledger(entries, {1: [xml], 2: [xml]}, [nightly], today=today, missing_runs=[3])
    row = ledger["entries"][0]
    assert ledger["queue_run_count"] == 3
    assert row["recovered_queue_run_ids"] == [1, 2]
    assert row["queue_rerun_percent"] == 66.67
    assert row["nightly_failures"] == ["still flaky"]
    monkeypatch.setattr(flake_ledger, "_gh", lambda *args: '{"state":"OPEN","labels":[],"comments":[]}')
    assert update_issues(ledger, dry_run=True) == ["comment #123: expiry", "escalate #123: 66.67%"]
    entries[0]["expires_on"] = today + timedelta(days=1)
    assert not make_ledger(entries, {}, [nightly], today=today)["entries"][0]["expired"]


def test_queue_runs_that_reused_a_green_run_are_not_missing_evidence(tmp_path, monkeypatch):
    """ci.yml's merge-queue reuse skips every shard: no JUnit, and none expected."""
    import json
    import subprocess

    jobs = {
        101: [{"name": "Reuse check", "conclusion": "success"}, {"name": "pytest (1)", "conclusion": "skipped"}],
        102: [{"name": "Reuse check", "conclusion": "success"}, {"name": "pytest (1)", "conclusion": "failure"}],
        103: [{"name": "Reuse check", "conclusion": "failure"}, {"name": "pytest (1)", "conclusion": "skipped"}],
    }

    def fake_gh(*args):
        if args[:2] == ("run", "list"):
            return json.dumps([{"databaseId": run, "createdAt": "2026-09-29T00:00:00Z"} for run in jobs])
        if args[:2] == ("run", "download"):
            raise subprocess.CalledProcessError(1, ["gh", *args])
        if args[:2] == ("run", "view"):
            return json.dumps({"jobs": jobs[int(args[2])]})
        raise AssertionError(args)

    monkeypatch.setattr(flake_ledger, "_gh", fake_gh)
    artifacts, missing = flake_ledger.fetch_queue_junit(tmp_path, since=date(2026, 9, 28))
    assert artifacts == {}
    assert missing == [102, 103]
