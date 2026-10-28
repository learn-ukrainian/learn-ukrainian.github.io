"""Behaviour of the structural scanner on published activity layouts."""

from pathlib import Path

import pytest

from scripts.audit import scan_activity_errors as scanner


@pytest.fixture
def curriculum(tmp_path, monkeypatch):
    monkeypatch.setattr(scanner, "PROJECT_ROOT", tmp_path)
    root = tmp_path / "curriculum" / "l2-uk-en"
    monkeypatch.setattr(scanner, "CURRICULUM_ROOT", root)
    return root


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.mark.parametrize("relative", ["a1-v1/finale/activities.yaml", "a2/activities/finale.yaml"])
def test_scan_track_finds_broken_answer_in_each_layout(curriculum, relative):
    _write(curriculum / relative, """
inline:
  - type: fill-in
    title: Missing answer
    items:
      - sentence: 'Choose ___.'
        answer: absent
        options: [first, second]
""")

    violations = scanner.scan_track(relative.split("/")[0])

    assert [v["type"] for v in violations] == ["FILL_IN_ANSWER_NOT_IN_OPTIONS"]
    assert violations[0]["file"] == f"curriculum/l2-uk-en/{relative}"


def test_scan_track_supports_flat_activity_lists(curriculum):
    _write(curriculum / "a1-v1/first/activities.yaml", """
- type: fill-in
  title: Missing blank
  items:
    - sentence: 'There is no blank.'
      answer: first
      options: [first, second]
""")

    assert [v["type"] for v in scanner.scan_track("a1-v1")] == ["FILL_IN_MISSING_BLANK"]


def test_scan_track_reports_parse_failure_alongside_other_files(curriculum):
    _write(curriculum / "a1-v1/bad/activities.yaml", "inline: [")
    _write(curriculum / "a1-v1/valid/activities.yaml", "[]")

    assert [v["type"] for v in scanner.scan_track("a1-v1")] == ["PARSE_ERROR"]


def test_cli_counts_both_layouts_and_excludes_unrelated_yaml(curriculum, monkeypatch, capsys):
    _write(curriculum / "a1-v1/activities/legacy.yaml", "[]")
    _write(curriculum / "a1-v1/first/activities.yaml", "[]")
    _write(curriculum / "a1-v1/first/resources.yaml", "not activity data")
    _write(curriculum / "a1-v1/discovery/first.yaml", "not activity data")
    monkeypatch.setattr("sys.argv", ["scan_activity_errors", "--track", "a1-v1"])

    assert scanner.main() == 0
    output = capsys.readouterr().out
    assert "Scanned 2 activity file(s) across 1 track(s)." in output
    assert "do not verify Ukrainian answer ambiguity or option validity" in output


@pytest.mark.parametrize("existing", [False, True])
def test_cli_fails_when_no_files_were_checked(curriculum, monkeypatch, capsys, existing):
    if existing:
        (curriculum / "a1-v1").mkdir(parents=True)
    monkeypatch.setattr("sys.argv", ["scan_activity_errors", "--track", "a1-v1"])

    assert scanner.main() == 1
    output = capsys.readouterr().out
    assert "SCAN_INPUT_ERROR" in output
    assert "No structural activity errors found" not in output


def test_default_scan_includes_previous_a1_edition():
    assert "a1-v1" in scanner.ALL_TRACKS
