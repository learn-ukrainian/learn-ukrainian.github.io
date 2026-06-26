from pathlib import Path

from scripts.audit import check_no_internal_ids


def test_clean_fixture_has_no_findings(tmp_path: Path) -> None:
    clean = tmp_path / "clean.mdx"
    clean.write_text(
        "---\ntitle: Clean\n---\n\nA public source URL is fine: https://www.ukrlib.com.ua/demo/\n",
        encoding="utf-8",
    )

    assert check_no_internal_ids.scan_files([clean]) == []


def test_violating_fixture_reports_chunk_and_section_ids(tmp_path: Path) -> None:
    bad = tmp_path / "bad.mdx"
    bad.write_text(
        "---\ntitle: Bad\n---\n\ntruthSource={`5794da94_c0817`}\nSource section S4433 leaked.\n",
        encoding="utf-8",
    )

    findings = check_no_internal_ids.scan_files([bad])

    assert [(finding.line_no, finding.value) for finding in findings] == [
        (5, "5794da94_c0817"),
        (6, "S4433"),
    ]


def test_main_files_mode_prints_file_line_on_violation(tmp_path: Path, capsys) -> None:
    bad = tmp_path / "bad.mdx"
    bad.write_text("Visible leak 40beaaff_c0000.\n", encoding="utf-8")

    exit_code = check_no_internal_ids.main(["--files", str(bad)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert f"{bad}:1:14: internal corpus chunk id leaked: 40beaaff_c0000\n" == output


def test_non_mdx_explicit_file_is_ignored(tmp_path: Path, capsys) -> None:
    note = tmp_path / "note.txt"
    note.write_text("Internal-looking text 40beaaff_c0000 outside MDX.\n", encoding="utf-8")

    exit_code = check_no_internal_ids.main(["--files", str(note)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert output == "0 findings: no published seminar/readings MDX files to scan.\n"
