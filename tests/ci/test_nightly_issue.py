from __future__ import annotations

import json
from pathlib import Path

from scripts.ci import nightly_issue as ni

URL = "https://github.com/o/r/actions/runs/1"
REPO = Path(__file__).resolve().parents[2]
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
    actions = ni.report(fake, key="zizmor.yml", status="failure", run_url=URL, owners=OWNERS,
                        workflow_path=".github/workflows/zizmor.yml")
    assert actions == ["create [nightly] zizmor.yml failing"]
    create = next(c for c in fake.calls if c[:2] == ["issue", "create"])
    assert "lane:infra" in create and ni.LABEL in create


def test_failure_comments_on_existing_issue_instead_of_duplicating() -> None:
    fake = FakeGh([{"number": 7, "title": "[nightly] zizmor.yml failing"}])
    ni.report(fake, key="zizmor.yml", status="failure", run_url=URL, owners=OWNERS)
    assert fake.verbs() == ["issue comment"]


def test_one_issue_per_failing_group(tmp_path: Path) -> None:
    junit = _junit(tmp_path, ["tests/projects/a/test_1.py", "tests/projects/b/test_2.py",
                              "tests/test_open_model_x.py"])
    fake = FakeGh()
    actions = ni.report(fake, key="nightly.yml", status="failure", run_url=URL, owners=OWNERS,
                        junit=[junit], root=REPO)
    assert sorted(actions) == ["create [nightly] nightly.yml: tests/projects/ failing",
                               "create [nightly] nightly.yml: tests/test_open* failing"]


def test_green_closes_owned_issues_only() -> None:
    fake = FakeGh([{"number": 3, "title": "[nightly] nightly.yml: tests/audit/ failing"},
                   {"number": 4, "title": "[nightly] Other failing"},
                   {"number": 8, "title": "[nightly] nightly2.yml failing"}])
    actions = ni.report(fake, key="nightly.yml", status="success", run_url=URL, owners=OWNERS)
    assert actions == ["close #3 [nightly] nightly.yml: tests/audit/ failing"]


def test_failed_run_never_closes_issues(tmp_path: Path) -> None:
    junit = _junit(tmp_path, ["tests/projects/a/test_1.py"])
    fake = FakeGh([{"number": 5, "title": "[nightly] nightly.yml: tests/audit/ failing"},
                   {"number": 6, "title": "[nightly] nightly.yml: tests/projects/ failing"}])
    actions = ni.report(fake, key="nightly.yml", status="failure", run_url=URL, owners=OWNERS,
                        junit=[junit], root=REPO)
    assert actions == ["comment #6 [nightly] nightly.yml: tests/projects/ failing"]
    missing = ni.report(FakeGh([{"number": 5, "title": "[nightly] nightly.yml: tests/audit/ failing"}]),
                        key="nightly.yml", status="failure", run_url=URL, owners=OWNERS,
                        junit=[tmp_path / "absent.xml"])
    assert missing == ["create [nightly] nightly.yml failing"]


def test_unexpected_junit_paths_fall_back_to_a_workflow_issue(tmp_path: Path) -> None:
    junit = _junit(tmp_path, ["/home/someone/private/test_x.py"])
    actions = ni.report(FakeGh(), key="nightly.yml", status="failure", run_url=URL, owners=OWNERS,
                        junit=[junit], root=REPO)
    assert actions == ["create [nightly] nightly.yml failing"]


def test_unexpected_run_url_is_refused() -> None:
    import pytest

    with pytest.raises(ValueError):
        ni.report(FakeGh(), key="nightly.yml", status="failure", run_url="https://evil/x", owners=OWNERS)


def test_cancelled_or_skipped_run_changes_nothing() -> None:
    for status in ("cancelled", "skipped", ""):
        assert ni.main(["--key", "k", "--status", status, "--run-url", URL]) == 0


def test_repo_owner_map_is_valid() -> None:
    owners = ni.load_owners(Path(__file__).resolve().parents[2] / ".github/nightly-owners.json")
    assert owners["default"]


def test_unreadable_report_or_unapproved_group_reports_at_workflow_level(tmp_path: Path) -> None:
    bad = tmp_path / "bad.xml"
    bad.write_text("<testsuites><testsuite>", encoding="utf-8")
    assert ni.report(FakeGh(), key="nightly.yml", status="failure", run_url=URL, owners=OWNERS,
                     junit=[bad], root=REPO) == ["create [nightly] nightly.yml failing"]
    unknown = _junit(tmp_path, ["tests/zz_not_a_real_dir/test_x.py"])
    assert ni.report(FakeGh(), key="nightly.yml", status="failure", run_url=URL, owners=OWNERS,
                     junit=[unknown], root=REPO) == ["create [nightly] nightly.yml failing"]


def test_classname_maps_to_the_test_file() -> None:
    import xml.etree.ElementTree as ET

    case = ET.fromstring('<testcase classname="tests.test_open_model_x.TestCase" name="t"/>')
    assert ni._case_file(case) == "tests/test_open_model_x.py"
    assert ni._case_file(ET.fromstring('<testcase file="/abs/tests/x/test_a.py"/>')) is None


def test_workflow_name_with_emoji_is_not_the_key() -> None:
    import pytest

    with pytest.raises(ValueError):
        ni.report(FakeGh(), key="Zizmor 🌈", status="failure", run_url=URL, owners=OWNERS)


def test_green_closes_every_duplicate() -> None:
    fake = FakeGh([{"number": 3, "title": "[nightly] nightly.yml failing"},
                   {"number": 4, "title": "[nightly] nightly.yml failing"}])
    assert ni.report(fake, key="nightly.yml", status="success", run_url=URL, owners=OWNERS) == [
        "close #3 [nightly] nightly.yml failing", "close #4 [nightly] nightly.yml failing"]
