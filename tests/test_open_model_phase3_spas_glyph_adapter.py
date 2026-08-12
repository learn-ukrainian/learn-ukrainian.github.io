from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_spas_glyph_adapter as adapter
from scripts.projects.open_model_data.phase3_linguistic_representation import canonical_json
from scripts.projects.open_model_data.phase3_spas_glyph_adapter import (
    SpasGlyphAdapterError,
    apply_bukyvede_mapping,
    reconstruct_raw_text,
)


def _mapped_text() -> str:
    return "|".join(rule.raw * rule.expected_occurrences for rule in adapter.MAPPING_RULES)


def _raw_record(number: int, text: str) -> dict[str, object]:
    return {
        "record_id": f"spas-na-berestovi:graffito:{number:04d}",
        "collection_id": adapter.COLLECTION_ID,
        "graffito_number": number,
        "source_pdf_sha256": adapter.SOURCE_PDF_SHA256,
        "source_text": text,
        "source_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "private_use_codepoint_counts": adapter._private_use_counts(text),
    }


def _write_raw(path: Path, records: list[dict[str, object]]) -> str:
    with (
        path.open("wb") as raw_handle,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as handle,
    ):
        for record in records:
            handle.write(canonical_json(record).encode() + b"\n")
    return adapter.file_sha256(path)


def _mapping_evidence(raw_sha256: str, raw_receipt_sha256: str) -> dict[str, object]:
    return {
        "schema_version": "private_phase3_spas_bukyvede_glyph_mapping_evidence_v1",
        "evidence_id": "fixture",
        "text_free": True,
        "source": {
            "collection_id": adapter.COLLECTION_ID,
            "source_pdf_sha256": adapter.SOURCE_PDF_SHA256,
            "catalog_records": 2,
            "raw_catalog_jsonl_sha256": raw_sha256,
            "raw_materialization_receipt_sha256": raw_receipt_sha256,
        },
        "embedded_font": {
            "font_sha256": adapter.EXPECTED_FONT_SHA256,
            "to_unicode_sha256": adapter.EXPECTED_TO_UNICODE_SHA256,
        },
        "source_verified_mapping_candidates": [
            {
                "raw_pattern": adapter._codepoints(rule.raw),
                "normalized_pattern": adapter._codepoints(rule.normalized),
                "occurrences": rule.expected_occurrences,
            }
            for rule in adapter.MAPPING_RULES
        ],
        "denominator_checks": {
            "private_use_occurrences": adapter.EXPECTED_MAPPING_EVENTS,
            "raw_pattern_occurrence_sum": adapter.EXPECTED_MAPPING_EVENTS,
            "unexpected_private_use_codepoints": 0,
        },
        "safeguards": {
            "mapping_is_deterministic_source_adapter_not_semantic_gold": True,
            "training_eligible": False,
            "phase4_authorized": False,
        },
    }


def _fixture_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    records = [_raw_record(1, _mapped_text()), _raw_record(2, "Без приватних символів.")]
    raw_path = raw_dir / adapter.RAW_OUTPUT_FILENAME
    raw_sha256 = _write_raw(raw_path, records)
    raw_receipt_path = raw_dir / adapter.RAW_RECEIPT_FILENAME
    raw_receipt_path.write_text('{"fixture":true}\n', encoding="utf-8")
    raw_receipt_file_sha256 = adapter.file_sha256(raw_receipt_path)
    raw_receipt_sha256 = "b" * 64

    monkeypatch.setattr(adapter, "EXPECTED_RAW_OUTPUT_SHA256", raw_sha256)
    monkeypatch.setattr(adapter, "EXPECTED_RAW_RECEIPT_FILE_SHA256", raw_receipt_file_sha256)
    monkeypatch.setattr(adapter, "EXPECTED_RAW_RECEIPT_SHA256", raw_receipt_sha256)
    monkeypatch.setattr(adapter, "EXPECTED_CATALOG_RECORDS", 2)
    monkeypatch.setattr(
        adapter,
        "validate_existing_materialization",
        lambda **_kwargs: {
            "source_pdf_sha256": adapter.SOURCE_PDF_SHA256,
            "records": 2,
            "private_jsonl_sha256": raw_sha256,
            "receipt_sha256": raw_receipt_sha256,
            "training_eligible": False,
        },
    )
    evidence_path = raw_dir / adapter.MAPPING_EVIDENCE_FILENAME
    evidence_path.write_text(
        json.dumps(_mapping_evidence(raw_sha256, raw_receipt_sha256), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    evidence_sha256 = adapter.file_sha256(evidence_path)
    monkeypatch.setattr(adapter, "EXPECTED_MAPPING_EVIDENCE_SHA256", evidence_sha256)

    raw_characters = sum(len(record["source_text"]) for record in records)
    normalized_characters = sum(len(apply_bukyvede_mapping(record["source_text"])[0]) for record in records)
    monkeypatch.setattr(adapter, "EXPECTED_RAW_RECORD_CHARACTERS", raw_characters)
    monkeypatch.setattr(adapter, "EXPECTED_NORMALIZED_CHARACTERS", normalized_characters)
    monkeypatch.setattr(adapter, "EXPECTED_RECORDS_WITH_MAPPINGS", 1)
    return {
        "raw_dir": raw_dir,
        "records": records,
        "raw_sha256": raw_sha256,
        "raw_receipt_file_sha256": raw_receipt_file_sha256,
        "raw_receipt_sha256": raw_receipt_sha256,
        "evidence_path": evidence_path,
        "evidence_sha256": evidence_sha256,
        "raw_characters": raw_characters,
        "normalized_characters": normalized_characters,
    }


def _adapt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, name: str = "normalized") -> tuple[dict, dict]:
    fixture = _fixture_inputs(tmp_path, monkeypatch)
    output = tmp_path / name
    receipt = adapter.adapt_spas_glyphs(
        pdf_path=tmp_path / "fixture.pdf",
        raw_catalog_dir=fixture["raw_dir"],
        mapping_evidence_path=fixture["evidence_path"],
        private_output_dir=output,
        expected_raw_output_sha256=fixture["raw_sha256"],
        expected_raw_receipt_file_sha256=fixture["raw_receipt_file_sha256"],
        expected_raw_receipt_sha256=fixture["raw_receipt_sha256"],
        expected_mapping_evidence_sha256=fixture["evidence_sha256"],
        expected_records=2,
        expected_raw_characters=fixture["raw_characters"],
        expected_normalized_characters=fixture["normalized_characters"],
        expected_records_with_mappings=1,
        expected_mapping_events=adapter.EXPECTED_MAPPING_EVENTS,
    )
    return receipt, fixture


def test_maps_exact_frozen_bukyvede_patterns_and_reverses() -> None:
    raw = "Початок " + _mapped_text() + " кінець"
    normalized, events = apply_bukyvede_mapping(raw)

    assert "\ue002" not in normalized
    assert "\ue026" not in normalized
    assert "\ue027" not in normalized
    assert "\ue02e" not in normalized
    assert "\ue02f" not in normalized
    assert normalized.count("\u0483") == 13
    assert normalized.count("\u0472") == 4
    assert normalized.count("\u0473") == 10
    assert normalized.count("\ua656") == 3
    assert normalized.count("\ua657") == 27
    assert len(events) == 57
    assert reconstruct_raw_text(normalized, events) == raw


def test_longest_patterns_consume_following_cyrillic_a() -> None:
    normalized, events = apply_bukyvede_mapping("\ue02e\u0410|\ue02f\u0430")

    assert normalized == "\ua656|\ua657"
    assert events[0]["raw_end_char"] - events[0]["raw_start_char"] == 2
    assert events[0]["normalized_end_char"] - events[0]["normalized_start_char"] == 1


@pytest.mark.parametrize("text", ["\ue02eБ", "\ue02fб", "\ue099"])
def test_rejects_unmapped_or_malformed_private_use_patterns(text: str) -> None:
    with pytest.raises(SpasGlyphAdapterError, match="unmapped private-use character"):
        apply_bukyvede_mapping(text)


def test_record_preserves_raw_text_hashes_offsets_and_fail_closed_flags() -> None:
    raw = _raw_record(1, "А\ue002Б \ue02fа")
    record = adapter.build_normalized_record(raw, upstream_raw_sha256="a" * 64)

    assert record["raw_source_text"] == raw["source_text"]
    assert record["raw_source_text_sha256"] == raw["source_text_sha256"]
    assert reconstruct_raw_text(record["normalized_text"], record["mapping_events"]) == raw["source_text"]
    assert record["output_private_use_codepoint_counts"] == {}
    assert record["commentary_and_inscription_layers_separated"] is False
    assert record["training_eligible"] is False
    assert record["modern_correction_eligible"] is False
    assert record["inferred_character_repairs"] is False
    assert record["provider_calls"] is False


def test_mapping_event_tamper_is_rejected() -> None:
    normalized, events = apply_bukyvede_mapping("А\ue002Б")
    events[0]["normalized_pattern"] = ["U+0472"]

    with pytest.raises(SpasGlyphAdapterError, match="normalized mapping pattern drift"):
        reconstruct_raw_text(normalized, events)


def test_mapping_event_raw_offset_tamper_is_rejected() -> None:
    normalized, events = apply_bukyvede_mapping("А\ue002Б")
    events[0]["raw_start_char"] += 1

    with pytest.raises(SpasGlyphAdapterError, match="raw mapping event start offset drift"):
        reconstruct_raw_text(normalized, events)


def test_adapter_writes_deterministic_private_layer_and_text_free_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt, _fixture = _adapt(tmp_path, monkeypatch)
    output = tmp_path / "normalized"
    with gzip.open(output / adapter.OUTPUT_FILENAME, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]

    assert len(rows) == 2
    assert rows[0]["raw_source_text"] == _mapped_text()
    assert rows[0]["normalized_text"] != rows[0]["raw_source_text"]
    assert receipt["denominator"]["mapping_events"] == 57
    assert receipt["denominator"]["records_with_mappings"] == 1
    assert receipt["denominator"]["output_private_use_occurrences"] == 0
    assert receipt["safeguards"]["training_eligible"] is False
    assert receipt["safeguards"]["phase4_authorized"] is False
    assert receipt["residuals"]["commentary_transcription_separation_pending"] is True
    assert receipt["residuals"]["lavra_cave_corpus_gap_closed"] is False
    assert "Без приватних символів" not in json.dumps(receipt, ensure_ascii=False)
    adapter._validate_receipt(receipt)


def test_adapter_output_is_byte_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first, fixture = _adapt(tmp_path, monkeypatch, name="first")
    second_output = tmp_path / "second"
    second = adapter.adapt_spas_glyphs(
        pdf_path=tmp_path / "fixture.pdf",
        raw_catalog_dir=fixture["raw_dir"],
        mapping_evidence_path=fixture["evidence_path"],
        private_output_dir=second_output,
        expected_raw_output_sha256=fixture["raw_sha256"],
        expected_raw_receipt_file_sha256=fixture["raw_receipt_file_sha256"],
        expected_raw_receipt_sha256=fixture["raw_receipt_sha256"],
        expected_mapping_evidence_sha256=fixture["evidence_sha256"],
        expected_records=2,
        expected_raw_characters=fixture["raw_characters"],
        expected_normalized_characters=fixture["normalized_characters"],
        expected_records_with_mappings=1,
        expected_mapping_events=57,
    )

    assert first["output"]["sha256"] == second["output"]["sha256"]
    assert first["output"]["record_identity_manifest_sha256"] == second["output"]["record_identity_manifest_sha256"]
    assert first["receipt_sha256"] == second["receipt_sha256"]


def test_existing_adapter_rebinds_pdf_raw_evidence_and_every_output_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt, fixture = _adapt(tmp_path, monkeypatch)
    validation = adapter.validate_existing_glyph_adapter(
        pdf_path=tmp_path / "fixture.pdf",
        raw_catalog_dir=fixture["raw_dir"],
        mapping_evidence_path=fixture["evidence_path"],
        private_output_dir=tmp_path / "normalized",
    )

    assert validation == {
        "ok": True,
        "records": 2,
        "mapping_events": 57,
        "output_sha256": receipt["output"]["sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "training_eligible": False,
        "phase4_authorized": False,
    }


def test_existing_adapter_rejects_output_tamper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _receipt, fixture = _adapt(tmp_path, monkeypatch)
    output_path = tmp_path / "normalized" / adapter.OUTPUT_FILENAME
    payload = bytearray(output_path.read_bytes())
    payload[len(payload) // 2] ^= 1
    output_path.write_bytes(payload)

    with pytest.raises(SpasGlyphAdapterError, match="SHA-256 drift"):
        adapter.validate_existing_glyph_adapter(
            pdf_path=tmp_path / "fixture.pdf",
            raw_catalog_dir=fixture["raw_dir"],
            mapping_evidence_path=fixture["evidence_path"],
            private_output_dir=tmp_path / "normalized",
        )


def test_receipt_rejects_mapping_rule_substitution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipt, _fixture = _adapt(tmp_path, monkeypatch)
    receipt["mapping_contract"]["rules"][0]["normalized_pattern"] = ["U+0472"]
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = adapter.sha256_value(body)

    with pytest.raises(SpasGlyphAdapterError, match="mapping-rule contract drift"):
        adapter._validate_receipt(receipt)


def test_mapping_evidence_tamper_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = _fixture_inputs(tmp_path, monkeypatch)
    evidence = fixture["evidence_path"]
    evidence.write_text(evidence.read_text(encoding="utf-8") + " ", encoding="utf-8")

    with pytest.raises(SpasGlyphAdapterError, match="mapping evidence SHA-256 drift"):
        adapter.validate_mapping_evidence(evidence)


def test_adapter_refuses_existing_output_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = _fixture_inputs(tmp_path, monkeypatch)
    output = tmp_path / "normalized"
    output.mkdir()

    with pytest.raises(SpasGlyphAdapterError, match="already exists"):
        adapter.adapt_spas_glyphs(
            pdf_path=tmp_path / "fixture.pdf",
            raw_catalog_dir=fixture["raw_dir"],
            mapping_evidence_path=fixture["evidence_path"],
            private_output_dir=output,
            expected_raw_output_sha256=fixture["raw_sha256"],
            expected_raw_receipt_file_sha256=fixture["raw_receipt_file_sha256"],
            expected_raw_receipt_sha256=fixture["raw_receipt_sha256"],
            expected_mapping_evidence_sha256=fixture["evidence_sha256"],
            expected_records=2,
            expected_raw_characters=fixture["raw_characters"],
            expected_normalized_characters=fixture["normalized_characters"],
            expected_records_with_mappings=1,
            expected_mapping_events=57,
        )


def test_adapter_refuses_private_output_inside_git_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture_inputs(tmp_path, monkeypatch)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").write_text("gitdir: fixture", encoding="utf-8")

    with pytest.raises(SpasGlyphAdapterError, match="cannot be inside a Git checkout"):
        adapter.adapt_spas_glyphs(
            pdf_path=tmp_path / "fixture.pdf",
            raw_catalog_dir=fixture["raw_dir"],
            mapping_evidence_path=fixture["evidence_path"],
            private_output_dir=checkout / "private",
        )
