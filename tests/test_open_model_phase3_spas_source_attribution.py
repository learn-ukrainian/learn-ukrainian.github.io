from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_spas_source_attribution as attribution
from scripts.projects.open_model_data.phase3_linguistic_representation import canonical_json
from scripts.projects.open_model_data.phase3_spas_source_attribution import SpasSourceAttributionError


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _candidate(text: str, *, trigger: bool, page: int) -> tuple[str, dict[str, object]]:
    line = "СЛОВО\n"
    start = text.index(line)
    context_start = max(0, start - 220)
    context = text[context_start:start]
    return line, {
        "candidate_id": "dominant-line:001",
        "classification": (attribution.TRIGGER_CLASSIFICATION if trigger else attribution.FALLBACK_CLASSIFICATION),
        "classification_is_semantic_gold": False,
        "pdf_page_number": page,
        "page_start_char": 100,
        "page_end_char": 100 + len(line),
        "raw_start_char": start,
        "raw_end_char": start + len(line),
        "raw_text": line,
        "raw_text_sha256": _sha(line),
        "normalized_start_char": start,
        "normalized_end_char": start + len(line),
        "normalized_text": line,
        "normalized_text_sha256": _sha(line),
        "line_nonspace_characters": 5,
        "bukyvede_nonspace_characters": 5,
        "dominance_numerator": 5,
        "dominance_denominator": 5,
        "dominance_threshold": "at_least_one_half",
        "trigger_context_start_char": context_start,
        "trigger_context_end_char": start,
        "trigger_context_sha256": _sha(context),
        "text_cue_present": trigger,
        "matched_shape_cues": ["вигляд", "віднов"] if trigger else [],
        "qualified_historical_review_status": "pending",
        "training_eligible": False,
    }


def _row(number: int, *, trigger: bool | None) -> dict[str, object]:
    if trigger:
        text = f"Графіті № {number}\nОпис: текст після відновлення має вигляд:\nСЛОВО\nКоментар.\n"
    else:
        text = f"Графіті № {number}\nПорівняльна таблиця:\nСЛОВО\nКоментар.\n"
    candidates: list[dict[str, object]] = []
    if trigger is not None:
        _line, candidate = _candidate(text, trigger=trigger, page=14 + number)
        candidates.append(candidate)
    return {
        "schema_version": "phase3_spas_layout_candidate_record_v1",
        "record_id": f"spas-na-berestovi:graffito:{number:04d}:layout-candidates-v1",
        "source_record_id": f"spas-na-berestovi:graffito:{number:04d}",
        "collection_id": attribution.COLLECTION_ID,
        "graffito_number": number,
        "source_pdf_sha256": attribution.SOURCE_PDF_SHA256,
        "raw_context": text,
        "raw_context_sha256": _sha(text),
        "normalized_context": text,
        "normalized_context_sha256": _sha(text),
        "historic_script_dominant_line_candidates": candidates,
        "commentary_and_inscription_layers_separated": False,
        "semantic_gold": False,
        "training_eligible": False,
        "modern_correction_eligible": False,
        "provider_calls": False,
        "phase4_authorized": False,
    }


def _rows() -> list[dict[str, object]]:
    return [_row(1, trigger=True), _row(2, trigger=False), _row(3, trigger=None)]


def _patch_denominator(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in (
        ("EXPECTED_INPUT_RECORDS", 3),
        ("EXPECTED_DOMINANT_RECORDS", 2),
        ("EXPECTED_DOMINANT_LINES", 2),
        ("EXPECTED_TRIGGER_LINES", 1),
        ("EXPECTED_TRIGGER_RECORDS", 1),
        ("EXPECTED_UNRESOLVED_LINES", 1),
        ("EXPECTED_UNRESOLVED_RECORDS", 1),
        ("EXPECTED_TRIGGER_UNRESOLVED_RECORD_OVERLAP", 0),
    ):
        monkeypatch.setattr(attribution, name, value)


def _patch_upstream(monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, object]]) -> None:
    _patch_denominator(monkeypatch)
    monkeypatch.setattr(attribution, "_load_and_rebind_layout", lambda **_kwargs: (rows, {"fixture": True}))


def _materialize(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str = "private",
) -> dict[str, object]:
    _patch_upstream(monkeypatch, _rows())
    return attribution.materialize_source_attribution(
        pdf_path=tmp_path / "fixture.pdf",
        raw_catalog_dir=tmp_path / "raw",
        adapter_output_dir=tmp_path / "adapter",
        mapping_evidence_path=tmp_path / "raw" / "mapping.json",
        layout_candidate_dir=tmp_path / "layout",
        private_output_dir=tmp_path / name,
    )


def test_attributes_only_explicit_author_reconstruction_cue() -> None:
    record = attribution.build_source_attribution_record(_row(1, trigger=True))

    assert record["raw_context"].startswith("Графіті № 1")
    assert record["denominator"] == {
        "candidate_lines": 1,
        "source_attributed_lines": 1,
        "unresolved_lines": 0,
    }
    disposition = record["candidate_dispositions"][0]
    assert disposition["disposition"] == attribution.ATTRIBUTED_DISPOSITION
    assert disposition["layer"] == "source_attributed_inscription_reconstruction"
    assert disposition["authority"] == "published_edition_author"
    assert disposition["source_attribution_evidence"]["source_author"] == "В. В. Корнієнко"
    assert disposition["source_attribution_evidence"]["evidence_status"] == "explicit_author_reconstruction_cue"
    assert record["semantic_gold"] is False
    assert record["training_eligible"] is False
    assert record["phase4_authorized"] is False
    assert record["explicit_source_attribution_pass_complete"] is True


def test_preserves_comparison_line_as_unresolved() -> None:
    record = attribution.build_source_attribution_record(_row(2, trigger=False))

    disposition = record["candidate_dispositions"][0]
    assert disposition["disposition"] == attribution.UNRESOLVED_DISPOSITION
    assert disposition["layer"] == "unresolved_historic_script_line"
    assert disposition["authority"] == "unresolved"
    assert disposition["source_attribution_evidence"]["evidence_status"] == "insufficient_for_attribution"
    assert record["candidate_line_disposition_complete"] is True


def test_rejects_forged_trigger_without_source_cues() -> None:
    row = _row(2, trigger=False)
    row["historic_script_dominant_line_candidates"][0]["classification"] = attribution.TRIGGER_CLASSIFICATION

    with pytest.raises(SpasSourceAttributionError, match="classification drift"):
        attribution.build_source_attribution_record(row)


def test_rejects_candidate_offset_or_hash_drift() -> None:
    row = _row(1, trigger=True)
    row["historic_script_dominant_line_candidates"][0]["raw_start_char"] += 1

    with pytest.raises(SpasSourceAttributionError, match="raw text drift"):
        attribution.build_source_attribution_record(row)


def test_materializes_private_complete_context_and_text_free_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _materialize(tmp_path, monkeypatch)
    output = tmp_path / "private" / attribution.OUTPUT_FILENAME
    with gzip.open(output, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]

    assert len(rows) == 2
    assert rows[0]["raw_context"].startswith("Графіті № 1")
    assert receipt["denominator"] == {
        "input_records": 3,
        "candidate_records": 2,
        "candidate_lines": 2,
        "source_attributed_lines": 1,
        "source_attributed_records": 1,
        "unresolved_lines": 1,
        "unresolved_records": 1,
        "attributed_unresolved_record_overlap": 0,
    }
    assert receipt["safeguards"]["explicit_source_attribution_pass_complete"] is True
    assert receipt["safeguards"]["semantic_gold"] is False
    assert receipt["safeguards"]["training_eligible"] is False
    assert receipt["safeguards"]["phase4_authorized"] is False
    assert receipt["residuals"]["unresolved_candidate_lines"] == 1
    assert "СЛОВО" not in json.dumps(receipt, ensure_ascii=False)
    attribution._validate_receipt(receipt)


def test_materialization_is_byte_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first = _materialize(tmp_path, monkeypatch, name="first")
    second = _materialize(tmp_path, monkeypatch, name="second")

    assert first["output"]["sha256"] == second["output"]["sha256"]
    assert first["receipt_sha256"] == second["receipt_sha256"]


def test_existing_output_rebinds_and_replays_every_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _materialize(tmp_path, monkeypatch)
    result = attribution.validate_existing_source_attribution(
        pdf_path=tmp_path / "fixture.pdf",
        raw_catalog_dir=tmp_path / "raw",
        adapter_output_dir=tmp_path / "adapter",
        mapping_evidence_path=tmp_path / "raw" / "mapping.json",
        layout_candidate_dir=tmp_path / "layout",
        private_output_dir=tmp_path / "private",
    )

    assert result == {
        "ok": True,
        "records": 2,
        "candidate_lines": 2,
        "source_attributed_lines": 1,
        "unresolved_lines": 1,
        "output_sha256": receipt["output"]["sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "semantic_gold": False,
        "training_eligible": False,
        "phase4_authorized": False,
    }


def test_existing_output_rejects_same_length_corruption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize(tmp_path, monkeypatch)
    output = tmp_path / "private" / attribution.OUTPUT_FILENAME
    payload = bytearray(output.read_bytes())
    payload[len(payload) // 2] ^= 1
    output.write_bytes(payload)

    with pytest.raises(SpasSourceAttributionError, match="SHA-256 drift"):
        attribution.validate_existing_source_attribution(
            pdf_path=tmp_path / "fixture.pdf",
            raw_catalog_dir=tmp_path / "raw",
            adapter_output_dir=tmp_path / "adapter",
            mapping_evidence_path=tmp_path / "raw" / "mapping.json",
            layout_candidate_dir=tmp_path / "layout",
            private_output_dir=tmp_path / "private",
        )


def test_receipt_rejects_disposition_partition_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _materialize(tmp_path, monkeypatch)
    receipt["denominator"]["source_attributed_lines"] += 1
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = attribution.sha256_value(body)

    with pytest.raises(SpasSourceAttributionError, match="disposition partition drift"):
        attribution._validate_receipt(receipt)


def test_refuses_existing_or_git_checkout_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_upstream(monkeypatch, _rows())
    kwargs = {
        "pdf_path": tmp_path / "fixture.pdf",
        "raw_catalog_dir": tmp_path / "raw",
        "adapter_output_dir": tmp_path / "adapter",
        "mapping_evidence_path": tmp_path / "raw" / "mapping.json",
        "layout_candidate_dir": tmp_path / "layout",
    }
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(SpasSourceAttributionError, match="already exists"):
        attribution.materialize_source_attribution(private_output_dir=existing, **kwargs)

    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").write_text("gitdir: fixture", encoding="utf-8")
    with pytest.raises(SpasSourceAttributionError, match="cannot be inside a Git checkout"):
        attribution.materialize_source_attribution(private_output_dir=checkout / "private", **kwargs)


def test_gzip_writer_uses_canonical_json(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl.gz"
    row = {"z": 1, "a": "українська"}
    attribution._write_jsonl_gzip(path, [row])

    with gzip.open(path, "rb") as handle:
        assert handle.read() == canonical_json(row).encode() + b"\n"
