"""Advisory selection boundaries and independent full-run failure scoring."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

import pytest

from scripts.ci import component_shadow as s
from scripts.ci import components as c
from scripts.ci import pytest_report


def git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def commit(root):
    git(root, "add", ".")
    git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture")
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init")
    for name in s.TOOLS:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((c.ROOT / name).read_bytes())
    path = tmp_path / "tests/test_sample.py"
    path.parent.mkdir()
    path.write_text("def test_sample():\n    assert True\n")
    commit(tmp_path)
    return tmp_path


@pytest.fixture
def static_graph(monkeypatch):
    graph = {"file_edges": [], "node_edges": [], "unresolved_edges": [], "missing_mandatory_edges": []}
    monkeypatch.setattr(c, "import_graph", lambda *args: graph)
    return graph


def test_empty_diff_and_missing_base_are_full(repo, static_graph):
    head = git(repo, "rev-parse", "HEAD")
    for base, reason in [(head, "empty-diff"), ("", "missing-base"), ("no-such-base", "diff-unavailable")]:
        result = s.select(base, head, "pull_request", repo)
        assert result["mode"] == "full"
        assert result["reason"] == reason
        assert result["selected_test_files"] == ["tests/test_sample.py"]


def test_historical_subject_can_predate_observer_tools(repo, static_graph):
    for name in s.TOOLS:
        (repo / name).unlink()
    head = commit(repo)
    result = s.select(head, head, "pull_request", repo)
    assert result["mode"] == "full"
    assert set(result["identities"]["tool_hashes"]) == set(s.TOOLS)


@pytest.mark.parametrize("event", ["workflow_dispatch", "merge_group", "schedule"])
def test_non_pr_events_always_full(repo, static_graph, event):
    assert s.select("", "HEAD", event, repo)["reason"] == "non-pr-event"


def test_stacked_pr_diff_includes_parent_and_ignores_new_base_commits(repo, static_graph):
    base = git(repo, "rev-parse", "HEAD")
    parent = repo / "site/parent.ts"
    parent.parent.mkdir()
    parent.write_text("parent")
    commit(repo)
    (repo / "site/top.ts").write_text("top")
    head = commit(repo)
    # Construct the advanced base with plumbing, without branch switching.
    git(repo, "read-tree", base)
    (repo / "site/base-only.ts").write_text("base")
    git(repo, "add", "site/base-only.ts")
    tree = git(repo, "write-tree")
    advanced_base = git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit-tree", tree, "-p", base, "-m", "advanced base")
    git(repo, "read-tree", head)
    result = s.select(advanced_base, head, "pull_request", repo)
    assert result["changed_paths"] == ["site/parent.ts", "site/top.ts"]


def test_renames_and_deletions_include_both_sides(repo, static_graph):
    path = repo / "site/old.ts"
    path.parent.mkdir()
    path.write_text("unchanged\n" * 20)
    deleted = repo / "site/deleted.ts"
    deleted.write_text("delete")
    base = commit(repo)
    path.rename(repo / "site/new.ts")
    deleted.unlink()
    head = commit(repo)
    result = s.select(base, head, "pull_request", repo)
    assert result["changed_paths"] == ["site/deleted.ts", "site/new.ts", "site/old.ts"]


@pytest.mark.parametrize("path,reason", [
    (".github/test.txt", "workflow-tool-or-dependency"),
    ("site/pnpm-lock.yaml", "workflow-tool-or-dependency"),
    ("site/nested/package.json", "workflow-tool-or-dependency"),
    ("site/nested/requirements.in", "workflow-tool-or-dependency"),
    ("requirements-new.txt", "workflow-tool-or-dependency"),
    ("scripts/ci/new.py", "workflow-tool-or-dependency"),
    ("scripts/config.py", "shared-core"),
    ("unknown/new.txt", "unmapped"),
])
def test_full_triggers(repo, static_graph, path, reason):
    base = git(repo, "rev-parse", "HEAD")
    file = repo / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("changed")
    head = commit(repo)
    result = s.select(base, head, "pull_request", repo)
    assert result["mode"] == "full"
    assert result["reason"] == reason


def test_selection_uses_resolved_importers_and_integration(repo, static_graph):
    source = "scripts/projects/open_model_data/new.py"
    test = repo / "tests/test_importer.py"
    test.write_text("import scripts.projects.open_model_data.new\n")
    base = commit(repo)
    path = repo / source
    path.parent.mkdir(parents=True)
    path.write_text("VALUE=1")
    head = commit(repo)
    static_graph["file_edges"] = [("tests/test_importer.py", source)]
    result = s.select(base, head, "pull_request", repo)
    assert result["mode"] == "selected"
    assert result["selected_nodes"] == ["open-model-data"]
    assert "tests/test_importer.py" in result["selected_test_files"]
    assert set(c.load_manifest()["shared_integration_tests"]) <= set(result["selected_test_files"])


def test_diff_timeout_is_full(repo, static_graph, monkeypatch):
    monkeypatch.setattr(s.dependency, "resolve_git_range", lambda *args, **kwargs: (_ for _ in ()).throw(
        subprocess.TimeoutExpired("git", 30)))
    assert s.select("base", "HEAD", "pull_request", repo)["reason"] == "diff-unavailable"


@pytest.fixture
def registration():
    return {"schema": s.SCHEMA, "registered_at": "2026-10-07T00:00:00Z", "stop_at": "2026-11-06T00:00:00Z",
            "identities": {"tool_hashes": {"tool": "hash"}}, "historical_run_ids": ["999"],
            "minimum_narrowed_cases": 1,
            "live_window": {"completed_first_attempt_pr_runs": 150, "minimum_pytest_red_runs": 30},
            "flaky_classification_rule": s.FLAKE_RULE, "base_commit_rerun_rule": s.BASE_RULE,
            "injections_frozen": True, "injected_cases": [
                {"id": "injection-" + label, "coverage": [label], "registered_at": "2026-10-07T00:00:00Z",
                 "expected_failure_ids": ["tests/test_selected.py::test_fault"]}
                for label in sorted(s.INJECTION_COVERAGE)]}


def receipt(run_id, kind="historical", **overrides):
    return {"schema": s.SCHEMA, "kind": kind, "run_id": str(run_id), "run_attempt": 1,
            "head_sha": "head", "base_sha": "base", "observed_at": "2026-10-08T00:00:00Z",
            "mode": "selected", "would_skip_test_files": ["tests/test_other.py"],
            "selected_test_files": ["tests/test_selected.py"], "full_junit_failing_ids": [],
            "collection_errors": [], "artifact_problems": [], "junit_hashes": {"shard.xml": "hash"},
            "identities": {"tool_hashes": {"tool": "hash"}}, **overrides}


def save(root, value, name=None):
    if value.get("schema") == s.SCHEMA:
        suite = ET.Element("testsuite")
        failures = set(value["full_junit_failing_ids"]) | set(value["collection_errors"])
        for failure in sorted(failures or {"tests/test_selected.py::test_pass"}):
            file, *suffix = failure.split("::")
            if suffix:
                case = ET.SubElement(suite, "testcase", classname=file[:-3].replace("/", "."), name="::".join(suffix))
            else:
                case = ET.SubElement(suite, "testcase", name=file[:-3].replace("/", "."))
            if failure in failures:
                ET.SubElement(case, "error" if failure in value["collection_errors"] else "failure")
        artifact = root / str(value["run_id"]) / "junit" / "shard.xml"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(ET.tostring(suite))
        if value.get("junit_hashes"):
            value["junit_hashes"] = {artifact.name: hashlib.sha256(artifact.read_bytes()).hexdigest()}
        value["full_junit_failing_ids"] = sorted(failures)
    path = root / (name or str(value["run_id"]) + ".json")
    path.write_text(json.dumps(value))


@pytest.fixture
def window(tmp_path):
    rows = [{"run_id": str(i), "event": "pull_request", "run_attempt": 1, "status": "completed",
             "created_at": "2026-10-07T01:00:00Z", "completed_at": "2026-10-08T00:00:00Z",
             "head_sha": "head", "pytest_red": i <= 30} for i in range(1, 151)]
    save(tmp_path, {"complete": True, "first_attempts": True, "runs": rows}, "runs.json")
    for row in rows:
        save(tmp_path, receipt(row["run_id"], "live"))
    save(tmp_path, receipt("999"))
    for label in s.INJECTION_COVERAGE:
        save(tmp_path, receipt("injection-" + label, "injected",
                               full_junit_failing_ids=["tests/test_selected.py::test_fault"]))
    return tmp_path


def test_complete_window_zero_misses_is_the_only_success(registration, window):
    result = s.check(registration, window, now="2026-10-09T00:00:00Z")
    assert result["status"] == "pass"
    assert result["registered_case_count"] == 163
    assert result["narrowed_red_case_count"] == 31
    assert result["narrowed_injected_case_count"] == 12
    assert result["narrowed_case_count"] == 43
    assert result["missed_failure_count"] == result["unresolved_count"] == 0


@pytest.mark.parametrize("mode", ["full", "selected"])
def test_window_without_any_skipped_files_cannot_pass(registration, window, mode):
    for path in window.glob("*.json"):
        value = json.loads(path.read_text())
        if value.get("schema") == s.SCHEMA:
            value.update(mode=mode, would_skip_test_files=[])
            path.write_text(json.dumps(value))
    result = s.check(registration, window, now="2026-10-09T00:00:00Z")
    assert result["status"] == "unresolved"
    assert result["narrowed_case_count"] == 0
    assert result["narrowed_red_case_count"] == result["narrowed_injected_case_count"] == 0
    assert "narrowed-cases:0/1" in result["unresolved"]
    assert s.main(["check", "--registration", str(_registration_file(window, registration)),
                   "--registration-sha256", hashlib.sha256(s.canonical_registration_bytes(registration)).hexdigest(),
                   "--receipts", str(window)]) == 1


def test_narrowing_below_registered_minimum_cannot_pass(registration, window):
    registration["minimum_narrowed_cases"] = 44
    result = s.check(registration, window)
    assert result["status"] == "unresolved"
    assert result["narrowed_case_count"] == 43
    assert result["minimum_narrowed_cases"] == 44
    assert "narrowed-cases:43/44" in result["unresolved"]
    assert s.main(["check", "--registration", str(_registration_file(window, registration)),
                   "--registration-sha256", hashlib.sha256(s.canonical_registration_bytes(registration)).hexdigest(),
                   "--receipts", str(window)]) == 1
    registration["minimum_narrowed_cases"] = 43
    assert s.check(registration, window)["status"] == "pass"


def test_only_green_live_cases_narrowing_is_unresolved(registration, window):
    for path in window.glob("*.json"):
        value = json.loads(path.read_text())
        if (value.get("schema") == s.SCHEMA and
            (value["kind"] != "live" or int(value["run_id"]) <= 30)):
            value.update(mode="full", would_skip_test_files=[])
            path.write_text(json.dumps(value))
    assert s.check(registration, window)["narrowed_case_count"] == 0
    assert "narrowed-cases:0/1" in s.check(registration, window)["unresolved"]


@pytest.mark.parametrize("minimum", [None, 0, -1, True, "1"])
def test_missing_or_invalid_registered_narrowing_minimum_is_unresolved(registration, window, minimum):
    registration["minimum_narrowed_cases"] = minimum
    assert "minimum-narrowed-cases-not-pre-registered" in s.check(registration, window)["unresolved"]


@pytest.mark.parametrize("fields", [
    {"mode": "full", "would_skip_test_files": ["tests/test_other.py"]},
    {"mode": "selected", "would_skip_test_files": ["tests/test_selected.py"]},
    {"mode": None}, {"would_skip_test_files": None},
])
def test_invalid_narrowing_evidence_is_not_counted(registration, window, fields):
    save(window, receipt("999", **fields))
    result = s.check(registration, window)
    assert result["narrowed_red_case_count"] == 30
    assert result["status"] == "unresolved"


def test_in_flight_run_completed_after_registration_enters_window(registration, window):
    census = json.loads((window / "runs.json").read_text())
    census["runs"][0]["created_at"] = "2026-10-06T23:59:00Z"
    save(window, census, "runs.json")
    assert s.check(registration, window)["status"] == "pass"


def test_every_skipped_failure_is_counted(registration, window):
    save(window, receipt("999", full_junit_failing_ids=["tests/test_skip.py::test_a", "tests/test_skip.py::test_b"]))
    result = s.check(registration, window)
    assert result["missed_failure_count"] == 2
    assert result["status"] == "fail"
    assert s.main(["check", "--registration", str(_registration_file(window, registration)),
                   "--registration-sha256", hashlib.sha256(s.canonical_registration_bytes(registration)).hexdigest(), "--receipts", str(window)]) == 1


def _registration_file(root, registration):
    path = root / "registration.input"
    path.write_bytes(s.canonical_registration_bytes(registration))
    return path


def test_pre_registered_base_rerun_exempts_only_identical_id(registration, window):
    save(window, receipt("999", full_junit_failing_ids=["tests/test_skip.py::test_a", "tests/test_skip.py::test_b"]))
    save(window, receipt("base-99", "base", candidate_run_id="999", head_sha="base",
                         full_junit_failing_ids=["tests/test_skip.py::test_a"]), "base.json")
    result = s.check(registration, window)
    assert result["missed_failure_count"] == 1
    assert result["base_exemptions"] == [{"run_id": "999", "test_id": "tests/test_skip.py::test_a"}]
    wrong_rule = copy.deepcopy(registration)
    wrong_rule["base_commit_rerun_rule"] = "after the fact exemption"
    with pytest.raises(ValueError, match="required rules"):
        s.check(wrong_rule, window)


def test_collection_error_outside_selection_counts_even_with_base_failure(registration, window):
    save(window, receipt("999", collection_errors=["tests/test_skip.py"]))
    save(window, receipt("base-99", "base", candidate_run_id="999", head_sha="base",
                         full_junit_failing_ids=["tests/test_skip.py"]), "base.json")
    assert s.check(registration, window)["missed_failure_count"] == 1


@pytest.mark.parametrize("problem", ["missing", "artifactless", "unreproducible"])
def test_unresolved_historical_cases_block_success(registration, window, problem):
    if problem == "missing":
        (window / "999.json").unlink()
    elif problem == "artifactless":
        save(window, receipt("999", junit_hashes={}))
    else:
        save(window, receipt("999", artifact_problems=["cannot-reproduce"]))
    result = s.check(registration, window, now="2026-11-07T00:00:00Z")
    assert result["status"] == "inconclusive"
    assert result["unresolved_count"] == 1
    assert s.main(["check", "--registration", str(_registration_file(window, registration)),
                   "--registration-sha256", hashlib.sha256(s.canonical_registration_bytes(registration)).hexdigest(), "--receipts", str(window)]) == 1


def test_registration_after_live_results_is_refused_but_historical_is_allowed(registration, window):
    save(window, receipt("999", observed_at="2026-10-03T00:00:00Z"))
    assert not s.check(registration, window)["unresolved_count"]
    save(window, receipt("1", "live", observed_at=registration["registered_at"]))
    with pytest.raises(ValueError, match="registration-after-results"):
        s.check(registration, window)


def test_missing_live_census_or_red_denominator_cannot_pass(registration, window):
    (window / "runs.json").unlink()
    result = s.check(registration, window)
    assert result["unresolved_count"] >= 3
    assert result["missed_failure_count"] == 0


def test_oracle_rejects_altered_receipt_and_missing_artifacts(registration, window):
    value = receipt("999", full_junit_failing_ids=["tests/test_skip.py::test_failure"])
    save(window, value)
    value["full_junit_failing_ids"] = []
    (window / "999.json").write_text(json.dumps(value))
    result = s.check(registration, window)
    assert "oracle-unavailable-or-mismatched:999" in result["unresolved"]
    (window / "1/junit/shard.xml").unlink()
    assert "oracle-unavailable-or-mismatched:1" in s.check(registration, window)["unresolved"]


def test_unobserved_injected_fault_is_unresolved(registration, window):
    save(window, receipt("injection-harness", "injected"))
    assert "injection-not-demonstrated:injection-harness" in s.check(registration, window)["unresolved"]


def test_day_30_does_not_accept_late_evidence(registration, window):
    save(window, receipt("1", "live", observed_at="2026-11-07T00:00:00Z"))
    result = s.check(registration, window, now="2026-11-07T00:00:00Z")
    assert result["status"] == "inconclusive"
    assert "receipt-after-day-30:1" in result["unresolved"]


def shard_artifacts(root, directory):
    directory.mkdir()
    (directory / "pytest-shard-1-files.txt").write_text("tests/test_sample.py\n")
    (directory / "pytest-shard-1-needs-artifact.txt").write_text("")
    (directory / "pytest-shard-1.xml").write_text(
        '<testsuites><testsuite><testcase classname="tests.test_sample" name="test_sample" time="2"/>'
        '</testsuite></testsuites>')
    expected = root / pytest_report.EXPECTED_ARTIFACT_SKIPS
    expected.parent.mkdir(parents=True, exist_ok=True)
    expected.write_text("")


def test_full_report_identical_before_and_after_shadow(repo, static_graph, tmp_path, capsys):
    directory = tmp_path / "artifacts"
    shard_artifacts(repo, directory)
    output = tmp_path / "tested-tree.json"
    args = ["--root", str(repo), "--results", str(directory), "--record", str(output)]
    assert pytest_report.main(args) == 0
    original = output.read_bytes(), capsys.readouterr().out
    s.report(argparse.Namespace(root=repo, results=directory, output=tmp_path / "shadow.json", event="pull_request",
             base=git(repo, "rev-parse", "HEAD"), head="HEAD", shards=1, kind="live", run_id="123",
             attempt=1, candidate_run_id="", cost=None))
    assert pytest_report.main(args) == 0
    assert (output.read_bytes(), capsys.readouterr().out) == original
    assert json.loads(output.read_text())["tier"] == "full"


def test_junit_failures_collection_errors_and_missing_shards(repo, tmp_path):
    directory = tmp_path / "artifacts"
    shard_artifacts(repo, directory)
    (directory / "pytest-shard-1.xml").write_text(
        '<testsuites><testsuite><testcase classname="tests.test_sample" name="test_a"><failure/></testcase>'
        '<testcase classname="tests.test_sample" name="test_b"><failure/></testcase>'
        '<testcase name="tests.test_broken"><error message="collection failure"/></testcase>'
        '</testsuite></testsuites>')
    result = s.read_full_results(directory, repo, 1)
    assert result["artifact_problems"] == []
    assert result["full_junit_failing_ids"] == ["tests/test_broken.py", "tests/test_sample.py::test_a", "tests/test_sample.py::test_b"]
    assert result["collection_errors"] == ["tests/test_broken.py"]
    assert result["executed_test_ids"] == ["tests/test_sample.py::test_a", "tests/test_sample.py::test_b"]
    assert "missing-or-duplicate-junit-shards" in s.read_full_results(directory, repo, 2)["artifact_problems"]


def test_junit_duplicate_failure_followed_by_pass_is_retained(repo, tmp_path):
    directory = tmp_path / "artifacts"
    shard_artifacts(repo, directory)
    (directory / "pytest-shard-1.xml").write_text(
        '<testsuites><testsuite><testcase classname="tests.test_sample" name="test_a"><failure/></testcase>'
        '<testcase classname="tests.test_sample" name="test_a"/></testsuite></testsuites>')
    result = s.read_full_results(directory, repo, 1)
    assert result["artifact_problems"] == []
    assert result["full_junit_failing_ids"] == ["tests/test_sample.py::test_a"]


def test_report_unavailable_evidence_is_zero_exit_and_unresolved(repo, static_graph, tmp_path):
    output = tmp_path / "shadow.json"
    assert s.main(["report", "--root", str(repo), "--results", str(tmp_path / "missing"), "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result["artifact_problems"]
    census = result["review_unresolved_edge_census"]
    assert census["total"] == sum(census["by_kind"].values()) == 14692
    assert census["head_sha"] == "c3695226db3b18ec0e3ab42c9a7a3221e00df69c"
    assert result["projected_cost_after_lost_reuse"]["unknown_reason"] == "matched-pr-queue-cost-inputs-not-supplied"


def test_report_records_explicit_unknown_cost_reason(repo, static_graph, tmp_path):
    output = tmp_path / "shadow.json"
    assert s.main(["report", "--root", str(repo), "--results", str(tmp_path / "missing"),
                   "--cost-unknown-reason", "matched-measurements-unavailable", "--output", str(output)]) == 0
    cost = json.loads(output.read_text())["projected_cost_after_lost_reuse"]
    assert cost["status"] == "unknown"
    assert cost["unknown_reason"] == "matched-measurements-unavailable"


def test_register_binds_historical_ids_hashes_rules_and_stop(repo, static_graph):
    baseline = {"complete": True, "created_window": s.BASELINE, "runs": [
        {"run_id": "42", "event": "pull_request", "pytest_red": True},
        {"run_id": "43", "event": "merge_group", "pytest_red": True},
        {"run_id": "44", "event": "pull_request", "pytest_red": False}]}
    result = s.register(baseline, repo, minimum_narrowed_cases=30)
    assert result["historical_run_ids"] == ["42", "43"]
    assert set(result["identities"]["tool_hashes"]) == set(s.TOOLS)
    assert s.instant(result["stop_at"]) - s.instant(result["registered_at"]) == s.timedelta(days=30)
    assert result["injections_frozen"] is False
    assert result["minimum_narrowed_cases"] == 30
    assert s.register(baseline, repo, minimum_narrowed_cases=44)["minimum_narrowed_cases"] == 44
    with pytest.raises(ValueError, match="positive integer"):
        s.register(baseline, repo, minimum_narrowed_cases=0)
    with pytest.raises(ValueError, match="complete baseline"):
        s.register({**baseline, "complete": False}, repo, minimum_narrowed_cases=30)


def test_registration_cli_refuses_overwrite(repo, static_graph, tmp_path, capsys, registration):
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"complete": True, "created_window": s.BASELINE, "runs": [
        {"run_id": "42", "event": "pull_request", "pytest_red": True}]}))
    output = tmp_path / "registration.json"
    controls = tmp_path / "controls.json"
    controls.write_text(json.dumps(registration["injected_cases"]))
    args = ["register", "--root", str(repo), "--baseline", str(baseline), "--output", str(output),
            "--minimum-narrowed-cases", "44", "--injections", str(controls)]
    assert s.main(args) == 0
    printed = json.loads(capsys.readouterr().out)
    assert json.loads(output.read_text())["minimum_narrowed_cases"] == 44
    before = output.read_bytes()
    assert before == s.canonical_registration_bytes(json.loads(before))
    assert printed["registration_sha256"] == hashlib.sha256(before).hexdigest()
    assert printed["injections_frozen"] is True
    assert len(printed["injected_cases"]) == len(registration["injected_cases"])
    assert all(case["registered_at"] == printed["registered_at"] for case in printed["injected_cases"])
    assert printed["injected_cases"][0]["expected_failure_ids"] == registration["injected_cases"][0]["expected_failure_ids"]
    assert s.main(args) == 2
    assert output.read_bytes() == before


def test_register_cli_requires_minimum(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        s.main(["register", "--baseline", str(tmp_path / "baseline.json"),
                "--output", str(tmp_path / "registration.json")])
    assert error.value.code == 2
    assert "--minimum-narrowed-cases" in capsys.readouterr().err


@pytest.mark.parametrize("minimum", [0, -1])
def test_register_cli_refuses_non_positive_minimum(tmp_path, capsys, minimum):
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"complete": True, "created_window": s.BASELINE}))
    output = tmp_path / "registration.json"
    assert s.main(["register", "--baseline", str(baseline), "--output", str(output),
                   "--minimum-narrowed-cases", str(minimum)]) == 2
    assert json.loads(capsys.readouterr().out)["error"] == "minimum narrowed cases must be a positive integer"
    assert not output.exists()


def test_canonical_registration_bytes_and_digest(tmp_path):
    value = {"z": "caf\u00e9", "a": {"y": 2, "b": 1}}
    expected = b'{"a":{"b":1,"y":2},"z":"caf\xc3\xa9"}\n'
    path = tmp_path / "registration.json"
    assert s.canonical_registration_bytes(value) == expected
    sha256 = s.write_registration(path, value)
    assert path.read_bytes() == expected
    assert sha256 == hashlib.sha256(expected).hexdigest()
    assert s.verified_registration(path, sha256.upper()) == value


def test_check_cli_accepts_published_registration(registration, window, capsys):
    path = window / "registration.json"
    sha256 = s.write_registration(path, registration)
    assert s.main(["check", "--registration", str(path), "--registration-sha256", sha256,
                   "--receipts", str(window)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "pass"


@pytest.mark.parametrize("supplied, reason", [
    (None, "registration-sha256-required"),
    ("0" * 64, "registration-sha256-mismatch"),
    ("not-hex", "registration-sha256-invalid"),
    ("g" * 64, "registration-sha256-invalid"),
])
def test_check_cli_refuses_missing_wrong_or_invalid_hash(tmp_path, registration, monkeypatch, capsys, supplied, reason):
    path = tmp_path / "registration.json"
    s.write_registration(path, registration)
    monkeypatch.setattr(s, "check", lambda *args: pytest.fail("unverified registration reached scorer"))
    args = ["check", "--registration", str(path), "--receipts", str(tmp_path)]
    if supplied is not None:
        args += ["--registration-sha256", supplied]
    assert s.main(args) == 2
    assert json.loads(capsys.readouterr().out) == {"status": "unresolved", "error": reason}


@pytest.mark.parametrize("mutation, reason", [
    ("minimum", "registration-sha256-mismatch"),
    ("controls", "registration-sha256-mismatch"),
    ("whitespace", "registration-not-canonical"),
    ("missing-newline", "registration-not-canonical"),
    ("duplicate-key", "registration-not-canonical"),
    ("invalid-json", "registration-invalid-json"),
    ("not-object", "registration-invalid-json"),
])
def test_check_cli_refuses_modified_registration(tmp_path, registration, monkeypatch, capsys, mutation, reason):
    path = tmp_path / "registration.json"
    sha256 = s.write_registration(path, registration)
    if mutation in {"minimum", "controls"}:
        if mutation == "minimum":
            registration["minimum_narrowed_cases"] += 1
        else:
            registration["injected_cases"][0]["expected_failure_ids"] = ["tests/test_other.py::test_fault"]
        path.write_bytes(s.canonical_registration_bytes(registration))
    else:
        raw = path.read_bytes()
        path.write_bytes({
            "whitespace": b" " + raw,
            "missing-newline": raw.rstrip(b"\n"),
            "duplicate-key": b'{"schema":"modified",' + raw[1:],
            "invalid-json": b"{",
            "not-object": b"[]\n",
        }[mutation])
    monkeypatch.setattr(s, "check", lambda *args: pytest.fail("modified registration reached scorer"))
    assert s.main(["check", "--registration", str(path), "--registration-sha256", sha256,
                   "--receipts", str(tmp_path)]) == 2
    assert json.loads(capsys.readouterr().out) == {"status": "unresolved", "error": reason}


def test_gh_pages_refuses_incomplete_census(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(
        [], 0, stdout=json.dumps([{"total_count": 2, "jobs": [{"id": 1}]}])))
    with pytest.raises(ValueError, match="incomplete GitHub census"):
        s.gh_pages("endpoint", "jobs")


def test_live_inventory_uses_first_attempt_even_after_rerun(monkeypatch):
    run = {"id": 42, "event": "pull_request", "status": "completed", "conclusion": "success",
           "run_attempt": 2, "created_at": "2026-10-08T00:00:00Z", "updated_at": "2026-10-09T00:00:00Z", "head_sha": "head"}
    called = []

    def pages(endpoint, key):
        called.append(endpoint)
        return [run] if key == "workflow_runs" else [{"name": "pytest (1)", "conclusion": "failure",
                                                     "completed_at": "2026-10-08T01:00:00Z"}]

    monkeypatch.setattr(s, "gh_pages", pages)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(
        [], 0, stdout=json.dumps({**run, "run_attempt": 1, "conclusion": "failure"})))
    result = s.inventory("owner/repo", "start..stop", first_attempts=True)
    assert result["first_attempts"] is True
    assert result["runs"][0]["run_attempt"] == 1
    assert result["runs"][0]["pytest_red"] is True
    assert called[-1].endswith("/attempts/1/jobs?per_page=100")


@pytest.mark.parametrize("mode,expected_saved,expected_candidate", [("selected", 80, 95), ("full", -10, 185)])
def test_cost_preserves_queue_reuse_and_includes_every_overhead(mode, expected_saved, expected_candidate):
    selection = {"mode": mode, "selected_test_files": ["tests/test_a.py"]}
    evidence = {"test_seconds_by_file": {"tests/test_a.py": 10, "tests/test_b.py": 90}}
    cost = {"full_pr_runner_minutes": 100, "full_queue_runner_minutes": 100, "reuse_probability": .25,
            "reporter_runner_minutes": 1, "rerun_runner_minutes": 2, "ejection_runner_minutes": 3,
            "duplicated_preparation_runner_minutes": 4, "elapsed_wait_minutes": 5}
    result = s.projected_cost(selection, evidence, cost)
    assert result["lost_reuse_runner_minutes"] == 0
    assert result["baseline_pr_plus_queue_runner_minutes"] == 175
    assert result["candidate_pr_plus_queue_runner_minutes"] == expected_candidate
    assert result["net_runner_minutes_saved"] == expected_saved
    assert result["elapsed_wait_minutes"] == 5
    assert s.projected_cost(selection, evidence, None)["status"] == "unknown"
    assert s.projected_cost(selection, evidence, {})["unknown_reason"] == "incomplete-cost-inputs-or-test-duration-evidence"
