"""Synthetic-only tests for the JSONL-chunk textbook headword extractor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.lexicon import extract_textbook_chunk_headword_inventory as extractor


def _fake_vesum(words: list[str]) -> dict[str, list[dict[str, Any]]]:
    matches = {
        "мама": [{"lemma": "мама", "pos": "noun", "tags": ""}],
        "тато": [{"lemma": "тато", "pos": "noun", "tags": ""}],
        "мама-мама": [],  # hyphenated syllable drill never matches directly
        "школа": [{"lemma": "школа", "pos": "noun", "tags": ""}],
        "і": [{"lemma": "і", "pos": "conj", "tags": ""}],
        "замки": [
            {"lemma": "замка", "pos": "noun", "tags": ""},
            {"lemma": "замок", "pos": "noun", "tags": ""},
        ],
    }
    return {word: matches.get(word, []) for word in words}


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _chunk(**kwargs: Any) -> dict[str, Any]:
    row = {"part": 1, "page_start": 1, "page_end": 1, "chunk_id": "x", "text": ""}
    row.update(kwargs)
    return row


def test_load_chunks_sorts_by_part_then_page(tmp_path: Path) -> None:
    path = tmp_path / "book.jsonl"
    _write_jsonl(
        path,
        [
            _chunk(part=1, page_start=3, page_end=3, chunk_id="c", text="в"),
            _chunk(part=1, page_start=1, page_end=1, chunk_id="a", text="а"),
        ],
    )
    chunks = extractor.load_chunks([path])
    assert [c["chunk_id"] for c in chunks] == ["a", "c"]


def test_load_chunks_requires_text_field(tmp_path: Path) -> None:
    path = tmp_path / "book.jsonl"
    path.write_text(json.dumps({"part": 1, "page_start": 1, "page_end": 1}) + "\n", encoding="utf-8")
    with pytest.raises(extractor.ExtractionError):
        extractor.load_chunks([path])


def test_extracts_words_only_headwords_with_locators() -> None:
    chunks = [
        {"part": 1, "page_start": 5, "page_end": 5, "text": "Мама і тато"},
        {"part": 2, "page_start": 7, "page_end": 8, "text": "Школа"},
    ]
    payload = extractor.extract_headword_inventory_from_chunks(
        chunks, source_id="x", title="x", vesum_lookup=_fake_vesum
    )
    headwords = payload["sources"][0]["headwords"]
    lemmas = {item["lemma"] for item in headwords}
    assert {"мама", "тато", "школа", "і"} <= lemmas
    mama = next(item for item in headwords if item["lemma"] == "мама")
    assert mama["pos"] == "noun"
    assert mama["locators"] == ["part 1 p.5"]
    # No source prose beyond individual tokens ever reaches the payload.
    assert "text" not in mama


def test_dehyphenates_bukvar_syllable_drills() -> None:
    chunks = [{"part": 1, "page_start": 1, "page_end": 1, "text": "ма-ма"}]

    def vesum_lookup(words: list[str]) -> dict[str, list[dict[str, Any]]]:
        return {w: ([{"lemma": "мама", "pos": "noun", "tags": ""}] if w == "мама" else []) for w in words}

    payload = extractor.extract_headword_inventory_from_chunks(
        chunks, source_id="x", title="x", vesum_lookup=vesum_lookup
    )
    headwords = payload["sources"][0]["headwords"]
    assert len(headwords) == 1
    assert headwords[0]["lemma"] == "мама"
    assert headwords[0]["from_hyphenated_syllables"] is True


def test_ambiguous_forms_are_flagged_and_counted() -> None:
    chunks = [{"part": 1, "page_start": 1, "page_end": 1, "text": "замки"}]
    payload = extractor.extract_headword_inventory_from_chunks(
        chunks, source_id="x", title="x", vesum_lookup=_fake_vesum
    )
    headwords = payload["sources"][0]["headwords"]
    assert {item["lemma"] for item in headwords} == {"замка", "замок"}
    assert all(item["ambiguous"] for item in headwords)
    assert payload["stats"]["ambiguous_forms"] == 1


def test_validate_result_rejects_empty_headwords() -> None:
    payload = {"sources": [{"headwords": []}], "stats": {"unknown_rate": 0.0, "unknown_forms": 0, "unique_forms": 0}}
    with pytest.raises(extractor.ExtractionError):
        extractor.validate_result(payload)


def test_validate_result_rejects_high_unknown_rate() -> None:
    payload = {
        "sources": [{"headwords": [{"lemma": "мама", "pos": "noun"}]}],
        "stats": {"unknown_rate": 0.5, "unknown_forms": 5, "unique_forms": 10},
    }
    with pytest.raises(extractor.ExtractionError):
        extractor.validate_result(payload)


def test_validate_result_default_threshold_matches_module_constant() -> None:
    payload = {
        "sources": [{"headwords": [{"lemma": "мама", "pos": "noun"}]}],
        "stats": {"unknown_rate": extractor.MAX_UNKNOWN_FORM_RATE + 0.01, "unknown_forms": 21, "unique_forms": 100},
    }
    with pytest.raises(extractor.ExtractionError):
        extractor.validate_result(payload)


def test_validate_result_accepts_explicit_higher_override() -> None:
    payload = {
        "sources": [{"headwords": [{"lemma": "мама", "pos": "noun"}]}],
        "stats": {"unknown_rate": 0.25, "unknown_forms": 25, "unique_forms": 100},
    }
    # Still rejected at the unchanged default...
    with pytest.raises(extractor.ExtractionError):
        extractor.validate_result(payload)
    # ...but passes with an explicit, book-scoped override.
    extractor.validate_result(payload, max_unknown_rate=0.30)


def test_cli_rejects_override_without_reason(tmp_path: Path) -> None:
    jsonl = tmp_path / "book.jsonl"
    _write_jsonl(jsonl, [_chunk(text="мама")])
    out = tmp_path / "out.yaml"
    rc = extractor.main(
        [
            "--jsonl",
            str(jsonl),
            "--source-id",
            "x",
            "--title",
            "x",
            "--out",
            str(out),
            "--max-unknown-rate",
            "0.5",
        ]
    )
    assert rc == 2
    assert not out.exists()


def test_cli_override_with_reason_reports_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # The CLI path resolves the module-level VESUM lookup; CI has no data/vesum.db,
    # so swap in the synthetic lookup ("мама" known, everything else unknown).
    monkeypatch.setattr(extractor, "verify_words", _fake_vesum)
    jsonl = tmp_path / "book.jsonl"
    # "змпщт" is not a real Ukrainian word; it deliberately drives the unknown
    # rate above 20% (1 of 2 forms) to exercise a gate only an explicit override can clear.
    _write_jsonl(jsonl, [_chunk(text="мама змпщт")])
    out = tmp_path / "out.yaml"
    rc = extractor.main(
        [
            "--jsonl",
            str(jsonl),
            "--source-id",
            "x",
            "--title",
            "x",
            "--out",
            str(out),
            "--max-unknown-rate",
            "0.6",
            "--unknown-rate-override-reason",
            "known upstream PDF glyph-drop defect (issue #7551)",
        ]
    )
    assert rc == 0
    assert out.exists()
    captured = capsys.readouterr().out
    assert "UNKNOWN-RATE OVERRIDE (60%)" in captured
    assert "known upstream PDF glyph-drop defect" in captured
