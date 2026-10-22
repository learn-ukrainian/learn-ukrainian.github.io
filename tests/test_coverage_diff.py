"""Coverage losses must not be hidden by gains, missing files or invalid reports."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ci.coverage_diff import main


@pytest.fixture
def reports(tmp_path):
    def write(name, files):
        directory = tmp_path / name
        directory.mkdir()
        path = directory / "coverage.json"
        path.write_text(json.dumps({"meta": {"branch_coverage": True}, "files": files}))
        (directory / "manifest.json").write_text(json.dumps({"complete": True}))
        return str(path)

    return write


def measured(lines, arcs):
    return {"executed_lines": lines, "executed_branches": arcs}


def test_gains_cannot_offset_lost_identities(reports, capsys):
    before = reports("before.json", {"scripts/a.py": measured([1, 2], [[1, 2], [2, -1]])})
    after = reports("after.json", {"scripts/a.py": measured([1, 3, 4], [[1, 3], [3, 4], [4, -1]])})
    assert main([before, after]) == 1
    assert json.loads(capsys.readouterr().out) == {
        "files_with_losses": [
            {
                "file": "scripts/a.py",
                "lost_lines": [2],
                "lost_arcs": [[1, 2], [2, -1]],
                "line_count": 1,
                "arc_count": 2,
            }
        ]
    }


@pytest.mark.parametrize("source", ["scripts", ".mcp", "agents_extensions", "packages"])
def test_disappeared_production_file_loses_every_identity(reports, capsys, source):
    name = f"{source}/gone.py"
    before = reports("before.json", {name: measured([1], [[-1, 1], [1, -1]])})
    after = reports("after.json", {"scripts/new.py": measured([1], [])})
    assert main([before, after]) == 1
    loss = json.loads(capsys.readouterr().out)["files_with_losses"][0]
    assert loss == {"file": name, "lost_lines": [1], "lost_arcs": [[-1, 1], [1, -1]], "line_count": 1, "arc_count": 2}


def test_gains_and_ordering_changes_do_not_report_losses(reports, capsys):
    before = reports("before.json", {"scripts/a.py": measured([2, 1], [[2, -1], [1, 2]])})
    after = reports("after.json", {"scripts/a.py": measured([1, 2, 3], [[1, 2], [2, -1], [2, 3]])})
    assert main([before, after]) == 0
    assert json.loads(capsys.readouterr().out) == {"files_with_losses": []}


def test_unconditional_arc_loss_is_visible_in_enriched_reports(reports, capsys):
    old = measured([1, 2], []) | {"executed_arcs": [[-1, 1], [1, 2], [2, -1]]}
    new = measured([1, 2], []) | {"executed_arcs": [[-1, 1], [2, -1]]}
    assert main([reports("old", {"scripts/a.py": old}), reports("new", {"scripts/a.py": new})]) == 1
    loss = json.loads(capsys.readouterr().out)["files_with_losses"][0]
    assert loss["lost_lines"] == []
    assert loss["lost_arcs"] == [[1, 2]]


@pytest.mark.parametrize(
    "contents",
    [
        "not json",
        "null",
        "[]",
        '{"meta": {"branch_coverage": false}, "files": {}}',
        '{"meta": {"branch_coverage": true}, "files": {}}',
    ],
)
def test_malformed_or_empty_reports_fail_closed(tmp_path, reports, contents, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text(contents)
    (tmp_path / "manifest.json").write_text(json.dumps({"complete": True}))
    valid = reports("valid.json", {"scripts/a.py": measured([1], [])})
    assert main([str(bad), valid]) == 2
    assert "coverage_diff:" in capsys.readouterr().err


@pytest.mark.parametrize(
    "name,data",
    [
        ("/host/scripts/a.py", measured([1], [])),
        ("scripts/../a.py", measured([1], [])),
        ("tests/a.py", measured([1], [])),
        ("scripts/a.py", measured([True], [])),
        ("scripts/a.py", measured([1], [[1]])),
        ("scripts/a.py", {"executed_lines": [1]}),
    ],
)
def test_invalid_identities_are_errors(reports, name, data):
    bad = reports("bad", {name: data})
    assert main([bad, bad]) == 2


def test_different_arc_formats_cannot_silently_compare(reports):
    plain = measured([1], [])
    enriched = plain | {"executed_arcs": [[-1, 1]]}
    assert main([reports("old", {"scripts/a.py": enriched}), reports("new", {"scripts/a.py": plain})]) == 2


def test_missing_input_is_an_error(tmp_path):
    assert main([str(tmp_path / "absent"), str(tmp_path / "absent")]) == 2


@pytest.mark.parametrize("side", ["baseline", "candidate"])
@pytest.mark.parametrize("contents", [None, "not json", "null", "[]", "{}", '{"complete": false}', '{"complete": 1}'])
def test_incomplete_or_missing_manifest_cannot_approve_a_prune(reports, side, contents, capsys):
    """A partial baseline can hide losses even when its branch report is nonempty."""
    paths = {name: reports(name, {"scripts/a.py": measured([1], [])}) for name in ("baseline", "candidate")}
    manifest = Path(paths[side]).with_name("manifest.json")
    if contents is None:
        manifest.unlink()
    else:
        manifest.write_text(contents)
    assert main([paths["baseline"], paths["candidate"]]) == 2
    result = capsys.readouterr()
    assert result.out == ""
    assert str(manifest) in result.err
    assert "complete: true" in result.err


def test_help_explains_usage_output_and_status(capsys):
    with pytest.raises(SystemExit, match="0"):
        main(["--help"])
    help_text = capsys.readouterr().out
    assert all(word in help_text for word in ("Examples:", "Outputs:", "Exit codes:", "Related:", "manifest"))


@pytest.fixture
def context_data(tmp_path):
    import coverage

    def write(arcs_by_context):
        path = tmp_path / "baseline" / ".coverage"
        path.parent.mkdir(exist_ok=True)
        data = coverage.CoverageData(basename=str(path))
        for context, arcs in arcs_by_context.items():
            data.set_context(context)
            data.add_arcs({"scripts/a.py": arcs})
        data.write()
        return path

    return write


def test_lost_identities_name_covering_tests_and_a_restore_set(reports, context_data, tmp_path, capsys):
    before = reports("before.json", {"scripts/a.py": measured([1, 2, 3], [[-1, 1], [1, 2], [2, 3], [3, -1]])})
    after = reports("after.json", {"scripts/a.py": measured([1], [[-1, 1], [1, -1]])})
    data = context_data(
        {
            "tests/test_old.py::test_one": [(-1, 1), (1, 2), (2, 3), (3, -1)],
            "tests/test_old.py::test_two": [(-1, 1), (1, 3), (3, -1)],
            "tests/test_keep.py::test_keep": [(-1, 1), (1, 2)],
        }
    )
    deleted = tmp_path / "deleted.txt"
    deleted.write_text("tests/test_old.py::test_one\ntests/test_old.py::test_two\n")
    candidate = tmp_path / "candidate"
    (candidate / "scripts").mkdir(parents=True)
    (candidate / "scripts/a.py").write_text("value = 1\n")

    assert (
        main(
            [
                before,
                after,
                "--baseline-data",
                str(data),
                "--deleted-test-nodes",
                str(deleted),
                "--candidate-root",
                str(candidate),
            ]
        )
        == 1
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["lost_identities"] == [
        {"file": "scripts/a.py", "line": 2, "tests": ["tests/test_keep.py::test_keep", "tests/test_old.py::test_one"]},
        {
            "file": "scripts/a.py",
            "line": 3,
            "tests": ["tests/test_old.py::test_one", "tests/test_old.py::test_two"],
        },
        {
            "file": "scripts/a.py",
            "arc": [1, 2],
            "tests": ["tests/test_keep.py::test_keep", "tests/test_old.py::test_one"],
        },
        {"file": "scripts/a.py", "arc": [2, 3], "tests": ["tests/test_old.py::test_one"]},
        {
            "file": "scripts/a.py",
            "arc": [3, -1],
            "tests": ["tests/test_old.py::test_one", "tests/test_old.py::test_two"],
        },
    ]
    assert payload["deleted_test_nodes"] == ["tests/test_old.py::test_one", "tests/test_old.py::test_two"]
    assert payload["dead_files"] == []
    assert payload["candidate_tests"] == ["tests/test_old.py::test_one", "tests/test_old.py::test_two"]
    # test_one alone covers every lost identity, so the redundant test_two stays deleted.
    assert payload["restore_set"] == ["tests/test_old.py::test_one"]
    assert payload["restore_coverage"] == {
        "tests/test_old.py::test_one": [
            "scripts/a.py:2",
            "scripts/a.py:3",
            "scripts/a.py:1->2",
            "scripts/a.py:2->3",
            "scripts/a.py:3->-1",
        ],
    }
    assert payload["unrestorable_identities"] == []


def test_dead_production_file_does_not_require_restoring_its_tests(reports, context_data, tmp_path, capsys):
    before = reports("before.json", {"scripts/gone.py": measured([1, 2], [[-1, 1], [1, 2], [2, -1]])})
    after = reports("after.json", {"scripts/a.py": measured([1], [[-1, 1], [1, -1]])})
    data = context_data({"tests/test_gone.py::test_one": [(-1, 1), (1, 2), (2, -1)]})
    deleted = tmp_path / "deleted.txt"
    deleted.write_text("tests/test_gone.py::test_one\n")

    assert (
        main(
            [
                before,
                after,
                "--baseline-data",
                str(data),
                "--deleted-test-nodes",
                str(deleted),
                "--candidate-root",
                str(tmp_path),
            ]
        )
        == 1
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["dead_files"] == ["scripts/gone.py"]
    assert payload["candidate_tests"] == []
    assert payload["restore_set"] == []
    assert payload["restore_coverage"] == {}
    assert payload["unrestorable_identities"] == []


def test_baseline_without_test_contexts_is_invalid(reports, tmp_path, capsys):
    import coverage

    before = reports("before.json", {"scripts/a.py": measured([1, 2], [[-1, 1], [1, 2], [2, -1]])})
    after = reports("after.json", {"scripts/a.py": measured([1], [[-1, 1], [1, -1]])})
    (tmp_path / "plain").mkdir()
    data = coverage.CoverageData(basename=str(tmp_path / "plain/.coverage"))
    data.add_arcs({"scripts/a.py": [(-1, 1), (1, 2), (2, -1)]})
    data.write()
    result = main([before, after, "--baseline-data", str(tmp_path / "plain/.coverage")])
    assert result == 2
    assert "expected per-test contexts" in capsys.readouterr().err


def test_deleted_nodes_require_baseline_context_data(reports):
    before = reports("before.json", {"scripts/a.py": measured([1], [[-1, 1], [1, -1]])})
    after = reports("after.json", {"scripts/a.py": measured([1], [[-1, 1], [1, -1]])})
    assert main([before, after, "--deleted-test-nodes", "missing.txt"]) == 2


def test_git_range_derives_deleted_test_node_ids(reports, context_data, tmp_path, capsys):
    import subprocess

    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    (repo / "tests/test_old.py").write_text("def test_one():\n    pass\n")
    (repo / "tests/test_keep.py").write_text("def test_keep():\n    pass\n")
    git = ["git", "-C", str(repo), "-c", "user.name=Coverage test", "-c", "user.email=coverage@example.invalid"]
    subprocess.run(["git", "init", "-q", str(repo)], check=True, timeout=30)
    subprocess.run([*git, "add", "."], check=True, timeout=30)
    subprocess.run([*git, "commit", "-q", "-m", "base"], check=True, timeout=30)
    base = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True, timeout=30).strip()
    (repo / "tests/test_old.py").unlink()
    subprocess.run([*git, "commit", "-q", "-am", "delete"], check=True, timeout=30)
    head = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True, timeout=30).strip()

    before = reports("before.json", {"scripts/a.py": measured([1, 2], [[-1, 1], [1, 2], [2, -1]])})
    after = reports("after.json", {"scripts/a.py": measured([1], [[-1, 1], [1, -1]])})
    data = context_data(
        {
            "tests/test_old.py::test_one": [(-1, 1), (1, 2), (2, -1)],
            "tests/test_keep.py::test_keep": [(-1, 1), (1, 2)],
        }
    )
    candidate = tmp_path / "candidate"
    (candidate / "scripts").mkdir(parents=True)
    (candidate / "scripts/a.py").write_text("value = 1\n")
    assert (
        main(
            [
                before,
                after,
                "--baseline-data",
                str(data),
                "--git-range",
                f"{base}..{head}",
                "--git-repo",
                str(repo),
                "--candidate-root",
                str(candidate),
            ]
        )
        == 1
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["deleted_test_nodes"] == ["tests/test_old.py::test_one"]
    assert payload["restore_set"] == ["tests/test_old.py::test_one"]


def test_git_range_matches_non_ascii_deleted_and_renamed_test_paths(reports, context_data, tmp_path, capsys):
    """Git quotes such paths by default; NUL-delimited output must match them exactly."""
    import subprocess

    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    (repo / "tests/test_старий.py").write_text("def test_deleted():\n    pass\n")
    (repo / "tests/test_новий.py").write_text("def test_renamed():\n    pass\n")
    git = ["git", "-C", str(repo), "-c", "user.name=Coverage test", "-c", "user.email=coverage@example.invalid"]
    subprocess.run(["git", "init", "-q", str(repo)], check=True, timeout=30)
    subprocess.run([*git, "add", "."], check=True, timeout=30)
    subprocess.run([*git, "commit", "-q", "-m", "base"], check=True, timeout=30)
    base = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True, timeout=30).strip()
    (repo / "tests/test_старий.py").unlink()
    (repo / "tests/test_новий.py").rename(repo / "tests/test_новий_renamed.py")
    subprocess.run([*git, "add", "-A"], check=True, timeout=30)
    subprocess.run([*git, "commit", "-q", "-m", "delete and rename"], check=True, timeout=30)
    head = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True, timeout=30).strip()

    before = reports("before.json", {"scripts/a.py": measured([1, 2, 3], [[-1, 1], [1, 2], [2, -1], [1, 3], [3, -1]])})
    after = reports("after.json", {"scripts/a.py": measured([1], [[-1, 1], [1, -1]])})
    data = context_data(
        {
            "tests/test_старий.py::test_deleted": [(-1, 1), (1, 2), (2, -1)],
            "tests/test_новий.py::test_renamed": [(-1, 1), (1, 3), (3, -1)],
        }
    )
    candidate = tmp_path / "candidate"
    (candidate / "scripts").mkdir(parents=True)
    (candidate / "scripts/a.py").write_text("value = 1\n")
    assert (
        main(
            [
                before,
                after,
                "--baseline-data",
                str(data),
                "--git-range",
                f"{base}..{head}",
                "--git-repo",
                str(repo),
                "--candidate-root",
                str(candidate),
            ]
        )
        == 1
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["deleted_test_nodes"] == [
        "tests/test_новий.py::test_renamed",
        "tests/test_старий.py::test_deleted",
    ]
    assert payload["restore_set"] == [
        "tests/test_новий.py::test_renamed",
        "tests/test_старий.py::test_deleted",
    ]


def test_pytest_cov_phases_reduce_to_one_test_node_id(reports, context_data, tmp_path, capsys):
    """--cov-context=test records nodeid|run; restore sets must still name the test once."""
    before = reports("before.json", {"scripts/a.py": measured([1, 2], [[-1, 1], [1, 2], [2, -1]])})
    after = reports("after.json", {"scripts/a.py": measured([1], [[-1, 1], [1, -1]])})
    data = context_data(
        {
            "tests/test_old.py::test_one|setup": [(-1, 1)],
            "tests/test_old.py::test_one|run": [(1, 2), (2, -1)],
            "tests/test_old.py::test_one|teardown": [],
        }
    )
    deleted = tmp_path / "deleted.txt"
    deleted.write_text("tests/test_old.py::test_one\n")
    candidate = tmp_path / "candidate"
    (candidate / "scripts").mkdir(parents=True)
    (candidate / "scripts/a.py").write_text("value = 1\n")

    assert (
        main(
            [
                before,
                after,
                "--baseline-data",
                str(data),
                "--deleted-test-nodes",
                str(deleted),
                "--candidate-root",
                str(candidate),
            ]
        )
        == 1
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["lost_identities"][0]["tests"] == ["tests/test_old.py::test_one"]
    assert payload["restore_set"] == ["tests/test_old.py::test_one"]


def test_subprocess_only_lines_are_reported_as_unattributed(reports, tmp_path, capsys):
    """Coverage's subprocess patch carries no test context; do not invent one."""
    import coverage

    before = reports("before.json", {"scripts/a.py": measured([1, 2, 3], [[-1, 1], [1, 2], [2, 3], [3, -1]])})
    after = reports("after.json", {"scripts/a.py": measured([1], [[-1, 1], [1, -1]])})
    path = tmp_path / "baseline/.coverage"
    path.parent.mkdir()
    data = coverage.CoverageData(basename=str(path))
    data.set_context("tests/test_old.py::test_one|run")
    data.add_arcs({"scripts/a.py": [(-1, 1), (1, 2)]})
    data.set_context("")
    data.add_arcs({"scripts/a.py": [(1, 3), (3, -1)]})
    data.write()
    deleted = tmp_path / "deleted.txt"
    deleted.write_text("tests/test_old.py::test_one\n")
    candidate = tmp_path / "candidate"
    (candidate / "scripts").mkdir(parents=True)
    (candidate / "scripts/a.py").write_text("value = 1\n")

    assert (
        main(
            [
                before,
                after,
                "--baseline-data",
                str(path),
                "--deleted-test-nodes",
                str(deleted),
                "--candidate-root",
                str(candidate),
            ]
        )
        == 1
    )
    payload = json.loads(capsys.readouterr().out)
    assert {"file": "scripts/a.py", "line": 3} in payload["unattributed_lost_identities"]
    assert {"file": "scripts/a.py", "arc": [2, 3]} in payload["unattributed_lost_identities"]
    assert {"file": "scripts/a.py", "arc": [3, -1]} in payload["unattributed_lost_identities"]
    assert payload["restore_set"] == ["tests/test_old.py::test_one"]


def restore_payload(reports, context_data, tmp_path, capsys, arcs_by_context, deleted_nodes, before_arcs, after_arcs):
    """Run main with per-test contexts for scripts/a.py and return its JSON payload."""
    before_lines = sorted({line for arc in before_arcs for line in arc if line > 0})
    after_lines = sorted({line for arc in after_arcs for line in arc if line > 0})
    before = reports("before.json", {"scripts/a.py": measured(before_lines, before_arcs)})
    after = reports("after.json", {"scripts/a.py": measured(after_lines, after_arcs)})
    data = context_data(arcs_by_context)
    deleted = tmp_path / "deleted.txt"
    deleted.write_text("".join(f"{node}\n" for node in deleted_nodes))
    candidate = tmp_path / "candidate"
    (candidate / "scripts").mkdir(parents=True)
    (candidate / "scripts/a.py").write_text("value = 1\n")
    args = [before, after, "--baseline-data", str(data), "--deleted-test-nodes", str(deleted)]
    assert main([*args, "--candidate-root", str(candidate)]) == 1
    return json.loads(capsys.readouterr().out)


def test_restore_set_drops_tests_whose_identities_another_choice_covers(reports, context_data, tmp_path, capsys):
    """A full candidate list as the restore set would reverse valid pruning of redundant tests."""
    payload = restore_payload(
        reports,
        context_data,
        tmp_path,
        capsys,
        {
            "tests/test_old.py::test_a": [(-1, 1), (1, 2), (2, -1)],
            "tests/test_old.py::test_b": [(-1, 1), (1, 3), (3, -1)],
            "tests/test_old.py::test_wide": [(-1, 1), (1, 2), (2, -1), (1, 3), (3, -1)],
        },
        ["tests/test_old.py::test_a", "tests/test_old.py::test_b", "tests/test_old.py::test_wide"],
        [[-1, 1], [1, 2], [2, -1], [1, 3], [3, -1]],
        [[-1, 1], [1, -1]],
    )
    assert payload["candidate_tests"] == [
        "tests/test_old.py::test_a",
        "tests/test_old.py::test_b",
        "tests/test_old.py::test_wide",
    ]
    assert payload["restore_set"] == ["tests/test_old.py::test_wide"]
    assert payload["restore_coverage"] == {
        "tests/test_old.py::test_wide": [
            "scripts/a.py:2",
            "scripts/a.py:3",
            "scripts/a.py:1->2",
            "scripts/a.py:1->3",
            "scripts/a.py:2->-1",
            "scripts/a.py:3->-1",
        ]
    }


def test_restore_set_breaks_equal_gains_by_test_id(reports, context_data, tmp_path, capsys):
    """Equal coverage must not make the restore set depend on dict or sqlite order."""
    payload = restore_payload(
        reports,
        context_data,
        tmp_path,
        capsys,
        {
            "tests/test_old.py::test_b": [(-1, 1), (1, 2), (2, -1)],
            "tests/test_old.py::test_a": [(-1, 1), (1, 2), (2, -1)],
        },
        ["tests/test_old.py::test_b", "tests/test_old.py::test_a"],
        [[-1, 1], [1, 2], [2, -1]],
        [[-1, 1], [1, -1]],
    )
    assert payload["candidate_tests"] == ["tests/test_old.py::test_a", "tests/test_old.py::test_b"]
    assert payload["restore_set"] == ["tests/test_old.py::test_a"]
    assert payload["restore_coverage"] == {
        "tests/test_old.py::test_a": ["scripts/a.py:2", "scripts/a.py:1->2", "scripts/a.py:2->-1"]
    }


def test_identity_no_deleted_test_covers_is_reported_unrestorable(reports, context_data, tmp_path, capsys):
    """Restoring deleted tests cannot recover a loss only a kept test covered; say so."""
    payload = restore_payload(
        reports,
        context_data,
        tmp_path,
        capsys,
        {
            "tests/test_old.py::test_one": [(-1, 1), (1, 2), (2, -1)],
            "tests/test_keep.py::test_keep": [(-1, 1), (1, 3), (3, -1)],
        },
        ["tests/test_old.py::test_one"],
        [[-1, 1], [1, 2], [2, -1], [1, 3], [3, -1]],
        [[-1, 1], [1, -1]],
    )
    assert payload["restore_set"] == ["tests/test_old.py::test_one"]
    assert payload["unrestorable_identities"] == [
        {"file": "scripts/a.py", "line": 3, "tests": ["tests/test_keep.py::test_keep"]},
        {"file": "scripts/a.py", "arc": [1, 3], "tests": ["tests/test_keep.py::test_keep"]},
        {"file": "scripts/a.py", "arc": [3, -1], "tests": ["tests/test_keep.py::test_keep"]},
    ]


def test_git_timeout_is_invalid_input_not_a_traceback(reports, context_data, monkeypatch, capsys):
    import subprocess

    def hang(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs.get("timeout"))

    monkeypatch.setattr(subprocess, "check_output", hang)
    before = reports("before.json", {"scripts/a.py": measured([1, 2], [[-1, 1], [1, 2], [2, -1]])})
    after = reports("after.json", {"scripts/a.py": measured([1], [[-1, 1], [1, -1]])})
    data = context_data({"tests/test_old.py::test_one": [(-1, 1), (1, 2), (2, -1)]})
    assert main([before, after, "--baseline-data", str(data), "--git-range", "a..b"]) == 2
    assert "cannot diff a..b" in capsys.readouterr().err
