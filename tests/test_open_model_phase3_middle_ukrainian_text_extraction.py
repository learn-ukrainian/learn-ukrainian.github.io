from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_middle_ukrainian_text_extraction as extraction
from scripts.projects.open_model_data.phase3_middle_ukrainian_text_extraction import (
    MiddleUkrainianTextExtractionError,
)

FAKE_DECODER = """
var DjVu = {
  VERSION: "test-1",
  Document: class {
    constructor(buffer) { this.buffer = buffer; }
    getPagesQuantity() { return 2; }
    getPageUnsafe(number) {
      const text = number === 1 ? "тест" : "";
      const zones = number === 1
        ? [{x: 1, y: 2, width: 3, height: 4, text: "тест"}]
        : null;
      return {
        getWidth() { return 100; },
        getHeight() { return 200; },
        getDpi() { return 300; },
        getRotation() { return 0; },
        getText() { return text; },
        getNormalizedTextZones() { return zones; },
        reset() {},
      };
    }
  }
};
"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _patch_fixture_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[Path, Path, Path]:
    source_path = tmp_path / "fixture.djvu"
    source_path.write_bytes(b"private-fixture-djvu")
    decoder_path = tmp_path / "decoder.js"
    decoder_path.write_text(FAKE_DECODER, encoding="utf-8")
    schema_path = tmp_path / "receipt-schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")

    monkeypatch.setattr(extraction.intake, "SOURCE_BYTES", source_path.stat().st_size)
    monkeypatch.setattr(extraction.intake, "SOURCE_SHA256", _sha256(source_path))
    monkeypatch.setattr(extraction, "DECODER_BYTES", decoder_path.stat().st_size)
    monkeypatch.setattr(extraction, "DECODER_SHA256", _sha256(decoder_path))
    monkeypatch.setattr(extraction, "DECODER_VERSION", "test-1")
    monkeypatch.setattr(extraction, "EXPECTED_PAGES", 2)
    monkeypatch.setattr(extraction, "RECEIPT_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(
        extraction.intake,
        "validate_existing_intake",
        lambda **_kwargs: {
            "receipt_file_sha256": extraction.RAW_INTAKE_RECEIPT_FILE_SHA256,
            "receipt_sha256": extraction.RAW_INTAKE_RECEIPT_SHA256,
        },
    )

    probe_path = tmp_path / "probe.jsonl"
    runner_summary = extraction._invoke_extractor(
        source_path=source_path,
        decoder_path=decoder_path,
        output_path=probe_path,
    )
    monkeypatch.setattr(extraction, "EXPECTED_TEXT_LAYER_PAGES", runner_summary["text_layer_pages"])
    monkeypatch.setattr(extraction, "EXPECTED_NONEMPTY_TEXT_PAGES", runner_summary["nonempty_text_pages"])
    monkeypatch.setattr(extraction, "EXPECTED_TOTAL_CODE_POINTS", runner_summary["total_code_points"])
    monkeypatch.setattr(extraction, "EXPECTED_TOTAL_UTF8_BYTES", runner_summary["total_utf8_bytes"])
    monkeypatch.setattr(extraction, "EXPECTED_TOTAL_ZONES", runner_summary["total_zones"])
    monkeypatch.setattr(extraction, "EXPECTED_PRIVATE_JSONL_BYTES", runner_summary["private_jsonl_bytes"])
    monkeypatch.setattr(extraction, "EXPECTED_PRIVATE_JSONL_SHA256", runner_summary["private_jsonl_sha256"])
    monkeypatch.setattr(
        extraction,
        "EXPECTED_PAGE_TEXT_HASH_MANIFEST_SHA256",
        runner_summary["page_text_hash_manifest_sha256"],
    )
    monkeypatch.setattr(
        extraction,
        "EXPECTED_TEXT_ZONE_HASH_MANIFEST_SHA256",
        runner_summary["text_zone_hash_manifest_sha256"],
    )
    monkeypatch.setattr(
        extraction,
        "EXPECTED_PAGE_GEOMETRY_MANIFEST_SHA256",
        runner_summary["page_geometry_manifest_sha256"],
    )
    monkeypatch.setattr(extraction, "EXPECTED_GEOMETRY_COUNTS", {"100x200@300r0": 2})
    probe_path.unlink()
    return source_path, decoder_path, schema_path


def test_materialize_and_validate_private_page_aligned_extraction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path, decoder_path, _schema_path = _patch_fixture_contract(monkeypatch, tmp_path)
    output_dir = tmp_path / "private-output"

    result = extraction.materialize_extraction(
        source_path=source_path,
        raw_intake_dir=tmp_path / "raw-intake",
        decoder_path=decoder_path,
        private_output_dir=output_dir,
    )
    replay = extraction.validate_existing_extraction(
        source_path=source_path,
        raw_intake_dir=tmp_path / "raw-intake",
        private_output_dir=output_dir,
    )

    assert result == replay
    assert replay["pages"] == 2
    assert replay["text_layer_pages"] == 1
    assert replay["total_code_points"] == 4
    assert replay["total_zones"] == 1
    assert replay["visual_alignment_quality_verified"] is False
    assert replay["training_eligible"] is False
    assert replay["phase3_complete"] is False
    assert replay["phase4_blocked"] is True
    private_rows = [
        json.loads(line)
        for line in (output_dir / extraction.PRIVATE_JSONL_FILENAME).read_text(encoding="utf-8").splitlines()
    ]
    assert private_rows[0]["decoded_text"] == "тест"
    assert private_rows[0]["text_zones"][0]["text"] == "тест"
    assert private_rows[1]["decoded_text"] == ""
    assert private_rows[1]["text_zones"] is None


def test_private_jsonl_rejects_same_length_text_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path, decoder_path, _schema_path = _patch_fixture_contract(monkeypatch, tmp_path)
    output_dir = tmp_path / "private-output"
    extraction.materialize_extraction(
        source_path=source_path,
        raw_intake_dir=tmp_path / "raw-intake",
        decoder_path=decoder_path,
        private_output_dir=output_dir,
    )
    jsonl_path = output_dir / extraction.PRIVATE_JSONL_FILENAME
    payload = jsonl_path.read_text(encoding="utf-8").replace("тест", "теср", 1)
    jsonl_path.write_text(payload, encoding="utf-8")

    with pytest.raises(MiddleUkrainianTextExtractionError, match="SHA-256 drift"):
        extraction.validate_existing_extraction(
            source_path=source_path,
            raw_intake_dir=tmp_path / "raw-intake",
            private_output_dir=output_dir,
        )


def test_decoder_tamper_fails_before_private_output_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path, decoder_path, _schema_path = _patch_fixture_contract(monkeypatch, tmp_path)
    decoder_path.write_text(FAKE_DECODER.replace("test-1", "test-X"), encoding="utf-8")
    output_dir = tmp_path / "private-output"

    with pytest.raises(MiddleUkrainianTextExtractionError, match="decoder SHA-256 drift"):
        extraction.materialize_extraction(
            source_path=source_path,
            raw_intake_dir=tmp_path / "raw-intake",
            decoder_path=decoder_path,
            private_output_dir=output_dir,
        )
    assert not output_dir.exists()


def test_existing_private_output_is_immutable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path, decoder_path, _schema_path = _patch_fixture_contract(monkeypatch, tmp_path)
    output_dir = tmp_path / "private-output"
    output_dir.mkdir()

    with pytest.raises(MiddleUkrainianTextExtractionError, match="already exists"):
        extraction.materialize_extraction(
            source_path=source_path,
            raw_intake_dir=tmp_path / "raw-intake",
            decoder_path=decoder_path,
            private_output_dir=output_dir,
        )


def test_private_output_inside_git_checkout_is_rejected(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").mkdir()

    with pytest.raises(MiddleUkrainianTextExtractionError, match="inside Git"):
        extraction.materialize_extraction(
            source_path=tmp_path / "missing.djvu",
            raw_intake_dir=tmp_path / "missing-intake",
            decoder_path=tmp_path / "missing.js",
            private_output_dir=checkout / "private-output",
        )


def test_runner_failure_removes_partial_jsonl(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path, decoder_path, _schema_path = _patch_fixture_contract(monkeypatch, tmp_path)
    bad_decoder = FAKE_DECODER.replace("width: 3", "width: 300")
    decoder_path.write_text(bad_decoder, encoding="utf-8")
    monkeypatch.setattr(extraction, "DECODER_BYTES", decoder_path.stat().st_size)
    monkeypatch.setattr(extraction, "DECODER_SHA256", _sha256(decoder_path))
    output_path = tmp_path / "partial.jsonl"

    with pytest.raises(MiddleUkrainianTextExtractionError, match="exceeds page bounds"):
        extraction._invoke_extractor(
            source_path=source_path,
            decoder_path=decoder_path,
            output_path=output_path,
        )
    assert not output_path.exists()


@pytest.mark.parametrize(
    ("needle", "replacement"),
    [
        ('const text = number === 1 ? "тест" : "";', 'const text = number === 1 ? "\\uD800" : "";'),
        ('text: "тест"', 'text: "\\uD800"'),
    ],
)
def test_runner_rejects_unpaired_utf16_surrogates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    needle: str,
    replacement: str,
) -> None:
    source_path, decoder_path, _schema_path = _patch_fixture_contract(monkeypatch, tmp_path)
    decoder_path.write_text(FAKE_DECODER.replace(needle, replacement), encoding="utf-8")
    monkeypatch.setattr(extraction, "DECODER_BYTES", decoder_path.stat().st_size)
    monkeypatch.setattr(extraction, "DECODER_SHA256", _sha256(decoder_path))
    output_path = tmp_path / "invalid-unicode.jsonl"

    with pytest.raises(MiddleUkrainianTextExtractionError, match="unpaired UTF-16 surrogate"):
        extraction._invoke_extractor(
            source_path=source_path,
            decoder_path=decoder_path,
            output_path=output_path,
        )
    assert not output_path.exists()


def test_private_jsonl_rejects_unpaired_utf16_surrogate_with_typed_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path, decoder_path, _schema_path = _patch_fixture_contract(monkeypatch, tmp_path)
    jsonl_path = tmp_path / "private-page-text.jsonl"
    extraction._invoke_extractor(
        source_path=source_path,
        decoder_path=decoder_path,
        output_path=jsonl_path,
    )
    rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
    rows[0]["decoded_text"] = "\ud800"
    payload = "".join(
        f"{json.dumps(row, ensure_ascii=True, separators=(',', ':'))}\n"
        for row in rows
    )
    jsonl_path.write_text(payload, encoding="ascii")
    monkeypatch.setattr(extraction, "EXPECTED_PRIVATE_JSONL_BYTES", jsonl_path.stat().st_size)
    monkeypatch.setattr(extraction, "EXPECTED_PRIVATE_JSONL_SHA256", _sha256(jsonl_path))

    with pytest.raises(MiddleUkrainianTextExtractionError, match="unpaired UTF-16 surrogate"):
        extraction.validate_private_jsonl(jsonl_path)


def test_materialization_failure_cleans_staging_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path, decoder_path, _schema_path = _patch_fixture_contract(monkeypatch, tmp_path)
    output_dir = tmp_path / "private-output"

    def reject(_receipt: object) -> None:
        raise MiddleUkrainianTextExtractionError("forced receipt failure")

    monkeypatch.setattr(extraction, "_validate_receipt", reject)
    with pytest.raises(MiddleUkrainianTextExtractionError, match="forced receipt failure"):
        extraction.materialize_extraction(
            source_path=source_path,
            raw_intake_dir=tmp_path / "raw-intake",
            decoder_path=decoder_path,
            private_output_dir=output_dir,
        )
    assert not output_dir.exists()
    assert not list(tmp_path.glob(".private-output.stage-*"))


def test_receipt_schema_is_text_free_and_fail_closed() -> None:
    schema = json.loads(extraction.RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    serialized = json.dumps(schema, ensure_ascii=False)

    assert '"decoded_text"' not in serialized
    assert '"text_zones"' not in serialized
    assert schema["properties"]["extraction_scope"]["properties"]["embedded_text_quality_verified"] == {
        "const": False
    }
    assert schema["properties"]["safeguards"]["properties"]["training_eligible"] == {"const": False}
    assert schema["properties"]["safeguards"]["properties"]["phase3_complete"] == {"const": False}
    assert schema["properties"]["safeguards"]["properties"]["phase4_blocked"] == {"const": True}


def test_receipt_binds_prior_raw_intake_identity() -> None:
    schema = json.loads(extraction.RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    source_properties = schema["properties"]["source_binding"]["properties"]

    assert source_properties["raw_intake_receipt_file_sha256"]["const"] == extraction.RAW_INTAKE_RECEIPT_FILE_SHA256
    assert source_properties["raw_intake_receipt_sha256"]["const"] == extraction.RAW_INTAKE_RECEIPT_SHA256
