"""Synthetic-only tests for the private-book headword extractor."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.lexicon import extract_book_headword_inventory as extractor


def _fake_vesum(words: list[str]) -> dict[str, list[dict[str, Any]]]:
    matches = {
        "передмова": [{"lemma": "передмова", "pos": "noun", "tags": ""}],
        "донька": [{"lemma": "донька", "pos": "noun", "tags": ""}],
        "модуль": [{"lemma": "модуль", "pos": "noun", "tags": ""}],
        "п'ять": [{"lemma": "п'ять", "pos": "numeral", "tags": ""}],
        "інший": [{"lemma": "інший", "pos": "adj", "tags": ""}],
        "замки": [
            {"lemma": "замка", "pos": "noun", "tags": ""},
            {"lemma": "замок", "pos": "noun", "tags": ""},
        ],
        "мати": [
            {"lemma": "мати", "pos": "noun", "tags": ""},
            {"lemma": "мати", "pos": "verb", "tags": ""},
        ],
        "повторення": [{"lemma": "повторення", "pos": "noun", "tags": ""}],
        "Львів": [{"lemma": "Львів", "pos": "noun", "tags": ""}],
    }
    return {word: matches.get(word, []) for word in words}


def _synthetic_pages() -> list[extractor.PageText]:
    return [
        extractor.PageText(
            1,
            "Передмова до́нька\n"
            "Inspiring resources for learning Ukrainian — UkrainianLessons.com\n"
            "Back to Contents\n"
            "1\n",
        ),
        extractor.PageText(2, "1 Модуль\nДонька пʼять\n2\n"),
        extractor.PageText(3, "2 Інший\nЗамки невідомиця\n3\n"),
        extractor.PageText(4, "«Повторення №1»\nДонька\n4\n"),
    ]


def _headword(result: extractor.ExtractionResult, lemma: str) -> dict[str, Any]:
    return next(
        item
        for item in result.inventory["sources"][0]["headwords"]
        if item["lemma"] == lemma
    )


def test_extracts_words_only_inventory_with_required_provenance() -> None:
    result = extractor.extract_headword_inventory(_synthetic_pages(), vesum_lookup=_fake_vesum)
    inventory = result.inventory
    source = inventory["sources"][0]

    assert source["id"] == "ohoiko-oho-a1-book-headwords"
    assert source["source_family"] == "ohoiko"
    assert source["extraction_mode"] == "headword_inventory"
    assert result.stats == extractor.ExtractionStats(
        pages_read=4,
        tokens_seen=10,
        unique_forms=8,
        unambiguous_forms=6,
        ambiguous_forms=1,
        unknown_forms=1,
        lemmas_found=8,
    )
    assert result.modules_map["pages"] == [
        {"page": 1, "module": "front-matter"},
        {"page": 2, "module": 1},
        {"page": 3, "module": 2},
        {"page": 4, "module": "review-1"},
    ]

    daughter = _headword(result, "донька")
    assert daughter == {
        "lemma": "донька",
        "pos": "noun",
        "count": 3,
        "first_module": "front-matter",
        "modules": ["front-matter", 1, "review-1"],
        "locator": "front-matter p.1",
    }
    assert _headword(result, "замка")["ambiguous"] is True
    assert _headword(result, "замок")["ambiguous"] is True
    assert source["unknown_forms"] == [
        {
            "form": "невідомиця",
            "count": 1,
            "first_module": 2,
            "modules": [2],
            "locator": "module 2 p.3",
        }
    ]

    serialized = yaml.safe_dump(inventory, allow_unicode=True, sort_keys=False)
    assert "gloss" not in serialized
    assert "context" not in serialized
    assert "Inspiring resources" not in serialized
    extractor.validate_result(result)


def test_capitalized_only_form_is_preserved_and_flagged() -> None:
    result = extractor.extract_headword_inventory(
        [extractor.PageText(1, "1 Львів\nЛьвів\n")], vesum_lookup=_fake_vesum
    )

    assert _headword(result, "Львів") == {
        "lemma": "Львів",
        "pos": "noun",
        "count": 2,
        "first_module": 1,
        "modules": [1],
        "locator": "module 1 p.1",
        "proper_noun_candidate": True,
    }


def test_module_mapping_uses_the_latest_header_on_a_page() -> None:
    page_modules, module_count = extractor.map_pages_to_modules(
        [extractor.PageText(1, "1 Перший\n2 Другий\n")]
    )

    assert page_modules == {1: 2}
    assert module_count == 2


def test_same_lemma_with_multiple_vesum_pos_values_is_ambiguous() -> None:
    result = extractor.extract_headword_inventory(
        [extractor.PageText(1, "1 мати\n")], vesum_lookup=_fake_vesum
    )
    candidates = [
        item for item in result.inventory["sources"][0]["headwords"] if item["lemma"] == "мати"
    ]

    assert [item["pos"] for item in candidates] == ["noun", "verb"]
    assert all(item["ambiguous"] is True for item in candidates)
    assert result.stats.ambiguous_forms == 1


def test_running_lines_are_removed_before_tokenization() -> None:
    cleaned = extractor.strip_running_lines(
        "слово\n"
        "Inspiring resources for learning Ukrainian — UkrainianLessons.com\n"
        "Back to Contents\n"
        "12\n"
    )

    assert cleaned == "слово"


def test_output_order_is_deterministic() -> None:
    first = extractor.extract_headword_inventory(_synthetic_pages(), vesum_lookup=_fake_vesum)
    second = extractor.extract_headword_inventory(_synthetic_pages(), vesum_lookup=_fake_vesum)

    assert yaml.safe_dump(first.inventory, allow_unicode=True, sort_keys=False) == yaml.safe_dump(
        second.inventory, allow_unicode=True, sort_keys=False
    )
    assert [item["lemma"] for item in first.inventory["sources"][0]["headwords"]] == [
        "донька",
        "передмова",
        "модуль",
        "п'ять",
        "замка",
        "замок",
        "інший",
        "повторення",
    ]


def test_validation_fails_closed_for_excessive_unknown_forms() -> None:
    pages = [extractor.PageText(1, "1 Модуль\nневідомиця інша-невідомиця\n")]
    result = extractor.extract_headword_inventory(pages, vesum_lookup=_fake_vesum)

    with pytest.raises(extractor.ExtractionError, match="unknown forms exceed 20%"):
        extractor.validate_result(result)


def test_validation_fails_closed_for_no_modules_or_headwords() -> None:
    no_modules = extractor.extract_headword_inventory(
        [extractor.PageText(1, "Модуль\n")], vesum_lookup=_fake_vesum
    )
    no_headwords = extractor.extract_headword_inventory(
        [extractor.PageText(1, "1 Header\n")], vesum_lookup=_fake_vesum
    )

    with pytest.raises(extractor.ExtractionError, match="zero numbered modules"):
        extractor.validate_result(no_modules)
    with pytest.raises(extractor.ExtractionError, match="empty headword output"):
        extractor.validate_result(no_headwords)


def test_output_never_serializes_synthetic_canary_sentence() -> None:
    canary = "Таємна фраза ніколи не має потрапити в YAML"

    def all_known(words: list[str]) -> dict[str, list[dict[str, Any]]]:
        return {
            word: [{"lemma": word, "pos": "noun", "tags": ""}]
            for word in words
        }

    result = extractor.extract_headword_inventory(
        [extractor.PageText(1, f"1 Розділ\n{canary}\n")], vesum_lookup=all_known
    )
    serialized = yaml.safe_dump(result.inventory, allow_unicode=True, sort_keys=False)

    assert canary not in serialized
    assert "Таємна фраза" not in serialized
    assert "фраза ніколи" not in serialized
    source = result.inventory["sources"][0]
    assert "context" not in source
    assert all(
        set(headword) <= {
            "lemma",
            "pos",
            "count",
            "first_module",
            "modules",
            "locator",
            "ambiguous",
            "proper_noun_candidate",
        }
        for headword in source["headwords"]
    )


def test_cli_dry_run_prints_report_without_writing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = extractor.extract_headword_inventory(_synthetic_pages(), vesum_lookup=_fake_vesum)
    monkeypatch.setattr(extractor, "extract_pdf_pages", lambda _: _synthetic_pages())
    monkeypatch.setattr(extractor, "extract_headword_inventory", lambda _: result)
    output = tmp_path / "inventory.yaml"

    exit_code = extractor.main(
        ["--pdf", str(tmp_path / "synthetic.pdf"), "--out", str(output), "--dry-run", "--report"]
    )

    assert exit_code == 0
    assert not output.exists()
    stdout = capsys.readouterr().out
    assert "BEFORE pages_read=4 tokens_seen=10 unique_forms=8" in stdout
    assert "AFTER lemmas_found=8" in stdout
    assert "MODULE COVERAGE" in stdout
    assert "DRY RUN: no output written" in stdout


def test_cli_writes_inventory_and_optional_module_map(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result = extractor.extract_headword_inventory(_synthetic_pages(), vesum_lookup=_fake_vesum)
    monkeypatch.setattr(extractor, "extract_pdf_pages", lambda _: _synthetic_pages())
    monkeypatch.setattr(extractor, "extract_headword_inventory", lambda _: result)
    output = tmp_path / "inventory.yaml"
    modules_map = tmp_path / "modules.yaml"

    exit_code = extractor.main(
        [
            "--pdf",
            str(tmp_path / "synthetic.pdf"),
            "--out",
            str(output),
            "--modules-map-out",
            str(modules_map),
        ]
    )

    assert exit_code == 0
    assert yaml.safe_load(output.read_text(encoding="utf-8")) == result.inventory
    assert yaml.safe_load(modules_map.read_text(encoding="utf-8")) == result.modules_map


def test_cli_failure_reports_stats_without_writing_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    invalid = extractor.extract_headword_inventory(
        [extractor.PageText(1, "Модуль\n")], vesum_lookup=_fake_vesum
    )
    monkeypatch.setattr(extractor, "extract_pdf_pages", lambda _: [extractor.PageText(1, "")])
    monkeypatch.setattr(extractor, "extract_headword_inventory", lambda _: invalid)
    output = tmp_path / "inventory.yaml"

    exit_code = extractor.main(["--pdf", str(tmp_path / "synthetic.pdf"), "--out", str(output)])

    assert exit_code == 2
    assert not output.exists()
    stderr = capsys.readouterr().err
    assert "BEFORE pages_read=1" in stderr
    assert "ERROR: zero numbered modules detected" in stderr


def test_pdf_extraction_invokes_pdftotext_once_per_page(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pdf = tmp_path / "synthetic.pdf"
    pdf.touch()
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[0] == "pdfinfo":
            return subprocess.CompletedProcess(command, 0, stdout="Pages:          2\n", stderr="")
        page = command[command.index("-f") + 1]
        return subprocess.CompletedProcess(command, 0, stdout=f"page {page}", stderr="")

    monkeypatch.setattr(extractor.subprocess, "run", fake_run)

    pages = extractor.extract_pdf_pages(
        pdf, pdftotext_binary="pdftotext", pdfinfo_binary="pdfinfo"
    )

    assert pages == [extractor.PageText(1, "page 1"), extractor.PageText(2, "page 2")]
    assert calls == [
        ["pdfinfo", str(pdf)],
        ["pdftotext", "-f", "1", "-l", "1", "-layout", str(pdf), "-"],
        ["pdftotext", "-f", "2", "-l", "2", "-layout", str(pdf), "-"],
    ]
