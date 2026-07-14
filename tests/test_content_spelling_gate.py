from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.audit import check_content_spelling as gate

requires_vesum_db = pytest.mark.skipif(
    not Path("data/vesum.db").exists()
    or Path("data/vesum.db").stat().st_size < 1_000_000,
    reason=(
        "requires the full VESUM data/vesum.db; CI may omit or stub it; "
        "build a verified shadow with scripts/rag/build_vesum_shadow.py and provision the required DB"
    ),
)


def test_fixture_reports_typo_and_suppresses_valid_form(tmp_path: Path) -> None:
    mdx_path = _write_mdx(tmp_path, "Мами хибаа слово.")

    result = gate.check_content_spelling([mdx_path], vesum_lookup=_fake_vesum)

    assert [item.form for item in result.unrecognized_forms] == ["хибаа"]
    assert result.summary == {
        "files_scanned": 1,
        "unique_forms": 3,
        "unrecognized": 1,
    }
    assert result.unrecognized_forms[0].example_line == "Мами хибаа слово."


def test_human_report_groups_unrecognized_forms_by_file(tmp_path: Path) -> None:
    first_path = _write_mdx(tmp_path, "Перший рядок з хибаа.", name="first.mdx")
    second_path = _write_mdx(tmp_path, "Другий рядок з хибб.", name="second.mdx")
    result = gate.check_content_spelling([second_path, first_path], vesum_lookup=_fake_vesum)

    report = gate.format_human_summary(result, project_root=tmp_path)

    assert "- first.mdx" in report
    assert "  - хибаа: Перший рядок з хибаа." in report
    assert "- second.mdx" in report
    assert "  - хибб: Другий рядок з хибб." in report


def test_advisory_cli_exits_zero_when_unrecognized_present(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mdx_path = _write_mdx(tmp_path, "Мами хибаа.")

    assert gate.main([], vesum_lookup=_fake_vesum, paths=[mdx_path], project_root=tmp_path) == 0
    output = capsys.readouterr().out

    assert "Content spelling gate" in output
    assert "Unrecognized forms: 1" in output
    assert "хибаа" in output


def test_strict_cli_exits_nonzero_when_unrecognized_present(tmp_path: Path) -> None:
    mdx_path = _write_mdx(tmp_path, "Мами хибаа.")

    assert (
        gate.main(
            ["--strict"],
            vesum_lookup=_fake_vesum,
            paths=[mdx_path],
            project_root=tmp_path,
        )
        == 1
    )


def test_json_cli_reports_unrecognized_forms(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mdx_path = _write_mdx(tmp_path, "Мами хибаа.")

    assert (
        gate.main(
            ["--json"],
            vesum_lookup=_fake_vesum,
            paths=[mdx_path],
            project_root=tmp_path,
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["summary"]["unrecognized"] == 1
    assert payload["unrecognized_forms"] == [
        {
            "form": "хибаа",
            "example_source": "sample.mdx",
            "example_line": "Мами хибаа.",
        }
    ]
    assert payload["grouped_by_file"] == [
        {
            "source": "sample.mdx",
            "forms": [
                {
                    "form": "хибаа",
                    "example_line": "Мами хибаа.",
                }
            ],
        }
    ]


@requires_vesum_db
def test_real_vesum_db_recognizes_valid_form_and_flags_typo(tmp_path: Path) -> None:
    mdx_path = _write_mdx(tmp_path, "Мами маммммм.")

    result = gate.check_content_spelling([mdx_path])

    assert [item.form for item in result.unrecognized_forms] == ["маммммм"]
    assert "мами" in result.unique_forms


def _write_mdx(tmp_path: Path, text: str, *, name: str = "sample.mdx") -> Path:
    mdx_path = tmp_path / name
    mdx_path.write_text(text, encoding="utf-8")
    return mdx_path


def _fake_vesum(words: list[str]) -> dict[str, list[dict[str, Any]]]:
    matches = {
        "другий": [{"lemma": "другий", "pos": "adj", "tags": "m:v_naz"}],
        "з": [{"lemma": "з", "pos": "prep", "tags": ""}],
        "мами": [{"lemma": "мама", "pos": "noun", "tags": "f:p:v_naz"}],
        "перший": [{"lemma": "перший", "pos": "adj", "tags": "m:v_naz"}],
        "рядок": [{"lemma": "рядок", "pos": "noun", "tags": "m:v_naz"}],
        "слово": [{"lemma": "слово", "pos": "noun", "tags": "n:v_naz"}],
    }
    return {word: matches.get(word, []) for word in words}
