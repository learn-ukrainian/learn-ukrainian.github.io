"""Coverage losses must not be hidden by gains, missing files or invalid reports."""

from __future__ import annotations

import json

import pytest

from scripts.ci.coverage_diff import main


@pytest.fixture
def reports(tmp_path):
    def write(name, files):
        path = tmp_path / name
        path.write_text(json.dumps({"meta": {"branch_coverage": True}, "files": files}))
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


def test_help_explains_usage_output_and_status(capsys):
    with pytest.raises(SystemExit, match="0"):
        main(["--help"])
    help_text = capsys.readouterr().out
    assert all(word in help_text for word in ("Examples:", "Outputs:", "Exit codes:", "Related:", "manifest"))
