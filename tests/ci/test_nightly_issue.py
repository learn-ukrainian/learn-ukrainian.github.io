from __future__ import annotations

import json
from pathlib import Path

from scripts.ci import nightly_issue as ni

URL = "https://github.com/o/r/actions/runs/1"
OWNERS = {"default": "core", "paths": {"tests/projects/": "open-model-data", ".github/": "infra"}}


class FakeGh:
    def __init__(self, open_issues: list[dict] | None = None) -> None:
        self.open_issues = open_issues or []
        self.calls: list[list[str]] = []

    def __call__(self, args):
        self.calls.append(list(args))
        if args[:2] == ["issue", "list"]:
            return json.dumps(self.open_issues)
        return ""

    def verbs(self) -> list[str]:
        return [" ".join(c[:2]) for c in self.calls if c[:2] != ["issue", "list"]]


def _junit(tmp_path: Path, files: list[str]) -> Path:
    cases = "".join(
        f'<testcase classname="x" name="t{i}" file="{f}"><failure message="boom"/></testcase>'
        for i, f in enumerate(files)
    )
    cases += '<testcase classname="x" name="ok" file="tests/api/test_ok.py"/>'
    path = tmp_path / "junit.xml"
    path.write_text(f"<testsuites><testsuite>{cases}</testsuite></testsuites>", encoding="utf-8")
    return path


def test_lane_longest_prefix_and_default() -> None:
    assert ni.lane_for("tests/projects/x/test_a.py", OWNERS) == "open-model-data"
    assert ni.lane_for(".github/workflows/zizmor.yml", OWNERS) == "infra"
    assert ni.lane_for("tests/test_foo.py", OWNERS) == "core"


def test_group_for() -> None:
    assert ni.group_for("tests/audit/sub/test_x.py") == "tests/audit/"
    assert ni.group_for("tests/test_open_model_phase3.py") == "tests/test_open*"


def test_failure_without_junit_opens_one_workflow_issue() -> None:
    fake = FakeGh()
    actions = ni.report(fake, key="Zizmor", status="failure", run_url=URL, owners=OWNERS,
                        workflow_path=".github/workflows/zizmor.yml")
    assert actions == ["create [nightly] Zizmor failing"]
    create = next(c for c in fake.calls if c[:2] == ["issue", "create"])
    assert "lane:infra" in create and ni.LABEL in create


def test_failure_comments_on_existing_issue_instead_of_duplicating() -> None:
    fake = FakeGh([{"number": 7, "title": "[nightly] Zizmor failing"}])
    ni.report(fake, key="Zizmor", status="failure", run_url=URL, owners=OWNERS)
    assert fake.verbs() == ["issue comment"]


def test_one_issue_per_failing_group(tmp_path: Path) -> None:
    junit = _junit(tmp_path, ["tests/projects/a/test_1.py", "tests/projects/b/test_2.py",
                              "tests/test_open_model_x.py"])
    fake = FakeGh()
    actions = ni.report(fake, key="Nightly", status="failure", run_url=URL, owners=OWNERS,
                        junit=[junit])
    assert sorted(actions) == ["create [nightly] Nightly: tests/projects/ failing",
                               "create [nightly] Nightly: tests/test_open* failing"]


def test_green_closes_owned_issues_only() -> None:
    fake = FakeGh([{"number": 3, "title": "[nightly] Nightly: tests/audit/ failing"},
                   {"number": 4, "title": "[nightly] Other failing"},
                   {"number": 8, "title": "[nightly] Nightly2 failing"}])
    actions = ni.report(fake, key="Nightly", status="success", run_url=URL, owners=OWNERS)
    assert actions == ["close #3 [nightly] Nightly: tests/audit/ failing"]


def test_failed_run_never_closes_issues(tmp_path: Path) -> None:
    junit = _junit(tmp_path, ["tests/projects/a/test_1.py"])
    fake = FakeGh([{"number": 5, "title": "[nightly] Nightly: tests/audit/ failing"},
                   {"number": 6, "title": "[nightly] Nightly: tests/projects/ failing"}])
    actions = ni.report(fake, key="Nightly", status="failure", run_url=URL, owners=OWNERS,
                        junit=[junit])
    assert actions == ["comment #6 [nightly] Nightly: tests/projects/ failing"]
    missing = ni.report(FakeGh([{"number": 5, "title": "[nightly] Nightly: tests/audit/ failing"}]),
                        key="Nightly", status="failure", run_url=URL, owners=OWNERS,
                        junit=[tmp_path / "absent.xml"])
    assert missing == ["create [nightly] Nightly failing"]


def test_unexpected_junit_paths_fall_back_to_a_workflow_issue(tmp_path: Path) -> None:
    junit = _junit(tmp_path, ["/home/someone/private/test_x.py"])
    actions = ni.report(FakeGh(), key="Nightly", status="failure", run_url=URL, owners=OWNERS,
                        junit=[junit])
    assert actions == ["create [nightly] Nightly failing"]


def test_unexpected_run_url_is_refused() -> None:
    import pytest

    with pytest.raises(ValueError):
        ni.report(FakeGh(), key="Nightly", status="failure", run_url="https://evil/x", owners=OWNERS)


def test_cancelled_or_skipped_run_changes_nothing() -> None:
    for status in ("cancelled", "skipped", ""):
        assert ni.main(["--key", "k", "--status", status, "--run-url", URL]) == 0


def test_repo_owner_map_is_valid() -> None:
    owners = ni.load_owners(Path(__file__).resolve().parents[2] / ".github/nightly-owners.json")
    assert owners["default"]
