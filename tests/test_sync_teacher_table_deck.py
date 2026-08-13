"""Tests for the narrowly-scoped Teacher table DOCX extractor."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts.lexicon.sync_teacher_table_deck import (
    DECK_ID,
    DESCRIPTION,
    SCHEMA,
    TeacherTableSyncError,
    extract_teacher_table,
    main,
    write_site_data,
)


def _paragraph(text: str) -> str:
    return f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"


def _table(rows: list[list[str]]) -> str:
    rendered_rows = []
    for row in rows:
        cells = "".join(f"<w:tc>{_paragraph(cell)}</w:tc>" for cell in row)
        rendered_rows.append(f"<w:tr>{cells}</w:tr>")
    return f"<w:tbl>{''.join(rendered_rows)}</w:tbl>"


def _write_docx(path: Path, body: str) -> bytes:
    document_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>{body}</w:body>
</w:document>""".encode()
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
    return path.read_bytes()


def test_extracts_only_the_table_following_the_exact_heading_and_preserves_multiword_cells(
    tmp_path: Path,
) -> None:
    path = tmp_path / "teacher-master.docx"
    docx_bytes = _write_docx(
        path,
        "".join(
            [
                _paragraph("A different table"),
                _table([["Ukrainian", "English"], ["не брати", "do not take"]]),
                _paragraph("Combined Master Vocabulary Table (#3)"),
                _paragraph("The next table, not a full-document form mine."),
                _table(
                    [
                        ["Current", "Ukrainian", "English"],
                        ["old", "Київ", "Kyiv"],
                        ["old", "синє   небо", "blue sky"],
                        ["old", "Київ", "Kyiv"],
                        ["old", "три слова", "three words"],
                        ["old", "", "missing Ukrainian"],
                    ],
                ),
            ],
        ),
    )

    report, lemma_keys = extract_teacher_table(path, "Combined Master Vocabulary Table (#3)")

    assert lemma_keys == ["Київ", "синє небо", "три слова"]
    assert report.raw_data_rows == 5
    assert report.unique_uk == 3
    assert report.multiword == 2
    assert report.first5 == lemma_keys
    assert report.last5 == lemma_keys
    assert report.sha256_docx == hashlib.sha256(docx_bytes).hexdigest()


def test_accepts_current_as_the_ukrainian_source_column_when_ukrainian_is_absent(tmp_path: Path) -> None:
    path = tmp_path / "teacher-master.docx"
    _write_docx(
        path,
        _paragraph("Combined Master Vocabulary Table (#3)")
        + _table([["Current", "English"], ["синє небо", "blue sky"]]),
    )

    _report, lemma_keys = extract_teacher_table(path, "Combined Master Vocabulary Table (#3)")

    assert lemma_keys == ["синє небо"]


def test_rejects_a_table_without_the_required_english_header(tmp_path: Path) -> None:
    path = tmp_path / "teacher-master.docx"
    _write_docx(
        path,
        _paragraph("Combined Master Vocabulary Table (#3)") + _table([["Ukrainian", "Translation"], ["слово", "word"]]),
    )

    with pytest.raises(TeacherTableSyncError, match="English column"):
        extract_teacher_table(path, "Combined Master Vocabulary Table (#3)")


def test_site_data_shrink_guard_preserves_the_previous_public_set(tmp_path: Path) -> None:
    site_data = tmp_path / "lexicon-teacher-table-deck.json"
    site_data.write_text(
        json.dumps({"lemma_keys": ["перше", "друге"]}, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(TeacherTableSyncError, match="refusing to shrink"):
        write_site_data(["перше"], site_data_path=site_data)
    assert json.loads(site_data.read_text(encoding="utf-8"))["lemma_keys"] == ["перше", "друге"]

    write_site_data(["перше"], site_data_path=site_data, allow_shrink=True)
    written = json.loads(site_data.read_text(encoding="utf-8"))
    assert written == {
        "schema": SCHEMA,
        "id": DECK_ID,
        "title": "Dev's example deck",
        "titleUk": "Приклад розробника",
        "description": DESCRIPTION,
        "lemma_keys": ["перше"],
    }


def test_main_emits_required_report_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "teacher-master.docx"
    report_path = tmp_path / "report.json"
    _write_docx(
        path,
        _paragraph("Combined Master Vocabulary Table (#3)")
        + _table([["Ukrainian", "English"], ["синє небо", "blue sky"]]),
    )

    exit_code = main(
        [
            "--docx",
            str(path),
            "--heading",
            "Combined Master Vocabulary Table (#3)",
            "--report",
            str(report_path),
        ],
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == json.loads(report_path.read_text(encoding="utf-8"))
