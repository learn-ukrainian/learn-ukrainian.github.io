from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

from scripts.audit.private_teacher_lesson_intake import (
    PROJECT_ROOT,
    SourceInventoryError,
    build_private_teacher_lesson_intake,
    candidate_review_payload,
    format_markdown_census,
    resolve_local_review_output_path,
)


def _write_manifest(path: Path, lemmas: list[str]) -> None:
    path.write_text(
        json.dumps({"entries": [{"lemma": lemma} for lemma in lemmas]}, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_minimal_xlsx(path: Path, sheets: list[list[str]]) -> None:
    workbook_sheets = "\n".join(
        (
            f'<sheet name="Private Sheet {index}" sheetId="{index}" '
            f'r:id="rId{index}"/>'
        )
        for index in range(1, len(sheets) + 1)
    )
    relationships = "\n".join(
        (
            f'<Relationship Id="rId{index}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{index}.xml"/>'
        )
        for index in range(1, len(sheets) + 1)
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "xl/workbook.xml",
            (
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                f"<sheets>{workbook_sheets}</sheets></workbook>"
            ),
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f"{relationships}</Relationships>"
            ),
        )
        for index, rows in enumerate(sheets, start=1):
            row_xml = "\n".join(
                (
                    f'<row r="{row_index}"><c r="A{row_index}" t="inlineStr">'
                    f"<is><t>{escape(text)}</t></is></c></row>"
                )
                for row_index, text in enumerate(rows, start=1)
            )
            archive.writestr(
                f"xl/worksheets/sheet{index}.xml",
                (
                    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                    f"<sheetData>{row_xml}</sheetData></worksheet>"
                ),
            )


def _write_minimal_docx(path: Path, paragraphs: list[str]) -> None:
    paragraph_xml = "".join(
        (
            "<w:p><w:r><w:t>"
            f"{escape(paragraph)}"
            "</w:t></w:r></w:p>"
        )
        for paragraph in paragraphs
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            (
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f"<w:body>{paragraph_xml}</w:body></w:document>"
            ),
        )


def test_private_teacher_full_intake_ignores_tab_three_and_omits_raw_text_from_census(
    tmp_path: Path,
) -> None:
    source = tmp_path / "local-private-source.xlsx"
    manifest = tmp_path / "manifest.json"
    _write_minimal_xlsx(
        source,
        [
            ["приватне слово приватне"],
            ["інше слово"],
            ["секретний витік"],
        ],
    )
    _write_manifest(manifest, ["приватне"])

    result = build_private_teacher_lesson_intake(
        [source],
        ignored_tab_indexes=(3,),
        manifest_path=manifest,
    )
    census_text = json.dumps(result.census, ensure_ascii=False)
    candidate_payload_text = json.dumps(candidate_review_payload(result), ensure_ascii=False)
    candidate_lemmas = {candidate.lemma for candidate in result.candidates}

    assert result.census["counts"]["units_seen"] == 3
    assert result.census["counts"]["units_included"] == 2
    assert result.census["counts"]["units_ignored"] == 1
    assert result.census["counts"]["token_occurrences"] == 5
    assert result.census["atlas"] == {
        "manifest_loaded": True,
        "existing_candidates": 1,
        "missing_candidates": 2,
    }
    assert {"приватне", "слово", "інше"} == candidate_lemmas
    assert "секретний" not in candidate_lemmas
    assert "витік" not in candidate_lemmas

    assert "приватне" not in census_text
    assert "секретний" not in census_text
    assert "local-private-source" not in census_text
    assert str(source) not in census_text
    assert "Private Sheet" not in candidate_payload_text
    assert str(source) not in candidate_payload_text
    assert '"source_path":' not in candidate_payload_text
    assert "surface_admission" not in candidate_payload_text


def test_private_teacher_full_intake_ignores_docx_unit_before_candidate_extraction(
    tmp_path: Path,
) -> None:
    source = tmp_path / "local-private-source.docx"
    _write_minimal_docx(
        source,
        [
            "перший кандидат",
            "другий кандидат",
            "таємний кандидат",
        ],
    )

    result = build_private_teacher_lesson_intake([source], ignored_unit_indexes=(3,))
    candidate_lemmas = {candidate.lemma for candidate in result.candidates}
    serialized = json.dumps(result.census, ensure_ascii=False)

    assert result.census["counts"]["units_seen"] == 3
    assert result.census["counts"]["units_ignored"] == 1
    assert "таємний" not in candidate_lemmas
    assert "таємний" not in serialized
    assert "local-private-source" not in serialized


def test_private_teacher_candidate_payload_uses_neutral_locators_only(tmp_path: Path) -> None:
    source = tmp_path / "source.tsv"
    source.write_text("лема\tприклад\nнова\tфраза\n", encoding="utf-8")

    result = build_private_teacher_lesson_intake([source])
    payload = candidate_review_payload(result)

    assert payload["production_outputs_updated"] == []
    assert payload["safety"]["raw_text_included"] is False
    assert payload["safety"]["source_paths_included"] is False
    for row in payload["candidates"]:
        assert row["source_family"] == "teacher_lesson"
        assert row["classification"] == "review_queue"
        assert row["source_ids"] == ["private-teacher-lesson-full-source"]
        assert all(locator.startswith("private source unit 1 row ") for locator in row["locators"])


def test_private_teacher_census_markdown_is_safe_summary(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("приховане слово\n", encoding="utf-8")

    result = build_private_teacher_lesson_intake([source])
    markdown = format_markdown_census(result.census)

    assert "deduped_candidates: 2" in markdown
    assert "raw_text_included: false" in markdown
    assert "production_outputs_updated: []" in markdown
    assert "приховане" not in markdown


def test_private_teacher_candidate_output_rejects_repository_paths() -> None:
    with pytest.raises(SourceInventoryError, match="outside the repository"):
        resolve_local_review_output_path(PROJECT_ROOT / "private-candidates.json")


def test_private_teacher_source_id_must_be_neutral_slug(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("приватне слово\n", encoding="utf-8")

    with pytest.raises(SourceInventoryError, match="neutral slug"):
        build_private_teacher_lesson_intake([source], source_id="Private Teacher/Name")
