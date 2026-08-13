from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_spas_layout_candidates as candidates
from scripts.projects.open_model_data.phase3_linguistic_representation import canonical_json
from scripts.projects.open_model_data.phase3_spas_layout_candidates import SpasLayoutCandidateError


def _texts() -> list[str]:
    return [
        (
            "Графіті № 1\n"
            "Опис: текст після відновлення виглядає таким чином:\n"
            "СЛОВО\n"
            "Довгий коментар з історичною літерою А всередині.\n"
        ),
        "Графіті № 2\nСЛОВО\nПодальший коментар.\n",
        "Графіті № 3\nДовгий рядок з однією історичною літерою А у коментарі.\n",
    ]


def _raw_record(number: int, text: str, page_number: int) -> dict[str, object]:
    return {
        "record_id": f"spas-na-berestovi:graffito:{number:04d}",
        "graffito_number": number,
        "source_text": text,
        "source_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "source_page_fragments": [
            {
                "pdf_page_number": page_number,
                "start_char": 0,
                "end_char": len(text),
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            }
        ],
    }


def _normalized_record(number: int, text: str) -> dict[str, object]:
    return {
        "source_record_id": f"spas-na-berestovi:graffito:{number:04d}",
        "graffito_number": number,
        "raw_source_text": text,
        "normalized_text": text,
        "normalized_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "mapping_events": [],
    }


def _tagged_layout(text: str, *, marks: list[str]) -> dict[str, object]:
    tags = ["/Fixture+Times"] * len(text)
    start = 0
    for mark in marks:
        position = text.index(mark, start)
        tags[position : position + len(mark)] = [candidates.BUKYVEDE_FONT_BASE_NAME] * len(mark)
        start = position + len(mark)
    return {"text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "font_tags": tags}


def _page_layouts() -> dict[int, dict[str, object]]:
    first, second, third = _texts()
    return {
        15: _tagged_layout(first, marks=["СЛОВО", "А"]),
        16: _tagged_layout(second, marks=["СЛОВО"]),
        17: _tagged_layout(third, marks=["А"]),
    }


def _records() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    texts = _texts()
    raw = [_raw_record(index, text, 14 + index) for index, text in enumerate(texts, start=1)]
    normalized = [_normalized_record(index, text) for index, text in enumerate(texts, start=1)]
    return raw, normalized


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> str:
    with (
        path.open("wb") as raw_handle,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as handle,
    ):
        for row in rows:
            handle.write(canonical_json(row).encode() + b"\n")
    return candidates.file_sha256(path)


def _fixture_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    raw_records, normalized_records = _records()
    layouts = _page_layouts()
    raw_dir = tmp_path / "raw"
    adapter_dir = tmp_path / "adapter"
    raw_dir.mkdir()
    adapter_dir.mkdir()
    raw_path = raw_dir / candidates.RAW_OUTPUT_FILENAME
    adapter_path = adapter_dir / candidates.ADAPTER_OUTPUT_FILENAME
    raw_sha256 = _write_jsonl(raw_path, raw_records)
    adapter_sha256 = _write_jsonl(adapter_path, normalized_records)
    adapter_receipt_path = adapter_dir / candidates.ADAPTER_RECEIPT_FILENAME
    adapter_receipt_path.write_text('{"fixture":true}\n', encoding="utf-8")
    adapter_receipt_file_sha256 = candidates.file_sha256(adapter_receipt_path)
    mapping_evidence_path = raw_dir / "bukyvede-glyph-mapping-evidence-v1.json"
    mapping_evidence_path.write_text('{"fixture":true}\n', encoding="utf-8")
    mapping_evidence_sha256 = candidates.file_sha256(mapping_evidence_path)

    monkeypatch.setattr(candidates, "EXPECTED_CATALOG_RECORDS", 3)
    monkeypatch.setattr(candidates, "EXPECTED_RAW_OUTPUT_SHA256", raw_sha256)
    monkeypatch.setattr(candidates, "EXPECTED_ADAPTER_OUTPUT_SHA256", adapter_sha256)
    monkeypatch.setattr(candidates, "EXPECTED_ADAPTER_RECEIPT_FILE_SHA256", adapter_receipt_file_sha256)
    monkeypatch.setattr(candidates, "EXPECTED_ADAPTER_RECEIPT_SHA256", "c" * 64)
    monkeypatch.setattr(candidates, "EXPECTED_MAPPING_EVIDENCE_SHA256", mapping_evidence_sha256)
    monkeypatch.setattr(candidates, "extract_font_layout_pages", lambda *_args, **_kwargs: layouts)
    monkeypatch.setattr(
        candidates,
        "validate_existing_glyph_adapter",
        lambda **_kwargs: {
            "records": 3,
            "output_sha256": adapter_sha256,
            "receipt_sha256": "c" * 64,
            "training_eligible": False,
            "phase4_authorized": False,
        },
    )
    built = [
        candidates.build_layout_candidate_record(
            raw_record,
            normalized_record,
            layouts,
            adapter_output_sha256=adapter_sha256,
        )
        for raw_record, normalized_record in zip(raw_records, normalized_records, strict=True)
    ]
    trigger_records = {
        record["graffito_number"]
        for record in built
        if any(
            item["classification"] == "author_reconstruction_trigger_candidate"
            for item in record["historic_script_dominant_line_candidates"]
        )
    }
    unresolved_records = {
        record["graffito_number"]
        for record in built
        if any(
            item["classification"] == "dominant_historic_script_unresolved"
            for item in record["historic_script_dominant_line_candidates"]
        )
    }
    expected = {
        "records_with_bukyvede": sum(bool(record["font_spans"]) for record in built),
        "records_without_bukyvede": sum(not record["font_spans"] for record in built),
        "bukyvede_runs": sum(len(record["font_spans"]) for record in built),
        "bukyvede_characters": sum(record["denominator"]["bukyvede_characters"] for record in built),
        "bukyvede_nonspace": sum(record["denominator"]["bukyvede_nonspace_characters"] for record in built),
        "lines_with_bukyvede": sum(record["denominator"]["lines_with_bukyvede"] for record in built),
        "dominant_lines": sum(len(record["historic_script_dominant_line_candidates"]) for record in built),
        "dominant_records": sum(bool(record["historic_script_dominant_line_candidates"]) for record in built),
        "trigger_lines": sum(
            item["classification"] == "author_reconstruction_trigger_candidate"
            for record in built
            for item in record["historic_script_dominant_line_candidates"]
        ),
        "trigger_records": len(trigger_records),
        "unresolved_lines": sum(
            item["classification"] == "dominant_historic_script_unresolved"
            for record in built
            for item in record["historic_script_dominant_line_candidates"]
        ),
        "unresolved_records": len(unresolved_records),
        "overlap_records": len(trigger_records & unresolved_records),
    }
    for name, value in (
        ("EXPECTED_RECORDS_WITH_BUKYVEDE", expected["records_with_bukyvede"]),
        ("EXPECTED_RECORDS_WITHOUT_BUKYVEDE", expected["records_without_bukyvede"]),
        ("EXPECTED_BUKYVEDE_RUNS", expected["bukyvede_runs"]),
        ("EXPECTED_BUKYVEDE_CHARACTERS", expected["bukyvede_characters"]),
        ("EXPECTED_BUKYVEDE_NONSPACE_CHARACTERS", expected["bukyvede_nonspace"]),
        ("EXPECTED_LINES_WITH_BUKYVEDE", expected["lines_with_bukyvede"]),
        ("EXPECTED_DOMINANT_LINES", expected["dominant_lines"]),
        ("EXPECTED_DOMINANT_RECORDS", expected["dominant_records"]),
        ("EXPECTED_TRIGGER_LINES", expected["trigger_lines"]),
        ("EXPECTED_TRIGGER_RECORDS", expected["trigger_records"]),
        ("EXPECTED_UNRESOLVED_LINES", expected["unresolved_lines"]),
        ("EXPECTED_UNRESOLVED_RECORDS", expected["unresolved_records"]),
        ("EXPECTED_TRIGGER_UNRESOLVED_RECORD_OVERLAP", expected["overlap_records"]),
    ):
        monkeypatch.setattr(candidates, name, value)
    return {
        "raw_dir": raw_dir,
        "adapter_dir": adapter_dir,
        "mapping_evidence_path": mapping_evidence_path,
        "raw_records": raw_records,
        "normalized_records": normalized_records,
        "layouts": layouts,
        "raw_sha256": raw_sha256,
        "adapter_sha256": adapter_sha256,
        "adapter_receipt_file_sha256": adapter_receipt_file_sha256,
        "mapping_evidence_sha256": mapping_evidence_sha256,
        "expected": expected,
    }


def _materialize(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str = "private",
) -> tuple[dict, dict]:
    fixture = _fixture_inputs(tmp_path, monkeypatch)
    expected = fixture["expected"]
    receipt = candidates.materialize_layout_candidates(
        pdf_path=tmp_path / "fixture.pdf",
        raw_catalog_dir=fixture["raw_dir"],
        adapter_output_dir=fixture["adapter_dir"],
        mapping_evidence_path=fixture["mapping_evidence_path"],
        private_output_dir=tmp_path / name,
        expected_records=3,
        expected_records_with_bukyvede=expected["records_with_bukyvede"],
        expected_records_without_bukyvede=expected["records_without_bukyvede"],
        expected_bukyvede_runs=expected["bukyvede_runs"],
        expected_bukyvede_characters=expected["bukyvede_characters"],
        expected_bukyvede_nonspace_characters=expected["bukyvede_nonspace"],
        expected_lines_with_bukyvede=expected["lines_with_bukyvede"],
        expected_dominant_lines=expected["dominant_lines"],
        expected_dominant_records=expected["dominant_records"],
        expected_trigger_lines=expected["trigger_lines"],
        expected_trigger_records=expected["trigger_records"],
        expected_unresolved_lines=expected["unresolved_lines"],
        expected_unresolved_records=expected["unresolved_records"],
        expected_overlap_records=expected["overlap_records"],
    )
    return receipt, fixture


def test_builds_exact_font_spans_and_trigger_candidate() -> None:
    raw_records, normalized_records = _records()
    record = candidates.build_layout_candidate_record(
        raw_records[0],
        normalized_records[0],
        _page_layouts(),
        adapter_output_sha256="a" * 64,
    )

    assert record["raw_context"] == raw_records[0]["source_text"]
    assert record["normalized_context"] == normalized_records[0]["normalized_text"]
    assert len(record["font_spans"]) == 2
    assert record["font_spans"][0]["raw_text"] == "СЛОВО"
    assert record["font_spans"][0]["pdf_page_number"] == 15
    assert len(record["historic_script_dominant_line_candidates"]) == 1
    candidate = record["historic_script_dominant_line_candidates"][0]
    assert candidate["classification"] == "author_reconstruction_trigger_candidate"
    assert candidate["pdf_page_number"] == 15
    assert candidate["page_start_char"] < candidate["page_end_char"]
    assert candidate["text_cue_present"] is True
    assert "вигляд" in candidate["matched_shape_cues"]
    assert candidate["classification_is_semantic_gold"] is False
    assert candidate["qualified_historical_review_status"] == "pending"
    assert candidate["training_eligible"] is False
    assert record["commentary_and_inscription_layers_separated"] is False
    assert record["phase4_authorized"] is False


def test_routes_dominant_line_without_cue_as_unresolved() -> None:
    raw_records, normalized_records = _records()
    record = candidates.build_layout_candidate_record(
        raw_records[1],
        normalized_records[1],
        _page_layouts(),
        adapter_output_sha256="a" * 64,
    )

    assert [item["classification"] for item in record["historic_script_dominant_line_candidates"]] == [
        "dominant_historic_script_unresolved"
    ]


def test_context_substring_does_not_satisfy_whole_word_text_cue() -> None:
    text = "Графіті № 4\nКонтекст після відновлення виглядає таким чином:\nСЛОВО\n"
    raw_record = _raw_record(4, text, 18)
    normalized_record = _normalized_record(4, text)
    layout = {18: _tagged_layout(text, marks=["СЛОВО"])}

    record = candidates.build_layout_candidate_record(
        raw_record,
        normalized_record,
        layout,
        adapter_output_sha256="a" * 64,
    )

    assert [item["classification"] for item in record["historic_script_dominant_line_candidates"]] == [
        "dominant_historic_script_unresolved"
    ]
    assert record["historic_script_dominant_line_candidates"][0]["text_cue_present"] is False


def test_inline_historic_font_remains_context_only() -> None:
    raw_records, normalized_records = _records()
    record = candidates.build_layout_candidate_record(
        raw_records[2],
        normalized_records[2],
        _page_layouts(),
        adapter_output_sha256="a" * 64,
    )

    assert len(record["font_spans"]) == 1
    assert record["denominator"]["lines_with_bukyvede"] == 1
    assert record["historic_script_dominant_line_candidates"] == []


def test_raw_to_normalized_boundary_tracks_width_reducing_event() -> None:
    record = {
        "raw_source_text": "x\ue02fаy",
        "normalized_text": "x\ua657y",
        "mapping_events": [
            {
                "raw_start_char": 1,
                "raw_end_char": 3,
                "normalized_start_char": 1,
                "normalized_end_char": 2,
            }
        ],
    }

    assert candidates._raw_boundary_to_normalized(record, 0) == 0
    assert candidates._raw_boundary_to_normalized(record, 1) == 1
    assert candidates._raw_boundary_to_normalized(record, 3) == 2
    assert candidates._raw_boundary_to_normalized(record, 4) == 3
    with pytest.raises(SpasLayoutCandidateError, match="splits a glyph mapping event"):
        candidates._raw_boundary_to_normalized(record, 2)


def test_materialization_writes_complete_private_queue_and_text_free_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt, fixture = _materialize(tmp_path, monkeypatch)
    with gzip.open(tmp_path / "private" / candidates.OUTPUT_FILENAME, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]

    assert len(rows) == 3
    assert rows[0]["raw_context"] == fixture["raw_records"][0]["source_text"]
    assert receipt["denominator"]["dominant_line_candidates"] == 2
    assert receipt["denominator"]["trigger_line_candidates"] == 1
    assert receipt["denominator"]["unresolved_dominant_line_candidates"] == 1
    assert receipt["routing_contract"]["classifications_are_semantic_gold"] is False
    assert receipt["safeguards"]["training_eligible"] is False
    assert receipt["safeguards"]["phase4_authorized"] is False
    assert receipt["residuals"]["commentary_transcription_separation_pending"] is True
    assert "СЛОВО" not in json.dumps(receipt, ensure_ascii=False)
    candidates._validate_receipt(receipt)


def test_materialization_is_byte_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first, fixture = _materialize(tmp_path, monkeypatch, name="first")
    expected = fixture["expected"]
    second = candidates.materialize_layout_candidates(
        pdf_path=tmp_path / "fixture.pdf",
        raw_catalog_dir=fixture["raw_dir"],
        adapter_output_dir=fixture["adapter_dir"],
        mapping_evidence_path=fixture["mapping_evidence_path"],
        private_output_dir=tmp_path / "second",
        expected_records=3,
        expected_records_with_bukyvede=expected["records_with_bukyvede"],
        expected_records_without_bukyvede=expected["records_without_bukyvede"],
        expected_bukyvede_runs=expected["bukyvede_runs"],
        expected_bukyvede_characters=expected["bukyvede_characters"],
        expected_bukyvede_nonspace_characters=expected["bukyvede_nonspace"],
        expected_lines_with_bukyvede=expected["lines_with_bukyvede"],
        expected_dominant_lines=expected["dominant_lines"],
        expected_dominant_records=expected["dominant_records"],
        expected_trigger_lines=expected["trigger_lines"],
        expected_trigger_records=expected["trigger_records"],
        expected_unresolved_lines=expected["unresolved_lines"],
        expected_unresolved_records=expected["unresolved_records"],
        expected_overlap_records=expected["overlap_records"],
    )

    assert first["output"]["sha256"] == second["output"]["sha256"]
    assert first["receipt_sha256"] == second["receipt_sha256"]


def test_existing_queue_rebinds_all_inputs_and_replays_every_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt, fixture = _materialize(tmp_path, monkeypatch)
    validation = candidates.validate_existing_layout_candidates(
        pdf_path=tmp_path / "fixture.pdf",
        raw_catalog_dir=fixture["raw_dir"],
        adapter_output_dir=fixture["adapter_dir"],
        mapping_evidence_path=fixture["mapping_evidence_path"],
        private_output_dir=tmp_path / "private",
    )

    assert validation == {
        "ok": True,
        "records": 3,
        "candidate_lines": 2,
        "trigger_lines": 1,
        "unresolved_lines": 1,
        "output_sha256": receipt["output"]["sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "training_eligible": False,
        "phase4_authorized": False,
    }


def test_existing_queue_rejects_output_tamper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _receipt, fixture = _materialize(tmp_path, monkeypatch)
    output = tmp_path / "private" / candidates.OUTPUT_FILENAME
    payload = bytearray(output.read_bytes())
    payload[len(payload) // 2] ^= 1
    output.write_bytes(payload)

    with pytest.raises(SpasLayoutCandidateError, match="SHA-256 drift"):
        candidates.validate_existing_layout_candidates(
            pdf_path=tmp_path / "fixture.pdf",
            raw_catalog_dir=fixture["raw_dir"],
            adapter_output_dir=fixture["adapter_dir"],
            mapping_evidence_path=fixture["mapping_evidence_path"],
            private_output_dir=tmp_path / "private",
        )


def test_receipt_rejects_candidate_partition_tamper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipt, _fixture = _materialize(tmp_path, monkeypatch)
    receipt["denominator"]["trigger_line_candidates"] += 1
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = candidates.sha256_value(body)

    with pytest.raises(SpasLayoutCandidateError, match="classification partition drift"):
        candidates._validate_receipt(receipt)


def test_refuses_existing_or_git_checkout_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = _fixture_inputs(tmp_path, monkeypatch)
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(SpasLayoutCandidateError, match="already exists"):
        candidates.materialize_layout_candidates(
            pdf_path=tmp_path / "fixture.pdf",
            raw_catalog_dir=fixture["raw_dir"],
            adapter_output_dir=fixture["adapter_dir"],
            mapping_evidence_path=fixture["mapping_evidence_path"],
            private_output_dir=existing,
        )

    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").write_text("gitdir: fixture", encoding="utf-8")
    with pytest.raises(SpasLayoutCandidateError, match="cannot be inside a Git checkout"):
        candidates.materialize_layout_candidates(
            pdf_path=tmp_path / "fixture.pdf",
            raw_catalog_dir=fixture["raw_dir"],
            adapter_output_dir=fixture["adapter_dir"],
            mapping_evidence_path=fixture["mapping_evidence_path"],
            private_output_dir=checkout / "private",
        )
