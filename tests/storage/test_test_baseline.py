from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.storage.test_baseline import (
    BaselineError,
    _pack_baseline,
    _safe_json,
    _unpack_baseline,
    capture_junit,
    compare_baselines,
    main,
    nodeid_to_junit_id,
)


def _junit(path: Path, cases: str) -> Path:
    path.write_text(f'<testsuite name="pytest">{cases}</testsuite>', encoding="utf-8")
    return path


def test_capture_records_sorted_ids_and_outcomes_per_job(tmp_path: Path) -> None:
    xml = _junit(
        tmp_path / "results.xml",
        '<testcase classname="pkg.mod" name="test_skip"><skipped message="missing"/></testcase>'
        '<testcase classname="pkg.mod" name="test_ok"/>',
    )
    result = capture_junit([("pytest-1", xml)], source_sha="abc123")
    assert result == {
        "schema_version": 1,
        "source_sha": "abc123",
        "jobs": {
            "pytest-1": {
                "collected": 2,
                "outcomes": {"pkg.mod::test_ok": "passed", "pkg.mod::test_skip": "skipped"},
                "skip_reasons": {"pkg.mod::test_skip": "missing"},
            }
        },
    }


def test_packed_baseline_roundtrips_exact_ids_without_raw_secret_patterns() -> None:
    synthetic_ip = ".".join(("10", "0", "0", "7"))
    synthetic_header = "-" * 5 + "BEGIN OPENSSH PRIVATE KEY" + "-" * 5
    baseline = {
        "schema_version": 1,
        "source_run": "123",
        "jobs": {
            "pytest-1": {
                "collected": 3,
                "outcomes": {
                    "pkg::test_many[case-a]": "passed",
                    f"pkg::test_many[{synthetic_ip}]": "skipped",
                    f"pkg::test_many[{synthetic_header}]": "failed",
                },
                "skip_reasons": {f"pkg::test_many[{synthetic_ip}]": "needs_artifact: absent"},
            }
        },
    }
    encoded = _safe_json(_pack_baseline(baseline))
    assert synthetic_ip not in encoded
    assert synthetic_header not in encoded
    assert _unpack_baseline(json.loads(encoded)) == baseline


@pytest.mark.parametrize(
    ("dispositions", "expected"),
    [
        ({}, ["undisposed"]),
        ({"needs_artifact": [{"job": "pytest-1", "id": "pkg::test_data", "host_run": "  "}]}, ["exact ID"]),
        (
            {
                "needs_artifact": [
                    {
                        "job": "pytest-1",
                        "id": "pkg::test_data",
                        "host_run": "PASSED pkg::test_data\n= 1 passed in 0.01s =",
                    }
                ]
            },
            [],
        ),
        (
            {"fixture": [{"job": "pytest-1", "id": "pkg::test_data", "fixture": "tests/fixtures/x.json"}]},
            ["passing CI outcome"],
        ),
    ],
)
def test_compare_enforces_needs_artifact_and_fixture_evidence(dispositions: dict, expected: list[str]) -> None:
    old = {"jobs": {"pytest-1": {"outcomes": {"pkg::test_data": "passed"}}}}
    new = {
        "jobs": {
            "pytest-1": {
                "outcomes": {"pkg::test_data": "skipped"},
                "skip_reasons": {"pkg::test_data": "needs_artifact: missing artifact"},
            }
        }
    }
    errors = compare_baselines(old, new, dispositions)
    for message in expected:
        assert any(message in error for error in errors)
    if not expected:
        assert errors == []


def test_compare_requires_paired_rename() -> None:
    old = {"jobs": {"pytest-1": {"outcomes": {"pkg::old": "passed"}}}}
    new = {"jobs": {"pytest-1": {"outcomes": {"pkg::new": "passed"}}}}
    assert compare_baselines(old, new, {"renamed": [{"job": "pytest-1", "old": "pkg::old", "new": "pkg::new"}]}) == []


def test_needs_artifact_disposition_rejects_an_unrelated_skip() -> None:
    old = {"jobs": {"pytest-1": {"outcomes": {"pkg::test_data": "passed"}}}}
    new = {
        "jobs": {
            "pytest-1": {"outcomes": {"pkg::test_data": "skipped"}, "skip_reasons": {"pkg::test_data": "unrelated"}}
        }
    }
    dispositions = {
        "needs_artifact": [{"job": "pytest-1", "id": "pkg::test_data", "host_run": "pkg::test_data PASSED"}]
    }
    assert "needs_artifact CI skip" in compare_baselines(old, new, dispositions)[0]


def test_fixture_disposition_requires_committed_fixture_and_pass(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, timeout=30)
    fixture = tmp_path / "tests/fixtures/example.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "add", "tests/fixtures/example.json"], cwd=tmp_path, check=True, timeout=30)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"],
        cwd=tmp_path,
        check=True,
        timeout=30,
    )
    old = {"jobs": {"pytest-1": {"outcomes": {"pkg::test_fixture": "failed"}}}}
    new = {"jobs": {"pytest-1": {"outcomes": {"pkg::test_fixture": "passed"}}}}
    dispositions = {
        "fixture": [{"job": "pytest-1", "id": "pkg::test_fixture", "fixture": "tests/fixtures/example.json"}]
    }
    assert compare_baselines(old, new, dispositions, repo_root=tmp_path) == []
    dispositions["fixture"][0]["fixture"] = "tests/fixtures/missing.json"
    assert "absent from HEAD" in compare_baselines(old, new, dispositions, repo_root=tmp_path)[0]


def test_duplicate_test_ids_in_junit_are_rejected(tmp_path: Path) -> None:
    xml = _junit(
        tmp_path / "duplicate.xml",
        '<testcase classname="pkg" name="same"/><testcase classname="pkg" name="same"/>',
    )
    with pytest.raises(BaselineError, match="duplicate test ID"):
        capture_junit([("pytest-1", xml)])


def test_passing_addition_and_cross_job_move_are_accepted() -> None:
    old = {"jobs": {"pytest-1": {"outcomes": {"pkg::existing": "passed"}}}}
    new = {"jobs": {"pytest-2": {"outcomes": {"pkg::existing": "passed", "pkg::added": "passed"}}}}
    assert compare_baselines(old, new, {}) == []
    new["jobs"]["pytest-2"]["outcomes"]["pkg::added"] = "failed"
    assert "undisposed" in compare_baselines(old, new, {})[0]


@pytest.mark.parametrize("outcome", ["failed", "skipped", "error"])
def test_cross_job_rename_requires_passed(outcome: str) -> None:
    old = {"jobs": {"pytest-1": {"outcomes": {"pkg::old": "passed"}}}}
    new = {"jobs": {"pytest-2": {"outcomes": {"pkg::new": outcome}}}}
    row = {"renamed": [{"old": "pkg::old", "new": "pkg::new"}]}
    assert "requires the new outcome passed" in compare_baselines(old, new, row)[0]
    new["jobs"]["pytest-2"]["outcomes"]["pkg::new"] = "passed"
    assert compare_baselines(old, new, row) == []


def test_rename_to_artifact_skip_requires_its_own_disposition() -> None:
    old = {"jobs": {"a": {"outcomes": {"pkg::old": "passed"}}}}
    new = {"jobs": {"b": {"outcomes": {"pkg::new": "skipped"}, "skip_reasons": {"pkg::new": "needs_artifact: absent"}}}}
    dispositions = {
        "renamed": [{"old": "pkg::old", "new": "pkg::new"}],
        "needs_artifact": [{"id": "pkg::new", "host_run": "PASSED pkg::new\n= 1 passed in 0.01s ="}],
    }
    assert compare_baselines(old, new, dispositions) == []


def test_host_run_rejects_failing_summary_and_accepts_junit(tmp_path: Path) -> None:
    old = {"jobs": {"a": {"outcomes": {"pkg::test_data": "passed"}}}}
    new = {
        "jobs": {
            "b": {
                "outcomes": {"pkg::test_data": "skipped"},
                "skip_reasons": {"pkg::test_data": "needs_artifact: absent"},
            }
        }
    }
    row = {
        "needs_artifact": [
            {"id": "pkg::test_data", "host_run": "PASSED pkg::test_data\n= 1 passed, 1 failed in 0.1s ="}
        ]
    }
    assert compare_baselines(old, new, row)
    xml = _junit(tmp_path / "host.xml", '<testcase classname="pkg" name="test_data"/>')
    row["needs_artifact"][0]["host_run"] = {"junit": str(xml)}
    assert compare_baselines(old, new, row) == []
    _junit(xml, '<testcase classname="pkg" name="test_data"><failure/></testcase>')
    assert compare_baselines(old, new, row)
    xml.write_text('<testsuite failures="1"><testcase classname="pkg" name="test_data"/></testsuite>')
    assert compare_baselines(old, new, row)


def test_compare_cli_reports_passing_addition(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    old = tmp_path / "old.json"
    new = tmp_path / "new.json"
    dispositions = tmp_path / "dispositions.json"
    old.write_text(json.dumps({"jobs": {"a": {"outcomes": {"pkg::existing": "passed"}}}}))
    new.write_text(json.dumps({"jobs": {"b": {"outcomes": {"pkg::existing": "passed", "pkg::new": "passed"}}}}))
    dispositions.write_text("{}")
    assert main(["compare", "--old", str(old), "--new", str(new), "--dispositions", str(dispositions)]) == 0
    assert "ADDED passed pkg::new (job b)" in capsys.readouterr().out


def test_collected_node_ids_match_junit_ids_for_classes_and_parameter_colons() -> None:
    assert nodeid_to_junit_id("tests/pkg/test_mod.py::TestCase::test_example[param::name]") == (
        "tests.pkg.test_mod.TestCase::test_example[param::name]"
    )
    assert nodeid_to_junit_id("scripts/test_tool.py::test_one") == "scripts.test_tool::test_one"
