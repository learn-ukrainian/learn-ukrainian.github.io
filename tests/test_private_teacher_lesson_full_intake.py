from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

from scripts.audit.check_no_private_source_review_exports import find_private_source_review_exports
from scripts.audit.private_teacher_lesson_intake import (
    PROJECT_ROOT,
    SourceInventoryError,
    build_bulk_triage_payload,
    build_private_teacher_lesson_intake,
    candidate_review_payload,
    format_markdown_census,
    inspect_private_source_shape,
    public_census_payload,
    resolve_local_review_output_path,
    write_bulk_triage_payload,
)


def _write_manifest(path: Path, lemmas: list[str]) -> None:
    path.write_text(
        json.dumps({"entries": [{"lemma": lemma} for lemma in lemmas]}, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_source_inventory(path: Path, lemmas: list[str]) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "kind": "atlas_source_inventory",
                "sources": [
                    {
                        "id": "committed-private-teacher-fixture",
                        "source_family": "teacher_lesson",
                        "extraction_mode": "private_document_token",
                        "title": "Synthetic committed teacher inventory",
                        "headwords": lemmas,
                    }
                ],
            },
            ensure_ascii=False,
        ),
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
    source_shape = inspect_private_source_shape([source])

    result = build_private_teacher_lesson_intake(
        [source],
        ignored_tab_indexes=(3,),
        expected_source_shape_sha256=source_shape["source_shape_sha256"],
        manifest_path=manifest,
    )
    census_text = json.dumps(result.census, ensure_ascii=False)
    candidate_payload_text = json.dumps(candidate_review_payload(result), ensure_ascii=False)
    candidate_lemmas = {candidate.lemma for candidate in result.candidates}

    assert result.census["counts"]["units_seen"] == 3
    assert result.census["counts"]["units_included"] == 2
    assert result.census["counts"]["units_ignored"] == 1
    assert result.census["counts"]["token_occurrences"] == 5
    assert result.census["atlas"]["manifest_loaded"] is True
    assert result.census["atlas"]["manifest_sha256"]
    assert result.census["atlas"]["existing_candidates"] == 1
    assert result.census["atlas"]["missing_candidates"] == 2
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
    source_shape = inspect_private_source_shape([source])

    result = build_private_teacher_lesson_intake(
        [source],
        ignored_unit_indexes=(3,),
        expected_source_shape_sha256=source_shape["source_shape_sha256"],
    )
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


def test_private_teacher_intake_requires_source_shape_when_ignoring_units(tmp_path: Path) -> None:
    source = tmp_path / "source.xlsx"
    _write_minimal_xlsx(source, [["відкрите"], ["приховане"]])

    with pytest.raises(SourceInventoryError, match="--expect-source-shape-sha256 is required"):
        build_private_teacher_lesson_intake([source], ignored_tab_indexes=(2,))


def test_private_teacher_intake_aborts_on_source_shape_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "source.xlsx"
    _write_minimal_xlsx(source, [["відкрите"], ["приховане"]])

    with pytest.raises(SourceInventoryError, match="source shape changed"):
        build_private_teacher_lesson_intake(
            [source],
            ignored_tab_indexes=(2,),
            expected_source_shape_sha256="0" * 64,
        )


def test_private_teacher_source_shape_is_safe_summary(tmp_path: Path) -> None:
    source = tmp_path / "private-name.xlsx"
    _write_minimal_xlsx(source, [["видиме"], ["секретний витік"]])

    source_shape = inspect_private_source_shape([source])
    serialized = json.dumps(source_shape, ensure_ascii=False)

    assert source_shape["source_shape_sha256"]
    assert source_shape["units_seen"] == 2
    assert "секретний" not in serialized
    assert "витік" not in serialized
    assert "Private Sheet" not in serialized
    assert str(source) not in serialized


def test_private_teacher_bulk_triage_buckets_and_public_summary_are_safe(tmp_path: Path) -> None:
    source = tmp_path / "source.tsv"
    manifest = tmp_path / "manifest.json"
    committed = tmp_path / "committed.json"
    rows = ["наявне", "покрите", "це", "часте часте часте", "звичайне"]
    rows.extend("" for _ in range(218 - len(rows)))
    rows.append("пізнє")
    source.write_text("\n".join(rows) + "\n", encoding="utf-8")
    _write_manifest(manifest, ["наявне"])
    _write_source_inventory(committed, ["покрите"])

    result = build_private_teacher_lesson_intake([source], manifest_path=manifest)
    triage = build_bulk_triage_payload(
        result,
        committed_inventory_paths=(committed,),
        min_frequency=3,
        post_boundary_row=218,
    )
    counts = triage["counts"]

    assert counts["total_candidates"] == 6
    assert counts["bucket_total"] == counts["total_candidates"]
    assert counts["atlas_existing"] == 1
    assert counts["committed_teacher_inventory"] == 1
    assert counts["low_signal_hold"] == 1
    assert counts["post_boundary_table_missing"] == 1
    assert counts["high_frequency_missing"] == 1
    assert counts["needs_review_bulk"] == 1

    public_text = json.dumps(public_census_payload(result, bulk_triage=triage), ensure_ascii=False)
    for lemma in ("наявне", "покрите", "часте", "звичайне", "пізнє"):
        assert lemma not in public_text
    detailed_text = json.dumps(triage, ensure_ascii=False)
    assert "пізнє" in detailed_text


def test_private_teacher_bulk_triage_output_rejects_repository_paths(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("приватне слово\n", encoding="utf-8")
    result = build_private_teacher_lesson_intake([source])
    triage = build_bulk_triage_payload(result, committed_inventory_paths=())

    with pytest.raises(SourceInventoryError, match="outside the repository"):
        write_bulk_triage_payload(triage, PROJECT_ROOT / "atlas-private-teacher-lesson-bulk-triage.json")


def test_private_source_review_export_guard_blocks_local_payload_marker(tmp_path: Path) -> None:
    export = tmp_path / "candidate-export.json"
    export.write_text(
        json.dumps({"workflow": "private_teacher_lesson_bulk_triage.v1", "buckets": {}}),
        encoding="utf-8",
    )

    assert find_private_source_review_exports([export]) == [export]


def test_private_teacher_source_id_must_be_neutral_slug(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("приватне слово\n", encoding="utf-8")

    with pytest.raises(SourceInventoryError, match="neutral slug"):
        build_private_teacher_lesson_intake([source], source_id="Private Teacher/Name")
