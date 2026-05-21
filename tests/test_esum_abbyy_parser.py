from __future__ import annotations

import json
from pathlib import Path

from lxml import etree

from scripts.ingest.esum_abbyy_parser import (
    NS,
    _is_entry_start_paragraph,
    _line_from_element,
    iter_abbyy_paragraphs,
    parse_abbyy_xml,
    write_jsonl,
)

FIXTURES = Path(__file__).parent / "ingest" / "fixtures"


def test_char_params_reconstruct_line_text_and_formatting() -> None:
    line = etree.fromstring(
        f"""
        <line xmlns="{NS.strip("{}")}" l="10" t="20" r="100" b="40">
          <formatting bold="1" ff="Default Metrics Font" fs="11.5">
            <charParams l="10" t="20" r="20" b="40">а</charParams>
          </formatting>
          <formatting ff="Default Metrics Font" fs="7">
            <charParams l="21" t="20" r="25" b="40">1</charParams>
          </formatting>
          <formatting italic="1" ff="Default Metrics Font" fs="11.5">
            <charParams l="26" t="20" r="40" b="40"> тест</charParams>
          </formatting>
        </line>
        """.encode()
    )

    parsed = _line_from_element(line)

    assert parsed.text == "а1 тест"
    assert parsed.left == 10
    assert [run.text for run in parsed.runs] == ["а", "1", " тест"]
    assert parsed.runs[0].bold is True
    assert parsed.runs[2].italic is True


def test_entry_boundary_detection_uses_indented_paragraphs() -> None:
    paragraphs = list(iter_abbyy_paragraphs(FIXTURES / "esum_abbyy_fixture.xml"))

    starts = [paragraph.text for paragraph in paragraphs if _is_entry_start_paragraph(paragraph)]

    assert starts == [
        "а1 (сполучник); — псл. а; споріднене з дінд. а, лат. atque; довга тестова фраза для повного запису.",
        "абетка, абетний; — власне українська назва азбуки, утворена від а і бе; текст достатньої довжини.",
        "[абе] (вигук відрази);— складне слово, утворене з вигуків а2 і бе2 (див.).",
    ]


def test_parse_abbyy_xml_merges_continuation_paragraphs() -> None:
    entries = parse_abbyy_xml(FIXTURES / "esum_abbyy_fixture.xml", vol=1)

    assert [entry["lemma"] for entry in entries] == ["а", "абетка", "абе"]
    assert entries[0]["page"] == 1
    assert "Продовження тієї самої статті" in str(entries[0]["etymology_text"])
    assert entries[0]["cognates"] == ["псл.", "дінд.", "лат."]


def test_write_jsonl_matches_existing_schema_keys(tmp_path: Path) -> None:
    entries = parse_abbyy_xml(FIXTURES / "esum_abbyy_fixture.xml", vol=1)
    output = tmp_path / "esum_abbyy.jsonl"

    count = write_jsonl(entries, output)

    assert count == 3
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert set(rows[0]) == {"cognates", "etymology_text", "lemma", "page", "vol"}
    assert rows[0]["lemma"] == "а"
